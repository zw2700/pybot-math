"""Stopping something: vaping, drinking. The ask is always "how do I stop".

The smoking half lives in `science.py` (#1413, entry `quit-smoking`), which is approved and
answers `how do i quit smoking` with the same method; this table answers the two habits that
were still a shrug and must not take the smoking line back.

These are the everyday habits people decide to give up on a Monday, and the answer is not
a lecture: it is the one method that is known to work, how long the bad part lasts, and
what to do when it does. Each entry needs the habit and a word for stopping, so
"does smoking cause cancer" and "how many units in a pint" stay with the entries that
answer them, and "i spilled beer on my shirt" stays with the stain answer.

The avoid lists hold whole phrases ("smoked salmon", "smoke alarm") rather than the bare
word, because an avoid matches the inflections of what it lists: avoiding "smoked" also
throws away "smoking", which is the line every entry here is for.
"""

import re

from .lookup import a_thing_has_stopped, entry
from .wording import screens_are_somebody_elses

# A bare "chewing" in the mouth row is what a follow-up needs, because the line carries no
# subject of its own: "how do i stop it chewing things" after "my puppy is chewing everything"
# is about the puppy, and the row's stand-in for a pen or a lip (gum, a straw) is the wrong
# answer for a dog. The animal in the earlier line is the understanding layer's business, so
# the row reads the subject it resolved instead of carrying a copy of every animal's phrasing:
# when the "it" of the line is a pet, the row stands down and the pet entry that the same
# behaviour word reaches ("puppy" + "chewing") answers with the training answer.
PET_SUBJECT = ("dog", "dogs", "puppy", "puppies", "pup", "pups", "cat", "cats", "kitten",
               "kittens", "rabbit", "rabbits", "bunny", "bunnies", "hamster", "hamsters",
               "guinea pig", "guinea pigs", "gerbil", "gerbils", "ferret", "ferrets",
               "parrot", "parrots", "bird", "birds", "horse", "horses", "pony", "ponies",
               "tortoise", "tortoises", "pet", "pets", "litter tray")

_PET_ANY = re.compile(r"\b(?:" + "|".join(re.escape(word) for word in PET_SUBJECT) + r")\b")


def _about_a_pet(understood):
    """Whether the subject this line points back to is an animal.

    Only the carried subject counts - the "it"/"them" of the line, or the subject of the line
    it leans on - never the words the person typed, because a line that types an animal already
    reaches the pet entry on its own words.
    """
    if not isinstance(understood, dict):
        return False
    said = []
    remembered = understood.get("ref")
    if isinstance(remembered, dict):
        said.extend(value for value in remembered.values() if isinstance(value, str))
    leans = understood.get("leans_on")
    if isinstance(leans, dict):
        subject = leans.get("subject")
        if isinstance(subject, str):
            said.append(subject)
        text = leans.get("text")
        if isinstance(text, str):
            said.append(text)
    return bool(said) and bool(_PET_ANY.search(" ".join(said).lower()))


MOUTH_TIP = ("Give the mouth or the fingers a stand-in: gum, a straw to chew, a pen you cannot "
             "bite to pieces, a bead on a chain. It happens at a desk or in front of a screen, so "
             "put the substitute where you sit and move the pen or the mirror out of reach.")


def _pet_row_answers_before_it(memory, understood):
    """Whether a row about the animal itself can answer this line instead of the mouth one.

    Standing aside is only worth it when an answer is waiting: the composer's next reading of
    a follow-up is the line with the earlier subject put back in, and when that reading reaches
    nothing the turn can end on a shape answer about something else. So the reading is made
    here, and this row steps aside only for a match in the animals' own domain.
    """
    from . import entries as all_entries       # the registry: no domain is imported here
    from .lookup import score, _forms
    if not isinstance(understood, dict):
        return False
    leans = understood.get("leans_on")
    carried = []
    if isinstance(leans, dict) and isinstance(leans.get("words"), list):
        carried = [word for word in leans["words"] if isinstance(word, str)]
    words = [word for word in (understood.get("words") or []) if isinstance(word, str)]
    together = [_forms(word) for word in carried + words]
    if not together:
        return False
    try:
        for item in all_entries():
            if getattr(item, "domain", "") == "pets" and score(item, together, carried + words):
                return True
    except Exception:
        return False               # a turn is never worth a crash over a lost improvement
    return False


def _mouth_tip(memory, understood):
    """The mouth tip, unless the thing being chewed is an animal's habit and not a person's."""
    if _about_a_pet(understood) and _pet_row_answers_before_it(memory, understood):
        return None
    return MOUTH_TIP

# Whose forgetting is it? "my mum keeps forgetting things" and "my husband keeps forgetting
# things" were answered with the reminder card - how to stop forgetting an errand yourself -
# because "keeps forgetting" and "things" are in this row's key. The memory-assessment entry
# next door keys both lines too and answers them well, and it could not get a look in. So the
# person word has to be the *subject* of the forgetting: a relative, a partner or another
# adult in front of it, not the person the errand is for ("i keep forgetting to ring my mum"
# is still this row's line, and the errand comes after the verb).
_ANOTHER_ADULT = (
    r"(?:mum|mom|mam|mother|dad|father|parent|parents|husband|wife|partner|spouse|"
    r"other half|nan|nana|gran|granny|grandma|grandad|grandpa|grandmother|grandfather|"
    r"son|daughter|child|kid|brother|sister|aunt|auntie|uncle|cousin|in law|"
    r"mother in law|father in law|friend|neighbour|neighbor|boss|colleague|coworker|"
    r"flatmate|housemate|landlord|carer|pal|chum|mate|nephew|niece|grandchild|grandson|"
    r"granddaughter|fiance|fiancee|stepmum|stepdad|sister in law|brother in law|missus|"
    r"other half|girlfriend|boyfriend)")
# The forgetting can be said as a state as well as a deed: "my best friend seems forgetful lately"
# and "my wife has become scatty" are the same worry as "my mum keeps forgetting things", and
# only the verb forms were here, so the friend's line got no answer at all.
_FORGOTTEN = (r"(?:forget|forgets|forgetting|forgot|forgotten|forgetful|forgetfulness|"
              r"memory|remember|remembers|repeating|repeats|confused|confusion|"
              r"getting confused|scatty|absent[- ]minded|away with it)")
_SOMEONE_ELSE_FORGETTING = re.compile(
    # "the wife keeps losing her glasses" says the person the same way "my wife" does: the
    # article in place of the possessive is how people talk about their own household.
    r"\b(?:my|his|her|our|their|the)\s+(?:\w+\s+){0,2}" + _ANOTHER_ADULT + r"\b"
    r"[^.!?]{0,30}?\b" + _FORGOTTEN + r"\b|"
    r"\b(?:he|she|they)\s+(?:keeps?|is|are|has|have|always|never|used to)\b"
    r"[^.!?]{0,25}?\b" + _FORGOTTEN + r"\b")


# The speaker's own memory said with an age: "im 50 and keep forgetting things" is asked as a
# worry about getting older, and the reminder card answers it as though a system would fix it.
_MY_AGE = re.compile(
    r"\b(?:im|i am|i'm)\s+(?:nearly |almost |just |only )?"
    r"(?:\d{2}|forty|fifty|sixty|seventy|eighty|ninety)\b|\bat my age\b|\bmy age\b|"
    r"\bgetting older\b|\bas i get older\b|\bsince i turned\b")
_FORGETTING = re.compile(
    r"\b(?:forget|forgets|forgetting|forgot|forgotten|forgetful|memory|remember)\b")


def _my_own_memory_and_my_age(understood):
    """Whether the speaker is asking about their own memory coming with age. A `guard=` test."""
    from ..compose.repair import line_of
    said = line_of(understood)
    if not said:
        return False
    text = " ".join(str(said).lower().replace("\u2019", "'").split())
    return bool(_MY_AGE.search(text) and _FORGETTING.search(text))


