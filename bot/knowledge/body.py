"""A part of the body that hurts: the everyday ache people type as "my <part> hurts".

People do not ask "what is a sore back", they type the complaint, so the key here is the
part plus the word for hurting, never the complaint on its own. Each region carries the
one thing that actually helps it, because "rest it and take a painkiller" is the same
sentence for a back and an ankle and would read as a shrug.

The region is data: one line per part in REGIONS, the shared words for hurting in HURT,
and the parts this table must not answer in AVOID, so a sore chest ("ring 999"), a sore
throat, a sore tooth and a stomach ache keep the answers that already handle them.
"""

import re
import string

from .lookup import ASK_ABOUT, RING_AS_A_CALL, entry
from ..understanding.kinds import OTHER_PEOPLE, PERSON_NOUNS

# The words a line uses for a temperature at all. The kitchen's thermometer, the oven, the room
# and the wash share every one of them, which is why the reading, not the word, decides.
TEMPERATURE_WORDS = frozenset((
    "temperature", "temperatures", "temp", "temps", "fever", "feverish", "fevered"))
# "we all have temperatures" is the same household fever in the plural, and a bare "i" is not
# evidence of anything: every question has one in it ("what temperature should i wash towels at").
WE_OUR_OURS = frozenset(("we", "us", "our", "ours"))
# "my temp is 39" is a fever the reading does not recognise, because `temp` on its own is not in
# its words for a body (`my temperature is 39` is, and that is the long form of the same line).
# The possessive directly in front is what makes it the speaker's own, and it is read as a pair
# so that "my oven temperature" - a thing's dial, with a word in between - is not swept in.
POSSESSIVE_OF_A_PERSON = frozenset(("my", "his", "her", "their", "our", "your"))
# What follows the word when it is a thing's reading and not a person's: "my temperature probe
# reads wrong" is a cook's question about a probe, and the reading still calls the number the
# speaker's own (`body` is `temperature` for it), so the word after it is what settles the line.
# A `reading` is not in here on purpose: "my temperature reading is 39" is a fever.
THING_AFTER_THE_WORD = frozenset((
    "probe", "probes", "thermometer", "thermometers", "gauge", "gauges", "gage", "gages",
    "sensor", "sensors", "dial", "dials", "knob", "knobs", "setting", "settings",
    "control", "controls", "thermostat", "thermostats", "stat"))


# A nail is a piece of metal as often as it is a fingernail. The nail rows in the health and
# routines domains key `nail` with the words of a how-to, so "how do i nail two bits of wood
# together" was answered "keep them short and filed, because a ragged edge is what a tooth
# finds", and "how do i put a nail in the wall" got the toenail-cutting rules. The workshop
# nouns below are what separate the two readings: nobody hammers a fingernail into a joist.
_WORKSHOP_NOUNS = (
    "wood", "wooden", "plank", "planks", "planking", "joist", "joists", "batten", "battens",
    "floorboard", "floorboards", "skirting", "moulding", "molding", "fence", "fencing", "gate",
    "shed", "decking", "worktop", "shelf", "shelves", "shelving", "cabinet", "wardrobe",
    "wall", "walls", "brick", "bricks", "plasterboard", "stud wall",
    # the words a fixing is asked about with, not only the words the fixing is done in: a shelf
    # on a plasterboard wall, a mirror over a fireplace, a bracket on masonry. "what nails for a
    # mirror" is the same metal nail as "how do i put a nail in the wall", and without these the
    # fungal-nail card took it.
    "stud", "studs", "mirror", "mirrors", "bracket", "brackets", "picture", "pictures",
    "concrete", "masonry", "tile", "tiles", "block wall", "stone wall", "curtain rail",
    "curtain pole", "anchor", "anchors", "hollow wall", "cavity wall",
    "picture hook",
    "picture hooks", "picture frame", "hanging a picture", "hang a picture", "hang the picture",
    "hammer", "hammers", "hammering", "drill", "drills", "drilling", "screw", "screws",
    "screwed", "screwing", "rawlplug", "rawlplugs", "wall plug", "wall plugs", "carpentry",
    "diy", "doorframe", "door frame",
    # a nail through a tyre is the same piece of metal, and "how do i get a nail out of a tyre"
    # was reaching the nail-biting and nail-growth rows before it reached the puncture row
    "tyre", "tyres", "tire", "tires", "wheel", "wheels", "puncture", "punctured",
)
_WORKSHOP = re.compile(r"\b(?:" + "|".join(re.escape(word) for word in _WORKSHOP_NOUNS) + r")\b")


def _the_nail_is_a_persons(understood):
    """False when the nail in the line is a piece of metal, not one on a person.

    Used as an entry `guard` on the rows that treat a nail as something to cut, bite or cure:
    those rows read a how-to ("how do i ... nail ...") as a question about the habit or the
    trimming, and the workshop nouns in the line are the reading that says otherwise. A nail
    that was hit is not affected - that row is about the injury, not the nail.
    """
    reading = understood if isinstance(understood, dict) else {}
    said = str(reading.get("clean") or "").lower()
    if not said:
        words = reading.get("words") or ()
        said = " ".join(str(word) for word in words).lower()
    if "nail" not in said:
        return True
    return not _WORKSHOP.search(said)


def _the_part_is_a_persons(understood):
    """False when the body word in the line belongs to a thing, not to the person.

    A chair, a table, a shoe and a sofa have legs, backs and heels too. The reading already
    knows which noun owns the part (`_a_thing_owns_the_part`), so every row whose key is a
    part plus a state - a sore back, dry skin, a crack in the skin - stands aside when the
    owner is a thing, and the repair answer for that thing gets the line instead. The test
    is used as an entry `guard`, so it runs on every line and reads the same reading every
    row does.
    """
    return not _a_thing_owns_the_part(understood)


def the_body_is_the_persons(understood):
    """False when the body the line names is somebody else's.

    "my dad is 70" then "hes got a bad hip" is one person's trouble told over two turns, and the
    carer's line ("Is it worse at any time of day, or about the same all the time?") is the right
    one for it. The reading already knows whose the state is, the way the composer's carer pool
    does, so a row of the person's own advice stands aside when `state_owner` says "other".

    A carer keeps talking about the other person after the turn that said so, and that turn has no
    owner of its own: "my mum is 80" / "shes got a bad knee" / "she says its the weather" got the
    mum's knee answered with the drill for the asker's own. Nobody says "she" about their own
    body, so a third person with no first person on the line is somebody else's too.
    """
    if str((understood or {}).get("state_owner") or "") == "other":
        return False
    words = set((understood or {}).get("words") or ())
    if words & _THE_PERSONS_OWN_WORDS:
        return True
    return not (words & _SOMEONE_ELSE)


# A part somebody cannot use at all is not one to train, and the region row already ends its
# advice with "get it looked at if ... you cannot put your weight on it": "i have a bad knee and i
# cant walk on it" got the sit-to-stand drill, which is the wrong answer for a knee in that state.
# The words are read off the line itself rather than an avoid list, because the reading splits
# "cant" into "can" and "not" and an avoid phrase never sees it whole.
_CANNOT_USE_IT = re.compile(
    r"\b(?:can'?t|can ?not|couldn'?t|could ?not|unable to|not able to)\s+"
    r"(?:walk|stand|put|bear|weight|move|straighten|bend|use|lift|raise|reach)\b"
    r"|\b(?:put|bear)\s+(?:my\s+)?weight\b"
    r"|\b(?:gave|gives|giving) way\b")


def the_part_that_keeps_grumbling(understood):
    """The person's own part, and one they can still use: the standing-condition rows' guard."""
    return the_body_is_the_persons(understood) and not _CANNOT_USE_IT.search(
        str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower())


# The words that make a body the speaker's own, and the ones that make it somebody else's. Both
# are read only when the line's own owner is unreadable, so "hes got a bad hip what can i do" is
# still the carer's line the reading named rather than the "i" in it.
_THE_PERSONS_OWN_WORDS = frozenset(("i", "im", "i'm", "me", "my", "mine", "myself", "ive",
                                    "i've"))
_SOMEONE_ELSE = frozenset(("he", "hes", "he's", "she", "shes", "she's", "him", "her", "his",
                           "hers", "they", "theirs", "their", "them"))
# How far along someone is, said as a figure and nothing else: "im 30 weeks and my ankle swelled
# up suddenly on one side" names no pregnancy word at all, so the pregnancy row never fired and
# the line was answered with the sprain card - ice it, rest it, six weeks. A figure in weeks is
# exactly how a pregnant person dates themselves, and it counts for this row alone: the shape is
# one signal, the same weight as a key word, so the swelling still has to be in the line.
# The figure has to be how the person dates themselves - "im 30 weeks", "30 weeks gone", "30 weeks
# pregnant" - and not any week count in a line: "i sprained my ankle 3 weeks ago", "ten weeks
# before a marathon" and "im at 2 weeks of a running plan" carry a figure in weeks and are not a
# pregnancy.
_WEEKS_ALONG = re.compile(
    r"\b(?:im|i'?m|i am|am)\s+(?:about\s+|nearly\s+|almost\s+|just\s+|only\s+)?"
    r"\d{1,2}\s*(?:weeks?|wks?)\b"
    r"|\b\d{1,2}\s*(?:weeks?|wks?)\s+(?:pregnant|gone|along|in)\b"
    r"|\bweeks (?:gone|along)\b")


_SWELLING = re.compile(r"\b(?:swollen|swelling|swelled|swell|swells|puffy|puffiness"
                       r"|water retention|retaining water|fluid)\b")


_PREGNANCY_WORDS = ("pregnant", "pregnancy", "expecting", "weeks pregnant", "weeks gone",
                    "trimester", "my bump", "having a baby", "midwife", "due in", "due date")


def _names_a_pregnancy(understood):
    """True when the line says, in words, that someone is pregnant.

    A key group only nudges the score, it does not have to be there: without this the swelling
    row answered every swelling with a part in it, and "my feet swell when im on them all day"
    got the pregnancy answer.
    """
    reading = understood if isinstance(understood, dict) else {}
    line = " ".join(str(reading.get("clean") or reading.get("text") or "").lower().split())
    return any(word in line for word in _PREGNANCY_WORDS)


def _dates_a_pregnancy_in_weeks(understood):
    """True when the line dates a pregnancy in weeks and is about swelling.

    Used as a `guard`, because a shape only nudges the score: without this the row answered
    "my feet swell when im on them all day", which says no dates at all.
    """
    reading = understood if isinstance(understood, dict) else {}
    line = " ".join(str(reading.get("clean") or reading.get("text") or "").lower().split())
    return _a_figure_in_weeks(line)


def _a_figure_in_weeks(words):
    """A week figure that dates a pregnancy, on a line that is about swelling.

    The swelling has to be there too: "im 20 weeks and my feet hurt when i run" says how far
    along it is and names a part, and the running answer is the one it wants.
    """
    line = (words or "").lower()
    return bool(_WEEKS_ALONG.search(line)) and bool(_SWELLING.search(line))


# The swelling answer, its words and its parts, named so one other row can say the same thing:
# a row keyed on the words dates a pregnancy ("im 30 weeks"), and a second row keyed on the
# pregnancy words answers the lines that say it in words ("im pregnant and my ankles are puffy").
_PREGNANCY_SWELLING = ("swollen", "swelling", "swelled", "swell up", "swells", "swell",
                       "water retention", "retaining water")
_PREGNANCY_SWELLING_PARTS = ("ankles", "ankle", "feet", "foot", "legs", "leg", "toes", "toe",
                             "calves", "calf", "hands", "hand", "fingers", "finger")
_PREGNANCY_SWELLING_AVOID = (
    "sprain", "sprained", "twisted", "broke", "broken", "fell", "fall",
    "bandage", "crutches", "ibuprofen", "paracetamol", "painkiller", "painkillers",
    "overdose", "took too much", "allergic", "dog", "cat",
    # "my ankles are fine" and "no swelling" are not a question about swelling
    "are fine", "is fine", "not swollen", "no swelling", "isnt swollen",
    "arent swollen", "no swelling at all", "nothing swollen",
    # "my ankles are swollen at night, im not pregnant" is the pooling answer
    "not pregnant", "isnt pregnant", "no longer pregnant",
    "not expecting", "not been pregnant")

_PREGNANCY_SWELLING_REPLY = (
    "Swollen feet and ankles are ordinary in the last months: the extra blood and the weight "
    "of the bump slow the fluid back up your legs. Put your feet up above hip height for "
    "twenty minutes a few times a day, keep walking, wear the support tights, and drink "
    "normally rather than less. Ring your midwife the same day if it comes on over a day or "
    "two, if one ankle or one leg swells on its own, if a leg is hot or sore, or if you have "
    "a bad headache, blurry vision or swelling in your face or hands.")



def a_persons_temperature(understood):
    """True when the reading says the temperature in the line is somebody's own.

    The one word "temperature" is a kitchen, an oven, a room and a wash as well as a fever,
    and the kitchen row that teaches the meat probe is keyed on it: "my temperature is 39,
    what should i do" and "i have a temperature of 38 what should i do" were both answered
    with "Push the probe into the thickest part, away from bone, fat and the tin". The reading
    has already settled which the line is (`body` is `temperature` only when the illness is the
    speaker's own), so the rows about a thermometer in a drawer stand aside for it: this is
    used as their `guard`, the same way `the_stomach_is_what_it_is_about` is.

    Somebody else's fever reads `body` empty, because the engine keeps that key for the
    speaker, and "she has a temperature of 39 what should i do" was the meat probe too. A
    person named beside the word makes it somebody's own either way, and the words for a
    person are the engine's own (`kinds.OTHER_PEOPLE`), never a list of names kept here.
    """
    if not isinstance(understood, dict):
        return False
    words = [str(word).lower().strip(string.punctuation)
             for word in (understood.get("words") or ())]
    # "my temperature probe reads wrong" is a probe that reads wrong, not a fever, and the
    # reading calls that number the speaker's own: the word right after it says which it is.
    if any(one in TEMPERATURE_WORDS and other in THING_AFTER_THE_WORD
           for one, other in zip(words, words[1:])):
        return False
    if understood.get("body") == "temperature":
        return True
    if not any(word in TEMPERATURE_WORDS for word in words):
        return False
    if any(word in OTHER_PEOPLE or word in WE_OUR_OURS for word in words):
        return True
    return any(one in POSSESSIVE_OF_A_PERSON and other in TEMPERATURE_WORDS
               for one, other in zip(words, words[1:]))


def the_stomach_is_what_it_is_about(understood):
    """True when the reading says the line is about the person's stomach.

    Two everyday words mean a thing as well as a part of a person: a stool is a chair, and
    green leaves keep a week in the drawer. "loose stools for 3 days" was answered with the
    wood-glue repair, and "my poo has been green for a week" with the shelf life of salad,
    because those rows share their words with a chair and a bag of leaves. The reading has
    already settled which the line is, so the furniture and the salad rows stand aside for
    it: this is used as their `guard`, the same way `_the_part_is_a_persons` is.
    """
    return isinstance(understood, dict) and bool(
        understood.get("body") == "stomach" or understood.get("own_output") is not None)

# The words that turn a part into a complaint. A part on its own ("i'll be back", "my leg
# of the journey") is not this entry: the matcher needs two words, so the part plus one of
# these is the smallest line that answers.
HURT = ("hurt", "hurts", "hurting", "ache", "aches", "aching", "achy", "pain", "pains",
        "painful", "sore", "stiff", "killing me", "kills", "twinge", "twinges", "throbbing",
        "agony", "soreness",
        # "my back is thumping after the gym" and "my back is pounding" are the same complaint as
        # "my back is throbbing", which was here, and both got "That's a nuisance to be carrying
        # round" because the region never saw a word for hurting in them.
        "thumping", "thumps", "pounding", "pounds",
        # What people say instead of "hurts" about a part that is bad today: "my knee is playing
        # up" was a question back, "my hip gives me jip" was the echo ("Got it - your hip gives
        # you jip"), and "my shoulder is acting up" the same. Main answers "my knee has been bad
        # for months" already, through the weeks entries, so "bad" is deliberately not here: a
        # word added to this tuple would take those lines off it.
        "playing up", "playing me up", "acts up", "acting up", "giving me jip", "giving me gyp",
        "giving me grief", "gives me jip", "gives me gyp", "gives me grief",
        # A sprain is the same complaint named by what happened to it: "i sprained my ankle" and
        # "how long does a sprained ankle take to heal" name the part and the injury and no hurt
        # word at all, so the region table never saw either line.
        "sprain", "sprained", "sprains", "strain", "strained", "strains", "twisted", "tweak",
        "tweaked", "pulled a muscle", "pulled my", "torn", "went over on", "rolled", "pulled", "tore", "ripped",
        # The injury named as the thing that happened, with no word for pain: "i injured my
        # shoulder at rugby" and "i've done my shoulder in" both name the part and the injury
        # and neither says hurt, so the region table never saw the part and both were a
        # question back ("How long has that been the case?"). "done my" and "did my" are the
        # way people say it about a part out loud; the region still has to be named, so
        # "i've done my exercises" is not a shoulder.
        "injured", "injury", "injuries", "done my", "did my", "done in", "did in",
        "put my back out", "put my shoulder out", "put my knee out",
        # The other way people say a part is bad today: an opinion of it rather than a pain word.
        # "my back is a joke today" was "That sounds rough", "my knee is in bits" was "Thanks for
        # telling me", "my shoulder is wrecked" was "I'm listening", and "my hip is banjaxed" was
        # "Got it. Is there anything you'd like a hand with?" - the part was named in all of them and
        # the region table never saw a word for hurting, because the hurt was said as a verdict on
        # the part. "thats a joke" is the joke told back, "work is a nightmare" and "the bus is a
        # joke" are not parts, "the chair is wrecked" is the furniture's, so the region still has to
        # be named for any of these to fire. "knackered" is deliberately not here: it means tired,
        # and "im knackered" is not a back. Bare "at me" is not here either, for the reason above:
        # "my boss shouted at me" is not a part.
        "a joke", "in bits", "wrecked", "banjaxed", "a nightmare", "torture", "is at me",
        "in a state", "a state", "hanging off me", "in agony", "giving me trouble",
        # The complaint said as what it stops you doing: "driving at night is hard because of my
        # back" is a back question, and the part was named with no word for hurting in the line,
        # so the region table never fired and the night-driving card answered it with headlights.
        # "because of my" only fires beside a named part.
        "because of my", "because of her", "because of his")

# A part that hurts somewhere else in the body is a different answer: chest pain is an
# emergency, a sore throat, a tooth and an ear belong to the entries that know them, and a
# stomach ache is not a muscle. Anything here sends the line on to those instead.
# Somebody else's arm is not this person's strain: "my son fell off the trampoline and hurt his
# arm", "my dog has a sore leg", "his back hurts", "my mum has a sore back" are asked about a
# third person, and the second-person advice that follows ("keep walking and carry on with your
# usual jobs") is the wrong voice for them, so those lines go back to the chat reply.
_OTHER_PEOPLE = ("my son", "my daughter", "my child", "my kid", "my kids", "my baby",
                 "my toddler", "my husband", "my wife", "my partner", "my mum", "my mom",
                 "my mother", "my dad", "my father", "my friend", "my dog", "my cat",
                 "my puppy", "my horse", "the dog", "the cat")
_PARTS = ("arm", "leg", "back", "knee", "foot", "feet", "hand", "shoulder", "neck", "hip",
          "ankle", "wrist", "elbow")
THIRD_PARTY = _OTHER_PEOPLE + tuple("%s %s" % (who, part) for who in ("his", "her")
                                    for part in _PARTS)

# An ache that has been there for weeks is a "what now" question rather than a fresh strain: the
# advice for a two-day-old knock ("ease off running for two days") is not the answer for a month
# of it, so the long-running ones keep the reply they had.
STANDING = ("for a week", "for two weeks", "for a fortnight", "for weeks", "for a month",
            "for months", "for ages", "weeks", "months", "a week now", "two weeks",
            "three weeks", "a few weeks")

# A follow-up that asks whether to go and get a part looked at is a decision question, not a fresh
# account of the pain: "should i see someone about it or wait" wants the "see a physio if it
# swells, locks or gives way" line back, and answering it with the whole strain paragraph again
# only repeats turn one.
# A part that hurts after a fall is a "have it looked at" question, not an overused tendon: bare
# "fall" covers "my wrist hurts after a fall", "a fall yesterday" and every part, where the spelled
# phrases only caught "i fell".
FALL = ("fall", "a fall", "after a fall", "from a fall", "banged", "knocked", "bump", "bumped")

DECIDE = ("see someone", "see a doctor", "see the doctor", "see a gp", "go to the doctor",
          "should i see", "do i need to see", "or wait", "see a physio", "worth seeing",
          "get it looked at", "should i get it checked")

# A part that hurts *with* one of these is not the everyday strain, and "most back pain is
# muscular" is the wrong opening for it: a back that cannot pass urine, a calf that is hot and
# swollen after a flight, pain that wakes somebody at night. Those lines get a short "get it seen
# today" answer of their own, and RED_FLAG is in the strain table's avoid so the two cannot race.
RED_FLAG = ("cant pee", "can't pee", "cannot pee", "cant wee", "can't wee", "cant pass urine",
            "can't pass urine", "cant pass water", "no urine", "cant urinate", "can't urinate",
            "cannot urinate", "numb", "numbness", "pins and needles", "cant feel my legs",
            "can't feel my legs", "cant feel my feet", "cant feel my foot", "legs give way",
            "leg gave way", "incontinent", "lost control of my bladder", "saddle",
            "hurts when i breathe", "hurts to breathe", "pain when i breathe",
            "worse at night", "wakes me at night", "wake me at night", "wakes me up",
            "woke me up", "hot and swollen", "swollen and hot", "swollen calf", "swollen leg",
            "hot calf", "red and hot", "after a flight", "after a long flight")
# The parts and the words for hurting, shared by the two red-flag entries below: the flag has
# to be attached to a body, or "i cant pee" alone would be this table's business.
_SORE_ANYWHERE = ("back", "leg", "legs", "calf", "calves", "thigh", "shin", "arm", "arms",
                  "hip", "knee", "foot", "feet", "spine", "side", "shoulder", "neck",
                  "ankle", "wrist", "elbow", "hand", "pain", "pains", "hurts", "hurting",
                  "ache", "aches", "aching", "achey",
                  # the plurals: people say "my ankles have swelled up", "my hands are puffy",
                  # "sore knees", and only the singular was here, so the part never counted
                  "ankles", "knees", "hands", "thighs", "shins", "hips", "wrists", "elbows",
                  "shoulders", "toes", "fingers", "thumbs", "heels")

# The next-day ache after new exercise, which sport.sore-after-exercise explains better. Named
# apart from the rest so the entry below can keep a back that went *at* the gym: that is an
# injury in the middle of a session, not the soreness two days after one.
EXERCISE_DAY = ("gym", "workout", "work out", "exercised", "weights", "next day", "day after")

# A sore part with a painkiller in the line is a medicine question, not a strain: "my back hurts
# can i take ibuprofen" wants the dose, the 1200 mg ceiling and the stomach cautions, and the
# six-weeks-and-keep-walking answer is beside the point. Only the names of the medicines are
# here: the asking words ("can i take", "is it safe to") go with a named medicine, and a line
# that says only those, with no medicine in it, still has only this table to answer it.
MEDICINE = ("ibuprofen", "ibruprofen", "ibuprofin", "nurofen", "brufen", "painkiller",
            "painkillers", "pain killer", "pain killers")
# The words here are only the ones the dose row in `health.py` answers. Standing a joint row
# down for a medicine nothing else answers leaves the person with a shrug: "my wrist hurts, is
# codeine ok" and "my shoulder aches, what painkiller is best" both went from an answer to "a
# pharmacist can answer that today" when this list was longer. Paracetamol is out for the same
# reason (no adult paracetamol row is reachable from here), and so are codeine, tramadol,
# naproxen, aspirin and co-codamol.
# A part word inside a compound is not a body. "just hand luggage", said a turn after "im flying
# to dublin next week", reached the sore-part table on the pair "hand" + "week" and answered a bag
# with "a hand that has been sore for a week or more... ask your GP about physio". The part has to
# be the person's part, so a line that names one of these is not this table's line at all. Phrases
# only: "hand" on its own is the body, and "the back of the car" is not a back, but bare "back"
# is the commonest part in the file.
_NOT_A_BODY_PART = (
    # hand
    "hand luggage", "hand bag", "handbag", "hand luggage only", "hand cream", "hand wash",
    "hand soap", "hand sanitiser", "hand sanitizer", "hand dryer", "hand towel", "hand brake",
    "hand held", "handheld", "first hand", "second hand", "secondhand", "second-hand",
    "on the other hand", "helping hand", "hand me", "hand in hand", "hand made", "handmade",
    "hand whisk", "hand mixer", "hand warmer", "hand rail", "handrail", "hand print",
    "handwriting", "handwriting", "hands on",
    # back
    "back garden", "back door", "back seat", "back pay", "back up", "cashback", "back to school",
    # "come back" and "go back" were here and are not compounds: "back" is the particle in them,
    # which the sore-part table already handles by asking whose the part is ("my back", "back
    # pain"), so they were only standing down the lines that name the pain twice - "my back pain
    # keeps coming back" and "my knee pain keeps coming back" got "That sounds wearing..." from
    # the chat pool instead of the strain answer on main d6918e6a -> 28610cbf.
    "back of the car", "back page",
    "back of the fridge", "back of my throat", "in the back of",
    # foot and the rest
    "on foot", "foot of the stairs", "foot of the bed", "foot of the garden", "six foot",
    "five foot", "foot long", "at the foot of",
    # arm, leg, knee, hip in an object
    "arm chair", "armchair", "arm of the sofa", "arm of the chair", "leg of the table",
    "leg of the chair", "table leg", "chair leg", "door handle", "knee deep", "hip flask",
)

AVOID = ("chest", "heart", "throat", "tooth", "teeth", "gum", "gums", "ear", "ears",
         "stomach", "tummy", "belly", "period", "pregnant", "pregnancy", "jaw",
         # a sore part with sickness, sweating or breathlessness on top of it is how a heart
         # attack reads: that line belongs to the emergency answer, not to this table
         "sick", "nauseous", "vomit", "dizzy", "faint", "breathless", "sweating",
         # a part that smells, or that has a mark on it, is a question for the skin and the
         # washing entries: "my feet smell even after washing what helps" is not foot pain,
         # and "a mole on my back" is not a strain
         "smell", "smells", "smelly", "stink", "stinks", "stinking", "odour", "odor",
         "sweaty", "sweat", "mole", "moles", "rash", "rashes", "spot", "spots",
         "blister", "blisters", "wart", "warts", "bruise", "bruises", "birthmark",
         "ingrown", "athletes foot",
         # the ache a day or two after new exercise is normal and it is not damage: that line
         # belongs to sport.sore-after-exercise, which explains it in the person's own terms
         # a knee that aches when it is cold or when it rains is the weather answer, not a strain:
         # "ease off running and ice it" is the wrong advice for a joint that has not been hurt.
         # Phrases, not the bare "cold": "my hands are cold all the time" is a circulation
         # question, and the bare word was taking the circulation answer away from four lines.
         "when its cold", "when it's cold", "when it is cold", "in the cold", "in this cold",
         "cold weather", "cold and damp", "when it rains", "when it rained", "in the rain",
         "when its damp", "when it's damp", "damp weather", "when the weather",
         "weather changes", "in the winter", "in winter", "before rain", "before it rains",
         ) + _NOT_A_BODY_PART + EXERCISE_DAY + STANDING + THIRD_PARTY + DECIDE + FALL + RED_FLAG + MEDICINE

# (entry name, the words people call that part, what actually helps it)
REGIONS = (
    ("back", ("back", "lower back", "spine", "backache"),
     "Most back pain is muscular and settles in two to six weeks, and staying active is what "
     "helps most: keep walking and carry on with your usual jobs as far as you can rather than "
     "taking to your bed, and take paracetamol or ibuprofen if you can. See a GP if it is no "
     "better in a fortnight, or today if you cannot pass urine, have numbness between your legs, "
     "or it came on after a fall."),
    ("knee", ("knee", "kneecap"),
     "A sore knee is usually a strain or the kneecap tracking badly: ease off running, stairs and "
     "kneeling, ice it for 20 minutes at a time with a cloth round it for the first two days, then "
     "keep it moving gently. Get it looked at if it gives way, locks, or you cannot put your "
     "weight on it."),
    ("shoulder", ("shoulder", "shoulders", "shoulder blade", "rotator cuff"),
     "Most shoulder pain is a strained or trapped tendon, worse when you reach overhead or lie on "
     "that side: keep using the arm as far as is comfortable, warm it before you use it, and do "
     "the pendulum swing (lean forward, let the arm hang, circle it slowly) a few times a day. See "
     "a GP if you cannot lift the arm at all or it started after a fall."),
    ("neck", ("neck", "stiff neck"),
     "A stiff neck is usually muscular, from posture or sleeping awkwardly: heat, gentle stretches "
     "and a look at your screen height help, and a soft collar for a day or two is fine but not "
     "longer, because the muscles need to work. Get seen the same day if it comes with a fever, a "
     "bad headache, or light hurting your eyes."),
    ("hip", ("hip", "hips"),
     "Hip pain in an adult is usually the joint or the tendon over the outside of the hip bone: "
     "keep walking as far as is comfortable, sit with your knees lower than your hips, and take a "
     "painkiller before a walk rather than after. See a GP if it hurts when you are resting or at "
     "night, or you have started to limp."),
    ("ankle", ("ankle", "ankles"),
     "An ankle sprain wants ice for 20 minutes at a time for the first two days, a support wrap "
     "and the foot up when you sit, then gentle movement and a slow return to walking on it. Most "
     "settle in two to six weeks, and the swelling can take months. Get it looked at the same day "
     "if you cannot put any weight on it, it swells badly, or it looks crooked."),
    ("foot", ("foot", "feet", "heel", "heels", "arch", "plantar"),
     "Foot pain is often the plantar fascia, the band under the arch, worst on your first steps in "
     "the morning: stretch the calf against a wall before you stand up, roll the arch on a cold "
     "bottle, and wear shoes with a firm sole indoors too. A heel that hurts all day, or a foot "
     "that is red and hot, needs looking at."),
    ("wrist", ("wrist", "wrists", "hand", "hands", "thumb", "fingers"),
     "Wrist and hand pain is usually an overused tendon or a nerve pressed by the way you grip and "
     "type: take breaks, keep the wrist straight rather than bent, and try a support splint from "
     "the pharmacy at night. Pins and needles in the fingers that wake you is worth a GP visit."),
    ("elbow", ("elbow", "elbows", "tennis elbow"),
     "Elbow pain on the outside is tennis elbow, an overused tendon, and it settles over weeks to "
     "months once you rest from the gripping and lifting that sets it off: a strap just below the "
     "elbow and slow strengthening with a light weight help. See a GP if it is no better in six "
     "weeks."),
    ("arm", ("arm", "arms", "upper arm", "forearm"),
     "Most arm pain is a muscle strain or the ache a day after lifting, and some of it comes down "
     "from a sore shoulder or elbow: keep using it as far as is comfortable and take a painkiller if you "
     "can. See a GP if the arm is weak or numb, and treat a heavy left arm with tightness in the "
     "chest, sweating or breathlessness as an emergency."),
    # The ribs, the tailbone and the groin were the three parts this table never learned, so
    # "my ribs hurt" and "my tailbone hurts" got "That's a nuisance to be carrying round" and
    # "my groin hurts" got "What have you tried for it so far?". Each wants its own advice:
    # ribs are about breathing normally and a cushion to cough against, a tailbone is about
    # where you sit and mends over weeks, a groin is a pulled muscle with a hernia to rule out.
    ("ribs", ("rib", "ribs", "ribcage", "rib cage", "ribs hurt"),
     "A rib that hurts when you breathe in, cough or press it is usually bruised, not broken, and "
     "it mends the same way either way: keep breathing normally rather than in shallow sips, take "
     "paracetamol or ibuprofen, and press a cushion against that side when you cough. It eases "
     "over three to six weeks. Get seen the same day if you are breathless or coughing blood."),
    ("tailbone", ("tailbone", "tail bone", "coccyx", "sacrum"),
     "A sore tailbone is usually a knock from a fall or hours sitting on a hard chair, and it "
     "mends slowly - a few weeks, sometimes a couple of months. Sit on a soft or doughnut "
     "cushion, tilt forward a little rather than leaning back onto it, and take paracetamol or "
     "ibuprofen; a warm bath helps the muscles around it. See a GP if it is no better after a "
     "few weeks, or if there is numbness or bleeding."),
    # A toe and a collarbone were the other two the table had no row for: "my toe hurts" got the
    # running-shoe answer and "my collarbone hurts" got "Does it come and go, or is it there all
    # the time?". A big toe that goes hot and red overnight is gout, and that is the one shape of
    # toe pain worth naming, so the toe answer says it.
    ("toe", ("toe", "toes", "big toe"),
     "Most toe pain is a stub, a bruise under the nail or an ingrown edge: soak it in warm salty "
     "water, wear shoes with room in them and take paracetamol. A big toe that goes red, hot and "
     "swollen overnight, often at night, is gout - that one wants seeing this week, and sooner if "
     "you have diabetes and it looks infected."),
    ("collarbone", ("collarbone", "collar bone", "clavicle"),
     "A collarbone that hurts after a knock usually mends in a sling over four to six weeks, and "
     "the pain often eases before the bone has joined: keep the hand and elbow moving gently, "
     "sleep propped up a little and take paracetamol. Have it looked at with an X-ray if you "
     "cannot lift the arm, the bone looks out of line, or it hurts too much to sleep."),
    # "inner thigh" is not in the key: a vague "my inner thigh hurts" is the day-after ache the
    # leg row answers honestly, and only a line that says groin or adductor is a groin pull.
    ("groin", ("groin", "adductor"),
     "A sore groin is usually a pulled muscle from twisting, kicking or turning quickly: give "
     "the sport that set it off a fortnight off, ice it for 20 minutes at a time for the first "
     "two days, then stretch and strengthen gently. Get a lump or a bulge that appears when you "
     "cough or lift looked at - that is a hernia - and get a sudden severe pain in one side "
     "seen the same day."),
    ("leg", ("leg", "legs", "calf", "calves", "thigh", "thighs", "hamstring", "shin"),
     "A pulled thigh or calf muscle, or the ache that lands a day after squats, wants the same "
     "start: rest it, ice it for 20 minutes at a time for two days, then gentle stretching and a "
     "slow return to what you were doing, with the leg kept up when you sit. Calf pain with a hot, "
     "swollen leg, or a shin that hurts to touch after a knock, needs looking at."),
)


# A part can be answered better elsewhere for one shape of line. Knee pain on the stairs is
# the kneecap being pulled out of line, which `sport.knee-pain-stairs` explains with the
# exercises for it; the general sore-knee reply here would be a step down, and in a
# conversation it also loses the follow-up ("it's worse going up stairs"), because that
# answer belongs to sport. So those words send the line on.
EXTRA_AVOID = {
    # a wrist or an arm that hurts because the person fell on it is a possible break, not an
    # overused tendon, so that line goes back to the chat reply (which asks about it)
    "wrist": ("i fell", "fell over", "fell on", "fell down", "fell off", "fell and", "tripped",
              "slipped", "landed on my", "banged it", "knocked it", "crushed"),
    "arm": ("i fell", "fell over", "fell on", "fell down", "fell off", "fell and", "tripped",
            "slipped", "landed on my", "banged it", "knocked it", "crushed"),
    # a knee that clicks or creaks is a noise question, not a pain one, and the sport entries
    # own both ("my knee clicks and hurts" is knee-pain-stairs, "my knee creaks but it doesnt
    # hurt" is knee-noise) - so the noise words hand the line on
    # a leg or a calf that is hot or swollen is the clot question, not the pulled muscle: those
    # lines go to body-see-today above instead of the ice-and-rest paragraph
    "leg": ("swollen", "swelling", "hot", "flight", "long sit", "red", "tender", "warm",
            # a shin is not a calf or a thigh: "what should i do about my shin" and "my shin
            # hurts" are the shin-splints answer, and the leg row was taking them because
            # "shin" is in its own key
            "shin", "shins"),
    # "the back of my knee" is a knee and "the back of my head" is a head: "back" comes first in
    # the region table, so a line that names another part after "back of" never reached that
    # part's row. The words arrive as a set, so there is no order to read - they are listed.
    # A back that gives trouble on and off is the long-running answer, and a back hurt by a day
    # of lifting or gardening has its own: with the ask phrase in the key the two-to-six-week
    # paragraph was taking all of them.
    "back": tuple("back of %s %s" % (whose, part) for whose in ("my", "the", "your")
                  for part in ("knee", "knees", "neck", "throat", "hand", "hands", "ankle",
                               "calf", "heel", "head", "shin", "elbow", "wrist", "foot")) + (
        "bad back", "a bad back", "gives trouble", "on and off",
        "gardening", "after gardening", "digging", "after a day of lifting", "lifting",),
    "knee": ("stairs", "stair", "staircase", "steps", "climb", "climbing", "downstairs",
             "upstairs", "up steps", "down steps",
             "click", "clicks", "clicking", "creak", "creaks", "creaking", "grind",
             "grinding", "noise", "noisy", "popping", "crack", "cracks", "cracking"),
}

# The joints that can go hot and swollen on their own. The red-flag paragraph below was written
# for a back, a side and a calf, so a swollen knee read as if the bot had not heard which part
# hurt: "my knee has been clicking since the gym", "its the left one", "and its swollen today" was
# told about chest pain and a hot calf after a flight. The reply speaks to the part named.
JOINTS = ("knee", "knees", "ankle", "ankles", "wrist", "wrists", "elbow", "elbows",
          "hip", "hips", "shoulder", "shoulders", "foot", "feet", "toe", "toes",
          "thumb", "thumbs", "joint", "joints")

HOT_SWELLING = ("swollen", "swelling", "swelled", "puffy", "hot", "red", "inflamed")

SEE_TODAY_BACK_AND_CALF = (
    "That is worth being seen today rather than waiting for it to settle. Pain in the back "
    "or side that hurts when you breathe, pain that wakes you at night, or a calf that is hot "
    "and swollen - especially after a flight or a long sit - are the shapes a doctor wants "
    "to look at the same day: ring 111 or your GP this morning. Go to A&E if your chest "
    "hurts suddenly or you are short of breath.")


# The parts whose swelling this paragraph is not about: a hot, swollen calf or a swollen leg is
# the clot question, and a back or a side is the breathing one, so those keep the paragraph.
# A rib is here for the same reason: the flag that brings a rib to this entry is "hurts when i
# breathe", and answering that with "a swollen rib is usually fluid" - which is what naming the
# part did once ribs were a region - is a sentence about nothing.
CLOT_AND_CHEST = ("leg", "legs", "calf", "calves", "thigh", "thighs", "shin", "shins",
                  "back", "side", "spine", "rib", "ribs")

