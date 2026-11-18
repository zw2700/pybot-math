"""The family rows from "the questions a parent asks in the first years" to the end.

`family.py` went over the publisher's 1 MiB file limit (1,051,549 bytes) and the world then
refused every PR whose clone carried it, with `{"error": "file too large: bot/knowledge/family.py
is over 1048576 bytes"}`, so no lane could change the family cards at all. The rows are data
rather than code and they are the end of the list, so they move as one block, the way
`home_craft.py`, `cooking_more.py` and `cooking_entries.py` hold the rows for their own files.

Nothing about the rows changed. `family.py` imports this file at the end, where these rows used
to stand, and extends its own list with this one, so `family.ENTRIES` holds the same entries in
the same order as before. The helpers this block defines (`_school_date`, `_half_term`,
`_said_date`, ...) travel with it; the three names it borrows from `family.py` are imported by
name, which works because `family.py` only imports this module after every helper it needs is
already defined, and this module has no ENTRIES of its own for the registry to read as a domain.
"""

import datetime
import re

from .lookup import entry
from .family import (_ADULT_RELATION, _a_phone_rule_and_an_age, _a_teenager_is_named,
                     _the_child_pronouns)

ENTRIES = []

# --- someone of theirs is going to live in another country --------------------------------
# The subject is the person going, not the place. "my daughter is leaving for australia" and
# "my brother is emigrating" were answered "Noted: your daughter is leaving for australia" - a
# receipt - and "my daughter is off to australia in september" and "my mate is going to
# australia" got the picks for a holiday in Australia ("Sydney for the harbour and the
# beaches"), which is advice for the wrong person about the wrong thing.
#
# A leaving word and a person are not enough on their own: "my daughter is leaving school in
# july", "my husband is leaving his job", "my sister is leaving her husband" and "my dad is
# moving to leeds" are all a person and a leaving word, and none of them is somebody going to
# live in another country. The line has to say another country - a country named, or one of the
# words that means leaving this one - so that is the guard, and the leaving phrases can stay
# wide because of it.
_LEFT_THE_COUNTRY = re.compile(
    r"\b(?:emigrat\w*|abroad|overseas|moving country|leaving the country|left the country)\b")


def _another_country_is_in_the_line(understood):
    """True when the line says the person is going to some other country, not just away.

    A country's name is the plainest way to say it, so the names the knowledge base already
    holds are the test rather than a second list to keep. "moving to" with a town in it is a
    move down the road: the line has to name somewhere in another country, or say `abroad`,
    `overseas` or `emigrating`.
    """
    low = " " + " ".join(str(part or "") for part in
                         (understood.get("text"), understood.get("clean"))).lower() + " "
    if _LEFT_THE_COUNTRY.search(low):
        return True
    from . import geography  # noqa: PLC0415 - loaded here so the row costs nothing until asked

    return any((" " + name + " ") in low for name in geography.COUNTRIES)


ENTRIES.append(entry(
    "a-person-going-to-live-abroad",
    (("leaving for", "leaving to", "leaves for", "is leaving", "left for", "is off to",
      "off to live", "moving to live", "moving to", "is moving to", "going to live in",
      "going to live there", "going to live abroad", "emigrating", "is emigrating",
      "emigrated", "has emigrated", "moving abroad", "is moving abroad", "moving overseas",
      "is moving overseas", "going abroad", "is going abroad", "going overseas",
      "going travelling", "going traveling", "is going travelling", "leaving the country",
      "moving away to", "has left the country", "left the country"),
     ("daughter", "son", "child", "kid", "kids", "mum", "mom", "mam", "mother", "dad",
      "father", "brother", "sister", "nan", "gran", "granny", "grandma", "grandad",
      "grandpa", "aunt", "uncle", "cousin", "niece", "nephew", "grandson", "granddaughter",
      "family", "best friend", "mate", "friend", "girlfriend", "boyfriend", "partner",
      "fiance", "fiancee", "husband", "wife")),
    "Say the hard thing while they are still here rather than at the airport: one evening "
    "just the two of you, and tell them what they have been to you. Then put the contact in "
    "the diary before they go - a real time each week rather than 'we'll see'. The first "
    "month after is the quiet one, so have one thing in it that is only yours.",
    # a holiday is not a life abroad ("my nan is off to spain for a week"), a move down the
    # road is not another country, and a care home is neither
    guard=_another_country_is_in_the_line,
    avoid=("holiday", "holidays", "for a week", "for a fortnight", "for two weeks",
           "for ten days", "for a month", "on holiday", "coming back", "comes back",
           "visiting", "care home", "nursing home", "sheltered", "a flat", "a house",
           "a bungalow", "new place", "next door", "same town", "the city",
           # a move of their own, down the road, or into somebody's flat is not another country
           "own flat", "own place", "own house", "his own", "her own", "their own",
           "down the road", "moving in with", "in with his", "in with her", "in with us"),
    bias=1))

# --- the questions a parent asks in the first years, which had no row at all -----------
# All six of these were a shrug or a wrong answer on main: "how much should a newborn
# sleep" got the under-three-months dosing rule, "how do i get my baby to take a bottle"
# got the flight-liquids card, "how do i help my child with anxiety" and "how do i explain
# money to my kid" got nothing, "how do i choose a school for my child" got the email to
# the teacher, and "how do i talk to my son about puberty" got the how-to-end-a-chat line.
# Each is one answer, keyed on the meaning rather than the wording, and each stands down
# for the neighbours that own the sick-child, the school and the shop versions.
ENTRIES.append(entry(
    "baby-refuses-the-bottle",
    (("bottle", "bottles", "teat", "teats", "expressed milk", "formula", "bottle feeding",
      "bottle fed", "take a bottle", "take the bottle"),
     ("take", "takes", "taking", "took", "refuse", "refuses", "refusing", "refused", "wont",
      "won't", "will not", "wont take", "won't take", "get my baby", "get him", "get her",
      "start", "starting", "switch", "switching", "introduce", "introducing", "combine",
      "combination", "back to work", "returning to work", "return to work", "how do i")),
    ("Give it when the baby is calm rather than hungry, and have somebody else offer it - a "
     "baby who can smell milk will hold out for the breast. Warm the teat and use a slow-flow "
     "one, hold them fairly upright and keep the bottle level so the milk comes at their pace "
     "rather than pouring in. Offer one bottle a day for a week without forcing it, and change "
     "the teat, the room and the person holding them before you decide they will not take one. "
     "If they are under six weeks old, are losing weight or the nappies are dry, ring the health "
     "visitor rather than pushing on."),
    bias=1,
    # A bottle is a thing as well as a feed: "how do i remove glue from a glass bottle" was
    # answered with this row on the words bottle and how do i. The line has to name the baby.
    ask=("baby", "babies", "newborn", "newborns", "infant", "little one", "my son", "my daughter",
         "my child", "my kid", "weeks old", "week old", "month old", "months old", "breastfed",
         "breastfeeding", "nursery", "childminder", "him", "her",
         # "how do i introduce a bottle" and "how do i start formula" name the feed being
         # started and no baby at all, so the baby-word gate stood this row down: the bottle
         # line got the scan picture and the formula line got the spreadsheet card, off the
         # word "formula". Introducing the bottle *is* what this row answers.
         "introduce a bottle", "introducing a bottle", "introducing the bottle",
         "introduce the bottle", "introduce bottles", "introducing bottles",
         "start a bottle", "start bottles", "start formula", "introduce formula",
         "introducing formula", "introduce a formula", "introducing a formula",
         "introduce the formula", "a formula", "the formula",
         "switch to formula", "switching to formula",
         "combination feed", "combination feeding", "combi feed", "combi feeding",
         "mixed feeding", "top up with formula"),
    # a baby who has stopped feeding is the under-three-months red flag, and a bottle to
    # sterilise, wash, pack or buy is a different question again
    avoid=("not feeding", "isnt feeding", "isn't feeding", "refusing feeds", "reduced feeds",
           "not interested in feeds", "too sleepy to feed", "not taking feeds", "stopped feeding",
           "losing weight", "not gaining", "weaker", "floppy", "limp", "fever", "temperature",
           # Ending the bottle is the opposite question and the child row below owns it:
           # "how do i stop my baby taking a bottle" was answered here with how to get a
           # baby to take one. "stopped taking" stays out, because a baby who stopped is a
           # baby refusing.
           "stop my baby taking", "stop him taking", "stop her taking",
           "stop my baby having", "stop him having", "stop her having",
           # the cup, the night feed and the toddler coming off it are the bottle-ending row
           "cup", "cups", "sippy cup", "free flow cup", "to a cup", "night feed", "night feeds",
           "off the bottle", "off bottles", "toddler",
           "stop giving", "stop the bottle", "stop using", "give up the bottle",
           "drop the bottle", "dropping the bottle", "coming off the bottle",
           "come off the bottle", "off the bottle",
           # "how do i introduce a bottle at night" is the night-feed row's question, which
           # ends the feed rather than starting one, and "at night" is how people say it
           "at night", "night time", "night-time", "nighttime", "overnight",
           # a bottle offered to a cat is nonsense in every reading: the pet-intro cards and
           # the two-people script are both wrong, and a punt is better than advice on teats
           "dog", "dogs", "cat", "cats", "kitten", "kittens", "puppy", "puppies", "pet", "pets",
           "water bottle", "gym", "flight", "flying", "liquids", "100ml", "100 ml",
           "sterilise", "sterilizer", "sterilise", "steriliser", "washing", "wash", "clean",
           "pump", "breast pump", "which bottle", "best bottle", "brand", "cost", "buy",
           "how many bottles", "how many",
           # "a formula" is a maths word too, and a key phrase is read wherever it appears in
           # the line: adding "a formula" and "the formula" for "how do i introduce a formula"
           # also took "the formulas" and "rearrange a formula", so a maths revision question
           # was answered with how to offer a bottle and the maths row that owns it never got
           # the turn. A maths word means the formula is the one on the sheet. The words are
           # the ones a maths or spreadsheet line carries and a feed line never does; a maths
           # word reaches only its own line, so nothing that names a feed stands down.
           "maths", "math", "mathematics", "algebra", "equation", "quadratic", "trigonometry",
           "geometry", "percentages", "gcse", "a level", "physics", "chemistry",
           "revision", "revising", "revise", "coursework", "exam", "exam paper", "mock exam",
           "spreadsheet", "excel", "autosum", "rearrange", "formula sheet",
           "learn the formula", "remember the formula") + _ADULT_RELATION,
))
# A child with a grown-up's age on them, or a grown-up's life, is not the worry this card is
# written for. "i keep worrying about my daughter, shes 19 and out all night" was answered with
# the keep-bedtime-and-meals card and its line about school, which is a young child's answer to
# a parent's worry about an adult. Eighteen and over is an adult, and a life of their own -
# university, their own place, driving, staying out - says the same thing without an age.
_GROWN_UP_SAID = ("out all night", "boyfriend", "girlfriend")
# A figure is only an age when the line says so. Counting every number as one took the card away
# from two ordinary lines - "my son is worried about 20 minutes of homework" and "my 9 year old is
# worried about 45 minutes of swimming" - so a number counts in one of two places: attached to
# "years old", or said of the person ("my daughter is 21", "he turned 21"). Minutes, months and
# weeks are not ages however they are written.
_AGE_FIGURE = r"(?:1[89]|[2-9][0-9])"
_AGE_SPELLED = (r"(?:eighteen|nineteen|twenty|thirty|forty|fifty|sixty"
                r"(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?)")
