"""Sport: the rules people look up, coaching a kids' team, and getting started again.

Data only, on the merged `lookup.entry` contract: one entry per thing people ask, keyed by
the words that identify it (offside, a cricket wicket, coaching under-8s) and phrased the
way someone who plays would explain it — plainly, with the detail that actually confuses
people, and no rule-book quoting.

Rules entries answer the question asked and then give the one exception that people trip
over ("not offside from a throw-in"), because that is the bit the person is really stuck on.
"""
import re

from .lookup import A_HOUSE_WARMING_UP, A_WEATHER_ASK, PRESENT_ASK, entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("sport", "fitness")


def _not_a_line_about_a_box(understood):
    """False when the line the person typed names a cardboard box, not the sport.

    Used as the `start-boxing` guard. "boxing" and "boxes" share the loose form "box" in
    lookup's word forms, so an `avoid` entry cannot tell them apart: "boxes" in the avoid list
    reduces to the same "box" the key matched, and the row stood down on its own question
    ("how do i start boxing" became a shrug). The words the person typed are what separate the
    two senses, so the guard reads those: a box or a carton with no boxing word beside it is a
    container, and the row has nothing to say about it.

        how do i get rid of boxes     -> container (a moving answer)
        how do i open boxes           -> container
        how do i lift heavy boxes     -> container
        how do i start boxing         -> the sport: answered here
        how do i wrap my hands for boxing -> the sport
    """
    said = understood if isinstance(understood, dict) else {}
    text = str(said.get("text") or said.get("clean") or "").lower()
    if not re.search(r"\bbox(es)?\b|\bcartons?\b|\bcardboard\b", text):
        return True
    return bool(re.search(r"\bbox(ing|er|ercise)\b|\bgloves\b|\bspar\b|\bring\b|"
                          r"\bkickbox|\bmuay thai|\bclub\b|\bgym\b|\bclass", text))

def _not_a_timetable_that_runs(understood):
    """False when the line is a bus or a train service, not the exercise.

    `how-often-exercise` keys the word "run" and a "how often" tail, so a timetable question -
    "how often does the bus run", "how often do the buses run", "how often does the train run" -
    got "Three sessions a week is the number to aim for". No word list in the row can tell the two
    apart, because the word is the same word: the reading can (bot/understanding/topics.py gives
    "run" beside a service noun the travel topic), so the guard reads the topic instead.

        how often does the bus run      -> a service: the row stands down
        how often do the buses run      -> a service
        how often should i run          -> fitness: answered here
        how often should i run to lose weight -> fitness
    """
    said = understood if isinstance(understood, dict) else {}
    if str(said.get("topic") or "") != "geography-and-travel":
        return True
    text = str(said.get("text") or said.get("clean") or "").lower()
    return not re.search(r"\brun(s|ning)?\b|\bran\b", text)


# The men's football World Cup, one row per final: the year, the winner and the line people
# remember it by. Keyed by year, so "who won the world cup in 1966" and "who won in 2010" are the
# same lookup, and a year not in the table falls back to the record rather than a guess.
WORLD_CUP = {
    1930: ("Uruguay", "the first tournament, at home in Montevideo"),
    1934: ("Italy", "at home, in a tournament that was all knock-out rounds"),
    1938: ("Italy", "the last one before the war"),
    1950: ("Uruguay", "the one England did not enter and the United States beat England in"),
    1954: ("West Germany", "the final against Hungary that nobody expected them to win"),
    1958: ("Brazil", "the tournament a 17-year-old Pele won"),
    1962: ("Brazil", "in Chile"),
    1966: ("England", "at Wembley, 4-2 against West Germany after extra time, still their only one"),
    1970: ("Brazil", "the side with Pele, Jairzinho and Carlos Alberto, often called the best"),
    1974: ("West Germany", "at home, beating the great Netherlands side in the final"),
    1978: ("Argentina", "at home, the first of their three"),
    1982: ("Italy", "in Spain"),
    1986: ("Argentina", "Maradona's tournament, the Hand of God and the goal of the century"),
    1990: ("West Germany", "a final against Argentina settled by a penalty"),
    1994: ("Brazil", "on penalties against Italy in the United States, the first final decided that way"),
    1998: ("France", "at home, 3-0 against Brazil, with Zidane scoring two headers"),
    2002: ("Brazil", "in Japan and South Korea, Ronaldo's tournament"),
    2006: ("Italy", "on penalties against France in Berlin"),
    2010: ("Spain", "against the Netherlands in South Africa, Iniesta in extra time"),
    2014: ("Germany", "1-0 against Argentina in Brazil, Gotze in extra time"),
    2018: ("France", "4-2 against Croatia in Russia"),
    2022: ("Argentina", "against France on penalties in Qatar, Messi's tournament"),
}

# The plan for a race is the same shape at every distance, so the numbers are kept per distance
# in one place and the entry picks the one the line is about. Written the way a club coach would
# say it out loud: the week's structure first, then what the first-timer always gets wrong.
_PLAN_5K = (
    "Three runs a week gets most people to 5k in about eight weeks. If you cannot run five "
    "minutes yet, start with run-walk: one minute jogging, two walking, seven times. Once you can "
    "run 20 minutes without a break, make one run a week the long one and add five minutes to it "
    "until it is 30. Keep the other two short and slow enough to talk in sentences, take a rest "
    "day between runs, and keep the last week light.")
_PLAN_10K = (
    "Once you can run for half an hour without stopping, a 10k takes about ten weeks on three "
    "runs a week: one long run that grows by five to ten minutes a week, one easy run, and one "
    "with four or five short faster bursts inside it. Take the long run up to about 9km two weeks "
    "before the day, then ease off. Keep the weekly increase near 10% and put a rest day after "
    "the long one, since the distance is built in the recovery, not in the run.")
_TIME_MARATHON = (
    "A first marathon usually takes 3 hours 30 to 4 hours 45 minutes, and under 4 hours is a good club "
    "standard; under 3 hours 30 is quick. Most people run the first half too fast and lose twenty "
    "minutes in the last 10km, so aim for even splits and walk the water stations.")
_PLAN_HALF = (
    "Once you can run for an hour without stopping, a half marathon takes twelve to sixteen weeks "
    "on three or four runs a week: the long run grows by a kilometre or two a week up to about "
    "18km, three weeks before the day. The others stay easy, with one session of faster bursts "
    "if you have the energy. Nothing new on race day, and a first half is always better run a "
    "little slower than you think you can.")
_TIME_5K = (
    "A first 5k usually takes 30 to 40 minutes at a jog with walking breaks; the average parkrun "
    "time is about 28 minutes, and anything near 25 is quick. Walking the whole way is roughly 45 "
    "to 50 minutes, and most races allow far longer than that, so a first one is not something to "
    "worry about being slow at.")
_TIME_10K = (
    "A first 10k usually takes 55 to 70 minutes, and the average club runner does 50 to 55; under "
    "45 is quick. Walking breaks in the second half cost you less than you would think.")
_TIME_HALF = (
    "A first half marathon usually takes 2 hours 15 to 2 hours 30, and two hours is a good club "
    "standard; under 1 hour 45 is quick. Walking breaks early on cost you very little, and the "
    "cut-offs at most races are generous.")


# Each distance is its own pair of entries rather than one entry that reads the distance off the
# line. What an entry's words say it is about is how a follow-up is read: one entry listing 5k,
# 10k and half together told the rest of the bot that the last answer had been about all three,
# so "how long does it take to run a 5k" after a half marathon plan trimmed that plan's "twelve
# to sixteen weeks" down to a bare figure. A distance is a thing in its own right here, and the
# runner of a 5k and the runner of a half are not asking the same question anyway.
_RACES = (
    ("5k",
     ("5k", "5km", "5 k", "couch to 5k", "couch 5k", "c25k", "3 miles", "three miles"),
     _PLAN_5K, _TIME_5K),
    ("10k",
     ("10k", "10km", "10 k", "couch to 10k", "6 miles", "six miles"),
     _PLAN_10K, _TIME_10K),
    ("half",
     ("half marathon", "half-marathon", "half", "21k", "21km", "13 miles"),
     _PLAN_HALF, _TIME_HALF),
)
# Getting round it, or getting faster, are the same two words for every distance; a run that is
# merely reported ("i run 5k twice a week") has none of them and is left to the other entries.
_PLAN_WORDS = ("train", "training", "plan", "planning", "prepare", "preparing", "build up",
               "get ready", "ready", "start", "starting", "beginner", "couch", "c25k",
               "round", "finish", "complete", "improve", "faster", "signed up", "got a place",
               "first one", "want", "wanting", "into", "run", "running", "jog", "jogging",
               # the same readiness words as the ask list, because the key needs one of them
               # before the ask is read at all: "is it too soon to enter a half marathon" has
               # no other training word in it
               "too soon", "enter", "entering", "sign up", "signing up", "should i",
               "am i ready", "ready for", "if i can only", "can only run", "only run",
               "is it enough", "enough for me")
# The distance has to be joined by a word that asks for the doing of it: "how long is a 5k" and
# "how long does a 5k take" name the distance and want the distance or the time, and a training
# plan under either of those is the wrong reply.
_PLAN_ASK = ("train", "training", "plan", "planning", "prepare", "preparing", "build up",
             "get ready", "ready", "start", "starting", "beginner", "couch", "c25k", "want",
             "first", "help", "how do i", "how to", "round", "finish", "complete", "improve",
             "faster", "signed up", "got a place", "work up to",
             # a question about whether the distance is in reach is a question about the plan:
             # "should i run a half marathon if i can only run 5k", "am i ready for a half", "is
             # it too soon to enter a half". The distance is already in the line and what the
             # person wants is what it takes - which is what the plan answers, in the first
             # sentence. A verdict of my own ("that's your call") is worth nothing beside it.
             "should i run", "should i enter", "should i sign up", "should i do", "should i try",
             "too soon", "am i ready", "ready for", "if i can only", "can only run",
             "only run", "only manage", "is it enough", "enough for me")
# "I can run 5k but I want to get faster" is a speed question, not a beginner plan: the
# person already runs the distance, and "want" plus "run" plus "5k" was reaching the plan
# before the speed entry could answer it.
_PLAN_AVOID = ("far", "distance", "how fast", "pace", "what time", "good time", "faster",
                "quicker", "speed", "5k time", "10k time", "personal best",
                # a target time is a speed goal, not a first plan: "i want to break 25 minutes for
                # 5k" and "sub 2 for a half" are people who can already run the distance
                # a stated goal time is a speed answer, not a first plan: the people who say
                # "i want to break 25 minutes for 5k" already run the distance
                "want to break", "want a sub", "want to go under", "want to get under",
                "target time", "goal time",
                # a body that hurts is a question about the body, never a plan to start: someone
                # who says their knee hurts while running is not asking how to begin
                "knee", "knees", "hurt", "hurts", "hurting", "pain", "painful", "sore", "ache",
                "aches", "aching", "shin", "shins", "calf", "calves", "ankle", "ankles", "foot",
                "feet", "heel", "injury", "injured", "injur", "tight", "stiff", "blister")
# The other way round: how long the race takes to run, which is the first thing anyone wants to
# know before entering one.
_TIME_WORDS = ("how long does", "how long to run", "how long should it take", "how long will",
               "what time", "whats a good time", "what's a good time", "good time",
               "average time", "how fast", "how long should", "take to run", "take me to run",
               "aim for", "how many minutes", "how many hours",
               # "what is a good half marathon time" put three words between "good" and "time",
               # so the phrase "good time" never matched and the line was a punt. The words are
               # named on their own here; "good" and "time" both have to be there, because the
               # distance in the first group is what keeps the row off everything else.
               "a good time", "good", "time", "time for")
_TIME_AVOID = ("train", "training", "plan", "prepare", "preparing", "ready", "couch",
               "far", "distance", "length",
               # A finish time is what a fast runner has, not how to become one:
               # "how do i improve my 5k time" and "how do i get my 10k time down" were answered
               # with the average times, which is the fact, not the answer they asked for.
               "improve", "improving", "get faster", "go faster", "run faster", "faster",
               "quicker", "speed", "speed up", "get my time down", "bring my time down",
               "get quicker", "shave", "personal best", "pb",

               # a race time is for a race, not for coming back from being ill: "how long before
               # i can run again after flu" names no distance, but a line that names one and an
               # illness is still the back-to-running question.
               "flu", "ill", "illness", "cold", "fever", "sick", "temperature", "chest", "cough",
               "back to running", "get back to", "run again", "running again", "before i can run",
               "when can i run", "injury", "injured", "recovering", "recovery",
               # the bare "good" and "time" above answer a few lines that are not about a finish
               # time at all, and the distance in the key does not save them: a shoe, a start
               # time, a time of year and a recovery window were all answered with a race time.
               # The two words stay, because "what is a good half marathon time" has a word
               # between them and the phrase "good time" never matches it.
               "trainers", "trainer", "shoes", "shoe", "kit", "gear", "garmin",
               # what to wear on the day is the kit card's question, and "10k" plus "what do i
               # wear" was answered with how long a 10k takes
               "wear", "wearing", "what do i wear", "what to wear", "what should i wear",
               "clothes", "put on", "rain", "raining", "rainy", "wet", "layers", "socks",
               "what time do", "what time does", "what time are", "what time is the",
               "start time", "start times", "start line", "starts", "start",
               "time of year", "best time of year", "season", "which month",
               "give myself", "good idea", "worth it",
               # rest is its own question: "how long should i rest after a marathon" is a
               # recovery answer, and a finish time is not it
               "rest", "resting", "after a marathon", "after a half marathon", "after the race",
               "after a race", "sore", "much time should i give",
               # "good" is a word in every other question too, and a bare "good <thing> for a
               # marathon" is a question about the thing: stretches, a breakfast, whether the
               # race suits a beginner or a 40-year-old. A finish time is a confident wrong
               # answer to all four, and two of them were honest punts before.
               "stretch", "stretches", "stretching", "warm up", "warmup", "breakfast", "eat",
               "eating", "food", "fuel", "fuelling", "snack", "porridge", "toast", "carbs",
               "carb", "hydrate", "hydration", "for beginners",
               "first one", "good for me", "good for a beginner", "good for a first timer",
               "at 40", "at 50", "at 60", "at 70", "too old",
               "too young", "my age", "in my 40s", "in my 50s", "in my 60s",
               # "is a marathon good for a 40 year old" and "what is a good age to run a
               # marathon" are a shape and an age question, and both were answered with a
               # finish time for the 40-year-old they name and for the age the second one asks
               # about. "at 40" was here; the way people write it was not.
               "year old", "years old", "good age", "what age", "age to run", "age for",
               # The word "beginner" on its own is not the shape that was wrong: "whats a good
               # time for a 10k for a beginner" and "good time for a beginner at 10k" are the
               # beginner asking for the very card, and both were punted because the bare word
               # was in this list. "for beginners" is the shape that is not a finish time, and
               # it is kept.
               #
               # A good time to BUY is not a good finish time: "is now a good time to buy a
               # marathon place" was answered with 3 hours 30 to 4 hours 45.
               "buy", "buying", "bought", "place", "places", "entry", "enter", "entries",
               "sign up", "signed up", "registration", "ballot", "charity place"
               # a rest or a recovery is not a time for the race either: "how long should i rest
               # after a 5k" was told how long a 5k takes, when the figure wanted is the recovery
               "rested", "recover", "recovers", "recovering", "days off", "day off",
               "easy days")
# A distance is run. "How long does it take to walk three miles" and "how long does it take to
# drive 5k" are the same words with another way of covering the ground, and a race time for them
# is a wrong fact: the walking and driving entries answer those.
_RACE_MODE_AVOID = ("walk", "walking", "walked", "drive", "driving", "drove", "cycle",
                    "cycling", "bike", "bicycle", "swim", "swimming", "swam")
# "Half" on its own is a half marathon to a runner and half an hour to everyone else, and the
# plan for one is twelve to sixteen weeks long. The measuring half is not a race.
_HALF_AVOID = ("half an hour", "half hour", "half a mile", "half mile", "half a kilometre",
               "half a kilometer", "half term", "an hour and a half", "hour and a half",
               "half time", "halftime", "half a day", "half the",
               # A runner never says "half a" - it is "a half", "the half", "half marathon" -
               # so "half a" is a thing being halved, whatever comes after it: half a head of
               # cabbage, half a bag of rice, half a tin of tomatoes. "I've got half a head of
               # cabbage and nothing else planned" was reaching the half-marathon plan on "half"
               # and "planned", and was told how many weeks the training takes. The nouns are
               # not listed because the list would never be finished."""
               "half a", "half an", "half of",
               # A dose "in half" is not 13.1 miles: "im going to cut my insulin in half and see
               # how i go" holds the word half and the word how, so the half's card answered a
               # question about a prescription with the race distance. A medicine is not a
               # distance, so the words for what is taken stand the race rows down. The inhaler
               # is left out on purpose: "i take my inhaler before a run, how far is a half" is
               # a running line with a medicine in it, and the distance is what it asks.
               "my dose", "dose", "dosage", "insulin", "tablets", "pills", "capsules",
               "medication", "medicines")

# A clock hour after the word is the time of day, not 13.1 miles: "i start at half 5 now which is
# grim" and "my shift starts at half five" were both answered with the half marathon plan. The
# normaliser spells the figure out, so both arrive as "half five" and one list covers the typed
# and the spoken form.
_CLOCK_HALF = tuple(f"half {hour}" for hour in (
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12))


_SAID = ("clean", "norm_text", "text")


# The words that make "putting" a golf stroke rather than the everyday verb. The loose form
# matcher reads "put" as a form of "putting", so the word alone cannot tell them apart.
_GOLF_SAID = ("golf", "putt", "putts", "putted", "putting", "green", "greens", "hole", "holes",
              "tee", "handicap", "fairway", "bunker", "club", "clubs", "course", "courses",
              "irons", "driver", "slice", "hook", "swing")


# --- the goggles that fog ---------------------------------------------------
# "how do i keep my goggles from fogging" was answered by the car's fog lights, because fog is
# in that row's key and nothing else held the lens. The fix and the reason are two different
# answers, so a line that asks why gets the reason first.
_GOGGLES_FIX = (
    "Spit in each lens, rub it round and rinse it out, or wipe a drop of baby shampoo over the "
    "inside and let it dry - both leave a film the water cannot bead on. Then keep the seal "
    "still: a mask that is too tight, or goggles pressed on with the strap under a swim cap, "
    "squeezes out the warm air and fogs faster. Anti-fog sprays work for a session or two.")
_GOGGLES_REASON = (
    "The lens is colder than the warm, damp air coming off your face, so the water in that air "
    "condenses on it as droplets. Anything that keeps the two closer in temperature or puts a "
    "film on the inside stops the droplets forming - and a gap that lets the warm air out works "
    "better than a tighter seal.")
_SWIMMING_WORDS = frozenset((
    "swim", "swims", "swimming", "swimmer", "swimmers", "pool", "pools", "length", "lengths",
    "lane", "lanes", "dive", "dives", "diving", "snorkel", "snorkelling", "lido", "open water",
    "underwater", "wetsuit",
))


def the_goggles_are_for_swimming(understood):
    """True when the goggles in the line are the ones in a pool.

    "my goggles keep fogging up" is pinned to the glasses card by a test, so a bare statement
    about goggles stays where it is: this row takes a swimming word or an explicit how or why.
    """
    words = set((understood or {}).get("words") or ())
    if words & _SWIMMING_WORDS:
        return True
    said = ((str((understood or {}).get("clean") or "")) + " " +
            str((understood or {}).get("plain") or "") + " " +
            str((understood or {}).get("text") or "")).lower()
    for word in _SWIMMING_WORDS:
        if word in said:
            return True
    asks = set((understood or {}).get("asks") or ())
    return bool(asks & {"how", "what", "why"})


def _goggles_fog(memory, understood):
    said = str((understood or {}).get("text") or "").lower()
    asks = set((understood or {}).get("asks") or ())
    if "why" in said or "why" in asks:
        return _GOGGLES_REASON + " " + _GOGGLES_FIX
    return _GOGGLES_FIX


def _a_put_is_not_a_putt(understood):
    """False when the line's "put" is the everyday verb and no golf word is beside it.

    "putting" is one of the golf row's second signals, and the matcher reads "put" as a form of
    it, so "what do i put in the bathroom to stop condensation" met the row's own "stop" and was
    answered with the aim-and-tempo card. The two words are spelled the same, so this reads what
    else is in the line instead of the word: a golf word keeps the row, and the verb stands it
    down. "how do i improve my putting" and "my putting is awful" are still the row's lines,
    because "putting" is in them and "put" is not.
    """
    said = " ".join(str((understood or {}).get(key) or "") for key in _SAID).lower()
    words = " ".join(said.replace("-", " ").split()).split()
    if any(word in _GOLF_SAID for word in words):
        return True
    return "put" not in words


def _a_clock_half_is_not_the_race(understood):
    """False when "half" in the line is a clock hour and the race is not named at all.

    A clock hour is not 13.1 miles, and it cannot be fenced off with an avoid word: the avoid
    works on the whole line, so "i start at half 5 and ive signed up for a half marathon" lost
    its plan as well. Naming the race is the difference, so the guard reads both.
    """
    said = " ".join(str((understood or {}).get(key) or "") for key in _SAID).lower()
    said = " ".join(said.replace("-", " ").split())
    if "half marathon" in said:
        return True
    return not any(f" {hour} " in f" {said} " for hour in _CLOCK_HALF)

# A line that names two distances is asking about the longer one: "i want to go from 5k to 10k"
# is a 10k plan, and the 5k in it is where the person is starting from. Each distance stands
# aside for the next one up, so the destination is what answers.
# A half is 13.1 miles, and "how far is a half marathon" was answered with the marathon's 26.2,
# because the half's line holds the word marathon and main's marathon entry keys on it.
_HALF_DISTANCE = entry(
    "race-distance-half",
    (("half marathon", "half", "13.1", "13 1 miles", "21.1", "21 1 km"),
     ("far", "long", "miles", "km", "kilometres", "kilometers", "distance", "how", "length",
      # a comparison between two distances was reaching nothing at all: "is a marathon longer
      # than a half marathon" is answered by saying how far each one is, and the half's card
      # gives both. The longer-distance words are the ask here, not a training word.
      "longer", "longer than", "further", "further than", "shorter", "shorter than")),
    "A half marathon is 13.1 miles, or 21.1 kilometres: half the marathon distance, which is why "
    "the number looks odd. A first one usually takes 2 hours 15 to 2 hours 30, and most plans "
    "build up to it over twelve to sixteen weeks.",
    ask=("far", "long", "miles", "km", "kilometres", "kilometers", "distance", "length", "how",
         "longer", "longer than", "further", "further than", "shorter", "shorter than"),
    avoid=(("train", "training", "plan", "prepare", "preparing", "build up", "ready", "couch",
            # a line that compares the two races is the marathon card's, which has both figures
            "longer than", "which is longer", "how much longer", "difference", "versus",
            "pace", "time", "good time", "faster",
            # a how-to about a half is not a question about how far it is: tapering, recovering,
            # shoes and fuel are all other answers, and a bare "how" in the ask let them in.
            "taper", "tapering", "recover", "recovery", "shoes", "sore", "injury", "fuel",
            "eat", "eating", "drink", "drinking", "blister", "weather") + _HALF_AVOID))

_LONGER_AVOID = {
    "5k": ("10k", "10 km", "10km", "half marathon", "half"),
    "10k": ("half marathon", "half"),
    "half": (),
}

_RACE_ENTRIES = tuple(
    made
    for _name, _phrases, _plan, _time in _RACES
    for made in (
        entry("race-plan-" + _name, (_phrases, _PLAN_WORDS), _plan, ask=_PLAN_ASK,
              avoid=(_PLAN_AVOID + _RACE_MODE_AVOID + _LONGER_AVOID[_name]
                     + (_HALF_AVOID if _name == "half" else ())),
              guard=(_a_clock_half_is_not_the_race if _name == "half" else None),
              bias=1),
        # A time question names its distance, so nothing else may answer it: back-to-running
        # keys "how long" and "run" with bias 4, and it was taking "how long does it take to run
        # a 5k" and answering it with the cold-and-flu rule. The distance word in the key is what
        # the bias is for, and the illness words above keep that entry's own lines.
        entry("race-time-" + _name, (_phrases, _TIME_WORDS), _time,
              avoid=(_TIME_AVOID + _RACE_MODE_AVOID + _LONGER_AVOID[_name]
                     + (_HALF_AVOID if _name == "half" else ())),
              guard=(_a_clock_half_is_not_the_race if _name == "half" else None),
              bias=10))
) + (entry("first-game-after-a-break",
      (("five a side", "5 a side", "five-a-side", "football", "soccer", "rugby", "hockey",
        "basketball", "netball", "badminton", "tennis", "squash", "rounders", "cricket"),
       ("first time in years", "first time in ages", "first game", "first match", "first time",
        "havent played", "haven't played", "not played for", "not played in", "back to football",
        "back to playing", "playing again", "start playing again", "getting back into",
        "how do i not get injured", "not get injured", "avoid injury", "avoid getting hurt",
        "dont get hurt", "don't get hurt", "not hurt myself", "sore after", "ache after",
        "will i be sore", "unfit", "out of shape")),
      "Do less than you want to: play twenty minutes of it rather than the whole hour, and warm "
      "up for five with a jog and a few short sprints before the first ball, because the sprint "
      "cold is what goes. Boots with grip for the surface, water at the side, and expect to ache "
      "for two days afterwards - that soreness is normal and walking helps it. If a joint swells "
      "or gives way, or a pain is still there after a fortnight, that is a physio rather than "
      "another game.",
      # the warm-up, the boots and the fitness are their own answers
      avoid=("warm up", "warm-up", "warming up", "warmup", "boots", "boot", "astroturf",
             "astroturf", "studs", "moulded", "how fit", "get fit", "lose weight",
             "how often", "how many times a week", "offside", "rules", "how long is a game",
             "world cup", "watch", "on tv"),
      bias=2),
     entry("race-day-kit",
      (("10k", "5k", "parkrun", "park run", "half marathon", "marathon", "marathons", "race",
        "race day", "sportive", "triathlon", "cross country"),
       # The weather is left out of this group on purpose: "a charity 10k in july and it will be
       # hot, what should i wear" is the hot-day clothes answer, and "10k on sunday and it might
       # rain" is the rain kit's, both of them more specific than a race-day list. The race is
       # named and the ask is what to wear; that is enough.
       ("wear", "wearing", "kit", "clothes", "what do i put on", "put on", "what should i wear",
        "what to wear", "socks", "layers")),
      "Nothing new on race day: the socks and shoes you did your long runs in, and dress for ten "
      "minutes in - a thin wicking base layer, a warm thin layer over it and a windproof shell you "
      "can tie round your waist, a cap for rain or sun, gloves for the first two miles and a "
      "waterproof jacket if it is really coming down, because you warm up two or three miles in "
      "and one layer fewer than feels right at the door is usually the right count. Vaseline on "
      "the nipples and inner thighs, safety pins for the number, a dry top and a bin liner for "
      "your bag at the finish, and a warm layer to pull on within ten minutes of stopping, which "
      "is when the cold really lands.",
      # how long it takes, how to train for it and what to eat round it are other rows
      avoid=("how long", "how fast", "what time", "what pace", "pacing", "split", "splits",
             "finish time", "training plan", "how many weeks", "how often", "bin bag",
             "lose weight", "taper", "carbs", "carb load", "what should i eat", "fuel",
             # which sock to put on with what is the sock's own card, and it answers the
             # question asked rather than adding a sock to the whole race-day list
             "what socks", "which socks", "socks for", "socks with", "socks to",
             # a hot day has its own answer, and a race-day list with warm layers in it is
             # wrong on it: "a charity 10k in july and it will be hot, what should i wear"
             "hot", "sun", "sunny", "heat", "heatwave", "boiling", "30 degrees", "35 degrees"),
      bias=2),
     _HALF_DISTANCE,
     # The full race had a distance card and a training card but no time card, so "what is a good
     # time for a marathon" was a search hedge while the 5k, the 10k and the half all answered.
     # It is not in _RACES above because that would make a second training card as well, and
     # "how do i train for a marathon" is marathon-training's line.
     entry("race-time-marathon",
           (("marathon", "26.2", "26 2 miles", "42.2", "42 2 km"), _TIME_WORDS),
           _TIME_MARATHON,
           avoid=_TIME_AVOID + _RACE_MODE_AVOID, bias=10))

# A knee can be noisy or painful, and the two get different advice: a noise on its own usually
# needs nothing doing, while pain on the stairs is a muscle job. Two entries, and the noisy one
# holds its words out of the pain entry so "clicks on the stairs" is not answered as pain.
_NOISY = ("click", "clicks", "clicking", "clunk", "clunks", "clunking", "grind", "grinds",
          "grinding", "creak", "creaks", "creaking", "pop", "pops", "popping", "crack", "cracks",
          "cracking", "noisy", "noise", "snapping")
_HURTS = ("hurt", "hurts", "hurting", "pain", "painful", "ache", "aches", "aching", "sore",
          "swollen", "swelling", "sharp", "stiff")
_KNEE_PAIN = ("Pain at the front of the knee on stairs is the kneecap being pulled off line by "
              "weak or tight muscles around it, which is common in new runners and in people who "
              "sit all day. Three times a week do sit-to-stands, step-ups and wall sits, and ease "
              "off hills and deep squats for a fortnight. See a physio if it swells, locks, or the "
              "knee gives way under you.")
_KNEE_NOISY = ("A knee that clicks or grinds without hurting is usually harmless - it is the "
               "kneecap sliding over the joint, and sometimes the gas in the joint fluid popping. "
               "It needs nothing doing. If the noise comes with pain or swelling, treat it as pain: "
               "strengthen the muscles around the knee with sit-to-stands, step-ups and wall sits "
               "three times a week, and see a physio if it swells, locks or gives way.")


# The same table read the other way round: a country and the years it won, so "when did england
# win the world cup" is answered from the winners rather than from a second list. West Germany
# counts as Germany, which is how people ask it now.
def _win_years():
    found = {}
    for year, (winner, _note) in WORLD_CUP.items():
        found.setdefault(winner.lower().replace("west ", ""), []).append(year)
    return {name: sorted(years) for name, years in found.items()}


WIN_YEARS = _win_years()


def _listed(years):
    """1966; 1958 and 1962; 1958, 1962 and 1970."""
    said = [str(year) for year in years]
    return said[0] if len(said) == 1 else ", ".join(said[:-1]) + " and " + said[-1]


def _world_cup(memory, understood):
    """The winner of the year the line names, the years one country won, or the record."""
    clean = understood.get("clean") or ""
    years = [int(year) for year in re.findall(r"\b(19\d\d|20[0-2]\d)\b", clean)]
    for year in years:
        if year in WORLD_CUP:
            winner, note = WORLD_CUP[year]
            return "In %d it was %s, %s." % (year, winner, note)
    if years:
        return ("The men's World Cup has been held every four years since 1930, apart from 1942 "
                "and 1946 for the war, so %d is not a tournament year." % years[0])
    lowered = clean.lower()
    for country in sorted(WIN_YEARS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(country) + r"\b", lowered):
            won = WIN_YEARS[country]
            how_many = {1: "once", 2: "twice", 3: "three times", 4: "four times",
                        5: "five times"}.get(len(won), "%d times" % len(won))
            return "%s have won the men's World Cup %s: %s." % (
                country.title(), how_many, _listed(won))
    # No invitation at the end: a bare "1966" in the next turn is read as a new line by the
    # understanding engine and gets an ack, so a promise to answer it would be one the bot
    # cannot keep. The record itself is the answer.
    return ("Brazil have won it five times (1958, 1962, 1970, 1994, 2002) and Germany and Italy "
            "four each; Argentina won in 2022 and France in 2018, England in 1966.")


_NOT = ("not", "no", "dont", "doesnt", "didnt", "isnt", "never", "without", "hardly")


def _noisy_knee(memory, understood):
    """A noise on its own is nothing to fix; a noise that hurts is the pain question."""
    words = set(understood.get("words") or [])
    hurts = bool(words & set(_HURTS)) and not words & set(_NOT)
    return _KNEE_PAIN if hurts else _KNEE_NOISY


_PROTEIN_TRAINING = ("muscle", "muscles", "lifting", "lift", "weights", "weight training",
                     "gym", "bulking", "bulk", "bodybuild", "bodybuilding", "stronger",
                     "training", "workout", "workouts", "gains", "protein shake", "protein shakes",
                     "protein powder", "whey")


def _protein(memory, understood):
    """Two different numbers: the everyday target, and the one for building muscle.

    "how much protein do i need" is the maintenance figure, about 0.75g a kilo, and 55g a day is
    the honest answer for an ordinary person. "how much protein do i need to build muscle" is a
    training question, and the maintenance number is too low for it, so the two are said
    separately and the one the person asked for comes first.
    """
    text = ((understood.get("clean") or "") + " " + (understood.get("norm_text") or "")).lower()
    if any(word in text for word in _PROTEIN_TRAINING):
        return ("To build muscle, aim for about 1.6-2.2g of protein for each kilo you weigh - "
                "roughly 110-155g a day at 70kg - spread over three or four meals of 25-40g: "
                "chicken, tuna, eggs, Greek yoghurt, lentils or tofu. There is no need for powder "
                "if meals get you there, and for healthy kidneys that amount is not a risk. "
                "Protein without hard training does little, so the lifting matters as much as "
                "the food.")
    return ("Aim for about 0.75g of protein for each kilo you weigh - roughly 55g a day at 75kg - "
            "which is a palm-sized portion at each meal: eggs or yoghurt at breakfast, beans, tuna "
            "or chicken at lunch, fish, lentils or mince at dinner. Lifting weights to build "
            "muscle takes it higher, to about 1.6g per kilo and over. Most people in the UK "
            "already eat enough without powder.")


_CALF_STRETCH = ("For the calf, stand with both hands on a wall, one leg back with the heel flat "
                 "on the floor and the back knee straight, and lean in until you feel it pull: "
                 "hold 30 seconds, three times each side. Then bend the back knee slightly, "
                 "keeping the heel down, for the lower calf. Stretch after you run rather than "
                 "before, when the muscle is warm, and breathe out into the stretch instead of "
                 "bouncing.")
_HAMSTRING_STRETCH = ("For the hamstring, sit or stand with one heel on a low step, keep that leg "
                      "straight and hinge forward from the hips with a flat back until you feel the "
                      "pull behind the thigh - hold 30 seconds, three times each side. No bouncing "
                      "and no reaching for your toes with a round back. Do it after the run, when "
                      "the muscle is warm.")
_QUAD_STRETCH = ("For the front of the thigh, the quad: stand tall, take one foot behind you and "
                 "pull the heel up towards your bottom with the knee pointing down at the floor and "
                 "your hips level, and hold 30 seconds each side - a hand on a wall or a chair for "
                 "balance. If the pull is at the back of the thigh instead, that is the hamstring: "
                 "heel on a low step, leg straight, hinge forward from the hips with a flat back, "
                 "30 seconds each side. Both after the exercise, when the muscle is warm.")
_WHOLE_LEG_STRETCH = ("For the whole leg, the calf first: hands on a wall, one leg back with the heel "
                      "flat on the floor and that knee straight, lean in for 30 seconds, three times "
                      "each side. Then the hamstring: one heel on a low step, that leg straight, hinge "
                      "forward from the hips with a flat back, 30 seconds each side. Both after the "
                      "exercise, when the muscles are warm, not before.")


def _stretch(memory, understood):
    """The stretch for whichever muscle the line names, asked before or after when it is."""
    words = set(understood.get("words") or ())
    if words & {"hamstring", "hamstrings"}:
        body = _HAMSTRING_STRETCH
    elif words & {"quad", "quads", "thigh", "thighs"}:
        # the front of the thigh is the quad; the hamstring is behind it, and the two are not
        # the same stretch - a line that names the thigh gets the quad, with the hamstring named
        body = _QUAD_STRETCH
    elif words & {"leg", "legs"}:
        # "my legs are tight" is the whole lower limb, so the calf comes first, then the hamstring
        body = _WHOLE_LEG_STRETCH
    else:
        body = _CALF_STRETCH
    if "before" in words and "after" in words:
        return ("After, when the muscle is warm, not before: holding a stretch on a cold muscle "
                "pulls it more than it loosens it, and five minutes of easy running is a better "
                "warm-up than any stretch. " + body)
    return body


