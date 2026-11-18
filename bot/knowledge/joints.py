"""A joint that clicks, pops or grinds: the noise people notice and then ask about.

"my knuckle clicks when i bend it", "my jaw clicks when i eat", "my wrist clicks when i move it"
are everyday lines, typed as a symptom rather than a question, so the key is the part plus the
word for the noise. The knee has had an answer of its own since the sport domain was written
(bot/knowledge/sport.py, knee-noise), and every other joint had none: the line came back as an
echo, which is the worst answer for a person who is quietly wondering whether it is serious.

The reply is built from the part the line names, because a clicking jaw and a clicking knuckle
are not the same worry, and "a joint of yours clicks" reads as if nobody heard which one.

A line that also says it hurts is not this entry at all: the body-part entries already answer
"my wrist clicks when i move it and it hurts" with what a wrist pain probably is and what to do
about it, and a general "have it looked at" would say less than the answer it replaced. So the
words for hurting are in AVOID, and this entry answers the noise on its own.

The words of a machine and of a sense are held out in AVOID: cars, boilers, phones and doors
click all day, and an ear that clicks is a hearing question, not a joint.
"""

from .lookup import entry

import re

ANSWERS = ("health",)

# The noise words. "crack" and "click" are the two people use, and both are also things that
# happen to eggs, phone screens and voices, which is what AVOID below is for.
NOISY = ("click", "clicks", "clicked", "clicking", "pop", "pops", "popped", "popping",
         "creak", "creaks", "creaking", "grind", "grinds", "grinding", "snap", "snaps",
         "snapping", "crack", "cracks", "cracking", "cracked", "noisy", "noise",
         "clunk", "clunks", "clunking")

# The parts this answers for. The knee is not one of them: sport.knee-noise holds it, with the
# noise answer and the stairs answer told apart by whether the line says it hurts.
PARTS = ("knuckle", "knuckles", "jaw", "jaws", "wrist", "wrists", "elbow", "elbows",
         "shoulder", "shoulders", "hip", "hips", "ankle", "ankles", "thumb", "thumbs",
         "toe", "toes", "finger", "fingers", "joint", "joints", "neck", "spine")

# The word to put in the sentence: the person's own word, singular, because "a knuckles that
# clicks" reads wrong and "a finger" answers a hand nobody mentioned.
ONE = {"knuckles": "knuckle", "jaws": "jaw", "wrists": "wrist", "elbows": "elbow",
       "shoulders": "shoulder", "hips": "hip", "ankles": "ankle", "thumbs": "thumb",
       "toes": "toe", "fingers": "finger", "joints": "joint"}

# The words for hurting. A line with one of these in it belongs to the body-part entry, which
# says what the pain probably is and what helps: this entry answers the noise on its own.
HURTS = ("hurt", "hurts", "hurting", "pain", "pains", "painful", "sore", "ache", "aches",
         "aching", "achy", "swollen", "swelling", "swelled", "stiff", "locked", "locking",
         "locks", "stuck", "sharp")