def _words_of(understood):
    """The line and whatever the reading carried with it, as one lower-case string.

    A follow-up is answered on the words of the line before it as well ("thats scary" after "my
    mum keeps forgetting things" is still her memory), so a guard about *whose* forgetting it is
    has to read the carried words too, not only the line as typed.
    """
    from ..compose.repair import line_of
    said = [line_of(understood)]
    if isinstance(understood, dict):
        for key in ("leans_on", "ref", "topic"):
            value = understood.get(key)
            if isinstance(value, dict):
                said.extend(str(item) for item in value.values() if isinstance(item, (str, int)))
                words = value.get("words")
                if isinstance(words, (list, tuple)):
                    said.extend(word for word in words if isinstance(word, str))
            elif isinstance(value, (list, tuple)):
                said.extend(word for word in value if isinstance(word, str))
    return " ".join(" ".join(said).lower().replace("\u2019", "'").split())


def _someone_else_is_forgetting(understood):
    """Whether another adult, not the speaker, is the one forgetting. A `guard=` test."""
    text = _words_of(understood)
    if not text:
        return False
    return bool(_SOMEONE_ELSE_FORGETTING.search(text)
                or _MY_AGE.search(text))


# "how do i help my husband stop drinking" is not the same question as "how do i stop
# drinking": the answer for the person doing it is the wrong voice for the person watching,
# so those lines go on to whichever entry handles somebody else's habit.
# Who is doing the forgetting decides the card. A relative's forgetting is a memory question
# (science.parent-memory), not the reminder system for the writer's own errands, and the two
# rows share the words "keeps forgetting" - so the person has to come first in the line, the way
# people say it: "my mum keeps forgetting things", "dad forgets what he went upstairs for".
_A_RELATIVE = re.compile(
    r"\b(?:my|his|her|their|our)\s+(?:mum|mom|mother|dad|father|parents|gran|granny|nan|nana|"
    r"grandma|grandmother|grandad|grandpa|grandfather|grandparents?|wife|husband|partner|spouse|"
    r"other half|son|daughter|brother|sister|aunt|auntie|uncle|cousin|boyfriend|girlfriend|"
    r"friend|mate|neighbour|neighbor|mother in law|father in law)\b")
# ... or the person is named by a pronoun, and it is not the writer: "he keeps forgetting",
# "she forgets everything" - a line about the writer says "i keep forgetting".
_SOMEBODY_ELSE = re.compile(
    r"\b(?:he|she|they)\s+(?:keeps?\s+forgetting|forgets|is\s+forgetful|"
    r"cant\s+remember|can't\s+remember|cant\s+recall|can't\s+recall|repeats|is\s+confused)")
_SOMETHING_FORGOTTEN = re.compile(
    r"\b(?:forgett?ing|forgets|forgetful|remember|remembers|recall|repeat(?:s|ing)?|"
    r"confused|gets lost|losing|loses)\b")


def _the_writer_is_the_one_forgetting(understood):
    """True when the writer is the one with the errand, so the reminder card may answer.

    A guard says whether its entry may answer, so this is the positive form: the card stands
    down when the line names somebody else as the forgetter.
    """
    if not isinstance(understood, dict):
        return True
    said = " ".join(str(understood.get("clean") or understood.get("text") or "").split()).lower()
    if not said:
        return True
    if _SOMEBODY_ELSE.search(said):
        return False
    relative = _A_RELATIVE.search(said)
    if relative and _SOMETHING_FORGOTTEN.search(said[relative.end():]):
        return False
    return True


# A line that says how bad the person feels is a line for the warm answer, not for a method:
# "i quit smoking 3 days ago and i feel awful" wants "three days is the worst of it", which is
# a different reply from "how do i quit smoking".
FEEL_BAD = ("feel awful", "feel terrible", "feel horrible", "feel like giving up",
            "i feel rubbish", "feel so low", "feel depressed")

THIRD_PARTY = ("my husband", "my wife", "my partner", "my boyfriend", "my girlfriend",
               "my mum", "my dad", "my parents", "my son", "my daughter", "my brother",
               "my sister", "my friend", "my friends", "my nan", "my gran", "my granny",
               "my grandma", "my grandad", "my grandpa", "my grandparent",
               "my uncle", "my aunt", "my auntie", "my cousin", "my colleague", "my mate",
               "my mother in law", "my father in law", "my flatmate", "help my",
               "he wants to", "she wants to", "he keeps", "she keeps")

# Words for stopping, shared by the three habits, plus the two-word phrases people type,
# since a phrase scores more than the two single words and wins against an entry that keys
# only one of them. The phrases name the habit ("quit smoking"), not the question ("how do i
# stop"): a phrase made of function words would go into the shared vocabulary that ranks
# every domain, and that is how a new table quietly moves an unrelated line like "nervous
# about a dentist appointment tomorrow" onto a different answer.
STOP = ("quit", "quitting", "quit for good", "stop", "stopping", "give up", "giving up",
        "cut down", "cutting down",
        # "im trying to cut back on the wine" was "Worth doing. What would you like help with
        # first?" - the same ask as "cut down", and the habit rows had only one of the two ways
        # people say it
        "cut back", "cutting back", "cut back on", "cutting back on", "ease off", "easing off",
        "pack in", "packed in", "cant stop", "can't stop",
        "quit smoking", "stop smoking", "give up smoking", "quit cigarettes",
        "stop drinking", "quit drinking", "cut down on drinking", "cut down on alcohol",
        "quit vaping", "stop vaping")

# A small habit is a thing you do without deciding to: nails, knuckles, the phone. The
# substitute belongs to the habit, so each one gets its own entry and its own tip. There is no
# shared method sentence on the end: a tip that has already said what to do does not need "one
# habit at a time" after it, and a general tail reads the same on every row, which is the tell
# that it is not answering this line. A line has to name the habit *and* say it wants to stop,
# so "my nails are brittle" and "my knuckles are sore" stay with the entries that answer them.