# A *report* that somebody else is taking running up is not a request for the plan "you"
# should follow: "my husband is getting back into running" is news, and main echoes it as news.
# Only the report shapes are spelled out, and only with the word that makes them a report
# ("my husband is", "she is getting"), because the same person in the line can still be part
# of an ask: "my wife says i should get back into running" and "i want to get back into
# running with my friend" are both the plan being asked for, and neither has one of these
# shapes. Both spellings are listed: the reading layer writes "shes" out for some lines and
# leaves it whole for others, and an avoid phrase only stands a line down while the words are
# there to match.
_REPORTED = ("my husband is", "my wife is", "my partner is", "my boyfriend is",
             "my girlfriend is", "my son is", "my daughter is", "my friend is",
             "my brother is", "my sister is", "my mum is", "my mom is", "my dad is",
             "he is getting", "she is getting", "they are getting",
             "hes getting", "shes getting", "theyre getting",
             "he is back", "she is back", "hes back", "shes back")
# --- what the bot cannot look up --------------------------------------
# The one honest line for a score, and a pass when the line is about a season long gone: "who won
# the world cup in 1966" is history, and "I can't see last night's scores" is a wrong answer to it.
_RESULTS_REPLY = (
    "I can't see last night's scores or the table - I have no way of looking them up, so I would "
    "only be guessing. A scores app or the club's own page will have it in a second. If you tell "
    "me the result I can talk it through with you."
)
_YEAR = re.compile(r"(19|20)\d\d")


# The named competitions, split by what kind they are, so the format answer can tell a
# comparison of two of a kind from a question about the league-versus-cup idea itself. "whats the
# difference between the fa cup and the league cup" is two knockouts and the premier league
# against the champions league is two tables: the answer below would be confidently about a
# different difference, so those lines pass. A single league on its own ("how does the champions
# league work") keeps its answer, because that is the line main answers.
_CUPS = ("fa cup", "league cup", "carabao", "world cup", "scottish cup", "copa del rey",
         "fa trophy", "playoff final", "play off final")
_LEAGUES = ("premier league", "champions league", "europa league", "conference league",
            "la liga", "serie a", "bundesliga", "ligue 1", "the championship", "county championship")
_LEAGUE_AND_CUP = (
    "A league is decided over a season: every team plays the others home and away, and the table "
    "decides who wins, so one bad afternoon only costs you three points. A cup is knockout: you "
    "play once, and losing means you are out, which is why a lower team can beat a big one on the "
    "day. That is how the same club can be top of the league and out of the cup in the same week."
)


def _league_and_cup(memory, understood):
    """The format answer, or nothing when the line compares two competitions of the same kind."""
    said = (str(understood.get("clean") or "") + " " +
            " ".join(str(word) for word in (understood.get("words") or []))).lower()
    cups = [name for name in _CUPS if name in said]
    leagues = [name for name in _LEAGUES if name in said]
    if len(cups) + len(leagues) > 1:
        return None
    if cups:
        return None
    return _LEAGUE_AND_CUP


def _cant_see_the_score(memory, understood):
    """The honest line about a score, or nothing when the line asks about another season."""
    said = " ".join(str(word) for word in (understood.get("words") or []))
    said = said + " " + str((understood or {}).get("clean") or "")
    if _YEAR.search(said):
        return None
    return _RESULTS_REPLY

_BATTING_WORDS = ("bat", "batting", "batsman", "batter", "runs", "drive", "pull", "cut shot",
                  "shot", "shots", "hit")
_BOWLING_WORDS = ("bowl", "bowling", "bowler", "spin", "spin bowling", "seam", "swing", "yorker",
                  "line and length", "wickets", "take wickets")


_BASKETBALL_DRIBBLE_WORDS = ("dribble", "dribbling", "dribbled", "handle", "handles",
                              "ball handling", "ball-handling", "crossover", "bring the ball up",
                              "handling the ball", "handle the ball")


def _basketball_better(memory, understood):
    """Getting better at basketball, opening with the part the line names.

    "how do i get better at dribbling a basketball" was answered with three sentences about
    shooting, because the row only knew shooting. A line that says dribble gets the dribble.
    """
    words = set(str(word).lower() for word in (understood.get("words") or []))
    words.update(str((understood or {}).get("clean") or "").lower().split())
    # the words as words and as one string: "ball handling" is two tokens, so the set alone
    # missed it and the line got the shooting card
    flat = " ".join(str((understood or {}).get("clean") or "").lower().split())
    if any(word in words or (" " in word and word in flat)
           for word in _BASKETBALL_DRIBBLE_WORDS):
        return ("Dribble low and hard with your fingertips, head up, and change pace rather than "
                "doing tricks: a slow dribble that suddenly speeds up beats a crossover nobody "
                "falls for. Pound the ball 50 times with each hand standing still, then walk the "
                "length of the court changing hands every three dribbles, then do it at a jog. "
                "Keep your body between the ball and the defender, and never pick the ball up "
                "until you have decided what you are doing with it.")
    return ("Shooting is one repeatable motion: elbow under the ball, a small dip, and push up "
            "from the legs so the ball leaves your fingertips with backspin. Start a metre from "
            "the hoop and make 20 in a row before you step back, then finish every session with "
            "20 free throws while you are tired, because that is when games are decided. Keep the "
            "guide hand off the ball and do not let the shooting elbow drift out.")


# The words that say the person is asking about the game rather than about a thing in it: how to
# hold it, how to get better, what to practise. A line with one of these is about the game even
# when the reading cannot settle the word "bat" from the rest of the sentence.
# The words that are the bat itself, so a guard about the bat has something to guard.
_A_BAT_WORD = frozenset("bat bats batting batsman batsmen batter batters".split())

_ABOUT_THE_GAME = frozenset("""better improve improving practise practice technique coach
    coaching training nets net batting bowling swing grip stance footwork drills drill
    warm-up warmup season match club league innings""".split())


def _not_the_coach_of_a_team(understood):
    """False when the "coach" in the line is the person who takes the session.

    "how do i coach a under 9s football team" matched this row on "football team" and was told
    which team to support. A coach is a vehicle, a sofa and a person who runs the sessions, and
    the rest of the line says which one (bot/understanding/senses.py).
    """
    sense = (understood or {}).get("sense") or {}
    return sense.get("coach") != "teacher"


def _a_bat_that_is_not_the_game(understood):
    """False when the "bat" in the line is not the game the row is about.

    "my bat is broken" matched this row on the single word "bat" - which folds with "batting" in
    the first group and "batsman" in the second - and was answered with a card of batting drills
    for a bat that is in two pieces. Nothing in the line says the game: it says a thing and that
    the thing is broken. The reading settles the word here rather than the row guessing
    (bot/understanding/senses.py), and an animal in the loft is the other sense of it, so a line
    about a bat that flew in is not the game either.
    """
    sense = (understood or {}).get("sense") or {}
    if sense.get("bat") == "animal":
        return False
    if sense.get("bat") == "sport":
        return True
    words = {str(word).lower() for word in ((understood or {}).get("words") or ())}
    words.update(str((understood or {}).get("clean") or "").lower().split())
    # A line with no bat in it cannot be the bat in the loft: "how do i bowl a yorker" says a ball
    # and a delivery and no bat at all, and it was stood down for not saying what the game is.
    if not (words & _A_BAT_WORD):
        return True
    return bool(words & _ABOUT_THE_GAME)


def _the_game_and_not_another(understood):
    """The row's one guard: not the other bowl game, and the word is the game or the line is."""
    return _not_another_bowl_game(understood) and _a_bat_that_is_not_the_game(understood)


def _not_another_bowl_game(understood):
    """False when the line says bowl and nothing else about cricket.

    A bowl is in three games and more than one of them gets asked about here. "bowls" is lawn
    bowls, "tenpin bowling" and a cracked bowling ball are the alley, and "how do i get better
    at bowling" names no game at all - only the word "bowling" separates those from the half of
    cricket this row is for, and "bowling" is in this row's own key, so a line with no cricket
    word in it matched and was given the cricket card. So: if the line says bowl and no cricket
    word is beside it, the row stands down and another card (or the honest shrug) takes it.
    """
    text = " ".join(str((understood or {}).get("clean") or " ".join(
        (understood or {}).get("words") or [])).lower().split())
    words = set(re.findall(r"[a-z0-9']+", text))
    if not (words & _BOWL_WORDS):
        return True
    return any(word in words or (" " in word and word in text)
               for word in _CRICKET_WORDS)


# the words that only say that a ball is being bowled, in any of the games that bowl one
_BOWL_WORDS = frozenset((
    "bowl", "bowls", "bowling", "bowled", "bowler", "bowlers", "bowling's"))


_CRICKET_WORDS = frozenset((
                   "cricket", "wicket", "wickets", "over", "overs", "nets", "net",
                   "batsman", "batsmen", "batter", "batters", "batting", "bat",
                   "test", "t20", "ashes", "innings", "stumps", "stump", "pitch", "slip",
                   "cover", "midwicket", "spinner", "spinners", "spin", "seam", "seamer",
                   "keeper", "keeper's", "yorker", "bouncer", "crease", "googly", "googlies",
                   "no ball", "no balls", "wicketkeeper",
                   "off stump", "leg stump", "long on", "mid off", "cover drive",
                   "bowling action", "spin bowling", "third man", "fine leg",
                   "short leg")) - _BOWL_WORDS


def _cricket_better(memory, understood):
    """Getting better at cricket, opening with the half the line actually names.

    "how do i get better at cricket" names no half of the game, and batting is the one most
    club players mean, so that is the lead. A line that says bowling gets the bowling part
    first: "how do i improve my bowling" was answered with three sentences about batting.
    """
    words = set(str(word).lower() for word in (understood.get("words") or []))
    words.update(str((understood or {}).get("clean") or "").lower().split())
    batting = any(word in words for word in _BATTING_WORDS)
    bowling = any(word in words for word in _BOWLING_WORDS)
    if bowling and not batting:
        return ("Aim at the top of off stump over and over rather than trying a new ball each "
                "over: mark a target on the pitch and land 10 out of 12 before you change "
                "anything. Run in the same way every time, keep the front arm up and the head "
                "still, and use the crease - wide of it for a ball going across, close to it for "
                "one coming in. A wicketkeeper or a mate behind the stumps tells you more than a "
                "camera does.")
    if batting:
        return ("Batting is mostly watching and waiting: watch the ball out of the bowler's hand, "
                "keep your head still, play straight and leave anything outside off you do not "
                "have to hit. Give every net session a purpose - 20 drives, 20 forward defences, "
                "20 pulls - against a bowler better than the ones you face on a Saturday. Ten "
                "minutes of throw-downs a day beats an hour of slogging.")
    return ("Batting is where most club players lose their place, so start there: watch the ball "
            "out of the bowler's hand, keep your head still, play straight and leave anything "
            "outside off you do not have to hit. Then the other half - aim at the top of off "
            "stump over and over rather than trying a new ball every over - and catch 50 high "
            "balls a week, because catches win more club games than runs do.")


# "Study" and "studs" share the loose form "stud", so a line about revision reached the football
# boot: "how do i remember what i study" was told which sole suits wet grass. In an avoid list the
# word "study" collides the other way and takes every "studs" line with it, so the two readings are
# told apart by the words as typed, one exact word at a time.
_STUDY_WORDS = frozenset("""study studies studying studied student students revise revising
revision revise exams exam mock mocks homework coursework essay essays dissertation notes
memorise memorising remember remembering learn learning learnt grade grades semester""".split())


def _not_a_study_line(understood):
    """False when the line is about revision: a pass on the words, not on their loose forms."""
    words = {str(word).lower() for word in (understood.get("words") or ())}
    return not (words & _STUDY_WORDS)


def _football_boots(memory, understood):
    """The surface picks the boot; a line about fit or a new pair opens with the fit instead."""
    text = str(understood.get("clean") or " ".join(understood.get("words") or [])).lower()
    surface = ("The surface picks the boot: moulded studs (FG) on grass, screw-in studs (SG) when "
               "it is wet and soft, astro or turf trainers (TF) on 3G and 4G, flat indoor shoes for "
               "a hall. ")
    grip = ("Astro boots on wet grass give almost no grip, which is how ankles turn.")
    fit = ("Go by fit: try them on in the afternoon with match socks on, leave a thumb's width at "
           "the toe, and go half a size up for a child whose feet are still growing. ")
    new = ("Wear a new pair around the house an evening at a time and never in a match first; a "
           "leather boot softens within a week. ")
    # "where can i get cheap ones" is a shop question, and the surface is only half its answer:
    # the pair a child grows out of in a season is the one not to spend on, and a club's kit sale
    # is where the near-new ones go.
    where = ("Buy them anywhere that lets you try them on: a sports shop, a supermarket's own "
             "brand, the big online retailers, or a club's second-hand kit sale, where "
             "out-grown pairs go for a few pounds. ")
    cheap = ("Do not spend much on a child's boots - feet grow a size a season - but do buy the "
             "right sole for the pitch, because a cheap boot in the wrong stud is worse than no "
             "stud at all. ")
    # "when should i buy football boots" is a calendar question about boots, and the answer is the
    # end of a season or the week before pre-season, not the January sales on winter coats.
    when = ("Boots are cheapest at the end of a season, in April to June, and again when a new "
            "colourway comes out and last year's drop; for a child the club's kit sale just before "
            "the season starts is the moment, because that is when the out-grown pairs come in. ")
    if any(word in text for word in ("when", "what month", "which month", "best time", "time to buy",
                                     "month")):
        return when + surface
    if any(word in text for word in ("cheap", "cheaper", "cheapest", "afford", "budget", "price",
                                     "prices", "cost", "costs", "spend", "sale", "second hand",
                                     "secondhand", "where", "shop", "shops", "store", "online",
                                     "order", "buy from")):
        return where + cheap + surface + fit
    if any(word in text for word in ("tight", "small", "smaller", "size", "sizing", "wide",
                                     "narrow", "blister", "blisters", "hurt", "hurts", "rubbed",
                                     "10 year old", "9 year old", "8 year old", "11 year old",
                                     "12 year old", "13 year old", "14 year old", "growing")):
        return fit + surface + grip
    if any(word in text for word in ("break in", "breaking in", "break them in", "new boots",
                                     "new pair", "stiff")):
        return new + surface + grip
    return surface + grip + " Try them on with match socks and leave a thumb's width at the toe."


# A parent asks after a child the other way round from a report: "is my son getting better at
# running" puts the person first, which the list above does not catch, so the training entry
# answered with the asker's own plan. These are the inverted forms for its avoid list only.
_ASKED_AFTER = ("is my son", "is my daughter", "is my child", "is my partner", "is my wife",
                "is my husband", "is my boyfriend", "is my girlfriend", "is my friend",
                "is my brother", "is my sister", "is my mum", "is my mom", "is my dad",
                "is he", "is she", "is your son", "is your daughter", "how is my",
                "how are my", "are my kids", "are my children", "are they getting")


# A pitch or a court asked about its size is a question about the ground, not the game: "how
# big is a football pitch" got the length of a match, and "how big is a tennis court" got
# nothing. One table keyed by the surface, so every way of asking about a ground is one answer
# each and a new ground is one more line.
GROUNDS = (
    (("football pitch", "football field", "soccer pitch", "football ground"),
     "A full-size football pitch is about 105 metres by 68 metres, which is 115 by 74 yards and "
     "a bit under two acres; the laws allow 90 to 120 metres long and 45 to 90 wide, which is "
     "why pitches differ. The goal is 7.32 metres wide and 2.44 metres high."),
    (("tennis court", "tennis courts"),
     "A tennis court is 23.77 metres long, 10.97 metres wide for doubles and 8.23 metres for "
     "singles, with room to run of 6.4 metres behind each baseline and 3.66 metres at the "
     "sides. The net is 1.07 metres at the centre and 0.91 at the posts."),
    (("cricket pitch", "cricket square"),
     "A cricket pitch is 20.12 metres — 22 yards — from stump to stump and 3.05 metres wide, "
     "with the popping crease 1.22 metres in front of the stumps. The boundary round it is a "
     "different size at every ground, from about 60 metres to 75."),
    (("netball court",), 
     "A netball court is 30.5 metres long and 15.25 metres wide, split into thirds, with a "
     "shooting circle of 4.9 metres round each goalpost."),
)


def _ground_size(memory, reading):
    """The size of the pitch or court this line names, or None when it names none of them."""
    said = " ".join(str((reading or {}).get("clean") or "").split())
    if not said:
        # the entry only matches a line that names a ground, so with no line to read the first
        # one is the answer the entry is about
        return GROUNDS[0][1]
    for words, text in GROUNDS:
        if any(one in said for one in words):
            return text
    return None


# A stitch in a wound is not the cramp in your side. The row's key holds a bare "get" and a bare
# "side", so "should i get stitches" and "does a cut need stitches" were answered with the runner's
# stitch, and an `avoid` list cannot fix it: avoid words are matched as loose forms of the line, so
# "cut" would also stand the row down for "cut back on sugar" and "cut out the junk". A guard reads
# the whole line instead: the plural "stitches" is never the cramp (a runner says "a stitch"), and a
# wound noun is never the cramp either.
_WOUND_WORDS = frozenset((
    "cut", "cuts", "wound", "wounds", "gash", "gashes", "laceration", "lacerations", "slash",
    "slashed", "sliced", "bleeding", "bled", "blood", "stitches", "sutures", "suture",
    "graze", "grazed", "scab", "tetanus", "butterfly", "steristrips", "glued"))


def _not_a_stitch_in_a_wound(understood):
    """False when the stitch the line is about is one holding a cut together."""
    words = [str(word).lower() for word in (understood.get("words") or ())]
    if not words:
        words = (understood.get("clean") or "").split()
    for word in words:
        if word in _WOUND_WORDS:
            return False
    return True


# "is a marathon longer than a half marathon" and "which is longer, a marathon or a half" were
# both punts: the marathon distance card stood down on the word "half" (rightly - "how far is a
# half marathon" is the half's own line), and no other card carries two distances side by side.
# The comparison is this card's subject too, so the words that compare are in its key and the
# guard draws the line the avoid list could not: a half with no comparison in the line is still
# the half's question, and its own card answers it.
_A_SHORTER_RACE = re.compile(r"\b(?:5\s?k|5km|five k|10\s?k|10km|ten k|parkrun)\b", re.I)
_THE_FULL_RACE = re.compile(r"\b(?:full|marathon)\b(?<!half marathon)", re.I)
_COMPARED = ("longer", "longer than", "longest", "further", "furthest", "which is longer",
             "how much longer", "difference", "compared", "compare", "versus", "vs", "twice")


def _a_shorter_race_is_the_question(understood):
    """True for "is a half marathon longer than a 10k", and only for that shape."""
    words = [str(w) for w in ((understood or {}).get("words") or ())]
    said = " ".join(words).replace("-", " ")
    if not _A_SHORTER_RACE.search(said):
        return False
    return not _THE_FULL_RACE.search(said)


def _half_is_not_the_question(understood):
    """False for a line that names the half and is not comparing it with the full race."""
    words = [str(w) for w in ((understood or {}).get("words") or ())]
    said = " ".join(words).replace("-", " ")
    half = "half" in words or "13.1" in words or "21.1" in words
    compares = "longer" in words or any(phrase in said for phrase in _COMPARED)
    # A half against a shorter race is not a comparison with the full one: "is a half marathon
    # longer than a 10k" was answered with 26.2 miles against 13.1, because "marathon" matches
    # inside "half marathon" and this card picked the line up.
    if half and not _THE_FULL_RACE.search(said) and _A_SHORTER_RACE.search(said):
        return False
    return compares or not half


# "is a half marathon longer than a 10k" was answered with 26.2 miles against 13.1 - the half
# against the full race, when the line asked about a 10k. The half's own card stands down on the
# comparison words (the full-race comparison is the marathon card's) and the marathon card is not
# the question, so the pair is answered here: the same card the half gets, with the shorter
# distances beside it.
# A comparison of the two races needs both figures in one sentence, and the marathon distance
# card answers a plain "how far is a marathon" - so the comparison is its own card, with the
# half named in the guard and a bias that beats the distance card on the lines that compare.
_MARATHON_COMPARED = ("A marathon is 26.2 miles, or 42.2 kilometres, and a half is 13.1 miles "
                      "(21.1 km), so the full race is exactly twice as far. The odd 0.2 of a mile "
                      "is there because the 1908 London course was extended to finish in front of "
                      "the royal box. A half is the obvious first step, and most plans build up to "
                      "it over about sixteen weeks.")


def _the_half_is_named(understood):
    words = [str(w) for w in ((understood or {}).get("words") or ())]
    said = " ".join(words).replace("-", " ")
    if _A_SHORTER_RACE.search(said):
        return False
    return "half" in words or "13.1" in words or "21.1" in words


_RACE_COMPARED_CARD = entry(
    "race-compare-full",
    (("marathon", "26.2", "42.2", "full marathon"),
     ("longer", "longer than", "which is longer", "how much longer", "difference", "compare",
      "compared", "versus", "vs", "twice", "further", "further than")),
    _MARATHON_COMPARED,
    guard=_the_half_is_named,
    bias=20)

_A_SHORTER_RACE_CARD = entry(
    "race-compare-shorter",
    (("half marathon", "half", "13.1", "21.1"),
     ("longer", "longer than", "further", "shorter", "bigger", "which is longer", "difference",
      "compare", "compared", "versus", "vs")),
    "A half marathon is 13.1 miles (21.1 km), which is further than a 10k at 6.2 miles and a 5k "
    "at 3.1 miles. A first half usually takes 2 hours 15 to 2 hours 30, over twelve to sixteen "
    "weeks of training.",
    guard=_a_shorter_race_is_the_question,
    bias=2)

# How long the recovery takes depends on what was done, so each distance carries its own figure
# and its own reason. The phrases are written the way people type them, and "a marathon" and
# "half marathon" are phrases rather than bare words so "half an hour" and a marathon's length
# are not caught.
_RECOVERY_BY_DISTANCE = (
    (("a marathon", "full marathon", "26.2", "42.2", "42k"),
     "Three to four weeks before anything hard: easy running or walking the first week, short easy "
     "runs the second, and a tempo or a long run only around a month out. The fitness comes back "
     "faster than the legs do, which is what catches people who feel fine on day five."),
    (("a half marathon", "half marathon", "half-marathon", "13.1", "21k"),
     "A week to ten days: three or four short easy runs in the first week, nothing hard for ten "
     "days, and a normal week after a fortnight. Most people feel fine after three days, and going "
     "hard then is how the second week goes wrong."),
    (("10k", "10 k", "ten k", "6.2", "six miles", "six mile"),
     "Three or four easy days and then normal training: a 10k at effort takes more out of the legs "
     "than the distance suggests, and the second day after is usually the sorest."),
    (("5k", "5 k", "five k", "three miles", "parkrun"),
     "A day or two of easy running: a hard 5k costs your legs about 48 hours, and an easy run the "
     "day after does more good than a full day off."),
)

# How many turns back a distance still counts: "im 45 and havent run since school" then "how long
# to train" then "and how long to recover" is the same run, and the six-turn window is the one the
# other lookback answers use.
_RECOVERY_LOOKBACK = 6


def _a_distance_is_named(understood):
    """True when the line names a race distance, so its "rest" is a runner's rest.

    A guard rather than a word: "how long should i rest a leg of lamb", "how long should i rest
    it" about a knee and "how long to rest between gym sessions" were all told to scale their
    recovery to a 5k when the rest row keyed the naked verb. A distance in the line is what makes
    the rest after it a session's.
    """
    text = str(understood.get("plain") or understood.get("clean") or "").lower()
    return any(phrase in text for phrases, _line in _RECOVERY_BY_DISTANCE for phrase in phrases)


def _recovery_time(memory, understood):
    """How long the recovery takes, in the figure the session asks for.

    "how long to recover after a run" was answered with the cold-and-flu rule and "how long to
    recover after a marathon" with how many miles a marathon is: both are on the subject and
    neither is a recovery time. A recovery depends on what was done, so the distance named - in
    this line, or in one just before it - picks the figure, and a line that names none gets the
    ladder.
    """
    text = str(understood.get("plain") or understood.get("clean") or "").lower()
    for phrases, line in _RECOVERY_BY_DISTANCE:
        if any(phrase in text for phrase in phrases):
            return line
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed(turns[-_RECOVERY_LOOKBACK:] if isinstance(turns, list) else []):
        said = str(turn.get("user") or "").lower() if isinstance(turn, dict) else ""
        for phrases, line in _RECOVERY_BY_DISTANCE:
            if any(phrase in said for phrase in phrases):
                return line
    return ("Scale it to what you did: a day or two easy after a hard 5k, three or four days after "
            "a 10k, a week to ten days after a half marathon, and three to four weeks before "
            "anything hard after a marathon. A gym session is about 48 hours for the same muscle "
            "group. Soreness shifts faster with a short easy effort than with total rest, and if "
            "you are still stiff on the stairs after a week, you went back too soon.")
# The circle throws differ in the implement and the release, and agree on the rest: the hips lead
# and the arm follows last. The line names which one, so the card answers for that one.
def _a_circle_throw(memory, understood):
    text = str((understood or {}).get("clean") or "").lower()
    if "hammer" in text:
        return ("Swing it from a low point and keep the arms long: three or four turns that get "
                "taller and faster, the body turning first and the arms following, and a high "
                "release over the left shoulder. Stay in the circle until the ball lands, and "
                "keep the wire clear of the ground on the way round - distance comes from the "
                "turns building, not from a big first pull.")
    if "shot" in text:
        return ("A shot is pushed, not thrown: hold it in the fingers at the base of the hand, "
                "tuck it under the chin, and drive off the back leg so the hips lead and the arm "
                "follows last. Keep the elbow behind the shot until the push, and stay in the "
                "circle - stepping out over the front is a foul.")
    return ("The throw comes from the legs and the turn, not the arm: hold the discus flat, spin "
            "across the circle so the hips lead and the arm follows last, and let it go at about "
            "shoulder height with the palm down. Keep the discus close to your body through the "
            "turn. Most beginners lose distance by throwing it up and by rushing the spin.")

# The words that make a card a card: a match, a player, a referee, or the card itself. A
# line without one of them is not asking about a card even when it uses the word "booked",
# because a typed "book" reaches that key (the ending table lets a word reach its longer
# forms) and "what book should i read" was answered with the yellow-card card.
_A_CARD_WORDS = ("yellow", "red", "card", "cards", "booked", "booking", "bookings", "sin bin",
                 "sin-bin", "football", "footballer", "soccer", "rugby", "match", "matches",
                 "ref", "referee", "sent off", "foul", "fouls", "tackle", "tackles", "player",
                 "players", "game", "games", "league", "cup", "premier", "world cup", "offside",
                 "penalty", "var", "half time", "pitch", "goal", "goals", "keeper", "chelsea",
                 "arsenal", "liverpool", "united", "spurs", "everton", "england")


def _a_card_is_named(understood):
    """True when the line names a card, a match or a sport, so the card row may answer it.

    A `guard` and not an `ask`: a line that wants something ("what book should i read") is let
    past the ask list by `score` (see `_wanting`), so the noun "book" still reached the card.
    """
    reading = understood if isinstance(understood, dict) else {}
    line = " " + " ".join(str(reading.get("clean") or reading.get("text") or "").lower().split()) + " "
    return any(" " + word + " " in line or (" " + word) == line[-len(word) - 1:]
               for word in _A_CARD_WORDS)


# A row about a block in the water answers a block: the person cannot, will not, is afraid, or
# asks how. The row was keyed on `underwater` beside `swim`, so a proud line about a child who
# has just done it - "my son can swim underwater now", "i can swim underwater", "my nephew can
# swim underwater" - got the lesson on how not to fear it. `polarity` and `keywords` do not carry
# the "cant" (the reading drops it), so the guard reads the line as it was typed.
_A_BLOCK_IN_THE_WATER = re.compile(
    r"\b(?:can'?t|cannot|couldn'?t|won'?t|unable|struggl\w*|scared|afraid|frightened|"
    r"terrified|nervous|panic\w*|hate[sd]?|dread\w*|worr\w*|refus\w*|phobia|"
    # "a fear of going under water" is the same block as "scared of going under water", and the
    # noun was standing the row down, so the line fell to the drowning card instead.
    r"fear\w*|"
    r"don'?t like|do not like|not (?:able|confident|brave))\b"
    # The breath is the other half of the block, but only where the water is in the same line:
    # "i hold my breath when i go under water" is a nervous swimmer, and "i held my breath for 90
    # seconds today" is a swimmer telling you how it went, which stays its own answer.
    r"|\b(?:hold|holds|holding|held)\b[^.?!]{0,25}\b(?:my|his|her|their|your)\s+breath\b"
    r"[^.?!]{0,40}\b(?:under|underwater|swim\w*|pool|dive\w*|dove|water)\b"
    r"|\bhow (?:do|can|should|would) i\b|\bhow to\b|\bhelp me\b|\bteach me\b"
    r"|\blearn\w*\b|\btips?\b|\badvice\b|\bwhat can i do\b",
    re.IGNORECASE)


def _a_block_in_the_water(understood):
    """True when the line is a fear, a refusal or an ask about going under, not an achievement.

    "i can swim underwater" and "my son can swim underwater now" name no block, so the row stands
    down and the line gets the swim card it had before; "i cant put my head under water",
    "my son is frightened of going under water" and "help me get my head under water" keep it.
    """
    return bool(_A_BLOCK_IN_THE_WATER.search(understood.get("text") or understood.get("clean") or ""))


# "Any short games" and "a short game to play tonight" are a video or board game to play, and
# "the short game" is golf's name for the chipping and putting, so the golf row keyed that phrase
# and answered the games lines with a chip shot. A line that names a game being played and no
# golf word is the game-picks row's, not this one; every real chip and pitch line names the club,
# the ball, the green or golf itself.
_A_GAME_WORD = re.compile(r"\b(?:games?|play|playing|played|tonight|board|video|console|xbox|"
                          r"playstation|nintendo|switch|steam)\b", re.IGNORECASE)
_A_GOLF_WORD = re.compile(r"\b(?:golf|green|pin|flag|flagstick|club|clubs|iron|irons|wedge|"
                          r"ball|balls|fairway|putt|putts|putting|putter|tee|tees|bogey|birdie|"
                          r"par|handicap|bunker|chip shot|chip shots|pitch shot|pitch shots|"
                          r"chipping|pitching|shot|shots)\b", re.IGNORECASE)


# "the short game" is the golf jargon itself, and it carries no golf word of its own, so it counts
# only where nothing in the line is asking for a game to play: "how do i improve my short game"
# keeps this row, "a short game to play tonight" does not.
_SHORT_GAME_JARGON = re.compile(r"\bshort game\b", re.IGNORECASE)
_A_PLAY_ASK = re.compile(r"\b(?:to play|play tonight|to play tonight|any games?|games? to play|"
                         r"board|video game|video games|console|xbox|playstation|nintendo|"
                         r"something to play|what should i play|what can i play)\b", re.IGNORECASE)


def _a_short_game_to_play(understood):
    """False when the line is a game to play rather than golf's short game."""
    reading = understood if isinstance(understood, dict) else {}
    line = str(reading.get("clean") or reading.get("text") or "")
    if _A_GOLF_WORD.search(line):
        return True
    if _SHORT_GAME_JARGON.search(line) and not _A_PLAY_ASK.search(line):
        return True
    return not _A_GAME_WORD.search(line)


# What to wear for a match in rain or cold. "What should I wear to a football match in the rain"
def _says(clean, phrases):
    """True when one of these phrases is in the line as a word, not inside a longer word.

    `phrase in clean` matches "take" inside "mistake" and "wear" inside "swear", which is how a
    row ends up answering a line that never asked it. Every phrase is anchored at a word start.
    """
    return re.search(r"(?<!\w)(?:%s)" % "|".join(re.escape(p) for p in phrases), clean) is not None


# was the stadium arrival card ("arrive 45 minutes early ... bag searches"), because "match" and
# "football" are that row's key and this line spends its words on clothes and weather. A kit
# question is a different question, and it splits in two: the person playing and the person
# standing on the touchline need different things, so the row leads with whichever it names.
_WET_MATCH_PLAYING = (
    "Layers you can take off: a base layer and shorts under a thin waterproof top, "
    "gloves once it is under about 8C, and boots to suit the surface - moulded studs on grass, "
    "astro trainers on 3G, long studs only on a soft winter pitch. A towel and a dry top in the "
    "bag for after, because you cool fast once you stop."
)
_WET_MATCH_WATCHING = (
    "A waterproof over everything and something to keep your legs dry: a coat with a hood, "
    "boots or wellies, and a dry top waiting in the car. Two hours standing in wind and rain is "
    "colder than the forecast sounds, so a hat and gloves even in spring."
)
_WET_MATCH_WEATHER = ("rain", "rains", "raining", "rainy", "wet", "drizzle", "showers",
                      "cold", "freezing", "bitter", "snow", "snowing", "wind", "windy",
                      "muddy", "sleeting")
_WET_MATCH_WEAR = ("wear", "wearing", "kit", "clothes", "clothing", "outfit", "boots",
                   "shin pads", "what do i need", "what does he need", "what do we need",
                   "what should i take", "what should he take", "what should she take",
                   "bring", "bringing", "pop", "take with", "pack", "shall i wear",
                   "should i wear", "what should we wear", "what do we wear",
                   "should he wear", "should she wear", "dress him", "dress her")
_WET_MATCH_SPORT = ("football", "football match", "soccer", "rugby", "hockey", "netball",
                    "match", "matches", "five a side", "game", "cup tie", "training")
_WET_MATCH_WATCHING_WORDS = ("watch", "watching", "support", "supporter", "spectator",
                             "spectators", "stands", "touchline", "sit in the",
                             "go to the game", "my husband plays", "my partner plays")
# The first-person ones are the only playing words that beat a watching word: "watch my son
# play" has "play" in it and the person being dressed is still the one on the touchline.
_WET_MATCH_I_PLAY = ("im playing", "i'm playing", "i am playing", "i play", "im in the team",
                     "i'm in the team",
                     # someone else who is playing: "my son has a football match saturday"
                     "has a match", "has a game", "has a football match", "has a rugby match",
                     "is playing", "he plays", "she plays", "they play", "we play", "were playing",
                     "we are playing")
# A bare "play" is weaker than a watching word ("watch my son play") but beats nothing: with no
# "watch" and no first person, "what should i wear to play football" is still the player.
_WET_MATCH_PLAYS = ("to play", "play ", "playing", "training", "five a side", "kick about")
# Buying boots is a shopping question, drying them a care question, and what to eat before is the
# nutrition row's: this row holds the line that asks what to put on.
_WET_MATCH_NOT = ("buy", "buying", "should i buy", "should i get", "which boots", "best boots",
                  "cheap", "price", "cost", "how much",
                  # a bare "dry" stood the row down on the very line it is for: "what should i
                  # wear to football in the rain to stay dry" is the wear question, and "dry" is
                  # how people say it. The drying questions are the phrases, not the word.
                  "how do i dry", "how to dry", "drying", "to dry", "dry them", "dry it",
                  "dry out", "dry my", "dry the", "dry off", "get them dry", "keep them dry",
                  "clean", "cleaning",
                  "smell", "smelly", "eat", "eating", "food", "breakfast", "before the game",
                  "after the game", "recovery", "injured", "injury", "hurt", "knee", "ankle")


def _a_wet_match(reading):
    """True for a line that asks what to wear, bring or take to a match in bad weather.

    A guard takes the reading, not the memory: it is asked whether this row may answer at all.
    """
    clean = " " + str((reading or {}).get("clean") or "").lower() + " "
    if not _says(clean, _WET_MATCH_SPORT):
        return False
    if not _says(clean, _WET_MATCH_WEATHER):
        return False
    if not _says(clean, _WET_MATCH_WEAR):
        return False
    return not _says(clean, _WET_MATCH_NOT)


