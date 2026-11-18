"""Routines: starting one, keeping it going after a slip, and stopping one you do not want.

The answers lane owns this domain. The habits.py domain next door answers the habits people
name (vaping, drinking); this one answers the behaviour around any habit at all, so a line that
does name smoking or drinking is left to those entries by the avoid lists below. People ask
about habits in their own words and about anything: walking every morning, practising an
instrument, saving, flossing, cutting down on phone time. The useful answer is the same every
time — make it small, tie it to something that already happens, do not rely on feeling like it
— so the entries here are keyed by the shape of the question (build one, keep one going after a
slip, break one, get off the phone) rather than by the subject of the habit.

Nothing here repeats a domain's own facts: the training plan is sport.py's, the sleep routine is
health.py's, quitting smoking and cutting down on alcohol are health's and safety's, and study
technique is study.py's. This domain only holds behaviour change, which is what nobody else has.
"""
import re

from .body import _the_nail_is_a_persons
from .wording import screens_are_somebody_elses
from .lookup import a_food_is_being_kept, entry

# The topics this domain answers (bot/understanding/topics.py). These are ids other domains
# already declare, so the union answers.py publishes does not change: this file answers the
# lines those domains pass on, it does not take their subject over. "sleep" is deliberately
# left out even though these are behaviour lines: declaring it would add a topic no other
# domain answers, and the arbiter then sends "i keep waking at 3am" to a sleep-hygiene entry
# instead of chat's better clockline answer.
ANSWERS = ("health", "fitness", "school-and-study")

# A habit question asks something or tells you about a routine in progress; it is never the habit
# itself named in passing ("my morning routine is chaos because of the kids" is a parenting line).
HABIT_ASK = ("how", "what", "any", "tips", "help", "should", "can i", "best way", "keep",
             "keep on", "stick", "start", "stop", "break", "build", "get into", "get back",
             "get rid", "kick", "ditch", "want to", "trying to", "struggling", "cut down",
             "always", "never", "end up", "stay",
             # a streak that has just gone is the same question as one to build, and the past
             # tense is how it is said: "i broke my streak", "i broke my streak yesterday and
             # feel awful" reached nothing at all, because a habit row asks "how", "keep" or
             # "start" and the line has none of them
             "broke", "broken", "breaking", "slipped", "slip", "failed", "fell off", "blew it",
             "missed", "miss a day", "missed a day", "skipped", "skip a")

# A machine that keeps doing something is a fault, not a habit. The avoid lists below name the
# fault phrases one by one ("keeps going off", "keeps stopping"), which the next one always gets
# past: on main "my shower keeps going cold", "my laptop keeps going black" and "my phone keeps
# going flat" were all answered "the rule that keeps a habit alive is never miss twice", while a
# washer, a boiler or a car reached its own fault card. The reading that separates them is not
# the phrase but the subject: when the thing named right before the verb is a machine, "keeps"
# says the machine is behaving badly, and the fault cards own that line. A person is still a
# person - "i keep checking my phone" and "my phone keeps me up at night" name the phone and are
# left alone, because the words before the verb there are "i" and "keeps me".
MACHINE_THAT_KEEPS = re.compile(
    r"\b(?:washing machine|tumble dryer|dishwasher|extractor fan|garage door|door bell|doorbell|"
    r"boiler|radiator|heating|hot water|shower|tap|toilet|cistern|fridge|freezer|oven|hob|"
    r"microwave|kettle|toaster|vacuum|hoover|printer|router|wifi|broadband|laptop|phone|"
    r"computer|screen|monitor|tablet|tv|television|camera|watch|headphones|earbuds|battery|"
    r"charger|socket|plug|bulb|lights|fan|car|van|bike|engine|alarm|lock|window)"
    r"s?\s+(?:keeps|keep|kept)\b", re.I)


# A food that keeps doing something is a cooking fault, not a habit of the person's: "my rice
# keeps going sticky" was answered "the rule that keeps a habit alive is never miss twice", because
# "keeps going" is one of the habit row's own words. The subject right before the verb is what
# says which it is - a pot of rice is not a streak.
FOOD_THAT_KEEPS = re.compile(
    r"\b(?:rice|pasta|noodles?|bread|dough|batter|cake|cakes|pastry|sauce|gravy|soup|stew|curry|"
    r"porridge|oats|custard|jam|chocolate|caramel|fudge|icing|meringue|potato|potatoes|chips|"
    r"meat|chicken|fish|egg|eggs|yoghurt|yogurt|milk|cream|tofu|beans|lentils|couscous|quinoa|"
    r"pancakes?|scones?|biscuits?|crust|pizza|mayo|mayonnaise|hollandaise|risotto|stir fry|"
    r"mash|omelette|scrambled eggs|steak|bacon|sausages?)s?\s+(?:keeps|keep|kept)\b", re.I)