SMALL_HABITS = (
    # biting nails and scrolling the phone are not here: main grew `routines.nail-biting` and
    # `technology.screen-time-limits` while this branch waited, and both answer those lines better
    # than a shared tip can, so this table keeps only the habits that still had no owner.
    ("skin", ("skin picking", "picking my skin", "pick my skin", "picking at my skin",
              "picking spots", "picking at spots", "picking my spots", "picking at my face",
              "picking my face", "picking at scabs", "picking scabs", "picking a scab",
              "picking", "picking at"),
     "Picking is a hand habit, so give the hand something else: moisturise so the spot feels "
     "different, keep a fidget toy or a ring where your fingers go, and cover it with a plaster "
     "for the first week so your fingers stop there. Mirrors and screens are where it starts, so "
     "keep them out of reach."),
    ("knuckles", ("knuckles", "cracking my knuckles", "crack my knuckles", "cracking knuckles",
                  "fidgeting", "fidget", "jiggling my leg", "shaking my leg",
                  "bouncing my leg"),
     "Cracking and fidgeting are how the body burns off a wriggle, so the fix is a quieter outlet "
     "rather than sitting still: a stress ball in your pocket, a foot pressed to the floor, or a "
     "short walk every hour. It happens most in meetings and while waiting."),
    # The temper questions are the ones asked as an ask rather than a report: "how do i stop being
    # so irritable", "how do i control my anger" and "i keep losing my temper" were a hedge, a
    # hedge and - worse - the memory card, because "losing my temper" was read as losing a thing.
    # The children have their own card (`family.stop-shouting-at-kids`) and keep it.
    ("temper", ("anger", "angry", "temper", "irritable", "irritated", "irritability",
                "rage", "raging", "losing my temper", "lose my temper", "lost my temper",
                "short fuse", "snappy", "snapping at", "snapped at", "lashing out",
                "blowing up", "blow up at"),
     "Anger is mostly a physical build-up, so catch it early rather than arguing with it: notice "
     "the first sign - jaw, shoulders, a louder voice - and leave the room for five minutes, "
     "breathing out for longer than you breathe in. Say \"I need a minute\" rather than the thing "
     "you are about to say. Then look at the fuel: too little sleep, no lunch, four coffees and a "
     "hangover will do more to your temper than any argument. If the fuse has been short for weeks "
     "rather than days, see a GP: anxiety, depression and a thyroid problem all arrive as "
     "irritability, and talking therapy works on anger."),
    # Worrying is asked for as a how-to ("how do i stop worrying", "im worried all the time") and
    # the habit the answer needs is the postponement, not the reassurance. The chat lane answers
    # the person who says how they feel, and this is the person asking what to do.
    # not "stress": "how do i deal with stress" already has its own answer ("pick the smallest
    # physical thing first, because stress lives in the body") and it is the better one.
    ("worry", ("worry", "worrying", "worried", "anxiety", "anxious", "panicky", "dread",
               "overwhelmed",
               # "how do i calm my nerves" is the same question as "how do i stop worrying",
               # said in the body rather than the head, and it was the search hedge.
               "nerves", "my nerves", "on edge", "wound up", "keyed up", "butterflies",
               "racing heart", "nervous",
               # the second signal for the lines that name no worry at all: "how do i calm down"
               # is the same ask as "how do i calm my nerves", and it needs a word of its own in
               # the subject group or the score stays under the bar.
               "calm down", "calm myself down", "worked up", "shaky", "jittery",
               # The commonest way to ask this card's question is a frame around one of the
               # words above: "how do i stop worrying about work", "worried about money all the
               # time". One covered word is under the bar, so both of those were the search
               # hedge even though this tip is the answer. The frame is the second signal.
               "stop worrying", "worrying about", "worry about", "worries about", "worries me",
               "worrying me", "keep worrying", "always worrying", "worrying all the time",
               # And the same untensed ask from the other end: "how do i relax", "i cant relax".
               # Winding down and switching off are their own cards and keep them.
               "how do i relax", "relax", "relaxing", "cant relax", "can't relax"),
     "Give the worry a time and a page: fifteen minutes in the evening when you write down "
     "everything on your mind, then ask of each one what you would actually do if it happened, "
     "and what the next step is. When it turns up at three in the afternoon, write one line to "
     "bring to the slot and go back to what you were doing - postponing is the part that trains "
     "it. Ten slow breaths out, longer than the in, settle the body enough to do that. If it is "
     "most days for six months or more, that is worth the GP and talking therapy, which works "
     "well on this."),
    ("swearing", ("swearing", "swear", "bad language", "foul language", "cursing"),
     "Pick one substitute word and use it out loud for a week - 'sugar', 'flip', whatever you can "
     "say at work - because the habit is in the sound, not the meaning. It spikes with pain and "
     "frustration, so slow your breath for a second before you answer."),
    # phone: `technology.screen-time-limits` owns it
    ("snooze", ("snooze", "snoozing", "hitting snooze", "my alarm", "alarm"),
     "Put the alarm across the room and take the first one for a week, even when you are tired: "
     "the nine extra minutes cost you the deep sleep at the end of the night and leave you "
     "groggier. If mornings are brutal, go to bed half an hour earlier that week."),
    # Hair has its own substitute: a mouth stand-in is no help to fingers looking for loose hair,
    # and pulling in patches is a GP question rather than a habit tip.
    ("hair", ("pulling my hair", "pull my hair", "pulling my hair out", "twirling my hair",
              "twirl my hair", "twirling hair", "chewing my hair", "biting my hair",
              "playing with my hair", "hair twirling", "trichotillomania"),
     "Keep it up and back - a bobble, a clip, a hat - so there is nothing loose for your fingers to "
     "find, and give them a ring to reach for instead. It happens most when you are bored or "
     "thinking hard. If you are pulling hair out in patches, see a GP: it is a known condition, "
     "not something you do on purpose."),
    # snacks: `nutrition.snacking-night` owns the evening, and its answer names the cause (a
    # lunch that was too small) that a general snack rule cannot; `nutrition.snacking` has the rest.
    # nails are not here: `routines.nail-biting` answers them, and "biting my nails" in this row
    # took two good nail answers and swapped in a gum tip. "chewing my nails" was added here
    # later for the fingers and it took that answer back the same way: the nail card answers
    # "how do i stop chewing my nails" properly, and this row cannot say anything about nails,
    # so the phrase is gone and only the fingers stay.
    ("mouth", ("chewing my pen", "chew my pen", "biting my pen", "chewing gum", "chewing",
               # the fingers are the other thing people chew on, and the bare "chewing" alone
               # was under the score this row needs, so "how do i stop chewing my fingers" was
               # a shrug while "chewing my pen" was answered
               "chewing my fingers", "chew my fingers", "biting my fingers",
               "biting my cheeks", "biting my lips", "chewing my lips", "licking my lips"),
     _mouth_tip),
)

# Words that say the line wants to stop. "how do i stop" is the commonest, but people also say
# quit, break, kick, cut down, get out of.
STOP_SMALL = ("stop", "stopping", "quit", "quitting", "kick", "kicking", "give up", "giving up",
              "cut down", "cutting down", "cut back", "get out of", "cant stop", "can't stop",
              "how do i stop", "i keep", "keep", "i always",
              # the same ask said as control rather than stopping: "how do i control my anger"
              # was a hedge while "how do i stop being so irritable" was answered, and the two
              # are one question. A phrase rather than a bare "control", which belongs to the
              # dog on the lead and the volume on the telly.
              "how do i control", "how can i control", "how do i manage", "how do i handle",
              "how do i deal with", "how do i get rid of", "how can i stop", "how can i quit",
              "help me stop", "what can i do about")

# The count people quote is 21 days, which is wrong and discouraging. The measured figure is
# about two months, with a wide spread, and a missed day makes no difference.
HABIT_WORDS = ("habit", "habits", "routine", "routines", "streak", "willpower", "resolution")

HABIT_TIME_WORDS = ("how long", "how many days", "how many weeks", "take", "takes", "took",
                    "days", "weeks", "months", "21 days", "three weeks", "66 days", "really",
                    # the duration shapes, as phrases: "how long does it take to break a habit"
                    # is asking for the number, and a phrase scores more than the single words
                    # of the entry that answers the trigger instead.
                    "how long does it take", "how long to break", "how long to stop",
                    "how many days", "how many weeks")

# "nails" in a line about a tyre or a scratch is not a nail-biting line, and a habit question
# about the drink or the cigarette has its own entry above.
NOT_A_SMALL_HABIT = ("tyre", "tire", "puncture", "scratch", "screw", "hammer", "polish",
                     # a machine picks things up: "why has my hoover stopped picking up" is the
                     # air path, not a hand habit, and "stopped" is a stop word here
                     "hoover", "vacuum", "dyson", "mower", "lawnmower", "crumbs", "crumb",
                     "varnish", "manicure", "salon", "split", "splitting", "peel", "peeling",
                     "chipping", "brittle", "strengthen", "grow", "growing", "fake", "acrylic",
                     "extensions", "dentist", "tooth", "teeth", "guitar", "piano",
                     # the phone questions that want a setting, not a habit
                     "data", "battery", "storage", "signal", "contract", "sim", "bill",
                     "network", "wifi", "hacked", "stolen", "lost my phone", "screen",
                     # the drinking, smoking and betting lines have entries of their own
                     "smoking", "smoke", "cigarette", "cigarettes", "vape", "vaping",
                     "alcohol", "drinking", "drink", "beer", "wine", "hangover",
                     "bet", "betting", "gambling", "porn", "drugs",
                     # the skin, hair and stomach lines are the health lane's, not a habit tip
                     "breaking out", "breakout", "break outs", "acne",
                     "brittle", "snapping", "splitting", "split end", "split ends", "frizzy",
                     "frizz", "dry", "dryness", "greasy", "itchy", "itching", "rash",
                     "eczema", "dermatitis", "thinning", "hair loss", "bald", "dandruff",
                     "colour", "dye", "dyeing", "heartburn", "reflux", "indigestion",
                     "acid", "bloating", "hiccups", "cough", "snoring", "snore",
                     # a fussy eater is not a hand habit: "how do i deal with a picky husband" was
                     # answered "picking is a hand habit, so give the hand something else", because
                     # "picky" folds to "pick". The eater phrases only, so "how do i stop picking
                     # my skin" keeps the hand-habit tip it has always had.
                     "picky eater", "picky eaters", "fussy eater", "fussy eaters",
                     "faddy eater", "picky husband")

