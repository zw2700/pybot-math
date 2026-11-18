"""Fitness: getting started, how much to do, and what a short session is worth.

The answers lane owns this domain. Data only, on the shared matcher: one Entry per thing
people ask about (starting to run, a first 10k, sore muscles, steps) and the help a good
coach would give in two sentences.

It also holds the session itself - how many sets and reps, how heavy, how long between sets,
when to add weight, how long to be there, whether to train to failure. Each of those is a
different question with a different answer, so each is its own entry, keyed on the words its
own question is asked with and leading with the number the person came for."""
import re

from .lookup import A_HOUSE_WARMING_UP, entry, the_back_is_a_body_part
from .body import _the_part_is_a_persons

# How long the person says they have. The short-session answers used to print "with 20 minutes"
# whoever asked and whatever they said, so "i only manage five minutes of exercise" was told to do
# a 20-minute circuit and "is a 10 minute workout enough" got the same 20 minutes back. The number
# is in the line, so the answer reads it and answers for the time the person actually has.
_MINUTE_WORDS = {"five": 5, "ten": 10, "fifteen": 15, "twenty": 20, "twenty five": 25,
                 "twenty-five": 25, "thirty": 30, "forty": 40, "forty five": 45, "sixty": 60}
_MINUTES_COUNTED = {5: "five", 10: "ten", 15: "fifteen", 20: "twenty", 25: "twenty-five",
                    30: "thirty", 40: "forty", 45: "forty-five", 60: "sixty"}
_MINUTES_NAMED = re.compile(r"\b(?:(\d{1,3})|(five|ten|fifteen|twenty(?:[\s-]five)?|thirty|"
                            r"forty(?:[\s-]five)?|sixty))\s*(?:-|\s)\s*(?:mins?|minutes?)\b")


def _minutes(text):
    """How many minutes the line is about, or 0 when it does not say."""
    text = str(text or "").lower()
    found = []
    for match in _MINUTES_NAMED.finditer(text):
        digits, word = match.group(1), (match.group(2) or "").replace("-", " ")
        if digits:
            found.append(int(digits))
        elif word in _MINUTE_WORDS:
            found.append(_MINUTE_WORDS[word])
    if re.search(r"\bhalf an hour\b", text):
        found.append(30)
    elif re.search(r"\b(?:an|one|1)\s+hour\b", text):
        found.append(60)
    return max(found) if found else 0


def _minute_phrase(minutes):
    """The number as a word where it is a word people say, else the digits."""
    return _MINUTES_COUNTED.get(minutes) or str(minutes)


_PRESS_UP_PLAN = (
    "Start from your knees or with your hands on a worktop, and add one rep a week rather than "
    "chasing a number - five sets of three done properly beats one shaky ten. When a worktop set "
    "of ten is easy, drop to the next lower surface, then to the floor: a couple of months of "
    "twice a week is what takes somebody from none to ten.")
_PULL_UP_PLAN = (
    "Start with the hang: 20 to 30 seconds from the bar, three times, twice a week, then negatives "
    "- jump to the top and lower yourself as slowly as you can for three to five seconds, three "
    "sets of three. A resistance band under your knee or an assisted machine fills the gap while "
    "you build up, and most people get their first pull up in six to twelve weeks of twice a week.")