def _kit_for_a_wet_match(memory, understood):
    """What to wear for a match in the rain, led by the playing or the watching half."""
    clean = " " + str((understood or {}).get("clean") or "").lower() + " "
    if _says(clean, _WET_MATCH_I_PLAY):
        return _WET_MATCH_PLAYING
    if _says(clean, _WET_MATCH_WATCHING_WORDS):
        return _WET_MATCH_WATCHING
    if _says(clean, _WET_MATCH_PLAYS):
        return _WET_MATCH_PLAYING
    # Going to the match with nothing said about playing it is the touchline: "what should i
    # wear to the rugby in the cold" wants a coat, not studs.
    return _WET_MATCH_WATCHING


_GYM_KIT_WORDS = ("what should i bring", "what do i bring", "what should i take",
                  "what do i take", "what should i wear", "what do i wear", "what to bring",
                  "what to wear", "shall i bring", "should i bring", "do i need to bring",
                  "do i need", "what do i need", "what will i need", "need to bring",
                  "need to take", "need to wear", "what kit", "kit list",
                  "bring", "bringing", "wear", "wearing", "take", "taking")
_GYM_INDUCTION_KIT = (
    "Bring trainers with a clean, non-marking sole, a towel, water and a padlock for the locker, "
    "and wear something you can move in - shorts or leggings and a t-shirt. A gym induction is a "
    "walk round with a trainer: they set the seat heights and write you a plan, so nothing else "
    "is needed on the day."
)
_GYM_INDUCTION = (
    "Take the free induction: staff walk you round the machines and set the seat heights, "
    "which is the bit that puts people off. Then keep it simple - a warm-up on the bike, "
    "then two or three sets of 8-12 reps on five or six machines covering legs, back, chest "
    "and shoulders, light enough that you could still do three or four more reps. Write the "
    "weights down and add a little next week."
)


def _the_gym_induction(memory, understood):
    """What to bring to the induction, or what to do with it, whichever the line asked."""
    clean = " " + str((understood or {}).get("clean") or "").lower() + " "
    if _says(clean, _GYM_KIT_WORDS):
        return _GYM_INDUCTION_KIT
    return _GYM_INDUCTION