# One habit's own neighbours, where the shared list is not enough. "how do i stop my dog chewing
# the sofa" is a training question and got the mouth tip (gum, a straw to chew) instead of the
# chewing-is-normal answer it had; "i want to cut down on sugar without giving up biscuits" names a
# biscuit but is a sugar question, so the snacking tip stands aside for it.
SMALL_HABIT_EXTRA_AVOID = {
    "temper": ("kid", "kids", "child", "children", "son", "daughter", "toddler", "baby",
               "my mum", "my mom", "my dad", "my brother", "my sister", "my boss", "my manager",
               "neighbour", "neighbor", "dog", "puppy", "cat", "traffic", "driver", "road",
               "computer", "laptop", "phone", "game", "football", "referee",
               # a parent's shouting has its own card; a partner has one of its own in family.py
               "shouting at my kids", "at my kids", "at the kids", "at my children",
               "at my partner", "at my husband", "at my wife", "snapping at my partner",
               # the temper aimed AT the asker is not the asker's habit to fix: "my husband loses
               # his temper with me" was told to say sorry plainly, which is the wrong person
               # apologising. Possessive and third-person forms, because the row is the asker's.
               "his temper", "her temper", "their temper", "your temper",
               "loses his temper", "loses her temper", "lost his temper", "lost her temper",
               "losing his temper", "losing her temper", "his rag", "her rag",
               "temper with me", "loses it with me", "lost it with me"),
    "worry": ("dog", "dogs", "cat", "puppy", "kitten", "pet", "pets", "money", "rent", "bill",
              "bills", "job", "work", "office", "boss", "deadline", "shift", "interview", "exam", "exams", "test", "results", "health",
              "cancer", "lump", "pregnant", "pregnancy", "mum", "mom", "dad", "son", "daughter",
              "child", "children", "kid", "kids", "baby", "flight", "flying", "wedding",
              "party", "speech", "presentation", "the future", "the news",
              # The calm words added to the row are also the words for a frightened animal, a
              # crying baby and someone else's temper: those keep their own cards. A racing
              # heart is a symptom question, so the palpitation and chest shapes stay away too.
              "puppies", "pup", "cats", "kittens", "rabbit", "bird", "parrot", "horse",
              "toddler", "toddlers", "palpitations", "racing heart when", "chest pain",
              "short of breath", "nervous system", "nerve pain", "trapped nerve", "sciatica",
              "pinched nerve", "root canal", "tooth nerve", "nerves in my", "afraid of the dark",
              # calming someone else down is a different answer: the deck's angry-customer line
              # had its own card before this row learned the calm words, and keeps it.
              "customer", "customers", "patient", "patients", "passenger", "client", "clients",
              "colleague", "colleagues", "staff", "crew", "someone else", "the other one"),
    "mouth": ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "kittens", "pet", "pets",
              "rabbit", "hamster", "parrot", "bird", "horse", "teething", "sleeve", "collar",
              # a nail question is the nail card's, however it is said: the bare "chewing" key
              # above reached "how do i stop chewing my nails" and answered it with a gum tip,
              # which stood the nail answer down for that phrasing alone
              "nail", "nails", "nail biting", "cuticles",
              # the mouth habit is the person's own mouth, and the same words are a cleaning job
              # when a surface is named: "how do i get rid of chewing gum from clothes" was told
              # to chew a straw instead, because "chewing gum" and "get rid of" are both keyed
              # here. A garment, a floor or a piece of furniture is the stain row's line.
              "clothes", "clothing", "shirt", "shirts", "trousers", "jeans", "dress", "dresses",
              "skirt", "jumper", "jumpers", "cardigan", "coat", "jacket", "hoodie", "leggings",
              "shorts", "towel", "bedding", "sheet", "sheets", "duvet", "fabric", "wool",
              "carpet", "carpets", "rug", "rugs", "sofa", "settee", "couch", "mattress",
              "upholstery", "floor", "floors", "tiles", "pavement", "path", "wall", "walls",
              "shoe", "shoes", "trainer", "trainers", "boot", "boots", "table", "chair",
              "washing machine", "dryer", "tumble dryer", "car seat", "car", "seats"),
    "snacks": ("sugar", "sugary", "sugar in", "sugars",
               # an evening snack is nutrition.snacking-night's line, not a general snack rule
               "night", "at night", "in the evening", "evening", "after dinner", "late",
               "before bed", "night time", "nighttime"),
    # The habit row keys on the bare word "alarm" too, so a burglar alarm, a car alarm and a
    # pendant alarm all reached "put the alarm across the room". They belong to a house
    # (home.py's `burglar-alarm-going-off`), a car or a person's neck (lifeadmin.py).
    "snooze": ("burglar", "burglars", "intruder", "intruders", "house alarm",
               "security alarm", "security system", "alarm system", "alarm panel",
               "control panel", "the panel", "sensor", "sensors", "cctv", "smoke",
               "smoke alarm", "smoke detector", "carbon monoxide", "car alarm",
               "alarm on my car", "van", "vehicle", "fob", "key fob", "immobiliser",
               "siren", "car park", "mechanic", "pendant", "pendant alarm", "falls alarm",
               "fall alarm", "personal alarm", "telecare", "careline", "lifeline",
               "care alarm", "panic alarm", "panic button", "medical alarm"),
}

# The ask group is shared by every small habit, because they are all "how do I stop" questions.
# Calming down is the same question asked from the other end - "how do I calm my nerves" wants
# the breathing in the worry tip, and it said none of the stop words, so it was the search
# hedge. Only the worry row gets these, so a "how do I calm the baby" stays where it was.
WORRY_ASK = STOP_SMALL + (
    "calm", "calming", "calm down", "calm myself down", "how do i calm", "how can i calm",
    "settle", "settle myself", "how do i settle", "chill out", "wind down", "feel better",
    "get through")

# The ask frames people use for this card are not all stop words: "what helps anxiety" and
# "how do i relax" name the subject and then ask a plain question, and with no stop word in the
# line they were the search hedge. The frame is the second signal, and the subject word still has
# to be said, so a line about any other habit is unaffected.
WORRY_ASK = WORRY_ASK + (
    "how do i", "how can i", "what helps", "what helps with", "what can i do", "helps",
    "help", "helping", "what should i do", "any tips", "tips")

# A relaxer is a hair treatment, not a habit: "how do i relax my hair" now says "how do i" and
# "relax", which is exactly the shape of the worry ask, so the hair lines stand this card down.
SMALL_HABIT_EXTRA_AVOID["worry"] = SMALL_HABIT_EXTRA_AVOID.get("worry", ()) + (
    "hair", "hairs", "my hair", "relaxer", "relaxers", "relax my hair", "relaxing my hair",
    "beard", "braids",
    # Two shapes say a worry word and are not this card: how to raise it with a doctor, and
    # whether a symptom is worth worrying about. "how do i talk to my doctor about anxiety"
    # became the tip, and "how do i know if a headache is something to worry about" was answered
    # with it instead of the headache card.
    "doctor", "gp", "gp appointment", "appointment", "surgery", "nurse", "practice nurse",
    "headache", "headaches", "migraine", "symptom", "symptoms", "pain", "ache", "aches",
    "spot", "spots", "mole", "lump", "bleeding", "fever", "temperature", "test results",
    "scan", "x-ray", "results")

SMALL_HABIT_ASK = {"worry": WORRY_ASK}

# Forgetting is the speaker's own job or it is somebody else's memory, and the person named
# decides it. "my mum keeps forgetting things" and "my wife keeps forgetting things" were read as
# the errand row above ("Set the reminder the moment you think of it"), which is advice for the
# person doing the forgetting, not for the one watching it happen: the row's own key has "keeps
# forgetting" and "things", and the third person in the line was not asked. science.py's
# `parent-memory` answers that shape and says so in its own comment ("my wife keeps forgetting
# things" is one of the lines it was extended for), so this row stands down for it.
_ANOTHER_PERSONS_MEMORY = re.compile(
    r"\b(?:mum|mom|mother|dad|father|parent|parents|grandma|grandmother|grandad|grandfather|"
    r"gran|nan|nana|granny|wife|husband|partner|spouse|other half|mother in law|father in law|"
    r"aunt|auntie|uncle|brother|sister)\b[^.?!]{0,40}"
    r"\b(?:forgets?|forgetting|forgetful|forgot|keeps forgetting|repeats|repeating|confused|"
    r"confusion)\b")


def _the_errand_is_the_speakers_own(understood):
    """False when the forgetting is somebody else's, so `parent-memory` answers it instead.

    The job shape stays here: "my mum keeps forgetting to pay her bills" and "my brother keeps
    forgetting to ring me" name a task with "to", and that is what this card tells you how to
    remember, whoever ends up doing it.
    """
    said = str(understood.get("clean") or "").lower()
    if not _ANOTHER_PERSONS_MEMORY.search(said):
        return True
    return bool(re.search(r"\bto\b", said))