# A figure said of the person is still not an age when a unit follows it: "my son is 19 months"
# is a baby and "my son is 20 minutes late home" is not a grown-up, and both were read as ages.
_NOT_A_UNIT = (r"(?!\s*(?:min|mins|minute|minutes|hour|hours|hr|hrs|day|days|week|weeks"
               r"|month|months)\b)")
_ADULT_AGE = re.compile(
    # "my daughter is 21", "my son is now thirty", also the repair reading's spelled form
    r"\b(?:is|are|was|were|turns?|turned|now)\s+(?:" + _AGE_FIGURE + "|" + _AGE_SPELLED + r")\b"
    + _NOT_A_UNIT +
    # "my 21 year old", "twenty one years old"
    r"|\b(?:" + _AGE_FIGURE + "|" + _AGE_SPELLED + r")\s*(?:years?|yrs?)(?:\s*old)?\b")


def _the_child_is_not_grown(understood):
    """False when the child the line is about has a grown-up's age or life on them."""
    if not isinstance(understood, dict):
        return True
    words = [str(word).lower() for word in understood.get("words") or ()]
    text = " ".join(words)
    if any(said in text for said in _GROWN_UP_SAID):
        return False
    return not _ADULT_AGE.search(text)


ENTRIES.append(entry(
    "child-worry",
    (("anxious", "anxiety", "worried", "worry", "worries", "worrying", "nervous", "scared",
      "frightened", "panic", "panics", "panicking", "overthinking", "on edge", "stressed",
      "reassurance", "reassure", "reassuring"),
     ("child", "children", "kid", "kids", "son", "daughter", "boy", "girl", "toddler",
      "teenager", "teen", "year old", "years old", "little one", "my little", "school age")),
    ("Name it and keep the day predictable: \"you've been worrying about that a lot\" does more "
     "than \"don't worry\", because the worry is real to them and being told it is nothing "
     "teaches them to hide it. Then take one small step towards whatever they are avoiding and "
     "praise the step rather than the result, and keep bedtime and meals at the same time so "
     "their body has something steady to settle on. If worry is stopping them going to school, "
     "eating or sleeping for more than a couple of weeks, ask the GP about children's mental "
     "health services."),
    bias=1,
    # school nerves have their own answer, the exams another, and an adult's own anxiety is
    # not a parenting question at all
    avoid=("school", "class", "teacher", "lesson", "lessons", "exam", "exams", "test", "tests",
           "sats", "gcse", "a level", "revision", "i am anxious", "im anxious", "i'm anxious",
           "i feel anxious", "my anxiety", "i am worried", "im worried", "i'm worried",
           "i feel worried", "i get anxious", "i have anxiety", "about myself",
           "panic attack", "panic attacks") + _ADULT_RELATION,
    guard=_the_child_is_not_grown,
))

ENTRIES.append(entry(
    "talk-about-puberty",
    (("puberty", "period", "periods", "bodies", "body changes", "body changing", "growing up",
      "sex", "sex education", "birds and bees", "voice breaking", "breasts", "wet dream",
      "wet dreams", "underarm hair", "pubic hair", "hormones",
      # not a bare "changes": its loose form is "change", and "how often should i change my
      # toothbrush" was answered with this card on "change" and "should i"
      "body changes", "the changes", "what changes"),
     ("talk", "talking", "tell", "explain", "discuss", "bring up", "what do i say",
      "what should i say", "how do i", "how to", "start", "started", "starting", "when",
      "what age", "old enough", "should i")),
    ("Start earlier and in smaller pieces than feels comfortable: the changes usually begin "
     "around nine or ten, and a first period comes about two years after the breasts start to "
     "develop, so the explaining has to be done before it happens. Use the proper words, keep it "
     "to a few minutes at a time in the car or at bedtime, and cover both sexes so a boy hears "
     "about periods and a girl about wet dreams. A good book left where they will find it does "
     "half the work, and \"ask me anything, including the embarrassing bits\" keeps the door "
     "open."),
    bias=1,
    # the subjects are the same whatever they are called; a line that names none of them is not
    # this card, which is how a toothbrush got here
    ask=("puberty", "period", "periods", "bodies", "body", "growing up", "grow up", "sex",
         "sex education", "birds and bees", "voice", "breasts", "wet dream", "hair",
         "hormones", "changes", "girl", "girls", "boy", "boys", "son", "daughter", "child",
         "children", "kid", "kids", "teenager", "teen"),
    # a period that is late, painful or heavy is a health question, and the adult versions of
    # the same words are the health domain's
    avoid=("late", "missed", "pain", "painful", "cramps", "cramping", "heavy", "bleeding",
           "spotting", "irregular", "contraception", "pregnant", "pregnancy", "test",
           "my period", "periods stopped", "no period", "first period", "period after",
           "pain during sex", "bleed after sex", "stds", "sti", "condom", "condoms",
           # "breasts" is a cooking word too, and with "how do i" in the second group this card
           # answered "how do i keep chicken breast juicy" with the puberty talk. Anything that
           # says cook, roast or pan is the kitchen's, whatever it names.
           "chicken", "turkey", "cook", "cooks", "cooking", "cooked", "roast", "roasted",
           "bake", "baked", "juicy", "moist", "tender", "oven", "grill", "grilled", "fry",
           "fried", "pan", "boil", "poach", "recipe", "dinner", "sausages", "breast of",
           # a bottle of milk for a baby is the freshness question, not a talk about growing
           # up: "how do i store breast milk" and "how do i freeze breast milk" were answered
           # with this card because "breast" and "how do i" were the only words they shared
           "breast milk", "breastmilk", "expressed milk", "formula milk", "pumped milk",
           # "body" is in the key, so "how do i get rid of body fat" was answered with the
           # how-to-talk-about-puberty card. Fat and calories are the health domain's; the
           # shape words are only the shape asks, not the bare "weight", because "how do i
           # talk to my son about his body changing and weight" is this card - the weight is
           # one of the things being talked about, not a competing topic.
           "fat", "fats", "calories", "diet", "dieting", "overweight", "obese",
           "bmi", "body fat", "belly", "lose weight", "losing weight", "weight loss",
           "lose a stone", "put on weight", "burn", "burning"),
))


# A shared house is its own set of questions, and the food one had no answer at all: "how do i
# stop my flatmate eating my food" was a search punt.
ENTRIES.append(entry(
    "flatmate-food",
    (("flatmate", "flatmates", "housemate", "housemates", "roommate", "roommates", "house share",
      "house mate", "houseshare"),
     ("eating", "eats", "ate", "eaten", "taking", "takes", "took", "stealing", "steals", "stolen",
      "food", "fridge", "cupboard", "leftovers", "labelled", "label", "share", "sharing")),
    ("Label a shelf and one tub of your own, then say it once, face to face: \"I'm happy to share "
     "milk and bread, but I'd rather the rest was mine\" is something a person can agree to, and a "
     "note on the fridge is not. Agree a shared shelf for the things you both use, and if it "
     "carries on, ask to split the shopping bill rather than policing the fridge."),
    # the rest of a shared house is other answers: rent, noise, mess, and a flatmate who is low
    avoid=("rent", "deposit", "bills", "bill", "pays", "paid", "loud", "noise", "music", "party",
           "clean", "cleaning", "washing up", "mess", "dirty", "smells", "smell", "depressed",
           "lonely", "moving out", "moves out", "mould", "damp", "landlord")))