ENTRIES = [
    # A drink to carry is a running question, and there was no row for it: "how do i stay hydrated
    # on a run" was a shrug, "how do i keep water cold on a run" and "do i need water on a half
    # marathon" were the eyes and the cool bag.
    entry("water-on-a-run",
          (("water", "hydrated", "hydration", "hydrate", "drink", "drinks", "drinking",
            "fluids", "electrolytes", "salt tablets", "bottle", "water bottle", "flask",
            "thirsty", "camelbak", "hydration vest", "water belt"),
           ("run", "runs", "running", "long run", "jog", "jogging", "ride", "cycling", "bike",
            "half marathon", "marathon", "10k", "5k", "parkrun", "race", "train", "training",
            "gym", "hot", "heat", "summer", "sweat", "workout", "work out", "exercise",
            "exercising", "spin", "class", "football", "rugby", "tennis", "netball",
            "hockey", "swim", "swimming")),
          "Under an hour you do not need to carry anything: have 300-500ml in the hour before you "
          "go and take water at fountains or taps on the way. Past an hour, or on a hot day, carry "
          "400-700ml and drink a few mouthfuls every 15-20 minutes rather than one big stop. To "
          "keep it cold, fill the bottle half full and freeze it the night before, top it up with "
          "cold water on the way out, and put it in a belt or vest rather than in your hand. Over "
          "90 minutes take electrolytes, and drink to thirst - drinking lots of plain water on a "
          "long run can make you feel worse, not better.",
          # the reverse question - sore eyes or joints from running - is not about a drink, and
          # a water bill, the water in a recipe and a wet floor are other rows
          # "rinse the rice until the water runs clear" is a kitchen line that reached this row
          # on the words "water" and "runs"; the rice-and-water rows answer it.
          avoid=("rinse", "rinsing", "rinsed",
                 # "wash the rice until the water runs clear" is the same kitchen line with the
                 # other verb, and this row kept it on "water" and "runs"
                 "wash", "washed", "washing", "water runs clear", "runs clear",
                 "eyes", "eye", "knee", "knees", "ankle", "ankles", "shin", "shins", "pain",
                 "hurts", "sore", "injury", "injured", "bill", "meter", "leak", "recipe",
                 "boil", "bath", "shower", "plant", "plants", "garden", "floor", "filter",
                 "softener", "swimming", "pool", "sea", "lake", "well",
                 # a hot tub is not a drink: "how often should i change the water in a hot tub"
                 # was this answer about a long run, on the "water" and the "hot" in it
                 "hot tub", "hot tubs", "hottub", "jacuzzi", "spa bath",
                 # a boiler, a radiator or a washing machine that runs hot water is a plumbing
                 # question, and "my boiler whistles when the hot water runs" was this row
                 "boiler", "boilers", "radiator", "radiators", "heating", "pipe", "pipes",
                 "washing machine", "dishwasher", "kettle", "cylinder", "immersion", "valve",
                 "thermostat", "hot water", "hot tap", "noise", "noisy", "whistling", "banging",
                 "gurgling", "humming",
                 # A supply that will not get hot is the plumbing row's question, and bare "hot"
                 # in the key above is enough to take it: "water not hot enough" was the drink to
                 # carry before a run. The cold-water line this row does own - "how do i keep
                 # water cold on a run" - has no "not" in it and still reaches it.
                 "not hot", "not hot enough", "not warm", "not warm enough", "lukewarm", "tepid",
                 "water is not hot", "water not hot", "water isn't hot", "water isnt hot",
                 # and the same fault said without the word "hot water" in front of it: "my hot
                 # water runs cold after a few minutes", "the water is hot then goes cold"
                 "hot then cold", "hot and then cold", "hot then goes cold", "goes cold",
                 "runs cold", "airing cupboard", "stopcock", "cistern", "plumbing",
                 "hot water tank", "hot water cylinder", "immersion heater"),
          # fitness.workout-time keys the word "workout" too, and "do i need to drink during a
          # workout" is about the drink: this row is the narrower one and wins the tie.
          bias=2),
    # --- rules ------------------------------------------------------------
    entry("ground-size", (tuple(one for words, _text in GROUNDS for one in words),
                          ("big", "size", "how big", "long", "wide", "how long", "how wide",
                           "metres", "yards", "dimensions")),
          _ground_size,
          # the game's own rows answer the length of a match, a set or an innings; a court's
          # opening times or a trip to it are not its size
          avoid=("match", "game", "games", "rules", "players", "score", "scoring", "innings",
                 "offside", "how many", "open", "opening", "opened", "closed", "close",
                 "closing", "hours", "booking", "book", "session", "lessons", "distance",
                 "far", "near me", "directions", "nearest"),
          bias=1),
    # --- a race to aim at: the plan, the time, and the knees ---------------------
    # A target distance is a plan question, and the plan question had no entry at all: a 5k or a
    # 10k was a shrug, while a half marathon got the marathon's 32km long run, which is the wrong
    # advice for the distance. One pair of entries per distance, made from the table above.
    *_RACE_ENTRIES,
    # "is running bad for my knees" is the question that keeps people on the sofa, and it was a
    # shrug. A knee that already hurts is another entry's question, so this one stands aside on
    # pain, and on the noises a knee makes.
    entry("running-and-knees",
          (("running", "run", "jogging", "jog"),
           ("knee", "knees", "joint", "joints", "cartilage")),
          "No: running does not wear out healthy knees, and long-term studies of runners find no "
          "more knee arthritis than in people who do not run. What does cause trouble is doing "
          "too much too soon, so build the distance slowly and keep the legs strong with squats, "
          "step-ups and single-leg work. If a knee hurts for more than two weeks or swells up, "
          "get it looked at rather than running through it.",
          avoid=_HURTS + _NOISY + ("stairs", "when i run", "when i'm running", "since",
                                   "fell", "twisted", "injury", "injured", "swollen"),
          # fitness.py's knees-when-running is about a knee that already hurts and stands in for
          # this one on the general question, where it fits the line just as well
          bias=2),
    entry("offside", ("offside", ("work", "explain", "rule", "rules", "mean", "mean work",
                                  "football", "soccer", "how")),
          "You are offside if, at the moment the ball is played forward to you, you are in the "
          "other team's half, closer to their goal line than both the ball and the second-last "
          "defender, and then you get involved in play. Standing there is fine — it is touching "
          "the ball or interfering that is punished. There is no offside straight from a throw-in, "
          "a goal kick or a corner.",
          # rugby offside is a different rule; that entry answers it, not this one
          avoid=("rugby", "hockey", "ice hockey")),
    entry("football-basics", (("football", "soccer"),
                              ("how long", "long", "minutes", "players", "positions", "extra time",
                               "half", "halves", "pitch", "team size")),
          "A football match is two halves of 45 minutes, with 11 a side including the keeper, and "
          "the clock keeps running — it does not stop for injuries or substitutions. The 90 "
          "minutes is why teams time-waste, and why added time at the end of each half can be long.",
          # the ground has its own answer, and a size question is not about the clock
          avoid=("big", "size", "wide", "metres", "yards", "dimensions", "how big")),
    entry("tennis-scoring", ("tennis", ("score", "scoring", "points", "set", "sets", "work",
                                       "deuce", "tie-break", "tiebreak", "explain")),
          "Points go 15, 30, 40, game — a point each from deuce is advantage and then game, so you "
          "have to win two in a row. Six games wins a set, but you need a two-game lead, so 6-6 "
          "goes to a tie-break. Matches are usually best of three sets, and the big men's matches "
          "are best of five."),
    entry("cricket-basics", ("cricket", ("work", "rules", "over", "wicket", "wickets", "basics",
                                        "explain", "innings", "how", "scoring", "match", "first",
                                        "beginner", "beginners", "spectator")),
          "One team bats to score runs and the other bowls and fields to get them out; an over is "
          "six balls, and an innings ends when ten batters are out or the overs run out. You are "
          "out if the ball hits your stumps, if a fielder catches it before it bounces, if you are "
          "run out, or leg before wicket — hit on the pads by a ball that was going to hit the "
          "stumps.",
          # a coaching line names a skill and is answered by cricket-batting
          avoid=("batting", "batting technique", "batting stance", "how do i bat",
                 "practice batting", "practise batting", "score more runs", "bowling action",
                 "how do i bowl", "how do i spin")),
    entry("rugby-basics", ("rugby", ("work", "rules", "basics", "explain", "how", "points",
                                     "scoring", "positions", "union", "long", "try", "tries",
                                     "minutes")),
          "In rugby union, 15 a side, you can only pass backwards — forward movement comes from "
          "running and kicking. A try is five points, the conversion two, a penalty three; a tackle "
          "becomes a ruck where both teams push for the ball, and the offside line moves as that "
          "happens. Two 40-minute halves, and the clock stops for injuries.",
          # rugby league is the other code, and it has its own card: "how many players in a
          # rugby league team" is 13, not this game's 15
          avoid=("league", "rugby league", "six tackles")),
    entry("rugby-league", (("rugby league", "rugby league team", "union and league",
                            "league and union"),
                           ("work", "rules", "basics", "players", "how many", "tackles", "points",
                            "try", "long", "minutes", "difference", "union", "team")),
          "Rugby league is 13 a side over two 40-minute halves, and the side with the ball gets "
          "six tackles to make progress before it goes to the other team. A try is four points "
          "and a penalty two, where union scores five and three - that is the quickest way to tell "
          "the two codes apart.",
          bias=2),
    entry("scrum", (("scrum", "scrums"),
                    ("what", "whats", "mean", "means", "is", "how", "work", "rugby", "do")),
          "A scrum restarts play after a knock-on or a forward pass: the eight forwards of each "
          "side bind together and push against the other pack, the scrum-half feeds the ball into "
          "the middle, and the hooker strikes it back with a foot. The side that shoves the other "
          "back can win the ball against the head."),
    # "booked" and "booking" were key words here, and the matcher hands out the loose form
    # "book" for them, so any line with a book in it and a football in it was answered with a
    # card: "any books for a 9 year old who's mad about football", "what book should i buy",
    # and "we booked a hotel" in a chat about Spain. In everyday English "booked" means a
    # table, a room or a flight, which is the far more common sense of the word. The card sense
    # is the phrase "got booked", and that is what the key says now.
    entry("yellow-card", (("yellow card", "yellow cards", "red card", "red cards", "sin bin",
                           "sin-bin", "got booked", "gets booked", "get booked", "was booked",
                           "were booked", "been booked",
                           # Dropping the bare "booked" left the card's own questions a punt:
                           # "when is a player booked", "why was he booked" and "what does
                           # booked mean" reached nothing, and the tests for them went red on
                           # main. The person is named here, so the phrase says the card sense
                           # without the bare verb doing it, which is what let "we booked a
                           # hotel" and "we booked a flight" into this row.
                           "player booked", "players booked", "a player booked", "he booked",
                           "she booked", "they booked", "booked mean", "booked mean in",
                           # the same question in the other noun: "how many bookings has he got
                           # this season" is the card, and it was a punt. "bookings" alone
                           # would take a hotel's or a restaurant's bookings, so the phrase
                           # names the person: "how many bookings" on its own took "how many
                           # bookings do they have for tonight", which is the restaurant.
                           "bookings has he", "bookings has she", "bookings this season",
                           # "why did the ref book him" is the card said in the present tense
                           # with the referee in it, and it was a shrug: the key had "he booked"
                           # and the past tense only, so the bare "book him" reached nothing.
                           "book him", "book her", "book them", "booked him", "booked her",
                           "booked them", "ref book", "ref booked", "ref has booked",
                           "ref gave him"),
                          ("what", "whats", "mean", "means", "is", "how", "work", "football",
                           "rugby", "why", "get", "point")),
          "A yellow card is a formal warning. In football two of them in a match mean a red and "
          "the player is off, and a straight red carries at least a one-match ban; in rugby a "
          "yellow means ten minutes in the sin bin, and a second one is a red too.",
          guard=_a_card_is_named,
          # "booked" and "booking" are the card words and also the ordinary verb: the ending table
          # lets "book" stand for "booking", so the weak word "how" carried "how do i book a
          # hotel", a flight and a restaurant table into this row. A place or a time gets booked;
          # a player gets booked. Only the second is this entry's question, so the first is held
          # out by the thing being booked rather than by the verb.
          avoid=(
                 "hotel", "hotels", "hostel", "b and b", "guest house", "airbnb", "cottage", "flight",
                 "flights", "ferry", "train", "tickets", "ticket", "restaurant", "table", "room",
                 "rooms", "campsite", "pitch", "venue", "appointment", "dentist", "doctor", "haircut",
                 # a novel and its adaptation are both named here, which is the book-or-film
                 # question and not a booking: the line "is the book better than the film" was
                 # a yellow card because "book" reads as "booking"
                 "book film", "book and film", "book the film", "book or film", "novel",
                 "novels", "audiobook", "paperback", "kindle", "author", "chapter", "spoilers",
                 "holiday", "taxi", "car hire", "parking", "court", "festival", "festivals",
                 "concert", "concerts", "gig", "gigs", "booking fee", "booking fees", "refund",
                 "refunds", "cancelled", "canceled", "cancellation", "reservation", "reserved",
                 "book a", "booked a", "booking a",
                 # A book to read is the books domain's, not a football answer, so the reading
                 # nouns are held out the same way. "book" and "books" are deliberately not in the
                 # list: the ending table reduces both to "book", which is inside "booked", so
                 # "what does booked mean in football" stopped being answered when they were.
                 "read", "novel", "novels", "reading", "reader", "author", "library", "kindle",
                 "audiobook", "bookshop", "chapter", "recommend", "club", "fiction", "nonfiction",
                 "poetry", "memoir", "biography", "depressing", "miserable",
                 # the nouns main's list does not reach: a line can name the book and nothing
                 # else on that list, and then it is still the card's. "my book is boring",
                 # "is the book better than the film", "this book is rubbish" and "the book is
                 # really long" were all "a yellow card is a formal warning".
                 "chapters", "my book", "a book", "what book", "which book", "this book",
                 "the book", "book to read")),
    # "who won the world cup in 1966" was getting a shrug or a news hedge: the winners are facts,
    # so they are a table keyed by year and one entry reads the year out of the line.
    entry("world-cup-winners", (("world cup", "world cup final", "the world cup"),
                                ("won", "win", "wins", "winner", "winners", "who", "which year",
                                 "which team", "champion", "champions", "held", "host", "hosted")),
          _world_cup,
          # the same words ask about other sports, and those winners are other answers
          avoid=("rugby", "cricket", "t20", "ashes", "league", "hockey", "netball", "olympic",
                 "olympics", "snooker", "darts", "swimming", "athletics", "skiing", "f1")),
    entry("netball-basics", ("netball", ("work", "rules", "basics", "players", "explain", "how",
                                        # "positions" is out: it answers its own question now, and
                                        # the card that names the seven was this one's reply.
                                        "seven")),
          "Netball is seven a side, and the rule that surprises people is that you cannot move "
          "with the ball: catch it, and you have to pass or shoot within three seconds, with one "
          "foot planted. Each position is limited to certain thirds of the court, which is why "
          "goal shooters barely leave the circle.",
          # how long a game runs is the length row's question
          avoid=("how long", "how many quarters", "minutes", "how many minutes")),
    # "how long is a netball game" and "how long is a basketball game" were both reaching the
    # board games card on "game" and "long", while netball's own card answered seven-a-side
    # without ever saying how long the match is.
    entry("netball-length", (("netball", "netball match", "netball game"),
                             ("how long", "long", "last", "minutes", "quarters", "periods",
                              "how many quarters")),
          "Four 15-minute quarters, so 60 minutes of play, and about 75 minutes all told with the "
          "breaks. The clock stops for injuries and for the ball going out, so a close game can "
          "run a little past that.",
          bias=1),
    # "how" alone is not a darts-rules word: it made this card answer "how do i play darts
    # better" and "how do i throw a dart straight", which are coaching questions.
    entry("darts-scoring", ("darts", ("score", "scoring", "rules", "501", "checkout", "work",
                                      "explain", "180", "maximum", "points",
                                      # taking `how` out of this key freed the coaching lines, and
                                      # the plain "how do i play darts" and "how long does a game
                                      # of darts take" were left with nothing: the duration and the
                                      # playing words name the format this card is about
                                      "play", "playing", "how long", "how many legs",
                                      "how many sets")),
          "In 501 both players start at 501 and count down, and you finish on a double or the "
          "bullseye — going below the target or landing on one is a bust and the turn is wiped. "
          "That is why players aim for treble 20s early and switch to a tidy double once they are "
          "under 170. Three treble 20s in one visit is 180, the highest score there is.",
          # a coaching word is the throw card's, and it says nothing about the rules
          bias=1,
          avoid=("better", "improve", "throw", "throwing", "aim", "aiming", "technique",
                 "practice", "practise", "grip", "consistent", "straight", "tips", "accurate",
                 "accuracy")),

    entry("darts-throw",
          (("darts", "dart", "oche", "dartboard", "darts board"),
           ("better", "improve", "throw", "throwing", "aim", "aiming", "technique", "practice",
            "practise", "grip", "tips", "accurate", "accuracy", "consistent", "straight",
            "more consistent")),
          "Stand side-on with your front foot behind the oche and your weight on it, keep the "
          "elbow up and still, and throw from the elbow rather than the shoulder: same speed, "
          "same release, every dart. Practise grouping rather than scoring - twenty darts at the "
          "20 bed, trying to land them inside a hand's width - and finish every session with ten "
          "at a double, because doubles win legs.",
          # the rules of 501 are the other card, and a match on television is news
          avoid=("rules", "scoring", "checkout", "how many points", "bust", "world championship",
                 "alexandra palace", "on tv", "tickets"),
          bias=1),
    # --- coaching, usually a parent ---------------------------------------
    entry("coach-kids-first-session", (("coach", "coaching", "coached"),
                                       ("under-8s", "under 8s", "under-9s", "under-7s", "kids",
                                        "football", "team", "first session", "first training",
                                        "training", "session")),
          "Give every child a ball and keep them moving: ten minutes of a game with a ball each "
          "(dribble and freeze), fifteen of one skill in a small game (passing through gates, or "
          "1v1 to a line), then twenty minutes of small-sided matches, four a side, no keepers. No "
          "queues, no laps, no long instructions — if they stand still for more than a minute you "
          "lose them. Finish with a game they already love and a quick handshake line.",
          # A "coach" is also a bus and "train" is read as "training": a question about getting
          # somewhere must not be answered with a session plan for children.
          avoid=("cheaper", "cheapest", "cheap", "fare", "fares", "ticket", "tickets",
                 "price", "prices", "cost", "costs", "how much", "to get"),
          ask=("kids", "kid", "children", "child", "under-8s", "under 8s", "under-9s", "under-7s",
               "football", "soccer", "players", "player", "team", "teams", "session", "sessions",
               "drill", "drills", "pitch", "juniors", "youth", "warm up", "warmup", "first")),
    entry("coach-kids-attention", (("coach", "coaching", "coached", "training", "session"),
                                   ("keep them", "interested", "attention", "bored", "listen",
                                    "behaviour", "behaviour problems")),
          "Keep instructions under twenty seconds, show it once, then let them try it in a game — "
          "children learn by playing, not by queueing to take turns. Give every child a job or a "
          "ball, praise the one who does the thing you asked, and change the game every ten "
          "minutes. Two or three restless ones are easier to manage when the rest are busy.",
          # "training" hands out the loose form "train", so the word "train" in a key was enough
          # for "im bored on the train" and "im bored on a train" to be answered with a coaching
          # session (reported from main, b9b63534). The rest of a coaching line says who is being
          # coached or where, and that is what is asked for now; "training" cannot be one of these
          # words or the train would satisfy it again.
          ask=("coach", "coaching", "coached", "session", "sessions", "kids", "children",
               "child", "team", "teams", "players", "player", "drill", "drills", "club",
               "group", "class", "classes", "pitch", "court", "juniors", "youth", "match",
               "under 8", "under 10", "under 12", "under 14", "warm up", "warmup"),
          bias=1),

    # --- starting, or starting again --------------------------------------
    entry("adult-sport-start", (("sport", "football", "netball", "hockey", "basketball", "rugby",
                                 "badminton", "squash"),
                                # "club" is not in this group: "how do i find a football club"
                                # is the club search itself, and only a line that says it is
                                # coming back, or gives an age, is this answer
                                ("start", "again", "adult", "adults", "beginner",
                                 "beginning", "back into", "40", "fifty", "forty", "old",
                                 "too old", "am i too old",
                                 # "is rugby safe for kids" asks the same thing a parent asks
                                 # before the first session, and it reached the search hedge
                                 # while "is rugby ok for an 8 year old" got this answer. Only
                                 # "safe": "kids" read "my kids need new football boots" as a
                                 # club question, and the boots row owns that.
                                 "safe", "safety")),
          "Look for a club that advertises a beginners' or \"back to\" session rather than a team "
          "trials night — most sports now run them, and the standard is friendly. Try three in a "
          "month before you judge, and go twice before deciding you are unfit for it, because the "
          "first session is always the worst one. Nobody at a casual session is watching you; they "
          "are all watching the ball.",
          # a search for a club is the join-a-club answer: this one is for the person coming
          # back to a sport, and "play hockey again at 42, how do I find a club" is that
          # question, so the two tie and this entry is listed first.
          # a return from an injury is the healing answer, not the beginner's-session one:
          # "when can i play football again after a broken leg" was sent to a taster night
          # A body that is already complaining is not a first session: "is it safe to play rugby
          # with a bad back" is the injury answer's, and "safe" in this entry's key would take it.
          avoid=("join", "joining", "near me", "where can i", "taster",
                 # kit is bought, not started again: "football boots for a 9 year old, where to
                 # buy" was a beginners'-session answer because "old" was in the key
                 "boots", "boot", "studs", "astro", "shin pads", "trainers", "kit", "shirt",
                 "shorts", "socks", "gloves", "gum shield", "goggles", "racket", "bat",
                 "broken", "broke", "fracture", "fractured", "cast", "plaster", "sprain",
                 "sprained", "injury", "injured", "operation", "surgery", "heal", "healing",
                 "physio", "crutches", "recovery",
                 "bad back", "bad knee", "sore", "aches", "aching", "heart condition",
                 "asthma", "pregnant", "pregnancy"),
          bias=1),
    # "how long does it take to get fit" reached nothing at all. The timeline is the same for
    # everyone starting out, and it is the question people ask before they begin, so it has its
    # own card rather than living in a reply to something else.
    entry("fit-timeline",
          (("how long", "how many weeks", "how many months", "how soon", "when will i",
            "how long until", "how long before"),
           ("get fit", "fitter", "fitness", "see results", "see a difference",
            "notice a difference", "feel a difference", "feel better", "stronger", "toned",
            "in shape", "shape", "start exercising", "start running", "start the gym")),
          "How you feel changes first: two to three weeks of regular sessions and the stairs and "
          "your sleep are easier. Visible change takes about six to eight weeks, and the real "
          "difference by three to six months when it shows in what you can do rather than in the "
          "mirror. Three sessions a week that you actually keep beat five you abandon.",
          # losing weight has its own answer, and a stone or a kilo is that question
          avoid=("lose a stone", "lose weight", "weight", "kilos", "pounds", "lbs", "stone",
                 "diet", "slim")),
    entry("kids-sport-choose", (("sport", "club", "activity", "classes"),
                                ("shy", "nervous", "try", "choose", "which", "kids", "son",
                                 "daughter", "reluctant", "hates")),
          "Try two or three taster sessions before choosing anything: the club matters far more "
          "than the sport. Pick one where the coach learns the children's names, keeps everyone "
          "playing, and the ratio of adults to children is decent — and for a shy child, a smaller "
          "club beats a big one with a waiting list. Ask if you can watch the first session from "
          "the side.",
          # A child who fainted at a club is the same call whichever club it was: "the kid in my
          # class fainted" reached the which-sport answer and told a worried adult to book taster
          # sessions. The club words are in the key, so the fainting is what has to stand it down.
          avoid=("faint", "fainted", "fainting", "pass out", "passed out", "collapsed",
                 "unconscious", "went white", "seizure", "ambulance")),
    entry("adult-swim-lessons", (("swim", "swimming", "swimmer", "learn to swim",
                                  "learning to swim"),
                                 ("can't", "cant", "cannot", "adult", "learn", "lessons", "teach",
                                  "beginner", "embarrassed", "worth it",
                                  # "i never learnt to swim" is the same admission as "i cant
                                  # swim", and it was the listening reply
                                  "never learnt", "never learned")),
          "Adult lessons at your local pool are the fastest route: most run classes for complete "
          "beginners, often in small groups, and every instructor has taught adults who are "
          "frightened of the water. Book a course rather than one lesson, start in the shallow end "
          "with floats, and ask for an instructor who is used to nervous beginners. Nobody in an "
          "adult class is watching anybody else.",
          # Learning to swim is the special case and the lengths row is the rule, so the gate
          # faces that way: "how long" was in the key and it took five lengths questions -
          # "how long does it take to swim a mile", "how long should i swim for" - that the
          # lengths card answers properly. A line that says learn, can't, adult or lessons is
          # this row's; a distance or a number of lengths is not.
          ask=("learn", "learning", "learnt", "learned", "can't", "cant", "cannot", "adult",
               "adults", "lessons", "lesson", "teach", "taught", "beginner", "beginners",
               "never learned", "never learnt", "dont know how", "don't know how", "how do i swim",
               "embarrassed", "frightened", "scared", "nervous", "worth it"),
          # a child's swimming is not an adult class, and the row was answering
          # "how do i teach my child to swim" with "book a course for adults"
          avoid=("child", "children", "kid", "kids", "son", "daughter", "toddler", "baby",
                 "school", "nursery", "my boy", "my girl", "grandson", "granddaughter"),
          bias=2),
    # Every line about a child and swimming reached the baby's-first-dip card, because "my son"
    # and "my daughter" are in that row's key: "my son has just learned to swim" was told about
    # six-week-old babies, "how do i teach my kid to swim" was a shrug, "my son cant swim yet
    # should i worry" was the worry card and "my kid is frightened of getting water in his face"
    # was how much a toddler should drink. A child learning is its own question, and it is the
    # one a parent asks most.
    entry("child-swimming",
          (("my son", "my daughter", "my kid", "my child", "my children", "our son",
            "our daughter", "our kids", "son", "daughter", "child", "children", "kid", "kids",
            "grandson", "granddaughter", "nephew", "niece", "little one", "year old",
            "years old", "reception", "primary school"),
           ("swim", "swims", "swimming", "swimmer", "learn to swim", "learning to swim",
            "cant swim", "can't swim", "cannot swim", "couldnt swim", "couldn't swim",
            "swim lesson", "swim lessons", "swimming lesson", "swimming lessons",
            "lessons", "lengths", "metres", "metre", "badge", "widths", "float", "floats",
            "float on", "armbands", "arm bands", "water wings", "noodles", "face in the water",
            "face in water", "underwater", "under water", "head under", "tread water",
            "front crawl", "backstroke", "pool", "pools", "lido", "splash", "splashing",
            # a frightened child is the commonest version of the question, and the phrase is what
            # says it: the bare `water` is left out so a bath, a drink and a fever stay theirs
            "scared of the water", "frightened of the water", "afraid of the water",
            "scared of water", "frightened of water", "afraid of water",
            "scared of the pool", "frightened of the pool", "afraid of the pool",
            "hates the water", "hates water", "wont get in the water", "wont get in the pool",
            "scared of swimming", "frightened of swimming", "afraid of swimming")),
          "Most children swim somewhere between five and eight, and time in the water with you "
          "does more than a weekly class they dread: short warm visits where they choose to put "
          "their face in beat a lesson they cry through. For a nervous one, goggles and bubbles "
          "at the side first, then holding the rail and putting one ear under at a time, and "
          "never hold them under - one dunking sets a nervous swimmer back months. What they "
          "need to be safe in the shallow end is to float on their front and back, turn round, "
          "and get to the side and climb out, and the width badge usually comes a season after "
          "that. Give it a term before you worry, and if they are seven or over and still "
          "frightened, a few one-to-one lessons are worth the money.",
          # a baby's first dip, a bath, a drink and a body in the water are other answers: the
          # ages are named because "month old" and "year old" are key words here too, and an
          # avoid word that is a form of a key stands the row down for its own question
          avoid=("baby", "babies", "newborn", "infant", "infants", "toddler", "toddlers",
                 "3 months", "three months", "4 months", "four months", "5 months",
                 "five months", "6 months", "six months", "7 months", "seven months",
                 "8 months", "eight months", "9 months", "nine months", "10 months",
                 "ten months", "11 months", "eleven months", "months old", "month old",
                 "weeks old", "6 week", "six week", "bath", "bathtime", "nappy", "nappies",
                 "drink", "drinks", "drinking", "water intake", "how much water",
                 "not breathing", "isnt breathing", "couldnt breathe", "limp", "unresponsive",
                 "sank", "didnt come up", "fell in", "pulled out", "drowned", "drowning",
                 # A body that lost consciousness is not a child learning to swim: "my son
                 # blacked out in the pool" was this row's answer ("most children swim somewhere
                 # between five and eight") while a boy on the bottom of a pool was typed in.
                 "blacked out", "blacking out", "passed out", "passing out",
                 "fainted", "fainting", "unconscious", "knocked out", "seizure",
                 "river", "canal", "lake", "reservoir", "sea", "beach", "lifeguard",
                 # what to eat before a gala is the pre-race food row's question, and "my
                 # daughter" used to carry that line to the baby card
                 "eat", "eats", "eating", "ate", "food", "foods", "breakfast", "lunch",
                 "dinner", "snack", "snacks", "meal", "carb", "carbs", "fuel",
                 "dog", "dogs", "puppy", "vet")),
    # The thing that keeps people out of the water is not the swimming, it is the head going under:
    # "i cant put my head under water", "i hate going under water", "my head goes under water when i
    # swim", and for a child "my son is frightened of going under water". Nothing keyed it, and
    # on main the safety module read the same words as a drowning and rang 999.
    entry("head-under-water",
          (("under water", "underwater", "under the water", "head under", "face in the water",
            "go under", "goes under", "going under", "went under", "duck under", "submerge",
            "dunk", "going under water", "go under water",
            # A frightened child is one sentence away from the worry row, which answers a child
            # who will not go to school: these phrases are what makes the line this one.
            "frightened of going under", "scared of going under", "afraid of going under",
            "frightened of the water", "scared of the water", "afraid of the water",
            "frightened of water", "scared of water", "afraid of water",
            # the same block said about getting in at all, and about the face getting wet: these
            # are the lines the emergency card used to ring for a child who will not jump in
            "scared of the pool", "afraid of the pool", "frightened of the pool",
            "scared of swimming", "afraid of swimming", "scared to jump in", "afraid to jump in",
            "frightened to jump in", "scared of jumping in", "wont jump in", "wont get in",
            "scared to get in", "afraid to get in", "frightened to get in",
            "wont go in the water", "wont go in the pool", "put her face in the water",
            "put his face in the water", "put my face in the water", "face in the pool",
            "wont put her face in", "wont put his face in", "wont put my face in",
            # and the way a parent says it: the water is what the face is frightened of, and the
            # line was reaching the worry card ("name it and keep the day predictable")
            "water in his face", "water in her face", "water in my face", "water in the face",
            "water in his eyes", "water in her eyes", "water up his nose", "water up her nose",
            "getting water in his face", "getting water in her face", "splash in his face",
            "splash in her face", "water on his face", "water on her face",
            # The fear has a noun as well as an adjective, and the noun is how most people
            # introduce it: "i have a fear of going under water", "i dread going under water",
            # "i fear going under water" and "my son has a fear of going under water" were all
            # the drowning card ("say he was in the water") and are this row's line.
            "fear of going under", "fear of going under water", "fear of going underwater",
            "fear going under", "fear of the water", "fear of water", "fear of the pool",
            "phobia of the water", "phobia of water", "phobia of going under",
            "dread going under", "dread going under water", "dreads going under",
            "dread the water", "dread getting in",
            # ...and the breath is what a nervous swimmer worries about, so a line that says
            # what the breath does when the head goes under is this row's too: "i hold my
            # breath when i go under water", "i always hold my breath when i go underwater",
            # "he holds his breath when he goes under".
            "hold my breath", "holds my breath", "holding my breath", "held my breath",
            "hold his breath", "holds his breath", "holding his breath",
            "hold her breath", "holds her breath", "holding her breath",
            "hold their breath", "holds their breath", "hold your breath"),
           ("head", "face", "swim", "swimming", "pool", "lesson", "lessons", "scared",
            "afraid", "frightened", "terrified", "nervous", "wont", "won't", "cant", "can't",
            "cannot", "hate", "hates", "hated", "struggle", "panic", "goggles", "nose",
            "fear", "fears", "feared", "fearful", "phobia", "dread", "dreads", "dreaded",
            "breath")),
          "Start where you can stand up: hold the rail in the shallow end and put your chin in, then "
          "your mouth, then blow bubbles with your nose and mouth under for a second, and build it up "
          "over a few visits - goggles, and a nose clip if the water up your nose is the worst of it, "
          "get most adults past this. An adult beginner class teaches exactly this in the first "
          "lesson, and the instructor has seen it a hundred times. With a child it is the same thing "
          "at their size: let them watch and splash their own face at bath time, and never hold them "
          "under - one dunking sets a nervous swimmer back months.",
          # The water going wrong is not this: a body under it, a boiler, a leak or a phone in the
          # sink all say "under the water" too, and the first of those is the emergency card's.
          # a block in the water, not a swim that went well
          guard=_a_block_in_the_water,
          avoid=("not breathing", "isnt breathing", "isn't breathing", "couldnt breathe",
                 "couldn't breathe", "limp", "unresponsive", "blue", "didnt come up",
                 "didn't come up", "slipped", "sank", "face down", "pulled out", "fell in",
                 # a body that lost consciousness is a person to check, not a lesson in
                 # putting the head under: "i held my breath too long and blacked out" and
                 # "my son blacked out in the pool" are the blackout card's lines.
                 "blacked out", "black out", "blacking out", "passed out", "passing out",
                 "fainted", "fainting", "unconscious", "ambulance", "drowning",
                 "boiler", "leak", "leaking", "radiator", "drain", "flood", "sink",
                 "phone", "watch", "kettle", "washing machine", "dishwasher", "water broke",
                 # a baby's first time in the water is the baby-swimming card (the temperature and
                 # the arm's reach), which is what a frightened baby's parent needs first
                 "baby", "babies", "newborn", "infant", "6 month", "six month"),
          bias=4),
    # "why do athletes carbo load" was a shrug: the words name the thing and nothing keyed it.
    entry("carbo-loading",
          (("carbo load", "carbo loading", "carbo-load", "carb load", "carb loading",
            "carbohydrate loading", "glycogen", "pasta party"),
           ("why", "what", "how", "athletes", "runners", "cyclists", "before", "race",
            "marathon", "does it work", "help", "worth it", "when")),
          "Carb loading tops up the glycogen in your muscles, the fuel they run on in the last "
          "hour of a long race - the reason a marathoner hits the wall near 20 "
          "miles. It only helps for events over 90 minutes: take the last two days easy and eat "
          "8 to 10g of carbohydrate per kilo of bodyweight a day, rice, pasta, bread and "
          "potatoes, keeping the fat and fibre low so it does not sit heavy. Drink and salt "
          "matter too, and nothing new on race day.",
          # blood sugar and low-carb diets are different questions with different answers
          avoid=("diabetes", "diabetic", "blood sugar", "keto", "low carb", "weight loss",
                 "lose weight", "type 2", "insulin"),
          ask=("why", "what", "how", "does", "is", "should", "when"),
          bias=1),
    entry("parkrun-first", ("parkrun", ("what", "start", "first", "join", "do", "beginners",
                                       "walk", "slow", "how")),
          "Parkrun is a free, timed 5k every Saturday at 9am in a local park: register once online, "
          "print or screenshot your barcode, and turn up ten minutes early for the first-timers' "
          "briefing. Walkers are genuinely welcome and plenty of people walk it, so you will not be "
          "last on your own. No barcode, no time — but you can still run."),
    entry("stadium-first-time", (("stadium", "ground", "match", "tickets"),
                                 ("first time", "what to expect", "what do i need", "away",
                                  "football", "before", "arrive", "bag")),
          "Arrive 45 minutes early the first time: queues at the turnstiles and bag searches are "
          "what make people miss kick-off. Take the card you booked with, check whether your stand "
          "is seated or standing, and expect to be close to strangers and loud for two hours — that "
          "is the point. At half time, either go for food in the first five minutes or wait until "
          "the second half starts.",
          # "how do i referee a football match" and "how do i get tickets for a match" both key
          # "match", and neither is what to expect at the turnstiles
          avoid=("referee", "refereeing", "run the line", "linesman", "whistle", "offside",
                 "get tickets", "buy tickets", "ticket for a match",
                 # a pitch that is too wet is a different afternoon from the turnstiles, and the
                 # row below answers it
                 "wet", "too wet", "pitch", "waterlogged", "frozen", "snow", "frost", "muddy",
                 "called off", "play", "playing", "training", "kids", "junior")),
    # "is the ground too wet to play football" was "arrive 45 minutes early": "ground" is the
    # pitch to a footballer and the stadium to a visitor, and the first one is the question.
    entry("wet-pitch", (("wet", "raining", "rain", "waterlogged", "frozen", "snow", "frost",
                         "muddy", "mud", "ground", "pitch", "called off"),
                        ("football", "match", "game", "pitch", "ground", "play", "playing",
                         "called off", "go ahead", "training", "kids", "junior")),
          "The referee decides, not the forecast: a pitch with standing water or frozen ground is "
          "called off, and a soft, muddy one usually still plays. Take moulded studs or boots for "
          "soft ground, a change of socks and a spare towel, and check the club's page or the "
          "league's feed an hour before you leave. Junior games are called off sooner than adult "
          "ones, and there the league, not the referee, has the last word.",
          avoid=("arrive", "turnstiles", "tickets", "stadium", "stand", "seated", "kick-off",
                 "away", "premier league", "tv", "watch", "how many", "capacity", "parking",
                 # who pays the money back is the refund row's question, and it answers it: "can i
                 # get a refund if the match is called off" was sent to the referee's card, which
                 # says nothing about a ticket
                 "refund", "refunds", "money back", "get my money", "claiming"),
          bias=1),
    entry("wimbledon-titles", ("wimbledon", ("record", "titles", "wins", "won", "most",
                                             "most titles", "serena", "federer")),
          "Martina Navratilova has nine singles titles, the record, and Roger Federer has eight "
          "among the men. Serena Williams won seven."),
    entry("rugby-offside", ("offside", ("rugby", "ruck", "maul")),
          "Rugby offside is about where you stand relative to the ball, not the goal line: stay "
          "behind the ball, or behind the last foot of the ruck or maul, until it is played away, "
          "and come back onside before you get involved. In open play, a team-mate's kick puts you "
          "offside until you are put onside by a chase or a pass — and standing in front of the "
          "kicker and going for the ball is the one that gives away a penalty.",
          bias=1),

    # --- the questions a new watcher asks next ----------------------------
    entry("handball", ("handball", ("shoulder", "arm", "hand", "ball", "count", "counts",
                                    "accidental", "deliberate", "what", "rules", "mean", "means")),
          "Handball is when the ball touches the arm below where the armpit ends: the shoulder "
          "and the very top of the arm are fine. It also counts when the arm makes the body "
          "bigger, even by accident — which is why defenders tuck their arms behind their backs "
          "in the box."),
    # The shootout is a football thing, so the other sports that have a penalty of their own
    # are named out: an ice hockey penalty is a spell in the box, not five kicks each.
    entry("penalty-shootout", (("penalty shootout", "penalties", "shootout", "penalty"),
                               ("how", "work", "works", "what", "who", "how many", "order",
                                "taken", "five", "misses", "football", "soccer", "world cup")),
          "Five players from each team take a penalty each, in turn, and the side that scores more "
          "wins; if it is still level after all ten, it goes to sudden death, one each until one "
          "side misses. Everyone else waits on the halfway line, the keeper has to keep one foot "
          "on the line, and the same player cannot take twice until everyone who can has taken one.",
          avoid=("hockey", "ice", "rugby", "gaelic", "nfl", "american football", "handball",
                 "water polo", "parking", "speeding", "fine", "points on")),
    # Scoring only. Any golf line with a bare "how" in it used to land here, so "how do i
    # improve my golf swing" was answered with par and birdies; the swing-and-fix vocabulary
    # stands this entry aside instead.
    entry("golf-scoring", ("golf", ("score", "scoring", "par", "birdie", "bogey", "handicap",
                                    "stableford", "points", "eagle", "albatross", "under par",
                                    "over par", "how do you score", "how does scoring work")),
          "Every hole has a par, and you count the shots you take: one under is a birdie, two "
          "under an eagle, three under an albatross, and one over is a bogey, two over a double "
          "bogey. Add up the stroke count over 18 holes and "
          "the lowest total wins; your handicap is the number subtracted from your total so players "
          "of different ability can compete.",
          avoid=("swing", "slice", "hook", "grip", "putt", "putting", "chip", "chipping",
                 "drive", "driver", "improve", "fix", "fixing", "better", "practice", "lesson",
                 "lessons", "tips", "beginner", "start playing", "join")),
    # The names for a score, asked without the word golf: "what is a birdie" and "what does
    # eagle mean" reached nothing, and the card above is keyed on the word golf.
    entry("golf-score-names", (("birdie", "birdies", "bogey", "bogeys", "eagle", "albatross",
                               "par", "handicap", "handicaps"),
                              ("what", "whats", "mean", "means", "is", "score", "scoring",
                               "under", "over", "good")),
          "Par is the score a good player should take on the hole. One under par is a birdie, two "
          "under an eagle, three under an albatross, and one over is a bogey - two over is a "
          "double bogey. A handicap is about your average score over par, so 18 is a shot a hole "
          "over par; single figures is a strong club player and scratch is zero.",
          avoid=("how many", "how long", "course", "round", "swing", "putt")),
    # The shape of a round, not the scoring: "how many holes in a round of golf" and "how long
    # does 18 holes take" were both a shrug, and "how many in a round of golf" got the card that
    # explains rounding a number. The scoring entry holds par, birdie and handicap; the swing and
    # lesson vocabulary stays out of both, since neither answers "how do i fix my slice".
    # The first group is every phrase that names a round and nothing else, so the bare word "golf"
    # is not in it: "how many calories do you burn playing golf" and "how long is a golf course"
    # are other questions, and with "golf" plus "how many" this card took both of them.
    # The second group is the shape of a round and nothing else: "golf" plus "how many" is every
    # golf question, and it took "how many calories do you burn playing golf" and "how many
    # players in a golf team" as well as the round itself.
    entry("golf-round", (("round of golf", "golf round", "18 holes", "eighteen holes",
                          "nine holes", "9 holes", "golf group", "golf course", "golf"),
                         ("holes", "how long", "take", "takes", "long",
                          "players", "in a round")),
          "A round of golf is 18 holes, and a full round on foot takes about four hours - about "
          "two hours for nine. A group is up to four players, and the winner is whoever takes the "
          "fewest shots.",
          avoid=("score", "scoring", "par", "birdie", "bogey", "handicap", "eagle", "stableford",
                 "swing", "slice", "hook", "grip", "putt", "putting", "chip", "chipping",
                 "improve", "fix", "practice", "lesson", "lessons", "tips", "learn",
                 "beginner", "join", "club", "clubs",
                 # how long the ground is, how much exercise it is and who is in the team are
                 # other questions, and each one reached this card on "long", "in a round" or
                 # "players" alone
                 "long is", "how far", "length", "yardage", "yards", "acres", "miles",
                 "kilometres", "kilometers", "calorie", "calories", "burn", "burned",
                 "burning", "team", "teams")),
    # The short game. "how do i chip a golf ball", "how do i hit a chip shot" and "what club do
    # i chip with" all got the potato-chip recipe, because chip is a food before it is a shot,
    # and "what is a chip shot in golf", "chipping onto the green", "golf chip vs pitch" and
    # "i keep thinning my chip shots" were shrugs. Both golf cards above stand aside on chip,
    # chipping and pitch already, so this is the row they were leaving room for.
    entry("golf-chip",
          (("chip", "chips", "chipping", "chip shot", "chip shots", "pitch", "pitching",
            "pitch shot", "pitch shots", "short game", "wedge", "lob wedge", "sand wedge",
            "golf shot", "golf shots"),
           # golf words only in the second part: an ask word here ("should", "how much", "what")
           # handed it "how much should i chip in", which is the contribution card's line
           ("golf", "green", "pin", "flag", "hole", "shot", "shots", "chip", "pitch", "club",
            "clubs", "wedge", "iron", "ball", "technique", "hit", "stop", "close", "better",
            "thin", "thinning", "chunk", "chunking", "top", "topping", "blade", "blading",
            "skull", "skulling", "fat", "distance", "roll", "carry", "lie", "rough", "fairway",
            "off the green", "onto the green", "short game", "practise", "practice",
            "practising", "practicing", "drill", "drills")),
          ("A chip is a small, low shot from just off the green, and the trick is to hit down on "
           "it rather than scoop it up: take a 7, 8 or 9 iron, put the ball back in your stance "
           "with your hands ahead of it and your weight on your front foot, and make the same "
           "small swing back and through so the club takes the ball first and the turf after. "
           "Land it about a third of the way onto the green and let it run out, and change club "
           "rather than swing harder for a longer chip - a 7 iron runs more, a wedge stops sooner. "
           "A pitch is the same idea with a fuller swing and more loft, so the ball flies most of "
           "the way and stops quickly. If you keep thinning or chunking them, you are trying to "
           "help the ball into the air: keep the hands ahead, don't flick the wrists, and brush "
           "the grass after the ball."),
          # potato chips, a chip in the paint, a chip in a windscreen, a chipped tooth and the
          # other golf shots each have their own answer
          guard=_a_short_game_to_play,
          avoid=("potato", "potatoes", "chips and", "fries", "crisps", "chip shop", "chippy",
                 "chip pan", "oven", "air fryer", "deep fry", "deep fryer", "recipe", "cook",
                 "cooking", "roast", "bake", "frozen", "salt", "vinegar", "peel",
                 "windscreen", "windshield", "paint", "paintwork", "car", "van", "plate", "cup",
                 "mug", "bowl", "tile", "worktop", "table", "nail", "tooth",
                 "putt", "putting", "putter", "drive", "driver", "handicap", "score", "scoring",
                 "par", "birdie", "bogey", "eagle", "bunker", "sand", "tee", "swing", "slice",
                 "hook", "grip", "lesson", "lessons", "handicap", "stableford", "how many",
                 "calorie", "calories", "present", "gift", "money", "fiver", "tenner",
                 "contribute", "contribution", "collection", "how much", "much", "should i",
                 "office", "leaving", "colleague", "colleagues", "birthday", "wedding")),
    # "how long is a marathon" asks the distance; "how do i train for a marathon" asks for a
    # plan, and this entry has no plan in it, so it stands aside rather than half-answer.
    entry("knee-outside-pain", (("knee", "knees",
                                 # the band by name needs no knee beside it: "my it band is sore"
                                 "it band"),
                                ("outside", "outer", "side of my knee", "it band",
                                 "runs down the outside"),
                                # "my knee hurts on the outside when i run" was main's general
                                # knee answer: the outside word scored the same as the running
                                # one, and the running half is what makes it the band.
                                ("run", "running", "jog", "jogging", "cycle", "cycling")),
          "Pain on the outside of the knee that comes on after ten or twenty minutes of running is "
          "usually the iliotibial band rubbing: it is a tracking problem, not a worn joint. Cut the "
          "run short at the first twinge rather than running through it, run on flatter, softer "
          "ground, and shorten your stride. Twice a day, foam-roll the outside of the thigh and do "
          "side-lying leg raises and clams; it settles in weeks if you keep runs short till it does.",
          # the front-of-knee answer, the stairs answer and a doctor's question are not this one.
          # Main's fitness.knees-when-running answers "my knees hurt when i run", so this entry is
          # for the outside-of-the-knee line and only that: the bias keeps it off the ties
          bias=2,
          # the running word only counts with the outside one: "my knee hurts when i run" is
          # main's general answer, and knee plus run alone is not this pain.
          ask=("outside", "outer", "side of my knee", "it band", "runs down the outside"),
          avoid=("front", "stairs", "stair", "downstairs", "climbing", "swelling", "swollen",
                 "locked", "locking", "gave way", "clicking", "surgeon", "arthroscopy",
                 "cruciate", "acl", "meniscus")),
    entry("race-distances", (("5k", "10k", "10km", "parkrun distance"),
                             ("far", "long", "miles", "km", "kilometres", "kilometers",
                              "distance", "how")),
          "A 5k is 3.1 miles and a 10k is 6.2 miles; a half marathon is 13.1 miles (21.1 km) and a "
          "marathon 26.2 miles (42.2 km). Races are named in kilometres but most runners in the UK "
          "and the US talk in miles, which is why the two numbers never look related.",
          # the marathon lines are main's answer and a better one: they explain the odd 0.2 and
          # point at a training plan
          # "how do i save 10k" is money with a shorthand on it: 10k of savings is not ten
          # kilometres, and the running answer was what people got. A race line never has a
          # money word in it. And "how does couch to 5k work" asks for the programme, not the
          # distance.
          avoid=("marathon", "train", "training", "plan", "pace", "faster", "improve",
                 "save", "saves", "saving", "saved", "money", "afford", "budget", "deposit",
                 "cash", "pound", "salary", "invest", "debt", "savings",
                 "couch to 5k", "couch to five k", "c25k"),
          # A distance is the question the words name outright, so it outranks a row that only
          # touches the line by a near miss: "how far is a 5k" scores "far" against the expenses
          # row's "fare", and without the bias the two tie and the mileage answer loses.
          bias=1),
    entry("marathon-distance", ("marathon", ("long", "longer", "longest", "km", "miles", "42",
                                             "how", "length", "distance", "far",
                                             # the comparison words, so the card is reached at all
                                             # when the half is named beside the full race
                                             "difference", "compare", "compared", "versus",
                                             "vs", "twice", "further")),
          "A marathon is 26.2 miles, or 42.2 kilometres \u2014 the odd 0.2 is there because the "
          "1908 London course was extended to finish in front of the royal box. A half marathon "
          "is the obvious first step, and most training plans build up to it over about sixteen "
          "weeks.",
          # "how far is a half marathon" holds the word marathon and was answered with 26.2
          # miles: race-distance-half answers the half, and this one keeps the full distance
          avoid=("train", "training", "plan", "planning", "prepare", "preparing", "build up",
                 "ready", "couch", "beginner", "slowest", "pace", "time"),
          # "half", "13.1" and "21.1" used to be in that avoid list, which stood this card down on
          # every comparison of the two races as well as on the half's own questions. The guard
          # draws the line where the avoid could not: a half with no comparison in the line is
          # still the half's question.
          guard=_half_is_not_the_question),
    entry("marathon-training", ("marathon", ("train", "training", "plan", "prepare", "build up",
                                             "first marathon", "ready", "couch", "start running")),
          "Start where you can already run 5km comfortably and build up over about sixteen weeks: "
          "three runs a week (one long, two short and easy), and add no more than 10% to the weekly "
          "total. Your longest run only needs to reach 32km, three weeks before the day, then taper "
          "— the last two weeks are much shorter on purpose. Do not do your longest run and your "
          "fastest in the same week."),
    # --- the body in the first months of exercise -------------------------
    entry("cramp-running", (("cramp", "cramps", "cramping"),
                            ("run", "running", "jog", "jogging", "exercise", "exercising",
                             "workout", "training", "after", "walking", "walk", "playing")),
          "Cramp in a run is usually a tired muscle, not a lack of salt: it comes on late in a "
          "session and eases when you stop and stretch. Walk, then stretch the calf against a "
          "wall for 20 to 30 seconds. To keep it away, build your distance more slowly and drink "
          "water with a pinch of salt if you sweat heavily for more than an hour.",
          avoid=("period", "periods", "stomach", "tummy", "dog", "cat"),
          # the science entry explains what a cramp is and scores the same on "cramp in my calf",
          # so the exercise one has to declare that it wants the line
          bias=2),
    entry("knee-noise", (_NOISY, ("knee", "knees", "kneecap", "joint", "joints")),
          _noisy_knee),
    entry("knee-pain-stairs", (("knee", "knees"),
                               ("stairs", "stair", "staircase", "steps", "climb", "climbing",
                                "downstairs", "upstairs", "up steps", "down steps")),
          "Pain at the front of the knee on stairs is the kneecap being pulled off line by weak "
          "or tight muscles around it, which is common in new runners and in people who sit all "
          "day. Three times a week do sit-to-stands, step-ups and wall sits, and ease off hills "
          "and deep squats for a fortnight. See a physio if it swells, locks, or the knee gives "
          "way under you.",
          avoid=_NOISY + ("fell", "fall", "fallen", "twisted", "landed", "can't walk",
                          "cant walk")),
    entry("protein-how-much", ("protein", ("much", "need", "needed", "day", "daily", "grams",
                                          "grammes", "enough", "target", "get")),
          _protein,
          # "how much protein in an egg" is one number for one food, not a daily target: a
          # confident answer to a question they did not ask is worse than the shrug.
          # The target is asked about the person - a day, a kilo of body weight, a muscle
          # goal - and never about a named food: "how much protein in a scone" is one number
          # for one food, and on main nine of thirty-three food lines got this target card
          # instead of any figure at all. The ask is the person shapes, so the row stands down
          # for a food question and something else answers it, or the person gets an honest
          # shrug rather than a card about their own body weight.
          ask=("a day", "per day", "daily", "in a day", "do i need", "i need", "need",
               "should i eat", "should i have", "to build muscle", "build muscle", "bulk",
               "bulking", "lose weight", "losing weight", "per kilo", "a kilo", "per kg",
               "my weight", "body weight", "weigh", "target", "enough", "diet", "each meal",
               "a meal", "protein powder", "grams of protein", "grammes of protein",
               "how many grams"),
          avoid=("dog", "cat", "puppy", "kitten", "rabbit", "hamster", "horse",
                 "egg", "eggs", "chicken", "beef", "steak", "pork", "fish", "salmon", "tuna",
                 "milk", "cheese", "yoghurt", "yogurt", "beans", "lentils", "tofu", "oats",
                 "porridge", "bread", "rice", "pasta", "banana", "apple", "nuts", "almonds",
                 "peanut", "powder", "shake", "burger", "bacon")),
    # "how many days in a week should i run" is a training plan, not a conversion of a week
    # into days: the measure is the object of a question about what to do. The answer is the
    # frequency a beginner can hold, with the rest days counted as part of it.
    # "how many times a week should i go out" is the frequency of a new running habit, and the
    # line names no run: "go out" is how people say it once they have started, so the phrase is
    # part of the key. Without it the follow-up after a plan was answered with the plan again.
    entry("how-often-to-run", (("run", "running", "jog", "jogging", "go out", "going out",
                                "get out for", "out for a run", "out running"),
                               ("how many days", "days a week", "times a week", "a week",
                                "days in a week", "days in the week", "rest days", "too many days",
                                "how much",
                                # "how long should i run for" is a duration question and this is
                                # the entry that holds the durations: 20 to 30 minutes.
                                "how long")),
          "Three runs a week is plenty to start, with a rest day between each: two easy runs of "
          "20 to 30 minutes and one a little longer. Add a fourth only when those three feel "
          "comfortable, and keep any increase to about 10% a week. The rest days are when the "
          "fitness is built, so they are part of the plan, not a gap in it.",
          # The frequency of a run is not the distance, the pace, the shoes, a race plan or a
          # pain: those have their own answers.
          # `how much` is a bare key word, so a line that spends it on money ("how much does it
          # really cost to run a car") reached this answer; a car is not a run.
          avoid=("car", "cars", "cost", "costs", "petrol", "insurance", "mot", "train", "bus",
                 "marathon", "half marathon", "10k", "5k", "parkrun", "race", "pace", "faster",
                 "calories", "weight", "shoe", "shoes", "injury", "knee", "shin", "sore", "pain",
                 "plan", "training plan", "treadmill speed", "treadmill pace",
                 # "how long" is a key here for the durations, so a rest question spent it on the
                 # plan: "how long to rest between runs" wants the rest-day answer, not three
                 # runs a week. How long to rest is the rest entry's line.
                 "rest between", "between runs", "between each run", "how long to rest",
                 "rest after", "how long should i rest", "recovery",
                 # `how long` also spends itself on the things around a run, and those have
                 # their own answers: "how long should i wait after eating to run" is the
                 # eat-before-run rule (a banana an hour or two before), and "how long should i
                 # run in the cold" is the cold-weather card. Both were read as the plan and
                 # answered "three runs a week", which is not what was asked.
                 "after eating", "after a meal", "after lunch", "after dinner", "eating",
                 "ate", "wait", "waiting", "in the cold", "cold", "cold weather", "cold out",
                 "in the heat", "the heat", "hot weather", "raining", "rain", "wind", "windy")),

    # "ran" is its own word to the matcher, not a form of "run": "been years since i ran" is the
    # same request as "i want to start running", and it reached nothing at all.
    entry("start-running",
          # "couch to 5k" is the plan by name, and it was the shrug: the line names the course
          # rather than the verb, so the plan had no word of its own to match.
          (("couch to 5k", "couch-to-5k", "couch to 5 km", "c25k",
            "running", "run", "jogging", "jog", "ran", "jogged", "went running",
            # a person who calls themselves the runner is asking the beginner's question:
            # "any tips for a beginner runner" and "im a beginner runner" were both a shrug
            "runner", "runners", "new runner", "beginner runner"),
                            # "into" alone is not a start: "shes 30 and into running" is a
                            # detail about somebody else, not a request for a plan. "get into"
                            # is the ask, and keeps "i want to get into running".
                            # The same ask for a return is "get back into" / "getting back
                            # into" - ask-shaped words, not "back into" on its own, because
                            # "my wife got back into running" is news about her.
                            ("start", "starting", "begin", "beginner", "never", "nothing",
                             "couch", "first", "get into", "getting into",
                             # "i get out of breath after two minutes" is the same question
                             # asked by someone who has already tried
                             "out of breath", "out of puff", "can't run", "cant run",
                             "get back into", "getting back into",
                             # coming back after years: the word is "ran", which the matcher
                             # does not read as a form of "run", and the stop that came before it
                             "used to run", "used to jog", "havent run", "haven't run",
                             "stopped running", "start running", "running after years",
                             "jog after years", "been years",
                             "years since", "years ago", "since school",
                             # "i want to run 5k without stopping" is the same first-goal ask
                             "without stopping", "non stop", "nonstop", "keep going",
                             "all the way",
                             # the same beginner's ask in its tip-and-advice clothes
                             "tips", "tip", "advice", "any advice", "pointers",
                             # "i can barely jog 5 minutes" is the same ask from somebody who
                             # has already tried: the distance run is the fact, and "barely" /
                             # "only manage" is the ask. A run word still gates it, so "barely"
                             # in a line about anything else stays where it was.
                             "barely", "barely jog", "cant even", "can't even",
                             "can only", "only manage", "manage to jog", "manage to run",
                             "struggle", "struggling", "really hard", "so hard",
                             "for a minute", "two minutes", "2 minutes", "a few minutes",
                             "30 seconds", "thirty seconds")),
          "Start with run-walk: one minute of easy jogging, two minutes of walking, repeated for "
          "20 minutes, three times a week with a rest day between. Each week add a minute to the "
          "jog and take one off the walk, and in about eight weeks you will run 20 minutes "
          "without stopping. Go slowly enough to speak in short sentences - that is the pace that "
          "builds the habit.",
          # "can't run" is mostly software, and a body that cannot run is a medical question,
          # not a beginner's plan: "my phone cant run this app", "i cant run because of my
          # asthma", "i cant run at all since my hip operation" all took the run-walk plan.
          # "injury" was held out whole, because a body that is hurt is not asking for a plan.
          # But the commonest way people ask for one is the thing they want to avoid: "how do i
          # start running without injury" is a beginner's question, and the bare word stood the
          # card down and left the search hedge. The complaint itself is a shape ("my injury",
          # "injured", "recovering from") and stays held out below.
          avoid=("marathon", "half marathon", "10k", "parkrun", "race", "train", "training",
                 "plan", "shoe", "shoes", "sore",
                 # the complaint, as a shape: "i cant run because of my injury" is a body, and
                 # "how do i start running without injury" is a plan. The bare word cannot tell
                 # them apart, and holding it out whole cost the beginner's card every line that
                 # said what it wanted to avoid ("without getting injured" still has its answer).
                 # A body that complains is a question about the body, not a beginner's plan.
                 # "so hard" / "really hard" / "struggle" are the key's asks and a run word gates
                 # them, so "jogging hurts my knees so hard" and "my knee is really hard to bend"
                 # took the run-walk plan; the complaint stands the card down and the sore-knee
                 # entry answers. The words are held as whole forms, so "how do i start running
                 # without hurting myself" keeps the plan.
                 "knees", "ankles", "shins", "calves", "achilles", "plantar", "soreness",
                 "hurt", "hurts", "hurting", "pain", "pains", "painful", "ache", "aches",
                 "aching", "stiff", "swollen", "swelling", "bend", "bending", "limp", "limping",
                 "my injury", "the injury", "an injury", "injury is", "injury has",
                 "injury wont", "injured my", "got injured", "been injured", "was injured",
                 "am injured", "is injured", "back from injury", "back from an injury",
                 "recovering from", "recovery from", "knee injury", "shin injury",
                 "ankle injury", "injury prevention",
                 # a return to running is the shape most people write, and it is the same body
                 # as "my injury": "how do i start running when injured" was being given the
                 # beginner's plan to a person who cannot run yet. The asked-for absence
                 # ("without injury", "without getting injured") is not one of these.
                 "when injured", "after injury", "after an injury", "running injured",
                 "run injured", "still injured", "start running injured",
                 # typed without the apostrophe, which is how most people write it
                 "im injured", "i'm injured",
                 "knee", "shin", "rest", "between",
                 "how often", "days a week", "car", "cost", "boiler", "cheaper",
                 # software
                 "app", "apps", "game", "games", "phone", "laptop", "computer", "software",
                 "program", "programme", "windows", "console", "android", "iphone", "app store",
                 # a body that cannot run
                 "operation", "surgery", "asthma", "hip", "doctor", "gp", "hospital",
                 "arthritis", "diagnosis", "disability", "wheelchair",
                 # "the toilet wont stop running" is the cistern, not a beginner's plan, and
                 # "stop running" folds to the same words as the key's "stopped running"
                 "toilet", "loo", "cistern", "tap", "taps", "flush", "flushing", "plumbing",
                 "sink", "leak", "leaking", "drip", "dripping", "engine", "motor", "fridge",
                 "freezer", "washing machine", "dishwasher",
                 # and a person run off their feet is busy, not a beginner runner: "ive been
                 # run ragged since the new term started" took the couch-to-5k plan because
                 # `run` and `started` are this entry's key.
                 "run ragged", "running ragged", "ran ragged", "run off my feet",
                 "run off our feet", "running off my feet", "off my feet",
                 "back on my feet",
                 # what a runner eats and drinks is a food question, and this key holds "runner"
                 # and "beginner": "what should a beginner runner eat" was given the run-walk
                 # plan, which answers a question nobody asked.
                 "eat", "eats", "eating", "ate", "food", "foods", "diet", "nutrition",
                 "carbs", "carb", "fuel", "fuelling", "fueling", "breakfast", "hydration",
                 "hydrate", "drink", "drinks", "protein", "caffeine", "gel", "gels",
                 # the other things called a runner: a rug in a hall, a bean, a sledge, a
                 # climbing plant, a horse in a race and a candidate for a job
                 "rug", "rugs", "carpet", "carpets", "hallway", "hall", "corridor", "stairs",
                 "bean", "beans", "sledge", "sled", "plant", "plants", "creeping",
                 "runner up", "runner-up", "front runner", "frontrunner", "job", "interview",
                 "candidate", "horse", "horses", "racehorse", "race horse")
                 + _REPORTED),
    entry("run-faster-easy-miles",
          (("get better at running", "better at running", "improve my running", "run faster",
            "get faster", "running faster", "faster", "improve my 5k", "better 5k", "5k time",
            "my 5k", "10k time", "get quicker", "personal best", "pb", "pace", "sprint",
            "interval", "intervals", "hill repeats"),
           # "5k", "10k" and "marathon" are not here: race-distances owns those words, and
           # _rank gives its point for a word only one entry in the domain uses, so sharing
           # them made "how far is a 5k" a four-all tie that the expenses row won.
           ("run", "running", "jog", "jogging", "train", "training", "faster", "quicker",
            "time", "improve", "better", "get")),
          "Speed comes from easy miles, not hard ones: run four times a week with three of those "
          "slow enough to chat through, and make the fourth the only hard session - 6 x 2 minutes "
          "quick with 2 minutes of jogging in between, at a pace where you could manage one more. "
          "Add 5 to 10% a week, keep one full rest day, and expect six to eight weeks before the "
          "same 5k feels easier. Runners who only go hard stall after a month.",
          # a first plan, a distance, an injury, a race or a heartbeat question is another
          # entry's line
          avoid=("heart", "heartbeat", "pulse", "beat", "beats",
                 "start", "starting", "beginner", "never run", "couch", "first run", "out of breath",
                 "how far", "how long is", "miles", "km", "kilometres", "kilometers",
                 "marathon", "half marathon", "train for", "training for", "plan for",
                 "injury", "injured", "knee", "shin", "splints", "pain", "sore", "hurt",
                 "shoe", "shoes", "watch", "app", "treadmill", "program",
                 # a heart that beats faster is the body's answer, not a training plan: this key
                 # has "faster" and "run", so "why does my heart beat faster when i run" reached
                 # the speed plan
                 "heart", "heartbeat", "heart rate", "pulse", "beats")
                 + _REPORTED + _ASKED_AFTER,
          # "get faster" is a shape four other hobbies use: with "get", "better" and "improve"
          # in the key, "how do i get faster at swimming" - and at cycling, typing, chess - was
          # given a running plan. An ask naming the sport keeps those out without narrowing a
          # single running line, because every one of them says so.
          ask=("run", "running", "runner", "ran", "jog", "jogging", "5k", "10k", "mile",
               "miles", "marathon", "pace", "sprint", "sprints", "interval", "intervals",
               "hill", "hills", "training", "train")),
    entry("stitch", ("stitch", ("run", "running", "jog", "jogging", "side", "get", "getting",
                                "exercise", "walk")),
          "A stitch is a cramp in the sheet of muscle under the diaphragm, and it usually means "
          "you are breathing shallowly or ran too soon after eating. Slow down, breathe out hard "
          "through pursed lips, and press your fingers under the ribs on the sore side while you "
          "walk it off. Leave two hours between a proper meal and a run, and warm up for five "
          "minutes before you pick up the pace.",
          guard=_not_a_stitch_in_a_wound),
    entry("sore-after-exercise", (("sore", "aching", "achy", "stiff", "stiffness", "tender",
                                   # "hurts" and "ache" are how most people say sore, and without
                                   # them the decision rule stepped out of "my back hurts after
                                   # the gym, should i see a doctor" for this row to answer, and
                                   # the person got the booking script instead
                                   "hurt", "hurts", "hurting", "ache", "aches"),
                                  ("gym", "workout", "exercise", "run", "running", "weights",
                                   "lifting", "next day", "day after", "two days", "walking")),
          "That ache a day or two after new exercise is normal and it is not damage: it is the "
          "muscle repairing itself after work it is not used to. Keep moving gently - a walk, an "
          "easy swim - rather than resting completely, drink water, and expect it to be worst "
          "about 48 hours in and gone within four days. Next time start with less weight or fewer "
          "repeats than you think you can do.",
          # An ache that comes on *during* a movement is not the ache after one. "my hip aches
          # when i walk" and "my shoulder aches when i lift my arm" were both told that a day or
          # two after new exercise is normal, when the person had said nothing about exercise at
          # all; the joint entries answer those, and each of them names the movement.
          avoid=("throat", "burn", "sunburn", "mouth", "eyes", "eye", "ulcer", "cough", "cold",
                 "when i walk", "when i walking", "when i run", "when i stand", "when i sit",
                 "when i climb", "when i bend", "when i lift", "when i move", "when i type",
                 "when i wake", "when i get up", "when i go up", "aches when", "ache when",
                 "hurting when", "hurts when", "hurting when", "pain when", "all the time",
                 "every day", "every morning")),
    # The day after a run is when people ask how to stretch, and nobody says "stretch a muscle".
    entry("stretch-calf", (("stretch", "stretches", "stretching", "loosen", "tight"),
                           ("calf", "calves", "achilles", "shin", "shins", "leg", "legs",
                            "after a run", "after running", "before a run", "hamstring",
                            "hamstrings", "quads", "quad", "thigh", "thighs",
                            # legs tight after a ride are a stretch question too: "my legs are
                            # tight after cycling" was the dry-skin card
                            "cycling", "cycled", "cycle ride", "after a ride", "spin class")),
          _stretch,
          # "my legs are tight after cycling" was the dry-skin card: a line that names a muscle
          # and a ride is the stretch
          bias=1,
          avoid=("bed", "sleep", "back", "neck", "shoulder", "shoulders", "hair", "canvas",
                 "ear", "ears", "leather", "shoes", "waistband", "jeans")),
    entry("rest-days", (("rest days", "rest day", "recovery days", "recovery day",
                         "days off training", "days off the gym"),
                        ("need", "many", "how", "gym", "training", "train", "week", "between",
                         "running", "exercise", "weights", "should")),
          "The rule that works for most people is one full rest day a week plus an easy day "
          "between hard ones: never two hard sessions back to back. Muscle is built while you "
          "recover, not while you lift. If you want to move every day, make the in-between days "
          "walks, easy swimming or stretching rather than another full session.",
          ),
    entry("rest-between-sessions", (("rest", "recovery"),
                                    ("after", "between", "sessions", "workout", "workouts",
                                     "lifting", "training", "gym")),
          "One easy day between hard sessions is enough, and it does not have to be a day in bed: "
          "a walk, a swim or stretching keeps you moving without loading the same muscles. Two "
          "hard sessions back to back is the pattern that leaves people sore and stale. Sleep and "
          "food do more of the rebuilding than any recovery gadget.",
          # someone who has hurt themselves is a different question from a training plan
          avoid=("bed", "sleep", "nap", "tired", "baby", "work", "holiday", "tweaked", "tweak",
                 "bad", "hurt", "hurts", "pulled", "injury", "injured", "slipped", "boxes",
                 "back",
                 # the rest between two sets is a session's own question (`rest-between-sets`
                 # in fitness.py); this entry is the rest between sessions
                 "sets", "set", "reps", "rep", "between sets", "each set")),
    entry("how-often-exercise", (("run", "running", "jogging", "gym", "exercise", "workout",
                                  "workouts", "weights", "swim", "swimming"),
                                 ("how often", "how many times", "times a week", "days a week",
                                  "per week", "a week", "frequency", "regularly")),
          "Three sessions a week is the number to aim for, with a day off between them, and it is "
          "the same for running, the gym or swimming. The health guideline is 150 minutes of "
          "something that makes you breathe harder each week, which is three 50-minute sessions "
          "or five half hours. Two or three weeks in, that gets easier and you can add a session.",
          avoid=("rest", "marathon", "10k", "parkrun", "race"),
          guard=_not_a_timetable_that_runs),
    # The figure a recovery question wants, scaled to what was done. "how long to recover after a
    # run" was the cold-and-flu rule and "how long to recover after a marathon" was how long a
    # marathon is - both on the subject, neither a recovery time. The distance in the line (or in
    # a line just before it) picks the figure; a line that names none gets the ladder.
    entry("recovery-time",
          (("recover", "recovers", "recovery", "recovering", "rest up", "ease back",
            "easy days", "legs recover"),
           ("how long", "how many days", "how much rest", "days", "how soon", "when can i",
            "time off", "how many weeks")),
          _recovery_time,
          # a recovery is about a session, and the line that asks how long it takes says so in its
          # own words or leans on the session just before it; the ask keeps the other "recover"
          # senses - a password, a deleted file, a car - out of the answer entirely
          ask=("recover", "recovers", "recovery", "recovering", "rest up", "ease back",
               "easy days", "legs recover"),
          bias=3,
          avoid=("ill", "illness", "flu", "cold", "fever", "sick", "virus", "covid",
                 "chest infection", "cough", "throat", "tonsillitis", "pneumonia",
                 "surgery", "operation", "hospital", "injury", "injured", "physio",
                 "broken", "fracture", "fractured", "sprain", "sprained", "strain",
                 "strained", "sore", "pain", "hurt", "hurts", "addiction", "grief",
                 "divorce", "breakup", "depression", "burnout", "bereavement",
                 # "recover" is also what a phone, an account and a car do
                 "password", "account", "email", "file", "files", "laptop", "phone",
                 "car", "van", "vehicle", "truck", "deleted", "data", "photos",
                 "position", "room", "service", "boiler", "heat", "waste", "copper",
                 "gold", "oil", "sleep", "nap", "baby", "birth", "caesarean",
                 # a body coming back from something is never this row's question, and the vet's
                 # recovery is the pets answer: "how long does a cat take to recover from
                 # neutering" was told to scale it to a 5k
                 "cat", "cats", "dog", "dogs", "puppy", "puppies", "kitten", "kittens",
                 "pup", "vet", "neuter", "neutering", "neutered", "spay", "spayed",
                 "stitches", "wound", "scar", "burn", "bruise", "twisted", "eye", "eyes",
                 "vision", "screen", "screens", "bug", "virus", "vomit", "vomiting",
                 "diarrhoea", "stomach", "food poisoning", "migraine", "tooth", "teeth",
                 "dental", "wisdom", "extraction", "jet lag", "hangover",
                 # an operation has its own timeline - "how long is recovery after a hip
                 # replacement" was told to scale it to a 5k - and so does a body part that is
                 # healing: knee, hip and shoulder names are the hospital answer's question
                 "replacement", "replacements", "hip", "hips", "knee", "knees", "shoulder",
                 "shoulders", "joint", "joints", "heal", "heals", "healing", "healed",
                 "cast", "plaster", "physiotherapy", "physiotherapist", "consultant",
                 "operation", "operated",
                 # the rest between two sets is a session's own question
                 "sets", "set", "reps", "rep", "between sets", "each set")),
    # The same figure under the word people more often use: "how long should i rest after a 5k"
    # was handed how long a 5k takes to run. The guard is the distance in the line, so the rest of
    # a roast, of a knee and between gym sessions stays with its own answer.
    entry("rest-after-a-distance",
          (("rest", "resting", "rest up", "rest day", "rest days", "day off", "days off"),
           ("how long", "how many days", "how much rest", "days", "how soon", "time off",
            "how many weeks")),
          _recovery_time,
          guard=_a_distance_is_named,
          bias=3,
          avoid=("ill", "illness", "flu", "cold", "fever", "sick", "injury", "injured",
                 "hurt", "hurts", "pain", "sore", "surgery", "operation", "hospital",
                 "replacement", "replaced", "hip", "knee", "shoulder", "joint", "heal",
                 "healing", "cast", "plaster", "physio",
                 "meat", "steak", "roast", "roasted", "chicken", "turkey", "lamb", "beef",
                 "pork", "brisket", "ribs", "joint of", "carving", "carve", "foil", "oven",
                 "sets", "set", "reps", "between sets", "each set")),
    entry("badminton-basics", ("badminton", ("play", "rules", "score", "scoring", "how", "court",
                                             "points", "serve")),
          "Games go to 21 points, and you score on every rally whoever served, so a game is quick; "
          "win two games and you win the match. The bit that catches beginners is that the shuttle "
          "cannot be hit before it crosses the net, and a serve has to go diagonally and land past "
          "the short service line.",
          # a racket grip, a restring and a new pair of shoes are kit questions, not the rule
          avoid=("grip", "grips", "replace", "replacing", "restring", "resting", "strings",
                 "string", "tension", "tensions", "broken", "buy", "buying", "which racket",
                 "racket", "racquet", "shoes", "net", "height", "post")),
    entry("hat-trick", ("hat trick", ("what", "what's", "mean", "means", "three", "goals",
                                          "why", "called")),
          "Three goals by the same player in one match is a hat-trick, and a perfect one is three in "
          "a row with nobody else scoring in between. The name comes from cricket, where a bowler "
          "who took three wickets with three balls was given a hat by the club."),
    entry("f1-points", (("formula 1", "formula one", "f1", "grand prix"),
                        ("points", "score", "scoring", "work", "championship", "how", "win")),
          "Points go to the top ten: 25 for a win, then 18, 15, 12, 10, 8, 6, 4, 2, 1. The bonus "
          "point for the fastest lap only ran up to 2024 and has been dropped, so do not count on "
          "it. Sprint weekends pay points to the top eight, and the driver and the team with the "
          "most points at the end of the year are the champions."),

    entry("var", (("var",), ("football", "soccer", "mean", "work", "video", "whats", "what")),
          "VAR is the video assistant referee: off-pitch officials watch replays and can tell the "
          "referee to review four things — a goal, a penalty, a straight red card, or a case of "
          " mistaken identity. The referee still makes the final call."),
    entry("keeping-kids-apart", (("chasing", "chase"), ("ball", "kids", "children", "all")),
          "Split the pitch into four small squares and put three or four children in each with "
          "one ball: everyone touches the ball, nobody can chase the whole crowd. Rotate the "
          "squares every five minutes so they meet each other, and finish with a game on a "
          "short, wide pitch so there is always someone to pass to."),
    entry("cricket-formats", (("cricket", "test match", "t20", "twenty20"), ("how long", "last",
                                                                            "days", "format",
                                                                            "formats", "how many",
                                                                            "many", "difference")),
          "A Test match is up to five days, 90 overs a day; a one-day match is 50 overs a side; a "
          "T20 is 20 overs a side and takes about three hours. Same game, very different patience "
          "required.",
          # what an over is, and how many balls are in one, is the basics card's answer: a bare
          # "over" in the ask sent "what's an over in cricket" here
          avoid=("whats an over", "what is an over", "whats a over", "an over",
                 "how many balls")),
    entry("cricket-over", (("over in cricket", "an over", "overs in an innings"),
                            ("balls", "six", "how many", "many", "mean", "means", "what", "is")),
          "An over is six balls bowled by one bowler from one end, then someone else bowls from "
          "the other end. In a limited-overs game a bowler can bowl at most a fifth of the overs "
          "- 10 in a 50-over match, 4 in a T20."),
    entry("cricket-lbw", (("lbw", "leg before wicket"), ("cricket", "mean", "rule", "out")),
          "Leg before wicket: the ball hit the batter's leg (or body) when it would have gone on "
          "to hit the stumps, and the bat wasn't involved first. The umpire has to think the ball "
          "was going on to hit, so a ball pitching outside leg, or a batter who hit it first, is "
          "not out."),
    entry("cricket-duck", (("duck",), ("cricket", "mean", "out", "score")),
          "A duck is a batter out for nought, and a golden duck is out first ball. It's just "
          "slang for zero on the scoreboard — the shape of the 0 looks like a duck's egg."),
    entry("cricket-wicket", (("wicket", "wickets"),
                             ("what", "whats", "mean", "means", "is", "how many", "three",
                              "stumps", "bails")),
          "A wicket is the set of three stumps and two bails a batter defends, and taking a "
          "wicket means getting a batter out - so ten wickets in an innings is all ten "
          "dismissals. The wicket-keeper stands behind it, with the slips beside them."),
    entry("cricket-no-ball", (("no ball", "no balls", "no-ball"),
                              ("cricket", "mean", "means", "what", "whats", "is", "why")),
          "A no ball is the bowler overstepping the popping crease, throwing instead of bowling, "
          "or sending down a full toss above waist height: the batting side gets a run and the "
          "ball is bowled again. In one-day and T20 cricket the next ball is a free hit, when a "
          "batter can only be run out."),

    # --- tennis, golf, darts, snooker ---------------------------------------,
    entry("tennis-sets", (("tennis", "wimbledon", "grand slam"), ("how many sets", "sets", "best of",
                                                                "match")),
          "Women's matches at the Grand Slams are best of three sets and men's are best of five, "
          "except that most other tournaments are best of three for both. A set is first to six "
          "games, two clear.",
          bias=1),
    # "what is a grand slam" was answered with the sets rule, which talks about the Slams without
    # saying what they are. The four tournaments are the fact the question wants.
    entry("tennis-grand-slam", (("grand slam", "grand slams"),
                                ("what", "whats", "is", "mean", "means", "four", "win", "won",
                                 "all four", "which")),
          "The Grand Slams are the four biggest tournaments: the Australian Open in January, the "
          "French Open at Roland-Garros on clay, Wimbledon on grass, and the US Open. Winning all "
          "four in the same year is a calendar Grand Slam - Rod Laver did it in 1969 and Steffi "
          "Graf in 1988.",
          bias=2,
          # a Grand Slam is a different thing in golf and in the Six Nations, and each has its
          # own card below
          avoid=("sets", "best of", "how many sets", "deuce", "tie-break", "score", "scoring",
                 "golf", "majors", "masters", "rugby", "six nations", "triple crown")),
    # "how" is not a rules word: with it here this card answered "how do i serve in volleyball",
    # "how do i spike" and every other technique question about the game.
    entry("volleyball-basics", (("volleyball", "volley ball"),
                                ("players", "how many", "rules", "work", "score",
                                 "scoring", "team", "play", "side")),
          "Volleyball is six a side, and each team can touch the ball three times before sending "
          "it over - a block does not count as one of them. Every rally now scores a point, sets "
          "go to 25 and the deciding fifth set to 15, and you have to be two points clear."),
    entry("snooker-basics", (("snooker",), ("rules", "work", "how", "play", "147", "reds",
                                            "colours")),
          "Pot a red (1 point), then a colour (2 to 7), and put the colour back on its spot; carry "
          "on that way until the reds are gone, then take the colours in order. The maximum break "
          "is 147: fifteen reds with fifteen blacks, then all the colours."),

    # --- rugby, basketball, other team sports -------------------------------,
    entry("basketball-basics", (("basketball", "basketballs"), ("rules", "work", "how", "play",
                                                           "points", "quarters", "players")),
          "Basketball is five a side over four quarters, and you score 2 points in the basket, 3 "
          "from behind the arc, and 1 from the free-throw line. You have to keep dribbling or pass "
          "— picking the ball up and walking with it is a travel.",
          # how long the game runs is the length row's question, and a foul is its own answer
          avoid=("how long", "long", "last", "minutes", "foul", "fouls", "fouled")),
    # A game's length is the first thing a new watcher asks, and "how long is a basketball game"
    # was reaching the board games card on "game" and "long".
    entry("basketball-length", (("basketball", "basketballs"),
                                ("how long", "long", "last", "minutes", "quarters",
                                 "periods", "how many quarters")),
          "Four quarters: 10 minutes each in international (FIBA) games, so 40 minutes of play, "
          "and 12 each in the NBA for 48. The clock stops on every whistle, so the whole game "
          "takes about two hours.",
          bias=1,
          avoid=("foul", "fouls", "fouled", "scoring", "points", "rules", "travel")),
    entry("basketball-foul", (("foul", "fouls", "fouled", "fouling"),
                              ("basketball", "mean", "means", "what", "whats", "is",
                               "how many", "before", "out", "personal")),
          "A foul is illegal contact - a push, a hold, or barging into a shooter - and the other "
          "side gets the ball, or free throws if it happened while shooting. Five fouls and you "
          "are out of the game (six in the NBA), and a team's fouls add up: once it reaches the "
          "limit in a quarter, every later foul gives the other side free throws."),
    # Field hockey and ice hockey are different games, so one card has both answers in it. The
    # length, the team size and the surprise - field hockey dropped offside in 1999 - are what
    # people look up.
    entry("hockey-basics", (("hockey", "field hockey", "ice hockey"),
                            ("how long", "long", "players", "many", "offside", "rule", "rules",
                             "work", "basics", "minutes", "quarters", "periods", "team",
                             "game", "match")),
          "Field hockey is 11 a side over four 15-minute quarters, so 60 minutes of play, and it "
          "has no offside rule - that was dropped in 1999, though you can only score from inside "
          "the shooting circle and only with the flat side of the stick. Ice hockey is a different "
          "game: six on the ice including the goalie, three 20-minute periods, and there the blue "
          "line does make an offside.",
          bias=1,
          avoid=("f1", "formula")),
    entry("join-a-club", (("join", "joining", "club", "clubs", "start playing", "back to playing",
                           "taster session", "local club", "sport club"),
                          ("football", "netball", "hockey", "cricket", "rugby", "basketball",
                           "tennis", "swimming", "running", "badminton", "rounders", "league",
                           "adult", "beginner")),
          "Search for the sport plus your town and 'club', then email and ask about a taster "
          "session: most clubs have a beginners' or social night that costs a few pounds. Turn up "
          "to that rather than a match, and say you're new — clubs are used to it, and it's the "
          "fastest way to find people at your level.",
          # a kit question is not a joining question: "what does she need to start, kit and all
          # that" was answered with the same joining reply a second time in a row.
          avoid=("kit", "equipment", "what does", "what do i need", "what should she", "shoes",
                 "boots", "bring", "wear",
                 # "am i too old to start playing football" is the age question, and the answer
                 # to it is how a grown-up gets back into a sport, not where the nearest club is
                 "too old", "am i too old"),
          bias=1),
    entry("swim-breathing", (("swimming", "swim", "front crawl", "crawl", "lengths"),
                             ("breathe", "breathing", "technique", "learn", "goggles")),
          "Breathe out slowly under the water and turn your head to the side to breathe in as one "
          "arm comes over, rather than lifting your head forwards. Practise with a float and "
          "breathe every three strokes to start; goggles make all of it easier."),
    entry("pool-kit", (("swimming", "pool"), ("take", "bring", "first time", "kit", "locker",
                                              "goggles")),
          "Take goggles, a towel, a swimming costume (not shorts for most pools), a padlock for the "
          "locker and £1 coins or a card for it. Most pools want a shower before you get in, and "
          "many have a fast lane and a slow lane — start in the slow one.",
          # "take" is a bare key word, so "how long does it take to learn to swim" was read as a
          # packing list; learning to swim is the lessons entry's question
          avoid=("kid", "kids", "child", "children", "toddler", "baby", "babies", "newborn",
                 "infant", "month old", "months old",
                 "learn to swim", "learn swimming", "swimming lessons", "swim lessons",
                 "how long does it take", "cant swim", "can't swim", "cannot swim")),
    entry("sport-kit", (("kit", "kits", "equipment", "gear", "shin pads", "boots", "trainers"),
                        ("start", "starting", "beginner", "first time", "playing", "netball",
                         "football", "hockey", "cricket", "rugby", "badminton", "rounders",
                         "sport", "son", "daughter", "child", "kid", "kids", "boy", "girl")),
          "Start with very little: trainers or astro boots, shorts or leggings, a water bottle and, "
          "for football or hockey, shin pads. Clubs lend sticks, bats and bibs to beginners, so "
          "email and ask what they provide before you buy anything.",
          # a kit question used to get the joining reply again, because "start playing netball"
          # was in both keys
          # a kit list is for starting a sport; a line about buying one pair of boots is the
          # boots' own question, and "cheap astro boots for my daughter" was spending its turn on
          # shin pads and a water bottle
          avoid=("which boots", "what boots", "football boots", "studs", "studded", "moulded", "firm ground", "soft ground", "astro turf", "3g", "4g", "boot size", "what size", "break them in", "break in", "blister", "blisters", "too tight", "too small",
                 "astro boots", "turf boots", "boots for", "cheap boots", "boots cheap", "boots under", "new boots", "where to buy boots", "where can i get boots",
                 "smell", "smelly", "wash", "washing", "lost", "forgot", "leaving", "left"),
          bias=1),
    entry("protein-safety", (("protein", "high protein diet", "high protein"),
                             ("safe", "safety", "harmful", "dangerous", "bad for you", "too much",
                              "kidney", "kidneys", "bones", "heart", "side effects", "worry")),
          "For healthy kidneys, up to about two grams of protein a kilo a day is not a risk: no "
          "study has shown kidney damage in people with normal kidney function, and it does not "
          "harm your bones either. Extra protein beyond what your muscles use is simply burned, "
          "not stored as poison, and you do not need to force litres of water - drink to thirst. "
          "If you already have kidney disease, ask your doctor for a number before you raise it.",
          avoid=("baby", "babys", "toddler", "child", "children", "kid", "kids", "formula",
                 "breastfed", "breastfeeding", "pregnant",
                 "dog", "cat", "puppy", "kitten", "rabbit", "hamster", "horse")),
    # Children are a different number from adults, and a baby needs nothing added at all, so
    # this sits before the adult entries: "how much protein does my baby need" was getting the
    # angle-plan shopping list, which has nothing to do with protein.
    entry("protein-child", (("protein", "protein powder", "protein shake"),
                            ("baby", "babies", "toddler", "toddlers", "child", "children", "kid",
                             "kids", "weaning", "6 months old", "one year old", "school age")),
          "A child needs about a gram of protein for each kilo they weigh, so around 20g a day at "
          "20kg - two small portions of meat, fish, beans or eggs. Babies under one get all they "
          "need from breast milk or formula, and from six months you add iron-rich foods twice a "
          "day: mashed lentils, egg, chicken, yoghurt. Fussy patches are normal; ask your health "
          "visitor if the weight chart worries you.",
          # "how much protein does my baby need" also matches the newborn-shopping entry, which
          # names a baby, a cot and a need; the protein word is what makes this the answer.
          bias=2),
    entry("protein-shakes", (("protein", "whey", "protein powder", "protein shake",
                              "protein shakes"),
                             ("shake", "shakes", "powder", "whey", "worth it", "buy", "buying",
                              "necessary", "essential", "need it")),
          "Only if you struggle to hit the number with meals: a shake is convenient protein, not "
          "a shortcut, and food does the same job for less money. If you do buy one, a plain whey "
          "or a plant blend is fine - one scoop after training covers 20 to 25g - and the timing "
          "barely matters, because the total for the day is what builds muscle. Look for 20g or "
          "more of protein a scoop and ignore anything promising to burn fat.",
          avoid=("safe", "safety", "harmful", "dangerous", "kidney", "kidneys", "too much",
                 "for dogs", "dog", "cat", "puppy", "kitten", "allergic", "allergy", "sick",
                 "made me ill", "stomach", "nausea",
                 "baby", "babys", "toddler", "child", "children", "kid", "kids")),
    entry("warm-up-match", (("warm up", "warm-up"), ("before", "match", "game", "playing",
                                                     "football", "sport")),
          "Ten minutes is plenty: a jog to get warm, then leg swings, side-steps, lunges and a few "
          "short sprints, and finish with the ball or the equipment so the last thing you do looks "
          "like the game. Save the long stretches for afterwards.",
          bias=1),

    # --- sports people ask about that the table above does not cover ---
    entry("boxing-rounds", (("boxing", "boxer", "bout"),
                            ("rounds", "how many", "long", "rules", "score", "scoring", "win")),
          "A professional championship fight is twelve rounds of three minutes with a minute "
          "between, and most ordinary fights are four, six, eight or ten. Amateur bouts are "
          "usually three rounds of three. You win on points from the judges if it goes the "
          "distance, or by knockout, and a boxer who cannot continue loses.",
          # a beginner asking how to train is not asking about round length
          avoid=("train", "training", "exercise", "gym", "get fit", "lose weight", "start boxing",
                 "beginner", "how do i start", "class", "classes", "lesson", "lessons")),
    entry("american-football-rules", (("american football", "nfl", "super bowl"),
                                      ("work", "works", "rules", "score", "scoring", "down",
                                       "downs", "how does", "how do you play", "explain")),
          "The team with the ball gets four attempts to move ten yards, and if they make it they "
          "get four more; that is the whole rhythm of the game. A touchdown is six points, the "
          "extra kick one more, a field goal three. If the four attempts run out, the other team "
          "takes over from where the ball is."),
    # The scoring alone, asked by name: "how many points is a field goal" names no team and no
    # league, so the card above never matched it.
    entry("american-football-scoring", (("field goal", "field goals", "touchdown", "touchdowns",
                                        "extra point", "two point conversion", "safety"),
                                       ("how many", "many", "points", "point", "score",
                                        "scoring", "worth", "what", "is")),
          "A touchdown is six points, the extra point kick after it is one more, a field goal is "
          "three, and a safety - tackled behind your own goal line - is two. That is the whole "
          "scoring system in American football."),

    entry("tour-de-france", (("tour de france", "cycling race", "yellow jersey", "grand tour"),
                             ("work", "works", "win", "wins", "winner", "stages", "explain",
                              "how", "what", "mean", "means")),
          "It is about three weeks and 21 stages, and the winner is whoever finishes with the "
          "lowest total time — not the most stage wins. The yellow jersey goes to the overall "
          "leader each day, green is the points competition for sprinters, and the polka dot is "
          "for the best climber. Most of the overall lead is built in the mountain stages and the "
          "two time trials."),
    entry("which-team-to-support", (("who should", "who to support", "which team", "which club",
                                     "which side", "football team", "pick a team", "pick a club",
                                     "support a club", "support a team", "what team"),
                                    ("team", "football", "premier league", "rugby", "cricket",
                                     "sport", "league", "support")),
          "Pick the team someone you already watch with supports, or the one nearest to where you "
          "live — going to games matters more than the badge. Watch a few matches first and let it "
          "happen; supporting a team is mostly habit plus the people you watch it with. Nobody "
          "will test you on the history, whatever the internet says.",
          # "which team won last night" is a result, not a question about who to follow.
          avoid=("won", "win", "wins", "score", "result", "table", "top of", "players", "best",
                 "points", "how many", "what is", "cup", "final", "better", "stronger", "versus",
                 "vs", "beat", "bet", "watch"),
          guard=_not_the_coach_of_a_team),

    # --- getting fit, on your own -------------------------------------------
    entry("gym-first-session", (("gym", "weight room", "weights", "free weights"),
                                ("first", "first time", "start", "starting", "beginner",
                                 "never", "joined", "what should i do", "what do i do",
                                 "how do i start", "do first",
                                 # how the same question is asked with no "first" in it
                                 "what should i try", "what do i try", "what to do",
                                 "know what to do", "no idea", "dont know", "don't know",
                                 "where do i start", "where to start", "how do i use",
                                 "use the machines", "machines", "induction",
                                 "what should i be doing", "tips", "advice")),
          _the_gym_induction,
          # a gym membership question is a different answer and it has one
          avoid=("cancel", "cancelling", "cancel my", "membership", "contract", "refund",
                 "quit", "leaving", "close my",
                 # someone who already started and is sore is not asking for a first session
                 "sore", "soreness", "aching", "ache", "push through", "been going",
                 "started at the gym", "started going"),
          # "i joined a gym last week" is news, not a question: it gets the ordinary
          # acknowledgement, and the person can ask what to do next turn
          ask=("what", "how", "should", "when", "first", "start", "do i", "tips", "advice")),

    # "how do i choose a gym", "which gym should i join" and "is it worth joining a gym" were a
    # shrug or the first-session answer: the gym rows knew what to do inside one and nothing about
    # picking it. Choosing is a short list of things to look at, and the contract is the part
    # people get caught by.
    entry("choosing-a-gym", (("gym", "leisure centre", "health club", "swimming pool"),
                             ("choose", "choosing", "pick", "picking", "which gym", "best gym",
                              "good gym", "worth joining", "compare", "look for", "near me",
                              "cheap", "cheapest", "price", "prices", "join", "joining")),
          "Go at the time you would actually go, on a weekday evening if that is when you are free: "
          "a gym that is full at six is the one you stop using. Then check three things - the "
          "distance from home or work, because anything past fifteen minutes gets skipped, whether "
          "the classes you want are included in the price or cost extra, and the notice period on "
          "the contract, which is often a month and sometimes three. Ask for a day pass or a week "
          "trial before you sign, look at the changing rooms as well as the equipment, and work out "
          "the price per visit rather than per month: 40 a month is cheap at three visits a week "
          "and dear at one. The cheapest gym is the one you actually use.",
          # a first session, a cancellation, a warm-up and a sore day all have their own answers
          avoid=("cancel", "cancelling", "refund", "quit", "leaving", "close my", "sore",
                 "first time", "first day", "beginner", "warm up", "what should i do",
                 "how do i start", "induction", "key fob"),
          ask=("choose", "choosing", "pick", "picking", "which", "best", "worth", "compare",
               "look for", "near me", "cheap", "price", "cost", "join", "how"),
          # "which gym should i join" carries "join", which the first-session row keys, so this
          # row has to outrank it when the line is a choice rather than a first visit
          bias=1),

    # "how do i build up my strength after illness" was a shrug, and the getting-back-into-
    # exercise row keys "back into" and "after being ill" and not the strength the person asks
    # about. Muscle comes back slower than the walk does, so it has its own row.
    entry("strength-after-illness", (("strength", "strong again", "muscle", "muscles", "energy",
                                      "weak", "weakness", "fitness", "stamina", "weight"),
                                     ("after illness", "after being ill", "after surgery",
                                      "after a operation", "after an operation", "after covid",
                                      "after chemo", "after hospital", "been ill", "was ill",
                                      "build up", "build back", "get back", "back to normal",
                                      "rebuild", "regain", "lost",
                                      # "after a long illness", "since my operation" and "after
                                      # being in hospital" are the same question in other words
                                      "illness", "ill", "surgery", "operation", "chemo",
                                      "hospital", "bed", "virus", "covid", "infection")),
          "Start with two short sessions a week and leave a day between them: a chair stand or a "
          "slow sit-to-stand for the legs, a wall press or a light band row for the upper body, "
          "eight to ten slow reps each, stopping while you still have three or four left in you. "
          "Add a little - one rep or one tin of beans - only when the last session left you tired "
          "but not wrecked. Muscle comes back at roughly half the speed of the walking, so expect "
          "weeks rather than days, and put protein in every meal: a palm-sized piece of meat, "
          "fish, eggs, beans or yoghurt, three times a day. If you were in hospital, in bed for "
          "more than a few days, or had heart, lung or kidney trouble, ask your GP or the "
          "physiotherapist who saw you before you start, and stop and get advice for chest pain, "
          "breathlessness at rest, or a swollen painful calf.",
          # this is not a session plan, a warm-up or a training programme for a race
          avoid=("warm up", "programme", "program", "plan for", "marathon", "half marathon", "5k",
                 "10k", "bulk", "bulking", "cutting", "bodybuilder", "personal best", "gym",
                 "first time", "beginner", "protein powder", "creatine", "how much weight"),
          ask=("how", "what", "should", "when", "build", "get back", "start", "help", "tips")),

    entry("gym-warm-up", (("warm up", "warmup", "warm-up"),
                          ("long", "how long", "gym", "weights", "run", "running", "exercise",
                           "before", "should i")),
          "Five to ten minutes: two or three minutes on the bike, rower or cross-trainer until you "
          "are warm, then a couple of light sets of whatever you are about to do - the same "
          "movement at half the weight, for 10 reps. That is a warm-up; the long stretches are for "
          "afterwards, when the muscles are warm.",
          # a warm-up before a match is a different answer, and that entry gives it; a house
          # that is warming up is not a session at all
          avoid=("match", "game", "playing", "football", "rugby", "netball", "hockey", "sport")
          + A_HOUSE_WARMING_UP),

    # The order of a session needs both halves in the line. With "cardio" alone in the key this
    # row answered "should i do cardio in the morning or at night", "should i do hiit or steady
    # cardio" and "which is better rowing or running" with the order to do them in, and none of
    # the three names any weights: the lifting half is demanded as `ask`, so a line that names
    # only one side goes to its own answer.
    entry("cardio-or-weights-first", (("cardio", "run", "running", "bike", "rowing"),
                                      ("first", "before", "after", "order", "should i do",
                                       "which", "same session", "same day", "lift weights",
                                       "weights first", "cardio or weights",
                                       "weights or cardio")),
          "Do the one that is the point of the session first, because the second one gets the "
          "tired version of you: if you are there to get stronger, lift first and finish with ten "
          "minutes of cardio; if you are training for a run or a ride, do that first. Ten easy "
          "minutes on the bike before you lift is a warm-up, not cardio. The best order is the one "
          "you will keep doing twice a week.",
          # The ask is the order itself, not the second half: "should i do cardio first" is the
          # order of a session and no other row owns it, while "should i do hiit or steady
          # cardio" and "which is better rowing or running" name two things to choose between
          # and no order words, so they leave this row to the two-sided rows.
          ask=("weights", "weight training", "lifting", "lift", "strength", "resistance",
               "circuits", "first", "before", "after", "order", "same session", "same day"),
          # both halves are named, so this beats the one-sided rows that fit the same words
          bias=1,
          # a rest day is the rest-days question, whichever exercise is named on it
          # ("should i do cardio on rest days" took the order-of-a-session answer)
          # "before" is how the order is asked, and it is also how the food, the stretch and the
          # warm-up are asked: "cardio before breakfast" was answered with the order of a session.
          avoid=("run out of", "ran out of", "running out of", "runs out",
                 "money", "payday", "pay day", "paid", "wage", "wages", "salary", "rent",
                 "bill", "bills", "cash", "pounds",
                 "rest day", "rest days", "day off", "days off", "recovery day", "recovery days",
                 "breakfast", "fasted", "fasting", "eat", "eats", "eating", "ate", "food",
                 "foods", "meal", "meals", "fuel", "carbs", "carb", "protein", "pre workout",
                 "pre-workout", "stretch", "stretches", "stretching", "warm up", "warmup",
                 "warm-up", "cool down", "cooldown", "water", "hydrate", "hydration",
                 # a body that already hurts is a question about the hurt body: "my back hurts
                 # after running" and "my back is sore after running" were answered with the
                 # order to do two halves of a session in
                 "hurt", "hurts", "hurting", "pain", "painful", "ache", "aches", "aching",
                 "sore", "soreness", "stiff", "twinge", "sciatica")),
    # Only the frequency words are in the key on purpose. "is it ok to run with a cold", "is it
    # safe to run at night" and "is it ok to run with my dog" are questions about being ill, about
    # the dark and about the dog: an "ok" in the key answered all three with a training plan.

    entry("run-every-day", (("run", "running", "jog", "jogging"),
                            ("every day", "everyday", "daily", "every single day")),
          "You can run every day eventually, but for the first couple of months three or four runs "
          "a week is the better deal - the legs get stronger on the days off, and running every day "
          "from nothing is how shins start hurting. Keep most runs easy enough to hold a "
          "conversation in; a hard run every day is the other common mistake. Add one run a week "
          "rather than one every day.",
          # being ill while running is a question this entry cannot answer, and "can i run every
          # day with a cold" is asked that way round often enough to say so; the dog, the knee
          # that hurts and "is it bad for your knees" are the same shape
          avoid=("marathon", "race", "parkrun", "how far", "distance",
                 "cold", "flu", "fever", "hangover", "ill", "sick", "cough",
                 "injury", "injured", "dog", "dogs", "knee", "knees", "hurt", "hurts",
                 "pain", "hurting",
                 # a school run is a car journey with children in it and an errand run is the
                 # shops: "i do the school run every day and work is tight" was answered with
                 # this plan because "run" and "every day" are both in the key
                 "school run", "school runs", "nursery run", "errand run", "errand runs",
                 "supermarket run", "shop run")),

    entry("eat-before-run", (("eat", "eating", "food", "breakfast", "snack"),
                             ("before a run", "before i run", "before running", "before the gym",
                              "before i go", "before exercise", "before a workout", "running",
                              "workout", "gym",
                              # The same question about a match: "playing five a side sunday,
                              # first time in years, what should i eat before" was answered
                              # with a list of twenty-minute dinners, because the row named
                              # only the run and the gym and "eat before" was the cook menu's.
                              "before a match", "before the match", "before a game",
                              "before the game", "before playing", "before i play",
                              "before i train", "before training", "before sport",
                              "before five a side", "five a side", "football", "rugby",
                              "netball", "hockey", "cricket", "a match", "the match")),
          "Something small and mostly carbohydrate, an hour or two before: a banana, a round of "
          "toast, a small bowl of porridge. Leave longer after a big meal - three hours - or you "
          "will feel it. For a short easy run first thing, plenty of people go out with nothing but "
          "water and are fine. The one rule is nothing new on the day of a race: try it in training "
          "first.",
          # "what should i eat after a run" was answered with the before-run advice, which is the
          # wrong half of the question: nutrition.py answers the after.
          avoid=("after a run", "after the run", "after running", "after the gym", "afterwards",
                 "recover", "recovery", "after a workout", "after exercise", "post workout",
                 "post-workout", "after my run", "after i run"),
          # "what should i eat before a workout" was answered with a training plan, because the
          # plan row also matches the bare word workout and won the tie: a line that says eat is
          # asking about food, and this row has the eat word in its key.
          bias=1),
    # The rules question a new fan asks, and the answer is the format: points versus knockout.
    entry("league-and-cup",
          (("league", "cup", "the cup", "premier league", "champions league", "fa cup",
            "knockout", "table"),
           ("difference", "what", "why", "how does", "explain", "both", "same", "cup and league",
            "works", "between")),
          _league_and_cup,
          # Two competitions of the same kind are a different question: the fa cup against the
          # league cup is two knockouts, and the premier league against the champions league is
          # two tables within a continent, so this answer would be confidently about neither.
          avoid=("my team", "we lost", "we won", "score", "kick off", "kick-off", "ticket",
                 "who won", "result",
                 # A table is a list in a league and a piece of furniture in a restaurant, so
                 # "whats the notice for cancelling a restaurant table" was told how a season is
                 # decided. The booking words are the whole of the other sense: the row stands
                 # down on them and the booking card answers.
                 "restaurant", "restaurant table", "booking", "book", "booked", "reservation",
                 "reservations", "cancel", "cancelling", "cancellation", "notice", "dinner",
                 "lunch", "dining", "table for", "pub")),
    # --- the body that hurts when you use it -------------------------------
    # Pain that comes on with load is not the stairs question and not the noisy-knee answer:
    # it is a muscle-and-mileage job, and a knee that gives way is neither.

    entry("knee-gives-way", (("knee", "knees", "kneecap"),
                             ("gave way", "gives way", "gave out", "gives out", "buckled",
                              "buckles", "collapsed", "collapses", "unstable", "wobbles",
                              "not stable", "keeps giving")),
          "A knee that gives way is one to get looked at rather than train through: it usually "
          "means a ligament is not holding, or the kneecap is slipping, and a physio can work out "
          "which in one visit. Skip pivoting sports and uneven ground until then, and keep the "
          "muscles awake with sit-to-stands and step-ups. Ring your GP or a physio this week.",
          # a knee that buckles ties with the legs-like-jelly row, which also keys "knee" and
          # "giving way" and carries a bias - and a named joint that gives way is the joint's
          # question, not the legs-feel-weak one
          bias=2),
    entry("exercise-when-ill", (("gym", "run", "running", "jog", "exercise", "exercising",
                                 "workout", "work out", "working out", "training", "train",
                                 "football", "swim", "swimming", "cycle", "cycling", "lift",
                                 "lifting", "weights",
                                 # "can i still ..." is the same question as "can i ...", and
                                 # it is how people ask it when they already have the cold
                                 "still run", "still train", "still go", "still play",
                                 "still swim", "still cycle"),
                                ("cold", "colds", "ill", "illness", "sick", "flu", "chest",
                                 "cough", "sore throat", "temperature", "fever", "virus", "bug",
                                 "tonsils")),
          "Use the neck rule: a runny nose, sneezing or a mild sore throat above the neck is fine "
          "for easy exercise; a chesty cough, fever, aching or a stomach bug below it means rest "
          "until you are properly over it. Come back at half your usual effort for the first "
          "session, and do not count a hard session as something that clears it.",
          # "how do i get rid of a cold fast" is the remedy question, and a chest pain is urgent.
          # Cold hands or cold feet after a session are a circulation question, not this rule.
          avoid=("get rid", "remedy", "cure", "fast", "quickly", "best", "what helps", "chest pain",
                 "cant breathe", "can't breathe", "baby", "babies", "child", "children",
                 "kid", "kids",
                 # cold hands or cold feet after a session are a circulation question, not this rule
                 "hands", "hand", "fingers", "feet", "foot", "toes", "toe"),
          # A person who is ill and training is asking whether to train, and the plan is the
          # wrong answer: "i am training for a half marathon and i have a cold, should i still
          # run" got twelve to sixteen weeks. The cold word is in this row's own key, so the
          # bias only decides the tie against the plan.
          bias=3),

    # The starter kit answer is right about shin pads and wrong about the boots: astro boots on
    # grass give no grip, and the surface is what decides the boot. The reply is a callable
    # because a line about size or a stiff new pair wants the fit first and the surface second.
    # "can i run in the cold" asks about the weather, not about exercising while ill: only the
    # going-outside words are in the key, and the illness lines are guarded off. Cycling says it
    # the same way - "is cycling in the cold bad for you" was told the laundry temperature - so
    # the bike words sit beside the run ones and the card is worded for both.
    entry("run-in-the-cold", (("cold", "freezing", "winter", "frost", "minus", "icy"),
                              # an activity is what a running-in-the-cold line has to have. The
                              # bare place word "outside" was in this half, so "is it cold outside"
                              # - a person asking what the sky is doing - was told that cold air
                              # does not damage healthy lungs. "outside" on its own says where the
                              # person is, not what they are doing there, so it went; the lines
                              # that do have an activity in them ("can i run outside when its
                              # freezing", "is cycling in the cold bad for you") still reach it.
                              ("run", "running", "jog", "jogging", "cycle", "cycling", "bike",
                               "bicycle", "ride", "riding", "exercise", "exercising")),
          "Cold air does not damage healthy lungs: it is dry and it warms on the way in, so a run "
          "or a ride in the cold is fine. Start slower for the first ten minutes, cover your "
          "hands and ears, and wear a layer you can tie round your waist. If you have asthma, "
          "take your inhaler before you go out and warm up indoors first, and use a buff over "
          "your mouth on very cold days.",
          # a cold someone already has is the neck-rule answer, and a chest that hurts on a cold
          # run is not a weather question
          # a "what should i wear" line is the clothes note's question, not the lungs'
          avoid=("wear", "wearing", "what to wear", "kit", "clothes", "outfit",
                 "a cold", "my cold", "with a cold", "have a cold", "run down",
                 "get a cold", "catch a cold", "cold sore",
                 "chest", "chest pain", "chest hurts", "cant breathe", "can't breathe",
                 "asthma attack",
                 "cough", "coughing", "chesty", "sore throat", "fever", "ill", "sick",
                 # cold hands or feet on a ride are the circulation question, not the weather
                 "hands", "hand", "fingers", "feet", "foot", "toes", "toe",
                 # "running" is not always a person: a pump, a filter and an engine all run in
                 # the cold, and "should i keep the pond pump running in winter" was this card
                 "pump", "pumps", "filter", "filters", "engine", "engines", "motor",
                 "generator", "machine", "air con", "aircon", "car", "cars", "van")
                 # the rest of the weather asks ("is it warm enough to go out", "what is the
                 # weather doing") are the live information note's, not a note on lungs
                 + A_WEATHER_ASK,
          # the neck rule reads "cold run" too: the weather is the narrower ask
          bias=1),

    # "is it ok to run in the rain", "can i run in the rain" and "should i run in bad weather"
    # were a search hedge, a phone's waterproof rating and the period-pain card on main
    # 4ed19296: the cold-run row above keys the weather but not the water.
    # A treadmill is the one running question with no weather in it, and "is it bad to run on a
    # treadmill" was a shrug: nothing keyed the machine.
    entry("treadmill-run",
          (("treadmill", "treadmills", "running machine", "run indoors", "running indoors"),
           ("bad", "worse", "ok", "okay", "good", "healthy", "outside", "vs", "versus",
            "better", "knees", "harder", "easier", "instead of", "worth it", "safe")),
          "A treadmill is not bad for you: the deck gives a little more than pavement does, and "
          "the machine keeps the pace honest. It is a touch easier than running outside because "
          "there is no wind or camber, so set the incline to 1% to make it match the road, and "
          "run tall rather than holding the handles. The one habit to avoid is the same flat "
          "stride every time - put a hill or a faster minute in most sessions.",
          # buying, fixing or the noise a machine makes are other questions
          avoid=("buy", "buying", "bought", "price", "prices", "cost", "cheapest", "which one",
                 "second hand", "second-hand", "fix", "repair", "broken", "motor", "belt",
                 "squeak", "squeaking", "noise", "noisy", "lubricant"),
          bias=1),
    # The cold has a note and the heat did not: "is it too hot to run" was a shrug, and it is the
    # commonest weather question of a summer week. The numbers are the point of it.
    entry("run-in-the-heat", (("hot", "heat", "heatwave", "warm", "boiling", "scorching",
                               "humid", "muggy", "sun", "sunny", "degrees", "30c", "25c"),
                              ("run", "running", "jog", "jogging", "cycle", "cycling", "ride",
                               "walk", "exercise", "exercising", "football", "tennis",
                               # A phrase in both groups makes the pair do nothing: "hot" is in
                               # the first group, so "too hot" here satisfied both and any line
                               # with "too hot" in it - "that chilli was too hot what do i do" -
                               # got the running numbers. The second group is the doing.
                               "safe")),
          "Above about 25C, slow down rather than stop: expect 20 to 30 seconds a kilometre "
          "slower for every 5C over 15C, and let the pace go. Run early or late, drink to thirst "
          "before and after, take walk breaks, and wear light, loose clothes. Stop and get into "
          "shade if you go dizzy, get a headache, feel sick or stop sweating. The first hot week "
          "is the worst one, and the body adapts in about ten days.",
          avoid=("baby", "babies", "pram", "buggy", "dog", "dogs", "car", "cars", "van",
                 "house", "flat", "bedroom", "room", "sleep", "sleeping", "radiator",
                 "heating", "boiler", "sunburn", "sun cream", "sunscreen", "spf", "uv",
                 "weather", "forecast", "washing", "laundry",
                 # an oven asked "how hot" is a dial and not the weather: "how hot should my oven
                 # be" was told how much to slow down at 25C. A cooking appliance word stands the
                 # heat-and-exercise row down, and the oven row has the dial answer.
                 "oven", "ovens", "fan oven", "cooker", "hob", "grill", "bake", "baking",
                 "roast", "roasting", "gas mark", "air fryer", "barbecue", "bbq", "kiln",
                 # a fever, a hot flush and a hot water bottle are not the weather
                 "fever", "temperature of", "hot flush", "flushes", "menopause", "period",
                 "hot water bottle"),
          bias=1),
    entry("run-in-the-rain", (("run", "running", "jog", "jogging", "cycle", "cycling",
                               "walk", "walking", "train", "training"),
                              ("rain", "raining", "rains", "wet", "drizzle", "drizzling",
                               "downpour", "showers", "shower", "bad weather", "weather",
                               "stormy", "storm", "thunder", "lightning", "miserable")),
          "Yes, and it is usually fine: you get wet either way once you are out, and the rain "
          "cools you rather than hurting you. Wear a thin breathable jacket or a cap with a brim "
          "so the rain stays out of your eyes, something bright or reflective because drivers "
          "see less in the wet, and trainers with grip - wet leaves and painted lines are slick. "
          "Rub a little vaseline where your clothes rub, because wet skin chafes. The one thing "
          "to stop for is thunder and lightning: head indoors and wait it out. Stuff newspaper "
          "in the shoes afterwards and dry them away from a radiator so they keep their shape.",
          # a phone that survives a splash, and a forecast, are answers about the phone and the
          # weather rather than about running in it
          avoid=("phone", "iphone", "waterproof", "leak", "leaking", "roof", "gutter",
                 "washing", "laundry", "dry the washing", "put the washing out",
                 "umbrella", "coat", "bbq", "barbecue", "picnic", "wedding", "drive",
                 "drive in", "forecast", "will it rain", "is it going to rain",
                 # "running in the rain is horrible" is a complaint, not a yes-or-no
                 "horrible", "awful", "hate", "dread", "cant stand", "can't stand",
                 # "should i run in the rain with a cold" is the neck rule's question: the
                 # weather is not what decides that one
                 "cold", "flu", "ill", "illness", "sick", "cough", "coughing", "chesty",
                 "fever", "sore throat", "virus", "bug", "chest infection")),

    # Exercising on a period is a question people ask the day of, and on main 4ed19296 the
    # answer was "a pharmacist or your GP can answer that today" - a referral where the person
    # wanted the ordinary answer. The pain and bleeding questions keep their own cards.
    entry("exercise-on-period", (("exercise", "exercising", "gym", "run", "running", "jog",
                                  "swim", "swimming", "workout", "work out", "working out",
                                  "train", "training", "lift", "lifting", "weights", "cycle",
                                  "cycling", "yoga", "pilates", "netball", "football", "hockey",
                                  "still go", "still run", "still train", "rest", "skip",
                                  "keep going", "stretch", "dance", "class", "spin"),
                                 ("period", "periods", "on my period", "time of the month",
                                  "menstrual", "monthlies", "day one", "day 1",
                                  # "first day" on its own is any first day: "what should i do
                                  # at the gym on my first day" is the gym's first session, and
                                  # it was told the period was fine. The period's own first day
                                  # is named with the period.
                                  "first day of my period", "first day of the period",
                                  "first day of it", "first day on my period")),
          "Yes - easy to moderate exercise is fine on your period, and it usually helps: moving "
          "lifts the endorphins and blood flow that take the edge off cramps. Go by how you feel "
          "rather than by the calendar: a walk, a swim or an easy run is fine on a heavy day, and "
          "if day one is rough keep it short and gentle and pick it up later in the week. "
          "Ibuprofen about half an hour before helps if cramps are the problem. For swimming, use "
          "whatever you already use - a tampon or a cup - and change it straight after.",
          # pain or bleeding that stops your day is its own card with its own advice, and a
          # missed or late period is a different question again
          avoid=("pain", "painful", "painkillers", "heavy", "heavier", "flooding", "bleeding",
                 "bleed", "missed", "late", "stopped", "irregular", "pregnant", "pregnancy",
                 "test", "contraception", "pill", "implant", "coil", "menopause",
                 "why", "what causes", "normal", "should my period",
                 # "working out on my period is horrible" is a complaint, and the sympathy
                 # first is the better first move: the answer below is for the ask.
                 "horrible", "awful", "hate", "dread", "cant stand", "can't stand"),
          bias=1),
    entry("tennis-serve", (("serve", "serving", "toss", "second serve"),
                           ("tennis", "improve", "better", "practise", "practice", "consistent",
                            "power", "fix", "long", "net", "fault", "faults", "double fault",
                            "inconsistent", "inconsistency", "keeps", "goes long",
                            # "how do i fix my double fault" names no tennis at all
                            "double", "faults")),
          "Two things fix most serves: a toss you can repeat and meeting the ball out in front. "
          "Practise 50 tosses without hitting, catching at the same spot each time, then serve at "
          "half speed from the service line and only move back when 8 of 10 land in. Toss first, "
          "power later - the pace comes from the leg bend and the shoulder turn, not from swinging "
          "harder.",
          # a different racket sport, or a dinner, is not this serve
          avoid=("volleyball", "badminton", "squash", "table tennis", "tennis elbow",
                 "dinner", "food", "guests", "wine", "coffee", "drinks", "pint",
                 "dns", "wifi", "fault with", "my fault", "at fault")),
    entry("football-boots", (("boot", "boots", "football boots", "studs", "studded", "moulded",
                              "cleats", "astro boots", "astro turf", "turf boots", "firm ground",
                              "soft ground", "sg boots", "fg boots", "predators"),
                             # "my boots have moulded studs" names the studs twice over and no
                             # surface, so the stud words count on this side too: the mould row
                             # for clothes used to take it, and dropping that left a shrug
                             ("grass", "astro", "astroturf", "3g", "4g", "turf", "indoor",
                              # the phrase only: bare "moulded" here is a loose form of the
                              # "mould" in "how do i get rid of mould", which made that line
                              # reach boots on both halves of the key
                              "moulded studs", "studded studs",
                              "futsal", "sports hall", "muddy", "wet", "surface", "which",
                              "what", "son", "daughter", "child", "kid", "need", "get", "wear",
                              "buy", "size", "first pair", "shin pads", "break in",
                              "breaking in", "break them in", "blister", "blisters", "too tight",
                              # a pair is bought before it is played in: "cheap football boots"
                              # and "where can i get football boots for a kid" are this row's
                              # question, and the price words were only in the calendar row's
                              # key, which answered them with the January sales on coats
                              "cheap", "cheaper", "cheapest", "afford", "budget", "price",
                              "prices", "cost", "spend", "sale", "second hand", "secondhand",
                              "where", "shop", "shops", "store", "online", "order", "pair",
                              "pairs", "years old", "year old", "age", "foot", "feet",
                              # a calendar question about boots is about boots, not about the
                              # winter coat's January sales
                              "when", "what month", "which month", "best time", "time to buy")),
          _football_boots,
          guard=_not_a_study_line,
          # no ask gate: the avoid list keeps the lookalikes out, and the lane's own test builds
          # a line from the id words ("boot grass"), which has no question in it to gate on
          # a walking boot, a wellington and the boot of a car are other questions, and so is the
          # boot bag that gets left on the bus
          avoid=("hiking", "walking", "walk", "wellies", "wellington", "welly", "snow boots",
                 # a ski boot has buckles and a piste, not studs: "what ski boots should i buy"
                 # was told which studs to buy for grass
                 "ski", "skis", "skiing", "ski boots", "ski boot", "snowboard", "snowboarding",
                 "piste", "slope", "slopes", "mountain", "chalet", "apres", "apres ski",
                 # a boot for the cold is a boot for the street, and "what boots are good for
                 # winter" reached the studs because a bare "what" was enough key
                 "winter", "winter boots", "snow", "ice", "icy", "grit", "slush", "frost",
                 "riding boots", "horse", "car boot", "boot sale", "boots the chemist", "job",
                 # the boot a smell is in is the car's or the hall's, not a pair of studs: "the
                 # smell in the boot of my car" was the surface card on main
                 "boot of my car", "boot of the car", "boot of a car", "boot of our car",
                 "in the boot", "the boot of", "boot space",
                 "jobs", "work boots", "steel toe", "dr martens", "timberland", "ankle boot",
                 "boot cut", "bootcut",
                 # a mark on a boot is a cleaning job, and the rows for leather, suede and fabric
                 # give it: "how do i get a stain out of my boots" was told which studs to buy
                 "stain", "stains", "stained", "mark", "marks", "scuff", "scuffs", "smell",
                 "smells", "smelly", "wax", "polish", "dubbin", "waterproof", "clean",
                 "cleaning", "washing", "wash",
                 # "moulded" is a loose form of "mould", so without these a line about the mould
                 # on a ceiling reached the boot that has moulded studs. The guard has to be the
                 # room and damp words rather than "mould" itself, because "mold" is a loose form
                 # of "moulded" too and stood the boot down on its own lines
                 # the room words matter as much as the damp ones: "what should i do about mould
                 # in my bedroom" said nothing about a ceiling and still reached the boot
                 "ceiling", "ceilings", "wall", "walls", "wallpaper", "bathroom", "shower",
                 "damp", "damp patch", "condensation", "mildew", "black mould", "black mold",
                 "spore", "spores", "grout", "sealant", "bedroom", "bedrooms", "room", "rooms",
                 "window", "windows", "sill", "corner", "corners", "kitchen", "floor", "floors",
                 "flat", "house", "curtain", "curtains", "cupboard", "wardrobe", "tile", "tiles",
                 "skirting", "loft", "attic", "airing cupboard", "windowsill",
                 # the mould people actually ask about at home is on food, and it said nothing
                 # about a room: "what can i do with mouldy bread" was told which studs to buy
                 # for wet grass. Food is not a pair of boots, whatever the word mould does.
                 "bread", "loaf", "loaves", "toast", "sandwich", "cake", "cheese", "jam",
                 "yoghurt", "yogurt", "fruit", "vegetable", "vegetables", "food", "foods",
                 "leftovers", "leftover", "eat", "eating", "ate", "edible", "safe to eat",
                 "throw away", "throw it away", "bin it", "loaf of", "slice of")),


    # --- habits people ask for help with -----------------------------------
    # "is it ok to swim in the sea" was the phone's waterproof rating on main 4ed19296, because
    # the bare "it" in that key read a swim as a device. The rating card now wants a device or a
    # rating in the line, and the open-water question gets its own answer here.
    entry("swim-in-the-sea", (("swim", "swimming", "swimmer", "paddle", "paddling", "dip",
                               "wild swim", "bathe"),
                              ("sea", "beach", "lido", "lake", "river", "reservoir", "cove",
                               "open water", "outdoors", "outside", "tarn", "loch")),
          "Yes, with a few things done right. Pick a lifeguarded beach and swim between the flags, "
          "go with someone rather than alone, and check the tide and the wind before you get in. "
          "The cold is the real danger at a British beach: it takes your breath away in the first "
          "few seconds, so walk in, let yourself gasp, and only then swim - and get out well before "
          "you start shivering. If a current pulls you sideways, do not fight it: swim parallel to "
          "the beach until you are out of it, then come in. No alcohol before you go in, and a "
          "wetsuit or a tow float on a cold day.",
          # a pool question is not open water, and a swimming lesson or a stroke question has its
          # own card
          avoid=("pool", "chlorine", "learn to swim", "lessons", "front crawl", "breaststroke",
                 "stroke", "goggles", "after eating", "cramp", "ear", "earache", "shoulder",
                 "how long", "how far", "calories", "burn"),
          bias=1),

    entry("swim-after-eating",
          (("swimming", "swim", "pool", "sea", "bathe", "lido"),
           # "how long" alone was a key here, so "how long should i swim for" and "how long till
           # i can swim a length" - duration questions - were answered with the cramp rule. The
           # wait is what this entry is about, so the phrases carry it now.
           ("after eating", "after a meal", "after lunch", "after dinner", "wait", "waiting",
            "how long after", "how long before", "how long do i have to wait",
            "how long should i wait", "how long till i can swim after",
            "before swimming", "cramp", "cramps", "straight after")),
          "There is no need to wait a full hour: the old cramp rule comes from one small study and "
          "the evidence does not back it up. Go in when you feel comfortable, which for most people "
          "is half an hour after a big meal and straight away after a snack - just keep off alcohol "
          "before you get in, because that one really does matter.",
          avoid=("cook", "recipe", "meal plan", "kids", "children", "toddler", "baby", "dog")),

    # "how do i get better at football" is a practice question, so it is about the two touches that
    # lift a park player, not about the rules or the sessions
    entry("football-improve",
          (("football", "soccer", "five-a-side", "five a side"),
           ("better", "improve", "improvement", "practise", "practice", "training", "train",
            "coach", "skill", "skills", "touch", "passing", "drills")),
          "The two things that lift a park player fastest are a first touch that keeps the ball "
          "close and being able to pass with both feet: twenty minutes of wall passes a few times "
          "a week does both. Then add scanning - a look over your shoulder before the ball arrives "
          "- so you know your next pass before it reaches you.",
          # the rules, the length of a match and joining a team are their own answers
          avoid=("offside", "how long", "minutes", "rules", "positions", "join", "club",
                 "television", "tv", "world cup", "who won", "score", "watch", "injury", "injured",
                 "knee", "ankle", "hamstring")),
    # Striking the ball is the one football skill people ask for by name, and it had no card:
    # "how do i kick a football", "how do i kick a ball" and "how do i shoot in football" were
    # all the honest shrug, beside a working answer for getting better at football in general.
    entry("kick-a-football",
          (("kick", "kicks", "kicking", "kick it", "strike", "striking", "shoot", "shooting",
            "curl", "curled", "chip", "volley"),
           ("football", "soccer", "ball", "goal", "goals", "laces", "harder", "further",
            "properly", "power", "spin", "top corner", "free kick", "penalty", "corner",
            "long ball", "cross", "shot", "shots")),
          "Strike it with the laces, not the toe: plant the standing foot beside the ball with "
          "the knee over it, keep the ankle locked and swing through the middle of the ball, "
          "then follow through where you want it to go. For a pass, use the inside of the foot "
          "with the ankle at a right angle - the toe is what makes it balloon.",
          ask=("how", "what", "where", "should", "any"),
          # a habit, a kick-off and a rule question are not the skill
          avoid=("habit", "kick off", "kick-off", "kickoff", "kickboxing", "kicked out",
                 "rules", "offside", "how long", "who won", "watch", "tickets",
                 "rugby", "basketball", "american football", "gaelic", "penalty shootout"),
          bias=1),

    # Angling is the one sport with a licence, and the questions are nearly always the paperwork:
    # a rod licence for freshwater, and a separate ticket for the water itself. "do i need a
    # licence to fish" was getting the baked-fish method, because "fish" is a staple in cooking.
    entry("fishing-licence",
          (("fish", "fishing", "angling", "angler", "coarse fishing", "fly fishing", "carp",
            "trout", "rod", "pike", "tench", "bream", "magot", "maggots"),
           ("licence", "license", "licencing", "licensing", "permit", "day ticket", "ticket",
            "legal", "illegal", "allowed", "need", "need one", "do i need", "rule", "rules",
            # bare "season" was the wrong word for this key: it is the stem of "seasoning" as
            # well, and "what seasoning for fish" was answered with a rod licence. A season is
            # only angling's when it is named as one - the close season, the fishing season - so
            # what the key holds is the phrases, in the shapes people ask them.
            "close season", "closed season", "fishing season", "what is the close season",
            "when is the close season", "what is the fishing season", "when is the fishing season",
            "season starts", "season opens", "open season",
            "when can i", "get started", "start",
            "get into", "getting into", "beginner", "beginners", "equipment", "kit",
            "where do i", "what do i need", "can i", "am i allowed", "is it allowed")),
          ("In England and Wales you need a rod licence from the Environment Agency for any "
           "freshwater fishing, even for a day, and it is separate from the permission to fish: "
           "the lake or club sells a day ticket on top. Buy it online or at a Post Office - about "
           "£7 for a day, £13 for eight days, £35 for a season, per rod, and under-13s free. "
           "Scotland needs none for coarse or trout, but salmon does. Fishing without one is a "
           "fine."),
          bias=2,
          # a fish to cook, a fishing trip to plan, and the sea are other answers
          avoid=("cook", "cooking", "bake", "baked", "fry", "fried", "oven", "recipe", "eat",
                 "eating", "salmon fillet", "fish pie", "fishcakes", "how long to cook",
                 "sea", "beach", "boat", "harbour", "mackerel", "crab", "prawn", "smell",
                 "smells", "smelly", "polluted", "swim", "swimming", "pet", "tank",
                 # a fish to keep is a storage question, not a licence: "can i freeze fish" and
                 # "can i refreeze fish" said "you need a rod licence from the Environment
                 # Agency", because "fish" plus "can i" was enough for this entry.
                 "freeze", "freezer", "freezing", "frozen", "refreeze", "defrost", "thaw",
                 "thawed", "fridge", "leftovers",
                 # a pet being fed fish is not an angler: "can i give my cat fresh fish" and
                 # "can my dog eat fish" both said "you need a rod licence". The feeding shapes,
                 # not the bare animal: "can i take my dog fishing" is a licence question and
                 # still gets the licence.
                 "give my cat", "give my dog", "give the cat", "give the dog", "feed my cat",
                 "feed my dog", "feed the cat", "feed the dog", "give my kitten", "give my puppy",
                 # and a fish in a tank is fed, not angled: "do i need to feed fish every day" and
                 # "what should i feed my goldfish" both said "you need a rod licence"
                 "feed fish", "feeds fish", "feeding fish", "fed fish", "a fish fed",
                 "feed a fish", "feed the fish", "feed my fish", "feeding the fish",
                 "fish food", "goldfish", "aquarium", "tropical fish", "fish tank",
                 "can my cat eat", "can my dog eat", "can cats eat", "can dogs eat",
                 "my cat eat", "my dog eat", "can i give my", "is fish safe for",
                 "safe for cats", "safe for dogs", "safe for my cat", "safe for my dog",
                 # a fish to keep is a storage question, not a licence
                 "shelf life", "gone off", "still good", "use by", "sell by", "cooked", "raw",
                 "leftover fillet",
                 # and a present for somebody who fishes is the shopping question: "what can i
                 # buy my dad who likes fishing" met "fishing" and "can i" and got the licence
                 # how a fish lives is not a licence either: "why do fish need oxygen" and "do
                 # fish need air" both said "you need a rod licence from the Environment Agency",
                 # because "fish" plus "need" is this entry's whole key.
                 "oxygen", "breathe", "breathes", "breathing", "gills", "underwater",
                 "under water", "why do fish", "do fish need air", "need air",
                 # a fish being served is a dinner, not an angler: "what can i have with fish"
                 # said "you need a rod licence", because "fish" plus "can i" is this key. A
                 # serving frame is never about the sport, and none of these contains the word
                 # that would fold back onto this row's own key.
                 "have with", "have it with", "eat with", "goes with", "go with", "serve with",
                 "serving with", "pairs with", "alongside", "on the side", "as a side",
                 "side dish", "same with",
                 # a fish to cook with is a dinner too: "what can i make with smoked fish" said
                 # "you need a rod licence", because "fish" plus "can i" is this key and the
                 # serving frames above are all about what goes beside it rather than what the
                 # person is holding. A smoked fish is the clearest case - nobody angles for one.
                 "make with", "make from", "make out of", "do with", "use up", "using up",
                 "cook with", "cooking with", "recipe for", "a recipe", "smoked fish",
                 "smoked haddock", "smoked mackerel", "smoked trout", "kipper", "kippers",
                 ) + PRESENT_ASK),
    _RACE_COMPARED_CARD,
    _A_SHORTER_RACE_CARD,
]