AVOID = ("knee", "knees", "kneecap",
         # a jaw is the one noisy joint with advice of its own: the jaw joint has a dentist, a
         # night guard, soft food and the lock to watch for, and the general "clicking that does
         # not hurt is harmless" is a thinner answer to "my jaw clicks when i eat". health.py's
         # jaw-click row keys the jaw and reads the click, the lock and the ache, so this row
         # stands down on the jaw and lets it answer.
         "jaw", "jaws", "jawbone", "jaw joint", "tmj",
         # a car, a bike and a boiler click too
         "car", "cars", "brake", "brakes", "engine", "clutch", "gearbox", "exhaust", "bike",
         "bicycle", "boiler", "radiator", "pipe", "pipes", "tap", "taps", "washing machine",
         "dishwasher", "tumble", "fridge", "freezer", "oven", "toaster", "kettle",
         # a house clicks
         "door", "doors", "gate", "window", "windows", "hinge", "floor", "floors",
         "floorboard", "floorboards", "decking", "stair", "stairs", "wall", "walls", "wood",
         "wooden", "tile", "tiles", "pavement", "road",
         # a device clicks
         "phone", "iphone", "laptop", "computer", "mouse", "keyboard", "headphones",
         "speaker", "speakers", "radio", "tv", "television", "printer", "camera", "app",
         "video", "audio", "volume", "hearing aid", "playstation", "xbox",
         # a click that is a sound in the head, not a joint
         "ear", "ears", "throat", "swallow", "swallowing", "hearing", "tinnitus",
         "chest", "heart", "breath", "breathing", "tooth", "teeth",
         # an egg, a mug and a voice crack
         "egg", "eggs", "shell", "boil", "boiling", "boiled", "mug", "cup", "glass",
         "screen", "voice", "whip", "meringue", "batter", "pastry", "dough", "bread", "cake",
         # something happened to the joint: "my ankle clicks after a sprain" is a rehab
         # question, and "it needs nothing doing" is the one thing not to say three days in
         "sprain", "sprained", "sprains", "strain", "strained", "strains", "injury",
         "injuries", "injured", "hurt myself", "fall", "falls", "fell", "fallen", "accident",
         "surgery", "operation", "op", "operated", "replaced", "replacement", "physio",
         "physiotherapy", "cast", "crutches", "brace", "break", "broke", "broken",
         "fracture", "fractured", "dislocated", "dislocate", "torn", "tear", "tore",
         "arthroscopy", "keyhole",
         # a joint that is not stable, or a nerve that is caught, is not a noise: "my hip
         # clicks and then gives way", "my wrist clicks and is numb" have answers of their own
         # and "it needs nothing doing" is the wrong thing to say to either
         "gives way", "give way", "giving way", "gave way", "out of place", "popped out",
         "pops out", "numb", "numbness", "numbed", "tingling", "tingles", "tingle",
         "pins and needles", "weak", "weakness", "unstable", "catching", "catches",
         # a child, a partner or a pet is not this body
         "my son", "my daughter", "my child", "my kid", "my kids", "my baby", "my toddler",
         "my husband", "my wife", "my partner", "my mum", "my mom", "my mother", "my dad",
         "my father", "my dog", "my cat", "my puppy")


SHOULDER_TIMELINE_CARD = (
    "A shoulder replacement is in a sling for the first 3 to 6 weeks, with gentle movement "
    "exercises started within days and the physio's programme once the sling comes off: driving "
    "again at about 6 to 8 weeks once you can turn the wheel and brake without pain, desk work at "
    "6 to 12 weeks, and full recovery 6 to 12 months. Hospital is usually one or two nights. Ring "
    "the ward or 111 if the wound starts leaking, the shoulder turns hot or red, or the pain "
    "suddenly gets worse.")

SHOULDER_IMPLANT_CARD = (
    "A shoulder replacement usually lasts 10 to 15 years, and a reverse shoulder about the same - "
    "it is not a countdown: the muscle you keep working and the load you put through it decide, so "
    "the exercises the physio gives you are what buy the time. If a shoulder that has been fine "
    "for years starts to ache, grind or give way, that is worth an X-ray rather than waiting, and a "
    "worn shoulder can be revised the way a hip can.")

SHOULDER_SORE_CARD = (
    "Yes - soreness and stiffness for months after a shoulder replacement is normal, and it eases "
    "with the exercises rather than with rest: it is at its stiffest in the first six weeks and "
    "keeps loosening for up to a year, and a warm, puffy shoulder after a session is the usual "
    "reaction to doing more. Build up slowly, ice it for 15 minutes after the exercises, and keep "
    "the daily ones going even on a bad day. Ring the ward or 111 if the shoulder is hot and red, "
    "the wound leaks, or the pain gets worse each week rather than better.")

SHOULDER_SLEEPING_CARD = (
    "Sleep is the awkward part for the first weeks after a shoulder replacement: sleep propped up "
    "on two or three pillows with the arm supported on one in front of you or on a pillow beside "
    "you, and not on the operated side. A cushion tucked under the elbow takes the pull off the "
    "shoulder, and most people find a recliner or the corner of a sofa easier than a bed at first. "
    "A bad night is normal rather than a sign of damage.")


def _timeline(memory, understood):
    """The healing schedule, spoken about the joint the line named."""
    if _joint(understood) == "shoulder":
        return SHOULDER_TIMELINE_CARD
    return TIMELINE_CARD


def _implant_life(memory, understood):
    if _joint(understood) == "shoulder":
        return SHOULDER_IMPLANT_CARD
    return IMPLANT_CARD


def _soreness(memory, understood):
    if _joint(understood) == "shoulder":
        return SHOULDER_SORE_CARD
    return SORE_CARD


def _sleeping(memory, understood):
    if _joint(understood) == "shoulder":
        return SHOULDER_SLEEPING_CARD
    return SLEEPING_CARD


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


