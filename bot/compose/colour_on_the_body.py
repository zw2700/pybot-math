"""A colour on a part of the person's own body, and a blush, are answered rather than filed.

"my back is red", "my neck is blotchy", "my face has gone bright red" are a person showing you
something. Every reading around them wants a shape of its own - a pain, an itch, a rash, a body
word the knowledge base knows - and a colour on its own is none of those, so the line fell to the
floor ("Got it. Is there anything you'd like a hand with?", "I'm listening — say more if it
helps."), which says nothing about the patch just mentioned. Some were worse than the floor: the
-ed catch-all read "red" as a past tense and answered "my arm is red" as an account of a nice day,
and "my ears went red" reached the laundry card.

Two readings, one module:

* a patch of colour on their own body gets what a patch like that usually is (contact or heat - a
  soap, a plant, sweat) and the one question that settles it: how long, and does it itch. Nothing
  is named as a diagnosis and no fact is invented; a pharmacist looks at the ones that spread or
  hurt.
* a face, cheek, neck or ear that goes red *in a moment* is a blush, not a patch. The advice for a
  patch - keep soap off it, let it settle - is about the wrong thing entirely for somebody telling
  you they go red when they talk to people, so it gets its own short answer and one question.

It stands down for a colour that is not on a body (the wash, a carpet, the sky), somebody else's
body (a child, a partner, the dog), a symptom word beside the colour ("red and itchy" has its own
question, and a red patch that is hot or spreading is the one to get looked at today), the inside
of a mouth or an eye, and a colour that already has a reading of its own (a yellow skin is
jaundice, a black nail is blood under it, a purple patch is a bruise).

Nothing else is claimed: `reply_for` returns None on every line this cannot read, so the line keeps
whatever answer it had.
"""
import re

# The colours that mean a patch which comes up and settles. Yellow, black and purple are left out
# on purpose - they are jaundice, blood under a nail and a bruise, and each has a reading of its
# own. "Mottled" is left out for the same reason: mottled skin is the cold and the circulation.
COLOUR = re.compile(r"\b(?:red|reddish|pink|pinkish|blotchy|blotches|flushed)\b")

# A colour that comes and goes on the face is a blush, in any tense: "my face goes red when i talk
# to people", "my face went red at work", "my ears went bright red". An intensifier sits between
# the verb and the colour more often than not, so it is allowed for.
BLUSH = re.compile(
    r"\b(?:blush\w*|"
    r"(?:face|cheeks?|neck|ears?)\b[^.!?]{0,24}?"
    r"\b(?:goes?|going|went|gone|turns?|turning|turned|gets?|getting|come up|came up)"
    r"\s+(?:(?:bright|very|all|so|quite|a bit|really|dead|properly)\s+)?red\b|"
    r"\b(?:red|redder|redden\w*)\b[^.!?]{0,30}?when(?:ever)? i (?:talk|speak|meet) to?\s?people)\b")
# "I could die of embarrassment" is a feeling with its own readers, not a face doing something, so
# an embarrassment word on its own is not a blush. The colour is what makes a blush a blush.

# A part of the person for the colour to be on.
BODY_PARTS = frozenset((
    "head", "face", "neck", "cheek", "cheeks", "forehead", "scalp", "ear", "ears", "nose",
    "chin", "jaw", "lip", "lips", "eyelid", "eyelids", "shoulder", "shoulders", "arm", "arms",
    "elbow", "elbows", "forearm", "forearms", "wrist", "wrists", "hand", "hands", "finger",
    "fingers", "thumb", "chest", "breast", "breasts", "back", "spine", "tummy", "belly", "waist",
    "hip", "hips", "thigh", "thighs", "knee", "knees", "shin", "shins", "calf", "calves",
    "ankle", "ankles", "foot", "feet", "toe", "toes", "heel", "heels", "skin", "torso",
    "underarm", "armpit", "armpits", "bum", "bottom", "crotch", "groin", "navel", "collarbone",
    "knuckle", "knuckles", "bottom",
))