HOT_FLAGS = ("hot", "red", "inflamed", "burning", "went red", "gone red")


def _see_today(memory, understood):
    """The same-day paragraph, spoken about the part the line actually named.

    The paragraph was written for a back, a side and a calf. A swollen knee reached it and was
    told about chest pain and a clot after a flight, which reads as if the bot had not heard
    which part hurt - worse than saying nothing. So the words of the line (and of the turn it
    leans on) pick the sentence: a joint speaks for itself, a hot one leads with the flag.
    """
    words = _words(understood)
    part = _part_named(words, understood)
    if not part or part in CLOT_AND_CHEST:
        return SEE_TODAY_BACK_AND_CALF
    if words & set(HOT_FLAGS):
        return ("A " + part + " that has gone hot and swollen wants looking at today rather "
                "than iced and waited on: ring 111 this morning, and go to A&E if there is a "
                "fever with it or you cannot put weight on it at all.")
    # Swollen feet on both sides are a tablet or the heart as often as a knock, so the generic
    # sentence sends the person to be looked at rather than to the ice pack.
    return ("A swollen " + part + " is usually fluid - from a knock or overuse, or from a tablet "
            "or the heart when it is on both sides - so have it looked at this week and keep it "
            "raised when you sit. Ring 111 today if it is hot, red and spreading, or painful on "
            "just one side.")


# The word to put in the sentence: the person's own word for the part, singular, because
# "a swollen hands" reads wrong and "a swollen wrist" answers a hand nobody mentioned.
PART_ONE = {"feet": "foot", "calves": "calf", "thighs": "thigh", "shins": "shin", "hands": "hand",
            "ribs": "rib", "ribs hurt": "rib", "tail bone": "tailbone", "big toe": "toe",
            "collar bone": "collarbone",
            "fingers": "finger", "thumbs": "thumb", "heels": "heel", "toes": "toe",
            "knees": "knee", "ankles": "ankle", "elbows": "elbow", "wrists": "wrist",
            "shoulders": "shoulder", "hips": "hip", "legs": "leg", "arms": "arm"}


def _part_named(words, understood=None):
    """The part of the body the line names, in the words the person used.

    "back" is the one part word that is also a particle, so a caller that has the reading hands
    it over and a back the line only sends or comes back is not a part: "my knee hurts and im
    going back to work" is a knee, and the rule called it a back.
    """
    if understood is not None and "back" in words and not _the_back_is_a_back(understood):
        words = set(words) - {"back"}
    for _name, spelled, _reply in REGIONS:
        for word in spelled:
            if word in words:
                return PART_ONE.get(word, word)
    for part in JOINTS:
        if part in words:
            return PART_ONE.get(part, part)
    return ""


# --- the back that has gone numb, and the hand that has ---------------------------------
# A numb hand is not a saddle numbness. The card below is the cauda equina one: it names the
# legs and the bladder, so a line about a back *and* a hand must not reach it - the Raynaud and
# carpal-tunnel answers are the right ones there, and a red flag that names the wrong part of
# the body teaches the reader to discount it. Main reached those lines with the wrong card only
# when the line scored four, which a single numb hand does not; the phrasings added here
# ("no feeling", "went numb", "cant feel") do score, so the region has to be read back off the
# line before the card is spoken.
LOWER_HALF = ("leg", "legs", "calf", "calves", "thigh", "thighs", "shin", "shins", "groin",
              "saddle", "bottom", "bum", "backside", "butt", "buttocks", "crotch",
              "genitals", "knickers", "undercarriage", "between my legs", "down there",
              "hips", "bladder", "wee", "wees", "peed", "pee", "urine", "urinate",
              "toilet", "catheter", "bowels", "waterworks")

# Somewhere that is not the lower half. A foot is here too: "my back hurts and my foot has gone
# numb" is the white-fingers answer on main, and a cold foot is not a saddle numbness - the
# feet that *are* the flag say so in words of their own (SPELLED_OUT) and are read first.
SOMEWHERE_ELSE = ("arm", "arms", "hand", "hands", "finger", "fingers", "thumb", "thumbs",
                  "wrist", "wrists", "elbow", "elbows", "shoulder", "shoulders", "neck",
                  "tongue", "face", "cheek", "jaw", "head", "foot", "feet", "toe", "toes")

# A back is the flag's own half: numbness below a sore back is read as the flag whatever part of
# the lower half the line names, because the part people mention ("my foot", "my toes") is the
# one that hurts, not the one that decides.
BACK_NAMES = ("back", "backs", "backache", "back ache", "spine", "spinal", "lower back",
              "slipped disc", "sciatica", "my back")
NUMB_ANYWHERE = ("numb", "numbness", "pins and needles", "tingling", "no feeling",
                 "lost feeling", "no sensation", "cant feel", "gone numb", "went numb",
                 "dead", "asleep")
# ... but only the parts below the back. A numb hand with a sore back is the hand cards' question:
# the flag names the legs and the bladder, and a card that names the wrong part is a card the
# reader learns to discount.
NUMB_LOWER = ("foot", "feet", "toe", "toes", "sole", "soles", "heel", "heels", "ankle",
              "ankles", "leg", "legs", "calf", "calves", "thigh", "thighs", "shin", "shins",
              "hip", "hips", "buttock", "buttocks", "bottom", "bum", "backside", "groin",
              "saddle", "between my legs", "down there")
# The numbness written out as the legs or the feet: the card's own words, so it answers whatever
# else the line mentions.
SPELLED_OUT = ("cant feel my feet", "cant feel my foot", "cant feel my toes",
               "cant feel my legs", "cant feel my leg")

# The saddle is the one part that is also a bicycle part, so a line can name it and mean the
# skin between the legs rather than the seat. Numbness there on its own is common and usually
# pressure; numbness there *with* a back or the waterworks is the cauda equina question. Both
# halves are spoken, in that order, and neither is left to a bike fit.
SADDLE_PARTS = ("saddle", "saddle area", "saddle region",
                # the same nerves and the same two answers: it is the skin between the legs
                # whether the line calls it the saddle, the groin or "down there", and
                # "my groin is numb" was a shrug on main
                "groin", "genitals", "crotch", "undercarriage", "down there")
FLAG_WITH_IT = ("back", "backs", "leg", "legs", "calf", "calves", "thigh", "thighs", "shin",
                "shins", "spine", "both legs", "hips", "hip", "give way", "gave way",
                "cant pee", "cant wee", "cant pass urine", "cant go for a wee",
                "cant go for a pee", "cant go to the toilet", "cant do a wee", "bladder",
                "bowels", "incontinent", "no urine", "wetting myself", "ache", "aching",
                "pain", "pains", "hurts", "hurting", "sore", "hurts to", "both sides")
# "went numb", "gone numb" and "down there" are not a second flag: they say the numbness
# itself, and "my groin has gone numb" or "numb down there" was pushed into "Do not wait on
# that one" by them, which is the 999 card for a back that has given way.

SADDLE_CARD = (
    "Numbness between the legs, in the saddle area or the groin, is usually pressure on the "
    "nerves there: a bike saddle, a long sit, tight jeans or a wallet in a back pocket. It "
    "lifts within an hour of standing up. Shorten the rides and the sits, stand up every 20 "
    "minutes, and set the bike saddle level and not too high. If it has not gone by the next "
    "day, or it comes with back pain, "
    "numbness down both legs, or any trouble weeing or opening your bowels, ring 111 the same "
    "day and say \"numbness in the saddle area\" - do not wait for that one to settle.")

RED_FLAG_CARD = (
    "Do not wait on that one. A sore back with no urine coming, numbness or pins and "
    "needles between your legs or in your feet, or a leg that gives way is the one back "
    "problem that has to be seen the same day: ring 999 or go to A&E now, and do not drive "
    "yourself. If you are not sure, ring 111 and say those words to them.")


def _names(text, words):
    """True when one of these words or phrases is in the line, as a whole word."""
    for word in words:
        if " " + word + " " in text:
            return True
    return False


def _red_flag(memory, understood):
    """The emergency card, or nothing at all when the numb part is not the lower half.

    "my back hurts and my hand has gone numb" is a hand question and keeps the answer it had
    before this entry could read "gone numb"; "no feeling between my legs and back pain" is
    the flag, and so is anything that names the waterworks.
    """
    if not isinstance(understood, dict):
        return RED_FLAG_CARD
    said = str(understood.get("text") or "").lower().replace("\u2019", "").replace("'", "")
    text = " " + re.sub(r"[^a-z]+", " ", said) + " "
    for key in ("words", "background"):
        for word in understood.get(key) or ():
            if isinstance(word, str):
                text += word.lower().replace("'", "") + " "
    if _names(text, SPELLED_OUT):
        return RED_FLAG_CARD      # "cant feel my feet": the card's own words, whatever else
    # The tented skin between the legs is not the legs: a line that names only the saddle, with
    # no back, no leg and no bladder in it, is the pressure answer with the same-day words at the
    # end of it. Read on its own words, so an earlier turn cannot turn it into the 999 card.
    own = " " + re.sub(r"[^a-z]+", " ", str(understood.get("text") or "").lower()) + " "
    # A line that says there is no back pain, no weakness and no trouble weeing has ruled the
    # flags out in words, and "numbness in my saddle but no back pain" was being sent to the 999
    # card by the word "back" alone. Take the ruled-out phrases out before looking for a flag.
    ruled_out = own
    for phrase in ("no back pain", "no backache", "no back ache", "no pain in my back",
                   "without back pain", "no leg pain", "no pain in my legs", "no weakness",
                   "no trouble weeing", "no trouble going for a wee", "no problems weeing",
                   "no trouble peeing", "no numbness in my legs", "no pain",
                   "my back is fine", "my back is ok", "my back is okay", "back is fine",
                   "without a bad back", "no problems with my back"):
        ruled_out = ruled_out.replace(phrase, " ")
    # A back with numbness anywhere below it is the same question, whatever part is named: a
    # foot that has gone numb and a back that hurts is cauda equina until it is ruled out, and
    # this file's own comment says so - but the guard read a foot as "somewhere else" and sent
    # "my back hurts and my foot has gone numb" to the running-injury card. The foot row stands
    # aside for a back (see numb-foot), so without this the line falls back to a shrug.
    if (_names(ruled_out, BACK_NAMES) and _names(ruled_out, NUMB_ANYWHERE)
            and _names(ruled_out, NUMB_LOWER)):
        return RED_FLAG_CARD
    if _names(ruled_out, SADDLE_PARTS) and not _names(ruled_out, FLAG_WITH_IT):
        return SADDLE_CARD
    if _names(text, LOWER_HALF) or not _names(text, SOMEWHERE_ELSE):
        return RED_FLAG_CARD
    return ""                     # a numb hand, arm or tongue: another entry's question


def _words(understood):
    """Every word of the line, and of the turn it leans on, as a set."""
    if not isinstance(understood, dict):
        return set()
    found = set()
    for key in ("words", "background"):
        for word in understood.get(key) or ():
            if isinstance(word, str):
                found.add(word.lower())
    return found


# Two shapes of line come before the strain answer. Both are keyed on the flag *and* a body, so
# neither can fire on the flag alone: "i cant pee" with no part is not this table's business.
# "ring" is a verb as well as a noun, and it is the commoner of the two by a long way: "i need
# to ring the dentist but i keep putting it off" is a phone call, not a stuck ring, and with
# "ring" plus "off" in the key it got soap and dental floss. `RING_AS_A_CALL` in lookup.py holds
# every phone shape, and the hob and the jeweller read the same list; what is added here is the
# other half of the same worry - a ring the person keeps meaning to make, which is still a call.
RING_NOT_ON_A_FINGER = RING_AS_A_CALL + (
    "putting it off", "keep putting off", "kept putting off",
    "keep meaning to", "meant to ring", "forgot to ring", "dreading ringing")


def _dose_for_the_drug_named(memory, reading):
    """The dose of the painkiller the line actually named, first.

    "how much ibuprofen can i take" opened on paracetamol tablets, because one entry answers
    every drug and the first sentence was written for paracetamol. STYLE asks for the answer in
    the first sentence, and the first sentence of a dose question is the figure for the packet
    the person is holding. A line that names no drug, or names two, keeps the pair answer.
    """
    words = set(reading.get("words") or ())
    # A painkiller this table has no row for is not a paracetamol question. "how much aspirin
    # can i take" was answered "two 500mg paracetamol tablets... and less if you have liver
    # trouble" - the wrong drug and the wrong warning, and worse than the shrug it replaces.
    # Handing the line back leaves it to the module that knows, which is the whole point of a
    # module that only answers what it is good at.
    if words & {"aspirin", "disprin", "anadin", "naproxen", "diclofenac", "voltarol", "tramadol",
                "solpadeine", "veganin", "feminax", "migraleve", "dydramol", "paracodol",
                "dihydrocodeine"}:
        return None
    paracetamol = bool(words & {"paracetamol", "acetaminophen", "calpol", "panadol"})
    ibuprofen = bool(words & {"ibuprofen", "nurofen", "brufen"})
    codeine = bool(words & {"codeine", "co-codamol", "co codamol", "cocodamol", "codamol"})
    if codeine and not paracetamol:
        return ("Co-codamol is paracetamol and codeine together, so the paracetamol limit is what "
                "caps it: two 500/8mg tablets, four times in 24 hours at most, eight a day. The "
                "codeine is what makes it constipating and drowsy, so days rather than weeks, and "
                "don't drive until you know how it treats you. Don't add paracetamol on top: over "
                "4g a day from any mix of products is a liver emergency.")
    if ibuprofen and not paracetamol:
        return ("Ibuprofen for an adult is 200 to 400mg every four to six hours, up to three "
                "times a day, with food, and no more than 1200mg a day without a prescription - "
                "six of the 200mg tablets. Skip it "
                "if you have a stomach ulcer, kidney trouble or are on a blood thinner, and in the "
                "last three months of pregnancy. Use the lowest dose that works, and check a cold "
                "remedy does not already contain it.")
    return ("Two 500mg paracetamol tablets, four times in 24 hours at most, four hours apart - 4g, "
            "or eight tablets, a day, and less if you have liver trouble or drink heavily. "
            "Ibuprofen is 200 to 400mg every four to six hours with food, and no more than 1200mg "
            "a day without a prescription. The packet is the one to trust, and check a cold remedy "
            "does not already contain paracetamol.")


# A new piercing is asked about in two ways that read the same: the healing time ("how long does a
# pierced ear take") and the sign of trouble ("my piercing is swollen and hot"). The sign words are
# in the healing row's key too, so a possible infection got two healing times and a cleaning
# routine. A sign word stands the healing row down - unless the line is about a bump, which is the
# piercing's own crusty-bump question and is answered by that card.
_PIERCING_TROUBLE = re.compile(
    r"\b(red|redness|swollen|swelling|hot|weeping|ooz|pus|yellow|green|feverish|fever|spreading|"
    r"streaking|throbbing|angry|infected|infection|smelly|smell|lump|lumps)\b", re.I)
_PIERCING_BUMP = re.compile(r"\b(bump|bumps|keloid|crusty|crust|scab|lump|stud sunk|embed)\b", re.I)


# The other half of the pair: the line names a sign of infection, so it is not asking how long
# healing takes. Standing the healing row down left these lines with whatever card caught them
# next - "my nose piercing is swollen and hot" got a kidney-stone card - so the signs get a card of
# their own, saying what to do today and what makes it urgent.
_PIERCING_PIECE = re.compile(
    r"\b(piercing|piercings|pierced|earring|earrings|ear ring|nose ring|nose stud|nose hoop|"
    r"septum|helix|tragus|daith|rook|conch|cartilage|industrial|barbell|labret|stud|hoop|"
    r"belly bar|belly button|eyebrow|nostril|lip ring|tongue bar|earlobe|ear lobe)\b", re.I)
_PIERCING_NOT_TROUBLE = re.compile(
    r"\b(how long|heal|heals|healing|take to heal|when can i change|change the jewellery|"
    r"aftercare|after care|keloid|crusty|crust|jewellery too tight|swollen in the morning|"
    r"when can i swim|can i swim|downsize|bump|bumps)\b", re.I)


def _a_piercing_in_trouble(understood):
    """True when the line is about a piercing that is showing a sign of infection."""
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join([str(reading.get("clean") or ""),
                     " ".join(str(word) for word in (reading.get("words") or ()))])
    if not (_PIERCING_PIECE.search(said) and _PIERCING_TROUBLE.search(said)):
        return False
    return not _PIERCING_NOT_TROUBLE.search(said)


def _piercing_infection(memory, understood):
    """A sign of infection in a new piercing: keep it clean, keep the jewellery in, and know the
    line where it stops being a cleaning question."""
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join([str(reading.get("clean") or ""),
                     " ".join(str(word) for word in (reading.get("words") or ()))])
    lead = ("A piercing with spreading redness, heat, pus or swelling is infected, and it needs "
            "cleaning and often antibiotics rather than patience.")
    if re.search(r"\bfever\b", said, re.I):
        lead = ("An infected piercing with a fever is one to have looked at today - a fever means "
                "it is not staying local.")
    return (lead + " Leave the jewellery in unless a piercer takes it out: the hole closes over "
            "the infection and traps it, and a piercer can fit a longer bar if the swelling has "
            "outgrown the one you have. Clean it twice a day with sterile saline on a clean pad, "
            "let water run over it in the shower, and stop touching or turning it. Warm salty "
            "water soaks for ten minutes twice a day ease the soreness. See a piercer or a GP "
            "within a day or two if the redness spreads more than a centimetre a day, the skin "
            "round it is hot, there is pus that keeps coming, or the swelling swallows the "
            "jewellery - and go straight away if the redness streaks towards the body, or you have "
            "a fever with it. Cartilage piercings are the ones that go wrong: a hot, swollen "
            "helix or nose that is spreading is worth being seen rather than watched.")


def _a_healing_piercing_not_a_troubled_one(understood):
    """True while the line is about healing a piercing rather than about a sign of infection."""
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join([str(reading.get("clean") or ""),
                     " ".join(str(word) for word in (reading.get("words") or ()))])
    if _PIERCING_BUMP.search(said):
        return True
    return not _PIERCING_TROUBLE.search(said)


_CARTILAGE_PIERCING = re.compile(
    r"\b(nose|nostril|septum|helix|tragus|daith|rook|conch|cartilage|industrial|eyebrow|"
    r"bridge|forward helix)\b", re.I)
_PIERCING_ROUTINE = (
    " Clean it twice a day with sterile saline on a clean pad and let water run over it in the "
    "shower - no alcohol, tea tree or antibacterial gel, and do not twist or turn it, because "
    "that keeps tearing the healing channel. Do not take it out early: a new piercing can close "
    "in hours, and if you must, have the piercer swap it. No swimming for two weeks, no sleeping "
    "on it, and no makeup or hairspray near it. A red bump that keeps growing, spreading redness, "
    "pus or a fever is a piercer or GP question, not a cleaning one.")


def _piercing_healing(memory, understood):
    """A lobe heals in weeks; a nose or an ear's cartilage takes twice as long, and the line knows
    which one it asked about."""
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join([str(reading.get("clean") or ""),
                     " ".join(str(word) for word in (reading.get("words") or ()))])
    if _CARTILAGE_PIERCING.search(said):
        return ("A cartilage piercing - a nose, a nostril, a septum, a helix - takes six to twelve "
                "weeks and often months to settle, where an earlobe is six to eight weeks."
                + _PIERCING_ROUTINE)
    return ("An earlobe takes six to eight weeks to heal and cartilage six to twelve weeks, though "
            "cartilage can take months to settle." + _PIERCING_ROUTINE)


ENTRIES = [
    entry("body-urgent",
          (("cant pee", "can't pee", "cannot pee", "cant wee", "can't wee", "cant pass urine",
            "can't pass urine", "cant pass water", "no urine", "cant urinate", "can't urinate",
            "cannot urinate", "numb", "numbness", "pins and needles", "cant feel my legs",
            "can't feel my legs", "cant feel my feet", "legs give way", "leg gave way",
            "incontinent", "saddle",
            # people say "i cant go for a wee" rather than "cant wee", and "no feeling" rather
            # than "numb", and both were getting the muscular-back card
            "cant go for a wee", "can't go for a wee", "cant go for a pee", "can't go for a pee",
            "cant have a wee", "can't have a wee", "cant do a wee", "can't do a wee",
            "cant go to the toilet", "can't go to the toilet", "cant get to the toilet",
            "no feeling", "lost feeling", "lost all feeling", "no sensation", "cant feel",
            "can't feel", "gone numb", "went numb", "dont know when i need a wee",
            # the plainest way of saying it, and the one the guard now reads part by part:
            # "my back hurts and my toes are numb" had no phrase of this row's in it, so the
            # running-injury card answered a back with numbness below it.
            "numb", "numbness", "pins and needles", "tingling",
            "don't know when i need a wee",
            # the numbing has to be said beside the groin: a bare "groin" next to "hurts" is a
            # pulled muscle or an infection, and those are not this row. "my groin is numb and
            # i am diabetic" was the foot-care card, which is not what numb skin there means.
            "numb groin", "groin is numb", "groin went numb", "groin has gone numb",
            "numb round my groin", "numbness in my groin"),
           ("back", "leg", "legs", "calf", "calves", "thigh", "shin", "spine", "side",
            "feet", "foot", "hip", "hips", "pain", "pains", "hurts", "hurting", "ache",
            "aching",
            # the toes and the heel are the other way people name the numbness that goes with a
            # back, and "my back hurts and my toes are numb" was the running-injury card
            "toe", "toes", "heel", "heels", "ankle", "ankles", "sole", "soles",
            # the saddle is a body part as well as a bicycle one: "numbness in my saddle"
            # named no other part, so the flag could not fire and the bike-fit answer took it.
            # The groin is the same skin and the same question, and "my groin is numb" named no
            # second part either.
            "saddle", "groin", "genitals", "crotch", "undercarriage", "down there")),
          _red_flag,
          ask=("cant", "can't", "cannot", "no", "numb", "numbness", "pins", "needles", "give",
               "gave", "incontinent", "saddle", "feeling", "sensation", "know", "toilet",
               "urine", "going", "groin"),
          # The card is the one that must win when it applies: a back with numbness below it was
          # losing to the toe, the foot and the running-injury rows on their own words. The reply
          # itself decides whether it applies (it answers "" for a numb hand or arm), so the
          # nudge costs nothing where the line is not this one.
          bias=4),
    entry("body-see-today",
          (("hurts when i breathe", "hurts to breathe", "pain when i breathe",
            "worse at night", "wakes me at night", "wake me at night", "wakes me up",
            "woke me up", "hot and swollen", "swollen and hot", "swollen calf", "swollen leg",
            "hot calf", "red and hot", "hot and red", "red and swollen", "swollen and red",
            "warm and red", "after a flight", "after a long flight",
            "swollen", "swelling", "swollen up", "gone hot", "hot to touch",
            # people say "me ankles have swelled up" and "my hands are puffy" as often as
            # "swollen", and neither word reached this entry, so both got "I'm listening"
            "swelled", "swelled up", "swelling up", "puffy", "puffed up", "puffiness"),
           _SORE_ANYWHERE + ("swollen", "swelling", "hot")),
          _see_today,
          ask=("hurts", "hurts to", "pain", "worse", "wakes", "woke", "hot", "swollen", "red",
               "after", "breathe", "night", "swelled", "puffy", "puffed"),
          # A sting or a bite that swells is the sting card's, not this one: the swelling is the
          # sting doing its ordinary work, and the sting answer is the one that says when it is
          # anaphylaxis. "a bee sting is swelling up" was told about chest pain and a hot calf
          # after a flight, which is the shape of answer that teaches a reader to skip the flag.
          avoid=("sting", "stings", "stung", "bee", "bees", "wasp", "wasps", "hornet",
                 "insect", "insects", "bite", "bites", "bitten", "nettle", "nettles", "ant",
                 "ants", "mosquito", "mosquitos", "mosquitoes", "horsefly", "tick", "midge",
                 "midges", "gnat", "gnats"),
          guard=_the_part_is_a_persons),
    # A finger closed in a door is a crush injury, and main answered it with the door's own
    # question: "my finger went black and blue after i shut it in the door" got "Oil the hinges:
    # a drop of 3-in-1 or a spray of silicone on each hinge pin". The nail rows do not reach it
    # either - there is no nail in the line - so the finger, the door and the words people use
    # for the moment it happened are what this row keys, and the first day of a crush is what it
    # answers.
    entry("crushed-finger",
          (("finger", "fingers", "thumb", "thumbs", "fingertip", "fingertips", "hand", "hands",
            "knuckle", "knuckles"),
           # the thing that came down on it, or the moment it did: "i shut my finger in the door",
           # "the door slammed on my fingers", "i trapped my thumb in the drawer"
           ("door", "doors", "drawer", "drawers", "window", "windows", "gate", "boot", "lid",
            "cupboard", "slammed", "slamming", "slam", "shut", "shutting", "closed", "trapped",
            "trapping", "caught", "catching", "jammed", "jamming", "crushed", "crushing",
            "squashed", "squashing",
            # and the words that say no door was needed: a drawer that came out on the hand, a
            # lid that came down, a weight that landed on it
            "came down on", "went between", "between the")),
          "That is a crush, so the first day is a cold pack - ice in a tea towel, ten minutes at a "
          "time, a few times - with the hand up, and paracetamol or ibuprofen for the ache. Take "
          "any ring off that finger now, before the swelling. Go to A&E the same day if the "
          "fingertip is split or the nail is torn, if blood is building up under the nail, if it "
          "throbs hard, if the finger will not straighten or looks the wrong shape, or if it is "
          "numb: a trapped fingertip can break the bone under the nail, and that needs an X-ray.",
          # the door's own questions are household jobs even when a hand is in the line: a hinge,
          # a lock, a handle, the paint, the draught, a fingerprint on the glass
          avoid=("hinge", "hinges", "oil", "oiling", "lock", "locks", "handle", "handles", "knob",
                 "creak", "squeak", "paint", "draught", "draft", "warped", "sticking", "adjust",
                 "marks", "mark", "smudge", "smudges", "fingerprint", "fingerprints", "clean",
                 "cleaning", "wipe", "stain", "stains", "glass", "panel", "install", "replace",
                 "fit a", "hang", "how do i get", "cat", "dog")),
    # A nail that went black is blood under it. It used to reach the bathroom-mould answer, because
    # "black" and "nail" are household words too: the question is what to do with the finger.
    entry("black-nail",
          (("nail", "nails", "toenail", "toenails", "fingernail", "fingernails", "nail bed"),
           ("black", "went black", "gone black", "blue", "purple", "dark", "bruised", "bruise",
            "dropped", "slammed", "hammer", "banged", "knock", "knocked", "caught it", "trapped",
            "after football")),
          "A knock that turns the nail black is blood trapped under it. Ice it for ten minutes at "
          "a time for the first day, keep the hand or foot up, and take paracetamol or ibuprofen "
          "for the ache. A small dark patch fades over weeks as the nail grows out. Get it seen the "
          "same day if it throbs hard, the nail is lifting, half of it is dark, or the finger will "
          "not bend properly: a doctor can let the blood out, and draining it at home can infect it.",
          ask=("black", "blue", "purple", "bruise", "bruised", "dropped", "slammed", "hammer",
               "bang", "knock", "caught", "trapped", "dark", "throbbing", "sore"),
          # a fungal infection, a nail that is coming off on its own and the habit of biting are
          # other answers
          avoid=("fungal", "fungus", "thrush", "yellow", "crumbly", "biting", "bite", "chew",
                 "polish", "gel", "acrylic", "manicure", "varnish")),
    # A limb that has gone black or blue is blood under the skin, and no row held it: the mould
    # answer had "my toe has gone black" (see the note on `mould-bathroom`), and without mould
    # words the same line was "Thanks for telling me" or the line said back - "Got it - it's
    # turned black". The colour is the question, so the row is the part plus the colour: the
    # bruise word alone keeps the `bruise` row, and the nail keeps `black-nail` above.
    entry("limb-went-black",
          (("toe", "toes", "foot", "feet", "ankle", "ankles", "heel", "heels", "leg", "skin",
            "bruise", "bruises",
            "legs", "shin", "shins", "calf", "calves", "thigh", "thighs", "knee",
            "knees", "hip", "hips", "arm", "arms", "forearm", "wrist", "wrists",
            "hand", "hands", "finger", "fingers", "thumb", "thumbs", "elbow", "elbows",
            "shoulder", "shoulders"),
           ("black", "black and blue", "gone black", "went black", "turned black",
            "turn black", "turning black", "going black", "gone blue", "went blue",
            "turned blue", "gone purple", "went purple", "turned purple", "purple")),
          "A bruise is blood under the skin from a knock: it looks black at first, then fades "
          "through purple, green and yellow over one to two weeks. A cold pack for twenty minutes "
          "with a cloth round it, a few times in the first two days, eases it. Get it seen the "
          "same day if it swells hard and fast, the skin is broken, the part will not take your "
          "weight, or a patch goes black with no knock you can remember.",
          guard=_the_part_is_a_persons,
          # the wall, the ceiling and the grout go black too, and each of them keeps its own
          # answer; the nail, the eye and the mouth are parts with a row of their own
          avoid=("mould", "mold", "mouldy", "moldy", "damp", "wall", "walls", "ceiling",
                 # a part that has also gone cold, numb or tingly is not a knock: fingers and
                 # toes that go white then blue then numb in the cold are Raynaud's, and feet
                 # that are always cold are circulation. Those keep the answers they had.
                 "numb", "numbness", "cold", "freezing", "tingling", "tingly", "pins and needles",
                 "grout", "sealant", "silicone", "tile", "tiles", "window", "frame",
                 "paint", "paintwork", "plaster", "skirting", "bathroom", "shower",
                 "nail", "nails", "toenail", "toenails", "fingernail", "fingernails",
                 "eye", "eyes", "eyelid", "gum", "gums", "tooth", "teeth", "tongue",
                 "lip", "lips", "mouth", "face", "cheek", "jaw",
                 "dog", "dogs", "puppy", "cat", "cats", "kitten", "vet", "horse",
                 "car", "bike", "boot", "boots", "shoe", "shoes", "sock", "socks",
                 "varnish", "polish", "screen", "phone", "kettle", "sink", "bath",
                 "bin", "bags", "tights", "leggings")),
    # White flecks in a nail are little knocks to the nail bed, not a shortage of calcium, which
    # is what most people have been told. The line is a statement, so it was echoed back: it
    # needs the answer. `nail-ridges` takes lines, ridges and splitting; this takes only the
    # white ones.
    entry("white-spots-nails",
          (("nails", "nail", "fingernails", "fingernail", "toenails", "toenail"),
           ("white spots", "white marks", "white flecks", "white patches", "white lines",
            "white dots", "little white", "spots on my nails", "marks on my nails")),
          "White spots in a nail are usually small knocks to the nail bed while that part of the nail "
          "was "
          "forming, and they grow out over a few months - not a calcium or zinc shortage, which is "
          "what most people are told. Filing the surface will not shift them and nothing needs "
          "doing. White lines across every nail, or half a nail white with a darker band above "
          "it, is worth a GP look.",
          avoid=("tongue", "mouth", "thrush", "fungal", "fungus", "yellow", "black", "blue",
                 "purple", "bruise", "paint", "polish", "varnish", "gel", "acrylic",
                 "dog", "cat", "wall", "paintwork", "fence", "shirt")),
    # Dry skin, hands and heels: the commonest winter complaint, and it had no answer at all.
    # The line is a part plus the state words, so "my skin is dry" answers, and the parts this
    # entry must not take (lips, mouth, eyes, hair) are in AVOID with the home and kitchen
    # meanings of the same word: drying the washing indoors answered "my skin is really dry in
    # winter" until this entry existed.
    entry("dry-skin",
          (("skin", "hands", "hand", "face", "cheeks", "legs", "arms", "elbows", "heels",
            "feet", "knuckles", "body", "moisturiser", "moisturizer", "emollient"),
           # "winter" used to be in this group, and a season is not a state: "how can i keep my
           # hands warm in winter" is a circulation question that this row was taking on the
           # pair "hands" + "winter". A dry skin line always says dry, cracked, itchy or tight.
           ("dry", "drier", "dryness", "flaky", "flakes", "flaking", "cracked", "cracking",
            "cracks", "rough", "itchy", "itching", "tight", "peeling", "chapped")),
          "Dry, tight skin in winter is mostly central heating and long hot showers washing the "
          "oils out: short lukewarm showers, pat dry rather than rub, and a thick unperfumed "
          "cream within three minutes while the skin is still damp. Cracked hands "
          "and heels want a cream with urea or lanolin and cotton gloves overnight. If the cracks "
          "bleed or the skin is red and itchy, a pharmacist can give you an emollient.",
          # the parts whose dry skin is another answer: lips and the corners of the mouth, and
          # the eyes. "washing up" is where dry hands come from, so it must not block them.
          # a child, a partner or a pet has dry skin, and the advice for your own body does not
          # fit: "my dog has dry skin" is the pet answer, "my son has dry skin" is a chat reply
          avoid=("lips", "lip", "mouth", "corner of my mouth", "eyes", "eye", "hair", "dandruff",
                 "my son", "my daughter", "my child", "my kid", "my kids", "my baby",
                 "my toddler", "my husband", "my wife", "my partner", "my mum", "my mom",
                 "my mother", "my dad", "my father", "my friend", "my dog", "my cat", "my puppy",
                 "my horse", "his skin", "her skin", "their skin",
                 # a part that hurts is the strain table's, not this one: "my legs are sore
                 # after the gym" and "my elbow is sore"
                 "sore", "hurts", "hurt", "aching", "ache", "pain", "pains", "painful",
                 "stiff", "injury", "injured",
                 # an egg is not dry skin, and "one handed" put "hand" in the line:
                 # "how do you crack an egg one handed" was getting this answer
                 "egg", "eggs",
                 # a joint cracking is the knuckles answer, not a dry one: "why do my knuckles
                 # crack" and "i crack my knuckles" were both getting the winter-skin advice
                 "knuckles crack", "knuckles cracking", "knuckle cracks", "knuckles click",
                 "knuckles clicking", "knuckles pop", "crack my knuckles",
                 "cracking my knuckles", "crack your knuckles", "cracking your knuckles"),
          guard=_the_part_is_a_persons),
    # A dry, flaky scalp is not the winter-skin answer: central heating and body cream do not fix
    # it, and it is usually dandruff - a yeast that lives on the oils of the head - so it wants a
    # medicated shampoo, not an emollient. `dandruff` in clothing.py answers the word itself; this
    # is the "my scalp is dry and flaky" wording of the same thing.
    # "what temperature should i wash my face with" reached the laundry dial: the face is washed at
    # a temperature like the dishes are, and nothing here said so.
    entry("face-wash",
          (("face", "facial"),
           ("wash", "washing", "washed", "clean", "cleanse", "cleanser", "temperature",
            "how hot", "hot water", "cold water", "lukewarm", "twice a day", "before bed")),
          "Lukewarm water and a gentle unperfumed cleanser, morning and evening: warm water and a "
          "flannel lift grime and make-up, while hot water strips the oils and leaves the skin "
          "tight. Pat dry rather than rub, and put moisturiser on while the skin is still damp; "
          "anything that stings is too harsh for a face.",
          # dry, spotty or itchy skin is its own answer, and so are hands, the body and the wash
          avoid=("dry", "drier", "drying out", "dry out", "dry it out", "itchy", "spot",
                 "spots", "acne", "eczema", "flaky", "cracked",
                 "hands", "hand", "body", "hair", "baby", "child", "dishes", "clothes",
                 "laundry", "mask", "face mask", "beard", "shave", "shaving"),
          bias=2),
    # Hand washing had no card: "how long should i wash my hands for" and "how do i wash my hands
    # properly" were both the search shrug, and "do i need hot water to wash my hands" reached the
    # laundry dial on the word "hot water".
    entry("hands-wash",
          (("hands", "hand", "fingernails", "fingertips"),
           ("wash", "washing", "washed", "clean", "cleaning", "soap", "germs", "bacteria",
            "hygiene", "how long", "before eating", "after the toilet", "after gardening",
            "after diy", "hot water", "cold water", "sanitiser", "hand gel")),
          "Wet your hands, then soap for twenty seconds - about as long as singing Happy Birthday "
          "twice - and cover the backs of the hands, between the fingers, the thumbs and the "
          "fingertips under the nails. Rinse and dry on a clean towel, because wet hands pick up "
          "germs again, and use hand gel only when there is no sink.",
          # dry, cracked, cold, numb or painful hands are their own answers, and so are the
          # things people wash that are not hands
          avoid=("dry", "drier", "cracked", "cracking", "itchy", "eczema", "numb", "tingling",
                 "cold", "warm", "winter", "raynaud", "pain", "hurt", "swollen", "nails",
                 "nail polish", "paint", "oil", "grease", "bleach", "stain", "dishes",
                 "washing up", "laundry", "washing machine", "gloves", "mittens", "dog", "cat",
                 "car", "window", "face", "hair",
                 # A garment washed by hand is the wool or the silk card's: "how do i wash a jumper
                 # by hand" outranked the wool row on "hand" and "wash" and then the arbiter turned
                 # the hand-hygiene reply down, so the line got the shrug. The garment words and
                 # the hand-wash shapes stand this row aside and nothing else does.
                 "jumper", "jumpers", "cardigan", "cardigans", "wool", "woollen", "woolens",
                 # "hand" is the verb in "i handed my notice in": a leaving-work line met the
                 # twenty-seconds-of-soaping card. The job words are not a hand question.
                 "notice", "notice in", "resign", "resigning", "resignation", "job", "boss",
                 "employer", "manager", "contract", "redundancy", "sacked", "promotion",
                 "knitwear", "knitted", "cashmere", "merino", "silk", "silky", "scarf", "scarves",
                 "dress", "dresses", "shirt", "shirts", "blouse", "sweater", "sweaters", "fleece",
                 "by hand", "hand wash", "hand washing", "hand-wash", "handwash", "hand washed",
                 # a hand with a wound on it is a wound question, and the wound cards are the
                 # ones that answer it: "how long do stitches stay in my hand" was twenty seconds
                 # of soaping, because "hand" and "how long" are both this row's words. The
                 # wound nouns only - "justice" to wash hands after cutting raw chicken is still
                 # a hand question, and so is any other verb "cut" can be.
                 "stitches", "stitch", "sutures", "suture", "staples", "wound", "wounds",
                 "gash", "gashes", "scab", "scabs", "bandage", "bandages", "dressing",
                 "dressings", "plaster cast", "graze", "grazes", "open wound", "cut on my hand",
                 "cut on the hand", "cut on my finger", "splinter", "ingrown"),
          bias=3),
    entry("dry-scalp",
          (("scalp", "scalp is", "head itches"),
           ("dry", "drier", "dryness", "flaky", "flakes", "flaking", "itchy", "itching",
            "scaly", "dandruff", "white bits", "snowy")),
          "A dry, flaky scalp is usually dandruff: a yeast that feeds on the oil on your head, so "
          "it is not the same thing as dry skin and body cream will not help it. Wash with an "
          "anti-dandruff shampoo - zinc pyrithione or ketoconazole, from any chemist - two or "
          "three times a week, work it into the scalp and leave it five minutes before rinsing, "
          "and give it a month. Do not scratch the flakes off, and keep washing your hair: a "
          "scalp left greasy feeds it. If it is red, sore, or hair is thinning in patches, see a "
          "pharmacist or your GP.",
          avoid=("hair", "shampoo", "conditioner", "dye", "coloured", "bleach")),
    # Three skin questions that had no answer at all on main: which cream to buy, a face that is
    # oily, and what to do to look after your skin. All three reached a search punt, and "what
    # skincare routine should i have" reached a card about planning the morning by the clock.
    # Choosing a cream is the dry-skin row's neighbour, so it is keyed on the buying words and
    # stands down on every state word that row answers.
    entry("moisturiser",
          (("moisturiser", "moisturizer", "moisturise", "moisturize", "moisturising",
            "moisturizing", "face cream", "day cream", "night cream", "body lotion",
            "face lotion", "skin cream", "cream for my face", "cream for dry skin"),
           ("need", "needs", "should", "what", "which", "choose", "choosing", "best", "use",
            "worth", "buy", "type", "kind", "recommend", "looking for", "how do i", "how to",
            "good", "cheap", "expensive")),
          "A plain unperfumed cream is the whole job: thicker (an ointment, or a cream in a tub) "
          "for dry or flaky skin, a light lotion or gel for oily skin, and one with SPF 30 in it "
          "for the morning if you want to skip a step. Put it on damp skin within three minutes of "
          "a shower, buy the cheap own-brand - the price is packaging - and a pump is cleaner than "
          "a tub you dig your fingers into.",
          # how to treat dry, itchy or cracked skin is the row above, and the states it answers
          # must keep their own card: "how do i get rid of dry skin on my face" is not a shopping
          # question
          avoid=("dry", "drier", "dryness", "flaky", "flakes", "flaking", "cracked", "cracking",
                 "cracks", "rough", "itchy", "itching", "tight", "peeling", "chapped", "sore",
                 "rash", "eczema", "psoriasis", "red", "burning", "sunburn", "sun cream",
                 "sunscreen", "spf", "dog", "cat", "puppy", "baby", "babies", "nappy",
                 "my son", "my daughter", "my child", "my kid", "my kids")),
    # The row is a part of the body plus the state, the way `dry-skin` is, and not a bare
    # adjective. It held "greasy" and "shine" on their own, next to the ask words ("how do i",
    # "stop", "wash"), so "how do i clean a greasy oven" scored exactly as well as "my face is
    # greasy" and a person cleaning their oven was told to wash their face twice a day with a
    # foaming cleanser - and so were a hob, greasy trays and a pair of glasses, none of which is
    # a body. With the part in the key, the state word only counts for a line that says whose
    # face, skin, nose or chin it is, and every line about a thing reaches the cleaning or the
    # garment answer. A bare "greasy" still had to answer "how do i stop my face getting greasy":
    # that line names the face, so it is the part group below that answers it now.
    entry("oily-skin",
          (("skin", "face", "forehead", "nose", "chin", "cheeks", "complexion", "t-zone",
            "t zone", "oily skin", "greasy skin", "shiny skin", "oily face", "greasy face"),
           # the state, and only the state: an ask word here ("how do i", "help", "stop") let
           # the part group score 4 on its own, so "how do i clear my skin" and "how do i stop my
           # nose running" were both answered with the oily-skin routine
           ("greasy", "oily", "oil", "shiny", "shine", "gleam", "getting greasy",
            "gets greasy", "getting oily", "gets oily", "getting shiny", "by lunchtime",
            "during the day")),
          "Wash twice a day with a gentle foaming cleanser rather than soap, which strips the skin "
          "and leaves it making more oil, then use a light oil-free gel moisturiser - oily skin "
          "still needs one. Do not scrub or wash more than twice; blot the shine at lunchtime "
          "instead, and a niacinamide or salicylic acid product is the one extra step worth adding.",
          avoid=("dry", "drier", "flaky", "tight", "rash", "eczema", "psoriasis", "spot",
                 "spots", "spotty", "spotting", "acne", "hair", "scalp", "chip", "chips",
                 # "shine" here is the skin, and "how do i make my stainless steel sink shine" was
                 # answered with a foaming cleanser: the metal and the kitchen are fenced out.
                 "sink", "sinks", "stainless", "stainless steel", "steel", "kitchen",
                 "bathroom", "tap", "taps", "worktop", "cutlery", "silver", "brass", "copper",
                 "metal", "floor", "floors", "window", "windows", "car", "shoes", "leather",
                 "pan", "frying", "food",
                 # a greasy oven, hob or cooker is the cleaning card's, not a face's: the key
                 # holds the bare word "greasy" and "how do i clean" is one of this row's
                 # context words, so "how do i clean a greasy oven" was answered with a
                 # foaming cleanser. The kitchen words are what stands it down.
                 "oven", "ovens", "hob", "hobs", "cooker", "cookers", "grill", "griller",
                 "microwave", "extractor", "tray", "trays", "baking", "roasting", "tin", "tins",
                 "saucepan", "saucepans", "worktop", "worktops", "splashback", "cupboard",
                 "cupboards", "sink", "dishes", "dishwasher", "fridge", "freezer", "kettle",
                 "toaster", "barbecue", "bbq", "wall", "walls", "tiles",
                 # the room, and the other surfaces grease lands on: "how do i clean a greasy
                 # kitchen" is the whole-room card's line
                 "kitchen", "kitchens", "bathroom", "bath", "shower", "floor", "floors",
                 "garage", "surface", "surfaces", "counter", "counters", "unit", "units",
                 "car", "engine", "bike", "chain", "dog", "cat",
                 # a greasy kitchen is a cleaning job with an answer of its own: "how do i clean
                 # a greasy kitchen" was told to wash twice a day with a foaming cleanser,
                 # because the bare "greasy" here plus "how do i" scored over the room routine
                 "kitchen", "kitchens", "hob", "hobs", "cooker", "oven", "worktop", "worktops",
                 "sink", "splashback", "extractor", "floor", "floors", "tiles", "dishes",
                 "cooking", "cooked", "bbq", "barbecue", "grill", "containers", "jars",
                 # a shine on a garment is the fabric's question, not the face's: "how do i get
                 # rid of a shine on a suit jacket" reached this row because the key holds the
                 # bare word "shine", and clothing.py answers the garment
                 "suit", "suits", "jacket", "jackets", "blazer", "blazers", "trousers",
                 "shirt", "shirts", "skirt", "dress", "dresses", "coat", "coats", "sleeve",
                 "sleeves", "elbow", "elbows", "fabric", "leather", "sofa", "settee",
                 "table", "tables", "wooden", "furniture", "cupboard", "chair", "desk",
                 # and a shine you put on shoes is the polish answer's line, not a cleanser's
                 "shoe", "shoes", "boot", "boots", "polish", "polishing", "polished")),
    entry("skin-routine",
          (("skincare", "skin care", "cleanser", "cleansing", "face wash", "glowing skin",
            "skin routine", "face routine", "my skin looks tired", "look after my skin",
            "look after your skin", "good skin"),
           ("what", "which", "should", "how do i", "how to", "choose", "best", "need", "start",
            "simple", "good", "order", "daily", "routine", "use")),
          "Keep it to three steps: a gentle cleanser, a moisturiser, and a sunscreen in the "
          "morning - add one active, a retinoid or an acid, at night only once those three are a "
          "habit. Most routines fail because they are too long, and no jar beats sleep, water and "
          "not smoking.",
          # a spot, a rash and a dry patch are complaints with their own answers, and a child or a
          # pet has skin the routine does not fit
          avoid=("spot", "spots", "spotty", "acne", "blackhead", "blackheads", "dry", "drier",
                 "flaky",
                 "itching", "itchy", "rash", "eczema", "psoriasis", "mole", "wrinkles",
                 "botox", "sunburn", "dandruff", "hair", "foundation", "makeup", "make up",
                 "dog", "cat", "baby", "babies", "nappy", "child", "kid", "kids")),
]