def _a(word):
    """The article for the word: "an ankle", "a knuckle". The sentence is spoken about the
    part the person named, so it has to read like a sentence for every one of them."""
    return ("an " if word[:1] in "aeiou" else "a ") + word


def _joint(understood):
    """"shoulder" if the line named one, otherwise "replacement" for a hip or a knee.

    The numbers in the cards below are a hip's and a knee's - sticks, driving an emergency stop,
    kneeling, 15 to 25 years - and a shoulder shares none of them. Rather than fence the shoulder
    out of the row entirely (which would send the person back to a shrug), the card speaks about
    the joint they had.
    """
    words = _words(understood)
    return "shoulder" if any(word in words for word in SHOULDER) else "replacement"


# A joint that has been replaced is not a joint with an ordinary noise in it. The line names the
# replacement, and "a tendon flicking over a bump, and it needs nothing doing" is not what a
# person three months into a new hip should be told: the noise there is soft tissue settling
# round the new parts, and the things worth watching are different (infection, and a joint that
# gives way). The words are held out of the noise entry above on purpose, so this one owns them.
NEW_JOINT_NOISE = ("click", "clicks", "clicked", "clicking", "clunk", "clunks", "clunking",
                   "pop", "pops", "popped", "popping", "grind", "grinds", "grinding",
                   "creak", "creaks", "creaking", "catch", "catches", "catching", "noisy",
                   "noise")
# A joint that feels loose, wobbles or gives way is not the settling-noise question even though
# people say it the same way: one is a sound, the other is a joint that does not hold, and the
# useful reply to the second is to ring the team rather than to promise it will settle.

NEW_JOINT_CARD = (
    "Clicking, clunking or a catching feeling around a new joint is usually the soft tissue "
    "moving over the new parts, and it is common while the muscles are still settling - keep up "
    "the exercises the team gave you and mention it at your next check. Ring the ward that did "
    "the operation, or 111, the same day if the joint is hot, red or more painful than it was, "
    "if you have a fever or the wound is weeping, or if the joint gives way or you cannot put "
    "your weight on it.")

# A joint that has been replaced asks a different set of questions from the same joint before:
# how long it takes to heal, when you can drive, whether kneeling ever comes back, and how long
# the thing itself lasts. On main almost all of them were punts ("I'd rather not guess") and two
# were wrong - "is it normal to be stiff after a knee replacement" got "ease off running", and
# "when can i go back to work after a hip replacement" got the back-to-work-after-a-cold answer.
# The replacement is the subject here, so the words are the replacement's own and no line without
# one can reach these entries.
#
# Each answer's first sentence has to carry the whole reply, because the composer may hand back
# only that sentence: a card that opens with "soreness is normal" and puts the six weeks in the
# second sentence gives a person who asked "how long?" nothing to go on.
# "Resurfacing" is a road's word as well as a hip's: "theyre resurfacing our road next week" was
# answered the joint timeline ("walking on it the day after the operation, driving at 6 weeks"),
# and "my road is closed" got the small-day nod. The road line belongs to the postcode row, so the
# replacement cards stand down for a line that names a road, a street or a pavement and no joint.
ROAD_WORDS = ("road", "roads", "street", "streets", "kerb", "kerbs", "pavement", "pavements",
              "driveway", "driveways", "tarmac", "junction", "junctions", "carriageway",
              "footpath", "footpaths", "pothole", "potholes")


def _not_a_road(understood):
    """True unless the line is about a road that names no joint - then a roadworks line answers."""
    words = _words(understood)
    if not any(word in words for word in ROAD_WORDS):
        return True
    return any(word in words for word in PARTS) or any(
        word in words for word in ("hip", "knee", "shoulder", "surgeon", "operation",
                                   "physio", "hospital", "nurse", "ward", "recovery",
                                   "physiotherapy"))


# "is it worth replacing a bath with a shower" is a builder's question that read as wound care:
# "replacing" is enough for REPLACED_JOINT and "bath" and "shower" are both WASH words, so two words
# about a bathroom made a washing-after-an-operation line. The thing being replaced has to be a
# joint; a line that replaces something else is not one of these cards.
# The determiner is optional: people type the article-less way too ("replacing bath with shower
# worth it", "replacing boiler cost"), and with the determiner required the guard read neither and
# both fell back to the wound card. The guard only has to answer "is the thing after 'replacing' a
# joint", and without the article the next word is that thing just the same.
A_REPLACING_A_THING = re.compile(
    r"\breplac(?:e|ing|ed)\s+(?:(?:a|an|the|my|our|your|his|her|their)\s+)?(?P<thing>[a-z]+)")