# --- a teenager who will not get up --------------------------------------------------------
# A 14-year-old was getting the walk-them-back card, and once that card stood aside the same line
# got the 5am-night-waking one: both are written for a child who cannot yet reason about bedtime.
# A teenager can, and what a parent needs is the shape of the morning, so it has its own answer.
ENTRIES.append(entry(
    "teen-wont-get-up",
    (("teenager", "teen", "teenagers", "son", "daughter", "14 year old", "15 year old",
      "16 year old", "13 year old", "17 year old", "year 10", "year 11", "gcse", "gcses",
      "secondary school", "high school"),
     ("wont get up", "won't get up", "wont get out of bed", "won't get out of bed",
      "wont wake", "won't wake", "wont wake up", "won't wake up", "late for school",
      "cant wake him", "can't wake him", "cant wake her", "can't wake her", "sleeps in",
      "sleeping in", "wont go to school", "won't go to school", "refusing school",
      "refuses school", "school refusal", "misses the bus", "always late", "wont get ready",
      "won't get ready", "stays up", "staying up", "wont go to sleep", "won't go to sleep",
      "cant get him up", "can't get him up", "cant get her up", "can't get her up")),
    ("Aim at the wake time, not the bedtime: get them up at the same time every day, weekends "
     "included, and open the curtains and put breakfast out straight away, because the body clock "
     "follows the morning light and the evening sorts itself out a week or two later. Take the "
     "phone and the charger out of the room, and let them stay up later rather than fight a 10pm "
     "battle a teenager's body cannot lose. If they are missing school most days for more than a "
     "couple of weeks, or sleeping through alarms and falling asleep in class, ring the school "
     "and ask the GP about their sleep - that is not laziness."),
    bias=1,
    # A parent describing the morning ("my daughter is 15 and stays up till 3am") is asking about
    # it, so there is no ask gate here: the teenager and the morning are the keys.
    guard=_a_teenager_is_named,
    avoid=(# the phone at midnight has its own card, and it answers the device itself
           "phone", "phones", "charger", "screens", "screen time", "tablet", "ipad", "xbox",
           "playstation", "console", "gaming", "tiktok", "instagram", "snapchat", "youtube",
           "baby", "babies", "toddler", "newborn", "months old", "i cant get out of bed",
           "i can't get out of bed", "i wont get up", "my alarm", "shift work", "night shift",
           "insomnia", "i cant sleep", "i can't sleep", "i feel", "i am", "im ",
           "depressed", "depression", "anxious", "low mood", "self harm", "exam stress",
           "revision", "cant be bothered", "lazy"),
))

# --- a child and a phone -------------------------------------------------------------------
# "should i take his phone off him" was a stain answer ("blot up what you can with kitchen paper")
# and "my son is 11 and his phone is his whole life" the age-banded card that begins at under two
# and never gets to an eleven-year-old who will not put it down. A parent asking what to do about
# a child's phone is a parenting question with a concrete answer.
ENTRIES.append(entry(
    "a-child-and-a-phone",
    (("phone", "phones", "mobile", "ipad", "tablet", "screen time", "screens", "gaming",
      "games console", "playstation", "xbox", "nintendo", "device", "devices", "social media",
      "tiktok", "snapchat", "instagram", "youtube"),
     ("son", "daughter", "child", "children", "kid", "kids", "teen", "teenager", "year old",
      "years old", "take it off", "take it away",
      "take his", "take her", "take the", "confiscate", "limit", "limits", "too much",
      "whole life", "addicted", "a phone", "have a phone", "have tiktok", "have snapchat",
      # The second half used to carry "should i", "how much" and "how long", and the first half
      # carries bare "phone", so any phone line that was a question reached this card: "how long
      # should i charge my phone" lost its charging-port answer to the rule card, and so did
      # "should i take my phone to the interview" (found on merged main `a3d6db94`). What a
      # parent asks is carried by the words below - the age ask by "too young", "first phone",
      # "a phone"; the habit and the taking-away by "take his", "whole life", "addicted",
      # "confiscate", "limit", "too much" - and none of them is a question shape.
      "have instagram", "too young")),
    _a_phone_rule_and_an_age,
    # the screen-time-by-age card answers the general question, and a mark on the screen or a
    # broken phone is another row's repair: this row is the limit and the habit
    avoid=("cracked", "crack", "smashed", "broken", "repair", "battery", "charge not", "wont charge",
           # a screen you wipe is a cleaning question: "how do i clean my phone screen" was told to
           # agree the rule about two hours a day of screens for fun
           "clean", "cleaning", "cleaned", "wipe", "wiping", "smudge", "smudges", "smear",
           "smears", "fingerprint", "fingerprints", "greasy", "mark on the screen",
           "scratch", "scratches", "scratched",
           "won't charge", "water damage", "warranty", "contract", "sim", "tariff", "which phone",
           "what phone", "best phone", "new phone", "buy a phone", "how much does", "cost",
           # bedtime is its own row (`teen-night-phone`): where the phone sleeps at night
           "at night", "bedtime", "staying up", "stays up", "till", "2am", "go to sleep",
           "get to sleep", "in bed", "wont sleep", "won't sleep",
           # a phone stuck in a car mount is a hardware question, and it was reaching this card
           "holder", "car holder", "mount", "phone mount", "cradle", "windscreen", "dashboard",
           "vent clip", "out of the car", "out of my car",
           # what a child saw is a conversation about the content, not the daily limit
           "saw something", "seen something", "saw a video", "watched something",
           "what they saw", "inappropriate", "upsetting video", "scary video",
           # a phone that has gone missing is the find-my-phone row, and "my daughter lost
           # her phone" was the screen-time limit: the child's word was all this row needed
           "lost", "lose", "loses", "lost it", "lost her", "lost his", "lost their",
           "mislaid", "stolen", "stole", "robbed", "find my", "tracker", "left it",
           "left her phone", "left his phone", "cant find", "can't find", "cannot find",
           # a fault in the phone is a repair, and an interview checklist is neither: without
           # these, "how long should i charge my phone" and "should i take my phone to the
           # interview" still name a phone next to "limit" or "take the"
           "charge", "charging", "charger", "battery", "port", "interview", "cv",
           "application",
           # a tablet you swallow is not a tablet you hand a child: "should i keep taking the
           # tablets" reached this card on merged main `c403b2bf`. The medicine words are plural
           # or named, so "should i get my 8 year old a tablet" still reaches the age advice
           "tablets", "pills", "medicine", "meds", "prescription", "antibiotics", "pharmacy",
           "dose", "doctor said",
           # an animal is not a child with a tablet: "my dog wont take his tablets" was answered
           # with "agree the rule before the argument: about two hours a day of screens"
           "dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "rabbit", "hamster",
           "guinea pig", "pet", "pets", "the vet", "vet")))

# --- the self and the feed -------------------------------------------------
# main's `putting-myself-down` and `comparing-myself` (further up this file) already answer
# "how do i be kinder to myself" and "how do i stop comparing myself to others", so this branch
# does not add a second row for either: one fact, one table. What was missing was the admission
# without a how-to ("i need to give myself a break"), which the two rows above now key on.

# --- the nappy kit: how many, what goes in the bag, and the cream -----------
# Three everyday asks that got a shrug, a health-visitor deflection, or somebody else's answer:
# "nappy cream" and "nappy bag" got the bare ack, "what should i pack in my nappy bag" was told
# to ring 111, and "how many nappies does a newborn use a day" was answered with a paracetamol
# dose. The changing steps and the rash card own their own lines and are left alone.
# How many a day is the age's question, not one number: "how many nappies does a toddler use" was
# told eight to ten, which is a newborn. The age the line names picks the row, and a line with no
# age gets the newborn figure with the rest of the first year in it.
_NAPPY_AGES = (
    (("3 month", "3 months", "three month", "three months", "4 month", "4 months",
      "four month", "four months", "6 week", "6 weeks", "six week", "six weeks",
      "2 month", "2 months", "two month", "two months"),
     "By three months it is about six to eight a day - a pack of 30 every four or five days - and "
     "most babies have moved up two sizes by then."),
    (("6 month", "6 months", "six month", "six months", "7 month", "7 months", "seven month",
      "seven months", "8 month", "8 months", "eight months", "9 month", "9 months",
      "nine months"),
     "By six months it is about five to seven a day, so a pack of 30 lasts around five days, and "
     "most babies are in size 3 or 4 by then."),
    (("1 year", "1 years", "one year", "12 month", "12 months", "twelve months", "18 month",
      "18 months", "eighteen months", "toddler", "2 year", "2 years", "two year", "two years"),
     "A one year old gets through about four to six a day - two packs of 30 a month - and a "
     "toddler nearer four, falling off as potty training starts."),
)