# A colour said with one of these is a symptom, not a colour: "my back is red and itchy" wants the
# question about the itch, and "warm" and "hot" belong here because a red patch that is hot to the
# touch is the one a person needs told to get it looked at today.
ALSO_A_SYMPTOM = frozenset((
    "itch", "itchy", "itches", "itching", "sting", "stings", "stinging", "burning", "tingling",
    "throbbing", "weeping", "crusty", "flaky", "scaly", "peeling", "swollen", "swelling",
    "warm", "hot", "feverish", "fever", "temperature", "shivery", "shivering", "spreading",
    "spread", "painful", "hurts", "hurting", "sore",
    "pain", "tender", "bleeding", "bled", "blood", "ooze", "oozing", "pus",
    # a patch that is puffy or raw is an allergy or a burn, not the contact-or-heat patch answer
    "puffy", "puffiness", "puffed", "raw", "shaved", "shaving", "razor",
    # numbness or a colour that changes to white or blue is the circulation: white, then blue, then
    # red is Raynaud's, and "my fingers go numb and white then red" has a card of its own
    "numb", "numbness", "white", "blue", "tingly", "pins",
    # a line running up an arm or a leg is an infection on the move: "there is a red streak up my
    # arm" wants 111 today, not a cool tap and a wait
    "streak", "streaks", "track", "tracks",
))
# A red patch from heat or a chemical is a burn, and a burn wants cool running water for twenty
# minutes, not "keep perfumed things off it": "i spilled boiling water on my arm and its gone red"
# was answered as a patch before this fence (found by sweeping every deck line).
A_BURN = frozenset((
    "singed", "singe", "singeing", "boiling", "boiled", "scald", "scalds", "scalded", "steam",
    "steamed", "bleach", "bleached", "chemical", "acid", "oven", "hob", "iron", "ironed",
    "kettle", "frying", "oil", "bonfire", "barbecue", "bbq", "fire", "flare", "sparkler",
))

# The inside of a mouth is not skin, and an eye is not a patch of skin either: a red throat is a
# sore throat and a red eye wants a pharmacist's eye counter, not "don't scrub at it".
INSIDE = frozenset((
    "throat", "tonsil", "tonsils", "gum", "gums", "mouth", "tongue", "palate", "sinus",
    "stomach", "gullet", "uvula", "eye", "eyes", "eyeball", "eyesight", "vision",
))

# Not a body at all: a colour in the wash, on a carpet, in a glass, in the sky.
SOMEWHERE_ELSE = frozenset((
    "wine", "sock", "socks", "whites", "shirt", "shirts", "sheet", "sheets", "towel", "towels",
    "carpet", "rug", "stain", "stains", "wash", "washing", "laundry", "dye", "dyed", "paint",
    "painted", "ink", "pen", "marker", "fabric", "curtain", "curtains", "bedding", "sofa",
    "tablecloth", "wall", "walls", "urine", "pee", "dress", "jumper", "blouse", "shoe", "shoes",
    "bag", "phone", "screen", "light", "lights", "sky", "sunset", "car", "door", "window",
    "leaves", "tree", "flower", "flowers", "candle", "flag", "light", "traffic",
))

# Somebody else's body. A patch on a child is a carer's question and the children cards and the
# safety module own those lines: "my 2 year old has a rash around her mouth" is not a patch on the
# person typing. A person types "my sons arm is red" as often as "my son's arm", so the possessive
# is read off the letters.
SOMEONE_ELSE = frozenset((
    "he", "she", "him", "her", "his", "hers", "they", "them", "their", "mum", "dad", "son",
    "daughter", "child", "kid", "kids", "baby", "babies", "toddler", "boy", "girl", "husband",
    "wife", "partner", "nan", "gran", "friend", "mate", "dog", "cat", "puppy", "kitten", "pet",
    "mother", "mom", "father", "sister", "brother", "aunt", "uncle", "niece", "nephew", "cousin",
    "grandma", "grandad", "granny", "stepson", "stepdaughter", "flatmate", "housemate",
    "colleague", "childminder", "babysitter", "siblings", "sibling", "pup", "rabbit", "hamster",
))
PETS = frozenset(("dog", "cat", "puppy", "kitten", "pet", "rabbit", "hamster", "pup", "parrot",
                  "budgie", "guinea", "horse", "pony"))

# A thing that has its own reading: a mole, a bite, a burn and a tattoo are not a patch of colour
# that came up on its own, and each of them has an answer elsewhere.
NOT_A_PATCH = frozenset((
    "mole", "moles", "bite", "bites", "bitten", "burn", "burns", "burnt", "scald", "scalded",
    "sunburn", "sunburnt", "wound", "wounds", "cut", "cuts", "graze", "grazed", "scar", "scars",
    "bruise", "bruises", "bruised", "lump", "lumps", "spot", "spots", "pimple", "pimples",
    "hives", "tattoo", "tattoos", "blister", "blisters", "cyst", "abscess", "sore", "sores",
    "ulcer", "ulcers", "stitches", "dressing", "bandage", "cast", "plaster", "cream", "ointment",
))