# A dressing, a bandage, a cast and a plaster are things a person replaces on a body rather than
# on a house, so "i replaced the dressing on my knee" keeps the card about a knee that was replaced.
THE_JOINT_WORDS = ("hip", "knee", "shoulder", "joint", "joints", "resurfacing", "implant",
                   "implanted", "replacement", "dressing", "dressings", "bandage", "bandages",
                   "cast", "plaster")


def _not_something_else_replaced(understood):
    """True unless the line replaces a thing that is not a joint - a bath, a boiler, a road."""
    said = str((understood or {}).get("clean") or "") if isinstance(understood, dict) else ""
    things = A_REPLACING_A_THING.findall(said.lower())
    if not things:
        return True
    return any(word in THE_JOINT_WORDS for word in things)


def _a_replacement(*args, **kwargs):
    """One of the cards about a joint that was replaced, which a road line must not reach."""
    asked = kwargs.pop("guard", None)
    if asked is None:
        kwargs["guard"] = lambda understood: (_not_a_road(understood)
                                              and _not_something_else_replaced(understood))
    else:
        kwargs["guard"] = lambda understood: (_not_a_road(understood)
                                              and _not_something_else_replaced(understood)
                                              and asked(understood))
    return entry(*args, **kwargs)


REPLACED_JOINT = ("replacement", "replaced", "new hip", "new knee", "new joint",
                  "new shoulder", "resurfacing", "resurfaced", "hip replacement",
                  "knee replacement", "shoulder replacement", "partial knee", "total knee",
                  "total hip", "had my hip done", "had my knee done", "reverse shoulder")

# A shoulder is a different operation from a hip or a knee: nobody walks on it, uses sticks for
# it or kneels with it, so the walking/driving/hospital schedule and the 15-to-25-year figure are
# wrong sentences for that person. The rows that speak those numbers ask `_joint()` and hand the
# shoulder its own, and the rows that only make sense for a leg stand down for it.
SHOULDER = ("shoulder", "shoulders", "new shoulder", "shoulder replacement",
            "reverse shoulder", "reverse shoulder replacement", "resurfaced shoulder")

# The same replacement words without the shoulder ones: the rows about stairs, sleeping for a
# hip and a swollen leg are hip-and-knee rows and must not claim a shoulder line.
HIP_KNEE = ("replacement", "replaced", "new hip", "new knee", "new joint", "resurfacing",
            "resurfaced", "hip replacement", "knee replacement", "partial knee", "total knee",
            "total hip", "had my hip done", "had my knee done")

TIMELINE = ("how long", "heal", "heals", "healing", "recover", "recovery", "recovering",
            "drive", "driving", "driven", "back to work", "go back to work", "return to work",
            "swim", "swimming", "hospital",
            "nights in", "how many days", "how many weeks", "when can i", "how soon",
            "how long before", "what can i do", "weeks", "months")

TIMELINE_CARD = (
    "Walking on it the day after the operation, off the sticks at about 6 weeks, driving again "
    "at 6 weeks once you can do an emergency stop without thinking, and back to desk work at 6 "
    "to 12 weeks: hospital is usually 2 to 4 nights for a hip and 1 to 3 for a knee, and full "
    "recovery is 6 to 12 months for a hip and up to a year for a knee. "
    "Kneeling after a knee replacement is uncomfortable for most people and may never come back "
    "fully. Ring the ward or 111 if the wound starts leaking, the joint turns hot or red, or the "
    "pain suddenly gets worse.")

SORE = ("stiff", "stiffness", "stiffen", "sore", "soreness", "hurts", "hurting", "pain",
        "painful", "swollen", "swelling", "normal", "expected", "should it", "is it")

SORE_CARD = (
    "Yes - soreness and stiffness for months after a joint replacement is normal, and it eases "
    "with the exercises rather than with rest: the joint is at its stiffest in the first six "
    "weeks and keeps loosening for up to a year, and a warm, puffy knee or hip after exercise is "
    "the usual reaction to doing more. Build up slowly, ice it for 15 minutes after the exercises, "
    "and keep the daily ones going even on a bad day. Ordinary swelling is around the joint; a "
    "calf or a whole leg that swells, goes hot or is tender to touch is not ordinary swelling - "
    "ring the ward or 111 the same day, because a clot is the thing to rule out. Ring about the "
    "joint too if it is hot and red, the wound leaks, or the pain gets worse each week rather "
    "than better.")

