"""Science: everyday physics, chemistry, biology and space, explained simply.

Answers lane domain. Each Entry is keyed by the meaning of the question (the thing and
what is being asked about it), not by one wording, so "why is the sky blue", "what makes
the sky blue" and "why does the sky look blue" all reach the same fact.

School-level explanations: the real mechanism in one or two sentences, then the detail
that makes it click. No invented numbers. The answers module turns the Entry into a reply.
"""
import re

from .health import HEADACHE_NO_DRUGS, NO_DRUGS
from ..compose.repair import owns_the_deed as _owns_the_deed
from .lookup import names_a_thing
from .lookup import (ASK_ABOUT, FEELING_WORDS, IMPROVE, NOT_A_NOSE, ORIGIN_ASK, all_of, entry,
                     not_a_count_for_the_box_or_the_dish, not_a_sleepy_body,
                     not_the_flat_you_live_in)

ANSWERS = ("science", "sleep")

# The person's own memory card must not take a line about somebody else's: "my dad is getting
# forgetful" and "she keeps forgetting things" are the memory-assessment entry's, which reads
# the relative in front of the forgetting. The pronoun forms have no relative to read, so they
# are held out here as well.
_ANOTHER_ADULTS_MEMORY = re.compile(
    r"\b(?:my|his|her|our|their|the)\s+(?:\w+\s+){0,2}"
    r"(?:mum|mom|mam|mother|dad|father|parent|parents|husband|wife|partner|spouse|other half|"
    # Not a child: a son forgetting his PE kit is a school-morning thing, not a memory
    # assessment, and the kit list is the answer to it.
    r"nan|nana|gran|granny|grandma|grandad|grandpa|grandmother|grandfather|"
    r"brother|sister|aunt|auntie|uncle|cousin|mother in law|father in law|friend|"
    r"neighbour|neighbor|boss|colleague|flatmate|housemate|carer|pal|chum|mate|"
    r"nephew|niece|grandchild|grandson|granddaughter|fiance|fiancee|stepmum|stepdad|missus|"
    r"girlfriend|boyfriend)\b|"
    r"\b(?:he|she|they)\s+(?:keeps?|is|are|has|have|always|never|used to)\b")
# Somebody else is still the subject when the somebody is a child: "my son forgets everything i
# tell him" is about him, even though a child's forgetting is not an assessment question.
_A_CHILD = r"(?:son|daughter|child|kid|kid|children|kids|toddler|teenager|teen|baby)"
_SOMEBODY_ELSE_IS_THE_SUBJECT = re.compile(
    r"\b(?:my|his|her|our|their|the)\s+(?:\w+\s+){0,2}" + _A_CHILD + r"\b|" +
    _ANOTHER_ADULTS_MEMORY.pattern)


def _not_somebody_elses_memory(understood):
    """True when the line is not about another adult forgetting. A `guard=` test.

    The carried words count as well as the line: a follow-up is answered on the line before it
    ("thats scary" after "my mum keeps forgetting things" is still her memory, not the speaker's),
    and this card is written in the first person.
    """
    from .habits import _words_of
    text = _words_of(understood)
    if not text:
        return True
    return not _SOMEBODY_ELSE_IS_THE_SUBJECT.search(text)


# A habit word names a thing that slipped - keys, a name, a tablet, a birthday - and those lines
# have their own cards (where to put the keys, the trick for a new name, the pill box, the calendar).
# What makes the difference is whether the line is asking about the illness: "is losing keys a sign
# of dementia" is the illness question, and the habit card is the wrong answer to it. So the habit
# words fence the card off only when the line does not name the illness, and the illness words are
# what the card is for.
_NAMES_THE_ILLNESS = re.compile(
    r"\bdementia\b|\balzheimers?\b|\balzheimer's\b|\bmemory clinic\b|"
    r"\bmemory assessment\b|\bearly onset\b|\bsigns? of (?:it|this|that)\b")
# The speaker's own errand: "i keep forgetting to book my daughter an eye test" and "ive forgotten
# to cancel the gas" are the speaker's to-do, not another person's memory. Both memory cards stood
# on the person word alone and answered these.
_MY_OWN_ERRAND = re.compile(
    r"\b(?:i|im|i'm|ive|i've)\b(?:\s+\w+){0,4}?\s+(?:keep\s+|kept\s+)?(?:forget|forgets|"
    r"forgetting|forgot|forgotten)\s+(?:about\s+)?to\b")


def _the_speaker_forgot_to_do_it(understood):
    """True when the line is the speaker forgetting to do a thing. A `guard=` test."""
    from .habits import _words_of
    text = _words_of(understood)
    return bool(text and _MY_OWN_ERRAND.search(text))


# A debt that slipped is not a memory question: "My mate owes me 50 quid and it's been months."
# then "He's not short of money, he just keeps forgetting." reached the memory-assessment card,
# because the errand's own person ("mate") was still in the chat and a forgetting word was in
# the line. The card is for the goings of a mind, not for money that has not arrived.
_MONEY_OWED = re.compile(
    r"\b(?:owes?|owed|owing|quid|pay (?:me )?back|paid back|repay|repays|borrowed|lent|"
    r"debt|debts|in arrears|wont pay|won't pay|not paid me|still hasnt paid|still hasn't paid)\b")


def _its_money_that_has_not_come_back(understood):
    """True when the chat is about a debt. A `guard=` test."""
    from .habits import _words_of
    text = _words_of(understood)
    return bool(text and _MONEY_OWED.search(text))


_A_HABIT_THING = re.compile(
    r"\b(?:names?|keys|glasses|wallet|purse|password|passwords|pin|birthdays?|anniversary|"
    r"tablets?|medication|medicines|pills|appointments?|shopping|bills?)\b")


def _a_habit_without_the_illness(understood):
    """True when the line is the speaker's own habit that slipped. A `guard=` test.

    Only the speaker's own: another person forgetting names or keys is part of the picture of
    their memory ("my husband cant remember names" is the assessment card), while "i keep
    forgetting names" is the trick for holding a new one.
    """
    from .habits import _words_of
    text = _words_of(understood)
    if not text:
        return False
    if _ANOTHER_ADULTS_MEMORY.search(text):
        return False
    return bool(_A_HABIT_THING.search(text)) and not _NAMES_THE_ILLNESS.search(text)


# A definition is answered when the line asks what the thing is, not when it only says a
# question word. The subject can arrive from the last turn ("i cant switch my brain off at
# night" ... "what helps"), so a bare "what" in an ask lets a definition claim a follow-up
# that asks for something to do. The ask is therefore the question frame as typed.
DEFINITION_ASK = ("what is", "what's", "what are", "what does", "what do", "how does",
                  "how do", "how is", "how are", "why is", "why are", "why does", "explain",
                  "tell me about", "define")

# "why do cows eat grass" and "how do plants eat" both name eating; only the second is a
# question about photosynthesis, so the animals that graze are kept out of the plant entries.
GRAZERS = ("cat", "cats", "dog", "dogs", "puppy", "pet", "pets", "cow", "cows", "rabbit",
           "rabbits", "horse", "horses", "sheep", "deer")

# A plant line with a pest, a fix or a watering in it is a how-to about the garden, not a question
# about how a plant works, so the photosynthesis and water-transport facts pass. It carries no bare
# "leaf", because _forms() collapses that with "leaves" and "why are my plant leaves pale" is the
# sunlight question.
PESTS_AND_CARE = ("slug", "slugs", "snail", "snails", "aphid", "aphids", "caterpillar",
                  "caterpillars", "pest", "pests", "bug", "bugs", "insect", "insects",
                  "eating my", "eats my", "ate my", "rid of", "stop", "killed", "kill",
                  "dying", "dead", "droop", "drooping", "wilt", "wilted", "yellow leaves",
                  "repot", "fertiliser", "fertilizer", "feed my", "prune", "lawn", "weed",
                  "weeds", "look after", "care for", "water my", "water them", "water it",
                  "how often", "how much water", "once a week", "shade", "frost",
                  "tomato plant", "my leaves", "yellow leaves", "leaves yellow",
                  "leaves are yellow", "houseplant", "houseplants", "plant food")
# PESTS_AND_CARE holds "houseplant" and "houseplants" because a pest answer must not take a
# houseplant pest. An entry whose whole subject *is* the houseplant cannot use it as an avoid:
# "my houseplant hasnt grown in months" was vetoed by the word it was asking about.
PLANT_CARE_AVOID = tuple(word for word in PESTS_AND_CARE
                         if word not in ("houseplant", "houseplants"))
WATERING = ("how often", "how much water", "water my", "water them", "water it",
            "water a", "should i water", "when to water", "once a week", "twice a week",
            "every day", "hose", "sprinkler", "tap water")

# The planets people ask about, with the number of confirmed moons we can state plainly.
MOONS = {"mercury": 0, "venus": 0, "earth": 1, "mars": 2, "jupiter": 95,
         "saturn": 146, "uranus": 28, "neptune": 16}

# Different ways of saying the morning is the hard part. Waking early and a low morning turn up
# together often enough that people say them as one thing, and a routine is the wrong reply to
# that half of the conversation.
LOW_MORNING = ("cant get out of bed", "can't get out of bed", "cannot get out of bed",
               "cant get up in the morning", "can't get up in the morning",
               "dont want to get up", "don't want to get up", "cant face the day",
               "can't face the day", "no point getting up", "no point in getting up",
               "no point at all", "hopeless", "worthless", "hate mornings",
               "cant get up", "can't get up", "struggling in the mornings",
               "struggling to get up", "not sleeping and not", "no energy for anything")

WAKE_AT_NIGHT = (
    "Waking in the night is normal - sleep runs in cycles of about ninety minutes - and the "
    "common patch is the small hours, around three. The fix is what you do in those minutes: "
    "do not check the clock, keep the light off, and if you are properly awake after about "
    "twenty minutes get up and sit somewhere dim with something dull until you feel heavy "
    "again. Keep the wake-up time the same, and go easy on alcohol and late coffee, because "
    "both knock you out and then wake you at four.")


# An early riser is not somebody lying awake at three: "i keep waking up at 5" is a body clock,
# and the bot already answers it ("that clockwork wake-up is your body clock"). But the hour is
# the setting and the staying asleep is the ask, so the hour only stands this entry down when the
# line says nothing about getting back to sleep. That is why the hours are here and not in the
# avoid list: "at 5" as an avoid word swallowed "my alarm goes off at 5 and i cant get back to
# sleep" as well, which is the waking this entry is for.
EARLY_HOUR = (
    r"\b(?:at|by|around|about)\s*(?:5|five|6|six)\b",
    r"\b(?:5|five|6|six)\s*(?:am|a\.m\.|o'?clock)\b",
)
STILL_ASLEEP = (
    r"\bback\s+(?:off\s+)?to\s+sleep\b",
    r"\bstay(?:ing)?\s+asleep\b", r"\bsleep(?:ing)?\s+through\b",
    r"\bwake\s+(?:up\s+)?(?:several|a\s+few|couple|twice|three)\s+times\b",
)


def _dinosaurs(memory, understood):
    """The age of the dinosaurs when the line asks when, and the end of them when it asks why.

    "when did the dinosaurs live" and "how long ago were the dinosaurs" were a hedge, because the
    row only held the asteroid. The two questions are the same animal and one answer each.
    """
    clean = ((understood or {}).get("clean") or (understood or {}).get("plain") or "").lower()
    if re.search(r"when|how long|how old|hoe long|what era|which era|what period|"
                 r"which period|million years", clean):
        return ("The dinosaurs were around for about 165 million years, from roughly 230 million "
                "years ago to 66 million years ago, in the Triassic, Jurassic and Cretaceous "
                "periods. The first ones were small and two-legged, the biggest - the long-necked "
                "sauropods and then T. rex - came late, and by the end they were on every "
                "continent including Antarctica.")
    return ("An asteroid about 10 km wide hit what is now Mexico 66 million years ago. The dust "
            "it threw up blocked the sun for years, plants and the animals that ate them "
            "collapsed, and the dinosaurs that could not fly died out; birds, which are their "
            "descendants, survived.")


# The words a person uses to say they are tired, and nothing else. The tiredness key names
# "most days" and "most weeks" in both of its parts, so a line that says one of them satisfied
# the whole key on its own: "my neighbour parks across my drive most days" was answered with the
# tiredness card, and so were ten other ordinary lines that end the same way. The guard asks the
# line to say the feeling before the row can answer at all; a card about being tired is only
# ever the answer to a line that says someone is tired.
# One list, two readers: the guard below asks a line to say the feeling, and the row's own key
# splices the same tuple into its subjects, so a phrasing added here covers both and the two can
# never drift apart. The drift was the fault three readers found: `_TIRED` held `no energy` but
# not `zero energy`, so a line that named the feeling lost the card as soon as the frequency
# phrase stopped counting as a subject.
_FEELINGS = ("tired", "knackered", "exhausted", "exhausting", "worn out", "drained",
             "run down", "shattered", "no energy", "any energy", "falling asleep",
             "more energy", "energy levels", "energy back", "get energy",
             # the words people use for it in their own mouth, which the guard was missing
             "zero energy", "low on energy", "wiped out", "zonked", "lethargic",
             "no get up and go", "no oomph", "keep my eyes open", "yawning", "sleepy",
             "shattered all the time", "dead on my feet")

# The phrases the row's key takes from the same tuple, minus the ones another row already owns
# ("sluggish" and "flagging" are the more-energy row's own words) and minus the bare words that
# are a machine's as often as a person's ("exhausted" strips to "exhaust"; see the row's comment).
_KEYED_FEELINGS = tuple(p for p in _FEELINGS if p not in (
    "exhausted", "exhausting", "drained", "run down", "shattered", "tired",
    "more energy", "energy levels", "energy back", "get energy", "falling asleep"))

_TIRED = re.compile(r"\b(" + "|".join(_FEELINGS) + r")\b")


def _names_the_feeling(understood):
    """True when the line says being tired in some form, not only how often it happens."""
    if not isinstance(understood, dict):
        return False
    # All three readings: the raw line keeps a missing space ("imtired all the time") inside
    # "imtired", and only the cleaned text and the words have it as two.
    parts = [understood.get("text") or "", understood.get("clean") or "",
             " ".join(understood.get("words") or ())]
    return any(_TIRED.search(str(part).lower()) for part in parts if part)

def _any_hit(patterns, text):
    return any(re.search(pattern, text) for pattern in patterns)


# A row with someone is not a fall. "me and my mum fell out" and "my dad and i fell out last
# week" were answered with the falls review ("Falls are usually several small things adding up
# ... ask the GP for a falls review"), and the second turn then inherited it: "she said i never
# visit" got "They check blood pressure lying and standing ... a falls clinic". Bare "out" cannot
# be an avoid word, because "my mum fell out of bed" is a line the falls card exists for, so the
# fence is the phrase: falling out *of* something is a fall, falling out *with* someone is a row.
# "fell about laughing" is not a fall either.
FELL_OUT = re.compile(
    r"\bf(?:ell|all|alls|alling|allen)\s+out\b(?!\s+of\b)|\bfell\s+about\b")


def _a_fall_and_not_a_row(understood):
    """Whether the line is about a fall at all, rather than a row with somebody.

    Only the phrases people use for a falling-out stand the card down: a fall out of something
    ("out of bed", "out of the car", "out of a tree") keeps it, which is the whole point of the
    key words being there.
    """
    if not isinstance(understood, dict):
        return True
    words = " ".join(str(word).lower() for word in (understood.get("words") or ()))
    text = " ".join((str(understood.get("clean") or ""), str(understood.get("text") or ""),
                     str(understood.get("raw") or ""), words)).lower()
    text = re.sub(r"[^a-z0-9' ]+", " ", text)
    return not FELL_OUT.search(text)


# A thing that stands up is not a person who has fallen. "How do tall buildings not fall over",
# a tower crane, the leaning tower and a tall tree were all answered with the falls-in-old-age
# review, because the entry keys a bare "fall" beside "how do i". The words could not simply go
# in its `avoid`: an avoid is unconditional, so "why does my nan keep falling over near the plant
# pots" lost the falls review the moment "plant" was fenced - the person is the subject there and
# the plant is only where it happened. So the fence reads the whole line instead: somebody falling
# keeps the review, and a structure or a plant as the subject is the row at the end of this file.
STANDS_UP_THINGS = re.compile(
    r"\b(?:buildings?|skyscrapers?|high[ -]?rises?|tower blocks?|blocks? of flats|towers?|"
    r"cranes?|bridges?|chimneys?|pylons?|statues?|cathedrals?|domes?|monuments?|trees?|"
    r"forests?|woods|houseplants?|plants?|seedlings?|tomato(?:es)?|flowers?|tulips?|"
    r"daffodils?|sunflowers?|roses?|hanging baskets?|shrubs?)\b")

PEOPLE_WHO_FALL = re.compile(
    r"\b(?:nan|nana|gran|granny|grandma|grandad|grandpa|grandmother|grandfather|mum|mum's|"
    r"mom|mother|dad|father|husband|wife|partner|sister|brother|aunt|uncle|friend|neighbour|"
    # "my" and "i" are not here on purpose: "why do my plants fall over" is the plant, and the
    # only person words that mean a person are the ones below.
    r"neighbor|carer|patient|resident|she|he|her|him|his|they|them|someone|somebody|"
    r"elderly|pensioner|oap|old people|old lady|old man|people|person)\b")


def _a_person_who_falls(understood):
    """Whether the line is about somebody falling rather than why a thing stands up.

    A person named in the line is the subject: "my nan fell over by the trees" is the falls
    review even though a tree is in it. With nobody named, a structure or a plant in the line is
    the subject, and the tall-things entry answers it. A line that names neither keeps the review,
    because an unsteady old person who is not named ("why do old people fall over") is still the
    person this entry is for.
    """
    if not isinstance(understood, dict):
        return True
    said = " ".join(str(part or "") for part in ((understood.get("clean"),
                                                   understood.get("text")))).lower()
    said = re.sub(r"[^a-z0-9' ]+", " ", said)
    if PEOPLE_WHO_FALL.search(said):
        return True
    return not STANDS_UP_THINGS.search(said)


# A fall is a body going down to the floor. Everything else with "fall" in it is another
# question, and each of these was answered with the falls review for the old and unsteady:
#
#     my boiler pressure keeps falling   -> a falls review, above "the second one is worth acting on"
#     it keeps falling off the wall      -> the same, for a shelf
#     my calendar keeps falling off the wall
#     i nearly fell over laughing        -> the same, for a joke
#     i keep falling behind              -> a lesson on gravity
#     i keep falling for the wrong people
#
# Two shapes decide it, and neither is a word list of things that fall. A word in front of the
# verb that is not a person is the thing that fell: "pressure", "calendar", "it". And a fall
# with a place it is going, or a reason, is the phrase people write rather than the event:
# "behind" is falling behind on work, "for" is falling in love, "laughing" is a joke.
A_FALL_VERB = re.compile(r"\bf(?:all|alls|alling|ell|allen)\b")
BEFORE_THE_FALL = re.compile(
    r"([a-z']+)\s+(?:keeps?|kept|is|are|was|were|has|have|had|just|nearly|almost|"
    r"keep|would|did|didnt|never|still|always)\s+(?:f(?:all|alls|alling|ell|allen))\b")
NOT_A_FALL_PHRASE = re.compile(
    r"\bf(?:all|alls|alling|ell|allen)\s+(?:(?:over|down|about|in|out)\s+)?"
    r"(?:behind|for|short|through|flat|foul|silent|quiet|ill|asleep|pregnant|in love|"
    r"into place|in place|laughing)\b")
PEOPLE_WHO_ARE_THE_SUBJECT = PEOPLE_WHO_FALL.pattern

# Words that sit in front of a verb without being the thing it happens to. Every one of these
# was read as the subject on the first pass, and "my nan is 89 and keeps falling" lost the falls
# card to an "and".
NOT_THE_SUBJECT = frozenset("""
    and but so then than that which who whom whose where when what why how if or nor yet though
    although while until till since because as also still just now even ever never always
    sometimes often usually again once only really nearly almost quite very too much more most
    s t d ll re ve m
    """.split())


def _a_thing_falls_not_a_person(understood):
    """False when the thing that falls is a thing, or the "fall" is a phrase.

    The card is for a person going down, so this reads who or what is doing the falling. A
    person word in front of the verb is a body: "my mum keeps falling" is the card. Anything
    else in front of the verb - "pressure", "calendar", "it" - is the thing that fell, and
    nothing here is about a person's balance. With no word in front of the verb the line keeps
    the card, because "why do old people fall over" names nobody ahead of the verb and is still
    the person this entry is for.
    """
    if not isinstance(understood, dict):
        return True
    said = " ".join(str(part or "") for part in ((understood.get("clean"),
                                                  understood.get("text"),
                                                  understood.get("raw")))).lower()
    said = re.sub(r"[^a-z0-9' ]+", " ", said)
    if NOT_A_FALL_PHRASE.search(said):
        return False
    for subject in BEFORE_THE_FALL.findall(said):
        if subject in ("i", "we", "you"):
            continue
        if re.search(PEOPLE_WHO_ARE_THE_SUBJECT, subject):
            continue
        # a joining word is not what fell: "my nan is 89 and keeps falling" is still her
        if subject in NOT_THE_SUBJECT:
            continue
        return False
    return True


def _a_fall_a_person_had(understood):
    """The fences in one, because an entry takes a single guard.

    `_a_fall_and_not_a_row` keeps falling out with somebody off the card; `_a_person_who_falls`
    keeps a building or a plant off it; `_a_thing_falls_not_a_person` keeps a boiler's pressure,
    a calendar on the wall and "falling behind" off it. All have to say yes for the falls review
    to answer.
    """
    return (_a_fall_and_not_a_row(understood) and _a_person_who_falls(understood)
            and _a_thing_falls_not_a_person(understood))


# A mouth that grinds belongs to one of two people, and they need different answers. A baby's
# brand-new teeth meet and click as the bite settles: common, harmless, and no guard is fitted to
# a baby. An adult's grinding is a dentist's job, with a splint to protect the enamel. The entry
# said the adult answer to both, so "how do i stop my baby grinding her teeth" came back "ask your
# dentist for a night guard" (main, 2026-11-06).
GRINDING_BABY = ("baby", "babies", "baby's", "toddler", "toddlers", "newborn", "newborns",
                 "months old", "month old", "1 year old", "one year old", "2 year old",
                 "two year old", "3 year old", "three year old", "first teeth", "new teeth",
                 "baby teeth", "milk teeth", "teething", "child", "children", "kid", "kids",
                 "little one", "my little", "my son", "my daughter", "my boy", "my girl")

GRINDING_ADULT = ("Ask your dentist for a night guard: a splint made for your teeth protects the "
                  "enamel and takes the load off the jaw, and most practices can fit one in about a "
                  "week. Cut caffeine and alcohol in the evening, and when you catch yourself "
                  "clenching, rest your tongue behind your top teeth with your jaw slack. If you "
                  "wake with a sore jaw or headaches, tell your dentist rather than buying a "
                  "one-size guard online.")

# "is a cold the same as the flu" is a no and "can i get flu more than once" is a yes, and the
# cold-vs-flu row answers both: it reads the line and says which sentence it owes, the way a row's
# `guard=` reads the line. A line asking what the difference is wants the two paragraphs, not a
# verdict, and gets no sentence.
_SAME_OR_TWICE = re.compile(r"\bsame\b|\bdifference\b", re.I)
_TWICE = re.compile(r"\btwice\b|\bagain\b|more than once", re.I)


def _cold_or_flu_verdict(understood):
    text = str((understood or {}).get("text") or "").lower()
    if _SAME_OR_TWICE.search(text):
        return "No"
    if _TWICE.search(text):
        return "Yes"
    return ""


BABY_GRINDING = ("Mostly nothing to fix: a child grinding brand-new teeth is common, harmless "
                 "and passes as the bite settles, and sore gums make a teething baby grind. It "
                 "does not damage the teeth, and no guard goes on a child whose teeth are still "
                 "coming through. If it carries on for months, or comes with a sore jaw, mention "
                 "it at the next dental check.")


# The hangover card answers two questions: what to do about one, and how long it lasts. "how do i
# get over a hangover" wants the cure first, and "how long does a hangover last" wants the hours -
# the card answered that with what to drink, which is not the length of anything.
_HANGOVER_LENGTH = (
    "A hangover peaks at about 12 hours and is usually gone within a day, with the headache and "
    "the tiredness easing as it goes; a heavy one can run into a second day. ")
_HANGOVER_CURE = (
    "There is no cure, only time: what your body needs back is water and sleep. Drink a pint "
    "of water or an electrolyte drink, eat something plain even if you don't want it, and "
    "take paracetamol if you want a painkiller, with food. Don't have another drink to steady "
    "yourself; a pint of water before bed helps a little, and eating before you started "
    "helps more.")
_HANGOVER_LENGTH_ASK = re.compile(
    r"\bhow long\b|\bhow many (?:hours|days)\b|\bwhen (?:will|does|do|should)\b|"
    r"\bhow soon\b|\bhow many hours does\b|\blasts?\b|\blast\b", re.I)


def _hangover(memory, understood):
    """The hours first when the line asks how long it lasts, the cure first otherwise."""
    said = "%s %s" % (str((understood or {}).get("clean") or ""),
                      " ".join(str(word) for word in ((understood or {}).get("words") or ())))
    if _HANGOVER_LENGTH_ASK.search(said):
        return _HANGOVER_LENGTH + _HANGOVER_CURE
    return _HANGOVER_CURE


def _grinding(memory, understood):
    """The baby's answer or the adult's, from the person the line is about."""
    clean = " " + str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower() + " "
    clean = re.sub(r"[^a-z0-9' ]+", " ", clean)
    if any(" " + word + " " in clean for word in GRINDING_BABY):
        return BABY_GRINDING
    if _asks_what_it_is(clean):
        return GRINDING_WHAT
    return GRINDING_ADULT


# "what is bruxism" and "what is teeth grinding" ask for the thing itself, not for a night
# guard: the person has usually just been given the word by a dentist and wants to know what it
# means. Whoever asks what it is may be about to do something about it, so the answer ends on
# what is worth doing.
GRINDING_WHAT = ("Bruxism is grinding or clenching your teeth, usually in your sleep, and most "
                 "people only find out from a dentist or a partner rather than noticing it. The "
                 "pressure is what wears enamel and leaves the jaw achey, and it is often worse "
                 "with stress, caffeine and alcohol in the evening. A night guard from a dentist "
                 "protects the teeth, and it is worth asking about one if you wake with a sore "
                 "jaw or headaches.")

# The ways a line opens when it asks what a thing *is* rather than what to do about it. Only the
# opening counts, so "what is causing my grinding" keeps the advice.
_WHAT_IS_IT = ("what is ", "what's ", "whats ", "what are ", "explain ", "define ",
               "meaning of ", "what does")


def _asks_what_it_is(clean):
    said = (clean or "").strip()
    return any(said.startswith(opening) for opening in _WHAT_IS_IT)


# A night the body or the mind caused ("i keep waking at 3am with pain", "i was up all night
# coughing", "i keep waking at 3am because i am so stressed about work") is not a body-clock
# question, and the routine below talks past it. chat.py has the answer that names the cause,
# so this entry stands down and lets it speak. The test is the understanding's own reading of
# what the line is about, which is a better judge than a word list: a plain "i keep waking at
# 3am" is about sleep and keeps the routine; a line whose reading carries health or feelings has
# a cause in it, and the cause is the question.
NIGHT_CAUSE_TOPICS = ("health", "feelings")
# A cheap net under the reading, for the line that names a symptom in words the reader does not
# file under health ("my ear is killing me at 3am and i cant get back to sleep").
NIGHT_SYMPTOM = ("pain", "painful", "ache", "aches", "aching", "achy", "hurt", "hurts",
                 "hurting", "cramp", "cramps", "cough", "coughing", "tooth", "toothache",
                 "headache", "headaches", "migraine", "heartburn", "reflux", "nausea",
                 "nauseous", "fever", "temperature", "itch", "itching", "sore", "swollen",
                 "stiff", "restless legs", "sick", "throwing up", "period pain")


def _night_waking(memory, understood):
    """The early-waking answer, or nothing when the waking is part of a low morning.

    The two come together often enough that people say them as one thing: "i cant get out of bed
    most mornings" and then "and i keep waking up at 5". What that second line needs is the care
    the first one got, not a sleep-hygiene list, so the conversation decides - and only the
    conversation, because "i keep waking up at 5" on its own is a sleep question.
    """
    said_so_far = " ".join(
        str((understood or {}).get(key) or "") for key in ("clean", "norm", "plain"))
    topics = (understood or {}).get("topics") or ()
    if any(topic in NIGHT_CAUSE_TOPICS for topic in topics):
        return None
    if _any_hit(NIGHT_SYMPTOM, said_so_far):
        # the reason they were awake is the question: the cause gets named, not the routine
        return None
    if _any_hit(EARLY_HOUR, said_so_far) and not _any_hit(STILL_ASLEEP, said_so_far):
        return None
    try:
        from ..memory import thread
        said = " ".join((text or "").lower() for text, _reading in thread.user_lines(memory))
    except Exception:  # noqa: BLE001 - no history only means no guard
        return WAKE_AT_NIGHT
    if any(phrase in said for phrase in LOW_MORNING):
        return None
    return WAKE_AT_NIGHT


# The named moons are the ones a person can actually do something with: the four Galilean moons
# of Jupiter and the one moon of Saturn anybody can see. Asking for the names was a shrug while
# "how many moons does jupiter have" was answered.
NAMED_MOONS = {
    "jupiter": "Io, Europa, Ganymede and Callisto are the four worth knowing - the ones Galileo "
               "saw in 1610 - and Europa is the one with an ocean under the ice",
    "saturn": "Titan is the one worth knowing - bigger than Mercury, with lakes of methane - then "
              "Enceladus, Rhea, Iapetus and Mimas",
    "mars": "Phobos and Deimos, both small lumps of rock no more than twenty-odd kilometres "
            "across",
    "uranus": "Titania, Oberon, Umbriel, Ariel and Miranda, all named after Shakespeare and Pope "
              "characters",
    "neptune": "Triton, the big one, which orbits backwards and is probably a captured "
               "Kuiper-belt object",
}


def _moons(memory, understood):
    """Answer for the planet named in the line, or the whole solar system."""
    clean = (understood or {}).get("clean") or ""
    if any(word in clean for word in ("name", "called", "which moon", "which moons", "list")):
        if "earth" in clean:
            return ("Just the Moon, the fifth largest in the solar system and the only "
                           "other world people have stood on.")
        for planet in ("jupiter", "saturn", "mars", "uranus", "neptune"):
            if planet in clean:
                return NAMED_MOONS[planet] + "."
        return ("Earth's is the Moon, Mars has Phobos and Deimos, and the four big Jovian moons "
                "are Io, Europa, Ganymede and Callisto. Most of the hundreds the counts refer to "
                "are unnamed rocks a few kilometres across.")
    if "most" in clean and not any(name in clean for name in ("earth", "mars", "jupiter")):
        return "Saturn has the most confirmed moons, more than 140, ahead of Jupiter at about 95."
    for planet in ("jupiter", "saturn", "uranus", "neptune", "mars", "earth", "venus",
                   "mercury"):
        if planet in clean:
            count = MOONS[planet]
            if count == 0:
                return f"{planet.capitalize()} has no moons."
            if count == 1:
                return f"{planet.capitalize()} has one moon."
            return f"{planet.capitalize()} has {count} confirmed moons."
    return ("Mercury and Venus have none, Earth has one and Mars has two; the gas giants have "
            "dozens, with Saturn topping the list at more than 140.")

# --- school-level numbers and who found what ---------------------------------
# One table of discoveries, each a whole sentence, answers "who discovered penicillin" and
# every other wording of the same question, so a new discovery is a line of data rather
# than a new entry. The key is the thing discovered, lower case, as it is typed.
DISCOVERERS = {
    "penicillin": ("Alexander Fleming found penicillin in 1928, when a mould that had drifted "
                   "onto a petri dish killed the bacteria round it."),
    "gravity": ("Isaac Newton worked out the law of gravity in 1687, and the same rule still "
                "covers a falling apple and an orbiting moon."),
    "evolution": ("Charles Darwin set out evolution by natural selection in 1859, in On the "
                  "Origin of Species, with Alfred Russel Wallace reaching the same idea at the "
                  "same time."),
    "natural selection": ("Charles Darwin set out natural selection in 1859, in On the Origin of "
                          "Species."),
    "x-rays": ("Wilhelm Rontgen discovered X-rays in 1895, and won the first Nobel Prize in "
               "Physics for them."),
    "x rays": ("Wilhelm Rontgen discovered X-rays in 1895, and won the first Nobel Prize in "
               "Physics for them."),
    "radioactivity": ("Henri Becquerel found radioactivity in 1896; Marie and Pierre Curie then "
                      "did the chemistry that explained it."),
    "dna": ("The structure of DNA was worked out by James Watson and Francis Crick in 1953, "
            "using Rosalind Franklin's X-ray photographs."),
    "the electron": ("J. J. Thomson discovered the electron in 1897."),
    "oxygen": ("Joseph Priestley isolated oxygen in 1774, and Carl Wilhelm Scheele had found it "
               "two years earlier without publishing first."),
    "the vaccine": ("Edward Jenner made the first vaccine in 1796, using cowpox against "
                    "smallpox."),
    "vaccines": ("Edward Jenner made the first vaccine in 1796, using cowpox against smallpox."),
}


def who_discovered(memory, understood):
    """The sentence for the thing the line names, or None so another entry can answer."""
    clean = (understood or {}).get("clean") or (understood or {}).get("text") or ""
    clean = clean.lower().replace("'", "")
    best = None
    for thing in DISCOVERERS:
        if re.search(r"\b" + re.escape(thing) + r"\b", clean):
            if best is None or len(thing) > len(best):
                best = thing
    if best is None:
        return None
    return DISCOVERERS[best]


# "i sleep about six hours and i never go outside" is the middle of a conversation about being
# tired: the reply has to answer the number they gave, not read the guideline back at them.
SLEEP_SAID = re.compile(r"\b(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
                        r"twelve)\s*(?:-\s*\d{1,2}\s*)?(?:hours?|hrs?|h)\b", re.IGNORECASE)
SLEEP_NUMBER = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
SLEEP_WORD = {6: "Six", 5: "Five", 4: "Four", 7: "Seven", 8: "Eight", 9: "Nine",
              10: "Ten", 11: "Eleven", 12: "Twelve"}
SLEEP_TALK = re.compile(r"\b(?:sleep|sleeping|slept|sleeps|bed|hours?)\b", re.IGNORECASE)


def _sleep_said(clean):
    """The hours the person says they get, when they are telling rather than asking."""
    match = SLEEP_SAID.search(clean)
    if not match or not SLEEP_TALK.search(clean):
        return None
    word = match.group(1).lower()
    hours = SLEEP_NUMBER.get(word) or int(word)
    return hours if 1 <= hours <= 14 else None


def _sleep_hours(memory, understood):
    """Hours of sleep, said for the age the line names: a teenager's night is not an adult's."""
    clean = ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    said = _sleep_said(clean)
    if any(word in clean for word in ("teenager", "teenagers", "teen", "teens", "teenage",
                                      "15", "16", "17", "sixteen", "fifteen", "seventeen")):
        return ("Teenagers need eight to ten hours a night, and their body clock runs late, so an "
                "11pm bedtime is not late for them. The fix that helps most is a light morning "
                "and the same wake-up time at weekends.")
    if any(phrase in clean for phrase in ("over 65", "over-65", "older", "elderly", "pensioner",
                                          "70")):
        return ("Seven to eight hours is usual after 65, and the sleep gets lighter and more "
                "broken, which is ordinary. Twenty-minute naps are fine; a long afternoon sleep "
                "is what makes the night worse.")
    if said is not None and said < 7:
        return ("%s hours is on the short side: most adults need seven to nine, and the shortfall "
                "shows as yawning, coffee and losing the thread by mid-afternoon. Half an hour "
                "earlier to bed, and the same wake-up time every day, is the fix - a long weekend "
                "lie-in is not." % SLEEP_WORD.get(said, said))
    if said is not None and 7 <= said <= 9:
        # "is eight hours enough" wants a yes first; "i get eight hours" wants the guide.
        yes = "Yes - " if re.search(r"\b(enough|ok|okay|fine|normal)\b", clean) else ""
        return ("%s%s hours is inside the seven to nine most adults need, so there is nothing to "
                "fix if your days are fine. If you are yawning by mid-afternoon anyway, half an "
                "hour earlier to bed does more than a weekend lie-in."
                % (yes, SLEEP_WORD.get(said, said).lower() if yes else SLEEP_WORD.get(said, said)))
    if said is not None and said > 9:
        return ("%s hours is more than an adult needs, and the extra is not doing anything for "
                "you. Long nights after a short week are fine; sleeping that long every night and "
                "still waking unrefreshed is worth a word with the GP." % SLEEP_WORD.get(said, said))
    return ("Most adults do best on seven to nine hours, but the number is a guide and the test "
            "that matters is how you are by mid-afternoon: yawning, reaching for coffee and "
            "losing the thread on six hours means you are short, whatever the chart says. The fix "
            "is usually a 30-minute earlier bedtime rather than a lie-in at the weekend, and "
            "keeping the wake-up time the same even after a bad night. Some people genuinely run "
            "fine on six and it runs in families; if your days are fine, the number is not a "
            "problem to solve.")


# The question "is it free" wants the cost first; "how often" wants the interval first. Both are
# the same entry, so the reply reads which one the line asked.
EYES_COST = re.compile(r"\b(?:free|cost|costs|pay|paid|price|how much|charge|charges|"
                       r"afford|nhs)\b", re.IGNORECASE)


def _eyes_test(memory, understood):
    """The sight-test reply: the money first when the line asks about the money."""
    clean = ((understood or {}).get("clean") or (understood or {}).get("text") or "")
    money = ("free if you are under 16, over 60, or on some benefits or a low income - otherwise "
             "about £25 to £45")
    when = ("every two years suits most adults, and every year from 70 or if you have diabetes, "
            "glaucoma in the family or a big change in your vision")
    if EYES_COST.search(clean):
        return ("In the UK a sight test is " + money + ". It checks eye health as well as glasses, "
                "and " + when + ".")
    # "should i get an eye test" wants a yes; "how often do i need one" wants the interval.
    asks_when = re.search(r"\b(?:how often|how frequently|when|how soon)\b", clean, re.IGNORECASE)
    says_yes = (re.search(r"\b(?:should|shall|ought)\b", clean, re.IGNORECASE) and not asks_when)
    return (("Yes - a sight test " if says_yes else "A sight test ") + when + ". It is " + money + ".")


_MED_MISSED = re.compile(
    r"\b(missed|miss|forgot|forgotten|skipped|skip)\b|\brain out\b|\bran out\b")
_MED_DOUBLE = re.compile(r"\b(double|doubled|doubling|two|2|extra|catch up|catch-up|twice)\b")
_MED_REPEAT = re.compile(
    r"\b(keep|keeps|kept|always|forget|forgets|forgetting|remember|remembers|remembering|muddle|"
    r"muddled|mixed up)\b")
_MED_SUGAR = re.compile(r"\b(diabetes|diabetic|insulin|hypo|blood sugar\w*)\b")
_MED_CONFUSED = re.compile(r"\b(confused|confusion|muddled|not himself|not herself)\b")
# Confusion about *the tablets* is a packet muddle, not a new confusion: "my dad is confused about
# which tablets to take" wants the box and the fortnight pattern, and it is the same answer whether
# it is said about himself or about her. The medical paragraph below is for confusion that is new,
# or that comes with a red flag, and those lines say so.
_MED_TABLET_MUDDLE = re.compile(
    r"\b(confus\w*|muddled|muddle|mixed\s+up)\b[^.?!]{0,20}"
    r"\b(about|over|with|by|between)\b[^.?!]{0,24}"
    r"\b(tablets?|pills?|medicines?|medication|dose|doses|packet|blister|boxes|"
    r"which\s+(?:ones?|tablets?|pills?)|what\s+to\s+take|when\s+to\s+take)\b"
    r"|\b(tablets?|pills?|medicines?|medication|doses?)\b[^.?!]{0,12}"
    r"\b(muddled|confused|mixed\s+up)\b")
_MED_CONFUSED_NEW = re.compile(
    r"\b(suddenly|sudden|since|yesterday|tonight|today|this\s+week|last\s+night|overnight|"
    r"started|for\s+days?|for\s+hours?|fever|temperature|fell|fallen|fall|not\s+eating|"
    r"cannot\s+wake|can'?t\s+wake|out\s+of\s+it|drowsy|sleepy|shaky|sweaty)\b")
_MED_TOO_MUCH = re.compile(
    r"\b(took|taken|had|swallowed)\s+(two|2|an extra|extra|double)\b|\bdouble(d)?\s+(up|my)\b|"
    r"\btwice\s+(today|already|by mistake)\b|\bby mistake\b|\baccident\w*\b|\binstead\b")

_MED_DOUBLE_ANSWER = (
    "Never double up to catch up: skip the missed dose and take the next one at its usual time. "
    "Check the leaflet or ask a pharmacist first, because a few medicines (insulin, blood thinners, "
    "epilepsy tablets, the contraceptive pill) are exceptions where an extra dose is the right "
    "thing.")
_MED_BOX = (
    "A weekly box or a blister pack from the chemist - most do it free - is what stops the next one "
    "being missed: fill it together on a Sunday, write the times on the lid and set a phone alarm "
    "for each dose.")
_MED_ROUTINE = (
    "A weekly box or a blister pack from the chemist is the fix: fill it together on a Sunday, "
    "write the times on the lid and set a phone alarm for each dose. If the same one keeps being "
    "missed or taken twice, ask the GP or the pharmacist for a medicines review - they can often "
    "cut the number of tablets as well as time them.")
_MED_CONFUSED_ANSWER = (
    "New confusion in someone who takes tablets every day is worth a same-day call to their GP or "
    "111: it can be an infection, a side effect, or a low blood sugar if they have diabetes. Test "
    "their blood sugar if they have a meter, and ring 999 if they cannot be woken or cannot swallow."
    )
_MED_TOOK_TWO = (
    "Ring 111 or ask a pharmacist now, before your next dose: for most tablets an accidental double "
    "means waiting longer before the next one rather than skipping it, and they will tell you which "
    "for yours. Take nothing more in the meantime, and get seen straight away if you feel faint, very "
    "sleepy or sick.")
_PILL_SEX = re.compile(
    r"\b(sex|unprotected|condom|condoms|intercourse|slept with)\b|\bhad it\b")
_PILL_MINI = re.compile(r"\b(mini pill|desogestrel|cerazette|progestogen only|progesterone only)\b")


def _missed_pill(memory, understood):
    """A missed contraceptive pill is the one missed dose with its own rule.

    "skip it and carry on" is wrong here twice over: one missed pill can let ovulation through, so
    the next seven days need condoms, and anything that already happened needs emergency
    contraception, which a pharmacy gives free and which works best the sooner it is taken.
    """
    clean = ((understood or {}).get("clean") or "").lower()
    first = ("Take the missed pill as soon as you remember, then carry on at your usual time, and "
             "use condoms for the next 7 days.")
    if _PILL_MINI.search(clean):
        first = ("Take the missed mini pill as soon as you remember - the window is 12 hours (3 "
                 "hours for the older progestogen-only pills), and a later one counts as missed - "
                 "and use condoms for the next 7 days.")
    return (first + " If you had sex in those days, get emergency contraception today: a pharmacy "
            "gives it free without an appointment and it is licensed up to 5 days, but it works "
            "best the sooner it is taken.")


_MED_RAN_OUT = re.compile(r"\b(ran out|run out|running out|out of my|out of her|out of his)\b")
_MED_CRITICAL = re.compile(
    r"\b(epilepsy|epileptic|anti-epileptic|seizures|warfarin|blood thinner|blood thinners|"
    r"clot|thyroid|levothyroxine|heart tablets|lithium|steroids|prednisolone|immunosuppressant)\w*",
    )
_MED_RAN_OUT_ANSWER = (
    "A pharmacist can give most repeat medicines an emergency supply of up to 30 days without a "
    "prescription, so ring the pharmacy first, then 111 or the GP surgery if they cannot help "
    "today. Do not just stop taking them: some tablets are dangerous to stop suddenly.")
_MED_CRITICAL_ANSWER = (
    "Epilepsy medicines, blood thinners, thyroid and heart tablets each have their own rule for a "
    "missed dose, and the leaflet in the box says which - ring the pharmacist or your GP surgery and "
    "they will tell you what to do today. Do not double up in the meantime.")
_MED_THIRD = re.compile(
    r"\bmy (mum|mother|mam|mom|dad|father|nan|nanna|gran|granny|grandma|grandad|grandpa|wife|"
    r"husband|partner|sister|brother|aunt|uncle|friend)\b|\b(she|he|they) (keeps|keep|forgets|"
    r"forgot|is forgetting)\b")
_MED_THIRD_PERSON = re.compile(
    r"\b(he|she|they|him|her|them|his|their|mum|mother|mam|mom|dad|father|nan|nanna|gran|granny|"
    r"grandma|grandad|grandpa|wife|husband|partner|sister|brother|aunt|uncle|friend|son|"
    r"daughter)\b")
_MED_PATTERN = (
    "If they are forgetting other things too - names, the day, where the keys went - write down what "
    "they forget for a fortnight and take that to the GP, because a pattern that is new is worth "
    "checking rather than sorting out with a box.")
# A course of antibiotics has its own rule, and it is not the everyday one: taking the missed
# tablet when you remember is right unless the next is nearly due, and the course is finished.
_MED_ANTIBIOTIC = re.compile(r"\bantibiotics?\b|\bpenicillin\b|\bamoxicillin\b")
_MED_ANTIBIOTIC_ANSWER = (
    "Take the missed antibiotic as soon as you remember, unless the next dose is nearly due - then "
    "skip it and carry on as normal, and never take two at once. Finish the whole course even if "
    "you feel better, and if you were sick within a couple of hours of a dose ask a pharmacist "
    "whether it needs taking again.")
_MED_INSULIN = (
    "A missed insulin dose is one to ask about rather than guess: ring your diabetes team, the "
    "out-of-hours number or 111, test your blood sugar while you wait, and they will tell you how "
    "much to take. Do not take a make-up dose on top without advice, and get seen straight away if "
    "you are being sick or your blood sugar stays high.")
_MED_SUGAR_LINE = (
    "If someone with diabetes goes suddenly confused, sweaty or shaky that is usually a blood sugar "
    "rather than the tablets: sugar first, and 999 if they cannot swallow.")


_KEEP_ANY = re.compile(r"\b(for life|for good|forever|long term|long-term|rest of my life)\b")
_KEEP_LONG = re.compile(
    r"\b(blood pressure|statins?|cholesterol|thyroid|levothyroxine|heart tablets?|warfarin|"
    r"anti-?coagulant\w*|beta ?blocker\w*|ramipril|amlodipine|bisoprolol)\b")


def _keep_taking(memory, understood):
    """Should I stay on this medicine - the answer, not the pharmacist hand-off.

    Three shapes, because they are three different answers: a course with an end, a tablet taken to
    stay well, and the general "it is not suiting me, can I stop". All three open with the same
    sentence, because it is the one that matters: the decision is a pharmacist's or a GP's, and it
    is a review, not a stop.
    """
    clean = ((understood or {}).get("clean") or "").lower()
    if _MED_ANTIBIOTIC.search(clean) or "finish the course" in clean or "finish them" in clean:
        return ("Finish the course even if you feel better - a half-finished course is how "
                "infections come back and how resistance starts - and take the missed dose when "
                "you remember unless the next one is nearly due. If the side effects are why you "
                "want to stop, ring the pharmacist: there is usually another antibiotic that suits "
                "better, and they can swap it today.")
    if _KEEP_LONG.search(clean) or _KEEP_ANY.search(clean):
        return ("Keep taking it: tablets for blood pressure, cholesterol, the thyroid and the heart "
                "are for the long haul, and they work precisely because you do not feel them - so "
                "stopping when you feel well is when the risk comes back. If the dose or the side "
                "effects are a problem, ask for a review rather than stopping, and never stop one "
                "of these suddenly on your own. Ring the pharmacist or the surgery if you have "
                "already stopped.")
    return ("Keep taking it until a pharmacist, nurse or GP tells you to stop, and ask for a review "
            "rather than deciding on your own: tablets for the heart, blood pressure, thyroid, "
            "epilepsy, steroids and antidepressants can be dangerous to stop suddenly. If it is not "
            "suiting you, the fix is usually the dose, the brand or the time of day, so say what "
            "has changed and ask. If you have already stopped and feel unwell, ring the pharmacist "
            "today or 111.")


def _missed_medication(memory, understood):
    """The dose in front of you first, the routine second.

    "can i double up my tablets if i missed one" wants today's answer; "i keep forgetting to take my
    tablets" wants the system that stops it happening again. One paragraph answered the first with a
    Sunday pill organiser, which is the wrong sentence to open with.
    """
    clean = ((understood or {}).get("clean") or "").lower()
    if _MED_CONFUSED.search(clean):
        if _MED_TABLET_MUDDLE.search(clean) and not _MED_CONFUSED_NEW.search(clean):
            return _MED_BOX + (" " + _MED_PATTERN if _MED_THIRD_PERSON.search(clean) else "")
        return _MED_CONFUSED_ANSWER
    if _MED_RAN_OUT.search(clean):
        return _MED_RAN_OUT_ANSWER
    if _MED_CRITICAL.search(clean):
        return _MED_CRITICAL_ANSWER
    if _MED_REPEAT.search(clean) and _MED_MISSED.search(clean):
        return _MED_ROUTINE + (" " + _MED_SUGAR_LINE if _MED_SUGAR.search(clean) else "")
    if _MED_ANTIBIOTIC.search(clean):
        # after the routine branch, so "i keep forgetting my antibiotics" keeps the box, and
        # before the generic ones, because "finish the course" is the sentence that matters.
        return _MED_ANTIBIOTIC_ANSWER
    if _MED_MISSED.search(clean) and _MED_SUGAR.search(clean) and not _MED_REPEAT.search(clean):
        return _MED_INSULIN
    if _MED_TOO_MUCH.search(clean) and not _MED_MISSED.search(clean):
        return _MED_TOOK_TWO
    if _MED_MISSED.search(clean) and _MED_DOUBLE.search(clean):
        return _MED_DOUBLE_ANSWER + " " + _MED_BOX
    if _MED_MISSED.search(clean) and not _MED_REPEAT.search(clean):
        return ("Skip the missed dose and take the next one at its usual time, and do not take two "
                "to catch up. " + _MED_BOX)
    if _MED_THIRD.match(clean):
        # fond-radio: the blister pack is right for the tablets, and the memory answer's "write down
        # what they forget for a fortnight" is right for the person. A third-person line gets both,
        # so neither the tablet fix nor the "is this new?" question is lost.
        return _MED_BOX + " " + _MED_PATTERN
    if not _MED_REPEAT.search(clean):
        # "i take two tablets twice a day" is somebody stating their regimen: there is no question
        # here for this entry to answer, so it passes rather than handing out a pill organiser
        return ""
    reply = _MED_ROUTINE
    if _MED_SUGAR.search(clean):
        reply += " " + _MED_SUGAR_LINE
    return reply

_CAFFEINE_SYMPTOM = ("anxious", "anxiety", "jittery", "jitters", "shaky", "shaking",
                     "palpitations", "palpitation", "wired", "racing", "races", "pounding",
                     "flutter", "heart", "panic", "panicky")
_CAFFEINE_COUNT = re.compile(
    r"\b(\d{1,3})\b(?:\s+(?:of\s+)?)(cups?|mugs?|coffees?|teas?|cans?|espressos?)"
    r"\s*(?:(?:a|per|each|every)\s+(day|week))?")


def _caffeine_while_expecting(memory, understood):
    """200mg is the answer either way, but the first sentence has to name the right person."""
    clean = ((understood or {}).get("clean") or "").lower()
    figure = ("200mg of caffeine a day, about two mugs of coffee or four cups of tea: half the "
              "usual limit. It is also in cola, energy drinks, chocolate and some cold remedies, "
              "so those count too. Stay under the figure rather than at it")
    if any(word in clean for word in ("breastfeeding", "breast feeding", "nursing", "feeding")):
        return ("While you are breastfeeding the advice is the same as in pregnancy: " + figure +
                ". A coffee before a feed is fine, and the caffeine peaks in your milk an hour "
                "later, so the evening ones are the ones to make decaf.")
    return ("In pregnancy the advice is " + figure + ", and the same 200mg is what to keep to "
            "while you are trying or breastfeeding.")


_KIDS_LINE = ("Children under 12 are better off with no caffeine at all, and 12 to 18 should keep "
             "under about 100mg a day: a can of cola is around 35mg, a cup of tea about 50mg, a "
             "coffee 80mg or more. Energy drinks are the ones to refuse outright, since one can "
             "hold a teenager's whole day's worth and the sugar and taurine come with it.")

# "is coffee safe for a 12 year old" then "can she have tea too": the second line names no age
# and no child, so it matched the adult limit and answered a child's follow-up with 400mg. A child
# named a turn or two back is still who the conversation is about.
_KID_WORDS = ("child", "children", "kid", "kids", "son", "daughter", "toddler", "baby",
              "teenager", "teenagers", "boy", "girl", "school", "under 12", "under 5")
_PRONOUN_SUBJECT = re.compile(r"\b(she|he|they|him|her|them|his|hers)\b")


def _child_in_chat(memory):
    """Whether the last few user lines named someone under 18."""
    for turn in ((memory or {}).get("turns") or [])[-3:]:
        if not isinstance(turn, dict):
            continue
        text = " ".join(str(turn.get("user") or "").lower().split())
        if not text:
            continue
        if any(word in text.split() for word in _KID_WORDS) or "$" in text:
            return True
        if any(phrase in text for phrase in _TEEN_AGE_PHRASES) or "under 12" in text:
            return True
    return False


def _per_day(daily):
    """2 or 2.3, never 2.0: the rate a weekly count works out at, said the way a person says it."""
    whole = int(daily)
    if abs(daily - whole) < 0.05:
        return "%d" % whole
    return ("%.1f" % daily).rstrip("0").rstrip(".")


def _caffeine_limit(memory, understood):
    """The adult limit, unless the line says the coffee has already bitten.

    "coffee makes me anxious" is a symptom, not a sum: leading with the milligrams answers a
    question nobody asked, so a symptom line starts with cutting back and the limit comes after.
    A count is the other way round, but it has to be turned into a day first - sixteen coffees a
    week is a bit over two a day and well inside the limit, so the rate decides, not the number.
    """
    clean = ((understood or {}).get("clean") or "").lower()
    if any(word in clean for word in _CAFFEINE_SYMPTOM):
        return ("Those are the usual signs of too much caffeine: cut back to a cup or two in the "
                "morning and make the rest decaf, which keeps the habit without the jitters. Taper "
                "over a week rather than stopping dead, or the headaches will be worse than the "
                "shakes, and if your heart pounds for no reason, get it checked.")
    # a pronoun follow-up about a child ("can she have tea too") is still the child's question
    if (_child_in_chat(memory) and _PRONOUN_SUBJECT.search(clean)
            and not re.search(r"\bi\b", clean)
            and not re.search(r"\b\d+\b", clean) and not _CAFFEINE_COUNT.search(clean)):
        return _KIDS_LINE
    heaviest = None
    for found in _CAFFEINE_COUNT.finditer(clean):
        count, unit, period = int(found.group(1)), found.group(2), (found.group(3) or "day")
        daily = count / 7.0 if period == "week" else float(count)
        if heaviest is None or daily > heaviest[0]:
            heaviest = (daily, count, unit, period)
    if heaviest and heaviest[0] >= 5:
        _, count, unit, period = heaviest
        return ("%d %s a %s is well over the 400mg adult limit, which is about four instant coffees "
                "or two large filter ones; a cup of tea is around 50mg against 80mg or more in a "
                "coffee. Come down a cup every few days and make the later ones decaf, and the "
                "sleep and the jitters both settle." % (count, unit, period))
    # "is 200mg of caffeine a lot" carries its own number, so it is judged against the limit
    # rather than answered with the limit as if the number had not been said.
    milligram = re.search(r"\b(\d{2,4})\s*(?:mg|milligrams?)\b", clean)
    if milligram and any(word in clean for word in ("a lot", "lot", "ok", "okay", "alright",
                                                    "fine", "safe", "too much", "bad")):
        amount = int(milligram.group(1))
        if amount >= 400:
            return ("%dmg a day is at or over the 400mg adult limit - four instant coffees or two "
                    "large filter ones - so it is the point to come down from, a cup every few "
                    "days rather than all at once. Keep it under 200mg if you are pregnant, and if "
                    "it comes with a pounding heart or bad sleep, get that looked at." % amount)
        return ("%dmg is under the 400mg adult limit, which is about four instant coffees or two "
                "large filter ones, so on the caffeine count alone it is fine. It is still worth "
                "keeping the last one before early afternoon if sleep is a problem, and the limit "
                "halves to 200mg in pregnancy." % amount)
    if not any(word in clean for word in ("much", "too", "limit", "safe", "many", "a lot", "lot",
                                          "ok", "okay", "alright", "fine", "bad")):
        if heaviest:
            # "i drink 16 coffees a week" is a count, and a count inside the limit is worth
            # turning into a day and saying so: a shrug leaves the person no answer at all.
            _, count, unit, period = heaviest
            return ("%d %s a %s is about %s a day, which is inside the 400mg adult limit - that is "
                    "four instant coffees or two large filter ones. Keep the last one before early "
                    "afternoon if sleep is a problem, and stay under 200mg a day if you are "
                    "pregnant." % (count, unit, period, _per_day(heaviest[0])))
        return ""  # a plain mention of coffee is not this entry's to rule on
    return ("Around 400mg of caffeine a day is the usual safe limit for an adult, which is about "
            "four cups of instant coffee or two large filter coffees; pregnant women are advised to "
            "keep to 200mg. Stop by early afternoon if your sleep is affected, and cut down slowly "
            "over a week or two, since going cold turkey can bring headaches and irritability.")


# "how much tea is too much" was answered with the cool-it-and-freeze-it card, because in the
# leftovers row "tea" is the evening meal, and only "cups of tea" and "cup of tea" were held out
# of it. The limit row keys tea already, so the line has an answer waiting; the only thing it got
# wrong was the figure, which was the coffee one for a person asking about tea. A limit question
# names the drink, and the first sentence is the number for the cup in their hand.
_CAFFEINE_LEAD = {
    "tea": ("Around 400mg of caffeine a day is the usual safe limit for an adult, which is about "
            "six to eight mugs of ordinary tea at 50mg a mug - a strong one is nearer 70mg, so "
            "four or five of those"),
    "coffee": ("Around 400mg of caffeine a day is the usual safe limit for an adult, which is about "
               "four cups of instant coffee or two large filter coffees"),
    "energy": ("Around 400mg of caffeine a day is the usual safe limit for an adult, which is two "
               "or three 250ml energy drinks"),
    "cola": ("Around 400mg of caffeine a day is the usual safe limit for an adult, which is about "
             "eleven cans of cola at 35mg a can"),
    "herbal": ("Camomile, peppermint and fruit teas have no caffeine in them, so there is no daily "
               "limit to count against - the only thing to watch is how much sugar or honey goes "
               "in, and a herbal tea at night is the reason people drink it"),
}
_CAFFEINE_TAIL = ("; pregnant women are advised to keep to 200mg. Stop by early afternoon if your "
                  "sleep is affected, and cut down slowly over a week or two, since going cold "
                  "turkey can bring headaches and irritability.")
_CAFFEINE_DRINKS = (("herbal", ("herbal tea", "herbal teas", "camomile", "chamomile",
                                "peppermint tea", "fruit tea", "rooibos")),
                    ("tea", ("tea", "teas", "green tea", "builder's tea", "builders tea",
                             "cup of tea", "cups of tea", "mug of tea", "mugs of tea")),
                    ("coffee", ("coffee", "coffees", "espresso", "filter coffee",
                                "instant coffee", "latte", "cappuccino", "americano")),
                    ("energy", ("energy drink", "energy drinks", "monster", "red bull")),
                    ("cola", ("cola", "coke", "pepsi")))


_LIMIT_ASKS = frozenset((
    "much", "many", "too", "limit", "limits", "safe", "safely", "day", "days", "daily",
    "week", "weekly", "cups", "often", "amount", "maximum", "max",
    # "is a cup of tea bad for you" asks the same question without a count in it
    "bad", "good", "harmful", "healthy", "unhealthy", "ok", "okay", "fine", "worse",
    "risky", "risk"))
# "cup" is not on that list: "a cup of tea" says the drink, not a count, and the joke line above
# says one too.


def _the_limit_for_the_drink_named(memory, reading):
    """The adult caffeine limit, with the figure for the drink the line actually named.

    Tea is the one that needed it: "how much tea is too much" is the same question as "how much
    coffee is too much", and the person asking it wants to know how many mugs, not how many cups
    of coffee. A line that names two drinks, or none, keeps the coffee figure, which is what this
    row answered before.
    """
    clean = ((reading or {}).get("clean") or "").lower()
    # The limit is an answer to a question about how much or how often, so a line with no such
    # word in it is not this row's line: "he hit me with the news and a cup of tea" is a joke
    # that names a drink, and it was handed the 400mg figure (#8152, saf-s123). Asked properly,
    # the line says "much", "how many", "a day", "too much" - none of them missing.
    if not (set((reading or {}).get("words") or ()) & _LIMIT_ASKS):
        return None
    # Herbal first, because "herbal tea" carries the word tea as well: without this the person
    # asking about camomile was given the caffeine figure for ordinary tea.
    herbal = dict(_CAFFEINE_DRINKS)["herbal"]
    if any(phrase in clean for phrase in herbal):
        return _CAFFEINE_LEAD["herbal"] + "."
    found = [name for name, phrases in _CAFFEINE_DRINKS if name != "herbal"
             and any(phrase in clean for phrase in phrases)]
    if len(found) == 1 and found[0] in _CAFFEINE_LEAD:
        return _CAFFEINE_LEAD[found[0]] + _CAFFEINE_TAIL
    # A tea question that also mentions coffee is not one drink, and the coffee figure is the
    # one that holds both ("a cup of tea is around 50mg against 80mg or more in a coffee").
    if "tea" in found and "coffee" in found:
        return _CAFFEINE_LEAD["coffee"] + _CAFFEINE_TAIL
    return _CAFFEINE_LEAD["coffee"] + _CAFFEINE_TAIL


# "12" on its own is a number of cups, not an age: the bare ages turned "i have 12 cups of coffee
# a day" and "i drink 16 coffees a week" into a child's question. An age is how it is written, so
# the phrases are the key and the number alone is not.
_TEEN_AGES = ("12", "13", "14", "15", "16", "17", "18")
_TEEN_AGE_PHRASES = tuple(shape % age for age in _TEEN_AGES
                          for shape in ("i am %s", "im %s", "aged %s", "age %s",
                                        "%s year old", "%s years old"))
_COLD_PREVENT = ("prevent", "preventing", "prevention", "ward off", "avoid", "avoiding",
                # keeping colds away is the same prevention asked as a keeping
                "keep away", "keeping away", "colds away", "stay well", "keeping well",
                "not catch",
                "coming on", "in its tracks", "catch", "catching", "not get", "dodge",
                "before it",
                # "how do i stop a cold" is the same question as "can i stop one coming on", and
                # the honest half of the answer ("you cannot, once it has started") is the one it
                # was not getting.
                "stop a cold", "stop this cold", "stop the cold", "stop my cold", "stops a cold")
_COLD_HELP = ("For a cold, the things that genuinely help are rest, plenty of fluids, honey in "
              "warm water for a cough, and paracetamol or ibuprofen for aches and a sore throat; "
              "steam can ease a blocked nose. Vitamin C, zinc and echinacea have not held up in "
              "trials, nothing cures it, and it usually settles in about a week - see someone if "
              "it lasts longer or you are breathless.")
_COLD_STOP = ("You cannot stop a cold once it has started, and nothing you can buy shortens one "
              "by much: rest, fluids and sleep do more than any remedy. To catch fewer of them, "
              "wash your hands properly and often, use your own cup and towel, keep your sleep up "
              "and stay away from smoke, which is most of what the evidence supports.")


# A named remedy is asked about, not avoided: "does vitamin c stop a cold" wants to know about
# vitamin C, and the answer that names it is the help paragraph.
_COLD_NAMED = ("vitamin c", "vitamin", "zinc", "echinacea", "supplement", "tablets", "lemsip")


def _cold_help(memory, understood):
    """The cold entry's reply, with the stopping question answered honestly and the rest treated."""
    said = " ".join(str(value) for value in ((understood or {}).get(key)
                                             for key in ("clean", "norm_text", "norm"))
                    if isinstance(value, str)).lower()
    if any(word in said for word in _COLD_NAMED):
        return _COLD_HELP
    if any(word in said for word in _COLD_PREVENT):
        return _COLD_STOP
    return _COLD_HELP


# Three days or more is the point where a headache stops being an ordinary one and becomes one
# to have looked at. The line says the length in every way people write it - "for 10 days",
# "for 2 weeks", "a few days", "weeks now", "every single day", "all day" - so the length is
# read out of the words rather than matched as a fixed list of phrases, and the entry answers
# only when that reading is three days or more. Anything shorter goes to the ordinary headache
# answer, which is where "ive had a headache all day" belongs.
_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "ninety": 90,
    "a couple of": 2, "couple": 2, "few": 3, "a few": 3, "several": 4, "many": 5,
    "lots of": 5, "ages": 5, "half a": 0,
}
_UNIT_DAYS = {"day": 1, "days": 1, "week": 7, "weeks": 7, "weekend": 2, "fortnight": 14,
              "month": 30, "months": 30}
# A length with no number in front of it: "for days", "weeks now", "months". Plural means
# three or more of the unit to whoever wrote it.
_BARE_LENGTHS = ("days", "weeks", "months", "days now", "for days", "days on end",
                 "days running", "weeks now", "lasted days", "going on days")
# A headache that comes back every day is a daily headache whatever its length so far, and
# that is the pattern painkillers make worse. "every afternoon this week" is not this.
_EVERY_DAY = ("every day", "every single day", "each day", "every morning", "daily",
              "day after day", "every blessed day")


def _headache_days(words):
    """How many days the line says the headache has gone on, or None if it says no length."""
    said = " ".join(words)
    for phrase in _EVERY_DAY:
        if phrase in said:
            return 3
    best = None
    for at, word in enumerate(words):
        unit = _UNIT_DAYS.get(word)
        if unit is None:
            continue
        count = None
        for back in (1, 2, 3):
            if at - back < 0:
                break
            before = words[at - back]
            if before.isdigit():
                count = int(before)
                break
            if before in ("a", "an"):
                # "for a week", "for a month": one of the unit, which matters because a month
                # is thirty days and a week is seven.
                count = 1
                break
            if before in _NUMBER_WORDS:
                count = _NUMBER_WORDS[before]
                break
            if before not in ("a", "an", "of", "the", "this", "last", "past", "few"):
                break
        if count is None:
            # "all week", "all day", "the past week": a length said without a number.
            if word in ("week", "weeks") and any(one in said for one in
                                                 ("all week", "past week", "last week",
                                                  "over a week", "a week", "this past")):
                count = 7
            elif word in ("day", "days"):
                count = 1 if "all day" in said else None
        if count is None:
            continue
        days = count * unit
        best = days if best is None else max(best, days)
    if best is not None:
        # A number in the line decides, so "for two days" is two days and not the bare plural
        # "days" of _BARE_LENGTHS below.
        return best
    for phrase in _BARE_LENGTHS:
        if phrase in said:
            return 3
    return None


HEADACHE_DAYS = ("A headache that has gone on for three days or more is one to have looked at: "
                 "book a GP appointment in the next few days rather than keep taking painkillers, "
                 "which can themselves cause a daily headache if used more than two or three days "
                 "a week. Keep a short note of when it comes, what you have taken and how you "
                 "slept - it makes the appointment much more useful.")


def _headache_days_reply(memory, understood):
    """The GP line for a headache of three days or more, and nothing for a shorter one."""
    words = understood.get("words") or []
    days = _headache_days(words)
    if days is None or days < 3:
        return None
    return HEADACHE_DAYS


_HEADACHE_AFTERNOON = (
    "An afternoon headache is usually tension, a day of screens, too little water or food, or "
    "too much coffee, and paracetamol or ibuprofen with water and a quiet dark room settles "
    "most of them within a few hours. Get one checked the same day if it comes on like a "
    "thunderclap, comes with a fever and a stiff neck, follows a bang on the head, or is the "
    "worst you have ever had.")


def _headache_reply(memory, understood):
    """The ordinary-headache answer, or the no-tablet one when the line rules tablets out.

    "i cant take ibuprofen, what can i do for a headache" was told to take ibuprofen: the line
    has already said it cannot. The reading that splits "cant" into "can not" also walks past a
    one-word avoid entry, so the answer is chosen here rather than by the avoid list.
    """
    text = ((understood or {}).get("clean") or "").lower()
    if any(phrase in text for phrase in NO_DRUGS):
        return HEADACHE_NO_DRUGS
    return _HEADACHE_AFTERNOON
_HEAVY_PERIOD_WORDS = ("heavy", "heavier", "flooding", "flood", "clots", "clot", "soaking",
                       "soak", "soaked", "a lot", "lots", "seven days", "longer than usual")

# The other thing a period does in midlife: the cycle itself changes, and that is a question with
# an answer of its own rather than a nod. Before this "my periods have gone mad" was answered "I'm
# listening - say more if it helps" and "im 45 and my periods are irregular" with "Got it. Is there
# anything you'd like a hand with?" (@honey-pencil, #answers 70732). The words are the change, not
# the flow and not the pain, so they are read before the pain fallback and after the heavy one -
# a heavy period is the more urgent thing to say even when the cycle has also gone ragged.
_PERIOD_CHANGE_WORDS = ("irregular", "all over the place", "gone mad", "haywire", "skipping",
                        "skipped", "skipping a month", "closer together", "further apart",
                        "every two weeks", "every three weeks", "random", "randomly",
                        "not regular", "unpredictable", "stopped", "stopping", "no period")
PERIOD_CHANGE_REPLY = (
    "Periods that change - closer together, further apart, lighter, or skipped altogether - are "
    "usually perimenopause if you are over 40, and it can go on for years. Check a pregnancy test "
    "first if there is any chance. Keep using contraception until you have gone a full 12 months "
    "with no period, because you can still conceive. Over 40, see a GP about bleeding between "
    "periods, after sex, or a heavy bleed after a year with none; HRT or the pill can settle the "
    "cycle. Under 40, a period that stops needs a GP anyway - thyroid, PCOS and weight loss are "
    "the usual causes.")
# A named cause is its own question, and a partner's or a mother's period is not this person's.
NOT_THIS_PERSONS_PERIOD = ("pcos", "pcod", "polycystic", "endometriosis", "thyroid", "coil",
                           "implant", "my wife", "my mum", "my mother", "my nan", "my sister",
                           "my friend", "my daughter", "she is", "she has", "her periods")


def _period_answer(memory, understood):
    """The heavy-period answer when the line is about how much, not how much it hurts.

    Both are the same subject, so both live in one entry: a second entry on "period" would have
    halved the word's rarity for both and dropped "why is my period late" under the bar.
    """
    words = set(understood.get("words") or ())
    clean = " " + (understood.get("clean") or "").lower() + " "
    if any(word in words or " " + word + " " in clean for word in NOT_THIS_PERSONS_PERIOD):
        return None
    if (not any(word in words or " " + word + " " in clean for word in _HEAVY_PERIOD_WORDS)
            and any(word in words or " " + word + " " in clean
                    for word in _PERIOD_CHANGE_WORDS)):
        return PERIOD_CHANGE_REPLY
    if not any(word in words or " " + word + " " in clean for word in _HEAVY_PERIOD_WORDS):
        return ("Period pain that is bad enough to stop your day is worth taking seriously: "
                "ibuprofen works better than paracetamol for it, started a day before, and heat "
                "on your lower tummy helps. Pain that is getting worse month by month, or that "
                "has started later in life, is the pattern to describe to a GP - it can be "
                "endometriosis, which takes years to get diagnosed if nobody is told.")
    return ("Heavy periods are common and treatable: soaking a pad or tampon every hour, clots "
            "bigger than a 10p coin, or bleeding past seven days are the things to describe to a "
            "GP, who can check for fibroids, thyroid trouble or a copper coil and offer tablets, "
            "the pill or a coil that thins the lining. Eat iron - red meat, beans, fortified "
            "cereal - and go the same day if you are flooding or feel faint.")



# The remedies above are for a person who can hold their breath and sip water. A baby cannot, and
# a parent asking about hiccups is asking whether it is normal, not for a paper bag.
HICCUPS_BABY = (
    "Hiccups in a baby or a small child are normal and they do not bother them: feed a little more "
    "upright, burp them, and the hiccups stop on their own within a few minutes. Mention it to a "
    "health visitor or GP if they come with reflux, coughing or trouble feeding.")

# A parent who says it again has not read the reassurance, or does not believe it, so the second
# answer is a different one that says the same thing from the other end - that hiccups coming back
# are still normal - instead of the same paragraph in a "Same as before:" frame. It keeps the
# carer-reading of a baby's symptom away from an ordinary bout of hiccups, which is not a change to
# report to a doctor.
HICCUPS_BABY_AGAIN = (
    "Hiccups coming back in a baby are still normal: a feed, a burp or a gulp of air sets them off, "
    "and they need no treatment. If they seem to bother them, stop and wind them partway through a "
    "feed, and keep them upright for a while after. Only reflux, coughing or trouble feeding is "
    "worth a call to the health visitor.")

_BABY_WORDS = ("baby", "babies", "newborn", "newborns", "infant", "infants", "toddler",
               "toddlers", "my son", "my daughter", "my child", "breastfeeding", "bottle feeding")


def _said_before(memory, opening):
    """Whether the bot has already said an answer that starts like this."""
    for turn in (memory or {}).get("turns") or ():
        if isinstance(turn, dict) and str(turn.get("bot") or "").startswith(opening):
            return True
    return False


def _hiccups_remedy(memory, understood):
    """The remedy for a grown-up, and the reassurance a parent is asking for."""
    words = set((understood or {}).get("words") or ())
    if words & set(_BABY_WORDS):
        if _said_before(memory, HICCUPS_BABY[:24]) or _said_before(memory, HICCUPS_BABY_AGAIN[:24]):
            return HICCUPS_BABY_AGAIN
        return HICCUPS_BABY
    return ("Sip cold water slowly, hold your breath for a few seconds, swallow a few times or "
            "breathe into a paper bag, and one of those stops most hiccups within a couple of "
            "minutes. They start when a big meal, a fizzy drink or a laugh pushes the stomach up "
            "against the diaphragm, which is why they pass on their own. A GP can help if they "
            "last more than two days, or come with pain or trouble swallowing.")



STEPS_PISA = "The Leaning Tower of Pisa is 296 steps to the top."
STEPS_EMPIRE = "The Empire State Building is 1,860 steps to the 102nd-floor observatory."
STEPS_PAULS = "St Paul's dome is 528 steps."
STEPS_FLIGHT = ("A single flight between house floors is 12 to 13 steps, and a whole staircase "
                "up to an upstairs flat is usually 14 to 16.")
STEPS_TAIL = "A cathedral or a stadium prints its own count at the entrance."


def _steps_up_a_building(memory, understood):
    """The count for the place the line names, then the others.

    "How many steps in a flight of stairs" was answered with Pisa first, so the one number the
    person could use came after two towers they had not asked about; a flight, a floor and a
    tower each lead now.
    """
    said = str((understood or {}).get("clean") or "").lower()
    # A named place beats the word "stairs": "how many stairs in the empire state building" carries
    # "stairs" too, and answering it with a house staircase is the same fault as answering a tower
    # with the daily target - confidently about something else. So the landmarks come first and
    # the staircase is the fallback.
    if "pisa" in said or "leaning tower" in said:
        lead, rest = STEPS_PISA, [STEPS_EMPIRE, STEPS_PAULS, STEPS_FLIGHT]
    elif "empire" in said:
        lead, rest = STEPS_EMPIRE, [STEPS_PISA, STEPS_PAULS, STEPS_FLIGHT]
    elif "paul" in said or "dome" in said or "cathedral" in said:
        lead, rest = STEPS_PAULS, [STEPS_PISA, STEPS_EMPIRE, STEPS_FLIGHT]
    elif any(word in said for word in ("flight", "floor", "storey", "story", "riser",
                                       "stair")):
        lead, rest = STEPS_FLIGHT, [STEPS_PISA, STEPS_EMPIRE, STEPS_PAULS]
    else:
        lead, rest = STEPS_PISA, [STEPS_EMPIRE, STEPS_PAULS, STEPS_FLIGHT]
    return " ".join([lead] + rest + [STEPS_TAIL])


STEPS_A_MILE = (
    "About 2,000 steps to a mile, so 10,000 steps is roughly five miles, a 5k is about "
    "6,500 steps and a marathon is around 55,000. Stride length moves that by around a "
    "tenth either way - a tall walker covers a mile in fewer - so use it for a pedometer "
    "target rather than a measurement.")

# A count in a line that says how the day went is a report, and what the person wants back is
# their own number in miles, not a paragraph on stride length. "walked 12000 steps" and "12000
# steps today" put no "i" in front of the verb, so no avoid phrase catches every shape of it;
# the words are read here instead, and a line with none of them is still the question.
STEPS_REPORT_WORDS = ("today", "so far", "yesterday", "already", "just", "did", "done",
                      "walked", "walking", "managed", "clocked", "hit", "reached", "notched",
                      "this morning", "this afternoon", "by lunchtime", "before work")
STEPS_COUNT = re.compile(r"\b(\d{1,3},\d{3}|\d{4,5})\b")


def _steps_in_a_distance(memory, understood):
    """The conversion, said as the question it is or as the report it is.

    "walked 12000 steps" is somebody telling you about their day, and the paragraph on stride
    length answers a question they did not ask; the same numbers said back in miles is what a
    friend says. Nothing here decides whether the row answers - the key and the avoid list do -
    so this only picks the wording once it does.
    """
    said = str((understood or {}).get("clean") or "").lower()
    found = STEPS_COUNT.search(said)
    if found and any(word in said for word in STEPS_REPORT_WORDS):
        count = int(found.group(1).replace(",", ""))
        if 1000 <= count <= 100000:
            miles = round(count / 2000.0, 1)
            if float(miles).is_integer():
                miles = int(miles)
            return ("That's about {} miles - {:,} steps at roughly 2,000 to a mile. A 5k is "
                    "about 6,500 steps and a marathon around 55,000, so that is a proper "
                    "walk.").format(miles, count)
    return STEPS_A_MILE
# What people name when they say what sets their heartburn off. "tomatoes give me heartburn",
# "spicy food gives me heartburn" and "curry gives me heartburn" name the subject once and ask
# nothing, so they had no ask word in them and got "Got it. Is there anything you'd like a hand
# with?" while "what can i take for heartburn" was answered in full. Naming the food IS the
# question: it is the one thing the person wants to know about. Each label is a sentence opener,
# so the reply names the food back to them before the advice that is the same for all of them.
# The shape a trigger is reported in, and the words that are never the food: "i get heartburn from
# baked beans" has the beans after "from", "baked beans gives me heartburn" has them before
# "gives me". A food nobody wrote into the list above is still the thing the person wants an
# answer about, so the words either side of the report are read off the line and named back.
_A_FOOD_WORD = r"[a-z][a-z'-]*(?: [a-z][a-z'-]*){0,2}"
_HEARTBURN_REPORT_BEFORE = re.compile(
    r"\b(" + _A_FOOD_WORD + r")\s+(?:gives? me|gives|give|sets? off|brings? on|"
    r"triggers?|triggered|does? it to me|do it)\b")
_HEARTBURN_REPORT_AFTER = re.compile(
    r"\b(?:heartburn|acid reflux|reflux|indigestion)\s*,?\s*(?:from|with|off)\s+"
    r"(" + _A_FOOD_WORD + r")")
_HEARTBURN_NOT_A_FOOD = frozenset((
    "i", "me", "it", "this", "that", "them", "they", "we", "you", "he", "she", "my", "the",
    "a", "an", "always", "sometimes", "often", "really", "badly", "awful", "terrible", "food",
    "eating", "everything", "anything", "something", "nothing", "things", "thing", "life",
    "and", "but", "so", "just", "too", "again", "still", "every", "time", "day", "night",
    "loads", "lots", "as", "well", "too much", "a lot", "all the time", "every time",
    # a time is not a food: "heartburn after dinner" names when, not what
    "after", "before", "dinner", "lunch", "breakfast", "tea", "supper", "meal", "meals",
    "late", "early", "lately", "recently",
    "a meal", "bed", "going to bed", "lying down", "drinking", "drink",
    # the report verb itself, when the capture runs on into it
    "get", "gets", "got", "give", "gives", "gave", "set", "sets", "bring", "brings",
    "trigger", "triggers", "does", "do", "take", "takes", "ate", "eat", "eaten", "drank",
    # not food, however the sentence is shaped: "stress gives me heartburn" and "pregnancy gives
    # me heartburn" are not things to "cut out for a fortnight", and naming one back would be
    # worse than saying nothing about it
    "stress", "worry", "worrying", "anxiety", "anxious", "being anxious", "work", "life",
    "tiredness", "being tired", "lack of sleep", "no sleep", "my weight", "weight", "being fat",
    "being overweight", "overweight", "age", "getting older", "hormones", "period", "my period",
    "periods", "the pill",
    # the line is read as its clean form and its normalised form joined together, so a capture can
    # run across the join and name the symptom back: "heartburn from not eating" blames
    # "not heartburn" and the card says "Cut not heartburn out for a fortnight".
    "heartburn", "heartburns", "reflux", "indigestion", "acid", "burning",
    # the ask itself: "what foods trigger heartburn" names no food, it asks for the list
    "what", "which", "why", "food", "foods", "list", "diet", "avoid", "should", "can"))


def _heartburn_blames(said):
    """The food the line blames, said back in its own words, or "" when it names none."""
    for pattern in (_HEARTBURN_REPORT_BEFORE, _HEARTBURN_REPORT_AFTER):
        found = pattern.search(said or "")
        if not found:
            continue
        words = [w for w in found.group(1).split()
                 if w.strip("'") and w not in _HEARTBURN_NOT_A_FOOD]
        if not words:
            continue
        phrase = " ".join(words[-3:])
        # The words before the verb are often grammar, not a food: "is it ok to give water"
        # reaches this card through "give" and blames "ok to", and "Cut ok to out for a
        # fortnight" is a broken sentence in the middle of an answer. When nothing in the
        # phrase names a thing, the card says the plain answer instead.
        return phrase if names_a_thing(phrase) else ""
    return ""


_HEARTBURN_ANSWER = (
    "An antacid or an alginate (Gaviscon and the like) settles most heartburn within minutes, and "
    "a pharmacy tablet such as omeprazole, taken daily for a fortnight, works better if it keeps "
    "coming back. Eat smaller meals, leave three hours between dinner and bed, and raise the head "
    "of the bed 10 to 15cm. See a GP if it lasts more than three weeks or you find food sticking "
    "on the way down.")
_HEARTBURN_BLAMED = (
    "Cut {} out for a fortnight and see if the heartburn eases; an antacid or an alginate (Gaviscon "
    "and the like) settles a bad night in minutes. Tomato, chilli, onion and garlic, citrus, fried "
    "food, chocolate, mint, coffee and alcohol are the other usual triggers, so smaller meals, three "
    "hours between dinner and bed and the head of the bed 10 to 15cm up do the rest. See a GP if it "
    "lasts more than three weeks.")
# The heartburn that comes with a pregnancy is not a food at all, and "cut it out for a fortnight"
# is no kind of advice for it: a woman told that learns the bot is not reading her. It is common,
# it eases once the baby is born, and the treatment is different only in what to ask first.
_HEARTBURN_PREGNANT = (
    "Heartburn is very common in pregnancy and eases once the baby is born: the hormones relax the "
    "valve at the top of the stomach, and later the baby takes the room. Eat little and often, stay "
    "upright an hour after eating, prop the head of the bed up 10 to 15cm, and try an antacid or an "
    "alginate (Gaviscon and the like) - ask a pharmacist or your midwife before omeprazole. Tell your "
    "midwife if it stops you eating or sleeping.")
# A painkiller is the other thing people name, and the answer is a different one: swap the tablet,
# do not cut out a food.
_HEARTBURN_PILLS = (
    "Some painkillers set heartburn off - ibuprofen, aspirin and naproxen are the usual three, "
    "because they irritate the stomach lining. Do not just stop a tablet you were prescribed: ask a "
    "pharmacist or your GP whether paracetamol would do instead, and take any of them with food. An "
    "antacid or an alginate settles a bad night in the meantime, and see a GP if it lasts more than "
    "three weeks.")
# "What can I eat with heartburn" is not the list of things to avoid: it wants the plate. The
# avoid list is still in it, but after the food that is fine.
_HEARTBURN_EAT = (
    "Plain, dry food sits easiest: porridge, rice, bread, bananas, melon, ginger, plain chicken or "
    "fish, and a glass of milk - little and often beats one big meal, and nothing within three hours "
    "of bed. Go steady on tomato, chilli, onion and garlic, citrus, fried and fatty food, chocolate, "
    "mint, coffee and alcohol, since those are the usual triggers. An antacid or an alginate "
    "(Gaviscon and the like) settles a bad night in minutes.")
_HEARTBURN_EAT_WORDS = ("what can i eat", "what should i eat", "what to eat", "what can i have",
                        "what should i have", "foods i can eat", "food i can eat", "safe to eat")
_HEARTBURN_PREGNANT_WORDS = ("pregnant", "pregnancy", "expecting a baby", "having a baby",
                             "with child")
# Only a *named* painkiller reaches the swap paragraph: "my heartburn tablets arent working" is a
# heartburn treatment that is not working, and answering it with "ibuprofen sets heartburn off" was
# a confidently wrong answer to a different question.
_HEARTBURN_PILL_WORDS = ("ibuprofen", "aspirin", "naproxen", "voltarol", "nurofen", "painkiller",
                         "painkillers", "pain killer", "pain killers", "anti inflammatories",
                         "anti-inflammatory")
# Tablets for the heartburn itself, and the tablets not working: a different answer again.
_HEARTBURN_TABLETS_NOT_WORKING = (
    "If the antacid is not holding it, a pharmacist can suggest a 14-day course of a PPI - "
    "omeprazole, esomeprazole or lansoprazole, one a day before breakfast - which is what GPs "
    "prescribe first for regular heartburn. Keep off the usual triggers meanwhile and stay upright "
    "for three hours after eating. See a GP if it has gone on three weeks, if you are over 55 and "
    "it is new, or if swallowing is getting hard.")
# The tablets people take *for* the heartburn are a treatment question; a bare "tablets" is the
# "is it my tablets that cause it" question. Two answers, so two lists.
_HEARTBURN_TREATMENT_WORDS = ("gaviscon", "antacid", "antacids", "ranitidine", "omeprazole",
                              "lansoprazole", "esomeprazole", "ppi", "ppis", "alginate")
_HEARTBURN_TABLETS_WORDS = ("tablets", "tablet", "pills", "pill", "medication", "medicine")
_HEARTBURN_NOT_WORKING_WORDS = ("not working", "arent working", "arent helping", "not helping",
                                "doesnt work", "doesnt help", "no good", "stopped working",
                                "isnt working", "not doing anything")
# A plain cup of tea is not coffee: it is a real but quieter trigger, and telling a tea drinker
# about caffeine and espresso read as a neighbour's answer.
_HEARTBURN_TEA = (
    "Tea is not one of the usual ones - coffee, alcohol, mint and fizzy drinks are the drinks that "
    "matter most - but tea has caffeine in it too, so a strong cup can loosen the valve the same way "
    "coffee does. If tea is the one thing you always have before it starts, a fortnight without it "
    "will tell you. An antacid or an alginate (Gaviscon and the like) settles a bad night in "
    "minutes.")
_HEARTBURN_TRIGGERS = (
    (("tomato", "tomatoes", "tomato sauce", "passata", "ketchup", "bolognese", "pasta sauce"),
     "Tomato, and anything made with it, is one of the usual triggers, along with chilli, onion, "
     "garlic, citrus, chocolate and alcohol: they loosen the valve at the top of the stomach, so "
     "acid travels back up. Cut back on it for a fortnight and the heartburn usually eases, and "
     "an antacid or an alginate (Gaviscon and the like) settles a bad night within minutes. "
     "See a GP if it lasts more than three weeks."),
    (("spicy", "spice", "spices", "curry", "curries", "chilli", "chilli sauce", "chili", "hot sauce",
      "hot food", "jalapeno", "jalapenos", "vindaloo", "tikka", "naga"),
     "Chilli and curry are the usual triggers, along with onion, garlic, citrus, chocolate and "
     "alcohol: they loosen the valve at the top of the stomach, so acid travels back up. A plain "
     "rice or bread with it soaks some of it up, and an antacid or an alginate (Gaviscon and the "
     "like) settles a bad night within minutes. See a GP if it lasts more than three weeks."),
    (("citrus", "orange", "oranges", "orange juice", "lemon", "lemons", "grapefruit", "lime",
      "satsuma", "clementine"),
     "Citrus is one of the usual triggers, along with tomato, chilli, onion, garlic, chocolate and "
     "alcohol: they loosen the valve at the top of the stomach, so acid travels back up. Cut back "
     "on it for a fortnight and the heartburn usually eases, and an antacid or an alginate "
     "(Gaviscon and the like) settles a bad night within minutes. See a GP if it lasts more than "
     "three weeks."),
    (("onion", "onions", "garlic", "shallot", "shallots", "leek", "leeks"),
     "Onion and garlic are two of the usual triggers, along with tomato, chilli, citrus, chocolate "
     "and alcohol: they loosen the valve at the top of the stomach, so acid travels back up. "
     "Cooking them well softens the effect for a lot of people, and an antacid or an alginate "
     "(Gaviscon and the like) settles a bad night within minutes. See a GP if it lasts more than "
     "three weeks."),
    (("fried", "frying", "fatty", "greasy", "chips", "batter", "pizza", "cheese", "cream",
      "takeaway"),
     "Fried and fatty food is one of the usual triggers, along with tomato, chilli, onion, garlic, "
     "citrus and alcohol: fat slows the stomach down, so the acid has longer to travel back up. "
     "Grilling rather than frying helps, and an antacid or an alginate (Gaviscon and the like) "
     "settles a bad night within minutes. See a GP if it lasts more than three weeks."),
    (("mint", "mint tea", "peppermint", "peppermint tea", "spearmint", "after dinner mint",
      "polos"),
     "Mint is a quiet trigger: it relaxes the valve at the top of the stomach, so the peppermint "
     "tea people drink for a bad stomach can make heartburn worse. Swap it for camomile or ginger, "
     "and an antacid or an alginate (Gaviscon and the like) settles a bad night within minutes. "
     "See a GP if it lasts more than three weeks."),
    (("coffee", "espresso", "latte", "cappuccino", "caffeine", "cola", "energy drink"),
     "Coffee is one of the usual triggers, along with alcohol, tomato, chilli, onion, citrus and "
     "chocolate: caffeine loosens the valve at the top of the stomach, so acid travels back up. "
     "Two cups a day is usually fine and four is usually not, and an antacid or an alginate "
     "(Gaviscon and the like) settles a bad night within minutes. See a GP if it lasts more than "
     "three weeks."),
    (("wine", "beer", "lager", "alcohol", "vodka", "gin", "cider", "prosecco", "whisky",
      "whiskey", "brandy", "cocktail", "cocktails"),
     "Alcohol is one of the usual triggers, along with tomato, chilli, onion, garlic, citrus and "
     "chocolate: it loosens the valve at the top of the stomach, so acid travels back up. Drinking "
     "earlier in the evening and less of it is what helps most, and an antacid or an alginate "
     "(Gaviscon and the like) settles a bad night within minutes. See a GP if it lasts more than "
     "three weeks."),
    (("chocolate",),
     "Chocolate is one of the usual triggers, along with alcohol, tomato, chilli, onion, citrus "
     "and coffee: it loosens the valve at the top of the stomach, so acid travels back up. Keeping "
     "it to the afternoon rather than the evening helps, and an antacid or an alginate (Gaviscon "
     "and the like) settles a bad night within minutes. See a GP if it lasts more than three "
     "weeks."),
)
# The words that reach this entry when they are what the line names, so a food trigger is an ask.
_HEARTBURN_ASKS = tuple(word for words, _label in _HEARTBURN_TRIGGERS for word in words)


# A line that asks which foods do it names no food of its own: "what foods trigger acid reflux"
# got the treatment answer, which never says what to cut back on.
# "why do i get heartburn" is the mechanism question, and it had no answer at all: the treatment
# paragraph says what to do without saying what is happening.
_HEARTBURN_WHY = (
    "A ring of muscle where the food pipe meets the stomach keeps the acid down, and heartburn is "
    "that ring relaxing at the wrong moment so acid travels back up and burns. Big or late meals, "
    "fatty and spicy food, alcohol, coffee, chocolate, mint and extra weight all loosen it. Eating "
    "smaller and earlier, and raising the head of the bed 10 to 15cm, is what settles it; an "
    "antacid or an alginate (Gaviscon and the like) covers a bad night in minutes.")
_HEARTBURN_WHICH = (
    "Tomato and tomato sauces, chilli and curry, onion and garlic, citrus, fried and fatty food, "
    "chocolate, mint, coffee and alcohol are the usual ones, and which of them matter is personal. "
    "Write down what you ate on the bad nights for a fortnight and two or three will stand out; cut "
    "those back and it usually eases, with an antacid or an alginate (Gaviscon and the like) settling "
    "a bad night in minutes.")


def _heartburn(memory, understood):
    """The heartburn entry's reply: name the food the line blames, then the advice that is the same."""
    said = " ".join(str(value) for value in ((understood or {}).get(key)
                                             for key in ("clean", "norm_text", "norm"))
                    if isinstance(value, str)).lower()
    if _any_hit([r"\b" + re.escape(word) + r"\b" for word in _HEARTBURN_PREGNANT_WORDS], said):
        return _HEARTBURN_PREGNANT
    if (_any_hit([re.escape(word) for word in _HEARTBURN_NOT_WORKING_WORDS], said)
            and _any_hit([r"\b" + re.escape(word) + r"\b"
                          for word in _HEARTBURN_TABLETS_WORDS + _HEARTBURN_TREATMENT_WORDS], said)):
        return _HEARTBURN_TABLETS_NOT_WORKING
    if _any_hit([r"\b" + re.escape(word) + r"\b" for word in _HEARTBURN_PILL_WORDS], said):
        return _HEARTBURN_PILLS
    # "do my tablets give me heartburn" is the same question family: a named drug or just "tablets"
    if _any_hit([r"\b" + re.escape(word) + r"\b" for word in _HEARTBURN_TABLETS_WORDS], said):
        return _HEARTBURN_PILLS
    # a heartburn remedy in the line is the treatment question, whichever way it is asked
    if _any_hit([r"\b" + re.escape(word) + r"\b" for word in _HEARTBURN_TREATMENT_WORDS], said):
        return _HEARTBURN_ANSWER
    if (re.search(r"\btea\b", said) and not re.search(r"\b(mint|peppermint|spearmint) tea\b",
                                                       said)):
        return _HEARTBURN_TEA
    for words, label in _HEARTBURN_TRIGGERS:
        if _any_hit([r"\b" + re.escape(word) + r"\b" for word in words], said):
            return label
    if _any_hit([re.escape(word) for word in _HEARTBURN_EAT_WORDS], said):
        return _HEARTBURN_EAT
    # A food actually named in the line beats the ask: "prawns trigger my heartburn" is a report,
    # not a request for the list, and the word "trigger" alone would have sent it to the list.
    blamed = _heartburn_blames(said)
    if _any_hit([r"\b" + re.escape(word) + r"\b"
                 for word in ("which", "what foods", "what food", "food", "foods", "diet",
                              "trigger", "triggers", "causes", "cause", "avoid", "cut out",
                              "what should", "list", "what can i eat")],
                said) and not blamed:
        return _HEARTBURN_WHICH
    if _any_hit([r"\bwhy\b", r"\bwhat causes\b"], said):
        return _HEARTBURN_WHY
    if blamed:
        return _HEARTBURN_BLAMED.format(blamed)
    return _HEARTBURN_ANSWER


def _freezing_point(memory, understood):
    """The freezing point, or why ice slips, told from the side the line asked.

    "Why is ice slippery" is the same fact seen from the other side: the first sentence has
    to be the thin film under the skate, not the temperature, or the card answers a question
    nobody asked. Both readings keep the number, because people want it either way.
    """
    line = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if re.search(r"slippery|slippy|slips? |slip on|skate|skating|glide", line):
        return ("Ice is slippery because a skate or a boot melts a thin film of water under "
                "it, so you are sliding on water rather than on ice, and the film keeps "
                "refreezing as you go over it. Water freezes at 0C (32F); salt lowers that, "
                "which is why roads are gritted.")
    return WATER_FREEZES


WATER_FREEZES = ("Water freezes at 0C (32F). Salt lowers that, which is why roads are "
                 "gritted, and pressure lowers it too, which is why ice skates glide on a "
                 "thin film of water.")
# A step count is asked about in two other currencies, and both were getting the daily target:
# "how many calories in 10000 steps" and "how many steps in an hour of walking". Neither is a
# habit - one is the energy in a count, the other is the steps a length of walking gets you - so
# the number the line names is the one the sum uses, the same way the mile row reads its distance.
# "calorie" and "kcal" only: "burn" on its own is in a kitchen question too ("why does spicy food
# burn"), and a word that another answer's line already carries makes that answer's key worth less.
CALORIE_WORDS = ("calorie", "calories", "kcal", "energy")
TIME_WORDS = ("an hour", "hour", "hours", "minutes", "minute", "mins", "half an hour", "hr",
              "hrs")
STEPS_PER_MILE = 2000.0
STEPS_PER_KM = 1250.0


def _step_count_said(said, default=10000):
    """The step count a line names, or the round figure people mean when they name none."""
    found = STEPS_COUNT.search(said)
    if found:
        count = int(found.group(1).replace(",", ""))
        if 200 <= count <= 100000:
            return float(count)
    return float(default)


def _steps_from_a_distance(said):
    """The steps in the distance a line names, on the same 2,000-to-a-mile figure as above."""
    for word, steps in (("mile", STEPS_PER_MILE), ("miles", STEPS_PER_MILE),
                        ("km", STEPS_PER_KM), ("kms", STEPS_PER_KM),
                        ("kilometre", STEPS_PER_KM), ("kilometres", STEPS_PER_KM),
                        ("kilometer", STEPS_PER_KM), ("kilometers", STEPS_PER_KM)):
        if re.search(r"\b" + word + r"\b", said):
            count = re.search(r"(\d+(?:\.\d+)?)\s*" + word + r"\b", said)
            many = float(count.group(1)) if count else 1.0
            return many * steps
    return None


def _steps_from_a_time(said):
    """The steps in the length of walking a line names, on the 6,250-to-an-hour figure.

    A calorie question can say its length instead of its count ("how many calories does an hour
    of walking burn"), and then there is no count in the line to convert: the hour is the count.
    """
    minutes = None
    found = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\b", said)
    if found:
        minutes = float(found.group(1)) * 60.0
    elif re.search(r"\b(?:an|one|a single)\s+hour\b", said):
        minutes = 60.0
    elif re.search(r"\bhalf an hour\b", said):
        minutes = 30.0
    else:
        found = re.search(r"\b(\d+)\s*(?:minutes|minute|mins|min)\b", said)
        if found:
            minutes = float(found.group(1))
    return 6250.0 * minutes / 60.0 if minutes else None


def _steps_calories(memory, understood):
    """What a step count burns: about 0.04 to 0.05 of a calorie a step for most adults."""
    said = str((understood or {}).get("clean") or "").lower()
    steps = _steps_from_a_distance(said)
    if steps is None:
        steps = _steps_from_a_time(said)
    if steps is None:
        steps = _step_count_said(said)
    low = int(round(steps * 0.04 / 10.0)) * 10
    high = int(round(steps * 0.05 / 10.0)) * 10
    return ("About {:,} to {:,} calories in {} steps - roughly 0.04 to 0.05 of a calorie a "
            "step, which is the figure for an average adult. It climbs with your weight and "
            "your pace, and it is a small number next to what a snack costs: a biscuit is often "
            "a whole mile's worth, so the walking is for the habit and the heart as much as the "
            "calories.").format(low, high, _said_steps(steps))


def _duration_phrase(minutes):
    """"an hour", "half an hour", "2 hours", "45 minutes": the length as a person says it."""
    if abs(minutes - 60) < 0.5:
        return "an hour"
    if abs(minutes - 30) < 0.5:
        return "half an hour"
    if abs(minutes % 60) < 0.5:
        hours = int(minutes // 60)
        return "%d hour%s" % (hours, "" if hours == 1 else "s")
    return "%d minutes" % int(round(minutes))


def _round_steps(value):
    for step in (1000, 500, 250, 50):
        if value >= step * 4:
            return int(round(value / step) * step)
    return int(round(value))


def _said_steps(value):
    return "{:,}".format(_round_steps(value))


def _steps_in_a_time(memory, understood):
    """How many steps a length of walking gets you: 1,250 steps a kilometre at about 5km/h."""
    said = str((understood or {}).get("clean") or "").lower()
    minutes = None
    found = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\b", said)
    if found:
        minutes = float(found.group(1)) * 60.0
    elif re.search(r"\bhalf an hour\b", said):
        minutes = 30.0
    else:
        found = re.search(r"\b(\d+)\s*(?:minutes|minute|mins|min)\b", said)
        if found:
            minutes = float(found.group(1))
    brisk = bool(re.search(r"\b(brisk|fast|quick|power|uphill|hilly)\b", said))
    ordinary = 6250.0 * (minutes if minutes else 60.0) / 60.0
    quick = 7500.0 * (minutes if minutes else 60.0) / 60.0
    if minutes:
        return ("About %s steps in %s of walking at an ordinary pace, or %s if you are walking "
                "briskly - that is 1,250 steps a kilometre at about 5km/h. Hills, a slow stroll "
                "and short legs all move it."
                % (_said_steps(ordinary), _duration_phrase(minutes), _said_steps(quick)))
    if brisk:
        return ("About %s steps in an hour of brisk walking - 6.5km/h or so, which is 1,250 steps "
                "a kilometre over six and a half of them. An ordinary-paced hour is about %s, and "
                "a slow wander round the shops is well under that."
                % (_said_steps(7500.0), _said_steps(6250.0)))
    return ("About %s to %s steps in an hour of walking: an ordinary pace is about 5km/h, which "
            "is 1,250 steps a kilometre, so an hour gets you five of them. A brisk walk nearer "
            "6.5km/h is the top of that range, and a slow wander round shops is well under it."
            % (_said_steps(6250.0), _said_steps(7500.0)))


BLANK_WORDS = ("what i was saying", "what i was about to say", "what i was going to say",
               "what i wanted to say", "lose my words", "train of thought", "mid sentence",
               "mid-sentence",
               "the word i", "word", "words")


def _forgetting(memory, understood):
    """Why a word or a sentence goes missing: the blank in the middle, or memory in general.

    "i keep forgetting what i was saying" is the sentence that vanishes halfway through, which is
    tiredness and distraction rather than the fading of a memory, and it wants what to do about
    it rather than how memory works. The word that will not come is the same kind of question
    with its own answer, so the row reads which one the line describes.
    """
    reading = understood if isinstance(understood, dict) else {}
    said = str(reading.get("clean") or reading.get("plain") or "").lower()
    if re.search(r"\b(?:tip of my tongue|the word (?:i|for)|a word for|word for|"
                 r"can'?t find the word|cant find the word|find the words?)\b", said):
        return ("Word-finding blanks are ordinary and commoner when you are tired, stressed or "
                "under pressure: describe the word out loud, or let it go and get on with the "
                "sentence, because it usually turns up a few minutes later once you stop "
                "reaching for it. Run through the alphabet or the first letter if you want to "
                "help it along. If you are losing everyday words often, or the wrong word comes "
                "out and you do not notice, that is worth a word with a GP.")
    if re.search(r"\b(?:saying|say|said|train of thought|mid sentence|mid-sentence|"
                 r"what i was about to)\b", said):
        return ("That is usually not memory loss: a blank mid-sentence comes from being tired, "
                "distracted or holding too much at once, and it passes. Say the last few words "
                "you did get out, or retrace the point you were making, and the rest normally "
                "follows; jotting the thing down before you go on stops it slipping again. If it "
                "starts happening most days, or it comes with losing everyday words and getting "
                "lost in familiar places, see a GP and say how long it has been going on.")
    # "i keep forgetting things at work" is a practical ask and it got the mechanism: what to do
    # comes first for a line that names the place or the tasks, and the general answer below stays
    # for the line that asks how memory works.
    if re.search(r"\b(?:at work|in work|at the office|work\b|tasks?|to-?do|deadlines?|"
                 r"meetings?|emails?|appointments?|errands?|shopping list|birthdays?)\b", said):
        return ("Keep one list instead of holding it in your head - a notebook or the notes app, "
                "written down the moment it comes up rather than later, because the thing you "
                "mean to remember is the thing that goes. Put a reminder on your phone for "
                "anything with a time on it, and if a thing takes under two minutes do it now "
                "rather than noting it. Keep a fixed place for keys, wallet and phone, and repeat "
                "a name back once when you are introduced. Most of this is too much at once "
                "rather than a fading memory, so sleep and one thing at a time help; if you are "
                "forgetting recent conversations or the names of people you know well, get it "
                "checked.")
    return ("Most forgetting is not a lost file: new memories fade unless they are slept on and "
            "retrieved, and the brain clears out details to keep the gist; being tired, stressed "
            "or trying to hold too much at once makes it worse. Write things down and sleep on "
            "it; if you are forgetting recent conversations or the names of people you know "
            "well, get it checked.")


# Every hair row in this file keys the bare word "hair", and most of the time the word is not about
# the hair on a person's head. It is down a plug hole ("how do i get hair out of the plughole" was
# told there is no medical reason to wait for a haircut), it is on a sofa or a car seat ("how do i
# get pet hair off the sofa" was told every six to eight weeks), or it is in a hairbrush. So the
# fence is the places and the owners that make it somebody else's question, and every hair row
# carries it.
# And something stuck in the hair is a rescue, not a trim: gum has its own card, and paint or resin
# is a shrug on main - better a shrug than "every six to eight weeks".
_SOMETHING_IN_THE_HAIR = ("gum", "chewing gum", "paint", "paints", "resin", "tar", "varnish",
                          "glue", "stuck", "sticky", "lice", "nits", "playdough", "slime",
                          "blu tack", "blue tack", "wax")

_HAIR_NOT_ON_A_HEAD = ("plughole", "plug hole", "plugholes", "plug holes", "drain", "drains",
                       "sink", "sinks", "basin", "blocked", "blockage", "unblock", "trap",
                       "u bend", "u-bend", "waste pipe", "bath", "baths", "bathroom", "shower",
                       "showers", "shower tray", "hairbrush", "hair brush", "hair brushes",
                       "hoover", "vacuum", "vacuumed", "tumble dryer",
                       "pet hair", "dog hair", "cat hair", "fur", "fur ball", "furball",
                       "moulting", "molting", "shedding", "sheds", "upholstery", "sofa",
                       "settee", "carpet", "rug", "car seat", "back seat", "clothes", "clothing",
                       "shirt", "jumper", "coat", "jacket", "duvet", "pillow")

# "Smoke" is a cooking verb as often as it is a habit, and the stop-smoking rows key on the verb:
# "how do i smoke a brisket" was answered "the most reliable way is nicotine replacement plus a
# stop date". The food is the subject, so a line that names one is not a habit line, and the
# smoking rows stand down for it - cooking_entries.py's smoke-meat answers it instead.
_SMOKE_IS_NOT_A_HABIT = ("brisket", "ribs", "rib", "pork", "pulled pork", "chicken", "turkey",
                         "wings", "sausage", "sausages", "salmon", "haddock", "mackerel", "trout",
                         "fish", "cheese", "tofu", "beef", "steak", "lamb", "duck", "meat",
                         "peppers", "aubergine", "eggplant", "mushrooms", "bacon", "gammon",
                         "ham", "hams", "almonds", "almond", "cashews", "nuts", "salt",
                         # "smoke a" alone stood down a person who smokes: "i smoke a pack a
                         # day" was the barbecue's, because the meat is the word that follows.
                         # The food nouns above already do that job, so the phrase is gone and
                         # the joint and the pipe are named instead.
                         "smoke some", "smoke my", "smoke the", "smoking some", "smoked it",
                         "smoke ring", "wood chips", "bark", "smoke a joint", "smoke a pipe",
                         "smoking a joint",
                         "low and slow", "internal temp", "probe")


def _asks_about_itching(understood):
    """True when the line is about the itch or the picking, not about what a scab is.

    `why does a scab itch` scored the same against the definition row and the itch row, and the
    definition came first, so the person got "a scab is a plug of dried blood" to a question
    about the itch. The definition row stands aside instead of relying on the tie.
    """
    words = understood.get("words") if isinstance(understood, dict) else None
    text = " ".join(words) if isinstance(words, list) else str(understood or "")
    return any(word in text.split() for word in
               ("itch", "itches", "itchy", "itching", "pick", "picking", "scratch", "scratching"))


def _not_about_itching(understood):
    """The `guard` the definition row uses: True when the line is not about the itch."""
    return not _asks_about_itching(understood)


# A definition is a different question from a symptom, and the words that ask for one are
# shared, so they are written once here and each row adds its own ("itch", "pick").
WHAT_IS_IT = ("what is", "whats a", "what's a", "what are", "what does", "what do", "what makes",
              "why do", "why does", "why is", "how come", "explain", "tell me about",
              "how does", "what happens")

BODY_WHAT = {
    # name: (the nouns, the asks of its own, the reply, the lines that are not this)
    "scab": (("scab", "scabs", "scabbing"),
             # the itch and the picking are the row below this one: they were in this key too,
             # and this answer outscored it on the ask words, so it led with the definition.
             # "infected" and "infection" were in this group, and a word in the key beats a
             # guard on another row: `my scab is infected` lost the infection card, which is the
             # answer that matters. A symptom is not a way of asking what a scab is.
             ("made of", "made", "form", "forms", "fall off", "falls off", "heal", "heals",
              "healing"),
             "A scab is a plug of dried blood, platelets and a stringy protein called fibrin that "
             "seals a cut while new skin grows underneath it. Leave it alone - it is the dressing - "
             "because picking it off reopens the wound and makes a scar more likely, and the itch "
             "under it is new skin and nerve endings knitting back. A scab with spreading redness, "
             "heat or pus around it is the one to get looked at.",
             # a scab in the mouth is an ulcer, and the photic sneeze answer keeps its own lines
             ("weeping", "oozing", "smell", "smells", "yellow", "green", "hot", "red", "sore",
              "painful", "knee", "arm", "face", "head", "child", "baby", "bleeding",
              "infected", "infection", "looks infected", "getting infected",
              "mouth", "in my mouth", "in the mouth", "gum", "gums", "tongue", "lip")),
    "blister": (("blister", "blisters", "blistering"),
                # "pop", "burst" and "should i" were in this group, and `should i pop a blister`
                # is a question for the plaster-and-socks card, not for the definition.
                # "prevent", "stop" and "avoid" were in this group, and they are not ways of
                # asking what a blister is: "what stops blisters" got the definition and lost
                # the plaster-and-socks prevention card. The prevention words are in `avoid`
                # below, so a how-to-stop question leaves this row to the row that answers it.
                ("come from", "form", "forms", "cause", "causes", "heal", "heals"),
                "A blister is fluid trapped under a separated top layer of skin, usually from "
                "friction, heat or a burn, and the fluid is serum protecting the new skin "
                "underneath. Leave it whole and cover it loosely - popping it invites infection - "
                "and if it bursts on its own keep it clean and put a plaster on it. A burn blister "
                "bigger than a 50p, or any blister with spreading redness, wants a pharmacist or GP.",
                ("burns", "burn", "scald", "scalded", "pop", "popped", "popping", "burst",
                 "bursting", "drain", "lance", "should i", "can i",
                 "prevent", "prevents", "preventing", "stop", "stops", "stopping", "avoid",
                 "avoiding", "not get", "from getting",
                 "feet", "foot", "heel", "toe", "shoe",
                 "shoes", "running", "walking", "hand", "finger", "mouth", "cold sore")),
    "plaque": (("plaque",),
               ("teeth", "teeth mean", "gum", "gums", "tartar", "brush", "brushing", "remove",
                "get rid", "build up", "buildup", "cause", "causes", "bad"),
               "Plaque is the soft, sticky film of bacteria that forms on teeth within hours of "
               "brushing, feeding on sugar and making the acid that causes decay and sore gums. "
               "Brushing twice a day with fluoride toothpaste and cleaning between the teeth once "
               "a day shifts it, and once it hardens into tartar only a dentist can scale it off. "
               "Blood on the toothbrush is the sign gum inflammation has started.",
               ("artery", "arteries", "heart", "brain", "skin", "psoriasis",
                "how often", "electric", "toothbrush")),
    "mole": (("mole", "moles"),
             ("check", "checks", "normal", "dangerous", "cancer", "remove", "removed", "new",
              "changing", "changed", "grow", "growing", "itch", "itchy", "bleed", "bleeding"),
             "A mole is a small cluster of pigment cells, the kind you are born with or that "
             "arrive slowly over years, and almost all are harmless. The check is the alphabet "
             "one: Asymmetry, a ragged Border, more than one Colour, a Diameter over 6mm, and "
             "anything Evolving in size, shape or itch. A new dark spot, or a mole that changes "
             "over weeks, wants a GP look rather than a wait.",
             ("on my back", "my back", "shoulder", "arm", "leg", "face", "removed", "shave",
              "garden", "grass", "in the garden", "lawn", "yard")),
    "callus": (("callus", "calluses", "callous"),
               # "painful" was in this key, so `my callus is painful` got the definition when
               # the person wanted it seen to. A symptom is not an ask.
               ("form", "forms", "cause", "causes", "remove", "get rid", "treat",
                "hard", "skin", "why"),
               "A callus is thickened skin built where repeated pressure or friction makes the "
               "skin protect itself: hands from tools, weights or a guitar, feet from tight shoes. "
               "File it gently after a bath and use gloves or better-fitting shoes so it stops "
               "coming back, and don't cut it with a blade. A painful hard lump on a foot, or any "
               "foot callus with diabetes, is a podiatrist's job.",
               ("feet", "foot", "heel", "toe", "shoe", "shoes", "running", "diabetes", "hand",
                "hands", "guitar", "weight", "weights", "deadlift", "gym",
                "painful", "pain", "hurts", "hurt", "sore", "aching", "aches", "bleeding",
                "cracked", "split", "infected")),
    "cough": (("cough", "coughs", "coughing"),
              ("dry", "chesty", "wet", "cause", "causes", "why", "what does", "mean",
               "normal", "how long", "last"),
              "A cough is a reflex that clears the airway: a quick breath in, the vocal cords "
              "shut, and air is forced out to shift mucus, dust or an irritant. Most coughs after "
              "a cold are viral and settle in two to three weeks, and honey in warm water eases "
              "the tickle. A cough with breathlessness, blood, chest pain, or one that lasts over "
              "three weeks needs a GP.",
              ("child", "baby", "kid", "toddler", "son", "daughter", "night", "at night",
               "cant stop", "can't stop", "wont stop", "won't stop", "medicine", "syrup",
               "antibiotic", "antibiotics", "get rid", "stop", "treat", "smoker", "smoking",
               "vape", "asthma", "covid", "chest infection", "fever")),
    "immunity": (("immunity", "immune system", "immune"),
                 ("how does", "how do", "what is", "work", "works", "build", "boost",
                  "stronger", "low", "weak", "mean"),
                 "Immunity is your body's memory of a germ: white blood cells that have met a "
                 "virus or a vaccine keep a record of its shape, so the next meeting is fought off "
                 "before it makes you ill. That is why some illnesses you only get once and why a "
                 "vaccine works without the disease, and why some of it fades over years - which "
                 "is what tetanus and flu boosters are for.",
                 ("boost", "boosting", "supplement", "supplements", "vitamin", "vitamins",
                  "weak", "compromised", "autoimmune", "hiv", "chemo", "steroid", "steroids")),
    "stitch": (("stitch", "stitches"),
               # `sport.py`'s stitch row already answers "a stitch in my side" better than a
               # definition can - it names the meal and the warm-up - so this one keeps only the
               # bare "what is a stitch", which nothing answered.
               ("what is", "whats a", "what's a", "explain", "mean"),
               "A stitch is a cramp-like pain in the side, from the diaphragm and the ligaments "
               "holding it being pulled while you breathe hard - most often in running. Slow down, "
               "breathe out fully, and press a hand into the sore spot; it usually eases in a "
               "minute or two, and building distance up gradually stops it coming back. Pain that "
               "stays after you stop, or comes with vomiting, is not a stitch.",
               ("get rid", "stop", "prevent", "why", "cause", "causes", "running", "run",
                "when i run", "while running", "side", "in my side", "in the side", "avoid",
                "wound", "cut", "surgery", "operation", "scar", "healing", "after birth",
                "perineum", "dissolvable", "removed", "nurse", "hospital", "a&e", "children",
                "child", "knitted")),
    "tonsils": (("tonsils", "tonsil"),
                # "swollen", "big" and "large" were in this key, so `my tonsils are swollen`
                 # got the definition instead of a throat answer. Size and soreness are symptoms.
                ("what are", "what do", "do", "for", "removed", "out", "why"),
                "The tonsils are two lumps of lymph tissue at the back of the throat that catch "
                "germs coming in through the mouth and nose, and they swell while they are "
                "fighting an infection. They shrink with age, which is why an adult's are small; "
                "very large ones in a child that cause snoring or pauses in breathing, or "
                "tonsillitis again and again, are what gets a referral.",
                ("swollen", "swelling", "big", "large", "enlarged", "lumpy",
                 "sore", "painful", "hurts", "hurt", "throat", "swallowing", "fever", "white",
                 "spots", "pus", "child", "son", "daughter", "kid", "tonsillitis", "antibiotic",
                 "antibiotics", "should i", "get them")),
    "sneeze": (("sneeze", "sneezes", "sneezing"),
               ("why", "cause", "causes", "what", "happen", "happens", "twice", "three times",
                "in a row", "sunlight", "light"),
               "A sneeze is a reflex that clears the nose: dust, pollen or a virus irritates the "
               "lining and the body takes a sharp breath and blasts air out to shift it. The droplets fly several "
               "metres, which is why you catch it in your elbow rather than your hand, and bright "
               "light makes some people sneeze.",
               # "why do i sneeze in the sun" is the photic reflex and has its own answer, which
               # names the one-in-four and the reason; this row was taking it and saying less.
               ("cant stop", "can't stop", "wont stop", "won't stop", "hayfever", "hay fever",
                "allergy", "allergies", "pollen", "cold", "flu", "covid", "snot", "blocked",
                "medicine", "antihistamine", "tablet", "tablets", "sun", "sunlight", "sunshine",
                "light", "bright", "in the sun", "in the light", "photic")),
}

_SUN_FACTORS = ("15", "20", "25", "30", "40", "50", "60", "70", "90", "100")


def _a_factor_question_without_the_sun(understood):
    """A factor of 12 is arithmetic; a factor 50 is a sunscreen. Only the sun makes it this row's.

    `factor` had to come out of this row's `avoid` for "should i use factor 50" to answer at all,
    and with it in the key a bare "what factor is 15 and 20" came here instead of the maths card:
    the sun words are what tell the two apart.
    """
    if not isinstance(understood, dict):
        return True
    text = str(understood.get("clean") or "").lower()
    if "factor" not in text:
        return True
    if any(word in text for word in ("sun", "spf", "suncream", "sun cream", "sunscreen",
                                     "sunblock", "sun factor")):
        return True
    # arithmetic says two numbers ("factor is 15 and 20") or one after an "of" ("the factors of
    # 12") or one of the maths words; a sunscreen says a single factor and a number in its range
    words = text.replace("?", " ").replace(",", " ").replace(".", " ").split()
    numbers = [word for word in words if word.isdigit()]
    if len(numbers) > 1 or ("of" in words and numbers):
        return False
    # "what factors does 24 have" and "what factor is 24 divisible by" are the same arithmetic
    # with the number in another place; and a sunscreen factor is only ever a step of five from
    # 15 to 100, so any other number with no sun word in the line is not this row's.
    if numbers and ("divisible" in words or "have" in words or "has" in words):
        return False
    if any(number not in _SUN_FACTORS for number in numbers):
        return False
    return not any(word in text for word in ("multiple", "multiples", "highest", "common"))


def _a_burn_without_the_sun(understood):
    """A burn is this row's only when the sun is what burnt it.

    The bare verbs had to be in the key for "my face burns in the sun" to score at all, because a
    key of phrases alone never reaches the two-word rule. The cost of that is every other burn:
    "what cream should i use for a burn" is the line somebody types after an oven, and sunscreen
    is the wrong thing to put on it. So a burn word with no sun word in the line stands this row
    down and the burns card answers instead.
    """
    if not isinstance(understood, dict):
        return True
    text = str(understood.get("clean") or "").lower()
    if not any(word in text for word in ("burn", "burns", "burning", "burnt")):
        return True
    return any(word in text for word in ("sun", "sunlight", "sunshine", "sun cream", "suncream",
                                         "sunscreen", "sunblock", "spf", "uv", "sunbed",
                                         "sunbed", "sun factor", "factor 30", "factor 50"))


DIZZY_SPELL = (
    "Sit or lie down the moment it starts, with your feet up, and drink a glass of water: most "
    "spells are the blood pressure dipping, not enough to drink, a skipped meal, being too hot, or "
    "a passing virus, and they pass in a minute. Get up in stages from now on, and eat something "
    "if it has been hours. See a GP if it keeps happening, if your hearing changes or rings with "
    "it, or if it happens lying down too.")


def _a_dizzy_spell(memory, understood):
    """The dizzy spell, unless the conversation is already an emergency.

    "i took an overdose", then "what have we talked about", then "i feel dizzy" is a person in
    the middle of the card that says ring 999, and a calm spell card here answers a different
    question from the one being asked. An emergency already on the table keeps its own answer.
    """
    if memory.get("safety_case") and not memory.get("safety_safe"):
        return ""
    return DIZZY_SPELL

# A pound is money before it is weight, and this row's key carries the bare word. A line that
# names a tip, a bill or a price is asking about the money, so the weight row stands down and the
# money rows answer it: "how do i work out a tip on 84 pounds" was the lose-weight plan. The
# phrases are the ones money uses, not the bare "tip", because "any tips for losing weight" is
# this row's own line and "tips" is in its ask.
POUNDS_THAT_ARE_MONEY = re.compile(
    r"\b(?:a tip|the tip|tip on|tip the|tips? for the|tipping|gratuity|service charge|"
    r"bill|bills|receipt|pence|quid|price|prices|cost|costs|costing|charge|charges|fee|fees|"
    r"pay|paid|paying|spend|spent|percent|percentage)\b|£|\$|€", re.I)


def _the_pounds_are_weight(understood):
    """False when the line's pounds are money, which the money rows answer."""
    if not isinstance(understood, dict):
        return True
    text = str(understood.get("clean") or understood.get("text") or "")
    return not POUNDS_THAT_ARE_MONEY.search(text)


# "lose" and "losing" are the only two words the forgetting row is about that are not about
# memory: they are what you say about weight, a job, a wallet and a game, and the row's own
# `avoid` sends those to their own answers. What is left over is a line that names nothing but
# the losing itself, and "how much should i lose" is an amount of weight, not a fact about how
# memories fade - yet "lose" is in the row's key and "how" in its asks, so a follow-up to
# "i want to lose weight" was answered "Most forgetting is not a lost file". An amount asked
# about a loss stands the row down unless the line says what is remembered or lost, which is
# what the row is about ("how much can you remember", "how many things have i lost").
AN_AMOUNT_OF_IT = re.compile(r"\bhow (?:much|many|long|often)\b", re.I)
WHAT_IS_REMEMBERED = re.compile(
    r"\b(?:forget\w*|forgot\w*|forgotten|memor\w+|remember\w*|things?|stuff|names?|words?|"
    r"anything|everything|dates?|numbers?|birthdays?|faces?|keys?|passwords?)\b", re.I)


# "lose" is the same verb for the temper, the plot and the job, and the row above keys on it with
# the asking words. So the object decides, the way it decides for a bereavement: a line that loses
# something nobody remembers is somebody else's question. "how do i lose my temper less" and
# "how do i lose the plot" were both given the science of forgetting.
# The pounds are not here, and nothing is being preserved by leaving them out: a weight line asks
# "how much", and `_an_amount_of_losing` already stands the row down for an amount of anything
# nobody remembers, so "how much should i lose" and "how much weight should i lose" reach the
# diet cards with or without a word for the pounds in this list. Which card wins
# "how do i lose the last stone" is the diet rows' ordering to settle, not this row's.
LOSING_SOMETHING_ELSE = re.compile(
    r"\b(?:lose|loses|losing|lost)\s+(?:the\s+|my\s+|our\s+|your\s+)?"
    r"(?:temper|patience|plot|mind|head|sleep|hair|voice|job|jobs|home|house|flat|"
    r"game|games|money|deposit|match|matches|argument|arguments|bet|race)\b", re.I)


def _an_amount_of_losing(understood):
    """False when the line asks how much is lost and never says what is remembered."""
    if not isinstance(understood, dict):
        return True
    text = str(understood.get("clean") or understood.get("text") or "")
    if LOSING_SOMETHING_ELSE.search(text):
        # "how do i lose my temper less" loses a thing nobody remembers, and the row that holds
        # the answer for it is never the science of forgetting.
        return False
    if not AN_AMOUNT_OF_IT.search(text):
        return True
    return bool(WHAT_IS_REMEMBERED.search(text))


_WHAT_WATER_IS = (
    "Water is H2O: two hydrogen atoms to one oxygen. It is wet because its molecules pull on each "
    "other and on most surfaces, so a drop spreads into a thin film instead of beading up - which "
    "is why water creeps along glass and soaked paper, and why it beads on a waxy leaf.")

# "water X" is a compound noun with its own subject - water retention, water damage, water
# pollution, water bears, water vapour, water flossing - and the fact about H2O is the wrong
# answer to every one of them. The row's `avoid` is a list of the water of everyday life, and a
# list cannot cover a shape that anyone can extend with one noun, so the row also answers only
# when "water" is the whole subject. What is left of the line once the asking words, the making
# words and "water" itself are taken out has to be nothing:
#     "what is water"              -> nothing left, the fact
#     "what is water made of"      -> "made of" is a making word, the fact
#     "what is water retention"    -> "retention" is left, so the retention answer keeps it
#     "what is water flossing"     -> "flossing" is left, so the dentist keeps it
# The words below are the ones a genuine question about water is built from, so a noun nobody
# has thought of stands the row down instead of taking a neighbour's answer.
WATER_IS_THE_SUBJECT = frozenset("""
    a about actually an and answer are as ask at be been being called can chemical chemistry
    composed composition consist consists define defined definition describe description do does
    earth element elements exactly explain explained for formula from h2o how in is it its it's
    kind made make makes made mean meaning molecule molecules name of on or out physical physics
    plain please really s science simple simply so sort substance substances tell terms than that
    the then there thing things this to up water waters what whats what's when where which who
    why you your
""".split())


def _water_is_the_subject(understood):
    """False when a word after the asking words names a compound of its own, like "retention"."""
    if not isinstance(understood, dict):
        return True
    words = [str(word).lower() for word in (understood.get("words") or ())]
    return not [word for word in words if word not in WATER_IS_THE_SUBJECT]
# A cold thing that is food is the leftovers question, not the illness: "what can i do with cold
# rice" was answered with rest, fluids and honey in warm water. The vocabulary is a guard rather
# than an avoid list because an avoid phrase is tested against the filled-in reading of a
# follow-up: after a bowl of cold rice, "what can i do for a cold" carries "cold rice" in that
# reading, and the row that answers a cold stood down on a line that names no food at all. The
# guard reads the words the person typed ("text"), which the widening leaves alone.
_COLD_FOOD = re.compile(
    r"cold (?:rice|pizza|chicken|pasta|potato|potatoes|noodles?|chips|meat|sausages?|beans|curry|"
    r"stew|takeaway|sandwich)\b|\bleft ?overs?\b|\bleft over rice\b", re.I)


def _not_a_food_cold(understood):
    """True for the illness, false for a bowl of something that has gone cold.

    A cold that is somebody being cold is not the illness either: "my mum is cold" and "the kids
    are cold" were answered with rest, fluids and honey in warm water, which is the right card
    for the wrong thing. Which of the two the word is cannot be read off the word, so the
    reading says it (bot/understanding/topics.py::the_warmth_said) and this row stands down
    where the health row that keeps somebody warm answers instead.
    """
    if (understood or {}).get("warmth"):
        return False
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or "")
    return not _COLD_FOOD.search(said)


# A baby's sleep is asked for by age - "how much should a 3 month old sleep" - and the card that
# answers it was written for the worried parent of a newborn ("a six-week-old still sleeps 15 to 17
# hours"), so a three-month-old and a six-month-old were told about a six-week-old. The age in the
# line picks the range instead, and the reassurance stays for the lines that give no age at all or
# that are a worry about the sleeping rather than a question about the hours.
_A_AGE = re.compile(
    r"\b(?P<n>\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|eighteen)"
    r"\s*(?P<unit>-?month|-?week|-?year)s?\s*old\b")
_A_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                   "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "eighteen": 18}
# "sleeping a lot", "sleeps all day", "too much" is a worry about the sleeping; "how much", "how
# many hours", "should" is a question about the hours. The two want different first sentences.
_A_WORRY = re.compile(
    r"\b(?:a lot|too much|all the time|all day|so much|more than usual|always sleeping|"
    r"sleeping loads|sleeps loads)\b")
# Months of age against the range, as the health visitor gives it: naps are counted in, and the
# total falls as the naps drop out.
_BABY_SLEEP_BANDS = (
    (0, 3, "a newborn sleeps 15 to 17 hours a day in stretches of two to four hours, day and "
           "night mixed together"),
    (3, 7, "a three to six month old sleeps about 14 to 16 hours over the 24, in three or four "
           "naps"),
    (7, 10, "a six to nine month old sleeps about 14 hours over the 24, usually in two or three "
            "naps plus eleven or so at night"),
    (10, 13, "a nine to twelve month old sleeps about 12 to 15 hours over the 24, in two naps "
             "and eleven or twelve at night"),
    (13, 36, "a one to three year old sleeps 11 to 14 hours over the 24, usually with one nap "
             "after lunch that drops somewhere between two and four"),
    (36, 72, "a three to five year old sleeps 10 to 13 hours a night, and most have given the "
             "nap up by five"),
)
_BABY_SLEEP_TAIL = ("What matters is feeding and nappies: six or more wet a day and steady "
                    "weight gain, and a call to the health visitor if they are hard to wake for a "
                    "feed.")
_BABY_SLEEP_PLAIN = ("A baby sleeping a lot is usually fine: a six-week-old still sleeps 15 to 17 "
                     "hours a day, in stretches of two to four hours, and a growth spurt makes "
                     "them sleepier for a few days. " + _BABY_SLEEP_TAIL)
# The tail is the newborn check - six wet nappies a day, steady weight gain, the health visitor if
# they are hard to wake for a feed - and it sat on the end of every age band, so the answer for a
# three year old read "A three to five year old sleeps 10 to 13 hours a night, and most have given
# the nap up by five. What matters is feeding and nappies: six or more wet a day and steady weight
# gain, and a call to the health visitor if they are hard to wake for a feed." A child of three
# has no feeds to be woken for, and the check is a baby's: it stops at a year, where the health
# visitor's weaning and weigh-in advice stops too.
_BABY_SLEEP_TAIL_UNDER_MONTHS = 12.0


def _the_age_in_months(said):
    """The baby's age in whole months, or None when the line does not give one."""
    found = _A_AGE.search(said)
    if not found:
        return None
    number = found.group("n")
    count = _A_NUMBER_WORDS.get(number, None)
    if count is None:
        try:
            count = int(number)
        except (TypeError, ValueError):
            return None
    if count <= 0:
        return None
    unit = found.group("unit").replace("-", "")
    if unit == "week":
        return count / 4.345
    if unit == "year":
        return count * 12
    return float(count)


def _a_baby_sleep_reply(memory, understood):
    said = " ".join(str(understood.get("text") or understood.get("clean") or "").lower().split())
    if not said:
        said = " ".join(str((memory or {}).get("turns", [{}])[-1].get("text", "")).lower().split())
    months = _the_age_in_months(said)
    if months is None and re.search(r"\btoddlers?\b", said):
        # a toddler is past one and short of three, and "my toddler is sleeping a lot" was told
        # about a six-week-old
        months = 18.0
    if months is None:
        return _BABY_SLEEP_PLAIN
    band = None
    for low, high, line in _BABY_SLEEP_BANDS:
        if low <= months < high:
            band = line
            break
    if band is None:
        return _BABY_SLEEP_PLAIN
    tail = _the_baby_sleep_tail(months)
    if _A_WORRY.search(said):
        # "A baby sleeping a lot is usually fine" is the reassurance for the parent of one; a
        # child of a year and up is told the same thing without the baby.
        opening = ("A baby sleeping a lot is usually fine: " if tail
                   else "Sleeping a lot is usually fine: ")
        return (opening + band + "." + tail)
    return (band[0].upper() + band[1:] + "." + tail)


def _the_baby_sleep_tail(months):
    """The newborn feeding check for a child still on milk, and nothing from a year up."""
    if months is not None and months >= _BABY_SLEEP_TAIL_UNDER_MONTHS:
        return ""
    return " " + _BABY_SLEEP_TAIL
# A record about the body, asked as a question about the thing itself: "what's the strongest
# bone in the body", "how many teeth do adults have", "why do we have fingerprints". Each is one
# fact about a named thing, and they were punts - "That's beyond what I know well, sorry" - while
# the row next door answered "how many bones does a baby have", because that key names the count
# and not the part. The subject is the part and the rest of the line is which record is wanted,
# so the table is keyed on those two and one row answers every way of asking. A part the table
# does not hold (the longest nerve, the liver's jobs) goes to whatever row does hold it.
FEMUR_RECORD = (
    "The thigh bone, the femur, is the strongest: it takes about 30 times your body weight "
    "lengthwise before it breaks, and it is also the longest bone in the body. It breaks across "
    "the shaft rather than along it, which is why a car bumper at knee height is such a common "
    "way to break one.")
STAPES_RECORD = (
    "The stapes, one of the three tiny bones in the middle ear: about 3mm long and lighter than "
    "a grain of rice. It passes the vibration of the eardrum on to the inner ear, and the three "
    "ear bones together are the smallest in the body. Because they are so small, a hard blow to "
    "the side of the head can break them.")
ENAMEL_RECORD = (
    "Tooth enamel, the outer layer of the teeth: harder than bone, and it is the only part of you "
    "that cannot repair itself, because it is not living tissue. That is why acid and grinding do "
    "permanent damage while a broken bone heals. Fluoride makes it a little more acid-resistant, "
    "which is most of what a fluoride toothpaste does.")
TEETH_RECORD = (
    "An adult has 32 teeth including the four wisdom teeth, and a child has 20 milk teeth, which "
    "start arriving at about six months and are all replaced by about 12. The wisdom teeth come "
    "last, in the late teens or twenties, and roughly a third of people never get room for all "
    "four, which is why so many are removed.")
MUSCLES_RECORD = (
    "About 600 skeletal muscles - the ones you can move on purpose - and something like 650 in "
    "all once the smooth muscle in the gut, blood vessels and bladder is counted. They are "
    "roughly 40% of your body weight, and the strongest for its size is the masseter, the muscle "
    "that closes the jaw.")
FINGERPRINT_RECORD = (
    "Fingerprints are ridges that form in the womb, and they help in two ways: the ridges give "
    "grip on a wet or smooth surface, the way a treaded tyre does, and they put the touch "
    "receptors closer to whatever you are handling, which is why a fingertip can feel a hair on "
    "a page. The pattern is set before birth and is different even in identical twins.")

FEMUR_LENGTH = (
    "The thigh bone, the femur, is the longest bone in the body - about a quarter of your height, "
    "so roughly 45cm in a 1.8m adult. The shortest is the stapes, deep in the ear, at about 3mm.")
FEMUR_BIGGEST = (
    "The thigh bone, the femur, is the biggest bone in the body: about 45cm long in a 1.8m adult, "
    "a quarter of your height, and it takes roughly 30 times your body weight lengthwise before "
    "it breaks, which also makes it the strongest. It breaks across the shaft rather than along "
    "it, which is why a car bumper at knee height is such a common way to break one.")
SARTORIUS_RECORD = (
    "The longest muscle is the sartorius, the thin one that runs from the outside of the hip "
    "across the front of the thigh to the inside of the knee - about 50cm, the longest in the "
    "body. It is the muscle that lets you sit cross-legged, and it is not a strong one: it is "
    "long and thin, and its job is to swing and turn the leg rather than to carry weight.")
STRONGEST_MUSCLE = (
    "The strongest muscle for its size is the masseter, the one that closes your jaw: the back "
    "teeth can bite with about 70kg of force, and the muscle is the strongest there is per square "
    "centimetre. The most powerful overall is the gluteus maximus in your backside, the muscle "
    "that stands you up and drives you upstairs.")
GLUTEUS_RECORD = (
    "The biggest muscle is the gluteus maximus, the large one in your backside: it is the most "
    "powerful muscle in the body and the one that straightens the hip when you stand up, climb "
    "stairs or run. The longest is a different one - the sartorius, the thin muscle that runs "
    "across the front of the thigh.")

# A record a part can hold only if the line says it is the body. "the strongest thing in the
# world" and "the hardest thing about being a parent" are not records about a body, and the
# generic words below are what put a car and a parent onto the tooth-enamel card.
_GENERIC_PARTS = ("substance", "thing", "part", "material")
_FINGER_WORDS = ("finger", "fingers", "fingertip", "fingertips", "hand", "hands", "thumb")
_SAYS_A_BODY = ("body", "bodies", "human", "humans", "animal", "mammal")
# An animal's record is not a person's: "how many teeth does a horse have" and "how many bones
# does a horse have" were both getting the human count.
_AN_ANIMAL = ("horse", "horses", "cow", "cows", "sheep", "pig", "pigs", "dog", "dogs",
              "cat", "cats", "puppy", "puppies", "kitten", "kittens", "rabbit", "rabbits",
              "hamster", "bird", "birds", "fish", "paw", "paws", "beak", "beaks",
              "tail", "tails", "animal", "animals", "pet", "pets")


BODY_RECORDS = (
    (("bone", "bones", "thigh bone", "femur"),
     ("strongest", "sturdiest"), FEMUR_RECORD),
    (("bone", "bones", "thigh bone", "femur"),
     ("biggest", "largest", "heaviest", "thickest"), FEMUR_BIGGEST),
    # "what is the longest bone" is the same bone as the strongest one, but the answer has to be
    # about length: the femur row said "it takes 30 times your body weight", which is not what
    # was asked.
    (("bone", "bones", "thigh bone", "femur"),
     ("longest", "tallest", "length"), FEMUR_LENGTH),
    (("bone", "bones", "ear"),
     ("smallest", "tiniest", "littlest", "shortest", "smallest bone"), STAPES_RECORD),
    (("substance", "thing", "part", "material", "enamel", "tooth enamel"),
     ("hardest", "toughest", "strongest"), ENAMEL_RECORD),
    (("teeth", "tooth", "adult teeth", "milk teeth"),
     ("how many", "many", "number", "count", "adults", "adult", "children", "kids", "baby",
      "people"), TEETH_RECORD),
    (("muscle", "muscles"), ("longest", "length"), SARTORIUS_RECORD),
    (("muscle", "muscles"), ("strongest",), STRONGEST_MUSCLE),
    (("muscle", "muscles"), ("biggest", "largest", "heaviest"), GLUTEUS_RECORD),
    # the count is the answer only to a count, so the ask is the count words and not "in the
    # body": "what is the longest muscle in the body" was getting "about 600 muscles"
    (("muscle", "muscles"),
     ("how many", "many", "number", "count"), MUSCLES_RECORD),
    (("fingerprint", "fingerprints", "fingertips", "finger tips", "prints"),
     ("why", "what for", "what are", "purpose", "for", "how"), FINGERPRINT_RECORD),
)

_RECORD_ASK = ("what", "whats", "what's", "which", "why", "how", "many", "much", "biggest",
               "strongest", "smallest", "longest", "hardest", "number", "count", "is", "the",
               "have", "has", "do", "does", "we", "my", "body", "adults", "adult", "people",
               "for", "what for", "purpose")


def _what_the_body_is_like(memory, understood):
    """The one record the line names, or None when it names nothing in the table."""
    text = " " + str(((understood or {}).get("clean")
                      or (understood or {}).get("text") or "")).strip().lower() + " "
    def said(word):
        return re.search(r"\b" + re.escape(word) + r"\b", text) is not None

    if any(said(word) for word in _AN_ANIMAL) and not said("human"):
        return None
    body_said = any(said(word) for word in _SAYS_A_BODY)
    for parts, asks, reply in BODY_RECORDS:
        named = [word for word in parts if said(word)]
        # a generic word is a host, not a part, so on its own it only counts when the line says
        # the record is about a body: "the hardest thing about being a parent" is not
        if not named or not any(word not in _GENERIC_PARTS for word in named) and not body_said:
            continue
        # "prints" on its own is usually a cleaning word ("how do i get prints off the window"),
        # so it only counts when the line says whose prints they are
        if "prints" in named and not any(said(word) for word in _FINGER_WORDS):
            continue
        if any(said(word) for word in asks):
            return reply
    return None


def _the_body_record_key():
    subjects = tuple(word for parts, _asks, _reply in BODY_RECORDS for word in parts)
    return subjects


# A cold and hay fever look alike on the first day and are told apart by three things the
# chemist's counter uses: itch, fever and timing. "is it a cold or hayfever" reached no row at
# all, because the line carries no asking word - "is it" is the ask and was not keyed.
_A_A_COLD = re.compile(r"\bcolds?\b|\bflu\b|\bsniffles?\b")

HAYFEVER_ADVICE = ("A once-a-day non-drowsy antihistamine (cetirizine or loratadine) is the usual "
                   "first step, and a steroid nasal spray from the pharmacy works better if your "
                   "nose is the worst part, started a week or two before your season begins. Shower "
                   "and change when you come in, keep windows shut in the morning and around midday "
                   "when the count peaks, and dry washing indoors.")


def _hayfever_or_a_cold(memory, understood):
    """Which of the two it is, when the line names both."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "text", "norm_text", "plain")).lower()
    if _A_A_COLD.search(said):
        return ("Hay fever itches - eyes, nose, throat, the roof of your mouth - and comes in "
                "sneezing fits with no fever, in the same weeks each year. A cold starts with a "
                "sore throat, then a blocked nose, a cough and often a mild fever, and clears in "
                "about a week. In June grass pollen is the usual one, so a week of antihistamine "
                "is the test.")
    return HAYFEVER_ADVICE


# "how do i make a volcano" is the bottle in a cone and "what makes a volcano erupt" is the
# geology, and the two words that tell them apart are next to each other: a verb of making or
# building in front of the volcano. An avoid word is read loosely, so the phrase had to be a
# guard, which reads the line itself.
_VOLCANO_CAUSE = re.compile(r"\b(?:what|that|which|why)\s+(?:makes|make|made|causes|cause)\b|"
                             r"\bwhy\s+(?:do|does|did)\b", re.I)
_VOLCANO_BUILD = re.compile(
    r"\b(?:make|makes|making|made|build|builds|building|built|model|models|project|projects)"
    r"\s+(?:(?:a|an|the|my|our|your|one)\s+)?(?:model\s+|paper\s+|own\s+)?volcano", re.I)


def _not_a_volcano_build(understood):
    """False when the line asks how to make a model volcano rather than why one erupts."""
    said = understood if isinstance(understood, dict) else {}
    text = " " + str(said.get("text") or said.get("clean") or " ".join(said.get("words") or ())) + " "
    if not _VOLCANO_BUILD.search(text):
        return True
    # "what makes a volcano erupt" wears the same two words - makes, then volcano - and is the
    # geology: the question word in front of the verb is what tells the two apart.
    return bool(_VOLCANO_CAUSE.search(text))
# A place-shaped ask is only half a question: "where should" on its own is "where should i stay
# in rome" as much as "where should my screen be". The posture row held both halves of the ask
# in its two groups - "where should" in the first and "should i" in the second - so every
# "where should i <verb>" line satisfied both on its own question words, and eight lookups came
# back as chair advice: "where should i stay in rome" was "Most bad posture is the chair and the
# sitting still", and so were "where should i go in lisbon", "where should i park", "where should
# i eat in york", "where should i keep my passport", "where should i hang a mirror" and "where
# should i go for my birthday". Only "where should i put my desk" had been patched, by an avoid
# word. The thing whose place is being asked about is what makes it a posture question, so the
# row now asks for the kit - the chair, the screen, the seat - and not the verb "sit": "where
# should i sit at a wedding" is a seat at a wedding, not a chair height.
_SITTING_KIT = frozenset((
    "chair", "chairs", "desk", "desks", "screen", "screens", "monitor", "monitors", "keyboard",
    "keyboards", "mouse", "mousemat", "laptop", "workstation", "office", "seat", "seating",
    "armrest", "armrests", "footrest", "posture", "slouch", "slouching", "setup",
))

_A_PLACE_SHAPED = ("where should", "where do i", "where does", "how high", "how low",
                   "too low", "too high", "set up", "setting up", "set my", "should my")

def _a_place_for_the_kit(understood):
    """Whether a line that asks where something goes is asking about the thing you sit at."""
    understood = understood or {}
    clean = " ".join(str(understood.get("clean") or "").split())
    if not clean:
        return False
    if not any(phrase in clean for phrase in _A_PLACE_SHAPED):
        return True
    return bool(set(clean.split()) & _SITTING_KIT)



# "How long does ice take to melt" is asked for a time, and the why of melting is a different
# answer: the card below opened on the molecules and left the time out of a question that asked
# only for it. The times are stated plainly, because the honest answer is "it depends on the
# size", and the sizes people actually ask about are a cube, a tray and a bag.
_ICE_WHEN = re.compile(r"\b(?:how\s+long|how\s+many\s+(?:minutes|hours)|how\s+quickly|"
                       r"how\s+fast|time\s+to|take\s+to)\b", re.I)


def _how_long_ice_takes(understood):
    """The melting time when the line asks how long, and the why of melting otherwise."""
    why = ("Ice melts when its molecules take in enough heat from the room or the air to break "
           "free of the fixed lattice they are locked in and slide around as liquid. It stays at "
           "0C the whole time it is melting, because the heat goes into loosening the bonds "
           "rather than raising the temperature.")
    text = " " + str(understood.get("clean") or understood.get("text") or "") + " "
    if not _ICE_WHEN.search(text):
        return why
    when = ("An ice cube on the counter is gone in about half an hour in a warm kitchen, and a "
            "whole tray left out takes a few hours. In a drink it is quicker still, a few minutes, "
            "because the drink is warmer than the freezer. ")
    return when + why


# --- a bruise, leading with the part of the bruise that was asked about ----------------
# One card answered every bruise line, and it opened with what a bruise is. So "how do i get
# rid of a bruise faster" was told the definition and got to the cold pack third sentence in,
# "why does my bruise hurt so much" the same, and "is it normal for a bruise to spread" nothing
# at all, because the row held no word for spreading. STYLE.md wants the answer in the first
# sentence, and the four bruise questions have four different first sentences.
_BRUISE_PLAIN = (
    "A bruise is blood leaking under the skin from small vessels broken by a knock, which is "
    "why it turns purple, then green, then yellow as the blood is cleared away. It fades on "
    "its own in one to two weeks, and a cold pack for twenty minutes with a cloth round it, a "
    "few times in the first two days, keeps it from spreading and eases the throbbing. "
    "If a bruise turns up with no injury behind it, or you bruise far more easily "
    "than you used to, get it checked: that is worth a blood test.")

_BRUISE_SPREADING = (
    "A bruise does spread a little in the first day or two, as the blood that leaked tracks "
    "along under the skin, and the colour drifting outwards is that blood being cleared rather "
    "than a new injury. Cold for twenty minutes at a time, with a cloth round the pack, for the "
    "first day or two, keeps the swelling down. Get it looked at if it is still growing after "
    "two days, if it goes hard, tight and hot, or if it came up without a knock.")

_BRUISE_FASTER = (
    "Cold is what speeds a bruise up: a cold pack for twenty minutes at a time, a cloth round "
    "it, a few times a day for the first two days, then time - and raise the limb on a cushion "
    "when you sit. It still fades over one to two weeks through purple, green and yellow, and no "
    "cream honestly changes that; arnica has little evidence behind it. Take paracetamol rather "
    "than aspirin or ibuprofen, which thin the blood and can make the bruising worse.")

_BRUISE_STAYS = (
    "A bruise that is still there after two weeks has stopped being an ordinary bruise: blood "
    "under the skin is cleared away in one to two weeks, so one that will not fade, or that keeps "
    "coming back in the same place, is worth showing to a GP. The same goes for bruising that "
    "arrives with no knock behind it, or bruising far more easily than you used to - that is a "
    "blood test, and it is a quick one. While you wait, treat it as any bruise: cold for twenty "
    "minutes at a time, a cloth round the pack, for the first day or two.")

_BRUISE_HURTS = (
    "A bruise hurts because the blood that leaked under the skin is pressing on the tissue "
    "around it, and that tightness eases over the first day or two as the blood settles and "
    "starts to clear. Cold for twenty minutes at a time, with a cloth round the pack, takes the "
    "throb down, and paracetamol is the painkiller to reach for: aspirin and ibuprofen thin the "
    "blood and can make the bruise bigger. Get it seen if the pain is worse rather than better "
    "after two days, or the area goes hard, hot and tight.")

# The order matters: a bruise that is spreading is the worry, whatever else the line asks.
_BRUISE_ASKS = (
    (("spread", "spreading", "spreads", "growing", "bigger", "larger", "getting worse"),
     _BRUISE_SPREADING),
    # a bruise that will not go is the one the GP sentence answers, and it also holds "fade",
    # so it has to be read before the how-to-heal-it branch
    (("wont go", "won't go", "not going", "doesnt fade", "doesn't fade", "not fading",
      "still there", "still here", "keeps coming back", "keeps coming", "for weeks",
      "months", "lasts", "lasting"),
     _BRUISE_STAYS),
    (("hurts", "hurt", "hurting", "pain", "painful", "throbbing", "sore", "aching", "ache"),
     _BRUISE_HURTS),
    (("faster", "quicker", "quickly", "quick", "get rid", "go away", "clear up", "heal",
      "healing", "fade", "treat", "treatment", "help"),
     _BRUISE_FASTER),
)


def _the_bruise_answer(memory, reading):
    """The bruise card, opening with the part of the bruise the line asked about."""
    text = " " + str(reading.get("text") or reading.get("clean") or "").lower() + " "
    for words, answer in _BRUISE_ASKS:
        for word in words:
            if " " + word + " " in text.replace("?", " ").replace(".", " ").replace(",", " "):
                return answer
    return _BRUISE_PLAIN


def _the_backs_are_a_body(understood):
    """True unless every "back" in the line is a direction, so this card only answers a body.

    "back" after a verb of moving is a direction: "im moving back in with my parents" was this
    card, a paragraph about a strain of a body the line never mentioned. A phrase list in `avoid`
    cannot do that job, because `avoid` is matched word by word: a line that owns a back and also
    says "moved back" - "i moved back to the gym and my back hurts", "moving home has been hard on
    my back" - was vetoed by the fence that was meant to protect the body it was talking about.
    body.py already reads the word, so the fence is that reading inverted.
    """
    from .body import _back_is_a_direction

    return not _back_is_a_direction(understood)


ENTRIES = [
    # --- light, sky, space ------------------------------------------------
    entry("sky-blue", ("sky", ("blue", "colour", "color", "rayleigh")),
          "Sunlight contains every colour, and air scatters the short blue wavelengths far more "
          "than the long red ones, so blue light reaches your eyes from all over the sky. That is "
          "also why the sky reddens at sunset: the light crosses more air, the blue is scattered "
          "away, and the reds come through.",
          avoid=("night", "dark", "black")),
    entry("sky-dark", ("sky", ("dark", "black", "night")),
          "Night is simply the side of the Earth turned away from the Sun: with no sunlight to "
          "scatter, the sky is dark. The stars are there all day too, but the bright blue "
          "scattered light drowns them out.",
          avoid=("blue",)),
    entry("sky-green", (("sky",), ("not green", "never green", "isnt", "isn't", "never")),
          "Blue is scattered much more strongly than green, so the green that is scattered "
          "arrives mixed with far more blue and the sky reads as pale blue. Violet is scattered "
          "even more, but there is less of it in sunlight and our eyes are less sensitive to it, "
          "so it never dominates.",
          # "why isnt the sky blue" is the blue question, not this one
          avoid=("blue",),
          ask=("why", "what", "colour", "color", "not", "green", "isnt", "isn't")),
entry("gas-flame-blue", (("gas flame", "gas hobs", "gas hob", "blue flame", "hob flame",
                             "flame on the hob", "boiler flame", "pilot light", "burner flame",
                             "yellow flame", "orange flame", "cooker flame", "flame yellow",
                             "flame orange", "flame is yellow", "flame is orange",
                             "flame on my cooker", "flame on the cooker"),
                            ("why", "blue", "yellow", "orange", "colour", "color", "mean", "means",
                             "normal", "safe", "should", "too much", "air")),
          "A blue gas flame is the clean one: blue means the gas is mixing with plenty of air, so "
          "it burns hot and leaves almost no soot. Yellow or orange tips mean it is short of air "
          "and burning dirty, which can give off carbon monoxide, so have the hob or boiler "
          "serviced, keep the vents clear and put a carbon monoxide alarm nearby.",
          # a smell of gas, a boiler that will not light and a bill are other rows
          avoid=("smell", "smells", "smelling", "leak", "leaking", "rotten", "egg", "boiler is",
                 "not lighting", "wont light", "won't light", "pilot light gone", "bill",
                 "meter", "pressure", "radiator", "radiators", "cooker", "oven", "barbecue",
                 "bbq", "camping", "stove", "lighter", "welding", "fireworks", "birthday",
                 # a candle and a wood fire are meant to be yellow: only a gas flame is not
                 "candle", "candles", "wood", "log", "logs", "fire", "fires", "campfire",
                 "bonfire", "torch", "lamp", "lantern", "match", "matches")),
    entry("sunset-red", (("sunset", "sunrise", "dusk", "dawn", "sun", "low sun"),
                         ("red", "orange", "pink", "yellow", "white", "colour", "color")),
          "Sunlight is white, but the air scatters the blue end of it away, so the Sun looks "
          "yellow and, low down, orange or red. At sunset the light crosses much more air, which "
          "takes out the blue and lets the reds through; dust and cloud deepen it.",
          avoid=("hot", "heat", "burn", "burning", "sunburn", "sun cream", "sunscreen",
                 "screen", "exposure", "vitamin", "lamp", "bed")),
    entry("moon-size", (("moon",),
                         ("how big", "how large", "size", "diameter", "across", "wide",
                          "bigger than", "bigger")),
          "The Moon is about 3,475 km across, a little over a quarter of the Earth's width, and "
          "you could fit about 50 Moons inside the Earth. It looks small only because it is about "
          "384,000 km away.",
          avoid=("photo", "photos", "photograph", "picture", "pictures", "camera", "phone",
                 "shoot", "capture", "zoom", "lens", "telescope", "horizon"),
          # the camera entry shares moon + how and carries a bias; the size question is this
          # entry's, and the photo words keep the camera lines out.
          bias=2),
    entry("sun-times", (("sun", "sunrise", "sunset", "sun sets", "sun set", "sun comes up",
                         "sun come up", "sun goes down", "sun go down", "gets dark", "get dark"),
                        ("what time does the sun", "what time is sunrise", "what time is sunset",
                         "what time is the sunrise", "what time is the sunset",
                         "when does the sun", "when is sunrise", "when is sunset",
                         "when will the sun", "sunrise time", "sunset time",
                         # the same ask without the word sun in it, which is how most people
                         # put it: "what time does it get dark today" reached the weekend plan,
                         # and "when does it get dark" the opening-hours note
                         "what time does it get dark", "what time does it go dark",
                         "when does it get dark", "when will it get dark",
                         "what time does it get light", "when does it get light",
                         "time of sunrise", "time of sunset",
                         "how long until sunrise", "how long until sunset",
                         "how long till sunrise", "how long till sunset",
                         "how long to sunrise", "how long to sunset")),
          "The exact time depends on where you are and the date, so I cannot give you the clock "
          "time: a weather app or the Met Office page for your postcode has it, along with "
          "tomorrow's. Sunrise moves only a minute or two a day, but the gap between sunrise and "
          "sunset swings by hours across the year.",
          avoid=("alarm", "lamp", "light therapy", "wake up light", "wake-up light",
                 "red", "orange", "pink", "colour", "color", "glow")),
    entry("sunrise-east", (("sun", "sunrise", "sunset"),
                           ("rise", "rises", "rising", "set", "sets", "setting",
                            "east", "west", "go down", "goes down")),
          "The Sun does not move round the Earth: the Earth spins from west to east, so the Sun "
          "appears to come up in the east, cross the sky and set in the west. The ground is "
          "turning under you at about 1,000 mph at the equator.",
          # a red or orange sky is the sunset-colour question, and an alarm or lamp is a
          # different sunrise altogether
          avoid=("red", "orange", "pink", "colour", "color", "glow", "alarm", "lamp",
                 "light therapy", "wake up light", "wake-up light",
                 # the exact time depends on where and when you are, which the bot cannot
                 # know: a time question is better passed on than answered with the spin
                 "what time", "when does", "when is", "time does")),
    entry("space-dark", ("space", ("dark", "black", "why")),
          "Space looks black because there is almost nothing there to scatter light into your "
          "eyes; light only reaches you if it comes straight from a star or a lit object. The "
          "sky is bright blue from Earth because our air scatters sunlight everywhere."),
    entry("sun-hot", (("sun",), ("hot", "heat", "why", "energy", "temperature")),
          "About 5,500C at the surface and around 15 million C at the core, hot enough to fuse "
          "hydrogen into helium. That reaction is what makes the heat: the Sun's own gravity "
          "squeezes the hydrogen together, and the energy crosses space as light.",
          avoid=("burn", "sunburn", "burning",
                 "today", "outside", "out there", "right now", "at the moment", "this heat",
                 "heatwave", "weather", "hot day",
                 # The star and the sunshine are two questions: "why is the sun hot" is this row,
                 # "my flat gets really hot in the sun" is a home keeping the heat out, and it
                 # was answered with the surface temperature of the Sun. A place in the line is
                 # the sign it is the second one.
                 "flat", "house", "home", "room", "bedroom", "kitchen", "office", "indoors",
                 "inside", "in here", "my place", "our place", "windows", "curtains"),
          ask=("hot", "heat", "temperature", "boil", "energy", "warm"),
          bias=2),
    entry("lava-hot",
          (("lava", "magma"), ("hot", "heat", "temperature", "how hot", "degrees", "celsius",
                               "fahrenheit")),
          "About 700 to 1,200C, or 1,300 to 2,200F, depending on the rock: basalt runs hottest and "
          "flows fastest, while the thick slow lava of a volcano like Etna is cooler. Steel melts "
          "at about 1,500C, so lava is hot enough to glow but not to melt steel."),
    entry("sun-distance",
          (("sun",), ("how far", "far away", "away", "distance", "miles", "km",
                      "kilometres", "light seconds", "how long does light")),
          "The Sun is about 150 million km (93 million miles) away, and sunlight takes 8 minutes "
          "20 seconds to reach us. That is why you never see the Sun as it is now, only as it was "
          "eight minutes ago."),
    entry("universe-size",
          (("universe", "observable universe", "cosmos"),
           ("big", "large", "wide", "size", "across", "how big", "how large")),
          "The observable universe is about 93 billion light years across, and that is wider than "
          "its 13.8 billion year age because space itself stretched while the light travelled. "
          "The whole universe may be far larger again, and we cannot see past that horizon."),
    entry("popcorn-pop",
          (("popcorn", "popping corn", "corn pop"), ("why", "pop", "pops", "popped", "explode", "kernel",
                                         "kernels", "corn")),
          "Each kernel holds a little water inside a hard shell. Heat turns that water to steam, "
          "the pressure builds until the shell splits, and the starch inside puffs out and sets: "
          "the pop is the shell giving way, and a kernel that is too dry or has a cracked shell "
          "will not pop."),
    entry("black-hole", (("black hole", "black holes"), ("what", "how", "form", "forms", "gravity")),
          "A black hole is a place where matter is packed so tightly that its gravity pulls in "
          "everything, even light. Most form when a very massive star runs out of fuel and "
          "collapses; we spot them by the way their gravity moves and heats nearby gas."),
    entry("supernova", (("supernova", "supernovae", "supernovas"),
                        ("what", "star", "explode", "explodes", "explosion", "happen", "why")),
          "A supernova is the explosion of a massive star at the end of its life: its core "
          "collapses and the outer layers are blown off, briefly outshining a whole galaxy. The "
          "iron in your blood and the calcium in your bones were made in stars that ended this "
          "way."),
    entry("galaxy", (("galaxy", "galaxies"),
                     ("what", "many", "made", "formed", "form", "big", "stars", "types")),
          "A galaxy is a huge group of stars, gas and dust held together by gravity; galaxies form "
          "as clouds of gas and dark matter pull together. Our Milky Way holds 100 to 400 billion "
          "stars and is about 100,000 light years across, and there are billions of galaxies beyond "
          "it, most with a supermassive black hole at the centre.",
          ask=("what", "many", "made", "formed", "form", "big", "stars", "types"),
          avoid=("hitchhiker", "guide", "samsung", "phone", "tablet")),
    entry("milky-way", (("milky way", "our galaxy", "galaxy called"),
                        ("what", "our", "galaxy", "why", "called", "see", "visible")),
          "The Milky Way is the galaxy we live in: a flat spiral of 100 to 400 billion stars, "
          "with the Sun about 26,000 light years from the centre. The pale band you see on a dark "
          "night is us looking along the disc from inside it.",
          ask=("what", "our", "galaxy", "why", "called", "see", "visible"),
          avoid=("chocolate", "candy", "bar", "recipe", "biscuit", "cake")),
    entry("satellite", (("satellite", "satellites"),
                        ("what", "how", "work", "orbit", "made", "stay", "natural")),
          "A satellite is anything that orbits a larger body: the Moon is Earth's natural "
          "satellite, and most people mean the machines we launch. They stay up by moving "
          "sideways fast enough that they keep falling around the Earth and missing it.",
          ask=("what", "how", "work", "orbit", "made", "stay", "natural"),
          avoid=("dish", "aerial", "tv", "television", "broadband", "internet", "receiver",
                 "signal", "phone", "phones")),
    entry("planets-orbit", (("planet", "planets", "earth"),
                            ("orbit", "orbits", "around the sun", "sun")),
          "Planets orbit the Sun because of gravity: the Sun's pull bends their straight-line "
          "motion into a curve, and their sideways speed stops them falling in. The same balance "
          "keeps the Moon going round the Earth and satellites going round the Earth.",
          ask=("orbit", "orbits", "around the sun", "sun", "how"),
          avoid=("travel", "trip", "holiday", "hotel")),
    entry("moon-follows", (("moon",),
                           ("follow", "follows", "following me", "move with me", "keep up")),
          "The Moon only looks as if it follows you: it is about 384,000 km away, so driving a "
          "few kilometres barely changes its angle against the stars. Nearby trees and houses "
          "rush past, which makes the Moon seem to keep pace.",
          ask=("follow", "follows", "following me", "move with me", "keep up", "why", "how"),
          avoid=("photo", "photograph", "picture", "camera", "shoot", "capture", "lens")),
    entry("gravity-space", (("gravity", "astronaut", "astronauts", "space station", "iss"),
                            ("space", "float", "floating", "weightless", "no gravity",
                             "zero gravity")),
          "There is gravity in space: astronauts on the space station float because they and the "
          "station are falling around the Earth together at the same speed, not because gravity "
          "has gone. At that height gravity is still about 90% as strong as it is on the ground.",
          ask=("why", "how", "what", "float", "floating", "weightless", "space"),
          avoid=("black hole", "the moon", "mars", "planet")),
    entry("speed-of-light", (("speed of light", "light"),
                             ("speed", "what", "what's", "how fast", "fast", "value")),
          "Light travels at about 300,000 kilometres per second in a vacuum, which is 299,792,458 "
          "metres per second exactly. At that speed it takes sunlight about 8 minutes to reach "
          "Earth.",
          # "light" is an everyday word - the light in the washing, a ceiling light, a traffic
          # light - and "what temperature for lights" was answered with 299,792,458 metres per
          # second. The row is the speed question, so it asks for the speed words or the other
          # light-physics words and stands aside when the line has none; the wash rows and the
          # wiring row answer the rest. The ceiling-light card in home.py carries bias=2 and
          # keys "light" and "how", so without this it also won "how fast does light travel".
          ask=("speed of light", "speed", "how fast", "fast", "value", "light year",
               "light years", "travels at", "made of", "what is light", "photon",
               "photons", "wave", "waves", "particle", "particles", "discovered",
               "measured", "how long does light"),
          avoid=("bulb", "traffic", "switch", "lamp", "room", "lunch", "meal")),
    entry("star-twinkle", (("star", "stars"), ("twinkle", "twinkling", "shimmer", "flicker",
                                              "steady")),
          "Stars twinkle because their light passes through moving layers of air, which bend it "
          "slightly this way and that before it reaches your eyes. Planets look steadier because "
          "they are close enough to show a tiny disc rather than a single point of light.",
          ask=("twinkle", "twinkling", "shimmer", "flicker", "steady")),
    entry("north-star", (("north star", "polaris", "pole star"),
                        ("what", "which", "find", "brightest", "where", "how")),
          "Polaris sits almost exactly above the Earth's north pole, so the rest of the sky turns "
          "around it while it stays put. Find it from the two stars at the end of the Big Dipper's "
          "bowl: follow the line through them about five times their gap. It is not the brightest "
          "star in the sky, just the one that marks north.",
          ask=("what", "which", "find", "brightest", "where", "how"),
          avoid=("photo", "photograph", "picture", "camera", "shoot", "capture", "exposure",
                 "lens", "telescope", "trail", "night sky", "north pole", "hotel",
                 "north star hotel")),

    # --- Earth, weather, physics -----------------------------------------
    entry("summer-hot", (("summer", "hot", "hotter", "heat"),
                         ("why", "than", "winter", "more", "cause")),
          "Summer is hotter because the Sun is higher in the sky and stays up longer, so the same "
          "patch of ground gets more direct sunlight and more hours of it. The Earth is actually "
          "farthest from the Sun in July, which is why distance is not the explanation.",
          ask=("why", "than", "winter", "more", "cause"),
          # a house that is not heating is the home domain's line, not the seasons
          avoid=("boiler", "radiator", "radiators", "thermostat", "central heating", "heating",
                 "hot water", "plumber", "kettle", "flask")),
    entry("moons", (("moon", "moons"), ("jupiter", "saturn", "mars", "earth", "venus", "neptune",
                                        "uranus", "mercury", "planet", "how many", "number of")),
          _moons, ask=("how many", "number of", "what about", "which planet", "does",
                       "names", "name", "called", "list")),
    # Not a bare "and": every follow-up in the conversation has one in it, and "ok and what
    # should i wear" was answered with this entry's difference instead of the weather.
    entry("weather-climate", ("weather", "climate", ("difference", "between", "vs")),
          "Weather is what the air is doing today: rain, wind, sun, temperature. Climate is the "
          "long-run pattern of that weather over years and decades, so one cold week says nothing "
          "about climate change and one hot day is not proof of it."),
    entry("ice-floats", ("ice", ("float", "floats", "water", "density")),
          "Water is unusual: it expands as it freezes, so ice is about 9% less dense than liquid "
          "water and floats. That is also why a full bottle left in the freezer can split.",
          # A compress on a body is the first-aid card's question, not this one: "is a hot water
          # bottle better than ice" was answered with ice being 9% less dense than water.
          avoid=("dry", "hot water bottle", "heat or ice", "ice or heat", "better than ice",
                 "ice pack", "cold compress", "compress", "sprain", "sprained", "swelling",
                 "swollen", "muscle", "sore", "ache", "aching")),
    entry("ocean-blue", (("ocean", "sea"), ("blue", "colour", "color", "why")),
          "Water absorbs red light much more strongly than blue, so the deeper the water the more "
          "the reds disappear and the blue is left. The sky's reflection adds to it, but the "
          "colour is mostly the water itself.",
          avoid=("salty", "salt", "saltier")),
    entry("sea-salty", (("ocean", "sea"), ("salty", "salt", "why")),
          "Rain wears minerals out of rocks and carries them to the sea, and when the water "
          "evaporates the salt stays behind. Rivers keep adding a little, so the sea has become "
          "salty over hundreds of millions of years.",
          avoid=("blue", "colour", "color")),
    entry("stroke-signs", (("stroke", "strokes", "mini stroke", "tia"),
                           ("sign", "signs", "symptom", "symptoms", "spot", "recognise",
                            "recognize", "first", "early", "warning", "how do i know",
                            "how would i know", "what are", "sudden",
                            # What a person asks when they want the signs rather than the
                            # definition: "what should i watch for", "what do i look out for".
                            "watch for", "watching for", "look out for", "watch out for")),
          "Think FAST: Face - ask them to smile, has one side dropped? Arms - can they raise both "
          "and hold them up? Speech - is it slurred or garbled? Time - if any of those is off, "
          "call 999 straight away and note when it started, because clot-busting treatment depends "
          "on the clock. A sudden loss of sight, or the worst headache of your life, is the same "
          "call. Do not drive them yourself.",
          avoid=("heat", "sun", "lawn", "paint", "brush", "cat", "happy", "lucky", "worry")),
    entry("tinnitus", (("tinnitus", "ringing", "buzzing", "humming", "whistling",
                        "ringing in my ears", "ringing in the ears", "buzzing in my ears"),
                       ("ear", "ears", "head", "hear", "hearing", "night", "silent", "quiet",
                        "what causes", "why", "help", "stop", "cope", "worse at night")),
          "Tinnitus is your hearing system filling silence with a sound, and it is common and "
          "rarely a sign of anything serious. It feels worse at night because the room is quiet, "
          "so give your ears something else: a fan, quiet radio or white noise at low volume. Cut "
          "back on caffeine and alcohol and look after your sleep. See a GP if it is one-sided, "
          "came with hearing loss or dizziness, or is stopping you sleeping.",
          # tinnitus is a thing in the ears, so the answer is only this one when the line says
          # ears: "why does a fridge hum" and "the fan is humming" are about the machine, and they
          # used to land here on the bare "humming" + "why". The avoid list keeps bells, alarms
          # and the phone out as well.
          # A ringing in the ears is a thing, not a machine: the ask gate wants ears, or the
          # time it happens ("ringing at night", "ringing when it's quiet"), and every machine
          # that hums is on the avoid list so nothing about it reaches this answer.
          ask=("ear", "ears", "hearing", "hear", "tinnitus", "ringing in my ears",
               "ringing in the ears", "in my head", "quiet", "silent", "silence", "at night",
               "night time", "in the night", "worse at night"),
          # a phone that rings is a call, not a thing in the ears: "my friend keeps ringing me late
          # at night" was answered with this, because "ringing" and "night" are both in the key,
          # and so was "he rings me late at night" - whoever is on the other end of the call is
          # somebody's behaviour, not a hearing question
          avoid=("ringing me", "rings me", "ring me", "rang me", "rings back", "rang back",
                 "ringing my", "ringing us", "calling me", "called me", "calls me",
                 "texted me", "messaged me", "phone", "phone is ringing", "doorbell",
                 "door bell", "bell", "bells",
                 "church", "alarm", "timer", "door", "in my head", "ring piece", "sausage",
                 # "why does my fridge hum" matched on "hum" and "why": a machine that hums is the
                 # machine's question, and the ears are what this answer is about
                 "fridge", "freezer", "washing machine", "machine", "dishwasher", "fan",
                 "extractor", "boiler", "motor", "compressor", "microwave", "kettle",
                 "laptop", "computer", "hoover", "vacuum", "engine", "car", "tumble dryer",
                 "washer", "dryer", "refrigerator", "oven", "appliance",
                 "radiator", "radiators", "printer", "pipes", "tap", "taps", "shower",
                 "light bulb", "lightbulb", "in the walls"),
          # "i have tinnitus" states it and asks nothing, which is how most people open.
          report=True),
    entry("cough-lasting", (("cough", "coughs", "coughing"),
                            ("week", "weeks", "month", "months", "wont shift", "won't shift",
                             "not going", "still", "keeps", "persistent", "long", "lingering",
                             "for ages")),
          "Most coughs after a cold last two to three weeks and settle on their own: honey in warm "
          "drinks, plenty of fluids and a propped-up pillow at night ease it, and cough medicines "
          "do little. See a GP if it lasts more than three weeks, you are coughing blood or "
          "breathless, you have lost weight, or it came with a fever that will not go.",
          ask=("week", "weeks", "month", "months", "shift", "long", "still", "keeps", "night",
               "ages", "persistent", "lingering"),
          # a line that says how long the cough has gone on wants this card over the plain one,
          # and "i have a cough for 3 weeks" was a tie that health.py's cough won
          bias=2,
          avoid=("cough drop", "cough sweets", "cough medicine", "syrup", "child", "baby",
                 "toddler", "son", "daughter", "my son", "my daughter",
                 "dog", "cat", "smoker", "smoking", "vape", "vaping")),
    # Two things on the feet that every pharmacy sells a treatment for, and both were going to
    # the search hedge: a verruca ("how do i get rid of a verruca") and athlete's foot ("my feet
    # itch between the toes"). They are the same shape of question as a cough, so they sit here.
    entry("verruca-pharmacy",
          (("verruca", "verrucas", "verruca pedis", "plantar wart", "wart", "warts"),
           ("get rid", "rid of", "remove", "removing", "treat", "treatment", "cure", "clear",
            "going", "go away", "goes away", "disappear", "freeze", "worth", "how", "best",
            "home remedy", "help", "have", "got", "keep getting", "growing", "painful")),
          "Most verrucas clear up on their own within two years, but a pharmacy treatment is "
          "quicker: soak the foot, file the hard skin down with a pumice or emery board, then "
          "paint on salicylic acid once a day for up to 12 weeks. Keep it covered in pools and "
          "gym showers. See a GP if it bleeds, is very painful, or you have diabetes or poor "
          "circulation in your feet.",
          ask=("get rid", "rid of", "remove", "removing", "treat", "treatment", "cure", "clear",
               "going", "go away", "goes away", "disappear", "freeze", "worth", "how", "best",
               "home remedy", "help", "have", "got", "keep getting", "growing", "painful"),
          # A wart on the dog is not this person's foot. Someone else's verruca is still this
          # entry's line, though: "how do i get rid of a verruca on my sons foot" wants the same
          # two-year-and-salicylic-acid answer, and the steps below never say "you".
          avoid=("my dog", "my cat", "my puppy", "the dog", "the cat", "dog", "cat", "puppy",
                 "kitten", "hamster", "horse")),
    entry("athletes-foot-itch",
          (("athlete's foot", "athletes foot", "athletic foot", "fungal infection",
            "feet itch", "foot itch", "itchy feet", "my feet itch", "itching between my toes",
            "between my toes", "between the toes", "my toes", "toes", "peeling between my toes",
            "toes itch", "toe itch"),
           ("get rid", "rid of", "treat", "treatment", "cure", "clear", "stop", "itching",
            "itch", "itchy", "keeps", "coming back", "how", "best", "help", "cream", "worth",
            "peel", "peeling", "peely", "flaky", "cracked", "sore", "smell", "smelly",
            "sweaty")),
          "Use a terbinafine cream from the pharmacy twice a day for two weeks, and carry on for "
          "a week after the itching stops or it comes back. Dry between the toes properly, wear "
          "cotton socks and change them daily, and alternate shoes so each pair dries out; wash "
          "socks at 60C. If the skin is cracked, weeping or has not cleared in a month, ask a "
          "pharmacist.",
          ask=("get rid", "rid of", "treat", "treatment", "cure", "clear", "stop", "itching",
               "itch", "itchy", "keeps", "coming back", "how", "best", "help", "cream", "worth",
               "peel", "peeling", "peely", "flaky", "cracked", "sore", "smell", "smelly",
               "sweaty"),
          avoid=("dog", "cat", "puppy", "kitten", "hands", "between my fingers")),
    entry("flu-jab", (("flu jab", "flu vaccine", "flu shot", "flu vaccination"),
                      ("should", "free", "need", "get", "worth", "who", "where", "when",
                       "eligible", "pay")),
          "In the UK the flu jab is free on the NHS if you are 65 or over, pregnant, or have a "
          "condition like asthma, diabetes or a weak immune system, and for some carers and "
          "young children. At 45 without one of those you would pay, about 15 to 20 pounds at a "
          "pharmacy, and it is worth it if you would rather not lose a week to flu. Best asked "
          "for in the autumn.",
          ask=("should", "free", "need", "get", "worth", "who", "where", "when", "pay"),
          avoid=("bird", "chicken", "poultry", "hamster", "reptile")),
    entry("teeth-check", (("teeth", "teeth checked", "dentist", "dental", "check-up",
                           "check up", "hygienist", "scale and polish"),
                          ("often", "how often", "how many times", "regular", "year", "yearly",
                           "check", "checkup", "check-up", "visit", "see")),
          "Most adults are told every six months, but if your teeth and gums are healthy a dentist "
          "may say twelve, and the NHS guidance is that the interval should be set by your risk - "
          "so ask them to write it down. Go sooner for bleeding gums, a tooth that hurts when you "
          "bite, or a mouth ulcer that has not healed in three weeks.",
          ask=("often", "regular", "year", "yearly", "check", "checkup", "check-up", "visit",
               "many"),
          avoid=("baby", "toddler", "child", "dog", "cat", "whiten", "whitening", "brace",
                 "braces", "false", "denture", "dentures", "grind", "grinding",
                 # "my manager checks up on me constantly" is a person being watched, not a
                 # dental check-up: the row's "check up" key read the watching as the appointment.
                 # Anyone at work in the line is that other question, whichever words they use.
                 "manager", "boss", "micromanage", "micromanaging", "micromanages",
                 "my team", "my staff", "colleague", "colleagues", "employee", "employees",
                 "apprentice", "trainee", "at work", "in work", "workplace", "my job",
                 "every move", "over my shoulder", "watches me", "watching me",
                 "checks on me", "checks up on me", "checking up on me")),
    entry("period-pain", (("period pain", "period pains", "period cramps", "cramps", "period",
                           "periods", "menstrual"),
                          ("worse", "worsening", "getting worse", "each month", "every month",
                           "help", "helps", "painful", "pain", "bad", "severe", "unbearable",
                           "what can i do", "stop",
                           # a heavy period is not a painful one, but it is the same subject said
                           # as a statement ("my period is heavy"), and both answers belong here
                           "heavy", "heavier", "very heavy", "so heavy", "flooding", "clots",
                           "soaking", "soak",
                           # the cycle changing is the same subject said as a change rather than
                           # a flow or a pain: "my periods have gone mad", "my period is
                           # irregular", "my periods stopped"
                           "irregular", "all over the place", "gone mad", "haywire", "skipping",
                           "skipped", "closer together", "further apart", "every two weeks",
                           "every three weeks", "randomly", "unpredictable", "stopped",
                           "stopping")),
          _period_answer,
          # The `ask` list is the second signal a statement needs, and the change of cycle is one:
          # "my periods have gone mad" names the period and the change, and without these words
          # here the row stood down and the line got a nod back. It is the same gate the heavy and
          # the painful statements come through.
          ask=("worse", "worsening", "help", "helps", "painful", "pain", "bad", "severe",
               "unbearable", "stop", "what", "heavy", "heavier", "flooding", "clots", "soaking",
               "irregular", "all over the place", "gone mad", "haywire", "skipping", "skipped",
               "closer together", "further apart", "every two weeks", "every three weeks",
               "randomly", "unpredictable", "stopped", "stopping"),
          # a cramp in a leg or a foot is a muscle, not a period: the bare word "cramps" in the
          # first group is the commonest way people say period pain, so the limb is what stands
          # this row down and lets the cramp entry answer
          avoid=("period drama", "history", "school", "grace period", "period of time",
                 "pause", "full stop", "menopause", "pregnant", "pregnancy", "test",
                 "leg", "legs", "calf", "calves", "foot", "feet", "toe", "toes", "thigh",
                 "hand", "hands", "arm", "arms", "muscle", "muscles")),
    entry("blocked-nose-lining", (("blocked nose", "nose is blocked", "bunged up", "stuffy nose",
                            "nose is bunged", "congested", "congestion", "cant breathe through my nose",
                            "can't breathe through my nose"),
                           ("what", "help", "helps", "clear", "unblock", "night", "sleep",
                            "better", "get rid", "how",
                            # "my nose is blocked all the time" is the commonest shape of the
                            # question and names no ask at all
                            "all the time", "all day", "always", "every day", "constant",
                            "constantly", "for weeks", "months")),
          "Saline spray or a salt-water rinse clears a blocked nose, and steam loosens it; sleep "
          "with your head raised. A nose blocked most days rather than after a cold is usually "
          "allergic rhinitis, and a steroid nasal spray from the pharmacy, used every day for two "
          "weeks, beats anything by mouth. A decongestant spray works a few days only - longer "
          "and the rebound makes it worse. See a GP if it is one-sided or comes with a nosebleed "
          "you cannot stop.",
          ask=("what", "help", "helps", "clear", "unblock", "night", "better", "rid", "how",
               "all the time", "all day", "always", "every day", "constant", "constantly",
               "weeks", "months"),
          avoid=("sink", "drain", "pipe", "pipes", "toilet", "road", "traffic", "spray paint",
                 "sinus", "child", "baby", "toddler")),
    entry("vitamins-with-food", (("vitamin", "vitamins", "supplement", "supplements",
                                  "multivitamin", "multivitamins", "iron tablets", "cod liver oil"),
                                 ("with food", "with a meal", "empty stomach", "before food",
                                  "after food", "when", "how", "take", "taking", "best time",
                                  "morning", "night")),
          "Take them with a meal: the fat in food helps you absorb vitamins A, D, E and K, and "
          "most people find a multivitamin easier on the stomach with breakfast. Iron is better "
          "with orange juice than with tea or coffee, which block it. Do not double up - a "
          "multivitamin plus a separate one of the same vitamin can push you over the daily limit, "
          "so compare the labels.",
          ask=("when", "how", "best", "morning", "night", "food", "meal", "stomach", "take",
               "taking"),
          avoid=("plant", "plants", "soil", "garden", "dog", "cat", "fish", "dose", "overdose",
                 "pregnant", "pregnancy", "child", "deficiency", "b12")),
    entry("stiff-neck", (("stiff neck", "neck is stiff", "neck stiffness", "neck ache",
                          "neck aches", "crick", "cricked"),
                         ("morning", "mornings", "wake up", "waking", "every", "pillow",
                          "sleep", "sleeping", "desk", "helps", "help", "what can i do")),
          "A neck that is stiff every morning is usually how you slept rather than anything else: "
          "a pillow that keeps your head in line with your spine - not propped up, not flat - and "
          "a warm shower first thing loosen it. Move it gently through its range rather than "
          "holding still. Get it checked the same day if it comes with a fever, a bad headache, "
          "or light hurting your eyes.",
          ask=("morning", "mornings", "wake", "waking", "every", "pillow", "sleep", "helps",
               "help", "what"),
          avoid=("child", "baby", "pregnant", "fever", "rash", "car", "crash", "whiplash",
                 "guitar", "violin")),
    # "how does a clock work" and "how does a mechanical watch work" were shrugs: the everyday
    # mechanism questions that a curious adult actually asks. Kept apart from "my clock is wrong"
    # and from the clock-changing line, which are different questions.
    entry("clockwork", (("clock", "clocks", "watch", "watches", "pendulum", "clockwork"),
                        ("work", "works", "working", "how does", "mechanism", "inside",
                         "tick", "tick tock", "spring")),
          "A weight or a wound spring stores the energy, a gear train slows it down, and an "
          "escapement lets it out one tick at a time - that tick is what moves the hands at a "
          "steady rate. A pendulum or balance wheel sets the rhythm, which is why a grandfather "
          "clock keeps good time and a cheap watch drifts. A quartz watch swaps the pendulum for a "
          "crystal vibrating 32,768 times a second, which a chip counts down to one second.",
          avoid=("wrong", "change", "clocks go back", "clocks go forward", "daylight", "late for",
                 "alarm", "snooze", "watch the", "watch tv", "watch a film", "watch the match",
                 "watch netflix")),
    entry("earthquakes", (("earthquake", "earthquakes", "quake", "quakes"),
                          ("happen", "happens", "cause", "causes", "caused", "why", "made",
                           "makes", "what makes", "what causes", "plate", "plates")),
          "The Earth's outer shell is broken into plates that move slowly and catch against each "
          "other. When the strain builds up and the rock suddenly slips, the ground shakes: that "
          "is an earthquake, and most happen near plate edges."),
    entry("volcanoes", (("volcano", "volcanoes", "volcanic"), ("erupt", "erupts", "eruption",
                                                               "how", "why", "what", "cause",
                                                               "causes", "magma", "lava",
                                                               # "what makes a volcano erupt" was
                                                               # the bottle-in-a-cone model: the
                                                               # row keyed cause and causes but
                                                               # not the commonest verb for it
                                                               "makes", "make", "made", "happen",
                                                               "happens", "formed", "forms")),
          "Deep underground, rock melts into magma, which is lighter than the rock around it and "
          "rises. It collects in a chamber until the pressure forces it up through a vent, and it "
          "erupts as lava, ash and gas. Most volcanoes sit where plates pull apart or push "
          "together.",
          # "how do i make a volcano for school" asks for the model, not for the geology: the
          # "how" here read as a question about how a real one works, and the bottle-in-a-cone
          # answer the study module already has (science-project-build) lost the line to this
          # row. Anything that names a project, a model or the ingredients is that row's.
          # "make a volcano" and "make one" are not in the list: an avoid phrase is read loosely,
          # words in any order and the plural form too, so "what makes a volcano erupt" matched
          # "make a volcano" and the geology question fell to a hedge. The build is a guard
          # instead, which reads the words next to each other.
          guard=_not_a_volcano_build,
          avoid=("for school", "school project", "science project", "project", "model",
                 "model volcano", "volcano model", "build",
                 "baking soda", "bicarbonate", "vinegar", "papier", "paper mache",
                 "food colouring", "science fair")),
    entry("lightning", ("lightning", ("form", "forms", "why", "cause", "causes", "strike",
                                      "strikes", "happen", "makes", "make", "what")),
          "Collisions between ice and water drops in a storm cloud build up electric charge. When "
          "the difference gets big enough, the charge leaps through the air as a huge spark: "
          "lightning, which heats the air so fast it makes the bang of thunder."),
    entry("thunder", ("thunder", ("sound", "why", "happen", "after", "lightning",
                                   "cause", "causes", "makes", "make", "what") + ORIGIN_ASK),
          "Lightning heats the air along its path to about 30,000°C in a split second, and the air "
          "expands violently, making a shock wave we hear as thunder. You see the flash first "
          "because light travels far faster than sound."),
    # The origin family: "where does X come from". Each row is the subject and the shape of the
    # ask (ORIGIN_ASK), so "where does honey come from", "honey is made from what" and "how is
    # paper made" all reach one fact and a bare "honey" still finds nothing.
    entry("honey", ("honey", ORIGIN_ASK),
          "Bees make it: a worker drinks nectar out of flowers into a honey stomach, where "
          "enzymes start breaking the sugar down, then passes it to a hive bee who packs it into "
          "a wax cell and fans the water out of it until it is too thick to spoil. One bee makes "
          "about a twelfth of a teaspoon in her whole life."),
    entry("paper", ("paper", ORIGIN_ASK),
          "Most paper is wood: chips are cooked with chemicals until the fibres separate into "
          "pulp, and the pulp is washed, pressed and dried into a sheet. Recycled paper skips the "
          "tree and goes back to pulp, and most office paper is now a mix of new and recycled "
          "fibre."),
    entry("electricity-made", (("electricity", "mains electricity", "power"), ORIGIN_ASK),
          "Nearly all of it is made by spinning a generator: gas, coal, nuclear, wind and water "
          "all turn the same kind of shaft, and the National Grid carries the result around the "
          "country and steps the voltage down through substations to your street. Solar panels "
          "are the odd ones out - they make it straight from light, with nothing turning.",
          # The consumer-unit card holds "electricity" and "where", so "where does electricity
          # come from" scored 6 there and 5 here, and the person asking about power stations got
          # the fusebox. The origin row has to outweigh it.
          bias=2),
    entry("glass", ("glass", ORIGIN_ASK),
          "Glass is sand melted with soda ash and limestone at about 1,700°C, then cooled fast "
          "enough that it sets as a liquid instead of forming crystals - which is why you can see "
          "through it. It can be melted down and remade indefinitely without losing anything."),
    entry("chocolate", ("chocolate", ORIGIN_ASK),
          "Cocoa beans grow in pods on trees in the tropics; they are fermented, dried, roasted "
          "and ground, and the fat that comes out with the powder - cocoa butter - is what makes "
          "chocolate smooth enough to melt on your tongue."),
    # The cooking row "milk" is the milk gone off; this one is where it comes from. One id for
    # two rows means one of them answers unseen and `test_knowledge_load` is red.
    entry("milk-made", ("milk", ORIGIN_ASK),
          "Dairy milk is made by cows, in the udder, from what they eat - mostly grass and "
          "silage - and it is about 87% water. A milking cow gives roughly 25 to 30 litres a day, "
          "in two or three milkings."),
    entry("eggs", ("eggs", ORIGIN_ASK),
          "Hens lay them. Each one starts as a yolk released from the hen's ovary, which picks up "
          "the white and then the shell on its way down the oviduct, roughly one egg every 25 "
          "hours in a good laying hen."),
    # The rest of the family: what a person actually asks about at the tap, in the kitchen and at
    # the pump. Each of these was a hedge, and "where does tap water come from" was worse than
    # that - the water words put it under the tradesman fallback, which offered a plumber.
    # A water that is where it should not be is a fault in the house, not a lesson in the water
    # cycle: "water is coming out of the bottom of my dishwasher" was answered "Rain soaks into
    # the ground and runs into rivers" because "water" is the subject and "coming out of" is one
    # of the ways of asking where a thing comes from. The appliances and the words for water on
    # the floor stand this row down, and the fault rows answer it.
    entry("water", (("water", "tap water", "drinking water"), ORIGIN_ASK),
          "Rain soaks into the ground and runs into rivers, and your tap water is drawn from a "
          "river, a reservoir or a borehole, then filtered and treated so nothing can grow in it "
          "and pumped to the house under pressure. A town near hills is usually fed from a "
          "reservoir; anywhere else it comes from a river or from deep underground.",
          avoid=("dishwasher", "washing machine", "washer", "tumble dryer", "fridge", "freezer",
                 "leaking", "puddle", "puddles", "flooded", "flooding")),
    entry("bread", (("bread", "loaf", "loaves"), ORIGIN_ASK),
          "Flour, water, salt and yeast. The yeast gives off gas as it feeds on the flour, and "
          "the gluten in the flour - stretchy because it is wheat - traps it as bubbles, which is "
          "what makes the loaf rise; the oven then sets the structure and browns the crust."),
    entry("salt", (("salt",), ORIGIN_ASK),
          "Either dug up as rock salt, laid down by seas that dried out long ago, or dried out of "
          "sea water in shallow ponds. Both are the same sodium chloride, and the difference in "
          "the shop is the size of the crystal and whether iodine or an anti-caking agent has "
          "been added."),
    entry("petrol", (("petrol", "petroleum", "diesel", "fuel"), ORIGIN_ASK),
          "Crude oil, heated in a refinery until its parts separate by boiling point. Petrol is "
          "one of the light fractions taken off near the top, then cleaned and blended, which is "
          "why it evaporates so quickly and catches light so easily.",
          # a fuel bill or a car that will not start is not the chemistry of the pump; the light
          # fractions row stands down and the car card keeps its line
          avoid=("car wont", "car won't", "wont start", "won't start", "misfuel", "misfuelled",
                 "wrong fuel", "diesel in", "petrol in", "bill", "cost", "price", "cheap",
                 "cheapest", "per litre", "a litre", "fill up", "empty")),
    # "where does coffee grow" and "where is tea grown" are the same question as where it comes
    # from, and the family's phrases have "grown in" and "grows on" but nothing that a bare "grow"
    # answers, so the two that people grow get their own
    entry("tea", (("tea",), ORIGIN_ASK + ("tea grow", "tea grown", "tea growing", "tea planted")),
          "One bush, Camellia sinensis: the leaves are picked, then wilted, rolled and dried, and "
          "how far they are allowed to oxidise decides the kind - none for green, all the way "
          "for black. Almost every tea in the shop, white, green, oolong and black, comes off that "
          "same bush.",
          # a cup's worth of questions (caffeine, milk, how to brew, how many cups) are the
          # kitchen's, not the shrub's
          avoid=("caffeine", "milk", "brew", "brew it", "stewed", "cups", "cup a day",
                 "how many cups", "before bed", "bag", "bags", "sugar", "green tea good",
                 "black tea good", "iced", "sweet tea")),
    entry("coffee", (("coffee",), ORIGIN_ASK + ("coffee grow", "coffee grown", "coffee growing",
                                                 "beans grow", "beans grown")),
          "Coffee beans are the seeds of a cherry that grows on bushes in the tropics, mostly in "
          "a band round the equator. The picked fruit is dried, the two seeds inside are "
          "removed and roasted, and the roast is what turns them brown and flavours the drink.",
          avoid=("caffeine", "how much", "cups a day", "cup a day", "before bed", "instant",
                 "machine", "grinder", "ground", "brew", "strong", "decaf", "milk", "sugar",
                 "stain", "stains", "stained")),
    entry("wine", (("wine",), ORIGIN_ASK),
          "Grapes, crushed and left to ferment: the yeast on the skins eats the sugar in the juice "
          "and turns it into alcohol. Red wine spends its time with the skins and white is "
          "pressed off them first, which is where the colour comes from.",
          avoid=("red wine", "white wine", "glass of", "bottle", "hangover", "stain", "stains",
                 "pair with", "open", "leftover", "keeps", "calories", "sulphites", "sulfites")),
    # A material is the same question as a food: where it comes from. Each of these stood as a
    # punt - "where does steel come from" even after the origin family was there, because no row
    # names steel - and each carries the sense its subject shares with a kitchen or a laundry:
    # a pan is not the alloy, and a shrunk jumper is not the sheep.
    entry("cheese", (("cheese", "cheddar"), ORIGIN_ASK),
          "Milk, and mostly cow's milk: it is warmed, a culture and rennet go in so the curds set, "
          "and the curds are cut, pressed and salted. Roughly 10 litres of milk go into a kilo of "
          "hard cheese, which is where the whey drains off to.",
          avoid=("melt", "melted", "melting", "grated", "substitute", "instead", "toast",
                 "toastie", "mouldy", "mould", "gone off", "how much", "calories", "bake",
                 "freeze", "keeps")),
    entry("steel", (("steel", "stainless steel"), ORIGIN_ASK),
          "Iron with a little carbon in it - under about 2% - and the stainless kind also has "
          "chromium, which is what stops it rusting. The carbon is the part that makes it hard: "
          "pure iron is soft and bends.",
          avoid=("pan", "pans", "knife", "knives", "wok", "rust", "rusty", "cutting",
                 "sharpen", "seasoning", "wool", "scrub", "scourer")),
    entry("plastic", (("plastic", "plastics"), ORIGIN_ASK),
          "Oil or gas, mostly: the refinery makes small molecules like ethylene and propylene and "
          "a chemical plant links them into long chains called polymers. How the chains are built "
          "decides whether it ends up as a clear bottle or a washing-up bowl.",
          avoid=("recycle", "recycling", "recycled", "bin", "bins", "bpa", "microwave",
                 "freezer", "freeze", "smell", "melt", "melting", "safe")),
    entry("rubber", (("rubber",), ORIGIN_ASK),
          "Latex sap from the rubber tree, for natural rubber: it is tapped out of the bark, then "
          "mixed with sulphur and heated, which links the chains so it springs back instead of "
          "staying sticky. Most car tyres are synthetic rubber made from oil.",
          avoid=("tyre", "tyres", "puncture", "smell", "perished", "perishing", "seal", "washer",
                 "gasket", "glue", "stuck", "squeak", "wipers", "boot")),
    entry("wool", (("wool", "woollen", "woolen"), ORIGIN_ASK),
          "Sheep, and sometimes alpaca, goat or rabbit: the fleece is shorn once a year, washed, "
          "carded into loose fibres and spun into yarn. Merino is the same sheep bred for a finer "
          "fibre, which is why it does not itch.",
          avoid=("shrink", "shrunk", "shrank", "wash", "washing", "bobble", "bobbles", "itch",
                 "itchy", "jumper", "cardigan", "socks", "moth", "moths", "dryer", "tumble")),
    entry("cotton", (("cotton",), ORIGIN_ASK),
          "The boll of the cotton plant, which is a ball of fluff around the seed: the fibres are "
          "picked, ginned out of the seed, combed straight and spun into thread. The plant wants "
          "heat and a long dry season, which is why so much of it grows in India, China and the "
          "southern United States.",
          avoid=("shrink", "shrunk", "wash", "washing", "iron", "bleach", "tshirt", "t-shirt",
                 "shirt", "sheets", "towel", "dryer", "tumble", "bobble")),
    entry("silk", (("silk", "silks"), ORIGIN_ASK),
          "Silkworms, the caterpillars of a moth, which spin a cocoon out of one continuous "
          "thread. The cocoons are unwound into a single fibre, which is why silk is smooth and "
          "strong where cotton is short fibres twisted together.",
          avoid=("wash", "washing", "iron", "stain", "stains", "dress", "shirt", "tie",
                 "delicate", "shrink", "dry clean")),
    entry("sugar", (("sugar", "white sugar", "brown sugar"), ORIGIN_ASK),
          "The juice of sugar cane or of sugar beet, boiled down until the sugar crystallises out "
          "and the molasses drains away. Brown sugar is white sugar with some of that molasses "
          "left on or stirred back in.",
          avoid=("how much", "blood sugar", "diabetes", "diabetic", "icing", "caster",
                 "granulated", "instead of", "substitute", "cut down", "give up", "addictive",
                 "teeth", "cavities", "cravings", "too much")),
    entry("olive-oil", (("olive oil", "olive oils"), ORIGIN_ASK),
          "Olives, crushed and pressed: the fruit is ground to a paste and the paste is pressed or "
          "spun so the oil separates from the water and the solids. Extra virgin means pressed "
          "cold with low acidity; the refined kind is heat-treated and blended.",
          avoid=("how much", "smoke", "smoking", "fry", "frying", "instead of", "butter",
                 "calories", "healthy", "healthier", "keep", "store", "rancid", "goes off",
                 "bottle", "use up")),
    entry("rice", (("rice", "paddy"), ORIGIN_ASK + ("rice grow", "rice grown", "rice growing",
                                                     "grows rice")),
          "Rice grows in a paddy: a field walled to hold a few inches of water, planted with "
          "seedlings and flooded for most of the season. It wants heat and a lot of water, which "
          "is why so much of it comes from Asia.",
          avoid=("cook", "boil", "how long", "leftover", "microwave", "keep", "reheat",
                 "washing", "rinse", "absorb", "calories")),
    entry("bananas", (("banana", "bananas"), ORIGIN_ASK + ("bananas grow", "bananas grown",
                                                           "banana grow", "banana tree")),
          "On a huge herb rather than a tree: the plant pushes up a single stem, flowers once and "
          "fruits once, and then it is cut down and a shoot from the root takes over. Bananas want "
          "heat and rain all year, which is why they come from the tropics.",
          avoid=("ripen", "ripe", "store", "keep", "brown", "black", "freeze", "mash", "bread",
                 "bunch", "smoothie", "too many", "gone soft")),
    entry("apples", (("apple", "apples", "apple tree"), ORIGIN_ASK + ("apples grow",
                                                                      "apples grown",
                                                                      "apple grow")),
          "On trees, and in an orchard nearly every tree is grafted: the fruiting variety on top "
          "and a rootstock underneath that decides how tall it grows. An apple grown from a pip "
          "comes up a different apple, which is why every Cox is a cutting of one old tree.",
          avoid=("store", "keep", "cook", "pie", "crumble", "bake", "fall", "drop", "windfall",
                 "juice", "brown", "soft", "variety")),
    entry("vanilla", (("vanilla", "vanilla pod", "vanilla pods"), ORIGIN_ASK),
          "The pod of an orchid, and it has almost no smell when it is picked: the pods are cured "
          "for months, dried and sweated until the flavour crystals form. The flowers have to be "
          "pollinated by hand outside Mexico, which is why real vanilla costs so much.",
          avoid=("essence", "extract", "substitute", "instead", "ice cream", "custard", "cake",
                 "how much", "cheaper")),
    entry("leather", (("leather", "suede"), ORIGIN_ASK),
          "Animal hide, mostly cow, that has been tanned: the skin is cleaned, then treated with "
          "tannins or chromium so the protein stops rotting and stays soft. Suede is the same "
          "skin buffed on the inside face.",
          avoid=("clean", "cleaning", "condition", "conditioner", "scuff", "scuffs", "shoe",
                 "shoes", "sofa", "jacket", "bag", "smell", "stain", "stains", "crack")),
    entry("rain", ("rain", ("form", "forms", "why", "fall", "falls", "happen")),
          "Water evaporates, rises and cools, and its vapour condenses into tiny droplets that "
          "make clouds. Those droplets collide and grow until they are too heavy to stay up, and "
          "then they fall as rain.",
          avoid=("bow", "bows", "coat", "jacket")),
    entry("metal-cold", (("metal",), ("cold", "colder", "feels", "touch", "why")),
          "Metal is not colder than the room; it conducts heat away from your hand much faster "
          "than wood or cloth, so your skin loses heat quickly and reads that as cold. That is "
          "also why a metal spoon feels cold and a wooden one does not."),
    entry("soap", ("soap", ("work", "works", "clean", "germs", "hands", "why")),
          "Soap molecules have one end that grabs water and one that grabs oil and grease, so "
          "they surround dirt and lift it off your skin into the water. Washing with water alone "
          "leaves the oils behind; the rubbing and rinsing matter as much as the soap."),
    entry("static", (("static", "static electricity"), ("shock", "spark", "hair", "why",
                                                         "happen")),
          "Rubbing two materials together can pull electrons from one to the other, leaving a "
          "charge that builds up on a surface. When you touch something, the charge jumps across "
          "as a small spark, which you feel as a shock.",
          # how to stop it is the hair and clothes entries' question, not this one's
          avoid=("stop", "stops", "stopping", "prevent", "preventing", "get rid", "fix",
                 "reduce", "how can i",
                 # a head that is full of static is asking to be helped, not explained, and that
                 # card is clothing.py's: "my hair is full of static" got the paragraph about
                 # electrons because the science row only stood down on a "how do i stop" shape
                 "full of static", "all static", "so much static", "nothing but static",
                 "goes static", "going static", "bit of static", "so static", "really static",
                 "very static", "gets static", "getting static", "keeps going static",
                 # a shock getting out of a car wants the practical answer, which clothing has
                 "car", "cars", "seat", "seats", "van", "door handle")),
    entry("magnets", (("magnet", "magnets", "magnetic"), ("work", "works", "why", "attract",
                                                           "field")),
          "A magnet has a magnetic field, and it pulls on materials whose electrons can line up "
          "with that field, like iron, nickel and cobalt. Cut a magnet in half and you get two "
          "smaller magnets, each with its own north and south pole."),
    entry("magnet-what", (("magnet", "magnets"),
                          ("what", "mean", "made", "material")),
          "A magnet is an object that produces a magnetic field, which pulls on iron, nickel and "
          "cobalt and pushes or pulls on other magnets. In most fridge magnets the field comes "
          "from tiny magnetic regions lined up in the same direction; in a compass needle it comes "
          "from a small piece of magnetised metal.",
          ask=("what", "mean", "made", "material"),
          avoid=("work", "works", "how", "field", "attract", "repel")),
    entry("electricity", (("electricity",), ("what", "how", "work", "works", "flow")),
          "Electricity is the flow of electric charge, usually electrons pushed along a wire by a "
          "voltage. A circuit has to be a complete loop: the source pushes the charge, the wires "
          "carry it, and a device like a bulb uses the energy as it passes."),
    entry("sound-travel", ("sound", ("travel", "travels", "speed", "faster", "vacuum", "through")),
          "Sound is a vibration that travels as a wave through air, water or solids; in air it "
          "moves at about 343 metres per second. It travels faster in water and fastest in "
          "solids, and it cannot travel through a vacuum because there is nothing to vibrate.",
          ask=("how", "why", "fast", "speed", "travel")),
    entry("plane-fly", (("plane", "planes", "aeroplane", "airplane", "aircraft"),
                        ("fly", "flies", "lift", "wing", "wings", "aerodynamics", "stay")),
          "A wing is shaped so air moves faster over the top than underneath, and the pressure "
          "difference pushes the wing up; that force is called lift. Engines provide the forward "
          "thrust, and lift grows with speed until it beats the plane's weight.",
          ask=("how", "why", "what")),
    entry("gravity", (("gravity",), ("work", "works", "what", "why", "pull", "force")),
          "Gravity is the attraction between anything with mass: the Earth pulls you toward its "
          "centre, and you pull the Earth back by the same rule. Bigger mass means a stronger "
          "pull, which is why the Moon orbits the Earth and the Earth orbits the Sun."),
    entry("atoms", (("atom", "atoms"), ("what", "made", "small", "how", "matter")),
          "An atom is the smallest unit of an element, with a nucleus of protons and neutrons "
          "surrounded by electrons. Atoms join into molecules, and everything you can touch is "
          "made of them; they are mostly empty space."),
    entry("dna", (("dna",), ("what", "mean", "stand", "do", "gene", "genes", "work")),
          "DNA is the long molecule that carries the instructions for building and running a "
          "living thing, written in a four-letter code. Genes are sections of it, and they are "
          "copied from parents to offspring."),
    entry("cell-what", (("cell", "cells"),
                        ("what", "smallest", "body", "living", "biology", "made", "inside",
                         "how many")),
          "A cell is the smallest unit of a living thing: a jelly-like space wrapped in a thin "
          "skin, with DNA inside and machinery that turns food into energy. Your body is made of "
          "about 30 trillion of them, and each kind is shaped for its job, from a nerve cell that "
          "carries signals to a red blood cell that carries oxygen.",
          ask=("what", "smallest", "body", "living", "biology", "made", "inside", "how many",
               "how", "why"),
          avoid=("prison", "jail", "police", "holding", "phone", "battery", "solar", "fuel",
                 "spreadsheet", "excel", "terror", "hotel", "room", "monk", "cellar")),
    entry("evolution", (("evolution",), ("work", "works", "natural", "selection", "what", "how")),
          "Living things vary, and the ones whose variations suit their surroundings tend to "
          "survive and pass those variations on. Over many generations that selection changes "
          "the population: small changes accumulate into new species."),
    entry("vaccines", (("vaccine", "vaccines", "vaccination", "jab", "immunisation", "immunization"),
                       ("work", "works", "teach", "teaches", "body", "immune", "how")),
          "A vaccine shows your immune system a harmless piece or blueprint of a germ, so it can "
          "practise making antibodies without you getting ill. If the real germ turns up later, "
          "those memory cells recognise it and fight it off fast."),
    # "how do plants make seeds" was answered with photosynthesis: `plants-make-food` keys the
    # verbs make/eat/feed, and a seed is the flower's job rather than the leaf's.
    entry("how-seeds-form",
          (("seed", "seeds", "seedling", "pollination", "pollinate", "pollen"),
           ("form", "forms", "made", "make", "makes", "grow", "grows", "plant", "plants",
            "flower", "flowers", "fruit", "how", "why", "where do", "come from", "produce")),
          "In the flower: pollen from the male part (the stamen) lands on the sticky tip (the "
          "stigma), and a tube grows down to the ovule at the base. The fertilised ovule becomes "
          "the seed and the ovary around it swells into the fruit - which is why every fruit has "
          "seeds inside. Wind, insects or your own brush carry the pollen; a tomato or a pea "
          "pollinates itself before the flower even opens.",
          bias=1,
          # a seed to eat is cooking's question, and sowing one is the garden's
          avoid=("eat", "eating", "toast", "bread", "recipe", "bake", "sow", "sowing", "plant out",
                 "when do i plant", "when should i plant", "bird seed", "sunflower seed",
                 "sesame", "chia", "pumpkin seed", "seed tray", "germinate", "germination")),
    entry("plants-make-food", (("plant", "plants", "tree", "trees"),
                               ("food", "make", "makes", "made", "eat", "eats", "feed",
                                # "how do plants get energy" is the same question, and the
                                # answer is the same reaction.
                                "energy")),
          "Plants make their own food by photosynthesis: they take carbon dioxide from the air and "
          "water from the soil and use sunlight to turn them into sugar. The green chlorophyll in "
          "their leaves captures the light, and oxygen is released as a by-product.",
          # A houseplant feeding schedule shares both words (plant, feed/food) and is the same
          # tie, so the fact about how a plant makes its own food keeps this question.
          avoid=GRAZERS + PESTS_AND_CARE, bias=1),
    entry("photosynthesis", (("photosynthesis",), ("plant", "plants", "leaves", "explain", "what",
                                                    "how")),
          "Plants use sunlight to turn carbon dioxide from the air and water from the soil into "
          "sugar, which is their food, and they release oxygen as a by-product. The green "
          "chlorophyll in their leaves captures the light that powers it."),
    entry("oxygen-source", ("oxygen", ("come", "comes", "from", "plants", "produced", "where",
                                       "make", "made")),
          "The oxygen in the air comes from photosynthesis: plants, algae and plankton split water "
          "and release oxygen as they make sugar. Most of the oxygen you breathe was made by "
          "ocean plankton rather than trees."),
    entry("plant-roots", (("roots", "root", "root system"),
                          ("plant", "plants", "why", "what", "have", "need", "do")),
          "Roots do three jobs: they hold the plant in the ground, they take up the water and "
          "minerals the leaves cannot make, and they store food for next year. The fine root hairs "
          "are what does the drinking, which is why a plant in a small pot dries out so fast.",
          # A root that is not a plant's is a different question: a tooth, a hair, a pipe under
          # the lawn, a root vegetable in the kitchen.
          avoid=("canal", "dental", "tooth", "teeth", "hair", "tree roots", "cracks", "pipes",
                 "drains", "blocked", "beetroot", "carrot", "carrots", "parsnip", "swede",
                 "turnip", "ginger", "turmeric", "propagate", "propagation", "cutting",
                 "cuttings", "bare root", "root bound", "rootbound", "rot", "rotting",
                 # grey roots are a dye job and there is no hair in the line to say so:
                 # "how do i cover my grey roots" was told what a plant's roots do
                 "grey", "gray", "dye", "dyed", "colour", "color", "regrowth",
                 "touch up", "touch-up")),
    entry("plant-sunlight", (("plant", "plants"),
                             ("need", "needs", "use", "uses", "without", "why")),
          "Plants need sunlight as the energy source for photosynthesis, the reaction that makes "
          "their food. Without enough light they cannot make sugar, so they stop growing and "
          "their leaves yellow and drop.",
          # The subject has to be a plant (or light): a pale leaf or a leggy seedling is this
          # answer too, so the plant words are back in the ask.
          ask=("plant", "plants", "leaf", "leaves", "grass", "tree", "trees",
               "sunlight", "sun", "light", "shade", "dark", "windowsill"),
          # A flickering bulb and a plant both want the word light; only one of them is asking
          # about photosynthesis. A green plant is the pigment question, not the light one.
          avoid=("green", "colour", "color") + PESTS_AND_CARE + (
                                  "flicker", "flickers", "flickering", "bulb", "bulbs", "switch",
                                  "socket", "wiring", "fuse", "led", "headlight", "headlights",
                                  "torch", "streetlight", "streetlights",
                                  # soil and its minerals have their own entry below
                                  "soil", "compost", "dirt", "potting", "nutrient", "nutrients",
                                  "minerals", "fertiliser", "fertilizer",
                                  # a plant that fell off the windowsill is a knocked-over pot,
                                  # not a question about where the light comes from
                                  "dropped", "dropping", "fell", "fallen", "knocked", "tipped",
                                  "broke", "broken", "cracked", "smashed", "spilled", "spilt")),
    entry("plant-soil", (("plant", "plants", "roots"),
                         ("soil", "compost", "dirt", "potting", "nutrient", "nutrients",
                          "minerals", "fertiliser", "fertilizer")),
          "Soil holds a plant up and holds the two things it needs: water around the roots and the "
          "minerals it cannot make itself, like nitrogen for leaves and phosphorus for roots. "
          "Plants can grow without it only if someone feeds them those minerals in water, which "
          "is how hydroponics works.",
          # A dry pot or a repotting question is care, and the plant entries own those lines.
          avoid=PESTS_AND_CARE + ("water", "watering", "dry", "damp", "when", "how often",
                                  "repot", "compost heap", "weed", "weeds", "mould", "mold",
                                  "white", "fungus", "gnats", "flies",
                                  # "pot" is a loose form of the key word "potting", so a dropped
                                  # or broken plant pot was read as a question about minerals
                                  "dropped", "dropping", "fell", "fallen", "knocked", "broke",
                                  "broken", "cracked", "smashed", "shattered", "tipped",
                                  "spilled", "spilt")),
    # A curling leaf is a climate or pest question, not a photosynthesis one: it was answered with
    # the sunlight fact, which is true and useless to someone looking at a curled leaf.
    entry("plant-leaves-curl",
          (("leaf", "leaves", "plant", "plants", "tomato", "tomatoes", "basil", "fern", "rose"),
           ("curl", "curls", "curled", "curling", "rolled", "rolling", "crinkled", "wrinkled")),
          "Curling is nearly always the climate rather than a disease: dry air and a hot windowsill "
          "make the edges roll up, and a plant that dried out badly once keeps its new leaves "
          "curled. Water it properly and move it off direct sun, then feel under the curled leaves "
          "for aphids, which cluster on soft new growth and make it pucker.",
          ask=("plant", "plants", "leaf", "leaves", "tomato", "tomatoes", "basil", "fern", "rose",
               "seedling", "seedlings", "houseplant", "houseplants"),
          avoid=PESTS_AND_CARE + ("hair", "page", "paper", "eyelash", "toenail", "nail",
                                  "curling tongs", "curling wand", "straighteners")),
    # "how much sun does a tomato need" was a shrug while "how do i grow tomatoes" answered.
    entry("tomato-sun",
          (("tomato", "tomatoes", "tomato plant", "tomato plants", "tomato seedlings"),
           ("sun", "sunlight", "light", "shade", "how much", "hours", "sunny", "windowsill")),
          "Tomatoes want full sun - six to eight hours a day - and they will not set fruit in shade. "
          "A south-facing wall or a sunny patio is ideal, and indoors they need the brightest "
          "windowsill you have plus a turn now and then so they do not lean. Too little light gives "
          "you a tall pale plant with leaves and no tomatoes.",
          ask=("tomato", "tomatoes"),
          avoid=("ketchup", "sauce", "soup", "salad", "chutney", "pizza", "recipe", "recipes",
                 "grow from seed", "how do i grow", "water", "watering", "feed", "feeding")),
    entry("plant-not-growing",
          (("plant", "plants", "houseplant", "houseplants", "seedling", "seedlings", "basil",
            "fern", "monstera"),
           ("not growing", "isnt growing", "isn't growing", "stopped growing", "no growth",
            "no new growth", "wont grow", "won't grow", "stunted", "slow to grow",
            "hasnt grown", "hasn't grown", "havent grown", "has not grown", "have not grown",
            "not grown", "grown in months", "grown at all", "growth",
            # "my houseplant hasnt grown in months" carries no "not": the negated word is the
            # auxiliary, so the participle has to be in the key on its own
            "grown")),
          "Three things stop a plant growing, in order: not enough light, a pot that is full of "
          "roots, and no food. Move it somewhere brighter for a fortnight, check whether roots are "
          "coming out of the drainage holes, and give it a feed - that order fixes most of them. A "
          "plant that has not grown since autumn is usually asleep rather than ill.",
          ask=("plant", "plants", "houseplant", "houseplants", "seedling", "seedlings", "basil",
               "fern", "monstera", "cactus", "orchid"),
          avoid=PLANT_CARE_AVOID + ("child", "children", "baby", "kid", "kids", "teenager",
                                    "beard", "hair", "tumour", "tooth", "teeth",
                                    # "my plant has grown a lot" is not a complaint
                                    "a lot", "lots", "so much", "loads", "bigger", "taller",
                                    "massive", "huge")),
    entry("houseplant-feed-growing",
          (("feed", "feeding", "fertiliser", "fertilizer", "plant food", "houseplant food",
            "nutrients"),
           ("houseplant", "houseplants", "plant", "plants", "often", "much", "need", "winter")),
          "Feed houseplants only while they are growing, from March to September: a half-strength "
          "liquid feed every two to four weeks is plenty, and none in winter while they rest. "
          "Overfeeding is worse than underfeeding - it burns the roots and leaves white crust on "
          "the compost - so if the leaves look pale, check the light before you reach for more "
          "food.",
          ask=("houseplant", "houseplants", "plant", "plants", "orchid", "fern", "basil",
               "monstera", "cactus", "succulent", "compost", "pot"),
          avoid=("baby", "babies", "breast", "breastfeeding", "formula", "bottle", "newborn",
                 "cow", "cows", "calf", "calfs", "calf's", "sheep", "horse", "dog", "cat",
                 "bird", "birds", "wildlife", "sourdough", "yeast", "starter", "twitter",
                 "facebook", "newsfeed", "rss")),
    entry("compost-mould",
          (("mould", "mold", "fuzz", "fungus", "white fluffy", "grey fluffy"),
           ("soil", "compost", "pot", "pots", "surface", "houseplant", "houseplants", "top of the pot")),
          "That white or grey fuzz on the compost is a fungus eating dead plant matter, and it is "
          "harmless to the plant: scrape the top centimetre off, water less and let the surface dry "
          "between waterings, and give the room some air. It only appears where the compost stays "
          "warm and wet.",
          ask=("soil", "compost", "pot", "pots", "surface", "houseplant", "houseplants", "plant",
               "plants"),
          # A seedling tray is the one place white mould is not harmless: damping off collapses
          # the seedling at soil level and its own row says so. "my seedling compost is mouldy"
          # was the damping-off answer on main f7fe9dda1 and reached this row once a new key word
          # elsewhere changed a rarity point, which is the third time this week that adding a
          # word has flipped a tie nobody meant to touch.
          avoid=PESTS_AND_CARE + ("bread", "jam", "wall", "walls", "bathroom", "shower", "ceiling",
                                  "fridge", "food", "cheese", "fruit", "tennis", "badminton",
                                  "seedling", "seedlings", "seed tray", "damping off", "damping",
                                  # a pot of food is the gone-off answer, not the compost one
                                  "curry", "stew", "soup", "sauce", "rice", "pasta", "noodles",
                                  "risotto", "casserole", "chilli", "chili", "broth", "gravy",
                                  "bolognese", "cooked", "leftovers", "leftover", "takeaway",
                                  "slow cooker", "yoghurt", "yogurt")),
    entry("seeds-grow", (("seed", "seeds"), ("grow", "germinate", "sprout", "sprouting")),
          "A seed waits until it has water, warmth and oxygen, then its stored food fuels the "
          "first root and shoot. Once the shoot reaches light, the plant starts making its own "
          "food by photosynthesis, so the seed's reserves matter less.",
          # money's startup-funding has the bare business word "seed", and a seed in the ground
          # is this answer; a seed round or a seed business stays with the money entry.
          avoid=("business", "businesses", "company", "companies", "startup", "start up",
                 "startups", "funding", "fund", "investor", "investors", "invest", "raise",
                 "raising", "venture", "capital", "money", "round", "loan",
                 # a lawn or a bed sown from seed is the sowing job, not what a seed does:
                 # "how do i grow a lawn from seed" was reaching this answer in one sentence
                 "lawn", "grass", "turf", "sow", "sowing", "sowed", "seed tray", "seedling"),
          bias=1),
    entry("green-plants", (("plant", "plants", "grass", "leaves"), ("green", "colour", "color",
                                                                     "why")),
          "Leaves look green because chlorophyll, the pigment that captures sunlight for "
          "photosynthesis, reflects green light and absorbs the reds and blues. In autumn the "
          "chlorophyll breaks down and the yellow and orange pigments underneath show through.",
          # Not PESTS_AND_CARE as a whole: it carries "leaf" and "houseplant", and "leaves are
          # green because" is exactly this answer. The care words it needs are listed out. An
          # autumn leaf turning and a cat eating grass are not the question either.
          avoid=GRAZERS + ("slug", "slugs", "snail", "snails", "aphid", "aphids", "caterpillar",
                           "caterpillars", "pest", "pests", "bug", "bugs", "insect", "insects",
                           "dying", "dead", "droop", "drooping", "wilt", "wilted", "repot",
                           "fertiliser", "fertilizer", "prune", "lawn", "weed", "weeds",
                           "look after", "care for", "water my", "how often", "houseplant",
                           "houseplants",
                           "autumn", "fall", "winter", "drop", "dropping", "fallen",
                           # A planting question that happens to say green is not the pigment
                           # question: "can i plant bulbs in the green" is the bulb window, and
                           # the leaf answer was winning it on a rarity tie.
                           "bulb", "bulbs", "sow", "sowing", "plant out", "plant bulbs",
                           "planting bulbs",
                           "when to plant", "in the green",
                           # not bare "planting": its forms include "plants", so it turned
                           # every plant question down, "why are plants green" included.
                           # An instruction to plant something green is still a garden
                           # question, so the planting shapes are listed out.
                           "plant a green",
                           "when do i plant", "when should i plant", "how do i plant",
                           "where do i plant", "green manure", "green roof", "green wall",
                           "green beans", "green fingers",
                           # why leaves are green is a why-question: every lawn and every border
                           # asked as a job ("how do i get my grass green") was answered with
                           # chlorophyll, and lawn-care one row away in the garden table has
                           # the answer.
                           "how do i", "how can i", "how to", "how do you", "how should i"),
          ask=("green", "colour", "color")),
    entry("dreams", (("dream", "dreams", "dreaming"), ("why", "what", "mean", "happen", "during")),
          "Dreaming happens mostly in REM sleep, when the brain is nearly as active as when "
          "awake. Scientists think it helps sort memories and practise threats and feelings; "
          "there is no good evidence that dreams predict the future.",
          # A line that tells a dream is the dream, not the explanation of REM sleep: "i had a
          # dream my mother died" was answered with "Dreaming happens mostly in REM sleep" - true,
          # and no answer to the person in front of you. The dreams module has the scene; this
          # entry keeps the questions about dreams in general ("why do i dream", "why do we dream").
          avoid=("job", "career", "goal", "house", "holiday", "career",
                 "i dreamt", "i dreamed", "i had a dream", "i had a nightmare", "nightmare",
                 "nightmares", "last night", "dream about", "dreamt about", "dreamed about",
                 "dreaming about", "dream of", "dreamt of", "dreamed of",
                 "keep dreaming", "keeps dreaming", "kept dreaming", "still dreaming")),
    entry("yawn", ("yawn", ("why", "contagious", "happen", "cause", "tired")),
          "A yawn stretches the jaw and takes a deep breath, and it seems to help cool the brain "
          "and shift gears between waking and sleep. Yawning is contagious because seeing or "
          "hearing one triggers the same response, more so in people you are close to."),
# A line that wants them gone wants the remedy first, and a line that asks why wants the
    # explanation first, so the two are separate answers rather than one reply with the
    # definition in front of the thing asked for.
    entry("hiccups", (("hiccup", "hiccups"),
                      ("stop", "stopped", "stops", "cure", "cured", "get rid", "rid",
                       "what can i do", "what should i do", "how do i get", "wont stop",
                       "won't stop", "wont go", "won't go", "home remedy", "remedy",
                       "remedies", "fast", "quickly", "hold my breath", "help",
                       "have hiccups", "got hiccups", "how long", "last", "lasts")),
          # a hiccup line that names a baby is still a hiccup line, and the birth-registration
          # card is one word of rarity away from taking it
          _hiccups_remedy, bias=1),
    # A parent's line has no remedy verb in it - "hiccups in my newborn", "my baby has hiccups" -
    # so the remedy above passes on it, and the baby words have to carry the answer on their own.
    entry("hiccups-baby", (_BABY_WORDS, ("hiccup", "hiccups", "hiccupping", "hiccupped")),
          HICCUPS_BABY),
    entry("hiccups-why", (("hiccup", "hiccups"),
                          ("why", "get", "cause", "causes", "happen", "what are") + ASK_ABOUT),
          "A hiccup is a sudden spasm of the diaphragm followed by your vocal cords snapping shut, "
          "which makes the 'hic' sound. It usually happens after a big meal, a fizzy drink or a "
          "laugh, when the stomach pushes up against the diaphragm, and it is harmless.",
          avoid=("stop", "stopped", "cure", "rid", "remedy", "remedies", "what can i do",
                 "what should i do", "wont stop", "won't stop", "fast", "quickly",
                 "hold my breath", "have hiccups", "got hiccups", "how long", "last",
                 "lasts")),
    entry("goosebumps", (("goosebumps", "goose bumps"), ("why", "get", "cause", "happen")),
          "Cold or strong emotion makes tiny muscles pull your hairs upright, which traps a layer "
          "of air for warmth and made our furry ancestors look bigger. We have kept the reflex "
          "even though we no longer have the fur for it to work."),
    # "what is a scab", "why does a scab itch", "what are tonsils": the everyday definition of
    # something on the body had no row anywhere, so it reached the shrug that says a search will
    # do better. The noun is the key and the ask is a definition ask, so a symptom line that
    # names the same noun with no ask ("my scab is weeping") still goes to triage.
    *[entry(f"body-what-{name}", (words, WHAT_IS_IT + asks), reply, bias=1, avoid=avoid,
            guard=_not_about_itching if name == "scab" else None)
      for name, (words, asks, reply, avoid) in BODY_WHAT.items()],
    # The itch is the question people actually ask about a scab ("why does my scab itch"), and
    # the definition above leads with what a scab is, so this one leads with the itch.
    entry("body-what-scab-itch", (("scab", "scabs"), ("itch", "itches", "itchy", "itching",
                                                     "pick", "picking", "should i pick")),
          "Itching under a scab is healing: new skin and nerve endings are growing back, and the "
          "histamine in the repairing tissue makes it tingle. Don't pick or scratch it off - it is "
          "the dressing, and taking it off reopens the wound and makes a scar more likely - and a "
          "cool flannel over it or a firm press with a finger settles the itch for a bit.",
          bias=2),
    # "how do i wash my hair properly" is a method question, not a frequency one: the frequency
    # answer below led with "two or three times a week", which does not answer it at all.
    entry("hair-wash-how", (("hair", "hair wash", "shampoo", "scalp"),
                            ("how do i", "how to", "properly", "correctly", "right way",
                             "best way", "step by step", "method", "technique")),
          "Wet the hair, rub a 10p-sized blob of shampoo between your palms and work it into the "
          "scalp with your fingertips, not the ends, for about 30 seconds. Rinse until the water "
          "runs clear, put conditioner on the mid-lengths and ends only, leave it a minute and "
          "rinse cool. Wash the scalp, condition the hair: that is the whole trick.",
          bias=1,
          avoid=("greasy", "oily", "stop", "static", "dandruff", "flaky", "flakes", "falling",
                 "thinning", "bald", "loss", "every day", "daily", "often", "too much",
                 "frizzy", "curl", "curly", "colour", "dye", "bleach", "straighten", "dryer",
                 "hair dryer", "hairdryer", "blow dry", "blowdry", "blow", "tongs", "straighteners",
                 "beard", "dog", "cat", "car", "hands", "face",
                 # how the hair sits is the volume row's and the curl row's question, not the
                 # method's: "how do i get volume in my hair" and "how do i get my hair to lie
                 # flat" were both told to rub a blob of shampoo into the scalp
                 "volume", "flat", "lifeless", "limp", "sticking up", "sticks up",
                 "sticking out", "sticks out", "flyaway", "flyaways", "cowlick",
                 # how fast it grows is not how to wash it: "how to make hair grow faster" was
                 # told to rub a blob of shampoo into the scalp
                 "grow", "grows", "growing", "grew", "faster", "longer", "thicker", "growth",
                 # something stuck in the hair has its own answer: "how do i get gum out of my
                 # hair" was told to rub a blob of shampoo into the scalp
                 "gum", "chewing gum", "lice", "nits", "paint", "glue", "sticky",
                 # likewise brushing it: "how do i detangle my hair" was told how to shampoo
                 "detangle", "detangling", "tangle", "tangles", "tangled", "knot", "knots",
                 "knotty", "matted", "matt", "brush", "brushing", "comb", "combing",
                 # cutting it is the haircut question, not the brush's
                 "cut", "cuts", "cutting", "haircut", "trim", "trimming", "scissors",
                 "clippers", "fringe", "layers",
                 # hair in the plug hole is a blocked drain, and the hair-washing method is no
                 # answer to it: the place in the line says which question this is
                 "plughole", "plug hole", "drain", "drains", "blocked", "unblock", "trap",
                 "bath", "sink", "shower", "showers", "shower tray", "u bend",
                 # a brush full of hair is the brush's own job: "how do i get hair out of my
                 # hairbrush" was told to rub a blob of shampoo into the scalp
                 "hairbrush", "hair brush", "hair brushes",
                 # so is somebody else's hair on a sofa: the shampoo method is for the head
                 "pet hair", "dog hair", "cat hair", "fur", "sofa", "settee", "couch", "carpet",
                 "rug", "floor", "mattress", "upholstery", "clothes", "clothing", "jumper",
                 "shirt", "coat", "vacuum", "hoover")),
    # Curly hair is looked after differently from straight hair, and nothing said so: "how do i
    # look after curly hair" was answered with the haircut card, because "hair" and "how do i"
    # matched there and no card was about curls.
    entry("curly-hair", (("curly hair", "curls", "wavy hair", "curly", "waves", "coils",
                          "coily hair", "3a", "4c"),
                         ("look after", "look after it", "care", "care for", "manage", "routine",
                          "wash", "washing", "dry", "drying", "style", "styling", "advice",
                          "product", "products", "how do i", "best way", "what should i")),
          "Curls want water and conditioner more than shampoo: wash the scalp two or three times a "
          "week, put plenty of conditioner through the lengths and squish it in with your head "
          "upside down, then rinse it out cool. Dry by scrunching with a cotton T-shirt rather "
          "than a towel, add a little leave-in while it is still soaking wet and then leave it "
          "alone until it is dry, because touching it is what makes it frizz. A trim every ten to "
          "twelve weeks keeps the shape.",
          avoid=("cut", "cutting", "haircut", "trim", "trimming", "straighten", "straightening",
                 "relaxer", "relaxing", "perm", "perming", "colour", "dye", "bleach", "grey",
                 "thinning", "bald", "dandruff", "stop", "greasy", "oily", "static", "gum",
                 "plughole", "drain", "sofa", "dog", "cat", "beard",
                 # the coil is a contraceptive in every question that fits one: "how do i get
                 # the coil fitted" was getting the curl routine
                 "iud", "fitted", "fitting", "contraception", "contraceptive", "hormonal",
                 "gynae", "the coil", "copper coil",
                 # "coils" is in this row's names and "coil" is one letter from it, so
                 # "how do i coil a cable properly" was getting the curl routine
                 "cable", "cables", "wire", "wires", "charger", "lead", "headphones",
                 # and the other everyday coil is the contraceptive one: "how do i get the coil
                 # fitted" was answered with the hair routine. The senses are named rather than
                 # the word, because "coils" in a hair line is this row's own subject.
                 "coil fitted", "the coil", "copper coil", "coil in", "coil out", "coil removed",
                 "contraception", "contraceptive", "iud", "intrauterine", "mirena", "implant",
                 "period", "periods", "pregnant")),

    entry("hair-wash", (("hair", "hair wash", "washing my hair", "shampoo", "shampooing"),
                        ("how often", "often", "should", "wash", "washing", "every day", "daily",
                         "too much", "greasy", "oily", "fine")),
          "Two or three times a week suits most people: washing more often strips the oil the scalp "
          "needs, and washing less leaves it greasy. Very oily hair can take a daily wash, and dry "
          "or curly hair does better every three or four days with conditioner on the ends. If your "
          "scalp itches or flakes, use a shampoo for that rather than washing more.",
          ask=("how often", "often", "should", "wash", "daily", "every day", "too much"),
          # Hair loss, thinning and a flaky scalp are their own worries and their own answers; the
          # washing frequency is not advice for any of them.
          avoid=("falling out", "falls out", "fall out", "falling", "thinning", "hair loss",
                 "losing my hair", "lose my hair", "going bald", "bald", "balding", "baldness",
                 "patchy", "alopecia", "flakes", "flaky",
                 # a tangle is the brush's question: "how do i detangle my hair" was told how to
                 # wash it, which is not what was asked
                 "detangle", "detangling", "tangle", "tangles", "tangled", "knot", "knots",
                 "knotty", "matted",
                 # so is washing the brush itself: "how often should i wash my hair brush" was
                 # told how often to wash the hair on your head
                 "hair brush", "hairbrush", "brush clean", "wash my brush", "clean my brush",
                 "washing my brush",
                 # and a cut is the haircut question: "should i trim my hair" was the wash
                 # frequency
                 "cut", "cuts", "cutting", "haircut", "trim", "trimming")),
    # Brushing the hair had no answer of its own: "how often should i brush my hair" was cleaning
    # the hairbrush, then two minutes of fluoride toothpaste, and "is it bad to brush wet hair" was
    # a shrug. The brush is the subject and the hair is the object, and the two questions differ.
    # Choosing a cut is not how often to have one, and the bot had nothing for it: "what should i
    # ask for at the hairdresser" and "i want a change of hairstyle, what should i get" both
    # reached "I don't know enough to answer that honestly", and "what haircut should i ask for"
    # was answered with the six-to-eight-weeks rule, which is a different question. A cut you want
    # to be different is a question about what to say in the chair.
    entry("hair-ask-for",
          (("haircut", "hair cut", "cut my hair", "cutting my hair", "hair", "hair style",
            "hairstyle", "fringe", "bangs", "layers", "trim", "hairdresser", "hairdressers",
            "salon", "barber", "stylist"),
           ("what should i ask for", "what do i ask for", "what to ask for", "what shall i ask for",
            "what should i get", "what should i do with", "what do i do with", "which cut",
            "which haircut", "change", "changed", "different", "new style", "new look",
            "suits me", "suit me", "look good", "looks good", "interview", "new job",
            "grown out", "growing out", "bored of",
            # one word each, because the thing asked for sits inside the frame: "what haircut
            # should i ask for" has no phrase of this row's unbroken
            "ask", "asking", "get", "want", "should", "style")),
          ("Take in three photos of cuts on hair like yours - same thickness and wave, not a "
           "different length - and ask for the nearest thing to one of them, because a photo says "
           "more than any name for a cut. Then say what you hate about it now: too flat on top, "
           "too heavy at the sides, frizzy ends. Ask for a dry cut if yours is curly, and if it is "
           "a big change have it two weeks before the interview or the wedding, not the day "
           "before, so it has time to settle."),
          ask=("ask", "get", "should", "want", "change", "changed", "suits", "suit", "interview",
               "job", "style", "look", "different"),
          # the frequency, the colour, doing it at home and every hair fault have their own cards
          avoid=("how often", "how long", "grow", "grows", "growing", "grew", "faster", "thicker",
                 "at home", "myself", "cut it myself", "cutting it myself", "clippers",
                 "grey", "gray", "colour", "color", "dye", "dyed", "dyeing", "bleach",
                 "highlights", "regrowth", "wash", "washing", "shampoo", "conditioner",
                 "dandruff", "frizz", "frizzy", "static", "greasy", "oily", "falling out",
                 "thinning", "hair loss", "bald", "my dog", "my cat", "dog", "cat",
                 "children", "child", "toddler", "baby", "beard")),

    entry("hair-brush",
          (("hair", "my hair", "brush my hair", "brushing my hair", "brushing hair",
            "hair brush", "comb", "combing"),
           ("brush", "brushing", "how often", "often", "should", "wet", "every day", "daily",
            "tangles", "tangled", "knots", "detangle", "100 strokes", "hundred strokes")),
          "Once or twice a day is plenty for most hair: start at the ends, work up towards the "
          "scalp in small sections, and use a wide-tooth comb on wet hair, because wet hair "
          "stretches and snaps where dry hair gives. The 100 strokes idea is a myth, since that "
          "much brushing only roughens the outside of the hair, and a comb through conditioner in "
          "the shower is what actually gets tangles out.",
          ask=("how", "often", "should", "is it", "why"),
          avoid=("hairbrush", "hair brush", "clean", "cleaning", "wash the brush", "dog", "cat",
                 # a wet head at night is the wet-hair row: "is it bad to sleep with wet hair"
                 # was answered with how often to brush it
                 "catch a cold", "make me ill",
                 # a colour, a dye job and its fading are the hair-colour rows in clothing:
                 # "how often should i colour my hair" was answered with how often to brush it
                 "colour", "color", "dye", "dyed", "dyeing", "bleach", "bleached", "fade",
                 "fading", "highlights", "roots", "regrowth", "tint",
                 "teeth", "tooth", "toothbrush", "beard", "dandruff", "flakes", "falling out",
                 "thinning", "bald", "wig", "dreadlocks", "curly", "frizzy", "straighten",
                 "cut", "cuts", "cutting", "haircut", "trim", "trimming", "scissors",
                 "clippers", "fringe", "layers")),
    # A wet head at night is not a brushing question and not a cold: "is it bad to sleep with wet
    # hair" got how often to wash it, and "will i catch a cold if i sleep with wet hair" was a
    # search hedge. The honest answer is the whole answer - it does not make you ill, and it does
    # snap the hair - so it is written out rather than left to a shrug.
    entry("wet-hair-at-night",
          (("wet hair", "hair wet", "wet head", "damp hair", "hair still wet", "dry my hair",
            "wet hair before bed", "with it wet", "bed with it wet",
            "to bed with it"),
           ("sleep", "sleeping", "slept", "bed", "night", "bad", "ill", "cold", "catch",
            "catch a cold", "catch a chill", "before bed", "should i")),
          "No: wet hair does not make you ill. A cold comes from a virus, and being damp or cold "
          "only nudges down what your nose fights it with, so nobody catches one from a wet head. "
          "What a wet head does do is break the hair, because wet hair stretches and snaps where "
          "dry hair gives, and a damp pillow is a night of rubbing. Towel it until it stops "
          "dripping, do not rub hard, and a loose braid or a silk-ish pillowcase is enough if you "
          "would rather not dry it properly. Dry it if you are going out into the cold with it, "
          "for comfort, not for the cold.",
          # brushing, cutting and washing the hair are their own rows, and a shower or a hairdryer
          # is a different question again
          avoid=("brush", "brushing", "comb", "cut", "trim", "haircut", "dye", "colour", "color",
                 "how often", "wash my hair", "washing my hair", "shampoo my", "hair wash",
                 "shampoo", "conditioner", "dryer", "hairdryer", "straighten",
                 "curly", "frizz", "dandruff", "flakes", "thin", "thinning", "bald", "beard"),
          bias=2),
    # Washing yourself had no card of its own: "how do i wash myself" got the laundry lesson, and
    # once the laundry row stands down for a part of a person the line was left to a shrug. The
    # question is the same for every part, so one row answers all of them and the parts that do
    # have their own rows - the hair, the face, the hands - stand it down with their own words.
    entry("wash-a-body",
          (("wash myself", "wash my body", "clean myself", "wash properly", "wash all over",
            "wash my back", "wash my legs", "wash my feet", "wash my arms", "wash my chest",
            "wash my neck", "shower properly", "wash under my arms", "how to wash"),
           ("how", "should", "do i", "often", "properly", "best", "good")),
          "Stand in a warm shower - warm enough to be comfortable, not hot enough to redden the "
          "skin - and work from the top down: hair if you are washing it, then the face, then the "
          "places that hold sweat, which are under the arms, under the breasts, the groin and "
          "between the toes. Plain soap or shower gel on your hands, a flannel or a soft cloth is "
          "all it needs, and a rinse of everything afterwards. Dry the folds properly rather than "
          "rubbing, and a wash of the face, hands, feet and under the arms is enough on the days "
          "in between a full shower.",
          ask=("how", "what", "should", "can", "is it", "do i"),
          # the hair, the face and the hands are their own cards, and a machine, a pet, a child
          # or a load of washing is a different question again
          avoid=("hair", "face", "hands", "car", "dog", "cat", "baby", "toddler", "child", "kids",
                 "dishes", "windows", "washing machine", "clothes", "laundry", "duvet", "pillow",
                 "trainers", "shoes", "brush", "brushes", "teeth", "bottle"),
          bias=1),
    # Cutting the hair had no answer: "how often should i cut my hair" got the hair-washing
    # frequency, and split ends and how often to shower were both shrugs.
    # A bare "trim" in the key made this the answer to "how do i trim ..." of any kind, so the
    # word only counts next to hair, a fringe or split ends: a hedge, a dog's claws, nails and a
    # beard are not on a six-to-twelve-week schedule, and a shrug is better than a wrong number.
    entry("hair-cut", (("hair", "haircut", "hair cut", "cut my hair", "cutting my hair",
                        "hair style", "fringe", "bangs"),
                       ("how often", "often", "should", "when", "how do i", "how to", "cut",
                        "trim", "haircut", "home", "myself")),
          "Every six to eight weeks for short hair, eight to twelve for long, or whenever the "
          "ends start looking ragged. A trim does not make hair grow faster, but it stops the "
          "split ends travelling up the hair shaft, which is what makes long hair look thin. A "
          "dry cut on wavy or curly hair is more honest about how it falls than a wet one.",
          ask=("how often", "often", "should", "when", "how do i", "how to"),
          # a cut the person wants to be different is `hair-ask-for`'s question, not a schedule
          avoid=("ask for", "ask the", "which cut", "which haircut", "new style", "new look",
                 "change of hairstyle", "different hairstyle",
                 "cut myself", "cutting myself", "burn", "scalp", "scissors in", "dandruff",
                 # booking one is a booking question, not a how-often one: "how do i book a
                 # haircut" was answered with the six-to-eight-weeks rule
                 "book", "booking", "appointment", "reserve", "a slot",
                 # a colour, a dye job and its fading are the hair-colour rows in clothing:
                 # "how often should i colour my hair" was answered with how often to brush it
                 "grey", "color", "colour", "dye", "dyed", "dyeing", "bleach", "bleached",
                 "shampoo", "wash", "washing", "fade", "fading", "highlights", "regrowth",
                 "my dog", "my cat", "children", "my child", "my son", "my daughter", "babys",
                 # every other hair fault has its own answer, and "how do i ... my hair" is the
                 # shape they all use: a static or greasy line is not a haircut question
                 # how to do it yourself is a technique (hair-cut-yourself) and how fast it grows is
                 # not a cutting schedule: "how do i trim my fringe" and "how to make hair grow
                 # faster" are each their own row now
                 "own hair", "my own hair", "cut it myself", "at home", "haircut at home",
                 "grow", "grows", "growing", "grew", "growth", "faster", "longer", "thicker",
                 "static", "frizz", "frizzy", "flyaway", "flyaways", "greasy", "oily", "flakes",
                 "flaky", "falling out", "thinning", "bald", "tangles", "tangled", "knots",
                 "straighten", "straightener", "curling", "tongs", "dryer", "blow dry",
                 # how the hair sits: static, volume, flat and curly questions have their own rows
                 "flat", "lifeless", "limp", "volume", "curly", "curls", "wavy", "sticking up",
                 "sticks up", "rain", "raining", "humid", "humidity",
                 "gum", "chewing gum", "stuck", "glue", "lice", "nits", "sap", "wax",
                 # a beard, a moustache and eyebrows are trimmed far more often than head hair,
                 # so the six-to-twelve-weeks schedule is the wrong number for them and they are
                 # a shrug on main, which is better than a confident wrong answer
                 "beard", "beards", "moustache", "mustache", "eyebrows", "eyebrow",
                 "nose hair", "ear hair", "pubic", "nails", "nail", "toenails", "cuticles",
                 "hedge", "hedges", "lawn", "bush", "bushes", "shrub", "claws", "wick",
                 "video", "videos",
                 # breakage is how hair is handled day to day, not how often it is cut
                 "breakage", "breaking", "snapping", "snaps",
                 # hair in a plughole, a sink or a trap is a blocked drain, and "how do i" in
                 # the ask opens this row for it: "how do i get hair out of the sink" was told
                 # every six to eight weeks
                 "plughole", "plug hole", "plugholes", "plug holes", "drain", "drains",
                 "sink", "sinks", "basin", "blocked", "blockage", "unblock", "trap",
                 "u bend", "waste pipe",
                 # `bangs` is in the key and its forms include "bang", so "how do i stop a
                 # shutter banging" was told to cut it every six to eight weeks. The thing that
                 # bangs is what says which job the line is, and none of these is a haircut.
                 "door", "doors", "gate", "gates", "shutter", "shutters", "window", "windows",
                 "chimney", "chimneys", "blind", "blinds", "fence", "fences", "panel", "panels",
                 "radiator", "radiators", "pipe", "pipes", "loo", "toilet", "car", "van",
                 "cupboard", "drawer", "drawers", "shed", "garage", "letterbox", "bin",
                 # the other half of the same trap: the thing that bangs is often named in the
                 # turn before ("my boiler is making a noise" / "its a banging sound when the
                 # hot water comes on"), so the line itself holds no noun at all and the list
                 # above cannot catch it. A line about a noise is not a haircut, whether or not
                 # it says what is making the noise. The bare word "banging" cannot go in this
                 # list - it shares the stem "bang" with the row's own key word "bangs", and
                 # the list would take the row down for "how often should i cut my bangs" -
                 # so the verb's shape is a phrase and the noise nouns are plain words.
                 "banging sound", "banging noise", "banging when", "is banging", "was banging",
                 "keeps banging", "bangs when", "bangs at", "bangs on",
                 "sound", "sounds", "noise", "noises", "knocking", "rattling", "clanking",
                 "humming", "whistling", "gurgling") + _HAIR_NOT_ON_A_HEAD + _SOMETHING_IN_THE_HAIR),
    entry("hair-split-ends", (("split ends", "split end", "ends", "hair"),
                              ("split", "ends", "stop", "fix", "get rid", "why", "splitting",
                               "frizzy", "dry", "damaged", "trim")),
          "Split ends cannot be repaired, so a 1cm trim is the only fix: then keep them tidy with "
          "conditioner on the mid-lengths and ends, a wide-tooth comb on wet hair and a towel "
          "squeezed rather than rubbed. Heat styling and a tight band in the same spot are what "
          "split them again fastest.",
          avoid=("washing", "shampoo", "greasy", "falling", "thinning", "dandruff", "matted",
                 "detangle", "knotty", "dog", "cat",
                 # hair wrecked by bleach, dye or a perm is its own advice (clothing's
                 # hair-colour-damaged), and "my hair is damaged from bleach" was reaching
                 # the split-ends card, which only knows about the last centimetre
                 "bleach", "bleached", "dye", "dyed", "perming", "perm", "relaxer",
                 # a trim of the nose or ear hair is a shrug, which beats the split-ends answer
                 "nose hair", "ear hair", "eyebrows", "eyebrow", "beard", "moustache",
                 # heat and a brush are how it is dried and styled, not why the ends split
                 "blow dry", "blowdry", "hair dryer", "hairdryer", "curlers", "tongs",
                 "straighteners", "straighten",
                 # nor is a question about how the hair sits a question about its ends: static,
                 # flat, volume and curls each have a row of their own in clothing.py, and this
                 # row was taking "how do i get rid of static in my hair" because "hair" plus
                 # "get rid" scored higher than the static row's "static" plus "hair"
                 "static", "static electricity", "flyaway", "flyaways", "flat", "volume",
                 "lifeless", "limp", "curly", "curls", "wavy", "sticking up", "sticks up")
                 + _HAIR_NOT_ON_A_HEAD
                 + _SOMETHING_IN_THE_HAIR),
    # Two everyday hair questions that had no card of their own. "how do i cut my own hair" and
    # "how do i trim my fringe" were the baby's first haircut ("cut it when you are ready, whether
    # that is four months or two years"), and "how to make hair grow faster" was told how to wash
    # it. Cutting it yourself is a technique, so it is its own row, and the row above it is the
    # "how often should I get it cut" question.
    entry("hair-cut-yourself",
          (("fringe", "bangs", "own hair", "my own hair", "cut it myself", "haircut at home",
            "cut my hair at home", "trim it myself", "blunt cut", "layers"),
           ("cut", "cutting", "trim", "trimming", "myself", "how do i", "how to", "home",
            "at home", "best way", "evenly", "straight")),
          "Cut dry hair, so you can see where it actually falls, and take less off than you think: "
          "small snips across the width, not one line, because hair springs up once it dries. For a "
          "fringe, comb a thin section down flat, hold it between two fingers and cut just under "
          "them, checking both sides sit level with the eyebrow. For length, part it down the "
          "middle, bring both sides forward under the chin and cut them together so they match. "
          "Sharp hairdressing scissors, about fifteen pounds, give a far cleaner line than kitchen "
          "ones.",
          ask=("how do i", "how to", "how can i", "myself", "at home", "trim", "cut"),
          # the fringe is in the schedule row's key too, and for "how often should i trim my
          # fringe" the schedule is the answer, so the technique wins only on the tie
          bias=1,
          # how often is the schedule row above, not this one: "how often should i trim my fringe"
          avoid=("how often", "how frequently", "how regularly", "every few weeks", "how long between",
                 "beard", "beards", "moustache", "mustache", "eyebrows", "eyebrow", "nose hair",
                 "ear hair", "pubic", "toenails", "nails", "nail", "cuticles", "hedge", "hedges",
                 "lawn", "bush", "bushes", "shrub", "dog", "cat", "puppy", "kitten", "horse",
                 "baby", "babys", "babies", "newborn", "toddler", "my son", "my daughter",
                 "my child", "my kid", "children", "child",
                 # a colour, a perm or a blow dry is not a cut, and a plughole is not a head
                 "dye", "colour", "color", "bleach", "perm", "perming", "highlights", "blow dry",
                 "hair dryer", "hairdryer", "straighteners", "curlers", "tongs", "plughole",
                 "drain", "sink", "blocked",
                 # `bangs` is a word of the key and its forms include "bang", so a loo seat, a
                 # shutter or a chimney that bangs was told how to cut a fringe. The thing that
                 # bangs says which job the line is; "banging" on its own stays a fringe question.
                 "door", "doors", "gate", "gates", "shutter", "shutters", "window", "windows",
                 "chimney", "chimneys", "blind", "blinds", "fence", "fences", "panel", "panels",
                 "radiator", "radiators", "pipe", "pipes", "loo", "toilet", "car", "van",
                 "cupboard", "drawer", "drawers", "shed", "garage", "letterbox", "bin")),
    entry("hair-grow",
          (("grow", "grows", "growing", "grew", "growth", "longer", "faster", "thicker"),
           ("hair", "my hair", "it", "beard", "nails", "fringe")),
          "Hair grows about 1 to 1.5cm a month, and nothing makes that much faster: the length is "
          "set by your genes and how long each follicle keeps growing before it sheds. What you can "
          "do is stop losing it to breakage - fewer hot washes and straighteners, a wide-tooth comb "
          "on wet hair, a loose band rather than a tight bobble - and keep the ends trimmed every "
          "two or three months so splits do not travel up and make the length look thin. If it is "
          "thinning as well as slow, get iron, ferritin, thyroid and vitamin D checked, because "
          "that is the one cause worth fixing.",
          ask=("how", "grow", "grows", "faster", "longer", "thicker", "why", "what"),
          avoid=("beard", "beards", "moustache", "mustache", "nails", "toenails", "lawn", "grass",
                 "hedge", "hedges", "plant", "plants", "tomato", "tomatoes", "vegetables",
                 "business", "company", "savings", "pension", "money", "dog", "cat", "puppy",
                 "kitten", "baby", "babys", "babies", "newborn", "toddler", "my son",
                 "my daughter", "children", "child", "crystals", "crystal", "mould", "mold",
                 "friendship", "taller", "children grow")),
    entry("shower-often", (("shower", "showers", "showering", "bath", "baths", "bathe"),
                           ("how often", "often", "should", "daily", "every day", "a day",
                            "wash", "washing", "too much", "long")),
          "Two or three times a week is plenty for most adults, with a wash of the face, hands, "
          "feet, under the arms and the groin every day; the rest of the skin can wait. Five to "
          "ten minutes and lukewarm is enough for a whole shower, and long hot ones strip the oils "
          "out of dry skin, so moisturise while it is still damp. Wash more often in hot weather "
          "or after sport, because sweat and smell are what need washing off.",
          avoid=("blocked", "drain", "leak", "mould", "mold", "shower curtain", "shower head",
                 "limescale", "boiler", "bath bomb", "baby", "toddler", "newborn", "my dog",
                 "my cat", "screen", "tray", "grout", "tiles", "thermostat",
                 # Bath is a city in this bot's own travel table, and "is bath worth a day trip"
                 # was answered "Two or three times a week is plenty for most adults". The
                 # travel frames stand this row down; a wash at home never says any of them.
                 "day trip", "day out", "worth visiting", "worth it", "things to do",
                 "what to do", "to do in", "to see", "see in", "sightseeing", "get to",
                 "how long to", "how long does it take", "roman baths", "city", "town",
                 "weekend away", "stay in", "hotel", "travel", "visit",
                 # "should i replace my bath with a shower" is a builder's question, not a
                 # question about how often to wash, and how often to wash is no answer to it
                 "replace", "replacing", "replaced", "swap", "swapping", "swapped",
                 "install a shower", "installing a shower", "fit a shower", "fitting a shower",
                 "fitted a shower", "shower over the bath")),
    entry("grey-hair", (("hair",), ("grey", "gray", "white", "turn", "turning", "going",
                                     "coming out", "why")),
          "Hair gets its colour from melanin, and the cells that make it gradually stop as we "
          "age, so new hairs grow in without pigment. Genetics decides when that starts, and "
          "stress can speed it up but does not turn a single hair white overnight.",
          # "why is my hair coming out grey" now reaches health's newer hair-loss card through
          # "hair" and "coming out"; the colour is what this question asks, so the colour has to
          # be in the line before this entry claims it.
          ask=("grey", "gray", "white", "silver"), bias=2,
          # a question about losing hair is not a question about its colour, and the grey that
          # someone wants covered, tinted or blended is the dye job's question rather than this
          # one: "how do i cover my grey roots" was answered with the facts about melanin
          avoid=("loss", "lose", "losing", "fall", "falling", "fell", "bald", "balding",
                 "thinning", "thin", "shed", "shedding", "patch", "patches",
                 "roots", "regrowth", "cover", "dye", "dyed", "tint", "colour it",
                 "color it", "get rid", "rid of", "hide", "conceal", "blend")),
    # The word "hair" is not always said: "im going grey", "im going grey at 30", "my beard has
    # gone grey" and "my husband is going grey" are all the colour question, and the only card that
    # claimed them was the safety one for a colour change, which told a person going grey to ring
    # 999. That card now stands down for a hair word and for a grey that is nobody's body part; this
    # is the card it hands those lines to. The body parts are the lines where a grey really is a
    # shut-down - lips, face, gums, fingertips - and they keep the emergency card, so none of them
    # may be answered with melanin.
    entry("gone-grey", (("going", "gone", "goes", "turning", "turned", "turn"), ("grey", "gray")),
          "Hair gets its colour from melanin, and the cells that make it gradually stop as we "
          "age, so new hairs grow in without pigment. Genetics decides when that starts, and "
          "stress can speed it up but does not turn a single hair white overnight.",
          ask=("grey", "gray"), bias=2, slips=("grey", "gray"),
          avoid=("lips", "lip", "face", "facial", "skin", "gums", "gum", "fingertips",
                 "fingertip", "fingers", "finger", "toes", "toe", "hands", "hand", "feet",
                 "foot", "clammy", "sweaty", "passed out", "pass out", "faint", "fainted",
                 "unconscious", "unresponsive", "floppy", "limp", "breathing", "breathe",
                 "ambulance", "999", "911", "nails", "nail", "tongue", "teeth", "eyes",
                 "dog", "dogs", "cat", "cats", "puppy", "kitten", "horse", "pony", "pet",
                 "paint", "wall", "walls", "ceiling", "sky", "cloud", "clouds", "weather",
                 "car", "cars", "hair dye", "roots", "dye", "dyed", "tint", "cover",
                 "colour it", "color it", "hide", "conceal", "blend", "wardrobe", "curtains",
                 "washing", "laundry", "shirt", "shirts", "socks", "fabric", "wool",
                 # A colour that has gone out of a garment is a wash question, and the fabric is
                 # what says so: "my old jeans have gone grey" and "my black jeans have gone grey"
                 # were the laundry card on main ("Wash dark things inside out, in cold water")
                 # and became "Hair gets its colour from melanin" once this row existed. The whole
                 # fabric family stands it down, not just a shirt.
                 "jeans", "trousers", "denim", "top", "tops", "jumper", "jumpers", "cardigan",
                 "hoodie", "dress", "dresses", "skirt", "coat", "jacket", "bedding", "sheets",
                 "towels", "towel", "wash", "washed", "wash it", "faded", "fading", "bleach",
                 "bleached", "faded black", "black clothes", "dark clothes")),
    entry("blood-red", (("blood",), ("red", "why", "colour", "color")),
          "Blood is red because of haemoglobin, the iron-containing protein in red cells that "
          "carries oxygen. Bright red blood is rich in oxygen; darker blood has given its oxygen "
          "to the body."),
    # not "how": "how long does X keep in the fridge" is a food question, not this one
    entry("fridge", (("fridge", "refrigerator", "freezer"), ("work", "works", "cold", "why",
                                                              "cool")),
          "A fridge moves heat out of the inside and dumps it at the back. A pump compresses a "
          "refrigerant gas, which releases heat, then lets it expand inside the fridge, where it "
          "absorbs heat and cools the air.",
          avoid=("smell", "smells", "smelly", "stink", "stinks", "odour", "noise", "noisy", "hum",
                 "humming", "rattl", "leak", "leaking", "frost", "frosting", "broken", "repair",
                 "keep", "keeping", "cooked", "raw", "store", "stored", "storage", "freeze",
                 "freezer", "days", "long")),
    entry("birds-fly", (("bird", "birds"), ("fly", "flying", "wing", "wings")),
          "A bird's wing is curved on top, so air moving over it travels faster and presses less "
          "than the air underneath; the difference lifts the bird. Flapping provides thrust, and "
          "light, hollow bones keep the whole body easy to carry.",
          avoid=("broken", "bleeding", "hurt", "injury", "injured", "vet", "sick", "clip",
                 "clipping", "pluck", "plucking", "feather", "feathers", "cage", "nest", "nests",
                 "roof", "eaves", "pet", "parrot", "budgie", "aviary", "chicken", "chickens",
                 "eat", "feed", "seed", "south", "migrate", "migrating", "migration", "winter",
                 "window", "windows", "glass")),
    entry("antibiotics", (("antibiotic", "antibiotics"), ("work", "works", "what", "how", "do")),
          "Antibiotics kill bacteria or stop them growing, usually by attacking something "
          "bacterial cells have and ours do not, such as their cell walls. They do nothing for "
          "colds and flu, which are viruses, and using them when they are not needed helps "
          "resistant bacteria spread.",
          # A cold or flu question is the specific `antibiotics-cold` entry: this one is the
          # general "how do they work", and it was swallowing "do antibiotics work on colds".
          avoid=("pill", "contraception", "contraceptive", "pregnant", "alcohol", "drinking",
                 "drunk", "missed", "dose", "side effect", "side effects",
                 "cold", "colds", "flu", "virus", "viral")),
    entry("plant-up", (("plant", "plants", "seedling", "seedlings", "roots", "shoots"),
                       ("gravity", "which way", "upside down", "up from down", "grow up",
                        "grows up", "growing up", "grow down", "grows down", "growing down",
                        "upwards", "downwards")),
          "Plants sense gravity using tiny starch grains inside their cells: shoots grow away "
          "from gravity and roots grow towards it. They also bend towards light, which is why a "
          "seedling on a windowsill leans that way.",
          avoid=("bulb", "bulbs", "potato", "potatoes", "tulip", "tulips", "daffodil",
                 "daffodils", "onion", "onions", "garlic", "seed", "seeds", "sow", "sowing",
                 "depth", "deep", "spacing", "compost", "soil", "pot", "pots")),
    entry("climate-change", (("climate change", "global warming"), ("what", "why", "cause",
                                                                      "causes", "happen")),
          "Burning coal, oil and gas releases carbon dioxide, which traps heat in the atmosphere "
          "instead of letting it escape to space. That extra heat raises average temperatures, "
          "melts ice and makes extreme weather more likely; the science is settled, though "
          "predicting any one storm is not."),

    # --- the sky and space, asked the way people ask it --------------------
    entry("sun-yellow", (("sun",), ("yellow", "white", "colour", "color")),
          "The Sun sends out every colour mixed together, so from space it looks white; through "
          "our air the blue is scattered away and what reaches you looks yellow-white. Low in the "
          "sky it looks orange because the light crosses even more air on the way in.",
          ask=("why", "what", "how", "is"),
          bias=2),
    entry("sun-age", (("sun",), ("old", "age")),
          "The Sun is about 4.6 billion years old, roughly halfway through its life, and it has "
          "another 5 billion years or so before it swells into a red giant. The Earth formed at "
          "about the same time, from the same cloud of dust and gas.",
          ask=("how", "old", "age")),
    entry("stars-night", (("star", "stars"), ("night", "dark", "day", "daytime")),
          "The stars are there in the daytime too: the sun lights up the air above you so "
          "brightly that their faint light is drowned out. Away from city lights, and out of the "
          "sun's glare, thousands more of them come into view.",
          ask=("why", "only", "see", "visible", "what")),
    entry("moon-horizon", (("moon",), ("big", "bigger", "large", "huge", "horizon", "size",
                                        "illusion")),
          "The Moon looks bigger near the horizon because of an illusion in how your brain judges "
          "it against the landscape; photograph it and it comes out the same size as when it is "
          "high overhead. It also looks dimmer down there, not brighter, because its light is "
          "crossing more air.",
          ask=("why", "look", "looks", "seems", "appear", "appears"),
          bias=2),
    entry("mountain-cold", (("mountain", "mountains", "altitude", "hill", "summit"),
                            ("cold", "colder", "temperature", "freezing")),
          "Air thins and expands as it rises, so it holds less heat, and the ground gives its "
          "warmth up to the cold sky faster than thin air can hold it: the temperature drops about "
          "6.5C for every kilometre you climb. The sunshine up high can still feel fierce while "
          "the air around you stays cold.",
          ask=("why", "colder", "cold")),
    entry("earth-age", (("earth", "planet"), ("old", "age", "formed", "born")),
          "The Earth is about 4.54 billion years old, worked out from meteorites and the oldest "
          "rocks. Life got going within the first billion years, and everything humans have done "
          "fits into the last tiny sliver of that time.",
          ask=("how", "old", "age", "when")),
    entry("earth-spin", (("earth",), ("spin", "spins", "spinning", "rotate", "rotates",
                                     "rotation")),
          "The Earth spins because the cloud of dust and gas it formed from was already turning, "
          "and nothing has braked it much in 4.5 billion years. The Moon's tides are slowly "
          "slowing it, so the day grows about a second longer every 50,000 years or so.",
          ask=("why", "does", "what", "how")),
    entry("fish-breathe", (("fish", "fishes"), ("breathe", "breathing", "underwater", "gills",
                                                 "water")),
          "Fish take oxygen out of the water with gills: water flows in at the mouth and over thin, "
          "blood-rich filaments, where oxygen passes into the blood and carbon dioxide passes out. "
          "Out of water the filaments collapse and stick together, so the fish suffocates even in "
          "air.",
          ask=("how", "why", "do", "does", "what"),
          # a fish breathing is not a "how do i cook fish" question, and cook-a-staple is
          # registered earlier, so this wins the line it plainly names
          bias=2),
    entry("birds-migrate", (("bird", "birds"), ("migrate", "migration", "south", "leave",
                                                 "leaves")),
          "Birds head off in autumn because the insects, worms and berries they live on run out as "
          "the days shorten; the trip costs a lot of energy but beats starving. They find their "
          "way by the sun, the stars, landmarks and the Earth's magnetic field, and many come back "
          "to the same nest site.",
          avoid=("home", "job", "city", "nest", "leaving me"),
          ask=("why", "south", "winter", "when", "do"),
          bias=2),

    # --- the body and everyday science ------------------------------------
    entry("virus-bacteria", (("virus", "viruses", "viral"),
                            ("bacteria", "bacterial", "bacterium", "difference", "vs", "versus")),
          "A virus is a scrap of genetic code in a protein coat that can only multiply inside your "
          "cells; bacteria are single living cells that can grow and divide on their own. So "
          "antibiotics kill bacteria but do nothing for a cold or flu, which are viral.",
          ask=("difference", "vs", "versus", "between", "bacteria", "bacterial")),
    entry("virus-what", (("virus", "viruses"),
                         ("what", "mean", "made", "work", "live", "cell", "alive")),
          "A virus is a scrap of genetic code wrapped in a protein coat, and it can only copy "
          "itself inside a living cell. That is why antibiotics do nothing for a cold or flu: "
          "they kill bacteria, which are cells that can grow on their own.",
          ask=("what", "mean", "made", "work", "live", "cell", "alive"),
          avoid=("bacteria", "bacterial", "difference", "vs", "versus", "antibiotic",
                 "computer", "email", "phone")),
    entry("bacteria-what", (("bacteria", "bacterium", "bacterial"),
                            ("what", "mean", "made", "good", "bad", "work", "live")),
          "Bacteria are single-celled living things, so small that millions fit on a pinhead. "
          "Most are harmless or useful, from the ones in yoghurt to the ones in your gut, and a "
          "few cause illness; unlike a virus, a bacterium can grow and divide on its own.",
          ask=("what", "mean", "made", "good", "bad", "work", "live"),
          avoid=("virus", "viral", "difference", "vs", "versus", "antibiotic", "probiotic",
                 "yoghurt", "yogurt", "urine", "uti", "pee", "bladder", "infection")),
    entry("antibiotics-cold", (("antibiotic", "antibiotics", "penicillin"),
                              ("cold", "colds", "flu", "virus", "viral", "sore throat")),
          "Antibiotics do nothing for a cold or flu: those are viruses and antibiotics only kill "
          "bacteria. What actually helps is rest, plenty of fluids, and paracetamol or ibuprofen "
          "for the aches, plus honey in warm water for a cough; see someone if a fever lasts more "
          "than a few days or you are breathless.",
          ask=("cold", "colds", "flu", "virus", "viral", "throat"),
          # "do antibiotics help with a cold" has cold+help, so it ties with the cold-remedy
          # entry; this one names the antibiotic, so it is the answer to the question asked.
          bias=2),
    # "take" is the verb of the medicine question ("what should i take for a cold") and also
    # the verb of a packing question ("what should i take to prague"), so both entries have it
    # and the guard that separates them is travel's avoid list, not this key.
    # "how do i stop a cold", "how do i shake a cold" and "how do i prevent a cold" were all a
    # shrug: the entry only knew the words of the take-and-get-rid question. The verbs of doing
    # something about a cold are the same question, and the preventing half of it has its own
    # answer, so the reply is selected rather than one paragraph for both.
    entry("cold-remedy", (("cold", "colds"), ("help", "helps", "actually", "best", "remedy",
                                              "cure", "better", "shift", "take", "takes",
                                              "taking", "rid",
                                              "stop", "stopping", "shake", "shaking", "fight",
                                              "fighting", "get over", "getting over",
                                              "prevent", "preventing", "ward off", "avoid",
                                              "avoiding", "coming on", "in its tracks",
                                              "dodge", "quickly", "fast",
                                              # "how do i deal with a cold" and "how do i
                                              # treat a cold" are this question in the words
                                              # people use when they do not yet know it is a
                                              # remedy, and "my cold is lingering" is the same
                                              # remedy asked as a complaint
                                              "deal", "dealing", "treat", "treating",
                                              "treatment", "lingering", "still got",
                                              # "how do i look after a cold" is the same
                                              # question in the words people use for a child,
                                              # a partner or themselves, and it was a shrug
                                              "look after", "looking after", "looked after",
                                              "care", "caring", "care for", "caring for",
                                              "nurse", "nursing", "get through",
                                              # "what can i do for a cold" is the same question
                                              # as "how do i shift a cold", and none of its
                                              # words is a remedy word: the ask itself is the
                                              # second key, so the line clears MIN_SCORE.
                                              "what can i do", "what do i do", "can i do",
                                              "anything i can",
                                              # the "should i" and "about" forms of the same
                                              # plain ask are in the key as well as the required
                                              # bucket: the bucket alone clears the fence but not
                                              # the score, so key and bucket take the phrase pair.
                                              "what should i do", "what shall i do",
                                              "should i do about", "do about",
                                              # "cold medicine for adults" and "what is good
                                              # for a cold" named the medicine and the goodness
                                              # and neither verb, so both were a shrug and a
                                              # punt: the thing you buy for a cold is this
                                              # question asked as a noun
                                              "medicine", "medicines", "medication",
                                              "tablets", "tablet", "syrup", "lemsip",
                                              "pharmacy", "chemist", "good for",
                                              "what is good for", "whats good for",
                                              # "how do i keep colds away this winter" is the
                                              # prevention half asked as a keeping, and it was
                                              # the frost card and then a punt
                                              "keep away", "keeping away", "keeps away",
                                              "colds away", "stay well", "keeping well",
                                              "not catch", "fight off")),
          _cold_help,
          # "take" belongs to the medicine question; a cold shower, a cold beer and cold weather
          # are other uses of the same word.
          avoid=("eat", "eating", "food", "left out", "leaving", "shower", "bath", "sauna",
                 "beer", "drink", "shell", "sweat", "sweatshirt", "weather", "sore shoulder",
                 # an appliance that keeps things cold is not an illness, and the fridge
                 # answers were a coin flip away from this one
                 "fridge", "freezer", "frozen", "freezing", "radiator", "draught", "draft",
                 "window", "outside", "tap",
                 # a house that is cold is a heating question, not an illness: "my boiler is
                 # noisy and the heating is cold, what do i do" got the cold remedy paragraph
                 # because "cold" was the whole of what it shared with this row, and the house
                 # words are the same class as "radiator" above
                 "heating", "boiler", "boilers", "thermostat", "central heating", "hot water",
                 "plumbing", "flue", "immersion", "combi", "trv", "no heat", "stone cold",
                 "cold sore", "cold sores", "herpes", "lip", "lips", "blister", "blisters",
                 # cold hands, cold feet and feeling cold all the time are a circulation
                 # question, and the word "stop" is what was carrying them here
                 "hands", "hand", "feet", "foot", "fingers", "fingertips", "toes", "toe",
                 "feeling cold", "always cold", "being cold", "so cold", "too cold",
                 # "deal with" and "treat" are keys now, so the words that share them come
                 # here: a cold caller is a nuisance call and a cold flat is a heating question
                 "call", "calls", "caller", "callers", "calling", "cold call", "cold calls",
                 "flat", "house", "home", "room", "rooms", "bedroom", "kitchen", "office",
                 "shed", "garage", "caravan", "conservatory",
                 # a cold wall, a cold corner or a cold window is where the water lands, which
                 # is the condensation question: "how do i stop condensation on a cold wall"
                 # was answered with rest, fluids and honey in warm water, on "cold" + "stop"
                 "wall", "walls", "ceiling", "ceilings", "corner", "corners",
                 "condensation", "condensing", "damp", "mould", "damp patch",
                 # "how do i stop getting colds all the time" is the repeated-colds question,
                 # not how to shift the one you have: the catch-and-repeat words stand this
                 # entry down so colds-repeated answers it.
                 "keep getting", "keeps getting", "getting colds", "get colds",
                 "catching colds", "catch colds", "one after another", "all the time",
                 "always ill", "always sick", "every winter", "every year",
                 # a cold hand is not a cold: "how do i stop my hands getting cold" is a
                 # circulation question, and this row was answering it with sleep and handwashing
                 "hands getting cold", "hands are cold", "hands get cold", "hands go cold",
                 "hands going cold", "cold hands", "hand is cold", "my hand is cold",
                 "fingers are cold", "fingers getting cold", "fingers go cold",
                 "cold fingers", "feet are cold", "feet get cold", "feet getting cold",
                 "feet go cold", "cold feet", "foot is cold", "toes are cold",
                 "toes get cold", "cold toes", "toes go cold",
                 # a car that is cold is a starting fault, not an illness: "what do i do if my
                 # car wont start in the cold" was answered with rest, fluids and paracetamol.
                 # Anything that names a machine or its parts stands this row down, and the
                 # cars table answers it.
                 "car", "cars", "van", "engine", "battery", "ignition", "starter",
                 "windscreen", "windshield", "diesel", "petrol", "motorbike"),
          ask=("help", "helps", "actually", "best", "remedy", "cure", "better", "shift",
               "take", "takes", "taking", "rid",
               "stop", "stopping", "shake", "shaking", "fight", "fighting", "get over",
               "getting over", "prevent", "preventing", "ward off", "avoid", "avoiding",
               "coming on", "in its tracks", "dodge", "quickly", "fast",
               "deal", "dealing", "treat", "treating", "treatment", "lingering", "still got",
               "look after", "looking after", "looked after", "care", "caring", "care for",
               "caring for", "nurse", "nursing", "get through",
               "what can i do", "what do i do", "can i do", "anything i can",
               # "what should i do about a cold" is the plainest ask of all, and the required
               # bucket had "what can i do" and "what do i do" but not the "should i" and
               # "about" forms, so the shortest question about a cold was a shrug while
               # "what can i do for a cold" - the same question - was answered here.
               "what should i do", "what shall i do", "should i do", "do about",
               "what helps", "anything for",
               "medicine", "medicines", "medication", "tablets", "syrup", "lemsip",
               "pharmacy", "chemist", "good for",
               "keep away", "keeping away", "colds away", "stay well", "keeping well",
               "not catch", "fight off"),
          # "what should i take for a cold" was answered with a packing list, because "take" is
          # the verb of both questions. A cold in the line is the illness, so this entry wins the
          # tie and the travel table keeps the lines that are about a trip.
          # A cold that is food is the leftovers question, not the illness; that stands this row
          # down from a guard rather than from an avoid phrase, because an avoid phrase reads the
          # filled-in reading of a follow-up and would take a line that names no food with it
          # (see `_not_a_food_cold`).
          bias=1, guard=_not_a_food_cold),
    entry("colds-repeated", (("cold", "colds"), ("keep getting", "keeps getting", "get colds",
                                                 "getting colds", "always ill", "always sick",
                                                 "one after another", "cold after cold",
                                                 "so many colds", "colds constantly",
                                                 "constantly ill", "catching colds",
                                                 "catch colds", "cold every", "colds every",
                                                 # the frequency question is the same fact: "how
                                                 # many colds a year is normal" was reaching the
                                                 # nuisance-calls card before this
                                                 "colds a year", "cold a year", "how many colds",
                                                 "colds in a year",
                                                 # and "how often" is how most people ask it:
                                                 # "how often do colds come" was a punt, so these
                                                 # phrases keep the cold word as the gate
                                                 "how often do colds", "how often do you get",
                                                 "how often do i get", "how often do people get",
                                                 "how often should i get", "how often am i")),
          "Most adults catch two to four colds a year and children get more, because hundreds of "
          "different viruses cause them, so one after another is normal. Sleep, handwashing, your "
          "own cup and towel and not smoking all help; if they come much more often than that, or "
          "each one turns into a chest infection, get it checked.",

          # "getting" and "cold" are both in the ask list, so "how do i stop my hands getting
          # cold" was reaching this row: the body part stands it down, because a cold hand is
          # a circulation question and not a virus.
          avoid=("cold sore", "cold sores", "blister", "blisters",
                 "hands getting cold", "hands are cold", "hands get cold", "hands go cold",
                 "hands going cold", "cold hands", "hand is cold", "my hand is cold",
                 "fingers are cold", "fingers getting cold", "fingers go cold",
                 "cold fingers", "feet are cold", "feet get cold", "feet getting cold",
                 "feet go cold", "cold feet", "foot is cold", "toes are cold",
                 "toes get cold", "cold toes", "toes go cold",
                 # a cold call is not a cold either: "i keep getting cold calls" has the same
                 # keep-getting shape as the run of colds, and only the noun tells them apart
                 "cold call", "cold calls", "call", "calls", "caller", "callers", "phone",
                 "phone call", "phone calls"),
          # a flat that is cold is the heating question, not a run of viruses: "my flat gets cold"
          # was being told to wash its hands and sleep more.
          guard=not_the_flat_you_live_in,

          ask=("cold", "colds", "getting", "keep", "ill", "sick", "always"),
          # a run of colds is this fact, not the treating-one-cold card, which ties on rank
          bias=1),
    entry("ageing", (("ageing", "aging", "get older", "getting older", "grow old", "growing old",
                      "old age", "we age", "people age", "humans age", "body age", "we get old",
                      "people get old", "humans get old"),
                     ("why", "how", "cause", "causes", "happen", "happens", "what", "does")),
          "Ageing is the slow build-up of small damage: cells divide less accurately, DNA and "
          "proteins get worn, and the body's repair and energy systems slow down. That makes "
          "illness more likely over time, but sleep, exercise, not smoking and a varied diet all "
          "shift the odds; how fast it happens is only partly fixed by your genes.",
          avoid=("school", "kid", "kids", "child", "children", "nursery", "potty", "start",
                 "at my age", "at your age", "at what age", "learn", "learning", "guitar",
                 "wrinkle", "wrinkles", "wrinkled", "skin", "dog", "dogs", "cat", "cats",
                 "pet", "pets",
                 # the ages are history, not biology: "what was the iron age" was answered with
                 # "Ageing is the slow build-up of small damage". The stem of "ageing" is "age".
                 "iron age", "stone age", "bronze age", "ice age", "dark ages", "middle ages",
                 "age of", "space age", "new age", "nuclear age", "coming of age")),
    entry("sneeze-sun", (("sneeze", "sneezing", "sneezes"),
                        ("sun", "sunlight", "bright", "sunshine")),
          "Bright light sets off a sneeze in about one person in four: the light triggers the same "
          "nerve that starts a sneeze reflex, so looking at the sun or walking out of a dark "
          "cinema does it. It is harmless and tends to run in families.",
          ask=("why", "does", "do", "sun", "light", "bright"),
          bias=2),
    entry("sneeze-why", (("sneeze", "sneezing", "sneezes"),
                        ("why", "makes", "make", "nose", "dust", "pollen", "allergy", "cause",
                         "happen")),
          "A sneeze is your nose clearing itself: dust, pollen or a virus irritates the lining and "
          "the body blasts air out to shift it. The droplets fly several metres, which is why you "
          "catch it in your elbow rather than your hand.",
          ask=("why", "cause", "happen", "what")),
    entry("ears-pop", (("ear", "ears"), ("pop", "pops", "popping", "popped", "plane",
                                          "flight", "pressure")),
          "Ears pop because the air pressure around you changes faster than the pressure inside "
          "your middle ear - in a lift, or in a plane as it climbs. Swallowing, yawning, or holding "
          "your nose and blowing gently pushes it back into balance; a blocked nose from a cold "
          "makes it harder.",
          # a bare report of the popping is the question too: "my ears pop when i swallow" has
          # no why in it, and the pop itself is the ask
          ask=("why", "do", "does", "what", "pop", "pops", "popping", "popped", "pressure"),
          # The pop explains the crackle, not the pain: "my ear popped and now it hurts" is an
          # earache, and the ache row is the one that answers it. Only the words that say the ear
          # hurts, because a pop in a cold or a feverish ear is still a pressure question, and
          # the ache row already stands down on "pressure" and "eustachian".
          avoid=("hurt", "hurts", "hurting", "pain", "painful", "ache", "aches", "aching",
                 "throb", "throbbing", "sore", "tender", "tenderness"),
          bias=2),
    entry("brain-freeze", (("brain freeze", "brainfreeze", "ice cream headache"),
                          ("ice", "cream", "cold", "drink", "drinks", "eat", "eating", "why",
                           "get", "getting", "cause", "causes")),
          "A cold mouthful chills the roof of your mouth and the blood vessels there tighten, then "
          "widen again; that swing is the stabbing headache behind your forehead. Eat more slowly, "
          "or press your tongue to the roof of your mouth to warm it, and it fades in a minute.",
          ask=("why", "get", "gets", "what", "cause"),
          # "brain freeze ... ice cream" is this entry, not the cooking freezer-storage one
          bias=1),
    entry("freckles-why", (("freckle", "freckles"),
                           ("why", "cause", "causes", "happen", "happens", "get", "getting",
                            "what", "appear")),
          "Freckles are little patches of melanin, the pigment that colours skin, made by cells "
          "that respond to sunlight; people with paler skin and certain genes make more of it, "
          "which is why they show up after time in the sun. They are harmless, but a new or "
          "changing spot needs checking, and sunscreen keeps them from darkening.",
          avoid=("rid", "remove", "fade", "laser", "cover", "makeup", "cream", "bleach",
                 "mole", "moles", "changing", "cancer", "check", "checking", "worried",
                 "worry", "baby", "babies", "child", "children", "kid", "kids")),
    entry("deja-vu-why", (("deja vu", "déjà vu", "dejavu"),
                          ("why", "cause", "causes", "happen", "happens", "what", "get", "feels",
                           "feel", "mean")),
          "Deja vu is a brief misfire in memory: the brain takes in a new scene and, for a second, "
          "files it as familiar, often because a similar layout or sound has primed the same "
          "circuits. It is common and harmless, especially when tired; if it comes with a seizure, "
          "a smell or a feeling of losing time, get it checked.",
          avoid=("seizure", "seizures", "epilepsy", "medication", "medicine", "doctor", "gp",
                 "worried", "worry", "dementia")),
    # "everything" is the other half of the everyday line: with "things" out of
    # `study.memorise-faster`, "i keep forgetting things" reaches this entry, and "i keep
    # forgetting everything" is the same question said more strongly. Left out, both fell to a
    # routine "Annoying. Is it the same every time, or does it vary?".
    # The past tense is not here on its own: "lost" is what you say about a job, a person, a
    # wallet and a game, and it made this card the answer to a redundancy. "i lost my job" then
    # "what should i do" got "most forgetting is not a lost file" from a person whose job had
    # just gone. "lose" and "losing" stay, because a habit is said in the present ("i keep losing
    # things", "im losing my memory"), and so do "forget" and "memory", which name what this
    # entry is about.
    # A method question is the same row said the other way round: "how do i remember birthdays"
    # asks for the habit that stops the forgetting, and until now the phrase was nobody's key, so
    # it went to the party planner on "birthdays" and then, once that stood down, to the hedge.
    # The phrases are long on purpose: a bare "remember" would take "how do i remember names",
    # which has a better answer of its own.
    entry("forgetting-why", (("forget", "forgetting", "forgot", "memory", "memories",
                              "lose", "losing",
                              # The generic method asks are deliberately not here: "how do i
                              # remember things" and "how do i remember stuff" are the recall-
                              # while-reading card, and "how do i remember the dates" is the
                              # timeline card, and either is a better answer than this one. Only
                              # the birthday phrases, which had no owner of their own.
                              "remember birthdays", "remembering birthdays",
                              "remember everyones birthdays",
                              "keep track of birthdays", "remember birthdays and", "birthday list",
                              "track of everyones birthdays", "track of everybodys birthdays",
                              "everyones birthdays", "everybodys birthdays",
                              "track of my friends birthdays"),
                             ("why", "cause", "causes", "happen", "happens", "what", "things",
                              "everything", "names", "words", "so")
                             # The words that make a line a method ("how", "way", "tips",
                             # "advice", "keep track") are not on this side either: with BLANK_WORDS
                             # in the first group, a bare "how" in the second made the card the
                             # answer to every follow-up that starts with one. "i want to lose a
                             # stone" then "how long will it take" got the forgetting card instead
                             # of the rate, and `tests/test_a_new_subject_ends_the_carry.py` went
                             # red on main (#10560). The birthday how-to has its own row below,
                             # which is what those words were added for.
                             + BLANK_WORDS),
          _forgetting,
          guard=_an_amount_of_losing,
          avoid=("study", "studied", "studying", "revise", "revising", "revision", "exam",
                 "exams", "learn", "learning", "test", "school", "course", "keys", "key",
                 "password", "passwords", "dementia", "alzheimer", "alzheimers",
                 # someone else's memory ("my mum keeps forgetting things") is a doctor question
                 "mum", "dad", "mother", "father", "grandma", "grandad", "wife", "husband",
                 "worried", "worry", "what did i", "what you said", "remind", "told", "again",
                 "nan", "nana", "granny", "grandmother", "grandfather", "aunt", "uncle", "friend",
                 "partner", "son", "daughter", "brother", "sister", "neighbour",
                 # "i want to remember things better" is a study technique (the reading card
                 # has it) and "he says he just doesnt remember things like that" is somebody
                 # else's memory, which is the doctor question and not the science of one
                 "things better", "remember better", "better at remembering",
                 "he says", "she says", "he just", "she just", "he doesnt", "she doesnt",
                 "he doesn't", "she doesn't", "he cant", "she cant", "he can't", "she can't",
                 # forgetting TO DO something is a habit and a reminder question, not the
                 # memory-science one: "i keep forgetting to drink water" wants a bottle in
                 # sight, and "why do i keep forgetting things" still gets this answer.
                 "to drink", "to eat", "to take", "to feed", "to walk", "to pay", "to call",
                 "to text", "to reply", "to post", "to book", "to bring", "to charge",
                 # "i lost interest in everything i used to enjoy" is the low mood said as a
                 # lost appetite for things, and the science of how memories fade is the wrong
                 # answer to it: the interest words belong to the mood card in health
                 "interest", "interested", "interesting", "enjoy", "enjoyed", "enjoying",
                 "enjoyment", "hobbies", "hobby", "motivation", "motivated", "bothered",
                 "to water", "to tidy", "to clean", "to put", "to send", "to ring",
                 # "thats scary" said about somebody else's forgetting is the person's feeling, and
                 # the chat module's warm line is the answer to a feeling; the science of memory
                 # is not. The words are matched on the line as typed, so they only stand this
                 # card down for a line that is nothing but the feeling.
                 "scary", "scared", "scares", "frightening", "frightened", "terrifying",
                 # A forgetting that is going on now ("lately", "these days", "for months") is the
                 # person's own worry and the card for it is `own-memory-worry`; the mechanism is
                 # the answer to "how does it work" and to nothing else.
                 "lately", "recently", "these days", "nowadays", "for months", "for weeks",
                 "for a while", "all the time", "constantly", "non stop",
                 "terrified", "upsetting", "upsets",
                 # "im so lost" is a feeling, not a question about memory: the science card
                 # answered it with "Most forgetting is not a lost file: new memories fade unless
                 # they are slept on", where "i feel lost" was already heard. Phrases only, and
                 # never the bare "lost" or "lose" - both are in this row's own key, so a bare
                 # word would take the whole answer away from "why do i keep losing things".
                 "so lost", "feel lost", "feeling lost", "felt lost", "completely lost",
                 "totally lost", "bit lost", "little lost", "get lost", "got lost", "lost at",
                 "lost in life", "lost in it", "lost with all", "lost with it", "lost with the",
                 "lost my way", "im lost", "i am lost", "i was lost",
                 # "how can i improve my memory", "how do i improve my memory" and "any tips for
                 # a better memory" are the study method - test yourself, space it out - and
                 # `memorise-faster` in study.py answered them until the method asks ("how",
                 # "tips", "best way") were added here for the birthday how-to. The words that
                 # make it a method belong to that row; the theory is what is left.
                 "improve", "improving", "improvement", "improvements", "sharper", "boost",
                 "technique", "techniques", "better memory", "memory better",
                 "improve my memory", "improve your memory", "memory improve",
                 "memorise", "memorize", "memorising", "memorizing")),
    # The memory card above fences the words for a relative, because "my mum keeps forgetting
    # things" is a question for a doctor and not the science of memory. That fence also stood in
    # the way of "how do i remember my mums birthday", which is the same habit as the plural: the
    # store stands down for the how-to (see memory/recall.KEEPING_TRACK) and this row is what
    # to catch it. So the birthday habit gets its own key, on the birthday and the remembering
    # word together, and it answers with the same `_forgetting` so the two can never drift. The
    # party and the present are the other rows' questions and are fenced out here.
    # The asks here are the method shapes only - "how do i remember", "any tips", "whats the best
    # way". Everything else that mentions a birthday belongs to somebody else: "my wife keeps
    # forgetting my birthday" is how that feels, "i keep forgetting my sisters birthday and she
    # minds" wants the reminder that works, and "my mrs wants a birthday thing, shes 40" is a
    # party. Widening this key to the bare remembering words took all three.
    entry("remember-the-birthdays",
          (("birthday", "birthdays"),
           ("how do i", "how can i", "how could i", "how do you", "how to", "how should i",
            "tips", "tip", "advice", "best way", "any way", "is there a way", "keep track",
            "track of", "a way to", "the trick", "tricks",
            # "birthday reminder ideas" is the same habit asked as a list of ideas, and the
            # party-food card answered it. The word is the phrase, not the bare "remind", which
            # is the store's own line ("remind me about my birthday").
            "reminder ideas", "reminder idea", "reminders for birthdays")),
          _forgetting, bias=1,
          avoid=("party", "parties", "plan", "planned", "planning", "present", "presents",
                 "gift", "gifts", "cake", "cakes", "decorate", "decorations", "host", "hosting",
                 "venue", "invite", "invites", "invitations", "surprise", "theme", "themes",
                 "games", "song", "songs", "dinner", "balloons", "when is", "whens", "what date",
                 "how old", "age", "card", "cards", "message", "wish", "wishes", "happy birthday",
                 "song", "sang", "sing")),
    entry("pruney-fingers", (("finger", "fingers", "fingertip", "fingertips", "toe", "toes",
                              "hand", "hands"),
                             ("pruney", "shrivelled", "shriveled", "shrivel", "prune", "bath",
                              "bathtub", "swim", "swimming", "pool", "soak", "soaking", "water",
                              "wet")),
          "The skin on fingers and toes puckers in water because the outer layer soaks up water "
          "while the nerves underneath tighten tiny blood vessels, which pulls the surface into "
          "ridges; it seems to give a better grip on wet things. It fades within minutes of drying "
          "and is not a sign of getting old.",
          ask=("why", "what", "how", "cause", "happen", "get", "go", "become", "turn"),
          avoid=("cut", "cuts", "hurt", "hurts", "pain", "painful", "swollen", "swelling", "numb",
                 "tingle", "tingling", "rash", "eczema", "arthritis", "infection", "cracked",
                 "age", "old", "ageing", "aging")),
    entry("morning-breath", (("morning breath", "bad breath", "breath smells", "breath stinks",
                              "halitosis"),
                             ("why", "cause", "morning", "get", "what", "how", "stop", "fix")),
          "Morning breath comes from a dry mouth: saliva slows overnight, so bacteria on the "
          "tongue and between the teeth break down food and cells and give off sulphur-smelling "
          "gas. Brush and floss before bed, clean your tongue, drink water, and see a dentist if it "
          "lasts all day, because gum disease is a common cause.",
          avoid=("dog", "dogs", "cat", "cats", "puppy", "kitten", "baby", "babies", "child",
                 "children", "mask", "diabetes", "ketone", "liver", "kidney", "coffee",
                 "garlic", "onion", "onions", "eating", "food", "lunch",
                 # How to raise it with someone is a different question from why it happens:
                 # "how do i tell my friend her breath smells" wants the words to say, and the
                 # friends entries already have those. Only the telling verb stands this entry
                 # down. A person named in the line does not: "my friend says my breath smells,
                 # what causes it" is still the cause question, and standing aside for the bare
                 # word "friend" left it with a hedge where main had this answer.
                 "tell", "tells", "telling", "mention", "raise it", "bring it up",
                 "bring this up", "how do i say", "how should i say")),
    entry("dark-circles", (("dark circles", "bags under my eyes", "bags under the eyes",
                            "puffy eyes", "under eye bags", "dark rings under my eyes"),
                           ("why", "cause", "get", "what", "how", "rid", "help", "always")),
          "The skin under the eyes is thin, so blood vessels and muscle show through more when you "
          "are tired, dehydrated or have a cold; genes, allergies and thinning skin with age make "
          "them darker. Sleep, water and an antihistamine if allergies are behind it help, and a "
          "caffeine eye cream can soften the look for a while.",
          avoid=("concealer", "makeup", "filler", "surgery", "laser", "tattoo", "dog", "cat",
                 "baby", "child", "pregnant", "pregnancy")),
    entry("sleepy-after-eating", (("sleepy after eating", "tired after eating", "sleepy after lunch",
                                   "food coma", "drowsy after eating", "sleepy after a meal",
                                   "tired after lunch"),
                                  ("why", "feel", "get", "always", "what", "cause")),
          "After a big meal, blood flow shifts to the gut and the body clock dips in the early "
          "afternoon, so feeling sleepy is normal, especially with a lot of refined carbs or "
          "alcohol. A smaller lunch, a short walk and daylight help; see a GP if it happens after "
          "every meal with thirst, weight loss or falling asleep mid-conversation.",
          avoid=("baby", "babies", "child", "children", "dog", "cat", "medicine", "tablet",
                 "diabetes", "pregnant", "pregnancy")),
    entry("laughter-why", (("laugh", "laughing", "laughter", "giggle", "giggling"),
                           ("why", "human", "humans", "contagious", "nervous", "funny", "social",
                            "what")),
          "Laughter is mostly social: people laugh far more with someone else there, and it "
          "signals that a threat or a mistake is harmless, which is why nervous giggles and "
          "contagious laughter happen. It releases tension and bonds a group, and there is no "
          "single joke centre in the brain.",
          ask=("why", "what", "human", "humans", "people", "contagious", "nervous", "social"),
          avoid=("at me", "bully", "bullied", "can't stop", "cant stop", "uncontrollable",
                 "crying", "therapy", "nervous breakdown", "baby", "babies", "child",
                 "children", "infant", "infants", "toddler", "toddlers", "kid", "kids")),
    entry("stomach-growl", (("stomach growl", "stomach growling", "tummy rumbling",
                             "stomach rumbling", "belly rumbling", "gurgling stomach",
                             "stomach gurgling"),
                            ("why", "what", "cause", "loud", "hungry", "mean", "happen")),
          "The growl is peristalsis: the gut's muscles squeeze and push gas and fluid along, and "
          "an empty stomach sounds louder because there is less food to muffle it. It is normal, "
          "and eating something or drinking water usually settles it; see a GP if it comes with "
          "pain, bloating or weight loss.",
          avoid=("dog", "dogs", "cat", "cats", "puppy", "kitten", "baby", "babies", "child",
                 "children", "period", "pregnant", "pregnancy")),
    entry("shiver", (("shiver", "shivering", "shivers", "shivery"),
                     ("cold", "warm", "body", "freezing", "get", "why", "keep", "keeps",
                      "always", "cant stop", "can't stop", "fever", "flu")),
          "Shivering is your muscles twitching fast on purpose: the movement makes heat, which is "
          "the body's way of holding its temperature when it is losing warmth faster than it makes "
          "it. Shivering with a fever means your temperature is still climbing, so wrap up and "
          "drink something warm.",
          # "why do we shiver" was going to the shaky-hands health card, which also lists the
          # shiver words. A part of the body or a tremor is that card's question, so the plain
          # reason holds those words out and wins the general line.
          avoid=("hands", "hand", "fingers", "arm", "arms", "voice", "nervous", "anxious",
                 "tremor", "tremors", "shaky", "shaking", "parkinsons", "parkinson's",
                 # a pet that shivers is the pet rows' line, not the reason people shiver:
                 # "my dog keeps shivering" was told "shivering is your muscles twitching fast on
                 # purpose", which is a fact about the person typing, not about the dog.
                 "dog", "dogs", "dog's", "puppy", "puppies", "pup", "cat", "cats", "kitten",
                 "kittens", "rabbit", "rabbits", "bunny", "horse", "horses", "pony", "ponies",
                 "hamster", "guinea pig", "budgie", "bird", "parrot", "pet", "pets"),
          ask=("why", "do", "does", "what", "keep", "keeps", "always", "cant stop",
               "can't stop", "fever"),
          bias=2),
    entry("pins-needles", (("pins and needles", "pins", "needles"),
                          ("hand", "hands", "arm", "foot", "feet", "leg", "numb", "tingle",
                           "tingling", "get", "why")),
          "Pins and needles come from a nerve being squashed, say by sitting on your foot: the "
          "signals get muddled, and the tingling is the nerve waking up as the pressure comes off. "
          "It usually clears in a minute or two; if it keeps coming back on its own, get it "
          "checked.",
          ask=("why", "get", "what", "cause")),
    entry("spicy-burn", (("spicy", "chilli", "chili", "chillies", "chillis", "hot sauce",
                          "curry"),
                        # a burning throat after a curry is the same capsaicin going down, and
                        # the row's ask gate kept it out of "my throat is burning after a curry",
                        # which the burnt-pan row then took
                        ("burn", "burns", "burning", "mouth", "hot", "heat", "throat")),
          "Chilli heat is not real heat: capsaicin switches on the same nerve receptors as a burn, "
          "so your mouth reports fire. Milk, yoghurt or ice cream settle it because the fat and "
          "milk protein lift the capsaicin away; water and beer just spread it round.",
          ask=("why", "does", "do", "so", "what", "how", "cool", "stop", "settle",
               "burning", "burns")),
    entry("blush", (("blush", "blushing", "blushes", "go red", "going red", "face go red",
                     "face goes red", "face is red", "face red"),
                    ("face", "cheeks", "embarrassed", "embarrassing", "red", "why", "cause",
                     "causes")),
          "Blushing is adrenaline opening up the small blood vessels in your face, and it happens "
          "when you feel exposed to other people's attention. You cannot stop it on purpose, which "
          "is exactly why it makes you more embarrassed, though people read it as honest rather "
          "than weak.",
          ask=("why", "do", "does", "what"),
          avoid=("makeup", "make up", "blusher", "powder", "shade", "blend", "apply",
                 "patchy", "patch",
                 "drink", "drinking", "drunk", "alcohol", "beer", "wine", "vodka", "hangover",
                 "exercise", "exercising", "running", "run", "gym", "sport", "workout",
                 "hot", "heat", "fever", "temperature", "sun", "sunburn", "sunburnt",
                 "rash", "rosacea", "allergic", "allergy", "spicy", "menopause",
                 "high blood pressure",
                 # a face red from crying, a hot shower or physical strain is not embarrassment
                 "cry", "crying", "cried", "tears", "shower", "bath",
                 "cough", "coughing", "sneeze", "sneezing", "sing", "singing")),
    entry("butterflies", (("butterflies", "knots in my stomach", "fluttery stomach"),
                          ("stomach", "tummy", "belly", "gut", "nervous", "nerves")),
          "Nerves and gut share the same wiring: adrenaline diverts blood to your muscles and slows "
          "digestion, so your stomach feels fluttery or churny. Slow breathing helps because it "
          "switches the body back toward rest, and it passes once the moment does.",
          ask=("why", "get", "what")),
    entry("dizzy-standing", (("dizzy", "dizziness", "lightheaded", "light headed", "head rush",
                              # "i feel faint when i stand up quickly" is the same question as
                              # the dizzy one and was an echo
                              "faint", "fainting", "feel faint", "nearly faint",
                              # The words people use for this that are not "dizzy". The `dizzy`
                              # row below names some of them and stands down for every standing
                              # word, so a spell that happens on getting up still had no answer:
                              # "im woozy when i stand up" and "i feel giddy when i stand up" were
                              # both met with "I'm listening", line after line, and "stood up and
                              # saw stars" with "Got it". Each is the same moment of blood pooling
                              # in the legs, said with the word that came first. The standing word
                              # is still needed, so "i felt giddy at the fair" and "the kids were
                              # giddy" keep their own replies.
                              "woozy", "woozy headed", "giddy", "swimmy", "swimmy headed",
                              "swim headed", "head spins", "head spinning", "head swims",
                              "saw stars", "see stars", "stars in front of my eyes",
                              "my vision went", "vision goes", "the spins", "all funny",
                              "eyes go funny", "drains from my head", "blood drains"),
                            ("stand", "standing", "stood", "get up", "getting up", "up",
                             # "i go woozy if i get out of bed" and "sat up too fast" say the same
                             # trigger as "when i stand", and "up" alone did not reach them: the
                             # movement is the rising, so the phrase is what is keyed.
                             "stand up", "stood up", "sat up", "sitting up", "out of bed",
                             "on my feet")),
          "Standing up quickly lets blood pool in your legs for a moment before your body tightens "
          "the vessels and adjusts, so your head is briefly short of blood and you see stars. Get "
          "up in two stages, drink enough water, and see a doctor if you actually faint or it "
          "happens most times you stand.",
          # The hour of it is said without a question word too: "i feel faint every time i
          # stand up" names the symptom and the trigger and asks nothing, so the ask gate held
          # it out and the person got "Got it". These are the words that say how often it
          # happens, and the two key parts still have to be in the line, so a bare "i sometimes
          # faint" stays where it was.
          ask=("why", "when", "do", "does", "every time", "each time", "whenever", "sometimes",
               "often", "always", "most times")),
    # A dizzy spell that is not about standing up had no card of its own: "i feel dizzy", "i keep
    # getting dizzy", "how do i stop feeling dizzy" and "what causes dizziness" got the empty
    # comfort line or a shrug, while the one real dizziness answer in the tree keyed on standing.
    # The standing card keeps its lines by the avoid list below, because it names the cause.
    # The id was `dizzy`, which health.py already has: two entries under one id is what
    # `tests.test_ids_are_unique` fails on, and the pair landed a day apart (#6554 in health.py,
    # #7068 here). The card stays as it is and only the name moves: health.py's `dizzy` answers
    # the plain "i feel dizzy", and this one answers the lines that name a cause ("what causes
    # dizziness", "i nearly faint every morning"), where `_a_dizzy_spell` is the answer.
    entry("dizzy-spell", (("dizzy", "dizziness", "lightheaded", "light headed", "light-headed",
                     "giddy", "woozy", "head rush", "seeing stars",
                     # the faint that is still coming: "i'm going to pass out" wants sitting
                     # down now, not the card that says ring 111 this week about a faint that
                     # already happened
                     "pass out", "passing out", "going to pass out", "about to pass out",
                     # "i feel faint" was an empty "Got it", and the standing card needs the
                     # standing to answer it, so the faint that is not about standing is this row
                     "faint", "fainting", "feel faint", "nearly faint", "going faint",
                     # blacking out and passing out already have a card that says ring 111 today,
                     # and a faint spell that has not got that far is this one
                     "see stars"),
                    # the ask half is only there to keep the row from answering a noun in passing
                    # ("the dizzy heights"), so it is written wide: what, why, how, and the words a
                    # person says about their own body when it happens
                    ("what", "why", "how", "causes", "cause", "feel", "feels", "feeling", "felt",
                     "get", "getting", "keep", "keeps", "kept", "always", "constantly",
                     "suddenly", "stop", "treat", "help", "normal", "morning", "mornings",
                     "every", "when", "whenever", "after", "before", "during", "at", "in",
                     "on", "going", "might", "im", "i'm", "ive", "have", "had", "am", "and")),
          _a_dizzy_spell,
          # the standing card is the same subject with its cause named, so it keeps those lines
          avoid=("stand", "standing", "stood", "get up", "getting up", "getting out of bed",
                 # a faint that has already happened is the collapse card's: it says ring 111
                 # today, and this card is about the spell that is happening or keeps happening
                 "yesterday", "last night", "last week", "this morning", "this afternoon",
                 "earlier", "ago", "already", "the other day", "an hour ago",
                 # the collapse card already answers the fainting that keeps happening and the
                 # pass out, and it says ring 111 today, which is better than this card's GP
                 "keep fainting", "keeps fainting", "fainting spells", "keep passing out",
                 "keeps passing out", "passed out", "black out",
                 # a faint that keeps happening is the card that says be seen this week
                 "sometimes", "often", "twice", "again and again", "every few weeks",
                 "blacked out", "blacking out",
                 "out of bed", "on my feet",
                 # a film, a ride and an idiom, not a person's head
                 "heights", "film", "films", "movie", "movies", "hitchcock", "ride", "roller",
                 "coaster", "rollercoaster", "theme park", "fairground",
                 # a child who faints or blacks out is ring 111 today, and that card names them
                 "child", "children", "kid", "kids", "son", "sons", "daughter", "daughters",
                 "baby", "babies", "toddler", "toddlers", "boy", "boys", "girl", "girls",
                 "grandson", "grandsons", "granddaughter", "granddaughters", "pupil", "pupils",
                 "teenager", "teenagers", "school",
                 # a racing or pounding heart is its own question and has its own card below
                 "heart", "palpitations", "heartbeat", "racing", "pounding", "pounding heart",
                 "chest", "flutters", "fluttering",
                 # an animal's head is the vet's, and a machine's is nobody's
                 "dog", "dogs", "puppy", "cat", "cats", "kitten", "rabbit", "hamster", "horse",
                 "printer", "screen", "monitor", "computer",
                 # "faint" is the same word as the faint smell, the faint line on a test and the
                 # faint writing on a receipt, and none of those is a person's head
                 "smell", "smells", "faint smell", "line", "lines", "faint line", "writing",
                 "print", "noise", "sound", "light", "accent", "memory", "hope", "chance",
                 # positional vertigo is the inner ear's and has a manoeuvre of its own, so the
                 # spell that only comes with lying down or turning over keeps the ear card: the
                 # word "vertigo" on its own is still a person's dizziness and stays here
                 "vertigo when i lie down", "vertigo lying down", "vertigo when i lay down",
                 "vertigo in bed", "vertigo rolling over", "vertigo turning over",
                 "bppv", "epley", "positional vertigo"),
          bias=1),
    entry("falls-elderly",
          (("fall", "falls", "falling", "fell", "fallen", "trips", "tripped", "tripping",
            # a shuffle is the same complaint said as a way of walking: "my dad shuffles instead
            # of walking" was a shrug ("Is there anything you'd like a hand with?"), and small
            # steps with the feet not lifted is exactly what the falls review is about
            "shuffle", "shuffles", "shuffling", "shuffled", "small steps", "tiny steps",
            "little steps", "not lifting her feet", "not lifting his feet",
            "wont lift her feet", "wont lift his feet", "feet dont leave the floor",
            "tripping over", "trips over", "tripped over", "keeps tripping", "trip over",
            "gone over", "goes over", "unsteady", "wobbly", "off balance", "bad balance",
            "poor balance", "balance is bad", "balance is poor", "balance isnt great",
            "balance isn't great", "balance problems", "lost her footing", "lost his footing",
            "lost their footing", "losing her balance", "losing his balance",
            "losing their balance", "loses her balance", "loses his balance",
            "loses their balance", "lost her balance", "lost his balance",
            "lost their balance"),
           # A fall on its own is a first-aid question and safety owns it. What this answers is
           # the pattern - the second, third, fourth time - plus the balance lines, because that
           # is the question that has an answer: strength, sight, medicines, blood pressure and
           # the house. Without this second part the entry would take "why do leaves fall in
           # autumn" and "the shares fell today".
           ("keeps", "keep", "kept", "twice", "three times", "several times", "a few times",
            "lately", "recently", "often", "always", "constantly", "unsteady", "wobbly",
            "balance", "feet", "foot", "walking", "stand", "standing", "all the time",
            "off her feet",
            "off his feet", "risk", "worried", "worry", "scared",
            # the carer's question, and the one this entry is really for: "how do i stop my
            # mum falling over", "what can I do to prevent a fall". Without these the card
            # never reaches the person who is asking on someone else's behalf.
            "stop", "stops", "stopped", "prevent", "prevention", "reduce the risk",
            "safer", "help her", "help him", "help them", "what can i do", "how do i",
            # "my dad is 80 and falls over" and "what should i do about my dad falling" are
            # carer's questions about a person, and the fall worth a look is theirs
            # the time of day is part of the same question: "how do i stop my dad falling in the
            # night" was answered with how to dip the headlights, because the driving-at-night
            # card keys "at night" and "how do i". A person who falls at night is this row.
            "in the night", "at night", "during the night", "night time", "nighttime",
            "gets up in the night", "in the dark", "when it is dark", "when its dark",
            "what should i do", "should i do", "do about", "falls over", "falling over",
            "fell over", "my dad", "my mum", "my mother",
            "my father", "my nan", "my nana", "my grandad", "my grandma", "my granny",
            "grandad", "grandma", "granny", "grandpa", "elderly", "oap", "in her 80s",
            "in his 80s", "in her 90s", "in his 90s", "80", "90",
              "had", "has had", "two", "three", "four", "this month", "last month",
            "this year", "since", "again")),
          "Falls are usually several small things adding up rather than one bit of clumsiness: leg "
          "strength and balance, eyesight, blood pressure that dips on standing, medicines, and the "
          "house itself - which is why the second one is worth acting on rather than waiting for the "
          "third. Ask the GP for a falls review: they check blood pressure lying and standing, go "
          "through the medicines, and can refer to a falls clinic or a strength and balance class, "
          "which is what actually cuts falls. Then take the house apart: grab rails on the stairs "
          "and by the loo, a night light, rugs lifted or taped down, cables out of the walkway, and "
          "a phone within reach from the floor. If they cannot get up or put weight on it, or knock "
          "their head - especially on a blood thinner - that is a same-day call.",
          # "i feel unsteady on my feet" is a balance question, and the foot entry was taking it.
          bias=1,
          guard=_a_fall_a_person_had,
          # falling asleep, falling out with someone, falling prices and hair falling out are
          # other questions; a fall off a ladder is a first-aid one. "how do i fix a wobbly
          # toilet seat" reached this card on "how do i" plus "wobbly", so a wobbly thing in the
          # house is named here: the person words ("wobbly", "unsteady", "feet") stay in the key.
          # Bare "out" used to be the fence for "falling out with someone", and it fenced off
          # every fall that happens on the way out of something: "my mum fell out of bed" lost
          # the falls answer and the friendship row took it. The phrase is the fence now.
          avoid=("asleep", "sleep", "fell out with", "fall out with", "falling out with",
                 "fallen out with", "out with", "not talking", "stopped talking", "made up",
                 "make up", "behind", "apart", "prices", "shares", "rain",
                 # "we had a falling out" names no person, so the friendship row cannot take it,
                 # and with bare "out" gone it reached this answer. A row is not a fall.
                 "had a falling out", "a falling out", "falling out last", "fell out over",
                 "fall out over", "falling out over",
                 # a row that keeps happening names no person either ("we keep falling out"), so
                 # with bare "out" gone it reached the falls answer. "falling out" without "of"
                 # is the argument; "fell out" alone cannot be here, because "fell out of bed"
                 # is the line this whole change exists to rescue.
                 "keep falling out", "always falling out", "keeps falling out",
                 "we fell out", "we have fallen out", "weve fallen out", "we've fallen out",
                 "out over money", "out over something",
                 # a wobbly seat, chair or shelf is the household-fix row's, not a falls review
                 "toilet seat", "toilet", "seat", "chair", "chairs", "table", "desk", "gate",
                 "door", "hinge", "shelf", "shelves", "bolt", "screw", "screws",
                 "washing machine", "washer", "fridge", "freezer", "wheel", "wheels",
                 "floorboard", "floorboards", "handrail", "railing", "stair gate", "tap",
                 "radiator", "trolley", "pram",
                 # a wobbly fence post is a fence repair, not a balance problem: the fence word
                 # was enough with "keeps" or "how do i" and "how do i fix a wobbly fence
                 # post" got a falls review on main
                 # a playlist shuffles and so do cards: the music and the game are not a gait
                 "playlist", "playlists", "music", "songs", "song", "spotify", "album", "shuffle "
                 "play", "on shuffle", "cards", "deck of cards", "shuffle the",
                 "fence", "fences", "fencing", "fence post", "fence posts", "gate post",
                 "gatepost", "gravel board",
                 # falling for someone, falling for a scam and falling in love are not falls,
                 # and neither is "i keep tripping myself up" over your own feet
                 "falling for", "fall for", "fell for", "fall in love", "falling in love",
                 "fell in love", "tripping myself up", "trips myself up", "tripped myself up",
                 # guilt tripping is a person working on someone's feelings, not feet: "keep"
                 # and "tripping" together were enough for this entry, so "my mum keeps guilt
                 # tripping me" got the falls answer. A trip out and a trip abroad are other
                 # questions too, and so is tripping over the cat.
                 # Packing is never falling: "how do i pack for a trip" was answered with this
                 # entry, because "trip" is one of its key words and the travel list scores lower.
                 "pack", "packing", "packed", "suitcase", "suitcases", "luggage",
                 "hand luggage", "rucksack", "backpack", "kit list", "packing list",
                 # "how do i survive a long coach trip" is a journey, not a fall
                 "survive a", "coach trip", "coach journey", "train journey", "long journey",
                 "long trip", "long drive", "long flight",
                 "guilt tripping", "guilt trip", "guilt trips", "guilt tripped",
                 "guilt-tripping", "guilt-trip", "tripping me", "trips me", "tripping him",
                 # "tripped over the" was here for tripping over the cat, and it matched
                 # "tripping over the" as the same word, so "i keep tripping over the rug" -
                 # the most ordinary falls line there is - got no answer at all. The pet words
                 # below already carry the cat and the dog.
                 "tripping her", "trip out", "trip abroad",
                 # a road trip is a plan to drive somewhere, not a fall: "how do i plan a road
                 # trip" was answered with a falls review, on "trip" plus "plan"/"how do i"
                 "road trip", "road trips", "roadtrip", "plan a trip", "planning a trip",
                 "plan the trip", "itinerary", "driving holiday", "long drive",
                 "snow", "leaves", "hair", "temperature", "standards", "short", "through",
                 "ladder", "roof", "scaffold",
                 # a pet that keeps falling over is a vet question, and a toddler who keeps
                 # falling over is a different answer too - both pass rather than get this one
                 "dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets",
                 "toddler", "baby", "child", "children", "kid", "kids", "son", "daughter",
                 "nursery", "boy", "girl",
                 # a fuse, a breaker or an RCD trips too, and that is the electrics question:
                 # "the fuse keeps tripping" was coming here because it has "keeps" and "tripping".
                 "fuse", "fuses", "breaker", "breakers", "plug", "plugs", "socket", "sockets",
                 "rcd", "electric", "electrics", "electricity", "wiring", "power", "lights",
                 "light", "consumer unit", "trip switch", "switch", "appliance", "appliances",
                 # the circuit itself trips too: "my circuit keeps tripping" had "keeps" and
                 # "tripping" and no electrical word the fence knew, so it got the falls card.
                 "circuit", "circuits", "mcb", "rcbo", "fuse box", "distribution board",
                 # a trip that is a holiday is not a stumble, and the planning memory puts the
                 # subject back on the end of a follow-up: "the best place to keep it while i
                 # save" after a saving goal has "trip" in it and read as a fall.
                 # A trip being planned is not a stumble either, and this entry is the one that
                 # wins those lines: "how do i plan a trip to japan" had "trip" and "how do i" and
                 # took the falls answer. The travel shapes below are the fence; bare "plan" is
                 # not in it, because "my plan for the stairs" is still a falls line.
                 "plan a trip", "planning a trip", "planned a trip", "plan my trip",
                 "plan the trip", "plan our trip", "plan a holiday", "trip plan", "trip plans",
                 "itinerary", "trip to", "trip with", "trip for", "city break", "days away",
                 "week away", "travel plan", "holiday plan", "organise a trip", "organize a trip",
                 "sort out a trip",
                 "holiday", "holidays", "abroad", "flight", "flights", "booking", "booked",
                 "save", "saves", "saving", "savings", "saved", "money", "budget", "fund",
                 # "trip" is a journey as well as a stumble, and the bare noun in an asking
                 # frame took "how do i plan a trip": the journey phrases stand the fall down,
                 # while "trips", "tripped" and "keeps tripping" still reach it
                 "plan a trip", "a trip", "trip to", "the trip", "our trip", "vacation",
                 "hotel", "hotels", "itinerary", "travel", "city break", "going away",
                 "book a trip", "passport", "airport", "packing", "planning a trip",
                 "plan my trip")),
    entry("bones", (("bones", "bone"), ("how many", "count", "number")),
          "An adult has 206 bones; a baby is born with roughly 270, and many of those fuse together "
          "as you grow. The smallest are three tiny ones in each middle ear.",
          # an animal's count is not a person's: "how many bones does a horse have" was
          # getting 206, the human number
          avoid=("dog", "cat", "puppy", "kitten", "pet", "chew", "chewed", "eat", "ate",
                 "horse", "horses", "cow", "cows", "sheep", "pig", "pigs", "rabbit",
                 "rabbits", "bird", "birds", "fish", "paw", "paws", "beak", "beaks",
                 "tail", "tails", "animal", "animals"),
          ask=("how", "many", "count", "number")),
    # One row for the record questions above: the subject is the part of the body, and the reply
    # hands over the fact for the part that was named.
    entry("body-record", (_the_body_record_key(), _RECORD_ASK),
          _what_the_body_is_like,
          # a pet's bones, a dentist appointment and an aching tooth are other answers, and so is
          # the dog's chew; the record questions are the ones that name the part and ask a number
          # or a superlative about it
          avoid=("dog", "cat", "puppy", "kitten", "pet", "chew", "chewed", "toothache",
                 "tooth hurts", "my tooth", "dentist", "filling", "braces", "brace",
                 "broken bone", "break a bone", "broke my", "fracture", "sprain",
                 "muscle ache", "sore muscles", "strain", "cramp", "cut my finger",
                 "numb", "numbness", "tingling", "nail",
                 # a line about cooking is about the dinner, whatever else it names: "whats a
                 # nice thing to cook for a date" named a "date", the record row took it and had
                 # nothing to say, and a candidate that says nothing is the search line.
                 "cook", "cooking", "cooked", "bake", "baking", "roast", "recipe", "recipes",
                 "dinner", "supper", "meal", "meals", "menu")),
    entry("heart-rate", (("heart", "heartbeat", "pulse"),
                        ("fast", "faster", "beat", "beats", "run", "running", "exercise",
                         "racing")),
          "Working muscles need more oxygen, so your heart beats faster and harder to move blood "
          "round; a fit heart pumps more with each beat, which is why fit people have slower "
          "resting rates. Anywhere from 60 to 100 beats a minute at rest is normal for adults.",
          ask=("why", "does", "when", "do")),
    entry("immune-system", (("immune system", "immunity", "immune"),
                           ("fight", "fights", "work", "works", "body", "infection", "germs")),
          "Your body fights infection in layers: skin and mucus keep germs out, white blood cells "
          "attack whatever gets through, and antibodies tag specific germs for destruction. "
          "Memory cells remember each germ, which is why you rarely catch the same one twice and "
          "why vaccines work.",
          ask=("how", "what", "why", "does")),

    entry("predict-earthquakes", (("predict", "prediction", "forecast"), ("earthquake",
                                                                          "earthquakes", "quake")),
          "Nobody can say when a particular earthquake will hit: the rock gives way suddenly and "
          "the signs beforehand are unreliable. What we can do is forecast where and how strongly "
          "the ground is likely to shake, which is why buildings in earthquake zones are built to "
          "flex.",
          ask=("can", "could", "how", "why", "do", "we")),
    entry("ice-melt", (("ice", "ices"), ("melt", "melts", "melting", "melted")),
          lambda memory, understood: _how_long_ice_takes(understood)),
    entry("cramp", (("cramp", "cramps", "cramping", "charley horse"),
                    ("leg", "legs", "foot", "feet", "calf", "calves", "toe", "toes", "night",
                     "muscle", "muscles", "why", "cause", "causes", "happen", "happens",
                     # "how do i get rid of a cramp" and "how do i stop cramp in my leg" are the
                     # same question as "why do i get cramp in my calf", and the remedy phrasing
                     # was reaching the period-pain row on the bare word "cramps"
                     "stop", "help", "holds", "get rid", "clear up", "cure", "fix",
                     # "i keep getting cramp" is the same question in the tense people use it in,
                     # and it was the one version that reached nothing at all: the ask gate below
                     # knew "get" but not "getting", "keep" or "always"
                     "getting", "got", "keep", "keeps", "kept", "always", "often", "most days",
                     "every day", "have", "had")),
          "A cramp is a muscle contracting hard and not relaxing, which hurts sharply for a minute "
          "or so. Stretch it gently, pull your toes up toward you for a calf cramp, and drink "
          "water; cramps at night often come with tired muscles, dehydration or low magnesium. "
          "Before exercise, warm up and add distance slowly, and see a GP if a cramp comes on "
          "every time you walk a set distance, or comes with a calf that is swollen and hot.",
          # "cramped" is a form of "cramp" once the words are stemmed, so it cannot go in the
          # avoid list: it stopped the row answering "cramp at night" as well. A cramped flat
          # names no muscle, foot or ask word, so it never reaches this row anyway.
          avoid=("stomach", "stomachs", "tummy", "abdomen", "belly", "period", "periods",
                 "menstrual", "ibs", "diarrhoea", "diarrhea",
                 # a child's cramp is the family lane's answer, not an adult's: the words of
                 # stretching and of a GP visit are right for a grown-up and not for a small one
                 "child", "children", "kid", "kids", "daughter", "son", "baby", "toddler",
                 "toddlers", "boy", "girl"),
          ask=("why", "get", "gets", "getting", "got", "at", "what", "how", "stop", "help",
               "cure", "keep", "keeps", "kept", "always", "often", "have", "had")),
    entry("allergy-why", (("allergy", "allergies", "allergic", "hay fever", "hayfever"),
                          ("why", "cause", "causes", "happen", "happens", "what", "get",
                           "getting", "develop")),
          "An allergy is the immune system mistaking something harmless - pollen, pet dander, "
          "dust, a food - for a threat and releasing histamine, which causes the sneezing, itchy "
          "eyes or rash. Hay fever is that reaction to pollen; antihistamines block the histamine, "
          "and a pharmacist can advise on the best one for you.",
          # "what can i do about my hay fever" asks for the hayfever entry's advice, not for what
          # an allergy is, so the ask shapes stand this explanation down.
          avoid=("throat", "breathing", "wheeze", "wheezing", "swollen", "swelling", "epipen",
                 "anaphylaxis", "hospital", "take", "tablet", "tablets", "medicine",
                 "antihistamine", "relief", "am", "was", "im", "i'm", "remind", "remember",
                 "said", "say", "told", "again", "anything", "did", "help", "helps", "relieve",
                 "treat", "treatment", "stop", "prevent", "manage", "best",
                 "what can i do", "what should i do", "what can we do", "how do i",
                 "how can i", "is there anything", "anything i can do")),
    entry("runny-nose-why", (("runny nose", "nose runs", "nose is running", "blocked nose",
                              "stuffy nose", "snot", "mucus"),
                             ("why", "cause", "causes", "happen", "happens", "what", "get", "keep")),
          "A runny nose is mostly your body flushing out irritants: the lining makes extra mucus "
          "to trap pollen, dust or a virus and wash it away, and it can keep running for a while "
          "after the trigger is gone. Clear, watery stuff is usually allergy or cold; thick green "
          "mucus is not automatically an infection, but a fever or one-sided pain should be checked.",
          avoid=("blood", "bleeding", "nosebleed", "baby", "babies", "child", "children", "kid",
                 "kids", "take", "medicine", "spray", "decongestant", "stop", "treat", "cure",
                 "am", "was", "im", "i'm", "said", "say", "told", "remind", "remember", "again",
                 "help", "helps", "relieve", "relief", "prevent", "manage", "best")),
    entry("fever-why", (("fever", "feverish", "high temperature"),
                        ("why", "cause", "causes", "happen", "happens", "what", "get")),
          "A fever is the immune system turning up the body's thermostat to make it harder for "
          "germs to multiply, so it is a response rather than the illness itself. It is common with "
          "infections and usually settles in a few days; in a baby under three months, or with a "
          "stiff neck, confusion, a rash that does not fade or trouble breathing, get medical help "
          "urgently.",
          avoid=("baby", "babies", "infant", "child", "children", "kid", "kids", "paracetamol",
                 "ibuprofen", "medicine", "take", "reduce", "bring", "lower", "how to", "have",
                 "has", "got", "do i", "should i", "what can i", "what should i", "help",
                 "helps", "relieve", "relief", "treat", "treatment", "cure", "stop", "prevent",
                 "manage", "best")),
    # People ask this two ways: "why do i crave sugar" and "why do i want sugar at night".
    # The second one names nothing but the food, so the food is a way into this entry too - but
    # then "why is sugar bad for you" reaches it as well, and that is the health question, not the
    # craving one. `ask` is what tells them apart: a craving line wants or craves something.
    entry("craving-why", (("craving", "cravings", "crave", "craving sugar", "craving sweets",
                           "sugar", "sweets", "sweet", "sweet things", "chocolate", "carbs",
                           "crisps", "biscuits", "cake", "salt", "salty", "junk food", "bread",
                           "pasta", "cheese"),
                          ("why", "cause", "causes", "happen", "happens", "what", "get", "always",
                           "suddenly", "mean")),
          "Cravings are usually the brain asking for quick energy or a habit cue rather than a "
          "nutrient shortage: sugar and salty fat hit the reward system fast, and seeing or "
          "smelling food can set one off. Eat a proper meal with protein and fibre first, then wait "
          "ten minutes; if you are craving non-food things, get that checked.",
          # "why am i craving sugar at night" is the same question as "why do i crave sugar", so
          # "am" is not a reason to stand down; "what did i say i was craving" still is.
          avoid=("pregnant", "pregnancy", "baby", "child", "kid", "ice", "dirt", "cigarette",
                 "smoke", "alcohol", "drink", "drug", "drugs", "was", "im", "i'm", "said",
                 "say", "told", "remind", "remember", "again", "did", "help", "helps", "relieve",
                 "relief", "treat", "treatment", "cure", "stop", "prevent", "manage", "best",
                 # "my mum is 80 next week and we want a cake, what should i bake" was answered
                 # with what cravings mean, because "cake" is one of this row's words and "what"
                 # is the other. A line that asks what to bake, or names the oven or a recipe, is
                 # a baking line: what someone wants to eat is not what they are about to make.
                 # The bare forms of bake are NOT here: a craving and a bake share both words in
                 # "why do i crave cake when i bake bread", and fencing the verb took a craving
                 # question to the sponge times. The asking phrase is what tells them apart.
                 "oven", "recipe", "recipes", "icing",
                 "decorate", "how long in the oven", "what should i bake", "what to bake"),
          ask=("want", "wants", "wanting", "crave", "craves", "craving", "cravings", "fancy",
               "feel like"),
          # a "why do i crave sugar" question wants the cause, not the cut-down plan, and the
          # nutrition sugar-craving card otherwise ties with this and is registered earlier
          bias=1),
    entry("acne-why", (("acne", "pimples", "spots", "breakouts", "zits"),
                       ("why", "cause", "causes", "happen", "happens", "what", "get", "getting",
                        "adult", "teenage", "teenager", "teenagers", "teen", "teens",
                        "teenaged", "hormonal",
                        # the answer has the two things a treatment ask wants - what causes it
                        # and what to put on it - so the goal is a key word here rather than a
                        # stand-down: "how do i get rid of acne", "how do i treat acne" and
                        # "best way to clear acne" are acne questions before they are anything
                        # else, and this card is the acne answer.
                        "get rid", "rid of", "clear", "clearing", "treat", "treatment", "cure",
                        "stop", "prevent", "best", "help", "helps", "relieve", "relief",
                        "manage")),
          "Acne happens when hair follicles get blocked by oil and dead skin, and skin bacteria "
          "multiply in the blocked pore; hormones make the oil glands busier, which is why it peaks "
          "in the teens. Wash gently twice a day, do not pick, and a pharmacy treatment with benzoyl "
          "peroxide or salicylic acid is a reasonable first try; painful cysts or scarring deserve "
          "a GP.",
          avoid=("shirt", "shirts", "clothes", "clothing", "fabric", "stain", "stains",
                 "detergent", "laundry", "wash", "washing", "rash", "chickenpox", "measles",
                 "mole", "cancer", "bleeding", "am", "was", "said", "say", "told",
                 "remind", "remember", "again", "did",
                 # the other life of "spots": on a car, a wall, a carpet, a leaf. The goal verbs
                 # above are what a person says about their face, and a marketing or a paint
                 # question is not an acne question.
                 "car", "cars", "windscreen", "wall", "walls", "floor", "floors", "carpet",
                 "carpets", "sofa", "duvet", "mattress", "paint", "leaf", "leaves", "plant",
                 "plants", "garden", "grease", "oil", "mud", "sink", "mirror",
                 # a sunbed does not clear spots, and neither a tanning question nor a product
                 # being chosen is an acne question: both were a punt on main
                 "sunbed", "sunbeds", "sun", "tan", "tanning", "solarium",
                 "moisturiser", "moisturizer", "sunscreen", "spf", "lotion", "serum",
                 "cleanser", "cleansers", "product", "products", "brand")),
    entry("sweat", (("sweat", "sweating", "sweaty"), ("nervous", "stress", "why", "smell",
                                                      "body")),
          "Nervous sweat comes from glands that open up under stress hormones, and it is the "
          "bacteria on your skin breaking that sweat down that makes it smell. Ordinary "
          "antiperspirant works better than deodorant for the smell and dampness, because it "
          "reduces the sweat itself.",
          # waking up drenched is the night-sweats question, not the stress-sweat one
          avoid=("night", "nights", "overnight", "asleep", "sleep", "sleeping", "bed",
                 "pillow", "pillows", "sheets", "wake", "waking", "woke", "drenched",
                 "soaked",
                 # a shoe that smells is the shoe's question: "how do i get sweat smell out of
                 # trainers" was answered with the stress-sweat chemistry, because "sweat" and
                 # "smell" are the whole of this key
                 "trainers", "trainer", "sneakers", "shoes", "shoe", "boots", "socks",
                 "sock", "insoles", "insole", "footwear", "plimsolls")),
    entry("night-sweats",
          (("sweat", "sweats", "sweating", "sweaty", "drenched", "soaked"),
           ("night", "nights", "overnight", "asleep", "sleep", "sleeping", "bed", "pillow",
            "pillows", "sheets", "wake", "waking", "woke", "doctor", "gp", "worried",
            "weeks", "months", "see a doctor", "see the doctor", "see my doctor",
            "should i worry")),
          "Most night sweats are a hot room, a thick duvet or a fever, so check those first: a "
          "cooler room and a lighter duvet settle it often enough. If you wake drenched for weeks "
          "with no explanation, or with weight loss, a cough or swollen glands, see a GP, because "
          "night sweats are worth checking for an infection, a thyroid problem and, rarely, "
          "lymphoma.",
          # a baby or child with a fever belongs to the fever and safety answers, and a
          # daytime sweat belongs to the stress-sweat entry. A night sweat that names stress
          # still needs the night answer: the ask gate already keeps a daytime nervous sweat
          # out, so stress words are not doing any work here.
          avoid=("baby", "babies", "child", "children", "kid", "kids", "boy", "girl",
                 "daughter", "son", "toddler", "newborn", "teething", "fever", "flu",
                 "covid", "interview", "speech",
                 "presentation", "exam", "gym", "run", "running", "exercise", "workout",
                 # "overnight" is doing two jobs: a night sweat, and the soak a cook gives
                 # beans, rice or lentils. "do i need to soak sticky rice overnight" was
                 # answered with night sweats, so the ingredients stand this row down and the
                 # cooking answer gets it. The ingredients, not "soak": "soaked" is matched
                 # by its own forms here, and "i woke up soaked in sweat" is a night sweat.
                 "beans", "bean", "lentils", "lentil", "chickpeas", "chickpea", "rice",
                 "oats", "porridge", "pasta", "noodles", "chicken", "stock", "sauce",
                 # and the same for the things people soak by choice: nuts, dried fruit and the
                 # grains that get a soak. "is it ok to soak cashews overnight" was a night-sweat
                 # answer, which is a bad thing to say to somebody asking about a curry.
                 "cashews", "cashew", "almonds", "almond", "walnuts", "walnut", "peanuts",
                 "peanut", "raisins", "raisin", "sultanas", "sultana", "dried fruit",
                 "apricots", "prunes", "dates", "barley", "bulgur", "couscous", "quinoa",
                 "millet", "buckwheat", "haricot", "cannellini", "soya", "soy", "adzuki",
                 "split peas", "black beans", "kidney bean",
                 # a wash is the other thing left in water overnight, and the dishes and a stain
                 # are soaked by choice too: "left the washing to soak overnight", "how do i soak
                 # a stained shirt overnight" and "can i leave the laundry to soak overnight"
                 # were all the night-sweat answer.
                 "washing", "laundry", "clothes", "shirt", "shirts", "towel", "towels",
                 "dishes", "dishcloth", "sink", "bucket", "stain", "stains", "stained"),
          ask=("night", "nights", "overnight", "asleep", "sleep", "sleeping", "bed", "pillow",
               "pillows", "sheets", "wake", "waking", "woke"),
          # "should i see a doctor" is part of the night-sweat question, so the generic
          # appointment card must not take it
          bias=2),
    entry("cry", (("cry", "crying", "tears", "tearful"), ("sad", "why", "happy", "emotion",
                                                          "upset")),
          "Crying is a pressure valve: strong feeling sets off the same nerves that make your "
          "breath catch, and the tears are part of that response rather than a sign of weakness. "
          "Emotional tears carry stress hormones, and most people feel calmer afterwards.",
          # a dog or a baby that cries is the pets and family lanes' question. A baby was the
          # gap: "why is my baby crying" was told the physiology of adult tears, so the baby
          # words are named here as well as the animals.
          avoid=("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets", "bird",
                 "parrot", "rabbit", "horse", "baby", "babies", "newborn", "new born", "infant",
                 "teething", "nappy", "feeding", "breastfeeding", "formula")),
    entry("blink", (("blink", "blinking", "blinks"), ("why", "eye", "eyes", "often", "do")),
          "You blink about 15 to 20 times a minute to keep the eye wet and to clear dust, and a "
          "blink also gives your brain a tiny rest from the visual stream. Screening and driving "
          "make people blink less, which is why eyes get sore and gritty after a long session."),
    entry("wrinkles", (("wrinkle", "wrinkles", "wrinkled", "wrinkly", "wrinklies",
                        "ageing skin", "aging skin", "thin skin", "skin thin", "skin thinner",
                        "skin gets thin", "skin so thin"),
                       ("why", "get", "skin", "face", "age", "stop", "prevent", "avoid",
                        "reduce", "how")),
          "Skin gets thin and creases as the collagen and elastin that keep it springy thin out "
          "with age and sun damage; smoking and too much sun make it happen much sooner. "
          "Sunscreen every day is "
          "the one thing that reliably slows it, and moisturiser plumps out the fine lines a "
          "little.",
          # bath water puckers fingers; that is not ageing skin
          avoid=("bath", "baths", "water", "swim", "swimming", "pool", "washing up", "dishes",
                 "pruney", "prune", "shrivel", "shriveled", "shrivelled",
                 # a wrinkly cactus or leaf is the garden's line, not ageing skin
                 "cactus", "cacti", "succulent", "plant", "plants", "leaf", "leaves",
                 # tanning leather is the tan entry's line, and a skin turn before it must not
                 # carry "thin" and "skin" into the next question
                 "leather",
                 "flower", "flowers", "tomato", "tomatoes",
                 # a creased shirt or sheet is laundry, not ageing skin
                 "shirt", "shirts", "clothes", "clothing", "trouser", "trousers", "fabric",
                 "iron", "ironing", "laundry", "cotton", "linen", "dryer", "sheet", "sheets",
                 # wrinkly skin with illness or dehydration is a symptom, not ageing. Thin or
                 # weight-losing skin is still the ageing answer: dropping those words is what
                 # lets "my skin is thin and wrinkles easily" reach it.
                 "dehydrated", "dehydration", "ill", "illness", "unwell", "sick"),
          # "so thin" only means ageing skin when the line is about skin or a wrinkle, not a
          # thin sauce or thin hair that happens to ask why.
          ask=("skin", "face", "wrinkle", "wrinkles", "wrinkled", "wrinkly", "wrinklies",
               "ageing skin", "aging skin"),
          # "why are my fingers wrinkly with age" ties with the ageing entry on score alone, and
          # the question is about the skin, so the skin answer is the one it wants.
          bias=1),
    entry("sleep-why", (("sleep", "sleeping", "asleep"),
                       ("why", "what", "happen", "happens", "need", "needed", "important",
                        "purpose", "body", "brain")),
          "Sleep is when the brain files the day's memories and clears waste, and the body repairs "
          "muscle and releases growth hormone. Most adults need seven to nine hours; if you are "
          "short for weeks, mood, concentration and immunity suffer before you feel sleepy.",
          ask=("we", "people", "humans", "purpose", "need sleep", "sleep needed",
               "sleep important", "sleep for", "what does sleep do"),
          avoid=("can't", "cant", "cannot", "trouble", "insomnia", "awake", "fall asleep",
                 "stay asleep", "too much", "so much", "how much", "hours", "baby", "babies",
                 "newborn", "toddler", "kid", "kids", "child", "children", "puppy", "puppies",
                 "cat", "dog", "wont sleep", "won't sleep", "weeks old", "months old")),
    # The other half of the same question: too much sleep, and still flat. Regular long nights
    # plus unrefreshed days is one of the few everyday tiredness patterns worth a GP visit, and it
    # used to get the search hedge.
    entry("sleep-too-much",
          (("sleep too much", "sleeping too much", "slept too much", "sleep so much",
            "sleeping so much", "oversleep", "oversleeping", "too much sleep", "sleep 10 hours",
            "sleep 12 hours", "sleeping 10 hours", "sleeping all day", "slept all day",
            "slept 10 hours", "slept 12 hours", "slept 9 hours", "sleep 9 hours", "10 hours",
            "11 hours", "12 hours", "ten hours", "eleven hours", "twelve hours",
            "slept in till", "cant wake up properly", "always sleepy", "sleepy all day"),
           ("why", "bad", "normal", "worry", "worried", "still tired", "still knackered",
            "keep", "every day", "always", "lately", "weeks", "months", "problem", "wrong",
            "night", "nights", "too much",
            "should", "what")),
          "Long sleeps now and then are just a debt being paid, especially after a run of short "
          "nights. Needing nine or ten hours most nights and still waking flat is worth a GP "
          "visit: an underactive thyroid, low iron, low vitamin D, depression and sleep apnoea "
          "all show up that way, and each is easy to test for. Keep the wake-up time the same "
          "every day while you wait, because long lie-ins at the weekend hide the pattern.",
          avoid=("my baby", "baby", "newborn", "toddler", "my son", "my daughter", "kids",
                 # a child's age makes it a child's question, and the baby-sleep row reads it:
                 # "my 3 month old is sleeping too much" was this card's adult sleep debt
                 "month old", "months old", "week old", "weeks old", "year old", "years old",
                 "puppy", "cat", "dog", "insomnia", "cant sleep", "can't sleep", "cant get to "
                 "sleep", "shift work", "jet lag", "time zone", "hangover", "teenager",
                 "in a day", "a day have", "hibernate", "pregnant")),
    # "how much sleep do i need" and "is 6 hours enough" are the pair the entry above leaves
    # alone on purpose (its avoid list holds "how much" and "hours"), and they used to get the
    # search hedge. The answer is the range plus the honest test, because the number on its own
    # either frightens people who are fine or reassures people who are not.
    # --- a baby that sleeps a lot -------------------------------------------
    # The adult sleep-needs answer was taking this: "my 6 week old is sleeping a lot" came back
    # with "most adults do best on seven to nine hours". A six-week-old is not a short adult, so
    # the small ages are the key here and the adult line steps aside for them. It lives in this
    # file, not in family.py, because a line about a baby's sleep is understood as sleep and
    # family.py does not answer sleep - adding the topic there moved a toddler's night waking off
    # its own answer.
    entry("baby-sleep",
          (("baby", "babies", "newborn", "new born", "infant", "week old", "weeks old",
            "month old", "months old", "6 week", "six week", "8 week", "eight week",
            "12 week", "twelve week",
            # a toddler's sleep is the same question a year later, and "my toddler is sleeping a
            # lot" was answered with "Thanks for telling me". The bands carry the ages.
            "toddler", "toddlers", "2 year old", "two year old", "3 year old",
            "three year old"),
           # "a lot", "too much" and "all the time" were bare here, and a bare frequency is how
           # every other complaint about a baby is phrased: "my baby cries a lot" and "my baby
           # cries all the time" were answered with the sleep chart. The sleeping has to be said.
           ("sleep", "sleeping", "sleeps", "slept", "sleepy", "drowsy",
            "sleeping a lot", "sleeps a lot", "sleeping all the time", "sleeps all the time",
            "sleeping all day", "sleeps all day", "sleeping too much", "sleeps too much",
            "more than usual", "normal", "hard to wake", "wont wake", "won't wake",
            # "is 14 hours too much for a 5 month old" names the age and the hours and never
            # says sleep, so the adult sleep-debt row answered it with nine or ten hours and a
            # GP visit. An age in the line has already made it a baby's question.
            "hours", "hour", "too much", "how much")),
          _a_baby_sleep_reply,
          # a baby who will not sleep is the opposite question, and the milestones, the feeding
          # and the illnesses are their own answers
          avoid=("wont sleep", "won't sleep", "not sleeping", "cant sleep", "can't sleep",
                 # "isnt sleeping" in the chat-speak spelling, which the apostrophe forms miss
                 "isnt sleeping", "isn't sleeping", "not sleeping well", "never sleeps",
                 "will not sleep", "wont settle", "won't settle",
                 # a baby who will not go off is the settling question, not the sleeps-a-lot one
                 "get my baby to sleep", "get a baby to sleep", "get them to sleep",
                 "help my baby sleep", "help them sleep", "goes to sleep",
                 "sleeping through", "sleeps through", "sleep through", "through the night",
                 # "hours" is one of this card's words now, and "my baby wakes up every two hours
                 # at night" is the night-waking question: the waking is named back here.
                 "wakes", "woke", "waking up", "up every", "every hour", "every two hours",
                 "at night", "all night", "night feeds", "night feeding", "up all night",
                 "colic", "reflux", "teething", "fever", "temperature", "rash", "cough",
                 "cold", "not feeding", "wont feed", "won't feed", "weaning", "milk",
                 "routine", "cot", "sids", "cot death", "swaddle", "cry", "crying",
                 # a baby that cannot be woken, is pale or floppy, or has stopped feeding is a
                 # 999 line, not a sleep pattern: the safety reply owns every one of these
                 "pale", "floppy", "limp", "blue", "grey", "unresponsive", "not responding",
                 "cant wake", "can't wake", "cannot wake", "not waking", "isnt waking",
                 "isn't waking", "wont wake", "won't wake", "wont wake up", "won't wake up",
                 "struggling to breathe", "breathing", "not breathing", "seizure", "fit",
                 "very sleepy", "too sleepy", "sleepy and")),

    entry("sleep-hours",
          (("sleep", "sleeping", "slept", "hours sleep", "hours of sleep", "sleep a night",
            # "i only get 5 hours a night" names no sleep verb at all: the hours and the night
            # are the whole of it, and the redundancy entry used to take the line because "only
            # get hours" reads as an employer cutting them.
            "hours a night", "hours at night", "hours per night", "hours in bed",
            "hours of kip", "hours kip",
            "teenager", "teenagers", "teen", "teens", "teenage", "over 65", "pensioner"),
           ("enough", "how much", "how many", "need", "needed", "short", "hours", "five", "six",
            "how long", "long should i", "long do i",
            "seven", "eight", "5", "6", "7", "8", "only", "less than", "plenty", "normal",
            "healthy", "recommended")),
          _sleep_hours,
          avoid=("my baby", "baby", "newborn", "toddler", "my son", "my daughter", "my child",
                 # a small baby is not a short adult: "my 6 week old is sleeping a lot"
                 "week old", "weeks old", "month old", "months old", "6 week", "six week",
                 "kids", "puppy", "shift work", "jet lag", "time zone", "insomnia", "cant sleep",
                 # A baby is not a small adult: "how much sleep should a 6 month old have" was
                 # getting the seven to nine hours, because a month old is not a "year old" and
                 # the under-one chart lives in family.py (baby-sleep-hours).
                 "month old", "months old", "month-old", "months-old", "weeks old", "week old",
                 "can't sleep", "cannot sleep", "cant get to sleep", "wake up", "waking", "woke",
                 "snoring", "apnoea", "sleep apnoea", "in a day", "a day have", "pregnant",
                 "sleeping tablet", "melatonin", "how long to sleep", "hibernate",
                 # "how long should i nap" is the nap entry's: the new "how long" asks made this
                 # one answer it with the adult night chart, which is the wrong number.
                 "nap", "naps", "napping", "nap for",
                 # "how much calcium does a teenager need" and "how many calories does a teenager
                 # need" reached this chart because the teen words are in its key and the line
                 # asks "how much" about something that is not sleep at all
                 "calcium", "iron", "vitamin", "vitamins", "protein", "fibre", "fiber",
                 "calories", "calorie", "potassium", "magnesium", "zinc", "b12", "folate",
                 "water", "milk", "steps", "exercise",
                 # "how long should i sleep if im ill" is answered warmly by the illness entry
                 # and "how long do i sleep after a concussion" wants a doctor, not a chart:
                 # the hours question is for a well adult, so a body that is not well is out.
                 "ill", "unwell", "sick", "illness", "flu", "fever", "cold", "covid",
                 "concussion", "sore throat", "chest infection", "hospital", "recovering",

                 # A countdown is not a sleep-needs question: "how many sleeps until my
                 # birthday" is asking for a number of nights, and answering it with the
                 # seven-to-nine hours guidance is the wrong subject entirely.
                 "sleeps until", "sleeps till", "sleeps to go", "sleeps left",
                 "sleeps is it", "sleeps before", "hours is it till", "hours until",
                 "hours till",
                 # a countdown to a birthday is not a nightly number of hours ("sleeps" cannot
                 # go here: it folds back onto "sleep" and would silence this entry entirely)
                 "birthday", "christmas",
                 # "always tired even when i sleep eight hours" wants the tiredness answer
                 "tired", "tiredness", "exhausted", "knackered", "fatigued")),
    # Snoring was a shrug on every line: the sleep entries all steer round it (cant-switch-off
    # and sleep-why both avoid "snoring") because it is a different question, and nobody had
    # taken it on. The partner and the loudness are in the key because that is how people say it.
    entry("snoring", (("snore", "snores", "snoring", "snored", "snorer"),
                      ("stop", "how", "why", "help", "prevent", "reduce", "less", "loud", "loudly",
                       "partner", "wife", "husband", "boyfriend", "girlfriend", "wake",
                       "wakes", "tips", "advice", "keep",
                       # "is it normal to snore" is the same question - whether to worry - and
                       # it names only one word from the subject side, so the judging words
                       # have to sit in the key for the line to score at all
                       "normal", "common", "usual", "ok", "bad", "worried", "worry",
                       "serious", "problem", "matter", "matters", "harm", "harmful")),
          "Most snoring is air whistling through a narrowed throat, so start with what widens it: "
          "sleep on your side, keep the last drink to three hours before bed, clear a blocked nose "
          "with a saline rinse or a strip, and lose a bit of weight if you have some to lose. If "
          "your partner hears you stop breathing or gasp, or you are tired all day, ask the GP "
          "about sleep apnoea - that one needs treating and a nose strip will not do it.",
          # "is it normal to snore" is the same question as "how do i stop snoring" - it is
          # asking whether to worry - so the judging words count as the ask too
          ask=("how", "stop", "what", "any", "help", "tips", "advice", "reduce", "prevent",
               "should", "is there", "why", "normal", "common", "usual", "ok", "bad",
               "worried", "worry", "serious", "problem", "matter", "matters", "harm",
               "harmful"),
          # a dog that snores, a baby, and a room that is too warm are other jobs
          avoid=("dog", "dogs", "puppy", "cat", "cats", "kitten", "baby", "babies", "newborn",
                 "toddler", "child", "children", "kid", "kids", "teeth", "grind", "grinding",
                 "apnoea", "cpap", "machine", "sleep talk", "talk in my sleep",
                 "paralysis", "nap", "dream", "dreams", "cot", "crib")),
    # A nap is a sleep question and the answer is about the clock, not about discipline.
    # Talking in your sleep is common and nothing to fix, and there was no entry for it: the
    # words went to the sneeze-or-snore rows and, on main, the bare phrase "i talk" in the
    # speaking-clearly key sent it voice exercises.
    entry("sleep-talking",
          (("sleep talking", "sleep talk", "sleeptalking", "talk in my sleep",
            "talking in my sleep", "talks in his sleep", "talks in her sleep",
            "talks in their sleep", "talk while asleep", "talking while asleep",
            "mumble in my sleep", "mumbling in my sleep", "shout in my sleep"),
           ("normal", "common", "why", "stop", "how", "harm", "harmful", "bad", "worry",
            "worried", "serious", "mean", "does it", "should", "is it")),
          "Sleep talking is common and almost always harmless: it happens in light sleep, it "
          "runs in families, and most people never know they do it. Nothing needs treating - "
          "keep the last drink early, cut late caffeine and get enough sleep, because it gets "
          "worse when someone is overtired or feverish. Ask the GP about it if the talking "
          "comes with acting out dreams or violent movement, since that pairing is worth "
          "checking for a sleep disorder.",
          # a bare report is the whole question: "i talk in my sleep" says it and asks nothing
          report=True,
          # a child who talks in their sleep, and a snorer, are other answers
          avoid=("baby", "babies", "newborn", "toddler", "my son", "my daughter", "my child",
                 "snore", "snoring", "snorer", "apnoea", "cpap")),

    entry("nap-afternoon",
          (("nap", "naps", "napping", "napped", "siesta", "forty winks"),
           # the nap itself has to be the question: "what about naps, should i cut them" after a
           # child's early waking is the child-sleep answer, and "should i" alone caught it
           ("afternoon", "good idea", "bad idea", "how long", "worth", "daytime", "lunchtime",
            "every day", "after lunch", "too long", "20 minutes", "help", "good for you",
            "bad for you", "take a nap", "benefit", "point",
            # "how do i nap properly" and "what is the best way to nap" say the nap twice and
            # name no benefit, so they were a shrug; the shape of the nap is this answer
            "properly", "proper", "best way", "right way")),
          "A short nap is worth having: 20 minutes, ideally before about 3pm, and set an alarm, "
          "because 90 minutes leaves you groggier than when you lay down. It helps most if you "
          "lost sleep the night before or you are driving later. Skip it if you already lie awake "
          "at night, and if you need one every afternoon for weeks, that is worth a word with the "
          "GP, especially with low mood, thirst or weight loss.",
          # a baby, a toddler and a bad night are other answers
          avoid=("baby", "babies", "newborn", "toddler", "my son", "my daughter", "my child",
                 "kids", "puppy", "night shift", "jet lag", "can't sleep", "cant sleep",
                 # an age is the child even when the line says "a 1 year old" and no other
                 # child word: "how long should a nap be for a 1 year old" was this card,
                 # which tells a parent of a toddler to set an alarm at 20 minutes.
                 "1 year old", "one year old", "2 year old", "two year old", "3 year old",
                 "three year old", "4 year old", "four year old", "5 year old",
                 "five year old", "months old", "18 months", "15 months", "6 months old")),

    # Getting to sleep is the other half of the night: the two entries above explain sleep and
    # how much of it is enough, and both step aside for "cant", "trouble" and "fall asleep", so
    # "how do i get to sleep faster" used to land on the search hedge.
    entry("sleep-onset",
          (("get to sleep", "fall asleep", "go to sleep", "nod off", "drop off", "drift off",
            "getting to sleep", "falling asleep"),
           ("fast", "faster", "quick", "quicker", "quickly", "sooner", "short", "shorter",
            "easier", "easy", "long", "longer", "ages", "hour", "hours", "cant", "can't",
            "cannot", "struggle", "takes", "hard", "help", "how", "tips", "advice", "what")),
          "Give yourself a run-up rather than trying to switch off: the same wake-up time every "
          "day, no caffeine after about two, the last hour dim with the phone out of reach, and a "
          "cool dark room. Falling asleep is a slope you slide down, so nothing you try harder at "
          "helps: if you are still awake after about twenty minutes, get up, sit somewhere dim "
          "with something dull, and go back when your eyes are heavy. Counting minutes on the "
          "clock is what keeps it going.",
          ask=("how", "what", "any", "anything", "help", "tips", "advice", "why", "should",
               "best", "faster", "quicker", "quickly", "cant", "can't", "want", "struggle",
               "takes", "need"),
          # a worry that keeps you awake is the cant-switch-off answer, and a child's bedtime,
          # a snoring partner and a real sleep disorder all belong to somebody else
          avoid=("overthinking", "overthink", "racing", "thoughts", "mind", "switch off",
                 "year old", "years old", "bedtime", "bed time", "put him to bed",
                 "put her to bed", "put them to bed", "school night", "school nights",
                 "worry", "worried", "worrying", "anxious", "anxiety", "stress", "stressed",
                 "baby", "babies", "newborn", "toddler", "kids", "child", "children",
                 "my son", "my daughter", "puppy", "cat", "dog", "snoring", "apnoea",
                 "apnea", "melatonin", "sleeping tablet", "sleeping tablets", "pregnant",
                 "shift work", "night shift", "jet lag", "time zone", "hangover", "died",
                 "funeral", "depressed", "suicidal", "out of bed", "red light", "phone",
                 # main's `sleep-how-to` is the general run-down of the same advice, and it is
                 # the right answer to the lines it keys: this entry is for the ones it misses
                 "sleep better", "sleeping better", "sleep well", "sleeping well", "good night",
                 "wind down", "sleep routine", "bedtime routine", "sleep hygiene", "sleep tips",
                 "tips for sleeping", "fall asleep faster", "fall asleep quicker",
                 "get to sleep faster", "help me fall asleep", "help me get to sleep")),
    # The 3am waking: short and common, and it used to get the hedge because the only entry with
    # "wake up" in it was the sleep-hours one, which steps aside for "waking" on purpose.
    entry("wake-at-night",
          (("wake up at", "waking up at", "wake at", "waking at", "woke up at", "woke at",
            # "im up at 3 every night" is the same report without the verb: it was "Thanks for
            # telling me - I'm here if you want to dig into any of that."
            "up at", "im up at", "i'm up at", "up every night", "up at night",
            "wake up in the night", "wake in the night", "waking in the night",
            "wake up in the middle of the night", "middle of the night", "wake up several times",
            "waking up several times", "wake up every night", "waking up every night",
            "cant get back to sleep", "can't get back to sleep", "cant get back off to sleep",
            # "how do i get back to sleep when i wake up" is the same night said as a question
            # about the next time it happens, and it got "Sure. What have you tried so far?"
            "get back to sleep", "get back off to sleep", "back to sleep",
            "get to sleep and stay asleep"),
           ("2", "3", "4", "5", "2am", "3am", "4am", "5am", "night", "nights",
            "why", "how", "stop", "always", "every", "again", "back to sleep", "repeat")),
          _night_waking,
          ask=("how", "why", "what", "should", "stop", "help", "any", "wake", "waking",
               "cant", "can't", "keep",
               # "im up at 3 every night" reports it and asks nothing, so the report words are
               # the ask here
               "up", "im", "i'm", "every night", "night", "nights", "every"),
          # a child or a pet waking is their answer, and a snorer, a weak bladder or a low morning
          # is a different problem with a different one
          avoid=("baby", "babies", "newborn", "toddler", "kids", "child", "children",
                 "year old", "years old", "bedtime", "bed time", "school night", "school nights",
                 "my son", "my daughter", "puppy", "cat", "dog", "snoring", "snore", "apnoea",
                 "apnea", "toilet", "pee", "wee", "bathroom", "thirsty", "pregnant",
                 "shift work", "night shift", "insomnia for years", "out of bed", "depressed",
                 "suicidal", "melatonin", "sleeping tablet", "sleeping tablets", "dying", "died",
                 # an early riser who cannot stay asleep past five is the body-clock answer on
                 # main ("that clockwork wake-up is your body clock"), and that one is right:
                 # this entry is for the small-hours waking, not for getting up too early
                 "too early", "up early", "wakes me early", "5am", "5 am", "5:30", "6am", "6 am",
                 "early riser", "wide awake at 5", "wake up early", "waking up early")),
    # "how do i fix my sleep pattern": the routine itself, which is different from how much sleep
    # and from lying awake, and was the hedge.
    entry("body-clock",
          (("sleep pattern", "sleep routine", "sleep schedule", "body clock", "circadian",
            "reset my sleep", "fix my sleep", "sort my sleep", "my sleep is", "sleeping pattern",
            "falling asleep late", "stay up too late", "staying up too late", "go to bed too late",
            "going to bed too late", "sleeping in late", "lie in at the weekend",
            "sleep in at the weekend", "night owl", "sleep in the day", "sleeping in the day",
            "sleep is all over the place", "sleep is a mess", "sleep is messed up",
            "sleep is shot", "my sleep is", "body clock is", "naps in the day", "get up earlier",
            "wake up earlier", "go to bed earlier", "sleep earlier", "wake earlier",
            # not "sleep better": main's `sleep-how-to` already answers that, and this entry
            # took "how do i sleep better" off it
            ),
           ("fix", "reset", "change", "sort", "better", "earlier", "later", "how", "what",
            "tips", "advice", "wrong", "messed", "mess", "routine", "pattern", "should",
            "help", "late", "always", "kids", "shot", "place")),
          "Anchor the wake-up time first and let the bedtime follow: get up at the same time every "
          "day, weekend included, and get outside into daylight within an hour of it, because "
          "morning light is what sets the clock. Then move bedtime fifteen minutes at a time, a "
          "couple of nights each, rather than an hour overnight. Keep naps under twenty minutes "
          "and early in the afternoon, skip caffeine after lunch while you shift it, and give it a "
          "week before it stops feeling like effort.",
          ask=("how", "what", "any", "help", "tips", "advice", "should", "fix", "reset",
               "change", "sort", "better", "messed", "mess", "wrong", "late", "shot",
               "all over", "out of whack"),
          avoid=("baby", "babies", "newborn", "toddler", "kids", "child", "children",
                 "year old", "years old", "bedtime", "bed time", "school night", "school nights",
                 "my son", "my daughter", "teenager", "puppy", "cat", "dog", "shift work",
                 "night shift", "jet lag", "time zone", "time difference", "melatonin",
                 "pregnant", "snoring", "apnoea", "apnea", "insomnia for years", "depressed",
                 "suicidal", "out of bed", "dying", "died", "funeral")),
    entry("headache-why", (("headache", "headaches", "migraine", "migraines", "head hurts",
                            "head is pounding", "sore head"),
                           ("why", "cause", "causes", "happen", "happens", "what", "every day",
                            "often", "always", "behind", "one side", "sudden", "bad")),
          "Most headaches are tension: muscles in the neck, jaw and scalp tighten with stress, "
          "screens, skipped meals or poor sleep, and the pain sits like a band round the head. "
          "Migraine is different: throbbing, often on one side, with nausea or light sensitivity, "
          "and regular or sudden worst-ever headaches should be checked by a doctor.",
          # "keep" used to stand this row down for every "keep" line, and "why do i keep getting
          # headaches" is exactly the pattern question it answers: it fell through to the chat
          # module's advice for one bad headache. A recurring headache is the why row's question,
          # and "keeps getting" is a complaint that keeps coming back rather than the fault verb
          # (see lookup._keeps_failing), so the shelf-life rows cannot reach these lines either.
          avoid=("take", "medicine", "medication", "paracetamol", "ibuprofen", "painkiller",
                 "painkillers", "relief", "help", "cure", "rid", "stop", "tablet", "tablets",
                 "my", "these", "behind", "desk", "at work", "should i", "worried")),
    entry("bald", (("bald", "balding", "baldness"),
                   ("men", "man", "why", "happen", "genetic", "male")),
          "Male pattern baldness is mostly inherited: hair follicles on top of the head become "
          "sensitive to testosterone by-products and shrink, so hairs get thinner and eventually "
          "stop. It is not caused by hats, washing or stress alone, and treatments only work while "
          "you keep using them.",
          avoid=("women", "woman")),
    entry("hair-loss", (("hair fall out", "hair falling out", "hair falls out", "hair is falling out", "losing my hair",
                         "losing hair", "thinning hair", "thinning", "shedding hair", "shedding",
                         "hair loss", "hair coming out", "hair is coming out", "hair come out",
                         "hair comes out"),
                        ("why", "happen", "cause", "normal", "much", "stop", "prevent", "my",
                         "women", "woman")),
          "Hair loss is usually a pattern that runs in families: follicles on top of the head "
          "shrink under testosterone by-products, so hairs get thinner and eventually stop. "
          "Sudden or patchy shedding is more often stress, illness, childbirth, iron or thyroid "
          "trouble, so see a GP if it is fast or patchy; minoxidil helps pattern loss but only "
          "while you keep using it.",
          # a dog or cat losing hair is an animal question, and a hair that comes out grey is
          # the colour question: neither wants the human hair-loss answer
          avoid=("men", "man", "male", "dog", "dogs", "cat", "cats", "pet", "pets", "puppy",
                 "kitten", "rabbit", "grey", "gray", "white", "colour", "color",
                 # hair lost to cancer treatment is not pattern baldness, and thinning paint,
                 # sauce or a shedding snake is not human hair
                 "chemo", "chemotherapy", "radiotherapy", "cancer",
                 "paint", "varnish", "sauce", "gravy", "soup",
                 "snake", "snakes", "lizard", "lizards", "reptile", "reptiles", "bird", "birds"),
          # "thinning" and "shedding" alone also describe thin skin or a thin sauce, so the
          # line has to mention hair before this answer applies.
          ask=("hair",)),
    entry("fish-sleep", (("fish", "fishes"), ("sleep", "sleeping", "rest", "night", "asleep")),
          "Fish rest but do not sleep the way we do: most have no eyelids, so they hover still in "
          "a sheltered spot, often at night, with their gills still moving. Some, like sharks, "
          "keep swimming the whole time so water keeps flowing over their gills."),
    # --- the greenhouse, climate and the atmosphere -----------------------
    entry("greenhouse-effect", (("greenhouse effect", "greenhouse gas", "greenhouse gases"),
                                ("what", "work", "works", "how", "why", "trap", "explain",
                                 "cause", "causes", "is")),
          "Gases in the air, mainly carbon dioxide and water vapour, let sunlight in but absorb "
          "the heat that bounces back off the ground, much like glass in a greenhouse. That keeps the "
          "Earth about 33C warmer than it would be. Burning coal, oil and gas adds more of those "
          "gases, so more heat is trapped and the planet warms."),
    entry("ozone-layer", (("ozone layer", "ozone"), ("what", "why", "hole", "protect",
                                                       "damage", "harm", "do")),
          "The ozone layer is a thin band of ozone high in the atmosphere that absorbs most of the "
          "Sun's ultraviolet light, which would otherwise burn skin and damage crops. CFCs thinned "
          "it; they were banned and it is slowly healing."),
    entry("acid-rain", (("acid rain",), ("what", "why", "cause", "causes", "happen", "bad")),
          "Acid rain forms when sulphur dioxide and nitrogen oxides from burning coal and oil mix "
          "with water in the air and fall as weak acid. It harms trees and lakes; filters on power "
          "stations and cleaner fuel have cut it a lot since the 1980s."),
    # "the water cycle" on its own, and "how does the water cycle work", reached nothing at all
    # (the plan card and the dry-eye card took them): the subject spoken as a name is the whole
    # question, so the phrasings go in the first part and the ask word follows in the second.
    entry("water-cycle", (("water cycle", "the water cycle", "how does the water cycle",
                           "how the water cycle", "why does the water cycle",
                           "what is the water cycle", "explain the water cycle",
                           "water cycle work", "water cycle works", "water cycle for kids",
                           "water cycle for a child"),
                          ("what", "how", "work", "works", "explain", "cycle", "is", "why",
                           "mean", "means")),
          "Water evaporates from the sea and land, rises and cools into clouds, falls as rain or "
          "snow, and runs back to the sea: the same water goes round and round. Sunlight drives it "
          "and gravity brings it back down.",
          # "water" and "cycle" are common enough in health and planning that the row tied with
          # them and lost; the phrase in its key means it is only ever about this one thing.
          # A project or a poster about it is the schoolwork row's line, not a request for the
          # facts, and that row answered it before this one could.
          bias=2, avoid=("project", "projects", "poster", "presentation", "assignment",
                         "essay", "coursework", "revision", "exam")),

    # --- space and the sky ------------------------------------------------
    entry("sun-size", ("sun", ("big", "large", "size", "wide", "compared", "how")),
          "The Sun is about 1.4 million km across, roughly 109 Earths side by side, and you could "
          "fit about 1.3 million Earths inside it. It looks small only because it is 150 million "
          "km away.", ask=("how big", "how large", "size", "bigger", "compared")),
    # The size of the Earth had no row of its own: the sun-size card is keyed on "sun", so
    # "how big is the earth" reached nothing. One row per body whose size people ask for.
    entry("earth-size", ("earth", ("big", "large", "size", "wide", "across", "diameter",
                                   "circumference", "weigh", "weighs", "heavy", "mass", "how",
                                   "compared")),
          "The Earth is about 12,742 km across (12,756 km at the equator, 12,714 km from pole to "
          "pole) and 40,008 km round the poles, a little less than the 40,075 km round the "
          "equator because the spin bulges it out. It weighs about 6 billion trillion tonnes."),
    entry("eclipse", (("eclipse", "eclipses"), ("solar", "lunar", "moon", "sun", "what",
                                                  "why", "happen", "explain")),
          "An eclipse happens when the Sun, Earth and Moon line up. In a solar eclipse the Moon "
          "passes between us and the Sun and covers it; in a lunar eclipse the Earth's shadow "
          "falls on the Moon, which turns a dull red."),
    entry("dark-matter", (("dark matter",), ("what", "made", "universe", "space", "unknown")),
          "Dark matter is the name for mass we cannot see but can measure: galaxies spin and bend "
          "light as if they hold far more matter than the stars show. Nobody yet knows what it is "
          "made of, which is why it is one of the big open questions."),
    entry("comet", (("comet", "comets"), ("what", "why", "tail", "made", "shooting", "shoot")),
          "A comet is a lump of ice, dust and rock left over from the birth of the solar system. "
          "Near the Sun its ice turns to gas, and the solar wind blows that gas and dust into a "
          "long tail pointing away from the Sun."),
    # "take" stays out of the key: it is the verb of the medicine question too ("what should i
    # take for a cold"), and a second use of it in this domain cost cold-remedy its rarity weight.
    entry("mars-travel", ("mars", ("how long", "get", "travel", "reach", "trip", "time",
                                   "journey")),
          "A trip to Mars takes about seven months each way with current rockets, because the "
          "planets are so far apart. Missions wait for a launch window about every 26 months, "
          "when Earth and Mars are lined up best.",
          ask=("how long", "get", "take", "travel", "reach", "trip"),
          # A generic follow-up row keys on "it" and "how long" with a bias, so in some readings
          # "how long does it take to get to mars" lost its own answer. A named planet is never
          # the jar that follow-up is about.
          bias=4,
          # "how long is a year on mars" is about the planet, not the journey: mars-year owns the
          # year/day words, so this one steps back when the line has them.
          avoid=("year", "years", "day", "days", "sol", "seasons", "length")),
    entry("mars-year", ("mars", ("year", "years", "day", "days", "sol", "seasons", "months")),
          "A year on Mars lasts 687 Earth days, nearly two of ours, because Mars is further from "
          "the Sun and moves more slowly round it. A Martian day is only about 40 minutes longer "
          "than an Earth day."),
    entry("mars-distance", (("mars", "red planet"),
                            ("far", "distance", "away", "miles", "km", "kilometres",
                             "kilometers")),
          "Mars is about 225 million km from Earth on average, but the gap swings from roughly 55 "
          "million to 400 million km as the two planets move round the Sun. That is why a mission "
          "leaves only every 26 months, and why radio messages take between 3 and 22 minutes each "
          "way.",
          ask=("how far", "far", "distance", "away", "miles", "km", "kilometres", "kilometers"),
          # "away" is also a word in the travel month row's ask, and "mars" is a typo-form of
          # March, so "how far away is mars" was answered with a month's holiday advice.
          bias=3,
          avoid=("travel", "trip", "journey", "get there", "how long does it take", "year",
                 "day", "moon", "rocket", "launch")),
    # "burning", not "burn": another entry keys on "burn" alone, and a second user of a word
    # costs that entry its rarity weight, which handed "why does spicy food burn" to the
    # burnt-pan answer. The loose forms still match "burn" in a line.
    entry("calorie", (("calorie", "calories", "kcal"), ("what", "mean", "burning", "burned",
                                                           "food", "energy", "need", "eat", "day")),
          "A calorie is a unit of energy; the calories on food labels are really kilocalories, the "
          "energy to raise 1 kg of water by 1C. An average adult needs roughly 2,000 to 2,500 a "
          "day, and eating fewer than you burn is what loses weight."),
    entry("helium-voice", (("helium",), ("voice", "high", "squeaky", "why", "balloon")),
          "Helium does not raise your voice: sound travels about three times faster in it than in "
          "air, which makes the echoes in your throat ring higher. Your vocal cords move exactly "
          "as before, and it wears off in seconds."),
    entry("rust", (("rust", "rusty", "rusting"), ("what", "why", "form", "forms", "metal",
                                                     "iron", "stop")),
          "Rust is iron oxide: iron reacts with oxygen and water in the air and slowly turns into a "
          "flaky orange layer that no longer holds together. Paint, oil or simply keeping the metal "
          "dry keeps water away and stops it."),
    entry("batteries", (("battery", "batteries"), ("work", "works", "how", "store", "stored",
                                                     "charge", "electricity", "why")),
          "A battery turns chemical energy into electricity: a reaction inside pushes electrons "
          "from one terminal to the other, and the circuit carries them round to do work. A "
          "rechargeable one reverses that reaction when you plug it in.",
          # "how much does a new phone battery cost" and "where do I replace the battery" are
          # other entries' answers; "why" in the key made this one take them.
          avoid=("alarm", "smoke", "recycle", "recycling", "bin", "dispose", "test", "cost",
                 "price", "how much", "replace", "replacement", "phone", "laptop", "car",
                 # a battery that drains or loses charge is the phone's question, and the
                 # chemistry answer is not what that person asked for. "dies", "dying" and
                 # "died" are not here: "why does a battery die" asks how a cell works, and the
                 # word alone cannot tell the two apart, so the phone's own words do the work.
                 "drain", "drains", "draining", "overnight",
                 "loses charge", "losing charge", "battery life", "last the day", "flat",
                 # a watch battery is a part to fit, not the chemistry of a cell
                 "watch", "watches", "wristwatch", "strap", "fob", "keyring", "hearing aid",
                 # a thermostat's battery is a cell to change in a house, and this answer is
                 # the chemistry of a cell in general ("how do i change the thermostat battery"
                 # was told that a battery turns chemical energy into electricity)
                 "thermostat", "thermostats", "boiler", "radiator", "radiators", "heating",
                 "smoke detector", "carbon monoxide",
                 # a battery to change in a remote or a set-top box is the same kind of part:
                 # "how do i change the batteries in my tv remote" wants the tray, not the cell
                 "remote", "remote control", "zapper", "telly", "tv remote", "set-top")),
    # "how" and "cook" are left out of the key on purpose: "how do i make porridge in the
    # microwave" is a porridge question, and it was getting this answer.
    # "can i put metal in the microwave" and "is foil safe in a microwave" are the one microwave
    # question with a fire in the answer, and it was a shrug: nothing in the key named the metal.
    entry("microwave-metal",
          (("microwave", "microwaves", "microwave oven"),
           ("metal", "foil", "tinfoil", "tin foil", "aluminium", "aluminum", "fork", "forks",
            "spoon", "spoons", "knife", "cutlery", "spark", "sparks", "sparked", "sparking",
            "gold rim", "gold rims", "takeaway carton", "carton", "crisp packet", "twist tie")),
          "No - metal reflects the microwaves and the tips of it spark, which can scorch the wall or "
          "start a fire, so keep forks, foil, gold-rimmed plates and takeaway cartons with metal "
          "handles out. If it has already sparked, switch it off and unplug it before you touch "
          "anything, and let it cool. A microwave with a burnt patch on the inside wall is worth "
          "replacing rather than carrying on with.",
          ask=("microwave", "microwaves", "microwave oven"),
          # a microwave that has already sparked, smoked or burned is the appliance-fire answer,
          # which says keep the door shut and ring 999; a microwave that will not heat is the
          # repair question. Neither is this one.
          avoid=("not heating", "wont heat", "won't heat", "stopped working", "not working",
                 "repair", "fix", "sparked", "sparking", "smoking", "smoke", "flames",
                 "on fire", "caught fire", "burnt", "burning"),
          bias=1),
    entry("microwave", (("microwave", "microwaves"),
                        ("heat", "heats", "heating", "work", "works", "why", "radioactive",
                         "radiation", "dangerous", "safe", "evenly", "uneven", "spin")),
          "A microwave floods food with microwaves, which make water molecules spin and rub against "
          "each other, and that friction heats the food. It does not make the food radioactive, and "
          "it heats unevenly, so stir or leave it to stand.",
          # metal is the fire answer above, not the how-it-works one
          avoid=("spark", "sparks", "sparking", "broken", "not working", "metal", "foil",
                 "tinfoil", "tin foil", "aluminium", "cutlery", "fork", "forks",
                 # a microwave that will not heat is the repair question, and "heating" and
                 # "heat" are in this key as how-it-works words: "my microwave isnt heating"
                 # was told how a magnetron makes water molecules spin instead of what to do
                 "not heating", "isnt heating", "isn't heating", "not heating up",
                 "isnt heating up", "isn't heating up", "wont heat", "won't heat",
                 "wont heat up", "won't heat up", "doesnt heat", "doesn't heat",
                 "no heat", "stopped heating", "not getting hot", "not hot", "stays cold",
                 "cold food", "heats nothing", "not warming", "faulty", "repair", "mend",
                 "dead", "died", "stopped working",
                 # How a microwave works is a question about the appliance. A line that asks
                 # about the food going into it - is it safe to reheat, does reheating kill the
                 # bacteria, how hot should it be - is the reheating question, and this card
                 # answered it with a magnetron and spinning water molecules: "is it safe to
                 # reheat chicken in the microwave" got the physics and no word about the
                 # chicken.
                 "reheat", "reheats", "reheating", "reheated", "warm up", "warms up",
                 "warming up", "warmed up", "heat up", "heats up", "heating up", "heated up",
                 "leftover", "leftovers", "left over", "bacteria", "food poisoning",
                 "piping hot", "safe to eat", "is it safe to eat"),
          # "why does my microwave heat unevenly" scored level with the summer answer on "why"
          # and "heat", and the tie used to fall this way only because "microwave" was a word
          # one entry in the domain used. The metal entry above is the second, so the tie needs
          # saying out loud: a line that names a microwave is the microwave question.
          bias=1),
    entry("sink-float", (("float", "floats", "floating", "sink", "sinks", "sinking"),
                         ("why", "things", "object", "water", "does", "some")),
          "Something floats when it is less dense than the water it pushes aside, and sinks when it "
          "is denser. That is why a steel ship floats: it is mostly air inside, so the whole thing "
          "weighs less than the water it displaces.",
          # "sink" alone is a kitchen word as well as a physics one: "water is not going down the
          # sink" was answered with density, and the plumbing words say which sink it is
          avoid=("drain", "drains", "draining", "plughole", "plug hole", "blocked", "unblock",
                 "unblocking", "tap", "taps", "pipe", "pipes", "plumber", "going down",
                 "not going down", "waste", "trap", "water down",
                 # the kitchen sink is also the thing that smells: "why does my sink smell" was
                 # answered with density, because "why" and "sink" are the whole of this key.
                 "smell", "smells", "smelly", "stink", "stinks", "odour", "odor", "clean",
                 "cleaning", "dirty", "grime", "grease", "limescale", "stain", "stains",
                 "bicarbonate", "scrub", "wash up", "washing up",
                 # a bake that drops is not buoyancy: "why does my bread sink in the middle"
                 # was told why a steel ship floats, and the dish is the word that says which
                 # kind of sinking it is
                 "bread", "loaf", "loaves", "cake", "cakes", "dough", "batter", "pastry",
                 "sponge", "souffle", "baked", "bake", "baking", "oven", "risen", "recipe")),
    entry("salt-ice", (("salt", "salting", "rock salt", "grit", "gritting"),
                       ("ice", "icy", "melt", "melts", "road", "roads", "driveway", "why")),
          "Salt lowers the temperature at which water freezes, so ice on a road melts even when the "
          "air is below 0C. It only works down to about -6C, which is why councils grit before the "
          "coldest nights.",
          avoid=("sea", "ocean", "salt water", "food", "recipe", "cook", "cooking", "eat",
                 "diet", "blood pressure", "bath", "swimming", "softener", "water softener"),
          bias=3),
    entry("friction", (("friction",), ("what", "why", "work", "works", "slow", "heat",
                                        "explain")),
          "Friction is the force between two surfaces that rub together, and it slows movement and "
          "turns the lost energy into heat. It is why brakes get hot and why oil and smooth surfaces "
          "make machines last longer."),

    # --- living things ----------------------------------------------------
    entry("plant-needs-water",
          (("plant", "plants", "houseplant", "house plant", "pot plant", "pot", "soil", "compost"),
           ("needs water", "need water", "thirsty", "tell if", "how often", "when to water",
            "watering", "water", "dry", "drooping")),
          "Push a finger about 2cm into the soil: water it if the soil is dry at that depth, and "
          "wait a day or two if it is still damp. A pot tells you by weight as well, because a "
          "light pot is a dry pot, and a thirsty plant droops and then perks up within a day of a "
          "drink. Water until it runs out of the drainage holes and empty the saucer, because "
          "roots left standing in water rot.",
          # "why do plants need water" is the transport answer, and a named plant has its own
          # care, so this one only takes the tell-me-when shape. (Not PESTS_AND_CARE as a whole:
          # it carries "water my" and "how often", which are the very lines this entry is for.)
          ask=("tell", "know", "how often", "when", "should i", "how do i", "how can i",
               "needs", "need", "thirsty", "dry"),
          avoid=("why", "roots", "stem", "drink", "absorb", "tree", "garden", "lawn", "grass",
                 "basil", "tomato", "potato", "monstera", "orchid", "cactus", "succulent", "fern",
                 "chilli", "lavender", "hydrangea", "slug", "slugs", "pest", "pests", "insect",
                 "insects", "repot", "fertiliser", "fertilizer", "prune", "dead", "died", "dying",
                 "wilt", "wilted", "leaves", "leaf",
                 # feeding the plant is its own question: "how often should i feed my plants" was
                 # getting the watering answer because both ask "how often"
                 "feed", "feeds", "feeding", "plant food", "nutrients", "food")),
    entry("plants-drink", (("roots", "root", "plant", "plants", "planting"),
                            ("water", "drink", "absorb", "absorbed", "travels")),
          "Plants take up water through their roots, and it is pulled up narrow tubes in the stem "
          "by evaporation from the leaves. That is why a cut flower wilts and why overwatering "
          "drowns roots that need air.",
          ask=("how", "where", "drink", "absorb", "roots", "up"),
          # "how can I tell if my plant needs water" is a question about the pot, not about how
          # water travels up a stem: plant-needs-water answers it.
          # The tap-water entry also has "drink" and "water" in its key, and wins the tie on
          # rarity: this fact asks how water gets up a plant, so it keeps that line.
          # a cutting in water is a propagation question, not a fact about how water travels
          avoid=WATERING + ("needs water", "need water", "tell", "tell if", "thirsty", "drooping",
                            "cutting", "cuttings", "propagate", "propagating", "root it",
                            "root a cutting"),
          bias=4),
    entry("fireflies", (("firefly", "fireflies", "glow worm", "glowworm"), ("glow", "light",
                                                                              "why", "how", "shine")),
          "Fireflies glow through a chemical reaction in their tail: luciferin reacts with oxygen "
          "and gives off light with almost no heat. They use it to attract mates, and each species "
          "has its own flash pattern."),
    entry("food-chain", (("food chain", "food web"), ("what", "how", "work", "works", "mean")),
          "A food chain is the line of who eats whom, starting with a plant that makes its own food "
          "and ending with a predator. Energy is lost at every step, which is why top predators "
          "are few and a chain rarely has more than four or five links."),
    entry("fossils", (("fossil", "fossils"), ("what", "how", "form", "formed", "made", "become",
                                                "dinosaur")),
          "A fossil forms when a dead animal or plant is buried quickly and its hard parts are "
          "slowly replaced by minerals from the surrounding rock over thousands of years. Most "
          "living things rot away entirely, which is why fossils are rare."),
    entry("spider-web", (("spider", "spiders"), ("web", "webs", "silk", "make", "makes",
                                                  "how")),
          "Spiders spin silk from glands in the abdomen and pull it out with their back legs, "
          "laying a frame first and then a spiral inside it. The silk is stronger than steel for its "
          "weight, and many spiders hunt without a web at all.",
          # a spider plant is not a spider: "how do i propagate a spider plant" was a question
          # about silk, and the garden table's take-cuttings row answers it
          avoid=("house", "home", "inside", "bath", "bedroom", "get rid",
                 "spider plant", "spider plants", "houseplant", "houseplants", "propagate",
                 "propagating", "cutting", "cuttings", "water it", "repot")),
    entry("duck-float", (("duck", "ducks"), ("float", "floats", "water", "why", "swim")),
          "Ducks float because their bodies are light and their feathers trap air, while a gland "
          "near the tail supplies oil that keeps the water out. Their bones are hollow too, so the "
          "whole bird is far less dense than the water it sits in."),
    entry("crocodile-alligator", (("crocodile", "crocodiles"), ("alligator", "difference",
                                                                "between", "vs")),
          "Crocodiles have narrow, V-shaped snouts and their fourth tooth shows when the mouth is "
          "shut; alligators have broad, U-shaped snouts and it stays hidden. Crocodiles are also the "
          "ones that tolerate salt water."),
    entry("mosquito", (("mosquito", "mosquitoes", "mosquitos", "midge", "midges"),
                       ("why", "bite", "bites", "bitten", "itch", "some", "me", "attract")),
          "Mosquitoes find you by the carbon dioxide you breathe out, your body heat and the "
          "chemicals on your skin, so they are drawn to some people more than others. Covering up "
          "and a repellent with DEET or picaridin are what actually keep them off."),

    # --- earth and water --------------------------------------------------
    entry("tsunami", (("tsunami", "tidal wave", "tidal waves"), ("what", "why", "cause", "causes",
                                                                  "happen", "wave")),
          "A tsunami is a series of waves usually set off by an earthquake under the sea, which "
          "lifts a whole column of water. Out at sea they are barely noticeable, but they steepen "
          "as they reach shallow water; if the sea suddenly pulls back, get to high ground."),
    entry("leap-year", (("leap year", "leap years"), ("why", "what", "when", "have", "366",
                                                       "extra")),
          "A year is about 365.24 days long, so every four years we add 29 February to keep the "
          "calendar in step with the seasons. Century years skip it unless they divide by 400, "
          "which trims the last bit of error."),
    entry("year-length", (("year",),
                          ("365", "why", "how long", "length", "days")),
          "A year is 365 days because that is roughly how long the Earth takes to go round the "
          "Sun once: 365.24 days. The extra quarter day is why we add a leap day every four years, "
          "so the calendar stays in step with the seasons.",
          ask=("365", "why", "how long", "length"),
          avoid=("leap", "new year", "tax year", "school year", "academic year", "birthday",
                 "age", "resolution", "christmas", "month", "months", "12 months")),
    entry("time-zones", (("time zone", "time zones", "time difference", "time differences"),
                         ("why", "what", "exist", "different", "hours")),
          "Time zones exist because the Earth turns: noon is when the Sun is highest, and that "
          "happens at a different moment in each place. The world is split into 24 zones of about "
          "an hour, so the clock roughly matches daylight; some countries bend the borders or use "
          "half-hour zones.",
          ask=("why", "what", "exist", "different", "hours", "how"),
          avoid=("jet lag", "flight", "travel", "call", "meeting", "zoom")),
    entry("universe-age", (("universe",), ("old", "age", "big", "how", "years", "billion",
                                           "expand", "expanding")),
          "The universe is about 13.8 billion years old, measured from how fast it is expanding "
          "and the oldest light we can see. It has no edge or centre that we know of; space itself "
          "stretches between the galaxies.",
          ask=("how old", "age", "how big", "when", "expand", "expanding", "billion")),
    entry("earth-inside", (("earth",), ("made", "inside", "core", "layers", "what", "crust",
                                        "mantle", "composition")),
          "The Earth is layered: a thin rocky crust, a hot slow-flowing mantle, a liquid outer core "
          "of iron and nickel, and a solid inner core. The churning iron outer core is what makes "
          "the magnetic field that keeps the solar wind off us.",
          ask=("what", "made", "inside", "core", "layers", "crust", "mantle")),
    entry("dinosaurs", (("dinosaur", "dinosaurs"), ("die", "died", "extinct", "extinction", "why",
                                                     "disappear", "kill", "killed", "gone", "live",
                                                     "lived", "long ago", "how long", "when",
                                                     "era", "period", "old", "million years")),
          _dinosaurs),
    # --- the everyday health questions, after the mundane and before the doctor -------
    # These are the small things a person handles at home. Each one stays out of the way of a
    # real emergency (a chest that is tight, a throat that will not swallow, a pet's cut): the
    # safety domain owns those lines, and this batch only answers what the person can do today.
    entry("vitamin-d", (("vitamin d", "vit d"),
                        ("winter", "dark", "october", "november", "december", "january", "february",
                         "march", "need", "should", "sun", "sunlight", "not enough")),
          "Take 10 micrograms (400 IU) of vitamin D every day through autumn and winter, roughly "
          "October to March: the sun is too low in the sky here for your skin to make it, however "
          "grey or bright the day is. From April to September, short spells outside with hands and "
          "face uncovered is enough for most people, and oily fish, eggs and fortified cereal help "
          "the rest of the year.",
          # A supplement question is not a vitamin D question: iron, calcium and the rest have
          # their own answers, so a bare "should i take supplements" passes.
          avoid=("iron", "calcium", "folic", "folate", "magnesium", "zinc", "multivitamin",
                 "multivitamins", "multivit", "protein", "creatine", "collagen", "omega", "fish oil",
                 "b12", "pregnant", "pregnancy", "deficiency", "deficient")),
    entry("stye", (("stye", "styes",
                    # "i have a sty" is the same complaint misspelt, and it was a nod
                    "sty",
                    "lump on my eyelid", "bump on my eyelid", "eyelid lump",
                    "chalazion", "lash line"),
                   ("get rid", "gone", "go away", "treat", "help", "what", "drain", "red",
                    "should i",
                    # A stye is reported as a lump far more often than it is asked about, and
                    # the plain report ("i have a stye", "my eyelid is swollen", "a hard lump on
                    # my eyelid") carries no question word at all. A stye or lid word in the
                    # first group is what makes these safe to share.
                    "have", "has", "had", "ive", "i've", "got", "my", "is", "are", "im",
                    "i'm", "it", "this", "lump", "bump", "pimple", "spot", "hard", "pea",
                    "swollen", "tender", "sore", "painful", "blocked", "how long", "last")),
          "Hold a warm, clean flannel against it for ten minutes, three or four times a day: that "
          "helps it drain, usually within two weeks. Don't squeeze it, and leave off eye make-up "
          "and contact lenses until it has gone. A hard, painless lump on the lid is a chalazion "
          "and wants the same warmth. See a pharmacist or GP if it has not settled in a week, or "
          "the lid is red and swollen.",
          # The two things that look like a stye and are other answers: a crusty red eye and a
          # twitching lid. `red-eye` owns the first and `eye-twitch` the second.
          avoid=("twitch", "twitching", "itchy", "itching", "sticky", "crusty", "gunky",
                 "watering", "watery", "gritty", "dry", "contact lens", "contacts", "mascara",
                 "makeup", "test", "glasses", "screen", "sleep", "tired", "dog", "cat",
                 "puppy")),
    entry("cold-sore", (("cold sore", "cold sores", "sore on my lip"),
                        ("get rid", "treat", "help", "stop", "first", "tingle", "spread", "how",
                         "what", "cream", "lip")),
          "Start aciclovir cream from the pharmacy at the first tingle and keep going for five "
          "days: caught early, it shortens the sore. It stays contagious until it has crusted over, "
          "so don't share towels, cups or lip balm, and don't pick it. Keep it away from newborn "
          "babies, who need a doctor straight away if one appears on them."),
    entry("hangover-morning", (("hangover", "hungover", "drank too much", "too much to drink",
                        "drank too much alcohol", "too much wine", "too much beer",
                        # "how do i sober up" is the same question asked from inside the evening,
                        # and there was no row for it. The abstinence lines ("i have been sober
                        # for a year") are fenced below, because a sober year is not a hangover.
                        "sober up", "sobering up", "get sober", "sober", "sobered",
                        "still drunk", "still pissed", "still tipsy"),
                       ("help", "cure", "get rid", "best", "what", "how", "water", "stop",
                        "avoid", "morning")),
          _hangover,
          # "i drank too much coffee" is not a hangover: coffee, water and sugar are not alcohol.
          avoid=("coffee", "tea", "water", "caffeine", "sugar", "juice", "milk", "fizzy",
                 "squash",
                 # a sober month, a sober year and a sober app are the giving-up-drink
                 # question, and "can i drive while still drunk" is the driving one
                 "sober for", "sober since", "years sober", "months sober", "weeks sober",
                 "days sober", "sober app", "gave up drinking", "quit drinking", "stop drinking",
                 "drive", "driving", "the car")),
    entry("teeth-grinding", (("grind", "grinding", "bruxism", "clench", "clenching"),
                             ("teeth", "jaw", "night", "sleep", "stop", "dentist", "morning")),
          _grinding,
          # "what is bruxism" names the thing and asks for it, and no other row knows the word:
          # the definition branch of the reply answers that shape.
          explain=True),
    entry("knuckles", (("knuckle", "knuckles", "crack", "cracking", "clicking"),
                       ("bad", "harm", "damage", "arthritis", "hurt", "why", "habit", "cause",
                        "bad for")),
          "No: the pop is gas coming out of the fluid in the joint, and the studies that have "
          "looked have found no link between cracking your knuckles and arthritis. Forcing a joint "
          "can make it sore or swollen, so if one clicks with real pain rather than a clean pop, "
          "get it looked at.",
          # a bare "clicking" is a car, a door or a machine as often as a joint: the answer is
          # about knuckles, so the line has to name one or say cracking. "is that bad" after
          # "my cars making a clicking noise when i brake" must not get a lesson on joints.
          ask=("knuckle", "knuckles", "crack", "cracking", "cracked"),
          # "why does my knee click" is about a knee: it needs its own answer, not this one.
          avoid=("knee", "knees", "ankle", "hip", "hips", "elbow", "shoulder", "jaw", "neck",
                 "back", "wrist",
                 # "why do my eggs crack when boiling" is an egg question: the word crack is a
                 # shell, a mug, a wall, a voice, a whip or a joke as often as it is a knuckle.
                 "egg", "eggs", "shell", "boil", "boiling", "boiled", "pan", "pot",
                 # "why do my carrots crack" is a root splitting in dry soil, not a joint: the
                 # vegetables are named here because the row keys the word "crack" itself
                 "carrot", "carrots", "parsnip", "parsnips", "beetroot", "radish", "radishes",
                 "turnip", "turnips", "swede", "celery", "cucumber", "cucumbers",
                 "voice", "throat", "lip", "lips", "skin", "hands", "heels", "heel",
                 "mug", "cup", "plate", "bowl", "glass", "window", "screen", "phone",
                 "wall", "walls", "ceiling", "tile", "tiles", "plaster", "pavement", "road",
                 "driveway", "brick", "concrete", "pipe", "whip", "meringue",
                 "batter", "pastry", "dough", "bread", "cake", "biscuit",
                 # ... and a cracked cheesecake, tart or brownie is the bake's own question
                 "cheesecake", "cheesecakes", "tart", "tarts", "choux", "macaron", "macarons",
                 "brownie", "brownies", "ganache", "pie", "loaf", "scone", "scones",
                 # "my knuckles hurt" is a pain question, not a cracking one
                 "hurt", "hurts", "hurting", "pain", "painful", "sore", "swollen", "aching",
                 "ache", "aches",
                 # the dry-skin entry has "knuckles" and "cracking" in its own key, so it was
                 # winning every knuckle question: dry skin keeps the dry lines, this keeps the
                 # cracking ones
                 "dry", "drier", "dryness", "flaky", "flaking", "chapped", "moisturiser",
                 "moisturizer", "emollient"),
          bias=2),
    entry("eye-twitch", (("eye", "eyelid"),
                         ("twitch", "twitching", "flicker", "flickering", "ticking", "spasm",
                          "jumping", "tics")),
          "A twitching eyelid is usually tiredness, caffeine or stress, and it settles by itself "
          "within a few days to a couple of weeks. Sleep more, ease off the coffee, and use "
          "lubricating drops if your eyes are dry from screens. See a GP if the twitch spreads "
          "down that side of your face, or the eye closes on its own."),
    entry("bruise", (("bruise", "bruised", "bruising"),
                     ("why", "treat", "treatment", "help", "get rid", "how", "fast", "heal",
                      "appear", "randomly", "explain", "gone",
                      # "i have a bruise that wont go away" was a chat line: the key had "gone"
                      # but never "go away", so the one shape where a GP matters did not match
                      "go away", "wont go", "not going", "still there", "lasts", "lasting",
                      "weeks", "months", "stay",
                      # a bruise that is spreading is its own worry and the row held no word
                      # for it: "is it normal for a bruise to spread" and "i have a bruise that
                      # keeps growing" were both answered with nothing at all
                      "spread", "spreading", "spreads", "growing", "bigger", "larger",
                      "getting bigger", "keeps growing",
                      # "a bruise that doesnt fade" had no ask word the row held either, and
                      # fading is the shape of the line that ends with a blood test
                      "fade", "fading", "fades", "doesnt fade", "not fading",
                      # "bruise on my arm hurts", "i bruise really easily" and "my bruise is
                      # going yellow" name the bruise and the thing they want explained, and
                      # none of those words was in the row: all three fell to the chat lane
                      "hurts", "hurt", "hurting", "pain", "painful", "sore", "throbbing",
                      "aching", "easily", "easy", "yellow", "colour", "color", "turning")
                     + ASK_ABOUT),
          _the_bruise_answer),
    entry("heartburn", (("heartburn", "acid reflux", "reflux", "indigestion"),
                        ("night", "help", "get rid", "stop", "what", "antacid", "burning", "worse",
                         "relief",
                         # "i get heartburn after dinner" says the subject once and when it
                         # happens, and had no ask in it, so it never reached this entry
                         "after dinner", "after eating", "after a meal", "after food",
                         "after my tea", "in the night", "at night", "when i lie down",
                         "lying down", "keep getting", "keeps coming back",
                         # "i have heartburn most evenings" and "i get it every night" say how
                         # often, and the recurrence is the ask: without these the line named
                         # the subject and nothing else the row held
                         "every", "every evening", "every night", "most evenings", "most nights",
                         "most days", "often", "always", "reflux")
                        # ... and a food the line blames is the question too: "tomatoes give me
                        # heartburn" asks about tomatoes, and the reply names them
                        + _HEARTBURN_ASKS
                        # "why do i get heartburn" is the mechanism question, and "which foods
                        # cause it" names no food of its own: both asked nothing the row held
                        + ("why", "why do i", "why am i", "cause", "causes", "trigger", "triggers",
                           "food", "foods", "diet", "avoid", "cut out", "eat", "eating",
                           # The shape people report a trigger in, whatever the food is: "baked
                           # beans gives me heartburn" names something the row's list cannot
                           # hold, and "gives me" is the ask, so it is answered as a report of a
                           # trigger rather than passed. Without it only the foods written into
                           # the list above were answered at all.
                           "gives me", "gives", "gives you", "sets off", "set off", "brings on",
                           "bring on", "i get", "getting", "get", "from", "reaction", "reactions",
                           # heartburn at night is the same question asked with what it costs:
                           # sleep. "heartburn keeps me awake" got "I'm listening - say more".
                           "awake", "sleep", "sleeping", "asleep", "wake me", "wakes me",
                           "woke me", "cant sleep", "keep me up", "keeps me up", "propped up",
                           # the two things people blame that are not food, and the way the
                           # question about a tablet is asked: "heartburn in pregnancy" and "can i
                           # take naproxen with heartburn" both asked nothing the row held.
                           "pregnant", "pregnancy", "expecting", "tablets", "pills", "medication",
                           "medicine", "ibuprofen", "aspirin", "naproxen", "painkillers",
                           "take", "taking", "safe", "ok to take",
                           # The plainest report of all: "i have heartburn" and "my heartburn is
                           # killing me" name the subject and say nothing else, so they carried no
                           # ask word and the fallback answered them. The answer is the same one
                           # "what can i take for heartburn" already had.
                           "have", "having", "got", "suffering", "again", "killing me", "terrible",
                           "awful", "so bad", "really bad", "hurts", "hurting", "today",
                           "right now", "all the time", "constantly", "drink", "drinking",
                           # the treatment in the line, and the treatment that has stopped
                           # working: "my gaviscon isnt helping" carried no ask word at all
                           "gaviscon", "antacid", "antacids", "isnt helping", "not helping",
                           "doesnt work", "doesnt help", "isnt working", "not working",
                           "stopped working", "any more")),
          _heartburn,
          # A line that says heartburn is about heartburn, so it outranks a how-to that shares a
          # word with it: "orange juice gives me heartburn" was reaching prepare-fruit on "orange"
          # and "juice" and being told how to squeeze one.
          bias=4,
          # ... and a baby's reflux is the posset row's: "my baby has reflux what can i do" is a
          # feed-tied question with a feed's answer, and this row's "what", "help" and "reflux"
          # outscored it. A grown-up's own heartburn never mentions a baby.
          avoid=("chest", "arm", "jaw", "breathless", "short of breath", "sweating", "crushing",
                 "tight", "baby", "babies", "newborn", "infant", "toddler", "my son",
                 "my daughter", "my child")),
    # A person who says they have it is asking what to do about it: "i have hay fever" and "ive
    # got hayfever" are the same question as "what helps hay fever", and both were a stock ack
    # because the second half wanted a how-to word. "i have" and "ive got" cannot overreach: the
    # subject has to hit the first half as well, and nothing else in this file keys "i have".
    entry("hayfever", (("hayfever", "hay fever", "pollen", "allergy season"),
                       ("help", "stop", "get rid", "treat", "worst", "control", "antihistamine",
                        "what", "how", "symptoms", "bad", "i have", "ive got", "i've got",
                        "i have got", "suffer", "suffering", "every year", "each year",
                        "seasonal", "started", "starting",
                        # "is it a cold or hayfever" asks which of the two it is and has none of
                        # the words above: the comparison itself is the ask.
                        "is it", "a cold", "or a cold", "cold or", "difference", "or is it",
                        "which is it", "all the time")),
          _hayfever_or_a_cold,
          avoid=("dog", "cat", "kitten", "puppy", "pet", "food", "peanut", "nuts", "bee", "wasp",
                 "sting", "baby", "milk", "gluten"),
          # "i have hayfever" states it and asks nothing
          report=True),
    # Three everyday body-and-mind questions that used to get the search hedge or a stock ack.
    # Each one is written to sort ordinary from "worth a GP", because the person asking usually
    # cannot tell the difference and that is the useful half of the answer.
    entry("always-tired",
          # The symptoms are single words here and the recurrence-or-question words live in the
          # second part: a phrase that names its own recurrence ("always tired") cannot also be
          # the second signal, or "i am always tired" scores under the minimum and gets nothing.
          # "exhausted", "worn out", "run down" and "drained" are machine words too, and their
          # loose forms are the machine's: "exhausted" strips to "exhaust" and "drained" to
          # "drain", so "why is my car exhaust so loud", "how do i fix a blowing exhaust" and
          # "what does worn out brake pads sound like" were all answered with the tiredness card.
          # A person saying how they feel says it in the first person or after "feel", so the
          # feeling is keyed as a phrase the machine cannot use.
          # "why dont i have any energy" was a shrug: the key held "no energy" and people write
          # the same complaint as "any energy". "how much energy does a kettle use" is a physics
          # line, and its own words keep it there.
          (("tired", "no energy", "any energy", "keep falling asleep", "tired even after", "knackered",
            # The same question said as a shortage, which is how most people say it and which no
            # card claimed: "im always low on energy in the afternoons" was answered with the
            # hours a two-rate tariff is cheap in. The personal shapes are phrases; the bare
            # "low energy" is a light bulb as often as it is a person.
            "low on energy", "low in energy", "low of energy",
            "am exhausted", "i'm exhausted", "im exhausted", "feel exhausted", "feeling exhausted",
            "so exhausted", "always exhausted", "exhausted all the time", "exhausted after",
            # "why am i exhausted" is the plainest way the question is asked, and the phrase
            # "am i exhausted" is how it arrives
            "am i exhausted",
            "exhausted by", "exhausted lately", "worn out", "feel worn out", "feeling worn out",
            "i'm worn out", "im worn out", "so worn out", "worn out after", "worn out all the time",
            "feel drained", "feeling drained", "so drained", "drained after", "drained all the time",
            "feel run down", "feeling run down", "i'm run down", "im run down", "a bit run down",
            "feeling a bit run down", "shattered",
            # A phrase, not the bare "tired": "i sleep 8 hours and im still tired" is this
            # question, and "im still tired" on its own is a passing feeling the chat pool meets.
            "still tired", "still exhausted", "still knackered", "tired all day",
            "tired all the time", "exhausted all the time",
            # A question about energy is the same question, and it names no tired word at all:
            # "what can i do to get some energy back" and "how do i get more energy" were the
            # back-pain paragraph and the honest shrug. The phrases rather than the bare
            # "energy", which is in a bill, a drink and a rating as often as it is in a person.
            "more energy", "some energy", "energy levels", "energy back", "get energy",
            # "often" and "a lot" are how most people say a thing keeps happening, and without
            # them the line missed this row and the chat pool answered it: "im often exhausted"
            # was told to call it an early night tonight, which is the answer to one late night,
            # not to a thing that keeps coming back. The phrases are the first-person ones, so a
            # car exhaust and worn brake pads stay where they were.
            "often exhausted", "often tired", "often knackered", "often shattered",
            "often worn out", "often drained", "exhausted a lot", "tired a lot",
            "knackered a lot",
            # How often a thing happens is the shape of the answer, not the thing itself. "Most
            # days" and "a lot of the time" stood here, in the list of subjects, and both are in
            # the shape list below as well, so one phrase answered both halves of the key: "i walk
            # the dog most days", "i go to the gym a lot of the time" and "i get home late most
            # days" were all told how to fix constant tiredness. A line reaches this row now only
            # when it says a tired word as well - the phrases kept below carry their own, and
            # "tired most days" still matches, one list each.
            "tired most days", "exhausted most days", "regularly tired",
            "regularly exhausted", "keep feeling tired", "keep feeling exhausted")
           + _KEYED_FEELINGS,
           ("normal", "why", "what", "how", "should", "worry", "worried", "fix", "wrong",
            "always", "constantly", "every day", "all the time", "all day", "lately", "for weeks",
            "for months", "doctor", "gp", "blood test", "sleep", "desk", "afternoon", "morning",
            "driving", "mornings",
            # how a thing that keeps coming back is said when it is not every day
            "often", "a lot", "regularly", "most days", "most weeks")),
          "Most constant tiredness is dull rather than medical: too little sleep, a late screen, "
          "alcohol, caffeine after lunch, or no daylight. Give it two weeks of the basics before "
          "you assume anything else - the same bedtime and getting-up time every day, twenty "
          "minutes outside in the morning, no caffeine after two, and no phone in the bedroom. "
          "If it is still there after that, see a GP for a blood test: low iron, an "
          "underactive thyroid and low vitamin D are the usual finds, and iron is common and easy "
          "to treat, especially for anyone with heavy periods.",
          # an emergency or a named illness is somebody else's answer, and "i'm tired" on its own
          # is a feeling the bot should meet, not a symptom to explain (tests/test_ack.py)
          avoid=("chest", "breathless", "cant breathe", "fainted", "passed out", "blood", "coughing",
                 "cancer", "chemo", "pregnant", "baby", "newborn", "depressed", "suicidal",
                 # "drained" is a form of "draining", so a phone battery that drains fast was
                 # being read as a person worn out
                 "battery", "phone", "laptop", "charger", "charging",
                 "cant get out of bed", "slept badly", "long day", "children are", "kids are",
                 # a person sharing a hard week is a feeling the chat pool meets, not a question,
                 # and the knowledge base now claims the sleep topic through sleep.py, so this
                 # entry would otherwise take "this week has been killing me, i'm exhausted"
                 "this week", "this month", "killing me", "want to help", "but im exhausted",
                 # a tired child is a question about the child, not this one
                 "my son", "my daughter", "my child", "my kids", "toddler", "teenager", "baby",
                 # tired eyes at a screen is the eye-strain entry, and a virus has its own
                 "eyes", "eye", "screen", "monitor", "glasses", "flu", "virus", "covid",
                 "cold", "infection", "chemo",
                 # A phone or laptop battery draining is technology, not a symptom. The
                 # typo pass reads "drains" as "drained", so a long battery question also
                 # scores on "lately". Keep the guard to the battery itself: a phone that
                 # keeps someone up is still a tiredness question.
                 "phone battery", "phone's battery", "phones battery",
                 "laptop battery", "laptop's battery", "battery drains", "battery drain",
                 "battery dies", "battery dying", "battery health",
                 # The drain in a sink is a noun and "drained" is the adjective, and one folds
                 # onto the other: "should i put bleach down the drain" was this entry. The
                 # household words below are what tell a plumbing line from a tired person, and
                 # they are phrases so a loose form cannot take "i feel drained" with them.
                 "down the drain", "the drain", "drain is", "drains are", "drain pipe",
                 # The bare word is unsafe, because the lookup folds "drain" onto "drained":
                 # "why is my drain blocked" and "why is my drain slow" ask why, "why" is in
                 # the second key group, and main answered both with this paragraph. The
                 # phrases below are the shape of a plumbing line ("my drain", "drain blocked"),
                 # so "i am always drained" and "i feel drained all the time" keep it.
                 "my drain", "drain blocked", "drain slow", "drain smells", "drain smelly",
                 "drain dripping", "drain leaking", "drain clogged",
                 "drainage", "plumbing", "plumber", "plughole", "bleach", "blocked drain",
                 "unblock", "sewer", "sink", "toilet", "tap", "washing machine", "dishwasher",
                 # "should i let her sleep in" is a decision about this morning, not a
                 # tiredness diagnosis, even when the last turn said she was tired.
                 "sleep in", "lie in", "let her sleep", "let him sleep", "let them sleep",
                 # a person whose company wears someone out is the friendship question, and the
                 # phrases are what tell it from a tired body ("i feel drained all the time"
                 # keeps this entry). "i have a draining friend what do i do" was this card.
                 "draining friend", "friend is draining", "friend drains", "friends draining",
                 "draining me", "drains me", "exhausting friend", "friend is exhausting",
                 "friends are exhausting", "friend who drains", "wears me out", "worn me out",
                 # The car and the bike have these words too, and the key cannot tell them
                 # apart on its own: "exhaust" is what "exhausted" folds onto and "worn out"
                 # is what a set of brake pads is, so "why is my car exhaust so loud" and
                 # "what does worn out brake pads sound like" were both this paragraph. The
                 # vehicle words are the noun that decides it. "exhaust" is not among them: a
                 # bare one also matches "i'm exhausted", which is the question.
                 "car", "cars", "van", "vans", "lorry", "truck", "mot", "motorbike",
                 "motorcycle", "scooter", "engine", "silencer", "exhaust pipe", "exhaust fumes",
                 "brake", "brakes", "brake pads", "pads", "clutch", "gearbox", "suspension",
                 "tyre", "tyres", "muffler", "catalytic",
                 # "tired of" is bored of a thing, not short of sleep: "im tired of my job what
                 # should i do" was answered with the two weeks of basics, which is the wrong
                 # subject. Bored of a thing belongs to the row about changing it, and a punt
                 # is better than a lecture about bedtimes.
                 "tired of", "sick of", "bored of", "bored with", "fed up of", "had enough of"),
          guard=_names_the_feeling),
    entry("more-energy",
          # "how do i get more energy" was a search and "what should i eat to have more energy"
          # was a random dinner, because `meal-tonight` keys the ask and the energy words were
          # nobody's subject. Energy is sleep, daylight and food in that order, whatever the
          # shape of the ask, so it is one card.
          # "no energy" is left out on purpose: the tiredness row above owns it, and two cards
          # with the same advice on the same phrase is how a knowledge base grows two answers.
          (("more energy", "low energy", "energy levels", "my energy", "afternoon slump",
            "energy slump", "sluggish", "keep flagging"),
           ("how", "what", "get", "getting", "eat", "should", "increase", "boost", "keep",
            "any", "tips", "help", "have", "why")),
          "Energy comes from sleep, daylight and food, in that order: the same bedtime and "
          "getting-up time every day, ten minutes outside in the morning light, and a lunch with "
          "protein and slow carbs rather than just a sandwich, so three o'clock does not flatten "
          "you. Water through the day and no caffeine after two help too. Still flat after two "
          "weeks, ask your GP for a blood test for iron and thyroid.",
          bias=1,
          # A bill, a supplier, a drink and a workout all carry these words, and none of them is
          # the body's energy question.
          # A contract, a meter or a tariff is a document and a bill is a bill: the utility
          # reading of "energy" wins whenever one of these is in the topic. "how do i cancel my
          # energy contract" and "how do i cancel my energy supply" were answered with this card,
          # which tells somebody asking how to leave a tariff to go to bed on time.
          avoid=("contract", "contracts", "cancel", "cancelling", "cancellation", "supply",
                 "account", "accounts", "meter", "meters", "switch", "switching", "switched",
                 "direct debit", "unit rate", "economy 7", "prepayment", "smart meter",
                 "bill", "bills", "company", "companies", "supplier", "tariff", "solar",
                 "electricity", "gas", "price cap", "standing charge", "renewable", "kwh",
                 "energy drink", "energy drinks", "red bull", "monster", "drink", "drinks",
                 "exercise", "workout", "gym", "calories", "carbs", "protein shake",
                 "my car", "the car", "house", "home", "flat", "boiler", "heating")),
    entry("sleep-in",
          # A decision about this morning, not the recurring-tiredness answer: "should i let her
          # sleep in" after a tired night wants a call, and the ask is what keeps a passing
          # "i sleep in the day" (shift work) out of it.
          (("sleep in", "sleeping in", "lie in", "lying in", "let her sleep", "let him sleep",
            "let them sleep", "let me sleep"),
           ("should", "shall", "is it", "is a", "ok to", "okay to", "alright to", "worth",
            "better", "bad", "allowed", "can i", "can we", "could i", "let")),
          "An extra hour or two is usually the good call after a short night. Let the sleep "
          "happen, then open the curtains and get some daylight. Keep the rest of the day on "
          "the usual times and go to bed at the usual hour tonight: a long lie-in shifts the "
          "body clock and makes the next night harder. If the tiredness is there most mornings "
          "for weeks, that is worth a GP and a blood test.",
          avoid=("night shift", "work nights", "night shifts", "in the day", "missed my train",
                 "late for work", "alarm", "baby", "newborn", "toddler")),
    entry("parent-memory",
          (("mum", "mom", "mother", "dad", "father", "parent", "parents", "grandma", "grandmother",
            "grandad", "grandfather", "gran", "nan", "nana", "mother in law", "father in law",
            # the forgetting is not always a parent's: "my husband forgets names" and "my wife
            # keeps forgetting things" are the same question about the same kind of adult, and
            # they were reaching the trick for remembering a new name instead.
            "husband", "wife", "partner", "spouse", "other half", "brother", "sister",
            "aunt", "auntie", "uncle", "boyfriend", "girlfriend",
            # an adult who forgets is not always a relative: "my best friend seems forgetful
            # lately" and "my neighbour keeps repeating himself" are the same question about the
            # same kind of person, and the friend's line got no answer at all.
            # a child is not: "my son keeps forgetting his PE kit" is a school morning, and the
            # kit list answers it.
            "cousin", "friend", "mate", "pal", "chum",
            "neighbour", "neighbor", "colleague", "coworker", "boss", "flatmate", "housemate",
            "carer", "nephew", "niece", "grandchild", "grandson", "granddaughter", "fiance",
            "fiancee", "missus", "stepmum", "stepdad", "sister in law", "brother in law",
            "daughter in law", "son in law"),
           ("forgetting", "forgetful", "forgets", "forgot", "memory", "repeats", "repeating",
            "confused", "confusion", "gets lost", "wandering", "same question", "forget things",
            "forgetting things", "forget names", "forgets names", "cannot remember",
            "cant remember", "can't remember", "cant recall", "keeps forgetting",
            "forget words", "cant remember words",
            # the slip said as losing something: "the wife keeps losing her glasses" is the same
            # worry as "keeps forgetting her glasses", and only the forgetting words were here.
            "losing her", "losing his", "losing their", "keeps losing", "loses things",
            "losing things", "losing track", "loses her", "loses his", "loses their")),
          "Write down for a fortnight what they forget, and whether it is new. Slower recall of "
          "names is ordinary; asking the same question within minutes, getting lost on a familiar "
          "route, or forgetting something they have always done are not, and want a GP "
          "appointment. Take the notes and ask for a memory assessment, and say if they still "
          "drive: an infection, low B12, an underactive thyroid, poor hearing and some medicines "
          "can all cause a fixable muddle.",
          # A line where the person forgot to do something for the relative is not a question
          # about the relative's memory: "i forgot to call my mum" was answered with the
          # memory-assessment card, which is the opposite end of the same word
          # (bot/compose/repair.py reads the deed and the composer answers it).
          guard=lambda reading: (not _owns_the_deed(reading)
                                and not _a_habit_without_the_illness(reading)
                                and not _the_speaker_forgot_to_do_it(reading)
                                and not _its_money_that_has_not_come_back(reading)),
          # a funeral, a will or a hurt birthday is not a memory question
          avoid=("died", "passed away", "funeral", "burial", "cancer", "hospice", "birthday",
                 "christmas", "never calls", "wont call", "anniversary", "card", "present",
                 "hospital", "stroke", "dementia diagnosed", "care home",
                 # A person who wanders is a safety question before it is an assessment one: the
                 # card that says a lockable gate, an alarm and a note in the wallet is the answer
                 # to "my mum has dementia and keeps wandering", and the assessment card was
                 # taking the turn because it is ranked above it.
                 "wandering", "wanders", "wandered", "gone missing", "went missing",
                 "gone walkabout", "left the house at night", "found in the street",
                 # forgetting a dose is a medicines question, not a memory assessment: the lines
                 # that name the tablets go to missed-medication, which answers for the dose.
                 "tablet", "tablets", "medication", "medications", "meds", "medicine", "medicines",
                 "dose", "doses", "insulin", "diabetes", "diabetic", "pills", "pill",
                 "blood pressure", "warfarin", "epilepsy",
                 # A line about your own forgetting is not a line about somebody else's memory:
                 # "i keep forgetting to call my mum" names a parent and the forgetting word and
                 # was answered with the memory assessment for a person who is fine.
                 "i keep forgetting", "i keep forgetting to", "i'm always forgetting",
                 "im always forgetting", "i always forget", "i forget to", "i forgot to",
                 "me keep forgetting"),
          # "My mum keeps forgetting things" is the memory question about somebody else, and the
          # forgetting-errands card next door keyed the same two words ("keeps forgetting" +
          # "things") and answered it with how to set a reminder in Siri. A person and the
          # forgetting together are this row's question, so it speaks first.
          bias=2),
    # The person's own memory, which had no card at all: "my memory is getting worse" was given
    # a shower and an early night, "im getting forgetful" was asked how far they wanted to get,
    # and "memory loss", "how do i know if its dementia" and "am i getting dementia" were a
    # shrug. The entry above is about somebody else's memory ("what they forget"), so the worry
    # in the first person is its own answer: the fortnight of notes, the ordinary at any age
    # part, and the fixable causes a GP can check.
    entry("own-memory-worry",
          (("memory", "memories", "forgetful", "forgetfulness", "forgetting", "forget",
            "dementia", "alzheimers", "alzheimer's", "recall", "remember", "remembers",
            "remembering"),
           ("my memory", "my memories", "my recall", "im getting forgetful",
            "i am getting forgetful", "im so forgetful", "i am so forgetful", "so forgetful",
            "getting forgetful", "getting worse", "worse lately", "getting bad",
            "memory loss", "my memory is", "memory is getting", "memory problems",
            "short term memory", "short-term memory", "losing my memory", "losing it",
            "keep forgetting things", "cant remember things", "can't remember things",
            "keep forgetting everything", "forgetting everything", "forgetting a lot",
            "forget things", "cant remember things like i used to", "remember things like i used to",
            "things like i used to", "not as good as it was",
            "should i worry", "is it normal", "how do i know", "am i getting", "am i losing",
            "could it be", "am i", "why am i", "worried", "worry",
            # the same question asked as a fear or as a meaning: "im scared im getting
            # alzheimers" and "does forgetting mean dementia" are both "is this the illness",
            # and both were answered with a listening line because no phrase here fit them.
            "scared", "frightened", "terrified", "im worried", "worried im", "scared im",
            "getting alzheimers", "getting dementia", "mean dementia",
            "does forgetting mean", "is forgetting", "does this mean", "does that mean",
            "cant hold on to", "forgetting names", "forgets names", "forgetting words",
            # "is losing keys a sign of dementia" is the illness question, and every phrase here
            # is the shape of asking it rather than a wording somebody wrote down.
            "sign of dementia", "sign of alzheimers", "signs of dementia", "a sign", "signs",
            "symptom of", "symptoms of", "early signs", "first signs", "is it dementia",
            "could it be dementia", "does it mean dementia", "start of dementia")),
          "Note it down for a fortnight before you decide anything: what was forgotten, when, and "
          "whether it was new. Forgetting names, or where the keys went, is ordinary at any age "
          "and worse when you are tired, stressed, low or sleeping badly. What is not ordinary is "
          "losing the thread of something you have always done - a recipe you know by heart, the "
          "way to a place you drive every week, paying the same bill twice - and that is what "
          "wants a GP. Book one if it is getting worse, if it came on suddenly, or if it frightens "
          "you, and take the notes with you: a GP can check the causes that are fixable, which "
          "include low B12, an underactive thyroid, blood pressure, sleep apnoea, depression and "
          "the medicines you already take. Going early is not an overreaction; it is how the "
          "fixable ones get found.",
          # The errand card answers "i keep forgetting to pay a bill" and the name trick answers
          # "i keep forgetting names": a deed that slipped is not the question this card is for.
          guard=lambda reading: (_not_somebody_elses_memory(reading) and not _owns_the_deed(reading)
                                and not _a_habit_without_the_illness(reading)
                                and not _the_speaker_forgot_to_do_it(reading)
                                and not _its_money_that_has_not_come_back(reading)),
          avoid=("forgetting to", "forgot to", "forget to",
                 # the forgetting is a symptom of the situation, not the subject: "i go bright red
                 # in interviews and forget everything" is about the nerves.
                 "interview", "interviews", "presentation", "presentations", "go red", "went red",
                 "blush", "blushes", "go blank", "went blank", "nervous", "panic",
                 "what causes", "why does", "why do we", "how does memory work", "sleep",
                 "tired", "exhausted", "baby", "newborn", "pregnant", "menopause",
                 # A "why" asks how memory works, and the explanation entry answers it with the
                 # mechanism ("most forgetting is not a lost file"); revision asks how to hold
                 # what is being learned, and the study card answers that with testing yourself.
                 "why", "revise", "revising", "revision", "revised", "study", "studying",
                 "studied", "exam", "exams", "coursework", "flashcards", "learn", "learning",
                 "memorise", "memorize", "test myself",
                 # A person who wants a better memory is asking for the training, not for a GP:
                 # "how can i improve my memory" was answered with the fortnight of notes and
                 # the assessment, when the card next door says to test yourself instead of
                 # rereading. Wanting a sharper memory is not the same question as fearing one.
                 "improve", "improving", "sharpen", "sharpening", "boost", "train my memory",
                 "better memory", "memory better", "memory tricks", "techniques", "tips",
                 "games for", "exercises", "get sharper", "keep my memory", "stay sharp",
                 # and the person who says their memory is fine is asking about the word that
                 # went, which is the explanation's subject, not this card's
                 "memory is fine", "memory is good", "memory is ok", "memory is okay")),

    # The most common wording of the question is "why cant i sleep", and it matched nothing: the
    # entry next door keys the phrase "cant sleep", which is not in that line ("cant i sleep"),
    # and the ones about the racing mind are about the mind. So this asks for the "why" shapes and
    # leads with the causes, because that is what the line is asking for.
    entry("why-cant-i-sleep",
          (("why cant i sleep", "why can't i sleep", "why cant i sleep at night",
            "why can't i sleep at night", "why am i not sleeping", "why am i not tired",
            "cant sleep at night", "can't sleep at night", "not sleeping well",
            "not sleeping at all", "why am i awake", "what keeps me awake"),
           ("night", "nights", "lately", "always", "any more", "anymore", "at all",
            "why", "cause", "reason", "again", "every night", "these days", "week")),
          "Usually it is the wake-up time rather than the bedtime: a lie-in at the weekend, a nap, "
          "or coffee after about two in the afternoon keeps the body clock late, and a warm room "
          "or a phone in bed finishes the job. Fix the getting-up time first, move the coffee "
          "before lunch, keep the bedroom around 18C and dark, and give it a week before you "
          "judge it. If it is a worry that wakes you, spend ten minutes before bed writing the "
          "list down so your head is not doing it at three. See a GP if it has gone on a month, "
          "or if the days are falling apart.",
          # a baby, a snorer, a shift worker and a low mood are other answers, and the timing of
          # falling asleep is `sleep-latency`'s question. Waking in the night is not this question
          # either: main answers it with the body clock and with the pen and the list, which are
          # both better than advice about the morning, so every waking shape stands this row down.
          avoid=("baby", "newborn", "toddler", "child", "children", "snoring", "apnoea",
                 "shift work", "jet lag", "how long does it take", "minutes to fall",
                 "melatonin", "sleeping tablets", "depressed", "hopeless", "suicidal",
                 "self harm", "died", "funeral", "exam tomorrow",
                 "wake up", "wakes up", "woke up", "waking up", "i wake", "keeps waking",
                 "keep waking", "in the night", "through the night", "middle of the night",
                 "get back to sleep", "back to sleep", "on my back", "on my front")),
    entry("cant-switch-off",
          (("overthinking", "overthink", "cant switch off", "can't switch off", "mind racing",
            "racing thoughts", "cant stop thinking", "can't stop thinking", "lying awake",
            "wide awake", "cant sleep", "can't sleep", "cant get to sleep",
            "my head wont stop", "thoughts spinning"),
           # "sleep" and "bed" are not here: "cant sleep lol" is a line to meet, not a lecture,
           # so the night part needs a second word that asks something
           ("night", "stop", "how", "help", "worry", "worrying", "anxious", "stress", "stressed",
            "work", "tomorrow", "always", "waking", "wake", "early", "hours", "thought")),
          "Get the thinking out of your head before bed: ten minutes with a pen, a list of what is "
          "actually worrying you and the first step for each, and a line at the bottom saying what "
          "can wait until morning. Then keep the bed for sleeping - if you are still awake after "
          "about twenty minutes, get up, sit somewhere dim with something dull, and go back when "
          "you are sleepy, so the bed does not become the place you argue with yourself. Same "
          "winding-down half hour each night, phone out of reach, and get up at the same time "
          "whatever happened, because the wake-up time is what steadies the sleep.",
          # It answers an ask, not a passing line. "i cant get out of bed most mornings" then
          # "and i keep waking up at 5" is one conversation about how they feel, and a
          # sleep-hygiene list is the wrong reply to it.
          ask=("how", "why", "what", "should", "help", "stop", "any", "tips", "advice", "could"),
          # a live crisis, a bereavement and a real sleep problem like apnoea are elsewhere, and
          # so is a low morning: "i cant get out of bed most mornings" then "i keep waking up at 5"
          # is one conversation about how they feel, and a sleep-hygiene list is the wrong reply
          avoid=("suicidal", "kill myself", "self harm", "panic attack", "died", "funeral",
                 "snoring", "apnoea", "sleep apnoea", "baby", "newborn", "shift work", "jet lag",
                 "melatonin", "sleeping tablets", "insomnia for years", "get out of bed",
                 "out of bed", "depressed", "hopeless", "no point", "cant face", "crying",
                 "empty", "numb", "worthless")),
    # The how-to half of sleep. `cant-switch-off` answers the racing mind and `sleep-hours` the
    # number, and between them "how do i sleep better", "how do i get to sleep" and "i keep waking
    # up in the night" fell through to the search hedge, which is most of what people ask about
    # sleep. The practical sequence is what the line wants: a fixed wake-up time, then the three
    # things that move it, then what to do at 3am.
    entry("sleep-how-to",
          (("how do i sleep better", "how to sleep better", "sleep better", "sleep properly",
            "how do i get to sleep", "how to get to sleep", "get to sleep faster",
            "fall asleep faster", "fall asleep quicker", "help me fall asleep",
            "help me get to sleep", "how do i fall asleep",
            # "get a good night's sleep" is the commonest wording of the ask, and it missed
            # because the key had the falling-asleep forms but not the sleeping-well ones.
            # The whole question is keyed, not "sleep well" or "get some sleep": those are
            # statements too ("i sleep well", "i just want to get some sleep") and the advice
            # is the wrong reply to both.
            "how do i get a good nights sleep", "how do i get a good night's sleep",
            "how do i get a good night sleep", "how can i get a good nights sleep",
            "how can i get a good night's sleep", "how can i sleep well",
            "how do i sleep well", "tips for sleeping well", "what helps me sleep well",
            "any tips for sleeping well",
            # the improving verb in front of the subject, which is how the same ask arrives when
            # nobody says "better": "how do i improve my sleep", "how do i sort out my sleep"
            "improve my sleep", "improve my sleeping", "sort out my sleep", "sort my sleep out",
            "better sleep", "get better sleep", "sleep improvement", "work on my sleep",
            "wind down", "sleep routine",
            "bedtime routine", "sleep hygiene", "sleep tips", "tips for sleeping",
            "keep waking up", "waking up in the night", "wake up in the night",
            "waking in the night", "wake up every night",
            # the same ask in the other two wordings people use
            "what helps me sleep", "helps me sleep", "help me sleep", "anything to help me sleep",
            "sleep through the night", "sleep right through", "stay asleep", "stop waking up"),
           ("sleep", "sleeping", "asleep", "bed", "bedtime", "night", "nights", "tonight")),
          "Fix the wake-up time first: the same hour every day, including after a bad night, and "
          "the rest tends to follow within a fortnight. Then the three that do most of the work - "
          "daylight and a walk in the first hour, no caffeine after lunch, and a screen-free half "
          "hour before bed - and only get into bed when you are sleepy rather than tired. Waking in "
          "the small hours is usually the mind, not a sleep problem: keep the room dark, don't check "
          "the clock, and after about twenty minutes get up and sit somewhere dim until you are "
          "sleepy, so the bed stops being the place you lie and argue with yourself. Still broken "
          "after six weeks of that is worth a word with a GP.",
          # The racing-mind lines are `cant-switch-off`'s, a child's night is the family answer,
          # and a loud snorer or a shift worker needs a different conversation.
          avoid=("overthinking", "overthink", "cant switch off", "can't switch off", "mind racing",
                 "racing thoughts", "cant stop thinking", "can't stop thinking", "lying awake",
                 "worry", "worried", "worrying", "anxious", "anxiety", "stress", "stressed",
                 "baby", "babies", "newborn", "toddler", "my son", "my daughter", "my child",
                 "kids", "puppy", "cat", "dog", "snoring", "snore", "apnoea", "shift work",
                 "night shift", "jet lag", "time zone", "melatonin", "sleeping tablets",
                 # a shift worker needs the other answer, and "work nights" is how they say it:
                 # "how do i improve my sleep when i work nights" is not the same advice
                 "work nights", "working nights", "on nights", "night shifts", "shifts",
                 "sleeping tablet", "insomnia for years", "out of bed", "get out of bed",
                 "too much", "how much", "how many hours", "hours of sleep")),
    # Half of the people who ask about smoking want to stop, and every wording of it got the
    # search hedge. The answer is the plan that works rather than the reason it is bad for you.
    # The harm questions were stood down on purpose by every stop plan in this file - each one
    # avoids "is smoking bad", "passive smoking", "second hand", "as bad as", "worse than" - and
    # nothing picked them up, so the plainest question about smoking got the search hedge. They
    # are not a plan to quit: they are what the smoke does, which is the school-level answer.
    entry("smoking-harm",
          (("smoking", "cigarettes", "cigarette", "tobacco", "nicotine",
            "cigarette smoke"),
           ("bad", "harmful", "harm", "damage", "damages", "effects", "effect", "why is",
            "what does it do", "do to your body", "bad for you", "bad for", "cause", "causes",
            "cancer", "dangerous", "how bad", "unhealthy", "health", "how many", "safe")),
          "Smoking is the single biggest cause of cancer and heart disease you can remove "
          "yourself: the tar and the carbon monoxide damage the lungs and the arteries, and about "
          "half of lifelong smokers die early because of it. There is no safe number of "
          "cigarettes - one to four a day still multiplies the heart risk - and the gains start "
          "within days of stopping, which is why quitting at any age is worth it.",
          # A plan to quit, somebody else's habit, a vape comparison, a joint and a smoked fish
          # are five other answers; the stop plans stand these lines down themselves, so this
          # one must not take theirs back.
          avoid=("stop", "stops", "stopping", "quit", "quits", "quitting", "give up", "cut down",
                 "patch", "patches", "cold turkey", "vape", "vapes", "vaping", "e cigarette",
                 "weed", "cannabis", "joint", "joints", "skunk", "marijuana", "dope", "spliff",
                 "passive", "second hand", "secondhand", "smoked salmon", "smoked haddock",
                 "smoked mackerel", "smoked bacon", "smoked paprika", "smoked cheese", "barbecue",
                 "bbq", "brisket", "smoker", "campfire", "bonfire", "wood smoke", "chimney",
                 "smoke alarm", "smell", "stain", "smoke from",
                 # A machine that smokes is not a habit: "why is my exhaust smoking" was this card,
                 # because "smoking" and "why is" are its own words. The exhaust row answers that
                 # line once this one stands down. "car" is left out on purpose: a person who
                 # smokes in the car is still a person's habit.
                 "exhaust", "exhausts", "engine", "engines", "motorbike", "motorcycle",
                 "scooter", "mower", "lawnmower", "lawn mower", "generator", "van",
                 "dad", "mum", "mother", "father",
                 "husband", "wife", "partner", "girlfriend", "boyfriend", "friend", "son",
                 "daughter", "brother", "sister", "worried", "worry", "he smokes", "she smokes",
                 "cost", "price", "how much do", "tax")),

    # "is secondhand smoke bad for you" is a question about the air in a room somebody else
    # smokes in, and the person asking is usually protecting a child or a pregnancy.
    entry("secondhand-smoke",
          (("second hand smoke", "secondhand smoke", "passive smoking", "passive smoke",
            "second hand smoking", "secondhand smoking", "someone smokes", "smokes in the house",
            "smokes indoors", "smoke in the house", "smoke around"),
           ("bad", "harmful", "harm", "risk", "risks", "dangerous", "affect", "effects", "effect",
            "health", "pregnant", "pregnancy", "baby", "children", "kids", "child", "really",
            "is it", "how bad", "safe", "do to")),
          "Secondhand smoke is a real risk, not a smell: it carries the same tar, carbon monoxide "
          "and carcinogens, and living with a smoker raises a non-smoker's lung cancer risk by "
          "roughly a quarter and a child's risk of chest and ear infections much more. There is no "
          "safe level of exposure, and an open window or a separate room does not clear it - the "
          "only thing that works is smoking outside, away from the door.",
          # the harm of the smoker's own habit is smoking-harm's, and a plan belongs to a plan
          avoid=("stop", "stops", "stopping", "quit", "quits", "quitting", "give up", "cut down",
                 "vape", "vapes", "vaping", "e cigarette", "patch", "patches", "help", "how do i",
                 "weed", "cannabis", "joint", "joints", "smoked salmon", "barbecue", "bbq",
                 "campfire", "bonfire", "wood smoke", "smoke alarm", "smell", "stain")),

    # Cannabis has its own answer because the comparison people actually ask for - a joint
    # against a cigarette - is not the tobacco answer with one word changed.
    entry("cannabis-harm",
          (("weed", "cannabis", "marijuana", "skunk", "joint", "joints", "spliff", "ganja",
            "hash", "dope", "stoned", "smoking weed", "smoke weed"),
           ("bad", "harmful", "harm", "worse than", "compared", "compare", "cigarettes",
            "tobacco", "health", "risk", "risks", "effects", "effect", "psychosis", "mental",
            "addictive", "addicted", "safe", "how bad", "lungs", "brain", "for you")),
          "Smoked cannabis is harmful in a different way from tobacco: most joints are rolled "
          "with tobacco, so they carry the same tar and nicotine, a joint is held in longer, and "
          "the risk of psychosis and of anxiety is real and rises with heavy use and with high-THC "
          "skunk. It is not physically addictive like nicotine but the habit is hard to shift, and "
          "the damage is worse under about 25 while the brain is still developing. Vaping THC or "
          "eating it takes out the smoke, not the effects on the mind.",
          # a stain, a garden weed and a plan to quit are other answers
          # "weeding" cannot be here: it folds onto "weed", so it stood this row down for the
          # very lines it is for. The garden's own words are "weed killer" and the patch names.
          avoid=("stain", "stains", "carpet", "sofa", "garden", "lawn", "flowerbed", "driveway",
                 "patio", "knees", "weed killer", "roundup", "stop", "stops",
                 "stopping", "quit", "quits", "quitting", "give up", "cut down", "how do i",
                 "help me", "vape", "vaping")),

    # The harm question about drink was the proxy order's job in `health.units-a-week`, which
    # answers how much rather than what it does, and neither it nor the drink-drive limit could
    # take "is alcohol bad for you": it was a shrug.
    entry("alcohol-harm",
          (("alcohol", "drinking", "drink", "drinker", "beer", "wine", "booze", "vodka",
            "whisky", "spirits"),
           ("bad for you", "bad for", "harmful", "harm", "damage", "damages", "risks", "risk",
            "effects", "effect", "cancer", "health", "does to your body", "liver", "safe",
            "how bad", "why is")),
          "Alcohol is a group 1 carcinogen and there is no amount that is good for you: the risk "
          "starts with the first drink and rises with the total, which is why the guidance is "
          "about keeping it low rather than finding a safe level. The liver, the blood pressure "
          "and the risk of seven cancers - mouth, throat, oesophagus, liver, colon, and in women "
          "breast - all move the same way. A couple of drink-free days and staying under 14 units "
          "a week is what keeps the risk small.",
          # how much, the weekly total, driving, a morning after, a pregnancy, a medicine, a
          # stain and a plan to change are seven other answers
          avoid=("how much", "how many", "units", "weekly", "limit", "limits", "recommended",
                 "guidelines", "drive", "driving", "drink driving", "licence", "police", "test",
                 "hangover", "hungover", "pregnant", "pregnancy", "breastfeeding", "antibiotics",
                 "tablets", "medication", "medicine", "stain", "stains", "spill", "carpet",
                 "recipe", "sauce", "cake", "opened", "fridge", "keep", "keeps", "calories",
                 "cut down", "reduce", "less", "stop", "quit", "give up", "dog", "cat", "pet",
                 "coffee", "tea", "energy drink", "battery", "hand gel", "smell", "pour")),

    # "how long does alcohol stay in your blood" is the morning-after question, and the weekly
    # limit and the drink-drive limit both stood it down because neither is about clearance.
    entry("alcohol-clearance",
          (("alcohol", "alcohol i drank", "drinks", "pint", "pints", "wine", "beer", "vodka",
            "booze", "a drink"),
           ("how long", "stay in", "stays in", "still in", "out of my system", "out of your system",
            "clear my system", "clear of", "blood", "breath", "system", "metabolise", "burn off",
            "leave my body", "last in")),
          "Alcohol leaves at about one unit an hour and nothing speeds that up - coffee, a cold "
          "shower and food only make you feel different, not soberer. A pint of normal-strength "
          "beer, a medium glass of wine or a single spirit is two to three units, so a heavy "
          "evening can still leave alcohol in your blood the next morning, which is why the "
          "morning-after drive is the one that catches people.",
          # the weekly limit, the drink-drive limit, a hangover and a habit are four other lines
          avoid=("units", "how much is too much", "weekly limit", "limit", "limits", "legal",
                 "drive", "driving", "drink driving", "licence", "arrested", "police", "test",
                 "pregnant", "pregnancy", "breastfeeding", "antibiotics", "tablets", "medication",
                 "medicine", "hangover", "hungover", "stop", "quit", "cut down", "less", "reduce",
                 "recipe", "sauce", "cake", "opened", "fridge", "keep", "keeps", "calories",
                 "unit in", "how many units", "spill", "stain")),

    # "i quit smoking last week" was told to set a stop date in the next two weeks - a plan to
    # start, handed to someone who has already stopped. The first days are their own question:
    # what to expect, and what the body is doing.
    # Every phrase in the key above names what was given up. "i quit" and "i stopped" on their own
    # do not: "i had a bad day at work and i quit" was given the cigarette-craving answer, "i
    # stopped watching it last week" (the news) the same, and "i quit drinking last week" is a
    # different habit with its own row. A line that names no habit is not this row's question, so
    # the bare verbs are gone from the key rather than left to be guarded later.
    entry("just-quit-smoking",
          (("quit smoking", "stopped smoking", "gave up smoking", "quit vaping", "stopped vaping",
            "given up smoking", "off the cigarettes", "no cigarettes", "haven t smoked",
            "havent smoked", "not had a cigarette", "lungs"),
           ("last week", "yesterday", "days", "day", "week", "weeks", "month", "months",
            "first day", "first week", "how long", "feel", "feels", "feeling", "withdrawal",
            "cravings", "craving", "recover", "what happens", "now what", "awful", "tired",
            "mood", "anxious", "irritable", "worth it")),
          "The first week is the hardest and it does get easier: a craving peaks in about five "
          "minutes and the gaps between them stretch out after the third or fourth day. Expect a "
          "few days of being short-tempered and foggy, and a cough that brings up more than usual - "
          "the airways clearing is a good sign, not a relapse. The carbon monoxide is gone within "
          "a couple of days, breathing is easier in two to twelve weeks, and if a bad moment "
          "arrives, ride it out with water and a walk rather than testing your willpower.",
          # a plan to start, a cough entry, a smoked fish and a drug that is not nicotine are
          # four other answers; "how do i stop smoking" has no past tense and stays with the plan
          avoid=("how do i", "how can i", "plan", "patch", "patches", "gum", "lozenge", "spray",
                 "best way", "tips", "tip", "stop date", "set a date", "should i",
                 "smoked salmon", "barbecue", "bbq", "brisket", "weed", "cannabis", "joint",
                 "weight", "vape flavour", "flavours", "cost", "price", "tax")),

    entry("stop-smoking",
          (("quit smoking", "stop smoking", "give up smoking", "quit cigarettes", "stop cigarettes",
            "cigarettes", "cigarette", "smoking", "vaping", "vape", "nicotine",
            # A bare "patch" was a key, and a garden is full of them: "and how big should the
            # patch be", five turns into a chat about growing veg, was told to set a stop date
            # and buy nicotine replacement, and so was "the bare patch by the shed". The patch
            # that replaces a cigarette is only ever said with one of these around it, so the
            # phrases carry the row and the bare word does not.
            "nicotine patch", "nicotine patches", "patch work", "patches work",
            "patch help", "patches help", "patch safe", "patches safe", "patch better",
            "patches better", "patch or gum", "patches or gum", "patch worth",
            "patches worth", "do patches", "does the patch", "does a patch", "the patch work",
            "patches any good", "patch any good", "gum",
            # "which patch is best" is the same ask as "do patches work", and with the bare word
            # gone it was the only shape left with nothing to carry it: it became a punt while
            # every phrase around it still reached the plan.
            "which patch", "which patches", "best patch", "best patches", "patch is best",
            "patches is best", "patch best", "patches best", "patch better than", "patches do i",
            # The habit said in the past tense is the same habit: "ive smoked for 20 years how do
            # i stop" was a search hedge, because the key held "smoking" and the line held
            # "smoked", and an -ed form of a verb whose base ends in e is not one of the loose
            # forms the matcher works out ("smoked" reads as smoked/smok, never smoke). The two
            # phrases with a length of time after them are the way a long habit is named, and a
            # cooked meat is not smoked "for 20 years", so the fence below still holds.
            "smoked for", "smoked since", "been a smoker", "pack a day"),
           ("quit", "stop", "give up", "cut down", "how", "help", "best", "way", "tip", "tips",
            "worth", "try", "again", "cant", "can't", "struggling", "failed", "start",
            # "is nicotine gum any good" was going to the dentist, because the only reading of
            # "gum" the engine had was a mouth
            "good", "work", "works", "work for", "effective", "better", "safe")),
          "Set a stop date in the next two weeks and use nicotine replacement or a prescription "
          "aid as well as willpower: on willpower alone most attempts fail, and patches, gum or a "
          "vape roughly double to triple your odds, with free help from a stop-smoking service "
          "adding more. Know your two triggers and plan the swap - a walk after meals, something "
          "in your hands on the phone - because a craving peaks in about five minutes and passes. "
          "Slips are normal, not the end of it: two failed tries still leave you far better off, "
          "and the health gains start within days.",
          # A barbecue, a smoked fish and a smoky room are not a habit to break.
          # "smoke" itself is not here: it is a loose form of "smoking", and one word would
          # stand the entry down for every line that names the habit.
          avoid=("meat", "brisket", "salmon", "barbecue", "bbq", "smoker", "smoked salmon",
                 # it is someone else's cigarette: "set a stop date" tells the wrong person to
                 # stop, and a worried relative wants what to say, not a plan for themselves
                 "dad", "mum", "mother", "father", "husband", "wife", "partner", "girlfriend",
                 "boyfriend", "friend", "son", "daughter", "brother", "sister", "worried",
                 "worry", "wont", "won't",
                 # a cough after stopping is the answer about the cough, and a vape has its
                 # own entry (#1235): patches and gum are not what it says
                 "cough", "coughing", "vape", "vaping",
                 # they have already stopped: "i quit smoking last week" is just-quit-smoking's,
                 # which is above this row
                 "last week", "yesterday", "havent smoked", "haven t smoked",
                 "not had a cigarette", "since i quit", "since i stopped", "i ve quit",
                 "i ve stopped", "3 days ago", "a week ago", "a month ago", "already",
                 "smoked meat", "smoked fish", "smoking meat", "wood smoke", "campfire",
                 "chimney", "is smoking bad", "why is smoking bad", "effects of smoking",
                 "passive smoking", "second hand", "secondhand", "smell", "as bad as",
                 "worse than", "safer than", "compared", "how many", "too many", "safe limit",
                 # a mouth is not a habit: "how do i stop bleeding gums" and "sore gums" are
                 # the dentist's questions, and the smoking entry keys on "gum" for nicotine gum
                 # "gums" alone is not here: it is a loose form of "gum", so it would stand
                 # this entry down for "is nicotine gum any good" too. The phrases below catch
                 # a mouth without touching nicotine gum.
                 "gum disease", "gingivitis", "bleeding gums", "sore gums", "swollen gums",
                 "gums bleed", "my gums", "gums are", "teeth", "tooth", "toothache",
                 "dentist", "floss", "flossing", "mouth ulcer", "mouthwash",
                 # a lump of chewing gum in the hair reads as "gum" and this entry answered it
                 # with a stop-smoking plan; hair is not a habit. "chewing gum" is not avoided
                 # here: does chewing gum help you quit smoking is this entry's line, and
                 # gum-in-hair steps aside for the smoking words instead.
                 "hair", "hairs", "scalp", "in my hair", "out of my hair", "stuck in",
                 # and gum on a jumper is clothing's stain-gum, not a stop-smoking plan:
                 # "how do i get gum out of my jeans" was answered with a stop date and patches
                 "gum out of", "gum off", "gum on", "gum in", "gum from", "gum stain",
                 # the sweet, asked about as a food: how much sugar in chewing gum is a
                 # figure question, not a habit to break
                 "how much sugar", "sugar in", "calories", "calorie", "sweetener",
                 "sweeteners",
                 # A smoke alarm is not a cigarette: "how do i change the battery in my smoke
                 # alarm" was told to set a stop date and buy nicotine replacement.
                 "smoke alarm", "smoke detector", "alarm", "detector", "carbon monoxide",
                 "chirp", "chirping", "beeping", "battery", "chimney", "bonfire", "bbq",
                 # a bare "patches" took "how do i stop my lawn going yellow in patches" and
                 # answered it with a stop-smoking plan: a garden is not a habit either
                 "lawn", "lawns", "grass", "garden", "gardens", "yellow", "yellowing",
                 "leaves", "plant", "plants", "flower", "flowers", "shrub", "shrubs",
                 "soil", "moss", "turf", "brown patches", "bare patches",
                 # and the gum stuck to something washable is the stain answer's: "how do i get
                 # gum off my trousers" was told to set a stop date and buy nicotine replacement
                 "gum off", "gum on", "gum from", "gum stuck", "stuck to", "stuck on",
                 "jeans", "denim", "trousers", "carpet", "sofa", "settee", "shoe", "shoes",
                 "trainers", "fabric", "clothes", "stain", "stains",
                 # "how do i smoke a brisket" was a stop plan: the food is the subject
                 ) + _SMOKE_IS_NOT_A_HABIT),
    # Cholesterol was the commonest everyday health question with no answer at all. It is a
    # diet-and-plumbing question, so the food that moves the number comes first, then the retest.
    entry("cholesterol",
          (("cholesterol", "ldl", "hdl", "triglycerides", "statins", "statin"),
           ("lower", "reduce", "bring down", "cut", "high", "diet", "food", "foods", "eat",
            "avoid", "help", "how", "what")),
          "Cut saturated fat first, because that moves the number more than anything else: less "
          "cheese, butter, fatty meat, pastry, biscuits and coconut oil, and swap to olive or "
          "rapeseed oil and leaner cuts. Then add the things that help - oats, beans or lentils "
          "daily, nuts, oily fish twice a week, and 30 minutes of walking on most days - and get a "
          "retest after about three months, since diet alone typically takes 10 to 20 percent off. "
          "If you have been given a statin, keep taking it; diet and the tablet work together.",
          avoid=("egg", "eggs", "shell", "yolk")),
    # The everyday fitness and health asks that met the hedge: how much walking, a first
    # strength session at home, desk posture, blood pressure, snoring and sugar. Each is the
    # practical answer rather than the reason, and each stands down for the entry that already
    # owns a neighbouring question (a knee that hurts, protein for muscle, sleep apnoea).
    entry("steps-a-day",
          # Two more entries keyed on "steps" lower what that word is worth in this domain, and
          # "is 5000 steps a day enough" then went to fitness's walking answer. The phrase costs
          # nothing and holds the number-of-steps-a-day question where it belongs; a bias would
          # have taken "i walk an hour a day is that enough", which is fitness's own line.
          (("how many steps", "steps", "step count", "steps a day", "walking", "walk every day",
            "10,000 steps", "10000 steps"),
           ("how many", "a day", "in the day", "daily", "every day", "target", "should i",
            "enough", "recommended", "need")),
          "About 7,000 to 8,000 steps a day is where most of the benefit is - the health gain "
          "levels off there rather than at 10,000, which came from a 1960s pedometer advert - so "
          "add a daily twenty minutes on top of what you already do rather than chasing a round "
          "number. If you are a long way off, two ten-minute walks beat one long one because they "
          "are easier to keep up, and the walking you do getting about counts.",
          # Walking the dog, a pram, a hike and a step counter are other questions: the key needs
          # the number sense of "how many a day", so a bare "walk" line stays with whatever it
          # was about.
          ask=("how many", "how much", "should i", "do i need", "enough", "recommended",
               "target", "a day", "daily"),
          avoid=("dog", "puppy", "cat", "pram", "pushchair", "baby", "toddler", "hike", "hiking",
                 "rambling", "trek", "stairs", "step by step", "stepper", "pedometer", "app",
                 # "big walk planned tomorrow / should i take an umbrella" is a weather
                 # question, not a step target. Only the umbrella shape needs standing down:
                 # rain, snow and wind are how people set a step question ("how many steps a
                 # day when it rains"), and those keep the step answer.
                 "umbrella", "forecast", "suncream",
                 # what to wear on the walk is the clothing domain's buying question, and
                 # "do i need waterproof trousers for walking" was getting the daily target
                 "waterproof", "waterproofs", "overtrousers", "trousers", "jacket", "coat",
                 "boots", "wellington", "wellies", "rucksack", "gaiters",
                 # how many litres to carry is not how many steps to take: "how many litres do i
                 # need for a long walk" was given the daily step target, on "how many" and
                 # "walk". A quantity in litres or in water is travel.py's day-out answer.
                 "litre", "litres", "liter", "liters", "how much water",
                 # "how many steps are there in the eiffel tower" is a count of stairs up a
                 # building, and it was getting the daily target: a place has a number, and a
                 # person has a habit, and only the second is this entry. The landmarks are
                 # here by name because their own answer is the count, and the rest of the
                 # list is the shape of the place question - "are there", a climb, a tower.
                 "eiffel", "tower", "building", "cathedral", "church", "abbey", "castle",
                 "monument", "stadium", "pyramid", "pisa", "empire state", "shard",
                 "snowdon", "ben nevis", "scafell", "mountain", "climb", "climbing", "summit",
                 "are there", "storey", "storeys", "story", "stories", "flight", "flights",
                 "floor", "floors",
                 # "how many steps in the" was here and it earned nothing - the place words do
                 # the work - while it stood the target down on its own phrasing: "how many
                 # steps in the day is normal" is the daily question, and it went to a shrug.
                 # A distance is a conversion, not a target: "how many steps in a mile", "in a
                 # marathon", "in a 10k". The mile and the race answer the count.
                 "mile", "miles", "kilometre", "kilometres", "kilometer", "kilometers", "km",
                 "marathon", "half marathon", "5k", "10k", "parkrun", "race",
                 # a count asked in calories is a sum on that count, not a daily target
                 "calorie", "calories", "kcal",
                 # and weight coming off is its own answer: the number first, then the plate
                 "lose weight", "losing weight", "weight loss", "lose a stone", "lose fat",
                 "slim", "slimming")),
    # The steps questions that are not about how much to walk: a count that has a number
    # (a mile, a race) and a count up a building. Both were getting the daily target, which
    # is a habit answered to a fact question - the worst kind of wrong, because it reads as
    # confident and is about something else.
    entry("steps-in-a-distance",
          # Phrases rather than the bare word: "steps" is also the daily target's and the
          # staircase's, and every entry that keys it lowers what the word is worth for the
          # others (a key word only one entry uses scores higher). A count in a distance is
          # always asked as a phrase, so the phrase is all this one needs.
          # A step count is a way of asking as well as a way of answering: "how many miles is
          # 10000 steps" is this row backwards, and the count is the only word in it that names
          # the question, so the count sits in the first group. A distance word alone stays out
          # of that group, because "how many miles is a marathon" is the race row's line.
          (("how many steps", "steps per", "steps in", "steps to a",
            "10000 steps", "10,000 steps", "5000 steps", "5,000 steps", "12000 steps",
            "12,000 steps", "15000 steps", "15,000 steps", "20000 steps", "20,000 steps"),
           ("mile", "miles", "km", "kilometre", "kilometres", "kilometer", "kilometers",
            "marathon", "half marathon", "5k", "10k", "parkrun", "race",
            # a count on its own is the other half of the same question - "12000 steps" is
            # somebody asking how far that is - so every count in the first group is a word of
            # this one too, and "i did 12000 steps today" stays a report because the avoid list
            # holds the walking verbs
            "10000 steps", "10,000 steps", "5000 steps", "5,000 steps", "12000 steps",
            "12,000 steps", "15000 steps", "15,000 steps", "20000 steps", "20,000 steps")),
          _steps_in_a_distance,
          # The daily target owns "how many a day", and the landmark owns the count up a tower.
          avoid=("a day", "daily", "every day", "per day", "target", "recommended", "enough",
                 "eiffel", "tower", "building", "cathedral", "pisa", "stadium", "stairs",
                 # a count asked in calories is the energy in it, not the miles it covers
                 "calorie", "calories", "kcal",
                 # "i did 12000 steps today" is someone telling you about their day, so the
                 # reply says their count back in miles rather than the paragraph on stride
                 # length; the row still answers it, because standing down only left a shrug
                 # for a line the bot can answer well.
                 )),
    # The count up a building that travel.py does not already own: `eiffel-steps` has the
    # Eiffel Tower, and it was losing to the daily target on "how many steps are there in the
    # eiffel tower" until the target learned to stand down for a place. So this one stands down
    # for the Eiffel too, and answers the towers, the dome and the flight of stairs.
    entry("steps-up-a-building",
          # The same phrases-only rule as the mile entry above, plus the word the count is
          # asked with when a place follows it: "how many stairs in the empire state building".
          (("how many steps", "how many stairs", "steps up", "stairs up"),
           ("pisa", "leaning tower", "empire state", "cathedral", "st pauls", "dome",
            "monument", "stadium", "flight of stairs", "flight", "risers", "between floors",
            # "how many steps to climb one floor" is the same count as a flight, and it was
            # hedging because a storey had no word in the key at all.
            "floor", "floors", "storey", "storeys", "story", "stories",
            # "how many steps up the stairs" was a shrug on main while the promotion
            # answer took it, and it is the flight count with the stairs named.
            "the stairs", "up the stairs", "upstairs", "staircase", "stairway",
            "flight of stairs", "are there")),
          _steps_up_a_building,
          # A floor or a storey ties with the daily target on score ("how many steps on one
          # floor" has no "climb" for the target to stand down on), and a count of a staircase
          # is the fact that was asked for, so this one wins the tie.
          bias=1,
          # The Eiffel Tower is travel's answer, a person's habit is the daily target, a
          # distance is the mile answer, and the Shard has no public staircase to count.
          avoid=("eiffel", "a day", "daily", "every day", "per day", "to lose weight",
                 "mile", "miles", "km", "marathon", "5k", "10k", "shard",
                 # a floor of a shop or a price per floor is not a staircase
                 "rent", "price", "cost", "square", "sq ft", "apartment for")),
    # The count in the other two currencies. The ask word is required: a line that mentions a
    # step by accident ("sat down on the step for ten minutes") must not become a walking sum.
    entry("steps-calories",
          (("steps", "step count", "walking", "walk"), CALORIE_WORDS),
          _steps_calories,
          bias=2,
          ask=("how many", "how much")),
    entry("steps-in-a-time",
          (("steps", "step count", "walking", "walk"), TIME_WORDS),
          _steps_in_a_time,
          # a numeric length ("2 hours", "45 minutes") matches one key word where "an hour"
          # matches a phrase, so it ties on score with the daily target's "steps...how many";
          # the conversion is the question, so it wins the tie
          bias=3,
          ask=("how many", "how much"),
          # "should i walk an hour a day" is a how-much-should-i-do question, which the daily
          # target answers; only a length of time asked on its own is the conversion.
          # a calorie question that names an hour is a calorie question, not a step count
          avoid=("a day", "per day", "daily", "every day", "each day", "a week",
                 "to lose weight", "lose weight",
                 "calorie", "calories", "kcal", "energy")),
    # "How many steps to lose weight" got a diet card that never named a number: the word
    # "steps" was read and the question it asked was not. Steps are the smaller half of that
    # answer, so the number comes first and then the part that decides it.
    entry("steps-to-lose-weight",
          (("steps", "step count", "walking", "walk"),
           ("lose weight", "losing weight", "weight loss", "lose a stone", "lose fat", "slim",
            "slimming", "drop a dress size")),
          "Walking alone will not do it - what you eat decides most of it - but 8,000 to 10,000 "
          "steps a day is a fair target, and the gain is that it burns a little and keeps you "
          "from sitting down all day. The quicker half is the plate: a smaller portion of the "
          "starch, more protein and vegetables, and no drinks with sugar in. Half a kilo a week "
          "is a good rate, and the walking is easier to keep up than a gym plan.",
          bias=2),
    entry("strength-at-home",
          (("build muscle", "get stronger", "get stronger at home", "strength training",
            "home workout", "work out at home", "push ups", "push-ups", "pushups", "squats",
            "bodyweight", "resistance band", "resistance bands", "dumbbells", "dumbbell",
            "kettlebell", "free weights", "lift weights", "get stronger", "stronger"),
           ("home", "at home", "without", "no gym", "how", "start", "beginner", "beginning",
            "routine", "plan", "best", "way", "muscle", "stronger")),
          "Two or three sessions a week of five moves covers the whole body at home: squats or "
          "sit-to-stands for legs, press-ups (hands on a worktop if needed) for chest and arms, a "
          "row pulling a loaded bag or a band towards you for the back, glute bridges for hips, and "
          "a plank for the middle. Do two or three sets of eight to twelve, and add a little each "
          "week - more reps, a slower lower, a heavier bag - because muscle only grows when the "
          "last rep is hard. Two sessions a week beats five that you stop after a fortnight.",
          # Protein for muscle is `protein`'s question, and a knee or a bad back is a pain line.
          # So is a drink: "how do i make my tea stronger" is a brewing question, and the coffee
          # rows own the same line about a cup, so a stronger drink is never a workout.
          # How to do one movement properly (a squat, a press-up) is `fitness.py`'s, and its own
          # answer gives the form; the bodyweight plan is the whole-body question.
          avoid=("protein", "how much protein", "knee", "back pain", "sore back", "injury",
                 "shoulder pain", "sciatica", "osteoporosis", "sarcopenia",
                 "coffee", "espresso", "tea", "cuppa", "brew", "beer", "ale", "cider",
                 "form", "technique", "proper", "how deep", "depth", "posture",
                 # a stronger signal is the wifi's question, not a muscle's: "how do i get a
                 # stronger signal upstairs" matched the bare "stronger" in the key
                 "signal", "wifi", "wi-fi", "wireless", "internet", "broadband", "reception",
                 "router", "upstairs", "downstairs", "booster", "mesh")),
    entry("posture",
          (("posture", "slouching", "slouch", "hunched", "hunching", "rounded shoulders",
            "stand up straight", "sit up straight", "sit properly", "sitting properly",
            "sit straight", "at my desk", "at a desk", "sitting at a desk", "sitting all day",
            "sit all day", "desk job", "working at a desk",
            # The everyday way this question is asked is about where the chair, the screen or the
            # desk should go rather than about "posture", and every one of these was a shrug:
            # "how should i set up my chair" ("I'm not sure about that one, sorry"), "is my chair
            # too low", "how high should my monitor be", "where should my screen be". So the key
            # is the words that ask where a thing goes, and the thing itself is the second group:
            # a bare "my screen" would take "how do i record my screen" and "the screen on my tv
            # is cracked" (118 chats in the deck say "screen", 19 of them technology).
            "set up", "setting up", "set my", "too low", "too high",
            "how high", "how low",
            # "where should i go in spain" and "where should we stay" are places to travel,
            # not a screen height: the phrase only counts when the thing follows it.
            "where should my", "where should the", "where should i place",
            "sitting position", "sitting posture"),
           ("fix", "improve", "better", "bad", "correct", "how", "help", "desk", "chair",
            "screen", "office", "work", "should i", "ache", "aches", "aching", "achey",
            "hurt", "hurts", "sore",
            # "what is good posture" is the same entry asked as a definition and it was the one
            # shape of the question still hedging.
            "good", "what is", "proper", "right way",
            # "my posture is terrible" is the same question told as a complaint
            "terrible", "awful", "poor", "rubbish", "dreadful",
            # the thing whose place is being asked about, and the word "position" said instead
            "monitor", "position")),
          "Most bad posture is the chair and the sitting still, not the spine: set the screen so "
          "the top of it is at eye level, feet flat, elbows near a right angle, and get up every "
          "half hour - five minutes of standing beats a whole evening of trying to sit straighter. "
          "Then strengthen what holds you up: chin tucks, rows with a band, and squeezing the "
          "shoulder blades ten times a few times a day. Aches that come with numbness, weakness or "
          "pain down an arm are worth a GP or physio, not a new chair.",
          # A desk that needs cleaning, buying or moving is a different question, and so is a
          # spine that has been operated on.
          avoid=("height", "tall", "bra", "support", "corset", "brace", "baby", "newborn",
                 "how tall", "grow", "clean", "clear", "tidy", "organise", "organize", "buy",
                 "buying", "wobbly", "broken", "standing desk", "move the desk", "surgery",
                 "slipped disc", "sciatica",
                 # hands are not posture: biting, chewing and filing are the habit answer
                 "nail", "nails", "chewing", "biting", "bite", "thumb", "fingers", "typing",
                 "keyboard",
                 # and a feeling is the subject, not the place: "i keep panicking at my desk"
                 # is a panic line that says where, and the chair is not what it is about.
                 # "where should i put my desk" is a room to lay out, not a screen height.
                 # "how high should i mount the tv" is the fixing, and a shelf is its own.
                 "put", "mount", "mounting", "shelf", "shelves", "bracket",
                 ) + FEELING_WORDS,
          # "where should" is the place-shaped ask, and it needs the kit to go with it: see
          # _a_place_for_the_kit. A country, a car park or a passport has no chair in it. A body
          # that is short of sleep is not sitting badly either - "i keep nodding off at my desk"
          # got the chair and the screen height, which answers somebody falling asleep with the
          # height of a monitor.
          guard=all_of(_a_place_for_the_kit, not_a_sleepy_body)),

    entry("blood-pressure-numbers",
          (("blood pressure", "hypertension", "systolic", "diastolic"),
           ("lower", "reduce", "bring down", "high", "diet", "exercise", "naturally", "how",
            "help", "without", "worried",
            # "what is a healthy blood pressure" is the same advice asked as a definition, and it
            # was the one shape of the question still reaching a hedge.
            "healthy", "normal", "ideal", "what should it be", "what should mine be",
            "what should my", "should my")),
          # The target first, because "what is a healthy blood pressure" is the same entry as the
          # how-to and the number is what that asker wants.
          "Under about 120/80 is normal and 140/90 or over at home is high. Salt is the biggest "
          "single lever: under 6g a day means watching bread, cheese, ham, stock cubes, sauces and "
          "takeaways rather than the salt cellar. Add 150 minutes of walking a week, more fruit "
          "and vegetables, at most 14 units of alcohol and a few kilos off if you carry them, and "
          "a typical reading comes down about 10 points in a couple of months. A week of home "
          "readings, sitting still, is what a GP wants - and never stop a blood pressure tablet to "
          "try diet alone.",
          # A reading, a symptom, a tablet or someone else's pressure is a different question.
          avoid=("over 90", "over 140", "reading", "monitor", "stroke", "dizzy", "faint",
                 "pregnant", "my mum", "my dad", "my husband", "my wife", "tablet side effect",
                 # Not the words "tablets" or "medication": "can i lower it without tablets" is
                 # the how-to, and only the dosing and stopping shapes are somebody else's.
                 "should i take", "can i stop", "stop taking", "come off", "side effect",
                 "my tablets", "my medication", "on tablets", "started on")),
    # A reading is the commonest way the blood pressure question is actually asked - "is 145
    # over 90 high", "my reading was 150 over 95", "is 130 over 80 ok" - and the how-to entry
    # stands down on it ("over 90", "reading") because lower-it advice is not what a frightened
    # person wants first. What they want is what the number means and whether one reading counts.
    entry("snore-less",
          (("snoring", "snore", "snores", "snored", "loud breathing at night"),
           ("stop", "help", "how", "prevent", "reduce", "quiet", "partner", "wife", "husband",
            "night", "nightly", "bad", "loud",
            # The partner is often named without a word for what they are to the speaker: "my
            # oh is snoring", "my other half keeps me awake". Without these the line named
            # nothing the entry asks for and it fell through to whatever else matched - a
            # bills question, because "other half" also reads as a share of the money.
            "other half", "oh", "bf", "gf", "dh", "dw", "dp", "boyfriend", "girlfriend")),
          "Sleeping on your side, cutting out alcohol in the evening and losing a little weight "
          "fix it for most people who snore, and a blocked nose is worth treating with a "
          "decongestant or a steroid spray from the chemist for a couple of weeks to see. A "
          "pillow that keeps you off your back, or a tennis ball sewn into the back of a top, "
          "does the side-sleeping job. Snoring with gasping, choking or stopping breathing, or "
          "daytime sleepiness despite enough hours, needs a GP - that is sleep apnoea and it is "
          "treatable.",
          # No ask gate: the commonest way to raise it is a complaint about a partner's snoring,
          # and the practical answer is what that person wants.
          avoid=("apnoea", "apnea", "gasping", "stop breathing", "sleep study", "cpap", "baby",
                 "child", "kids", "dog", "cat", "puppy", "sleeping tablet")),
    # Losing weight is the commonest everyday health question there is and it met either the
    # search hedge or, worse, "a pharmacist or your GP can answer that today" - which is not
    # what anyone wants for belly fat. The honest mechanism is the answer: a modest deficit,
    # what to eat more of, and the fact that you cannot pick where the fat comes off.
    entry("weight-loss",
          (("lose weight", "lose fat", "losing weight", "slim down", "slimming", "belly fat",
            "flat stomach", "love handles", "get lean", "lose a stone", "lose a few pounds",
            # the same question in the words people use for the parts: a flat tummy, fat round
            # the waist, the thighs, the bingo wings
            "flat tummy", "fat around", "fat round", "around my waist", "round my waist",
            "thigh fat", "bingo wings", "muffin top", "saddlebags", "flabby",
            # "how do i lose my belly" is the same question with the part in the possessive
            "lose my belly", "lose the belly", "lose my tummy", "lose the tummy",
            "flatten my belly", "flatten my tummy", "flat belly",
            "lose 10kg", "lose a kg", "drop a dress size", "tone up", "get in shape",
            # the stalled scales, said as a question: "why am i not losing anything" is the
            # same subject as "how do i lose weight" and used to reach the memory row through
            # the word "losing"
            "not losing weight", "not losing anything", "not lost anything", "losing nothing",
            "scales wont move", "scales won't move", "scales havent moved",
            "scales have not moved", "scales are stuck", "weight is stuck",
            "stuck at the same weight", "weight wont shift", "weight won't shift",
            "not shifting the weight",
            # the amount of a loss, asked without the word "weight": the forgetting row's key
            # holds "lose" and its asks hold "how", so "how much should i lose" was answered
            # with the science of memory (see `_an_amount_of_losing`), and the amount asked
            # for is this row's subject
            "how much should i lose", "how much can i lose", "how much do i lose",
            "how much to lose", "how much do i need to lose", "how much weight should i lose",
            "how much weight can i lose", "how many pounds should i lose",
            "how many pounds can i lose", "how many kilos should i lose"),
           ("how", "what", "best", "way", "tips", "advice", "start", "safely", "quickly",
            "fast", "should i", "can i", "want to", "trying to", "help", "plan", "diet",
            "why", "stuck", "anything", "nothing", "same")),
          "A steady half a kilo to a kilo a week comes from a deficit you can live with, not a "
          "crash: cut the drinks, the handfuls and the second helping - usually 300 to 500 "
          "calories a day - and eat the protein and vegetables first, because they fill you up "
          "longer than the same calories of bread. Walk 30 minutes most days and lift something "
          "twice a week, so what goes is fat, not muscle. You cannot choose where it comes off: "
          "belly fat goes when the total comes down, and the scales stalling for a week is normal.",
          # A statement of intent keeps the warm line it gets today, so this waits for an actual
          # how-to. Distress about the body, a crash diet and someone else's weight are all a
          # different conversation.
          ask=("how", "what", "best", "way", "tips", "advice", "help", "start", "safely",
               "quickly", "fast", "plan", "diet", "why", "stuck"),
          avoid=("hate my body", "hate the way", "disgusting", "starve", "starving myself",
                 # a mat that is slimy is a laundry question: "slimy" is not a word the engine
                 # reads, so it was one slip from "slim" and a bath mat became a diet
                 "mat", "mats", "bath mat", "bath mats", "shower", "bathroom", "grout",
                 "floor", "floors", "towel", "towels", "sink", "drain", "tiles", "curtain",
                 "purge", "anorexic", "anorexia", "bulimia", "binge", "not eating", "cant eat",
                 "eat nothing", "my mum", "my dad", "my wife", "my husband", "my friend",
                 "my daughter", "my son", "my child", "kids", "toddler", "baby", "dog", "cat",
                 "puppy", "dress size 8", "wedding", "in two weeks", "by summer", "my face",
                 "my hair", "i keep losing weight", "losing weight without trying",
                 "unexplained")),
    entry("cut-down-sugar",
          (("sugar", "sugary", "sweets", "cravings", "sweet tooth", "chocolate", "biscuits",
            "fizzy drinks", "coke"),
           ("stop", "cut", "cut down", "eat less", "too much", "too many", "addicted",
            "addiction", "reduce", "quit", "how", "help", "less", "every day", "every night",
            "all the time", "cant stop", "can't stop", "eating too much", "eating too many")),
          "Cut the liquid sugar first, because it is the easiest to lose and the least filling: "
          "fizzy drinks, juice and squash swapped for water, sparkling water or tea. Then make the "
          "sweet thing a planned part of the day - a biscuit with the afternoon cup - instead of a "
          "thing you graze on, since grazing is what keeps the craving going. Protein and fibre at "
          "breakfast (eggs, porridge, yoghurt with nuts) takes the edge off the four o'clock "
          "search, and half a teaspoon less in the tea for a fortnight gets your taste down "
          "without noticing.",
          # a line about melting chocolate is a cooking question, and it has its own answer:
          # this entry keeps the eating and the cutting down
          avoid=("blood sugar", "diabetes", "diabetic", "insulin", "recipe", "baking", "cake",
                 # a sugar-free bake is a bake: the dish is named and the sugar is what's
                 # missing from it, so the swap and recipe rows answer. Without these, "how do
                 # i make sugar free banana bread" got this card, which is the diet answer to
                 # a baking question.
                 "banana bread", "bread", "loaf", "cookies", "cookie", "muffins", "muffin",
                 "sponge", "brownies", "brownie", "scones", "scone", "meringue", "pancakes",
                 "pancake", "pudding", "dessert", "gateau", "frosting", "buttercream",
                 "how much sugar is in", "sugar in a", "jam", "child", "kids", "toddler",
                 # a nutrient figure for one biscuit is the nutrient table's line, not the
                 # cutting-down card: "how much protein in a biscuit" is not a craving.
                 "protein", "calories", "calorie", "kcal", "carbs", "carb", "carbohydrates",
                 "fat", "fibre", "fiber", "nutrition", "nutrients",
                 "baby", "hyper",
                 "melt", "melts", "melting", "melted", "temper", "tempering", "seize", "seized",
                 "ganache", "dipping", "double boiler", "bain marie",
                 # a chocolate mark on a sofa or a shirt is a cleaning question, and the diet
                 # card answered it ("cut the liquid sugar first") because sugar and chocolate
                 # are the whole of the key
                 "off the", "off my", "off a", "out of", "out the", "stain", "stains", "stained",
                 "carpet", "sofa", "settee", "couch", "upholstery", "shirt", "jeans", "duvet",
                 "mattress", "cushion", "fabric", "washed", "scrub", "blot",
                 # a bake that went wrong is the bake's fault row: "my biscuits spread too much"
                 # was read as a craving and told to cut the fizzy drinks. The words that name a
                 # fault in the oven keep this card for the eating.
                 "spread", "spreads", "spreading", "flat", "dough", "batter", "oven",
                 "bake", "baked", "flour", "yeast", "soggy", "sank", "sunken", "lumpy",
                 "curdled", "rise", "risen", "prove", "proofed", "shortcrust", "icing")),
    # The number question: how long it should take to nod off. "how much sleep do I need" is
    # `sleep-hours` and the bedtime routine is `sleep-how-to`, so this is only the timing.
    entry("sleep-latency",
          (("fall asleep", "falling asleep", "get to sleep", "getting to sleep", "nod off",
            "sleeping"),
           # "take" is not in this key: adding it made the word common enough to move
           # "what should i take for a cold" off its remedy and onto the packing list
           ("how long", "long does it", "minutes", "normal", "quickly")),
          "Most people nod off within 10 to 20 minutes of lights out, and 30 minutes or more is "
          "the usual sign of a body clock that is not ready yet: shift your getting-up time "
          "earlier slowly rather than going to bed earlier. Lying there clock-watching makes it "
          "longer, so get up and do something dull for ten minutes and try again.",
          ask=("long", "minutes", "normal", "much", "quickly", "takes"),
          avoid=("plane", "train", "flight", "baby", "toddler", "child", "children", "medicine",
                 "melatonin", "tablet", "tablets", "falling asleep at my desk", "driving",
                 "driving tired", "wheel")),
    entry("sore-throat", (("sore throat", "throat", "tonsils", "swallowing", "hurts to swallow",
                          "hurts when i swallow"),
                          ("hurt", "hurts", "sore", "help", "helps", "soothe", "stop", "painful",
                           "scratchy", "worse", "what", "killing", "kills", "agony", "raw")),
          "Paracetamol or ibuprofen, plenty to drink, honey in warm water and a salt-water gargle "
          "(half a teaspoon in a glass) all ease it, and most sore throats are viral and settle in "
          "three to five days. See a GP if it lasts more than a week, you cannot swallow fluids, or "
          "it comes with a high fever and a stiff neck.",
          # Saying you have a sore throat is not asking for a remedy: the bot answers that with a
          # warm line, so this only fires when the line asks something (tests/test_ack.py).
          ask=("what", "help", "helps", "how", "ease", "soothe", "tip", "tips", "remedy", "stop",
               "painful", "scratchy", "worst", "swallow", "swallowing", "killing", "kills", "agony",
               "raw"),
          # The same verb does two jobs: a throat that hurts to swallow, and a machine that
          # swallows your card. "what should i do if my bank card is swallowed by the atm" was
          # answered with this gargle, so the machine and the thing it keeps are named here and
          # money.card-in-the-machine answers that line instead. A throat, a person or a pill
          # still reaches this one, because none of these words is in those lines.
          avoid=("sing", "singing", "singer", "voice", "lump", "cancer", "hoarse", "shout",
                 "shouting", "atm", "cashpoint", "cash machine", "swallowed my card",
                 "swallowed the card", "ate my card", "kept my card", "card stuck",
                 "sim card", "memory card", "sd card", "gift card", "loyalty card")),
    entry("headache", (("headache", "headaches", "head ache", "my head is banging",
                       "heads banging", "head banging", "head is thumping", "head pounding",
                       "head is pounding", "banging head", "head hurting", "head hurts",
                       "my head hurts"),
                       # "take" is not in this list on purpose: a key word shared with other
                       # domains' entries makes it common, and rarity is what breaks the tie
                       # between "what should i take for a cold" and the cold-weather list.
                       ("what", "help", "helps", "get rid", "cure", "stop", "painkiller",
                        "worst", "sore", "should i", "anything", "medicine")),
          _headache_reply,
          avoid=("migraine", "migraines", "chest", "child", "baby", "pregnant", "tablet", "tablets",
                 "dose", "doses", "how many", "overdose",
                 # what can be taken while pregnant or feeding is the medicine question, and it
                 # answers the symptom too - see body.py's what-can-i-take-pregnant-or-feeding
                 "pregnancy", "breastfeeding", "breast feeding", "nursing", "chestfeeding",
                 "expecting", "trimester"),
          # A named symptom outranks a word that only happens to be in the line: without this,
          # "i have had a headache since lunch, what can i take" ties with the packed-lunch entry.
          bias=2),
    # The old warning that water with a meal dilutes your digestion, which is what the question
    # underneath usually is.
    entry("water-with-meals", (("water", "drink", "drinking", "fluids"),
                               ("with meals", "with food", "with my meal", "with a meal",
                                "during meals", "before a meal", "before meals", "after a meal",
                                "after meals", "while eating")),
          "Water with a meal is fine: it does not dilute your stomach acid enough to matter, and "
          "it helps if you eat fast or get constipated. The only thing to watch is filling up on "
          "it so there is no room for the food - a glass or two rather than a pint before you sit "
          "down. Soup, tea and squash count towards the day the same way.",
          avoid=("dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets", "plant", "garden",
                 "tap", "abroad", "holiday"),
          # a line that names water and a meal is this question: "should i drink water before a
          # meal" tied with the food-around-training entry on "meal" and "before"
          bias=1),
    # The person who is drinking a lot and cannot stop. Nothing on the board asked it, but it was
    # the line the pet bowl used to answer, and "aim for six to eight glasses" is the answer to a
    # different question: a lot of thirst that will not quench is worth a GP, and that is the bit
    # a friend would say.
    entry("water-too-much", (("drink", "drinking", "drunk", "thirsty", "thirst", "water"),
                             ("too much", "so much", "stop drinking", "cant stop", "can't stop",
                              "always thirsty", "constantly thirsty", "never quenched",
                              "still thirsty", "all the time")),
          "If you are drinking far more than usual and still thirsty, see a GP: thirst that will "
          "not quench is worth a blood test, because it can be the first sign of diabetes. If it "
          "is just habit, spread the day's drinks out, keep water out of sight between meals, and "
          "sip rather than down a pint at once - but do not ration it, since your body asks for "
          "what it needs.",
          avoid=("dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets", "bowl", "plant",
                 "plants", "garden", "lawn", "tap", "abroad", "holiday", "alcohol", "beer", "wine",
                 "coffee", "before bed", "night")),
    # "glasses" is not a water word on its own: half the people who write it are looking for
    # their spectacles ("i keep forgetting where i put my glasses" was answered with the daily
    # figure). A water word has to be on the line, and then "how many glasses of water a day"
    # and "8 glasses" reach this through the ask below.
    entry("water-intake", (("water", "fluids", "litres", "liters",
                            "hydration",
                            # A counted glass is a measure of water: "5 glasses a day enough" and
                            # "should i drink 8 glasses a day" are the daily figure asked without
                            # the word water, and they came back empty (or as the alcohol units)
                            # once "glasses" on its own stood down. What makes it a measure is the
                            # count in front of it, so the count is in the phrase.
                            "glasses a day", "glasses a week", "glasses daily"),
                           ("day", "daily", "drink", "drinking", "drinks", "how much",
                            "enough", "more", "forget", "forgetting", "forgot", "remind",
                            "remember", "habit", "keep", "8 glasses", "eight glasses",
                            "glasses of water")),
          "Six to eight glasses a day, about 1.5 to 2 litres, is plenty, and more in heat or after "
          "exercise; tea, coffee, milk, squash and food all count towards it, and pale straw-coloured "
          "urine is the check that you are about right. If you forget, keep a filled bottle where you "
          "sit and drink a glass with every meal.",
          # How much, or a day: a bottle in a gym bag and a pan of salted water are other questions.
          # "Should I drink more water" is the same figure asked without the "how much", and it
          # had no entry at all: the water question is the only one that leaves out the amount.
          ask=("much", "many", "litres", "liters", "daily", "day", "glasses", "enough",
               "drink more", "more water", "enough water", "should i drink", "forget",
               "forgetting", "forgot", "remind", "remember", "hydrat"),
          avoid=("plant", "plants", "flowers", "garden", "lawn", "turf", "sod", "grass",
                 "seedbed", "tomato", "tomatoes", "seedlings", "houseplant", "houseplants",
                 "where i put my glasses", "where are my glasses", "where my glasses",
                 "left my glasses", "lost my glasses", "find my glasses", "my glasses are",
                 "broke my glasses", "glasses broke", "clean my glasses", "glasses dirty",
                 "glasses are dirty", "smudged", "spectacles", "sunglasses", "reading glasses",
                 "optician", "glasses case", "contact lenses", "new glasses",
                 # A fault on a pair of glasses rarely puts the word next to the object: they
                 # steam up, fog, get lost, get left at home. "i keep losing my glasses" and
                 # "my glasses keep steaming up" were both the six-to-eight figure.
                 "losing my glasses", "lose my glasses", "glasses go missing",
                 "forgot my glasses", "forget my glasses", "forgotten my glasses",
                 "keep forgetting my glasses", "steaming up", "steams up", "steam up",
                 "fogging up", "fogs up", "fogged up", "fog up", "lens", "lenses", "specs",
                 "wearing glasses", "wear glasses", "pair of glasses", "glasses are broken",
                 "glasses fell", "sat on my glasses", "glasses slide",
                 # Watering a plant is not drinking it, and the plant words above are no help
                 # when the line only has the pronoun: after "my tomato plants have yellow
                 # leaves", "i water them every day" came back with six to eight glasses a
                 # day. The verb is the give-away - water them, water it once a week, feed and
                 # water - so the phrases that make water a verb are here. Not "watering" or
                 # "watered" on their own: the matcher reads those forms of "water", which
                 # would turn the ordinary how-much-should-i-drink line into a shrug.
                 "water them", "water it", "water the", "water my", "water your", "water once",
                 "water twice", "water every", "water in the morning", "water in the evening",
                 "water deeply", "feed and water",
                 "hose", "water butt", "water bill",
                 "kettle", "boiler", "bill",
                 "bills", "leak", "leaking", "pool", "swim", "filter", "softener", "bottle",
                 "bottles", "salt", "salting", "boil", "boils", "boiling",
                 # how much water goes in a pan or a cup is a cooking question, and so is a
                 # grain or a flour that is cooked in it: "how much water for couscous" was
                 # answered with six to eight glasses a day
                 "cup of tea", "cups of tea", "pasta", "rice", "pan", "saucepan", "stock",
                 "couscous", "quinoa", "bulgur", "porridge", "oats", "oatmeal", "dough",
                 "batter", "flour", "recipe", "gravy",
                 # a child or a pregnancy has its own answer, and the adult figure is the
                 # wrong one for either: a health visitor or midwife should be the one to say.
                 "baby", "babies", "toddler", "toddlers", "child", "children", "kid", "kids",
                 "infant", "newborn", "year old", "years old", "pregnant", "pregnancy",
                 "breastfeeding", "nursing", "formula",
                 # An animal drinks by weight, so a dog or a cat has its own answer: pets.py
                 # reads the millilitres per kilo, and the human glasses figure is the wrong one.
                 "dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens",
                 "pet", "pets", "hamster", "hamsters", "rabbit", "rabbits", "guinea pig",
                 "parrot", "horse", "horses", "litter tray",
                 # a drink at bedtime is a sleep question, not a daily total
                 "before bed", "at night", "before sleeping", "before sleep",
                 # How much water a bath holds, a washing machine uses or a bucket takes is a
                 # question about litres, and six to eight glasses is the wrong answer to it:
                 # home.water-use has the figures, so every fixture and container stands this
                 # row down. A repair on the same fixture never had the figure in it anyway.
                 "bath", "baths", "bathtub", "shower", "showers", "toilet", "toilets", "flush",
                 "cistern", "bucket", "buckets", "mop bucket", "paddling pool", "hot water bottle",
                 "washing machine", "dishwasher", "tank", "water tank", "hose", "hosepipe",
                 "sprinkler", "watering can",
                 # A litre of something that is not drunk is priced or measured, not drunk: the
                 # price entry answers "how much is a litre of petrol", and this row was taking
                 # "how much is a litre of paint" and "of milk". The phrase is the shape, so a
                 # bare "paint" or "milk" stays out of the list and "does milk count" still works.
                 "litre of paint", "litre of petrol", "litre of diesel", "litre of oil",
                 "litre of olive oil", "litre of bleach", "litre of screenwash",
                 "litre of emulsion", "litre of white spirit", "litre of milk",
                 "litre of juice", "litre of beer", "litre of wine")),
    # The row answered "what spf should i use" and nothing else: a person asking how to protect
    # their skin in the sun, which sunscreen to buy, or how to stop their face burning was given a
    # search punt, because the words they used were the sun and the skin, not "sunscreen".
    entry("sunscreen", (("sunscreen", "suncream", "sun cream", "spf", "sunblock",
                         "sun protection", "protect my skin", "protect your skin",
                         "protect skin", "skin in the sun", "skin from the sun",
                         "factor 30", "factor 50", "sun factor", "what factor",
                         "which factor", "what spf",
                         # a face that burns is the same question as the factor, and the line
                         # says the sun rather than the cream
                         # A key made only of phrases never scores: the two-word rule wants
                         # two different key words, so "my face burns in the sun" was a shrug
                         # while "burning in the sun" would have matched. The bare verbs and
                         # the part that burns are what the line actually says.
                         "burn", "burns", "burning", "burnt",
                         "burning in the sun", "burn in the sun", "burns in the sun",
                         "burning in sunlight", "face burning", "get burnt", "gets burnt"),                        ("use", "wear", "need", "should", "what", "which", "high", "apply",
                         "reapply", "protect", "choose", "choosing", "best", "buy", "stop",
                         "prevent", "everyday", "day to day", "enough",
                         # the part that burns is the second word: "my face burns", "my nose
                         # burns", "my shoulders burn"
                         "face", "skin", "nose", "shoulders", "arms", "chest",
                         # "does sunscreen block uv" and "how does spf work" were punts: the
                         # answer is in the card already (SPF is measured for UVB, the stars
                         # for UVA), so the row only needed the words people use for it.
                         "block", "blocks", "blocking", "uv", "uva", "uvb", "work", "works")),
          "Use a broad-spectrum sunscreen of at least SPF 30, with four or five stars for UVA, "
          "and use more than feels right: about two tablespoons for an adult in a costume, "
          "reapplied every two hours and after swimming or sweating. SPF 50 for children, and "
          "sunscreen adds to shade, a hat and a shirt rather than replacing them.",
          # not a bare "factor": it is in this row's own key ("factor 30", "factor 50"), and a
          # stand-down on the word killed both, so "should i use factor 50" was a punt and
          # "what factor sunscreen should i use" reached the maths card. The maths lines say
          # common factor, highest common factor.
          # a factor of 12 is arithmetic and a burn with no sun in the line is the burns card's
          guard=lambda understood: (_a_factor_question_without_the_sun(understood)
                                    and _a_burn_without_the_sun(understood)),
          # "does sunscreen stop a tan" is a question about whether a tan is safe, not about how
          # to put cream on: the tan row says what a tan is and that it is damage. "stop" is in
          # this row's key, so the tan words have to stand it down.
          avoid=("common factor", "highest common factor", "isan", "insurance",
                 "tan", "tanning", "tanned", "suntan", "sun tan", "get a tan", "have a tan")),
    # "does sun cream go off" was reaching the yogurt-and-cream row in still_ok ("stir it back
    # in"), and an out-of-date sunscreen is a protection question, not a food one.
    entry("sunscreen-expiry",
          (("sun cream", "suncream", "sunscreen", "sunblock", "spf"),
           ("go off", "gone off", "goes off", "out of date", "use by", "expire", "expires",
            "expired", "expiry", "last", "lasts", "keep", "keeps", "shelf life", "old",
            "from last year", "last summer", "still good", "still work")),
          "Sunscreen keeps about three years unopened and about a year once it is open, so write "
          "the month on the bottle when you start it. Out of date it does not turn dangerous, it "
          "just stops protecting as the label says: if it has separated, gone gritty or smells "
          "odd, replace it, and a bottle that has sat in a hot car all summer is the one to bin."),

    # The sunscreen lifetime row's twin, asked of every jar in the bathroom: how long a cosmetic
    # keeps. Two reviewers of this change asked for it - the `still_ok` stand-down stops the
    # yogurt card from answering "has my moisturiser gone off", and without this row the line is
    # a punt, which is worse than the wrong card it used to get.
    entry("cosmetic-lifetime",
          (("moisturiser", "moisturizer", "face cream", "facial cream", "day cream", "night cream",
            "body lotion", "face lotion", "skin cream", "serum", "cleanser", "foundation",
            "makeup", "make up", "mascara", "lipstick", "concealer", "blusher", "blush",
            "eye cream", "hand cream", "body cream", "shaving cream", "spot cream", "nappy cream",
            "eczema cream", "lip balm", "lip salve", "toner", "aftershave"),
           ("go off", "gone off", "goes off", "out of date", "use by", "expire", "expires",
            "expired", "expiry", "last", "lasts", "keep", "keeps", "shelf life", "old",
            "from last year", "still good", "still ok", "still fine", "still alright",
            "still work", "how long",
            # a cream that has turned is said by its smell, and the fridge's yogurt card owns
            # "smells funny" - the jar on the shelf is this row's once the word is a cosmetic
            "smell", "smells", "smelly", "smells funny", "smells off", "smells odd",
            "smells sour", "separated", "gritty", "gone gritty")),
          "Most creams keep about 30 months sealed and 12 months once they are open, so write the "
          "month you opened it on the jar; a cleanser or a serum is roughly the same, and mascara "
          "is the short one at three months because the wand picks up bacteria. A cream that has "
          "separated, gone gritty or smells sour should go, and anything you would not put on a cut "
          "does not belong on your face."),

    # A day by a window is the way most people get their colour without noticing, and main had
    # no answer for it. The subject is the glass, so a sun cream or a sunbed question is not this.
    entry("tan-through-glass",
          (("tan", "tanned", "tanning", "a tan", "tan line", "tan lines", "suntan", "sun tan",
            "uv", "uva", "uvb"),
           ("window", "windows", "glass", "car", "car window", "office", "driving", "drive",
            "through", "indoors", "inside", "sunlight", "sun", "block", "blocked", "blocking",
            "protect", "protects")),
          # no "Yes:" opener: the row catches "does glass block uv", and the honest answer to that
          # is that it blocks the burning UVB but not the tanning UVA
          "The UVA that tans and ages skin goes straight through glass, so a day by a window "
          "or a long drive gives you colour and lines, while the UVB that burns is mostly "
          "filtered out. It creeps up on you because you do not feel it getting hot. Glass is not "
          "sun protection, so use SPF 30 on the arm and face nearest the window if you sit there "
          "for hours, and do not treat a sunbed as a shortcut to the same thing.",
          avoid=("sunscreen", "sun cream", "suncream", "spf", "factor", "sunblock", "sunburn",
                 "after sun", "aftersun", "fake tan", "spray tan", "self tan", "false tan",
                 "sunbed", "tanning bed", "tanning shop", "moisturiser", "exfoliate", "streaks",
                 "clean", "cleaning", "cleaner", "smear", "smears", "dust", "dusty", "dirty",
                 "squeegee", "windscreen", "wipers", "condensation", "double glazing", "glazier",
                 "insulate", "insulation", "curtains", "blinds", "replace", "repair", "cracked",
                 "broken", "lamp", "nails", "filter", "purifier", "sparkle", "vinegar")),
    # A tanning bed is not glass: the rays are the same two, so it sits beside the window row
    # rather than inside it, and "is a sunbed safe" was a shrug.
    entry("sunbed-risk",
          (("sunbed", "sunbeds", "tanning bed", "tanning beds", "tanning salon", "tanning shop",
            "uv bed", "fake tan bed"),
           ("safe", "bad", "harm", "harmful", "risk", "risks", "cancer", "ok", "worth",
            "healthy", "damage", "how often", "should i", "is it")),
          "No: a sunbed gives out mostly UVA, the ray that ages skin and drives melanoma, in doses "
          "several times stronger than midday sun, and using one before 35 raises the melanoma "
          "risk by around three quarters. Under-18s are banned from them in the UK. A spray tan or "
          "a gradual self-tan gives the same colour without the damage.",
          avoid=("window", "glass", "bed size", "bed sheets", "mattress", "sleep")),
    entry("freckles", (("freckle", "freckles", "freckled"), ("why", "get", "have", "sun", "skin",
                                                             "cause", "appear")),
          "Freckles are clumps of the brown pigment melanin that your skin makes in response to "
          "sun, so they show up most on fair skin in summer and fade in winter. They are harmless, "
          "and the fairer your skin the more carefully you need to cover up: sunscreen and a hat "
          "stop new ones and protect against sun damage."),
    # "can i crush a tablet" and "is it ok to break a pill" got a maker's support page and, worse,
    # the job contract: a tablet that cannot be swallowed whole is a pharmacy question with a
    # short, definite answer, and the one thing to check is whether it is a modified-release one.
    entry("cut-or-crush-a-tablet",
          (("tablet", "tablets", "pill", "pills", "capsule", "capsules", "medicine", "medication",
            "paracetamol", "ibuprofen", "antibiotic", "antibiotics"),
           ("crush", "crushed", "crushing", "split", "splitting", "break", "breaking", "broken",
            "cut", "cutting", "halve", "halved", "half", "in half", "in two", "swallow",
            # the phrase, not just the verb: "can i break a tablet" and "is it ok to break a
            # tablet" lost to the job contract and to the repeat-prescription card on the main
            # this was rebased onto, because a bare "break" or "tablet" is a word those also hold
            "break a tablet", "break a pill", "break my tablet", "break my pill",
            "break the tablet", "break the pill", "break it in half", "cut a tablet",
            "cut a pill", "split a tablet", "split a pill", "split the tablet",
            "swallowing", "dissolve", "chew", "chewed", "grind", "open the capsule")),
          "Check the box first: if it says modified release, extended release, MR, XL or SR, or "
          "that the tablet is film-coated or a capsule, do not crush, split or open it - the whole "
          "dose comes out at once. An ordinary plain tablet can usually be broken along the score "
          "line, or crushed and taken in water or yoghurt. Ask a pharmacist for the same medicine "
          "as a liquid or a dispersible tablet; they do that most days and it costs nothing to ask.",
          # an overdose, a child, or a whole swallowing problem is another answer, and a serious one
          avoid=("overdose", "too many", "took too much", "swallowed the pack", "suicide", "harm",
                 "child", "children", "toddler", "baby", "kid", "kids", "son", "daughter",
                 "cant swallow", "can't swallow", "cannot swallow", "too big", "stuck", "choking",
                 "throat", "tablet stuck", "side effect", "side effects", "contraceptive",
                 "pill free week", "morning after", "antibiotic course", "dose", "dosage")),
    entry("earwax", (("earwax", "ear", "ears"),
                     ("blocked", "block", "clean", "cleaning", "remove", "build up", "cotton",
                      "buds", "bud", "plug", "plugged",
                      # "how do i get wax out of my ear" and "my ear is full of wax" name the wax
                      # and what to do about it without either of the words above
                      "out", "get wax out", "full of wax", "drops", "soften", "syringed",
                      "microsuction", "syringe", "clear",
                      # "wax" belongs in this half, not the ear half: on its own it took
                      # "how do i wax my car" and "what wax should i use on my car", and the
                      # answer was olive oil drops and no cotton buds. An ear word has to be
                      # somewhere in the line for this to be an ear question.
                      "wax", "waxing")),
          "Leave earwax alone: it works its way out, and cotton buds push it back and pack it "
          "against the eardrum. If it blocks your hearing, a pharmacist can sell you olive or "
          "sodium bicarbonate drops for a week; if that does not shift it, a nurse can syringe or "
          "microsuction it. Never put anything smaller than your elbow in your ear.",
          ask=("blocked", "block", "clean", "cleaning", "remove", "wax", "cotton", "buds", "plugged",
               "build", "out", "drops", "soften", "full of wax", "syringe", "clear"),
          # the same guard as the blocked-ear answer: a table has wax on it too, and that one is
          # the cleaning entry's question
          avoid=("phone", "earphones", "headphones", "buds in", "airpods", "ringing", "infection",
                 "table", "tables", "tablecloth", "floor", "carpet", "wood", "wooden",
                 "furniture", "worktop", "skirting", "cloth", "fabric")),
    entry("bloating", (("bloating", "bloated", "wind", "windy", "trapped wind", "fart",
                        "farting",
                        # "how do i sort out my gut" names the organ and nothing else: the
                        # symptom word never appears, so the subject is the gut itself.
                        # "digestion" is not one of these: "how do i improve my digestion" is the
                        # digestion card's line, and this row answered it about bloating.
                        "gut", "guts", "my gut"),
                       ("after", "meals", "eating", "help", "stop", "reduce", "get rid", "why",
                        "always", "much",
                        # "my stomach is bloated all the time" had one key word and the quality
                        # of a shrug: the words people put round a bloat without naming a meal,
                        # and the feeling said without the word bloating twice ("my stomach
                        # feels bloated"), which names the part and the feeling instead
                        "all the time", "constantly", "every day", "most days", "for weeks",
                        "feels", "feel", "stomach", "tummy", "belly",
                        # "how do i settle my gut" and "can i sort out my wind" ask for the fix
                        # with none of the words above; the improving verb arrives from IMPROVE
                        "settle", "calm", "sort") + ASK_ABOUT + IMPROVE),
          "Most bloating is gas and fluid moving slowly: eat more slowly, drink less fizzy stuff, "
          "and try cutting back on one thing at a time for a fortnight, usually fizzy drinks, "
          "chewing gum, or a big jump in fibre. A daily walk helps, and peppermint tea or capsules "
          "settle wind for many people. See a GP if you are bloated most days for weeks, lose "
          "weight without trying, or have blood in your stool.",
          # "wind" is the word for gas, so it also reads a door or a gate banging in the wind:
          # "how do i stop a door banging in the wind" is a latch question, and a bloating answer
          # is worse than a pass. Anything about the house makes the line the home domain's.
          avoid=("door", "doors", "gate", "gates", "window", "windows", "latch", "hinge",
                 "draught", "draft", "slam", "slamming", "bang", "banging", "cupboard",
                 "drawer", "radiator", "pipe", "pipes", "trampoline", "flag",
                 # a gut is also a feeling and a verb: "i should have trusted my gut", "gut
                 # feeling", "gutted", "gut the kitchen" are not a question about wind
                 "gut feeling", "gut instinct", "trust my gut", "trusted my gut", "beer gut",
                 "gut the", "gut a", "gut reaction",
                 # the ask words now in this key would otherwise answer the weather: "can wind
                 # blow my fence down" is what the air outside does, not what a body does
                 "fence", "fences", "roof", "roofs", "tree", "trees", "garden", "kite",
                 "sail", "sailing", "storm", "storms", "gale", "weather",
                 # the bare "better" that IMPROVE brings reads a statement as a request:
                 # "my gut is better today" is someone telling you their news, not asking how
                 # to improve it. Only the report shapes are fenced, so "what is better for
                 # bloating" and "is walking better than lying down" keep this answer.
                 "better today", "better now", "is better now", "is much better", "much better",
                 "feels better", "feeling better", "gut is better", "getting better")),
    entry("eyes-test", (("eye test", "eyes test", "eyes tested", "eye exam", "optician",
                         "eyes checked", "get my eyes", "sight test", "sight check",
                         "eyesight test", "eye health check", "sight tests"),
                        ("often", "how often", "regular", "should", "need", "due", "when",
                         "free", "cost", "how much", "time")),
          _eyes_test,
          ask=("often", "when", "should", "need", "due", "free", "cost", "regular", "how much"),
          # main now has two shorter eye-test cards (health and science's own frequency row), and
          # this one carries the money-first and yes-first wording the tests and the deck expect.
          bias=3,
          # "how much does an eye test cost" is the money table's question, and it answers it
          # with the high-street range and the hidden extras: this entry is the interval and the
          # free-or-not question.
          avoid=("how much", "cost of", "price", "prices", "cheapest", "afford",
                 "dry eyes", "dry eye", "sore eyes", "red eyes", "itchy eyes", "stye",
                 "conjunctivitis", "contacts", "contact lens", "contact lenses", "glasses",
                 "scratched", "laser", "cataract", "floaters",
                 # The reply says "every two years suits most adults", and this row carries a
                 # bias of 3, so it beat the child's own card on the child's question:
                 # "when should my child have an eye test" and "when should a baby have their
                 # first eye test" were both told the adult interval. The sibling row
                 # (eye-test-frequency) already stands down for a child; this one is the row
                 # that actually wins, so the same words belong here.
                 "child", "children", "kids", "kid", "son", "daughter", "toddler", "baby",
                 "school", "squint", "squinting", "year old", "years old")),
    entry("toothache-weekend", (("toothache", "tooth ache", "tooth hurts", "tooth is killing",
                                 "dental", "dentist"),
                                ("weekend", "dentist is shut", "shut", "closed", "out of hours",
                                 "emergency", "cant get", "can't get", "night", "help",
                                 "what do i do", "do i do")),
          "Ring 111 for the out-of-hours dental service: they can book you an urgent appointment "
          "at a surgery that is open, and they can prescribe antibiotics if the tooth is infected. "
          "Until then, take ibuprofen or paracetamol as the packet says, keep the mouth clean, and "
          "do not put aspirin next to the gum. Swelling that closes the eye, a fever or trouble "
          "swallowing is a hospital job, so ring 999 or go to A&E.",
          ask=("what do i do", "weekend", "shut", "closed", "out of hours", "help",
               "cant get", "can't get", "night", "emergency"),
          avoid=("wisdom tooth extraction", "braces", "whitening", "veneer", "implant",
                 "how much does", "cost of", "price")),
    entry("toothbrush-change", (("toothbrush", "toothbrushes", "electric toothbrush",
                                "brush head", "brush heads"),
                               ("change", "changing", "replace", "new one", "often", "long",
                                "when", "how often", "should i")),
          "Change it every three months, or sooner if the bristles splay: a worn brush cleans "
          "much less well. Electric brush heads are the same, rinsing it after use and letting it "
          "dry upright, and swap it after any illness if it has been in a shared pot."),
    entry("caffeine-limit", (("caffeine", "coffee", "coffees", "espresso", "energy drinks",
                              "tea", "teas"),
                             ("much", "too", "limit", "safe", "how many", "too much",
                              # a count of cups is the same question asked with a number in it:
                              # "i have 12 cups of coffee a day" was priced by the money domain.
                              "day", "week", "cups", "daily", "weekly")),
          _the_limit_for_the_drink_named,
          # A question with a how much or a limit in it, not a line that mentions coffee: "i had tea
          # tonight and couldnt sleep" and "how much water for two cups of tea" are not this.
          ask=("much", "too", "limit", "safe", "many", "day", "week", "cups", "daily",
               "weekly"),
          avoid=("plant", "plants", "grounds", "garden", "compost", "coffee table", "machine",
                 "mug", "shop", "cafe", "pod", "pods", "stain", "stains", "kettle",
                 "tea bag", "tea bags", "leaves",
                 # a fault said about the cup is the brew question, not a dose one: "my coffee is
                 # too strong" reached this entry through "too" and was told the daily limit.
                 "weak", "watery", "bitter", "sour", "strong", "stronger", "taste", "tastes",
                 "tasting", "brew", "brewing", "brewed", "stewed", "grind", "grinder", "strength",
                 # the limit is half as much in pregnancy, so let a health line that knows that
                 # answer it rather than leading with the adult figure
                 "pregnant", "pregnancy",
                 # what it costs is the money domain's question, and a count of cups is not:
                 # "i buy a coffee every day, how much is that a year" was reaching this entry
                 # once "too much" was a key phrase.
                 "spend", "spends", "spent", "spending", "cost", "costs", "buy", "buys",
                 "buying", "price", "prices", "expensive", "afford", "budget", "money",
                 "a year", "per year", "a month", "save", "saving", "savings",
                 # a brewing amount counts cups too: "how much water for two cups of tea" is the
                 # kettle's question, not a caffeine limit
                 "how much water", "water for", "how many cups of water",
                 # A cup that is an occasion is not a dose question: "then she sat down with a
                 # cup of tea" is the deck's own two-turn chat and on main it got the safe limit
                 # for the drink she was holding (garnet-notebook, #8152). A line that asks a
                 # real limit still says "a day", "too much" or "how many", which none of these
                 # words do.
                 "sat down with", "sitting with", "over a cup of", "over a mug of",
                 "cup of tea and a", "cuppa and a", "sipping", "sipped",
                 # the sugar or the calories in the cup is the nutrient table's question, not
                 # the caffeine limit's: "how much sugar is in a cup of tea", "how many calories
                 # in a cup of tea" and "does tea have sugar in it" were all told the 400mg limit
                 # while the person was asking about a spoonful
                 "sugar", "sugars", "sugary", "calorie", "calories", "kcal", "milkshake",
                 # a pot that overflowed is the leftovers row's: "i made too much tea" was
                 # answered with the daily limit once the drink words met "too much".
                 "made", "cooked", "leftover", "leftovers", "left over", "freeze", "fridge",
                 "reheat", "keeping", "keep it",
                 # how much to make is a catering question, not a dose one
                 "to make", "should i make", "for 4", "for 6", "for 8", "for 20", "per person",
                 # a child's share is the kids row's answer, and the nudge on this row was
                 # enough to take "how much caffeine can my 5 year old have" off it
                 "child", "children", "kid", "kids", "son", "daughter", "toddler", "baby",
                 "year old", "years old", "teen", "teenager", "teenagers", "school",
                 # "how much coffee for 20 people" is how much to make, and the measures table
                 # answers it with 12g a mug; this entry was reading the "how much" as a dose.
                 "people", "cafetiere", "jug", "tablespoon", "tablespoons", "ground coffee",
                 "mugs", "per mug", "per cup", "mug of")),
    # "how much cola is too much" was a shrug, and it is the same question as the coffee one with
    # a smaller cup. It is a row of its own because cola added to the limit row's key moved "how
    # many cups of coffee is too much" off that row and onto the cut-down card: a key tuple is
    # scored as a whole, so the words go where the question is.
    entry("cola-caffeine-limit",
          (("cola", "coca cola", "pepsi", "fizzy drink", "fizzy drinks", "diet coke"),
           ("much", "too", "limit", "safe", "how many", "too much", "day", "week", "cans",
            "daily", "weekly")),
          _CAFFEINE_LEAD["cola"] + _CAFFEINE_TAIL,
          ask=("much", "too", "limit", "safe", "many", "day", "week", "cans", "daily",
               "weekly"),
          # "should i give my child cola" is the child's question, and a can with a meal is not
          # a limit question.
          avoid=("child", "children", "kid", "kids", "son", "daughter", "toddler", "baby",
                 "year old", "years old", "teen", "teenager", "pregnant", "pregnancy",
                 "stain", "stains", "teeth", "tooth", "sugar", "calories", "plant", "plants",
                 "cake", "ham", "chicken", "rum", "vodka", "whisky", "whiskey", "mixer",
                 "diet", "recipe", "bottle", "bottles", "price", "cost", "buy")),

    # "how much caffeine can my 5 year old have" was answered with the per-drink table, which
    # is a fact about the cup and not about the child. A child's share is its own answer.
    entry("caffeine-kids",
          (("caffeine", "coffee", "coffees", "tea", "teas", "cola", "energy drinks",
            "energy drink", "fizzy"),
           ("child", "children", "kid", "kids", "son", "daughter", "toddler", "baby",
            "year old", "years old", "teenager", "teenagers", "teen", "school")),
          "Children under 12 are better off with no caffeine at all: a small body clears it "
          "slowly, so a can of cola at lunch can still be keeping a seven-year-old awake at ten. "
          "Teenagers should stay under about 100mg a day - one coffee, or two cans of cola - and "
          "none after early afternoon. Energy drinks are the usual culprit and a big can is "
          "160mg or more, so they are worth a firm no under 16, and none of it replaces sleep.",
          avoid=("plant", "plants", "grounds", "garden", "compost", "coffee table", "mug",
                 "pod", "pods", "stain", "stains", "kettle", "brew", "brewing", "taste",
                 "tastes", "bitter", "sour", "machine", "shop", "cafe")),
    # "how are mountains made" is a school question, so the mechanism leads and the three ways
    # of making one follow in one sentence each.
    entry("mountains-form",
          # no "andes": the typo repair reads a plain "and" as it, and "and how do i know when
          # ive spent it" became a mountain question
          (("mountain", "mountains", "mountain range", "himalayas", "alps"),
           ("form", "formed", "forming", "made", "make", "created", "created", "grow", "grown",
            "how", "why", "build", "built")),
          "Most mountains are made by two plates of the earth's crust pushing together, which folds "
          "and crumples the rock into ranges like the Himalayas and the Alps. Others are volcanoes "
          "piled up by eruptions, or blocks of crust lifted along a fault, like the Sierra Nevada.",
          # how high, how old and which is the biggest are other answers. A count of steps is
          # not a geology question either: "how many steps up a mountain" was answered with
          # plate tectonics because the line has "how" in it and "mountain", and it reads as
          # someone asking for a number the bot does not have rather than for the mechanism.
          avoid=("highest", "tallest", "everest", "oldest", "biggest", "longest", "climb",
                 "climbing", "cold", "snow", "altitude", "height", "how high", "steps",
                 "stairs", "staircase")),
    # What a calorie is, rather than how many are in a food: the food question is answered from
    # the calorie table in cooking.py, so this asks for the definition.
    entry("what-is-a-calorie", (("calorie", "calories", "kcal", "kilocalorie", "kilocalories"),
                                ("what is", "whats", "what are", "mean", "meaning", "define",
                                 "explain", "actually")),
          "A calorie is a unit of energy - the heat that raises 1 gram of water by 1 degree "
          "Celsius - and the calories on a food label are really kilocalories, a thousand of "
          "those each. Most adults need around 2,000 to 2,500 of them a day, and a pound of body "
          "fat holds about 3,500.",
          ask=("what", "mean", "meaning", "define", "explain", "tell me about")),

    # --- school-level facts people ask for by name -------------------------------
    # What water is, rather than when it boils or how much of it to drink: "what is water made
    # of" reached the cooking row `fix-watery`, whose food half has "what can i make with" in it
    # and whose "watery" is the same form as "water", and the line was told to simmer the lid off
    # a pan. "what is water" and "whats water" were an honest "not sure". A school fact people
    # ask by name belongs in the knowledge base.
    entry("what-water-is", (("water",), ("what is water", "whats water", "made of", "made from",
                                        "made out of", "h2o", "chemical formula",
                                        "what are water")),
          _WHAT_WATER_IS,
          # the water of everyday life is somebody else's answer: boiling, a bill, a plant, a
          # bottle to carry, a leak, a body that needs more of it
          avoid=("boil", "boiling", "kettle", "bill", "meter", "bottle", "drink", "drinking",
                 "plant", "plants", "water the", "leak", "leaking", "shower", "bath", "tap",
                 "filter", "softener", "hard water", "salt water", "sea", "swim", "swimming",
                 "pool", "weight", "litre", "litres", "glasses", "dehydrated", "hydration"),
          # "what is water made of" also matches the cooking row `fix-watery`, whose food half
          # has the word "made" in it ("what can i make with...") and whose "watery" is the same
          # form as "water": the line was told to simmer the lid off a pan. This is not a
          # cooking question, so the bias is what wins the tie back.
          ask=("what", "why", "made", "h2o", "formula"),
          # and "water" has to be the whole subject: see WATER_IS_THE_SUBJECT
          guard=_water_is_the_subject,
          bias=2),
    entry("water-boiling", (("boiling point", "boils", "boil"), ("water", "temperature",
                                                                "degrees", "celsius",
                                                                "fahrenheit", "what", "at")),
          "Water boils at 100C (212F) at sea level, and the boiling point drops as you go up: "
          "about 95C in Denver or Mexico City, and 71C on the summit of Everest, which is why "
          "tea brews badly up there.",
          # cooking is its own question: "how long do i boil an egg" is not a physics fact
          avoid=("egg", "eggs", "pasta", "rice", "potato", "potatoes", "kettle", "vegetables",
                 "cook", "cooking", "saucepan", "pan", "how long", "soft", "hard",
                 # water on a person is a scald, not a fact about pressure: "i put my hand in
                 # boiling water" is the first aid's line, and the boiling point of it is no
                 # help to somebody who has just done it.
                 "my hand", "my hands", "my arm", "my arms", "my foot", "my feet", "my leg",
                 "my legs", "my skin", "my face", "my finger", "my fingers", "on my",
                 "hand in", "arm in", "foot in", "scald", "scalded", "scalding", "splashed",
                 "spilt", "spilled", "poured",
                 # A boil is also a sore, and "what do i do about a boil" asked about the sore:
                 # the "what" in this group was enough to answer it with the boiling point of
                 # water, which is an answer to a question nobody asked. A sore word stands this
                 # row down and the boil row takes it.
                 "about a boil", "a boil on", "my boil", "squeeze", "squeezing", "pop a",
                 "popping", "pus", "abscess", "carbuncle", "flannel", "dressing", "sore",
                 # and a notice that says to boil the tap is the water company's row, not the
                 # pressure one: "is there a water boil notice" was answered "Water boils at
                 # 100C (212F) at sea level", which is true and no help at all.
                 "notice", "alert", "tap", "do not drink", "safe to drink")),
    entry("water-freezing", (("freezing point", "freezes", "freeze", "ice"),
                             ("water", "temperature", "degrees", "celsius", "fahrenheit", "what",
                              "slippery", "slippy")),
          _freezing_point,
          # a cold bedroom is a heating answer, not a freezing point: "my bedroom is freezing at
          # night" holds "freezing" and "what", and took this entry instead of heat-a-room
          # "freezers", not "freezer": any typed word one edit from an avoid word counts as a hit,
          # and "freeze" is one edit from "freezer", so the row denied itself the questions it is
          # for ("what temperature does water freeze" and "at what temperature does water freeze"
          # were both hedges on main). The plural is still a form of "freezer" as typed.
          avoid=("pipes", "pipe", "boiler", "fridge", "freezers", "food", "meat", "chicken",
                 "milk", "bread", "defrost", "thaw", "bedroom", "house", "flat", "home",
                 "heating", "radiator", "indoors", "inside the house", "at night",
                 # a grittier answer is about the road, not about why water freezes at 0C
                 "black ice"),
          # The row is about water, so the line has to name it. The bare "what" in the key was
          # what a carried word could complete: after "its freezing", "what do i do" and "what
          # should i eat" both got this card.
          #
          # "ice" is not in the ask even though it is in the key: naming ice is not asking about
          # the freezing point of water. "what is dry ice", "what is an ice hockey puck made of"
          # and "what is a ice pick" each hold "ice" and "what", and a confident 0C is a wrong
          # answer about a different substance. A slippery or slippery-shape line carries its own
          # ask word, so "why is ice slippery" still reaches the card.
          ask=("water", "temperature", "degrees", "celsius", "fahrenheit", "freezing point",
               "slippery", "slippy", "zero")),
    # How long ice takes is not the same question as what temperature water freezes at: the
    # first wants hours, the second wants 0C. The row below names the ice tray, so the line has
    # to carry a word for the thing freezing or a word for ice, and a time word, and it stands
    # down on anything already frozen, on food (the freezer-keeping rows own that), and on the
    # frost-and-ice jobs around the house.
    entry("ice-freezing-time", (("ice", "ice cube", "ice cubes", "freeze", "freezes",
                                 "freezing", "frozen"),
                                ("how long", "long", "take", "takes", "taking", "time",
                                 "hours", "hour", "quick", "quickly", "fast", "soon")),
          "About 3 to 4 hours for a tray of ice cubes in a freezer set to -18C, two hours for a "
          "thin layer of water in a shallow tray, and overnight for a deep tub. Smaller, flatter "
          "and colder all freeze faster, so an empty freezer beats a full one.",
          # a time word and a freeze word are enough to reach this row, so everything that asks
          # something else with those same words stands it down: the temperature fact, food that
          # is already frozen or being kept, the frost jobs, and melting.
          ask=("how long", "long", "take", "takes", "time", "hours", "hour", "quick",
               "quickly", "fast", "soon"),
          # "how long does ice take to freeze in the freezer" reaches the fridge thermometer row
          # on the bare word "freezing", and the ice tray is the answer there, so this row has
          # to be the one that wins a tie: one point, not two, or the fridge fault loses its own
          # report ("my freezer is freezing up").
          bias=1,
          # "freezer" is deliberately not in the avoid list: "freezer" is one edit from "freeze",
          # so the row denied itself the lines it is for (the same trap the freezing-point row
          # above records). A line about a freezer says "defrost" or "icing up", not "freeze".
          avoid=("temperature", "degrees", "celsius", "fahrenheit", "slippery", "slippy",
                 "melts", "melt", "melting", "thaw", "defrost", "defrosting", "refreeze",
                 "re-freeze", "food", "meat", "chicken", "beef", "pork", "fish", "milk",
                 "bread", "cake", "cakes", "dough", "pastry", "rice", "soup", "stew",
                 "fridge", "pipes", "pipe", "boiler", "windscreen",
                 # a person who is freezing wants the body's answer, not the ice tray's:
                 # "my feet are freezing all the time" and "my hands are freezing" were the
                 # three-to-four-hours-for-a-tray answer, because "freezing" is in the key and
                 # "time" is all the ask side needs. The body's own row says it better.
                 "my feet", "my foot", "my toes", "my hands", "my hand", "my fingers", "my finger",
                 "feet", "foot", "toes", "toe", "hands", "hand", "fingers", "finger",
                 "always cold", "freezing all", "i am freezing", "im freezing", "i feel freezing",
                 "car", "road", "roads", "grit", "salt", "black ice", "pond", "lake",
                 "leaves", "lawn", "hose", "tap", "milk bottle",
                 "ice cream", "ice pack", "ice packs", "ice bath", "ice rink",
                 # A keeping question is asked with a keeping verb, and the food in it is not a
                 # noun anyone can list: "how long can i keep frozen peas", "...frozen spinach",
                 # "how long can you keep frozen prawns", "how long can frozen mince stay in the
                 # freezer" and "how long can i freeze berries" all reached the ice tray, because
                 # a freeze word plus "how long" is all this row needs. Stand down on the verb
                 # and every one of them goes back to the keeping answer it had.
                 "keep", "keeps", "keeping", "kept", "last", "lasts", "lasting", "stay", "stays",
                 "store", "stores", "storing", "stored", "can i freeze", "can you freeze",
                 "can i keep", "how long can i", "how long can you",
                 # A frozen food is a cooking time, and "how long do frozen chips take" was
                 # answered with the ice tray: a freeze word and a time word is all this row
                 # needs, so the cooking words stand it down. "frozen" stays in the key, because
                 # "how long does it take to freeze" is this row's own question.
                 "cook", "cooking", "cooked", "oven", "bake", "baking", "roast", "grill",
                 "grilled", "air fryer", "air fry", "airfryer", "air fried", "microwave",
                 "microwaved", "boil", "boiled", "fry", "fries", "fried", "frying", "reheat",
                 "reheated", "ready meal", "nuggets", "fish fingers", "sausages", "pie", "pizza",
                 "yorkshire", "toast", "chips", "wedges", "peas", "spinach", "berries",
                 "prawns", "veg", "vegetables", "defrost in the microwave",
                 # a stock cube is not an ice cube: "how do i store stock cubes" was the ice
                 # tray, because "cubes" plus a keeping verb is all the row above needs
                 "stock", "stocks", "broth", "bouillon")),
    # The keeping question about ice is the one nobody answers: "how long can i store ice cubes"
    # was a search punt, and "how long does ice keep in the freezer" got the card for meat, soup
    # and stock. Ice is the one thing in a freezer whose own answer is about the freezer smell.
    entry("ice-keeping", (("ice", "ice cube", "ice cubes", "cubes"),
                          ("keep", "keeps", "keeping", "kept", "store", "stores", "storing",
                           "stored", "last", "lasts", "how long", "months")),
          "Ice cubes keep for months in a sealed bag or box, but they pick up freezer smells "
          "within a few weeks, and they shrink and go cloudy as the ice slowly turns to vapour. "
          "Seal the tray's cubes in a bag, use them within about three months, and bin any that "
          "smell of the freezer - ice takes on the smell of whatever is next to it.",
          # the freeze-time row is the question "how long does ice take to freeze", and a
          # question about food in the freezer is the keeping card's, not this one's
          avoid=("take", "takes", "quick", "quickly", "fast", "soon", "temperature", "degrees",
                 "meat", "chicken", "fish", "peas", "spinach", "berries", "mince", "prawns",
                 "chips", "bread", "cake", "rice", "soup", "milk", "veg", "food", "cream",
                 "lollies", "defrost", "melting", "melt", "slippery", "lolly", "sorbet",
                 "ice pack", "ice packs", "ice bath", "ice rink", "bag of ice for a bruise",
                 # a stock cube is not an ice cube: "how do i store stock cubes" was the ice
                 # tray, because "cubes" plus a keeping verb is all this row needs
                 "stock", "stocks", "broth", "bouillon"),
          bias=1),
    entry("planets-count", (("planet", "planets"), ("how many", "solar system", "there",
                                                    "eight")),
          "There are eight planets: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus and "
          "Neptune. Pluto was reclassified as a dwarf planet in 2006, which is why the number "
          "went down from nine.",
          ask=("how many", "number", "count", "solar system"),
          # "how many planets in the solar system" ties with the solar-system project answer on
          # score alone, and that one talks about a volcano; a count question is this entry's.
          bias=2),
    entry("hottest-planet", (("planet", "planets", "venus", "mercury"), ("hottest", "hot",
                                                                       "hotter", "warmest")),
          "Venus is the hottest planet, around 465C, and it is hotter than Mercury even though "
          "Mercury is closer to the Sun: Venus is wrapped in a thick carbon dioxide atmosphere "
          "that traps the heat.",
          ask=("hottest", "hotter", "warmest", "which", "why")),
    entry("biggest-planet", (("planet", "planets", "jupiter"),
                              ("biggest", "largest", "bigger", "big", "size")),
          "Jupiter is the biggest planet: about 143,000 km across, or 11 Earths side by side, and "
          "more than twice as massive as all the other planets put together. It is a gas giant "
          "with no solid surface to stand on.",
          ask=("biggest", "largest", "bigger", "which", "what"),
          # a model or a project is a craft answer, and a hot planet is the Venus question
          avoid=("model", "project", "cake", "hot", "hottest", "hottest planet", "temperature"),
          # "the largest planet in the solar system" also reaches the eight-planet count on
          # "solar system", which carries a bias of its own; the size question is this entry's,
          # and the count question names no size word.
          bias=3),
    entry("who-discovered", (("who",), ("discovered", "found out", "worked out")),
          who_discovered,
          # a discovery has to be in the table; "who discovered i was pregnant" is a story
          avoid=("pregnant", "i was", "she was", "he was", "that", "this")),

# "the periodic table" is two words that belong to another world each: "period" is a health
    # word and "tablet" is a device one, so a line about the table itself fell through to the
    # pharmacist. The table is a school fact, so it answers here before either can claim it.
    entry("periodic-table", (("periodic table", "periodic", "first 20 elements",
                              "first twenty elements"),
                             ("what", "remember", "memorise", "memorize", "learn", "elements",
                              "first 20", "how", "who", "invented", "made", "mendeleev",
                              "groups", "columns", "rows", "school", "gcse")),
          "There are 118 elements in order of atomic number, and Mendeleev put the first table "
          "together in 1869 leaving gaps for elements nobody had found yet. For school you need "
          "the first 20 by heart: hydrogen, helium, lithium, beryllium, boron, carbon, nitrogen, "
          "oxygen, fluorine, neon, sodium, magnesium, aluminium, silicon, phosphorus, sulfur, "
          "chlorine, argon, potassium, calcium. Learn the columns rather than the rows: a column "
          "is a family that behaves alike, which is why sodium and potassium both fizz in water."),
    # --- everyday health: the questions a pharmacist gets asked on a Saturday ---------------
    # Two painkillers together is asked as "at the same time", "both" or "can i alternate", and
    # the answer is yes, because they work in different ways - so the ask words are the shapes of
    # that question rather than a general "is this safe".
    entry("painkillers-together-safe",
          (("paracetamol", "acetaminophen", "ibuprofen", "painkiller", "painkillers", "nurofen",
            "co-codamol"),
           ("together", "at the same time", "same time", "both", "alternate", "alternating",
            "with each other", "and ibuprofen", "plus ibuprofen", "and paracetamol",
            # "with" on its own is a common word the reader drops, so "can i take ibuprofen with
            # paracetamol" only reaches this entry through the whole phrase, and the pair named
            # the other way round is the same question
            "with paracetamol", "with ibuprofen", "with nurofen", "with co-codamol",
            "ibuprofen with paracetamol", "paracetamol with ibuprofen",
            "ibuprofen and paracetamol", "paracetamol and ibuprofen")),
          "Yes - paracetamol and ibuprofen work in different ways, so you can take both, and "
          "alternating them is what people often do for a bad headache, toothache or a bad back. "
          "Keep to the box: two 500mg paracetamol up to four times a day, at least four hours "
          "apart and no more than eight in 24 hours, and 400mg of ibuprofen three times a day "
          "with food. Skip ibuprofen if you have a stomach ulcer, kidney trouble or are on a "
          "blood thinner, and read the labels of anything else you take - a lot of cold remedies "
          "already contain paracetamol.",
          # a child's dose is by weight and a baby's is the family domain's own question.
          # "with ibuprofen" is a phrase the reader matches, so a line about drink or about a
          # drug's own timing landed here: "can i drink with ibuprofen" was answered "Yes -
          # paracetamol and ibuprofen work in different ways, so you can take both", which is
          # an answer to a question nobody asked. Drink, the blood, sleep and how fast a
          # tablet works all have their own cards in body.py.
          ask=("can i", "should i", "is it", "does it", "do i", "ok", "safe", "okay", "better"),
          avoid=("baby", "babies", "newborn", "infant", "calpol",
                 "alcohol", "drink", "drinking", "beer", "wine", "pint", "pints", "hangover",
                 "booze", "blood thinner", "thin your blood", "thins the blood", "warfarin",
                 "sleepy", "drowsy", "drowsiness", "how long", "take to work", "kick in",
                 "stomach", "ulcer",
                 # health.py has the other copy of this row, and the two have to disown the same
                 # lines or the copy that did not learn the word answers them: an antibiotic is
                 # not the paracetamol-and-ibuprofen pair, and a tablet taken with a meal is the
                 # with-food question, not this one.
                 "antibiotic", "antibiotics", "pregnant", "pregnancy", "breastfeeding",
                 "empty stomach", "before or after food", "with food", "without food",
                 "with a meal", "before food", "after food", "eat with", "eat before",
                 "need to eat", "have to eat")),
    entry("eye-test-frequency",
          (("eye test", "eye tests", "eyes tested", "eyesight test", "sight test", "optician",
            "optometrist", "glasses"),
           ("how often", "how frequently", "when should", "frequency", "overdue", "need",
            "free", "regular", "every")),
          "Every two years is the usual answer for an adult, and every year once you are over 70 "
          "or if you are diabetic or have glaucoma in the family. In Scotland, Wales and Northern "
          "Ireland the sight test is free on the NHS; in England it is free if you are under 16, "
          "over 60, diabetic, on certain benefits or have a close relative with glaucoma, and "
          "otherwise it is usually around £25 - worth it, because the test spots glaucoma and "
          "diabetes changes years before you would notice them.",
          # "when did i last have an eye test" is a memory question, and a headache is its own
          # line before it is an eyesight one
          avoid=("last", "remember", "headache", "headaches", "migraine", "migraines", "dog",
                 "cat",
                 # a child's eyes are a different answer - the two-year adult interval, and the
                 # glaucoma and diabetes reasons for a yearly one, do not apply to a seven year
                 # old: child-eye-test in family.py answers those
                 "child", "children", "kids", "kid", "son", "daughter", "toddler", "baby",
                 "school", "squint", "squinting")),
    entry("swallow-a-tablet",
          (("tablet", "tablets", "pill", "pills", "capsule", "capsules", "medicine"),
           ("too big", "swallow", "swallowing", "cant swallow", "can't swallow",
            "cannot swallow", "hard to swallow", "stuck", "trouble swallowing")),
          "Take a mouthful of water first, put the tablet on your tongue, then drink from a "
          "bottle or through a straw - and tip your head the right way: a tablet is denser than "
          "water so it sinks, so tilt your head back, while a capsule floats, so tip your chin "
          "down. Swallowing with a mouthful of yoghurt or a soft banana hides the shape. If it "
          "is still hard, ask the pharmacist for a liquid, a dispersible or a smaller tablet, but "
          "never crush or split one that says not to - some are slow release.",
          avoid=("dog", "cat", "puppy", "kitten", "pet", "horse")),
    # One card answers both sides of this: "is a cold the same as the flu" is a no, and "can i
    # get flu more than once" is a yes, so the row reads the line and says which sentence it owes
    # (`bot/compose/lead.py`). A line asking what the difference is wants the two paragraphs and
    # not a verdict, and gets no sentence.
    entry("cold-vs-flu",
          (("cold", "colds", "flu", "influenza"),
           ("same", "difference", "different", "same thing", "worse", "which is", "or is it",
            "twice", "again", "still get")),
          "A cold stays in the nose and throat: a runny nose, sneezing, a sore throat, and you "
          "can still get up and work. Flu comes on in hours with a fever, aching limbs and being "
          "flattened in bed, and the cough and the tiredness can drag on for two or three weeks. "
          "You can get flu more than once, because each season has different strains - that is "
          "why the jab changes every year - and a cold is a different family of viruses again.",
          bias=1,
          lead=("yesno", _cold_or_flu_verdict)),
    entry("cold-duration-cough",
          (("cold", "colds", "a cold", "sniffles", "runny nose"),
           ("how long", "last", "lasts", "go away", "gone", "over it", "weeks", "still",
            # "when will my cold go" is the same question with the verb on its own; "shift" and
            # "shake" are how to get rid of one, and that ask has the remedy answer
            "go", "going")),
          "A cold usually peaks in two or three days and is gone in about a week, though a cough "
          "and a blocked nose can linger for two weeks and that is normal. Rest, plenty of fluid "
          "and paracetamol for the ache are the treatment; antibiotics do nothing for a virus. "
          "See a GP if it lasts more than three weeks, if you are breathless or wheezing, or if "
          "a child is drinking less and has a fever that will not come down.",
          bias=1,
          avoid=("sore", "sores", "hands", "feet", "fingers", "toes", "war", "country",
                 # A child who has gone grey, mottled or clammy has a circulation question, not
                 # a virus: "my son is mottled and cold" was told a cold is a virus, and the
                 # safety colour card is the answer to that line. Only the colours a cold never
                 # makes are here - "pale" on its own is how people describe a sniffle.
                 "mottled", "clammy", "grey", "gray", "ashen", "white as a sheet",
                 "blue round the lips", "blue lips",
                 "countries", "weather", "room", "water", "outside", "garden", "morning",
                 # "is it too cold to go for a bike ride" is the day's question: "cold" is the
                 # temperature and "go" is the verb in the ask, so the illness duration answered
                 # a line about a bicycle. Anything said of being out in it stays out of here.
                 "too cold to", "too cold for", "cold enough", "cold outside", "out in the cold",
                 "bike", "bikes", "bicycle", "cycle", "cycling", "ride", "walk", "walking",
                 "hike", "picnic", "barbecue", "bbq", "parasol", "washing", "laundry",
                 "line", "dog", "dogs", "baby out", "pram", "buggy",
                 # "how long does a cold beer last in the fridge" is a "cold" drink and a
                 # keeping question, not an illness: the food-keeping answers own it.
                 "beer", "lager", "wine", "milk", "juice", "brew", "coffee", "tea", "fridge", "freezer",
                 "freeze",
                 "leftovers", "leftover", "food", "meat", "chicken", "rice", "pasta", "cake",
                 "bread", "eggs", "egg", "cheese", "yoghurt", "yogurt", "opened", "unopened",
                 # a child's cold at school is the school answer's question
                 "school", "nursery", "off school", "dog", "cat", "puppy", "kitten",
                 # a heating thing that "keeps going cold" is the heating's own question: on
                 # main "the radiator keeps going cold" and "the heating keeps going cold" were
                 # both told "A cold usually peaks in two or three days", and the subject named
                 # in the line is the thing that went cold, not the person
                 "radiator", "radiators", "rads", "heating", "central heating",
                 "boiler", "hot water", "hot tap", "hot taps", "thermostat", "immersion",
                 "towel rail", "pipe", "pipes",
                 # "what should i pack for a cold week in prague" names a cold place to go,
                 # not a cold to have: anything you pack and carry is the packing list
                 "pack", "packing", "packed", "suitcase", "luggage", "hand luggage",
                 "handbag", "backpack", "rucksack", "carry on", "wear", "wearing",
                 "clothes", "layers",
                 # whether to run, train or swim with a cold is the exercise answer, not how long
                 # a cold lasts: "i have a cold can i still run" was getting the duration one.
                 # main's list already covers those lines; this PR adds only the shapes it names
                 # that main did not: "still play", "still swim", "still cycle", "running with",
                 # "training with", "go running", "go for a run", "work out", "netball", "hockey",
                 # "cycle", "cycling".
                 "can i still", "can i run", "can i train", "can i exercise", "can i swim",
                 "can i go to the gym", "should i run", "should i train", "should i exercise",
                 "run with", "running with", "train with", "training with", "exercise with",
                 "still run", "still train", "still play", "still swim", "still cycle",
                 "go running", "go for a run", "work out", "workout", "gym",
                 "running", "swim", "swimming", "cycle", "cycling", "football", "netball",
                 "hockey", "training",
                 # a thing that runs cold is not a person with a cold: "my radiator keeps going
                 # cold" was told a cold peaks in two or three days, and the heating cards own
                 # that line. The nouns below only turn up in a line about a thing's temperature.
                 "radiator", "radiators", "boiler", "heating", "thermostat", "shower", "tap",
                 "hot water", "washing machine", "dishwasher", "kettle", "oven", "fridge",
                 "freezer", "car", "engine", "bath water", "hot tub", "shed", "greenhouse",
                 "appliance", "furnace", "heat pump",
                 )),
    entry("five-a-day-grams",
          (("5 a day", "five a day", "five portions", "fruit and veg", "fruit and vegetables",
            "smoothie", "smoothies", "juice"),
           ("count", "counts", "really", "thing", "true", "enough", "portion", "portions",
            "what counts", "does it")),
          "Five a day is real, and it is about 400g of fruit and vegetables rather than five "
          "items: a portion is 80g, which is one apple, three heaped tablespoons of peas, or a "
          "handful of grapes. A smoothie counts once however much of it you drink, and so does a "
          "150ml glass of juice, because the fibre is broken up and it goes down too fast - "
          "whole fruit is better. Potatoes, chips and crisps do not count: they are the "
          "carbohydrate on the plate.",
          bias=1),
    entry("night-snacking",
          (("snack", "snacks", "snacking", "crisps", "biscuits", "chocolate"),
           ("night", "nights", "evening", "evenings", "late", "bed", "bedtime", "stop",
            "habit", "why", "midnight")),
          "Evening snacking is usually a habit loop rather than hunger: it starts with being "
          "tired, bored or in front of a screen, and it is the cue you have to change. Brush "
          "your teeth straight after dinner, keep food out of the living room, and make dinner "
          "big enough and with enough protein and fibre that you are not catching up at ten. If "
          "you know you will want something, plan it - a yoghurt or a bowl of cereal at nine, "
          "eaten sitting down, beats an unplanned raid at eleven.",
          # a snack for a child, a packed lunch or a dog's treats are other questions
          avoid=("toddler", "baby", "child", "children", "kids", "dog", "cat", "puppy",
                 "lunch", "school", "party")),
    entry("cold-and-school",
          (("cold", "cough", "sniffles", "runny nose"),
           ("school", "nursery", "off school", "go to school", "keep her off", "keep him off",
            "keep my kid off", "keep them off", "send her", "send him")),
          "A cold with no fever, and a child who is eating and drinking, is fine for school - a "
          "runny nose on its own is not a reason to stay off. Keep her home if she has a "
          "temperature, is too tired or clingy to join in, is being sick, or has a cough that "
          "leaves her breathless or wheezing. Send tissues and tell the teacher, and let her go "
          "back once the fever has been gone for 24 hours without medicine; the cough can hang "
          "on for a week or two after that and does not need another day off."),
    # "How long does flu last" and "why am I so tired after flu" are the two ways people ask this,
    # and the antibiotics entry does not cover either: it is a recovery question, not a treatment.
    entry("flu-recovery",
          (("flu", "influenza", "virus", "cold"),
           ("last", "how long", "tired", "exhausted", "fatigue", "weeks", "recover", "recovery",
            "better", "still", "ache", "aches", "weak", "knackered")),
          # The ask words are not in this key: "virus" and "cold" are in the first one, and
          # "how do i get rid of a virus on my laptop" is not a flu question.
          "Flu usually hits hardest for two or three days and is mostly gone in a week, but a "
          "cough and a flat, tired feeling can drag on for two or three weeks, and that is normal. "
          "Sleep as much as your body asks for, drink more than you think you need, and go back to "
          "work or training gently. See a doctor if you are breathless, have chest pain, a fever "
          "past five days, or are still exhausted after a month.",
          # the neighbour is the treatment question: "do antibiotics work for flu" belongs to
          # antibiotics-cold, and a baby or a child with flu belongs to the family domain
          avoid=("antibiotic", "antibiotics", "penicillin", "covid", "test", "vaccine", "vaccines",
                 # "how long does a cold beer last in the fridge" is a drink, not an illness
                 "beer", "lager", "ale", "stout", "cider", "wine", "fridge", "bottle", "bottles",
                 "opened", "unopened",
                 "jab", "jabs", "baby", "babies", "toddler", "child", "children", "pregnant",
                 "temperature", "rash", "vomiting", "diarrhoea",
                 # "i have a cold, can i still run" is whether to train, not how long flu lasts
                 "can i still", "can i run", "can i train", "can i exercise", "can i swim",
                 "can i go to the gym", "should i run", "should i train", "should i exercise",
                 "run with", "train with", "exercise with", "gym", "running", "swim",
                 "swimming", "football", "training")),
    entry("eggs-daily", (("egg", "eggs"), ("every day", "daily", "too many", "ok", "okay", "fine",
                                           "safe", "healthy", "bad", "cholesterol", "harm")),
          "An egg a day is fine for most people: the cholesterol in food moves blood cholesterol "
          "far less than saturated fat does, which is the butter you cook it in. An egg gives "
          "cheap protein, vitamin D and B12. Two a day is still reasonable for a healthy adult; "
          "if you have heart disease or diabetes, ask your GP what suits you.",
          # A date question is the float test in cooking.egg-fresh, not how many are safe in a
          # week: "is it ok to eat eggs past the date" says "eggs" and "ok", which was enough to
          # take this entry's answer and lose the test the person asked for.
          avoid=("dog", "cat", "puppy", "kitten", "bird", "chicken", "hatch", "boil", "boiled",
                 "poach", "scramble", "fry", "frying", "recipe", "bake", "baking", "cake",
                 "cook", "cooked", "yolk", "white", "shell", "go off", "gone off", "fresh",
                 "date", "dates", "use by", "best before", "out of date", "expired", "expiry",
                 # a shell that is already cracked is the cracked-egg answer: "an egg cracked in
                 # the fridge is it ok" was taken by this entry off the word "ok" alone
                 "crack", "cracked", "cracks")),
    entry("nail-biting-habit", (("nail biting", "bite my nails", "biting my nails", "biting nails",
                           "chew my nails", "chewing my nails", "bitten nails", "nail biter"),
                          ("stop", "stopping", "how", "habit", "quit", "break", "help")),
          "Nail biting is a habit that turns up when you are bored, tense or concentrating, so "
          "give the hand something else to do: keep nails short and filed, hold a pen or a ring "
          "of putty, and try a bitter polish for a month. Many people beat it, and most of the "
          "way is noticing the moment rather than forcing it.",
          # "chewing" is this card's own word, and `routines.nail-biting` answers the biting
          # phrasings; without the step up, the routines row's ask words ("stop", "how") beat
          # the exact phrase here and this card was only reached by the literal "nail biting
          # habit", so one of the two ids was dead on every other line
          bias=2),
    # The cold feet are the same answer as the cold hands - the body pulling blood in from the
    # skin - and "my feet are always cold" and "my toes are cold" were getting "Thanks for
    # telling me", so the parts carry feet and toes and the answer says so.
    entry("cold-hands", (("hands", "hand", "fingers", "fingertips", "raynauds", "raynaud",
                          "raynaud's", "feet", "foot", "toes", "toe"),
                         ("cold", "freezing", "freeze", "always", "white", "blue", "purple",
                          "circulation", "winter", "help", "helps", "worse", "feet", "toes",
                          # "how do i keep my hands warm" is the same question the other way
                          # round, and "warm" is the word people use for it: without it the row
                          # needed the word "cold" in a line that never says it.
                          "warm", "warmer", "warmth", "warmish", "toasty")),
          "Cold hands and feet are usually just circulation: the body pulls blood in from the "
          "skin when you are cold. Warm the whole body, not just the hands - gloves, thick socks, a "
          "hat, a warm drink - and flex the fingers and toes. White, then blue, then red and "
          "painful in the cold is Raynaud's, and "
          "keeping the wrists warm helps. See a GP if it is one hand only, or comes with "
          "tiredness or weight change.",
          # A hot hand, a hand that hurts or swells, and a symptom said of a child are other
          # questions: this one is the hands that are simply always cold.
          avoid=("burn", "burnt", "scald", "swollen", "swelling", "rash", "itch", "numb since",
                 "fell", "cut", "wound", "broken", "baby", "babies", "child", "children", "kid",
                 "kids", "pins and needles",
                 # a warm room, a warm house and a warm bed are the heating answer: this one is
                 # the body part, which is why "warm" needs the hand or the foot in the line
                 # not "water": cold water is a Raynaud's trigger and a normal way to say the
                 # line - "my hands are cold after washing up in cold water" was being stood down
                 "bedroom", "bedrooms", "living room", "room", "rooms", "house", "home", "flat",
                 "oven", "cook", "cooking",
                 # the illness is the line, not the hands in it: "i keep getting colds, i wash my
                 # hands a lot" is the colds question and the circulation answer is not about it
                 # a bare "colds" here would take the singular too, and "my hands are always
                 # cold" with it, so the illness is fenced by the phrases it is said in
                 "catching colds", "catch colds", "keep getting colds",
                 "got a cold", "have a cold", "had a cold", "cold after cold", "a cold and",
                 "wash my hands", "washing my hands", "handwashing", "hand washing",
                 "sore throat", "flu", "virus", "viruses",
                 # the nerves, not the feet: "i have cold feet about the wedding" is the
                 # wedding, and the nerves answer below has it (see `cold-feet-nerves`)
                 "cold feet about", "cold feet over", "cold feet before"),
          # "numb" is in the check but not in the key: numb, tingling hands with no cold in the
          # line is a nerve question, not a circulation one.
          ask=("cold", "freezing", "numb", "white", "blue", "circulation", "raynauds",
               "raynaud", "warm", "warmer", "warmth", "toasty")),

    # The nerves before a big day, said as the feet: "i have cold feet about the wedding" is the
    # wedding. Read off the words, "cold" and "feet" are the cold-hands answer - the body
    # pulling blood in from the skin, gloves and thick socks - and the person had said nothing
    # about being cold. The figures of speech are the ones with the thing they are about in them,
    # or the ones said with getting or got, and that is what keeps a cold foot of your own on the
    # other answer: it is said with a time or a place in the line ("i get cold feet at night",
    # "cold feet in winter", "cold feet in bed") or with the feet said of the person ("my feet
    # are cold").
    entry("cold-feet-nerves", (("cold feet", "cold foot"),
                               ("about", "over", "before", "getting", "got", "gotten",
                                "wedding", "married", "marrying", "interview", "move",
                                "moving", "exam", "flight", "driving test", "second thoughts")),
          "Nerves before something big are normal. Slow breaths for a minute genuinely help, "
          "and so does saying the worry out loud to one person: what is it that the day itself "
          "might bring? Cold feet before a wedding, a move or an interview are usually the size "
          "of the change rather than a warning about it, so give it a night before you act on it "
          "- and if it is a promise you are not sure you want, that is worth talking through "
          "properly, with the person if you can.",
          # the body part is the other answer, and it is said with a time or a place in the
          # line, or with the feet said of the person. The figure of speech has the thing it is
          # about instead, which is in the key.
          avoid=("feet are", "feet get", "feet go", "feet feel", "feet were", "hands and feet",
                 "bed", "night", "nights", "winter", "morning", "evening", "weather",
                 "cold day", "when", "whenever", "always", "all day", "all the time", "toes",
                 "toe", "raynauds", "raynaud", "socks", "slippers", "gloves", "duvet",
                 "blanket"),
          bias=2),

    # --- the mind and the body clock -------------------------------------
    entry("teen-sleep", (("teenager", "teenagers", "teen", "teens", "puberty", "adolescent",
                          "adolescents"),
                         ("sleep", "sleepy", "tired", "late", "wake", "waking", "morning",
                          "night", "owl", "bedtime")),
          "In the teen years the body clock shifts later by up to two hours, so a teenager really "
          "is not sleepy at 10pm and cannot wake at 7am. It is biology, not laziness: keep a "
          "steady wake time, get morning daylight and dim screens late, and aim for 8 to 10 hours. "
          "Tiredness that persists with low mood, or falling asleep in class, is worth a GP visit.",
          ask=("why", "what", "how", "cause", "always", "help", "should"),
          avoid=("baby", "babies", "toddler", "child", "children", "dog", "cat")),
    entry("caffeine-awake", (("caffeine", "coffee", "espresso", "energy drink", "energy drinks",
                              "tea", "cola", "coke"),
                             ("awake", "wake", "wakes", "waking", "wired", "insomnia", "sleep",
                              "sleeping", "keep me awake", "keeps me awake", "stops me sleeping",
                              "stop me sleeping", "can't sleep", "cant sleep", "late", "night")),
          "Caffeine blocks adenosine, the molecule that builds up through the day and makes you "
          "sleepy, so it hides tiredness rather than removing it. Its effect lasts about five "
          "hours: have your last coffee by early afternoon, and cut down slowly to avoid headaches.",
          ask=("why", "what", "how", "cause", "keep", "stop", "can't", "cant",
                "does", "can"),
          avoid=("much", "limit", "safe", "many", "pregnant", "pregnancy", "plant", "plants",
                 "grounds", "compost", "stain", "stains", "table", "mug", "pod", "pods"),
          # a coffee that keeps you awake is this entry, not the coffee-jitters one
          bias=2),
    entry("earworm", (("earworm", "earworms", "song stuck", "songs get stuck", "song gets stuck",
                       "tune stuck", "tunes get stuck", "tune gets stuck", "music stuck",
                       "song in my head", "tune in my head"),
                      ("why", "what", "stuck", "head", "get rid", "stop", "how", "happen")),
          "A catchy piece with a simple shape and a repeated phrase loops because the brain "
          "predicts the next note and keeps replaying the bit it knows. Chewing gum, singing the "
          "song all the way through, or listening to a different familiar song usually breaks it; "
          "it is harmless.",
          ask=("why", "what", "how", "get", "stop", "happen"),
          # a song stuck in the head is this fact, not the general life-rut card
          bias=1,
          avoid=("hearing", "hear", "tinnitus", "ringing", "deaf", "deafness")),
    entry("boredom", (("bored", "boredom", "boring"),
                      ("why", "feel", "get", "always", "what", "mean")),
          "Boredom is the brain asking for something engaging: with no clear goal it looks for "
          "novelty or meaning, and time feels slow because little is being laid down as a memory. "
          "It is not a flaw, and letting yourself be bored for a bit often restarts curiosity and "
          "ideas.",
          ask=("why", "what", "feel", "always"),
          # A thing called boring is a recommendation, not a question about the feeling:
          # "a podcast that isn't boring" is a podcast ask, and that answer owns it. The
          # words here must not stem to "bored", so "boring" itself is left out.
          avoid=("film", "movie", "book", "show", "series", "game", "lesson", "class",
                 "job", "work", "meeting", "party", "podcast", "podcasts", "listen",
                 "recommend", "recommendation"),
          # work's "boring jobs" key reads "boring" broadly; a plain "why do i get bored" is
          # the feeling, so this answer should win the tie rather than the jobs one.
          bias=1),
    entry("fake-tan",
          (("fake tan", "spray tan", "self tan", "self-tan", "false tan", "tanning lotion",
            "tanning mousse", "gradual tan", "bronzer", "tan in a bottle"),
           ("safe", "safety", "protect", "spf", "sun", "last", "long", "how", "what", "does",
            "work", "risk", "breathe", "fade", "wash", "off")),
          "Fake tan is a dye, usually DHA, that colours only the dead cells on the surface and "
          "fades after about five to seven days, so it gives no sun protection; you still need "
          "SPF, and the one real risk is breathing in a spray mist - ask for a lotion or mousse, "
          "hold your breath or wear the mask, and patch test first.",
          ask=("fake", "spray", "self", "false", "gradual", "bronzer", "mousse", "lotion", "bottle",
               "dha")),
    entry("skin-tan", (("tan", "tanning", "tanned", "suntan", "sun tan", "sunbed", "solarium"),
                       ("why", "how", "get", "skin", "sun", "safe", "faster", "work", "use",
                        "stop", "prevent", "block", "protect")),
          "A tan is your skin making extra melanin to shield skin-cell DNA from ultraviolet "
          "light, and that is damage, not health: it raises the risk of skin cancer and ageing, "
          "so use SPF 30, shade and a hat and skip sunbeds; a fake tan is safer because it colours "
          "only the top layer.",
          ask=("why", "how", "what", "get", "safe", "work", "stop", "prevent", "block",
                "protect", "does", "can"),
          avoid=("leather", "shoe", "shoes", "bag", "bags", "boot", "boots", "carpet", "paint",
                 "wood", "furniture")),

    entry("sleep-teenagers",
          # the teen words are the whole of the second group: "my daughter wont go to sleep"
          # is the toddler routine, and only a line that says teenager or an age in the teens
          # is this answer
          # A bare number was in the second group and it read a count as an age: "she sleeps
          # about 18 hours a day" (a greyhound) got this answer because of the 18. A number is
          # only an age when it is written as one - "my 14 year old", "aged 18" - so the teen
          # words, the school years and the age shapes stay, and a bare number does not.
          (("sleep", "sleeping", "slept", "hours", "bedtime", "bed time"),
           ("teenager", "teenagers", "teen", "teens", "teenage", "year 9", "year 10", "year 11",
            "secondary school", "college",
            "13 year", "14 year", "15 year", "16 year", "17 year", "18 year",
            "13-year", "14-year", "15-year", "16-year", "17-year", "18-year",
            "13 years old", "14 years old", "15 years old", "16 years old", "17 years old",
            "18 years old", "aged 13", "aged 14", "aged 15", "aged 16", "aged 17", "aged 18",
            # "im 17 and cant sleep" is a person saying their own age, which is an age however it
            # is written; it stays in the key while a bare number does not
            "im 13", "im 14", "im 15", "im 16", "im 17", "im 18",
            "i am 13", "i am 14", "i am 15", "i am 16", "i am 17", "i am 18")),

          "Teenagers need more sleep than adults, not less: 8 to 10 hours a night from 14 to 17, "
          "and 9 to 12 from 6 to 13. Their body clock also shifts late, so an 11pm natural "
          "bedtime is biology rather than laziness, and a school start of 8am means lights out "
          "by 10:30 with the phone out of the room for the last hour. A weekend lie-in of more "
          "than two hours moves the clock further back and makes Monday worse, so a shorter "
          "catch-up and a dark room work better.",
          # "cant sleep" is not held out: the second group already needs a teen word or a teen
          # age, and a 16 year old who cannot sleep is exactly this question
          avoid=("my baby", "baby", "newborn", "toddler", "puppy", "cat", "dog", "insomnia",
                 "shift work", "jet lag", "apnoea", "snoring",
                 "pregnant", "hibernate",
                 # the nutrient questions ask "how much" and name a teenager, and this row read
                 # the age and answered with the night chart
                 "calcium", "iron", "vitamin", "vitamins", "protein", "fibre", "fiber",
                 "calories", "calorie", "potassium", "magnesium", "zinc", "b12", "folate",
                 "water", "milk", "steps"),
          # "my teenager is always tired" is a line to meet, not a lecture on hours, so the
          # line has to name the teenager and ask about hours or sleep
          ask=("teenager", "teenagers", "teen", "teens", "teenage", "year old", "year-old",
               "my son", "my daughter", "hour", "hours", "how much", "how many", "sleep")),
    entry("cholesterol-lower",
          (("cholesterol", "ldl", "hdl", "triglycerides", "lipid", "lipids"),
           ("lower", "reduce", "high", "how", "bring down", "improve", "diet", "statins",
            "statin", "raised", "bad", "down", "naturally")),
          "Cut saturated fat first, since that is what raises LDL: butter, cheese, fatty and "
          "processed meat, pastries and coconut oil. Swap to olive or rapeseed oil, and add oats, "
          "beans, nuts and oily fish twice a week, all of which lower LDL or triglycerides a "
          "little. Activity most days raises the good HDL. Together that is often 5 to 10%, so if "
          "your LDL is high enough for medication your GP will offer a statin, which does more "
          "than any diet does.",
          avoid=("egg", "eggs", "prawns", "shellfish", "butter or margarine", "my levels are")),
    # The egg question is the one people still ask, and the answer is "less than you think"
    # rather than a repeat of the fat swaps.
    # Blood pressure, immunity and weight are the three health asks where the honest answer is
    # "here is the lever, and here is when to see someone", so each names its lever first.,
    entry("blood-pressure-lower",
          (("blood pressure", "hypertension"),
           ("lower", "reduce", "high", "bring down", "how", "diet", "exercise", "naturally",
            "salt", "down", "help")),
          "Salt is the biggest lever most people have: aim under about 6g a day, a teaspoon, "
          "which means cooking from scratch and reading the labels on bread, sauces and "
          "takeaways. Then 150 minutes a week of walking, cycling or swimming, losing a few kilos "
          "round the middle, cutting back on alcohol, and eating more fruit, vegetables, beans "
          "and dairy. Together those often take 5 to 10 points off; if your reading is around "
          "140/90 or more on repeated home checks, see your GP, because tablets do more than the "
          "lifestyle changes alone.",
          avoid=("what is", "whats a normal", "what's a normal", "normal", "reading", "machine",
                 "monitor", "cuff", "over 80", "too low", "low")),
    entry("weight-without-dieting",
          (("weight", "lose weight", "losing weight", "slim down", "kilos", "pounds", "fat",
            "stone", "stones"),
           ("lose", "without dieting", "diet", "dieting", "how", "start", "slowly", "keep off",
            "sustainable", "naturally", "losing")),
          "Change a few things you can keep doing rather than going on a diet: fill half the "
          "plate with vegetables, put protein in every meal so you are not hungry an hour later, "
          "swap sugary drinks for water or squash, and walk for half an hour a day. Losing about "
          "0.5 to 1kg a week is the rate that stays off, and the plan that works is the one you "
          "would still follow in a year. If you are hungry all the time, or the weight is going on "
          "without trying, see a GP.",
          # Weight coming off without trying is a symptom, not a plan: someone asking why
          # they or their partner keep losing weight must not be told to eat less.
          guard=_the_pounds_are_weight,
          ask=("how", "what", "want to", "trying to", "should i", "tips", "advice", "best",
               "start", "help", "plan", "lose", "losing", "diet", "dieting", "slim"),
          avoid=("baby weight", "pregnant", "weight of", "weight limit", "baggage",
                 "suitcase", "how much does", "weight training", "lifting weights",
                 "the weights", "my weights", "keeps losing weight", "keep losing weight",
                 "i keep losing", "for no reason", "without trying", "unexplained",
                 "gone off my food", "no appetite",
                 # A kilo is a unit before it is a body: "how long per kilo" is a roasting
                 # time and "a kilo of potatoes" is a shopping list. The weight words in the
                 # key ("kilos", "pounds") match the unit, so the shapes that make it a unit
                 # stand this entry down, or a follow-up about a chicken gets the diet plan.
                 # Only the unit and cooking-time shapes are here: a food or an oven noun is
                 # not enough, because "i want to lose weight but i love baking" and "i want
                 # to lose a few kilos is beef ok" are diet lines with food in them.
                 "per kilo", "per kg", "per pound", "a kilo of", "how many kilos of",
                 # A pound is money before it is weight, and the row's key takes it: "how much
                 # do i need to put by a week to have 100 pounds" - the question a saving plan
                 # asks about the money still to find - was answered with the diet plan, because
                 # a small sum reads as weight and this row has "pounds" in its key. The saving
                 # verbs stand the row down; none of them is a way of saying lose weight.
                 "put by", "putting by", "save up", "saving up", "savings", "save",
                 "saved", "to save", "a week to have", "a month to have",
                 # A stone is a unit before it is a body too: "how heavy is a stone" and
                 # "a stone in kilos" are conversions, and the stone in the key now matches
                 # the word, so the shapes that ask what a stone weighs stand this entry down.
                 "how heavy is a stone", "how heavy is stone", "a stone in kilos",
                 "a stone in kg", "stone in kilos", "stone in kg", "how much is a stone",
                 "how many kilos in a stone", "how many kilos is a stone",
                 "how much does a stone weigh", "what is a stone in", "whats a stone in",
                 # ...and a stone is a thing before it is a weight: a plum's stone, a pizza
                 # stone, a stone in a wall. Only the nouns that a stone belongs to are here,
                 # so a weight line with a day or a holiday in it still gets the plan.
                 "stone from", "stone out", "stones from", "stones out",
                 "plum", "plums", "peach", "peaches", "cherry", "cherries", "damson",
                 "damsons", "greengage", "avocado", "mango", "olive", "olives", "apricot",
                 "apricots", "date stone", "pips", "pitted",
                 "oven", "hob", "tray", "pizza", "grill", "paving", "patio", "worktop",
                 "wall", "walls", "path", "steps", "slab", "slabs", "gravel", "driveway",
                 "floor", "sink", "drain", "garden", "rockery", "shoes", "shoe", "foot",
                 "kidney", "kidneys", "gallbladder", "bladder", "tonsil", "tonsils",
                 "basting", "bast", "carving", "stuffing", "cooking time", "minutes per",
                 "joint of", "how long do i cook", "how long to cook",
                 # the pound and the half kilo are units the same way: "how much is a pound
                 # of butter" and "how long per lb" are a price and an oven, and both were the
                 # diet plan on main
                 "per kilos", "per lb", "per 500g", "per 500 g", "kilo of", "kilos of",
                 "pound of", "pounds of", "how much is a kilo", "how much is a pound",
                 # ...and a sum of money is a sum of money: "how far can i go on 300 pounds" and
                 # "how far will 300 pounds get me" are asking what the money buys, and this row
                 # read the "how" and the "pounds" and answered with a diet plan. "How far" is a
                 # distance or a budget and never a way to lose weight.
                 "how far", "how far can i go", "how far will", "far will",
                 # someone else's weight is not this plan either: a child's is the health
                 # visitor's chart, and a parent asking is not asking for themselves. The bare
                 # words "year old" and "my son" are too wide for that - "im 40 years old and
                 # want to lose weight" is the person themselves, and "my kids want me to lose
                 # weight" is still their own plan - so the child or the age has to be the
                 # subject of the clause.
                 "year old weigh", "year olds weigh", "year old weight", "what should a 5 year",
                 "my son is", "my daughter is", "my child is", "my kid is", "my children are",
                 "my kids are", "my son wants to lose", "my daughter wants to lose",
                 "my child wants to lose", "my kid wants to lose",
                 # a cat or a dog that needs to slim is the vet's question, with its own
                 # answer about portions and treats: the person's plan is not it
                 "cat", "cats", "dog", "dogs", "puppy", "puppies", "kitten", "kittens",
                 "rabbit", "hamster", "guinea pig", "my pet", "vet")),
    # The health asks people actually type, one entry each: the lever first, then the number
    # that decides whether it is a GP question. All of them pass the "how do i get rid of a cold"
    # and "how many calories in" lines, which have their own answers.,
    entry("statin-work",
          (("statin", "statins", "atorvastatin", "simvastatin", "rosuvastatin"),
           ("work", "how", "do i need", "need", "side effects", "side effect", "worth",
            "should i take", "stop", "muscle", "safe",
            # the same ask in the other shapes it is typed: "should i be on statins", "should i
            # start statins", "should i keep taking them" were the "that's your call" line
            "should i be on", "should i go on", "should i start", "should i keep taking",
            "keep taking")),
          "A statin blocks the liver enzyme that makes cholesterol, so less LDL ends up in your "
          "blood: expect roughly a 30 to 50% fall in LDL depending on the dose, with the biggest "
          "benefit for anyone who has already had a heart attack or stroke. Muscle aches are the "
          "side effect people worry about, and in trials they were about as common on the dummy "
          "tablet; if you do get them, try a different statin or a lower dose before giving up, "
          "because the benefit is real. Don't stop one on your own: ask the GP or pharmacist.",
          # when in the day to take one is the timetable row's question ("when should i take
          # atorvastatin" is this card's "should i take" and nothing about the timetable)
          # "is it worth" was fenced here, and "worth" is in this entry's own key: the line it was
          # meant to keep out ("is it worth taking statins") is this card's question, and fencing it
          # sent it to "Can't call that one for you". Only the price and the timetable stay out.
          avoid=("how much do statins cost", "how much is a statin", "when should i take",
                 "when do i take",
                 "when to take", "what time", "time of day", "at night", "in the evening",
                 "in the morning", "same time each day")),
    entry("bmi-healthy",
          (("bmi", "body mass index"),
           ("healthy", "what", "whats", "good", "normal", "range", "calculate", "work out",
            "chart", "mean", "do i")),
          "BMI is weight in kilos divided by height in metres squared, and 18.5 to 24.9 is the "
          "range the NHS calls healthy. It is a crude tool: it cannot tell muscle from fat and it "
          "reads badly for very tall, very short or very muscular people, so waist measurement "
          "and how you feel matter alongside it. Use it as a rough flag, not a diagnosis, and if "
          "you want a real assessment ask the GP or a pharmacist.",
          avoid=("child", "children", "kid", "kids", "my son", "my daughter", "baby", "toddler")),
    entry("quit-smoking",
          (("smoking", "smoke", "smoked", "smoker", "smokers", "i smoke", "cigarettes",
            "cigarette", "cigs", "vape", "vaping", "nicotine",
            # "pack" alone is a suitcase ("pack a day", "packing for a weekend"), and the packing
            # row was answering a smoker's line; the phrase is the cigarette one
            "pack a day", "packs a day", "smoke a pack", "pack and a half"),
           ("quit", "stop", "give up", "cut down", "how", "help", "best way", "cold turkey",
            # "ive smoked for 20 years, how do i stop" is the same question in the words people
            # actually use: the habit named as a history ("smoked for", "a smoker since", "30
            # years", "20 a day") rather than as the phrase "quit smoking". Only the report was
            # a shrug: the plain how-to lines were already answered.
            "a day", "for years", "since i was", "i want to stop",
            "i want to quit", "want to give up", "years")),
          "The most reliable way is nicotine replacement plus a stop date: patches for the "
          "background craving and a fast-acting gum, lozenge or spray for the moments it spikes, "
          "used together. Set a date in the next two weeks, tell people, and change the routines "
          "that went with a cigarette - the first coffee, the car, the pub garden. Your GP can "
          "prescribe and refer you to a free stop-smoking service, and vaping is far less harmful "
          "than smoking if you need something in your hand.",
          # "smoked" is a loose form of "smoking", so the fish and the barbecue need phrases
          # The meat has its own smoky words too: "how do i smoke a brisket" is a cooking
          # question, and the stop plan was answering it with patches and a stop date.
          avoid=("smoked salmon", "smoked haddock", "smoked mackerel", "smoked bacon",
                 "smoked paprika", "smoked cheese", "barbecue", "bbq", "smoke alarm",
                 "brisket", "briskets", "meat", "ribs", "pork", "pastrami", "jerky",
                 "sausages", "smokehouse", "low and slow",
                 "smoke from", "bonfire", "smoke house",
                 # "smoker" alone was standing down a person who smokes: "ive been a smoker for
                 # 30 years" reached nobody. The barbecue machine is named by what makes it one.
                 "pellet smoker", "electric smoker", "charcoal smoker", "smoker grill",
                 "smoker box", "smoker tube", "use a smoker", "my smoker", "buy a smoker",
                 # it is someone else's cigarette: "set a stop date" tells the wrong person to
                 # stop, and a worried relative wants what to say, not a plan for themselves
                 "dad", "mum", "mother", "father", "husband", "wife", "partner", "girlfriend",
                 "boyfriend", "friend", "son", "daughter", "brother", "sister", "worried",
                 "worry", "wont", "won't",
                 # they have already stopped, and this row is a plan to start
                 "last week", "yesterday", "havent smoked", "haven t smoked",
                 "not had a cigarette", "since i quit", "since i stopped", "i ve quit",
                 "i ve stopped", "3 days ago", "a week ago", "a month ago",
                 # a cough after stopping is the answer about the cough, below
                 "cough", "coughs", "coughing",
                 # a barbecue or a smoked brisket is cooking, and the verb is what this row
                 # keys on: the food stands the stop plan down
                 ) + _SMOKE_IS_NOT_A_HABIT),
    # The other half of the smoking questions are about someone else: a partner, a parent, a grown
    # child. Standing the stop plan down left those lines with nothing (and one of them got
    # anxiety advice), so they get what actually helps: the short version of helping a person stop.
    entry("helping-someone-stop-smoking",
          (("quit smoking", "stop smoking", "giving up smoking", "giving up", "smokes", "smoker",
            "cigarettes", "cigarette", "vaping", "vape", "nicotine"),
           ("dad", "mum", "mother", "father", "husband", "wife", "partner", "girlfriend",
            "boyfriend", "son", "daughter", "brother", "sister", "friend", "mate", "nan",
            "nana", "gran", "grandad", "grandma", "grandpa", "he", "she", "they", "worried",
            "worry", "him", "her", "their", "their smoking")),
          "The decision has to be theirs, but you can make it much easier: pick a date together, "
          "say once what you have noticed and then leave it, and offer the nicotine patches or gum "
          "rather than a lecture. Keep the house and the car smoke-free, and do something else "
          "when the craving hits at the usual times. Expect two or three tries, so a slip is not "
          "a failure - just start again the next day.",
          # The person words in the key are what keeps my own habit on the stop plan's line
          # ("i want to stop smoking" names nobody), and "my dad" must still answer. A cough
          # after stopping is cough-after-quitting's, below, so it stands that one down.
          # "smokes" plus a person word is any smoking at all, so a drug that is not nicotine
          # stood this plan down for a weed or cannabis line, and a quit that finished years
          # ago is not a plan to make: both now fall to their own answers or to the hedge.
          avoid=("cough", "coughs", "coughing", "chest", "wheeze", "phlegm",
                 "weed", "cannabis", "joint", "joints", "skunk", "marijuana", "dope",
                 "spliff", "ganja", "hash", "stoned", "high",
                 "years ago", "already quit", "already stopped", "used to smoke",
                 "has quit", "has stopped", "gave up years", "quit years")),
    # A cough that turns up after someone quits is the thing that sends people back to smoking,
    # so the line is worth its own answer rather than the help-them plan or the cough entry.
    entry("cough-after-quitting",
          (("stopped smoking", "quit smoking", "gave up smoking", "stopped vaping",
            "since i stopped", "since i quit"),
           ("cough", "coughs", "coughing", "chest", "wheeze", "phlegm")),
          "That cough is usually the airways clearing themselves: the little hairs that sweep "
          "mucus out start working again once the smoke stops, so a few weeks of coughing up is "
          "normal and a good sign. Do not let it send you back to cigarettes. See a doctor if "
          "there is blood, if you are breathless, or if it is still there after a month.",
          avoid=("stop date",)),
    # "is vaping better than smoking" is a comparison, not a plan to quit: the stop plan avoids
    # "vape" (a vape line about a person belongs to habits.py's quit-vaping) and the help-them
    # plan needs a person word, so on main the question got the search hedge.
    entry("vaping-vs-smoking",
          (("vaping", "vape", "vapes", "e cigarette", "e cigarettes", "ecig", "ecigs"),
           ("better than", "worse than", "safer", "healthier", "harmful", "harm", "risk",
            "as bad", "bad as",
            "risks", "bad for", "damage", "compared", "compare", "switch", "switching",
            "instead of", "worth it", "side effects", "long term")),
          "Vaping is not harmless, but it is much less harmful than smoking: there is no tar "
          "and no carbon monoxide, and the nicotine arrives without the smoke that does most of "
          "the damage. What is left is the unknown - vapes are too new for long-term data, and "
          "the flavours are not tested for inhaling - so if you already smoke, switching is a "
          "real win, and if you do neither there is no reason to start. Most people's end point "
          "is neither one.",
          # a line that asks how to stop, or asks for help for someone, is not a comparison
          avoid=("stop", "stops", "stopping", "quit", "quits", "quitting", "giving up",
                 "give up", "help", "helping", "how do i", "cut down")),
    entry("cut-alcohol",
          (("alcohol", "drinking", "beer", "wine", "booze", "units"),
           ("cut down", "reduce", "less", "how much", "too much", "stop", "healthy", "limit",
            "week", "safe")),
          "The guideline is no more than 14 units a week, spread over three or more days, with "
          "a couple of drink-free days: that is about six pints of average beer or six medium "
          "glasses of wine. The changes that work are the boring ones - smaller glasses, a glass "
          "of water between drinks, no alcohol at home on weeknights, and a couple of alcohol-free "
          "beers in the fridge. If you are drinking every day to feel normal, or shaking without "
          "it, see a GP before stopping suddenly.",
          # the line has to be about alcohol, and "how much water should i drink a day" is
          # water-intake's answer rather than this one
          ask=("alcohol", "drinking", "drink", "drinks", "beer", "wine", "booze", "units",
               "pint", "pints", "vodka", "whisky", "gin"),
          avoid=("water", "hydrate", "hydration", "thirsty", "fluids", "juice", "milk",
                 # the drink that is not alcohol: "how much tea should i drink" was the weekly
                 # units answer, and the caffeine entry is the one that knows about tea
                 "coffee", "coffees", "espresso", "latte", "cappuccino", "tea", "teas",
                 "caffeine", "decaf", "cola", "energy drink", "energy drinks",
                 "how do i make", "recipe", "wine with", "pair with", "hangover",
                 # nobody's safe limit covers a pregnancy: "how much alcohol is safe in
                 # pregnancy" took the 14-units-a-week guideline, and the answer that matters
                 # is that no amount is known to be safe
                 "pregnant", "pregnancy", "expecting", "trimester", "breastfeeding")),
    entry("stress-relief",
          # "how do i destress" is the same ask in one word, and it had nothing at all
          (("stress", "stressed", "overwhelmed", "burnout", "burnt out", "anxious",
            # "how do i clear my head" is the same ask as "how do i destress" and it had
            # nothing: the plans card answered it with "start with the smallest version of it",
            # which is a plan for a job rather than for a head full of things
            "clear my head", "clear my mind", "clear my thoughts", "head is full",
            "mind is full", "cant think straight", "too much in my head",
            # not "switch off" or "wind down": those are the words of "how do i switch off the
            # wifi" and "how do i switch off the boiler", which are not about a person's stress
            "destress", "de-stress", "de stress", "destressing", "unwind"),
           ("deal", "manage", "how", "help", "reduce", "cope", "stop", "better", "relieve",
            "handling")),
          "Pick the smallest physical thing first, because stress lives in the body: a slow "
          "breath out for longer than the breath in, a ten-minute walk, or a glass of water and "
          "something to eat if you have skipped a meal. Then write down what is actually on your "
          "plate and cut one thing or ask for one deadline to move. Sleep, exercise and talking "
          "to someone once a week do more than any app; if it has been most days for weeks, or "
          "you cannot work or sleep, that is a GP conversation.",
          # "how do i tell my boss i am stressed" is about the conversation, not the feeling;
          # "how do i destress" is the feeling in one word.
          avoid=("stress fracture", "stress test", "stressed about money", "work stress",
                 "tell my boss", "tell your boss", "tell the boss", "tell my manager",
                 "talk to my boss", "talk to my manager", "with my boss", "raise it with",
                 "bring it up with",
                 # a head to clear at bedtime is the sleep question, and the sleep routine is
                 # the answer to it: "how do i clear my mind before bed" took this card on the
                 # phrase "clear my mind" when the helpful thing to say is lights down, screens
                 # off, and out of bed after 20 minutes
                 "before bed", "before bedtime", "to bed", "bedtime", "at bedtime",
                 "at night", "before sleep", "to sleep", "asleep", "so i can sleep",
                 "cant sleep", "can't sleep", "sleep",
                 # a person saying what already works is telling you, not asking: "taking a
                 # walk helps me clear my head" is not a request for the stress card
                 "helps me", "helped me", "helps my", "helped my", "works for me",
                 "helps a lot", "helps so much", "helps when")),
    entry("panic-attack",
          (("panic attack", "panic attacks", "panicking", "cant breathe", "heart racing"),
           # a panic attack arrives mid-sentence - "having one right now", "why do i get
           # them" - and the line is a request for what to do, not a topic nobody asked about
           ("stop", "how", "help", "deal", "cope", "what do i do", "during", "calm",
            "having", "right now", "think im", "think i am", "symptoms", "symptom", "why",
            "what is", "again", "at night", "feel like", "feels like", "keep", "started",
            "coming on", "what can i do")),
          "A panic attack peaks in about ten minutes and cannot hurt you, so the aim is to ride "
          "it rather than stop it: breathe out for longer than you breathe in, name five things "
          "you can see and four you can touch, and remind yourself it will pass. Don't fight the "
          "heart rate - it is adrenaline, not a heart problem. If they keep coming, ask about CBT: "
          "it is the treatment with the best evidence, and a GP can refer you.",
          # a nose that is blocked keys "cant breathe" and is a cold, not a panic
          avoid=("dog", "cat", "puppy", "kitten", "child", "my son", "my daughter")
                + NOT_A_NOSE),
    entry("friend-depression",
          # a son or a daughter is the parent's entry (main has teenager-low-mood), so this one
          # is the friend, the sibling and the partner
          (("friend", "mate", "husband", "wife", "partner", "brother", "sister"),
           ("depressed", "depression", "not themselves", "withdrawn", "suicidal", "self harm",
            "self-harm", "low", "help them", "support")),
          "Say it plainly and once - \"you have not seemed yourself, and I am worried about you\" "
          "- and then listen without fixing. Ask whether they have thought about suicide: asking "
          "does not plant the idea, and it is the thing that opens the door. Practical help is "
          "what people remember: a lift to a GP appointment, a walk, a text on a bad day. If they "
          "are in danger now, stay with them and call 999 or the Samaritans on 116 123.",
          avoid=("how do i tell", "how do i deal with", "my friend hurt me", "friend at work",
                 "my son", "my daughter", "my child", "my kid", "teenager", "my mum", "my dad",
                 "my mother", "my father")),
    entry("posture-sitting",
          (("posture", "sitting", "sit all day", "desk", "slouching", "hunched"),
           ("improve", "fix", "bad", "back", "pain", "hurts", "better", "how", "help")),
          "There is no perfect posture to hold: the fix is moving, not sitting straighter. Set "
          "the screen so the top is at eye level, feet flat, elbows near a right angle, and stand "
          "up every 30 to 40 minutes even for a minute. Two or three times a day, stand with your "
          "hands on the door frame and lean through for 20 seconds to open the chest, and do a "
          "few slow chin tucks. Back pain that comes with numbness, weakness or trouble passing "
          "water is a GP matter, not a posture one.",
          # a back that aches from sitting is this answer rather than the general back-pain one,
          # and the general one matches more of the line ("back", "pain", "aches"), so bias decides
          bias=1,
          # the desk in the key means sitting at one: "how do i clean a desk fan" was reaching
          # the screen-height answer on "desk" and "how". Only the fan words go here, because a
          # plain "how do i clean a desk" is answered as it was before, wrong or not, and taking
          # the cleaning words out too would turn that line into a hedge.
          # "a proper sit down with my manager" is a meeting, not an armchair: the noun is what
          # people call the conversation, and this answer was telling them the screen height.
          # Phrases, and only the noun ones: the verb ("when i sit down") is a body in a chair.
          avoid=("dog", "cat", "horse riding", "baby carrier", "chair", "mattress",
                 "a sit down", "sit down with", "sit down about", "sit down and talk",
                 "sit down to talk", "proper sit down", "sit down meeting",
                 "fan", "fans", "ceiling fan", "desk fan", "pedestal fan", "blades", "grille",
                 # "sit out" is food on the side, not a person in a chair: "how long can meat
                 # sit out" was answered with the screen height, on "sitting" and "how". Phrases,
                 # so the typo repair never reads one as a near miss of a key word.
                 "sit out", "sits out", "sat out", "sitting out", "left out", "left on the side",
                 "on the side", "room temperature", "out of the fridge", "out overnight",
                 "overnight", "how long can", "how long do", "how long does",
                 # a sit up is an exercise, not a chair: both fold to "sit", and "how do i do a
                 # sit up properly" was told that the fix is moving, not sitting straighter.
                 "sit up", "sit ups", "situp", "situps", "crunch", "crunches", "press up",
                 "press ups", "push up", "push ups", "squat", "squats", "plank", "planks",
                 "lunge", "lunges", "deadlift", "deadlifts", "reps", "rep", "workout",
                 "exercise", "form", "technique", "gym",
                 # painting a desk is the decorating row's job, and "how do i paint a desk" was
                 # the screen-height answer on "desk" once the hobby row stood down
                 "paint", "paints", "painted", "painting", "repaint", "varnish", "sand")),
    entry("cholesterol-eggs",
          (("eggs", "egg", "prawns", "shellfish", "liver", "dietary cholesterol"),
           ("cholesterol", "raise", "bad", "safe", "how many", "every day", "too many",
            "high", "affect", "ok", "good")),
          "For most people the cholesterol in food matters much less than the saturated fat in it: "
          "an egg a day is fine, and it is the butter, cheese, fatty meat and pastries around the "
          "egg that move your LDL. People with diabetes or an inherited high cholesterol are "
          "usually advised to keep to about one a day, and it is worth asking your GP if that "
          "applies to you. Prawns and liver are similar: fine in normal amounts, not a reason to "
          "worry on their own.",
          # "how many minutes for a boiled egg" is a cooking time, not a question about how many
          # eggs are safe: "how many" is in the key for "how many eggs a day", and it took the
          # timing line as well and answered it with the cholesterol advice.
          # A bare "boiled" is not enough on its own: "are boiled eggs good for you" is this
          # question and must keep this answer. It is the time that gives the line away.
          # And the verb tells a daily amount from a count in a dish or a count of days in the
          # box: "how many eggs go in an omelette" and "how many days do eggs keep" are not this.
          guard=not_a_count_for_the_box_or_the_dish,
          avoid=("how do i cook", "poach", "scramble", "how many minutes", "how many mins",
                 "how long", "minutes", "minute", "timer", "eggs for breakfast ideas",
                 # A shell that did not open is a food-safety question about that pan, not a
                 # question about cholesterol: "is it ok to eat shellfish that didnt open" was
                 # answered with the egg advice, because "shellfish" and "eat" are in this key
                 # and the mussel row's own key lost the tie on the extra word.
                 "open", "opened", "unopened", "shut", "closed", "stays open", "stayed shut",
                 "didnt open", "didn't open", "not opened")),
    entry("cough-lingering", (("cough", "coughs", "coughing"),
                              ("weeks", "week", "wont go away", "won't go away", "still",
                               "nearly", "persistent", "lingering", "long")),
          "A cough after a cold often lasts three to four weeks and still settles on its own: "
          "sip fluids, take honey (a spoonful, or in a warm drink), and don't bother with most "
          "cough medicines, which do little. See a GP if it is still there after three weeks, or "
          "sooner if you are coughing blood, getting breathless or wheezy, losing weight, or "
          "have a fever that keeps coming back.",
          # "wont go away" is how the line that never uses "weeks" is written, so "away" counts.
          ask=("weeks", "week", "long", "still", "nearly", "went", "back", "away"),
          avoid=("dog", "cat", "puppy", "kennel", "child", "children", "baby", "kid", "kids",
                 "toddler", "pregnant", "smoker", "smoking", "vape", "vaping"),
          bias=1),
    entry("chesty-cough", (("chesty", "cough", "phlegm", "mucus", "catarrh", "rattly",
                            # "how do i clear my chest" is the chesty cough in the words of
                            # the job, and it was a punt: the cough word was the only way in
                            "clear my chest", "clear the chest", "chest feels full"),
                           ("cold", "cough", "chest", "green", "yellow", "worse at night",
                            "at night")),
          "A chesty cough is usually a cold that has moved down, and the colour of what comes up "
          "does not mean you need antibiotics. Drink plenty, breathe steam from a bowl or a hot "
          "shower, prop yourself up to sleep, and give it two or three weeks. A GP the same day "
          "if you are breathless at rest, coughing blood, or feel properly unwell with a fever.",
          # "chest" and "cold" are furniture and a freezer as easily as a cough: "my chest of
          # drawers is stuck" and "the chest freezer is cold" both got this answer. The cough word
          # has to be in the line, and the chest of drawers and the freezer are named here.
          avoid=("dog", "cat", "puppy", "child", "children", "baby", "kid", "kids", "toddler",
                 # a parent's line about their own child belongs to the child cough entry, and
                 # "my son has a cough at night" was landing here
                 "son", "daughter", "my son", "my daughter",
                 "pigeon", "bird", "horse", "chicken", "chickens",
                 "drawers", "drawer", "of drawers", "furniture", "freezer", "cupboard",
                 "wardrobe", "chest of drawers", "treadmill",
                 # a dry cough is the opposite of this answer, and "at night" in the second part
                 # was enough to make it say a cold had moved down: "i have a dry cough at night"
                 # and "my cough is dry at night" are the honey-and-pillow answer's
                 "dry", "dry cough", "tickly", "tickly cough"),
          bias=1),
    # Work and the office only: this is the fever rules, and "school" in the key made every
    # "should i go to the school" a sick day. A parent asking whether to go into the school about
    # bullying, or to a school meeting, got "Stay off while you have a fever" (red-wasp, main
    # 04b0d523). A pupil's own school day is family.child-off-school's, and "can i go to school
    # with a cold" is science.cold-and-school's, so nothing loses its answer by narrowing here.
    entry("cold-back-to-work", (("work", "office"),
                                ("stay off", "go back", "back to", "should i go", "off work",
                                 "go in", "return")),
          "Stay off while you have a fever, and go back when you have been 24 hours without one "
          "and feel up to it: a normal cold with a bunged nose is fine to work through if you can "
          "keep away from people who are vulnerable. Rest and fluids get you back quicker than "
          "pushing through, and a fever, aches or a chesty cough means wait.",
          ask=("should", "when", "can", "safe", "ok", "okay"),
          avoid=("dog", "cat", "puppy", "chicken", "build", "diy", "shed", "garden", "plant",
                 "holiday", "flight", "abroad", "gym", "run", "running",
                 # a post office is a shop, not a workplace: "can i take a parcel back to the
                 # post office without the label" was answered with the fever rules
                 "post", "post office", "parcel", "parcels", "package", "label", "parcel shop",
                 "return a parcel", "return the parcel",
                 # whether to go into the office at all is a work-pattern question with no
                 # illness in it, and this answer is about a fever
                 "go to the office", "go into the office", "into the office", "the office on",
                 "back to the office", "the office tomorrow", "the office at the end",
                 "hybrid", "work from home",
                 # a child's school day is a different answer, and asked about someone else
                 "my son", "my daughter", "my child", "my kid", "my kids", "my baby",
                 "my toddler", "she", "he",
                 # a bone that is mending is "back to work" too, and the healing time is a
                 # different answer: "when can i go back to work after a broken wrist" was
                 # reaching the fever rules and then nothing
                 "broken", "broke", "fracture", "fractured", "cast", "plaster", "sprain",
                 "sprained", "injury", "injured", "operation", "surgery", "heal", "healing",
                 "recovery", "recovering", "physio", "crutches", "wrist", "ankle", "collarbone",
                 "rib", "ribs", "hip", "shoulder", "knee",
                 # "off work" is the go-back-to-work phrase this row is keyed on, and a week off
                 # is the opposite question: "i have a week off work what should i do" is asking
                 # what to do with the time, and got the fever rules for going back.
                 "week off", "weeks off", "week off work", "few days off", "off work for a week",
                 "off for a week", "off all week", "off for the week", "week off sick"),
          bias=1),
    entry("back-tweak", (("back", "back has gone", "put my back out", "tweaked my back",
                          "lower back"),
                         ("lifting", "lift", "tweaked", "twisted", "went", "gone", "rest",
                          "keep moving", "moving", "move", "better")),
          "Keep moving gently rather than resting in bed: most back strains ease in one to two "
          "weeks, and staying in bed makes them last longer. Carry on with your usual jobs but "
          "cut the lifting, take paracetamol or ibuprofen if you need it, and use a hot water "
          "bottle on the tight part. See a GP or a physio if the pain is down a leg, you have "
          "numbness or tingling, or it is no better after two weeks.",
          ask=("rest", "moving", "move", "better", "should", "what"),
          # a back that aches because of a desk is the posture answer, not the strain one
          avoid=("dog", "cat", "horse", "chair", "sofa", "garden", "hedge", "car", "seat",
                 "sit all day", "sitting all day", "sat all day", "sit at a desk",
                 "sitting at a desk", "sit at my desk", "sitting at my desk", "desk job",
                 "my son", "my daughter", "my husband", "my wife", "my mum", "my dad",
                 "my partner", "pregnant",
                 ),
          guard=_the_backs_are_a_body, bias=1),
    entry("sprain-heal", (("sprain", "sprained", "twisted", "ankle", "wrist", "thumb"),
                          ("heal", "healing", "how long", "long", "recover", "recovery", "take",
                           "weeks", "better")),
          "A sprained ankle or wrist usually hurts a lot for two or three days and is properly "
          "better in two to six weeks; a bad one can take three months. Ice it for 20 minutes at "
          "a time for the first couple of days, wrap it, keep it up when you can, and start "
          "moving it gently as the pain allows. Get it checked if you cannot put weight on it, "
          "it is badly swollen and bruised, or the joint looks out of shape.",
          ask=("how long", "long", "weeks", "when", "should"),
          # a bone that is actually broken is the fracture answer, not this one: "how long does a
          # broken wrist take to heal" was told a sprained wrist is better in two to six weeks
          avoid=("dog", "cat", "car", "wheel", "bike", "house", "market",
                 "broken", "broke", "fracture", "fractured", "cracked", "cast", "plaster",
                 # "30 weeks pregnant and my ankles are a bit swollen" matched "ankle" and
                 # "weeks" and was told how long a sprain takes: the pregnancy word wins
                 "pregnant", "pregnancy", "weeks pregnant", "trimester", "midwife"),
          bias=1),
    entry("headache-see-doctor", (("headache", "headaches", "head ache", "migraine"),
                                  ("worry", "worrying", "serious", "should i see", "doctor",
                                   "gp", "dangerous", "normal", "checked")),
          "Most headaches are not serious, and the ones to get checked the same day are: the "
          "worst you have ever had, one that comes on like a thunderclap, one with a fever and a "
          "stiff neck, one after a bang on the head, one with weakness, slurred speech or a "
          "change in vision, or a headache that is getting steadily worse over weeks. Otherwise "
          "a GP can look at it in the normal way if painkillers are needed more than a couple of "
          "days a week.",
          ask=("should", "worry", "serious", "normal", "dangerous", "checked", "see"),
          avoid=("dog", "cat", "child", "children", "baby", "kid", "kids", "pregnant"),
          bias=2),
    entry("headache-days", (("headache", "headaches", "head ache"),
                            # Any word that can carry a length, and the length is then read out
                            # of the line: see _headache_days below. A fixed word list cannot hold
                            # every number people write ("for 10 days", "for 12 days"), and a bare
                            # "days" or "week" alone took "ive had a headache all day" and told a
                            # person with a headache since breakfast to book a GP appointment.
                            ("day", "days", "week", "weeks", "weekend", "month", "months",
                             "fortnight", "while", "constant")),
          _headache_days_reply,
          # "while" is a key word here, so a line that asks what can be taken while pregnant or
          # feeding ("what can i take for a headache while breastfeeding") read as a headache with
          # a length on it. The medicine question owns those lines: body.py's
          # what-can-i-take-pregnant-or-feeding answers both halves.
          avoid=("dog", "cat", "child", "children", "baby", "kid", "kids", "pregnant",
                 "pregnancy", "breastfeeding", "breast feeding", "nursing", "chestfeeding",
                 "expecting", "trimester", "before my period", "hangover"),
          # "ive had a headache for 3 days should i worry" ties on words with the afternoon-
          # headache entry, and a headache with a duration in it is the one that needs the GP
          # line rather than the water-and-a-dark-room one.
          bias=4),
    # "gasping" and "gasp" are in the list because the sleep-apnoea row used to own that word
    # wherever it appeared, and "im gasping going up the stairs" is an effort on the stairs, not
    # a night-time airway: the second half of the key is what makes the gasp an effort, so a
    # line with no stairs, hill or walk in it is left alone.
    entry("out-of-breath-stairs", (("out of breath", "breathless", "short of breath",
                                    "puffed out", "puffed", "cant breathe",
                                    "gasping", "gasp", "gasped"),
                                   ("stairs", "upstairs", "walking", "hills", "hill",
                                    "exercise", "everyday")),
          "Getting puffed on the stairs is usually fitness rather than illness, and it improves "
          "in a few weeks if you walk a little more each day. Get it checked if it has come on "
          "over weeks, if you are breathless sitting still or lying flat, if it comes with chest "
          "pain, swollen ankles or a cough, or if it is worse than it was a month ago - that is a "
          "GP appointment, not a training problem.",
          # A statement of the symptom with no question word in it is still the question, so this
          # entry asks for nothing: "i get out of breath walking up the stairs" is the whole line.
          avoid=("dog", "cat", "car", "bike", "stairs at work", "lift", "running", "run",
                 "marathon", "swim"),
          bias=1),
    entry("tablets-forgotten", (("tablet", "tablets", "pill", "pills", "medication",
                                 "medicine", "inhaler"),
                                ("forget", "forgetting", "forgot", "miss", "missing",
                                 "remember", "keep forgetting")),
          "Put the tablets where the job happens rather than where they are stored - by the "
          "kettle, the toothbrush, the front door - and set a phone alarm with the name of the "
          "dose. A weekly pill box from the pharmacy makes a missed day obvious, and a pharmacist "
          "can switch you to a once-a-day version or a combined tablet if the timing is the "
          "problem. If you have missed a dose, take it when you remember unless it is nearly time "
          "for the next one, and never double up; ask the pharmacist about your particular tablet.",
          ask=("how", "keep", "help", "what", "should"),
          avoid=("dog", "cat", "puppy", "horse", "child", "children", "baby", "kid", "kids",
                 "water", "dishwasher", "washing machine", "toilet", "limescale"),
          bias=1),
    entry("tired-after-illness", (("flu", "cold", "virus", "infection", "covid", "illness"),
                                  ("tired", "knackered", "exhausted", "fatigue", "weeks",
                                   "still", "normal", "energy")),
          "Feeling washed out for a week or two after flu or another virus is normal, and it "
          "eases faster if you build back up slowly - a short walk, then a bit further - rather "
          "than going straight back to everything. Eat properly, keep fluids up and get your "
          "usual sleep. See a GP if the tiredness is no better after three or four weeks, or if "
          "it comes with breathlessness, a racing heart or feeling low.",
          # The tiredness has to be the thing asked about: "i have a cold, can i still run" is
          # the exercise question, and this answer used to take it on the word "still".
          ask=("tired", "tiredness", "knackered", "exhausted", "exhaustion", "fatigue",
               "washed out", "no energy", "worn out", "drained", "shattered", "lethargic"),
          avoid=("dog", "cat", "puppy", "horse", "child", "children", "baby", "kid", "kids",
                 "toddler", "pregnant", "my mum", "my dad", "my husband", "my wife"),
          bias=1),
    entry("immune-boost",
          (("immune system", "immunity", "immune"),
           ("boost", "improve", "stronger", "strengthen", "how", "better", "support",
            "naturally", "build")),
          "You cannot boost it with a pill: the things that hold up are sleep of seven to nine "
          "hours, regular activity, enough fruit and vegetables, not smoking, keeping alcohol "
          "low, and the vaccines you are offered. Vitamin D 10 micrograms a day through autumn "
          "and winter is the one supplement worth taking for most people. Big doses of vitamin C, "
          "echinacea and the rest have not held up in trials, and if you keep getting infections "
          "that is a GP question rather than a supplement one."),

    entry("missed-contraceptive-pill",
          (("pill", "pills", "contraceptive", "contraception", "mini pill", "combined pill"),
           ("missed", "miss", "forgot", "forgotten", "skipped", "late", "sex", "unprotected",
            "condoms", "contraceptive", "mini", "last night", "this week")),
          _missed_pill,
          bias=2,
          ask=(("missed", "miss", "forgot", "forgotten", "skipped", "late", "sex", "unprotected",
                "condoms"),),
          # a blood pressure pill, a vitamin or a painkiller keeps the generic answer
          avoid=("blood pressure", "statins", "tablet", "tablets", "medication", "medicines",
                 "insulin", "diabetes", "antibiotics", "water", "vitamin", "vitamins", "diet",
                 "painkiller", "painkillers", "headache", "hayfever", "allergy", "morning after",
                 "emergency contraception", "paracetamol", "ibuprofen")),
    entry("missed-medication",
          (("tablets", "tablet", "medication", "medications", "medicines", "medicine", "pills",
            "pill", "insulin", "dose", "doses", "dosage", "prescription", "prescriptions",
            # the tablets whose skipped dose has its own rule: each needs its own branch below
            "warfarin", "epilepsy", "epileptic", "thyroid", "levothyroxine", "blood thinner",
            "blood thinners", "antibiotic", "antibiotics", "penicillin", "amoxicillin"),
           ("confused", "muddled", "muddle", "forgot", "forget", "forgets", "forgetting",
            "missed", "miss", "missing", "double", "doubled", "doubling", "twice", "remember",
            "remembering", "remembers", "keeps forgetting", "ran out", "runs out", "mixed up",
            "instead", "by mistake", "mistake", "accident", "accidentally")),
          _missed_medication,
          # main's tablets-forgotten answers the routine question ("my dad keeps forgetting his
          # tablets") and was winning the missed-dose lines too: a missed dose is a different
          # question with a different answer, so this one ranks above it.
          bias=2,
          # an overdose, and a story about a tablet long ago, are not this
          avoid=("overdose", "too many", "took all", "swallowed", "years ago", "side effect",
                 "side effects", "paracetamol", "ibuprofen", "morning after",
                 # a contraceptive pill has its own rule: seven days of condoms, not "carry on"
                 "contraceptive", "contraception", "mini pill", "combined pill", "my pill",
                 "had sex", "unprotected")),
    # "should i keep taking the tablets" is the commonest shape of this question and it reached
    # nothing: a pharmacist line, the expired-tablet card ("a dry tablet keeps its strength"), the
    # side-effects card, or - for "should i keep taking the tablet" - the support page for a
    # tablet computer. Every one of those is a different question from *should I stay on this*.
    entry("keep-taking",
          (("tablet", "tablets", "pill", "pills", "medication", "meds", "medicine", "medicines",
            "prescription", "statins", "statin", "inhaler", "steroids", "prednisolone",
            "antidepressants", "antibiotics", "antibiotic", "blood pressure tablets",
            "thyroid tablets", "levothyroxine"),
           ("keep taking", "keep on taking", "keep them up", "carry on taking", "carrying on",
            "stay on", "staying on", "still take", "still taking", "still be taking",
            "should i still be", "should i be taking", "am i supposed to keep", "supposed to be",
            "should i keep",
            "should i stop", "can i stop", "stop taking", "stop them", "come off", "coming off",
            "do i have to keep", "do i have to take", "have to take them", "need to keep",
            "for life", "for good", "forever", "long term", "is it ok to stop", "ok to stop",
            "bad to stop", "safe to stop", "should i finish", "finish the course", "finish them")),
          _keep_taking,
          # The side-effects, expired-tablet and not-working cards all key "tablet" and hold one of
          # these phrases too, so this has to outrank them: the question here is whether to stay on
          # the medicine at all, and stopping is the dangerous half of it.
          bias=5,
          # A tablet computer is not a tablet you swallow, and the questions around the medicine
          # box are somebody else's: an expiry date, a missed dose, a side effect, a pill for
          # contraception or for vitamins.
          ask=("keep", "keeps", "should", "can", "do i", "is it", "stop", "stay", "come off",
               "still", "finish", "safe", "ok", "bad", "have to", "need"),
          avoid=("screen", "screens", "app", "apps", "wifi", "wi-fi", "battery", "batteries",
                 "charger", "charging", "sim", "storage", "draw", "drawing", "stylus", "pen",
                 "cracked", "slow", "kindle", "ipad", "android", "samsung", "fire", "kids",
                 "child", "children", "baby", "toddler", "puppy", "dog", "cat",
                 "out of date", "past the date", "expired", "expiry", "use by", "old tablets",
                 # a tablet that goes back to a shop is a thing, not a medicine: the follow-up
                 # reader turns "should i keep taking it back to the shop" into the tablet itself,
                 # so the return words are what keep the two apart
                 "shop", "refund", "warranty", "guarantee", "receipt", "exchange", "return it",
                 "returning it", "send it back", "took it back", "take it back", "money back",
                 # "the pill" on its own is the contraceptive: a pill chat is not a tablet chat
                 "the pill", "my pill", "on the pill", "contraceptive", "contraception",
                 "mini pill", "combined pill", "morning after", "vitamin", "vitamins",
                 "hayfever", "hay fever", "allergy",
                 "overdose", "too many", "swallowed", "double", "doubled", "missed", "miss",
                 "forgot", "forget", "forgetting", "ran out", "run out", "with alcohol",
                 "side effect", "side effects", "making me", "breastfeeding", "pregnant")),

]

# Whether it is free is a different question from what it costs, and "is the dentist free on the
# nhs" was the price table's blind spot: none of the money words are in the line at all. It is its
# own row because the answer is the qualifying list, not a range, and the price row keeps the
# question that asks what the work costs.
ENTRIES.append(entry(
    "nhs-dentist-free",
    (("dentist", "dentists", "dental", "check up", "checkup", "nhs", "filling", "crown"),
     ("free", "get it free", "free treatment", "do i pay", "do i have to pay", "covered",
      "who pays", "qualify", "exempt", "concession")),
    "NHS dentistry is free for children, anyone under 19 in full-time education, pregnant women "
    "and mothers in the year after the birth, and people on certain benefits such as universal "
    "credit or income support. Everyone else pays a fixed band per course of treatment - about "
    "£27 for a check-up, £75 for a filling and £325 for a crown or a denture - and a check-up is "
    "free in Scotland. Ask at the desk which band you are in, because the work in one band is "
    "covered by one charge.",
    # the price of the work and the private comparison keep their own answer
    avoid=("how much", "how many", "cost", "costs", "price", "prices", "charge", "charges",
           "private", "expensive", "cheaper", "worth it", "going rate"),
    bias=2))



# --- the clock question: what time to go to bed, and what time to get up ---------------------
# "What time should I go to bed tonight" and "what time should I wake up" were both a search
# hedge, because every sleep entry here answers how much, why, or lying awake, and nothing was
# keyed on the clock. It is the one sleep question with an arithmetic answer, so the reply works
# it back from the morning, and reads a stated wake time when the line gives one.
_CLOCK_AT = re.compile(r"\b(up|awake|wake|wakes|alarm|get up|getting up)\b[^0-9]{0,16}?"
                       r"\b(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?\b")
# The same question the other way round: a bedtime given, and the morning asked for.
_BED_AT = re.compile(r"\b(bed|bedtime|sleep|lights out)\b[^0-9]{0,14}?"
                     r"\b(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?\b")


def _clock_time(hour, minute):
    """"6.30am", "10.20pm": the way a person says a clock time."""
    suffix = "am" if hour < 12 else "pm"
    on_clock = hour % 12 or 12
    return "%d%s" % (on_clock, suffix) if not minute else "%d.%02d%s" % (on_clock, minute, suffix)


def _back_from(hour, minute, hours):
    """The clock time `hours` before the one given, counted back over midnight."""
    total = (hour * 60 + minute - hours * 60 - 20) % (24 * 60)     # and 20 minutes to drop off
    return total // 60, total % 60


def _forward_from(hour, minute, hours):
    """The alarm a given bedtime leads to: twenty minutes to drop off, then `hours` asleep."""
    total = (hour * 60 + minute + 20 + hours * 60) % (24 * 60)
    return total // 60, total % 60


def _sleep_clock(memory, understood):
    """A bedtime worked back from the morning, or the morning picked once if that is the ask."""
    text = (understood or {}).get("clean") or ""
    found = _CLOCK_AT.search(text)          # "to be up at 6.30" is the morning, and comes first
    in_bed = None if found else _BED_AT.search(text)
    hour, minute = 0, 0
    if found or in_bed:
        match = found or in_bed
        try:
            hour, minute = int(match.group(2)), int(match.group(3) or 0)
        except (TypeError, ValueError):
            hour, minute = 0, 0
        if match.group(4) == "pm" and hour < 12:
            hour += 12
        if in_bed and hour < 12 and not match.group(4):
            hour += 12                       # "in bed at 11" is the evening, not the morning
    if in_bed and 20 <= hour <= 23 or in_bed and hour <= 3:
        eight = _forward_from(hour % 24, minute, 8)
        nine = _forward_from(hour % 24, minute, 9)
        return ("In bed at %s, asleep about twenty minutes later, so up at %s on eight hours or "
                "%s on nine - and that alarm is worth keeping the same every day, weekend "
                "included, because the fixed morning is what sets the body clock and the bedtime "
                "then follows it."
                % (_clock_time(hour % 24, minute), _clock_time(*eight), _clock_time(*nine)))
    if 4 <= hour <= 11:
        eight = _back_from(hour, minute, 8)
        nine = _back_from(hour, minute, 9)
        return ("To be up at %s, count back eight hours and leave twenty minutes to drop off, so "
                "lights out about %s - and about %s if you are a nine-hour sleeper. What matters "
                "more than the exact minute is keeping the morning the same every day, weekend "
                "included, because that is the end of the night the body clock sets itself by, "
                "and the bedtime then falls into place on its own."
                % (_clock_time(hour, minute), _clock_time(*eight), _clock_time(*nine)))
    return ("Work it back from the morning: pick the time you have to be up, count back eight "
            "hours and allow twenty minutes to drop off - a half six alarm means lights out about "
            "ten, a seven o'clock one about half ten. Nine-hour sleepers go an hour earlier. Keep "
            "the wake-up time the same every day, weekends included: a bedtime held while the "
            "mornings shift is the wrong way round. If you lie awake an hour, the bedtime is too "
            "early, not too late.")


ENTRIES.append(entry(
    "sleep-clock",
    # The morning side of the question, because the general "what time should i go to bed" is
    # already answered in bot/knowledge/sleep.py and this adds the arithmetic, not a rival answer.
    (("wake up", "waking up", "get up", "getting up", "alarm", "up", "awake"),
     ("what time", "what hour", "when should i", "how late", "how early", "time should i",
      "time do i", "time to", "goal", "need to be")),
    _sleep_clock, bias=1,
    ask=("what time", "when should i", "how late", "how early", "time should i"),
    # A child's bedtime, a nap, a shift worker's clock and a night of waking are all their own
    # answers, and none of them is a count-back from a morning alarm.
    avoid=("kids", "child", "children", "my son", "my daughter", "toddler", "baby", "babies",
           "newborn", "teenager", "teenagers", "teen", "school night", "school nights",
           # A child's bedtime is written by age far more often than by word: "what time should my
           # 7 year old go to bed" was getting the adult count-back. The phrases, not a bare
           # "year", which is every sentence about a holiday or a birthday.
           "year old", "years old", "yr old", "yrs old", "month old", "months old",
           "year-old", "years-old", "old go to bed", "puppy",
           "cat", "dog", "shift work", "night shift", "jet lag", "time zone", "nap", "naps",
           "insomnia", "cant sleep", "can't sleep", "cant get to sleep", "wake up at 3",
           "wake at 3", "wake up at 4", "wake at 4", "2am", "3am", "4am", "5am",
           "cant get back to sleep", "middle of the night", "too late", "stay up too late",
           # "put the tree up" is one phrasal verb: the up is the tree, not the morning alarm,
           # and the count-back was answering when to decorate
           "tree up", "put up", "putting up", "christmas tree", "xmas tree", "decorations",
           "decorate", "decorating")))


# --- everyday gaps: questions people ask that nothing answered -------------------------------
# Each is a real mechanism at school level, kept to two or three sentences. They are appended
# here rather than beside the older cards so the diff is one block and the ids stay easy to find.

ENTRIES.append(entry(
    "closest-planet",
    (("closest to the sun", "closest planet to the sun", "nearest to the sun",
      "nearest the sun", "closest to the sun", "first planet", "innermost planet",
      "mercury closest", "mercury the closest"),
     ("which planet", "what planet", "mercury", "closest", "nearest", "sun")),
    "Mercury is the closest planet to the Sun, about 58 million km out, and it goes round once "
    "every 88 Earth days. It is not the hottest, though: Venus is, because its thick carbon "
    "dioxide atmosphere traps the heat.",
    avoid=("moon", "moons", "star", "stars", "toxic", "poison", "thermometer", "fish",
           "element", "barometer", "symbol", "planet facts", "retrograde", "astrology",
           "sign", "horoscope", "metal")))

ENTRIES.append(entry(
    "moon-orange",
    (("moon", "moons"), ("orange", "red", "yellow", "pink")),
    "Near the horizon the Moon's light crosses much more air, and the air scatters the blue end "
    "of it away, so what reaches you looks orange or red. The same effect reddens a low Sun, and "
    "dust or smoke deepens it.",
    ask=("orange", "red", "yellow", "pink", "why", "colour", "color"),
    bias=1))

ENTRIES.append(entry(
    "blood-moon",
    (("blood moon", "lunar eclipse", "lunar eclipses"),
     ("what", "why", "is", "red", "orange", "happen", "happens")),
    "A blood moon is a lunar eclipse: the Earth sits between the Sun and the Moon, and the only "
    "sunlight reaching the Moon has passed through Earth's atmosphere, which scatters the blue "
    "away and leaves red. It is safe to look at, unlike a solar eclipse.",
    bias=1))

ENTRIES.append(entry(
    "moon-white",
    (("moon", "moons"), ("white", "grey", "gray", "silver", "pale")),
    "The Moon is grey-brown rock; it looks white because it is lit by direct sunlight against a "
    "black sky, and your eyes judge it against that darkness. The bright and dark patches are "
    "different rocks, not ice or cloud.",
    ask=("white", "grey", "gray", "silver", "pale", "why", "colour", "color"),
    bias=1))

ENTRIES.append(entry(
    "moon-craters",
    (("moon", "moons"), ("crater", "craters", "pothole", "potholes", "dark spot",
                          "dark spots", "dark patch", "dark patches")),
    "The Moon's craters are mostly impact scars from rocks that hit it over billions of years, "
    "and with no air or water to erode them they stay. The dark patches are old lava plains, not "
    "shadows.",
    ask=("why", "how", "what", "made", "made of", "formed", "have", "get")))

ENTRIES.append(entry(
    "shooting-star",
    (("shooting star", "shooting stars", "falling star", "falling stars", "meteor", "meteors"),
     ("what", "why", "is", "are", "see", "night", "sky")),
    "A shooting star is a speck of dust or grit burning up high in the atmosphere, not a star "
    "falling. Most are the size of a grain of sand and vanish in a second; during a meteor shower "
    "you can see dozens an hour.",
    avoid=("photograph", "photography", "photo", "picture", "camera", "phone", "film",
           "movie", "song", "lyrics", "lyric", "band", "album", "track", "cook", "chicken"),
    bias=3))

ENTRIES.append(entry(
    "rockets-work",
    (("rocket", "rockets", "rocket engine", "rocket engines"),
     ("how", "work", "works", "fly", "launch", "space", "get to space", "escape")),
    "A rocket pushes gas out of the back at high speed, and the equal push forwards lifts it; it "
    "does not need air to push against. It has to reach about 28,000 km/h sideways to stay in "
    "orbit rather than fall back.",
    avoid=("toy", "toys", "lego", "bottle", "water bottle", "cress", "salad", "leaf",
           "leaves", "my app", "launch my", "game", "games", "kerbal", "rocket league",
           "app store", "startup", "business")))

ENTRIES.append(entry(
    "humidity",
    # "Close" on its own is the verb people use for a shop shutting - "what time does the post
    # office close", "why does the library close so early" - and it took those turns for the muggy
    # weather answer, because the second group only asks for a question word. The adjective is
    # kept only where it is said with the weather: "close and muggy", "close in here". "Close
    # tonight" and "close today" are left out for the same reason as "close" - "does it close
    # tonight" is the shop shutting.
    (("humidity", "humid", "relative humidity", "muggy", "sticky", "close and",
      "close in here", "close weather"),
     ("what", "why", "mean", "means", "high", "low", "air", "hot")),
    "Humidity is how much water vapour the air holds; relative humidity is that as a share of "
    "the most it could hold at that temperature. Warm air holds more, which is why a hot muggy "
    "day feels worse than the same heat in dry air.",
    avoid=("forecast", "weather app", "tomorrow", "weekend")))

ENTRIES.append(entry(
    "hunger",
    (("hungry", "hunger", "why am i hungry", "why do i get hungry"),
     ("why", "what", "always", "still", "after", "eat", "eating", "meal", "meals")),
    "Hunger is your body's signal that fuel is running low: the stomach releases a hormone "
    "called ghrelin, and blood sugar and habit both feed into it. Feeling hungry again soon after "
    "a meal is often a fast carbohydrate meal rather than a real shortage; protein, fibre and fat "
    "keep it down for longer.",
    avoid=("food bank", "food banks", "starving", "starve", "cant afford", "can't afford",
           "no money", "benefits", "hunger strike", "africa", "famine", "cat", "cats",
           "dog", "dogs", "puppy", "puppies", "kitten", "kittens", "pet", "pets", "vet",
           # an animal that is always hungry is the pet's diet, not the human's ghrelin: "my
           # horse is always hungry" and "my rabbit is always hungry" were told why the stomach
           # releases ghrelin, which is advice about a person
           "horse", "horses", "pony", "ponies", "rabbit", "rabbits", "bunny", "bunnies",
           "guinea pig", "guinea pigs", "hamster", "hamsters", "gerbil", "gerbils", "ferret",
           "parrot", "parrots", "budgie", "budgies", "bird", "birds", "chicken", "chickens",
           "fish tank", "tortoise", "lizard", "snake", "reptile", "livestock",
           "cattle", "sheep", "goat", "goats",
           # A book or a film named in the line is the subject, and the title is not a topic:
           # "what about a book for her, she liked the hunger games" was given ghrelin because
           # the title says hunger (reported by cheerful-jay).
           "hunger games", "the hunger games", "book", "books", "novel", "novels",
           "film", "films", "movie", "movies", "box set", "tv series", "series",
           "watch", "watching", "reading", "read", "author", "called")))

ENTRIES.append(entry(
    "thirst",
    (("thirsty", "thirst", "why am i thirsty", "why do i get thirsty"),
     ("why", "what", "always", "so", "very", "mean", "means")),
    "Thirst means your body is slightly short of water and your blood has become a little more "
    "concentrated; your brain responds by making you want a drink and your kidneys concentrate "
    "your urine. If you are always thirsty and passing a lot of urine, get it checked, because "
    "that can be diabetes.",
    avoid=("beer", "wine", "hangover", "pub", "drink less", "alcohol")))

ENTRIES.append(entry(
    "things-fall",
    (("things fall", "why do things fall", "falling", "fall"),
     ("why", "what", "makes", "make", "gravity", "down")),
    "Things fall because gravity pulls every mass towards every other mass, and the Earth is by "
    "far the biggest thing near you. Drop a stone and a coin together with no air and they hit "
    "at the same time; air resistance is what makes a feather float.",
    # a person falling is the falls question, not the physics one: "what should i do about my
    # dad falling" was being given a lesson on gravity
    avoid=("hair", "leaves", "leaf", "rain", "snow", "prices", "stocks", "shares", "asleep",
           # "why does my fish fall apart when i fry it" was a lesson on gravity, off "fall":
           # a thing coming apart is not a thing falling, and the kitchen answers it.
           "apart", "falls apart", "falling apart", "fell apart", "breaks up", "breaking up",
           "to bits", "crumbles", "crumbling", "in the pan", "in the oven", "when i cook",
           "fell over", "fall over", "fell down the stairs",
           # an empire falls too, and every one of those is a history line with its own answer:
           # "why did the aztecs fall" was getting a lesson on gravity and a dropped stone
           "aztec", "aztecs", "inca", "incas", "rome", "roman", "romans", "empire", "empires",
           "civilisation", "civilization", "dynasty", "regime", "soviet", "berlin wall",
           "government", "governments", "monarchy", "kingdom", "republic", "slave trade",
           # and not every "fall" is a thing going down through the air: "i keep falling behind",
           # "i keep falling for the wrong people" and "we didnt fall out" were all given the
           # dropped-stone lesson. Falling behind is being behind on work, falling for somebody
           # is love, and a falling-out is a row.
           "falling for", "fell for", "fall for", "fall out", "falling out",
           "fell out", "falls out", "falling behind", "fell behind", "falls behind",
           "my dad", "my mum", "my mother", "my father", "my nan", "my nana", "my grandad",
           "my grandma", "grandad", "grandma", "granny", "grandpa", "elderly", "oap",
           "unsteady", "balance", "his feet", "her feet", "on his feet", "on her feet",
           "shaky", "hip", "hospital", "ambulance", "the stairs")))

ENTRIES.append(entry(
    "bubbles-pop",
    (("bubble", "bubbles", "soap bubble", "soap bubbles"),
     ("pop", "pops", "burst", "why", "last", "float", "make")),
    "A bubble is a thin film of water with soap holding it together, and it pops when the water "
    "drains or evaporates from the top until the film is too thin. Dry air and a dusty surface "
    "speed that up, which is why bubbles last longer in a steamy bathroom.",
    avoid=("bubble tea", "bubble wrap", "gum", "economy", "housing", "market",
           "stomach", "tummy", "gut", "wind", "gas", "bloating", "belly", "fart",
           "urine", "pee", "wee", "piss", "bladder", "kidney")))

ENTRIES.append(entry(
    "stars-count",
    (("stars", "star"),
     ("how many", "number", "count", "in the sky", "universe")),
    "From a dark place you can see about 2,000 to 3,000 stars at once, and the whole sky holds "
    "around 9,000 visible to the naked eye. The Milky Way alone has 100 to 400 billion, and the "
    "observable universe has more stars than there are grains of sand on Earth.",
    avoid=("star sign", "star signs", "horoscope", "zodiac", "star wars", "movie", "film",
           "hotel", "restaurant", "review", "rating", "michelin")))


ENTRIES.append(entry(
    "moon-bright",
    (("moon", "moons"), ("bright", "shining", "shine", "glow", "glowing")),
    "The Moon makes no light of its own: it reflects sunlight, and at full moon it is opposite "
    "the Sun so nearly all of its lit face is turned towards you. Its rock is dark grey, but "
    "with no air to dim the light and a black sky around it, it looks brilliant.",
    ask=("why", "what", "so", "look", "looks", "bright", "shine", "glow"),
    bias=1))

ENTRIES.append(entry(
    "kettle-whistle",
    (("kettle", "kettles", "electric kettle"),
     ("whistle", "whistles", "whistling")),
    "The whistle is a small cap with a slit: steam from boiling water is forced through it and "
    "makes the air vibrate, which is the note you hear. It stops when you lift the cap or the "
    "switch cuts the power, and a whistle that never sounds usually means the cap is loose or "
    "blocked.",
    avoid=("descale", "descaler", "descaling", "limescale", "scale", "fur", "furred", "clean",
           "cleaning", "element", "slow", "not boiling", "wont boil", "won't boil",
           "taste", "tastes", "smell", "smells", "plastic", "so long", "take so long",
           "takes so long", "boil over", "boils over"),
    bias=3))

ENTRIES.append(entry(
    "banana-curved",
    (("banana", "bananas"), ("curved", "curve", "bent", "bend", "why", "shape")),
    "A banana starts growing downwards, then turns and grows upwards towards the light, and the "
    "side facing the ground grows faster, so the fruit ends up curved. The bend is set by the "
    "time it is cut, which is why a bunch hangs like a hand of fingers.",
    avoid=("bread", "cake", "muffin", "loaf", "milkshake", "smoothie", "recipe", "brown",
           "black", "ripe", "ripen", "eat", "peel", "banana plant", "banana tree",
           "how do bananas grow", "growing bananas"),
    ask=("why", "what", "how", "curved", "curve", "bent", "shape")))


ENTRIES.append(entry(
    "mirror-reverse",
    (("mirror", "mirrors"), ("reverse", "reverses", "backwards", "back to front",
                             "left and right", "left right", "why", "what")),
    "A mirror does not swap left and right: it swaps front and back, because it sends the light "
    "straight back at you. Your face is nearly symmetrical, so the only thing you notice is that "
    "a raised right hand seems to be on the other side.",
    avoid=("makeup", "make up", "shave", "shaving", "clean", "cleaning", "fog", "steam",
           "hang", "hanging", "wall", "buy", "shatter", "broken", "bedroom", "bathroom"),
    ask=("why", "what", "how", "reverse", "reverses", "backwards", "left", "right")))

ENTRIES.append(entry(
    "cut-sting",
    (("cut", "cuts", "graze", "scrape", "scratch", "paper cut"),
     ("sting", "stings", "hurt", "hurts", "why", "salt", "lemon")),
    "A cut stings because the broken skin leaves nerve endings exposed, and salt, lemon or soap "
    "irritates them directly; the sting fades as the cut seals. Rinse it with clean water and "
    "cover it, and get help if it is deep, very dirty or will not stop bleeding.",
    avoid=("recipe", "cook", "cooking", "meat", "beef", "lamb", "pork", "chicken", "cake",
           "hair", "grass", "lawn", "wood", "metal", "budget", "pay", "job", "staff",
           "infected", "infection", "septic", "pus", "swollen", "red", "hot", "smell", "smells",
           "tetanus", "deep", "bleeding", "stitches",
           # a machine that "cuts out" is stopping, not cutting anything: "why does my boiler keep
           # cutting out" was answered "a cut stings because the broken skin leaves nerve endings
           # exposed". The particles are phrases so a genuine cut keeps this answer - "i cut my
           # finger on a tin", "why does a cut sting" - and cutting something out of paper, cake or
           # a dress pattern is not in these shapes.
           "cut out", "cuts out", "cutting out", "cut off", "cuts off", "cutting off",
           "cut out on me", "keeps cutting out", "cutting out at", "cuts out when",
           # an animal scratches what it sits on, and a sting has nothing to do with that: "why
           # does my cat scratch the furniture" was answered "a cut stings because the broken skin
           # leaves nerve endings exposed". The shapes are phrases, not the bare animal, because a
           # cat scratch on a hand is a cut and keeps this answer: "how do i treat a cat scratch".
           "scratching the", "scratches the", "scratch the", "keeps scratching", "scratching my",
           "scratch its", "scratch his", "scratch her", "scratch everything", "scratch the door",
           "furniture", "flea", "fleas", "mites", "scratching post", "scratch post",
            # a room's things are not a cut either: "why does my cat scratch the sofa" was the
            # delivery-note row and "my dog scratched the floor" the nerve-endings answer, so
            # the surfaces the animal works on stand this fact down too. The animal words are
            # deliberately not here - "how do i treat a cat scratch" is a wound and keeps it.
            "sofa", "settee", "couch", "carpet", "floor", "claws", "clawing",
           # the same shape for a dog: "why is my dog scratching" met "why" and "scratching"
           # here and was told about a cut, when the itch row further down is the answer
           "dog scratching", "dog scratches", "dog keeps scratching", "scratches himself",
           "scratching himself", "my dog scratching"),
    ask=("why", "what", "how", "sting", "stings", "hurt", "hurts", "salt", "lemon"),    bias=2))


ENTRIES.append(entry(
    "sun-made-of",
    (("sun",), ("made of", "made from", "composed", "composition", "hydrogen", "helium",
                "inside", "what is it made")),
    "The Sun is about three-quarters hydrogen and a quarter helium, all so hot that it is a "
    "gas-like plasma. Its gravity squeezes the core until hydrogen fuses into helium, and that "
    "reaction is what makes its light and heat.",
    avoid=("hot", "heat", "temperature", "burn", "sunburn", "sun cream", "sunscreen", "lamp",
           "bed", "bright", "moon"),
    ask=("what", "made", "of", "from", "inside")))

ENTRIES.append(entry(
    "day-night",
    # "how do we get day and night" asked with the words of the asking ("how", "get"), and the
    # second part of the key is read off what the first part leaves, so the asking words belong
    # there rather than in a phrasing that would swallow the whole line and score too little.
    (("day and night", "day night", "night and day"),
     ("why", "what", "cause", "causes", "happen", "happens", "have", "earth", "sun", "work",
      "works", "get", "how", "does", "do")),
    "The Earth turns on its axis about once every 24 hours, so the half facing the Sun is in "
    "daylight while the other half is in night. The Sun itself does not go anywhere.",
    # "how do we get day and night" carries none of the why-words the row looked for, and the
    # ask gate alone turned it away; "how" and "get" are how the same question is put. The
    # sleep words are the same phrase about a person's own night, which a sleep row answers.
    ask=("why", "what", "cause", "have", "how", "get", "does", "make", "makes"),
    avoid=("baby", "babies", "toddler", "newborn", "sleep", "sleeping", "slept", "wake",
           "waking", "woke", "night shift", "shift work", "jet lag", "insomnia")))

ENTRIES.append(entry(
    "earth-round",
    (("earth", "world"), ("round", "sphere", "spherical", "flat", "shape", "why")),
    "Gravity pulls every part of a large body towards its centre, and over 4.5 billion years that "
    "has pulled the Earth into a ball. Its spin makes it bulge slightly at the equator, so it is a "
    "squashed sphere rather than a perfect one.",
    avoid=("around the world", "travel", "trip", "song", "lyrics", "earthquake", "earth wire",
           "rare earth", "earth day", "earth hour", "down to earth"),
    ask=("why", "is", "round", "flat", "shape")))

ENTRIES.append(entry(
    "urine-yellow",
    (("urine", "pee", "wee"), ("yellow", "why", "colour", "color")),
    "Urine is yellow because it carries urobilin, a breakdown product of old red blood cells, and "
    "the more water you drink the paler it gets. See a doctor if it is dark brown or red, or comes "
    "with pain or fever, because those are not just concentration.",
    avoid=("dark", "brown", "red", "blood", "pain", "burning", "stings", "smell", "foamy",
           "cloudy", "infection", "doctor", "gp", "uti", "pregnant", "test"),
    ask=("why", "yellow", "colour", "color")))

ENTRIES.append(entry(
    "energy-what",
    (("energy",), ("mean", "meaning", "definition", "explain", "what is energy")),
    "Energy is the ability to make something happen - to move, heat, light or power something - "
    "and it is never used up, only changed from one form into another. Food stores chemical "
    "energy, a moving bike has kinetic energy, and a hot cup has thermal energy.",
    avoid=("bill", "bills", "electricity", "gas", "supplier", "tariff", "meter", "saving",
           "save", "tired", "sluggish", "drink", "food", "calories", "protein", "solar",
           "panel", "company", "price", "cost", "cheap"),
    ask=("what", "mean", "meaning", "explain")))

ENTRIES.append(entry(
    "temperature-what",
    (("temperature",), ("mean", "meaning", "definition", "explain", "measure",
                        "what is temperature")),
    "Temperature measures how fast the particles in something are moving: faster particles mean a "
    "higher temperature and slower ones mean a lower one. It is not the same as how much heat is "
    "stored, which is why a cup of tea and a bath can be the same temperature but hold very "
    "different amounts of heat.",
    avoid=("fever", "high", "low", "body", "baby", "child", "thermometer", "room", "oven",
           "cook", "weather", "outside", "today", "hot", "cold", "forecast"),
    ask=("what", "mean", "meaning", "explain", "measure"),
    bias=3))


ENTRIES.append(entry(
    "anger-why",
    (("angry", "anger", "rage"), ("why", "what", "cause", "causes", "get", "feel")),
    "Anger is the body's alarm at a threat or at a goal being blocked: adrenaline speeds your heart "
    "and tenses your muscles, and the emotional part of the brain reacts before the thinking part "
    "has caught up. It usually passes in minutes; slow breathing and naming what set it off help it "
    "pass sooner.",
    avoid=("always", "every day", "all the time", "my partner", "my wife", "my husband", "my kids",
           "hit", "hurt", "violent", "abuse", "depressed", "anxiety", "therapy", "counselling",
           "hungry", "hunger", "hangry", "snappy", "stopped eating"),
    ask=("why", "what", "get", "feel")))

ENTRIES.append(entry(
    "water-wet",
    (("water",), ("wet", "why", "what")),
    "Water is wet because it clings to surfaces and spreads across them instead of beading up: its "
    "molecules stick to each other and to most things, so a thin film stays on your skin. Wetness "
    "is that film, not a property of the water on its own.",
    # A domestic water problem is not a question about what wetness is, and "why is my hot water
    # cold", "why is my cold water warm" and "why is my heating not warming the water" were all
    # answered with the film-of-water explanation. The temperature words are what those lines
    # have that "why is water wet" does not, so they are the fence.
    avoid=("floor", "carpet", "bed", "washing", "laundry", "leak", "pipe", "boiler", "bottle",
           "drink", "pool", "swim", "rain", "garden", "plant", "kettle", "tap", "bill", "meter",
           "softener", "filter", "blue", "green", "boil", "boils", "freeze", "freezes", "salty",
           "taste", "tastes", "hard", "soft", "sea", "hot", "cold", "warm", "lukewarm", "tepid",
           "heating", "cylinder", "immersion", "combi", "radiator", "radiators", "shower", "bath",
           "temperature", "thermal store", "mixing valve", "pressure"),
    ask=("why", "wet")))


# --- the words a school science lesson starts with ---------------------------
# These are asked as "what is X" by people who want the idea, not a revision plan.
# Each one names its own thing in the key; the neighbouring cards (periodic table,
# compound interest, acid rain, magnets, speed of light) keep their questions by
# naming what they are about in avoid.

ENTRIES.append(entry(
    "molecule-what",
    (("molecule", "molecules"), ("what", "mean", "meaning", "definition", "explain", "made")),
    "A molecule is two or more atoms joined together: two hydrogen atoms and one oxygen make a "
    "water molecule, and DNA is a very long one. The atoms can be the same, as in oxygen gas, or "
    "different, as in water.",
    avoid=("mole", "moles", "skin", "spot", "spots"),
    ask=("what", "mean", "definition", "explain")))

ENTRIES.append(entry(
    "element-what",
    (("element", "elements"), ("what", "mean", "meaning", "definition", "explain",
                              "chemistry", "periodic")),
    "An element is a substance made of just one kind of atom: gold, oxygen and carbon are "
    "elements, and there are 118 known. A chemical reaction can join elements to other elements, "
    "but it cannot split one element into a simpler substance.",
    avoid=("element of surprise", "in my element", "out of my element", "heating element",
           "element of risk", "the element"),
    ask=("what", "mean", "definition", "explain"),
    bias=1))

ENTRIES.append(entry(
    "compound-what",
    (("compound", "compounds"), ("what", "mean", "meaning", "definition", "explain",
                                "chemistry", "made")),
    "A compound is two or more different elements chemically joined in fixed proportions: water "
    "is hydrogen and oxygen, and table salt is sodium and chlorine. Unlike a mixture, the elements "
    "in a compound cannot be separated just by filtering or boiling.",
    # compound interest is money, not chemistry
    avoid=("interest", "money", "savings", "save", "loan", "bank", "rate", "mortgage",
           "invest", "fracture"),
    ask=("what", "mean", "definition", "explain"),
    bias=4))

ENTRIES.append(entry(
    "chemical-reaction-what",
    (("chemical reaction", "chemical reactions", "chemical change", "chemical changes"),
     ("what", "mean", "meaning", "definition", "explain", "happen", "example")),
    "A chemical reaction is when substances rearrange their atoms to make new ones: bonds break, "
    "new bonds form, and the starting materials are used up. Burning, rusting, baking and "
    "digestion are all reactions, and they usually give out or take in heat.",
    avoid=("periodic table", "element", "atom", "lab report", "experiment", "school"),
    ask=("what", "mean", "explain"),
    bias=1))

ENTRIES.append(entry(
    "acid-what",
    (("acid", "acids", "acidic"), ("what", "mean", "meaning", "definition", "explain",
                                  "strong", "weak", "ph")),
    "An acid is a substance that releases hydrogen ions when it dissolves in water: it tastes "
    "sour, turns blue litmus red, and reacts with a base to make a salt and water. Vinegar, lemon "
    "juice and stomach acid are weak acids; car battery acid is strong.",
    avoid=("rain", "heartburn", "reflux", "indigestion", "stomach", "battery", "lsd", "trip",
           "amino", "fatty", "folic", "uric", "acid house"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "base-chemistry",
    (("base", "bases", "alkali", "alkalis", "alkaline"),
     ("what", "mean", "meaning", "definition", "explain", "chemistry", "acid", "ph")),
    "A base is the opposite of an acid: it takes hydrogen ions, turns red litmus blue, and reacts "
    "with an acid to make a salt and water. An alkali is a base that dissolves in water, such as "
    "baking soda or bleach.",
    avoid=("military", "army", "navy", "air force", "baseball", "database", "home base",
           "touch base", "base rate", "customer base", "tax base", "knowledge base",
           "base camp", "london", "manchester", "birmingham", "office", "hotel", "city",
           # a make-up base is a primer, and a number base is maths, not chemistry
           "make up", "makeup", "foundation", "primer", "concealer", "in maths", "maths",
           "math", "logarithm",
           # and a base built of concrete is a building job, not a chemistry one: "what concrete
           # for a shed base" was answered with what a base is in chemistry
           "concrete", "cement", "mortar", "ballast", "postcrete", "shed", "shed base",
           "sheds", "patio", "footing", "footings", "slab", "slabs", "drive", "driveway",
           "brick", "bricks", "garden wall", "retaining wall", "damp course"),
    ask=("what", "mean", "definition", "explain"),
    bias=3))

ENTRIES.append(entry(
    "magnetism-what",
    (("magnetism", "magnetic field", "magnetic force"),
     ("what", "mean", "meaning", "definition", "explain", "work", "works")),
    "Magnetism is the force a magnet exerts on other magnets and on iron, nickel and cobalt, "
    "carried by a magnetic field around the magnet. Like poles repel and opposite poles attract, "
    "and a compass needle is a tiny magnet lining up with Earth's field.",
    avoid=("fridge", "freezer", "seal", "strip", "door", "phone", "card", "train",
           # the hospital question wants the MRI, not the definition
           "mri", "scan", "scans", "hospital", "hospitals"),
    ask=("what", "mean", "explain"),
    bias=2))

ENTRIES.append(entry(
    "sound-what",
    (("sound", "sound wave", "sound waves"),
     ("what", "mean", "meaning", "definition", "explain", "made", "cause", "hear")),
    "Sound is a pressure wave travelling through air, water or a solid: something vibrates, "
    "pushes the particles next to it, and the push travels outwards. It cannot cross a vacuum, "
    "and it goes faster through water and solids than through air.",
    avoid=("alarm", "smoke alarm", "notification", "ringtone", "keyboard", "video call",
           "speaker", "speakers", "headphones", "tv", "telly", "loud", "quiet", "noise",
           "like", "sounds like", "safe and sound", "soundproof", "sound bar", "soundbar",
           "travel", "travels", "speed", "through", "vacuum", "hearing", "ear", "ears",
           # sound proofing is a building job, not the definition of sound
           "proof", "proofing", "sound proof"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "light-what",
    (("light", "visible light"),
     ("what", "mean", "meaning", "definition", "explain", "made", "nature", "particle",
      "wave", "photon")),
    "Light is a form of energy that travels as a wave and also as particles called photons, at "
    "about 300,000 km a second in a vacuum. It carries colour, lets us see, and is only a tiny "
    "part of the electromagnetic spectrum.",
    avoid=("speed", "how fast", "fast", "travel", "houseplant", "plant", "window", "windowsill",
           "bulb", "bulbs", "lamp", "switch", "fitting", "traffic", "light blue", "light meal",
           "light headed", "lightheaded", "blocking", "sunlight", "year", "years",
           "light year", "light years", "how far", "distance", "far", "away", "long",
           # a light in a room is a lamp or a fitting
           "kitchen", "bathroom", "hall", "hallway", "ceiling", "bedside", "fairy lights",
           "christmas lights",
           # "something light for dinner, im watching what i eat" is about a meal, and it carries
           # "what", which is one of this row's two key parts: the eating words are what tell the
           # two senses of the same word apart.
           "dinner", "dinners", "lunch", "lunches", "supper", "breakfast", "meal", "meals",
           "diet", "calorie", "calories", "eating", "im watching what i eat",
           # a light on a car's dash is the fault it warns about, and the cars table answers it:
           # "what does the engine light mean" was answered with photons travelling at 300,000 km
           # a second. The words below are the ones that make the light a warning light.
           "engine", "engine light", "warning light", "warning lights", "dashboard",
           "dash light", "on the dash", "on my dash", "headlight", "headlights",
           "brake light", "brake lights", "mot",
           # the same for the other lights on a dash, which people ask about by the system they
           # warn about rather than with the words "warning" or "engine": "what does the oil
           # pressure light mean" kept the photons because none of the words above was in it
           "oil", "oil light", "oil pressure", "pressure light", "coolant", "temperature light",
           "battery light", "abs light", "airbag light", "glow plug", "dpf light", "warning",
           "traction light", "handbrake light", "dipped beam", "indicator", "indicators"),
    ask=("what", "mean", "definition", "explain"),
    bias=4))

ENTRIES.append(entry(
    "force-what",
    (("force", "forces"), ("what", "mean", "meaning", "definition", "explain", "physics",
                          "newton", "newtons")),
    "A force is a push or a pull that can change an object's speed, direction or shape, measured "
    "in newtons. Gravity, friction and the push of a hand are all forces, and an object with no "
    "net force keeps doing what it was doing.",
    avoid=("air force", "workforce", "work force", "police force", "force of habit",
           "force quit", "force close", "force stop", "by force", "task force",
           "driving force", "armed forces", "labour force", "labor force", "sales force",
           # force majeure is a contract clause
           "majeure"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "pressure-what",
    (("pressure",), ("what", "mean", "meaning", "definition", "explain", "physics",
                     "measure", "measured", "formula")),
    "Pressure is force spread over an area: the same push on a smaller area gives a higher "
    "pressure, which is why a knife cuts and a wide boot does not sink into snow. It is measured "
    "in pascals, and in a fluid it rises with depth.",
    avoid=("blood pressure", "blood", "peer pressure", "pressure washer", "washer", "tyre",
           "tire", "water pressure", "gas pressure", "boiler", "tap", "shower", "time pressure",
           "under pressure", "pressure to", "high pressure", "low pressure", "pension",
           "cooker", "headache", "behind my eyes", "ear", "ears", "pan",
           # a definition is not a thing to do: "what should i do about it" after a boiler
           # that keeps dropping was reading "pressure" out of memory and explaining pascals
           "do about", "what should i do", "what shud i do", "fix", "fault", "keeps dropping",
           "keeps droppin", "droppin", "dropin", "dropping"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "density-what",
    (("density",), ("what", "mean", "meaning", "definition", "explain", "measure",
                    "measured", "formula", "water")),
    "Density is how much mass is packed into a volume: a block of iron and a block of foam the "
    "same size have very different densities. Water has a density of about 1 kg per litre, which "
    "is why things less dense than water float.",
    avoid=("population", "housing", "traffic", "urban", "city", "cities", "bone", "breast"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "wave-what",
    (("wave", "waves"), ("what", "mean", "meaning", "definition", "explain", "physics",
                         "type", "types")),
    "A wave is a moving disturbance that carries energy without carrying the material with it: a "
    "sound wave is air particles pushing and pulling, and a water wave is the surface moving up "
    "and down while the water stays roughly in place. Light is a wave too, and so is a radio "
    "signal.",
    avoid=("wave to", "wave goodbye", "heat wave", "heatwave", "wave of", "new wave",
           "microwave", "tsunami", "tidal wave", "shock wave", "crime wave", "wave at",
           "hand", "flag", "hello", "goodbye", "hair", "curls", "curly", "perm", "permanent",
           "straighteners", "straightener"),
    ask=("what", "mean", "definition", "explain"),
    bias=3))

ENTRIES.append(entry(
    "star-what",
    (("star", "stars"), ("what", "mean", "meaning", "definition", "explain", "made",
                        "how", "formed")),
    "A star is a huge ball of gas held together by gravity, with fusion in its core turning "
    "hydrogen into helium and giving out light and heat. The Sun is the nearest star, and stars "
    "look small only because they are very far away.",
    avoid=("sign", "signs", "horoscope", "zodiac", "wars", "trek", "movie", "film", "pop",
           "rock", "football", "rating", "ratings", "review", "reviews", "five star",
           "5 star", "star of", "lucky", "shooting", "falling", "twinkle",
           "north star", "how many", "count", "night", "sky"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "ecosystem-what",
    (("ecosystem", "ecosystems", "eco system", "eco systems"),
     ("what", "mean", "meaning", "definition", "explain", "example")),
    "An ecosystem is a community of living things plus the non-living parts they depend on - "
    "soil, water, air and sunlight - interacting in one place. A pond, a woodland and a garden "
    "are ecosystems, and they work because energy flows through them and materials are recycled.",
    avoid=("business", "digital", "startup", "start up", "company", "app", "software"),
    ask=("what", "mean", "definition", "explain"),
    bias=1))

ENTRIES.append(entry(
    "natural-selection-what",
    (("natural selection",), ("what", "mean", "meaning", "definition", "explain", "work",
                            "works", "how", "evolution")),
    "Natural selection is how evolution works: individuals vary, the ones whose variations suit "
    "their surroundings have more surviving young, and those variations become common over "
    "generations. It is not a plan or a choice - the environment simply filters what is already "
    "there.",
    avoid=("selection box", "select", "choose", "chosen", "job", "team", "school"),
    ask=("what", "mean", "explain"),
    bias=1))
ENTRIES.append(entry(
    "light-year",
    (("light year", "light years", "lightyear", "lightyears", "light-year"),
     ("what", "how far", "distance", "long", "far", "mean", "meaning", "explain", "measure",
      "many", "km", "kilometres", "kilometers", "miles")),
    "A light year is a distance, not a time: it is how far light travels in a year, about 9.46 "
    "trillion kilometres (5.88 trillion miles). Proxima Centauri, the nearest star after the Sun, "
    "is about 4.2 light years away, and the Milky Way is about 100,000 light years across.",
    avoid=("how fast", "speed", "travel at", "wavelength", "per second", "last year", "this year",
           "next year", "new year"),
    ask=("what", "how far", "distance", "long", "far", "mean", "explain", "measure", "many")))

ENTRIES.append(entry(
    "electric-current",
    (("electric current", "electrical current", "current electricity", "amps", "amperes",
      "ampere", "electric flow"),
     ("what", "mean", "meaning", "definition", "explain", "flow", "measure", "measured", "unit",
      "how")),
    "An electric current is the flow of electric charge: in a wire, electrons drift along and carry "
    "energy from the battery or the mains to whatever is using it. It is measured in amperes (amps), "
    "and a current only flows round a complete circuit.",
    avoid=("account", "bank", "mortgage", "job", "address", "partner", "temperature", "weather",
           "news", "bill", "bills", "tariff", "supplier", "price", "cost", "cheap", "saving"),
    ask=("what", "mean", "definition", "explain", "flow", "measure", "unit", "how")))

ENTRIES.append(entry(
    "electric-shock",
    (("electric shock", "electrical shock", "electrocuted", "electrocution",
      "electricity shock", "electricity shocks", "shock from the socket",
      "shock from the wire", "shock from the plug"),
     ("what", "why", "cause", "get", "happen", "happens", "electricity", "electric", "live",
      "wire", "socket", "plug", "mains", "body")),
    "An electric shock happens when your body becomes part of a circuit: touching something live "
    "lets current flow through you to the ground, and it is the current, not the voltage alone, "
    "that does the harm. Switch the power off at the mains before touching anyone who is still "
    "connected, and call the emergency services if they are unconscious or burned.",
    avoid=("surprise", "surprised", "news", "anaphylactic", "allergic", "bill", "bills",
           "price", "cost", "bleeding", "unconscious", "collapse", "collapsed", "pale",
           "fainting"),
    ask=("what", "why", "cause", "get", "happen", "electricity", "electric", "live", "wire",
         "socket", "plug", "mains")))

ENTRIES.append(entry(
    "gene-what",
    (("gene", "genes", "genetic code"),
     ("what", "mean", "meaning", "definition", "explain", "work", "works", "do", "does", "make",
      "made", "for", "inherit", "inherited")),
    "A gene is a section of DNA that holds the instructions for making one thing the body needs, "
    "usually a protein: eye colour, blood type and how a muscle works all come from genes. You "
    "inherit half your genes from each parent, and they switch on and off depending on the cell.",
    avoid=("jeans", "denim", "trousers", "genealogy", "family tree", "test", "testing", "cancer",
           "brca", "crispr", "edit", "editing", "therapy"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "blood-types",
    (("blood type", "blood types", "blood group", "blood groups"),
     ("what", "why", "have", "different", "mean", "which", "compatible", "compatibility",
      "transfusion", "donor", "negative", "positive", "rhesus", "rh")),
    "Blood types come from markers on the surface of red blood cells: the ABO system gives A, B, AB "
    "or O, and the rhesus factor adds positive or negative. Your type is inherited, and it matters "
    "for transfusions because the immune system attacks markers it does not recognise; O negative is "
    "the universal red-cell donor, and only a blood test can tell you yours.",
    avoid=("blood pressure", "blood test", "blood in", "blood clot", "period", "donate", "donation",
           "give blood", "needle", "needles"),
    ask=("what", "why", "have", "different", "mean", "which", "compatible", "transfusion",
         "donor")))

ENTRIES.append(entry(
    "cholesterol-what",
    (("cholesterol",), ("what is", "what's", "mean", "meaning", "definition", "explain",
                        "is cholesterol")),
    "Cholesterol is a waxy fat the body needs for cell walls and hormones, and the liver makes most "
    "of it; the rest comes from food. The number that matters most is the LDL ('bad') part, which can "
    "clog arteries, and diet, exercise and sometimes a statin bring it down.",
    avoid=("lower", "reduce", "bring down", "high", "diet", "food", "foods", "eat", "avoid", "help",
           "statin", "statins", "hdl", "ldl", "triglycerides", "level", "levels", "number"),
    ask=("what is", "what's", "mean", "meaning", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "brain-what",
    (("brain", "brains"), ("how", "work", "works", "what", "does", "do", "function", "parts")),
    "The brain is a network of about 86 billion nerve cells that talk to each other through "
    "electrical and chemical signals. Different regions handle different jobs - movement, sight, "
    "language, emotion and memory - and the connections between them are what let you think, learn "
    "and remember; it runs on about 20 percent of the body's energy.",
    avoid=("study", "studying", "revise", "revision", "exam", "exams", "memorise", "memorize",
           "remember", "forget", "forgetting", "learn", "learning", "memory", "dementia",
           "alzheimers", "alzheimer's", "injury", "tumour", "tumor", "stroke", "concussion"),
    ask=DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "memory-what",
    (("memory",), ("what", "how", "work", "works", "mean", "meaning", "definition", "explain",
                   "stored", "store", "made")),
    "Memory is not one store: short-term memory holds a handful of things for seconds, and long-term "
    "memory is a web of connections between neurons that gets stronger each time you recall it. "
    "Sleep and repetition file it away, and forgetting details is normal - the brain keeps the gist "
    "and drops the rest.",
    avoid=("forget", "forgetting", "forgot", "remember", "remembering", "memorise", "memorize",
           "study", "exam", "my mum", "my dad", "dementia", "alzheimers", "alzheimer's", "loss",
           "losing", "improve", "better", "card", "cards", "ram", "phone", "computer"),
    ask=DEFINITION_ASK,
    bias=2))

# The next words of a science lesson: states of matter, living things and body chemistry.
# Each key names its own subject; the everyday cards that share the word (gas bill, organ
# donor, rock music, mineral water, low carb) keep their lines through avoid.
ENTRIES.append(entry(
    "mixture-what",
    (("mixture", "mixtures"), ("what", "mean", "meaning", "definition", "explain", "example")),
    "A mixture is two or more substances together that are not chemically joined, so each keeps "
    "its own properties: sand and salt, or air, are mixtures. You can usually separate a mixture "
    "by filtering, sieving or boiling, which you cannot do with a compound.",
    avoid=("cake", "cooking", "recipe", "concrete", "cement", "mortar", "trail mix", "nuts",
           "dj", "djing", "music", "playlist", "track", "song", "set"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "solution-what",
    (("solution", "solutions"), ("what", "mean", "meaning", "definition", "explain",
                                "chemistry", "made")),
    "A solution is a mixture where one substance dissolves in another: the dissolved substance is "
    "the solute and the liquid it goes into is the solvent. Salt water and sugar water are "
    "solutions, and the dissolved part cannot be filtered out.",
    avoid=("problem", "solve", "solved", "fix", "answer", "software", "it support", "cleaning",
           "cleaner", "contact lens", "saline", "eye", "drops", "your", "maths", "math",
           "equation", "puzzle",
           # "a solution for a blocked drain" is a fix, not chemistry: the household problem
           # is what the line means, so the chemistry card stands down for it.
           "drain", "plughole", "blocked", "unblock", "squeak", "squeaky", "hinge", "leak",
           "damp", "condensation", "mould", "weeds", "weed", "stain", "limescale", "scuff",
           "crack"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "solid-what",
    (("solid", "solids"), ("what", "mean", "meaning", "definition", "explain", "state", "matter")),
    "A solid has a fixed shape and a fixed volume: its particles are packed tightly together and "
    "vibrate in place, which is why a solid keeps its shape unless something pushes or breaks it. "
    "Ice, wood and rock are solids; melting turns a solid into a liquid.",
    avoid=("solid wood", "solid food", "solid fuel", "solid tumour", "solid state drive",
           "solid oak", "solid pine", "solid door", "solid wall", "solid ground", "solid start"),
    ask=("what", "mean", "definition", "explain", "state"),
    bias=2))

ENTRIES.append(entry(
    "liquid-what",
    (("liquid", "liquids"), ("what", "mean", "meaning", "definition", "explain", "state",
                            "matter")),
    "A liquid has a fixed volume but takes the shape of its container: its particles are close "
    "enough to stick together but free to slide past each other. Water, milk and oil are liquids; "
    "heating a liquid enough turns it into a gas.",
    avoid=("liquid diet", "liquid soap", "liquid nitrogen", "liquid oxygen", "liquid gold",
           "liquid lunch", "liquid asset", "liquid cash", "liquid damage", "liquid food"),
    ask=("what", "mean", "definition", "explain", "state"),
    bias=2))

ENTRIES.append(entry(
    "gas-what",
    (("gas", "gases", "gaseous"), ("what", "mean", "meaning", "definition", "explain", "state",
                                   "matter")),
    "A gas has no fixed shape or volume: its particles are far apart and move freely, so a gas "
    "spreads out to fill whatever it is in. Air and steam are gases; cooling a gas enough turns "
    "it into a liquid.",
    avoid=("bill", "boiler", "cooker", "hob", "oven", "leak", "supplier", "meter", "heating",
           "central heating", "price", "cap", "tariff", "cylinder", "canister", "bottle",
           "nitrogen", "oxygen", "laughing gas", "tear gas", "gaslight", "gas fire", "gas safe",
           # "what gas mark do i roast chicken at" is the oven's question, not what a gas is:
           # the word "gas" plus the word "what" fitted this row exactly, and a chat's first
           # line has no talk to stand the reading down (jade-easel on #5548)
           "gas mark", "roast", "roasting", "bake", "baking", "grill", "grilling", "cook",
           "cooking", "oven temperature"),
    ask=("what", "mean", "definition", "explain", "state"),
    bias=2))

ENTRIES.append(entry(
    "organ-what",
    (("organ", "organs"), ("what", "mean", "meaning", "definition", "explain", "body", "job")),
    "An organ is a part of the body made of several tissues working together for one job: the "
    "heart pumps blood, the lungs take in oxygen and the liver cleans the blood. Your skin is the "
    "largest organ, and organs work together in systems.",
    avoid=("donor", "donation", "transplant", "recipient", "donate", "organ recital", "church",
           "pipe organ", "mouth organ", "hammond", "musical", "music"),
    ask=("what", "mean", "definition", "explain", "body"),
    bias=2))

ENTRIES.append(entry(
    "species-what",
    (("species",), ("what", "mean", "meaning", "definition", "explain", "same", "breed")),
    "A species is a group of living things that can breed together and produce fertile young: "
    "dogs are one species, and a horse and a donkey are different species because their mule "
    "offspring cannot have young. Members of a species share most of their genes.",
    avoid=("endangered", "extinct", "extinction", "invasive", "protected", "rare", "native",
           "introduced", "alien", "conservation", "red list", "bird", "birds", "animal",
           "animals", "plant", "plants", "tree", "trees", "flower", "flowers", "fish", "insect",
           "mushroom", "identify", "this", "that"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "enzyme-what",
    (("enzyme", "enzymes"), ("what", "mean", "meaning", "definition", "explain", "do", "work")),
    "An enzyme is a protein that speeds up a chemical reaction in a living thing without being "
    "used up itself: amylase in saliva starts breaking down starch, and lactase splits milk "
    "sugar. Each enzyme fits only the substance it acts on, like a key in a lock.",
    avoid=("cleaner", "washing", "detergent", "laundry", "drain", "bio", "powder", "tablet",
           "supplement", "digestive", "digestive enzyme", "bromelain"),
    ask=("what", "mean", "definition", "explain", "do"),
    bias=2))

ENTRIES.append(entry(
    "hormone-what",
    (("hormone", "hormones"), ("what", "mean", "meaning", "definition", "explain", "do", "work")),
    "A hormone is a chemical messenger made by a gland and carried in the blood to switch "
    "something on or off somewhere else: insulin tells cells to take up sugar, and adrenaline "
    "gets the body ready for action. Small amounts can have big effects, and each hormone only "
    "acts on cells that can receive it.",
    avoid=("therapy", "treatment", "imbalance", "hrt", "testosterone", "oestrogen", "estrogen",
           "growth hormone", "thyroid", "menopause", "contraceptive", "replacement"),
    ask=("what", "mean", "definition", "explain", "do"),
    bias=2))

ENTRIES.append(entry(
    "carbohydrate-what",
    (("carbohydrate", "carbohydrates", "carbs"), ("what", "mean", "meaning", "definition",
                                                 "explain", "are", "do")),
    "Carbohydrates are one of the main food groups: sugars and starches that the body breaks "
    "down into glucose for energy. Bread, rice, pasta, potatoes, fruit and sugar are "
    "carbohydrates, and fibre is a carbohydrate the body cannot digest.",
    avoid=("low carb", "low-carb", "cut carbs", "cutting carbs", "count", "counting", "keto",
           "grams", "how many", "diet", "lose weight", "weight loss", "no carb"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "mineral-what",
    (("mineral", "minerals"), ("what", "mean", "meaning", "definition", "explain", "made",
                               "rock")),
    "A mineral is a natural solid with a definite chemical make-up and a crystal structure, "
    "formed in the earth without anything living making it: quartz, calcite and iron ore are "
    "minerals. A rock is usually a mixture of minerals.",
    avoid=("vitamin", "vitamins", "supplement", "supplements", "deficiency", "water", "drink",
           "food", "diet", "intake", "iron", "calcium", "zinc", "bottle", "spring", "spa"),
    ask=("what", "mean", "definition", "explain"),
    bias=3))

ENTRIES.append(entry(
    "rock-what",
    (("rock", "rocks"), ("what", "mean", "meaning", "definition", "explain", "made", "type")),
    "A rock is a solid piece of the earth made of one or more minerals: granite is mostly quartz "
    "and feldspar, and limestone is mostly calcite. Rocks come in three kinds - igneous from "
    "cooled magma, sedimentary from settled layers, and metamorphic changed by heat and pressure.",
    avoid=("music", "band", "concert", "gig", "album", "song", "rock star", "punk", "indie",
           "climbing", "climb", "bouldering", "cake", "bun", "on the rocks", "rock bottom",
           "rock salt", "rock pool", "rockery", "garden"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "habitat-what",
    (("habitat", "habitats"), ("what", "mean", "meaning", "definition", "explain", "animal",
                               "live")),
    "A habitat is the place where a plant or animal lives, with the food, water, shelter and "
    "space it needs: a hedge is a habitat for sparrows, and a pond is one for frogs. Different "
    "species are suited to different habitats, and losing a habitat is the biggest threat to "
    "many of them.",
    avoid=("loss", "destruction", "destroy", "destroying", "restore", "restoration", "create",
           "creating", "garden", "pond", "hedge", "wildlife", "project"),
    ask=("what", "mean", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "predator-what",
    (("predator", "predators"), ("what", "mean", "meaning", "definition", "explain", "animal",
                                 "eat")),
    "A predator is an animal that hunts and eats other animals: a fox, an owl and a lion are "
    "predators, and the animals they eat are their prey. Predators keep prey numbers in check, "
    "which is why removing them can upset a whole habitat.",
    avoid=("child", "children", "kid", "kids", "online", "sexual", "grooming", "groomer",
           "drone", "tank", "fish tank", "aquarium", "game", "film", "movie", "alien"),
    ask=("what", "mean", "definition", "explain", "animal"),
    bias=2))

ENTRIES.append(entry(
    "protein-what",
    (("protein", "proteins"), ("what", "mean", "meaning", "definition", "explain", "made",
                               "body", "do")),
    "Protein is a building material made of chains of amino acids: the body uses it to build and "
    "repair muscle, skin, hair and organs, and enzymes are proteins too. Meat, fish, eggs, milk, "
    "beans, lentils, nuts and tofu are good sources.",
    avoid=("how much", "much protein", "grams", "need", "needed", "daily", "day", "powder",
           "shake", "whey", "supplement", "diet", "lose", "weight", "build muscle",
           "vegan", "vegetarian", "deficiency", "kidney", "uric",
           # "what should i eat for protein" asks for food and got the definition, because this
           # row keys the bare "what". A line about eating, a meal or a shop is the food list's
           # question (cooking_entries.py, the `protein` row), not this one's.
           "eat", "eats", "eating", "food", "foods", "meal", "meals", "breakfast", "lunch",
           "dinner", "snack", "snacks", "shop", "shopping", "cook", "cooking", "recipe",
           "recipes", "high in protein", "protein rich", "protein-rich", "source", "sources"),
    ask=("what", "mean", "definition", "explain"),
    bias=3))

ENTRIES.append(entry(
    "vaccine-what",
    (("vaccine", "vaccines", "vaccination", "jab"), ("what", "mean", "meaning", "definition",
                                                    "explain", "work", "do")),
    "A vaccine teaches the immune system to recognise a germ without you having to get the "
    "illness: it shows a harmless part or a weakened version, and the body makes antibodies and "
    "memory cells ready for the real thing. That protection usually takes a few weeks and may "
    "need boosters.",
    avoid=("safe", "safety", "side effect", "side effects", "should i", "should my", "child",
           "children", "baby", "flu", "travel", "pregnant", "autism", "reaction", "passport",
           "certificate", "booster", "booking", "appointment", "nhs"),
    ask=("what", "mean", "definition", "explain"),
    bias=3))

ENTRIES.append(entry(
    "vitamin-what",
    (("vitamin", "vitamins"), ("what", "mean", "meaning", "definition", "explain", "do",
                               "body")),
    "A vitamin is a nutrient the body needs in small amounts and cannot make enough of, so it "
    "has to come from food: vitamin C is in fruit and vegetables, vitamin A in carrots and dairy, "
    "and vitamin D is made in skin from sunlight. A varied diet usually covers them.",
    avoid=("should i", "take", "supplement", "supplements", "deficiency", "deficient", "d3",
           "b12", "vitamin d", "vitamin c", "vitamin b", "folic", "prenatal", "pregnant",
           "child", "baby", "daily", "dose", "tablet", "chewable"),
    ask=("what", "mean", "definition", "explain"),
    bias=3))

ENTRIES.append(entry(
    "metal-what",
    (("metal", "metals"), ("what", "mean", "meaning", "definition", "explain", "made",
                           "properties")),
    "A metal is an element that conducts heat and electricity, is usually shiny, and can be "
    "bent or hammered into shape without breaking: iron, copper, aluminium and gold are metals. "
    "Most elements are metals, and they sit on the left and middle of the periodic table.",
    avoid=("cold", "colder", "taste", "tastes", "detector", "detecting", "recycle", "recycling",
           "scrap", "scrapyard", "precious", "heavy metal", "band", "music", "concert", "gig",
           "roof", "roofing", "sheet", "fence", "gate", "rust", "rusty", "alloy"),
    ask=("what", "mean", "definition", "explain"),
    bias=3))

# --- digestion, electricity and light: the words that also have an everyday sense ----------
# These seven are the school definitions, and every one of them is a word a person also uses for
# something else: indigestion, a car battery's voltage, a circuit that trips, the conductor on a
# train, loft insulation, shadows under the eyes, and a written reflection. The `avoid` list is
# the everyday sense; the `ask` is the school question, so a fault or a bill keeps its own row.
ENTRIES.append(entry(
    "digestion-what",
    (("digestion", "digestive system", "digest", "digests", "digesting"),
     ("what", "how", "work", "works", "process", "happen", "happens", "mean", "definition",
      "explain", "stomach", "gut", "body")),
    "Digestion is how the body breaks food into pieces small enough to absorb: chewing and stomach "
    "acid start it, enzymes in the small intestine split carbohydrates into sugars, proteins into "
    "amino acids and fats into fatty acids, and the nutrients pass through the gut wall into the "
    "blood. The whole trip usually takes six to eight hours, and fibre and water keep it moving.",
    avoid=("indigestion", "heartburn", "reflux", "acid reflux", "bloating", "constipation",
           "diarrhoea", "diarrhea", "stomach ache", "stomach pain", "ibs", "food poisoning",
           "ulcer", "vomit", "vomiting", "nausea", "medicine", "medication", "tablet", "tablets",
           "supplement", "probiotic", "fibre supplement", "laxative", "news", "book", "books",
           "email", "emails", "information", "read", "reading", "report", "reports", "article",
           "biscuit", "biscuits"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "voltage-what",
    (("voltage", "volt", "volts", "potential difference"),
     ("what", "how", "mean", "meaning", "definition", "explain", "measure", "measured", "unit",
      "difference", "work")),
    "Voltage is the push that makes electric charge move: it is the difference in electrical energy "
    "between two points, measured in volts (V), and one volt gives one joule of energy to each "
    "coulomb of charge that passes. A AA battery is 1.5 volts and the mains is about 230 volts in "
    "the UK; current is how much charge flows, voltage is how hard it is pushed.",
    avoid=("car", "cars", "battery", "batteries", "charger", "charging", "phone", "laptop",
           "mains", "wiring", "wire", "shock", "electric shock", "fuse", "socket", "plug"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "watt-what",
    (("watt", "watts", "kilowatt", "kilowatts", "kw", "kwh", "kilowatt hour",
      "kilowatt-hour"),
     ("what", "how", "mean", "meaning", "definition", "explain", "many", "much", "difference",
      "work", "unit", "measure")),
    "A watt is a rate of energy use: one watt is one joule every second, so a 10-watt LED left on "
    "for 100 hours uses one kilowatt-hour, and a unit on your electricity bill is exactly that. "
    "Watts are volts times amps, which is why a 2,400-watt kettle on 230 volts pulls about 10 "
    "amps. A kilowatt is 1,000 watts, and a kWh is a kilowatt for an hour - the number the meter "
    "counts, not the number on the label.",
    avoid=("car", "cars", "battery", "batteries", "charger", "charging", "phone", "laptop",
           "wiring", "wire", "shock", "fuse", "socket", "plug", "boiler", "heater", "bulb",
           "light bulb", "microwave", "kettle"),
    ask=DEFINITION_ASK + ("how many", "how much", "what is a", "whats a", "in a kilowatt",
                          "per hour")))

ENTRIES.append(entry(
    "circuit-what",
    (("circuit", "circuits", "electrical circuit", "electric circuit"),
     ("what", "how", "work", "works", "mean", "meaning", "definition", "explain", "complete",
      "closed", "open", "series", "parallel")),
    "An electric circuit is a complete loop that charge can flow round: a source such as a battery "
    "pushes current out through a wire, through a component such as a bulb, and back to the source. "
    "Break the loop with a switch and the current stops; in a series circuit everything shares one "
    "path, and in a parallel circuit each branch has its own.",
    avoid=("workout", "exercise", "training", "gym", "court", "judge", "legal", "appeal",
           "board", "boards", "soldering", "repair", "repairs", "fuse", "fuse box", "breaker",
           "trips", "tripping", "keeps tripping", "socket", "socket keeps", "light", "lights",
           "short circuit", "short-circuit", "shorts", "electrics", "electrician"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "conductor-what",
    (("conductor", "conductors", "electrical conductor", "electric conductor", "thermal conductor"),
     ("what", "how", "why", "mean", "meaning", "definition", "explain", "electricity", "heat",
      "material", "materials", "metal", "metals", "copper", "good")),
    "A conductor is a material that lets heat or electricity pass through it easily because some of "
    "its electrons are free to move. Metals are the usual conductors - copper and aluminium carry "
    "current in wires, and a metal pan conducts heat - while materials that hold their electrons "
    "tightly, such as rubber and plastic, are insulators.",
    avoid=("train", "trains", "rail", "railway", "ticket", "tickets", "fare", "orchestra",
           "symphony", "music", "band", "choir", "bus", "driver", "inspector", "concert"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "insulator-what",
    (("insulator", "insulators", "electrical insulator", "thermal insulator", "insulation"),
     ("what", "how", "why", "mean", "meaning", "definition", "explain", "electricity", "heat",
      "material", "materials", "good", "plastic", "rubber", "keeps")),
    "An insulator is a material that does not let heat or electricity pass through it easily because "
    "its electrons are not free to move. Plastic and rubber insulate electrical wires, and trapped "
    "air in foam, wool or double glazing slows heat loss; that is why a woolly jumper keeps you warm "
    "and a plastic handle lets you hold a hot pan.",
    avoid=("loft", "attic", "wall", "walls", "roof", "house", "home", "cavity", "boiler", "pipe",
           "pipes", "cost", "grant", "install", "installation", "damp", "floor", "floors",
           "garage", "conservatory", "how much"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "shadow-what",
    (("shadow", "shadows", "shadow form", "shadow made"),
     ("what", "how", "why", "make", "makes", "made", "form", "formed", "mean", "definition",
      "explain", "light", "sun", "lamp")),
    "A shadow is the patch where an object blocks light: light travels in straight lines, so an "
    "opaque object stops the rays and leaves a dark shape behind it. The shadow is biggest when the "
    "light source is close to the object and the surface is far behind, and a point of light gives a "
    "sharper edge than a wide one.",
    avoid=("eyes", "eye", "under my eyes", "dark circles", "makeup", "eyeshadow", "eye shadow",
           "face", "sunken", "tired", "panda eyes", "concealer", "cabinet", "minister",
           "government", "politics", "shadow ban", "shadowban", "five o'clock", "doubt",
           "shadow work", "therapy", "journal"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "reflection-what",
    (("reflection", "reflections", "reflect", "reflects", "reflected", "mirror", "mirrors"),
     ("what", "how", "why", "work", "works", "mean", "meaning", "definition", "explain", "light",
      "mirror", "mirrors", "water", "surface")),
    "Reflection is light bouncing off a surface: the ray hits the surface and leaves at the same "
    "angle on the other side of an imaginary line straight up from it. A smooth surface such as a "
    "mirror reflects the rays in one direction and gives a clear image; a rough surface scatters them "
    "and gives a duller, softer one.",
    avoid=("self reflection", "self-reflection", "journal", "journaling", "diary", "essay",
           "feedback", "performance", "behaviour", "behavior", "yourself", "myself", "my life",
           "how do i reflect", "write a reflection", "reflective essay", "hang", "hanging",
           "wall", "bathroom", "buy", "clean", "cleaning", "mirror cabinet", "mirror ball",
           # stopping a mirror from steaming up is the cleaning card's line: "how do i stop my
           # mirror fogging up" wants the washing-up liquid, not the angle of the ray
           "stop", "stops", "stopping", "prevent", "prevents", "fog", "fogging", "fogged",
           "foggy", "steaming up", "misted", "misty",
           # a mark on the mirror is a cleaning job on glass: "how do i get hairspray off the
           # mirror" was answered with the angle of the ray
           "hairspray", "hair spray", "toothpaste", "marks", "mark", "dirty", "smudge",
           "smudges", "washed", "washes"),
    ask=DEFINITION_ASK,
    bias=2))

# The rest of the school-science words. The file already answers enzyme, hormone, carbohydrate,
# mineral and rock; these nine - the cell, the gene, the atom and the ground - were shrugs, one by
# one, while it answered the rarer "why is the sky blue". Each is a definition ask, so it carries an
# `ask` for the asking shapes and stands down for the practical question that shares its word: a
# garden soil, a hairdryer ion, a rock band, a carbon-dated bone.
ENTRIES.append(entry(
    "osmosis-what",
    (("osmosis",), ("what", "is", "work", "works", "mean", "explain", "water")),
    "Osmosis is water moving through a thin membrane from where there is more of it to where there is "
    "less, until the two sides even out. A raisin plumps up in water and a slug shrivels in salt for "
    "the same reason: the water follows the salt. That is also how a plant's roots drink, and why a "
    "wilted lettuce leaf firms up in cold water.",
    ask=("what", "work", "works", "mean", "explain", "how"),
    bias=2))

ENTRIES.append(entry(
    "diffusion-what",
    (("diffusion",), ("what", "is", "work", "works", "mean", "explain", "spread", "spreads",
                     "smell")),
    "Diffusion is particles spreading out on their own from where there are many of them to where "
    "there are few, because they are always moving. A drop of ink colours a whole glass of water "
    "without stirring, and the smell of toast reaches the next room the same way. Warmer means "
    "faster, which is why tea brews quicker in hot water.",
    ask=("what", "work", "works", "mean", "explain", "how"),
    bias=2))

ENTRIES.append(entry(
    "neuron-what",
    (("neuron", "neurons", "nerve cell", "nerve cells", "synapse", "synapses"),
     ("what", "are", "do", "does", "work", "works", "mean", "explain")),
    "A neuron is a nerve cell: a long strand that carries an electrical pulse from one end to the "
    "other and passes it on to the next cell through a tiny gap called a synapse, using a chemical. "
    "You have around 86 billion of them, and learning is the connections between them getting "
    "stronger with use.",
    ask=("what", "are", "do", "does", "work", "works", "mean", "explain"),
    bias=2))

ENTRIES.append(entry(
    "chromosome-what",
    (("chromosome", "chromosomes"), ("what", "are", "do", "does", "many", "mean", "explain")),
    "A chromosome is one long tightly wound packet of DNA; humans have 46 of them in most cells, in "
    "23 pairs, with one of each pair from each parent. They are the filing system that lets a cell "
    "copy all its instructions without tangling them, and the sex chromosomes are the pair that "
    "decides whether you develop as male or female.",
    ask=("what", "are", "do", "does", "many", "mean", "explain"),
    bias=2))

ENTRIES.append(entry(
    "rna-what",
    (("rna",), ("what", "is", "do", "does", "mean", "explain", "dna", "differ", "difference")),
    "RNA is DNA's working copy: the same four-letter code, but single-stranded and short-lived. A "
    "cell copies the gene it needs into RNA, carries it out of the nucleus and builds a protein from "
    "it, which is why a cell can keep its DNA safe and still make what it needs. Some viruses, "
    "including the cold and flu viruses, store their instructions as RNA instead.",
    ask=("what", "is", "do", "does", "mean", "explain", "difference", "how"),
    bias=2))

ENTRIES.append(entry(
    "isotope-what",
    (("isotope", "isotopes", "radioisotope", "radioactive"), ("what", "are", "do", "mean",
                                                              "explain", "difference")),
    "Isotopes are versions of the same element with different numbers of neutrons, so the same "
    "chemistry but a different weight. Carbon-12 and carbon-14 both behave like carbon, but "
    "carbon-14 is unstable and decays at a steady rate, which is how archaeologists date old bone "
    "and wood. Some isotopes are radioactive enough to be useful in medicine and power, and some "
    "are harmless.",
    avoid=("carbon dating", "how does carbon dating", "radon", "radiotherapy", "cancer", "x-ray"),
    ask=("what", "are", "do", "mean", "explain", "difference"),
    bias=2))

ENTRIES.append(entry(
    "ion-what",
    (("ion", "ions"), ("what", "are", "do", "mean", "explain", "charge", "charged")),
    "An ion is an atom or molecule that has lost or gained electrons, which leaves it with an "
    "electrical charge. Table salt is sodium ions and chloride ions held together by that charge, "
    "and the ions in seawater are what make it conduct electricity. Your nerves and muscles work by "
    "shuffling ions in and out through their membranes.",
    ask=("what", "are", "do", "mean", "explain", "charge", "charged", "how"),
    bias=2))

ENTRIES.append(entry(
    "catalyst-what",
    (("catalyst", "catalysts", "catalyse", "catalyze", "catalysis"),
     ("what", "do", "does", "mean", "explain", "work", "works")),
    "A catalyst speeds up a reaction and comes out of it unchanged, so a small amount does the job "
    "over and over. It works by giving the molecules an easier route, which means the reaction can "
    "happen at a lower temperature. Enzymes are nature's catalysts and the catalytic converter on a "
    "car uses metals to turn exhaust fumes into less harmful gases.",
    ask=("what", "do", "does", "mean", "explain", "work", "works"),
    bias=2))

ENTRIES.append(entry(
    "soil-what",
    (("soil",), ("what", "is", "made", "mean", "explain", "difference", "form", "formed")),
    "Soil is crushed rock mixed with rotted plant and animal matter, plus air, water and a vast "
    "number of microbes. The rotted part, humus, is what holds water and feeds plants, and it takes "
    "hundreds of years to build up an inch of it. A handful of healthy soil has more living things in "
    "it than there are people on Earth.",
    avoid=("garden", "plant", "plants", "pot", "pots", "compost", "clay", "sandy", "chalk",
           # "soil for a hydrangea" and "what soil do hydrangeas need" are recommendation
           # questions about a plant, not what soil is, and bias 2 here beat the plant rows on
           # every one of them
           "for", "need", "needs", "should", "best", "good", "want", "wants",
           "improve", "test", "ph", "mulch", "border", "lawn", "veg", "vegetable", "seed",
           "sow", "grow", "dig", "weed",
           # my soil, this soil: a complaint about the ground in a garden is a garden question
           "my soil", "the soil", "this soil", "dry", "wet", "soggy", "poor", "acid", "alkaline",
           # a process that happens to soil is a different question from what soil is
           "erosion", "eroded", "pollution", "polluted"),
    ask=("what", "is", "made", "mean", "explain", "difference", "form", "formed"),
    bias=2))

# --- the animal classes, the sky, and the water cycle -------------------------
# These are the first definitions a school lesson asks for, and main shrugged at all of them.
# Each one is a definition only: "what is a fish" is this row, while "my fish is sick" and
# "what is a fish tank" are not, which is what the ask and the avoid list are for.

ENTRIES.append(entry(
    "mammal-what",
    (("mammal", "mammals", "mammalian"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "animal",
      "animals", "science", "warm", "fur", "milk")),
    "A mammal is a warm-blooded animal with a backbone that has hair or fur and feeds its young on "
    "milk. Almost all give birth to live young rather than laying eggs, and they keep a steady body "
    "temperature - which is why a whale is a mammal even though it lives in the sea, and a bat is "
    "one even though it flies.",
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "reptile-what",
    (("reptile", "reptiles", "reptilian"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "animal",
      "animals", "science", "cold", "scales", "eggs")),
    "A reptile is a cold-blooded animal with a backbone and dry, scaly skin. It cannot keep its own "
    "body temperature, so it warms up in the sun, and most lay leathery eggs on land - lizards, "
    "snakes, turtles and crocodiles are the groups.",
    avoid=("brain", "lizard brain", "alien", "aliens", "person", "people",
           "house", "reptile house", "zoo", "vivarium", "pet shop", "enclosure"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "amphibian-what",
    (("amphibian", "amphibians"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "animal",
      "animals", "science", "water", "land", "frog", "frogs")),
    "An amphibian is a cold-blooded animal with moist skin that lives part of its life in water and "
    "part on land. Frogs, toads and newts hatch as tadpoles with gills, then change into adults with "
    "lungs, and their skin has to stay damp, which is why you find them near ponds and in wet grass.",
    avoid=("vehicle", "car", "cars", "plane", "planes", "boat", "boats", "amphibious"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "insect-what",
    (("insect", "insects"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "animal",
      "animals", "science", "body", "legs", "wings")),
    "An insect is a small animal with a hard outer skeleton and three body parts - head, thorax and "
    "abdomen - with six legs and usually two pairs of wings. Beetles, bees, ants and butterflies are "
    "insects; a spider is not, because it has eight legs and two body parts.",
    avoid=("bite", "bites", "bitten", "sting", "stings", "stung", "pest", "pests", "infestation",
           "infestation", "kill", "get rid", "in my house", "in the house", "spider", "spiders"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "bird-what",
    (("bird", "birds"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "animal",
      "animals", "science", "feathers", "wings", "fly", "flies")),
    "A bird is a warm-blooded animal with feathers, a beak and two wings, and it lays hard-shelled "
    "eggs. All birds have feathers and none has teeth, and most can fly - though ostriches, penguins "
    "and kiwi cannot.",
    avoid=("bird flu", "flu", "table", "spotting", "watching", "watching", "feed", "feeder",
           "feeder", "bath", "nest", "nests", "cage", "aviary", "chicken", "chickens", "turkey",
           # a bird that has flown at the window is not a question about what a bird is:
           # "what does it mean when a bird hits your window" was answered with feathers, a beak
           # and hard-shelled eggs.
           "window", "windows", "glass", "flew into", "flew at", "flew in", "hit my window",
           "hits my window", "hit the window", "crashed into", "stunned", "dead bird"),
    ask=DEFINITION_ASK))


ENTRIES.append(entry(
    "bird-at-the-window",
    (("bird", "birds", "pigeon", "sparrow", "blackbird", "robin", "starling", "swallow"),
     ("window", "windows", "glass", "flew into", "flew at", "hit the window", "hit my window",
      "hits the window", "crashed", "stunned", "dead", "flying into",
      # The follow-up a person sends after this answer: what to put on the glass, and what to do
      # with the bird that is still there. A key word is what lets the second question land on
      # the same card instead of a search hedge.
      "stickers", "sticker", "tape", "silhouette", "silhouettes", "box", "the box",
      "still there", "sitting there", "hasnt moved", "hasn't moved", "let it go")),
    ("A window acts like a mirror: it reflects the sky and the trees you have behind you, so a bird "
     "flies at what looks like more trees. Put something on the outside of the glass - stickers, "
     "tape, a hanging silhouette - because one on the inside does nothing. If the bird is alive and "
     "stunned, put it in a box with air holes in a warm, dark, quiet place and leave it an hour or "
     "two; most fly off, and one that has not gone by then wants a wildlife rescue or a vet. A "
     "feeder within a metre of the window, or past three metres, helps too. It is not a sign of "
     "anything."),
    # a bird's mess on the window is a cleaning job, and that card knows the glass: this row is
    # only for the bird that flew at it.
    avoid=("eat", "recipe", "cook", "feed", "feeder", "table", "nest", "nests", "cage",
           "chicken", "chickens", "turkey", "bird flu", "keep", "keeping", "as a pet",
           # a bird a cat or a dog brought in never hit the glass: "my dog left a dead bird on
           # the mat" was told that a window reflects the sky. The pet that carries one in has
           # its own card, and only a bird nobody carried in is this row's.
           "dog", "dogs", "doggy", "cat", "cats", "kitten", "puppy", "pup",
           "brought in", "brought it in", "brought me", "brings in", "brings me", "bringing in",
           "carried in", "left it", "left a", "left me", "on the mat", "on the doormat",
           "doorstep", "door step", "at the door", "in the house", "in the kitchen",
           "poo", "poos", "mess", "droppings", "dirt", "muck", "clean", "cleaning", "clean off",
           "wash", "washing", "smear", "smears", "squeegee", "wipes", "wipe"),
    bias=2))

# The other half of the same question: the bird that is on the ground, still there. It is the
# first thing to do rather than the reason, so it is its own row - "what should i do with a
# stunned bird" wants the box, not the physics of a reflective pane.
ENTRIES.append(entry(
    "a-stunned-bird",
    (("bird", "birds", "pigeon", "sparrow", "blackbird", "robin", "starling", "swallow"),
     ("stunned", "stunned bird", "sitting there", "still there", "hasnt moved", "hasn't moved",
      "not moving", "the box", "in a box", "let it go", "what do i do with", "wont fly",
      "won't fly", "on the path", "on the ground")),
    ("Put it in a cardboard box with air holes in the lid, somewhere warm, dark and quiet, and "
     "leave it an hour or two: most come round and fly off. Do not feed it or try to give it "
     "water, and do not keep it longer than a few hours - one that is still there after that "
     "wants a wildlife rescue or a vet. Wash your hands afterwards. Then stop the next one: "
     "something on the outside of the glass, because a pane reflects the sky and the birds fly "
     "at it."),
    avoid=("eat", "recipe", "cook", "feed", "feeder", "table", "nest", "nests", "cage",
           "chicken", "chickens", "turkey", "bird flu", "keep", "keeping", "as a pet",
           "poo", "poos", "mess", "droppings", "dirt", "muck", "clean", "cleaning", "clean off",
           "wash", "washing", "smear", "smears", "squeegee", "wipes", "wipe"),
    bias=3))

ENTRIES.append(entry(
    "fish-what",
    (("fish", "fishes"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "animal",
      "animals", "science", "water", "gills", "fins")),
    "A fish is a cold-blooded animal with a backbone that lives in water and breathes through gills. "
    "It has fins to swim and usually scales, and most lay eggs; a whale or a dolphin is not a fish "
    "because it breathes air and feeds its young on milk.",
    avoid=("eat", "eats", "cook", "cooking", "recipe", "fry", "fried", "bake", "baked", "chips",
           "pet", "pets", "tank", "tanks", "aquarium", "pond",
           "catch", "caught", "market", "monger", "mongers", "oil", "omega", "finger", "fingers",
           "slice", "fillet", "fillets", "smell", "smells", "sick", "ill", "dying", "dead"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "planet-what",
    (("planet", "planets"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "space",
      "science", "solar", "sun", "star", "orbit")),
    "A planet is a large round body that orbits a star and has cleared other objects out of its own "
    "orbit. There are eight in our solar system - Mercury, Venus, Earth, Mars, Jupiter, Saturn, "
    "Uranus and Neptune - and Pluto is a dwarf planet because it shares its orbit with other icy "
    "bodies.",
    avoid=("fitness", "gym", "hollywood", "daily planet", "bank", "insurance"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "orbit-what",
    (("orbit", "orbits", "orbiting"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "space",
      "science", "earth", "sun", "moon", "satellite", "gravity")),
    "An orbit is the curved path one object takes around another because gravity pulls it inward "
    "while its sideways speed carries it forward. The Moon orbits Earth about once a month, and "
    "Earth orbits the Sun once a year at about 30 kilometres a second.",
    avoid=("gum", "chewing", "chewing gum", "brand", "sugar free", "sugar-free", "tube"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "solar-system-what",
    (("solar system", "the solar system", "our solar system"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "space",
      "science", "sun", "planets", "made", "how")),
    "The solar system is the Sun and everything held in orbit around it by its gravity: eight "
    "planets, their moons, dwarf planets such as Pluto, and billions of asteroids and comets. It "
    "formed about 4.6 billion years ago from a cloud of gas and dust, and the Sun holds 99.8% of its "
    "mass.",
    avoid=("panel", "panels", "solar panel", "solar panels", "install", "installation", "cost",
           "quote", "roof", "home", "house", "battery", "inverter", "tariff"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "asteroid-what",
    (("asteroid", "asteroids"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "space",
      "science", "rock", "space", "belt", "meteor", "planet")),
    "An asteroid is a lump of rock and metal left over from the birth of the solar system, smaller "
    "than a planet and usually irregular in shape. Most circle the Sun in the asteroid belt between "
    "Mars and Jupiter; one that enters Earth's atmosphere and burns up is a meteor, and one that "
    "lands is a meteorite.",
    avoid=("mining", "mine", "game", "games", "film", "movie", "documentary"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "evaporation-what",
    (("evaporation", "evaporate", "evaporates", "evaporating"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "science",
      "water", "liquid", "gas", "heat", "sun")),
    "Evaporation is a liquid turning into a gas at its surface, without needing to reach boiling "
    "point. Water left in a glass disappears over days because the fastest molecules escape into the "
    "air; warmth, wind and a larger surface make it happen faster, which is why washing dries on a "
    "line.",
    avoid=("milk", "evaporated milk", "recipe", "cook", "cooking", "pan", "sauce", "soup",
           "puddle", "spill", "spilled", "smell", "odour", "odor"),
    ask=DEFINITION_ASK))

ENTRIES.append(entry(
    "condensation-what",
    (("condensation", "condense", "condenses", "condensing"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "science",
      "water", "liquid", "gas", "cool", "cold")),
    "Condensation is a gas turning back into a liquid when it cools. Warm air holds water vapour, "
    "and when it meets a cold surface the vapour loses heat and forms droplets - that is the mist on "
    "a bathroom mirror, the water on a cold glass, and the clouds in the sky.",
    avoid=("stop", "stops", "prevent", "reduce", "get rid", "damp", "mould", "mold", "window",
           "windows", "wall", "walls", "boiler", "pipe", "pipes", "car", "headlight",
           "headlights", "dryer", "tumble dryer", "dehumidifier", "loft", "ceiling"),
    ask=DEFINITION_ASK))
ENTRIES.append(entry(
    "life-cycle-what",
    (("life cycle", "life cycles", "lifecycle", "lifecycles"),
     ("what", "mean", "meaning", "definition", "explain", "stages", "animal", "plant")),
    "A life cycle is the stages a living thing goes through from one generation to the next: a "
    "frog goes egg, tadpole, froglet, adult, and a butterfly goes egg, caterpillar, chrysalis, "
    "butterfly. A plant's is seed, seedling, flowering plant, then seed again. The adult stage is "
    "the one that makes the next generation, which is what closes the circle.",
    # No word here may share a stem with "cycle": "cycling" and "cycle to work" would both
    # stand the entry down on the line it exists for.
    avoid=("washing machine", "washer", "dishwasher", "tumble dryer", "drying", "spin",
           "menstrual", "period", "periods", "carbon", "assessment", "product", "products",
           "laundry", "clothes", "machine", "processor", "cpu", "duty"),
    ask=DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "triangle-what",
    (("triangle", "triangles"),
     ("what", "mean", "meaning", "definition", "explain", "type", "types", "kind", "kinds",
      "angles", "sides")),
    "A triangle is a flat shape with three straight sides and three corners, and its three angles "
    "always add up to 180 degrees. By its sides it is equilateral (all three equal), isosceles "
    "(two equal) or scalene (all different); by its angles it is acute, right-angled or obtuse.",
    avoid=("love triangle", "roof", "roofing", "sandwich", "toastie", "warning", "road",
           "sign", "yoga", "pose", "garden", "land", "plot", "field", "bermuda", "area",
           "perimeter", "hypotenuse", "pythagoras"),
    ask=DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "quadrilateral-what",
    (("quadrilateral", "quadrilaterals"),
     ("what", "mean", "meaning", "definition", "explain", "type", "types", "kind", "kinds",
      "sides")),
    "A quadrilateral is a flat shape with four straight sides and four corners, and its angles add "
    "up to 360 degrees. Squares, rectangles, parallelograms, rhombuses, trapeziums and kites are all "
    "quadrilaterals; a shape with four sides that is not a quadrilateral does not exist.",
    avoid=("garden", "land", "plot", "field", "room", "floor", "table", "rug", "tile",
           "tiles", "area", "perimeter"),
    ask=DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "diameter-what",
    (("diameter", "diameters"),
     ("what", "mean", "meaning", "definition", "explain", "radius", "circle", "difference")),
    "The diameter is the distance straight across a circle through its centre, and it is twice the "
    "radius. A circle 10 cm across has a radius of 5 cm and a circumference of about 31.4 cm, "
    "because circumference is pi times the diameter.",
    avoid=("pipe", "pipes", "hose", "wire", "cable", "tree", "trunk", "hole", "drill", "bit",
           "saw", "pizza", "cake", "tin", "pan", "wheel", "tyre", "tire"),
    ask=DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "vertebrate-what",
    (("vertebrate", "vertebrates"),
     ("what", "mean", "meaning", "definition", "explain", "animal", "animals")),
    "A vertebrate is an animal with a backbone: fish, amphibians, reptiles, birds and mammals are "
    "the five groups. The backbone is a column of bones or cartilage that protects the spinal cord, "
    "and it lets the animal grow large and move actively.",
    avoid=("invertebrate", "invertebrates", "pet", "dog", "cat", "horse", "back pain", "spine",
           "surgery", "injury", "fracture"),
    ask=DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "invertebrate-what",
    (("invertebrate", "invertebrates"),
     ("what", "mean", "meaning", "definition", "explain", "animal", "animals")),
    "An invertebrate is an animal with no backbone: insects, spiders, worms, snails, crabs, "
    "jellyfish and squid are all invertebrates. They are most of the animal species on Earth, and "
    "many have a hard shell or exoskeleton instead of bones.",
    avoid=("pet", "dog", "cat", "horse", "back pain", "spine", "surgery", "injury"),
    ask=DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "erosion-what",
    (("erosion", "erode", "eroding", "eroded"),
     ("what", "mean", "meaning", "definition", "explain", "cause", "causes", "coast",
      "soil", "rock", "land")),
    "Erosion is the wearing away and moving of rock, soil or sand by water, wind, ice or waves: "
    "rain washing soil off a bare field, or a river cutting into its banks. The material is then "
    "dropped somewhere else, which is deposition, and planting cover or slowing the water is the "
    "usual defence.",
    avoid=("tooth", "teeth", "enamel", "acid", "gum", "dental", "dentist", "rights",
           "confidence", "trust", "market", "profit", "brand", "relationship", "friendship",
           "democracy", "freedoms"),
    ask=DEFINITION_ASK,
    bias=2))

# "what keeps the moon in orbit" asks with the words of the asking in front ("what keeps"),
# and the moon card and the orbit card each held one end of it, so the line got a search hedge.
# Two parts that both match: the asking phrase, then the thing asked about. One phrase of the
# whole line would score 3 and MIN_SCORE is 4, which is why this is not a flat key.
ENTRIES.append(entry(
    "moon-orbit",
    (("what keeps the moon", "what holds the moon", "how does the moon stay",
      "how does the moon keep", "what makes the moon stay"),
     ("orbit", "orbits", "up", "up there", "in orbit", "in the sky", "going round")),
    "The Moon is falling towards the Earth all the time and moving sideways fast enough - about "
    "1 km a second - that it keeps missing, and that curved fall is the orbit. Gravity is the "
    "pull; with no sideways speed it would drop straight in. It has kept its own motion for 4.5 "
    "billion years because there is almost nothing out there to slow it down.",
    bias=2))

ENTRIES.append(entry(
    "moon-what",
    (("moon",),
     ("what", "mean", "meaning", "definition", "explain", "satellite", "earth")),
    "The Moon is the Earth's only natural satellite, about 384,000 km away, and gravity holds it "
    "in orbit. It makes no light of its own - we see sunlight reflected from its surface - and its "
    "pull is the main cause of our tides. It takes about 27 days to go round the Earth and the same "
    "time to turn once, so we always see the same side.",
    avoid=("honeymoon", "moonlight", "moonlighting", "boot", "landing", "apollo", "nasa",
           "astronaut", "flag", "made of", "made from", "inside", "core", "surface",
           "full", "new", "blue", "blood", "super", "harvest", "crescent", "phase",
           "phases", "bright", "orange", "white", "craters", "follows", "size", "big",
           "bigger", "horizon", "eclipse", "jupiter", "saturn", "mars", "venus", "neptune",
           "uranus", "titan", "io", "europa"),
    ask=DEFINITION_ASK,
    bias=2))
# --- how big is a planet ------------------------------------------------------------
# The Sun, the Earth and the Moon each had a size row of their own and the other planets had
# none, so "how big is jupiter" and "how big is mars" reached nothing at all and got the search
# hedge. A body is data, not wording, so the sizes are one table and one row rather than a row
# per question. Each figure is the width across, rounded the way the rows above quote it, and the
# comparison with the Earth is rounded too. The Earth is left out: earth-size already answers it.
PLANET_SIZES = (
    (("mercury",), "Mercury is about 4,879 km across, a little over a third of the Earth's width "
                   "and smaller than Jupiter's moon Ganymede."),
    (("venus",), "Venus is about 12,104 km across, almost exactly the Earth's width - about 95% "
                 "of it - and a little hotter than a pizza oven all over its surface."),
    (("mars",), "Mars is about 6,779 km across, a bit over half the Earth's width, so nearly two "
                "Marses would fit across the Earth's face."),
    (("jupiter",), "Jupiter is about 143,000 km across, eleven Earths side by side, and about "
                   "1,300 Earths would fit inside it: it is the biggest planet by a wide margin."),
    (("saturn",), "Saturn is about 116,460 km across, nine Earths side by side, and about 760 "
                  "Earths would fit inside it. Its rings are far wider than the planet and, in "
                  "places, only tens of metres thick."),
    (("uranus",), "Uranus is about 50,724 km across, four Earths side by side, and about 63 "
                  "Earths would fit inside it."),
    (("neptune",), "Neptune is about 49,244 km across, nearly four Earths side by side, and "
                   "about 58 Earths would fit inside it - a little smaller than Uranus but "
                   "heavier."),
    (("pluto",), "Pluto is about 2,377 km across: about a fifth of the Earth's width, and smaller "
                 "than our Moon."),
)

# The ways of asking how wide a thing is. This is the row's ask as well as its key, so a line
# that only names a planet ("mars is a big one in the calendar this month") is not this question.
_SIZE_ASK = ("how big", "how large", "how wide", "what size", "size", "diameter", "across",
             "bigger", "smaller", "compared", "how many earths", "how much bigger",
             "how much smaller")


def _the_planet_size(memory, understood):
    """The size of the planet the line names, and only when the planet is what it asks about.

    "how big is the sun compared to jupiter" is the Sun's question and sun-size answers it, so a
    body named earlier in the line than the planet stands this row down. "how big is jupiter
    compared to earth" is the other way round, and Jupiter is the answer.
    """
    said = " ".join(str(part).lower() for part in ((understood or {}).get("clean"),
                                                  (understood or {}).get("text")) if part)

    def at(name):
        found = re.search(r"(?<![a-z])" + name + r"(?![a-z])", said)
        return found.start() if found else None

    found = [(at(name), answer) for names, answer in PLANET_SIZES for name in names
             if at(name) is not None]
    if not found:
        return None
    first, answer = min(found)
    # A body with a size row of its own, named before this planet, is the one being asked about.
    for other in ("sun", "moon", "earth"):
        found_other = re.search(r"(?<![a-z])" + other + r"(?![a-z])", said)
        if found_other is not None and found_other.start() < first:
            return None
    return answer


ENTRIES.append(entry(
    "planet-size",
    (("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"),
     _SIZE_ASK),
    _the_planet_size,
    ask=_SIZE_ASK,
    # A planet named in passing in another question is that question: the night sky, the
    # horoscope, the mission and the trip each answer their own line.
    avoid=("see", "visible", "tonight", "telescope", "horoscope", "star sign", "zodiac",
           "astrology", "chart", "retrograde", "mission", "nasa", "rover", "rocket",
           "travel", "trip", "holiday", "hotel", "live on", "life on", "temperature",
           "hot", "cold", "weather", "moons", "orbit", "distance", "how far", "weight",
           "weigh", "gravity", "ring", "rings", "how many planets", "planet names"),
    bias=2))


# --- why a tall thing stays up -------------------------------------------
# "How do tall buildings not fall over" was answered by the falls-in-old-age card ("Falls are
# usually several small things adding up"), because the entry keys a bare "fall" beside "how do
# i". The subject is what makes the line a different question, so the falls card now stands down
# for a structure, and the thing named picks the answer here: a crane, a bridge and a tree each
# have their own reason, and a line that names none of them is the building.
BUILDING_STANDS = (
    "A tall building stays up because its weight runs straight down a braced frame into deep "
    "foundations, so wind bends it a little instead of tipping it, and the tallest carry a heavy "
    "damper near the top to soak up the sway. Pisa leans without falling because its weight still "
    "sits over its base: it sank slowly into soft ground, and soil taken out from the high side is "
    "what steadied it.")

CRANE_STANDS = (
    "A tower crane stays up because its mast is bolted to a concrete base and tied into the "
    "building as that rises, and a counterweight on the short arm balances the load on the long "
    "one. It is built to lift a set weight at a set reach and no more, so it trips out before it "
    "can tip.")

BRIDGE_STANDS = (
    "A bridge gets its load to the ground in one of three ways: a beam rests the span on a support "
    "at each end, an arch pushes the weight outwards into solid abutments, and a suspension or "
    "cable-stayed bridge hangs the deck from cables over towers anchored into the ground. Whichever "
    "it is, the span is never left to carry itself.")

CHIMNEY_STANDS = (
    "A chimney stays up because each stack of bricks is bonded into the wall it stands on and "
    "strapped to the roof, and every joint is staggered so the bricks cannot slide on each other - "
    "a straight stack of bricks with a flue down the middle is strong only while the mortar and the "
    "flaunching at the top are sound. That is why a chimney comes down in a storm, and why it comes "
    "down as one piece: the mortar in the joints has gone soft, or smoke and rain have washed it out "
    "from under the flaunching, so the whole stack rocks on its base.")

TREE_STANDS = (
    "A tree stays up because its roots spread about as wide as its branches and the trunk tapers as "
    "it rises, so most of the weight is low down and the crown is light. Wind is what tests it: a "
    "tree that bends sheds the force, and the one that comes down is the one whose roots were cut "
    "on one side or left standing in waterlogged soil.")

PLANT_STANDS = (
    "A houseplant flops over for one of three reasons: it has grown tall and thin reaching for "
    "light, the pot has become top-heavy for its roots, or the roots have rotted in soggy compost "
    "and let go. Move it somewhere brighter, put a cane or a hoop in and tie the stems loosely, and "
    "check the drainage holes before you water again - a pot standing in a full saucer is the usual "
    "cause.")

GARDEN_PLANT_STANDS = (
    "A plant in the ground or a grow bag goes over for one of four reasons, and the fix is the one "
    "that matches: it grew tall and soft reaching for light, so stake it loosely with a cane and a "
    "soft tie in a figure of eight and give it more sun; it was sown too thickly and the stems are "
    "thin, so thin them next time; the roots have been eaten or rotted, so lift the sick one and "
    "look; or wind and rain bent it, so a windbreak or a row of sturdier plants on that side is "
    "what stops it next year. Seedlings that flop at soil level are damping off from cold wet "
    "compost rather than anything above it.")

# A tomato or a sunflower is not a windowsill plant: the garden answer is the one that helps.
GARDEN_PLANTS = re.compile(
    r"\b(?:tomato(?:es)?|sunflowers?|tulips?|daffodils?|roses?|seedlings?|sweetcorn|corn|"
    r"beans?|peas?|courgettes?|pumpkins?|squash|dahlias?|climbers?|clematis|wisteria|"
    r"shrub|shrubs|hedge|hedges|garden|gardens|outdoor|outdoors|outside|allotment|"
    r"grow bag|bed|beds|plot)\b")

STANDING_WORDS = ("fall over", "falls over", "falling over", "fallen over", "fell over",
                  "fall down", "falls down", "fell down", "falling down",
                  "fall", "falls", "collapse", "collapses", "collapsed", "topple", "topples",
                  "flop over", "flops over", "flopped over", "keel over", "keels over",
                  "keeled over", "keeling over", "stay up", "stays up",
                  "stay standing", "stays standing", "still standing", "stay upright",
                  "not fall", "dont fall", "doesnt fall", "does not fall",
                  "not collapse", "sway", "sways", "wobble", "wobbles", "blown over",
                  "blow over", "blows over", "not tip", "tip over", "stand up", "stands up",
                  "standing up", "survive", "survives", "withstand", "withstands",
                  "hold up", "holds up", "earthquake", "earthquakes", "quake", "quakes",
                  "hurricane", "high winds",
                  # a plant that is top heavy, leans, or keeps going over is the same question
                  # as one that flops (measured on `3ae8d520`: "my plant is top heavy" was a
                  # filler, and these four words move it and nothing else)
                  "top heavy", "top-heavy", "tips over", "tipping over", "keeps falling",
                  "lopsided")


def _tall_thing(memory, understood):
    """The answer for the tall thing the line names, and the building's if it names none."""
    said = " ".join(str(part).lower() for part in ((understood or {}).get("clean"),
                                                   (understood or {}).get("text")) if part)
    if re.search(r"\bcranes?\b", said):
        return CRANE_STANDS
    if re.search(r"\bbridges?\b", said):
        return BRIDGE_STANDS
    if re.search(r"\bchimneys?\b", said):
        return CHIMNEY_STANDS
    if re.search(r"\btrees?\b|\bforest\b|\bwoods\b", said):
        return TREE_STANDS
    if GARDEN_PLANTS.search(said):
        return GARDEN_PLANT_STANDS
    if re.search(r"\bplants?\b|\bhouseplants?\b|\bflowers?\b|\bhanging basket\b",
                 said):
        return PLANT_STANDS
    return BUILDING_STANDS


ENTRIES.append(entry(
    "tall-things-stand-up",
    (("building", "buildings", "skyscraper", "skyscrapers", "high rise", "high-rise",
      "tower", "towers", "tower block", "tower blocks", "block of flats", "blocks of flats",
      "crane", "cranes", "bridge", "bridges", "chimney", "chimneys", "pylon", "pylons",
      "tree", "trees", "forest", "woods", "plant", "plants", "houseplant", "houseplants",
      "seedling", "seedlings", "tomato", "tomatoes", "flowers", "hanging basket",
      "tulip", "tulips", "daffodil", "daffodils", "sunflower", "sunflowers", "rose", "roses",
      "shrub", "shrubs", "climber", "climbers", "sweetcorn", "dahlia", "dahlias"),
     STANDING_WORDS),
    _tall_thing,
    # A line that names a structure and a standing word is asking why it stands up, not telling
    # someone about one: "how do i get to the shard" and "my nan fell over" are other answers.
    # The last few are how a person reports one that has gone over rather than asks why.
    ask=("why", "how", "what", "does", "do", "dont", "doesnt", "can", "is", "are", "will",
         "has", "have", "keeps", "keep", "fell", "fallen", "flopped", "flop"),
    # the markets fall, a tree's leaves fall and a hair falls out, and none of them is standing up
    avoid=("shares", "stocks", "prices", "share price", "the market", "markets", "hair",
           "leaves", "leaf", "rain", "snow", "asleep", "twin towers", "9/11", "nine eleven",
           "world trade", "rent", "price", "value", "house prices",
           # a person who has fallen keeps the falls review, whatever they were near
           "nan", "nana", "grandad", "grandma", "granny", "gran", "mum", "mom", "dad",
           "elderly", "pensioner", "old people", "old lady", "old man", "i fell", "tripped",
           "stairs", "ladder", "roof",
           # a plant that has to survive the frost is not a plant that flops over: "will my
           # plants survive the frost" was the houseplant answer, because "survive" is a
           # standing word. The cold is the garden's question.
           "frost", "frosts", "frosty", "freezing", "cold", "winter", "winters", "ice"),
    bias=1))


# --- a bridge, and what kind it is ---------------------------------------------------------
# The card above answers why a structure stays up, and it was all there was: "what is a bridge",
# "what is a beam bridge", "what is a viaduct" and "what is a cantilever" were the honest shrug,
# "how does an arch work" was answered as though the person had told the bot something, and two
# lines got another subject's answer - "what is a suspension bridge" was the chemistry suspension
# and "what is the longest bridge in the world" was the Nile. A bridge is a school-book subject,
# and each kind of bridge is one fact, so the kind the line names picks the answer.
STRUCTURE_ANSWERS = (
    (("longest bridge", "longest bridges", "longest bridge in the world"),
     "The longest bridge in the world is the Danyang-Kunshan Grand Bridge on the Beijing-Shanghai "
     "high-speed railway, about 165 km, most of it on piers over land and water. The longest over "
     "open sea is the Jiaozhou Bay Bridge at about 42 km, and the longest in Europe is the Crimean "
     "Bridge at about 19 km. A long bridge is nearly always a run of short spans on piers rather "
     "than one big span."),
    (("suspension bridge", "suspension bridges"),
     "A suspension bridge hangs its deck from two main cables slung over the towers and anchored "
     "into the ground at each end, with vertical hangers dropping to the deck. The cables pull, "
     "the towers carry that pull down, and the anchors take it at the ends, which is why it can "
     "span 1 to 2 km - the Humber Bridge, the Golden Gate, the Akashi Kaikyo."),
    (("cable stayed", "cable-stayed", "cable stayed bridge"),
     "A cable-stayed bridge runs cables straight from the tower to the deck, a fan or a harp of "
     "them, instead of one main cable with hangers. It needs no big anchorage at the ends, so it "
     "suits spans of a few hundred metres - the Queen Elizabeth II Bridge at Dartford and the "
     "Millau Viaduct are cable-stayed."),
    (("box girder", "box girders", "box girder bridge"),
     "A box girder is a beam made as a hollow box of steel or concrete, wide at the top to carry "
     "the road and deep enough to be stiff: a hollow box is far stiffer than a solid bar of the "
     "same weight, because the material sits out at the edges. Most long concrete bridges and "
     "cable-stayed decks are a box girder, and the box is also where the cables and the air for "
     "the inside run."),
    (("pier", "piers"),
     "A pier is one of the upright supports a bridge span rests on, and it is what the weight of "
     "the span comes down through to the ground. In a river they are built inside a cofferdam or "
     "a caisson, and the spans sit on bearings on top of them so the deck can expand and "
     "contract without cracking."),
    (("beam bridge", "beam bridges", "girder bridge", "girder bridges"),
     "A beam bridge is the simplest kind there is: a slab or a girder laid across two supports. "
     "The deck bends under the load, so the top is squeezed and the bottom is stretched, and the "
     "deeper the girder the further it reaches. Cheap, quick, and right for a short span."),
    (("arch bridge", "arch bridges", "how does an arch work", "how do arches work",
      "why do arches work"),
     "An arch bridge carries its load in compression: the weight comes down through the arch and "
     "pushes outwards at the bottom, so the ground or the abutments at each end have to resist "
     "that push. That is why stone and brick are so good in an arch - they take squeezing and not "
     "stretching - and why the Iron Bridge at Coalbrookdale, the first big cast-iron arch, was "
     "built in 1779 in the same shape."),
    (("viaduct", "viaducts", "aqueduct", "aqueducts"),
     "A viaduct carries a road or a railway across a valley on a run of arches or piers rather "
     "than one span, which is what you need when the gap is long and the ground below is uneven - "
     "the Ribblehead Viaduct has 24 arches. An aqueduct is the same structure carrying water: the "
     "Romans built them on stone arches, and a canal aqueduct does the same job for boats."),
    (("cantilever", "cantilevers", "cantilever bridge", "cantilever bridges"),
     "A cantilever is a beam held at one end with the other end free: a balcony, a diving board, a "
     "crane jib. Two cantilevers reaching out from opposite banks make a cantilever bridge, and it "
     "can be built outwards from each side without scaffolding in the water - the Forth Bridge is "
     "the famous one."),
    (("expansion joint", "expansion joints"),
     "Bridges have expansion joints because steel and concrete change length as they warm and "
     "cool, and a long deck moves by several centimetres between winter and summer. The joint is "
     "the strip that lets it happen without cracking the deck or shoving the abutments - the "
     "toothed metal you hear clicking under the wheels - and it is also what lets the bridge move "
     "in an earthquake."),
    (("tunnel", "tunnels"),
     "A tunnel under water is usually not bored through the seabed: most are immersed tubes - a "
     "trench is dredged, boxed sections are floated out, sunk into it and joined, then covered "
     "over, which is how the Oresund link and the Fehmarn tunnel were built. Boring is used where "
     "the ground is good, as in the chalk under the Channel: a shielded machine cuts the face and "
     "the lining goes up behind it as it goes."),
)


def _a_tunnel_named(said):
    """The tunnel record or the Channel Tunnel, when that is what the line asks about."""
    if " tunnel" not in said and " tunnels" not in said:
        return None
    if "channel tunnel" in said or (" channel " in said and ("how long" in said or "long" in said)):
        return ("The Channel Tunnel is 50.5 km from end to end, with about 38 km of it under the "
                "sea, and a train takes about 35 minutes from Folkestone to Calais. Three tubes "
                "run side by side: two for trains and a smaller service tunnel between them, "
                "bored through chalk that is soft enough to cut and stiff enough to stand while "
                "you do it.")
    if "longest" in said or "how long" in said:
        return ("The longest railway tunnel in the world is the Gotthard Base Tunnel in "
                "Switzerland at 57 km, opened in 2016; the longest road tunnel is the Laerdal "
                "Tunnel in Norway at 24.5 km. The longest undersea one is still the Channel "
                "Tunnel at 38 km under the water.")
    return None


PLACES_WITH_A_TALLEST = ("the world", "world", "london", "uk", "the uk", "britain", "great britain",
                         "the united kingdom", "united kingdom", "england", "scotland", "wales",
                         "british")


# The bridge records the file holds are the world, Europe, Britain and the home countries. A
# longest bridge asked about any other place gets the honest pass, not the world record.
PLACES_WITH_A_LONGEST = ("the world", "world", "europe", "uk", "the uk", "britain",
                         "great britain", "the united kingdom", "united kingdom", "england",
                         "scotland", "wales", "british")


def _the_place_asked(said, known=PLACES_WITH_A_TALLEST):
    """The place a record line asks about, or None when the line names none."""
    parts = said.split(" in ")
    if len(parts) < 2:
        return None
    words = parts[-1].split()
    for count in (3, 2, 1):
        guess = " ".join(words[:count])
        if guess in known:
            return guess
    return words[0] if words else None


def _the_longest_bridge(said):
    """The longest bridge in the place the line names, or None when it names no bridge."""
    if " bridge" not in said and " bridges" not in said:
        return None
    if "longest" not in said and "biggest" not in said and "largest" not in said:
        return None
    place = _the_place_asked(said, PLACES_WITH_A_LONGEST)
    if place and place not in PLACES_WITH_A_LONGEST:
        return None
    if " europe " in said and " world " not in said:
        return ("The longest bridge in Europe is the Crimean Bridge at about 19 km, if you count "
                "the crossing built in 2018; inside the European Union the longest is the Vasco "
                "da Gama Bridge in Lisbon at about 17 km, opened in 1998. The Oresund link between "
                "Denmark and Sweden is about 8 km of bridge and 4 km of tunnel.")
    if any((" " + word + " ") in said for word in ("uk", "britain", "england", "scotland",
                                                   "wales", "british")):
        return ("The longest bridge in Britain is the Prince of Wales Bridge over the Severn, "
                "about 5 km, which carries the M4; the Queen Elizabeth II Bridge at Dartford is "
                "about 2.9 km and the Humber Bridge 2.2 km, though the Humber has the longest "
                "single span in Britain.")
    return None


def _a_kind_of_bridge(memory, understood):
    """The kind of structure the line names, or the plain bridge answer when it names none."""
    said = _the_line(understood) if "_the_line" in globals() else ""
    if not said:
        said = " " + str((understood or {}).get("clean") or (understood or {}).get("text")
                         or "").lower() + " "
    named = _the_longest_bridge(said) or _a_tunnel_named(said)
    if named:
        return named
    if "longest" in said or "biggest" in said or "largest" in said:
        place = _the_place_asked(said, PLACES_WITH_A_LONGEST)
        if place and place not in PLACES_WITH_A_LONGEST:
            return None
    if any(word in said for word in (" build ", " built ", " builds ", " building ",
                                     " construct ", " constructed ")) and any(
            (" " + word + " ") in said for word in ("bridge", "bridges", "viaduct", "flyover")) and any(
            (" " + word + " ") in said for word in ("motorway", "motorways", "road", "roads",
                                                    "railway", "railways", "rail")):
        return ("A bridge over a motorway is built a piece at a time so the road can stay open: "
                "the beams or the whole deck are put together beside it and lifted or slid into "
                "place in overnight closures, or the deck is pushed out from one side with a "
                "launching girder. The piers go in first, the beams land on them, and the road "
                "below is only shut for the hours it takes to place each piece.")
    if any(word in said for word in (" how long does it take ", " how long to ", " cost of ",
                                     " how much does ")):
        return None
    if any(word in said for word in (" what does ", " what do ", " meaning ", " in english ")) and not any(
            (" " + word + " ") in said for word in ("bridge", "bridges", "tunnel", "tunnels",
                                                    "viaduct", "aqueduct", "span", "spans")):
        return None
    for names, answer in STRUCTURE_ANSWERS:
        if any((" " + name + " ") in said for name in names):
            return answer
    return ("A bridge carries a load across a gap, and it does it in one of four ways: a beam "
            "resting on a support at each end, an arch pushing the weight outwards into solid "
            "ground, a truss or box girder making a beam stiffer, or cables hanging the deck from "
            "towers - suspension or cable-stayed. Stone and brick work in an arch, steel works in "
            "all four.")


# --- the tallest building ---------------------------------------------------------------
# "What is the tallest building in the world" was the honest shrug on main, and it is a school-book
# question with one answer. The tallest in Britain is a different record, so the place in the line
# picks it, and a line about why a tall thing stands up keeps the card above.
TALL_BUILDINGS = (
    (("shard",),
     "The Shard in London is 310 m to the tip of its spire, 95 storeys, finished in 2012 - the "
     "tallest building in the United Kingdom and, for four years, in western Europe. Its floor "
     "plate is glass on all sides and the tower leans in as it rises, so the top storeys are "
     "smaller than the bottom ones."),
    (("burj khalifa", "burj"),
     "The Burj Khalifa in Dubai is 828 m, 163 floors, finished in 2010, and it is the tallest "
     "building in the world. It is concrete from top to bottom rather than steel, and it steps in "
     "as it rises to break up the wind, which is what allows the height."),
)

# A place the file has no record for gets an honest pass rather than the world record: a confident
# answer about New York or Manchester that names Dubai is worse than the shrug it replaces.
def _the_tallest_building(memory, understood):
    said = " " + str((understood or {}).get("clean") or (understood or {}).get("text") or ""
                     ).lower() + " "
    for names, answer in TALL_BUILDINGS:
        if any((" " + name + " ") in said for name in names):
            return answer
    place = _the_place_asked(said)
    if place and place not in PLACES_WITH_A_TALLEST:
        return None
    if ((" skyscraper " in said or " skyscrapers " in said)
            and not any((" " + word + " ") in said for word in
                        ("tallest", "highest", "biggest", "world", "london", "uk", "britain"))):
        return ("A skyscraper is a very tall building, and the usual line is 100 m for one and "
                "150 m for a supertall. Two things made them possible: a steel frame that carries "
                "the weight instead of the walls, and the safety lift, so the building could go up "
                "rather than out. The first was the Home Insurance Building in Chicago in 1885, "
                "ten storeys; the Burj Khalifa is 163.")
    if " london " in said and " world " not in said:
        return ("The tallest building in London is The Shard at 310 m, finished in 2012, with 95 "
                "storeys; One Canada Square at Canary Wharf, 235 m, was the tallest before it. "
                "The tallest in the United Kingdom is still The Shard.")
    if any((" " + word + " ") in said for word in ("uk", "britain", "england", "scotland",
                                                   "wales", "british")):
        return ("The tallest building in the United Kingdom is The Shard in London at 310 m, "
                "finished in 2012. The tallest in Scotland is the Aughton Street tower in "
                "Glasgow, and in Wales it is the Sky Plaza in Cardiff.")
    return ("The tallest building in the world is the Burj Khalifa in Dubai at 828 m, 163 floors, "
            "finished in 2010; Merdeka 118 in Kuala Lumpur at 679 m is second, and the Shanghai "
            "Tower at 632 m third. The Burj was built that tall because the client wanted it to "
            "be, and the limits above 500 m are the lifts - a single lift run gets too long - and "
            "the wind, which is why the tower steps in as it rises.")


ENTRIES.append(entry(
    "the-tallest-building",
    (("tallest building", "tallest buildings", "tallest tower", "tallest skyscraper",
      "highest building", "biggest building", "burj khalifa", "burj", "shard", "skyscraper",
      "skyscrapers"),
     ("what", "whats", "what's", "which", "where", "how tall", "tall", "highest", "tallest",
      "in the world", "world", "uk", "britain", "london", "explain", "tell me")),
    _the_tallest_building,
    # a line about why a tall thing stands up, or about the flat they live in, is another answer
    avoid=("hold up", "holds up", "stay up", "stays up", "stand up", "stands up", "fall down",
           "collapse", "sway", "wobble", "topple", "leaning", "my flat", "my office", "rent",
           "my building", "upstairs", "neighbour", "neighbours", "lease", "cladding",
           "fire", "fires", "insurance", "mortgage", "buy", "move", "moving"),
    bias=1))

ENTRIES.append(entry(
    "a-kind-of-bridge",
    (("bridge", "bridges", "suspension bridge", "beam bridge", "arch bridge", "girder",
      "cantilever", "viaduct", "viaducts", "aqueduct", "tunnel", "tunnels", "expansion joint",
      "expansion joints", "arch", "arches"),
     ("what", "whats", "what's", "how", "why", "explain", "mean", "means", "built", "build",
      "building", "work", "works", "working", "used for", "made", "made of", "difference",
      "definition", "define", "longest", "highest", "biggest")),
    _a_kind_of_bridge,
    # The card above answers why a named structure stands up, and a line that says it is falling
    # down or standing up is that question, not this one.
    avoid=("hold up", "holds up", "hold it up", "stay up", "stays up", "standing up",
           "stand up", "fall down", "falls down", "fell down", "falling down", "collapsed",
           "collapse", "sway", "wobble", "topple", "lean", "leaning",
           # an arch in a foot, a dental bridge and a game of cards are not a bridge
           "foot", "feet", "fallen arches", "arch support", "arch supports", "insole",
           "insoles", "plantar", "heel", "nose", "tooth", "teeth", "dental", "dentist",
           "dentures", "dentistry", "bridgework", "implants", "crown", "crowns",
           "card game", "cards", "bridge the gap", "bridge a gap", "loan",
           "the gap",
           # a network bridge, and the Romans, whose arch is a history line with its own card
           "network", "networking", "ethernet", "router", "routers", "wifi", "wi-fi", "modem",
           "switch", "lan", "vlan", "docker", "hypervisor", "virtual machine",
           "roman", "romans", "roman britain", "the romans", "boudicca", "hadrians wall",
           "hastings", "castle", "castles", "monastery", "cathedral", "cathedrals",
           # a car's suspension, a tunnel in the wrist and a tunnel in the garden
           "car", "rear suspension", "front suspension", "suspension arm", "suspension arms",
           "suspension bush", "suspension bushes", "shock", "shocks", "spring", "springs",
           "mot", "wheel",
           "carpal", "wrist", "tunnel vision", "polytunnel", "wind tunnel", "garden",
           "allotment", "greenhouse", "sewing", "fabric", "music", "song", "guitar", "piano"),
    bias=1))


# --- the school science definition that had no card ---------------------------------------
# Twenty everyday "what is" questions from a school book, asked on main `e900c474`: eight were a
# shrug ("what is resistance", "what is respiration", "what is mitosis", "what is mass", "what is
# weight", "what is kinetic energy", "what is potential energy", "what is frequency"), the rock
# cycle was answered with what a rock is, and Newton's second law with a sentence about Newton.
# Each row is the term in the first group and a way of asking for a definition in the second, so
# "define mitosis" and "what is mitosis" are the same question. The mass-and-weight and the two
# energies are one row each because the pair *is* the answer.
_DEFINE = ("what is", "what are", "whats", "what's", "define", "definition", "meaning", "mean",
           "means", "explain", "explanation", "difference between", "difference", "vs",
           "measured in", "measure", "measured", "how is it", "simple terms", "for kids",
           "gcse", "physics", "chemistry", "biology", "science")

# One row holds each pair of terms because the pair *is* the answer, but a card that opens on the
# other one is a confident answer to a question nobody asked: "what is weight" opened "Mass is how
# much stuff is in you", "what is wavelength" opened "Frequency is how many times something happens
# in a second", and "what is velocity" opened "Speed is how fast you are going". Three readers
# asked for the same fix, so the pair cards now read which of the two words the line names and
# open on it, and the partner term comes second.
_DEFINITION_FILLER = frozenset((
    "what", "whats", "is", "are", "the", "a", "an", "of", "in", "and", "or", "it", "its", "mean",
    "means", "meaning", "define", "definition", "explain", "explanation", "simple", "terms",
    "for", "kids", "gcse", "physics", "chemistry", "biology", "science", "difference", "between",
    "vs", "versus", "measured", "measure", "how", "do", "you", "that", "this", "please", "sir",
    "miss", "again", "when", "would", "be", "use", "used", "example", "examples", "give", "me",
    "one", "some", "tell", "about", "which", "so", "then", "kind", "sort", "class", "school"))


def _the_line(understood):
    """The person's own words, lower case, with a space at each end."""
    said = ""
    if isinstance(understood, dict):
        said = str(understood.get("clean") or understood.get("text") or "")
    return " " + said.lower() + " "


def _names(said, words):
    """The first of `words` the line actually says, or "" when it says none of them."""
    best, at = "", None
    for word in words:
        found = said.find(" " + word + " ")
        if found == -1:
            found = said.find(word)
            if found == -1:
                continue
        if at is None or found < at:
            best, at = word, found
    return best

# The words a line uses when it is asking what mass or weight is. A figure on its own is not
# one: "about a stone" one turn after "i want to lose weight" matched this row on the word
# "weight" in the turn above, and got a definition of mass in answer to how much somebody wanted
# to lose.
MASS_OR_WEIGHT_WORDS = ("mass", "weight", "weigh", "weighs", "weighed", "weighing", "newton",
                        "newtons", "gravity")
# A unit on its own is a figure, not a question about what the unit is: "i want to lose half a
# stone" is not asking what a stone weighs, so a unit only keeps the card when the line is shaped
# like a definition ("how many pounds in a stone", "what does a kilo mean").
MASS_OR_WEIGHT_UNITS = ("kg", "kgs", "kilo", "kilos", "kilogram", "kilograms", "kilogramme",
                        "kilogrammes", "lb", "lbs", "pounds", "pound", "stone", "stones")


def asks_about_mass_or_weight(understood):
    """Whether this line, not the conversation, asks what mass or weight is.

    Read from what the person typed rather than from `clean`, because the knowledge pass hands a
    follow-up a clean line with the subject carried over from the turn above: "about a stone"
    after "i want to lose weight" arrives as "what about about a stone weight", and the word
    "weight" in it is the bot's own, not theirs.
    """
    said = ""
    if isinstance(understood, dict):
        said = str(understood.get("text") or understood.get("clean") or "")
    said = " " + said.lower() + " "
    if isinstance(understood, dict) and isinstance(understood.get("leans_on"), dict):
        # The follow-up's line is the person's own words with the earlier line's words tacked on
        # the end, so the tail is what the bot brought, not what they said.
        borrowed = {str(word).lower() for word in
                    (understood["leans_on"].get("words") or []) if isinstance(word, str)}
        words = re.findall(r"[a-z0-9']+", said)
        while words and words[-1] in borrowed:
            words.pop()
        said = " " + " ".join(words) + " "
    if _names(said, MASS_OR_WEIGHT_WORDS):
        return True
    return bool(_names(said, MASS_OR_WEIGHT_UNITS) and _names(said, _DEFINE))


def _mass_and_weight(memory, understood):
    """Weight asked about first, because "what is weight" was opening with the mass sentence."""
    said = _the_line(understood)
    if _names(said, ("weight", "weigh")) == "weight" and not _names(said, ("mass",)):
        return ("Weight is the pull of gravity on a mass, measured in newtons: a 60 kg person "
                "weighs about 600 N on Earth, about 100 N on the Moon and nothing at all in "
                "orbit. Mass is how much stuff is in something, measured in kilograms, and it is "
                "60 kg in all three places. The scales in your bathroom measure weight and are "
                "marked in kilograms for the mass that goes with it here.")
    return ("Mass is how much stuff is in something, measured in kilograms, and it does not change "
            "wherever you go. Weight is the pull of gravity on that mass, measured in newtons: a "
            "60 kg person weighs about 600 N on Earth, about 100 N on the Moon and nothing at all "
            "in orbit, while their mass is 60 kg in all three places. So the scales in your "
            "bathroom measure weight and are marked in kilograms for the mass that goes with it "
            "here.")


ENTRIES.append(entry(
    "mass-and-weight",
    (("mass", "weight", "mass and weight", "mass vs weight", "kg", "newtons"),
     _DEFINE + ("in space", "on the moon", "on the moon", "gravity", "moon", "kilogram",
                "kilogramme", "pounds", "lb", "same")),
    _mass_and_weight,
    guard=asks_about_mass_or_weight,
    # a church mass, a body mass index and a diet are other questions
    avoid=("church", "catholic", "in church", "the mass", "bmi", "lose weight", "losing weight",
           "lose", "losing", "diet", "gain weight", "put on weight", "slimming", "scale",
           "scales", "how much should i weigh", "healthy weight", "protein", "deadlift",
           # "what time is mass" and "mass on sunday" are the church, and neither was a hedge
           # before this row existed: the row is fenced off them, not the other way round.
           "what time", "sunday", "saturday", "say mass", "dead weight", "mass in",
           # a newton metre is torque, not mass, and the line names no car part to send it to
           "newton metre", "newton metres", "newton-metre", "newton meter", "newton meters",
           "nm", "torque", "wrench", "priest", "communion", "midnight mass", "christmas",
           "easter"),
    bias=1))
def _kinetic_and_potential(memory, understood):
    """The energy the line names comes first: "what is potential energy" led with kinetic."""
    said = _the_line(understood)
    named = _names(said, ("potential", "kinetic"))
    if named == "potential":
        return ("Potential energy is energy stored ready to be used: a ball held up high has "
                "potential energy, and it turns into kinetic energy as it falls, faster and "
                "faster. Kinetic energy is the energy something has because it is moving. Both "
                "are measured in joules. Potential is mass times gravity times height, so twice "
                "the height is twice the energy; kinetic is half the mass times the speed "
                "squared, so doubling the speed gives four times the energy.")
    return ("Kinetic energy is the energy something has because it is moving, and potential "
            "energy is energy stored ready to move: a ball held up high has potential energy, "
            "and it turns into kinetic energy as it falls, faster and faster. Both are measured "
            "in joules. Kinetic is half the mass times the speed squared, so doubling the speed "
            "gives four times the energy; potential is mass times gravity times height, so twice "
            "the height is twice the energy.")


ENTRIES.append(entry(
    "kinetic-and-potential-energy",
    (("kinetic energy", "potential energy", "kinetic and potential", "kinetic", "potential",
      "stored energy", "energy of motion"),
     _DEFINE + ("store", "stored", "difference between", "convert", "converted", "transfer",
                "example", "examples", "joules", "falling", "swing", "roller coaster")),
    _kinetic_and_potential,
    avoid=("boiler", "thermostat", "battery", "solar", "tariff", "bill", "meter", "kettle"),
    bias=1))
ENTRIES.append(entry(
    "electrical-resistance",
    (("resistance", "ohms", "ohm", "ohm's law", "ohms law"),
     _DEFINE + ("circuit", "circuits", "current", "voltage", "wire", "conductor", "measure",
                "measured in", "increase", "decrease", "lower", "reduce", "series", "parallel",
                "lamp", "bulb", "resistor")),
    "Resistance is how much a material fights the current, measured in ohms: a thin, long, hot "
    "wire has more of it than a short thick cold one, which is why a laptop charger stays cool "
    "and a toaster element glows. Ohm's law ties the three together, voltage equals current "
    "times resistance, so at 12 V a 4 ohm resistor carries 3 A. It turns the energy into heat, "
    "which is the point of a heater and the reason a long cable warms up.",
    # a resistance band is exercise, and an antibiotic resistance is a health question
    avoid=("band", "bands", "training", "gym", "workout", "weights", "exercise", "antibiotic",
           "antibiotics", "insulin", "airway", "drug", "drugs"),
    bias=1))
ENTRIES.append(entry(
    "respiration",
    (("respiration", "aerobic respiration", "anaerobic respiration", "breathing and respiration",
      "cellular respiration"),
     _DEFINE + ("difference between", "equation", "word equation", "aerobic", "anaerobic",
                "muscle", "muscles", "lactic", "energy", "glucose", "oxygen", "plants", "cell",
                "cells")),
    "Respiration is how cells release energy from glucose: glucose plus oxygen gives carbon "
    "dioxide plus water plus energy, and every cell does it all the time. Breathing is only the "
    "moving of air in and out - the oxygen it brings is used in respiration and the carbon "
    "dioxide it carries away was made there. Sprinting, or holding your breath under water, "
    "outruns the oxygen, so muscles switch to anaerobic respiration, which makes energy fast and "
    "leaves lactic acid: that is the burn.",
    avoid=("cough", "colds", "chest", "lung", "lungs", "asthma", "doctor", "gp", "nhs",
           "my breathing", "breathless", "wheeze", "wheezing", "sleep", "snoring", "apnoea",
           # a respiration RATE is a number to look up and a health visitor's question
           "rate", "per minute", "breaths a minute", "breaths per minute", "my baby",
           # "breaths" alone reaches "breathing", which is in this row's own key
           "baby", "normal"),
    bias=1))
def _mitosis_meiosis(memory, understood):
    """Three words one row, and the first sentence answers the one the line names: "what is
    meiosis" opened with the mitosis sentence and "what is the cell cycle" never named the
    cycle at all, though both words are in this row's key."""
    said = _the_line(understood)
    named = _names(said, ("meiosis", "cell cycle", "mitosis"))
    if named == "meiosis":
        return ("Meiosis makes four cells with half the chromosomes each, and that is how eggs "
                "and sperm are made, so that when two of them join the new cell has a full set "
                "again. Mitosis makes two identical cells, each with the same chromosomes as the "
                "parent, and that is how you grow and how a cut heals. Meiosis has two divisions "
                "in a row, mitosis one; the mnemonic that works is mitosis for maintenance, "
                "meiosis for making babies.")
    if named == "cell cycle":
        return ("The cell cycle is the whole life of a cell from one division to the next: a "
                "growth stage where the cell gets bigger and copies its DNA, then the division "
                "itself, which is mitosis if it makes two identical cells. Cells that stop "
                "dividing leave the cycle and sit in a resting state instead. Meiosis is the "
                "different division that makes eggs and sperm, with half the chromosomes each.")
    return ("Mitosis makes two identical cells, each with the same chromosomes as the parent, and "
            "that is how you grow and how a cut heals. Meiosis makes four cells with half the "
            "chromosomes, and that is how eggs and sperm are made, so that when two of them join "
            "the new cell has a full set again. The mnemonic that works: mitosis for maintenance, "
            "meiosis for making babies. Mitosis has one division, meiosis has two in a row.")


ENTRIES.append(entry(
    "mitosis-and-meiosis",
    (("mitosis", "meiosis", "cell division", "mitosis and meiosis", "cell cycle"),
     _DEFINE + ("difference between", "stages", "phases", "how", "why", "purpose", "gcse",
                "growth", "repair", "gametes", "sex cells", "chromosomes", "diploid", "haploid")),
    _mitosis_meiosis,
    bias=1))
def _frequency_wavelength_amplitude(memory, understood):
    """Three words one row, and the first sentence answers the one the line names. "what is
    wavelength" and "what is amplitude" were both opening with the frequency sentence, which
    never said the word asked about."""
    said = _the_line(understood)
    named = _names(said, ("wavelength", "amplitude", "frequency"))
    if named == "wavelength":
        return ("Wavelength is the length of one whole wave, from one peak to the next, measured "
                "in metres. Frequency is how many of those waves pass a point each second, in "
                "hertz, and the two are locked together by the speed of the wave: wavelength is "
                "the speed divided by the frequency, so a 340 m/s sound at 50 Hz has a wavelength "
                "of 6.8 m. That is why a low note travels further round a corner than a high one.")
    if named == "amplitude":
        return ("Amplitude is how big the wave is - how far it swings from the middle - and it is "
                "what you hear as volume or see as brightness: a bigger amplitude is a louder "
                "sound or a brighter light. Frequency is the different thing, how many waves pass "
                "each second, measured in hertz, and that is the pitch. So a loud low note is big "
                "amplitude and small frequency, and turning the volume up changes the amplitude "
                "only.")
    return ("Frequency is how many times something happens in a second, measured in hertz: 50 Hz "
            "is fifty times a second. A sound's frequency is its pitch - 440 Hz is the A above "
            "middle C, and the higher the number the higher the note - while a radio station's "
            "100 MHz is a hundred million waves a second. It is the reciprocal of the period, so "
            "a wave that repeats every 0.02 seconds has a frequency of 50 Hz, and the wavelength "
            "is the speed divided by the frequency.")


ENTRIES.append(entry(
    "frequency",
    (("frequency", "hertz", "wavelength", "amplitude", "wave frequency",
      "amplitude of a wave", "amplitude of the wave", "wavelength of a wave",
      "wavelength of the wave", "frequency of a wave", "wave amplitude", "wave length",
      "peak to peak", "trough to trough"),
     _DEFINE + ("physics", "sound", "sound wave", "wave", "waves", "light", "radio", "signal",
                "measured in", "measure", "hz", "pitch", "loudness", "period", "unit")),
    _frequency_wavelength_amplitude,
    avoid=("wifi", "wi-fi", "broadband", "train", "trains", "bus", "buses", "tram", "how often",
           "hoover", "washing", "shower", "cleaning", "water the", "cut the grass", "floss",
           "dehumidifier"),
    # "what is the amplitude of a wave" reached main's "what is a wave" row, which never says the
    # word the person asked about
    bias=2))
ENTRIES.append(entry(
    "rock-cycle",
    (("rock cycle", "igneous", "sedimentary", "metamorphic", "types of rock", "type of rock"),
     _DEFINE + ("cycle", "formed", "how are", "how is", "made", "form", "forms", "examples",
                "example", "gcse", "difference between", "which")),
    "The rock cycle is rocks being made, broken down and made again. Magma cools to igneous rock "
    "such as granite or basalt; wind and water wear any rock into grains that settle, get "
    "squashed and cement into sedimentary rock such as limestone and sandstone; heat and pressure "
    "bake or squeeze rock into metamorphic rock such as marble, from limestone, or slate, from "
    "shale. Bury it deeper and it melts back to magma: the three types are one loop, not three "
    "separate things.",
    # "the rock" and "a rock" cannot be held out here: "the rock cycle" contains the first word
    # for word and the whole row refused its own question.
    # "rocking" cannot be held out here: the avoid words are matched on their forms too, and
    # "rocking" reaches "rock", which is in the key of the row itself.
    avoid=("my rock", "rock music", "rock band", "rock salt", "on the rocks", "rock the",
           "punk", "gig", "concert"),
    # main's "a rock is a solid piece of the earth" row answers "what is the rock cycle" and
    # "what are the three types of rock" as well, and it is the answer to a different question
    bias=6))
# Newton had three laws and main answered all three with the same sentence about the man:
# "Isaac Newton (1643-1727) worked out the three laws of motion". A law is not a biography, and
# "what does f=ma mean" and "what is acceleration" were shrugs while "what is momentum" was
# "that's beyond what I know well".
# One card holds all three laws, and the first sentence is the answer people read, so the law the
# line names comes first: "what is newtons first law" opened with "the second law is the useful
# one", which is somebody else's answer.
_NEWTON_SECOND = (
    "The second law is the useful one: force equals mass times acceleration, F = ma, so the same "
    "push moves a light thing quickly and a heavy one slowly, and a 1,000 kg car pushed with "
    "2,000 N accelerates at 2 m/s each second.")
_NEWTON_FIRST = (
    "The first law says a thing keeps still, or keeps going in a straight line at the same speed, "
    "unless a force acts on it - which is why a passenger is thrown forward when a bus brakes, and "
    "why a seatbelt is the force that stops them.")
_NEWTON_THIRD = (
    "The third law says every force has an equal force back the other way: you push the ground and "
    "it pushes you forward, a rocket throws gas down and the gas throws the rocket up.")
# "give me one example of newtons second law" opened with the first law, because "one" came
# before "second" in the line and the old pattern took any of one/two/three anywhere. A number
# word only counts next to the noun, and the ordinal on its own is the fallback.
_NEWTON_EACH = re.compile(
    r"\b(first|1st|second|2nd|third|3rd)\s+law\b"
    r"|\blaw\s+(?:number\s+)?(first|1st|second|2nd|third|3rd)\b"
    r"|\b(first|1st|second|2nd|third|3rd)\b")
_NEWTON_WORD = {"first": 0, "1st": 0, "second": 1, "2nd": 1, "third": 2, "3rd": 2}


def _newtons_laws(memory, understood):
    """The law the line names first, then the other two."""
    said = ""
    if isinstance(understood, dict):
        said = str(understood.get("text") or "")
    order = [_NEWTON_SECOND, _NEWTON_FIRST, _NEWTON_THIRD]
    match = _NEWTON_EACH.search(" " + said.lower() + " ")
    if match:
        word = match.group(1) or match.group(2) or match.group(3)
        which = _NEWTON_WORD.get(word)
        if which == 0:
            order = [_NEWTON_FIRST, _NEWTON_SECOND, _NEWTON_THIRD]
        elif which == 2:
            order = [_NEWTON_THIRD, _NEWTON_SECOND, _NEWTON_FIRST]
    return " ".join(order)
ENTRIES.append(entry(
    "newtons-laws",
    (("newton's second law", "newtons second law", "newton's first law", "newtons first law",
      "newton's third law", "newtons third law", "newton's laws", "newtons laws",
      "law of motion", "laws of motion", "second law of motion", "first law of motion",
      "third law of motion", "f=ma", "f = ma", "f ma", "force equals mass times acceleration",
      # the understanding layer splits "f=ma" into "f" and "ma", so the phrase never matches;
      # "mass times acceleration" is the same sentence written out
      "force equals mass times acceleration", "mass times acceleration", "force mass"),
     _DEFINE + ("second", "first", "third", "law", "laws", "force", "motion", "acceleration",
                "mass", "action", "reaction", "inertia", "example", "explain", "use")),
    _newtons_laws,
    # the man himself is another answer, and a car's newton-metres another
    avoid=("who was", "biography", "born", "died", "apple", "newton metres", "newton metre",
           "nm", "torque", "wrench", "newton abbot"),
    bias=2))
ENTRIES.append(entry(
    "acceleration",
    (("acceleration", "accelerate", "accelerating", "deceleration", "decelerating"),
     _DEFINE + ("physics", "calculate", "calculated", "measured in", "unit", "units",
                "formula", "m/s", "per second", "gravity", "speed", "velocity", "motion",
                "equation", "constant")),
    "Acceleration is how quickly speed changes, measured in metres per second squared: 2 m/s "
    "squared means each second it goes 2 m/s faster. A car from 0 to 60 mph in 9 seconds is "
    "accelerating at about 3 m/s squared, and gravity pulls a falling thing at about 9.8. "
    "Slowing down is acceleration the other way, so a brake is not a different idea, just one "
    "that points backwards.",
    # a car's own noise and a firm's growth are other questions
    avoid=("car makes", "noise", "noisy", "clunk", "judder", "judder", "engine", "clutch",
           "gear", "gears", "pedal", "bike", "insurance", "company", "startup", "business",
           "growth"),
    bias=1))
ENTRIES.append(entry(
    "momentum",
    (("momentum", "conservation of momentum"),
     _DEFINE + ("physics", "calculate", "measured in", "formula", "mass", "velocity", "speed",
                "collision", "collisions", "conserved", "unit", "units", "moving")),
    "Momentum is mass times velocity, measured in kg m/s, and it is what makes a lorry harder to "
    "stop than a bike going at the same speed. Its rule is that the total is unchanged in a "
    "collision: two skaters pushing apart, or a cue ball hitting another, end up with the same "
    "total momentum they started with - one gains what the other loses. That is why a big "
    "airbag spreads the change over longer, so the force on you is smaller.",
    # losing momentum with a diet or a habit is the everyday sense, and it has its own cards
    avoid=("diet", "exercise", "gym", "running", "training", "motivation", "motivated",
           "keeping going", "keep going", "study", "studying", "project", "habit", "losing",
           "lost my", "weight loss",
           # "i have no momentum at work" is a tired person, and a confident answer about kg m/s
           # is worse than the echo it got before; keep the momentum one to the physics.
           "at work", "no momentum", "momentum going", "keep momentum", "build momentum",
           "back on track"),
    bias=1))
# "what is speed" and "what is velocity" had no card either, and the two are one question: the
# difference is the whole answer, so one row holds both.
def _speed_and_velocity(memory, understood):
    """Velocity is a speed with a direction, and a line that asks about velocity gets that first."""
    said = _the_line(understood)
    if _names(said, ("velocity",)) == "velocity" and _names(said, ("speed",)) != "speed":
        return ("Velocity is how fast you are going and which way: 50 mph north is a velocity, "
                "and 50 mph on its own is a speed. So a car going round a roundabout at a steady "
                "30 mph has a constant speed and a changing velocity, because the direction keeps "
                "changing. Speed is distance over time, and average speed is the whole trip's "
                "distance over the whole time, which is why a two-hour journey with a stop does "
                "not average the speed you had on the motorway.")
    return ("Speed is how fast you are going, distance over time: 100 miles in two hours is "
            "50 mph. Velocity is that speed with a direction, so a car going round a roundabout "
            "at a steady 30 mph has a constant speed and a changing velocity. Average speed is "
            "the whole trip's distance over the whole time, which is why a two-hour journey with "
            "a stop does not average the speed you had on the motorway.")


ENTRIES.append(entry(
    "speed-and-velocity",
    (("speed", "velocity", "speed and velocity", "speed vs velocity", "average speed",
      "calculate average speed", "how do you work out average speed",
      "distance time graph", "distance-time graph"),
     _DEFINE + ("physics", "calculate", "calculated", "formula", "measured in", "unit", "units",
                "difference between", "average", "constant", "graph", "motion", "direction")),
    _speed_and_velocity,
    # broadband and film speeds are other questions
    avoid=("broadband", "wifi", "wi-fi", "internet", "download", "upload", "connection",
           # "speeding" cannot be a bare avoid word: its forms reach "speed", which is in this
           # row's own key, so the row refused "what is speed". The phrases below stay.
           "cycling", "running", "my run", "pace", "mph", "speed camera", "speed limit",
           "caught speeding", "got a speeding", "fixed penalty", "fast",
           # "what is a good serve speed in tennis" is coaching, not physics: the ball games
           # and the motor senses of speed have their own cards and want them back.
           "serve", "tennis", "golf", "swing", "bowling", "my car", "my bike", "top speed",
           "0-60", "quarter mile", "terminal velocity",
           # the speed OF a thing is that thing's card, not this definition: a light-speed fact
           # and the sound card both lost their line to this row on the first head (deck
           # single-612, "What's the speed of light, roughly?").
           "speed of light", "speed of sound", "of light", "of sound", "of a wave",
           "miles an hour", "km/h", "kilometres an hour", "kilometers an hour",
           # and any other "speed of <thing>" is that thing's own card - the cheetah, the trains,
           # the escape velocity - so the phrase itself stands this row down
           "speed of", "velocity of"),
    # main's speed-camera row answers "what is average speed" as well, and a school definition is
    # not a camera report: the two collide on the phrase "average speed"
    bias=3))


# The sky words and the body words: a solstice, an equinox, a crystal, a coral and an antibody
# were a shrug on main (89aed8ccb) - "I don't know enough to answer that honestly" - while the
# rest of the science deck answered. Each is keyed by the name of the thing, so the ask can
# arrive as "what is a solstice", "explain the equinox" or "what does crystal mean", and each
# holds out the everyday card that shares its word: a crystal ball and crystal healing, a coral
# necklace, an antibody test result, the longest day.
_SKY_ASK = ("what", "mean", "meaning", "definition", "explain", "why")
_RECORD_WORDS = ("biggest", "largest", "longest", "shortest", "highest", "lowest", "deepest",
                 "oldest", "how many", "how much", "how long", "what date", "which date",
                 "what time", "when is", "when does", "this year", "next year", "2025", "2026")

ENTRIES.append(entry(
    "solstice-what",
    (("solstice", "solstices", "summer solstice", "winter solstice", "midsummer"),
     _SKY_ASK),
    "A solstice is the day the sun is highest or lowest in the sky, which is why it is the "
    "longest day (about 21 June in the north) or the shortest (about 21 December): the Earth's "
    "tilt is leaning that half of the planet most towards or away from the sun.",
    avoid=_RECORD_WORDS + ("party", "festival", "celebrate", "bonfire", "sweden", "ritual",
                           "what happens at", "tradition"),
    ask=_SKY_ASK,
    bias=2))

ENTRIES.append(entry(
    "equinox-what",
    (("equinox", "equinoxes", "spring equinox", "autumn equinox", "vernal equinox",
      "autumnal equinox"), _SKY_ASK),
    "An equinox is the day the sun sits over the equator, so day and night are about twelve "
    "hours each everywhere: around 20 March and 22 September, which is when spring starts on one "
    "half of the planet and autumn on the other.",
    avoid=_RECORD_WORDS + ("celebrate", "ritual", "tradition", "pagan", "party", "festival"),
    ask=_SKY_ASK,
    bias=2))

ENTRIES.append(entry(
    "crystal-what",
    (("crystal", "crystals", "crystalline"), ("what", "mean", "meaning", "definition",
                                             "explain", "science", "structure")),
    "A crystal is a solid whose atoms sit in a regular repeating pattern, which is why it grows "
    "flat faces and sharp edges: salt, sugar, quartz and ice from the freezer are all crystals. "
    "The pattern decides the shape, so salt makes cubes and snowflakes make six-armed stars.",
    avoid=_RECORD_WORDS + ("ball", "meth", "healing", "heal", "chakra", "energy", "vibrations",
                           "shop", "pendant", "necklace", "decorative", "wine", "glasses",
                           "champagne", "clear", "grow", "growing", "make", "buy", "gift",
                           "battery", "watch", "screen", "lamp", "display"),
    ask=("what", "mean", "meaning", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "coral-what",
    (("coral", "corals", "coral reef", "coral reefs"), ("what", "mean", "meaning",
                                                       "definition", "explain")),
    "Coral is an animal, not a plant: a colony of tiny polyps that build a hard skeleton around "
    "themselves, and the reef is thousands of years of those skeletons stacked up. They get most "
    "of their food from algae living inside them, which is why they bleach white when the water "
    "gets too warm.",
    avoid=_RECORD_WORDS + ("necklace", "jewellery", "jewelry", "earring", "beads", "cut",
                           "bleaching", "bleached", "dying", "dead", "restore", "planting",
                           "pink", "red coral", "coral island", "coral sea"),
    ask=("what", "mean", "meaning", "definition", "explain"),
    bias=2))

ENTRIES.append(entry(
    "antibody-what",
    (("antibody", "antibodies"), ("what", "mean", "meaning", "definition", "explain")),
    "An antibody is a protein your immune system makes that sticks to one particular germ or "
    "chemical, marking it so the body can clear it, and it stays in the blood afterwards, which "
    "is why you usually do not get the same illness twice. That is also how a vaccine works: it "
    "shows you the shape first, so the antibodies are ready.",
    avoid=_RECORD_WORDS + ("test", "tests", "tested", "positive", "negative", "result",
                           "results", "level", "levels", "high", "low", "how long do they last",
                           "do i have", "should i get"),
    ask=("what", "mean", "meaning", "definition", "explain"),
    bias=2))


# The mechanics words a school lesson and a garage both use. Each was a shrug on main, and each
# shares its name with an everyday card: a lever arch file, camping gear, a car's torque figures,
# an engine oil's viscosity. The fence is the words beside the phrase, never the key itself.
# A school question about a thing is asked two ways: what it is, and how it works. The second
# half was missing, so "how does a lever work", "how does erosion happen" and "what makes rocks
# break up" reached the shrug while "what is a lever" was answered - the row's own subject was in
# the line, in the frame the ask makes. These are the explaining frames, and they are phrases
# rather than bare words on purpose: "how does" is not "how do i clean it", so a practical
# how-to still goes to the row that gives the steps.
_MEASURED = ("what", "mean", "meaning", "definition", "explain",
             "how does", "how do", "how do they", "how do you", "how it works", "how they work",
             "how it happens", "how that works", "what makes", "what causes", "what creates")

ENTRIES.append(entry(
    "lever-what",
    (("lever", "levers"), _MEASURED + ("physics", "simple machine", "machines")),
    "A lever is a bar that turns on a pivot, and it lets a small push move a big weight if the "
    "pivot sits close to the weight: a crowbar, a wheelbarrow, a see-saw and a bottle opener are "
    "all levers.",
    avoid=_RECORD_WORDS + ("arch file", "file", "folder", "handle", "tap", "gate", "door",
                           "buy", "shop", "pull"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "pulley-what",
    (("pulley", "pulleys"), _MEASURED + ("physics", "simple machine", "machines")),
    "A pulley is a wheel with a rope running over it: one changes the direction of a pull, so you "
    "pull down to lift a load up, and two together halve the force you need by doubling the rope. "
    "That is why a flagpole and a crane both use one.",
    avoid=_RECORD_WORDS + ("gym", "cable machine", "lat", "workout", "buy", "shop"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "gear-what",
    (("gear", "gears"), _MEASURED + ("physics", "simple machine", "machines", "ratio")),
    "A gear is a toothed wheel that turns another wheel, so turning one turns the other at a "
    "different speed or with more force: a small gear driving a big one gives slow, strong, and "
    "the other way round gives fast, weak, which is how a bike's gears work.",
    avoid=_RECORD_WORDS + ("camping", "fishing", "climbing", "walking", "kit", "stuff",
                           "what gear do i need", "what gear should i", "list", "buy", "shop",
                           "cheap", "best"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "pendulum-what",
    (("pendulum", "pendulums"), _MEASURED + ("physics", "clock", "swing")),
    "A pendulum is a weight on a string that swings to and fro at a steady rate, which is how "
    "clocks kept time for three hundred years: a longer string swings more slowly, and the weight "
    "hardly matters.",
    avoid=_RECORD_WORDS + ("buy", "shop", "gift", "decor", "art", "tattoo"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "torque-what",
    (("torque",), _MEASURED + ("physics", "car", "engine", "measured in", "unit", "formula")),
    "Torque is a turning force, measured in newton metres: force times the distance from the "
    "pivot. That is why a longer spanner loosens a tight bolt more easily, and why a car engine's "
    "torque figure tells you how hard it pulls low down rather than how fast it goes.",
    avoid=_RECORD_WORDS + ("figures", "bhp", "hp", "spec", "specs", "which car", "buy",
                           "setting", "wrench", "nm setting", "manual"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "buoyancy-what",
    (("buoyancy", "buoyant"), _MEASURED + ("physics", "float", "floats", "water")),
    "Buoyancy is the upward push a liquid or gas gives anything in it, equal to the weight of the "
    "fluid it pushes aside. A steel ship floats because the air inside makes it push aside more "
    "water than the ship itself weighs, while a solid lump of steel cannot.",
    avoid=_RECORD_WORDS + ("aid", "jacket", "life jacket", "swim", "swimming", "pool",
                           "boat", "buy"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "viscosity-what",
    (("viscosity", "viscous"), _MEASURED + ("physics", "oil", "liquid", "measured in")),
    "Viscosity is how thick a liquid is, or how hard it is to pour: honey is far more viscous "
    "than water. Engine oil is graded by it, so a 5W-30 flows easily when cold and stays thick "
    "enough when hot.",
    avoid=_RECORD_WORDS + ("oil", "engine oil", "grade", "5w", "10w", "car", "which oil",
                           "brand", "buy"),
    ask=_MEASURED, bias=2))


# Heat, light, sound and the sky's coordinates: the rest of the school words that were a shrug.
ENTRIES.append(entry(
    "convection-what",
    (("convection", "convection current", "convection currents"), _MEASURED),
    "Convection is heat carried by a moving fluid: warm air or water rises because it is lighter, "
    "cooler stuff sinks to take its place, and that loop is what heats a room and builds a "
    "thundercloud.",
    avoid=_RECORD_WORDS + ("oven", "fan oven", "microwave", "hob", "cooker", "setting", "bake",
                           "air fryer", "recipe"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "conduction-what",
    (("conduction", "thermal conduction"), _MEASURED),
    "Conduction is heat moving through a solid, passed from one particle to the next: a metal "
    "spoon left in soup gets hot to the handle while a wooden one does not, because metals carry "
    "heat well and wood does not.",
    avoid=_RECORD_WORDS + ("nerve", "hear", "hearing", "block", "heart", "bone", "headphones",
                           "audio", "earbuds"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "radiation-what",
    (("radiation",), _MEASURED + ("physics", "heat", "sun")),
    "Radiation is energy travelling as waves or particles, and heat that reaches us from the Sun "
    "crosses empty space that way, with nothing to carry it. The word also covers the harmful "
    "ionising sort, from X-rays and nuclear material, which is why those have safety limits.",
    avoid=_RECORD_WORDS + ("therapy", "cancer", "treatment", "exposure", "safe", "leak",
                           "nuclear", "radon", "wifi", "5g", "mobile phone", "microwave"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "refraction-what",
    (("refraction", "refract"), _MEASURED),
    "Refraction is light bending as it crosses from one material into another at an angle, "
    "because it changes speed: that is why a straw looks broken in a glass of water, and how a "
    "lens or a pair of glasses focuses light.",
    avoid=_RECORD_WORDS + ("eye", "eyes", "test", "glasses", "prescription", "laser", "surgery",
                           "cataract", "specs"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "decibel-what",
    (("decibel", "decibels", "db"), _MEASURED + ("sound", "loud", "noise")),
    "A decibel measures how loud a sound is, on a scale where each extra 10 dB is about ten times "
    "the power and roughly twice as loud to the ear: a whisper is about 30, ordinary talk about "
    "60, and 85 or more for long spells can damage hearing.",
    avoid=_RECORD_WORDS + ("tinnitus", "hearing", "ear", "headphones", "noise complaint",
                           "too loud", "how loud", "is it too"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "solvent-what",
    (("solvent", "solvents"), _MEASURED + ("chemistry", "dissolve")),
    "A solvent is the liquid something dissolves in, and the thing that dissolves is the solute: "
    "water is the usual solvent, while white spirit and acetone dissolve things water cannot, "
    "like paint and nail polish.",
    avoid=_RECORD_WORDS + ("abuse", "glue", "adhesive", "paint", "pvc", "cement", "cleaner",
                           "which solvent", "buy", "fumes"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "half-life-what",
    (("half life", "half-life", "half lives"), _MEASURED + ("physics", "radioactive",
                                                           "radiation", "chemistry")),
    "The half-life of a radioactive substance is the time it takes for half of it to decay: "
    "carbon-14's is about 5,730 years, which is how wood and bone are dated, and after ten "
    "half-lives almost none is left.",
    avoid=_RECORD_WORDS + ("game", "film", "movie", "series", "book", "song", "value",
                           "dose", "medicine", "drug", "tablet"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "radioactivity-what",
    (("radioactivity", "radioactive"), _MEASURED + ("physics", "atom", "atoms")),
    "Radioactivity is what unstable atoms give off, rays or particles, as they settle into a "
    "steadier state: it happens on its own and cannot be switched off. It powers a nuclear plant, "
    "and the tiny amount in a smoke alarm is what sets it off.",
    avoid=_RECORD_WORDS + ("test", "level", "levels", "safe", "radon", "leak", "waste",
                           "nuclear", "danger", "is it"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "equator-what",
    (("equator",), ("what", "mean", "meaning", "definition", "explain", "why")),
    "The equator is the imaginary line round the middle of the Earth, halfway between the poles "
    "at zero degrees latitude: day and night are about twelve hours each there all year, and the "
    "sun passes almost straight overhead.",
    avoid=_RECORD_WORDS + ("crossing", "ceremony", "cruise", "flight", "hotel", "visit"),
    ask=("what", "mean", "meaning", "definition", "explain"), bias=2))

ENTRIES.append(entry(
    "latitude-what",
    (("latitude",), ("what", "mean", "meaning", "definition", "explain", "why")),
    "Latitude is how far north or south of the equator a place is, in degrees from 0 at the "
    "equator to 90 at the poles: London is about 51 north, and your latitude is what sets how "
    "long the days are and how warm the place gets.",
    avoid=_RECORD_WORDS + ("of london", "of my", "what is my", "app", "gps", "phone"),
    ask=("what", "mean", "meaning", "definition", "explain"), bias=2))

ENTRIES.append(entry(
    "longitude-what",
    (("longitude",), ("what", "mean", "meaning", "definition", "explain", "why")),
    "Longitude is how far east or west of Greenwich a place is, measured in degrees up to 180 "
    "each way, and it is what sets your time zone. Sailors could find their latitude for "
    "centuries before they could find their longitude, which is why accurate clocks were so "
    "valuable.",
    avoid=_RECORD_WORDS + ("what is my", "app", "gps", "phone"),
    ask=("what", "mean", "meaning", "definition", "explain"), bias=2))

ENTRIES.append(entry(
    "nebula-what",
    (("nebula", "nebulae", "nebulae"), ("what", "mean", "meaning", "definition", "explain")),
    "A nebula is a cloud of gas and dust in space, either thrown off by a dying star or the stuff "
    "new stars are forming out of: the Orion Nebula is a star nursery you can pick out with your "
    "eyes as a fuzzy patch below the belt.",
    avoid=_RECORD_WORDS + ("film", "movie", "song", "game", "wallpaper", "buy"),
    ask=("what", "mean", "meaning", "definition", "explain"), bias=2))


# The living-things words a school lesson names, and the same everyday-card rule: a parasite on a
# pet, a niche in a wall, algae on a pond. habitat, ecosystem, food chain and photosynthesis were
# already answered on main; these were the shrugs.
ENTRIES.append(entry(
    "herbivore-what",
    (("herbivore", "herbivores"), _MEASURED),
    "A herbivore is an animal that eats only plants: a cow, a rabbit, a deer, a caterpillar. Its "
    "teeth grind and its gut is long enough to break down plant fibre, which is why it spends much "
    "of the day eating.",
    avoid=_RECORD_WORDS + ("dinosaur", "diet", "recipe", "vegan", "lose weight", "meal"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "carnivore-what",
    (("carnivore", "carnivores"), _MEASURED),
    "A carnivore is an animal that eats other animals: a lion, a cat, a heron, a spider. Most have "
    "sharp teeth or a beak for tearing meat, and a short gut, because meat is easier to digest than "
    "plants.",
    avoid=_RECORD_WORDS + ("dinosaur", "diet", "recipe", "cooking", "restaurant", "meal"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "omnivore-what",
    (("omnivore", "omnivores"), _MEASURED),
    "An omnivore eats both plants and animals: people, pigs, bears, crows and most gulls. That mix "
    "is why our teeth are partly sharp and partly flat, and why a varied diet suits us.",
    avoid=_RECORD_WORDS + ("dinosaur", "diet", "recipe", "meal"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "prey-what",
    (("prey",), _MEASURED),
    "Prey is the animal a predator hunts and eats: a rabbit for a fox, a zebra for a lion. The word "
    "is about the role in the food chain rather than the act of hunting: an animal can be prey to "
    "one thing and a predator of another.",
    avoid=_RECORD_WORDS + ("prey on my mind", "prey upon", "prayer", "pray", "church",
                           "religion", "fishing lure", "hunting"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "biome-what",
    (("biome", "biomes"), _MEASURED),
    "A biome is a large region with one climate and the plants and animals that go with it: "
    "rainforest, desert, grassland, tundra, coral reef. The same biome turns up on different "
    "continents, because it is the climate that decides it.",
    avoid=_RECORD_WORDS + ("minecraft", "game", "skin", "mod", "seed"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "niche-what",
    (("niche",), ("what", "mean", "meaning", "definition", "explain", "biology", "ecology")),
    "In biology, a niche is the job a species does where it lives: what it eats, when it is active, "
    "where it shelters and what eats it. Two species with the same niche in one place compete, and "
    "one usually wins or moves away.",
    avoid=_RECORD_WORDS + ("perfume", "fragrance", "scent", "business", "market", "shop",
                           "buy", "products"),
    ask=("what", "mean", "meaning", "definition", "explain"), bias=2))

ENTRIES.append(entry(
    "lichen-what",
    (("lichen", "lichens"), _MEASURED),
    "A lichen is not one thing but two living together: a fungus with algae or bacteria inside it, "
    "sharing food the algae make from light and shelter the fungus gives. That is why lichen grows "
    "on bare rock and why it is a sign of clean air.",
    avoid=_RECORD_WORDS + ("proxy", "sclerosis", "skin", "treatment", "cream", "planus",
                           "lichen planus", "genital", "mouth", "rash"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "plankton-what",
    (("plankton",), _MEASURED),
    "Plankton is the mass of tiny plants and animals drifting in water that cannot swim against the "
    "current: the plant sort makes oxygen and feeds everything up to the whales. Half the oxygen you "
    "breathe was made by it.",
    avoid=_RECORD_WORDS + ("spongebob", "film", "movie", "game"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "spore-what",
    (("spore", "spores"), _MEASURED),
    "A spore is a single cell that fungi, mosses and ferns release instead of seed, and it grows "
    "into a new plant if it lands somewhere damp enough. That is why mould spreads through a room "
    "as dust, and why moss appears on a wall.",
    avoid=_RECORD_WORDS + ("pore", "skincare", "skin", "cream", "acne"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "nectar-what",
    (("nectar",), _MEASURED),
    "Nectar is the sugary liquid flowers make to attract bees, butterflies and birds, and it is the "
    "payment for carrying pollen to the next flower. Honey is nectar that bees have concentrated.",
    avoid=_RECORD_WORDS + ("juice", "drink", "brand", "buy", "skincare", "face"),
    ask=_MEASURED, bias=2))


# Chemistry and space: the words a lesson names that main had nothing for, each fenced by the
# everyday card that shares it - an alloy wheel, car suspension, a proton therapy appointment,
# hair electrolysis, an electron microscope, a meteorite for sale.
ENTRIES.append(entry(
    "alloy-what",
    (("alloy", "alloys"), _MEASURED + ("chemistry", "metal", "metals")),
    "An alloy is a metal mixed with another element to make it stronger or easier to work: steel "
    "is iron with carbon, brass is copper with zinc, and solder is tin with lead or silver. The "
    "mix is melted together rather than just glued, so it behaves as one metal.",
    avoid=_RECORD_WORDS + ("wheel", "wheels", "rim", "rims", "car", "tyre", "tire", "scuff",
                           "paint", "gate", "roof", "fence"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "sublimation-what",
    (("sublimation", "sublime"), _MEASURED + ("chemistry", "physics")),
    "Sublimation is a solid turning straight into a gas without melting first: dry ice does it at "
    "room temperature, and so does the ice in a freezer over months, which is why ice cubes shrink. "
    "The reverse, gas straight to solid, is deposition.",
    avoid=_RECORD_WORDS + ("print", "printing", "shirt", "mug", "design", "psychology",
                           "meaning in"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "distillation-what",
    (("distillation", "distil", "distilled"), _MEASURED + ("chemistry", "water")),
    "Distillation is boiling a liquid off a mixture and condensing it back to a liquid somewhere "
    "cooler, which separates things that boil at different temperatures: spirit is distilled from "
    "a fermented mash, and distilled water is water with the minerals left behind.",
    avoid=_RECORD_WORDS + ("whisky", "whiskey", "gin", "vodka", "rum", "still", "buy",
                           "brand", "brewing"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "filtration-what",
    (("filtration", "filtrate"), _MEASURED + ("chemistry", "water")),
    "Filtration is passing a mixture through something with holes too small for the solid bits, so "
    "the liquid goes through and the solid stays behind: a coffee filter, a sieve in a flour mill, "
    "a kidney. It separates a solid from a liquid but not one dissolved chemical from another.",
    avoid=_RECORD_WORDS + ("pool", "pond", "tap", "water filter", "aquarium", "fish tank",
                           "coffee", "kettle", "buy"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "oxidation-what",
    (("oxidation", "oxidise", "oxidize"), _MEASURED + ("chemistry",)),
    "Oxidation is a substance reacting with oxygen: iron rusts, a cut apple browns, a fire burns, "
    "and the cells in your body get energy the same way. It does not always need a flame; slow "
    "oxidation is what rust and browning are.",
    avoid=_RECORD_WORDS + ("cholesterol", "antioxidant", "wine", "stainless", "rust", "rusty",
                           "metal", "apple", "avocado"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "combustion-what",
    (("combustion",), _MEASURED + ("chemistry",)),
    "Combustion is burning: a fuel reacts with oxygen and gives out heat and light, usually "
    "leaving carbon dioxide and water. It needs fuel, oxygen and enough heat to start, which is why "
    "a fire goes out when you cut off the air.",
    avoid=_RECORD_WORDS + ("engine", "car", "boiler", "spontaneous", "human", "fire", "stove",
                           "wood burner", "efficiency"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "proton-what",
    (("proton", "protons"), _MEASURED + ("physics", "chemistry", "atom")),
    "A proton is one of the particles in the middle of an atom, carrying a positive charge, and the "
    "number of them is what makes an element what it is: one is hydrogen, six is carbon, eight is "
    "oxygen.",
    avoid=_RECORD_WORDS + ("therapy", "cancer", "beam", "treatment", "nhs"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "electron-what",
    (("electron", "electrons"), _MEASURED + ("physics", "chemistry", "atom")),
    "An electron is the tiny negative particle that orbits the nucleus of an atom, and it is the "
    "one that moves when electricity flows. Its arrangement decides how an atom joins others, which "
    "is the whole of chemistry in one sentence.",
    avoid=_RECORD_WORDS + ("microscope", "configuration", "bill", "billing", "signature",
                           "document", "transfer", "app"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "exothermic-what",
    (("exothermic", "exothermic reaction"), _MEASURED + ("chemistry",)),
    "An exothermic reaction gives out heat as it happens, so the mixture gets warmer: burning, "
    "rusting and the reaction in a hand warmer are all exothermic. The opposite, one that takes "
    "heat in and feels cold, is endothermic.",
    avoid=_RECORD_WORDS + ("example", "examples", "gcse", "exam", "revision", "worksheet"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "suspension-what",
    (("suspension", "suspensions"), ("what", "mean", "meaning", "definition", "explain",
                                     "chemistry", "mixture")),
    "In chemistry a suspension is solid bits mixed through a liquid that do not dissolve and settle "
    "out if you leave it: muddy water, or flour stirred into water. Shaking it mixes it again, "
    "which is how it differs from a solution.",
    # a suspension bridge is a structure, not a mixture: the line named the subject and the
    # chemistry card answered a different question about the same word
    avoid=_RECORD_WORDS + ("car", "bike", "bicycle", "fork", "shock", "shocks", "spring",
                           "school", "work", "job", "driving", "licence", "license", "mot",
                           "bridge", "bridges", "viaduct", "tower", "towers", "span", "cables"),
    ask=("what", "mean", "meaning", "definition", "explain"), bias=2))

ENTRIES.append(entry(
    "colloid-what",
    (("colloid", "colloids", "colloidal"), _MEASURED + ("chemistry", "mixture")),
    "A colloid is a mixture where tiny particles of one substance are spread through another and "
    "stay spread: milk, fog, mayonnaise and paint are colloids. The particles are bigger than in a "
    "solution but too small to settle like a suspension.",
    avoid=_RECORD_WORDS + ("silver", "supplement", "oatmeal", "bath", "buy"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "covalent-bond-what",
    (("covalent bond", "covalent bonds", "covalent"), _MEASURED + ("chemistry", "bonding")),
    "A covalent bond is two atoms sharing a pair of electrons, which is how most of the molecules "
    "around you are held together: water, oxygen, sugar, plastic. Sharing is what makes a molecule "
    "stay one thing, rather than the ions of an ionic bond.",
    avoid=_RECORD_WORDS + ("gcse", "exam", "revision", "worksheet"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "electrolysis-what",
    (("electrolysis",), _MEASURED + ("chemistry",)),
    "Electrolysis is passing a current through a liquid or solution to drive a chemical change that "
    "would not happen on its own: it splits water into hydrogen and oxygen, and it is how aluminium "
    "is extracted and how metal is plated.",
    avoid=_RECORD_WORDS + ("hair", "hair removal", "beauty", "facial", "laser", "permanent",
                           "treatment", "salon", "painful"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "meteorite-what",
    (("meteorite", "meteorites", "meteor", "meteors"), _MEASURED),
    "A meteorite is a rock from space that has landed on the ground; while it is still burning "
    "through the air it is a meteor, or a shooting star. Most are chips off asteroids, and the "
    "biggest found weighs about 60 tonnes.",
    avoid=_RECORD_WORDS + ("for sale", "buy", "worth", "value", "price", "ring", "pendant",
                           "jewellery", "jewelry", "watch"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "pulsar-what",
    (("pulsar", "pulsars"), _MEASURED),
    "A pulsar is a tiny, extremely dense dead star that spins and sweeps a beam of radio waves past "
    "the Earth, so a telescope sees a regular pulse: some tick faster than a kitchen blender. They "
    "are accurate enough to be used as clocks.",
    avoid=_RECORD_WORDS + ("watch", "buy", "price", "casio", "seiko"),
    ask=_MEASURED, bias=2))


# The earth-science words. Four of these were answered wrongly on main rather than not at all -
# "what is weathering" got the climate card, "what is a rain shadow" the shadow-of-an-object card,
# "what is the gulf stream" a streaming service - so those carry bias=6 to beat the neighbour
# that scores, and their avoid lists hold the words of that neighbour rather than the word itself,
# because an avoid word that folds onto the row's own key zeroes the row.
# The sky as a person asks about it is not the science of rocks. `weathering` folds onto
# `weather`, so "whats the weather like" reached this row and was told how rock breaks up; the
# row keeps every line that says what it is about and stands down on the ones that ask about the
# weather where the person is.
THE_ROCK = frozenset("""weathering weathered erosion erode rock rocks soil science homework
geology""".split())
THE_SKY = frozenset("""weather forecast today tomorrow tonight weekend weekends outside""".split())


def _the_rock_and_not_the_sky(understood):
    """A line about weathering and erosion, not a line asking what the weather is doing."""
    words = set(understood.get("words") or ())
    if words & THE_ROCK:
        return True
    return not (words & THE_SKY)


ENTRIES.append(entry(
    "weathering-what",
    (("weathering",), _MEASURED + ("rock", "rocks", "science", "erosion")),
    "Weathering is rock being broken up where it sits, by rain, frost, wind, roots or weak acid, "
    "without being carried away. Erosion is the next step: the loosened pieces being moved "
    "somewhere else.",
    avoid=("forecast", "today", "tomorrow", "weekend", "rain today", "sunny", "climate",
           "cold", "hot", "snow"),
    guard=_the_rock_and_not_the_sky,
    # `_MEASURED` carries the explaining frames too ("how does", "what makes"), so "how does
    # weathering work" is answered as "what is weathering" is. The subject group is still the
    # weathering word itself, so this widens the ask and not the reach.
    ask=_MEASURED, bias=6))

ENTRIES.append(entry(
    "rain-shadow-what",
    (("rain shadow", "rain shadow desert"), _MEASURED + ("desert", "mountain", "mountains")),
    "A rain shadow is the dry side of a mountain range: air is forced up the windward side, drops "
    "its rain there, and comes down the other side warm and dry. Deserts like the one east of the "
    "Rockies sit in a rain shadow.",
    avoid=("of an object", "light", "length", "sunlight", "dark", "eye shadow", "eyeshadow"),
    ask=_MEASURED, bias=6))

def _the_ocean_current(understood):
    """"what is the gulf stream" is the Atlantic one; "what is a stream" is a video service."""
    # `words` is None when the matcher re-reads the line - with the words that were wrong repaired,
    # or as its subject alone - and hands a guard that reading. Reading a None as a list raised
    # TypeError, and an exception inside the base leaves the turn with no reply at all, so the
    # person got the search hedge instead of the answer: on 2026-11-11 "what is today's date" was
    # answered with "I don't know enough to answer that honestly" because the walk reached this
    # guard through a re-read line. The words of the line the guard is asked about are what it
    # wants, and a line with none is a line with none.
    words = understood.get("words") or ()
    return "stream" in words and "gulf" in words or "atlantic" in words


ENTRIES.append(entry(
    "gulf-stream-what",
    # "gulf" is a key word of its own so "what is the Atlantic current" reaches this card too, and
    # the guard keeps "what is a gulf" and "what is a stream" away from it.
    (("gulf stream", "gulf", "atlantic current"),
     _MEASURED + ("ocean", "atlantic", "weather", "climate")),
    "The Gulf Stream is a fast warm current that carries water from the Gulf of Mexico up the east "
    "coast of America and across the Atlantic. Its heat is why Britain and Ireland are milder than "
    "the same latitude in Canada.",
    # "streaming" cannot be fenced here: it folds onto this row's own key word "stream" and that
    # zeroes the row. The guard does that job instead, because it needs gulf or atlantic.
    avoid=("netflix", "series", "tv", "watch", "service", "subscription", "subscribe",
           "film", "movie", "shows", "boxset"),
    ask=_MEASURED, guard=_the_ocean_current, bias=6))

ENTRIES.append(entry(
    "tide-pool-what",
    (("tide pool", "tide pools", "rock pool", "rock pools"), _MEASURED),
    "A tide pool is the pocket of seawater left behind in the rocks when the tide goes out, and it "
    "is a small sheltered world: anemones, limpets, crabs and weed that survive being cut off until "
    "the water comes back.",
    ask=_MEASURED, bias=3))

ENTRIES.append(entry(
    "sediment-what",
    (("sediment", "sediments"), _MEASURED),
    "Sediment is the loose material that settles at the bottom of water or is dropped by wind and "
    "ice: sand, mud, grit and bits of shell. Pressed together over millions of years, sediment "
    "becomes sedimentary rock like sandstone and chalk.",
    avoid=_RECORD_WORDS + ("wine", "bottle", "coffee", "filter", "sediment in my"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "magma-what",
    (("magma",), _MEASURED),
    "Magma is molten rock under the ground; once it reaches the surface it is called lava. It forms "
    "where rock gets hot enough to melt, and because it is lighter than the rock around it, it rises.",
    avoid=_RECORD_WORDS + ("film", "movie", "game", "band", "album", "poem"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "lava-what",
    (("lava",), _MEASURED),
    "Lava is molten rock that has come out of a volcano onto the surface; the same stuff underground "
    "is magma. It cools into rock, and runny lava flows far while thick lava piles up near the vent.",
    avoid=_RECORD_WORDS + ("lamp", "lamps", "soap", "buy", "colour", "color"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "earthquake-what",
    (("earthquake", "earthquakes"), _MEASURED),
    "An earthquake is the ground shaking when two slabs of the Earth's crust slip past each other "
    "and the energy built up is released as waves. The slipping happens at a fault, and the shaking "
    "is strongest near it.",
    avoid=_RECORD_WORDS + ("insurance", "cover", "damage", "claim", "building", "house",
                           "safe", "kit"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "sea-breeze-what",
    (("sea breeze", "sea breezes", "land breeze"), _MEASURED),
    "A sea breeze is the cool air blowing in off the sea on a sunny afternoon, because land heats "
    "faster than water, so the warm air over the land rises and the cooler sea air moves in to "
    "replace it. At night the pattern reverses as the land cools faster.",
    avoid=_RECORD_WORDS + ("hair", "skin", "perfume", "candle", "candle scent", "air freshener"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "precipitation-what",
    (("precipitation",), _MEASURED + ("weather", "rain", "water cycle")),
    "Precipitation is water falling out of the sky - rain, snow, sleet or hail - when droplets in a "
    "cloud join up until they are too heavy to stay up. It is one step of the water cycle, after "
    "evaporation and condensation.",
    avoid=_RECORD_WORDS + ("chemistry", "reaction", "test", "blood", "chemical"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "carbon-footprint-what",
    (("carbon footprint", "carbon footprints"), _MEASURED),
    "A carbon footprint is the total greenhouse gas your choices add up to in a year, counted as "
    "carbon dioxide: heating, electricity, flights, car trips, the food and things you buy. A "
    "typical UK footprint is around 10 tonnes a year, and flying and meat are usually the biggest "
    "single items.",
    avoid=_RECORD_WORDS + ("calculate", "calculator", "offset", "offsets", "reduce",
                           "how do i"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "clay-what",
    (("clay",), _MEASURED + ("soil", "rock", "science")),
    "Clay is a soil and rock material made of microscopic flat particles that pack tightly, so it "
    "holds water and feels sticky when wet and hard when dry. Pots and bricks are made from it "
    "because it can be shaped wet and keeps that shape when fired.",
    avoid=_RECORD_WORDS + ("pigeon", "target", "shooting", "tennis", "court", "face mask",
                           "mask", "skin", "hair", "paint", "cat litter"),
    ask=_MEASURED, bias=2))

ENTRIES.append(entry(
    "fault-line-what",
    (("fault line", "fault lines", "geological fault"), _MEASURED),
    "A fault line is a crack in the Earth's crust where the rock on either side has moved, and it "
    "is where most earthquakes happen because the two sides keep slipping. The San Andreas fault is "
    "the best known.",
    avoid=_RECORD_WORDS + ("relationship", "team", "argument", "blame", "politics", "party"),
    ask=_MEASURED, bias=2))

# "does magnesium help you sleep" was the general sleep-habits list and "do sleep gummies work"
# was a search hedge: the row that answers sleep at night never reads the name of a pill, so the
# thing a person is holding in their hand was never the subject. The supplements people ask about
# by name each have their own line, and the habit advice is the one thing all of them are worth.
# The supplements answer is the same three facts in a different order, and a person who names
# valerian should not hear about magnesium first. Two sentences have to do it: @clean-bench
# measured the old paragraph at 159 words in six sentences, and STYLE.md asks for one to three.
_SLEEP_MAGNESIUM = ("Magnesium has only a little evidence behind it, and only if you are short "
                    "of it: the glycinate or citrate sorts, not the oxide.")
_SLEEP_VALERIAN = "Valerian and the herbal teas do very little in trials."
_SLEEP_GUMMIES = "The gummies are usually a low dose of melatonin or an antihistamine."
_SLEEP_HABIT = ("What beats them is a steady wake-up time, no caffeine after early afternoon, "
                "and getting up rather than lying there.")
_SLEEP_CHILD = "For a child, ask a pharmacist or the GP first."
_SLEEP_CHILD_WORDS = (" child", "kids", "kid ", "my son", "my daughter", "baby", "toddler",
                      "teenager", "my boy", "my girl", " 8 year", " 9 year", " 10 year",
                      " 11 year", " 12 year")


def _sleep_supplements_reply(memory, understood):
    """The supplement the line names is answered first; the habit is always the last word."""
    clean = " " + (understood.get("clean") or understood.get("text") or "").lower() + " "
    for word in _SLEEP_CHILD_WORDS:
        if word in clean:
            # a child's question is the pharmacist's before it is the supplement's
            return " ".join([_SLEEP_CHILD, _SLEEP_MAGNESIUM, _SLEEP_HABIT])
    if "valerian" in clean or "herbal" in clean or "tea" in clean:
        order = (_SLEEP_VALERIAN, _SLEEP_MAGNESIUM, _SLEEP_GUMMIES)
    elif "gumm" in clean or "melatonin" in clean or "antihistamine" in clean:
        order = (_SLEEP_GUMMIES, _SLEEP_MAGNESIUM, _SLEEP_VALERIAN)
    else:
        order = (_SLEEP_MAGNESIUM, _SLEEP_VALERIAN, _SLEEP_GUMMIES)
    return " ".join(order + (_SLEEP_HABIT,))

ENTRIES.append(entry(
    "sleep-supplements",
    (("magnesium", "valerian", "sleep gummies", "gummies", "herbal sleep", "sleep supplement",
      "sleep supplements", "supplements for sleep", "sleep aid", "sleep aids", "natural sleep",
      "natural remedy", "what can i take to sleep", "anything i can take to sleep",
      "something to help me sleep", "something to help me sleep", "sleeping remedy",
      "sleep remedy"),
     ("sleep", "sleeping", "asleep", "help", "helps", "work", "works", "take", "taking",
      "bed", "night", "nights", "insomnia", "better", "anything", "supplement", "tablet",
      "tablets", "pill", "pills")),
    # "help you sleep", "good for sleep" and "helps me sleep" are how people ask about a bath, a
    # walk and a book as well as a tablet, so those shapes are only this row's when the line also
    # holds something you swallow: "is a hot bath good for sleep" and "does exercise help you
    # sleep" were both the magnesium paragraph, and the bath and the exercise cards are better.
    ask=("take", "taking", "tablet", "tablets", "pill", "pills", "supplement", "supplements",
         "dose", "dosage", "gummy", "gummies", "magnesium", "valerian", "herbal", "remedy",
         "remedies", "aid", "aids", "anything", "something", "worth", "try", "trying",
         "help you sleep", "helps you sleep", "help me sleep", "good for sleep",
         "good for sleeping"),
    reply=_sleep_supplements_reply,
    bias=1,
    # the magnesium in food, a cramp, a child, a pregnancy and melatonin each keep their own row
    avoid=("foods", "food", "diet", "rich in", "deficiency", "deficient", "how much magnesium",
           "cramp", "cramps", "restless legs", "melatonin",
           "pregnant", "pregnancy", "breastfeeding")))

ENTRIES.append(entry(
    "vacuum-what",
    (("vacuum",), _MEASURED + ("physics", "space")),
    "In physics a vacuum is a space with no matter in it at all, or as close as anyone gets: there "
    "is no air in space, and a thermos flask keeps its heat by holding a vacuum between two walls. "
    "It is also why a vacuum cleaner's fan can push air in.",
    avoid=_RECORD_WORDS + ("cleaner", "cleaners", "hoover", "bag", "filter", "robot", "cordless",
                           "buy", "best", "which"),
    ask=_MEASURED, bias=4))
# --- a phrase from the news that people are handed without a number -------------------------
# "what is a carbon footprint" was a search hedge. The commonest misunderstanding is that it is
# mostly about flights and plastic bags, so the answer says what it counts and where the weight
# actually sits.
ENTRIES.append(entry(
    "carbon-footprint",
    (("carbon footprint", "carbon footprints", "my carbon footprint", "co2 footprint",
      "carbon emissions", "my emissions", "greenhouse gas"),
     ("what is", "whats", "what does", "mean", "means", "reduce", "lower", "cut", "shrink",
      "how big", "size", "offset", "calculate", "work out", "biggest", "how much", "co2")),
    "A carbon footprint is the total greenhouse gas a person, a household or a product causes, "
    "counted in kilograms of carbon dioxide equivalent over a year. For a household in the UK it "
    "is roughly 8 to 10 tonnes, and the weight is not where people think: heating and electricity "
    "and car travel are the bulk of it, while a flight is big in one hit and a plastic bag is "
    "almost nothing. The changes that move it most are the boring ones - a heat pump or good "
    "insulation, less red meat and dairy, fewer and shorter flights, a smaller car - and offsetting "
    "does not cancel them out.",
    # a footprint in sand, a tyre footprint and a data footprint are other things
    avoid=("footprint in", "sand", "tyre", "tire", "shoe", "data footprint", "building footprint",
           "boot", "animal", "dinosaur", "imprint"),
    bias=1))
