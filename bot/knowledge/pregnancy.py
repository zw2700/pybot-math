"""Pregnancy: what is off the menu, and what is not.

"Can I eat brie when pregnant" is one of the most asked questions in the world, and the answer
is not a lecture about a healthy diet: it is a short list of foods a pregnant woman should skip,
each with the reason, and the reassurance that most of the kitchen is still fine. So the table is
keyed on the food and on the pregnancy, the same way keeping.py keys a food that has gone off on
the food and the sign, and one row is a food or a group of foods that share a verdict.

The advice is the NHS line as it stands in the UK, because the details people ask about are UK
details: British Lion eggs are fine runny, hard cheese is fine, and the caffeine figure is 200mg
a day. Where a line has no food in it at all ("what can I eat", "how much coffee") the row is
keyed on the general words, so "what can't i eat when pregnant" still gets the list.
"""
import datetime
import re

from .lookup import entry

ANSWERS = ("health", "food-and-drink")


def _a_late_that_is_not_a_period(understood):
    """False when "late" in this line is lateness, and the cycle rows should stand aside.

    "im on lates this week" is a week of two-till-ten, not a period that is late: "lates" was
    read as "late" and reached the cycle card. A line that names a period as well keeps the
    entry: "im on lates and my period is late" is still a late period.

    The second shape is the same fault without a roster in it: "they fired me for being late
    every day" and "im late for work again" were answered with the advice for a period that has
    not come, because "late" is on the key and nothing said which late it was. The reading says
    it now - `understood["sense"]["late"]` is `time` when the line names something a person is
    late for (a boss, a bus, an interview, a deadline) and `cycle` when it names the cycle - and
    only `time` changes anything here: a line that says neither keeps the card it had.
    """
    if not isinstance(understood, dict):
        return True
    if (understood.get("sense") or {}).get("late") == "time":
        return False
    if not understood.get("shift"):
        return True
    text = understood.get("clean") or ""
    return bool(re.search(r"\b(?:periods?|cycles?|pregnan\w*|tests?)\b", text, re.I))

# How people say they are pregnant. The key needs two covered words, so this only ever counts
# together with a food word: "am i pregnant" and "pregnancy test" reach nothing here.
PREGNANT = ("pregnant", "pregnancy", "pregnancies", "expecting a baby", "expecting our baby",
            "trimester", "weeks pregnant", "months pregnant", "im having a baby",
            "i'm having a baby", "baby on the way", "antenatal", "first baby", "second baby",
            "third baby")

# What a pregnant person might ask whether they can still do: one verdict for all of them, so
# the row below is keyed on the movement rather than on the sport.
PREGNANT_MOVEMENT = ("exercise", "exercising", "workout", "work out", "workouts", "gym",
                     "run", "running", "jog", "jogging", "swim", "swimming", "lengths",
                     "weights", "lift", "lifting", "weight training", "strength training",
                     "yoga", "pilates", "spin", "spinning", "cycling", "cycle", "bike",
                     "walking", "walks", "hike", "hiking", "dance", "dancing", "zumba",
                     "tennis", "badminton", "netball", "football", "hockey", "climbing",
                     "horse riding", "riding", "skiing", "ski", "crossfit", "fitness class",
                     "aerobics", "training", "keep fit", "stay active", "active")

# A line is not a question about food in pregnancy: it is about the mother's body, the baby, a
# test, the birth, or a supplement, and each of those has its own answer elsewhere.
NOT_FOOD = (
    "morning sickness", "nausea", "sick every", "bleeding", "bleed", "spotting", "cramps",
    "cramping", "scan", "scans", "midwife", "labour", "labor", "birth", "c-section", "induction",
    "glucose test", "gestational", "pre-eclampsia", "blood pressure", "kick", "kicks",
    "movement", "movements", "heartbeat", "twins", "miscarriage", "ectopic", "test", "tests",
    "folic acid", "vitamin d", "vitamin a", "supplement", "supplements", "paracetamol",
    "ibuprofen", "medicine", "medication", "tablet", "tablets", "antibiotic", "vaccine",
    # a symptom is not a food: "my headache is bad and im 8 weeks pregnant" was told that
    # the food was not on the list of things to avoid
    "headache", "headaches", "migraine", "migraines", "pain", "painful", "sore",
    "soreness", "ache", "aches", "aching", "hurts", "hurting", "toothache",
    "travel", "flight", "fly", "flying", "sleep", "sleeping", "sex", "exercise", "gym",
    "swim", "swimming", "bump", "back", "backache", "heartburn", "constipation", "swollen",
    "stretch marks", "weight gain", "how much weight", "mood", "anxious", "anxiety", "sick of",
    "not pregnant", "no longer pregnant", "was pregnant", "weren't pregnant",
    "breastfeeding", "breastfeed", "nursing", "formula", "weaning", "my wife is not",
    "trying to get pregnant", "trying for a baby", "ivf", "fertility", "baby shower",
    "baby names", "nursery", "pram", "pushchair", "cot", "nappy", "nappies",
    # a raw or runny egg has its own answer in cooking.py that already covers pregnancy
    "egg", "eggs", "runny egg", "raw egg", "mayonnaise", "mayo", "dippy",
)

LIST = ("The list is short: no soft mould-ripened or blue cheese unless it is cooked until "
        "steaming, no pate or liver, no raw or undercooked meat, fish or shellfish, and nothing "
        "made with unpasteurised milk. "
        "Everything else is fine - hard cheese, cooked eggs, cooked fish, peanuts, fruit and veg "
        "- though wash the veg and heat leftovers until they are steaming hot, because listeria "
        "is the reason for the whole list and it is killed by heat.")

# The foods people worry about most in pregnancy, and the verdict for each. None of them is on the
# short list, so the answer is a plain yes with the reason: "is pineapple safe in pregnancy" was
# answered with the pineapple-on-pizza opinion, "is mango safe in pregnancy" and "is hummus safe
# in pregnancy" were shrugs, and "can i eat mango when pregnant" got the general list. The verdict
# is keyed on the food, not on the wording, so every way of asking about it reaches the same line.
PREG_WORRY_FOODS = (
    (("pineapple", "pineapples", "pineapple juice"),
     "Fine. Pineapple does not bring on labour: the enzyme people blame for it is in the stem, "
     "not in the fruit you eat, and a portion has nowhere near enough of it to do anything. So "
     "have it fresh, tinned or juiced - the myth is the only thing to worry about."),
    # Juice is a drink, not a piece of fruit, and the fruit row answered it as one: "can i drink
    # orange juice while pregnant" was told "Fine, and worth eating: fruit is where most of the
    # vitamin C comes from. Rinse it under the tap first" (jolly-crane, #9118). It comes before
    # the fruit row so it wins the tie, and after pineapple so "pineapple juice" keeps its answer.
    (("juice", "juices", "orange juice", "apple juice", "fruit juice", "grapefruit juice",
      "cranberry juice", "tomato juice", "a glass of juice"),
     "Juice is fine: the cartons and bottles in a shop are pasteurised already, so nothing on the "
     "pregnancy list applies to them, and juice you squeeze yourself is fine if you wash the fruit "
     "and drink it the same day. It is mostly sugar without the fibre that slows it down, so one "
     "glass with a meal is the habit to aim for rather than sipping it through the day, and whole "
     "fruit is the better version of the same vitamins."),
    (("mango", "mangoes", "mangos", "melon", "melons", "watermelon", "grapes", "grape", "kiwi",
      "kiwis", "berries", "strawberries", "blueberries", "raspberries", "blackberries",
      "peach", "peaches", "pear", "pears", "plum", "plums", "banana", "bananas", "orange",
      "oranges", "apple", "apples", "pineapple chunks", "satsuma", "satsumas", "clementine",
      "clementines"),
     "Fine, and worth eating: fruit is where most of the vitamin C comes from. Rinse it under the "
     "tap first, because listeria and toxoplasmosis are on the outside of fruit and veg rather "
     "than in it, and a melon wants washing before it is cut, not after. Fruit juice is fine too, "
     "but it is sugary - whole fruit is the better habit."),
    (("papaya", "papayas", "pawpaw", "pawpaws", "green papaya", "unripe papaya"),
     "Ripe papaya is fine. The one to leave is the unripe green papaya, and papaya skin and seeds: "
     "unripe papaya carries a latex-like substance that is said to act on the womb, so a green "
     "papaya salad is one to skip for nine months. A ripe orange one is a good breakfast."),
    (("honey",),
     "Fine for you. The warning about honey is for babies under one, whose gut can let botulism "
     "spores grow - it does not apply to you or to the baby before birth. It is still sugar, so a "
     "spoon in a drink rather than a jar a day."),
    (("hummus", "houmous", "humous", "tahini", "houmus"),
     "Fine, including the tubs from the supermarket: shop hummus is made with pasteurised sesame "
     "and chickpeas, and sesame is not one of the allergens to avoid in pregnancy. Keep an opened "
     "tub in the fridge and eat it within a couple of days, because it is a cold food and the "
     "listeria advice is about cold food."),
    (("spicy food", "spicy", "curry", "curries", "chilli", "chili", "chillies", "chilies",
      "hot sauce", "spices", "spice"),
     "Fine. Spicy food does not bring on labour or harm the baby, and the old advice to avoid it "
     "was about the mother's comfort. If you get heartburn, which is common later on, it is worth "
     "eating smaller amounts more often rather than avoiding spice altogether."),
    (("ice cream", "icecream", "soft serve", "soft-serve", "soft whip", "milkshake",
      "milkshakes"),
     "Fine from a tub: ice cream is made with pasteurised milk. The one to skip is soft-serve from "
     "a machine, the sort that sits in a hopper all day - that is the cold-served food listeria "
     "has been found in, and a machine that is not cleaned often is the risk. A scoop from a shop "
     "tub is no riskier than a supermarket one."),
    (("coleslaw", "slaw", "potato salad", "deli salad"),
     "Fine from a packet or a supermarket tub, which is made with pasteurised mayonnaise. The one "
     "to skip is salad that has been sitting out on a deli counter, and anything you are unsure "
     "has been kept cold: listeria grows in food that is kept cold for a while, not in food that "
     "is freshly made."),
    (("bean sprouts", "beansprouts", "sprouts", "sprouted seeds", "alfalfa"),
     "Cook them through, or leave them: raw bean sprouts and sprouted seeds are one of the foods "
     "listeria and salmonella have been found in, and washing does not reliably clear them. "
     "Sprouts cooked into a stir fry, a curry or a soup are fine."),
    (("olives", "pickles", "gherkins", "sauerkraut"),
     "Fine, and the vinegar or brine they are in is not a problem. They are salty, so if your "
     "ankles or blood pressure are being watched, keep them to a few rather than a bowl."),
    (("dates", "dates fruit"),
     "Fine, and a good snack: they are sweet, so they are the thing to reach for instead of a "
     "biscuit at four in the afternoon. There is no evidence they bring on labour, whatever "
     "you read."),
)

# Nothing on the short list: the general answer for a fruit, a vegetable or another everyday food
# asked about with "safe" or "ok" in the line. It names the list, so a person who is worried gets
# both halves - this food is fine, and here is what is not.
# A drink with its own card is not this row's line. This row's reply is "that food is not on
# the list of things to avoid, so it is fine", which is right for a biscuit and badly wrong for
# wine: on main "is it safe to drink alcohol when pregnant", "is a glass of wine ok while
# pregnant", "is alcohol safe when pregnant", "is it safe to drink beer when pregnant" and "is it
# safe to drink tea when pregnant" all got that sentence, while "can i drink wine while pregnant"
# got the right answer. The caffeine and alcohol rows already stand down for each other's drinks;
# this row is the one that has to stand down for both, because it is the catch-all.
# The names, not the pouring words: "a glass of" and "drink" alone belong to water and juice as
# much as to wine, and with them in this list "is it safe to have a glass of water when pregnant"
# left the catch-all for the alcohol warning.
DRINKS_WITH_THEIR_OWN_ANSWER = (
    "alcohol", "wine", "beer", "lager", "cider", "stout", "ale", "prosecco", "champagne", "gin",
    "vodka", "whisky", "whiskey", "rum", "brandy", "tequila", "booze", "cocktail", "cocktails",
    "coffee", "caffeine", "decaf", "tea", "espresso", "latte", "cappuccino", "energy drink",
    "energy drinks", "cola", "diet coke", "hot chocolate", "mulled wine", "alcopop")

PREG_ANY_FOOD = (
    "That food is not on the list of things to avoid, so it is fine. The list is short: no "
    "mould-ripened or blue cheese unless it is cooked until steaming, no pate or liver, no raw "
    "meat, fish or shellfish, and nothing made with unpasteurised milk. Wash fruit and veg and "
    "heat leftovers until steaming - listeria is why the list exists, and heat kills it.")