KNEEL = ("kneel", "kneeling", "kneel down", "on my knees", "get down on the floor",
         "get up off the floor")

KNEEL_CARD = (
    "Kneeling is the one thing many people never get back after a knee replacement: the new knee "
    "can take it, but the skin over it is numb and sore against a hard floor, so most people kneel "
    "on a cushion for a few minutes at a time rather than rule it out - try it on something soft "
    "once the wound is fully healed and the swelling has gone down. After a hip replacement you "
    "can kneel, but get down on the operated knee first and keep the new hip from bending past 90 "
    "degrees for the first few months. If kneeling is for gardening or a job, ask the physio to "
    "practise it with you rather than finding out on the day.")

IMPLANT_LIFE = ("how long does it last", "how long will it last", "how long do they last",
                "last", "lasts", "lifetime", "how many years", "wear out", "worn out",
                "wears out", "need another", "second replacement", "revision", "20 years",
                # "i need a second hip replacement" is a question about the life of the first
                # one, and on main it was read as a shopping line: "What kind of replacement do
                # you usually go for?" The replacement is named, so this row answers it.
                "second hip replacement", "second knee replacement", "another hip replacement",
                "another knee replacement", "needs doing again", "needs redone",
                "has worn out", "gone wrong after years")

IMPLANT_CARD = (
    "A hip or knee replacement usually lasts 15 to 25 years, and about 8 in 10 are still going "
    "at 20 years; when one does wear out, a second operation to replace the worn parts is a "
    "routine job - smaller than the first, with a similar recovery. It is not a countdown: "
    "weight, activity and the wear on it decide, so the muscles kept strong and a healthy weight "
    "are what buy the time. If a joint that has been fine for years starts to ache, grind or "
    "give way, that is worth an X-ray rather than waiting.")


WASH = ("shower", "showers", "bath", "baths", "washing", "wash", "get it wet", "get it wet",
        "wound", "wounds", "dressing", "dressings", "stitches", "staples", "scar", "scars",
        "waterproof", "sealed", "healed over")

WASH_CARD = (
    "A shower is usually fine once the dressing is off and the wound is dry and sealed, and most "
    "wards send people home with a waterproof dressing so it can happen sooner - but a bath, a "
    "hot tub or a swim waits until the wound is fully closed, around two to six weeks, because "
    "standing water is where infection gets in. Pat the wound dry rather than rubbing it, leave "
    "it open to the air when you can, and put nothing on it - no creams, oils or powders. Ring "
    "the ward or 111 if the wound turns hot or red, leaks or smells, or the edges start to open.")

STAIRS = ("stairs", "stair", "upstairs", "downstairs", "steps", "flight of stairs")

STAIRS_CARD = (
    "Stairs are fine from the day you get home, one stair at a time with a rail and the crutches "
    "in the other hand: the good leg goes up first and the operated leg comes down first - up "
    "with the good, down with the bad - and both feet land on each step rather than one leg per "
    "stair. Sit down on the bottom step to put the sticks and slippers on rather than bending. If "
    "you live alone and the stairs are steep, ask the ward to watch you do a flight before you go "
    "home; it is a normal part of the discharge check.")

SLEEPING = ("sleep", "sleeping", "slept", "lie on", "lying on", "lie down", "on my side",
            "side to sleep", "in bed")

SLEEPING_CARD = (
    "Sleep is the awkward part for the first few weeks, and the answer depends on the joint: "
    "after a hip, sleep on your back with a pillow between the knees, or on the unoperated side "
    "with the pillow still between the knees so the new hip cannot cross the middle - keep that "
    "up for the six weeks the ward tells you. After a knee, sleep on your back with the leg "
    "straight on a pillow, or on the good side with a pillow under the new knee. A pillow under "
    "the heels stops the sheet rubbing, and a bad night is normal rather than a sign of damage.")

# A numb or itchy patch around the scar is the commonest odd feeling after a replacement, and the
# joint is fine: the little nerves under the incision are cut on the way in. It needs its own
# answer because the line reads like a symptom - on main "my hip replacement scar is numb" got
# the cauda-equina card ("numbness or pins and needles between your legs ... seen the same day"),
# which is frightening, wrong, and the one shape where the 999 card should not fire.
SCAR = ("scar", "scars", "numb", "numbness", "no feeling", "lost feeling", "pins and needles",
        "tingling", "tingles", "itchy", "itches", "itching", "dead patch")

