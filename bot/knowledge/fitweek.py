"""Fitness: the shape of an exercise week, in a module of its own.

Five everyday exercise questions that had no owner on the current main, or got a health-triage
pointer: the cool-down, coming back after years off, the kit worth buying for a home gym, the
running load that causes repeated injuries, and training on an empty stomach. Each reply leads
with the number or the one thing to buy, because that is what the person asked for.

The five rows live here rather than in `fitness.py` and `sport.py` because those two files are
edited by other lanes several times an hour; nothing about the rows is specific to this file.
"""
import re

from .lookup import entry

# Every white good and small appliance home.py knows, read from its one table rather than copied,
# so this row recognises the machines the fault rows answer. A cool-down is a body doing a workout;
# no appliance is one.
from .home import SMALL_APPLIANCES, WHITE_GOODS
MACHINE_WORDS = tuple(dict.fromkeys(
    [word for pair in WHITE_GOODS + SMALL_APPLIANCES for word in pair]
    + ["appliance", "appliances", "white goods"]))
# "machine" and "machines" are deliberately not in that list: a rowing machine and "the gym
# machines" are what a workout happens on, and standing the card down for them answered
# "how do i cool down after using the rowing machine" with the rowing technique instead.

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("fitness", "sport")

ENTRIES = [
# --- the shape of a week: rest, the cool-down, coming back, and what to buy -----------
entry("cool-down",
      (("cool down", "cool-down", "cooldown", "cooling down", "stretch after", "after a workout",
        "after a session", "after a run", "after exercise", "finish a workout", "finish a run"),
       ("how", "should", "need", "do i", "what", "worth", "best", "long", "properly")),
      "Walk or cycle easily for five minutes until your breathing is normal, then hold two or "
      "three stretches for 20 to 30 seconds each - that is the whole cool-down, and it will not "
      "stop next-day soreness. Stretching before a run does not prevent injuries either; "
      "starting slowly does. If you are short of time, skip the stretches and take the extra "
      "ten minutes of sleep.",
      # an ache a day later is soreness, which has its own answer, and the question that
      # gets it is "how do i stop my legs aching after exercise"
      avoid=("hamstring", "calf", "cramp", "how do i stretch", "stretches for", "before or after",
             "warm up", "aching", "ache", "sore", "doms", "stiff",
             # a hot room, a car or a dog is not a workout: "cool down" is the same words
             "room", "bedroom", "house", "flat", "summer", "weather", "dog", "baby",
             "car", "drink", "fever", "temperature", "bath", "shower",
             # and neither is a machine: "my dishwasher is not cooling down properly" was
             # answered with a five-minute walk and two stretches. The white goods are read
             # from the same table home.py answers them from, so a machine added there is
             # stood down here the same day.
             MACHINE_WORDS,
             # the other half of "after a workout" is what to eat: "what should i eat after a
             # workout" wants the protein answer, not a five-minute walk and two stretches
             "eat", "eating", "ate", "food", "protein", "carb", "carbs", "snack", "snacks",
             "meal", "breakfast", "lunch", "dinner", "shake", "calories",
             # a dish that is too hot is the kitchen's question: "how do i cool down a curry"
             # was answered with a five-minute walk and two stretches.
             "curry", "chilli", "chili", "stew", "sauce", "soup", "rice", "pasta", "casserole"),
      bias=1),

entry("back-to-exercise",
      (("back into exercise", "getting back into exercise", "get back into exercise",
        "start exercising again", "exercise again", "havent exercised", "have not exercised",
        "havent trained",
        # "years off" on its own was the CV-gap card's line: "i took 3 years off to care for my
        # mum how do i explain it" matched this row on "years off" and the ask, and was answered
        # with how to start walking again. The years off are the years off training, so the
        # phrase carries the training with it; a bare "ive had two years off" leans on the chat
        # it follows, which is what `use_context` is for.
        "years off", "stopped exercising", "restart exercise",
        "starting again with exercise", "unfit", "really unfit", "long break"),
       ("how", "best", "should", "start", "again", "after", "long", "years", "slowly",
        "beginner", "where do i")),
      "Start at about half of what you think you can manage and go every other day for the "
      "first two weeks - 20 minutes of walking or easy cycling is plenty, and the aim is to "
      "finish feeling you could have done more. Add about a tenth a week after that, and expect "
      "the second day to be sorer than the first, which is normal, while a joint that hurts is "
      "a stop. Give it six weeks before you judge it, because the habit and the tendons come "
      "back more slowly than the muscle.",
      # a return to running is not a return to exercise in general: "how do i get back into
      # running after years off" is the run-walk answer, and "years off" alone was enough for
      # this entry's bias to take it, so the run words here hand it back.
      #
      # The frequency of the week is its own answer, and it is the other way this card gets in
      # the way: after "start running again after years off" the follow-up "how many times a
      # week should i go out" was answered with this card again, framed "Same as before:". The
      # number of sessions is how-often-to-run's line, not the slow start.
      avoid=("gym", "membership", "swim", "kettlebell", "dumbbell", "running plan", "couch to 5k",
             "run", "runs", "running", "ran", "jog", "jogs", "jogging", "5k", "10k",
             "marathon", "half marathon", "parkrun",
             # The ask of a CV gap, not of a training plan: "how do i explain it", "how do i put
             # it on my cv". A fitness question does not ask how to explain the years away to an
             # employer, so those words hand the line back to the CV-gap card.
             "explain", "explaining", "explanation", "cv", "resume", "work history",
             "employment", "employer", "interview", "recruiter", "maternity", "career break",
             "how many times", "how often", "times a week", "days a week", "a week", "per week",
             "rest days", "every day"),
      bias=1),

entry("every-day-exercise",
      # only the words of the gap: "is it bad to work out every day" and "can i train every day"
      # are already answered by `sport.rest-days` and `sport.same-muscle-two-days`, and keying
      # "workout" here would take them and demote the cool-down and rest-day rows' rarity
      (("exercise", "exercising"),
       ("every day", "everyday", "daily", "seven days", "7 days", "each day", "every single day",
        "all week", "no rest", "every morning", "every evening", "twice a day")),
      "Yes, for anything you can hold a conversation through - a walk, a bike ride, a swim - and "
      "that is the kind of movement most people can do every day. What needs a day in between is "
      "hard strength work on the same muscles: lift hard today and leave that muscle 48 hours, "
      "because the muscle is built on the rest day, not in the session. Two or three hard "
      "sessions a week plus easy movement on the other days beats five hard ones, which is where "
      "sore joints and stalled progress come from.",
      # the amount of exercise in a week is its own card, the pace of a comeback is another,
      # and a walk that counts as exercise is the steps answer - so none of those reach here
      avoid=("how much exercise", "how long", "how many minutes", "how long should i exercise",
             "minutes a day", "150", "minutes a week", "a week",
             "per week", "times a week", "days a week", "enough", "steps", "how many steps",
             "10000", "10,000", "get back into", "havent exercised", "have not exercised",
             "unfit", "beginner", "start exercising", "rest day", "rest days",
             "dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "horse", "rabbit",
             "guitar", "piano", "practise", "practice", "revision", "revise", "study")),

entry("home-gym-kit",
      # not the bare words "kit" and "equipment": "what kit do i need for camping", for a new
      # baby, to paint a room were all answered with a kettlebell. The gym noun has to be in
      # the line, and the second group carries the buying question.
      (("home gym", "kettlebell", "kettlebells", "dumbbell", "dumbbells", "resistance band",
        "resistance bands", "barbell", "pull up bar", "pull-up bar", "bench", "weights",
        "gym equipment", "gym kit"),
       # the bare "what" and "much" made "what weight should i use for bench press" a buying
       # question, so the second group is the buying words themselves
       # "kit" and "equipment" are not buying words of their own - they are the first group's
       # own nouns - so leaving them here let "my gym kit still stinks after washing" and "my
       # gym equipment smells" answer themselves with a shopping list. A buying line says buy,
       # cheap, which or start, or it says need: "what kit do i need for a home gym" has one.
       ("budget", "cheap", "cheaper", "buy", "buying", "bought", "need", "worth", "best",
        "which", "start", "starting", "small space", "flat", "set up",
        "get started", "first")),
      "Buy one adjustable dumbbell or one kettlebell and nothing else to begin with: about "
      "6 to 10 kg suits most beginners and 10 to 16 kg if you are already strong, and a used "
      "one goes for £40 to £80. Add a resistance band for about £10 and a step or a sturdy "
      "chair, and that covers squats, rows, presses and carries - a mat only if your floor is "
      "hard. Skip the bench and the multi-gym until you have trained for six months, because "
      "the routine is what makes the difference, not the rack.",
      avoid=("treadmill", "rower", "spin bike", "exercise bike", "trampoline", "rent",
             "delivery", "assembly",
             # how much to lift is the session answer (10 reps but not 15), not a shopping list
             "bench press", "deadlift", "squat", "squats", "lifting", "lift", "reps", "rep",
             "sets", "one rep max", "1rm", "heavier", "load", "form",
             # "what dumbbell weight should i start with" is the load question too, and "weight"
             # is what it says; the plural "weights" is still a thing to buy
             "weight",
             # A kit that stinks, or needs a wash, is the laundry question: main already
             # answers "how do i get the smell out of gym clothes" with the vinegar soak, and
             # a shopping list is the wrong answer to a nose problem.
             "wash", "washed", "washing", "stink", "stinks", "stinks of", "smell", "smells",
             "smelly", "odour", "odor", "laundry", "sweat", "sweaty", "musty", "damp"),
      bias=1),

entry("running-load",
      (("keep getting injured", "injured again", "always injured", "injuries when i run",
        "injury when i run", "injury every time", "too much too soon", "increase my mileage",
        "increase my distance", "how much should i increase", "shin splints", "niggles"),
       ("run", "running", "mileage", "distance", "week", "again", "keep", "every time",
        "how much")),
      "It is nearly always the weekly distance going up too fast: keep the increase under "
      "about a tenth a week and hold it steady every fourth week. Run most of it easy enough "
      "to talk in full sentences, with one faster session and one longer run, and do two short "
      "strength sessions a week for calves, glutes and hips, which is what covers most running "
      "injuries. The same pain in the same spot three runs in a row is a physio visit, not a "
      "new pair of shoes.",
      avoid=("knee", "knees", "ankle", "achilles", "foot", "feet", "hip", "shoe", "shoes",
             "blister", "cramp", "side stitch"),
      bias=1),

entry("fasted-exercise",
      (("empty stomach", "fasted", "without eating", "no breakfast", "before breakfast",
        "without breakfast", "havent eaten"),
       ("exercise", "exercising", "work out", "working out", "workout", "run", "running",
        "train", "training", "gym", "cycle", "swim", "ok", "okay", "bad", "good", "fine")),
      "It is fine for anything up to about an hour: there is enough fuel stored to cover it, "
      "and it makes no difference to how much fat you burn over a day. Eat something small and "
      "mostly carbohydrate if you are going longer or harder than that, and always if you feel "
      "light-headed, because that is a sign to eat first rather than push on. Water matters "
      "more than food at that length of session.",
      avoid=("intermittent", "16:8", "5:2", "ramadan", "blood test", "operation", "surgery",
             "tablet", "medication", "insulin", "diabetes",
             # a medicine taken on an empty stomach is a question about the medicine: "is it ok to
             # take ibuprofen on an empty stomach" was answered with this card's "fine for
             # anything up to about an hour ... eat something small and mostly carbohydrate".
             "paracetamol", "ibuprofen", "nurofen", "painkiller", "painkillers", "aspirin",
             "co codamol", "co-codamol", "antibiotic", "antibiotics", "medicine", "medicines",
             "pill", "pills", "prescription", "capsule", "capsules", "dose", "mg",
             "tablet", "tablets", "medication", "insulin", "diabetes",
             # a tablet on an empty stomach is a stomach question, not a session: health.py's
             # medicine-with-food owns it
             "ibuprofen", "paracetamol", "aspirin", "naproxen", "painkiller", "painkillers",
             "medicine", "medicines", "antibiotic", "antibiotics", "steroid", "steroids",

             # "running" and "fast" are this key's words as well, and a phone battery is
             # not a session: "why is my phone running out of battery so fast" was
             # answered with the empty-stomach advice.
             "battery", "batteries", "phone", "iphone", "android", "on charge",
             "laptop", "running out", "runs out", "ran out",
             # a drink or a food named on an empty stomach is a question about that drink or
             # food, not about the session: "is it bad to drink coffee on an empty stomach" was
             # answered with this card's "fine for anything up to about an hour ... eat
             # something small and mostly carbohydrate".
             "coffee", "tea", "caffeine", "espresso", "latte", "green tea", "drink", "drinks",
             "drinking", "milk", "juice", "smoothie", "alcohol", "wine", "beer", "banana",
             "fruit", "yoghurt", "yogurt", "porridge", "toast", "breakfast food"),
      bias=1),

# --- how do i avoid hurting myself -------------------------------------------------------
# "how do i avoid hurting myself in the gym" and "how do i not get injured at the gym" were
# search hedges on main, while the rows beside them answered how often to train and whether to
# warm up: the prevention question had no owner, and it is the one people ask before they start.
entry("training-injuries",
      (("gym", "gyms", "lifting", "weights", "weight training", "workout", "workouts",
        "training", "run", "running", "runs", "jogging", "marathon", "parkrun", "squats",
        "deadlifts", "bench", "class", "classes", "exercise", "exercising"),
       ("injury", "injuries", "injured", "hurt", "hurts", "hurting", "hurt myself",
        "getting hurt", "pain", "pains", "ache", "aches", "aching", "niggles", "niggle",
        "safe", "safely", "avoid", "prevent", "prevention", "stop", "damage", "overdo",
        "overdoing", "too much", "strain")),
      "Most training injuries come from a jump in load, not bad luck: add about a tenth a week "
      "at most, to the weight or to the miles. Warm up for five minutes, take a lighter first "
      "set, and keep the form good on the last set or drop the weight - a sloppy last rep is "
      "where most of them happen. Never train through a sharp pain. If an ache lasts more than "
      "two weeks, or a joint gives way, see a physio rather than resting it for a month.",
      # the frequency and the warm-up are their own answers, and so is every named injury: this
      # row is only the prevention half, so the knee, the shin and the shoulder hand back
      avoid=("how often", "how many times", "every day", "rest day", "warm up", "warmup",
             "cool down", "stretch", "stretches", "stretching", "sore after", "dom",
             "doms", "supplement", "supplements", "protein", "creatine", "how much", "cost",
             "price", "membership", "gym membership", "equipment", "kit", "shoes", "buy",
             # "stop" in the key means "stop it happening", and "i stopped going to the gym"
             # is the other stop: quitting. The cancellation answer had that line before this
             # row existed, and the injury card took it (quality, 9411). Every form of leaving
             # stands this row down, whatever else the line says about the gym.
             "stopped going", "stopped training", "stopped the gym", "stop going",
             "quit", "quits", "quitting", "gave up", "give up", "packed it in",
             "cancelled", "cancels", "cancelling", "cancel my", "left the gym",
             # a nose that will not stop running is not a training load: "my nose wont stop
             # running" was answered with "add about a tenth a week". What runs here is a body
             # part or a fixture, and the list of them is the one the running rows already use.
             "nose", "noses", "eye", "eyes", "loo", "toilet", "cistern", "tap", "taps", "hose",
             "sink", "drain", "plughole", "shower", "bath", "boiler", "radiator", "heater",
             "dishwasher", "washing machine", "software", "app", "apps", "programme", "program",
             "campaign", "school run", "errand run",
             "knee", "knees", "shoulder", "shoulders", "back", "backs", "achilles", "shin",
             "shins", "shin splints", "plantar", "hamstring", "hamstrings", "elbow", "elbows",
             "wrist", "wrists", "ankle", "ankles", "hip", "hips", "groin", "sciatica",
             "cramp", "cramps", "blister", "blisters", "dizzy", "faint", "chest pain",
             # "weights" is this key's word and the loose plural also reads "weight", so
             # every way of saying "lose weight" plus a word from the second group landed
             # here: "how do i lose weight safely" was answered with a jump in training load,
             # "is it safe to lose weight quickly" with a warm-up and a physio, and "lose
             # weight without getting hurt" the same. Losing weight is its own question, so
             # every phrasing of it hands back, including the ones that say safe or hurt.
             "slimming", "weight loss", "lose weight", "losing weight", "lost weight",
             "lose the weight", "losing the weight", "lose a stone", "lose some weight",
             "lose a few pounds", "lose fat", "losing fat", "dropping weight",
             # "hurt" is in the key, so the phrases that mean something far worse are held
             # out by name: those lines belong to the crisis answer, never to a training tip
             "self harm", "self-harm", "kill myself", "cut myself", "want to die", "end it all",
             "end my life", "suicide", "suicidal", "not be here anymore",
             # "the toilet won't stop running" is a cistern and the run is the water: "running"
             # and "stop" are both in this row's key, so the fault in the house reached a
             # training tip. Every thing in a house that runs is held out by name.
             "toilet", "toilets", "loo", "loos", "cistern", "cisterns", "flush", "flushes",
             "flushing", "flush button", "ball valve", "fill valve", "flush valve", "tap",
             "taps", "faucet", "sink", "sinks", "drain", "drains", "plughole", "radiator",
             "radiators", "boiler", "washing machine", "dishwasher", "shower", "bath",
             "overflow", "overflowing", "pipes", "pipework"),
      # This row is the prevention half and nothing else, and an injury that has already
      # happened is the first-aid question: "i hurt myself at the gym" and "i hurt myself
      # running" were both answered with "add about a tenth a week at most", advice for
      # somebody who is not yet hurt. The tense is the test, so it cannot be an avoid word:
      # "hurting" folds onto "hurt", and an avoid phrase for it took the prevention lines that
      # are this row's whole point ("how do i avoid hurting myself in the gym" became a hedge).
      guard=lambda u: not _the_hurt_already_happened(u)),
]

# The injury said as something that has happened, in the past tense, by the person in the line:
# "i hurt myself", "i've hurt my back", "i got injured playing football". A prevention question
# asks how not to ("how do i avoid hurting myself", "how do i not get injured") and never has
# this shape, which is why the test is the wording around the verb and not the verb alone.
_ALREADY_HURT = re.compile(
    r"\b(?:i|ive|i've|i have|he|she|we|they)\s+(?:have\s+|has\s+|had\s+|got\s+|just\s+)?"
    r"(?:hurt|injured)\b")


def _the_hurt_already_happened(understood):
    """True when the line says the injury has already happened, not how to avoid one."""
    reading = understood if isinstance(understood, dict) else {}
    line = " ".join(str(reading.get("clean") or reading.get("text") or "").lower().split())
    return bool(_ALREADY_HURT.search(line))