def _nappies_a_day(memory, understood):
    """How many nappies a day, at the age the line names."""
    said = " " + (understood.get("clean") or "").lower() + " "
    for ages, answer in _NAPPY_AGES:
        for age in ages:
            if " %s " % age in said:
                return answer
    return ("A newborn gets through eight to ten a day - about seventy a week, so two big packs a "
            "month or a subscription. It drops to around six to seven a day by six months and four "
            "or five by a year. Buy one pack of newborn size and one of the next size up: they "
            "grow out of newborn in a fortnight, and a size that leaks is usually too small.")


ENTRIES.append(entry(
    "nappies-how-many",
    (("nappies", "nappy", "diapers", "diaper"), ("how many", "a day", "per day", "do i need",
                                                "will i need", "a week", "how often",
                                                "newborn", "a month", "stock up", "buy")),
    _nappies_a_day,
    # the rash, the changing steps and the bag are other rows' questions
    avoid=("rash", "sore", "red bottom", "cream", "how do i change", "how to change",
           "nappy bag", "changing bag", "pack", "leaking", "leak")))
_A_NAPPY_BAG = (
    "Pack for two changes plus one for luck: four or five nappies, wipes or two damp flannels in "
    "a bag, a fold-out changing mat, nappy sacks, a full spare vest and sleepsuit, a muslin and a "
    "spare top for you. Add a feed - a bottle with the powder in a pot, or a cover if you are "
    "breastfeeding - and a snack and water for yourself. Restock it the moment you get home, "
    "because the one day it is empty is the day you are out.")
ENTRIES.append(entry(
    "nappy-bag",
    (("nappy bag", "changing bag", "baby bag", "packing bag"),
     ("nappy", "nappies", "baby", "newborn", "out", "going out", "day out", "hospital bag",
      "pack", "take", "need")),
    _A_NAPPY_BAG,
    # a bag for a weekend, a holiday or a birth is another bag: this row keys on "pack" and was
    # answering all three with four or five nappies
    avoid=("rash", "cream", "how do i change", "how to change", "hospital bag",
           "hospital bag for birth", "weekend", "weekend away", "week away", "for a weekend",
           "holiday", "holidays", "suitcase", "for a trip", "overnight", "labour", "birth")))
# "what should i pack" on its own is every bag there is - a beach, a weekend, a school trip - and
# it was the first key group here, so an ask about a beach got four or five nappies (the second
# group only needs "pack"). The bag has to be a baby's bag to count: a bag word in the line, or
# the pack question with a baby in it. Two rows rather than a fence, because the fence was the
# wrong shape - it stood this row down for a weekend or a holiday, and a holiday is exactly when
# a line says "and what should i pack" with the baby already on the table.
ENTRIES.append(entry(
    "nappy-bag-packing",
    (("what should i pack", "what do i pack", "what shall i pack", "what to pack",
      "what should we pack", "what should i take"),
     ("nappy", "nappies", "baby", "babys", "newborn", "formula", "bottle", "changing",
      "feed", "moses basket")),
    _A_NAPPY_BAG,
    avoid=("rash", "cream", "how do i change", "how to change", "hospital bag for birth",
           "labour", "birth", "weekend away", "week away", "for a weekend")))
ENTRIES.append(entry(
    "nappy-cream",
    (("nappy cream", "barrier cream", "sudocrem", "metanium", "bepanthen", "nappy ointment"),
     ("which", "best", "what", "should i use", "do i need", "buy", "use", "recommend",
      "how much", "safe", "cream")),
    "A barrier cream with zinc oxide in it is the one to have - Sudocrem, Metanium or Bepanthen "
    "all do the same job - and a thin layer at every change is enough once the skin looks pink. "
    "Thick white paste is for a sore bottom, not for prevention. If it is still red after three "
    "days, or there are spots at the edges, that is usually thrush and needs an antifungal cream "
    "from the health visitor rather than more barrier cream.",
    avoid=("rash that", "thrush", "nappy rash is not", "how do i change", "ingest", "eat",
           "swallowed")))


# "is breastfeeding ok", "im breastfeeding is that ok", "does breastfeeding hurt", "how long should
# i breastfeed for" all reached nothing: a check-in, an echo, the health-visitor handoff, a punt.
# `breastfeeding` is in the domain's word list, so nothing here ever needed it as a key. The rows
# that do key it are about a drink, a medicine or a food, and each of them stands down on the
# others - so the plain question about feeding had no home at all.
_BREAST_PAIN = ("hurt", "hurts", "hurting", "painful", "pain", "sore", "soreness", "cracked",
                "bleeding", "latch", "latching", "engorged", "mastitis", "blocked duct")
_BREAST_LENGTH = ("how long", "how many months", "what age", "until", "till", "how old",
                  "months", "years", "how much longer", "toddler", "older baby", "one year",
                  "two years", "how long for", "how many years")
# "is it ok to breastfeed if im ill" was the take-today-down-a-gear card and "is it safe to
# breastfeed with a cold" the search hedge: the plain answer ("Yes - it is the normal way to feed
# a baby") is true but does not answer the illness at all, and the illness is what is being asked.
_BREAST_ILL = (" im ill", " if im ill", "im ill", "i am ill", "feel ill", "feeling ill",
               "poorly", "unwell", "i am sick", "im sick", "being sick", "a cold", "with a cold",
               "got a cold", "flu", "fever", "temperature", "chest infection", "covid",
               "food poisoning", "vomiting", "diarrhoea", "diarrhea", "migraine", "tonsillitis",
               "infection", "on antibiotics")
# "i cant breastfeed should i feel bad" came back "Yes - it is the normal way to feed a baby",
# because the line keys on "can i" and the plain answer opens on "Yes". The worst line in the set
# was a yes to "should i feel bad", so the could-not words answer first and answer alone.
_BREAST_COULD_NOT = ("cant", "can't", "cannot", "couldnt", "couldn't", "could not", "unable",
                     "not able", "didnt manage", "didn't manage", "never managed", "gave up",
                     "give up", "stopped", "stopping", "had to stop", "wouldnt latch",
                     "wouldn't latch", "wouldnt feed", "wouldn't feed", "feel bad", "feeling bad",
                     "feel guilty", "feeling guilty", "guilty", "feel awful", "failure",
                     "a failure", "not good enough", "let my baby down", "let her down",
                     "let him down", "cried", "beat myself up")
# "nursing" is the job as well as the feed: "should i retrain as a nurse at 45" was told "Yes -
# it is the normal way to feed a baby", and so were "is nursing a good career", "should i go back
# to nursing after 10 years" and "how long does it take to train as a nurse". The profession is
# another card's question, so this row stands down on the words that make the line a career.
_A_NURSING_CAREER = ("retrain", "retraining", "retrained", "career", "careers", "become a nurse",
                     "becoming a nurse", "be a nurse", "train as a nurse", "training as a nurse",
                     "nursing degree", "nursing course", "nursing job", "nursing home",
                     "staff nurse", "ward", "go back to nursing", "return to nursing",
                     "back to nursing", "qualify as a nurse", "nurse training", "midwife",
                     "midwifery", "nursery nurse", "veterinary nurse", "dental nurse", "salary",
                     "shifts", "hospital", "agency", "apply for nursing", "nursing at",
                     # the job named without any of the above: "is a job in nursing worth it"
                     # was the feed card on main and here, because the line carries the bare
                     # word and nothing else that says what it is about
                     "job", "jobs", "worth it", "pay", "paid", "pension", "part time",
                     "full time", "bank staff", "nhs")


def _not_a_nursing_career(understood):
    """False when the line is about the job rather than about feeding a baby."""
    said = understood if isinstance(understood, dict) else {}
    text = " " + str(said.get("clean") or said.get("text") or "").lower() + " "
    return not any(" " + word + " " in text or text.strip().endswith(word)
                   for word in _A_NURSING_CAREER)


_BREAST_PUBLIC = ("in public", "public", "in a cafe", "in a restaurant", "on a train",
                  "on the bus", "in front of", "people stare", "stares", "ask me to stop",
                  "ask me to leave", "cover up", "cover myself", "let me", "legal",
                  "where can i feed", "feeding in public")