SCAR_CARD = (
    "A numb patch of skin around the scar is normal after a joint replacement and it often stays "
    "that way: the small nerves under the incision are cut on the way in, so the skin there feels "
    "wooden, tingly or dead to touch, and it usually softens over a year or two rather than "
    "meaning anything about the joint. An itchy scar is the same story - healing nerves - and so "
    "is a scar that pulls or feels tight. A scar that turns hot, red, weepy or spreads, or "
    "numbness that comes on suddenly or spreads up the leg, is the one to ring the ward or 111 "
    "about, the same day.")

LOOSE = ("feels loose", "feel loose", "loose", "wobble", "wobbles", "wobbly",
         "gives way", "give way", "giving way", "gave way", "gives out", "unstable",
         "not stable", "pops out")

# A leg that swells after a hip is the one swelling that must never be reassured: the joint can
# be perfectly normal and the calf still be a clot. On main the line got a fluid card, and from
# the soreness card it would get "a warm, puffy hip after exercise is the usual reaction to doing
# more" - the one sentence a person with a clot should not be told.
# An ankle that puffs up after a knee replacement is the ordinary post-operation swelling, so
# the ankle is deliberately not here: this row is the calf and the whole leg, which is the shape
# a clot takes.
SWOLLEN_LEG = ("leg is swollen", "leg swollen", "leg has swollen", "swollen leg",
               "leg is puffy", "puffy leg", "leg has puffed", "calf is swollen", "swollen calf",
               "calf hurts", "calf is sore", "calf is tender", "my calf", "leg went big",
               "leg swelled up", "leg is tight")

SWOLLEN_LEG_CARD = (
    "A leg that swells after a hip or knee replacement is not ordinary swelling and it is worth a "
    "phone call rather than a wait: a calf that is hot, tight, red or tender, or a whole leg that "
    "swells up, can be a clot, and clots are more common in the weeks after this operation than "
    "people expect - ring the ward that did the operation or 111 and say when the swelling "
    "started. If you are also short of breath, coughing or feeling faint, that is 999. Swelling "
    "around the joint itself is the ordinary sort, and that one goes down with ice and the leg "
    "raised.")

LOOSE_CARD = (
    "A new joint that feels loose, gives way or clunks hard when you put weight on it is one to "
    "have looked at rather than wait for the next appointment: ring the ward or your surgeon's "
    "team and tell them when it started and what it does. Sometimes it is weak muscle around a "
    "joint that is fine - the physio can tell you that in one visit - and sometimes the parts "
    "need checking, which is why it is a phone call rather than a wait. If it gives way and you "
    "fall, or the joint is hot and red with it, treat that as urgent: 111 the same day.")

def _noisy_joint(memory, understood):
    """The noise answer, about the part the line named: "A knuckle that clicks...".

    A line with a word for hurting never reaches here: it is in AVOID, so the body-part entry
    answers it with what the pain probably is.
    """
    words = _words(understood)
    part = next((ONE.get(word, word) for word in PARTS if word in words), "joint")
    return (_a(part).capitalize() + " that clicks or pops and does not hurt is almost always harmless: a "
            "tendon flicking over a bump, or gas coming out of the joint fluid, and it needs "
            "nothing doing. Keep the muscles around it working, because clicking that turns "
            "into pain is usually a strength problem rather than the noise. If it starts to "
            "hurt, swell or lock, have a physio or your GP look at it.")