# "my back went" names no hurt word, so the region table never saw it: the part and the verb are
# the whole complaint. The part is spelled "my back" rather than "back", because "i want to back
# out of the deal" is a different sentence with the same two words in it.
BACK_WENT = ("put my back out", "put out my back", "put it out", "threw my back out",
             "threw it out", "my back went", "back went", "my back has gone", "my back is out",
             "my back went out", "my back gave way", "my back locked", "my back is in spasm",
             "my back went into spasm", "i tweaked my back", "i twisted my back", "my back slipped")

# Two halves of the same "how long": "how long does a dentist appointment take" is the length of
# the visit, and "how long does it take to get an appointment", "how long is the wait" are the
# queue. The registering card answered the first with how to find a practice that takes new
# patients, because "taking" is one of the words that errand is written with, so a person booking
# time off work was told to ring round practices.
_THE_VISIT = {"appointment", "appointments", "checkup", "check-up", "check", "visit", "filling",
              "hygienist", "root canal"}
_THE_QUEUE = {"wait", "waits", "waiting", "soon", "sooner", "quickly", "book", "booking",
              "booked", "getting", "seen", "available", "weeks", "days", "months", "list"}
_REGISTERING_A_DENTIST = (
    "Look for practices near you that are taking on new patients, then ring rather than "
    "email: each practice keeps its own list and it opens and closes, and the phone gets "
    "you a straight answer. Ask on the call whether they take NHS adults and how long the "
    "first check-up wait is. If nobody near you has room, ring 111 and ask for the urgent "
    "dental service, which will see you and can tell you who is taking patients.")


# The card answers two errands - join a practice, or be told how long being seen takes - and the
# key was widened so that a visit named by what is being done ("how long does a filling take")
# reaches it. The wider key also matched a line that only *mentions* one of those nouns: "how long
# after a filling can i eat" and "how soon can i eat after a filling" were handed "look for
# practices near you", "it was only a check up last month" was told the length of a check-up, and
# "Can I wait until my checkup in March?" got the wait for a GP appointment. So the card is asked
# only for the two errands: a line that asks how long the visit takes, or a line that asks to
# find or join a practice.
_A_LENGTH_OF_A_VISIT = re.compile(
    r"\bhow long (?:does|do|will|would|should)\b[^?.!]*\b(?:take|last|wait)\b"
    r"|\bhow long (?:is|are|was)\b"
    r"|\bhow many (?:minutes|hours)\b",
    re.I)
# A list said as a fact is a complaint about access, not a question about length: "the dentist
# waiting list is months what can i do" and "i cant get an nhs dentist appointment the waiting
# list is two years" both want what to do about it, and they were left with no card at all when
# the guard only knew the two asks. The list *asked about* ("how long is the waiting list") is
# still a length, and `_the_dentist_errand` sends that half to the queue.
_A_LIST_THAT_IS_LONG = re.compile(
    r"\bwaiting list\b|\bon the list for\b|\blist is (?:months|years|weeks|long|closed)\b",
    re.I)
_A_PRACTICE_ERRAND = re.compile(
    r"\b(?:register|registering|sign up|join|join up|find|finding|accepting|new patients?|"
    r"taking (?:on )?(?:new )?patients?|need (?:a|an|an nhs|a new) dentist|get a dentist|"
    r"looking for a dentist|near me|nearby|local dentist|none|no dentist|moved)\b", re.I)


# The card answers how long being seen takes. It does not answer how long it takes to *be* one:
# "how long does it take to become a dentist" carries "how long does ... take" and the word
# dentist, so this card took it and told the person the length of a check-up. The training is
# years and it has its own row in `study.py`, so a line about becoming, training, studying or
# qualifying stands this card down.
_A_BECOMING_A_DENTIST = re.compile(
    r"\b(?:become|becoming|train as|training as|study|studying|degree|qualify as|qualifying as|"
    r"career|became)\b[^?.!]*\b(?:dentist|dentistry|dental school|dental surgeon)\b"
    r"|\b(?:dentist|dentistry|dental school|dental surgeon)\b[^?.!]*"
    r"\b(?:training|course|degree|qualify|career|school)\b", re.I)


def _an_errand_the_dentist_card_answers(understood):
    """True when the line asks how long a visit takes, or asks to find or join a practice."""
    reading = understood if isinstance(understood, dict) else {}
    said = str(reading.get("clean") or reading.get("text") or "")
    if _A_BECOMING_A_DENTIST.search(said):
        return False
    if _A_PRACTICE_ERRAND.search(said) or _A_LIST_THAT_IS_LONG.search(said):
        return True
    return bool(_A_LENGTH_OF_A_VISIT.search(said))


# The visit is not one length: a check-up is 15 to 20 minutes, a filling 20 to 30, a root canal
# 45 minutes to an hour, a clean with the hygienist about 30, and a crown two visits of about an
# hour. Each is written as what the thing *takes*, not as a label on it - a reply is read a part
# at a time, and "A filling is a 20 to 30 minute slot" came back to a follow-up as "20 to 30
# minute.", an attributive with its noun cut off. The part the line named is said first: "how
# long does a filling take" opens on the filling, not on the check-up that happens to be written
# before it, because the answer the person asked for belongs in the first sentence.
_A_CHECK_UP = ("A check-up with a dentist is booked for about 15 to 20 minutes, and a first "
               "visit to a practice often gets half an hour because they take an X-ray and a "
               "history.")
_A_FILLING = "A filling takes 20 to 30 minutes."
_A_ROOT_CANAL = "A root canal takes 45 minutes to an hour."
_A_HYGIENIST = "A clean with the hygienist takes about 30 minutes."
_A_CROWN_VISIT = ("A crown is two visits of about an hour each, one to shape the tooth and one "
                  "to fit it.")
_AN_IMPLANT = ("An implant is two short visits and a long wait in between: about an hour to "
               "place it under the gum, three to six months for the bone to take to it, then "
               "about an hour to fit the crown on top.")
_THE_BOOKING = ("Say what it is for when you book, and ask for a double appointment if you have "
                "more than one thing to look at, so the slot fits.")
_THE_VISIT_IN_ORDER = (_A_CHECK_UP, _A_FILLING, _A_ROOT_CANAL, _A_HYGIENIST, _A_CROWN_VISIT)


def _the_lengths_of_the_visit(said, words):
    """Every length the visit has, with the one the line named in the first sentence."""
    named = []
    if words & {"filling", "fillings"}:
        named.append(_A_FILLING)
    if words & {"canal"} or "root canal" in said:
        named.append(_A_ROOT_CANAL)
    if words & {"hygienist", "hygienist's", "clean", "cleaning"}:
        named.append(_A_HYGIENIST)
    if words & {"crown", "crowns"}:
        named.append(_A_CROWN_VISIT)
    # An implant is longer than anything else here and is not one appointment, so it is only said
    # when the line names it - every other visit line keeps the order it had.
    if words & {"implant", "implants"}:
        named.append(_AN_IMPLANT)
    # A crown that was asked about "taking" is the two visits, and that is the only crown length
    # here; a bare "how long does a crown take" reaches this same arm through `a_crown`.
    parts = named + [part for part in _THE_VISIT_IN_ORDER if part not in named]
    return " ".join(parts + [_THE_BOOKING])


def _the_dentist_errand(memory, understood):
    """The length of a dental visit, or the wait for one, when that is what was asked.

    The card is the one that wins "how long ... dentist", and this line has three different
    questions in it. "How long does a dentist appointment take" is the visit, and it was answered
    "look for practices taking on new patients" - a hunt for a practice, because "taking" is a
    word the registering answer is written with. "How long is the wait for a dentist", "how long
    does it take to get a dentist appointment", "how long until i can see a dentist" and "how
    soon can i get a dentist appointment" and "how long do dentists take to see you" are the wait,
    and a wait is what `_book_the_appointment`
    already knows how to answer in the words of the place named (it answers the GP half of this
    exactly). "How do i register with a dentist" is neither, and keeps the registering answer.
    """
    words = set(_line_words(understood))
    said = str(understood.get("clean") or understood.get("text") or "").lower()
    # The subject of the line does not have to be spelled with the word "dentist": "how long does
    # a filling take", "how long is a check up" and "how many minutes is a hygienist appointment"
    # never say it, and every one of them was answered with how to find a practice.
    #
    # Two kinds of noun ask two different lengths, and the verb says which. An occasion - an
    # appointment, a check-up, a visit, a hygienist's clean - lasts 15 to 20 minutes: "how long
    # does an appointment last" and "how long does an appointment take" are the same question. A
    # thing done to a tooth - a filling, a root canal, a crown - *takes* 20 to 60 minutes but
    # *lasts* five to fifteen years, so only "take" is the visit there and "last" stays the
    # durability answer's.
    occasion = words & {"appointment", "appointments", "checkup", "check-up", "check", "visit",
                        "hygienist", "hygienist's"}
    done_to_a_tooth = words & {"filling", "fillings", "crown", "crowns", "canal"} or (
        "root canal" in said) or ("check up" in said)
    the_place = words & {"dentist", "dentists", "dental", "orthodontist", "tooth", "teeth",
                         "practice", "surgery"}
    how_long = re.search(r"\bhow (?:long|many (?:minutes|hours))\b", said)
    takes = words & {"take", "takes", "taking"}
    lasts = words & {"last", "lasts"}
    # The wait is asked with "see", "to get", "wait", "soon": those are never the visit's length,
    # and registering is the one errand that is not a visit.
    the_wait = bool(words & (_THE_QUEUE | {"see", "seen"}) or "to get" in said)
    registering = bool(words & {"register", "registering", "sign up", "join"})
    # A thing done to a tooth lasts years and that is a different answer from the visit's: "how
    # long does a crown last" is not how long the fitting takes, and the line has no "take" in it
    # to say so. The filling half of this is the lifespan card's; the crown half is here.
    a_crown = bool(words & {"crown", "crowns"})
    if a_crown and lasts and not takes and not the_wait and not registering:
        return (
            "A crown lasts ten to fifteen years on average, and some go much longer. What wears "
            "it out is usually the tooth and the gum under it rather than the crown itself, so "
            "keep cleaning round the edge where it meets the gum, and tell the dentist if it "
            "starts to feel loose or the gum bleeds when you floss.")
    a_visit = ((occasion and (how_long or takes or lasts))
               or (done_to_a_tooth and (takes or re.search(r"how many (?:minutes|hours)", said)))
               or (the_place and how_long and (takes or lasts)))
    if a_visit and not the_wait and not registering:
        return _the_lengths_of_the_visit(said, words)
    # A wait is a question the appointment card already answers, in the words of the place named:
    # one answer, in one place, for every wording that asks how long until you are seen.
    # The list said as a fact is the access errand: they know the wait is long and are asking
    # what to do about it, so the registering answer is the one, not the length of the queue.
    if _A_LIST_THAT_IS_LONG.search(said) and not how_long:
        return _REGISTERING_A_DENTIST
    if words & (_THE_QUEUE | {"see", "seen"}) or "to get" in said:
        return _book_the_appointment(memory, understood)
    return _REGISTERING_A_DENTIST


ENTRIES = [
    entry("back-went",
          (("my back", "lower back", "my spine"),
           ("went", "gone", "put", "out", "threw", "twisted", "tweaked", "slipped", "locked",
            "spasm", "gave way", "went out", "is out",
            # The present tense and the seizing were a gap: "what should i do when my back goes",
            # "if my back goes what should i do", "my back goes if i lift anything", "my back
            # goes every few months", "my back seizes up" and "my back seized up this morning"
            # were punts or "I'm listening", while the same complaint in the past tense
            # ("my back has gone", "my back went") had the answer all along. The first group
            # still has to carry "my back", so a bare "go" cannot reach here from another
            # sentence, and every red flag word (numb, cant pee, both legs) is still in `avoid`
            # and still gets the same-day card.
            "goes", "go", "going", "seize", "seizes", "seized", "seizing",
            # the phrasings that carry the doing rather than the hurting: "ive done my back in",
            # "i pulled my back", "my back's gone". Phrases, because "gone" and "pulled" alone
            # belong to other sentences: "my money's gone", "pulled a muscle in my arm".
            "done my back in", "done my back", "pulled my back", "back has gone", "backs gone",
            "back went", "in spasm")),
          "A back that goes like that is almost always a muscle strain, and it is at its worst in "
          "the first day or two: keep moving gently rather than taking to your bed, take "
          "paracetamol or ibuprofen if you can, and use a hot water bottle on the tight part. Most "
          "settle in two to six weeks. Ring 111 today if you cannot pass urine, have numbness "
          "between your legs, or the pain came on after a fall, and see a GP if it is no better in "
          "a fortnight.",
          # the red flags and a back that hurts when breathing are body-urgent and body-see-today,
          # and the rest of the avoid list is the region table's: a back that went is still not a
          # stomach ache, a toothache or somebody else's back
          # everything the region table avoids, except the next-day exercise words: a back that
          # went at the gym is this entry's, not sport.sore-after-exercise's
          avoid=tuple(w for w in AVOID if w not in EXERCISE_DAY)
          + ("deal", "contract", "wedding", "booking", "order", "offer", "agreement", "mortgage",
             "pull out", "pull out of", "going ahead", "hire purchase",
             # "my back goes stiff in the morning" is the slow stiff back the region card
             # answers, not a strain that has just happened: the stiffness words stand this
             # row down, and "this morning" does not, because "my back seized up this morning"
             # is the one that just happened.
             "stiff", "stiffness", "stiffened", "stiffens", "stiffening")),

    # A ring that will not come off is a hand problem, not a hob to wipe clean: the line was
    # reaching the cleaning table from "ring" plus "how". The ask is the ring itself, so no
    # ordinary ache can land here.
    entry("ring-stuck",
          (("ring", "rings", "wedding ring", "engagement ring", "band"),
           ("stuck", "swollen finger", "swollen", "off my finger", "off", "wont come off",
            "won't come off", "cut off", "tight", "too tight", "trapped")),
          "Work it off with soap and water or a little oil, twisting rather than pulling, hand "
          "raised above your head for a few minutes first to let the swelling go down. Wind a "
          "piece of thread or dental floss under the ring from the finger side and unwind it "
          "around the finger past the knuckle, tucking the ring along a loop at a time. Get help "
          "the same day if the finger goes numb, cold or blue: A&E or a jeweller can cut it off.",
          avoid=("hob", "cooker", "burner", "stove", "bath", "curtain", "doorbell", "bell",
                 "phone", "answering", "ear", "ears", "nose", "nose ring", "earring", "earrings",
                 "sound", "sounds", "noise", "circle", "tree",
                 "bite", "bites", "bitten") + RING_NOT_ON_A_FINGER,
          # the ring is the whole subject of the line, so it outranks the sprain entry that
          # shares "swollen" and "finger"
          bias=2,
          ask=("ring", "rings")),
    entry("piercing-healing",
          # "how long does a pierced ear take to heal" and "new ear piercing aftercare" were both
          # a search hedge, and the answer is two numbers and a cleaning routine.
          (("piercing", "piercings", "pierced ear", "pierced ears", "ear piercing",
            "ear piercings", "nose piercing", "septum", "belly piercing", "belly button piercing",
            "cartilage piercing", "helix", "tragus", "daith", "industrial piercing",
            "lip piercing", "eyebrow piercing", "nipple piercing", "new piercing",
            # the thing in the hole, which is how most people say it: "how long does a nose ring
            # take to heal" is the same question as "how long does a nose piercing take"
            "nose ring", "nose rings", "septum ring", "nose hoop", "ear hoop", "hoop earring",
            "nose stud", "stud earring", "ear stud", "belly bar", "ring in my nose",
            "ring in my ear"),
           ("how long", "heal", "heals", "healing", "take to heal", "sore", "red", "swollen",
            "aftercare", "clean", "cleaning", "clean it", "care", "infection", "bump", "keloid",
            "crusty", "weeping", "swimming", "sleep on", "change the jewellery", "take it out",
            # changing it is the second half of the same question, and "change" alone missed
            # "when can i change my nose ring"
            "when can i change", "change it", "changing it", "swap it", "downsize", "shorter bar")),
          _piercing_healing,
          guard=_a_healing_piercing_not_a_troubled_one,
          # "how long does a nose ring take to heal" and "when can i change my nose ring" were
          # lost to the bare "ring" in this advance: a nose ring, a septum ring, a hoop, a barbell
          # and a stud are how people say the same question. The key needs a piercing word, so a
          # finger ring cannot reach this row anyway - the homographs are what has to be fenced.
          avoid=("earring", "earrings", "ear ring", "tongue", "clit", "industrial estate",
                 "helix nebula", "engagement ring", "wedding ring", "ring finger", "ring main",
                 "ring final", "hob ring", "onion ring", "boxing ring", "circus ring",
                 "key ring", "keyring", "napkin ring", "curtain ring", "smoke ring")),
    # The finger has already lost its blood supply, so the move changes: this one leads with
    # getting it cut off rather than with soap.
    entry("ring-stuck-blue",
          (("ring", "rings", "wedding ring", "engagement ring", "band"),
           ("gone blue", "turning blue", "blue", "cold", "black", "cutting in", "cut into")),
          "Get it off today, and get help if you cannot: a finger that has gone numb, cold, blue or "
          "black behind a ring needs the ring cut off, so go to A&E or ring 111 and they will tell "
          "you where. While you wait, keep the hand raised above your heart and run it under cool "
          "water, and do not keep twisting the ring. A jeweller can cut it off for a few pounds if "
          "the finger still looks normal.",
          # "cold" and "ring" are a caller's words too, and "cold callers keep ringing" was sent
          # this finger card: a telephone that rings is never a ring on a finger. Not "ringing",
          # though - an avoid word is read as a form of the words in the key, so it would stand
          # this card down for "my ring is cutting in" as well.
          avoid=("hob", "cooker", "burner", "stove", "bath", "curtain", "doorbell", "bell",
                 "phone", "answering", "ear", "ears", "nose", "sound", "circle",
                 "caller", "callers", "cold call", "cold calls", "nuisance", "spam",
                 "robocall", "robocalls", "unknown number",
                 "tree", "bite", "bites", "bitten") + RING_NOT_ON_A_FINGER,
          bias=4,
          ask=("ring", "rings")),
    # --- which service, for a thing that is not an emergency -----------------
    # Registering is paperwork, and the understanding engine calls the line health, so the
    # entries live here: a domain that does not answer the topic never gets asked.
    # "how do i register with a dentist" was getting the toothache answer, which is the wrong
    # errand: nobody in pain is asking how to join a practice. The key is the errand, and the
    # pain words stand this entry down so the dentist-on-the-day answer keeps those lines.
    entry("register-dentist",
          (("dentist", "dental practice", "dental surgery", "nhs dentist", "orthodontist",
            # the card is the one that holds the three times - the visit's length, the wait,
            # and the answer that registering keeps - so every shape that asks for one has to
            # reach it. A visit is named by what is being done: "how long does a filling take"
            # was going to a paint card, "how many minutes is a dentist appointment" to a
            # pay-rate card, and "how long does a dentist appointment last" to nothing at all.
            # A word that means the appointment itself is not added here: "appointment" is a key
            # in half this domain, and another entry's key weight is read from how rare its words
            # are in the domain, so a broad word here quietly took a point off the booking card
            # ("can i get an emergency dentist appointment" moved to the weekend-toothache card).
            # The visit is named by what is being done, or by the word doctor's line already has.
            "filling", "fillings", "root canal", "hygienist", "check up", "check-up",
            "checkup",
            # A crown is the one thing done to a tooth with two visits in it, and the card that
            # holds the times did not know the word: "how long does a crown take" went to a
            # card about rates. The guard keeps the paint and the moulding out (see
            # `_an_errand_the_dentist_card_answers`), which is why the word can be here.
            "crown", "crowns",
            # "how long does a dental appointment last" says dental and not dentist, and a bare
            # "appointment" here moved the booking card's weight (see above), so the adjective is
            # the word that has to be there
            "dental"),
           ("register", "sign up", "join", "find", "accepting", "new patients", "new patient",
            "taking patients", "patients", "taking", "on the list", "no dentist", "need a dentist",
            "looking for", "get one", "get a dentist", "near me", "nearby", "local", "none",
            "waiting",
            # and the ask that wants a length: "how long does a dentist appointment last",
            # "how long does an appointment at the dentist take", "how many minutes is a check
            # up", "how soon can i get seen". `_the_dentist_errand` reads which half it is.
            "how long", "how soon", "how many minutes", "last", "lasts", "take", "takes",
            "wait", "waits")),
          _the_dentist_errand,
          guard=_an_errand_the_dentist_card_answers,
          avoid=("toothache", "tooth", "teeth", "pain", "hurts", "hurting", "agony", "bleeding",
                 "abscess", "swollen", "broken", "chipped", "knocked out", "emergency", "today",
                 "child", "children", "kid", "kids", "baby", "toddler", "in pain", "wisdom",
                 # the answer names the NHS and 111, so a line about a dentist on holiday is
                 # not this one
                 "abroad", "holiday", "holidays", "travelling", "traveling", "expat", "spain",
                 "france", "greece", "turkey", "portugal", "america", "usa", "thailand",
                 "croatia", "italy",
                 # signing up is not complaining about care: the complaint entry owns those
                 # lines, and "nhs" made this one answer "complain about an nhs dentist"
                 "complain", "complaining", "complaint", "complaints"),
          # the errand is the line's subject, and "after moving" must not hand it to the
          # change-of-address entry, which shares no subject with it
          bias=2),
    entry("register-gp",
          (("gp", "doctor", "doctor's", "doctors surgery", "doctors practice", "health centre",
            "medical centre", "surgery", "nhs"),
           ("register", "sign up", "join", "find", "new patient", "new patients", "on the list",
            "taking patients", "moved", "just moved", "change", "switch", "another", "different",
            "near me", "nearby", "local")),
          "Ring the surgeries near your new address and ask if their list is open: most take "
          "people from their own area, and a practice can say no if you live outside it, so try "
          "the next one rather than arguing. Take photo ID and something with the new address to "
          "the first appointment. If you are on regular medicine, ask for the repeat prescription "
          "to be set up that week, and tell them you have just moved so the old notes are asked "
          "for.",
          avoid=("appointment", "appointments", "refer", "referral", "sick note", "fit note",
                 "ignored", "dismissed", "sent me away", "waiting list", "results", "test"),
          bias=2),


# Becoming a dentist is years, and the visit card answered it with the length of a check-up
# because the line holds "how long does ... take" and the word dentist. The card now stands down
# (see `_A_BECOMING_A_DENTIST`), and this row is the answer underneath it, in the domain that owns
# the word: the person asked how long the training is, not how long the chair takes.
] + ENTRIES

ENTRIES.append(entry(
    "a-dentist-career-length",
    (("become a dentist", "becoming a dentist", "be a dentist", "train as a dentist",
      "training as a dentist", "study dentistry", "studying dentistry", "dentistry degree",
      "dental school"),
     ("how long", "how many years", "years", "long does it take", "long does it")),
    "Five years at dental school, then a year of dental foundation training in a practice "
    "before you can work on your own, so six years from starting to being paid as a dentist. "
    "The entry grades are the thing that decides it: A-level chemistry and biology are wanted by "
    "most schools, and the UCAT test plus an interview come before any offer.",
    # the visit, the pain and the booking are the other cards in this domain
    avoid=("toothache", "tooth", "teeth", "pain", "hurts", "emergency", "check up", "check-up",
           "filling", "crown", "root canal", "hygienist's", "appointment", "cost", "much",
           "how much", "salary", "paid", "pay", "worth it", "nhs"),
    bias=3))


# The other half of an everyday ache: which painkiller, and can I take it with the other one.
# Every one of these lines reached the pharmacist deflection ("a pharmacist or your GP can answer
# that today") or the search hedge, which is a shrug for questions with a settled, safe answer -
# two painkillers that work differently, and the two situations where the choice is made for you.
# The drug names are the key rather than "can i take", so a line about any of these medicines
# lands here; overdose, an allergic reaction and a child's dose stay with the modules that own
# them (child-medicine, safety).
def _what_can_i_take_pregnant_or_feeding(memory, reading):
    """The same answer with the half the line asked about first.

    "what can i take while breastfeeding" opened "In pregnancy, paracetamol..." and never said
    what to take instead of a feed, so the first sentence answered a question nobody asked.
    """
    words = set(reading.get("words") or ())
    feeding = bool(words & {"breastfeeding", "breast", "feeding", "nursing", "chestfeeding"})
    pregnant = bool(words & {"pregnant", "pregnancy", "expecting", "trimester"})
    if feeding and not pregnant:
        return ("Paracetamol and ibuprofen are both fine while you are breastfeeding; avoid "
                "aspirin and go easy on codeine. Heartburn takes an antacid like Gaviscon, "
                "own-brand is the same. A pharmacist will check anything else for free, and see "
                "your GP if it lasts days rather than hours.")
    return ("In pregnancy, paracetamol at the lowest dose that works, for the shortest time, and "
            "no ibuprofen - especially after 20 weeks - or aspirin unless a doctor prescribed it. "
            "While breastfeeding, paracetamol and ibuprofen are both fine; avoid aspirin and go "
            "easy on codeine. Heartburn takes an antacid like Gaviscon, own-brand is the same. A "
            "pharmacist will check the rest, and ring your midwife if it lasts days or comes with "
            "bleeding or less movement.")


_DRUGS = ("paracetamol", "ibuprofen", "nurofen", "co codamol", "co-codamol", "co codrydamol",
          "codeine", "aspirin", "painkiller", "painkillers", "calpol", "neurofen")

# "Can I take two at once" is already answered by science.py's painkillers-together, so this
# block owns the three questions it does not: which of the two, how much of it, and whether it is
# safe while pregnant or feeding.
ENTRIES += [
    entry("painkillers-pregnancy",
          (_DRUGS,
           ("pregnant", "pregnancy", "expecting a baby", "expecting", "weeks pregnant",
            "trimester", "while im pregnant", "having a baby")),
          "Paracetamol is the one to use in pregnancy: the lowest dose that works, for as short a "
          "time as you can. Avoid ibuprofen, especially after 20 weeks, and don't take aspirin "
          "unless a doctor has prescribed it for you. For anything else - a headache that keeps "
          "coming back, heartburn, a bad back - ask your midwife or a pharmacist, who will check "
          "it against your stage.",
          avoid=("overdose", "overdosed", "took too much", "whole packet", "allergic",
                 "reaction", "child", "kid", "baby is", "my baby", "son", "daughter",
                 "dog", "cat")),
    entry("painkillers-breastfeeding",
          (_DRUGS,
           ("breastfeeding", "breast feeding", "nursing", "feeding my baby", "chestfeeding",
            "while im feeding")),
          "Paracetamol and ibuprofen are both fine while you are breastfeeding - ibuprofen is the "
          "one usually suggested for pain with swelling, taken with food. Avoid aspirin, and go "
          "easy on co-codamol and other codeine tablets, which can make a baby drowsy. Check what "
          "else is in any cold remedy you take, and a pharmacist will check anything else for "
          "free.",
          avoid=("overdose", "overdosed", "took too much", "whole packet", "allergic",
                 "reaction", "son", "daughter", "dog", "cat")),
    entry("what-can-i-take-pregnant-or-feeding",
          (("what can i take", "can i take anything", "is there anything i can take",
            "anything safe", "is it safe to take", "what can i have", "whats safe to take",
            "whats safe"),
           ("pregnant", "pregnancy", "expecting", "weeks pregnant", "trimester", "while im pregnant",
            "breastfeeding", "breast feeding", "nursing", "while im feeding")),
          _what_can_i_take_pregnant_or_feeding,
          # "what can i take" plus a pregnancy word is enough to reach this entry, so every
          # question that has its own answer stands it down: an antacid for heartburn, the
          # sickness tablets, a laxative for constipation, and the class of drug named.
          avoid=_DRUGS + ("antibiotic", "antibiotics", "heartburn", "indigestion", "reflux",
                          "antacid", "gaviscon", "sickness", "nausea", "vomiting",
                          "constipation", "laxative", "hayfever", "hay fever",
                          "antihistamine", "antihistamines", "thrush", "uti")),
    # Which of the two, and how much of it. Both are asked in a handful of words and both had the
    # pharmacist deflection, which is a shrug to a question with a printed answer on the packet.
    entry("painkillers-which-one",
          (("paracetamol or ibuprofen", "ibuprofen or paracetamol",
            "paracetamol and ibuprofen which", "which painkiller", "which is better paracetamol",
            "which one is better ibuprofen", "ibuprofen or paracetamol for a headache"),
           ("which", "better", "or", "should", "for a", "vs", "versus")),
          "Ibuprofen suits pain with swelling or inflammation - a sprain, period pain, toothache - "
          "taken with food. Paracetamol suits a plain headache or a temperature, and it is the one "
          "to use if ibuprofen upsets your stomach, you are pregnant, or you take a blood thinner. "
          "If one alone is not enough they can be taken together, on their own schedules.",
          avoid=("stomach", "ulcer", "kidney", "asthma", "blood thinner", "warfarin",
                 # the tablets have rows of their own for the stomach, the blood, sleep, drink
                 # and how fast they work, and this card answers which of the two to take
                 "alcohol", "drink", "drinking", "beer", "wine", "pint", "hangover",
                 "sleepy", "drowsy", "thin your blood", "how long",
                 "overdose", "took too much", "child", "kid", "baby", "dog", "cat",
                 "pregnant", "breastfeeding", "allergic", "hangover", "period pain not",
                 "newborn", "newborns", "new born", "neonate", "infant",
                 "month old", "months old", "week old", "weeks old")),
    entry("painkillers-dose",
          (_DRUGS,
           ("how much", "how many", "how often can i take", "dose", "dosage", "maximum",
            "max", "safe amount", "a day", "per day", "in 24 hours", "at a time")),
          _dose_for_the_drug_named,
          # An adult's dose is not a smaller person's. "how much calpol for a newborn" was
          # answered "two 500mg paracetamol tablets, four times in 24 hours" - an adult's day,
          # handed to a baby under three months, where paracetamol is a doctor's decision and
          # ibuprofen is not used at all. Anything under about three months stands down here
          # and family.py's medicine-under-three-months answers instead.
          avoid=("child", "kid", "baby", "toddler", "year old", "son", "daughter",
                 # a dose asked for someone else is not my own maximum: "my sun needs calpol,
                 # how much do i give him" is a parent's line and one known-word typo is all it
                 # takes to lose "son", so the give-to and the child brands stand this row down
                 "calpol", "calprofen", "nurofen for children", "childrens", "children's",
                 "junior", "give him", "give her", "give them", "give my", "shall i give",
                 "can i give", "do i give", "for my son", "for my daughter", "for my baby",
                 "dog", "cat", "overdose", "overdosed", "took too many", "too many",
                 "whole packet", "pregnant", "pregnancy", "breastfeeding", "allergic",
                 "reaction", "how many days", "how long can i take",
                 "newborn", "newborns", "new born", "neonate", "neonates", "infant",
                 "infants", "month old", "months old", "week old", "weeks old",
                 "under 3 months", "under three months", "breastfed", "formula fed")),
    # Swelling in pregnancy. The pre-eclampsia card in safety.py owns the swelling that is a
    # sign - the face, the hands - and its comment keeps the feet and ankles out on purpose,
    # because they swell anyway by the third trimester. What nobody owned was the question
    # itself: "im 30 weeks pregnant and my ankles are a bit swollen" was answered about a
    # sprained ankle, and "39 weeks pregnant and my feet are swollen" about running shoes.
    # So this is not the 999 card; it is the ordinary answer with the two red flags in it - a
    # clot in one leg, and the swelling that comes on suddenly or with a headache, which is
    # the pre-eclampsia card's own subject and goes to it, not here.
    entry("pregnant-swollen-ankles",
          # Three groups, and the swelling is one of them on its own: a row that took a part
          # OR a swelling word for its first group answered "im pregnant and my toes are numb"
          # and "im pregnant and my feet hurt" with the swelling card.
          #
          # "puffy" and its forms are left to body-see-today: they are that entry's rarest key
          # words, and a second entry asking for them took "my hands have been puffy for a
          # week" off its own answer. The swelling words here are enough to catch the lines.
          (_PREGNANCY_SWELLING, _PREGNANCY_SWELLING_PARTS, _PREGNANCY_WORDS),
          _PREGNANCY_SWELLING_REPLY,
          avoid=_PREGNANCY_SWELLING_AVOID,
          # A nudge, because the sprain and the fluid rows match an ankle line word for word:
          # "30 weeks gone and my ankles are swollen" reached the sprain card on "ankle" and
          # "weeks", and the pregnancy reading is the one that knows which swelling is checked.
          bias=6,
          # The words the row is about have to be said: a key group only nudges the score, so
          # without this every swelling with a part in it was the pregnancy answer.
          guard=_names_a_pregnancy),
    # The same answer for the line that gives its dates in weeks and never says the word:
    # "im 30 weeks and my ankle swelled up suddenly on one side" was answered with the sprain
    # card - ice it, rest it, better in six weeks - for one ankle that swelled suddenly in the
    # third trimester, which is the clot shape. Its own row, because the row above wants the
    # word pregnancy in the line and this one has only a figure.
    entry("pregnant-swollen-ankles-in-weeks",
          _PREGNANCY_SWELLING + _PREGNANCY_SWELLING_PARTS,
          _PREGNANCY_SWELLING_REPLY,
          avoid=_PREGNANCY_SWELLING_AVOID,
          bias=6,
          shape=(_a_figure_in_weeks,),
          guard=_dates_a_pregnancy_in_weeks),
]