# How long one session lasts, for the three people ask about most. These are plain duration
# questions - "how long should i cycle for", "how long does it take to swim a mile" - and with no
# row of their own they were reached by whatever entry ranked the sport word plus "how long": one
# of them answered with the phone's waterproofing, another with the food that keeps you full.
ENTRIES += [
    entry("cycle-duration",
          (("cycle", "cycles", "cycling", "bike", "bikes", "bicycling", "ride", "riding"),
           ("how long", "how far", "how many minutes", "how many miles", "how many km",
            "how much time", "duration", "distance")),
          "Thirty to sixty minutes at a pace where you can still talk is the everyday ride worth "
          "doing - roughly 10 to 20km - and three or four of those a week beats one long ride at "
          "the weekend. Add ten minutes to a ride a week rather than jumping to a long one, and "
          "take an easy day after a hard ride.",
          ask=("how long", "how far", "how many minutes", "how many miles", "how many km",
               "how much time", "duration", "distance"),
          # buying one, fixing one and whether cycling counts as exercise are other questions
          avoid=("buy", "buying", "worth", "cost", "price", "cheap", "puncture", "chain",
                 "saddle", "gears", "helmet", "e-bike", "ebike", "electric", "good for me",
                 "worth it", "benefits", "how often",
                 # a washer has a cycle too: "how long does a spin cycle take" is a machine
                 "washing machine", "washer", "wash cycle", "spin cycle", "dishwasher",
                 "tumble dryer", "dryer")),
    entry("swim-mile",
          (("swim", "swimming", "swimmer", "front crawl", "breaststroke", "lengths", "laps",
            "pool"),
           ("how long", "how many lengths", "how many laps", "how far", "a mile", "mile",
            "how many minutes")),
          "A mile is 1,600m, so 64 lengths of a 25m pool or 32 of a 50m one. A steady front-crawl "
          "swimmer takes about 30 to 40 minutes, and breaststroke or a first season 45 to 60. "
          "Build up 200m at a time - four lengths more each swim - rather than trying the mile on "
          "your first session.",
          ask=("how long", "how many lengths", "how many laps", "how far", "a mile", "mile",
               "how many minutes"),
          # the phone entry also keys "how long ... take" and ranks a rarer word, so a mile in the
          # pool was answered with IP67 and a dunk in fresh water; the length of a swim wins here
          bias=2,
          # learning to swim, a fear of the water and what to take are other questions, and how
          # long after eating is the cramp rule
          avoid=("learn", "lessons", "cant", "can't", "cannot", "scared", "frightened", "afraid",
                 "cost", "price", "open water", "sea", "triathlon", "goggles", "cap", "near me",
                 "eat", "eats", "eating", "ate", "cramp", "cramps", "stomach", "meal", "food",
                 # the mile is the distance question. A beginner asking how long to swim or how
                 # many lengths to do wants the starter (fitness.swim-start), not 64 lengths:
                 # "how long should i swim for" is not a request for a mile.
                 "should i swim", "swim a length", "beginner", "beginners", "starting out",
                 "how do i start", "get into swimming", "start swimming", "swim again",
                 # a baby or a toddler in the water is how long and how warm, not a mile
                 "baby", "babies", "newborn", "infant", "toddler", "month old", "months old")),
    entry("run-to-lose-weight",
          (("run", "running", "jog", "jogging", "cardio"),
           ("lose weight", "losing weight", "weight loss", "fat")),
          "The weekly total does more than any single run: build to 150 to 250 minutes a week of "
          "easy running, which is four or five half hours. A half hour of steady running burns "
          "roughly 300 calories, so the food you do not eat matters more than the extra mile - "
          "run somewhere you can still hold a conversation and keep it up rather than going hard "
          "twice and stopping.",
          ask=("lose", "losing", "weight", "fat", "how long", "how much", "how far",
               "how many", "should i", "best"),
          # the weight-loss entries rank higher on the same words and answer with the food; the
          # minutes and the calories of a run are this row's question
          bias=1,
          # how often to run is the running-every-day answer
          avoid=("every day", "everyday", "daily", "how often", "days a week", "times a week")),
    # --- the race you sign up for, and how the competitions differ ---------
    # A first 10k already has its row in fitness.py (`10k-training`), so the plan is not repeated
    # here: only the shape of the race itself, and the 5k build-up, are this domain's questions.
    entry("couch-to-5k", (("couch to 5k", "c25k", "couch to five k"),
                          ("plan", "work", "works", "how", "start", "weeks", "long", "app",
                           "explain", "what is", "does it", "5k")),
          "Couch to 5k is nine weeks of three runs a week, starting with 60 seconds of jogging "
          "alternating with 90 seconds of walking. Each week the jogging gets longer and the "
          "walking shorter, and by week nine you run 30 minutes without stopping. The free NHS "
          "podcast tells you exactly when to run and when to walk, which is the bit that makes it "
          "work for people who have never run."),
    entry("five-a-side-kit", (("five a side", "5 a side", "5aside", "five aside",
                               "seven a side", "small sided"),
                              # `first`, `game`, `start` and `goal` are not keys: "how do i
                              # improve my five a side game" is a coaching question, and a kit
                              # list is the wrong answer to it. "what should i bring to my first
                              # game" is carried by `bring` and `kit` already.
                              ("wear", "kit", "shin pads", "bring", "need",
                               "astro", "indoor", "outdoor")),
          "Astro trainers or moulded boots, shin pads, shorts and a top you do not mind sweating "
          "in, plus water. Most places play on 3G astro, so no studs, and a lot of leagues ask for "
          "the same colour top for the whole team - ask the organiser before you buy anything. A "
          "size 4 ball is the usual one for five a side, and someone always brings one.",
          # a general kit question is the other entry's, and the shirt-washing kind is not sport
          avoid=("wash", "washing", "smell", "smelly", "lost", "forgot", "left",
                 # the improvement question is a different question, and it punts honestly
                 "improve", "get better", "better at", "skills", "training", "practise",
                 "practice", "tactics",
                 # which boot for which surface is the other entry's whole answer, and this
                 # kit list says less about boots in one clause than that one says in a line
                 "boot", "boots", "studs", "moulded", "screw-in", "firm ground", "soft ground",
                 "astro trainers", "which boots", "what boots"),
          bias=1),
    entry("detraining", (("lose fitness", "lost fitness", "fitness loss", "detrain", "out of shape",
                          "lose my fitness", "how quickly do i lose"),
                         ("weeks", "couple", "two weeks", "time off", "break", "stop", "stopped",
                          "injury", "injured", "ill", "holiday", "true", "how long")),
          "You lose very little in a week or two: the fitness you built comes back quickly and "
          "rest can even leave you fresher. Real losses start after about two to four weeks off, "
          "and even then most of it returns within a few weeks of training again. What drops first "
          "is the top end - sprint speed and the pace you can hold hard - not your easy running. "
          "Come back at about 70% of where you left off for a week, then build."),
    entry("start-boxing", (("boxing", "boxer", "boxercise", "muay thai", "kickboxing"),
                          ("start", "starting", "begin", "beginner", "first", "learn", "get into",
                           "classes", "class", "join", "club", "gym", "how do i", "how to")),
          "Find a club that teaches technique rather than a fitness boxercise class - most amateur "
          "clubs run beginners' sessions and lend gloves and wraps for the first few. Go twice a "
          "week, expect the first month to be footwork, stance and the basic four punches on your "
          "own, and tell the coach you have not boxed before so nobody puts you in to spar. Boots, "
          "wraps and your own gloves are the only kit worth buying early.",
          # the rules of a bout are a different question from how to start, and so is how the
          # class left you feeling: "i did a boxing class and i was out of breath" names a class
          # but asks about the breathlessness, which is a fitness answer
          avoid=("rounds", "how many rounds", "judges", "knockout", "knock out", "points",
                 "out of breath", "breathless", "short of breath", "knackered", "dizzy",
                 "felt sick", "feel sick", "sore", "aching", "hurt", "injury", "injured",
                 "i was", "i felt",
                 # "box" is a cardboard one as often as it is the sport: "how do i lift a heavy
                 # box safely" was sent to a boxing club. Phrases, so `boxing` itself still keys.
                 "heavy box", "heavy boxes", "cardboard box", "cardboard boxes", "a box of",
                 "packing boxes", "moving boxes", "stack of boxes", "lifting a",
                 "lift a", "moving house", "parcel", "parcels", "suitcase", "sofa", "wardrobe"),
          # ...and a cardboard box is not a fighter: see the guard above
          guard=_not_a_line_about_a_box),
    
    entry("sports-results", (("who won", "team won", "the score", "final score", "the result",
                              "the results", "who is winning", "who's winning",
                              "league table"),
                             ("match", "game", "play", "played", "playing", "won", "score",
                              "result", "results", "table", "last night", "yesterday", "tonight",
                              "weekend", "cup", "final", "league")),
          _cant_see_the_score,
          # "who won the election" and "who won the bake off" are the news hedge's, not a sport
          # answer: the line has to name something that is played
          ask=("match", "game", "games", "play", "played", "playing", "football", "rugby", "cricket",
               "tennis", "sport", "sports", "team", "teams", "league", "cup", "final", "score",
               "nil", "half", "kick off", "table", "season", "club", "united", "city", "fc"),
          # a line about who to support, or about the rules, is a different question, and so is
          # one asking what a league table IS: "whats the league table" wants the explanation
          # of how a table works, not an admission that I cannot see it
          avoid=("who should i", "which team should", "support", "rules", "offside", "how does",
                 "whats the league table", "what is the league table", "whats a league table",
                 "what is a league table", "league table mean", "league table work")),
]