PATCH_POOL = (
    "A patch that comes up like that is usually contact or heat - a new soap or washing powder, "
    "a plant, sweat in a warm room - and it fades in a few days without much doing. Keep perfumed "
    "things off it, don't scrub at it, and let a pharmacist look if it spreads or starts to hurt. "
    "If there is a fever with it, or the patch stays red under a glass pressed on it, get seen "
    "today. How long has it been there, and does it itch?",
    "Redness like that is usually contact or heat and it settles on its own in a few days. Plain "
    "water rather than soap, leave it uncovered, and show a pharmacist if it is no better by the "
    "weekend or it is spreading. A fever with it, or red that does not blanch under a glass, is a "
    "same-day call rather than a wait. When did you first notice it?",
    "That sounds like contact or heat: a soap, a plant, a fabric, sweat under a coat. Cool water "
    "and no cream until you know what it is, and a pharmacist if it is still there in a few days "
    "or it starts to hurt. With a fever, or if it stays red where you press a glass on it, get "
    "seen the same day. Is it in one place or spreading?",
    "Patches like that are usually contact or heat and they calm down in a few days. Wash it with "
    "plain water, keep anything perfumed off it, and have a pharmacist look if it spreads or gets "
    "sore. If you also feel feverish or shivery, or the colour stays put under a glass, that is a "
    "today job. Where is it, and has it changed since you first saw it?",
)
BLUSH_POOL = (
    "That is a blush rather than anything wrong: the vessels in the face open up for a moment and "
    "there is nothing to treat. It eases as you get used to the people in the room, and finding "
    "one friendly face to talk to helps more than trying to fight it. What sort of moment sets it "
    "off?",
    "Going red like that is a blush - your own body's alarm, and it fades in a minute or two. Most "
    "people read it as being interested rather than embarrassed. Is it situations with people you "
    "don't know, or does it happen with friends too?",
    "A blush is the face's own thermostat rather than a sign of anything wrong, and everybody has "
    "one. It helps to let it happen instead of fighting it - fighting it is what keeps it going. "
    "Does it bother you more at work or with people you know?",
)

WORD = re.compile(r"[a-z']+")


def _words(text):
    return WORD.findall(text.lower().replace("’", "'"))


def _last_reply(memory):
    """What the bot said on the turn before, if the store has it."""
    turns = (memory or {}).get("turns") or []
    for turn in reversed(turns):
        if isinstance(turn, dict) and turn.get("bot"):
            return " ".join(str(turn["bot"]).split())
    return ""


def _pick(pool, line, memory=None):
    """A wording for this line, never the whole of what the bot said last time.

    The arbiter passes over a candidate that only repeats the bot's previous reply, and the line
    after a patch is often another patch ("my neck is blotchy" then "my chest is red"): with one
    wording chosen by the line alone the second turn would repeat the first and the arbiter would
    hand the turn to whatever card the words matched - the wash card, for "i go bright red when i
    talk to people". So the wording steps on when it would be the last one said again.
    """
    if not pool:
        return ""
    start = sum(ord(letter) for letter in line.lower()) % len(pool)
    last = _last_reply(memory)
    for step in range(len(pool)):
        said = pool[(start + step) % len(pool)]
        if not last or " ".join(said.split()) not in last:
            return said
    return pool[start]


def _someone_elses(words):
    """True when the line says whose body it is and it is not the person typing.

    "my son's arm", "my sons arm" and "his arm" are all somebody else. The plural is read by
    dropping one trailing s, and only when what is left is a person word - "his" must not become
    "hi" and slip through, which is how "the skin under his belly is red" was answered as the
    person's own patch.
    """
    for word in words:
        if word in SOMEONE_ELSE or word in PETS:
            return True
        for suffix in ("'s", "'"):
            if word.endswith(suffix) and word[: -len(suffix)] in SOMEONE_ELSE | PETS:
                return True
        if word.endswith("s") and word[:-1] in SOMEONE_ELSE | PETS:
            return True
    return False


def _thread_names_a_pet(memory):
    """True when the last few turns were about an animal, whose skin is not the person's."""
    turns = (memory or {}).get("turns") or []
    seen = 0
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        said = (turn.get("user") or "").strip().lower()
        if not said:
            continue
        seen += 1
        if seen > 4:
            break
        if set(_words(said)) & PETS:
            return True
    return False


def reply_for(text, memory=None):
    """The answer to a colour on the person's own body or a blush, or None."""
    clean = " ".join((text or "").lower().replace("’", "'").split())
    if not clean:
        return None
    words = set(_words(clean))

    # A blush is a moment, not a patch, and it is the one shape that needs no body part in the
    # line: "i go bright red when i talk to people" is the same thing said without naming a face.
    if BLUSH.search(clean):
        # "why do we blush" is a question about people in general: the answer to it has no
        # business asking this person about their own moments.
        if clean.startswith("why") and not (words & {"i", "my", "me", "im", "myself"}):
            return None
        if words & SOMEWHERE_ELSE or words & INSIDE:
            return None
        if _someone_elses(words):
            return None
        return _pick(BLUSH_POOL, clean, memory)

    if COLOUR.search(clean) is None:
        return None
    if not (words & BODY_PARTS):
        return None
    if words & INSIDE:
        return None
    if words & SOMEWHERE_ELSE:
        return None
    if _someone_elses(words):
        return None
    if words & ALSO_A_SYMPTOM or words & NOT_A_PATCH or words & A_BURN:
        return None
    if _thread_names_a_pet(memory):
        return None
    return _pick(PATCH_POOL, clean, memory)