def _breastfeeding_basics(memory, understood):
    clean = " " + str((understood or {}).get("clean") or "").lower() + " "
    if any(word in clean for word in _BREAST_COULD_NOT):
        return ("No - a baby who is fed is fed, and how they were fed is not something you owe "
                "anyone an apology for. If it did not work, that is usually a latch, a supply or a "
                "medical reason rather than effort, and formula is a complete food: the health "
                "visitor will help you swap over or mix the two without a fuss. If the guilt is "
                "sticking, say so to your midwife or GP - it is common, it has a name, and it is "
                "treatable.")
    if any(word in clean for word in _BREAST_PUBLIC):
        return ("Yes - you can feed your baby wherever you happen to be, and in the UK the law "
                "protects it: nobody can ask you to stop, move on or leave because you are "
                "breastfeeding. A scarf or a layered top is plenty if you want cover, and if you "
                "would rather have a quiet corner, a cafe, library or shopping centre will nearly "
                "always find you one - ask the staff.")
    if any(word in clean for word in _BREAST_PAIN):
        return ("It should not hurt beyond the first few seconds of a feed, so get help early "
                "rather than pushing through: a midwife, health visitor or a local breastfeeding "
                "clinic will watch a whole feed and fix the latch, which is the cause most of the "
                "time. Cracked or bleeding nipples, a red painful patch on the breast with a fever, "
                "or a baby who stops feeding are the reasons to be seen the same day.")
    if any(word in clean for word in _BREAST_ILL):
        return ("Yes - keep feeding through it: your milk carries the antibodies you are making "
                "against whatever it is, so it is the best protection the baby can get, and "
                "stopping suddenly is what causes mastitis and a dip in supply. Drink more than "
                "you feel like and feed lying down if you are wiped out, and check any medicine "
                "with a pharmacist first - most are fine.")
    if any(word in clean for word in _BREAST_LENGTH):
        return ("Only breast milk for about the first six months, then keep going alongside solid "
                "food for as long as you both want - the UK advice is to two years and beyond, and "
                "plenty of babies stop before that. There is no point where the milk stops being "
                "worth it, and no rule you have to keep to if it is not working for you.")
    if " formula" in clean or " bottle " in clean or " bottles " in clean:
        return ("Formula is a safe, complete food and a baby fed formula is a baby fed well - the "
                "only thing it does not carry is the antibodies that come in your milk, which is "
                "why breast milk is the default advice rather than the only good choice. Mixed "
                "feeding works too, and a baby on both gets the antibodies from the feeds you do "
                "give. What matters is that the baby is growing and that feeding is not miserable "
                "for you.")
    return ("Yes - it is the normal way to feed a baby and it is what the milk is for. Feed on "
            "demand rather than by the clock: a newborn feeds eight to twelve times in 24 hours, "
            "and six or more wet nappies a day with steady weight gain say it is going in. If it "
            "hurts, the baby is sleepy at the breast or not putting on weight, a midwife or health "
            "visitor will see you the same week.")


ENTRIES.append(entry("breastfeeding-basics",
                     (("breastfeeding", "breast feeding", "breastfeed", "breast fed", "breastfed",
                       "nursing", "chestfeeding", "chest feeding", "exclusively breastfeeding",
                       "bottle of formula", "give formula", "giving formula", "switch to formula",
                       "mixed feeding", "breast and formula", "formula and breast"),
                      ("ok", "okay", "normal", "alright", "fine", "is it", "is that", "should i",
                       "shouldnt i", "cant", "can't", "couldnt", "couldn't", "unable", "guilty",
                       "feel bad", "feel awful", "gave up", "stopped", "in public", "public",
                       "can i", "good", "healthy", "hurt", "hurts", "painful", "sore",
                       "how long", "how often", "how many", "months", "years", "worth it",
                       "what age", "until", "till", "stop", "carry on", "keep going",
                       "safe", "worried", "worry", "formula", "bottle", "bottles", "mixed")),
                     _breastfeeding_basics,
                     guard=_not_a_nursing_career,
                     bias=2,
                     # a drink, a medicine, a food, a pump and a formula question each have a row
                     avoid=("coffee", "caffeine", "tea", "alcohol", "wine", "beer", "gin",
                            "vodka", "drink", "drinks", "drinking", "medicine", "medication",
                            "paracetamol", "ibuprofen", "antibiotic", "antibiotics", "tablet",
                            "tablets", "pill", "eat", "eating", "food", "foods", "diet",
                            # "what can i take while breastfeeding" is a medicine question and
                            # the medicine row answered it: this one answered "is it normal".
                            "what can i take", "can i take", "what to take", "take something",
                            "painkiller", "painkillers", "remedy", "anything for the pain",
                            "cheese", "sushi", "peanuts", "liver", "pump", "pumping",
                            "express", "expressing", "wean", "weaning",
                            "solids", "sleep", "co-sleep", "teeth", "cracked nipple",
                            # "nursing" is one of this row's words and a nurse is a person with
                            # a job: "how many hours does a nurse work" and "how many hours a week
                            # is a nurse" were answered with twelve feeds a day, while the same
                            # question about a doctor or a midwife reached the hours row. A nurse
                            # named as a person stands aside here.
                            # not the bare word "nurses": the matcher's loose forms read
                            # "nursing" as it, and this row's own lines - "is nursing in public
                            # ok" - stopped being answered
                            "a nurse", "a nurse in", "nursing assistant", "nurse work",
                            "nurse job", "nurse shift", "nurse shifts", "nurse salary",
                            "does a nurse", "do nurses", "nurses work",
                            # not the generic hour words: "how many hours should i breastfeed
                            # for" is a feeding question and the bare phrases fenced it
                            )))


# --- school holidays ---------------------------------------------------------
# A school holiday is a date question, and the date is set by the school or the council rather
# than by the calendar, so the answer that helps is the usual pattern for English state schools
# and, when the line asks how long, the count to it. Every reply points at the school's own term
# dates, because a school can move the break by a day or two, and the patterns are close enough
# across England to name a date rather than to shrug.
_SCHOOL_WORDS = ("school", "schools", "kids", "children", "child", "term", "terms",
                 # a break is named without a school word: "how long is the summer break"
                 "break", "breaks",
                 "term dates", "break up", "breaks up", "broke up", "nursery", "academy",
                 "primary", "secondary", "infant", "junior", "sixth form", "pupil", "pupils",
                 "holidays", "half term")

# A school holiday named as a trip is a travel question, and "where shall we go in the summer
# holidays" belongs to the travel rows, not to the school calendar.
_TRAVEL_HOLIDAY = ("spain", "portugal", "greece", "turkey", "france", "italy", "florida",
                   "abroad", "flights", "flight", "hotel", "hotels", "where", "book", "booking",
                   "booked", "cheap", "cheapest", "all inclusive", "package", "resort", "villa",
                   "airbnb", "my holiday", "our holiday", "shall we go", "to go", "should we go")

_SCHOOL_TIME_ASK = ("when", "date", "dates", "start", "starts", "begin", "begins", "end",
                    "ends", "finish", "finishes", "back", "go back", "how long", "how many",
                    "days", "weeks", "till", "until", "until", "countdown", "soon", "time")


def _said_date(found):
    """A date said the way a person says it: "Tuesday 21 July", with the year when it is not the
    one we are in, because a break-up date said in November is next year's."""
    import datetime
    said = "%s %d %s" % (found.strftime("%A"), found.day, found.strftime("%B"))
    if found.year != datetime.date.today().year:
        said += " %d" % found.year
    return said


def _school_date(month, day):
    """The usual date of a school break, this year if it has not been and gone, else next year."""
    import datetime
    today = datetime.date.today()
    for year in (today.year, today.year + 1):
        found = datetime.date(year, month, day)
        if found >= today:
            return found
    return datetime.date(today.year + 1, month, day)


def _this_or_next(found):
    """How the date is introduced: "this year that is Wednesday 21 July", or "the next one is"."""
    import datetime
    if found.year == datetime.date.today().year:
        return "this year that is %s" % _said_date(found)
    return "the next one is %s" % _said_date(found)


def _about_days(days):
    """"36 days (five weeks)" - the count in days, and in weeks when it is worth saying."""
    if days <= 10:
        return "%d days" % days
    weeks = int(round(days / 7.0))
    return "%d days (about %d weeks)" % (days, weeks)


def _asks_the_length(clean):
    """"How long are the summer holidays" wants six weeks, not the days until they start."""
    return bool(re.search(r"\bhow long (?:is|are|do|does|will)\b|\bhow many weeks off\b"
                         r"|\bhow long (?:a|an|the)\b|\blast(?:s|ed)?\b", clean, re.I))


def _counts_the_wait(clean):
    """True when the line wants the days until a break rather than when it is or how long."""
    if _asks_the_length(clean):
        return False
    return bool(re.search(r"\b(?:how (?:long|many)|days|weeks|till|until|countdown|left)\b",
                          clean, re.I))


# The four nations of the United Kingdom set their own school year, and the person asking is in
# one of them. Without this the rows below gave an English year to everyone: "when do schools go
# back in scotland" and "when is half term in glasgow" were told the first days of September,
# and Scottish schools go back in the middle of August. A shrug is a bad answer; a confident
# answer to another country's calendar is worse.
_NATION_WORDS = (
    ("scotland", ("scotland", "scottish", "glasgow", "edinburgh", "aberdeen", "dundee",
                  "inverness", "stirling", "fife", "paisley", "perthshire", "highlands",
                  "shetland", "orkney")),
    ("wales", ("wales", "welsh", "cardiff", "swansea", "newport", "wrexham", "bangor",
               "caernarfon", "bridgend", "carmarthen")),
    ("northern ireland", ("northern ireland", "northern irish", "belfast", "derry",
                          "londonderry", "armagh", "lisburn", "newry", "antrim", "ulster")),
    ("ireland", ("ireland", "irish", "dublin", "cork", "galway", "limerick",
                 "republic of ireland")),
    ("england", ("england", "english", "london", "manchester", "birmingham", "leeds",
                 "bristol", "newcastle", "liverpool", "sheffield", "nottingham",
                 "yorkshire", "kent", "essex", "cornwall", "surrey", "devon")),
)