def _the_rep_plan(memory, understood):
    """The progression for the move the line actually names."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or " ".join(
        (understood or {}).get("words") or ())).lower()
    if re.search(r"\b(?:pull|chin)[\s-]?ups?\b", text):
        # "how do i work up to a pull up" was handed the press-up progression, which starts from
        # your knees on the floor and never mentions a bar.
        return _PULL_UP_PLAN
    return _PRESS_UP_PLAN


# The day the ache came is half of the soreness question, and it is the half the scorer does not
# insist on: a row answers on any two words of its key, so "arm" and "hurt" reached the
# day-after answer with no day in the line at all. "my son fell off the trampoline and hurt his
# arm", "my son hurt his leg" and "he hurt his arm" are a fall or a knock, and telling a parent
# that their child's muscles are repairing themselves is wrong about the cause and about the
# person. So the row asks for the day its own key is written with.
_ACHE_DAY = re.compile(
    r"\b(?:(?:a|one|two|three|four|five|six|seven|eight|nine|ten|few|couple\s+of)\s+days?|"
    r"(?:the\s+)?day\s+after|next\s+day|days?\s+(?:after|later|since)|48\s+hours|"
    r"second\s+day|third\s+day)\b")
# Somebody else's ache is not the speaker's: the answer says "your muscles", and a parent asking
# about a child is asking for that child.
_ACHE_SOMEONE_ELSE = re.compile(r"\b(?:his|her|their)\b")


def _the_ache_has_its_day(understood):
    """False when the line names no day after the exercise, or the ache is somebody else's.

    The part still has to belong to a person rather than a chair (body.py's test), because a
    table's legs hurt too.
    """
    if not _the_part_is_a_persons(understood):
        return False
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    if _ACHE_SOMEONE_ELSE.search(said):
        return False
    return bool(_ACHE_DAY.search(said))


def _short_workout(memory, understood):
    """The kitchen-floor circuit, sized to the minutes the person says they have."""
    minutes = _minutes((understood or {}).get("text") or " ".join(
        (understood or {}).get("words") or ()))
    circuit = ("40 seconds each of squats, press-ups (on your knees is fine), a plank and lunges, "
               "twice round, with a minute's rest")
    keeps = ("Bodyweight work like that keeps strength and gets your heart going without a gym.")
    if minutes and minutes <= 5:
        # A person who says they have five minutes is not short of a workout, they are short of
        # time and probably short of faith that it counts: say it does before saying what to do.
        return ("Even " + _minute_phrase(minutes) + " minutes counts: 40 seconds each of squats, "
                "press-ups (on your knees is fine) and a plank, twice round, and that is a real "
                "session. " + keeps)
    if minutes:
        if minutes >= 30:
            return ("With " + _minute_phrase(minutes) + " minutes, do a circuit: 40 seconds each "
                    "of squats, press-ups (on your knees is fine), a plank and lunges, three "
                    "times round, with a minute's rest, then a brisk walk to finish. " + keeps)
        # Twenty minutes is the sentence this answer has always given, word for word, so the rows
        # and the chats that already read well do not change for a change of number style.
        if minutes == 20:
            return ("With 20 minutes, do a circuit: " + circuit + ". " + keeps)
        return "With " + _minute_phrase(minutes) + " minutes, do a circuit: " + circuit + ". " + keeps
    return ("In the time you have, do a circuit: " + circuit + ". " + keeps)


# The words that make a run question a count of sessions rather than an hour of the day, and the
# words that name an hour. "times" is "time" with an -s, so the tokenizer hands a count the key
# word "time" - the row has to tell the two apart itself (see `_a_count_beside_the_hour`).
THE_COUNT_OF_SESSIONS = ("how often", "how many times", "times a week", "times per week",
                         "times a day", "days a week", "a week", "per week", "frequency")
THE_HOUR_ITSELF = ("morning", "evening", "afternoon", "at night", "night", "time of day",
                   "what time", "which time", "best time", "before work", "after work",
                   "first thing")


# Money is not a workout. "is 20 pounds each way cheap for a train" reached the short-workout row
# because a train is a "training" and "20" is one of the row's numbers, and the person was handed
# the kitchen-floor circuit. The fare has its own words, and none of them belong here.
_MONEY_IN_THE_LINE = re.compile(
    r"\b(?:pounds?|quid|pence|euros?|dollars?|cheap|cheaper|cheapest|expensive|price|prices|"
    r"cost|costs|costing|fare|fares|ticket|tickets|refund|paid|pay|paying)\b|£|\$|€")


def _not_a_fare(understood):
    """False when the line is about what something costs: the circuit is no answer to a fare."""
    said = " " + str((understood or {}).get("clean") or "").lower() + " "
    return not _MONEY_IN_THE_LINE.search(said)


def _a_count_beside_the_hour(understood):
    """False when the line asks how many times a week and names no hour of the day.

    "how many times a week should i run" is a count of sessions, and the row that answers
    "how often should i run" is the better one. But a count said *beside* an hour still asks
    about the hour: "should i run in the morning if i only run twice a week" and "what time of
    day should i run, i want to go 3 times a week" were both told how many runs to do, and the
    second one reached a holiday card when this row stood down, because nothing else answered.
    """
    said = " " + str((understood or {}).get("clean") or "").lower() + " "
    if not any(phrase in said for phrase in THE_COUNT_OF_SESSIONS):
        return True
    return any(phrase in said for phrase in THE_HOUR_ITSELF)


# A session the person went to and enjoyed is a chat, not a question about when to go: "i went to
# the gym this morning, it was quiet" and "going to the gym for the first time in ages, any tips"
# both got this row when "gym" joined the key, and the chat and the beginner's answer were better.
# So the line has to ask about the time - or name the hour work ends, which is a time of day for
# the session - and nothing else here counts as asking.
_A_TIME_IS_ASKED = ("when", "what time", "which time", "best time", "time of day", "time should",
                    "time to go", "time to exercise", "time to work out", "time to train",
                    "first thing", "before or after", "or morning", "or evening", "morning or",
                    "evening or", "before work", "after work",
                    "finish work", "finishes work", "finished work", "get out of work",
                    "out of work at", "leave work", "left work", "work until", "work till",
                    "working until", "working till", "after my shift")


def _a_time_is_asked(understood):
    """False when the line does not ask when: a session already had, or a beginner's tips."""
    said = " " + str((understood or {}).get("clean") or "").lower() + " "
    return any(phrase in said for phrase in _A_TIME_IS_ASKED)


def _short_cardio(memory, understood):
    """Twenty minutes a day, or honestly less when that is what the person has."""
    minutes = _minutes((understood or {}).get("text") or " ".join(
        (understood or {}).get("words") or ()))
    if minutes and minutes < 20:
        return (_minute_phrase(minutes).capitalize() + " minutes of brisk walking, stairs or "
                "cycling still counts, and it is doing it most days that builds the habit: start "
                "with the time you have and add five minutes a week until you are at about twenty.")
    if minutes and minutes >= 20:
        return (_minute_phrase(minutes).capitalize() + " minutes of brisk walking, cycling or "
                "stairs most days is plenty to build a base. Add one or two short sessions where "
                "you're a bit out of breath, and you get most of the benefit of longer workouts.")
    return ("Twenty minutes of brisk walking, cycling or stairs most days is plenty to build a "
            "base. Add one or two short sessions where you're a bit out of breath, and you get "
            "most of the benefit of longer workouts.")


def _stretch_when(memory, understood):
    """After, not before - unless the line named a session that warms up first.

    A line that already says "after" is asking to be told it is right, not for the comparison:
    "will i need to stretch after?" opened with "After, not before" as if it had asked both.
    """
    said = " " + str((understood or {}).get("clean") or "").lower() + " "
    opening = "Yes, after:"
    if " before " in said and " after " not in said:
        opening = "Not before, no - after:"
    elif " before " in said or " after " not in said:
        opening = "After, not before:"
    return (opening + " stretching pays off when the muscle is "
            "warm, and holding a cold one first does not prevent injury - it takes a little "
            "power off the session instead. What belongs before is the moving version: leg "
            "swings, lunges, skips, five minutes of easy jogging, which is what actually warms "
            "you up. The flexibility it keeps - reaching, bending, getting up off the floor - "
            "comes from half a minute a side, twice, a few times a week.")


# The topics this domain answers, as ids from bot/understanding/topics.py.
ANSWERS = ("fitness",)

# The row carries two answers and has to pick one, and "what does toned mean" was given the
# abs-are text because it names no how-to verb: the person asked what a word means, not what the
# muscle is. Only a line that names the muscle can have the abs text.
_ABS_NAMES = ("abs", "six pack", "six-pack", "sixpack", "abdominals", "washboard", "abdominal")


def _tone_or_abs(memory, understood):
    """What abs are, or how to get them to show: the same muscle, the same deficit."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    words = {str(one).lower() for one in ((understood or {}).get("words") or ())}
    names_the_muscle = any(name in text for name in _ABS_NAMES) or bool(words & {"abs", "abdominals"})
    if names_the_muscle and not re.search(
            r"\b(?:how|get|gain|build|start|fast|quick|want|can i|should i)\b", text):
        return ("Abs are the muscle across the front of your middle, and everyone has them - what "
                "shows is the layer of fat in front, so training makes them bigger and only a "
                "steady calorie deficit makes them visible. Sit-ups alone will not do it: two "
                "20-minute sessions a week of squats, press ups (from the knees is fine) and a row "
                "with a bag or band, plus walking, is the whole of what works.")
    return ("Toning is building a little muscle and losing a little fat, so it needs both strength "
            "work and a steady calorie deficit - there is no exercise that spot-reduces one area. "
            "Two 20-minute sessions a week of squats, press ups (from the knees is fine) and a row "
            "with a bag or band, plus walking, does the job without a gym.")


_EVERY_DAY_ASK = re.compile(
    r"\b(should|shall|can|could|is it|ok|okay|bad|wrong|fine|alright|all right|better|worse|"
    r"safe|harm|hurts?|need|rest|how often|how many|how much|how long|what|why|when|do i|"
    r"does it|too much|too often|overdo\w*|overtrain\w*)\b", re.I)


def _an_ask_about_training_every_day(understood):
    """True only for a line that asks about training every day.

    "i go to the gym every morning" is a routine told as news, and the chat acknowledges it; the
    same words with a question in them ("should i go to the gym every morning", "is it bad to
    work out every single day") are this row's question. The words alone cannot tell them apart,
    because the row is keyed on "every morning" and "gym".
    """
    clean = str((understood or {}).get("clean") or "")
    if _EVERY_DAY_ASK.search(clean):
        return True
    return bool((understood or {}).get("signals", {}).get("question_mark"))



# What to bring to a gym induction belongs to the induction row in sport.py, which answers the
# kit half and the first-month half of the same reading. This row keeps the first month, and it
# stands down when the line asks what to bring, take or wear, so one owner decides the split:
# "what should i bring to my first gym session" and "what should i take to a gym induction" were
# answered two different ways while both rows read the same words.
GYM_KIT_ASKS = ("what should i bring", "what do i bring", "what should i take", "what do i take",
                "what should i wear", "what do i wear", "what to bring", "what to wear",
                "shall i bring", "should i bring", "do i need to bring", "do i need",
                "what do i need", "what will i need", "need to bring", "need to take",
                "what kit", "kit list",
                # the bare verbs are what the review caught: an avoid word is read loosely, so
                # a lone "take" or "wear" stands this row down wherever the line says it
                "bring a", "bring my", "bring your", "bring to", "bring on", "bring in",
                "wear to", "wear for", "wear at", "wear on", "take to the gym",
                "take to a gym", "take with me", "taking with me")

ENTRIES = [
    entry("legs-after-run", (("legs", "thighs", "calves", "quads", "hamstrings", "glutes"),
                           ("dead", "heavy", "sore", "soreness", "ache", "aching", "tired",
                            "stiff", "after a run", "after that run", "next day", "two days")),
          "That ache a day or two after a new or harder run is normal and it eases faster if you "
          "keep moving: a walk or a very easy jog, plenty of water and a normal night's sleep do "
          "more than stretching. Go back to running once the soreness is gone in a normal walk, and "
          "add distance more slowly next time.",
          # it is the running answer: a dead-legged gym session is sport.py's sore-after-exercise,
          # and a calf or a knee that hurts is body.py's
          ask=(("run", "running", "ran", "jog", "jogging", "5k", "10k", "parkrun", "treadmill"),
               ),
          avoid=("cramp", "cramping", "numb", "numbness", "swollen", "swelling", "shin", "knee",
                 "injur", "blood", "dark urine")),

    entry("run-faster", (("get faster", "run faster", "speed up", "be quicker", "improve my pace",
                          "pb", "personal best", "pace"),
                         ("how", "run", "running", "should", "ways", "tips", "improve")),
          "Run most of your miles slow enough to hold a conversation, then add one faster session "
          "a week: six 2-minute efforts with 2 minutes of easy jogging between them. Progress "
          "comes from that weekly session plus the easy miles, not from chasing every run.",
          # "how do i speed up my laptop", "how do i speed up my wifi", "how do i speed up my
          # computer" and "how do i speed up my metabolism" all carry "speed up" and "how", so
          # the phrase alone let a running plan answer a device question. Anything with a machine
          # or a body measurement in it is that thing's own question.
          avoid=("knee", "knees", "pain", "hurt", "injur", "marathon", "10k", "5k",
                 "phone", "laptop", "computer", "pc", "mac", "windows", "tablet", "ipad",
                 "device", "wifi", "wi-fi", "internet", "broadband", "router", "network",
                 "download", "downloads", "upload", "browser", "app", "apps", "website",
                 "metabolism", "weight loss", "lose weight", "losing weight", "digestion",
                 "healing", "recovery", "charger", "battery", "engine")),

    entry("knees-when-running", (("knee", "knees", "shin", "shins", "ankle", "hip", "heel"),
                                 ("hurt", "hurts", "hurting", "pain", "sore", "aching",
                                  "when i run", "after a run", "running")),
          "Cut the distance and the speed for a week or two: most running knee, shin and ankle "
          "pain is too much, too soon, and hip and glute strength work fixes it. Ice after a run "
          "and run on softer ground, and see a physio if the pain is sharp, that leg swells up "
          "after every run, or it is still there in two weeks.",
          # a knee that aches is not a running knee: without one of these the warm question
          # ("my knee has been aching for a week") is the right reply.
          ask=("run", "running", "jog", "jogging", "ran", "5k", "10k", "marathon", "after a run",
               "when i run", "gym", "treadmill"),
          avoid=("baby", "toddler", "child", "doctor", "older", "years", "replacement")),

    # The body part the running rows were missing. "my back hurts after running" and "my back is
    # sore after running" were answered by the order of a gym session (that row keys `run` and
    # `after`), which has nothing to say to a back; with no running and no back in any key the
    # general back-pain card also lost the line. A back and a run in the same line is this row.
    entry("back-after-running",
          (("my back", "my backs", "lower back", "back pain", "backache", "back ache", "bad back",
            "sore back", "stiff back", "sciatica", "slipped disc"),
           ("running", "run", "runs", "jog", "jogging", "ran", "5k", "10k", "parkrun",
            "treadmill", "long run", "after a run", "after running", "when i run")),
          "A tired lower back after a run is usually the load rather than damage: cut your "
          "distance and pace for a fortnight, keep off the hills, and add glute and core work three "
          "times a week - bridges, bird-dogs and dead bugs. An ordinary ache is fine to run "
          "through; pain that shoots down your leg, or numbness, is a physio.",
          # the heat, the mattress and the desk are the general back-pain card's, and a back hurt
          # lifting or gardening is that card's too
          ask=("run", "running", "runs", "jog", "jogging", "ran", "5k", "10k", "parkrun",
               "treadmill", "after a run", "after running", "when i run", "with a bad back"),
          # the order-of-a-session row keys the same `run` and `after` words and has a bias, so
          # this row has to say that a back plus a run is its line
          bias=2),

    # "how do i get back into running after years off" was a shrug, and so was "how many hours a
    # week should i work out": both are the same beginner question from two directions.
    # "my mate says i need insoles" was answered with "Insoles - fair enough. What's stopped it
    # happening so far?", which is a reflect-and-ask where a person wanted to know whether they
    # need them at all. There was no card for it in any domain: the only rows that held the word
    # were the shoe-cleaning ones, and those want "smell" or "wash" in the line first.
    entry("insoles-help",
          (("insole", "insoles", "orthotic", "orthotics", "supportive insole", "shoe insert",
            "shoe inserts", "inserts for my shoes", "heel insert", "heel inserts",
            "heel cup", "heel cups", "arch support", "arch supports"),
           # The second group is the ask word, and every word in it is a word that no other row
           # of this domain is the only row to key. `_rank` gives a key word a point when only
           # one entry uses it, so a word another row owns alone is a point taken off that row:
           # "arch" and "plantar" are `plantar-fasciitis`'s and "feet" is `feet-after-run`'s, and
           # with "arch support", "flat feet" and "plantar" written here both rows fell under the
           # score a line needs - "plantar fasciitis" on its own went to the punt, and "my feet
           # hurt when i run" to the general training-load card. What makes this the insole row
           # is the insole word; the rest only says what sort of question it is, so a person who
           # types "insoles" and "flat feet" still lands here on the first group alone.
           ("need", "needs", "should i", "do i", "worth it", "worth", "help", "helps", "get",
            "buy", "buying", "my mate", "my friend", "my physio", "podiatrist", "podiatry",
            "physio", "hurt", "hurts", "pain", "knee", "knees", "heel", "best", "good",
            "better", "what", "which", "running", "walking")),
          "Insoles help a foot that rolls in or an arch that aches, and on their own they do little "
          "for knee pain - so it depends what is hurting. A running shop will watch you run for "
          "free and tell you whether you overpronate, and a cheap pair with a firm arch is a fair "
          "first try: if the pain is worst in your heel with the first steps in the morning that is "
          "plantar fasciitis, and a heel cup with a firmer arch usually eases it over a few weeks. "
          "Do the strength work too, because insoles support a foot rather than fix it - calf raises "
          "and picking a towel up with your toes, most days. See a podiatrist rather than guessing "
          "if you are diabetic, if the pain is sharp and one-sided, or if two months of the cheap "
          "ones has changed nothing.",
          # the shoe-care rows hold the same word and want the smell, the wash or the size; a
          # blister is its own answer, and so is a shoe that does not fit
          avoid=("smell", "smells", "smelly", "stink", "stinks", "wash", "washing", "clean",
                 "cleaning", "fresh", "squeak", "wet", "damp", "size", "sizing", "too tight",
                 "too small", "blister", "blisters", "rubbing", "lace", "laces", "socks",
                 "which shoes", "what shoes", "new shoes", "new trainers", "trainers for"),
          bias=2),

    entry("back-into-running", (("back into running", "running again", "run again", "havent run",
                                 "haven't run", "not run in", "years off",
                                 "get back into exercise", "back into exercise",
                                 "start running again"),
                                ("how", "start", "again", "should", "build", "years", "slowly")),
          "Start with run-walk: three minutes of easy running, two minutes of walking, five times, "
          "three days a week, and add a minute of running each week. Build up for six weeks before "
          "you add speed, keep every run slow enough to talk, and expect the first fortnight to "
          "feel harder than it looks.",
          # "how do i start running from nothing" is sport.py's start-running, so a line has to
          # say it is a return, not a first go; resting between sessions is sport.py's rest-days
          ask=("back", "again", "years", "havent", "haven't", "not run", "restart", "return"),
          avoid=("dog", "puppy", "car", "engine", "bus", "tap", "bath", "water", "rest",
                 "recovery")),

    entry("run-again-after-rest", (("how long should i rest", "how long before i can run",
                                    "when can i run again", "rest before running",
                                    "rest before i run", "how many days rest",
                                    "days off running"),
                                   ("run", "running", "again", "rest", "long", "should", "when",
                                    "days", "sore", "legs", "train")),
          "After a normal hard session, a day of easy walking or nothing at all is enough, and 48 "
          "hours is plenty before the same hard session again - soreness eases faster with gentle "
          "movement than with complete rest. Build back with two easy runs before your next hard "
          "one, and see a physio if pain is sharp, one-sided, or still there after two weeks.",
          ask=("run", "running", "jog", "rest", "days"),
          # a joint, a bird and a steak rest on a board, not on a recovery day, and the kitchen
          # has the minutes for them: "how long should i rest it" after a roast is not this
          avoid=("sport", "football", "match", "ill", "sick", "flu", "covid", "injury", "bone",
                 # a bone that is mending is not a recovery day: "when can i run again after a
                 # broken ankle" was told a day off after a hard session is enough
                 "broken", "broke", "fracture", "fractured", "cast", "plaster", "sprain",
                 "sprained", "operation", "surgery", "heal", "healing", "physio", "crutches",
                 "meat", "steak", "roast", "joint", "chicken", "turkey", "lamb", "beef", "pork",
                 "brisket", "ribs", "chops", "gammon", "carving", "carve", "foil")),

    entry("hours-a-week", (("how many hours a week", "hours a week", "how much exercise",
                            "how much should i exercise", "how much should i work out",
                            "minutes a week", "how often should i work out",
                            "how often should i exercise", "how often should i train",
                            "how many times a week should i train",
                            "how often should you train", "how often to train",
                            "how many days a week should i train",
                            # The same question in days: "how long should i exercise each day",
                            # "how much exercise a day" and "how long should you exercise" all
                            # reached no entry at all, so the guideline went to a search punt. The
                            # phrases are the daily shape of the weekly one, and the second group
                            # still has to name the exercise. They stop at the "how much" and "how
                            # long" forms on purpose: a line that says how many minutes it has
                            # ("i can only do 10 minutes of exercise a day") is a session question
                            # and stays with the circuit that is sized to the time.
                            "how long should i exercise", "how long should you exercise",
                            "how long should i work out", "how long should you work out",
                            "how long should i train", "how much exercise a day",
                            "how much exercise per day", "how much exercise each day",
                            "how long to exercise"),
                           # "week" alone was the tie-breaker that took a working week: "they are
                           # only giving me 20 hours a week now instead of 40" scored the same as
                           # work.py's hours-cut and won on registry order, so the person whose
                           # hours were cut was told to aim for 150 minutes of exercise. Every
                           # phrase in the first half already says the week, so the word is spare.
                           ("exercise", "work out", "workout", "exercise", "train", "gym",
                            "should")),
          # "how long should i exercise each day" asks for a day, and the week was the only
          # figure in the opening: the daily equivalent goes in the same sentence so the shape
          # asked for is the shape given.
          "Aim for about 150 minutes a week, which is around 20 minutes a day: anything that "
          "gets you warm and out of breath - five half-hours, or three twenty-minute sessions "
          "and some walking - plus two short strength sessions. Three or four sessions a week is "
          "plenty to start; consistency beats length.",
          # "how much exercise do they need" after a rescued greyhound is the dog's walk, not a
          # person's week, so the line has to be about you
          # "day" is in the guard because the daily shapes are said with no pronoun at all:
          # "how much exercise a day" has no "i" in it and was passing on every reason but this
          ask=("i", "me", "my", "we", "us", "myself", "should", "recommended", "guidelines",
               "day", "days"),
          avoid=("dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "greyhound", "pet",
                 "pets", "rabbit", "horse",
                 # "how many hours a week should i revise" is a study question that wears this
                 # entry's own shape ("how many hours a week" + "should"): a week of revision is
                 # not 150 minutes of anything that gets you out of breath
                 "revise", "revising", "revision", "study", "studying", "studies", "exam",
                 "exams", "gcse", "gcses", "a-level", "a level", "homework", "coursework",
                 "dissertation", "thesis",
                 # and a working week is not a training week: the employer words say whose
                 # week it is, so an hours-cut line reaches the contract answer instead
                 "boss", "job", "employer", "manager", "shifts", "rota", "contract",
                 # "minutes a day" is also how a habit is asked for, and a guitar or a book is
                 # not a training session: the practice words stand this entry down
                 "guitar", "piano", "violin", "drums", "instrument", "practise", "practice",
                 "practising", "practicing", "meditate", "meditation", "duolingo", "language",
                 "flashcards", "chess", "reading", "screen time",
                 "overtime", "paid", "cut", "cutting", "wage", "wages", "colleague",
                 "workplace")),

    # The plainest question in the domain punted: "what exercise should i do", "which exercise is
    # best", "what sort of exercise should i do", "best exercise for me" and "exercise ideas" all
    # reached nothing, because the exercise words alone are one signal (2) and every phrase in the
    # keys nearby is a contiguous run the line does not contain ("what should i" in "what exercise
    # should i do"). What kind to do is a question with an answer, and it is the answer a person
    # gets before they know enough to ask how much.
    entry("what-exercise-to-do",
          (("exercise", "exercises", "exercising", "work out", "workout", "training", "train"),
           # What the person does with it: the ask second, so the kind is always the subject and
           # the words here are the ones that ask for a kind. "sort of"/"kind of"/"type of" are
           # what people say instead of "which", and "ideas" is the same ask in one word.
           ("what exercise", "which exercise", "what exercises", "which exercises",
            "should i do", "should i be doing", "should i start", "can i do", "do you recommend",
            "would you recommend", "best", "ideas", "sort of", "kind of", "type of", "for me",
            "recommend", "beginner", "to do")),
          "Anything that gets you warm and out of breath counts, so pick the kind you will actually "
          "turn up for three times a week: brisk walking, cycling, swimming, stairs, dancing or a "
          "run-walk. Add two short strength sessions - squats or sit-to-stands, press-ups on the "
          "stairs or against the worktop, a row with a band or a loaded bag - because muscle is what "
          "keeps carrying and climbing easy. Three half-hours and two strength sessions a week is "
          "plenty to start, and adding five minutes or one rep a week beats changing everything at "
          "once.",
          # The kind is a general question only: a named place, a named part, an age, an injury, a
          # target time, a gym to join and a weight to lose all have their own answers, and the
          # generic card would be the wrong one for every one of them.
          avoid=("at home", "home", "living room", "bedroom", "flat", "garden", "no equipment",
                 "no gym", "without a gym", "gym membership", "join a gym", "joining a gym",
                 "membership", "classes", "class", "personal trainer", "pt",
                 "knee", "knees", "back pain", "bad back", "back is", "shoulder", "shoulders",
                 "hip", "hips", "ankle", "ankles", "wrist", "elbow", "neck", "injury", "injured",
                 "sore", "ache", "aches", "arthritis", "pregnant", "pregnancy", "after a break",
                 "havent", "haven't", "years off", "in my 20s", "in my 30s", "in my 40s",
                 "in my 50s", "in my 60s", "in my 70s", "older", "elderly", "at 40", "at 50",
                 "at 60", "at 70", "age",
                 "run", "running", "jog", "jogging", "5k", "10k", "marathon", "half marathon",
                 "swim", "swimming", "bike", "cycling", "yoga", "pilates", "weights", "lifting",
                 "press up", "press ups", "push up", "push ups", "sit up", "plank", "squat",
                 "squats", "lunge", "deadlift", "stretch", "stretches", "walking", "steps",
                 "lose weight", "weight loss", "fat", "belly", "tone", "toned", "muscle",
                 "muscles", "stronger", "strength", "cardio", "hiit", "how long", "how often",
                 "how much", "how many", "calories", "protein", "diet", "eat", "eating",
                 "dog", "dogs", "puppy", "cat", "horse",
                 # "what exercise should i do in the morning" asks *when*, and the timing card
                 # answered it: a question about the time of day is not a question about the kind.
                 "morning", "evening", "night", "lunchtime", "what time", "best time", "when",
                 "before breakfast", "after work", "empty stomach", "at the weekend",
                 "work out the", "work out my", "work out what", "work out which", "calculate",
                 "percentage", "average", "volume", "area", "paint", "bmi", "tax", "mortgage",
                 "pension", "guitar", "piano", "practice", "practise", "revise", "revision",
                 "study", "studying", "exam", "homework")),

    entry("cardio-or-weights", (("cardio or weights", "cardio and weights", "weights or cardio",
                                "first cardio", "lift or run", "run or lift", "weights first"),
                               ("should", "before", "after", "which", "better", "order", "do")),
          "Do the one that is the goal of the session first, then the other: lifting first if you "
          "are training strength, cardio first if you are training for a run. If you are after "
          "general fitness, three of each a week on separate days beats worrying about the order.",
          avoid=("dog", "cat")),

    entry("exercise-at-50", (("50", "fifty", "60", "sixty", "older", "middle aged", "my age"),
                             ("get fit", "fitness", "exercise", "start", "training", "strong",
                              "in shape")),
          "Start with what you can repeat three times a week: a 20 to 30 minute walk, two short "
          "strength sessions and some balance work, and add a little each week. Strength training "
          "twice a week matters more after 50 than a hard cardio session, because it is what keeps "
          "muscle and bone. Check with a GP first if you have a heart condition or you have not "
          "exercised in years.",
          # "50" is also an amount of money: "how do i start investing with 50 a month" was a
          # fitness plan because it had 50 and start in it. A line about money is not an age.
          # Only the investing words: a broad money word also stands this entry down for
          # "how do i get fit at 50 on a budget", which is still a fitness question.
          avoid=("baby", "toddler", "child", "birthday", "years ago", "wedding", "50 pounds",
                 "invest", "investing", "investment", "shares", "stock", "isa", "pension",
                 "savings plan")),

    entry("stay-motivated", (("stay motivated", "keep motivated", "motivation", "stick to it",
                              "keep exercising", "cant be bothered"),
                             ("exercise", "gym", "workout", "running", "how", "should", "keep")),
          # "clothes ready" and "train with someone" read as gym advice, and this entry is now
          # reached for any practice being kept up - the piano, a novel, a language - so the
          # wording has to fit all of them.
          "Make it small and scheduled: a set time, everything you need out and ready, and a "
          "session so short that skipping it feels sillier than doing it. Track the days you "
          "show up rather than the results, and do it with someone or book it like an "
          "appointment: habit carries you when motivation does not.",
          avoid=("work", "job", "boss", "study", "revision", "business", "diet")),

    entry("is-walking-enough", (("walking", "walk", "steps"), ("enough", "exercise", "count",
                                                               "benefit", "good")),
          "Walking counts, and brisk walking for 30 minutes most days does most of what a gentle "
          "gym session would for your heart and mood. Add two short strength sessions a week for "
          "muscle and bone, and pick up the pace until you are slightly out of breath.",
          # "how many steps a day is good" is the target, not this: a count question wants a
          # number, and this answer is about whether the walking counts at all. The count has
          # its own entry, so the shape of the count question stands this one down.
          avoid=("dog", "cat", "puppy", "baby", "toddler", "walk to work", "walk the dog",
                 "country walk", "hike", "route", "map",
                 # only the count shape: "i walk an hour a day is that enough" is this entry's
                 # own question, so "a day" on its own must not stand it down.
                 "how many", "per day", "step target")),
    entry("start-walking", (("walking", "walk", "walks", "a walk"),
                            ("start", "starting", "started", "begin", "beginner", "get into",
                             "fitness", "get fit", "lose weight", "build up")),
          "Start with three 10-minute walks in a week you can keep, then add five minutes to one "
          "of them each week until you are walking 30 minutes on five days - that is the 150 "
          "minutes a week the guidelines ask for. Walk fast enough that you can talk but not "
          "sing, wear the shoes you already have, and put each walk in your diary like an "
          "appointment so it happens on the days you do not feel like it.",
          # An adult's walking plan is not a baby's first steps: the milestones card keys the
          # same "walk" and "start" words and answered "how do i start walking for fitness"
          # with the ages a child walks at.
          #
          # The ask has to be a start or a fitness ask, because "how long is the wait at the walk
          # in centre", "does she need a walk every day" (a dog) and "i walk 10 minutes a day"
          # are none of them a plan, and a row keyed on "how long" or "every day" took all three.
          avoid=("baby", "babies", "toddler", "child", "children", "son", "daughter",
                 "months old", "first steps", "puppy", "dog", "kitten", "walk him", "walk her",
                 "enough", "how many", "step target", "walk to work", "country walk", "hike",
                 "route", "map", "boots", "shoes that fit", "walk in centre", "wait at")),

    entry("10k-training", (("10k", "10 k"), ("train", "training", "plan",
                                                                 "ready", "week",
                                                                 # "i want to do a 10k" is the
                                                                 # same ask as "how do i train for
                                                                 # a 10k", and it got the
                                                                 # shrink-the-goal reply instead
                                                                 "want", "wanted", "thinking of",
                                                                 "first", "race", "run a", "do a",
                                                                 "signed up", "goal", "aim")),
          "For a first 10k, build up to three runs a week and add about 10% to your longest run "
          "weekly, with the last long run a fortnight before race day. If you can run 5k "
          "comfortably now, eight to ten weeks is a realistic build.",
          # a distance question is race-distances, and a 5k or half-marathon plan is its own entry
          avoid=("how far", "far is", "distance", "miles", "km", "kilometres", "kilometers",
                 "how long is", "5k", "half marathon", "marathon")),
    # a bare "run" here answered "i want to start running but i have never run before" with race
    # morning breakfast, so the first group is the race itself
    entry("race-morning", (("race", "race day", "long run", "marathon", "half marathon",
                            "parkrun",
                            # a distance is a race by its name: "should i eat before a 5k" and
                            # "... before a triathlon" were answered by this row before the
                            # workout key was narrowed, and a punt is worse than either card.
                            # A bare "half" stays out: "can i eat half a banana before a run"
                            # is a snack question.
                            "5k", "10k", "triathlon", "ultra"),
                           ("eat", "morning", "breakfast", "before")),
          "Eat something plain you've had before, like porridge or toast with banana, two to three "
          "hours before the start, and sip water rather than drinking a lot at once. Nothing new on "
          "race day, and go out slower than feels natural.",
          avoid=("stomach", "sick", "diarrhoea", "the runs", "vomit", "monday", "tuesday")),
    entry("workout-time", (("workout", "work out", "exercise", "exercising", "cardio", "jog",
                            "jogging", "jogged",
                            # "gym" is the word people use for the session itself, and the time
                            # half is what keeps it off a bag, a contract and a pair of trainers.
                            "gym", "gyms",
                            # "train" is a train you get on, so it only carries the session as a
                            # phrase: "when should i train if i finish work at 7" was a fare.
                            "should i train", "when to train", "time to train",
                            "train in the morning", "train in the evening",
                            "training in the morning", "training in the evening",
                            # "run" and "running" on their own are any machine, tap or nose that is
                            # running, and next to the word "time" they took every one of them:
                            # "how do i stop my laptop fan running all the time" was answered with
                            # when to exercise. A phrase that can only mean going for a run carries
                            # the word instead, and it still reaches the plainest asks.
                            "a run", "to run", "i run", "go run", "running a 5k", "run a 5k",
                            "go running", "went running", "out running", "running club",
                            # "running in the morning" is a person and an hour with no ask in it,
                            # and the bare gerund is what a nose and a tap also are: the phrase
                            # carries the person. It was a chat ack on main.
                            "running in the morning", "running in the evening", "morning run",
                            "evening run"),
                           # a time of day has to be named: "which is better, rowing or running"
                           # carries "run" and "which" but it is not a question about when
                           ("morning", "evening", "afternoon", "at night", "in the morning",
                            "in the evening", "time of day", "best time", "time",
                            "before work", "after work", "first thing",
                            # The hour is often a fact about the day rather than a word for the
                            # morning: "i want to start the gym but i get out of work at 8, when
                            # should i go" was the job-search card (it keys "start" and "work")
                            # and "when should i go to the gym if i finish work late" was the
                            # late-period one. Naming the work and its finish time is a time of
                            # day for the session, so the job row and the period row lose it.
                            "when should i go", "what time should i go", "when to go",
                            "finish work", "finishes work", "finished work", "get out of work",
                            "out of work at", "leave work", "left work", "work until",
                            "work till", "working until", "working till", "work at 8",
                            "work at 9", "work at 7", "after my shift")),
          "Whatever time you'll actually stick to is the best time: morning suits consistency, "
          "evening suits people who feel stiffer early. If you go in the evening, finish at least "
          "two hours before bed so it doesn't keep you awake.",
          # a body that hurts, a night run and a shift rota are other questions. So is a
          # machine: "run" is the verb for a dishwasher, a washing machine and a dryer, and
          # "is it cheaper to run a dishwasher at night" was told when the person should go
          # jogging - the appliance names the run as a machine's, and the tariff row answers it.
          avoid=("hurt", "hurts", "pain", "dark", "safe", "safety", "alone", "shift",
                 "night shift", "park", "road", "breakfast",
                 "dishwasher", "washing machine", "washer", "tumble dryer", "dryer",
                 "dish", "oven", "kettle", "boiler", "vacuum", "hoover", "fridge",
                 "freezer", "engine", "car", "generator"),
          # "times" is "time" with an -s, so "how many times a week should i run" matched the one
          # time-of-day word in the key and was told morning suits consistency. A count of
          # sessions is `how-often-exercise`'s question - unless the line names an hour too, and
          # then the hour is what was asked.
          # "a count beside the hour" and "a time is asked" are both needed: the first keeps a
          # count of sessions off this row, the second keeps a session that has already happened
          # and a beginner's "any tips" on the row that answers them.
          guard=lambda understood: (_a_count_beside_the_hour(understood)
                                    and _a_time_is_asked(understood)),
          # A line that names the session and asks when loses the tie to whatever else it
          # mentions on the way: "i finish work at 8pm what time should i train" was a
          # productivity card and "when should i train if i finish work at 7" was a train fare.
          bias=2),
    # Where the cardio happens is a real choice with a real answer, and the two sides are named in
    # the line: without this the treadmill question was the composer's "can't call that one for
    # you", which is the one answer a person weighing it up cannot use.
    entry("treadmill-or-outside",
          (("treadmill", "treadmills", "tread mill", "running machine", "indoor", "indoors",
            "inside", "gym"),
           ("outside", "outdoors", "outdoor", "road", "park", "fresh air")),
          "Outside is a little harder at the same pace, because of the wind, the cambers and the "
          "turns, so set the treadmill to 1% incline if you want the two to match: either gets you "
          "fit and the one you will actually do wins. Go outside when you can for the daylight and "
          "the changing ground, and use the treadmill when it is dark, icy, or you want an exact "
          "pace for intervals.",
          # buying one, fixing one and the noise it makes through the floor are other questions,
          # and so is a knee or a shin that hurts whichever surface it is on
          avoid=("buy", "buying", "bought", "cost", "price", "cheap", "second hand",
                 "used", "fix", "fixed", "broken", "repair", "sell", "selling", "rent",
                 "delivery", "assemble", "noise", "noisy", "neighbour", "neighbor",
                 "downstairs", "warranty", "hurt", "hurts", "pain", "injury")),
    # HIIT and steady work are both asked as "which", and the session-order answer to that shape
    # was no answer at all: the two are not an order, they are a mix.
    entry("hiit-or-steady",
          (("hiit", "interval training", "intervals", "sprints", "sprint training"),
           ("steady", "continuous", "slow", "long run", "long slow", "jogging", "normal",
            "or", "vs", "versus", "better")),
          "Use both: two hard interval sessions a week and steady work the rest of it, because the "
          "total minutes matter more than the label. Intervals give the same fitness in less time "
          "but leave you flat for a day, so they suit someone already training; steady sessions "
          "are easier to recover from and build the base everything else sits on.", bias=1,
          ask=("better", "or", "vs", "versus", "which", "should", "what", "more", "good",
               "instead", "worth"),
          avoid=("app", "timer", "watch", "phone", "plan for")),
    # Cardio or weights is asked two ways, and they are different questions: the order inside one
    # session (sport.py's `cardio-or-weights-first`) and what to spend the week on to lose fat.
    # This one is the fat question, and it took the running-for-weight-loss answer, which never
    # mentions the weights half of it.
    entry("weights-or-cardio-for-fat",
          (("weights", "lifting", "strength training", "resistance training"),
           ("cardio", "cardio or weights", "weights or cardio")),
          "Both, and the food decides most of it: lift twice a week to keep the muscle you have "
          "while the fat comes off, and add cardio for the burn, so two of each beats either alone. "
          "If you can only keep one, keep the lifting, because muscle is what a diet takes first "
          "and it is what keeps you burning a little more all day.", bias=2,
          ask=("fat", "fat loss", "lose weight", "losing weight", "weight loss", "weight",
               "tone", "toning", "better", "should"),
          avoid=("first", "before", "after", "order", "same session", "same day")),
    # The reply is the circuit the person has time for, not a 20-minute one: see _short_workout.
    entry("short-workout", (("workout", "exercise", "training"), ("20", "minutes", "short", "quick",
                                                                 "home", "little time")),
          _short_workout, guard=_not_a_fare),
    entry("back-lifting",
          (("back", "lower back", "spine"),
           ("lift", "lifting", "heavy", "carry", "carrying", "boxes", "box", "move house",
            "moving house", "moving furniture", "sofa", "wardrobe", "bending", "gardening",
            "shovelling", "digging")),
          ("Bend at the hips and knees rather than the waist, keep the load touching you, and "
           "brace your stomach as you stand - a weight held out at arm's length puts five times "
           "the strain on your back. Feet shoulder-width, one foot slightly forward, and turn "
           "with your feet instead of twisting your spine. For a heavy move, take the drawers out "
           "first and use a sack trolley, and slide things on a blanket rather than lifting them."),
          # a back that has gone, or one that hurts, is body's question, and a gym lift is the
          # strength card's
          avoid=("went", "gone", "put my back out", "threw my back", "tweaked", "slipped",
                 "spasm", "hurts", "hurting", "pain", "painful", "ache", "aching", "sore",
                 # A back that is hurting now is the body's card, not the manual-handling
                 # one: "i helped my mate move house now my back is killing me" was answered
                 # with the bend-at-the-hips technique, which is advice for before the lift.
                 "killing me", "killing", "kills", "kill", "agony", "in agony",
                 "my back is gone", "my back has gone", "bad back", "sore back",
                 "squat", "deadlift", "bench", "weights", "1 rep", "1rm",
                 # a back that clicks or pops when it bends has not been asked about lifting:
                 # the joint-noise answer is the one that says what is happening (health.back-click)
                 "click", "clicks", "clicking", "clicked", "crack", "cracks", "cracking",
                 "cracked", "pop", "pops", "popping", "popped", "snap", "crunch"),
          # "my back fence is rotten on one side" lends its "back" to the next line, and the dog
          # digging under it was answered with this card's manual handling
          guard=the_back_is_a_body_part),
    entry("strength-start", (("weights", "lifting", "strength", "stronger"),
                             ("start", "beginner", "worth", "home", "minutes", "enough", "need",
                              "should", "have to", "twice")),
          "It's worth it even in 20 minutes: two sessions a week of squats, press-ups, lunges and a "
          "row with a band or dumbbell builds real strength. Muscle matters for everyday things like "
          "carrying shopping and climbing stairs, not just for looks.",
          # a protein target question is protein-how-much's, from sport.py
          avoid=("protein", "shakes", "whey", "grams",
                 # "should i use a weighted blanket" is a sleep question that shares the word
                 # "weight" with this row, and it was getting the two-sessions-a-week answer
                 "blanket", "blankets", "weighted blanket", "weighted duvet", "duvet", "quilt",
                 "sleep", "bed", "bedtime", "nap",
                 # a pet that needs to lose weight is the vet's plan, and "weights" is a loose
                 # form of the "weight" in that line: an animal is never this entry's question
                 "my cat", "my dog", "my puppy", "my kitten", "my rabbit", "my hamster",
                 "the cat", "the dog", "overweight", "vet")),
    # Grip is the one strength question people ask about by name, and it was a punt: nothing held
    # "how do i improve my grip strength". It belongs with the other starting-strength rows.
    entry("grip-strength", (("grip", "grip strength", "grip weaker", "hand strength",
                            "forearm strength", "forearms", "crushing grip", "pinch grip"),
                           ("strength", "stronger", "improve", "increase", "weak", "weaker",
                            "how", "better", "train")),
          "Grip comes from holding heavy things for time: hang from a bar for 20 to 30 seconds, "
          "three times, and carry a heavy bag or a pair of dumbbells in each hand for 30 metres. "
          "Add a thick towel round the bar or the handle now and then to make it harder without "
          "more weight. Do it twice a week on the end of a normal session, and give it a rest day "
          "after - the forearms recover slowly and a strained tendon takes weeks.",
          ask=("how", "what", "should", "improve", "better", "train"),
          avoid=("tennis racket", "golf grip", "putter", "cricket bat", "how to hold",
                 "steering wheel", "phone case", "tyre", "tire", "shoes", "boots")),
    entry("20-min-cardio", (("cardio", "fitness"), ("20", "minutes", "get fit", "improve",
                                                   "most", "out")),
          _short_cardio),
    # The before-or-after question and the is-it-worth-it question are two questions, and the
    # one row answered both with the flexibility card: "should i stretch before or after
    # running" was told what stretching is for, and "do i need to stretch" was answered as if
    # it had asked about timing. The verdict goes first, because it is the answer.
    entry("stretch-when", (("stretch", "stretching", "stretches"),
                           ("before", "after")),
          _stretch_when,
          avoid=("back", "neck", "shoulder", "desk", "sitting", "hip flexor", "posture"),
          # "should i stretch before or after exercise" is this entry, not the eat-before-or-after
          # one main added: a stretch question is about the session, not about food
          bias=3),
    # The number of seconds is the other half of the stretching question, and it had no row:
    # "how long should i hold a stretch" was a search hedge, and the before-or-after row
    # answered it with the session instead of the dose. Held separately, because the answer
    # is a count and the other row's is a verdict.
    entry("stretch-how-long", (("stretch", "stretching", "stretches", "stretched"),
                               ("how long", "long", "hold", "holds", "holding", "seconds",
                                "how many seconds", "how many", "count", "time")),
          "Twenty to thirty seconds, twice on each side, at the point of a gentle pull: the "
          "first twenty is when most of it gives, and holding for a minute more adds little. "
          "Breathe out into it and do not bounce, and do the long holds after the session when "
          "the muscle is warm - a cold stretch before sport takes a little power off it without "
          "stopping injuries.",
          # a calf or a back that is being stretched is its own entry, and a newborn, a pet or
          # a car are not this row's question at all
          avoid=("calf", "calves", "achilles", "back", "neck", "shoulder", "hip flexor",
                 "hamstring", "baby", "babies", "newborn", "toddler", "child", "dog", "cat",
                 "car", "engine", "sore", "pain", "hurts", "hurt")),
    # "do i need to stretch" and "does stretching prevent injury" were answered as if they had
    # asked about timing: the verdict ("not for injury, no") is a different answer from "after,
    # not before". The words that ask it are the worth words, so the row is keyed on those.
    entry("stretch-worth", (("stretch", "stretching", "stretches"),
                            ("worth", "needed", "need", "need to", "do i need", "why", "why should",
                             "benefit", "benefits", "point", "matter", "does it help", "help",
                             "prevent", "injury", "injuries", "important", "actually",
                             "necessary", "any point")),
          "Not for injury, no: strength work and building up slowly are what keep you off the "
          "physio's couch, and a stretch before sport takes a little power off it. What the "
          "flexibility is worth having is the reach - a high shelf, a shoe, getting up off the "
          "floor - and that goes quickly if you stop. Half a minute a side, twice, two or three "
          "times a week is enough to keep it.",
          avoid=("back", "neck", "shoulder", "desk", "sitting", "hip flexor", "posture",
                 "calf", "calves", "achilles", "hamstring", "hip", "hips", "knee", "thigh",
                 "baby", "babies", "newborn", "toddler", "child", "dog", "cat", "car",
                 "engine", "led", "screen", "budget", "pay", "money", "wage", "sentence",
                 "truth", "story", "film", "book"),
          bias=1),
    # How to get more of it had no row at all - three ways of asking for a routine were search
    # hedges - and the route is unglamorous: the same few holds, often.
    entry("flexibility-routine",
          (("flexibility", "flexible", "limber", "supple", "range of motion",
            "mobility", "stretching routine", "stretch routine", "stretching plan",
            "how often should i stretch", "how often do i need to stretch",
            "how often should i do stretching", "should i stretch every day",
            "what stretches", "which stretches", "stretches should i do",
            "stretches to do", "best stretches", "stretching every day"),
           ("how", "how often", "how many", "what", "which", "improve", "better", "increase",
            "more", "often", "routine", "every day", "daily", "times", "week", "get",
            "exercise", "exercises")),
          "Hold each one for 20 to 30 seconds, twice on each side, and do the set two or three "
          "times a week - daily works too but the gains come from doing it often, not from "
          "going deep. The five that matter for everyday life are the backs of the thighs, the "
          "hips and hip flexors, the calves, the chest and the upper back; warm up first with a "
          "few minutes of walking, and ease into the stretch rather than bouncing at the end of "
          "it.",
          # a calf or a shoulder that is being stretched, a pulled muscle and a stiff back are
          # each their own answer; a newborn, a pet and a car are not this row's question
          # "flexible" is two questions: a request to the manager for flexible working,
          # flexible hours or fewer days is `flexible-hours` in work.py, and "how do i ask for
          # flexible working" and "how do i request flexible working" were getting this card.
          avoid=("flexible working", "flexible hours", "flexi time", "flexitime", "job", "boss",
                 "manager", "employer", "employment", "hr", "contract", "rota", "office",
                 "hours at work", "working from home", "work from home", "wfh", "part time",
                 "part-time", "hybrid", "maternity", "paternity", "parental", "redundancy",
                 "union", "colleague", "salary", "holiday",
                 "calf", "calves", "achilles", "back", "neck", "shoulder", "hip flexor",
                 "hamstring", "sore", "pain", "hurts", "hurt", "pulled", "pull", "baby",
                 "babies", "newborn", "toddler", "child", "dog", "cat", "car", "engine",
                 "leather", "shoes", "budget",
                 # "flexible" is a word about a ticket, a fare and a working pattern too:
                 # "what is a flexible ticket" got this stretching routine, and the travel row
                 # that answers it was in the table all along.
                 "ticket", "tickets", "fare", "fares", "season ticket", "train", "trains",
                 "rail", "railway", "flight", "flights", "airline", "booking", "bookings",
                 "refund", "refundable", "date change", "change the date", "working hours",
                 "flexitime", "flexi time", "hours", "contract"),
          bias=1),
    # "should i foam roll before or after" was a bread roll: "should i" and "rolls" is the
    # cooking row's key, and the roller is a gym question that had no answer of its own.
    entry("foam-roll", (("foam roll", "foam roller", "foam rolling", "foam-roll",
                         "roller", "massage gun", "roll out", "rolling out", "self massage"),
                        ("before", "after", "tight", "sore", "worth", "help", "how", "use",
                         "should i", "do i", "best", "much", "often", "long", "legs")),
          "Either, and it does not matter much: a couple of minutes on a tight spot before you "
          "train loosens it enough to move better, and afterwards it feels good without doing "
          "much for soreness. What works is slow passes over the muscle, 30 to 60 seconds a "
          "spot, breathing out and stopping at a 6 or 7 out of 10 rather than gritting your "
          "teeth. It will not fix a tight muscle on its own - strength work and a bit of "
          "stretching do that - so treat it as the warm-up, not the cure.",
          avoid=("carpet", "paint", "bread", "pastry", "dough", "baking", "bake", "toilet roll",
                 "kitchen roll", "wallpaper", "sushi", "spring roll", "cinnamon"),
          bias=1),
    # "how do i warm up" was the search hedge: stretch-when says a warm-up beats a cold stretch but
    # never says what one is, and every sport and every gym session starts with the same question.
    entry("warm-up", (("warm up", "warmup", "warm-up", "warming up"),
                      ("how", "should i", "what", "need", "long", "do i", "before",
                       "good", "best", "quick", "proper")),
          "Five minutes, in two parts: first something easy that gets you slightly out of breath - "
          "a brisk walk, a slow jog, skipping, the exercise bike - then a few quick movements "
          "through the range you are about to use, like leg swings, arm circles, hip circles and "
          "ten bodyweight squats. Start the first set lighter than the rest. Save the long holds "
          "for afterwards: stretching cold muscles first does not prevent injury and takes a little "
          "power off the session.",
          # a stretch question is stretch-when's, and a child or a pet is another answer again
          avoid=("stretch", "stretching", "stretches", "baby", "toddler", "child", "dog",
                 "cat", "car", "engine", "oven", "food", "milk", "bottle",
                 # warming up a *meal* is the reheat table's, and "food" alone does not catch it:
                 # "how do i warm up leftovers" got the five minutes before exercise
                 "leftovers", "leftover", "rice", "pasta", "pizza", "soup", "stew", "curry",
                 "casserole", "chips", "scone", "scones", "bread", "pastry", "croissant",
                 "baguette", "potatoes", "roast potatoes", "takeaway",
                 # a warm-up for a named session is the sport's own entry (sport.py has the
                 # match and the run, and the gym answer knows the sets): "how do i warm up
                 # before running" was told the generic five minutes instead of the run's
                 "before the gym", "before running", "before a run", "before lifting",
                 "before weights", "before leg day", "before a match", "before football",
                 "before a swim", "before cycling",
                 # a house warms up too, and so does a pan: the shared list is in lookup.py
                 ) + A_HOUSE_WARMING_UP),

    # --- the questions that come with a first month of exercise -------------
    # "protein" is not a key here: a protein *target* question is protein-how-much's, and the
    # eat-around-it answer is only about timing
    entry("eat-less-or-train-more", (("eat less", "eating less", "train more", "train harder",
                                      "eat more", "exercise more", "more cardio"),
                                     ("or", "should i", "weight", "lose", "better", "both")),
          "For the scales, food moves more than exercise does: a hard session burns maybe 300 to "
          "500 calories, and an extra biscuit and a glass of wine take that back. Do both, but take "
          "the food loss slowly - a smaller portion of the same meals and fewer liquid calories - "
          "and add two brisk sessions a week rather than cutting hard and training hard at once.",
          # eating more *to build muscle* is a protein and calories question, not a weight one
          # a goal clause in front of a food question is still a food question: "i'm trying to
          # eat more fibre, what should i have" names a nutrient and asks what to eat, and the
          # fibre row answers it. Without this the "should i" in "what should i have" scored here
          # and the person got the calories-in-calories-out card instead of the food.
          avoid=("dog", "dogs", "baby", "child", "puppy", "cat", "muscle", "muscles", "build",
                 "bulk", "protein", "gaining", "gain weight", "put on",
                 "what should i have", "what should i eat", "what can i eat", "what do i eat",
                 "what to eat", "what should i cook", "meal ideas", "meal idea",
                 "fibre", "fiber", "salt", "sugar", "calcium", "iron", "vitamins")),
    # The second key used to be "before"/"after" with the training words, so every line that
    # said when it ate matched: "is it ok to eat 2 hours before bed" and "is it ok to eat after
    # 8pm on a diet" were answered "Eat something with carbs an hour or two before if you can,
    # and protein within a couple of hours after". A workout is the whole of the question here,
    # so the line has to name one and "before" on its own is not enough.
    entry("eat-around-workout", (("eat", "food", "breakfast", "carbs", "meal", "snack"),
                                 ("workout", "workouts", "run", "a run", "runs", "running",
                                  "gym", "training", "exercise", "exercising", "session",
                                  "sessions", "sport", "football", "rugby", "netball", "hockey",
                                  "swim", "swimming", "cycle", "cycling", "bike ride",
                                  "lift", "lifting", "weights", "weight training", "cardio",
                                  # a race has its own row (`race-morning`), and putting its
                                  # words here took "what should i eat before parkrun" away from
                                  # it, so the words that name one are deliberately absent
                                  "match", "climbing", "boxing", "hiit",
                                  # a class or a match can be the whole sport: "should i eat
                                  # before yoga" and "... before a walk" are the same question
                                  # as "... before a run", and both were a punt or a pets answer
                                  # once the old before/after key was narrowed.
                                  "yoga", "pilates", "spin", "dance", "dancing", "hike",
                                  "hiking", "walk", "walking", "row", "rowing", "tennis",
                                  "cricket", "ski", "skiing", "dance class", "gym session")),
          "Eat something with carbs an hour or two before if you can, and protein within a couple "
          "of hours after - a banana and yoghurt, or toast and eggs, is plenty. The order matters "
          "far less than the total: getting enough food and sleep is what makes the training work.",
          # a restaurant, a takeaway and a dinner plan are not training
          avoid=("salad", "slimy", "lettuce", "leaves", "vegetables", "restaurant", "takeaway",
                 # "do i need to eat before ibuprofen" is a tablet question, not food timing
                 "ibuprofen", "paracetamol", "aspirin", "naproxen", "painkiller", "painkillers",
                 "medicine", "medicines", "medication", "tablet", "tablets", "antibiotic",
                 "antibiotics", "steroid", "steroids",
                 "dinner tonight", "recipe", "cook", "roast", "bake",
                 # "can i eat prawns the day after" and "can i eat rice the day after" are food
                 # keeping questions, and "eat" plus "after" is the whole key of this row: the
                 # person asking whether yesterday's dinner is safe got carb timing for a run.
                 # a snack on a train is a journey, not training
                 "on a train", "on the train", "train journey", "train ride", "train trip",
                 "on a coach", "on the coach", "coach trip", "long journey", "long trip",
                 "the day after", "day after", "the next day", "next day", "day later",
                 "a day later", "still ok", "still good", "still safe", "gone off", "goes off",
                 "reheat", "reheating", "leftover",
                 # "should i eat less or train more" is a weight question, not food timing
                 "eat less", "eating less", "train more", "train harder", "eat more",
                 "table", "menu", "leftovers", "fridge", "shelf life", "stomach", "tummy",
                 "cramp", "cramps", "sick", "nausea", "diarrhoea", "heartburn", "after eating",
                 # bloating after meals is a gut question, not what to eat round a workout
                 "wind", "bloated", "bloating", "gas", "after meals", "after dinner",
                 "after lunch",
                 # "is frozen food safe after a year": `food` and `after` are this entry's key,
                 # but the question is how long it keeps, not what to eat round training.
                 "frozen", "freezer", "freeze", "defrost", "thaw", "use by", "best before",
                 "still safe", "safe after", "safe to eat", "gone off", "expired",
                 "out of date",
                 # An eating verb with a clock on it is a question about eating late, not about
                 # food round a session: "does eating after 8pm make you gain weight" took
                 # this card's "eat" and "after" and got carbohydrate timing for a run. The
                 # workout word still wins where it is said ("what should i eat after a run at
                 # 8pm" carries none of these phrases).
                 "eat after 8pm", "eating after 8pm", "eat after 9pm", "eating after 9pm",
                 "eat after 10pm", "eating after 10pm", "eat after 11pm", "eating after 11pm",
                 "ate after 8pm", "ate after 9pm", "ate after 10pm",
                 "eat late", "eats late", "eating late", "ate late",
                 "late at night", "too late to eat", "before bed", "midnight")),
    entry("feet-after-run", (("feet", "foot", "blister", "blisters", "toes", "toenail"),
                             ("run", "running", "jog", "aching", "hurt", "sore", "after",
                              "week")),
          "Most foot pain after running is shoes or mileage: check the shoes are not worn through "
          "at the heel, build distance slowly and let blisters drain and cover rather than pop. "
          "Pain under the heel that is worst first thing in the morning is plantar fasciitis, and "
          "a podiatrist or physio sorts it faster than rest alone.",
          # a foot that aches in the cold is weather ache (health.joints-in-cold-weather), not
          # shoes and mileage: "my feet ache in the cold" was getting the running answer
          # Someone rushed off their feet is busy, not injured: `feet` and `run` are both in
          # this entry's key, so the idiom has to be named here or a busy week gets a running
          # injury. "on my feet all day" stays out on purpose - that one is aching feet.
          # ...and a toenail that has grown into the skin is not shoes and mileage either:
          # "my toenail is ingrowing and sore" was answered with this card
          avoid=("dog", "cat", "puppy", "baby", "socks drawer", "in the cold", "when its cold",
                 "when it's cold", "cold weather", "in the rain", "when it rains", "in winter",
                 "damp weather", "when the weather",
                 "off my feet", "off our feet", "off your feet", "off her feet", "off his feet",
                 "run ragged", "running ragged", "ran ragged",
                 "dead on my feet", "dead on her feet", "dead on his feet",
                 "back on my feet", "back on her feet", "back on his feet",
                 "find my feet", "finding my feet", "found my feet",
                 "two left feet", "swept me off my feet", "cold feet",
                 # a diabetic foot is the diabetic foot answer, not shoes and mileage:
                 # "how do i look after my feet with diabetes" was getting this running reply
                 "diabetic", "diabetes", "neuropathy", "foot ulcer", "ulcer on my foot",
                 "ingrown", "ingrowing", "in growing", "growing into", "fungus", "fungal",
                 "yellow", "crumbly", "clippers", "nail scissors",
                 # swollen feet in a pregnancy are not shoes and mileage (body.py owns them)
                 "pregnant", "pregnancy", "weeks pregnant", "trimester")),
    # "what is plantar fasciitis" was "I don't know enough to answer that honestly" while the
    # same pain worded as a symptom got a good answer: the sore-feet row keys a foot and a run,
    # and the name of the thing had nothing. A named injury is a plain request to explain it, so
    # this one explains itself back and carries the two things that actually fix it.
    entry("plantar-fasciitis",
          (("plantar fasciitis", "plantar fascia", "heel pain", "pain in my heel", "sore heel",
            "pain under my heel", "arch pain", "pain in my arch", "foot pain in the morning"),
           ("what", "why", "how", "help", "fix", "treat", "cure", "get rid", "should i",
            "morning", "walking", "run", "running", "standing", "better")),
          ("Plantar fasciitis is the thick band under the arch pulling where it attaches to the "
           "heel bone, and the signature is the first steps out of bed hurting most and easing as "
           "you walk. It is not a spur or a bone problem, so the fix is load and stretch rather "
           "than rest: roll a frozen bottle under the arch for ten minutes, stretch the calf "
           "against a wall and off a step twice a day, and do heel raises on the edge of a stair "
           "every other day. Buy shoes with a firmer heel and a bit of support rather than flat "
           "plimsolls, drop the running mileage for a few weeks, and see a physio if it is no "
           "better in six weeks or it hurts at rest."),
          bias=1,
          avoid=("diabetic", "diabetes", "pregnant", "pregnancy", "child", "baby", "dog", "cat",
                 "horse", "plantar wart", "verruca", "wart")),
    entry("swim-start", (("swim", "swimming", "pool", "laps"),
                         ("start", "beginner", "beginners", "learn", "fitness", "how do i",
                          "get into", "improve",
                          # the same request from someone going back: "i stopped swimming years
                          # ago" and "i want to swim again" reached nothing at all
                          "again", "stopped", "back into", "get back", "returning",
                          "used to swim", "years ago", "years since", "out of practice",
                          # a duration or a distance is the beginner's question too: "how long
                          # should i swim for", "how many lengths should i swim"
                          "how long", "how many lengths", "how far")),
          "Start with 20 minutes of lengths and break each one into two lengths of front crawl "
          "with a rest at the wall - technique first, distance later. A one-to-one lesson or an "
          "adult improver class is the fastest way to stop getting out of breath, and two swims a "
          "week is plenty at the start.",
          # an adult who cannot swim wants lessons, and sport.py has that answer
          avoid=("sea", "beach", "holiday", "hotel", "spain", "pool table", "paddling",
                 # a cue ball in a pub is not a swimming pool, and neither is billiards or
                 # snooker: "how do i get better at pool" was this starter plan
                 "billiards", "pool cue", "cue ball", "eight ball", "8 ball", "snooker",
                 # the bare word is how people say the pub game, and the starter plan won the tie
                 # on "pool": "how do i get better at pool" was the lengths plan (@tidy-aspen)
                 "at pool", "playing pool", "play pool", "game of pool", "pub pool",
                 "pool hall", "get good at pool", "good at pool", "pool player",
                 # a mile in the pool is a number, not a way to start swimming
                 "how many laps", "how many lengths is a mile", "lengths in a mile",
                 "mile in a pool", "a mile in the pool", "a mile in the pool",
                 "adult", "learn to swim", "cant swim", "can't swim", "cannot swim",
                 "frightened", "scared", "panic", "lessons", "lesson",
                 # a child learning is neither an adult class nor a get-fit plan: with the
                 # adult row fenced off, "how do i teach my child to swim" landed here and was
                 # told to do 20 minutes of lengths
                 "child", "children", "kid", "kids", "son", "daughter", "toddler", "baby",
                 "my boy", "my girl", "nursery",
                 # a body, not a return: "is swimming good for my back"
                 "my back", "bad back", "sore back", "back pain", "good for my back",
                 "shoulder", "shoulders", "knee", "knees", "hurt", "hurts", "ache",
                 "aching",
                 # an hour after eating is the cramp rule's question, not a training plan
                 "after eating", "after a meal", "after lunch", "after dinner", "wait",
                 "waiting", "cramp", "cramps", "before swimming",
                 # a baby or a toddler in the water is a how-long-and-how-warm question, not an
                 # adult training plan
                 "baby", "babies", "newborn", "infant", "toddler", "month old", "months old",
                 # a pool being emptied is a job with a hose, not a training plan: "how do i
                 # empty a swimming pool" was told to start with twenty minutes of lengths,
                 # because "pool" is this row's subject and "how do i" is one of its asks
                 "empty", "emptying", "emptied", "drain", "draining", "drained",
                 "get the water out", "water out", "pump out", "pump it out", "siphon",
                 "syphon", "winterise", "winterize", "winterising", "cover", "covered")),
    entry("press-ups", (("press up", "press ups", "pressup", "pressups", "push up", "push ups",
                         "pull up", "pull ups", "chin up", "chin ups"),
                        ("cant", "can't", "cannot", "one", "start", "build", "how", "zero",
                         "properly", "form", "technique", "correctly",
                         # "how do i get better at push ups" and "how many push ups should i do"
                         # are the same move asked two ways, and both went to the whole-body
                         # plan, which never says how to get from one press-up to ten.
                         "how many", "a day", "a week", "better", "get better", "improve",
                         "stronger", "reps", "sets", "should i do", "work up to")),
          _the_rep_plan,
          bias=1),
    # A sit up, a plank, a lunge and a deadlift are the four moves people ask how to do in words,
    # and every one of them was a shrug or the sitting-at-a-desk answer. The move is the subject
    # and the form words are the ask, the same shape as `squat-form` and `press-ups`.
    entry("sit-up-form",
          (("sit up", "sit ups", "situp", "situps", "crunch", "crunches", "ab exercises",
            "ab workout", "core exercises"),
           ("form", "proper", "properly", "technique", "correctly", "how do i do", "how to do",
            "how many", "should i do", "sets", "reps", "neck", "hurts my neck", "back",
            "without hurting")),
          "Hands crossed on your chest or resting at your temples, never laced behind your head "
          "and never pulling: pull with your neck and you get a sore neck, not a stronger middle. "
          "Press your lower back into the floor, curl your ribs towards your hips and lift only "
          "until the shoulder blades clear the floor, then lower slowly. Ten slow ones beat "
          "thirty fast: two or three sets of ten, twice a week, is plenty. If a sit up hurts your "
          "back, a dead bug or a plank trains the same muscle without it.",
          bias=1,
          # the desk and the sleep rows key "sitting" and "back": a chair is not this move
          avoid=("desk", "chair", "posture", "office", "screen", "sleep", "bed", "sofa",
                 "stand up", "stand", "sit out", "sit down", "left out",
                 # "should i do planks or crunches" is the comparison row's, not the form's
                 "better than", "rather than", "instead of", "versus", "vs", "or a plank",
                 "or planks", "or crunches", "or sit ups", "which is better", "which one")),
    entry("plank-form",
          (("plank", "planks", "planking"),
           ("form", "proper", "properly", "technique", "correctly", "how do i do", "how to do",
            "hips", "shoulders", "sagging", "straight line", "elbows")),
          "Elbows under your shoulders with the forearms flat, feet hip-width: squeeze your glutes "
          "and tuck your ribs down so the hips neither sag nor poke up - one straight line from "
          "ear to heel - and keep breathing. Twenty to thirty seconds done well beats two minutes "
          "with a sagging back; add ten seconds a week and stop the set when the hips drop. A low "
          "back that aches during a plank is usually the sag, not a weak back.",
          bias=1,
          # how long to hold one is the duration row's question, and it already answers it well
          avoid=("how long", "how many", "seconds", "minutes", "hold a plank", "hold the plank",
                 "rounds")),
    # A comparison is the shape a new move row most easily unshadows: "is a plank better than a
    # sit up" named two of the rows above and no other subject, so the sitting row's stand-down
    # left it to the plane-seat card (that keys `sit` and `better`). The two moves are the
    # subject here and the comparing words are the ask, and the answer is short.
    entry("core-exercise-choice",
          (("plank", "planks", "planking", "sit up", "sit ups", "situps", "crunch", "crunches",
            "hollow hold", "core exercise", "core exercises"),
           ("better", "best", "rather", "instead", "versus", "vs", "which one", "either",
            "or", "compare", "worth it", "swap")),
          "Both, and they do different jobs: a sit up moves the trunk through a range, so it works "
          "the front of the core and the hip flexors, and a plank holds the trunk still, which is "
          "the job a back has to do all day. If you have time for one, take the plank - it is the "
          "one that carries over to lifting and sitting, and it needs no movement to get wrong - "
          "and add crunches after it if you want the curl. Two or three sets of a plank you can "
          "hold with a straight back beats a hundred sit ups.",
          bias=2,
          avoid=("how do i do", "form", "technique", "properly", "how long", "how many",
                 "seconds", "minutes")),
    entry("lunge-form",
          (("lunge", "lunges", "walking lunge", "split squat", "split squats"),
           ("form", "proper", "properly", "technique", "correctly", "how do i do", "how to do",
            "knee", "knees", "hurt", "hurts")),
          "Step forward far enough that both knees bend to about a right angle: the front knee "
          "tracks over the middle of the foot rather than caving inwards, the back knee dips "
          "towards the floor without banging it, and the chest stays upright. Push through the "
          "front heel to stand up. If the front knee is what complains, take a longer step and a "
          "smaller dip; a wobble means the step was too short.",
          bias=1),
    entry("deadlift-form",
          (("deadlift", "deadlifts", "barbell row", "how do i lift safely", "heavy box", "heavy boxes", "lift a heavy", "lifting heavy",
            "carry a heavy", "carrying a heavy", "lift something heavy", "heavy lifting"),
           ("form", "proper", "properly", "technique", "correctly", "how do i do", "how to do",
            "how do i lift", "how to lift", "how do i carry", "back", "safely", "start",
            "beginner")),
          "Feet hip-width with the weight over the middle of your feet, then bend at the hips "
          "and knees rather than the back: take the bar (or the box, close in against your "
          "shins and no further out) with straight arms, chest up, shoulders slightly in front "
          "of it, and set your back flat before you pull. Push the floor away with your legs, "
          "keep the weight dragging up your shins, and stand tall without leaning back; lower "
          "it by sending the hips back first. A weight you can lift with a flat back is the "
          "weight to use - a rounded back is the whole risk.",
          bias=1,
          # a bad back is the pain question, and a parcel is a lifting-and-shifting one
          # a sofa or a mattress moved up a stairwell is the moving-house row's question
          avoid=("parcel", "parcels", "sofa", "furniture", "moving house", "move house",
                 "mattress", "wardrobe", "upstairs", "shopping bags", "bad back", "back pain",
                 "injury",
                 # "how do i lift weights safely" is the whole-body programme's line, not one lift
                 "lift weights", "lifting weights", "weights at home", "at home", "home gym",
                 "dumbbells", "kettlebell")),
    entry("doms-two-days",
          (("muscles", "muscle", "legs", "arms", "thighs", "body", "everything"),
           # "sore", "aching" and "stiff" are sport.py's sore-after-exercise words, and it answers
           # those lines already: this entry is only the "hurt" shapes it misses
           ("hurt", "hurts", "hurting", "painful", "aching when"),
           ("two days", "three days", "day after", "days after", "next day", "days later",
            "second day", "a couple of days")),
          "That ache a day or two after new or harder exercise is delayed-onset muscle soreness, "
          "not damage: it is the muscle repairing itself and it peaks around 48 hours and eases "
          "within four days. Keep moving gently, drink water and sleep, and start lighter next "
          "time; see someone if one spot is sharp, swollen or bruised, or if your urine goes "
          "cola-coloured.",
          ask=(("hurt", "hurts", "hurting", "painful"),),
          # an injury is not soreness: a pulled, torn or swollen muscle is body.py's line, and a
          # line that names no day at all is a knock rather than the ache two days after one
          guard=_the_ache_has_its_day,
          avoid=("pulled", "pull", "tear", "torn", "sharp", "swollen", "swelling", "red", "hot",
                 "bruise", "bruised", "injury", "injured", "snap", "pop", "numb", "cramp",
                 "chest", "breath", "dog", "cat")),
    entry("stretch-calves", (("calf", "calves", "achilles"),
                             ("stretch", "stretches", "stretching", "tight", "sore", "ache",
                              "aching", "stiff", "warm up", "warmup")),
          "Stand with the ball of the foot on a step and let the heel drop slowly for 30 seconds, "
          "three times each side, twice a day; keep the knee straight for the calf and bend it for "
          "the soleus behind it. Tight calves that come with sharp heel pain or a sudden snap in "
          "the back of the leg need looking at, not stretching.",
          # a calf that is swollen or hot after stretching is the clot question body.py asks, not
          # the instruction that may have caused it
          # a calf that hurts when you run is the pulled-muscle answer's line, and a swollen or
          # hot one is the clot question: the stretch is only for a tight, stiff calf
          avoid=("cow", "cows", "farm", "veal", "milk", "swollen", "swelling", "swelled", "hot",
                 "lump", "bruise", "red", "run", "running", "ran", "jog", "jogging", "pulled",
                 "pull", "tear", "torn", "strain", "snap", "sharp", "cramp", "hurts when")),
    entry("swim-shoulder", (("swim", "swimming", "crawl", "laps"),
                            ("shoulder", "shoulders", "hurts", "ache", "aching", "sore", "pain",
                             "stroke")),
          "Swimming shoulder is nearly always too much front crawl too soon: halve the distance for "
          "two weeks, keep the pull long and relaxed rather than yanking each stroke, and add ten "
          "minutes to a swim instead of a whole extra session. Sharp pain, or an arm that will not "
          "lift, is a physio's job.",
          avoid=("gene", "pool table", "pool cue", "pool party", "carpool", "closed", "voucher",
                 "swimming pool at")),
    # "how do i get abs" and "how do i get a six pack" were the honest hedge: the same answer as
    # toning covers them, since visible abs are the fat coming off rather than an exercise, so
    # they key the same row instead of a row of their own. "what are abs" is the same row read
    # the other way round, and it leads with the muscle rather than the deficit.
    entry("tone-up", (("tone", "toned", "tone up", "toning", "firm up", "abs", "six pack",
                       "six-pack", "abdominals", "washboard"),
                      ("without", "gym", "how", "arms", "tummy", "stomach", "legs", "weights",
                       # "i want to get toned" names no ask at all, and the question is common
                       "want", "get", "become", "look", "body",
                       # "what are abs" asks what the muscle is, and the row opened with the
                       # deficit for it; the phrases, because "what" alone is in every line
                       "what are", "what is a", "what is an", "whats a", "what's a", "mean")),
          _tone_or_abs,
          avoid=("phone", "ringtone", "skin", "paint", "colour", "hair", "voice", "tone of",
                 "tone deaf", "deaf", "hearing", "pitch",
                 # a six pack is a beer as often as it is a stomach, and "what is a six pack of
                 # beer" was answered "Abs are the muscle across the front of your middle": a
                 # confident wrong answer where main at least hedged. The cans take it back.
                 "beer", "beers", "lager", "ale", "stout", "cider", "cans", "can of",
                 "bottle", "bottles", "coke", "coca cola", "pepsi", "pop", "yogurt", "yoghurt",
                 "drink", "drinks", "supermarket", "shop", "cost", "price", "how much")),
    entry("plank", (("plank",), ("how long", "time", "seconds", "minutes", "good")),
          "Thirty to sixty seconds is plenty: a plank you can hold with a straight back beats two "
          "minutes with a sagging hip. Three rounds with a minute's rest between, and squeeze "
          "your glutes so your lower back doesn't take the load."),
    # Yoga and pilates are the two practices people choose between and ask what they are worth,
    # and both were a search punt. The comparison names both in the order either way round, so
    # "whats better for that, pilates or yoga" is answered from a follow-up as well.
    entry("yoga-or-pilates",
          (("pilates or yoga", "yoga or pilates", "yoga vs pilates", "pilates vs yoga",
            "yoga versus pilates", "pilates versus yoga", "yoga and pilates",
            "which is better yoga", "which is better pilates"),
           ("better", "best", "choose", "which", "worth", "should", "start", "difference")),
          "Pilates is the better pick for a weak or sore back and a strong middle - it is slow, "
          "controlled work on the deep stomach and hip muscles - and yoga is the better pick for "
          "flexibility, balance and winding down. Both are low-impact and fine to start from "
          "nothing, so if the choice is still even, take the one whose teacher you liked.",
          # a bad back, a pregnancy and a knee are the health rows' questions
          avoid=("back pain", "bad back", "slipped", "sciatica", "pregnan", "knee", "injury",
                 "injured", "arthritis", "surgery", "operation")),
    entry("yoga-good-for-you",
          (("yoga", "pilates"),
           ("good for you", "good for me", "benefits", "benefit", "worth it", "worth doing",
            "count as exercise", "counts as exercise", "good exercise", "what does it do",
            "why do it")),
          "Yes: it builds flexibility and balance and strengthens the muscles that hold you up, "
          "and it counts as exercise, though the heart and lungs get less from it than from a "
          "brisk walk. Two or three sessions a week is where the change shows, and a weekly class "
          "plus ten minutes at home most days is the usual way people keep it up.",
          # a part that hurts, a pregnancy or an injury is a health question, not a general one
          avoid=("back pain", "bad back", "sciatica", "pregnan", "knee", "injury", "injured",
                 "arthritis", "surgery", "operation", "sore", "hurt", "pain", "lose weight")),
    # joining a gym is the opposite of cancelling one: "im thinking of joining a gym" and
    # "i joined a gym last week" both got the cancellation steps, because the bare "join" was a
    # trigger on that row. A joining line wants what to do there, which is this answer.
    entry("gym-first-time",
          (("gym",),
           ("first", "start", "beginner", "begin", "nervous",
            "join", "joining", "joined", "sign up", "signing up", "signed up", "new member",
            "membership starts", "thinking of joining", "want to join")),
          "Learn five movements and ignore everything else for a month: squat, hinge (deadlift), "
          "push, pull and carry. Two or three sessions a week, three sets of 8–12, adding a little "
          "weight each time. Book the induction: a trainer checks your form once and shows you "
          "the machines, and it's usually free.",
          avoid=("sore", "soreness", "aching", "ache", "push through", "hurts", "pain",
                 # what to eat around training is health's, and a first-session tip would
                 # lose the subject of the next question ("and do i need shakes for that")
                 "protein", "shakes", "shake", "macros", "calories", "carbs", "diet",
                 "weight loss", "lose weight", "eat", "eating", "food",
                 # a joining line that is really a decision is not a first session: "is joining a
                 # gym a waste of money" wants shopping.py's cost-per-visit maths, and "should i
                 # join a gym" and "which gym should i join" want the induction answer. Without
                 # this the bare "join"/"joining" words below take all three, so the money
                 # question was answered with a workout.
                 "worth it", "worth joining", "worth the money", "waste of money", "money",
                 "cost", "costs", "cheap", "expensive", "price",
                 "should i join", "which gym") + GYM_KIT_ASKS,
          # sport.py has a first-session entry too; this is the one main's test pins, so it
          # keeps the "first time and nervous" line
          bias=1),
    entry("fit-at-home",
          (("get fit", "get fitter", "fitter", "exercise", "exercising", "work out", "workout",
            "training at home", "keep fit", "in shape", "out of shape", "start exercising"),
           ("home", "at home", "in the house", "living room", "my flat", "bedroom", "garden",
            "no equipment", "without equipment", "no gym", "without a gym", "small space",
            "dont want a gym", "don't want a gym",
            # "how do i get fit" on its own names no place and no plan, and it was a shrug: the
            # answer below is the one that needs no equipment, so the bare ask belongs here too.
            # The joins that make it another question (a gym, a run, a marathon, a body part, an
            # age) stay in the avoid list under this one.
            "how do i", "how to", "what should i", "want to", "need to",
            "wanna", "help", "tips", "advice", "plan", "beginner", "start")),
          "Three half-hour sessions a week is enough to feel different in a month, and you need no "
          "equipment: a walk or a jog for ten minutes to warm up, then squats or sit-to-stands, "
          "press-ups on the stairs or against the worktop, a hip hinge, and a plank, two rounds of "
          "each. Push into the last two or three of every set and add a rep each week, because that "
          "progression is what changes anything. Walk on the days between, and give it six weeks "
          "before you judge it.",
          ask=("get fit", "fitter", "exercise", "work out", "workout", "keep fit", "in shape",
               "start"),
          # not the bare word gym: "i want to get fitter without a gym" is this question, and
          # only the joining shapes belong to gym-first-time
          avoid=("gym membership", "join a gym", "joining a gym", "membership", "classes",
                 # "work out" is a sum as well as a session, and "how do i" is in the joining
                 # words above: "how do i work out the volume of a box", "... how much paint i
                 # need" and "... the area of a room" all got the three-sessions-a-week answer.
                 # A sum is "work out the ..." and also "work out my ..." (a bmi, a tax, a
                 # pension), so the nouns of the figure are named here too, not only the shapes.
                 "volume", "area", "paint", "calculate", "work out the", "how much paint",
                 "square metre", "square metres", "cubic", "percentage", "average",
                 "bmi", "tiles", "tax", "mortgage", "calories", "pension", "one rep max",
                 # "work out what to give" is a sum about a present, not a session: the object of
                 # the figuring is a gift, so the nouns come with it.
                 "work out what", "work out which", "what to give", "what to buy", "what to get",
                 "present", "presents", "gift", "gifts",
                 "run", "running", "marathon", "5k",
                 "walking", "steps", "lose weight", "diet", "belly", "muscle", "stronger",
                 # the sums a person does with a pencil in their hand, not a session: a
                 # discount, the change from a note, an exchange rate, the tip on a bill.
                 # "how do i work out a discount" was answered "three half-hour sessions a
                 # week", and "how do i work out change from a note" and "... an exchange
                 # rate" the same way, because "work out" is in this row's key.
                 "discount", "discounts", "change from", "my change", "the change",
                 "change in a", "exchange rate", "exchange rates", "currency", "convert",
                 "conversion", "tip", "tips", "service charge", "share of the bill",
                 "split the bill", "share of a", "fraction", "fractions",
                 # and the sums a pay office does: "how do i work out my redundancy pay" got the
                 # three-sessions-a-week answer, because "work out my" is a figure and this row
                 # only knew the pencil nouns. The money a job owes is that kind of figure too.
                 "redundancy", "redundant", "severance", "notice pay", "final wages",
                 "holiday pay", "sick pay", "wages", "salary", "payslip", "pay slip",
                 "swimming", "bike", "cycling", "yoga", "pilates", "park", "dog",
                 # the bare ask is here now, so the questions that only look like it step aside:
                 # an injury, an age, a long break, a target time and a body part all have their
                 # own answer, and telling someone with a bad knee to do squats is the worst one
                 "knee", "knees", "back pain", "bad back", "shoulder", "injury", "injured",
                 "sore", "arthritis", "pregnant", "after a break", "years off", "havent",
                 "haven't", "at 40", "at 50", "at 55", "at 60", "at 65", "at 70", "in my 40s",
                 "in my 50s", "in my 60s", "older", "age of", "how long", "how often",
                 "how many times", "weight loss", "protein",
                 # "work out" is two things: a session, and a sum. Every line that asks how to
                 # work something out - a percentage, VAT, an average, a BMI, how much paint - has
                 # the exercise words by accident, because "out"/"how do i" are in the key, so
                 # "how do i work out a percentage" was answered "three half-hour sessions a week"
                 # while maths.percent-how sat right there with the method. The object decides
                 # the sense, so the objects that are sums step aside.
                 "percentage", "percent", "per cent", "vat", "tax", "tip", "average",
                 "mean", "median", "bmi", "interest", "mortgage", "loan", "paint", "wallpaper",
                 "area", "square", "metre", "meter", "mile", "km", "kilometre", "kilometer",
                 "convert", "celsius", "fahrenheit", "fraction", "decimal", "ratio", "sum",
                 "total", "split", "share", "split the bill", "bill", "cost", "price", "wage",
                 "salary", "hourly rate", "overtime", "holiday pay", "unit", "dose", "medicine",
                 "score", "odds", "probability", "distance", "how much petrol",
                 # "work out how much carpet i need" is a sum about a floor, and the material
                 # being measured is not in the list above: the shapes are, so every "work out
                 # how much / how many / how long" and every "how much do i need" step aside
                 # whatever is being bought.
                 "work out how much", "work out how many", "work out how long",
                 "how much do i need", "how many do i need", "how much will i need",
                 "how many will i need"),
          bias=1),
    # --- the session itself -------------------------------------------------------------
    # Somebody who has joined a gym asks about the session, not the week: how many sets, how
    # heavy, how long between sets, when to add weight, how long to be there. None of those is
    # the frequency question the sport domain answers, and the numbers are what people come for,
    # so each entry leads with its own number.
    entry("sets-and-reps",
          (("sets and reps", "sets", "reps", "repetitions", "rep range", "reps and sets"),
           ("how many", "how much", "number of", "should i do", "do i do", "what should")),
          "Three sets of 8 to 12 reps is the all-round default for building muscle: pick a weight "
          "where the last two reps are hard but your form still holds. For strength, go heavier "
          "and shorter - 3 to 5 sets of 4 to 6 reps - and for endurance, lighter at 15 to 20. "
          "Three or four exercises a session is plenty.",
          # "sets" is an ordinary word - a tennis match, a set of sheets, the clock - and this
          # entry only answers it when the line is counting reps
          avoid=("tennis", "badminton", "squash", "volleyball", "match", "table tennis",
                 "bed", "sheets", "bedding", "curtains", "table", "clock", "alarm", "timer",
                 # the heating's own "set" - "what should i set my bedroom thermostat to at
                 # night" was three sets of eight to twelve reps
                 "thermostat", "heating", "radiator", "boiler", "temperature",
                 "tv", "television", "lego", "chess", "cards", "darts", "leaves",
                 # "set up" is the phrasal verb of every business line: "how much does it cost
                 # to set up a website" was three sets of eight to twelve reps
                 "set up", "setting up", "website", "business", "company", "limited", "ltd",
                 "sole trader", "invoice", "accountant", "hmrc", "tax", "shop", "landlord",
                 "pension", "savings", "insurance", "mortgage", "domain")),
    entry("rest-between-sets",
          (("rest", "resting", "break", "wait", "how long"),
           ("between sets", "between each set", "between every set", "each set", "sets", "set",
            "reps")),
          "Ninety seconds to two minutes between sets for most of what you do: long enough to get "
          "your breath back and keep your strength, short enough to finish in an hour. Heavy sets "
          "of 4 to 6 reps want two to three minutes; a small isolation move or a warm-up set needs "
          "45 seconds.",
          # "how long" plus "set" is also a screen's own setting - "how long should i set my
          # screen timeout" was ninety seconds between sets
          avoid=("screen", "timeout", "phone", "iphone", "ipad", "android", "tablet", "laptop",
                 "display", "brightness", "monitor", "tv", "television", "watch", "alarm",
                 "timer", "heating", "thermostat", "boiler", "radiator")),
    entry("add-weight",
          (("increase", "add", "put up", "go up", "more", "heavier", "progress"),
           ("weight", "weights", "load", "the weight", "the bar")),
          "Add weight when you can hit the top of your rep range on every set with clean form - "
          "usually every week or two when you are new. Take the smallest jump you have, 2.5kg on a "
          "bar or the next dumbbell up, and expect to lose a rep or two for a session or so; that "
          "is the new weight working, not a bad day.",
          # a weight that is dropping is a diet question, and a lift is not the only thing counted
          avoid=("lose", "losing", "loss", "diet", "fat", "belly", "stone", "pounds",
                 "scales", "bmi", "calories", "fast", "quickly", "drugs", "medicine",
                 "dose", "hair",
                 # the other direction of the same scale: putting weight on is a diet question
                 "gain", "gaining", "put on", "eat", "eating", "food", "meal", "feed",
                 "appetite", "underweight")),
    entry("how-heavy",
          (("how heavy", "how much weight", "what weight", "how much should i", "which weight"),
           ("lift", "lifting", "weights", "weight", "use", "start", "begin", "choose", "go")),
          "There is no number that suits everyone: choose a weight you can lift 10 times but not "
          "15, with the last two a real effort. If you can do 15 easily it is too light; if your "
          "form breaks before 8, it is too heavy. Write down what you use each session so you know "
          "what to beat.",
          avoid=("lose", "losing", "loss", "diet", "fat", "belly", "stone", "pounds",
                 "scales", "bmi", "baby", "pram", "pushchair", "carry", "shopping",
                 "suitcase", "bag", "box", "surgery", "operation", "pregnant", "pregnancy",
                 "broken", "fracture", "hernia", "hospital", "nurse",
                 # what a house, a car or a roof will hold is a different kind of weight
                 "roof", "rack", "car", "van", "bike", "bicycle", "trailer", "boot", "plane",
                 "flight", "luggage", "shelf", "wall", "beam", "loft", "tow bar", "towing",
                 # and what a butcher weighs is a dinner: "what weight is a joint" and "what
                 # weight of meat for a roast" are the portion answer's lines
                 "joint", "joints", "meat", "roast", "roasting", "butcher", "dinner",
                 "sunday lunch", "gravy", "thighs", "mince", "steak", "joint of")),
    entry("train-to-failure",
          (("failure", "to failure", "all out", "max out", "go hard"),
           ("train", "training", "lift", "lifting", "set", "sets", "push", "should i",
            "every set", "each set", "need", "need to", "have to", "must")),
          "You don't need to: stopping one or two reps short of failure builds about as much "
          "muscle and leaves you far less battered, so keep the last rep hard but doable on most "
          "sets. Take a set to all-out failure now and then on a machine or a small isolation "
          "move, not on squats or deadlifts where form goes first."),
    entry("session-length",
          (("how long", "length", "how much time"),
           # not the bare word gym: "how long does it take to get to the gym" is a journey.
           ("workout", "session", "gym session", "training session", "in the gym", "at the gym")),
          "Forty-five minutes to an hour is the sweet spot: five minutes of warm-up, three or four "
          "exercises at three sets each, and a couple of minutes between sets. Past 90 minutes you "
          "are mostly resting and getting tired rather than stronger, so drop an exercise rather "
          "than the rest.",
          avoid=("plan", "holiday", "away", "membership", "contract", "queue", "waiting",
                 "stay", "open", "close", "driving", "walk",
                 # the rest *after* a session is the recovery question, not the session's length
                 "rest", "resting", "recovery", "recover", "sore", "soreness")),
    entry("same-muscle-two-days",
          (("two days in a row", "two days running", "back to back", "every day", "daily",
            "consecutive days", "day after day",
            # "every single day", "each day" and "7 days a week" are the same question in the
            # words people use, and "is it bad to work out every single day" was a shrug.
            "every single day", "everyday", "each day", "six days a week", "7 days a week",
            "seven days a week", "every morning", "every night"),
           ("muscle", "muscles", "same muscle", "train", "training", "lift", "lifting", "gym",
            "workout", "work out")),
          "Rest a muscle about 48 hours before training it hard again, so not the same one every "
          "day: two full-body sessions a "
          "week with a day between them, or an upper/lower split on back-to-back days so each "
          "muscle still gets its rest. Training the same muscle every day is how people end up "
          "sore, stale and not adding weight.",
          guard=_an_ask_about_training_every_day),
    entry("stamina",
          (("stamina", "endurance", "cardiovascular fitness", "fitness level"),
           ("improve", "build", "increase", "better", "boost", "up", "more", "back")),
          "Build stamina with easy, longer efforts rather than all-out ones: three sessions a week "
          "of 20 to 30 minutes at a pace where you can still talk in short sentences, adding five "
          "minutes a week. Once those feel comfortable, swap one for four minutes hard, two easy, "
          "repeated three or four times."),
    entry("squat-form",
          (("squat", "squats", "squatting"),
           ("form", "proper", "technique", "how do i do", "how to do", "how deep", "deep",
            "depth", "posture")),
          "Feet about shoulder-width with the toes turned out slightly, chest up and eyes forward: "
          "sit back and down as if reaching for a chair, and let your knees travel forward over "
          "your toes while your back stays straight. Go as deep as you can with your heels down - "
          "hips below the knees is the usual aim - and practise onto a chair until it feels natural.",
          # a knee or a back that hurts is the pain question (`sport.py`, `body.py`)
          avoid=("hurt", "hurts", "hurting", "pain", "painful", "ache", "aches", "aching",
                 "knee", "knees", "click", "clicks", "clicking", "swollen", "injury", "injured",
                 "surgery", "squash", "court", "weight loss")),
    # "How long until I see results" is the question every new gym member asks, and the only
    # answer here was how to train: "how long does it take to get fit", "when will i see results"
    # and "how long until i notice a difference" were all shrugs. The figure is what the person
    # came for, so the reply is the ladder - feel it, lift more, see it, others see it - and it
    # says plainly that the mirror is the slow part.
    entry("exercise-timeline",
          (("get fit", "get fitter", "getting fit", "fitter", "in shape", "get stronger",
            "stronger", "build muscle", "gaining muscle", "see results", "results",
            "see a difference", "notice a difference", "a difference", "see a change",
            "notice a change", "progress"),
           ("long", "when", "soon", "weeks", "months", "time", "take", "until",
            "sessions")),
          "You feel it before you see it: stairs and breathing get easier in two to three weeks, "
          "and by six weeks you are lifting noticeably more than your first session. The mirror "
          "is the slow part - six to eight weeks for a change you can see, about three months for "
          "anyone else to notice, and a kilo of muscle a month at best, so judge it on a session "
          "you can now finish rather than on the scales.",
          # the clock has to be asked for: "i want to get fit" is the starts-today answer, not a
          # timetable, and the two rows are one line apart
          ask=("how long", "how soon", "when will", "when should", "when do", "when can",
               "how many weeks", "how many months", "how much time", "how long until",
               "how long before", "how long till", "until i", "until my", "time to"),
          # results that come from a test, a scan or an application are not training, and
          # "the difference between" is a comparison somebody else answers
          avoid=("blood", "test", "tests", "exam", "exams", "results day", "scan", "x-ray",
                 "xray", "biopsy", "hospital", "doctor", "gp", "nurse", "pregnant",
                 "pregnancy", "came back", "interview", "job", "application", "mortgage",
                 "house", "offer", "court", "election",
                 "difference between", "whats the difference", "what is the difference",
                 "skin", "hair", "teeth", "nails", "acne", "diet", "weight loss", "lose",
                 "losing", "stone", "pounds", "lbs", "kg", "scales", "bmi", "calories",
                 # a dog, a plant and a baby grow and change too, and none of them is a workout
                 "dog", "dogs", "puppy", "cat", "puppies", "baby", "babies", "child",
                 "toddler", "plant", "plants", "garden", "lawn", "haircut", "beard",
                 # a beginner's program, an injury and a return from a break all have their own
                 "injury", "injured", "sore", "pain", "knee", "knees", "back pain",
                 "havent", "haven't", "after a break", "years off", "covid", "ill", "sick")),
]


# "how fast should i walk a mile" named nothing the fitness domain keys on, so understanding gave
# it no topic at all and the line fell to the punt - while the same question asked as "how long
# does it take to walk a mile" was answered, because maths read the arithmetic. The pace is one
# number a person came for, and it is the same number however they ask it. An explaining row is
# reached on a line with no topic (the two-position pre-filter is skipped), which is why this one
# carries explain: the lines arrive with no domain at all.
# The question is asked with the pace word and the verb together ("how fast should i walk"),
# and the row was outscored on exactly those lines - geography's "how far" row took "how fast
# should i walk a mile" and "how quickly should i walk" went to the steps row. The phrases put
# the pace in the first part of the key, which is what the row is built on.
_WALK_PACE = ("how fast should i walk", "how fast do i walk", "how fast can i walk",
              "how quickly should i walk", "how quickly do i walk", "how fast to walk",
              "walking pace", "pace should i walk", "what pace should i walk",
              "how fast should i walk a mile", "how long should a mile take",
              "how long does a mile take", "how long does it take to walk a mile",
              "speed should i walk", "walks", "walk", "walking", "walked", "mile", "miles",
              "brisk", "stroll", "strolling", "steps", "stepping")
_WALK_PACE_ASK = ("how fast", "fast", "how quickly", "quickly", "pace", "speed", "how long",
                  "how many minutes", "minutes", "mile", "miles", "brisk", "briskly",
                  "quick", "slow", "slowly", "an hour", "an hour and a half", "mph",
                  "how far", "time")
_PACE_WORD = re.compile(
    r"\b(how fast|how quickly|how long|how far|pace|speed|mph|fast|faster|quick|quickly|"
    r"slow|slowly|brisk|briskly|good|normal|ok|okay|average)\b")
# "walk" is a word in a place's name as often as it is a thing someone does: "how long is the wait
# at the walk in centre" was told the pace of a mile, because the row keys on "how long" and
# "walk" and a walk-in centre carries both. The wait at a clinic is the clinic's own number to
# know, so the row stands down when the line is about waiting rather than walking.
_NOT_A_WALK = re.compile(
    r"\b(walk[\s-]?in[\s-]+(?:centre|center|clinic|service|baths?)|"
    r"how long (?:is|are|will) (?:the )?(?:wait|queue)|waiting time|"
    r"how long (?:will|do) i (?:have to )?wait)\b")
def _a_question_about_pace(understood):
    """True only for a line that actually asks about the pace.

    Two things the words alone cannot tell apart. First, a walk that has already happened
    ("i walked 5 miles") is news the chat acknowledges, not a question - and the avoid list
    cannot hold "walked" because it is a form of the row's own key word. Second, the key holds
    "steps" and "minutes", which is any line with a number of minutes in it: in a chat about
    dizzy spells, "i had to sit down on the step for ten minutes" was told the pace of a mile.
    So the row answers only a line that carries a pace or a judgement word as well.
    """
    clean = str((understood or {}).get("clean") or "")
    if _NOT_A_WALK.search(clean):
        return False
    if re.search(r"\b(i|we|he|she|they)\b[^.]*\b(walked|went|did)\b", clean):
        return False
    return bool(_PACE_WORD.search(clean))


activity = entry("walking-pace", (_WALK_PACE, _WALK_PACE_ASK),
      "A mile is 20 minutes at a brisk walk - three miles an hour, and 1.6 km - or about 15 "
      "minutes if you are pushing it. Brisk means you are breathing a bit harder and can talk but "
      "not sing. Half an "
      "hour a day is the number that earns most of the benefit: about a mile and a half, or the "
      "seven to eight thousand steps people talk about. If you want a target, walk a mile at a "
      "pace that leaves you slightly warm rather than comfortable, three times a week, and time "
      "yourself - it is an easy number to watch come down. Are you walking for fitness or for a "
      "particular distance?",
      # a run, a race and a dog walk are other rows' questions; a treadmill is a session, not a
      # pace, and the arithmetic of distances belongs to maths. An avoid phrase is flattened to
      # its single words, so a phrase that carries one of this row's own key words ("walk the
      # dog", "how many steps") vetoes every line the row is for: those are named by the one
      # word that is not in the key ("dog", "pedometer") instead.
      avoid=("run", "running", "ran", "jog", "jogging", "jogged", "marathon", "10k", "5k",
             "parkrun", "race", "races", "half marathon", "sprint", "treadmill", "incline",
             "dog", "dogs", "puppy", "cat", "baby", "toddler", "child", "pushchair", "pram",
             "school run", "commute",
             "map", "shoes",
             "trainers", "boots", "blister", "blisters", "sore", "knee", "knees", "hip",
             "ankle", "feet", "foot", "pain", "pregnant", "pregnancy", "period", "ill",
             "sick", "covid", "heart", "chest", "breath", "blood pressure", "diabetes",
             "weight", "lose", "losing", "calories", "diet", "pedometer", "app", "watch",
             # "im walking a mile a day is that enough" asks whether the amount is enough, and
             # the walking-is-enough row answers that; so does "is walking 3 miles an hour fast
             # enough". This row is the pace itself.
             "enough", "too much", "too little",
             # a walk already taken is news, not a question, and it gets the acknowledgement
             "today", "yesterday", "this morning", "last night",
             # a body that is dizzy, faint or off balance is a health question: "i had to sit
             # down on the step for ten minutes", said in a chat about dizzy spells, was reaching
             # this row on "step" and "minutes" and being told the pace of a mile. The two words
             # "steps"/"minutes" are any line with a number of minutes in it, so the row has to
             # stand down when the body is the subject.
             "dizzy", "dizziness", "dizzier", "faint", "fainted", "fainting", "lightheaded",
             "light headed", "vertigo", "spinning", "nausea", "nauseous", "balance",
             "blurred", "blacked out", "passed out", "collapse", "collapsed"),
      guard=_a_question_about_pace)
activity.explain = True
ENTRIES.append(activity)

# --- what a week of it looks like ------------------------------------------
# "whats a good workout routine" and "whats a good gym routine" both reached the habit row in
# `routines.py`, which answers how to *build* a habit ("two minutes, one press-up") rather than
# what to do in the session. The subject words now stand that row down and this one answers.
ENTRIES.append(entry(
    "a-workout-routine",
    (("routine", "routines", "plan", "schedule", "split", "programme", "program"),
     # "weights" is not here on its own: `_forms("weights")` also matches "weight", so
     # "whats a good routine for losing weight" reached this card and lost the answer main
     # already gave it (a deficit you can live with). A weights line says it as a phrase.
     ("workout", "workouts", "gym", "exercise", "exercises", "training", "lifting",
      "weights session", "lifting weights", "free weights", "weights at the gym",
      "session", "sessions")),
    "A full-body session three times a week beats a body-part split for the first year: five "
    "moves - a squat, a push, a pull, a hinge and a carry - three sets of eight to twelve reps, "
    "and add a little weight once twelve feels easy. Monday, Wednesday and Friday (or Tuesday, "
    "Thursday and Saturday) with a walk between, five minutes of anything that gets you breathing "
    "before the first set, and a rest day between sessions, because that is when the muscle is "
    "built. Twenty minutes counts if that is the time you have; what changes the result is "
    "turning up three times a week for two months, not the perfect plan.",
    bias=3,
    avoid=("membership", "cancel", "join", "price", "cost", "how much", "contract",
           "treadmill", "shoes", "trainers", "home", "at home", "app", "watch",
           "sore", "pain", "knee", "back", "shoulder", "injury", "injured", "pregnant",
           "beginner", "beginners", "starting", "start", "first time", "never",
           "how many", "how long", "how often", "enough",
           # a routine for losing weight is the deficit and the food, not five gym moves: those
           # rows already answer it and this card was taking their lines
           "losing weight", "lose weight", "lost weight", "weight loss", "fat loss",
           "lose fat", "slimming", "diet", "diets", "dieting", "a stone", "stones",
           "kilos to lose", "pounds to lose", "tone up", "toning up"),
    ask=("whats a good", "what is a good", "what's a good", "good", "best", "recommend",
         "suggest", "what should i do", "look like", "give me", "write me", "set me")))

# "i cant walk far" and "i struggle to walk to the shops" got nothing at all, "i cant walk more
# than 5 minutes" got "I'm listening", and "my nan cant walk far, what would help her get out the
# house" was answered with advice about agreeing boundaries - four lines about one common thing,
# a person whose walking has a limit, and no answer among them. `an-easy-walk` in travel.py is
# the row for choosing somewhere to walk, and it took "i cant walk far what do i need" as a place
# question; this row is for the limit itself, so the words that ask *where* stand it down.
ENTRIES.append(entry(
    "a-short-walk-limit",
    (("walk", "walks", "walking", "walked", "get about", "get around", "the shops", "shops"),
     ("cant walk", "can't walk", "cannot walk", "not far", "walk far", "struggle", "struggling",
      "cant manage", "can't manage", "cant go far", "a few minutes", "5 minutes", "ten minutes",
      "out of breath", "tire quickly", "tires quickly", "tired quickly", "exhausted",
      "my legs", "weak legs", "unsteady", "off balance")),
    "Get the reason looked at if it has come on lately: breathlessness, a calf that aches and "
    "stops you, or one leg tiring before the other are worth a GP appointment, and a physio can "
    "fit a stick or a four-wheel rollator properly instead of guessing. Then build the distance "
    "in short bouts rather than one trip: five minutes out and back, twice or three times a day, "
    "adding a minute or two a week, and sit down at the far end rather than turning round the "
    "moment it aches. Short and often beats one long walk for both legs and confidence, and "
    "leaning on a shopping trolley or carrying a folding stick makes the shops doable now "
    "rather than after.",
    # a place to walk, a dog, a pram, a step count and a symptom in a body part are all other
    # rows' answers, and this row must not take them
    avoid=("where can i", "where can we", "where to", "somewhere", "route", "routes", "canal",
           "country park", "near me", "map", "dog", "dogs", "puppy", "pram", "pushchair",
           "baby", "babies", "toddler", "child", "children", "kids", "hike", "hiking",
           "holiday", "flight", "airport", "stairs", "upstairs", "how many steps", "step count",
           "pedometer", "run", "running", "jog", "marathon", "parkrun", "race",
           "knee", "knees", "hip", "ankle", "foot", "feet", "hurt", "hurts", "pain", "painful",
           "sore", "swollen", "cramp", "should i walk", "is it ok to walk", "good for",
           # a claim is a benefits question, and answering "can i claim pip for not being able
           # to walk far" with what helps the walking loses the thing being asked about
           "pip", "dla", "esa", "uc", "universal credit", "claim", "claiming", "benefit",
           "benefits", "allowance", "blue badge", "disabled badge", "motability", "entitled",
           "work capability", "assessment"),
    bias=3))

# The same limit in somebody else: "my nan cant walk far, what would help her get out the house"
# was answered with the boundaries card, because it names a relative and asks for help. What the
# person wants is how to get an outing to work when the walking has a ceiling on it.
ENTRIES.append(entry(
    "out-of-the-house",
    (("out of the house", "out the house", "get her out", "get him out", "get them out",
      "take her out", "take him out", "take them out", "take mum out", "take dad out",
      "an outing", "get out more"),
     ("walk", "walks", "walking", "walk far", "cant walk", "can't walk", "not far",
      "mobility", "scooter", "wheelchair", "tired", "slow", "elderly", "old",
      "hip", "knee", "knees", "arthritis", "recovering", "recovery", "since her fall",
      "since his fall")),
    "Plan the outing around the walking. Go door to door - a taxi, or the bus that stops nearest "
    "the door - and make a bench or a cafe the turning point so the trip is two short walks with "
    "a sit in between. A four-wheel rollator with a seat means they can rest anywhere, and most "
    "big supermarkets, shopping centres and National Trust or English Heritage places lend a "
    "wheelchair or a mobility scooter free if you ring a day or two ahead; a Radar key opens the "
    "accessible toilets, and going in the morning, before they are tired, makes the most of the "
    "day. Two short trips a week beat one long one.",
    avoid=("toddler", "baby", "babies", "child", "children", "kids", "dog", "puppy",
           "holiday", "flight", "airport", "hotel", "cruise", "abroad"),
    bias=4))

# --- the words on a training plan ---------------------------------------------------
# Three things a person meets in a running plan or a gym bag and has to ask about: the pace a
# plan calls a "tempo", the way a race should be run, and the thing that stops running being
# painful. All three were search hedges on main, and each is a definition, so each answer says
# what the thing is and then the number that makes it usable.
ENTRIES.append(entry(
    "negative-split",
    (("negative split", "negative splits", "negative splitting", "positive split",
      "run the second half faster", "second half faster"),
     ("what is", "whats", "what does", "mean", "means", "how", "why", "should i", "better",
      "good", "pace", "race", "marathon", "half", "10k", "5k", "train", "training")),
    "A negative split is running the second half of a race faster than the first - 5k in 25 "
    "minutes then 5k in 24, say - and it is the mark of a well-paced run rather than a fast one. "
    "It works because the first half of a race is where people go too quickly: the effort feels "
    "easy for the first two miles, so the pace creeps up, and the last third is paid for at a "
    "price. Start five or ten seconds a mile slower than your goal pace for the first third, hold "
    "it through the middle, and let the last third come to you.",
    # a marathon plan, a personal best and a stitch are other questions
    avoid=("marathon plan", "training plan", "personal best", "pb", "stitch", "cramp",
           "shin", "knee", "blister", "chafing"),
    bias=1))

ENTRIES.append(entry(
    "tempo-run",
    (("tempo run", "tempo runs", "tempo session", "tempo running", "threshold run",
      "threshold training", "comfortably hard"),
     ("what is", "whats", "what does", "mean", "means", "how", "how long", "how fast", "pace",
      "should i", "do i", "week", "per week", "beginner", "start", "started", "faster")),
    # the length comes first on purpose: "how long should a tempo run be" asks on the back of this
    # reply and the follow-up reader takes the first duration out of it, which used to be "an
    # hour" from the pace description and answered a 20-to-40-minute session with "An hour."
    "A tempo run is 20 to 40 minutes at a pace you could just about hold for an hour - \"comfortably "
    "hard\", where talking is possible in short sentences but not a conversation. It trains the "
    "point "
    "where your body stops clearing lactate as fast as it makes it, which is what makes a race "
    "pace feel easier. It sits inside an easy run, once a week, with the warm-up and cool-down "
    "done slowly; if you cannot speak a sentence, it is "
    "too fast, and if you can chat, it is too slow.",
    # an easy run, an interval session and a race are other runs, and a tempo in music is
    # entertainment's
    avoid=("interval", "intervals", "fartlek", "hill repeats", "sprint", "sprints", "race day",
           "music", "song", "bpm"),
    bias=1))

ENTRIES.append(entry(
    "sports-bra",
    (("sports bra", "sports bras", "running bra", "high impact bra", "bra for running",
      "bra for the gym", "bra for exercise"),
     ("what is", "whats", "what does", "mean", "which", "what", "buy", "buying", "need",
      "support", "impact", "size", "sizing", "fit", "fits", "right", "best", "how often",
      "wash", "replace", "last", "running", "gym", "exercise", "bounce")),
    "A sports bra is a bra built to hold the breast still rather than shape it, and the amount it "
    "holds is graded: low support for yoga and walking, medium for cycling and weights, high for "
    "running and anything bouncy. Buy it by the band size rather than the cup alone - it should be "
    "snug on the loosest hook with two fingers of room under the band - and replace it when the "
    "band has stretched, usually after about a year of regular washing. Wash it cool after every "
    "wear, because sweat and elastic do not get on.",
    # an everyday bra, a bikini and a fitted bra are clothing questions
    avoid=("underwire", "wired bra", "everyday bra", "bra size", "bikini", "swimsuit",
           "strapless", "backless", "nursing bra"),
    bias=1))