# The question after an illness, which is not the rest-day rule and not the "tired after flu"
# answer: "how long till i can run again after flu" was getting the fatigue advice.
ENTRIES += [
    entry("back-to-running",
          (("running", "run", "jogging", "jog", "training", "gym", "exercise", "swim",
            "swimming", "cycling", "cycle"),
           # "rest before" and "how much rest" are not here: how many easy days to take is the
           # rest-day question, and this entry answers coming back after illness
           ("run again", "how long", "before i run", "before running", "before a run",
            "running again", "back to running", "get back to", "return to", "time off",
            "after being ill", "after the flu", "after a cold", "after a week off",
            "after illness", "after having flu", "start running again",
            "when can i", "when can i run", "when can i start", "how soon can i")),
          "Above the neck and no temperature - a cold, a sore throat - and an easy run is fine "
          "once you feel up to it. Flu or a fever means a week of easy effort after the fever has "
          "gone, building back up over two or three weeks, because the fatigue outlasts the "
          "illness. For a strain or a niggle, walk pain-free first, then run and walk in "
          "alternate minutes, and add a little each week rather than starting where you left off.",
          # illness plus running is this answer, not the general "tired after flu" one, and not
          # the dessert table, which also ranks "when can i" highly
          bias=4,
          # This entry answers coming BACK: after flu, after a fever, after time off. Without this
          # gate the key's "how long" and a sport word were enough, and a plain duration question
          # got the illness rule - "how long is a good gym session" and "how long should i run to
          # lose weight" were told about running with a cold. The words here are what makes the
          # line the recovery question; a duration question with none of them belongs to the
          # workout, the run-walk or the swimming entry.
          ask=("flu", "cold", "ill", "illness", "fever", "sick", "virus", "bug",
               "chest infection", "cough", "throat", "hospital", "operation", "surgery",
               "week off", "time off", "run again", "running again", "back to running",
               "get back to", "return to", "start running again",
               # the illness does not always have a disease noun: "i was in bed all week when can
               # i run again" is the same question, and so is "i have been off work"
               "poorly", "covid", "tonsillitis", "sprain", "strain", "injury", "injured",
               "niggle", "glandular", "bronchitis", "pneumonia", "sinusitis", "ear infection",
               "food poisoning", "been off", "in bed", "off work", "off sick", "bed all week",
               "unwell", "not well", "run down", "recovering", "recovery", "got over",
               "getting over", "temperature"),
          # a rest-day question, a training plan and a sore part are all different questions
          avoid=("rest days", "rest day", "between sessions", "between runs", "between workouts",
                 # weather "cold" is not the illness "cold": "how long should i run in the cold"
                 # is a question about clothing and effort, not about coming back from a virus
                 "in the cold", "cold weather", "cold out", "freezing", "hot weather",
                 "in the heat", "the heat", "wind", "windy", "raining", "rain",
                 # stretching and warming up are the stretch entry's question: "should i stretch
                 # before running" was getting the cold-and-training answer
                 "stretch", "stretches", "stretching", "warm up", "warming up", "warmup",
                 "cool down", "cooling down",
                 # what to eat before a run is the food answer, and the food words were reaching
                 # "before a run" here: "what should i eat before a run" got the cold rule
                 "eat", "eats", "eating", "food", "breakfast", "fuel", "carb", "carbs",
                 "drink", "drinks", "drinking", "hydrate", "hydration", "water",
                 # getting back into it after a break is the start-running answer, which owns
                 # "run-walk, one minute of jogging to two of walking" - and so is wanting to
                 # start again, which says "start running again" and would otherwise read as
                 # "run again" here
                 "getting back", "back into", "after a break", "got out of the habit",
                 # wanting to start again is the run-walk plan; "when can i start running
                 # again after being ill" is still this answer, so only the wanting is here
                 "want to start", "wants to start", "wanting to start", "want to get back",
                 "thinking of starting", "keen to start", "hoping to start", "out of shape",
                 "rest before running", "rest before a run", "rest before i run", "how much rest",
                 "how often", "days a week",
                 # learning to swim is the swimming-lesson answer, not the
                 # come-back-after-illness one: "how long does it take to learn to swim" got the
                 # cold-and-training rule, because "swim" is a word here and so is "how long"
                 "learn to swim", "learning to swim", "learn swimming", "swim lessons",
                 "swimming lessons", "swim school", "cannot swim", "cant swim", "can not swim",
                 "couch to 5k", "marathon", "10k", "half", "parkrun", "plan", "training plan",
                 "tweaked", "pulled", "sprain", "sprained", "knee", "shin", "ankle", "calf",
                 "achilles", "hurt", "hurts", "pain", "injury", "injured",
                 # a return after years is the run-walk plan, not coming back from an illness:
                 # "how do i start running again after years" was getting the cold rule from
                 # "start running again"
                 "after years", "years ago", "years off", "been years", "used to run",
                 "used to jog", "stopped running", "years since",
                 # a bone is not a cold: "how long till i can run again after a stress
                 # fracture" is the fracture's question, and "an easy run is fine once you feel
                 # up to it" is wrong advice for a bone that is healing
                 "fracture", "fractures", "fractured", "stress fracture", "broken bone",
                 "hairline", "cracked bone")),
    # A broken bone is its own question, and nothing in the knowledge answered it: the line went
    # to the illness rule ("an easy run is fine once you feel up to it"), which is the opposite
    # of what a healing bone needs.
    entry("stress-fracture",
          # a wrist, a rib or a spine is not a running injury, so the row keys only the
          # fracture words; "broken bone" on its own was catching "how long does a broken bone
          # take to heal", which is not this question
          (("stress fracture", "stress fractures", "fracture", "fractures", "fractured",
            "hairline crack"),
           ("run", "running", "jog", "jogging", "sport", "exercise", "training", "train",
            "shin", "shins", "foot", "feet", "leg", "legs", "again", "off",
            "weeks", "how long", "heal", "healing",
            # the bare subject with nothing else in the line - "i have a stress fracture" was an
            # acknowledgement and no answer at all
            "have", "has", "got", "ive", "diagnosed", "doctor", "gp", "x-ray", "xray")),
          "Six to eight weeks off running is the usual answer for a stress fracture, and the bone "
          "decides rather than the calendar. A foot one often gets a walking boot for a few "
          "weeks. Keep some fitness with swimming or cycling if that is pain-free, and come back "
          "with walk-run: a minute of jogging to two of walking, adding a minute a week. Get it "
          "looked at if one small spot is tender to a fingertip or it hurts sitting still.",
          # the same word in another body part, the other senses of break, and the line that is
          # still asking whether it is broken or what it is - the tell-it-apart and X-ray card
          # owns those, and "six to eight weeks off running" is advice for someone who already
          # knows the bone is cracked, not for someone working out whether it is
          avoid=("think", "thinking", "might have", "could be", "not sure", "do i have",
                 "is it broken", "is it a fracture", "is it a stress fracture", "broken or sprained",
                 "shin splints", "how do i tell", "how to tell", "tell the difference",
                 "show on", "x-ray", "xray", "scan", "mri",
                 "arm", "arms", "wrist", "wrists", "hand", "hands", "finger", "fingers",
                 "rib", "ribs", "collarbone", "shoulder", "shoulders", "hip replacement",
                 "back", "backs", "spine", "spinal", "neck", "vertebra",
                 "osteoporosis", "bone density", "heart", "heartbroken", "phone", "screen",
                 "wind", "voice",
                 # a work question is the sick-note answer, not six to eight weeks off running:
                 # "how long off work with a stress fracture" got this card and said nothing
                 # about work, and "how long does a hairline fracture take to heal" got it for a
                 # bone that can be a wrist, so the bare "hairline fracture" shape is left to
                 # whatever answered it before, while "hairline crack" in the key still reaches
                 # the running lines that name one
                 "off work", "sick note", "fit note", "back to work", "hairline fracture",
                 # a line still working out whether the bone is cracked is the four-steps-and-an-
                 # X-ray card's: "is my foot fractured" and "how do i know if ive got a stress
                 # fracture" were taking the recovery weeks instead, and the telling-apart words
                 # the entry already held are not the order these come in
                 "how do i know", "do i know", "can i tell", "is my", "do i have one",
                 "feel like")),
    entry("goggles-that-fog",
          (("goggles", "goggle", "mask", "lens", "lenses", "swim cap"),
           ("fog", "fogging", "fogged", "foggy", "steam", "steams", "steamed", "steaming",
            "mist", "misting", "misted", "clear", "blurred", "condensation", "swim", "swim",
            "swimming", "pool", "lens")),
          _goggles_fog,
          # the car in fog, the bathroom mirror and the glasses are other rows' questions
          avoid=("car", "driving", "headlights", "windscreen", "wipers", "motorway", "road",
                 "mirror", "bathroom", "shower", "window", "windows", "spectacles",
                 "glasses", "walking", "walk"),
          # the car's fog row scores the same on a line that says fog and how, and it was
          # winning the tie, so this row has to outrank it
          guard=the_goggles_are_for_swimming,
          bias=2),
    entry("basketball-layup",
          (("layup", "lay up", "lay-up", "layups", "lay ups", "drive to the basket",
            "finish at the rim", "under the basket"),
           ("basketball", "basket", "hoop", "rim", "backboard", "ball", "how")),
          "Go up off the foot opposite your shooting hand - right hand, left foot - and take the "
          "last dribble with the outside hand a stride before you jump. Bring the ball up in two "
          "hands and let it go softly off the backboard into the top corner of the square, rather "
          "than throwing it at the rim. Aim to jump up rather than forward: most missed layups are "
          "a jump that was too long and too fast.",
          ask=("how", "what", "should", "help", "better"),
          avoid=("rules", "foul", "points", "positions", "travel", "travelling", "highway")),
    entry("spin-a-cricket-ball",
          (("spin", "spinner", "spinning", "leg spin", "off spin", "turn the ball", "ripping"),
           ("cricket", "ball", "bowl", "bowling", "bowler", "off break", "leg break", "googly",
            "seam", "fingers")),
          "Spin comes from the fingers and the wrist, not the shoulder: hold the ball across the "
          "seam in the fingers rather than deep in the palm, and as the arm comes over give it a "
          "sharp clockwise rip from the third finger so it turns off the pitch. Keep the arm "
          "straight and the run-up slow - spin is a skill of the hand, and the slower ball turns "
          "more. Practise on a line until the ball lands where you look.",
          ask=("how", "what", "should", "help", "better"),
          avoid=("rules", "points", "wicket", "score", "overs", "match", "spin class",
                 "spin cycle", "washing machine", "spin dryer", "spin doctor", "spinning class",
                 "spin bike", "road bike"),
          bias=2),
    entry("tennis-backhand",
          (("backhand", "back hand", "two handed backhand", "one handed backhand",
            "double hander"),
           ("tennis", "court", "racket", "racquet", "ball", "how", "hit", "swing")),
          "Turn your shoulders as the ball comes and take the racket back with both hands if it is "
          "a two-hander, then meet the ball out in front of your front hip with a flat face and "
          "swing low to high so the ball lifts. Hold the finish over your shoulder rather than "
          "stopping at the ball - the follow-through is where the control comes from. Practise "
          "the turn first: most backhands fail on the shoulders, not the arm.",
          ask=("how", "what", "should", "help", "better"),
          # a backhanded compliment is the snide-email card's question, and the vegetable is not
          # this row's: fencing "squash" sent "how do i improve my backhand at squash" to a
          # butternut squash recipe, so the game keeps the card it had
          avoid=("backhanded compliment", "backhanded remark", "backhanded comment",
                 "a compliment", "rules", "score", "butternut", "roast squash", "squash soup",
                 "squash the", "table tennis", "padel", "drive"),
          bias=2),
    entry("rugby-drop-goal",
          (("drop goal", "drop goals", "drop kick", "dropkick", "drop kicked", "three points"),
           ("rugby", "posts", "over the posts", "conversion", "penalty try", "score")),
          "For a drop goal, catch the pass and hold the ball out in front of you with its point "
          "down, then drop it and kick it off the ground as it starts to bounce - the ball has to "
          "touch the ground first, so the timing is the whole skill. Watch the ball rather than "
          "the posts, keep your head down, and strike through the bottom half so it goes up and "
          "over. Practise from ten metres until you can do it without looking at your feet.",
          ask=("how", "what", "should", "help", "better"),
          avoid=("goal setting", "set a goal", "smart goal", "goals for", "new year", "target",
                 "aim", "resolution"),
          bias=2),
    entry("football-throw-in",
          (("throw in", "throw-in", "throw ins", "throw-ins", "throw the ball in",
            "take a throw", "long throw"),
           ("football", "soccer", "touchline", "pitch", "keeper", "corner", "byline",
            "the line", "how")),
          "Both feet stay on the ground behind the line, and the ball goes back over your head "
          "with both hands on it from behind - a foot over the line or a hand that comes round "
          "the side turns it over. Plant both feet shoulder width, get some bend in the elbows and "
          "throw it flat to a teammate's feet rather than high and looping. The long throw is a "
          "run-up and a bigger arch of the back, and it is worth learning only if you can reach "
          "the box.",
          ask=("how", "what", "should", "help", "better"),
          avoid=("bin", "bins", "rubbish", "trash", "away", "out", "recycle", "laundry",
                 "washing", "clothes", "old", "throw the ball at", "throw up")),
    entry("learn-to-skateboard",
          (("skateboard", "skateboards", "skateboarding", "skate", "longboard", "ollie",
            "cruiser"),
           ("learn", "start", "beginner", "first", "how", "begin", "ride", "balance")),
          "Find flat, empty tarmac and a line to stand on, and learn to push and stop before you "
          "try anything else: front foot across the board at an angle, back foot on the ground, "
          "and three pushes then both feet on. Bend your knees and keep your weight over the "
          "board rather than leaning back, and look where you are going, not at your feet. A "
          "helmet and wrist guards cost less than an evening in A&E, and pads make you braver.",
          ask=("how", "what", "should", "help", "start", "begin"),
          # a skateboard on the road is a road question, and the transport card answers it
          avoid=("price", "cheap", "buy", "gift", "present", "brand", "skating on thin ice",
                 "ice", "rules", "on the road", "road", "roads", "traffic", "street",
                 "cycle lane", "pavement")),
    entry("snooker-break-off",
          (("break off", "break off shot", "breaking off", "opening shot", "break shot",
            "first shot"),
           ("snooker", "cue", "billiards", "pool table", "reds", "baulk", "pack", "frame",
            "table")),
          "Put the cue ball just off the side cushion and hit the outside of the pack thinly with "
          "screw, so the cue ball comes back up the table and tucks behind baulk rather than "
          "sitting in the open. A soft, thin contact brings a red out to the side pocket for the "
          "next shot, and the safety is the point: the break-off is not a shot to win the frame "
          "with. Do not hit the pack straight on, because that leaves the cue ball in the middle.",
          ask=("how", "what", "should", "help", "better"),
          avoid=("rules", "points", "score", "ball count", "how many", "take a break", "break up",
                 "break in", "breaking in", "tea break", "lunch")),
    entry("golf-putting",
          (("putt", "putts", "putting", "putter", "green", "lag putt", "three putt"),
           ("golf", "hole", "score", "better", "improve", "how", "practice", "practise")),
          "For most club golfers the pace matters more than the line: pick a spot a foot past the "
          "hole on the high side and try to roll the ball over it, because a putt that finishes "
          "close is holed eventually and one that is hit too hard is not. Keep the wrists still "
          "and rock the shoulders, with the same length back and through. On long putts, aim to "
          "leave it inside a metre rather than to hole it.",
          ask=("how", "what", "should", "help", "better", "improve"),
          # the aim-and-the-tee row already answers "how do i improve my putting", and it says it
          # better than this one does: this row is for the stroke itself
          avoid=("put the kettle", "put off", "put on", "put up with", "put down", "put away",
                 "putting on", "putting off", "putting up", "put it", "rules", "handicap",
                 "improve my putting", "better at putting", "putting tips", "my putting",
                 "putting stroke", "putting lesson",
                 # a bare "put" is read as this row's "putting", so "how do i put a zip in a
                 # dress" was the pace-of-putting answer. A zip is not a putt.
                 "zip", "zips", "zipper", "zippers", "sew", "sewing", "seam", "hem")),
    # --- getting better at a game ------------------------------------------
    # "how do i get better at tennis" was a shrug, and the same ask for cricket, basketball,
    # darts and badminton reached the rules card, because those rows carry the bare word "how"
    # in their second key and nothing else scored higher. A person asking how to get better
    # wants the two or three things that lift a club player, not the shape of the game, so each
    # of these rows is keyed on the asking (get better, improve, practise) plus the game, and
    # outranks the rules card on score rather than on bias.
    entry("tennis-get-better",
          (("get better", "get better at", "improve", "better at", "practise", "practice",
            "technique", "training", "my forehand", "my backhand", "my game"),
           ("tennis", "forehand", "backhand", "racket", "racquet", "court", "baseline")),
          "Club tennis is won by keeping the ball in, so play the percentages: height over the net "
          "and length to the back of the court, and count how many cross-court balls you can rally "
          "without missing - 20, then 30. Two sessions a week of that beats a new racket. Then "
          "practise the shot that actually loses you games: 50 serves to the same corner, and 50 "
          "returns down the middle.",
          # the serve has its own answer, and a court or a racket question is a fact, not coaching
          avoid=("table tennis", "ping pong", "paddle", "serve", "serving", "toss",
                 "double fault", "how big", "how long", "size",
                 "dimensions", "resting", "cost", "price", "best racket", "which racket",
                 "elbow", "wrist", "shoulder",
                 # a forehand that hurts is a body question, not a coaching one: "my forehand
                 # hurts" was getting the drills. The body words are here rather than on one
                 # order of them, because the person can put the pain anywhere in the line.
                 "hurt", "hurts", "hurting", "pain", "pains", "painful", "sore", "soreness",
                 "ache", "aches", "aching", "injury", "injured", "injuring", "tennis elbow",
                 "stiff", "strain", "strained", "swollen", "swelling", "torn", "physio",
                 "physiotherapy", "doctor", "nhs", "gp")),
    entry("first-touch",
          (("first touch", "first touches", "touch", "control", "cushion", "improve", "get better",
            "practice", "practise"),
           # the game is not enough: "how do i get better at football" already has a good
           # answer that names a first touch and passing with both feet, and it keeps it
           # "control" alone is not a football word: "how do i get better at controlling my
           # spending" was answered with a first touch. The ball phrasings keep the football.
           ("first touch", "my touch", "touch", "control the ball", "ball control",
            "controlling the ball", "touch and control", "cushion", "first")),
          "A first touch is a cushion, not a stop: as the ball arrives, take the pace out of it and "
          "push it a stride ahead into the space you are about to run into. Kick a ball against a "
          "wall 200 times a day with each foot, using the inside and the sole, then have a partner "
          "pass at speed. Twenty minutes of wall work a day fixes more first touches than any drill "
          "with cones.",
          avoid=("remote", "tv", "television", "birth control", "the pill", "pest control",
                 "weeds", "mould", "damp", "temper", "lose control")),
    entry("dribbling",
          (("dribbling", "dribble", "close control", "keep the ball"),
           ("football", "soccer", "improve", "better", "practice", "practise", "cones")),
          "Keep the ball within a stride of you and touch it every step or two - small touches "
          "with the inside and outside of both feet, head up so you can see the pass before you "
          "make it. Four cones two metres apart, through them slow enough to be perfect, then "
          "faster, then with someone shadowing you. A change of pace beats a change of direction: "
          "slow, then push it past and go.",
          # basketball dribbling is a different answer, and a football boot or a match question
          # is not this
          avoid=("basketball", "hoop", "boots", "rules", "offside", "how many players")),
    entry("golf-swing",
          (("get better", "get better at", "improve", "practice", "practise", "fix", "stop",
            "stopping", "swing", "swings", "off the tee", "slice", "slicing", "hook",
            "hooking", "half swing", "ball striking", "my drive", "my tee shot", "my driver",
            "hit my driver", "hit my drive", "hit my irons"),
           ("golf", "swing", "swings", "drive", "driver", "drivers", "tee", "slice", "hook",
            "chipping", "putting", "irons", "fairway", "bunker")),
          "For most club golfers it is not the swing but the aim and the tempo: check that feet, "
          "hips and shoulders all point where you want the ball to start, then swing at eight out "
          "of ten with a smooth one-two count. Practise half-swings with a 7 iron and brush the "
          "grass - the divot should come after the ball. Two or three lessons with a pro filming "
          "you will save a season of guessing.",
          # a swing in a garden or a park is a seat, and mood swings and swing shifts are not golf
          # slicing a loaf, an onion or a finger is a kitchen question, and it is the only
          # thing that kept the bread answer off "how do i stop slicing bread"
          avoid=("bread", "loaf", "loaves", "cake", "onion", "onions", "garlic", "meat", "roast",
                 "ham", "cheese", "finger", "fingers", "hand", "kitchen", "knife",
                 "garden", "park", "playground", "swing seat", "swingball", "mood", "moods",
                 "shift", "vote", "voting", "election", "how many holes",
                 "how long", "handicap", "rules", "score", "scoring", "cost", "price",
                 # a driving test is not a golf shot: "my driving test" matched "my drive" and a
                 # person who failed it got the aim-and-tempo card. A computer drive is not one
                 # either, and neither is a driving licence.
                 "driving test", "driving lesson", "driving licence", "driving license",
                 "driving theory", "hard drive", "flash drive", "usb", "printer", "back up",
                 # "drive" and "hook" are ordinary words too: a car, a computer and the hook a
                 # coat goes on were all answered with the aim-and-tempo card
                 # "driving" alone is not in this list: an avoid word is matched loosely, so
                 # it also stood the row down for "my drive" and cost the golf lines
                 "car", "cars", "at driving", "driving a car", "driving on", "learn to drive",
                 "driving school", "drive to", "laptop", "laptops", "coat hook",
                 "wall hook", "picture hook", "curtain", "curtains", "hooks on the wall",
                 # the drive in front of the house: a stain or moss on the paving is the
                 # cleaning row's line, not a shot off the tee
                 "stain", "stains", "stained", "driveway", "drive way", "off the drive",
                 "on the drive", "moss", "pressure wash", "jet wash", "paving",
                 # a learner is not a golfer either: "can i practice driving with a learner" has
                 # the word "practice" and matched "drive". Fenced by the words that come with a
                 # learner rather than by one order of them.
                 "learner", "learners", "learner driver", "provisional", "driving with",
                 "practice driving", "practise driving", "driving practice", "driving practise",
                 "dual controls", "instructor", "parallel park", "bay park", "test route",
                 # and a hook on a coat is not a slice: "coat hook" was fenced, "a hook on a
                 # coat" was not
                 "coat", "coats", "on a coat", "jacket", "jackets", "hanger", "hangers",
                 "curtain rail", "picture rail"),
          # "put" is the everyday verb far more often than it is a stroke, and the row's "stop"
          # was enough to bring the golf answer to a bathroom that needs an extractor fan
          guard=_a_put_is_not_a_putt),
    entry("cricket-get-better",
          (("get better", "get better at", "improve", "better at", "practice", "practise",
            "technique", "batting", "bowling", "score runs", "my batting", "my bowling",
            # the ask side of the bowling half: "how do i bowl a yorker" names the ball and the
            # delivery but no word on this side, so the row never matched and the line got the
            # search hedge
            "bowl", "bowled", "bowling a", "how do i bowl", "my action", "run up", "no ball",
            "no balls", "yorker"),
           # the words of the bowling half: "how do i bowl a yorker" matched nothing but the
           # ordinary "bowl" before, and the guard now wants a cricket word beside it
           ("cricket", "nets", "bowler", "batting", "bowling", "wicket", "batsman", "batter",
            "yorker", "bouncer", "googly", "off stump", "leg stump", "crease", "seam",
            "bowling action", "spin bowling", "how do i bowl")),
          # the half of the game the line names leads, and a line that names neither opens
          # with batting, which is what most club players mean by "get better at cricket"
          _cricket_better,
          # the rules, the formats and the length of a match are other answers
          avoid=("rules", "work", "lbw", "leg before", "how long", "how many overs", "t20",
                 "ashes", "world cup", "history", "duck", "how many players",
                 # lawn bowls is the other game with a bowl in it: "how do i get better at
                 # bowls" was given the batting card. Only words that cannot turn up in a
                 # bowling line: a bare "bowls" or "at bowls" loose-matches "bowling", which
                 # stood the row down for "how do i improve my bowling". The word "bowls" on
                 # its own is the guard below.
                 "lawn bowls", "crown green", "indoor bowls", "bowls club", "bowls match",
                 "play bowls", "playing bowls", "game of bowls", "bowls green", "jack high"),
          # "how do i get better at bowls" says the other game and no cricket, and "bowls" as a
          # word of its own is the only thing that tells them apart. The other test is the word
          # "bat" itself: it is a thing in the game and a thing in a loft, and a line that says
          # neither the game nor anything about playing it is not this row's.
          guard=_the_game_and_not_another),
    
    entry("basketball-get-better",
          (("shooting", "shoot", "my shot", "jump shot", "free throws", "free throw", "get better",
            "improve", "practice", "practise", "technique",
            # the dribble is the other half of the game: "how do i get better at dribbling a
            # basketball" got the shooting card
            "dribble", "dribbling", "dribbled", "ball handling", "ball-handling",
            "bring the ball up", "crossover"),
           # "ball handling" names the game by itself: "how do i improve my ball handling" was
           # answered with a door handle, because no basketball word was in the line
           ("basketball", "hoop", "foul line", "free throw line", "three point",
            "ball handling", "ball-handling", "dribbling a basketball")),
          # the part of the game the line names leads, and a line that names neither opens
          # with shooting, which is what most people mean by "get better at basketball"
          _basketball_better,
          avoid=("rules", "work", "points", "quarters", "how many players", "how long",
                 "court size", "how big",
                 # a dribble in football is the first-touch row's line, and it has its own answer
                 "football", "soccer", "foot", "feet", "netball")),
    entry("darts-get-better",
          (("get better", "improve", "practice", "practise", "technique", "my throw", "throwing",
            "accuracy", "consistent"),
           ("darts", "treble", "double", "oche", "board", "180")),
          "Change nothing but the aim: same stance, same grip, same speed every throw, elbow up, "
          "and a follow-through that finishes with your hand pointing at the target. Practise in "
          "blocks - 20 darts at treble 20, then 20 at the doubles round the board, and always "
          "finish on a double. If the darts drift, slow the throw down rather than throwing "
          "harder; speed is what scatters them.",
          avoid=("rules", "501", "checkout", "scoring", "score", "how many", "how long")),
    entry("badminton-get-better",
          (("get better", "improve", "practice", "practise", "technique", "footwork", "my serve"),
           ("badminton", "shuttle", "shuttlecock", "racket", "racquet")),
          "Badminton is won with the feet: after every shot get back to the middle of the court, "
          "and split-step as your opponent hits so you can move either way. Learn the overhead "
          "clear hit high and deep to the back line, then the drop shot from the same action, so "
          "your opponent cannot read it. Twenty minutes of shadow footwork with a racket in your "
          "hand beats an hour of hitting.",
          avoid=("rules", "scoring", "score", "how many points", "how long", "court size")),
    # "how do i serve in volleyball" was the rules card and then the passing answer: the serve is
    # a technique of its own and the first sentence has to be about it.
    entry("volleyball-serve",
          (("serve", "serving", "my serve", "overhand serve", "underhand serve", "float serve",
            "jump serve", "serves", "goes long", "keeps going long", "keeps going out"),
           ("volleyball", "volley ball", "volley-ball", "over the net", "the net")),
          "Toss the ball low and just in front of your hitting shoulder - a high toss behind you "
          "is why serves go long - then hit it with the heel of your hand, arm swinging fast and "
          "straight, and aim at a spot (deep middle, or the gap between two passers) rather than "
          "just over the net. Practise twenty a session and count the ones that land in: a serve "
          "that goes in beats an ace you miss.",
          # "serve" is dinner, a summons and a tennis shot as well
          avoid=("dinner", "food", "drink", "wine", "portion", "tennis", "badminton", "squash",
                 "padel", "legal", "notice", "papers", "prison", "time"),
          bias=1),
    entry("volleyball-get-better",
          (("get better", "improve", "practice", "practise", "technique", "my pass",
            # the skills with a coaching answer: a spike, a dig and a block were a punt once the
            # rules card stopped taking a bare "how"
            "spike", "spiking", "dig", "digging", "block", "blocking", "setting", "set"),
           ("volleyball", "volley ball", "volley-ball")),
          "Volleyball starts with the pass: get your feet there early, lock your arms into a "
          "platform and let the ball come to you instead of swinging at it - it should go up and "
          "to the setter, not forward. A spike is the last touch of three: high approach, arm back, "
          "and hit the top half of the ball so it drives down; a dig is the same low platform, "
          "absorbing the ball rather than swinging at it. Serve overhand for consistency, and call "
          "the ball loudly.",
          avoid=("beach", "rules", "how many players", "how long")),
    entry("rowing-technique",
          (("get better", "improve", "technique", "form", "practice", "practise", "split",
            "properly", "proper", "good form", "right way", "catch", "drive",
            "how do i", "how to", "learn"),
           ("rowing", "row", "rows", "rowed", "rower", "erg", "ergo", "ergometer",
            "rowing machine", "concept 2", "oars", "scull", "sculls", "eight", "cox",
            "boat", "boats", "a boat", "the boat", "indoor rower")),
          "Rowing is legs, then body, then arms on the drive, and arms, body, then slide on the way "
          "back. Keep the handle level and pull it to the same spot at the bottom of the ribs every "
          "stroke, and rate 20 to 22 rather than thrashing at 30. Ten minutes of steady pieces "
          "with someone filming you side-on will show the timing errors faster than any coaching "
          "cue.",
          # "row" is an argument, a line of seats and a line of houses: only the boat and the
          # machine words reach here
          # the argument rows both reach a bare "how do i row", and this card says the thing the
          # boat lines are asking for
          bias=1,
          avoid=("argument", "row with", "row about", "arguing", "quarrel", "fight", "seats",
                 "houses", "terraced", "front row", "death row", "rules",
                 # "we had a proper row" is the other kind of row, and "proper" and "good form"
                 # are the words somebody uses about an argument too: the words that say the
                 # row was a falling-out have to keep the boat card out of it
                 "had a row", "having a row", "a row with", "our row", "massive row",
                 "huge row", "proper row", "bitter row", "row last night", "rows with")),
    entry("cycling-get-better",
          (("get better", "improve", "faster", "training", "train", "practice", "practise"),
           ("cycling", "cycle", "bike", "bicycle", "rides", "riding")),
          "Ride easy miles before hard ones: three or four rides a week with one long steady one, "
          "spinning at 80 to 90 turns a minute in a gear you can hold. Add one session of 4 x 5 "
          "minutes hard with 5 minutes easy between, and put the hills in the long ride. Check "
          "saddle height first - a saddle too low costs power and sore knees.",
          # a motorbike, a bike to buy and a child learning to ride are other questions
          avoid=("motorbike", "motorcycle", "scooter", "moped", "which bike", "best bike",
                 "buy", "cost", "price", "child", "son", "daughter", "toddler", "learn to ride",
                 "stabilisers", "puncture", "chain", "brakes", "helmet",
                 # "riding" is a bike word and a horse word: "how do i get better at horse
                 # riding" was told to spin at 80 to 90 turns a minute
                 "horse", "horses", "pony", "ponies", "equestrian", "trot", "canter",
                 "gallop", "stirrups", "riding hat", "riding school", "hacking",
                 # a train ride and a coach trip are not a bike: "what do i need for a 4 hour
                 # train ride" was told to spin at 80 to 90 turns a minute
                 "train ride", "train journey", "train trip", "coach trip", "coach journey",
                 "bus journey", "bus trip", "by train", "on a train", "on the train",
                 "by coach", "on a coach")),
    entry("horse-riding",
          (("get better", "improve", "learn", "ride", "riding", "sit", "canter", "trot",
            "stop bouncing", "how do i"),
           ("horse", "horses", "pony", "ponies", "equestrian", "trot", "canter", "gallop",
            "stirrups", "riding hat", "riding school", "hacking")),
          "Sit deep and still: a long leg with the heel down and a soft hand that follows the "
          "horse's mouth does more than any amount of kicking. Learn to absorb the movement in "
          "your hips rather than your hands - walk and trot without stirrups, on the lunge if you "
          "can - and ride a well-schooled horse at a riding school for a term; the feel of a "
          "trained one teaches faster than a green horse will.",
          # a horse to buy, a bet and an injury are other questions
          avoid=("buy", "buying", "cost", "price", "how much", "race", "racing", "bet", "bets",
                 "fall", "fell off", "injury", "injured", "back hurts", "vet")),
    entry("pool-table-get-better",
          (("get better", "get good", "get good at", "improve", "practice", "practise", "play",
            "playing", "cue ball", "my break", "position"),
           # "control" alone is not a cue word: "how do i get better at controlling my anger"
           # was answered with the cue ball, and so was controlling your temper or your
           # drinking. The cue-ball phrasings keep the pool lines.
           ("pool", "billiards", "eight ball", "8 ball", "pool table", "cue", "snooker",
            # "ball control" is football's line, so the cue is named
            "cue ball control", "control the cue", "controlling the white", "control the white",
            "spin", "pot", "table")),
          "Cue games are won with the cue ball, not the pot: before every shot decide where the "
          "white has to finish for the next one, and hit it with the pace that leaves the easiest "
          "next shot rather than the hardest pot. Play the shot you can make nine times out of ten. Practise "
          "a straight pot up and down the table 50 times, stopping the cue ball dead, then "
          "following through and screwing back.",
          # a swimming pool is another answer, and so is a pool of water or a car pool.
          # The fitness starter keys "how do i ... pool" and is registered before sport.py, so
          # this row wins a tie on bias rather than on order.
          bias=1,
          avoid=("swim", "swimming", "lengths", "lido", "water", "car pool", "carpool", "typing",
                 "gene pool", "pool of",
                 # "table" alone is a tennis table too: "how do i get better at table tennis"
                 # was given a cue and a white ball
                 "table tennis", "ping pong", "tennis",
                 # the phone game is not a table
                 "phone", "app", "apps", "video game", "on my tablet", "online game",
                 # self-control is not cue control
                 "anger", "angry", "temper", "emotions", "impulse", "drinking", "appetite",
                 "blame", "my feelings", "anxiety", "stress",
                 # a spin class is the other thing people call spinning: "how do i get better
                 # at spinning" was told to use the cue ball. Phrases again, so "how do i put
                 # spin on the cue ball" and "how do i spin the white" keep the cue.
                 "spin class", "spin classes", "spinning class", "spinning classes",
                 "at spinning", "my spinning", "indoor cycling", "exercise bike", "peloton",
                 "soulcycle", "rpm")),
    entry("run-form",
          (("form", "technique", "cadence", "posture", "overstriding", "over striding",
            "heel strike", "running style", "run properly"),
           ("run", "running", "jog", "jogging", "my run", "runs")),
          "Run tall and quiet: a slight lean from the ankles, feet landing under your hips rather "
          "than out in front, and a quicker, shorter stride - about 170 to 180 steps a minute. "
          "Think light and quick, not long. Finish an easy run with 4 x 30 seconds of fast relaxed "
          "strides, and film yourself side-on once: overstriding is the fault nearly everyone "
          "has.",
          # "form" is a form to fill in and a school form, and a form of words is not a run
          avoid=("fill in", "fill out", "fill", "application", "tax", "school", "sick note",
                 "consent", "form for", "this form", "the form", "printing", "printer", "visa"),
          bias=1),
]