# The shape of each school year, said without a date: the exact days are the council's or the
# education authority's, and a bot that makes one up is the thing these rows exist to avoid.
_SCHOOL_YEAR = {
    "scotland": (
        "Scottish schools go back in the middle of August, usually between the 15th and the 20th, "
        "and break up at the end of June. The holidays are a week in mid-October, about two weeks "
        "at Christmas, a week or so at Easter and the long summer break from the last week of "
        "June."),
    "wales": (
        "Welsh schools usually go back in the first days of September and break up in the third "
        "week of July, with half term a week in late October and about two weeks at Christmas. "
        "Each council sets its own dates and they differ by a few days."),
    "northern ireland": (
        "Schools in Northern Ireland go back in the first days of September and finish at the end "
        "of June, with half terms in late October and mid-February, two weeks at Christmas and a "
        "week or two at Easter."),
    "ireland": (
        "Irish schools go back at the end of August or in the first days of September and finish "
        "at the end of June, with a week off in late October, two weeks at Christmas, a week in "
        "February and Easter week."),
    "england": None,  # the rows below already answer the English year: see _the_nations_year
}
_THE_DATES_ARE_LOCAL = (" Every council, education authority and academy sets its own exact "
                        "dates, so check the council's school term dates page or the school's "
                        "own calendar for the day.")


def _the_nation_said(text):
    """The nation whose school year the line is asking about, or "" when it names none."""
    for nation, words in _NATION_WORDS:
        if any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in words):
            return nation
    return ""


def _the_nations_year(memory, understood):
    """The school year of the nation the chat is in, or None for a chat that names none.

    A line that names no nation is still in one if an earlier line did: a chat that said Glasgow
    two turns ago is a Glasgow chat, and its next question about term dates is about Scotland.
    """
    text = " " + str((understood or {}).get("clean") or "").lower() + " "
    nation = _the_nation_said(text)
    if not nation and memory:
        from ..memory import recent
        for turn in reversed(recent(memory, 6)):
            nation = _the_nation_said(" " + str(turn.get("user") or "").lower() + " ")
            if nation:
                break
    if not nation:
        return None
    # A line about England, or a chat that has only ever named England, needs nothing: every row
    # below already says the English year, so an override would cost it the dates it gives.
    said = _SCHOOL_YEAR.get(nation)
    if not said:
        return None
    return said + _THE_DATES_ARE_LOCAL


SUMMER_BREAK = ("English state schools break up in the third week of July and go back in the "
                "first days of September")
WINTER_BREAK = ("The Christmas break runs from just before Christmas to the first days of "
                "January")
EASTER_BREAK = ("The Easter break is the two weeks around Easter weekend: schools usually break "
                "up on the Friday a week before Good Friday and go back the Monday after Easter "
                "Monday")


def _summer_break(memory, understood):
    """When the summer holidays start, or how long it is until they do."""
    there = _the_nations_year(memory, understood)
    if there:
        return there
    clean = understood.get("clean") or ""
    usual = _school_date(7, 21)
    if _asks_the_length(clean):
        return ("Six weeks off: %s. The exact two days are on your school's term dates, because "
                "a school can start back a day or two either side." % SUMMER_BREAK)
    if _counts_the_wait(clean):
        import datetime
        days = (usual - datetime.date.today()).days
        return ("%s until the summer holidays: %s, so they break up on %s. The exact day is on "
                "your school's term dates, and it can sit a day or two either side."
                % (_about_days(days), SUMMER_BREAK, _said_date(usual)))
    return ("%s - %s. The exact day is on your school's term dates, and it can sit a day or two "
            "either side." % (SUMMER_BREAK, _this_or_next(usual)))


def _winter_break(memory, understood):
    """The Christmas holidays, and the count to them when the line asks how long."""
    there = _the_nations_year(memory, understood)
    if there:
        return there
    clean = understood.get("clean") or ""
    usual = _school_date(12, 19)
    if _counts_the_wait(clean):
        import datetime
        days = (usual - datetime.date.today()).days
        return ("%s until the Christmas holidays: schools usually break up on about 19 December, "
                "and %s, then go back the first Tuesday or Wednesday in January."
                % (_about_days(days), _this_or_next(usual)))
    return ("%s: the break-up is usually about 19 December, %s, and back on the first Tuesday or "
            "Wednesday in January. Your school's term dates give the exact two days."
            % (WINTER_BREAK, _this_or_next(usual)))


def _easter_break(memory, understood):
    """The Easter holidays, which follow Easter weekend rather than a fixed date."""
    there = _the_nations_year(memory, understood)
    if there:
        return there
    return ("%s. Easter moves each year, so the two weeks move with it - your school's term dates "
            "name the Friday it breaks up and the Monday it goes back." % EASTER_BREAK)


def _half_term(memory, understood):
    """Half term: a week in October, February and May, on the school's own dates."""
    there = _the_nations_year(memory, understood)
    if there:
        return there
    return ("Half term is one week off: the last week of October, the middle of February and the "
            "last week of May. Which week it falls in is set by your school, and the three dates "
            "for the year are on its term dates page - the October one is usually the week the "
            "clocks go back.")


# When each term starts, for a line that names the term: "when does the summer term start" was
# answered with the summer return in September, which is the start of the autumn term.
_TERM_STARTS = (
    (("summer term", "summer terms"),
     "The summer term starts in the second half of April, a week after the Easter break, and runs "
     "to the third week of July"),
    (("autumn term", "autumn terms", "winter term"),
     "The autumn term starts in the first days of September and runs to about 19 December"),
    (("spring term", "spring terms"),
     "The spring term starts on the first Tuesday or Wednesday in January and runs to the Easter "
     "break"),
)


def _back_to_school(memory, understood):
    """The day term starts: the term the line named, or all three returns when it names none."""
    there = _the_nations_year(memory, understood)
    if there:
        return there
    clean = (understood or {}).get("clean") or ""
    for words, said in _TERM_STARTS:
        if any(word in clean for word in words):
            return "%s. Your school's term dates give the exact day, and a school can add an " \
                   "inset day at the start of term." % said
    return ("The summer return is the first days of September, after Christmas it is the first "
            "Tuesday or Wednesday in January, and after Easter it is the Monday a week after "
            "Easter Monday. Your school's term dates give the exact day, and a school can add an "
            "inset day at the start of term.")


def _school_holidays_general(memory, understood):
    """The shape of the school year, for a line that names no particular break.

    A line like "when do the kids break up" names no break at all, so the useful half of the
    answer is the next one on the calendar, and the dates of the two that have a usual date.
    """
    there = _the_nations_year(memory, understood)
    if there:
        return there
    import datetime
    today = datetime.date.today()
    summer = _school_date(7, 21)
    winter = _school_date(12, 19)
    if winter < summer:
        soon = "the Christmas break, from about 19 December (%s) to the first days of January" % (
            _said_date(winter),)
    else:
        soon = "the summer break, from the third week of July (%s) to the first days of September" % (
            _said_date(summer),)
    if _counts_the_wait(understood.get("clean") or ""):
        # "how many days until the kids break up" names no break, and a count is what it wants:
        # it was answered with the shape of the year and no number at all.
        days = ((winter if winter < summer else summer) - today).days
        return ("%s until the next break - %s. The exact dates come from your school or your "
                "council." % (_about_days(days), soon))
    return ("The next one is %s. English state schools have six weeks off in summer, two at "
            "Christmas, two at Easter and a week's half term in October, February and May; the "
            "exact dates come from your school or your council." % soon)


ENTRIES.append(entry("school-break-summer",
                     (("summer holidays", "summer holiday", "summer break", "summer term",
                       "summer hols", "six weeks holiday", "six weeks holidays",
                       "school summer holidays", "break up for summer", "break up for the summer",
                       "breaks up for summer"),
                      _SCHOOL_TIME_ASK),
                     _summer_break, bias=1, ask=_SCHOOL_WORDS,
                     avoid=_TRAVEL_HOLIDAY + ("activities", "things to do", "what to do",
                                              "days out", "keep them busy", "ideas", "bored",
                                              "rainy", "suncream", "packing")))

ENTRIES.append(entry("school-break-christmas",
                     (("christmas holidays", "christmas break", "christmas term",
                       "break up for christmas", "schools break up for christmas",
                       "christmas school holidays", "end of term"),
                      _SCHOOL_TIME_ASK),
                     _winter_break, bias=1, ask=_SCHOOL_WORDS,
                     avoid=("santa", "presents", "present", "dinner", "turkey", "tree",
                            "decorations", "gift", "gifts", "advent", "carols", "carol",
                            "nativity", "activities", "things to do", "what to do")))

ENTRIES.append(entry("school-break-easter",
                     (("easter holidays", "easter break", "break up for easter", "easter term"),
                      _SCHOOL_TIME_ASK),
                     _easter_break, bias=1, ask=_SCHOOL_WORDS,
                     avoid=("egg", "eggs", "chocolate", "church", "service", "lamb", "activities",
                            "things to do", "what to do")))