def _preg_food(memory, understood):
    """The worry food the line names, by meaning; otherwise the general safe-food answer."""
    words = set(understood.get("words") or ())
    joined = " ".join(understood.get("words") or ())
    for names, reply in PREG_WORRY_FOODS:
        for name in names:
            if " " in name:
                # "ice cream", "bean sprouts", "spicy food": a phrase is two words on the line,
                # so it is looked for in the line as written rather than word by word
                if name in joined:
                    return reply
                continue
            if name in words or (name.endswith("s") and name[:-1] in words):
                return reply
    return PREG_ANY_FOOD


# Am I pregnant, my period is late, the test was positive: the three lines people send before
# there is a fact to file. `PREGNANT` above is the food table's second key and needs a food word
# beside it, so every one of these reached the mood pool instead - "i think im pregnant" was
# answered "Brilliant. Thanks for telling me.", "am i pregnant" was a search hedge, and "i might
# be pregnant and i dont want to be" was answered with the alcohol warning, as if it were a
# wanted baby. The test is the answer to all three, so they share one section.
# The doubt words, which is what makes the line a question rather than a fact: "i might be",
# "i think i'm", "am i", "could i be". A bare "pregnant" is not enough on its own (score 2, under
# MIN_SCORE), so "i am pregnant" stays with the composer and only the doubting line comes here.
AM_I = ("am i", "am i not", "could i be", "could i", "might be", "might i", "maybe", "perhaps",
        "possibly", "possible", "think", "think im", "think i'm", "suspect", "wondering",
        "not sure", "unsure", "no idea", "or not", "when will i know", "how do i know",
        "how can i tell", "signs", "symptoms", "early", "missed")

# "early" is not in here on purpose: a period that came early is the opposite of one that has not
# come, and "my period came two weeks early" was being answered as a late one.
WHEN = ("period", "periods", "missed period", "late period", "period late", "no period",
        "periods late", "period hasnt come", "period hasn't come", "period not come",
        "late", "late by", "days late", "weeks late", "due date", "baby due",
        "when am i due", "due date is", "missed", "irregular")
# "Due" on its own is not here: rent, a library book and a bill are all due on a date, and "when
# is my rent due" was answered with the late-period card. The phrases above are the ones only a
# pregnancy says; the due date itself has its own row below.

# These say the line is about a test, so the row keyed on them needs a word of this kind in it.
# "two lines" is not on the list, though it is the result: it is already the first part of the
# positive card, and with it here one span satisfied both halves of that key. "what should i put
# in a two-line bio for a conference badge" was answered with the booking-in appointment, because
# the hyphen reads as "two lines". A faint line stays, because nothing else says it.
TEST_WORDS = ("pregnancy test", "test", "tests", "tested", "faint line",
              "clearblue", "test kit", "test strip", "test strips", "positive", "negative")

# A pregnancy that is already a fact, not a doubt: "i am pregnant, what do i do" is not asking
# for a test. The composer keeps the bare fact (a congratulation is the honest reply to "im
# pregnant" on its own); these are the shapes that would otherwise reach the test card.
PREGNANT_ALREADY = ("im pregnant what", "i am pregnant what", "i'm pregnant what",
                    "im pregnant now what", "i am pregnant now what",
                    "im pregnant so what", "i am pregnant so what",
                    "found out im pregnant what", "found out i am pregnant what")

# Words that say the line is about cycles in general rather than one period that is late: "what
# is a normal period", "my period lasts 10 days", "how many days between periods".
CYCLE_SHAPE = ("normal", "how long", "how often", "how many days", "days between", "lasts",
               "started", "when do periods", "first period", "regular")

# A fertility question, not a doubt about this month: "can i get pregnant on my period" asks how
# conception works, so neither the test card nor the late card is its answer - it keeps whatever
# reply it had before these rows existed. The shapes are the interrogative ones only: bare "get
# pregnant" is left out on purpose, because "im trying to get pregnant and my period is late" is
# a late period first, and it must keep the late card.
FERTILITY = ("get pregnant on", "get pregnant after", "get pregnant if", "get pregnant while",
             "get pregnant from", "pregnant on my period",
             "conceive", "conceiving", "conception", "ovulate", "ovulating", "ovulation",
             "fertile", "fertility", "chance of", "chances of", "how likely")

# A test that is not this test. Two common words ("test" and "positive") are enough to reach an
# answer, so the other tests in a life are listed rather than hoped for.
NOT_A_TEST = ("covid", "coronavirus", "lateral flow", "pcr", "mot", "theory", "driving test",
              "eye test", "blood test", "urine test", "hearing test", "smear", "cervical",
              "chlamydia", "sti", "std", "thyroid", "diabetes", "allergy", "intolerance",
              "paternity", "dna", "quiz", "exam", "revision", "mock", "interview", "coding",
              "swab", "skin prick")

TEST_REPLY = (
    "A test is the answer, and the timing is the part people get wrong: from the day your period "
    "is due, on the first pee of the morning, which has the most hormone in it. A faint second "
    "line is still a line. If it is negative and nothing comes in three days, test again, because "
    "the hormone doubles every couple of days. Early signs - sore breasts, going off food, "
    "tiredness, feeling sick - are not reliable enough to go on either way. If you would rather "
    "not be pregnant, a GP or a sexual health clinic will go through the options without pushing "
    "you either way, and the sooner you ring the more there is to choose from.")

POSITIVE_REPLY = (
    "Ring the GP surgery and say you have had a positive test: the booking-in appointment is "
    "usually between 8 and 10 weeks, and they will sort the midwife, the scans and the bloods. "
    "Start 400 micrograms of folic acid and 10 micrograms of vitamin D every day, and stop "
    "alcohol - most of what you eat is still fine, and the list of what is not is short. If the "
    "line was faint or early, test again in three days. A negative test with no period in three "
    "days is worth testing again; a positive one with pain or bleeding is a call to the GP or "
    "111 rather than something to sit on.")

NEGATIVE_REPLY = (
    "A negative test this early is worth repeating rather than believing: test again in three "
    "days, first pee of the morning, because the hormone doubles every couple of days and an "
    "early test can simply be too soon. Plenty else shifts a period - stress, a bug, a bad "
    "month of sleep, a change in weight, travel, the pill - so one late period with a negative "
    "test is common and usually settles. Ring the GP if nothing comes for three months, if the "
    "tests stay negative but you feel pregnant, or if there is pain one side at all.")

EARLY_REPLY = (
    "A period that comes early is common and usually just a short cycle: stress, a bug, a change "
    "in sleep or travel, a big drop in weight, or the pill can all bring one on, and the spotting "
    "some people get at ovulation a couple of weeks before is often taken for one. Write the "
    "dates down for the next two or three - if they stay under three weeks apart, if you bleed "
    "between periods or after sex, or if the bleeding is very heavy, that is a GP appointment. "
    "If there is any chance you could be pregnant, test anyway: a bleed can happen early on.")

CYCLE_REPLY = (
    "The usual cycle is 21 to 35 days from the first day of one period to the first day of the "
    "next, and the bleeding itself is usually two to seven days - up to eight is still normal. "
    "What is worth a GP appointment: cycles closer than 21 days or longer than 35, bleeding that "
    "lasts more than eight days, bleeding between periods or after sex, soaking a pad or tampon "
    "an hour for several hours, or three months with no period at all. Write the dates down for "
    "three cycles first, because that is what the GP will ask for, and the pill can change the "
    "pattern while you are on it.")

LATE_REPLY = (
    "Plenty shifts a period by a few days - stress, a bug, a bad month of sleep, a change in "
    "weight, travel, the pill - so the useful next step is a test rather than a wait: from the "
    "day it was due, first pee of the morning, and again in three days if it is negative and "
    "nothing comes. Three months without a period, bleeding between periods or after sex, or a "
    "positive test with pain or bleeding is a GP appointment. If your cycles were always "
    "irregular, a few weeks late on its own is not alarming.")

_FEEDING_WORDS = ("breastfeed", "breastfeeding", "breast feeding", "breast fed", "breastfed",
                  "nursing", "nurse", "lactating", "chestfeeding", "expressing",
                  "pumping", "feeding")


# ------------------------------------------------------------------ when is the baby due
#
# The date a pregnancy is owed is arithmetic, and people ask for it in their own words: "when is
# my due date", "when is the baby due", "how many weeks am i". It was answered with a search
# hedge ("that is beyond what I know well"), with the late-period card, or - worse, on "im 12
# weeks pregnant when is my due date" - with the answer about eating dates. One row answers the
# whole family, and it does the sum when the line gives it the one figure the sum needs: the
# first day of the last period, or how many weeks the person is now.
#
# The words that ask when a baby is due. A "when ... due" on its own is not enough: "when am i
# due back at work" and "im due a tax refund" say the word and ask nothing of a pregnancy, so
# the guard below wants a pregnancy word in the line as well.
_DUE_SHAPE = re.compile(
    r"\b(?:due date|due dates|baby due|baby is due|due in|when am i due|when are you due|"
    r"weeks pregnant|weeks along|weeks am i|weeks gone|"
    r"how far along|how far gone|what week am i|which week am i|"
    r"how many (?:weeks?|wks?|months) (?:pregnant|preg|am i|along|into|gone|left|to go)|"
    r"how pregnant am i|pregnancy weeks|"
    r"how many weeks (?:is|does|are) (?:a |the |an )?pregnan\w*|"
    r"how many months (?:pregnant|along)|"
    r"how long (?:is|does|are|do|can) (?:a |the |an )?pregnan\w*|"
    r"how long (?:are you|is a woman|is she|is he) pregnant|"
    r"last period|first day of (?:my|her|your|the) last period|"
    r"lmp\b|"
    r"(?:when|what date|which date)\b[^.?!]{0,30}\bdue\b|"
    r"when will (?:the baby|my baby|she|he|it) (?:arrive|come|be born|get here)|"
    r"when (?:is|are) (?:the baby|my baby|she|he|it) born|"
    r"when (?:is|are) (?:the baby|my baby|she|he|it) (?:due|coming))", re.I)

# The line has to be about a pregnancy as well. Without it "how many weeks in a year" and "how
# long is my period" read as due-date questions on their shape alone.
_PREG_WORD = re.compile(
    r"\b(?:pregnan\w*|preg|expecting|baby|babies|due date|lmp|last period|"
    r"weeks (?:pregnant|preg|along|gone|am i)|birth|born|midwife)\b", re.I)
# "How far along am i" and "im 20 weeks, how far along is that" name no pregnancy word at all: the
# phrase is the pregnancy. They are read as pregnancy asks unless the line is plainly about
# something else being built or written, which is what the subject words below are for.
_PREG_SOFT = re.compile(
    r"\b(?:how far along|how far gone|weeks am i|wks am i|what week am i|which week am i|"
    r"when am i due|when are you due|"
    r"when (?:is|are) (?:she|he) due|"
    r"due (?:in|on) (?:january|february|march|april|may|june|july|august|september|"
    r"october|november|december))\b", re.I)
_OTHER_SUBJECT = re.compile(
    r"\b(?:essay|project|thesis|dissertation|book|build|renovation|course|game|sprint|"
    r"assignment|paper|novel|training|app|website)\b", re.I)

# "Due" has a second life that is not a baby: work, a refund, a payment. A line naming one of
# those is not a due-date question however much it looks like one.
_DUE_ELSEWHERE = re.compile(
    r"\bdue\s+(?:back|at work|for work|in work|"
    r"to (?:start|finish|go|leave|renew|pay|return|hand|come back)|"
    r"(?:a|an|any|some|my|the)?\s*(?:tax\s+)?(?:refund|rebate|payment|bill|rise|bonus|"
    r"money|fee|invoice))\b", re.I)

# A milestone in the pregnancy, not the date: "when will i feel the baby move", "when will i start
# showing", "when do the kicks start". The row read "when will i" as an ask for the date and
# answered a question nobody asked, so these stand it down and the milestone keeps its own answer.
_A_MILESTONE = re.compile(
    r"\bwhen (?:will|do|should|can)\b[^?]{0,40}?"
    r"\b(?:feel (?:the )?(?:baby|it|them|kicks?|movement|movements)|kicks? (?:start|begin)|"
    r"start (?:to )?(?:show|showing)|be showing|bump (?:show|appear|grow)|"
    r"feel (?:him|her) move|movement)\b", re.I)

# Only a period with no pregnancy beside it: "when is my period due", "when is my next period".
# Those belong to the late-period row, which is about waiting for one, not about a baby's date.
_PERIOD_ONLY = re.compile(r"\bperiods?\b", re.I)
_PERIOD_WITH_A_PREGNANCY = re.compile(
    r"\b(?:pregnan\w*|expecting|baby|babies|last period|lmp|weeks (?:pregnant|along|gone|am i)|"
    r"due date|when am i due|when are you due)\b", re.I)

_MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3, "april": 4,
    "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7, "august": 8,
    "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10, "oct": 10,
    "november": 11, "nov": 11, "december": 12, "dec": 12}
_DAY_THEN_MONTH = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([a-z]{3,9})\b", re.I)
_MONTH_THEN_DAY = re.compile(
    r"\b([a-z]{3,9})\s+(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?\b", re.I)