# A cup, a loaf or a bowl that keeps going into a bad state is the same kind of line as a machine
# that keeps faulting, and the streak cards were answering it: "why does my tea keep going cold",
# "why does my coffee keep going cold", "my soup keeps going cold" and "why does my bread keep
# going mouldy" all got "the rule that keeps a habit alive is never miss twice". The reading that
# separates them from a habit is not the phrase but the thing: tea, coffee, soup and bread cannot
# have a habit, so when one of them is the thing in front of "keep", the line is about the thing
# going wrong and these cards stand down.
_STATE_WORDS = re.compile(
    r"\b(?:cold|lukewarm|warm|hot|stale|staler|mouldy|moldy|off|flat|soggy|dry|curdled|"
    r"lumpy|burnt|burned)\b", re.I)

GOODS_THAT_KEEP = re.compile(
    r"\b(?:tea|coffee|soup|broth|stew|dinner|food|milk|bread|loaf|toast|cake|cuppa|brew|"
    r"hot chocolate|porridge|rice|pasta|gravy|sauce|drink|pint|beer|wine|juice|cup|mug|pot|"
    r"bath|shower water|washing|laundry)\b\s+(?:keeps|keep|kept)\b", re.I)


def _a_machine_behaving_badly(understood):
    """Whether the line is a thing that keeps doing something, not a habit of the person's."""
    if a_food_is_being_kept(understood):
        # A loaf that keeps going mouldy is a keeping question, not a streak of the person's:
        # "my bread keeps going mouldy in the cupboard" was told the rule that keeps a habit
        # alive is never miss twice. Any other line - "how do i keep my bread habit", "i keep
        # eating bread at night" - names no keeping word and is read exactly as before.
        return True
    said = ""
    for field in ("clean", "text"):
        value = (understood or {}).get(field) if isinstance(understood, dict) else None
        if isinstance(value, str) and value:
            said = value
            break
    if MACHINE_THAT_KEEPS.search(said):
        return True
    return bool(GOODS_THAT_KEEP.search(said) and _STATE_WORDS.search(said))


# What "keeps" is the subject of decides which card owns the line. A person keeps going, a habit
# keeps falling apart: those are streaks. "My hair keeps going frizzy", "my knee keeps giving way",
# "my tomato plants keep wilting" are a thing going wrong, and the card for that thing owns them -
# but the streak card was answering all three, because "keeps going" and "keeps failing" are its
# own words. The word in front of the verb is the reading, so the noun there is what decides.
KEEPS_SUBJECTS = frozenset((
    "i", "we", "you", "they", "he", "she", "people", "everyone",
    "habit", "habits", "routine", "routines", "streak", "streaks", "resolution", "resolutions",
    "goal", "goals", "plan", "plans", "planning", "effort", "efforts", "attempt", "attempts",
    "progress", "motivation", "discipline", "willpower", "schedule", "diary", "calendar",
    "app", "tracker", "journal", "challenge", "programme", "program", "training", "practice",
    "savings", "budget", "diet", "weight", "sleep", "mood", "mind", "thoughts", "anxiety",
    "work", "study", "revision", "job", "career", "friendship", "friendships", "marriage",
    "relationship", "sobriety", "quit", "quitting", "smoking", "drinking", "gambling",
    "walking", "running", "swimming", "cycling", "running plan", "writing", "reading",
    "meditation", "exercise", "exercising", "yoga", "gym", "cooking", "tidying",
))
KEEPS_VERB = re.compile(r"\b([a-z]+)\s+(?:keeps|keep|kept)\b", re.I)

# A habit card is about keeping a habit going, and smoking is a habit only in the abstract: the
# person asking about it wants the stop plan, which knows about nicotine replacement, triggers
# and slips. The habit rows said `"smok"`, meaning to catch smoke/smoking/smoker with one
# string, but an avoid word is matched by form, not by prefix, and `_forms("smok")` is
# `{"smok"}` while `_forms("smoking")` is `{"smoke", "smoking"}` - so the fence never fired
# and "how do i give up smoking" and "how do i break the habit of smoking" got the streak and
# trigger advice instead of the plan. The words below are the ones people actually type.
_SMOKING_IS_NOT_A_HABIT = ("smoke", "smoking", "smoker", "smokers", "smoked", "cigarette",
                           "cigarettes", "fag", "fags", "vape", "vapes", "vaping",
                           "nicotine", "tobacco", "e cigarette", "e-cigarette")