# The words of a game: love and deuce, a knock-on and a lineout, a transfer window and a pit
# stop. Each was asked plainly ("what is a tie break") and got a shrug, or a same-word answer
# from another world (a tie break in tennis was the break at work).
ENTRIES += [
    entry("tennis-love", (("love",), ("in tennis", "tennis", "score", "scoring", "40", "nought",
                                      "mean", "means")),
          "Love is nought in tennis, said to come from the French for an egg. A new game starts "
          "at love-all, and 40-0 is called forty love.",
          bias=2),
    entry("tennis-deuce", (("deuce", "advantage", "tie break", "tiebreak", "tie-break"),
                           ("what", "whats", "mean", "means", "is", "score", "scoring", "how",
                            "work", "tennis", "why", "called")),
          "40-40 is deuce: from there you need two points in a row, and the first of them is "
          "advantage, so a game can go on a long time. At 6-6 in a set a tie-break decides it - "
          "first to seven points, two clear.",
          bias=2,
          # the break in a shift is a different question, and it owns the bare word
          avoid=("work", "shift", "lunch", "job", "boss", "employer", "overtime")),
    entry("snooker-frames", (("snooker",), ("frames", "frame", "how many", "long", "match",
                                            "final")),
          "A frame is one game of snooker, and a match is a set number of them: tour finals are "
          "usually best of 19 frames and the World Championship final is best of 35, played over "
          "two days in four sessions.",
          bias=1),
    # "how many subs can i put on my sandwich" was answered here on "subs" and "how many", so
    # the entry only answers when the line says the game too.
    entry("football-subs", (("football", "soccer", "premier league"),
                            ("subs", "substitutes", "substitution", "substitutions", "bench")),
          "Five substitutions from three stoppage windows in the Premier League and most "
          "competitions, plus a sixth in extra time; it was three until 2020. A bench of nine is "
          "named, so most of the squad gets a game.",
          ask=("football", "soccer", "premier league"),
          bias=1),
    # "how do i get into watching football" and "how do i keep up with the premier league" were
    # both a shrug: the football rows answer the rules (offside, subs, the transfer window) and
    # none of them answers a person who has decided to start watching. The ask is the beginning,
    # so that is what this row keys, and the rules rows keep their own lines.
    entry("start-watching-football",
          (("football", "soccer", "premier league", "the premier league", "champions league",
            "match of the day", "the football"),
           ("get into", "getting into", "start watching", "begin watching", "keep up with",
            "keep up", "follow", "learn about", "understand", "beginner", "beginners",
            "know nothing", "dont know anything", "don't know anything", "new to",
            "where to start", "who should i support", "which team should i support",
            "which team", "how do i watch", "watch football", "watching football",
            "talk about football", "on tv")),
          "Start with one team and one weekly programme rather than the whole sport: pick the club "
          "nearest you, or the one your family and friends already argue about, and watch its "
          "highlights every week - Match of the Day or ten minutes on the club's app. Learn three "
          "things and the rest follows: offside, what a VAR check is stopping play for, and how "
          "the league table works (three points for a win, one for a draw, most points wins). A "
          "local non-league or Sunday game costs a fiver and teaches you more in ninety minutes "
          "than a month of television, and listening to one weekly podcast gives you the names "
          "everyone else already knows.",
          ask=("football", "soccer", "premier league", "watch", "follow", "understand"),
          # playing it, buying for it, betting on it and the other sports are other answers
          avoid=("play", "playing", "played", "boots", "shin pads", "five a side", "5 a side",
                 "tickets", "ticket", "bet", "betting", "odds", "accumulator", "fantasy",
                 "fpl", "fifa", "video game", "cricket", "rugby", "tennis", "golf", "f1",
                 "formula 1", "netball", "hockey", "darts", "kids", "child", "son", "daughter",
                 "nursery", "school")),

    entry("transfer-window", (("transfer window", "transfer windows", "transfer deadline",
                              "deadline day"),
                             ("what", "whats", "mean", "means", "is", "how", "work", "works",
                              "when", "closes", "open", "football")),
          "It is the period when a club can register new players: a long summer window, roughly "
          "June to the start of September, and a short one through January. Outside them nobody "
          "can move, which is why deadline day is frantic.",
          bias=2),
    entry("pit-stop", (("pit stop", "pit stops", "pitstop", "pit lane"),
                       ("what", "whats", "mean", "means", "is", "how", "work", "long", "tyres",
                        "f1", "formula 1")),
          "A pit stop is the stop for fresh tyres: the crew changes all four in about two "
          "seconds, and with the drive down the pit lane at the speed limit it costs roughly 20 "
          "seconds of race time. Most races are one or two stops.",
          bias=2),
    entry("rugby-knock-on", (("knock on", "knock-on", "knocked on", "forward pass"),
                             ("what", "whats", "mean", "means", "is", "rugby", "happens", "why",
                              "rule")),
          "A knock-on is losing the ball forward out of your hands, or it bouncing forward off "
          "your arm: play stops and the other side gets a scrum where it happened. A forward pass "
          "is the same offence thrown instead of dropped.",
          bias=2,
          # a knock on the door is not a rugby offence
          avoid=("door", "doors", "neighbour", "neighbor", "visitor", "caller")),
    entry("rugby-lineout", (("lineout", "line out", "line-out"),
                            ("what", "whats", "mean", "means", "is", "rugby", "how", "work",
                             "rule")),
          "A lineout restarts play after the ball goes into touch: the forwards of both sides "
          "line up in two rows, a hooker throws the ball straight down the middle, and the "
          "jumpers are lifted to catch it. The throwing side usually wins their own ball.",
          bias=2),
    entry("rugby-maul", (("maul", "mauls", "ruck", "rucks"),
                         ("what", "whats", "mean", "means", "is", "rugby", "how", "work",
                          "rule", "difference")),
          "A maul is a ball carrier held up with teammates bound on to him, everyone on their "
          "feet; a ruck is the same idea with the ball on the ground. In both, players must stay "
          "on their feet, join from behind the ball, and the side going forward gets the "
          "advantage.",
          bias=2,
          # "how do i stop a carpet from rucking up" and "the carpet is rucking up" were both the
          # rugby answer: a ruck in a carpet is a room job, not a rule.
          avoid=("carpet", "carpets", "rug", "rugs", "floor", "floors", "flooring", "underlay",
                 "gripper", "grippers", "laminate", "lino", "linoleum", "mat", "mats")),
]