SMALL_HABIT_ENTRIES = [
    entry("stop-" + name, (keys, SMALL_HABIT_ASK.get(name, STOP_SMALL)), tip,
          avoid=NOT_A_SMALL_HABIT + THIRD_PARTY + FEEL_BAD
                + SMALL_HABIT_EXTRA_AVOID.get(name, ()), bias=1)
    for name, keys, tip in SMALL_HABITS
]


# The two habit questions that are not a habit in the list above: how long one takes, and how
# to lay a new one down. Both are keyed on the word "habit" or "routine" as well as their own
# question words, so a work break and a cooking instruction stay where they belong.
EXTRA_ENTRIES = [
    # "how long does it take to break a habit" was answered by the work break entry ("on a
    # shift longer than six hours..."), so the habit and the question both have to be there.
    entry("habit-time", (HABIT_WORDS, HABIT_TIME_WORDS),
          "About two months, not the three weeks people quote: in the study that measured it the "
          "median was 66 days, and the easy ones (a glass of water with breakfast) settled in a "
          "few weeks while the hard ones took most of a year. Missing one day made no difference "
          "to how long it took, so a slip is not a restart - the rule is never miss twice.",
          avoid=("work break", "shift", "rest between", "holiday", "annual leave", "routine "
                 "blood test", "morning routine for school",
                 # a routine with a clock on it is a different question: how long the gym takes
                 "gym", "gyms", "workout", "workouts", "exercise", "training", "run", "running",
                 "walk", "commute", "morning routine", "bedtime routine", "evening routine",
                 "school run",
                 # "i keep breaking my streak after a week" is not a duration question: the
                 # "week" in it is when the streak goes, and this row answered with how long a
                 # habit takes to settle ("About two months..."). The never-miss-twice row is
                 # the one for a streak that has just broken, so the phrases that say a break
                 # stand this row down. Phrases, not the bare word: "how long to build a streak"
                 # is still a duration question.
                 "breaking my streak", "broke my streak", "breaks my streak",
                 "keep breaking my streak", "streak keeps breaking", "losing my streak",
                 "lost my streak", "ruined my streak", "missed my streak", "keep breaking the",
                 "my streak", "the streak", "missed a day", "miss a day"),
          # the trigger entry sits on the same "habit" key with bias 2, and a duration question
          # wants the number rather than the method, so this one outweighs it.
          bias=3),

    # "how do i build a habit" was a shrug, and it is the other half of the same question.
    entry("habit-build", (HABIT_WORDS + ("something new", "something every day"),
                          ("build", "start", "make it stick", "make a habit", "make it a habit",
                           "form", "stick", "sticking", "keep up", "new", "begin",
                           "get into", "get back into", "every day", "daily")),
          "Attach it to something you already do every day - after the kettle boils, after you "
          "brush your teeth - because a new habit needs an old one to hang on. Make the first "
          "version almost too small to fail (one page, one glass, two minutes), keep it in the "
          "same place and time, and put a tick on a wall calendar: the streak is what carries it "
          "past the first fortnight, when the novelty has gone.",
          avoid=("work break", "shift", "holiday", "salary", "job", "interview", "pan",
                 "oven", "recipe", "sauce", "bake"),
          bias=1),
    # Retirement is a life change with a known shape, and nothing in the tree answered it: "is it
    # normal to feel lost after retiring", "how do i adjust to retirement", "what do people do
    # when they retire" and "does retirement feel strange at first" were every one of them a
    # search hedge on main. `pensions.py` is the age and the pot and `money.py` the number; this is
    # the year after work stops, which is a routine question and belongs beside the habit rows.
    entry("retired-and-at-a-loss",
          (("retire", "retires", "retiring", "retired", "retirement", "gave up work",
            "given up work", "stopped working", "no longer working", "finished work",
            "left work", "packed in work", "last day at work", "not working any more",
            "not working", "no work to go to", "stopped work", "given up work"),
           # the ask has to be about the change itself: the money questions below carry the word
           # "retire" too, and they have their own rows with the pot, the age and the access date.
           # a bare "feel" is left out: "im retired and i feel great" is small talk, and the chat
           # lane asks how the days are going, which is the right reply to it. Only the trouble
           # words and the questions come here.
           ("lost", "at a loss", "feel lost", "normal", "strange", "odd", "weird", "adjust",
            "adjusting", "get used to", "getting used to", "cope", "coping", "struggling",
            "what do i do", "what do people do", "what to do with myself", "know what to do",
            "what now", "bored", "boredom", "lonely", "loneliness", "miss", "missing",
            "structure", "routine", "purpose", "with myself", "nothing to do", "keep busy",
            "keep occupied", "how do i", "tips", "advice")),
          "That lost feeling is the usual thing and it has a shape: the first few months are the "
          "holiday, the flat part comes next, and by a year most people have a week they like "
          "again. What went with the job was not only the money - it was the diary, the reason to "
          "be up, and the people you saw without arranging it. So rebuild those three on purpose "
          "and small: one fixed thing a week that somebody expects you at (a class, a shift at a "
          "charity shop, a badminton game, a regular coffee), one reason to be dressed and out by "
          "nine on a weekday, and one afternoon a week that is properly yours. Say yes to the "
          "first invitation even when staying in is easier, because the invitations thin out when "
          "you stop going. If the mornings are still heavy all day after six months, mention it to "
          "the GP - low mood after a big change is common and treatable - but drift at the start "
          "is not a warning sign, it is the gap between one life and the next.",
          # the money questions about retirement are pensions.py's and money.py's, and a partner's
          # retirement is the relationship card's: only the person's own change belongs here
          avoid=("pension", "pensions", "state pension", "pot", "savings", "money", "afford",
                 "tax", "annuity", "drawdown", "lump sum", "ni", "national insurance",
                 "how much", "how many years", "when can i", "at 55", "at 60", "at 65", "at 66",
                 "at 67", "early retirement", "retire early", "my husband", "my wife",
                 "my partner", "my mum", "my dad", "my colleague", "my boss", "he ", "she ",
                 # a retirement party is a party with a guest list and a room, not the year
                 # after work stops: "how do i plan a retirement party" was this card until the
                 # party row was fenced this way, and the word "retirement" is the only one the
                 # two questions share.
                 "party", "parties", "retirement party", "leaving do", "leaving party",
                 "celebrate", "celebration", "send off", "guest list", "invitations",
                 "invite people", "venue", "catering", "speech", "toast", "present", "gift"),
          # the chat lane reads a big change on its own ("That is a big change. What does a normal
          # week look like now?"), and that line is warm but says nothing; this row has the shape
          # of the year and what to rebuild, so it has to outweigh it.
          bias=3,
          # "my oven has stopped working, what do i do" is the same words as a person's retirement
          # and a different question: the machine that stopped has the plug and the fuse, and this
          # card told a person with a broken oven that the first few months are the holiday. The
          # guard stands this row down when the thing that stopped is a thing, so `home_craft.py`'s
          # appliance rows answer it; a retirement or a job said by the person keeps this card.
          guard=lambda understood: not a_thing_has_stopped(understood)),

    # "how do i stop being late" and "im always late" reached nothing: the only lateness row is
    # about telling your boss, which is the other question. Keyed on the punctuality phrases so
    # a late parcel, a late train and a late period stay where they belong.
    entry("always-late", (("always late", "im always late", "i am always late",
                           "i'm always late", "stop being late", "keep being late",
                           "keeps being late", "never on time", "not on time", "punctual",
                           "timekeeping", "time keeping", "late again", "late for everything",
                           "late every day", "always rushing", "running out of time in the morning"),
                          ("how", "why", "stop", "help", "advice", "tips", "time", "morning",
                           "better", "fix", "always", "keep", "what", "should")),
          # Kept under the habits suite's 450-character bar, so the second half of each sentence
          # goes rather than the advice: the two anchors are timing one real journey and laying
          # the night before out, and the rest is dressing.
          "Lateness is nearly always the plan rather than the person: time one real journey at the "
          "hour you actually travel and add ten minutes, then set an alarm for leaving rather than "
          "only for waking. Lay out clothes, bag and keys the night before, and book the one "
          "earlier train instead of telling yourself you will hurry. If it is the last five "
          "minutes that keep going, drop the one job you do on the way out: being five minutes "
          "early costs nothing.",
          avoid=("parcel", "parcels", "delivery", "deliveries", "train", "trains", "bus", "buses",
                 "flight", "flights", "payment", "rent", "bill", "bills", "fee", "fees",
                 # "late again" is the row's own phrase and it belongs to any subject: "my pay
                 # is late again" and "my wages are late again" are money somebody owes, which
                 # is unpaid-wages' question, so the pay words stand this row down. The person
                 # being late is the only thing it answers.
                 "my pay", "our pay", "the pay", "wages", "wage", "salary", "payslip",
                 "payslips", "payday", "payroll", "pay packet", "paid me", "refund", "invoice",
                 "period", "periods", "pregnant", "baby", "midwife", "deadline", "tax return",
                 # "im always late for work" is the commonest way the line is said, and a bare
                 # "work" in this list turned it into the echo question while the card sat one
                 # word away. The boss lines stay fenced by their own phrases, which no lateness
                 # card should answer.
                 "boss", "manager", "interview", "school run", "night shift", "late for work?",
                 "sorry im late", "tell my boss", "what do i say"),
          bias=1),

    # Meditation is a habit people ask to start and to judge, and the bot had nothing for it:
    # "how do i start meditating" was a search hedge and "how do i learn to meditate" got the
    # study method ("test yourself instead of rereading"), which is the wrong practice entirely.
    # The words people use for it are the subject; how to start, how long before it works and
    # whether it is worth it are the same answer, so they share the row.
    entry("meditate-start",
          (("meditation", "meditate", "meditating", "meditates", "meditated", "mindfulness",
            "mindful", "breathing exercise", "breathing exercises", "headspace", "mbsr", "mbct",
            "guided meditation"),
           ("start", "begin", "learn", "how", "long", "often", "work", "works", "worth",
            "help", "helps", "better", "app", "apps", "beginners", "beginner", "every day",
            "daily", "routine", "habit", "should", "try", "anxiety", "anxious", "stress",
            "stressed", "calm", "panic", "relax"),
           # A mind that will not settle is the beginner's first complaint, and it is this
           # practice's own question, not the study card's: "how do i stop my mind wandering
           # when i meditate" was answered "put the phone in another room and work in 25-minute
           # blocks", which is about revising. It is a part of its own rather than more words in
           # the ask above, so that a line which names the practice and the wandering scores
           # above the study card, and a line that names only one of them still does not.
           ("wander", "wanders", "wandering", "wandered", "wandering mind", "mind wanders",
            "distracted", "distraction", "drift", "drifts", "drifting", "monkey mind")),
          "Five minutes sitting still with your attention on your breathing is the whole of it: "
          "the mind wanders, you notice and come back, and the coming back is the exercise, not a "
          "failure. Same time each day, for two weeks before you judge it. The eight-week "
          "courses, MBSR and MBCT, are the ones that have been tested, for low mood and for "
          "anxiety, and an app like Headspace teaches the same thing.",
          # A prayer, a yoga class and a breathing exercise for a cough are not this practice,
          # and a child's mindfulness is a different question from the reader's own.
          avoid=("pray", "prayer", "praying", "bible", "church", "yoga", "pilates",
                 "cough", "asthma", "inhaler", "peak flow", "baby", "toddler", "child",
                 "children", "kids", "kid", "school", "sleep", "insomnia"),
          bias=1),

    # "What is mindfulness" and "what is meditation" were both the search hedge, and a definition
    # is asked as often as "how do i start". The reply is the thing itself, then the myth that
    # stops people trying it (an empty mind), then the two courses the evidence is for.
    entry("meditation-what-it-is",
          (("meditation", "meditating", "meditate", "mindfulness", "mindful", "mbsr", "mbct"),
           ("what", "whats", "is", "are", "mean", "means", "meaning", "definition",
            "define", "explain", "explained", "difference", "different", "actually")),
          "Meditation is paying attention to one thing on purpose - usually the breath - and coming "
          "back to it each time you notice you have drifted; an empty mind is not the aim, and the "
          "noticing is the skill. The tested versions are the eight-week courses, MBSR and MBCT, "
          "mainly for low mood and anxiety.",
          # A prayer, a class and a breathing exercise for a cough are not this practice, and a
          # child's mindfulness is a different question from the reader's own.
          avoid=("pray", "prayer", "praying", "bible", "church", "yoga", "pilates",
                 "cough", "asthma", "inhaler", "peak flow", "baby", "toddler", "child",
                 "children", "kids", "kid", "school", "sleep", "insomnia"),
          bias=1),
] + SMALL_HABIT_ENTRIES