ENTRIES.append(entry("school-half-term",
                     (("half term", "halfterm", "half-term", "half terms"),
                      _SCHOOL_TIME_ASK + ("off",)),
                     _half_term, bias=1,
                     avoid=("activities", "things to do", "what to do", "days out", "ideas",
                            "bored", "rainy", "keep them busy", "kids club", "camps", "childcare",
                            "time off work", "cover", "work",
                            # a line that asks what to do with the week is the activity rows'
                            "what can we do", "what can i do", "what shall we do",
                            "what should we do", "do with the kids", "do with my", "entertain",
                            "rainy day", "stuck indoors", "how do i keep")))

ENTRIES.append(entry("school-back-to-school",
                     (("school go back", "schools go back", "go back to school", "school goes back",
                       "back to school date", "term starts", "new term", "school return",
                       "school starts again", "kids go back", "children go back",
                       "go back after christmas", "back after christmas",
                       "go back after half term", "go back after easter"),
                      ("when", "date", "dates", "term dates", "term", "starts", "start again",
                       "back", "first day", "return")),
                     _back_to_school, bias=3, ask=("school", "schools", "kids", "children",
                                                   "child", "term", "term dates", "nursery"),
                     avoid=("uniform", "shoes", "lunchbox", "bag", "nervous", "anxious",
                            "worried", "first day", "friends", "shopping", "supplies", "clothes",
                            "bullying", "teacher", "won't go", "wont go", "refusing",
                            # "when can my child go back to school" is about a child who is ill,
                            # and the screening card answers it; the calendar is the question
                            # about the school, which is asked about "the kids" or the school
                            "my child", "my son", "my daughter", "my baby", "my boy",
                            "my girl", "he is ill", "she is ill")))

ENTRIES.append(entry("school-holidays-when",
                     (("school holidays", "school holiday", "term dates", "school term",
                       "school terms", "school breaks up", "schools break up", "kids off school",
                       "children off school", "kids break up", "children break up",
                       "kids finish school", "when do we break up"),
                      _SCHOOL_TIME_ASK),
                     _school_holidays_general, bias=1,
                     avoid=_TRAVEL_HOLIDAY + ("activities", "things to do", "what to do",
                                              "days out", "keep them busy", "ideas", "bored",
                                              "rainy", "childcare", "cover", "juggle", "work")))

# Someone in the family is arrested, and the bot answered it as small talk: on main
# "my son has been arrested" was "Nice one. How did the rest of it go?", "my partner has been
# arrested" the same, "my son is in police custody" the mirror line, and "my kid is in trouble
# with the police" was a card about school absence fines. The first hour is the part a person
# can act on, so the card is the first hour and nothing else.
THE_FIRST_HOUR = (
    "Get the station and the custody record number first, because that reference is what "
    "everyone else quotes from then on. Ask for the free duty solicitor: saying you want one is "
    "not an admission and it is the step most people skip. Note the time of the arrest as well, "
    "since the clock starts there - usually 24 hours before they have to charge or release.")

# A stop, a search or a questioning is the same family of question and a different answer, and
# main had nothing for any of them: "my son was stopped by the police" was "What has your son
# said about it", "my daughter was searched by the police" was "Nice one. How did the rest of it
# go?" and "my child was questioned by police without me" was "How was it, overall?".
THE_STOPPED = (
    "A stop and search needs grounds: ask which power is being used and why, and ask for the "
    "record slip, which carries the officer's number, the station and the reason. Being stopped "
    "is not the same as being arrested, so write down the time and the names while it is fresh, "
    "and complain to the force if the slip is refused.")

THE_QUESTIONED = (
    "If they are under 18 an appropriate adult - you, or another adult - has to be there before "
    "they are interviewed, so say that at the desk. Under caution 'no comment' is allowed and the "
    "solicitor is free; write down what was said and when, while you both remember it.")


def _police_matter(memory, reading):
    """The first hour of an arrest, or what a stop, a search or a questioning allows."""
    said = ((reading or {}).get("norm_text") or (reading or {}).get("clean") or "").lower()
    if re.search(r"\b(questioned|questioning|interviewed|interview|under caution|"
                 r"asked questions|statement|appropriate adult)\b", said):
        return THE_QUESTIONED
    if re.search(r"\b(stopped|stop and search|searched|searches|search|"
                 r"handcuffed|detained|frisked)\b", said):
        return THE_STOPPED
    return THE_FIRST_HOUR


ENTRIES.append(entry("a-police-matter-in-the-family",
          # "custody" on its own is not in the key: it is police custody in one family and
          # custody of the children in another, and "how do i get custody of my kids" is a
          # family-court question rather than an arrest (mint-plum's review).
          (("arrested", "arrest", "arrests", "police custody", "in custody", "held in custody",
            "taken into custody", "remanded", "charged with", "been charged", "on bail",
            "out on bail", "bailed",
            # not "criminal record": "i have a criminal record will that stop me getting a job"
            # is a job question and the record is not an arrest happening now
            "police station", "in trouble with the police", "police trouble",
            # NOT "what now", "what happens now", "what happens next": those carry no police
            # word, so they buy one follow-up and cost four ordinary lines - "i lost my job what
            # now" and "my wife wants a divorce what now" both got the arrest card (pink-lime's
            # review). The follow-up after an arrest is the memory and composer lane's, and it
            # already continues the answer.
            # a stop, a search or a questioning is the same question with a different answer,
            # and the phrase keeps it off "my daughter was searched at school"
            "stopped by the police", "stopped by police", "police stopped", "stop and search",
            "searched by the police", "searched by police", "police search",
            "questioned by police", "questioned by the police", "police interview",
            "under caution", "taken to the station"),
           ("son", "daughter", "child", "children", "kid", "kids", "teenager", "teen", "boy",
            "girl", "husband", "wife", "partner", "boyfriend", "girlfriend", "brother",
            "sister", "nephew", "niece", "stepson", "stepdaughter", "mum", "dad", "mother",
            "father", "i", "me", "myself", "my family")),
          _police_matter,
          # "my son is in custody of his dad" is a custody arrangement, not an arrest: the phrase
          # names the other parent and the row stands down for it
          avoid=("custody of", "in custody of"),
          bias=3))

# A small child's speech, bedtime and anger on main `e06365cb`: every line below was a shrug
# ("I'm listening - say more if it helps.") or a "Noted:" nod, and each has a concrete answer a
# parent can use the same evening. They are appended rather than inserted because no row they
# compete with wants these lines. (A cot that is outgrown was here too, and it is left to the
# `toddler-climbs-out-of-cot` row another branch is adding, so the two do not both answer it.)
ENTRIES.append(entry(
    "child-lisp",
    (("lisp", "lisps", "lisping", "speech therapy", "speech therapist", "speech and language",
      "says s as th", "says th for s", "says th instead", "th for s", "f for th",
      "cant say his s", "cant say her s", "cant say r", "cant say his r",
      "cant say her r", "hard to understand", "pronounces", "pronunciation", "stammer",
      "stutter", "stutters", "stammering",
      # one word only: a four-word phrase in the key scores once, so "my son cant say his r
      # sounds" fell under the bar and was a chat question. "words", "word" and "says" are not
      # here because they are every child's line - "my son has a spelling test and he cant
      # remember the words" and "can you help me word a text" were both this card with them in it.
      "sounds", "sound", "wrong words", "words wrong", "cant say", "unclear",
      "unclearly", "mispronounces"),
     ("child", "son", "daughter", "kid", "toddler", "year old", "years old", "still",
      "should i worry", "worried", "normal", "help", "referral", "referred", "nursery",
      "school", "health visitor", "gp", "cant say", "cannot say", "hard to understand",
      "struggles", "struggling")),
    "Most children lisp while they are learning their sounds and grow out of it on their own - "
    "the /s/ and /z/ sounds often take until about four and a half, and /r/ and /th/ until six or "
    "seven. Don't correct them or ask them to say it again: repeat the word back correctly in your "
    "own sentence and let it go. Ask the health visitor or the GP for a speech and language referral "
    "if the lisp is still there at four and a half, if strangers cannot understand them at three, "
    "if they are losing sounds they used to say, or if they are being teased or going quiet about "
    "it at nursery.",
    avoid=("adult", "myself", "my own", "i have", "ive had", "i lisp", "i stammer", "i stutter",
           "my speech", "battery", "piano", "guitar", "audio", "music", "recording", "podcast",
           "accent", "language learning", "french", "spanish", "welsh", "dog", "puppy", "cat",
           "parrot", "budgie", "car", "engine")))

ENTRIES.append(entry(
    "child-bedtime-tears",
    (("cries every bedtime", "cries at bedtime", "crying at bedtime", "cries every night",
      "cries when i leave", "cries when i put him down", "cries when i put her down",
      "screams at bedtime", "bedtime is a battle", "wont go to bed", "wont settle at night",
      "wont settle at bedtime", "fight at bedtime", "bedtime battle", "hates bedtime",
      "cries himself to sleep", "cries herself to sleep", "cries every nap"),
     ("child", "son", "daughter", "kid", "toddler", "baby", "year old", "years old", "months",
      "every night", "every bedtime", "bedtime", "nap", "naps", "sleep", "bed", "cot",
      "how do i", "what do i do", "help", "stop", "settle")),
    "Tears at bedtime are usually overtiredness or a routine that changes shape from night to "
    "night: the same four or five steps in the same order at the same time (bath, milk, teeth, "
    "two books, lights low, into bed), starting the wind-down half an hour before, with the last "
    "nap not too late for a toddler. Do the same short goodnight every time and leave while they "
    "are awake but sleepy; if they cry, go back after a minute, then two, then three, with a "
    "quiet 'it's sleep time, I love you' and no light and no play. It is normal for the first "
    "three or four nights to be worse before they are better, and see the GP if they also snore, "
    "stop breathing, or are exhausted in the daytime.",
    avoid=("adult", "myself", "my own", "i cry", "i cant sleep", "insomnia", "puppy", "dog",
           "puppies", "dog crying", "cat", "kitten", "crate", "neighbour", "neighbours",
           "baby monitor", "teething", "colic", "reflux", "newborn")))