# A figure in weeks, but only when it is how the person dates the pregnancy: "im 30 weeks", "30
# weeks pregnant", "at 20 weeks". "in three weeks" and "three weeks ago" name no date yet.
# "How many weeks is a pregnancy" and "how long does a pregnancy last" ask about pregnancy, not
# about this person, so they get the 40 weeks. "How many weeks pregnant am i" gets the count.
_A_PREGNANCY = re.compile(r"\b(?:a|the|an) pregnanc(?:y|ies)|\bpregnancies\b|"
                          r"\bpregnancy last(?:s|ing)?\b|\bpregnancy norm(?:al|ally)\b", re.I)
_MY_OWN = re.compile(r"\b(?:am i|i am|i'?m|im|my|me|we|us|our)\b", re.I)
# The asks that want the count rather than the date: "how many weeks pregnant am i".
_ASKS_WEEKS = re.compile(
    r"\b(?:how many (?:weeks?|wks?|months)|how far along|how far gone|weeks am i|wks am i|"
    r"weeks pregnant|weeks along|weeks gone)\b", re.I)
_WEEKS_NOW = re.compile(
    r"\b(?:im|i'?m|i am|am|is|are|at|now|about|nearly|almost|just|only)\s+"
    r"(\d{1,2})\s*(?:weeks?|wks?)\b"
    r"|\b(\d{1,2})\s*(?:weeks?|wks?)\s+(?:pregnant|along|gone|in)\b", re.I)


# The line has to ask. A statement that dates a pregnancy - "im 6 weeks pregnant and have a
# temperature", "im 8 weeks pregnant what should i eat", "the baby is due in march" - is a
# complaint or a piece of news with a date on it, and its own row answers it; counting the due
# date back at it answered a question nobody asked and lost the temperature and the meal.
_SHORT_ASK = re.compile(r"\bdue date\b|\bhow far along\b", re.I)
_ASKED = re.compile(
    r"\bwhens?\b|\bwhen's\b|\bhow (?:many|far|long|soon|pregnant)\b|\bwhich date\b|"
    r"\bwhat date\b|\bwhat week\b|\bwhich week\b|\bpregnancy weeks\b|"
    r"\bcalculat\w* (?:my|the) due date\b|\bdue date calculator\b|"
    r"\bwhat(?:'s|s)? (?:is |was )?(?:my|the|your) (?:due date|date thing)\b", re.I)


# The other half of the same ask is the answer to it: the bot asks for the first day of the last
# period, so "3 may was the first day of my last period" and "my last period was 3 may" are
# figures to count from, not news. A day and the words for it are the whole signal.
_GIVES_THE_DAY = re.compile(r"\b(?:last period|period started|lmp|first day)\b", re.I)
_A_MONTH = re.compile(r"\b(?:january|february|march|april|may|june|july|august|september|"
                      r"october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|"
                      r"nov|dec)\b", re.I)


def _gives_a_month(line):
    """A month in the line is a day being given, which is the answer to the bot's own question.

    The bot asks for the first day of the last period, and the reply to that names a day and
    asks nothing: "my last period was 3 may", "my last period started on 3 may", "lmp was 3 may".
    None of those carries an ask word, so the row scored 0 and the cycle card, the puberty card
    and the greeting took them. A month is the figure this row counts from, so it is a signal in
    its own right - the same weight as a key word, so the subject still has to be in the line -
    and `_asks_when_due` is what keeps a mention in passing ("baby is due in march") off it.
    """
    return bool(_A_MONTH.search(line or ""))


def _asks_when_due(understood):
    """True for a line that asks when a baby is due, and for nothing that only looks like one."""
    line = " ".join(str((understood or {}).get("clean") or "").split())
    if not line or not _DUE_SHAPE.search(line):
        return False
    if not _ASKED.search(line) and not (_GIVES_THE_DAY.search(line) and _A_MONTH.search(line)):
        # "due date?" and "my due date" are the whole line: that is the question, however it is
        # punctuated, and a two-word line cannot be about anything else.
        if not (_SHORT_ASK.search(line) and len(line.split()) <= 4):
            return False
    if _DUE_ELSEWHERE.search(line) or _A_MILESTONE.search(line):
        return False
    if _PERIOD_ONLY.search(line) and not _PERIOD_WITH_A_PREGNANCY.search(line):
        return False
    if _PREG_WORD.search(line):
        return True
    return bool(_PREG_SOFT.search(line)) and not _OTHER_SUBJECT.search(line)


def _the_day(date, today):
    """A date as a person says it: "7 February", with the year only when it is not this one."""
    said = f"{date.day} {date.strftime('%B')}"
    return said if date.year == today.year else f"{said} {date.year}"


def _the_date_named(line, today):
    """The day the line names, or None. A last period is always in the past, so a date still to
    come in this year is last year's: "my last period was 3 may" said in November is 3 May."""
    for match in _DAY_THEN_MONTH.finditer(line):
        day, month = int(match.group(1)), _MONTHS.get(match.group(2).lower())
        if month is not None:
            date = _the_date_in_this_year(today, month, day)
            if date:
                return date
    for match in _MONTH_THEN_DAY.finditer(line):
        month, day = _MONTHS.get(match.group(1).lower()), int(match.group(2))
        if month is not None:
            date = _the_date_in_this_year(today, month, day)
            if date:
                return date
    return None


def _the_date_in_this_year(today, month, day):
    for year in (today.year, today.year - 1):
        try:
            date = datetime.date(year, month, day)
        except ValueError:  # a 31 in a month of 30, or a figure that is no day at all
            return None
        if date <= today + datetime.timedelta(days=3):
            return date
    return None


def _the_weeks_named(line):
    """How many weeks along the line says the person is, or None."""
    for match in _WEEKS_NOW.finditer(line):
        figure = match.group(1) or match.group(2)
        if figure:
            weeks = int(figure)
            if 1 <= weeks <= 45:
                return weeks
    return None


# The rule and where the date is written down: the answer when the line gives no figure to count
# from. (The row was a card before it could do the sum, and this is that card.)
CARD = ("Forty weeks from the first day of your last period, so count 280 days from it "
        "(nine months and a week): a midwife writes that date in your notes at your "
        "booking-in appointment, and the dating scan can move it by a few days. If you have "
        "neither to hand, the date on your scan report or in your maternity notes is the one "
        "they will go by. Weeks gone are counted from that same first day of your last "
        "period, not from the day you conceived.")


def _preg_due_date(memory, understood):
    """When the baby is due: the date from the figures the line gives, else the rule and an ask.

    A due date is 40 weeks - 280 days - from the first day of the last period, so a line that
    gives that day gets the date worked out, and a line that gives how many weeks the person is
    now gets the weeks that are left counted on from today. A line that gives neither gets the
    rule itself and one question, because the bot cannot see a date the person has not said.
    """
    line = " ".join(str((understood or {}).get("clean") or "").split())
    today = datetime.date.today()
    weeks = _the_weeks_named(line)
    if weeks is not None:
        left = 40 - weeks
        if left < 0:
            return (f"At {weeks} weeks you are past the 40-week due date, so the date on your "
                    "notes and your midwife are the ones to go by now. Most places offer an "
                    "induction by 41 or 42 weeks, and she will talk you through what happens "
                    "next - worth asking her at your next appointment rather than waiting.")
        date = today + datetime.timedelta(days=left * 7)
        return (f"Week {weeks} of 40 leaves {left} weeks to go, which puts the due date at about "
                f"{_the_day(date, today)}. That is the 40-week count, but the dating scan at 11 "
                "to 14 weeks is the date the midwife goes by, so go by what is on the notes if "
                "the scan moved it.")
    named = _the_date_named(line, today)
    if named is not None:
        date = named + datetime.timedelta(days=280)
        said = (f"Counted from the first day of the last period, {_the_day(named, today)}, the "
                f"due date is about {_the_day(date, today)} - 40 weeks, or 280 days, later. ")
        days = (today - named).days
        if 0 <= days <= 300:
            return (said + f"That makes you {days // 7} weeks now. The dating scan at 11 to 14 "
                    "weeks is the date the midwife goes by, so if it moved the date, the scan is "
                    "the one that counts.")
        return (said + "If that is not the day you meant, tell me the first day of the last "
                "period as a date and I will work it out again.")
    # No figure in the line, so the answer is the card: how the count goes, and where the date is
    # written down.
    return CARD


def _preg_hair_dye(memory, understood):
    """Dyeing in pregnancy, or while breastfeeding - two different questions.

    The row keys both, and its one card opened on pregnancy: a mother asking about feeding was
    told it was fine in pregnancy and to wait twelve weeks, which answers a question she did not
    ask. The feeding answer is shorter and has no twelve-week line in it, so the line decides.
    """
    line = " " + str((understood or {}).get("clean") or "") + " "
    if any((" " + word + " ") in line or word in line for word in _FEEDING_WORDS):
        return ("A colour is fine while you are breastfeeding: the dye does not get into your "
                "milk, so nothing reaches the baby through a feed. Keep the room aired, wear the "
                "gloves that come with the kit and do the 48-hour patch test first, because skin "
                "can react differently after a baby. Highlights or a semi-permanent keep the dye "
                "off your scalp if you would rather be careful, and a salon can do the mixing for "
                "you.")
    return ("Fine, and there is no evidence hair dye harms a baby: the amount that reaches your "
            "bloodstream through the scalp is tiny. Plenty of women wait until after 12 weeks "
            "before colouring, which is a reasonable choice rather than a rule. Have the patch "
            "test as usual, keep the dye off a cut or an eczema patch, and make sure the room is "
            "ventilated if you are doing it at home.")


# --------------------------------------------------------------------- the birth, and the bag
# The last month brings the same two questions, and both were the shrug: "how long does labour
# take" and "when should i pack my hospital bag" got "I'm not sure about that one", and "how long
# is labour for a first baby" was answered with the trying-for-a-baby card. A time asked for in a
# birth is a time, and these are the figures the midwife gives.
_TIME_ASK = re.compile(
    r"\bhow long\b|\bhow many hours\b|\bhow many days\b|\bhow soon\b|\bhow early\b|"
    r"\bwhen should i\b|\bwhen do i\b|\bwhen to\b|\bwhat week\b|\bhow far along\b|"
    r"\bwhat (?:should|shall|can|do) i (?:take|bring|pack|put)\b|"
    r"\bwhat do i (?:need|want|have) to (?:pack|take|bring)\b|"
    r"\bwhat to (?:take|bring|pack)\b|"
    r"\blonger\b|\bshorter\b|\bquicker\b|\bfaster\b|\blongest\b|\btoo long\b", re.I)
# "labour" is a wage, a garage bill and a political party as well as a birth, so the row wants the
# birth senses of the word and stands down on the others.
_BIRTH_WORD = re.compile(
    r"\bin labour\b|\bin labor\b|\blabour\b|\blabor\b|\bgiv(?:e|ing) birth\b|"
    r"\bthe birth\b|\bbirth\b|\bcontractions?\b|\bwaters\b|\bc-section\b|"
    r"\bc section\b|\bcaesarean\b|\bcesarean\b|\bepidural\b|\bpregnan\w*\b|"
    r"\bbaby\b|\bdelivery\b|\bhospital bag\b|\bmaternity bag\b|\bmaternity\b|"
    # the stages of the birth are asked about by name, without the word labour: "how long does
    # the second stage last" and "how long is pushing" were both a plain hedge on main.
    r"\b(?:first|second|third) stage\b|\bstage of (?:labour|labor|birth)\b|"
    r"\bpushing stage\b|\bhow long (?:is|does) pushing\b|\bplacenta\b", re.I)
_NOT_THE_BIRTH = (
    "car", "cars", "garage", "mot", "bill", "bills", "quote", "wage", "wages", "hourly",
    "party", "mp", "mps", "election", "vote", "voted", "government", "council", "worker",
    "workers", "job", "jobs", "engine", "clutch", "cambelt", "servicing", "price", "cost",
    "union", "manifesto", "poll", "brexit", "tax", "budget",
    # placenta praevia is a condition with its own care, not a stage of the birth
    "praevia", "previa",
)
_SECOND_BIRTH = re.compile(r"\bsecond\b|\bthird\b|\bfourth\b|\bnot my first\b|"
                           r"\banother baby\b|\b2nd\b|\b3rd\b|\bnot the first\b", re.I)
# "how long until i can drive after birth" is the wait, not the birth: a line that names a thing
# to do afterwards has its own answer elsewhere (the caesarean recovery row, or the health one),
# and the labour figure is a wrong answer to it.
_AFTER_THE_BIRTH = re.compile(
    r"\bdriv(?:e|ing)\b|\bexercise\b|\bexercising\b|\bgym\b|\bswim(?:ming)?\b|"
    r"\bbath\b|\bbath(?:e|ing)\b|\bback to work\b|\bto work\b|\blift(?:ing)?\b|"
    r"\bsex\b|\bstitches\b|\bbleed(?:ing)?\b|\bperiod\b|\bwash my hair\b|"
    r"\balcohol\b|\bdrink\b|\brun(?:ning)?\b|\bwalk(?:ing)?\b|\bhoover\b|"
    r"\bhousework\b|\bpelvic floor\b|\bscar\b|\brecover\w*\b|\bheal\w*\b|"
    r"\bnumb\b|\bcontinence\b|\bpostnatal\b|\bpost natal\b", re.I)