# The other Grand Slams, and the length of an NFL game: the same words, four different sports,
# and a shrug for the one game whose length is asked about on both sides of the Atlantic.
ENTRIES += [
    entry("golf-grand-slam", (("grand slam", "grand slams", "majors", "major"),
                              ("golf", "golfer", "masters", "open championship", "pga")),
          "The four men's majors are the Masters at Augusta in April, the PGA Championship in "
          "May, the US Open in June and the Open Championship in July. Winning all four in one "
          "year is the calendar Grand Slam - only Bobby Jones, in 1930, and Tiger Woods, in 2000 "
          "and 2001 across two years, have come close.",
          bias=3,
          avoid=("tennis", "wimbledon")),
    entry("rugby-grand-slam", (("grand slam", "grand slams", "triple crown"),
                               ("rugby", "six nations", "wales", "ireland", "england", "scotland",
                                "france", "italy")),
          "In the Six Nations a Grand Slam is winning all five of your matches in the same "
          "season, which also brings three bonus points; a Triple Crown is one of the home "
          "nations beating the other three.",
          bias=3,
          avoid=("tennis", "wimbledon", "golf")),
    entry("nfl-length", (("nfl", "american football", "super bowl"),
                         ("how long", "long", "last", "hours", "minutes", "game", "watch")),
          "Four 15-minute quarters, so 60 minutes of play, but the clock stops on every "
          "incomplete pass and the whole game runs about three hours, and longer for the "
          "Super Bowl with its half-time show.",
          bias=2),
]

# "what is a triple crown" alone: the same words in two sports, so answer both rather than guess.
ENTRIES += [
    entry("triple-crown", (("triple crown",), ("what", "whats", "is", "mean", "means", "rugby",
                                              "six nations", "horse", "racing", "win", "won")),
          "In rugby's Six Nations, the Triple Crown goes to whichever of England, Ireland, "
          "Scotland or Wales beats the other three in the same season. In US horse racing it is "
          "winning the Kentucky Derby, the Preakness and the Belmont Stakes in one year.",
          bias=2),
]


# The sport lines that were answered by the word rather than the game. `how do i play squash`
# was the roast, `how do i throw a discus` was the washing machine, and `how do i row properly`
# was two people having a row. Each of these names its own thing - the game, the implement, the
# stroke - so each gets a card keyed on that thing, and the row that shares the word stands down
# for the sport's own words. The two coaching lines (breathing, injuries) and the two numbers
# (how many lengths, a handicap) are here because they had no answer at all.
ENTRIES += [
    entry("squash-the-game",
          (("squash", "squash court", "racquetball"),
           ("play", "playing", "rules", "court", "rak", "racket", "racquet", "game", "beginner",
            "better", "start", "serve", "serve")),
          "Squash is two players in a room, and you win a point only when you serve: hit the ball "
          "above the middle line and below the top line onto the front wall, and let it bounce "
          "once on the floor. If it goes out, hits the tin or bounces twice, the point is over. "
          "Stand near the T in the middle after your shot - whoever holds the middle wins.",
          ask=("how", "what", "whats", "should", "any", "rules"),
          # the vegetable, the drink and the game all share the word
          avoid=("roast", "roasted", "recipe", "cook", "cooking", "oven", "butternut", "bake",
                 "soup", "squash recipe", "cordia", "cordial", "drink", "grow", "growing",
                 "allotment", "plant", "plants", "seed", "seeds"),
          bias=1),
    # The three circle throws share their answer, so one card holds them and picks the implement
    # the line named. A javelin is not one of them: it is thrown from a straight run-up with no
    # circle and no spin, and "how do i throw a javelin" was answered with "hold the discus flat,
    # spin across the circle" word for word.
    entry("discus",
          (("discus", "discus throw", "shot put", "shotput", "hammer throw", "hammer"),
           ("how do i", "throw", "throwing", "technique", "better", "far", "further", "coach",
            "training", "rules")),
          _a_circle_throw,
          ask=("how", "what", "should", "any", "far", "further"),
          avoid=("washing machine", "machine", "cycle", "tumble", "blanket", "blankets",
                 "cushion", "dryer", "towel", "tumble dryer", "load", "nail", "picture",
                 "wall", "thumb", "toe"),
          bias=1),
    entry("javelin",
          (("javelin", "javelin throw", "throw a javelin", "throwing a javelin"),
           ("how do i", "throw", "throwing", "technique", "better", "far", "further", "coach",
            "training", "rules", "what")),
          "A javelin is thrown over the shoulder from a run: a straight run-up of about eight "
          "strides building through the last three, the arm back and high with the point level "
          "by your ear, then the front foot plants and the hips turn before the arm comes "
          "through. Let it go with the tip up and run through past the line, because the throw is "
          "measured where the tip lands. The length comes from the run-up and the hip turn, not "
          "from muscling it.",
          ask=("how", "what", "should", "any", "far", "further"),
          avoid=("washing machine", "machine", "cycle", "phone", "pen", "pencil", "arrow"),
          bias=1),
    entry("googly",
          (("googly", "leg spin", "leg break", "off spin", "off break", "offbreak", "offspin",
            "wrist spin", "finger spin", "what is a googly", "wrong un", "wrongun",
            "bowl a googly", "bowling a googly", "bowl leg spin"),
           ("what", "whats", "is", "mean", "means", "bowl", "bowling", "spin", "bowler",
            "how", "how do i", "work")),
          "Spin is the bowler turning the ball off the pitch: a leg break turns away from a "
          "right-hander, an off break turns in, and a googly is a leg-spinner's ball that turns "
          "the other way - it looks like a leg break out of the hand, but the wrist rolls the "
          "other way. Batsmen read it off the pitch rather than the hand, because the wrist gives "
          "it away late.",
          ask=("what", "whats", "what's", "is", "mean", "means", "explain", "define",
               "how", "how do i", "bowl", "bowling"),
          bias=1),
    entry("running-injury",
          (("injury", "injuries", "get injured", "stay injury free", "injured", "sore knees",
            "shin splints", "overtraining"),
           ("running", "run", "jogging", "jog", "training", "avoid", "prevent", "marathon",
            "half marathon", "10k", "5k")),
          "Nearly all running injuries come from doing more, sooner than the body can repair: add "
          "no more than about 10 per cent to your weekly distance, keep every second run easy, "
          "and take a rest day after a long one. Two short strength sessions a week - calf raises, "
          "squats, a single-leg balance - and shoes that are not worn through do the rest. Sharp "
          "pain that changes how you run means stop.",
          ask=("how", "what", "any", "prevent", "avoid", "should"),
          avoid=("already", "i hurt", "i have hurt", "it hurts", "he hurt", "she hurt", "pain now",
                 "swollen", "bleeding", "sprain", "broke"),
          bias=1),
    entry("running-breathing",
          (("breathe", "breathing", "out of breath", "breathless", "breath"),
           ("running", "run", "jogging", "jog", "while i run", "when i run", "long runs",
            "marathon", "5k", "10k")),
          "Breathe in through the nose and mouth together, into the belly rather than the chest, "
          "and let the rhythm follow your steps - two in, two out, then three and three when the "
          "pace is easy. If you can only speak a few words at a time, slow down: most breathless "
          "running is a pace problem, not a lung problem. Cold air is fine, just warm up first.",
          ask=("how", "what", "should", "any"),
          avoid=("asthma", "inhaler", "wheeze", "wheezing", "cough", "coughing", "covid",
                 "chest pain", "can't breathe", "cant breathe", "cannot breathe", "choking"),
          bias=1),
    entry("golf-handicap",
          (("handicap", "handicaps", "handicap index", "playing handicap"),
           ("golf", "work", "works", "what is", "how does", "lower", "get", "calculate",
            "explain")),
          "A handicap is how many shots you get: it is roughly your best scores, averaged, "
          "against the course rating, so a 20-handicapper gets a shot on the 18 hardest holes and "
          "plays the course as a scratch golfer would. It goes down when you score better than "
          "your handicap - you need a few rounds, not one - and it is why two players of "
          "different ability can have a fair match.",
          ask=("what", "whats", "what's", "is", "how", "explain", "mean", "means", "does"),
          bias=1),
    entry("triathlon-training",
          (("triathlon", "triathlons", "ironman", "sprint triathlon", "olympiad distance"),
           ("train", "training", "how do i", "start", "beginner", "first", "prepare", "ready",
            "plan")),
          "Train the bike mostly, because it is the longest leg and the one you can do most of "
          "without damage: two rides a week, one long and one with short hard efforts, plus two "
          "swims of 20 to 30 minutes and two short runs. Practise the changeovers - a brick "
          "session of bike then run - because the first five minutes off the bike feel strange. "
          "A sprint distance (750m, 20k, 5k) is a good first race.",
          ask=("how", "what", "should", "any", "where"),
          avoid=("watch", "watching", "on tv", "results", "winner", "world championship",
                 "hawaii", "kona", "price", "cost", "bike to buy", "wetsuit"),
          bias=1),
    entry("table-tennis",
          (("table tennis", "ping pong", "pingpong"),
           ("play", "playing", "rules", "how do i", "better", "score", "scoring", "serve",
            "bat", "beginner", "start")),
          "Games go to 11 and you serve every two points, so a game turns faster than it looks: "
          "serve short and low, keep the ball on the table rather than hitting it hard, and step "
          "back only when you have to. The basics win club games - a heavy spin serve, a steady "
          "block, and returning the serve rather than trying to win the point with it.",
          ask=("how", "what", "whats", "rules", "should", "any"),
          # "table" is the row's own game, so it cannot fence anything: a dining table, a
          # tablecloth and a table top are fenced by name instead.
          avoid=("dining table", "tablecloth", "table top", "table runner", "furniture",
                 "buy", "price", "cheap", "restaurant",
                 # cleaning and storing the table is not the game: "how do i clean a table
                 # tennis table" was this card instead of the hard-surface answer
                 "clean", "cleaning", "wipe", "dust", "stain", "storage", "store", "storing",
                 "fold", "folding", "bat case", "net"),
          bias=1),
]

# Four questions with no card, all found by typing them at `main`: what a shot is called, what a
# position does, how the club is held, and how to watch a tournament. Each names a word the rest of
# the registry uses for something else, so each carries the fence that keeps it off that other world.
ENTRIES += [
    entry("badminton-shots",
          (("smash", "smashing", "jump smash", "drop shot", "drop shots", "net shot", "net shots",
            "overhead clear", "deception"),
           ("badminton", "shuttle", "shuttlecock", "racket", "racquet", "court")),
          "A smash is hit steeply down from above your head: get behind the shuttle, meet it high "
          "and in front, and snap the wrist through it as you step forward. The drop shot and the "
          "net shot are the same action with a slower swing, the first landing just over the net "
          "and the second taken close in so the shuttle tumbles over. A smash is the last shot to "
          "learn: a weak one hands your opponent the attack.",
          ask=("what", "whats", "what's", "how", "explain", "mean", "means"),
          # a smash is a window, a car, a plate of potatoes and a tennis shot
          avoid=("window", "windows", "windscreen", "car", "cars", "crash", "crashing",
                 "potato", "potatoes", "pumpkin", "avocado", "burger", "glass", "tennis",
                 "squash", "hit and run", "smash hit", "boxing", "wrestling"),
          bias=1),
    # netball-basics held "positions" and answered it with the three-second rule, which names no
    # position at all: "what do the positions in netball do" wants the seven names and who shoots.
    entry("netball-positions",
          # the netball-only position names count in both halves, so "what does the goal shooter
          # do" is the card without the word netball in the line at all. Goal keeper is left out:
          # it is a football position as well, and that question is not this card's.
          (("positions", "position", "roles", "role", "each player", "players do", "who can shoot",
            "goal shooter", "goal attack", "wing attack", "wing defence", "goal defence",
            "shooting circle"),
           ("netball", "netball court", "shooting circle", "goal shooter", "goal attack",
            "wing attack", "wing defence", "goal defence")),
          "Only the two shooters can score: goal shooter stays in the attacking third and goal "
          "attack works the circle edge with her, and the two defenders - goal keeper and goal "
          "defence - are the mirror of them at the other end. Wing attack and wing defence carry "
          "the ball through the middle thirds and centre takes the pass-offs, so the positions "
          "are really about which thirds you may enter.",
          ask=("what", "whats", "which", "who", "how", "explain", "does", "do"),
          avoid=("how long", "how many quarters", "minutes", "substitute", "substitutes",
                 "injury", "injured", "swap", "roll", "rolling"),
          bias=2),
    entry("golf-grip",
          (("grip", "grips", "hold the club", "hold my club", "hold a club", "holding the club",
            "how do i hold", "grip the club", "interlocking", "overlapping", "baseball grip"),
           ("golf", "club", "clubs", "driver", "iron", "irons", "putter", "tee", "shot")),
          "Hold it in the fingers of your left hand, not the palm, with the handle running from "
          "the base of the little finger to the knuckle of the index finger, then lay the right "
          "hand over the top so both Vs point at your right shoulder. Squeeze about three out of "
          "ten: a tight grip stops the wrists hinging, which is where the distance comes from.",
          ask=("how", "what", "which", "should", "any", "explain"),
          # a grip is also a badminton grip, a tyre, a phone case and a strength word
          avoid=("badminton", "tennis", "squash", "racket", "racquet", "tyre", "tyres", "tire",
                 "wheel", "phone", "camera", "towel", "strength", "grip strength", "bar",
                 "steering", "pen", "pencil", "boot", "boots", "shoes", "floor", "stairs",
                 "handrail", "rail", "train", "bus"),
          bias=2),
    # "how do i watch the world cup" was the get-into-a-sport card, which tells you to pick one
    # team and one weekly programme - fine advice for a season, no use for a tournament next month.
    entry("watch-a-tournament",
          (("world cup", "the world cup", "euros", "euro 2028", "european championship",
            "olympics", "olympic games", "world championship", "world championships",
            "commonwealth games", "tournament", "cup final"),
           ("watch", "watching", "on tv", "tv", "television", "stream", "streaming", "channel",
            "where can i", "how do i watch", "tickets", "kick off", "kick-off", "what time")),
          "In the UK the World Cup, the Euros and the Olympics are free to air - BBC and ITV share "
          "the football, and the BBC carries the Olympics with a stream per sport, so pick the "
          "sport rather than hunting the channel. Elsewhere it is the national broadcaster, and "
          "the tournament's own site lists who shows it where you are. Group games sit at fixed "
          "times, so check the kick-off before you plan the evening.",
          ask=("how", "where", "what", "which", "can", "should"),
          # who won is the winners card's question, and a ticket price is a shopping question
          avoid=("won", "win", "winner", "winners", "who won", "host", "hosted", "qualify",
                 "qualified", "price", "prices", "cost", "how much", "rugby", "cricket",
                 "darts", "snooker", "results", "highlights", "when did"),
          bias=1),

]
# A start time is not a shop's opening hours. "what time do marathons start", "what time does the
# match start" and "what time do the fireworks start" all reached the shop-hours note in
# bot/compose/fallback.py ("No live opening times here. Ring them or check the branch page on a map
# app"), because "what time do" is one of its shapes and no row anywhere named a start. The bot
# cannot see a schedule, but a person with a race on Sunday needs more than a shrug: the usual
# window, and the bit of the timetable people get wrong.
_RACE_WORDS = ("marathon", "marathons", "half marathon", "10k", "5k", "parkrun", "race",
               "races", "ultra", "triathlon", "cross country", "fun run")
_MATCH_WORDS = ("match", "matches", "kick off", "kick-off", "kickoff", "game", "football",
                "rugby", "cricket", "netball", "hockey", "fixture", "derby")
# "show" is left out on purpose: "what time does the show start" is as often a TV programme,
# and a gig's door time is no answer to a schedule on a screen.
_GIG_WORDS = ("concert", "concerts", "gig", "gigs", "festival", "glastonbury", "gig ")
_FIREWORK_WORDS = ("fireworks", "firework", "bonfire", "display")

_EVENT_START = {
    "race": ("Mass races start early and in waves: most city marathons and half marathons go off "
             "between 8 and 10 in the morning, a 10k usually between 9 and 10, and a parkrun at 9 "
             "on a Saturday. Your race email has your own wave and the time the pens close, which "
             "is the one people miss - and the earlier wave is often the one with the friendlier "
             "cut-offs."),
    "match": ("Most Saturday football kicks off at 3pm and Sunday games at 2pm or 4.30pm, but a "
              "televised game moves by hours, so the club's or the ticket page's fixture list is "
              "the only reliable one. Turn up an hour before for a big ground, because the queues "
              "at the turnstiles are what make people late."),
    "gig": ("Doors for a gig usually open an hour before the support act, and the headline act "
            "comes on about two hours after doors; most venues have a curfew at half past ten or "
            "eleven, so that is roughly when it ends. A big venue also has a bag check, so add "
            "twenty minutes. The venue's own page or your ticket email gives the door time, and "
            "check the last train home before the encore."),
    "fireworks": ("A firework display goes up after dark, so most are between 7 and 9 in the "
                  "evening in November and later in midsummer, and the organiser's page gives the "
                  "exact time because it depends on sunset. Wrap up warm and stand upwind, and get "
                  "there early if you are driving, since car parks empty slowly."),
}

_EVENT_START_GENERIC = ("I can't see the schedule from here, so the organiser's page or your "
                        "confirmation email is the one to trust. Ask about the gate or start pen "
                        "closing time as well, because that is usually earlier than the start, "
                        "and plan to be there half an hour before it.")


def _event_start(memory, understood):
    """The window an event usually starts in, picked by the kind of event the line names."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    found = []
    for kind, words in (("race", _RACE_WORDS), ("match", _MATCH_WORDS),
                        ("gig", _GIG_WORDS), ("fireworks", _FIREWORK_WORDS)):
        if any(word in said for word in words):
            found.append(kind)
    # "the marathon match"? two kinds in one line is a mix-up, and the generic line is honest
    if len(found) == 1:
        return _EVENT_START[found[0]]
    if found:
        return _EVENT_START_GENERIC
    return None


ENTRIES += [
    entry("event-start",
          (("what time", "when do", "when does", "when is", "start time", "what time is",
            "kick off", "kick-off", "kickoff", "doors"),
           ("start", "starts", "starting", "kick off", "kick-off", "kickoff", "doors open",
            "begin", "begins", "go off", "goes off", "what time", "when",
            # a schedule answer needs the event named, so these are the nouns it may be
            "marathon", "marathons", "half marathon", "10k", "5k", "parkrun", "race", "races",
            "match", "matches", "game", "football", "rugby", "cricket", "netball", "hockey",
            "concert", "concerts", "gig", "gigs", "festival", "fireworks", "firework",
            "bonfire", "display", "triathlon", "ultra", "fun run", "fixture")),
          _event_start,
          # A shop's opening hours, a pill and a ferry are not a race: those keep their own rows.
          # "what time do you close" and "what time does the pharmacy open" are the hours note's.
          # a parkrun line already has a card that names its start ("every Saturday at 9am"), and
          # the generic race window is a worse answer than that one.
          avoid=("parkrun", "park run", "pharmacy", "chemist", "shop", "supermarket", "bank",
                 "post office", "pub",
                 # A house sale is not a fixture. "when will we exchange" and "when do we get the
                 # keys" reached here and were answered with "No date from you on that one" - the
                 # sport row asking for a date, because "when do" is its first group and a bare
                 # "when" is in its second. The sale has its own row; these words stand this one
                 # down so the sale's row can take them.
                 "contracts", "contract", "completion", "complete", "exchange", "keys", "key",
                 "house", "flat", "mortgage", "solicitor", "conveyancer", "sale", "seller",
                 "buyer", "landlord", "tenancy",
                 "restaurant", "open", "opens", "opening", "close", "closes", "closing", "shut",
                 "shuts", "pill", "pills", "tablet", "tablets", "dose", "insulin", "ferry",
                 "flight", "train", "bus", "sunrise", "sunset", "shift", "appointment",
                 "meeting", "interview", "school", "class", "lesson", "service", "opening times"),
          ask=("start", "starts", "starting", "kick off", "kick-off", "kickoff", "doors",
               "begin", "begins", "go off", "goes off", "what time", "when")),
]


# ---- the strike, the corner and the whistle ------------------------------------------------
#
# The ball sports were asked as skills and the deck answered the theory. "how do i take a penalty"
# reached the shootout rules - five players, sudden death, one foot on the line - which is where the
# rules card belongs and no use to someone standing over the ball. "how do i take a corner", "how do
# i volley a football" and "how do i do a header" reached nothing, and "how do i juggle a football"
# reached the card about having too much on. The whistle had the same shape: a referee's pay got the
# job-reference card, because a referee is also the word for the person who gives you one.

_BALL_ASK = ("how", "what", "should", "can", "help", "tips", "technique", "better", "practice",
             "practise")

ENTRIES += [
    entry("penalty-kick",
          (("penalty", "penalties", "penalty kick", "spot kick", "twelve yards"),
           ("take", "taking", "score", "scoring", "shoot", "shooting", "strike", "hit", "shootout",
            "in a match", "into the corner", "side foot", "laces", "practice", "practise",
            "technique", "nervous", "missed", "kept missing")),
          "Pick your corner before the run starts, keep it low and side-foot it inside the post, and "
          "do not change your mind on the last step: a firm, repeatable penalty beats a clever one. "
          "Practise ten to the same corner at the end of training so the run, the plant foot and the "
          "strike are one habit.",
          # an avoid word is read loosely, so "refereeing" here also caught "referee" on the job
          # reference card: the whistle words are the phrases, not the bare stem
          avoid=("shootout", "sudden death", "how many", "who takes", "order", "world cup",
                 "keeper has to", "the rules", "how does", "the line"),
          bias=2),
    entry("save-a-penalty",
          (("penalty", "penalties", "spot kick", "twelve yards"),
           ("save", "saving", "stop", "stopping", "keeper", "goalkeeper", "in goal", "dive",
            "diving", "guess", "read the taker")),
          "Stay tall and wait: most takers decide their corner early, so watch the standing foot and "
          "the hips rather than the ball, and dive late with a strong hand. Keep your weight on the "
          "balls of your feet so the first step can go either way.",
          avoid=("shootout", "sudden death", "how many", "who takes", "how does", "the rules"),
          bias=2),
    entry("corner-kick",
          (("corner", "corners", "corner kick", "corner flag"),
           ("take", "taking", "kick", "kicking", "swing", "inswing", "outswing", "cross",
            "delivery", "head it", "practice", "practise", "where do i aim")),
          "Aim for the six-yard box rather than the penalty spot: drive it inswinging and low with "
          "the inside of the foot, and send two players across the near post so the keeper has to "
          "decide. Practise one corner ten times - the ball you can repeat beats the clever one.",
          avoid=("shop", "street", "room", "garden", "table", "bed", "photos", "picture",
                 "cupboard", "car", "parking", "hockey", "rugby", "gaelic", "netball", "cricket",
                 "corner shop", "corner of the room"),
          bias=2),
    entry("volley-a-football",
          # "first time" is the first-visit card's phrase, not a volley: the shot is the
          # volleyed ball
          (("volley", "volleys", "half volley", "on the volley", "volley it"),
           ("football", "ball", "soccer", "practice", "practise", "strike", "technique", "how")),
          "Watch the ball onto your foot instead of swinging at it: get side-on, keep your knee over "
          "the ball and your toe down, and strike through the middle so it stays low. Start with a "
          "ball tossed up and volleyed into a wall, then ask a partner for a low pass to hit first "
          "time.",
          # the ground-strike row also holds "volley" in its key, so this one has to outrank it
          # for "how do i volley a football": its own words are the more specific answer
          bias=3),
    entry("head-a-football",
          (("header", "headers", "head it", "heading a ball", "head a football", "head the ball",
            "headed goal", "a header", "a header in football", "do a header"),
           ("football", "ball", "soccer", "practice", "practise", "technique",
            "clear it", "score", "hurts", "hurt", "better", "properly", "do it", "how")),
          "Head the ball with your forehead, not the top of your head: attack it, keep your eyes "
          "open, keep your neck firm and head it back where it came from rather than up in the air. "
          "For a clearance, jump early and put your shoulders through it, and learn the timing with "
          "a soft ball so the head does not do the flinching.",
          # the key is read loosely, so a bare "heading" also caught "head" in a nail, a garlic
          # bulb, a headache and a hair wash: the ball phrases are the key and the rest is fenced
          avoid=("garlic", "nail", "head hurts", "headache", "headaches", "head of hair",
                 "shampoo", "headboard", "bald", "head injury", "concussion", "helmet",
                 "pillow", "dizzy", "head cold", "headlights", "head start",
                 # a header is also a line at the top of a page or an email
                 "email", "document", "word", "spreadsheet", "page", "logo", "css", "http",
                 "letterhead", "cv", "template", "website",
                 # and a head is the top of a queue, a school, an office or a pint
                 "head office", "head teacher", "head of", "ahead", "overhead", "head to toe",
                 "head and shoulders", "shower", "beer", "pint", "lettuce", "cabbage",
                 "broccoli", "cauliflower", "bed", "mattress", "comb", "haircut"),
          bias=1),
    entry("juggle-a-football",
          (("juggle", "juggling", "keepy uppies", "keepie uppies", "keep ups", "keepie uppies",
            "football tricks"),
           ("football", "ball", "soccer", "how", "learn", "practice", "practise", "better",
            "without dropping")),
          "Use the laces, keep the knee soft and let the ball drop to your foot instead of reaching "
          "up for it: drop the ball, touch it once and catch it, then add one touch a day. Ten "
          "minutes a day for a fortnight beats an hour once.",
          bias=1),
    entry("strike-a-ball-with-the-laces",
          (("laces", "laces of the boot", "instep", "top of the boot"),
           ("football", "ball", "soccer", "kick", "kicking", "strike", "shoot", "shooting",
            "harder", "far", "how")),
          "Strike it with the laces, not the toes: plant your standing foot beside the ball, point "
          "the toe down, and follow through towards the target so the ball stays low. The power "
          "comes from the follow-through and a locked ankle, not from swinging harder.",
          # "how do i tie my laces" and a loose lace are the knot's question
          avoid=("tie my laces", "tie laces", "tying laces", "coming undone", "untied"),
          bias=2),
    entry("match-tickets",
          (("ticket", "tickets", "season ticket", "away end", "home end"),
           ("match", "matches", "football", "soccer", "game", "stadium", "club", "fixture",
            "fixtures", "premiership", "league", "cup final", "rugby", "cricket")),
          "Go through the club's own site rather than a reseller: home tickets usually need a "
          "membership or a ballot first, and the club's official resale page is the only safe way "
          "to get a sold-out one at face value. Buy two or three weeks ahead, before the ballot "
          "closes, and check the kick-off time again the day before because it moves for television.",
          ask=("how", "where", "when", "can", "should", "what"),
          avoid=("concert", "gig", "festival", "train", "rail", "flight", "plane", "cinema",
                 "parking", "speeding", "fine", "parking fine", "expenses", "claim back"),
          bias=2),
    entry("referee-a-football-match",
          (("referee", "refereeing", "ref", "linesman", "assistant referee", "run the line"),
           ("become", "course", "qualification", "qualify", "qualified", "start", "train",
            "training", "match", "football", "game", "whistle", "how", "get into")),
          "Take the FA's free online Laws of the Game course first, then book the basic referee "
          "course through your county FA - about 20 hours, a theory exam and a practical run-out - "
          "and join a local league. Ask for a mentor for your first games, arrive an hour early and "
          "blow the whistle loud: players test a quiet one.",
          avoid=("paid", "pay", "earn", "salary", "reference", "feed the referee", "var",
                 "how many points",
                 # "how do i ask someone to be my referee" is a job reference with the same word,
                 # and the bare "referee" plus "how" was enough for two points and this card
                 "be my referee", "my referee", "referee for my", "referee for a job",
                 "job reference", "for a job application", "for my job application"),
          bias=1),
    entry("referee-pay",
          (("referee", "referees", "ref", "whistle", "linesman", "assistant referee"),
           ("pay", "paid", "money", "earn", "earnings", "salary", "wage", "wages", "how much",
            "get paid", "per match", "a game")),
          "Read the fee off the league's own handbook rather than a round number: grassroots referees "
          "in England are paid a match fee by the competition - around 30 to 45 pounds for an adult "
          "Saturday game - plus mileage, and the level above is a good deal more. Ask the league "
          "secretary what the fee and the travel rate are before your first appointment.",
          avoid=("job", "reference", "references", "employer", "cv", "application"),
          bias=2),

    # A kit question for a wet match: the weather words keep it off the boots-buying row and the
    # arrival-times row, and the guard needs all three parts (a sport, weather, a wear verb).
    entry("kit-for-a-wet-match",
          (_WET_MATCH_SPORT, _WET_MATCH_WEAR + _WET_MATCH_WEATHER),
          _kit_for_a_wet_match,
          # bias=3 because "what should i take to my sons rugby match, its freezing" tied with
          # family.py's child-too-cold row (bias=2, keyed "son" + "freezing"), which answers about
          # a baby's neck. That row's question is a child's body at night; this line's "freezing"
          # is the weather at a match. family.py is over the file cap so it cannot be fenced here,
          # and the guard above is what keeps this row narrow.
          ask=_WET_MATCH_WEAR, guard=_a_wet_match, bias=3),
]