ENTRIES.append(entry(
    "child-anger",
    (("anger problems", "anger issues", "always angry", "angry all the time", "so angry",
      "gets angry", "gets so angry", "angry at everything", "loses his temper",
      "loses her temper", "bad temper", "has a temper", "a temper", "rages", "raging",
      "explosive", "lashes out",
      "screams at me", "shouts at me", "throwing things", "throws things", "smashing things",
      "breaks things"),
     ("child", "son", "daughter", "kid", "toddler", "teenager", "year old", "years old",
      "always", "every day", "all the time", "help", "what can i do", "how do i",
      "worried", "worries me", "school", "at school", "at home", "behaviour")),
    "Anger in a child is usually the top of something else - hunger, tiredness, screens off "
    "too fast, or a day with no say in it - so name the feeling for them, stay calm yourself, and "
    "give the same short limit every time; a child who is shouting needs you quieter, not louder. "
    "Pick the moment later, when everyone is calm, to talk about what set it off and what they "
    "could do instead, and give them something physical to do with it (run, kick a ball, punch a "
    "cushion). Ask the school or the GP for help if it is most days, if someone is getting hurt, "
    "or if it has got worse over a few weeks rather than better.",
    # "i am always angry at work" was this card: the two words that make the key are the two
    # words a grown-up uses about themselves, so the speaker has to be stood down.
    # a parent's own temper is not the child's card: "i get so angry at my kids" is the person
    # asking about themselves, and that is a different answer.
    avoid=("i get", "i lose", "i shout", "i yell", "i scream", "i hit", "i am", "im",
           "at work", "my job", "my boss", "my office", "colleagues",
           "colleague", "shift", "commute",
           "adult", "myself", "my own", "i am angry", "im angry", "my anger", "my partner",
           "husband", "wife", "boss", "colleague", "friend", "road rage", "hits", "hitting",
           "hit me", "hits me", "bangs his head", "bangs her head", "self harm", "himself",
           "herself", "hurt himself", "hurt herself", "puppy", "dog", "cat")))


def _the_age_in_the_line(understood):
    """"a 15 year old" in the line, or None.

    The two cards below are about a rule with an age in it, and a card that says "14" to a line
    about a 16 year old is a different child and a different rule. So the age the parent gave is
    the one the answer names, and the fallback is the rule's own wording ("under 18") rather than
    a guess at the child.
    """
    reading = understood if isinstance(understood, dict) else {}
    text = str(reading.get("clean") or reading.get("text") or " ").lower()
    pattern = (r"\b(1[0-9]|[89])\s*(?:year|yr)s?\s*old\b|\bis\s+(1[0-9]|[89])\b"
               r"|\bat\s+(1[0-9]|[89])\b|\baged\s+(1[0-9]|[89])\b")
    for pair in re.findall(pattern, text):
        for one in pair:
            if one:
                return one
    return None


def _a_teenagers_tattoo(memory, understood):
    """The tattoo rule first, because a tattoo is what the line asked about."""
    reading = understood if isinstance(understood, dict) else {}
    text = str(reading.get("clean") or reading.get("text") or " ").lower()
    age = _the_age_in_the_line(understood)
    if re.search(r"\b18th\b|\b(?:is|turns|turning|she is|he is)\s+18\b|\b18\b", text) \
            and not age:
        return ("At 18 it is her own decision and no consent is needed, so the useful thing now is "
                "which studio rather than whether: licensed only, ask to see the licence and the "
                "sterile sealed needles opened in front of you, and look at healed work rather "
                "than the photographs they choose. A design drawn now and lived with for a few "
                "months is what saves the cover-up later. A piercing is a different rule: 16 "
                "without consent for lobes and most placements, and a parent with ID below that.")
    if age:
        who = ("In the UK a tattoo is 18 with no exceptions, so a %s year old cannot be tattooed "
               "at all - and a studio that would do one is breaking the law and is the studio to "
               "avoid" % age)
    else:
        who = ("In the UK a tattoo is 18 with no exceptions, so nobody under 18 can be tattooed "
               "at all - and a studio that would do one is breaking the law and is the studio to "
               "avoid")
    return (who + ". What you can say yes to now is the design: have them draw it and live with "
            "it on paper for a year, because a good studio will still be there at 18. Piercings "
            "are the smaller ask, and a different rule: 16 without consent for lobes and most "
            "other placements, and under that a parent is usually there with ID, so ring the shop "
            "first because the rules differ by council.")


def _a_teenagers_piercing(memory, understood):
    """The piercing rule first: the person asked about an ear, not about a tattoo."""
    age = _the_age_in_the_line(understood)
    he, him, his, does = _the_child_pronouns(memory, understood)
    if age and age.isdigit() and int(age) >= 16:
        lead = ("At %s %s can have lobes and most other placements pierced without a parent's "
                "consent, so this one is up to %s" % (age, he, him))
    elif age:
        lead = ("At %s a piercing needs you there: most studios want a parent present with ID, "
                "and many will only do lobes below 16" % age)
    else:
        lead = ("Under 16 a piercing usually needs a parent there with ID, and 16 is when lobes "
                "and most other placements stop needing consent")
    return (lead + ". Ring the shop before you go, because the age rules and the placements "
            "allowed differ by council, and only a licensed studio is worth using: gloves, "
            "sterile sealed needles, a hollow needle rather than a gun for anything but lobes, "
            "and written aftercare. A nose ring or a navel heals for months and wants cleaning "
            "twice a day, so agree who does that before the appointment. A tattoo is a different "
            "rule: 18, no exceptions.")

ENTRIES += [
    # "my 14 year old wants a tattoo" was acknowledged and dropped ("I'll remember that"),
    # and "can my 15 year old get her ears pierced" reached nothing. A parent is asking what is
    # allowed and what they are letting themselves in for, which is answerable - and the two are
    # two rows, because the first sentence has to be the rule for the thing that was asked
    # about: one card opened a piercing question with "a tattoo is 18" and told a 16 year old
    # about a 14 year old.
    # The rule is asked about in the abstract as well as about a named child: "what age can you
    # get a tattoo in the uk" was answered by the ageing card ("Ageing is the slow build-up of
    # small damage") and "how old do you have to be to get a tattoo" was a search hedge, because
    # both rows named only the child. The age words are a person here: a line that asks what age
    # it is allowed is asking about the child whoever it belongs to.
    entry("a-teenager-wants-a-tattoo",
          (("daughter", "son", "teenager", "teenagers", "teen", "my girl", "my boy",
            "year old", "13 year old", "14 year old", "15 year old", "16 year old",
            "17 year old", "is 13", "is 14", "is 15", "is 16", "is 17",
            "what age", "how old", "old enough", "legal age", "age limit", "is it legal",
            "whats the age", "minimum age", "too young", "under 18", "under 16",
            # "is a tattoo legal at 16" was answered with a school penalty notice: the age is
            # there as "at 16" rather than as a year old, and the ask was the law itself
            "legal", "illegal", "allowed", "against the law", "is it legal"),
           ("tattoo", "tattoos", "tattooed", "tattooing")),
          _a_teenagers_tattoo,
          ask=("my", "can", "should", "is", "what", "how"),
          # a piercing is its own row, and so is an adult's own tattoo
          avoid=("hair", "dye", "hair dye", "school", "tattoo removal", "remove a tattoo",
                 "laser", "my tattoo", "infected", "infection", "swollen", "my ear",
                 "piercing", "piercings", "pierced", "pierce")),
    entry("a-teenager-wants-a-piercing",
          (("daughter", "son", "teenager", "teenagers", "teen", "my girl", "my boy",
            "year old", "13 year old", "14 year old", "15 year old", "16 year old",
            "17 year old", "is 13", "is 14", "is 15", "is 16", "is 17",
            "what age", "how old", "old enough", "legal age", "age limit", "is it legal",
            "whats the age", "minimum age", "too young", "under 18", "under 16",
            # "is a tattoo legal at 16" was answered with a school penalty notice: the age is
            # there as "at 16" rather than as a year old, and the ask was the law itself
            "legal", "illegal", "allowed", "against the law", "is it legal"),
           ("piercing", "piercings", "pierce", "pierced", "ears pierced", "ear pierced",
            "earrings", "belly button", "nose ring", "navel", "helix", "tragus", "lobe",
            "lobes")),
          _a_teenagers_piercing,
          ask=("my", "can", "should", "is", "what", "how"),
          avoid=("hair", "dye", "hair dye", "school", "infected", "infection", "swollen",
                 "nosebleed", "my ear hurts", "tattoo", "tattoos")),
]