def _the_line(understood):
    return " ".join(str((understood or {}).get("clean") or "").split())


def _asks_a_birth_time(understood):
    """True for a question about how long the birth takes, and for nothing that reads like one."""
    line = _the_line(understood)
    if not line or not _TIME_ASK.search(line) or not _BIRTH_WORD.search(line):
        return False
    if _AFTER_THE_BIRTH.search(line):
        return False  # the wait to do something afterwards is not the length of the birth
    words = set(re.findall(r"[a-z']+", line.lower()))
    return not words & set(_NOT_THE_BIRTH)


def _asks_about_the_bag(understood):
    """True for "when do I pack the bag", so a labour question about going in does not get it."""
    line = _the_line(understood)
    if not line or not _TIME_ASK.search(line):
        return False
    if not re.search(r"\bpack\b|\bpacked\b|\bpacking\b", line, re.I):
        return False
    return bool(re.search(r"\bhospital\b|\bmaternity\b|\bbag for\b|\bdelivery\b", line,
                          re.I))


def _preg_labour_length(memory, understood):
    """How long a labour lasts: the figure people ask for, and what "early labour" really means.

    Three questions hide behind the same words, and each has its own figure: the whole labour,
    one contraction, and the stay in hospital afterwards. "how long do contractions last" was
    answered with the 8 to 18 hours of a labour, which is a different question.
    """
    line = _the_line(understood)
    if re.search(r"\bin hospital\b|\bstay in\b|\bstay at\b|\bcome home\b|\bgoing home\b|"
                 r"\bhow long do i stay\b", line, re.I):
        return ("After a straightforward birth most women are home within a day: a few hours if "
                "everything is well and it is not your first, overnight or a day or two with a "
                "first baby. A caesarean is two to four days, and any concern about you or the "
                "baby adds a day, so plan for the longer end when you arrange a lift home.")
    if re.search(r"\bcontractions?\b", line, re.I) and not re.search(
            r"\blabour\b|\blabor\b|\bthe birth\b|\bgiv(?:e|ing) birth\b", line, re.I):
        return ("Each contraction usually lasts 30 to 60 seconds early on, then 60 to 90 seconds "
                "once labour is established, with a few minutes between them. They get longer, "
                "stronger and closer together as it goes on - that pattern is what tells you it "
                "is real labour rather than the practice tightenings. Ring the midwife if one "
                "lasts much longer than 90 seconds, or there is no gap between them.")
    if re.search(r"\blongest\b|\btoo long\b|\bstall(?:ed|ing)?\b|"
                 r"\bhow long can (?:a |the |my )?(?:labour|labor|it|this) (?:go|last|be)\b|"
                 r"\bgo on for\b", line, re.I):
        return ("There is no fixed limit: a first labour is usually under 18 hours once it is "
                "established, but slow is not the same as dangerous, and they go by how it is "
                "progressing, how you are and how the baby is rather than the clock. If it "
                "stalls they offer to break the waters or a hormone drip, and if it is not "
                "moving at all they talk to you about a caesarean. Ask what has changed each "
                "time they examine you.")
    if re.search(r"\b(?:first|second|third|1st|2nd|3rd) stage\b|\bpushing\b|"
                 r"\bplacenta (?:take|takes|come|comes|coming|out)\b|"
                 r"\bdelivery of the placenta\b|\bskin to skin\b", line, re.I):
        if re.search(r"\bfirst\b|\b1st\b", line, re.I):
            return ("The first stage is the long part: the cervix opening to 10cm, which takes "
                    "most of the 8 to 18 hours of a first labour and is much quicker with a "
                    "second. It starts with contractions you can talk through and ends with "
                    "strong ones a few minutes apart - that middle stretch, 4 to 6cm, is usually "
                    "the hardest, so ask for pain relief before you need it.")
        if re.search(r"\bthird\b|\b3rd\b|\bplacenta\b|\bskin to skin\b", line, re.I):
            return ("The third stage is the placenta: usually 5 to 15 minutes, and up to half an "
                    "hour if you wait for it to come away by itself rather than having the "
                    "injection that speeds it up. They check it is all out, and it is also when "
                    "any tear is stitched, so it can feel longer than it is.")
        return ("The second stage is the pushing: about an hour on average for a first baby, "
                "sometimes two, and often 10 or 20 minutes with a second or later one. The urge "
                "to push is hard to resist and that is normal - go with it, take the breaks "
                "between contractions, and expect the midwife to guide you to slow down at the "
                "end so you tear less.")
    if re.search(r"\bwaters?\b", line, re.I) and re.search(
            r"\bbreak|broke|broken|gone|went|went off\b", line, re.I):
        return ("Once your waters break, ring the midwife and go in to be checked - she will "
                "want to know the time, the colour and the smell. If labour has not started, "
                "most units offer to induce it within about 24 hours, because the risk of "
                "infection to you and the baby starts to rise after that. Do not use tampons or "
                "have sex once the waters have gone, and ring straight away if the water is "
                "green, brown or smelly, or if you feel unwell or the baby is not moving as "
                "usual.")
    if _SECOND_BIRTH.search(line):
        return ("A second or later labour is usually quicker than the first - often 5 to 12 hours "
                "from regular contractions to the birth, and some are much faster than that. "
                "Because it can move quickly, ring the midwife early rather than timing it at "
                "home, and go in when the contractions are strong and regular.")
    return ("A first labour usually takes 8 to 18 hours from the first regular contractions to the "
            "birth, and a second or later baby is usually quicker. Early labour at home can run "
            "much longer than that - a day or more of stop-start contractions is normal - so it "
            "is the pattern that matters: contractions getting stronger, longer and closer "
            "together, or your waters breaking, is the point to ring the midwife.")


def _preg_bag(memory, understood):
    """When the hospital bag gets packed, and what goes in it - the ask decides which."""
    line = _the_line(understood)
    when = ("Pack it by about 36 weeks - roughly a month before the due date - so it is ready if "
            "you go early. Two bags: yours with your maternity notes, a nightdress or two, big "
            "pads, toiletries, a phone charger and snacks; the baby's with nappies, vests, "
            "sleepsuits, a hat and a blanket. Keep it by the door, and add the notes last because "
            "you need them at appointments before then.")
    if re.search(r"\bwhat (?:should|do) i (?:pack|take|bring)\b|\bwhat to (?:pack|take|bring)\b|"
                 r"\bwhat goes in\b", line, re.I):
        return ("For you: maternity notes, a nightdress or two, big pads, toiletries, a phone "
                "charger and snacks. For the baby: nappies, vests, sleepsuits, a hat and a "
                "blanket. Pack it by about 36 weeks so it is ready if you go early, keep it by "
                "the door, and leave the notes on top because you need them at appointments "
                "before then.")
    return when



_PREG_SAID = re.compile(
    r"\b(?:pregnan\w*|expecting a baby|expecting our baby|with child|trimester|"
    r"\d\d? weeks (?:pregnant|gone))\b")
# "im not pregnant but i have bad headaches" is a headache question for someone who is not
# pregnant, and this row took it and told them about pre-eclampsia.
_PREG_DENIED = re.compile(
    r"\b(?:not|isn't|isnt|aren't|arent|no longer|stopped being|never)\s+(?:pregnan\w*)")


HEAD_PREGNANCY_REPLY = (
    "Paracetamol is the one to take for a headache in pregnancy, at the lowest dose that works "
    "and for the shortest time - not ibuprofen or aspirin unless a doctor or midwife has told "
    "you to. Water, food and sleep do a lot, and a skipped meal, dehydration and caffeine "
    "withdrawal are the usual causes. Mention headaches that keep coming back to your midwife, "
    "and go in the same day if a bad headache comes with blurred vision or flashing lights, pain "
    "under the ribs, swelling of the face or hands, or vomiting after 20 weeks: that combination "
    "is the one that has to be checked for pre-eclampsia.")


def _said_pregnant(understood):
    """Whether the line itself says the person is pregnant, used as an entry guard.

    The key holds the symptoms, so without this the row took every headache, every ibuprofen
    question and a dog's bad leg: "is ibuprofen bad for my kidneys" was answered about
    pre-eclampsia.
    """
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "text", "norm_text")).lower()
    if _PREG_DENIED.search(said):
        return False
    return bool(_PREG_SAID.search(said))