def _bare_words(line):
    """The words of a line as typed, for reading one of the last few turns back."""
    return [w for w in re.findall(r"[a-z']+", str(line or "").lower()) if len(w) > 2]


# What makes a turn a tooth turn: the thing that is wrong, not the place it was seen.
TOOTH_WORDS = {"tooth", "teeth", "toothache", "filling", "fillings", "crown", "crowns",
               "extraction", "extracted", "gum", "gums", "denture", "dentures", "wisdom",
               "brace", "braces", "root canal", "enamel", "abscess", "chipped", "chipped tooth"}

# ...and what makes a turn a turn about being seen, so "can i book the dentist" two lines back
# still sends the next booking to the practice, while "i went to the dentist last week" does not.
SEEN_ABOUT_IT = {"book", "booking", "booked", "appointment", "appointments", "ring", "ringing",
                 "call", "phone", "see", "seen", "register", "registering", "register", "get in",
                 "joined", "joining", "new", "urgent", "emergency", "pain", "hurts", "hurting"}


def _book_the_appointment(memory, understood):
    """The steps to being seen, in the words of the place the line names.

    The card opened on "8am for most GP surgeries", and a question about the dentist kept that
    first sentence: "how do i book a dentist appointment" and "can i get an emergency dentist
    appointment" were told to ring a GP surgery at eight, and the dentist came later in the
    paragraph, after advice that did not apply to a tooth. The steps are the same - ring when the
    lines open, say what it is for, ask about cancellations - so the same card answers both, with
    its opening, its fallback and its pain advice written for the place the person named.
    """
    words = set(_line_words(understood))
    places = {"dentist", "dentists", "dental", "orthodontist"}
    doctors = {"doctor", "doctors", "gp", "gps", "surgery", "practice", "clinic", "nurse"}
    named = words & places
    if not named and not words & doctors:
        # "how do i book an appointment" a line after a dentist chat is still about the dentist:
        # the place named in the line wins, and with none named the turn just before is read.
        # The turn before, not the last four - a dentist mentioned a few turns back is not what
        # the chat has moved on to ("i went to the dentist last week" / "my back has been sore" /
        # "i cant lift my arm" / "how do i book an appointment" is a back, and the GP is right) -
        # and it is read for the thing itself, not for the word: a tooth, a filling, or a dentist
        # the person is booking with. "i went to the dentist last week" is a report.
        before = []
        turns = (memory.get("turns") or []) if isinstance(memory, dict) else []
        for turn in turns[-1:]:
            if isinstance(turn, dict) and isinstance(turn.get("user"), str):
                before.extend(_bare_words(turn["user"]))
        before = set(before)
        if before & TOOTH_WORDS:
            named = before & places or {"dentist"}
        elif before & places and before & SEEN_ABOUT_IT:
            named = before & places
    # "how long does it take to get an appointment" is the same card asked for a different half of
    # it: the practice is right, the urgent slot is not. The wait is what that line wants, and a
    # card that answers "ask for an urgent slot" to it sends a person with a routine check-up to
    # ring as if it hurt.
    if words & {"long", "soon", "quickly", "wait", "waits", "waiting", "weeks", "days"}:
        if named:
            return (
                "Ask what the wait is when you ring: a routine dental check-up is usually a few "
                "days to a couple of weeks, depending on the practice, and a tooth that hurts is "
                "seen the same day or the next because most practices keep a few slots back each "
                "morning. Ring at opening time for one of those, and 111 can name an urgent NHS "
                "dentist if yours has nothing for days.")
        return (
            "Ask what the wait is when you ring: a routine GP appointment is usually a few days to "
            "a couple of weeks, and anything urgent is seen the same day because surgeries keep "
            "slots back each morning for it. Ring at the moment the lines open for one of those, "
            "and 111 can find an urgent dentist or a walk-in centre if your surgery has nothing.")
    if named:
        return (
            "Ring the dental practice as soon as it opens and ask for an urgent slot: most keep a "
            "few back each morning, and saying it hurts, or that a tooth has broken or a filling "
            "has come out, is what gets you one of them. Ask what they have sooner if the wait is "
            "weeks, and ring 111 for the out-of-hours dental service if your practice is shut or "
            "cannot see you within a few days - they can also name an urgent NHS dentist. Until "
            "then paracetamol or ibuprofen at the dose on the pack, and a pharmacist can help you "
            "hold on.")
    return (
        "Ring at the moment the lines open - 8am for most GP surgeries - and ask for the first "
        "appointment of the day: same-day slots go in the first half hour. Say in one sentence "
        "what it is for, because \"I need it looked at today\" books faster than \"I was "
        "wondering\", and ask to go on the cancellation list if the wait is weeks. Dentists are "
        "the same: say it hurts and ask what they have sooner, and 111 can find an urgent NHS "
        "dentist if yours cannot see you within a few days. If there is nothing at all, ask which "
        "day the next slots are released and whether the duty doctor can ring you back, and "
        "remember a pharmacist can treat a lot of everyday things the same day.")


# Nobody forgets that they want the appointment; what they ask is how to get one this week.
# Two words of the appointment are not enough on their own - "i have a dentist appointment at 3"
# is a fact - so the booking verb has to be there too.
# "should i see a doctor" is a decision, and the booking script is the answer to a person who
# has already decided: the steps to being seen, "ring when the lines open". The part entries and
# the decision rule answer the decision, and where they stand down - the ache a day or two after
# new work steps out of the rule on purpose - the person still got "ring at 8am" for a question
# they had not answered. So the booking card answers only a line that is about the booking: an
# ask and nothing about how to get one is the decision question.
_DECISION_ASK = re.compile(
    r"\b(?:should|shall|do|would|could)\s+i\b[^.?!]*\b(?:see|go|get|be seen|have it|"
    r"have this|bother|worry)\b|\bis it worth\b|\bworth (?:seeing|going|getting|a trip)\b|"
    r"\bdo i need to\b|\bneed i\b")
_THE_BOOKING_WORDS = frozenset((
    "book", "books", "booking", "booked", "appointment", "appointments", "register",
    "registering", "registration", "online", "app", "phone", "ring", "call", "surgery",
    "practice", "clinic", "cancellation", "cancellations", "slot", "slots", "reception",
    "receptionist", "walk in", "111"))


_A_RETURN_TO = ("back to", "back at", "going back", "go back", "went back", "come back",
                "coming back", "got back")


def _a_decision_is_not_a_booking(understood):
    """False for "should i see a doctor", True for "should i book an appointment"."""
    clean = ((understood or {}).get("clean") or "").lower()
    if not _DECISION_ASK.search(clean):
        return True
    # "back to my knee, should i see a doctor" is a return to a part after another subject, and
    # the decision rows are fenced out of it by SEE_DOCTOR_AVOID, so the booking card is still
    # the one that answers it.
    if any(phrase in clean for phrase in _A_RETURN_TO):
        return True
    return bool(set(re.findall(r"[a-z']+", clean)) & _THE_BOOKING_WORDS)


ENTRIES.append(entry(
    "book-an-appointment",
    (("appointment", "appointments", "doctor", "dentist", "gp", "surgery",
      # "practice" on its own is a music practice, a football practice or a lawyer's work:
      # "how do i get practice at this" and "book practice rooms at uni" were both answered
      # with how to get a GP appointment. Only the surgery sense of the word counts here.
      "doctors practice", "doctor's practice", "doctors' practice", "gp practice",
      "medical practice", "the practice", "my practice", "our practice", "local practice",
      "clinic", "checkup", "check up"),
     # "my surgery never has any appointments, what do i do" is this question asked by someone
     # who has already tried: the words are about there being none, not about booking one.
     ("book", "booking", "make", "made", "get", "arrange", "appointment", "see",
      "any appointments", "never has", "no appointments", "nothing available", "fully booked",
      "cant get in", "can't get in", "none left", "all booked")),
    _book_the_appointment, guard=_a_decision_is_not_a_booking,
    # a real request for time off, an emergency and someone already at the surgery are other
    # lines: this one is about getting seen
    # registering with a surgery is its own job - proof of address, an online form or the
    # reception desk - and this answer is about getting seen, so that line keeps whatever
    # answer it had
    # "how often should i see the dentist" is the check-up interval, not the booking
    avoid=("often", "frequently", "regular", "regularly", "times", "interval",

           "register", "registering", "registration", "sign up", "signed up", "signup",
           "off", "leave", "holiday", "boss", "cover", "sick", "ill", "unwell", "chest pain",
           "bleeding", "cant breathe", "can't breathe", "111", "999", "a&e", "waiting room",
           # the fear of the visit is the nerves row's line, and `terrified` and `frightened`
           # were not here: "i have booked a dentist and im terrified" was answered "ring the
           # practice and ask for an urgent slot ... saying it hurts", to a person who had booked
           # and said nothing about pain. `hate going` and `cant face` are left out on purpose:
           # a line saying that is a line the chat asks a question about.
           "nervous", "scared", "dreading", "terrified", "terrifying", "frightened", "phobia",
           "afford", "cost", "how much",
           # "is it free to see a dentist" is the money question: nhs-dentist-free answers it
           "free", "is it free", "do i pay", "do i have to pay",
           # a bare "appointment" is not a medical one: "how do i book a haircut appointment"
           # was answered with the 8am GP lines, and a barber, a salon and a garage take
           # bookings of their own (consumer.py's book-a-slot answers those)
           "haircut", "hair cut", "hair appointment", "barber", "barbers", "hairdresser",
           "salon", "nails", "manicure", "pedicure", "waxing", "massage", "facial",
           "hair colour", "colour", "restaurant", "table")))

# A person who has swallowed sea water is a person, not a dog. pets.py's salt-water entry is a
# "ring the vet" answer keyed on "sea water" and "drank", so "I drank salt water at the beach",
# "my son swallowed sea water" and even "is sea water safe to drink" all got the vet and a bowl.
# The animal words are in this answer's `avoid` and an animal in the line is in the pets answer's
# `ask`, so each line goes to the body that has the danger in it.
# Someone who is already being sick, dizzy or confused after swallowing sea water is not asking
# whether a mouthful is fine: the phone call comes first and the reassurance, if it comes, last.
SEA_WATER_ALARM = re.compile(
    r"\b(?:sick|sickness|throwing up|thrown up|threw up|vomit|vomiting|vomited|dizzy|dizziness|"
    r"confused|confusion|drowsy|lethargic|floppy|faint|fainted|fainting|unwell|poorly|"
    r"too much|lots|loads|plenty|gallons|whole bottle|a lot)\b")

SEA_WATER_ALARM_REPLY = (
    "Ring 111 now: being sick, dizzy or confused after swallowing sea water needs a doctor "
    "today, and 999 if they are drowsy, floppy or hard to wake. Never make anyone sick to get "
    "it out. A mouthful or two does no harm - the salt just makes you thirsty, so rinse your "
    "mouth and drink fresh water - and boiling it is no help, because the water steams off and "
    "the salt stays.")


def _said_already(opening, memory, keep=3):
    """True when the bot's last few turns already opened with this advice."""
    opening = opening.lower()
    for turn in (memory.get("turns") or [])[-keep:]:
        if isinstance(turn, dict) and opening in (turn.get("bot") or "").lower():
            return True
    return False


def _sea_water_reply(memory, understood):
    # "is he going to be ok" after "my dog drank sea water" names no animal of its own, so the
    # human card used to reassure an owner whose dog had just been told to see the vet. The pet
    # rows keep the rule for who the talk is about; when a pet is the one being talked about, the
    # same answer as `pet-salt-water` comes back here rather than the mouthful-is-harmless one.
    from .pets import _pet_in_the_talk, _pet_salt_water
    if _pet_in_the_talk(memory, understood):
        if _said_already("ring the vet now", memory):
            # The advice has just been given, so the same paragraph twice is no answer either.
            # A worried "is he going to be ok" gets the short form, with the watch-for said out loud.
            return ("Same as before, and it still stands: ring the vet now and say how much salt "
                    "water and when. Being sick, wobbly or drowsy in the next few hours is a "
                    "same-day visit, not a wait and see, and keep the fresh water away until the "
                    "vet has said otherwise.")
        return _pet_salt_water(memory, understood)
    line = ((understood or {}).get("clean") or "").lower()
    if SEA_WATER_ALARM.search(line):
        return SEA_WATER_ALARM_REPLY
    return (
        "A mouthful or two of sea water does no harm: the salt in it just makes you thirsty, so "
        "rinse your mouth out and drink some fresh water. Boiling it is no help - the water "
        "steams off and the salt stays, so it gets saltier. A child or an adult who has swallowed "
        "a lot of it - or who is being sick, dizzy or confused - needs 111, and 999 if they are "
        "drowsy or hard to wake. Never make anyone sick to get it out.")


ENTRIES.append(entry(
    "body-sea-water",
    (("sea water", "salt water", "saltwater", "seawater", "salty water", "sea"),
     ("drank", "drink", "drinking", "swallowed", "swallow", "mouthful", "gulp", "gulped",
      "sick", "vomiting", "thirsty", "sipped", "safe", "harm", "boil", "boiling", "boiled")),
    _sea_water_reply,
    avoid=("dog", "dogs", "cat", "cats", "puppy", "puppies", "kitten", "pup", "pet", "pets",
           "vet", "hamster", "rabbit", "horse", "pony", "livestock",
           # washing, cleaning and cooking sentences that happen to hold "salt water"
           "wash", "washing", "rinsed the", "soak", "gargle", "boil pasta", "boil potatoes",
           "boiled pasta", "cooking water", "for pasta", "to boil", "boiling pasta", "potatoes",
           # a drowning is a 999 conversation and this is not it
           "bath", "drown", "drowned",
           # the bare word "sea" in the key read "is it safe to swim in the sea" as a question
           # about drinking it: swimming in it is sport.py's open-water answer, not this one
           "swim", "swimming", "swimmer", "paddle", "paddling", "lido", "beach", "tide",
           "rip current", "wetsuit")))

# The toe is the one part a fitness entry already claims: `fitness.feet-after-run` keys "toes" and
# "hurt", so "my toe hurts" - a line with no run in it - got "most foot pain after running is
# shoes or mileage", and its rarer words outranked the new row. The bias is how this table wins a
# tie on a shared word without widening the key or touching that entry.
REGION_BIAS = {"toe": 3}

# The other half of the same line: a toe that hurts *after a run* is the mileage-and-shoes
# question, and `fitness.feet-after-run` is right about it. Words that name the run hand the line
# back, so the bias only wins the bare "my toe hurts" it was added for.
EXTRA_AVOID["toe"] = ("run", "runs", "running", "jog", "jogging", "jogged", "ran", "miles",
                      "mileage", "after a run", "my run", "long run", "treadmill", "triathlon")

# A body part that is part of a thing is not a person's part: "the table leg is broken" is a
# furniture repair, and "my shoe heel hurts" is the shoe. The words are ordinary body words, so
# the region table read them as the person's back or heel and gave a strain answer. What makes
# the part the thing's is the noun right before it ("table leg", "chair back", "shoe heel",
# "glasses arm"), its possessive ("the chair's back"), or "the leg of the table" just after.
# These are the nouns that own a part people also have, and the parts those things have.
# A thing worn on the part it covers names the part too ("my shoulder bag strap", "my knee
# brace"), and so does a bird or a room ("a chicken leg", "the back bedroom").
OBJECT_OWNERS = frozenset("""
table tables chair chairs desk desks bed beds sofa sofas couch couches settee settees stool
stools shelf shelves cupboard cupboards wardrobe wardrobes drawer drawers door doors gate
gates fence fences car cars bike bikes bicycle bicycles pram prams buggy buggies wheelchair
wheelchairs glasses sunglasses shoe shoes boot boots trainer trainers sandal sandals ladder
ladders machine machines printer printers laptop laptops phone phones window windows wall
walls floor floors ceiling ceilings roof roofs oven ovens fridge fridges
bag bags strap strap braces brace pillow pillows sleeve sleeves
chicken chickens turkey turkeys duck ducks goose lamb fish
bedroom bedrooms room rooms lounge kitchen bathroom loft attic landing hallway study office
garage garages garden gardens
""".split())
THING_PARTS = frozenset("""
leg legs back arm arms heel heels head foot feet toe toes knee knees hand hands finger
fingers thumb elbow shoulder hip shin spine joint neck sole
""".split())
# An owner named after "of" tells us whose part it is without needing a list of things:
# "the spine of the book", "the neck of the bottle", "the shoulder of the road". The one
# owner that keeps the part a person's is a word for a person or a body word, and a
# possessive ("the back of my head", "the neck of his shirt") is always somebody's.
_PERSON_OWNER = PERSON_NOUNS | frozenset("my your his her their our whose".split())
_DETERMINERS = frozenset("the a an this that these those".split())
# The one-word hurting words, for a rule that only needs to know whether the part has already
# been called a complaint by the word after it.
HURT_WORDS = frozenset(word for word in HURT if " " not in word)
_POSSESSIVES = frozenset("my your his her its their our".split())


def _owner_word(word):
    """The thing named by a word that can own a part: "chair", "chair's", "chairs"."""
    word = word.strip(string.punctuation)
    if word.endswith("'s"):
        word = word[:-2]
    return word in OBJECT_OWNERS or (word.endswith("s") and word[:-1] in OBJECT_OWNERS)


def _a_thing_owns_the_part(understood):
    """True when the line's body word belongs to a thing, not to a person."""
    words = understood.get("words")
    if not isinstance(words, list):
        words = str(understood.get("clean") or "").lower().split()
    words = [str(word).lower() for word in words]
    for index, word in enumerate(words):
        if word.strip(string.punctuation) not in THING_PARTS:
            continue
        if index and _owner_word(words[index - 1]):
            return True
        # A thing named straight after the part owns it just as well as one named before it:
        # "my back wall", "the back fence", "my shoulder bag strap", "my knee brace". The owner
        # has to come straight after the part, with only a determiner between, so the back in
        # "my back hurts in the car" is still the person's own.
        nxt = [word.strip(string.punctuation) for word in words[index + 1:index + 4]]
        nxt = [word for word in nxt if word and word not in _DETERMINERS]
        if nxt and nxt[0] not in THING_PARTS and _owner_word(nxt[0]):
            return True
        # A part that does something inside a thing is the thing's part too: "my foot slipping
        # in my shoes", "my heel rubbing in my boots". The hurt word is what tells the two
        # apart: "my back hurts in the car" is the person's back.
        between = [word.strip(string.punctuation) for word in words[index + 1:index + 5]]
        for preposition in ("in", "inside"):
            if preposition in between:
                cut = between.index(preposition)
                if not any(word in HURT_WORDS for word in between[:cut]):
                    rest = [word for word in between[cut + 1:] if word]
                    rest = [word for word in rest if word not in _DETERMINERS]
                    rest = [word for word in rest if word not in _POSSESSIVES]
                    if rest and _owner_word(rest[0]):
                        return True
                break
        after = words[index + 1:index + 5]
        if after and after[0].strip(string.punctuation) == "of":
            rest = [word.strip(string.punctuation) for word in after[1:]]
            rest = [word for word in rest if word and word not in _DETERMINERS]
            # A possessive in front of the noun says whose the thing is, so the noun after it is
            # what decides: "the back of my tv" and "the back of his shirt" are the tv and the
            # shirt, while "the back of my head" is still the person's own part and "the back of
            # my mum" is a person. Without this the possessive itself was read as the owner and
            # the part stayed the person's.
            while len(rest) > 1 and rest[0] in _POSSESSIVES:
                rest = rest[1:]
            # One noun after "of" is enough owner: "the leg of the table", "the spine of the
            # book", "the shoulder of the road". A body word there is still the person's own
            # part ("the back of the head", "the sole of the foot"), and a possessive or a word
            # for a person ("the back of my head", "the neck of his shirt") is somebody's.
            if rest and rest[0] not in _PERSON_OWNER and rest[0] not in THING_PARTS:
                return True
            if any(_owner_word(word) for word in rest):
                return True
    return False


def the_part_that_hurts(text):
    """The part of the body a line complains about, or None.

    A complaint names its cause as well as its part: "my back has been killing me since i moved
    the sofa" says the back and the sofa, and a follow-up ("its a dull ache on the left side")
    is about the back. This is the part the region table would answer for, read from the line
    alone, so the store can carry the part into a follow-up instead of the cause. The same
    ownership rule as the entries applies: a chair's back and a door's back are the thing's,
    not the person's, and a line with no word of hurting ("i moved the sofa") names no part.
    """
    line = " ".join(str(text or "").lower().split())
    found = re.findall(r"[a-z']+", line)
    if not found:
        return None
    # "killing" is how people say an ache is bad ("my back is killing me"); it is not in the
    # table's HURT because the key spells the phrase out, so it is read here.
    if not (set(found) & HURT_WORDS or "killing" in found):
        return None
    if _a_thing_owns_the_part({"clean": line, "words": found}):
        return None
    for name, parts, _reply in REGIONS:
        if any(part in found for part in parts):
            return name
    return None


# A part named in a question about it is the same complaint as a part that hurts: "what should i
# do about my back", "what can i do about my knee", "whats the best thing for my back", "anything
# i can do about my shoulder", "what helps a bad back". None of them say a hurting word, so the
# region table never saw them and every one of those lines got a shrug. The phrase is the ask and
# the part is the subject, and the part still has to be the person's own (`_the_part_is_a_persons`,
# `_a_thing_owns_the_part`), so "what should i do about my back garden" stays a garden question.
ASKING_ABOUT_A_PART = ("what should i do about", "what should i do for",
                       "what can i do about", "what can i do for",
                       "what do i do about", "what do i do for",
                       "what can i do", "what should i do",
                       "whats the best thing for", "what is the best thing for",
                       "best thing for", "best thing to do for",
                       "anything i can do about", "anything i can do for",
                       "is there anything for", "is there anything i can do",
                       "what helps", "what helps with", "what helps a", "what helps my",
                       # "what is wrong with my knee" is the ask above in the commonest words
                       # people use for it: the frame names the part and asks what the matter
                       # with it is, and every other way of putting that phrase was here. Five
                       # of five joints put this way met the search hedge while the part's own
                       # card was in the tree.
                       "what is wrong with", "whats wrong with", "what's wrong with",
                       "what could be wrong with", "what might be wrong with",
                       "whats the matter with", "what is the matter with",
                       "whats going on with", "what is going on with",
                       "whats good for", "what is good for",
                       # The plainest way anybody asks about a part: "what is wrong with my knee",
                       # "any idea whats wrong with my back", "what have i done to my shoulder".
                       # The rule above already said a part named in a question about it is the
                       # same complaint as a part that hurts, but the list only had the "what
                       # should i do about it" shapes, so the ask that names the *problem* rather
                       # than the *action* fell through to the search hedge
                       # (close-pipe's census, #uncertainty). "is it broken" and "have i broken"
                       # join them: a part with a break in the question is still that part's card.
                       "whats wrong with", "what is wrong with", "what could be wrong with",
                       "what might be wrong with", "what do you think is wrong with",
                       "any idea whats wrong with", "any idea what is wrong with",
                       "what have i done to", "what did i do to my", "whats up with my",
                       "is something wrong with my", "should i worry about my",
                       "how bad is my", "is it broken", "is it fractured", "is it dislocated",
                       "have i broken", "have i fractured", "did i break", "did i fracture",
                       "is it torn", "have i torn", "is it snapped",
                       "remedy for", "any tips for", "any advice for",
                       "how do i ease", "how do i relieve",
                       # "best exercises for a bad back" and "exercises for back pain" were a
                       # shrug while "stretches for a bad back" and "best exercises for a bad
                       # knee" answered: the exercise words were never an ask, so a part plus
                       # "exercises" had no second signal. Which exercises help a named part is
                       # that part's question, and the part still has to be named, so
                       # "what exercises burn the most fat" is not this table's.
                       "what exercises", "which exercises", "any exercises",
                       "best exercises", "good exercises", "exercises for", "exercise for",
                       "exercises to", "exercises help", "exercises that help",
                       "what exercise", "which exercise", "best exercise", "any exercise",
                       "what stretches", "which stretches", "any stretches",
                       "best stretches", "good stretches", "stretches for")

# A part named on its own as a follow-up ("what about my knee" after "my back hurts") is the same
# question about a different part, and the part word is the whole of it: there is no second word
# for the row to find, so the frame that asks it is the ask. Without this every "what about my
# <part>" punted - knee, elbow, wrist, hip, ankle and neck - except the shoulder, whose own card
# happens to score on the part alone. A thing that owns the part ("what about the back door") is
# still stood down by the row's guard, so the frame cannot answer for a door.
ASKED_AGAIN = ("what about my", "how about my", "what about our", "how about our",
               "what about your", "how about your")


# "back" is the one part word that is also a particle and a verb: "keeps coming back", "has come
# back", "is back again". Once the phrases were out of _NOT_A_BODY_PART, a knee that keeps coming
# back reached this table on that word and was told about a back - "Most back pain is muscular,
# keep walking" for a shoulder, a hip, a wrist, a knee. The phrase list could not fix that (an
# avoid phrase stands the whole table down for every part at once, and a key cannot see the word
# order), so the back row asks whether the line's "back" is a back at all.
_BACK_VERB_BEFORE = frozenset((
    "come", "comes", "coming", "came", "go", "goes", "going", "went", "gone", "bring", "brings",
    "bringing", "brought", "send", "sends", "sending", "sent", "put", "puts", "putting", "get",
    "gets", "getting", "got", "take", "takes", "taking", "took", "taken", "give", "gives",
    "giving", "gave", "given", "keep", "keeps", "keeping", "kept", "hold", "holds", "holding",
    "held", "pay", "pays", "paying", "paid", "call", "calls", "calling", "called", "ring",
    "rings", "ringing", "rang", "phone", "phones", "phoning", "phoned", "text", "texts",
    "texting", "texted", "write", "writes", "writing", "wrote", "hand", "hands", "handing",
    "be", "is", "was", "are", "were", "being", "been", "way", "step", "steps", "far",
    "cut", "cuts", "cutting", "fight", "fights", "fighting", "hit", "hits", "hitting",
))


# The other words a line can name the back with: any of these is the body, whatever the word
# order, so the guard only has to decide about the bare "back".
# "hips" and "pelvis" are the lower back of a pregnancy, and the hip joint has its own row, so
# the plural is here and the singular is not.
_ALSO_THE_BACK = frozenset(("backache", "back's", "spine", "lumbar", "sciatica", "pelvis",
                            "hips"))

# "get" is the one verb in that list that is also how people say they have the pain: "i keep
# getting back pain" is a complaint about a back, not a particle. The noun pair is the cure -
# "back pain", "back ache", "back trouble" is always the part, whatever comes in front of it.
_BACK_IS_A_NOUN_AFTER = frozenset(("pain", "aches", "ache", "trouble", "problems", "problem",
                                   "soreness", "strain", "spasms", "spasm"))


def _reading_words(reading):
    """The words of a reading, however much of itself the caller passed.

    Some of the calls that reach this table hand over the words and some hand over the line
    ("clean" or "text" only), and a guard that reads nothing answers True for every line - which
    put the back card in front of "i keep coming back to the same problem", a line with no body
    part in it at all. So the words are taken from the line when the caller has not split it.
    """
    if not isinstance(reading, dict):
        return []
    said = reading.get("words")
    if said:
        return [str(word).lower().strip(string.punctuation) for word in said]
    line = reading.get("clean") or reading.get("text") or ""
    return re.findall(r"[a-z']+", str(line).lower())


def _the_back_is_a_back(understood):
    """False when the line's only "back" is the particle in "come back" or "is back again"."""
    if not isinstance(understood, dict):
        return True
    words = _reading_words(understood)
    leaned = understood.get("leans_on") or {}
    if isinstance(leaned, dict):
        # a follow-up says "it keeps coming back", so the back a chat was about is in the line
        # this one leans on: "it hurts when i sit" after "my back aches" is still a back.
        words += _reading_words(leaned)
    if not words:
        # nothing to read is no reason to stand down: the row answers as it did before.
        return True
    if _ALSO_THE_BACK.intersection(words):
        return True
    for index, word in enumerate(words):
        if word != "back":
            continue
        if words[index + 1:index + 2] and words[index + 1] in _BACK_IS_A_NOUN_AFTER:
            return True
        if index and words[index - 1] in _BACK_THEIRS:
            return True
        if index and words[index - 1] in _BACK_VERB_BEFORE:
            continue
        if index and words[index - 1] in _BACK_DESCRIBED:
            return True
        if words[index + 1:index + 2] and words[index + 1] in _BACK_IS_A_RETURN:
            continue
        if _a_verb_earlier_took_it(words, index):
            continue
        return True
    return False


# "back to <the thing>" is a return to a subject, not a part: "anyway back to the race", "back to
# my knee", "back to the boiler". The word is the particle there however little else the line has,
# and it was reading as the part as soon as a chat had any ache in it - a knee sore since Tuesday,
# then "anyway back to the race, how should i taper", got "Most back pain is muscular and settles in
# two to six weeks". The rest of the check already stands a real part down first, because "my back
# to the wall" and "a bad back to work on a cold morning" are caught by the possessive and the
# describing word before this is reached.
_BACK_IS_A_RETURN = frozenset(("to", "into", "onto", "towards", "toward"))

# The words that make the back the line's own however far back the verb is: "a stiff back",
# "my back" and "a bad back" are the part, and "can i get my back checked" is a question about it.
_BACK_THEIRS = frozenset(("my", "his", "her", "their", "our", "your", "the", "a", "an", "its",
                          "this", "that", "these", "those", "mine", "hers", "theirs", "ours"))
_BACK_DESCRIBED = frozenset("""
stiff sore bad aching achy painful lower upper middle tight weak dodgy old broken fragile seized
knackered tired poor
""".split())
# The verbs that send a thing back, when the thing is said between the verb and the word:
# "want my money back", "get my results back", "ask for the deposit back". Only the two that
# take a "my" object this way are missing from the set above; "get" is already in it.
_BACK_TAKING_A_THING = frozenset("""
want wants wanted wanting need needs needed needing ask asks asked asking owe owes owed
get gets getting got give gives giving gave given send sends sending sent take takes taking
took taken pay pays paying paid bring brings bringing brought keep keeps keeping kept put puts
putting hand hands handing hold holds holding held call calls calling called ring rings ringing
rang text texts texting texted write writes writing wrote throw throws threw pull pulls pulled
""".split())
# The words that end a clause: a verb on the far side of one of these has nothing to do with
# this "back" ("i rang the shop and asked about my back").
_BACK_CLAUSE_JOIN = frozenset(("and", "but", "then", "so", "because", "when", "if", "before",
                               "after", "until", "while", "or"))


def _a_verb_earlier_took_it(words, index):
    """True when a verb earlier in this clause has this "back" as its particle.

    "get some energy back" and "want my money back" put the thing the verb acts on between the
    verb and the word, so the neighbour test above cannot see the verb at all and the line kept
    the back-pain card: "what can i do to get some energy back" was answered "Most back pain is
    muscular and settles in two to six weeks", a paragraph about a body nobody mentioned.

    What is between them has to be the thing, so a word that describes the part ("sore", "lower",
    "bad") or a determiner on its own ("my back") keeps the back a back - that is the `return
    True` the caller already made before this is asked.
    """
    seen = 0
    for at in range(index - 1, -1, -1):
        word = words[at]
        if word in _BACK_CLAUSE_JOIN:
            return False
        if word in _BACK_TAKING_A_THING:
            return True
        seen += 1
        if seen > 4:
            return False
    return False


# Both readings are wanted on the back row: a "back" that is a particle is not a part, and a
# "back" that belongs to a thing ("the door back aches") is the thing's, not the person's.
def _the_back_is_a_back_that_is_someones(understood):
    return _the_part_is_a_persons(understood) and _the_back_is_a_back(understood)


def _the_part_is_not_a_standing_trouble(understood):
    """This line is about a fresh knock, not a part that has given trouble for years.

    A part that "gives trouble", is "bad" or "dodgy", or is asked what would strengthen it, has
    its own standing-condition row (`bad-<part>` below), which says which movement builds the part
    up rather than how to rest it. Those rows key the same part word as this one, and the movement
    asking phrases in `ASKING_ABOUT_A_PART` ("what exercise", "exercises for") make this row match
    too, so without this the general resting answer won: "what exercise can i do with a bad knee"
    and "whats a good exercise for bad knees" went from the strengthening card to "ease off
    running". The parts that never name one of those words keep this row.
    """
    line = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    # A report of a bad part ("i have a bad shoulder") is the part's own card, which the composer
    # reads by asking what can be done about the thing reported; this row is the card it asks.
    if _REPORTED_COMPLAINT.search(line):
        return True
    return not any(w in line for w in _STANDING_TROUBLE)


def _a_region_guard(name):
    """The `guard` for one part's region row, built here rather than in the loop.

    A lambda written inside the entry loop would close over the loop's `name` and read the last
    part at call time, so every row would be guarded as if it were that one.
    """
    if name == "back":
        def _the_back_is_the_persons_and_not_a_standing_trouble(understood):
            return (_the_back_is_a_back_that_is_someones(understood)
                    and _the_part_is_not_a_standing_trouble(understood))

        return _the_back_is_the_persons_and_not_a_standing_trouble

    def _the_part_is_the_persons_and_not_a_standing_trouble(understood):
        return (_the_part_is_a_persons(understood)
                and _the_part_is_not_a_standing_trouble(understood))

    return _the_part_is_the_persons_and_not_a_standing_trouble

# A part is bad because of what it stops the person doing, which is how a lot of people say it:
# "my back is keeping me awake", "its my back thats keeping me up", "my knee is stopping me
# walking". None of those says "hurt", so the strain table - a part plus a hurt word - answered a
# question back ("is there anything you'd like a hand with") or a shrug, while "my back hurts" had
# the answer. The consequence is the pain said by what it costs, so it counts as the hurt word.
#
# The verb is the shape, not a list of parts or of what people cannot do, so it holds for every
# part the table knows: "keeping me up", "keeps me awake", "wont let me sleep", "stopping me
# walking", "keeping me off my feet". A line with no part in it is not this row's line - the
# shape is one signal, so "the noise is keeping me up" still needs a body before it answers.
_KEPT_AWAKE = re.compile(
    r"\b(?:keeps?|kept|keeping|stops?|stopped|stopping|prevents?|prevented|preventing|held|holding)"
    r"\s+me\s+(?:up\b|awake\b|off\s+my\s+feet\b|from\s+\w+ing\b|from\s+sleep\b|"
    r"sleeping\b|walking\b|standing\b|sitting\b|driving\b|working\b|"
    r"lying\b|sleep\b)"
    # "wont let me" is the other way people say it, and it has to stay narrow: the same words
    # are how a line about permission reads - "my dad wont let me go out", "my boss wont let me
    # leave early", "my husband wont let me leave the house and he grabbed my arm" - and those
    # are the safety rows, whose answer must not be a strain card. Only the verbs a body stops
    # you doing are here; "go", "leave", "have", "see" and "work" are not.
    r"|\b(?:wont|won t|wouldnt|would not|doesnt|does not|will not|didnt|did not)"
    r"\s+let\s+me\s+(?:sleep|sleeping|nap|rest|lie\s+down|lie\s+still|lie\s+flat|"
    r"sit\s+down|stand\s+up|walk|drive|get\s+up|get\s+out\s+of\s+bed|roll\s+over)\b"
)


# The shape above says what the part costs, so the line still has to name a part: the shape is
# one signal, and on its own "the noise is keeping me up" answered with the knee's drill, because
# a row whose part word is missing is not a part that belongs to a thing either, so its guard had
# nothing to say against it. The parts are read off the table this row comes from, so a part added
# there is covered without a list to keep in step.
_A_PART_IN_THE_TABLE = re.compile(
    r"\b(?:%s)\b" % "|".join(sorted({re.escape(p)
                                     for _n, parts, _r in REGIONS for p in parts},
                                    key=len, reverse=True)))


def _a_part_keeps_me_from_something(words):
    """True when the line says a part is stopping the person doing something."""
    line = (words or "").lower()
    return bool(_KEPT_AWAKE.search(line) and _A_PART_IN_THE_TABLE.search(line))