def _a_thing_behaving_badly(understood):
    """Whether a machine or a pot of food keeps doing something, rather than a habit.

    Both are the same reading of "keeps": the subject in front of the verb is a thing going
    wrong, so the fault card owns the line and the habit card stands down. A person is still a
    person - "i keep burning the rice" names the rice after the verb, not before it.
    """
    if _a_machine_behaving_badly(understood):
        return True
    for field in ("clean", "text"):
        value = (understood or {}).get(field) if isinstance(understood, dict) else None
        if isinstance(value, str) and value:
            said = value.lower()
            if FOOD_THAT_KEEPS.search(said):
                return True
            # anything else in front of "keeps" that is not a person or a habit is a thing
            # going wrong - hair, a knee, a tomato plant - and some other card answers it.
            subjects = KEEPS_VERB.findall(said)
            if subjects and not all(word in KEEPS_SUBJECTS for word in subjects):
                return True
            return False
    return False



# "how do i stop paying for facebook": the habit card is for the pull, and a line about money is
# not the pull. Read from the line, not the key, so the money words stay out of the vocabulary.
_MONEY_WORDS = ("pay", "pays", "paying", "pay for", "paid", "pays for", "payment", "bill",
                "billed", "billing", "subscription", "subscriptions", "subscribed", "cost",
                "costs", "costing", "price", "prices", "priced", "charge", "charged", "charges",
                "refund", "refunded", "cancel", "cancelled", "canceled", "cancel my",
                "free trial", "upgrade", "premium", "monthly", "direct debit", "invoice")