ENTRIES = [
    entry("preg-soft-cheese",
          (("brie", "camembert", "soft cheese", "soft cheeses", "blue cheese", "stilton",
            "gorgonzola", "roquefort", "chevre", "goats cheese", "mould ripened", "mold ripened",
            "mexicana", "mould ripened cheese", "mold ripened cheese", "baked camembert"),
           PREGNANT),
          "Skip it unless it is cooked until steaming hot: brie, camembert, soft blue cheeses and "
          "any mould-ripened cheese can carry listeria, and listeria can reach the baby. Baked "
          "camembert or brie in a hot dish is fine because the heat kills it. Hard cheese is a "
          "different story - cheddar, parmesan, and the tubs of cream cheese, cottage cheese and "
          "mozzarella are all fine, because they are made with pasteurised milk.",
          ask=("can i", "is it", "ok", "safe", "eat", "avoid", "should", "what about"),
          bias=2, avoid=NOT_FOOD),
    entry("preg-cheese-list",
          (("cheese", "cheeses", "dairy"),
           PREGNANT),
          "Hard cheese is all fine - cheddar, parmesan, gruyere - and so are feta, halloumi, "
          "mozzarella, cottage cheese and cream cheese, because they are made with pasteurised "
          "milk. The ones to cook until steaming or leave alone are the mould-ripened and blue "
          "ones: brie, camembert, stilton, gorgonzola, and any soft cheese with a rind. Skip "
          "anything labelled unpasteurised.",
          ask=("which", "what", "can i", "is it", "safe", "ok", "avoid", "eat", "list"),
          bias=2, avoid=NOT_FOOD),
    entry("preg-feta-halloumi",
          (("feta", "halloumi", "goats cheese", "goat cheese", "cottage cheese", "cream cheese",
            "mozzarella", "cheddar", "parmesan", "hard cheese", "paneer"),
           PREGNANT),
          "Fine, and this is where people cut out more than they need to: feta, halloumi, "
          "mozzarella, cottage cheese, cream cheese and all the hard cheeses - cheddar, parmesan, "
          "paneer - are made with pasteurised milk, and listeria is the only reason soft cheese "
          "is a worry. Check the label says pasteurised if it is a farm shop one; the "
          "supermarket tubs always are.",
          ask=("can i", "is it", "ok", "safe", "eat", "avoid", "have"),
          bias=2, avoid=NOT_FOOD),
    entry("preg-raw-milk",
          (("unpasteurised", "unpasteurized", "raw milk", "raw cheese", "farmhouse cheese",
            "goats milk", "sheeps milk", "raw dairy"),
           PREGNANT),
          "No: anything made with unpasteurised milk can carry listeria and campylobacter, so "
          "leave the raw-milk cheese and the milk straight from the farm. Pasteurised milk and "
          "cheese are fine, and most goat and sheep cheese sold in supermarkets is pasteurised - "
          "the label will say so.",
          ask=("can i", "is it", "ok", "safe", "eat", "avoid", "drink"),
          bias=2, avoid=NOT_FOOD),
    entry("preg-pate-liver",
          (("pate", "pates", "liver", "liver sausage", "liver pate", "chicken liver", "foie gras",
            "haggis", "liver and onions", "cod liver oil", "vitamin a"),
           PREGNANT),
          "No pate and no liver, and that includes vegetable pate: liver is so high in vitamin A "
          "that too much of it can harm the baby, and pate can carry listeria. The same goes for "
          "cod liver oil and any multivitamin with vitamin A in it - take folic acid and vitamin "
          "D instead, and ask the midwife about anything else.",
          ask=("can i", "is it", "ok", "safe", "eat", "avoid", "take"),
          bias=2, avoid=NOT_FOOD),
    entry("preg-raw-meat",
          (("rare", "raw meat", "undercooked", "pink", "medium rare", "steak", "salami",
            "chorizo", "prosciutto", "parma ham", "salami", "pepperoni", "cured meat",
            "cured meats", "sausage", "sausages", "hot dog", "hot dogs", "beef", "lamb", "pork",
            "chicken", "turkey", "mince", "burgers", "meat"),
           PREGNANT),
          "Cook meat right through: no rare steak, no pink lamb, and nothing raw or cured unless "
          "it is cooked into a hot dish. The worry is toxoplasmosis, which is in raw meat, and "
          "salami, chorizo, Parma ham and prosciutto are cured rather than cooked. Well-done "
          "steak, cooked chicken, ham from the deli counter and hot dogs heated until steaming "
          "are all fine.",
          ask=("can i", "is it", "ok", "safe", "eat", "avoid", "have"),
          bias=2, avoid=NOT_FOOD),
    entry("preg-raw-fish",
          (("sushi", "sashimi", "raw fish", "raw salmon", "smoked salmon", "gravadlax",
            "oysters", "oyster", "raw prawns", "shellfish", "mussels", "prawns", "fish",
            "salmon", "cod", "ceviche", "anchovies", "sardines", "mackerel", "sashimi"),
           PREGNANT),
          # "is it safe to eat prawns when pregnant" and "can i eat shellfish while pregnant" were
          # answered with the first sentence of this row, which was about oily fish: the verdict
          # they asked for was three sentences further down. The rule comes first now, and
          # shellfish is named in it.
          "Yes, with one rule. Raw is the part to skip: cooked prawns, mussels that have opened "
          "in the pan, tinned tuna and smoked salmon are all fine in the UK, and so is sushi made "
          "with cooked or frozen fish. What to leave alone is raw fish and raw shellfish - no "
          "oysters, no raw prawns - because of listeria and norovirus. Cooked fish is good for "
          "you and the baby too: salmon, mackerel and sardines are the ones to have, twice a week.",
          ask=("can i", "is it", "ok", "safe", "eat", "avoid", "have"),
          bias=2, avoid=NOT_FOOD),
    entry("preg-big-fish",
          (("swordfish", "shark", "marlin", "tuna", "tinned tuna", "tuna steak", "oily fish",
            "mercury"),
           PREGNANT),
          "Skip swordfish, shark and marlin completely, and keep tuna to two fresh steaks or four "
          "medium tins a week: those three are the fish with the most mercury, and tuna is the one "
          "people eat most of. Oily fish like salmon, mackerel and sardines is good for the baby's "
          "brain - two portions a week, and no more than one of them tuna.",
          ask=("can i", "is it", "ok", "safe", "eat", "avoid", "how much", "how many"),
          bias=2, avoid=NOT_FOOD),
    entry("preg-peanuts",
          (("peanuts", "peanut", "nuts", "nut", "almonds", "peanut butter", "tree nuts"),
           PREGNANT),
          "Peanuts and nuts are fine in pregnancy, and avoiding them does not prevent an allergy - "
          "the old advice to cut them out has been dropped. The exception is if you are allergic "
          "yourself, or the midwife or GP has told you to avoid them. Nuts are a good snack: a "
          "handful with an apple beats a biscuit at three in the afternoon.",
          ask=("can i", "is it", "ok", "safe", "eat", "avoid", "have"),
          bias=2, avoid=NOT_FOOD),
    entry("preg-herbal",
          (("herbal tea", "herbal teas", "green tea", "fennel", "liquorice", "raspberry leaf",
            "camomile", "chamomile", "peppermint tea"),
           PREGNANT),
          "Keep herbal teas to a couple of cups a day and don't treat any of them as medicine: "
          "liquorice is the one to avoid (it can raise blood pressure), and raspberry leaf is "
          "usually left until the last weeks and only with the midwife's agreement. Ordinary tea, "
          "decaf tea and water are the easy answers.",
          ask=("can i", "is it", "ok", "safe", "drink", "have"),
          bias=2, avoid=NOT_FOOD),
    entry("preg-listeria",
          (("listeria", "listeriosis", "food poisoning", "food hygiene", "toxoplasmosis"),
           PREGNANT),
          "Listeria is a bug that is rare but dangerous in pregnancy because it can cross to the "
          "baby, and it grows in food kept cold rather than in food left out - soft cheese, pate, "
          "smoked fish and cooked meats from a deli are the usual culprits. That is why the advice "
          "is to heat leftovers until steaming, wash the veg, and skip those foods. It usually "
          "shows as a mild flu-like illness, so mention any fever to the midwife.",
          ask=("is", "what", "can i", "should", "worried", "dangerous", "risk", "how"),
          bias=2, avoid=NOT_FOOD),
    entry("preg-what-can-i-eat",
          (("eat", "eating", "food", "foods", "diet", "avoid", "anything", "menu"),
           PREGNANT),
          LIST,
          # The same question, said the other way round: the ask list had "what can i eat" and
          # "what should i avoid", so "what should i eat when pregnant" and "what not to eat when
          # pregnant" were shrugs while "what can i eat when im pregnant" was answered. A line
          # with a pregnancy word and a food word in it is this question however it is put.
          ask=("what can i eat", "what can't i eat", "what cant i eat", "what can i not eat",
               "what should i avoid", "what to avoid", "what foods", "which foods",
               "what shouldn't i eat", "what is off limits", "can i eat", "avoid",
               "anything i shouldn't",
               "what should i eat", "what should i be eating", "what to eat", "what do i eat",
               "what not to eat", "what i shouldn't eat", "what i shouldnt eat",
               "shouldn't eat", "shouldnt eat", "shouldn't i eat", "shouldnt i eat",
               "not eat", "not to eat", "can't i eat", "cant i eat", "avoid eating",
               "what's safe to eat", "whats safe to eat", "safe to eat"),
          avoid=NOT_FOOD),
# Three everyday things that are not food and were answered by whoever owned the word: a bath
# question got the newborn's bath ("5 to 8 cm of water"), a flight question got the fares card
# ("book six to eight weeks ahead"), and hair dye got a hedge. Each is a real question with a
# real answer, and none of them is a symptom, so they are not in the food table.
    entry("preg-hot-bath",
          (("hot bath", "bath", "baths", "bathwater", "hot tub", "jacuzzi", "sauna", "steam room",
            "spa", "warm bath"),
           PREGNANT),
          "Warm is fine, hot is the part to avoid: keep the water comfortable rather than "
          "steaming, and get out if you feel light-headed. Hot tubs, saunas and steam rooms are "
          "best skipped for the first 12 weeks, because raising your core temperature early on "
          "has been linked to problems with the baby's spine. A warm bath, a shower and a swim "
          "are all fine right through.",
          ask=("safe", "ok", "okay", "fine", "allowed", "can i", "should i", "is it", "is a",
               "how hot", "how warm"),
          bias=2,
          avoid=NOT_FOOD + ("baby", "babies", "newborn", "toddler", "child", "clean the",
                            "cleaning", "limescale", "mould", "drain")),
    entry("preg-flying",
          (("fly", "flying", "flight", "flights", "plane", "airplane", "aeroplane", "air travel",
            "long haul", "long-haul", "holiday abroad",
            # "can i still travel while pregnant" and "can you travel when pregnant" are the
            # same question as "can i fly when pregnant", and the row had only the flights in
            # its key, so both were a search hedge. The pregnancy word is the other half.
            "travel", "travelling", "traveling", "a trip", "trip abroad", "go abroad",
            "going abroad", "flying abroad",
            # the holiday is the same question, and a pregnancy word in the line is what keeps
            # "how much holiday pay am i owed" out of this row
            "holiday", "holidays", "on holiday", "vacation", "a break abroad"),
           PREGNANT),
          "Flying is usually fine: most airlines take you up to 36 weeks for one baby, and 32 "
          "weeks for twins, and some ask for a letter from the midwife from 28 weeks, so check "
          "your airline before you book. Drink water, get up and walk every hour or so and wear "
          "compression socks on a long flight. Ask the midwife first if you have had bleeding, "
          "high blood pressure, pre-eclampsia or twins.",
          ask=("safe", "ok", "okay", "fine", "allowed", "can i", "should i", "is it", "when can i",
               "how late", "how far", "abroad",
               # "can you travel when pregnant" asks the same thing in the second person, and
               # the ask words were all first person, so it fell through to the hedge
               "can you", "can we", "could i", "is it ok to", "still ok", "still fine"),
          bias=2,
          # NOT_FOOD lists flying because a food row must stand down for it; this row is the
          # one that answers those lines, so the word comes back out here
          avoid=tuple(w for w in NOT_FOOD if w not in ("fly", "flying", "flight", "travel")) + (
              "cheap", "cheaper", "cheapest", "book a flight", "price", "fare", "delayed",
              "cancelled", "luggage", "legroom", "jet lag")),
    entry("preg-hair-dye",
          (("hair dye", "dye my hair", "dye your hair", "dyeing my hair", "colour my hair",
            "color my hair", "hair colour", "hair color", "highlights", "bleach my hair",
            "hair treatment", "salon"),
           PREGNANT + ("breastfeeding", "breastfeed", "breast feeding", "nursing")),
          _preg_hair_dye,
          ask=("safe", "ok", "okay", "fine", "allowed", "can i", "should i", "is it", "when can i",
               "still"),
          bias=2,
          # breastfeeding is in NOT_FOOD because a food row must stand down for it, and this row
          # is the one that answers the dye question for it: "can i bleach my hair while
          # breastfeeding" was told to keep caffeine to 200mg a day
          avoid=tuple(w for w in NOT_FOOD if w not in ("breastfeeding", "breastfeed", "nursing")) + (
              "cut", "cuts", "trim", "hairdresser", "fringe", "grey", "thinning", "hair loss",
              "hair falling", "shampoo", "conditioner", "dandruff")),

    # Moving about, which is the one part of pregnancy the food rows kept answering: "is it safe
    # to run while pregnant" got "That food is not on the list", because "run" was not in
    # NOT_FOOD, and "can i exercise while pregnant", "can i lift weights when pregnant" and "is
    # it safe to swim while pregnant" were all a search punt. One row answers every movement
    # word, since the advice is the same for all of them.
    entry("preg-exercise",
          (PREGNANT_MOVEMENT, PREGNANT),
          "Keep doing what you already do, at a pace where you can still hold a conversation: "
          "150 minutes a week of walking, swimming, yoga, pilates or light weights is what the "
          "guidance recommends, and it is good for you and the baby. Leave out contact sports "
          "and anything with a fall risk such as riding, skiing or cycling on the road, and in a "
          "class do not lie flat on your back after 16 weeks. Stop and ring your midwife if you "
          "bleed, leak fluid, feel dizzy or very breathless, and ask her first if you have a "
          "condition or were not active before.",
          ask=("safe", "ok", "okay", "fine", "allowed", "can i", "should i", "is it", "still",
               "while", "when", "how much", "how often", "how long", "continue", "keep"),
          bias=2,
          # inducing labour, gaining weight and a body part that hurts are other questions
          avoid=("bring on labour", "bring on labor", "start labour", "start labor", "induce",
                 "kick start", "weight gain", "how much weight", "put on", "gained",
                 "back pain", "backache", "pelvic", "sciatica", "cramp", "sick", "nausea",
                 "bleeding", "bleed", "discharge", "waters", "contractions")),

    # A headache or a migraine in pregnancy is its own question, and nothing answered it: "im
    # pregnant and have a migraine" was a congratulations and "headache while pregnant" was
    # "Lovely to hear. Enjoy it!". The tablets are the part that matters, since ibuprofen is not
    # for pregnancy, so the row is about the pain and the two red flags.
    entry("preg-headache",
          # The key holds the head and nothing else. "paracetamol" and "painkiller" were here,
          # and they took a back-pain question ("the midwife said paracetamol is fine but it
          # does nothing") and answered it about a headache, which lost the good follow-up that
          # was there before. A question about the tablet alone has its own card.
          (("headache", "headaches", "migraine", "migraines", "head ache", "head aches",
            "my head hurts", "my head is banging", "head is pounding", "head pounding",
            "splitting headache", "bad head"),
           ("pregnant", "pregnancy", "expecting a baby", "expecting our baby", "trimester",
            "weeks pregnant", "weeks gone", "safe", "ok", "okay", "can i", "could i", "is it",
            "while pregnant", "in pregnancy", "take")),
          HEAD_PREGNANCY_REPLY,
          bias=2,
          guard=_said_pregnant,
          # a body question with a different answer, a scan, an appointment or a food is not this
          avoid=("folic acid", "vitamin", "supplement", "scan", "scans", "midwife appointment",
                 "bp", "blood pressure", "glucose test", "sugar test", "kick", "kicks",
                 "movement", "movements", "bleeding", "bleed", "spotting", "waters",
                 "contractions", "swollen feet", "swollen ankles", "sickness", "nausea",
                 "vomiting", "heartburn", "constipation", "piles", "stretch marks", "sleep",
                 "travel", "flight", "flying", "food", "eat", "eating", "diet", "sex",
                 "exercise", "gym", "swim", "nursery", "pram", "cot", "nappy", "nappies")),

    # "Is it safe to eat X in pregnancy" for the foods the list does not name: one row, keyed on
    # the shape of the question rather than on any one food, with a table of the ones people ask
    # about most. The named rows above score higher (their food word is beside "safe" and
    # "pregnant" and they carry bias=2), so brie and liver and tuna keep their own answers.
    entry("preg-any-food",
          (tuple(name for names, _ in PREG_WORRY_FOODS for name in names) +
           ("safe", "safely", "ok", "okay", "fine", "allowed", "allow", "bad", "harm", "harmful",
            "danger", "dangerous", "risky", "risk",
            # A drink with no row of its own is still "not on the list of things to avoid", which
            # is the true answer for juice and squash. Without the drink in this key the food row
            # has nothing to match and the line is read as alcohol instead - "can i drink juice
            # while pregnant" was given the no-alcohol paragraph.
            "drink", "drinks", "drinking", "juice", "squash", "squashes", "smoothie"),
           PREGNANT),
          _preg_food,
          ask=("safe", "ok", "okay", "fine", "allowed", "allow", "bad", "harm", "harmful",
               "danger", "dangerous", "risky", "risk", "can i", "should i", "is it", "are they",
               "is", "are"),
          bias=1,
          # a body question, a symptom, a medicine or an appointment is not a food question, and
          # neither is a dye, a bath or a scan: each has its own answer elsewhere
          avoid=NOT_FOOD + PREGNANT_MOVEMENT + (
              "bath", "baths", "sauna", "jacuzzi", "hot tub", "steam room", "hair dye", "dye",
              "dying my hair", "highlights", "hair colour", "hair color", "nails", "massage",
              "tattoo", "tattoos", "fake tan", "sunbed", "sunbathing", "cat litter", "litter",
              "cleaning products", "bleach", "paint", "x-ray", "xray", "dentist", "dental",
              # a bottle of something is not a food, and the food list answered the question
              # anyway: "is white spirit safe to use when pregnant" was told "that food is not on
              # the list of things to avoid, so it is fine", which is the opposite of the truth.
              # The chemicals people ask about by name, and the words a can or a spray says.
              "white spirit", "turps", "turpentine", "paint thinner", "thinner", "varnish",
              "wood stain", "primer", "gloss paint", "spray paint", "aerosol", "adhesive",
              "wood glue", "superglue", "solvent", "solvents", "fumes", "fumigate",
              "weedkiller", "weed killer", "glyphosate", "pesticide", "insecticide",
              "antifreeze", "oven cleaner", "drain cleaner", "descaler", "disinfectant",
              "ammonia", "mould spray", "ant powder", "slug pellets", "rat poison", "rodenticide",
              "flea treatment", "flea bomb", "creosote", "wood preserver", "decking oil",
              "paint stripper", "nitromors", "caustic", "swimming pool chemicals",
              # a jab is not a food: "is the covid jab ok while pregnant" was told that the thing
              # it named is not on the list of foods to avoid, which is the wrong question
              "jab", "jabs", "jabbed", "booster jab", "booster", "vaccination", "immunisation",
              "immunization", "covid jab", "flu jab", "covid vaccine", "flu vaccine",
              # the general list is its own row: "what can i eat when pregnant" and "what foods
              # should i avoid" are questions about the whole list, not about one food
              "what can i eat", "what cant i eat", "what can't i eat", "what can i not eat",
              "what should i avoid", "what to avoid", "what foods", "which foods", "diet",
              "menu", "foods to avoid", "eat when pregnant", "eat while pregnant") +
              DRINKS_WITH_THEIR_OWN_ANSWER +
              # milk has its own row now, and so does the hot drink made with it
              ("milk", "a pint of milk", "dairy", "milkshake", "milkshakes", "hot chocolate")),

    # Milk was answered with the alcohol paragraph: the only drink rows were caffeine and
    # alcohol, the bare verb "drink" is in the alcohol row's key, and no row said milk.
    # Pasteurised milk is fine in pregnancy and the calcium is worth having, so the honest
    # answer is a yes with the one exception named.
    entry("preg-milk",
          (("milk", "a pint of milk", "dairy", "milkshake", "milkshakes", "hot chocolate"),
           ("pregnant", "pregnancy", "expecting", "drink", "drinking", "is it", "safe", "ok",
            "okay", "fine", "can i", "should i", "much")),
          "Pasteurised milk is fine, and worth drinking: about three servings of dairy a day "
          "covers the calcium and iodine a baby needs. The one to skip is unpasteurised milk and "
          "anything made with it - some farm-shop milk, and raw-milk cheese - because of "
          "listeria. If milk turns your stomach early on, yoghurt, cheese and a fortified plant "
          "milk cover the same ground.",
          # a baby in the line is a feeding question, and cheese has its own answer
          avoid=("breastfeeding", "nursing", "formula", "weaning", "my baby", "a baby",
                 "the baby", "baby have", "baby need", "how much milk", "ounces", "oz",
                 "expressing", "colic", "reflux", "allergy", "allergic", "lactose",
                 "cows milk protein", "cheese", "brie", "camembert", "feta", "stilton",
                 "yoghurt", "yogurt", "ice cream", "goat", "soya", "oat milk", "almond milk",
                 # a milk that is going in the freezer is the freezer table's question, and its
                 # answer is the one with the inch of room and the shake: "can i freeze milk" was
                 # reaching this row on "can i" and "milk" with no pregnancy in the line at all
                 "freeze", "freezes", "freezing", "frozen", "freezer", "thaw", "thawed",
                 "defrost", "defrosted", "use by", "out of date", "gone off", "goes off",
                 "how long does milk", "how long can i keep", "storage"),
          # The key's second group is nearly all ways of asking ("can i", "should i", "is it",
          # "ok", "fine"), so with no guard this row answered "what milk should i use" and
          # "which milk should i buy" with the calcium an unborn baby needs. The same reading
          # the other pregnancy rows use: the line has to say the pregnancy.
          guard=_said_pregnant),

    # The doubt, before there is a fact: "am i pregnant", "could i be pregnant".
    entry("preg-am-i",
          (("pregnant", "pregnancy"), AM_I + TEST_WORDS + WHEN),
          TEST_REPLY, bias=2,
          # NOT_FOOD lists "test" because a food entry must stand down for a test line. This
          # entry is the one that answers those lines - its key holds TEST_WORDS - so the word
          # comes out of its avoid list here: with it in, "can i take a pregnancy test" scored
          # nothing at all.
          avoid=tuple(w for w in NOT_FOOD if w not in ("test", "tests")) + NOT_A_TEST +
                PREGNANT_ALREADY + FERTILITY +
                ("how many weeks", "weeks pregnant", "weeks am i", "due date", "trimester",
                 "maternity", "birth control", "contraception", "condom", "morning after",
                 # a result already in the line is the result cards' question: "i think im
                 # pregnant but the test was negative" is the negative one's line.
                 "test was negative", "test is negative", "test was positive",
                 "test is positive", "tests were negative", "tests are negative")),
    # Two lines said on their own: "what does two lines mean", "i have two lines". The result is
    # in the line and nothing else names a test, so the row above cannot reach it - its second
    # half wants a test word. Kept as its own row rather than put back into TEST_WORDS, because
    # there the phrase is in both halves of one key and a hyphen supplies both: "a two-line bio
    # for a badge" was answered with the booking-in appointment.
    entry("preg-two-lines",
          (("two lines", "both lines"), ("mean", "means", "meant", "pregnant", "pregnancy",
                                         "test", "tests", "positive", "got", "have", "see",
                                         "showing", "shows")),
          POSITIVE_REPLY,
          avoid=NOT_A_TEST + ("negative", "not pregnant")),
    # The result, in its two directions: "i did a test and it was positive", "the test was
    # negative". One entry cannot answer both - the positive line wants the booking-in and the
    # negative one wants to test again - so the word that says which it is decides the entry.
    entry("preg-test-positive",
          (("positive", "two lines", "both lines", "faint line", "faint", "it says",
            "says positive"),
           TEST_WORDS),
          POSITIVE_REPLY,
          ask=("what", "should", "do i", "is", "does", "test", "result", "now", "next", "so"),
          # a result words line is the more specific one: "two lines on a pregnancy test" is
          # the positive card, not the timing one.
          bias=2, avoid=NOT_A_TEST + ("negative", "not pregnant")),
    entry("preg-test-negative",
          (("negative", "not pregnant", "one line", "no line", "no lines", "nothing there"),
           TEST_WORDS),
          NEGATIVE_REPLY,
          ask=("what", "should", "do i", "is", "does", "test", "result", "now", "next", "so",
               "can i", "how"),
          bias=2, avoid=NOT_A_TEST + ("positive",)),
    # The period that has not come, which is how most people say it.
    entry("preg-late-period",
          (WHEN, ("late", "missed", "days", "weeks", "hasnt", "not come", "where", "why",
                  "when", "worry", "normal", "pregnant", "pregnancy", "test")),
          LATE_REPLY,
          ask=("my period", "period", "late", "missed", "why", "when", "should", "is it",
               "how long", "what"),
          guard=_a_late_that_is_not_a_period,
          # "missed" and "late" each sit in both halves of this entry's key, so one word can
          # carry the pair: "i missed my driving test" was answered with the late-period card.
          # The other lives the word names are fenced rather than the word itself, because "my
          # period is late and the test was negative" is a real line this entry should still
          # have a neighbour for.
          avoid=("period pain", "period pains", "cramps", "heavy period", "period pads",
                 "menopause", "hot flushes", "contraception", "condom", "morning after",
                 "early", "days early", "week early", "weeks early", "sooner", "shorter",
                 "driving test", "theory test", "theory", "mot", "exam", "exams",
                 "missed my test", "missed the test", "missed a test", "interview",
                 "deadline", "payment", "train", "bus", "flight",
                 # a pregnancy with a due date is a pregnancy, not a late period
                 "due date", "weeks pregnant", "weeks am i", "trimester", "maternity",
                 # "due" is a date for all sorts of other things: "when am i due back at work"
                 # was the late-period card, and the card is about waiting for a period.
                 "due back", "due to be", "back at work", "back to work", "refund",
                 "tax return", "parcel", "library", "renewal", "invoice",
                 # the cycle in general, which has its own answer below
                 "normal", "how long", "how often", "how many days", "days between",
                 "lasts", "started", "when do periods", "first period", "heavy", "light",
                 # asking how conception works, which is not a late period
                 # ... and a wage is not a period either: "my boss wants me to work late every
                 # week, do i have to be paid for it" met "late" and "weeks" and was given
                 # "plenty shifts a period by a few days". A line about pay for the hours worked
                 # names no period of its own.
                 "boss", "manager", "rota", "my job", "work late", "working late", "work every",
                 "overtime", "be paid for", "paid for it", "get paid", "wages", "salary",
                 "hourly", "hours i work", "for the hours"
                 ) + FERTILITY),
    # What a cycle normally looks like, which the late entry used to answer with "test again in
    # three days": "what is a normal period", "how many days between periods".
    entry("preg-cycle-normal",
          (("period", "periods", "cycle", "cycles"),
           CYCLE_SHAPE + ("how often", "typical", "average", "length", "between")),
          CYCLE_REPLY, bias=1,
          guard=_a_late_that_is_not_a_period,
          avoid=NOT_A_TEST + NOT_FOOD +
                ("heavy", "light", "late", "missed", "pregnant", "pregnancy", "test",
                 "tests", "period pain", "cramps",
                 # a fish tank has a cycle too, and it is the one with weeks in it: "my new
                 # tank is cycling how long" was answered with "the usual cycle is 21 to 35
                 # days from the first day of one period". The tank row knows the four to six.
                 "tank", "tanks", "aquarium", "fish tank", "nitrogen cycle", "ammonia",
                 "nitrite", "nitrate",
                 # "period" is a word with two lives: "how long is my probation period" was
                 # answered with the 21-to-35-day cycle. Probation, a contract, a trial shift
                 # and a court sentence are the other life, and none of them is a cycle.
                 "probation", "probationary", "on probation", "trial period", "trial shift",
                 "contract", "contracts", "employment", "employer", "job offer", "new job",
                 "at work", "sentence", "court", "parole",
                 # a machine has a cycle too, and "how long does a dishwasher cycle take"
                 # was answered with "21 to 35 days from the first day of one period"
                 "dishwasher", "dishwashers", "washing machine", "washer", "washer dryer",
                 "tumble dryer", "dryer", "spin cycle", "wash cycle",
                 # a bike has a cycle too: "i want to learn to cycle" is the bike lesson, and
                 # "how long does it take" after it was the 21-to-35-day period answer because
                 # the carried word was "cycle". The bike words stand this row down when the
                 # conversation is about riding one, and a period line names none of them.
                 "bike", "bikes", "bicycle", "bicycles", "cycle to work",
                 "cycling to work", "learn to cycle", "learning to cycle",
                 "pedal", "pedals", "pedalling", "saddle", "ride a bike", "riding a bike",
                 "learn to ride",
                 # the wash itself is the other life "cycle" has here: "how long is a wash
                 # cycle" was answering "the usual cycle is 21 to 35 days". The wash-length
                 # row knows what a machine programme is, and a line naming the wash is not a
                 # body. "program" and "eco" are the dial's words too, so both are named.
                 "wash", "washing", "washed", "laundry", "programme", "program", "quick wash",
                 "eco",
                 # and the bike ride's own names: "how long is a cycle ride" is the ride, and
                 # the sport row answers it. No "cycling" here: it is a loose form of "cycle",
                 # so it turned down every line that says cycle at all - "how long is a cycle"
                 # included.
                 "cycle ride", "cycle lane", "cycle path", "cycle route")),

    # When PMS turns up, which the cycle row answered with the length of a cycle: "how many days
    # before my period do i get pms" is a when-question, and the window is the answer.
    entry("preg-pms-days",
          (("pms", "pmt", "premenstrual", "pre menstrual", "pre-menstrual"),
           ("how many days", "how long", "when", "before", "last", "lasts", "start", "starts",
            "days", "week", "weeks", "early")),
          "Premenstrual symptoms usually start a week or two before a period and are at their "
          "worst in the five days before it, then ease within a day or two of bleeding starting. "
          "Track them for two or three cycles - the pattern is what tells you it is the cycle and "
          "not the week. If it is bad enough to wreck two weeks in four, or the mood change is "
          "severe, that is worth the GP: PMDD is real and treatable.",
          bias=1,
          avoid=NOT_FOOD + NOT_A_TEST + ("pregnant", "pregnancy", "test", "tests", "missed",
                                         "late", "period pain", "cramps")),

    # The other direction, which the late entry used to take: "my period came two weeks early".
    entry("preg-early-period",
          (("period", "periods", "cycle"), ("early", "days early", "week early", "weeks early",
                                            "sooner", "shorter", "before i expected",
                                            "earlier than usual", "two weeks early")),
          EARLY_REPLY, bias=1,
          avoid=NOT_FOOD + NOT_A_TEST + ("late", "missed", "period pain", "cramps", "heavy")),

    # The date itself, which nobody had an answer for: "when is my due date" and "how many weeks
    # pregnant am i" were both a hedge ("That's beyond what I know"). Neither is a fact about the
    # world that a card can hold - the date is theirs - so the answer is how it is worked out and
    # where it is written down. "Due" on its own is not in the key: rent, a bill and a library
    # book are all due on a date, and the phrases here are the ones that only a pregnancy says.
    entry("preg-due-date",
          (("due date", "due date is", "when am i due", "when is my due", "whens my due",
            "when's my due", "baby due", "when is the baby due", "how far along",
            "weeks pregnant am i", "weeks am i", "how many weeks pregnant",
            "how pregnant am i", "how many weeks am i", "pregnancy weeks",
            "when will the baby", "when will my baby", "when is the baby born",
            "how long left of my pregnancy", "how many weeks left of my pregnancy",
            "weeks pregnant", "how many wks am i", "how many weeks along",
            "how many weeks into", "how many weeks gone", "what week am i",
            "which week am i",
            "how many weeks is a pregnancy", "how long is a pregnancy",
            "when are you due", "when is she due", "when is he due", "baby is due",
            "last period", "lmp", "first day of my last period", "period started",
            "my period started", "how many months"),
           ("when", "what", "how many", "how far", "date", "weeks", "days", "am i",
            "due", "work out", "worked out", "calculate", "count", "left", "born",
            "is it", "will it", "how long")),
          # Bias 4, not 3: the line that gives a day reaches the cycle card as well, and the row
          # that counts from that day is the more specific answer - "my last period was 3 may" was
          # answered with the usual cycle. Measured over 24 period lines, this and the shape below
          # change that one line and nothing else: "my period is late", "when is my next period
          # due", "how long is my period" and "can i fly at 30 weeks pregnant" keep their rows.
          _preg_due_date, bias=4,
          ask=("when", "whens", "how many", "how far", "how long", "which date", "what date",
               "due date", "weeks", "week", "months", "calculate", "worked out", "left",
               "am i", "is", "are", "will",
               # The bot asks for the first day of the last period, so the answer to that
               # question names the day and asks nothing: "3 may was the first day of my last
               # period" reached the cycle card, and "my last period started on 3 may" the
               # puberty one, because the ask words are the gate and a line that only gives
               # the day has none of them. The guard still holds it to a day and to a
               # pregnancy, so "my last period was late" is not a date to count from.
               "last period", "first day", "period started", "lmp"),
          shape=(_gives_a_month,),
          guard=_asks_when_due,
          avoid=NOT_FOOD + NOT_A_TEST + (
              "am i pregnant", "could i be pregnant", "test was", "test is", "two lines",
              "one line", "negative", "positive", "missed period", "late period",
              "period late", "contraction", "contractions", "induction", "c section",
              "c-section", "epidural", "maternity pay", "maternity leave", "paternity",
              "birth certificate", "names", "name", "nursery", "cot",
              "rent", "bill", "bills", "payment", "pay", "invoice", "loan",
              "library", "essay", "assignment", "coursework", "homework",
              "deadline", "tax", "mot", "insurance", "subscription")),
          # A line that gives the day or the week gets the date worked out; a line that gives
          # neither gets the card, which says how the count goes and where the date is written
          # down. The card is the fallback text in `_preg_due_date`.

    # The birth itself: both questions the last month brings, and both were the shrug.
    entry("preg-labour-length",
          (("labour", "labor", "birth", "give birth", "in labour", "contractions", "waters",
            # the stages are asked about by name, and without them the row was never reached
            "first stage", "second stage", "third stage", "pushing", "pushing stage", "placenta",
            "stage of labour"),
           ("how long", "how many hours", "hours", "long", "longer", "shorter", "quicker",
            "faster", "slow", "take", "last", "how soon", "longest", "too long", "stalled",
            "stalling", "go on")),
          _preg_labour_length, bias=1,
          guard=_asks_a_birth_time, avoid=_NOT_THE_BIRTH),
    entry("preg-hospital-bag",
          (("hospital bag", "hospital bags", "maternity bag", "bag for hospital",
            "bag for the hospital", "bags for hospital", "hospital"),
           ("pack", "packed", "packing", "when", "what to take", "what to bring")),
          _preg_bag, bias=2,
          guard=_asks_about_the_bag,
          avoid=("bin", "bin bag", "tea", "teabag", "teabags", "shopping", "dog", "school",
                 "rucksack", "backpack", "handbag", "luggage", "suitcase", "sleeping bag")),
]