# A break said of a part - "is my rib fractured", "have i cracked a rib", "is my tailbone broken" -
# is a knock card's line wherever that card has a test to offer. For the parts it has no test for
# (a rib, a tailbone, a groin) the part's own row is the answer, so the break words join *those*
# rows only. "is my wrist broken" therefore keeps the knock card's four-steps test and "is my rib
# fractured" stops being the search hedge.
BREAK_SAID = ("broken", "broke", "fractured", "fracture", "cracked", "crack", "snapped")
# The region rows the knock card has no test for, by name. A rib, a tailbone and a groin have no
# "stand on it" test and no row of their own on the knock card (`BROKEN_PARTS`, below), so their
# break question is their own row's. A back or a neck is not here on purpose: a broken back or
# neck is an ambulance, not a strain card, and the honest hedge is the better answer until the
# safety cases own that line.
A_PART_NO_KNOCK_TEST = ("ribs", "tailbone", "groin")


def _the_breaks_it_says(name):
    """The break words for a row whose part the knock card has no test for; else nothing."""
    return BREAK_SAID if name in A_PART_NO_KNOCK_TEST else ()


ENTRIES += [entry(f"sore-{name}",
                  (parts, HURT + ASKING_ABOUT_A_PART + ASKED_AGAIN + _the_breaks_it_says(name)),
                  reply,
                  avoid=AVOID + EXTRA_AVOID.get(name, ()),
                  bias=REGION_BIAS.get(name, 0),
                  guard=_a_region_guard(name),
                  shape=(_a_part_keeps_me_from_something,))
            for name, parts, reply in REGIONS]

# A hurt limb that belongs to somebody else is still a first aid question, and until this row
# existed it was answered by the day-after-soreness card in fitness: "my son fell off the
# trampoline and hurt his arm", "my son hurt his leg" and "my husband hurt his arm" all named a
# part and "hurt" and got "that ache a day or two after new or harder exercise is delayed-onset
# muscle soreness" - a fall told its muscles were repairing themselves. The sore rows above stand
# down on another person's part because their advice is written in the second person ("keep
# walking and carry on with your usual jobs"), but standing down is not an answer and a parent
# needs one. This row speaks about the child and keeps the two questions a parent has: is it
# broken, and where do we go.
SOFT_TISSUE = ("arm", "arms", "forearm", "leg", "legs", "thigh", "thighs", "calf",
               "calves", "shin", "shins", "wrist", "wrists", "hand", "hands", "elbow",
               "elbows", "shoulder", "shoulders", "knee", "knees", "ankle", "ankles",
               "foot", "feet", "thumb", "thumbs", "finger", "fingers", "collarbone")
# Who a limb can belong to when it is not the person typing. The key names the hurt and the part,
# and this list is the guard rather than a third key group: a keyed "my husband" makes the spouse
# the subject of the conversation the store keeps, so the next line ("should he see someone") was
# read as being about the husband, and the decision card stood down because a husband is in its
# avoid list - the follow-up that main answered got a shrug. A guard leaves the topic on the part.
_SOMEONE_ELSE = frozenset("""
he him his she her hers they them their theirs son daughter child kid kids baby toddler
husband wife partner boyfriend girlfriend mum mom mother dad father brother sister friend mate
nephew niece grandson granddaughter grandad grandma granny uncle aunt cousin
""".split())


# A fall that was a month ago is not a first aid question any more. "she fell last month and broke
# her wrist" comes from a daughter worried about her mother falling again, and what she needs is
# the diary of where and when it happens (the store's answer) rather than ice and A&E tonight.
_A_WHILE_AGO = re.compile(
    r"\b(?:last|past)\s+(?:week|month|year|summer|winter|christmas|autumn|spring)\b"
    r"|\b(?:a|one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s*(?:days?|weeks?|months?|years?)\s+ago\b"
    r"|\b(?:a\s+)?(?:few|couple\s+of)\s+(?:weeks|months|years)\s+ago\b"
    r"|\b(?:weeks|months|years) ago\b|\byears back\b|\byears since\b"
    r"|\bwhen (?:he|she|they|my \w+) (?:was|were)\b|\bused to\b")


# What happened to the part, as opposed to how it feels. "my son hurt his arm" and "she banged
# her knee" say something happened; "her knee hurts" says only that it aches, and an ache with
# nothing behind it is the conversation's to answer (the store says how long, whether to see
# someone), not a first aid card about A&E.
_IT_HAPPENED_TO = frozenset("""
fell fallen falling fell trip tripped tumbling tumbled landed hit smacked banged bashed
knocked injured sprained twisted cricked wrenched
""".split())
_TO_HURT_A_PART = frozenset("hurt hurting".split())


def _it_is_somebody_elses_part(understood):
    """True when the part that is hurt belongs to another person, so the line is theirs to answer.

    The sore rows above are written in the second person and step aside for a relative, which is
    right: "keep walking and carry on with your usual jobs" is not advice a parent can pass on.
    This row is the answer for those lines, and only those: "i hurt my arm", "my legs hurt" and
    "my wrist hurts after a fall" are still the person's own and keep the rows that answer them.
    "My son has a bad back" names no hurt and no fall, so it never reaches this row at all.
    """
    if not isinstance(understood, dict) or not _the_part_is_a_persons(understood):
        return False
    words = [str(word).lower() for word in understood.get("words") or ()
             if isinstance(word, str)]
    people = {word[:-2] if word.endswith("'s") else word for word in words}
    if not people & _SOMEONE_ELSE:
        return False
    said = str(understood.get("clean") or understood.get("text") or "").lower()
    if _A_WHILE_AGO.search(said):
        return False
    parts = [at for at, word in enumerate(words) if word in SOFT_TISSUE]
    if not parts:
        return False
    if any(word in _IT_HAPPENED_TO for word in words) or "went over" in said:
        return True
    # "hurt his arm" is something that happened to the arm; "her knee hurts" is the ache on its
    # own, and the word order is what tells them apart.
    return any(word in _TO_HURT_A_PART and at < parts[0] for at, word in enumerate(words))


ENTRIES.append(entry(
    "hurt-limb-someone",
    (("hurt", "hurts", "hurting", "injured", "banged", "knocked", "bashed",
      "fell", "fell off", "fell over", "fallen", "tripped", "tumbled",
      "landed on"),
     SOFT_TISSUE),
    "Check it where they are: whether it is swollen or bruising fast, whether they will use it "
    "at all, and whether it looks bent. Ice it for 15 minutes, keep it raised, and give "
    "children's paracetamol if their age allows. A limb they will not use or let you move, one "
    "that looks bent, or swelling that comes up fast is A&E the same day; a bang on the head with "
    "sickness, drowsiness or a knockout is 999.",
    guard=_it_is_somebody_elses_part,
    # a dog or a cat is the vet's question, whatever it has hurt
    avoid=("dog", "cat", "puppy", "horse", "kitten")))

# The region table passes on an ache that has been there for weeks, because the advice for a
# two-day-old knock ("ease off running for two days") is the wrong advice for a month of it, and
# the words that send it on are in that table's avoid list. Nothing was holding those lines, so
# "my back has been aching all week", "my knee has hurt for months", "my shoulder has ached for
# weeks" and "my hip has been hurting for weeks" all got "That's a nuisance to be carrying round.
# How long has it been like that?" - a question where an answer was asked for. A long-running
# ache is a different answer from a fresh one: what has to change is the load, not the rest.
WEEKS = ("for a week", "for two weeks", "for a fortnight", "for three weeks", "for weeks",
         "for a month", "for months", "for a year", "for years", "for ages", "for a while",
         "all week", "all month", "a week now", "weeks now", "months now", "a few weeks",
         "a couple of weeks", "two weeks", "three weeks", "weeks", "months",
         "the last few months", "the past few months", "the last few weeks",
         "the past few weeks", "on and off for")

# A knee that aches after every run has its own answer, and it is a better one than the general
# load-and-physio paragraph: `sport` knows the mileage, the shoes and the kneecap, so a line that
# names the running stands this entry down. Without this, "i run three times a week but my knee
# aches" lost "cut the distance and the speed for a week or two" to the general answer.
_SPORT_WORDS = ("run", "runs", "running", "ran", "jog", "jogging", "jogged", "miles", "treadmill",
                "gym", "workout", "work out", "weights", "cycling", "cycle", "swim",
                "swimming", "football", "rugby", "netball", "hockey", "tennis", "marathon",
                "half marathon", "parkrun", "training", "training for", "after every run")

# The one strengthening move that suits each part, because "do some exercise" is not something a
# person can act on and the wrong move for a shoulder is a wasted fortnight. The keys are the
# words the person used, as `_part_named` returns them.
_WEEKS_DRILL = {
    "back": "two short sessions a week of a slow bridge lying on your back, or standing and "
            "lifting one knee at a time",
    "spine": "two short sessions a week of a slow bridge lying on your back",
    "knee": "two short sessions a week of sit-to-stand from a chair, ten times each, plus a walk",
    "kneecap": "two short sessions a week of sit-to-stand from a chair, ten times each",
    "hip": "two short sessions a week of sit-to-stand from a chair and a walk",
    "shoulder": "two short sessions a week of a slow wall push-up, and the pendulum swing (lean "
                "forward, let the arm hang, circle it slowly)",
    "neck": "chin tucks, ten at a time, twice a day, and a look at where your screen sits",
    "foot": "a calf stretch against a wall before your first steps in the morning, and a rolled "
            "towel under the arch",
    "heel": "a calf stretch against a wall before your first steps, and shoes with a firm sole",
    "ankle": "heel raises holding a chair, ten at a time",
    "wrist": "a slow curl with a light weight, palm up and palm down, and breaks from gripping",
    "hand": "a slow curl with a light weight, and breaks from gripping",
    "thumb": "a slow curl with a light weight, and breaks from gripping",
    "elbow": "a light weight lifted slowly, palm down then palm up",
    "leg": "two short sessions a week of a slow squat to a chair, plus a walk",
    "calf": "two short sessions a week of a slow squat to a chair and heel raises",
    "thigh": "two short sessions a week of a slow squat to a chair, plus a walk",
    "hamstring": "a slow squat to a chair and a gentle hamstring stretch after a warm bath",
    "shin": "a walk, and calf raises holding a chair",
    "rib": "keeping your breathing normal rather than in shallow sips, and a cushion pressed "
           "against that side when you cough",
    "toe": "shoes with room in them, and a warm soak",
}


def _line_words(understood):
    """Only the words of this line, not the turn it leans on.

    `_words` adds the background, and in a conversation about a sore tailbone the sentence "30
    weeks pregnant and my back hurts" was answered about the tailbone: the part has to be the one
    the person has just named.
    """
    if not isinstance(understood, dict):
        return set()
    return set(w.lower() for w in understood.get("words") or () if isinstance(w, str))


def _how_long(understood):
    """How long the line says it has been going on, in the person's own scale."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if re.search(r"\byear", said):
        return "for months or years"
    if re.search(r"\bmonth", said):
        return "for months"
    return "for a week or more"


_PREGNANT_WORDS = ("pregnant", "pregnancy", "expecting", "trimester", "baby due")

# After a verb, "back" is a direction and never a body part: "it came back after a week", "i
# went back to work today", "should i give it back to the shop". Read as a part it took the weeks
# entry, so a turn after the boiler answer - "it came back after a week" - was answered
# "A back that has been sore for a week or more is usually a tendon or a joint...", a paragraph
# about a body the person never mentioned. A back the line owns ("my back") is still a back, so
# every back in the line has to be this kind before the entry stands down.
_BACK_AFTER_A_VERB = re.compile(
    r"\b(?:was|were|is|are|be|been|being|am|im|came|come|comes|coming|went|go|goes|going|gone|"
    r"get|gets|getting|got|give|gives|"
    r"giving|gave|given|takes?|took|taken|brings?|brought|sends?|sent|pays?|paid|calls?|"
    r"called|sits?|sat|cuts?|holds?|held|puts?|stepped|steps?|looks?|looked|turns?|turned|"
    r"fights?|fought|throws?|threw|pulls?|pulled|comes?|coming|"
    # "we moved back to bristol last year" is a returning and the only back in the line, and the
    # place it names is not one `_BACK_BEFORE_A_PLACE` knows: without the verb the reading called
    # it a body and the line was given a back strain it never mentioned.
    r"mov(?:e|es|ed|ing)|relocat(?:e|es|ed|ing))\s+"
    r"(?:(?:it|them|him|her|me|us|you|one)\s+)?back\b")


# The other way a line says "back" without meaning a part: the place it is going back to. "im
# exhausted with the baby and back at work next month" and "back at work next month" were both
# answered "A back that has been sore for months is usually a tendon or a joint..." - a paragraph
# about a body the person never mentioned. No verb is needed in front of the word for this one -
# the place after it is the whole of the signal - so it is a pattern of its own. A back the line
# owns is still a back, whatever follows it ("my back at work gets sore by lunchtime"), which is
# why every determiner in front of the word stands the pattern down.
_BACK_BEFORE_A_PLACE = re.compile(
    r"(?<!\bmy )(?<!\bhis )(?<!\bher )(?<!\byour )(?<!\btheir )(?<!\bour )(?<!\bthe )"
    r"(?<!\bthis )(?<!\bthat )(?<!\ba )(?<!\ban )"
    r"\bback\s+(?:at|to|from|in|on)\s+(?:the\s+|my\s+|her\s+|his\s+)?"
    r"(?:work|school|home|college|uni|university|office|nursery|holidays?|shift|shifts|"
    r"placement|term|nights?|days?|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b")

# A homecoming needs no preposition: "back home" and "back in with my parents" are a place, and
# the pattern above wants "back at/to/in/on" before the place, so "moving back home next week" and
# "im moving back in with my parents" were read as a back of the body - a paragraph about a tendon
# for somebody who was talking about a suitcase. The words after the place keep a back the line
# owns out of it, the same way the determiner rule above does.
_BACK_HOME = re.compile(
    r"(?<!\bmy )(?<!\bhis )(?<!\bher )(?<!\byour )(?<!\btheir )(?<!\bour )(?<!\bthe )"
    r"(?<!\bthis )(?<!\bthat )(?<!\ba )(?<!\ban )"
    r"\bback\s+(?:home|in\s+with|with\s+(?:my|her|his|our|the)\s+(?:parents|mum|dad|mother|"
    r"father|family|folks)|to\s+(?:my|her|his|our)\s+(?:parents|mum|dad|mother|father|home))\b")


def _back_is_a_direction(understood):
    """True when every back the line says is a particle or a returning, not a part of the body."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    said = len(re.findall(r"\bback\b", text))
    seen = (len(_BACK_AFTER_A_VERB.findall(text)) + len(_BACK_BEFORE_A_PLACE.findall(text))
            + len(_BACK_HOME.findall(text)))
    return bool(said) and seen >= said


def _a_back_in_the_chat(memory):
    """True when a line already in this conversation named a back of its own.

    "i hurt my back lifting boxes" then "the pain came back after a week" is a question about
    that back, so the direction in the second line does not take the answer away: the chat has
    the part, and the entry is the one that speaks for it.
    """
    for turn in (memory or {}).get("turns") or []:
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if re.search(r"\bback\b", said.lower()) and not _back_is_a_direction({"text": said}):
            return True
    return False


def _sore_weeks_reply(memory, understood):
    # The pregnancy answer is the one for a back in pregnancy, and it is the one that knows not to
    # offer ibuprofen. In a conversation the words of the turn before ("a tailbone", "weeks") can
    # lift this entry over it, so a line that says pregnant stands this one down outright.
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    # The conversation counts too: the turn before may be the one that said "pregnant" ("my hips
    # have been aching for months during pregnancy"), and in a long conversation this entry could
    # otherwise be the card the composer carries over that line.
    parts = [said]
    for key in ("text", "plain"):
        value = (understood or {}).get(key)
        if isinstance(value, str):
            parts.append(value.lower())
    for key in ("words", "background"):
        for word in (understood or {}).get(key) or ():
            if isinstance(word, str):
                parts.append(word.lower())
    turns = (memory or {}).get("turns") or []
    if turns and isinstance(turns[-1], dict) and isinstance(turns[-1].get("user"), str):
        parts.append(turns[-1]["user"].lower())
    if any(word in " ".join(parts) for word in _PREGNANT_WORDS):
        return None
    part = (_part_named(_line_words(understood), understood)
            or _part_named(_words(understood), understood) or "part")
    if (part == "back" and _back_is_a_direction(understood)
            and not _a_back_in_the_chat(memory)):
        return None
    article = "An" if part[:1] in "aeiou" else "A"
    # No "back" or "hurts" in the shared part of the wording: every part's card carries it, and
    # the composer hands a sentence of an earlier answer back to a line that shares two content
    # words with it, so a generic pair like that made this card answer "30 weeks pregnant and my
    # back hurts" a turn after a tailbone card. Each part's own drill names its own part.
    drill = _WEEKS_DRILL.get(part, "two short sessions a week of the movement you want to "
                                   "return to, stopping short of pain")
    return (article + " " + part + " that has been sore " + _how_long(understood) + " is usually "
            "a tendon or a joint asked for more than it is used to: keep going as far as is "
            "comfortable, and add " + drill + ". If it is no better after six weeks, wakes you "
            "up, or keeps coming back, ask your GP about physio. Ring 111 sooner for numbness, a "
            "part that gives way, or pain with a fever or weight loss.")


# "Should I see someone about my back" is a decision, and it is not the booking script. The
# appointment answer in this file is keyed on the doctor words and the verb "see", so every one of
# these lines spent its turn on "ring at the moment the lines open, ask for the first appointment
# of the day": how to get seen, when what was asked is whether to be seen and how soon. The
# answer is a decision rule, and the three things that move it are the same for every part.
# The parts and the pain words are the ones the strain table uses, so a line that reaches here is
# a line about a body; the parts with an answer of their own are in the avoid, because a cough or
# a headache already gets a "go sooner if" sentence written for it, and a knee ache that only
# comes on when it is cold is the weather answer's.
DECIDE_ASK = ("see someone", "see a doctor", "see the doctor", "see a gp", "see my gp",
              "go to the doctor", "go to a doctor", "go to my gp", "should i see",
              "do i need to see", "worth seeing", "see a physio", "see the physio",
              "get it looked at", "get it seen", "should i get it checked", "worth getting checked",
              "checked out", "get it checked", "get my checked",
              "should i go to the doctor", "do i need to get it checked", "worth going to the",
              "should i be worried", "is it worth going",
              # The plainest way people ask it, which none of the frames above cover: "is it
              # worth getting my knee looked at" got "Nothing on my side can look, sorry" where
              # "is it worth seeing someone" got the go-by-how-long answer, and "should i bother
              # going about my shoulder" got a dilemma answer about what you would lose either
              # way. A part being looked at is the same decision, and a hedge word in front of a
              # decision does not change it, so "bother" and "any point" belong here too.
              "get it looked at", "get my", "looked at", "looked over", "get it seen to",
              "should i bother", "bother going", "bother seeing", "any point in",
              "worth it to", "worth a visit", "worth a trip", "worth making an appointment")

SEE_DOCTOR_AVOID = (
    # a lump or a gland is the lump card's own line: "should i see a doctor about a lump on my
    # arm" asks what the lump is, and an arm-and-how-long-it-has-been-going answer is not it
    "lump", "lumps", "gland", "glands", "node", "nodes", "breast", "lump on",
    # a part with its own "go sooner if" answer: the cough, the headache, the throat, the ear,
    # the tooth, the stomach, a pregnancy
    "chest", "heart", "throat", "tooth", "teeth", "gum", "gums", "ear", "ears", "head",
    "headache", "headaches", "migraine", "cough", "cold", "flu", "sore throat", "stomach",
    "tummy", "belly", "toothache", "jaw", "period", "periods", "pregnant", "pregnancy",
    # a part of somebody else, and an animal
    "son", "daughter", "child", "kid", "kids", "baby", "toddler", "husband", "wife",
    "partner", "mum", "mom", "mother", "dad", "father", "friend", "dog", "cat", "puppy",
    # the emergency shapes: those are the red-flag cards' lines, not a decision rule
    "sick", "nauseous", "vomit", "dizzy", "faint", "breathless", "sweating", "numb",
    "numbness", "pins and needles", "cant pee", "can't pee", "blood", "bleeding",
    "gave way", "gives way", "locked", "locks", "swollen", "swelling", "hot and swollen",
    # "back" is two words: "is it worth going back to nursing" is a job, not a spine, and this
    # card told that person to give it two to six weeks. A part of the body is never followed
    # by "to", so the going-back shapes and the things people go back to hand the line on.
    "go back", "going back", "went back", "come back", "coming back", "back to", "back at",
    "nursing", "career", "careers", "retrain", "retraining", "job", "jobs", "degree",
    "university", "college", "course", "shift", "my old",
    # (the ache after new exercise and the part that hurts when the weather turns are not here:
    # a decision ask is a decision even when the line names the gym or the cold, and a line that
    # names neither a decision ask nor a part with its own answer cannot reach this row at all,
    # so the weather-ache card keeps its own lines without a fence. The day-after ache is the one
    # shape the rule steps out of, and it is `_see_doctor_reply` that does it, because it takes
    # an ache word *and* an exercise word to recognise it and an entry's avoid cannot say "and")
    ) + FALL

SEE_DOCTOR_PARTS = ("back", "leg", "legs", "knee", "knees", "hip", "hips", "shoulder",
                    "shoulders", "neck", "ankle", "ankles", "wrist", "wrists", "elbow",
                    "elbows", "foot", "feet", "arm", "arms", "hand", "hands", "joint",
                    "joints", "side", "spine", "thigh", "thighs", "shin", "shins", "calf",
                    "heels", "heel", "finger", "fingers", "thumb", "thumbs",
                    "pain", "pains", "hurts", "hurting", "ache", "aches", "aching", "sore")


# "my legs ache after the gym, should I see a doctor" is not a question about how long a part has
# been going on: it is the ache a day or two after new work, and the answer to that is "it is
# normal, it is not damage, keep moving, worst at 48 hours" - a no, with the reason, which is what
# was asked. That card is `sport.sore-after-exercise`'s line and it is a lower entry, so the rule
# has to step out of the turn rather than win it (`_offer` in bot/modules/answers.py passes a
# declined entry over and offers the next). An entry's avoid cannot say "an ache word *and* an
# exercise word", which is the shape, so the check is here.
ACHE_WORDS = ("ache", "aches", "aching", "achey", "achy", "sore", "soreness", "stiff",
              "stiffness", "tender")
# The work is named *after*, not met during: "my knee aches when i run" is a knee that hurts on
# the stairs' pattern and the rule answers it, while "my muscles are stiff after running" is the
# ache of new work. So the exercise side is a phrase with "after" in it, and a bare `run` or
# `walk` in the line is not enough: stepping out of the turn for those handed the line to the
# steps card ("my legs ache after a long walk, should I see a doctor").
EXERCISE_AFTER = ("after the gym", "after gym", "after weights", "after lifting", "after a workout",
                  "after my workout", "after the workout", "after exercise", "after exercising",
                  "after a session", "after a class", "after training", "after running",
                  "after a run", "after the run", "after a jog", "the next day", "day after",
                  "next day")


# The word that makes it an ache, not the part it is in: `ACHE_WORDS` also holds "back", "knee"
# and "arm", so "should i see a doctor about my back after the gym" read as the day-after ache and
# stepped out of the rule for a card that only keys on "sore" - and the person got the booking
# script instead of either. This is the same word list the sport card's own key uses.
_SORENESS_WORDS = frozenset(("sore", "soreness", "aching", "achy", "achey", "ache", "aches",
                             "stiff", "stiffness", "tender", "hurt", "hurts", "hurting"))


def _the_day_after_new_exercise(understood):
    """True when the line is the ache a day or two after new work, not an ache on its own."""
    if not _line_words(understood) & _SORENESS_WORDS:
        return False
    clean = str((understood or {}).get("clean") or "").lower()
    return any(phrase in clean for phrase in EXERCISE_AFTER)


def _see_doctor_reply(memory, understood):
    """The decision rule, with the part named when the line names one.

    The window is the one every muscle-and-joint card in this file already gives, "two to six
    weeks", because one back cannot settle in two to three weeks here and in two to six weeks in
    `back-went`: the same person asking twice got two numbers. And the rule comes first, in the
    line's own words, instead of a preamble about what the question is - the answer is the
    decision, with the red flags and the next step behind it.

    The ache a day or two after new work is the one shape it steps out of, so that
    `sport.sore-after-exercise` can say the ache is normal and not damage.
    """
    if _the_day_after_new_exercise(understood):
        return None
    part = _part_named(_line_words(understood), understood)
    opening = "Go by how long it has been going: "
    if part:
        article = "An" if part[:1] in "aeiou" else "A"
        opening = article + " " + part + " like that: "
    return opening + (
        "give it two to six weeks if it is steady or easing, and book sooner if it is getting "
        "worse, waking you at night or stopping you doing normal things. Go today if it came on "
        "suddenly or after a fall, or comes with a fever, numbness or pins and needles. Ask "
        "about physio when you ring; in most areas you can refer yourself.")


# The decision rule's key holds every part at once, so the back's own reading cannot be its
# guard as it stands: `_the_back_is_a_back` answers False for a line that names no back, and
# "should i see a doctor about my knee" has to keep the rule. The guard asks the back's question
# only when "back" is the only part the line names.
def _a_part_in_a_decision_is_a_part(understood):
    words = set(_reading_words(understood))
    if "back" not in words or (words - {"back"}) & set(SEE_DOCTOR_PARTS):
        return True
    return _the_back_is_a_back(understood)


ENTRIES.append(entry("see-about-a-part", (DECIDE_ASK, SEE_DOCTOR_PARTS),
                     _see_doctor_reply, bias=2, avoid=SEE_DOCTOR_AVOID,
                     guard=_a_part_in_a_decision_is_a_part))

# A line that says only "should i see someone" is a decision, and the rule is the answer to it.
# A line that names a thing - a uti, a hoarse voice, a rash, a mole, a burn - is a question about
# that thing, and its own card answers it better than a window that was written for muscles and
# joints. So the row answers only when every word left in the line is one a decision question is
# made of: a word outside this list means the line is about something, and the row stands down.
# A list of conditions would never be complete; a list of the words a bare decision is built from
# is closed, because the very thing that makes the line a decision is that it names nothing.
_DECISION_WORDS = frozenset("""
a about all also am an and any anything are as at be been being both but by can check checked
could did do does doing doctor doctors each even ever for from get gets getting go goes going got gp
gps had has have having he her here him his how i if in into is it its just look looked looking me
more most much must my myself need needed needs no nor not now of off on once one only or other our
out over own rather really same see seeing seen shall she should so some someone something still
first anyway
such sure than that the their them then there these they thing things this those through to too
under up us very wait waiting was we were what when where whether which while who why will with
worth worthwhile would yet you your
""".split())


def _a_bare_decision(understood):
    """True when the line asks the decision and names nothing else.

    "do i need to see someone" is this row's line. "i think i have a uti, do i need to see
    someone" is the uti card's line, and "my voice has been hoarse for a week, do i need to see
    someone" is the hoarse-voice card's: the rule's two-to-six-weeks window was written for a
    muscle and a joint, and it says nothing useful about either of those.
    """
    words = _line_words(understood)
    if not words:
        return False
    return all(word in _DECISION_WORDS for word in words)


def _see_doctor_decision(memory, understood):
    """The same rule for a line that names no part.

    "should i get a rash checked out" says no limb, so the physio line at the end of the part
    answer - "ask about physio when you ring" - is advice for a muscle it does not have. The rule
    and its red flags are the same, so this is the part answer with that one sentence left out
    whenever no part is named in the line.
    """
    reply = _see_doctor_reply(memory, understood)
    if reply is None or _part_named(_line_words(understood), understood):
        return reply
    return reply.replace(
        " Ask about physio when you ring; in most areas you can refer yourself.", "")

# A decision question that names no part at all - "do i need to see a doctor", "should i go to the
# doctor", "should i get it checked out" - is still the decision rule, and it was the booking
# script's line: "ring at the moment the lines open" answered a person who had not decided
# whether to ring, and "i cannot weigh that one safely" answered the ones that said "checked".
# The rule does not need a part. The parts entry above holds every part and wins those lines; this
# one is the same rule with no part named, sits after it, and loses every tie, so a card that
# already answers the line keeps it.
#
# The ask words are shared with that entry, so what keeps this one narrow is the word list and the
# fences: the mind is not a part with a how-long rule, the physio card says when to go, and a line
# that wants the appointment wants the steps rather than the decision.
ENTRIES.append(entry("see-about-it",
                     # The word is the phrase a person says, not the bare pronoun: "someone"
                     # on its own is a key any line with an ask word can reach, and the lines
                     # that need it say "see someone" or "someone about it".
                     (DECIDE_ASK, ("doctor", "gp", "see someone", "someone about",
                                   "checked", "checked out", "looked at", "seen")),
                     _see_doctor_decision, bias=0, guard=_a_bare_decision,
                     # The ask is what tells a decision from a statement of need: "i need to see
                     # a doctor" wants the steps to get seen, and it carries every word "do i need
                     # to see a doctor" has, so no fence can separate them. An ask word can.
                     ask=("should i", "do i", "can i", "could i", "would i", "shall i",
                          "is it", "any point", "worth"),
                     avoid=SEE_DOCTOR_AVOID + (
                         "appointment", "book", "booking", "register", "surgery",
                         "physio", "physiotherapy", "chiropractor",
                         "mental", "anxiety", "anxious", "depressed", "depression",
                         "counselling", "counselor", "counsellor", "therapy", "therapist",
                         "panic", "stress", "stressed", "self harm", "suicidal",
                         "dentist", "vet", "optician",
                         # a card that already answers the line: a wart has its own
                         "wart", "warts", "verruca", "verrucas",
                         # and how to get seen at a weekend is the appointment answer again
                         "weekend", "weekends", "saturday", "sunday", "bank holiday",
                         "out of hours", "evening", "evenings")))

# The same decision question about the dentist. `see-about-it` names the doctor and its rule is
# the muscle-and-joint window - "give it two to six weeks", "ask about physio" - which is no use
# for a tooth: "do i need to see a dentist" got the booking script, "ring at the moment the lines
# open - 8am for most GP surgeries", for a person who had not decided to ring anybody, and
# "should i see a dentist about my tooth" got the bleeding-gums card. A tooth is decided on what
# it is doing, so the rule is written for teeth: what can wait, what goes today, what goes back
# in the gum within the hour.
ENTRIES.append(entry("see-a-dentist",
                     (DECIDE_ASK, ("dentist", "dentists", "dental", "nhs dentist",
                                   "dental practice", "dental surgery", "emergency dentist",
                                   "out of hours dentist", "dentist or a doctor")),
                     "Go by what the tooth is doing: a twinge with cold that settles, or a check-up "
                     "you are overdue, is an ordinary appointment. Ring the dentist today if it "
                     "aches at night or keeps you awake, if there is swelling in your face or "
                     "under the jaw, a fever, a lost filling or crown that hurts, or bleeding that "
                     "will not stop. A tooth knocked right out goes straight back into the socket, "
                     "by the crown and not the root, and you are seen within the hour; ring 111 "
                     "for the out-of-hours dental service if your practice is shut.",
                     # The ask is what tells a decision from a statement of need, as it does for
                     # the doctor's row: "i need to see a dentist" wants the steps to get seen.
                     ask=("should i", "do i", "can i", "could i", "would i", "shall i",
                          "is it", "any point", "worth"),
                     # finding a practice, the interval, the fear, the price and the appointment
                     # already booked are all other rows' lines
                     avoid=("register", "registering", "registration", "taking new",
                            "new patients", "nhs patients", "how do i get", "find a",
                            "find an", "nearest", "near me", "how often", "how long since",
                            "havent been", "haven't been", "never been", "years", "ages",
                            "scared", "nervous", "afraid", "terrified", "dreading", "phobia",
                            "embarrassed", "cost", "costs", "price", "how much", "private",
                            "nhs band", "band 1", "band 2", "band 3", "free", "afford",
                            "whitening", "whiten", "braces", "implant", "implants",
                            "denture", "dentures", "appointment at", "cancel", "check up",
                            # a symptom the line names has its own card, and that card answers
                            # the question better than the decision rule: "should i see a dentist
                            # about a tooth that hurts when i bite" is what the sensitive-tooth
                            # answer is for
                            "cold", "hot", "sweet", "bite", "biting", "chew", "chewing",
                            "sensitive", "bleeding", "bleeds", "swollen", "swelling", "chipped",
                            "broken", "hole", "decay", "abscess", "went", "knocked out", "fell out",
                            "came out", "wisdom", "gums", "gum", "mouth", "jaw", "ache")))

# A back that has *gone* is the strain entry's line, not this one's: "my back went last week" is
# the middle of an injury, and the stand-and-be-careful answer is for that, not for a month of
# ache. The words that name the moment belong to `back-went`.
_GONE_BACK = ("went", "gone", "goes", "put my back out", "put it out", "pulled my back",
              "threw my back out", "thrown my back out", "in spasm", "locked", "did my back in")


# A body word the verb has taken is not the person's part. "my mate hasnt text me back in a
# week" reached the sore-back-for-a-week row on the pair "back" + "week" and answered a text
# message with a physio plan, and "he rang her back about the boiler" and "she got back to me
# yesterday" are the same shape. The verb is the owner, and the pronoun between the two ("text
# *me* back") is how people say it, so the look is two words back and not one. The same words at
# the top of this file only catch the bare ones ("come back", "back up"), because they are a
# list of spellings and the verb is open-ended.
_A_VERB_TOOK_THE_BACK = re.compile(
    r"\b(?:text|texts|texted|texting|message|messages|messaged|messaging|msg|dm|dm'd|"
    r"call|calls|called|calling|ring|rings|rang|ringing|phone|phones|phoned|phoning|"
    r"email|emails|emailed|emailing|write|writes|wrote|written|writing|reply|replies|replied|"
    r"replying|answer|answers|answered|answering|hear|hears|heard|hearing|get|gets|getting|got|"
    r"pay|pays|paid|paying|send|sends|sent|sending|bring|brings|brought|push|pushes|pushed|"
    r"hold|holds|held|look|looks|looked|turn|turns|turned|talk|talks|talked|take|takes|took|"
    r"step|steps|stepped|sit|sits|sat|lean|leans|leant|lie|lies|lay|fall|falls|fell|walk|walks|"
    r"walked|move|moves|moved|drive|drives|drove|run|runs|ran|hit|hits|fight|fights|fought|"
    r"come|comes|came|coming|go|goes|going|went|gone|"
    # A garment that has shrunk is stretched back: "my jeans shrank in the wash, can i stretch
    # them back" reached the bad-back row on "back" + "stretch" and answered a shrunken jumper
    # with a physio plan for the lower back. The washing has the back, not the person.
    r"stretch|stretches|stretched|stretching|shrink|shrinks|shrank|shrunk|shrinking)"
    r"\s+(?:(?:me|him|her|us|them|you|it|myself|yourself|himself|herself|themselves)\s+)?back\b"
)
# ...unless the line says the part is theirs, or that it hurts, which it always does when the
# back is the body: "i walked back from the shop and my back is killing me" keeps the row.
_THE_BACK_IS_THEIRS = re.compile(
    r"\b(?:my|your|his|her|our|their|the|this|that)\s+back\b"
    r"|\b(?:sore|bad|lower|upper|stiff|aching|soreness|painful)\s+back\b"
    r"|\bback\s+(?:pain|ache|aches|aching|hurts?|hurting|problem|trouble|spasm|went|gone)\b"
    r"|\bback\s+(?:is\s+)?(?:killing|kills)\b")


def _the_back_is_the_persons(understood):
    """False when the line's "back" is the verb's particle and nothing else.

    Used as an entry `guard` on the sore-back-for-a-week row, which is the one row whose key is
    "back" plus a duration - the shape a text message and a sore back share.
    """
    clean = str((understood or {}).get("clean") or "").lower().replace("\u2019", "'")
    if not _A_VERB_TOOK_THE_BACK.search(clean):
        return True
    # The verb's own back goes before the question is asked, so "he rang her back about the
    # boiler" is not read from the "her back" inside it.
    return bool(_THE_BACK_IS_THEIRS.search(_A_VERB_TOOK_THE_BACK.sub("  ", clean)))


# One entry per part, with only that part's words in its key. A single key holding every part is
# matched by chat's "the answer we gave about this topic" look-up (the entry's key words are kept
# with the answer), so the tailbone card was quoted back for "30 weeks pregnant and my back hurts"
# - the word "back" was in the tailbone entry's key too.
ENTRIES += [entry(f"sore-{name}-weeks", (parts, WEEKS),
                  _sore_weeks_reply,
                  # the duration words are this entry's whole point, so they come out of the
                  # region table's avoid list; the red flags, the other people's parts, the
                  # pregnancy and the "see a doctor" lines all stay out of its reach
                  avoid=tuple(w for w in AVOID if w not in STANDING) + _GONE_BACK
                  + _SPORT_WORDS
                  + ("pregnant", "pregnancy", "expecting", "trimester", "weeks pregnant",
                     "months pregnant"),
                  guard=_the_back_is_the_persons if name == "back" else None,
                  )
            for name, parts, reply in REGIONS]


# A part somebody has had trouble with for years is a standing condition, not a fresh strain, and
# the back was the only one that had an answer: "i have a bad back" would otherwise reach the chat
# reply ("Ugh, that's rotten. Take it slow today"), which is a sympathy line rather than an answer,
# and every other part went the same way - "whats a good exercise for a bad knee" got "Sorry to
# hear that", "is swimming good for a bad shoulder" the same, and "how do i strengthen my knees"
# the offer to search. What the line asks is which movement is safe and which builds the part up,
# and `_WEEKS_DRILL` already keeps one move per part for the weeks row, so the same drill answers
# here, with the kind cardio named for the parts that carry weight.
# The movement words are the standing part's own question too: "best exercises for a bad back"
# and "exercises for back pain" were a shrug while "stretches for a bad back" answered, because
# the row's key held only "bad" and the after-a-new-workout fence ("exercised" loose-matches
# "exercises") stood it down. The one-session words ("gym", "workout") stay out of the key, so
# "my back is killing me after the gym" keeps the sore-muscle card.
_BAD_PART_MOVEMENT = ("exercises", "exercise", "stretches", "stretching", "physio")
# The words that say the part is a standing trouble rather than a fresh knock. Kept apart from the
# movement words above, because the region rows stand down for these only: an ache that names
# "exercise" in passing is still a fresh ache and keeps the resting answer.
_STANDING_TROUBLE = ("bad", "badly", "dodgy", "gammy",
                     # the other way the same question is asked: nobody with a bad knee asks what
                     # is "bad", they ask what would strengthen it
                     "strengthen", "strengthening", "stronger", "build up", "building up",
                     "crap")
_BAD_PART_WORDS = _STANDING_TROUBLE + _BAD_PART_MOVEMENT
# The parts whose trouble is made worse by the pounding of running, so the answer says which
# movement to do instead. A wrist or an elbow has no such trade.
_CARRIES_WEIGHT = ("back", "spine", "knee", "kneecap", "hip", "ankle", "foot", "heel",
                   "leg", "calf", "thigh", "hamstring", "shin", "toe")