# A charge going up is spoken of with the same verb as a job being dragged out: "putting the rent
# up", "they keep putting prices up". These phrases name the charge, so the postponement card
# above never confuses the two.
_PUTTING_A_CHARGE_UP = (
    "putting the rent up", "putting my rent up", "putting our rent up", "putting up the rent",
    "putting up my rent", "puts the rent up", "puts my rent up", "put the rent up",
    "put my rent up", "rent going up", "rent went up", "rent keeps going up",
    "putting the price up", "putting prices up", "putting up the price", "putting up prices",
    "puts the price up", "puts prices up", "put the price up", "put prices up",
    "putting the price of", "putting up the price of",
    "putting the tax up", "putting taxes up", "putting up taxes", "putting the council tax up",
    "putting the fares up", "putting fares up", "putting up fares", "putting the bills up",
    "putting up the bills", "putting the charges up", "putting the fees up",
    "putting the rates up", "putting the cost up", "putting costs up",
)

ENTRIES = EXTRA_ENTRIES + [

    # Procrastination with no study word in it: "i keep putting things off" is about the start,
    # not about revision, so it gets the smallest-first-step answer rather than a timetable.
    entry("putting-things-off", (("procrastinat", "procrastinating", "putting off", "put off",
                                  "put things off", "put it off", "cant start", "can't start",
                                  "cannot start", "keep putting",
                                  # chat.py answers a bare "I keep <verb>ing" as a reflection
                                  # ("Is it the same every time, or does it vary?") and it sits
                                  # above the answer modules, so the bare procrastination lines
                                  # need the phrase that names the habit, not just the pattern
                                  "keep procrastinating", "keep putting off",
                                  "keep putting things off", "always putting things off",
                                  "procrastinate",
                                  # The same complaint said as a verdict on themselves rather
                                  # than as putting something off: "im lazy at work" was a "Got
                                  # it" and "i have no motivation at work" was said back as a
                                  # note. Nobody asks to be lazy; the line is about not being
                                  # able to start, which is this answer. Each phrase names the
                                  # not-starting, so no line reaches the row on "lazy" alone
                                  # ("my dog is lazy" is a pet and "a lazy sunday" is a day off).
                                  "lazy at work", "lazy at my job", "lazy with work",
                                  "lazy at home", "lazy at the moment", "lazy lately",
                                  "so lazy", "am lazy", "im lazy", "feeling lazy",
                                  # the place is in the phrase on purpose: a bare "no motivation"
                                  # also grabbed "i have no motivation for anything" and "i have
                                  # no motivation in life", which are the low-mood answer
                                  "no motivation at work", "no motivation at my job",
                                  "no motivation for work", "no motivation to work",
                                  "no motivation at home",
                                  "cant be bothered to start",
                                  "do nothing all day", "doing nothing all day",
                                  "get nothing done", "gets nothing done",
                                  "nothing gets done"),
                                 ("stop", "always", "constantly", "keep", "keeps", "everything",
                                  "anything", "stuck", "help", "how",
                                  # the place the not-starting happens is what makes it a work
                                  # line, and these are its names
                                  "at work", "work", "my job", "job", "office", "shift", "desk",
                                  "at home", "chores",
                                  "housework", "uni", "school", "revising", "the gym",
                                  # The shapes that name the habit with no question word at all:
                                  # "i must ring the dentist, ive been putting it off" was
                                  # "I'm listening", and "im putting off going to the doctors" was
                                  # the warm acknowledgement. The putting-off phrase is what these
                                  # lines have instead of "how", and it is a whole phrase so no
                                  # other line picks it up by accident.
                                  # Whole phrases, and none of them built on the bare word
                                  # `put`: `_forms()` reads a key `put` as `putting`, so a
                                  # phrase like "been putting off" also matched the passive
                                  # "the wedding has been put off until next year" and tried to
                                  # shrink someone else's postponement.
                                  "putting it off", "kept putting it off", "keeps putting it off",
                                  "putting off this", "putting off that", "putting off going",
                                  "putting off making", "putting off ringing",
                                  "putting off calling", "putting off booking")),
          "Shrink the job until it is almost silly: name the very next physical action — open the "
          "letter, put the shoes by the door — and do only that one, for five minutes, with "
          "permission to do it badly. Putting things off is usually about the task feeling too big "
          "to begin, and it stops the moment you are in it. Decide tonight what tomorrow's first "
          "step is, so it is an instruction rather than a choice.",
          # a line with a study word in it is the study entry's, and the exam lines want a plan
          avoid=("study", "studying", "revise", "revising", "revision", "homework", "essay",
                 "exam", "exams", "gcse", "a-level", "mocks", "uni", "university", "college",
                 "school", "coursework", "dissertation", "thesis", "assignment", "deadline",
                 # a school project that is being put off is family.school-project's line, and
                 # its key phrases are what separate it from the everyday putting-off question
                 "project due", "has a project", "project about", "project on", "school project",
                 "poster about",
                 # somebody putting a person down is not a task being put off, and "keep
                 # putting" was catching "my friend keeps putting me down"
                 "put me down", "puts me down", "putting me down", "put down",
                 # Somebody else being lazy is not this person's not-starting, and the answer
                 # here is addressed to the person who cannot begin. The lazy and
                 # nothing-done phrases took "my husband is lazy at home" and "my son is lazy
                 # at home" (both were an echo of the line), and the fair-shares card answers
                 # the wife's version, so a partner or a child stands this row down. Not the
                 # whole THIRD_PARTY list: "i keep putting off ringing my mum" is the everyday
                 # putting-off question and it names a person.
                 "husband", "wife", "partner", "boyfriend", "girlfriend", "fiance",
                 "fiancee", "son", "daughter", "child", "children", "teenager", "teen",
                 "flatmate", "housemate", "his share", "her share", "doesnt help", "doesn't help",
                 # a day with no edges is its own card: "i work from home and get nothing done"
                 # was this answer once the work words were in the key, and the working-from-home
                 # entry says the thing that is actually hard about it.
                 "work from home", "working from home", "wfh", "from home",
                 # "put up" is to raise and "put off" is to postpone, and the key above has the
                 # bare "keep putting", which read "my landlord keeps putting the rent up" as a
                 # task being avoided. The rise is the same shape for every charge, so the whole
                 # family is held out here and `money.rent-rise` answers it.
                 ) + _PUTTING_A_CHARGE_UP,
          # The card is about the writer forgetting their own jobs. When the person who forgets
          # is somebody else - "my mum keeps forgetting things", "my wife keeps forgetting where
          # she put things" - it is a question about that person's memory, and `science.parent-
          # memory` is the card that answers it. Both matched this row on "keeps forgetting" and
          # the errand card won on "things", so the memory question was told to set phone alarms.
          guard=_the_writer_is_the_one_forgetting),

    entry("quit-vaping", (("vaping", "vape", "vapes", "vaper", "e cigarette", "e cigarettes",
                           "e cig", "elf bar", "nic salt"),
                          STOP),
          "Staying on the vape beats going back to cigarettes, so if it is the only thing keeping you "
          "off tobacco, the win is not to stop. To come off it: drop the nicotine strength a step "
          "every two weeks, keep it out of sight rather than in your hand, and set a date "
          "instead of drifting down. The hand-to-mouth habit outlasts the nicotine, so keep a straw "
          "or gum where the vape used to live. Feeling low or snappy for a week is withdrawal, and "
          "it passes.",
          avoid=("coil", "coils", "battery", "charger", "shop", "cheapest", "price", "flavour",
                 "flavor", "illegal", "law", "underage", "ban") + THIRD_PARTY + FEEL_BAD),

    entry("cut-down-drinking", (("drinking", "drink", "alcohol", "beer", "wine", "booze",
                                 "units", "pint", "pints", "vodka", "whisky", "gin"),
                                STOP + ("less", "reduce", "reducing", "too much", "every day",
                                        "every night", "how much is too much",
                                        # A rate beside a drink is this question, not a buying
                                        # one and not a keeping one: "a bottle of wine a night is
                                        # that ok" was the open-bottle card ("an open bottle keeps
                                        # 3 to 5 days") and "she has a bottle of wine a night" was
                                        # the wine shelf's ("buy the shop's own-label bottle").
                                        # The words are safe here because the first group needs a
                                        # drink in the line.
                                        # Only the heavy rate, beside a drink in the line: a
                                        # bottle or a pint a night is the question this card
                                        # answers. A glass a day is the units card's - it gives
                                        # the number - so "a day" is deliberately not here.
                                        "a night", "every evening", "a bottle a night",
                                        "a bottle every night", "a pint a day", "each night")),
          "Write down what you really drink for a fortnight - most people are surprised - then take "
          "three drink-free days a week as the first change, since days off are easier than smaller "
          "measures. Alternate each drink with a glass of water, keep nothing in the house on the "
          "days you are off it, and tell one person you are doing it. If you drink every day and "
          "shake or sweat when you stop, see a GP first: coming off alcohol suddenly can be "
          "dangerous.",
          # "i spilled beer on my shirt" and a glass of water are not a drinking habit.
          avoid=("stain", "stains", "spill", "spilled", "spilt", "shirt", "sofa", "carpet",
                 "coffee", "tea", "water", "juice", "milk", "fizzy", "thirsty", "kebab",
                 # a drink with no alcohol in it is a thing to buy, not a habit to change: after
                 # "i quit drinking last year" the words "quit" and "beer" met in the window and
                 # "whats a good alcohol free beer" got the fortnight of drink-free days.
                 # and a person who has stopped saying they miss it is not asking how to count
                 # drinks: "i quit drinking last year" / "i miss a cold pint on a friday" came back
                 # with the fortnight of drink-free days.
                 "miss a", "miss the", "miss my", "missing a", "craving", "crave", "craves",
                 "alcohol free", "alcohol-free", "alcoholfree", "non alcoholic",
                 "non-alcoholic", "nonalcoholic", "zero alcohol", "booze free", "no alcohol",
                 # an energy drink is not a drinking habit: "how much energy drink is too much"
                 # was answered with the drink-free-days diary, because "drink" and "too much"
                 # are this row's own two words
                 "energy", "energy drink", "energy drinks", "red bull", "monster",
                 "relentless", "lucozade", "sports drink", "sports drinks", "protein shake",
                 "caffeine", "espresso", "cola", "coke",
                 "chocolate", "sauce", "recipe", "braised", "marinade",
                 # "is a glass of red wine a day good for you" asks about the benefit, and the
                 # units card answers it with the number
                 "good for you", "good for me", "healthy", "healthier", "benefit", "benefits",
                 # a hangover is a morning problem, not a habit to change
                 "hangover", "hungover", "drank too much", "last night", "so hard",
                 # an animal drinks too, and "is my dog drinking too much" is a thirst question,
                 # not a habit to change: without this the drink-free-days answer came back for
                 # a dog, and it outranks the pet answer because it keys the same two words.
                 "dog", "dogs", "puppy", "pup", "pups", "cat", "cats", "kitten", "kittens",
                 "pet", "pets", "vet",
                 # nor is any other animal: "my guinea pig has stopped drinking" was answered
                 # with the drink-free-days diary.
                 "rabbit", "rabbits", "bunny", "bunnies", "hamster", "hamsters", "guinea pig",
                 "guinea pigs", "gerbil", "gerbils", "rat", "rats", "hamster's", "chinchilla",
                 "ferret", "horse", "horses", "pony", "ponies", "kitten", "kittens",
                 "litter tray", "water bottle") + THIRD_PARTY + FEEL_BAD),
    # "how do i stop snacking at night" is not here: `nutrition.snacking-night` owns the evening
    # and its answer names the cause (a lunch that was too small) that a habit tip cannot, so this
    # branch had two entries for one line and this one lost every time it was asked.

    # Forgetting to *do* something is not forgetting what a page said, and it is not putting the
    # job off: the person wants the dentist rung. On main `e06365c` four asks of this shape went
    # three different wrong ways - "i keep forgetting to ring the dentist" and "how do i stop
    # forgetting errands" reached the note-taking card in `study.remember-reading` ("Read a
    # section, then close the book and say its three points out loud"), "i keep forgetting to pay
    # a bill" reached nothing at all, and "my landlord keeps putting the rent up" was read as
    # procrastination ("Shrink the job until it is almost silly") because "keeps putting" is a
    # phrase of `putting-things-off` above and a landlord putting the rent up is a rise, not a
    # postponement. This is the card for the first three; the fenced rows are held in their own
    # files.
    # "my husband is always on his phone" is the mirror of `routines.phone-distraction`: the
    # writer is not the one scrolling, so advice about their own notifications answers a
    # different question. On main `35321d86` these lines reached the children's limit card
    # ("Match the limit to the age"), which is advice for a parent about a child, and "my husband
    # is always on his phone" reached nothing at all.
    entry("their-phone-habit",
          (("phone", "phones", "his phone", "her phone", "their phone", "screens", "screen",
            "scrolling", "scroll", "instagram", "tiktok", "facebook", "social media", "tablet",
            "ipad", "youtube"),
           ("always on", "on his phone", "on her phone", "on their phone", "addicted", "glued to",
            "too much", "never puts", "wont put", "won't put", "cant put", "can't put", "all day",
            "all the time", "ignores me", "stuck on")),
          "Say the thing you miss rather than a number of minutes, because a limit argued about in "
          "the moment is a row about the phone and a request is something they can answer: \"I "
          "miss talking at dinner\" works where \"you are on that thing again\" does not. Ask for "
          "one phone-free slot a day, a meal is the easy one, and put your own phone face down for "
          "it, because a rule that covers both of you holds and one imposed on them does not. If "
          "the scrolling is new, or they seem flat as well as glued to it, the phone is the "
          "symptom and a chat about how they are is the better move.",
          ask=("how", "what", "any", "help", "should", "can i", "says", "told me", "wont",
               "won't", "always", "spends", "is on", "on his", "on her", "on their", "glued",
               "addicted", "never puts", "ignores me"),
          # a child's screens are the parent's question in family.screen-time, and a phone that
          # costs, breaks or dies is a technology question
          avoid=("kid", "kids", "child", "children", "toddler", "son", "daughter", "teen",
                 "teens", "teenager", "year old", "homework", "school", "screen time",
                 "contract", "bill", "tariff", "price", "cost", "upgrade", "battery", "charge",
                 "cracked", "repair", "replace", "lost", "stolen", "storage"),
          guard=screens_are_somebody_elses),
    entry("forgotten-errand",
          (("keep forgetting", "keeps forgetting", "keep forgetting to", "keeps forgetting to",
            "always forgetting", "i forget to", "forget to", "forgetting to", "forgot to",
            "keep missing", "stop forgetting", "keep forgetting about", "remember to do",
            "remember to"),
           # What is forgotten is a job, not a fact: an errand, an appointment or a date. The
           # words of the ask ("to", "do", "go") are here so the plainest shape - "i keep
           # forgetting to do things" - is answered, and the things that have their own cards
           # (a tablet, a drink of water, where the keys are) are held out below.
           ("to", "ring", "call", "phone", "book", "pay", "renew", "post", "send", "email",
            "collect", "pick up", "buy", "order", "do", "make", "take", "go", "appointment",
            "appointments", "dentist", "doctor", "gp", "optician", "bill", "bills",
            "errand", "errands", "job", "jobs", "chore", "chores",
            "renewal", "form", "parcel", "parcels", "things", "stuff", "shopping", "return",
            "returns")),
          "Set the reminder the moment you think of it, while the phone is in your hand: \"remind "
          "me to ring the dentist at nine tomorrow\" into Siri or Google, or an alarm labelled with "
          "the job. Anything with a date - dentist, MOT, renewal, a birthday - goes in the calendar "
          "now, with an alert the day before and a yearly repeat for birthdays. A job that takes "
          "under two minutes is quicker done than remembered, so do it there and then; for the "
          "rest, leave the note where you will trip over it - the door keys, the kettle, the front "
          "door.",
          ask=("how", "stop", "keep", "keeps", "always", "help", "better", "tips", "tip",
               "remind", "reminder", "reminders", "system"),
          # What was forgotten, when it has a card of its own, is that card's: a tablet, a drink
          # of water, where the keys went, a name, a password. Each of those rows already says
          # this one does not.
          avoid=("tablet", "tablets", "medication", "medicine", "pill", "pills", "prescription",
                 "water", "drink", "drinking", "where i put", "where i left", "where ive put",
                 "keys", "glasses", "wallet", "phone number", "password", "pin", "name of",
                 "names", "word", "spelling", "what i read", "book i", "reading", "revise",
                 "revision", "study", "exam", "exams", "coursework", "someone", "somebody",
                 "my ex", "grief", "died", "passed away", "birthday card", "present",
                 "gift",
                 # A birthday or an anniversary already has the better answer - the composer's
                 # card names the two-step reminder ("a day before and again that morning")
                 # and says why the date is never the part that slips - so a line about one
                 # keeps it rather than being read as a general errand.
                 "birthday", "birthdays", "anniversary", "anniversaries",
                 # A "why" is asking for the reason, not for the system: `why do i keep
                 # forgetting things` had the explanation of how memories fade and was being
                 # given the reminder card instead. The explanation rows keep their why lines.
                 "why", "what causes", "what makes", "is it normal"),
          # Two more lines this row would otherwise take: somebody else's forgetting (the
          # memory-assessment entry answers those, see _SOMEONE_ELSE_FORGETTING above), and the
          # speaker's own memory said with an age ("im 50 and keep forgetting things" asked for a
          # worry about getting older, not for a reminder to be set in the phone).
          guard=lambda reading: (_the_errand_is_the_speakers_own(reading)
                                 and not _someone_else_is_forgetting(reading)
                                 and not _my_own_memory_and_my_age(reading)))
]