def _not_about_money(understood):
    """False when the line asks about paying, so the habit rows stand down for it."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text", "raw")).lower()
    return not any(word in said for word in _MONEY_WORDS)

ENTRIES = [
    entry("habit-build-routine", (("habit", "habits", "routine", "ritual"),
                          ("build", "start", "make", "form", "form a", "get into", "new",
                           "better", "good", "create", "stick")),
          "Make it too small to fail: two minutes, one press-up, one page. Tie it to something "
          "you already do at the same time each day — after you brush your teeth, before you sit "
          "down with a coffee — so the day decides instead of your mood. Do one habit at a time "
          "for a month, and mark it off on a calendar you see, because seeing the chain is what "
          "keeps it going when the first enthusiasm runs out.",
          ask=HABIT_ASK,
          avoid=_SMOKING_IS_NOT_A_HABIT + ("drink", "alcohol", "drug", "gambling", "gamble",
                 "sugar", "diet", "lose weight", "quit", "nail", "biting", "thumb", "bedtime",
                 "nap", "baby", "toddler", "kids", "child", "puppy", "toilet",
                 "cleaning", "clean the", "tidy", "chores", "food", "eat", "eating", "sugar",
                 # "whats a good workout routine" was this row, which answers how to *start* a
                 # habit and not what the routine should contain. The subjects with contents of
                 # their own stand it down: fitness.py has the training week, cleaning.py the
                 # house rota, and the sleep and study cards answer their own.
                 "workout", "workouts", "gym", "exercise", "exercises", "training",
                 "study", "studying", "revision", "revise", "revising", "sleep",
                 # the start and end of the day have their own cards too: the night-before
                 # list for a morning, and the wind-down for a night
                 "morning", "mornings", "night", "nights", "evening", "evenings",
                 "biscuit", "biscuits", "chocolate", "snack", "snacks", "salt", "caffeine",
                 "carb", "carbs", "dairy", "meat", "takeaway")),
    # A line that says "make it stick" or "keep it up" is the same question with no noun on it:
    # the thing being kept up is whatever the last few turns were about, and the answer is how to
    # carry on. Without these words the line reached nothing at all, and the pan-fault row in
    # cooking answered "how do i make it stick" with advice about a hot frying pan.
    entry("habit-restart", (("habit", "habits", "streak", "streaks", "routine", "resolution",
                             "resolutions", "goal", "goals", "keep starting",
                             "make it stick", "make it stick this time", "stick with it",
                             "stick at it", "keep it up", "keep going", "keep at it",
                             "dont give up", "not give up", "stay on it",
                             "starting and stopping", "started and stopped", "give up",
                             "gave up", "keep failing", "keep messing up",
                             # the subject said with its owner: a two-word phrase here is what
                             # lifts "i broke my streak" over the line, because the second key
                             # part can only reach "broke" once "streak" is already covered
                             "my streak", "the streak", "my habit", "the habit", "my routine",
                             "my resolution", "new years resolution", "new year resolution"),
                            ("keep starting", "starting and stopping", "started and stopped",
                             "give up", "gave up", "lose it", "lost it", "slip", "slipped",
                             "missed", "miss a", "keep failing", "again", "failed", "fail",
                             "restart", "back on track", "cant stick", "can't stick", "keep",
                             # "make it stick" is a phrase in the first part and the word it
                             # turns on has to be in this one too, or the two words the score
                             # needs are one phrase and nothing else: "how do i make it stick"
                             # was a search hedge.
                             "stick", "make it stick", "carry on", "keep on",
                             "keep going", "lose", "lost", "going", "broken", "broke",
                             "break", "breaking", "reset",
                             # one word is not enough on this row - the score needs two key
                             # parts - so the whole shape of a broken streak is here, and
                             # "i broke my streak" stops reaching nothing at all
                             "broke my streak", "break my streak", "breaking my streak",
                             "broke the streak", "breaks my streak", "my streak broke",
                             "lost my streak", "ruined my streak", "streak broke",
                             "missed my streak", "missed the streak", "missed a day",
                             "after a week", "after a month", "after a few weeks", "week",
                             "weeks", "month", "months", "soon", "every time", "stay",
                             "stay on track", "on track", "stick with", "with my")),
          "The rule that keeps a habit alive is never miss twice: one missed day is a rest, two "
          "is how a habit ends, so the day after a slip you do the smallest version — one minute, "
          "one page — and the chain starts again. Plan that now, before the bad week, and cut the "
          "habit to a size that survives it rather than resetting to the version you could only "
          "do while life was calm. A streak you broke is not a score you lost: keep the total "
          "visible, mark today, and carry on from there instead of waiting for a fresh Monday.",
          ask=HABIT_ASK,
          # a machine or a pot of food that keeps doing something is a fault, not a broken habit
          guard=lambda understood: not _a_thing_behaving_badly(understood),
          # "my serve keeps going long" and "my golf swing keeps going right" are technique
          # questions: the word "keeps" is the only thing they share with a broken habit
          avoid=("my serve", "serve keeps", "serves keep", "serving", "my swing", "swing keeps",
                 "golf swing", "putt", "putts", "forehand", "backhand", "volley", "batting",
                 "darts", "golf", "tennis", "badminton", "squash", "cricket", "netball",
                 ) + _SMOKING_IS_NOT_A_HABIT + ("alcohol", "drink", "drug", "gambling", "diet",
                 "lose weight", "quit", "nail", "biting", "bedtime", "sleep", "baby", "toddler",
                 "kids", "child", "food", "eat", "eating", "sugar", "biscuit", "biscuits",
                 "chocolate", "snack", "snacks", "salt", "caffeine", "carb", "carbs", "dairy",
                 "meat", "takeaway",
                 # "my friend has cancer and i keep going over it" is not a streak: the words
                 # "keep going" reached this row and it answered never-miss-twice. News about
                 # somebody else's illness is the worry cards' line, and a person who cannot stop
                 # turning it over does not need a habit rule.
                 "cancer", "diagnosis", "diagnosed", "chemo", "hospice", "terminally",
                 "bereaved", "funeral", "died", "dying", "going over", "over it", "replaying",
                 "in my head", "going round",
                 # A subject going badly is a study question, not a streak: "i keep failing
                 # maths what should i do" shares "keep failing" with this row and was told
                 # about never missing twice, when the answer is how to work at maths.
                 "maths", "math", "english", "science", "biology", "chemistry", "physics",
                 "history", "geography", "french", "spanish", "german", "revision", "revise",
                 "revising", "exam", "exams", "past paper", "past papers", "mock", "mocks",
                 "my grades", "my marks", "gcse", "a level", "a levels",
                 # a driving test failed twice is a lessons question, not a streak
                 "driving test", "driving lesson", "driving lessons", "driving instructor",
                 # A machine that keeps going wrong is a repair decision, not a habit: "my car
                 # keeps failing its mot" shares only "keep" and "fail" with this entry, and two
                 # ordinary words were enough for it to answer a car line with a streak. The
                 # things below only ever turn up in a repair line, so a phone or an app stays a
                 # habit question ("how do i stop checking my phone in bed").
                 "car", "cars", "van", "mot", "garage", "engine", "boiler", "radiator",
                 "washing machine", "dishwasher", "tumble dryer", "fridge", "freezer", "oven",
                 "worth fixing", "worth repairing",
                 # A screen that keeps going black is a repair question as well, and the key
                 # above holds "keep" beside "going" and "black" was not needed: "my laptop
                 # screen keeps going black" was answered with never miss twice. The shapes
                 # below only ever describe a machine that keeps faulting, so the fault is what
                 # is fenced and not the device: a bare "screen" here took the habit card off
                 # "i keep going back to my screen after work", which is the line this row is for.
                 "keeps going black", "going black", "goes black", "went black",
                 # A charge that keeps going up is a bill question, not a streak: "my rent keeps
                 # going up" is the same shape as a machine that keeps faulting, and it was told
                 # about never missing twice. `money.rent-rise` answers it.
                 "rent", "rents", "council tax", "my tax", "taxes", "the price of", "prices",
                 "price", "bills", "my bills", "energy bill", "cost of living", "interest rate",
                 "interest rates", "fares", "mortgage", "inflation",
                 "keeps going flat", "going flat", "keeps going dark", "keeps going dim",
                 "black screen", "blank screen", "keeps going blank", "going blank",
                 "keeps flickering", "flickering", "flickers", "keeps turning itself off",
                 "turns itself off", "keeps restarting", "restarting itself",
                 "keeps freezing", "keeps crashing", "wont turn on", "wont switch on",
                 "wont come on", "keeps dropping", "keeps disconnecting", "keeps cutting out",
                 "no signal",
                 # a device named on its own is still a habit line, so only the fault phrases
                 # above are fenced; these carry the same faults beside the device's name
                 "screen keeps going", "screen going black", "screen going blank",
                 # And a line that names the practice has a card of its own for it: "how do i
                 # keep going with my running" is the run-walk plan and "how do i keep going
                 # with my learning" is how to test yourself, so the bare "keep going" does not
                 # take them. A practice with no card of its own ("keep going to the gym") still
                 # reaches this one, which is the line it belongs to.
                 "running", "jogging", "swimming", "cycling", "walking", "learning",
                 "revision", "revising", "study", "studying",
                 # A thing that goes off, comes back or drops on its own is a fault, and "keeps
                 # going off" shares "keeps going" with this row: "my smoke alarm keeps going off
                 # when i cook" was answered "the rule that keeps a habit alive is never miss
                 # twice". The fault cards own those lines, so the carrying-on phrases that only
                 # look like a habit stand down on them.
                 "keeps going off", "keeps going out", "keeps coming back", "keeps dropping",
                 # the same for a screen: "the sky box keeps going blank" was told the rule that
                 # keeps a habit alive is never miss twice
                 "keeps going blank", "gone blank", "goes blank", "keeps going fuzzy",
                 "keeps losing the picture", "keeps breaking up", "keeps going dark",
                 "keeps leaking", "keeps tripping", "keeps cutting out", "keeps beeping",
                 "keeps flashing", "keeps stopping", "keeps jamming",
                 # And a line asking whether something will heal is a question about the body,
                 # not about a streak: "i cant breathe when i run for the bus" then "will that
                 # get better if i keep at it" was the habit card, and "keep at it" there means
                 # the exercise the breathlessness answer had just described.
                 "will that get better", "will it get better", "will this get better",
                 "will they get better", "does it get better", "does that get better",
                 "get better on its own", "clear up on its own", "go away on its own",
                 "get better if i", "if i keep at it",
                 # A set that keeps going off is a fault, and "keep going" is in the key:
                 # "my telly keeps going off on its own" was being answered with a streak
                 "telly", "going off", "switches off", "switching off", "turns off",
                 "turning off", "power", "electricity", "lights", "socket")),
    entry("habit-break", (("habit", "habits", "routine", "cue", "trigger", "willpower"),
                          ("break", "stop", "quit", "cut down", "cut back", "give up", "get rid",
                           "kick", "ditch", "less", "reduce", "bad", "worse", "control")),
          "Work on the trigger rather than the willpower: note when the habit happens for three "
          "days, then change that moment — the biscuit tin out of the cupboard, the phone charging "
          "in the hall, a different route past the shop. Have a replacement ready for the same "
          "slot, because an empty slot fills itself. When the urge arrives, wait it out for ten "
          "minutes; urges peak and fall instead of building, so the ten minutes is the whole trick.",
          ask=HABIT_ASK,
          bias=2,
          avoid=_SMOKING_IS_NOT_A_HABIT + ("alcohol",
                 "drinking", "drunk", "drug", "drugs", "weed", "gambling", "gamble", "betting",
                 "porn", "sugar", "sugary", "caffeine", "coffee", "nail", "biting", "thumb",
                 "skin", "picking", "hair", "food", "eat", "eating", "sugar", "biscuit",
                 "biscuits", "chocolate", "snack", "snacks", "salt", "caffeine", "carbs",
                 "dairy", "meat", "takeaway", "phone", "screen")),
    entry("nail-biting", (("nail", "nails", "nail biting", "biting my nails",
                           # "nibbling" is the third word people use for the same habit, and
                           # without it "how do i stop nibbling my nails" fell past every nail
                           # card to a garden row about caterpillars on cabbages
                           "nibbling my nails", "nibble my nails", "nibbled nails"),
                          # "bitten" is the word a history uses ("ive bitten my nails since i
                          # was a kid"), and without it that line reached only the card about a
                          # child's nails
                          ("bite", "biting", "bit", "bitten", "stop", "chew", "chewing", "habit",
                           "help")),
          "Keep them short and filed, because a ragged edge is what a tooth finds. Notice the "
          "moment you start — driving, on the phone, reading — and give that hand something else "
          "to do: a ring to twist, a pen, a stress ball. A bitter-tasting polish from the pharmacy "
          "works because it makes you aware of the bite, not because it is unpleasant; the point "
          "is the pause, and the habit fades once you notice it often enough.",
          # a person describing the habit ("i keep chewing my nails at my desk") is asking the
          # same thing, so the gate is a request or a statement of the habit itself, not only a
          # question word: "i bite my nails" and "i chew my nails when im nervous" are the same
          # question, and they were reaching the card about a child's nails and being told to
          # mention it once, kindly
          ask=("how", "what", "any", "tips", "help", "stop", "can i", "keep", "always",
               "cant stop", "can't stop", "want to",
               # the plainest way people say it is not a question at all: "i bite my nails" and
               # "i chew my nails when nervous" were left to the composer's nod, and the only
               # card that answered them was the one written for a parent watching someone else
               "i bite", "i chew", "i bit", "i keep biting", "i keep chewing", "i always bite",
               "i always chew", "i nibble", "i keep nibbling",
               # the habit said as a history or a wish: "ive bitten my nails since i was a kid",
               # "i want to stop biting my nails", "i cant stop biting them". Each was reaching
               # the card about a child's nails and being told to mention it once, kindly. A
               # child's nails are fenced off by the avoid list below, not here.
               # the phrasing itself, so a line that names the nails the person bites reaches
               # this card whatever the rest of the sentence says ("im 34 and i still bite my
               # nails", "nail biting", "how do i stop chewing my nails")
               "bite my nails", "biting my nails", "chew my nails", "chewing my nails",
               "nail biting", "nails biting", "bitten", "keep biting my nails",
               "want to stop biting", "cant stop biting", "can't stop biting", "biting them"),
           # a nail in a joist is not a habit: "how do i nail two bits of wood together" was
           # answered with the bitter-polish plan
           guard=_the_nail_is_a_persons,
          # An injured nail is not a habit: a nail that went black, bruised or lifted after a
          # knock wants ice and a look, so "what helps a bruised nail" and "my nail has gone
          # black" stand this down rather than get the bitter-polish plan. A nail that hurts is
          # the same health question as a nail that went black.
          # What the nail looks like is the other question: "what helps a yellow nail" and "my
          # nail is discoloured and thick" were answered "Keep them short and filed, because a
          # ragged edge is what a tooth finds... bitter-tasting polish", because this row keys
          # `help`/`what` and the word nail. A nail that is yellow, thick or crumbling is the
          # fungus card, and the colour words are what tell the two apart.
          avoid=("yellow", "thick", "thickened", "thickening", "crumbly", "crumbling", "crumbles",
                 "discoloured", "discolored", "brown", "white spots", "ridging", "ridges",
                 "fungus", "fungal",
                 "finger", "thumb is", "toe", "toenail", "fungal", "infection", "painting",
                 "polish colour", "gel", "acrylic", "broken nail", "split",
                 "bruised", "bruise", "black", "blue", "dropped", "slammed", "hammer", "caught it",
                 "fell off", "lifting", "lifted", "sore", "throbbing",
                 "hurt", "hurts", "hurting", "pain", "painful", "inflamed", "red and",
                 "abscess", "bleeding", "doctor", "gp", "pharmacist",
                 # this card is the person's own habit. A parent asking about a child
                 # ("my daughter bites her nails", "how do i help my child stop biting his
                 # nails") wants bot/knowledge/family.py's nail-biting-edges, where the advice
                 # is how to help someone else
                 # said with the person it belongs to, not as a bare word: "i bit my nails as a
                 # kid" and "since i was a child" are the person's own habit, and a bare "kid"
                 # in the avoid list sent them to the card about a child's nails
                 "my child", "my children", "my son", "my daughter", "my boy", "my girl",
                 "my toddler", "my teenager", "their nails", "they bite",
                 "he bites", "she bites", "his nails", "her nails")),
    entry("phone-distraction", (("phone", "scroll", "scrolling", "doomscroll", "doomscrolling",
                                 "notifications",
                                 # the app named instead of the phone: "how do i stop checking
                                 # instagram", "how do i stop looking at facebook", "how do i
                                 # stop using snapchat so much", "how do i stop scrolling tiktok
                                 # at night" are the same habit said with the pull's name, and
                                 # they were a hedge. The second word still gates it, so an
                                 # account to close, a subscription to cancel or a post that was
                                 # taken down is not this row - and the money words below are
                                 # the fence that keeps "how do i stop paying for facebook" out.
                                 "instagram", "facebook", "snapchat", "tiktok", "twitter",
                                 "reddit", "youtube", "whatsapp", "linkedin",
                                 "social media", "socials"),
                               ("distract", "distracting", "distracted", "distraction", "end up",
                                "cant stop", "can't stop", "put it down", "all day", "waste",
                                "wasting", "instead of", "too much time", "stop scrolling",
                                "scroll", "scrolling", "at night", "before bed", "way too much",
                                # the lines that name the pull rather than the phone: "how do i
                                # stop doomscrolling", "my phone is distracting me at work", "i
                                # check my phone first thing in the morning", "how do i reduce
                                # screen time". Each needs the word in the first part too, so a
                                # line about a broken, lost or pinging phone still cannot reach
                                # here.
                                "doomscroll", "doomscrolling", "distracting me", "distracts me",
                                "at work", "while i work", "screen time", "first thing",
                                "in the morning", "use it less", "phone less", "reach for it",
                                # "how do i stop doomscrolling" is the pull named once and
                                # nowhere else, so the stop has to count as the second word:
                                # a fault (broken, dying, pinging, blocked) is in the avoid
                                # list below, which is what keeps this from being "stop"
                                # as a topic in its own right.
                                "stop", "stops", "stopping", "stayed off", "time on it",
                                # The habit said as a habit rather than as the pull: "how do i
                                # cut down on my phone" (which reached the phone-contract answer
                                # about the retention price), "im always on my phone how do i
                                # stop" and "my girlfriend says im always on my phone" (both of
                                # which reached the children's screen limit), and "my phone habit
                                # is out of control" (which reached a stain card). These are
                                # said as phrases, not as single common words: "less", "limit"
                                # and "habit" alone are keys of other rows, and widening this row
                                # with them made those rows rarer and the cards that own them
                                # lose their own lines. The phone, the app or "screen time" is
                                # still needed in the first part, and a child's screens are
                                # fenced out by the guard below.
                                "cut down", "cutting down", "cut back", "cut down on it",
                                "addicted to my phone", "addicted to it", "phone addiction",
                                "always on my phone", "always on it", "on it all the time",
                                "on my phone all", "cant put it down", "can't put it down",
                                "my phone habit", "phone habits", "out of control", "too attached",
                                "glued to my phone", "glued to it")),
          "Take the choice out of the moment rather than counting on willpower: put the phone "
          "in another room while you get on with something, turn off everything except calls, "
          "and charge it outside the bedroom so the first and last hour of the day are "
          "phone-free. If you want a handbrake, set a screen-time limit and let someone else "
          "hold the passcode, since a limit you can dismiss is not a limit.",
          ask=("how", "what", "any", "tips", "help", "should", "can i", "keep", "stop", "cant",
               "can't", "ways", "distracting me", "distracts me", "keeps", "too much", "less",
               # a line that reports the habit instead of asking about it: "my girlfriend says
               # im always on my phone", "my phone habit is out of control" - the person wants
               # the habit broken, and the report is the ask
               "says", "told me", "my phone habit"),
          # A payment is not a habit. With the app names in the key above, "how do i stop paying
          # for facebook" became "take the choice out of the moment" - willpower advice for a
          # question about a bill - and the free-app row that owns the line never saw it. The
          # words live here rather than in the `avoid` list because an avoid word counts towards
          # how rare a word is across the knowledge base, and moving the money words into this
          # domain made two money rows lose their own lines.
          guard=lambda reading: (_not_about_money(reading)
                                 and not screens_are_somebody_elses(reading)),
          avoid=("battery", "charger", "charging", "dying", "dies", "cracked", "screen is", "wifi",
                 # a subscription billed through the phone is the cancellation card's line:
                 # "how do i stop a subscription on my phone bill" was answered with the screen
                 # time tips, which is a phone repair answered with "put it down"
                 "subscription", "subscriptions", "unsubscribe", "phone bill",
                 "direct debit", "free trial",
                 # "stopped working" stems to "stop", which is in the key: a broken touch screen
                 # is a repair question, not the pull of the phone
                 "touchscreen", "touch screen", "stopped working", "not working", "doesnt work",
                 "does not work", "not responding", "wont respond", "unresponsive", "frozen",
                 "freezes", "freezing", "restart",
                 # "how do i take better photos at night on my phone" is the camera, not the habit:
                 # "at night" is in the key above, so the camera words have to hold it off
                 "photo", "photos", "picture", "pictures", "camera", "pics", "video", "videos",
                 "selfie", "selfies", "shoot", "photograph", "photographs", "zoom", "lens",
                 "wi-fi", "sim", "contract", "storage", "storage full", "update", "water",
                 "broken", "stolen", "new phone", "which phone", "upgrade", "kids", "kid",
                 "child", "children", "son", "daughter", "toddler", "baby", "teenager", "waking",
                 "wake me", "woke me", "asleep", "alarm", "ping", "pinging", "pings", "sound",
                 "sounds", "vibrate", "vibrating", "ring", "ringing", "do not disturb", "silent",
                 # a phone that buzzes or beeps is a sound question, and main answers it
                 # with Do Not Disturb; "stop" is in the key now, so these have to be here
                 "buzz", "buzzes", "buzzing", "beep", "beeping", "beeps",
                 "block", "blocked", "blocking",
                 # the screen's own setting, not the habit: "how do i stop my phone screen timing
                 # out" is a timeout question and the phone-habit card is not the answer
                 "timing out", "times out", "timed out", "timeout", "screen goes off",
                 "goes off", "stays on", "auto lock", "autolock", "lock screen", "screen locks",
                 # the setting, named: "how do i switch off notifications" and "how do i stop
                 # notifications" are answered by the Do Not Disturb row in technology, not by
                 # advice to put the phone in another room
                 "notification", "notifications",
                 # a phone that eats data is a setting question, not a habit: "how do i stop my
                 # phone using data" and "how do i stop my phone using so much data" were told to
                 # put the phone in another room and charge it outside the bedroom, because
                 # "phone" and "stop" are both here. The data rows answer the same ask with the
                 # per-app list and background refresh, which is what the person wanted.
                 "using data", "use data", "uses data", "so much data", "lots of data",
                 "mobile data", "data usage", "data plan", "data allowance", "data cap",
                 "data limit", "gb of data", "eating my data", "eat my data", "eats my data",
                 "saving data", "save data", "hotspot", "tethering",
                 "block this", "scam", "spam", "nuisance", "taxi", "lost it", "left it",
                 "left my phone", "stolen", "find my",
                 # A mouse and a keyboard are the computer's parts, so "my mouse stopped
                 # scrolling" is a faulty mouse and not a phone habit.
                 "mouse", "mice", "keyboard", "trackpad", "touchpad",
                 # a camera question is not a screen-time question: "how do i take better photos
                 # at night on my phone" was landing here. The camera words only - "night" and
                 # "dark" stay out, because they are this answer's own lines ("how do i stop
                 # scrolling at night").
                 "photo", "photos", "picture", "pictures", "photography", "camera", "cameras",
                 "blurry", "blurred", "in focus", "zoom")),
]


# "what can i do about the morning rush" and "how do i make mornings less rushed" were search
# hedges, and "morning routine tips" got the greeting. The habit entries here are keyed on the
# habit (build one, restart one, break one); an ordinary weekday morning is not a habit, it is a
# plan, so it had nothing. The answer is what to move to the night before, the three things that
# have to happen and where the lost ten minutes usually go.
ENTRIES.append(entry(
    "morning-rush",
    (("morning", "mornings", "school run", "get out the door", "out the door", "before work",
      "before school", "getting ready"),
     ("rush", "rushed", "rushing", "late", "always late", "running late", "chaos", "hectic",
      "stress", "stressful", "smoother", "calmer", "easier", "slow", "routine", "tips", "plan",
      "organised", "organized", "time", "quicker", "faster", "start")),
    ("The night before does most of it: clothes out, bag and keys by the door, breakfast and lunch "
     "decided, and the alarm set for the time you actually need rather than the time you hope for. "
     "In the morning keep only three things that must happen - washed and dressed, something "
     "eaten, out of the door - and let the rest wait, because a fixed order you do without "
     "deciding is what stops the rush. Give yourself fifteen minutes more than you think you need "
     "for the first week, and leave the phone face down until you are out, because one scroll is "
     "where the last ten minutes go."),
    ask=("how", "what", "any", "tips", "help", "should", "ways", "make", "stop", "less", "cant",
         "can't"),
    # a school refusal, a child who will not get up and a person who cannot wake are other
    # answers, and so is the commute
    avoid=("refuses", "refusing", "wont go", "won't go", "school refusal", "anxiety",
           "wont get up", "won't get up", "cant wake", "can't wake", "oversleep", "sleep through",
           "insomnia", "wake up early", "waking up", "night shift", "shift work", "commute",
           "traffic", "train times", "bus times", "missed the bus", "alarm clock", "snooze",
           # "how do i complain" is not a routine question. One deck conversation - the bus
           # cancelled three mornings running, late twice, how do i complain - came here for the
           # night-before plan and stayed for three turns, because "late" and "mornings" are in
           # both halves of this key. The complaint rows answer it.
           "complain", "complaining", "complaint", "complaints", "refund", "delay repay",
           "cancelled", "canceled", "cancellation", "delayed", "replacement bus",
           "depressed", "depression", "exhausted", "burnout", "baby", "newborn", "toddler",
           "night feeds"),
    bias=1))