ENTRIES += [entry("bad-back",
                  (tuple(w for _name, parts, _r in REGIONS if _name == "back"
                         for w in parts), _BAD_PART_WORDS),
                  "A back that gives trouble on and off is usually muscular, and what keeps it "
                  "quiet is strength and movement rather than rest: walk most days, and add two "
                  "short sessions a week of a slow bridge lying down or sit-to-stand from a "
                  "chair. Ask your GP about physio if it is stopping you sleep or work, and ring "
                  "111 the same day if you cannot pass urine, have numbness between your legs, or "
                  "it came on after a fall.",
                  # the back's own wording is pinned by tests and carries the physio line, so it
                  # keeps winning over the per-part row that would otherwise answer "strengthen
                  # my back"
                  bias=3,
                  # the back this row is about is the person's own: a line whose only "back" is
                  # the verb's particle ("stretch them back", "wash it back") is about the thing
                  guard=_the_back_is_the_persons,
                  # the day-after-the-gym words are the sore-muscle card's, but "exercises" is
                  # the same stem and it is the commonest way this question is asked, so the
                  # sport words carry that fence here instead
                  avoid=tuple(w for w in AVOID
                              if w not in STANDING and w not in EXERCISE_DAY) + _GONE_BACK
                  + _SPORT_WORDS
                  # "my back has been bad for months" is the weeks row's, which says when to ask
                  # about physio; this row is for a part with no duration on it
                  + WEEKS
                  + ("pregnant", "pregnancy", "expecting", "weeks pregnant",
                     "months pregnant"))]


def _the_part_is_named_today(understood):
    """This line names the part itself, and it is the person's own part they can still use.

    A later turn about a part is read with the earlier line put back in it, so the ankle of "my
    ankle hurts after football" is in the room when "is that bad" is asked - and the two words
    that fit this row's key are "bad" and the part, which is exactly that follow-up. The drill is
    advice for a part somebody has had trouble with for years, and a sprain from Saturday is not
    that, so the part has to be in the line as it was typed. A reading with no text of its own is
    one the store made by putting an earlier subject back in, and it never speaks for this row.
    """
    if not the_part_that_keeps_grumbling(understood):
        return False
    said = (understood or {}).get("text")
    if not isinstance(said, str) or _REPORTED_COMPLAINT.search(said):
        return False
    typed = set(re.findall(r"[a-z']+", said.lower().replace("\u2019", "'")))
    return bool(_part_named(typed))


# A line that reports a complaint - "i have a bad shoulder", "ive had a dodgy knee for years" - is
# answered by the part's own card, and the composer reads those lines itself (`COMPLAINT` and
# `_a_complaint_answered` in the answers module) by asking the health rows what can be done about
# the thing reported. That reading only starts when the line has not already found an entry, so a
# row that matched the report would take the turn from the card that knows the part: "i have a bad
# shoulder" got the shoulder card on main and this row's general drill with the row added. The row
# below answers the ask about a part instead, and a report is left to the part's own answer.
_REPORTED_COMPLAINT = re.compile(
    r"\b(?:i (?:get|have|had|keep getting|keep|suffer from|live with)|"
    r"i(?:'ve|ve) (?:got|had|been having))\b", re.I)


def _bad_part_reply(memory, understood):
    part = _part_named(_line_words(understood)) or _part_named(_words(understood)) or "joint"
    article = "An" if part[:1] in "aeiou" else "A"
    drill = _WEEKS_DRILL.get(part, "two short sessions a week of the movement you want to keep, "
                                    "stopping short of pain")
    instead = ("Swimming, cycling and a flat walk are the kind ones on the other days."
               if part in _CARRIES_WEIGHT
               else "Keep the rest of you moving, and use it as far as is comfortable.")
    return (article + " " + part + " that gives trouble on and off is usually weak muscle round "
            "a joint that does not like one particular movement, and building it up is what "
            "keeps it quiet: " + drill + ". " + instead + " Get it looked at if it gives way, "
            "locks, or swells up after a knock.")


# The same standing-condition row for every other part. A shoulder, a hip and an ankle had no
# answer of this kind at all: "how do i strengthen my ankles" was the offer to search, "my ankle
# is dodgy" the echo "Got it - is there anything you'd like a hand with?", and "whats good for a
# bad wrist" a sympathy line. The knee keeps its own longer answer below.
ENTRIES += [entry("bad-" + name, (parts, _BAD_PART_WORDS), _bad_part_reply,
                  guard=_the_part_is_named_today,
                  # a row that already answers the part is the one to keep: the wrist, the hip,
                  # the neck and the shoulder each have a card about the complaint itself, and
                  # "i have a bad shoulder" belongs to the one that says what a bad shoulder
                  # usually is. This row is for the part no card covers, and for the ask those
                  # cards do not read ("whats a good exercise for a bad shoulder")
                  bias=-1,
                  avoid=tuple(w for w in AVOID
                              if w not in STANDING and w not in EXERCISE_DAY) + _GONE_BACK
                  # a line about running or the gym with a bad part is sport's: it knows the
                  # mileage and the shoes, and this row only names the kind movement. Swimming
                  # and cycling are left out of the fence on purpose, because "is swimming good
                  # for a bad knee" is this question and sport has nothing kinder to say.
                  + tuple(w for w in _SPORT_WORDS
                          if w not in ("swim", "swimming", "cycle", "cycling"))
                  # "my knee has been bad for months" is the weeks row's, which says when to
                  # ask about physio; this row is for a part with no duration on it
                  + WEEKS
                  # a pull or a strain is a fresh injury with its own first aid, and the region
                  # row knows it; this row is for the part that keeps grumbling
                  + ("pulled", "pull", "strained", "sprain", "sprained", "torn", "tear",
                     "injured", "injury")
                  + ("pregnant", "pregnancy", "expecting", "weeks pregnant",
                     "months pregnant"))
            for name, parts, _reply in REGIONS if name not in ("back", "knee")]

# The part of the body nobody has hurt yet is the part nobody has an answer for. "how do i protect
# my back" was the offer to draft something together, "how do i look after my knees" the same, and
# the same shape of line about a shoulder, a hip or an ankle reached nothing at all. Every one of
# them is the strength-and-use question the part rows already answer, asked a day earlier: what
# keeps the part quiet is the same thing that keeps it from going, and the per-part drill is
# already the table below. So the row is the *ask* (protect, look after, take care of, keep
# strong) plus the part, and the answer is the drill for that part.
_PROTECT_ASK = ("protect", "protects", "protecting", "protection",
                "look after", "looking after", "looks after",
                "take care of", "taking care of", "takes care of", "care for", "caring for",
                "keep strong", "keep it strong", "keep them strong", "keep healthy",
                "keep it healthy", "keep supple", "keep flexible",
                "avoid injury", "avoid injuring", "prevent injury", "prevent a strain")
_ALL_PART_WORDS = tuple(w for _name, spelled, _r in REGIONS for w in spelled)


# The row above is the day before the trouble, and the cards for a desk, a run and a pair of shoes
# are the day of it: "how do i protect my wrists at a desk" is the posture card's line, "how do i
# save my knees when running" the running one. So this row takes only a line that names nothing
# except the part and the wish to keep it well - a part with a desk, a sport or a shoe in the line
# beside it belongs to the card that knows that thing.
_PROTECT_FILLERS = frozenset("""
    a an the and or of to for in on at with my your me it them i we you
    how do does did can could should would whats what is are be been
    best way ways good better keep keeps keeping well healthy strong stronger
    supple flexible care careful carefully properly safely help home
""".split())
_PROTECT_ALLOWED = _PROTECT_FILLERS | set(_ALL_PART_WORDS) | set(
    w for phrase in _PROTECT_ASK for w in phrase.split())


def _the_ask_names_nothing_else(understood):
    """True when the line is only the wish and the part, with no desk, sport or shoe in it."""
    said = (understood or {}).get("clean") or (understood or {}).get("text") or ""
    if not isinstance(said, str):
        return False
    words = set(re.findall(r"[a-z']+", said.lower().replace("\u2019", "'")))
    return all(_in_the_allow_list(w) for w in words)


def _in_the_allow_list(word):
    """True when the word is the allow list's own, or that word with a plural or -ing on it."""
    if word in _PROTECT_ALLOWED:
        return True
    for tail in ("ing", "es", "s", "ed", "d"):
        stem = word[:-len(tail)] if word.endswith(tail) else ""
        if len(stem) >= 3 and stem in _PROTECT_ALLOWED:
            return True
    return False


def _protect_reply(memory, understood):
    part = (_part_named(_line_words(understood), understood)
            or _part_named(_words(understood), understood) or "joint")
    article = "An" if part[:1] in "aeiou" else "A"
    drill = _WEEKS_DRILL.get(part, "two short sessions a week of the movement you want to keep, "
                                    "stopping short of pain")
    if part in _CARRIES_WEIGHT:
        instead = ("Swimming, cycling and a flat walk are the kind ones on the other days. Warm "
                   "up before a big job, keep the load close to you when you lift, and change "
                   "position every half hour rather than holding one.")
    else:
        instead = ("Keep it moving every day rather than resting it, and keep it in the middle of "
                   "where it moves - not locked straight, not at the end of its range.")
    return (article + " " + part + " is protected by the muscle round it and by how you use it "
            "more than by anything you wear or avoid: " + drill + ". " + instead)


ENTRIES += [entry("protect-a-part", (_PROTECT_ASK, _ALL_PART_WORDS), _protect_reply,
                  guard=_the_ask_names_nothing_else,
                  # a part that is already bad is the part's own card's, not the day-before-it
                  # question this row answers
                  avoid=STANDING + EXERCISE_DAY + WEEKS + _GONE_BACK +
                  ("injury", "injured", "hurt", "hurts", "hurting", "pain", "painful", "ache",
                   "aches", "aching", "sore", "swollen", "swelling",
                   # a burn, a bite and the sun are their own answers
                   "sun", "sunburn", "sunburnt", "burn", "burnt", "burned", "suncream",
                   "sun cream", "sunscreen", "bites", "bitten", "graze", "gravel",
                   "burn", "sting", "stung",
                   # the eyes and the hearing are not joints, and their own answers hold them
                   "eyes", "eye", "hearing", "ears", "ear", "teeth", "tooth", "gums",
                   # the foot already has a card about looking after it: "how do i look after my
                   # feet" was answered with shoes, mileage and the heel that hurts first thing,
                   # and that is a better answer than this one
                   "feet", "foot", "heel", "toes", "toe", "plantar",
                   "pregnant", "pregnancy", "expecting"))]

# "exercises for bad knees" and "what exercise can i do with a bad knee" both reached nothing -
# one a "say more" echo and the other a sympathy line - while the same question about a back has had
# an answer for a long time. A knee that gives trouble on and off is a strength question too.
KNEE_WORDS = ("knee", "knees", "kneecap", "patella")
_STANDING_KNEE = ("bad", "badly", "dodgy", "weak", "trouble", "troublesome", "sore", "aching",
                  "aches", "worn", "wear and tear", "arthritis", "arthritic", "stiff",
                  "stiffness", "exercises", "exercise", "strengthen", "strengthening")
ENTRIES += [entry("bad-knee",
                  (KNEE_WORDS, _STANDING_KNEE),
                  "A knee that gives trouble is helped most by the muscle above it: sit-to-stands "
                  "from a chair, step-ups onto a low step and straight-leg raises, two or three "
                  "times a week, which builds the thigh muscle that takes the load off the joint. "
                  "Keep walking on the flat and skip deep squats and running downhill; a physio "
                  "can set the pace. A knee that locks, gives way or swells hot needs a GP.",
                  # an injury, the click and creak question, the front-of-knee stairs pain, the
                  # walking answer and a knee after an operation each have their own answer
                  avoid=("twisted", "twist", "twisting", "sprain", "sprained", "tore", "torn",
                         "pop", "popped", "swollen", "swelling", "swells", "locked", "locks",
                         "gave way", "gives way", "gave out", "gave in", "snapped", "fell",
                         "fall", "fallen", "stairs", "stair", "upstairs", "downstairs",
                         "running", "run", "runner", "marathon", "football", "rugby", "squat",
                         "squats", "operated", "operation", "replacement", "replaced", "keyhole",
                         "arthroscopy", "injection", "steroid", "pregnant", "pregnancy",
                         "how long", "recovery", "recover", "crutches", "brace", "support",
                         "click", "clicks", "clicking", "clicked", "creak", "creaks", "creaking",
                         "noise", "noisy", "grind", "grinds", "grinding", "crackle", "crackles",
                         "crackling", "pops", "popping", "rattle", "rattles",
                         "walk", "walking", "walked", "steps", "step count", "how far"))]

# A back that hurts in pregnancy is the one back the region table deliberately passes on: its
# avoid list holds "pregnant", because the answer it gives offers ibuprofen, and ibuprofen is
# not what a pregnant woman should be taking. The line then got the pressing note or the honest
# shrug ("im 30 weeks pregnant and my back hurts, what can i do" -> "I don't know enough to
# answer that"), and "my back is killing me and im 6 months pregnant" got congratulated, which
# is how it reads when the only thing in the line a table recognises is the pregnancy.
# Words the region table avoids that the pregnancy answer must keep: the pregnancy itself and
# the count of weeks, both of which the general back entry reads as "not this answer".
BACK_PREGNANCY_KEEP = ("pregnant", "pregnancy", "weeks", "months", "for weeks", "for months",
                       "for a month", "for a fortnight", "a few weeks", "two weeks",
                       "three weeks", "a week now", "for ages")
PREGNANT = ("pregnant", "pregnancy", "pregnancies", "weeks pregnant", "months pregnant",
            "expecting a baby", "expecting", "trimester", "due in", "due next month",
            "due in a few weeks")
ENTRIES += [entry("back-pain-pregnant",
                  (("back", "lower back", "spine", "backache", "hips", "pelvis", "sciatica"),
                   PREGNANT),
                  "Back pain is very common in the second half of pregnancy: the weight sits out "
                  "in front, and the hormone that loosens your ligaments for the birth loosens "
                  "them everywhere. Paracetamol is the painkiller to use; steer clear of ibuprofen "
                  "and the other anti-inflammatories unless your midwife or doctor has said they "
                  "are fine for you. A maternity support belt, flat shoes, a warm bath and sleeping "
                  "on your side with a pillow between your knees all take the strain off, and your "
                  "midwife can refer you to a physiotherapist who deals with exactly this. Ring "
                  "your midwife or maternity unit the same day if the pain comes with bleeding, any "
                  "waters, a bad headache, blurred vision or swelling in your hands and face, a "
                  "temperature, stinging when you pass urine, or the baby moving less than usual.",
                  # a back that hurts on its own is the region table's, and the red-flag words
                  # there (numbness, cannot pass urine) still belong to the emergency reading
                  # the region table's duration words ("weeks", "months", "for a fortnight")
                  # are there to spot a strain that has dragged on; in this line they are how
                  # far along the pregnancy is, and the count is the most ordinary thing in it
                  avoid=tuple(w for w in AVOID if w not in BACK_PREGNANCY_KEEP)
                  # and the other way round: "my back is sore, im not pregnant" is the general
                  # answer's line, so a line that says it is not this one stands down
                  + ("not pregnant", "not expecting", "no longer pregnant"),
                  bias=2,
                  # the words a person uses for a bad back, and "backache" is one word that a
                  # key of "back" plus "ache" does not reach: "ive got awful backache and im 7
                  # months pregnant" found nothing at all
                  ask=("back", "hurts", "hurt", "ache", "aching", "backache", "back ache",
                       "bad back", "pain", "painful", "sore", "sciatica", "killing me", "agony"),
                  # "expecting" is a pregnancy word and also the word in "i keep expecting her to
                  # come back": with the particle phrases gone from _NOT_A_BODY_PART that line
                  # reached this card, which told a grieving person about a maternity belt. The
                  # back has to be a back here too.
                  guard=_the_back_is_a_back),
          ]
# A fever is not a part that hurts, and it is asked as one of two questions: what to do about it,
# and whether it needs looking at. Both start the same way, so one entry answers both, and the
# signs that send somebody to a doctor are part of the answer rather than a second entry.
# "how do i bring a fever down" and "should i take my child to the doctor with a fever" were a
# shrug and the time-off script on main.
# "how long does a fever last" asks about the clock, and the bring-it-down advice answers a
# different question. Most fevers settle in a few days; the red flags do not change.
_FEVER_ADVICE = ("Treat how they seem, not the number: cool clothes and plenty to drink do more "
                 "than the thermometer, plus paracetamol or ibuprofen at the dose on the pack if it "
                 "is making them miserable. Don't sponge with cold water or use both to chase the "
                 "number. Get seen the same day for a baby under three months with 38C, a rash that "
                 "will not fade under a glass, a stiff neck, breathing trouble, a fit, or a child "
                 "floppy or not drinking; ring 111 if unsure.")


_TAKE_A_TEMPERATURE = (
    "Use a digital thermometer under the tongue or in the armpit: wait 20 minutes after a hot or "
    "cold drink, tuck the tip under the tongue and keep it there until it beeps. In the armpit, "
    "dry the skin first and hold the arm clamped to the body, which reads about half a degree "
    "lower than the mouth. An ear thermometer has to point across towards the other eye to read "
    "right, and write the number and the time down if you are watching a fever.")
# "how do i take a temperature" was answered with the treat-the-fever card ("Treat how they seem,
# not the number"), because both are put with "temperature" and "how do i". A person asking where
# to put the thermometer wants the steps, and the fever entry answers the other question ("what do
# i do about a fever", "how long does a fever last"), so the steps get a row of their own and the
# number and the red flags stay with the fever entry.


def _take_a_temperature(memory, understood):
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if "without" in said:
        # "how do i take my temperature without a thermometer" is the same how-to with the tool
        # taken away, and the steps for using one are no answer to it.
        return ("Without a thermometer there is no number to take, so go by how they seem: a hot "
                "back or neck, flushed cheeks, shivering, and a hand on the skin is a poor guide "
                "either way. Don't pile layers on or take them off to chase a guess, and get "
                "anyone seen the same day if a baby under three months feels hot, or they are "
                "floppy, breathing fast or not drinking.")
    return _TAKE_A_TEMPERATURE


def _fever_reply(memory, understood):
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if "how long" in said or "last" in said or "how many days" in said:
        return ("Most fevers from a virus settle within two or three days, and the last day is "
                "usually lower than the first. Have it looked at if it has been there five days or "
                "is still climbing, or if it goes away and comes back. Treat how they seem rather "
                "than the number, and get seen the same day for a baby under three months with "
                "38C, a rash that will not fade under a glass, a stiff neck, breathing trouble or "
                "a fit.")
    return _FEVER_ADVICE


# The medicine question comes before the timeline: a parent asking "can i give my child ibuprofen
# with chickenpox" should read "no, use paracetamol" in the first sentence, not in the last clause.
_CHICKENPOX_TIMELINE = ("They are infectious from about two days before the rash appears until "
                        "every spot has crusted over, usually five days after the rash first "
                        "shows, which is when they can go back to school.")


def _chickenpox_reply(memory, understood):
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if "ibuprofen" in said or "nurofen" in said or "brufen" in said:
        return ("No - avoid ibuprofen with chickenpox, because it is linked to a serious skin "
                "infection in children who have it. Use paracetamol at the dose on the pack, "
                "calamine or a cool bath for the itch, and keep the nails short so the spots do not "
                "scar. They are infectious from two days before the rash until every spot has "
                "crusted over, usually five days, which is when they can go back to school.")
    return (_CHICKENPOX_TIMELINE + " Calamine or a cool bath eases the itch, paracetamol helps the "
            "temperature and short nails stop the spots scarring; avoid ibuprofen. Ring the GP if "
            "a newborn, a pregnant woman or anyone with a weak immune system has been in contact.")


ENTRIES += [
    entry("fever-rest", (("fever", "temperature", "high temperature", "burning up", "shivery"),
                    ("bring down", "lower", "reduce", "get rid", "what can i do", "what should i do",
                     "how do i", "should i worry", "worried", "how long", "when should i",
                     "see a doctor", "doctor", "gp", "hospital", "paracetamol", "ibuprofen",
                     "calpol", "medicine", "worry", "help")),
          _fever_reply,
          avoid=("oven", "thermostat", "heating", "room", "house", "home", "fridge", "freezer",
                 "cook", "bake", "set the", "washing", "hob", "air fryer", "boiler", "bedroom",
                 "weather", "outside", "garden", "how hot", "the sea", "pool", "chickenpox",
                 # "hay fever" holds the word "fever" and is not one: "how do i get rid of hay
                 # fever" was answered with the treat-the-child-not-the-number card, which talks
                 # about a baby of three months and a rash. The allergy season has its own entry
                 # (science.hayfever), so a line that says hay fever is not this one's.
                 "hay fever", "hayfever", "hay-fever", "pollen", "allergy season",
                 # An illness with a name has its own card, and its timeline is part of it:
                 # "how long does glandular fever last" and "what is scarlet fever" were taking
                 # this row's what-a-fever-is answer off the single word "fever".
                 "glandular fever", "glandular", "scarlet fever", "scarlet",
                 "rheumatic fever", "dengue", "typhoid", "malaria")),
    entry("take-a-temperature",
          (("thermometer", "thermometers", "temperature", "temps"),
           ("take", "takes", "taking", "read", "reading", "use", "using", "best way",
            "under the arm", "under my arm", "underarm", "armpit", "armpits", "ear", "mouth",
            "oral", "forehead", "accurate", "accurately")),
          _take_a_temperature,
          # the probe in a joint and the oven's dial are the cooking rows' lines, and the same
          # words reach both: "how do i use a meat thermometer" is not a fever question, and
          # cleaning one is a different how-to again
          avoid=("meat", "chicken", "pork", "beef", "lamb", "turkey", "joint", "steak", "roast",
                 "cooked", "cooking", "doneness", "oven", "fan oven", "air fryer", "bake",
                 "baking", "bread", "cake", "sugar", "jam", "oil", "frying", "boiling water",
                 "without a thermometer", "no thermometer", "hay fever", "hayfever",
                 # a house has a temperature too: the bath, the boiler, the butter and the room
                 # are the home rows' lines, and "how do i get butter to room temperature" was
                 # answered with these steps
                 "room temperature", "room temp", "butter", "boiler", "flow temperature",
                 "radiator", "fridge", "freezer", "washing machine", "tumble dryer", "bath",
                 "bathing", "heating", "greenhouse", "wine", "beer", "water", "washing up",
                 "frying pan", "cooker", "hob", "kettle", "saucepan", "milk", "yogurt",
                 "dough", "yeast", "sourdough", "stock", "soup", "sauce", "sugar", "jam",
                 "homebrew", "aquarium", "fish tank", "pond", "compost", "kiln", "sauna",
                 "sterilis", "steriliz", "disinfect", "clean", "washing", "wash the",
                 "fever", "feverish", "chickenpox", "rash"),
          # the fever entry's key holds the phrase "how do i", which this one does not (a bare
          # follow-up "and what temperature" must not be read as a how-to), so the nudge is what
          # puts this row over the fever card on "how do i take a temperature"
          bias=3),
    # Chickenpox has its own timeline and its own rule about medicine, so it is not the fever
    # entry: the question is how long they are off school and what to put on the spots.
    entry("chickenpox", (("chickenpox", "chicken pox", "spots", "blisters", "scabs"),
                         # "my daughter has chickenpox" was the composer's carer line ("are they
                         # drinking and keeping it down?"), because the second part named "child"
                         # and "kid" and not the son, daughter, toddler or baby a parent actually
                         # types. The row's own answer is the one that line wants.
                         ("chickenpox", "chicken pox", "how long", "contagious", "infectious",
                          "school", "nursery", "childminder", "child", "children", "kid", "kids",
                          "baby", "toddler", "son", "daughter", "little one", "last", "calamine",
                          "cream", "bath", "ibuprofen", "paracetamol", "back to school",
                          "off school", "catch")),
          _chickenpox_reply,
          avoid=("sun", "sunburn", "sunbed", "freckle", "freckles", "mole", "moles", "acne",
                 "face wash", "makeup", "wall", "paint", "grease", "brass", "stain", "stains",
                 "remove", "get out", "spot cream", "spot treatment", "best", "buy", "which",
                 "product", "products")),
]

# Hands that go numb in bed are a nerve question with its own first move, and the region table
# has no entry for "numb" at all (it is a red flag word for the back, so it must stay careful).
NUMB_HANDS = (
    "Hands and fingers that go numb, often in bed or after holding a phone, or that cannot be "
    "felt at all, are usually a nerve being pressed, most often the median nerve at the wrist "
    "(carpal tunnel), which is why the thumb and first two "
    "fingers tingle and "
    "shaking the hand brings it back. Sleep with the wrist straight - a soft splint from a "
    "pharmacy keeps it that way - and take breaks from gripping and typing. See a GP if it "
    "starts happening in the day, the hand weakens or wastes, or it is numb all the time.")
NUMB_ASK = ("numb", "numbness", "pins", "needles", "tingling", "dead", "asleep", "wake",
            "wakes", "waking",
            # a hand that cannot be felt is asked about in these words and none of the above
            "feel", "feeling", "cannot", "no feeling", "lost feeling")
NUMB_AVOID = ("leg", "legs", "feet", "foot", "toes", "back", "saddle", "pee", "urine")
# `arm` is not in this tuple: the bed-time entry keys a part and a time, and a bare "my arm
# is numb" has no time, so the arm went to the bed answer. The arm has its own entry in
# health.py now, and "my arm is numb in bed" still reaches this one through "in bed".
HAND_PARTS = ("hand", "hands", "fingers", "finger", "thumb", "wrist", "wrists")
ENTRIES.append(entry("numb-hands-night",
    (("numb", "numbness", "pins and needles", "tingling"),
     HAND_PARTS + ("night", "nights", "in bed", "asleep", "wake me", "wakes me", "waking up",
                   "morning", "driving", "phone", "cycling")),
    NUMB_HANDS,
    ask=NUMB_ASK,
    avoid=NUMB_AVOID))
# ... but "dead", "gone to sleep" and "asleep" are what a phone and a car battery are too, and
# the time words that carry the entry above handed them the carpal tunnel answer: "my phone was
# dead" in a chat about a missed bus was read as numb hands. A word a thing can be is only a
# body when the line names the body, so this arm asks for the part and takes no time or place.
ENTRIES.append(entry("dead-hand",
    (("dead", "gone to sleep", "asleep",
      # People say a hand they cannot feel rather than a hand that is numb: "i cant feel my
      # fingers" and "i cant feel my thumb" were a shrug, while "my fingers are numb" answered.
      "cant feel", "can't feel", "cannot feel", "no feeling", "lost feeling",
      "lost the feeling", "feel nothing"),
     HAND_PARTS),
    NUMB_HANDS,
    ask=NUMB_ASK,
    avoid=NUMB_AVOID))

# --- the foot that has gone numb, and the chest that is tight --------------------------
# "my foot is numb" was a shrug on main: the saddle card stands down for a foot (a cold foot is
# not a numb groin) and the hand cards name a hand, so nothing answered the commonest version of
# it. A foot on its own is the same pressed nerve, in a shoe or under a leg, and the two flags
# that belong to it - a back, and the waterworks - travel with the answer instead of a separate
# card, because a card for a foot must not be learned as "never urgent".
# "toes" is left out on purpose: a toe that goes numb is Raynaud's card on main, and it names
# the white-then-blue that a foot card does not, so the smaller part keeps its own answer.
FOOT_PARTS = ("foot", "sole", "heel", "instep", "ankle")
NUMB_FOOT = (
    "A foot that has gone numb is usually a nerve being pressed - a tight shoe, a leg crossed "
    "over it, kneeling or sitting on it - and the feeling comes back over a few minutes as the "
    "pressure comes off. Shake it out, walk on it and change position rather than rubbing it. "
    "If it keeps happening, or both feet are numb, it is worth a GP visit for the usual causes: "
    "diabetes, a B12 or thyroid problem, a trapped nerve from the back, and narrow shoes. Both "
    "feet numb with back pain, or no feeling between the legs with trouble weeing, is the "
    "same-day one: ring 111, or 999 if the back has given way. A sudden cold, white or blue "
    "foot, or a foot that drags, is 999.")
NUMB_SHOE = ("shoe", "shoes", "boot", "boots", "sock", "socks", "laces", "tight", "sitting",
             "crossed", "kneeling", "sleep", "asleep", "cold", "white", "blue", "swollen",
             "broken", "sprained", "walking", "run", "running", "cycling", "bike", "driving",
             "work", "standing", "long")
ENTRIES.append(entry(
    "numb-foot",
    (FOOT_PARTS, ("numb", "numbness", "pins and needles", "tingling", "no feeling",
                  "cant feel", "can't feel", "gone numb", "went numb", "dead", "asleep")),
    NUMB_FOOT,
    ask=("numb", "numbness", "pins", "needles", "tingling", "no feeling", "gone numb",
         "went numb", "dead", "asleep", "feel"),
    # A foot that has gone numb *with* a back, or with the waterworks, is the cauda equina
    # question and it has its own card in this file, which says the same-day words and nothing
    # about tight shoes. This row was taking those lines and answering "usually a nerve being
    # pressed", because it names the foot and the flag row names the back: "my back hurts and i
    # cant feel my foot" is not a shoe. The flag row is left to answer it, so the words that
    # make a foot a red flag are held here.
    # A back *is fine* is not a back: the phrases are the hurting ones, so "my back is fine but my
    # foot is numb" still gets the foot. Everything with a sore back in it is the other card's.
    avoid=("backache", "back ache", "back pain", "my back hurts", "my back is sore", "sore back",
           "aching back", "bad back", "my back went", "my back has gone", "my back is killing",
           "back is killing", "my back is bad", "back spasm", "lower back", "spine", "spinal",
           "slipped disc", "sciatica", "between my legs",
           "bladder", "wee", "weeing", "peed", "pee", "peeing", "urine", "urinate",
           "catheter", "incontinent", "bowels", "no urine", "wet myself", "wetting myself"),
    bias=1))
# "i have a tight chest" was the asthma card, which names one of three causes and gives the
# inhaler answer to anxiety or to a chest infection. The three feel alike, so the card names
# them, and the one combination that must not wait is said last and in the plainest words.
TIGHT_CHEST = (
    "A tight chest has three common causes and they feel much alike. Asthma: a wheeze, a cough "
    "at night or with cold air or exercise, which eases with a blue reliever inhaler. Anxiety: "
    "a fast heart, tingling hands, and it comes in waves of ten or twenty minutes, often when "
    "you are wound up. A chest infection: a fever, a wet cough and feeling rough, which needs "
    "seeing if you are breathless or it is going on. Sudden tightness with pain spreading to "
    "the jaw, neck or arm, sweating, or breathlessness while sitting still is 999. If it keeps "
    "coming back, see a GP and say when it happens - they may give you a peak flow meter or an "
    "inhaler to try.")
ENTRIES.append(entry(
    "tight-chest",
    (("chest", "in my chest", "my chest"),
     ("tight", "tightness", "tightening", "tightens", "constricted", "band", "pressure",
      "heavy", "weight")),
    TIGHT_CHEST,
    # a chest that is tight is not a machine, a heartburn or a cough on its own, and the other
    # half of the match - "heavy" - is what a chest of drawers and a heartburn are
    avoid=("heartburn", "acid", "reflux", "indigestion", "cough", "cold", "flu", "covid",
           "drawers", "fridge", "freezer", "box", "packing", "suitcase", "lift", "carry",
           "exercise", "running", "run", "gym", "when i run", "when i exercise",
           "dog", "cat", "baby", "child", "toddler", "muscle", "muscles", "gym"),
    bias=1))

# Joints are not one of the parts above: "my joints ache" names no part at all, and a knuckle is
# not a wrist. The advice is the same for every joint, so it is one entry keyed by the word for
# the joint plus a word for hurting. It carries a bias because "my joints ache when it is cold"
# was read as the flu-recovery answer, which keys "cold" and "ache", and because the cracking
# answer in science.py stands aside for the word "hurt" on the promise that a pain answer exists.
ENTRIES.append(entry(
    "aching-joints",
    (("joints", "joint", "knuckles", "knuckle"),
     HURT),
    "Most aching joints are ordinary wear and tear - osteoarthritis - and keeping them moving is "
    "what helps most: walk, swim or cycle, strengthen the muscles around the joint, and lose a bit "
    "of weight if you can, which takes the load off knees and hips. Paracetamol or an ibuprofen "
    "gel eases a flare. A joint that is hot, red and swollen, or sore with a fever, needs seeing "
    "the same day; see a GP if it aches most days or your hands are stiff for more than half an "
    "hour in the morning.",
    guard=_the_part_is_a_persons,
    # the region table's neighbours are this entry's too (a sore knee is not an aching joint, a
    # chest or a jaw is another answer), and a knuckle that is dry or has just clicked is the
    # skin answer's and the cracking answer's
    # a fever with aching joints is a different answer, and so is a joint that is hot and red
    # on its own (the reply says so, but a line that leads with the fever or a flu wants that)
    # the duration words are not this entry's: the region table avoids them because a two-day
    # strain is not a month of it, but aching joints are the complaint that lasts for months
    avoid=tuple(w for w in AVOID if w not in STANDING) + (
                   "dry", "dryness", "cracked", "cracking", "flaky", "chapped", "skin",
                   "fever", "feverish", "temperature", "shivery", "shivering", "chills",
                   "flu", "influenza", "virus"),
    bias=2,
))

# Frozen shoulder is its own thing and, in a shoulder that will not lift, it is not the strain
# the region table describes: rest and a pendulum swing are not what it needs. The cooking lines
# that name a cut of meat are kept out by their own words, and so is a shoulder hurt in a fall.
ENTRIES.append(entry(
    "frozen-shoulder",
    (("shoulder", "shoulders"),
     ("frozen", "frozen shoulder", "locked", "cant lift", "can't lift", "cannot lift",
      "cant raise", "can't raise", "wont move", "won't move", "cant move it", "can't move it")),
    "A shoulder that stiffens up over weeks until you cannot lift the arm, especially turning it "
    "outwards, is usually a frozen shoulder: the capsule around the joint tightens, often for no "
    "clear reason. It eases in stages, and most people take 1 to 2 years to get most of the "
    "movement back. Keep using the arm as far as it goes, warm it before gentle stretches, and "
    "take paracetamol or ibuprofen if you can; a GP can refer you for physiotherapy and give a "
    "steroid injection early, which helps most in the painful first stage.",
    # a shoulder that will not lift after a knock is an injury, and a joint replacement is its
    # own conversation; the meat and the oven are the cooking entries'
    avoid=("lamb", "pork", "beef", "chicken", "meat", "roast", "cook", "cooking", "recipe",
           "oven", "freezer", "defrost", "joint of",
           "fell", "fall", "after a fall", "injury", "injured", "dislocated", "broken",
           "replacement", "operation", "surgery", "after the operation"),
))

# Arthritis is a named condition, not an aching part, and nothing answered it: "what foods help
# arthritis", "can arthritis be cured" and "is it arthritis" were all shrugs, while "does cold
# weather make arthritis worse" was answered with the colds-and-flu entry because of the word
# cold. The person who says the word wants to know what helps, so the key is the word itself plus
# a word of asking, and the reply carries the whole of what is known to help. The pets have their
# own answer (a cat that stops jumping is in pain), so a line about a cat or a dog stays theirs.
_ARTHRITIS_TAIL = (
    "it aches after years of use, is stiff first thing and eases as you move, and the treatment "
    "is using the joint rather than sparing it. Walking, swimming or cycling and a little "
    "strength work a few times a week keep the muscles that support the joint strong, and "
    "paracetamol with an ibuprofen gel handles a flare better than most tablets sold for "
    "arthritis. Glucosamine and cod liver oil have not held up in trials, no diet cures it, and "
    "cold, damp weather can make it ache more without damaging the joint; losing weight if you "
    "are carrying extra takes real load off knees and hips. Stiffness that lasts more than an "
    "hour in the morning, or a joint that is hot, red and swollen, is the inflammatory kind and "
    "wants a GP soon - ask about physiotherapy, and about a steroid injection for one joint that "
    "keeps flaring.")

# A line that asks about a cure gets the verdict first, because "can arthritis be cured" was
# answered with a paragraph on how to live with it and the no never came. Every other arthritis
# line keeps the description, since "is it arthritis" wants the kind it is, not the prognosis.
_ARTHRITIS_CURE = ("cure", "cured", "cures", "curable", "reverse", "reversed", "reversible",
                   "rid", "go away", "gone away", "permanent", "permanently")


def _arthritis_reply(memory, reading):
    words = set(reading.get("words") or ())
    if words & set(_ARTHRITIS_CURE):
        return ("Arthritis cannot be cured, but the ordinary wear-and-tear kind is managed "
                "well: " + _ARTHRITIS_TAIL)
    return "Ordinary arthritis - osteoarthritis - is the wear-and-tear kind: " + _ARTHRITIS_TAIL


ENTRIES.append(entry(
    "arthritis",
    (("arthritis", "osteoarthritis", "arthritic", "arthritus", "arthrosis", "arthrits"),
     ASK_ABOUT + ("pain", "pains", "painful", "hurts", "hurt", "ache", "aching", "aches",
                  "stiff", "stiffness", "hands", "hand", "fingers", "knees", "knee", "hips",
                  "hip", "thumb", "joint", "joints", "weather", "cold", "damp", "diet",
                  "food", "foods", "exercise", "exercising", "walking", "swimming",
                  "tablets", "glucosamine", "injection", "manage", "know", "cause")),
    _arthritis_reply,
    # the cat and the dog have their own answer, and a joint that is hot and swollen on its own
    # is the emergency reading's; a joint replacement is another conversation
    avoid=("cat", "cats", "kitten", "dog", "dogs", "puppy", "pet", "pets", "horse",
           "rabbit", "vet", "replacement", "replaced", "hip replacement", "knee replacement",
           "operation", "surgery"),
    bias=2,
))

# Fingers stiff first thing is the way arthritis of the hand usually starts, and the wrist entry
# was answering it with overused tendons and typing. The reply says how to tell the ordinary kind
# from the inflammatory one, which is the question behind the line.
ENTRIES.append(entry(
    "stiff-hands-morning",
    (("fingers", "finger", "hands", "hand", "knuckles", "knuckle", "thumbs", "thumb"),
     ("stiff", "stiffness", "stiffens", "stiffened", "stiffening", "gone stiff",
      "cant bend", "can't bend", "wont bend", "won't bend", "cant make a fist",
      "can't make a fist", "first thing", "in the morning", "feel tight")),
    "Stiff fingers in the morning are usually the small joints of the hands starting to wear - "
    "osteoarthritis - and that kind loosens within half an hour of moving them: run warm water "
    "over the hands first thing, do gentle finger and thumb circles, and keep using them, because "
    "rest is what makes a stiff hand stiffer. Paracetamol helps a sore spell and a pharmacist can "
    "suggest an ibuprofen gel. See a GP if the stiffness lasts more than an hour, the knuckles "
    "are swollen, or both hands are the same, because that pattern is the inflammatory kind and "
    "wants treating early.",
    # a hand hurt by typing or by a fall is the wrist entry's and the injury answer's
    avoid=("typing", "type", "keyboard", "mouse", "phone", "grip", "gripping", "wrist",
           "wrists", "tendon", "sprained", "sprain", "fell", "fall", "injury", "injured",
           "hot", "red", "swollen"),
    bias=2,
))