ANSWERS = ("health",)
ENTRIES.append(entry(
    "a-worry-about-me",
    (("worrying about me", "worries about me", "worry about me", "worried about me",
      "anxious about me", "fussing about me", "fusses about me", "fussing over me",
      "stop worrying about me", "stop fussing about me",
      "my parents worry", "parents worrying", "my mum worries", "my mom worries",
      "my dad worries", "mum worrying", "mom worrying", "dad worrying", "they worry",
      "she worries", "he worries", "overprotective", "over protective", "smothering",
      "keeps checking on me", "keep checking on me", "always checking on me",
      "worries too much", "worry too much", "worrying too much",
      "worries about me all the time", "worrying about me all the time",
      "always worrying about me", "parents are overprotective", "overprotective parents",
      "controlling parents",
      # the ask gets said with the person in the middle of it
      "get my mum to stop worrying", "get my mom to stop worrying",
      "get my dad to stop worrying", "get my parents to stop worrying",
      "get her to stop worrying", "get him to stop worrying", "mum to stop worrying",
      "dad to stop worrying", "parents to stop worrying", "to stop worrying about me"),
     # The frame around it, said plainly. These are how the ask is put, not the subject, so the
     # subject above still has to be named: a "my dog worries when I leave" stays with the dog.
     ("how do i", "how can i", "what can i do", "what do i do", "stop", "help", "deal with",
      "get them to", "make them stop", "reassure", "calm", "tell them", "explain to them",
      "get her to", "get him to", "handle", "why does", "why do", "are", "always", "all the time",
      "every day", "constantly", "too much", "so much", "keeps", "keep")),
    "Give them a fact rather than a reassurance: \"I'll text you when I'm on the train\" works "
    "where \"don't worry\" does not, because a worry needs something to hold. Ask what exactly "
    "they are afraid of, answer that one thing once, and then stop explaining - saying it a "
    "second and third time is what teaches them the worry is worth asking about.",
    ask=("how", "what", "can", "should", "do", "i", "my", "help", "stop", "deal", "get",
         "make", "reassure", "calm", "tell", "explain", "to", "why", "they", "she", "he"),
    # A worrying pet, a worry about money and a symptom are all other cards: the subject here is
    # somebody else's worry about the person asking.
    avoid=("dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets", "horse", "rabbit",
           "baby", "toddler", "child", "children", "son", "daughter", "money", "rent", "bills",
           "debt", "doctor", "gp", "appointment", "headache", "symptom", "results", "exam",
           "exams", "revision", "interview", "wedding", "flight", "flying"),
    # "my mum worries about me all the time" was the "all the time" card, which keys the phrase
    # as a schedule; the worry is the subject here, so this row has to outscore it.
    bias=3))