# --- the words of having a baby ----------------------------------------------------------------
# A person expecting a baby meets a new vocabulary in the appointments and the leaflets: a
# membrane sweep, a ventouse, an epidural, a nuchal scan. On main `b5a628e1` every one of these
# questions got nothing, and some got a card about something else, because another row owned the
# noun: "what is a contraction" was answered with advice about apostrophes, "what is a show in
# pregnancy" with a television series, "what is a forceps delivery" with the physics of force,
# "what is a mucus plug" with phlegm, "what is a nuchal scan" with X-rays, "what is a tongue tie"
# with mouth thrush.
#
# So this is one glossary keyed on the term, in the shape the cook-words and music-words tables
# use: the term and a definition shape are both required, and the reply is the plain meaning in
# the first sentence plus the one thing it is worth knowing. A phrase scores for all its words,
# which is what lets "nuchal scan" and "mucus plug" win the line from the row that only has
# "scan" or "mucus".
_BIRTH_WORDS = (
    (("c section", "c-section", "caesarean", "caesarian", "cesarean", "cesarian",
      "caesarean section", "cesarean section"),
     "A caesarean is the baby delivered through a cut in the tummy and womb, usually because "
     "labour is not progressing, the baby is breech or either of you is unwell. It is a major "
     "operation: about 45 minutes, a spinal so you are awake, and roughly four to six weeks of "
     "careful lifting afterwards. An emergency one is done for a reason found in labour, not "
     "because anything went wrong on your part."),
    (("doula", "doulas"),
     "A doula is a person who supports you through pregnancy, birth and the first weeks - "
     "practical help and someone who stays with you - but she is not a midwife and does no "
     "clinical care. Doulas are hired privately, usually GBP 300 to 800, and there are free "
     "volunteer doulas in many areas; ask what she does at a hospital birth, as some trusts "
     "limit how many people are in the room."),
    (("midwife", "midwives"),
     "A midwife is the trained professional who looks after a straightforward pregnancy, birth "
     "and the first weeks, and she is who you see at the antenatal appointments. She is a nurse "
     "or a direct-entry midwife with a degree, and she can order scans and blood tests, deliver "
     "the baby and stitch a tear. A doctor takes over only if something needs one."),
    (("epidural", "epidurals"),
     "An epidural is pain relief given through a fine tube in the back, numbing from the waist "
     "down while you stay awake. It takes about 20 minutes to set up and 15 to 20 to work, and "
     "it can make your legs heavy and slow labour, so it is usually offered once labour is "
     "established. You can still push with one; ask early if you want one, because it needs an "
     "anaesthetist."),
    (("birth plan", "birth plans"),
     "A birth plan is a page saying what you would prefer - who is with you, how you want pain "
     "relief, water, feeding, and what to do if things change - written so a midwife can read it "
     "in a minute. Keep it to one side of A4 and put your first two wishes at the top: the plan "
     "that helps is a short list of preferences, not a script, because birth often goes its own "
     "way."),
    (("induced", "induction", "inductions", "being induced", "induced labour"),
     "Induction is starting labour with medicine or a balloon instead of waiting for it to start "
     "itself, usually offered if you go past about 41 weeks or there is a reason the baby is "
     "better out. It is a prostaglandin tablet or gel first, then a drip if needed, and it can "
     "take two or three days from the first dose to the baby. You can ask what the reason is and "
     "what happens if you wait."),
    (("water birth", "water births", "birthing pool", "birth pool"),
     "A water birth is labouring, and sometimes delivering, in a deep pool of warm water, which "
     "takes the weight off and often eases the pain of contractions. Many birth centres and some "
     "labour wards have pools; ask early, as there may be one and it may be taken. You can get "
     "out at any point, and being in water is not offered if there are complications."),
    (("colostrum", "colostrum harvesting"),
     "Colostrum is the first milk: thick, yellow and made in small amounts in the last weeks and "
     "the first days, and it is all a newborn needs - a teaspoon at a time, full of antibodies. "
     "It acts as a laxative that clears the meconium, which is why the first dirty nappies come. "
     "Hand expressing a little into a syringe before the birth is worth asking about if your "
     "baby may need extra."),
    (("membrane sweep", "stretch and sweep", "sweep", "sweeps"),
     # "sweep" is a chimney sweep and a clean sweep too, so it needs a birth in the line like the
     # other ambiguous words in _AMBIGUOUS below
     "A membrane sweep is a midwife's gloved finger passing over the cervix to separate the "
     "membranes, which releases hormones and can start labour - offered from about 40 weeks if "
     "you are keen to avoid induction. It takes a minute, feels like a smear test and a period "
     "cramp, and works for roughly one in eight. You can say no and ask again in a week."),
    (("ventouse", "ventouse delivery", "vacuum delivery", "vacuum extraction"),
     "A ventouse is a soft cup on the baby's head that a doctor pulls with, to help in the last "
     "stage when pushing is not moving the baby or either of you is tiring. It leaves a bruise "
     "and a cone-shaped head that settles in a few days. Forceps do the same job with metal "
     "tongs; the doctor will explain which they want and why."),
    (("episiotomy", "episiotomies"),
     "An episiotomy is a small cut made at the bottom of the vagina during birth to make room, "
     "done with local anaesthetic when the baby needs to come quickly or the tissue is about to "
     "tear badly. It is stitched and heals in two to three weeks, and it is not routine - a tear "
     "that happens on its own is often smaller and heals better, so not every birth needs one."),
    (("nicu", "scbu", "special care baby unit", "neonatal unit"),
     "NICU is the neonatal intensive care unit, and SCBU the special care baby unit - where a "
     "baby goes if they are early, small or need help breathing or feeding. You can visit almost "
     "all the time, ask to do the nappy changes and feeds, and ask the nurse to explain every "
     "tube and number: babies on these units are usually there for warmth, feeding and time."),
    (("labour", "in labour", "going into labour"),
     "Labour is the womb contracting to open the cervix and push the baby out: for a first baby "
     "it usually takes 8 to 18 hours from regular contractions, and it comes in three stages - "
     "the cervix opening to 10 cm, the pushing, and the placenta. Call the midwife when "
     "contractions are regular, getting longer and stronger, about every five minutes."),
    (("placenta", "the afterbirth", "afterbirth"),
     "The placenta is the organ on the womb wall that feeds the baby through the cord, and it "
     "comes out as the third stage of labour, usually within 15 to 30 minutes of the birth. You "
     "can have an injection to speed that up or wait for it to happen on its own. It is checked "
     "whole afterwards, which is the one reason to look at it if you want to."),
    (("birth centre", "birth centres", "midwife led unit", "midwifery led unit"),
     "A birth centre is a midwife-led unit for a straightforward birth - a room with a pool, "
     "your own space, no doctors on site and usually a shorter stay, so it suits a pregnancy "
     "with no complications. If something needs a doctor you are transferred to the labour ward, "
     "which is usually minutes away. Ask for a look round at about 30 weeks."),
    (("home birth", "home births", "birth at home"),
     "A home birth means two midwives come to you, with gas and air and a pool if you have one, "
     "and you are transferred to hospital by ambulance if it is needed. It is offered for a "
     "straightforward second or later pregnancy, and it is your choice to ask for it - about 2 "
     "in 100 births in the UK happen at home."),
    (("perineal tear", "tear", "tears", "second degree tear", "third degree tear", "a tear"),
     "A tear is the skin at the bottom of the vagina stretching and splitting as the baby comes: "
     "most are small, most need a few stitches with local anaesthetic, and they heal in two to "
     "three weeks. A third or fourth degree tear reaches the muscle and the back passage and is "
     "repaired in theatre. Tell your midwife about the pain rather than sitting on it."),
    (("lochia", "postnatal bleeding", "bleeding after birth"),
     "Lochia is the bleeding after birth: heavy red blood for three to five days, then browner "
     "and lighter for up to six weeks. Use pads rather than tampons, and get help the same day "
     "if you soak a pad in an hour, pass clots bigger than a 50p coin, or the blood smells bad "
     "or you feel feverish - that is a sign to have checked."),
    (("heel prick test", "newborn blood spot", "blood spot test", "heel prick"),
     "The heel prick test is the newborn blood spot test, done at five days old: a few drops of "
     "blood from the heel onto a card, checked for nine rare conditions including cystic "
     "fibrosis, sickle cell and an underactive thyroid. It takes a minute and the baby cries "
     "briefly. It is offered to every baby and you can ask what each result means."),
    (("mucus plug", "bloody show", "show in pregnancy", "a show in pregnancy", "show"),
     "The mucus plug is the plug of mucus that seals the cervix, and it comes away as a thick "
     "jelly, sometimes streaked with blood - the \'show\'. It can be days or a fortnight before "
     "labour and means nothing on its own; call the midwife if the blood is more than a streak "
     "or comes with regular contractions."),
    (("nuchal scan", "nuchal translucency", "dating scan", "20 week scan", "anomaly scan"),
     "A nuchal scan is the 12-week scan: it measures the fluid at the back of the baby's neck "
     "and, with a blood test, gives a risk figure for Down's, Edwards' and Patau's syndromes - "
     "a screening test, not a diagnosis. The 20-week scan checks how the baby is growing and "
     "developing. Both are offered, and you can decline or ask for time to think."),
    (("skin to skin", "skin to skin contact", "kangaroo care"),
     "Skin to skin is the naked baby laid on your bare chest, covered with a blanket, in the "
     "first hour and as often as you like after. It keeps them warm, steadies their breathing "
     "and blood sugar, and is the strongest start to feeding - and it works just as well for a "
     "dad or a partner, which is useful when the mother needs stitching or a rest."),
    (("forceps", "forceps delivery", "kiwi cup"),
     "Forceps are the metal tongs a doctor uses to guide the baby out in the last stage, when "
     "pushing is not moving them or one of you is tiring. They leave marks on the head that fade "
     "in a few days, and you are given pain relief first. They are used in about one birth in "
     "fourteen, and a ventouse is the alternative when a cup is enough."),
    (("tongue tie", "tongue-tie", "tongue tied", "tongue-tied"),
     "A tongue tie is the strip of tissue under the tongue being tight or short, so the tongue "
     "cannot lift or reach forward as far as it should - which can make feeding sore and slow. It "
     "is common, it is checked at the newborn examination, and a simple snip in the first weeks "
     "is quick and needs no anaesthetic. Ask a midwife or health visitor to look if feeding "
     "hurts."),
    (("gestational diabetes", "gestational diabetes test", "glucose tolerance test"),
     "Gestational diabetes is high blood sugar that starts in pregnancy, from the placenta's "
     "hormones making insulin work less well - it is tested for with a glucose drink and blood "
     "tests at 24 to 28 weeks if you are at risk. It is managed with diet, monitoring and "
     "sometimes tablets or insulin, and it usually goes after the birth. Nothing you did caused "
     "it."),
)
_BIRTH_WORD_KEY = tuple(word for words, _ in _BIRTH_WORDS for word in words)
_BIRTH_WORD_NAMES = tuple(sorted(((word, reply) for words, reply in _BIRTH_WORDS
                                  for word in words), key=lambda pair: len(pair[0]),
                                 reverse=True))