# Rheumatoid arthritis is not the wear-and-tear kind and the arthritis entry's advice (glucosamine,
# wear and tear) would be the wrong answer to it. It is the one that wants drugs early, so it gets
# its own entry rather than a shrug.
ENTRIES.append(entry(
    "rheumatoid-arthritis",
    (("rheumatoid", "rheumatism", "rheumatoid arthritis"),
     ("arthritis", "joints", "joint", "hands", "hand", "fingers", "flares", "flare", "pain",
      "hurts", "hurt", "medication", "methotrexate", "drugs", "treatment", "exercise",
      "tired", "stiff")),
    "Rheumatoid arthritis is the immune system attacking the lining of the joints, and it is "
    "treated early and hard because most of the damage happens in the first year or two: a "
    "rheumatology team starts disease-modifying drugs such as methotrexate, with a short course "
    "of steroids to settle a flare, and those are what keep the joints working. Keep moving "
    "between flares, take the tablets even when you feel well, and tell the team the same day "
    "if a joint is hot and swollen or you feel generally unwell, since that can be an "
    "infection rather than a flare and the two want opposite treatment.",
    bias=1,
))

ANSWERS = ("health",)

# "is my ankle broken" is a different question from "my ankle hurts", and nothing answered it: the
# safety cases need an injury in the past tense ("i broke my wrist") and the sore-part table keys
# the words for hurting, not the question of whether it is a bone. The test is the same for every
# part, so the parts and the words for a possible break are the key and the reply is one answer.
# Only the parts you can stand on, grip with or take a step on: the four-step test is the whole
# answer here, and "take four steps on a nose" or on a rib is not a sentence that helps. A broken
# nose and a broken rib keep whatever answer they had.
BROKEN_PARTS = ("ankle", "ankles", "wrist", "wrists", "arm", "arms", "foot", "feet", "toe",
                "toes", "finger", "fingers", "thumb", "hand", "hands", "leg", "legs", "knee",
                "knees", "elbow", "shoulder", "hip", "shin", "heel", "collarbone",
                "collarbones")
BROKEN_WORDS = ("broken", "broke", "fractured", "fracture", "cracked", "crack", "is it broken",
                "or broken", "or sprained", "or just sprained", "do i need an x-ray",
                "do i need an xray", "need an x-ray", "need an xray", "how do i know",
                "how can i tell", "how to tell", "is it a break", "a break or a sprain",
                "broken or sprained",
                # a part hurt in a fall is the same question, and it had no answer at all:
                # "my wrist hurts after a fall" got "I'm sorry, that's frustrating"
                "after a fall", "fell on it", "went over on it", "landed on it", "since i fell",
                "twisted it")

# The test in the reply has to fit the part: "stand on it and take four steps" is the right test
# for an ankle and advice nobody can follow for a wrist. One answer per kind of part, so the same
# question about a hand, a foot or a shoulder still gets one concrete test rather than "see a
# doctor".
ON_YOUR_FEET = ("ankle", "ankles", "foot", "feet", "toe", "toes", "leg", "legs", "knee", "knees",
                "shin", "heel", "hip", "hips")
IN_YOUR_HANDS = ("wrist", "wrists", "hand", "hands", "finger", "fingers", "thumb", "elbow",
                 "elbows")
AT_YOUR_SHOULDER = ("shoulder", "shoulders", "arm", "arms", "collarbone")

FOUR_STEPS_REPLY = (
    "How much it hurts does not tell you - a bad sprain can hurt more than a small break. Stand "
    "on it and take four steps: if you cannot, or it is crooked, numb or swelling fast, go to a "
    "minor injuries unit or A&E today for an X-ray. If you can walk on it, treat it as a sprain - "
    "ice for 20 minutes, a support wrap, keep it up - and have it checked if it is no better in "
    "two days.")

IN_YOUR_HANDS_REPLY = (
    "How much it hurts does not tell you - a bad sprain can hurt more than a small break. Try to "
    "use it: make a fist, turn a door handle, lift something light. If you cannot, or the bone "
    "looks crooked, the fingers are numb or it is swelling fast, go to a minor injuries unit or "
    "A&E today for an X-ray. If you can use it with care, treat it as a sprain - ice for 20 "
    "minutes, a support wrap, keep it raised - and have it checked if it is no better in two days.")

AT_YOUR_SHOULDER_REPLY = (
    "How much it hurts does not tell you - a bad sprain can hurt more than a small break. Try to "
    "raise the arm sideways to shoulder height and reach across your chest: if you cannot move "
    "it, or the "
    "joint looks out of shape, the arm or hand is numb or it is swelling fast, go to a minor "
    "injuries unit or A&E today for an X-ray. If you can move it with care, treat it as a sprain "
    "- ice for 20 minutes, a support wrap, keep it up - and have it checked if it is no better in "
    "two days.")


def _broken_or_sprained(memory, understood):
    """The same check, said in the test the part can actually take."""
    if _a_thing_owns_the_part(understood or {}):
        return None
    words = _words(understood)
    if words & set(IN_YOUR_HANDS):
        return IN_YOUR_HANDS_REPLY
    if words & set(AT_YOUR_SHOULDER):
        return AT_YOUR_SHOULDER_REPLY
    if words & set(ON_YOUR_FEET):
        return FOUR_STEPS_REPLY
    return FOUR_STEPS_REPLY


ENTRIES.append(entry(
    "broken-or-sprained",
    (BROKEN_PARTS, BROKEN_WORDS),
    _broken_or_sprained,
    # someone else's bone, an old break that has healed, and the recovery questions a cast or
    # crutches bring are other conversations; the emergency shapes belong to the safety cases
    avoid=("my son", "my daughter", "my child", "my kid", "my baby", "my toddler", "my husband",
           "my wife", "my partner", "my mum", "my mom", "my mother", "my dad", "my father",
           "my friend", "my dog", "my cat", "his", "her", "when i was", "years ago", "last year",
           "healed", "healing", "cast", "crutches", "boot", "physio", "physiotherapy",
           "recovery", "recover", "how long does it take", "sticking out", "through the skin",
           # and the healing question said the other way: "when can i play football again after
           # a broken leg" is not "is it broken", which is what this row answers
           "when can i", "how soon", "again after", "play again", "back to work", "back to sport",
           "back to football", "back to the gym", "back to running",
           # a break that has happened is the safety case's, with its "keep it still, ice it,
           # ring 999 if it is bent" answer: this entry is only the question of whether it is one
           "i broke", "ive broken", "i've broken", "i fractured", "i cracked", "think i broke",
           "thinks he broke", "thinks she broke", "think ive broken", "think i've broken",
           "bone is showing", "999", "ambulance", "unconscious", "head injury",
           # an egg cracking is a cooking method, not a break: "one handed" put "hand"
           # in the line and "crack" did the rest
           "egg", "eggs",
           # a head, a neck or a fall bad enough to knock someone out is the safety module's
           "hit my head", "hit his head", "head injury", "knocked out", "unconscious",
           "blacked out", "cannot get up", "cant get up", "could not get up", "neck",
           # a thing worn on the face or the wrist has an arm too, and the pair that broke is the
           # optician's or the jeweller's question: "my glasses arm broke off" is how most people
           # write a broken pair, and it was reaching this triage on "glasses" + "arm" + "broke"
           "glasses", "spectacles", "specs", "sunglasses", "frame", "frames", "lenses",
           "watch", "watch strap", "watchstrap", "bracelet")))

ENTRIES += [
    # Sweating is a body question with a plain answer, and it had none: "how do i stop sweating so
    # much" went to the search hedge.
    entry("sweating", (("sweat", "sweats", "sweaty", "sweating", "perspire", "perspiring",
                        "perspiration", "clammy", "b.o.", "body odour", "body odor"),
                       ("stop", "less", "too much", "so much", "a lot", "excessive", "reduce",
                        "under my arms", "armpits", "always")),
          "Use an antiperspirant rather than a deodorant, put it on last thing at night on dry "
          "skin where it works, and choose one with aluminium in it. Loose cotton and a spare "
          "shirt help, spicy food and alcohol make it worse, and if you sweat buckets from one "
          "place or at night, that is worth a GP visit.",
          # a hot flush, a fever and a panic are other answers, and so is how much you sweat
          # when you exercise
          avoid=("fever", "hot flush", "hot flushes", "menopause", "night sweat", "night sweats",
                 "panic", "anxious", "anxiety", "withdrawal", "opiate", "gym", "workout",
                 "running", "hyperhidrosis", "my son", "my daughter", "my baby", "my child",
                 "my husband", "my wife", "my partner", "my mum", "my dad")),
    # Teeth whitening is about stains and bleach, not about brushing, and it had no answer.
    entry("whiten-teeth", (("whiten", "whiter", "whitening", "bleach", "stains", "stained",
                            "yellow", "yellowing", "brighter"),
                           ("teeth", "tooth", "smile", "my teeth")),
          "A dentist or a hygienist scale and polish first, because most yellowing is staining on "
          "the outside, and then whitening works: either a professional kit made for your teeth or "
          "a legal-strength high-street one, and expect it to take a couple of weeks. Charcoal and "
          "bicarbonate toothpastes scrub the enamel and do not whiten it.",
          # not the bare word "teething": it is a form of "teeth", so the avoid list would
          # have turned this entry down for its own line
          avoid=("brush", "brushing", "toothbrush", "toothpaste", "my toddler", "my child",
                 "my kid", "my son", "my daughter", "baby", "teething baby", "teething ring",
                 "cutting teeth", "dentist appointment", "register", "toothache", "hurts",
                 "sensitive", "filling", "brace", "braces", "whitening strips are safe")),
    # Growing nails is diet, time and not picking, and nothing answered it.
    entry("nails-grow", (("nails", "nail", "fingernails", "fingernail", "toenails", "toenail"),
                         ("grow", "growing", "longer", "long", "stronger", "strong", "break",
                          "breaking", "brittle", "peel", "peeling", "split", "splitting",
                          "flaky", "weak",
                          # "how do i strengthen my nails" is the same question asked with a
                          # verb, and it was a shrug
                          "strengthen", "strengthening", "healthy", "healthier", "harder",
                          "faster", "thicker")),
          "Nails grow about 3mm a month, so a full nail takes six months and nothing speeds it up "
          "much: keep them filed rather than bitten, use a hand cream or cuticle oil daily, wear "
          "gloves for washing up, and take in enough protein and iron. Ridges and white spots are "
          "normal; a nail that changes colour or lifts is worth showing a pharmacist.",
          # a nail that has been knocked is the black-nail answer, and it uses the same words
          avoid=("biting", "bite", "cuticle", "gel", "acrylic", "acrylics", "polish", "paint",
                 "manicure", "pedicure", "hammer", "hangnail", "fungal", "infection",
                 "black", "bruised", "bruise", "purple", "dark", "slammed", "slam", "dropped",
                 "knocked", "knock", "stubbed", "smashed", "football", "door", "trapped",
                 "my dog", "my cat", "my baby", "my toddler", "my child"),
          # "how do i stop wood splitting when i nail it" holds "nail" and "splitting", and the
          # answer to it is a pilot hole, not growth. The guard is the same one the health and
          # routines rows use: a workshop noun in the line means the nail is a piece of metal.
          guard=_the_nail_is_a_persons),
]

# The region table answers "my back hurts" for everyone; the lines it gets wrong are the person
# asking whether this needs a physio, which was reaching the "find a city" fallback.
ENTRIES += [
    entry("physio-or-stretch",
          (("physio", "physiotherapy", "physiotherapist", "chiropractor", "osteopath"),
           ("see", "should i", "or just", "worth", "need", "go", "stretch", "gp", "refer")),
          "See a physio if the pain has lasted more than a fortnight, keeps coming back, or comes "
          "with numbness, weakness or pins and needles - and you can refer yourself on the NHS "
          "without seeing a GP first. If it is a recent strain that is already easing, gentle daily "
          "stretching plus some strength work (sit-to-stands, bridges, a short walk) is what a "
          "physio would give you anyway.",
          avoid=("knee", "shoulder", "ankle", "calf", "hamstring", "achilles", "cost", "how much",
                 "price", "private")),
]

# A complaint about care is its own move: the person is not asking who to see, they are asking
# how to get a practice or a hospital to answer for something that went wrong. Registering,
# booking and a medical question all share the same nouns, so the complaint words are the
# subject here, and the appointment and registration answers keep their own lines.
ENTRIES.append(entry(
    "health-complaint",
    (("dentist", "dentists", "dental", "gp", "doctor", "doctors", "doctor's", "hospital",
      "hospitals", "nhs", "surgery", "clinic", "nurse", "midwife", "consultant", "surgeon",
      # "the care i received" names no provider either; "my care" alone is left out because
      # the chat module reads "make a complaint about my care" as a feeling and outranks us
      "care i got", "care i received", "care i had", "the care i"),
     ("complain", "complaining", "complaint", "complaints", "made a complaint",
      "make a complaint", "raise a complaint", "raised a complaint", "mistake", "mistakes",
      "misdiagnosed", "misdiagnosis", "negligence", "negligent", "botched", "wrong tooth",
      "wrong tooth out", "wrong medication", "wrong medicine", "hurt me", "caused harm",
      "bad treatment", "poor treatment", "did a bad job")),
    "Ask the practice or hospital for its complaints procedure and put it in writing: what "
    "happened, when, who you saw and what you want. Ask for a written reply and keep copies. "
    "Still unhappy? Ask for a deadlock letter and take it free to the NHS ombudsman - PALS at "
    "a hospital will help you word it, and private dental work has the free Dental Complaints "
    "Service. If someone was harmed, get the records and advice from AvMA before signing "
    "anything.",
    # a bill, a parking charge and a waiting-time grumble are other questions, and the dentist
    # registration and appointment answers use the same nouns
    avoid=("bill", "billing", "invoice", "parking", "car park", "charge", "charges", "cost",
           "price", "how much", "register", "registering", "sign up", "appointment",
           "appointments", "book", "booking", "waiting list", "waiting time", "food", "meal",
           "cleanliness", "cleaning"),
    # a bare "complain" also sits in lifeadmin's escalate-complaint and shopping's shop
    # complaint, and their generic "how" made them win a named health provider. This entry
    # has the provider in its key, so it should win when the line names one.
    bias=2))

# The commonest skin-cancer line in English was in no entry at all: "my mole has changed shape",
# "my mole is bleeding", "should i get my mole checked" all fell through to the greeting pool, so
# the one body thing where "get it looked at" is the whole answer got a shrug. The animal and the
# lawn are the same word, which is why the entry has to say which mole it means.
MOLE_CHANGE = ("change", "changed", "changes", "changing", "different", "bigger", "growing",
               "grown", "grew", "larger", "size", "shape", "edge", "edges", "border", "colour",
               "color", "colours", "colors", "darker", "dark", "black", "bleeding", "bled",
               "bleeds", "blood", "crusty", "crusting", "scab", "scabby", "itchy", "itching",
               "itches", "sore", "tender", "raised", "lumpy", "new", "suddenly", "worried",
               "worry", "worrying", "checked", "check", "checking", "dangerous", "cancer",
               "melanoma", "malignant", "normal", "looks", "look", "found", "keep an eye",
               "keep my eye", "monitor", "watch", "hair", "hairy",
               # a mole the bra strap or a collar keeps catching is being rubbed raw, and
               # "a mole appeared on my shoulder" is a mole that was not there before: both are
               # a reason to have it looked at, and without the words below the line fell to
               # the mould row ("wipe it off with a mould spray") or to an echo.
               "catching on", "catches on", "catch on", "caught on", "rubs", "rubbing",
               "rubbed", "friction", "irritated", "appeared", "appears", "appearing")

# A mole that is *new*, growing a hair or being looked at is not a mole that has changed, and the
# card that opens "get it checked by a GP within two weeks" is the right answer to one of those
# and too strong for the other. The words below are the ones that say something is happening to
# the mole itself; a line with none of them gets the same facts at the tone of an ordinary mole.
MOLE_HAPPENING = ("change", "changed", "changes", "changing", "different", "bigger", "growing",
                  "grown", "grew", "larger", "size", "shape", "edge", "edges", "border",
                  "colour", "color", "colours", "colors", "darker", "dark", "black",
                  "bleeding", "bled", "bleeds", "blood", "crusty", "crusting", "scab",
                  "scabby", "itchy", "itching", "itches", "sore", "tender", "raised",
                  "lumpy", "dangerous", "cancer", "melanoma", "malignant",
                  # "should i worry about my mole" is a worry already: the two weeks is the answer
                  "worried", "worry", "worrying", "anxious", "bad", "serious", "abnormal",
                  "cancerous",
                  # the same two reasons as the key: being rubbed by clothing, and having
                  # appeared where there was nothing before
                  "catching", "catches", "caught", "rubs", "rubbing", "rubbed", "friction",
                  "irritated", "appeared", "appears", "appearing")
# The signs that stand on their own even in a line that also mentions a hair.
_MOLE_CLEAR = frozenset("""
bleeding bled bleeds blood crusty crusting scab scabby itchy itching itches changed changing
change changes different bigger larger darker black sore tender lumpy
catching catches caught rubbing rubbing rubbed friction appeared appears appearing
""".split())
_MOLE_CHANGED_TEXT = (
    "Get it checked by a GP within two weeks. A mole that changes shape, edge, colour or size, "
    "or bleeds, itches or crusts on its own, wants a look rather than a wait, though almost all "
    "of them turn out to be nothing. The signs worth saying out "
    "loud are the ABCDE ones: not symmetrical, a ragged or blurry border, more than one colour, "
    "wider than about 6mm, or changing in any way. Photograph it beside a coin for scale and "
    "ring the surgery rather than waiting to see whether it settles.")
# The same ABCDE facts for a mole nothing has happened to, which is what "is my mole normal",
# "i have a new mole" and "my mole has a hair growing out of it" are asking. The check is still
# in the first sentence and the two-week line is still in the card, so a follow-up "should i be
# worried" is answered from a card that says both things in proportion.
_MOLE_ORDINARY_TEXT = (
    "Almost all moles are harmless, so what matters is knowing what a change looks like rather "
    "than checking it every day: the ABCDE test is not symmetrical, a ragged or blurry border, "
    "more than one colour, wider than about 6mm, or anything that is changing. Photograph it "
    "beside a coin for scale and compare it every few months; a mole that changes, bleeds, itches "
    "or crusts on its own wants a GP within two weeks, and a hair growing out of one usually "
    "means it is an ordinary mole that has been there a long time.")
_CHECK_HOW_TO = re.compile(r"\bhow\s+(?:do|can|should|would)\s+(?:i|you|we)\s+(?:check|inspect)|"
                           r"how\s+to\s+check|what\s+(?:do\s+i\s+)?look\s+for", re.I)
# A line that leans on the mole just talked about names nothing of its own: "is that bad",
# "should i be worried", "what should i do". A line that names someone else or a *new* mole is a
# new question and gets the card that fits it, however short it is.
_NEW_SUBJECT = ("new", "another", "child", "children", "kid", "kids", "son", "daughter",
                "baby", "wife", "husband", "partner", "friend", "mother", "father", "mum",
                "dad", "sister", "brother", "gran", "nan", "other")


def _a_bare_followup(said):
    """True for a short line about the thing just discussed rather than a new mole.

    It has to name nothing of its own: no mole noun ("are moles normal" is its own question) and
    no other person or new mole ("my child has a new mole").
    """
    words = re.findall(r"[a-z']+", str(said).lower())
    if not words or len(words) > 6:
        return False
    if any(word in words for word in ("mole", "moles", "birthmark", "birthmarks", "spot", "spots")):
        return False
    return not any(word in words for word in _NEW_SUBJECT)


# "How do I get rid of a mole" is a removal question, and the answer is not the change signs: the
# thing that bothers someone is taken off by a GP, and the home remedies for it are worse than the
# mole. The words below are the removal reading, and a line that also says the mole changed keeps
# the two-week card, because that is the appointment that matters first.
MOLE_REMOVE = ("get rid", "rid of", "remove", "removing", "removal", "removed", "laser",
               "freeze", "freezing", "cut off", "cut it off", "tie it off", "shave off",
               "cut a mole", "cut my mole", "cut this mole", "get it cut")
_MOLE_REMOVE_TEXT = (
    "Most moles need no treatment at all, and one that bothers you - catching on clothes, or a GP "
    "wanting a closer look - is taken off on the NHS: a short excision under local anaesthetic, "
    "with the mole sent for a check. Don't cut, tie off or use a wart or skin-tag kit on it, and "
    "don't book a beauty clinic for something a GP should see first.")


def _mole_reply(memory, understood):
    """The two-week card for a mole that is doing something, the same facts for the other one."""
    words = _words(understood)
    said_words = str(understood.get("text") or understood.get("clean") or "") if isinstance(
        understood, dict) else ""
    if (any(phrase in said_words.lower() for phrase in MOLE_REMOVE)
            and not words & set(MOLE_HAPPENING)):
        # a removal question, with nothing said about the mole having changed
        return _MOLE_REMOVE_TEXT
    said = str(understood.get("text") or understood.get("clean") or "") if isinstance(
        understood, dict) else ""
    if words & {"hair", "hairy"} and not words & _MOLE_CLEAR:
        # a hair growing out of a mole is the reassuring sign, not the changing one
        return _MOLE_ORDINARY_TEXT
    # "how do i check my moles" is the method, not a mole that needs an appointment; "should i
    # get my mole checked" is the appointment, and the words below send it to the card.
    if _CHECK_HOW_TO.search(said):
        return _MOLE_ORDINARY_TEXT
    if words & set(MOLE_HAPPENING) or words & {"check", "checked", "checking"}:
        return _MOLE_CHANGED_TEXT
    # "is that bad" after the two-week card must not be answered with the ordinary one, which
    # reads as "never mind"; it is about the mole the last turn named, so it keeps that card.
    if _a_bare_followup(said) and any(
            "get it checked by a gp" in str(turn.get("bot") or "").lower()
            for turn in (memory or {}).get("turns") or [] if isinstance(turn, dict)):
        return _MOLE_CHANGED_TEXT
    return _MOLE_ORDINARY_TEXT


ENTRIES.append(entry(
    "changing-mole",
    (("mole", "moles", "birthmark", "birthmarks", "beauty spot", "beauty spots", "skin spot"),
     MOLE_CHANGE + MOLE_REMOVE),
    _mole_reply,
    # the animal under the lawn, the garden it lives in, and the sauce that shares the name
    avoid=("garden", "gardens", "lawn", "lawns", "grass", "golf", "green", "molehill",
           "molehills", "mole hill", "hill", "hills", "tunnel", "tunnels", "trap", "traps",
           "trapping", "pest", "pests", "animal",
           "animals", "wildlife", "drain", "drains", "field", "fields", "farm", "farmer",
           "vole", "voles", "rodent", "rodents", "sauce", "recipe", "recipes", "cook",
           "cooking", "dish", "dish", "chilli", "chocolate", "poblano", "chicken",
           # acne, the other thing people call a spot, keeps its own answers
           "acne", "pimple", "pimples", "blackhead", "blackheads", "spot cream",
           "spot treatment", "face wash", "cleanse", "cleanser", "routine", "product",
           "products", "best", "sunscreen", "sun cream", "sunbed", "sun tan", "fake tan",
           "tanned", "tanning", "sunless"),
    bias=1))

# A painkiller question about the stomach, the liver or how fast it works is not a dose question
# and not a which-of-the-two question: those three rows are keyed on a drug name and a number,
# and every line below was the pharmacist deflection on its own. "can i drink alcohol with
# paracetamol" was worse than a shrug - it reached the which-of-the-two card and read "Yes -
# paracetamol and ibuprofen work in different ways, so you can take them together", which is an
# answer to a question nobody asked.
PAINKILLER_NAMES = ("paracetamol", "acetaminophen", "panadol", "calpol", "ibuprofen", "nurofen",
                    "brufen", "co codamol", "co-codamol", "painkiller", "painkillers",
                    "anti inflammatory", "nsaid", "nsaids")
# Heartburn, indigestion and an antacid already have their own answer, and a line about one of
# those is not a question about the tablet.
_NOT_THE_TABLET = ("heartburn", "indigestion", "reflux", "antacid", "gaviscon", "rennie",
                   "omeprazole", "lansoprazole", "acid reflux")

# The stomach and the kidneys are the two organs an anti-inflammatory upsets, and the answer
# opens on the one the line asked about: "is ibuprofen bad for your kidneys" wants the kidneys
# first, and a line about eating before a tablet wants the stomach. Same shape as the dose row,
# which leads with the drug the person is holding.
_KIDNEY_WORDS = ("kidney", "kidneys", "renal", "water tablet", "water tablets", "diuretic",
                 "blood pressure tablet", "blood pressure tablets", "blood pressure medication",
                 "blood pressure pills", "only one kidney")


# Paracetamol is not an anti-inflammatory, and the kidney warning is about the ones that are:
# "can i take paracetamol with my blood pressure tablets" was answered with the warning against
# ibuprofen, which reads as a warning about the tablet the person actually holds.
_NOT_AN_NSAID = ("paracetamol", "acetaminophen", "panadol", "calpol", "co codamol", "co-codamol")


def _the_organ_the_painkiller_upsets(memory, reading):
    line = " ".join(str((reading or {}).get("text") or "").split()).lower()
    holds_paracetamol = any(word in line for word in _NOT_AN_NSAID)
    holds_nsaid = any(word in line for word in ("ibuprofen", "nurofen", "brufen", "naproxen",
                                                "aspirin", "diclofenac", "nsaid", "anti "
                                                "inflammatory", "anti-inflammatory",
                                                "voltarol", "indomethacin"))
    if holds_paracetamol and not holds_nsaid:
        return ("Paracetamol is the painkiller to use here: it is not an anti-inflammatory, so it "
                "does not cut the blood flow the kidneys rely on or irritate the stomach the way "
                "ibuprofen does, and a blood pressure tablet or a water tablet is no reason to "
                "avoid it. Stay within the 4g a day limit (less if a GP has said so, and less if "
                "you have liver trouble or drink heavily), and space the doses out. If it is not "
                "touching the pain, that is worth a word with a pharmacist rather than more "
                "tablets.")
    if any(word in line for word in _KIDNEY_WORDS):
        return ("An anti-inflammatory cuts the blood flow the kidneys rely on, so it is the wrong "
                "choice if yours are already poor, if you are dehydrated, or if you take a water "
                "tablet or a blood pressure tablet - that mix is the one pharmacists watch for. "
                "Paracetamol is the painkiller to use instead, and it is worth asking a "
                "pharmacist or GP before starting ibuprofen at all if you have kidney disease or "
                "only one kidney.")
    return ("Ibuprofen and the other anti-inflammatories (naproxen, aspirin, diclofenac) can "
            "irritate the stomach lining, so take them with or after food rather than on an empty "
            "stomach, at the lowest dose that works and for the shortest time. Don't take them at "
            "all if you have had a stomach ulcer or a bleed, or if you are on a blood thinner - "
            "paracetamol is the one to use instead. Get seen the same day for a pain in the top of "
            "the stomach that is severe, for black tarry poo, or for vomiting blood or anything "
            "that looks like coffee grounds.")


ENTRIES.append(entry("painkiller-stomach",
          (PAINKILLER_NAMES,
           ("stomach", "tummy", "gut", "upset", "upsets", "upsetting", "empty stomach",
            "with food", "before food", "after food", "eat before", "eat something",
            "on food", "bad for my stomach", "bad for your stomach", "sore stomach",
            "irritate", "irritates", "irritating", "lining", "ulcer", "ulcers",
            "bleeding in my stomach", "stomach bleed", "does it upset",
            "kidney", "kidneys", "renal", "bad for my kidneys",
            "water tablet", "water tablets", "diuretic", "blood pressure tablet",
            "blood pressure tablets", "blood pressure medication", "blood pressure pills")),
          _the_organ_the_painkiller_upsets,
          avoid=_NOT_THE_TABLET + ("pregnant", "pregnancy", "breastfeeding", "breastfeed",
                                   "child", "kid", "baby", "toddler", "dog", "cat",
                                   "overdose", "took too many", "whole packet", "allergic",
                                   "reaction", "rash", "asthma")))

ENTRIES.append(entry("painkiller-and-alcohol",
          (PAINKILLER_NAMES,
           ("alcohol", "drink", "drinking", "drunk", "beer", "wine", "vodka", "gin", "pint",
            # `hangover` is not here: there is a hangover card that is the right answer to "does
            # ibuprofen help a hangover", and this row took it. What is left after the word comes
            # out is a person asking whether the two go together, which is this row.
            "pints", "booze", "a few drinks", "nights out", "night out")),
          "Paracetamol and drink is a liver question and ibuprofen and drink is a stomach one, "
          "and a normal dose of either with an occasional drink is fine. Paracetamol's warning "
          "is about drinking heavily or daily for years, because the liver handles both, and the "
          "ceiling stands whatever you have drunk: no more than 4g (eight 500mg tablets) in 24 "
          "hours, with no other paracetamol product on top. Ibuprofen mainly raises the risk of "
          "stomach irritation and bleeding, so eat something with it and keep to the lowest dose "
          "that works. If you drink heavily every day, ask a pharmacist before taking paracetamol "
          "at all.",
          avoid=_NOT_THE_TABLET + ("pregnant", "pregnancy", "breastfeeding", "child", "kid",
                                   "baby", "toddler", "dog", "cat", "overdose", "took too many",
                                   "whole packet", "alcoholic", "addiction", "stop drinking",
                                   "give up alcohol", "cut down")))

ENTRIES.append(entry("painkiller-how-fast",
          (PAINKILLER_NAMES,
           ("how long", "how quickly", "how fast", "how soon", "when does it work",
            "take to work", "kick in", "kicks in", "start working", "starts working",
            "how long to work", "how long until")),
          "Tablets taken by mouth start working in about 30 minutes and are at their best at one "
          "to two hours; a soluble or effervescent one is quicker, and ibuprofen lysine and the "
          "liquid capsules are faster than a plain tablet. Pain that has not shifted at all after "
          "two hours, at a proper dose, is a reason to ask a pharmacist rather than to take more "
          "sooner than the packet allows.",
          avoid=_NOT_THE_TABLET + ("child", "kid", "baby", "toddler", "pregnant", "pregnancy",
                                   "breastfeeding", "dog", "cat", "how long can i take",
                                   "how long should i take", "how many days", "how long does "
                                   "ibuprofen last", "how long does it last")))

ENTRIES.append(entry("painkiller-and-the-blood",
          (PAINKILLER_NAMES,
           ("thin your blood", "thins the blood", "thin the blood", "thinning", "blood thinner",
            "blood thinners", "warfarin", "clot", "clotting", "bleed more", "bleeding",
            "bruise", "bruises", "bruising", "before an operation", "before surgery",
            "before my operation", "dental work", "tooth out")),
          "Ibuprofen and the other anti-inflammatories make the blood a little slower to clot, "
          "which is why they are stopped before an operation or a tooth out - usually a few days "
          "before, on the surgeon's or dentist's word - and why they are not mixed with warfarin "
          "or a blood thinner without advice. Paracetamol has no effect on clotting at all, so "
          "if you bruise easily or bleed for longer than you used to, that is a question for a "
          "pharmacist or GP rather than a reason to keep taking it.",
          ask=("can i", "should i", "is it", "does it", "do i", "is", "does", "before", "with",
               "ok", "safe", "okay"),
          avoid=_NOT_THE_TABLET + ("pregnant", "pregnancy", "breastfeeding", "child", "kid",
                                   "baby", "toddler", "dog", "cat", "overdose", "took too many",
                                   "cut myself", "cut my", "wound", "nosebleed", "heavy period")))

ENTRIES.append(entry("painkiller-and-sleep",
          (PAINKILLER_NAMES,
           ("sleepy", "drowsy", "drowsiness", "make me tired", "makes me tired", "knock me out",
            "knocks me out", "can i drive", "drive after", "drowsy driving", "sleep",
            "keep me awake", "awake")),
          "Paracetamol and ibuprofen are not sedatives and neither is meant to make you sleepy - "
          "drowsiness is an uncommon side effect of ibuprofen, so if one does leave you dozy it is "
          "worth mentioning to a pharmacist. What does make people drowsy is the codeine in "
          "co-codamol, and the sleepy feeling is one of the reasons not to drive on it until you "
          "know how it treats you. Pain itself is often what stops people sleeping, so a dose at "
          "bedtime is fine.",
          avoid=_NOT_THE_TABLET + ("child", "kid", "baby", "toddler", "pregnant", "pregnancy",
                                   "breastfeeding", "dog", "cat", "cant sleep", "can't sleep",
                                   "insomnia", "sleep aid", "sleeping tablet", "melatonin",
                                   "nightmare")))

# "how do i wax my legs" was a shrug, and the ear-wax answer already stands down on legs, so
# nothing answered it. Hair removal is one question with three answers in it - the blade, the
# wax and the bump - so the person who asks about a rash of ingrown hairs gets that part.
_WAX_FIRST_REPLY = (
    "Waxing wants hair about 5mm long, a patch test a day ahead and one firm pull against the "
    "growth with the skin held tight; take an antihistamine an hour before if you come up "
    "blotchy. Shaving is quicker: end of a warm shower, fresh blade, conditioner instead of "
    "foam, and with the hair rather than against it, which is what keeps the red bumps away. An "
    "ingrown hair wants a warm compress and an exfoliating glove every other day.")

_SHAVE_FIRST_REPLY = (
    "Shave at the end of a warm shower with a fresh blade and conditioner, rinsing the blade "
    "often, and on legs and bikini line go with the hair, not against it, which is what keeps "
    "the red bumps away. Waxing wants hair 5mm long, a patch test a day ahead and a firm pull "
    "against the growth, plus an antihistamine an hour before if you come up blotchy. An "
    "ingrown hair wants a warm compress and an exfoliating glove every other day.")

_WAX_WORDS = {"wax", "waxes", "waxing", "waxed", "wax strip", "wax strips", "strip", "strips",
              "sugaring", "hot wax", "cold wax", "bikini wax", "leg wax", "underarm wax",
              # sugaring is a wax by another name, so a line that names it opens with the wax
              # half rather than the blade; the diet lines never reach this row
              "sugar"}


def _hair_removal(memory, understood):
    """Open with the half the line asked about.

    STYLE wants the answer in the first sentence, and "how do i wax my legs" was opening with
    the shave: the waxing words were there, in the middle. A line that names wax starts with the
    wax, and a line that only names the blade or the bumps keeps the shave first.
    """
    if _words(understood) & _WAX_WORDS:
        return _WAX_FIRST_REPLY
    return _SHAVE_FIRST_REPLY


# A beard, a face and a razor blade are the one kind of shaving `hair-removal` stands down on:
# its card is about legs and a bikini line, and a man asking how to trim a beard should not be
# told about a wax strip. Nothing answered those lines - "how do i trim my beard", "how do i
# shave my face without cutting myself", "how often should i change my razor blade" were all
# punts - so face shaving is one row with the four answers it needs inside it.
_BEARD_TRIM_WORDS = {"trim", "trims", "trimming", "trimmer", "trimmers", "shape", "shaping",
                     "line", "line up", "lining", "neckline", "guard", "guards", "shorten",
                     "tidy", "tidying", "beard", "beards", "moustache", "mustache", "goatee",
                     "stubble"}
_BLADE_WORDS = {"blade", "blades", "razor blade", "razor blades", "change", "changing",
                "rust", "rusty", "rusting", "going rusty", "sharpen", "sharp",
                "replace", "replacing", "how often", "blunt", "dull", "dragging", "drags",
                "last", "lasts", "how long", "wear out", "worn out", "how many shaves",
                "pulling", "pulls", "pull", "new razor", "cartridge", "cartridges"}
# "stop", "prevent" and "avoid" are how people ask anything, and a bare one of them sent
# "how do i stop cuts when shaving" to the burn card: they only count next to the thing they
# are about.
_SHAVE_BURN_WORDS = {"burn", "burns", "burning", "razor burn", "sore", "red", "redness",
                     "irritation", "irritated", "rash", "bumps", "spot", "spots", "sting",
                     "stings", "stinging", "stop razor burn", "prevent razor burn", "stop razor rash",
                     "prevent shaving rash", "avoid razor bumps", "stop the burn",
                     "stop it burning", "prevent the burn", "avoid the burn",
                     "stop the rash", "prevent the rash", "stop the redness",
                     "stop the irritation", "prevent irritation", "avoid irritation",
                     "stop the stinging", "stop the stinging", "avoid shaving rash"}

_BEARD_TRIM_REPLY = (
    "Trim it dry, on a guard a couple of steps longer than the length you want, and go with the "
    "hair first before tidying the edges against it. Take the neckline just above the Adam's "
    "apple and the cheeks along the jaw, then finish with the guard off and the blade flat so "
    "the lines are sharp.")
_STRAIGHT_SHAVE_REPLY = (
    "Warm the hair first - a shower or a flannel held on for two minutes - then use a sharp blade "
    "and proper cream, and take short strokes with the grain without pressing. Most nicks come "
    "from a blunt blade or going over the same patch again, so rinse and stop there.")
_RAZOR_BLADE_REPLY = (
    "Rinse the blade in hot water and stand it up to dry rather than leaving it in the shower, "
    "and change it after five to seven shaves, or the moment it drags and pulls instead of "
    "gliding: a blunt blade scrapes the skin, which is what most razor burn really is.")
_RAZOR_BURN_REPLY = (
    "Rinse with cool water, pat it dry and skip anything with alcohol in it; then a fresh blade, "
    "shaving with the grain and short strokes are what stop it coming back. If it stings for "
    "days or comes up in spots, shave every other day until it settles, and take anything "
    "blistered or spreading to a pharmacist.")


def _face_shaving(memory, understood):
    """The beard, the blade, the burn or the shave, whichever the line is about."""
    words = _words(understood)
    if words & _BLADE_WORDS:
        return _RAZOR_BLADE_REPLY
    if words & _SHAVE_BURN_WORDS:
        return _RAZOR_BURN_REPLY
    if words & _BEARD_TRIM_WORDS:
        return _BEARD_TRIM_REPLY
    return _STRAIGHT_SHAVE_REPLY