ENTRIES = [
    entry("noisy-joint", (NOISY, PARTS), _noisy_joint, avoid=AVOID + HURTS),
    # "how long does a hip replacement last" is the implant's life, not the recovery, and it is
    # a different answer, so it is read first and holds only its own words.
    _a_replacement("replaced-joint-noise", (REPLACED_JOINT, NEW_JOINT_NOISE), NEW_JOINT_CARD, bias=2,
          # a joint that is hot and red is the infection question, and a torn or dislocated one
          # is the urgent one: both keep the cards they had
          avoid=("hot", "red", "fever", "temperature", "wound", "weeping", "oozing", "pus",
                 "infection", "infected", "dislocated", "dislocate", "popped out",
                 "out of place", "fell", "fallen", "fall", "broke", "broken", "fracture",
                 "torn", "tore", "numb", "numbness", "tingling", "pins and needles",
                 "dog", "cat", "puppy")),
    _a_replacement("joint-implant-life", (REPLACED_JOINT, IMPLANT_LIFE), _implant_life, bias=2),
    # kneeling is the one question in the recovery family with an answer of its own, and it is
    # the one people ask before an operation rather than after
    _a_replacement("joint-kneeling", (REPLACED_JOINT, KNEEL), KNEEL_CARD, bias=2,
          avoid=("pray", "praying", "church", "garden", "weed", "weeds", "weeding")),
    _a_replacement("joint-replacement-timeline", (REPLACED_JOINT, TIMELINE), _timeline, bias=1,
          # the cost of the operation is the money table's; a joint that has failed (hot, red,
          # dislocated, broken) is the urgent one and keeps its answer
          avoid=("cost", "costs", "private", "how much does", "how much is", "nhs waiting",
                 "waiting list", "dislocated", "dislocate", "popped out", "out of place",
                 "broke", "broken", "fracture", "fractured", "infected", "infection",
                 "hot and red", "red and hot", "pus", "oozing", "kneel", "kneeling",
                 "shower", "bath", "wound", "dressing", "stairs", "upstairs", "downstairs",
                 "sleep", "sleeping", "side",
                 # "replacement" is a general word, and "driving" is in the timeline words, so
                 # "i need a replacement driving licence" scored twice here and was told when
                 # it could drive again after the operation. A replacement is a joint only when
                 # the thing being replaced is one, so a document, a part, a battery or an
                 # appliance stands this row down and its own table answers it.
                 "licence", "license", "passport", "photocard", "document", "documents",
                 "battery", "batteries", "phone", "laptop", "screen", "remote",
                 "bulb", "bulbs", "fuse", "fuses", "filter", "filters", "part", "parts",
                 "spare", "tyre", "tyres", "tire", "tires", "wheel", "wheels",
                 "boiler", "radiator", "washer", "washing machine", "dishwasher",
                 "fridge", "freezer", "oven", "kettle", "toaster", "door", "lock",
                 "handle", "zip", "zipper", "button", "buttons", "strap", "strap on",
                 "tile", "tiles", "roof", "fence", "key", "keys", "card", "cards")),
    # The washing, stairs and sleeping questions are what a person asks the week they get home,
    # and the timeline answer is no answer to them: a shower line got a paragraph about driving
    # and desk work. Each has its own row and its own first sentence, and the timeline stands
    # down for their words so the two cannot both claim a line.
    _a_replacement("joint-replacement-washing", (REPLACED_JOINT, WASH), WASH_CARD, bias=2,
          # a scar that is numb, itchy or sore is the scar card's question, not the washing one
          avoid=("hot and red", "red and hot", "oozing", "pus", "smelly", "infected",
                 "infection", "fever", "temperature", "numb", "numbness", "no feeling",
                 "pins and needles", "tingling", "itches", "itching", "itchy",
                 "sore", "hurts", "hurting", "pain", "painful")),
    _a_replacement("joint-replacement-scar", (REPLACED_JOINT, SCAR), SCAR_CARD, bias=2,
          avoid=("hot and red", "red and hot", "oozing", "pus", "smelly", "infected",
                 "infection", "fever", "temperature", "weeping")),
    _a_replacement("joint-replacement-stairs", (HIP_KNEE, STAIRS), STAIRS_CARD, bias=2,
          # "my new knee clunks when i go upstairs" is the noise question with a stair in it,
          # and "it hurts on the stairs" is the soreness one: this row is only the how-to
          avoid=("click", "clicks", "clicking", "clunk", "clunks", "clunking", "grind",
                 "grinds", "grinding", "creak", "creaks", "catch", "catches", "catch",
                 "pop", "pops", "loose", "wobble", "wobbly", "gives way", "giving way",
                 "hurt", "hurts", "hurting", "pain", "painful", "sore", "swollen",
                 "ache", "aches", "aching",
                 # stairs after a shoulder are the same stairs as before: no crutches, no order
                 "shoulder", "shoulders", "arm", "elbow", "wrist", "hand")),
    _a_replacement("joint-replacement-sleeping", (REPLACED_JOINT, SLEEPING), _sleeping, bias=2),
    _a_replacement("joint-replacement-loose", (REPLACED_JOINT, LOOSE), LOOSE_CARD, bias=2,
          avoid=("hot and red", "red and hot", "dislocated", "popped out", "broke", "broken",
                 "fracture")),
    _a_replacement("joint-replacement-swollen-leg", (HIP_KNEE, SWOLLEN_LEG), SWOLLEN_LEG_CARD,
          bias=2),
    _a_replacement("joint-replacement-soreness", (REPLACED_JOINT, SORE), _soreness,
          # the failed-joint and infection lines keep their own answers
          avoid=("dislocated", "dislocate", "popped out", "out of place", "broke", "broken",
                 "fracture", "infected", "infection", "hot and red", "red and hot", "pus",
                 "oozing", "fever", "temperature",
                 # deciding whether to replace a thing is a shopping question, not a question
                 # about the joint that was already replaced: "my phone screen is cracked, is
                 # it worth replacing" and "my car tyre is cracked, is it worth replacing"
                 # both got "soreness and stiffness for months after a joint replacement"
                 "worth replacing", "worth repairing", "worth fixing", "repair or replace",
                 "fix or replace", "replace it", "replace the", "replacing it")),
]