# A thing people are sent for is asked as "what happens during a c section" as often as
# "what is a c section", and on main every one of those shapes was the search hedge: the walk
# through the day is the same definition the person is after, so the shapes that ask for it are
# part of the definition group.
_BIRTH_ASK = ("what is", "whats", "what's", "what are", "mean", "means", "meaning", "explain",
              "definition", "define", "stand for", "difference", "what does",
              "what happens", "what happens during", "what happens at", "what happens in",
              "what goes on", "what goes on during", "whats it like", "what is it like")


# Everyday words that are also birth words, and are the commoner sense on their own: a section of
# a report, a show on Netflix, a tear in a muscle, an induction hob, a sweep in football, Labour
# Day. Each needs a birth word somewhere in the line (see _A_BIRTH_LINE) before it is answered,
# and the row that owns the other sense keeps the bare ask.
_AMBIGUOUS = frozenset(("section", "show", "a show", "tear", "tears", "a tear", "sweep",
                        "sweeps", "labour", "in labour", "going into labour", "induction",
                        "contraction", "contractions", "bump"))


# Labour Day is a public holiday and a day off is a day off: neither is a birth.
_NOT_A_BIRTH_LINE = re.compile(r"\blabou?r day\b|\bpublic holiday\b|\bday off\b|"
                               r"\bbank holiday\b", re.I)