ENTRIES.append(entry("face-shaving",
          (("shave", "shaves", "shaving", "shaved", "razor", "razors", "beard", "beards",
            "moustache", "mustache", "goatee", "stubble", "beard trimmer", "trimmer",
            "razor blade", "razor blades", "wet shave", "close shave"),
           ("face", "neck", "chin", "jaw", "jawline", "cheek", "cheeks", "upper lip",
            "moustache", "mustache", "beard", "beards", "blade", "blades", "razor blade",
            "burn", "burns", "razor burn", "rash", "irritation", "cut", "cuts", "nick",
            "nicks", "trim", "trimming", "shave", "shaving", "stubble", "how often",
            "change", "replace", "closest", "smooth", "pulling", "pulls", "pull", "drag",
            "last", "lasts", "how long", "long does", "wear out", "worn out",
            "blunt", "dull", "rust", "rusty", "rusting", "cartridge", "cartridges",
            "drags", "dragging", "tugging", "look after", "care", "care for", "keep", "head",
            "scalp", "how do i", "how to", "best way", "what should i")),
          _face_shaving,
          # a leg, a bikini line, an underarm and an eyebrow are hair-removal's, and its card
          # answers the rash and the bump; a head shave has its own answer; a scald and a
          # sunburn are burns and not the razor
          avoid=("leg", "legs", "bikini", "underarm", "underarms", "armpit", "armpits",
                 "eyebrow", "eyebrows", "pubic", "ingrown", "ingrowing", "ingrown hair",
                 "razor bumps", "shaving rash", "shaving bumps", "wax", "waxes", "waxing",
                 "sunburn", "sun burn",
                 "scald", "scalded", "hot water", "iron", "oven", "hair removal",
                 "legs and bikini",
                 # things shaved thin in a kitchen, and the questions around a beard that are
                 # not the shave: cleaning the trimmer, itch and dandruff, growing one faster
                 "parmesan", "cheese", "chocolate", "fennel", "truffle", "horseradish",
                 # A razor clam is a shellfish, and "how do i cook razor clams" was answered
                 # with the shampoo-and-a-sharp-blade card. Every shellfish called a razor goes
                 # in the same fence, so the kitchen question keeps the kitchen answer.
                 "clam", "clams", "razor clam", "razor clams", "razor shell", "razor shells",
                 "clean", "cleaning", "wash", "washing", "itch", "itchy", "itching",
                 "dandruff", "grow", "growing", "faster", "thicker", "patchy", "beard oil",
                 "beard balm",
                 # a trimmer is also what cuts a hedge and edges a lawn: "can i keep a hedge
                 # trimmer in a shed" was answered with the beard card and "how do i use a hedge
                 # trimmer" with the neckline, so the garden machines stand this row down
                 "hedge", "hedges", "hedge trimmer", "hedge cutters", "garden", "gardening",
                 "lawn", "lawns", "lawnmower", "mower", "mowers", "strimmer", "strimmers",
                 "leaf blower", "chainsaw", "secateurs", "shears", "shed", "garage",
                 "topiary", "shrub", "shrubs", "bush", "bushes")))

ENTRIES.append(entry("hair-removal",
          (("wax", "waxes", "waxing", "waxed", "shave", "shaves", "shaving", "shaved",
            "hair removal", "hair remover", "epilator", "epilate", "epilating", "razor",
            "razors", "depilatory", "hair removal cream", "sugaring",
            # "sugar" on its own is not a form of "sugaring" to the form match, so "how do i
            # sugar my legs" was a punt after the diet-sugar words went into the avoid below:
            # the shapes that put sugar on a part of the body are keyed here, and the diet
            # sentences ("cut down on sugar", "how much sugar") are still not among them
            "sugar my legs", "sugar legs", "sugar my bikini", "sugar my underarms",
            "sugar my armpits", "sugar wax", "sugar paste", "sugaring wax",
            "ingrown", "ingrowing", "ingrown hair", "ingrown hairs", "ingrowing hair",
            "razor bumps", "shaving rash", "shaving bumps"),
           ("leg", "legs", "bikini", "bikini line", "underarm", "underarms", "armpit",
            "armpits", "eyebrow", "eyebrows", "beard", "face", "upper lip", "chin", "pubic",
            "hair", "hairs", "stubble", "ingrown", "ingrowing", "bumps", "rash", "irritation",
            "redness", "smooth", "how do i", "best way", "how to", "sore", "hurts",
            "painful", "stings", "itchy",
            # the name of the thing is its own second word: "what is sugaring" names no body
            # part and no how-to, and it is a question about this card
            "sugaring", "sugar wax")),
          _hair_removal,
          # the other waxes, which are furniture, cars and candles, and the ear
          avoid=("ear", "ears", "earwax", "ear wax", "blocked ear", "bunged up ear",
                 "table", "tables", "floor", "floors", "furniture", "car", "cars", "skirting",
                 "candle", "candles", "surfboard", "skis", "ski", "snowboard", "boots", "wood",
                 "wooden", "paintwork", "leather", "thread", "eyebrow pencil", "tweezers",
                 "tweeze", "threading", "bleach",
                 # A tablecloth is not a form of the word table, so "how do i get wax off a
                 # tablecloth" was taken by this row on "wax" alone and answered with the salon
                 # card. The cloth words and the "wax off/out of" shapes are what a candle line
                 # looks like, whatever the surface is made of.
                 "tablecloth", "tablecloths", "cloth", "candle wax", "candle holder",
                 "wax off", "wax out of", "off the table", "off my table", "wax stain",
                 # a beard, a head and a face are shaved but not the legs and bikini line this
                 # card talks about, and a wax warmer is a pot to clean, not a person
                 "beard", "beards", "shave my head", "shaving my head", "head shave",
                 "shave my face", "shaving my face",
                 # A razor clam is not a razor: the shellfish card in the kitchen answers it,
                 # and this one answered "how do i cook razor clams" with the shower and the
                 # fresh blade.
                 "clam", "clams", "razor clam", "razor clams", "razor shell", "razor shells",
                 "oyster", "oysters", "mussel", "mussels", "shellfish",
                 # An ingrown nail is not an ingrown hair: "how do i treat an ingrown toenail" and
                 # "my toenail is ingrowing" are the nail card, and `ingrown` is in this key, so
                 # the body part has to be named here or the razor bumps answer takes them.
                 "toenail", "toenails", "toe nail", "toe nails", "ingrown toenail",
                 "ingrowing toenail", "fingernail", "fingernails", "podiatrist", "chiropodist",
                 # "blood sugar" and "sugar crash" are nourishment and the crash after a
                 # sweet thing, so neither is a pot of wax; the craving words and the bare
                 # "eat sugar" are the nutrition rows' question too.
                 "blood sugar", "sugar crash", "crave", "craves", "craving", "cravings",
                 "stop wanting", "wanting sugar", "sugar addiction", "addicted to sugar",
                 "sugar out of my diet", "eating sugar", "eat sugar", "stop eating",
                 "warmer", "melt warmer", "wax pot", "melter", "clean the wax",
                 "clean a wax",
                 # sugar in the diet is not sugaring the skin, and "cut down" is the usual
                 # wording of that question
                 "cut down on sugar", "cut out sugar", "cutting out sugar", "cut sugar",
                 "eat less sugar", "less sugar", "so much sugar", "eating so much sugar",
                 "sugar habit", "sugar at night", "give up sugar", "quit sugar",
                 "too much sugar", "sugar in my diet", "sugar in your diet", "sugar cravings",
                 "sugar craving", "stop eating sugar", "added sugar",
                 "sugar free", "sugar-free", "reduce sugar", "reducing sugar", "how much sugar",
                 "sugar intake", "sugary", "fizzy drinks", "sweet tooth", "sweets",
                 "craving sugar", "crave sugar", "stop craving", "sugar rush", "sugar hit")))

# "how long does a broken bone take to heal" is the question that comes the day after the cast
# goes on, and the triage row above stands down for it on purpose ("how long does it take" is in
# its avoid), so nothing answered it but the search hedge. The numbers are the ordinary union
# times a fracture clinic gives out, and they are the same for every way of asking.
_HEAL_PARTS = ("arm", "arms", "wrist", "wrists", "leg", "legs", "ankle", "ankles", "foot",
               "feet", "toe", "toes", "finger", "fingers", "thumb", "hand", "hands", "rib",
               "ribs", "collarbone", "clavicle", "shoulder", "elbow", "shin", "tibia", "fibula",
               "knee", "hip", "femur", "bone", "bones", "fracture", "fractured", "break",
               "broken", "cracked", "cast", "plaster")
_HEAL_TIME = ("how long", "how many weeks", "how long till", "how long until", "take to heal",
              "heal", "heals", "healing", "healed", "mend", "mends", "mending", "recover",
              "recovery", "back to normal", "back to work", "back to sport", "back to running",
              "back to football", "back to the gym", "in a cast", "off work", "how soon",
              "when can i", "play again", "playing again", "back to playing", "back on it",
              "again after")


# A break from work is not a break in a bone: "how long is my break", "how long should a
# break be" and "how long are my breaks at work" all reached the healing row on the two words
# "how long" and "break" and were told about six weeks for most bones. The row's part words
# include "break", "broken", "cracked" and "cast", so the words alone cannot tell the two
# readings apart; a rest says whose it is ("my break", "a break", "breaks at work") and no part
# noun is anywhere in the line, which is the shape a bone question does not have.
_A_REST_NOT_A_BONE = re.compile(
    # somebody's break: "my break", "our tea break", "his lunch break"
    r"\b(?:my|your|our|their|his|her)\s+"
    r"(?:lunch|tea|coffee|dinner|toilet|rest|water|cigarette|fag)?\s*breaks?\b"
    # the break names itself
    r"|\b(?:lunch|tea|coffee|dinner|toilet)\s+breaks?\b"
    # where the break is: "breaks at work", "a break between shifts"
    r"|\bbreaks?\s+(?:at|from|during|in)\s+(?:work|the shift|a shift|my shift|shift)\b"
    r"|\bbreaks?\s+between\s+shifts\b"
    r"|\bbreaks? at work\b"
    # the length question a break has and a bone does not
    r"|\bshould (?:a|my|our) breaks? be\b")
# A line that says heal, mend, knit, cast or an X-ray is a bone question however it words the
# break: "how long does a break take to heal" and "how long does a break take to knit" are both
# about a fracture, and "a break" alone is the shape the two readings share.
_A_HEALING_WORD = re.compile(
    r"\b(?:heal|heals|healing|healed|mend|mends|mending|knit|knits|knitting|cast|plaster|"
    r"x-ray|xray|fracture|fractured|broken|pinned|pin|pins|physio|physiotherapy|set|setting)\b")
# The part words that make a line a bone question on their own. "break" and "broken" are not
# among them, because they are the words the two readings share.
_A_PART_NAMED = (
    "arm", "arms", "wrist", "wrists", "leg", "legs", "ankle", "ankles", "foot", "feet",
    "toe", "toes", "finger", "fingers", "thumb", "hand", "hands", "rib", "ribs",
    "collarbone", "clavicle", "shoulder", "elbow", "shin", "tibia", "fibula", "knee",
    "hip", "femur", "bone", "bones", "fracture", "fractured", "surgery", "pinned",
    "metal plate", "screw", "screws")


# A leg is a bone until the line says whose it is: "how long should i rest a leg of lamb" is the
# joint on the board, and this row answered it with the cast and the X-ray. A meat word anywhere in
# the line is the kitchen reading, however the rest of it is worded.
_A_JOINT_OF_MEAT = re.compile(
    r"\b(?:lamb|beef|pork|chicken|turkey|duck|goose|brisket|gammon|veal|venison|meat|steak|"
    r"joint of|of lamb|of beef|of pork|roast)\b")


def _not_a_break_from_work(understood):
    """False when the line's "break" is a rest, so the healing row keeps its bones.

    "how long is my break" was answered "About six weeks for most bones - six for a wrist or
    collarbone", and so were "how long should a break be" and "how long are my breaks at work".
    A line that names a part - a wrist, a leg, a bone, a fracture - is a bone question whatever
    else it says, and a line that says whose break it is, with no part in it, is a rest.
    """
    said = str((understood or {}).get("text") or "").lower()
    if _A_JOINT_OF_MEAT.search(said):
        return False
    words = set(str(word).lower() for word in ((understood or {}).get("words") or ()))
    if words & set(_A_PART_NAMED):
        return True
    if _A_HEALING_WORD.search(said):
        return True
    return not _A_REST_NOT_A_BONE.search(said)


def _healing(memory, understood):
    """One answer, with the part's own number when the line names one."""
    words = set((understood or {}).get("words") or ())
    slow = words & {"leg", "legs", "shin", "tibia", "fibula", "femur", "ankle", "ankles",
                    "knee", "hip", "foot", "feet"}
    if slow:
        return ("Bones in the leg take the longest: about 12 weeks for a shin or ankle, and a "
                "thigh bone can be four months or more. The cast usually comes off before the "
                "bone is fully strong - it is the X-ray at each clinic visit that decides - and "
                "the muscles and joint need a few weeks after that to feel normal, so build back "
                "slowly rather than testing it early.")
    return ("About six weeks for most bones - six for a wrist or collarbone, six to eight for an "
            "arm, and longer for a leg or anything that had to be pinned, up to 12 weeks or more. "
            "Children heal faster, often in half the time. The cast comes off before the bone is "
            "fully strong and the joint takes a few more weeks to feel normal, and smoking slows "
            "bone healing a lot, so it is worth stopping while it knits.")


ENTRIES.append(entry(
    "bone-healing",
    (_HEAL_PARTS, _HEAL_TIME),
    _healing,
    guard=_not_a_break_from_work,
    # the triage question (is it broken?) is the row above, and an old break that healed years
    # ago is not a healing question at all
    avoid=("is it broken", "or broken", "or sprained", "do i need an x-ray",
           "do i need an xray", "how do i know", "how can i tell", "years ago", "last year",
           "when i was", "sticking out", "through the skin", "bone is showing", "999",
           # "back" alone took "when can i go back to work" off this row, which is the
           # question the "back to work" key is for
           "ambulance", "unconscious", "neck", "my back", "back pain", "lower back",
           "slipped disc", "spine", "my son", "my daughter",
           "my child", "my baby", "my dog", "my cat", "my mum", "my dad", "my husband",
           "my wife", "my partner",
           # a healing cut, a healing tattoo or a healing piercing is skin, not bone
           "cut", "cuts", "wound", "tattoo", "piercing", "burn", "scab", "sore", "gums",
           "tooth", "teeth", "wisdom tooth", "nail", "nails",
           # and a thing that has broken is not a bone at all
           "phone", "screen", "laptop", "tv", "telly", "washing machine", "car", "boiler",
           "hoover", "vacuum", "glasses", "heart", "heartbroken",
           # and a new joint is its own recovery, with its own numbers: the leg answer's
           # "shin or ankle" is no answer to "how long does a knee replacement take"
           "replacement", "knee replacement", "hip replacement", "resurfacing",
           # cooking bones are not a healing bone: "how long to simmer chicken bones for broth"
           # and "how long do i cook beef bones for stock" are the broth rows' own questions,
           # and "bones" with "how long" is this row's key too (helpful-hippo, #5679)
           "stock", "broth", "bouillon", "simmer", "carcass", "for stock", "for broth",
           "bone broth", "soup", "cook the bones", "roast the bones", "boil the bones",
           "beef bones", "chicken bones", "lamb bones", "ham bone", "bones for",
           # and the kitchen words are the kitchen's: "rib" and "ribs" are in the healing row's
           # parts and "how long" in its time, so a rack of ribs became a fracture (fleet-kettle,
           # #5679). A healing bone is never in an oven.
           "cook", "cooks", "cooking", "cooked", "boil", "boils", "boiled", "roast", "roasts",
           "roasted", "oven", "barbecue", "bbq", "grill", "grilled", "slow cooker", "recipe",
           "marinade", "marinate", "smoker", "air fryer")))

# Ice or heat is the one question every ache ends with, and "should i use a heat pack" was a
# shrug while "should i put ice or heat on a sprained ankle" had the ankle answer. The row below
# answers only the choosing - which one, for how long, and what it must not go on - and it stands
# down for a part with its own row, because that row knows the part and this one does not.
#
# The guard is the fence that keeps the row out of the rest of the house: "heat" and "hot" are the
# boiler's words as much as a muscle's, and the bare key words plus "should i" took "should i
# leave the heating on low all day", "no hot water or heating" and "how much water should i drink
# walking in 30 degree heat". A line is answered only when it names a body or an ache, or one of
# the things you put on one.
ACHE_WORDS = frozenset((
    "muscle", "muscles", "muscular", "sprain", "sprained", "strain", "strained", "pulled",
    "pull", "ache", "aches", "aching", "achy", "sore", "soreness", "stiff", "stiffness",
    "injury", "injured", "swollen", "swelling", "twinge", "cramp", "cramps", "tight",
    "back", "neck", "shoulder", "shoulders", "knee", "knees", "ankle", "ankles", "wrist",
    "wrist", "elbow", "hip", "hips", "thigh", "calf", "shin", "foot", "feet", "arm", "arms",
    "leg", "legs", "joint", "joints", "tendon", "ligament", "whiplash", "flaring", "flare"))
COMPRESS_WORDS = frozenset((
    "heat pack", "heat packs", "heat pad", "heat pads", "ice pack", "ice packs", "hot pack",
    "cold pack", "cold packs", "wheat bag", "wheat bags", "ice bath", "cold compress",
    "hot compress", "frozen peas", "ice cubes", "hot water bottle", "ice", "icing"))


# A compress is a thing a kitchen also has: frozen peas are a bag of peas before they are a cold
# pack, and ice is what a drink wants. A line about cooking them is the cooking card's, and a line
# about a tray in the freezer is the freezer's, however good the match on "frozen peas" is.
_ON_A_BODY = ("ice it", "ice that", "ice my", "ice the", "icing it", "put ice", "use ice",
              "apply ice", "hold ice", "hold an ice", "ice pack on", "ice pack to", "pack on",
              "put a cold", "put heat", "use heat", "apply heat", "heat it", "heat that",
              "heat my", "heat the", "heat or ice", "ice or heat", "hot or cold", "cold or hot",
              "compress on", "should i ice", "should i heat", "frozen peas on", "peas on",
              # The comparison itself is the question, with no part named and no ache word:
              # "is heat better than ice" was a hedge and "is a hot water bottle better than ice"
              # was answered with the freezing point of water, while "is heat or ice better" got
              # this card. Naming both of the two is what makes it this row's line.
              "heat better than ice", "hot better than cold", "better than ice", "than ice",
              "better than heat", "than heat", "heat vs ice", "ice vs heat", "heat versus",
              "ice versus", "heat or cold", "cold or heat", "ice or hot", "heat and ice")
# The noun that follows "heat the", "ice my" and the rest of the phrases above, and the nouns that
# make it a house, a kitchen or a garden instead of a body. "heat the room", "heat the house",
# "ice the cake" and "heat the bath water" are all lines this row used to answer with a compress.
_HEAT_OR_ICE_THE_THING = re.compile(
    r"\b(?:heat|heating|ice|icing|hot|cold)\s+(?:the|my|our|that|this|a|an)\s+([a-z']+)")
_A_THING_THAT_IS_NOT_A_BODY = frozenset((
    "room", "rooms", "house", "houses", "home", "flat", "kitchen", "bedroom", "bathroom", "hall",
    "hallway", "lounge", "garage", "shed", "office", "conservatory", "loft", "attic", "cellar",
    "caravan", "car", "van", "bed", "bath", "shower", "pool", "greenhouse", "oven", "pan", "pot",
    "kettle", "mug", "cup", "bottle", "thermos", "cake", "buns", "bread", "milk", "wine", "beer",
    "water", "radiator", "radiators", "boiler", "heating", "thermostat", "air", "whole house",
    "place", "window", "windows", "door", "towel", "towel rail", "dehumidifier", "humidifier",
    "washing machine", "dryer", "tumble", "dishwasher", "microwave", "fridge", "freezer"))


_NOT_ON_A_BODY = ("cook", "cooks", "cooked", "cooking", "boil", "boils", "boiled", "boiling",
                  "oven", "bake", "baked", "baking", "recipe", "roast", "roasted", "fry",
                  "fried", "frying", "steam", "steamed", "steaming", "microwave", "defrost",
                  "defrosting", "thaw", "thawed", "saucepan", "freezer", "freeze", "freezes",
                  "freezing", "ice cube tray", "ice tray", "in the fridge",
                  # ice under the wheels is the road, not a compress: "should i pull away in
                  # second gear on ice" and "what should i do about black ice" both reached this
                  # row on the bare word "ice" (and, for the first, on "pull" from ACHE_WORDS).
                  "black ice", "gear", "pull away", "drive", "driving", "road", "roads", "tyre",
                  "tyres", "windscreen", "brake", "braking", "grit", "gritting", "pavement",
                  "pavements", "snow", "icy")


def _a_place_you_would_ice(understood):
    """True when the line is about a body, an ache, or something you put on one.

    A `guard` and not an `ask`: `score` lets a line that wants something past the ask list, and
    "heat" is the boiler's word too - so the words that make it a body question have to be read
    out of the whole line rather than listed as an ask.

    The compress words are not enough on their own: "how long do frozen peas take to cook" and
    "how long before ice freezes" both name a compress and are neither of them a body question,
    and this row was answering both with the ice-or-heat card while the kitchen's own row for
    frozen peas sat one match away.
    """
    reading = understood if isinstance(understood, dict) else {}
    line = " " + " ".join(str(reading.get("clean") or reading.get("text") or "").lower().split()) + " "
    if any(" " + word + " " in line for word in _NOT_ON_A_BODY):
        return False
    # "heat the", "ice my" and the rest say what the heat or the ice is going on, so the noun after
    # them decides who answers: "is it cheaper to run a dehumidifier or heat the room" was this
    # card, because `heat the` is in the list above and a room is not a body. Only a body word or
    # something you put on one keeps the line, and the phrase being there at all is what is being
    # overruled - a room, a house or an appliance is never a compress.
    for thing in _HEAT_OR_ICE_THE_THING.findall(line):
        if thing in _A_THING_THAT_IS_NOT_A_BODY and thing not in ACHE_WORDS:
            return False
    # The compress is only this row's when it is being put on something. "should i ice it" and
    # "should i use heat or ice" are this row; "should i pull away in second gear on ice" and
    # "what should i do about black ice" are the road, and it was answering those too.
    if any(" " + phrase + " " in line for phrase in _ON_A_BODY):
        return True
    for word in sorted(ACHE_WORDS, key=len, reverse=True):
        if " " + word + " " in line:
            return True
    return False


ENTRIES.append(entry(
    "heat-or-ice",
    (("heat", "ice", "hot", "cold", "warm", "warmth",
      "heat pack", "ice pack", "hot pack", "cold pack", "wheat bag", "heat pad",
      "hot water bottle", "ice bath", "cold compress", "frozen peas", "ice cubes"),
     ("should i use", "should i put", "should i apply", "do i use", "or heat", "or ice",
      "heat or ice", "ice or heat", "which is better", "which one", "better for", "good for",
      # "is heat better than ice" is the same comparison as "which is better", and it was the
      # one shape the ask list did not have: a hedge, while "is heat or ice better" got the card.
      "better than", "rather than", "heat or cold", "cold or heat", "heat and cold",
      "what should i use", "help", "helps",
      # the same question asked as a permission or a timer: "can i put ice on a fresh sprain"
      # and "how long should i hold an ice pack on" were a punt and the moving-house card
      "can i put", "can i use", "can i apply", "should i", "how long", "how often",
      "am i meant to")),
    "Cold for a fresh knock and heat for a stiff, old ache. Ice in the first 48 hours of a "
    "sprain, a bump or a pulled muscle: a bag of frozen peas or an ice pack wrapped in a tea "
    "towel, 15 to 20 minutes at a time, every two or three hours, never straight on the skin and "
    "never for longer, because that burns. After that, heat - a hot water bottle, a wheat bag or "
    "a warm bath, 15 to 20 minutes - loosens a muscle that has tightened up, so it is the one for "
    "a stiff neck or a back that has been bad for days. Never heat a fresh injury, a hot swollen "
    "joint or anywhere you cannot feel properly, and do not use either on broken skin. Heat on a "
    "sprain after two days is fine; ice on a stiff neck is not. If the joint is hot, very swollen "
    "or you cannot use it, that is a look-at-it-today rather than a compress.",
    guard=_a_place_you_would_ice,
    # a part with its own row knows more than this one does, and so does a period, a burn and a
    # headache: "can i use a hot water bottle for period pain" is the cramp answer and heat on a
    # burn is the burn's own instruction not to
    # A named part does not stand this row down any more. A part with its own row knows more
    # than a general compress card, and that is why the list below used to hold the wrists, the
    # ankles, the shoulders and the lower back - but a part's row knows more about the part, not
    # about this question: "should i ice my wrist" and "should i ice my shoulder" were answered
    # with a ganglion cyst, "should i use heat on my neck" with "That's your call, not mine", and
    # "should i apply heat to my lower back" with the heating bill. This row is the one written
    # for cold-then-heat, and it says when each is the right one, so it takes the part when the
    # line asks about heat or ice. A stiff neck keeps its own answer, which says which of the two
    # to use for a neck rather than what each is for, so the ask about a stiff neck is in here and
    # the bare word "neck" is not: "ice or heat for a stiff neck" and "is a hot water bottle good
    # for a stiff neck" are the stiff-neck card's, and "should i ice my neck" is this one's.
    avoid=("stiff neck", "neck ache", "crick", "period", "periods", "cramps",
           "burn", "burned", "burnt", "scald", "scalded",
           "headache", "migraine", "temperature", "fever", "nappy rash", "toothache",
           # a bruise has its own card and it is the better answer: "should i ice a fresh bruise"
           # was the bruise card and this row would have taken it. A hot bath and sore muscles
           # after exercise are the ache card's, which says more than this one can.
           "bruise", "bruises", "bruised", "hot bath", "bath", "sore muscles", "aching muscles",
           "dog", "cat", "baby", "pregnant", "pregnancy",
           # a bill is a cost question, and "is it cheaper to run a dehumidifier or heat the
           # house" reached this card through "or heat" and was told to ice a sprain. The other
           # side of the comparison is a machine or the house, never a body.
           "cheaper", "cheap", "cost", "costs", "expensive", "electricity", "energy", "bill",
           "bills", "tariff", "dehumidifier", "kilowatt", "kwh", "per hour", "running cost",
           # the phrases, not the bare word "heating": an avoid word is read loosely enough to
           # cover the words it is made of, so "heating" here stood this row down on "or heat"
           "central heating", "heating on", "gas heating", "electric heating", "heat the house",
           "heating the house", "heating bill", "heating the flat", "radiator", "radiators",
           "boiler", "heat pump")))
# `pulled-muscle` in health.py answers a pulled muscle in general ("two to three weeks"), and it
# stands down on a calf and a groin because those two are a clot and a hernia until proven
# otherwise. The muscle people actually name is the one where the number is the whole question and
# where the general answer is wrong: "how long does a torn hamstring take to heal" was the day-one
# sprain card with no number in it, and a hamstring is four to eight weeks rather than two to
# three. So this row is keyed on the named muscle, not on the word "muscle".
_MUSCLE_PARTS = ("hamstring", "hamstrings", "pulled hamstring", "torn hamstring",
                 "hamstring strain", "hamstring injury", "calf", "calves", "calf muscle",
                 "pulled calf", "torn calf", "calf strain", "groin", "groin strain",
                 "pulled groin", "adductor", "thigh muscle", "quad", "quads", "quadriceps",
                 "torn muscle", "tore a muscle", "muscle tear")


def _muscle_healing(memory, understood):
    """The muscle's own numbers, with the slower end named when the line says which muscle.

    A groin and a hamstring do not heal on the same timetable, so the muscle the line or the
    thread names picks the number: "how long before i can play again", said after a groin pull,
    is asking about the groin.
    """
    words = set((understood or {}).get("words") or ()) | set((understood or {}).get("background") or ())
    # a hamstring and a calf are the two that really do take two months; a thigh or a groin is
    # quicker, and "pulled a muscle in my thigh how long till its better" is not asking about a
    # tear unless it says torn
    slow = words & {"hamstring", "calf", "calves", "tear", "tore", "torn", "badly",
                    "completely", "snapped"}
    if words & {"groin", "adductor"}:
        return ("A groin strain is usually two to six weeks, and the milder ones are back in a "
                "fortnight: the first week is ice and rest from the twisting and kicking, then "
                "gentle stretching, and back to football or five-a-side only when you can sprint "
                "and change direction without pain. A sudden sharp pain, or a lump that appears in "
                "the groin when you cough, wants a physio rather than time.")
    if slow:
        return ("A torn hamstring or calf is four to eight weeks, and the last third of that is "
                "the part people rush: run again only when you can move it through its full "
                "range without pain and it feels as strong as the other side. A sudden snap, a "
                "lot of bruising, or a dent in the muscle wants a physio this week rather than "
                "rest alone.")
    return ("A pulled thigh muscle is usually two to three weeks: ice it for 15 minutes every few "
            "hours for the first two days, then keep it gently moving, because gentle movement "
            "heals faster than total rest. Go back to sport when it moves fully without pain and "
            "feels as strong as the other side, and see a physio if it is no better after a "
            "fortnight.")


ENTRIES.append(entry(
    "muscle-healing",
    (_MUSCLE_PARTS, _HEAL_TIME),
    _muscle_healing,
    # the day-one strain card matches a pulled calf just as well and says what to do, not how
    # long, so the row that answers the question asked nudges past it
    bias=2,
    # building muscle is a training question with no injury in it, and the day-after ache is
    # sport's, which says the soreness is normal and sells nobody a fortnight of rest
    avoid=("build muscle", "building muscle", "muscle mass", "gain muscle",
           "grow muscle", "put on muscle", "muscle tone", "bulk", "protein", "shakes",
           "sets and reps", "workout", "gym", "soreness", "doms",
           "day after", "next day", "delayed onset",
           # a muscle that is not a person's: an animal's, or somebody else's
           "my dog", "my cat", "my puppy", "my horse", "my son", "my daughter", "my child",
           "my baby", "my husband", "my wife", "my partner", "my mum", "my dad",
           # the kitchen: "how long to cook a pulled pork" and "strain the" are not injuries
           "pulled pork", "pulled beef", "pulled chicken", "pulled jackfruit", "pork",
           "beef", "chicken", "jackfruit", "cook", "cooks", "cooking", "cooked", "oven",
           "slow cooker", "recipe", "air fryer", "bake", "baked", "stock", "sieve",
           "drain", "juice", "yoghurt", "yogurt", "curds",
           # a heart, a chest or a head is not this row: those lines are emergencies' or the
           # named-topic answers', and "heart muscle" must never be told to rest for a fortnight
           "heart", "chest", "head", "eye", "eyes", "jaw", "stomach", "tummy",
           # a calf or a thigh that is swollen, hot or one-sided is the clot question, which
           # `safety` and the swollen-leg rows answer
           "swollen", "swelling", "hot", "red", "clot", "numb", "tingling", "one side",
           "pregnant", "pregnancy", "surgery", "operation", "replacement")))


ENTRIES.append(entry(
    "piercing-infection",
    (("piercing", "piercings", "pierced ear", "ear piercing", "nose piercing", "nose ring",
      "nose stud", "nose hoop", "septum", "helix", "tragus", "daith", "cartilage piercing",
      "earring hole", "earring", "belly piercing", "belly button piercing", "belly bar",
      "lip piercing", "eyebrow piercing", "industrial piercing", "earlobe"),
     ("red", "redness", "swollen", "swelling", "hot", "weeping", "oozing", "pus", "yellow",
      "green", "infected", "infection", "spreading", "streaking", "throbbing", "smelly",
      "fever", "angry", "sore and", "hurts")),
    _piercing_infection,
    guard=_a_piercing_in_trouble,
    bias=2,
    avoid=("how long", "aftercare", "keloid", "crusty", "crust", "when can i change",
           "downsize", "can i swim", "how do i clean", "how do i look after")))


# "how long should a tampon stay in" was a shrug, and once another row stood down it came back
# from a wound row about closing a cut - the timer question answered by whatever card happened to
# hold the verb "stay in". A tampon is worn for a stretch and taken out, so the number is the
# answer, and one warning rides on top of it.
_TAMPON_WORD = re.compile(r"\btampons?\b")
_NOT_A_TAMPON_LINE = re.compile(
    r"\b(bins?|bin it|dispose|disposal|throw (?:it|them) away|flush\w*|down the loo|"
    r"wrapper|applicator|recycl\w*|compost\w*|landfill)\b")


def _a_tampon_worn_too_long(understood):
    """True when the line is about wearing a tampon, and not about getting rid of one.

    "can i use a tampon while pregnant" is answered here too - the reply ends with pads rather
    than tampons during pregnancy - so pregnancy does not stand the row down. What does stand it
    down is a line about the bin, the loo or the wrapper: the rubbish row owns those.
    """
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join([str(reading.get("clean") or ""),
                     " ".join(str(word) for word in (reading.get("words") or ()))])
    return bool(_TAMPON_WORD.search(said)) and not _NOT_A_TAMPON_LINE.search(said)


ENTRIES.append(entry(
    "tampon-how-long",
    (("tampon", "tampons"),
     ("how long", "how often", "leave", "leaves", "stay in", "stays in", "staying in",
      "keep in", "keeps in", "keeping it in", "in for", "overnight", "sleep", "slept",
      "all night", "asleep", "fell asleep", "hours", "long can", "long should",
      "when should", "forgot", "forget", "change", "changed", "changing", "safe", "okay",
      "ok", "can i", "should i", "wear", "wearing", "use", "using", "put one in")),
    "Change a tampon every four to six hours and never leave one in for more than eight, so "
    "take it out before bed rather than sleep through with the same one. Use the lowest "
    "absorbency that still lasts four hours, wash your hands before and after, and if one has "
    "been in longer than that take it out now and watch for a fever, a rash like sunburn, "
    "vomiting, dizziness or a sore throat: that is toxic shock syndrome, which is rare but "
    "serious, so ring 111 for advice. Contact lenses and retainers have their own limits, and "
    "pads rather than tampons are the answer during pregnancy and for the first weeks after a "
    "baby.",
    guard=_a_tampon_worn_too_long,
    bias=1))


# "how long does a walk in centre take" is not a question about walking: the line carries "how
# long" and "walk", and the pace card answered it with the pace of a mile - then, once that card
# stood down, with a search hedge. Nobody can put a number on a queue before the person gets
# there, so the answer is the part that is knowable: what decides the order, how to shorten the
# wait, and what to do if it gets worse while they sit.
ENTRIES.append(entry(
    "the-wait-at-a-walk-in-centre",
    ("walk in centre", "walk-in centre", "walk in center", "walk in clinic",
     "walk-in clinic", "walk in service", "urgent care centre", "urgent care center",
     "urgent treatment centre", "minor injuries unit", "minor injuries",
     "out of hours gp", "out of hours doctor", "the walk in"),
    "Nobody can tell you before you go: a walk-in centre sees people in the order they need "
    "seeing rather than the order they arrived, so a queue of two hours can move in twenty "
    "minutes when something urgent comes in, and a quiet room can still mean a long wait. Ring "
    "the centre or look at its own site on the day for the wait it is running, and go early "
    "rather than late in the evening. Take a drink, a book and any medicines you take with you, "
    "and tell the desk if you get worse while you are sitting there rather than wait your turn.",
    ask=("wait", "waits", "waiting", "queue", "how long", "long will", "long do i",
         "how quick", "busy", "packed", "hours", "tonight", "this evening", "weekend"),
    # going there, finding it and what it costs are other questions, and the pace card answers
    # the walking ones
    avoid=("how do i get", "parking", "postcode", "address", "where is", "nearest",
           "walk up", "walk to", "how far", "open on christmas", "phone number")))


# Coming off a bike, a horse, a ladder or a trampoline had no card of its own: "i came off my
# bike", "i fell off my bike", "she came off her horse" and "he came off his motorbike" got no
# answer at all, and "the cyclist came off his bike and is holding his arm" got the card that tells
# you to scrub a mark off your hands with a nail brush. A fall is the commonest injury people bring
# to the bot, and what helps is the same whether you were on two wheels or on a ladder.
#
# The second group is the thing fallen off plus the words for hurting, so "orders fell off" and
# "the paint came off the door" stay where they are, and the mechanical half of a bike is kept out
# by name: "the chain came off" is a repair, not a fall.
_OFF_A_THING = ("came off", "fell off", "fell from", "come off", "fall off", "went over the",
                "over the handlebars", "came a cropper")
_FALL_AVOID = ("chain", "chains", "derailleur", "gears", "gearset", "brake", "brakes", "pedal",
               "pedals", "wheel", "wheels", "tyre", "tyres", "tire", "tires", "saddle", "sprocket",
               "cassette", "handlebar", "mudguard", "rack", "pannier", "battery",
               "motor", "throttle", "exhaust", "spark plug", "clutch", "pill", "medication",
               "my meds", "wagon", "a lorry", "the back of a lorry", "radar", "the list",
               "diet", "my food", "the challenge", "bandwagon", "sales", "orders", "shares", "price",
               "prices", "paint", "button", "handle", "sticker", "label", "wallpaper", "tiles",
               "the map", "nearly fell", "nearly came",
               # a fall that says what it cost is the injury card's line, not this one: "my son
               # fell off his bike and hurt his arm" is first aid for a hurt limb, and this row
               # took the two tests that guard it.
               "hurt", "hurts", "hurting", "sore", "ache", "aches", "aching", "pain", "painful",
               "broken", "break", "fracture", "swelling", "swollen", "can't move", "cant move")

ENTRIES.append(entry(
    "came-off-a-thing",
    (_OFF_A_THING,
     ("bike", "bikes", "bicycle", "cycle", "horse", "pony", "scooter", "motorbike", "motorcycle",
      "moped", "ladder", "trampoline", "skateboard", "skates", "skis", "sled", "sledge",
      "roof", "wall", "stairs", "steps", "horse", "quad", "go kart", "swing", "climbing frame",
      "bruise", "bruised", "graze", "grazed", "gashed", "landed", "hit", "banged", "knocked",
      "arm", "wrist", "elbow", "shoulder", "collarbone", "knee", "hip", "ankle", "hand", "head",
      "ribs", "walk", "weight")),
    "Coming off is a fall, so check the head first: a bang that knocked them out, made them sick, "
    "left them confused or gave them a bad headache is A&E the same day, and so is anything they "
    "cannot remember. Most falls land on a hand or a shoulder, and a wrist that cannot take weight "
    "or an arm that cannot be lifted across the chest is worth an X-ray today - the collarbone is "
    "the break people miss. Grazes want cool running water, a dressing and no scrubbing. Ice a "
    "bruise for 20 minutes at a time with a cloth round it, take paracetamol or ibuprofen if you "
    "can, and expect it to be stiffer tomorrow than today. A helmet that took the hit is finished, "
    "even with no crack you can see.",
    # not the body table's AVOID: it carries FALL ("fall", "banged", "knocked", "bump") to keep the
    # part rows off a fall, and a fall card that inherits it stands down on its own subject - the
    # first draft answered "i came off my bike" and not "i fell off my bike".
    avoid=_FALL_AVOID,
    # The lowest bias on purpose: a card that names what the fall cost answers first ("my son fell
    # off his bike and hurt his arm" is the hurt limb, not the head), and this one fills the fall
    # that nothing else answers.
    bias=0))