# --- a joint that locks, catches or will not straighten ----------------------
# The noise answer above says a clicking joint needs nothing doing, and that is the wrong thing
# to say about a joint with something physically in the way: a torn meniscus or a loose body in a
# knee, a tendon catching in a swollen sheath in a finger. HURTS already holds "locks", "locking"
# and "stuck" - so the noise row stands down for these words and, on main, nothing else picked
# them up: "my knee locks when i walk" came back "Got it. Is there anything you'd like a hand
# with?", "my finger locks when i bend it" and "my hand locks up" the same. This row is that
# answer, built from the part the line named, because a locked finger has self-care and a locked
# knee is a phone call.
LOCKED = ("locks", "locked", "locking", "lock up", "locks up", "locked up", "locking up",
          "catches", "catching", "caught on", "gets stuck", "get stuck", "got stuck",
          "will not straighten", "wont straighten", "cannot straighten", "cant straighten",
          "will not bend", "wont bend", "cannot bend", "cant bend", "jams", "jammed",
          "jamming", "in a locked")

# The parts a lock is asked about. The knee joins here even though it is not a PARTS word: a
# knee that locks is this question and not the noise one, and sport.py's knee rows key only the
# words for giving way and for hurting.
LOCK_PARTS = PARTS + ("knee", "knees", "kneecap", "leg", "legs", "thumb", "hand", "hands")

TRIGGER_FINGER_CARD = (
    "A finger that locks or clicks and then catches as it straightens is trigger finger: the "
    "tendon that bends the finger runs through a sheath, the sheath swells, and the tendon has to "
    "jump through the tight spot - which is why it locks bent and then lets go with a click. "
    "Rest it from hard gripping for a few weeks, keep it straight at night with a finger splint "
    "from a chemist, and take ibuprofen if it is sore. See your GP if it stays locked, keeps "
    "locking during the day, or a second finger starts: a steroid injection into the sheath "
    "usually sorts it, and a small operation does if it does not.")

LOCKED_CARD = (
    "A {part} that locks, catches or will not straighten has something physically in the way, so "
    "it is worth being examined this week rather than waiting for it to settle: ring your GP and "
    "say which movement brings it on, whether it lets go on its own, and whether there was a twist "
    "or a knock before it started. A knee that locks is usually a torn cartilage or a loose piece "
    "of it catching in the joint, which a physio or doctor can tell apart by hand in one "
    "appointment, so keep off twisting sports and deep squats until then rather than testing it. "
    "Go to 111 the same day if the joint swells up, is hot, or you cannot put weight on it at all.")


def _locked_joint(memory, understood):
    """The lock answer, about the part the line named, with the finger's own self-care."""
    words = _words(understood)
    part = next((ONE.get(word, word) for word in LOCK_PARTS if word in words), "joint")
    if part in ("finger", "fingers", "thumb", "thumbs"):
        return TRIGGER_FINGER_CARD
    return LOCKED_CARD.format(part=part)


ENTRIES.append(
    entry("locked-joint", (LOCKED, LOCK_PARTS), _locked_joint,
          # a jaw that locks is health.py's jaw row (soft food, a night guard, a dentist), and a
          # joint that was replaced, hurt or was knocked is a different question with an answer
          # "how do i lock my knee" is the gym's version - a knee held straight under a bar - and
          # a how-to has no business being told to see a doctor
          avoid=("how do i lock", "lock out", "lock my knee", "lock your knee", "locking out",
                 "lock the knee", "jaw", "jaws", "jaw joint", "tmj", "dog", "cat", "door",
                 "doors", "gate",
                 "car", "cars", "bike", "bicycle", "phone", "laptop", "computer", "screen",
                 "window", "windows", "cupboard", "cupboards", "drawer", "drawers"),
          bias=2))