def _a_birth_word(memory, understood):
    """The term the line names, defined; the longest name first so "birth plan" beats "birth"."""
    reading = understood if isinstance(understood, dict) else {}
    said = (" " + " ".join(str(reading.get("plain") or reading.get("text") or "").lower().split())
            + " ")
    if _NOT_A_BIRTH_LINE.search(said):
        return None
    for word, reply in _BIRTH_WORD_NAMES:
        if not re.search(r"\b" + re.escape(word) + r"s?\b", said):
            continue
        if word in _AMBIGUOUS and not _A_BIRTH_LINE.search(said):
            # a longer name for the same thing may still be in the line - "perineal tear" is not
            # the ambiguous one even when "tear" is also here
            continue
        return reply
    return None


# Contractions is the one word of the glossary that is not mainly a birth word: "what is a
# contraction" is a question about apostrophes as often as about labour, so it needs a pregnancy
# word in the line and the grammar row keeps the bare ask.
_A_BIRTH_LINE = re.compile(
    r"\b(?:pregnan\w*|labour|labor|birth|births|midwife|midwives|due date|weeks|bump|baby|"
    r"babies|newborn|waters|dilat\w*|hospital|epidural|cervix)\b", re.I)


# The timing and the pain are unambiguous without a birth word in the line, so they are answered
# on their own; the plain definition still needs one, because "what is a contraction" is grammar.
_WHEN_TO_CALL = re.compile(
    r"\b(?:how far apart|how often|how close|close together|when should i (?:go|call)|"
    r"how long (?:do|should) (?:they|contractions) last|timing|time them)\b", re.I)
_DO_THEY_HURT = re.compile(r"\b(?:hurt|hurts|painful|pain|supposed to)\b", re.I)

_HOW_FAR_APART = (
    "Time them from the start of one to the start of the next, and call the midwife when they are "
    "about five minutes apart, each one lasting 45 to 60 seconds, for an hour - or straight away "
    "if your waters break, you bleed, the baby stops moving or you feel frightened. A first labour "
    "is usually 8 to 18 hours, so early ones at ten or fifteen minutes apart are the time to rest "
    "and eat rather than go in.")

_THEY_HURT = (
    "Yes, contractions hurt - it is a strong muscle working, and for most people it is the "
    "hardest pain they meet. It peaks and then stops completely between contractions, which is "
    "what makes it bearable, and the relief you can ask for is real: gas and air, a pool, "
    "diamorphine or an epidural. Say what you want early rather than waiting to see how bad it "
    "gets.")


def _a_labour_contraction(memory, understood):
    """The contraction of labour, when the line has a birth in it, or asks about the timing."""
    reading = understood if isinstance(understood, dict) else {}
    said = str(reading.get("plain") or reading.get("text") or "")
    if _WHEN_TO_CALL.search(said):
        return _HOW_FAR_APART
    if _DO_THEY_HURT.search(said):
        return _THEY_HURT
    if not _A_BIRTH_LINE.search(said):
        return None
    return ("A contraction is the womb muscle tightening and then relaxing, which is what opens the "
            "cervix: it builds, holds for 45 to 60 seconds and fades, and the first ones feel like "
            "a bad period pain. They get longer, stronger and closer together as labour goes on. "
            "Time them from the start of one to the start of the next, and call the midwife when "
            "they are about five minutes apart.")


ENTRIES.append(entry(
    "birth-words", (_BIRTH_WORD_KEY, _BIRTH_ASK), _a_birth_word,
    ask=_BIRTH_ASK,
    # a symptom, an appointment, a pain, a cost and a choice are other rows' questions: "my
    # waters broke" and "is it normal to bleed" are answered by the advice rows, and "epidural or
    # not" is a decision, not a definition
    avoid=("bleeding", "bled", "waters broke", "my waters", "pain", "pains", "hurt", "hurts",
           "cramp", "cramps", "contractions are", "how much", "cost", "costs", "price", "pay",
           "should i", "shall i", "or not", "worth it", "safe", "dangerous", "risk",
           "how do i", "how to", "how long", "when do i", "when should i",
           "appointment", "results", "not offered", "decline", "choose", "decide",
           "my friend", "my sister", "my wife", "my partner", "for my"),
    bias=1))

ENTRIES.append(entry(
    "a-contraction-has-a-birth-in-it",
    (("contraction", "contractions"),
     _BIRTH_ASK + ("how far apart", "how often", "how long", "hurt", "hurts", "painful",
                   "supposed to", "close together")),
    _a_labour_contraction,
    ask=_BIRTH_ASK + ("how far apart", "how often", "hurt", "painful"), bias=3))

# The bleeding after a baby is not a period and it is not a birth to register. On main, "is it
# normal to bleed after birth" was the heavy-periods card - clots bigger than a 50p coin read as
# a reason to see a GP about periods - "how long do you bleed after giving birth" was the card
# about registering the birth, and "postnatal bleeding" and "lochia" were nothing at all, even
# though the glossary row below has the answer: that row needs a definition ask, so the term on
# its own never reached it.
#
# The rule is the pair, not the sentences: a bleeding word and a birth word in the same line is
# the lochia question, whatever order they come in. The term is on both sides of the key so that
# "lochia" and "postnatal bleeding" reach it alone, and the pads, the section and the six weeks
# are the words people type when they are worried rather than asking.
_POSTNATAL_BLEED = (
    "bleed", "bleeds", "bled", "bleeding", "blood", "bloods", "clot", "clots",
    "pad", "pads", "lochia", "postnatal", "post natal", "postpartum")
_POSTNATAL_BIRTH = (
    "birth", "births", "after birth", "baby", "babies", "the baby", "my baby",
    "section", "c section", "c-section", "caesarean", "cesarean", "caesarian",
    "postnatal", "post natal", "postpartum", "lochia", "maternity", "midwife",
    "give birth", "gave birth", "giving birth", "delivered", "weeks after", "days after",
    # "bleeding after my son was born" says the birth without the word birth
    "born", "was born",
    # "im still bleeding 4 months after having my son" is the same six weeks, said the long way
    "having my son", "having my daughter", "having a baby", "had my son", "had my daughter",
    "had a baby", "months after", "month after")

ENTRIES.append(entry(
    "postnatal-bleeding",
    (_POSTNATAL_BLEED, _POSTNATAL_BIRTH),
    "Lochia is the bleeding after birth: heavy red blood for three to five days, then browner and "
    "lighter for up to six weeks, coming back a little when you do more - so a bleed still going "
    "past six weeks is a GP visit, not lochia. Use pads, not tampons. Ring your maternity unit the "
    "same day if you soak a pad in an hour, pass clots bigger than a 50p coin, or the blood smells "
    "bad or you are feverish - and 999 or 911 if you are faint, dizzy or flooding.",
    # a period, a miscarriage, a pregnancy and a nappy are other answers: the baby's blood in a
    # nappy is the nappy's, and anything with a period in it is the cycle's
    avoid=("period", "periods", "menstrual", "between periods", "miscarriage", "missed",
           "ectopic", "implantation", "pregnant", "pregnancy test", "after sex", "sex",
           "nappy", "nappies", "poo", "stool", "stools", "cord", "circumcision", "nose",
           "nosebleed", "gums", "tooth", "teeth", "urine", "wee", "cut", "wound", "gash",
           "stitches in my hand", "dog", "cat",
           # the cut from a section is a wound and not lochia, and the person says "scar": a
           # blood test, a heel prick and a jab are somebody taking blood, not blood arriving
           "scar", "scars", "scar tissue", "incision", "stitches", "dressing",
           "blood test", "blood tests", "blood test tomorrow", "heel prick", "screening",
           "jab", "jabs", "vaccine", "vaccination", "vaccinated", "injection", "immunisation",
           "group b strep", "newborn screening",
           # "birth control" is not a birth: a bleed on the pill is the pill's answer, and a
           # bleed inside the head is not this at all
           "birth control", "contraception", "pill", "pills", "implant", "coil", "iud",
           "morning after", "brain", "head injury", "hit my head"),
    # 4, because a dessert row keys "and" and "afters", "after" folds onto "afters", and that
    # row is at bias 3: "bleeding after birth and i feel dizzy" was a pudding idea
    bias=4))

