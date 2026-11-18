"""Facts about the user, pulled out of what they say. The conversation lane owns this file.

`extract(text)` returns only the facts a line clearly states, e.g.
{"name": "Jess", "job": "nurse", "city": "Leeds", "allergies": ["nuts"]}.
Callers merge the result into memory["user"] with bot.memory.remember(), which keeps an
ordered log so the bot can answer "what did I say my name was?" and "which city did I say
first?". Nothing here replies; it is data extraction only.
"""
import re

from ..understanding import breeds, lexicon, normalize
from ..understanding.kinds import EMOTION_WORDS, VERB_FORMS
from ..understanding.topics import STRONG, PHRASES, WORD_NUMBERS, CONDITIONS

from .named import the_name_in
from . import taste
from .filler import TAIL_OFF

# ---------------------------------------------------------------------------
# names

# A capitalised word right after "I'm" is a name ("I'm Jess"), but only when it is not one
# of the words people usually put there. The same list lets lower-case chat ("im tom") work.
NOT_NAMES = frozenset("""
a an the this that these those not no so really very quite just still also always already
only even now here there back home off out in on at up down over around about all both too
good bad great fine ok okay sure glad happy sad angry upset tired exhausted hungry thirsty bored
busy free late early lost done ready sorry afraid scared nervous worried stressed excited
confused lonely ill sick better worse old young new first second third next last single
married pregnant vegan vegetarian allergic serious interested trying looking thinking planning
coeliac celiac diabetic asthmatic epileptic anaemic anemic intolerant lactose gluten autistic
adhd menopausal perimenopausal pescatarian flexitarian veggie
going coming getting having making doing writing working learning studying cooking moving buying
playing watching reading listening talking speaking feeling letting taking giving waiting
hoping wondering asking saying telling checking shopping cleaning walking running driving
flying travelling traveling starting finishing meeting visiting staying living eating drinking
sleeping sitting standing paying spending saving booking ordering calling texting emailing
posting sharing using fixing building creating preparing practising practicing revising
training coaching organising organizing decorating painting gardening baking coming around
fine good well okay alright nearly almost definitely probably maybe perhaps honestly actually
literally seriously totally completely absolutely pretty rather kind sort bit little lot
off down out away along through until since while because though although whether
""".split())

# English makes a state out of a noun with a "y": sweat, sweaty; clam, clammy. The endings below
# cannot carry those, because "y" is the last letter of more names than any other one (emily,
# lucy, molly, kelly, daisy, holly), so no length makes the tail safe. They are listed with the
# other states instead, at the end of NOT_NAMES_EXTRA, and the list is the ones that are always
# somebody's state and never somebody's name: "im sweaty" was answered "Nice to meet you,
# Sweaty", and clammy, woozy, jittery, achey, queezy, muggy, bleary, puffy, giddy, edgy, antsy,
# twitchy, hangry, drowsy, buzzy, spacey, dopey, mopey, quivery, fidgety and sniffy were the
# same. `husky` is left out on purpose - it is a dog and a voice as well as a name.
# A lower-case word after "im" is only a name if it does not look like how people describe
# themselves: "im knackered" is a feeling, "hi im alex" is an introduction. The endings
# below are the ones English builds states and conditions with ("tired", "coeliac",
# "diabetic", "welsh", "pregnant"), each with the length a word needs before the ending
# counts more than the chance of it being a name, so "im lily" and "im eric" still work.
NAME_TAIL_MIN = {"ed": 5, "ing": 5, "ly": 6, "ous": 5, "ful": 6, "less": 6,
                 "ish": 4, "able": 6, "ible": 6, "ic": 5, "ac": 5, "ist": 6,
                 "ism": 6, "ese": 5, "ant": 6,
                 # -ive is how English makes a long condition or a mood: depressive,
                 # aggressive, sensitive, possessive. No name of six letters or more ends in it
                 # ("clive" and "steve" are five and keep their own reading), so six is safe:
                 # "im depressive" was answered "Nice to meet you, Depressive".
                 "ive": 6}
# -nt was tried and taken out again: unlike -ed or -ing it is the ending of real names as well
# ("im vincent", "im lamont"), and a name kept by mistake is worse than a state read as one. The
# states that end in it are listed in NOT_NAMES_EXTRA instead.
# The names that end like a state: "im dominic" is still an introduction, and so is "im
# isaac" (which ends in -ac like coeliac) and "im ahmed" (-ed like tired). The endings in
# NAME_TAIL_MIN carry the weight, so the names an ending would eat are listed here.
NAMES_THAT_LOOK_LIKE_STATES = frozenset("""
dominic dominick
isaac cedric frederic
ahmed mohamed muhammed jared
manish trish
kimberly
kay
""".split())
# `rich` is deliberately not here: unlike `cold` or `itchy` it is also a name people are called,
# and the cost is the wrong way round - `im rich` only ever got a silly "Nice to meet you, Rich",
# while a Rich loses his own name for the whole conversation. The state list is for words that
# cannot be both.
NOT_NAMES_EXTRA = frozenset("""
due owed english scottish welsh irish british muslim hindu sikh jew pagan mormon sober adhd ocd ptsd
trans gay straight lesbian bisexual asexual blind deaf disabled unemployed retired homeless
dyspraxic dyscalculic
# A condition somebody lives with is how they are, not who they are, and these two end in
# nothing a state is built out of, so the endings cannot catch them: "im depressive" was
# answered "Nice to meet you, Depressive", and a bare "im hypertensive" the same.
depressive hypertensive
knackered shattered starving freezing boiling skint broke aching sore stuck done outside inside
upstairs downstairs online offline asleep awake alright okay fine good great awful terrible
here there back home away out off in on over around up down away late early soon nearly almost
definitely probably maybe honestly seriously literally actually totally completely absolutely
cold hot warm wet dry cross half mid bloody soaked frozen numb dizzy queasy poorly shaky
safe unsafe itchy stiff calm restless faint bloated snotty sniffly achy crampy
tight weak sleepy dozy groggy foggy comfy cosy snug proud guilty unwell dirty clean poor
# How a person is, not who they are: "im unheard" was answered "Nice to meet you, Unheard" - the
# coldest reply there is to somebody saying they are not heard. "unseen" and "nobody" are the
# same shape ("im nobody" was a name too).
unseen unheard nobody
dead beat spent zonked pooped livid fuming miffed
content confident different important present silent decent pleasant fluent patient absent
violent brilliant distant recent constant sunburnt burnt
full empty unsure certain brave silly daft mad grumpy moody fed fedup
# How somebody says they are, in words that are also other things: "im grand" (Ireland), "im
# sound", "im chill", "im content", "im brill", "im mint". Nothing is repaired in any of them,
# so the repair rule cannot see them, and the store handed the word back as a name: "im grand"
# was answered "Nice to meet you, Grand" and every later turn called the person Grand.
grand sound chill content brill mint
# The same for a disparaging word: "im fat" and "im stupid" are how somebody says they are, and
# the store was filing them as a name ("Nice to meet you, Fat").
fat ugly stupid thick dumb
rundown offshore horny
dressed settled from with for by of to near into than as after
# A word about the spelling or the print of the name is not the name: "my name is spelt wrong on
# my payslip" was answered "Hi Spelt - open the payslip and check...", and "my name is misspelt on
# my contract" was answered "Nice to meet you, Misspelt." Every one of these is a thing said *of*
# a name, never a name people are given.
spelt spelled misspelt misspelled mispelt mispelled printed print handwritten hyphenated
capitalised capitalized typed type pronounced
# The words that close a sentence about somebody else's behaviour, which is where a name is
# least likely and the store was most confident: "my son doesnt call me anymore" was read as an
# introduction, so every later turn called the person Anymore, and the reply opened "Hi Anymore
# - a relative going quiet...". A name after "call me" is offered ("call me Dan"); a word that
# only says when or whether the calling happens is not offered at all.
anymore anyways someday sometime sometimes nowadays ever either neither soon later sooner
tomorrow tonight meanwhile afterwards afterward
# The same list, for the reviewers of this change who sent three more of exactly that shape:
# "my son wont call me again" was "Hi Again", and "call me anytime" and "call me whenever you
# like" introduced the person as Anytime and Whenever. They say when or whether, not who.
again anytime whenever always eventually already once then
""".split()) | frozenset("""
sweaty clammy woozy jittery achey queezy muggy bleary puffy giddy edgy antsy twitchy
hangry drowsy buzzy spacey dopey mopey quivery fidgety sniffy wobbly
# A body word that is also a dog's coat or a Snow White dwarf: "im husky" is a voice going and
# "im sneezy" is a cold starting, and both were answered "Nice to meet you, Husky".
husky sneezy
hungover hangover jetlagged jetlag dehydrated out
""".split())

# A word that names a feeling is how the person is, not who they are: "im mad", "im happy",
# "im grateful" are not introductions. The reading engine already lists those words, so they
# come from there rather than from a second list that would drift.
NOT_A_NAME_FEELING = frozenset(
    word for cues in EMOTION_WORDS.values() for cue in cues for word in cue.split())
# A laugh is not a name either, and it comes from the reading's one table so a form the bot has
# just learned to hear as a laugh cannot still be a person called that: "im lmfao" was met with
# "Nice to meet you, Lmfao."
NOT_A_NAME_LAUGH = frozenset(lexicon.LAUGHTER)


# A condition named by its own name is a state of a body or a mind, not who somebody is: "im
# psoriasis", "im sciatica", "im ibs", "im crohns", "im schizophrenia" all introduced the person
# as Psoriasis, Sciatica, Ibs, Crohns and Schizophrenia, and every later turn called them that.
# The body conditions are the reading engine's own table, so a condition it learns to hear is one
# the store will not file as a name. A condition of the mind is deliberately not added to that
# table: `topics.CONDITIONS` is also the health *subject* scorer, and putting "ptsd" in it made
# "my husband has ptsd from the army" / "he wont talk about it" read as an illness follow-up, so
# the card that tells you how to open a hard conversation stood down (measured by breezy-violet on
# #10914). Two tables with two jobs: the word is a name's lookalike here, and a subject there.
CONDITIONS_OF_THE_MIND = frozenset("""
    bipolar schizophrenia schizophrenic psychosis psychotic anorexic bulimic ptsd ocd adhd
    autism autistic dyspraxic dyspraxia agoraphobia agoraphobic narcolepsy narcoleptic""".split())


def _health_words():
    """The words the reading engine already uses for an illness, as whole words."""
    words = set(STRONG["health"].split())
    for phrase in PHRASES["health"]:
        words.update(phrase.split())
    words.update(CONDITIONS)
    words.update(CONDITIONS_OF_THE_MIND)
    return frozenset(words)


# A word that names how the body is is not who they are either: "im shivery" was read as an
# introduction and answered "Nice to meet you, Shivery." The reading engine already knows the
# illness words ("hoarse", "shivery", "queasy", "crampy"), so they come from there rather than
# from a third list that would drift. Nouns in that list ("doctor", "tablet", "appointment") are
# already in NOT_NAMES, so the same test can be one test.
NOT_A_NAME_ILLNESS = _health_words()

# What a person is like is not who they are called either: "im lazy" was answered "Nice to meet
# you, Lazy. What can I help with?", and the trait is the whole line. The words come from the
# reading engine's one table (`lexicon.TRAITS`), so the answer in bot/modules/chat.py and this
# refusal can never drift apart.
NOT_A_NAME_TRAIT = frozenset(lexicon.TRAITS)
# A word that says what somebody is like, written with none of the endings a state usually
# carries, was read as an introduction: "im quiet" and "im messy" were answered "Nice to meet
# you, Quiet", and so were noisy, picky, fussy, bossy, spoilt, rude, chatty, negative, tidy,
# untidy, nosy, weird, odd and loud - and "im hard work" introduced somebody called Hard. These
# are the words `_describes_them` already keeps for another person ("my dad is stubborn", "my
# sister is noisy"); nothing asked that list when the word came straight after "im". They are
# listed here rather than built from that set because the set is defined further down the file,
# and `DESCRIBING_WORDS` takes this one in so the two cannot drift apart.
NOT_A_NAME_DESCRIBING = frozenset("""quiet messy noisy picky fussy bossy stubborn rude spoilt
    chatty negative positive tidy untidy nosy weird odd loud hard""".split())
# How they are and what they are like, in one test: almost every name rule asks this question,
# and a set that is asked in six places is a set that gets forgotten in one.
# The conditions and states that carry none of the endings above and name a thing a person has
# rather than a thing they are called: "im bipolar" was answered "Nice to meet you, Bipolar",
# and every later turn called the person Bipolar. The condition endings are already covered
# (diabetic, asthmatic, dyslexic, epileptic and coeliac are all -ic, -ac or illness words), so
# this is the short list the endings miss: `bipolar` has no ending to go on, and `froze` is how
# somebody says "I am freezing" ("im froze" was an introduction too).
NOT_A_NAME_CONDITION = frozenset("""bipolar froze""".split())
NOT_A_NAME_STATE = (NOT_A_NAME_FEELING | NOT_A_NAME_ILLNESS | NOT_A_NAME_TRAIT
                    | NOT_A_NAME_DESCRIBING | NOT_A_NAME_CONDITION)

# Words people put round an introduction: "oh sorry, im jess", "jess btw", "im jess here".
# They say nothing about the person, so the clause is still an introduction with them in it.
NAME_FILLER = frozenset("""
sorry oh ah ok okay so well hey hi hello hiya morning evening afternoon good hmm um err erm anyway
btw actually also and but yeah yes yep no nah right cool thanks thank please alright howdy
first quickly just then too lol haha
""".split())
NAME_FILLER_PHRASES = ("i forgot to say", "forgot to say", "i should say", "i should have said",
                       "should have said", "by the way", "for the record", "just so you know",
                       "forgot to mention", "i did not say", "i did not mention")

# What can follow a name and leave the line an introduction rather than a sentence about
# something else: "jess here", "jess btw", "jess, nice to meet you", "jess and im 34".
NAME_FOLLOWERS = frozenset("""
here there btw way hi hey hello hiya nice to meet you u thanks thank ta cheers too also again
lol haha x xo sorry but and so just actually ok okay right good great yes yeah yep im am is was
did do your my we us how pleased glad meet meetin
""".split())
# After one of these the rest of the line says where they are or what they do, not what they
# are called: "jess from leeds", "jess at work".
NAME_PLACE_WORDS = frozenset("from in near at live living moved moving".split())
# Words that stand between "where they are" and the place itself: "jess living in leeds".
PLACE_JOIN = frozenset("in near at to from round around outside".split())
# A clause after the name that goes on about the person: "jess, live in salford with two kids",
# "tom, i work in a bakery", "sam, have two cats", "ellie and i'm 34". The line is still an
# introduction, so the name stands; the clause after it is what the person is telling us.
# A possessive ("my daughter is 6", "our cat is called Biscuit") or "I've" ("ive got two
# kids") starts a clause about the person just as "i"/"im" does, and people join an
# introduction to it with nothing but "and": "hi im dan and my daughter is 6" is the same
# introduction as "hi im dan, my daughter is 6". Without these the name was dropped and the
# bot answered "You haven't told me your name yet" to somebody who had just given it.
NAME_SAYS_ABOUT_ME = frozenset("""i i'm im ive i've live lives living work works working have
    has got like love hate prefer study studying play playing run running keep keep looking
    trying do doing need want grew raised born based married
    my our we we're we've myself""".split())

# A name is often followed by a hedge that adds nothing to who they are: "hi im meg to be
# honest", "im sam tbh". The hedge is not the start of a sentence about them, so it is taken
# off the end of the introduction before the tail is read, and the name stands.
NAME_ASIDES = ("to be honest", "to be fair", "to be truthful", "if that helps", "if im honest",
               "i think", "i suppose", "i guess", "i expect", "by the way", "for what its worth",
               "honestly", "tbh", "btw", "anyway", "though", "actually")

# The same hedges, taken off an answer to the bot's own name question rather than off the end of
# an introduction: "its sam by the way", "sam, btw", "im sam thanks". The store waits for one
# word there, so a hedge still on the line made it three and the answer went nowhere: the person
# gave the name they had just been asked for and the bot said "I'm listening - say more if it
# helps", then "You haven't told me your name yet" a turn later. A courtesy after the name is the
# same kind of word, and goes with it.
NAME_ANSWER_HEDGES = re.compile(
    r"\b(?:" + "|".join(sorted(NAME_ASIDES + ("thanks", "thank you", "ta", "cheers"),
                                 key=len, reverse=True)) + r")\b", re.I)


def without_the_hedges(text):
    """A name answer with its hedges taken off: "its sam by the way" -> "its sam".

    Only the words in `NAME_ASIDES` and a courtesy after the name are removed, so the name itself
    is handed on exactly as it was typed.
    """
    low = " ".join(str(text or "").lower().split())
    return " ".join(NAME_ANSWER_HEDGES.sub(" ", low).split()).strip(" ,.:;!?")

# The word that marks a correction sits inside the introduction as often as in front of it:
# "my name's actually Preeya", "my names honestly Dan". Only the words that say nothing about
# what follows are here, so "my name is really long" is still not somebody called Long.
NAME_MIDDLE = r"(?:(?:actually|honestly|truthfully|officially|properly|tbh)\s+)?"

# The person names themselves: "my name's Jess", "call me Dan". The word after it is a name.
ANNOUNCED_NAME_PATTERNS = (
    re.compile(r"\bmy name(?:['\u2019]s| is|s)\s+" + NAME_MIDDLE +
               r"([a-z][a-z'-]{1,19})", re.I),
    re.compile(r"\bcall me\s+" + NAME_MIDDLE + r"([a-z][a-z'-]{1,19})", re.I),
    # "I'm called Dave", "I am called Dave": the same introduction the other way round, and
    # the one people use when the name is not the first thing in the line ("hi, I'm called
    # Dave"). The word after "called" passes the same test as any other name.
    re.compile(r"\b(?:i am|i'm|im)\s+(?:called|named)\s+([a-z][a-z'-]{1,19})", re.I),
    # "Name's Dave", "the name's Dave": the line opens with it, so it is not "her name's
    # Biscuit", which names someone else's pet. The name has to end the line, or close it before
    # a courtesy ("names Dave, thanks"), because "names are hard" and "name and shame" open the
    # same way and are sentences about names, not introductions.
    re.compile(r"^\W*(?:the\s+)?names?(?:['\u2019]s)?\s+(?:is\s+)?" + NAME_MIDDLE +
               r"([a-z][a-z'-]{1,19})"
               r"(?=\s*[,.!?;:)\]]|\s*$|\s+(?:thanks|ta|cheers|btw|anyway|by the way|"
               r"nice to meet you|pleased to meet you|how are you|good to meet you)\b)", re.I),
)
# The name they answer to, as against the one on the paperwork: "i go by kit" is how somebody
# introduces themselves when the name they use is not their first one.
GOES_BY_NAME = re.compile(r"\b(?:i|we)\s+go(?:es)?\s+by\s+([a-z][a-z'-]{1,19})", re.I)
# The edges a line opens a new clause on, so a go-by said as its own thought can be read alone.
CLAUSE_SPLIT = re.compile(r"\b(?:but|and|though|although)\b|[;,.!?]")
# "I'm Jess" and "I go by Kit" are also how any number of sentences about a person start
# ("im cold", "im sat in the car", "i go by bus"), so the rest of the line has to agree.
GUESSED_NAME_PATTERNS = (
    re.compile(r"\b(?:i am|i'm|im|we are|we're)\s+([A-Z][a-z'-]{1,19})\b"),
    re.compile(r"\b(?:i am|i'm|im|we are|we're)\s+([a-z][a-z'-]{1,19})\b", re.I),
    GOES_BY_NAME,
)
# Ways of going somewhere, so "i go by bus" is not someone called Bus.
GO_BY_WAYS = frozenset("""bus car train coach tube tram plane bike foot taxi rail boat ship road
motorway""".split())

# ---------------------------------------------------------------------------
# places

MONTHS = frozenset("""january february march april may june july august september october
november december jan feb mar apr jun jul aug sep sept oct nov dec""".split())
DAYS = frozenset("monday tuesday wednesday thursday friday saturday sunday weekend".split())
COUNTRIES = frozenset("""england scotland wales ireland britain uk america usa canada australia
new zealand france spain portugal italy germany greece turkey egypt morocco japan china korea
india pakistan thailand vietnam indonesia mexico brazil argentina peru chile colombia cuba iceland
norway sweden denmark finland netherlands belgium switzerland austria poland czech slovakia
hungary croatia serbia romania bulgaria russia ukraine israel south africa kenya nigeria ghana
philippines malaysia singapore""".split())
# Where a thing is in the house is not a place name: "im from upstairs", "i live downstairs".
NOT_POSITIONS = frozenset("""upstairs downstairs inside outside indoors outdoors here there
abroad away""".split())
NOT_PLACES = MONTHS | DAYS | NOT_NAMES | NOT_POSITIONS | frozenset("""christmas easter summer winter autumn
spring morning afternoon evening night today tomorrow yesterday home work school uni
university college hospital doctor dentist""".split())

PLACE_AFTER = re.compile(
    r"\b(?:in|to|from|near|at|visit|visiting|visited|off to|trip to|travel to|went to)\s+"
    r"([A-Z][a-z]+(?:[ -][A-Z][a-z]+)?)\b")
# Chat-speak names places in lower case: "we're going to lisbon in may".
PLACE_LOWER = re.compile(
    r"\b(?:going to|off to|flying to|fly to|travel(?:l)?ing to|trip to|holiday in|moving to|"
    r"heading to|visit(?:ing)?)\s+([a-z][a-z]{2,})\b", re.I)
# Asking words, not facts: "what am i allergic to again" names no allergy, and "what is my
# budget then" names no budget. A value that opens with one of these is the question talking.
NOT_A_FACT = frozenset("""again already actually anyway anyhow please sorry else though now
anybody anyone anything everywhere somewhere nothing something then though""".split())


# A clause that asks ("what can I have?", "where do I live?") ends the fact before it.
ASK_WORDS = NOT_A_FACT | frozenset("""what who where when why how which whether can could
should would do does did""".split())


# A verb that can follow a joining "then" inside a plan: "swim then do a triathlon".
AFTER_THEN = frozenset("""do get go be have see try take make start learn visit eat stay move
buy save write read run walk swim cook book""".split())


def _fact_value(word):
    """The thing a pattern caught, cut short where the question starts: "" when there is none.

    "what am i allergic to again" caught "again", and "nuts, what can I have?" caught "nuts,
    what can": neither is a fact. Returns the value itself otherwise.
    """
    # The value is kept exactly as it was written, separators and all: splitting on commas
    # turned "6,000 pounds" into "6 000 pounds".
    parts = re.split(r"([\s,]+)", str(word or "").strip())
    words = [parts[i] for i in range(0, len(parts), 2)]
    kept = []
    for i, value in enumerate(words):
        # "learn to swim then do a triathlon": the "do" after a joining "then" is the second
        # thing they mean to do, not the start of a question.
        if value.lower() in AFTER_THEN and i and words[i - 1].lower() == "then":
            kept.append(parts[2 * i] + (parts[2 * i + 1] if 2 * i + 1 < len(parts) else ""))
            continue
        if value.lower() in ASK_WORDS:
            # "then" mid-sentence joins two things they mean to do ("york then leeds", "learn
            # to swim then do a triathlon"), so it only ends a value when nothing follows it:
            # "my budget is 300 then" is 300.
            if value.lower() == "then" and words[i + 1:]:
                kept.append(parts[2 * i] + (parts[2 * i + 1] if 2 * i + 1 < len(parts) else ""))
                continue
            break
        kept.append(parts[2 * i] + (parts[2 * i + 1] if 2 * i + 1 < len(parts) else ""))
    out = "".join(kept).strip(" ,;:")
    if out.lower().endswith(" then"):
        out = out[:-5].rstrip(" ,;:")  # a "then" the cut left behind is not part of the fact
    return out


# "a flat in leeds", "the house near york": the home named before the place it is in.
HOME_IN = (r"(?:a|an|the|my|our|this|that)\s+(?:[a-z][a-z-]*\s+){0,2}"
           r"(?:flat|house|home|place|cottage|bungalow|farm|village|town|city|studio|area|"
           r"suburb|apartment|maisonette|caravan|boat)\s+(?:in|near|on|at|outside|round)\s+")

# Where they live is a place whatever the capitals: "i live in leeds", "we moved to preston".
# A stay is a visit and not a home ("we're staying in york for the weekend"), so the verb is
# caught on its own and _places() files the place without calling it home.
# The place they live is still the place when they name what they live in first: "we live in a
# flat in manchester", "we live in a village outside leeds". The second preposition is what makes
# the word after it a place name, so "i live in the city centre" stays a way of living.
DWELLING = (r"(?:flat|house|home|cottage|bungalow|place|caravan|boat|hostel|studio|bedsit|"
            r"village|town|hamlet)")
HOME_DWELL = re.compile(
    r"\b(?:i|we)(?:\s?'?(?:m|re|ve|s)| am| are| have| has| had)?\s+"
    r"(?:(?:just|recently|finally|already|also|now)\s+)?"
    r"(?:(?P<stay>stay|stays|staying)|(?P<planned>moving|relocating|relocate|moving house)|"
    r"(?:live|living|lives|moved|moves|moving|settled|settling|relocating|relocated|relocate|"
    r"based))\s+"
    r"(?:(?:up|back|over|out|down|away)\s+)?(?:in|to|near|outside|round)\s+"
    # A word about the dwelling sits between the article and the noun: "a rented flat in leeds",
    # "a two bed flat in leeds". It cannot be the second preposition, which is where the place
    # starts.
    r"(?:(?:a|an|the|our|my|their|his|her)\s+"
    r"(?:(?!(?:in|to|near|outside|round|at|by|with|from)\b)[a-z][a-z'-]*\s+){0,2}"
    + DWELLING + r"\s+)"
    r"(?:in|near|outside|round)\s+"
    r"(?P<place>[A-Za-z][A-Za-z'-]{1,}(?:[ -][A-Za-z][A-Za-z'-]{1,})?)\b", re.I)
HOME_PLACE = re.compile(
    # "we're living in leeds" is the usual way to say it, and chat-speak drops the apostrophe:
    # "we re living in leeds". Both are the same line.
    r"\b(?:i|we)(?:\s?'?(?:m|re|ve|s)| am| are| have| has| had)?\s+"
    # "i've just moved to bristol", "we recently settled in york": an adverb between the
    # auxiliary and the verb does not change which verb it is, and the move is still a move.
    r"(?:(?:just|recently|finally|already|also|now)\s+)?"
    r"(?:(?P<stay>stay|stays|staying)|(?P<planned>moving|relocating|relocate|moving house)|"
    r"(?:live|living|lives|"
    r"moved|moves|moving|settled|settling|relocating|relocated|relocate|based|"
    # "i rent a flat in leeds", "we bought a house near york": the same fact in the words of
    # someone who pays for the place rather than moves to it.
    r"rent|rents|renting|bought|buying))\s+"
    # "we've recently moved up to york": a particle before the preposition does not change where
    # they moved to. "i live just outside leeds" is the same line with the particle in front.
    r"(?:(?:up|back|over|out|down|away|just|right|far)\s+)?"
    # "i live in a flat in leeds", "we rent a small house near york", "i bought a house in
    # preston": the home is named first and the place it stands in comes after it, so the place
    # is the one the home is in - either after "in" or straight after the verb.
    #
    # The preposition is not optional: left optional, "i live near a school in leeds" read
    # "near" as the place and "i live close to bristol" read "close to" as one, and the store
    # then answered "You live in Near". A preposition with nothing that names a place behind it
    # says how they live, not where, so it leaves the line with no place at all.
    r"(?:(?:in|to|near|outside|round)\s+(?:" + HOME_IN + r")?|" + HOME_IN + r")"
    r"(?P<place>[A-Za-z][A-Za-z'-]{1,}(?:[ -][A-Za-z][A-Za-z'-]{1,})?)\b", re.I)
# A place name of two words is a place: "i live in new york". The words that end it are the same
# ones that end a one-word place, checked word by word in _places().
# Words that follow "i live in" without naming a place: "i live in hope", "i moved in with my
# boyfriend".
HOME_STOP = frozenset("""hope fear pain tears debt misery despair silence darkness denial poverty
sin sin sins the a an my our his her their this that these those with without for at on of two
three four five six ten twenty some any no such what which who whom when where why how much many
more less few lot lots bit town city village flat house home there here it them him me us you
case fact truth style general particular common between limbo fear
tonight today tomorrow yesterday now soon later always never usually often sometimes already still
once twice early late morning evening afternoon night weekend week month year day minute moment while
ago yet again anyway anymore then there here coming going and but so because or plus also
originally born from to into onto towards toward via until till before after about""".split())
# "to" is the one that bites a move: "i moved from leeds to bristol" kept the origin as "Leeds To",
# because the word after a place had to be a stop word to be refused and the destination's own
# preposition was not on the list. The other connectives are the same seam one phrasing over
# ("from leeds into bristol", "from india until 2019"), so the fix is the list and not the move.
# Where they are from, which is not where they live: "i live in bristol now, but im from leeds
# originally" names two places, and a later "where am i from?" asks for the second one.
# The subject and its auxiliary are read as whole words, because half of "were" is "we" and "re":
# with a bare "re" in the auxiliary list, "the parts were from ebay" says the person is from Ebay.
FROM_PLACE = re.compile(
    r"(?:^were\b|\b(?:i'm|i've|i m|i am|i have|i was|im|ive|i|we're|we've|we re|we are|we have|"
    r"we were|weve|we))\s+"
    r"(?:(?:originally\s+|born\s+)?(?:come\s+)?from|born\s+in)\s+"
    r"([a-z][a-z'-]{2,}(?:[ -][a-z][a-z'-]{1,})?)\b", re.I)
# The second from-phrase in one line often has no subject in front of it: "im from leeds,
# originally from bradford though".
FROM_MORE = re.compile(r"\boriginally\s+from\s+([a-z][a-z'-]{2,}(?:[ -][a-z][a-z'-]{1,})?)\b",
                       re.I)
# Where they are from said without the word "from": "i grew up in cork", "i was brought up in
# oslo", "we moved here from poland". The subject has to be the person, so "my mum grew up in
# kerala" is her history and not theirs.
FROM_GROWN = re.compile(
    r"\b(?:i|we)\s+(?:"
    # Where they grew up is named with a preposition, and the preposition can be a soft one:
    # "i grew up near manchester" is from Manchester, not from "Near Manchester".
    r"(?:(?:grew|grows|grow)\s+up|(?:was|were|been|being)\s+(?:brought\s+up|raised))\s+"
    r"(?:in|near|just\s+outside|outside|close\s+to|on)\s+"
    # A place named this way can be wrapped up in a phrase: "i grew up in a village near cork"
    # is Cork.
    r"(?:(?:a|an|the)\s+[a-z][a-z'-]{1,}(?:\s+[a-z][a-z'-]{1,})?\s+"
    r"(?:near|outside|close\s+to|just\s+outside|of)\s+)?"
    # Moving says where from, so the name follows "from" with no second preposition.
    r"|(?:moved|move|moves|moved over|come|came|comes)\s+(?:here|over)\s+from\s+"
    r")([a-z][a-z'-]{2,}(?:[ -][a-z][a-z'-]{1,})?)\b", re.I)
# What someone grew up in is not always a place: "i grew up in care", "i grew up in foster care",
# "i was brought up in a children's home". The place is the name of somewhere, so a common noun
# with an article in front of it ("a council estate", "the countryside") names no place either,
# and a line about it must not leave the person "from Care".
GROWN_NOT_PLACE = frozenset("""care pride poverty debt fear church faith carehomes orphanage
carehome hostel bed sit benefit benefits hospital ill health politness""".split())
GROWN_ARTICLE = frozenset("a an some such every any this that these those".split())
# A place can be wrapped in a phrase - "a village near cork", "a suburb of manchester" - and the
# name after the softer preposition is still where they grew up.
GROWN_NEAR = re.compile(
    r"\b(?:near|outside|close\s+to|just\s+outside|of)\s+([a-z][a-z'-]{2,}(?:[ -][a-z][a-z'-]{1,})?)",
    re.I)


def grown_up_in_a_place(phrase):
    """True when what follows "grew up in" names a place, so "care" and "a council estate" do not.

    The ack side reads the same phrase ("i grew up in care" must not come back as *Care - what's
    it like there?*), so the reading is shared rather than written twice.
    """
    return _grown_up_in_a_place(phrase, "")


def _grown_up_in_a_place(phrase, text):
    """True when what follows "grew up in" is the name of a place and not a way of growing up."""
    words = str(phrase or "").split()
    if not words:
        return False
    low = [word.lower().strip(".,!?;:'\"") for word in words]
    if any(word in GROWN_NOT_PLACE for word in low):
        return False
    near = GROWN_NEAR.search(str(phrase or ""))
    if near and _place_name(near.group(1)):
        return True
    if low[0] in GROWN_ARTICLE:
        return False
    # "i grew up in the Philippines", "we grew up in the UK": the country keeps its article.
    if low[0] == "the":
        return len(low) > 1 and low[1] in COUNTRY_ARTICLE
    return True


# Words that name the first half of a two-word place: "new york", "saint malo".
PLACE_MIDDLE = frozenset("""new old saint st san santa los las la le port cape fort great little
south north east west upper lower mount lake northern southern eastern western united""".split())
# A naming word in lower case keeps the word after it, because that word is part of the name:
# "im going to sri lanka in june" was filed as Sri, and the store answered "Sri is off, then" to
# a person who had just taken back a trip to Sri Lanka. After an ordinary first word the next word
# is not part of a name at all ("going to bed early" is bed, not "Bed Early").
#
# Only a word that is a name and not an ordinary word of the language is read without a capital to
# guide it. "great", "little", "old", "upper", "lower" and "united" are adjectives first, so
# "im going to great lengths to sort this" was filed as a trip to Great Lengths - and, the whole
# point of the reader, answered "You're going to great lengths to sort this. What do you want to
# do while you're there?". "new" is kept because it names a place far more often than it opens a
# phrase in a line about going somewhere ("new york", "new orleans", "new zealand").
PLACE_NAME_FIRST = frozenset("""new saint st san santa los las la le mount lake fort cape
port sri""".split())
PLACE_LOWER_NAMED = re.compile(
    r"\b(?:going to|off to|flying to|fly to|travel(?:l)?ing to|trip to|holiday in|moving to|"
    r"heading to|visit(?:ing)?)\s+(" + "|".join(sorted(PLACE_NAME_FIRST)) + r")\s+"
    r"([a-z][a-z]{2,})\b", re.I)


def _an_everyday_word(word):
    """Whether the word is one of the language's own, so it is not part of a place's name.

    The name after a naming word is a name because it is not a word the person would have used
    on its own: "sri lanka" and "new york" are names, "great lengths" and "new job" are not.
    The plural is looked at too, because a place is not named for a heap of something: "new
    heights" is not a place and "athens" is.
    """
    low = str(word or "").lower()
    if not low:
        return True
    if low in normalize.LEXICON:
        return True
    for tail in ("es", "s"):
        if low.endswith(tail) and len(low) - len(tail) > 2 and low[:-len(tail)] in normalize.LEXICON:
            return True
    return False
# A country people type in capitals, and the article it keeps: "I live in the UK".
COUNTRY_CAPS = {"uk": "UK", "us": "US", "usa": "USA", "uae": "UAE", "states": "States"}
# A country people write with its article, and the article it keeps: "I live in the UK".
COUNTRY_ARTICLE = frozenset("""uk us usa uae netherlands philippines bahamas maldives seychelles
states""".split())
# Words that follow a travel phrase without naming a place: "going to bed", "off to work".
PLACE_VERBS = frozenset("""bed sleep work school town sleep the a an see do get have try start stop
ask tell say make take give look feel stay live move eat drink buy sell pay book plan meet call go
come home there here it that this them him her me us you we my your our their about back out over
be used buy""".split())
# The home phrase above wants the home verb straight after the subject; people also put a word
# or two between it and the place: "I have just moved to Bristol", "we've lived in York for
# years", "I live in a flat in London". This is the fallback for those, and it only ever adds a
# city the home phrase above could not read. The verb has to follow the subject, so "I want to
# live in Spain one day" and "I told you my sister lives in Leeds" are left alone.
HOME_LOOSE = re.compile(
    r"(?i:\b(?:i|we)(?:'?(?:ve|m|re|d)|\s+(?:have|has|had|am|are|was|were))?"
    r"\s+(?:now|still|just|recently|finally)?\s*"
    r"(?:liv(?:e|ing|ed)|mov(?:e|ed|ing)|settl(?:e|ed|ing)|relocat(?:e|ed|ing)|based|staying)\b)"
    r"[^.;!?]{0,30}?\b(?:in|to|at)\s+([A-Z][a-z]+(?:[ -][A-Z][a-z]+)?)\b")

# "Tokyo and Kyoto", "Rome, not Florence": a short line that names places on its own.
SHORT_LIST = re.compile(r"^\W*(?:[A-Z][a-z]+)(?:\s*(?:,|and|or)\s*[A-Z][a-z]+)+\W*$")

# ---------------------------------------------------------------------------
# diet, allergies, pets, budget, family

# A denial is the opposite of the fact it names, in the same words: "im not allergic to nuts"
# has "allergic to nuts" in it, and "im not coeliac" has the condition. The negator right in
# front of the words is what tells them apart, and getting this wrong fills the store with the
# one thing the person said they do not have.
# The negator is typed without its apostrophe as often as with it - "he isnt allergic to nuts",
# "she doesnt have one" - and the apostrophe-only reading heard no negation at all: the line
# was filed as the opposite fact, so "my son isnt allergic to nuts" was kept as an allergy of
# his and answered with the nut-free shopping lecture.
DENIAL_WORDS = re.compile(r"(?:\bnot|\bnever|\bno longer|\b(?:is|are|was|were|do|does|did|can|"
                          r"could|would|should|has|have|had|wo|ca|ai)n'?t|\baint)\s+"
                          r"(?:really\s+|actually\s+|even\s+)?(?:a\s+|an\s+|any\s+|\bat all\s+)?$", re.I)


# "im not coeliac", "i'm no longer vegetarian", "im not allergic to nuts": the fact they say
# they do not have. Kept in the shape extract() files it under, so the store can drop it.
DENIAL_OF = re.compile(
    r"\b(?:i(?:m|'m| am)|we(?:re|'re| are))\s+(?:not|never|no longer)\s+"
    r"(?:really\s+|actually\s+|even\s+)?(?:a\s+|an\s+|any\s+)?"
    r"(?:(?P<food>allergic to\s+[a-z]+(?:(?:,| and| or)\s+[a-z]+){0,3})"
    r"|(?P<condition>coeliac|celiac|diabetic|asthmatic|epileptic|anaemic|anemic|"
    r"lactose intolerant|gluten intolerant)"
    r"|(?P<diet>vegan|vegetarian|pescatarian|flexitarian|veggie|plant[- ]based))", re.I)

# A diet taken back rather than a way of eating denied: "im not on a diet any more", "im off the
# diet now", "i stopped doing keto", "ive given up the diet". DENIAL_OF only hears "im not
# vegetarian", so "im on a diet" then "im not on a diet any more" left the fact in the store and
# the next "what diet am i on" answered "You told me you're on a diet" - the line they had just
# taken back, said back to them.
# The plans people follow by name, spelled the way they type them. A plan said with on, doing
# or trying is a diet even when the word "diet" never comes, so the list is what makes "im on
# slimming world" a diet the store can say back instead of denying it a turn later. It is kept
# in one place because the take-back ("i stopped slimming world") and the named read ("im doing
# intermittent fasting") have to know the same plans.
DIET_PLANS = (r"(?:slimming world|weight watchers|intermittent fasting|whole ?30|omad|"
              r"carnivore|dukan|south beach|fast 800|5:2|16:8|4:3|"
              r"keto|paleo|atkins|low[- ]carb|mediterranean|gluten[- ]free|dairy[- ]free|"
              r"plant[- ]based|pescatarian|flexitarian|vegan|vegetarian)")
DIET_PLAN_WORD = (r"(?:(?:slimming world|weight watchers|intermittent fasting|whole ?30|omad|"
                  r"carnivore|dukan|south beach|fast 800|5:2|16:8|4:3|"
                  r"keto|paleo|atkins|low[- ]carb|mediterranean|gluten[- ]free|dairy[- ]free|"
                  r"plant[- ]based|vegan|vegetarian)|diet|dieting)")
DIET_OFF = re.compile(
    r"\b(?:i|we)\s*(?:'m|'re|m|re|am|are)\s+(?:not|no longer)\s+(?:on|doing)\s+"
    r"(?:a\s+|the\s+|an\s+)?(?P<plan>" + DIET_PLAN_WORD + r")\b"
    r"|\b(?:i|we)\s*(?:'m|'re|m|re|am|are)\s+(?:off|done with)\s+"
    r"(?:the\s+|a\s+|my\s+|that\s+)?(?P<off>" + DIET_PLAN_WORD + r")\b"
    r"|\b(?:i|we)\s+(?:came|come|came off|got|went)\s+off\s+"
    r"(?:the\s+|a\s+|my\s+)?(?P<gone>" + DIET_PLAN_WORD + r")\b"
    r"|\b(?:i|we)(?:'ve|ve|'d|d|\s+have|\s+had)?\s+"
    r"(?:stopped|quit|gave up|given up|packed in)\s+"
    r"(?:the\s+|my\s+|this\s+|on\s+)?(?:being\s+|doing\s+|eating\s+|going\s+)?"
    r"(?P<quit>" + DIET_PLAN_WORD + r")\b", re.I)

# The take-back for pets. A pet is nobody's until the line says it is theirs, so a negation is
# not enough on its own: "i dont like my cat today" has the words "dont" and "cat" in it and
# nothing lives in the house on that.
# The words that can end a statement, so "i have a cat and im not allergic to nuts" takes the
# nuts and only the nuts.
CLAUSE_EDGE = re.compile(r"[.;!?]|\b(?:and|but|so|because|though|although|which|while)\b|,", re.I)
# Possession, not feeling: have, own, keep, got, and the words that say it is gone.
NOT_HAVE = re.compile(r"\b(?:don'?t|do not|doesn'?t|doesnt|didn'?t|didnt|never|not|no longer|"
                      r"haven'?t|havent|hadn'?t|hadnt)\s+(?:have|has|had|own|owns|owned|keep|"
                      r"kept|got)\b|\b(?:have|has|had|got)\s+(?:no|not|never)\b",
                      re.I)
# The half of `NOT_HAVE` that a held animal is taken by: the negation is carried by a word that
# means having ("dont have", "never had", "no longer own"), so the animal that follows the clause
# is the thing that is gone. The other half of `NOT_HAVE` ("has never liked it") stays for the
# reader that asks whether a line brings an animal in, where the answer is no either way.
NOT_HAVE_LONGER = re.compile(
    r"\b(?:don'?t|do not|doesn'?t|doesnt|didn'?t|didnt|never|not|no longer|"
    r"haven'?t|havent|hadn'?t|hadnt)\s+(?:have|has|had|own|owns|owned|keep|"
    r"kept|got)\b", re.I)
# "he has no dog" says they have not got one, and it is a take-back. "he has never liked it",
# "she has no interest in walks" and "he has no dog friends" say what the animal is like, and
# `NOT_HAVE` read all of them as the same denial: the store took the animal off its own record
# and answered "Right - no cat, then." to somebody who had just described their cat. The line
# that takes an animal back names the animal as the thing that is gone, so the words after the
# negation are what decides, and a bare verb after it is not a possession at all.
HAVE_NONE = re.compile(
    r"\b(?:have|has|had|got)\s+(?:no|not|never)\s+"
    r"(?:(?:any|a|an|the|my|our|this|that|those|these)\b|pets?|dogs?|cats?|pupp(?:y|ies)|"
    r"kittens?|rabbits?|hamsters?|parrots?|goldfish|fish|horses?|animals?|guinea\s+pigs?|"
    r"gerbils?)\b", re.I)
# A kind word that is the first half of a compound names something else: "he has no dog friends"
# is about the friends, and the dog at the front of it stays theirs.
A_COMPOUND_AFTER = re.compile(r"\s+[a-z]+s\b", re.I)
# "without" is a take-back only when the animal itself is what follows it: "we get by without a
# car" is about the car, and "how do i help rex settle without him" is about the one that has
# gone, not the one they still have. Read as a bare "not", any "without" took the animal they
# were telling the chat about.
WITHOUT_ANIMAL = re.compile(
    r"\bwithout\s+(?:(?:a|an|any|the|my|our|his|her|their|these|those)\s+)?(?:[a-z-]+\s+)?"
    r"(?:pets?|dogs?|cats?|pupp(?:y|ies)|kittens?|rabbits?|hamsters?|parrots?|goldfish|fish|"
    r"horses?|animals?|guinea\s+pigs?|gerbils?)\b", re.I)
# A bare "not" right in front of the animal still names it: "i have a cat, not a dog".
NOT_JUST = re.compile(r"\bnot\s+(?:(?:a|an|the|any|my|our)\s+)?$", re.I)
# A take-back in front of the animal is a take-back even though nothing says "have": "forget the
# dog", "forgot the cat", and a bare "no dog" is the shortest way to say it. Such a line is not
# introducing an animal, and a store that read it as one invented a dog nobody had mentioned and
# then filed it under `pets_gone`: "forget the dog" answered "what pets do i have" with "You've
# got a cat called Tom and a dog".
#
# Only the words that take the animal away are here. "never mind the dog", "ignore the dog" and
# "drop the cat" ask the chat to move on and leave the animal where it was - reading them as a
# take-back deleted a dog the person still had and then told them "You don't have your dog Rex
# any more" - and a bare "no" is the take-back only when the animal ends the line, so the rules
# people state ("no dogs allowed in my flat") are not one. `taken_back_before` reads both.
TAKEN_BACK_BEFORE = re.compile(
    r"\b(?:forget|forgot|forgetting)\s+(?:(?:about|with)\s+)?(?:(?:a|an|the|any|my|our|that|"
    r"this|those|these)\s+)?$", re.I)
# A bare "no" or "not" in front of the animal is the shortest take-back there is, and it is only
# that when the animal is the whole line: "no dog", "no, no dog".
BARE_NO = re.compile(r"^\s*(?:(?:no|not|nope)\b[\s,.]*){1,2}(?:(?:a|an|the|any|my|our)\s+)?$",
                     re.I)
# The same "no" in front of a determiner, with no comma after it, is the person naming the animal
# they mean instead: "no a cat" is "no, a cat" typed the way people type it, and the cat is the one
# they have. Read as a take-back it answered "Right \u2014 no cat." - the opposite of the line - to
# somebody who had just said they had a dog and meant they had a cat.
NO_THEN_A_THING = re.compile(r"^\s*(?:no|nope)\b[\s,.]*(?:a|an|the|my|our|your|his|her|their)\s*$",
                             re.I)
# A phrase can take a pet with no "not" at all: "we had to give the dog away".
GIVEN_AWAY = re.compile(r"\b(?:gave|give|given|giving|took|take|taken|returned|"
                        r"rehom(?:e|es|ed|ing)|got rid of)\b[^.;!?]{0,24}?\b(?:away|up|back|"
                        r"to a (?:friend|neighbour|neighbor|rescue)|to (?:my|his|her|their))\b|"
                        r"\brehom(?:e|es|ed|ing)\b[^.;!?]*", re.I)
# "no pets" takes every animal back, with none named.
NO_PETS = re.compile(r"\b(?:no|not got any|don'?t have any|dont have any|without any|"
                     r"never had any|no longer have any)\s+pets?\b", re.I)
EVERYTHING = "*"
# A pet that died is one they no longer have, but it is not a take-back to say back to them:
# the loss is answered warmly by the feelings side, and the store only has to stop handing the
# animal back. "my cat died last month" then "what pets do i have" must not say they have a cat.
DIED = re.compile(r"\b(?:died|dead|passed (?:away|on)|put (?:\S+ ){0,3}?down|"
                  r"put (?:\S+ ){0,3}?to sleep|euthanis(?:ed|e)|euthaniz(?:ed|e)|"
                  r"have (?:him|her|it|them) put (?:down|to sleep)|"
                  r"didn'?t make it|didnt make it|no longer with us)\b", re.I)
# A pronoun pointing at the animal the line already named: "my dog is called rex, we dont have
# him any more", "we had to put her to sleep".
ANIMAL_DEATH = re.compile(r"\b(?:put (?:\S+ ){0,3}?(?:down|to sleep)|euthan\w*"
                           r"|no longer with us|didn'?t make it|had to be put)", re.I)
# "both cats died", "we lost all of them": a death said over the whole lot takes the lot. Any
# other death of a kind takes one animal, because "my cat died" from someone with two cats is one
# of them, not the two.
LOSS_ALL = re.compile(r"\b(?:both|all of them|all of the|all my|all our|every one|the pair|"
                      r"our pairs?)\b", re.I)
PET_PRONOUN = re.compile(r"\b(?P<pron>him|her|it|them|those|they|he|she)\b", re.I)
PLURAL_PRONOUN = frozenset("them those they".split())
# A line about what they think, remember or said is not a line about what is. "i dont think i
# have a cat" and "i never said i have a dog" are a doubt and a record, and taking the animal
# back on either loses something the person still has: nothing later puts a pet back.
HEDGE = re.compile(r"\b(?:don'?t|do not|didn'?t|did not|cant|can'?t|couldn'?t|could not|"
                   r"wouldn'?t|would not|might not|may not)\s+(?:think|know|remember|recall|say|"
                   r"mean|believe|reckon|suppose|guess|be sure|be certain)\b|"
                   r"\bnot sure|\bnot certain|\bno idea|\bprobably not|\bnot that i know|"
                   r"\bi doubt|\bdoubt it|\bnever said|\bnever told|\bnever mentioned|"
                   r"\bdidn'?t say|\bdidn'?t tell|\bdidn'?t mention|\bhaven'?t said|"
                   r"\bhavent said|\bhaven'?t told|\bhavent told|\bnot what i said", re.I)

ALLERGY = re.compile(r"\ballergic to ([a-z]+(?:[ ,]+(?:and )?[a-z]+){0,3})", re.I)
# The correction shape: the right thing, then the wrong one it replaces. "im allergic to soya
# not peanuts" keeps soya and takes peanuts back out of the store, because a person correcting
# an allergy must be believed - advice for an allergy they have just corrected away is the one
# kind of wrong answer that can hurt.
CONTRAST = re.compile(r"\b(?:allergic to|cant eat|can'?t eat|cannot eat|can not eat)\s+[a-z]+"
                      r"(?:(?:,| and| or)\s+[a-z]+){0,3}[\s,]+not\s+(?P<old>[a-z]+"
                      r"(?:(?:,| and| or)\s+[a-z]+){0,3})", re.I)
# The same fact said the other two ways people say it: "i cant eat nuts", "i have a dairy
# allergy". "Can't" is an allergy or an intolerance; "don't eat" below is a diet.
CANNOT_EAT = re.compile(r"\b(?:can'?t|cannot|can not)\s+(?:eat|have|drink|touch)\s+"
                        r"([a-z]+(?:[ ,]+(?:and |or )?[a-z]+){0,3})", re.I)
X_ALLERGY = re.compile(r"\b([a-z]+)\s+allerg(?:y|ies)\b", re.I)
# The word in front of "allergy" names the allergen only when it is a thing. In a question about
# allergies the word there is a verb, because the line is about how people come by them: "why do
# we get allergies", "how do you catch allergies", "can you develop an allergy". Filed as a fact,
# "get allergies" becomes an allergy called "get", and the store then says it back for the rest of
# the conversation - worse than the denial it replaces, because a denial can be forgotten and a
# fact cannot. The verbs that turn up in that one place are a closed set.
NOT_AN_ALLERGEN = frozenset("""get gets getting got gotten have has had having develop develops
developed developing catch catches caught catching treat treats treated treating prevent prevents
prevented test tests tested testing cause causes caused causing trigger triggers triggered avoid
avoids avoiding manage manages managing notice notices noticed noticing control controls
controlled risk suffer suffers suffered experience make makes made become becomes became""".split())
# "im vegetarian" is how most people type it, so the apostrophe and the "am" are optional
# and "a vegetarian" is allowed.
VEGETARIAN = re.compile(r"\b(i(?:m|'m| am)|he(?:s|'s| is)|she(?:s|'s| is)|we(?:re|'re| are))\s+"
                        r"(?:a |an )?(vegan|vegetarian|pescatarian|flexitarian|veggie|veg|"
                        r"plant[- ]based)\b", re.I)
NO_MEAT = re.compile(r"\b(?:i|we) ?(?:dont|don'?t|do not|never|no longer) eat\s+"
                     r"(?:any |any more |more )?([a-z]+(?:(?:,| or| and) "
                     # A comma joins two foods ("i dont eat fish, shellfish") or opens a new
                     # clause ("i dont eat cashews, im allergic"). The second word has to be
                     # a food, so a subject word after the comma ends the list: read as the
                     # diet, "no cashews, im" is handed back as "you don't eat cashews, im".
                     r"(?!i\b|im\b|i'm\b|ive\b|i'd\b|we\b|we're\b|and\b|but\b|so\b)[a-z]+)?)", re.I)
# Drinking is the other half of what goes on the table, and the store only kept the eating half.
# "i dont drink" filed nothing and got the stock line, "ive given up drinking" the same, and "im
# teetotal" was read as a name - "Nice to meet you, Teetotal." A thing someone does not drink is a
# diet like a thing they do not eat, and a diet is what the answers that keep food off the plate
# read. The verb with no object after it is alcohol: "i dont drink" is how people say they do not
# drink it.
DRINK = frozenset("""alcohol booze wine wines beer beers lager lagers cider spirits gin vodka
whisky whiskey rum prosecco champagne cocktails cocktail sherry brandy""".split())
NO_DRINK = re.compile(
    r"\b(?:i|we)\s+(?:really\s+|just\s+|actually\s+)?"
    r"(?:don'?t|do not|dont|never|no longer)\s+(?:really\s+|just\s+|actually\s+)?drink\b"
    # A shortfall is not a diet: "i dont drink much water" is someone who wants to drink more.
    r"(?!\s+(?:enough|much|too much|a lot|loads|that much|as much|plenty|water|it\b))"
    # "any more" and "at all" are how a thing given up is said; "at the moment" and "these days"
    # are a stretch of time and not a way of life, and a person who is off it for a while is
    # answered about refusing a drink, which is the answer that turn wants.
    r"(?:\s+(?:any\s?more|anymore|at\s+all|now))?\s*[.!]*$", re.I)
# The same said as something given up: "ive given up drinking", "i stopped drinking", "i quit",
# "im on the wagon", "im not drinking at the moment".
# What follows the verb decides whether the line is about drink: "i stopped drinking in january"
# gave up the drink, and "i stopped drinking coffee" gave up the coffee, whose answer is the
# caffeine one and would be lost if this filed a diet. So the verb has to be about the drink and
# nothing else - the sentence ends, or it goes on about when, or why.
GAVE_UP_DRINK = re.compile(
    r"\b(?:i|we)\s*(?:have|'ve|had|ve)?\s*"
    r"(?:given\s+up|gave\s+up|quit|quitted|stopped|packed\s+in|cut\s+out)\s+"
    r"(?:the\s+|my\s+|all\s+)?(?:drinking|drink|alcohol|booze)\b"
    r"(?=\s*(?:[.,;!?]|$|\s+(?:any\s?more|anymore|at\s+all|now|for\s+good|and|but|so|"
    r"because|since|when|after|before|\d+\s+(?:years?|months?|weeks?|days?)(?:\s+ago)?|"
    r"years?\s+ago|months?\s+ago|weeks?\s+ago|ago|"
    r"in\s+\w+|at\s+\w+|last\s+\w+|this\s+\w+|on\s+\w+|over\s+\w+)))", re.I)
# A drink given up by name: "i stopped drinking wine" is the same fact as "i dont drink wine", and
# only names from the drinks people give up on purpose, so "i stopped drinking coffee" is not it.
GAVE_UP_DRINK_THING = re.compile(
    r"\b(?:i|we)\s*(?:have|'ve|had|ve)?\s*"
    r"(?:given\s+up|gave\s+up|quit|quitted|stopped|packed\s+in|cut\s+out)\s+"
    r"(?:the\s+|my\s+|all\s+)?drinking\s+"
    r"(?P<thing>[a-z]+(?:\s+(?:or|and)\s+[a-z]+){0,3})", re.I)
NOT_DRINKING = re.compile(
    r"\b(?:i'?m|i\s+am|we'?re|we\s+are)\s+(?:a\s+|an\s+)?(?:"
    # "im not drinking" is alcohol and "im not drinking much water these days" is a shortfall
    # about water: what follows the verb decides which, so the quantity or the drink after it
    # takes the line back to the hydration question it was asking.
    r"not\s+drinking(?!\s+(?:enough|much|too\s+much|a\s+lot|loads|as\s+much|that\s+much|"
    r"water|anything|any\s+water|it\b|at\s+the\s+(?:moment|minute)|these\s+days|for\s+now"
    r"|this\s+(?:week|month|year)|till\b|until\b))"
    # Only the bare shape and the one that says it is for good: "im not drinking at the moment"
    # is a stretch of time, and the answer for it is how to turn a drink down.
    r"(?:\s+(?:any\s?more|anymore|now))?"
    r"|off\s+the\s+(?:booze|drink)"
    r"|on\s+the\s+wagon|teetotal(?:ler)?|tee-total|non-drinker|nondrinker)\b", re.I)
# A named drink they do not take, and only the drinks that are a choice about alcohol: water, tea
# and coffee are habits, and "i dont drink water" is a shortfall rather than a diet.
NO_DRINK_THING = re.compile(
    r"\b(?:i|we)\s+(?:really\s+|just\s+|actually\s+)?"
    r"(?:don'?t|do not|dont|never|no longer)\s+drink\s+"
    r"(?P<thing>[a-z]+(?:\s+(?:or|and)\s+[a-z]+){0,3})", re.I)


def _the_drink_they_do_not_take(text):
    """What the line says they do not drink, as the word a diet says "no" to, or "".

    "i dont drink" names no drink and means alcohol - that is the idiom - and so does a drink
    given up ("ive given up drinking", "im teetotal"). A named drink counts only when it is one
    of the drinks a person gives up on purpose, so a shortfall about water stays a shortfall.
    """
    low = " ".join(str(text or "").split())
    if not low:
        return ""
    if NOT_DRINKING.search(low) or GAVE_UP_DRINK.search(low) or NO_DRINK.search(low):
        return "alcohol"
    for pattern in (NO_DRINK_THING, GAVE_UP_DRINK_THING):
        drank = pattern.search(low)
        if drank:
            thing = _finish(drank.group("thing"))
            words = [word for word in re.split(r"[ ,]+", thing.lower())
                     if word not in ("or", "and")]
            if words and all(word in DRINK for word in words):
                return thing
    return ""


# meat words: only these make "i dont eat ..." a vegetarian, not "i dont eat dairy".
MEAT = frozenset("""meat meats beef chicken pork lamb bacon ham sausages sausage fish seafood
prawns shellfish turkey duck goose venison steak mince gelatine gelatin""".split())
ANIMALS = frozenset("""dog puppy cat kitten rabbit hamster parrot goldfish fish horse pet""".split())
# What a diet is said to be "free from". A person says it of themselves ("im dairy free") and of
# somebody else ("my mum is lactose free"), and it is the same diet either way, so the words live
# in one list and both readers use them.
FREE_FROM = r"(?:dairy|gluten|lactose|nut|egg|sugar|soya|soy|wheat|yeast)[- ]free"
DIET_FREE_WORDS = frozenset("dairy gluten lactose nut egg sugar soya soy wheat yeast"
                            .split())
# "she doesnt eat meat", "my mum is vegetarian": what someone else eats is a fact about them, so
# it is kept against that person (memory["others"]) and never becomes the user's own diet. The
# subject can come first or be named, so both "my mum doesnt eat meat" and "she is vegetarian"
# land on the mum she was just talking about.
OTHER_DIET = re.compile(
    r"(?<!\w)(?P<subj>(?:he|she|they)(?:'s|'re|s|re)?|(?:my|his|her|their|our)\s+\w+)(?!\w)"
    r"[^.,;!?]{0,24}?"
    r"(?:(?:is|are|'s|'re|s|re)?\s*(?:a |an )?(?P<free>" + FREE_FROM + r")(?!\w)"
    r"|(?:is|are|'s|'re|s|re)?\s*(?:a |an )?(?P<word>vegan|vegetarian|pescatarian|flexitarian|"
    r"veggie|gluten[ -]free|dairy[ -]free|lactose[ -]free|wheat[ -]free|sugar[ -]free|"
    r"low[ -]carb|plant[ -]based|keto|paleo|carnivore)(?!\w)"
    r"|(?:doesn'?t|does not|doesnt|don'?t|do not|dont|never|won'?t|wont|can'?t|cant)\s+"
    r"eats?\s+(?:any\s+|any more\s+|much\s+)?"
    r"(?P<food>[a-z]+(?:\s+(?:or|and)\s+[a-z]+)?))", re.I)
# The same fact turned back: "my son doesnt eat fish" then "actually he eats fish", "my wife
# hates mushrooms" then "actually she loves mushrooms". Said on its own the second line is no
# news - "he eats fish" states nothing a store has to keep - so it is read only as a correction,
# and only the store can tell whether the person has anything on record for the line to lift.
# Without this the store went on answering "what does my son eat" with "Your son doesn't eat
# fish.", which is the opposite of the last thing the person said.
THEIR_BACK = re.compile(
    r"(?<!\w)(?P<subj>(?:he|she|they)(?:'s|'re|s|re)?|(?:my|his|her|their|our)\s+\w+)(?!\w)"
    r"(?P<gap>[^.,;!?]{0,24}?)\b(?P<verb>eats|eat|likes|like|loves|love|does|do|did)\b\s+"
    r"(?:(?P<emph>eat|eats|like|likes|love|loves)\s+)?"
    r"(?:now\s+|actually\s+|really\s+)?"
    r"(?P<food>them|it|that|[a-z]+(?:\s+(?:or|and)\s+[a-z]+)?)", re.I)
# The words that make such a line a correction of what they said rather than a new sentence.
# "he eats fish" with none of them is not read at all.
A_CORRECTION = re.compile(r"\b(?:actually|no|nope|sorry|wait|oh|now|again|rather|really|"
                          r"these\s+days|after\s+all)\b", re.I)
# A negator between the person and the verb says the line keeps the restriction rather than
# lifting it: "he doesnt eat fish now" and "he wont eat fish again" are not take-backs.
A_NEGATOR_IN_BETWEEN = re.compile(r"\b(?:not|never|no\s+longer|n'?t|nt)\b|\wnt\b", re.I)
# "a nut allergy" is one nut too many when it is said back: a countable allergen is stored in
# the plural, which is how people list them ("allergic to nuts").
ALLERGEN_PLURALS = {"nut": "nuts", "peanut": "peanuts", "walnut": "walnuts",
                    "hazelnut": "hazelnuts", "cashew": "cashews", "almond": "almonds",
                    "prawn": "prawns", "egg": "eggs", "strawberry": "strawberries",
                    "kiwi": "kiwis", "berry": "berries", "sesame": "sesame", "soya": "soya"}
# A line that only names one more thing ("and milk too", "plus cheese", "i think soya as
# well") states no fact of its own: it has no verb and no subject. Read against what is already
# on record it is that same fact with one more thing in it. Nothing in the line says the thing is
# food, so the words decide: only what people name as a food or an allergen counts, and a line
# that names anything else ("and my sister too", "and work is awful too") adds nothing.
ONE_MORE_FOODS = frozenset("""
    milk dairy cheese butter cream yoghurt yogurt lactose egg eggs
    nut nuts peanut peanuts walnut walnuts hazelnut hazelnuts cashew cashews almond almonds
    pistachio pistachios pecan pecans brazil macadamia chestnut chestnuts pine
    wheat gluten flour bread pasta semolina spelt barley rye oats oat couscous noodles
    soya soy tofu sesame tahini mustard celery celeriac lupin corn maize rice potato potatoes
    fish salmon cod tuna haddock prawn prawns shellfish crab crabs lobster mussels oysters
    squid scallops clam clams anchovy anchovies sardine sardines mackerel trout
    meat chicken beef pork lamb bacon ham sausage sausages turkey duck venison gelatine
    gelatin yeast sugar honey chocolate coffee caffeine alcohol wine beer vinegar
    feta halloumi parmesan mozzarella cheddar brie ricotta paneer stilton gouda edam
    strawberry strawberries kiwi kiwis berry berries banana bananas apple apples
    pear pears peach peaches plum plums cherry cherries grape grapes melon melons
    mango mangoes pineapple avocado coconut tomato tomatoes onion onions garlic
    pepper spices spice curry chilli chili cinnamon cloves ginger mint
    sulphites sulphite sulfites sulfate sulphur sulfites msg aspartame sweetener
    preservatives colourings colouring dye colour color additives
    """.split())
# The lead-in and the tail a line uses when it is adding to what was just said. Both come off,
# again and again, so "oh and also i think maybe milk as well" is the one word "milk".
ONE_MORE_HEAD = re.compile(
    # "actually shellfish too", "sorry, sesame as well": the word that marks the line as an
    # addition is not part of the thing being added. Without "actually" the whole line was read
    # as a maybe that names nothing, so a real allergy was dropped outright.
    r"^(?:(?:it'?s|its|it is|that'?s|thats|this is|these are|those are)|and|also|plus|oh|right|but|"
    r"so|yeah|yes|then|actually|sorry|true|wait|no wait|"
    r"hold on|i think|i reckon|i suppose|maybe|probably|possibly|i think maybe)\b[\s,]*", re.I)
ONE_MORE_TAIL = re.compile(r"[\s,]*(?:\btoo\b|\bas well\b|\balso\b|\bi suppose\b)[\s.!?]*$",
                           re.I)
# A want, a dislike, a maybe, or an animal from their childhood puts no animal in the house.
# "i dont want a dog", "i hate cats", "im thinking about getting a dog" and "i had a dog growing
# up" all used to store one, so the next ask answered "You've got a dog", and a take-back on the
# line then had an animal to hand back that the person never claimed. The cue counts only in the
# same clause as the animal, and only up to the animal.
NOT_THEIRS = re.compile(r"\b(?:want|wants|wanted|need|needs|needed|fancy|fancied|"
                        r"would like|wish i|wishes|hate|hates|hated|dislike|dislikes|"
                        r"disliked|can'?t stand|cant stand|not a fan of|afraid of|scared of|"
                        r"thinking (?:about|of)|thought (?:about|of)|considering|considered|"
                        r"might|maybe|perhaps|hoping|hope to|planning (?:to|on)|plan to|"
                        r"one day|some day|someday|eventually|dream(?:ing)? of|"
                        r"looking at|shopping for|researching|used to|use to|"
                        # "shes been asking for a hamster", "im after a kitten", "the kids are
                        # desperate for a dog": a want said as an ask. Without these the animal
                        # was read as one they have, and the store answered "You've got a
                        # hamster" for a hamster the person was asking about buying.
                        r"asked for|asking for|been asking|begging for|desperate for|"
                        r"mad on|mad for|keen on|keen to get|after a|after an|"
                        r"growing up|as a kid|as a child|when i was (?:little|younger|a kid|"
                        r"a child|small))\b", re.I)
# A want in front of the animal is not a take-back: "i want a labrador" and "i might get a dog"
# name an animal the person would like, and the store has to keep it out of the house without
# also reading the line as an animal being handed back - "No dog, then." answered a wish, which
# is the bot agreeing to take away a dog nobody had. The wish is recorded beside the animal so a
# module that reads `not_theirs` can tell the two apart: bot/memory/ack declines a wish and lets
# the composer answer what they would do with one.
A_WISH = re.compile(r"\b(?:want|wants|wanted|would like|wish i|wishes|fancy|fancied|"
                    r"need|needs|needed|thinking (?:about|of)|thought (?:about|of)|considering|"
                    r"considered|might|maybe|perhaps|hoping|hope to|planning (?:to|on)|plan to|"
                    r"one day|some day|someday|eventually|dream(?:ing)? of|looking at|"
                    r"shopping for|researching|going to get|gonna get)\b", re.I)


# The same in the words that come after the animal: "i had a dog growing up", "a cat years ago".
NOT_THEIRS_AFTER = re.compile(r"^\s*(?:,?\s*(?:when i was|as a (?:kid|child)|growing up|"
                              r"years ago|back (?:then|when)|as a young|later on))\b", re.I)
# Possession is what makes the animal theirs, and it is said with an owner word: "i have a dog",
# "my dog", "our cats", "we got a puppy". A want that names no owner is only a want.
THEIRS_WORD = re.compile(r"\b(?:my|our|their|his|her|have|has|had|got|own|owns|owned|keep|"
                         r"keeps|kept|walk|walks|walked|feed|feeds|fed|bought|rescued|"
                         r"adopted|rehomed)\b", re.I)


# A pet on its way is not a pet in the house. "we are getting a puppy next week" put a puppy in
# the store, so "what pets do i have" answered "You've got a puppy" about one still with its
# mother, and the pet tail asked how long it had been with them. Only the words that buy or
# collect an animal count, and only the same clause, so "we got a puppy" (already theirs) and
# "i am getting the dog out for a walk" (a dog of theirs) are untouched.
# Only the doing, never the noun: "a rescue dog" and "a rescue greyhound" name a dog of theirs,
# and reading "rescue" as the thing they are doing took the dog out of the store, so the next
# "what should i feed him?" had no dog to answer about.
COMING_HOME = re.compile(r"\b(?:getting|adopting|rehoming|picking (?:up|out)|collecting|"
                         r"bringing home|waiting for)\b", re.I)
# Between the word and the animal, only an article or a size can stand: "getting a puppy" and
# "getting two kittens" name an animal that is coming, "getting the dog out" and "getting our
# dog used to it" name one that is already theirs.
ON_ITS_WAY_BETWEEN = re.compile(r"^\s*(?:(?:a|an|another|one|two|three|four|five|some|a "
                                r"rescue|a new|some new|my new|our new|the new|a little|"
                                r"a small|[0-9]+)\s+)*$", re.I)


def _coming_home(text, start):
    """True when the animal in the line is one they are getting, not one they have."""
    window = CLAUSE_EDGE.split(text[max(0, start - 60):start])[-1]
    for cue in COMING_HOME.finditer(window):
        between = window[cue.end():]
        if not ON_ITS_WAY_BETWEEN.match(between):
            continue
        return True
    return False


def _only_wanted(text, start, end):
    """True when the animal is one they want, dislike or had once, not one they have.

    "i dont want a dog" and "i hate cats" name an animal the person does not have; "im thinking
    about getting a dog" and "i had a dog growing up" name one they may have later or had once.
    Storing either one answers "You've got a dog" to the next ask, which is the store claiming a
    pet for them, and it is also what let a take-back hand back an animal nobody mentioned.
    """
    window = CLAUSE_EDGE.split(text[max(0, start - 60):start])[-1]
    for cue in NOT_THEIRS.finditer(window):
        # "i want to train my dog" and "we are thinking about our cat" keep the animal: the
        # owner word after the want is what says it is already theirs.
        if THEIRS_WORD.search(window[cue.end():]):
            continue
        return True
    return bool(NOT_THEIRS_AFTER.match(text[end:end + 30]))


def _not_theirs(animal, text, start, end):
    """The record for an animal the person does not have, marked, and a wish marked as a wish."""
    record = {"animal": animal, "name": None, "not_theirs": True}
    if _a_wish_for(text, start):
        record["wanted"] = True
    return record


def _a_wish_for(text, start):
    """True when the animal is one they would like rather than one taken away.

    "i want a labrador", "im thinking about getting a cat" and "i might get a greyhound" all put
    no animal in the house, and none of them takes one away either. `_only_wanted` reads them
    together with "not the dog" and "forget the cat", and the modules that answer a take-back
    ("Right - no dog, then") need the two told apart.
    """
    window = CLAUSE_EDGE.split(text[max(0, start - 60):start])[-1]
    if THEIRS_WORD.search(window):
        return False
    return bool(A_WISH.search(window))


# "im coeliac", "i am diabetic": a condition, kept as a fact in its own right.
CONDITION = re.compile(r"\b(?:i(?:m|'m| am)|we(?:re|'re| are))\s+(?:a |an )?"
                       r"(coeliac|celiac|diabetic|asthmatic|epileptic|anaemic|anemic|"
                       r"lactose intolerant|gluten intolerant)\b", re.I)
# The slang word is stored as the plain one, so the reply never says "you're veggie".
# Only the slang word is folded: "plant based" rules out dairy and eggs too, so it is not a
# synonym for vegetarian and is kept as it was said.
DIET_NAMES = {"veggie": "vegetarian"}
# How people describe what they eat. None of these is a name, however short the line is:
# "im veg" and "im plant based" are diets, not an introduction.
DIET_WORDS = frozenset("""vegan vegetarian veggie veg pescatarian flexitarian plant based raw
gluten-free dairy-free lactose-free nut-free egg-free sugar-free soya-free soy-free
wheat-free yeast-free keto paleo low-carb carnivore""".split())
# "im on a gluten free diet", "ive been doing the keto diet": the diet is named as a diet.
# A word about not drinking is a word about the person, not what they are called: "im teetotal"
# was read as an introduction and the bot answered "Nice to meet you, Teetotal." The diet reader
# files the same words as the drink they have given up, so the two agree about the line.
SOBER_WORDS = frozenset("teetotal teetotaller tee-total non-drinker nondrinker sober".split())
DIET_NAMED = re.compile(r"\b(?:i'm|im|i've|ive|i am|i have)\b(?:\s+been)?(?:\s+\w+){0,2}?\s+"
                        r"(?P<named>" + DIET_PLANS + r")\s+diet\b", re.I)
# "im on a diet", "ive started a diet", "im doing keto": on / doing / trying says the person
# has taken it up, so a plan named there is a diet even when the word "diet" never comes, and
# a diet with no name is still a diet. Both are what the person eats, which is what the store
# keeps; without them "im on a diet" then "do you remember my diet" denies the diet they said.
DIET_UNDERWAY = re.compile(
    r"\b(?:i(?:m|'m| am)|we(?:re|'re| are)|i(?:'ve|ve| have))\b(?:\s+been)?\s+"
    r"(?:(?:on|doing|trying|starting|started|back on|gone)\s+(?:a\s+|the\s+|an\s+)?"
    r"(?:(?P<named>" + DIET_PLANS + r")\b|(?P<diet>diet)\b)"
    r"|(?P<dieting>dieting)\b)", re.I)
# Some plans are said without on or doing and without the word "diet": "im dairy free", "im
# keto", "im low carb". The plan word after "im" is the diet there.
DIET_BARE = re.compile(
    r"\b(?:i'm|im|i am|i've been|ive been)\s+(?P<bare>" + FREE_FROM + r"|"
    r"low[- ]carb|plant[- ]based|carnivore|keto|paleo|pescatarian|flexitarian)\b", re.I)
# A way of eating said with a verb is not a plan name and is not a name without a verb either:
# "im cutting out dairy", "im off sugar", "im avoiding carbs", "im doing dry january". The
# store kept nothing from those, so the next ask about the diet was denied to somebody who had
# just said it - and a denial of something they said is the worst shape a memory has. The verb
# is kept with the food, because that is what they said: "you're cutting out dairy".
DIET_DOING = re.compile(
    r"\b(?:i'm|im|i am|i've been|ive been|i have been)\s+"
    r"(?P<doing>trying to eat less|trying to eat more|trying to cut out|"
    r"trying to give up|cutting out|cutting down on|cut back on|giving up|avoiding|"
    r"eating less|eating more|not eating|off|doing)\s+(?P<what>[a-z][a-z' -]{1,38})", re.I)
# The word after the verb has to be something to eat. "im off work tomorrow" and "im doing the
# shopping" are the same shape and are not a way of eating, so this decides, not the verb.
DIET_WHAT = frozenset("""sugar sugars carbs carbohydrate carbohydrates dairy meat meats fish
seafood gluten wheat eggs egg alcohol booze caffeine fizzy chocolate sweets bread pasta rice
potatoes protein veg vegetables fruit junk snacks takeaway takeaways processed salt fat
calories soya soy nuts junk-food processed-food fizzy-drinks red-meat white-bread
cheese milk butter coffee tea wine beer lager cider""".split())
DIET_WHAT_TWO = ("dry january", "sober october", "clean eating", "junk food",
                 "processed food", "fizzy drinks", "red meat", "white bread")


def _the_food_named(raw):
    """The food a phrase about eating names, or "" when the words are not something to eat.

    "sugar" and "red meat" are food, "work" and "the shopping" are not, and the phrase stops at
    the first filler: "dairy for a month" is the dairy. One reader for both the diet a person
    names ("im cutting out dairy") and the one they take back ("im back on dairy").
    """
    words = " ".join(str(raw or "").lower().split()).split()
    if not words:
        return ""
    two = " ".join(words[:2])
    if words[0] not in DIET_WHAT and two not in DIET_WHAT_TWO:
        return ""
    kept = []
    for word in words:
        if word in DIET_STOP_A_WAY_OF_EATING:
            break
        kept.append(word)
    return " ".join(kept)


# The same way of eating said in the past: "i gave up sugar", "ive given up cheese", "i stopped
# drinking coffee", "we packed in the takeaways". The verb is the whole of what changed and the
# food behind it is what the store keeps, so the phrase is filed as the way of eating they are on
# now. Without it the store kept nothing, and the only row that answered said to take something
# back to the shop, because "gave up" is how a machine dies. Only something to eat counts, so "i
# gave up smoking" is not a diet and keeps the card its own words reach.
DIET_QUIT = re.compile(
    r"\b(?:i|we)\s*(?:have|'ve|had|ve)?\s*"
    r"(?P<doing>gave up|given up|give up|gives up|quit|quitted|stopped|packed in|cut out|"
    r"cut back on|cut down on)\s+(?:the\s+|my\s+|all\s+|our\s+)?(?P<what>[a-z][a-z' -]{1,38})",
    re.I)
# The doing word a way of eating can be said with: "stopped eating meat" is the meat, and the
# verb of the eating is not what they gave up.
EATING_VERB = frozenset("eating drinking having taking".split())
# The store says a diet back in the present ("You told me you're cutting out sugar", "no more
# cutting out sugar"), so a way of eating said in the past is filed as the same thing happening
# now. Filed as it was typed, "i gave up sugar" came back as "You told me you're gave up sugar".
QUIT_AS_DOING = {"gave up": "giving up", "given up": "giving up", "give up": "giving up",
                 "gives up": "giving up", "quit": "giving up", "quitted": "giving up",
                 "stopped": "giving up", "packed in": "giving up",
                 "cut out": "cutting out", "cut back on": "cutting down on",
                 "cut down on": "cutting down on"}


def _a_way_of_eating_said_with_a_verb(text):
    """The way of eating a line says with a verb, as they said it, or "".

    "im cutting out dairy" -> "cutting out dairy". Only a food word behind the verb counts, so
    the shape is never read from "im off work" or "im doing the shopping".
    """
    for match in DIET_DOING.finditer(text):
        food = _the_food_named(match.group("what"))
        if not food:
            continue
        return match.group("doing").lower() + " " + food
    for match in DIET_QUIT.finditer(text):
        what = match.group("what").split()
        food = _the_food_named(" ".join(what))
        if not food and what[0] in EATING_VERB:
            # "stopped eating meat" names the meat, not the eating: the food behind the eating
            # verb is what they gave up.
            food = _the_food_named(" ".join(what[1:]))
        if not food:
            continue
        doing = match.group("doing").lower()
        return QUIT_AS_DOING.get(doing, doing) + " " + food
    return ""


# A diet they went back on, said in the words of the food they eat again. "im cutting out sugar"
# is kept as that phrase, so "im back on sugar" names only the thing that is back: without this
# the store goes on telling them to avoid what they have just put back ("what diet am i on" ->
# "You told me you're cutting out sugar"), which is the opposite of their last line. The food
# word after the verb has to be something to eat, so "im back on monday" is not a diet returning.
DIET_BACK = re.compile(
    r"\b(?:i'm|im|i am|i've|ive|i have|i'd|we're|were|we are|we've)\s+(?:now\s+)?"
    r"back\s+on\s+(?P<back>[a-z][a-z' -]{1,38})"
    r"|\b(?:i'm|im|i am|i've|ive|i have|i'd|we're|were|we are|we've)\s+"
    r"(?:(?:back\s+to|gone\s+back\s+to|started|start|just)\s+)?(?:eating|having)\s+"
    r"(?P<eat>[a-z][a-z' -]{1,38}?)\s+again\b", re.I)


# Words that end the food in "im cutting out sugar for a bit": the fact is the sugar.
DIET_STOP_A_WAY_OF_EATING = frozenset("""for since because cos till until and but so as to
with from at in on the a an my our this that it all last next ago yesterday today years months
weeks days year month week""".split())
# The word in front of the food in "i dont eat red meat": on its own it says nothing.
NO_EAT_QUALIFIER = frozenset("red white processed raw oily fatty farmed".split())
PETS = re.compile(r"\b(dog|puppy|cat|kitten|rabbit|hamster|guinea pig|parrot|goldfish|fish|horse)"
                  r"(?:s|es)?\b", re.I)
# "two cats, milly and tom": a count, then the animals, then their names. The count is what
# says the names belong to the animals and not to something else in the line.
#
# The words between the figure and the animal describe the animal ("two big dogs", "three black
# cats"); they never open a new thing. Allowing a conjunction, a possessive or a verb there made
# a number that belongs to the person into a number of animals: "im 34 and my dog is 3" was read
# as 34 dogs, and "what pets do i have" then answered "You've got 34 dogs." So the gap stops at
# any word that starts the next thing, which also keeps "2 kids and 1 dog" a line about one dog.
NOT_A_COUNT_GAP = r"(?!(?:and|or|but|plus|with|my|our|his|her|their|the|a|an|is|are|was|were|has|have|had|then|so|because)\b)"
# An age is not a count: "a 3 year old dog" is one dog of three, not three dogs, and "my 9 week
# old dog" is not nine of them. The words between the number and the animal are what tell the two
# apart, so an age unit there cancels the count and the line goes on to answer the animal.
AGE_GAP_WORD = (r"(?!(?:year|years|yr|yrs|month|months|mth|mths|week|weeks|wk|wks|day|days|"
                r"hour|hours|minute|minutes)\b)")
PET_COUNT = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d{1,2}|"
                       r"a couple of|a pair of|couple of)\s+" + NOT_A_COUNT_GAP +
                       r"(?:" + NOT_A_COUNT_GAP + AGE_GAP_WORD + r"[a-z-]+\s+){0,2}$", re.I)
PET_COUNT_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                   "seven": 7, "eight": 8, "nine": 9, "ten": 10, "a couple of": 2,
                   "a pair of": 2, "couple of": 2}
NAME_WORD = re.compile(r"^[A-Za-z][a-z'-]{1,19}$")
NOT_A_NAME = frozenset("""and or but the a an my our his her its their is are was were has have
had got both they them one all each two three four five six seven eight nine ten of to for with
called named too also as who that which name names nickname known rescued rescue puppy kitten
isnt isn't arent aren't wasnt wasn't doesnt doesn't dont don't didnt didn't cant can't wont won't
not never neither nor hardly
dog cat pets animals years
year months month old new little big small
again now then please yet already still just even never before after later soon today tonight
tomorrow yesterday ever anything something
him her it them he she they us me you there""".split())
# The words that say the animal is one more of a kind they already have: "we got another cat called
# Max", "a second dog". Without them, "my cat" is the cat the store already holds, so a line that
# gives the cat a new name is naming the same animal again and not adding one. "a new cat" counts
# because people say it about an animal they have just taken on, and the store keeps its own
# record of the count for a line that gives a number ("i have two cats").
# The marker has to be the word right before the animal ("another cat", "my other cat", "our
# second cat", "my third cat", "the new kitten"), so a phrase that only has the words further
# back is not read as a second animal: "wait a second, my cat is called Max" names one cat.
ANOTHER_ANIMAL = re.compile(
    r"\b(?:another|other|second|third|fourth|fifth|sixth|seventh|new|one more)\s+"
    r"(?:[a-z-]+\s+){0,1}$", re.I)
# The same thing said with the animal after the verb: "we also have a cat called Max", "i also got
# a dog". The marker is "also" with a verb of having right beside it, so a stray "also" elsewhere
# in the line ("also, my cat is called Max") is not a second animal, and "we also have a cat"
# beside a cat they already have is one more of them rather than the cat they have, named again.
ALSO_HAVE = re.compile(r"\b(?:also|too)\s+(?:have|has|had|got|own|owns|keep|keeps|rehomed"
                       r"|adopted|took in|rescued|named)\b"
                       r"|\b(?:have|has|had|got|own|owns|keep|keeps)\s+also\b", re.I)
# "we named the cat Biscuit", "the vet named my rabbit Bunny": the verb comes before the animal and
# the name after it, so the name is not the word next to "named". "i named my cat after my grandma"
# names the cat after somebody and gives it no name; the word after the animal is read only when it
# is a name and not a word about the animal (the lists below say which words are not names).
# "her cat" and "their dog" are somebody else's animal, so a name given to one is not the user's.
NOT_THEIR_DETERMINER = frozenset("his her their".split())
# A title in front of the name is part of the name: "my cat is called Mr Whiskers" is a cat
# called "Mr Whiskers", not a cat called "Mr", and people do name animals after titles ("Lady",
# "Prince", "Sir Purrs"). The title is only taken when a word follows it, so "my cat is called
# Prince" keeps the whole name and "called Dr" alone is still one word.
PET_TITLE = re.compile(r"(?i:(?:mrs|mr|ms|miss|mx|doctor|professor|prof|dr|captain|princess|"
                       r"prince|saint|dame|lady|lord|sir|st)\.?)")
PET_VERB_NAME = re.compile(
    r"\b(?:named|called)\s+(?:(?P<whose>the|our|my|a|an|their|his|her)\s+)?"
    r"(?:dog|puppy|cat|kitten|rabbit|hamster|parrot|goldfish|fish|horse)s?\s+"
    r"(?:(?P<title>" + PET_TITLE.pattern + r")\s+)?"
    r"(?P<name>[A-Za-z][A-Za-z'-]{1,19})\b")
# "we got a puppy and named him Rex": the animal is a pronoun by the time the name is said, and the
# pronoun is not the name. "named him" alone was read as a puppy called "Him".
PET_PRONOUN_NAME = re.compile(r"\b(?:named|called)\s+(?:him|her|it|them)\s+"
                              r"([A-Za-z][A-Za-z'-]{1,19})\b")
# Words that come after the animal in "we named the cat ..." without being the name: where the cat
# is, what it is for, and who it was named after.
NOT_THE_VERB_NAME = frozenset("""
after before because for in into out up down over round around off on at with to from by since
while and or but so then if once already now today tomorrow yesterday tonight
house home flat garden yard boat farm stable
""".split())
NOT_A_PRONOUN_NAME = frozenset("him her it them he she they us me you".split())
PET_NAME = re.compile(
    r"\b(?:called|named)\s+(?:(?P<title>" + PET_TITLE.pattern + r")\s+)?"
    r"(?P<name>[A-Z][a-z'-]+|[a-z][a-z'-]+)\b")
# A word after a title that is still part of the name even though it is in NOT_A_NAME. "Who" is
# there because a question starts with it ("who is the oldest"), but it is also a name word: a cat
# named after the doctor is "Dr Who", and without this the title is all that is kept.
NAME_AFTER_TITLE = frozenset(("who",))


def _with_title(match):
    """The name a "called"/"named" match gives, with its title kept: "Mr Whiskers", "Lady Grey"."""
    title = match.group("title")
    name = match.group("name")
    if not title:
        # A one-word name is stored exactly as it was said, as it always has been: the store is
        # not the place to change the case of what somebody called their animal.
        return name
    if name.lower() in NOT_A_NAME and name.lower() not in NAME_AFTER_TITLE:
        # The word after a title is part of the name only when it is a name word: "my cat is
        # called lady and she is 3" names the animal Lady, and "Lady And" is not a name. The
        # title alone is what the line gave, which is what the store did before titles were kept.
        return title.rstrip(".")
    # "called mr whiskers" is the same name as "called Mr Whiskers", and a two-word name is said
    # back the way a name is written.
    return (title + " " + name) if any(char.isupper() for char in title + name) else \
        " ".join(word[:1].upper() + word[1:] for word in (title + " " + name).split())


def _name_at(match):
    """Where a "called" match names the animal: the title, when there is one, comes first."""
    return match.start("title") if match.group("title") else match.start("name")


# "my cat is Biscuit": a name given with no "called". Only a capitalised word, so "my dog is
# scared of men" does not become a dog called scared.
PET_IS_NAME = re.compile(r"\b(?:dog|puppy|cat|kitten|rabbit|hamster|parrot|goldfish|fish|horse)s?\s+"
                         r"(?:is|are)\s+(?:called\s+|named\s+)?(?:(?P<title>" + PET_TITLE.pattern +
                         r")s?\s+)?(?P<name>[A-Z][a-z'-]{1,20})\b")
# "the dogs name is rex", "my cats name is milo": the animal is named by the possessive in front
# of "name" and the word after it is the pet's name. The animal's own word is the whole signal, so
# the name is read in lower case too (people type "the dogs name is rex" far more often than with a
# capital), and no pet on record is needed: the line introduces the dog it names. On main the
# animal was filed and the name was dropped - "the dogs name is rex" gave a dog with no name - so
# "whats my dogs name" answered "You haven't told me a name for your dog yet" about a dog the
# line had just named.
PET_POSSESSIVE_NAME = re.compile(
    r"\b(?:the|my|our|your|his|her|its|their)\s+(?:new\s+|little\s+|old\s+|rescue\s+)?"
    r"(?:dog|puppy|cat|kitten|rabbit|hamster|parrot|goldfish|fish|horse)s?\s*(?:'s|s)?\s+"
    r"name\s*(?:'s|is|was)\s+(?:(?P<title>" + PET_TITLE.pattern + r")\s+)?"
    r"(?P<name>[A-Za-z][A-Za-z'-]{1,19})\b", re.I)
# "and her name is Biscuit", "she's called Biscuit": a name for a pet the line does not name
# again. Only her/his/its, so "my name is Nadia" never becomes a dog's name.
# "we adopted a rescue dog, biscuit", "our cat, milo, is scared of men": a name given as an aside
# after the animal, with no "called". Only a single word between commas, so "we're getting a
# kitten, next week" and "my dog has been sick twice, today" name nothing.
PET_APPOSITIVE = re.compile(
    r"\b(?:dog|puppy|cat|kitten|rabbit|hamster|parrot|goldfish|fish|horse)\b[^,.;!?]{0,24},\s*"
    r"([a-zA-Z][a-zA-Z'-]{1,20})\s*(?=$|[,.;!?]|\s+(?:is|was|and|has|needs|loves|hates|does)\b)")
# "my dog max is 4", "our cat biscuit was 12": the name sits between the animal and the fact
# the line says about it, the same way "my brother tom is 12" gives a person's name. Only one word
# is read, so "the dog next door is noisy" names nothing.
PET_BEFORE_FACT = re.compile(
    r"\b(?:dog|puppy|cat|kitten|rabbit|hamster|parrot|goldfish|fish|horse)s?\s+"
    r"(?P<name>[A-Za-z][A-Za-z'-]{1,19})\s+(?:is|was|are|were)\b")
# A word in that place that is about where the animal is, not what it is called: "the dog upstairs
# is loud" has no dog called Upstairs.
NOT_A_NAME_MIDDLE = frozenset("""
upstairs downstairs outside inside indoors outdoors away home back next front behind there here
nearby around about settled used fine
""".split())
# Words that look like a name after the comma but are not: how people talk about a pet, and when.
PET_ANIMALS = frozenset("""
dog puppy cat kitten rabbit hamster parrot goldfish fish horse dogs puppies cats kittens rabbits
hamsters parrots fish horses animal pet
""".split())
# Which kind of animal a word names, so two words for one animal ("a cat and a kitten") are one
# pet and two words for two animals ("a cat and a dog") are a pair. The plural and the young are
# the same animal: a person who says "two cats" has one kind of pet, not two.
ANIMAL_KINDS = {
    "dog": "dog", "dogs": "dog", "puppy": "dog", "puppies": "dog",
    "cat": "cat", "cats": "cat", "kitten": "cat", "kittens": "cat",
    "rabbit": "rabbit", "rabbits": "rabbit",
    "hamster": "hamster", "hamsters": "hamster",
    "parrot": "parrot", "parrots": "parrot",
    "fish": "fish", "goldfish": "fish",
    "horse": "horse", "horses": "horse",
}


def another_animal(text, animal):
    """A second, different kind of animal in the same line, or "".

    "i have a cat and a dog" names two animals, and the reply it got was "A cat - good to know.
    What's its name?", which quietly dropped the dog. Which animal a line is about is the wrong
    question when it is about two, so a reader that would answer for one of them asks this first.
    Two words for one animal are one animal: "i have two cats" and "a cat and a kitten" are not
    pairs, so the kinds are compared rather than the words.
    """
    kind = ANIMAL_KINDS.get(str(animal or "").strip().lower(), "")
    if not kind:
        return ""
    for word in re.findall(r"[a-z]+", str(text or "").lower()):
        other = ANIMAL_KINDS.get(word, "")
        if other and other != kind:
            return other
    return ""
NOT_A_PET_NAME = frozenset("""
today tomorrow yesterday tonight now soon again though although instead already still even too
also either rather which who whose what when where why how and but so or if then than there here
vet vets help advice question thing things lot lots bit one two three years year months weeks days
man men woman women boy girl child kid kids people person male female puppy dog cat kitten pet
he she they it them i we you every each some any all one ones day days week weeks month months
year years after before from with without about over under round around back away out off
""".split())
# The name is read in either case: "her name is pepper" is the same line as "her name is
# Pepper", and people type it lower-case far more often than not. What a word after "name is"
# cannot be ("not", "still", "weird") is turned down by `_not_a_name` below, so lowering the
# case does not turn ordinary words into names.
PET_NAME_ONLY = re.compile(r"\b(?:her|his|its)\s+name(?:'s| is)\s+([A-Za-z][a-z'-]{1,20})\b|"
                           r"\b(?:she|he|it)(?:'s|s)\s+(?:called|named)\s+([a-zA-Z][a-z'-]{1,20})\b|"
                           r"\b(?:we|i)(?:'ve| have)?\s+(?:named|called|call)\s+(?:him|her|it)\s+"
                           r"([a-zA-Z][a-zA-Z'-]{1,20})\b")
# The same line typed in lower case: "and her name is biscuit". People type a name without a
# capital far more often than with one, and the possessive in front of "name" is what says it is
# the animal's name, not the word after it being a name at all. Only used where a pet is already
# on record (see `pet_name_only(lower=True)`), so "his name is long" alone reads nothing.
PET_NAME_ONLY_LOWER = re.compile(
    r"\b(?:her|his|its|their)\s+names?\s+(?:'s|is|was|actually|really)\s+"
    r"([a-z][a-z'-]{1,20})\b", re.I)
# Words that follow "name is" as a comment on the name rather than as the name: "the dogs name is
# long" is a name that is hard to remember, "his name is short" the same, and none of them is a pet
# called Long. They are the words a person reaches for when the name is the thing being described,
# so the line says nothing the store can keep.
A_COMMENT_ON_THE_NAME = frozenset("""long short hard easy difficult tricky complicated silly daft
weird funny strange odd boring lovely nice horrible stupid ridiculous impossible embarrassing
forgettable unpronounceable common rare plain simple weird rubbish""".split())


def _a_name_for_the_pet(word, strict_ly=True):
    """The word a pet's name was given as, or None when the word only comments on the name."""
    low = str(word or "").lower()
    if not word or _not_a_name(word, strict_ly=strict_ly) or low in A_COMMENT_ON_THE_NAME:
        return None
    return word
# What the bot says when it asks for a pet's name, so a one-word answer can be read as the name.
PET_NAME_ASKED = re.compile(
    r"\bwhat(?:'s| is|s)? (?:its|his|her|their) name\b|"
    r"\bwhat (?:do|shall|should) (?:i|we) call (?:it|him|her|them)\b|"
    r"\bwhat(?:'s| is|s)? the name of (?:your|the)\s+(?:dog|cat|puppy|kitten|rabbit|hamster|pet)\b",
    re.I)
# What the bot says when it asks for the person's own name, or admits it does not know it:
# "can you remember my name" -> "I don't know it yet - you haven't said" is a question in all
# but the question mark, and the one word after it is the answer. Without this a bare "sam" was
# nothing at all and the store still said it had never been told.
# Every word of it is about the name. The store's other "I don't know it - you haven't said"
# lines (the age, the job, the place) are the same shape, so a pattern that read "it" instead of
# "name" made "how old am i" / "nine" file a person called Nine: the ask has to be the name's.
USER_NAME_ASKED = re.compile(
    r"\bwhat(?:'s| is|s)? your name\b|\bwhat (?:do|shall|should) i call you\b|"
    r"\bwho am i (?:speaking|talking|chatting) to\b|\bwhat are you called\b|"
    r"\bdon'?t know (?:your name|what your name is)\b|"
    r"\bdon'?t know it yet\b|\byour name (?:again|then)\b|"
    r"\bhaven'?t (?:said|told me) your name\b", re.I)
# A word said about the situation rather than a person: "its hard", "this is tough". They pass
# the shape tests, so they are listed with the other words that are not names.
NOT_A_NAME_THING = frozenset("""hard easy tough great rubbish weird strange wrong right broken
amazing lovely nice better worse possible impossible funny awful terrible horrible annoying
confusing complicated tricky simple stupid mad""".split())


# What people answer with when they read the question as "what do you do": a job says nothing
# about the person's name, and "teacher" came back as "Hi Teacher - good to meet you."
JOB_WORDS = frozenset("""teacher nurse doctor dentist engineer chef waiter waitress builder driver
farmer student accountant lawyer manager receptionist cashier soldier police mechanic hairdresser
barber baker butcher postman designer developer programmer analyst consultant researcher
scientist professor lecturer pilot cleaner decorator handyman gardener carer midwife pharmacist
vet secretary clerk apprentice volunteer""".split())

# A count is not a name: "thirty" and "nine" pass every shape test the name reader has.
NUMBER_WORDS = frozenset("""one two three four five six seven eight nine ten eleven twelve
thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty
seventy eighty ninety hundred thousand million billion dozen zero none""".split())


def _names_something_else(low):
    """Whether a word on its own names a thing rather than a person.

    The "im Jess" rules will read any word as a name, and the answer to "what's your name" can
    be anything at all: "london", "monday", "teacher" and "thirty" all came back as the person's
    name and then stuck ("You're Wednesday."). The lists the store already keeps decide it - the
    days, the months, the countries, a number - and the knowledge base's own city and trade
    lists for the rest, read here so a large module is only loaded when a name is being taken.
    """
    if not low:
        return True
    if (low in DAYS or low in MONTHS or low in COUNTRIES or low in NOT_PLACES
            or low in NUMBER_WORDS or low in JOB_WORDS):
        return True
    try:
        from ..knowledge import costs, travel  # noqa: PLC0415 - only when a name is on the table
        if low in travel.CITIES or low in costs.JOBS:
            return True
    except Exception:  # noqa: BLE001 - an unread list just leaves the word alone
        pass
    return False


def reads_as_a_name(word):
    """Whether a word on its own, in answer to a name question, is what a person is called.

    The rules that read "im Jess" decide it, so a word that says how something is ("its cold",
    "this is tired") never becomes a name. Returns the name in its spelled form, or None.
    """
    if not bare_name(word):
        return None
    low = _finish(str(word or ""))
    if not low or low in NOT_A_NAME_THING or low in NOT_A_NAME_TRAIT \
            or _names_something_else(low):
        return None
    name = _name("im " + low)
    if name and _finish(name) == low:
        return name
    return None


# "its sam", "this is sam", "the names sam": the words in front of the name are only read as
# an introduction when the bot has just asked for it, because on their own they say something
# else - "its cold" is the weather and "this is hard" is the job.
NAME_ANSWER_ANNOUNCED = re.compile(
    r"^\s*(?:it's|its|it is|this is|that'?s|the name'?s|the name is|the names|the name's|"
    r"im|i'm|i am)\s+([a-z][a-z'-]{1,19})\s*[.!]?\s*$", re.I)
# The same introduction at the end of a longer answer, when the bot has just asked for the name:
# "i havent told you, its sam by the way" is the name and nothing else after it, said after the
# apology for not having given it. Only the end of the line is read, so the name is still the last
# thing the person said, and only where the store was waiting for a name.
NAME_ANSWER_ANNOUNCED_LAST = re.compile(
    r"(?:^|\W)(?:it's|its|it is|this is|that'?s|my name'?s|my name is|call me|"
    r"im|i'm|i am)\s+([a-z][a-z'-]{1,19})\s*[.!]?\s*$", re.I)


# The bot's own list of names, as the memory store writes it: "For a cat: Miso, Willow or Pepper."
# The animal is in the line, and so is every name the person can pick from, so the patterns are
# read off the reply rather than kept in a list here: whatever was offered is what can be picked.
NAMES_OFFERED = re.compile(
    r"\bfor\s+(?:a|an|your)\s+(?P<animal>[a-z]+)\s*:\s*(?P<list>[^.]*?)\.", re.I)
# The question the list answers, said by either of them: "what should we name her" is the same
# ask as the bot's own "what's its name?", and the answer to it is a name and nothing else.
NAME_PICK_ASK = re.compile(
    r"\b(?:what|which)\s+(?:shall|should|would|could|do|can|will|might)\s+(?:i|we|you)\s+"
    # The thing being named is pointed at ("call it", "name her") or named outright: "what
    # should i name my cat" is the same question, and the answer to it is still a name.
    r"(?:call|name)\s+(?:it|him|her|them|this|that|(?:my|our|the|your)\s+"
    r"(?:[a-z]+\s+)?(?:" + "|".join(sorted(PET_ANIMALS)) + r"))\b"
    r"|\bwhat(?:'s|s| is)\s+(?:a|some)\s+good\s+name\b"
    r"|\b(?:any|some)\s+(?:name\s+)?ideas?\s+for\s+(?:a\s+)?names?\b", re.I)
# The words a figure of money is said in after the number. "6 grand" was read as a budget of 6:
# "grand" was not one of them, so the store kept the figure and dropped the word, and two turns
# later the person's own budget came back as "Your budget is 5." - a fact they gave, said back
# wrong. "grand" and "bucks" are how people say thousands and pounds out loud, so they belong in
# the same list as pounds and quid, with the word boundary kept so "5 grandkids" is a count.
BUDGET = re.compile(r"\bbudget\b[^.\d]{0,40}?((?:under |over |less than |up to )?[£$€]?\s?"
                    r"\d[\d,.]*(?:\s?(?:pounds|quid|euros?|dollars?|grand|bucks|k)\b)?)", re.I)
SPEND_BUDGET = re.compile(r"\b(?:i|we)(?:'?ve|\s+have)\s+(?:only\s+)?(?:got\s+)?"
                          r"((?:about |around |up to |under |max(?:imum)? )?[£$€]?\s?\d[\d,.]*"
                          r"(?:\s?(?:pounds|quid|euros?|dollars?|grand|bucks|k)\b)?)\s*(?:to spend|on it|budget)",
                          re.I)
# The limit said as what they mean to do with it, which is how most people say a limit out
# loud: "i want to keep it under 80 pounds", "i can only spend 80 pounds on it", "i need to
# spend under 40". None of those was filed as a budget - the only spend shapes the store knew
# wanted money they already had ("ive got 80 pounds to spend") - so six turns later a party plan
# with a stated ceiling got "You haven't told me a budget", a fact they had given and the bot had
# already answered, which is the worst kind of forgetting: it contradicts them.
#
# Two things make the figure a limit rather than a price: the person is the subject and the verb
# is what they mean to spend (want, need, can, only), and a cap word sits between the verb and
# the money (under, up to, no more than) or the money is what to spend on a named thing. A price
# they are only reporting ("the coat was under 80 pounds") has neither, and stays a remark.
_INTENT = (r"(?:want|wanna|wanted|need|needed|would like|'d like|d like|plan to|planning to|"
           r"am going|are going|hoping|have|'ve|got|can|could|will|'ll|must|should|try to|"
           r"trying to)")
_WHAT_THEY_MEAN_TO_DO = (r"(?:spend|keep (?:it|the cost|costs|the budget|the price)|come in|stay|"
                         r"be (?:under|below|within)|keep to)")
_A_CAP = (r"(?:under|below|less than|up to|no more than|not more than|at most|max(?:imum)?|"
          r"within|around|about|circa)?\s*")
_MONEY_AGAIN = (r"((?:" + _A_CAP + r")(?:[\u00a3$\u20ac]\s?\d[\d,.]*|"
                r"\d[\d,.]*\s?(?:pounds?|quid|euros?|dollars?|bucks|grand|k)\b))")
INTENDED_SPEND = re.compile(
    r"\b(?:i|we)\s+(?:only\s+)?" + _INTENT + r"\s+(?:only\s+)?(?:to\s+)?" +
    _WHAT_THEY_MEAN_TO_DO + r"\b[^.\d]{0,24}?" + _MONEY_AGAIN, re.I)
# The same limit with the thing as the subject: "it has to come in under 80 quid", "this needs to
# stay below 40 pounds". The thing is what the chat is about, and the person is still the one
# saying what it may cost.
THE_THING_MAY_COST = re.compile(
    r"\b(?:it|this|that|the whole thing)\s+(?:has to|needs to|should|must|will|can)" +
    r"\s+(?:only\s+)?(?:come in|stay|be|keep)\b[^.\d]{0,16}?" + _MONEY_AGAIN, re.I)
# "under 80 pounds is all i can do": the figure comes first and the limit is the second half.
# The money word is what makes it money, and "all i can do" is what makes it the ceiling rather
# than a price they are reporting.
ALL_I_CAN_DO = re.compile(
    r"\b" + _MONEY_AGAIN + r"\s+is\s+all\s+(?:i|we)\s+(?:can|could|have|got|afford|manage)"
    r"\s+(?:do|afford|manage|spend|stretch to|stretch|pay)\b", re.I)
# What the person can spend, said as money they have: "i've got 50 pounds for a present", "we
# only have 40 pounds for food", "i only have 30 quid". The line states no budget, but it is
# the figure their answer has to fit, and a later "make that 80" has to move it: without it the
# store has nothing to correct and the turn hedges. The verb has to be there ("i've got", "i
# have", "we had") so "i got 50 pounds for my birthday" stays money received, and "for" has to
# open a thing ("for a present", "for her party") so "for luck" is not a budget.
SPEND_FOR = re.compile(r"\b(?:i|we)(?:'?ve|'d|\s+have|\s+had)\s+(?:only\s+)?(?:got\s+|have\s+)?"
                       r"((?:about |around |up to |under |max(?:imum)? )?[£$€]?\s?\d[\d,.]*"
                       r"(?:\s?(?:pounds|quid|euros?|dollars?|grand|bucks|k)\b)?)"
                       r"\s+for\s+(?:a|an|the|my|our|his|her|their|your|another|\w+'s)\s+\w",
                       re.I)
# "i only have 30 pounds" is a budget; "i only have 30 minutes", "i only have 2 days" are not. A
# bare number after "only have" is nearly always a length of time, so the money word or the symbol
# is what makes it money - without it the store filed a budget of 30 for "i only have 30 minutes
# to cook" and then answered "whats my budget" with it.
MONEY_AMOUNT = (r"((?:(?:about |around |up to |under )?"
                r"(?:[£$€]\s?\d[\d,.]*|\d[\d,.]*\s?(?:pounds?|quid|euros?|dollars?|"
                r"bucks|grand|k)\b)))")
ONLY_HAVE = re.compile(r"\b(?:i|we)\s+only\s+(?:have|had|got)\s+" + MONEY_AMOUNT, re.I)
# The limit said again in another shape: "my budget is 500" then "ive only got 300 now". The word
# that makes it the money they have is "only", and the word that makes it now is "now" - without
# them "ive got 300 followers" is a count and "my budget was 500" is the past.
SPEND_BUDGET_NOW = re.compile(r"\b(?:i|we)(?:'ve| have)\s+only\s+(?:got\s+|have\s+)?"
                              r"((?:about |around |up to |under |max(?:imum)? )?[£$€]?\s?"
                              r"\d[\d,.]*(?:\s?(?:pounds|quid|euros?|dollars?|grand|bucks|k)\b)?)\s*"
                              r"(?:now|these days|at the moment|left)\b", re.I)
# A limit raised in another shape, with the word "budget" nowhere in it: "my budget is 500"
# then "i could stretch to 600", "we can go up to 900 at a push". The person has just told you
# the ceiling moved, so the plan, the present and the recall all have to use the new figure;
# without this the store kept 500 and "whats my budget now" handed back a limit they had
# already left behind. The figure is bare in the common case ("stretch to 600"), so a bare one
# has to end the line or be followed by the words people put after a limit - otherwise "i can
# go up to 600 followers" would file a budget of 600. The first person and the modal keep it to
# their own money: "the jeans will stretch to fit" and "can you stretch to 600" (a question to
# the bot) say nothing about what they can spend.
MONEY_FIGURE = (r"(?:[\u00a3$\u20ac]\s?\d[\d,.]*|\d[\d,.]*\s?"
                r"(?:pounds?|quid|euros?|dollars?|bucks|grand|k)\b)")
STRETCH_BUDGET = re.compile(
    r"\b(?:i|we)\s+(?:could|can|might|may|would|'d)\s+"
    r"(?:maybe\s+|probably\s+|possibly\s+)?"
    r"(?:stretch\s+(?:it\s+)?(?:up\s+)?to|go\s+up\s+to|push\s+(?:it\s+)?(?:up\s+)?to)\s+"
    r"((?:about |around |up to |maybe |just )?"
    r"(?:" + MONEY_FIGURE + r"|\d[\d,.]*(?=\s*(?:$|[.,;!?]|\bat a push\b|\bmax\b|"
    r"\btops\b|\bnow\b|\bfor\b))))", re.I)
# What comes in is the same kind of limit as what they have to spend: "i only earn 1200 a month"
# and "i only get 900 a month" are the figure any plan has to fit, and said back with the stock
# echo ("Got it - you only earn 1200 a month.") they are the filing cabinet again. Two things make
# a figure the money they live on rather than a count of something or a rate: the verb (what they
# are paid) and a period ("a month", "a year", "a week", "a fortnight"). "i get 3 runs a week" is
# a routine and "i earn 20 pounds an hour" is a rate, so neither is a budget; the period is what
# tells the count from the money and the word after the period tells the rate from it.
INCOME_PERIOD = re.compile(r"\s*(?:a|per|each|every)\s+(?:month|week|year|fortnight)\b", re.I)
# A rate, not the money they live on: "20 pounds an hour", "300 a day", "a grand a week"? no - a
# week is a period people are paid by, so it stays. An hour and a day are rates.
# The figure and its period are not always side by side: "we bring home 3000 between us a month"
# and "i take home 1800 after tax a month" put the household, or the deductions, in the gap. Only
# the words that can sit there are allowed through, so a count keeps its counting: "i get 300
# emails a week" is still a routine and not a wage.
INCOME_QUALIFIER = re.compile(
    r"(?:\s+(?:between\s+(?:us|the\s+two\s+of\s+us)|together|in\s+total|altogether|combined|"
    r"after\s+tax|after\s+taxes|after\s+deductions|after\s+national\s+insurance|after\s+ni|"
    r"after\s+stoppages|net|clear|clean|now|currently|each|both)\b){0,3}", re.I)
INCOME_RATE = re.compile(r"\s*(?:an?|per|each|every|/)\s*(?:hour|hr|day|shift|weekend)\b", re.I)
INCOME = re.compile(r"\b(?:i|we)(?:'m|m\b| am| are)?\s+(?:only\s+)?(?:"
                    r"(?:earn|make|get paid|get|bring home|take home|be on|am on)"
                    r"|(?:on))\s+"
                    r"((?:about |around |roughly |up to |just )?(?:[£$€]\s?\d[\d,.]*|"
                    r"\d[\d,.]*\s?(?:pounds?|quid|euros?|dollars?|bucks|grand|k)\b))", re.I)
INCOME_BARE = re.compile(r"\b(?:i|we)(?:'m|m\b| am| are)?\s+(?:only\s+)?(?:"
                         r"earn|make|get paid|get|bring home|take home|on)\s+"
                         r"((?:about |around |roughly |up to |just )?\d[\d,.]*)", re.I)
# A year's pay said with no period at all: "i earn 32000", "my salary is 32000", "im on 32k".
# The period is what tells money from a count ("i get 300 emails") and from a rate ("i earn 20
# pounds an hour"), so its absence is why these lines filed nothing - and why the reply to a
# statement of their pay was a stock line, while "i earn 32000 a year" got the year-to-month
# answer. What stands in for the period is the *shape* of the figure and the verb: only the verbs
# that cannot mean anything but pay are here ("get" and "make" are not, because "i get 3000
# views" and "i make 2000 cookies" are counts), and the figure has to be a year's wage rather
# than a count, which is four digits or a figure in thousands.
INCOME_A_YEAR = (
    re.compile(r"\b(?:i|we)(?:'m|m\b| am| are)?\s+(?:only\s+)?"
               r"(?:earn|earns|earned|get paid|bring home|take home|be on|am on|on)\s+"
               r"((?:about |around |roughly |up to |just )?"
               r"(?:[£$€]\s?\d[\d,.]*|\d[\d,.]*(?:\s?(?:pounds?|quid|grand|k)\b)?))", re.I),
    re.compile(r"\b(?:my|our)\s+(?:salary|wages?|pay|income)\s*(?:is|was|'s|are)?\s*"
               r"((?:about |around |roughly )?"
               r"(?:[£$€]\s?\d[\d,.]*|\d[\d,.]*(?:\s?(?:pounds?|quid|grand|k)\b)?))", re.I),
)
# A budget said with nothing around it: "under 15 pounds", "about 30", "anything under 15 pounds",
# "no more than 20 pounds", "something around 20". The figure is what the line is about, so a lead
# in is allowed but nothing else is: "anything" and "something" are people thinking out loud about
# the number, and the qualifier still has to be there ("just 25" is as likely to be minutes).
BARE_BUDGET_LEAD = (r"(?:(?:anything|anythink|something|somewhere|maybe|probably|honestly|"
                    r"i dunno|dunno|i reckon|i'd say|say|i was thinking|i'm thinking|im thinking|"
                    r"i thought|thinking|i was going to say)\s+){0,3}")
BARE_BUDGET = re.compile(r"^\W*" + BARE_BUDGET_LEAD +
                         r"((?:(?:under|below|less than|up to|around|about|max(?:imum)?|"
                         r"no more than|not more than)\s*)"
                         r"[£$€]?\s?\d[\d,.]*(?:\s?(?:pounds|quid|euros?|dollars?|grand|bucks|k)\b)?)"
                         r"(?:\s*(?:or so|ish|please|i think|i reckon))?\W*$", re.I)
# A ceiling is said as a negative as often as with "under": "nothing over 25 pounds", "not over
# 30 quid", "nothing above \u00a340". It is the same limit as "under 25 pounds" and so the same fact,
# filed as that shape ("no more than 25 pounds") because the store says a budget back as a value
# and "nothing over 25 pounds" opens on a word that ends a value (`_fact_value` cuts at
# "nothing"). The figure has to be money: without the unit "nothing over 25" is as likely to be
# minutes, and "no more than 5 a day" is a habit rather than what they can spend.
CEILING_BUDGET = re.compile(r"^\W*" + BARE_BUDGET_LEAD +
                            r"(?:nothing|not|nowt|no)\s+(?:more than|over|above|past)\s*"
                            r"([£$€]\s?\d[\d,.]*|"
                            r"\d[\d,.]*\s?(?:pounds?|quid|euros?|dollars?|bucks|k)\b)"
                            r"(?:\s*(?:or so|ish|please|i think|i reckon))?\W*$", re.I)
# A limit said without a figure: "not too expensive", "nothing too pricey", "something cheap",
# "on the cheap". It rules out what is worth suggesting as much as a figure does, so it is kept
# like a budget and said back with what the bot will do with it. The whole line has to be the
# limit: "the tickets were cheap" is about a thing they bought, not what they can spend.
# A limit asked as a question about the figure: "is 30 pound enough", "would 20 pound get
# something decent", "will 15 quid do". The money word is there and the figure is what the line
# is about, so it is the same fact as "about 20 pounds" said the other way up. Without it a gift
# chat kept the figure but lost the noun beside it and the bare number was read as a temperature.
# A figure thought out loud: "i was thinking 25 pound", "im thinking about 40 quid". The money
# word is what makes it a limit; without one the same line is a time ("i was thinking 20 minutes")
# and the store leaves it alone.
BUDGET_THOUGHT = re.compile(r"^\W*(?:i\s+was\s+|i'?m\s+|im\s+|i\s+am\s+)?thinking\s+"
                            r"(?:about\s+)?(?:around\s+)?"
                            r"(?P<figure>[\u00a3$\u20ac]?\s?\d[\d,.]*\s?(?:pounds?|quid|"
                            r"euros?|dollars?))", re.I)
BUDGET_ASKED = re.compile(r"^\W*(?:is|would|will|does|do|could|can|should)\s+"
                          r"(?P<figure>[\u00a3$\u20ac]?\s?\d[\d,.]*(?:\s?(?:pounds?|quid|euros?|"
                          r"dollars?))?)"
                          r"\s+(?:enough|do|be enough|get|buy|cover|work|be ok|be okay|be fine)\b", re.I)


def vague_budget(text):
    """The limit a line states with no figure in it, as the store says it back: "nothing too
    pricey" -> "not too expensive", "something cheap" -> "cheap". None when the line is not a
    limit ("the tickets were cheap" is about what they bought)."""
    match = VAGUE_BUDGET.match(text or "")
    if not match:
        return None
    said = " ".join(match.group(0).lower().split()).strip(" .,;:!")
    if "cheap" in said and said.startswith("on "):
        return "on the cheap"
    if "cheap" in said or "reasonable" in said:
        return "cheap"
    if said.startswith("budget"):
        return said
    return "not too expensive"


VAGUE_BUDGET = re.compile(
    r"^\W*(?:(?:not|nothing|no|never)\s+(?:\w+\s+){0,2}(?:too\s+|that\s+|very\s+)?"
    r"(?:expensive|pricey|dear)|(?:something|anything|nothing)\s+(?:cheap|cheaper|reasonable)|"
    r"on\s+the\s+cheap|budget\s+(?:friendly|ish))\W*$", re.I)
MONEY = re.compile(r"([£$€]\s?\d[\d,.]*|\b\d[\d,.]*\s?(?:pounds|quid|euros?|dollars?|grand|bucks)\b)", re.I)
# An age, and only an age: "i am 6 foot 2" is a height, so a number with a unit after it is not
# one (the reader keeps to a sane range as well), and "i'm 5 11" is a height typed without its
# unit. "i'm 34 years old" is still an age, so "years" is not a unit here. A decimal ("1.75
# metres") is not one either: the 1 in it is not the number the line is about.
AGE_UNIT = (r"(?:foot|feet|ft|cm|centimetres?|centimeters?|inches?|inch|stone|st|kg|kilos?|kgs?|"
            r"pounds?|lbs?|lb|metres?|meters?|m|miles?|mph|hours?|hrs?|mins?|minutes?|weeks?|"
            r"days?|months?|percent|%)")
AGE = re.compile(r"\bi(?:m|'m| am)\s+(\d{1,2})(?![\d.,]\d)\b(?!\s*" + AGE_UNIT + r"\b)"
                 r"(?!\s*\d)", re.I)
# How tall somebody is. The age reader above already refuses a number with a unit after it ("im 5
# foot 10" was no age), and nothing else read the height, so the figure was dropped: the line got
# a listening noise and "how tall am i" was answered "I'm not sure about that one" about a height
# the person had given one line earlier. Both shapes people use are read - feet and inches as it is
# spoken, and the centimetres that go on a form - and the key is the one the correction code
# already knows, so a later "no, 5 foot 8" lands on it.
HEIGHT_FEET = re.compile(r"\b(?:i'm|i\s+am|im|my\s+height\s+is)\s+(?P<feet>\d)\s*"
                         r"(?:foot|feet|ft|')\s*(?P<inches>\d{1,2}|ten|eleven|one|two|three|"
                         r"four|five|six|seven|eight|nine)?\s*(?:\"|''|in(?:ches)?)?"
                         r"(?=\W|$)", re.I)
# The height said as a correction with nothing around it: "no, 5 foot 8". The whole line is a
# lead-in and the figure, so a recipe or an address cannot be read as one.
HEIGHT_BARE = re.compile(r"^\s*(?:(?:no|nope|sorry|wait|ah|oh|actually|make\s+it)[,.!]?\s+)*"
                         r"(?P<feet>\d)\s*(?:foot|feet|ft)\s*(?P<inches>\d{1,2})\s*\W*$", re.I)
# The inches said as a word ("5 foot ten") written as the figure. Kept under its own name: a
# second `NUMBER_WORDS` here would be the one the file has by the time a name is read, and the
# first - the count-words-no-name list above - is what the two name readers ask for. That
# shadowing is how "thirty", "forty", "dozen" and "million" came to be names: only one to eleven
# were still in the list when `reads_as_a_name` asked.
INCH_WORDS = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
              "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11"}
HEIGHT_CM = re.compile(r"\b(?:i'm|i\s+am|im|my\s+height\s+is)\s+(?P<cm>1\d{2}|2[0-2]\d)\s*"
                       r"(?:cm|centimetres?|centimeters?)\b", re.I)


# An age said in words. The age readers take figures, so "my daughter is eight" was filed as a
# fact with no age in it while the ack said "Noted: your daughter is eight", and the ask one line
# later answered "you haven't told me how old your daughter is". "my gran is eighty-eight" was
# worse: the words were filed as her name, and said back as one (polite-ruler, #conversation
# 50582). Only the words in an age's place are turned into figures - after "is", "are", "was",
# "i am" and "aged", and with nothing after them but the end of the fact or the years counted -
# so "she is one of those" and "two weeks old" stay exactly as they were said.
_NUMBER_IN_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90,
}
_A_UNIT_WORD = r"(?:one|two|three|four|five|six|seven|eight|nine)"
_A_TEEN_WORD = (r"(?:ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen"
                r"|nineteen)")
_A_TEN_WORD = r"(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)"
AGE_IN_WORDS = re.compile(r"\b(?P<words>" + _A_TEN_WORD + r"(?:[-\s]" + _A_UNIT_WORD + r")?|"
                          + _A_TEEN_WORD + r"|" + _A_UNIT_WORD + r")\b", re.I)
# "hes five" and "shes seven" say an age just as plainly as "he is five" does, and the contracted
# word is the only thing between the person and the number, so it stands where "is" stands.
BEFORE_A_FIGURE = re.compile(r"(?:\b(?:is|are|was|were|aged)\s+|\bi\s+am\s+|\bim\s+|\bi'm\s+"
                            r"|\bam\s+|\b(?:he|she|they|it)(?:'s|s|'re|re)\s+)$", re.I)
AFTER_A_FIGURE = re.compile(r"\s*(?:years?\b(?:\s+old\b)?|yrs?\b(?:\s+old\b)?|yo\b)?\s*"
                            r"(?:[,.!?;:]|$|\band\b|\bbut\b|\bso\b)", re.I)
NOT_YEARS_AFTER = re.compile(r"\s*(?:weeks?|months?|days?|hours?|o.clock)\b", re.I)


def _the_numbers_in_words(text):
    """The line with an age said in words written as figures, so the age readers can read it."""
    if not text or not any(word in text.lower() for word in _NUMBER_IN_WORDS):
        return text

    def figure(match):
        if not BEFORE_A_FIGURE.search(text[:match.start()]):
            return match.group(0)
        after = text[match.end():]
        if NOT_YEARS_AFTER.match(after) or not AFTER_A_FIGURE.match(after):
            return match.group(0)
        total = sum(_NUMBER_IN_WORDS.get(part, 0)
                    for part in re.split(r"[-\s]+", match.group("words").lower()))
        return str(total) if total else match.group(0)

    return AGE_IN_WORDS.sub(figure, text)


def _how_tall(text):
    """The height a line states as the words to say it back in, or "".

    Only the shapes that name a height: a bare "im 5" is not one, and the inches have to be real
    ones, so "5 foot 14" is not a reading of anything.
    """
    match = HEIGHT_CM.search(text)
    if match:
        return match.group("cm") + "cm"
    match = HEIGHT_FEET.search(text) or HEIGHT_BARE.match(text)
    if not match:
        return ""
    inches = INCH_WORDS.get((match.group("inches") or "").lower(), match.group("inches") or "")
    if inches and not inches.isdigit():
        return ""  # a word nothing counts inches in, so the line names no height
    if inches and int(inches) >= 12:
        return ""  # 14 is not inches: the figure is not a height, and 5 foot would be a guess
    return match.group("feet") + " foot" + (" " + str(int(inches)) if inches else "")
# A birthday is a date, and the date is what they want back: "when's my birthday" -> "the 3rd of
# May". The asking word has to be there ("my birthday party is on saturday" is a party, not the
# date they were born), and the date has to look like one - a month or a figure - so a line that
# goes on about the day ("my birthday is going to be quiet") is not read as a date at all.
MONTHS = frozenset("""january february march april may june july august september october november
december jan feb mar apr jun jul aug sep sept oct nov dec""".split())
BIRTHDAY = re.compile(
    r"\bmy\s+(?:birthday|bday|dob|date of birth)\s*(?:'s|s)?\s*"
    r"(?:is|was|falls|:|=|on|in)\s+(?:on\s+)?(?:the\s+)?"
    r"([^,.;!?]{2,28})", re.I)
# The pronoun a birthday was said with, as the word the rest of the store fits to a person. The
# reader for it is with the other readers of somebody else's facts (`OTHER_BIRTHDAY`), because it
# needs the words a relation can be named by.
BIRTHDAY_PRONOUN = {"his": "he", "her": "she", "their": "they"}


# Where a date clause ends: the conjunction that starts the next person's clause ("my daughters
# birthday is in may AND MY SONS is in july"). Nothing said so, and the reader takes everything up
# to the next comma, so one date came out as "may and my sons is in jul" and the ask about the
# daughter's birthday answered with both halves in the first person.
A_DATE_CLAUSE_ENDS = re.compile(r"\s+(?:and|but|so)\s+(?=(?:my|our|his|her|their)\b)", re.I)


def _the_date_clause(date):
    """The date as far as the clause it is said in goes: "may and my sons is in july" -> "may"."""
    return A_DATE_CLAUSE_ENDS.split(str(date or ""))[0]


def _a_birthday_date(after):
    """The date words of a birthday clause, or "" when they name no date at all.

    A birthday is the one fact kept as a date, so the words after it have to look like one - a
    month or a figure - and a line that goes on about the day ("my birthday is going to be
    quiet", "my birthday is a big one this year") names no date.
    """
    date = _the_date_clause(" ".join(str(after or "").lower().split())).strip()
    date = date.rstrip(" .,;:")
    date = re.sub(r"^(?:in|on)\s+", "", date)  # "my birthday is in august" names august
    looks_like_a_date = any(word in MONTHS for word in re.split(r"[^a-z0-9]+", date)) \
        or re.search(r"\d", date)
    if not date or not looks_like_a_date:
        return ""
    if re.search(r"\b(?:to be|going|quiet|coming|soon|weekend|week|tomorrow|today)\b", date):
        return ""
    return date

# What they weigh, in the words people give it: "im 90 kilos", "i weigh 13 stone", "im 85kg".
# The unit is what tells a weight from an age ("im 34" is an age), so a bare figure is not one.
WEIGH_UNITS = {"kilo": "kilos", "kilos": "kilos", "kilogram": "kilos", "kilograms": "kilos",
               "kg": "kilos", "kgs": "kilos", "stone": "stone", "st": "stone",
               "pound": "pounds", "pounds": "pounds", "lb": "pounds", "lbs": "pounds"}


def _weight_unit(word):
    """The unit a weight was said in, however they pluralised it.

    "12 stones" is the same weight as "12 stone", and people write both; the store keeps one
    spelling for each unit, so the plural is looked up as its singular rather than listed twice.
    """
    word = str(word or "").lower()
    unit = WEIGH_UNITS.get(word)
    if unit is None and word.endswith("s"):
        unit = WEIGH_UNITS.get(word[:-1])
    return unit
# Only the present: a weight is a fact about now, so "i weighed 90 kilos last year" and "my weight
# will be 90 kilos" are not what they weigh, and storing either would have the ask say "You weigh
# 90 kilos." about a number that is not true today. A past or planned weight is left to whoever
# reads the line it is in, and the ask stays honest ("You haven't told me what you weigh.").
WEIGH = re.compile(r"\bi\s+weigh\s+(\d{2,3}(?:\.\d)?)\s*([a-z]+)\b", re.I)
WEIGH_IM = re.compile(r"\bi(?:m|'m| am)\s+(\d{2,3}(?:\.\d)?)\s*([a-z]+)\b", re.I)
# "my weight is 90 kilos" is the shape people use when they mean to be clear about it, and it is
# the same fact as "i weigh 90 kilos": read as one, or the ask that follows says they never told
# me, right after they did. The unit is what makes it a weight, as it is for the other shapes.
WEIGH_MY = re.compile(r"\bmy\s+weights?\s+(?:(?:is|are|works out at)\s+)?"
                      r"(\d{2,3}(?:\.\d)?)\s*([a-z]+)\b", re.I)

# A relation word that a noun follows is part of the noun ("my parents evening", "my mum house"):
# the line is about an evening, not the people in it. This is the handful of nouns that turn up
# there, because the word after a relation is what decides who the line is about.
COMPOUND_AFTER = frozenset("""evening wedding birthday party house home flat garden car room
meeting funeral anniversary holiday dinner tea lunch day night weekend bedtime visit health
money phone number address school work dog cat baby pram bath""".split())
# The compounds a relation can own: everything the list above has, less the one phrase that is
# an event of the school rather than a thing of the parents'.
COMPOUND_THAT_IS_THEIRS = COMPOUND_AFTER - {"evening"}

# The age said with its own name: "my age is 34", "my ages 34".
# A number with a unit after it is a measurement and not an age, the same as for anybody else:
# "my age is 68 kilos" said a weight and was filed as the age 68.
MY_AGE = re.compile(r"\bmy ages?(?:'s|\s+is|\s+just)?\s+(\d{1,2})\b"
                    r"(?!\s*(?:" + AGE_UNIT + r")\b)(?!\s*\d)", re.I)
# A word in front of a relation makes a different relation, and people say these far more often
# than the list below suggests: a stepson is not the son, and a grandson is not the son either, so
# each is kept as its own person. Built from the relations rather than listed again, so "step" and
# "grand" reach every relation a person can be. Without this the store filed "my stepmum is 40"
# under the person "stepmum" and then answered "how old is my stepmum" with a search hedge,
# because the readers on the way out were built from a narrower list than the writers.
# Only the relations that name one person: a "grandparents" or a "stepchildren" is a group the
# store keeps no age for, and reading one as a person answered "my grandparents are 80" with
# "Your grandparent is 80." - one figure for two people.
_STEP_OF = ("mum", "mom", "mother", "dad", "father", "son", "daughter", "brother", "sister")
_GRAND_OF = ("mum", "mom", "mother", "dad", "father", "son", "daughter", "child")
_BUILT_KIN = tuple(["step" + word for word in _STEP_OF]
                   + ["grand" + word for word in _GRAND_OF])
RELATIONS = ("daughter", "son", "twins", "partner", "husband", "wife", "mum", "mom", "mother",
             "dad", "father", "sister", "brother", "parents", "gran", "grandma", "grandad",
             "granny",
             "nana", "nan", "nanna", "grandmother", "grandfather", "grandpa", "aunt", "auntie",
             "aunty", "uncle", "niece",
             "nephew", "cousin", "friend", "neighbour", "neighbor", "boyfriend", "girlfriend",
             "fiance", "fiancee") + _BUILT_KIN + (
    "gran", "granddad", "stepchild")

# The relations people type short. `lexicon.CHAT` already spells them out for the understanding
# engine ("gf", "bf", "hubby", "missus", "bairn", "bubba", "m8"), and a person is the same person
# however they were said: "my gf is vegetarian" was read as the user's own diet, because the word
# "gf" named no relation to this file and the clause fell through to the "my", so the bot said
# nothing about the girlfriend and would have warned the person about a diet of their own. Read
# here, the short word is a relation everywhere this file looks for one, and it is kept as the
# full word, so "what's my girlfriend's name" still finds the name filed under "gf".
SPOKEN_RELATION = {said: full for said, full in lexicon.CHAT.items()
                   if full in RELATIONS or (full.endswith("s")
                                            and full[:-1] in RELATIONS)}
SPOKEN_RELATION = {said: (full[:-1] if full.endswith("s") and full[:-1] in RELATIONS else full)
                   for said, full in SPOKEN_RELATION.items()}
RELATIONS = RELATIONS + tuple(word for word in SPOKEN_RELATION if word not in RELATIONS)

# A person named in a line, so a bare "he died" after "my grandad was ill" is the grandad and not
# the one animal the store holds.
PEOPLE_WORD = re.compile(r"\b(?:" + "|".join(sorted(RELATIONS, key=len, reverse=True)) + r")s?\b"
                         r"|\b(?P<name>(?:my|his|her|their|our)\s+[a-z]{3,}\b)", re.I)

# "my mum is called janet", "my son is 8": the relation names which person the name or the age
# belongs to. They are theirs, not the user's, the same way "my son is allergic to nuts" is.
# A figure with a unit or a currency after it is a measurement, not how old anybody is:
# "my mum is 5 foot 4" is her height.
# The number has to end where it ends: without the bare `(?!\d)` a two-digit figure can give up a
# digit and slip past the unit, which read "my mum is 72 kilos" as age 7 and "shes 12 miles away"
# as age 1.
NOT_A_UNIT = (r"(?![\d.,]\d)(?!\d)"
              r"(?!\s*(?:foot|feet|ft|cm|centimet|inches?|inch|stone|st|kg|kilo|lbs?|lb|metres?"
              r"|meters?|miles?|mph|hours?|hrs?|mins?|minutes?|weeks?|percent|%))")
# The words a person can be to the user here: the relations, and the everyday ones people name
# in the same breath ("my nan is 81", "my flatmate is 27"). Kept local to this reader so the
# people the store keeps stay the ones RELATIONS names.
# The people in an ordinary person's life who are not family: somebody in a role, named the same
# way a relation is ("my tutor is 40", "my tutor is called mrs owens", "whats my tutors name").
# They were missing from every person list, so a name or an age said about a tutor or a childminder
# was filed nowhere and the ask about them fell to whatever card the line's other words hit. Kept
# to roles a person holds, so a word that is as often a thing (a coach, a cleaner, a trainer) stays
# out of it.
ROLE_PEOPLE = ("tutor", "childminder", "carer", "hairdresser", "barber", "instructor")
KIN = RELATIONS + (
    "nan", "gran", "granddad", "grandmother", "grandfather", "auntie", "niece", "nephew",
    "colleague", "boss", "flatmate", "housemate", "godson", "goddaughter", "manager",
    "landlord", "landlady", "lodger",
    # "my mate dave is coming over" is how half the country names a friend, and the store knew
    # nobody by it: the name was filed nowhere and "whats my mates name" was answered "I don't
    # know enough to answer that honestly". The compound words above still win, because
    # `KIN_WORDS` is taken longest first and "flatmate" is read before "mate" is tried.
    "mate") + ROLE_PEOPLE + (
    # "my girl is 7" and "my boy is 4" are how people name a child far more often than "my
    # daughter". Not a relation in RELATIONS, because that list is what the rest of the store
    # treats as a person everywhere, and a "boy" in a line is not always one.
    "girl", "boy",
    # A baby is a person the store keeps an age for, and the words people use for one are how a
    # question about them is put: "how old is the baby", "how old is our little one". They are in
    # this list so the ask names the person the age was kept under.
    "baby", "little one", "wee one")
# "my youngest is 3", "my eldest is 9": how people name one of several children, with no noun at
# all. They are a person only where no relation word follows, because "my eldest son is 8" is the
# son, and filing an "eldest" beside him makes two children of one.
# "my toddler is 18 months", "my little one is 3": a word that names one person with no
# relation after it, beside the words above. Without them the line named nobody, so the
# age was never kept, "how old is my toddler" answered a card about toddlers in general,
# and the ask back eight turns later said the chat had never been told.
ALONE_PERSON = ("youngest", "eldest", "oldest", "baby", "toddler", "newborn", "little one")
# An adjective in front of the word for a person names the same person: "my little girl is 2",
# "my eldest son is 8", "my big boy is 5". It is the commonest way people say it, and without it
# the line named nobody - the store filed nothing while the acknowledgement said "Noted: your
# eldest son is 8.", so the bot told the person it had kept the fact and then denied it a turn
# later ("You haven't told me how old your son is.").
PERSON_MODIFIER = ("little", "big", "small", "tiny", "eldest", "oldest", "youngest", "baby",
                   "middle", "older", "younger", "teenage", "grown", "first", "second", "third",
                   "fourth", "other", "poor", "darling", "littlest", "new")
MODIFIER_BEFORE = r"(?:(?:" + "|".join(PERSON_MODIFIER) + r")\s+)?"
# "in law" is the same modifier however it is typed ("my brother-in-law", "my sister in law",
# "my inlaws"), and the person it names is the in-law, not the brother: "my brother-in-law is
# called raj" filed a person called brother with no name, and the next "whats his name" was told
# "You haven't told me your brother's name." The suffix is read with the relation.
IN_LAW = r"(?:[ \t]*-?[ \t]*in[ \t]*-?[ \t]*laws?)?"
# The same phrase as a word on its own, for the readers that ask whether one word names an
# in-law ("is my brother in law a relation the store knows?").
IN_LAW_WORD = re.compile(r"^[a-z]+(?:[ \t]*-?[ \t]*in[ \t]*-?[ \t]*laws?)$", re.I)


def an_in_law(word):
    """Whether a person's word names an in-law: "brother in law", "mother-in-law", "inlaws"."""
    return bool(IN_LAW_WORD.match(str(word or "").strip()))


# The same suffix at the front of the words that follow a relation word: "brother-in-law" leaves
# "-in-law is coming" behind the match, and "sister in law" leaves " in law is coming".
IN_LAW_AFTER = re.compile(r"[ \t]*-?[ \t]*in[ \t]*-?[ \t]*laws?\b", re.I)
# Longest first: "stepmum" has to be read as one word before "mum" is tried, and the same for
# "grandson" and "son". Exported so the store asks about exactly the people it can file, which is
# what kept "my stepmum is 40" answerable but "how old is my stepmum" a shrug.
KIN_WORDS = tuple(sorted(set(KIN), key=len, reverse=True))
_RELATION_WORDS = "(?:" + "|".join(KIN_WORDS) + ")" + IN_LAW
# The word a person can be named by with no noun after it, for the readers that can tell the
# two apart: "my youngest is 3" is somebody, and the "eldest" in "my eldest son is 8" is not.
_A_PERSON = "(?:" + _RELATION_WORDS + "|" + "|".join(ALONE_PERSON) + ")"
# Every word that can be a person, and every adjective that can stand in front of one: neither is
# a name, so neither can be read as the name of the person the line just named.
_A_WORD_FOR_A_PERSON = frozenset(KIN) | frozenset(ALONE_PERSON) | frozenset(PERSON_MODIFIER)
# A title in front of a name belongs with it. "my landlord is called mr patel" was read as a
# person called "Mr", and "my mum is called mrs smith" the same, because the name was one word
# and the title is one word. The title takes the word after it, however it is punctuated.
# Longest first: "mr" would take the first two letters of "mrs" and leave the s behind.
TITLE = r"(?:professor|miss|mrs|mr|ms|dr|sir|prof|dame|lord|lady|rev|capt|sgt)\.?"
# A title on its own names nobody, so it is not a name: "my sister is called mr smith" is Mr
# Smith, and the store must never answer "Your sister is called Mr." The other readers ("my
# sister is called ...") are built from `_NAME` as well, so none of them can file the title alone
# as the name while the next one files the whole of it - which is how the store came to hold two
# people called "mr" and "Mr smith" and to answer "how old is your landlord" with "Your landlord
# is called Mr".
TITLE_WORDS = frozenset(re.findall(r"[a-z]+", TITLE))
# A title is the one thing that says whether a person is a he or a she: "my landlord is called
# mr smith" then "whats his name" is Mr Smith, and "whats her name" is not answered as his.
TITLE_GENDER = {"mr": "he", "sir": "he", "lord": "he", "mrs": "she", "ms": "she", "miss": "she",
                "lady": "she", "dame": "she"}
_NAME = (r"(?P<name>" + TITLE + r"(?:\s+[A-Za-z][A-Za-z'\-]{1,19})?"
         r"|[A-Za-z][A-Za-z'\-]{1,19})")
# The naming verb is only read as one when the line has already said it is talking about the
# person: "my mum is called janet", "my mums called janet". Without that, "called" and "named"
# are the line's own verbs and the word after them is not a name at all - "my mum called me
# yesterday" and "my sister named her baby after me" would file a person called Me and a person
# called Her, and the store would say them back.
RELATION_NAME = re.compile(
    r"\b(?:my|our)\s+" + MODIFIER_BEFORE + r"(?P<who>" + _A_PERSON + r")(?:\s+is\s+|'s\s+|s\s+)"
    r"(?:called|named)\s+" + _NAME, re.I)
# The same fact said with "have": "i have a son called jack", "we've got a daughter named amy".
# Every relation pattern above needs the possessive, so this shape kept the person and dropped
# the name: the bot answered "Noted: you have a son called jack." and then, asked, said "You
# haven't told me your son's name." With "have a" in front, "called" is unambiguously the naming
# verb - the line has already said the person exists - so no further guard is needed.
RELATION_HAVE_NAME = re.compile(
    r"\b(?:i|we)\s*(?:'ve|ve|have|got)(?:\s+got)?\s+"
    r"(?:an?\s+|one\s+|two\s+|three\s+)?"
    r"(?P<who>" + _RELATION_WORDS + r")s?\s+(?:called|named)\s+" + _NAME, re.I)
# "my mum's name is janet", "my brothers name is tom": the same fact said the other way round.
RELATION_POSSESSIVE_NAME = re.compile(
    r"\b(?:my|our)\s+" + MODIFIER_BEFORE + r"(?P<who>" + _A_PERSON + r")(?:'s|s)?\s+name\s+(?:is\s+)?"
    + _NAME, re.I)
# "my brother tom is 12", "my friend sarah is 40": the name sits between the relation and the
# age, so one line gives the store both.
# The word between the person and the age is their name, so it is not another word for a person:
# "my eldest son is 8" is the son at eight, and read the other way it files an "eldest" beside him.
_NOT_A_PERSON_NAME = r"(?!(?:" + "|".join(sorted(_A_WORD_FOR_A_PERSON, key=len, reverse=True)) + r")\b)"
RELATION_NAMED_AGE = re.compile(
    r"\b(?:my|our)\s+" + MODIFIER_BEFORE + r"(?P<who>" + _A_PERSON + r")\s+"
    r"(?P<name>" + _NOT_A_PERSON_NAME + r"[A-Za-z][A-Za-z'-]{1,19})"
    r"\s+(?:is|'s|was)\s+(?P<age>\d{1,3})" + NOT_A_UNIT, re.I)
# The age given as the thing asked about rather than as a figure after the person: "my mums age is
# 68", "my sons age is 7". The word between the person and the figure is the fact being given, so
# it is that person's age; read as a name it filed "Age" against them and lost the age the line
# gave, and the store then said "Your son is called Age."
RELATION_POSSESSIVE_AGE = re.compile(
    r"\b(?:my|our)\s+" + MODIFIER_BEFORE + r"(?P<who>" + _A_PERSON + r")s?'?s?\s+ages?\s+"
    r"(?:is|was|'s)\s+(?P<age>\d{1,3})" + NOT_A_UNIT, re.I)
# The age said as the birthday coming: "my son is turning 7", "my daughter is turning 5 on friday".
# The verb between the person and the figure meant nothing was kept - the store held no age, the
# present asked for next turn was a punt, and "how old is he" answered "You haven't told me".
RELATION_AGE = re.compile(
    r"\b(?:my|our)\s+" + MODIFIER_BEFORE + r"(?P<who>" + _A_PERSON + r")(?:\s+is\s+|'s\s+|s\s+|\s+)?"
    r"(?:turning\s+|turns\s+)?(?P<age>\d{1,3})" + NOT_A_UNIT, re.I)
# "the eldest is 7", "the little one is 4": a child named by their place in the family takes the
# definite article as readily as a possessive. It is how the second of two children is said - "our
# youngest is 4 and the eldest is 7" - and read with the possessive only, the second age was filed
# against nobody, so the ask about that child ("how old is the eldest") fell through to the world
# and came back as advice about something else. The article says "mine" here because the place
# word is the whole of the noun phrase: "the eldest son" is the son, and that shape is left alone.
THE_PLACE_AGE = re.compile(
    r"\bthe\s+(?P<who>" + "|".join(sorted(ALONE_PERSON, key=len, reverse=True)) + r")"
    r"(?:\s+is\s+|'s\s+|s\s+)(?P<age>\d{1,3})" + NOT_A_UNIT, re.I)
# A baby is somebody people give an age for with no relation word in the line: "my baby is 4
# months old", "the baby is 18 months". The readers above need a word like "son" or "daughter",
# so the age was filed nowhere and the store said a turn later that it had never been told.
BABY_AGE = re.compile(
    r"\b(?:my|our|the)\s+(?:(?P<who>baby)|(?P<little>little\s+one|wee\s+one)|newborn|tot)"
    r"\s+(?:is|'s|was|are)\s+"
    r"(?P<age>\d{1,3})(?![\d.,]\d)(?!\d)\s*(?P<unit>months?|years?)\b"
    r"(?!\s*(?:away|ago|later|early|behind|off))", re.I)
# The age as the name of the baby: "our 7 month old", "my 18 month old is crawling". The figure
# sits inside the phrase that names the person, so no reader above - all of which want "is" after
# the person - found it, and the age the line gave away was filed nowhere.
MONTH_OLD_BABY = re.compile(
    r"\b(?:my|our|the)\s+(?P<age>\d{1,2})(?![\d.,]\d)(?!\d)\s*(?:months?)\s+old\b"
    r"(?!\s*(?:away|ago|later|early|behind|off))"
    # The phrase has to name a person, and "old" is what a thing is too: "our 7 month old labrador
    # needs walks", "my 6 month old phone keeps dying", "our 9 month old puppy is chewing". So the
    # phrase must end the clause or be followed by a verb or a word for the person - never by
    # another noun, which is the thing being described.
    r"(?=\s*(?:[,.;!?]|$|\s+(?:is|was|are|were|has|have|had|keeps|needs|wakes|sleeps|who|that|and|"
    r"but|eats|walks|loves|will|can|does|did|goes|cries|feeds|naps|sits|crawls|started|still|now|"
    r"baby|boy|girl|son|daughter|child|little one|wee one)\b))", re.I)
# The name given without the naming verb: "my mum is sue", "my son is tom". A word after "is" is
# an adjective far more often than a name ("my mum is tired", "my brother is older"), so the word
# has to look like a name and not like the state it would otherwise be - see `_bare_name`.
RELATION_BARE_NAME = re.compile(
    r"\b(?:my|our)\s+" + MODIFIER_BEFORE + r"(?P<who>" + _A_PERSON + r")(?:\s+is\s+|'s\s+|s\s+)"
    r"(?P<name>[A-Za-z][A-Za-z'-]{1,19})\b", re.I)
# Two people given one after the other: "my mum and dad are dave and sue". The line names two
# people and two names and no more, so the pair is kept whole rather than split by guesswork.
RELATION_PAIR_NAMES = re.compile(
    r"\b(?:my|our)\s+(?P<who1>" + _RELATION_WORDS + r")\s+and\s+(?P<who2>" + _RELATION_WORDS
    + r")\s+(?:are|were)\s+(?P<name1>[A-Za-z][A-Za-z'-]{1,19})\s+and\s+"
    r"(?P<name2>[A-Za-z][A-Za-z'-]{1,19})\b", re.I)
# A group given its names in one breath: "my kids are called jack and emma", "my son and
# daughter are called jack and emma". The pair reader above takes the line with no naming verb
# ("my mum and dad are dave and sue"), and a group word ("kids", "children") is not a relation
# at all, so this line was answered "Got it" and the two names were never kept.
GROUP_NAMED_NAMES = re.compile(
    r"\b(?:my|our)\s+(?P<who>" + _RELATION_WORDS + r"|kids?|children)"
    r"(?:\s+and\s+(?P<who2>" + _RELATION_WORDS + r"))?\s+(?:are|were)\s+(?:called|named)\s+"
    r"(?P<rest>[A-Za-z][A-Za-z'-]{1,19}(?:\s*(?:,|and)\s*[A-Za-z][A-Za-z'-]{1,19}){1,3})\b",
    re.I)
# The same pair shape with an age on each: "my kids are ada 7 and sam 4". A group of people is
# the only relation this reads, because one person is never two name-and-age pairs.
GROUP_NAMED_AGES = re.compile(
    r"\b(?:my|our)\s+" + MODIFIER_BEFORE + r"(?P<who>" + _A_PERSON + r"|kids?|children|child)\s+(?:are|were)\s+"
    r"(?P<rest>[a-z][a-z'-]{1,19}\s+\d{1,3}(?:\s*(?:,|and)\s*[a-z][a-z'-]{1,19}\s+\d{1,3}){1,3})",
    re.I)
# The person named with a clause about them: "its for my daughter whos 9", "my son, who is 7,
# starts school in september". The "who" belongs to the person named before it, so the number
# after it is their age exactly as "my daughter is 9" is: without this the age was dropped and
# "how old is my daughter" said she had never told.
RELATION_WHOS_AGE = re.compile(
    r"\b(?:my|our)\s+(?P<who>" + _RELATION_WORDS + r")\s*,?\s+who(?:['\u2019]?s)?\s+"
    r"(?:is\s+)?(?P<age>\d{1,3})\b" + NOT_A_UNIT, re.I)
# A relation of a relation: "my partner's mum is 68", "my sisters husband is 41", "my mums friend
# julie is 70". The person is the pair, not the first word, and the store filed it as neither: the
# line was read as two people with no age, so the reply said "Noted: your partner's mum is 68." and
# then, asked, "You haven't told me how old your partner is" - the wrong person's age. The pair is
# kept as one person, in the words the line used ("partner's mum"), and the ask that names the same
# pair finds it.
CHAINED_RELATION_AGE = re.compile(
    r"\b(?:my|our)\s+" + MODIFIER_BEFORE + r"(?P<first>" + _A_PERSON + r")"
    r"(?:'s|\u2019s|s)\s+(?P<second>" + _A_PERSON + r")"
    r"(?:\s+(?P<name>(?!(?:is|was|'s)\b)[A-Za-z][A-Za-z'-]{1,19}))?"
    r"\s*(?:'s|\u2019s|is|was)\s+(?P<age>\d{1,3})" + NOT_A_UNIT, re.I)


# The same pair named by an ask rather than given an age: "how old is my partner's mum", "and my
# sisters husband?". The pair is the person, so the age filed against "partner's mum" is found by
# the question that names her the same way.
CHAINED_PERSON = re.compile(
    r"\b(?:my|our)\s+" + MODIFIER_BEFORE + r"(?P<first>" + _A_PERSON + r")"
    r"(?:'s|\u2019s|s)\s+(?P<second>" + _A_PERSON + r")\b", re.I)


def a_chained_person(text):
    """"partner's mum" for "my partners mum", or "" when the line names no pair of people."""
    found = CHAINED_PERSON.search(str(text or ""))
    if not found:
        return ""
    first = re.sub(r"(?:'s|\u2019s|s)$", "", found.group("first").lower())
    return first + "'s " + found.group("second").lower()


# "my mum is called janet and she is 72": after the relation is named, a pronoun is that person.
# "they" is here too: "theyre 12" is somebody's age said the way people type it, and the reply is
# the same kind of reply as "shes 12".
# The figure of a pronoun's age as people write it: a digit, or the word for it, with the way an
# approximate age is said in front ("hes about five years old", "shes nearly seven"). "hes five"
# was read as nothing at all while "hes 5" was read as the son's age, so a person who spelled the
# number out - which is most people, most of the time - was told "You haven't told me how old your
# son is" about a line that had just said it.
# The words that put an age in the future rather than now: "next month", "in june", "on friday".
# Written once so a reader that keeps the age they have now can stand aside for the one that keeps
# a birthday, instead of taking the figure and losing the day it was said with.
AGE_TO_COME_TAIL = (r"(?!\s+(?:next\s+(?:week|month|year|spring|summer|autumn|winter)|"
                    r"(?:in|on)\s+[a-z]{3,9})\b)")
# How the person feels about it is a thing they told you, and it outranks the figure:
# "shes turning 40 and she hates being the centre of attention" is a line about a sister, and
# reading the 40 as a fact to file turned a warm reply into a receipt for it. This is a check
# rather than part of the pattern below because it only applies to an age said with the word
# that says it is coming: "shes 70 and she hates fuss" is a fact with an aside, and the aside
# has always been echoed back to the person, which is the reply that line wants.
HOW_THEY_FEEL = re.compile(r"\b(?:hate|hates|hated|hating|love|loves|loved|likes?|liked"
                           r"|wants?|wanted|prefers?|dreads?|shy|embarrassed|nervous"
                           r"|excited|proud|rather)\b", re.I)

_AN_AGE_IN_WORDS = ("(?:" + _A_TEN_WORD + r"(?:[-\s]" + _A_UNIT_WORD + r")?|"
                    + _A_TEEN_WORD + "|" + _A_UNIT_WORD + ")")
PRONOUN_AGE = re.compile(r"\b(?P<who>she|he|they)(?:'s|s|re|'re)?(?:\s+(?:is|are))?"
                         r"(?:\s+(?:about|around|nearly|almost|roughly|maybe|probably|just|only"
                         r"|now|already|still))*\s+"
                         # The word that says the age is coming, which the relation readers have
                         # always taken: "my daughter is turning 6" was read and "shes turning 6"
                         # was not, so the age the chat had just been given was filed nowhere and
                         # the next ask was a punt. Same words, same reading, whoever they are
                         # said of.
                         r"(?P<come>turning\s+|turns\s+|will\s+be\s+|is\s+going\s+to\s+be\s+)?"
                         r"(?P<age>\d{1,3}|" + _AN_AGE_IN_WORDS + r")" + NOT_A_UNIT
                         # A birthday still to come is `AGE_TO_COME`'s: "hes turning 9 in june"
                         # is the age he is not yet, and reading it here as the age he is now
                         # replaced the 8 the chat had been told with the 9.
                         + AGE_TO_COME_TAIL, re.I)


def a_stated_number(word):
    """The number a person wrote as a word or a digit, or None when it says no number at all."""
    said = str(word or "").strip().lower()
    if not said:
        return None
    if said.isdigit():
        return int(said)
    total = sum(_NUMBER_IN_WORDS.get(part, 0) for part in re.split(r"[-\s]+", said))
    return total or None


def a_person_word(word):
    """A person's word said plainly: "brother in law" and "brother-in-law" are one person.

    The store keeps one entry per person, and the pronoun that fits her is one word: "my
    brother-in-law" and "my brother in law" are the same brother in law, said two ways.
    """
    plain = " ".join(re.sub(r"[ \t]*-[ \t]*", " ", str(word or "").strip().lower()).split())
    # "my mother in laws name" is the same person as "my mother in law": the plural of the
    # suffix is how the possessive gets typed, and one person is filed under one word.
    return re.sub(r"\bin laws$", "in law", plain)
def _the_person(found, who, name=""):
    """The entry for one person, when the word for the relation can be more than one of them.

    "my son jack is 6 and my son sam is 9" is two sons, so the word "son" alone does not say
    which of them an age belongs to: the name in the clause does. A fact with no name of its own
    ("he is 9", "my son is 9") still goes on the person the chat just named, so an entry with no
    name is a match for anything.
    """
    who = a_person_word(who)
    for one in found:
        if one.get("who") != who:
            continue
        if name and one.get("name") and str(one["name"]).lower() != str(name).lower():
            continue
        return one
    return None


def _relation_facts(text):
    """A relation's own name and age: [{"who": "mum", "name": "Janet", "age": "72"}]."""
    found = []
    text = stated_not_asked(text)
    if not text:
        return found

    def entry(who, name=""):
        """The entry for this person: one word for the relation is one person, unless a second
        name is said for it.

        "my son jack is 6 and my son sam is 9" has two sons, and the word they are both filed
        under is the same word, so filing by the word alone kept one entry whose name was the
        first and whose age was the last - one child made out of two. A name said for the
        relation is what tells the two apart, and a fact with no name of its own still goes on
        the person the chat just named.
        """
        who = a_person_word(who)
        for known in found:
            if known.get("who") != who:
                continue
            if name and known.get("name") and str(known["name"]).lower() != str(name).lower():
                continue
            return known
        made = {"who": who}
        found.append(made)
        return made

    for match in RELATION_POSSESSIVE_AGE.finditer(text):
        entry(match.group("who").lower())["age"] = int(match.group("age"))
    for pattern in (RELATION_NAME, RELATION_POSSESSIVE_NAME, RELATION_NAMED_AGE,
                    RELATION_HAVE_NAME):
        for match in pattern.finditer(text):
            name = _finish(match.group("name"))
            if not name or _not_a_name(match.group("name"), strict_ly=False):
                continue
            if not _name_after_a_title(match.group("name")):
                continue
            if str(match.group("name")).lower() in _A_WORD_FOR_A_PERSON:
                # "my eldest son is 8": the word after the person is another word for a person,
                # not a name, and reading it as one filed an "eldest" beside the son.
                continue
            # Main's `_tidy_a_titled_name` is the newer reading of the same name; this branch's
            # change is the name as the key for two people with one word, which is elsewhere.
            entry(match.group("who").lower(), _tidy(name)).setdefault(
                "name", _tidy_a_titled_name(name))
    for match in RELATION_BARE_NAME.finditer(text):
        name = _bare_name(match.group("name"))
        if name:
            entry(match.group("who").lower(), name).setdefault("name", name)
    for match in RELATION_PAIR_NAMES.finditer(text):
        # Two names under two people are kept as the pair they were said as: "my mum and dad are
        # dave and sue" does not say which name is whose, and the order is only a guess, so
        # pairing them off would file a fact about their mother they never gave. Each name with
        # its own age ("my kids are ada 7 and sam 4") is the line doing the pairing, and that is
        # read below.
        names = [_bare_name(match.group("name1"), pair=True),
                 _bare_name(match.group("name2"), pair=True)]
        if all(names):
            who1 = match.group("who1").lower()
            who2 = match.group("who2").lower()
            found.append({"who": who1 + " and " + who2, "names": names})
    for match in GROUP_NAMED_NAMES.finditer(text):
        said = [word for word in re.split(r"\s*(?:,|and)\s*", match.group("rest")) if word]
        names = [_bare_name(word, pair=True) for word in said]
        if len(names) < 2 or not all(names):
            continue
        who = match.group("who").lower()
        if match.group("who2"):
            who = who + " and " + match.group("who2").lower()
        found.append({"who": who, "names": names})
    for match in GROUP_NAMED_AGES.finditer(text):
        pair = re.findall(r"([A-Za-z][A-Za-z'-]{1,19})\s+(\d{1,3})", match.group("rest"))
        if len(pair) < 2:
            continue
        named = [(said, _bare_name(said, pair=True), age) for said, age in pair]
        if not all(name for _, name, _ in named):
            continue  # one word that is not a name makes the whole list somebody else's line
        for who, name, age in named:
            made = {"who": match.group("who").lower(), "name": name, "age": int(age)}
            if made not in found:
                found.append(made)
    for match in BABY_AGE.finditer(text):
        # The unit decides which fact it is, because a baby's age is kept in months: "4 months"
        # said back as "4" would read as four years.
        # The age is filed under the word the line used for the baby, because that is the word
        # every list of people the asks read is looked up by: "our little one is 10 months" then
        # "how old is our little one" found nobody when it was filed under "baby".
        made = entry(str(match.group("who") or match.group("little") or "baby").lower())
        if str(match.group("unit")).lower().startswith("month"):
            made.setdefault("months", int(match.group("age")))
        else:
            made.setdefault("age", int(match.group("age")))
    for match in MONTH_OLD_BABY.finditer(text):
        # The age is the name of the baby here, with no "is" after it: "our 7 month old", "my 18
        # month old". Nobody kept it, so "how old is he" after "our 7 month old is waking every
        # two hours" got a search hedge. A baby is what the line is about, and months is how the
        # age is kept.
        entry("baby").setdefault("months", int(match.group("age")))
    for pattern in (RELATION_AGE, THE_PLACE_AGE, RELATION_NAMED_AGE, RELATION_WHOS_AGE):
        # A clause ("my brother whos 30 is coming to stay") ends where the next verb starts, so
        # the age is read when what follows it is not a unit, rather than only when it is one of
        # the words an age ends with. The plain shapes keep the short list: "my son is 8 grams"
        # is a weight and not a birthday.
        clause = pattern is RELATION_WHOS_AGE
        for match in pattern.finditer(text):
            # The number is an age only when what follows it is the end of the fact or the words
            # an age is said with. Without this, "my mum is 68 kilos" matched the 6 in 68 and filed
            # a six-year-old, because 68 itself is followed by a unit and the pattern could take a
            # shorter number to get past it.
            rest = text[match.end():]
            months = _month_age_after(text, match.end())
            if months:
                # A baby's age is said in months and kept that way: "18 months old" is not
                # eighteen years old, and denying it on the next turn is worse than either.
                entry(match.group("who").lower()).setdefault("months", int(match.group("age")))
                continue
            if not (clause or AGE_TAIL.match(rest)):
                continue
            # The age belongs to the person the clause names, not to whoever shares their word
            # for the relation: "my son jack is 6 and my son sam is 9" is six and nine, not two
            # sons of nine. It is kept as a number, the way every other reader files an age: as a
            # string it was a fact the store held and the ask could not read, so "how old are my
            # kids" denied an age it had just been told.
            named = match.groupdict().get("name")
            known = (entry(match.group("who").lower(), _tidy(named)) if named
                     else entry(match.group("who").lower()))
            known.setdefault("age", int(match.group("age")))
    for tasted in taste.read_other(text):
        # What one of them likes is a fact about that person, filed on them like an age: "my
        # sister loves cooking" left the sister in the store with nothing about her in it, and
        # "what does my sister like" was a search hedge about somebody the chat had just named.
        thing = tasted.get("thing")
        if not thing:
            continue
        key = "likes" if tasted.get("how") == "yes" else "dislikes"
        if tasted.get("eaten") and set(str(thing).split()) & DIET_GROUP:
            # "she doesnt eat meat" is her diet, which the line's own reader has. Only a whole
            # food group is a diet, though: "wont eat vegetables" is a fussy eater rather than a
            # way of eating, and "my daughter wont eat peas" is one food she will not eat, which
            # the diet reader leaves alone (it wants a group). The store kept nothing at all
            # then, so the person had to say it twice and "what wont she eat" was answered "You
            # haven't told me what your daughter eats". A food they will not eat is a taste like
            # any other, so it goes on the list the dislike ask reads.
            continue
        who = tasted.get("who")
        if who:
            known = entry(who)
        else:
            known = next((made for made in found
                          if made.get("pronoun") == tasted.get("pronoun")
                          and not made.get("who")), None)
            if known is None:
                known = {"pronoun": tasted.get("pronoun") or ""}
                found.append(known)
        held = known.setdefault(key, [])
        if thing not in held:
            held.append(thing)
    for match in OTHER_BIRTHDAY.finditer(text):
        # Whose birthday it is: the relation the line names ("my mums birthday") or the pronoun,
        # which the store folds onto the person the chat is about the way it does an age.
        date = _a_birthday_date(match.group("date"))
        if not date:
            continue
        said_who = (match.groupdict().get("who") or "").lower()
        said_pronoun = (match.groupdict().get("pronoun") or "").lower()
        if said_who:
            known = entry(said_who)
        else:
            pronoun_word = BIRTHDAY_PRONOUN.get(said_pronoun, said_pronoun)
            person = _the_person_the_pronoun_is(text, match.end(), pronoun_word)
            if person:
                known = entry(person)
            else:
                known = next((made for made in found
                              if made.get("pronoun") == pronoun_word and not made.get("who")), None)
                if known is None:
                    known = {"pronoun": pronoun_word}
                    found.append(known)
        known.setdefault("birthday", date)
    pronoun = PRONOUN_AGE.search(text)
    if pronoun and a_stated_number(pronoun.group("age")) is None:
        pronoun = None
    if pronoun and pronoun.group("come"):
        # Only what the line says in the same breath as the age: "shes turning 40. she hates
        # being the centre of attention" is two thoughts, and the second is not about the 40.
        same_breath = re.split(r"[.!?]", text[pronoun.end():], 1)[0]
        if HOW_THEY_FEEL.search(same_breath):
            pronoun = None
    if pronoun and _month_age_after(text, pronoun.end()):
        # The same month age with only a pronoun: "shes 18 months old" after "my daughter...".
        fits = SHE if pronoun.group("who").lower() == "she" else HE
        for known in found:
            if "age" not in known and "months" not in known and known.get("who") in fits:
                known["months"] = a_stated_number(pronoun.group("age"))
                break
        else:
            # Nobody in this line took the age, which is not the same as nothing in `found`: a
            # line can hold a taste about the same person ("shes seven and loves dinosaurs") and
            # the taste entry is not where the age belongs, so the age was dropped and
            # "what age is she" denied an age the chat had just been given.
            if not any("months" in made for made in found):
                found.append({"months": a_stated_number(pronoun.group("age")),
                              "pronoun": pronoun.group("who").lower()})
    elif pronoun and AGE_TAIL.match(text[pronoun.end():]):
        # The line has to name somebody for "she" to be them: a bare "she is 72" with nobody
        # named is not a fact about anyone the store can name. And the pronoun has to fit: "my
        # mum is called janet and he is 72" is somebody else's 72, not the mum's.
        word = pronoun.group("who").lower()
        # The number is kept as one, the way every other reader files an age: as a string it was
        # a fact the store held and the answers could not read, so "my son is called tom" then
        # "he is 6" then "what should i get him" gave the grown-up list, and a birthday said
        # after it ("she turns 8 in june") replaced the age she is now instead of sitting beside
        # it. A month age above has always been read as a number.
        # "they" is nobody in particular, so it fits no relation and stands on its own.
        fits = SHE if word == "she" else HE if word == "he" else frozenset()
        for known in found:
            if "age" not in known and known.get("who") in fits:
                known["age"] = a_stated_number(pronoun.group("age"))
                break
        if not any("age" in made for made in found):
            # Nobody is named in this line, so the age is filed against the pronoun and the
            # store fills in the person the chat is about: "my mum is coming to stay next
            # weekend" then "shes 78 and doesnt walk far" is the mum's age, and without this
            # nothing held the two together and "how old is my mum" said she had never said.
            word = pronoun.group("who").lower()
            person = _the_person_the_pronoun_is(text, pronoun.start(), word)
            if person:
                # The line named them before the pronoun ("my mum, shes 60"): the age is theirs
                # rather than the store's guess at who "she" is.
                found.append({"who": person, "age": a_stated_number(pronoun.group("age"))})
            else:
                found.append({"age": a_stated_number(pronoun.group("age")), "pronoun": word})
    return [known for known in found if len(known) > 1 or "who" not in known]

# Who a bare "she" or "he" most likely is, so "my mum is coming sunday" then "she doesnt eat
# meat" is the mum's diet and not a stray fact about nobody. The person a relation names is
# spelled the way the store files them ("brother in law", no hyphen).
_SHE_SAID = frozenset("""mum mom mother daughter sister wife grandma granny nana nan grandmother aunt
niece girlfriend fiancee partner friend neighbour neighbor colleague girl boss manager landlord
landlady cousin flatmate housemate roommate lodger mate""".split())
_HE_SAID = frozenset("""dad father son brother husband grandpa grandad grandfather uncle nephew
boyfriend fiance partner friend neighbour neighbor colleague boy boss manager landlord landlady
cousin flatmate housemate roommate lodger mate""".split())


def _kin_pronoun(word):
    """The relation inside a step- or grand-word, so the pronoun it takes can be read from it."""
    for prefix in ("step", "grand"):
        if word.startswith(prefix) and word[len(prefix):] in _SHE_SAID | _HE_SAID:
            return word[len(prefix):]
    return word


# A word in front of a relation does not change whose pronoun it takes: a stepmum is a she and a
# grandson is a he. Without this a person the store can file could not be pointed at with "she"
# or "he", so "my stepmum is 40" then "how old is she" found no mother.
# An in-law is the relation they are an in-law of, said with the suffix: "my sister-in-law"
# and "my sister in law" are one person, and a pronoun has to be able to point at her.
SHE = (_SHE_SAID | frozenset(word for word in _BUILT_KIN if _kin_pronoun(word) in _SHE_SAID)
       | frozenset(("gran", "sister in law", "mother in law", "daughter in law",
                    "sister in laws", "mother in laws")))
HE = (_HE_SAID | frozenset(word for word in _BUILT_KIN if _kin_pronoun(word) in _HE_SAID)
      | frozenset(("brother in law", "father in law", "son in law",
                   "brother in laws", "father in laws")))


def _sided(word):
    """The pronoun a word for a person names from inside it: "she", "he", or "" for neither.

    Read from the word rather than listed again: a goddaughter is a daughter and a nanna a nan, so
    the relation a longer word is built from decides it, where the words written out by hand above
    only ever knew the ones somebody had thought of. A word that names no gender of its own gets
    nothing, because these sets are also what a reply reads to say "her" or "him": a stepchild
    given both would be called "her" by a bot that should have said "them".
    """
    inside = _kin_pronoun(word)
    for gendered in sorted(_SHE_SAID | _HE_SAID, key=len, reverse=True):
        if inside.startswith(gendered) or inside.endswith(gendered):
            return "she" if gendered in _SHE_SAID else "he"
    return ""


# A person the store can file is a person a pronoun can point at. The two lists above were written
# by hand, so a word the store files and neither list holds could be told about and never referred
# to: "my auntie is a hairdresser" then "what does she do" found nobody and fell to a search hedge,
# where the same two lines about a sister were answered, and "my nanna is 71" then "how old is she"
# asked the search instead of saying 71. Every word whose own relation has a pronoun takes it now,
# so a relation added to the list of people is pointed at without a second list to remember.
_UNPOINTED = frozenset(word for word in KIN if word not in SHE and word not in HE)
SHE = SHE | frozenset(word for word in _UNPOINTED if _sided(word) == "she")
HE = HE | frozenset(word for word in _UNPOINTED if _sided(word) == "he")

# A limit on what a plan can be - "nothing too tiring", "no long walks", "my sister cant walk
# far", "we need to keep it cheap" - is a constraint, not a plan and not a feeling: the person is
# saying what to leave out. The plan reader below files "keep it cheap" as a plan (it came back as
# "You are going to Keep it cheap next weekend") and the correction reader takes "no long walks"
# as one, so the line is read here first and neither is kept from it.
A_LIMIT = re.compile(
    r"\b(?:nothing|no|not|never|nowt)\s+(?:too\s+|very\s+|much\s+|any\s+)?"
    r"(?P<move>tiring|strenuous|energetic|demanding|exhausting|exhaustive|walking|walk|walks|"
    r"long walks?|hikes?|hiking|hills?|stairs?|standing|climbing|lifting)\b"
    r"|\b(?:can'?t|cannot|can not|isn'?t able to|is not able to|not able to|only manage)\s+"
    r"(?:walk|climb|manage)\s+(?:far|long|much)\b"
    # "she cant do stairs" and "she cant get up the stairs" are the same limit as "she cant walk
    # far", said with the thing rather than with the walking. The verb is what stands between
    # "can't" and the limit, so it is the verb that is allowed to be there, not any word: "i cant
    # do this" and "i cant do monday" name no limit. Airing this here rather than in the abilities
    # reader means the plan and the mood both read it, and "i cant do stairs" on its own is a
    # remark about their knee, which the pools that answer a body already own.
    r"|\b(?:can'?t|cannot|can not|isn'?t able to|is not able to|not able to|only manage)\s+"
    r"(do|manage|get\s+up|get\s+up\s+and\s+down|get\s+up\s+the|use|cope\s+with)\s+"
    r"(?:the\s+|a\s+|any\s+)?(?:more\s+)?(?:stairs?|steps?|hills?|walks?|walking|"
    r"climbing|standing)\b"
    # "i cant stand long" is the standing, and "i cant stand much more of this" is a feeling:
    # the word after "stand" decides, so "much" is not allowed on its own.
    r"|\b(?:can'?t|cannot|can not|isn'?t able to|is not able to|not able to|only manage)\s+"
    r"(?:stand|sit)\s+(?:for\s+)?(?:long|far)\b"
    r"|\b(?:keep (?:it|the cost|costs) (?:cheap|low|small)|on a (?:tight )?budget)\b"
    r"|\b(?:nothing|no|not)\s+(?:too\s+)?(?:expensive|pricey|fancy)\b", re.I)
# A plan the person has committed to ("im going to", "we are booking"), as opposed to one they
# say they want or need: "im going to keep it cheap this month" is a month planned, while "we need
# to keep it cheap" is only the limit.
COMMITS_TO = re.compile(
    r"\b(?:going to|planning to|off to|about to|booking|booked|saving up|i(?:'?ve| have) booked)\b",
    re.I)
# What the limit is on, which is what decides what the reply does with it: the money, or the rest.
MONEY_LIMIT = re.compile(r"\b(?:cheap|budget|expensive|pricey|fancy|cost|costs|money|low)\b", re.I)


def _own_body_is_the_trouble(clean):
    """True when the line is the speaker's own body complaining, read by the pool that owns it.

    `bot/compose/badnews.py` already has the reading ("my knee hurts", "i have a bad back", and
    not "she has a bad chest"), so it is asked rather than a second list kept here. Imported
    inside the call because badnews is a composer module and the store is read before it exists.
    """
    try:
        from ..compose.badnews import reads_like_a_symptom
    except Exception:
        return False
    try:
        return bool(reads_like_a_symptom(clean))
    except Exception:
        return False


def a_limit_on_the_plan(text):
    """The limit a line puts on a plan - the feet, the money, or some other thing to avoid.

    "nothing too tiring", "no long walks", "my sister cant walk far", "we need to keep it
    cheap": the person is saying what to leave out of the plan, never how they are. The reading
    is here because the plan reader would otherwise file one as a plan, and the mood readers ask
    it too, so it has to be one reading both can ask. None when the line puts no limit on anything.
    """
    if not isinstance(text, str):
        return None
    clean = " ".join(text.lower().split())
    if not clean or "?" in clean:
        return None
    match = A_LIMIT.search(clean)
    if match is None:
        return None
    if _own_body_is_the_trouble(clean):
        # A limit whose reason is the person's own body is a symptom with a consequence, and the
        # answer they need is the one for the back or the knee: "my back is bad so no long walks"
        # came back as "Nothing I put to you needs hours on your feet", which tells them nothing
        # about the back they just mentioned. A body that is somebody else's is still a limit -
        # "my sister cant walk far" is what a carer is saying about the trip.
        return None
    hit = match.group(0)
    if match.group("move") or re.search(
            r"\b(?:walk|stand|sit|climb|climbing|manage|stairs?|steps?|hills?|walking|standing)\b",
            hit):
        # "my sister cant walk far" is a limit on the walking too, and "she cant do stairs" is
        # the same limit said with the thing rather than with the walking.
        return "move"
    return "money" if MONEY_LIMIT.search(hit) else "other"


# a plan or intention: the line says what the user is going to do
PLAN = re.compile(r"\b(?:(?:i(?:'m| am)|we(?:'re| are)|im|were)\s+(?:going to|planning|thinking of|off to|"
                  r"about to|hoping to|trying to|aiming to|aim to|meaning to|learning to|"
                  r"working on|writing|training|moving|"
                  r"buying|looking for|starting|organising|organizing|preparing|building|making|"
                  r"booking|saving|decorating|redecorating|painting|renovating|tiling|plastering|"
                  r"sorting|packing|cleaning|planting|digging|sewing|knitting|baking|cooking)(?: up| out| around| through)?|"
                  r"i want to|i need to|we want to|"
                  # "ive" is how a plan gets typed without the apostrophe, and it is a plan all
                  # the same: "ive got to paint the fence this weekend".
                  r"we need to|i(?:'?ve| have) got|i(?:'?ve| have) just got)\b", re.I)
PARTICLES = frozenset("""up out around through off""".split())
# A particle belongs to the verb, not to the plan: "i'm saving up for a bike" is saving, up, then
# for a bike. Without a place for it the line read as no plan at all and the person got the stock
# line back; PLAN takes it and the plan keeps it.
# The frames that are always followed by a verb rather than a place, so the word after them is
# the doing: "i'm aiming to get fit" is a plan about getting fit, and "get" opens it as a verb
# even though "get" is a place word in "i'm going to get the bus". Without this the aim was read
# as a destination and dropped, and the aim's own follow-up ("how long will it take") then had no
# subject but the deadline the aim named.
INFINITIVE_FRAME = re.compile(r"\b(?:trying|aiming|hoping|planning|meaning|learning|want|need)"
                              r"\s+to\s*$", re.I)
# The words people put in front of a plan verb: "i'm saving", "we are moving", "i want to save".
PERSON_OPEN = re.compile(r"^(?:i(?:'m| am)|we(?:'re| are)|im|were|i want to|i need to|we want to|"
                         r"we need to|i(?:'ve| have) got|i(?:'ve| have) just got)\s+", re.I)
# A plan whose rest opens with a preposition has lost its verb: "for a bike" says what the money
# is for, and reads back as "You're planning to for a bike". The verb is the plan there.
PREPOSITIONS = frozenset("for to in on at with about into by from".split())
# And an object that only points at something is no object at all: "saving up for it" and
# "saving up for the one i saw" name nothing to keep, and said back they tell the person nothing
# about their own week.
POINTING = frozenset("""it them that this these those one ones nobody nothing anything
something everything anyone someone none""".split())
ARTICLES = frozenset("""a an the my our your his her their""".split())
# "i've got" / "ive got" with no infinitive after it is what somebody owns or has, and only the
# date on it makes it something coming up.
# "ive got to go, speak later" is a goodbye: the infinitive carries no object and the clause after
# it ends the conversation, so nothing about it is coming up.
_FAREWELL = re.compile(r"\b(?:speak|talk|chat|text|see you|see ya|catch you|bye|goodbye|later|ttyl|"
                       r"gtg|cya|night)\b", re.I)
_GOT_A = re.compile(r"\b(?:i'?ve|ive|i have)\s+got\b(?!\s+to\b)", re.I)
_GOT_TO = re.compile(r"\b(?:i'?ve|ive|i have)\s+got\s+to\b", re.I)
# A date written the way people write dates: a day and a month next to each other, with or
# without the ordinal ("14 march", "3 june", "the 4th of may"). The two readers below both want
# it, and neither knew it: the plan reader took "on friday" and "in august" but not "on 3 june",
# so "my driving test is on 14 march" kept nothing at all, and the appointment reader wanted a
# clock, so "the scan is on 3 june" was a thing with no date on it.
MONTH_NAMES = (r"(?:january|february|march|april|may|june|july|august|september|october|november|"
               r"december)")
# Grouped, because it is dropped into two longer patterns: without the bracket the last way of
# writing a date would escape the word in front of it ("on" a date, "june 3" anywhere at all).
DAY_AND_MONTH = ("(?:" + r"\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?" + MONTH_NAMES +
                 r"|(?:the\s+)?\d{1,2}(?:st|nd|rd|th)\s+of\s+" + MONTH_NAMES +
                 r"|" + MONTH_NAMES + r"\s+\d{1,2}(?:st|nd|rd|th)?" + ")")
# A date ahead is what makes a line a plan, whatever words carry it: "i start my new job on
# monday", "my holiday is in august", "my daughter's party is next saturday". The event itself is
# open, so this reads any future-dated statement rather than a list of events.
FUTURE = re.compile(
    r"\b(?:tomorrow|tonight|this (?:weekend|week|evening|morning|afternoon|month|year|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday)|next (?:week|weekend|month|year|"
    r"summer|winter|spring|autumn|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"january|february|march|april|may|june|july|august|september|october|november|december)|"
    r"(?:(?:on|by|before|until) (?:the )?(?:monday|tuesday|wednesday|thursday|friday|saturday|"
    r"sunday|\d{1,2}(?:st|nd|rd|th))|"
    r"(?:is|are) (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"(?:is|are) (?:on |in )?the \d{1,2}(?:st|nd|rd|th))|"
    r"(?:on|by|before|until) (?:the )?" + DAY_AND_MONTH + r"|"
    r"(?:is|are) (?:on )?" + DAY_AND_MONTH + r"|"
    # A date after the verb that says what comes up is a date: "my course starts december 3",
    # "the term ends 12 july". Such a line has neither "is" nor "on", so the date was read and
    # the plan was not.
    r"(?:starts?|starting|begins?|beginning|ends?|ending|finishes|finishing|opens?|closes?|due|"
    r"scheduled|booked) (?:on )?" + DAY_AND_MONTH + r"|"
    r"in (?:january|february|march|april|may|june|july|august|september|october|november|december|"
    r"the (?:summer|winter|spring|autumn|morning|afternoon|evening))|"
    r"(?:the )?(?:week|month|summer) after|at the end of the (?:week|month|year)|"
    r"later (?:this|next) (?:week|month|year)|in (?:a|\d+|a few|two|three) (?:days?|weeks?|months?))\b",
    re.I)
# A clause about what already happened is not a plan.
PAST = re.compile(r"\b(?:was|were|went|had|did|didnt|didn't|last|yesterday|ago|already|used to|back in|"
                  r"just|never|kept|used)\b", re.I)
# A report of something already done is not a plan: "i saw my mum on sunday" and "my daughter
# started school in september" are news, not what is coming up. The verb right after the person
# is what says so: it ends in -ed ("started", "booked") or it is one of the irregular ones
# ("saw", "met", "went"). A word that ends in -ed but describes how someone is ("tired",
# "excited") is not a deed, and neither is a past verb whose object is an arrangement they have
# already made ("i agreed to help on saturday", "i booked a table for friday").
PAST_VERBS = frozenset("""saw met took made got went came said told gave found thought felt knew
left ran sat stood spent paid sent held won lost ate drank drove flew slept read wrote spoke broke
chose forgot began rang phoned watched visited played finished started cleaned painted fixed
argued fought moved booked texted emailed ordered carried""".split())
PAST_ARRANGED = frozenset("""agreed promised arranged booked planned sorted organised organized
reserved scheduled offered""".split())
PAST_STATES = frozenset("""tired bored excited worried wrecked shattered interested pleased scared
annoyed confused stressed exhausted married engaged retired aged blessed wicked naked sacred
beloved rugged hundred""".split())
# What turns an -ed verb into a wish or a decision about later rather than a report: "hoped to",
# "needed to", "decided we could".
INTENTION_AFTER = frozenset(("to", "i", "we", "you", "he", "she", "they", "that"))
# The person, then their verb: "i saw", "we started", "my daughter started".
PAST_DEED = re.compile(r"^(?:ok(?:ay)?[, ]+|and |so |but |also |well |oh )*"
                       r"(?:i|we|he|she|they|(?:my|our)\s+[a-z]+)\s+([a-z']+)(?:\s+([a-z']+))?\b",
                       re.I)


def a_deed(clause):
    """Whether the clause reports something the person has already done.

    Only the verb right after the person is read, so "im excited about my holiday next week"
    (the verb is "am") and "my daughter's party is next saturday" (the verb is "is") are still
    plans, and a past verb that names an arrangement made for later is not a report.
    """
    match = PAST_DEED.match(clause or "")
    if not match:
        return False
    word = match.group(1).lower()
    if word in PAST_ARRANGED:
        return False
    if word in PAST_VERBS:
        return True
    if word.endswith("ed") and len(word) >= 5 and word not in PAST_STATES:
        # An -ed verb that opens a clause of its own is an intention said in the past tense, not
        # something done: "i hoped to start my course in september", "i decided to go to rome in
        # may", "i hoped we could meet on monday" are all still ahead of them. The irregular past
        # forms are deeds whatever follows: "i went to see my mum on friday".
        return (match.group(2) or "").lower() not in INTENTION_AFTER
    return False


# The plan has to be the person's own business, in their own voice.
OWN = re.compile(r"^(?:ok(?:ay)?[, ]+|and |so |but |also |well |oh )*"
                 r"(?:i|i'm|im|i've|we|we're|were|we've|weve|my|our|me)\b", re.I)
# A plan is the person's own week, not something they say to the bot: "i'll call you tomorrow".
SECOND_PERSON = re.compile(r"\b(?:you|your|you're|u|ur|yours)\b", re.I)
# A line that says what is not happening, or how today feels, is not a plan.
NEGATED = re.compile(r"\b(?:cant|can't|cannot|dont|don't|doesnt|doesn't|wont|won't|not|never|no)\b", re.I)
# Words that say the next word is a thing, not a verb: "going to the gym" is not "going to visit".
DETERMINERS = frozenset("""a an the my our his her their your some any this that these those
one two three""".split())
# The words before a plan verb that make the line a question about the plan, not a plan.
ASKED_BEFORE = re.compile(r"\b(?:what|when|where|which|remind me|tell me)\b", re.I)
# A question is about the plan, not a plan.
# People leave the apostrophe out of the question word as often as not, and "whats my plan for
# saturday" was read as a plan of its own: kept as "whats my plan on Saturday" and said back as
# "You're planning to whats my plan on Saturday." One optional tail on the wh-word is enough for
# every shape of it they type ("whats", "what's", "hows", "wheres", "whens", "whos") and the word
# boundary after it keeps a longer word ("whatsoever") out.
ASKING = re.compile(r"\b(?:what|when|where|which|who|why|how)(?:'s|s|'re|re)?\b|"
                    r"\b(?:should|shall|can|could|would|do|does|did|is|are|was|will|any)\b", re.I)
# A correction names the value that was wrong, and the old one too when it is handy: "sorry, I
# meant Florence, not Rome", "no I mean Bristol", "sorry, Bristol not Leeds", "no, Bristol".
# "mean" and "meant" are the same move, and people drop the "I" as often as not.
# "make that" is the same move only when it is the move the line makes: at the front, after at
# most a word or two that opens a correction ("ok", "actually", "sorry", "no"). In the middle of
# a sentence it is ordinary English - "we make that recipe a lot", "i make that mistake" - and
# reading it as a correction put "Recipe a lot in june" in the plan and dropped the trip.
# A correction usually comes with the reason it changed: "sorry, i meant 900 because the boiler
# went", "no, bristol, since i moved for work". The reason names no value, so it is said around
# the value like the apology words are; left on it, the value read as "900 because the boiler
# went", which is not a value any reader here takes, so the 1500 stayed on record.
CORRECTION_WHY = r"\s*,?\s*(?:because|cos|coz|cuz|'cause|since)\b[^.!?]*"
CORRECTION = re.compile(
    r"(?:\b(?:sorry,?\s*)?(?:no,?\s+)?(?:i\s+meant|i\s+mean)"
    r"|^(?:\s*(?:ok|okay|actually|sorry|no|oh)[, ]+)*make\s+that)\s+(?:it'?s\s+|its\s+)?"
    r"([£$\u20ac]?\s?[a-z0-9][a-z0-9 '£$\u20ac-]{0,30}?)"
    r"(?:,?\s+not\s+([a-z0-9][a-z0-9 '-]{0,30}?))?"
    r"(?:\s+instead|[,.]|$|(?=" + CORRECTION_WHY + r"))",
    re.I)
# "sorry, Bristol not Leeds": the two values side by side, with no verb to say which is which.
# Either value can be two words ("tree nuts", "hard boiled"), and people put "it's" in front of
# the pair: "sorry, it's tree nuts not peanuts" is one correction, not a statement. A date or a
# count arrives this way as often as a name does ("sorry, the 12th not the 5th"), so a digit is a
# value too and the "the" in front of it is part of the way it is said.
# "rather than" and "instead of" take a value back in the same shape, and people say them
# without a subject: "im an accountant" / "actually an engineer rather than an accountant" was
# left with the accountant, because the pair reader knew only "not" as the word between the two
# values.
TAKES_BACK_THE_VALUE = r"(?:not|rather\s+than|instead\s+of)"
# The pair is often said with a verb in front of it: "actually weve got 900 not 1500, the boiler
# just went" is the same correction as "actually 900 not 1500", and read without it the line named
# no value at all, so the 1500 stayed on record. Only the words that carry the fact - what a
# person has, or has got - are allowed between, so the marker is still what marks the correction.
CORRECTION_PAIR = re.compile(
    r"\b(?:sorry|no|actually|oops)[, ]+"
    r"(?:(?:it'?s|its|it\s+is|that'?s|thats|that\s+is)\s+)?"
    r"(?:(?:i|we|you|they|he|she)\s*(?:'ve|ve|have|had)\s*(?:got\s+|get\s+|now\s+)?)?"
    r"((?:the\s+)?[a-z0-9][a-z0-9'-]{1,20}(?: [a-z0-9][a-z0-9'-]{1,15})?),?\s+"
    + TAKES_BACK_THE_VALUE + r"\s+"
    r"((?:the\s+)?[a-z0-9][a-z0-9'-]{1,20}(?: [a-z0-9][a-z0-9'-]{1,15})?)"
    r"(?:\s+instead\b|\s*[-,.;!?]|$)", re.I)
# "make that 4", "make it the 15th", "change it to friday": the value goes back up for a second
# go with no verb that names what is being corrected. The line has to start with it (or with the
# "no"/"sorry" that marks a correction), so "i make it 4" - an estimate - is not a correction.
CORRECTION_MAKE = re.compile(
    r"^\s*(?:(?:no|nope|sorry|actually|oops|ok|okay)[,.]?\s+)?"
    r"(?:make\s+(?:that|it)|change\s+(?:that|it)\s+to|switch\s+(?:that|it)\s+to)\s+"
    r"((?:the\s+)?[a-z0-9][a-z0-9 '£$\u20ac-]{0,25}?)"
    r"(?:,?\s+(?:please|then|instead|actually|now))?\s*[.!?]?\s*$", re.I)
# "no, I said 700": the person says the value again with "I said" in front of it. It is the same
# move as "I meant", in the words people reach for when the first go was simply wrong, and the
# "no"/"sorry" in front is what marks it as a correction rather than something they said once.
CORRECTION_SAID = re.compile(
    r"\b(?:no|nope|sorry|actually|oops)[,.]?\s+(?:i\s+said|i\s+did\s+say|i\s+actually\s+said|"
    r"i\s+meant\s+to\s+say)\s+(?:it'?s\s+|its\s+)?([a-z0-9][a-z0-9 '-]{0,30}?)"
    r"(?:,?\s+not\s+([a-z][a-z '-]{1,30}?))?(?:\s+instead|[,.]|$)", re.I)
# A time that has been moved is the same correction in the words people use for it: "i got it
# moved to thursday" after "my interview is on tuesday" is Tuesday being taken back, and the
# store has the plan to put Thursday in. The thing that moved is one they have already told us
# about, so the shape needs a pointing object ("got it moved", "changed it to") or a passive
# with the thing as its subject ("it's been moved") - without one, "we moved to preston" is a
# new address and not a correction of anything.
MOVED_VERB = (r"(?:moved|changed|pushed|shifted|switched|bumped|rescheduled|rearranged|"
              r"brought|put|shoved|dragged)")
MOVED_TO = r"\s*(?:back|forward|ahead|earlier|later|round|on)?\s*(?:to|until|till|for)\s+"
CORRECTION_MOVED = re.compile(
    r"(?:"
    # "i got it moved to thursday", "they've had the appointment changed to friday": the thing
    # that moved comes before the verb, because it is the one they already told us about.
    r"\b(?:got|had|get|have|has)\s+(?:it|that|this|them|the\s+[a-z]+)\s+" + MOVED_VERB + MOVED_TO +
    r"|"
    # "it's been moved to thursday", "its moved to the 4th": the thing that moved is the subject
    # of a passive, so the line points back with "it" and nothing else. A bare "they"/"she's" is
    # not a pointing back: "i live in bristol / she's moved to manchester" is news about her, and
    # reading it as a correction of where the person lives moved a fact they never changed.
    r"\b(?:it'?s|its|it\s+is|it\s+was|it\s+has|they'?ve|they\s+have|"
    r"has\s+been|have\s+been|had\s+been|been)\s+" + MOVED_VERB +
    r"(?:\s+(?:it|that|this|them))?" + MOVED_TO +
    r"|"
    # "they moved it to thursday", "she moved it to saturday", "the hospital moved it to the
    # 10th": someone else did the moving, and the thing they moved is named as "it".
    r"\b(?:they|he|she|we|i|the\s+[a-z]+)\s+" + MOVED_VERB +
    r"\s+(?:it|that|this|them)" + MOVED_TO +
    # "its now on thursday", "the scan is now on the 4th": the new time said as where the thing
    # sits, which is how a moved appointment is usually put.
    r"|\b(?:it'?s|its|it\s+is)\s+now\s+(?:on|for)\s+"
    r")"
    r"((?:the\s+)?[a-z0-9][a-z0-9 ':-]{0,25}?)"
    # A time that was moved is rarely said on its own: the reason follows it in the same breath
    # ("we moved it to sunday because of the football", "they pushed it to friday as we're
    # away"). The value is the time before that clause, or the line reads as no correction at
    # all and the move is answered as if it were news.
    r"(?:\s+(?:because|cos|cause|coz|due|since|so|as|seeing|what\s+with)\b"
    r"|\s+instead|[,.;!?]|$)", re.I)


# A clock time, as a plan says it: "2pm", "8.30", "20:30", "7 o'clock", "noon". A plan can
# have its clock put right the way it has its day put right - "the meeting is at 10am" then
# "make it 2pm" - and the two were not read the same way. A figure inside a plan was replaced by
# word boundary (`\b10\b`), which does not find the 10 in "10am", so the store answered "Meeting
# at 10am - got it" over a plan it had not changed; and "sorry, its at 8pm" was not read as a
# correction at all. The clock is read on its own so both have somewhere to go.
CLOCK_SAID = (r"(?:\d{1,2}(?:[:.][0-5]\d)?\s*(?:am|pm|a\.m\.|p\.m\.)"
              r"|(?:[01]?\d|2[0-3]):[0-5]\d"
              r"|\d{1,2}\s*o'?\s*clock"
              r"|noon|midday|midnight)")
# The value a correction says on its own ("2pm", "at 8pm").
CLOCK_VALUE = re.compile(r"^(?:the\s+|at\s+)?(" + CLOCK_SAID + r")$", re.I)
# The clock a plan already says. A plan's own clock is often written without am or pm ("dinner at
# 8"), and that hour is still the one a correction names, so the word in front of the figure is
# what makes it a clock here.
CLOCK_IN_PLAN = re.compile(
    r"(?<![\d.:])(?:" + CLOCK_SAID + r")"
    r"|(?<=\bat )\d{1,2}(?![\d:.,a-z%])", re.I)


def a_clock_time(phrase):
    """The clock time a phrase is, said the way the person said it ("2pm", "noon"), or "".

    Only a time nothing else can read as counts. A bare figure is not a clock ("make it 8" has
    no am or pm on it and may be any number a plan holds), and neither is a price: "8.30" is a
    minute on the clock only when an hour and a whole minute are written against each other and
    am or pm says which half of the day it is in.
    """
    match = CLOCK_VALUE.match(" ".join(str(phrase or "").split()))
    return match.group(1) if match else ""


def the_clock_in(text):
    """The clock a plan says, as the match to replace, or None."""
    return CLOCK_IN_PLAN.search(str(text or ""))


def a_moved_time(phrase):
    """True when a phrase is a time a plan can be moved to: a day, a month, a date or a clock.

    A thing can be moved to something that is not a time - "they changed it to a cheaper
    tariff", "its now on the table" - and that is a fact about the thing, not a time taken back.
    Only the three shapes a time is said in make the line a correction of a plan.
    """
    words = [word for word in re.split(r"[^a-z0-9]+", str(phrase or "").lower()) if word]
    if not words:
        return False
    if any(word in MONTHS or word in DAYS for word in words):
        return True
    if a_clock_time(phrase):
        return True  # "they moved it to 2pm" moves the clock of the plan, not its day
    # "the 10th", "the 12th of june", "12 june": a date is a number the month or the ordinal
    # makes one, so a bare number is only a date when nothing else in it is a word.
    return bool(DATE_VALUE.fullmatch(str(phrase or "").strip())) or bool(
        re.fullmatch(r"(?:the\s+)?\d{1,2}(?:st|nd|rd|th)?", str(phrase or "").strip(), re.I))


def _a_day_taken_back(text):
    """The day the line puts right, as a correction: "sorry saturday i got the day wrong".

    The value is the day, which is what the shapes for a moved time carry, so the store puts a
    plan's day to it rather than filing a plan of its own.
    """
    return A_DAY_TAKEN_BACK.search(text) or A_DAY_I_MEANT.search(text)


def _a_moved_time(text):
    """The moved-time correction in the line, when what it moves to is a time.

    The shape says something was moved; only the value says it was moved to a time, and that is
    what makes the line a correction of a plan. `a_moved_time` is the value's side of it.
    """
    for moved in CORRECTION_MOVED.finditer(text):
        if a_moved_time(moved.group(1)):
            return moved
    return None


# "no, 4 times not 3 times": the same side-by-side shape with a number and its unit on each
# side. The numbers carry the meaning, so the words after them are optional.
CORRECTION_NUMBER_PAIR = re.compile(
    r"\b(?:sorry|no|actually|oops)[, ]+(\d+(?:\.\d+)?(?:\s+[a-z]+)?)\s+"
    + TAKES_BACK_THE_VALUE + r"\s+"
    r"(\d+(?:\.\d+)?(?:\s+[a-z]+)?)(?:\s+instead|[,.]|$)", re.I)
# A date as a moved plan names it: a month or a weekday on its own, "the 4th", "the 4th of june",
# "12 june". One fragment so every shape that carries a moved date accepts the same dates.
A_DATE_VALUE = (r"((?:the\s+)?\d{1,2}(?:st|nd|rd|th)?(?:\s+of\s+(?:the\s+)?[a-z]{3,10})?"
                r"|(?:the\s+)?\d{1,2}(?:st|nd|rd|th)?\s+[a-z]{3,10}"
                r"|the\s+[a-z]{3,10}"
                r"|[a-z]{3,10})")
# The words a person puts after the value they are putting right: "sorry, the 5th actually",
# "no, june then", "make it july, i think". The marker in front is what says the line is a
# correction, and people say a second one after the value as often as before it. It stopped the
# value being read at all, so the correction turn moved nothing and the ask after it gave the old
# date back ("my sons birthday is on 4 june" / "its the 5th actually" still said 4 June), and
# `a_date_put_right` said yes while `the_date_put_right` found no date in the line.
AFTER_THE_VALUE = (r"(?:\s+(?:actually|instead|then|though|sorry|please|i\s+think|"
                   r"i\s+reckon|if\s+thats\s+ok|if\s+that'?s\s+ok))*\s*[.!]?\s*$")
# "we moved it to july": the date of a plan is moved, and the plan itself is pointed at ("it",
# "the booking", "our trip") rather than named. People say the new date and leave the old one
# out, because the plan already holds it.
CHANGED_TO = re.compile(
    r"\b(?:we|i|they)(?:\s*'?ve|\s+have|\s+had)?\s+"
    r"(?:moved|changed|pushed|shifted|switched|brought|put|bumped|made)\s+"
    r"(?:it|that|this|the\s+[a-z]{2,15}|our\s+[a-z]{2,15}|my\s+[a-z]{2,15})\s+"
    r"(?:back\s+|forward\s+|on\s+)?(?:to|until|for)\s+"
    + A_DATE_VALUE + AFTER_THE_VALUE, re.I)
# The same move said with no subject: "make it july", "change it to august". A question is not
# a change ("can we move it to july?"), so the reader refuses a line with a question mark.
CHANGED_BARE = re.compile(
    r"^\s*(?:(?:ok|okay|right|well|so|and|actually|no|sorry|oh)[, ]+)?"
    r"(?:make|change|move|push|put|shift|bring)\s+"
    r"it\s+(?:to\s+)?" + A_DATE_VALUE + AFTER_THE_VALUE, re.I)
# A change of date said with no verb at all: "its actually july", "its july instead". The
# "actually" or the "instead" is what makes it a correction rather than a fact about the world,
# so "its july" on its own states something else and is left alone. A bare "now" is not enough:
# "its monday now" is someone remarking on the day they are having, and reading it as "move the
# exam to Monday" put an exam a week earlier than the person had said it.
CHANGED_NOW = re.compile(
    # "its actually july", "its actually on saturday": the "actually" is the marker.
    r"^\s*(?:it'?s|its|that'?s|thats)\s+(?:actually|really)\s+"
    r"(?:(?:on|in|at)\s+)?([a-z]{3,10})(?:\s+now)?\s*[.!?]?\s*$"
    # "its saturday instead", "its on saturday instead".
    r"|^\s*(?:it'?s|its|that'?s|thats)\s+(?:(?:on|in|at)\s+)?([a-z]{3,10})\s+instead"
    r"(?:\s+now)?\s*[.!?]?\s*$"
    # The correction word in front is the marker, and a day is said with its "on" as often as
    # without: "no, its on thursday" after "the dentist is on tuesday" is the same correction as
    # "no, thursday", and neither read the day before. The "it's" is optional here for the same
    # reason: "sorry, on saturday" is what people say when the thing is already in the air.
    r"|^\s*(?:(?:ok|okay)[,.]?\s+)?"
    r"(?:(?:no|nope|sorry|wait|ah|oh|oops|hold\s+on|hold\s+up|hang\s+on|hmm|um+|erm+|well)"
    r"[,.]?\s+){1,3}"
    r"(?:(?:it'?s|its|that'?s|thats)\s+)?(?:actually\s+|really\s+)?"
    r"(?:(?:on|in|at)\s+)?([a-z]{3,10})(?:\s+now)?\s*[.!?]?\s*$", re.I)


# A date put right with no subject of its own: "sorry, it's the 4th", "no, the 4th of june",
# "actually the 4th instead". The marker in front is what makes it a correction rather than a
# date about something else, and the value has to be a date, so "no its fine" and "sorry, the
# dog" put nothing right. People say it this way when the date they gave was simply wrong.
CORRECTION_A_DATE = re.compile(
    r"^\W*(?:(?:ok|okay|right|so|and|no|nope|sorry|actually|oops|wait|oh|hmm)[,.]?\s+)+"
    r"(?:(?:it'?s|its|it\s+is|that'?s|thats|the\s+date\s+is)\s+)?"
    r"(?:(?:now|on|for)\s+)?"
    + A_DATE_VALUE + AFTER_THE_VALUE, re.I)
# A day put right in the words people use when they got the day wrong. `CORRECTION_A_DATE` wants
# the line to be nothing but the date, and these two shapes are not: the day comes with the reason
# after it ("sorry saturday i got the day wrong") or with "now" after it ("actually its sunday
# now because of the football"). Left unread, the day they took back is the day that answers:
# "when is it again" said "On Friday" over a dinner they had just moved to Sunday.
#
# The day has to be the thing the line puts up, so a day that starts a clause of its own is not a
# correction - "no saturday is the football", "actually sunday was lovely" are about the day and
# not a new answer for the plan. The reason after the day is what makes the first shape one at
# all: "sorry saturday" on its own is an apology about a day, not a date put right.
A_DAY_TAKEN_BACK = re.compile(
    r"^\W*(?:(?:ok|okay|right|so|and|no|nope|sorry|actually|oops|wait|oh|hmm)[,.]?\s+)+"
    r"(?:(?:it'?s|its|it\s+is|make\s+it)\s+)?"
    r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
    r"(?!\s+(?:is|was|are|were|and|or|but)\b)"
    r"(?:\s+(?:now|instead)\b"
    r"|[,.]?\s*(?:i\s+(?:got|had|put)\s+(?:the|that)\s+day\s+wrong|wrong\s+day|"
    r"my\s+mistake|i\s+was\s+wrong|im\s+wrong|silly\s+me|\s+i\s+meant\b))", re.I)

# The day said with the words people use when they got it wrong in front of it: "sorry i meant
# friday", "no i mean sunday", "i said thursday". The shapes above put the reason after the day
# ("sorry saturday i got the day wrong") or the word "instead"; the way most people correct a day
# is to say "i meant" and then the day, and that line was read as nothing at all:
#
#     i got the job and i start thursday / sorry, i meant friday
#       before  On Thursday.   (the day they had just taken back)
#       after   On Friday.
#
# The marker in front is still needed, so "i meant it" and a line that means something else about a
# day ("i meant to ring on monday") are not a date put right.
A_DAY_I_MEANT = re.compile(
    r"^\W*(?:(?:ok|okay|right|so|and|no|nope|sorry|actually|oops|wait|oh|hmm)[,.]?\s+)+"
    r"i\s+(?:meant|mean|said|was\s+thinking)\s+"
    r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
    r"(?!\s+(?:is|was|are|were)\b)", re.I)

# The same date said only as the thing that replaces the old one: "its the 4th instead". With no
# marker in front, the "instead" is the whole of what makes it a correction, so it is required.
A_TIME_INSTEAD = re.compile(
    r"^\W*(?:it'?s|its|that'?s|thats)\s+"
    + A_DATE_VALUE +
    r"\s+instead\b" + AFTER_THE_VALUE, re.I)
# The date moved by saying what the thing does now: "actually it starts tuesday", "the move
# slipped to september", "it got pushed back to the 4th". Only the verbs a date moves with are
# read, and the value still has to be a date: "it went to london" moves nothing, and "it is red"
# is not a change of anything.
MOVED_BY_ITS_OWN_VERB = re.compile(
    r"\b(?:it|that|this|the\s+[a-z]{2,15}|our\s+[a-z]{2,15}|my\s+[a-z]{2,15})\s+"
    r"(?:(?:has|have|had|got|was|is|been)\s+)?"
    r"(?:starts?|started|slips?|slipped|moves?|moved|pushes?|pushed|changes?|changed|"
    r"shifts?|shifted|lands?|landed|happens?|puts?)\s+"
    r"(?:back\s+|forward\s+|on\s+|to\s+|until\s+|for\s+)?"
    + A_DATE_VALUE +
    r"(?:\s+instead)?\s*[.!]?\s*$", re.I)
# The trip they already told us about, said again with a new date and none of the "moved" words:
# "actually we fly in september", "no we're going in august now", "sorry we go in june". The
# going verb is what makes this a trip and not a date on its own, and a marker in front is what
# makes it a change: "we fly in september" says a trip, not that an earlier one moved. A date at
# the end is still only read when it is one, so "actually we fly in a bit" moves nothing.
TRIP_DATE_MOVED = re.compile(
    r"^\W*(?:(?:ok|okay|right|well|so|and)[,.]?\s+)?"
    r"(?:(?:no|nope|sorry|actually|oops|wait|ah|oh|hmm)[,.]?\s+){1,3}"
    # "we're" typed as "were", "i'm" as "im": chat-speak drops the apostrophe, and the
    # subject still has to be there or "no flying in september" is a plan, not a move.
    r"(?:(?:we|were|i|im|they|theyre|he|hes|she|shes)\s*(?:'re|'ve|'ll|'m|'s|\s+are|"
    r"\s+have|\s+had|\s+will)?\s+)?"
    r"(?:fly|flies|flying|go|goes|going|leave|leaves|leaving|head|heading|"
    r"travel|travelling|traveling|drive|driving|sail|sailing|arrive|arriving)\b"
    r"[^.!?]{0,40}?"
    r"\b(?:in|on|for)\s+"
    + A_DATE_VALUE +
    r"(?:\s+(?:now|instead))?\s*[.!]?\s*$", re.I)


# "sorry, not peanuts": the value taken back with nothing put in its place. The "no"/"sorry" in
# front is what makes it a correction rather than part of the fact, so "i'm not allergic to
# peanuts" states something else and is left alone.
# "no, not today", "sorry, not now", "not again": a refusal of the moment, not a value that goes.
NOT_A_DAY = frozenset("""today tonight tomorrow now anymore yet again either neither even sure
really quite very much bad good great one""".split())
CORRECTION_NOT = re.compile(
    r"\b(?:sorry|no|nope|actually|oops)[, ]+not\s+(?:the\s+)?([a-z][a-z'-]{1,20}"
    r"(?: [a-z][a-z'-]{1,15})?)(?:\s+instead\b|\s*[-,.;!?]|$)", re.I)
# "take that back", "scratch that", "strike it out": the last thing they said goes and no value is
# named, so the store is the only place that can undo it. Only phrases that can mean nothing else
# are here: "forget that" and "never mind" also change the subject, and the understanding lane
# reads those, so a retraction must not take those turns.
RETRACT = re.compile(
    r"^\W*(?:(?:ok|okay|no|nope|sorry|actually|wait|oh|hmm|um|yeah)[,.]?\s+)*"
    r"(?:take|taking)\s+(?:that|it|this)\s+back\b(?:\s+(?:then|please|sorry|yeah))?\W*$"
    r"|^\W*(?:(?:ok|okay|no|nope|sorry|actually|wait|oh|hmm|um|yeah)[,.]?\s+)*"
    r"(?:scratch|strike|disregard|ignore|undo|delete)\s+(?:that|it|this)\b"
    r"(?:\s+(?:out|then|please|yeah))?\W*$"
    r"|^\W*(?:(?:ok|okay|no|nope|sorry|actually|wait|oh|hmm|um|yeah)[,.]?\s+)*"
    r"forget\s+(?:what\s+)?i\s+(?:just\s+)?(?:said|told you)\b\W*$", re.I)
# "not lisbon, porto", "not lisbon - porto instead": the value they want is said after the one they
# are taking back. The line is a correction, not a bare take-back: the old value is replaced, so the
# plan (or the place) keeps everything else it said and only that word moves.
CORRECTION_NOT_TO = re.compile(
    r"\b(?:sorry|no|nope|actually|oops)[, ]+not\s+(?:the\s+)?"
    r"([a-z][a-z'-]{1,20}(?: [a-z][a-z'-]{1,15})?)\s*(?:,|;|-|\u2013|\u2014|\bto\b)\s*"
    r"(?:(?:it'?s|its|that'?s)\s+)?"
    r"([a-z][a-z'-]{1,20}(?: [a-z][a-z'-]{1,15})?)(?:\s+instead)?\s*[.!?]?$", re.I)


# "no, not Friday, Monday": the value taken back, and the right one after it. People say a
# correction in this order as often as the other way round ("Monday, not Friday"), and reading
# only the first value is worse than reading neither: "sorry, not peanuts, tree nuts" took the
# peanut allergy off the list and filed nothing, so an allergic person was left with no allergy
# on record. The comma is what tells the pair from a two-word value ("not tree nuts"), and the
# right value is kept as `to` because that is the value the store goes with from now on.
CORRECTION_NOT_PAIR = re.compile(
    r"\b(?:sorry|no|nope|actually|oops)[, ]+not\s+(?:the\s+)?([a-z0-9][a-z0-9'-]{1,20}"
    r"(?: [a-z0-9][a-z0-9'-]{1,15})?)\s*,\s*(?:its\s+|it's\s+|the\s+)?"
    r"([a-z0-9][a-z0-9'-]{1,20}(?: [a-z0-9][a-z0-9'-]{1,15})?)(?:\s+instead\b|\s*[.;!?]|$)",
    re.I)
# "no he isn't Dave" and "no he isn't, it's Dan": a line that denies a name says the pronoun
# first and the value after it, which is the opposite of the pair above, and the pronoun was read
# as the value - "no hes not dave" filed "Hes" as the son's name, answered "Hes, got it." and
# then "Your son is called Hes." A denial on its own takes a name away and puts nothing in its
# place, so nothing here is kept; a denial with a name after the pronoun ("it's Dan", "she's
# called Dana", "hes dan") is the usual way people put a name right, and that name is kept.
DENIAL_OF_A_VALUE = re.compile(
    r"^\W*(?:(?:ok|okay|ah|oh|no|nope|sorry|actually|wait)\b[,.]?\s+){1,2}"
    r"(?P<whose>he|she|it|they)(?:'?s|s)?\s*"
    r"(?:isnt|is\s+not|not|wasnt|was\s+not)\b\W*"
    r"(?:(?:the\s+)?(?!(?:its|it'?s|hes|he'?s|shes|she'?s|theyre|they'?re|called|named)\b)"
    r"(?P<wrong>[a-z][a-z'-]{1,20})?\s*[,.;!?-]*\s*)?"
    r"(?:(?P<says>its|it'?s|hes|he'?s|shes|she'?s|theyre|they'?re"
    r"|(?:he|she|it|they)\s+(?:is|are)|called|named"
    r"|the\s+name\s+is|his\s+name\s+is|her\s+name\s+is|their\s+name\s+is)\b\s*"
    r"(?:called\s+|named\s+)?)?"
    r"(?P<value>[a-z][a-z'-]{1,20})?\s*[.!?]?$", re.I)
# The naming word after a denial belongs to the clause being denied, not to a new value: "no he
# isnt called max" says the dog is not called Max, and reading "called max" as a rename gave the
# dog the name the person had just ruled out ("Max - got it, I'll call the dog Max"). A rename
# said in the same breath names the old value too ("no he isnt max, hes called leo"), and that
# line does not reach this reader at all, so the naming word there still names.
A_NAME_IS_TAKEN_BACK = frozenset(("called", "named"))


def a_name_is_taken_back(text):
    """True when the line denies a name rather than giving one: "no hes not called max".

    The tense is the tell: "no hes not called max" is about the name it had, and "no hes called
    max" is the name it has now. Only the denying frame is read here, so the second line is left
    to the rename route that already reads it.
    """
    denial = DENIAL_OF_A_VALUE.match(str(text or "").strip())
    return bool(denial and denial.group("value")
                and (denial.group("says") or "").strip().lower() in A_NAME_IS_TAKEN_BACK
                and not denial.group("wrong"))


# The person taking back the name they gave the bot: "im not kay", "my names not kay", "thats
# not my name", "dont call me kay". None of these names anybody new, so the store kept the old
# name and went on using it - the next turn called them by the name they had just said was wrong
# - and the reply had nothing of its own at all ("I'm listening - say more if it helps", "Got it
# - that's not your name").
#
# Every shape here denies the name rather than giving one, and the word is read only against the
# name on record: "im not hungry" and "im not sure" are the commonest openings of any line, and
# a denial of the name cannot be about a word the person never gave. "dont call me kay" is the
# same denial said as an instruction, and it is why the naming word is listed on its own: the
# line is not a phone call to be refused.
# A name said in a denial is a whole name as often as one word: "im not kay smith" takes back
# the name the store holds, and reading only the first word left the line with nothing at all.
_A_SAID_NAME = r"[a-z][a-z'\-]{1,19}(?:\s+[a-z][a-z'\-]{1,19})?"
NAME_TAKEN_BACK = re.compile(
    r"^\W*(?:(?:no|nope|sorry|ah|oh|actually|wait|oi|hey)[,.!]?\s+){0,2}"
    r"(?:"
    r"i(?:'?m|\s+am)\s+not\s+(?P<said>" + _A_SAID_NAME + r")"
    r"|my\s+name(?:'?s|\s+is)?\s*(?:is|was)?\s*not\s+(?P<said2>" + _A_SAID_NAME + r")"
    r"|my\s+name(?:'?s)?\s*(?:isn'?t|ain'?t|aint)\s+(?P<said3>" + _A_SAID_NAME + r")"
    r"|(?:that|this)(?:'?s|\s+is|\s+was)\s+not\s+my\s+name"
    r"|my\s+name(?:'?s)?\s+(?:is\s+)?wrong"
    r"|you(?:'?ve|\s+have)?\s+got\s+my\s+name\s+wrong"
    r"|(?:please\s+)?(?:don'?t|do\s+not|stop)\s+(?:call|calling)\s+me\s+"
    r"(?P<said4>" + _A_SAID_NAME + r")"
    r")\W*(?:[.!]|\?)?$", re.I)


def _the_same_name(left, right):
    """Whether a word names the same person as a name on record: "kay" is "Kay Smith"."""
    said = " ".join(str(left or "").lower().replace(".", " ").split())
    known = " ".join(str(right or "").lower().replace(".", " ").split())
    if not said or not known:
        return False
    return said == known or said in known.split() or known in said.split()


def the_name_they_take_back(text, stored=""):
    """The name on record a line takes back, "" when it denies the name without saying which,
    or None when the line does not take the name back at all.

    Read against the name the store holds, so the denial is never a guess: "im not kay" only
    denies a name when Kay is the one the bot was told, and every other use of the same words
    ("im not sure" being the commonest line in any chat) is left to the readers that know it.
    """
    known = str(stored or "").strip()
    if not known:
        return None
    said = " ".join(str(text or "").split())
    # The chat-speak hangs off the end of the denial as it does off every other line: "im not kay
    # lol" takes the name back exactly as "im not kay" does.
    from . import filler as _filler
    denial = NAME_TAKEN_BACK.match(_filler.without_filler(said))
    if not denial:
        return None
    named = ""
    for group in ("said", "said2", "said3", "said4"):
        named = named or (denial.group(group) or "").strip()
    if named and not _the_same_name(named, known):
        return None
    return known


# "no, Bristol": a bare value after a "no" that starts the line, once the line before it said a
# fact. Only a value on its own counts, so "no, i'm tired" is not a correction. A figure comes with
# what it is counted in ("sorry, 88 kilos"), because that is how a weight, a height or a price is
# said back, and the unit is what tells the weight from the age.
# People stack the words that announce a correction: "no sorry croatia", "oh no, bristol",
# "sorry no, soya", "no wait 600". One word was all this read, so "no sorry croatia" was not a
# correction and the value went into the store with the idiom still on the front of it. "ok" only
# opens a correction in front of one of those words: "ok wait 600" takes something back and
# "ok 600" is an answer, so it leads without carrying the value on its own.
# People also stall before they correct: "no wait, Leeds", "hold on, Porto", "sorry, hang on,
# June". The stall says nothing about the value, so it is an opener like the "no" it follows.
# A value can be two words: the thing people correct to is often not one ("tree nuts", "new
# york", "hard boiled"), and the clause guards below still refuse a phrase that is a sentence
# ("no, i'm tired" opens with "i'm").
CORRECTION_STALL = r"(?:hold\s+on|hold\s+up|hang\s+on)"
# A stock apology or an acknowledgement is not a value: "sorry, my mistake", "sorry, my bad",
# "sorry, thank you". A possessive opens a phrase that names something of the person's ("my
# mistake", "my bus") and not a new value for the fact the line before stated, and with the value
# widened to two words it was read as one ("sorry, my mistake" made the city "My").
NOT_A_VALUE_START = (r"(?!\s*(?:my|your|his|her|our|their|its|thank|thanks|cheers|please"
                     r"|and|but|so|not|nothing|never|no|ok|okay|right|yes|yeah|why|what|how)\b)")
# The hedges belong in the run too: "hmm sorry croatia", "well actually 800" and "um no bristol"
# announce a correction in the same breath as the words above, and a run of them is still one run.
CORRECTION_HEDGE = r"(?:hmm|um+|erm+|well)"
# "scratch that, 800" after "my budget is 500", "strike that, in august" after the trip: the words
# that take the last thing back, with the right value after them, are a correction and not a
# retraction. The retraction reader takes "scratch that" on its own - it is anchored to the end of
# the line - so the lined line "scratch that, 800" matched neither: the reply said "Got it -
# scratch that, 800." and the store still had 500, and the next ask said the old figure back.
CORRECTION_TAKEBACK = (r"(?:(?:scratch|strike|disregard)\s+(?:that|it|this)"
                       r"|(?:take|taking)\s+(?:that|it|this)\s+back"
                       r"|forget\s+(?:what\s+)?i\s+(?:just\s+)?said"
                       # Owing the mistake is as plain a way of taking the last thing back as
                       # "scratch that": "i got that wrong, its 4 may" and "im wrong, its 4 may"
                       # carry the corrected date exactly as "actually its 4 may" does, and with
                       # no opener here the whole line fell through to the greeting, which said
                       # it back - "Got it - you got that wrong, it's 4 may" - while the store
                       # kept the date that had just been taken back.
                       r"|i\s+got\s+(?:that|it|this)\s+wrong"
                       r"|i\s+had\s+(?:that|it|this)\s+wrong"
                       r"|i\s+(?:was|got\s+it)\s+wrong"
                       r"|i\s+made\s+a\s+mistake"
                       r"|i\'?m\s+wrong"
                       r"|my\s+mistake)")
CORRECTION_LEAD = (r"^\s*(?:(?:ok|okay)[,.]?\s+)?"
                   r"(?:(?:(?:no|nope|sorry|wait|ah|oh|actually|oops|"
                   + CORRECTION_STALL + r"|" + CORRECTION_HEDGE + r"|"
                   + CORRECTION_TAKEBACK + r")[,.]?\s+){1,3})")
# The correction word on the end of the line instead of in front of the value: "its the 4th
# actually", "my budget is 400 actually". People put the marker after the thing as often as before
# it, and every reader in the correction block anchors the value to the end of the line, so a
# marker there left the line with nothing taken back at all: after "the party is on 3 june", "its
# the 4th actually" was answered "It's the 4th, good to know" and the store still held the 3rd, so
# the next ask said their own correction was the date they had taken back. The word is the same
# word, so a line that ends with it is read as the line with it in front.
A_MARKER_ON_THE_END = re.compile(r"\s+(?:actually|really|honestly)\s*[.!?]*\s*$", re.I)


def _the_marker_in_front(text, question=False):
    """The line with a correction word moved from its end to its front, or None.

    "its the 4th actually" is "actually its the 4th". Only the word moves: what follows is read by
    the readers that already know the shape, so a date, a figure, a count and a name all come back
    the same way they do with the marker in front.

    The line left behind has to be a value and nothing else. "my mum is 70 actually" states the
    mother's age, and moving the word would file the 70 a second time as the correction of some
    other fact; "my son is jack actually" would correct the son's name to the name he was just
    given. So a head that says anything of its own is a statement with the word on the end, and a
    statement is not a correction.
    """
    said = str(text or "").strip()
    end = A_MARKER_ON_THE_END.search(said)
    if end is None:
        return None
    head = said[:end.start()].strip()
    if not head or len(head.split()) > 8:
        return None
    if _extract(head, question):
        return None
    return "actually " + head
# A bare value can carry the unit it is said in ("no wait, 8 kilos", "no, 5 minutes"): which
# fact it corrects is still decided by the line before, and memory_store refuses a unit the fact
# on the table is not measured in.
# A name put right says the pronoun before it ("no hes called max", "no she's called dana"),
# and without that frame the line read as three words and no value at all, so the correction was
# lost and the line went on to be answered as something else.
# The frame the corrected value usually wears - "it's 4 may", "that's on thursday" - is written
# without its apostrophe as often as with: "actually it is on 4 may" says the corrected day as
# plainly as "actually it's on 4 may", and with only the contractions listed the line was read as
# a statement and the store kept the date that had just been taken back. One frame, so the date,
# the clock and the bare value cannot drift apart.
CORRECTION_FRAME = (r"(?:(?:it'?s|its|it\s+is|it\s+was|that'?s|thats|that\s+is|that\s+was"
                    r"|he'?s|hes|she'?s|shes|they'?re|theyre|they\s+are)\s+)")
CORRECTION_BARE = re.compile(
    CORRECTION_LEAD
    + r"(?:" + CORRECTION_FRAME + r""
       r"|(?:his|her|its|their|the)\s+names?\s+(?:is\s+|not\s+|was\s+)?)?"
    + NOT_A_VALUE_START +
    r"(?!(?:oops|sorry|wait|hold|hang|hmm|um+|erm+|nope?|actually|oh|ah"
    r"|eh|well)\b)"
                             r"([a-z][a-z'-]{1,20}(?:[ ][a-z][a-z'-]{1,15})?"
                             r"|[\u00a3$\u20ac]?\s?\d[\d,]*(?:\.\d+)?"
                             r"(?:\s?(?:pounds?|quid|euros?|dollars?|k|kilos?|kgs?|kg"
                             r"|stones?|st|lbs?|lb|grams?|g|litres?|liters?|miles?|km"
                             r"|minutes?|mins?|hours?|days?|weeks?|months?|years?)\b)?)"
                             r"\s*[.!?]?$",
                             re.I)
# A figure on its way back is usually hedged: "actually just 6", "no, only 2", "sorry, about
# five". The hedge is neither a second correction word nor a value, so the readers above stop on
# it and the line is left as something said rather than something put right: a table for eight
# stayed eight after "actually just 6", and the readback then gave the person both numbers ("you
# are 8 for dinner on Saturday; you said actually just six"). Only a figure can follow the hedge.
# "no just checking" and "sorry about that" are the words people use to get off a subject, and
# they correct nothing to a word: the value after the hedge is read only as a number, with the
# unit it is said in, so the correction needs the figure the person actually changed.
CORRECTION_HEDGED = re.compile(
    CORRECTION_LEAD
    + r"(?:just|only|about|around|roughly|nearly|almost|exactly|more\s+like|closer\s+to)"
    r"\s+(?:(?:it'?s|its|that'?s|thats|the)\s+)?"
    + r"([\u00a3$\u20ac]?\s?\d[\d,]*(?:\.\d+)?"
      r"(?:\s?(?:pounds?|quid|euros?|dollars?|k|kilos?|kgs?|kg|stones?|st|lbs?|lb|grams?|g"
      r"|litres?|liters?|ml|miles?|km|minutes?|mins?|hours?|days?|weeks?|months?|years?"
      r"|people|guests?|adults?|kids?|of\s+us)\b)?"
      r"|" + "|".join(sorted(NUMBER_WORDS, key=len, reverse=True)) + r")"
    r"\s*(?:now\b)?\s*(?:[.!?,]|$)",
    re.I)
# A clock said again: "sorry, its at 8pm", "no wait, 8pm". The plan on the table holds the
# clock this replaces, so the line names only the new one. Only a time with am or pm (or a clock
# written as one) is read here, because a bare figure after "no" is a number and belongs to the
# reader that reads numbers. A clock often arrives with a word of preference on the end ("4.30pm
# is better", "8 works"), which says the time is the one they want and nothing else.
CLOCK_PREFERENCE = (r"(?:\s+(?:is|would\s+be|works|suits|sounds)\s*"
                    r"(?:(?:much|a\s+lot|way|far)\s+)?"
                    r"(?:better|best|fine|good|easier|ok|okay)?)?")
CORRECTION_CLOCK = re.compile(
    CORRECTION_LEAD + r"(?:" + CORRECTION_FRAME + r")?(?:at\s+|for\s+)?"
    r"(" + CLOCK_SAID + r")" + CLOCK_PREFERENCE + r"\s*(?:instead|now)?\s*[.!]?$", re.I)
# The same clock with no correction word in front of it, because the preference is the whole
# line: "4.30pm is better", "2pm works better", "9am suits". Nothing in the line says what it
# corrects, so the store asks it of the plan on the table and refuses it when that plan holds no
# clock: "morning is better" is not a time, and a clock with no plan is a remark about some other
# time, not a change to a turn of theirs. A line that goes on to compare two clocks ("4pm is
# better than 3pm") names no single value and is left alone.
CLOCK_PREFERRED = re.compile(
    r"^\s*(?:(?:and|but|or|so)\s+)?"
    r"(" + CLOCK_SAID + r")\s+"
    r"(?:(?:is|would\s+be|sounds|seems)\s+)?(?:(?:much|a\s+lot|way|far)\s+)?"
    r"(?:better|best|fine|good|easier|ok|okay|w(?:orks|ould\s+work)|suits?|sounds?)"
    r"(?:\s+(?:better|best|fine|good))?"
    r"\s*(?:instead|then|though|now)?\s*[.!]?$", re.I)
# A number corrected in its own line: "my budget is 500" then "actually make that 800". The
# value is the number, and what it corrects is decided by the line before ("$ 500" is a budget).
# The whole line has to be the correction. The verb alone is not enough: "put it 20 in the oven"
# is a step in a recipe, and reading the 20 as a new budget answered "put it in the oven at 200"
# over the number they had given. A period qualifier is the one thing allowed after the number
# ("make it 800 a month"), because it says what the same amount is measured over.
AMOUNT_CORRECTION = re.compile(
    r"^\W*(?:(?:sorry|actually|no|nope|ok|okay|wait|well|hmm|um)\b[,.]?\s*)*"
    r"(?:(?:make|makes|change|changed|put)\s+(?:it|that|them)\s+(?:to\s+)?"
    r"|more\s+like\s+(?:[£$\u20ac]\s?)?)"
    r"(\d[\d,. ]{0,12}?)"
    r"(?:\s*(?:a|per|each)\s+(?:day|week|month|year|person|head)\b|"
    r"\s+for\s+(?:the|a|an|our|my|this|that)\s+[\w' -]{1,20}|"
    r"\s*(?:pounds?|quid|euros?|dollars?|bucks)\b|"
    r"\s+(?:instead|now)\b)?\W*$", re.I)
# The same correction said without the verb: "my budget is 300" then "sorry, 400 a month". People
# correct a figure by saying the figure again with what it is measured over, and the line has to
# open with a correction word so a plain "i pay 400 a month" is a new statement, not a replacement.
# The period qualifier is required: "sorry, 400" on its own says too little to move anything, and
# the number this replaces is decided by the line before ("$ 300" is a budget).
AMOUNT_CORRECTION_BARE = re.compile(
    r"^\W*(?:(?:sorry|actually|no|nope|ok|okay|wait|well|hmm|um)\b[,.]?\s*)+"
    r"(?:(?:it'?s|that'?s)\s+)?(?:make\s+(?:it|that|them)\s+(?:to\s+)?)?"
    r"(\d[\d,. ]{0,12}?)\s*(?:a|per|each)\s+(?:day|week|month|year|person|head)\b\W*$",
    re.I)
# "i want to make it to 30 countries" is a wish about the future, not a correction of a number
# already given: the verb only changes a value when nothing in front of it is hoping.
AMOUNT_WISH = frozenset("""want wants wanted wanting hope hopes hoped hoping wish wishes
wishing try tries trying tried going gonna like love plan plans planning intend intends
aim aims aiming""".split())
# "no im 35" after "im 34" is a correction too: a marker in front of a plain statement of the
# same kind of fact means the statement's own value is the one to keep, and people say it that
# way when the first go was simply wrong - "no im 35", "actually im 35", "no i live in york" -
# with no "i meant" anywhere in the line. The word after the marker has to open a statement about
# the person, so "sorry to bother you" and "no the dog is called rex" stay ordinary lines, and
# the keys it may correct are the person's own values only: a pet, a relative or a diet never
# lands on the user by this route.
CORRECTION_MARK = re.compile(r"^\W*(?:no|nope|sorry|actually|oops)\b[,.]?\s+"
                             r"(?=(?:i|im|i'm|i've|ive|i'd|my|we|we're|we've|its|it's|i'll|"
                             r"it\s+is|that\s+is)\b)",
                             re.I)
CORRECT_FROM_MARK = ("age", "height", "city", "places", "name", "job", "budget")
# "no thanks", "no idea", "no worries" are answers, not values.
CORRECTION_BARE_NO = frozenset("""thanks thank idea ideas worries worry problem way chance
doubt rush need matter point wonder clue reason sorry luck harm""".split())


# The sentence shape each fact arrives in, so a corrected value can be read the way the fact it
# corrects was read: "no I mean 43" after "I'm 34" is an age, not a name.
CORRECTION_SHAPE = {"name": "my name is {}", "age": "i am {}", "budget": "my budget is {}",
                    "city": "i live in {}",
                    "places": "i live in {}", "job": "i work as a {}", "diet": "i am {}",
                    "allergies": "i am allergic to {}", "pets": "i have a {}"}


# A corrected value names a thing. It is not a clause: "no, i am not on shift" and "sorry, it's
# not far from york" are things people say, and the value in them is a sentence, not a value.
CLAUSE_OPENERS = frozenset("""i i'm im i've ive i'd id it it's its that that's thats this
we we're we've you you're he she they there here not no yes and but so don't dont doesn't didnt
can't cant won't wont isn't aren't was wasn't weren't is are am was were do does did have has had
could would should can will must might may be been being sorry thanks thank please just really
""".split())


# A value is a name, a place or a number, so it ends where a verb starts: "no i said bristol is
# fine" corrects the place, and "is fine" is a comment on it, not part of the name.
COPULA_SPLIT = re.compile(r"\s+(?:is|was|are|were|be|been|being|seems|seemed|looks|looked|"
                          r"now|then|actually|though|anyway)\b", re.I)


# Words that point at something instead of naming it. A correction has to name the value, and a
# line that names nothing - "no i said the other one", "i said nothing", "three of them" - is a
# complaint or a shrug, not a new fact. Reading one of those as the value would replace a fact the
# person did give with one that was never said, which is worse than not correcting at all.
NOT_A_VALUE = frozenset("""nothing anything something everything nobody none someone somebody
anybody everybody them they it him her us you me that this these those there here
anywhere somewhere nowhere everywhere whatever whoever whichever whenever wherever
other another else one ones same such what which who whom whose when where why how whether
he she his hes shes theyre he's she's they're thats im i'm ive i've weve we've
""".split())

# A phrase that ends by pointing back ("three of them", "any of those") names nothing either,
# however the words before it read.
POINTING_AT = frozenset("""them they it him her us you me that this these those""".split())

ARTICLES = frozenset("""a an the""".split())


# A date is a value however many little words it is said with: "the 12th", "the 13th of june",
# "june the 12th". The word count below is about clause-fragments, and a date is not one.
_MONTH_ALT = "|".join(sorted(MONTHS, key=len, reverse=True))
DATE_VALUE = re.compile(
    r"(?:the\s+)?\d{1,2}(?:st|nd|rd|th)(?:\s+of\s+(?:" + _MONTH_ALT + r"))?"
    r"|(?:the\s+)?\d{1,2}\s+(?:" + _MONTH_ALT + r")"
    r"|(?:" + _MONTH_ALT + r")\s+(?:the\s+)?\d{1,2}(?:st|nd|rd|th)?", re.I)

# A date said again is a value with more than one word in it, and the one-word reader above
# cannot carry it: "my birthday is 3rd may" then "sorry, its the 4th of may" left the month where
# it was, so the store answered with the day the person had just taken back. A day and a month, a
# month on its own or a day on its own is the value here; which fact it moves is the store's
# question, because a birthday and a trip are both kept with a date on them.
_DAY_NUMBER = r"(?:0?[1-9]|[12]\d|3[01])"
CORRECTION_DATE = re.compile(
    CORRECTION_LEAD + r"(?:" + CORRECTION_FRAME + r")?(?:on\s+|in\s+)?"
    r"(?P<date>(?:the\s+)?" + _DAY_NUMBER + r"(?:st|nd|rd|th)?"
    r"(?:\s+(?:of\s+)?(?:" + _MONTH_ALT + r"))?"
    r"|(?:" + _MONTH_ALT + r")(?:\s+(?:the\s+)?" + _DAY_NUMBER + r"(?:st|nd|rd|th)?)?)"
    r"\s*[.!?]?$", re.I)


# A date is moved on a plan by saying the going itself, and the going sits between the correcting
# word and the date: "im going to spain in june" then "actually we fly in july now". The words say
# which of the person's dates moved, the way "actually its cornwall we go to" says which place -
# and without them the line read as no correction at all, so the month in the plan stayed June and
# the line went on to be answered as something else ("we fly in july now" was answered about fruit
# flies). Only the going is allowed there, and only in the present: "actually we went in june" is a
# line about a trip already taken, not a plan being moved.
_GOING_VERB = (r"(?:fly|flies|flying|go|goes|going|travel|travels|travelling|traveling|head|heads"
               r"|heading|leave|leaves|leaving|visit|visits|visiting|get|gets|getting|are|is)")
_GOING_SAID = (r"(?:(?:we|i|they|he|she)(?:'?re|'?m|'?s)?\s+" + _GOING_VERB +
               r"|(?:the\s+|our\s+|their\s+)?(?:flight|trip|holiday|booking|wedding|party"
               r"|appointment|visit)\s+(?:is|are|'s))")
_GOING_DATE = (r"(?:the\s+)?(?:0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?"
               r"(?:\s+(?:of\s+)?(?:" + _MONTH_ALT + r"))?"
               r"|(?:" + _MONTH_ALT + r")(?:\s+(?:the\s+)?" + r"(?:0?[1-9]|[12]\d|3[01])"
               r"(?:st|nd|rd|th)?)?")
CORRECTION_DATE_GOING = re.compile(
    CORRECTION_LEAD + _GOING_SAID + r"\s+(?:out\s+)?(?:on\s+|in\s+)?(?P<date>" + _GOING_DATE
    + r")", re.I)
# The same move said with the marker behind it instead of in front: "we fly out in august now",
# "we travel in december instead". The word at the end is what makes it a change rather than a
# statement ("we fly in june every year" is not read here), and the plan it moves is the store's
# question, so the reader only says which date the line names.
CORRECTION_GOING_MOVED = re.compile(
    r"^\s*" + _GOING_SAID + r"\s+(?:out\s+)?(?:on\s+|in\s+)?(?P<date>" + _GOING_DATE + r")"
    r"\s+(?:now|instead|this\s+time|from\s+now\s+on)\b", re.I)


# A correction is rarely the value and nothing else: people put a word of apology or a shrug after
# it, or say the value and then which one it replaces ("no bristol sorry", "in july instead",
# "sorry, in august thanks", "no, 500 i mean"). The readers above are anchored at the end of the
# line, so one of those words stopped the value being read at all, and the person's own line went
# back to them ("Got it — no in july sorry."), which is the restatement STYLE.md rules out. The
# words here name nothing, so a run of them after the value is still the value.
CORRECTION_TAIL_WORDS = frozenset("""sorry soz thanks cheers please pls
    instead then now though tho anyway either too also again ok okay ha haha lol lmao""".split())
# "i mean" and "i meant" trail a correction in the same way ("sorry, in july i mean"), and they
# are two words, so they are their own run.
CORRECTION_TAIL = (r"(?:" + CORRECTION_WHY + r")?"
                   r"(?:\s*,?\s*(?:i\s+mean|i\s+meant|i\s+mean\s+it|"
                   r"(?:" + "|".join(sorted(CORRECTION_TAIL_WORDS)) + r")))"
                   r"*\s*[.!?]?\s*$")


def _a_tail_hangs_off(pattern, then=""):
    """`pattern` with a run of the words that name nothing allowed after its value.

    Every reader here finishes at the end of the line, so the run goes on the end: the value is
    what the reader already knows how to find, and what follows the value is said around it -
    `then` is what may come between the value and the run.
    """
    if not pattern.rstrip().endswith("$"):
        return pattern
    return pattern.rstrip()[:-1] + then + CORRECTION_TAIL


# A place corrected to can be said with the going that shows which fact it is: "actually its
# cornwall we go to" after "im going to rome in may". The words are the frame around the place,
# the way "in july instead" is a frame around the month, and the value is the place.
CORRECTION_TRIP_FRAME = (r"(?:\s+(?:we|i)\s+(?:go|went|'re\s+going|are\s+going|'m\s+going"
                         r"|am\s+going)(?:\s+to)?)?")
# The value readers, opened up to the run of words that name nothing after the value.
CORRECTION_BARE = re.compile(_a_tail_hangs_off(CORRECTION_BARE.pattern,
                                               CORRECTION_TRIP_FRAME), re.I)
# "no the 12th of july at 6": the time of day comes after the date people correct to, and the
# date is still the date with it there.
CORRECTION_DATE = re.compile(
    _a_tail_hangs_off(CORRECTION_DATE.pattern,
                      r"(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm|o'?clock)?)?"), re.I)
AMOUNT_CORRECTION_BARE = re.compile(_a_tail_hangs_off(AMOUNT_CORRECTION_BARE.pattern), re.I)


def a_value(phrase):
    """True when a phrase reads as a value (a name, a place, a number), not as a clause.

    Two things can go wrong. A clause ("no, i am not on shift") is a sentence, not a value, and is
    refused by its opener. A phrase that only points at something ("the other one", "nothing",
    "three of them") has no thing in it to keep, so it is refused by what it is made of: if none
    of its words names anything, there is nothing here to remember."""
    parts = re.findall(r"[a-z0-9']+", str(phrase or "").lower())
    if not parts:
        return False
    if len(parts) > 3 and not DATE_VALUE.fullmatch(str(phrase or "").strip()):
        return False
    if parts[0] in CLAUSE_OPENERS or parts[0] in NOT_A_VALUE:
        return False
    if any(word in POINTING_AT for word in parts[1:]):
        return False
    names = [word for word in parts if word not in ARTICLES]
    return any(word not in NOT_A_VALUE and word not in CLAUSE_OPENERS for word in names)


def reread(value, key):
    """The facts a corrected value states when it is read in the shape that key arrives in."""
    shape = CORRECTION_SHAPE.get(key)
    value = re.sub(r"^(?:a|an|the)\s+", "", str(value or "").strip(), flags=re.I)
    if not shape or not value:
        return {}
    found = extract(shape.format(value))
    found.pop("correction", None)
    return found
# "no a vegan" says the thing they mean with the article chat-speak keeps in front of it, and the
# bare-value reader cannot see it: its value starts at a letter run of two, so "a" is no value at
# all, and the line filed nothing at all - "im vegetarian" stayed the only diet in the store while
# the person said they were vegan. Only the whole line is read here, and only the article plus one
# to two words, so "no a bit tired" and "no a good idea really" stay lines about nothing. The
# animal is left out on purpose: "no a cat" after "i have a dog" is another pet, and the pet
# reader already has it (see NO_THEN_A_THING above). "actually a stir fry" is left out for the
# same reason: the swap reader already moves the dish, and claiming the line here changed which
# pairing the drink answer was for.
NO_THEN_A_THING_NAMED = re.compile(
    r"^\s*(?:no|nope|sorry|oops)[,.]?\s+(?:a|an)\s+"
    r"([a-z][a-z'-]{1,20}(?:\s[a-z][a-z'-]{1,15})?)\s*[.!?]?\s*$", re.I)

# a job after "I'm a ..." / "I work as ..." / "my job is ..."
# "I'm a nurse": the article is the signal. Without it "I'm caught outside" reads as a job.
JOB_AFTER = re.compile(r"\b(?:i(?:'m| am)|im)\s+(?:now |just )?(?:a|an)\s+([a-z][a-z '-]{2,30})",
                       re.I)
# "i've just become a teacher", "i retrained as a plumber": the job arrives as a change, and it
# is still the job they have now. "i'm now a teacher" is the same move, said with "now".
# Only the verbs that cannot mean anything else: "i switched to a cheaper tariff" and "i moved
# into a studio flat" take the same shape and would file a tariff or a flat as the job.
JOB_BECOME = re.compile(r"\b(?:(?:i(?:'ve| have)?|ive)\s+(?:just\s+)?(?:become|became|retrained as|"
                        r"qualified as))\s+(?:a|an)\s+([a-z][a-z '-]{2,30})",
                        re.I)
# How the job was said decides how it is said back: "i work as a nurse" is "you're a nurse",
# while "i work in a warehouse" is "you work in a warehouse" and never "you're a warehouse".
# The article is part of the match so "in an office" leaves "office" and not "n office".
# A job said in the past is still their job. Somebody coming back to work after years at home
# says it this way - "i was a teaching assistant before the kids", "i used to be a nurse", "i
# worked as a carer" - and the store took only the present tense ("i work as", "i'm a"), so the
# line was filed nothing and a turn later the bot denied it: "what was my job before" got "You
# haven't told me what you do yet". The noun phrase stops at the word that says when, because
# "before the kids" and "until 2019" are not part of the job.
JOB_WAS = re.compile(
    r"\b(?:i|we)\s+(?:was|were|used to be|used to work as|worked as|was working as|"
    r"were working as)\s+(?:(as)\s+)?((?:an?|the)\s+)?"
    r"([a-z][a-z '-]{2,30}?)(?=\s+(?:before|until|till|then|after|years|when|but|and|"
    r"in \d{4}|at the time)\b|[,.;!?]|$)", re.I)
# A word for how old they were is not a job: "i was a kid", "i was a teenager", "i used to be a
# lad". What they did all day is the job; these only say when.
WAS_NOT_A_JOB = frozenset("""kid kids child children boy girl baby toddler teenager teen lad lass
man woman person human""".split())
JOB_WORK = re.compile(r"\b(?:i work (as|in|at|for|on)|i work|my job is|"
                      r"i(?:'m| am) working as|im working as)"
                      r"\s+((?:an?|the)\s+)?([a-z][a-z '-]{2,30})", re.I)
JOB_FRAME = frozenset(("in", "at", "for", "on"))
JOB_APPOSITIVE = re.compile(r",\s*(?:a|an)\s+([a-z][a-z '-]{2,30})", re.I)
# A comma and a noun after something they have is the thing itself, not what they do: "we have
# two cars, a fiesta and a focus" and "i have a bike, a giant" were filed as the job `fiesta`
# and `giant`, and the store then answered "what do i do" with them. A person naming their job
# after a comma ("im jess, 28, from dublin, a nurse") has no having word before the comma.
POSSESSION = re.compile(
    r"\b(?:i|we)(?:\s+(?:have|had|has|got|own|bought|keep|kept|just got|recently got))\b[^,]*,\s",
    re.I)
# Nothing but the way a correction opens is not a person for a noun to be about: "i have a dog" and
# "no, a cat" was filed as the job `cat`, and the store then answered "what do i do for work" with
# "You told me you're a cat." The appositive that reads "im jess, 28, from dublin, a nurse" needs
# somebody before its comma to be about.
CORRECTION_OPENER_WORDS = frozenset("""no nope not sorry soz ok okay well actually oh ah
    yes yeah nah right wait anyway and but so then also just hi hey hello thanks please""".split())
# "i got a job at tesco", "i just got the job at the co-op", "i start my new job at tesco on
# monday": the line names where they work without ever saying "i work there", so the store kept
# nothing and the follow-up ask ("where do i work now") denied it - "You haven't told me what you
# do yet". The job word is required: "i started at the gym" names no job at all.
JOB_GOT_AT = re.compile(
    r"\b(?:i|i've|ive)\s+(?:just\s+|finally\s+|only\s+|now\s+|recently\s+)?"
    r"(?:got|get|gotten|landed|bagged|start|started|began|begin|begun)"
    # "work" is not a job word here: "i got work at the weekend" names a shift and "i got my work
    # at the office done" names a task, and both were read as an employer. "job interview" and
    # "job offer" are not the job either: a person who is still being interviewed has not got it.
    r"\b[^.!?]{0,25}?\b(?:job|role|position|contract)\b"
    r"(?!\s+(?:interview|interviews|offer|offers|application|applications|trial))"
    r"[^.!?]{0,20}?\b(at|with|in)\s+(an?\s+|the\s+)?([a-z][a-z '&.-]{2,30})", re.I)
# "with" is a frame like "at": "i got a job with the council" is where they work.
JOB_GOT_FRAME = frozenset(("at", "with", "in"))
# What the words after "at"/"with" must not be. Not every line that gets a job says where: "i got
# a job at christmas" is a date, "at the weekend" a shift, "at my old firm" the person's own words
# about the past and "with a start date in may" the paperwork. Filed as places they were answered
# "You work at Christmas" and "You work at Your old firm", where the line had only been quoted.
JOB_GOT_NOT_A_PLACE = NOT_PLACES | frozenset("""soon notice point start beginning first last next
day week weeks month months moment present past future offer interview application trial salary
wage wages money hours shift shifts nights evenings mornings""".split())
JOB_GOT_POSSESSIVE = re.compile(r"^(?:my|our|your|their|his|her|its|mine|ours|yours)\b", re.I)
# Somewhere people are employed that is also a word for going there: "i got a job at the
# hospital", "... at a school" and "... at the office" are the commonest way of naming an
# employer there is, and these words are on the not-a-place list so that "im in hospital" is
# not read as a city. After a job word they can only be where the person works.
JOB_GOT_AN_EMPLOYER = frozenset("""hospital school college university office surgery
practice nursery""".split())


def a_place_that_employs(phrase):
    """Whether the words after "at"/"with" name somewhere a person works.

    "i got a job at tesco" names an employer. "i got a job at christmas" (a date), "at the
    weekend" (a shift), "at my old firm" (the person's own words) and "with a start date in may"
    (the paperwork) name no employer, so they are left to the readers that quote the line.
    """
    words = str(phrase or "").strip(" .!?,").split()
    if not words:
        return False
    said = " ".join(words)
    if JOB_GOT_POSSESSIVE.match(said):
        return False
    if (words[0].lower() in JOB_GOT_NOT_A_PLACE
            and words[0].lower() not in JOB_GOT_AN_EMPLOYER):
        return False
    return True
# "i got a new job as a nurse", "i start my job as a carer on monday": the job is named after
# "job as", and whether it is the speaker's own is read from the clause in front of it.
JOB_AS_A = re.compile(r"\bjob\s+as\s+(?:an?\s+)?([a-z][a-z '-]{2,30})", re.I)
JOB_OWN_VOICE = re.compile(r"\b(?:i|i've|ive|im|i'm)\b", re.I)
# "my new job as a nurse" is theirs; "my brother got a job as a chef" is his, and the mine
# frame is the word "my" with nothing about a person between it and the job.
JOB_MINE = re.compile(r"\bmy\s+(?:new\s+|first\s+|current\s+)?$", re.I)
# A job they want, or are applying for, is not one they have: "i want a job as a teacher" was
# said back as "you're a teacher".
JOB_WANTED = re.compile(r"\b(?:want|wanted|wanting|wants|looking for|hoping|hope|apply|applied|"
                        r"applying|application|would like|thinking of|considering|training to|"
                        r"study|studying|studied|need|needs|trying|try|dream|goal|someday|"
                        r"one day|qualified|interview|interviewing)\b", re.I)
# A noun that only exists in a judgement of oneself. "i'm a doormat" and "i'm a problem for my
# team at work" have the same shape as "i'm a nurse" to the job reader below, so they were filed
# as a job and read back as "Noted: you're a doormat." - the coldest answer there is to somebody
# saying what they think of themselves. Nothing here is a thing a person does.
# A noun that is itself an insult is a verdict whenever it is said about the speaker, whether or
# not it is also a role: "im an awful coward", "im a right brat". The insult nouns are on the same
# list as the ones above, so the job reader and the judgement reading can never disagree about
# what a word is.
JUDGEMENT_NOUNS = frozenset("""
burden joke doormat letdown disappointment waste problem mistake nuisance embarrassment fraud
imposter impostor hypocrite mess failure loser idiot muppet moron fool clown
coward liar cheat bully crybaby slob brat wimp
""".split())

# Who somebody is is not what they do all day. "im a woman", "im a girl" and "im a pensioner"
# were kept as jobs, and the chat pool answered "A woman - nice one. What's a normal day like for
# you?" - a workplace question about a line that named no workplace. The family words below are
# the same shape, and a line that says both ("im a mum of two") keeps the person.
JOB_STOP = frozenset("""bit little big huge real good bad terrible complete total rubbish great
boring bored stressful exhausting tiring draining demanding repetitive mind numbing busy quiet slow
fine okay ok awful horrible crap pants nightmare easy hard tough long short dull repetitive
massive proper new first second lot lots fan week month year while bit bit more less couple
surprise
few kind sort mum dad mother father parent nan granny grandad
woman women man men girl boy lady ladies bloke guy teenager teen pensioner
brit briton englishman englishwoman scotsman scotswoman
somewhere anywhere nowhere""".split())
# A judgement said about themselves is not a fact about the world. "im an idiot" is how they
# feel today, not what they do all day, and "im a bad mum" does not mean they have told the chat
# about a mum. The words are the ones people reach for when they are being hard on themselves;
# the shape that matters is the speaker as the subject ("im a hopeless cook", "im a lazy
# student"), so "my mum is a teacher" and "im a nurse like my mum" are untouched.
SELF_JUDGEMENT = frozenset("""
bad terrible awful horrible rubbish useless hopeless worthless pathetic stupid dumb thick
idiot imbecile moron failure loser letdown disappointment burden nuisance waste mess disaster
wreck nightmare fool clown muppet fraud imposter impostor hypocrite doormat lazy selfish
greedy ungrateful nasty boring shit crap lousy naff rotten dreadful
shitty crappy crapola shite pants wank bollocks tosser twat prick git sod bugger arse arsehole
""".split())
# The same words said the ruder way, and the ones built out of them ("im shitty", "im crappy",
# "im bollocks", "im pants"), were kept as names because none of them is in the state lists the
# name reader asks. The note is out here on purpose: a "#" line written inside the triple quotes
# above is data, not a comment, so `.split()` turned every word of it into a judgement - and any
# reader that builds a shape out of this set then matched the prose ("the", "in", "and", "of",
# "as", "all", "is", "them"), which read a plain fact about the person as a verdict on themselves:
# "im in bristol" answered "you're being harder on yourself than you'd be on a friend".
# The noun after the word is what makes a judgement a verdict. A role with somebody on the other
# side of it - "im a bad mum", "im a shit driver", "im a lazy student" - is a verdict on the job
# they are doing, and saying it back to them agrees with it. A habit being described - "im a bad
# sleeper", "im a terrible dancer" - is a fact about them like any other, kept and said back, and
# only how the chat answers it changes (bot/modules/chat.py, `_judged_a_role`).
ROLE_YOU_CAN_FAIL = frozenset("""
mum mom mummy mam mother mumma dad daddy father parent parents guardian carer friend partner
husband wife son daughter brother sister sibling child kid colleague coworker boss manager
employee worker teacher nurse doctor cook driver parent person student pupil apprentice learner
""".split())
# "poor" is a judgement only in front of a role: "im a poor parent" is how they feel about the
# job they are doing, and "im poor this month" is about money, which the store does keep.
SELF_JUDGEMENT_ROLE_ONLY = frozenset("poor".split())
# The relation in "im a bad mum" / "im a mum of two" is the role they are describing themselves
# in, not another person: the subject is the speaker and the relation is what they are, said with
# an article rather than "i have". "my mum is ill" and "im a nurse, and my mum is a nurse too"
# are still about a person, so only the frame straight before the word counts.
SELF_AS_A_ROLE = re.compile(
    r"\b(?:i'?m|i am|im|we'?re|we are)\s+(?:a|an|such a|such an)\s+(?:[a-z][a-z'-]*\s+)?$"
    r"|\b(?:feel|feels|felt|feeling)\s+like\s+(?:a|an|such a|such an)\s+",
    re.I)
# A word that is a judgement about themselves is one about how they are, not about a stretch of
# time: "im an awful lot better now", "im a bad week away from finishing" are not verdicts, and
# answering them with "that is a hard thing to say about yourself" reads as not listening.
NOT_A_JUDGEMENT_AFTER = (r"(?!\s+(?:lot|bit|deal|day|days|week|weekend|month|year|time|times|"
                         r"mood|thing|things|while|way|shame|pity|job)\b)")
# The judgement said rather than compared: "im a bad mum", "im an idiot", "i feel useless". The
# words alone are not enough ("i had a terrible day" is about the day), so the speaker has to be
# the subject and the word has to be what they say they are.
SELF_JUDGEMENT_SAID = re.compile(
    r"\b(?:im|i am|i feel|i felt|feeling|feel)\s+(?:like\s+)?"
    r"(?:such\s+|a bit of\s+|a bit\s+|a right\s+|a total\s+|a complete\s+|really\s+|so\s+|"
    r"just\s+|always\s+|pretty\s+|very\s+|quite\s+)*(?:a\s+|an\s+)?"
    r"(?:" + "|".join(sorted(SELF_JUDGEMENT)) + r")\b" + NOT_A_JUDGEMENT_AFTER
    + r"|\b(?:im|i am|i feel|i felt|feeling|feel)\s+(?:like\s+)?(?:a\s+|an\s+|a right\s+|such a\s+)"
    r"(?:" + "|".join(sorted(SELF_JUDGEMENT_ROLE_ONLY)) + r")\s+"
    r"(?!(?:lot|bit|day|days|week|weekend|month|year|time|times|mood|thing|things|while|"
    r"lot better|deal)\b)[a-z]+", re.I)


# The word and the noun after it: "im a bad mum", "im a bad sleeper". Which noun it is decides
# whether the line is a verdict on a role or a fact about a habit.
SELF_JUDGEMENT_ABOUT_A_NOUN = re.compile(
    r"\b(?:im|i am|i feel|i felt|feeling|feel)\s+(?:like\s+)?(?:a|an)\s+(?P<judged>"
    + "|".join(sorted(SELF_JUDGEMENT | SELF_JUDGEMENT_ROLE_ONLY))
    + r")\s+(?P<next>[a-z][a-z'-]*)", re.I)
# The word after the judgement is only a noun that qualifies it when it is not the rest of the
# sentence: "im a bad sleeper" is a habit, and "im a failure and i know it" is still a verdict on
# themselves - the word judged decides on its own there, where the line carries on in a connective
# or a preposition rather than in a noun.
JUDGEMENT_TAIL = frozenset("""and but so because though although when whenever if at in on
really tbh again today tonight now honestly actually anyway though still even too also as for
with of from to that which who""".split())


def is_a_judgement(text):
    """Whether the line is the speaker judging themselves, not telling a fact about the world.

    "im a bad mum" is not news about a mum, "im an idiot" is not a job, and neither is something
    the store should say back to them as a fact ("you said you are a bad mum" agrees with them).
    The chat answers these as feelings (bot/modules/chat.py, OWN_HARSH): this is the one reading
    the other parts share, so a judgement is never filed and never recalled as one.
    """
    low = " ".join(str(text or "").lower().replace("\u2019", "'").replace("'", "").split())
    about = SELF_JUDGEMENT_ABOUT_A_NOUN.search(low)
    if about:
        # Where the word is followed by a noun, that noun decides: "im a bad mum" is a verdict and
        # is never said back, "im a bad sleeper" is a fact about a habit and is kept.
        noun = about.group("next")
        if noun in JUDGEMENT_TAIL:
            # The line carries on in "and"/"at"/"really" rather than in a noun, so there is no
            # habit being described and the word judged is the whole verdict: "im a failure and i
            # know it" is the same line as "im a failure".
            return about.group("judged") in SELF_JUDGEMENT or about.group("judged") in ROLE_YOU_CAN_FAIL
        return noun in ROLE_YOU_CAN_FAIL or noun in SELF_JUDGEMENT or noun in JUDGEMENT_NOUNS
    return bool(SELF_JUDGEMENT_SAID.search(low))
# The words that take back the value said before them, in the shapes people say them: "im a
# teacher not a nurse", "an engineer rather than an accountant", "york instead of leeds". A fact
# said with the one it replaces in the same breath is the value in front of these words.
TAKE_BACK = (" not ", " rather than ", " instead of ")
TAKE_BACK_SPLIT = re.compile(r"\s*(?:,|;)?\s+(?:not|rather than|instead of)\b", re.I)
# "not" does two jobs. One takes a value back ("not leeds" names another place); the other
# qualifies the value in front of it ("not far from the station" says where Leeds is, and is not
# another place at all). These are the words that make it the qualifier, so a place keeps its name
# and the words after it are said instead of being thrown away.
QUALIFYING = frozenset("""
far too very that quite long much more near close nearby just only really entirely totally
always good bad great nice close
""".split())


def take_back_cut(phrase):
    """The phrase up to the words that take it back, with a qualifier's own words left in.

    "i live in york not leeds" is York, and "i live in leeds not far from the station" is the
    whole phrase: the second says where Leeds is rather than naming another place, so cutting at
    it would throw away what the person told us.
    """
    text = str(phrase or "")
    for match in TAKE_BACK_SPLIT.finditer(text):
        after = text[match.end():].split()
        if after and after[0].lower().strip(".,;:!?") in QUALIFYING:
            continue
        return text[:match.start()]
    return text


def qualified_by(phrase):
    """The qualifier said after a value ("not far from the station"), or "".

    The words are the person's own, so a reply can say them back: "Leeds, not far from the
    station" is the answer they gave, not just the name.
    """
    text = str(phrase or "")
    for match in TAKE_BACK_SPLIT.finditer(text):
        after = text[match.end():].split()
        if not after or after[0].lower().strip(".,;:!?") not in QUALIFYING:
            continue
        said = text[match.start():].strip(" ,.;:-'")
        if said:
            return said
    return ""
def _the_role(words):
    """The role in the first words of a phrase, with a joining word left off its end.

    "im a nurse on a ward" kept "nurse on a" - three words cut into the place phrase - and the
    store said that back as a job ("You're a nurse on a") which reads as a sentence cut in half. A
    role is a noun and its qualifiers ("primary school teacher", "head of sales"), so a tail of
    prepositions, articles and conjunctions is dropped rather than kept.
    """
    words = list(words[:3])
    while words and words[-1].lower().strip(".,!?") in JOB_DANGLING:
        words.pop()
    return " ".join(word.lower() for word in words)


# Words that cannot end a role: "nurse on a", "teacher at the", "driver for" are the line turning to
# something else, cut three words in, and the person's job is what is left in front of them.
JOB_DANGLING = frozenset("""a an the on at in of for with to and but so who that my our their his her
its this these those over under near across by from as""".split())
JOB_TAIL = (" in ", " at ", " for ", " with ", " who ", " that ", " and ", " but ", " so ") + TAKE_BACK
# With a place preposition the job is the place, and what follows is a shift or a day rather
# than part of it: "i work in a warehouse on the night shift" is a warehouse.
JOB_TAIL_PLACE = JOB_TAIL + (" on ", " near ", " across ", " covering ", " doing ",
                         " starting ", " starts ", " beginning ", " begins ")
# A job the person says they have changed is the job now, and the line rarely says it the way
# "i work as a nurse" does: "i changed jobs, im in a hospital now" names the new place in a
# clause of its own. Read on its own that clause could be anywhere ("im in a hospital" visiting),
# so it is only a job when the same line has said the old one is gone.
CHANGED_WORK = re.compile(r"\b(?:(?:changed|switched|left|quit|packed in|gave up|lost)\s+"
                          r"(?:my |the )?(?:job|jobs|work|role|career)\b|new job\b)", re.I)
WORK_NOW = re.compile(r"\b(?:i(?:'m| am)|im|we(?:'re| are))\s+(?:now\s+)?"
                      r"(?:working\s+)?(in|at)\s+(an?|the)?\s*"
                      r"([a-z][a-z '-]{2,30}?)\s+(?:now|these days)\b", re.I)


# When or where a person works is not what they do: "i work nights", "i work from home",
# "i work two jobs". The store keeps the line as work ("you work nights"), but a detail like
# this must never take the place of a job they have already given.
WORK_DETAIL = frozenset("""
    night nights day days evening evenings morning mornings afternoon afternoons weekend
    weekends weekday weekdays shift shifts earlies lates late early overtime flexi flexitime
    home away abroad remotely onsite hybrid
""".split())
# The words a detail is said with, which say nothing on their own: "from home", "two jobs",
# "part time", "late shifts".
WORK_DETAIL_FILLER = frozenset("""
    a an the from at in on to my two three four both all full part time times job jobs of and
    every most some
""".split())


def is_a_place_of_work(frame):
    """Whether the frame says where they work rather than what they do.

    "i work in a school" is a place told with a preposition; "i work as a nurse" and "im a
    teacher" are the work itself. `facts.extract` writes the frame, so the two are told apart
    without looking at the word: a school, an office and a bakery are all places, and what is
    inside the question "what do you do" is the role beside them.
    """
    preposition = str(frame or "").strip().split(" ")[0].lower()
    return preposition in ("in", "at", "on")


def is_a_work_detail(value, frame=None):
    """Whether what a line says about their work is only when or where it is, not what it is.

    "i work nights" says when, "i work in a school" says where; "im a nurse" says what. The
    store keeps all three, but only the what is the job, so a shift or a place never takes the
    place of a role: after "im a nurse" and "i work nights" the job is still nurse, and after
    "im a teacher" and "i work in a school" it is still teacher.
    """
    if is_a_place_of_work(frame):
        return True
    words = re.findall(r"[a-z']+", str(value or "").lower())
    meaningful = [word for word in words if word not in WORK_DETAIL_FILLER]
    if not meaningful:
        # "from home", "two jobs", "part time": nothing but the filler that says it is a detail.
        return bool(words)
    return all(word in WORK_DETAIL or word == "job" or word == "jobs" for word in meaningful)


def work_weight(value, frame=None):
    """How much a line about their work says: 3 for the role, 2 for a place, 1 for a shift.

    A role is what they do, a place is where, a shift is when, and a fuller answer never loses
    to a thinner one: "i work in a bakery" keeps the bakery when "i work nights" comes after it,
    and "im a teacher" keeps the teacher when either comes after it.
    """
    if not is_a_work_detail(value, frame):
        return 3
    return 2 if is_a_place_of_work(frame) else 1


def _finish(word):
    return word.strip().strip(".,!?;:'\"").lower()


# A word at the end that says *when*, not *what*, is no part of a name. "im a chef now" was kept
# as the job "chef now" and said back as "You told me you're a chef now", and "my car is a corsa
# now" was kept as "Corsa Now" and came back as "You drive a Corsa Now." - the same line said an
# hour earlier, without the "now", read as a different job and a different car. The moment the
# line was said belongs to the line, so it is dropped wherever a name is read.
THE_MOMENT = ("right now", "at the moment", "at present", "just now", "these days", "for now",
              "nowadays", "currently", "anymore", "any more", "already", "still", "now",
              "today", "tonight")


def without_the_moment(words):
    """The same words with the moment they were said in taken off the end.

    Only the end is touched, so "a chef in a kitchen now" keeps its kitchen, and a name that is
    nothing but the moment ("now") comes back empty for the caller to drop.
    """
    words = [word for word in words if str(word or "").strip()]
    while len(words) > 1:
        cut = 0
        for span in (3, 2, 1):
            if len(words) >= span and _finish(" ".join(words[-span:])) in THE_MOMENT:
                cut = span
                break
        if not cut:
            break
        words = words[:-cut]
    if len(words) == 1 and _finish(words[0]) in THE_MOMENT:
        return []
    return words


# Words people put round what they say, which say nothing about the thing itself: "my sister is
# called meg tbh", "i work as a nurse haha", "my budget is 300 though". The lexicon expands some
# of them before the store sees the line ("tbh" -> "to be honest"), so both shapes are listed.
# A value that ends with one of them is the value without it: nobody is called Meg To Be Honest,
# and "you're a nurse tbh" reads like a machine reading a transcript back.
TONE_TAIL = ("to be honest", "if i am honest", "if im honest", "i must say", "by the way",
             "for the record", "just so you know", "i suppose", "i guess", "to be fair",
             "haha", "hehe", "lol", "lmao", "hmm", "though", "honestly", "actually",
             "anyway", "tbf", "ngl", "imo", "tbh", "tho")


# A tail is only a tail when the line still stands without it. "my sister is called meg to be
# honest" is Meg, but "im not going to be honest" is about being honest: the phrase is what the
# verb in front of it takes, and taking it off leaves "im not going" - a different thing, said as
# if it were a fact. The same goes for a line that would end on a word that cannot end a
# sentence ("i dont like it, i have to be honest" would come back as "i dont like it, i have").
INFINITIVE = re.compile(r"\b(?:going|go|goes|went|want|wants|wanted|need|needs|needed|try|tries|"
                        r"trying|tried|mean|means|meant|promise|promised|learn|learned|learnt|"
                        r"used|rather|hope|hoping|hate|hates|love|loves|have|has|had|like|likes|"
                        r"prefer|plan|planning|planning)\s*$", re.I)
# Words that a sentence cannot end on: an auxiliary or a determiner left with nothing after it.
NOT_AN_END = frozenset("""to of and but or nor not never the a an my your his her their our its
is am are was were be been do does did has have had will would shall should can could must
may might""".split())
# "may" is the one word on that list that is also a month, and a month can end a sentence: "im
# going to york in may honestly" is a plan for May with a "honestly" after it, not a modal left
# hanging. The word in front says which one it is.
MAY_AS_A_MONTH = frozenset("""in on by from until till to before after during through for
early late mid this next last coming end start""".split())
DAY_OF_A_MONTH = re.compile(r"^\d{1,2}(?:st|nd|rd|th)?$")


def _can_end(words):
    """Whether the last word of a sentence can be the end of it ("may" is the month or the modal)."""
    if not words:
        return False
    last = words[-1].lower().strip(".,!?;:'\"")
    if last not in NOT_AN_END:
        return True
    if last == "may" and len(words) > 1:
        before = words[-2].lower().strip(".,!?;:'\"")
        return before in MAY_AS_A_MONTH or bool(DAY_OF_A_MONTH.match(before))
    return False


def no_tone(text):
    """The same words with the tone words people leave at the end taken off.

    Only the end is touched, so "i actually work in a bakery" keeps its shape, and a value that
    is nothing but tone ("haha") becomes "" so the caller can drop it.
    """
    out = str(text or "").strip()
    for _ in range(3):
        low = out.lower().rstrip(" .,!?;:")
        cut = next((phrase for phrase in TONE_TAIL
                    if low.endswith(" " + phrase) or low == phrase), None)
        if not cut:
            break
        left = out[:len(low) - len(cut)].rstrip(" ,;:-.)")
        words = left.split()
        if cut.startswith("to ") and INFINITIVE.search(" ".join(words)):
            break
        if words and not _can_end(words):
            break
        out = left
    return out if out.strip(" ,;:-.") else ""

def _date_change(text):
    """The date a plan is moved to, or None: "we moved it to july", "it's july now".

    Only a month or a day is read, because that is what a plan carries: "put it to one side"
    moves nothing. A question is not a change, so "can we move it to july?" leaves the plan
    where it is until they say they have moved it.
    """
    line = str(text or "")
    if "?" in line:
        return None
    for pattern in (CHANGED_TO, CHANGED_BARE, CHANGED_NOW, CORRECTION_A_DATE,
                    A_TIME_INSTEAD, MOVED_BY_ITS_OWN_VERB):
        found = pattern.search(line)
        if found is None:
            continue
        for group in found.groups():
            if group and _a_date(group):
                return _tidy(group)
    return None


# A day of the month is a date the same way a month or a weekday is: "sorry, it's the 4th"
# moves the appointment to a numbered day, and "the 4th of june" moves it to the day and month
# together. The ordinal ending is what says a number is a day rather than an amount, so "the 4th"
# is a date and "4" on its own stays a number.
ORDINAL_DAY = re.compile(r"(?:the\s+)?\d{1,2}(?:st|nd|rd|th)", re.I)
A_DATE_WORD = MONTHS | DAYS


# A plan's destination is put right the way its date is: "no we changed it to devon", "we moved
# it to florence", "the booking has been moved to portugal". The verb is the same one a date uses
# ("we moved it to july"), so the two are told apart by what the words after it name: a month or a
# day is the date reader's, a place is this one's.
MOVED_PLACE_TO = re.compile(
    r"\b(?:we|i|they|you|we've|weve|i've|ive|they've)\b[^.!?]{0,24}?"
    r"\b(?:changed|change|moved|move|switched|switching|swap|swapped|shifted|transferred|"
    r"rebooked|booked)\s+(?:it|that|this|the\s+booking|the\s+trip|the\s+holiday|the\s+flight)"
    r"\s+(?:to|for|instead\s+to)\s+([A-Za-z][A-Za-z' -]{1,30})", re.I)
MOVED_PLACE_PASSIVE = re.compile(
    r"\b(?:booking|trip|holiday|flight|plan|reservation|its|it's|it)\b[^.!?]{0,30}?"
    r"\b(?:has|have|had|is|its|it's|was|were|been)\s+(?:been\s+)?"
    r"(?:changed|moved|switched|swapped|shifted)\s+to\s+([A-Za-z][A-Za-z' -]{1,30})", re.I)
# The words that name no place at all, however much they look like one after a move: "we changed
# it to the other one", "we changed it to one side".
NOT_A_PLACE_NAME = frozenset("""one ones other others same thing place somewhere else front back
side left right first second third last next top bottom middle here there it that this""".split())


def a_moved_place(text):
    """The place a line moves a plan to: "no we changed it to devon" -> "Devon", else "".

    A plan's destination is put right the way its date is ("we moved it to july"), so the line is
    a correction of the plan the store already holds and not a place of its own. Whether the words
    name a place is the module's own question, asked of the same reader that reads a place said
    out loud, so "we changed it to a cottage" and "i changed it to the other one" name nothing
    here either. A question is not a change, and a date is the date reader's.
    """
    line = str(text or "")
    if not line or "?" in line:
        return ""
    for pattern in (MOVED_PLACE_TO, MOVED_PLACE_PASSIVE):
        for found in pattern.finditer(line):
            places, _home, _said = _places("we are going to " + found.group(1))
            for place in places:
                if _a_date(place) or a_moved_time(place):
                    continue
                if place.lower() in NOT_A_PLACE_NAME:
                    continue
                return place
    return ""


def a_date_put_right(text):
    """True when the line is only a date put right, with no subject of its own.

    "sorry, it's the 4th" and "its the 4th instead" say what the date is and nothing else about
    it, so the date belongs to the thing already in the air. A line that also names something of
    its own - "my exam is on the 4th" - is a date of its own and is read as one.
    """
    line = str(text or "")
    if "?" in line:
        return False
    return bool(CORRECTION_A_DATE.search(line) or A_DAY_TAKEN_BACK.search(line)
                or A_DAY_I_MEANT.search(line) or A_TIME_INSTEAD.search(line))


def the_date_put_right(text):
    """The date the line puts right: "sorry, it's the 4th" -> "the 4th", else ""."""
    line = str(text or "")
    if "?" in line:
        return ""
    for pattern in (CORRECTION_A_DATE, A_DAY_TAKEN_BACK, A_DAY_I_MEANT, A_TIME_INSTEAD):
        found = pattern.search(line)
        if found is not None:
            for group in found.groups():
                if group and _a_date(group):
                    return group.strip(" .,")
    return ""


def a_trip_date_put_right(text):
    """The date a trip is moved to by a line that says how they travel, or "".

    "im going to spain in june" / "actually we fly in september" is the plan they already gave
    us, with its month put right. The line is not a plan of its own, so the store is the only
    one that can read it: it knows whether there is a trip on record to move. A question is not
    a change, so "do we fly in september?" leaves the plan where it is.
    """
    line = str(text or "")
    if "?" in line:
        return ""
    found = TRIP_DATE_MOVED.search(line)
    if found is None:
        return ""
    for group in found.groups():
        if group and _a_date(group):
            return _tidy(group)
    return ""


def _a_date(word):
    """A month or a day: the only values a plan carries, so the only ones a change can name.

    A date is read word by word, so every way of saying one lands here: a month, a weekday, "the
    4th", "the 4th of june", "12 june". The words of a date are only those - a month or a day
    word, an ordinal day, or the "of" that joins them - so "put it to one side" and "it went to
    london" name no date and move nothing.
    """
    phrase = str(word or "").strip()
    if not phrase:
        return False
    seen = False
    a_month = False
    a_plain_number = False
    for piece in re.split(r"\s+", phrase.lower()):
        if piece in ("of", "the"):
            continue
        if ORDINAL_DAY.fullmatch(piece) or piece in A_DATE_WORD:
            seen = True
            a_month = a_month or piece in MONTHS
            continue
        if piece.isdigit() and len(piece) <= 2 and not a_plain_number:
            # A day typed as a plain number, which is how "no, 4 june" is written: it counts
            # only with a month or a day word beside it, because "4" on its own is an amount.
            a_plain_number = True
            continue
        return False
    return seen or (a_plain_number and a_month)


def _tidy(word):
    word = word.strip().strip(".,!?;:'\"")
    return word[:1].upper() + word[1:] if word else word


def _tidy_a_titled_name(word):
    """A name that starts with a title is written the way a name is: "mr smith" -> "Mr Smith".

    Only the title was capitalised in "my landlord is called mr smith", so the store said the
    surname back the way it was typed and the reply had to repair it. Repairing it here means the
    name is stored the way it is said back.
    """
    words = str(word or "").split()
    if len(words) > 1 and words[0].strip(".").lower() in TITLE_WORDS:
        return " ".join(_tidy(part) for part in words)
    return _tidy(word)
# A correction usually arrives with the preposition the fact is said with: "no, to rome instead",
# "no, in naples", "the dentist is on tuesday / no, on thursday". The value is what gets filed, so
# the preposition belongs to the sentence and not to the thing: left on, the plan read back
# "you're going to To rome in may" and the store answered "To rome" when asked where they were
# going (main kept Naples, so this is the one way a correction could make the chat worse).
A_LEAD_PREPOSITION = ("to", "in", "at", "on", "for", "into")
# ... unless the words after it are an idiom rather than a thing: "no, in fact", "no, at all",
# "no, in person" name nothing at all, so there is no value and no correction to file. A place
# that people go to ("no, at home", "no, at work") is a thing and stays.
A_LEAD_IDIOM = frozenset("""fact facts all general public advance particular least long
last once time times order case place touch person people""".split())


def _the_value_alone(phrase):
    """`phrase` without the word of apology, the shrug, or the preposition around a value.

    "no bristol sorry" names Bristol and says sorry for it, and the value on its own is what the
    store wants: left on, the apology went into the city ("Bristol sorry") and the plan read it
    back that way. Only the words that name nothing come off, and the phrase is handed back as it
    is when they are all it has ("no thanks" names nothing either way).

    The preposition in front goes the same way ("no, to rome instead" names Rome) when what is
    left of it is still a thing, and stays when it is only an idiom ("no, in fact").
    """
    words = str(phrase or "").split()
    while len(words) > 1 and words[-1].strip(".,!?;:'\"").lower() in CORRECTION_TAIL_WORDS:
        words.pop()
    if len(words) > 2 and [w.lower() for w in words[-2:]] in (["i", "mean"], ["i", "meant"]):
        words = words[:-2]
    if (len(words) > 1 and words[0].lower() in A_LEAD_PREPOSITION
            and words[1].strip(".,!?;:'\"").lower() in A_LEAD_IDIOM):
        return ""
    if (len(words) > 1 and words[0].lower() in A_LEAD_PREPOSITION
            and re.search(r"[a-z]", words[1], re.I)
            # "sorry for moaning" is an apology for a doing, not a value with "for" in front
            and not (words[0].lower() == "for" and words[1].lower().endswith("ing"))):
        words = words[1:]
    return " ".join(words)


def _tidy_apart(word):
    """The old value said beside the new one. An article in front of it stays lower case, because
    the pair is said as one sentence - "the 12th, not the 5th" - and only a name is a capital."""
    word = word.strip().strip(".,!?;:'\"")
    first, _, rest = word.partition(" ")
    if first.lower() in ARTICLES:
        return (first.lower() + (" " + rest if rest else "")).strip()
    return word[:1].upper() + word[1:] if word else word


INTRO_WORDS = ("hi", "hey", "hello", "yo", "morning", "evening", "alright", "howdy", "hullo")


# The frames a name is given in, with the words in front of it as they read once the filler is
# off: the greeting and the correcting word are filler, the frame is not.
NAME_FRAMES = ("", "im", "iam", "i'm", "i am", "i go by", "i goes by", "we go by",
               "we goes by")


def _lowercase_name_fits(text, match):
    """A name written without a capital only passes if its clause reads as an introduction:
    "hi im alex", a bare "im alex", "sorry i forgot to say, im alex". "im cold" and "im
    caught outside" are sentences about how they are, not introductions."""
    head = text[:match.start(1)]
    for mark in ".!?;":
        at = head.rfind(mark)
        if at != -1:
            head = head[at + 1:]
    head = head.lower().replace("\u2019", "'")
    for phrase in NAME_FILLER_PHRASES:
        head = head.replace(phrase, " ")
    words = [word.strip(",.!?;:'\"()") for word in head.split()]
    # Everything before the name has to be filler and the frame that carries it. "i go by kit"
    # is the same introduction as "im kit" and the whole of "i go by" is the frame, so the
    # lowercase reading has to know it: without it the frame was read as words that are not
    # filler and a name given that way was no name at all.
    left = [word for word in words if word and not _filler_or_intro(word)]
    return " ".join(left) in NAME_FRAMES


def _filler_or_intro(word):
    """Whether a word in front of a name is filler or the greeting that opens a line.

    People stretch a greeting when they are pleased to be there: "hii im dan", "heyy im
    jo", "hellooo im sam" are the same introduction as "hi im dan". The letters held are
    settled here as well, so the greeting still counts as one and the name is kept.
    """
    if word in NAME_FILLER or word in INTRO_WORDS:
        return True
    settled = re.sub(r"(.)\1+", r"\1", word)
    if settled == word:
        return False
    # "hellooo" settles to "helo" with its double l gone too, so the greeting is compared
    # with the runs squeezed on both sides: "hellooo" and "hello" are the same word held.
    return (settled in NAME_FILLER or settled in INTRO_WORDS
            or _squeezed(word) in _SQUEEZED_INTROS)


def _squeezed(word):
    return re.sub(r"(.)\1+", r"\1", word)


# The greetings people stretch, held: "hellooo", "heyyy", "hiii" all squeeze to one of these.
_SQUEEZED_INTROS = frozenset(_squeezed(word) for word in INTRO_WORDS) | {
    _squeezed(word) for word in NAME_FILLER}


# A verb said with the person as its subject ends like this: "sendin", "sortin", "leavin",
# "going", "waitin". A name can too ("justin", "martin"), so the ending on its own is not
# evidence - but a name is followed by the person saying who they are ("im dan my daughter is
# 6"), and a verb is followed by what it is being done to ("im sendin my cv off"). So the
# ending only counts against the name when the line goes on with a determiner and no verb:
# "im sendin my cv off" is not somebody called Sendin, and "im dan my daughter is 6" still is.
VERB_ISH = re.compile(r"^[a-z]{3,}(?:in|ing)$", re.I)
TAIL_DETERMINERS = frozenset("my our the a an this that some his her their".split())


def _tail_has_a_verb(words):
    """Whether a clause says something, rather than being the object of the word before it.

    The verbs an introduction carries are the ones a person says about themselves: "im dan my
    daughter is 6", and the body that hurts ("im justin my back hurts"), the thing that broke
    ("im robin my car broke down") and the day that went wrong ("im justin my boss shouted at
    me"). A guess from the ending is not safe the way it is for a name: "im packin my bags" ends
    in an s too, and the bags are what is being packed, not something the line says about the
    person. So an -s word has to be one of the verbs named here, and the -ed ending has to be
    four letters and more, because "my old shed" and "my bed" end the same way.
    """
    for word in words:
        low = word.lower()
        if low in SAYS_SOMETHING_VERBS or low.endswith("'s") or low.endswith("\u2019s"):
            return True
        if low in SAYS_SOMETHING_ELSE:
            return True
        if len(low) > 4 and low.endswith("ed"):
            # a clause about the person almost always has a past tense in it: "escaped",
            # "shouted", "started", "snapped". A plural noun is what the -s guard is for.
            return True
    return False


# The verbs that turn the words after a determiner into a clause: "im dan my daughter is 6",
# "im sam my sister lives in cork", "im robin my flat is tiny".
SAYS_SOMETHING_VERBS = frozenset("""is are am was were be been being have has had got get gets
do does did will would can could should shall may might must need needs want wants live lives
work works like likes love loves hate hates know knows say says go goes come comes died passed
lost found""".split())

# What a person says next about themselves without a helper verb: the body that hurts, the
# feeling, and the past tense of the everyday verbs that do not end in -ed and are not in the
# list above. Held as whole words, because the -s and -ed endings on their own are plurals and
# nouns as often as they are verbs ("my bags", "my old shed").
SAYS_SOMETHING_ELSE = frozenset("""hurts hurt aches ache aches bleeds bleed swells swells throbs
throb stings sting itches itch kills kill feels feel looked looks seems seems
ran fell left went came broke broke got lost found said told bought sold died ate slept hurt felt
became caught threw took gave made drove wrote saw heard thought stood sat woke quit
""".split())


def _followers_fit(text, end, name_word=None):
    """Whether the line goes on with the rest of an introduction after a name typed without
    a capital.

    An introduction ends where the name ends. "im jess" and "jess and im 34" are
    introductions; "im caught outside" and "im sat in the car" are sentences, and the word
    after the name is what says so. A new clause after a comma is not a tail, though: in
    "im sam, we are moving in june" the name ends at the comma. A capitalised name needs no such
    test: typing it with a capital is the person saying it is a name.
    """
    tail = re.split(r"[.!?;,]", text[end:], 1)[0]
    tail = _without_asides(tail)
    found = re.findall(r"[A-Za-z0-9']+", tail)
    at = 0
    while at < len(found):
        word = found[at]
        low = word.lower()
        at += 1
        if word.isdigit() or word[:1].isupper():
            continue  # an age, or a place or another name: "jess from Leeds", "jess and Tom"
        if low in NAME_SAYS_ABOUT_ME:
            if (name_word and VERB_ISH.match(str(name_word)) and low in TAIL_DETERMINERS
                    and not _tail_has_a_verb(found[at:])):
                # "im sendin my cv off": the determiner opens the object of a verb, and nothing
                # after it says anything about the person, so the word before it was the verb
                return False
            return True  # the rest of the line is the person saying who they are
        if low in NAME_FOLLOWERS:
            continue
        if low in NAME_PLACE_WORDS:
            # "jess from Leeds", "jess living in leeds": where they are is part of saying who
            # they are, so the introduction goes on through it. The place itself is one word
            # and the word in front of it may be the preposition that places it.
            if at < len(found) and found[at].lower() in PLACE_JOIN:
                at += 1
            if at >= len(found):
                return False  # "im jess from" says nothing about where
            at += 1  # the place
            continue
        return False
    return True


def _without_asides(tail):
    """The tail of an introduction with a trailing hedge taken off: "and my daughter is 6 tbh"
    keeps the clause and drops the "tbh", and " to be honest" leaves nothing at all.

    Only an aside that ends the tail is removed, so the same words inside a clause about the
    person are left alone: "im sam, i think i need a new bike" is not cut.
    """
    low = tail.lower().replace("\u2019", "'").replace("'", "")
    changed = True
    while changed and low.strip():
        changed = False
        for aside in NAME_ASIDES:
            aside = aside.replace("'", "")
            stripped = low.rstrip(" ,.!?")
            if stripped.endswith(aside):
                cut = stripped[: -len(aside)].rstrip(" ,")
                low = cut
                tail = cut
                changed = True
                break
    return tail


# Nobody is called a number. Main keeps the list the rest of the reader uses (NUMBER_WORDS,
# above), and this is the one place that did not consult it: "im forty" and "im thirty" were
# read as introductions, so a person who gave their age that way lost their own name.
def _a_state_word(low):
    """Whether the word on its own is one of the states a person describes themselves with."""
    return (low in NOT_NAMES or low in NOT_NAMES_EXTRA or low in NOT_A_NAME_FEELING
            or low in NOT_A_NAME_ILLNESS or low in DIET_WORDS or low in SOBER_WORDS)


# English says a state comes in degrees: happy, happier, happiest; sad, sadder, saddest; hungry,
# hungrier. The ending is not one of NAME_TAIL_MIN's, because "er" is a person's ending as well
# ("im peter", "im oliver", "im jasper"), so nothing stood "im happier" and "im sadder" down and
# both were kept as names. What makes a comparative safe is its stem: "happier" is a feeling
# because "happy" is one, and "peter" is a name because "pet" is nothing.
STATE_DEGREES = (("iest", "y"), ("ier", "y"), ("iest", ""), ("ier", ""),
                 ("est", ""), ("er", ""))
# A doubled last letter is the commonest typo there is, and it is safe to undo because the word
# with one letter fewer is the state the person meant: "im stuckk", "im stresssed".
def _a_degree_of_a_state(low):
    for ending, restore in STATE_DEGREES:
        if not low.endswith(ending) or len(low) <= len(ending) + 2:
            continue
        stem = low[: -len(ending)] + restore
        if _a_state_word(stem):
            return True
        # A short state doubles its last letter before the ending: sad, sadder; big, bigger.
        if len(stem) >= 3 and stem[-1] == stem[-2] and _a_state_word(stem[:-1]):
            return True
    return False


def _a_letter_too_many(low):
    if len(low) < 5 or low[-1] != low[-2]:
        return False
    return _a_state_word(low[:-1])


def _sounds_like_a_state(low):
    """Whether a lower-case word after "im" describes the person rather than naming them."""
    if low in NAMES_THAT_LOOK_LIKE_STATES:
        return False
    if _a_degree_of_a_state(low) or _a_letter_too_many(low):
        return True
    for tail, shortest in NAME_TAIL_MIN.items():
        if len(low) >= shortest and low.endswith(tail):
            return True
    return False


# The states that are not one of the endings above, asked of a closed list rather than of the
# letters: every word here is how somebody is and never what they are called. No state is two
# letters long, and the filler words people put round an introduction are ("a", "an", "so"), so
# the length keeps "im ann" a name: a letter off its run is the article "an".
def _a_word_that_is_a_state(word):
    return len(word) >= 3 and (
        word in NOT_A_NAME_STATE or word in lexicon.FEELINGS or word in lexicon.A_STATE
        or word in NOT_NAMES_EXTRA)


# How somebody looks, said the same way a name is: "she is blonde", "her name is ginger".
# None of them ends in one of NAME_TAIL_MIN's tails, so the endings cannot catch them, and none of
# them is a state either - a hair colour is not a feeling. A closed list, because these are the
# ones people say about a person in a line that is not about their name.
LOOKS_WORDS = frozenset("""
blonde blond brunette ginger redhead fair pale tanned olive freckled spotty pimply
curly straight bald bearded
""".split())


def _a_word_not_a_name(low):
    """Whether a word after "is" says how somebody is rather than what they are called.

    A name put right is read from the word after "is" ("she is rosie"), and that is also how a
    person says everything else about somebody: "she is blonde", "she is twelve", "she is
    tired", "she is married". Without this the correction reader kept Blonde as a person's name
    and said "Blonde, not Amy - got it", the same open class as "im blonde" was for the
    introduction reader. The colours and the numbers written out have no ending to catch them,
    so they are listed; the states, the conditions and the nationalities are the ones the
    introduction reader already knows by their ending or by name.
    """
    return (low in LOOKS_WORDS or low in NUMBER_WORDS
            or _sounds_like_a_state(low) or _a_word_that_is_a_state(low))


# The endings English makes a comparison with. A state takes -er and -est, and a name can carry
# the same two letters by accident (peter, heather, summer), so the stem has to be a state from
# the closed list before the word counts as one.
COMPARED = (("er", 5), ("est", 6))


def _the_state_compared(word):
    """The state a comparison is written in, or None: "happier" is happy, "sadder" is sad.

    The endings table has no room for -er and -est: it answers what a word is built with, and
    "er" is Peter's ending as much as it is a comparison's, so nothing in the name reader could
    tell "im happier" from an introduction and each of them was welcomed by name (agile-jay).
    Only a stem that is a state counts, which is what keeps "im peter" and "im heather" names.
    "happier" keeps the y it lost as an i, and "sadder" carries the doubled consonant English
    puts in front of -er, so both are put back before the stem is asked about.
    """
    for ending, shortest in COMPARED:
        if len(word) < shortest or not word.endswith(ending):
            continue
        stem = word[: -len(ending)]
        if not stem:
            continue
        for state in (stem, _with_its_y_back(stem), stem + "y", stem + "e",
                      *_a_letter_off_each_run(stem)):
            if state and _a_word_that_is_a_state(state):
                return state
    return None


def _with_its_y_back(stem):
    """The y a comparison turned into an i: "happi" is "happy", "angri" is "angry".

    English writes -ier and -iest on a state that ends in y (happy, happier, happiest), so the
    stem of the comparison is one letter off the word it was made from. Only an i is put back,
    because that is the only letter the ending ever changes.
    """
    if stem.endswith("i"):
        return stem[:-1] + "y"
    return None


def _a_letter_off_each_run(word):
    """The word with one letter taken out of each run of the same letter: "stuckk" gives "stuck".

    A held key repeats one letter, so a word typed that way is one letter too long where the key
    stuck, and every run is a place that can happen: "im stuckk", "im worrried", "im sleeeepy"
    are how they are, and each of them was answered "Nice to meet you, ...". One letter off a
    run at a time, not a run cut to one letter, because a state carries a real doubled letter of
    its own ("happy", "worried") and cutting every run would leave "hapy". A word with no run of
    two letters gives nothing back, so no name is bent by this ("im matt" is still Matt).
    """
    out = []
    at = 0
    while at < len(word):
        end = at
        while end + 1 < len(word) and word[end + 1] == word[at]:
            end += 1
        if end > at:
            out.append(word[:end] + word[end + 1:])
        at = end + 1
    return tuple(out)


def _a_state_written_as_a_comparison_or_a_double(low):
    """Whether this word is how they are, in a shape the endings table and the fixer both miss.

    `normalize.reads_as_a_feeling` asks the tables and the one-edit fixer, which between them
    see a feeling and a slip of one. Two shapes of the same word are outside both: the
    comparison ("im happier", "im saddest") and the word typed with a letter held down ("im
    stuckk"). "Nice to meet you, Happier" is the worst of them, because the false name is kept
    for the rest of the conversation and "whats my name" then answers Happier.
    """
    if normalize.reads_as_a_feeling(low) or _the_state_compared(low):
        return True
    if normalize.the_feeling_two_letters_are_gone_from(low):
        # Two letters gone from a long feeling is still how they are: "im stessd" is stressed.
        # The reading repairs it and the reply is right, and the store went on keeping the typed
        # word as the person's name, so the same turn said "Hi Stessd" and "whats my name" then
        # answered Stessd. The repair itself is fenced to a word standing on its own after the
        # be-form ("im stessd", not "my phone screen is cracked"), so it cannot take a name off a
        # word said of a thing.
        return True
    for cut in _a_letter_off_each_run(low):
        if _a_word_that_is_a_state(cut) or _the_state_compared(cut):
            return True
    return False


def _name(text):
    # One line can give two names at once: "my names tom but i go by tommy" says the one that is
    # on the paperwork and then the one they answer to, and the second is the name. Read as the
    # first alone it told a person called Tomas that their name was Tom, so the go-by reading
    # stands in front of the announced one when the line holds both. A go-by said by itself is
    # still read in the pass below, unchanged.
    went_by = _name_from(GOES_BY_NAME, text, guessed=True)
    if not went_by and GOES_BY_NAME.search(text):
        # The go-by can keep a clause of its own: "my names tom but i go by tommy". Read over the
        # whole line the frame is not the first thing in it - a name statement comes first, and a
        # name is not filler - so the reading is made again on its own clause.
        for clause in CLAUSE_SPLIT.split(text):
            if not GOES_BY_NAME.search(clause):
                continue
            went_by = _name_from(GOES_BY_NAME, clause, guessed=True)
            if went_by:
                break
    for pattern in ANNOUNCED_NAME_PATTERNS:
        name = _name_from(pattern, text, guessed=False)
        if name:
            if went_by and went_by.lower() != name.lower():
                return went_by
            return name
    for pattern in GUESSED_NAME_PATTERNS:
        name = _name_from(pattern, text, guessed=True)
        if name:
            return name
    return None



# The lines that say outright that the word is a name, so a word that sounds like a feeling is
# still a name there.
SAYS_A_NAME = re.compile(r"\b(?:my name is|my name's|my names|i am called|im called|"
                         r"call me|you can call me|known as)\b", re.I)


# A judgement on the speaker is how they are, never what they are called. The file already keeps
# the words people reach for when they are being hard on themselves - `SELF_JUDGEMENT` answers
# "im an idiot" and "im a hopeless cook" when the store is deciding whether a word is a job - and
# the name reader never asked it, so "im shit" was answered "Hi Shit - that's the tiredness
# talking, not the truth", and "im naff", "im muppet", "im clown", "im waste" and "im nightmare"
# were kept as names and said back for the rest of the chat. The building of a judgement is a
# judgement too: English makes "shitty" and "crappy" out of the same word with a "-y", and a
# doubled last letter is written before it ("crapp" -> "crap").
def _a_judgement_on_themselves(low):
    if low in SELF_JUDGEMENT:
        return True
    for ending in ("ish", "y"):
        if not low.endswith(ending) or len(low) <= len(ending) + 2:
            continue
        stem = low[: -len(ending)]
        if stem in SELF_JUDGEMENT:
            return True
        if stem[-1] == stem[-2] and stem[:-1] in SELF_JUDGEMENT:
            return True
    return False


def _name_from(pattern, text, guessed):
    """The first word this pattern offers that could be a name, or None."""
    for match in pattern.finditer(text):
        word = match.group(1)
        low = _finish(word)
        if (low in NOT_NAMES or low in NOT_NAMES_EXTRA or low in GO_BY_WAYS
                or low in DIET_WORDS or low in SOBER_WORDS
                or low in lexicon.JOINED_WORDS or len(low) < 2):
            continue  # "im sickof my brother" is "sick of", two words, not somebody Sickof
        if not word[:1].isupper() and (low in NOT_A_NAME_STATE or _a_judgement_on_themselves(low)
                                       or low in NOT_A_NAME_LAUGH or lexicon.is_a_laugh(low)):
            # "my name is quiet" is the same refusal as "im quiet": a describing word is what
            # the person is like however they introduce it, and one session calling them
            # Quiet is worse than not having a name for them. A name that only looks like a
            # state is kept by NAMES_THAT_LOOK_LIKE_STATES below.
            continue  # "im mad" is how they are, not what they are called
        spelled = normalize.spelled(low)
        # A curated spelling of how they are is how they are, however many letters it drops:
        # "im hungrey" is "im hungry" and not somebody called Hungrey. Only the tables speak
        # here; the fixer's guesses stay under the length guard below, because a cut is not
        # evidence.
        if low not in NAMES_THAT_LOOK_LIKE_STATES and any(
                one in NOT_NAMES or one in NOT_NAMES_EXTRA or one in NOT_A_NAME_STATE
                for one in spelled if one != low):
            continue
        if low in NUMBER_WORDS:
            continue  # "im forty" is an age, and nobody is called Forty
        repaired = normalize.repaired_tokens(low)
        # Only a repair that says more than the word did: "gd" is "good", "gud" is "good".
        # A cut is not evidence ("ann" collapses to "an" and is a name), so a shorter reading
        # never talks anybody out of a name.
        if low not in NAMES_THAT_LOOK_LIKE_STATES and any(
                one in NOT_NAMES or one in NOT_NAMES_EXTRA or one in NOT_A_NAME_STATE
                for one in repaired if one != low and len(one) >= len(low)):
            # A chat spelling of how they are is still how they are: "im gd" is "im good", and
            # "im gud" was answered "Nice to meet you, Gud", with the name kept for the chat.
            continue
        if guessed and low not in NAMES_THAT_LOOK_LIKE_STATES and _describes_them(low):
            # The list the store already keeps for "my mum is messy" answers the guessed
            # introduction too, and it answers it with the one test rather than a second list.
            # "im noisy", "im stubborn", "im overweight" and "im tall" are how somebody is, and
            # each was answered "Nice to meet you, Noisy" - or "Overweight" in the deck chat
            # `dq-aug5-06` - and then said back for the rest of the chat. The words that say how
            # a person is are one list (`DESCRIBING_WORDS`), asked by this reader and by the
            # relation reader, so a word added for "my sister is chatty" is refused here as well
            # and the two cannot drift apart. A line that says outright it is giving a name is
            # giving one, the same exception every other reading has, and the names that only
            # look like states (Ahmed, Jared, Mohamed, all "-ed") are kept by the list above.
            continue
        if guessed and low not in NAMES_THAT_LOOK_LIKE_STATES and any(
                one != low and len(one) >= len(low) and _sounds_like_a_state(one)
                for one in repaired):
            # A state typed the way people say it is still a state: "im coughin" is coughing and
            # "im burnin" is burning, and the endings test below cannot see either, because the
            # ending is the part the typing dropped. The repair is the one the reading already
            # makes (`plain` reads "im coughing"), and it can only take a name off a word that is
            # nothing but a state once its last letter is back, so no name loses out: none of the
            # 649 common names repairs to a word with a state's ending. Only the guessed reading
            # ("im ...") is read this way: a line that says it is giving a name is giving one, and
            # "my brother is called crispin" stays a Crispin rather than becoming a crisping.
            continue
        if _a_state_written_as_a_comparison_or_a_double(low) and not SAYS_A_NAME.search(text):
            # A feeling typed with a letter wrong is still how they are, not what they are
            # called: "im knackerd", "im tierd", "im worrid" were all answered "Nice to meet
            # you, ..." because the endings test cannot see a slip. Capitals do not help:
            # "Im Knackerd", "Im Tierd" and "IM SHATTERD" are the same slip, and no name
            # people are given lowers to a feeling word. The one exception is the line that
            # says outright it is giving a name, the same way the sound reading below has it:
            # "my name is board" introduces somebody called Board, and no feeling table should
            # take the name off them.
            continue
        if normalize.reads_as_a_sound(low) and not SAYS_A_NAME.search(text):
            # "im board" is bored, and nobody is called that. A line that says outright that it
            # is giving a name keeps it however the word sounds: "my name is board" is a name.
            continue
        if not word[:1].isupper():
            if _sounds_like_a_state(low) and not SAYS_A_NAME.search(text):
                # The third place the sound of a word stands a name down, and the only one that
                # had no exception for a line that says outright it is naming: "my name is
                # happier" says nothing at all, because a comparison now reads as a state
                # (bot/modules/... the -er table) and the sound test answers True for it.
                continue  # "im knackered", "im coeliac", "im welsh"
            if guessed and (not _lowercase_name_fits(text, match)
                            or not _followers_fit(text, match.end(1), word)):
                continue
        return word[0].upper() + word[1:]
    return None


def _first_tail(phrase, tails=JOB_TAIL):
    """The earliest place the job phrase stops: its position and the word it stops on.

    The order the tails are listed in says nothing about the order they come in the line, so
    "I'm a nurse and I live in Leeds" has to stop at "and", not at the "in" that follows it,
    or the job is kept as "nurse and i".
    """
    found = None
    for tail in tails:
        at = phrase.find(tail)
        if at != -1 and (found is None or at < found[0]):
            found = (at, tail)
    return found


def _job_as_a(text):
    """The "job as a ..." lines that name the speaker's own job, as their matches.

    "i got a new job as a nurse" says what they do, while "my brother got a job as a chef" is
    his job and "i want a job as a teacher" is one they have not got: only a clause that opens
    in their own voice, with no wanting in it and nobody else named, files a job.
    """
    found = []
    for match in JOB_AS_A.finditer(text):
        clause = CLAUSE_EDGE.split(text[:match.start()])[-1]
        if JOB_WANTED.search(clause) or _people(clause):
            continue
        if not (JOB_OWN_VOICE.search(clause) or JOB_MINE.search(clause)):
            continue
        found.append(match)
    return found


# What a judgement word is followed by without making the phrase a job: the reason for it
# ("im a nuisance to my flatmates", "a waste of space") and when or how often the person thinks
# it ("im an idiot sometimes"). A word that names a thing straight after it is the job the noun
# describes instead: "a problem solver", "a waste engineer", "a joke writer".
JUDGEMENT_AFTER = frozenset("""to for at in of on with and but because when yet either too
about around""".split() + """sometimes today lately honestly though mostly usually always really
actually generally now these days""".split())


def _is_a_judgement_phrase(words):
    """Whether "im a <judgement noun> ..." judges the person rather than naming what they do.

    "im a doormat" and "im an idiot sometimes" are what the person thinks of themselves and must
    never be kept as their job. "im a problem solver" uses the noun to describe a job, so the
    phrase is only a judgement when nothing but when or how often comes after the noun.
    """
    if not words or words[0].lower() not in JUDGEMENT_NOUNS:
        return False
    # The noun is the phrase ("a doormat") or the second word opens the reason or says when
    # ("a waste of space", "a nuisance to my flatmates", "an idiot sometimes"). Anything else
    # straight after the noun extends it into a role: a problem solver, a waste engineer.
    return len(words) == 1 or words[1].lower() in JUDGEMENT_AFTER


def _only_discourse_before(before):
    """True when the words in front of a comma name nobody, only the way a correction opens."""
    words = re.findall(r"[a-z']+", str(before or "").lower())
    return all(word in CORRECTION_OPENER_WORDS for word in words)


def _the_correction_named_a_thing(text, match):
    """True when the noun after a correction opens the line and names a thing, not a person.

    "no, a cat" and "no, a fiesta" come after the correction's "no" and name a thing the pet and
    car readers already have; filed as a job they came back as "You told me you're a cat". A
    person comes the same way, so a noun the job lexicon knows is still their job: "what do you
    do" then "actually, a teacher" is a job, and so is "no, a nurse" after one.
    """
    if not _only_discourse_before(text[:match.start()]):
        return False  # somebody before the comma: "im jess, 28, from dublin, a nurse"
    groups = match.groups()
    phrase = ((groups[-1] if len(groups) > 2 else groups[0]) or "").strip().lower()
    words = phrase.split()
    return bool(words) and words[0] not in JOB_WORDS


# The endings a word that names a role has and a word that names a state rarely does: a plumber,
# a barrister, a dentist, a pianist, a chairman, an assistant. The lexicon is the first test and
# this is the second, because the roles people type are endless and the lexicon is not.
ROLE_ENDING = ("er", "or", "ist", "ian", "man", "woman", "ess", "ant", "ent")


def _was_names_a_role(phrase, article=None):
    """Whether a phrase said after "i was" names what they did, not how they were.

    "i was a nurse" and "i was head chef at the pub" are roles. "we were flat out", "i was eight
    weeks pregnant" and "i was born in leeds" are a state, a length and a birth, and read as roles
    they came back late in a chat as "You were a flat out". What a role is said with is an article
    in front of it ("a nurse", "an electrician"), or a word the job lexicon knows ("head chef",
    "student"), or an ending only a role has ("a plumber", "a barrister"). A participle is a verb
    ("i was managing a shop") and a state word is how they were ("flat out", "retired"), so
    neither is a role however noun-like the line looks.
    """
    low = [word.lower().strip(".,!?;:") for word in str(phrase or "").split() if word.strip()]
    while low and low[0] in ("both", "all", "just", "only", "still", "now", "then", "also"):
        low.pop(0)  # "we were both nurses" is the same role said with a word in front of it
    low = low[:3]
    if article and low:
        return True
    if not low:
        return False
    if any(len(word) > 4 and word.endswith(("ing", "ed")) for word in low):
        return False
    head = low[-1]
    if head in STATE_WORDS or head in PAST_STATES or head in PREGNANCY_STATES:
        return False
    # The lexicon is written in the singular and people say the plural: "we were both nurses".
    single = [word[:-1] if word.endswith("s") and word not in JOB_WORDS else word for word in low]
    if any(word in JOB_WORDS for word in low + single):
        return True
    return len(head) > 4 and head.endswith(ROLE_ENDING)


def _job_and_city(text, name=None, question=False):
    job = city = None
    frame = ""
    if name:
        at = text.lower().find(name.lower())
        if at != -1:
            text = text[at + len(name):]
    matches = (list(JOB_AFTER.finditer(text)) or list(JOB_BECOME.finditer(text))
               or list(JOB_WORK.finditer(text)) or list(JOB_WAS.finditer(text))
               or _job_as_a(text) or list(JOB_GOT_AT.finditer(text)))
    if not matches and not POSSESSION.search(text):
        # The appositive is for a person naming what they do; after a having word the same shape
        # names the thing they have.
        matches = [match for match in JOB_APPOSITIVE.finditer(text)
                   if not _the_correction_named_a_thing(text, match)]
        if question:
            # A question with only an appositive is asking about the bot, not saying what the
            # person does: "what are you then, a robot?" filed `robot` as their job, and the next
            # turn told them "you're a robot in Leeds". The noun is theirs only when the line
            # puts them first ("call me jess, a nurse"), so an appositive with no "i" before it
            # says nothing about them.
            matches = [match for match in matches
                       if re.search(r"\bi(?:'m|m| am)\b", text[:match.start()], re.I)]
    if not matches:
        return job, city, frame
    for match in matches:
        groups = match.groups()
        was_working = len(groups) > 2
        phrase = (groups[-1] if was_working else groups[0]).strip()
        place_job = (was_working and (groups[0] or "").lower() in ("in", "at", "for", "on")) \
            or match.re is JOB_AS_A or match.re is JOB_GOT_AT
        cut = _first_tail(phrase)
        if place_job and not cut:
            cut = _first_tail(phrase, tails=JOB_TAIL_PLACE)
        if cut:
            at, tail = cut
            rest = phrase[at + len(tail):]
            if tail.strip() in ("in", "at") and not city:
                place = re.match(r"([A-Z][a-z]+(?: [A-Z][a-z]+)?)", rest.strip())
                if place and place.group(1).split()[0].lower() not in NOT_PLACES:
                    city = place.group(1)
            phrase = phrase[:at]
        if match.re is JOB_GOT_AT:
            if (groups[0] or "").lower() == "in" and not (groups[1] or "").strip():
                # "in" names where the work is only with an article in front of it: "i got a job
                # in a bakery" does, while "i got a job in two weeks" and "in may" name a time.
                continue
            if not a_place_that_employs(phrase):
                # A date, a shift or the person's own words about the past is not where they work.
                continue
        words = without_the_moment(phrase.split())
        if match.re is JOB_WAS and words and words[0].lower() in WAS_NOT_A_JOB:
            # "i was a kid", "i used to be a lad": how old they were, not what they did.
            continue
        if match.re is JOB_WAS and not _was_names_a_role(
                phrase, article=len(groups) > 1 and groups[1]):
            # "we were flat out", "i was eight weeks pregnant", "i was born in leeds": how they
            # were, and when - not what they did.
            continue
        if (not words or words[0].lower() in JOB_STOP or words[0].lower() in NOT_NAMES
                or words[0].lower() in NOT_NAMES_EXTRA
                # Only a phrase that *is* the judgement noun ("im a doormat", "im a joke",
                # "im an idiot sometimes") is one. "im a problem solver" and "im a waste
                # engineer" open with a word on that list and are what the person does: there the
                # noun describes the job rather than the person.
                or _is_a_judgement_phrase(words)):
            continue
        if name and words[0].lower() == name.lower():
            continue
        if words[0][:1].isupper() and len(words) == 1:
            continue
        if re.match(r"\s*\d", text[match.end(match.lastindex or 1):]):
            continue  # "im a size 12" measures them, it is not what they do
        if words[0].lower() in ("bit", "little", "lot", "couple", "few"):
            continue
        if words[0].lower() in ("my", "our", "his", "her", "their", "your"):
            # "i work on my own", "i work on their terms": a possessive names nobody's job.
            continue
        if words[0].lower() in SELF_JUDGEMENT:
            # "im an idiot", "im a hopeless cook", "im a lazy student": how they feel about
            # themselves, not what they do all day. The word is also never a job for anyone
            # else ("my brother is an idiot"), so it is skipped whoever the line is about.
            continue
        job = _the_role(words)
        if match.re is JOB_AS_A and not was_working:
            # "i got a new job as a chef": the line says how the job is said, so it is said back
            # the same way ("you work as a chef"), never with the frame of the job it replaced.
            # The article is read from the words the line used, not from a group: the job group
            # is the one every reader here takes its phrase from.
            article = re.search(r"\bas\s+(an?)\b", match.group(0), re.I)
            frame = "as " + (article.group(1).lower() if article else "a")
        elif match.re is JOB_WAS:
            # A job they had is said back in the past: the frame carries the tense the same way it
            # carries the preposition of a place, so every reader of the job says "You were a
            # teaching assistant" and never "You're a teaching assistant" to an ask that came
            # after "i was a teaching assistant before the kids".
            frame = "was"
        elif was_working and not (groups[0] or "").strip():
            # "i work nights", "i work two jobs", "i work from home": no preposition names where
            # the work is, so the verb itself is the frame and the reply says "you work ..." -
            # never "you're a nights".
            frame = "work"
        elif was_working and (groups[0] or "").lower() in JOB_FRAME | JOB_GOT_FRAME:
            # "in a warehouse", "for the council": the preposition and the article are how they
            # said where they work, so they are kept together and the reply follows them.
            frame = " ".join(part.strip() for part in groups[:2] if part and part.strip())
            if (match.re is JOB_GOT_AT and len(frame.split()) == 1
                    and job.lower() in JOB_GOT_AN_EMPLOYER):
                # "i got a job at school" names an employer without an article, and the store
                # says a workplace back with one: "You work at school" reads as a place the
                # person went to, where "You work at a school" is where they go now. The
                # article is added here rather than in the reply so every reader of the frame
                # (the whole job, the where-do-i-work ask) says it the same way.
                frame += " a"
        break
    return job, city, frame


def place_value(phrase):
    """The place a corrected value names, or "" when the value is not a place at all.

    One word is a place ("leeds", "porto"). Two words only when the first is a naming word
    ("new york", "saint malo"): a place fact is what the last line stated, and "tree nuts" is a
    food, not a city, however much the line before was about where the person lives.
    """
    words = str(phrase or "").split()
    if len(words) > 1 and words[0].lower() not in PLACE_MIDDLE:
        return ""
    return _place_name(phrase)
# The words that take back the value said before them: "i live in york not leeds" names York, and
# the place kept was "York Not Leeds" because a name runs until a word that is not part of one, and
# "not" was not one of those words.
TAKES_ONE_BACK = frozenset(("not", "rather", "instead"))


# "i drive a corsa", "i drive an old fiesta": the car is the thing the verb takes, and it is a
# fact the store keeps under `car`. The ask side has named a car since the slot list was written
# (`_FACT_SLOT`, bot/modules/memory_store.py) and nothing ever filed one, so "what do i drive" and
# "whats my car" had nothing to read. The verb on its own is not a fact: "i drive to work", "i
# drive a lot", "i drive for a living", "i drive carefully" name a place, an amount, a job or a
# manner, and each of those is refused below.
I_DRIVE = re.compile(r"\bi (?:drive|drives|driving)\s+(?P<art>a |an |my |the )?"
                     r"(?P<what>[a-z0-9][\w'-]*(?: [a-z0-9][\w'-]*)?)", re.I)
# Words that make what follows the verb something other than a car. A manner ("carefully"), a
# place ("to work", "home"), an amount ("a lot", "200 miles") and a purpose ("for a living") are
# all things a person drives, and none of them is a thing they own. The class of the thing is not
# the thing either: "i drive a car" and "i drive my mums car" say nothing a "what do i drive" can
# be answered from.
NOT_A_CAR = frozenset("""
about across along around away back badly bargain bike bikes carefully car cars everywhere far
fast for from hard home in into like lorries lorry lots lot me message miles mine motorbike
motorbikes myself nail nowhere off on out point safely slowly somewhere stake that them there
these this those to too truck trucks up us van vans vehicle very wedge work
""".split())
# A distance or a length of time is what follows a drive: "i drive 200 miles a week".
MEASURED = frozenset("miles mile km kms kilometres kilometers hours hour mins minutes day week".split())
# "do i drive a corsa" asks rather than says, and a question states nothing to keep.
CAR_ASKED = re.compile(r"\b(?:do|does|did|should|can|could|would|will|have|has)\s+i\s+drive\b"
                       r"|\bdrive\s+a\b[^?.!]*\?", re.I)
# The car is named without the verb far more often than with it: "its a 2016 fiesta" is how
# somebody answers what they have got, and "my fiesta wont start" says whose it is. Neither
# line was filed, so the chat that had just said what the car was answered "what car was it
# again" with "you haven't told me what you drive". The name is what carries it: the words after
# the frame are read as a car only when one of them is a name from the table the car answers
# already keep (`bot/knowledge/cars.py`), which is the same table that leaves out every word that
# is also an ordinary thing (golf, focus, mini, leaf), so "my focus is on work" names no car.
CAR_NAMED = re.compile(
    r"\b(?:its|it's|it is)\s+(?:a|an)\s+(?:(?:19|20)\d\d\s+)?(?P<what>[a-z][\w'-]*(?:\s+[a-z][\w'-]*)?)"
    r"|\bmy\s+(?P<mine>[a-z][\w'-]*(?:\s+[a-z][\w'-]*)?)", re.I)
# The names, longest first, so "range rover" is read whole rather than as "range".
_CAR_NAMES = []


def _the_car_name_in(phrase):
    """The car name the phrase starts with, or "" when the words name no car."""
    if not _CAR_NAMES:
        from ..knowledge.cars import MODELS  # lazy: the facts need no table to be read
        _CAR_NAMES.extend(sorted(set(MODELS), key=len, reverse=True))
    flat = " ".join(str(phrase or "").replace("'", "").lower().split())
    for name in _CAR_NAMES:
        if flat == name or flat.startswith(name + " "):
            return name
    return ""


# "my fiesta used to do the same", "i sold my corsa last year": a car named in the past was
# theirs and is not what they drive now, so the possessive frame files nothing in a line that
# says so. The answering frame is not read this way - "its a 2016 fiesta" names the car in front
# of them however the chat got there.
CAR_IN_THE_PAST = re.compile(
    r"\b(?:used to|used it|sold|selling|sale|wrote off|written off|scrapped|traded in|part "
    r"exchanged|had|old|previous|previously|before|last car|first car|was|were|years ago)\b", re.I)


def _car_named_in_passing(text):
    """The car a line names without the verb, or None."""
    past = bool(CAR_IN_THE_PAST.search(text))
    for match in CAR_NAMED.finditer(text):
        mine = match.group("mine")
        if mine and past:
            continue
        name = _the_car_name_in(match.group("what") or mine)
        if name:
            return name
    return None


def _car(text):
    """The car a line says they drive, or None when the verb is not about a car."""
    if CAR_ASKED.search(text):
        return None
    for match in I_DRIVE.finditer(text):
        phrase = _finish(match.group("what"))
        article = (match.group("art") or "").strip().lower()
        for tail in TONE_TAIL:
            if phrase.endswith(" " + tail):
                phrase = phrase[: -len(tail)].strip()
        words = phrase.split()
        # "i drive a 2015 golf": a year in front of the model is how people with an older car say
        # it, so the year is dropped and the model kept. A number on its own is a distance or an
        # amount ("i drive 200 miles a week") and names no car.
        while words and words[0].isdigit():
            words = words[1:]
        phrase = " ".join(words)
        if not words:
            continue
        if any(word in NOT_A_CAR for word in words) or words[-1] in MEASURED:
            continue
        if not article and words[-1].endswith("s"):
            # "i drive trains", "i drive lorries": what they drive for a living, not their car.
            continue
        return phrase
    return _car_named_in_passing(text)
# The naming words that are also ordinary adjectives: "new" names a place only in front of a
# word that is a name and nothing else, so "new heights" and "new job" are not places.
ADJECTIVE_NAMING = frozenset("new".split())


def _reads_as_a_plural(name_word, first):
    """Whether the word after a naming word is the plural of something, so not part of a name.

    "new heights", "old ways": the noun after an adjective that also starts place names is a heap
    of something rather than a name. The places it must not cost are the ones said in the
    singular ("new york"), which is the trade this makes: a lower-case "new orleans" is read as
    no place at all rather than as a heap of orleans.
    """
    word = str(name_word or "").lower()
    return first in ADJECTIVE_NAMING and word.endswith("s") and not word.endswith("ss")


# A word that says how something is is not the name of somewhere to go. "im going to rome in
# may" / "actually its fine" was read as a place called Fine: the store held the trip as "Fine in
# may" and "where am i going" answered "Fine." A place can be named after an ordinary word, but
# not after a comment on the thing itself.
NOT_A_PLACE_WORD = frozenset("""fine good great ok okay alright lovely rubbish awful terrible
brilliant perfect amazing wonderful horrible disgusting cancelled canceled booked sorted done
shut closed busy quiet cheap expensive pointless useless worthwhile""".split())


def _place_name(phrase):
    """The name a place phrase really names, in title case, or "".

    A two-word place ends at the first word that is not part of a name: "leeds and work in
    york" is Leeds, "preston last year" is Preston, "staying in tonight" is nothing at all.
    """
    words = str(phrase or "").replace("-", " - ").split()
    # "i live in the uk": a country keeps its article, but "the city centre" is no place, and
    # "the US" is not the pronoun HOME_STOP knows.
    the = ""
    if len(words) > 1 and words[0].lower() == "the" and words[1].lower() in COUNTRY_ARTICLE:
        the, words = "the ", words[1:]
    kept = []
    for i, word in enumerate(words):
        if the:
            kept.append(word)
            break
        low = word.lower()
        # "new york", "saint malo": a naming word that reads as an ordinary word on its own.
        if i == 0 and len(words) > 1 and low in PLACE_MIDDLE:
            # "im going to port my number": a naming word with a determiner after it is the
            # language's own word, not a place ("port my number", "new the way").
            if words[1].lower() in DETERMINERS:
                return ""
            if _an_everyday_word(words[1]) or _reads_as_a_plural(words[1], low):
                return ""  # "im moving to new job in may" is a job, not a place
            kept.append(word)
            continue
        if (low in HOME_STOP or low in NOT_PLACES or low in PLACE_VERBS or low.endswith("ly")
                or low in TAKES_ONE_BACK or low in NOT_A_PLACE_WORD or word == "-"):
            break
        kept.append(word)
    if not kept:
        return ""
    if len(kept) == 1 and kept[0].lower() in PLACE_MIDDLE:
        # A naming word on its own names nothing: "im going to port my number" is the verb, and
        # base filed it as a place called Port and then said "You're going to Port your number."
        return ""
    name = " ".join(kept)
    if len(kept) == 1 and name.lower() in COUNTRY_CAPS:
        return the + COUNTRY_CAPS[name.lower()]
    return the + " ".join(w[:1].upper() + w[1:] if w.islower() else w for w in name.split())


def _born_place(text):
    """The place they were born, when the line says it, or None.

    Only the person's own birth counts, so "my husband was born in cork" is his. A birth place is
    kept apart from where they are from: "i was born in lagos but i grew up in ibadan" is from
    Ibadan and born in Lagos, and both questions have an answer.
    """
    born = []
    for pattern in (FROM_PLACE, FROM_GROWN):
        for match in pattern.finditer(text):
            if not re.search(r"\bborn\b", match.group(0), re.I):
                continue
            name = _place_name(match.group(1))
            if name:
                born.append((match.start(), name))
    return max(born)[1] if born else None


# A move names two places: the one they went to and the one they came from. "i moved to preston
# from bolton last year" said both, and the origin was kept as nothing - the older patterns want
# the person in front of "from" ("im from leeds"), and here the subject is at the front of the
# line with the destination between it and the word. So the move verb is the cue: whatever "from"
# names after it is where they came from.
FROM_A_MOVE = re.compile(
    r"\b(?:moved|moves|moving|relocated|relocating|relocate|migrated)\b[^.;!?]{0,40}?"
    r"\bfrom\s+([A-Za-z][A-Za-z'-]{1,}(?:[ -][A-Za-z][A-Za-z'-]{1,})?)\b", re.I)


# The same move typed the other way round - origin first, destination second. "i moved from leeds
# to bristol" named Bristol as plainly as the other order names Preston, and only the origin was
# kept: "where do i live" answered "You haven't told me where you live - I know you're from Leeds."
A_MOVE_FROM_THEN_TO = re.compile(
    r"\b(?:moved|moves|moving|relocated|relocating|relocate|migrated)\s+from\s+"
    r"[A-Za-z][A-Za-z'-]{1,}(?:[ -][A-Za-z][A-Za-z'-]{1,})?\s+"
    r"(?:to|into)\s+"
    r"(?P<place>[A-Za-z][A-Za-z'-]{1,}(?:[ -][A-Za-z][A-Za-z'-]{1,})?)\b", re.I)


def _the_person_moved(before):
    """True when the clause in front of a move verb has the person themselves as its subject."""
    clause = re.split(r"[.;!?,]|\band\b|\bbut\b|\bso\b", str(before or ""))[-1]
    return bool(re.match(r"\s*(?:i|im|i'm|ive|i've|id|we|were|we're|weve|we've|we'd)\b",
                         clause, re.I))


def _from_place(text):
    """The place they say they are from, when the line says where that is.

    What they say about where they are from beats where they were born, and the last of those
    wins, because that is the one the person settled on: "im from leeds, originally from
    bradford though" is Bradford, and "i was born in lagos but i grew up in ibadan" is Ibadan.
    Only the person's own history counts, so "my mum grew up in kerala" names nothing about them.
    """
    born = []
    said = []
    for pattern in (FROM_PLACE, FROM_MORE, FROM_GROWN, FROM_A_MOVE):
        for match in pattern.finditer(text):
            if pattern is FROM_A_MOVE and not _the_person_moved(text[:match.start()]):
                # "my cousin moved to preston from bolton" is where her family is from, not
                # where they are from: the move has to be the person's own.
                continue
            phrase = match.group(1)
            if pattern is FROM_GROWN and not _grown_up_in_a_place(phrase, text):
                continue
            name = _place_name(phrase)
            if not name:
                continue
            if re.search(r"\bborn\s+in\b", match.group(0), re.I):
                born.append((match.start(), name))
            else:
                said.append((match.start(), name))
    if said:  # where they say they are from, or grew up, is the answer; being born is only a hint
        return max(said)[1]
    if not born:
        return None
    return max(born)[1]


# A home they live in beside another place is said with the home in front of it: "i live in a
# small village near york". York is the place that answered "where do i live" before, and it is
# not where they live; the village is. The home is kept in the words they said it in - "You live
# in a small village near York" reads right - so the place they gave is neither denied ("You
# haven't told me where you live") nor named as somewhere it is not ("You live in York").
A_HOME_BEFORE = re.compile(
    r"\b(?:a|an|the|my|our|their|his|her|this|that)\s+[a-z][a-z'-]*"
    r"(?:\s+[a-z][a-z'-]*){0,2}\s+(?:near|outside|round|close to|next to|by)\s+$", re.I)


def _places(text):
    """Places the line named, and the one they live in if it says where that is."""
    places = []
    home = None
    home_said = ""
    # The place named behind a dwelling is the place they live, so it is read first: "we live in a
    # flat in manchester" is Manchester and not the flat.
    for pattern in (HOME_DWELL, HOME_PLACE):
        for match in pattern.finditer(text):
            # A two-word place ends at the first word that is not part of a name: "leeds and work
            # in york" is Leeds, "preston last year" is Preston, "staying in tonight" is nothing.
            word = _place_name(match.group("place"))
            if not word:
                continue
            if not any(word.lower() == p.lower() for p in places):
                places.append(word)
            # A stay is a visit, and a move with a date still to come is not where they live yet:
            # both name a place without being home ("we're moving to york next month").
            ahead = match.group("planned") and FUTURE.search(text)
            if home is None and not match.group("stay") and not ahead:
                home = word
                # "i live in a small village near york" is a village near York, and the place is
                # what they said it with: the home is kept as "a small village near York".
                said_with = A_HOME_BEFORE.search(text[:match.start("place")])
                if said_with:
                    home_said = " ".join(said_with.group(0).split()) + " " + word
            break
        if home:
            break
    if home is None:
        for match in A_MOVE_FROM_THEN_TO.finditer(text):
            if not _the_person_moved(text[:match.start()]):
                continue
            word = _place_name(match.group("place"))
            if not word:
                continue
            if not any(word.lower() == p.lower() for p in places):
                places.append(word)
            # "we're moving from york to bristol next month" is a move still to come, so the
            # destination is a place they named and not where they live yet.
            if not FUTURE.search(text):
                home = word
            break
    for match in PLACE_AFTER.finditer(text):
        word = match.group(1)
        first = word.split()[0].lower()
        if first in NOT_PLACES or word.lower() in NOT_PLACES:
            continue
        # A capital is no proof on its own when the word is also one of the language's: "going to
        # Port my number" was filed as a place called Port, and the store then said "You're going
        # to Port your number." The same reader and the same guard as one typed in lower case.
        if first in PLACE_MIDDLE:
            pair = " ".join(text[match.start(1):].split()[:2])
            word = _place_name(pair)
            if not word:
                continue
        if word not in places:
            places.append(word)
    for match in PLACE_LOWER_NAMED.finditer(text):
        if _an_everyday_word(match.group(2)):
            continue  # "great lengths", "new heights": the second word is not part of a name
        word = _place_name(match.group(1) + " " + match.group(2))
        if word and not any(word.lower() == p.lower() for p in places):
            places.append(word)
    for match in PLACE_LOWER.finditer(text):
        word = _finish(match.group(1))
        low = word.lower()
        if not word or low in NOT_PLACES or low in PLACE_VERBS:
            continue
        if low in PLACE_MIDDLE:
            continue  # "going to port" and "off to saint" name no place until the name follows
        if word[:1].isupper() and word in places:
            continue
        # "im going to sri lanka in june" is Sri Lanka and not Sri as well: the first word of a
        # name is not a place of its own once the name is on the list.
        if any(p.lower().startswith(low + " ") for p in places):
            continue
        if not any(word.lower() == p.lower() for p in places):
            places.append(word[:1].upper() + word[1:])
    if not places and SHORT_LIST.match(text.strip()):
        for word in re.findall(r"[A-Z][a-z]+", text):
            if word.lower() not in NOT_PLACES and word not in places:
                places.append(word)
    return places, home, home_said


# How much of a thing there is, where a diet record would want which thing: see NO_MEAT below.
_QUANTITY_WORDS = frozenset("""enough much many any more less too little lots plenty loads
loads""".split())
ALLERGY_STOP = frozenset("""i we he she they it you have has had got also but so because
which and the a an my our his her their anything something everything much many most
lot food stuff no not few several some any real bad serious""".split())

# ---------------------------------------------------------------------------
# who a fact is about

# A relation or a flatmate: "my son is allergic to nuts" is a fact about the son, not the user.
OTHER_NOUNS = ("son", "daughter", "child", "children", "kid", "baby", "girl", "boy",
               "youngest", "eldest", "oldest", "husband", "wife",
               "partner",
               "boyfriend", "girlfriend", "fiance", "fiancee", "mum", "mom", "mother",
               "stepmum", "stepdad", "dad", "father", "sister", "brother", "friend",
               "mate", "colleague", "coworker", "boss", "flatmate", "housemate",
               "nephew", "niece", "grandma", "grandad", "granny", "nana", "grandpa",
               "aunt", "uncle", "cousin", "neighbour", "neighbor", "dog", "cat", "pet")
# A relation the bot already knows by name is somebody else, and this list has to know every one
# of them: "nan", "gran", "grandmother" and "grandson" are in RELATIONS and were missing here,
# so "my nan is allergic to nuts" named no relation at all and the allergy was filed as the
# user's own - the bot then warned the person about an allergy they never said they had, and the
# nan's went in the bin. The relations are added rather than retyped, so a relation added to the
# vocabulary is somebody else everywhere at once. Longest first, so "mother in law" is read as
# the two words it is before the "mother" inside it.
OTHER_NOUNS = OTHER_NOUNS + tuple(sorted((word for word in RELATIONS
                                          if word not in OTHER_NOUNS), key=len, reverse=True)) \
    + ("twin",)

CLAUSE_BREAK = re.compile(r"[.!?;]|\b(?:but|so|because|which|although|though|while)\b", re.I)
# A yes/no question puts the verb in front of the person: "is she vegan", "am i allergic to nuts",
# "do i live in leeds". The word order is the whole test - a statement never opens on the verb, so
# "my mum is vegan, is that a problem?" still says what it says.
QUESTION_OPEN = re.compile(
    r"^(?:(?:and|but|so|then|also|oh|ok|okay|well|now|hey|sorry|please|quick|hi)\s+)*"
    r"(?:is|isnt|are|arent|was|wasnt|were|werent|am|do|dont|does|doesnt|did|didnt|has|hasnt|"
    r"have|havent|had|can|cant|could|couldnt|would|wouldnt|will|wont|shall|should|shouldnt)\b",
    re.I)
# The clauses a line runs on into; a fact stated after one of these is a statement even when the
# line opened with a question ("can i eat nuts if im allergic to peanuts" states the allergy).
CLAUSE_JOIN = re.compile(r"\b(?:if|because|since|though|although|when|whenever|and|but|so)\b|[,;]",
                         re.I)


def stated_not_asked(text):
    """The part of a yes/no question that states something, or "" when it only asks.

    A question about somebody states nothing about them, and the readers below file what they
    find as a fact about that person: "is she vegan" after "my mum is called ann" filed a vegan
    diet against the mum and the store then answered the question as if it were a fact ("Your mum
    is vegan."). The ask is dropped and only the clauses that state something are read.
    """
    said = " ".join(str(text or "").strip().split())
    if not said or not QUESTION_OPEN.match(said):
        return said
    kept = [part.strip(" ,.;:!?") for part in CLAUSE_JOIN.split(said)]
    kept = [part for part in kept if part and not QUESTION_OPEN.match(part)]
    return ", ".join(kept)

# The pronoun a clause is about, read the same way `SUBJECT` reads it, for a clause that names no
# relation at all: "she is 70 next month" is somebody's birthday and the line never says whose.
PRONOUN_SUBJECT = re.compile(r"\b(?P<pron>he|she|they|him|them|hes|shes|theyre|her)\b", re.I)

# Every way a clause can name its subject; the last one before the fact is the one that owns it.
SUBJECT = re.compile(
    # The plural belongs to the whole list, not to its last word: written inside the group
    # ("...|kid|pet)s?") the "s?" only ever matched "pets", so "my sons" and "my mums" matched
    # no person at all and the clause fell through to the "my" below - the son's allergy was
    # filed as the user's own.
    r"\b(?:my|our|his|her|their|the)\s+" + MODIFIER_BEFORE + r"(?P<rel>"
    + "|".join(OTHER_NOUNS) + r")"
    # "my mother in law", "our brothers in law": the two words after the relation are part of
    # who this is. Cut to "mother", every reply said "Your mother is vegetarian" about someone
    # the person had just called their mother in law. The plural belongs to the whole phrase:
    # "my sons" and "my mums" are a person each, so the "s?" sits after the "in law".
    r"(?P<inlaw>\s+in\s+laws?)?s?\b"
    # People type the pronoun with the apostrophe left off, and "shes"/"hes" is not the
    # word "she"/"he" to a word boundary: without these the clause named no subject and the
    # fact fell to the user - "shes allergic to nuts" was filed as the user's own allergy.
    r"|\b(?P<pron>he|she|they|him|them|his|their|hes|shes|theyre|theyve)\b"
    r"|\b(?P<her>her)\b"
    r"|\b(?P<user>i'm|im|i am|i've|ive|i|me|mine|my|my own|we're|we are|we've|we|us|our)\b",
    re.I)


# The person is one of the people the clause is about: "me and my husband", "my wife and i",
# "us and the kids". The relation alone would file the thing against somebody else.
A_ME_WITH_SOMEONE = re.compile(
    r"\b(?:me|us|we|i)\b[^.!?]{0,24}\b(?:and|,|&)\b[^.!?]{0,24}\b(?:my|our)\s+\w+"
    r"|\b(?:my|our)\s+\w+[^.!?]{0,24}\b(?:and|,|&)\b[^.!?]{0,12}\b(?:me|us|i)\b", re.I)


def _the_person_is_in_it(clause):
    """Whether the clause says the thing is about the person as well as somebody else."""
    return bool(A_ME_WITH_SOMEONE.search(clause))


def subject(text, pos):
    """Who the clause that ends at pos is about: (kind, who).

    kind is "user", "other", or "" when the line never says; who is the person named
    ("son", "husband"), or "" for a bare pronoun. "I'm allergic to nuts" is the user's,
    "my son is allergic to nuts" and "he's allergic to nuts" are not: a fact belongs to the
    person it is about, and only the first can be recalled as something the user told us
    about themselves.
    """
    start = 0
    for match in CLAUSE_BREAK.finditer(text, 0, pos):
        start = match.end()
    clause = text[start:pos]
    kind, who = "", ""
    for match in SUBJECT.finditer(clause):
        if match.group("rel"):
            kind = "other"
            who = " ".join((match.group("rel") + (match.group("inlaw") or "")).split()).lower()
            who = SPOKEN_RELATION.get(who, who)
        elif match.group("pron") or match.group("her"):
            kind, who = "other", ""
        else:
            kind, who = "user", ""
    if kind == "other" and who and _the_person_is_in_it(clause):
        # "its for me and my husband, four days": the relation is the last person the clause names,
        # so the length was filed against the husband and not kept at all - the chat then answered
        # "and how many days was it again" from its own memory of a "few days" said before. A
        # thing said about "me and my husband" is about both of them, and the person is one of
        # the two.
        kind = "user"
    if kind == "other" and who:
        # A pair of people is one person, and the clause's own words say which: "my partners mum is
        # allergic to shellfish" read the first relation as the subject and filed the allergy
        # against the partner, who is the person the line did not say it about. The pair wins only
        # when the word the clause named is the pair's first word, so "my mums car" and "my sister
        # and my mum are coeliac" are untouched.
        pair = a_chained_person(clause)
        if pair and pair.split("'s ")[0] == who:
            who = pair
    if kind == "":
        # Nobody in the clause said "my" or "i", so the person in it is the one the words name:
        # a relation word on its own ("mum is allergic to shellfish") or a name ("tom is
        # allergic to nuts"). Before this they were both read as the user, and the bot told the
        # person about somebody else's allergy as if it were their own.
        bare_who, bare_name = _the_person_without_a_relation(clause)
        if bare_who or bare_name:
            kind, who = "other", bare_who
            # A bare relation can head a pair the same way "my" can: "mum and dad are allergic to
            # nuts" is one couple in the store the way "my mum and dad" is.
            pair = a_chained_person(clause)
            if pair and pair.split("'s ")[0] == who:
                who = pair
    return kind, who


# The person a clause names without the "my" in front of them, or by name alone: "mum is
# allergic to shellfish" is the mum's allergy and "tom is allergic to nuts" is Tom's, and both
# were filed as the user's own, so the store told the person about an allergy they never said they
# had, and the mum's or Tom's went in the bin. The word has to be the last thing before the fact,
# which is where a subject stands, and a bare name has to be the whole clause, so a line about a
# thing ("the boiler is broken") is not read as somebody called Boiler.
BARE_RELATION = re.compile(
    r"\b(?P<rel>" + "|".join(sorted(OTHER_NOUNS, key=len, reverse=True)) + r")"
    r"(?P<inlaw>\s+in\s+laws?)?s?$", re.I)
# Words that fill the place in front of a fact without naming anybody: the softeners people open
# a line with, and the grammar words a subject is never made of.
NOT_A_PERSON_WORD = frozenset("""
and but so then also oh ok okay well now anyway actually quick just plus hey hi sorry right yeah yes
today tonight tomorrow yesterday here there this that these those it its he she they them their his
her him i im ive me my mine we us our ours you your yours who what which the a an some any no not
dont doesnt didnt is are was were be been am do does did have has had can could would should will
shall may might must of to for from in on at by with about time day week month year morning
evening night thing things something anything nothing everything someone anyone everyone nobody
help thanks please get got go going come coming done""".split())


# The words between a person and the fact said of them: "mum is", "tom has", "sarah cant". The
# clause the readers hand over ends at the fact, so what is left in front of it is the person once
# these are taken off the end.
BETWEEN_PERSON_AND_FACT = frozenset("""
is are was were be been being am has have had isnt arent wasnt werent hasnt havent hadnt
s does do did doesnt dont didnt can cant cannot could couldnt may might must shall should
shouldnt will wont would wouldnt get gets got become becomes became
""".split())
# The words in front of a person that mean the clause is not naming them the bare way: "the
# boiler is broken" has "the" in it and no person, and neither does "my son is 4".
NOT_A_BARE_PERSON_AHEAD = frozenset("""
my our his her their your its the a an this that these those some any every no each
""".split())
# A pronoun with its verb written on is not a name: "i'm allergic to nuts" is the person typing
# and "shes got a nut allergy" is the woman they were talking about, and read as names the two
# lines lost the fact and filed it on somebody called Im and somebody called Shes.
A_PRONOUN_NOT_A_NAME = frozenset("""
im ive id ill ima youve youre youd youll hes shes its itd its were weve wed well theyre theyve
theyd theyll thats whats theres heres isnt arent wasnt werent hasnt havent hadnt doesnt dont didnt
cant couldnt wouldnt shouldnt wont mustnt aint lets
""".split())


def _a_person_word(word):
    """A word the way a person says it, so "i'm", "im" and "I’m" are one word."""
    return str(word or "").strip().strip(".,!?;:\"'").lower().replace("\u2019", "'").replace("'", "")


def _the_person_without_a_relation(clause):
    """(who, name) for a person the clause names without a "my": ("mum", ""), ("", "Tom")."""
    words = [word.strip(" ,.;:!?").strip("'") for word in clause.split()]
    words = [word for word in words if word]
    while words and words[0].lower() in ("and", "but", "so", "then", "also", "oh",
                                        "ok", "okay", "well", "now", "btw"):
        words.pop(0)
    while words and words[-1].lower() in BETWEEN_PERSON_AND_FACT:
        words.pop()
    if not words or len(words) > 3:
        return "", ""
    if any(word.lower() in NOT_A_BARE_PERSON_AHEAD for word in words[:-1]) \
            or words[-1].lower() in NOT_A_BARE_PERSON_AHEAD:
        return "", ""
    said = " ".join(words)
    found = BARE_RELATION.search(said)
    if found:
        who = found.group("rel") + (found.group("inlaw") or "")
        who = " ".join(who.lower().split())
        if who.endswith("s") and who[:-1] in RELATIONS:
            who = who[:-1]
        return SPOKEN_RELATION.get(who, who), ""
    if len(words) == 1:
        word = words[0]
        if _a_person_word(word) in NOT_A_PERSON_WORD or _a_person_word(word) in DIET_GROUP \
                or _a_person_word(word) in RELATIONS or _a_person_word(word) in A_PRONOUN_NOT_A_NAME:
            return "", ""
        if _may_be_a_name(word) and _name_after_a_title(word):
            return "", word
    return "", ""


# Words that end the sentence rather than name a thing: "I'm allergic to nuts, please don't put
# them in the pasta" is an allergy to nuts, and "remind me what I'm allergic to, please" states
# nothing at all.
# The chat-speak at the end of a line is the same set the recall drops (`filler.TAIL_OFF`, which
# is the leaf module so nothing here has to import the store). "im allergic to nuts tbh" is an
# allergy to nuts, and saying "you told me you're allergic to nuts tbh" back puts their shrug in
# the fact; "tho", "ngl" and "innit" do the same to a diet or an allergen.
FILLER_TAIL = frozenset(TAIL_OFF | frozenset("""please again then now though either too also
still yet anyway plus thanks thank sorry ok okay""".split()))


# The tail of a sentence that is about how much rather than about what: "i cant eat dairy at
# all" is dairy, and "i cant eat gluten anymore" is gluten. Two words on their own are not a thing
# anybody is allergic to.
FILLER_TAIL_PHRASES = ("at all", "any more", "anymore", "these days", "whatsoever", "at least",
                       "any longer", "no more", "for years", "since i was little")


def _trim_filler(text):
    words = text.split()
    while True:
        while words and words[-1].strip(".,!?;:'\"").lower() in FILLER_TAIL:
            words.pop()
        tail = " ".join(words[-3:]).strip(".,!?;:'\"").lower()
        cut = next((phrase for phrase in FILLER_TAIL_PHRASES
                    if tail.endswith(phrase)), None)
        if not cut:
            break
        words = " ".join(words).strip(".,!?;:'\"")[:-len(cut)].split()
    return " ".join(words)


# The ask at the end of a line names no allergy: "I'm allergic to peanuts and soya, what can I
# have?" is an allergy to peanuts and soya. A piece that starts with a question word ends the
# list, and so does the piece after it.
QUESTION_START = re.compile(r"^(?:what|which|who|how|when|where|why|can|could|should|would|"
                            r"will|shall|do|does|did|is|are|was|were|any|if)\b")


# What follows "cant eat" without naming a food: "he cant eat at all", "she cant eat much for
# breakfast", "they cant eat properly yet". The allergy reader is right that there is a limit in
# the line, but the words are not one, so nothing is filed and nothing is said back - "Your son
# can't eat at all, good to know" is a sick child answered with a diet.
NOT_A_FOOD = frozenset("""much many more anything everything nothing something all at properly
enough food stuff lot any now yet still anymore here there""".split())

# The generic noun people put after the food they mean: "i cant eat spicy food", "no fried stuff
# for me", "she cant eat dairy things". The word itself says nothing about what they cannot eat,
# so on its own it is not a food ("i cant eat food" names nothing); after a word that does say
# what, the modifier is the food and the noun is how they said it.
A_GENERIC_FOOD = frozenset("""food foods stuff things thing""".split())

def _trim_time_tail(item):
    """The food off the front of a time: "chilli after 6" is chilli, "dairy before work" dairy."""
    words = item.split()
    while len(words) > 1:
        last = words[-1].strip(".,!?;:'\"")
        if last in NOT_A_FOOD_IN_IT or last.isdigit() or last in ("the", "a", "my", "our"):
            words.pop()
        else:
            break
    return " ".join(words)


# A limit can be about when or where someone eats, and then there is no food in the line:
# "i cant eat late at night", "i cant eat before work", "i cant eat at my desk". The allergy
# reader took the words after "cant eat" for the thing, filed "late at night" as an allergy and
# said it back - "You can't eat late at night, good to know" - which is a timing question
# answered as a diet, and it took the turn from the food-timing card that answered it.
NOT_A_FOOD_IN_IT = frozenset("""at in on before after during while when whenever until till
    by from around late early night nights morning mornings afternoon evenings evening
    midnight lunchtime bedtime work school desk shift commute""".split())


def _a_modifier_before_a_generic_noun(words):
    """Whether the thing said is a word that names it plus a generic noun: "spicy food"."""
    if len(words) < 2:
        return False
    if words[-1].strip(".,!?;:'\"").lower() not in A_GENERIC_FOOD:
        return False
    return not set(words[:-1]) & ALLERGY_STOP


def _only_stop_words(item):
    """Whether every word of a piece is one the allergy reader knows is not an allergen."""
    words = item.split()
    return bool(words) and all(word in NOT_A_FOOD or word in ALLERGY_STOP for word in words)


def _allergy_items(chunk):
    """The things in "nuts and shellfish, not peanuts": ["nuts", "shellfish"].

    A "not" in the phrase is a correction, not another allergen: "im allergic to soya not
    peanuts" is soya, and the peanuts it names are the thing being taken back (see `denials`).
    """
    items = []
    chunk = re.split(r"\bnot\b|\b(?:but|so|because|which)\b", chunk)[0]
    for item in re.split(r",| and ", chunk):
        item = _trim_time_tail(_trim_filler(_finish(item)))
        if QUESTION_START.match(item.lower()):
            break
        if not item or len(item) < 2:
            continue
        if (set(item.split()) & ALLERGY_STOP
                and not _a_modifier_before_a_generic_noun(item.split())):
            # "spicy food" has the word "food" in it, which is a stop word, but the limit is the
            # spicy: the generic noun is how they said it, and the word in front is the thing.
            continue
        if item in ("it", "them", "that", "this") or item in items:
            continue
        if (set(item.split()) & NOT_A_FOOD_IN_IT
                and not set(item.split()) & ONE_MORE_FOODS):
            # "late at night" and "before work" say when, not what, so nothing is filed: the line
            # is about when they eat. A food in the piece keeps it ("i cant eat chilli after 6"),
            # because there the words around it only say when.
            continue
        if _only_stop_words(item):
            continue
        items.append(item)
    return items


# The words a line puts in front of the thing it names, which are not part of it.
ONE_MORE_DETERMINERS = frozenset("""the a an my your his her their our this that these those some""".split())
# "sorry, not peanuts" and "actually not nuts" take an item back; they do not add one. The
# negation is in front of the thing itself, so the part is skipped rather than read as the food
# "not peanuts" - which the store then kept, and "is a prawn curry ok" answered against nothing.
NOT_AN_ADDITION = frozenset("""not no dont don't didnt didn't doesnt doesn't scratch forget never
    nor without""".split())


def one_more(text):
    """The one more thing a line names and nothing else: "and milk too" -> ["milk"].

    A follow-up that adds to a fact already on record names the thing and no fact of its own:
    "im allergic to peanuts" then "and milk too", "plus cheese", "i think soya as well".
    Read on its own such a line states nothing (no verb, no subject), which is why the store
    threw it away and the bot could only echo "milk too" back. The lead-in is not part of the
    thing, and neither is the "too"; what is left has to be a food, because nothing in the line
    says what kind of fact is being added to. A line that names anything else ("and my sister
    too", "and work is awful too", "and the weather") comes back empty and states nothing.
    """
    said = " ".join(str(text or "").lower().split())
    if not said:
        return []
    typed = said
    # The lead-in and the tail come off again and again: "oh and also i think maybe milk as
    # well" is the word "milk", and "milk, as well, please" is the word "milk".
    for _ in range(6):
        before = said
        said = ONE_MORE_HEAD.sub("", said).strip(" ,")
        said = ONE_MORE_TAIL.sub("", said).strip(" ,.!?")
        if said == before:
            break
    if not said or said == typed:
        # A line that is only the thing itself ("milk") is an answer to a question, not an
        # addition to what is on record; the store keeps an answer where it asked for one.
        return []
    items = []
    for part in re.split(r",| and | or ", said):
        words = [word.strip("'\u2019") for word in part.split() if word.strip("'\u2019")]
        # A negation in front of the thing is a take-back, not an addition: "sorry, not peanuts"
        # is the peanuts off the list, and nothing else on the line is being added.
        if words and words[0].lower() in NOT_AN_ADDITION:
            continue
        # "and the milk too" is the milk: a determiner in front is how they said it, not the thing.
        while words and words[0] in ONE_MORE_DETERMINERS:
            words = words[1:]
        if not words or len(words) > 2:
            continue
        # A word in front of the food says which one ("tree nuts", "blue cheese"), so the last
        # word is the one that has to be food: "and tree nuts too" holds a thing the list can
        # take, and "and my sister too" does not.
        if words[-1] not in ONE_MORE_FOODS:
            continue
        head, last = " ".join(words[:-1]), ALLERGEN_PLURALS.get(words[-1], words[-1])
        item = (head + " " + last).strip()
        if item not in items:
            items.append(item)
    return items


# The lead-ins a person puts in front of sharing a limit: "oh me too", "yeah, im too as well".
SHARE_LEAD = r"(?:(?:oh|yeah|yes|and|haha|honestly|sorry|actually)[\s,]+)*"
# The person talking says the limit just said of somebody else is theirs too. The whole line is
# this shape and nothing else, so "me too" after a pizza is a taste (bot/modules/chat.py) and the
# store only reads it when the turn before filed a limit.
I_SHARE_IT = re.compile(
    r"^\W*" + SHARE_LEAD + r"(?:"
    r"im|i'm|i am|me|i"
    r")\s*(?:"
    r"too|also|as well|aswell|the same|same|not alone|"
    r"have (?:it|that|this|the same)(?: too| as well)?|"
    r"do too|am too|"
    # the same said with the verb the limit itself was said with: "i dont either" after "my mum
    # cant eat gluten", "i can too" after "my son can eat nuts again".
    r"dont either|don't either|cant either|can't either|couldnt either|couldn't either|"
    r"havent either|haven't either|can too|could too|do as well|am as well"
    r")\W*$", re.I)
# The same said without a subject: "same here", "so am i", "same as him".
I_SHARE_IT_SHORT = re.compile(
    r"^\W*" + SHARE_LEAD + r"(?:"
    r"same here|same for me|same for us|same|same as (?:me|him|her|them|that|my [a-z]+)|me neither|"
    # The one word that only ever agrees in a chat: "likewise" after "my husband is coeliac" is the
    # user taking the coeliac too. It is read only when the turn before filed a limit, so it stays
    # a plain "you too" after a greeting.
    r"likewise|"
    r"(?:that'?s|this is) me(?: too| as well)?|"
    # "so do i", "neither can i": the verb matches the limit the turn before filed, and the store
    # only reads the line when there was one, so any of them is a share.
    r"so (?:am|do|does|did|have|has|can|could|would) i|"
    r"neither (?:am|do|does|did|have|has|can|could) i|nor (?:am|do|have|can) i"
    r")\W*$", re.I)
# The same share said with the verb first and the relation after it: "so does my brother",
# "neither can my mum". The pronoun forms ("so can he") are not read: after "my wife cant eat
# dairy", "so can he" says the opposite of the limit, so the store keeps out of it.
SOMEONE_SHARES_IT_VERB_FIRST = re.compile(
    r"^\W*" + SHARE_LEAD + r"(?:so|neither|nor)\s+"
    r"(?:does|do|is|are|has|have|can|could|would)\s+(?:my|our)\s+(?P<who>[a-z][a-z'-]{1,14})\W*$",
    re.I)
# Somebody else shares it: "my son is too", "my wife as well", "my mum has it too".
SOMEONE_SHARES_IT = re.compile(
    r"^\W*" + SHARE_LEAD + r"(?:my|our)\s+(?P<who>[a-z][a-z'-]{1,14})\s+"
    r"(?:is|are|does|do|has|have|gets|got|wants)?\s*(?:too|also|as well|aswell|the same|same|"
    r"it too|that too|one too)\W*$", re.I)
# The same with a pronoun, which is the last person the chat named: "she is too", "he has it too".
SOMEONE_SHARES_IT_PRONOUN = re.compile(
    r"^\W*" + SHARE_LEAD + r"(?:he|she|they)\s+"
    r"(?:is|are|does|do|has|have)?\s*(?:too|also|as well|aswell|the same|same|it too|that too)\W*$",
    re.I)
# The word the reader gives back when the line shares it but names nobody: the last person named.
LAST_PERSON = "@last"


def the_limit_they_share(text):
    """"im too", "my son is too": the limit just said is theirs as well, and who "theirs" is.

    A limit said of one person is often shared by the next line, and the line says nothing on its
    own: "my son is allergic to nuts" then "im too" was answered "Glad to hear it." - a happy nod
    at an allergy, with nothing filed - and the reverse "im allergic to nuts" then "my son is too"
    was only echoed back. Both lines mean the same fact said of the other person, so they are
    read here as who the limit belongs to: the person talking ("i"), the relation they named
    ("son"), or the last person the chat named (@last).

    What the line shares is the limit on record, which is the store's question, not this one: a
    line read here that has no limit to share files nothing. Nothing else is a share, so "i love
    pizza" then "me too" stays a taste and "my son is 6" then "im too" is not an age.
    """
    said = " ".join(str(text or "").lower().split()).strip(" !.,")
    if not said or len(said.split()) > 6:
        return ""
    if I_SHARE_IT.match(said) or I_SHARE_IT_SHORT.match(said):
        return "i"
    found = SOMEONE_SHARES_IT.match(said) or SOMEONE_SHARES_IT_VERB_FIRST.match(said)
    if found:
        who = found.group("who").strip()
        # "my own too" and "my self too" name nobody else.
        return "" if who in ("own", "self") else who
    if SOMEONE_SHARES_IT_PRONOUN.match(said):
        return LAST_PERSON
    return ""


def denied_before(text, start):
    """Whether the words at `start` are said not to be true: "im not allergic to nuts"."""
    return bool(DENIAL_WORDS.search(str(text or "")[max(0, start - 40):start]))


def _clause(text, start):
    """The words before the fact at `start`, from the nearest clause edge."""
    head = text[:start]
    cut = 0
    for edge in CLAUSE_EDGE.finditer(head):
        cut = edge.end()
    return head[cut:]


def _the_clause_before(text, start, edges=4):
    """The clause before the fact at `start`, with the clause it continues put back.

    A list drops the subject: "my brother has a son and a daughter" is one clause with two
    relations in it, and read on its own the second one looks like the person's own. So the
    clause is read back to the nearest one that opens with a subject - "and i have a son" is
    its own clause and stops the walk.
    """
    parts, last = [], 0
    head = text[:start]
    for edge in CLAUSE_EDGE.finditer(head):
        parts.append(head[last:edge.end()])
        last = edge.end()
    parts.append(head[last:])
    said, walked = parts[-1], 0
    # The walk stops at the first part as well as at a subject: `parts[-1 - walked]` was read
    # one part too far back on a line whose only edge left a clause that opens with no subject -
    # "and for my dad", "and some for my sister" - and the reader raised IndexError instead of
    # reading the line, so the relation the follow-up named was never filed and every reader of
    # the line died with it: nothing was proposed at all and the person got "Hello!" back.
    while (walked + 1 < len(parts) and walked < edges
           and not _opens_a_subject(parts[-1 - walked])):
        walked += 1
        said = parts[-1 - walked] + said
    return said


def _opens_a_subject(clause):
    """Whether this clause starts by naming who it is about."""
    words = str(clause or "").replace(",", " ").split()
    if not words:
        return False
    return re.sub(r"[^a-z']", "", words[0].lower()) in ANY_SUBJECT


def _around(text, start):
    """The whole clause the words at `start` sit in, from one edge to the next."""
    left = 0
    for edge in CLAUSE_EDGE.finditer(text[:start]):
        left = edge.end()
    right = len(text)
    edge = CLAUSE_EDGE.search(text, start)
    if edge:
        right = edge.start()
    return text[left:right]


def _own_named(text, start, own):
    """The animals the store holds whose name the line has said before `start`.

    "rex died last month" names no animal kind at all - only the name the person gave it - so
    the store's own pet list is the only thing that can hear it. A name counts only when the
    line says it, and it is matched whole, so "rex" does not fire on "rexy".
    """
    found = []
    lowered = text.lower()
    for pet in own or []:
        name = str((pet or {}).get("name") or "").strip().lower()
        animal = str((pet or {}).get("animal") or "").strip().lower()
        if not name or not animal or len(name) < 3:
            continue
        match = re.search(r"\b" + re.escape(name) + r"\b", lowered[:start])
        if match:
            found.append(animal)
    return list(dict.fromkeys(found))


def _own_in_denial(text, own):
    """The store's pets the line says are gone by name, when it named no animal kind.

    "we dont have rex any more" names no animal, only the name, so the store's own list is what
    hears it. Only a name the line puts behind a possession denial counts, and what comes back is
    that one record rather than its animal kind: "we gave fred away" from someone with Milly and
    Fred takes Fred alone, where the kind took both cats off the store.
    """
    gone = []
    for pet in own or []:
        name = str((pet or {}).get("name") or "").strip()
        animal = str((pet or {}).get("animal") or "").strip().lower()
        if not name or not animal or len(name) < 3:
            continue
        for match in re.finditer(r"\b" + re.escape(name) + r"\b", str(text or ""), re.I):
            if not_had(text, match.start()):
                if pet not in gone:
                    gone.append(dict(pet))
                break
    return gone


# A line takes one animal out of a set only when it says something happened to it: "we gave one
# away", "one of them died". "one of them is ill" and "one of them is ginger" are about a pet that
# is still in the house, so the count must not move.
ONE_TAKEN = re.compile(r"\b(?:gave|give|giving|given|gives|rehom(?:e|ed|es|ing)|took|taken|sold|"
                       r"got rid of|went to|passed (?:away|on)|died|lost|left)\b", re.I)
DIY_OF_ALL = re.compile(r"\bone\s+of\s", re.I)
ONE_OF_THEM = re.compile(r"\b(?:one|1)\s+of\s+(?:them|those|the\s+\w+s|our\s+\w+s|my\s+\w+s)\b|"
                         r"\b(?:gave|give|giving|given|rehom(?:e|ed|es|ing)|took|taken|got rid of)\b"
                         r"[^.;!?]{0,20}?\bone\b", re.I)


def given_away_one(text, own=None):
    """The one animal a line gives away without saying which, out of a set on the store.

    "i have two cats" then "we gave one away" leaves one cat, and the store used to keep the
    count at two and answer "You've got two cats." What comes back is the record to take one
    from, and only when the line names no animal of its own: "we gave the cat away" is the
    whole kind, and `denials` has it.
    """
    said = str(text or "")
    if not ONE_OF_THEM.search(said) or not ONE_TAKEN.search(said):
        return []
    kinds = {}
    for pet in own or []:
        if not isinstance(pet, dict):
            continue
        animal = str(pet.get("animal") or "").strip().lower()
        if not animal or (pet.get("count") or 1) < 2:
            continue
        kinds.setdefault(animal, pet)
    if len(kinds) != 1:
        return []
    return [dict(next(iter(kinds.values())))]


def _pointed_at(text, start, plural):
    """The animals a pronoun at `start` can be pointing at: the ones the line named first.

    "my dog is called rex and my cat is milly, we dont have them any more" names two, so a
    plural takes both and a singular takes the nearest: "we dont have him any more" is about
    the cat when the cat was the last animal named. Nothing is guessed when the line never
    named an animal at all.
    """
    named = [match.group(1).lower() for match in PETS.finditer(text[:start])]
    named = list(dict.fromkeys(named))
    if not named:
        return []
    return named if plural else named[-1:]


def not_had(text, start):
    """True when the line says the pet at `start` is not, or no longer, theirs.

    Only possession counts. "i dont have a cat" takes the cat back; "i dont like my cat today"
    and "i dont want a dog" are about how they feel about it, not about what lives in the house,
    and nothing later puts a pet back, so the narrow reading is the safe one.
    """
    clause = _clause(text, start)
    if HEDGE.search(clause):
        return False
    # `_have_none` is given the animal as well as the words before it: the shape it reads is
    # "have no dog", and the animal is the word `_clause` stops at.
    if (NOT_HAVE_LONGER.search(clause) or _have_none(clause + " " + text[start:])
            or WITHOUT_ANIMAL.search(clause)
            or NOT_JUST.search(clause) or taken_back_before(text, start)):
        return True
    return any(match.start() <= start <= match.end() for match in GIVEN_AWAY.finditer(text))


def _have_none(clause):
    """Whether the clause says the animal is not theirs, read without a bare verb deciding it.

    "i have got no dog" and "we have no pets now" name the animal as the thing that is gone, so
    they are the take-back `NOT_HAVE` takes them for. "he has never liked it" names no animal
    after the negation at all, and "he has no dog friends" names one that is not the dog: both
    are things the person is saying about the animal, and neither makes it stop being theirs.
    """
    for match in HAVE_NONE.finditer(clause):
        if A_COMPOUND_AFTER.match(clause[match.end():]):
            continue
        return True
    return False


def taken_back_before(text, start):
    """True when the words in front of the animal take it back, read with the whole line.

    "forget the dog" is a take-back - nothing says "have", so the animal is not one they have.
    "never mind the dog" and "ignore the dog" are not: they ask the chat to move on and leave
    the animal where it was, and a store that read them as a take-back deleted a dog the person
    still had. A bare "no" counts only when the animal ends the line - "no dog" - because "no
    dogs allowed in my flat" is a rule about the flat and "no dog food in the house" is about
    the food.
    """
    said = str(text or "")
    clause = _clause(said, start)
    if HEDGE.search(clause):
        return False
    if TAKEN_BACK_BEFORE.search(clause):
        return True
    animal = PETS.match(said, start)
    rest = said[animal.end():] if animal else said[start:]
    if NO_THEN_A_THING.match(clause):
        # "no a cat": the "no" is the correction talking and the animal is the one they mean.
        return False
    return bool(BARE_NO.match(clause)) and not rest.strip(" .,!?;:")


def denials(text, own=None):
    """The facts a line says the person does *not* have, in the shape extract() keeps them.

    "im not coeliac" after "im coeliac", "i'm no longer vegetarian": the store can only stop
    planning around a thing if it hears which thing is being taken back. A pet goes the same way,
    but only on possession - see `not_had`. `own` is the pets the store already holds, so a
    take-back can name the animal by the name the person gave it. A denial about somebody else
    comes back under "theirs" (a list of {"who", "allergies"}), because it takes the item off
    that person's list rather than the user's.
    """
    said = str(text or "")
    denied = {}
    # A take-back about somebody else: "he isnt allergic to nuts" one line after "my son is
    # allergic to nuts" is the same denial, and the store can only stop cooking around it if it
    # hears whose list the nuts are coming off. Kept under "theirs", which is no fact key: the
    # store takes each item off the record it holds for that person and says so.
    for match in ALLERGY.finditer(said):
        if not denied_before(said, match.start()):
            continue
        kind, who = subject(said, match.start())
        if kind != "other":
            continue
        person = _a_person(said, match.end(), who)
        items = [ALLERGEN_PLURALS.get(item, item) for item in _allergy_items(match.group(1))]
        if not person or not items:
            continue
        entry = next((seen for seen in denied.setdefault("theirs", [])
                      if _same_person(seen, person)), None)
        if entry is None:
            entry = dict(person, allergies=[])
            denied["theirs"].append(entry)
        entry["allergies"].extend(item for item in items if item not in entry["allergies"])
    for match in CONTRAST.finditer(said):
        items = _allergy_items(match.group("old"))
        for item in items:
            name = ALLERGEN_PLURALS.get(item, item)
            if name not in denied.setdefault("allergies", []):
                denied["allergies"].append(name)
    for match in DENIAL_OF.finditer(said):
        if match.group("food"):
            items = _allergy_items(re.sub(r"^allergic to\s+", "", match.group("food"), flags=re.I))
            if items:
                denied.setdefault("allergies", []).extend(
                    item for item in items if item not in denied.get("allergies", []))
            continue
        if match.group("condition"):
            denied["condition"] = match.group("condition").lower()
            continue
        if match.group("diet"):
            denied["diet"] = DIET_NAMES.get(match.group("diet").lower(), match.group("diet").lower())
    for match in DIET_OFF.finditer(said):
        plan = next((match.group(name) for name in ("plan", "off", "gone", "quit")
                     if match.group(name)), "")
        if not plan:
            continue
        plan = "-".join(plan.lower().replace("-", " ").split())
        # "im on a diet" is kept as "on a diet": the take-back has to be the value the store
        # holds, or `forget` finds nothing to take out.
        denied["diet"] = DIET_NAMES.get(plan, "on a diet" if plan.startswith("diet") else plan)
    for match in DIET_BACK.finditer(said):
        food = _the_food_named(match.group("back") or match.group("eat") or "")
        if food:
            denied["diet"] = food
    if NO_PETS.search(said):
        denied["pets"] = [EVERYTHING]
    animals = []
    others = _someone_elses(said)
    for match in PETS.finditer(said):
        if not not_had(said, match.start()):
            continue
        if any(start <= match.start() < stop for start, stop in others):
            continue  # someone else's pet is not the user's to take back
        animal = match.group(1).lower()
        if animal not in animals:
            animals.append(animal)
    if not animals:
        # "we dont have him any more": the animal is a pronoun, and the line named it earlier.
        for match in PET_PRONOUN.finditer(said):
            if not not_had(said, match.start()):
                continue
            pointed = _the_one_they_have(said, match, own)
            if not pointed and not _names_a_relative(said):
                pointed = _only_pet(own)
            for animal in pointed:
                if animal not in animals:
                    animals.append(animal)
            break
    if not animals:
        animals = _own_in_denial(said, own)
    if animals and denied.get("pets") != [EVERYTHING]:
        denied["pets"] = _merge_pets(denied.get("pets", []), _one_of_several(animals, said, own))
    return denied


def their_back(text):
    """A line that puts back what somebody else does not eat or does not like, if it says so.

    "my son doesnt eat fish" then "actually he eats fish", "my wife hates mushrooms" then
    "actually she loves mushrooms": the second line is the person correcting the first, and the
    store went on answering "what does my son eat" with "Your son doesn't eat fish." What it
    reads is what the line says the person does now - [{"who": "son", "pronoun": "", "kind":
    "diet", "food": "fish"}] - and whether anything is on that person's record for the line to
    lift is the store's question, because "he eats fish" on its own is a sentence about the
    world that nobody asked to keep. "them"/"it"/"that" is kept as the pointing word it is: the
    store knows the one thing on that person's record it points at.
    """
    said = str(text or "")
    marked = bool(A_CORRECTION.search(said))
    found = []
    for match in THEIR_BACK.finditer(said):
        if not marked and not match.group("emph"):
            continue  # "my son eats fish" is a sentence about the world, not a correction
        if A_NEGATOR_IN_BETWEEN.search(match.group("gap") or ""):
            continue  # "he doesnt eat fish now" keeps the restriction, it does not lift it
        verb = (match.group("emph") or match.group("verb") or "").lower()
        if not verb:
            continue
        kind = "diet" if verb.startswith("eat") or verb in ("does", "do", "did") else "taste"
        food = " ".join((match.group("food") or "").lower().split())
        if not food:
            continue
        subj = " ".join((match.group("subj") or "").lower().split())
        named = subj.startswith(("my ", "his ", "her ", "their ", "our "))
        found.append({"who": subj.split()[-1] if named else "",
                      "pronoun": "" if named else subj,
                      "kind": kind, "food": food})
    return found


ALL_OF_THEM = re.compile(r"\b(?:both|all|the\s+\w+s|my\s+\w+s|our\s+\w+s)\b", re.I)


def _one_of_several(animals, said, own):
    """A kind word takes one animal when the store holds several: "we gave the cat away".

    Only the whole set is taken by a plural or by "both": "we gave the cats away", "both cats
    went to my mum". Saying "my cat" with two cats on the store that shows one cat, so one goes.

    The several can be one record with a count on it ("i have two cats" is one record, count 2)
    as well as two named records, so the count is what decides, not how many records there are:
    otherwise "we gave the cat away" left nobody with a cat and the store answered "Right - no
    cat, then." to somebody who still had one.
    """
    # "one of the cats" is one animal, so it cancels the plural reading the word itself gives.
    one_of = bool(ONE_OF_THEM.search(said))
    whole = bool(ALL_OF_THEM.search(said)
                 or re.search(r"\b(?:them|those|these)\b", said, re.I)) and not one_of
    out = []
    for animal in animals:
        if not isinstance(animal, str):
            out.append(animal)
            continue
        same = [pet for pet in (own or []) if isinstance(pet, dict)
                and str(pet.get("animal") or "").strip().lower() == animal]
        held = sum(int(pet.get("count") or 1) for pet in same)
        plural = whole or (bool(re.search(r"\b" + re.escape(animal) + r"s\b", said, re.I))
                           and not one_of)
        if held > 1 and not plural:
            out.append(dict(same[-1]))
        else:
            out.append(animal)
    return out


def _merge_pets(had, more):
    """The take-backs of one line, without saying the same one twice.

    A species word ("cat") takes every cat they have; a record takes that one animal; so the two
    kinds do not dedupe against each other and are kept apart.
    """
    out = list(had or [])
    words = {str(item).strip().lower() for item in out if not isinstance(item, dict)}
    records = [item for item in out if isinstance(item, dict)]
    for item in more or []:
        if isinstance(item, dict):
            if item not in records:
                records.append(item)
        elif str(item).strip().lower() not in words:
            words.add(str(item).strip().lower())
            out.append(item)
    return [item for item in out if not isinstance(item, dict)] and (
        [item for item in out if not isinstance(item, dict)] + records) or records


def _the_one_they_have(said, match, own):
    """The animal a bare "him"/"her" points at: one the line already named, or one the store holds.

    "rex died last month, we dont have him any more" is about Rex, and the store's own list is
    what hears a name. A plural takes them all. With nothing to point at this returns nothing;
    `_only_pet` is the fallback and the caller decides whether it is safe.
    """
    return (_pointed_at(said, match.start(), match.group("pron").lower() in PLURAL_PRONOUN)
            or _own_named(said, match.start(), own) or [])


def _only_pet(own):
    """The one animal the store holds, when it holds exactly one."""
    held = [str((pet or {}).get("animal") or "").strip().lower() for pet in (own or [])]
    held = [animal for animal in dict.fromkeys(held) if animal]
    return held if len(held) == 1 else []


def _names_a_relative(said):
    return any(re.search(r"\b" + word + r"\b", said, re.I) for word in RELATIONS)


def _may_be_an_animal(said, match, own=None, said_before=None):
    """Whether a bare "he"/"she" is the animal they keep rather than a person.

    "the vet put him to sleep" is about a pet; "my dad was ill and he died" is not, and taking a
    living pet off the store because a person died is the worst thing this reader could do. So an
    "it" is taken, and a "he"/"she" when the words around it are about putting an animal to sleep
    with no relative anywhere in the line. A plain "he died" is the animal only when the turn
    before it named an animal and no person: "i have a dog" then "he died" is the dog, where "my
    grandad was ill" then "he died" is the grandad, and a bare "he died" with no turn behind it
    says too little to take a living animal off the store.
    """
    if match.group("pron").lower() in ("it", "them", "those", "they"):
        return True
    if _names_a_relative(said) or PEOPLE_WORD.search(said):
        return False
    if ANIMAL_DEATH.search(_around(said, match.start())):
        return True
    before = str(said_before or "")
    if not before or PEOPLE_WORD.search(before) or not PETS.search(before):
        return False  # nothing points at an animal, so "he" is not one
    return bool(_only_pet(own))


def losses(text, own=None, said_before=None):
    """The animals a line says have died, in the shape extract() keeps pets.

    "my cat died last month" is not a take-back to say out loud - the loss is answered by the
    feelings side of the bot, and "Right - no cat, then." is the wrong reply to a bereavement.
    The store still has to hear it, or it hands the animal back later: "what pets do i have"
    after "my cat died" must not answer "You've got a cat called Milly."
    """
    said = str(text or "")
    if not DIED.search(said):
        return []
    animals = []
    others = _someone_elses(said)
    for match in PETS.finditer(said):
        if not DIED.search(_around(said, match.start())):
            continue
        if any(start <= match.start() < stop for start, stop in others):
            continue
        # "my mum's cat died", "the dog next door was put down": somebody else's animal. The
        # sympathy is still theirs to hear, but their own pets stay in the store.
        if _not_their_animal(said, match.start(), match.end()):
            continue
        animal = match.group(1).lower()
        if animal not in animals:
            animals.append(animal)
    if not animals:
        for match in PET_PRONOUN.finditer(said):
            # "put him to sleep" splits around the pronoun, so the clause is read whole
            # rather than only the words before it.
            if not DIED.search(_around(said, match.start())):
                continue
            pointed = _the_one_they_have(said, match, own)
            if not pointed and _may_be_an_animal(said, match, own, said_before):
                pointed = _only_pet(own)
            for animal in pointed:
                if animal not in animals:
                    animals.append(animal)
            break
    if not animals and own:
        for pet in own:
            name = str((pet or {}).get("name") or "").strip().lower()
            animal = str((pet or {}).get("animal") or "").strip().lower()
            if not animal:
                continue
            for match in DIED.finditer(said):
                if HEDGE.search(_clause(said, match.start())):
                    continue
                if name and len(name) >= 3 and re.search(r"\b" + re.escape(name) + r"\b",
                                                         said.lower()):
                    if animal not in animals:
                        animals.append(animal)
    return animals


def _allergies(text):
    """(the user's allergies, the others': [{"who", "allergies"}])."""
    mine, others = [], []
    for pattern in (ALLERGY, CANNOT_EAT, X_ALLERGY):
        for match in pattern.finditer(text):
            if pattern is not CANNOT_EAT and denied_before(text, match.start()):
                continue  # "im not allergic to nuts" is the opposite fact
            if pattern is X_ALLERGY and match.group(1).lower() in NOT_AN_ALLERGEN:
                continue  # "why do we get allergies" names no allergy of theirs
            items = _allergy_items(match.group(1))
            if not items:
                continue
            if pattern is X_ALLERGY:
                items = [ALLERGEN_PLURALS.get(item, item) for item in items]
            kind, who = subject(text, match.start())
            if kind != "other":
                mine.extend(item for item in items if item not in mine)
                continue
            person = _a_person(text, match.end(), who)
            if not person:
                continue  # somebody the line never names and never points at either
            entry = next((seen for seen in others if _same_person(seen, person)), None)
            if entry is None:
                entry = dict(person, allergies=[])
                others.append(entry)
            entry["allergies"].extend(item for item in items if item not in entry["allergies"])
    return mine, others


# A number said of a person other than the user is that person's age: "my son is 7", "my mum is
# 68", "my daughter's 4". The number has to follow the person and the verb, and what follows the
# number has to be the end of what they said about them (a full stop, a comma, "and", "now") or
# the words an age is said with ("years old", "next month", "in june"). Anything else is a unit
# and the number is not an age: "my mum is 68 kilos", "my son is 8 grams", "my husband is 6 foot",
# "my daughter is 5 stone" are a weight and a height, and a closed list of units missed the ones
# nobody thought of, so the list is the words that are allowed to follow instead.
# "18 months old" is an age in months, not eighteen years, and it is still a fact the chat
# holds. Kept apart from AGE_TAIL because the answer has to say the unit. The "old" is optional:
# people write "22 months" more often than "22 months old", and the tail still has to end the
# fact, so "22 months away" is not an age.
AGE_MONTHS_TAIL = re.compile(r"^\s*months?(?:\s+old)?\b", re.I)

AGE_TAIL = re.compile(
    r"^\s*(?:$|[.,;:!?)]|\b(?:and|but|so|now|today|tomorrow|yesterday|too)\b"
    # "my daughter is 7 going on 8", "im 41 going on 42": the figure after the phrase is the age
    # coming, and it says the figure before it is an age too. Without this the line filed no age
    # at all, so the manners reader took the whole thing for the phrase "going on" and answered
    # "I'm well, thanks", and the ask a turn later said nobody had ever given an age.
    r"|\bgoing on \d{1,3}\b"
    r"|\bas well\b|\bthis year\b|\byears? old\b|\bold\b"
    r"|\bnext (?:week|month|year|spring|summer|autumn|winter|monday|tuesday|wednesday|"
    r"thursday|friday|saturday|sunday)\b|\b(?:in|on|by) [a-z]{3,9}\b)",
    re.I)


def _month_age_after(text, end):
    """True when the words after `end` are an age in months and then the end of the fact."""
    match = AGE_MONTHS_TAIL.match(text[end:])
    if not match:
        return False
    return bool(AGE_TAIL.match(text[end + match.end():]))


# An age that is still to come is said with a birthday: "she's 5 next month", "my daughter turns
# 7 in june". The person has not had that birthday yet, so the number is kept with the words that
# say when, and the reply says it back as a birthday rather than as an age they have now.
# The "who" clause says whose age it is exactly as the plain shape does, so it is read the same
# way: "my sister whos 40 next week" is a birthday still to come, the same fact as "my sister is
# 40 next week", and saying she is 40 this week would be wrong for one of the two wordings.
AGE_TO_COME = re.compile(r"\b(?:turns?|will be|is|are|'s|shes|hes|she's|he's|theyre|they're|"
                         r"who(?:['\u2019]?s)?)\s+"
                         r"(\d{1,3})\s+"
                         r"(next\s+(?:week|month|year|spring|summer|autumn|winter)|"
                         r"(?:in|on)\s+[a-z]{3,9})\b", re.I)


# A name given for someone in the family, so "what's my sister called" is a fact about the chat
# and not a search: "my sister is called meg", "my sisters called meg", "my sister's name is meg",
# "my brother dan".
OTHER_CALLED = re.compile(r"\bmy\s+(?P<who>" + _RELATION_WORDS + r")s?\s+"
                          r"(?:(?:is|was|are)\s+)?(?:called|named)\s+" + _NAME, re.I)
OTHER_NAME_IS = re.compile(r"\bmy\s+(?P<who>" + _RELATION_WORDS + r")(?:'s|s'|s)?\s+name\s+"
                           r"(?:is|was)\s+" + _NAME, re.I)
# "my brother dan" names him in passing, with no verb at all. Only the whole line is read this
# way: a word after the relation mid-line is as often a verb ("my mum coming sunday") as a name.
OTHER_NAMED_BARE = re.compile(r"^\s*my\s+(?P<who>" + _RELATION_WORDS + r")s?\s+"
                              r"(?P<name>[A-Za-z][a-z'-]{1,19})\s*[.!]?$", re.I)
# The date somebody else was born on: "my mums birthday is on the 3rd of may", "his birthday is
# the 3rd of may", "my sons birthday is the 3rd of may". The date was kept as a line of the chat
# and nothing else, so the one fact the store did not hold about that person was their birthday:
# "my son is called tom" / "his birthday is the 3rd of may" then "when is toms birthday" was
# answered "I don't have a date from you for that", which denies a date they had just given. The
# person is the relation the line names, or the pronoun, which the store folds onto the person the
# chat is about the way it does an age ("shes 78" after a line about the mum is the mum's).
OTHER_BIRTHDAY = re.compile(
    r"\b(?:(?:my|our)\s+(?P<who>" + _RELATION_WORDS + r")s?|(?P<pronoun>his|her|their))\s+"
    r"(?:birthday|bday|dob|date of birth)\s*(?:'s|s)?\s*"
    r"(?:is|was|falls|:|=|on|in)\s+(?:on\s+)?(?:the\s+)?"
    r"(?P<date>[^,.;!?]{2,28})", re.I)
# The name given in passing between the person and what is said about them: "my son tom is 7",
# "my sister meg is allergic to nuts", "my daughter lily hates mushrooms". The name stands where a
# subject stands, so the word after it has to be one that follows a subject; that is what keeps
# "my son goes to school" and "my mum always says" from naming anybody. The relation is written
# without the possessive s, because "my nans death was peaceful" and "my sons teacher wants a
# word" say which person the thing belongs to, not what they are called.
# A name typed with its capital is a name however the rest of the line goes: "my friend Sarah
# called round" gives the friend her name, and the verb list below has no word for what she did,
# so the line filed a friend with no name and "whats my friends name" denied it. Only the capital
# is the evidence - a line typed all in lower case is read by the list above, because the word
# after a relation there is as often a verb ("my mum coming sunday") as a name.
# A lower-case name is said the same way: "my friend sarah called round", "my mate dave went
# home". The verb list above is a closed set and "called" is not in it, because "called" is also
# the naming verb ("my mate is called dave"). What settles it is the word *after* the name: a
# verb there means the word before it is the person, and a line whose third word is not a verb
# ("my mum coming sunday") still says nothing.
OTHER_NAMED_BEFORE_VERB = re.compile(
    r"\bmy\s+(?P<who>" + _RELATION_WORDS + r")\s+(?P<name>[a-z][a-z'-]{1,19})\s+"
    r"(?P<verb>[A-Za-z][a-z'-]{1,19})\b")


def _the_word_then_a_verb(name, following):
    """Whether the word after a name is a verb, so the word before it is the person's name."""
    name, following = (name or "").lower(), (following or "").lower()
    if not name or not following or name in VERB_FORMS:
        return False
    if following in VERB_FORMS:
        return True
    # The past forms of the verbs a line about somebody most often carries ("called round",
    # "texted me", "moved out"), which no list holds in full.
    return len(following) > 3 and following.endswith("ed")


OTHER_NAMED_CAPITAL = re.compile(
    r"\bmy\s+(?P<who>" + _RELATION_WORDS + r")\s+(?P<name>[A-Z][a-z'-]{1,19})\b")
# A possessive is not part of a name, and the readers above take the whole run of letters,
# apostrophe included: "my son Tom's car is broken" was kept as a son called "Tom's", and the
# store said it out loud ("Your son is called Tom's.") where main said it had not been told.
# "my friend Sarahs birthday is in may" is the same possessive with the apostrophe left out:
# the s is the possessive when the word after it is a thing and the word after *that* is a
# copula, which is the shape a possession has, and a name that merely ends in s ("my mate James
# was late", "my son Tom saw it") never matches. The stem is the person.
OTHER_NAME_POSSESSIVE = re.compile(
    r"\bmy\s+(?P<who>" + _RELATION_WORDS + r")\s+(?P<name>[A-Z][a-z]{1,19})(?:['\u2019]s?|"
    r"s(?=\s+[a-z]{3,19}\s+(?:is|are|was|were|will|has|have|had)\b))\b")
OTHER_NAMED_MIDLINE = re.compile(
    r"\bmy\s+(?P<who>" + _RELATION_WORDS + r")\s+"
    r"(?P<name>[A-Za-z][a-z'-]{1,19})\s+"
    r"(?P<verb>is|was|are|were|has|have|had|does|did|will|can|loves|hates|likes|needs|wants|"
    r"keeps|goes|works|plays|sleeps|eats|starts|started|turns|turned|says|said|misses|cries|"
    r"refuses|comes|came|gets|got|seems|looks|feels|takes|took|makes|made|buys|bought|"
    r"tells|told|struggles|wont|won't|cant|can't|doesnt|doesn't|isnt|isn't|didnt|didn't|"
    # The verbs a line about a person most often carries after their name, including the ones a
    # bereavement line uses: "my dad john died last year" gives the name, and denying it a turn
    # later is the one thing a memory store must not do.
    r"died|dies|passed|passes|lives|lived|moved|went|grew|became|married|left|arrived|retired|"
    r"finished)\b",
    re.I)
# Words in the name's place that are never a name: modals, auxiliaries and the adverbs that sit
# between a subject and its verb ("my mum always says", "my son still wont sleep"). Named for the
# place, not for the certainty: `NOT_A_NAME_EITHER` is already the pet-and-name reader's smaller
# set further down the file, and two sets under one name means the later assignment silently
# replaces the earlier one.
NOT_A_NAME_MIDLINE = frozenset("""
will would can could shall should may might must did does do dont doesnt didnt wont cant
shall always never often sometimes usually still really just also only suddenly already quite
rather very too more most less least better worse then than soon later yet ever once twice
she he they them we you it its this that there here i me him her his hers their
""".split())
# Words that stand in a name's place without being one: the thing a person owns or has said about
# them with the possessive's dropped ("my son name is tom", "my mum birthday is saturday"), and
# the things people say in the same breath ("my dads speech is slurred"). The reader would rather
# miss a name than answer "What is your nan called?" with "Death".
NOT_A_NAME_THERE = frozenset("""
name names age birthday bday anniversary death funeral wake school teacher teachers class
homework reading exam exams job work shift shifts boss mood temper speech health weight diet
appetite sleep room bedroom car phone mobile laptop house flat garden leg legs arm arms back
head hand hands knee ankle shoulder eye eyes ear ears teeth tooth hair skin cough cold
temperature illness surgery appointment hospital care medication meds pills tablets inhaler
hearing eyesight memory bills rent money wages pension benefits passport visa wedding holiday
flight train bus ticket tickets booking order parcel present presents card
""".split())


def _may_be_a_name(word):
    """Whether a word standing where a name stands can be one."""
    low = word.lower()
    return (_looks_like_a_name(word) and low not in NOT_A_NAME_MIDLINE
            and low not in NOT_A_NAME_THERE)

# Endings that make a word a doing or a way of being rather than a name: "coming", "tired",
# "angrily". Nobody is called Coming.
NOT_NAME_ENDING = ("ing", "ed", "ly")
# Names that end the way a doing or a way of being does, so the ending alone does not rule them
# out: "my daughter lily is 4" is a girl called Lily, and "ted" is a man's name.
NAMES_THAT_END_LIKE_A_VERB = frozenset("""
lily holly molly polly sally kelly emily billy willy ted ned fred jed ed
""".split())


def a_titled_name(word):
    """Whether a word is a title with a name after it: "mr patel", "dr. kaur", "mrs smith"."""
    return bool(re.fullmatch(r"(?:" + TITLE + r")\s+[A-Za-z][A-Za-z'\-]{1,19}",
                             str(word or "").strip(), re.I))


def _looks_like_a_name(word):
    """Whether a word after a relation can be their name: not a relation, not a grammar word."""
    low = word.lower()
    if a_titled_name(word):
        return True  # a title is not a name on its own, but the name after it is the name
    if low.strip(".") in TITLE_WORDS:
        return False  # "my sister is called mr smith" is Mr Smith, and Mr names nobody
    if not NAME_WORD.match(word) or low in NOT_A_NAME or low in RELATIONS:
        return False
    if is_a_contraction(low):
        return False
    if word[:1].isupper() or low in NAMES_THAT_END_LIKE_A_VERB:
        return True  # typed with a capital, the way a name is written
    return not low.endswith(NOT_NAME_ENDING)


def _name_after_a_title(name):
    """Whether a name that starts with a title is a name at all.

    A title is part of the name ("Mr Smith"), and the word after it is what makes it a name: "my
    sister is called mrs tired" names nobody, because the word after the title is one of the
    things people say about a person. A title on its own names nobody either, which is how the
    store came to answer "Your sister is called Mr".
    """
    words = str(name or "").split()
    if not words:
        return False
    title = words[0].strip(".").lower()
    if title not in TITLE_WORDS:
        return True
    if len(words) == 1:
        return False
    rest = " ".join(words[1:]).lower()
    if rest in NAME_AFTER_TITLE:
        return True  # "Dr Who"
    if rest in NOT_A_NAME or rest in NOT_NAMES or rest in NOT_NAMES_EXTRA \
            or rest in _A_WORD_FOR_A_PERSON:
        return False
    return not _not_a_name(rest, strict_ly=False)


def _the_name_without_a_possessive(text):
    """{"tom's": "Tom", "sarahs": "Sarah"} for the possessive runs in a line.

    The key is what the readers below capture (the name with the possessive still on it), so a
    pass that takes "Tom's" reads the same person as the naming lines do.
    """
    stems = {}
    for match in OTHER_NAME_POSSESSIVE.finditer(text):
        raw = text[match.start("name"):match.end()]
        raw = str(raw).replace("\u2019", "'").lower()
        stem = match.group("name")
        if raw and stem:
            stems[raw] = stem
    return stems


def _a_relations_name(text):
    """[{"who": "sister", "name": "meg"}] for a name the line gives to someone in the family."""
    found = []
    text = stated_not_asked(text)
    if not text:
        return found
    without_possessive = _the_name_without_a_possessive(text)
    for pattern in (OTHER_CALLED, OTHER_NAME_IS, OTHER_NAMED_BARE):
        for match in pattern.finditer(text):
            who = a_person_word(match.group("who"))
            if who.endswith("s") and who[:-1] in RELATIONS:
                who = who[:-1]
            name = match.group("name")
            if not _looks_like_a_name(name) or not _name_after_a_title(name):
                continue
            if who in [entry["who"] for entry in found]:
                continue
            found.append({"who": who, "name": name})
    for match in OTHER_NAMED_BEFORE_VERB.finditer(text):
        who = a_person_word(match.group("who"))
        if who.endswith("s") and who[:-1] in RELATIONS:
            who = who[:-1]
        name = without_possessive.get(str(match.group("name")).lower(), match.group("name"))
        if not _the_word_then_a_verb(name, match.group("verb")):
            continue
        if not _may_be_a_name(name):
            continue
        if who in [entry["who"] for entry in found]:
            continue
        found.append({"who": who, "name": name})
    for match in OTHER_NAMED_CAPITAL.finditer(text):
        who = a_person_word(match.group("who"))
        if who.endswith("s") and who[:-1] in RELATIONS:
            who = who[:-1]
        name = without_possessive.get(str(match.group("name")).lower(), match.group("name"))
        if not _may_be_a_name(name):
            continue
        if who in [entry["who"] for entry in found]:
            continue
        found.append({"who": who, "name": name})
    for match in OTHER_NAMED_MIDLINE.finditer(text):
        who = a_person_word(match.group("who"))
        if who.endswith("s") and who[:-1] in RELATIONS:
            who = who[:-1]
        name = without_possessive.get(str(match.group("name")).lower(), match.group("name"))
        if not _may_be_a_name(name):
            continue
        if who in [entry["who"] for entry in found]:
            continue
        found.append({"who": who, "name": name})
    return found


# How many children they have. "i have two kids" was filed as nothing at all, so the store could
# not answer "how many kids do i have" and the line itself got no fact read back. The number comes
# with the word for the children, because "i have two" alone is about whatever was just mentioned,
# and "a couple of" is two however it is put.
KID_COUNT = re.compile(
    r"\b(?:i|we)(?:'ve|ve|\s+have|\s+have\s+got|\s+got)\s+(?:got\s+)?"
    r"(?P<n>\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"a\s+couple\s+of)\s+(?:kids?|children|child)\b"
    r"|\bmy\s+(?P<m>\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    r"\s+(?:kids?|children)\b", re.I)
# The count is often the second thing in the line, after something else they have: "i've got a dog
# and two kids" kept the dog and no number of children, while the same count said first ("i've got
# two kids and a dog") was held - so the recap of the first line could not say the children at all.
# A count joined on with "and" or a comma belongs to the same person, and it is read as one.
KID_COUNT_AND = re.compile(
    r"\b(?:i|we)(?:'ve|ve|\s+have|\s+have\s+got|\s+got)\s+[^.;!?]{0,40}?(?:\band\b|,)\s*"
    r"(?P<n>\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"a\s+couple\s+of)\s+(?:kids?|children|child)\b", re.I)
KID_NUMBERS = {word: number for number, word in enumerate(
    ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
     "eleven", "twelve"))}
# The same count the other way, so a reply can say "Two kids" rather than "2 kids".
KID_NUMBER_WORDS = {number: word for word, number in KID_NUMBERS.items()}
# A figure spelled as a word is the same figure. Every ages reader here matched on digits, so
# "my kids are four and seven" was no fact at all, and a line the reading spells only part way
# ("i have two kids, 4 and 7" reaches the store as "i have two kids, four and 7") gave a lone 7
# for a group of two children - an age stuck on the end of a list of ages that was already right.
# The words become digits once, before any reader looks, and "twenty one" is 21, not 20 and 1.
FIGURE_WORDS = {word: str(number) for number, word in enumerate(
    ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
     "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
     "eighteen", "nineteen", "twenty"), start=1)}
FIGURE_PAIR = re.compile(r"\btwenty[\s-]+(one|two|three|four|five|six|seven|eight|nine)\b",
                         re.I)
FIGURE_WORD = re.compile(r"\b(?:" + "|".join(sorted(FIGURE_WORDS, key=len, reverse=True))
                         + r")\b", re.I)


def figures_as_digits(text):
    """The line with every figure it spells as a word written as a digit instead."""
    if not isinstance(text, str) or not text:
        return ""
    text = FIGURE_PAIR.sub(
        lambda match: str(20 + int(FIGURE_WORDS[match.group(1).lower()])), text)
    return FIGURE_WORD.sub(lambda match: FIGURE_WORDS[match.group(0).lower()], text)
# Their own children, so a count followed by where those children are ("in my class", "in year
# four") is a class the person teaches.
# The ages said with the children: "my two kids are 4 and 7", "i have two kids aged 4 and 7".
# The count alone is a fact and the ages are another one, so a reply that has them should use
# them rather than ask for the ages the person has just given.
KID_AGES = re.compile(
    r"\b(?:kids?|children|child)\b[^.!?]{0,24}?\b(?:are|aged?|of)\s+"
    r"(?P<ages>\d{1,2}(?:\s*(?:,|and)\s*\d{1,2})+)", re.I)
# The same list with no verb in it: "i have two kids, 4 and 7" gives the ages after a comma, and
# the reply that asked "How old are they?" asked for what the person had just written down.
KID_AGES_AFTER_A_COMMA = re.compile(
    r"\b(?:kids?|children)\b\s*[,:;-]\s*(?P<ages>\d{1,2}(?:\s*(?:,|and)\s*\d{1,2})+)", re.I)


def kid_ages(text):
    """The ages the line gives the children, oldest reading only, or []."""
    if not isinstance(text, str):
        return []
    match = KID_AGES.search(figures_as_digits(text)) or KID_AGES_AFTER_A_COMMA.search(
        figures_as_digits(text))
    if match:
        ages = [int(number) for number in re.findall(r"\d{1,2}", match.group("ages"))]
        return [age for age in ages if 0 <= age <= 110]
    # A child given one by one is aged just as plainly: "we have a 3 year old" says the age of the
    # one child, and a reply that asks "How old are they?" asks for what the line just said.
    counted = _children_by_year_old(figures_as_digits(text))
    if counted:
        return _ages_held(counted)
    # "my boys are 4 and 7 years old" names the group rather than the children as such, and the
    # reader for the people a line names keeps that age under the group's own name.
    grouped = [entry for entry in _other_ages(text)
               if (entry.get("who") or "").lower() in KID_GROUP]
    if grouped and not any(entry.get("name") for entry in grouped):
        held = []
        for entry in grouped:
            held.extend(age for age in _ages_held(entry) if age not in held)
        if held:
            return held
    # Children named one at a time keep their ages under their own relation - "my daughter is 6
    # and my son is 9" - so the ages are read off the entries themselves, in the order the line
    # says them. One named child is left alone: "my son is 6" has an answer of its own.
    each = [entry for entry in _other_ages(text)
            if (entry.get("who") or "").lower() in KID_ONE_BY_ONE]
    if len(each) >= 2 and not any(entry.get("name") for entry in each):
        held = []
        for entry in each:
            held.extend(age for age in _ages_held(entry) if age not in held)
        if held:
            return held
    return []


# The ages of the children the store already counts, handed out one at a time on the next line:
# "i have two kids" then "ones 7 and ones 4". No group word is in the second line, so none of the
# readers above match it, the store kept nothing, and the bot said the line back ("Got it - ones 7
# and ones 4."); "what do you know about my kids" then answered that it did not know. The same line
# is the plain answer to the question the count was met with ("how old are they?").
ONES_BY_ONE = re.compile(
    r"\bones?\b|\bthe\s+(?:other|older|younger|little|big|small|eldest|youngest)\s+one\b", re.I)
# What such a line may say besides the ages: the words that hand them out, and nothing that names
# another thing ("i have 2 dogs and 4 cats" is not two children).
AGES_ONLY_WORD = frozenset("""and or is are s the other older younger little big small eldest
youngest of them both now too yeah oh well ok okay right so but theyre they there its it aged old
then
years year yrs yo nearly almost just turned about""".split())


def the_ones_are_given_one_at_a_time(text):
    """Whether the line hands the ages out one by one ("ones 7 and ones 4", "the older one is 7")."""
    if not isinstance(text, str):
        return False
    return bool(ONES_BY_ONE.search(" ".join(text.lower().replace("'", "").split())))


def ages_said_one_by_one(text, count):
    """The ages a line gives a group the store counts, or [] when it gives anything else."""
    if not isinstance(text, str) or not isinstance(count, int) or count < 2:
        return []
    flat = " ".join(text.lower().replace("'", "").split())
    if not flat or len(flat.split()) > 12:
        return []
    flat = figures_as_digits(ONES_BY_ONE.sub(" & ", flat))
    ages = []
    for word in re.split(r"[^a-z0-9]+", flat):
        if not word:
            continue
        if word.isdigit():
            age = int(word)
            if not 0 < age <= 120:
                return []
            ages.append(age)
        elif word not in AGES_ONLY_WORD:
            return []
    return ages if len(ages) == count else []


KID_ELSEWHERE = re.compile(
    r"^\s*(?:in|at)\s+(?:my|the|our|a|this|that)\s*(?:class|classes|classroom|school|nursery|"
    r"club|group|team|unit|year)\b|^\s*in\s+year\b|^\s*in\s+(?:reception|year)\b", re.I)
# A question about the number is not a statement of it: "do i have two kids" asks.
KID_ASKING = re.compile(r"^\W*(?:do|did|does|have|has|how|are|is|was|were|can|could|would)\b",
                        re.I)
# A number of zero is still a number. "i dont have any kids" said nothing to the store at all,
# so "how many kids do i have" answered "You haven't told me how many kids you have yet" to a
# person who had just said they have none. The words are the ordinary ways of saying none: a
# negated have, a plain "no kids", and the count said as zero.
KID_NONE = re.compile(
    r"\b(?:i|we)(?:'ve|ve)?\s+(?:do\s+not|dont|don't|did\s+not|didnt|didn't|have\s+not|"
    r"havent|haven't|has\s+not|hasnt|hasn't)\s+(?:got\s+)?(?:have\s+)?(?:any\s+|a\s+)?"
    r"(?:kids?|children|child)\b"
    r"|\b(?:i|we)(?:'ve|ve|\s+have|\s+have\s+got|\s+got)\s+no\s+(?:kids?|children)\b"
    r"|\bno\s+(?:kids?|children)\b"
    r"|\b(?:i|we)(?:'ve|ve|\s+have|\s+have\s+got|\s+got)\s+(?:zero|0)\s+(?:kids?|children)\b",
    re.I)
# A zero that is not a zero: "i dont have any kids yet" is somebody trying, "i dont have kids at
# home" is a house with grown children in it, and "i dont have kids anymore" with them gone says
# nothing about how many there are. None of them is a count to say back.
KID_NONE_NOT_AFTER_ALL = re.compile(
    r"\b(?:yet|anymore|any\s+more|with\s+me|at\s+home|living\s+at\s+home|but|instead)\b", re.I)


def kid_count(text):
    """"i have two kids" -> 2, "i dont have any kids" -> 0: the number a line states, or None."""
    if not isinstance(text, str) or KID_ASKING.match(text):
        return None
    none = KID_NONE.search(text)
    if none and not KID_NONE_NOT_AFTER_ALL.search(text[none.end():]):
        return 0
    match = KID_COUNT.search(text) or KID_COUNT_AND.search(text)
    if not match:
        # Children given one by one are still a number of children: "i have a 4 year old and a 7
        # year old" and "my kids are 4 and 7" name two children in the same breath as their ages,
        # and the answer to "how many kids do i have" is the count of the ages the line gave.
        ages = kid_ages(text)
        if ages:
            return len(ages)
        counted = _children_by_year_old(figures_as_digits(text))
        if counted:
            return len(_ages_held(counted))
        grouped = [entry for entry in _other_ages(text)
                   if (entry.get("who") or "").lower() in KID_GROUP]
        if grouped and not any(entry.get("name") for entry in grouped):
            held = []
            for entry in grouped:
                held.extend(age for age in _ages_held(entry) if age not in held)
            if held:
                # "my boys are 4 and 7 years old" counts the children it has ages for.
                return len(held)
        # Children named one relation at a time, each with their own age: "my daughter is 6 and
        # my son is 9" says two children as plainly as "my kids are 6 and 9" does, and the store
        # could not count it, so the line came back as a receipt - "Noted: your daughter is 6 and
        # my son is 9" - while the same line with the word "kids" in it was answered "Two kids,
        # six and nine. What are they into at the moment?". Two or more, because one named child
        # ("my son is 6") has an age answer of its own that must keep its turn.
        each = [entry for entry in _other_ages(text)
                if (entry.get("who") or "").lower() in KID_ONE_BY_ONE
                and (entry.get("age") or _ages_held(entry))]
        if len(each) >= 2 and not any(entry.get("name") for entry in each):
            return len(each)
        return None
    if KID_ELSEWHERE.search(text[match.end():]):
        # "i have two kids in my class" is a teacher counting the class, not a parent counting
        # their own: the children are at school, and not in this person's house.
        return None
    said = (match.group("n") or match.group("m") or "").lower()
    if said.startswith("a couple"):
        return 2
    if said.isdigit():
        return int(said)
    return KID_NUMBERS.get(said)

# The count said back about the group in hand: "actually there are three of them", "we have
# three altogether". People correct a number this way, with no word for the people in the line at
# all, so `kid_count` finds no "kids" to read and the store kept the old number: "i have two kids"
# then "actually there are three of them" still answered "You've got two children." The group is
# whatever the turn before was about, which is the store's question, not the reader's.
COUNT_OF_THEM = re.compile(
    r"\b(?:there are|there're|there is|theres|there's|that's|thats|we have|we've got|we got|we"
    r" have got)\s+(?P<n>\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    r"\s+(?:of them|altogether|in total|in all)\b", re.I)
# A line that goes on to say where they are is about that place, not a correction of the count:
# "there are three of them at school" is not how anybody says "I have three children".
COUNT_OF_THEM_ELSEWHERE = re.compile(
    r"^\s*(?:at|in|on|down|up|over|for|from|who|here|there|with|left|still|near|around|about|"
    r"already|so|but)\b", re.I)
# The words that say the group in hand is the children: the count has nothing else to say which
# people it is about.
CHILDREN_WORDS = ("kid", "kids", "child", "children", "boy", "boys", "girl", "girls", "son",
                  "sons", "daughter", "daughters", "twin", "twins")


def count_of_the_people(text, memory):
    """"there are three of them" -> 3, while the group in hand is the children.

    The count in front of the word ("my three kids") is `kid_count`'s to read. This is the same
    fact said the other way round - the number, then "of them" - and it needs the store to say
    which people it counts: the group the turn before was about, or the children the store holds.
    "my cats are called milo, tom and otis" then "there are three of them" counts cats, and a
    number about cats is not a number of children.
    """
    if not isinstance(text, str) or KID_ASKING.match(text):
        return None
    match = COUNT_OF_THEM.search(text)
    if not match:
        return None
    said = match.group("n").lower()
    number = int(said) if said.isdigit() else KID_NUMBERS.get(said)
    if not number or not 1 < number <= 12:
        return None
    if COUNT_OF_THEM_ELSEWHERE.match(text[match.end():]):
        return None
    if not _the_group_in_hand_is_the_children(memory):
        return None
    return number


def _the_group_in_hand_is_the_children(memory):
    """Whether the children are what the chat was last on, so a bare count is theirs."""
    user_record = (memory or {}).get("user")
    turns = (memory or {}).get("turns")
    said = ""
    if isinstance(turns, list):
        last = next((turn for turn in reversed(turns) if isinstance(turn, dict)), None)
        said = " ".join(str((last or {}).get("user") or "").lower().split())
    words = set(re.split(r"[^a-z']+", said))
    if words & set(CHILDREN_WORDS):
        return True
    if isinstance(user_record, dict) and user_record.get("kids"):
        # The children are on file and the turn before named another group of people ("my cats"):
        # then the cats are what the count is about.
        others = set(words) & {"cats", "cat", "dogs", "dog", "pets", "pet", "fish", "birds"}
        return not others
    return False


# The children said as one group: "my kids are 4 and 7", "i have two children aged 4 and 7",
# "my kid is 5". They are not in RELATIONS, which names one person at a time, because a line
# about children usually gives more than one age in the same breath and the ages belong together:
# "how old are my kids" is one of the commonest things a person asks a chat that has been
# listening, and a confident "you haven't told me" straight after they did is worse than no answer.
# The count above uses its own ages reader (KID_AGES/kid_ages, which needs "are" or "aged"); this
# is the one the store files, because it also reads the ages said after a comma and keeps them in
# the order the person gave them.
KIDS = ("kids", "children", "child", "kid")
# The words a group of children can be said under. "my boys" and "my sons" are two children the
# same way "my kids" is, and the word is kept as the person each of them belongs under.
KID_GROUP = tuple(KIDS) + ("sons", "daughters", "boys", "girls")
# A child named one at a time is said with the singular word - "my daughter is 6 and my son is
# 9" - so a line that gives children their own ages is read with these as well as the group
# words above. The plural is here too: "my sons are 6 and 9" is the same line.
KID_ONE_BY_ONE = ("son", "daughter", "sons", "daughters", "child", "children", "kid",
                  "kids", "boy", "girl", "boys", "girls", "baby", "twins", "twin")
# "my kids are 4 and 7", "my children are 4, 7 and 9"
#
# Two words in front of the group were read as not the group at all. A count is the number of
# them, not part of who they are - "my two girls are 6 and 9" names the same two girls "my girls
# are 6 and 9" does - and "our" is the same possessive as "my": "our two boys are 6 and 9" and
# "our 2 girls are 6 and 9" were answered with a receipt ("Thanks for telling me") and the store
# kept nothing, so "how old are they" a turn later had no ages to read.
A_COUNTED_GROUP = (r"\b(?P<whose>my|our)\s+"
                   r"(?:(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
                   r"|\d{1,2})\s+)?")
KID_AGES_ARE = re.compile(A_COUNTED_GROUP + r"(?P<who>" + "|".join(KIDS) + r")\s+(?:are|is)\s+"
                          r"(?:both\s+)?(?:aged?\s+)?(?P<ages>\d{1,3}"
                          r"(?:\s*(?:,|and)\s*\d{1,3})*)", re.I)
# The same ages said under any of the words a group of children go by: "my boys are 9 and 6" is
# the line "my kids are 9 and 6" in another word, and the ask can be in either.
KID_GROUP_AGES_ARE = re.compile(A_COUNTED_GROUP + r"(?P<who>" + "|".join(KID_GROUP) + r")\s+"
                               r"(?:are|is)\s+(?:both\s+)?(?:aged?\s+)?"
                               r"(?P<ages>\d{1,3}(?:\s*(?:,|and)\s*\d{1,3})*)", re.I)
# "i have two kids, 4 and 7", "i've got three children aged 2, 4 and 7": the count in front of
# the word is the number of them, not an age, so the ages are read after the word.
KID_COUNT_AGES = re.compile(
    r"\b(?:i|we)(?:\s+have|'ve|ve)(?:\s+got)?\s+(?:\w+\s+)?(?P<who>kids|children)\b"
    r"(?:[^.\d]{0,14})(?P<ages>\d{1,3}(?:\s*(?:,|and)\s*\d{1,3})*)", re.I)
# The same ages in a line that counts the children without the word "my" in front of them: "we
# are 2 adults and 2 kids aged 6 and 9" is two children and their two ages, and the store kept
# nothing at all, so the very next "how old are they" said they had never told.
KID_ADULTS_AGES = re.compile(
    r"\b(?:kids?|children|child)\b(?:[^.\d]{0,14})?(?:aged?|of|are)\s+"
    r"(?P<ages>\d{1,3}(?:\s*(?:,|and)\s*\d{1,3})+)", re.I)
# A number that says where the group sits rather than what age each of them is: "two kids under
# 5" is not "two kids aged 5".
KID_AGES_NOT = re.compile(r"\b(?:under|over|above|below|nearly|almost|about|round|around)\s*$", re.I)


# The children named with their ages in one breath: "my kids are ada 7 and sam 4", "my children
# are ada, 7, and sam, 4". Each child is their own person, with their own name and their own age,
# so "how old is ada" and "how old are my kids" are both answerable from the line. The group word
# in front is what says these are their children, and it is kept as the person each one of them
# belongs under.
KID_NAME_AGES = re.compile(r"\bmy\s+(?P<who>" + "|".join(KID_GROUP) + r")\s+(?:are|is)\s+(?P<rest>"
                           r"[a-z][a-z'-]{1,19}\s+\d{1,3}(?:\s*(?:,|and)\s*"
                           r"[a-z][a-z'-]{1,19}\s+\d{1,3})*)\b", re.I)
KID_NAME_AGE = re.compile(r"(?P<name>[a-z][a-z'-]{1,19})\s+(?P<age>\d{1,3})", re.I)
# A figure the line says after the names it has already paired up. The line reaches this reader
# with its numbers spelled out ("my kids are ada 7 and four"), so a digit alone is not enough to
# see the second child: pairing "ada 7" on its own invents one child and quietly drops the other.
FIGURE_AFTER = re.compile(r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven"
                          r"|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen"
                          r"|nineteen|twenty)\b", re.I)


# The words that say where a figure sits rather than whose it is: "my kids are nearly 5 and 7"
# is not two children called Nearly and 7, and "my children are under 5" is not a child called
# Under. `KID_AGES_NOT` already stops the plain ages reader taking the figure; a name taken from
# one of these words is worse than the shrug, because it invents a person and drops the other
# child.
NOT_A_NAME_HEDGE = frozenset("""nearly almost about around round under over above below
roughly approximately approx somewhere only just both all each every either neither
aged age ages yrs year years old""".split())


def _kids_named_with_ages(text):
    """[{"who", "name", "age"}] for the children given with a name and an age, or []."""
    found = []
    who_word = "|".join(RELATIONS)
    for match in KID_NAME_AGES.finditer(text):
        rest = match.group("rest")
        if KID_AGES_NOT.search(text[:match.start("rest")]):
            continue  # "my kids are nearly 5 and 7" gives a figure for the group, not a name
        pairs = list(KID_NAME_AGE.finditer(rest))
        if not pairs:
            continue
        if len(re.findall(r"\d{1,3}", rest)) != len(pairs) or FIGURE_AFTER.search(text[match.end():]):
            # One age of the run was given without a name ("my kids are ada 7 and 4"), so the
            # line is not a person per figure: the reader matches the named part and would stop
            # before the bare one. Pairing "ada 7" alone invents a child and drops the 4, so the
            # line is left to the readers that were there before.
            continue
        for pair in pairs:
            name, age = pair.group("name"), int(pair.group("age"))
            low = name.lower()
            if (low in NOT_A_NAME or low in KIDS or low in NOT_A_NAME_HEDGE
                    or low in NOT_A_NAME_MIDDLE or low in NOT_A_NAME_THING
                    or low in NOT_A_NAME_STATE
                    or low in MONTHS or low in DAYS or not 0 <= age <= 120):
                continue
            if age <= 2 and not name[:1].isalpha():
                continue
            found.append({"who": match.group("who").lower(), "name": name,
                          "age": age})
    return found


def _the_same_person(one, other):
    """Whether two readings of the people in a line are about the same person.

    Two children named in one breath ("my kids are ada 7 and sam 4") share the word in front of
    them, so the word alone is not enough to tell them apart: the name is what says which child
    the age belongs to, and two named children are never folded into one.
    """
    if (one.get("who") or "") != (other.get("who") or ""):
        return False
    return str(one.get("name") or "").lower() == str(other.get("name") or "").lower()


# A state of a person they live with that changes what you would suggest for them: a pregnancy,
# or an alcohol-free limit. It is a fact about that person, like a diet or an age, so it is kept
# against them and never read as something wrong with the person typing ("my wife is pregnant so
# she cant drink" was answered "What has your wife said about it - and how long has it been like
# this?"). Only a relation-named person ("my wife", "my daughter"), never "i".
_STATE_WHO = lambda: r"\bmy\s+(?P<who>" + "|".join(sorted(RELATIONS, key=len, reverse=True)) + r")"
# The length comes before the word as often as not: "my wife is 8 weeks pregnant" is the common
# way a pregnancy is said, and read only as "is pregnant" it kept nothing at all - the store had
# no pregnancy for her, so the turn after it ("she feels sick in the mornings") was answered by a
# card that opened "Morning sickness that is not pregnancy is usually...". The weeks are part of
# the same fact: they are kept with it, because they date nothing and are only true of now.
OTHER_STATE = re.compile(
    _STATE_WHO() + r"\s*(?P<tense>'s|is|are|was|were)\s+"
    r"(?:(?P<weeks>\d{1,2})\s*(?:weeks?|wks?)\s+)?"
    r"(?P<state>pregnant|expecting|breastfeeding|nursing a baby)\b", re.I)
# The words that mean the pregnancy, and the words that do not. A woman who is breastfeeding was
# kept as pregnant and answered "your wife being pregnant is worth knowing": the state is the
# word they said, and a state the store did not hear is a fact it must not put on anyone.
PREGNANCY_STATES = ("pregnant", "expecting")
OTHER_LIMIT = re.compile(
    _STATE_WHO() + r"\s*(?:can'?t|cannot|doesn'?t|does not|won'?t|will not|isn'?t)"
    r"\s+(?:really\s+)?(?:drink|drinks)\b"
    # "my son cant drink milk" is about the milk, not about alcohol: the limit ends where the
    # line does, or goes on with a word that is about drinking and nothing else.
    r"(?=\s*(?:$|[.,;!?]|alcohol\b|at all\b|any ?more\b|anymore\b|either\b|though\b|"
    r"these days\b|now\b|when\b))", re.I)


# The person's own state, said about themselves: "im 12 weeks pregnant", "i'm expecting a baby".
# The store kept this state only for somebody else, so the person's own news was congratulated and
# forgotten, and "how far along am i" after it got a search hedge. The subject is the person, so
# the fact is filed against them (`memory["user"]`) rather than against a relation.
OWN_STATE = re.compile(
    # The pronoun has to open the clause: "i thought i was pregnant" is a thought about a maybe,
    # and the "i was pregnant" inside it is not news.
    r"(?:^|[.;,!?]\s*|\b(?:and|but|so|because|although|though)\s+)"
    r"(?:i|im|i'm|i’m|ive|i've)\s+(?:am\s+|was\s+|feel\s+|think\s+i\s*m\s+)?"
    # "not" and "no longer" take the state back out: "im not pregnant" says the opposite.
    r"(?!not\b|no longer\b|never\b|wasnt\b|wasn't\b)"
    r"(?:(?P<weeks>\d{1,2})\s*(?:weeks?|wks?)\s+)?"
    r"(?P<state>pregnant|expecting)\b", re.I)
# A pregnancy nobody put a length on is still the state, and the length is only true of now.
OWN_PREGNANCY_WEEKS_MAX = 45


def _own_states(text):
    """{"pregnant": True, "weeks": 12} for the person themselves, or {}.

    A length said with the state is part of the same fact, exactly as it is for "my wife is 8
    weeks pregnant": the weeks date nothing, they are only true of now, so a past tense keeps
    nothing at all.
    """
    # "im eight weeks pregnant" is the same fact as "im 8 weeks pregnant": most people spell a
    # small number out, and the length was lost while the state was kept, so "how far along am i"
    # after it was a search hedge about a chat that had said the answer.
    for match in OWN_STATE.finditer(figures_as_digits(text)):
        said = match.group(0).lower()
        if re.search(r"\b(?:was|were|thought|maybe|might|may|hope|hoping|could)\b", said):
            continue
        found = {"pregnant": True}
        weeks = match.group("weeks")
        if weeks is not None and 1 <= int(weeks) <= OWN_PREGNANCY_WEEKS_MAX:
            found["weeks"] = int(weeks)
        return found
    return {}


def _other_states(text):
    """[{"who", "pregnant"|"breastfeeding": True}] and [{"who", "drinks": False}] for these people.

    A question is not a fact: "is my wife pregnant?" asks, and only a line that says it stores it.
    Nor is a thing that was: "my wife was pregnant" is not a state she is in now, so a past tense
    keeps nothing (said back in the present it told a woman whose child had arrived that a drink
    was off the table because she was pregnant).
    """
    found = []
    for match in OTHER_STATE.finditer(text):
        if match.group("tense").lower() in ("was", "were"):
            continue
        who = " ".join(match.group("who").lower().split())
        state = match.group("state").lower()
        if state in PREGNANCY_STATES:
            entry = {"who": who, "pregnant": True}
            weeks = match.groupdict().get("weeks")
            if weeks and 1 <= int(weeks) <= 45:
                entry["weeks"] = int(weeks)
            found.append(entry)
        else:
            found.append({"who": who, "breastfeeding": True})
    for match in OTHER_LIMIT.finditer(text):
        who = " ".join(match.group("who").lower().split())
        found.append({"who": who, "drinks": False})
    return found
# The child given as "a 4 year old": the age comes with no age word in front of it and, often,
# no relation either ("i have a 4 year old and a 7 year old"). Read as digits above, the phrase
# is the same as "aged 4", and the children it counts are the children the chat knows about.
YEAR_OLD = re.compile(r"\b(?P<age>\d{1,3})\s*(?:years?|yrs?)[- ]old\b", re.I)
# "when i was a 4 year old" is the person's own age, not their child's.
OWN_AGE_BEFORE_IT = re.compile(r"\b(?:i|we)\s+(?:was|were|am|had been)\s*(?:a|an)?\s*$", re.I)
# An animal is aged in years too, and "our dog is a 4 year old" is about the dog.
YEAR_OLD_ANIMAL = re.compile(r"\b(?:" + "|".join(sorted(ANIMALS)) + r")\b", re.I)
# A thing is aged in years as well, and it is not a child: "my laptop is really slow" / "its
# about 5 years old" was read as a five year old child, and the turn after it asked the person
# how old they were. The subject of the age is the word before it, so a thing named there (or the
# pronoun for one) means the number is the thing's age, not a child's.
THING_AGED = re.compile(
    r"\b(?:it|its|it's|that|thats|that's|this|these|those|there|hes|he's|shes|she's|theyre|"
    r"they're|mine|ours|yours|theirs)\b[^.!?]{0,12}$", re.I)
# A person pointed at is a person, and the years after them are theirs: "he is 8 years old" says
# what "hes 8" says, and neither line says there are any children. Read as a count of children,
# the store answered "One kid, eight - noted." to a person who had just said how old their nephew
# was, and the count then stood as a fact about the family. The pronoun's own entry keeps the
# age, so nothing is lost by standing down here.
A_PERSON_AGED = re.compile(
    r"\b(?:he|she|they|hes|she's|he's|shes|theyre|they're)\b[^.!?]{0,12}$", re.I)
NAMED_THING_AGED = re.compile(
    # A figure belongs in the noun because the reading spells figures as digits before this runs:
    # "the old one is 12 years old" arrives as "the old 1 is 12 years old", and a noun class of
    # letters alone could not see the thing that is aged. The age was then filed as a twelve year
    # old child, and the store said "One kid, twelve - what are they into?" to a person who had
    # just said how old their washing machine was. Any numbered thing is the same ("my machine 2
    # is 8 years old"), so the noun takes a figure wherever it falls.
    r"\b(?:my|our|your|his|her|their|the)\s+(?P<noun>[a-z' 0-9]{1,30}?)\s*"
    r"(?:is|was|are|were|s|'s)\b[^.!?]{0,12}$", re.I)
# A thing is aged in years without a be-form too: "a dell about 4 years old", "the sofa, about 6
# years old". The determiner and the thing are there; only the word "is" is missing. Without this
# the age went in as a child's - "a dell about 4 years old" was answered "One kid, four. What are
# they into at the moment?" in a chat about a laptop fan, and "the sofa, about 6 years old" the
# same. So when a determiner names a thing and only a be-form or a qualifier ("about", "roughly",
# "around", "nearly", "only", "just") sits between that name and the age, the age is the thing's -
# unless the name is a person word, which is what the check below is for. A determiner with nothing
# after it names no thing ("i have a 4 year old and a 7 year old"), so it is left alone.
THING_AGED_QUALIFIED = re.compile(
    r"\b(?:a|an|the|my|our|your|his|her|their)\s+(?P<noun>[a-z'][a-z'0-9]*)(?:\s*,)?\s*"
    r"(?:(?:is|was|are|were|s|'s)\s*)?(?:(?:,\s*)?(?:about|roughly|around|nearly|only|just)\s*)?$",
    re.I)
# "the youngest about 4 years old" is one of the children, not a thing that is 4 years old.
PERSON_ELSEWHERE = frozenset("""youngest oldest eldest younger older middle first second third
last little big small""".split())
# The words a line uses for the children themselves: a noun here is a person ("my kids are 4 and
# 7 years old") and the age is one of theirs.
PEOPLE_AGED = frozenset(KID_GROUP) | frozenset("""kid child children boy boys girl girls son
sons daughter daughters twin twins baby babies toddler toddlers lad lads lass lasses""".split())
# "my 5 year old laptop" ages the laptop, not a child: the word just after the age says what the
# age belongs to.
AFTER_YEAR_OLD = re.compile(r"^\s+(?P<word>[a-z']{2,})\b", re.I)
AFTER_YEAR_OLD_OKAY = frozenset("""and or but who which that whose now today next in at on
with too as when so already nearly exactly almost about boy girl kid child son daughter lad
lass twins baby toddler to from""".split())
# A child is under eighteen, so a grown-up's age is not a count of children when the line does
# not say whose age it is.
CHILD_AGE_UNDER = 18
# "my boys are 4 and 7 years old" says the years once, at the end of the list, so the figure the
# reader sees is the last one of a list the reader for the named group has already read whole.
LIST_BEFORE_IT = re.compile(r"\d{1,3}\s*(?:,|and|, and)\s*$", re.I)
# The rest of a list of ages after the first one: "my brothers are 20 and 24".
A_LIST_OF_AGES = re.compile(r"(?P<ages>\d{1,3}(?:\s*(?:,|and|, and)\s*\d{1,3})+)\b", re.I)


GROUP_NAMED = re.compile(r"\b(?:" + "|".join(KID_GROUP) + r")\b", re.I)
# The thing an age belongs to is often a clause away from the number: "it's a front loader,
# about five years old" put the whole of "a front loader," between the pronoun and the years, so
# the two guards above (which reach 12 characters back) sailed past it and the store filed a
# five-year-old child. On the same chat the store then answered "how many kids do i have" with
# "You've got one kid." about a child nobody had. So the subject is read back to the last thing
# the line named, and a line with no people word in it at all cannot be counting children.
THING_NAMED_BACK = re.compile(
    r"\b(?:it|its|it's|that|thats|that's|this|these|those|there|they|theyre|they're)\b"
    r"|\b(?:my|our|your|his|her|their|the)\s+(?P<noun>[a-z' ]{1,30}?)\s*"
    r"(?:is|was|are|were|s|'s)\b", re.I)
PEOPLE_NAMED_ANYWHERE = re.compile(r"\b(?:" + "|".join(sorted(PEOPLE_AGED)) + r")\b", re.I)
# How far back the subject of an age is worth looking for: one short clause and the thing it
# named ("my old washing machine, a front loader, about five years old").
SUBJECT_REACH = 80


# The nouns an age in years is said of, and the "is" that puts the age after them, with the
# appositive people really use in between: "my washing machine is a front loader, about 4 years
# old". The window is wide because the words between the thing and the figure are the point of
# the sentence - a make, a model or a type - and the reader that can only see twelve characters
# past the "is" filed a four year old child for a four year old washing machine, and the turn
# after asked the person about the kid.
_A_THING_SAID_IS = re.compile(
    r"\b(?:my|our|your|his|her|their|the)\s+(?P<noun>[a-z' 0-9]{1,30}?)\s*"
    r"(?:is|was|are|were|s|'s)\b[^.!?]{0,40}$", re.I)
# The same, said with a pronoun: "its a front loader, about 4 years old", "thats a band new one,
# two years old". No noun is named, so the pronoun is the subject and whatever it points at is
# the thing, because a person is named rather than pointed at when their age is given.
_A_THING_POINTED_AT = re.compile(
    r"\b(?:it|its|it's|that|thats|that's|this|these|those|there|theyre|they're|mine|ours)\b"
    r"[^.!?]{0,40}$", re.I)


def _the_years_are_a_things(text):
    """Whether every age in years on the line belongs to a thing rather than to a child.

    A line can age a person and a thing together ("my son is 4 and the dog is 6 years old"), and
    one thing aged on it is not enough to drop the children the line counts - so every figure has
    to be a thing's before the reading stands down.
    """
    figures = list(YEAR_OLD.finditer(text))
    if not figures:
        return False
    for match in figures:
        before = text[max(0, match.start() - 80):match.start()]
        words = re.findall(r"[a-z']+", before.lower())
        if PEOPLE_AGED.intersection(words):
            return False
        named = _A_THING_SAID_IS.search(before)
        if named and named.group("noun").split()[-1].lower() not in PEOPLE_AGED:
            continue
        if _A_THING_POINTED_AT.search(before):
            continue
        return False
    return True


def _children_by_year_old(text):
    """The children a line counts in years: {"who": "kids", "ages": [...]}, or None."""
    if not YEAR_OLD.search(text):
        return None
    if _the_years_are_a_things(text):
        return None
    if (not GROUP_NAMED.search(text)
            and re.search(r"\bmy\s+" + _A_PERSON + r"\b", text, re.I)):
        # "my daughter is a 4 year old" names one child, and the reader for the people the line
        # names keeps her age; filing the same number against the children as a group would say
        # "your kids is 4" about a child the line had a name for.
        return None
    group_named = bool(GROUP_NAMED.search(text))
    if group_named and len(YEAR_OLD.findall(text)) > 1:
        # "my boys are 4 and 7 years old" says the years once at the end of the list, and the
        # reader for the group the line named has already read both ages; reading the last one
        # again would put a second, smaller answer about the children on top of it.
        return None
    ages = []
    for match in YEAR_OLD.finditer(text):
        age = int(match.group("age"))
        if not 0 <= age <= 120:
            continue
        if OWN_AGE_BEFORE_IT.search(text[:match.start()]):
            continue
        if not group_named and A_PERSON_AGED.search(
                text[max(0, match.start() - 40):match.start()]):
            # "he is 8 years old" is somebody's age, said the way "hes 8" says it, and the
            # reader for the pronoun keeps it. Counting a child here put a kid in the store the
            # person never mentioned.
            continue
        if YEAR_OLD_ANIMAL is not None and YEAR_OLD_ANIMAL.search(
                text[max(0, match.start() - 24):match.start()]):
            continue
        before = text[max(0, match.start() - 40):match.start()]
        if breeds.BREED_RE.search(before):
            # A breed is the animal it is, and an animal is aged in years: "hes a lurcher, about
            # two years old" is the dog's age. Read as a child it put a kid in the store the
            # person never mentioned - the turn after answered "One kid, two - good to know. Tell
            # me about them.", and the next ask about the dog came back with the children's food.
            continue
        if not PEOPLE_NAMED_ANYWHERE.search(text):
            # Nothing in the line is a person, so the number cannot be a child's age: it is the
            # age of whatever the line was about. "how old is it" is the next question, not "how
            # many kids do you have". This is the same fault the breed guard above fixes for an
            # animal, for every other thing: a machine's age is a whole clause from its name
            # ("it's a front loader, about five years old"), further than the guards under this
            # line can see.
            nearest = None
            for found in THING_NAMED_BACK.finditer(
                    text[max(0, match.start() - SUBJECT_REACH):match.start()]):
                nearest = found
            noun = (nearest.groupdict().get("noun") or "").split() if nearest else []
            if nearest is not None and (not noun or noun[-1].lower() not in PEOPLE_AGED):
                continue
        if group_named and LIST_BEFORE_IT.search(before):
            continue
        if THING_AGED.search(before):
            continue
        qualified = THING_AGED_QUALIFIED.search(before)
        if qualified:
            thing = qualified.group("noun").lower()
            if thing not in PEOPLE_AGED and thing not in PERSON_ELSEWHERE:
                continue
        named = NAMED_THING_AGED.search(before)
        # The thing can be named in more than one word ("my washing machine is 8 years old"), so
        # the noun that is aged is the last word of the phrase in front of the be-form.
        if named and named.group("noun").split()[-1].lower() not in PEOPLE_AGED:
            continue
        after = AFTER_YEAR_OLD.match(text[match.end():])
        if after and not group_named and after.group("word").lower() not in AFTER_YEAR_OLD_OKAY:
            continue
        if age >= CHILD_AGE_UNDER and not group_named:
            continue
        ages.append(age)
    if not ages:
        return None
    return {"who": "kids", "ages": ages} if len(ages) > 1 else {"who": "kids", "age": ages[0]}


def _ages_held(entry):
    """Every age an entry holds, the list and the lone one together, in the order given."""
    held = [age for age in entry.get("ages") or [] if isinstance(age, int)]
    if isinstance(entry.get("age"), int) and entry["age"] not in held:
        held.append(entry["age"])
    return held


def _keep_the_ages(found, entry):
    """Add a reading about a group of children, or fold it into the group already read.

    Two readings of one line of the same children are the same fact however they were worded
    ("my kids are 4 and 7" and "my kids are 4 and 7 years old"), and the fuller reading wins.
    A lone age beside a list is the reading that saw one figure of the list, which is what put
    "7" on the end of "4 and 7" and made the chat answer "Your kids are 7, 4 and 7."
    """
    who = entry.get("who")
    known = next((one for one in found if one.get("who") == who), None)
    if known is None:
        found.append(dict(entry))
        return
    said, held = _ages_held(entry), _ages_held(known)
    if held and said and len(held) >= len(said) and set(said) <= set(held):
        return  # the group already read says everything this reading does
    known.pop("age", None)
    known["ages"] = said if len(said) > 1 else held + [age for age in said if age not in held]
    if len(known["ages"]) == 1:
        known["age"] = known.pop("ages")[0]


def _other_ages(text):
    """[{"who", "age"}] for the people the line gives an age for, or []."""
    text = figures_as_digits(text)
    found = []
    text = stated_not_asked(text)
    if not text:
        return found
    # Longest first, so "my mother in law is 68" is about the mother-in-law and not about a
    # "mother" who is somehow "in law is 68". Unsorted, the shorter relation won and the age was
    # dropped on the floor: the reply said the age back and the store held nothing.
    relations = "|".join(sorted(RELATIONS, key=len, reverse=True))
    # "my mother in law is 68" is a person of her own: the relation keeps its second word, so the
    # age is filed against the mother-in-law instead of being dropped on the floor ("how old is
    # she" then said "You haven't told me how old your mother in law is" about a line that did).
    who_one = r"(?:" + relations + r")(?:\s+in\s+laws?)?"
    # A word that is already a group is a group whether or not a singular of it is in the list
    # above: "my parents are 66 and 70" and "my grandparents are 80 and 82" were read by nothing
    # at all, because this wanted the singular word and then an "s".
    group_two = "grandparents|grandchildren"
    pattern = re.compile(r"\bmy\s+(?:(?P<many>(?:" + who_one + r"|" + group_two
                         + r")s?)\s+are|(?P<one>" + who_one + r")\s*(?:'s|is|was))\s+"
                         r"(?P<age>\d{1,3})\b", re.I)
    # "my son and my daughter are 7 and 4" gives the ages in the order the people come, so the
    # numbers are paired with them rather than one number taken for one person.
    pair = re.compile(r"\bmy\s+(?P<a>" + who_one + r")\s+and\s+(?:my\s+)?(?P<b>"
                      + who_one + r")s?\s+(?:are|is)\s+(?P<ages>\d{1,3}"
                      r"(?:\s*(?:,|and)\s*\d{1,3})+)", re.I)
    for match in pair.finditer(text):
        ages = [int(number) for number in re.findall(r"\d{1,3}", match.group("ages"))]
        if not all(0 <= age <= 120 for age in ages) or len(ages) < 2:
            continue
        for who, age in zip((match.group("a").lower(), match.group("b").lower()), ages):
            entry = next((one for one in found if one.get("who") == who), None)
            if entry is None:
                found.append({"who": who, "age": age})
            else:
                entry["age"] = age
    for kid_pattern in (KID_GROUP_AGES_ARE, KID_COUNT_AGES, KID_ADULTS_AGES):
        for match in kid_pattern.finditer(text):
            ages = [int(number) for number in re.findall(r"\d{1,3}", match.group("ages"))]
            if not ages or not all(0 <= number <= 120 for number in ages):
                continue
            if KID_AGES_NOT.search(text[:match.start("ages")]):
                continue
            if not AGE_TAIL.match(text[match.end():]):
                continue
            who = (match.groupdict().get("who") or "").lower()
            if not who:
                # A reading that names no word for the people is about the children the line has
                # already named, so it joins that group instead of a second one of its own. "my
                # children are 4 and 7" is read twice - once with the word, once by the pattern
                # for a line that only counts them - and the second reading filed "kids" beside
                # "children" on one line of one chat, so "how old are my kids" answered "Your
                # children are 4 and 7 and your kids are 4 and 7."
                who = next((one["who"] for one in found
                            if (one.get("who") or "").lower() in KID_GROUP), "kids")
            # The ages are kept in the order they were said, as one list: the children are a
            # group and the answer says them as one ("your kids are 4 and 7").
            _keep_the_ages(found, {"who": who, "ages": ages} if len(ages) > 1
                           else {"who": who, "age": ages[0]})
    # "my son whos 7 and my daughter whos 4": the clause names the person and gives their age,
    # the same fact as "my son is 7", so the ages are numbers here like every other age the store
    # keeps and "how old are my kids" can list them.
    for match in CHAINED_RELATION_AGE.finditer(text):
        age = int(match.group("age"))
        if not 0 <= age <= 120 or _month_age_after(text, match.end("age")):
            continue
        first = re.sub(r"(?:'s|\u2019s|s)$", "", match.group("first").lower())
        entry = {"who": first + "'s " + match.group("second").lower(), "age": age}
        name = match.groupdict().get("name")
        if name and name.lower() not in _A_WORD_FOR_A_PERSON:
            # "my mums friend julie is 70" gives the pair and her name, so the ask that uses
            # either ("how old is my mums friend", "how old is julie") finds the one age.
            entry["name"] = name
        found.append(entry)
    for match in RELATION_WHOS_AGE.finditer(text):
        age = int(match.group("age"))
        if not 0 <= age <= 120 or _month_age_after(text, match.end()):
            continue
        found.append({"who": match.group("who").lower(), "age": age})
    for match in AGE_TO_COME.finditer(text):
        # The clause is read to the end of the birthday rather than to its start: "shes 70 next
        # month" is the whole line, so the pronoun that says whose age it is sits inside the part
        # read, and reading only what comes before it found no subject at all.
        kind, who = subject(text, match.end())
        if kind != "other" or (who and who not in RELATIONS):
            continue
        age = int(match.group(1))
        if not 0 <= age <= 120:
            continue
        turns = " ".join(match.group(2).lower().split())
        if not who:
            # "my mum is 72 and she is 73 next month": the clause names no relation, but the line
            # does, and the pronoun is that person. Read to the pronoun alone, the birthday would
            # be filed against "she" beside a person called mum, which is two people where the
            # line has one.
            who = _relation_before(text, match.start())
        if who:
            # A birthday folded onto a person the line already gave an age for is the same person
            # said twice: "my mum is 72 and she is 73 next month" keeps 72 as the age she is and
            # "next month" as the day the next one comes, rather than a second entry beside her.
            entry = next((one for one in found if one.get("who") == who), None)
            if entry is not None and not entry.get("turns"):
                entry["turns"] = turns
                if entry.get("age") != age:
                    # "my daughter is 3, she turns 4 next month" gives the age she is and the one
                    # still to come. Keeping only the day left the store saying she turns 3.
                    entry["to_come"] = age
                continue
            found.append({"who": who, "age": age, "turns": turns})
        else:
            # The line gives the age of somebody it never names ("she is 70 next month"). The fact
            # is filed against the pronoun rather than against nobody: an entry with an empty
            # "who" is not a person, and the store points a pronoun at the person the chat is
            # about.
            pronoun = _the_pronoun(text, match.end())
            if pronoun:
                person = _the_person_the_pronoun_is(text, match.start(), pronoun)
                if person:
                    found.append({"who": person, "age": age, "turns": turns})
                else:
                    found.append({"pronoun": pronoun, "age": age, "turns": turns})
    # "my son tom is 7": the name sits between the relation and the age, and the number is still
    # the son's. The name itself is read by `_a_relations_name`, which files it with the same
    # person; here it is only stepped over, and only when it can be a name.
    named = re.compile(r"\bmy\s+(?P<who>" + relations + r")\s+(?P<name>[A-Za-z][a-z'-]{1,19})"
                       r"\s*(?:'s|is|was)\s+(?P<age>\d{1,3})\b", re.I)
    for match in named.finditer(text):
        name = match.group("name")
        if not _may_be_a_name(name):
            continue
        if not AGE_TAIL.match(text[match.end():]):
            continue
        age = int(match.group("age"))
        if not 0 <= age <= 120:
            continue
        who = match.group("who").lower()
        if who.endswith("s") and who[:-1] in RELATIONS:
            who = who[:-1]
        kept = _tidy(name)
        entry = _the_person(found, who, kept)
        if entry is None:
            found.append({"who": who, "name": kept, "age": age})
        else:
            entry.setdefault("name", kept)
            entry["age"] = age
    for match in pattern.finditer(text):
        plural = match.group("many")
        if plural:
            listed = A_LIST_OF_AGES.match(text, match.start("age"))
            if listed:
                ages = [int(number) for number in re.findall(r"\d{1,3}", listed.group("ages"))]
                if (len(ages) > 1 and all(0 <= one <= 120 for one in ages)
                        and AGE_TAIL.match(text[listed.end():])):
                    # One word for the family and two ages said for it: "my brothers are 20 and 24"
                    # was filed as the first figure on the singular word, so the ask answered
                    # "Your brother is 20" - half the fact, in the wrong number. Every ask reader
                    # already keeps a group as a word plus a list of ages (that is how "my kids are
                    # 4 and 7" is answered), so the list is filed that way and said back whole.
                    _keep_the_ages(found, {"who": " ".join(plural.lower().split()), "ages": ages})
                    continue
        rest = text[match.end():]
        if not AGE_TAIL.match(rest):
            continue  # a weight, a height or a span of time, not an age
        age = int(match.group("age"))
        if not 0 <= age <= 120:
            continue
        who = match.group("many") or match.group("one")
        who = " ".join(who.lower().split())
        who = re.sub(r"\bin laws$", "in law", who)
        if who.endswith("s") and who[:-1] in RELATIONS:
            who = who[:-1]  # "my sons are 7" is kept as the son, so "how old is my son" reads it
        entry = _the_person(found, who)
        if entry is None:
            found.append({"who": who, "age": age})
        else:
            # The age the line gives plainly is the age they are now; an entry that already
            # carries a birthday to come keeps the day and takes this as its age.
            if entry.get("turns") and entry.get("age") not in (None, age):
                # "my daughter is 3, she turns 4 next month": the number the entry carried was the
                # birthday still to come, and dropping it left the chat saying she turns 3.
                entry["to_come"] = entry["age"]
            entry["age"] = age
    counted = _children_by_year_old(text)
    if counted:
        _keep_the_ages(found, counted)
    for entry in _kids_named_with_ages(text):
        if not any(one["who"] == entry["who"] and one.get("name") == entry["name"]
                   for one in found):
            found.append(entry)
    return found


def _relation_before(text, pos):
    """The relation the line named most recently before `pos`, or "" for none."""
    who = ""
    for match in re.finditer(r"\bmy\s+(" + "|".join(RELATIONS) + r")\b", text[:pos], re.I):
        who = match.group(1).lower()
    return who


def pet_appositive(text, start=0):
    """The name given for the animal at `start` as an aside ("a rescue dog, biscuit"), or None."""
    animals = [match.start() for match in PETS.finditer(text)]
    later = [position for position in animals if position >= start]
    limit = later[1] if len(later) > 1 else len(text)
    span = text[start:limit]
    match = PET_APPOSITIVE.search(span)
    if not match or not _names_it_aside(match, span):
        return None
    return match.group(1)


BARE_NAME = re.compile(r"^[\W_]*([a-zA-Z][a-zA-Z'-]{1,19})[\W_]*$")
NOT_A_BARE_NAME = frozenset("""
yes yea yeah yep no nope nah ok okay k fine good great thanks thank ta cheers please
hi hello hey bye later maybe sure right true false nothing none neither dunno
sorry sure why what when where who how which it that this there here them him her
""".split())


def names_offered(memory):
    """The names the bot itself put in front of them on the turn before, and what they are for.

    "what should i name it" is answered with three names, and the next line is one of them or a
    name of their own. That turn is a choice, not a fact to look up, so the list is read back
    out of the bot's own reply instead of being written down twice.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return None
    match = NAMES_OFFERED.search(str(turns[-1].get("bot") or ""))
    if not match:
        return None
    names = re.findall(r"[A-Za-z][a-z'-]{1,20}", match.group("list"))
    names = [word for word in names if word.lower() not in ("or", "and")]
    if len(names) < 2:
        return None
    return {"animal": match.group("animal").lower(), "names": names}


def a_name_picked(text, memory):
    """The name given as the answer to the bot's own question or list, or None.

        we got a puppy / What's its name? / biscuit
        what should i name it / For a cat: Miso, Willow or Pepper. / milo
        we got a kitten / what should we name her / pepper

    The word alone says nothing, so it is a name only when the line before it asked for one or
    offered some: anything longer than a word or two ("i dont know", "no idea") is not this, and
    nor is a word the bot never asked about. That is the whole test - the caller decides what to
    do with the name, and the answers lane stands down on it, because a person choosing a name is
    not asking about the food the word also names ("pepper").
    """
    word = bare_name(text)
    if not word:
        return None
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return None
    last = turns[-1]
    asked = str(last.get("bot") or "")
    asked_for_one = (asked.rstrip().rstrip('"').endswith("?")
                     and bool(PET_NAME_ASKED.search(asked)))
    theirs = bool(NAME_PICK_ASK.search(str(last.get("user") or "")))
    if not (asked_for_one or theirs or names_offered(memory)):
        return None
    return word


def bare_name(text):
    """The one word a line is, when the line is nothing but that word: "biscuit", "milo".

    A word on its own says nothing; the question before it is what says it is a name, so this
    only shape-checks the line and leaves the reading to the caller.
    """
    if not isinstance(text, str):
        return None
    match = BARE_NAME.match(text.strip())
    if not match:
        return None
    word = match.group(1)
    low = word.lower()
    if is_addressing(word):
        return None
    if low in NOT_A_BARE_NAME or low in NOT_A_PET_NAME or low in PET_ANIMALS:
        return None
    if not re.search(r"[aeiouy]", low) or re.fullmatch(r"\d+", low):
        return None
    return word

# "shes not vegetarian", "he used to be vegan", "she said she eats meat": the line is not a
# statement that this is how they eat now, so nothing is kept.
NOT_DIET = re.compile(r"\b(?:never|no longer|used to|isnt|isn'?t|arent|aren'?t|said|says|"
                      r"asked|wondered|whether)\b|"
                      # "she's not vegetarian", "he was not vegan": the "not" belongs to the state,
                      # and a bare "does not eat dairy" is the diet itself.
                      r"\b(?:is|are|was|were|(?:he|she|it|they|we|i)(?:'s|s|'re|re)?)\s+not\b",
                      re.I)

# Things that say nothing about what a person eats: "he doesnt eat much", "she doesnt eat
# anything green". A food name has to survive these to be kept.
DIET_STOP = ALLERGY_STOP | frozenset("""much many more anything everything nothing something
food stuff lot any""".split())


def foods_ruled_out(found):
    """Every food a line rules out, for the person or for somebody they named, or [].

    A diet is kept as "no fish", an allergy as "fish", and a line can rule out several ("my son
    cant eat fish and nuts"). The dictionary is what `extract` already returned, so the caller
    does not read the line twice. A limit on a food is the only kind a reply can be built on: the
    words after "cant eat" that name no food are already kept out by `_only_stop_words`.
    """
    if not isinstance(found, dict):
        return []
    foods = []
    match = re.match(r"^\s*no\s+([a-z][a-z ]{1,20}?)\s*$", str(found.get("diet") or ""), re.I)
    if match:
        foods.append(match.group(1))
    # The speaker's own limit, which is kept as an allergy whatever way it was said: "i cant eat
    # chilli" files the chilli, and a reader that only looks at a diet and at other people finds
    # no limit in the line and answers it as nothing (a filler, or a dish with chilli in it).
    mine = found.get("allergies") or ()
    if not isinstance(mine, (list, tuple)):
        mine = [mine]
    foods.extend(str(food).strip() for food in mine if str(food).strip())
    for entry in found.get("others") or ():
        if not isinstance(entry, dict):
            continue
        match = re.match(r"^\s*no\s+([a-z][a-z ]{1,20}?)\s*$",
                         str(entry.get("diet") or ""), re.I)
        if match:
            foods.append(match.group(1))
        allergies = entry.get("allergies") or ()
        if not isinstance(allergies, (list, tuple)):
            allergies = [allergies]
        foods.extend(str(food).strip() for food in allergies if str(food).strip())
    return foods


# The food groups a diet is about: "she doesnt eat dairy" is how she eats, "he wont eat
# vegetables" is a Tuesday at the dinner table.
DIET_GROUP = frozenset("""meat meats fish dairy gluten wheat eggs egg sugar carbs seafood
shellfish pork beef chicken lamb alcohol nuts soya soy""".split())


# A word about not drinking is a limit like a diet, and one said of somebody else is kept against
# that person the same way: "my mate is teetotal" filed nobody, so "what can he have at the do" had
# nothing to answer with. The verb ("my dad doesnt drink") is already read as that person's
# `drinks: False` and is left to it.
OTHER_NO_DRINK = re.compile(
    r"(?<!\w)(?P<subj>(?:my|our|his|her|their)\s+[a-z]+|he|she|they)(?!\w)"
    r"[^.,;!?]{0,24}?"
    r"(?:(?:is|are|'s|'re|s|re)\s+(?:a\s+|an\s+)?"
    r"(?P<word>teetotal(?:ler|lers)?|tee-?total(?:ler|lers)?|non-?drinker|nondrinker)(?!\w))",
    re.I)


def _other_no_drink(text):
    """Who else in the line does not drink, as the person the store keeps: [{...}], or []."""
    found = []
    text = stated_not_asked(text)
    if not text:
        return found
    for match in OTHER_NO_DRINK.finditer(text):
        if NOT_DIET.search(match.group(0)):
            continue
        kind, who = subject(text, match.start("subj"))
        if kind == "":
            # "shes teetotal" is not a pronoun the clause reader knows, but it is still someone
            # else: the subject is the start of this match.
            kind, who = _somebody(match.group("subj"))
        if kind != "other" or who in ANIMALS or who in ("i", "we"):
            continue
        person = _a_person(text, match.end(), who)
        if not person:
            continue
        entry = next((seen for seen in found if _same_person(seen, person)), None)
        if entry is None:
            entry = dict(person)
            found.append(entry)
        entry.setdefault("diet", "no alcohol")
    return found


def _somebody(subject_text):
    """Who a subject phrase names: ("other", "mum") for "my mum", ("other", "") for "shes"."""
    named = re.match(r"(?:my|his|her|their|our)\s+(\w+)", subject_text or "", re.I)
    if named:
        word = named.group(1).lower()
        return "other", SPOKEN_RELATION.get(word, word)
    return "other", ""


def _other_diets(text):
    """What someone else in the line eats: [{"who": "mum", "diet": "no meat"}].

    Only other people: the user's own diet is VEGETARIAN and NO_MEAT above, so "i dont eat meat"
    is still their no_meat and "she doesnt eat meat" is hers. A line that names nobody in
    particular ("they dont eat meat") keeps who "" and is still merged with the last person, the
    same way a bare "hes allergic to nuts" is.
    """
    found = []
    text = stated_not_asked(text)
    if not text:
        return found
    # "my son cant eat nuts" is his allergy, not a diet: the allergy patterns above already have
    # it, and keeping both would say the same thing back twice.
    claimed = [span for pattern in (ALLERGY, CANNOT_EAT, X_ALLERGY)
               for span in (m.span() for m in pattern.finditer(text))]
    for match in OTHER_DIET.finditer(text):
        if any(start < match.end() and match.start() < end for start, end in claimed):
            continue
        word, food = match.group("word"), match.group("food")
        free = match.group("free")
        at = match.start("word") if word else (match.start("free") if free
                                               else match.start("food"))
        kind, who = subject(text, at)
        if kind == "":
            # "shes vegan" is not a pronoun the clause reader knows, but it is still someone
            # else: the subject is the start of this match, not something before it.
            kind, who = _somebody(match.group("subj"))
        if kind != "other" or who in ANIMALS:
            continue
        if NOT_DIET.search(match.group(0)):
            continue
        if free or word:
            # The diet is kept the way the person's own diet is kept, so "my wife is gluten free"
            # and "im gluten free" are the same fact in the same words: a plan said with a
            # space is the same plan as the one said with a hyphen.
            diet = "-".join((free or word).lower().replace("-", " ").split())
        else:
            food = _trim_filler(_finish(food or ""))
            if not food or set(food.split()) & DIET_STOP:
                continue
            # "he wont eat vegetables" is a fussy eater, not a way of eating: a diet names a
            # whole food group, so the vegetable he refused at dinner is not his diet for life.
            if not set(food.split()) & DIET_GROUP:
                continue
            diet = "no " + food
        person = _a_person(text, match.end(), who)
        if not person:
            continue
        entry = next((seen for seen in found if _same_person(seen, person)), None)
        if entry is None:
            entry = dict(person)
            found.append(entry)
        entry.setdefault("diet", diet)
    # "my mate is teetotal" is that person's limit, and it is kept in the same place and the same
    # words as their diet: the store says it back as "your mate doesn't drink alcohol".
    for entry in _other_no_drink(text):
        person = next((seen for seen in found if _same_person(seen, entry)), None)
        if person is None:
            found.append(entry)
        else:
            person.setdefault("diet", entry["diet"])
    return found


# A condition said of somebody else, which the store keeps against that person the same way it
# keeps their allergy or their diet. "my son is coeliac" was only the word "son" and a line in
# the greeting, so the next turn - "what can he eat" - had nothing to answer with and the turn
# after it forgot the boy could not have gluten. The speaker's own conditions are CONDITION
# above; nothing here is ever kept as the user's.
# Both ways people say it: what they are ("my mum is diabetic") and what they have ("my dad has
# diabetes"). The clause has to end after the word, so "my mum has a diabetes appointment on
# tuesday" is an appointment and not a condition - the words after it are what carry the news.
# "high blood pressure" and "crohns" are kept as said: they name no single food, but they are
# what the person has, and a follow-up ask can still be answered honestly with them.
OTHER_CONDITION = re.compile(
    r"(?<!\w)(?P<subj>(?:my|our|his|her|their)\s+[a-z][a-z'\u2019-]*(?:\s+in\s+laws?)?|he|she|they)(?!\w)"
    r"(?:'s|'re|\s+is|\s+are|\s+was|\s+were|s|\s+has|\s+have|\s+got|"
    r"\s+suffers?\s+from|\s+suffering\s+from)\s+(?:a\s+|an\s+)?"
    r"(?P<cond>coeliac|celiac|diabetic|asthmatic|epileptic|anaemic|anemic|"
    r"lactose\s+intolerant|gluten\s+intolerant|"
    r"diabetes|asthma|epilepsy|anaemia|anemia|arthritis|crohn'?s|colitis|ibs|"
    r"high\s+blood\s+pressure|high\s+cholesterol|coeliacs?\s+disease)\b"
    r"(?=\s*(?:[,.;!?]|$|\s+(?:and|but|so|because|which|too|as\s+well|now|since|at\s+the\s+moment)\b))",
    re.I)
# A condition said as what they have is kept as the word for what they are: the reply says "your
# mum is diabetic", which is the same fact in the words the rest of the bot knows it by.
CONDITION_AS_A_WORD = {"diabetes": "diabetic", "asthma": "asthmatic",
                       "epilepsy": "epileptic", "anaemia": "anaemic",
                       "anemia": "anaemic", "anemic": "anaemic", "celiac": "coeliac",
                       "crohns": "crohn's", "crohn": "crohn's",
                       "coeliac disease": "coeliac", "celiac disease": "coeliac",
                       "coeliacs disease": "coeliac"}


def _other_conditions(text):
    """What somebody else has: [{"who": "mum", "condition": "diabetic"}].

    Only other people, and only the condition: "my son is coeliac and cant eat gluten" is his
    condition here and his allergy there, and the two are kept apart the same way a diet and an
    allergy are.
    """
    found = []
    text = stated_not_asked(text)
    if not text:
        return found
    for match in OTHER_CONDITION.finditer(text):
        if NOT_DIET.search(match.group(0)):
            # "he isnt diabetic any more" is a condition taken back, not one to keep.
            continue
        kind, who = subject(text, match.start("cond"))
        if kind == "":
            kind, who = _somebody(match.group("subj"))
        if kind != "other" or who in ANIMALS:
            continue
        cond = " ".join(match.group("cond").lower().split())
        cond = CONDITION_AS_A_WORD.get(cond, cond)
        person = _a_person(text, match.end(), who)
        if not person:
            continue
        entry = next((seen for seen in found if _same_person(seen, person)), None)
        if entry is None:
            entry = dict(person)
            found.append(entry)
        entry.setdefault("condition", cond)
    return found


# What somebody else in the chat does all day, which the store keeps against that person the way
# it keeps their age or their diet. "my sister is a nurse" then "what does my sister do" was a
# search hedge about somebody the chat had been told about a turn before, because every job
# reader here is about the speaker's own work.
# A role is a phrase of ordinary words and it stops where the line turns to something else: a
# connective, a place or a clause. Read as one greedy run, "my mum is a nurse and my dad is a
# builder" named the mum's job as "nurse and my dad is a builder" and never saw the dad at all.
JOB_PHRASE = (r"(?P<job>[a-z][a-z'\u2019-]*"
              r"(?:\s+(?!(?:and|but|so|because|who|that|which|in|at|for|on|with|from|near)\b)"
              r"[a-z][a-z'\u2019-]*){0,3})")
OTHER_JOB = re.compile(
    r"(?<!\w)(?P<subj>(?:my|our|his|her|their)\s+[a-z][a-z'\u2019-]*|he|she|they)"
    r"(?:'s|'re|\s+is|\s+are|\s+was|\s+were|s)\s+(?:a|an)\s+" + JOB_PHRASE, re.I)
# "my brother got a job as a chef", "my mum works as a teacher": the same fact said the other
# way. Only "as" is read: "my mum works in a warehouse" names where she works rather than what
# she does, and saying that back as her job would be a place handed over as a role.
OTHER_JOB_AS = re.compile(
    r"(?<!\w)(?P<subj>(?:my|our|his|her|their)\s+[a-z][a-z'\u2019-]*|he|she|they)"
    r"[^.,;!?]{0,20}?\b(?:job|work|works|working|worked)\s+as\s+(?:an?\s+)?" + JOB_PHRASE,
    re.I)


# The same fact with the person's name between the relation and the verb: "my sister emma is a
# nurse", "our son tom is a teacher". Every other reader of somebody else's fact allows the name
# ("my son jack is 6"), so the job did too little: the word after the relation was the name, the
# pattern wanted the verb, and `my sister emma is a nurse` / `what does my sister do` answered
# that the chat had never been told what she does - while the name itself was dropped as well.
OTHER_JOB_NAMED = re.compile(
    r"(?<!\w)(?P<subj>(?:my|our|his|her|their)\s+[a-z][a-z'\u2019-]*)"
    r"\s+(?P<name>[a-z][a-z'\u2019-]*)"
    r"(?:'s|\s+is|\s+was)\s+(?:a|an)\s+" + JOB_PHRASE, re.I)


def _the_job_phrase(phrase, place_job=False):
    """A job as it is said back: "nurse", "car mechanic", "primary school teacher".

    The same cleaning the speaker's own job gets: the phrase stops where the line turns to
    something else, and a word that judges the person rather than naming a role is not a job.
    """
    cut = _first_tail(phrase, JOB_TAIL_PLACE if place_job else JOB_TAIL)
    if cut:
        phrase = phrase[:cut[0]]
    words = without_the_moment(phrase.split())
    if not words:
        return ""
    first = words[0].lower()
    if (first in JOB_STOP or first in NOT_NAMES or first in NOT_NAMES_EXTRA
            or first in SELF_JUDGEMENT or _is_a_judgement_phrase(words)):
        return ""
    if re.match(r"\d", first):
        return ""
    return _the_role(words)


def _other_jobs(text):
    """What somebody else does: [{"who": "sister", "job": "nurse"}].

    Only other people. "i'm a nurse" is the speaker's own job and stays the store's `job` fact,
    and a line about somebody with no person in it ("she's a nurse" with nobody named before
    it) keeps the pronoun, so the store can put it on the last person it heard about.
    """
    found = []
    for pattern, place_job in ((OTHER_JOB_AS, True), (OTHER_JOB, False), (OTHER_JOB_NAMED, False)):
        for match in pattern.finditer(text):
            at = match.start("job")
            kind, who = subject(text, at)
            if kind != "other":
                continue
            if JOB_WANTED.search(CLAUSE_EDGE.split(text[:at])[-1]):
                # "my brother wants to be a chef" is not his job, and neither is one he is
                # training for: only work the line says somebody does is kept.
                continue
            job = _the_job_phrase(match.group("job"), place_job)
            if not job or job in SOBER_WORDS:
                # "my mum is a teetotaller" is a limit of hers, read above, not what she does.
                continue
            person = dict(_a_person(text, at, who))
            if not person:
                continue
            said = (match.groupdict().get("name") or "").strip()
            # A word that is not a name is not one here either ("my sister in law is a nurse"
            # names a relation, not a woman called In), and a name the chat is given is kept on
            # her entry so a later line can ask about her by it.
            if (said and not _not_a_name(said, strict_ly=False)
                    and _name_after_a_title(said)
                    and said.lower() not in _A_WORD_FOR_A_PERSON):
                person["name"] = _tidy(said)
            entry = next((seen for seen in found if _same_person(seen, person)), None)
            if entry is None:
                entry = dict(person)
                found.append(entry)
            entry.setdefault("job", job)
    return found


def _names_before_a_fact(text):
    """The names a line puts between the animal and what it says about it.

    "my dog max is 4" and "our cat biscuit was 12" name the animal in passing, and the word
    between it and the verb is its name. A word that goes with the animal as a thing ("my dog
    food is expensive") is the thing, not the name, unless the line then says a fact about the
    animal itself ("my cat biscuit is 3").
    """
    found = []
    for match in PET_BEFORE_FACT.finditer(text):
        name = match.group("name")
        if _not_a_name(name, strict_ly=False) or name.lower() in NOT_A_NAME_MIDDLE:
            continue
        if name.lower() in PET_COMPOUND and not AFTER_A_PET.match(text[match.end("name"):]):
            continue
        found.append((match.start("name"), name))
    return found


def pet_name_only(text, lower=False):
    """The name a line gives to a pet it does not name again: "and her name is Biscuit".

    `lower` also reads the name typed without a capital ("and her name is biscuit"). It is for
    the caller that already knows there is a pet on record: there the possessive in front of
    "name" is the whole signal, and the word after it is a name until `_not_a_name` says it is
    not ("his name is long", "his name is the one i forget").
    """
    for match in PET_NAME_ONLY.finditer(text):
        name = match.group(1) or match.group(2) or match.group(3)
        name = _a_name_for_the_pet(name) if name else None
        if name:
            return name
    if lower:
        for match in PET_NAME_ONLY_LOWER.finditer(text):
            # The possessive names the animal and what follows says a name, so a word ending in
            # -ly is a name here, not the adverb the bare rule is right about: "her names
            # actually tilly" kept Tom because Tilly ends in -ly, and Kitty, Molly and Lily are
            # as ordinary a pet name as any.
            name = _a_name_for_the_pet(match.group(1), strict_ly=False)
            if name:
                return name
    return None


def _count_before(text, start):
    """"two cats", "2 dogs", "a couple of rabbits": how many, or 0 when the line does not say."""
    match = PET_COUNT.search(text[:start])
    if not match:
        return 0
    word = match.group(1).lower()
    if word.isdigit():
        return int(word)
    return PET_COUNT_WORDS.get(word, 0)


# How many names a plural animal can be followed by when the line never gave a number: the
# plural says only that there is more than one, so the list is read until the words run out.
MOST_NAMES = 6


def pet_counts(text):
    """The animals a corrected line counts: "3 cats", "two dogs" -> [{"animal", "count"}].

    Read through the same pet reader, so "sorry, 3 cats" counts the cat the person already told
    us about rather than making a second one.
    """
    found = _pets("i have " + str(text or ""))
    return [{"animal": pet["animal"], "count": pet["count"]}
            for pet in found if pet.get("count")]


def _names_after(rest, count, most=None):
    """The names a line lists for the animals it has just counted.

    "two cats, milly and tom" and "two cats called milly and tom" are both two cats; the count is
    what makes the list a list of names, so "two dogs, a lab and a terrier" stays nameless.

    `most` is for the line whose only count is a plural animal: "my cats are called tom, jerry and
    bub" names three, and a guess of two there drops Bub - the same wrong fact as reading one name
    off a line that lists two. So the list is read until the words run out and only the number of
    names the line really supports is kept.
    """
    if count < 2 and not most:
        return []
    target = count if count >= 2 else most
    # "my cats are called tom and jerry", "two dogs named..." - the verb can come before
    # "called", and the plural animal already said how many there are.
    match = re.match(r"\s*(?:(?:are|is|were|was)\s+)?(?:called|named)\s+", rest, re.I)
    if match:
        rest = rest[match.end():]
    else:
        match = re.match(r"\s*[,:]\s*", rest)
        if not match:
            return []
        rest = rest[match.end():]
    names = []
    for piece in re.split(r"\s*(?:,|/|&|\band\b)\s*", rest):
        piece = piece.strip().strip(".!?")
        if not piece or len(piece.split()) != 1:
            break
        if not NAME_WORD.match(piece) or piece.lower() in NOT_A_NAME:
            break
        names.append(piece)
        if len(names) == target:
            break
    if count < 2:
        return names if len(names) >= 2 else []
    return names if len(names) == count else []


# "my neighbour has a dog called Rex": the animal belongs to someone else, and reading it back as
# the user's own would put words in their mouth. "my partner and I got a dog" is still theirs.
OTHER_PET = re.compile(r"\b(?:my|our)\s+(?:[a-z]+\s+){0,2}(?:" + "|".join(RELATIONS) +
                       r")\s+(?:has|have|got|adopted|rescued|bought|owns?|keeps?|"
                       r"doesn'?t have|doesnt have|does not have|don'?t have|dont have|"
                       r"never had|no longer has|had to (?:give|rehome))\b", re.I)


# An animal that is not theirs, said with its owner in front ("my mum's cat died", "the
# neighbour's dog", "sarah's dog was put down") or with where it lives after it ("the cat next
# door", "a cat died in our street", "the dog across the road"). Read as the user's own, a death
# of somebody else's animal takes theirs off the store, and the pet ask is where a person checks
# the bot remembers an animal that is alive.
OWNER_OF = re.compile(r"\b(?:(?:my|our|his|her|their|the)\s+(?:\w+\s+){0,2}?[\w-]+"
                      r"(?:'s|s'|\u2019s))\s+(?:\w+\s+){0,2}$", re.I)
LIVES_ELSEWHERE = re.compile(r"^\s*(?:\w+\s+){0,3}?(?:next door|across the (?:road|street)|"
                             r"in (?:our|the) (?:street|road|village|block)|down the road|"
                             r"from next door|round the corner|up the road)\b", re.I)


# The same owner said without the possessive, which is how most people type it: "the neighbours
# dog", "the family cat", "their dog". A plural is enough - "the neighbours dog" is the same
# animal as "the neighbour's dog" - and the plain word is the only thing saying whose it is.
# "their" is here too: "their dog barks at my kids" is not an animal of the user's, and reading
# it as one is how the store came to answer "Right - no dog, then." a turn later.
# Only the people who are not the household: "the family dog" and "our family cat" are the
# family's own animals, the same as "our dog", so family, kids, mum and the rest are not here.
# A named person with an apostrophe ("my mum's dog", "the kids' rabbit") is read by OWNER_OF.
OTHER_PEOPLE = (r"(?:neighbou?rs?|landlords?|landlad(?:y|ies)|flatmates?|housemates?|roommates?|"
                r"friends?|mates?|colleagues?|boss(?:es)?|owners?|walkers?|someone|somebody|"
                r"anyone|anybody|nobody|people|another)")
OWNER_OF_PLAIN = re.compile(r"\b(?:their|" + OTHER_PEOPLE + r")\s+(?:[a-z]+\s+){0,2}$|"
                            # "someone else's dog", "anyone else's cat": the owner is nobody they
                            # can name, and the apostrophe goes missing as often as not.
                            r"\b(?:someone|somebody|anyone|anybody|nobody)\s+else'?s?\s+"
                            r"(?:[a-z]+\s+){0,2}$", re.I)
# An animal the line names as the person's own ("my dog", "our cat") is theirs whatever else the
# sentence says: "the vet put my dog down" is about their dog, and the vet is who did it.
# "our" is not enough on its own: "our neighbours dog" is still the neighbours' animal, so the
# word after it must not be somebody else. "my kids love our dog" is about their own dog.
OWN_ANIMAL = re.compile(r"\b(?:my|our)\s+(?!(?:" + OTHER_PEOPLE + r")\b)(?:[a-z]+\s+){0,2}$",
                        re.I)


# "we got another cat" is one more of the animals they have, not somebody else's animal: the word
# "another" is on the not-theirs list for "another family's dog" and "a dog of another", and a
# line that says whose hand took the animal on is about their own. Read as somebody else's, the
# second cat was dropped and "we got another cat called Max" left the store with one cat called
# Milo. The verb has to be there, so "i saw another cat in the garden" is still not a new pet.
OURS_ANOTHER = re.compile(r"\b(?:we|i)(?:\s+have|\s*'ve|\s*ve)?\s+(?:just\s+|also\s+)?"
                          r"(?:got|gotten|adopted|rescued|took in|taken in|bought|brought home|"
                          r"rehomed)\s+(?:another|a second|one more|a new)\b", re.I)


# "my brothers cat is called Max", "my mums dog": the apostrophe goes missing as often as it is
# typed, and the animal is the relation's, not the person's. `OWNER_OF` needs the apostrophe, so
# without this the brother's cat went into the store as theirs and took the name of the cat they
# do have. Only the relations who live somewhere else: "my kids cat" and "the family dog" are the
# household's own animals.
KIN_OWNER = re.compile(
    r"\b(?:my|our|his|her|their)\s+(?:brothers?|sisters?|mums?|moms?|mothers?|fathers?|dads?|"
    r"sons?|daughters?|grandmas?|grandads?|grandmothers?|grandfathers?|nans?|uncles?|aunts?|"
    r"cousins?|nephews?|nieces?|in-laws?|parents?|neighbou?rs?|flatmates?|housemates?|"
    r"friends?|step-?(?:mums?|moms?|dads?|sons?|daughters?))\b\s+(?:[a-z]+\s+){0,2}$", re.I)


def _not_their_animal(text, start, end):
    """True when the animal at this position belongs to somebody else, or to nobody."""
    before = text[max(0, start - 40):start]
    # "my brothers cat" is the same shape as "my dog", so the kin word is read first: OWN_ANIMAL
    # would take the animal for theirs on the strength of the "my".
    if KIN_OWNER.search(before):
        return True
    if OWN_ANIMAL.search(before):
        return False
    if OURS_ANOTHER.search(before):
        return False
    return bool(OWNER_OF.search(before) or OWNER_OF_PLAIN.search(before)
                or LIVES_ELSEWHERE.match(text[end:end + 40]))


def _someone_elses(text):
    """The parts of a line where the animal belongs to another person."""
    spans = []
    for match in OTHER_PET.finditer(text):
        end = re.search(r"[.!?;]", text[match.end():])
        spans.append((match.end(), match.end() + end.start() if end else len(text)))
    return spans

# "i don't eat fish", "we cook a chicken", "fish for dinner": the animal is on the plate.
FOOD_BEFORE = re.compile(r"\b(?:eat|eats|eating|ate|without|cook|cooked|cooks|cooking|buy|bought|"
                         r"roast|roasted|grilled|fried|order|ordered|serve|served|avoid|avoids|"
                         r"allergic to|instead of)\s+(?:\w+\s+){0,2}$", re.I)
FOOD_AFTER = re.compile(r"\s+(?:\w+\s+){0,2}?(?:(?:for|as)\s+(?:dinner|lunch|tea|supper|"
                        r"breakfast|christmas|a meal)|tonight|today|tomorrow|last night|"
                        r"this evening)\b", re.I)
# "my cat is called Fish": that word is a name, not a second animal.
NAME_BEFORE = re.compile(r"\b(?:called|named)\s+$", re.I)
# "i got a fish bone out myself", "the cat flap is broken": the animal is part of a compound
# noun, and the head of it is the other word, so nothing says the person keeps the animal. A
# fishbone, dog food and cat litter are all things around the house, not a pet introduced.
PET_COMPOUND = frozenset("""
bone bones food meat fingers finger pie cake cakes sandwich soup stock oil sauce
flap collar lead leash harness bed basket bowl cage hutch tank litter tray
toy toys treats treat biscuit biscuits brush shampoo hair fur vet insurance tag
door house kennel mask net bowlful piece poo mess hairball
""".split())
AFTER_ANIMAL = re.compile(r"[a-z]+")
# "my cat biscuit is 3": biscuit is a thing that goes with a cat and also a name a cat is given,
# so the compound read is only right when the line is about the thing. When the animal is
# introduced with a possessive and the word after it is what the line then says something about,
# the word is the animal's name: "my cat biscuit is 3", "my dog patch has a bad leg".
AFTER_A_PET = re.compile(
    r"\s*(?:(?:is|was)(?:n't|nt)?\s+(?:\d|a\b|an\b|so\b|really\b|very\b|getting\b|not\b)|"
    r"(?:has|had|needs|likes|hates|loves|eats|sleeps|snores|bites|chews|barks|sheds|"
    r"doesn't|doesnt|isn't|isnt)\b)", re.I)
THEIR_ANIMAL = re.compile(r"\b(?:my|our)\s+$", re.I)


# A relation that is somebody else's, not the person's: "my dad has a son" is the dad's son,
# "my sister has two sons" is two grandsons, and "my dad's son is a teacher" is a brother. Filed
# as the person's own, a relative's child answered "how many children do i have" with somebody
# else's, and the count was confidently wrong.
SOMEONE_ELSE_HAS = re.compile(
    r"\b(?:my|our)\s+(?:" + "|".join(RELATIONS) + r")(?:\s*-?\s*in\s*-?\s*laws?)?\b"
    r"(?:\s+\w+){0,2}?\s+(?:has|have|had|got)\b", re.I)
A_RELATION_OWNED = re.compile(
    # "my dad's son", "my sister's two sons", "my mother in laws son": the apostrophe is left off
    # as often as it is typed, and a count can sit between the owner and the person.
    r"\b(?:my|our)\s+(?:" + "|".join(RELATIONS) + r")\b"
    r"(?:\s*-?\s*in\s*-?\s*laws?|['\u2019]s?)"
    r"(?:\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|older|"
    r"younger|elder|eldest|youngest|first|second|third|only|own|other))*\s+$", re.I)


def _people(text):
    """The people this line is about. "my parents evening" is an evening, not the people in it.

    A relation word names someone when it stands on its own in the clause ("my parents are
    coming", "my son's allergy", "I saw my mum"): what gives it away is a noun straight after it.
    """
    found = []
    for relation in RELATIONS:
        for match in re.finditer(r"\b" + relation + r"s?\b", text, re.I):
            after = text[match.end():]
            said_possessive = after.startswith("'s") or after.startswith("s'")
            if said_possessive:
                after = after.split("'", 1)[1][1:]  # "my son's allergy": the son is still a person
            # "my brother-in-law is coming" is the in-law, not the brother: the suffix is the
            # person the line named, and dropping it filed a brother the chat had never mentioned.
            if IN_LAW_AFTER.match(after):
                found.append(relation + " in law")
                break
            words = [word.strip(".,!?;:'") for word in after.split()]
            words = [word for word in words if word]  # a lone "'" is not a word
            next_word = words[0].lower() if words else ""
            if next_word in COMPOUND_AFTER:
                # "my daughters birthday" and "my daughter's birthday" are one fact: the "s" with
                # no apostrophe is the possessive people type out, and reading the whole thing as
                # a compound noun ("my parents evening") left the daughter out of the chat, so the
                # age said for her two turns later ("shes turning 6") had nobody to belong to and
                # "how old is my daughter" answered "You haven't told me". The school evening is
                # the one compound that is genuinely an event rather than a thing of theirs.
                if not ((str(match.group(0)).lower().endswith("s") or said_possessive)
                        and next_word in COMPOUND_THAT_IS_THEIRS):
                    continue
            before = _the_clause_before(text, match.start())
            if SOMEONE_ELSE_HAS.search(before) or A_RELATION_OWNED.search(before):
                # somebody else's relation, said as theirs: the owner is the person the line is
                # about and this one is not the person's own
                continue
            if SELF_AS_A_ROLE.search(text[:match.start()]) and is_a_judgement(text):
                # "im a bad mum" is their own role, judged, not someone they know. A role they
                # are simply stating - "im a mum of two", "im a teacher" - is a fact about the
                # person and is kept, or the store notes it and then says it did not hear it.
                continue
            # "my mother in law" is one person and she is called that: kept as "mother", the
            # next answer about her said "Your mother is vegetarian".
            inlaw = re.match(r"\s+in\s+laws?\b", after, re.I)
            found.append(relation + (" " + " ".join(inlaw.group(0).split()) if inlaw else ""))
            break
    return found


# The things people say are theirs and then ask about later by name. A line that names one of
# these and what it is ("my car is a ford fiesta", "my phone is an iphone 13") says something
# about the person that no other reader keeps, so "what car do i drive" was a hedge about a car
# the chat had been told the model of two turns earlier. The list is the everyday things a
# person names by make or model, not everything anybody owns: a closed list is what keeps "my
# car is old and keeps breaking down" and "my phone is on its way out" from filing a model.
OWNED = frozenset("""car phone mobile iphone laptop bike motorbike motorcycle van tablet ipad
camera tv television boiler oven fridge freezer dishwasher washing-machine tumble-dryer
hoover vacuum mower kettle""".split())
# A make or model of two words is a model: "ford fiesta", "worcester bosch". Three is the most
# anybody says in one breath ("iphone 13 pro max" is four, so the cap is four).
OWNED_VALUE = re.compile(
    # "my car is a ford fiesta", "my phone's an iphone 13", "our boiler is a worcester bosch".
    # The contraction goes with the word: nobody types "my car 's a fiesta", so an apostrophe
    # alternative written after \s+ never matches at all.
    r"\b(?:my|our)\s+(?P<thing>[a-z][a-z-]*)(?:\s+(?:is|was)|\s*'s)\s+(?:a|an|the)\s+"
    r"(?P<value>[a-z0-9][a-z0-9' .+-]{0,31})"
    # "the car i drive is a ford fiesta"
    r"|\bthe\s+(?P<thing2>[a-z][a-z-]*)\s+i\s+(?:drive|ride|use|have|own)\s+(?:is|'s)\s+"
    r"(?:a|an|the)\s+(?P<value2>[a-z0-9][a-z0-9' .+-]{0,31})"
    # "i drive a ford focus", "i ride a boardman"
    r"|\bi\s+(?P<verb>drive|ride)\s+(?:a|an|the)\s+(?P<value3>[a-z0-9][a-z0-9' .+-]{0,31})"
    # "i have a ford fiesta", "i've got an iphone 13": the line names no thing, so only a make
    # can say which thing it is - "i have a focus" stays out, as "a focus" is as likely to be
    # a focus on the week ahead.
    r"|\bi(?:'ve|\u2019ve)?\s+(?:have|got)\s+(?:a|an|the)\s+"
    r"(?P<value4>[a-z0-9][a-z0-9' .+-]{0,31})",
    re.I)
# Words that end the value: a model is a name, so the first word of another clause is not part.
OWNED_STOP = frozenset("""and but so because or plus then which that who what when where why how
if although though while also too as well""".split())
# What a thing is, when it is not a model: "my car is old", "my phone is broken", "the boiler is
# a nightmare". None of these says what make it is, so none of them is kept: the ask about the
# car is answered by saying it has not been told the make, never by "Your car is old".
# The makes people name a thing by, with the kind of thing each one makes and the way it is
# written. The kind does two jobs. It lets "i have an iphone 13" file a phone in a line that
# never says "phone", and it is the brake: an unknown word is no make at all, so "i drive a hard
# bargain" and "my car is a right state" file nothing, and a make of the wrong kind ("my car is
# an iphone") files nothing either. A make with no kind (Bosch, Sony, Samsung) is made by many
# things, so it is taken for whatever thing the line named.
OWNED_MAKES = {
    "ford": ("car", "Ford"), "vauxhall": ("car", "Vauxhall"), "toyota": ("car", "Toyota"),
    "volkswagen": ("car", "Volkswagen"), "vw": ("car", "VW"), "bmw": ("car", "BMW"),
    "audi": ("car", "Audi"), "nissan": ("car", "Nissan"), "honda": ("car", "Honda"),
    "kia": ("car", "Kia"), "hyundai": ("car", "Hyundai"),
    "peugeot": ("car", "Peugeot"), "renault": ("car", "Renault"),
    "citroen": ("car", "Citroen"), "skoda": ("car", "Skoda"), "volvo": ("car", "Volvo"),
    "mini": ("car", "MINI"), "fiat": ("car", "Fiat"), "tesla": ("car", "Tesla"),
    "mazda": ("car", "Mazda"), "suzuki": ("car", "Suzuki"), "jaguar": ("car", "Jaguar"),
    "seat": ("car", "SEAT"), "dacia": ("car", "Dacia"), "lexus": ("car", "Lexus"),
    "mitsubishi": ("car", "Mitsubishi"), "subaru": ("car", "Subaru"),
    "mercedes": ("car", "Mercedes"), "cupra": ("car", "Cupra"),
    "iphone": ("phone", "iPhone"), "oneplus": ("phone", "OnePlus"),
    "pixel": ("phone", "Pixel"), "samsung": ("phone", "Samsung"),
    "motorola": ("phone", "Motorola"), "nokia": ("phone", "Nokia"),
    "xiaomi": ("phone", "Xiaomi"), "redmi": ("phone", "Redmi"), "oppo": ("phone", "Oppo"),
    "huawei": ("phone", "Huawei"), "honor": ("phone", "Honor"),
    "fairphone": ("phone", "Fairphone"),
    "boardman": ("bike", "Boardman"), "carrera": ("bike", "Carrera"),
    "trek": ("bike", "Trek"), "giant": ("bike", "Giant"),
    "brompton": ("bike", "Brompton"), "specialized": ("bike", "Specialized"),
    "ridgeback": ("bike", "Ridgeback"), "voodoo": ("bike", "Voodoo"),
    "cube": ("bike", "Cube"), "scott": ("bike", "Scott"),
    "pinnacle": ("bike", "Pinnacle"), "dawes": ("bike", "Dawes"),
    "worcester": ("boiler", "Worcester"), "vaillant": ("boiler", "Vaillant"),
    "ideal": ("boiler", "Ideal"), "baxi": ("boiler", "Baxi"),
    "viessmann": ("boiler", "Viessmann"), "potterton": ("boiler", "Potterton"),
    "bosch": (None, "Bosch"), "lg": (None, "LG"), "sony": (None, "Sony"),
    "panasonic": (None, "Panasonic"), "philips": (None, "Philips"),
    "dyson": (None, "Dyson"), "hoover": (None, "Hoover"), "miele": (None, "Miele"),
    "smeg": (None, "Smeg"), "aeg": (None, "AEG"), "zanussi": (None, "Zanussi"),
    "beko": (None, "Beko"), "indesit": (None, "Indesit"), "hotpoint": (None, "Hotpoint"),
    "neff": (None, "Neff"), "siemens": (None, "Siemens"), "whirlpool": (None, "Whirlpool"),
    "candy": (None, "Candy"), "shark": (None, "Shark"), "vax": (None, "Vax"),
    "henry": (None, "Henry"), "canon": (None, "Canon"), "nikon": (None, "Nikon"),
    "fujifilm": (None, "Fujifilm"), "olympus": (None, "Olympus"), "dell": (None, "Dell"),
    "lenovo": (None, "Lenovo"), "acer": (None, "Acer"), "asus": (None, "Asus"),
    "toshiba": (None, "Toshiba"), "macbook": (None, "MacBook"), "ipad": (None, "iPad"),
    "ipod": (None, "iPod"), "apple": (None, "Apple"), "surface": (None, "Surface"),
    "razer": (None, "Razer"), "flymo": (None, "Flymo"), "mountfield": (None, "Mountfield"),
    "stihl": (None, "Stihl"), "ryobi": (None, "Ryobi"), "makita": (None, "Makita"),
    "husqvarna": (None, "Husqvarna"), "rangemaster": (None, "Rangemaster"),
    "electrolux": (None, "Electrolux"),
}
# The models people say without the make: "my car is a fiesta", "sorry its a focus". A model is
# only read for a thing the line - or the correction - already says is that kind of thing,
# because "a focus" on its own is as likely to be a focus on the week ahead.
OWNED_MODELS = {
    "fiesta": ("car", "Fiesta"), "focus": ("car", "Focus"), "golf": ("car", "Golf"),
    "corsa": ("car", "Corsa"), "astra": ("car", "Astra"), "polo": ("car", "Polo"),
    "clio": ("car", "Clio"), "micra": ("car", "Micra"), "yaris": ("car", "Yaris"),
    "qashqai": ("car", "Qashqai"), "mondeo": ("car", "Mondeo"),
    "fabia": ("car", "Fabia"), "ibiza": ("car", "Ibiza"),
    "sportage": ("car", "Sportage"), "tucson": ("car", "Tucson"),
    "civic": ("car", "Civic"), "passat": ("car", "Passat"), "octavia": ("car", "Octavia"),
    "transit": ("car", "Transit"),
}
# The kind of thing a word names, for the brake above: a van is a car in the sense that matters
# here, and a motorbike and a bike are one kind.
OWNED_KIND = {"car": "car", "van": "car", "bike": "bike", "motorbike": "bike",
              "motorcycle": "bike", "phone": "phone", "mobile": "phone", "boiler": "boiler"}
OWNED_NOT_A_MODEL = frozenset("""old new broken dead knackered leaking noisy rubbish great fine
ok okay good bad slow fast heavy light cheap expensive tiny small big rubbish fantastic brilliant
useless amazing lovely horrible awful terrible second third hand handy faulty dodgy nightmare
disaster joke mess dream beauty beast monster bargain steal ripoff wreck banger shed pain on mine
yours theirs ours its""".split())


# A line that opens with an asking word asks: "what car do i drive" is not "i drive a focus".
# Only the opening word counts, because the words that ask sit inside statements too - "is" in
# "my car is a ford fiesta", "do" in "i do like it" - and a statement read as a question files
# nothing at all.
OPENS_AN_ASK = re.compile(r"^(?:what|which|who|whom|whose|how|where|when|why|do|does|did|is|are|"
                          r"was|were|can|could|would|should|shall|will|have|has)\b", re.I)
TELLS_ABOUT = re.compile(r"^(?:my|our|the|i|we|he|she|they)\b", re.I)


def _a_question(text):
    """Whether the line asks rather than tells: "what car do i drive" is not "i drive a focus"."""
    low = str(text or "").strip()
    if OPENS_AN_ASK.match(low):
        return True
    return low.endswith("?") and not TELLS_ABOUT.match(low)


def _owns(text):
    """What the person says they have, by the name of the thing: {"car": "Ford Fiesta"}.

    Only a line that names a thing and its make or model is read - "my car is a ford fiesta",
    "i drive a ford focus", "i've got an iphone 13" - and only for the closed list of things
    people name that way. A line that asks is not a statement of one, so "what car do i drive"
    files nothing, and a word that is not a make files nothing either.
    """
    if not text or _a_question(text):
        return {}
    found = {}
    for match in OWNED_VALUE.finditer(text):
        thing = (match.group("thing") or match.group("thing2") or "").lower()
        said = (match.group("value") or match.group("value2") or match.group("value3")
                or match.group("value4") or "")
        if not thing and match.group("value4"):
            # "i have a ford fiesta" names no thing, so the make says which one it is: only a
            # make can, and a make of no one kind ("i have a bosch") says nothing at all.
            thing = _the_thing_of(match.group("value4"))
        if not thing:
            # The verb says which thing it is: "i drive" a car, "i ride" a bike.
            thing = {"drive": "car", "ride": "bike"}.get((match.group("verb") or "").lower(), "")
        thing = thing.replace("-", " ")
        if thing not in OWNED or thing in found:
            continue
        value = _the_model(said, thing)
        if value:
            found[thing] = value
    return found


def _the_thing_of(value):
    """The thing a make belongs to: "i have a ford fiesta" names a car without saying so."""
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'+-]*", str(value or ""))
    family = (OWNED_MAKES.get(words[0].lower()) or (None, ""))[0] if words else None
    return {"car": "car", "phone": "phone", "bike": "bike", "boiler": "boiler"}.get(family, "")


def _the_model(value, thing=""):
    """The make and model out of what followed the article, or "" when it is not one.

    "a ford fiesta and a bike rack" is a Fiesta: the value stops at the word that starts the next
    clause. "old" and "broken" are what the thing is like, not what it is, and a word that is no
    make or model is nothing either - "a right state" and "a hard bargain" file nothing, which is
    what stops the store answering "You drive a Hard Bargain."
    """
    words = []
    for word in re.findall(r"[A-Za-z0-9][A-Za-z0-9'+-]*", str(value or "")):
        if word.lower() in OWNED_STOP or len(words) == 4:
            break
        words.append(word)
    words = without_the_moment(words)  # "a corsa now" is a Corsa, not a "Corsa Now"
    if not words:
        return ""
    first = words[0].lower()
    if first in OWNED_NOT_A_MODEL:
        return ""
    kind = OWNED_KIND.get(str(thing or "").lower(), "")
    make = OWNED_MAKES.get(first)
    if make:
        # A make of the wrong kind is not this thing's make: "my car is an iphone".
        if kind and make[0] and make[0] != kind:
            return ""
        return _spell_the_model(words)
    model = OWNED_MODELS.get(first)
    # A model is only read for a thing the line already named as that kind of thing.
    if not model or not kind or model[0] != kind:
        return ""
    return _spell_the_model(words)


def _spell_the_model(words):
    """The value written the way a name is: "ford fiesta" -> "Ford Fiesta", "bmw" -> "BMW"."""
    spelled = []
    for word in words:
        known = OWNED_MAKES.get(word.lower()) or OWNED_MODELS.get(word.lower())
        spelled.append(known[1] if known else word[:1].upper() + word[1:])
    return " ".join(spelled)


def _a_name_given_by_the_verb(word):
    """True when the word after "we named the cat ..." is the name and not the rest of a sentence.

    A name is a word the line gives the animal: "after my grandma" is who it was named *after*,
    "in for dinner" is where it was called, and "him" is the animal itself.
    """
    word = str(word or "").strip()
    low = word.lower()
    if low in NOT_A_NAME or low in NOT_THE_VERB_NAME or low in NOT_A_PRONOUN_NAME:
        return False
    return bool(NAME_WORD.match(word))


# A puppy is a dog and a kitten is a cat. The pet reader keeps the word the person used - people
# say "my puppy is a spaniel" far more often than "my dog is a spaniel" - so the breed's kind and
# the animal's own word were compared as different animals and one pet was filed as two: "You've
# got a puppy and a spaniel. Do they get on?" about the one animal they had just described.
GROWN_UP = {"puppy": "dog", "pup": "dog", "kitten": "cat", "kitty": "cat"}


def _the_same_animal(one, other):
    """Whether two names for a kind of animal are the same animal."""
    return GROWN_UP.get(one, one) == GROWN_UP.get(other, other)


def _with_the_breed(pet, breed):
    """The record, with the breed the line named kept beside the kind of animal it is.

    The store compares one pet with another by `animal` ("my dog" and "my greyhound" are the same
    dog), so the kind is what goes there; the breed is what lets a reply say the word they used.
    """
    if breed:
        pet["breed"] = breed
    return pet


def _pets(text, question=False):
    """The animals a line introduces, with the names it gives them.

    A question names no pet: "what is my dog called?" asks, and storing a second, nameless "dog"
    from it would make the recall read "dog and dog". A question gives no name either: the
    lowercase "again" in "what's my dog called again?" is not a name.
    """
    theirs = _someone_elses(text)
    names = [(_name_at(match), _with_title(match)) for match in PET_NAME.finditer(text)]
    names += [(_name_at(match), _with_title(match)) for match in PET_VERB_NAME.finditer(text)
              if _a_name_given_by_the_verb(match.group("name"))
              and (match.group("whose") or "").lower() not in NOT_THEIR_DETERMINER]
    names += [(match.start(1), match.group(1)) for match in PET_PRONOUN_NAME.finditer(text)
              if _a_name_given_by_the_verb(match.group(1))]
    names += [found for found in _names_before_a_fact(text)
              if found[1] not in [name for _, name in names]]
    names += [(_name_at(match), _with_title(match)) for match in PET_IS_NAME.finditer(text)
              if _with_title(match) not in [name for _, name in names]]
    names += [(match.start("name"), _with_title(match))
              for match in PET_POSSESSIVE_NAME.finditer(text)
              if _a_name_for_the_pet(match.group("name"), strict_ly=False)
              and _with_title(match) not in [name for _, name in names]]
    names += [(match.start(1), match.group(1)) for match in PET_APPOSITIVE.finditer(text)
              if _names_it_aside(match, text)]
    # "called again" in "what's my dog called again?" names no pet: a name is a word of its own,
    # not the grammar of the ask
    names = [(position, name) for position, name in names if name.lower() not in NOT_A_NAME]
    names.sort()
    if question:
        names = [(position, name) for position, name in names if name[:1].isupper()]
    # A name belongs to the animal it follows and comes before the next one: "a dog and a cat
    # called Tom" names the cat, not the dog. Another person's pet is not the user's: "my
    # neighbour has a dog called Rex" says nothing about what the user has.
    # The name just given is not another animal: "my cat is called Fish" names one cat, and
    # reading "Fish" as a second one left the cat unnamed, so "what is my cat called" answered
    # "you haven't told me a name for your cat yet" about a cat the line had just named.
    named_at = {position for position, _ in names}
    animals = [[match.start(), match.end(), match.group(1).lower(), ""]
               for match in PETS.finditer(text)
               if not any(start <= match.start() < stop for start, stop in theirs)
               and match.start() not in named_at]
    # A breed is the animal it is. "we got a rescue greyhound last week" told the store nothing,
    # so "what pets do i have" answered "You haven't told me about a pet yet" about a dog the
    # person had just described, and "my labrador is 4" lost the age for the same reason: the
    # pet reader only knew the animal's own word. The breed is kept beside the kind, so the
    # store compares `animal` with `animal` as it always did and can still say the word they used.
    one_of_the_group = set()  # starts where the breed named one animal of a group
    for match in breeds.BREED_RE.finditer(text):
        if any(start <= match.start() < stop for start, stop in theirs):
            continue
        if match.start() in named_at:
            continue
        breed = breeds.the_breed_named(match.group(0))
        kind = breeds.BREED_KIND.get(breed, "")
        if not kind:
            continue
        # The word has to be said as an animal: "im husky" is a voice, and the store filed a dog
        # for it and answered "A husky - is it good company?" about the person.
        if not breeds.a_frame_before(text, match.start()):
            continue
        # "the greyhound bus is late", "greyhound racing on saturday": the breed names something
        # else here, and the word after it is what says so.
        after = re.match(r"[\s-]*([a-z]+)", text[match.end():match.end() + 24])
        if after and after.group(1).lower() in breeds.NOT_A_CREATURE_NEXT:
            continue
        # A breed said beside the animal's own word is the same animal: "my cat, a tabby, is 3",
        # "my dog is called miss and she is a spaniel" and "we have two dogs, a lab and a terrier"
        # each describe one pet, and reading the breed as a second animal left the store holding
        # two records and the reply counting two where the person had said one.
        beside = [entry for entry in animals if _the_same_animal(entry[2], kind)
                  and abs(entry[0] - match.start()) <= 40]
        if beside:
            closest = min(beside, key=lambda entry: abs(entry[0] - match.start()))
            # A breed beside a group is the breed of one of them, not of the group: "we have two
            # dogs, a lab and a terrier" was kept as two terriers, and the reply said "Two
            # terriers. Who's in charge?" about a lab and a terrier. The breed stays on the
            # record - the words were said, and the ack reads them to see the line added nothing
            # else - but it is marked as one of the group, so what is said back is the kind:
            # "two dogs". A breed said as the group itself ("we have two greyhounds") is not
            # marked, so the word they used is still the word said back.
            if not closest[3]:
                closest[3] = breed
                if _count_before(text, closest[0]) > 1:
                    one_of_the_group.add(closest[0])
            continue
        animals.append([match.start(), match.end(), kind, breed])
    animals.sort()
    pets = []
    # One animal in the line is the only one a description and a figure can both be about:
    # "we have two dogs, 3 and 5" gives two ages in one clause (`_names_after`), not one.
    one_animal = len(animals) == 1
    for index, (start, end, animal, breed) in enumerate(animals):
        limit = animals[index + 1][0] if index + 1 < len(animals) else len(text)
        # "we got another cat called Max" beside a cat they already have is a second cat; the same
        # words without "another" are the cat they have, named again. Read here rather than in the
        # store, which sees only the animal and the name; bot/memory/remember decides with it.
        before = text[max(0, start - 60):start]
        second = bool(ANOTHER_ANIMAL.search(before) or ALSO_HAVE.search(before))
        # "i don't eat fish", "we had chicken for dinner": the animal is on the plate, not in the
        # house, so it is a diet and not a pet.
        if FOOD_BEFORE.search(text[max(0, start - 30):start]):
            continue
        # "i love dogs", "not keen on rabbit": a taste, not a pet ("we love our dog" is both, and
        # taste.said_about keeps the pet there because the possessive says which animal it is).
        if taste.said_about(text, start):
            continue
        if FOOD_AFTER.match(text[end:end + 30]):
            continue
        # The head of the phrase is the word after the animal, not the animal: "a fish bone"
        # is a bone, so the line says nothing about a pet. Two shapes hide here. "a fish bone",
        # "the dog bowl" is not a pet at all. "my dog food is expensive", "my cat litter costs a
        # fortune" is a pet, said through a thing of theirs: the compound is not the pet's name,
        # but the animal is still theirs, so it is kept and left unnamed rather than dropped.
        after = re.match(r"\s*([a-z]+)(.{0,40})", text[end:], re.S)
        compound_they_have = False
        if after and after.group(1).lower() in PET_COMPOUND:
            named = (THEIR_ANIMAL.search(text[max(0, start - 12):start])
                     and AFTER_A_PET.match(after.group(2)))
            if not named:
                if not THEIR_ANIMAL.search(text[max(0, start - 12):start]):
                    continue
                compound_they_have = True
        if NAME_BEFORE.search(text[max(0, start - 12):start]):
            continue
        # An animal they want, dislike or had once is not an animal they have, and a line that
        # says they have not got one adds nothing: "i dont have a cat" used to store a cat and
        # then take it back, so "what pets do i have" answered "you don't have your cat any more".
        # The record still goes out, marked, so the line can be said back to them ("Noted: you
        # don't want a dog"): bot/memory/remember keeps only the ones that are theirs.
        if _not_their_animal(text, start, end):
            # "my mum's cat is called Tom" tells us about a cat the person does not have.
            pets.append(_with_the_breed(_not_theirs(animal, text, start, end), breed))
            continue
        clause = CLAUSE_EDGE.split(text[max(0, start - 60):start])[-1]
        if (_only_wanted(text, start, end)
                or NOT_HAVE.search(clause)
                or WITHOUT_ANIMAL.search(clause)
                # "not the dog" is the same take-back as "i don't have a dog": reading it as a
                # pet left the store holding a dog the line had just taken back, and a second
                # reader then filed that dog under `pets_gone` as a loss they never had.
                or NOT_JUST.search(clause)
                # "forget the dog", "no dog": a take-back names the animal, so the line is not
                # introducing it.
                or taken_back_before(text, start)):
            pets.append(_with_the_breed(_not_theirs(animal, text, start, end), breed))
            continue
        # An animal on its way is not one in the house: "we are getting a puppy next week" is a
        # plan, and the store claiming the puppy answered "You've got a puppy" about one still
        # with its mother. It is read as theirs and marked, because the follow-ups need it ("what
        # do i need to buy first", "will they get on") and only the sentence said back changes.
        coming = _coming_home(text, start)
        count = _count_before(text, start)
        # "my cats are called tom and jerry" is two cats and two names: the plural animal is the
        # only thing that says there is more than one, and without it the second name was dropped
        # and "what are my cats called" answered "you've got a cat called tom". It says nothing
        # about how many, so the list is read for as many names as the line gives.
        plural = count < 2 and text[start:end].lower().endswith("s")
        listed = _names_after(text[end:limit], count, most=MOST_NAMES if plural else None)
        if compound_they_have:
            # "my dog food is expensive": the compound is a thing of theirs, not a name.
            listed = []
        if question:
            listed = [name for name in listed if name[:1].isupper()]
        if listed:
            pets.extend(_with_the_breed({"animal": animal, "name": name,
                                         **({"coming": True} if coming else {})}, breed)
                        for name in listed)
            for name in listed:
                if name in names:
                    names.remove(name)
            continue
        name = None
        for position, candidate in list(names):
            if end <= position < limit:
                name = candidate
                names.remove((position, candidate))
                break
        if question and not name:
            # A word after the animal in commas introduced the animal, even when the word is not
            # a name: "our dog, mate, is 4" has told us there is a dog, and dropping it makes the
            # next turn answer "what's my dog called?" with "you haven't told me about a pet".
            if PET_APPOSITIVE.search(text[start:limit]) is None:
                continue
        if not name and count > 0:
            # "i have two cats" names no animal one at a time, so the number is the only thing
            # that says how many there are. Without it "one of them died" empties the house, and
            # "we have two cats" then "sorry, 1 cat" cannot move the count down to one either:
            # a number the line really gave for that animal is kept, even when it is one.
            pet = {"animal": animal, "name": name, "count": count}
        else:
            pet = {"animal": animal, "name": name}
        if coming:
            pet["coming"] = True
        # "my dog is 5", "my dog max is 4": how old the animal is is a fact of theirs like any
        # other, so it is kept with the animal and a later "how old is max" has an answer.
        age = _pet_age(text[end:limit])
        if not age and one_animal and not pet.get("count"):
            # The figure said after what the animal is: "hes a labrador, 9", "my dog is a
            # spaniel and hes 11", "she is a tabby, 3 years". The breed line is the animal's
            # own record, and the figure that follows it belongs to the same animal - without
            # this it was filed against nobody and "what did i tell you his age was" said the
            # chat had never been told, about an age it had just been given.
            age = _pet_age_tail(text[end:limit])
        if age:
            pet["age"] = age[0]
            if age[1]:
                pet["unit"] = age[1]
        if second:
            pet["another"] = True
        if breed and start in one_of_the_group:
            pet["breed_of_one"] = True
        pets.append(_with_the_breed(pet, breed))
    return pets


# The figure a line gives for an animal right after saying what it is: "hes a labrador, 9",
# "my cat is a tabby and she is 3". The comma or the "and" is what makes it the same animal's
# age: a figure set off on its own is a new clause and could be anybody's.
PET_AGE_TAIL = re.compile(
    r"^\s*(?:is\s+(?:a|an)\s+[A-Za-z][A-Za-z'-]{1,19}\s*)?(?:,|\band\b)\s*"
    r"(?:(?:hes|shes|its|theyre|he's|she's|it's|they're|he is|she is|it is|they are)\s+)?"
    r"(?:aged?\s+)?(?P<age>\d{1,2})(?![\d.,]\d)"
    r"(?!\s*(?:kg|kilo\w*|lbs?|pounds?|stone|st|cm|inches?|inch|metres?|meters?|miles?|km|mph|"
    r"hours?|hrs?|mins?|minutes?|percent|%))"
    r"\s*(?P<unit>years?|yrs?|months?|weeks?)?\b", re.I)


def _pet_age_tail(after):
    """The age said after the animal's own description, or None: "hes a labrador, 9".

    Read only where the line gave one animal (`one_animal` in `_pets`), because with two a
    figure cannot say which one it is. `unit` is kept the way `_pet_age` keeps it, so "shes a
    tabby, 6 months" is a kitten and not a six-year-old cat.
    """
    match = PET_AGE_TAIL.match(str(after or ""))
    if not match:
        return None
    age = int(match.group("age"))
    if not 0 < age <= 40:
        return None
    unit = str(match.group("unit") or "").lower()
    return age, ("months" if unit.startswith("month")
                 else "weeks" if unit.startswith("week") else "")


# The figure a line gives for an animal's age: "is 5", "max was 12", "is 3 years old". A figure
# with a weight or a length after it is a measurement ("my dog is 5 kilos"), not an age, and the
# words before the verb are at most the name the line gave the animal.
PET_AGE = re.compile(
    r"^\s*(?:[A-Za-z][A-Za-z'-]{1,19}\s+)?(?:is|was|are|were)\s+(?P<age>\d{1,2})"
    r"(?![\d.,]\d)"
    r"(?!\s*(?:kg|kilo\w*|lbs?|pounds?|stone|st|cm|inches?|inch|metres?|meters?|miles?|km|mph|"
    r"hours?|hrs?|mins?|minutes?|percent|%))"
    r"\s*(?P<unit>years?|yrs?|months?|weeks?)?\b", re.I)


# The same fact said with no verb at all: "hes a labrador, 9 weeks old", "a kitten, 12 weeks".
# The figure is still the animal's age, and without it "how old is the puppy" had nothing to
# answer from although the person had just said how old it was. A unit word is required here,
# because a bare number after the animal ("two cats, one dog") is a count, not an age.
PET_AGE_BARE = re.compile(
    r"^\s*[,;:]?\s*(?:aged\s+)?(?P<age>\d{1,2})\s*(?P<unit>years?|yrs?|months?|weeks?)"
    r"(?:\s*old)?\b", re.I)


def _pet_age(rest):
    """How old the animal is, when the words right after it say so, or None.

    A kitten or a puppy is often given in months, so the unit is kept: "4 months" is an age of
    four months, and reading it as four years says something about the animal that is not true.
    """
    match = PET_AGE.match(rest) or PET_AGE_BARE.match(rest)
    if not match:
        return None
    age = int(match.group("age"))
    if not 0 < age <= 30:
        return None
    unit = (match.group("unit") or "").lower()
    if unit.startswith("month"):
        unit = "months"
    elif unit.startswith("week"):
        unit = "weeks"
    else:
        unit = ""
    return age, unit


# Words people use to address the person they are talking to, not to name an animal: "i got a
# dog, mate" names the dog nothing. The list leaves out the words people do give pets (buddy,
# honey, chief), so a name still lands.
ADDRESSING = frozenset("""
mate matey mates pal fella feller fellas chum cocker bruv bro brother sis sister
love lovey duck ducks petal hun hon dear dearie sunshine lad lass guys folks friend
son daughter dad mum mam mom missus mister sir madam flower
""".split())


def is_addressing(word):
    """Whether a word is how someone addresses a person ("mate", "love"), not a pet's name."""
    return isinstance(word, str) and word.lower() in ADDRESSING


def _names_it_aside(match, text):
    """Whether the word after the animal in commas names it.

    A word that is not a name at all does not ("our dog, mate, is 4"), but one the person wrote
    with a capital and then carried the sentence on with does: "our cat, Flower, is old" is a cat
    called Flower, while "i got a dog, Mate" ends the line and is someone being friendly.
    """
    word = match.group(1)
    if not _not_a_name(word):
        return True
    return word[:1].isupper() and bool(re.search(r"[A-Za-z]", text[match.end():]))


# The words that stand where a name can stand and are certainly not one: "my mum called me
# yesterday", "my sister named her baby after me", "my son is called after his dad".
NOT_A_NAME_EITHER = frozenset((
    "me", "her", "him", "us", "them", "you", "my", "your", "his", "hers", "its", "it", "this",
    "that", "these", "those", "who", "what", "which", "someone", "somebody", "anyone", "anybody",
    "everyone", "everybody", "nobody", "something", "anything", "nothing", "after", "for", "by",
    "with", "from", "up", "out", "back", "there", "here", "then", "not", "never", "still",
    "also", "too", "either", "both", "all",
))


# A describing word is not a name: "my mum is amazing" is a compliment, and "Your mum is called
# Amazing" puts a word in the person's mouth. The test is the shape of the word rather than a
# list of every adjective - the endings no name carries (-ing, -ous, -ful, -less, -ness, -able,
# -ible, -ity, -tion, -sion) plus -ed, which only Fred, Ned, Ted, Ed and Jed keep - because a
# person's name is the one word in the line that nothing else in the language explains.
DESCRIBING_ENDS = ("ing", "ous", "ful", "less", "ness", "able", "ible", "ity", "ation",
                   "ition", "sion")
# The everyday describing words with no ending to go on: "my dad is stubborn", "my sister is
# overweight". Words ending in -y are here rather than in the endings above, because Daisy, Lucy
# and Poppy are names and a -y means nothing on its own.
# A relationship and a shape, and the two comparisons: "im taken" is a relationship rather
# than an introduction, and "im best at maths" answered "Nice to meet you, Best" too.
DESCRIBING_WORDS = frozenset("""
clever stubborn overweight underweight thin tall short fat skinny slim lazy happy sad funny angry
hungry thirsty pretty ugly smelly messy noisy silly busy cheeky grumpy sleepy cranky dizzy clumsy
greedy greedy wealthy healthy rocky risky shaky steep bumpy itchy sweaty queasy tipsy
nosey spoiled bratty mardy stroppy sulky clingy fit unfit taken best worst
""".split()) | NOT_A_NAME_DESCRIBING
# -ed is an adjective's ending too, and these are the names it would otherwise swallow.
ED_NAMES = frozenset("fred ed ned ted jed".split())


def _describes_them(word):
    """Whether a word says how somebody is rather than what they are called."""
    low = str(word or "").lower()
    if not low:
        return False
    if low in STATE_WORDS or low in DESCRIBING_WORDS or low in lexicon.A_STATE:
        return True
    if low in DIET_WORDS or low in DIET_NAMES or low in DIET_FREE_WORDS or low in SOBER_WORDS:
        # "my mum is dairy free" and "my veggie sister" say what she eats, so the word is not her
        # name: read as one, the store told the person their mum was called Dairy.
        return True
    if low in ED_NAMES:
        return False
    if low.endswith("ed") and len(low) > 3:
        return True
    return any(low.endswith(end) and len(low) > len(end) + 2 for end in DESCRIBING_ENDS)


# The words a line says *about* a name rather than a name: "my daughters name" ends in the word
# itself, and filed as one the bot tells the person their daughter is called Name. Nothing in
# the line names anybody.
NOT_A_NAME_WORD = frozenset("""name names nickname called known ages age""".split())


def _bare_name(word, pair=False):
    """The name a line gives without the naming verb, or "" when the word is something else.

    "my mum is sue" names the mum; "my mum is tired" and "my brother is older" say how they are,
    and filing "Tired" as a name would be worse than holding nothing at all. The test is the
    bot's own word list: a word it already knows is the word it is, and a word it does not know
    - or one typed with a capital, the way a name is written - is the person's name. Tom, Rose
    and Sam are ordinary words as well as names, so those are read only from a capital.

    `pair` is for a line that gives two of them at once - "my mum and dad are dave and sue", "my
    kids are ada 7 and sam 4". Two names side by side is the line's own sign that the words are
    names, so a word the lexicon knows is taken as one there.
    """
    said = str(word or "").strip().strip(".,!?;:'\"")
    low = said.lower()
    if not re.fullmatch(r"[a-z][a-z'-]{1,19}", low):
        return ""
    if _not_a_name(said, strict_ly=False):
        return ""
    if low in WORD_NUMBERS:
        # "my son is seven" is an age written out, and Seven is nobody's name.
        return ""
    if low in NOT_A_NAME_WORD:
        # "my daughters name" is a question with the verb left off, not a person called Name.
        return ""
    if is_a_contraction(low):
        return ""
    if low in lexicon.COMMON_NAMES or low in NAMES_THAT_END_LIKE_A_VERB:
        # A name typed in lower case is still a name. "my husband is tom" filed the husband with
        # no name - though the bot had just said "Noted: your husband is tom." - so the next ask,
        # "whats my husbands name", answered "You haven't told me your husband's name." People
        # type the name the way they type everything else; the reading already knows these words
        # are names (the same list that keeps "hi im lisa" an introduction), so the capital is
        # not needed to tell them from a state. A word that only says how somebody is ("tired",
        # "late", "asleep") is not on that list and is turned down below, as before.
        return _tidy(_finish(said))
    if not said[:1].isupper() and _describes_them(low):
        # A capital is how a name is written, so "my mum is Sue" is her name whatever else the
        # word means; without one, a word that says how somebody is says nothing about a name.
        return ""
    if not pair and low in normalize.LEXICON and not said[:1].isupper():
        return ""
    return _tidy(_finish(said))


# Every word the understanding lane keeps as ordinary English, so the store can tell a word with
# a job in the sentence ("its complicated", "its the plumber") from a word that only has the job
# of being somebody's name. Read once, because it is asked on every correction of a name.
COMMON_WORDS = frozenset(lexicon.COMMON.split()) | frozenset(lexicon.CORE_WORDS) | lexicon.A_STATE


# The endings a describing word wears and a name rarely does: "complicated", "amazing", "real".
NOT_A_NAME_ENDINGS = ("ed", "ing", "ous", "ful", "less", "ish", "able", "ible", "ive", "est", "ly",
                      "al", "ic")


def a_name_could_be(word):
    """Whether a single word could be somebody's name, with nothing else in the line to say so.

    People put a name right with the name and no other words: "no its dave", "i meant dave",
    "sorry, dave". Nothing in the line says the word is a name, so the word itself has to hold
    up: one word, not a word the bot reads as language ("fine", "tired", "complicated",
    "plumber"), and not a month or a day. A word kept as a first name wins even when it is an
    ordinary word as well ("grace", "hope", "rob"), because that is what those names are.
    """
    low = str(word or "").strip().lower()
    if not re.fullmatch(r"[a-z][a-z'-]{1,19}", low):
        return False
    if low in MONTHS or low in DAYS:
        return False
    if low in lexicon.COMMON_NAMES:
        return True
    if low in NOT_A_PET_NAME or low in NOT_NAMES or low in NOT_NAMES_EXTRA:
        return False
    if low in STATE_WORDS or low in DESCRIBING_WORDS:
        return False  # "its fine", "its complicated", "its rubbish": a word said of the person
    if low not in COMMON_WORDS and low.endswith(NOT_A_NAME_ENDINGS):
        # A describing word that the word lists happen to miss still wears a describing word's
        # ending ("complicated", "amazing", "real"), and names rarely do. Names that do - Lily,
        # Molly, Kelly, Teddy - are in the list of first names, which is read before this.
        return False
    return low not in COMMON_WORDS


# A contraction typed without its apostrophe ("isnt", "arent", "didnt"): the stem is a verb the
# lexicon knows, which is what tells it apart from a name that happens to end in the same letters.
NEGATED_VERB = re.compile(r"^(?P<stem>[a-z]{2,})n['\u2019]?t$")


def is_a_contraction(word):
    """Whether a word is a verb with its "not" written on: "isnt", "arent", "didnt".

    "my son isnt" filed a person called Isnt beside the son - "whats my sons name" answered "Your
    son is called Isnt." - because the word after the relation is read as the name it gives. A
    verb with its "not" written on is one of the things that word can never be.
    """
    low = str(word or "").strip().strip(".,!?;:'\"").lower().replace("\u2019", "'")
    match = NEGATED_VERB.match(low)
    if not match:
        return False
    stem = match.group("stem")
    return stem in normalize.LEXICON or stem + "e" in normalize.LEXICON


def _not_a_name(word, strict_ly=True):
    """Whether a word after the comma is one of the things people say about a pet, not a name.

    A word ending in -ly is an adverb far more often than a name ("our dog, friendly, is 4"), so
    it is turned down. That rule is only safe where the line gives no other sign that the word is
    a name: in "my daughter Emily is 6" the relation and the verb in front of it already say so,
    and Emily, Molly, Kelly and Lily are names. `strict_ly=False` is for those shaped lines.
    """
    low = word.lower()
    if is_addressing(word) or low in NOT_A_PET_NAME or low in NOT_NAMES or low in NOT_NAMES_EXTRA:
        return True
    if low in NOT_A_NAME_EITHER:
        return True  # a pronoun or a preposition is never somebody's name, whatever it follows
    if low in PET_ANIMALS or not re.search(r"[aeiouy]", low):
        return True
    if strict_ly and low.endswith("ly") and len(low) > 4:
        return True
    if _a_word_not_a_name(low):
        # "her name is blonde": a hair colour, a number written out or a state is how somebody
        # is, not what they are called, and every reader of a name asks this guard.
        return True
    return bool(re.fullmatch(r"\d+", low))


def _object_words(rest):
    """The words of a plan's object, once the preposition and the article are out of the way."""
    words = [w for w in re.findall(r"[a-z']+", str(rest or "").lower()) if w not in ARTICLES]
    return [w for w in words if w not in PREPOSITIONS] if words else []


def _object_plan(rest):
    """Whether the rest of a plan is one the verb has to carry.

    Two things say the verb belongs in the plan. The rest opens with a preposition, so on its own
    it says only what the verb is about: "for a bike" is what the money is for, and "You're
    planning to for a bike" is not a sentence. Or the verb took a particle of its own ("writing
    up", "saving up"), which leaves the object needing its verb to mean anything."""
    if not rest:
        return False
    first = re.sub(r"[^a-z]", "", rest.split()[0].lower())
    return first in PREPOSITIONS


def _plan_verb(match, rest):
    """The verb the plan pattern stopped after, when the plan is that verb and its object.

    "i'm saving up for a bike" keeps "saving up": "for a bike" on its own is what the money is
    for, not what they are doing. A plan with a thing straight after the verb ("i'm buying a
    bike") needs no verb, because the thing is the plan."""
    verb = PERSON_OPEN.sub("", match.group(0), count=1).strip(" .")
    words = verb.split()
    if not words or not words[0].lower().endswith("ing"):
        return ""
    if _object_plan(rest) or words[-1].lower() in PARTICLES:
        return verb[:1].upper() + verb[1:]
    return ""


def _a_plan_has_a_thing(rest):
    """Whether the object of the verb names something, rather than pointing at it.

    "saving up for a bike" names the bike; "saving up for it" and "saving up for the one i saw"
    name nothing, so there is no plan to keep and no plan to say back."""
    if not _object_plan(rest):
        return True
    words = _object_words(rest)
    return bool(words) and words[0] not in POINTING


# A question uses the words a plan does: "what do we need to pack?", "how much do i need to save?",
# "do i need to book?". The frame a plan is written with ("i need to", "im going to") is the
# person's own doing only when the clause that carries it is theirs, so a frame that opens its
# clause with an asking word names nothing, and neither does one a wrapper asks the plan for.
PLAN_CLAUSE_BREAK = re.compile(r"[.!?,;:]|\s+(?:and|but|so|then|or)\s+", re.I)
# The words people put in front of a question, which do not make it a statement: "and what do we
# need to take?" asks just as "what do we need to take?" does.
PLAN_CLAUSE_OPENER = re.compile(r"^(?:(?:and|but|so|then|or|ok|okay|also|well|oh|plus|now)\b[ ,]*)*",
                                re.I)


def _asks_about_the_plan(text, at):
    """Whether the plan frame at `at` sits in a question rather than in a statement.

    Two ways it does. A wrapper asks for the plan before naming the frame ("remind me what im
    saving for" was kept as "For" and said back as "You're saving for"), which ASKED_BEFORE
    reads. Or the clause the frame is in opens with an asking word, which is how the rest of the
    asks are worded: "how much do i need to save?" left "Save?", "do i need to book?" left
    "Book?", and "what am i planning?" said "You're planning to save." either way."""
    before = text[:at]
    if ASKED_BEFORE.search(before):
        return True
    clause = PLAN_CLAUSE_BREAK.split(before)[-1]
    clause = PLAN_CLAUSE_OPENER.sub("", clause.strip()).strip()
    return bool(clause) and bool(ASKING.match(clause))


def _plan_text(text, start):
    """The plan itself: from the verb the pattern stopped after, to the end of its clause.

    "I want to save 480 pounds in 6 months, how much should I put away" states the plan and then
    asks a question about it: the plan is the part before the comma, and the rest is the ask.
    """
    rest = text[start:].strip(" ,;:-")
    rest = re.split(r"(?<=[.!?])\s|\s+(?:but|and then|so)\s+", rest, 1)[0].strip(" ,;:-")
    rest = re.split(r",\s+(?:(?:how|what|which|where|when|who|why|should|can|could|would|do|does|"
                    r"is|are|will|any|and)\b)", rest, 1)[0].strip(" ,;:-")
    if not rest:
        return ""
    return rest[0].upper() + rest[1:] if rest else ""


# How the person is, rather than what they are doing. A feeling with a date on it - "im really
# low this week", "i feel awful this week", "im feeling better this week" - is not something
# coming up: the store kept it as a plan, read it back as "Noted: you're really low this week",
# and answered "what are my plans?" with how they felt. The words that can fill the clause
# after the copula are the state adjectives this file already lists, so "im on holiday next
# week" and "im at the dentist on monday" are untouched: a holiday and a dentist are not states.
COPULA = re.compile(
    r"^\W{0,2}(?:i(?:'m| am)|im|i\s+feel|i\s+felt|i(?:'ve| have)\s+been|we(?:'re| are)|were|"
    r"we\s+feel)\s+(?P<rest>.+)$", re.I)
# The words that sit between the copula and the state ("im feeling really low"), and the date,
# which is not part of what they are.
STATE_FILLER = frozenset("""really so very quite pretty rather too still just feeling feel felt
been absolutely completely totally a bit kind of sort of kind sort getting more less somewhat
this that week weekend morning evening afternoon night today tomorrow month year""".split())
# Particles and adverbs that look like a state ("im back", "im online", "im off", "im late") and
# are not: a line about where they are is about something coming up once it carries a date.
STATE_PARTICLE = frozenset("""up down in on at out off away back home here there over around
from with for by of to near into than as after upstairs downstairs online offline asleep awake
outside inside late early soon nearly almost definitely probably maybe honestly seriously
literally actually totally completely absolutely half mid bloody""".split())
# A feeling said plainly that the lists do not carry on their own.
STATE_MORE = frozenset("""low flat blue rough rubbish manky wiped better worse ill sick
                             unwell poorly""".split())
STATE_WORDS = frozenset(
    word for word in (NOT_NAMES_EXTRA | STATE_MORE |
                      frozenset(word for cues in EMOTION_WORDS.values()
                                for cue in cues for word in cue.split()))
    if word not in STATE_PARTICLE)


# "off sick" is an absence, not a mood: "im off sick next week" is a week they are not at work,
# and the store has to keep it as something coming up (happy-linden, #1869: the state reading
# dropped that plan). A word said about being off work is doing, not being.
OFF_ABSENCE = re.compile(r"\boff (?:sick|work|school|college|uni|university|shift|shifts|rota)\b",
                         re.I)
# ...when the absence is still to come ("im off sick next week", "im off work tomorrow"). "im off
# sick this week" is where they are now, so it stays a state and is not filed as something ahead.
OFF_AHEAD = re.compile(r"\bnext\b|\btomorrow\b|\bon\s+(?:mon|tues|wednes|thurs|fri|satur|sun)day"
                       r"|\bin\s+(?:january|february|march|april|may|june|july|august|september"
                       r"|october|november|december)\b", re.I)


def _how_they_are(clause):
    """True when the clause only says how the person is, so a date on it is not a plan."""
    match = COPULA.match(clause)
    if not match:
        return False
    if OFF_ABSENCE.search(match.group("rest")) and OFF_AHEAD.search(clause):
        return False  # "im off sick next week" is a week at home still to come, not a mood
    rest = " " + match.group("rest").lower() + " "
    rest = re.sub(r"[^a-z' ]", " ", FUTURE.sub(" ", rest))
    words = [word for word in rest.split() if word not in STATE_FILLER]
    words = [word for word in words if word not in STATE_PARTICLE]
    return bool(words) and all(word in STATE_WORDS for word in words)


# The same test for a thing of theirs rather than for them: "my budget is tight this month" and
# "my back has been bad this month" are how things are, and the date on them is when it has been
# like that, not something coming up. Read as a plan, the whole line came back at them as what
# they are doing ("You're planning to my budget is tight this month"), and it took the place of
# the plan they had actually told us: "my budget is tight this month" after "a holiday in spain"
# left the holiday out of `user["plan"]`. The thing, the copula and a state, in that order, is the
# shape; a date or a place after the copula ("my holiday is in august", "the car is in the garage
# on friday") is still a plan, and a doing ("my course starts in september") never gets here.
THING_COPULA = re.compile(
    r"^\W{0,2}(?:my|our|the)\s+[a-z'\u2019\-]+(?:\s+[a-z'\u2019\-]+)?\s+"
    r"(?:is|are|was|were|has been|have been|had been|feels?|felt|seems?|seemed|looks?|looked|"
    r"gets?|got|remains?)\s+(?P<rest>.+)$", re.I)


# A thing of theirs with a date on it is a state only when the predicate says how the thing is
# *today*. A predicate that names something still to come is an event with a date on it, and the
# plan store has to keep it: "my essay is due on friday", "my pay rise is due in april", "my rent
# is going up in may" all name a day, and reading them as states emptied the store (lime-frame,
# #8159: "what am i planning" answered "You haven't told me about anything coming up yet" after
# all three). Same in the other direction for how a thing is now: "broken", "leaking", "playing
# up" were not in the state words, so "my car is broken this month" was filed as a plan.
AHEAD_OF_THE_THING = re.compile(
    r"\b(?:due|booked|scheduled|expected|coming|starting|beginning|renewal|renewed|renewing|"
    r"up\s+for|going\s+up|out\s+on|in\s+for|on\s+order|happening)\b", re.I)
# How a thing of theirs is today. Kept apart from the state words the *person* is read with: a
# broken boiler says nothing about how they are, and "im flat out" is not this reader's business.
THING_TODAY = frozenset("""
    broken bust bursting cracked leaking leaky dripping damp mouldy mouldering rusty
    clogged blocked jammed faulty dead knackered noisy slow patchy scratched chipped wonky
    playing playing-up playin sticking wobbling rattling screeching smoking
    """.replace("playing-up", "playing up").split())


def _how_their_things_are(clause):
    """True when the clause only says how a thing of theirs is, so a date on it is not a plan."""
    match = THING_COPULA.match(clause)
    if not match:
        return False
    raw = match.group("rest").lower()
    if AHEAD_OF_THE_THING.search(raw):
        return False
    rest = " " + raw + " "
    rest = re.sub(r"[^a-z' ]", " ", FUTURE.sub(" ", rest))
    words = [word for word in rest.split() if word not in STATE_FILLER]
    words = [word for word in words if word not in STATE_PARTICLE]
    return bool(words) and all(word in STATE_WORDS or word in THING_TODAY for word in words)


# A thing with a clock on it and no verb: "dentist at 3 on tuesday", "train at 7.15", "lunch
# with sam at 1 on friday", "haircut saturday at 10". This is how people name an appointment;
# every other plan reader here wants a subject ("i'm meeting sam at 6") or a future word
# ("my holiday is in august"), so these lines were read as nothing at all: "dentist at 3 on
# tuesday" got "I'm listening - say more if it helps", and "what time is my dentist" and
# "what time is the train" got a hedge, though the clock was in the line.
#
# The thing, its clock and its day are the arrangement. What keeps a line out is a subject of
# their own (the plan reader has it), a question, a pronoun for the thing ("it's at 3"), and
# anything past ("yesterday", "was", "had").
APPOINTMENT_CLOCK = re.compile(
    r"\b(?:at|around|about|for|by)\s+((?:1[0-2]|0?[1-9])(?:[:.][0-5]\d)?\s*(?:am|pm)?|noon|midday|"
    r"midnight|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b", re.I)
APPOINTMENT_DAY = re.compile(
    r"\b(?:(?:on|this|next)\s+)?(?:mon|tues|wednes|thurs|fri|satur|sun)day\b|\b(?:today|tomorrow|"
    r"tonight|this (?:morning|afternoon|evening))\b|\b(?:(?:on|by)\s+)?" + DAY_AND_MONTH +
    r"\b", re.I)
APPOINTMENT_PAST = re.compile(
    r"\b(?:yesterday|was|were|went|had|did|last (?:night|week|monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday)|ago|already)\b", re.I)
# The thing an appointment is about: a noun or two, never a pronoun standing in for something
# else and never a question word.
# "i start my new job on monday" is the plan reader's line; "my train at 7.15" has no subject in
# front of it, only a thing, and the plan reader does nothing with it.
APPOINTMENT_OWN_SUBJECT = re.compile(
    r"^(?:ok(?:ay)?[, ]+|and |so |but |also |well |oh )*"
    r"(?:i|i'm|im|i've|i'd|id|we|we're|were|we've|weve|we'd)\b", re.I)
# The words that take the last thing back name nothing, so they are never the thing a day is said
# about: "scratch that, saturday" after "im flying to dublin on friday" kept the plan "scratch that
# on saturday", and the store answered "Your scratch that is on Saturday" and moved no date. "make
# that" is the same family - it corrects the line before, it does not begin a plan of its own.
TAKE_BACK_WORDS = re.compile(CORRECTION_TAKEBACK + r"|mak(?:e|ing)\s+(?:that|it)", re.I)
# "anything", "something", "nothing", "everything" and "whatever" are the words a person uses
# when they have not named a thing yet: "anything on tonight" asks what there is, and it was kept
# as the appointment "anything tonight" and said back "You're anything tonight. What do you want
# to have ready for it?"
# The words that stand in for a thing the person has not named: "anything on tonight" was read
# as the plan "anything tonight". They are the placeholder words only. The people words are not
# here - "someone at 3 on tuesday" is still something to be ready for, and a name the person has
# not given yet is not a placeholder ("Somebody at 3 on tuesday" was answered "I'm listening").
APPOINTMENT_NOT_A_THING = frozenset("""it its it's that this he she they them there here we us
i im i'm you what when where which who why how the a an anything something nothing everything
whatever""".split())
# A past-tense verb is what makes a clock line a report of something that has already happened,
# and APPOINTMENT_PAST only knows the time words ("yesterday", "last night"). "the plumber came
# at 9" was kept as the thing "plumber came" and read back "Your plumber came is at 9": the verb
# is in the thing, so the thing is where it is caught. The irregulars come first because no "-ed"
# rule can see them.
APPOINTMENT_PAST_VERB = frozenset("""came went left rang arrived started finished met ate had was
were got sent made saw took gave told said ran sat stood put bought paid brought caught found
kept slept spoke drove flew drank began broke chose fell felt fought heard held hit hurt lost
meant read rode rose sold sang shut spent threw understood woke wore won wrote""".split())
# The same glue in the present: "my shed is coming at 3" would read back "Your shed is coming is
# at 3". A thing that has a verb phrase in it is a sentence, and an appointment's thing is a noun.
APPOINTMENT_A_VERB = frozenset("""is are am be being comes coming arrives arriving leaves leaving
starts starting finishes finishing returns returning waits waiting""".split())
# A verb in front of a date is the verb's own line, not a thing they have on a day: "the shop
# closes december 3" kept as an appointment was said back as "Your shop closes is on December 3".
# The same verb in front of a clock is left alone, because "the pharmacy opens at 9" is a thing
# worth answering and the store already says it the way the person typed it.
APPOINTMENT_A_DATE_VERB = frozenset("""closes closing opens opening begins beginning ends ending
starts starting finishes finishing runs running happens arrives arriving leaves leaving""".split())
# Words that end in "-ed" and are not a verb: a shed and a bed keep a delivery time.
APPOINTMENT_NOT_A_VERB = frozenset("""bed beds shed sheds red seed feed speed need hundred wed
aged kindred moped""".split())
# A line that opens with a word of taking something back is not an appointment of its own: it
# is the dentist's day being put right. Read as a thing with a day on it, "sorry thursday"
# became the thing "sorry" at its own day, and the store then corrected that instead of the
# dentist: "Got it — your sorry is on Thursday", and the appointment still said Tuesday.
APPOINTMENT_CORRECTION = frozenset("""sorry no nope nah actually wait oh ah oops rather instead
wrong not""".split())
# How the day itself is, which is a remark and not a thing anyone has on a day. "hot today",
# "freezing this morning" and "lovely weather today" name nothing the person is going to do, and
# kept as a thing with a day on it they came back as plans: "what have i got coming up" answered
# "You're planning to hot today", and "hot today" then "i might go to the beach" was two things
# ahead of them. The words below are the ones a day is described with, plus the weather itself; a
# thing made only of them is that remark. A thing with anything else in it ("dentist today",
# "the scan tomorrow", "nice meal out on friday") keeps its day.
DAY_REMARK_WORDS = frozenset("""hot cold warm freezing boiling chilly cooler warmer mild sunny
cloudy overcast windy wet rainy foggy misty grey gray bright dull damp humid muggy sticky close
lovely nice horrible awful miserable grim rubbish lousy great good fine better worse busy quiet
long short dark clear beautiful gorgeous stunning glorious pleasant freezing bitter fresh soft
weather rain rains raining snow snowing sun sunshine wind winds windy frost icy ice sleet hail
thunder storm stormy drizzle drizzling pouring showers downpour heatwave freezing""".split())
# The little words that hold a remark together: "lovely weather today", "very hot out today".
DAY_REMARK_GLUE = frozenset("""the a an and but its it is was out in up here there very really so
quite too bit rather enough still again today tonight tomorrow now morning afternoon evening all
day week week's end bit lot much more""".split())


def _the_day_described(thing):
    """True when the thing before the day is how that day is, not something they have on it.

    "hot today" and "lovely weather today" are remarks about the day, and the store that kept
    them as plans said them back as things ahead of the person. Only a thing with no other word
    in it is a remark: "nice meal out on friday" and "dentist today" have a thing of their own
    after the words a day is described with are taken out.
    """
    left = [word.strip(",.!;:'\u2019") for word in str(thing or "").lower().split()]
    left = [word for word in left if word and word not in DAY_REMARK_WORDS
            and word not in DAY_REMARK_GLUE]
    return not left


# The day can also be said first: "december 3 my course starts", "21 october the boiler service is
# booked". Nothing is in front of the day to be the thing, so the thing is the clause after it, cut
# where the clause says what happens on the day. Without this the line kept no plan at all: the
# course was noted as a line that says nothing, and "when does my course start" was answered "No
# date from you on that one".
A_DAY_SAID_FIRST = re.compile(
    r"^(?:on\s+|in\s+)?(?:the\s+)?(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?)?"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2}(?:st|nd|rd|th)?\b", re.I)


# "dinner for 6 on saturday" is six people, not six o'clock. A figure after "for" is a clock only
# when nothing in front of it is what people are counted for - "be there for 6", "booked for 7" -
# and a count when a meal, a table or a party is the thing said before it. Kept as a clock, the
# plan was filed "dinner at 6 on saturday", so "actually make that 8" moved the dinner to eight
# o'clock instead of putting the table up to eight people, and "how many am i cooking for" could
# not be answered at all.
_A_COUNT_NOT_A_CLOCK = re.compile(
    r"\b(?:dinner|lunch|breakfast|brunch|supper|tea|meal|table|tables|party|round|booking|"
    r"seats?|covers|guests?|people|plates?|portions?|helpings?|rooms?)\b", re.I)


def _the_thing_said_after_the_day(low, day):
    """The thing named after a day said at the front of the line, "" when the rest is not a thing.

    The clause tells what happens on the day in its own verb ("my course starts", "the boiler
    service is booked"), so the thing is the clause up to that verb: what is kept is the thing and
    the day, which is the order every other appointment is kept in.
    """
    if day.start() > 4:
        return ""  # the day is not the opening: something in front of it was the thing already
    rest = low[day.end():].strip(" ,;:-")
    rest = re.sub(r"^(?:on|in|at)\s+", "", rest)
    kept = []
    for word in rest.split():
        bare = word.strip(",.!;:")
        if bare in APPOINTMENT_A_VERB or bare in APPOINTMENT_A_DATE_VERB:
            break
        if len(bare) > 3 and bare.endswith("ed") and bare not in APPOINTMENT_NOT_A_VERB:
            break
        kept.append(word)
    thing = " ".join(kept).strip(" ,;:-")
    thing = re.sub(r"^(?:the|my|our|a|an)\s+", "", thing)
    return thing


def _appointment(text):
    """The appointment in a line that names a thing and a time and nothing else.

    "dentist at 3 on tuesday" -> "dentist at 3 on tuesday"; "" for every other line, so the
    plan reader and the deed reader keep every line they had."""
    said = " ".join(text.split()).strip(" .,!;:-")
    words = said.split()
    if not words or "?" in said or len(words) > 12:
        return ""
    low = said.lower()
    if APPOINTMENT_OWN_SUBJECT.match(low):
        return ""  # a line with their own subject in front is the plan reader's
    if ASKING.match(low) or APPOINTMENT_PAST.search(low) or NEGATED.search(low):
        return ""
    if SECOND_PERSON.search(low):
        return ""  # "your appointment is at 3" is about the bot
    clock, day = APPOINTMENT_CLOCK.search(low), APPOINTMENT_DAY.search(low)
    if clock and re.match(r"for\s", clock.group(0), re.I) and _A_COUNT_NOT_A_CLOCK.search(low[:clock.start()]):
        clock = None
    if not clock and not day:
        return ""
    if clock:
        # Whatever follows the clock has to be the day and nothing else: "the shop is at 3 the
        # parade" puts a street after the number, and that is a place, not an appointment.
        after = low[clock.end():].strip(" ,.;:-")
        if after and not re.match(r"^(?:on\s+)?" + APPOINTMENT_DAY.pattern + r"$", after, re.I):
            return ""
    cut = min([m.start() for m in (clock, day) if m])
    thing = low[:cut].strip(" ,;:-")
    thing = re.sub(r"^(?:the|my|our)\s+", "", thing)
    thing = re.sub(r"\s+(?:is|at|on|for)$", "", thing).strip()
    if not thing and day is not None and cut == day.start():
        thing = _the_thing_said_after_the_day(low, day)
    if not thing or len(thing.split()) > 4:
        return ""
    if _the_day_described(thing):
        return ""  # "hot today" is how the day is, not a thing they have on it
    if TAKE_BACK_WORDS.search(thing):
        return ""  # the line takes the last thing back; it does not name something on a day
    if thing.split()[0] in APPOINTMENT_NOT_A_THING:
        return ""
    if thing.split()[0].strip(",.!") in APPOINTMENT_CORRECTION:
        return ""  # "sorry, its at 8pm" is the clock being put right, not a thing called Sorry
    if not re.search(r"[a-z]{3}", thing):
        return ""
    # A thing the line says has already happened is not an appointment: "the nurse arrived at 6"
    # is news, and kept as a thing on a clock it answers "Your nurse arrived is at 6".
    for word in thing.split():
        if word in APPOINTMENT_PAST_VERB or word in APPOINTMENT_A_VERB:
            return ""
        if len(word) > 3 and word.endswith("ed") and word not in APPOINTMENT_NOT_A_VERB:
            return ""
    if day is not None and re.search(r"\d|" + MONTH_NAMES, day.group(0), re.I):
        if thing.split()[-1].strip(",.!") in APPOINTMENT_A_DATE_VERB:
            return ""
    # The plan is kept the way the ask will read it back: the thing, then its clock, then its
    # day ("dentist at 3 on tuesday"). The day goes last because that is the order the when ask
    # says it back in, and a plan that keeps their word order says "You're planning to dentist
    # saturday at 10" - a machine reading a phrase.
    when = []
    if clock:
        when.append("at " + " ".join(clock.group(1).split()))
    if day:
        day_text = " ".join(day.group(0).split())
        # A day already carries its own word ("on tuesday", "next friday", "this morning"),
        # and "tomorrow" takes none: "on tomorrow" is not something anyone says. Every other day
        # needs the "on", a date written month-first included: "the scan is december 3" kept as
        # "scan december 3" was read back as "You're planning to scan december 3".
        if not re.match(r"^(?:on|this|next|today|tomorrow|tonight)\b", day_text, re.I):
            day_text = "on " + day_text
        when.append(day_text)
    return thing + " " + " ".join(when)


# A clock on its own puts nothing in the future: "i woke at 3" is this morning, not tonight. So
# the plan reader asks for a word of coming up, and a thing the person has to do carries its own:
# "i have to pick up the kids at 3" is today, and read as nothing at all it was answered with a
# hedge. Only the present says so - "i had to" and "i needed to" have already happened.
OBLIGATION = re.compile(r"\b(?:have|has|ve|need|needs|got|gotta|must)\s+(?:to\s+)?[a-z]", re.I)


# A thing they do on repeat is how their week runs, not something coming up: "i have to get up at
# 6 every day" is a habit, and kept as a plan it turned "whats coming up" into a list of their
# routine. The words that put a thing on repeat refuse it, the way PAST refuses "i had to". A
# one-off with a day on it still stands ("i have to work this weekend", "the dentist on monday").
RECURRENCE = re.compile(
    r"\b(?:every|each|most\s+(?:days?|nights?|mornings?|weeks?|weekends?|evenings?)|"
    r"usually|always|never|twice|daily|nightly|weekly|monthly|fortnightly|"
    r"weekdays?|weeknights?|on\s+weekends?|weekends)\b", re.I)


# A clock on a train that leaves, a shift that starts or a flight that lands is a time they have
# to be somewhere, and it is ahead of them with no "tomorrow" in the line: "my train leaves at
# 8.15" was read as nothing at all ("I'm listening - say more if it helps") while "my bus gets in
# at 7" was a plan, because "gets in" is not one of the verbs that make a thing a sentence.
A_CLOCKED_EVENT = re.compile(
    r"\b(?:leaves?|leaving|departs?|departing|starts?|starting|begins?|beginning|arrives?|"
    r"arriving|lands?|landing|gets?\s+(?:in|there|back)|takes?\s+off|checks?\s+in|"
    r"sails?|sailing|flies?|flying|boards?|boarding|opens?|opening|closes?|closing)\b", re.I)


def _coming_up(clause):
    """True when the clause says something that is still to come.

    A future word says it ("tomorrow", "on monday", "in july"), and so does a thing they have to
    do with a clock or a day on it: "i have to pick up the kids at 3" names no future word and is
    the rest of today.
    """
    if RECURRENCE.search(clause):
        return False
    if FUTURE.search(clause):
        return True
    if OBLIGATION.search(clause):
        return bool(APPOINTMENT_CLOCK.search(clause) or APPOINTMENT_DAY.search(clause))
    return bool(A_CLOCKED_EVENT.search(clause) and APPOINTMENT_CLOCK.search(clause))


def _dated_plan(text, deed=None):
    """The plan in a line that puts something in the future, however it is worded.

    "i start my new job on monday", "my holiday is in august" and "my daughter's party is next
    saturday" all say what is coming up, and none of them opens with "i'm going to". The clause
    that carries the date is the plan: it has to be the person's own business, in their own
    voice, and not a question or something that already happened.

    A clause that already happened is news rather than a plan, and it is still a fact about them
    worth answering with the thing itself ("you paid the rent on friday - noted"), so the deed is
    put in the list a caller passes in instead of being dropped."""
    # A line with nothing coming up in it is not a plan whatever its halves look like: a thing
    # with a clock on it ("we've got a plumber coming at 9") is read by the appointment reader,
    # and taking it here would keep the half and lose the sentence the person said.
    if not _coming_up(text):
        return ""
    for clause in _dated_plans(text, deed):
        return clause
    return ""


# The same coming thing is said with another verb too: "my mum is coming to stay in may" then
# "my brother in june" is one person's plan and another's, and the second half is said without a
# verb because the first half carries it.
CLAUSE_SUBJECT = re.compile(
    r"^\W*(?:(?:and|but|so|also|then|oh|ok|okay|well|plus)[\s,]+)*"
    r"(?:my|our|the|his|her|their|i|we|me)\b"
    r"(?:\s+(?!(?:is|are|was|were|am|in|on|at|next|this|tomorrow|tonight|over|for|by|"
    r"before|after)\b)[\w'\u2019.\-]+){0,4}", re.I)
WHEN_OR_WHERE = re.compile(
    r"\b(?:in|on|at|next|this|tomorrow|tonight|over|for|by|from|before|after)\b|"
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b",
    re.I)
A_SHARED_VERB = re.compile(r"^(?:is|are|was|were|am)\b", re.I)
CORRECTION_LEAD_RE = re.compile(CORRECTION_LEAD, re.I)
# A word that can open a correction, and is also an ordinary word in front of a noun: "no heat",
# "no comedy", "sorry business", "wait list". What tells the two apart is the punctuation the
# person put after the opener - "no, four brothers" - or an opener that is more than one word and
# announces itself - "no wait, three sisters", "oh actually, six". Written once, so the reader that
# takes the opener off and the one that asks whether the words are only an opener agree.
OPENER_WORDS = ("ok", "okay")
OPENER_PUNCTUATION = re.compile(r"[,.:;!?\-\u2013\u2014]\s*$")


def _the_opener_end(said):
    """Where the correction opener in front of `said` ends, or 0 when it does not open with one."""
    lead = CORRECTION_LEAD_RE.match(said)
    if not lead:
        return 0
    front = lead.group(0)
    if OPENER_PUNCTUATION.search(front):
        return lead.end()
    words = [one for one in re.split(r"[^a-z']+", front.lower()) if one]
    words = [one for one in words if one not in OPENER_WORDS]
    return lead.end() if len(words) >= 2 else 0



def without_the_correction_opener(text):
    """The line after the opener that says the last thing is being said again, or "" when the
    line does not open with one.

    The opener is the person's, but it names nothing the line is about: "sorry, four brothers"
    and "no wait, three sisters" both go back over the fact the turn before stated, and the apology
    in front of one says only that the value is being said again. Every reader that takes a
    subject, a thing or a key out of a line reads it here first, so a correction never arrives
    wearing an opener that a card can match on - "sorry, three sisters" after "i have two sisters"
    was answered by the apology row, whose ask word is "sorry"
    (bot/knowledge/lookup.py, `_past_a_correction`; bot/memory/named.py, `about_it`).
    Only a lead the person punctuated - or one that is two words and announces itself ("no wait",
    "oh actually") - is taken off. "no" and "sorry" are ordinary words too: "no heat in my car",
    "no time to cook dinner" and "sorry i snapped at her" are the line, not an opener with a value
    behind it, and stripping the word off those took a heater, a dinner and an apology away from
    their own answers.
    """
    said = " ".join(str(text or "").lower().split())
    end = _the_opener_end(said)
    if not end:
        return ""
    return said[end:].strip(" ,.;:\t\u2013\u2014")


def is_a_correction_opener(text):
    """True when the words are nothing but the opener that announces a correction.

    The words are the person's ("no wait,", "sorry,", "oh, actually,", "scratch that,"), and they
    name nothing on their own: they say that the last thing is being said again. Read off the same
    lead as the correction itself, so a reader that has to tell an opener from a value cannot
    disagree with the one that reads the correction - "wait, four brothers" was said back as
    "Got it - wait, four brothers" because the echo took "wait," for part of the value
    (bot/memory/ack.py, `_only_the_correction_in_front`).
    """
    said = " ".join(str(text or "").lower().split())
    if not said:
        return False
    lead = CORRECTION_LEAD_RE.match(said + " ")
    return bool(lead and lead.end() > len(said))


def _said_after_the_subject(clause):
    """What the clause says about its subject, before the time or place it is nailed to:
    "is coming" in "my sister is coming in may", and "" in "my brother in june"."""
    match = CLAUSE_SUBJECT.match(clause)
    rest = clause[match.end():] if match else clause
    where = WHEN_OR_WHERE.search(rest)
    return (rest[:where.start()] if where else rest).strip(" ,")


def _the_verb_for(body, subject):
    """The lent verb agreeing with the person it now belongs to: "are going to spain" said of
    "my mum" is "is going to spain", and said of "i" is "am going to spain"."""
    first = body.split()[0].lower() if body.split() else ""
    person = str(subject or "").strip().lower()
    plural = person in ("we", "they", "you") or " and " in person
    if not plural:
        if first == "am":
            return "is" + body[2:]
        if first in ("are", "were"):
            return ("is" if first == "are" else "was") + body[len(first):]
    if person == "i" and first == "is":
        return "am" + body[2:]
    return body


def _with_the_verb_lent(clause, earlier):
    """The clause with the verb of the clause before it put back: "my brother in june" after
    "my sister is coming in may" is "my brother is coming in june". Left alone when either
    half says something other than this sharing, or when the clause has a verb of its own."""
    if not clause or not earlier or _said_after_the_subject(clause):
        return clause
    body = _said_after_the_subject(earlier)
    if not A_SHARED_VERB.match(body):
        return clause
    match = CLAUSE_SUBJECT.match(clause)
    subject = match.group(0) if match else ""
    body = _the_verb_for(body, subject)
    rest = clause[match.end():].lstrip() if match else clause
    if not rest:
        return clause
    return (clause[:match.end()].rstrip() + " " + body + " " + rest).strip()


def _dated_plans(text, deed=None):
    """Every plan a line carries, in the order it says them.

    "my sister is coming in may and my brother in june" is two things coming up, and the second
    is said without a verb of its own: the verb of the first is lent to it ("my brother is coming
    in june"), because that is how the person said it."""
    # The words that put a thing in the future are not the only ones a plan is said with: "we've
    # got a plumber coming at 9" has a clock on it and no "going to", and the line's own coming-up
    # reader knows the difference. Either one opens the line; the clause still has to carry it.
    if not FUTURE.search(text) and not _coming_up(text):
        return
    at = 0
    earlier = ""
    for piece in re.split(r"(?<=[.!?])\s+|,|;|\s+(?:but|and|so|then)\s+", text):
        # Where this piece sits, so the person it was joined to can be taken back: the "and" in
        # "my sister and i are going to italy in june" splits the subject, not two clauses, and
        # the half that is left ("i are going to italy in june") agrees with nobody and says the
        # sister is not going. The same line read against one person is "you are going to italy".
        start = text.find(piece, at) if piece else -1
        ahead = text[:start] if start != -1 else ""
        if start != -1:
            at = start + len(piece)
        clause = " ".join(piece.split()).strip(" ,.;:-!")
        if not clause:
            continue
        # A correction opens with a lead and the rest of it is still the plan it is about:
        # "actually my brother is coming in july" is the brother's plan with the new date. Left
        # whole, the lead keeps the clause from being read as theirs at all, so the newer date is
        # never filed and the ask is answered from the older plan the store kept.
        opened = CORRECTION_LEAD_RE.sub("", clause, count=1).strip()
        if opened and OWN.match(opened):
            clause = opened
        # The person the clause was split from is put back before anything is asked of it: it is
        # what makes the clause theirs, so "me and sarah are going to the cinema on friday" (kept
        # as "sarah are going to the cinema on friday") and "me and the kids are going to spain
        # in july" (kept as "the kids are going to spain in july") are one plan, not none.
        joined = _with_the_person_joined_to_the_subject(ahead, clause)
        # Either half can be the half that says whose plan it is: "the kids and i are going to
        # spain" opens with the kids, "me and the kids are going to spain" opens with the person.
        if not (OWN.match(joined) or OWN.match(clause)
                or THE_THING_HAS_A_DAY.match(clause)) or "?" in joined:
            # A thing of the household with a day on it is theirs too ("the rent is due on 1
            # july"), which `OWN` cannot see because it names no person.
            continue
        clause = _with_the_verb_lent(joined, earlier)
        if not _coming_up(clause) or PAST.search(clause):
            continue
        if ASKING.match(re.sub(r"^(?:ok(?:ay)?[, ]+|and |so |but |also |well |oh )+", "", clause,
                               flags=re.I)):
            continue
        if SECOND_PERSON.search(clause):
            continue  # "i'll call you tomorrow" is about the bot, not about their week
        if NEGATED.search(clause):
            continue  # "i can't sleep tonight" is how today is, not a plan
        if _how_they_are(clause) or _how_their_things_are(clause):
            # "im really low this week" is how they are, and "my budget is tight this month" is
            # how a thing of theirs is: neither is what they are doing
            continue
        if a_deed(clause):
            if deed is not None:
                deed.append(clause)
            continue  # "i saw my mum on sunday" has happened; it is not coming up
        words = clause.split()
        if len(words) < 3 or len(words) > 18:
            continue
        if not (re.search(r"\b(?:my|our|i|we|i'm|im|me)\b", clause, re.I)
                or THE_THING_HAS_A_DAY.match(clause)):
            continue
        if len(re.findall(r"\b(?:i|my|we|our)\b", clause, re.I)) > 3:
            continue  # a whole paragraph said in one breath is not one plan
        earlier = clause
        yield clause


# A thing of the household with a day on it is theirs as much as "my" makes it: "the rent is due
# on 1 july", "the car tax is due on 3 august", "the boiler service is on 21 october". The clause
# names no person, so the plan reader skipped it and the store kept nothing - the person's own
# arrangement got the dead "Thanks for telling me" and the next ask about it was a search offer,
# while the knowledge base answered a general card about road tax or a boiler service. Only the
# shapes where the thing comes round on a day are read: "the weather is nice this weekend" is how
# the weekend is, and "the shop closes at 5" already names its own verb.
THE_THING_HAS_A_DAY = re.compile(
    r"^the\s+[a-z][a-z' \-]{1,30}?\s+(?:is|are|was|were)\s+"
    r"(?:due|on|booked|scheduled|expected|renewed)\b"
    r"|^the\s+[a-z][a-z' \-]{1,30}?\s+(?:expires?|expiring|runs?\s+out|renews?)\b", re.I)


# The one half of a subject that can come before the "and": "me", "i" and a person of theirs
# ("my sister", "the kids"). Requiring one of those shapes is what keeps an "and" between two
# things they are doing ("we went to spain and my sister is coming too") from joining them.
JOINED_PERSON = r"(?:me|i|(?:my|our|the|his|her|their)\s+[a-z'\u2019]{2,20})"
SUBJECT_JOIN = re.compile(
    r"^(?:and|but|so|also|well|ok|okay|oh|then|plus)?[\s,]*"
    r"(?:" + JOINED_PERSON + r")\s+and(?:\s+(?:me|i))?"
    r"(?:\s+" + JOINED_PERSON + r")?$", re.I)


def _with_the_person_joined_to_the_subject(ahead, clause):
    """The clause with the person it was split from, when the split went through a subject.

    "my sister and i are going to italy in june" keeps "i are going to italy in june", which is
    neither of them and is said back as "You're planning to i are going to italy". Only a piece
    that names a person and has no verb of its own joins, so "i'm 34 and i live in leeds" (whose
    first half says something) and "we are going to spain and my sister is coming too" (whose
    second half does) are split the way they were."""
    person = " ".join((ahead or "").split())
    if not person or not SUBJECT_JOIN.match(person):
        return clause
    return person + " " + clause



# A self-introduction is often typed as a list of who they are: "im sam, 34, live in
# leeds", "im jess, 28, from dublin, a nurse". Read on its own the line names the person
# and drops the rest, because the parts after a comma have no "i" in front of them. Each
# part is read the way the line would be if it were said by itself, and a part that talks
# about someone else ("my sister lives in cork") is left to the readers that expect it.
# A part that already has an "i" of its own is a clause, not a half clause: "im in bristol, i
# moved in march" is two facts, and the second one put under an "i'm" of its own comes out as
# "i'm i moved in march" and is read back as "you're you moved in march".
SELF_INTRO = re.compile(
    r"^\W{0,2}(?:(?:hi+|hey+|hello+|hiya)\b[\s,]*)*(?:im|i'm|i am)\s+"
    r"[a-z'\u2019\-]{2,}(?:\s+[a-z'\u2019\-]{2,})?\s*,(?P<rest>[^?]*)$", re.I)
OTHER_START = frozenset("my our his her their the it we they she he there this that".split())
# A part that starts with one of these is not a fact about them: it is the rest of a question
# ("im tired, should i go to bed") and reading it would name them after a question word.
NOT_A_PART = frozenset("""what how why when where who which should can could do does did is are
was were will would shall may might help thanks thank sorry please so but and if maybe just""".split())


# A second clause that leaves the subject out still says something about the person: "im 34 and
# live in leeds", "i work in a bakery and drive a van", "im 34, live in leeds". The subject of
# the line carries over the "and", and English drops it whenever it repeats, so the clause is
# read with it put back. Only when the clause it follows was about them: "my mum is 72 and lives
# in York" carries her subject over, not theirs.
CONTINUATION_SPLIT = re.compile(r",|;|\s+(?:and|but)\s+", re.I)
PERSON_SUBJECT = frozenset("""i im i'm i've ive i'd id we we're we've""".split())
ANY_SUBJECT = PERSON_SUBJECT | frozenset("""my our his her their he she it they there this that
you your""".split())


def _continued_parts(text):
    """The later clauses of a line about them that leave their subject out, read as their own."""
    clauses, start = [], 0
    for match in CONTINUATION_SPLIT.finditer(text):
        clauses.append(text[start:match.start()])
        start = match.end()
    clauses.append(text[start:])
    words = clauses[0].replace(",", " ").split()
    subject = "person" if words and words[0].lower() in PERSON_SUBJECT else None
    if subject == "person" and WISHING.search(" ".join(words)):
        # "i want to move to bristol and work part time" says what they would like, not what is
        # true: the subject carries over the "and" but the frame does too, and putting it back
        # without the frame turns a wish into a job. Only a clause that states is read.
        return []
    parts = []
    for clause in clauses[1:]:
        clause = clause.strip(" .!?,")
        if not clause:
            continue
        first = clause.split()[0].lower().strip(",")
        if first in ANY_SUBJECT:
            subject = "person" if first in PERSON_SUBJECT else "other"
            continue
        if subject != "person" or first not in CONTINUATION_VERB:
            continue
        for lead in ("i ", "i'm "):
            read = _extract(lead + clause)
            read.pop("name", None)  # a name opens a line: "i like fish and chips" is not Chips
            read = {key: value for key, value in read.items() if key in CONTINUATION_KEYS}
            if read:
                parts.append(read)
                break
    return parts


# The frames that make the line a wish or a condition rather than a fact about them. A
# continuation under one of these keeps the frame, so it says nothing about what is true.
WISHING = re.compile(
    r"\b(?:want|wanna|wish|hope|might|may|could|would|should|plan|planning|thinking|thought|"
    r"going to|gonna|used to|trying|try|like to|love to|if|unless|pretend|imagine)\b", re.I)


# The clause has to open with a verb that takes the person as its subject; a noun opening one
# ("and a tin of tomatoes") is part of the list before it, and "i tin of tomatoes" is not a job.
CONTINUATION_VERB = frozenset("""live work have got am 'm was were come comes came moved move
drive study teach train run play commute rent own need want speak hold""".split())
# Only what the stream keeps as a fact about them: the other stream (plans, deeds) reads a
# whole line and its own subject, and half a clause is not enough for it.
CONTINUATION_KEYS = frozenset("""places home city town job job_frame age pets allergies people diet
diets conditions name country county""".split())


# The pronoun that carries a second clause on about the person the first clause named: "my mum is
# 70 and she loves gardening" says two things about the mum, and the store kept only the age. The
# clause is put back under the relation the line named ("my mum loves gardening") and read as a
# line of its own, because that is what it is.
SAME_PERSON_CLAUSE = re.compile(
    r"^\W*(?:she|he|they)\s+(?P<rest>[a-z0-9'\u2019 ]{3,80}?)\s*$", re.I)
# The clauses one line can carry more than one fact in: a full stop, a comma, or the little
# conjunctions people join two facts with ("and", "but", "also", "n").
SAME_PERSON_SPLIT = re.compile(r"[.!?;]+|,\s*|\s+(?:and|but|also|n)\s+", re.I)


def _the_relation_named(clause):
    """The relation a clause names with "my"/"our", or None."""
    for relation in RELATIONS:
        if re.search(r"\b(?:my|our)\s+" + relation + r"(?:'s|s)?\b", clause, re.I):
            return relation
    return None


def _a_clause_about_the_same_person(text):
    """The later clauses of a line that say more about the person the clause before named.

    Only a line that names a relation is read this way: "my mum is 70 and she loves gardening" is
    two facts about the mum, while "the cake is done and she loves it" names nobody and is left
    alone. What the clause says has to be a fact the store keeps about a person, so a clause about
    what they are doing tomorrow ("and she is coming on friday") adds nothing.

    The pronoun belongs to the person named last, not the first one the line opened with: in "my
    son is 7 and my daughter is 3 and she hates peas" the she is the daughter, and reading it onto
    the son filed the daughter's dislike on him as well.
    """
    clauses = [part for part in SAME_PERSON_SPLIT.split(text or "") if part.strip()]
    if len(clauses) < 2:
        return []
    named = _the_relation_named(clauses[0])
    if not named and not any(_the_relation_named(clause) for clause in clauses[1:]):
        return []
    parts = []
    for clause in clauses[1:]:
        found = SAME_PERSON_CLAUSE.match(clause.strip())
        if not found:
            # A clause that names somebody else takes the pronoun over: the next "she" is about
            # the daughter, not the son the line started with.
            named = _the_relation_named(clause) or named
            continue
        if not named:
            continue
        read = _extract("my " + named + " " + found.group("rest").strip())
        kept = []
        for entry in read.get("others") or []:
            if not (isinstance(entry, dict) and entry.get("who")
                    and str(entry["who"]).lower() == named.lower()):
                continue
            # A name only opens a line: "my mum is 70 but she is sharp" is a description, and the
            # name reader takes the word after "is" as one.
            entry = {key: value for key, value in entry.items() if key != "name"}
            if any(value for key, value in entry.items() if key != "who"):
                kept.append(entry)
        if kept:
            parts.append({"others": kept})
    return parts


def _self_intro_parts(text):
    """The list parts of a self-introduction, each read as a line of its own."""
    match = SELF_INTRO.match(text.strip())
    if not match:
        return []
    parts = []
    for piece in re.split(r",|\band\b|;", match.group("rest")):
        piece = piece.strip(" .!?")
        words = piece.split()
        if not words or set(w.lower() for w in words[:1]) & (OTHER_START | NOT_A_PART):
            continue
        # A part that opens with its own subject is a whole clause and is read as it stands: it
        # already says "i", and a lead put in front of it says it twice.
        leads = ("",) if words[0].lower() in PERSON_SUBJECT else ("i'm ", "i ")
        for lead in leads:
            read = _extract(lead + piece)
            if read:
                parts.append(read)
                break
    return parts



def _same_thing(one, other):
    """The same fact under a plural: "pets" and "pet", "cats" and "cat"."""
    one = _tidy(str(one)).lower().strip()
    other = _tidy(str(other)).lower().strip()
    if not one or not other:
        return False
    return one == other or one.rstrip("s") == other.rstrip("s")


def _is_only_the_take_back(value, gone):
    """"no pets" is not a correction to something called "Pets": a line that takes a fact back
    corrects nothing, and "Pets" is not a value anybody holds.

    Only a value the line says it is denying is skipped. A line can correct and take something
    back at once, and the correction is the half worth keeping: "im not allergic to nuts, no i
    mean dairy" puts dairy back on the table while it takes nuts off, and the "no" in it opens
    the correction, not the denial.
    """
    if not gone:
        return False
    for fact, said in gone.items():
        if _same_thing(value, fact):
            return True
        for item in (said if isinstance(said, list) else [said]):
            if isinstance(item, dict):
                item = item.get("animal") or item.get("name") or ""
            if str(item) == EVERYTHING:
                # "no pets" takes the lot, so there is nothing left for a value to be about.
                return True
            if _same_thing(value, item):
                return True
    return False


# The name a person gives the bot: "im going to call you bob", "your name is Pip from now on",
# "i'll call you max from here". Only a naming, never a question - "what should i call you" asks
# and names nothing - and never a time: "i'll call you when i get there" names no one.
BOT_NAME = re.compile(
    r"\b(?:call|calling|callin|name|naming|named)\s+(?:you|u)\s+([A-Za-z][a-z'-]{1,19})\b"
    r"|\byour name(?:'s| is| will be)\s+([A-Za-z][a-z'-]{1,19})\b", re.I)
# The words that make a line a question about the name rather than a gift of one: "what should i
# call you", "which name do you want", "your name is bob right?". A question that offers the name -
# "can i call you bob", "shall i call you bob" - is the person choosing it, so it names the bot.
BOT_NAME_ASKED = re.compile(r"\bwhat\b|\bwhich\b|\bwho\b", re.I)
# A tag on the end of the line takes the gift back: "your name is bob right?" asks instead of says.
BOT_NAME_TAG = re.compile(r"\bright\s*\?|\bam i right\b|\barent you\b|\bisnt it\b", re.I)
BOT_NAME_TITLE = frozenset("mr mrs ms miss mx dr doctor sir lady lord captain prof professor "
                           "prince princess saint dame".split())
# What can follow "call you" without being a name: a time, a reason, a person, a politeness.
BOT_NAME_STOP = frozenset("""when then tomorrow tonight today later back after before if once until
soon now again please ok okay mate guys someone somebody him her them it me you us everyone
all every one two three four five six seven eight nine ten eleven twelve
day week month year morning evening night weekend christmas
at in on by around about this next last half noon midnight oclock o'clock
really very so quite pretty much always never just only definitely
short tall long great cool funny weird silly fine good bad better best worse worst wrong right
hard easy nice lovely rubbish dumb stupid same different strange odd lovely amazing awesome
useless perfect brilliant terrible awful""".split())


# The ask for the name the person gave the bot: "whats your name", "what should i call you",
# "what do they call you". Only the ask - "do you like your name" is a question about a taste,
# and "who are you" is the identity ask, which another module answers.
BOT_NAME_ASK = re.compile(
    r"\bwhat(?:'s|s| is| was)?\s+your name\b|\byour name (?:again|now)\b"
    r"|\bwhat (?:should|shall|do|can|would) (?:i|we|they) (?:call|name) you\b"
    r"|\bwhat(?:'s|s| is| was) (?:it|that) (?:i|we) (?:call|called) you\b"
    r"|\b(?:do|have) you (?:got |have )?(?:a |any )?(?:name|nickname)\b"
    r"|\bwhat are you called\b"
    r"|\bcall you again\b", re.I)


def bot_name(text):
    """The name they have just given the bot, or None.

    A name is theirs to give: kept, it is what the bot says when asked its name later in the chat,
    and without it the bot claims to have no name after being named. The word after "call you" is
    read as a name only when the line is not a question and the word is not a time or a person
    ("i'll call you when i get there", "i'll call you back").
    """
    if not isinstance(text, str):
        return None
    match = BOT_NAME.search(text)
    if not match:
        return None
    if BOT_NAME_ASKED.search(text[:match.start()]) or BOT_NAME_TAG.search(text):
        # "what should i call you" and "your name is bob right?" ask; they do not name this bot.
        return None
    word = (match.group(1) or match.group(2) or "").strip()
    if not word or word.lower() in BOT_NAME_STOP or word.lower() in NOT_A_NAME:
        return None
    if word.lower() in BOT_NAME_TITLE:
        # "call you Mrs Whiskers" is a whole name, not the title in front of it.
        more = re.match(r"\s+([A-Za-z][a-z'-]{1,19})\b", text[match.end():])
        if more:
            word = word + " " + more.group(1)
    if not all(NAME_WORD.match(part) for part in word.split()):
        return None
    return word[:1].upper() + word[1:] if word.islower() else word


# The correction people say on its own, with the subject left out: "im an accountant" then
# "actually an engineer rather than an accountant". Read on its own the line names nothing (no
# "im", no "i work"), so the take-back never reached the store and the old job was still the
# answer a turn later. The subject is the words the turn before opened with, and the line is read
# with them put back - only when the line opens with a correction and takes a value back, so a
# bare "actually" with no value in it and a plain "no" are still nothing.
CORRECTION_OPENER = re.compile(r"^\s*(?:(?:no|nope|sorry|actually|wait|ah|oh|i\s+mean(?:t)?|"
                               r"make\s+that|or\s+rather)[,.\s!\u2014-]+)+", re.I)
SUBJECT_OPENERS = ((re.compile(r"^\s*(?:i'?m|i\s+am|im)\b", re.I), "im"),
                   (re.compile(r"^\s*i\s+work(?:s|ed)?\s+as\b", re.I), "i work as"),
                   (re.compile(r"^\s*i\s+work(?:s|ed)?\s+(?:in|at|for)\b", re.I), "i work in"),
                   (re.compile(r"^\s*i\s+live(?:s|d)?\s+in\b", re.I), "i live in"),
                   (re.compile(r"^\s*(?:i\s+have|i'?ve\s+got|i\s+have\s+got)\b", re.I),
                    "i have"))


def a_correction_without_a_subject(text, before):
    """The fact a subject-less correction states, read with the turn before's subject put back."""
    low = str(text or "").strip().lower()
    if not low or not any(word in low for word in TAKE_BACK):
        return {}
    opener = CORRECTION_OPENER.match(low)
    if not opener:
        return {}
    rest = low[opener.end():].strip()
    if not rest or not any(word in rest for word in TAKE_BACK):
        return {}
    before = str(before or "").strip().lower()
    for shape, frame in SUBJECT_OPENERS:
        if shape.search(before):
            found = extract(frame + " " + rest)
            if found:
                return found
    return {}


# "i said the party is on tuesday", "i told you i live in leeds": the line is the person
# saying the same thing again, in the words that report it. Read as it stands, the report verb is
# a past one, so the dated thing inside it is filed as something that has already happened ("i
# said the party is on tuesday" put a "done" fact in the store and no plan, and the correction
# that followed it had nothing to land on). The report is a frame, and what is inside the frame
# is the fact: the words after it are read the way they would be if they were said on their own.
# A line that corrects ("no, i said 700") is left to the correction readers, which need the
# marker in front to know the value is going back up.
REPORTED = re.compile(
    r"^\W{0,3}(?:(?:ok|okay|so|and|but|well|no|nope|look|see|yes|yeah|actually|honestly|literally|"
    r"i\s+mean)[, ]+)*"
    r"(?:(?:i|we)\s+(?:already\s+|did\s+|just\s+|definitely\s+)?(?:said|told\s+you|mentioned)|"
    r"like\s+i\s+said|as\s+i\s+said|to\s+repeat)\b[\s,:]*(?P<rest>[^?]*\S)", re.I)


def _reported_clause(text):
    """The thing a line reports having said, when the line is only the reporting of it."""
    text = (text or "").strip()
    if not text or "?" in text:
        return None
    if (CORRECTION_SAID.search(text) or CORRECTION.search(text)
            or CORRECTION_PAIR.search(text) or CORRECTION_MAKE.search(text)):
        return None  # a correction says the value again; it is not a report of a fact
    match = REPORTED.match(text)
    if not match:
        return None
    rest = match.group("rest").strip(" ,.;:-")
    return rest or None


def _paid_by_a_period(text, end):
    """Whether a period follows the figure, with the household allowed in the gap.

    "we bring home 3000 between us a month" says the same as "we bring home 3000 a month", and
    the words in the middle name who the money is for rather than a count of something else. The
    words are read from the short list above, so "i get 300 emails a week" is still a routine.
    """
    qualifier = INCOME_QUALIFIER.match(text[end:])
    return bool(INCOME_PERIOD.match(text, end + (qualifier.end() if qualifier else 0)))


def _a_years_pay(figure):
    """Whether a figure with no period is a year's wage rather than a count.

    "i earn 32000" and "my salary is 32k" are a year's pay and nobody says the period; "i get 300
    emails" and "i make 2000 cookies" are counts and their period is what said so. So the figure
    itself has to be the size of a wage: four digits, or a figure in thousands.
    """
    said = str(figure or "")
    if re.search(r"\d[\d,.]*\s?(?:k|grand|thousand)\b", said, re.I):
        return True
    return len(re.sub(r"[^\d]", "", said)) >= 4


def extract(text, question=False):
    """Facts this line states about the user (only the keys it states).

    question says whether the line is a question: it can still state a fact ("I'm allergic to
    nuts, what can I have?"), but only a statement introduces a pet.
    """
    reported = _reported_clause(text)
    if reported:
        # Only when the thing reported is itself a fact: a report of a greeting or a thank you
        # ("i said thanks") names nothing and is read the way it was said.
        if _extract(reported, question):
            text = reported
    found = _extract(text, question)
    given = bot_name(text)
    if given:
        found["bot_name"] = given
    if a_limit_on_the_plan(text) is not None and not COMMITS_TO.search(text):
        # A limit on the plan is not a plan and not a correction: "keep it cheap" was kept as
        # something they are going to do and "no long walks" as a correction to nothing. A line
        # that commits to the plan keeps it - "im going to keep it cheap this month" is the month
        # they have planned, and the limit is how they mean to do it.
        found.pop("plan", None)
        found.pop("plans", None)
        correction = found.get("correction")
        if isinstance(correction, dict) and not correction.get("from"):
            found.pop("correction", None)
    for part in (_self_intro_parts(text) + _continued_parts(text)
                 + _a_clause_about_the_same_person(text)):
        for key, value in part.items():
            if key == "name":
                continue  # the name is the opening word of the line, not of a part
            if key in ("places", "others"):
                # A place and a fact about somebody else are lists that two clauses can both add
                # to: "my mum is 70 and she loves gardening" is one person with two facts.
                found[key] = _union(found.get(key), value)
                if key == "others":
                    found[key] = _one_entry_per_person(found[key])
            elif key not in found:
                found[key] = value
    # The person is kept as the relation, whichever reader found them. The readers that name a
    # person have each been read by now, and not all of them go through `subject` - the age, the
    # name and the condition are read by their own clauses - so "my gf is 30" filed an age under
    # a person the store cannot be asked about while "my girlfriend is 30" filed her own. One
    # mapping at the end is one place, and the entries are merged again because two ways of
    # saying the same person are one person.
    if found.get("others"):
        for entry in found["others"]:
            if isinstance(entry, dict) and entry.get("who") in SPOKEN_RELATION:
                entry["who"] = SPOKEN_RELATION[entry["who"]]
        found["others"] = _one_entry_per_person(found["others"])
    if not found.get("correction") and found.get("drop") is None:
        # A correction word on the end of the line takes the same values back as one in front of
        # it, and the line already reads with the word in front, so the read is that line's read:
        # only the correction is taken, because the rest of the words are the same words.
        marked = _the_marker_in_front(text, question)
        if marked is not None:
            again = _extract(marked, question)
            for key in ("correction", "drop"):
                if again.get(key) is not None:
                    found[key] = again[key]
    return found


# The ways a line says what the person is, what they have or what they do, right after a hello:
# "hi, I'm vegetarian", "hi, I have a bad back", "hi, I work nights". The lead is what says the
# rest of the line is about them rather than about somebody else or about the day.
SAYS_WHAT_THEY_ARE = (("i", "am"), ("im",), ("i'm",), ("i", "have"), ("i", "work"),
                      ("i", "live"), ("i", "take"), ("i", "get"))
# What a line keeps about them and is still not what they are: their name, which is the chat
# module's to answer ("hi, I'm Sam"), and a thing they are after, which is a request rather than
# a fact about them - "im looking for a plumber" is asking for a plumber.
THEIR_NAME = frozenset(("name",))
THEIR_PLAN = frozenset(("plan", "plans"))


def about_themselves(said):
    """The facts a line says about the person themselves, or None when it says none about them.

    A hello in front of a fact is the fact, said by somebody who said hello first: "hi, im
    vegetarian" keeps the diet, and the fact store is the reading that can tell that from
    "hi, im Sam". Three shapes are not that fact. Nothing is not one ("hi there"), a name is
    the chat module's own turn, and a plan is a request the modules that answer a want answer
    better than a note does - the greeting at least leaves the door open to it.
    """
    words = tuple(word.lower() for word in str(said or "").split())
    if not any(words[:len(lead)] == lead for lead in SAYS_WHAT_THEY_ARE):
        return None
    kept = extract(said)
    if not kept or set(kept) <= THEIR_NAME or set(kept) <= THEIR_PLAN:
        return None
    return kept


def _one_entry_per_person(entries):
    """One entry per person: a line that says the same thing twice is still one person.

    "my mum is 72 and she is 73 next month" is read twice. The first reading has both numbers and
    keeps them the right way round (72 now, 73 next month); the later clause is then read on its
    own, as "my mum she is 73 next month", and cannot see the 72 in front of it, so it hands back a
    second entry for the same woman. Two entries for one person is two mums to everything that
    reads the store, and the age the line opened with is lost from the reply.

    The fold is the store's own (`bot/memory/__init__._fold_into`): a birthday still to come sits
    beside the age they are rather than replacing it, and an entry that only repeats the birthday
    already kept adds nothing. Two entries are one person only when they name the same person - the
    same word for them, and the same name if either gave one - so "my kids are ada 7 and sam 4"
    stays two children.
    """
    out = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        who = str(entry.get("who") or "").lower()
        kept = None
        if who and not entry.get("pronoun"):
            for one in out:
                if str(one.get("who") or "").lower() != who or one.get("pronoun"):
                    continue
                mine = str(one.get("name") or "").lower()
                theirs = str(entry.get("name") or "").lower()
                if mine and theirs and mine != theirs:
                    continue  # two children with one word for them are two children
                kept = one
                break
        if kept is None:
            out.append(dict(entry))
            continue
        for key, value in entry.items():
            if key in ("who", "pronoun"):
                continue
            if key == "name":
                # A name read on the line goes onto the person the line already named: "my son
                # tom is allergic to nuts" is one boy with a name and an allergy, and dropping
                # the name left the store unable to answer to "what is tom allergic to". The
                # spelling that keeps its capital is the one to keep: the reader that catches a
                # name as it was typed says "Meg", and one that takes the word after the verb
                # says "meg", and a store that answers "your sister is called meg" is a store
                # that looks like it was not listening.
                mine = str(one.get("name") or "")
                if not mine or (mine[:1].islower() and str(value)[:1].isupper()):
                    one["name"] = value
                continue
            if key == "age":
                # The birthday already kept, said again: the age they are stays.
                if one.get("to_come") == value:
                    continue
                if one.get("turns") and not one.get("age"):
                    one["age"] = value
                    continue
                if isinstance(one.get("age"), int) and isinstance(value, int) and one["age"] != value:
                    if not one.get("turns"):
                        one["age"] = value
                    continue
                one["age"] = value
                continue
            if key in ("turns", "to_come"):
                # The day belongs to the number it was said with, and the entry that already has
                # both is the one read with the line in front of it.
                if not one.get("turns"):
                    one["turns"] = value
                    if key == "to_come" and one.get("age") != value:
                        one["to_come"] = value
                continue
            if not isinstance(value, (list, tuple)):
                one.setdefault(key, value)
                continue
            have = one.setdefault(key, [])
            if isinstance(have, list):
                have.extend(item for item in value if item not in have)
    return out


def _union(one, other):
    out = list(one or [])
    for value in other or []:
        if value not in out:
            out.append(value)
    return out


def _the_pronoun(text, pos):
    """Which person a clause that names no relation is about: "she", "he", or "" for none."""
    start = 0
    for match in CLAUSE_BREAK.finditer(text, 0, pos):
        start = match.end()
    found = PRONOUN_SUBJECT.search(text, start, pos)
    if not found:
        return ""
    word = found.group("pron").lower()
    return {"her": "she", "him": "he", "them": "they", "shes": "she", "hes": "he",
            "theyre": "they"}.get(word, word)


# A relation the line names with their possessive, kept with an in-law's second word: "my mum",
# "my mums", "my mother in law". Longest first, so "mother in law" is not read as "mother".
RELATION_SAID = re.compile(
    r"\b(?:my|our)\s+(?P<who>" + "|".join(sorted(RELATIONS, key=len, reverse=True))
    + r")(?P<plural>s?)(?P<inlaw>\s+in\s+laws?)?\b", re.I)


def _the_person_the_pronoun_is(text, pos, pronoun):
    """The relation the line named before a bare pronoun, when it names exactly one.

    A line can name a person and then go on about them with a pronoun: "my mum is coming on
    sunday, shes 60", "my sister is staying, her birthday is 3 May". The clause the pronoun sits
    in names nobody, so the fact was filed against "she" and the store put it on whoever it had
    heard of last - a sister from an earlier line got the mum's age, and then "how old is my
    sister" said 60 while "how old is my mum" said she had never given it. The line named one
    person, so that is who the pronoun is.

    "" when the line names nobody (the store folds the pronoun onto the person the chat is about),
    names more than one ("my mum and my sister are coming, shes 60" is genuinely either), or names
    somebody the pronoun does not fit ("my mum is called janet and he is 72" is somebody else's
    72, and a fact on the wrong person is worse than one on nobody).
    """
    fits = SHE if pronoun == "she" else HE if pronoun == "he" else frozenset()
    if not fits:
        return ""
    who = ""
    for match in RELATION_SAID.finditer(text, 0, pos):
        word = a_person_word(" ".join((match.group("who")
                                       + (match.group("inlaw") or "")).split()).lower())
        if who and word != who:
            return ""
        who = word
    if not who:
        return ""
    parts = [part for part in re.split(r"[-\s]+", who) if part]
    return who if who in fits or any(part in fits for part in parts) else ""


# A name that opens a clause with the verb after it: "tom is allergic to nuts" says nothing about
# the person typing, and the fact is Tom's. Only a name that opens the clause counts - "the bag tom
# left is heavy" says nothing about anybody's allergy even where it sits in front of a verb.
NAME_THEN_THE_VERB = re.compile(
    r"^\W*(?:(?:and|but|so|then|also|oh|ok|okay|well|now|btw|hey|hi|quick)\W+)?"
    r"(?P<name>[A-Za-z][A-Za-z'\-]{1,19})\s+(?:is|was|has|had|isnt|wasnt|hasnt|cant|cannot|"
    r"doesnt|dont|didnt|never|only|gets|got|became)\b", re.I)


def _a_name_opening_the_clause(clause):
    """The name a clause opens with, or "" - "tom" in "tom is allergic to nuts"."""
    found = NAME_THEN_THE_VERB.match(clause or "")
    if not found:
        return ""
    name = found.group("name")
    low = _a_person_word(name)
    if low in NOT_A_PERSON_WORD or low in RELATIONS or low in DIET_GROUP \
            or low in A_PRONOUN_NOT_A_NAME:
        return ""
    if not (_may_be_a_name(name) and _name_after_a_title(name)):
        return ""
    return name


def _the_name_in_front(text, pos):
    """The name of the person the clause ending at pos names, or "".

    "tom is allergic to nuts" names Tom and nobody else, and "my son tom is allergic to nuts"
    names the son, who is Tom - the relation is the store's word for him, so the name is kept
    beside it rather than instead of it.
    """
    start = 0
    for match in CLAUSE_BREAK.finditer(text, 0, pos):
        start = match.end()
    clause = text[start:pos]
    who, name = _the_person_without_a_relation(clause)
    if name and not who:
        return name
    if not who:
        opening = _a_name_opening_the_clause(clause)
        if opening:
            return opening
    if who:
        # The relation is the subject; a name after it ("my son tom") is who that person is.
        found = re.search(r"\b(?:" + "|".join(sorted(OTHER_NOUNS, key=len, reverse=True))
                          + r")(?:\s+in\s+laws?)?s?\s+(?P<name>[A-Za-z][A-Za-z'\-]{1,19})\s*$",
                          clause, re.I)
        if found:
            name = found.group("name")
            low = name.lower().strip("'")
            if (low not in NOT_A_PERSON_WORD and low not in RELATIONS
                    and _may_be_a_name(name) and _name_after_a_title(name)):
                return name
    return ""


def _a_person(text, pos, who):
    """The person a fact about somebody else belongs to: {"who": "mum"}, {"name": "Tom"} or
    {"pronoun": "she"}.

    A line can point at somebody without naming them ("shes allergic to nuts", "hes vegetarian
    now"), and that person is still a person: a fact filed against nobody is an entry whose
    "who" is missing, and the next reading of the same line stumbled over it. When the line named
    one person before the pronoun, that person is who it is. {} means the line neither names
    anybody nor points at anybody.
    """
    if who:
        return {"who": who}
    # A person named and nothing else: "tom is allergic to nuts" is Tom's allergy, and there is
    # no relation word to file it under, so the entry carries the name the way "ada is 8" does.
    named = _the_name_in_front(text, pos)
    if named:
        return {"name": named}
    pronoun = _the_pronoun(text, pos)
    if not pronoun:
        return {}
    person = _the_person_the_pronoun_is(text, pos, pronoun)
    if person:
        return {"who": person}
    return {"pronoun": pronoun}


def _same_person(seen, entry):
    """Whether two readings of one line are about the same person.

    A reading that names the relation ("my son") and one that only has the pronoun ("she is 7")
    are the same person only when the line named nobody else, so a named reading matches another
    reading with that name and a pronoun reading matches the same pronoun. Merging a "she" into
    "my son" would put somebody else's birthday on the son.
    """
    who = seen.get("who") or ""
    other = entry.get("who") or ""
    if who or other:
        # Two children named in one breath ("my kids are ada 7 and sam 4") share the word in
        # front of them, so the word alone cannot tell them apart: the name is what says which
        # child an age belongs to, and two named children are never folded into one. A reading
        # with no name of its own is the same person as one that has a name - "my son is called
        # tom" then "my son is allergic to nuts" is one boy, and the name read on its own line
        # is how the allergy entry learns who he is.
        mine = str(seen.get("name") or "").lower()
        theirs = str(entry.get("name") or "").lower()
        return who == other and (not mine or not theirs or mine == theirs)
    return bool(seen.get("pronoun")) and seen.get("pronoun") == entry.get("pronoun")


# A figure said with a name and nothing else is about the person the chat knows by that name.
# "my kids are ada 7 and sam 4" and then "ada is 8" is Ada's age moved, and "no, sam is 5" is
# Sam's; without this the store kept 7 and 4 while the bot had already said "Ada is 8, good to
# know". The line names no relation, so the entry carries the name and no "who", and the store
# fills that in from the names it holds - a name the chat was never given stays nobody's.
NAME_AND_A_FIGURE = re.compile(
    r"^\W*(?:(?:no|nope|sorry|actually|wait|hold on|correction|i mean|and|but|so|oh)\W+)*"
    r"(?P<name>[A-Za-z][a-z'-]{1,19})(?:'s| is| was)\s+(?:now\s+|already\s+|actually\s+)?"
    r"(?P<age>\d{1,3})(?:\s*(?:years?|yrs?)(?:\s+old)?)?(?:\s+(?:now|already|today))?\W*$", re.I)

# The words a figure can be said with that are not names: "it is 8", "there is 8 left". The
# store also has to hold a person of that name, so this is the second of two gates, not the only
# one.
NOT_A_NAME_FIGURE = frozenset("""i you he she it we they there that this here what who which
the a an my your his her our their its mine yours hers ours theirs and but so now then just only
still really also too very time day week month year morning evening night today tomorrow
yesterday half""".split())


def _a_name_and_a_figure(text):
    """{"name": "Ada", "age": 8} for "ada is 8", "no sam is 5", "ada's 8 now" - or None.

    A whole line only, so "ada is 8 and sam is 4" is left to the relation readers and a clause
    inside a longer sentence is not taken for a fact about anybody.
    """
    match = NAME_AND_A_FIGURE.match(" ".join(str(text or "").split()))
    if not match:
        return None
    name = match.group("name")
    low = name.lower()
    if (low in NOT_A_NAME_FIGURE or low in NOT_A_NAME or low in NOT_A_NAME_THING
            or low in NOT_A_NAME_STATE
            or low in MONTHS or low in DAYS):
        return None
    age = int(match.group("age"))
    if not 0 < age <= 120:
        return None
    # The name is said back the way a name is written - "ada" is Ada - but a name the person
    # wrote with an awkward capital is left as they typed it.
    shown = name[:1].upper() + name[1:]
    return {"name": shown, "age": age}


# Where it hurts: the part of the body a line names, and the side or the place on it.
# "its on the outside of the knee", "my left shoulder is killing me", "the pain is in my lower
# back", "i hurt my ankle yesterday". A closed vocabulary, because a part of the body is not a
# word the line can invent, and a line that names one of these with nothing the matter with it
# ("my knee is fine") files nothing.
BODY_PARTS = ("knee", "knees", "back", "shoulder", "shoulders", "hip", "hips", "ankle", "ankles",
              "foot", "feet", "heel", "heels", "calf", "calves", "shin", "shins", "thigh",
              "thighs", "hamstring", "hamstrings", "wrist", "wrists", "elbow", "elbows", "hand",
              "hands", "finger", "fingers", "thumb", "neck", "head", "chest", "stomach", "tummy",
              "tooth", "teeth", "ear", "ears", "eye", "eyes", "arm", "arms", "leg", "legs", "toe",
              "toes", "jaw", "rib", "ribs", "groin", "abdomen", "spine", "tailbone", "collarbone",
              "achilles", "quad", "quads", "glute", "glutes", "arch")
BODY_PART = re.compile(r"\b(" + "|".join(BODY_PARTS) + r")\b", re.I)
BODY_HURTS = re.compile(r"\b(?:hurt|hurts|hurting|sore|ache|aches|aching|achy|pain|painful|"
                        r"injur\w*|twinge|stiff|swollen|swelling|niggle|flare[sd] up|"
                        r"killing me|playing up)\b", re.I)
BODY_LATERAL = re.compile(r"\b(left|right|both)\s+(?:(?:outer|inner|lower|upper|front|back)\s+)?"
                          r"(?:" + "|".join(BODY_PARTS) + r")\b", re.I)
BODY_PLACE = re.compile(r"\b(?:on|in|at|to|round|around)\s+(?:the|my|his|her|their|its)\s+"
                        r"(outside|inside|front|lower|upper|top|bottom|inner|outer)\b", re.I)


# The people a body part can belong to instead of them: "my mum has a sore hip", "my son hurt his
# arm", "my daughter has a sore knee" are how people talk about a parent or a child. A part with
# one of these in front of it is that person's, and a part said with "his", "her", "their" or
# "its" is not theirs at all.
SOMEONE_ELSE = re.compile(r"\b(?:my|our|the)\s+(?:(?:little|older|youngest|eldest|baby|big|"
                          r"grown[- ]up|step)\s+)?(?:son|sons|daughter|daughters|child|children|"
                          r"kid|kids|boy|boys|girl|girls|baby|babies|toddler|mum|mums|mom|mother|"
                          r"dad|dads|father|husband|wife|partner|ex|boyfriend|girlfriend|brother|"
                          r"brothers|sister|sisters|friend|friends|mate|mates|nephew|niece|cousin|"
                          r"grandma|grandad|granny|gran|nan|nanna|aunt|aunty|uncle|in-?law|"
                          r"dog|cat|puppy|kitten|patient|client|customer|colleague|boss)\b"
                          r"(?:'s|s')?", re.I)
# A part handed to another body: "my son hurt his arm". The name is its own because `NOT_THEIRS`
# above is the pet reader's ("i dont want a dog"), and a second constant of that name would take
# the first one's place for every reader loaded after this line.
A_PART_HANDED_OVER = re.compile(r"\b(?:his|her|their|its)\s+(?:\w+\s+){0,2}?(?:"
                                + "|".join(BODY_PARTS) + r")\b", re.I)


# The words that tie a part to the person typing: "my knee", "my left shoulder", "i have a sore
# knee", "i hurt my ankle". A part with none of them is a part the line is about rather than a
# report of one, and most lines like that are questions: "who has a sore hip", "does a sore knee
# need a doctor", "what helps a sore back". Filing one of those put a complaint in the person's
# mouth that they never made - the recall then said "It is your hip that you said was hurting" to
# someone who had asked who a sore hip has.
MY_OWN_PART = re.compile(r"\b(?:my|our)(?:\s+\w+){0,2}\s+$", re.I)
# A part said as the subject of the hurting word is theirs with no possessive at all: "knee
# hurts", "back is killing me", "shoulders are sore". Rare in chat, and unambiguous when it does
# happen, because nobody asks a question about a part in that word order.
THE_PART_HURTS = re.compile(r"^\s*(?:'s|s)?\s*(?:is|are|was|were|has|have|have been|has been|"
                            r"keeps)?\s*(?:killing|hurting|hurts|sore|aching|aches|ache|painful|"
                            r"stiff|swollen|playing|giving|in pain|bad|killing me)\b", re.I)
# A clause that opens with the person and then says something is the matter with a part of them:
# "i have a sore knee from running", "i hurt my ankle yesterday", "i've got a dodgy shoulder".
THE_PERSON_SAYS = re.compile(r"^(?:ok(?:ay)?[, ]+|and |so |but |well |oh |also )*"
                             r"(?:i|i'm|im|i've|ive|we|we're|were|we've|weve)\b", re.I)
# A line about a place on a part already named is about their own complaint even with no "my" in
# it: "its on the outside of the knee", "the pain is in the lower back".
A_PLACE_ON_IT = re.compile(r"^(?:it|its|it's|that|that's|this|the (?:pain|ache|hurt|soreness))\b",
                           re.I)


def _tied_to_them(part, low):
    """Whether the line ties the part to the person typing it, or only talks about parts.

    A question about a part names one with nothing that makes it theirs, and reading it as a
    complaint is the worst thing this reader can do: "who has a sore hip" filed a sore hip on the
    person who asked, and the store then answered "what did i say was hurting" with a hip they had
    never mentioned. Miss a bare "knee hurts" and nothing is lost; assert a complaint they did not
    make and the store lies to them.
    """
    before = low[:part.start()]
    after = low[part.end():]
    if MY_OWN_PART.search(before):
        return True
    if THE_PART_HURTS.match(after):
        return True
    # The clause the part sits in, so a question's own "i" does not count: "should i see someone
    # about a sore back" opens with "should", and the part is what it asks about.
    clause = re.split(r"[,;.!?]|\s+(?:and|but|so|then)\s+", before)[-1]
    if THE_PERSON_SAYS.match(clause.strip()) and BODY_HURTS.search(low):
        return True
    if A_PLACE_ON_IT.match(low) and BODY_PLACE.search(low):
        return True
    return False


def _theirs(part, low):
    """Whether the part at this place in the line is the speaker's own body.

    A part belongs to somebody else when a person word comes between them and it ("my mum has a
    sore hip", "my son's back"), and when the line hands it to another body with his, her, their
    or its ("my son hurt his arm"). Filing one of those as theirs put their mother's hip on them.
    A part the line only talks about, with no owner at all, is nobody's: it is a question.
    """
    part_at = part.start()
    owner = None
    for found in SOMEONE_ELSE.finditer(low):
        if found.start() < part_at:
            owner = found
    if owner is not None:
        between = low[owner.end():part_at]
        if not re.search(r"\b(?:my|our|i|me|mine|myself)\b", between):
            return False
    for other in A_PART_HANDED_OVER.finditer(low):
        if other.end() <= part_at + 1 and other.start() < part_at:
            return False
    return _tied_to_them(part, low)


def the_part_it_hurts(text):
    """The part of them that is sore, and where on it, or None.

    Filed as one record because it is one fact: the part, the side they gave ("left", "right",
    "both"), the place on it ("outside", "lower"), and the line as they said it, so the store can
    hand the words back instead of describing them. Read this way because nothing filed it at
    all: "its on the outside of the knee" left the store holding no fact, and eight turns later
    "and which knee was it" was answered with a hedge.
    """
    if not isinstance(text, str):
        return None
    low = " ".join(text.lower().split())
    # The first part that is their own body: "my son hurt his arm" says nothing about them, and
    # "my son has a sore arm and my knee is bad" says something about both.
    part = None
    for found in BODY_PART.finditer(low):
        if _theirs(found, low):
            part = found
            break
    if part is None:
        return None
    lateral = BODY_LATERAL.search(low)
    place = BODY_PLACE.search(low)
    if not (BODY_HURTS.search(low) or lateral or place):
        return None
    # "my knee is fine", "the back door": a part word with nothing the matter with it is not a
    # complaint, and the words that put a body word in front of another noun are not a side.
    if re.search(r"\b(?:no|not|never)\b[^.]{0,20}" + re.escape(part.group(1)) + r"\b", low):
        return None
    if not lateral and not place and re.search(r"\b" + re.escape(part.group(1)) +
                                              r"\s+(?:door|room|garden|yard|seat|window|wheel|"
                                              r"teacher|line|table|of the house)\b", low):
        return None
    held = {"part": part.group(1).lower(), "said": " ".join(text.split())}
    if lateral:
        held["side"] = lateral.group(1).lower()
    if place:
        held["place"] = place.group(1).lower()
    return held


def _extract(text, question=False):
    found = {}
    hurt = the_part_it_hurts(text)
    if hurt:
        found["hurts"] = hurt
    text = _the_numbers_in_words(text)
    diet = VEGETARIAN.search(text)
    name = _name(text)
    if name and diet and re.match(r"(?:i|we)", diet.group(1).lower()):
        # "im plant based" is how they eat, not what they are called: a way of eating that
        # starts with an ordinary word would otherwise also name them after that word.
        if diet.group(2).lower().replace("-", " ").startswith(_finish(name) + " "):
            name = None
    if name:
        found["name"] = name
    job, city, frame = _job_and_city(text, name, question)
    if not job and CHANGED_WORK.search(text):
        # "i changed jobs, im in a hospital now": the old job is gone, so the place the line
        # names as where they are now is the one to keep.
        moved = WORK_NOW.search(text)
        if moved:
            place = _finish(moved.group(3))
            if place and place not in JOB_STOP and len(place.split()) <= 3:
                # The preposition and the article are how they said where they work, so they
                # read back the same way: "you work in a hospital", never "in hospital".
                job = place
                frame = " ".join(part for part in (moved.group(1), moved.group(2)) if part)
    if job:
        found["job"] = job
        if frame:
            found["job_frame"] = frame
    car = _car(text)
    if car:
        found["car"] = car
    places, home, home_said = _places(text)
    if home is None:
        near = HOME_LOOSE.search(text)
        if near and near.group(1).split()[0].lower() not in NOT_PLACES:
            home = near.group(1)
            if home not in places:
                places.append(home)
    origin = _from_place(text)
    if origin:
        found["from"] = origin
        # A place they live in now is the one a "where do i live?" asks for, so the place they are
        # from joins the list only when nothing says where they live.
        if not home and origin not in places:
            places.append(origin)
    born = _born_place(text)
    if born:
        found["born"] = born
    for place in places:
        found.setdefault("places", []).append(place)
    if home and not city:
        city = home
        # The city is where they live, so a reply can say so rather than "you mentioned". A home
        # said with its place in front of it ("a small village near York") is kept in the words
        # they used, so the place they live is neither denied nor named as somewhere it is not.
        found["home"] = home_said or True
    if city and city not in found.get("places", []):
        found.setdefault("places", []).append(city)
    if city:
        found["city"] = city
    own = _own_states(text)
    if own:
        found.update(own)
    allergies, others = _allergies(text)
    if allergies:
        found["allergies"] = allergies
    for entry in _other_diets(text):
        known = next((seen for seen in others if _same_person(seen, entry)), None)
        if known is None:
            others.append(entry)
        else:
            known.setdefault("diet", entry["diet"])
    for entry in _other_conditions(text):
        known = next((seen for seen in others if _same_person(seen, entry)), None)
        if known is None:
            others.append(entry)
        else:
            known.setdefault("condition", entry["condition"])
    for entry in _other_jobs(text):
        known = next((seen for seen in others if _same_person(seen, entry)), None)
        if known is None:
            others.append(dict(entry))
        else:
            known.setdefault("job", entry["job"])
    for entry in _other_states(text):
        known = others[-1] if others and others[-1]["who"] == entry["who"] else None
        if known is None:
            others.append(dict(entry))
        else:
            for key, value in entry.items():
                known[key] = value
    for entry in _other_ages(text):
        known = next((seen for seen in others if _same_person(seen, entry)), None)
        if known is None:
            others.append(dict(entry))
        else:
            # A list of ages and one age are two readings of the same thing, and a lone age on
            # top of a list is the reading that saw only one of them: "i have two kids, 4 and 7"
            # was stored as "ages 4, 7" with an extra age of 7 beside it, and the chat said back
            # "Your kids are 7, 4 and 7." The fuller reading replaces the other instead.
            if entry.get("ages") or known.get("ages"):
                merged = _ages_held(known) + [age for age in _ages_held(entry)
                                              if age not in _ages_held(known)]
                held = _ages_held(entry)
                if held and len(held) >= len(_ages_held(known)):
                    merged = held
                known.pop("age", None)
                known["ages"] = merged
                if len(merged) == 1:
                    known["age"] = known.pop("ages")[0]
            else:
                known["age"] = entry["age"]
                # An age said with when it arrives is kept with those words: "my daughter is 3"
                # then "shes 5 next month" is a birthday, and an age that drops the "next month"
                # says she is 5 now, which is not what they told us.
                if entry.get("turns"):
                    known["turns"] = entry["turns"]
                else:
                    known.pop("turns", None)
            if entry.get("name") and not known.get("name"):
                known["name"] = entry["name"]
    for entry in _a_relations_name(text):
        known = next((seen for seen in others if _same_person(seen, entry)), None)
        if known is None:
            others.append(dict(entry))
        else:
            known["name"] = entry["name"]
    # The same person can be named with their name, their age or both, and the two readings are
    # merged by who they are rather than by the order they came in. A reading about "she" has no
    # "who" at all, so no step here may read the key as if every person had one.
    for entry in _relation_facts(text):
        # A line that names nobody files its fact against the pronoun instead ("shes 5 next
        # month" after "my daughter is 3"), so there is no "who" to merge by: the reader
        # crashed on the missing key and the person got "Hello!" back for a line about their
        # own child. The pronoun is the person there is to merge with, and when nobody carries
        # it the entry is kept for the store to fill in later.
        who = entry.get("who") or entry.get("pronoun") or ""
        known = None
        for seen in others:
            seen_who = seen.get("who") or seen.get("pronoun") or ""
            if (entry.get("name") and seen.get("name")
                    and str(entry["name"]).lower() != str(seen["name"]).lower()):
                # "my kids are ada 7 and sam 4" is two children, not one. A fact with no name of
                # its own still goes on the person the line already named.
                continue
            if who and (seen_who == who
                        or (not seen_who and entry.get("pronoun") and not seen.get("who"))):
                known = seen
                break
        if known is None:
            others.append(entry)
            continue
        for key, value in entry.items():
            if key in ("who", "pronoun"):
                known[key] = known.get(key) or value
            else:
                known.setdefault(key, value)
    entry = _a_name_and_a_figure(text)
    if entry:
        known = next((seen for seen in others
                      if str(seen.get("name") or "").lower() == entry["name"].lower()), None)
        if known is None:
            others.append(dict(entry))
        else:
            known["age"] = entry["age"]
            known.pop("months", None)
            known.pop("ages", None)
    if others:
        # A line that says something about a person is a line about that person: "my mums called
        # janet and shes 72" names the mum as surely as "my mum is coming round" does.
        for entry in others:
            for key in ("name", "age", "months"):
                if key in entry:
                    # A fact filed against a pronoun has no person yet: the store fills that in.
                    who = entry.get("who")
                    if who and who not in found.get("people", []):
                        found.setdefault("people", []).append(who)
                    break
        found["others"] = others
    if diet and re.match(r"(?:i|we)", diet.group(1), re.I):
        # The plain word is what people expect back, not "you're veggie".
        eating = " ".join(diet.group(2).lower().replace("-", " ").split())
        found["diet"] = DIET_NAMES.get(eating, eating)
    named = DIET_NAMED.search(text)
    if named and "diet" not in found:
        # "im on a gluten free diet" names the diet without naming a way of eating people adopt
        # as an identity, and it is the same fact: what the person will and will not eat.
        found["diet"] = " ".join(named.group(1).lower().split()).replace(" ", "-")
    underway = DIET_UNDERWAY.search(text)
    if underway and "diet" not in found:
        # "im on a diet" is a diet with no name, and "im doing keto" names one without the word
        # "diet": either way the line says how they eat, so the store keeps it.
        if underway.group("named"):
            found["diet"] = " ".join(underway.group("named").lower().split()).replace(" ", "-")
        else:
            found["diet"] = "on a diet"
    doing = _a_way_of_eating_said_with_a_verb(text)
    if doing and "diet" not in found:
        found["diet"] = doing
    bare = DIET_BARE.search(text)
    if bare and "diet" not in found:
        # "im dairy free" and "im low carb" name what the person eats without on or doing and
        # without the word "diet", and the store filed nothing, so the next ask about the diet
        # was denied to someone who had just said it.
        found["diet"] = "-".join(bare.group("bare").lower().replace("-", " ").split())
    meat = NO_MEAT.search(text)
    if meat:
        avoided = _finish(meat.group(1))
        if avoided in NO_EAT_QUALIFIER:
            # "i dont eat red meat": the first word qualifies the food, so the food comes with it,
            # and "red" on its own is not something anyone can be read back as avoiding.
            rest = _finish(text[meat.end():].split()[0]) if text[meat.end():].split() else ""
            if rest in MEAT:
                avoided = avoided + " " + rest
        # "i dont eat enough veg" and "i dont drink enough water" are a shortfall, not a way of
        # eating: filed as `diet: "no enough"` the line comes back as "You don't eat enough veg,
        # good to know - I'll plan around it", which is the complaint made into a diet.
        if avoided and avoided.lower().split()[0] not in _QUANTITY_WORDS \
                and not set(avoided.split()) & ALLERGY_STOP:
            found["diet"] = "no " + avoided
            if MEAT & set(avoided.replace(",", " ").split()):
                found["no_meat"] = True
    if not found.get("diet"):
        # The drinking half of the same fact, filed the same way, so the answers that keep food
        # off the plate keep the drink out too ("what wine goes with lamb" after "i dont drink").
        drank = _the_drink_they_do_not_take(text)
        if drank:
            found["diet"] = "no " + drank
    condition = CONDITION.search(text)
    if condition:
        found["condition"] = " ".join(condition.group(1).lower().split())
    pets = _pets(text, question)
    if pets:
        found["pets"] = pets
    owned = _owns(text)
    if owned:
        # "my car is a ford fiesta": the thing said with its make, which is what "what car do i
        # drive" asks for. One line can name two ("my car is a fiesta and my phone is a pixel").
        found["owns"] = owned
    tastes = [] if found.get("diet") else taste.read_all(text)
    if tastes:
        # "i love dogs", "not keen on fish", "not sure if i like curry": a taste of theirs, said
        # back like any other fact, and never an animal in the house (`bot/memory/taste.py`).
        # "i don't eat fish" is a diet and the diet extractor has it: a taste is what is left.
        # One line can hold two ("i like dogs but i hate cats"), and each is its own fact.
        found["tastes"] = tastes
    budget = (BUDGET.search(text) or SPEND_BUDGET.search(text) or SPEND_FOR.search(text)
              or INTENDED_SPEND.search(text) or THE_THING_MAY_COST.search(text)
              or ALL_I_CAN_DO.search(text)
              or ONLY_HAVE.search(text) or SPEND_BUDGET_NOW.search(text)
              or STRETCH_BUDGET.search(text)
              or BARE_BUDGET.search(text) or BUDGET_ASKED.search(text)
              or BUDGET_THOUGHT.search(text) or CEILING_BUDGET.search(text))
    if not budget:
        # A figure they live on is a limit like the money they have ("i only earn 1200 a month").
        # It has to be paid by a period and it must not be a rate: "i get 3 runs a week" is a
        # routine and "i earn 20 pounds an hour" is a wage rate, and neither is what a plan fits.
        money = INCOME.search(text)
        if money and not _paid_by_a_period(text, money.end()):
            money = None
        if not money:
            bare = INCOME_BARE.search(text)
            if bare and _paid_by_a_period(text, bare.end()):
                figure = bare.group(1).split()[-1]
                if sum(ch.isdigit() for ch in figure) >= 3:
                    money = bare
        if not money:
            for a_year in INCOME_A_YEAR:
                year = a_year.search(text)
                if (year and _a_years_pay(year.group(1))
                        and not text[year.end():].strip(" .,;!?-").strip()):
                    money = year
                    break
        if money and INCOME_RATE.match(text, money.end()):
            money = None
        budget = money
    if budget and subject(text, budget.start())[0] != "other":
        said_budget = " ".join(budget.group(1).split()).rstrip(".,;:")
        if budget.re is CEILING_BUDGET:
            # The refusal is the limit, said as the limit it is: "nothing over 25 pounds" and
            # "no more than 25 pounds" are the same ceiling, and the second is the one the
            # store can say back.
            said_budget = "no more than " + said_budget
        found["budget"] = said_budget
    elif not question and vague_budget(text) and subject(text, 0)[0] != "other":
        found["budget"] = vague_budget(text)
    kids = kid_count(text)
    if kids is not None:
        # A zero is a fact the store can answer with: "i dont have any kids" then "how many kids
        # do i have" was "You haven't told me how many kids you have yet", and a truthiness test
        # here dropped the one number that was said.
        found["kids"] = kids
    # "my age is 34" is the age said with its name, and people say it that way when they are
    # being clear. "i'm 34" is the shape that covers most of it.
    age = AGE.search(text) or MY_AGE.search(text)
    if age:
        found["age"] = int(age.group(1))
    # How tall, read after the age for the same reason the age reader refuses these figures: the
    # unit is what says this number is a height and not an age.
    tall = _how_tall(text)
    if tall:
        found["height"] = tall
    birthday = BIRTHDAY.search(text)
    if birthday and subject(text, birthday.start())[0] != "other":
        date = _a_birthday_date(birthday.group(1))
        if date:
            found["birthday"] = date
    weight = WEIGH.search(text) or WEIGH_IM.search(text) or WEIGH_MY.search(text)
    if weight and subject(text, weight.start())[0] != "other":
        unit = _weight_unit(weight.group(2))
        if unit:
            found["weight"] = weight.group(1) + " " + unit
            if str(found.get("age")) == weight.group(1):
                # The same figure read twice: "im 85 kilograms" is a weight, and a bare-number age
                # reader takes the 85 for an age as well, which has the bot say "you told me
                # you're 85" at the ask for their age. A line with its own age keeps it ("im 34
                # and i weigh 90 kilos" leaves both alone).
                found.pop("age", None)
    # "my sons" names the same person as "my son": _people reads the plural of every relation,
    # and a person the store knows is one the next "what is he allergic to" can be about.
    relations = _people(text)
    if relations:
        found["people"] = relations
    # A line that only moves the date of a plan they already told us about is not a new plan:
    # the plan is the one the store holds, with its date put right.
    moved = _date_change(text)
    plan = PLAN.search(text)
    if plan and _asks_about_the_plan(text, plan.start()):
        # A question about the plan is not a plan: the same words a plan is written with sit
        # inside the ask (bot/memory/facts.py, _asks_about_the_plan).
        plan = None
    if (plan and _GOT_A.search(plan.group(0)) and not FUTURE.search(text)
            and not _GOT_TO.search(text)):
        # "ive got a headache", "ive got two kids", "ive got a question about my tax": what they
        # have, not what they are going to do. The "got" form only plans when the infinitive is
        # there ("ive got to paint the fence") or when a date puts it ahead of them.
        plan = None
    if plan and re.match(r"^to\s+(?:go|leave|head off|set off|get going|dash)\b",
                          _plan_text(text, plan.end()), re.I) and _FAREWELL.search(text):
        plan = None  # "ive got to go, speak later" is a goodbye, not an arrangement
    if plan:
        plan_text = _plan_text(text, plan.end())
        words = re.sub(r"^to\s+", "", plan_text, flags=re.I).lower().split()
        while words and words[0] in ("a", "an", "the", "my", "our"):
            words.pop(0)
        first_word = words[0] if words else ""
        # "i'm going to bed" stops after "to" with a place; "i've got to call the dentist" stops
        # with the "to" still on the front, and the word after an infinitive "to" is a verb,
        # however much it looks like a place ("call", "book", "see" are in PLACE_VERBS).
        after_an_infinitive = (bool(re.match(r"to\b", plan_text, re.I))
                               or bool(INFINITIVE_FRAME.search(plan.group(0))))
        if (plan_text and not re.match(r"(?:[£$€]|\d)", plan_text)
                and first_word not in NOT_PLACES
                and (after_an_infinitive
                     or (first_word not in PLACE_VERBS and _a_plan_has_a_thing(plan_text)))):
            verb = _plan_verb(plan, plan_text)
            if verb:
                # the verb goes back in front of the thing it is about: "Saving up for a bike"
                plan_text = verb + " " + plan_text[:1].lower() + plan_text[1:]
            found["plan"] = plan_text
    if found.get("plan") and found.get("pets"):
        # "i've got two cats, milly and tom" is a pet, not a plan: the animal is the thing the
        # line is about, and a plan only reads it back as something they mean to do
        if PETS.search(found["plan"]):
            del found["plan"]
    for key in ("places", "allergies", "people"):
        if key in found:
            kept = [value for value in (_fact_value(v) for v in found[key]) if value]
            if kept:
                found[key] = kept
            else:
                del found[key]
    for entry in found.get("others") or []:
        for key in ("allergies", "places"):
            if key in entry:
                entry[key] = [value for value in (_fact_value(v) for v in entry[key]) if value]
    for key in ("budget", "diet", "city", "plan"):
        if key in found and not _fact_value(found[key]):
            del found[key]
        elif key in found:
            found[key] = _fact_value(found[key])
    if "plan" not in found:
        deed = []
        several = list(_dated_plans(text, deed))
        dated = _appointment(text) or (several[0] if several else "")
        if dated:
            found["plan"] = dated
            if len(several) > 1:
                found["plans_today"] = several
        elif deed:
            # A dated thing they have already done is not coming up, but it is theirs: the store
            # answers it with the thing itself, and only a plan is read back as ahead of them.
            found["done"] = deed[0]
    if "plan" in found and moved is None:
        found["plans"] = found.pop("plans_today", None) or found["plan"]
    if moved is not None:
        # "we moved it to july" is the plan they already gave us, said again with a new date.
        # The words of the line are not a plan of their own ("You moved it to july").
        found.pop("plan", None)
        found.pop("plans", None)
    # "i said" is read before "i meant", because "no i meant to say bristol" is caught by the
    # "meant" pattern with "to" as its value if it gets there first.
    correction = (CORRECTION_SAID.search(text) or CORRECTION.search(text)
                  or CORRECTION_PAIR.search(text) or CORRECTION_NUMBER_PAIR.search(text)
                  or _a_day_taken_back(text)
                  or _a_moved_time(text) or CORRECTION_CLOCK.search(text)
                  or CLOCK_PREFERRED.search(text)
                  or CORRECTION_MAKE.search(text))
    # "make it"/"make that" is the one shape that names no old value, and it is also the shape a
    # half sentence arrives in: "my boiler is broken / make it stop". Whether it corrects anything
    # is the store's question (it knows what the line before said), so the shape goes along.
    made = correction is not None and correction.re is CORRECTION_MAKE
    hedged = None
    if correction is None:
        dated = (CORRECTION_DATE.search(text) or CORRECTION_DATE_GOING.search(text)
                 or CORRECTION_GOING_MOVED.search(text))
        if dated is not None:
            # A date is said back with its day and its month in it, which the one-word reader
            # keeps to a single value: "sorry, its the 4th of may" is the whole date.
            found["correction"] = {"to": _tidy(" ".join(dated.group("date").split())),
                                   "from": None}
    if correction is None and "correction" not in found:
        # The date reader above already named the value, and its value is the one to keep: the
        # bare reader matches the same line with the preposition still on it ("no in july" is
        # its value "in july"), and putting that over the date moved the month into the plan's
        # place ("you're going to In july next month").
        # A hedged figure is the same move as a bare one, and the readers below cannot see it:
        # the hedge sits where the value should start, so it is read here, before them.
        hedged = None if correction is not None else CORRECTION_HEDGED.search(text)
        if hedged is not None:
            correction = hedged
        bare = None if correction is not None else CORRECTION_BARE.search(text)
        # The word that says "no thanks" can arrive behind the apology the tail strip takes
        # off ("no idea sorry"): the value is what gets compared with them, so it is the value
        # that decides, and a line that names nothing is still not a correction.
        if bare is not None and bare.group(1).lower() not in CORRECTION_BARE_NO and (
                _the_value_alone(COPULA_SPLIT.split(bare.group(1))[0]).strip().lower()
                not in CORRECTION_BARE_NO):
            correction = bare
        if correction is None:
            named = NO_THEN_A_THING_NAMED.search(text)
            if named is not None and named.group(1).lower().split()[0] not in ANIMALS:
                correction = named
    if correction is None and moved is not None:
        found["correction"] = {"to": moved, "from": None}
    if correction is None:
        amount = AMOUNT_CORRECTION.search(text) or AMOUNT_CORRECTION_BARE.search(text)
        if amount:
            before = set(re.findall(r"[a-z']+", text[:amount.start()].lower())[-4:])
            if not before & AMOUNT_WISH:
                found["correction"] = {"to": amount.group(1).strip(" .,"), "from": None}
    if correction and not _is_only_the_take_back(correction.group(1), denials(text)):
        wrong = correction.group(2) if correction.re.groups > 1 else None
        # The value stops at a verb: "no i said bristol is fine" corrects the place to Bristol and
        # says nothing about "is fine", so the copula and what follows is not part of the value.
        value = _the_value_alone(COPULA_SPLIT.split(correction.group(1))[0])
        # "no, its on thursday", "no, in bristol": the preposition in front says what kind of value
        # this is and is not part of it, but CORRECTION_BARE reads the two words together ("On
        # thursday"), so the fact in hand never matched a day again and the correction was dropped
        # without a word. A line whose value is only the preposition keeps it ("no, on"), and the
        # value has to still read as one afterwards, so the strip is tried, not forced.
        without_it = re.sub(r"^(?:on|in|at)\s+", "", value, flags=re.I).strip()
        if without_it and a_value(without_it):
            value = without_it
        # A value said with the naming word in it is a name being put right, and the naming word
        # is the frame, not the name: "no its called tim" hands over "called tim" and the cat
        # was filed as "Called tim".
        value = the_name_in(value) or value
        # A figure is a value even when the word for it is one the pointer list holds. "one" is on
        # that list because "the other one" points at something and keeps nothing, but after
        # "actually just" it is the number the person changed: "i have two kids" then "actually
        # just one" said two children back, because no value reached the count reader.
        if a_value(value) or hedged is not None:
            found["correction"] = {"to": _tidy(value),
                                   "from": _tidy_apart(wrong) if wrong else None}
            if made:
                found["correction"]["make"] = True
    if "correction" not in found:
        # "make it" can name more than the value: "make it 800 for the trip" is not a value on its
        # own, so a line the shapes above matched but could not read still has to be read for the
        # number it puts up. The amount rule is the one that knows "for the trip" and "a month"
        # leave the number as it is.
        amount = AMOUNT_CORRECTION.search(text) or AMOUNT_CORRECTION_BARE.search(text)
        if amount:
            before = set(re.findall(r"[a-z']+", text[:amount.start()].lower())[-4:])
            if not before & AMOUNT_WISH:
                found["correction"] = {"to": amount.group(1).strip(" .,"), "from": None}
    # A value taken back and the right one after it: "no, not Friday, Monday". This is read
    # before the bare take-back below, because that pattern reads the first value only and takes
    # it away - "sorry, not peanuts, tree nuts" left the person with nothing on record.
    if "correction" not in found and found.get("drop") is None:
        pair = CORRECTION_NOT_PAIR.search(text)
        if pair is not None:
            right, wrong = _tidy(pair.group(2)), _tidy(pair.group(1))
            if (a_value(right) and a_value(wrong)
                    and right.lower() not in NOT_A_DAY and wrong.lower() not in NOT_A_DAY):
                found["correction"] = {"to": right, "from": wrong}
    # A name denied with the pronoun first: "no he isn't Dave" takes a value away and puts
    # nothing in its place, and "no he isn't, it's Dan" gives the right one after it. Read by
    # CORRECTION_PAIR it was the pronoun that became the value ("no hes not dave" filed "Hes"),
    # so this shape is read on its own, and only when the line says whose value it is - a pronoun
    # sweep over every denial would turn "no it isnt" into a correction of whatever came before.
    if "correction" not in found and found.get("drop") is None:
        denial = DENIAL_OF_A_VALUE.match(text)
        if denial is not None and not a_name_is_taken_back(text):
            said, wrong = denial.group("value"), denial.group("wrong")
            if said and denial.group("says") and a_value(said):
                from_wrong = (_tidy(wrong) if wrong and a_value(wrong)
                              and wrong.lower() != said.lower() else None)
                found["correction"] = {"to": _tidy(said), "from": from_wrong}
            elif said and not denial.group("says"):
                # The only value in the line is the one being denied, so nothing is kept: what
                # the store holds is either still right or was never said here.
                pass
    # A value taken back with nothing in its place: "sorry, not peanuts" says which one goes,
    # and the store is the only thing that can take it off the list it was on. This is its own
    # `if` on purpose: it was the `elif` of the block above, so when "make it" moved in between
    # them the take-back came to belong to the wrong branch and no line took anything back.
    if "correction" not in found and found.get("drop") is None:
        paired = CORRECTION_NOT_TO.search(text)
        if paired is not None:
            # "not lisbon, porto": the value after the one taken back is what they mean instead, so
            # this is a correction and the rest of the line stays where it was.
            wrong, right = _tidy(paired.group(1)), _tidy(paired.group(2))
            # "porto instead" is the value plus the word that says it replaces the other one.
            right = re.sub(r"\s+(?:instead|then|now)\b\W*$", "", right, flags=re.I)
            if (a_value(wrong) and a_value(right) and wrong.lower() not in NOT_A_DAY
                    and right.lower() not in NOT_A_DAY and wrong.lower() != right.lower()):
                found["correction"] = {"to": right, "from": wrong}
        gone = CORRECTION_NOT.search(text)
        if gone is not None and "correction" not in found:
            value = COPULA_SPLIT.split(gone.group(1))[0]
            if a_value(value) and value.lower() not in NOT_A_DAY:
                found["drop"] = _tidy(value)
    # "take that back" states no fact of its own: it undoes the line before it, and only when the
    # line has nothing else in it, so "im allergic to peanuts, take that back" keeps the peanuts
    # going up for the correction path to read.
    if not found and RETRACT.match(str(text or "").strip()):
        found["retract"] = True
    # The tone words go last, over everything the line left behind: "my sister is called meg
    # tbh" is a sister called Meg, and "i work as a nurse haha" is a nurse. A value that was
    # nothing but tone ("haha") leaves nothing to keep.
    for key, value in list(found.items()):
        if isinstance(value, str) and value:
            kept = no_tone(value)
            if kept:
                found[key] = kept
            else:
                del found[key]
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            # A retraction hung off the end of a line is not one of the things in it: "im allergic
            # to peanuts, take that back" is the peanuts going up, not a second allergy.
            cleaned = [(item, no_tone(item)) for item in value]
            found[key] = [kept for item, kept in cleaned
                          if kept and not RETRACT.match(kept)]
            if not found[key]:
                del found[key]
    for entry in found.get("others") or []:
        for key, value in list(entry.items()):
            if key == "who":
                continue
            if isinstance(value, str) and value:
                entry[key] = no_tone(value)
            elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                entry[key] = [kept for kept in (no_tone(item) for item in value) if kept]
    if "correction" not in found and CORRECTION_MARK.search(text):
        for key in CORRECT_FROM_MARK:
            value = found.get(key)
            if isinstance(value, list):
                value = value[0] if value else None
            if isinstance(value, (int, float)):
                value = str(value)  # an age or a budget is kept as a number
            if not isinstance(value, str) or not value.strip():
                continue
            if not a_value(value):
                continue
            found["correction"] = {"to": _tidy(value), "from": None}
            break
    return found
