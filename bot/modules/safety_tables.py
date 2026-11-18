"""The tables and helpers `bot/modules/safety.py` no longer holds inline.

Moved here whole, name by name, with the comment above each one and nothing changed: the
file had grown past the size the Hub will take. `safety_tables` imports every name back, so
`safety_tables.PLAN_ASKS` is the object it was and nothing that reads it can tell.
"""

import re
from .safety_cards import (
    ALLERGY_AIRWAY,
    ALLERGY_FACE,
    ALLERGY_FOOD,
    ALLERGY_OFF,
    BLEEDING_SMALL,
    BODY,
    BREATH_BARE,
    BURNT_BODY_VERB,
    BURN_ON_BODY,
    BURN_VERB,
    CRUSH,
    CRUSH_HARD,
    CRUSH_OFF,
    CUT_BODY_PART,
    CUT_ON_BODY,
    CUT_ON_THROAT_BODY,
    FOOD_WORDS,
    HEAT_BREATH_RED,
    HEAT_CAUSE,
    HEAT_NOT_WEATHER,
    HOT_COMFORT,
    HOT_SURFACE,
    HOT_WAX_ON_BODY,
    LAUGH_BREATH_RED,
    LAUGH_OTHER_PERSON,
    LAUGH_TAKES_BREATH,
    LAUGH_WORD,
    MINOR,
    NOT_A_PET_LINE,
    NOT_BURN_ON_BODY,
    PET_APPOSITIVE,
    PET_APPOSITIVE_SUB,
    PET_BREATH,
    PET_BREATH_NOW,
    PET_CANT_SETTLE,
    PET_EFFORT,
    PET_NAIL,
    PET_OWNS_THE_WOUND,
    PET_WOUND,
    RING_STUCK,
    SCORCHED_A_PERSON,
    SIGHT_EVER,
    SIGHT_LIFE_REPLIES,
    STING_WORDS,
    TOOTH_CHIPPED,
    TOOTH_OUT,
    WAX_BODY,
    WEIGHT_JOINT,
    _PET_APPOSITIVE,
    _PET_DAMAGE_THING,
)
from .safety_cards import (BITE_DONE, PERSON_HANGING, HEAD_OUT_COLD, STRUCK_NOT_NOW, SELF_HARM_HABIT, HEAL_TIME, HEAD_REPLIES, HUMAN_BITTEN, HIT_IN_FUN_HARD, WATER_DANGER, MILD, SCALD, HYPERBOLE_WISH, PURSUIT_PLACE_HOME, INJURY_HOW, LIPS_SWELL_BARE, DOG_ATTACK, HYPO_SIGN, SUGAR_READING_LOW, SELF_HARM_REPEAT_CAUSE, FOLLOW_UP, LIMP_ONGOING, SHOULD_I_CALL, NOT_JUST_A_NEAR_THING, LIMP_PERSON, PURSUIT_FINE, LIMB_IS_A_THING, COUNTERFACTUAL_WISH)
from .safety_phrases import (  # noqa: F401 - named so the undefined-name guard can see them
    ABUSE, ABUSER, ABUSE_DISCLOSURE,
    ABUSE_DISCLOSURE_FINE, ABUSE_FINE, ABUSE_HEAD_INTO,
    ABUSE_HIT_ME, ABUSE_MEMORY, ABUSE_NOW,
    ABUSE_PURSUIT_HARD, ABUSE_VERB, ABUSE_VERBAL,
    ABUSE_VERBAL_FINE, ABUSE_VERBAL_LABEL, ABUSE_VERBAL_MAD,
    ABUSE_VERBAL_PERSON, ABUSE_VERBAL_SUBJECT, ABUSE_VERB_PART,
    ASK_AFTER_ME, BLOW_THINGS, CHILD_AGGRESSOR,
    CHILD_HIT_NOW, CLOSE, DYING_OTHER,
    GAME_AFTER_ME, GAME_PLAYED, GAME_WORD_STOP,
    GAME_NOT_A_BLOW, GRIP_GAME, GRIP_GAME_FENCE, GRIP_NOT_AN_ASSAULT,
    GRIP_NOT_AN_ASSAULT_STR, HAS_ME_SUBJECT, HIT_AS_A_CHILD,
    HIT_BY_A_VEHICLE, HIT_THING_NOT_PERSON, I_DID_NOT_HIT,
    I_HIT_SOMEONE, MONEY_NAMED, NOT_A_FEAR,
    OTHERS, PARTNER_CLOSE, PEOPLE,
    PERSON, PLAY_FACE_REPLIES, PURSUIT,
    PURSUIT_FEAR, PURSUIT_LOUD, PURSUIT_OUTSIDE,
    PURSUIT_PLACE_WORK, PURSUIT_SUBJECT, PURSUIT_SUBJECT_EX,
    REMORSE_FOR_THE_ACT, SELF_HARM_NEEDS_PERSON, SELF_OWN_DYING,
    SOFT_FACE_PUSH, SOFT_FACE_STOP, SOMEONE_HOLDS_THE_MONEY,
    THREAT_COERCIVE, THREAT_SUBJECT, _NOT_A_THREAT,
    _REFUSED_EXIT, _THE_BLOW, _THE_HAND,
    _THE_ONE_HIT, _both_here,
)

# Who is hurt? "my mum ... cushion their head" reads badly, so the reply follows the person named.
FEMALE_WORDS = (r"\bm(?:u|o)m\b", r"\bmother\b", r"\bwife\b", r"\bgirlfriend\b", r"\bsister\b",
                r"\bdaughter\b", r"\blittle\s+girl\b", r"\bgirl\b", r"\baunt\b", r"\bnan\b",
                r"\bgran\b", r"\bgranny\b", r"\bgrandma\b", r"\bgrandmother\b", r"\bniece\b",
                r"\bshe\b", r"\bher\b")

# (what a reply says, what it says about one person). Order matters: long phrases first.
_AGREEMENT = (
    (r"\bthey\s+stop\b", "stop"), (r"\bthey\s+need\b", "need"), (r"\bthey\s+feel\b", "feel"),
    (r"\bthey\s+seem\b", "seem"), (r"\bthey\s+come\b", "come"), (r"\bthey\s+look\b", "look"),
    (r"\bthey\s+get\b", "get"), (r"\bthey\s+go\b", "go"), (r"\bthey\s+start\b", "start"),
    (r"\bthey\s+keep\b", "keep"), (r"\bthey\s+have\b", "have"), (r"\bthey\s+were\b", "were"),
    (r"\bthey\s+are\b", "are"), (r"\bthey\s+do\b", "do"),
)

# In these cases "they" is the person who is hurt. In the abuse and self-harm replies it is the
# helpline or the people around the user, so those keep their own words.
FIT_CASES = ("medical", "chest", "breathing", "breath_past", "unconscious", "seizure", "stroke", "bleeding",
             "drowning", "fire", "poison", "minor", "heat", "fall", "scald", "red_flags",
             "stiff_neck", "sepsis_signs", "newborn_fever", "hypo", "old_fall", "shot",
             "eye_chem", "bone_out", "headache", "cough_blood", "fall_hip", "lips_swell",
             "breath_rest", "pregnancy_bp", "pet_loss", "baby_fell", "baby_fell_red",
             "puncture", "appendix", "stuck_machine", "poo_blood", "torsion", "safety",
             "swallow_gone")

SWALLOWED_SELF = (
    "Ring 111 (or your local urgent line) today rather than waiting, and keep a spare of whatever it "
    "was to show them; don't make yourself sick. If you start coughing, drooling, or finding it hard "
    "to swallow or breathe, that is 999 or 911 straight away.",
    "Ring 111 (or your local urgent line) today with the packet or a spare in your hand, and don't "
    "make yourself sick or eat and drink for now. Coughing, drooling or trouble swallowing or "
    "breathing means 999 or 911 instead.",
)

# The objects that are a call whoever swallowed them: a battery burns, and a magnet or anything
# sharp or long blocks or tears. A line naming one gets the flat answer, not the conditional one,
# because there is no version of it that waits for a symptom. A bone is not in this set: a bone that
# went down is a same-day 111 call and only the airway signs make it 999, and main's
# `bone_throat` case already answers it.
# A stated dose is a count, and a count can be checked against the day's limit. On main only the
# question was answered - "how many paracetamol can i take" gives two 500mg tablets four times in
# 24 hours, eight a day - and every line that states the dose was a shrug: "i took 6 paracetamol
# today" got the hold, "i took 8 tablets of paracetamol today" got "I'm listening", and "take 4
# paracetamol" got "Thanks for telling me". Eight is not a guess: the packet's day's limit is what
# decides whether the answer is "stop there" or "ring 111 now", and paracetamol damage does not
# show in how the person feels, so the tone of the reply changes with the count rather than the
# count being ignored.
DOSE_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
              "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
              "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
              "nineteen": 19, "twenty": 20, r"a\s+couple": 2, r"half\s+a\s+dozen": 6,
              r"a\s+dozen": 12}

# "should i call an ambulance", asked with nothing in the line to judge. Somebody typing that is
# often looking at a person on the floor and does not know how to word the question a form wants,
# so the answer is the rule for when to call: ring and let them decide. Anything with a symptom in
# it is answered by its own card before this one is reached.
ASKS_IF_CALL = (
    r"\b(?:should|shall|do|does|would|must|need|is\s+it\s+worth)\s+(?:i|we|you|he|she|they)\b"
    r"[^.?!]{0,24}\b(?:call|ring|phone|dial|get)\s+(?:an?\s+|the\s+)?"
    r"(?:ambulance|999|911|112|a\s*&?\s*e|a\s*and\s*e|emergency\s+services|paramedics|"
    r"out\s+of\s+hours)\b",
    r"\b(?:do|does)\s+(?:i|we|he|she|they)\s+need\s+(?:an?\s+)?(?:ambulance|999|911|"
    r"a\s*&?\s*e|a\s+and\s+e|the\s+er|paramedics)\b",
    r"\bis\s+(?:this|that|it)\s+(?:an?\s+)?(?:emergency|999\s+call|ambulance\s+job)\b",
    r"\b(?:am|are|is)\s+(?:i|we|he|she|they)\s+(?:meant\s+to|supposed\s+to)\s+(?:call|ring)\b"
    r"[^.?!]{0,20}\b(?:999|911|ambulance)\b",
)

# A sign in the line means somebody else has already judged it: the chest, the breath and the
# bleeding cases each answer better than a rule of thumb, so this arm leaves them alone.
CALL_HAS_A_SIGN = (
    r"\bchest\b", r"\bbreath\w*", r"\bbleed\w*", r"\bunconscious\b", r"\bunresponsive\b",
    r"\b(?:fit|seizure|seized|fitting)\b", r"\bstroke\b", r"\bblue\b", r"\bswallow\w*",
    r"\boverdos\w*", r"\bpoison\w*", r"\bburn\w*", r"\bchoking\b", r"\bcollapsed\b",
    r"\bnot\s+waking\b", r"\b(?:pain|hurts?|hurting|ache\w*)\b", r"\bfever\b",
    r"\brash\b", r"\bvomit\w*", r"\bblood\b", r"\bfell\b", r"\bcut\b",
)

# Asking whether to go in, rather than whether to ring: the same rule of thumb, in the words for a
# waiting room. "should i take him to a&e" was a shrug on main.
ASKS_IF_GOING = (
    r"\b(?:should|shall|do|does|would|must|need|is\s+it\s+worth)\s+(?:i|we|you|he|she|they)\b"
    r"[^.?!]{0,24}\b(?:take|bring|get|drive|walk)\s+(?:\w+\s+){0,2}?(?:to|into)\s+"
    r"(?:a\s*&?\s*e|a\s*and\s*e|the\s+er|er|casualty|the\s+hospital|hospital|"
    r"the\s+emergency\s+room|out\s+of\s+hours)\b",
    r"\b(?:should|shall|do|does|would|must|need)\s+(?:i|we|you|he|she|they)\s+go\s+"
    r"(?:in|to|into)\s+(?:a\s*&?\s*e|a\s*and\s*e|the\s+hospital|hospital|the\s+er|er|"
    r"casualty|the\s+emergency\s+room|out\s+of\s+hours)\b",
)

ASK_GO_REPLIES = (
    "If it can't wait until the morning, take them in — A&E is for tonight's problems, and you "
    "don't need an ambulance to go. If you're not sure, ring 111 first and describe it.",
    "Go in if it can't wait for a GP appointment, and ring 111 if you're unsure which door to use. "
    "Take the medicine box with you and say what happened at the start of the story.",
)

# The cards that sent an ambulance. The A&E rule of thumb above ("you don't need an ambulance to
# go") talks a person down inside one: a chest card says ring 999, and the next line, "should i go
# to hospital", answered "you don't need an ambulance to go".
AMBULANCE_CASES = frozenset((
    "chest", "chest_slow", "stroke", "breathing", "not_breathing", "unconscious", "bleeding",
    "choking", "seizure", "overdose", "poison", "drowning", "hanging", "heat", "head_injury",
))

# "should i go in", "do i need to go to hospital": the same question, asking left out. Read only
# while a card is live.
ASKS_GO_BARE = (
    r"\bgo\s+in\b",
    r"\bgo\s+to\s+(?:a\s*&?\s*e|a\s*and\s*e|the\s+hospital|hospital|casualty|the\s+er|"
    r"the\s+emergency\s+room)\b",
)

# Going in to work the next morning is not the hospital question, card or no card.
GO_IN_NOT_ABOUT_IT = (
    r"\b(?:work|office|job|shift|school|college|uni(?:versity)?|nursery|childminder)\b",
)

# While an ambulance is coming the call is the way in, and the waiting advice follows it.
GO_IS_A_CALL = (
    "Going is the call, not a drive: ring 999 or 911 and say what is happening, and let them "
    "bring you in. ",
)

ASK_CALL_REPLIES = (
    "If you're asking, that usually means ring: 999 or 911 now if someone can't breathe, won't "
    "wake up, has chest pain or is bleeding heavily, and 111 or your GP today for anything less "
    "than that. Nobody minds you ringing and being wrong.",
    "When in doubt, ring them and say what you can see — 999 or 911 if it's someone's breathing or "
    "waking, 111 or your surgery for the rest. They would far rather take the call than miss one.",
    "Ring 999 or 911 if someone can't breathe, won't wake, has chest pain or is losing blood fast; "
    "111 or your GP today otherwise. Say what you're seeing out loud and let them sort the rest.",
)

SWALLOWED_BAD_REPLY = (
    "Ring 999 or 911 now: a battery, a magnet or anything sharp or long can burn or block within "
    "hours, however well you feel. Don't make them sick, don't give them food or drink, and have an "
    "identical one ready to name on the call.",
    "That is a 999 or 911 call now, not a wait-and-see: a battery burns, and a magnet or anything "
    "sharp or long can block or tear on its way through. Don't make them sick and don't "
    "give them anything to eat or drink; keep a spare of whatever it was to show the staff.",
)

SWALLOWED_BAD_SELF = (
    "Ring 999 or 911 now: a battery, a magnet or anything sharp or long can burn or block within "
    "hours, however well you feel. Don't make yourself sick and don't eat or drink anything; keep a "
    "spare of whatever it was to show the staff.",
    "That is a 999 or 911 call now, not a wait-and-see: a battery burns, and a magnet or anything "
    "sharp or long can block or tear on its way through. Don't make yourself sick, don't "
    "eat or drink anything, and take a spare of whatever it was with you.",
)

# The shape rule needs the first two letters right, and people type "siezure" with the vowels the
# wrong way round perhaps as often as "sezure". These are written out: the typos the shape cannot
# reach, pluralised, and nothing else.
TYPED_TYPOS = {"siezure": "seizure", "siezures": "seizures", "siesure": "seizure",
               "siesures": "seizures", "siezuring": "seizing", "siezed": "seized",
               # The vowel put in the wrong place in "breathe" is two slips from "breath" and
               # one from "breathe", which the shape rule cannot reach: "i cant braethe".
               "braethe": "breathe", "braethes": "breathes", "braething": "breathing",
               "braethed": "breathed", "breate": "breathe", "breatheing": "breathing",
               # The wish typed fast: the two letters of "kill" said as one, and the forms the
               # shape rule cannot reach because "k" is not the word's second letter ("kll").
               "kll": "kill", "klling": "killing", "k!ll": "kill", "k1ll": "kill",
               "k!lling": "killing", "k1lling": "killing"}

LOOKS_REAL = frozenset(
    "seize seized seizes seizing secure secured securer secures securely security securing"
    " securer security"
    # Real words the wider repair could reach: "the breadth of it" is not a breath, and a chess
    # question about cheating is not a chest.
    " breadth breadths cheat cheats cheated cheating cheater chests flop flops flopped flopping"
    # Real words one slip from "breathe": a wreath is not a lung, and a breather is a rest.
    " wreathe wreathes wreathed wreathing breather breathers breathable breathers"
    " floppy-disk choked chokes choking-hazard overdo overdos overdoes overdos overdid overdoing"
    " overdone flappy flippy".split())

# Fiction is always hypothetical, even when the injury is the user's own: "in my story i burn my
# hand" wants no first aid. It is kept apart from the rest of NOT_NOW, because a person who says
# "what do i do if i burn my hand" is asking about a real risk in their own kitchen.
NOT_NOW_FICTION = (
    r"\bfor\s+(?:a|my|the)\s+(?:story|novel|book|film|script|screenplay|essay|assignment|character)\b",
    r"\bin\s+(?:a|my|the)\s+(?:story|novel|book|film|game|dream)\b",
    r"\b(?:story|novel|script|screenplay|essay|film)\b.*\b(?:character|plot|scene)\b",
    r"\bmy\s+(?:character|protagonist)\b",
)

NOT_NOW = NOT_NOW_FICTION + (
    r"\bif\s+(?:someone|a\s+person|somebody|you|your\s+friend)\b",
    r"\bwhat\s+(?:do|should)\s+(?:you|i|we)\s+do\s+(?:if|when)\b",
    r"\bwhat\s+(?:if|would\s+happen\s+if)\b",
    r"\bhow\s+do\s+you\s+(?:help|treat|deal\s+with)\b",
    r"\bhow\s+(?:can|do|should)\s+(?:i|we|you)\s+(?:help|support|talk\s+to|deal\s+with|approach|comfort)\b",
    r"\bfirst\s+aid\s+(?:for|course|kit|training)\b",
    r"\b(?:qualified|trained|training|work(?:ing)?\s+as)\b.*\b(?:nurse|doctor|paramedic|lifeguard)\b",
    # Knowing what something looks like is not having it: "how do I know if someone is having a
    # stroke", "what are the signs of a stroke".
    r"\b(?:how|what)\b.{0,15}\b(?:know|tell|spot|recognise|recognize|signs?|symptoms?)\b",
    r"\bwhat\s+does\b.{0,25}\b(?:feel\s+like|look\s+like|mean|do\s+to\s+you)\b",
    r"\b(?:signs?|symptoms?|causes?|cause[sd]?|prevent\w*|reduce\s+the\s+risk)\b.{0,25}"
    r"\b(?:of\s+)?(?:a\s+)?(?:stroke|seizures?|choking|anaphyla\w*|asthma|hypo\w*|heart\s+attack)\b",
)

WORLD_QUESTION = (
    r"\bwhat\s+(?:causes?|are\s+the\s+causes?)\b", r"\bwhy\s+(?:do|does|would)\b",
    r"\b(?:symptoms?|signs?|treatment|rate|rates|statistics|study|research|awareness|prevention)\b",
    r"\bwhat\s+(?:is|are)\s+(?:the\s+)?(?:difference|best\s+way)\b",
    r"\bhow\s+(?:common|likely|dangerous|many|often)\b", r"\b(?:book|film|documentary|series|article)\s+about\b",
    # These two name the gas themselves: a general "is it dangerous?" would take the chest and
    # stroke questions away from their own reply, which is the reply those lines need.
    r"\bcarbon\s+monoxide\b.{0,30}\b(?:dangerous|kill\w*|harm\w*|fatal|safe)\b",
    r"\b(?:is|are|can|does|do)\b.{0,25}\b(?:carbon\s+monoxide|co\s+(?:alarm|detector|monitor))\b"
    r".{0,30}\b(?:dangerous|kill\w*|harm\w*|fatal|safe)\b",
)

# "i cut myself shaving", "i hurt myself at netball": the line says how it happened, so the cut
# or the knock is an accident and not a way of hurting yourself.
ACCIDENT = (
    # the chore or the game is named, so it was an accident: "i cut myself shaving"
    r"\b(?:cut|cutting|nicked|sliced|grazed|scraped|hurt|burn\w*|scalded|injured)\s+my\s*self\b"
    r".{0,24}\b(?:while\s+(?:shaving|chopping|cooking|slicing|peeling|grating|opening|washing|"
    r"cleaning|gardening|trimming|diy|cooking\s+dinner|making)|at\s+(?:work|netball|football|rugby|"
    r"hockey|school|the\s+gym|training|practice)|playing\s+(?:football|rugby|netball|hockey|"
    r"basketball|tennis|squash|badminton)|doing\s+(?:diy|the\s+gardening|the\s+decorating)|"
    r"accidentally|by\s+(?:accident|mistake)|on\s+accident)\b",
    r"\b(?:cut|cutting|nicked|sliced|grazed|scraped|hurt)\s+my\s*self\s+(?:again\s+)?"
    r"(?:shaving|chopping|cooking|slicing|peeling|grating|opening|washing|cleaning|gardening|"
    r"trimming|diy)\b",
    # "i cut myself on a tin", "i burnt myself with the kettle"
    # ...and the same thing said bare or with a word in between: "i cut myself on glass" and "i cut
    # myself badly on the broken glass" were the crisis card with no first aid at all, because the
    # article was doing the work of the sentence. The line still has to name the thing and say
    # "myself", so a blade and no cause keeps the card.
    r"\b(?:cut|cutting|nicked|sliced|grazed|scraped|hurt|burn\w*|scalded)\s+my\s*self"
    r"(?:\s+\w+){0,2}\s+(?:on|with)\s+(?:(?:a|an|the|some)\s+)?(?:\w+\s+){0,5}"
    r"(?:knife|glass|tin|can|blade|lid|grater|packet|jar|pan|"
    r"oven|kettle|saw|drill|branch|wire|needle|pin|scissors|hot\s+water|boiling\s+water)\b",
) + INJURY_HOW

# The words that make the same cut a habit rather than a pane: "i cut myself again on glass" is
# somebody who does it on purpose, and no cause word in the line may turn that into a dressing.
# `again` only counts straight after "myself": `i cut myself on the grater again` is a clumsy cook,
# while `i cut myself again on glass` is not. The reason a cut was made is the second list - the
# glass is the method, not the cause, when the line says what the cut was for.
SELF_HARM_AGAIN = (
    r"\bmyself\s+again\b",
    # "i cut myself on glass again" is the second time, and glass is nobody's chore: the tools a
    # clumsy cook cuts himself on (grater, tin, knife, oven shelf) are not in this list, so
    # `i cut myself on the grater again` stays a dressing.
    r"\b(?:cut|cutting|cuts|sliced|nicked|scratched)\s+my\s*self\b[^.?!]{0,30}"
    r"\b(?:glass|mirror|shards?|blade|razor)\b[^.?!]{0,8}\bagain\b",
)

# The word-level refusal: whatever the wording, the line still says the thought. The five pattern
# sets named above do not catch every phrasing - "and i dont want to exist", "and im better off
# dead", "and i dont see the point" reach the crisis card through the flanked-wish rules elsewhere
# in this file - so the stand-down also asks whether any word in the line can only be about dying.
# These are words that are not in a lonely line, and "plan" and "point" only in the shapes that
# make them that thought, so "i cut myself out of the plan for saturday" stays the phrasal verb.
CRISIS_WORD = re.compile(
    r"\b(?:dead|died|die|dying|death|kill|killing|suicide|suicidal|exist|existing|ending|"
    r"end\s+it|hopeless|worthless|burden|disappear|better\s+off|no\s+reason|give\s+up|"
    r"\bi\s+have\s+a\s+plan|see\s+the\s+point|what'?s\s+the\s+point|"
    # "after my attempt" is the disclosure itself, so the withdrawal after it keeps the card. An
    # attempt at a recipe is not one, so a trailing "at" stands that reading down.
    r"(?:my|the|his|her|their)\s+(?:last\s+|first\s+|second\s+|previous\s+|suicide\s+|own\s+)?"
    r"attempt\b(?!\s+at\b)|suicide\s+attempt|attempted\s+suicide|overdos\w*|"
    r"tried\s+to\s+(?:kill|end)\s+my\s*self)\b", re.I)

# A plan is often said without any of the words above it: "i know how i'd do it", "ive written the
# note", "i gave my things away", "i wont be around". These only count inside a line that has
# already said the crisis shape (the cut-off guard below), so the note, the things and the
# goodbye are read as what they are in that sentence and not as an errand.
CRISIS_PLAN_SAID = (
    r"\bi\s+know\s+how\s+i'?d\s+(?:do\s+it|end\s+it|go\b|be\s+done)\b",
    r"\b(?:i'?d|i\s+would)\s+know\s+(?:exactly\s+)?how\s+to\s+do\s+it\b",
    r"\bsuicide\s+note\b|\bgoodbye\s+letter\b",
    r"\b(?:wrote|written|writing)\s+(?:the|my)\s+note\b",
    r"\bthe\s+note\s+is\s+written\b",
    # Giving things away is the goodbye, unless the things went to a shop or a charity: that is a
    # clear-out the withdrawal was already about.
    r"\b(?:gave|giving|given)\s+(?:all\s+)?my\s+(?:\w+\s+)?(?:things|stuff|belongings|"
    r"possessions|clothes|books|records)\s+(?:all\s+)?away\b(?!\s+to\s+(?:a|the|my)?\s*"
    r"(?:charity|shops?|charity\s+shop|hospice|tip|car\s+boot|boot\s+sale|jumble\s+sale))",
    r"\b(?:said|saying|written)\s+(?:my\s+)?goodbyes?\b",
    # "and i wont be around" is the goodbye; "and i wont be around next week" is a diary.
    r"\bwon'?t\s+be\s+around\b(?!\s+(?:next|on|today|tomorrow|tonight|this|at|for|till|"
    r"until|before|during|in|friday|monday|tuesday|wednesday|thursday|saturday|sunday)\b)",
    r"\bnot\s+(?:be\s+)?around\s+(?:much\s+)?(?:longer|after\s+this)\b",
    r"\b(?:got|bought|have|saved)\s+(?:the|a)\s+(?:pills|tablets|rope|noose|razors?)\s+"
    r"(?:ready|sorted|saved|lined\s+up|in\s+my\s+(?:bag|pocket|drawer|room))\b",
    r"\btied\s+a\s+noose\b",
)

SELF_HARM_REASON = (
    # A wish said next to the cut is the reason for it: `i cut myself on glass and i want to keep
    # going` was the crisis card on main and no cause word in the line can make it a dressing.
    r"\b(?:want|wanna|need)\s+to\s+(?:keep\s+going|carry\s+on|go\s+on|give\s+up|end\s+it|"
    r"stop|disappear|not\s+be\s+here|die)\b",
    r"\b(?:on\s+purpose|deliberately|every\s+(?:day|night|week)|all\s+the\s+time|"
    r"to\s+cope|to\s+feel|to\s+punish|to\s+calm\s+down|to\s+hurt\s+my\s*self|"
    r"to\s+see\s+(?:the\s+)?blood|to\s+relieve|to\s+stop\s+the\s+noise|"
    r"to\s+feel\s+(?:something|anything|real|pain)|"
    r"when\s+(?:i|im|i'?m)\s+(?:get\s+|got\s+|am\s+|feel\s+)?"
    r"(?:overwhelmed|upset|anxious|stressed|panicky|low|angry|numb))\b",
)

# A third person's plan said with any verb - "my dad is going to end it with pills", "my mum
# feels like ending it with pills" - is their plan, and main answered the speaker as if it were the
# speaker's. The subject list is THIRD_PERSON_ACTOR's, so the shapes agree with the rest of the file.
END_MEANS_OTHER = (
    r"\b(?:he|she|they|my\s+(?:mum|mom|mother|dad|father|son|daughter|child|kid|brother|sister|"
    r"step\w+|husband|wife|partner|boyfriend|girlfriend|fella|ex|friend|mate|flatmate|housemate|"
    r"neighbou?r|colleague|boss|classmate|patient|client|lodger|aunt|auntie|uncle|cousin|nephew|"
    r"niece|gran|nana|nan|grandad|grandpa|grandson|granddaughter))\b[^.?!]{0,30}"
    r"\b(?:end(?:ing)?\s+(?:it|(?:his|her|their)\s+(?:own\s+)?life)|kill\s+(?:him|her|them)sel(?:f|ves)|"
    r"take\s+(?:his|her|their)\s+own\s+life)\b",
)

# "ending it with my dad" is a relationship ending, not a plan, and the same for a job or a
# friendship; the person need not be a partner, so family and friends are in the list too.
# The people, and the jobs and marriages, that an "end it with ..." is really ending. Named so the
# method reading below can ask the same question of what follows "with".
END_IT_WITH_NOUN = (
    r"(?:husband|wife|partner|boyfriend|girlfriend|fella|missus|fiance|fiancee|ex|marriage|"
    r"relationship|dad|mum|mom|father|mother|son|daughter|child|children|brother|sister|family|"
    r"parents|inlaws|in\s+laws|flatmate|housemate|tenant|colleague|mate|friend|friends|boss|job|"
    r"course)"
)

# "i deserve it" is said about a job, a holiday or a hard week, so the cue is a wish only when the
# line also says what the harm is: "i cut myself because i deserved it" is a wish, "i got a pay
# rise but i dont feel i deserve it" is not, and neither is the bare cue on its own.
SELF_HARM_DESERVE = (
    # main's cue, kept whole: "i deserve it" is on the card, and a false card is cheaper than a
    # missed disclosure. Only the negated forms stand down (see _deserve).
    r"\bdeserve[sd]?\s+(?:it|this|pain)\b",
    # "i deserve to hurt", "i deserve the pain": the harm is named, so it is not a job or a week.
    r"\bi\s+deserve[sd]?\s+(?:to\s+)?(?:hurt|suffer|die|be\s+in\s+pain|the\s+pain)\b",
)

# The wish said as an obligation or a shrug rather than as a want: "i should just end it", "i think
# i should die", "i might as well end it". Every shape in SELF_HARM is a wanting or a planning, so
# these were answered with "I'm listening - say more if it helps", which is the one reply a person
# saying that must not get. The modal is the obligation; the harm after it is either unambiguous
# (die, kill myself, end my life, not be here) or the bare "end it"/"end things" said and then
# left alone, because an "end it" with a partner or a reason behind it is a marriage, a job or a
# phone call: "i should end it with him", "i should end it before it gets worse".
WISH_BY_MODAL = (
    r"\bi\s+(?:should|ought\s+to|might\s+as\s+well|may\s+as\s+well)\s+"
    r"(?:just\s+|probably\s+|really\s+|honestly\s+|seriously\s+)?"
    # "i should die my hair purple" is the dye, not the wish, and "i should die laughing" is the
    # joke: both name what the dying is about, so the word after "die" stands them down.
    # "i should be dead after that run" is the workout talking, and "i should disappear for a bit"
    # is wanting an afternoon off, so the cause phrase stands the first down and the second is not
    # in the list at all.
    r"(?:die\b(?!\s+(?:my|the|it|them|her|his|your|laughing|of\s+laugh(?:ing|ter))\b)|"
    r"be\s+dead\b(?!\s+(?:after|following)\b)|"
    # "i should not be here, i should be at work" is somebody in the wrong place, not somebody at
    # the end: when the line goes on to say where they should be, the "here" is a room. The
    # exception is a place that is death itself, so "i should not be here i should be dead" and
    # "... i should be gone by 6" keep the card (peach-hammer on #2581).
    r"kill\s+my\s*self\b|end\s+my(?:\s+own)?\s+life\b|"
    r"not\s+be\s+here\b(?!\s*[^.?!]{0,40}\bshould\s+be\s+(?!dead|gone))|"
    # "i should be gone by 6" is a bus, not a wish.
    r"be\s+gone\b(?!\s+(?:by|before)\b))",
    # "i should just end it" with the line stopping there, or saying when. The end of the line is
    # what makes the "it" the speaker's life rather than a thing they can name.
    r"\bi\s+(?:should|ought\s+to|might\s+as\s+well|may\s+as\s+well)\s+(?:\w+\s+){0,2}end\s+"
    r"(?:it|things)\s*(?:[.?!]|$|tonight\b|now\b|for\s+good\b)",
)

# A wish with no verb of ending and no harm named: "im tired of living", "ive had enough of life".
# Main answered that whole family with the reply for a bad day at work - "Annoying. Walk it off for
# ten minutes before you reply." - because nothing in it says the harm, only the tiredness of it.
# A word after "living" or "life" is what the sentence is about, so "tired of living alone", "tired
# of living out of a suitcase" and "sick of living a lie" keep their ordinary answer. Two kinds of
# tail are not a place or an arrangement, though, and they say the wish more plainly than the bare
# phrase: a tail that adds nothing ("at all", "any more", "tbh"), and a tail that says how the
# living is going or who it is for - "tired of living like this", "living this way", "living this
# life", "living like a prisoner", "living for other people", "living my life for others". Cream-eel
# found the second kind (msg 55602): those seven were the card on base and my tail rule made them
# ordinary, and "tired of living like this" is somebody saying the days are unbearable, not somebody
# naming where they live.
_FLAT_WISH_HOW = (
    r"|like\s+(?:this|that|a\s+(?:prisoner|slave|dog|zombie|captive))"
    r"|(?:this|that)\s+way"
    r"|(?:this|my)\s+life"
    r"|(?:my\s+)?life\s+for\s+(?:others|other\s+people|everyone\s+else|everybody\s+else)"
    r"|for\s+(?:other\s+people|others|everyone\s+else|everybody\s+else)"
)

END_THING = (
    r"\b(?:end(?:ing)?|close|closing|finish(?:ing)?|wrap(?:ping)?\s+up)\b"
    r"[^.?!]{0,24}\b(?:this|that|the|my|an?)\s+(?:email|e-mail|letter|report|essay|list|form|"
    r"filing|tax\s+return|argument|row|draft|chapter|book|project|job|task|sentence|code|story|"
    r"application|coursework)\b",
    r"\b(?:this|that|the|my|an?)\s+(?:email|e-mail|letter|report|essay|list|form|filing|"
    r"tax\s+return|argument|row|draft|chapter|book|project|job|task|sentence|code|story|"
    r"application|coursework)\b[^.?!]{0,24}\b(?:end(?:ing)?|close|closing|finish(?:ing)?)\b",
)

# Giving up says the wish, and a negated giving up says the opposite: "i cant give up on life",
# "i wont give up on life", "dont give up on life", "you shouldnt give up on life" and "i never
# gave up on life" are all somebody still holding on, and every one of them reached the crisis
# card on the giving-up arm. The negator has to sit on the verb, so "i cant go on, i give up on
# life" keeps the card - the second half is the wish and the "cant" is about something else.
GIVING_UP_HELD_ON = (
    r"\b(?:can'?t|cannot|can\s+not|won'?t|will\s+not|don'?t|do\s+not|didn'?t|did\s+not|"
    r"doesn'?t|does\s+not|shouldn'?t|should\s+not|mustn'?t|must\s+not|wouldn'?t|would\s+not|"
    r"never|not|no\s+longer)\s+(?:ever\s+)?"
    r"(?:giv(?:e|es|ing)|gave|giv(?:en))\s+up\b",
)

# "on purpose" says how, not what: "i parked on purpose" and "i made myself a sandwich" are not
# about a person being harmed. The deliberate branch needs a harm done to the speaker in the same
# line, so an ordinary choice with those words keeps its ordinary answer.
# "on purpose" says how the thing was done, so the act itself has to be in the line too. These
# are the ways people name a harm done to themselves, not a list of every verb: a harm word with
# myself / me / a body part, an act that is only ever done to yourself (made myself sick, took
# pills), and a place or a thing that only makes sense as a way of dying. The ordinary completions
# of the same framing words - "made myself a sandwich", "parked on purpose" - have no such act.
# Not eating is starving whatever the word for it is, but only when no object follows: "i stopped
# eating meat on purpose" is a choice about a food, not a way of starving. The contracted and
# continuous forms are the same act: "i havent eaten in days on purpose", "i havent been eating",
# "i havent eaten properly in a week".
SELF_HARM_NOT_EATING = (
    r"\b(?:stopped|stop|quit|not|haven'?t|hasn'?t|hadn'?t|didn'?t|have\s+not|has\s+not|"
    r"had\s+not|did\s+not)\s+(?:been\s+)?(?:eating|drinking|eaten|ate|eat|drink|drunk)\b"
    r"(?=\s*(?:$|"
    r"[.,!?;]|on\s+purpose|deliberately|again\b|anymore\b|at\s+all\b|properly\b|much\b|"
    r"for\b|in\s+(?:days|weeks|a\s+week|a\s+while)\b|since\b))",
    r"\b(?:haven'?t|hasn'?t|hadn'?t|have\s+not|has\s+not|had\s+not)\s+(?:eaten|had)\s+"
    r"(?:anything|much)\b(?=(?:\s+to\s+(?:eat|drink))?\s*(?:$|[.,!?;]|on\s+purpose|"
    r"deliberately|in\s+days\b|for\s+days\b|all\s+day\b|today\b))",
    r"\bbarely\s+(?:eaten|eating|eat|ate|drunk|drinking|drink)\b",
    # The same act as a choice about food: eating nothing, skipping meals, going without, refusing
    # food. The framing word still has to be in the line, so "i skipped lunch" stays ordinary.
    r"\b(?:ate|eat|eating)\s+nothing\b"
    r"(?=\s*(?:[.,!?;]|$|on\s+purpose|deliberately))",
    r"\b(?:skip|skipped|skipping)\s+(?:a\s+meal|meals|food)\b"
    r"(?=\s*(?:[.,!?;]|$|on\s+purpose|deliberately))",
    r"\b(?:went|go|going|gone)\s+without\s+(?:food|eating)\b"
    r"(?=\s*(?:[.,!?;]|$|on\s+purpose|deliberately))",
    r"\brefused\s+(?:food|to\s+eat)\b"
    r"(?=\s*(?:[.,!?;]|$|on\s+purpose|deliberately))",
)

SELF_HARM_DELIBERATE_ACT = (
    # A harm verb with the person as its object: "cut myself", "stabbed myself", "hurt my back",
    # "gave myself a black eye".
    r"\b(?:hurt|hurting|cut|cutting|burn|burnt|burned|burning|scald|scalded|scalding|"
    r"bruise|bruised|bruising|starve|starved|starving|scratch|scratched|scratching|"
    r"hit|hitting|bang|banged|banging|harm|harmed|harming|poison|poisoned|poisoning|"
    r"smash|smashed|smashing|bite|biting|bit|bitten|break|breaks|broke|broken|breaking|"
    r"punish|punished|punishing|stab|stabbed|stabbing|slit|slitting|slash|slashed|"
    r"punch|punched|punching|choke|choked|choking|strangle|strangled|strangling|"
    r"suffocate|suffocated|suffocating|smother|smothered|smothering|wound|wounded|wounding|"
    r"electrocute|electrocuted|electrocuting|slice|sliced|slicing|"
    r"hang|hanged|hanging|hung|drown|drowned|drowning)"
    r"\b[^.?!]{0,24}"
    r"\b(?:my\s*self|me|my\s+(?:own\s+)?(?:arm|arms|wrist|wrists|leg|legs|thigh|thighs|stomach|"
    r"belly|head|hand|hands|finger|fingers|skin|face|eye|eyes|neck|throat|mouth|tongue|jaw|"
    r"lip|lips|ear|ears|nose|cheek|cheeks|forehead|temple|temples|back|shoulder|shoulders|"
    r"rib|ribs|knee|knees|foot|feet|ankle|ankles|hip|hips|chest|body|abdomen|waist|spine|"
    r"bone|bones|vein|veins|groin))\b",
    r"\bgave\s+my\s*self\s+(?:a\s+)?(?:black\s+eye|black\s+eyes|bruise|burn|cut|gash)\b",
    # "shot myself", but not "shot a photo of myself": the object after the verb has to be the
    # speaker, not the camera.
    r"\b(?:shoot|shoots|shooting|shot)\s+(?:my\s*self|me|my\s+(?:own\s+)?(?:arm|arms|leg|legs|thigh|"
    r"thighs|stomach|belly|head|hand|hands|chest|body|foot|feet|neck|mouth|face))\b",
    # Fire and fuel need their own wording: "set myself on fire" is not a harm verb with an
    # object, and "set my sleeve on fire" names no body part at all.
    r"\b(?:set|setting)\s+(?:my\s*self|me|my\s+(?:own\s+)?(?:arm|arms|leg|legs|hand|hands|clothes|"
    r"clothing|shirt|shirts|trousers|jumper|jumpers|coat|hoodie|sleeve|sleeves|body))\s+"
    r"(?:on\s+fire|alight|ablaze)\b",
    r"\bset\s+fire\s+to\s+(?:my\s*self|me|my\s+(?:arm|arms|leg|legs|hand|hands|clothes|"
    r"clothing|shirt|shirts|trousers|jumper|jumpers|coat|hoodie|sleeve|sleeves|body))\b",
    r"\bpoured\s+(?:petrol|gasoline|fuel|lighter\s+fluid|white\s+spirit)\s+(?:on|over)\s+"
    r"(?:my\s*self|me|my\s+(?:arm|arms|leg|legs|hand|hands|clothes|clothing|shirt|shirts|"
    r"trousers|jumper|jumpers|coat|hoodie|sleeve|sleeves|body))\b",
    r"\b(?:made|make|making)\s+my\s*self\s+(?:sick|throw\s+up|vomit|pass\s+out|bleed)\b",
    # The harm verb with nothing after it, the framing word straight after the verb: "i cut on
    # purpose", "i starved on purpose". A noun between the verb and the framing word keeps the
    # ordinary line: "i cut the cake on purpose", "i burnt the toast on purpose".
    r"\b(?:cut|cutting|cut\s+up|burn|burnt|burned|burning|hurt|hurting|starve|starved|starving|"
    r"bleed|bleeding|overdose|overdosed)\b(?:\s+(?:too\s+)?(?:deep|deeper|badly))?\s+"
    r"(?:on\s+purpose|deliberately)\b",
    *SELF_HARM_NOT_EATING,
    # Taking the month's tablets at once, or something not meant to be swallowed, is the act:
    # "took my pills on purpose", "swallowed pills", "drank bleach". Without the framing words
    # "i took my pills this morning" is an ordinary prescription line and never reaches here.
    r"\b(?:took|take|taking|taken|had|have|having|swallowed|swallow|swallowing|downed|"
    r"downing|popped|popping|necked|drank|drink|drinking|drunk|ate|eat|eating|eaten)\s+"
    r"(?:(?:too\s+many|some|the|those|these|my|his|her|their|a|an|every|"
    r"all(?:\s+(?:my|his|her|their|the|these|those))?)\s+)?(?:pills?|tablets?|paracetamol|"
    r"ibuprofen|painkillers?|meds|medicines?|sleeping\s+pills?|antidepressants?|"
    r"tranquill?i[sz]ers?|insulin|bleach|detergent|disinfectant|antifreeze|weed\s?killer|"
    r"hand\s+saniti[sz]er|paint\s?thinner|white\s+spirit|drain\s+cleaner|"
    r"cleaning\s+products?|cleaning\s+fluid)\b",
    r"\boverdos(?:e|ed|ing)\b",
    # A handful of hair, a head held under water, or a body thrown down the stairs is the act
    # even though the harm verb has no body word after it.
    r"\b(?:pull|pulled|pulling)\s+my\s+(?:own\s+)?hair\s+out\b",
    r"\b(?:held|hold|holding)\s+my\s+(?:own\s+)?head\s+under\s+(?:the\s+)?water\b",
    r"\b(?:put|puts|putting|place|placed|placing)\s+my\s+(?:own\s+)?"
    r"(?:hand|hands|arm|arms|finger|fingers|foot|feet)\s+(?:in|into|on)\s+"
    r"(?:the\s+)?(?:fire|flames|boiling\s+water|hot\s+water|stove|hob)\b",
    r"\b(?:crash|crashed|crashing)\s+(?:my|the|our)\s+(?:car|van|motorbike|truck)\b",
    r"\b(?:threw|throw|throwing)\s+my\s*self\s+(?:down\s+(?:the\s+)?stairs|"
    r"under\s+(?:a|the)\s+bus)\b",
    # The place or the traffic is the act: nobody jumps off a bridge on purpose to get somewhere.
    r"\b(?:jump(?:ed|ing|s)?|fell|falling|(?:throw|threw|throwing)\s+my\s*self)\b[^.?!]{0,10}"
    r"\b(?:off|from)\s+(?:a|the|this)\s+(?:bridge|roof|building|cliff|balcony|ledge|car\s*park)\b",
    r"\b(?:ran|run|running|walked|walk|walking|stepped|step|stepping|darted|dart|stood|stand|"
    r"standing|lay|lying|lie)\s+(?:into|in\s+front\s+of)\s+(?:traffic|a\s+bus|a\s+train|"
    r"a\s+car|a\s+lorry|a\s+truck)\b",
    r"\b(?:stood|stand|standing|lay|lying|lie|sat|sit|sitting)\s+on\s+(?:the\s+tracks|"
    r"the\s+track|the\s+railway\s+line|a\s+train\s+track|the\s+line)\b",
    # A blade named as the thing used on the speaker: "i used a knife on myself".
    r"\b(?:used|use|using|took|take|taking|held|holding)\s+(?:a|the|my)\s+"
    r"(?:knife|razor|blade|scissors|piece\s+of\s+glass|glass)\s+(?:on|to|against)\s+"
    r"(?:my\s*self|me|my\s+(?:arm|arms|wrist|wrists|leg|legs|thigh|thighs|stomach|belly|"
    r"head|hand|hands|finger|fingers|skin|face|eye|eyes|neck|back|shoulder|shoulders|rib|ribs|"
    r"knee|knees|foot|feet|ankle|ankles|hip|hips|chest|body))\b",
)

# The figure of speech stands down for a state, a dull job or a sore foot, and not for a line that
# also names a loss: "my mum died in march and i wish i was dead" is the wish whatever else is in
# the sentence, so a grief or abuse word in the line keeps the card.
HYPERBOLE_BLOCK = (
    # A person, a marriage or their own life is never the dull thing in a figure of speech,
    # whatever adjective is on it: "my life is so bad i wish i was dead", "my husband is awful
    # i wish i was dead" and "everything is so awful i wish i was dead" are the wish.
    r"\b(?:my|his|her|their|our|the)\s+(?:whole\s+)?(?:life|marriage|relationship|family|"
    r"husband|wife|partner|boyfriend|girlfriend|fianc\w+|mum|mom|mother|dad|father|son|"
    r"daughter|child|children|kids?|baby|brother|sister|boss|manager|health|mind|sanity)\b",
    r"\beverything\b", r"\bnothing\b",
    r"\bno\s+point\b", r"\bworthless\b", r"\bhopeless\b", r"\bunbearable\b",
    r"\b(?:died|death|funeral|buried|passed\s+away|lost\s+my|left\s+me|walked\s+out|"
    r"divorce\w*|separation|abuse\w*|hits?\s+me|cancer|tumour|tumor|diagnosis|miscarriage|"
    r"stillborn|overdose\w*|relapse\w*|evicted|homeless|bankrupt)\b",
)

# The hopeless phrases whose owner the line names. Each is one clause, so the subject can be
# required in front of it: "cant go on", "there is no point", "nothing will ever get better".
SOMEONE_ELSES_DESPAIR = (
    r"(?:can'?t|cannot|can\s+not)\s+go\s+on\b",
    r"(?:there'?s|there\s+is)\s+no\s+point\b",
    r"\bno\s+point\s+(?:in\s+)?(?:anything|going\s+on|carrying\s+on|anymore)\b",
    r"\bno\s+way\s+out\b",
    r"\b(?:is|are|feels?)\s+hopeless\b",
    r"\b(?:tired|sick)\s+of\s+(?:everything|it\s+all|life|living)\b",
    r"\b(?:wants?|wanted)\s+to\s+(?:die|end\s+it)\b",
    r"\b(?:doesn'?t|does\s+not|don'?t|do\s+not)\s+want\s+to\s+(?:be\s+here|live|go\s+on|wake\s+up)\b",
)

# "my chest hurts after the gym, is that normal?" is a training question, so it is not 999 unless
# a heart-attack sign is in the line as well.
AFTER_EXERCISE = (
    r"\b(?:after|following|post)[-\s]+(?:[a-z]+\s+){0,2}(?:gym|workout|work\s?out|run|running|jog|jogging|"
    r"exercise|exercising|training|session|swim|swimming|cycle|ride|football|rugby|netball|basketball|"
    r"tennis|hockey|lifting|weights|spinning|hiit|class|match|game|climb|climbing|rowing|cardio|"
    r"walk|walking|hike|hiking|steps|mile|miles|5k|10k|stairs)\b",
    r"\b(?:at|in)\s+the\s+gym\b",
    # "chest pain when I climb the stairs", "i get chest pain when i exercise": the same
    # exertion, said as the trigger rather than as the thing it came after.
    r"\bwhen\s+(?:i\s+|im\s+|i'm\s+)?(?:go\s+|am\s+|start\s+)?(?:running|jogging|walking|climbing|"
    r"cycling|swimming|exercising|training|lifting|playing|rowing|hiking|shovelling|shoveling)\b",
    r"\bwhen\s+i\s+(?:run|jog|walk|climb|cycle|swim|exercise|train|play|lift|row|hike|shovel|shine)\b",
    r"\b(?:on|up)\s+the\s+stairs\b",
    # "my chest hurts walking up the hill" - the exertion is the activity, with no "when".
    r"\b(?:walking|running|jogging|climbing|cycling|swimming|lifting|exercising)\s+"
    r"(?:up|uphill|fast|hard|home|the\s+(?:hill|stairs))\b",
)

# Chest pain on effort is not an ambulance, but it is not nothing either: it wants a doctor this
# week, with the red flags still said out loud.
CHEST_EFFORT = (
    "Chest pain that comes on with effort is worth checking today, not next week: ring 111 or your GP "
    "first thing. If it turns to pressure, spreads to the arm or jaw, or comes with breathlessness or "
    "sweating, ring 999 or 911 straight away.",
    "Pain in the chest on effort should be looked at today - ring 111 or your GP first thing, and let "
    "them hear when it comes on. Ring 999 or 911 straight away if it becomes pressure, spreads to the "
    "arm or jaw, or comes with breathlessness or sweating.",
)

CHEST_ASKED = (
    "Chest pain is worth having looked at rather than waiting: ring 111 or your GP today. If it "
    "feels like pressure or tightness, spreads to the arm, jaw or back, or comes with "
    "breathlessness, sweating or feeling sick, ring 999 or 911 straight away.",
    "Most chest pain is not the heart, but it is not something to work out on your own either: get "
    "it looked at today - 111 or your GP. Ring 999 or 911 if it is pressure or tightness, spreads "
    "to the arm or jaw, or comes with breathlessness, sweating or feeling faint.",
)

# A cut that will not stop bleeding: the small-cut advice ("press for ten minutes") is the wrong
# answer once the cloth is soaked through or it is still going. "the rain won't stop" and a
# nosebleed are not this, so the line has to be about a cut or blood.
# "It won't stop" on its own is already answered by the small-cut reply, which tells them to press
# for ten minutes and what the 999 signs are. This is the next step up: the line says the cloth is
# soaked, the bleeding is carrying on, or blood is going everywhere - so ten minutes has been tried.
NOT_STOPPING = (
    r"\b(?:bleeding|blood)\s+(?:through|soak\w*\s+through|through\s+to)\b.{0,20}"
    r"\b(?:cloth|bandage|dressing|towel|plaster|gauze|padding|scarf|t-?shirt|sock|sleeve)s?\b",
    # "the blood is soaking through the tea towel" is a wound; "the plaster is soaking through on the
    # ceiling" is a ceiling, so the soaking needs blood or a cut in the same line.
    r"\b(?:blood|bleed\w*|cut|wound|gash)\b.{0,40}\b(?:soaked|soaking|soaks|soak)\s+through\b",
    r"\b(?:soaked|soaking|soaks)\s+through\b.{0,20}\b(?:blood|bleed\w*)\b",
    r"\bblood\s+(?:is\s+)?(?:dripping|pouring|running)\b",
    r"\b(?:bleeding|blood)\s+everywhere\b",
)

SOFT_BLEED_OFF = (
    r"\ba\s+bit\b", r"\ba\s+little\b", r"\bslightly\b", r"\b(?:small|paper|shaving)\s+cut\b",
    r"\b(?:gums?|tooth|teeth|mouth\s+ulcer)\b", r"\bperiod\b", r"\bhemorrhoid",
    r"\b(?:tattoo|steak|meat|paint|dye|ink|marker|sauce|juice|tomato|jam|stain|wall|pipes?)\b",
    r"\b(?:has|have|had|it|they)\s+(?:now\s+)?stopp?ed\b", r"\bno\s+longer\s+bleeding\b",
)

# A cut only counts when it went into a body: "i cut the bread badly" and "the butcher cut the
# meat badly" are kitchen accidents, not wounds.
BODY_PART = (
    r"\b(?:my|his|her|their|your|our|the)\s+(?:hand|hands|finger|fingers|thumb|arm|arms|leg|legs|knee|"
    r"knees|foot|feet|head|lip|face|chin|shin|wrist|ankle|toe|toes|shoulder|side|back|neck|chest|"
    r"skin|palm|knuckle|forearm|thigh|calf|ear|mouth|eyebrow|scalp|heel|elbow)\b"
)

# Spreading means a symptom, not a body part on its own: "my arms are dead" after a chest workout
# is sore muscle, while "my arm went numb" and "jaw pain" are the real thing (#447 review).
CHEST_SPREADING = (
    r"\b(?:(?:arm|arms|jaw|shoulders?)\s+(?:went\s+|is\s+|are\s+|feels?\s+|have\s+gone\s+)?"
    r"(?:numb|tingl\w*|pain\w*|ache\w*|hurts?|heav\w*)|numb(?:ness|ed|ing|s)?|tingl\w*|sweat\w*|clammy|"
    r"sick|nausea\w*|vomit\w*|breathless\w*|dizzy|faint\w*|grey|gray|pale|crushing\s+pain)\b",
)

A_PERSON = (
    r"\b(?:i|me|myself|he|she|him|her|they|them|his|hers|their|someone|somebody|anyone|man|"
    r"woman|boy|girl|child|children|baby|babies|toddler|patient|kid|kids|mum|mom|mother|dad|father|"
    r"son|daughter|husband|wife|partner|boyfriend|girlfriend|brother|sister|friend|gran|grandma|"
    r"grandad|grandpa|nan|uncle|aunt|niece|nephew|colleague|neighbour|neighbor|people|men|women|"
    r"workers?|guests?|everyone|anybody)\b",
)

# A team, a club or a class gives up too, and that is not a person's life: "my team gave up on
# everything in the second half" reached the crisis card. The noun in front of the verb is what
# says who gave up, so a group there stands the giving-up arm down - unless the speaker says a
# wish of their own in the same line, which keeps the card.
GIVING_UP_GROUP = (
    r"\b(?:team|teams|club|squad|side|players?|group|class|band|orchestra|choir|committee|"
    r"company|staff|crew|panel|jury|government|opposition|management|union|audience|crowd|"
    r"fans?|supporters?|students?|pupils?|workers?|colleagues?|strikers?)\b[^.?!]{0,30}"
    r"\b(?:giv(?:e|es|ing)|gave|giv(?:en))\s+up\b",
)

# A wish the person says they do NOT have: "im not suicidal", "i would never kill myself", "i dont
# want to die". The crisis card is the wrong answer to somebody telling us they are all right, and
# the reply that asks them to ring a helpline for it teaches them not to say it again.
_DENIED = (
    r"\b(?:i'?m|im|i\s+am|i\s+was)\s+not\s+(?:feeling\s+|really\s+|actually\s+)?"
    r"(?:suicidal|depressed\s+enough|"
    r"thinking\s+(?:about|of)\s+(?:suicide|killing|hurting)|"
    r"going\s+to\s+(?:kill\s+my\s*self|hurt\s+my\s*self)|"
    r"about\s+to\s+(?:kill\s+my\s*self|end\s+it))",
    r"\bi\s+(?:would\s+never|wouldn'?t|will\s+not|won'?t)\s+(?:kill\s+my\s*self|"
    r"hurt\s+my\s*self|harm\s+my\s*self|cut\s+my\s*self|end\s+(?:it|my\s+life)|"
    r"top\s+my\s*self|die)\b",
    # "i dont want to die" is left out on purpose: it is as often a person frightened by how bad
    # they feel as it is a denial, and main's card is not a false alarm there the way it is for
    # "i would never kill myself".
    # "hurt myself" and "cut myself" are left out of the denial on purpose: "i dont want to hurt
    # myself" and "i dont want to cut myself anymore" are the words a person uses with the urge
    # already in the room, and main's own test keeps the card on the first of them. "i dont want
    # to kill myself" is a denial and stays outside the card.
    r"\bi\s+(?:dont|don'?t|do\s+not)\s+(?:want|wanna)\s+(?:to\s+)?"
    r"(?:kill\s+my\s*self|harm\s+my\s*self|end\s+it|"
    r"top\s+my\s*self)\b",
    r"\bi\s+(?:have\s+)?never\s+(?:felt\s+suicidal|(?:wanted|want)\s+to\s+die|"
    r"thought\s+(?:about|of)\s+suicide|hurt\s+my\s*self)\b",
    r"\bi\s+(?:would\s+)?never\s+want\s+to\s+die\b",
    r"\b(?:not|never)\s+(?:suicidal|thinking\s+about\s+suicide)\b",
)

# A day's total is the packet's own limit, not an overdose. "i had 8 paracetamol today" is the
# most the box allows, said over a day, and answering it with 999 teaches a person that the bot
# cries wolf on the line where they told the truth. Above the maximum it is still the card
# ("i had 20 paracetamol today"), and a sign in the line is the card whatever the count
# ("i had 6 ibuprofen today and i feel sick").
DAY_TOTAL_WORD = (
    r"\b(?:today|tonight|this\s+morning|this\s+afternoon|this\s+evening|so\s+far|"
    r"this\s+week|over\s+the\s+day|across\s+the\s+day|during\s+the\s+day|in\s+a\s+day|"
    r"in\s+the\s+day|in\s+24\s+hours|since\s+(?:this\s+morning|last\s+night|yesterday|"
    r"6\s?am|lunch))\b",
)

DAY_TOTAL_SIGN = (
    r"\b(?:feel|felt|feeling)\s+(?:sick|ill|rough|queasy|nauseous|dizzy|faint)\b",
    r"\b(?:vomit\w*|throwing\s+up|threw\s+up|been\s+sick|being\s+sick)\b",
    r"\b(?:stomach|tummy|abdomen|belly)\b", r"\byellow\b", r"\bbruis\w*\b",
    r"\b(?:sweat\w*|shaking|shaky|ringing\s+in\s+my\s+ears)\b",
    r"\b(?:overdos\w*|too\s+many|whole\s+(?:packet|pack|box|bottle))\b",
)

# A question about the world is asked calmly. Any of these means the thing is going on as they
# type, so the line is a call for help whatever it opens with: "why is my dad bleeding now" stays
# the bleeding card, and only the calm version of a question is a question.
SAID_AS_IT_HAPPENS = (
    r"\bright\s+now\b", r"\bnow\b", r"\bsuddenly\b", r"\bcurrently\b",
    r"\bat\s+the\s+moment\b", r"\bas\s+we\s+speak\b", r"\bstill\b", r"\bhappening\b",
    # Someone other than the speaker in the line is in trouble, not being asked about: "what
    # causes a baby to stop breathing" typed by a parent is a baby not breathing.
    r"\b(?:my|our|his|her|their|the)\s+(?:son|daughter|child|kid|kids|baby|babies|toddler|"
    r"husband|wife|partner|boyfriend|girlfriend|mum|mom|mother|dad|father|friend|mate|"
    r"neighbour|neighbor|brother|sister|grandma|grandad|granny|nan|nana|aunt|uncle|cousin|"
    r"flatmate|roommate|lodger|carer|patient|client|dog|cat|puppy|kitten)(?:'s|s)?\b",
    r"\bstop(?:ped|ping|s)?\s+breathing\b", r"\bnot\s+breathing\b", r"\bisn'?t\s+breathing\b",
    r"\bwon'?t\s+wake\b", r"\bwont\s+wake\b", r"\bno\s+pulse\b", r"\bunresponsive\b",
)

# The speaker's own cry is not a question about the world either: "why do i think about suicide"
# and "why do i feel so hopeless" are a person saying how they are, and the world-question reading
# answered them with the advice for helping someone else ("ask them directly and stay with
# them"). A first person in the line is what makes it the speaker's: "what is the suicide rate"
# has none, and stays a question about the world.
OWN_CRY = (
    r"\b(?:i|im|i'm|i've|me|my)\b[^.?!]{0,25}\b(?:suicid\w*|self[-\s]?harm\w*|"
    r"kill\s+my\s*self|want\s+to\s+die|wants?\s+to\s+die|not\s+want\s+to\s+(?:live|be\s+here)|"
    r"don'?t\s+want\s+to\s+(?:live|be\s+here)|end\s+it\s+all|better\s+off\s+dead|"
    r"hurt\s+my\s*self|harm(?:ing)?\s+my\s*self|cutting\s+my\s*self|hope?less)\b",
    r"\b(?:suicid\w*|self[-\s]?harm\w*)\b[^.?!]{0,25}\b(?:i|me|my)\b",
)

# The wish to cut with nothing after it is still the wish: "i want to cut", "i want to cut so bad"
# and "i feel like cutting" were chat's "start with the smallest version of it, not the whole
# thing", which reads as a plan. The thing after the verb is what makes the line ordinary, so this
# arm takes only the bare verb, "something", or how much it is wanted - "i want to cut costs",
# "i want to cut my hair", "i want to cut down on coffee" and "i want to cut a rug" all have a
# thing after it and are left alone.
SELF_HARM_CUT_NO_OBJECT = (
    r"\b(?:i\s+)?(?:want|wanna|wanting|need|needing|feel\s+like|feeling\s+like|felt\s+like|"
    r"thinking\s+(?:of|about)|planning\s+(?:to|on)|going\s+to|about\s+to)\s+(?:to\s+)?"
    r"(?:just\s+)?cut(?:ting)?\s*(?:$|[.?!;,]|\b(?:something|tonight|again)\b|"
    r"\bso\s+(?:bad|much|badly)\b|\breally\s+bad(?:ly)?\b)",
)

# Where the threat happens, not who made it: "someone is threatening me at work" is the
# workplace answer, and `tests/test_threat_not_loan` holds it. Both arms are spelled out with
# the unnamed subject rather than a bare "at work", so a partner who did it at the office
# still gets the card, and they start at a word boundary because safety reads a line padded
# with spaces. School is left out on purpose: there is no school-threat answer behind this,
# so standing the card down there left "someone is threatening me at school" with "Got it",
# and the card - warm, and it names 999 and a helpline - is the better of the two. "in the office"
# and "at the site" are out for the same reason: the bullying answer keys on "work", so those two
# left the line with "thanks for telling me" where main had the card.
#
# It is a separate tuple because a place does not make a threat ordinary. "someone threatened
# me with a knife at work" is an emergency, and the notebook-and-manager answer is the wrong
# first reply to it, so the caller keeps the card whenever the line also names violence.
ABUSE_FINE_PLACE = (
    # Where the threat happens, not who made it: "someone is threatening me at work" is the
    # workplace answer, and `tests/test_threat_not_loan` holds it. Both arms are spelled out with
    # the unnamed subject rather than a bare "at work", so a partner who did it at the office
    # still gets the card, and they start at a word boundary because safety reads a line padded
    # with spaces. School is left out on purpose: there is no school-threat answer behind this,
    # so standing the card down there left "someone is threatening me at school" with "Got it",
    # and the card - warm, and it names 999 and a helpline - is the better of the two.
    r"(?:^|\s)(?:someone|somebody|a\s+(?:man|bloke|guy|woman|lad)|(?:the|our|my)\s+neighbours?|"
    r"next\s+door)\b[^.?!]{0,30}\bthreaten(?:s|ed|ing)?\s+me\b"
    r"[^.?!]{0,40}\b(?:at\s+work|from\s+work)\b",
    r"(?:^|\s)(?:someone|somebody|a\s+(?:man|bloke|guy|woman|lad))\s+"
    r"(?:at\s+work|from\s+work)\b[^.?!]{0,40}"
    r"\bthreaten(?:s|ed|ing)?\s+me\b",
)

# The words that make a threat an emergency wherever it happens. Kept to what is done or
# feared rather than "threatened to", because "someone at work threatened to report me" is a
# workplace problem and not a call to 999.
VIOLENT_THREAT = (
    r"\b(?:kill|kills|killed|killing|murder|murders|stab(?:s|bed|bing)?|shoot|shoots|shot|"
    r"gun|guns|knife|knives|weapon|weapons|strangle|strangled|choke|choked|rape|raped|"
    r"beat|beats|beating|punch|punches|punched|slap|slaps|slapped|hit|hits|hitting|"
    r"hurt|hurts|hurting|harm|harms|attack|attacks|attacked|throat|"
    r"in\s+danger|scared|terrified|afraid|following\s+me|waiting\s+outside|come\s+after\s+me)\b",
)

# Horseplay at home lands on the sofa: "my kids pushed me onto the sofa" and "my sister threw me
# onto the sofa" are a game between people who live together. It is its own list rather than one
# more line in ABUSE_FINE because a hard word turns it back into an assault: "my brother pushed me
# onto the bed and held me down", "my son pushed me onto the floor and kicked me", "my cousin pushed
# me onto the bed and i was terrified" are a person being hurt by somebody they live with, and the
# family subject is what made them invisible.
ABUSE_PLAY = (
    r"\bmy\s+(?:kid|kids|child|children|son|daughter|sister|brother|mate|mates|friend|friends|"
    r"cousin|flatmate|housemate|boy|girl)\b[^.?!]{0,25}\b(?:push(?:ed|es)|shov(?:ed|es)|"
    r"thr(?:ew|ows)|dump(?:ed|s)|pull(?:ed|s)|drag(?:ged|s))\s+(?:me|us)\s+(?:on)?to\s+"
    r"(?:the\s+|a\s+|my\s+)?(?:sofa|couch|bed|floor|cushions?|beanbag|trampoline|grass|mattress)\b",
)

# The hard word that makes the same push an assault rather than the game: what is done to a person
# (held down, kicked, punched, slapped), what is said (worthless, stupid), what the speaker felt
# (scared, terrified) or the state the other one is in (drunk). A partner or an ex is not needed
# here: a hard word with a family subject is the card, and peach-hammer's four lines proved it.
ABUSE_PLAY_HARD = (
    r"\b(?:held|holding|hold|pinned|trapped|punch(?:ed|es|ing)?|kick(?:ed|s|ing)?|"
    r"slap(?:ped|s|ping)?|throat|neck|choke(?:d|s|ing)?|strangl(?:ed|es|ing)|kill\w*|"
    r"murder\w*|rape\w*|bruis(?:e|es|ed|ing)|blood|bleed\w*|hit|hits|hitting|beat|beaten|"
    r"beating|drunk|scared|afraid|terrified|frightened|worthless|useless|stupid|thick|"
    r"fat|ugly|whore|slut|bitch|cunt|shut\s+up)\b",
)

# A hand on you or a room you are in is ordinary when the line says why: "my granny cornered me in
# the kitchen to give me cake", "my son cornered me in the kitchen for a hug", "he backed me into the
# kitchen to show me the leak", "my dad blocked me in the doorway with the hoover", "my mate pinned
# me down for a selfie". The reason has to name a harmless thing, so a wall, a bedroom or a refusal
# in the line keeps the card, and one of the blow words in ABUSE_BLOW keeps it whatever the reason.
# A body being moved, held or thrown is the case whatever else the line is about: a row about the
# bins stops being a row about the bins the moment a hand lands on somebody. Both the quarrel
# stand-down and the family-in-a-room stand-down ask this first, so "we argued about the bins and
# he grabbed me by the hair" and "my son cornered me in the kitchen and shoved me onto the floor"
# keep the card that main gave them.
ABUSE_HANDS_ON = (
    r"\b(?:push(?:ed|es|ing)|shov(?:ed|es|ing)|grab(?:bed|s|bing)|drag(?:ged|s|ging)|"
    r"pull(?:ed|s|ing)|held|holding|hold|pinn(?:ed|ing)|press(?:ed|ing)|slam(?:med|s|ming)|"
    r"thr(?:ew|own|owing)|kick(?:ed|s|ing)|punch(?:ed|es|ing)|hit|hits|hitting|slapp?(?:ed|ing)|"
    r"chok(?:ed|es|ing)|strangl(?:ed|es|ing)|bit|bitten|bent\s+my|twist(?:ed|ing)\s+my|"
    r"yank(?:ed|ing)|wrench(?:ed|ing))\s+(?:me|us|my|our)\b",
    r"\bby\s+the\s+(?:hair|throat|neck|arm|wrist|collar)\b",
    r"\b(?:held|pinned|pressed|slammed|shoved|pushed|threw)\s+(?:me|us)\s+(?:against|onto|into|to)\b",
)

# A row about the bins is a row about the bins: "my husband cornered me in the kitchen about the
# bins" is a couple arguing in a kitchen, and where the row happened does not make it the card. The
# reason has to name something ordinary and the line has to be free of a blow word, a fear or a
# refusal, so "he cornered me in the hall about the knife" and "he cornered me about the rent and
# then he hit me" both keep the card.
ABUSE_QUARREL = (
    r"\b(?:corner(?:ed|s)?|pinned|trapped|stuck|backed|blocked|held|shout(?:ed|s|ing)?\s+at|"
    r"yell(?:ed|s|ing)?\s+at|argu(?:ed|es|ing))\b[^.?!]{0,30}\b(?:about|over)\s+"
    r"(?:the\s+|a\s+|my\s+|our\s+|his\s+|her\s+|these\s+|those\s+)?(?:deadline|deadlines|rota|"
    r"roster|budget|essay|review|appraisal|numbers|figures|report|proposal|invoice|quotes?|tax|"
    r"paper|project|contract|bills?|homework|exam|presentation|spreadsheet|work|targets?|quotas?|"
    r"results?|grades?|coursework|assignment|bins?|rubbish|recycling|bin\s+day|shopping|chores?|"
    r"mess|washing|washing[\s-]up|dishes|dinner|tea|bedtime|school|laundry|ironing|hoovering|"
    r"litter|garden|hedge|car|keys|holiday|guests?|tv|telly|remote|football|dog|cat|nappies|"
    r"nappy|toys?|clutter|tidying)\b",
)

ABUSE_CHILD_REFUSAL = (
    r"\b(?:my|our)\s+(?:son|sons|daughter|daughters|kid|kids|child|children|baby|toddler|"
    r"teen|teens|teenager|teenagers|boy|girl|boys|girls)\b[^.?!]{0,25}\b(?:won'?t|wont|"
    r"wouldn'?t|wouldnt|didn'?t|doesn'?t|(?:will|would|do|does|did)\s+not|refus(?:es?|ed)\s+to|"
    r"never\s+lets?)\s+(?:let|allow)\s+me\b",
)

ABUSE_PARENT_REFUSAL = (
    r"\b(?:my\s+)?(?:mum|mom|mother|dad|father|parents|step\s?dad|step\s?mum|step\s?mom|"
    r"step\s?parents|guardian|guardians)\b[^.?!]{0,25}\b(?:won'?t|wont|wouldn'?t|wouldnt|"
    r"didn'?t|doesn'?t|(?:will|would|do|does|did)\s+not|refus(?:es?|ed)\s+to|never\s+lets?)\s+"
    r"(?:let|allow)\s+me\s+" + _REFUSED_EXIT + r"\b",
)

# A refusal, whoever is making it. The parent's no and the employer's rota are named above, and both
# now keep the card when a hand is beside them - but the stand-down that matters most here looked at
# the refusal alone, so "my boss wont let me go home and he grabbed my arm" was answered as a rota
# with a hand in it. This is the same refusal shape with nobody in front of it: it is not used to
# stand anything down, only to ask what else is in the line.
ANY_REFUSAL_TO_GO = (
    r"\b(?:won'?t|wont|wouldn'?t|wouldnt|didn'?t|doesn'?t|(?:will|would|do|does|did)\s+not|"
    r"refus(?:es?|ed|ing)\s+to|never\s+lets?|not\s+letting|(?:is|was|are|were)n'?t\s+letting)\s+"
    r"(?:let|allow)\s+me\s+" + _REFUSED_EXIT + r"\b",
)

# A hand on the body, not a hand on a thing. `ABUSE_HANDS_ON` reads a physical verb with any object
# ("grabbed my deposit", "pushed me to finish the report"), which is right for the card itself but
# not for the refusal exemption beside it: a deposit dispute and a manager asking for a report are
# the two most ordinary lines in that shape, and both were answered with the emergency card once the
# refusal stopped standing them down (review of #13091). Here the object decides - a part of the
# body, or the person with nothing after it, or the person and where they landed.
A_HAND_ON_THE_PERSON = (
    # grabbed my arm, twisted my wrist, held me by the hair, pulled my hair, shook me by the
    # shoulders: the verb takes a part of the body, said with "my" or after "by the".
    r"\b(?:grab(?:bed|s|bing)|seiz(?:ed|es|ing)|twist(?:ed|ing)|yank(?:ed|ing)|"
    r"wrench(?:ed|ing)|pinn(?:ed|ing)|pins|pinning|held|hold|holding|squeez(?:ed|ing)|"
    r"shook|shak(?:en|es|ing)|pull(?:ed|s|ing)|slam(?:med|s|ming)|press(?:ed|ing)|"
    r"clamp(?:ed|ing)|lift(?:ed|ing))\s+(?:me|us|my|our)\s*(?:by\s+the\s+)?"
    r"(?:arm|arms|wrist|wrists|hair|throat|throats|neck|necks|collar|collars|shoulder|"
    r"shoulders|hand|hands|face|jaw|mouth|leg|legs|waist|back|fist|fists|clothes|shirt|"
    r"top|jumper|hood|scarf|belt)\b",
    # pushed me, shoved me, dragged me, kicked me, hit me: the person is the object, and nothing
    # says what they were pushed towards. "pushed me to finish the report" is a demand and
    # "dragged the meeting out" takes a thing, so neither is this.
    r"\b(?:push(?:ed|es|ing)|shov(?:ed|es|ing)|drag(?:ged|s|ging)|kick(?:ed|s|ing)|"
    r"punch(?:ed|es|ing)|slapp?(?:ed|ing)|hit|hits|hitting|chok(?:ed|es|ing)|"
    r"strangl(?:ed|es|ing)|bit|bitten|thr(?:ew|own|owing)|flung)\s+(?:me|us|him|her|them)\b"
    r"(?!\s+to\b)(?:\s+(?:by|against|across|onto|into|down|over|off|out\s+of|in\s+the|"
    r"on\s+the)\b|[\s.,!?]|$|\s+(?:again|hard|back)\b)",
    # "he grabbed me": with nothing after it the object of grab is the person, and a thing would
    # have been named ("grabbed my bag", "grabbed the keys").
    r"\b(?:grab(?:bed|s|bing)|shov(?:ed|es|ing)|shook|kick(?:ed|es)|punch(?:ed|es))\s+"
    r"(?:me|us|him|her|them)\s*(?:[.,!?]|$|and\b|while\b|so\b|then\b)",
)

# A boss or a rota refusing you your hours is a job, not a life taken away: "my boss wont let me
# work", "my manager wont let me leave early", "my shift wont let me have the day off" and "my boss
# wont let me work from home" are arrangements with an employer, and the refusal arms above reach
# them because "boss" is one of the people in ABUSER. The word for the employer or the arrangement
# has to be in the line, so "my husband wont let me work" and "my partner refuses to let me work"
# keep the card, and the dispatch keeps the card when a hand, a blow, a threat or a lock is beside
# it: "my boss wont let me work from home and he grabbed me" is an assault at work, not a rota.
ABUSE_EMPLOYER_REFUSAL = (
    r"\b(?:boss|manager|supervisor|employer|company|firm|agency|payroll|hr|rota|rotas|shift|"
    r"shifts|roster|office|workplace|job)\b[^.?!]{0,40}?\b(?:won'?t|wont|wouldn'?t|wouldnt|"
    r"will\s+not|doesn'?t|doesnt|does\s+not|refuses?|refused|not\s+letting)\b[^.?!]{0,15}?"
    r"\b(?:let|allow)\s+me\b",
)

# A refusal on its own is the control the card is for, so a blow word beside a harmless reason
# keeps the card - but that also means a no from a parent would never stand down, and a parent
# saying no is parenting. This is the hard half only: the injury, the fear, the threat and the lock.
ABUSE_PARENT_REFUSAL_HARD = (
    r"\b(?:hit|hits|hitting|punched|punching|beat|beaten|beating|kick(?:ed|s|ing)|chok(?:ed|es|ing)|"
    r"strangl(?:ed|es|ing)|slapp?(?:ed|s|ing)?|threw|thrown|hurt\s+me|hurts\s+me|bruis(?:e|es|ed)|"
    r"blood|black\s+eye|split\s+lip|dragged|dragging|scare(?:s|d)?|scaring|terrified|afraid|"
    r"frightened|frighten(?:s|ing)?|raped|"
    r"assaulted|threaten(?:s|ed|ing)?|locked|lock(?:s|ing)\s+me|shut\s+me|starve\w*|no\s+food|"
    r"belt|punish(?:ed|es|ing)?|burn(?:s|ed|ing)\s+me|handcuff\w*|tied\s+me)\b",
)

# A parent's no with a blow in the same line is not a rule: "my dad wont let me out and he hit me"
# answers with what to do about being hit. The blow has to land on the person, so "wont let me go
# out until i hit the books" and "he wont let me have it because i hit my brother" stay ordinary.
PARENT_REFUSAL_BLOW = (
    # The blow has to land on the person: "me" or "us" wherever it comes from, and a body of mine
    # only when somebody else did it - "my dad wont let me go out because i hit my brother" is the
    # reason for the rule, not a blow on anybody in the line.
    r"\b(?:hit|hits|hitting|punch(?:ed|es|ing)?|kick(?:ed|s|ing)?|beat|beats|beaten|beating|"
    r"slapp?(?:ed|s|ing)?|chok(?:ed|es|ing)|strangl(?:ed|es|ing)|grabb(?:ed|es)|drag(?:ged|s|ging)|"
    r"shov(?:ed|es)|push(?:ed|es)|thr(?:ew|own)|lock(?:ed|s|ing)|shut|shuts|shutting)\s+"
    r"(?:me|us)\b",
    r"(?<!\bi\s)(?<!\bwe\s)\b(?:hit|hits|hitting|punch(?:ed|es|ing)?|kick(?:ed|s|ing)?|"
    r"beat|beats|beaten|beating|slapp?(?:ed|s|ing)?|grabb(?:ed|es)|drag(?:ged|s|ging)|"
    r"shov(?:ed|es)|push(?:ed|es)|thr(?:ew|own)|lock(?:ed|s|ing)|shut|shuts|shutting)\s+"
    r"my\s+(?:arm|leg|face|head|back|ribs?|stomach|throat|hair|wrist|shoulder|neck|side|"
    r"chest|knee|hip|belly|jaw|nose|hand|foot|feet|eye|ear)\b",
    r"\b(?:hurt|hurts|hurt|hurting)\s+(?:me|my\s+\w+|us)\b",
    # Fear has to be of the person, not of the dark: "my mum wont let me watch it, it scares me"
    # is a film, and "my dad wont let me out and he scares me" is not.
    r"\b(?:he|she|they|dad|mum|mother|father|step\s?dad|step\s?mum|parents?|guardian)\b"
    r"[^.]{0,12}\b(?:scares?|scared|scaring|terrif(?:ies|ied)|frighten(?:s|ed|ing)?)\s+"
    r"(?:me|us)\b",
    r"\b(?:afraid|frightened|scared)\s+of\s+(?:him|her|them|my\s+(?:dad|mum|stepdad|"
    r"stepmum))\b",
    r"\b(?:threaten(?:s|ed|ing)?\s+(?:me|us|to\s+kill)|gave\s+me\s+a\s+(?:bruise|black\s+eye|"
    r"split\s+lip)|left\s+me\s+with\s+a\s+(?:bruise|black\s+eye|split\s+lip)|"
    r"belt|burn(?:s|ed|ing)?\s+me|starve\w*|no\s+food|handcuff\w*|tied\s+me|"
    r"rap(?:e|ed|es)|assault(?:ed|s)?)\b",
)

ABUSE_BENIGN_REASON = (
    r"\b(?:corner(?:ed|s)?|trapped|backed|blocked|pinned|shov(?:ed|es)|push(?:ed|es)|held)\s+"
    r"(?:me|us)\b[^.?!]{0,30}\bfor\s+(?:a\s+|the\s+|my\s+|your\s+|his\s+|her\s+)?(?:hug|"
    r"selfie|photo|picture|cup\s+of\s+tea|tea|coffee|cake|biscuit|dinner|"
    r"lunch|breakfast|leak|boiler|fuse|hoover|washing|shopping|presents?|surprise|tickets?|letter|"
    r"parcel|book|coat|keys)\b",
    r"\b(?:corner(?:ed|s)?|trapped|backed|blocked|pinned|shov(?:ed|es)|push(?:ed|es)|held)\s+"
    r"(?:me|us)\b[^.?!]{0,30}\bto\s+(?:give|show|hand|fetch|get|check|fix|make|find|"
    r"bring|grab|take|give\s+over)\s+(?:me\s+|us\s+)?(?:a\s+|the\s+|my\s+|your\s+|his\s+|"
    r"her\s+)?(?:hug|selfie|photo|picture|cup\s+of\s+tea|tea|coffee|cake|"
    r"biscuit|dinner|lunch|breakfast|leak|boiler|fuse|hoover|washing|shopping|presents?|surprise|"
    r"tickets?|letter|parcel|book|coat|keys)\b",
    # A doorway blocked by the hoover, the buggy or the shopping is a full pair of hands.
    r"\b(?:blocked|shoved|shoved?|pushed|backed|pinned)\s+(?:me|us)\s+[^.?!]{0,20}\bwith\s+the\s+"
    r"(?:hoover|vacuum|washing|shopping|pushchair|buggy|pram|bags?|ironing|car\s+seat|bike|"
    r"laundry|bin|mop|ironing\s+board)\b",
    # "they cornered me in the lift to talk about the rota": a conversation with a route and a
    # destination is a conversation, and the room it happened in does not change that.
    r"\b(?:corner(?:ed|s)?|pinned|trapped|backed|blocked)\b[^.?!]{0,40}\bto\s+(?:talk|ask|"
    r"discuss|pitch|sell|persuade|convince|apologise|apologize|chat|catch\s+up|explain|complain|"
    r"run\s+(?:something|an\s+idea)\s+by|check|tell)\b",
)

# Being buttonholed is a conversation, not a body in a room: "she had me cornered at the school
# gate about the raffle", "my mate had me cornered about the rota". The complaint is named with an
# article, and a complaint that is a threat or a control - the knife, the money, the pills, the
# phone, the children - is not in that list, so those keep the card.
ABUSE_BUTTONHOLED = (
    r"\b(?:(?:corner(?:ed|s)?|buttonhol(?:ed|es|ing)|pinned|trapped|backed|blocked)\s+(?:me|us)"
    r"|(?:had|has|have|got|keeps|keeping|kept)\s+(?:me|us)\s+cornered)\b"
    r"[^.?!]{0,40}\babout\s+(?:the|a|an|my|his|her|their|our|some|this|that)\s+"
    r"(?!knife|gun|blade|weapon|pills?|tablets?|money|rent|debt|affair|phone|keys|kids|children|"
    r"divorce|will|deeds|police|hospital|bruises?|drink|drugs?|door|escape|leaving)\w+",
)

# A parent at home with small children is not locked in: "my kids have me locked in the house all
# day", "my toddler keeps me stuck indoors". The actor is the child, so a partner is untouched, and
# a fear or a way out refused in the line puts the card straight back.
# What a child keeping a parent in does not explain: a fear, a blow, a name called. The refused
# exit is left out on purpose, because a refusal is exactly what a toddler is doing.
ABUSE_KIDS_CARD = (
    r"\b(?:scared|afraid|frightened|terrified|panic(?:king|ked)?|crying|sobbing|shaking|shook|"
    r"hurt\s+me|hurts\s+me|hit|hits|hitting|punched|punch|kick(?:ed|s)|slapped|slap|beaten|"
    r"beat\s+me|choked|choking|strangled|blood|bruis(?:e|es|ed)|black\s+eye|split\s+lip|"
    r"raped|assaulted|worthless|useless|stupid|thick|fat|ugly|drunk|threat(?:ened|ens|s)?)\b",
)

ABUSE_KIDS_AT_HOME = (
    r"\b(?:my|the)\s+(?:kids|children|child|toddler|baby|boys|girls|twins|little\s+ones)\b"
    r"[^.?!]{0,25}\b(?:have|has|had|keep|keeps|keeping|kept)\s+(?:me|us)\s+"
    r"(?:locked|stuck|indoors|in\s+the\s+house|stuck\s+in)\b",
    # The other way a parent says it: "my kids wont let me leave the house", "my toddler wont let me
    # leave the room", "the baby wont let me out of the house". A small child who will not be put
    # down is not a person keeping you in, and the refusal arm reads it as one.
    r"\b(?:my|the)\s+(?:kids|children|child|toddler|baby|boys|girls|twins|little\s+ones)\b"
    r"[^.?!]{0,25}\b(?:won'?t|wont|will\s+not|wouldn'?t|refuses?\s+to|never\s+lets?\s+me)\s+"
    r"(?:let|allow)\s+me\s+(?:leave|go\s+out|out|go\s+anywhere|sleep|sit\s+down|put\s+them\s+down)"
    r"\b",
)

# The violence words that keep the card whatever harmless reason is beside them: "he pinned me
# against the wall for a hug and then he hit me" is still the card.
ABUSE_BLOW = (
    r"\b(?:hit|hits|hitting|punch(?:es|ed|ing)?|beat(?:s|en|ing)?|kick(?:s|ed|ing)?|"
    r"chok(?:es|ed|ing)|strangl(?:e|es|ed|ing)|slapp?(?:s|ed|ing)?|threw|thrown|"
    r"hurt\s+me|hurts\s+me|bruis(?:e|es|ed)|blood|black\s+eye|split\s+lip|"
    r"drag(?:s|ged|ging)\s+me|would\s+not\s+let\s+me|wont\s+let\s+me|won'?t\s+let\s+me|"
    r"scared|terrified|afraid|rape|assault)\b",
)

# A family at home corners each other: "my son cornered me in the kitchen", "my kids cornered me in
# the bedroom", "my son keeps me trapped in the kitchen", "my friend has me trapped in the car",
# "they cornered me in the lift". The room words are ordinary when the person in front of them is a
# child, a parent, a sibling or a friend, and the card comes back the moment the line says what was
# done, how it felt, or that the way out was refused - which is what ABUSE_ROOM_CARD is for. A
# partner or an ex is not in this list at all: "my husband has me pinned to the wall" is the card
# with nothing else added, and ochre-hedgehog's "my husband cornered me in the kitchen about the
# bins" is stood down by the ordinary reason above instead.
ABUSE_ROOM_FAMILY = (
    r"\b(?:my\s+(?:son|daughter|child|children|kid|kids|baby|toddler|boy|girl|mum|mom|mam|mother|"
    r"dad|father|sister|brother|parent|parents|friend|friends|mate|mates|flatmate|housemate|"
    r"roommate|colleague|co-?worker|cousin|nephew|niece|aunt|uncle|nan|nana|gran|granny|"
    r"grandma|grandad|grandpa|in-laws?|boss|manager|carer)\b|they)\b[^.?!]{0,40}"
    r"\b(?:corner(?:ed|s)?|trapped|trapping|traps|backed|backing|blocked|blocking|pinned|"
    r"pinning)\b",
)

# ...and the words that say it was not ordinary after all.
ABUSE_ROOM_CARD = (
    r"\b(?:scared|afraid|frightened|terrified|panic(?:king|ked)?|crying|sobbing|shaking|shook|"
    r"hurt\s+me|hurts\s+me|hit|hits|hitting|punched|punch|kick(?:ed|s)|slapped|slap|beaten|"
    r"beat\s+me|choked|choking|strangled|blood|bruis(?:e|es|ed)|black\s+eye|split\s+lip|"
    r"raped|assaulted|worthless|useless|stupid|thick|fat|ugly|drunk|again|threat(?:ened|ens|s)?|"
    r"would\s+not\s+let|wouldn'?t\s+let|won'?t\s+let|wont\s+let|refus(?:ed|es))\b",
    # the way out refused is the case whatever the subject was
    r"\b(?:let|allow)\s+me\s+(?:go|out|past|leave|through|by)\b",
)

ABUSE_FINE_ANIMAL = (
    # An owner's animal is the one that bit, not the owner: "my neighbour's dog bit me on the leg"
    # reached the abuse card because `my <neighbour>` opened the arm and `bit me` closed it, so a
    # dog bite was answered with a domestic abuse helpline. The person is named only to say whose
    # animal it was, so the bite readers below get the line and answer it by where the bite landed.
    r"\b(?:[\w']+\s+)?(?:dog|dogs|puppy|puppies|cat|cats|kitten|kittens|pet|pets|horse|pony|"
    r"rabbit|parrot|hamster|gerbil|ferret|snake|lizard|bird|guinea\s+pig)\s+"
    r"(?:bit|bite|bites|biting|nipped|snapped\s+at|went\s+for|attacked|scratched|clawed)\s+"
    r"(?:me\b|us\b|him\b|her\b|them\b|my\s+(?:hand|hands|leg|legs|arm|arms|face|finger|fingers|"
    r"foot|feet|ankle|wrist|head|neck|lip|cheek|nose|ear|ear|thigh|shoulder))",
    # The passive turn of the same thing: "i was attacked by a dog", "my hand was bitten by a cat".
    # The animal still did it, so the abuse arm stands down and the bite readers answer.
    r"\b(?:attacked|bit|bitten|nipped|savaged|mauled|scratched|clawed|stung)\b[^.?!]{0,15}\bby\s+"
    r"(?:(?:a|an|the|my|our|his|her|their)\s+)?(?:[\w'’]+\s+){0,2}"
    r"(?:dog|dogs|puppy|puppies|cat|cats|kitten|kittens|pet|pets|horse|pony|rabbit|parrot|hamster|"
    r"gerbil|ferret|snake|lizard|bird|guinea\s+pig|bees?|wasps?|hornets?|midges?|gnats?|"
    r"mosquito(?:e)?s?|flies|fly|insects?|bugs?)\b",
)

# A blow from a small child in the middle of a game, or a hand brushed away, is not violence.
# The child has to be named and the play named in the same line: "my son hit my face while
# playing" is a Tuesday, while "he hit my face" a few words later in the same line as a row is
# still the card, and a partner's blow is never playful here.
PLAYFUL_HIT = (
    r"\b(?:my\s+)?(?:son|daughter|child|kid|toddler|baby|nephew|niece|grandson|"
    r"granddaughter)\b[^.?!]{0,40}\b(?:hit|hits|slapp?(?:ed|s)?|punch(?:ed|es)?|kicked?)\b"
    r"[^.?!]{0,40}\b(?:play(?:ing)?|playfully|play-?fighting|mucking\s+about|"
    r"messing\s+about|wrestl(?:e|ing)|tickl(?:e|ing)|accidentally|by\s+accident|"
    r"by\s+mistake|didn'?t\s+mean|didnt\s+mean|not\s+on\s+purpose|tantrum)\b",
    # "while we were playing my son hit my face": the game is named first.
    r"\b(?:play(?:ing)?|wrestl(?:e|ing)|tickl(?:e|ing)|mucking\s+about|messing\s+about)\b"
    r"[^.?!]{0,40}\b(?:my\s+)?(?:son|daughter|child|kid|toddler|baby)\b[^.?!]{0,40}"
    r"\b(?:hit|slapp?(?:ed|s)?|punch(?:ed|es)?|kicked?)\b",
    # A hand pushed away is not a hit: "he hit my hand away", "she batted my hand away".
    # A small child with a toy is not the card for a man hitting a woman: "my son hit my nose
    # with a toy" was parenting advice on main and became the abuse card in the same change,
    # because the toy arm in ABUSE_FINE now stops at a body part. A child that small, and a toy,
    # is a Tuesday with a small person - and `ADULT_HIT` keeps the card when an adult hit the
    # speaker in the same line.
    r"\b(?:my\s+)?(?:son|daughter|child|kid|toddler|baby|nephew|niece|grandson|granddaughter)\b"
    r"[^.?!]{0,30}\b(?:hit|hits|slapp?(?:ed|s)?|punch(?:ed|es)?|kicked?|head-?butt(?:ed|s)?)\b"
    r"[^.?!]{0,30}\b(?:toy|ball|pillow|block|blocks|stick|book|cup|spoon|remote|brick|lego)\b",
    r"\bh(?:it|its|itting)\s+my\s+(?:hand|arm|finger)s?\s+(?:away|off|aside|back)\b",
)

# A hit the line itself calls play is not an assault: "my wife slapped my leg, we were laughing",
# "we were playing and he hit my arm", "he punched my arm joking around" all got the abuse card on
# main (simple-radio, msg 64277). A child's game was already fenced by PLAYFUL_HIT, and these are
# grown-ups, so the fun has to be in the line and it has to be the two of them: laughing, joking,
# in fun, playing, fooling or messing about.
HIT_IN_FUN = (
    r"\b(?:hit|hits|slapp?(?:ed|s)?|punch(?:ed|es)?|elbow(?:ed|s)?|kick(?:ed|s)?|"
    r"shov(?:ed|es)|push(?:ed|es)?|tap(?:ped|s)?|nudg(?:ed|es)?|whack(?:ed|s)?)\b"
    r"[^.?!]{0,40}\b(?:laugh(?:ing|ed)?|jok(?:e|ing|ed)|kidding|in\s+fun|for\s+fun|"
    r"for\s+a\s+laugh|play(?:ing|ful)?|play-?fighting|fooling\s+about|fooling\s+around|"
    r"messing\s+about|mucking\s+about|teasing)\b",
    # The fun named first: "we were playing and he hit my arm", "as a joke he punched my arm".
    r"\b(?:play(?:ing)?|laughing|joking|joking\s+around|messing\s+about|fooling\s+about|"
    r"as\s+a\s+joke|in\s+fun|for\s+a\s+laugh)\b[^.?!]{0,40}"
    r"\b(?:hit|hits|slapp?(?:ed|s)?|punch(?:ed|es)?|elbow(?:ed|s)?|kick(?:ed|s)?|"
    r"shov(?:ed|es)|push(?:ed|es)?)\b",
)

# The fun has to be the two of them. A laugh that belongs to the other person is not the speaker's
# framing of it, it is the shape people are told to watch for: "he hit me and laughed", "he pushed
# me and laughed", "he kicked me and everyone laughed", "my husband punched my arm and laughed it
# off" were the 999 card on main and became the play reply, which is the wrong way round. The
# hitter's excuse is not the speaker's framing either - "he hit me, he was joking", "he slapped me
# then said he was only joking" - so those are the card whatever else the line says. Only a laugh
# the speaker shares ("we both laughed when he hit my arm", "my wife slapped my leg, we were
# laughing") is play.
HIT_THE_LAUGH_IS_HIS = (
    r"\b(?:and|then|but|so)\s+(?:he|she|they|everyone|everybody|all\s+of\s+them|"
    r"his\s+mates|her\s+mates|the\s+others)\s+(?:laughed|laughs|was\s+laughing|"
    r"were\s+laughing|is\s+laughing|are\s+laughing|grinned|smiled)\b",
    # "he hit me and laughed" with nobody named between the blow and the laugh
    r"\b(?:and|then)\s+(?:laughed|laughs|laughing)\b",
    r"\b(?:laugh(?:ed|ing)?\s+it\s+off|laughed\s+it\s+away)\b",
    r"\b(?:everyone|everybody|all\s+his\s+mates|all\s+her\s+mates)\s+"
    r"(?:laughed|was\s+laughing|were\s+laughing)\b",
    # the hitter's own account of it: "he was joking", "he said he was only joking",
    # "he told me it was a joke", "said it was banter"
    r"\b(?:he|she|they)\s+(?:was|were|is|are)\s+(?:only\s+|just\s+|always\s+)?"
    r"(?:joking|kidding|laughing|mucking\s+about|messing\s+about|playing|play-?fighting)\b",
    r"\b(?:said|says|saying|told|tells|telling|claimed|claims)\b[^.?!]{0,25}"
    r"\b(?:he|she|they)\s+(?:was|were|is)\s+(?:only\s+|just\s+)?(?:joking|kidding)\b",
    r"\b(?:he|she|they)\s+(?:said|says|told\s+me|tells\s+me|keeps\s+saying)\b"
    r"[^.?!]{0,20}\b(?:joke|joking|fun|banter|laugh)\b",
)

# A hand moved off a person is a gesture, not a blow: "he pushed my arm away", "she pushed my arm
# away when i tried to hug her", "she pushed my shoulder away", "he shoved my arm away". These were
# an echo on main and became the abuse card when a hit that names the part arrived (#5719): the
# part is the object of the verb, so the verb alone decided it. What makes a push a blow is that it
# lands on the person - "he pushed me", "he pushed me over", "he shoved me into the wall" - and what
# makes it a gesture is the part, and the direction it was moved in.
# What a person gets instead of the card when the line is a hand moved off and nothing more. It is
# a question rather than a verdict, because only they know whether it landed: main's card is wrong
# for a shrug of the arm, and the greeting pools are worse - "he pushed my arm away" was answered
# "Sounds alright. Anything good in it?", which is not an answer to anything they said.
PUSHED_AWAY_REPLY = (
    "A hand pushed away usually is not a blow - but only you know how it landed. If it hurt, or it "
    "frightened you, tell me and I will take it seriously.",
    "That sounds like a hand moved off rather than a hit. If there is more to it than that - it "
    "landed hard, or it is not the first time - say so and I will treat it as the real thing.",
    "Fair enough, that is a hand being moved aside rather than somebody being hit. Was it just that, "
    "or did it feel like more? I would rather ask than assume.",
)

# What the hand was pushed away in the middle of. A fall, a head into a wall or a door, being held
# in or hurt is the abuse card whatever the hand did before it - the gesture is the smallest part of
# the line (cyan-trumpet, #safety 88437).
PUSHED_AWAY_THEN_RESTRAINT = (
    r"\b(?:fell|fall|fallen|tripped|slipped)\b",
    r"\b(?:hit|banged|knocked|smashed|bumped)\s+(?:my|the|his|her)\s+(?:head|face|nose|arm|"
    r"shoulder|back|knee|hip|hand|elbow|wall|door|frame|floor|radiator|table|corner|worktop|"
    r"shelf|sideboard|stairs|banister|bed)\b",
    r"\b(?:so|because|till|until)\s+(?:i|he|she)\s+(?:couldn'?t|could\s+not|cant|wasn'?t\s+able)\b",
    r"\b(?:couldn'?t|could\s+not|cant|wouldn'?t|would\s+not)\s+(?:leave|get\s+(?:away|out)|go|move)\b",
    r"\b(?:wouldn'?t|would\s+not|won'?t)\s+let\s+me\b",
    r"\b(?:trapped|held|pinned|dragged|strangled|choked|threatened|hurt|hurts|hurting|bleeding|"
    r"blood|bruise[ds]?|sore|swollen|hard)\b",
)

# A line where something else is the subject - a pan, the dinner, a child, the day - keeps whatever
# answer that subject has, so the stand-down reply is only for the line that is the hand and nothing
# else.
PUSHED_AWAY_BUT_SOMETHING_ELSE = (
    r"\b(?:pan|pans|hob|oven|stove|grill|kettle|iron|saucepan|frying|boiling|heat|fire|smoke|"
    r"babies|baby|child|children|kid|kids|son|daughter|toddler|pregnant|hospital|ambulance|"
    r"police|999|911|work|office|shift|meeting|game|match|film|tv|phone)\b",
)

PUSHED_AWAY = (
    # ...and every verb the same motion is said with: a hand slapped or batted away is the same
    # gesture (magenta-pine's read, #safety 83005).
    r"\b(?:push(?:es|ed|ing)?|shov(?:e|es|ed|ing)|slapp?(?:s|ed|ing)?|batt?(?:s|ed|ing)?)"
    r"\s+my\s+"
    # The head is where a hand goes in an argument more often than the shoulder.
    # Not "back": a head pushed back is a blow, not a hand moved aside (crisp-beacon, #safety
    # 86096: "he pushed my head back" is the card on main).
    r"(?:hand|hands|arm|arms|finger|fingers|shoulder|shoulders|face|head)\s+"
    r"(?:away|off|aside)\b",
)

# ...but the gesture is only the gesture while nothing else in the line is restraint or a threat.
# A hand moved off a face is where an argument starts, not where it ends, and the reviewer of #6858
# found seven lines that lost the card to it: "he pushed my face away and then held me down", "...and
# grabbed my throat", "...and then shoved me", "he pushed my head away and shouted at me", "she
# pushed my face away and locked the door", "he pushed my arm away and i fell", "he pushed my arm
# away hard". A person describing being moved aside *hard* is describing force, not a shrug, so any
# of these beside the push keeps the card - it is the restraint, the raised voice, the locked door or
# the fall that makes the line, not the direction the hand went.
RESTRAINT_BESIDE = (
    r"\b(?:held|hold|holding|pinn(?:ed|ing)|dragg(?:ed|ing)|wrestl(?:ed|ing)|"
    r"restrain(?:ed|ing)?|"
    # a grip on the person, not on their coat: "grabbed my coat" is where a coat comes off
    r"grabb(?:ed|ing)\s+(?:me|my\s+(?:arm|arms|wrist|wrists|throat|neck|hair|hand|hands|"
    r"shoulders?|waist|leg|legs|body))|"
    # the same push, said of the person: "he pushed my arm away and then shoved me"
    r"(?:shov(?:ed|ing)|push(?:ed|ing))\s+me|lock(?:ed|ing)|block(?:ed|ing)|"
    r"shout(?:ed|ing)|yell(?:ed|ing)|scream(?:ed|ing)|threaten(?:ed|ing)?|fell|falling|"
    r"wouldn'?t\s+let\s+me|would\s+not\s+let\s+me|wouldn'?t\s+let\s+go|"
    r"strangl(?:ed|es|ing)|chok(?:ed|es|ing)|hard)\b",
)

# ...and a blow that also landed is still the card, whatever was moved aside first: "he pushed my
# arm away and then hit me" is a hit. A push at a body part must not stand the card down for it.
BLOW_ON_ME = (
    r"\b(?:hit|hits|hitting|slapp?(?:ed|s|ing)?|punch(?:ed|es|ing)?|kick(?:ed|s|ing)?|"
    r"beat|beats|beating|struck|thump(?:ed|s|ing)?|whack(?:ed|s|ing)?|"
    r"chok(?:ed|es|ing)|strangl(?:ed|es|ing))\s+(?:me|us)\b",
    # ...and the same blow said as the part it landed on: "he pushed my arm away and then hit my
    # face" is a hit, whatever was moved aside first.
    r"\b(?:hit|hits|hitting|slapp?(?:ed|s|ing)?|punch(?:ed|es|ing)?|kick(?:ed|s|ing)?|"
    r"beat|beats|beating|struck|thump(?:ed|s|ing)?|whack(?:ed|s|ing)?)\s+my\s+"
    r"(?:face|head|back|arm|arms|leg|legs|ribs?|stomach|belly|jaw|eye|eyes|ear|ears|neck|"
    r"throat|shoulders?|chest|side|hips?|thigh|mouth|nose|teeth|wrist|knee)\b",
    # ...and a blow on somebody else in the line: "he pushed my arm away and then hit my husband".
    r"\b(?:hit|hits|hitting|slapp?(?:ed|s|ing)?|punch(?:ed|es|ing)?|kick(?:ed|s|ing)?|"
    r"beat|beats|beating|struck|thump(?:ed|s|ing)?|whack(?:ed|s|ing)?)\s+my\s+"
    r"(?:husband|wife|partner|boyfriend|girlfriend|son|daughter|child|kid|baby|mum|mom|mother|"
    r"dad|father|brother|sister|friend|mate)\b",
)

# An age on the line itself vetoes the child the memory remembers: "my son is 2 and keeps
# hitting" then "hes 15 and he hits me" is a teenager, whatever the pronoun leaves out. A
# fifteen year old hitting a parent wants the card.
A_GROWN_AGE = re.compile(
    r"\b(?:teen(?:ager|aged)?|adolescen\w+|grown\s+up|"
    r"(?:five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
    r"seventeen|eighteen|nineteen|twenty|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20)\s*"
    r"(?:years?|yrs?)\s*(?:old)?\b|"
    r"(?:hes|shes|theyre|he'?s|she'?s|they'?re|he\s+is|she\s+is|they\s+are|aged?)\s+"
    r"(?:five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
    r"seventeen|eighteen|nineteen|twenty|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20)\b"
    r"(?!\s*months?))",
    re.IGNORECASE)

# What to say to a parent a small child has just hit or bitten, when the line itself names no
# child and the knowledge card has nothing to read: the age, the same words every time, and the
# words to give the child instead. Written to fit a hit as well as a bite.
SMALL_CHILD_LASH_REPLIES = (
    "That is what a small child does when the feeling is too big for the words, and it still "
    "hurts when it lands. Say 'no - that hurts' once, in the same words each time, put them "
    "down for a minute, then give them the words: 'you wanted that toy'.",
    "Nothing is wrong with them, or with you - hitting and biting are among the last things a "
    "small child drops. The same short reply every time is what teaches it: 'no, that hurts', a "
    "minute of no attention, then back to normal.",
    "It stings, and it is tiring, and it is the age rather than you: a small child has no other "
    "way to say the feeling yet. Catching it just before "
    "helps most - tired, hungry, or in a crowd - and one flat line when it lands, 'no - that "
    "hurts', with no big reaction to make it a game.",
)

# What a small child cannot be: a weapon, a killing, a hand round the throat, a lock on the door.
# A blow from a two year old is the blow, so ABUSE_HANDS_ON and VIOLENT_THREAT do not stand this
# down on their own; these words do, whatever age the child is.
A_REAL_DANGER = (
    r"\b(?:kill(?:ed|s|ing)?|murder\w*|knife|knives|gun|weapon|blade|strangl\w*|chok(?:e|ed|ing)|"
    r"throat|threaten\w*|scared|terrified|afraid|frightened|"
    r"drink(?:s|ing)?|drunk|beers?|pub|pints?|wine|whisky|vodka|flinch\w*|panic\w*|"
    r"walk(?:ing)?\s+on\s+eggshells|every\s+(?:single\s+)?day|nightly|"
    r"kill\s+my\s*self|suicide|the\s+police|"
    r"(?:won'?t|will\s+not|wouldn'?t|would\s+not|doesn'?t|does\s+not|never)\s+let(?:ting)?\s+me\s+"
    r"(?:leave|out|go|see))\b",
)

ADULT_HIT = (
    r"\b(?:my\s+)?(?:husband|wife|partner|boyfriend|girlfriend|ex|fiance|fiancee|dad|mum|mom|"
    r"father|mother|stepdad|stepmum|stepmom|carer|uncle|aunt)\b[^.?!]{0,30}"
    # ...and the push that comes with the rest: a partner who pushes a hand away is not the same
    # line as a stranger's hand moved off, and main gave it the card (peach-hammer, steward-frank-
    # chicken: "my husband pushed my arm away" is the card on base, and the docstring says so).
    r"\b(?:hit|hits|slapp?(?:ed|s)?|punch(?:ed|es)?|kicked?|beat|beats|struck|push(?:ed|es|ing)?|"
    r"shov(?:ed|es|ing))\b",
)

# A person can still be the one who did it when an animal is named in the same line: "my
# boyfriend attacked me and i was bitten by a dog" is the abuse card's, not the bite card's. The
# window from the person to the verb is tempered, so an animal noun in between ("my neighbour's
# dog bit me") still leaves the line to the bite readers.
PERSON_AS_ATTACKER = re.compile(
    r"\b(?:he|she|they|hubby|my\s+" + ABUSER + r")\b"
    r"(?:(?!\b(?:dog|dogs|puppy|puppies|cat|cats|kitten|kittens|pet|pets|horse|pony|rabbit|parrot|"
    r"hamster|gerbil|ferret|snake|lizard|bird|guinea\s+pig|bees?|wasps?|hornets?|midges?|gnats?|"
    r"mosquito(?:e)?s?|flies|insects?)\b)[^.?!]){0,30}"
    r"\b" + ABUSE_VERB + r"\s+me\b")

LOSS_SUBJECT = (
    r"\b(?:the\s+)?(?:death|dying|loss|losing|lost|passing|funeral|burial|cremation|news|"
    r"diagnosis|divorce|split|separation|breakup|break-up|illness|cancer)\s+of\s+"
    r"(?:my|our|the|his|her|their)\s+(?:\w+\s+)?\w+",
    r"\b(?:my|his|her|their|our)\s+\w+(?:'s|s')?\s+(?:death|dying|died|dead|departure|loss|"
    r"passing|funeral|diagnosis|illness|cancer)\b",
    r"\b(?:losing|lost|lose)\s+(?:my|our|the|his|her)\s+\w+",
    # "the day my dad died hit me sideways": the day, not the dad, is the subject.
    r"\b(?:the\s+(?:day|week|year|month|news|thought|idea|fact)\b[^.?!]{0,30}?"
    r"\b(?:died|dying|death|passed|gone|left\s+us)\b)",
    # The same bereavement said as what happened rather than as a noun: "my dad passed away
    # and its hit me hard", "my wife left me and its hit me hard". Nothing in it is a person
    # doing the hitting, and main rang the alarm for both.
    r"\b(?:my|our|his|her|their)\s+(?:\w+\s+)?\w+(?:'s|s')?\s+"
    r"(?:passed\s+(?:away|on)|left\s+(?:me|us)|walked\s+out|moved\s+out|went\s+away|"
    r"is\s+gone|has\s+gone|died|has\s+died)",
)

# "im not safe" is not self-harm language and not yet a named abuser: it is the shape people
# use when someone at home, or where they live, has stopped being safe. The reply asks which,
# and names the emergency line for now and a helpline for later, which is the same offer the
# abuse reply makes - the difference is that this line has not named what is happening yet.
# "not safe to drive" and "not safe to walk home" are about the road, so a task tail is out.
# A tail about the road, the dark or a journey is a practical worry, not this one:
# "i dont feel safe walking home at night" is not the same line as "i dont feel safe at home".
# A tail is what decides it, and a preposition plus a *thing* is not a person: "im not safe on
# a ladder since my knee" is a knee, "im not safe on my bike" is a bike, "not safe walking home
# at night" is the walk home. Listing the things cannot be complete (a ladder, the stairs, a
# chair, a roof, a horse), so the prepositional tails name the people instead and everything else
# falls through to the fallback. "on my own" is a state of a person, not an object, so it stays.
# A group is not this case either: "i dont feel safe around other people", "around men", "with
# strangers" is a general worry about a crowd, and it reads better as the honest shrug.
_PERSON = (r"(?:him|her|them|he|she|they|his|their|mum|mom|mam|mother|dad|father|stepdad|"
           r"stepfather|nan|nana|gran|granny|grandma|grandad|granddad|grandpa|son|daughter|"
           r"child|baby|brother|sister|wife|husband|hubby|partner|boyfriend|girlfriend|ex|"
           r"friend|mate|flatmate|housemate|roommate|neighbou?r|uncle|aunt|cousin|in-?laws?|"
           r"carer|staff|someone|somebody|anyone|anybody)")

# The things a worry can be about after "i feel unsafe", as a tail that stands the abuse reply
# down: a road or a climb, a journey, a night out in the open, a gym, a dog, a body part that
# will not hold. See the fourth case in UNSAFE for why this one case is a negative list.
_AWAY_TAIL = (
    r"on\s+(?:the\s+|a\s+|this\s+|my\s+)?(?:motorway|dual\s+carriageway|road|roads|stairs|"
    r"staircase|steps|ladder|ladders|bike|bicycle|motorbike|scooter|horse|roof|scaffolding|ice|"
    r"pavement|platform|escalator)\b"
    r"|up\s+(?:a\s+|the\s+|this\s+|my\s+)?(?:ladder|ladders|roof|scaffolding|stairs)\b"
    r"|in\s+(?:the\s+)?(?:dark|car|van|traffic|bus|train|tube|town|city|sea|crowd)\b"
    r"|at\s+(?:the\s+)?(?:gym|pool|beach|match|festival|club)\b"
    r"|(?:driving|walking|cycling|running|jogging|lifting|swimming|climbing|hiking|travelling|"
    r"commuting|shopping)\b"
    r"|around\s+(?:dogs?|animals?|strangers|men|crowds?|traffic)\b"
    r"|with\s+(?:this|my|the)\s+(?:knee|back|hip|shoulder|leg|ankle|arm|wrist|neck|heart|"
    r"health|balance|eyesight|grip)\b"
)

FLAMES = (
    r"\bflames?\b[^.?!]{0,25}\b(?:coming|pouring|shooting|bursting|licking|roaring|spreading|"
    r"spread|out\s+of|from|everywhere|on\s+the\s+(?:ceiling|wall|floor))\b",
    r"\b(?:coming|pouring|shooting|bursting|licking|roaring)\s+(?:out\s+of|out|from|up)\b"
    r"[^.?!]{0,25}\bflames?\b",
    r"\b(?:is|are|was|were|went|go|goes|going|it'?s)\s+(?:up\s+)?in\s+flames\b",
    r"\b(?:see|saw|can\s+see|i\s+can\s+see|there\s+are|there\s+is)\s+(?:\w+\s+){0,3}flames?\b",
    r"\bflames?\s+(?:everywhere|all\s+over|in\s+the\s+(?:room|kitchen|hall|house|flat))\b",
)

# Burnt food smokes a lot and burns nothing else: "i burnt the toast and the kitchen is full of
# smoke" was the air-the-room answer on main and the leave-the-building card here, which is the
# worst of the two for the commonest smoke line in a kitchen. The card keeps the fire that got
# out of the pan, so the food words stand the case down only when there is no fire in the line.
BURNT_FOOD = (
    r"\b(?:burnt|burned|scorched|charred)\s+(?:the\s+|my\s+|a\s+)?(?:toast|toastie|dinner|tea|"
    r"supper|lunch|bread|rice|pasta|chicken|meat|pie|pizza|beans|potatoes|chips|sauce|soup|cake|"
    r"biscuits?|muffins?|pastry|fish|veg|vegetables|garlic|onions?|bacon|sausages?|pancakes?|"
    r"porridge|toastie|crumpets?|pan|pot|wok|saucepan|cooker|food|roast|stew|curry|"
    r"casserole|lasagne|lasagna|toastie)\b",
    r"\b(?:the|my)\s+(?:toast|dinner|tea|bread|rice|chicken|meat|pie|pizza|sauce|soup|cake|"
    r"garlic|bacon|sausages?|porridge)\s+(?:is|was|has|'s|got)\s+(?:burnt|burned|charred|"
    r"scorched|smoking)\b",
    r"\bi\s+(?:burnt|burned|scorched|charred)\s+(?:it|them|something)\b",
    r"\b(?:let|left)\s+(?:the|my)\s+(?:toast|dinner|pan|sauce|rice|chicken|pizza|porridge)\b",
    r"\b(?:smoke|smoking|smoking\s+out)\s+(?:from|out\s+of)\s+(?:the|my)\s+(?:toast|"
    r"toaster|oven|cooker|grill|hob|pan)\b",
)

# The fire that is not the food: a pan alight, flames, a fire that is spreading.
FIRE_OUT = (
    r"\b(?:on|caught)\s+fire\b",
    r"\bflames?\b",
    r"\b(?:alight|ablaze|out\s+of\s+control|spreading|spread)\b",
    # Smoke everywhere is the house, whatever burnt first: a burnt bit of toast in a room you
    # cannot see across is the card on main and it stays the card.
    r"\bevery[\s-]?where\b",
    r"\ball\s+over\b",
    r"\bcan'?t\s+see\b",
    r"\b(?:chip\s+pan|grease|deep\s+fat|fryer)\b[^.?!]{0,20}\b(?:fire|flames?|alight)\b",
)

# What keeps the card even when a flame is in the thing that holds one: fat spitting on a
# barbecue is the barbecue, but the same line with the ceiling alight, smoke in the room, or the
# fire out of the grill and up the wall is the building's.
FIRE_ELSEWHERE = (
    r"\b(?:on|caught)\s+fire\b",
    r"\bsmok\w*\b",
    r"\b(?:everywhere|spreading|spread|alight|ablaze|out\s+of\s+control)\b",
    r"\b(?:ceiling|walls?|curtains?|sofa|settee|couch|mattress)\b",
    r"\b(?:alarm|trapped|can'?t\s+get\s+out|cannot\s+get\s+out)\b",
    r"\b(?:house|flat|kitchen|room|living\s+room|hall|hallway|landing|building|car|garage|"
    r"shed|chimney)\b[^.?!]{0,15}\b(?:fire|burning|flames?)\b",
)

# The clothes somebody is wearing are part of the person: a garment alight is a person alight,
# and main sent it to the laundry module, which answered "Air it before you wash it". The garment
# words are the trap the other way round - a jacket in a shop window, a dress on a hanger - so the
# line has to say the thing is alight, and the reply is stop-drop-roll before anything else.
# The things a person wears, and their hair: a garment alight is a person alight. The flame arms
# below read the same list from both sides, so the list lives in one place.
GARMENT = (r"\b(?:coat|jacket|shirt|t-?shirt|jumper|sweater|hoodie|cardigan|fleece|top|dress|"
           r"skirt|trousers|pants|jeans|pyjamas?|pj'?s|dressing\s+gown|gown|robe|scarf|apron|"
           r"overalls?|sleeve|sleeves|tie|clothes|hair|trouser\s+leg|gloves?|mittens?|socks?|"
           r"shorts|leggings|vest|sleepsuit|onesie|babygro|baby\s*gro|romper|nappy|nightie|"
           r"nightdress|dungarees|blouse|waistcoat|anorak|raincoat|mac|frock)\b")

# A pan of oil alight has ten seconds of its own answer, and "leave the building" is not it: the
# heat goes off, the lid goes on and water never goes near it. Anything that says the fire has left
# the pan - flames in the hood, smoke, the walls - keeps the building card.
PAN_FIRE = (
    r"\b(?:chip\s*pan|chip\s*pot|frying\s+pan|pan|wok|deep\s*fat|fryer)\b"
    r"[^.?!]{0,20}\b(?:is\s+|was\s+|'s\s+)?(?:on\s+fire|alight|ablaze|caught\s+fire)\b",
    r"\b(?:oil|fat|grease)\b[^.?!]{0,25}\b(?:pan|wok|fryer)\b[^.?!]{0,15}"
    r"\b(?:on\s+fire|alight|caught\s+fire)\b",
    r"\b(?:pan|wok|fryer)\b[^.?!]{0,20}\b(?:oil|fat|grease)\b[^.?!]{0,15}"
    r"\b(?:on\s+fire|alight|caught\s+fire)\b",
    # ...and the flame named rather than the fire: "the pan caught the flame", "the chip pan went
    # up in flames". A pan alight is still the pan's ten seconds, and the building card is still
    # wrong while the fire is in the pan.
    r"\b(?:chip\s*pan|chip\s*pot|frying\s+pan|pan|wok|deep\s*fat|fryer)\b[^.?!]{0,20}"
    r"\b(?:caught|catches|took|takes|went\s+up\s+in)\s+(?:the\s+|a\s+)?flames?\b",
    r"\b(?:chip\s*pan|chip\s*pot|frying\s+pan|pan|wok|deep\s*fat|fryer)\b[^.?!]{0,10}"
    r"\b(?:is|was|were|are)\s+(?:in\s+flames|blazing)\b",
)

# A car fire is not a house fire, and the words people use for it are the car's own: the engine,
# the bonnet, the dashboard. On main `the engine is on fire` and `the dashboard is on fire` were a
# shrug ("I'm sorry - that's frustrating"), `smoke from under the bonnet` was a shrug too, and
# `my car is on fire` got the leave-the-building card, which tells a driver to leave a building.
# The card below is the one for a vehicle: stop, everyone out, stand well clear, 999, and don't open
# the bonnet. It sits before the fire case so a car fire gets its own wording.
VEHICLE_FIRE = (
    r"\b(?:my|our|the)\s+(?:car|van|motorbike|moped|scooter|lorry|truck|caravan|camper|"
    r"engine|bonnet|dashboard)\b[^.?!]{0,30}\b(?:is\s+|'?s\s+|are\s+|was\s+|were\s+)?"
    r"(?:on\s+fire|caught\s+fire|alight|ablaze|in\s+flames)\b",
    # "the engine is burning" is how drivers say it uses oil, so only the bonnet and the dashboard
    # take the plain "burning"; the engine itself needs a fire word or smoke.
    r"\b(?:bonnet|dashboard)\b[^.?!]{0,20}\b(?:is\s+|'?s\s+|was\s+)?burning\b",
    r"\b(?:smoke|flames?)\b[^.?!]{0,25}\b(?:out\s+of|from(?:\s+under)?|under)\s+"
    r"(?:the\s+|my\s+|our\s+)?(?:bonnet|engine\s+bay|engine|dashboard|car|van)\b",
    r"\b(?:bonnet|engine\s+bay)\b[^.?!]{0,20}\bsmok\w*\b",
    # Smoke inside the car is the driver's own fire, and "there is smoke in the car" was told to
    # leave the building. Flames out of the exhaust belong to the car as well.
    r"\b(?:smok\w*|flames?)\b[^.?!]{0,15}\b(?:in|into|inside|filling|through)\s+"
    r"(?:the\s+|my\s+|our\s+)?(?:car|van|camper|caravan|cabin)\b",
    # A cabin full of smoke is a fire whether or not anyone can smell it.
    r"\b(?:cabin|car|van)\b[^.?!]{0,15}\bfull\s+of\s+smoke\b",
    r"\bexhaust\b[^.?!]{0,30}\b(?:flames?|fire|alight|ablaze)\b",
    r"\b(?:flames?|fire)\b[^.?!]{0,30}\bexhaust\b",
    r"\bthe\s+exhaust\b[^.?!]{0,10}\bis\s+burning\b",
    # A smell of burning needs the part it comes from. "i can smell burning in the car" is the
    # brakes or the clutch far more often than a fire, and main answers it well ("Work out when it
    # happens: a hot, acrid smell after hard braking..."), so a bare smell in the car keeps that
    # answer; a smell off the bonnet, the engine or the dashboard is where the fire is.
    r"\bsmell\w*\s+(?:of\s+)?burning\b[^.?!]{0,25}\b(?:bonnet|engine(?:\s+(?:bay|"
    r"compartment))?|dashboard)\b",
    r"\b(?:bonnet|engine\s+bay|dashboard)\b[^.?!]{0,20}\bsmell\w*\b[^.?!]{0,10}\bburn\w*\b",
    # "my car is burning" is "my car is on fire" in the words a frightened person uses, and it got
    # the leave-the-building card. Oil, fuel and petrol are left out so the oil question stays
    # where it was.
    r"\b(?:my|our|the)\s+(?:car|van|motorbike|moped|scooter|lorry|truck|caravan|camper)\b"
    r"(?![^.?!]{0,25}\b(?:oil|fuel|petrol|diesel)\b)[^.?!]{0,20}\bburning\b",
    # "burning" and "smoke" together is not a question about oil consumption, wherever the parts
    # of the line fall: "the engine is burning and there is smoke" went to the exhaust card.
    r"(?=.*\bburn\w*\b)(?=.*\bsmok\w*\b)"
    r"(?=.*\b(?:engine|bonnet|dashboard|car|van|exhaust)\b)"
    r"(?!.*\b(?:oil|fuel|petrol|diesel|calories)\b)",
    # Burning oil with smoke in the line is the worn-engine question, not this card: "my car is
    # burning oil and there is smoke" is a car that needs its rings, and VEHICLE_NOT_FIRE stands
    # this case down for the oil word while the plain burning-and-smoke arm above keeps a fire
    # that is not about oil.
)

# Smoke out of a car's exhaust is a car that is running badly, not a building on fire: "there is
# smoke coming out of the exhaust" got "Leave the building straight away and call 999 or 911". The
# fire case's own "smoke coming from" arm is what catches it, and VEHICLE_STILL_FIRE counts any
# smoke, so this needs its own fence.
VEHICLE_EXHAUST = (
    r"\b(?:smok\w*|steam|fumes?)\b[^.?!]{0,25}\b(?:from|out\s+of|out\s+the)\s+"
    r"(?:the\s+|my\s+|our\s+)?exhaust\b",
    r"\bexhaust\b[^.?!]{0,25}\b(?:smok\w*|fumes?)\b",
    r"\b(?:burning|using|losing)\s+(?:a\s+bit\s+of\s+|some\s+)?(?:oil|fuel)\b[^.?!]{0,25}"
    r"\b(?:smoking|smoky|smokes)\b",
)

# A smell is not a fire, and "burning" in "a burning smell" is a noun: "my car smells of burning",
# "the car smells like burning" and "my car has a burning smell" were all sent to the 999 card
# while the same thing said the other way round kept the brake and clutch answer. Any fire word,
# any smoke and any part named with the smell keeps the card.
VEHICLE_BURNING_SMELL = (
    r"\b(?:smell\w*|smells?|smelling|stink\w*|odou?r)\b[^.?!]{0,12}"
    r"\b(?:of|like|off)\s+(?:a\s+)?burn\w*\b",
    r"\bburn\w*\s+(?:smell|odou?r|stink)\b",
    r"\b(?:a\s+)?burning\s+(?:smell|odou?r)\b",
    # A smell of smoke is a smell too: "how do i get the smoke smell out of my car" was the 999
    # card while "my car smells of smoke" kept the cabin-filter answer.
    r"\bsmoke\s+smell\b",
    r"\b(?:smell\w*|stink\w*|odou?r)\b[^.?!]{0,12}\b(?:of|like|off)\s+smoke\b",
    r"\b(?:smoky|smokey)\s+smell\b",
)

VEHICLE_BURNING_SMELL_HARD = (
    # Not the word "smoke" on its own: "smoke smell in my car" and "a smell of smoke in the car"
    # are the smell and not the fire. Real smoke in the line is smoke there is, or smoke that is
    # doing something, or a part it comes from.
    r"\b(?:on\s+fire|caught\s+fire|alight|ablaze|in\s+flames|flames?|bonnet|"
    r"engine\s+bay|dashboard|inside\s+the\s+car|coming\s+into\s+the\s+car)\b",
    r"\bthere\s+(?:is|was|were|are)\s+(?:a\s+lot\s+of\s+|loads\s+of\s+|thick\s+)?smoke\b",
    r"\bsmoke\s+(?:coming|pouring|billowing|filling|everywhere|belching|pumping)\b",
    r"\bfull\s+of\s+smoke\b",
)

# A report that is already over is not a fire in progress: "there was smoke from the bonnet and
# the fire brigade put it out" was told to get everyone out and ring 999. The past and the fix
# have to be in the same line, and a fire that is still going keeps the card.
VEHICLE_FIRE_OVER = (
    r"(?=.*\b(?:there\s+was|there\s+were|smoke\s+came|i\s+saw|i\s+smelt|i\s+smelled|"
    r"it\s+was|we\s+had|caught\s+fire|had\s+a\s+(?:small\s+)?fire)\b)"
    r"(?=.*\b(?:fixed|put\s+(?:it\s+)?out|sorted|fine\s+now|ok\s+now|seems?\s+"
    r"(?:fine|ok|alright|to\s+be\s+(?:fine|ok))|all\s+(?:fine|ok)|no\s+(?:damage|problem|"
    r"harm))\b)",
)

# A near thing with fire in it: a near word, then a fire word inside the same sentence. Only the
# shape is here; the rule that no fire word sits outside the near clause is in `safety.py`
# (`_a_fire_that_did_not_happen`), because it asks about every fire word in the line and not just
# the one this pattern found. Without this, a near miss the fire cards did not catch - "i nearly
# burnt the house down" - was left to the fallback, which answered "I'm listening".
NEAR_FIRE = (
    r"\b(?:nearly|almost|close\s+to|about\s+to)\b[^.?!]{0,40}\b(?:fire|fires|flames?|alight|"
    r"ablaze|blazing|burning|burn|burnt|burned|catch|caught|catchin(?:g)?|smoke|smoking|"
    r"smouldering|smoldering|torched?|caught\s+light|took\s+light|went\s+up)\b",
)

# A fire drill is a fire the way a photograph of a beach is a holiday: "we almost had a fire drill at
# work" was answered "Stay out and ring 999 or 911", and it is neither a fire nor a near miss.
FIRE_DRILL = (
    r"\bfire\s+drill\b",
    r"\bfalse\s+alarm\b",
)

# The turn after a near miss with fire, which is nearly always the person saying it was nothing:
# "no it didnt catch, i caught it in time". The card has said what to check; this says when to stop
# checking, because "I'm listening - say more if it helps" is not an answer to "it didnt catch".
# The turn after a road scare is still that scare. "it was a white van" after "someone nearly hit
# me at the crossing" was answered "Good to hear. What was the best bit?", and "they never even
# stopped" after the same line got the same cheer. The near thing's own answer holds the thread
# while the person is still saying what happened.
NEAR_THING_OVER = (
    r"\b(?:it|he|she|they)\s+(?:was|were|is|came|come|did|didn'?t|wouldn'?t|never|just)\b"
    r"[^.?!]{0,26}\b(?:van|car|lorry|truck|bus|taxi|cab|bike|bicycle|driver|fella|man|woman|"
    r"bloke|idiot|speed\w*|fast|close|corner|junction|lights|crossing|pavement|road|kerb)\b",
    r"\b(?:they|he|she|it)\s+(?:didn'?t|did\s+not|never)\s+(?:stop|stop\w*|slow|slow\w*|look|"
    r"even\s+(?:stop\w*|slow\w*|look))\b",
    # What the person did about it: "i had to jump back onto the pavement" was answered "Good to
    # hear. What was the best bit?".
    r"\bi\s+(?:had|needed)\s+to\s+(?:jump|run|dive|leap|step|swerve|pull|shout|grab|yank|"
    r"scramble)\b",
    r"\b(?:jumped|dived|leapt|leaped|ran|scrambled|swerved)\s+(?:back|out\s+of\s+the\s+way)\b",
    r"\b(?:came|come|coming|appeared)\s+out\s+of\s+nowhere\b",
    r"\b(?:shook\s+me\s+up|really\s+shook\s+me|shaken\s+up|hands?\s+(?:are|were)\s+shaking|"
    r"still\s+shaking|heart\s+was\s+racing)\b",
    r"\bno\s+(?:it|they|he|she)\s+(?:didn'?t|did\s+not)\b",
    r"\b(?:nearly|almost)\s+(?:had|hit|got)\s+me\b",
)

NEAR_FIRE_OVER = (
    r"\b(?:didnt|didn'?t|never|did\s+not)\s+(?:catch|caught|go\s+up|went\s+up|take|light|"
    r"ignite|spread)\b",
    r"\b(?:caught|got|put)\s+it\s+(?:in\s+time|before|quick|early|out)\b",
    r"\bno\s+(?:real\s+)?(?:damage|harm|fire)\b",
    r"\bit\s+(?:was|is)\s+(?:fine|nothing|ok|alright|just\s+smoke|only\s+smoke)\b",
)

FIRE = (
    # The things a fire gets into, said as "<thing> is on fire". `chimney` and the rest of the
    # parts were missing while `FIRE_ELSEWHERE` below already named `chimney` as a thing that keeps
    # the card, so the two lists disagreed: "my chimney is on fire" was answered "Ugh, that's a
    # lot to carry", and so were the roof, the loft, the porch, the fence, the caravan and the
    # tumble dryer. A part of the building is the building, and anything alight is the card's
    # whatever the thing is, so this arm takes the parts as well as the rooms. What must not reach
    # it - a barbecue, a candle, an old flame, a team that is playing well - is held out by
    # `FLAMES_NOT_FIRE` below (and by not being one of these nouns), not by keeping this list short.
    r"\b(?:house|flat|apartment|kitchen|home|building|shed|garage|car|roof|roofs?|attic|loft|"
    r"chimney|chimney\s*pot|porch|balcony|fence|hedge|caravan|motorhome|camper|tent|bungalow|"
    r"cottage|semi|hall|hallway|landing|stairs?|stairwell|stairway|outhouse|lean-to|"
    # A room is part of the house too, and every room of a home is one: main answered "my
    # bedroom is on fire", "the ceiling is on fire" and "the living room is on fire" with a
    # sympathy line while the kitchen got the card. The list is the furniture of a house, not a
    # set of examples, so it takes rooms, parts of the structure and the fittings a fire starts
    # in; nothing here is a thing a flame belongs in (that is `FLAMES_NOT_FIRE`).
    r"bedroom|bedrooms?|bathroom|bath\s*room|bathrooms?|living\s*room|living\s*rooms?|"
    r"sitting\s*room|front\s*room|back\s*room|dining\s*room|spare\s*room|utility\s*room|"
    r"bed\s*room|lounge|study|conservatory|extension|cellar|basement|room|rooms|"
    r"ceiling|ceilings|wall|walls|floor|floors|floorboards?|skirting|door|doors|window|"
    r"windows|window\s*frame|banister|carpet|rug|wardrobe|cupboard|bed)\s+"
    r"(?:is\s+|'s\s+|are\s+)?(?:on\s+fire|burning|going\s+up|alight|ablaze)\b",
    # A car, a caravan or a hedge fire said with "caught": the noun was never the problem, the
    # verb was, and "the fence caught fire" had nothing at all behind it.
    r"\b(?:roof|attic|loft|chimney|chimney\s*pot|porch|balcony|fence|hedge|caravan|motorhome|"
    r"camper|tent|outhouse|shed|garage)\b[^.?!]{0,20}\bcaught\s+(?:on\s+)?fire\b",
    r"\bthere'?s\s+a\s+fire\b", r"\bfire\s+in\s+(?:the|my|our)\s+(?:house|flat|kitchen|building|room|garage|car)\b",
    r"\bsmoke\s+(?:is\s+)?(?:pouring|billowing|filling|coming\s+(?:from|out))\b",
    r"\b(?:can't|cannot|can\s+not)\s+get\s+out\b.{0,40}\b(?:smoke|fire|flames?|burning|alarm|trapped)\b",
    r"\b(?:trapped|blocked\s+in|locked\s+in)\b.{0,30}\b(?:can't|cannot)\s+get\s+out\b",
    r"\b(?:can't|cannot)\s+breathe\b.{0,20}\bsmoke\b",
    r"(?<!\bi )(?<!\bI )(?<!\bhe )(?<!\bshe )(?<!\bwe )(?<!\bthey )"
    r"\bsmoke\s+(?:everywhere|in\s+(?:the|my)\s+(?:house|flat|room|kitchen))\b",
    r"\b(?:my|the)\s+(?:house|kitchen|flat)\s+(?:is\s+)?burning\b",
    r"\bfire\s+(?:has\s+)?(?:started|spread)\b",
    r"\b(?:smoke|fire)\s+alarm\b.{0,30}\b(?:going\s+off|sounding|blaring|wailing)\b",
    r"(?<!\bi )(?<!\bI )(?<!\bhe )(?<!\bshe )(?<!\bwe )(?<!\bthey )"
    r"\bsmoke\s+(?:in|coming\s+into|filling|pouring\s+into)\s+(?:the|my|our)\b",
    r"\b(?:chip\s+pan|pan|toaster|oven|grill|curtains?|sofa|cushion|bin|"
    r"mattress|socket|plug|car|fridge|washing\s+machine|tumble\s*dryer|dryer|dishwasher|"
    r"microwave|kettle|freezer|hoover|vacuum)\b.{0,25}\b(?:caught|on)\s+fire\b",
    # "flames in the bin" was a shrug: the flame is somewhere it does not belong, which is the
    # question the card answers, and the "coming out of" arms only saw it moving.
    r"\bflames?\s+(?:in|on|inside|from|coming\s+out\s+of|out\s+of)\s+(?:the|my|our)\s+"
    r"(?:bin|bins|sofa|settee|couch|chair|car|curtains?|cushion|bed|mattress|wardrobe|cupboard|"
    r"shed|garage|oven|microwave|kettle|pan|toaster|socket|plug|wires?|lamp|lights?|tv|telly|"
    r"television|banister|rug|carpet|door)\b",
    r"\bthere'?s\s+smoke\b",
    # Smoke that fills a place, or comes in past a closed door, is the fire and not a smell to
    # clear. "the kitchen is filling with smoke" was answered with a pan of vinegar and the
    # extractor fan, "the house is filling with smoke" with bowls of white vinegar, and "smoke
    # coming under the door" with a draught excluder - all three are the card.
    r"\bsmoke\b[^.?!]{0,30}\b(?:filling|filled)\s+(?:up\s+)?(?:the|my|our)\s+(?:house|flat|"
    r"kitchen|room|living\s+room|bedroom|hall|hallway|landing|building|car|garage|shed)\b",
    r"\b(?:the|my|our)\s+(?:house|flat|kitchen|room|living\s+room|bedroom|hall|hallway|"
    r"landing|building|car|garage|shed)\b[^.?!]{0,15}\b(?:filling\s+(?:up\s+)?with\s+smoke|"
    r"full\s+of\s+smoke)\b",
    r"\bsmoke\s+(?:is\s+|was\s+)?(?:coming|pouring|seeping|drifting|billowing)\s+(?:under|through|"
    r"round|around)\s+(?:the|a|my|our)\s+(?:door|doors|floor\s?boards?|floor|ceiling|wall|walls)\b",
    # "i smoke in the hall" is a habit, not a fire: the smoke word is a verb there, so the arms
    # below refuse it when a person is the subject of it.
    r"(?<!\bi )(?<!\bI )(?<!\bhe )(?<!\bshe )(?<!\bwe )(?<!\bthey )"
    r"\bsmoke\s+(?:on|in)\s+(?:the|my|our)\s+(?:stairs|stairwell|landing|hall|hallway|corridor)\b",
) + FLAMES

# A smoulder from one appliance is not a house fire, and telling someone to leave the building
# and ring 999 because the toaster is smoking is worse than useless: it makes the card noise, and
# the card is the one that has to land on the day it is real. Smoke from a single thing, and an
# alarm that goes off whenever the grill is on, are the two shapes people write most and both
# were being read as a fire. The stand-down below keeps the card for what it is for: flames,
# smoke at room scale, a whole room filling, or a way out you cannot take.
_SMOKE_THING = (r"(?:oven|hob|grill|toaster|kettle|microwave|air\s?fryer|washing\s+machine|"
               r"washer|tumble\s+dryer|dryer|dishwasher|fridge|freezer|hoover|vacuum|"
               r"laptop|computer|phone|mobile|charger|plug|socket|tv|telly|television|iron|"
               r"hair\s?dryer|printer|boiler|radiator|heater|extractor|fuse\s?box)")

APPLIANCE_SMOKE = (
    r"\b" + _SMOKE_THING + r"\b[^.?!]{0,25}\bsmok\w*",
    r"\bsmok\w*\s+(?:is\s+)?(?:coming|pouring|billowing|rising|streaming)\s+(?:out\s+)?"
    r"(?:of|from)\s+(?:the|my|our|your)?\s*(?:\w+\s+){0,3}" + _SMOKE_THING,
    r"\bsmoke\s+(?:out\s+)?(?:of|from)\s+(?:the|my|our|your)?\s*(?:\w+\s+){0,3}"
    + _SMOKE_THING,
)

# The card is kept for these whatever the appliance is: flames, a room filling, smoke in the
# hall or on the stairs, or a door you cannot get out of. "Smoke" alone is not on the list,
# because "smoke coming out of my laptop" is the case this whole block exists for.
FIRE_SCALE = (
    r"\b(?:flames?|alight|ablaze|caught\s+fire|on\s+fire|set\s+alight)\b",
    r"\bsmoke\s+(?:everywhere|filling|pouring\s+into|coming\s+into|billowing)\b",
    # Smoke that pours out of a thing is past the thing, whatever it is: "smoke is pouring out
    # of the boiler" was read as the boiler's own small smoke and got the appliance answer, when
    # a flue that smokes like that is the fire card's.
    r"\bsmoke\s+(?:is\s+|was\s+)?(?:pouring|billowing|belching|roaring)\b",
    # The room is the subject as often as the smoke is: "the kitchen is filling with smoke" was
    # read as one appliance smoking, because "filling" sat in front of the noun.
    r"\b(?:kitchen|room|living\s+room|hall|hallway|house|flat|landing|stairs|stairwell|"
    r"bedroom)\b[^.?!]{0,15}\bfilling\s+(?:up\s+)?with\s+smoke\b",
    r"\bsmoke\s+(?:in|on)\s+(?:the|my|our)\s+(?:hall|hallway|stairs|stairwell|landing|"
    r"bedroom|room|house|flat|kitchen|toilet|bathroom)\b",
    r"\b(?:whole|entire)\s+(?:house|flat|kitchen|room|building)\b",
    r"\b(?:can'?t|cannot)\s+get\s+out\b",
    r"\b(?:spread\w*|took\s+hold|getting\s+(?:bigger|worse))\b",
    r"\b(?:smoke|fire)\s+alarm\b[^.?!]{0,30}\b(?:going\s+off|sounding|blaring)"
    r"[^.?!]{0,40}\bsmoke\b",
)

# A smoke alarm that goes off whenever the grill is on is doing its job from the wrong place.
ALARM_NUISANCE = (
    r"\b(?:smoke|fire)\s+(?:alarm|detector)\b[^.?!]{0,40}\b(?:goes\s+off|going\s+off|"
    r"sounds|sounding|beeps|beeping|chirp\w*|wails?|keeps\s+going\s+off|wont\s+stop|"
    r"won'?t\s+stop|stop\s+it)\b[^.?!]{0,40}\b(?:when|cooking|toast|toasting|grill|"
    r"grilling|oven|hob|fry|frying|roast|roasting|bake|baking|shower|steam|kitchen|"
    r"cooker)\b",
)

# Smoke that is only a smell on something is laundry, not a fire. "how do i get rid of the smell
# of smoke in my coat" was answered with "leave the building straight away and call 999", and the
# person wanted to know what to wash it with - a card spent on a coat is a card that reads as noise
# on the day it is real. The smell has to be on a thing (a coat, hair, curtains, a car) and no
# room may be named: "i can smell smoke in the kitchen" is the card, and so is anything the fire
# scale covers, which is why the stand-down below refuses itself for those.
_SMELLY_THING = (
    r"coat|jacket|clothes|clothing|jumper|shirt|top|dress|trousers|jeans|skirt|hoodie|fleece|"
    r"cardigan|suit|uniform|hat|scarf|gloves|shoes|trainers|bag|rucksack|hair|curtains?|"
    r"cushions?|sofa|settee|couch|mattress|bedding|duvet|pillow|blanket|rug|carpet|car|van|"
    r"tent|sleeping\s+bag|washing|laundry|sheets?"
)

SMOKE_IS_A_SMELL = (
    # "the smell of smoke in my coat", "my coat smells of smoke", "smoke smell in the car"
    r"\b(?:smell|smells|smelly|stinks?|stinking|reek\w*|whiff|odour|odor)\b[^.?!]{0,40}"
    r"\bsmoke\b",
    r"\bsmoke\s+(?:smell|stain\w*)\b",
    # "how do i get the smell of smoke out of a coat": the ask is a cleaning one whichever way
    # round the coat and the smoke are said.
    r"\b(?:get|getting|got|remove|removing|clear|take|taking)\b[^.?!]{0,30}\bsmoke\b"
    r"[^.?!]{0,20}\b(?:out|off)\b",
    r"\bsmoke\s+out\s+of\b",
)

BATTERY_FIRE = (
    r"\b(?:phone|laptop|tablet|ipad|battery|batteries|power\s?bank|e-?bike|e-?scooter|"
    r"hoverboard|charger|drone)\b[^.?!]{0,20}\b(?:is\s+|'s\s+|are\s+)?(?:on\s+fire|"
    r"caught\s+fire|smoking|sparking|melting|burning(?!\s+(?:up|hot|my|his|her|their|a|the))|burnt)\b",
    r"\b(?:battery|batteries)\s+(?:is\s+|are\s+)?(?:on\s+fire|caught\s+fire|smoking|"
    r"burning(?!\s+(?:up|hot|my|his|her|their|a|the)))\b",
)

# The same devices said the other way round: "my phone has flames coming out of it" is the one
# that is alight, not the kitchen it is sitting in, so the building card stands down for it.
DEVICE_BURNING = (
    r"\b(?:phone|laptop|tablet|ipad|battery|batteries|power\s?bank|e-?bike|e-?scooter|"
    r"hoverboard|charger|drone)\b[^.?!]{0,30}\b(?:flames?|alight|ablaze|burning|burnt|"
    r"caught\s+fire|on\s+fire)\b",
    r"\bflames?\b[^.?!]{0,25}\b(?:out\s+of|from)\b[^.?!]{0,10}\b(?:phone|laptop|tablet|"
    r"ipad|battery|power\s?bank|charger)\b",
)

# A child and a medicine in an amount is the poisons line, whatever the verb: a parent writes
# "my child swallowed the whole bottle of calpol" and the medicine the child drank is not on the
# tablet list, so the quantity never reached the poisons case at all.
MEDICINE = (
    r"(?:calpol|nurofen|benylin|infant\s+paracetamol|children'?s\s+(?:paracetamol|ibuprofen)|"
    r"junior\s+ibuprofen|cough\s+(?:medicine|syrup)|cold\s+medicine|antibiotics?|pills|tablets|"
    r"medicine|medicines|meds|paracetamol|ibuprofen|painkillers|antidepressants|insulin|"
    r"eye\s+drops|vitamins?|iron\s+tablets|sleeping\s+pills)"
)

# A dose given twice, said the other way round. The arms below read the child first and the
# amount second, which is one of the two ways a parent writes it, and none of them reads a child
# at all when the child is "her" or "him".
DOSE_AMOUNT = (
    r"\b(?:too\s+many|too\s+much|double|twice|extra)\s+"
    r"(?:doses?|spoonfuls?|mouthfuls?|syringes?)\b"
    r"|\b(?:twice|double|three\s+times)\s+(?:the|her|his|their|your)\s+dose\b"
    # A count of doses says the amount only when it says how close together they were: "two doses
    # of calpol" over an evening is the label's own course, so only the back-to-back way of saying
    # it counts. "in 24 hours" is not here for the same reason - that is the packet's maximum.
    r"|\b(?:two|three|four|several)\s+(?:doses?|spoonfuls?)\b[^.?!]{0,15}\b"
    r"(?:at\s+once|together|at\s+the\s+same\s+time|in\s+(?:an|one|1|a\s+single)\s+hour|"
    r"within\s+an\s+hour|in\s+\d+\s+minutes|back\s+to\s+back)\b"
)

# Doses spaced apart are the course the packet prints, not an overdose: "my toddler had two doses
# of calpol today four hours apart" is a parent following the label, and the poisons card teaches
# them that the bot cries wolf on the line where they told the truth. The spacing has to sit with
# the dose word, so a count of tablets stays the card (six tablets four hours apart is still above
# the day's limit) and "two doses in an hour" stays one as well.
DOSE_COURSE = (
    r"\b(?:doses?|spoonfuls?|syringes?)\b[^.?!]{0,20}\b(?:apart|(?:\d+|two|three|four|five|six|"
    r"several)\s+hours?\s+(?:apart|later|between|gap)|every\s+(?:\d+|two|three|four|six)\s+"
    r"hours?)\b",
    r"\bevery\s+(?:\d+|two|three|four|six)\s+hours?\b[^.?!]{0,20}\b(?:doses?|spoonfuls?)\b",
    # A count of doses over a day is the packet's own maximum: "my toddler had four doses of
    # calpol today" is what the label tells a parent to give.
    r"\b(?:two|three|four|five|six)\s+(?:doses?|spoonfuls?)\b[^.?!]{0,20}\b(?:today|"
    r"so\s+far|since\s+(?:this\s+morning|last\s+night|yesterday)|this\s+(?:morning|afternoon|"
    r"evening|week)|in\s+24\s+hours|over\s+the\s+day)\b",
)

# ...and what keeps the card on a line that is otherwise the course: too much said plainly, an
# opened packet, or a sign the medicine is not sitting well. A child who has had the day's doses
# and is now sleepy is the one to worry about, which is the sign the adult day-total does not
# carry (an adult who is sleepy after eight tablets is tired as often as poisoned).
DOSE_COURSE_KEEP = (
    r"\btoo\s+many\b", r"\boverdos\w*", r"\bhandful\b",
    r"\bwhole\s+(?:packet|pack|box|bottle)\b",
    r"\ball\s+(?:of\s+)?(?:my|his|her|their)\b",
    r"\b(?:sleepy|drowsy|floppy|limp|unrousable|hard\s+to\s+wake|wont\s+wake)\b",
    r"\bvomit\w*", r"\bbeing\s+sick\b", r"\bthrowing\s+up\b", r"\bnot\s+himself\b",
    r"\bnot\s+herself\b",
)

# Asking whether a bigger dose may be given is not a report that it was: "can i give my baby a
# double dose of calpol". 999 is no answer to somebody who has given nothing yet, and the question
# belongs to the label or a pharmacist. Anything that says the medicine has already gone in keeps
# the card.
DOSE_ASKED = (
    r"\b(?:can|could|should|shall|may|might)\s+(?:i|we)\s+(?:give|dose|add|top\s+up|double)\b",
    r"\bis\s+it\s+(?:ok|okay|alright|safe|fine)\s+to\s+(?:give|dose|add|top\s+up)\b",
    r"\bwould\s+(?:it|that)\s+be\s+(?:ok|okay|alright|safe|fine)\b",
    # The question said with the amount instead of a verb: "is it too many doses for a baby",
    # "how many doses of calpol for a baby".
    r"\bis\s+(?:it|that|this)\s+too\s+(?:many|much)\b",
    r"\bis\s+(?:it|that|this)\s+(?:ok|okay|alright|fine)\s+(?:for|to\s+give)\b",
    r"\bhow\s+(?:many|much)\b[^.?!]{0,20}\b(?:doses?|calpol|nurofen|paracetamol|ibuprofen)\b",
)

# "i overdosed on coffee", "an overdose of meetings": too much of a good thing. There is no
# substance anyone is poisoned by and no packet to keep, so it is not the poisons line.
OVERDOSE_OF_A_TREAT = (
    r"\boverdos(?:e|ed|ing)\s+(?:on\s+)?(?:(?:the|a|an|my|his|her|their)\s+)?"
    r"(?:coffee|caffeine|tea|chocolate|cake|"
    r"sugar|sweets|crisps|biscuits|cheese|ice\s+cream|tv|telly|netflix|box\s+sets?|sleep|"
    r"sun|sunshine|shopping|gossip|christmas\s+music)\b",
    r"\ban\s+overdose\s+of\s+(?:coffee|caffeine|tea|chocolate|cake|sugar|sweets|crisps|"
    r"biscuits|cheese|ice\s+cream|tv|telly|netflix|box\s+sets?|sleep|sun|sunshine|shopping|"
    r"gossip|work|meetings?|emails?|paperwork|spreadsheets?|christmas\s+music)\b",
)

# A mouthful from the bathroom cabinet is not a poisoning, and it was answered two wrong ways:
# "i swallowed a bit of mouthwash" and "i swallowed a bit of toothpaste" were the hold, and "i drank
# a mouthful of mouthwash" was the poisons card. The amount is what decides: a sip or a smear of
# mouthwash, toothpaste, shampoo or soap is water and no making yourself sick; a bottle of it, a
# child, or one of the cleaners keeps the poisons card. So the small-amount shapes are named here
# and everything else is left to `POISON` below.
MILD_SWALLOWED = (
    r"(?![^?]{0,70}\b(?:child|kid|kids|son|daughter|baby|babies|toddler|boy|girl|grandson|"
    r"granddaughter|niece|nephew)\b)"
    r"(?![^?]{0,70}\b(?:bottle|bottles|whole|tube|tubes|packet|litre|litres|pint|glass\s+full)\b)"
    r"\b(?:i|ive|i've|im|i'm)\b[^.?!]{0,20}"
    # A sip and a swig are the same mouthful as a drink, and the bubble bath is one of the
    # bathroom-cabinet things the calm answer is written for: "i drank some bubble bath" was a
    # shrug on main, because the poisons row read the product and this row did not.
    r"\b(?:swallowed|swallow|drank|drunk|drinking|licked|sucked|got|took|sipped|swigged|necked|"
    r"glugged)\b[^.?!]{0,15}"
    r"\b(?:a\s+bit|a\s+little|a\s+small\s+amount|a\s+mouthful|a\s+sip|one\s+sip|one\s+mouthful|"
    r"a\s+taste|a\s+drop|a\s+dab|a\s+smear|a\s+swig|some)\b[^.?!]{0,25}"
    r"\b(?:mouthwash|mouth\s+wash|toothpaste|shampoo|conditioner|shower\s+gel|soap|body\s+lotion|"
    r"hand\s+cream|sun\s?cream|moisturiser|moisturizer|bubble\s+bath|hand\s+soap|bath\s+soap)\b",
    r"\b(?:mouthwash|mouth\s+wash|toothpaste|shampoo|shower\s+gel)\b[^.?!]{0,15}"
    r"\b(?:got|went|sprayed|squirted)\b[^.?!]{0,10}\b(?:in|into)\s+my\s+mouth\b",
)

SOME_OF_IT = (
    r"(?:some\s+(?:of\s+the\s+)?|a\s+little\s+(?:bit\s+)?(?:of\s+)?|little\s+(?:of\s+)?|"
    r"a\s+(?:bit|drop|splash|swig|mouthful|sip|handful|piece|lick|spoonful|tablespoon|"
    r"teaspoon|glass|cup|swallow|bottle|tube|packet|can|carton|jar)\s+(?:of\s+)?|"
    r"a\s+small\s+amount\s+(?:of\s+)?|half\s+a\s+(?:glass|cup|bottle)\s+(?:of\s+)?|"
    # "i swallowed the bleach", "i drank the paint thinner": the word in front of the substance is
    # sometimes just "the", and friendly-kangaroo's point is that it hides the substance exactly
    # the way "a bit" did (friendly-kangaroo, #8776).
    r"(?:the|my|his|her|their|our|these|those)\s+)?"
)

# A mouthful of soap, toothpaste or shampoo is not the poisons line: there is a milder answer that
# washes it away, and making a small child sick over a smear of soap does more harm than the soap.
# A whole tube, a bottle or a packet is the poisons line, so the container words keep the card.
MILD_PRODUCT_SMALL = (
    # Mouthwash and hand sanitiser are not here: a child who drinks either has had alcohol, so the
    # poisons line is the right one for them and the alcohol answer is the wrong one.
    r"\b(?:toothpaste|shampoo|conditioner|shower\s+gel|soap|"
    r"body\s+lotion|hand\s+cream|sun\s?cream|moisturiser|moisturizer|bubble\s+bath)\b",
)

# Taking a product out of, from or off something is fetching, not swallowing: "i took the bleach out
# of the car" was the poisons card once the word "the" was read in front of the substance.
TOOK_OUT_OF = (
    r"\b(?:took|taken|taking|take|got|get|getting|fetched|fetch)\b[^.?!]{0,25}"
    r"\b(?:out\s+of|from|off|down\s+from|out\s+the)\s+(?:the\s+|a\s+|my\s+|his\s+|her\s+)?"
    r"(?:car|cupboard|garage|shed|bathroom|kitchen|boot|cabinet|box|bag|shelf|drawer|bottle|tin|"
    r"jar|bucket|machine|van|garden|work|locker|store|closet|cupboards|shelves)\b",
)

# The ordinary things a small child puts in their mouth - a wax crayon, a bit of chalk, a smear of
# toothpaste, a bar of soap, play dough - are neither a medicine nor on any label with a poison
# symbol. They pass through, and the answer is water, watch them, 111 if you are unsure: a 999 card
# for "my son ate a crayon" would teach a parent to ignore the card that matters. A person has to be
# named doing it, which keeps "i ate crayons as a kid" and "when i was little i ate a crayon" out,
# and the verb has to be a swallowed or eaten one, so "he chewed a crayon at nursery" and "he licked
# the soap" stay ordinary lines too.
SWALLOWED_ORDINARY = (
    # The people are named rather than matched with `my \w+`, which took "my dog ate a bar of soap"
    # and handed a person's water-and-watch card to a dog. Pets belong to pet_harm, not here.
    r"\b(?:child|kid|kids|son|daughter|baby|babies|toddler|boy|girl|he|she|they|grandson|"
    r"granddaughter|niece|nephew|"
    r"my\s+(?:son|daughter|child|kid|baby|toddler|boy|girl|grandson|granddaughter|niece|nephew|"
    r"husband|wife|partner|friend|mum|mom|dad|nan|gran))\b[^.?!]{0,25}"
    r"\b(?:swallowed|swallowing|ate|eaten|eating|drank|drunk)\b"
    r"[^.?!]{0,20}\b(?:wax\s+crayons?|crayons?|chalk(?!\s*paint)|toothpaste|bars?\s+of\s+soap|soap|"
    r"play\s?dough|(?:blu|blue)\s?tack?)\b",
)

# Smelling gas is the commonest real emergency in a home, and the answer is short: nothing that
# can spark, doors and windows open, the gas off if you can reach it, and the emergency line from
# outside. "My car smells of petrol" is not this; the word gas has to be in the line, or an
# appliance with fumes or a smell and a symptom next to it.
GAS_SMELL = (
    r"\b(?:smell|smells|smelling|smelled|smelt|whiff)\s+(?:of\s+|like\s+)?(?:a\s+)?(?:gas|gas\s+leak)\b",
    r"\b(?:can|could)\s+(?:i|you|we|she|he|they)\s+smell\s+gas\b",
    r"\bi\s+(?:can\s+)?smell\s+gas\b",
    r"\b(?:strong|funny|odd|strange|faint)\s+(?:smell|whiff)\s+of\s+gas\b",
    r"\b(?:gas|leak)\s+smell\b",
    r"\bgas\s+(?:leak|leaking|leaked)\b",
    # a boiler or a pipe leaks gas the other way round: "it is leaking gas", "gas coming out"
    r"\bleak(?:ing|s|ed)?\s+(?:out\s+)?(?:\w+\s+)?gas\b",
    r"\bgas\s+(?:is\s+)?(?:leaking|escaping|coming\s+(?:out|from)|seeping)\b",
    r"\b(?:smell\w*|whiff\w*)\b[^.?!]{0,30}\bgas\b",
    r"\bgas\b[^.?!]{0,20}\b(?:smell|stink|reek)\w*\b",
    r"\b(?:boiler|cooker|hob|heater|oven|fire|gas\s+fire)\b.{0,30}\bsmell\w*\b.{0,30}"
    r"\b(?:gas|fumes?|rotten|sulphur|sulfur|eggs?|headach\w*|dizzy|nauseous)\b",
    r"\bsmell\w*\s+(?:of\s+|like\s+)?(?:rotten\s+eggs?|sulphur|sulfur)\b.{0,30}"
    r"\b(?:boiler|cooker|hob|heater|gas)\b",
)

# Bleach and an acid make chlorine gas, and the smell does the harm. Eight ways of saying it were
# a shrug on main - "i mixed bleach and vinegar" got "Got it. Is there anything you'd like a hand
# with?", and "can i mix bleach and vinegar" got "that's beyond what I know well" - which is the
# one place a shrug is worst, because the answer is a thing the person has already done. The acid
# is the one in the house: vinegar, ammonia, a toilet cleaner, a limescale remover, a descaler.
BLEACH_MIX = (
    r"\A(?=.*\bbleach\w*\b)(?=.*\b(?:vinegar|ammonia|acid|acidic|toilet\s+cleaner|"
    r"cistern\s+cleaner|descaler|de\s?scaler|limescale|drain\s+unblocker|oven\s+cleaner|"
    r"another\s+cleaner|two\s+cleaners|other\s+cleaner|bleach\s+tablets?)\b)"
    r"(?!.*\b(?:separately|separate|different\s+days?|not\s+together|never\s+mix|washed\s+it|"
    r"rinsed\s+it|in\s+another\s+room|one\s+after\s+the\s+other)\b).*",
    # The smell, or the gas named, with nothing about what was mixed: "the bathroom smells of
    # chlorine", "i breathed in bleach fumes".
    # ...and not the smell in a glass of water: tap water, a pool and a kettle smell of chlorine
    # because that is what is in them, and the water rows answer that.
    r"\A(?!.*\b(?:tap|taps|water|waters|pool|swimming|drinking|shower|kettle|cold\s+water)\b)"
    # Chlorine is the gas; a room that smells of bleach smells of the bottle, and hands that
    # smell of it after cleaning are not an exposure.
    r".*?\b(?:smell|smells|smelling|smelt|whiff|reek\w*)\b[^.?!]{0,25}\bchlorine\b",
    r"\bchlorine\s+(?:gas|fumes?)\b",
    r"\bbreathed\s+in\b[^.?!]{0,25}\b(?:bleach|chlorine|cleaner|cleaning\s+fumes?)\b",
)

# The same question asked before it is done: "can i mix bleach and vinegar" is the one where the
# answer is worth having in one sentence, and "don't stay in the room" is an answer to a thing they
# have not done yet.
BLEACH_MIX_Q = (
    # The question has to be about the mix: "can i put bleach down the drain" and "should i use
    # bleach on mould" are cleaning questions, and they kept their answers.
    r"\b(?:can|could|should|may)\s+(?:i|we|you)\s+(?:mix|put|add|use)\b[^.?!]{0,30}\bbleach\b"
    r"(?=[^.?!]{0,30}\b(?:vinegar|ammonia|acid|acidic|toilet\s+cleaner|descaler|limescale)\b)",
    r"\b(?:is\s+it\s+(?:ok|okay|safe|fine)|would\s+it\s+(?:be\s+)?(?:ok|okay|safe|fine))\b"
    r"[^.?!]{0,30}\b(?:mix|with)\b[^.?!]{0,20}\bbleach\b",
    r"\bwhat\s+happens\s+(?:if|when)\s+(?:i|we|you)\s+mix\b[^.?!]{0,30}\bbleach\b",
    r"\bbleach\b[^.?!]{0,20}\b(?:and|with)\b[^.?!]{0,15}\b(?:vinegar|ammonia|toilet\s+cleaner|"
    r"acid)\b[^.?!]{0,20}\b(?:together|at\s+the\s+same\s+time|ok|okay|safe|fine)\b",
)

# A carbon monoxide alarm is a gadget as well as a warning. "My carbon monoxide alarm keeps
# beeping" and "how do I test my carbon monoxide alarm" are questions about a thing; the alarm
# actually sounding, or a person with the symptoms, is the emergency.
CO_GOING_OFF = (
    r"\b(?:carbon\s+monoxide|co)\s+(?:alarm|detector|monitor)s?\b.{0,30}"
    r"\b(?:beep\w*|chirp\w*|going\s+off|going\s+beep|went\s+off|gone\s+off|sounding|sounds|"
    r"sounded|wailing|ringing)\b",
    r"\b(?:beep\w*|chirp\w*|going\s+off|went\s+off|gone\s+off|sounding|sounds|sounded|wailing|"
    r"ringing)\b.{0,40}\b(?:carbon\s+monoxide|co)\s+(?:alarm|detector|monitor)s?\b",
)

# A burning smell from a device is not a cooking smell and not a charging tip: a phone, a charger,
# a plug or a battery that smells of burning, smokes, melts or bulges is a fire starting, and it
# needs to leave the house rather than get a tip about taking the case off.
ELECTRIC_BURN = (
    r"\b(?:phone|mobile|charger|charging\s+brick|laptop|tablet|ipad|battery|batteries|"
    r"power\s?bank|adapter|adaptor|plug|socket|extension\s+lead|lead|cable|wire|wiring|"
    r"fuse\s?box|vape|e-?cig\w*|hoverboard|scooter|drill|toothbrush|headphones?|earbuds?|"
    r"console|charger\s+port|charging\s+port)\b[^.?!]{0,45}"
    r"\b(?:smell\w*|smelling|smoke|smoking|smoked|smoulder\w*|melt(?:ing|ed|s)?|spark(?:ing|s|ed)?|"
    r"scorch\w*|charred|caught\s+fire|catch(?:es|ing)?\s+fire|on\s+fire|flames?|bulging|"
    r"bulged|puffed\s+up|swollen)\b",
    r"\b(?:smell\w*|smelling)\s+(?:of\s+|like\s+)?(?:burning|melting|plastic|acrid)\b[^.?!]{0,40}"
    r"\b(?:phone|charger|plug|socket|lead|cable|wire|wiring|battery|laptop|tablet|adapter|adaptor|"
    r"power\s?bank)\b",
    r"\b(?:plug|socket|extension\s+lead|adapter|adaptor|charger)\b.{0,30}"
    r"\b(?:is|are|'s|'re|was|were)\s+(?:melting|melted|scorched|charred|blackened|buzzing|"
    r"sparking)\b",
    r"\bbatter(?:y|ies)\b.{0,20}\b(?:bulging|bulged|swollen|puffed\s+up|hot\s+to\s+touch)\b",
)

# A swollen battery that is not smoking, sparking or hot is the step before the fire: it has to
# stop being used and charged, and it has to leave the house by a battery bin rather than the
# kitchen bin. Main's practical answer here is better than the fire card on its own, so it is kept
# and the fire warning is added to the end of it.
BATTERY_BULGE = (
    r"\b(?:phone|mobile|laptop|tablet|ipad|battery|batteries|power\s?bank|vape|e-?cig\w*|"
    r"hoverboard|scooter|drone|toothbrush|headphones?|earbuds?|watch)\b[^.?!]{0,25}"
    r"\b(?:bulg(?:ing|ed|es)|swollen|swelling|puffed\s+up|puffing\s+up)\b",
    r"\b(?:bulg(?:ing|ed|es)|swollen|puffed\s+up)\b[^.?!]{0,15}\b(?:battery|batteries)\b",
)

# ...and the lookalikes: heat while charging, a slow charge, a flat battery and a frayed lead are
# questions about a thing, not a fire.
ELECTRIC_FINE = (
    r"\b(?:gets?|getting|is|are)\s+(?:quite\s+|really\s+|a\s+bit\s+|very\s+)?(?:warm|hot)\b"
    r"(?!.{0,20}\b(?:smell\w*|smoke|smoking|melt\w*|spark\w*|bulging|swollen)\b)",
    r"\b(?:frayed|worn|broken|cracked|tangled)\s+(?:lead|cable|wire)\b"
    r"(?!.{0,25}\b(?:smell\w*|smoke|smoking|melt\w*|spark\w*)\b)",
    r"\b(?:battery|charge)\s+(?:life|lasts?|lasted|drains?|dropping|dies|died|percentage)\b",
    r"\bhow\s+(?:do|can|should)\s+(?:i|we|you)\s+(?:stop|keep|make|get)\b.{0,30}"
    r"\b(?:phone|battery|charger|laptop)\b.{0,20}\b(?:cool|cooler|warm|hot|charged\s+up)\b",
    r"\b(?:recycle|recycling|dispose|disposal|take|bin)\b.{0,30}\b(?:battery|batteries|phone)\b",
)

# Something foraged and eaten is a poison nobody can name: a wild mushroom, a berry picked off a
# hedge, a leaf out of the garden, and on main the whole family of them was "Good to hear. What was
# the best bit?". The poisons card says to keep the container and there is no container, so this
# gets its own card: keep what is left of it, or a photo of the plant.
FORAGED_EATEN = (
    # A named wild thing. "Wild" or "foraged" is the word that makes it unknown, and the eating verb
    # says it went into a mouth rather than a basket.
    r"\b(?:swallowed|swallowing|drank|drunk|eaten|ate|eating|licked|sucked|chewed|nibbled|"
    r"tasted|bit\s+into|put\s+(?:it\s+)?in\s+(?:his|her|their|my)\s+mouth)\b[^.?!]{0,30}"
    r"\b(?:wild\s+mushrooms?|toadstools?|puffballs?|liberty\s+caps?|magic\s+mushrooms?|"
    r"foraged|foraging|fungus|fungi)\b",
    # A berry, a leaf, a seed or a flower with where it came from: a hedge, a bush, the woods, the
    # park, the garden. A berry with no place is breakfast, so the place is the thing that is read.
    r"\b(?:swallowed|swallowing|eaten|ate|eating|licked|sucked|chewed|nibbled|tasted|"
    r"bit\s+into)\b[^.?!]{0,30}\b(?:berries|berry|leaf|leaves|plants?|seeds?|nuts?)\b"
    r"[^.?!]{0,25}\b(?:from|off|in|out\s+of)\s+(?:the\s+|a\s+|our\s+|my\s+)?(?:garden|hedge|"
    r"bush|bushes|tree|field|woods?|woodland|park|wall|plants?|border|allotment|lane|path|verge)\b",
    # A child and a garden is the same card even for a flower, because a child does not know which
    # ones are edible; a grown-up asking about eating flowers from the garden keeps the gardening
    # answer it has on main, which is about the edible ones.
    r"\b(?:my|our)\s+(?:son|daughter|child|kid|baby|toddler)\b[^.?!]{0,25}\b(?:ate|eaten|eating|"
    r"swallowed|nibbled|chewed|sucked)\b[^.?!]{0,25}\b(?:flowers?|plants?|leaf|leaves|berries|"
    r"berry|seeds?)\b[^.?!]{0,25}\b(?:from|off|in|outside)\s+(?:the\s+|a\s+)?(?:garden|hedge|"
    r"bush|park|woods?|field|ground|outside|path|allotment)\b",
    # Something brought home and eaten, with the picking said before the eating.
    r"\b(?:picked|found|gathered|brought\s+home|brought\s+me|handed\s+me)\b[^.?!]{0,25}"
    r"\b(?:mushrooms?|toadstools?|berries|berry)\b[^.?!]{0,20}\b(?:and|then)\b[^.?!]{0,15}"
    r"\b(?:ate|eaten|eating|swallowed|nibbled|chewed)\b",
)

# A dish, a punnet from the shop, a plant somebody is still growing or naming, and the wild food
# that is dinner (wild garlic, elderflower) are all food that was chosen.
FORAGED_FINE = (
    r"\b(?:risotto|soup|pie|pizza|pasta|curry|sauce|omelette|stir\s?fry|salad|dish|recipe|toast|"
    r"restaurant|menu|cake|jam|pesto|smoothie|juice|wine|ketchup|garlic|elderflower)\b",
    r"\b(?:picked\s+up|bought|shop|supermarket|market|growing|grow|planted|seeds?\s+to|"
    r"want\s+to\s+grow|identify\w*|what\s+are\s+these|which\s+mushrooms?)\b",
    r"\b(?:cooked|cook|fried|roast\w*|boiled|baked|washed|peeled)\b",
)

# Carbon monoxide is a gas, not a swallowed substance: it gets its own leak case rather than the
# poison-control reply ("keep the container so the medics know what it was" fits neither).
CO_LEAK = (
    r"\bcarbon\s+monoxide\b.{0,40}\b(?:leak\w*|poison\w*|inhaled|breath\w*|fumes?|"
    r"giving\s+(?:off|out)|emitting|exposure)\b",
    r"\b(?:leak\w*|giving\s+(?:off|out)|emitting|inhaled|poison\w*)\b.{0,40}"
    r"\bcarbon\s+monoxide\b",
    r"\bthere'?s\s+(?:some\s+|a\s+lot\s+of\s+)?(?:carbon\s+monoxide|co)\b",
    r"\bcarbon\s+monoxide\b\s+(?:in|inside|all\s+over|coming\s+(?:in|through))\s+(?:the|my|our)\b",
)

CO_SIGNS = (
    # a boiler, flue or gas fire that is giving off fumes is the gas itself, alarm or no alarm
    r"\b(?:boiler|flue|cooker|hob|gas\s+fire|fireplace|wood\s*burner|woodburner|back\s+boiler|"
    r"heater|oven)\b.{0,50}\bfum(?:e|es|ing|y)\b",
    r"\bcarbon\s+monoxide\b.{0,60}\b(?:dizzy|dizziness|headach\w*|nauseous|nausea|sick|"
    r"vomit\w*|drowsy|sleepy|confused|faint\w*|light.?headed|breathless)\b",
    r"\b(?:dizzy|dizziness|headach\w*|nauseous|nausea|sick|vomit\w*|drowsy|sleepy|confused|"
    r"faint\w*|light.?headed|breathless)\b.{0,60}\bcarbon\s+monoxide\b",
)

CO_TEST = (
    r"\bhow\s+(?:do|can|should)\s+(?:i|we|you)\s+(?:test|check|service|clean|reset|change\s+the\s+battery)"
    r"\b.{0,40}\b(?:carbon\s+monoxide|co)\s+(?:alarm|detector|monitor)\b",
    r"\b(?:carbon\s+monoxide|co)\s+(?:alarm|detector|monitor)\b.{0,40}"
    r"\b(?:test|tested|testing|service|servicing|calibrat\w+|checked)\b.{0,40}\?",
    r"\bhow\s+often\b.{0,30}\b(?:carbon\s+monoxide|co)\s+(?:alarm|detector|monitor)\b",
    r"\bwhere\s+(?:should|do)\s+(?:i|we|you)\s+(?:put|place|fit|mount|install)\b.{0,30}"
    r"\b(?:carbon\s+monoxide|co)\s+(?:alarm|detector|monitor)\b",
)

# "Gasping" is the British word for very thirsty, and it is also what a run leaves you doing:
# `im gasping for a brew`, `im gasping after that run`. The bare word put all of those on the
# emergency line. It stays a red flag for air, for breath, and for a person doing nothing.
#
# What comes after "gasping for" when the gasp is a thirst. The list it used to be was eight
# drinks long, so `im gasping for a lemonade` was the 999 line - lemonade was the one drink
# nobody had written down, and the next soft drink would have gone the same way. The rule is not
# a longer list: in British English "gasping for a X" is a thirst for any X, and the only things
# it is not are the air itself and the people who bring it. So the thing named is anything at
# all, unless the next word or two is air, breath, oxygen or someone who can help - those keep
# the emergency, and so does every red flag outside this list ("cant breathe", "woke up gasping",
# blue lips), which is re-checked before any of this stands an answer down.
_GASP_NOT_A_THIRST = (
    r"air|breath|breathe|breathing|oxygen|help|doctor|nurse|ambulance|paramedic|paramedics|"
    r"inhaler|nebuliser|nebulizer|ventilator|respirator|999|911|111|rescue|defibrillator|aed"
)
_A_THIRST = (
    r"(?:a|an|the|some|any|my|me|that|one)\s+"
    r"(?!(?:[\w'-]+\s+){0,1}(?:" + _GASP_NOT_A_THIRST + r")\b)"
    r"(?:[\w'-]+)"
)

GASP_FINE = (
    r"\bgasping\s+(?:for|after|at)\s+" + _A_THIRST,
    r"\bgasping\s+(?:for|after)\s+(?:a|an|the|some|any|my|that)\s+(?:run|walk|jog|workout|gym|session|"
    r"swim|cycle|ride|bike|spin|class|game|match|training|hill|stairs|flight\s+of\s+stairs|"
    r"shopping|hoovering|dance|dancing|song|tune|race|marathon)\b",
    r"\bgasps?\s+for\s+" + _A_THIRST,
    r"\bgasping\s+(?:on|up|coming\s+up|going\s+up|climbing)\s+(?:the\s+|a\s+|my\s+)?(?:stairs|steps|hill|"
    r"slope|incline|road|bank|staircase)\b",
    # "i was gasping after that run": the run is what took the breath away.
    r"\b(?:i|we|he|she|they)\s+(?:was|were|'m|'re|am|are)\s+gasping\s+after\b",
    r"\bgasping\s+after\s+(?:that|the|a|my|this)\b",
)

GASP_RED = (
    r"\bcan'?t\s+breathe\b", r"\bcannot\s+breathe\b", r"\bgasping\s+for\s+(?:air|breath|oxygen)\b",
    r"\bnot\s+breathing\b", r"\bturning\s+blue\b", r"\b(?:collapsed|unconscious|passed\s+out)\b",
    r"\b(?:lips|face)\s+(?:are\s+|'re\s+)?(?:blue|grey|gray)\b", r"\bchoking\b",
    r"\b(?:his|her|their)\s+(?:chest|breathing)\b",
)

# A birth story and a bout years ago are memories of a person, not an accident this week.
BREATH_PAST_OVER = (
    r"\b(?:years?|months?|decades?)\s+ago\b", r"\bwhen\s+(?:he|she|they|i)\s+was\s+"
    r"(?:born|a\s+baby|little|small|young|a\s+(?:child|kid|toddler))\b",
    r"\bas\s+a\s+(?:baby|child|kid|toddler|newborn)\b", r"\bback\s+then\b",
    r"\blast\s+(?:year|decade|winter|summer)\b", r"\bin\s+(?:the\s+)?(?:19|20)\d\d\b",
)

# A hand on the chest is how everyone points at a heart, and the gesture reaches no pain word
# at all: "my dad is clutching his chest and sweating" was answered "Noted: your dad is
# clutching his chest and sweating." Two shapes count, and a joke does not: a hand on someone
# else's chest ("my dad", "he", "she") is that person in trouble whatever else the line says,
# and a hand on your own chest is that too when a symptom is beside it - the sweating, the grey,
# the sickness, the pain, the going down. "i was clutching my chest laughing" is a joke, and
# "he grabbed his chest bag" is a bag, so both stand down: the words after "chest" have to end
# the thought or name the symptom, not start a noun.
CHEST_IN_A_HAND_TAIL = (
    r"(?:\s*[,.!?;:]|\s*$|\s+(?:and|so|but|then|too|now|again|because|with|when|as|while)\b"
    r"|\s+(?:sweat\w*|clammy|grey|gray|pale|breathless|short\s+of\s+breath|sick|dizzy|"
    r"nause\w*|faint\w*|hurts?|hurting|pain\w*|ache\w*|tight\w*|pressure|fell|fallen|"
    r"collaps\w*|went\s+down)\b)"
)

CHEST_IN_A_HAND = (
    r"\A(?![^.!?]*\b(?:laugh\w*|giggl\w*|jok\w*|hysteric\w*|sides?|meme|tiktok)\b)"
    r"(?=[^.!?]*\b(?:clutch\w*|gripp?\w*|grabb?\w*|holding|holds?|held)\s+"
    r"(?:at\s+)?(?:his|her|their)\s+chest\b" + CHEST_IN_A_HAND_TAIL + r")",
    r"\A(?![^.!?]*\b(?:laugh\w*|giggl\w*|jok\w*|hysteric\w*|sides?)\b)"
    r"(?=[^.!?]*\b(?:clutch\w*|gripp?\w*|grabb?\w*|holding|holds?|held)\s+"
    r"(?:at\s+)?(?:my|the)\s+chest\b" + CHEST_IN_A_HAND_TAIL + r")"
    r"(?=[^.!?]*\b(?:sweat\w*|clammy|grey|gray|pale|breathless|short\s+of\s+breath|"
    r"sick|dizzy|nause\w*|faint\w*|fell|fallen|collaps\w*|pass(?:ed|ing)?\s+out|"
    r"went\s+down|hurts?|hurting|pain\w*|ache\w*|tight\w*|pressure)\b)",
)

# Words and settings that slur the speech without it being a stroke: the dentist's injection,
# a night out, being tired on the phone. The sign comes after those words as often as before
# them - "i had a filling and my speech is slurring", "he was a few pints in and slurring" - so
# the guard is anchored to the whole line, the same way NOT_PREG is.
# A tooth that was out is the dentist's, whatever the tense: "after his tooth was out" is the
# same afternoon as "after he had a tooth out", and the words between the tooth and the out are
# what the first version of this guard missed (the 999 it gave was reported in #safety).
DENTAL_WORDS = (r"dentist|dental|fillings?|anaesthetic|anesthetic|numbing|novocaine|injection|"
                r"wisdom\s+tooth|root\s+canal|extraction|extracted|"
                r"(?:tooth|teeth|molar)\s+(?:\w+\s+){0,2}(?:out|removed|pulled|taken|extracted)|"
                r"(?:removed|pulled|extracted|took|take)\s+(?:a\s+|my\s+|his\s+|her\s+|"
                r"their\s+|the\s+)?(?:tooth|teeth|molar)")

# The other two ordinary causes. A drink is said as often by the glass as by the state ("he had
# a few", "a couple of drinks", "been on it all afternoon"), and being worn out is the third:
# "im slurring my words when im tired" is a person who needs sleep, and the sleep answer that
# main already gives is the right one, so the slur stands down and the line falls through.
DRINK_WORDS = (r"drink|drinking|drunk|pints?|wine|beer|alcohol|pub|party|tipsy|night\s+out|"
               r"had\s+a\s+few|a\s+few\s+(?:pints|drinks|beers|wines)|"
               r"a\s+couple\s+of\s+(?:drinks|pints|beers|wines)|been\s+on\s+it|"
               r"on\s+the\s+lash|bladdered|squiffy|merry|half\s+cut|pissed|steaming|"
               r"stag\s+do|hen\s+do|wedding\s+do|celebrat\w*|one\s+too\s+many|"
               r"a\s+skinful|three\s+sheets")

# The stroke signs that are not the words: a limb or a side that will not do as it is told, a
# face that has dropped. "dead tired" and "my voice is weak" are not these, so the limb is named.
SLUR_RED_BESIDE = (r"weak\w*|numb(?:ness|ed|ing|s)?|droop\w*|confus\w*|can'?t\s+move|can\s+not\s+move|"
                   r"one\s+side|left\s+side|right\s+side|slumped|limp\s+(?:arm|leg|hand|side)|"
                   r"dead\s+(?:arm|leg|hand|side|foot|fingers)|(?:arm|leg|hand|side|foot|face)\s+"
                   r"(?:is\s+|feels?\s+|went\s+)?(?:weak|numb|dead|heavy)")

# A child too young to say its words clearly mush-mouths a lot of the time, so the stroke card is
# the wrong answer to "the toddler is slurring his words": it asks for the sudden part instead,
# and names the number for the case that is sudden. "my 2 year old isnt talking yet" is a
# different thing and is not this.
SMALL_CHILD = (r"toddler|baby|infant|newborn|(?:one|two|1|2)[\s-]?year[\s-]?old|"
               r"1[0-9][\s-]?month[\s-]?old|1[89]\s*months|preschooler|small child|little one|"
               # the way a parent says it: "my son is 2 and he slurs his words"
               r"(?:son|daughter|boy|girl|child|kid)\s+is\s+(?:one|two|three|1|2|3)\b")

SLUR_THICK = (r"(?:slurr\w*|slurs?|slurred|speech\s+(?:is|are|sounds?|comes)|"
              # "mush\w*" caught the mushroom: "can my baby have mushrooms" is a food question,
              # and it was answered with the thick-speech card.
              r"words?\s+(?:are|is|come|coming|sound|sounds)|mush(?!room)\w*|thick\s+speech)")

# The third is the occasion: a stroke does not wait for the meeting. "i cant get my words out in
# meetings", "my words wont come out when i talk to people" and "i cant get my words out when i
# meet new people" are how nerves are said, and all three were the ambulance. The stand-down is
# whole-line and only on the words-out patterns, so a weakness, a droop or a numb side beside the
# words still rings through the red-sign patterns below, the same way the drink and the tiredness
# are stood down and a weak arm is not.
WORDS_OUT_OCCASION = (
    r"\b(?:in|during|at)\s+(?:a\s+|the\s+|my\s+|his\s+|her\s+|their\s+|our\s+)?"
    r"(?:meetings?|interviews?|presentations?|class(?:es)?|lectures?|part(?:y|ies)|phone\s?calls?|"
    r"video\s?calls?|calls?|seminars?|assembl(?:y|ies))\b"
    r"|\bwhen(?:ever)?\s+(?:i|he|she|they)\s+(?:talk|speak|meet|phone|ring|present|"
    r"have\s+to\s+speak|stand\s+up)\b"
    r"|\bmeet(?:ing)?\s+(?:new\s+)?(?:people|someone|strangers)\b"
    r"|\bin\s+front\s+of\s+(?:people|everyone|the\s+class|a\s+crowd|others)\b"
    r"|\bpublic\s+speaking\b"
    r"|\bon\s+the\s+phone\b"
    r"|\b(?:nerv\w*|anxious|anxiety|panic\w*|shy|embarrass\w*|scared|self[- ]conscious|"
    r"introvert\w*)\b"
)

# The hand that will not hold what it is holding, or keeps dropping it, is the F in FAST said the
# way people say it: "my nan cant hold her cup and she is confused" was answered with a dementia-care
# line and "my mum cant hold her drink and she is confused" with the drinking one. The thing in the
# hand has to be named, so "i keep dropping things" and "my grip is weak after the gym" keep their
# answers, and the hand needs another sign of the stroke beside it - alone, a dropped cup is a cup.
STROKE_HAND = (
    r"\b(?:can'?t|cannot|couldn'?t|could\s+not|unable\s+to|not\s+able\s+to|struggl\w*\s+to)\s+"
    r"(?:hold|grip|lift)\s+(?:my|his|her|their|our|the)\s+"
    r"(?:cup|mug|glass|drink|knife|fork|pen|phone|keys|bag|book|plate|spoon|toothbrush|comb|"
    r"hairbrush)\b",
    r"\b(?:keeps?|kept|is|was|are|were|started)\s+(?:on\s+)?dropping\s+"
    r"(?:my|his|her|their|our|the)\s+(?:cup|mug|glass|drink|knife|fork|cutlery|pen|phone|"
    r"keys|bag|book|plate|spoon|toothbrush|remote|knitting)\b",
    r"\b(?:dropped|dropping)\s+(?:my|his|her|their|our|the)\s+"
    r"(?:cup|mug|glass|drink|knife|fork|cutlery|pen|phone|keys|bag|book|plate|spoon|"
    r"toothbrush|remote|knitting)\b",
)

# The signs of a stroke that no ordinary cause explains: a face that has dropped, the words gone,
# the sight doubled. These are the ones a chronic illness does not account for, so they keep the
# card even when the line also names the flu, the cold or a long-standing condition.
STROKE_HAND_HARD = (
    r"\b(?:droop\w*|"
    r"face\s+(?:is\s+|has\s+|s\s+)?(?:dropped|drooping|gone\s+on\s+one\s+side)|"
    r"slurr\w*|slurred|speech\s+(?:is\s+|was\s+|has\s+)?(?:slurred|wrong|gone|thick)|"
    r"can'?t\s+speak|cant\s+speak|wrong\s+words?|words?\s+wrong|not\s+making\s+sense|"
    r"double\s+vision|drool\w*|swallow\w*|"
    r"doesn'?t\s+know\s+(?:where|what|who)|didn'?t\s+know\s+(?:where|what|who)|"
    r"(?:one\s+side|left\s+side|right\s+side|one\s+arm|one\s+leg|one\s+hand|one\s+foot|"
    r"(?:the\s+)?left\s+(?:arm|leg|hand|foot)|(?:the\s+)?right\s+(?:arm|leg|hand|foot))"
    r"\s+(?:is\s+|has\s+gone\s+|went\s+|feels?\s+)?(?:weak\w*|numb(?:ness|ed|ing|s)?)|"
    r"(?:face|lip|mouth|tongue)\s+(?:feels?\s+|is\s+|has\s+gone\s+|went\s+)?numb(?:ness|ed|ing|s)?)",
)

# The other sign that turns a hand into the ambulance: the face, the words, a confused head, the
# sight, the swallow, not knowing where they are, or one side gone weak or numb. Bare "weak" and
# bare "numb" are not here: a wrist is weak and a hand is numb in the cold.
STROKE_HAND_BESIDE = (
    r"\b(?:confus\w*|disorient\w*|doesn'?t\s+know\s+(?:where|what|who)|"
    r"droop\w*|face\s+(?:is\s+|has\s+|s\s+)?(?:dropped|drooping|gone\s+on\s+one\s+side)|"
    r"slurr\w*|slurred|speech\s+(?:is\s+|was\s+|has\s+)?(?:slurred|wrong|gone|thick)|"
    r"can'?t\s+speak|cant\s+speak|wrong\s+words?|words?\s+wrong|"
    r"not\s+making\s+sense|vision|can'?t\s+see|cant\s+see|blurr\w*|double\s+vision|"
    r"drool\w*|swallow\w*)\b",
) + STROKE_HAND_HARD

# A cause that is already known and long-standing explains a hand and a weak or confused head on
# its own: the flu, the cold, Raynaud's, arthritis, Parkinson's, a stroke years ago. It stands the
# case down unless one of the hard signs above is in the line too, because those are new.
STROKE_HAND_CHRONIC = (
    r"\b(?:sometimes|occasionally|always|for\s+years|for\s+months|for\s+ages|"
    r"since\s+(?:the|her|his|their|last|she\s+was|he\s+was|they\s+were)|"
    r"it'?s\s+been\s+like\s+this|arthritis|arthrit\w*|parkinson\w*|multiple\s+sclerosis|"
    r"\bms\b|cerebral\s+palsy|carpal\s+tunnel|raynaud\w*|circulation|"
    r"when\s+it'?s\s+cold|when\s+it\s+is\s+cold|in\s+the\s+cold|when\s+the\s+weather\s+"
    r"(?:is\s+)?(?:cold|turns)|after\s+the\s+flu|the\s+flu\b|long\s+covid|"
    r"neuropath\w*|chemo\w*|old\s+stroke|stroke\s+years\s+ago|dementia\s+already)\b",
)

# A weak side is how most strokes are said, and "my dad has gone all weak on one side" was a
# shrug on main. The weakness word and the side word come in either order, and a limb that has
# "gone numb" or "gone dead" is the same sign said about one arm. The stand-downs below keep the
# ordinary numb lines ordinary: a cold hand, a limb slept on, a trapped nerve after the gym.
STROKE_WEAK = (
    r"\b(?:weak\w*|numb|dead|useless|heavy|droop\w*|gone\s+(?:all\s+)?(?:weak|numb|dead))\b"
    r"[^.?!]{0,25}\b(?:one\s+side|left\s+side|right\s+side|down\s+one\s+side)\b",
    r"\b(?:one\s+side|left\s+side|right\s+side)\b[^.?!]{0,25}"
    r"\b(?:weak\w*|numb|dead|useless|heavy|droop\w*|gone\s+(?:all\s+)?(?:weak|numb|dead)|"
    r"won'?t\s+work|wont\s+work|not\s+working)\b",
    r"\b(?:face|cheek|mouth|smile|eyelid|one\s+eye)\b[^.?!]{0,25}"
    r"\b(?:droop\w*|has\s+gone\s+(?:slack|droopy|funny|loose)|sagging|lopsided|gone\s+slack)\b",
    r"\b(?:can'?t|cannot|can\s+not)\s+(?:feel|move|use|hold)\s+(?:my|his|her|their)\s+"
    r"(?:arm|hand|leg|side|left\s+arm|right\s+arm|left\s+leg|right\s+leg)\b",
    # An arm that will not come up is the arm of FAST - but only when nothing about the movement
    # is named: "i cant lift my arm above my head" is a shoulder, and a leg is a strain.
    r"\b(?:can'?t|cannot|can\s+not)\s+lift\s+(?:my|his|her|their)\s+(?:arm|hand)\b"
    r"(?!\s*(?:above|up|over|high|any\s*more|at\s+all|very|to\s+the|past|out))",
    # FAST is asked as "can you lift both arms", so both arms are the arm of a stroke - and the
    # same fences apply, because `i cant lift my arms over my head after the gym` is a shoulder
    # however many arms it is.
    r"\b(?:can'?t|cannot|can\s+not)\s+(?:lift|raise)\s+(?:both\s+(?:of\s+)?)?"
    r"(?:my|his|her|their)\s+arms\b"
    r"(?!\s*(?:above|up|over|high|any\s*more|at\s+all|very|to\s+the|past|out|since|because))",
    r"\b(?:can'?t|cannot|can\s+not)\s+(?:lift|raise)\s+both\s+arms\b"
    r"(?!\s*(?:above|up|over|high|any\s*more|at\s+all|very|to\s+the|past|out))",
    # A limb that has gone numb is only the stroke when the line names a side, or the arm is
    # dead or useless: `my hand has gone numb` is carpal tunnel and `my leg has gone dead` is a
    # back, and both had their own good answers on main.
    r"\b(?:my|his|her|their)\s+(?:side|left\s+(?:arm|hand|leg|side)|right\s+(?:arm|hand|leg|side))"
    r"\b[^.?!]{0,15}\b(?:has\s+|have\s+|had\s+|went\s+|is\s+|feels?\s+|feels\s+like\s+its\s+)?"
    r"(?:gone|went|all)\s+(?:all\s+)?(?:numb|dead|useless|weak|funny|heavy|like\s+lead)\b",
    r"\b(?:my|his|her|their)\s+(?:arm|hand)\b[^.?!]{0,15}"
    r"\b(?:has\s+|have\s+|had\s+|went\s+|is\s+|feels?\s+|feels\s+like\s+its\s+)?"
    r"(?:gone|went|all)\s+(?:all\s+)?(?:dead|useless|weak)\b",
    # An arm that went numb *for a few minutes* is the transient kind, which is the one thing a
    # numb arm really is a warning of: `my arm went numb for a few minutes` is how a TIA is said.
    # A numb hand with no time in it is carpal tunnel and stays ordinary.
    r"\b(?:my|his|her|their)\s+(?:arm|hand)\b[^.?!]{0,25}\bnumb(?:ness|ed|ing|s)?\b[^.?!]{0,25}"
    r"\b(?:for\s+(?:a\s+)?(?:few|several|couple\s+of|two|three|ten|twenty|\d+)\s+"
    r"(?:minutes?|mins?|hours?|hrs?)|came\s+and\s+went|then\s+it\s+went|"
    r"out\s+of\s+nowhere|suddenly|this\s+(?:morning|afternoon|evening))\b",
    r"\b(?:lost|loss\s+of)\s+(?:the\s+)?(?:sight|vision)\s+in\s+"
    r"(?:(?:my|his|her|their)\s+)?(?:left|right|one|an?)\s+eye\b",
    r"\b(?:can'?t|cannot)\s+see\s+(?:out\s+of|with|in)\s+(?:(?:my|his|her|their)\s+)?"
    r"(?:left|right|one)\s+(?:of\s+(?:my|his|her|their)\s+)?eyes?\b",
    # Losing the sight of an eye is said more ways than "lost vision in": "my vision has gone in
    # my left eye", "my sight has gone in one eye", "my eye has gone blind", "i have gone blind in
    # one eye". Sight that is blurry, fuzzy, dim or worse is a slow thing for the optician and
    # stays ordinary; "blind drunk", "blind date", "blind spot" and "colour blind" are not an eye
    # at all, and none of them fit these arms.
    r"\b(?:my|his|her|their)\s+(?:sight|vision|eye)\b[^.?!]{0,15}"
    r"\b(?:has\s+|have\s+|had\s+)?(?:gone|went|is\s+gone)\b"
    r"(?!\s+(?:all\s+)?(?:blurry|blurred|fuzzy|dim|funny|worse|bad|downhill|soft|double)\b)"
    # A black, red, puffy or bloodshot eye is a bruise or an infection, and sight that goes when
    # you stand up is the dizzy-on-standing line, which is a GP's afternoon.
    r"(?![^.?!]{0,25}\b(?:black|red|puffy|swollen|bloodshot|bruised)\b)"
    r"(?![^.?!]{0,25}\bwhen\s+(?:i|he|she|they)\s+(?:stand|stands|get\s+up|gets\s+up|bend|bends|"
    r"stood|got\s+up)\b)"
    # ...and sight that goes and comes back in a second is the faint, not a lost eye: "my sight went
    # for a minute" and "i went blind for a second" are already somebody else's card.
    r"(?![^.?!]{0,25}\b(?:briefly|momentarily|for\s+(?:a|an|a\s+few)\s+(?:second|seconds|moment|"
    r"minute|minutes)|then\s+(?:it\s+)?came\s+back|and\s+came\s+back)\b)",
    r"\b(?:blind|sightless)\s+in\s+(?:my|his|her|their|one)\s+(?:left|right|one)\s+eye\b",
    r"\b(?:gone|going|went)\s+blind\b(?!\s+(?:drunk|fold|folded|baked?))"
    r"(?![^.?!]{0,25}\b(?:briefly|momentarily|for\s+(?:a|an|a\s+few)\s+(?:second|seconds|moment|"
    r"minute|minutes)|then\s+(?:it\s+)?came\s+back|and\s+came\s+back)\b)",
)

# The line says how long the sight has been gone: days or weeks is the clinic today rather than
# the ambulance, and the sight that went this morning is still the 999 call.
SIGHT_A_WHILE = (
    r"\bfor\s+(?:\d+|a\s+couple\s+of|couple\s+of|a\s+few|few|several|many|a|an|two|three|four|"
    r"five|six|seven|eight|nine|ten)\s+(?:days?|weeks?)\b",
    r"\b(?:a\s+couple\s+of\s+(?:days|weeks)|a\s+few\s+(?:days|weeks)|\d+\s+(?:days|weeks))\s+ago\b",
    r"\byesterday\b", r"\blast\s+(?:night|week)\b",
)

STROKE_WEAK_OFF = (
    r"\b(?:cold|freezing|frozen|snow|outside|slept\s+on|sleeping\s+on|lay\s+on|lying\s+on|"
    r"sat\s+on|sat\s+funny|trapped\s+nerve|pins\s+and\s+needles|gym|weights|workout|"
    r"leg\s+day|dentist|filling|anaesthetic|anesthetic|migraine|hungover|drunk|massage|"
    r"blood\s+test|injection|vaccine|jab)\b",
    # An arm that will not come up because of the joint it hangs from is the joint: "i cant lift my
    # arm because of my shoulder" was the stroke card, and so was "since my operation". The older
    # stroke arms above are unaffected - this only stands down the bare lift.
    r"\b(?:can'?t|cannot|can\s+not)\s+lift\s+(?:my|his|her|their)\s+(?:arm|hand)\b"
    r"[^.?!]{0,40}\b(?:because|since|due|after|from|thanks)\b[^.?!]{0,30}"
    r"\b(?:shoulder|rotator|elbow|wrist|sling|cast|crutch|collarbone|collar\s+bone|operation|"
    r"surgery|operated|post-?op|broken|fracture\w*|cracked|pulled|strained|sprain\w*|arthritis|"
    r"arthritic|injured|injury|tendon|ligament|bursitis|frozen)\b",
    r"\b(?:shoulder|rotator|elbow|wrist|sling|cast|collarbone|operation|surgery|broken|"
    r"fracture\w*|strained|sprain\w*|arthritis|injured|injury)\b[^.?!]{0,40}"
    r"\b(?:can'?t|cannot)\s+lift\s+(?:my|his|her|their)\s+(?:arm|hand)\b",
    # An arm that will not lift *to do something* is a shoulder: "i cant lift my arm to reach the
    # shelf" is a frozen shoulder, not a FAST arm.
    r"\blift\s+(?:my|his|her|their)\s+(?:arm|hand)\b[^.?!]{0,20}\bto\s+(?:reach|touch|grab|"
    r"hold|carry|wave|put|scratch|open|close|comb|wash|brush|dry|dress|text|type)\b",
    # A closed or covered eye is not a lost one.
    r"\b(?:one|an?)\s+eye\s+(?:closed|shut|covered|patched|winking)\b",
    # "both" and "two" were in that list too, and a stroke is not always one-sided to look at:
    # "i cant lift both arms" is the FAST test and it was stood down for naming two arms. The
    # words that stay are the body parts a numb line is made of, because those are the ordinary
    # "both hands have gone numb" the stand-down is for.
    r"\b(?:hands|feet|foot|toes|fingers|legs)\b",
    r"\b(?:both|two)\b[^.?!]{0,20}\b(?:numb|dead|tingl\w*|pins\s+and\s+needles|asleep)\b",
    r"\b(?:numb|dead|tingl\w*|pins\s+and\s+needles|asleep)\b[^.?!]{0,20}\b(?:both|two)\b",
    # "arms" was in that list, and it stood down the one arm sign FAST asks for: `i cant lift both
    # arms` never reached the stroke card because it named both. The plural is a stand-down only
    # when it is the numb kind ("my arms have gone numb" is the position it was in), not when the
    # arms will not lift at all.
    r"\barms\b[^.?!]{0,25}\b(?:numb|dead|tingl\w*|pins\s+and\s+needles|asleep|fell\s+asleep)\b",
    r"\b(?:numb|dead|tingl\w*|pins\s+and\s+needles|asleep)\b[^.?!]{0,25}\barms\b",
    # A limb that has gone numb while it was being lain on, sat on or held in one position is the
    # positional kind, and it is the ordinary answer people need: "my leg went dead at the cinema",
    # "my hand went numb holding the shopping", "my arm went numb when i was asleep".
    r"\b(?:sitting|sat|seated|stood|standing|kneeling|crouched|leaning|leant|slouched|"
    r"crossed\s+(?:my|his|her|their)\s+legs|asleep|sleep\w*|in\s+the\s+night|at\s+night|"
    r"overnight|in\s+bed|holding|held|carrying|carried|gripping|gripped|grip|pressed|"
    r"pressure|squeez\w*|shopping|bags?|phone|driving|driven|typing|writing|playing|knitting|"
    r"sewing|guitar|piano|cinema|sofa|desk|train|bus|theatre|meeting|lecture|church|"
    r"sleep\s+on\s+it)\b",
    # A sign with its own everyday cause named is that cause: hayfever for the eye, a cold for the
    # hand, a lens or a screen for the vision.
    r"\b(?:hayfever|hay\s+fever|allerg\w*|conjunctivitis|sty|stye|contact\s+lens|lens|"
    r"cataract\w*|glaucoma|laser\s+surgery|new\s+glasses|optician|"
    r"itch\w*|screen|flu|cold|sinus\w*|infected|infection)\b",
    # ...and so is the thing that was in the eye: "my eye shadow went in my eye" is make-up, and the
    # word *eye* inside "eye shadow" was read as an eye going blind. A lens or a pair of glasses
    # says the same thing about the sight: "i cant see out of one eye without my glasses".
    r"\b(?:eye\s*shadow|eye\s*liner|eyeliner|mascara|make-?up|foundation|moisturis\w*|"
    r"sunscreen|sun\s?cream|shampoo|soap|shower\s+gel|toothpaste|glasses|specs|goggles|"
    r"contact\s+lenses?)\b",
    # Sight that was always like that is not a loss: "i cant see out of one eye since i was a child",
    # "i have been blind in one eye from birth", "all my life", "i have a lazy eye".
    # ...and the same sentence with a count instead of "since": "my sight has been gone in my left
    # eye for years", "i cant see out of my left eye for 3 years" (zippy-kangaroo). Days and weeks
    # are not here, because the sight that went this week is the one to ring about.
    r"\bfor\s+(?:\d+\s+|a\s+few\s+|many\s+|most\s+of\s+my\s+)?(?:years|decades|months)\b",
    # The person can be somebody else: "my son has a droopy shoulder on one side since he was
    # little", "my daughter has had a weak left side since she was a baby", "my husband has been
    # weak on one side since he was a kid" all rang the ambulance while only "since i was" stood
    # down (patient-tangerine, on this PR).
    r"\b(?:since\s+(?:(?:i|he|she|they|we)\s+(?:was|were)\s+|(?:a|an)\s+)"
    r"(?:a\s+)?(?:child|kid|baby|born|birth|little)|"
    r"all\s+my\s+life|my\s+whole\s+life|for\s+as\s+long\s+as\s+i\s+can\s+remember|"
    r"from\s+birth|born\s+(?:blind|with)|was\s+born|as\s+a\s+(?:child|kid|baby)|"
    r"(?:many\s+)?years\s+ago|a\s+lazy\s+eye|lazy\s+eye|always\s+(?:been|had))\b",
    # The same history with no pronoun in it: "ive been blind in my left eye since birth" and "since
    # childhood" were the two phrasings this list missed, and the side word in them put them on the
    # 999 card while "i have been blind in one eye since birth" got the eye test. The lifelong sight
    # row answers both; it reads the same history words (`LIMP_ONGOING`), so standing down here is
    # all that is needed for the line to reach it.
    r"\bsince\s+(?:birth|childhood|i\s+was\s+(?:little|a\s+kid|a\s+baby))\b",
    r"\bborn\s+(?:blind|deaf|with\s+one\s+eye|without\s+(?:an|one)\s+eye)\b",
)

# "not responding" is also what a medicine or a friend's phone does. These say what the person was
# not responding to, and none of them is a collapse: "i am not responding well to the tablets".
RESPOND_SENSE = (r"to\s+(?:(?:the|my|his|her|their|these|those)\s+)?(?:tablets?|pills?|medication|"
                 r"medicine|meds|antibiotics?|injections?|treatment|chemo|therapy|dose|drugs?|"
                 r"texts?|messages?|emails?|calls?|whatsapp|letters?|tickets?|names?|phones?|"
                 r"mobiles?|landline|voicemail|answerphone|doorbell)\b")

# A person, so that "my laptop is not responding" and "the shelf collapsed" stay ordinary.
# Bare "my \w+" is not enough: cakes, shelves and markets are "my" things too.
# The people a line can name. The carers are the ones people live with as much as their family, and
# they were in none of the lists: "my support worker has collapsed", "the care worker is on the
# floor and not responding", "my personal assistant collapsed" all got small talk. The
# grandchildren are the same hole at the other end of the family: "my grandson collapsed" got
# nothing, while "my granddaughter is unresponsive" only reached a card because "unresponsive" is a
# word of its own.
PERSON = (r"(?:mum|mom|mother|dad|father|son|daughter|husband|wife|partner|boyfriend|girlfriend|"
          # Plural as well as singular: "my grandsons collapsed" and "my doctors are" are the same
          # line said about more than one person, and the list is followed by \b in most patterns, so
          # a bare "grandson" missed the plural whole (lilac-apple, #12389).
          r"brother|sister|friend|flatmate|roommate|baby|child|kid|kids|children|"
          r"grand(?:child|children|son|daughter|kid)s?|step(?:child|children|son|daughter)s?|"
          r"boy|girl|man|woman|"
          r"lady|guy|bloke|neighbou?r|colleague|boss|gran|granny|nan|grandad|grandma|grandpa|mate|"
          r"carers?|care\s+workers?|support\s+workers?|social\s+workers?|personal\s+assistants?|"
          r"nurses?|midwives?|midwife|doctors?|gps?|physios?|therapists?|"
          r"patient|pupil|student|teacher|driver|passenger|singer|player|runner|swimmer)")

# The reader asking how to help somebody else: "how do i help a friend who self harms", "how can i
# support my son who cuts himself". It is the helper's card all the way through, and the reader's
# own crisis line was being handed to them instead.
HELP_SOMEONE = (
    r"\b(?:(?:want|wanted|need|needed|trying|try)\s+to\s+)?(?:help|support|approach|talk\s+to|"
    r"deal\s+with)\s+(?:a|an|my|some)\s+" + PERSON +
    r"\b[^.?!]{0,40}\b(?:suicid\w*|self[-\s]?harm\w*|cutting|hurting\s+(?:him|her|them)sel(?:f|ves)|"
    r"wants?\s+to\s+die|starving\s+(?:him|her|them)sel(?:f|ves))\b",
)

# The word "suicide" as a subject rather than a state: "i read an article about suicide", "the
# suicide rate in young men", "i am training to be a suicide counsellor". The bare word is in
# SELF_HARM because a person saying it is usually talking about themselves, and main rang the
# reader's own crisis line at all of these. Only the frames that name the topic are here, and
# the speaker's own distress in the same line still wins (see `not _matches(OWN_DISTRESS, line)`).
SUICIDE_TOPIC = (
    r"\b(?:article|book|documentar(?:y|ies)|film|movie|programme|program|podcast|episode|news|"
    r"paper|report|study|studies|research|statistics?|stats|figures?|rates?|numbers|data|"
    r"training|trained|counsell?or|counselling|counseling|helpline|charity|campaign|awareness|"
    r"prevention|policy|lecture|course|class|essay|thesis|dissertation|talk|seminar|conference|"
    r"day|week|month)\b[^.?!]{0,30}\bsuicid",
    r"\bsuicid\w*\b[^.?!]{0,20}\b(?:rates?|statistics?|figures?|numbers|prevention|awareness|"
    r"campaign|helpline|charity|counsell?or|research|paper)\b",
)

# Shaking a baby is the injury that does not show: `my son wont stop crying and i shook him` was
# nobody's pattern at all. Shaking someone awake, or a rattle, is not this.
SHAKEN = (
    r"\b(?:i|we|he|she|they)\s+(?:shook|shaken|have\s+shaken|has\s+shaken)\s+"
    r"(?:him|her|them|the\s+(?:baby|newborn|infant|toddler|child)|my\s+(?:baby|newborn|infant|son|"
    r"daughter|child|kid|boy|girl|toddler))\b",
    r"\b(?:shook|shaken)\s+(?:the|my|our|his|her)\s+(?:baby|newborn|infant|toddler)\b",
    r"\b(?:baby|newborn|infant|toddler)\b[^.?!]{0,25}\b(?:was|were|got|has\s+been|had\s+been)\s+"
    r"shaken\b",
)

SHAKEN_REPLY = (
    "A baby who has been shaken needs checking now, even if they seem fine: bleeding inside the "
    "head can take hours to show. Ring 999 or 911 if they are floppy, drowsy, sick, fitting or "
    "not feeding normally, otherwise take them to A&E today - and if you feel close to shaking "
    "them, put them down safely and step away for a minute.",
    "That needs a doctor today: shaking a baby can bleed inside the head without a mark on them. "
    "Ring 999 or 911 if they go floppy, drowsy, vomit or fit, and otherwise go straight to A&E - "
    "putting the baby down safely and walking away for a minute is the right move when you are "
    "at the end of your rope.",
)

# Who did it, when it was not the user: `my friend overdosed on purpose` was being answered as
# if the user had taken the pills.
THIRD_PERSON_ACTOR = (
    r"\b(?:he|she|they|my\s+(?:friend|mate|boyfriend|girlfriend|partner|husband|wife|son|daughter|"
    r"child|kid|mum|mom|mother|father|dad|brother|sister|step\w+|cousin|nephew|niece|grandson|"
    r"granddaughter|gran|nan|ex|flatmate|housemate|neighbou?r|colleague|boss|classmate|patient|"
    r"client|lodger|aunt|auntie|uncle))\b",
)

OTHER_SELF_HARM = (
    # Said straight out - on purpose, again, when they are upset - so nothing after the verb
    # softens it: "he cuts himself on purpose" and "he cuts himself when hes upset" are the
    # crisis whatever comes next.
    r"\b(?:my\s+(?!own\b)\w+|he|hes|she|shes|they|someone|somebody)\b.{0,20}\b(?:cuts?|cutting|hits?|"
    r"hitting|burns?|burning|hurts?|hurting|pinch(?:es|ing)|scratch(?:es|ing)|bites?|biting|"
    r"bangs?|banging|starves?|starving|scalds?|scalding)\s+(?:him|her|them)sel(?:f|ves)\b"
    r"(?=\s+(?:on\s+purpose|again\b|when\s+(?:he|she|they)\s*(?:'s|s|is|are|was|were)\b|"
    r"to\s+(?:hurt|punish|cope)|because\b))",
    # A body verb with nothing after it. An accident says how it happened - "he cut himself on
    # glass", "she burnt herself on the iron", "he cut himself shaving" - so those keep their
    # first aid. `hurt` and `bite` are out of this arm on purpose: "my son hurt himself" is a
    # playground fall and "my daughter bites herself" is a two year old, so only the framing arm
    # above can make those a crisis ("he hurts himself when hes upset").
    r"\b(?:my\s+(?!own\b)\w+|he|hes|she|shes|they|someone|somebody)\b.{0,20}\b(?:cuts?|cutting|hits?|"
    r"hitting|burns?|burning|hurting|pinch(?:es|ing)|scratch(?:es|ing)|"
    r"bangs?|banging|starves?|starving|scalds?|scalding)\s+(?:him|her|them)sel(?:f|ves)\b"
    r"(?!\s+(?:on|with|in|at|by|while|against|accidentally|shaving|cooking|chopping|opening|"
    r"playing|making|ironing|cycling|running|trying)\b)",
)

# A bare "they" is only about people when something in the line, or the turn before it, says who
# they are: "my sister is in a bad way" then "they are going to kill themselves" is a real report,
# while "i'm strangling the life out of my houseplants" then the same words are about the plants.
# A child named by an age is a person: "my 8 month old has a fever and a rash", "my 2 year old
# has a rash and a temperature", "my toddler has a fever and a rash". None of those words is in
# PERSON, so the fever-and-rash card never saw a person in the line and the glass test - the one
# thing a parent can do themselves - was never offered. It is one gate, so the age is added to
# the gate rather than to every row that asks "is this about a body".
AGE_PERSON = (r"(?:\d{1,2}[\s-]*(?:month|months|week|weeks|year|years|yr|yrs|mo|mth|mths)"
              r"[\s-]*old\b|"
              r"(?:\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
              r"[\s-]*(?:months?|weeks?|years?|yrs?)[\s-]+old\b|"
              r"\b(?:newborn|newborns|toddlers?|infants?|teenagers?|teens?|preschoolers?|"
              r"schoolboy|schoolgirl)\b)",)

# Blue lips or a person going blue means not enough oxygen, which is a 999 call; "I feel blue" is
# a mood, and a blue dress, a blue sky and blue cheese are things.
# How parents write it: "a blue tinge round his lips", "a tinge of blue round the mouth". A tinge
# is only cyanosis when a body part is what has it, so a tinge in the water or the paint is colour.
BLUE_TINGE = (
    r"(?=.*\b(?:blue|grey|gray)\s+tinge\b)(?=.*\b(?:lips?|mouth|face|skin|fingers?|"
    r"fingertips?|hands?|feet|toes|nails?|cheeks?|tongue|gums)\b)",
    r"(?=.*\btinge\s+of\s+(?:blue|grey|gray)\b)(?=.*\b(?:lips?|mouth|face|skin|fingers?|"
    r"fingertips?|hands?|feet|toes|nails?|cheeks?|tongue|gums)\b)",
)

BLUE = (
    # "went" is how most people say it about what has already happened: "he had a coughing fit
    # and went blue" was reaching the laundry answer, not this one.
    r"\b(?:going|went|turned|turning|gone|goes|turns?)\s+blue\b",
    r"\b(?:lips?|face|fingertips?|fingers?|nail\s?beds?|around\s+the\s+mouth|skin|"
    r"cheeks?|tongue|gums|hands?|feet|toes|legs?|mouth)\b.{0,20}"
    r"\b(?:blue|grey|gray)\b",
    *BLUE_TINGE,
    r"\b(?:blue|grey|gray)\s+(?:around\s+the\s+lips?|round\s+the\s+lips?|in\s+the\s+face|lips?)\b",
    # "i'm blue all over" says the colour has spread without naming a part or a verb: the whole of
    # them changed, which is the widest way of saying a person has gone blue.
    r"\b(?:blue|grey|gray)\s+all\s+over\b",
    # A person whose colour has changed: the state verb has to sit right next to them, so a jogger
    # someone needs, a jumper their daughter wears or a kitchen they want is not a colour change.
    r"\b(?:i|i'm|he|he's|she|she's|they|they're|we|you|someone|somebody|"
    r"(?:my|the|our)\s+" + PERSON + r"|" + PERSON + r")\s+"
    r"(?:is|was|are|were|looks?|looking|looked|appears?|seems?|becomes?|becoming|"
    r"has\s+gone|had\s+gone|went|turned|turning|going|gone|getting|gets)\s+"
    r"(?:(?:a|bit|really|very|so|all|quite|pale|grey|gray|cold|clammy|sweating|confused|"
    r"shivering|breathless|struggling|limp|floppy|sleepy|and)\s+){0,4}"
    r"(?:blue|grey|gray)\b",
)

# Any pet, singular or plural: "my puppies gums look grey" and "my rabbits gums look grey" were
# both reaching the 999 card for a person short of oxygen. A pet's colour is the vet's case, and
# the pet table answers it in the pet's own words.
PET_ANY = (
    r"\b(?:dog|dogs|puppy|puppies|pup|pups|cat|cats|kitten|kittens|rabbit|rabbits|bunny|bunnies|"
    r"hamster|hamsters|guinea\s+pig|guinea\s+pigs|parrot|parrots|budgie|budgies|bird|birds|"
    r"ferret|ferrets|horse|horses|pony|ponies|tortoise|tortoises|snake|snakes|lizard|lizards|"
    r"gerbil|gerbils|rat|rats|pet|pets)\b",
)

# The colour of a body that has changed is not overridden by a shopping word later in the line.
BLUE_STRONG = (
    r"\b(?:going|turned|turning|gone|goes|go|turns?|getting|gets|is\s+turning)\s+"
    r"(?:blue|grey|gray)\b",
    r"\b(?:lips?|face|fingertips?|fingers?|nail\s?beds?)\b.{0,20}\b(?:blue|grey|gray)\b",
    # The colour spread over the whole of them is not a mood: "i'm blue all over" is not sad.
    r"\b(?:blue|grey|gray)\s+all\s+over\b",
)

# Cold is a cause for the lips too when the line says so: "my lips are blue with cold" is a person
# on a cold platform. A child, a breath, a chest, or a person not responding are not explained by
# the cold, and a bare "my lips have gone blue" keeps ringing.
LIPS_COLD = (
    r"\b(?:lips?|mouth|face)\b[^.!?]{0,30}\b(?:cold|freezing|frozen|chilly|perishing|the\s+snow|"
    r"the\s+sea|the\s+pool|the\s+swim|a\s+swim|swimming)\b",
    r"\b(?:cold|freezing|frozen|chilly)\b[^.!?]{0,30}\b(?:lips?)\b",
    r"\b(?:out\s+in\s+the\s+cold|in\s+this\s+cold|from\s+the\s+cold)\b",
)

# "I have a cold" is an illness, not the weather on a platform: a cold does not turn lips blue, so
# blue lips beside one are the oxygen running out. On main "i have a cold and my lips are blue" got
# the honey-and-lemon reply, and the weather shapes below excuse a colour the line never explains.
# Only a cold somebody *has* counts - "my lips are blue from the cold" and "out in a cold wind"
# are the weather and stay stood down.
COLD_ILLNESS = (
    r"\b(?:have|has|had|having|got|caught|catch|fighting|full\s+of|down\s+with|"
    r"coming\s+down\s+with|suffering\s+from|come\s+down\s+with|getting)\s+"
    r"(?:a|the|my|his|her|their|this|such\s+a|a\s+really)\s+(?:\w+\s+){0,2}cold\b",
    r"\ba\s+cold\b[^.!?]{0,20}\b(?:chest|flu|fever|temperature|wheeze|coughing)\b",
    r"\b(?:my|his|her|their|the)\s+(?:\w+\s+){0,2}cold\b[^.!?]{0,20}"
    r"\b(?:wont\s+shift|worse|gone\s+to\s+my\s+chest)\b",
)

# Food changes colour on its own: a tomato gone mouldy, milk on the turn, a chicken past its date.
# The colour of a thing in the fridge is not a person short of oxygen, so a food word with no person
# and no lips or face in the line stands the arm down. Only concrete food nouns go here - a vague
# "turned" or "gone off" would excuse a hand that has turned blue.
BLUE_FOOD = (
    r"\b(?:tomato(?:es)?|cheese|milk|chicken|beef|pork|lamb|meat|fish|ham|bacon|bread|toast|"
    r"pickle(?:s|d)?|chutney|kimchi|sauerkraut|"
    r"dough|batter|rice|pasta|potato(?:es)?|onion(?:s)?|garlic|fruit|apple(?:s)?|banana(?:s)?|"
    r"orange(?:s)?|lemon(?:s)?|berries|strawberr(?:y|ies)|grape(?:s)?|cabbage|lettuce|salad|"
    r"vegetables?|soup|sauce|smoothie|juice|wine|beer|yogurt|yoghurt|cream|butter|egg(?:s)?|"
    r"mushroom(?:s)?|courgette(?:s)?|cake|biscuit(?:s)?|leftovers?)\b",
)

# The person who changed colour, as the subject of it: "my son went blue", "i turned blue". A bare
# "i" anywhere in the line is not enough - "my garlic went blue when i pickled it" is the garlic.
BLUE_PERSON_SUBJECT = (
    r"\b(?:i|i'm|i\s+am|he|he's|she|she's|they|they're|we|we're|you|someone|somebody|anyone|"
    r"baby|child|children|kid|kids|toddler|infant|boy|girl|man|woman|mum|mom|mother|dad|father|"
    r"son|daughter|husband|wife|partner|friend|gran|grandma|grandad|nan|"
    r"(?:my|the|our)\s+" + PERSON + r")\b[^.!?]{0,20}\b"
    r"(?:is|was|are|were|went|gone|goes|going|turned|turning|turns?|looks?|looking|looked|"
    r"appears?|seems?|become|becomes|becoming|getting|gets)\s+(?:\w+\s+){0,3}"
    r"(?:blue|grey|gray)\b",
)

# ...and anyone else in the line who could be the one gone blue, however it is worded: "my chicken
# has gone blue and so has my son" is still a child short of oxygen. The speaker alone is not that
# person, because "when i pickled it" puts an i in every pickle line.
BLUE_OTHER_PERSON = (
    r"\b(?:he|she|him|her|they|them|his|hers|their|someone|somebody|anyone|man|woman|boy|girl|"
    r"child|children|baby|babies|toddler|patient|kid|kids|mum|mom|mother|dad|father|son|daughter|"
    r"husband|wife|partner|boyfriend|girlfriend|brother|sister|friend|gran|grandma|grandad|"
    r"grandpa|nan|uncle|aunt|niece|nephew|colleague|neighbour|neighbor|people|men|women|workers?|"
    r"guests?|everyone|anybody)\b",
)

# Cloth and dye go blue in the wash: "my jeans went blue in the wash" was answered with the 999
# card, and the thing that changed colour was the fabric. A person's lips, face or body part in the
# same line keeps it ringing.
BLUE_CLOTH = (
    r"\b(?:jeans|jumper|jumpers|top|tops|shirt|shirts|t-?shirts?|blouse|dress|dresses|trousers|"
    r"pants|shorts|skirt|coat|jacket|hoodie|cardigan|socks?|tights|knickers|underwear|bra|pyjamas|"
    r"pjs|washing|laundry|whites|wash|fabric|clothes|clothing|cloth|wool|denim|cotton|linen|"
    r"curtains?|sheets?|towels?|bedding|duvet|cover|cushion|carpet|rug|dye|dyed|dyeing|bleach|"
    r"paint|paintbrush|pen|ink|felt\s?tip|highlighter)\b",
)

BLUE_FINE = (
    r"\b(?:feel|feeling|feels|felt)\s+(?:a\s+bit\s+|really\s+|so\s+|very\s+)?(?:blue|grey|gray)\b",
    r"\b(?:i'?m|i\s+am)\s+(?:a\s+bit\s+|really\s+|so\s+)?blue\b",
    r"\b(?:mood|day|monday|week|film|movie|song|album|book)\b.{0,15}\b(?:blue|grey|gray)\b",
    r"\b(?:blue|grey|gray)\s+(?:mood|day|monday|car|door|paint|paintwork|wall|walls|sky|carpet|"
    r"sofa|dress|shirt|top|jeans|coat|eyes?|bin|bag|towel|fabric|nail\s+varnish|polish|cheese|"
    r"milk|ink|pen|light|screen|toothbrush|hair|tie|shoes?|trainers?|hat|scarf)\b",
    r"\bblue\s+cheese\b",
    r"\b(?:room|rooms|wall|walls|ceiling|kitchen|bathroom|bedroom|hall|hallway|lounge|floor|"
    r"woodwork|paintwork|curtains?|blinds?|lighting|light)\b[^.?!]{0,25}\b(?:blue|grey|gray)\b",
    r"\b(?:paint|painting|painted|dye|dyed|sprayed|spray)\b[^.?!]{0,25}\b(?:blue|grey|gray)\b",
    r"\b(?:wearing|wears?|bought|buy|buying|got|getting|choose|chooses|chose|chosen|picked|pick|"
    r"like|likes|love|loves|prefer|prefers|want|wants|wanted|need|needs|needed|ordered|order|"
    r"matches|match)\b[^.?!]{0,25}\b(?:blue|grey|gray)\b",
    r"\b(?:blue|grey|gray)\b[^.?!]{0,20}\b(?:paint|dye|shirt|dress|top|coat|jeans|hat|scarf|"
    r"shoes|trainers|car|door|wall|carpet|sofa|bag|towel|team|kit|badge|light|card|ticket|"
    r"folder|mug|cup|plate|bike|bicycle|pram|buggy|room|bedroom|bathroom)\b",
)

SELF_TALK = (
    r"\b(?:tell|tells|telling|told|ask|asks|asking|asked|say|says|saying|said|think|thinks|thinking|"
    r"thought|remind|reminding|reminded|convince|convincing|convinced|promise|promising|promised|"
    r"let|letting|made|make|making|allow|allowing|allowed|permit|permitting|permitted|forgive|"
    r"forgiving|gave|give|giving|reassure|reassuring|reassured|comfort|comforting|talk|talking|"
    r"keeping)\b[^.?!]{0,16}\bmy\s*self\b",
)

# A school or work morning is the reason a person is hard to wake, not the collapse itself:
# "my son cant wake up for school" is an ordinary grumble. Real signs further along the line
# ("and he is not breathing", "blue lips", "floppy") keep it an emergency.
ROUTINE_WAKE = (
    # The routine named by its place or its time: "wake up for school", "wake up for the bus".
    r"\b(?:can'?t|cant|cannot|won'?t|wont|isn'?t|is\s+not|not)\s+wake\s+(?:up\s+)?"
    r"(?:for|to|before|in\s+time\s+for|on\s+time\s+for)\s+"
    r"(?:school|work|college|uni|university|nursery|childminder|the\s+(?:school\s+)?(?:bus|train)|"
    r"(?:his|her|their|my|an?)\s+(?:exam|exams|test|appointment|meeting|interview|shift|flight|"
    r"lesson|lecture|class|early\s+start))\b",
    # "he can't wake up to get to school", "he can't wake up to get ready for work"
    r"\b(?:can'?t|cant|cannot|won'?t|wont)\s+wake\s+(?:up\s+)?to\s+get\s+(?:to|ready\s+for)\s+"
    r"(?:school|work|college|uni|university|nursery)\b",
    r"\b(?:for|to)\s+(?:school|work|college|uni|university|nursery)\s+(?:this\s+)?"
    r"(?:morning|today)\b.{0,20}\b(?:won'?t|wont|can'?t|cant)\s+wake\b",
)

WAKE_RED = (
    r"\b(?:not|isn'?t|stopped)\s+breathing\b", r"\bblue\b", r"\blips\b",
    r"\b(?:seizure|fit|fits|limp|floppy|unconscious|unresponsive|pulse|ambulance)\b",
    # A child who cannot be roused and is also feverish, pale or has been sick is ill, not
    # grumpy about school. The reason clause only makes the line routine when nothing else is wrong.
    r"\b(?:temperature|fever|feverish)\b", r"\bburning\s+up\b",
    r"\bhot\s+to\s+(?:the\s+)?touch\b",
    r"\b(?:grey|gray|pale|clammy|sweating)\b", r"\bvomit\w*\b",
    r"\b(?:been\s+)?sick\s+(?:all\s+night|all\s+day|twice|three\s+times|since)\b",
    # A routine reason only wins while the person is simply hard to wake. A stroke is the sign
    # that has to beat it: "he cant wake up to get ready for work and he is not making sense" was
    # read as a school morning because "to get ready for" was the whole of what the line said.
    r"\bslurr\w*\b", r"\bnot\s+making\s+sense\b", r"\bdoesn'?t\s+make\s+sense\b",
    r"\bconfused\b", r"\bcan'?t\s+(?:speak|talk)\b", r"\bface\s+(?:is\s+|looks\s+)?droop\w*\b",
    r"\b(?:one\s+side|his\s+side|her\s+side)\s+(?:is\s+)?(?:weak|limp|dropping)\b",
)

# The verb in front of a fit is written as a contraction as often as not: "he's fitting", "hes
# fitting", "she's seizing". A pattern that wants the word "is" on its own reads none of them, so
# `hes fitting` got "Thanks for telling me" while `my son is fitting` rang 999 - the same fit, one
# apostrophe apart. A contraction with a person in it is the verb; a contraction with a thing in it
# is not, so "its fitting nicely" and "thats fitting for the shed" stay out of it.
_COPULA = (r"(?:is|are|was|were|keeps?|kept|started|he'?s|hes|she'?s|shes|they'?re|theyre)")
# Somebody fitting a kitchen is not somebody fitting: the thing after the verb is what is being
# fitted, and `my son is fitting the new kitchen` rang the seizure card before this.
_FITTING_A_THING = (
    r"(?!\s+(?:in|on|into|up|together|his|her|their|my|your|our|the|a|an|"
    r"new|some|another|kitchen|bathroom|windows?|doors?|floor|carpet|wardrobe|cabinets?|shelves|"
    r"shelf|tiles|laminate|boiler|units?|radiators?|dishwasher|oven|cooker|shower|toilet|sink|"
    r"sofa|bed|lino)\b)")
SEIZURE = (
    r"\bseizur\w*\b", r"\b(?:had|has|having|have)\s+a\s+fit\b", r"\bconvuls(?:ing|ions?)\b",
    r"\b" + _COPULA + r"\s+fitting\b" + _FITTING_A_THING,
    # "he is seizing" is the same fit in the other word; "the engine is seizing up" is not.
    r"\b" + _COPULA + r"\s+seizing\b(?!\s+up)",
)

# A child who has a fit every few months has epilepsy a doctor already knows about, so it is not
# tonight's emergency - and it is not a story that needs the GP either.
FIT_ROUTINE = (
    r"\b(?:every\s+(?:few|couple\s+of|so\s+many)\s+(?:months|weeks|years)|twice\s+a\s+year|"
    r"once\s+a\s+year|a\s+(?:few|couple)\s+of\s+times\s+a\s+year|now\s+and\s+(?:then|again)|"
    r"from\s+time\s+to\s+time|keppra|epilep\w*)\b",
    # The pattern the family knows: "he has a fit when he is tired", "she fits if she misses her
    # tablets". The trigger is in the line, so this is the same known condition as "every few
    # months", not tonight's first one.
    r"\bfits?\s+(?:when|if|whenever)\b[^.?!]{0,30}\b(?:tired|unwell|poorly|ill|stressed|"
    r"miss\w*|forget\w*|skip\w*|meds?|medicine|tablets?|keppra)\b",
)

# The figure of speech that is not a fit even when the line is old: "a seizure laughing" and "a fit
# of coughing" stay ordinary, but "had a seizure when he was a baby" is a time, not a trigger, so
# the whole-line figurative guard would swallow the one story this rule is for.
SEIZURE_STORY_GUARD = (
    r"\bseizure\s+(?:laughing|from\s+laughing)\b",
    r"\bseizures?\s+of\s+(?:laughter|laughing|giggl\w*|coughing|sneez\w*)\b",
    r"\b(?:had|having|have|get)\s+a\s+seizure\s+(?:laughing|at\s+that)\b",
    r"\bfits?\s+of\s+(?:cough\w*|sneez\w*|giggl\w*|laughter|laughing|the\s+giggles|"
    r"temper|pique)\b",
    r"\b(?:nearly|almost|thought\s+i'?d)\s+(?:had\s+)?(?:a\s+)?(?:seizure|fit)\b",
)

# The signs that keep a routine fit an ambulance: the family's epilepsy today is still a fit that
# will not stop, and a child who cannot breathe after one is a call whatever the history.
FIT_STILL_RINGS = (
    r"\b(?:can'?t|cannot|not|stopped|isn'?t|stop)\s+breath", r"\bwon'?t\s+stop\b",
    r"\bisn'?t\s+stopping\b", r"\bkeeps?\s+going\b", r"\bunconscious\b", r"\bcollapsed\b",
    r"\bon\s+the\s+floor\b", r"\bconvuls\w*", r"\bturning\s+blue\b", r"\bblue\s+lips\b",
    r"\bstiff\b", r"\bshaking\s+all\s+over\b", r"\bambulance\b",
)

# Their own childhood is history people carry and have long since had looked at: "i had a fit when
# i was a kid" is not a question for a doctor now, and it is not an emergency either. Someone
# else's childhood fit is still somebody's GP question - a parent asking about their child.
CHILDHOOD_FIT = (
    r"\b(?:as|when\s+i\s+was)\s+(?:a\s+|an\s+)?(?:kid|child|baby|toddler|tot|infant|nipper|"
    r"young|little|small|at\s+school)\b",
    r"\b(?:in|during)\s+my\s+childhood\b",
    r"\bwhen\s+i\s+was\s+(?:about\s+)?(?:one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|1|2|3|4|5|6|7|8|9|10|11|12)\b",
)

# A first fit a week ago is still not a wait: it is seen today, not "mentioned to the GP".
# Days ago, not hours ago: a fit last night or this morning is still the ambulance, as guidance has
# it for a first fit today. This is the gap where the appointment would be far too slow.
FIT_THIS_WEEK = (
    r"\b(?:last\s+(?:week|weekend|friday|saturday|sunday|monday|tuesday|wednesday|thursday)|"
    r"earlier\s+this\s+week|the\s+other\s+(?:day|night)|yesterday|"
    r"a\s+(?:few|couple\s+of)\s+days?\s+ago|\d+\s+days?\s+ago|on\s+(?:monday|tuesday|"
    r"wednesday|thursday|friday|saturday|sunday))\b",
)

# "i nearly had a seizure when i saw the price" is a figure of speech, not a fit.
SEIZURE_FIGURATIVE = (
    r"\bseizure\s+(?:laughing|from\s+laughing)\b",
    r"\b(?:had|having|have|get)\s+a\s+seizure\s+(?:laughing|when|at\s+that)\b",
    r"\b(?:nearly|almost|thought\s+i'?d)\s+(?:had\s+)?(?:a\s+)?(?:seizure|fit)\b",
    # "a fit of coughing" is a cough and "a fit of sneezing" is hayfever.
    r"\bfit\s+of\s+(?:cough\w*|laughter|laughing|sneez\w*|giggles|itch\w*|temper|pique)\b",
)

# A choking fit that is over, or that never stopped the person talking, is not the airway
# emergency: the cough is what clears it.
MILD_CHOKE = (
    r"\bi\s+chok(?:ed|ing)\s+on\s+(?:(?:my|your|his|her|their|a|an|some|the)\s+)?(?:own\s+)?"
    r"(?:drink|tea|coffee|water|juice|"
    r"beer|wine|ice|pill|tablet|vitamin|crisp|chip|crumb|sweet|grape|bit\s+of\s+\w+|mouthful|"
    r"spit(?:tle)?|saliva|it)\b",
    # "i choked at the dentist" is a thing that happened and is over, the same as choking on a
    # mouthful of tea. The place is what makes it over; someone still in trouble says so.
    r"\bi\s+chok(?:ed)\s+(?:at|in|during)\s+(?:the\s+)?\w+",
    r"\bi\s+(?:nearly|almost)\s+choked\b", r"\bchoked?\s+(?:on\s+)?laughing\b",
    # "i choked up at the end of the film" is a feeling, not a blocked airway, so "choked up" is
    # left to the figure-of-speech rows above and to the ordinary reply.
)

# The signs that this choke is not over: no air, no voice, a colour change, or someone on the
# floor. "still coughing" is the good sign and stays out of this list.
CHOKE_RED = (
    r"\b(?:can'?t|cannot|couldn'?t|unable\s+to)\s+(?:breathe|breath|brethe|speak|talk|make\s+a\s+sound)\b",
    r"\b(?:went|turned|going|turning|is|looks?)\s+blue\b", r"\b(?:lips?|face)\s+(?:are|is|going)\s+blue\b",
    r"\b(?:still|now|and)\s+choking\b", r"\b(?:collapsed|unconscious|gone\s+limp|floppy)\b",
    r"\b(?:holding|clutching|grabbing)\s+(?:his|her|their|my)\s+throat\b",
    r"\bchoking\s+(?:and|but)\s+(?:can'?t|cannot)\b",
)

# A mouthful that went down the wrong way is the cough-and-sip reply only while they can still
# breathe: `i choked on a bit of toast and i cant breathe` was getting "that usually sorts
# itself", which is the wrong advice for a blocked airway.
CHOKE_STILL_RED = (
    r"\bcan'?t\s+breathe\b", r"\bcannot\s+breathe\b", r"\bcan'?t\s+(?:speak|talk|get\s+(?:any\s+)?"
    r"(?:air|breath))\b", r"\bnot\s+breathing\b", r"\b(?:turning|going|gone)\s+blue\b",
    r"\b(?:lips|face|mouth)\s+(?:are\s+|'re\s+|is\s+)?(?:blue|grey|gray)\b",
    r"\bno\s+air\b", r"\b(?:airway|throat)\s+(?:is\s+|'s\s+)?(?:blocked|closing|swollen)\b",
    r"\bstill\s+choking\b", r"\bstuck\s+in\s+(?:my|his|her|their)\s+throat\b",
    r"\b(?:passed|passing|faint|fainted|collapsed|unconscious)\b",
)

WENT_BLUE_IDIOM = (
    r"\b(?:went|going|go|turn(?:ed|s)?|turning)\s+blue\s+in\s+the\s+face\b.{0,60}"
    r"\b(?:laugh\w*|joke\w*|crying|shouting|screaming|kidding|breath\w*)\b",
    r"\b(?:laugh\w*|joke\w*|crying|holding\s+(?:my|his|her|your)\s+breath|"
    r"held\s+(?:my|his|her|your)\s+breath)\b.{0,60}"
    r"\b(?:went|going|go|turned?|turning)\s+blue\s+in\s+the\s+face\b",
    # The same colour without "in the face": "i went blue holding my breath", "my toddler holds his
    # breath until he goes blue". A held breath and a laughing fit both turn a face blue and both
    # come back in seconds, and neither is the oxygen running out on its own.
    r"\b(?:hold|holds|holding|held)\s+(?:my|his|her|their|your|the)?\s*breath\b[^.?!]{0,60}"
    r"\b(?:go\w*|went|turn(?:ed|s|ing)?|turning)\s+blue\b",
    r"\b(?:go\w*|went|turn(?:ed|s|ing)?|turning)\s+blue\b[^.?!]{0,60}"
    r"\b(?:hold|holds|holding|held)\s+(?:my|his|her|their|your|the)?\s*breath\b",
    r"\b(?:went|going|go|goes|turn(?:ed|s|ing)?|turning)\s+blue\b[^.?!]{0,50}"
    r"\b(?:laugh\w*|joke\w*|kidding|giggling)\b",
    r"\b(?:laugh\w*|joke\w*|kidding|giggling)\b[^.?!]{0,50}"
    r"\b(?:went|going|go|goes|turn(?:ed|s|ing)?|turning)\s+blue\b",
)

# Cold hands and feet are the surgery's question, not the ambulance's. Every arm here is a cause
# or a thing, never a body part on its own.
WENT_BLUE_FINE = (
    r"\braynaud\w*\b", r"\bin\s+the\s+cold\b", r"\bwhen\s+(?:it'?s|its)\s+cold\b",
    r"\bwith\s+(?:the\s+)?cold\b", r"\bafter\s+(?:a\s+)?(?:swim|cold\s+swim|bath)\b",
    r"\bthe\s+wash\b", r"\bwash(?:ing)?\s+machine\b", r"\bjeans\b", r"\bbruise\b",
    r"\bcold\b", r"\bfreez\w*", r"\bwinter\b", r"\bsnow\b", r"\bice\b",
)

BLUE_COLD_CAUSE = (
    r"\bwith\s+(?:the\s+)?cold\b", r"\bin\s+the\s+cold\b", r"\bwhen\s+(?:it'?s|its)\s+cold\b",
    # "in this cold" is where the person is standing, which is the warm-up answer rather than the
    # echo it used to get ("my lips are blue in this cold" was a shrug).
    r"\bin\s+(?:this|that)\s+cold\b",
    r"\bafter\s+(?:a\s+)?(?:swim|cold\s+swim|bath)\b", r"\bfrom\s+the\s+cold\b",
    # Said the way people say it: "my baby has blue lips and hes cold", "ive got blue lips and im
    # freezing". The breathing and the waking red flags still take the line back to the 999 card.
    r"\b(?:he|she|they|i|we|it)\s*(?:'s|s|is|are|am|was|were|feels?|felt)\s+"
    r"(?:so\s+|very\s+|really\s+|a\s+bit\s+|already\s+|freezing\s+)?cold\b",
    r"\bfreezing\b", r"\bshiver\w*", r"\bhypotherm\w*",
)

# A hand in a machine is an ambulance and a machine nobody may switch on again: "my hand is stuck
# in the blender" was answered with "Annoying. Is it every time, or only now and then?" The list
# is the machines people lose fingers to; a jar, a ring and a zip are not on it.
MACHINE = (
    r"\b(?:blender|food\s+processor|liquidis(?:er|or)|mincer|meat\s+grinder|mangle|shredder|"
    r"chipper|wood\s+chipper|washing\s+machine|tumble\s+dryer|spin\s+dryer|drill|circular\s+saw|"
    r"chainsaw|bench\s+saw|lathe|hydraulic\s+press|conveyor|escalator|elevator|mower|lawnmower|"
    r"strimmer|hedge\s+trimmer|auger|cement\s+mixer|pasta\s+machine)\b"
)

STUCK_MACHINE = (
    r"\b(?:hand|hands|arm|arms|finger|fingers|thumb|wrist|foot|leg|toe|toes|hair|knee|head|"
    r"clothes|sleeve|jumper|coat|scarf|glove|jewellery|ring)\b[^.?!]{0,40}\b(?:stuck|caught|"
    r"trapped|jammed|wedged|pinned|crushed|sucked\s+in)\b[^.?!]{0,40}\b" + MACHINE,
    r"\b" + MACHINE + r"\b[^.?!]{0,40}\b(?:has|have|got|took|caught|grabbed|crushed|sucked|"
    r"chewed)\b[^.?!]{0,30}\b(?:my|his|her|their|the)\s+(?:hand|arm|finger|fingers|sleeve|hair|"
    r"jumper|coat)\b",
    # The machine first and the person's body second: "i put my hand in the washing machine and now
    # its stuck". A body or a garment has to be in the line, so "the washing machine is stuck on the
    # spin cycle" is still a repair job.
    r"\b" + MACHINE + r"\b[^.?!]{0,40}\b(?:stuck|caught|trapped|jammed|wedged|crushed)\b"
    r"(?=[^.?!]{0,70}\b(?:my|his|her|their|the)\s+(?:hand|hands|arm|arms|finger|fingers|thumb|"
    r"wrist|foot|feet|leg|legs|toe|toes|hair|knee|head|sleeve|jumper|coat|scarf|glove)\b)",
    # The body, then the machine, then the state: "i put my hand in the washing machine and now its
    # stuck". The order people speak in is not the order of the other arms.
    r"\b(?:hand|hands|arm|arms|finger|fingers|thumb|wrist|foot|feet|leg|legs|toe|toes|hair|knee|"
    r"sleeve|jumper|coat|scarf|glove)\b[^.?!]{0,40}\b" + MACHINE +
    r"\b[^.?!]{0,40}\b(?:stuck|caught|trapped|jammed|wedged|crushed)\b",
)

BLEEDING = (
    r"\b(?:bleeding|blood)\s+(?:badly|heavily|everywhere|a\s+lot|so\s+much|profusely)\b",
    r"\bso\s+much\s+blood\b", r"\bblood\s+everywhere\b", r"\bspurting\b", r"\b(?:won't|wont|doesn't)\s+stop\s+bleeding\b.{0,40}\b(?:hour|hours|pressure|bandage)\b",
    r"\b(?:stabbed|stab\s+wound)\b", r"\bdeep\s+cut\b", r"\b(?:cut|slit|sliced)\s+(?:(?:my|his|her|their|a)\s+)?(?:wrist|neck|throat|thigh)s?\b",
    r"\b(?:bleeding|blood)\s+(?:through|soaking)\s+(?:the|my)\s+(?:bandage|towel|clothes)\b",
    r"\bcan't\s+stop\s+the\s+bleeding\b",
    # The volume said before the noun. "There is a lot of blood" and "lots of blood and it wont
    # stop" were the shrug: the amount was on the line, it just came before the word "blood"
    # instead of after it, which is the only order the arm above reads. A nose, a period, the
    # lavatory, a sick bowl, a film or a costume has its own answer, so those words keep this
    # card off the line, and so does a cut that is already named with a site - "i've cut my hand
    # badly and there's a lot of blood" is a cloth pressed on it and a look, which is the cut
    # card's own advice, not an ambulance the moment it is said.
    r"^(?!.*\b(?:nose|nostril|nosebleed|period|periods|menstrual|poo|stool|faeces|feces|wee|"
    r"urine|vomit|vomited|sick|nappy|diaper|film|films|movie|movies|tv|telly|programme|show|"
    r"episode|scene|game|games|book|novel|documentary|costume|fake|prop|ketchup|paint|"
    r"cut|cuts|cutting|gash|gashes|sliced|slices|wound|wounded|grazed|scratched)\b).*?"
    r"\b(?:a\s+lot\s+of|lots\s+of|loads\s+of|puddles?\s+of|pools?\s+of|so\s+much|"
    r"that\s+much)\s+blood\b",
    # The blood that will not stop is the ambulance whatever else is named: the cloth is not
    # holding it.
    r"^(?!.*\b(?:nose|nostril|nosebleed|period|periods|menstrual|poo|stool|faeces|feces|wee|"
    r"urine|vomit|vomited|sick|nappy|diaper|film|films|movie|movies|tv|telly|programme|show|"
    r"episode|scene|game|games|book|novel|documentary|costume|fake|prop|ketchup|paint)\b).*?"
    r"(?:\b(?:the\s+)?blood\s+(?:won'?t|wont|doesn'?t|doesnt|isn'?t)\s+stopp?(?:ed|ing)?\b|"
    r"\bcan'?t\s+(?:get\s+)?(?:it|the\s+bleeding|the\s+blood)\s+to\s+stop\b)",
    r"\b(?:slash(?:ed|es|ing)?|slit)\s+(?:(?:my|his|her|their|a)\s+)?(?:arms?|wrists?|hands?|legs?|thighs?|neck|throat)\b",
)

# The water that is not water: "i nearly drowned laughing", "i was drowning in paperwork", "i
# drowned my sorrows". On its own the drowning case rang on the first of those.
DROWNING_HYPERBOLE = (
    r"\b(?:nearly|almost)\s+drowned\s+(?:laughing|in\s+(?:it|them|tears))\b",
    r"\bdrown(?:ing|ed)?\s+in\s+(?:paperwork|work|debt|emails?|chores|admin|deadlines?|"
    r"homework|bills|laundry|it|them|wine|beer|sorrows)\b",
    r"\bdrowned\s+(?:my|our|his|her|their)\s+sorrows\b",
)

# A person said to be drowning right now, with no water word anywhere in the line: "hes drowning",
# "the boy is drowning", "i think shes drowning". `WATER_DANGER` above needs a body of water or a
# going-under, and a person watching somebody drown types neither - on main those lines went to the
# what-to-drop-first answer (@magenta-pine). The subject has to be a person: "the garden is drowning
# in weeds" and "im drowning in emails" are how people say a bad week.
WATER_DROWNING_NOW = (
    r"\b(?:he|she|they|hes|shes|theyre|he's|she's|they're)\b[^.?!]{0,15}\bdrown(?:ing|s)\b",
    r"\b(?:the|a|my|our)\s+(?:kid|kids|baby|child|children|boy|girl|toddler|little\s+one|son|"
    r"daughter|husband|wife|partner|mum|mom|dad|father|mother|friend|mate|brother|sister|"
    r"neighbour|neighbor|man|woman|lad|person|someone|somebody)\b[^.?!]{0,15}"
    r"\bdrown(?:ing|s)\b",
    r"\b(?:is|are)\s+drowning\b",
    # The speaker alone only when the water is named: "im drowning in the sea". A bare
    # "im drowning" and "i feel like im drowning" are how people say they are overwhelmed, and
    # main answers those with the overwhelm card, which is the better reply - a CPR card for
    # somebody in that state is a false alarm (@sky-tuna, #6259).
    r"\b(?:im|i'?m|i\s+am)\s+drowning\b[^.?!]{0,25}\b(?:water|sea|ocean|pool|lake|river|"
    r"canal|bath|bathtub|tub|waves?|deep\s+end|swimming|under\s+the\s+surface)\b",
    r"\b\d+\s+(?:year\s+old|yo)\b[^.?!]{0,15}\bdrowning\b",
)

# A thing dropped in the water was drowning on main, because the speaker's own verb and the water
# word are both there: "i dropped my phone in water" got "say you were under the water and could not
# breathe" (@white-ruler). The thing has to be the object of the drop, and nobody else may be in
# trouble in the same line.
WATER_THING_DROPPED = (
    r"\b(?:dropped|drops?|slipped|slips?|tipped|tips?|knocked|knocks?|kicked|kicks?|threw|"
    r"left|lost|dunked|dipped)\s+(?:[\w']+\s+){0,2}(?:phone|mobile|keys?|wallet|purse|watch|"
    r"glasses|book|towel|bag|coat|hat|money|passport|teddy|dummy|nappy|remote|toy|ball|boot|"
    r"trainer|tools?|sponge|cloth|loaf|bread|toast|cutlery|mug|cup)\b",
)

# ...unless somebody is still in the water in the same sentence: "i dropped my phone in the water
# and my son went under" is a boy under the water, not a phone.
WATER_PERSON_TOO = (
    r"\b(?:went|goes|gone|sank|sunk|sinking|fell|fallen|falls?)\s+(?:in|into|under)\b[^.?!]{0,20}"
    r"\b(?:water|pool|sea|river|lake|pond|canal|bath)\b",
    r"\b(?:went|goes|gone)\s+under\b",
    r"\b(?:not\s+breathing|no\s+pulse|unresponsive|blue\s+lips|limp)\b",
    r"\b(?:my|his|her|their|our)\s+(?:son|daughter|child|baby|kid|boy|girl|toddler|husband|"
    r"wife|partner|friend|mate|mum|mom|dad|brother|sister)\b[^.?!]{0,25}\b(?:drowning|"
    r"drowned|under|in\s+the\s+water)\b",
)

# ...and the drowning that is not one: a workload, a bill, a garden, a plate of chips and the joke
# about drowning your sorrows. A thing said to be drowning is the thing's own answer.
WATER_DROWNING_FINE = (
    r"\bdrown\w*\s+(?:in\s+|under\s+)?(?:emails?|work|works|debt|debts|paperwork|admin|bills?|"
    r"tears|weeds|jobs?|chores?|stress|sorrows|booze|wine|beer|noise|it\s+all|everything|"
    r"the\s+lot|chips|gravy|ketchup|sauce|salt|vinegar|cream|syrup|oil)\b",
    r"\b(?:plant|plants|garden|lawn|grass|seedlings?|crops?|flowers?|houseplant|basil|tomato\w*|"
    r"hanging\s+basket)\b",
    r"\blaugh(?:ing|ed|s)\b",
    r"\bdrowned\s+(?:out|by\s+the\s+noise)\b",
    # "i feel like im drowning", "it feels like im drowning" - a feeling said with "like", and the
    # overwhelm card is the answer however the rest of the line reads.
    r"\b(?:feel|feels|felt|feeling|like)\s+(?:im|i'?m|i\s+am|like\s+im)\s+drown",
)

WATER_NOT_A_PERSON = (
    # the water in the wrong place: a road, a cellar and a car are flooded, not drowning
    r"\b(?:roads?|streets?|garden|lawn|fields?|basement|cellar|kitchen|hall|drive|driveway|"
    r"lane|path|patio|bridge|cars?|vans?|shed|garage|town|village|pitch|allotment|"
    r"house|flat|loft|attic|cupboard)\b",
    r"\b(?:flood\w*|burst\s+pipe|leak\w*)\b",
    # ...and going under a bus or a lorry is a road, not water: "i almost went under a bus" was
    # reading the word "under" as the drowning card.
    r"\bunder\s+(?:a|an|the)\s+(?:bus|car|lorry|truck|van|tram|train|taxi)\b",
    # and the thing that went under is a thing: "my phone went under the water" is a phone. Only
    # the thing as the subject counts, so "my son went under the water with his phone" is still a
    # person in the water.
    r"\b(?:phone|mobile|keys?|wallet|purse|watch|glasses|book|towel|shoes?|socks?|clothes|"
    r"washing|dishes|plates?|mug|cup|kettle|loaf|bread|food|dinner|rice|pasta|eggs?|toys?|ball|"
    r"dummy|nappy|ring|coin|remote|bag|coat|hat|money|passport|boot|trainer|teddy|blanket)\b"
    r"\s+(?:has\s+|had\s+)?(?:went|goes|gone|fell|falls?|slipped|drops?|dropped|is|was|got|"
    r"gets)\b",
    # ...and a boat is a boat only when it is the thing that went in: "my son fell off the boat into
    # the sea" is a person in the water.
    r"\b(?:boats?|dingh(?:y|ies)|canoes?|kayaks?|ship|ferry|raft)\b\s+(?:has\s+|had\s+)?"
    r"(?:went|goes|gone|sank|sunk|tipped|turned\s+over|capsized|is|was|got)\b",
)

# The speaker is the one in the water, so the reply has to be written to them: "i fell in the river"
# was answered "say they were in the water, start CPR if they're not breathing", which the person it
# happened to cannot follow (@cream-eel). The verb has to tie to the water, so "i was walking the dog
# and he fell in" is still about him.
WATER_SELF = (
    r"\bi\b[^.?!]{0,25}\b(?:fell|fallen|slipped|slips?|went|goes|gone|sank|sunk|jumped|dropped|"
    r"tipped|tumbled|drowned|drowning|got\s+pulled|got\s+dragged|was\s+pulled|was\s+pushed|"
    r"was\s+dragged|was\s+thrown|was\s+tipped|got\s+knocked)\b[^.?!]{0,30}\b(?:water|pond|"
    r"river|lake|sea|pool|canal|reservoir|loch|harbour|harbor|lagoon|deep\s+end|shallow\s+end|"
    r"bath|tub|under)\b",
    r"\b(?:pushed|pulled|threw|thrown|dragged|tipped|shoved|knocked)\s+me\s+(?:in|into|under)\b",
    # somebody else's hands, and the speaker is the wet one
    r"\b(?:pulled|hauled|dragged|lifted|fished|got|gets)\s+me\s+out\s+of\s+the\s+(?:water|pond|"
    r"river|lake|sea|pool|canal)\b",
    r"\bi\s+(?:got|was|were|am)\s+(?:pushed|pulled|thrown|dragged|tipped|shoved|knocked)\b",
    r"\bwe\b[^.?!]{0,25}\b(?:went|goes|gone|fell|slipped|sank)\b[^.?!]{0,20}\bunder\b",
)

WATER_HUMAN = (
    r"\b(?:baby|babies|newborn|infant|son|daughter|child|children|kid|kids|boy|girl|toddler|"
    r"little\s+one|niece|nephew|grandson|granddaughter|husband|wife|partner|mum|mom|mother|dad|"
    r"father|brother|sister|friend|mate|lads?|guys?|man|woman|person|people|he|she|him|her|"
    r"them|they|someone|somebody|anyone|i|me|my\s+(?:son|daughter|child|baby|boy|girl|"
    r"husband|wife|partner|mum|mom|dad|friend|brother|sister)|we|us)\b",
)

WATER_FINE = (
    r"\b(?:swimming\s+(?:lesson|lessons|class|club|badge)|learnt?\s+to\s+swim|"
    r"learning\s+to\s+swim|splash\w*|playing|playing\s+about|having\s+fun|laughing|"
    r"came\s+up|came\s+back\s+up|popped\s+up|surfaced|came\s+to\s+the\s+surface|"
    r"loves?\s+(?:going\s+under|the\s+water)|"
    r"likes?\s+(?:going\s+under|the\s+water)|enjoys\s+the\s+water)\b",
)

# A head that will not go under is a lesson, a fear or a shower, not a drowning: "i cant put my
# head under water", "my son wont put his head under the water", "i struggle to put my head under
# water" and "i cant swim under water" were the 999 card, because `WATER_DANGER` reads bare
# `under water` and `WATER_DANGER_PERSON` then finds the `i` / `my son` in the same line. The head
# is what is being put under, or the line says plainly that the person cannot or will not go under.
# Nothing about the breath or the body accompanies it in that case, and the two arms that do say
# something is still wrong in the water (`WATER_URGENT`, `WATER_BREATH_RED`) keep the card.
WATER_HEAD_FEAR = (
    r"\b(?:can'?t|cant|cannot|couldn'?t|won'?t|wont|unable|struggl\w*|scared|afraid|"
    r"terrified|frightened|nervous|hate|hates|hated|panic\w*|refus\w*|"
    # The feeling has a noun and a verb as well as an adjective, and the noun is how a fear is
    # usually introduced: "i have a fear of going under water", "my son has a fear of going
    # under water", "i dread going under water" and "i fear going under water" were all the
    # drowning card ("say he was in the water"), with nobody in the water.
    r"fear|fears|feared|fearful|phobia|phobic|dread|dreads|dreaded|dreading)\b[^.?!]{0,40}"
    r"\b(?:under\s*(?:the\s+)?(?:water|surface)|underwater|go(?:ing|es)?\s+under)\b",
    r"\b(?:put|puts|putting|get|gets|getting|duck|ducks|ducking|dip|dips|dipping|stick|"
    r"sticks|sticking|hold|holds|holding|keeping|lower\w*)\b[^.?!]{0,20}\bhead\b"
    r"[^.?!]{0,20}\b(?:under\s*(?:the\s+)?(?:water|surface)|underwater)\b",
    # a head going under while swimming is the swim itself, in either word order
    r"\bhead\b[^.?!]{0,20}\b(?:under\s*(?:the\s+)?(?:water|surface)|underwater)\b"
    r"[^.?!]{0,25}\b(?:swim\w*|pool|lesson\w*|bath|shower|float\w*|splash\w*)\b",
    r"\b(?:swim\w*|pool|lesson\w*|bath|shower|float\w*|splash\w*)\b[^.?!]{0,25}\bhead\b"
    r"[^.?!]{0,20}\b(?:under\s*(?:the\s+)?(?:water|surface)|underwater)\b",
    # ...and the same block said about getting in at all: "my daughter is scared to jump in the
    # pool" rang 999 because `WATER_DANGER` reads `jump in the pool` and `WATER_DANGER_PERSON`
    # finds the daughter. A child who will not jump in is a lesson, and nobody is in the water.
    # `of` or `to` is what makes it a refusal rather than a fact: "my son cant swim and fell in
    # the pool" and "she cant swim and went in the sea" are people in the water, and `cant swim`
    # alone must never stand this card down. Only a fear, a refusal or a panic gets here, and
    # `WATER_IN_NOW` below keeps even those out when the line also says somebody went in.
    # a fear carries `of` or `to` ("scared to jump in the pool", "afraid of getting in"), which
    # is what keeps "my son cant swim and fell in the pool" out; a refusal does not need one
    # ("he wont jump in the pool"). `cant` is in neither: "cant swim" is the person's own words
    # about themselves, not a refusal to get in.
    r"\b(?:scared|afraid|frightened|nervous|terrified|panic\w*|dread\w*)\s+(?:of|about|to)"
    r"\s+(?:\w+\s+){0,2}(?:jump\w*|get|getting|go|going|dive|diving|swim\w*)\s+"
    r"(?:in|into)\s+(?:the\s+)?(?:water|pool|sea|lake|deep\s+end|shallow\s+end)\b",
    r"\b(?:won'?t|wont|refus\w*|won'?t|hates?|hated)\s+(?:\w+\s+){0,2}(?:jump\w*|get|"
    r"getting|go|going|dive|diving|swim\w*)\s+(?:in|into)\s+(?:the\s+)?(?:water|pool|"
    r"sea|lake|deep\s+end|shallow\s+end)\b",
    # a child who screams when water reaches their face is not in trouble either
    r"\b(?:scream\w*|cry\w*|hate[sd]?|scared|afraid|frightened|terrified|nervous)\b"
    r"[^.?!]{0,30}\bwater\b[^.?!]{0,20}\b(?:face|head|hair)\b",
    # Holding your breath on purpose is what a swimmer does, and a line that says it happens
    # when the head goes under is a habit, not an event: "i hold my breath when i go under
    # water", "i always hold my breath when i go underwater" and "he holds his breath when he
    # goes under" were all the 999 card ("say you were under the water and could not breathe").
    # The `when` clause is the whole point - "i held my breath too long and went under" and "i
    # couldnt hold my breath and went under" name no habit, so neither is this arm's.
    r"\b(?:hold|holds|holding|held)\b[^.?!]{0,25}\b(?:my|his|her|their|your)\s+breath\b"
    r"[^.?!]{0,35}\b(?:when|whenever|every\s+time|each\s+time|before)\b[^.?!]{0,30}"
    r"\b(?:go|goes|going|went|dive\w*|dove|jump\w*|swim\w*|duck\w*|put\w*|get\w*|"
    r"stick\w*|dip\w*)\b[^.?!]{0,20}\b(?:under|underwater|in)\b",
)

# ...and somebody has actually gone in: a line that says that is a body in the water whatever
# fear or refusal it also carries. "my son cant swim and fell in the pool" and "she cant swim and
# went in the sea" lost the 999 card to a fear arm that read only the `cant`.
WATER_IN_NOW = (
    # a jump or a dive that happened: "scared to jump in the pool" is a refusal, and the fear arm
    # above has to keep its 999 off, so the bare `jump` of "too scared to jump" cannot be here.
    # "he cant swim and he jumped in" names no water at all, so this arm has to stand alone.
    r"\b(?:jumped|jumping|dived|diving|dove|leapt|leaped|sank|sunk|sinking)\b"
    r"[^.?!]{0,15}\b(?:in|into|under)\b",
    # `in` or `into` only: "my head goes under water when i swim" is the lesson, not a body in
    # the water, and `under` is the word the fear lines themselves use.
    r"\b(?:fell|fallen|falls?|went|goes|gone|slipped|slips?|tipped|tumbled|pushed|dropped)\b"
    r"[^.?!]{0,20}\b(?:in|into)\b[^.?!]{0,20}\b(?:water|pool|sea|lake|river|canal|"
    r"pond|deep\s+end|shallow\s+end|bath)\b",
    r"\b(?:is|hes|shes|theys|they're|was|were|are|am)\s+(?:still\s+)?(?:in|under)\s+"
    r"(?:the\s+)?(?:water|pool|sea|lake|river|canal|pond|deep\s+end)\b",
    # not `under the water` on its own: "i wont put my head under the water" is the lesson this
    # fence exists for. Going under is the motion words above, and `WATER_STILL_BAD` has the rest.
    r"\b(?:went\s+under|gone\s+under|deep\s+end|shallow\s+end)\b",
)

# What is still going on in the water: the breath, the colour, the stillness, and the asking.
WATER_URGENT = (
    r"\b(?:breath\w*|blue|limp|unresponsive|not\s+moving|not\s+breathing|still\s+not|"
    r"hasn'?t\s+(?:come|moved)|didn'?t\s+come|still\s+under|under\s+for|"
    r"get\s+(?:him|her|them)\s+(?:up|out)|find\s+(?:him|her|them)|"
    r"can'?t\s+(?:see|swim|get|wake)|cant\s+(?:see|swim|get|wake)|"
    r"struggl\w*|scream\w*|panic\w*|swim\s+back|swallow\w*)\b",
)

# A plant, a phone or a plate of chips can be drowned; a person cannot. Main answered "i nearly
# drowned my plant", "the plant nearly drowned" and "i nearly drowned the basil" with "Ring 999 or
# 911 immediately and say they were in the water. Start CPR". The verb has to be followed straight
# away by the thing, so "i nearly drowned trying to save my plant" is still the person's card.
DROWNED_THING = (
    r"\b(?:drown(?:ed|ing)?)\s+(?:my|our|the|his|her|their|this|that|a)\s+"
    r"(?:plant|plants|houseplant|houseplants|seedlings?|basil|tomato(?:es)?|chillies|chilli|"
    r"flowers?|lawn|grass|garden|window\s+box|hanging\s+basket|pot\s+plant|succulent|cactus|"
    r"fern|herbs?|crops?|phone|chips|toast|cereal|salad|sorrows|cares|fears|sulks|fire)\b",
    r"\b(?:the|my|our)\s+(?:plant|plants|houseplant|seedlings?|basil|lawn|garden|flowers?|herbs?|"
    r"crops?)\b[^.?!]{0,20}\b(?:nearly\s+)?drown(?:ed|ing)?\b",
)

HANGING = (
    *PERSON_HANGING,
    r"\b(?:hung|hanged|hang|hanging)\s+(?:himself|herself|themselves|my\s*self)\b"
    # ...and the one figure of speech that names hanging: "he hung himself out to dry". Only the
    # idiom, and only directly after the reflexive. A chore is not an idiom - "she hung herself
    # doing the laundry" and "she hung herself washing out the laundry" are a person in a utility
    # room, and a line like that must never fall through to small talk (purple-camel, #5545). The
    # washing has to be the thing hung with a "the" in front of it: "she hung herself the washing"
    # is a washing line.
    r"(?!\s+(?:upside|on\s+the\s+(?:bars|swing|wall)|from\s+the\s+(?:bars|swing)|"
    r"out\s+to\s+dry|up\s+to\s+dry|the\s+(?:washing|laundry|clothes)\b))",
    r"\b(?:hung|hanged|hang|hanging)\s+(?:him|her|them)\b\s+(?:from|in|on|to)\s+(?:the\s+|a\s+)?"
    r"(?:rafters|beam|balcony|banister|railing|railings|stair(?:s|case)|ceiling|hook|tree|treehouse|"
    r"door|bridge|window|bars|shower|garage|shed|loft|basement|bathroom|bedroom)\b",
    # "my brother is hanging, i just found him": the scene, not the act, is how people say it.
    r"\b(?:is|was|'s)\s+(?:hanging|hung)\b.{0,25}\bfound\b",
    r"\bfound\s+(?:him|her|them|my\s+\w+)\s+hanging\b",
    # Finding somebody strangled is the same scene as finding them hanging, and it was a shrug.
    r"\bfound\s+(?:him|her|them|my\s+\w+)\s+strangl\w+\b",
    r"\bstrangl(?:ed|ing)\s+(?:me|him|her|them|himself|herself|themselves|someone|somebody)\b",
    # A possessive needs the person named after it. The arm used to take `my`, `his`, `her` and
    # `their` on their own, so "im strangling my houseplants" - and "strangling my tomatoes",
    # "strangling my budget" - was answered "Get them down or take the pressure off the neck now":
    # first aid for a hanging, for a person whose plants were dying. Everything a person can be
    # strangled by is already in `STRANGLE_LOOKALIKE`; this is the other direction, the person
    # doing it, and a hand on a throat always lands on a person.
    r"\bstrangl(?:ed|ing)\s+(?:my|his|her|their|our)\s+" + ABUSER + r"\b",
    r"\bstrangulation\b", r"\bnoose\b",
    r"\bstrangl(?:ed|ing)\b.{0,20}\bneck\b",
    r"\b(?:ligature|rope|belt)\s+(?:round|around|tight\s+round)\s+(?:his|her|their|my)\s+neck\b",
)

SNAKE_LOOKALIKE = (
    r"\b(?:snake\s+plant|snake\s+plants|snakes?\s+and\s+ladders|snake\s+print|snake\s+skin|"
    r"snake\s+charmer|snake\s+bite\s+kit|snake\s+in\s+the\s+garden|saw\s+a\s+snake|"
    r"grass\s+snake|slow\s+worm|snake\s+in\s+(?:my|the)\s+(?:boot|shed|grass|pond))\b",
    r"\b(?:stung|bit|bitten)\s+by\s+the\s+(?:price|bill|cost|tag)\b",
)

# A hoof or a horn is a blow with weight behind it, and the bruise hides what it did inside. Main
# answered `my son was kicked by a horse` with the biting-correction script.
ANIMAL_KICK = (
    r"\b(?:horse|pony|horses|cow|cows|bull|bullock|donkey|mule|llama|alpaca)\b[^.?!]{0,30}"
    r"\b(?:kicked|kick|kicks|trampled|trampling|stamped|stood\s+on|stood\s+on\s+(?:my|his|her|me))\b",
    r"\b(?:kicked|trampled|stamped\s+on|stood\s+on)\s+by\s+(?:a|an|the|my|his|her)\s*"
    r"(?:horse|pony|cow|bull|donkey|mule)\b",
)

# A loop on a blind or a curtain cord is a strangulation for a child. Main answered
# `my son got tangled in the blind cord` with how to wind a cable tidy.
BLIND_CORD = (
    r"\b(?:blind|blinds|curtain|curtains|venetian|roman)\s+cords?\b[^.?!]{0,25}"
    r"\b(?:neck|round|around|tangled|caught|wrapped|hanging|choking|tight)\b",
    r"\b(?:got|caught|tangled|wrapped|hanging|choking|stuck)\b[^.?!]{0,25}"
    r"\b(?:blind|curtain|venetian|roman)s?\s*cords?\b",
    r"\b(?:tangled|caught|wrapped|hanging|stuck)\s+(?:in|on|round|around)\s+the\s+"
    r"(?:blind|blinds|curtain|curtains)\b",
)

# The reader is the one who was strangled. `HANGING` takes these lines too - `strangled me` is one
# of its arms - and every reply it has is written for a bystander: `he strangled me` was told to
# "get them down", which the person reading it cannot do, and `i was strangled by my husband` was
# the echo "Noted: you were strangled by your husband." Strangulation is the strongest predictor of
# being killed by a partner, so it gets a reply of its own, said to the person it happened to.
STRANGLED_SELF = (
    r"\bstrangl\w*\s+me\b",
    r"\bthrottl\w*\s+me\b",
    # the disclosure in the past tense, which reached the echo instead
    r"\bi\s+(?:was|got|been|have\s+been|had\s+been)\s+strangl\w+",
    r"\bi\s+(?:was|got|been)\s+throttl\w+",
    r"\bstrangled\s+by\s+(?:my|him|her|them|an?)\b",
    # The same hand on the throat in the words main answered with something else: a choke, a grip
    # on the neck, a hand laid on it. "he choked me" got the abuse card ("Please get a real person
    # involved"), "he held me by the neck" got the shrug, and "he strangled my neck" got the
    # cut-them-down card, which the person typing cannot do.
    r"\b(?:he|she|they|someone|somebody|this\s+(?:man|woman|guy|lad|girl|bloke)|"
    r"a\s+(?:man|woman|bloke|lad|lady|girl|guy|stranger|boy)|my\b[^.?!]{0,12}\b" + ABUSER + r")"
    r"[^.?!]{0,25}\b(?:choked|chokes|is\s+choking)\s+me\b",
    r"\b(?:grab(?:s|bed|bing)?|held|holds|holding|seiz(?:ed|es|ing)|pinned|shoved|pushed)\s+me\s+by\s+"
    r"the\s+(?:throat|neck)\b",
    r"\b(?:put|puts|putting|laid|laying|lay|wrapped|wrapping|wraps|had|has|slid|slipped|clamped|"
    r"locked|forced)\s+(?:his|her|their|both)\s+"
    r"(?:hands?|fingers|fist|forearm)\s+(?:round|around|on|across|to)\s+my\s+(?:throat|neck)\b",
    # Both arms round the neck is also how a hug is written ("my daughter wrapped her arms around my
    # neck"), so the arms keep the card only for the throat, where a hug does not reach.
    r"\b(?:put|puts|putting|wrapped|wrapping|wraps|threw|had|got|slid|slipped|clamped)\s+"
    r"(?:his|her|their|both)\s+arms?\s+(?:round|around|on|across)\s+my\s+throat\b",
    # A throat is not where a hand rests, so any hand on it is the card: "a hand round my throat",
    # "someone put a hand on my throat".
    r"\b(?:a\s+hand|his\s+hands?|her\s+hands?|their\s+hands?|someone'?s\s+hands?|"
    r"somebody'?s\s+hands?)\s+(?:round|around|on|across)\s+my\s+throat\b",
    # The neck is, though: "his hand on my neck" is as likely a cuddle, and it was the card. Round
    # the neck or with a grip word beside it, it is the card again.
    r"\b(?:a\s+hand|his\s+hands?|her\s+hands?|their\s+hands?|someone'?s\s+hands?|"
    r"somebody'?s\s+hands?)\s+(?:round|around)\s+my\s+neck\b",
    r"\b(?:a\s+hand|his\s+hands?|her\s+hands?|their\s+hands?|someone'?s\s+hands?|"
    r"somebody'?s\s+hands?)\s+(?:on|across)\s+my\s+neck\b"
    r"(?=[^.?!]{0,30}\b(?:tight(?:ly|en\w*)?|grip\w*|squeez\w*|press\w*|pin(?:ned|ning|s)?|"
    r"clamp\w*|hard|crush\w*|chok\w*)\b)",
    # The neck named instead of "me": "he strangled my neck", "he was choking my neck".
    r"\bstrangl(?:ed|ing|es|e)\s+my\s+(?:neck|throat)\b",
    r"\bchok(?:ed|ing|es)\s+my\s+(?:neck|throat)\b",
    # A grip that failed is still a hand on the throat, and it was a shrug.
    r"\b(?:nearly|almost)\s+(?:got|was|been|had\s+me)\s+(?:strangled|throttled|choked)\b",
)

# ...and the thing that is doing the strangling. A tight pair of jeans, the heat or the workload are
# said with the same words as a hand on the throat, and main answered every one of them with "Ring
# 999 or 911 now". No person is on this list, so "my husband strangled me" keeps the card.
STRANGLE_THING_SUBJECT = (
    r"\b(?:the|this|that|my|our|his|her|their)\s+(?:[a-z']+\s+){0,2}(?:jeans|trousers|shirt|top|"
    r"bra|shoes?|boots|socks?|belt|watch|coat|jumper|hoodie|heat|humidity|workload|work|job|"
    r"debt|debts|bills?|traffic|stress|anxiety|panic|pressure|paperwork|bureaucracy|admin|"
    r"commute|queue|noise|mortgage|rent|council|kids?|in-?laws?|exams?|revision|"
    r"deadlines?|red\s+tape|system|money|poverty|town|city|weather)\b[^.?!]{0,20}"
    r"\bstrangl(?:e|es|ing|ed)\b",
    # The same thing with no word in front: "work is strangling me", "money is strangling us".
    r"\b(?:jeans|trousers|shirt|bra|heat|humidity|workload|work|job|debt|bills?|traffic|stress|"
    r"anxiety|panic|pressure|paperwork|bureaucracy|admin|commute|queue|noise|mortgage|rent|"
    r"council|kids|in-?laws|exams?|revision|deadlines?|red\s+tape|system|money|poverty|"
    r"life|everything)\b(?:\s+[a-z']+){0,2}\s+(?:is|are|was|were|keeps?)\s+strangl(?:ing|ed)\b",
)

# Who the hoof landed on. "my horse kicked me" has the person after the verb; "i was kicked by a
# horse" and "i got trampled by a cow" have them before it, in the passive, and that shape was
# reading as the animal because nothing follows the verb at all. A person told to ring the vet
# about their own ribs is worse than the shrug main gave them.
KICKED_PERSON = (
    r"\b(?:kicked|kicks?|trampled|trampling|stamped\s+on|stood\s+on)\s+(?:me|us|my|our)\b",
    r"\b(?:i|we)\s+(?:was|were|got|have\s+been|had\s+been|'ve\s+been)\b[^.?!]{0,25}"
    r"\b(?:kicked|trampled|stamped\s+on|stood\s+on|sat\s+on|thrown|tossed)\b",
    r"\b(?:my|his|her|their|our)\s+(?:son|daughter|child|kid|baby|boy|girl|husband|wife|partner|"
    r"mum|mom|mother|dad|father|brother|sister|friend|nan|gran|grandad|grandma)\b[^.?!]{0,25}"
    r"\b(?:was|were|got|had\s+been)\b[^.?!]{0,15}\b(?:kicked|trampled|stamped\s+on|stood\s+on)\b",
)

# Your own cut, said as a cut rather than as a wish: "i cut myself", "i cut my arm", "i keep
# cutting my arm". The crisis line is the right answer to the bare one; this is what tells the
# branch below whether there is a wound to press on as well.
SELF_CUT = (
    r"\b(?:cut|cutting|sliced|slashed|gashed|slit|nicked|scratched)\s+"
    r"(?:my\s*self|my\s+(?:arm|arms|wrist|wrists|hand|hands|leg|legs|thigh|thighs|finger|"
    r"fingers|foot|feet))\b",
    # The habit without an object: "i keep cutting and the blood wont stop".
    r"\b(?:i\s+)?(?:keep|keeps|kept|am|im|'m)\s+(?:on\s+)?cutting\b",
)

# A cut that is still coming through the cloth, said either way round: "the blood wont stop",
# "it wont stop bleeding", "blood everywhere".
CUT_NOT_STOPPING = (
    r"\b(?:won'?t|wont|doesn'?t|doesnt|didn'?t|didnt|not|never|keeps?)\s+stop(?:ped|ping)?\s+"
    r"(?:bleeding|blood|the\s+blood)\b",
    r"\b(?:the\s+)?blood\s+(?:wont|won'?t|doesnt|doesn'?t)\s+stop\b",
    r"\bblood\s+(?:everywhere|every\s*where|a\s+lot|lots|badly|heavily|pouring)\b",
    r"\bsoaking\s+(?:through|the)\b",
)

# Petrol on your hands after filling the car, or a jumper that smells of the pump, is not a leak
# in the building: that is a smell you wash off. The leak reply is for gas in a room.
GAS_ON_YOU = (
    r"\b(?:my|his|her|their|your|the)\s+(?:hands?|clothes|shirt|coat|jumper|fingers|gloves|cloths?)\b"
    r"[^.?!]{0,25}\b(?:smell|smells|smelling|smelt|reek|reeks|stink|stinks)\b",
    r"\b(?:smell|smells|smelling|smelt)\s+(?:of\s+|like\s+)?gas\b"
    r"[^.?!]{0,20}\b(?:on|from)\s+(?:my|his|her|their|your)\s+"
    r"(?:hands?|clothes|shirt|coat|jumper|fingers|gloves)\b",
)

# Gas left running is the same emergency with the smell left out: the person is standing in a room
# that may be filling up. "I left the gas on", "I turned the hob on and forgot", "did I leave the
# hob on" all end the same way - knob off, windows and doors open, nothing that can spark.
# "on the table" is not "on all night", and "on for the boiler" is someone's pilot light.
GAS_ON_NOT_RUNNING = (
    r"(?!\s+(?:the\s+)?(?:table|side|counter|worktop|shelf|floor|bed|sofa|desk|hook|wall|windowsill|"
    r"ledge|rack|top\s+shelf|board|tray|plate|doorstep))"
    r"(?!\s+(?:for|to\s+keep)\s+(?:the\s+)?(?:boiler|pilot|pilot\s+light|heating|hot\s+water|"
    r"water|radiators?|fire|shower|bath|oven|cooker|fridge|freezer|central\s+heating))\b"
)

GAS_LEFT_ON = (
    r"\b(?:left|leave|leaving|forgot|forgotten|think\s+i\s+(?:left|turned))\b[^.?!]{0,30}"
    r"\b(?:gas|hob|burner|ring|cooker)\b[^.?!]{0,12}\bon\b" + GAS_ON_NOT_RUNNING,
    r"\b(?:turned|switched|put)\s+(?:the\s+)?(?:gas|hob|burner|ring|cooker)\b[^.?!]{0,15}"
    r"\b(?:on|up)\b[^.?!]{0,25}\b(?:forgot|forgotten|walked\s+away|left\s+it)\b",
    r"\b(?:did|have|had)\s+(?:i|you|we)\s+\b(?:leave|left)\b[^.?!]{0,20}\b(?:gas|hob|burner|cooker)\b"
    r"[^.?!]{0,10}\bon\b" + GAS_ON_NOT_RUNNING,
    r"\b(?:gas|hob|burner|ring\s+on\s+the\s+cooker)\b[^.?!]{0,20}\b(?:is\s+)?(?:still\s+)?on\b"
    r"[^.?!]{0,30}\b(?:cant|cannot|can'?t|not\s+sure|no\s+idea|don'?t\s+know)\b",
    r"\b(?:gas|hob|burner)\b[^.?!]{0,20}\b(?:hissing|running|going\s+and\s+i)\b",
)

# A gas smell from last year, or at somebody else's flat, is a story rather than a leak here.
GAS_PAST = (
    r"\b(?:smelt|smelled|smelling|smell)\b[^.?!]{0,40}\b(?:last\s+(?:year|week|month|winter|summer)|"
    r"years?\s+ago|months?\s+ago|weeks?\s+ago|yesterday|ages\s+ago|once|when\s+i\s+was|"
    r"as\s+a\s+kid|at\s+(?:my|her|his|our)\s+\w+'s)\b",
    r"\b(?:last\s+(?:year|week|month)|years?\s+ago|when\s+i\s+was|ages\s+ago)\b[^.?!]{0,30}"
    r"\b(?:smelt|smelled|smell)\b",
)

# Somebody in the house, or following the user.
INTRUDER = (
    r"\b(?:someone|somebody|a\s+man|a\s+person|intruder|burglar)\s+(?:is\s+)?(?:trying\s+to\s+get\s+in|"
    r"breaking\s+in|breaking\s+into\s+(?:the|my|our)\s+(?:house|flat|home|kitchen|bedroom)|climbing\s+(?:in|through|over)|"
    r"in\s+(?:the|my)\s+(?:house|flat|home|garden|kitchen|living\s+room)|inside\s+(?:the|my)\s+house)\b",
    r"\b(?:there's|there\s+is|theres)\s+(?:someone|somebody|a\s+man)\s+(?:in|inside|at)\s+(?:the|my)\s+"
    r"(?:house|flat|home|garden|window)\b"
    # A parcel, a takeaway or a letter means a delivery, not a break-in.
    r"(?!\s+(?:with|holding|delivering)\s+(?:a|the|my)\s+(?:parcel|package|delivery|letter|clipboard|"
    r"takeaway|pizza|parcels))",
    # "someone is at the door" on its own is a delivery, so a following-me claim needs a real place.
    r"\b(?:a\s+man|someone|somebody)\s+(?:is\s+)?following\s+me\b(?!\s+(?:on|around)\s+"
    r"(?:instagram|insta|twitter|x|tiktok|facebook|snapchat|social|the\s+internet|online))",
    # Somebody at the door is a delivery; somebody breaking the door down is not.
    r"\b(?:someone|somebody|a\s+man)\s+(?:is\s+)?(?:banging|pounding|kicking|hammering|smashing)\s+"
    r"(?:on\s+)?(?:the|my)\s+(?:door|window)\b",
    r"\b(?:someone|somebody|a\s+man|he|she|they)(?:'s|\s+is)?\s+(?:trying|tried)\s+to\s+"
    # "breaking in his new boots" is not a break-in.
    r"(?:get\s+in|break\s+(?:in\b(?!\s+(?:his|her|their|my|your|these|those|new|a\s+new)\s)|"
    r"the\s+door|down\s+the\s+door))\b",
    r"\b(?:i\s+think|i\s+heard)\s+(?:someone|somebody)\s+(?:is\s+)?(?:in|inside|downstairs|upstairs)\b",
)

# Breathlessness that comes on with effort, and nothing else, is ordinary: "i cant breathe when i
# run for the bus" is a fitness question, not an ambulance.
# In British English "gasping" is the ordinary word for very thirsty: gasping for a brew, a cuppa,
# a pint of water. The breathing case keeps the bare word for the real gasp, and this guard takes
# the drink out of it.
GASPING_THIRST = (
    r"\bgasping\s+(?:for|at)\s+(?:" + _A_THIRST + r")",
    r"\bgasping\s+(?:for|at)\s+(?:something\s+to\s+drink|something\s+to\s+eat)\b",
    r"\bgasping\s+(?:after|during|at)\s+(?:a\s+|that\s+|the\s+|my\s+)?(?:run|jog|workout|gym|"
    r"session|match|game|swim|cycle|bike\s+ride|climb|hill|walk|climbing|going\s+up|running)\b",
    # An engine gasps for fuel and a phone gasps for power; neither is a throat.
    r"\bgasp\w*\s+(?:for|on)\s+(?:fuel|petrol|diesel|power|charge|bandwidth|data)\b",
)

EXERTION = (
    r"\b(?:after|during|while|when|whenever)\s+(?:a\s+|the\s+|my\s+)?(?:run|running|jog|jogging|gym|"
    r"workout|exercise|exercising|cycling|ride|swim|swimming|walk|walking|football|netball|climbing|"
    r"lifting|weights|stairs|cardio)\b",
    # "when im running" and "when i'm walking" are the same line with the apostrophe dropped and
    # no space in the contraction, which the person form below cannot see.
    r"\b(?:after|during|while|when|whenever)\s+(?:im|i'm|ive|i've|were|we're|hes|he's|shes|"
    r"she's|theyre|they're)\s+"
    r"(?:run|running|jog|jogging|gym|workout|exercis\w*|cycl\w*|rid(?:e|ing)|swim\w*|walk\w*|"
    r"climb\w*|lift\w*|play\w*|football|netball|squash|tennis|stairs|cardio|train\w*|row\w*|"
    r"hik\w*|danc\w*|aerobics|hiit|spinning|weights?|press-?ups?|squats)\b",
    # "when I run for the bus" has a person between the cue and the effort.
    r"\b(?:after|during|while|when|whenever)\s+(?:i|we|he|she|they|my\s+\w+)\s+"
    r"(?:am\s+|'m\s+|is\s+|was\s+|are\s+|start\s+|do\s+|play\s+|go\s+|come\s+)?"
    r"(?:run|running|jog|gym|workout|exercis\w*|cycl\w*|rid(?:e|ing)|swim\w*|walk\w*|climb\w*|"
    r"lift\w*|play\w*|football|netball|squash|tennis|stairs|cardio|train\w*|row\w*|hik\w*|"
    r"danc\w*|aerobics|hiit|spinning|weights?|press-?ups?|squats)\b",
    r"\b(?:going|walking|running)\s+up\s+(?:the\s+)?(?:stairs|hill)\b",
    r"\b(?:going|walking|running)\s+(?:up\s+)?upstairs\b",
    # The place says the effort: "struggling to breathe on the stairs".
    r"\b(?:on|up|down|going\s+up)\s+(?:the\s+|some\s+)?(?:stairs|hill|upstairs)\b",
)

# A cause in the line explains the breathing: a blocked nose or a cold is not an airway closing.
# The cold is named any way people name it - "a stinking cold", "this rotten flu" - because the
# adjective in front of it was the only thing keeping "i have a stinking cold and cant breathe" on
# the ambulance card.
BREATH_CAUSE = (
    r"\b(?:nose|nostrils?|blocked|bunged|stuffed|congestion|congested|hayfever|hay\s+fever|"
    r"sinus\w*|blocked\s+up)\b",
    # The illness sense of "cold" only. `im so cold and i cant breathe` is the temperature, and it
    # was ring-999 before a bare `cold` was let in here, so the word has to be said as a thing you
    # have caught: "a stinking cold", "got a cold", "this cold", "the flu", "a virus".
    r"\b(?:a|this|that|the|my|your|his|her|stinking|rotten|bad|nasty|heavy|terrible|awful|"
    r"horrible|proper|real|slight|streaming|head|chest|summer|winter|24\s?hour)\s+cold\b",
    r"\b(?:got|have|had|caught|catch|fighting|coming\s+down|full\s+of)\s+(?:a\s+|the\s+|this\s+)?"
    r"cold\b",
    # Flu and a virus are not a blocked nose: they are the illnesses most likely to turn into
    # pneumonia, so `i have the flu and i cant breathe` keeps the ambulance. They count here only
    # with the congestion said as well, which is the shape the red arm already uses.
    r"\b(?:flu|virus|flu\s+bug)\b[^.?!]{0,30}\b(?:nose|blocked|bunged|stuffed|congestion|"
    r"congested|sinus\w*)\b",
    # "chesty" sits between the article and `cold`, so the article arm misses it while `\bchest\b`
    # in the red list does not match it: a chesty cold is the cold this reply is about.
    r"\bchesty\b",
)

# The everyday wording of it: "short of breath", "out of breath", "breathless", "struggling to
# breathe". Kept apart from BREATHING because most of these are not emergencies.
BREATH_SHORT = (
    r"\b(?:short|out)\s+of\s+(?:breath|puff)\b",
    r"\bbreathless\b",
    r"\bpuffed\s+out\b",
    r"\b(?:struggling|struggle|hard|harder|difficult\w*|trouble)\b[^.?!]{0,18}\bbreath\w*\b",
    r"\b(?:can'?t|cannot|can\s+not)\s+breath\w*\b",
    r"\bbreathing\s+(?:heavily|hard)\b",
)

# Moved to safety_cards.py: LAUGH_BREATH_RED, LAUGH_OTHER_PERSON, LAUGH_TAKES_BREATH, LAUGH_WORD
# A small effort: a flight of stairs, a hill, the walk to the shops. Being out of puff on those,
# when it is new, is the GP's question rather than the ambulance's or a shrug.
EXERTION_SMALL = (
    r"\b(?:on|up|down|climbing|walking\s+up|going\s+up)\s+(?:the\s+|a\s+|some\s+)?"
    r"(?:stairs|staircase|steps|hill|slope|hillock)\b",
    r"\b(?:going|walking|running|coming)\s+upstairs\b",
    r"\b(?:walk\w*|stroll\w*|potter\w*|get(?:ting)?)\s+(?:to\s+|into\s+)?(?:the\s+)?"
    r"(?:shops?|shop|bus|station|school|work|village|town)\b",
    r"\b(?:small|short|little|gentle)\s+(?:walk|walks|effort|hill|stroll)\b",
    r"\b(?:a|one|two|three)\s+flights?\s+of\s+stairs\b",
    # "i cant catch my breath after the stairs" and "after a walk up the stairs" are the same
    # small effort as "walking up the stairs", which already got this reading: the effort answer
    # was taking them because the words of recovery match and "stairs" is a small effort, not a
    # class. The forms below are the ones the effort answer was swallowing.
    r"\b(?:after|on|from)\s+the\s+stairs\b",
    r"\b(?:the|some)\s+stairs\b",
    r"\b(?:walking|walked|went|going)\s+up\s+(?:the\s+|a\s+)?(?:hill|slope)\b",
    r"\b(?:getting|get|got)\s+dressed\b",
    r"\b(?:around|round)\s+the\s+(?:house|garden|park)\b",
)

# A meal explains a new breathlessness the way a hill does - reflux, a full stomach, being
# overweight - and it is the GP's question rather than an ambulance. It is not effort, so it gets
# its own arm and its own wording.
MEAL_BREATH = (
    r"\b(?:after|before|when|while)\s+(?:i\s+|she\s+|he\s+|they\s+)?(?:eating|a\s+(?:big\s+|"
    r"heavy\s+|large\s+|huge\s+|proper\s+)?meal|dinner|lunch|breakfast|tea)\b",
    r"\b(?:eating|a\s+meal|dinner|lunch|breakfast)\b[^.?!]{0,20}\b(?:breath|puffed|winded)\w*\b",
    r"\b(?:short|out)\s+of\s+(?:breath|puff)\b[^.?!]{0,20}\b(?:eat|eating|meal|dinner|lunch)\b",
)

# The cue "when/after/while" is how most people write it ("i get out of breath when i run"), but
# "at the gym" and "short of breath running" carry the effort without any of those words, so the
# second guard looks for the effort anywhere in the line.
EFFORT_ANYWHERE = (
    r"\b(?:run|runs|running|jog\w*|gym|workout|exercis\w*|cycl\w*|swim\w*|football|netball|squash|"
    r"tennis|cardio|stairs|hills?|climb\w*|walk\w*|hike|hiking|danc\w*|hiit|weights?|press-?ups?|"
    r"squats|spin|rowing|skipping|badminton|rugby|cricket|climbing|box\w*|class|classes|"
    r"session|ran|singing|sing|laughing|talking|carrying|shopping|cleaning|"
    r"hoovering|garden\w*|digging)\b",
)

SHORT_OF_BREATH = (
    r"\b(?:out\s+of|short(?:ness)?\s+of)\s+breath\b",
    # "i am still short of breath" is the present tense with a word in between, so the copula list
    # above cannot see it.
    r"\b(?:still|now|very|quite|really|so|a\s+bit|a\s+little|always|already)\s+"
    r"(?:out\s+of|short(?:ness)?\s+of)\s+breath\b",
)

# Nouns only: "my car" holds a possessive and no person, so `my` here would let every gadget through.
A_BREATHER = (
    r"\b(?:i|me|we|us|he|him|she|they|them|you|husband|wife|partner|"
    r"boyfriend|girlfriend|mum|mom|mother|dad|father|son|daughter|baby|child|kid|nan|gran|"
    r"grandma|grandad|brother|sister|friend|man|woman|boy|girl|patient|neighbour|neighbor|"
    r"dogs?|cats?|pupp(?:y|ies)|kittens?|pets?|parrot|hamster|rabbit)\b",
)

# Breathlessness that comes on with effort, with none of these in the line, is ordinary.
BREATH_RED = (
    r"\b(?:blue|lips?|can'?t\s+speak|cannot\s+speak|unable\s+to\s+speak|at\s+rest|resting|in\s+bed|"
    # A form says "chest pain"; a person typing at midnight says "my chest hurts when i walk".
    # Only the form was a red flag, so "i cant breathe and my chest hurts when i walk" was read
    # as breathlessness on effort and sent to the fitness answer, which is the one line in this
    # file where being wrong costs the most. "Ache" is not in the arm: it is the ordinary word
    # for the soreness a hard session leaves, so "i cant catch my breath after spin class and my
    # chest aches" is effort and keeps the effort answer (agile-lychee, #5550).
    r"woke\s+me|sudden\w*|getting\s+worse|chest\s+pains?|"
    r"chest\b[^.!?]{0,20}\b(?:hurt\w*|tight\w*|pressure|heav\w*|squeez\w*)|"
    r"(?:tight\w*|pressure|heavy|heaviness)\b[^.!?]{0,15}\bchest\b|swell\w*|anaphyla\w*|epipen|wheez\w*|"
    # "asthma" used to sit here as a bare word, so a person whose asthma is controlled could not
    # say "my asthma is fine but i get short of breath at the gym" without the ambulance. The
    # attack shapes are what keep a line an emergency; the diagnosis on its own is not.
    r"asthma\s+attack|\basthma\b[^.!?]{0,15}\b(?:bad|badly|worse|severe|uncontrolled|out\s+of\s+control)\b|"
    r"inhaler\b[^.!?]{0,25}\b(?:not\s+working|isn'?t\s+working|isn'?t\s+helping|not\s+helping)\b|"
    r"stopped\s+breathing|isn'?t\s+breathing|not\s+breathing|gasping|coughing\s+up|blood)\b",
)

# A cold only explains the breathing when the lungs are not already a problem. A bare "asthma" is
# deliberately not a red flag on its own (a controlled asthmatic may say "short of breath at the
# gym"), but in the same line as a cold and "i cant breathe" it is the emergency.
BREATH_CAUSE_RED = BREATH_RED + (
    r"\basthma\b", r"\binhaler\b", r"\bwheez\w*", r"\bchest\b", r"\btongue\b",
    r"\bstridor\b", r"\bcroup\b",
    # A throat has to be the problem, not a place: "a blocked nose and a sore throat and cant
    # breathe" is a cold with a raw throat, which is not the same-day line's red flag. The closing
    # throat, the one that cannot swallow, is still a red flag.
    r"\bthroat\b[^.?!]{0,20}\b(?:clos\w*|swell\w*|tight\w*|shut|seal\w*)\b",
    r"\b(?:clos|swell|tight)\w*\s+(?:up\s+)?(?:in\s+|of\s+)?(?:my\s+|the\s+|his\s+|her\s+)?"
    r"throat\b",
    r"\bcant\s+swallow\b", r"\bcan'?t\s+swallow\b", r"\bdifficulty\s+swallowing\b",
    r"\bswallow(?:ing)?\s+(?:is\s+)?(?:hard|painful\s+and\s+getting\s+worse)\b",
    # The temperature sense of `cold`, so "im so cold and i cant breathe" can never be read as a
    # cause: shivering is a sign, and being chilled is not a blocked nose.
    r"\b(?:feel(?:ing)?|am|im|so|very|really|freezing|frozen|shivering|shivery|shivers|bit)\s+"
    r"cold\b",
    r"\bcold\s+(?:and|or)\s+(?:shivering|shivery|clammy|sweating|weak|floppy|confused)\b",
    r"\bcold\s+to\s+(?:the\s+)?touch\b",
)

HUMAN_TOO = (
    r"\b(?:my|our|her|his|their)\s+(?:son|daughter|child|kid|baby|boy|girl|mum|mom|dad|father|mother|"
    r"husband|wife|partner|brother|sister|nan|gran|grandma|grandad|friend|neighbour|neighbor)\b",
    # The speaker or another person said to be the one who cannot breathe, get their breath or wake.
    r"\b(?:i|i'm|im|he|she|they|we|you|someone|somebody)\b[^.?!]{0,12}"
    r"\b(?:can'?t|cannot|can\s+not|couldn'?t|struggling\s+to|unable\s+to)\s+"
    r"(?:breath\w*|(?:get|catch)\s+(?:my|his|her|their|our|a)\s+breath\w*|wake\s+up|stay\s+awake)",
    # And a person said to be bleeding, collapsed, choking or unresponsive is the patient too.
    r"\b(?:i|i'm|im|he|she|they|we)\b[^.?!]{0,10}\b(?:am|is|are|'m|'s|'re|was|were)\s+"
    r"(?:bleeding|unconscious|unresponsive|collapsed|choking)\b",
    # "im bleeding" / "i'm choking" writes the verb without a separate "am".
    r"\b(?:im|i'm)\s+(?:bleeding|unconscious|unresponsive|collapsed|choking)\b",
)

# The pet cases that cannot wait for morning. A dog that is sick in the car or has a sore paw is a
# vet appointment; one that cannot breathe, is bleeding or has eaten poison is tonight.
# "my dog choked on a bone last year, is that common?" is not an emergency now.
PET_PAST = (
    r"\b(?:last|this)\s+(?:year|month|week)\b", r"\byears\s+ago\b", r"\bages\s+ago\b",
    r"\bwhen\s+(?:he|she|it|they)\s+(?:\w+\s+){0,3}(?:was|were)\s+(?:a\s+)?(?:puppy|kitten|young)\b",
    r"\bused\s+to\b",
    # A pet that has these turns every so often is a condition to ask about, not tonight's call.
    r"\bevery\s+(?:few\s+)?(?:days?|weeks?|months?|years?)\b",
    r"\bis\s+that\s+(?:normal|usual|common)\b",
)

PET_GASP_FINE = (
    # Something the animal was doing took its breath away.
    r"\bgasp\w*\b[^.?!]{0,30}\b(?:after|from|during|when(?:ever)?|on|in)\b[^.?!]{0,25}"
    r"\b(?:walk|run|runn\w*|plays?|playing|played|exercis\w*|fetch|ball|games?|zoomies|"
    r"chas\w*|charged|park|garden|hill|stairs|beach|frisbee|swim\w*|train\w*)\w*\b",
    # Thirst and hunger are the other gasping a pet does.
    # Being hot is how a dog cools down, and the heat answer already says to ring the vet for
    # bright red gums or a dog that will not settle - so the gasp on its own is not the card.
    r"\bgasp\w*\b[^.?!]{0,25}\b(?:in|from)\s+(?:the|this|that)\s+(?:heat|sun|hot\s+weather|warmth)\b",
    # A car seat, a certain animal, a bit of it: the gasp a person is not worried about yet.
    r"\bgasp\w*\s+at\s+(?:the|a|an|his|her|its|their|my|other|next)\b",
    r"\b(?:in|on|during)\s+(?:the|a|his|her|its|their)\s+(?:car|drive|journey|train|bus)\b",
    r"\bgasp\w*\b[^.?!]{0,15}\b(?:a\s+bit|a\s+little|slightly)\b",
    r"\bgasp\w*\s+(?:for|after)\s+(?:(?:a|an|the|some|its|his|her|their|my)\s+)?"
    r"(?:a\s+)?(?:drink|water|food|biscuit|treat|dinner|tea)\b",
)

# A list of activities only catches the ones someone thought of, and a person writes the reason in
# the sentence: `my dog gasps when he gets excited` was the vet's night, and so were the sneeze, the
# lead and the bowl of water. These are the shapes a trigger takes, so the next activity nobody
# listed is read too - ochre-hedgehog's read at `11a33d55`.
PET_GASP_EXPLAINED = (
    r"\bgasp\w*\b[^.?!]{0,40}\bwhen\s+(?:he|she|it|they)(?:'?s|s|\s|\b)",
    r"\bgasp\w*\b[^.?!]{0,40}\b(?:because|whenever|every\s+time)\b",
    # A noise that came first explains the one that followed it.
    r"\b(?:sneez\w*|cough\w*|hiccup\w*|laugh\w*|retch\w*|splutter\w*|purr\w*)\b"
    r"[^.?!]{0,25}\bgasp\w*\b",
    r"\bgasp\w*\b[^.?!]{0,30}\b(?:on|off)\s+the\s+lead\b",
    r"\bgasp\w*\b[^.?!]{0,30}\bafter\s+(?:a\s+|an\s+|the\s+|his\s+|her\s+|its\s+|their\s+|"
    r"our\s+|my\s+)?(?:drink\w*|water|food|meal|dinner|tea|breakfast|eating|ate|gulping|"
    r"too\s+fast|too\s+quickly)\b",
)

# The signs that say the gasp is not the walk or the weather, whatever else the line says: a pet
# with blue gums is the vet's even if it has just been for a run.
PET_GASP_RED = (
    r"\bcan'?t\s+breathe\b", r"\bnot\s+breathing\b", r"\bblue\b", r"\bpale\b",
    r"\bunconscious\b", r"\bchok\w*", r"\bcollaps\w*", r"\bwoke\s+up\b", r"\bwakes?\s+up\b",
    r"\bkept?\s+waking\b", r"\blimp\b",
    r"\bstill\b", r"\bfor\s+(?:\d+|a\s+few|ten|twenty|half\s+an?\s+hour)\b",
    r"\bgums?\b", r"\bbright\s+red\b", r"\b(?:grey|gray|white)\s+gums?\b",
)

# A bang on the head is the one injury where the words alone do not say how bad it is, so it gets
# its own answer instead of "Noted!": what to do now, and the one question that sorts the cases.
# It only counts with a head in the line, so "he was knocked out in the third round" and "banging my
# head against a brick wall" stay out (see MILD and FIGURATIVE for the rest).
HEAD_BANG = (
    r"\b(?:bang|bangs|banged|banging|hit|hits|hitting|knock|knocks|knocked|knocking|strike|struck|"
    r"smack(?:s|ed|ing)?|crack(?:s|ed|ing)?|bump(?:s|ed|ing)?|bashed?|bashing|smashed?|smashing|"
    r"slammed?)\s+"
    r"(?:my|his|her|their|the|me\s+in\s+the|him\s+in\s+the|her\s+in\s+the|on\s+the|in\s+the)\s+head\b",
    r"\bhead\s+(?:injury|injuries|trauma|wound)\b",
    r"\b(?:got|gets|getting)\s+(?:hit|struck|clipped|caught|banged)\s+(?:on|in)\s+the\s+head\b",
    r"\bhit\s+(?:on|in)\s+the\s+head\s+(?:by|with)\b",
    # The fall has to land on the head, not merely happen in the same line: "my hair fell out and my
    # head is cold" and "we fell out over money and my head is all over the place" are not injuries.
    r"\b(?:fell|fallen|fall|falls|tripped|slipped|toppled|tumbled)\s+(?:over|down|off|from|onto|on\s+to)\b"
    r".{0,25}\bhead\b",
    r"\bhead\s+(?:first|hit|banged|struck)\s+(?:on|into|off|against)\b",
)

# A knock-out with no head word in the line: "i was knocked out for a few seconds", "i got knocked
# out cold at rugby". Being knocked out is a brain injury whatever caused it, so it does not need
# the word "head" to be the same call. It is not a sport result: "knocked out of the cup" and
# "knocked out by a better team" are somebody's Saturday, and "out cold" is never that.
# "Out cold" is a person who is unconscious, and the bare phrase is also how a takeaway arrives:
# "my takeaway came out cold" was the head-injury 999 card, complete with "confusion, drowsiness or
# sickness after a bang on the head". So the phrase needs a person in front of it, or a fall beside
# it, and a meal does not count as either.
OUT_COLD_PERSON = (
    r"\b(?:i|he|she|they|we|you)\b[^.?!]{0,15}\bout\s+cold\b",
    r"\b(?:my|his|her|their|our|your|the)\s+" + PERSON + r"\b[^.?!]{0,20}\bout\s+cold\b",
    # No subject at all is still a person: "out cold on the kitchen floor" is not a dinner.
    r"\b(?:out\s+cold)\b[^.?!]{0,20}\b(?:floor|ground|sofa|couch|bed|street|pavement|road|"
    r"bathroom|kitchen|hospital)\b",
    r"\b(?:fell|fallen|collapsed|dropped|banged|hit|knocked|tripped)\b[^.?!]{0,25}"
    r"\bout\s+cold\b",
)

HEAD_KNOCKOUT = (
    r"\b(?:was|were|been|got|gets|getting|being|had|has)\s+knocked\s+out\b(?!\s+(?:of|in|by)\b)",
    r"\bknocked\s+(?:him|her|them|my\s*self|him\s*self|her\s*self)\s*out\b",
    # A bare "out cold" is a faint now, so the phrase needs the knock above to reach this arm. The
    # one exception is nobody named with a floor under them: "out cold on the kitchen floor" is
    # somebody out cold in front of you, and "my takeaway came out cold" is a dinner.
    *HEAD_OUT_COLD,
    r"\bout\s+cold\b[^.?!]{0,20}\b(?:floor|ground|street|pavement|road|bathroom|kitchen|"
    r"hospital)\b",
)

# A tooth that came out by itself is a milk tooth on its way to the tooth fairy, or one that came
# out years ago: neither wants a dentist tonight.
TOOTH_OUT_FINE = (
    r"\bmilk\s+tooth\b", r"\bbaby\s+tooth\b", r"\bwobbly\b", r"\bloose\s+tooth\b",
    r"\btooth\s+fairy\b", r"\btoothache\b", r"\b(?:last|this)\s+(?:year|month|week)\b",
    r"\byears?\s+ago\b", r"\bwhen\s+i\s+was\s+(?:a\s+)?(?:kid|child|little)\b",
    # The socket left behind is a hole to let clot, not a tooth to put back: "the hole where my
    # tooth came out is bleeding" is a bleeding answer.
    r"\b(?:hole|socket|gap)\b[^.?!]{0,25}\btooth\b", r"\btooth\b[^.?!]{0,25}\b(?:hole|socket)\b",
    r"\bwhere\s+(?:my|his|her|their)\s+tooth\s+(?:came|fell|was)\b",
    r"\bgum\b[^.?!]{0,30}\b(?:tooth|teeth)\b",
    # A crown is a cap on a tooth, not a tooth: "the crown came off my tooth" is a dentist's
    # appointment this week, and the socket advice below is for a tooth that left the mouth.
    r"\bcrowns?\b",
    # A child's tooth that fell out on its own is a milk tooth on its way out, not one to put back;
    # a knock is still a knock, so the word for it keeps the socket advice.
    r"\b(?:son|daughter|kid|child|children)'?s?\s+(?:front\s+|back\s+|adult\s+|baby\s+|milk\s+)?"
    r"(?:tooth|teeth)\b[^.?!]{0,10}\b(?:came|fell)\s+out\b",
)

# A tooth knocked out of a cat, a dog or a rabbit is the vet's, and the socket advice above is the
# worst thing to do with it: "my cat knocked a tooth out" was told to put the tooth back in its own
# socket. The animal has to be named as the one whose tooth it is, so a person's tooth keeps the
# dentist and "my son knocked his tooth out" is untouched.
PET_TOOTH = (
    r"\b(?:my|our|his|her|their|the)\s+(?:\w+\s+){0,2}"
    r"(?:cat|cats|dog|dogs|puppy|puppies|kitten|kittens|rabbit|rabbits|bunny|bunnies|hamster|"
    r"guinea\s+pig|horse|pony|parrot|ferret|gerbil|rat|mouse|tortoise|snake|lizard|pup)\b"
    r"[^.?!]{0,40}\b(?:tooth|teeth|tusk|beak)\b",
    r"\b(?:tooth|teeth|tusk)\b[^.?!]{0,25}\b(?:of|from)\s+(?:my|our|the)\s+"
    r"(?:cat|dog|puppy|kitten|rabbit|hamster|horse|parrot)\b",
    r"\b(?:cat|dog|puppy|kitten|rabbit|hamster|horse|parrot)'?s\s+"
    r"(?:\w+\s+){0,2}(?:tooth|teeth|tusk)\b",
)

# The flags that make it a 999 call rather than a watch-and-see. A knock-out is the big one: it is a
# brain injury until a doctor says otherwise, and people who seem fine after one still need checking.
HEAD_RED = (
    # Being sick once after a bang is a 999 call: vomiting is one of the signs that gets a scan, and
    # "i was sick" is the report of it. "i feel a bit sick" is nausea without being sick, which is the
    # watch answer, and the watch reply says what an ambulance is for.
    r"\bknock(?:ed|s)?\s+(?:him|her|them|my\s*self|him\s*self|her\s*self)?\s*out\b",
    r"\b(?:was|were|been|got|had|being)\s+knocked\s+out\b", *OUT_COLD_PERSON,
    r"\bunconscious\b", r"\bpassed\s+out\b", r"\bblacked\s+out\b", r"\bkeeled\s+over\b",
    # "confused about the recipe" is a bump, not a brain injury: the confusion has to be about the
    # person, not their cooking. "a pupil" is a schoolchild, so the pupil sign needs the uneven pair.
    r"\bconfus(?:ed|ion)\b(?!\s+about\s+(?!where\b|who\b|how\b))", r"\bdidn'?t\s+know\s+(?:where|who)\b",
    # "isnt making sense" is as common as "not making sense", and after a fall it is the same sign
    # (khaki-key, #safety 20210).
    r"\b(?:not|isn'?t|isnt|ain'?t|wasn'?t|doesn'?t)\s+making\s+sense\b",
    r"\b(?:talking|chatting)\s+(?:rubbish|nonsense|gibberish)\b",
    r"\bslurr\w*\b", r"\bdouble\s+vision\b",
    r"\bpupils?\b.{0,15}\b(?:different|unequal|dilated|blown|one\s+(?:bigger|smaller|larger))\b",
    # "drowsy" is the word people use, and "drowsi" is not how it starts: the sign named in the
    # 999 reply has to ring on it.
    r"\bdrows(?:y|iness|ily)?\b", r"\b(?:very|really|so)\s+sleepy\b", r"\bcan'?t\s+(?:wake|stay\s+awake)\b",
    # "drowsy" is the word in the 999 reply, and "keeps dozing off" is the way people say it: a
    # bang on the head and then a person who cannot keep their eyes open is the sign, whatever
    # word they reached for. It only counts with the bang in the line, so `i keep dozing off at
    # work` is still the chat it was.
    r"\b(?:keep|keeps|kept)\s+(?:on\s+)?(?:dozing(?:\s+off)?|nodding\s+off|drifting\s+off|"
    r"falling\s+asleep|zonking\s+out)\b",
    r"\b(?:dozing|nodding|drifting|zonking)\s+(?:off|out)\b",
    r"\bcan'?t\s+keep\s+(?:my|his|her|their)?\s*eyes\s+open\b",
    # ...said as a feeling rather than an adjective: "i banged my head and i feel sleepy" was the
    # bump card. Feeling sick is not here: being sick is the sign, and a churned stomach after a
    # knock is the watch card (the head-injury test holds that).
    r"\b(?:feel|feels|feeling|felt)\s+(?:a\s+bit\s+|really\s+|very\s+|so\s+)?"
    r"(?:sleepy|drowsy|confused|not\s+with\s+it)\b",
    r"\b(?:being|been|keeps?)\s+sick\b", r"\bvomit\w*\b", r"\b(?:throw(?:ing|n)?|threw)\s+up\b",
    r"\b(?:was|were|got|gets|getting|kept)\s+(?:a\s+bit\s+|really\s+|very\s+)?sick\b",
    r"\bfaint(?:ed|s|ing)?\b", r"\bseizure\b", r"\b(?:having|had)\s+a\s+fit\b",
    # "he is fitting" is a seizure; "his helmet isnt fitting" is a hat.
    r"\b(?:is|was|were|had|has|kept)\s+fitting\b(?!\s+(?:in|on|into|his|her|their|my|your|the|a)\b)",
    r"\bbleed(?:ing)?\s+(?:from|out\s+of)\s+(?:the\s+|his\s+|her\s+)?ears?\b",
    r"\bclear\s+fluid\b", r"\bwarfarin\b", r"\bblood\s+thinners?\b", r"\bclopidogrel\b",
    r"\b(?:worse|worst)\s+headache\b", r"\bheadache\s+(?:is\s+)?(?:getting|getting\s+)\s+worse\b",
    r"\bneck\s+(?:is\s+)?stiff\b", r"\bcan'?t\s+move\s+(?:my|his|her)\s+neck\b",
)

# The same trick with the other verbs in `FALL_REPEAT`: "i keep slipping up at work" is a mistake
# and "i keep tripping over my words" is nerves in an interview, and both were the 999 card once
# the confusion next to them was read (azure-trout, #2997).
FALL_WORD_IDIOM = (
    r"\b(?:slip|slips|slipped|slipping)\s+up\b",
    r"\btrip(?:s|ped|ping)?\s+over\s+(?:my|his|her|their|your|our)\s+(?:words|tongue)\b",
    r"\b(?:fall|fell|falling)\s+(?:out|in)\s+with\b",
    # "i fell owt wiv me sister" is the same quarrel written the way people type it, and it was the
    # bruising card. The chat-speak spelling is what the fall arm read as a fall; "fell out of bed"
    # keeps "of", so the quarrel is the only thing after the verb here.
    r"\b(?:fall|fell|falling)\s+(?:out|owt)\s+(?:wi|wiv|wid|with|over|about)\b",
)

# The words that say the pet is all right, or that the odd thing has an ordinary reason. A dog that
# ignores its recall, a puppy asleep after a big meal and a stiff old dog are the three commonest
# reasons someone types the behaviour patterns below, and none of them is tonight's call.
PET_ALL_RIGHT = (
    r"\b(?:but|and|though|although|except|only)\b.{0,40}\b(?:fine|ok|okay|alright|all\s+right|"
    r"normal|himself|herself|no\s+different|not\s+himself)\b",
    r"\b(?:seems?|looks?|appears?)\s+(?:fine|ok|okay|alright|normal|himself|herself)\b",
    r"\b(?:he|she|it|they|hes|shes|its|theyre)(?:'s|s)?\s+(?:is|are)?\s*"
    r"(?:fine|ok|okay|alright|normal)\b",
    r"\bjust\s+(?:ate|eaten|had\s+a\s+(?:big\s+)?meal|a\s+big\s+meal|tired|sleeping|"
    r"worn\s+out|getting\s+old|old|woken\s+up|having\s+a\s+lazy\s+day)\b",
    r"\b(?:1[0-9]|[2-9][0-9])\s*(?:years?\s+old|and\s+stiff|now)\b|\b(?:is|getting)\s+(?:old|stiff)\b",
    r"\bstiff\s+(?:in\s+the\s+morning|first\s+thing)\b",
    r"\b(?:the\s+)?vet\s+(?:said|says|told|checked|has\s+seen|saw|thinks?)\b",
)

# A pet that will not respond, or that has stopped moving about, gets its own first line: the
# emergency wording about bleeding and swallowed poison describes none of it.
# "wont respond" is also what a dog does about its recall, and a puppy about anything at all: the
# thing it will not answer is a voice, a call, a name, a treat. None of those is a collapse, and the
# stand-down is written once here so the three arms that key the bare verb cannot drift apart
# (magenta-hammer's blocker on #795: `my dog wont respond when i call him` was the vet card).
PET_RESPOND_AT = (r"(?!\s+(?:to|for|when|if)\b[^.?!]{0,30}\b(?:i|we|me|us|him|her|them|my|our|"
                  r"voice|calling|call|calls|say|says|said|speak|talk|asks?|asked|names?|"
                  r"treats?|food|dinner|toys?|recall|commands?|laser|catnip|nip|clicker|"
                  r"whistle|lead|ball|kibble|chews?|train\w*|housetrain\w*|sits?|stays?|heels?|"
                  r"tricks?|classes?|obedience|sessions?|cues?)\b)")

# "I choked on a bit of bread at lunch" is over; only a line that says it is still going is urgent.
CHOKE_OVER = (
    r"\bchoked\b.{0,40}\b(?:at\s+(?:lunch|dinner|breakfast)|yesterday|last\s+night|this\s+morning|"
    r"earlier|a\s+while\s+ago|years\s+ago|ages\s+ago|once|before|again|last\s+year|"
    r"last\s+week|last\s+month|months?\s+ago|when\s+i\s+was\s+(?:a\s+)?(?:kid|child|little|"
    r"young|small)|as\s+a\s+(?:kid|child|baby|teen|little\s+one))\b",
    r"\bchoked\b[^.?!]{0,30}\bin\s+(?:19|20)\d\d\b",
    r"\b(?:used\s+to|always)\s+choke\b",
)

# A stated duration is the difference between a symptom and an emergency: weeks of breathlessness is
# a same-day appointment (anaemia, COPD, a chest infection, a bad heart), and an ambulance for it
# frightens a person who was only telling you how long it has been going on. Hours are not this:
# "short of breath for an hour" is new, and it keeps the careful line.
CHRONIC_BREATH = (
    # A counted duration: "for a week", "for 3 days", "going on for two months".
    r"\b(?:for|going\s+on\s+for|over\s+the\s+(?:last|past))\s+"
    r"(?:about\s+|nearly\s+|almost\s+|over\s+)?(?:\d+|one|two|three|four|five|six|seven|eight|"
    r"nine|ten|a|an|a\s+few|a\s+couple\s+of|several|many|last)\s+"
    r"(?:day|days|week|weeks|month|months|year|years)\b",
    # An uncounted one: "for weeks", "for days now", "for the last few months".
    # "for a long time" and "for a while" are left out on purpose: "short of breath when i talk for
    # a long time" is a habit with a cause, not a symptom with a duration.
    r"\bfor\s+(?:the\s+)?(?:last\s+|past\s+|few\s+|several\s+|a\s+few\s+|a\s+couple\s+of\s+)?"
    r"(?:days|weeks|months|years)\b",
    # The same duration said as a clause of its own: "im short of breath and its been a week".
    # Main's long-duration reading is keyed on "for a week", and people say it this way too, so a
    # line with the duration after an "and" still got an ambulance.
    r"\b(?:it'?s|its|it\s+has|this\s+has)\s+been\s+(?:like\s+this\s+|going\s+on\s+)?"
    r"(?:about\s+|nearly\s+|over\s+)?(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a|an|"
    r"a\s+few|a\s+couple\s+of|several|many)\s+(?:day|days|week|weeks|month|months|year|years)\b",
    # And the point it started: "since christmas", "these last few weeks".
    r"\bsince\s+(?:last\s+)?(?:christmas|new\s+year|the\s+summer|the\s+holidays|easter|then|"
    r"march|april|may|june|july|august|september|october|november|december)\b",
    r"\bthese\s+(?:last|past)\s+(?:few\s+|couple\s+of\s+|several\s+)?(?:days|weeks|months)\b",
)

# Breathlessness that happens in the night, or only when lying flat, is a different illness from
# breathlessness on the stairs: it is the heart or the lungs asking for a same-day appointment, and
# the words people use for it ("i couldnt breathe last night", "i wake up gasping", "i have to
# sleep propped up") had no answer at all - a listening prompt, or an ambulance for a night that is
# already over. Each pattern needs both halves, the occasion and the breath, in either order.
# The past night is the person typing, not the person they are writing about: a child or a parent
# who woke up gasping is a night that stopped breathing, and the same-day appointment is the wrong
# answer to it. Naming somebody else in the line takes the past arm away, and the case below gives
# it the ambulance instead. The habitual present keeps any subject, because a child who keeps
# doing it is the sleep apnoea question, and the future tense is nobody's night yet.
NIGHT_BREATH_OTHER = (
    r"\b(?:my|our|his|her|their)\s+(?:mum|mom|mother|dad|father|son|daughter|baby|child|kid|"
    r"boy|girl|partner|husband|wife|brother|sister|gran|granny|nan|grandma|grandad|grandpa|"
    r"friend|neighbour|neighbor|flatmate|roommate|niece|nephew|aunt|uncle)s?\b",
    r"\b(?:he|she|they)\s+(?:woke|woken|has\s+woken|had\s+woken)\b",
)

# `i woke up gasping for breath` is heart failure as much as apnoea, so the breath word keeps the
# ambulance the gasp on its own gave up: only the bare gasp becomes the same-day call.
NIGHT_BREATH_PAST = (
    # Anchored at the start: the guard has to read the whole line, not the tail of it, or a scan
    # that starts after "my son" would let the same line through.
    r"\A(?!.*?(?:" + "|".join(NIGHT_BREATH_OTHER) + r"))"
    r"(?![^.?!]*\bfor\s+(?:breath|air)\b)"
    r".*?\b(?:woke|woken)\s+up\b[^.?!]{0,40}\b(?:breath\w*|gasp\w*)\b",
)

# The night that is still happening is the ambulance, not the appointment: "i still cant breathe",
# blue lips, a chest pain with it, or an attack already under way. These words take the line away
# from the same-day answer and give it back to the cases above.
NIGHT_BREATH_RED = (
    # The present tense is still the ambulance: "i cant breathe when i lie down" is now, while
    # "i have to sleep propped up" and "i couldnt breathe last night" are the appointment.
    r"\b(?:can'?t|cannot|can\s+not|unable\s+to|struggling\s+to)\s+breath\w*\b|"
    r"\b(?:blue|lips?|can'?t\s+speak|cannot\s+speak|chest\s+pains?|right\s+now|at\s+the\s+moment|"
    r"as\s+we\s+speak|just\s+happened|a\s+minute\s+ago|still|getting\s+worse|stopped\s+breathing|"
    r"not\s+breathing|isn'?t\s+breathing|asthma\s+attack|wheez\w*|blood|anaphyla\w*|epipen|"
    r"swell\w*)\b",
)

# "i cant breathe and it passed" is still the present tense, so it must not take the "it has gone"
# line - but `i cant breathe when i run for the bus` is effort, and the effort guard has to keep
# working, so these words are red only for that one decision, not for the whole case.
# "I get short of breath when I talk for a long time" is a habit with a cause in it, and the
# red flag the talking words stand for ("short of breath while talking" as a thing happening now)
# is a different sentence. The stretch of talking excuses the line; a red flag anywhere still wins.
TALK_HABIT = (
    r"\b(?:when|whenever|while|after|if)\s+(?:i|we)\s+(?:talk|talks|speak|sing|read|laugh|shout|"
    r"chat)\b[^.!?]{0,20}\b(?:for\s+(?:a\s+long\s+time|a\s+while|ages|long|hours)|a\s+lot)\b",
    r"\b(?:talk|talking|sing|singing|read|reading|laugh|laughing)\w*\s+(?:for|over)\s+"
    r"(?:a\s+long\s+time|a\s+while|ages)\b",
    # Reading or singing out loud takes breath the way walking up a hill does, and main answered
    # "short of breath when i read out loud" with a book recommendation.
    r"\b(?:out\s+loud|aloud|by\s+heart)\b",
)

# Laughing hard empties the lungs and leaves anyone gasping for a few seconds; it is not the lungs
# failing. "i cant catch my breath when i laugh", "my daughter is short of breath when she
# laughs" and "i cant catch my breath laughing" were all the 999 breath card on main. The laugh
# has to be the stated cause, and nothing red may be in the line: at rest, blue lips, a wheeze,
# chest pain or blood keep the card. Talking is left out on purpose - "short of breath while
# talking" is a red flag, not a hobby - and crying is left for whoever can fence it.
BREATH_LAUGH = (
    r"\b(?:when|whenever|while|after|from|every\s+time|each\s+time|if)\b[^.!?]{0,20}"
    r"\blaugh\w*\b",
    r"\blaugh\w*\b[^.!?]{0,25}\b(?:breath(?:less)?|puffed|winded|gasp\w*)\b",
    r"\b(?:can'?t|cannot|can\s+not)\s+(?:catch|get|find)\s+(?:my|his|her|their|a)\s+"
    r"breath\s+laugh\w*\b",
)

BREATH_LAUGH_REPLY = (
    "Laughing hard empties the lungs and leaves anyone gasping for a few seconds; it passes once "
    "the laughing stops, and it is not a sign of bad lungs on its own. Worth a GP if the "
    "breathlessness turns up when nobody is laughing, if a cough or a wheeze comes with it, or if "
    "it is new and getting worse.",
    "A hard laugh leaves nobody with air for a moment, and it settles as soon as the laughing "
    "stops, so there is usually nothing in it. Worth a GP if the breathlessness turns up without "
    "the laugh, or comes with a cough, a wheeze or chest pain.",
)

# The airway that is still letting air through is the cough, which clears itself. "cant speak" and
# "cannot talk" are the opposite, so the air-ok patterns all name the act that still works.
CHOKE_AIR_OK = (
    r"\b(?:can|could|able\s+to)\s+(?:still\s+)?(?:cough|talk|speak|breathe|say)\w*\b",
    r"\bcoughing\s+(?:well|fine|ok|okay|strongly|strong|up)\b",
    r"\b(?:he|she|they|i)\s+(?:is|are|am|'s)\s+(?:coughing|talking|speaking)\b",
    r"\bstill\s+(?:coughing|talking|speaking)\b",
)

# A sink, a drain, an engine and a lawn choke too, and none of them want the five and five. The
# thing chokes, or it is choked with the thing that blocked it.
CHOKE_NOT_PERSON = (
    r"\b(?:kitchen\s+sink|sink|drains?|pipes?|toilet|loo|garden|lawn|flowerbeds?|engine|filter|"
    r"radiator|chimney|gutter\w*|weeds?|moss|bog|traffic|paperwork|inbox|diary|sourdough|"
    r"mower|lawnmower|hoover|vacuum|dishwasher|printer|motorbike|scooter|tears?)\b",
    # A bath, a basin, a shower and a washing machine are choked the same way a drain is, and
    # "my bath is choked" was answered with five sharp back blows. A person in the line still
    # wins below, so "my mum is choking in the shower" keeps the card.
    r"\b(?:bath\s*tub|bathtub|baths?|tub|basins?|hand\s?basins?|wash\s?basins?|showers?|"
    r"shower\s+tray|washing\s+machine|washer|hose|pipework|downpipe|gulley|drainpipe|"
    r"water\s+butt|pump|cistern|plughole|plug\s+hole)\b",
    r"\bchoked\s+(?:with|on)\s+(?:weeds|leaves|moss|traffic|paperwork|debt|hair|roots|fat)\b",
)

# The question a parent asks before anything happens: how do i stop my baby choking on grapes. That
# is the cutting-grapes answer, not the maneuver on a baby who is breathing.
CHOKE_PREVENT = (
    r"\bhow\s+(?:do|can|should|could|would)\s+(?:i|we|you)\s+(?:stop|prevent|avoid|keep)\b",
    r"\bhow\s+to\s+(?:stop|prevent|avoid|keep)\b",
    r"\b(?:stop|prevent|avoid|keep)\s+(?:my|him|her|them|a|the|your|me\s+from)\s+"
    r"(?:\w+\s+){0,2}chok",
    r"\bbest\s+way\s+to\s+(?:stop|avoid|prevent|keep)\b",
    r"\b(?:is|was|am)\s+(?:my|the|a|she|he|it)\s+(?:\w+\s+){0,2}choking\s+if\b",
    r"\bwhy\s+do\s+(?:babies|toddlers|kids|children)\b",
    r"\b(?:so|that)\s+(?:he|she|they|it)?\s*(?:doesn'?t|does\s+not|wont|won'?t|never)\s+choke\b",
    r"\bchoking\s+(?:hazard|risk)\b",
)

# A choke that has already sorted itself out, or one that the laugh did, is not this minute: the
# cough advice covers it, and "got it out" and "hes fine now" are the words that say so.
CHOKE_SETTLED = (
    r"\blaugh\w*\b", r"\bgiggl\w*\b", r"\bchuckl\w*\b",
    r"\b(?:got|get|getten)\s+it\s+(?:out|up)\b", r"\bcoughed\s+it\s+up\b",
    r"\b(?:it|came|went)\s+(?:up|out)\b",
    r"\b(?:he|she|they|i)(?:'s|s|\s+is|\s+am|\s+are)?\s+(?:fine|ok|okay|alright)\s+now\b",
    r"\bthat\s+was\s+close\b",
)

# Who it is happening to. The person word has to win over an "i" in another clause, or a parent
# reading about their own child is told to give themselves abdominal thrusts.
CHOKE_PERSON = (
    r"\b(?:my|his|her|their|our|the)\s+(?:\w+\s+){0,1}(?:mum|mom|mother|dad|father|son|daughter|"
    r"husband|wife|partner|brother|sister|friend|baby|child|kid|boy|girl|man|woman|gran|granny|"
    r"nan|grandad|grandma|grandpa|toddler|newborn|infant|mate|neighbou?r)\b",
    r"\b(?:he|she|they)\s+(?:is\s+|are\s+|was\s+|were\s+)?choking\b",
    r"\b(?:he|she|they)\s+choked\b",
)

FLOPPY_THING = (
    r"\bflopp\w*[\s-]+(?:disk|disc|drive|hat|hats|brim|brimmed|hair|haired|fringe|ears?|eared|bow|"
    r"toy|teddy|puppet|sleeve|leaves|book|bag|flag|cover|blanket|flower|plant|bunny|rabbit|dog|"
    r"puppy|kitten|cat|doll|ears|eared)\b",
    # "my hair has gone limp", "the lettuce went limp".
    r"\b(?:hair|lettuce|salad|leaves|plant|flowers?|washing|sheets|flag|sail|balloon|fabric|battery)\b"
    r".{0,20}\b(?:limp|floppy)\b",
)

# "my baby is floppy when sleepy, is that normal" is a question about sleep, not a collapse: the
# floppiness is tied to the moment of falling asleep, and that is normal in a baby that is itself
# when awake. "very sleepy and floppy" is the opposite and stays 999 - a sleepy floppy newborn is a
# red flag - so the sleepy word has to come after "when", and any red flag in the line wins.
FLOPPY_SLEEPY = (
    r"\bflopp\w*[^.]{0,40}\bwhen\s+(?:they\s+are\s+|she\s+is\s+|he\s+is\s+|hes\s+|shes\s+)?"
    r"(?:very\s+)?(?:sleepy|sleeping|asleep|drowsy|tired|nodding\s+off|dropping\s+off)"
    r"(?:\s+(?:he|she|they|it)\s+(?:falls?|drops?|nods?)\s+(?:a\s+)?(?:asleep|off|sleep)\b)?",
    r"\b(?:goes|go|gets|get|turns?)\s+flopp\w*[^.]{0,40}\bwhen\s+(?:very\s+)?"
    r"(?:sleepy|sleeping|asleep|drowsy|tired|nodding\s+off|dropping\s+off)\b",
    r"\bflopp\w*[^.]{0,40}\bwhen\s+(?:he|she|they|it)\s+(?:falls?|drops?|nods?)\s+"
    r"(?:a\s+)?(?:asleep|off|sleep)\b",
    r"\b(?:goes|go|gets|get|turns?)\s+flopp\w*[^.]{0,40}\b[^.]{0,20}?"
    r"\b(?:falls?|drops?|nods?)\s+(?:a\s+)?(?:asleep|off)\b",
)

FLOPPY_RED_FLAG = (
    r"\bwont\s+wake\b", r"\bwon'?t\s+wake\b", r"\bhard\s+to\s+wake\b", r"\bnot\s+waking\b",
    r"\bnot\s+feeding\b", r"\bwont\s+feed\b", r"\bwon'?t\s+feed\b", r"\bstopped\s+feeding\b",
    r"\btemperature\b", r"\bfever\b", r"\bbreath\w*\b", r"\bunresponsive\b", r"\blife-?less\b",
    r"\bvery\s+sleepy\b", r"\btoo\s+sleepy\b",
)

# Heat stroke is a real emergency and, unlike most of them, it is usually said as a complaint
# rather than as a scene ("i have heatstroke"): cool them now and ring 999.
HEAT = (
    r"\bheat\s?stroke\b", r"\bheat\s+exhaustion\b", r"\bsun\s?stroke\b",
    r"\b(?:overheated|over\s?heated)\b.{0,25}\b(?:sick|dizzy|faint|confused|headache)\b",
    r"\b(?:sick|dizzy|faint|confused)\b.{0,25}\b(?:from|in)\s+(?:the\s+)?heat\b",
    # People say "overheating" and "boiling hot" of a person as well as an oven or a laptop, so the
    # word only counts with a symptom or someone unable to stand.
    r"\b(?:overheat\w*|boiling\s+hot)\b.{0,30}\b(?:confused|dizzy|faint\w*|sick|vomit\w*|"
    r"collapse\w*|unconscious|can'?t\s+stand|couldn'?t\s+stand|cant\s+stand|headache)\b",
    r"\b(?:confused|dizzy|faint\w*|vomit\w*|collapse\w*)\b.{0,30}\b(?:overheat\w*|boiling\s+hot)\b",
    # A child who has gone hot and floppy or drowsy is the same emergency said another way.
    r"\b(?:baby|babies|toddler|newborn|infant|child|kid|son|daughter|boy|girl)\b.{0,40}"
    r"\b(?:boiling\s+hot|burning\s+up|overheat\w*)\b",
)

# The act named as a noun: "my 16 year old is self harming", "my teenager has been self harming".
# The person words around it never had "teenager" or "16 year old" in them, so a parent saying it
# got the card for the reader's own crisis, with the wrong person's name on the help. A talk, a
# course or a counsellor is a subject rather than a person at risk, and stays ordinary.
SELF_HARM_TOPIC_OFF = (
    r"\b(?:course|essay|dissertation|talk|lecture|workshop|training|charity|article|book|"
    r"stud(?:y|ies)|research|film|documentary|paper|conference|lesson|class|exam|revision|"
    r"homework|awareness)\b",
    # the role as a phrase, so a person who is a nurse is still a person: "my friend is a self
    # harm counsellor" is the job, "my nurse is self harming" is somebody at risk.
    r"\bself[-\s]?harm\s+(?:counsell?or|nurse|worker|charity|helpline|awareness|prevention|"
    r"team|service)\b",
)

# read by `_an_ordinary_helping`, which stands the self-harm reading and the first-aid rows down for
# them.
SELF_HARM_LOOKALIKE = (
    r"\b(?:on|with|against|from|by|through)\s+(?:a|an|the|some|his|her|their)?\s*"
    r"(?:tin|knife|blade|glass|sharp|nail|wire|cooker|oven|iron|kettle|pan|nettles?|bike|wall|"
    r"door|stone|gravel|rose|thorn|hook|scissors|grater|hob|razor|bat|ball|toy|swing|frame|"
    r"trampoline|slide|scooter|skateboard|climbing\s+frame|bouncy\s+castle|"
    r"barbed\s+wire)\b",
    r"\b(?:at|playing|during|in)\s+(?:netball|football|rugby|hockey|gym|sport|training|school|"
    r"playtime|the\s+park|the\s+playground)\b",
    # The same sport said as a habit rather than a moment: "every time he plays rugby" is a boy
    # who plays rugby, not a boy who hurts himself for the sake of it.
    r"\b(?:play|plays|playing|played)\s+(?:\w+\s+){0,2}"
    r"(?:netball|football|rugby|hockey|sport|sports|tennis|basketball|cricket|golf|squash|"
    r"badminton|rounders|outside|the\s+park)\b",
    # ...and the sleep, the same way round as the first person's: "my son scratches himself in his
    # sleep" is an itch or a dry skin, not the act.
    r"\bin\s+(?:his|her|their|my)\s+sleep\b",
    r"\bwhile\s+(?:he|she|they|i)\s+(?:'?s\s+|is\s+|was\s+)?(?:asleep|sleeping)\b",
    r"\bin\s+(?:his|her|their|my)\s+bed\b",
    r"\b(?:shaving|chopping|cooking|gardening|diy|ironing|baking|haircut)\b",
    r"\bby\s+accident\b", r"\baccidentally\b",
)

# ...and the itch is a lookalike of its own, because it is the one lookalike that can be beaten by
# another act in the same line: "my son picks at his spots and cuts himself" is a cut, and the spots
# must not stand the card down for it (`AN_ACT_BESIDE_THE_ITCH`, in safety.py).
AN_ITCH_LOOKALIKE = (
    # Scratching is an itch before it is an act, and the words that decide are in the line, not the
    # spelling of the person doing it. "hes scratching himself at night" was the first wording this
    # reached, and it was fixed for the joined spelling only; the same sentence with a child
    # named in it still rang, so "my son keeps scratching at night" and "my daughter has
    # threadworms and keeps scratching at night" (a deck row) were both answered by asking a
    # parent whether their child is thinking about suicide.
    # What makes it the itch:
    #   * the skin - eczema, a rash, hives, head lice, nits, threadworms, chickenpox, scabies,
    #     psoriasis, ringworm, dry skin, dandruff, an allergy, or the itch itself;
    #   * the night - scratching is worse in bed, which is why the itch is said with "at night";
    #   * how often - "a lot", "all the time", "constantly" is a condition, not a decision.
    # What makes it the act: a mark ("raw", "to bits", "until it bleeds"), the act said again
    # ("scratching himself again"), a purpose ("on purpose"), or a cut, a burn, a wish or the word
    # itself. Those keep the card, and the pet reading is `_a_pet_hurting_itself`'s.
    r"\b(?:scratch\w*|rub\w*|pick\w*)\b[^.?!]{0,25}?"
    r"\b(?:itch(?:y|ing|es)?|eczema|rash|spots|scabs|hives|dandruff|dry\s+skin|head\s+lice|"
    r"nits|threadworms?|chicken\s?pox|scabies|psoriasis|ringworm|allerg(?:y|ic)|sore|"
    r"at\s+night|at\s+bedtime|all\s+night|every\s+night|in\s+the\s+night|"
    r"a\s+lot|all\s+the\s+time|constantly|non[\s-]?stop)\b",
    # ...and the cause said first: "she has eczema and scratches herself", "the threadworms have
    # her scratching all night".
    r"\b(?:itch(?:y|ing|es)?|eczema|rash|spots|scabs|hives|dandruff|dry\s+skin|head\s+lice|"
    r"nits|threadworms?|chicken\s?pox|scabies|psoriasis|ringworm|allerg(?:y|ic))\b"
    r"[^.?!]{0,30}?\b(?:scratch\w*|rub\w*|pick\w*)\b",
)


# A lookalike plus a wish is the wish
A_WISH_OR_TALK_OF_IT = (
    r"\b(?:want|wants|wanted|wanting|wish|wishes|talk|talks|talking|mention|mentions|mentioned|"
    r"say|says|said|saying|tells?|told|thinking|thinks|thought|feels?|keeps?)\b"
    r"[^.?!]{0,22}\b(?:die|dying|end\s+(?:it|it\s+all|things)|ending\s+it|suicide|suicidal|"
    r"kill\s+(?:my|him|her|them)sel(?:f|ves)|not\s+be\s+(?:here|around))\b",
)

# ...and the plate does not answer for the person: "i cut myself a slice of cake and i cant stop
# crying" is somebody in a bad night, and the row that reads the tears should have the line.
DISTRESS_BESIDE_IT = (
    r"\b(?:crying|sobbing|in\s+tears|tearful|depressed|miserable|hopeless|worthless|"
    r"can'?t\s+cope|cant\s+cope|falling\s+apart|numb|suicidal|self[\s-]?harm|"
    r"want\s+to\s+die|killing\s+my\s*self)\b",
    # ...and the wishes said without the word suicide: "i cut myself a slice of cake and i dont
    # want to be here anymore" is the night, whatever the plate.
    r"\b(?:dont|don'?t|do\s+not)\s+want\s+to\s+be\s+here\b",
    r"\bbetter\s+off\s+without\s+me\b",
    r"\bno\s+point\s+(?:in\s+)?(?:going\s+on|living)\b",
    r"\b(?:cant|can'?t)\s+go\s+on\b",
    r"\bend\s+it\s+all\b",
    # ...and the worry is beside the plate too: "she cuts herself a slice of cake and im worried
    # about her" is somebody asking about a person they are afraid for, and the cake answers the
    # plate instead of the worry. The chat row reads that line well on its own, so the stand-down
    # hands it over rather than keeping the card.
    r"\b(?:worried|worrying|concerned|frightened|scared|afraid)\s+(?:about|for|that)\b",
    # ...and the person who has gone quiet or stopped eating: "she has been quiet all week" and
    # "she isnt herself" are the same worry without the word.
    r"\b(?:not|isn'?t|hasn'?t|has\s+not)\s+(?:been\s+)?(?:her|him|them)sel(?:f|ves)\b",
    r"\b(?:gone\s+quiet|has\s+been\s+quiet|stopped\s+eating|not\s+eating|off\s+her\s+food|"
    r"off\s+his\s+food)\b",
)

# ...but a wish is also how people say "very". "im so tired i wish i was dead" and "i laughed so
# hard i wished i was dead" are a long day, and the same reading `WISH_DEAD` already gives "dead
# tired" and "die laughing". Only the physical degree words go here: "i am so sad i wish i was
# dead" and "i am so lonely i wish i was dead" are what the card is for.
WISH_DEAD_HYPERBOLE = (
    # "im so tired of it all and i wish i was dead" is not a long day: the tiredness is of being
    # alive, so "of it all" takes the line back out of this stand-down and the card stays.
    r"\bso\s+(?:tired|exhausted|knackered|worn\s+out|sleepy|drowsy|bored|hungry|starving|"
    r"thirsty|full|stuffed|hot|cold|freezing|sore|aching|busy|snowed\s+under|laughing|"
    r"embarrassed|hungover|old|fat|slow)\b(?!\s+of\s+(?:it|all|life|everything|this|the\s+world)\b)"
    r"[^.?!]{0,40}\bwish\w*\b",
    # "i laughed so hard i wished i was dead" - the degree is "hard", and the laugh is what says
    # it is a joke rather than a plan.
    r"\blaugh(?:ed|ing|s)?\b[^.?!]{0,30}\bwish\w*\b",
)

# A place after "here" is an evening, not a plan: "i wish i wasnt here at this wedding" is a bad
# party, and the same line without the place is still the wish. A bare "i wish i wasnt here" rings.
# "at all" is not a place: it is how the wish is finished, so it stays the wish.
# A TIME after "here" is not a place, and standing the wish down for one was the worst thing this
# guard did: "i dont want to be here in december" is the same wish with a date on it, and the
# stand-down handed it to the greeting ("Got it. Is there anything you'd like a hand with?"), to
# the landlord-repairs card ("i dont want to be here in a month"), to the party card ("on my
# birthday") and to the Christmas-film card ("at christmas"). Only a place somebody can be in
# stands the wish down, so what follows the preposition must not be a month, a day, a season, an
# occasion or a length of time.
WISH_DEAD_WHEN = (
    r"(?:january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"(?:my|our|the|his|her)?\s*(?:birthday|wedding\s+day)|christmas|xmas|easter|"
    r"(?:the\s+)?new\s+years?|spring|summer|autumn|winter|half\s+term|(?:the\s+)?weekend|"
    r"today|tonight|tomorrow|this\s+(?:week|month|year|weekend|evening|morning)|next\s+\w+|"
    r"a\s+(?:day|week|fortnight|month|year|minute|hour)|an\s+hour|"
    r"\d+\s*(?:days?|weeks?|months?|years?|hours?)|the\s+end\s+of\s+the\s+(?:week|month|year))"
)

WISH_DEAD_PLACE = (
    r"\bi\s+wish\w*\s+i\s+(?:wasnt|wasn'?t|was\s+not)\s+(?:here|around)\s+"
    r"(?:at\b(?!\s*(?:all\b|the\s+time\b))|in|on|with|near)\s+"
    r"(?!(?:the\s+)?" + WISH_DEAD_WHEN + r"\b)",
    r"\bi\s+(?:dont|don'?t|didnt|didn'?t)\s+want\s+to\s+be\s+(?:here|around)\s+"
    r"(?:at\b(?!\s*(?:all\b|the\s+time\b))|in|on|with|near)\s+"
    r"(?!(?:the\s+)?" + WISH_DEAD_WHEN + r"\b)",
)

# A death the speaker knows is not a lesson, even when it is talked about in a class: "someone in
# my class died by suicide" is a bereavement and has its own answer on the other side, so the
# lesson reply must not take it. The words a death is actually said with, all of them in the past.
LOSS_SAID = (
    r"\b(?:died|dies|dying|dead|passed\s+(?:away|on)|funeral|burial|cremation|buried|"
    r"killed\s+(?:him|her|them)self|killed\s+himself|took\s+(?:his|her|their)\s+own\s+life|"
    r"ended\s+(?:his|her|their)\s+own\s+life|committed\s+suicide|lost\s+(?:my|our|his|her|their|the)\s+\w+|"
    r"we\s+lost\s+\w+)\b",
)

# ...but a lesson the speaker cannot stop turning over is not a topic any more: "i read about
# suicide in class and now i keep thinking about it" and "we talked about it in class and i feel
# like doing it" are the person's own thought or wish, and the crisis reply is the one for them.
SELF_RUMINATION = (
    r"\b(?:keep|kept|still|can'?t\s+stop|cannot\s+stop)\b[^.?!]{0,40}\b(?:thinking|think|"
    r"thought|wondering|imagining)\b",
    r"\b(?:thinking|thought|wondering)\s+(?:about|of)\s+(?:doing\s+)?it\b",
    # A lesson that set them off is the reader too, and it is said in the past: "our teacher talked
    # about suicide today and it made me think about doing it", "suicide came up at school and i
    # think about it every night". Neither has `keep` or `can't stop` in it, so both were the
    # lesson reply on the last head.
    r"\bmade\s+me\s+(?:think|wonder)\s+(?:about|of)\b",
    r"\bthink(?:s|ing)?\s+(?:about|of)?\s*it\s+(?:every|all\s+the|each)\s+"
    r"(?:night|day|time|morning)\b",
    r"\b(?:feel\s+like|felt\s+like|want\s+to|wanted\s+to|going\s+to|gonna|might|tempted\s+to)"
    r"\s+(?:do|doing|try|trying|end)\s+(?:it|something|this|things)\b",
)

# A thing can be suicide and the speaker still be fine: "this job is suicide" is a bad job,
# "the m25 at 5pm is suicide" is traffic, "playing that team is suicide" is a fixture. The word
# is doing the work of "a terrible idea" and the crisis card is a non-sequitur, so the subject
# has to be a thing - a job, a drive, a route, a climb, a plan - named right before "is suicide".
# A bare "this is suicide" stays the crisis card, because that one can be a person's own plan.
THING_THAT_IS_SUICIDE = (
    r"(?:job|jobs|work|shift|shifts|rota|commute|drive|driving|cycle|ride|run|route|road|lane|"
    r"motorway|m25|m1|m6|a1|a3|a4|climb|descent|hike|walk|hill|slope|piste|traffic|weather|"
    r"plan|idea|option|choice|move|career|course|diet|exam|interview|pitch|season|fixture|trip|"
    r"deal|deadline|rent|mortgage|timetable|schedule|sale|launch|market|game|match|tactic|team)"
)

SUICIDE_ABOUT_A_THING = (
    r"\b(?:this|that|the|my|his|her|our|their|your|a|an)\s+(?:\w+\s+){0,2}"
    r"" + THING_THAT_IS_SUICIDE + r"\b[^.!?]{0,30}\b(?:is|was|'s|would\s+be|will\s+be|"
    r"must\s+be)\s+(?:pure\s+|total\s+|absolute\s+|outright\s+)?suicid(?:e|al)\b",
    # "career suicide" is the idiom and nothing else: no one means their life by it.
    r"\bcareer\s+suicid(?:e|al)\b",
    # "it's suicide to drive down there at five", "it would be suicide to take that job".
    r"\b(?:it'?s|its|it\s+is|it\s+was|it'?d\s+be|it\s+would\s+be)\s+"
    r"(?:pure\s+|total\s+|absolute\s+)?suicid(?:e|al)\s+to\b",
    # The subject of "is suicide" is often the doing of the thing rather than a noun: "going out
    # in that wind is suicide", "doing that at your age is suicide", "cycling on that road is
    # suicide". The gerund is an everyday activity, so the sentence is about the activity; a
    # gerund of harm ("cutting myself is suicide") is not in the list and keeps the card.
    # ...and the gerund needs the thing it is done to, or "that": "going out in that wind",
    # "cycling on that road", "doing that at your age". "going on is suicide" and "keeping going
    # is suicide" are the person's own life and keep the card.
    r"\b(?!(?:going|carrying)\s+on\s+(?:is|was|would|'?s|and|like|any|much\s+further)\b)"
    r"(?:going|driving|cycling|walking|climbing|running|commuting|working|eating|drinking|"
    r"flying|sailing|swimming|skiing|snowboarding|surfing|dating|studying|shopping|travelling|"
    r"traveling|moving|wearing|betting|buying|opening|marrying|getting|booking|hiking|camping|"
    r"jogging|rowing|parking|queuing)(?:\s+(?:out|in|on|up|down|through|with|to|for|at|off|"
    r"across|around|round|over|back)){1,2}\s+"
    # ...and the object has to be named, so the sentence is about that thing: "in that wind", "on
    # that road", "to work". A bare "going out is suicide for me" names no object and is a person
    # saying how an ordinary thing feels, which is the card.
    r"(?:(?:that|this|these|those|the|a|an|my|his|her|their|our|your)\s+\w|work\b|school\b|"
    r"college\b|uni\b)[^.?!]{0,40}\b"
    r"(?:is|was|would\s+be|'?s)\s+(?:pure\s+|total\s+|absolute\s+|outright\s+)?"
    r"suicid(?:e|al)\b",
    r"\b(?:doing|trying|taking|starting|going)\s+(?:that|this|it)\b[^.?!]{0,30}\b"
    r"(?:is|was|would\s+be|'?s)\s+(?:pure\s+|total\s+|absolute\s+|outright\s+)?"
    r"suicid(?:e|al)\b",
)

# The idiom span itself is not the wish: cut it away and read the rest of the sentence. A person
# who writes "i nearly killed myself carrying that sofa" and then nothing else is telling a story;
# one who writes "i nearly killed myself carrying that sofa and i hate myself" is telling you where
# they are. The remainder is what decides, so no list of postscripts is ever complete.
# "i wanted to die of embarrassment" and "i want to die my hair pink" are the same words as the
# wish and no wish at all, so both the frame and the phrase go together when the rest of the line is
# read. Cutting only "of embarrassment" left "i wanted to die" behind, which reads as the wish.
DIE_OF_THE_FEELING = (
    r"\b(?:want\w*|wish\w*|feel\w*|felt|think\w*|thought|going|gonna|nearly|almost)\b"
    r"(?:[\s,]+[a-z']+){0,3}\s+(?:to\s+)?(?:die|dying|died)\s+(?:of|from)\s+"
    r"(?:embarrass\w*|boredom|thirst|curiosity|laughter|shame|fright)\b",
    r"\b(?:die|dyed|dyeing|dying)\s+my\s+hair\b",
)

# A figure of speech in the line does not clear a wish said plainly in the same one. "work is
# killing me and i keep thinking about suicide" and "my back is killing me, i feel like ending it
# all" were answered as small talk, because "killing me" is the idiom and the minor-injury arm
# below dropped the whole line before the self-harm case was ever reached. These are the words
# that name the speaker's own death with no figure in them.
WISH_NAMED = (
    r"\bsuicid(?:e|al)\b",
    r"\bself[-\s]?harm(?:ing|ed)?\b",
    r"\b(?:want|wanted|wanting|need|needed|like)\s+to\s+die\b(?!\s+(?:of|laughing))",
    r"\b(?:think|thinks|thinking|thought|thoughts?)\s+(?:about|of)\s+(?:dying|suicide|"
    r"self[-\s]?harm|killing\s+my\s*self|ending\s+it)\b",
    r"\bend(?:ing)?\s+(?:it|my\s+(?:own\s+)?life|it\s+all)\b",
    r"\b(?:don'?t|do\s+not|doesn'?t)\s+want\s+to\s+(?:live|be\s+here|exist|wake\s+up|go\s+on)\b",
    r"\bbetter\s+off\s+(?:dead|without\s+me|if\s+i\s+was\s+gone|if\s+i\s+weren'?t\s+here)\b",
    r"\b(?:hurt|hurting|cut|cutting|kill|killing|harm|harming)\s+my\s*self\b",
)

# Something that happened a while ago and is still going on is happening now: a fall two weeks ago
# with the person still on the floor is an ambulance, while "i broke my wrist when i was 12" is not.
# "and he is fine now" is the same line told as history: the "now" in it is the recovery, not the
# fit, so it must not switch a week-old story back to a call happening this minute.
FIT_ALL_BETTER = (
    r"\b(?:is|was|feels?|seems?|looks?)\s+(?:much\s+|totally\s+|completely\s+|absolutely\s+)?"
    r"(?:fine|ok|okay|alright|better|himself|herself|themselves|normal)\s+(?:again\s+)?now\b",
    r"\b(?:now|since\s+then)\s+(?:he|she|they)\s+(?:is|are|seems?|feels?|was)\s+"
    r"(?:fine|ok|okay|alright|better|normal)\b",
)

STILL_GOING = (
    r"\b(?:can'?t|cannot|can\s+not|unable\s+to)\s+(?:get\s+up|move|walk|stand|feel)\b",
    r"\b(?:stuck|trapped)\b", r"\bwon'?t\s+(?:wake|get\s+up)\b",
    r"\bis\s+still\s+(?:on\s+the\s+floor|there|stuck|bleeding|in\s+pain)\b",
    r"\bhasn'?t\s+(?:stopped|shifted|got\s+up)\b", r"\bstill\s+(?:in|on)\s+(?:bed|the\s+floor)\b",
)

OLD_TIME = (
    r"\b(?:in\s+)?(?:19|20)\d\d\b", r"\b(?:years?|months?|decades?|weeks?)\s+ago\b",
    r"\bwhen\s+i\s+was\s+(?:\d+|a\s+kid|a\s+child|young|little|at\s+school)\b",
    # The same story about someone else: "my son had a seizure when he was a baby" is history
    # too, and it is the relative's age that puts it back, not the user's.
    r"\bwhen\s+(?:i|he|she|they|we)\s+(?:was|were)\s+(?:\d+|a\s+kid|a\s+child|a\s+baby|"
    r"a\s+toddler|a\s+tot|an\s+infant|young|little|small|at\s+school|born)\b",
    # "my son had a fit last week, is that bad" is the same week-old story as "a week ago".
    r"\blast\s+(?:year|summer|winter|decade|century|week|month)\b", r"\bused\s+to\b",
    # "she fell last month and broke her wrist" is a month-old fracture, not this minute: the fall
    # and what it broke are the story, and the answer to it is not "get to A&E now".
    r"\b(?:fell|fallen|had\s+a\s+fall|broke|fractured|dislocated|sprained)\b[^.?!]{0,30}"
    r"\blast\s+(?:week|month)\b",
)

# An attempt that already happened is still the attempt. "i took an overdose last week", "i tried
# to hang myself last week", "i laid on the train tracks last week" and "i cut my wrists last week"
# were all answered with "Got it. Is there anything you would like a hand with?", because the time
# on the line stood the whole crisis card down. The week changes what to do about it - there is no
# ambulance to call now - not whether it is worth telling somebody about.
# A drug is a name, not a container: "a load of washing round to my mums" and "a packet of crisps"
# are the same words as a dose and neither one is a dose. Every container arm reads this list after
# the "of", so the packet is only a dose when a drug is named in it.
DRUG_NAME = (
    r"(?:pills?|tablets?|capsules?|paracetamol|ibuprofen|aspirin|painkillers?|sleeping\s+pills?|"
    r"antidepressants?|co-?codamol|codeine|tramadol|morphine|methadone|insulin|lithium|valium|"
    r"diazepam|temazepam|xanax|heroin|heroine|cocaine|opioids?|opiates?|drugs?|meds|medication|"
    r"medicines?|antihistamines?|antibiotics?|iron\s+tablets|vitamins?|laxatives?|diuretics?|"
    r"beta\s+blockers?|statins?)"
)

# The edge of a bridge has no other reason to be stood on; the edge of a station platform is where
# everybody waits for a train, so that one carries the thought with it or it is nothing.
EDGE_OF_A_DROP = (
    r"\b(?:stood|standing|sat|sitting|walked)\b[^.?!]{0,10}\b(?:on|at)\s+the\s+edge\s+of\s+"
    r"(?:a\s+|the\s+)?(?:bridge|roof|building|cliff|car\s*park)\b",
    r"\b(?:stood|standing|sat|sitting|walked)\b[^.?!]{0,10}\b(?:on|at)\s+the\s+edge\s+of\s+"
    r"(?:a\s+|the\s+)?(?:platform|tracks?)\b(?=[^.?!]*\b(?:thought|thinking|wanted|want|nearly|"
    r"almost|about\s+to|going\s+to|close\s+to|jump|jumped|looked\s+down|someone|police|pulled|"
    r"grabbed|swaying|drunk|end\s+it|easy)\b)",
)

# "i tried to end it with my girlfriend last week" is a break-up: ending a relationship is the same
# verb as ending a life. The noun after the "with" is what says which one it is, but it cannot be an
# allowlist of people and jobs - that list never ends (a bank, a gym, an insurer, a mobile contract)
# and any noun not on it fell through to the crisis card. "Ended it with" is the past tense of the
# same sentence and the old arm only read "end it" and "ending it".
#
# So the arm runs the other way: a means after the "with" rings, and anything else after it stands
# the attempt down. "Tried to end it with pills" or "... with a knife" is the way out; "ended it with
# him", "end it with my gym", "end it with the bank" are break-ups and cancellations.
END_IT_WITH_A_THING = (
    r"\bend(?:ed|ing|s)?\s+it\s+(?:with|by|using|between)\b",
    # "i tried to end it by hanging" and "off the bridge" name the means after a different word, so
    # the means is read on its own as well as behind "with".
    r"\bend(?:ed|ing|s)?\s+it\s+(?:by|off|on|under|in)\s+(?:the\s+)?(?:bridge|train|tracks|railway)\b",
)

END_IT_MEANS = (
    r"\b(?:pills?|tablets?|painkillers?|paracetamol|antidepressants?|meds?|medication|"
    r"an?\s+overdose|overdosing|a\s+knife|the\s+knife|a\s+razor|a\s+blade|a\s+rope|"
    r"a\s+belt|a\s+ligature|a\s+gun|a\s+shotgun|gas|the\s+car|a\s+car|the\s+train|"
    r"a\s+train|drowning|a\s+bridge|the\s+bridge|something\s+sharp|"
    # the means a lot of people actually use, said plainly
    r"hang(?:ing|ed)?|alcohol|drink|drinking|vodka|whisky|whiskey|gin|tablets|"
    r"my\s+wrists?|my\s+own\s+life)\b",
)

# The recent window, for an attempt and a wish only. It is kept out of OLD_TIME on purpose: "last
# night" is very often the live event - a fit, an attack, a collapse, a carbon monoxide alarm - and
# the gate that reads OLD_TIME passes those lines on as old stories. Here the question is only
# whether the attempt has a time on it, and "i tried to end it last night" is yesterday's attempt
# exactly as "last week" is.
RECENT_TIME = (
    r"\b(?:yesterday|last\s+night|last\s+evening|this\s+(?:morning|afternoon|evening)|"
    r"earlier(?:\s+today)?|a\s+few\s+(?:days?|weeks?)\s+ago|"
    r"a\s+couple\s+of\s+(?:days?|weeks?)\s+ago|recently|"
    r"on\s+(?:mon|tues|wednes|thurs|fri|satur|sun)day|"
    r"(?:at|over|during)\s+the\s+weekend|last\s+weekend)\b",
)

# The scars of it, said with no verb at all: "i have cuts on my wrists", "i have got scars on my
# arms", "my daughter has cuts on her arms". It was answered "Noted: you have cuts on your wrists",
# which is the one reply nobody should get for this. The place has to be one people cut themselves
# on purpose - a hand, a finger and a knee are accidents, and "i have cuts on my hands from work" is
# left alone by the cause guard beside it.
SELF_HARM_SCARS = (
    # Plural on purpose. One cut on a wrist is a kitchen knife and it belongs to the first aid; a
    # set of them on a place people cut themselves is the telling.
    r"\b(?:have|got|has|had|covered\s+in|full\s+of)\b[^.?!]{0,15}"
    r"\b(?:cuts|scars|scratches|burn\s*marks|slashes)\b[^.?!]{0,12}"
    r"\b(?:on|across|down|up)\s+(?:both\s+)?(?:my|his|her|their|your)\s+"
    r"(?:wrists?|arms?|forearms?|thighs?|tummy|stomach|belly)\b",
    # the same scars named as the thing, with the body part in front of them
    r"\b(?:my|his|her|their)\s+(?:wrists?|forearms?|thighs?)\b[^.?!]{0,10}"
    r"\b(?:are|is|r)\s+(?:all\s+)?(?:scars?|scarred|cut\s+up|covered\s+in\s+scars?)\b",
)

# The cause guard for the scars, and it is not PAST_ATTEMPT_NOT: that one reads "on my wrists" as
# the thing the body hit, which is the whole shape of a scar line, and it stood the card down.
SELF_HARM_SCARS_NOT = (
    r"\b(?:from|off)\s+(?:the|a|an|my|our|his|her|their)\s+(?:cat|dog|puppy|kitten|pet|rabbit|"
    r"hamster|hedgehog|parrot|budgie|horse|pony|bike|motorbike|car|van|ladder|shelf|barbecue|"
    r"oven|hob|cooker|kettle|toaster|knife|blade|glass|tin|can|tool|drill|saw|mower|gate|fence|"
    r"nails?|rose|bush|brambles?|thorns?|shower|tap|bath|door|window|cupboard|drawer|work|job|"
    r"office|school|nursery|garden|allotment|kitchen|garage|shed|building\s+site|farm|"
    r"football|rugby|hockey|netball|climbing|cycling|gardening|diy|cooking|chopping|shaving|"
    r"washing\s+up|hoovering|cleaning|moving|flat|house|home)\b",
    r"\b(?:at|from)\s+(?:work|the\s+garden|the\s+allotment|the\s+tip|the\s+shops?)\b",
    r"\b(?:on|off)\s+(?:a|an|the|some)\s+(?:knife|blade|glass|tin|can|nail|screw|wire|fence|"
    r"barbed\s+wire|thorn|rock|stone|kerb|roof|wall|door|drawer|bike|motorbike|car|mower|tool)\b",
    r"\b(?:while|when)\s+(?:i\s+was\s+|i'm\s+)?(?:cooking|chopping|shaving|carving|cutting|"
    r"peeling|washing\s+up|gardening|diy|working|cleaning|hoovering|painting|decorating)\b",
    r"\b(?:acne|spot|spots|chickenpox|eczema|psoriasis|rash|allergy|allergic|hives|itch\w*|"
    r"surgery|operation|scarred\s+from\s+the)\b",
)

SPOKEN_ATTEMPT_UNDATED = (
    *SELF_HARM_SCARS,
    r"\b(?:tried|try|tries|trying|attempted|attempt|attempts|attempting|went\s+to|"
    r"nearly|almost)\b"
    r"[^.?!]{0,25}\b(?:end(?:ed|ing)?\s+it|kill(?:ing)?\s+my\s*self|end\s+my\s+life|"
    r"(?:take|took)\s+my\s+own\s+life|end(?:ed)?\s+my\s+life|suicide|"
    r"hang(?:ing|ed)?\s+my\s*self|jump\s+off)\b",
)

# ...and the words that make the same cut an accident: a kitchen, a pane of glass, a craft word.
# A joke is the other accident - "i nearly killed myself laughing" is a film, not an evening.
PAST_ATTEMPT_NOT = (
    # A thing on the line is what the body hit - "on a fence", "on a tin", "on the glass" - and a
    # craft is what it was doing. "on purpose" is the opposite and stays out of this arm.
    r"\b(?:on\s+(?:(?:a|an|the|some|my)\s+)?(?!purpose\b)[a-z]+|while\s+(?:cooking|chopping|"
    r"shaving|carving|cutting|peeling|washing\s+up|gardening|diy|working)|chopping|carving|"
    r"peeling|shaving|gardening|trimming|pruning)\b",
    r"\b(?:laughing|of\s+laughter|off\s+my\s+bike|on\s+the\s+stairs|tripping|embarrass\w*|"
    r"mortified)\b",
)

# A wish or a plan said in the past tense with a time on it falls through the same gate as an act:
# "i wanted to kill myself last week" is a person telling you where they were, and the week on the
# line changes what to do now, not whether it is worth answering. The wish has to be their own and
# about themselves, and "i thought i was going to die" is a fright, not a wish.
PAST_WISH = (
    r"\bi\b[^.?!]{0,24}\b(?:wanted|wanting|thought\s+about|thought\s+of|thoughts\s+about|"
    r"kept\s+thinking\s+about|kept\s+thinking\s+of|thinking\s+about|thinking\s+of|planned|"
    r"planning|was\s+going\s+to|was\s+planning\s+to|felt\s+like|considered|dreamt\s+about)"
    r"\b[^.?!]{0,18}\b(?:kill\s+my\s*self|killing\s+my\s*self|end\s+it\s+all|"
    r"ending\s+it|end\s+my\s+life|ending\s+my\s+life|die|dying|suicide|suicidal|not\s+be\s+here|"
    r"disappear|hurt\s+my\s*self|cutting\s+my\s*self|self\s*harm)\b",
    # "i felt suicidal last week" has no verb to read, so the state itself is the arm.
    r"\bi\b[^.?!]{0,20}\b(?:felt|was|were|have\s+been|had\s+been|been|got)\b[^.?!]{0,8}"
    r"\b(?:suicidal|feeling\s+suicidal)\b",
)

# The effort frame: "i nearly killed myself carrying that sofa" is a near thing with a heavy
# thing, not a wish. What says so is the word straight after the phrase - the job they were doing
# in the -ing form ("carrying", "moving house", "shovelling gravel"), or the place it went wrong
# ("at the gym", "on my bike", "on the stairs"). A self-harm word in that place is the act itself
# ("nearly killed myself cutting"), so those keep the card.
EFFORT_AFTER = re.compile(
    r"\b(?:nearly|almost)\b[^.?!]{0,24}\b(?:killed|kill)\s+my\s*self\s+"
    r"(?:at\s+the\s+(?:gym|pool|park|tip)|"
    r"on\s+(?:the\s+|my\s+|a\s+)?(?:bike|bicycle|stairs|steps|staircase|ladder|roof|"
    r"treadmill|run|road|motorway|trampoline|pitch|hill|scaffold)\b|"
    # The fall said from the thing rather than the surface: "off my bike" is a tumble, and it is
    # the same accident as "on my bike" - main answered "i nearly killed myself off my bike last
    # week" with a crisis line. Only what a person rides or stands on is here, so "off the bridge"
    # names a means and stays out (EFFORT_MEANS).
    r"off\s+(?:the\s+|my\s+|a\s+)?(?:(?:back|front)\s+of\s+(?:a|the|my)?\s*)?"
    r"(?:bike|bicycle|motorbike|motorcycle|moped|scooter|horse|pony|ladder|roof|wall|"
    r"scaffold|trampoline|skateboard|skis|boat|truck|lorry|van|trailer)\b|"
    r"(?P<doing>[a-z']+ing)\b)",
)

# A wish said as a thing that nearly happened carries no date and needs none: "i wish the accident
# had killed me" is a wish now, not a story from last week.
PAST_WISH = PAST_WISH + COUNTERFACTUAL_WISH

# The wish that is not a wish: dying of embarrassment, of boredom, of laughter, and the fright of
# "i thought i was going to die when the car skidded".
PAST_WISH_NOT = (
    r"\b(?:of|from)\s+(?:embarrass\w*|boredom|thirst|curiosity|laughter|shame|fright)\b",
    r"\b(?:die|dying|died)\s+(?:laughing|of)\b",
    r"\bthought\s+(?:i|that\s+i)\s+(?:was|were)\s+(?:going\s+to|about\s+to|gunna)\s+die\b",
    r"\bfelt\s+like\s+(?:i|that\s+i)\s+(?:was|were)\s+(?:going\s+to|about\s+to)\s+die\b",
    r"\b(?:scared|afraid|terrified|convinced)\b",
)

# "i overdosed on cake" is a joke about eating too much, and so is "a overdose of chocolate": the
# 999 card belongs to a drug. A drug word anywhere on the line keeps the card, and a food word with
# no drug word stands it down, which is what "i overdosed on cake" was otherwise getting.
OVERDOSE_FOOD = (
    r"\boverdos(?:e|ed|ing)\b[^.?!]{0,12}\b(?:on|of|with)\s+(?:the\s+|a\s+|some\s+)?"
    r"(?:cake|cakes|chocolate|sweets|candy|biscuits?|cookies|crisps|chips|chinese|curry|pizza|"
    r"ice\s*cream|cheese|coffee|tea|netflix|tv|telly|sugar|bread|"
    r"pastr(?:y|ies)|do(?:ugh)?nuts|burgers?|takeaways?|naps|love|pies?|pudding|trifle|"
    r"turkey|roast|stuffing|mince|gravy|easter\s+eggs?)\b",
)

OVERDOSE_DRUG = (
    r"\b(?:pills?|tablets?|paracetamol|ibuprofen|painkillers?|meds|medicines?|"
    r"sleeping\s+pills?|antidepressants?|insulin|heroin|heroine|cocaine|methadone|tramadol|"
    r"codeine|morphine|opioid|opiates?|drugs?|liquid|bottle|packet|pack|box|strip|blister)\b",
    # A bottle of spirits is how a lot of people do it, so a drink is the drug and not the joke:
    # "i overdosed on vodka" was standing the card down with the cake.
    r"\b(?:alcohol|vodka|whisky|whiskey|wine|beer|gin|rum|brandy|tequila|lager|cider|champagne|"
    r"prosecco|ros\u00e9|spirits?|drink|drinking|booze)\b",
)

CHEST_WORK = (
    r"\bchest\b.{0,30}\b(?:after|during|when)\s+(?:the\s+|a\s+|my\s+)?"
    r"(?:gym|run|running|jog|jogging|workout|exercise|exercising|swim|swimming|cycle|cycling|"
    r"football|netball|walk|walking|stairs|climbing|training|weights|lifting)\b",
    r"\bchest\b.{0,30}\b(?:when\s+i\s+(?:run|walk|climb|exercise|train|cycle|swim|lift))\b",
    r"\bafter\s+(?:the\s+|a\s+)?(?:gym|run|workout|training)\b.{0,30}\bchest\b",
)

CHEST_SLOW = (
    r"\bchest\b.{0,45}\b(?:for\s+(?:a\s+(?:few|couple)\s+(?:days|weeks)|\d+|two|three|four|five|"
    r"several|weeks?|months?|days?)\s*(?:days|weeks|months|years)?|for\s+months|for\s+ages|"
    r"comes?\s+and\s+goes|keeps?\s+coming\s+back|on\s+and\s+off|since\s+(?:last|christmas)|"
    r"\d+\s+(?:days|weeks|months)\s+now)\b",
)

CHEST_URGENT = (
    r"\b(?:can'?t|cannot|couldn'?t)\s+breathe\b", r"\bshort\s+of\s+breath\b",
    r"\b(?:crushing|squeezing|heavy)\b", r"\bspreading\b", r"\bsweat\w*\b",
    r"\bcollapsed\b", r"\b(?:going|gone|turning)\s+blue\b", r"\bpassed\s+out\b",
    r"\bright\s+now\b", r"\bthis\s+(?:morning|afternoon|evening)\b", r"\bjust\s+happened\b",
    # A chest pain that arrived in one moment is not a strain, whatever it arrived with: a sudden
    # pain in a coughing fit is a pneumothorax before it is a muscle, and `my chest pain came on
    # suddenly while i was coughing` was the muscle answer (teal-spruce, #10407).
    r"\b(?:sudden(?:ly)?|all\s+of\s+a\s+sudden|out\s+of\s+nowhere)\b",
    r"\b(?:came|come|comes|coming)\s+on\s+(?:suddenly|all\s+of\s+a\s+sudden|out\s+of\s+nowhere)\b",
)

# A dog that keeps biting is a habit to train, not an attack in progress. The attack arms below
# carry "biting", so every one of these lines rang 999: "my dog keeps biting me" and "how do i
# stop my dog biting" got "Call 999 or 911 now, and don't put yourself in the way". A habit word
# stands both dog cases down, unless the line says the dog has hold of someone now.
DOG_HABIT = (
    r"\b(?:keeps?|kept|always|sometimes|occasionally|now\s+and\s+then|every\s+time|"
    r"has\s+started|started|used\s+to|since\s+(?:he|she|the\s+dog)|has\s+become|"
    r"getting\s+worse|how\s+do\s+i\s+stop|how\s+to\s+stop|stop\s+(?:him|her|it|them)\b|"
    r"any\s+advice|train|training|behaviourist|behaviour)\b",
    # A bite with a condition round it is a habit, not a bite in progress: "my dog bites me when i
    # take his food" is the resource-guarding question and it rang 999.
    r"\b(?:when|whenever|while|if|as\s+soon\s+as|before|after)\s+"
    r"(?:i|we|he|she|they|you|someone|anyone|the\s+(?:vet|postman|kids))\b",
    r"\b(?:take|taking|touch|touching|reach\s+for|go\s+near|going\s+near|stroke|stroking|"
    r"pet|petting|pick\s+up|picking\s+up|move|moving)\b[^.?!]{0,20}"
    r"\b(?:his|her|their|the)\s+(?:food|bowl|bone|toy|bed|lead|collar|chew)\b",
)

# ... and a bite whose first object is a thing, with the person only joined on by "and", is a dog
# mouthing the lead and catching a hand: "my dog is biting the lead and my hand" rang 999, and the
# yelp-and-redirect answer is the right one for it.
DOG_MOUTHING = (
    r"\b(?:bit|bite|bites|biting|nipped|nipping|nips|snapped\s+at|chewing|chewed)\s+"
    # A mouth on a toy, a lead or a sleeve with a hand caught second is a soft turn. A door, a gate
    # or a fence is not something a dog mouths in play, and "biting the door and my fingers" is a
    # person with their fingers in a dog's mouth at that moment, so those three stay on the alarm.
    r"(?:at\s+)?(?:the|a|an)\s+(?:lead|leash|toy|stick|bone|cushion|blanket|"
    r"sofa|bed|sleeve|shoe|shoes|trouser\s+leg)\b[^.?!]{0,30}\band\s+(?:my|me)\b",
)

# A dog biting at itself is an itch, not an attack: "my dog keeps scratching and biting himself"
# read as dog + biting and rang 999. The alarm stands down for a self-directed bite - the reflexive
# or a body part of the animal's own - or for an itch, skin or flea line about the animal, and it
# still rings for every bite with a person in it (see DOG_BIT_A_PERSON), because the objects below
# and a person's hand can be in the same line: "my dog is biting the lead and my hand".
DOG_SELF_BITE = (
    r"\b(?:bit|bite|bites|biting|nipped|nipping|nips|snapped)\b[^.?!]{0,15}"
    r"\b(?:himself|herself|itself|themselves)\b",
    r"\b(?:bit|bite|bites|biting|nipped|nipping|nips|snapped)\s+(?:at\s+)?(?:his|her|its|their)\s+"
    r"(?:own\s+)?(?:paws?|feet|foot|pads?|tail|legs?|fur|coat|skin|ears?|flank|back|bed|blanket|"
    r"lead|cage|bedding)\b",
    # the same objects with "the" or "a" in front of them, which is how people write half the time
    # ("my dog is biting the lead"); only things that are never a person are listed
    r"\b(?:bit|bite|bites|biting|nipped|nipping|nips|snapped)\s+(?:at\s+)?(?:the|a|an)\s+"
    r"(?:lead|leash|cage|blanket|bedding|bed|toy|stick|bone|chew|kong|ball|cushion|pillow|"
    r"sofa|gate|fence|door)\b",
)

# A bite or an attack that lands on an animal is the vet's, not a person's first aid: "a dog bit
# my cat" reached BITE_DONE, which is written for a person, and the answer said a bite on the face
# or hand goes to A&E. The animal owns the wound, so the vet answers and the dog warden follows.
PET_NAMES = (r"(?:cat|cats|dog|dogs|puppy|puppies|kitten|kittens|pup|pups|rabbit|rabbits|bunny|"
             r"hamster|hamsters|guinea\s+pig|guinea\s+pigs|pony|ponies|horse|horses|pet|pets|"
             r"bird|birds|parrot|parrots|budgie|budgies|ferret|gerbil|tortoise|"
             r"chicken|chickens|hen|hens|duck|ducks|goat|goats|sheep|lamb|lambs)")

BITE_ON_ANIMAL = (
    # "a dog bit my cat", "next doors dog savaged our rabbit", "the cat was attacked by a dog"
    # Only what one animal does to another. "hurt" and "killed" are how a person describes a pet
    # that was injured or died - "my cat got hurt", "my dog was attacked by fleas" - and with a
    # possessive pet after them they turned a plain injury into a dog attack, warden and all. An
    # attack has to name an attacker, so "attacked by fleas, ticks or bees" is a vet's day, not an
    # attack to report.
    r"\b(?:bit|bite|bites|biting|bitten|nipped|nips|snapped\s+at|snaps\s+at|went\s+for|"
    r"goes\s+for|going\s+for|attacked|attacks|attacking|mauled|mauls|savaged|savages|"
    r"latched\s+onto)\b[^.?!]{0,30}\b(?:my|our|the|his|her|their|"
    r"next\s+doors?|neighbou?rs?)\s+" + PET_NAMES + r"\b",
    r"\b(?:my|our|the|his|her|their|next\s+doors?|neighbou?rs?)\s+" + PET_NAMES +
    r"\b[^.?!]{0,30}\b(?:got|was|were|has\s+been|had\s+been|have\s+been|been)\s+"
    r"(?:bit|bitten|attacked|mauled|savaged)\b"
    r"(?!\s+by\s+(?:fleas?|ticks?|bees?|wasps?|insects?|ants?|mites?|mosquitoes?)\b)",
)

# Fiction is the only thing that stands the vet answer down: "what if a dog bit my cat" is a real
# question about a real cat, and the story markers are the ones that are not. This is NOT_NOW's
# story arms alone, because its "what if" arms are the way people ask about their own animal.
FICTION_NOW = (
    r"\bfor\s+(?:a|my|the)\s+(?:story|novel|book|film|script|screenplay|essay|assignment|"
    r"character)\b",
    r"\bin\s+(?:a|my|the)\s+(?:story|novel|book|film|game|dream)\b",
    r"\b(?:story|novel|script|screenplay|essay|film)\b.*\b(?:character|plot|scene)\b",
    r"\bmy\s+(?:character|protagonist)\b",
)

OTHER_RISK = (
    r"\b(?:he|she|they|my\s+" + PERSON + r"|the\s+" + PERSON + r"|" + PERSON + r")\b.{0,30}"
    r"\b(?:wants?\s+to\s+(?:die|kill)|wanna\s+die|kill\s+(?:him|her)self|kill\s+themselves|"
    r"suicid\w*|self[-\s]?harm\w*|"
    r"end\s+(?:it|their\s+life)|doesn'?t\s+want\s+to\s+(?:live|be\s+here)|better\s+off\s+dead|"
    r"tried\s+to\s+kill|has\s+taken\s+(?:too\s+many|a\s+lot\s+of|all\s+(?:his|her|the)\s+pills))\b",
    # "she hurt herself at netball" is a bump; self-harm needs a sign that it is on purpose.
    r"\b(?:he|she|they|my\s+" + PERSON + r")\b.{0,25}"
    r"\b(?:hurt|hurts|hurting|cut|cuts|cutting|harm|harming|burning|starving)\s+"
    r"(?:him|her|them)self\b.{0,25}"
    r"\b(?:on\s+purpose|again|keeps?|kept|every\s+day|at\s+night|to\s+(?:cope|feel)|"
    r"because|won'?t\s+stop|can'?t\s+stop|deliberately|in\s+secret|in\s+private)\b",
    r"\b(?:he|she|they|my\s+" + PERSON + r")\b.{0,30}\b(?:has\s+|'s\s+)?locked\s+(?:him|her|them)self\s+"
    r"(?:in|away)\b.{0,30}\b(?:pills|tablets|pills?|knife|blades?|something\s+to\s+use|razor)\b",
    r"\b(?:he|she|they|my\s+" + PERSON + r")\b.{0,25}\b(?:keeps?|kept)\s+"
    r"(?:hurting|cutting|burning|starving)\s+(?:him|her|them)self\b",
)

SAFE_NOW = (
    r"\b(?:i'm|im|i\s+am|we're|we\s+are|they're|they\s+are|he's|she's)\s+(?:outside|out|safe|clear)\b",
    r"\b(?:breathing|feels?|looks?|seems?)\s+(?:better|easier|normally|again)\b",
    r"\bthey\s+(?:seem|look|are)\s+(?:better|okay|ok|awake)\b",
    r"\b(?:fire\s+(?:brigade|service|fighters?)|paramedics?|ambulance)\b.{0,25}\b(?:here|arrived|came|with\s+(?:us|me))\b",
    r"\b(?:it|the\s+bleeding)\s+(?:has\s+)?stopped\b",
)

# A break in the back or the neck is the spinal cord's question, and it is not first aid: the answer
# is don't move and 999. Main answered `my spine is broken` with a chat nod and
# `my neck is broken and i cant move my fingers` with "I'm listening", and the bone row's "support
# it where it is, ice it and take painkillers" is the one card that must never reach a spine.
SPINE_BREAK = (
    r"\b(?:my|the)\s+(?:back|neck|spine|spinal)\b"
    # ...and "my back gate is broken" is a gate: the same noun guard the bone row needs, because
    # the back of a person is followed by the verb and the back of a house by a noun.
    r"(?![^.?!]{0,15}\b(?:gate|door|window|fence|garden|yard|wall|room|lawn|patio|"
    r"light|pack|passage|road|bumper|seat)\b)[^.?!]{0,20}"
    r"\b(?:is|are|'?s|'?re|was|were|feels?|looks?)\s+"
    r"(?:broken|cracked|fractured|snapped)\b(?!\s+out\b)",
)

# ...and a back that went while it was working is a strain, not a spine: `my back is broken from all
# the lifting`, `... from lifting`, `... after moving the sofa` and `... from gardening` were the
# lifting card before this row existed ("bend at the hips and knees"), and the ambulance for them
# would teach somebody to ignore it. A cause that is ordinary exertion stands the row down; a fall
# or a crash does not (`my back is broken from the fall` keeps the 999 card).
SPINE_BACK_WORK = (
    r"\b(?:from|after|with|doing|lifting|moving|carrying|digging|gardening|shovelling|shoveling|"
    r"hoovering|hoover|cleaning|housework|diy|build(?:ing)?)\b",
    r"\b(?:from\s+all\s+the|from\s+the\s+lifting|from\s+lifting|all\s+the\s+lifting|"
    r"after\s+moving|after\s+the\s+move|from\s+the\s+move|moving\s+the)\b",
)

FOLLOW_UP_ANCHOR = (
    r"\b(?:999|911|112|ambulance|paramedics?|fire|brigade|smoke|stairs|outside|safe|clear|"
    r"breath\w*|cpr|pulse|conscious|awake|asleep|bleeding|blood|burn\w*|hospital|doctor|a&e|"
    r"nurse|poison\w*|pills?|tablets?|medic\w*|medicine|epipen|inhaler|police|help|waiting|"
    r"wait|call\w*|now|still|they|them|him|her|she|he|it|ok|okay|done|yes|no|thanks|anything|"
    r"something|else|that|this|scared|frightened|terrified|afraid|soak\w*|through|still)\b",
)

HELP_ARRIVED = (
    r"\b(?:ambulance|paramedics?|fire\s+(?:brigade|service|engine)|police|crew)\b[^.?!]{0,25}"
    r"\b(?:is|are|'s|was|were)\s+(?:here|outside|coming|on\s+(?:its|their|the)\s+way|"
    r"arriving|arrived|pulling\s+up|at\s+the\s+door)\b",
    r"\b(?:they|someone|somebody|my\s+(?:mum|mom|dad|husband|wife|partner|sister|brother|son|"
    r"daughter|friend|neighbour|neighbor))\b[^.?!]{0,15}\b(?:is|are|'s)\s+(?:here|outside|"
    r"with\s+me|on\s+(?:their|his|her)\s+way|coming\s+(?:over|round))\b",
    r"\b(?:im|i'?m)\s+not\s+on\s+my\s+own\b",
)

FOLLOW_UP_MORE = (
    r"\bshould\s+i\s+(?:try|open|shut|close|turn|grab|hold|press|cover|warm|sit|lie|stand|walk|drive|eat|drink|wake|ring|phone|tell|say|text|message)\b",
    r"\bcan\s+i\s+(?:open|shut|close|turn|give|move|go|drive|eat|drink|wake|ring|phone)\b",
    r"\bis\s+it\s+(?:ok|okay|safe|alright|fine)\s+to\b",
)

CASE_WORDS = {
    'gas': r"\b(?:gas|meter|windows?|doors?|flames?|lights?|switches|smell|boiler|hob)\b",
    'fire': r"\b(?:fire|smoke|flames?|stairs?|windows?|doors?|building|flat|brigade|outside|neighbours?)\b",
    'dog_attack': r"\b(?:dog|dogs|collar|lead|leash|between|barrier|shout\w*)\b",
    'dog_bite': r"\b(?:bite|bitten|wound|dog|dressing|tetanus)\b",
    'bleeding': r"\b(?:blood|cloth|bandage|dressing|pressure|bleed\w*|wound|soak\w*|through|stop\w*|stitch\w*|scar)\b",
    'self_harm': r"\b(?:crisis|line|alone|phone|talk\w*|tell|say|mum|dad|mother|father|friend|partner|wife|husband|family|sister|brother|gp|doctor)\b",
    'chest': r"\b(?:chest|arm|jaw|aspirin|door|sit\w*|walk\w*|stand\w*|move|drive|climb\w*)\b",
    'chest_slow': r"\b(?:chest|tight\w*|gp|doctor|aspirin|weeks?|pain|breath\w*)\b",
    'unconscious': r"\b(?:breathing|side|pulse|recovery)\b",
    'breathing': r"\b(?:inhaler|epipen|upright|breath\w*|wheez\w*|lips?)\b",
    'stroke': r"\b(?:face|arm|speech|slurr\w*|time|food|drink)\b",
    'head_injury': r"\b(?:head|awake|wake|drowsy|sleepy|sick|vomit\w*)\b",
    'poison': r"\b(?:packet|container|bottle|pills?|tablets?|sick|vomit\w*)\b",
    'overdose': r"\b(?:packet|container|bottle|pills?|tablets?|sick|vomit\w*|breath\w*)\b",
    'hanging': r"\b(?:rope|neck|breath\w*|side|cpr)\b",
    'seizure': r"\b(?:fitting|fit|seizure|time|mouth|side)\b",
    'heat': r"\b(?:shade|water|cool\w*|fan|sweat\w*)\b",
    'general': r"\b(?:999|911|ambulance|paramedics?|police|help|waiting|wait|call|now|they|them|him|her|ok|safe|clear)\b",
}

LOCKED_IN_RISK = (
    r"\b(?:is\s+)?(?:locked|shut|locks?|locked\s+himself|locked\s+herself|locked\s+themselves)"
    r"\b.{0,30}\b(?:in|inside|behind)\b.{0,40}\b(?:pills?|tablets?|medication|medicine|knife|"
    r"razors?|blades?|scissors|gun)\b",
    r"\b(?:pills?|tablets?|knife|razors?|blades?)\b.{0,30}\b(?:locked|shut|barricaded)\b",
)

FIRE_NOW = (
    r"\b(?:smoke|fire)\s+alarm\b.{0,30}\b(?:going\s+off|sounding|blaring|wailing)\b",
    r"\bsmoke\s+(?:in|coming\s+into|filling|pouring\s+into|everywhere)\b",
    r"\b(?:on|caught)\s+fire\b",
    r"\bfire\s+(?:has\s+)?(?:started|spread)\b",
    r"\b(?:can't|cannot)\s+get\s+out\b.{0,40}\b(?:smoke|fire|flames?)\b",
)

# Weight bearing is the test a fracture has to pass: "he cant put weight on it" is the hip, and
# that person stays where they are. A joint named on its own is the other side of the same test:
# someone who cannot put weight on an ankle or a knee is up and talking to the bot, so "stay where
# you are, don't try to stand" is advice for a spine and not for them - what they need is an X-ray
# today, which is the first-aid entry below. The hip, the floor, a fall from a height and an older
# person who has gone down are the cases where failing to take weight still means the ambulance.
WEIGHT_OFF_FEET = (
    r"\b(?:can'?t|cant|cannot|unable\s+to|won'?t|wont)\s+(?:put|bear|take|stand\s+on)\s+"
    r"(?:any\s+)?weight\b",
    # The same thing said the other two ways round: "i cant put my foot down", "i cant stand on
    # my ankle". Both are the person telling you the foot will not take them.
    r"\b(?:can'?t|cant|cannot|unable\s+to)\s+put\s+(?:my|his|her|their|your)\s+(?:foot|feet)\s+down\b",
    r"\b(?:can'?t|cant|cannot|unable\s+to)\s+stand\s+on\s+(?:my|his|her|their|the)\s+"
    r"(?:ankle|knee|foot|feet|leg|toe|toes|heel)\b",
)

WEIGHT_HIP = (
    r"\b(?:hip|hips|pelvis|pelvic|thigh|thighs|groin|femur)\b",
    # Still down, or a fall that was more than a step: the hip fracture answer.
    r"\b(?:on\s+the\s+(?:floor|ground)|lying|can'?t\s+get\s+up|cant\s+get\s+up|not\s+moving)\b",
    r"\b(?:fell|fallen|fall|falling|slipped|tripped|collapsed|landed)\b[^.?!]{0,30}"
    r"\b(?:ladder|roof|scaffold\w*|stairs|steps|wall|cliff|horse|bunk|loft|trampoline|balcony)\b",
    r"\b(?:ladder|roof|scaffold\w*|stairs|steps|cliff|horse|bunk|loft|balcony)\b[^.?!]{0,30}"
    r"\b(?:fell|fallen|slipped|landed)\b",
    # A limb at a funny angle is a fracture the ambulance wants, whatever joint it is - but it has
    # to be somebody's limb: "the arm of my glasses is bent" is a hinge, not a fracture.
    r"\b(?:my|his|her|their|your|our)\s+(?:\w+'s\s+)?"
    r"(?:arm|leg|wrist|ankle|shoulder|elbow|knee|foot)\b"
    r"[^.?!]{0,25}\b(?:bent|deformed|at\s+a\s+funny\s+angle|sticking\s+out|back\s+to\s+front)\b",
)

# A foot that has been like this for months is a GP or a physio question, not A&E tonight: the
# morning is the giveaway for the everyday ones ("i cant put my feet down in the morning").
WEIGHT_LONG = (
    r"\b(?:every|each)\s+(?:morning|day|night)\b", r"\bin\s+the\s+mornings?\b", r"\blately\b",
    r"\bfor\s+(?:the\s+)?(?:last\s+|past\s+|few\s+|several\s+|a\s+few\s+|a\s+couple\s+of\s+)?"
    r"(?:weeks|months|years)\b",
    r"\b(?:weeks|months|years)\s+(?:now|ago)\b", r"\bfor\s+ages\b",
    r"\b(?:long\s+time|while)\s+now\b",
)

# A fall from a height, or a hip that has changed shape. A fall from a chair or a bike is a graze,
# so the height has to be in the line, and a fall that ended fine is a story, not an emergency.
FALL_CORE = (
    r"\b(?:fell|fallen|falling|tumbled|came\s+off|come\s+off)\s+(?:off|from|down)\s+"
    r"(?:a\s+|the\s+|his\s+|her\s+|their\s+|my\s+)?(?:ladder|roof|scaffold\w*|stairs|steps|"
    r"wall|cliff|horse|top\s+bunk|loft|roof\s+rack)\b",
    r"\b(?:fell|fallen|tumbled)\s+down\s+(?:the\s+|a\s+)?(?:stairs|steps|flight\s+of\s+stairs)\b",
    # A trampoline, a bike and a swing are heights children come off every day: they only count
    # when something else in the line says this one went wrong.
    r"\b(?:fell|fallen|tumbled)\s+(?:off|from)\s+(?:a\s+|the\s+)?(?:trampoline|bike|swing|"
    r"slide|climbing\s+frame|bunk\s+bed)\b[^.?!]{0,40}"
    r"\b(?:head|neck|back|spine|unconscious|knocked\s+out|not\s+moving|isn'?t\s+moving|"
    r"won'?t\s+wake|wont\s+wake|can'?t\s+feel|vomit\w*)\b",
    r"\b(?:fell|fallen|tripped)\b[^.?!]{0,30}\b(?:broke|broken|fractured)\s+(?:my|his|her|their)\s+"
    r"(?:hip|pelvis|back|neck|skull|spine)\b",
    r"\b(?:hip|pelvis)\b[^.?!]{0,25}\b(?:looks?\s+(?:wrong|odd|out\s+of\s+place)|is\s+(?:out\s+of\s+place|"
    r"deformed|mangled)|won'?t\s+bear\s+weight)\b",
    # A fall with no way up: an older person on the floor is a possible hip fracture and a long
    # lie, so the ambulance comes first and nobody is moved. `i fell and cant get up` takes the
    # "stay where you are" form.
    r"\b(?:fell|fallen|fall|slipped|tripped|collapsed)\b[^.?!]{0,25}"
    r"\b(?:can'?t|cant|cannot|not\s+able\s+to|unable\s+to)\s+(?:get|getting|stand)\s*"
    r"(?:\w+\s+)?(?:up|back\s+up)\b",
    # Someone who went down and has not got up is on the floor now, whatever the hour.
    r"\b(?:fell|fallen|fall|slipped|collapsed|fainted)\b[^.?!]{0,40}"
    r"\b(?:still\s+(?:on\s+the\s+floor|lying|down)|(?:he|she|they)\s*(?:'s|s|\s+is|\s+are)\s+"
    r"(?:still\s+)?(?:on\s+the\s+floor|lying\s+(?:there|on)))\b",
    # Someone on the floor who cannot move is a spinal-injury guess nobody at home can make, and
    # main greeted "my mum is on the floor and she cant move" as small talk.
    r"\b(?:on\s+the\s+(?:floor|ground)|fell|fallen|slipped|collapsed)\b[^.?!]{0,35}"
    r"\b(?:can'?t|cant|cannot|not|won'?t|wont)\s+(?:move|moving)\b",
    r"\b(?:my|his|her|their|the)\s+" + PERSON + r"\b[^.?!]{0,20}\b(?:can'?t|cant|cannot)\s+"
    r"(?:move|feel\s+(?:his|her|their)\s+(?:legs?|arms?|body))\b",
    # Weight bearing is the test a fracture has to pass: "he cant put weight on it" is the hip.
    # A named joint is answered by the first aid instead, which is why the fall itself is a fall.
    WEIGHT_OFF_FEET[0],
    r"\b(?:can'?t|cant|cannot|unable\s+to|won'?t|wont)\s+(?:put|bear|take|stand\s+on)\s+"
    r"(?:any\s+)?weight\b",
    r"\b(?:fell|fallen|fall|slipped|collapsed|on\s+the\s+(?:floor|ground))\b[^.?!]{0,40}"
    r"\b(?:can'?t|cant|cannot|not\s+able\s+to|unable\s+to|struggl\w+\s+to)\s+(?:lift|pick|"
    r"get)\s+(?:her|him|them|my\s+(?:mum|mom|mother|dad|father|wife|husband|partner|nan|gran|"
    r"neighbou?r|friend|brother|sister))\b",
    r"\b(?:can'?t|cant|cannot)\s+lift\s+(?:her|him|them|my\s+\w+)\s+off\s+the\s+"
    r"(?:floor|ground)\b",
)

# Clothes are worn, so a garment shares the sentence with the body in it all the time: "my knee is
# bent the wrong way and my trouser leg is torn" names a fracture and a seam, and standing the line
# down because a trouser has a leg of its own threw the ambulance away. With the object phrase taken
# out, a limb that still belongs to the person, and is still at an angle, keeps the card.
OWN_LIMB_AT_AN_ANGLE = (
    r"\b(?:my|his|her|their|our|your|the)\s+(?:arm|arms|leg|legs|knee|knees|ankle|ankles|wrist|wrists|"
    r"elbow|elbows|shin|shins|thigh|thighs|hip|hips|shoulder|shoulders|jaw|foot|feet|hand|hands)\b"
    r"[^.?!]{0,25}\b(?:bent|deformed|at\s+a\s+funny\s+angle|sticking\s+out|back\s+to\s+front)\b",
)

# A fall last week is a story; the same line that says it is still going is the emergency.
FALL_PAST = (
    r"\b(?:last|this)\s+(?:year|month|week|night|winter|summer|spring|autumn|xmas|christmas)\b",
    r"\b(?:\d+|a|one|two|three|four|five|six)\s+(?:yrs?|years?|months?|weeks?)\s+ago\b",
    r"\b(?:years|months|weeks|ages)\s+ago\b", r"\bused\s+to\b", r"\byesterday\b",
    r"\ba\s+while\s+ago\b", r"\bwhen\s+i\s+was\s+(?:a\s+kid|young|little|a\s+child|small)\b",
    # The same story about someone else: "my grandad fell over when he was a kid".
    r"\bwhen\s+(?:he|she|they)\s+(?:was|were)\s+(?:a\s+)?(?:kid|child|boy|girl|young|little|"
    r"small|at\s+school|a\s+teenager)\b",
    r"\b(?:had|got)\s+it\s+checked\b", r"\bwas\s+in\s+hospital\s+(?:for|with|after)\b",
    r"\b(?:back)\s+then\b", r"\bwhen\s+he\s+was\s+(?:a\s+)?(?:baby|small|little)\b",
)

FALL_NOW = (
    r"\bright\s+now\b", r"\bthis\s+(?:morning|afternoon|evening)\b", r"\bjust\b",
    r"\btoday\b", r"\bminutes?\s+ago\b", r"\ban\s+hour\s+ago\b",
    # The state the person is in beats the time word: someone still on the floor is a long lie
    # however long ago they went down.
    r"\bcan'?t\s+(?:get|stand|sit|feel|move)\b", r"\bunable\s+to\s+(?:get|stand|move)\b",
    r"\bnot\s+able\s+to\s+(?:get|stand|move)\b", r"\ban\s+ambulance\b",
    r"\bnot\s+breathing\b", r"\bunconscious\b", r"\bbleeding\b", r"\bhead\s+injur\w*\b",
    r"\bstill\s+(?:on\s+the\s+floor|lying|down)\b",
)

# "my dad fell off a ladder but hes ok", "she got up and walked it off": the line says how it ended.
FALL_FINE = (
    r"\b(?:but|and)\s+(?:he|she|they|it)\s*(?:'s|s|\s+is|\s+was)?\s*(?:ok|okay|fine|alright|"
    r"all\s+right)\b",
    # A comma is as common as a conjunction: "my dad fell off the roof, hes fine now".
    r"[,;]\s*(?:but\s+)?(?:hes|shes|theyre|it\s+is|he\s+is|she\s+is|they\s+are|"
    r"he'?s|she'?s|they'?re)\s+(?:now\s+)?(?:ok|okay|fine|alright|all\s+right)\b",
    r"\b(?:says?|said|tells?|told)\s+(?:me\s+)?(?:he|she|they)\s*(?:'s|s|\s+was|\s+is)?\s*"
    r"(?:ok|okay|fine|alright)\b",
    r"\b(?:got\s+up|walked\s+it\s+off|laughed\s+it\s+off|laughed|ran\s+off|is\s+walking|"
    r"shes\s+walking|hes\s+walking|nothing\s+broken|no\s+harm|was\s+fine)\b",
    r"\b(?:i'?m|im)\s+(?:ok|okay|fine|alright)\b",
    r"\bstill\s+(?:fine|ok|okay|walking)\b",
    # A thing falling off a wall is a DIY job, not somebody going down: `my picture keeps falling
    # off the wall` and `the plaster is falling off the wall` were both getting the ambulance.
    # It is only DIY while nothing lands on a person.
    r"\b(?:picture|mirror|shelf|shelves|plaster|paint|tiles?|clock|poster|frame|curtains?|blind|"
    r"radiator|handle|door|window|bricks?|render|gutter(?:ing)?|shingles?|hook|rail|coving|"
    r"wallpaper|wreath|chimney|cable|lights?|fixture|fitting)\b[^.?!]{0,30}"
    r"\b(?:fell|falls?|falling|came\s+off|come\s+off|coming\s+off|keeps?\s+falling)\b"
    r"(?!\s+(?:on|onto|over)\s+(?:me|my\s+\w+|him|her|them|his\s+\w+|her\s+\w+|their\s+\w+))",
    r"\bit\s+(?:keeps?\s+falling|fell|falls|is\s+falling|came)\s+off\s+(?:the|a)\s+"
    r"(?:wall|shelf|hook|ceiling|door|window|board)\b",
    # "keeps falling off" is the DIY complaint whatever the object is called.
    r"\b(?:keeps?|is\s+always)\s+falling\s+off\s+(?:the|a|my|our)\s+(?:wall|shelf|ceiling|hook|door|"
    r"window|board|brackets?)\b",
)

# A fall that keeps happening is a pattern, not an accident: "i keep falling down the stairs"
# and "my dad keeps falling down the stairs" were getting "stay where you are and ring 999"
# from the stairs arm, which is advice for somebody who has just gone down. The pattern has an
# answer of its own (strength, sight, medicines, a falls review), and that is the answers lane's.
# Anyone down now, hurt or unable to get up keeps the card through FALL_NOW and FALL_RED.
FALL_REPEAT = (
    # "i keep falling", "he keeps tripping", "she kept going over on it". The idioms that only
    # borrow the verb are stood down here, so "keeps falling asleep" is not a fall.
    r"\b(?:keep|keeps|kept)\s+(?:on\s+)?(?:falling|tripping|slipping|going\s+over|having\s+falls?)\b"
    r"(?!\s+(?:asleep|out|for|behind|apart|short|through|into|in\s+love))",
    r"\b(?:falls?|falling|trips?|tripping)\b[^.?!]{0,25}"
    r"\b(?:all\s+the\s+time|every\s+day|each\s+day|a\s+lot|constantly|regularly|often)\b",
    r"\b(?:is|am|are)\s+always\s+(?:falling|tripping|slipping)\b",
    # "my nan has been falling" is the same pattern as "my nan keeps falling", and "ive had a few
    # falls" is the same said as a count.
    r"\b(?:has|have|had)\s+been\s+(?:falling|tripping|slipping|going\s+over)\b"
    r"(?!\s+(?:asleep|out|for|behind|apart|short|through|into|in\s+love))",
    r"\b(?:had|have|has)\s+(?:a\s+)?(?:few|couple\s+of|several|two|three|more)\s+falls?\b",
)

FALL_CHECK_OFF = (
    # "i nearly fell over laughing" is a near-miss about a joke, not a fall that happened.
    r"\b(?:nearly|almost|could\s+have|might\s+have|would\s+have)\b[^.?!]{0,15}\b(?:fell|fallen|"
    r"fall|slipped|tripped)\b", r"\blaugh\w*\b",
    # bare "out" fenced off "we fell out", and it also fenced off every fall on the way out of
    # something: "i fell out of bed" got nothing at all. Only "fell out" with no "of" is the
    # argument, so the phrase keeps the fence and the bed, bath, tree and car get the card.
    r"\b(?:fell|fallen|fall|falling)\s+(?:asleep|for|in\s+love|behind|apart|short|through|into)\b",
    r"\b(?:fell|fallen|fall|falling)\s+out\b(?!\s+of\b)",
    # "i fell off the wagon with my diet" is a slip of the diet, not a fall to check for bruising,
    # and "he fell off the wagon" is the same said about somebody else.
    r"\b(?:fell|fallen|fall|falling)\s+off\s+the\s+wag[go]n\b",
    r"\b(?:hair|wig|snow|rain|leaves|price|prices|temperature|pound|stock|market)\b",
    r"\b(?:dont|don'?t|didnt|didn'?t|never|not)\b[^.?!]{0,10}\b(?:fell|fallen)\b",
) + FALL_WORD_IDIOM + (
    # A phrasal "slipped" is not a fall. Work slips, a schedule slips behind, a note is slipped to
    # someone, a chance slips by, and somebody slips out for lunch - all of them spelled exactly
    # like a foot going over. The bath, the ice and the stairs keep the card: "slipped in the bath"
    # and "slipped out of the bath" are both falls, so "out" is only fenced when no "of" follows.
    r"\b(?:slip|slips|slipped|slipping)\s+(?:up|behind|past|by|through|away|me|him|her|them|us)\b",
    r"\b(?:slip|slips|slipped|slipping)\s+out\b(?!\s*of\b)",
    # What slipped, when it is not a body: a grade, a market, a deadline, a quarter's figures.
    r"\b(?:slip|slips|slipped|slipping|trip|trips|tripped)\b[^.?!]{0,25}"
    r"\b(?:work|works|schedule|deadlines?|grades?|marks?|standards?|quality|sales|figures?|"
    r"prices?|markets?|memor(?:y|ies)|attention|a\s+note)\b",
    r"\b(?:work|schedule|deadlines?|grades?|standards?|quality|sales|figures?|prices?|markets?|"
    r"the\s+quarter)\b[^.?!]{0,25}\b(?:has|have|had|keeps|keep|is|was)\b[^.?!]{0,10}"
    r"\b(?:slip|slips|slipped|slipping)\b",
)

# A fall that has already been answered. The card below asks two questions - can they get up, did
# they hit their head - and someone who says the person is not breathing, not responding or
# unresponsive has answered them. `she fell and isnt breathing` was being asked whether it was just
# bruising, because a fall in the line outranks the breathing cards; `my mum fell and is
# unresponsive` the same. The word has to be about the body: "hes unresponsive at work lately" and
# "my boss is unresponsive to emails" are someone's manner, not a person on the floor.
FALL_ANSWERED = (
    r"\b(?:not|isn'?t|isnt|aren'?t|arent|stopped|stop|stopt)\s+breathing\b",
    r"\b(?:not|isn'?t|isnt|aren'?t|arent)\s+responding\b",
    r"\bcan'?t\s+breathe\b", r"\bcant\s+breathe\b",
    r"\bno\s+pulse\b", r"\bwithout\s+a\s+pulse\b", r"\bno\s+heartbeat\b",
    r"\bunresponsive\b(?!\s*(?:to|at|when|whenever|if|because|as|after|with|about)\b)",
    r"\bnot\s+waking\b", r"\bstill\s+not\s+waking\b",
)

# What makes a "fine" line not fine after all.
FALL_RED = (
    # Something that came off a wall and landed on somebody is that person's injury, not a DIY
    # job: `the mirror fell off the wall and hit my dad on the head` was getting fixings advice.
    r"\b(?:hit|hits|struck|landed\s+on|came\s+down\s+on|fell\s+on)\b[^.?!]{0,15}"
    r"\b(?:me|my\s+\w+|him|her|them|his\s+\w+|her\s+\w+|their\s+\w+)\b",
    r"\b(?:unconscious|knocked\s+out|not\s+moving|isn'?t\s+moving|won'?t\s+wake|wont\s+wake|"
    r"can'?t\s+feel|cant\s+feel|numb|vomit\w*|bleed\w*|hospital|ambulance|a\s+and\s+e|a&e|"
    r"broken|broke|fractured|stiff\s+neck)\b",
    r"\b(?:head|neck|back|spine)\b[^.?!]{0,20}\b(?:hit|bang\w*|hurt|pounding|bleeding)\b",
)

# The glass test is the thing a parent can do, so the words people use to describe it are the cue.
RASH_FADE = (
    r"\b(?:doesn'?t|does\s+not|don'?t|dont|won'?t|wont|isn'?t|is\s+not|not|never)\s+"
    r"(?:fade|fades|fading|blanch|blanches|go\s+away|goes\s+away|disappear|disappears|"
    r"turn\s+white|come\s+off|rub\s+off)\b",
    r"\b(?:doesn'?t|does\s+not|won'?t|wont)\s+(?:blanch|fade)\b",
    r"\bnon[\s-]?blanch\w*",
    r"\b(?:still|stays?|remains?|same)\b[^.?!]{0,20}\b(?:press\w*|glass|push\w*)\b",
    r"\b(?:press\w*|glass|push\w*)\b[^.?!]{0,25}\b(?:still|stays?|remains?|same|doesn'?t|"
    r"does\s+not|won'?t|wont)\b",
    r"\bunder\s+a\s+glass\b",
    r"\b(?:go|goes|going|went|come|comes|coming|came)\s+(?:back|straight\s+back)\b",
)

# The press test said out loud, as opposed to a mark that fades on its own. "the rash on my arm
# doesnt fade" is the doctor-today question the row above keeps for a mark, but a hand and a glass
# on it is the sign: "he has a rash that doesnt fade when i press it", "the rash doesnt turn white
# when i press it" and "i have a rash that doesnt blanch" were all reaching an everyday answer.
RASH_PRESSED = (
    r"\bnon[\s-]?blanch\w*",
    r"\b(?:doesn'?t|does\s+not|don'?t|dont|won'?t|wont|isn'?t|is\s+not|not)\s+blanch\w*",
    r"\b(?:doesn'?t|does\s+not|don'?t|dont|won'?t|wont|isn'?t|is\s+not|not)\s+"
    r"(?:fade|fades|fading|turn\s+white)\b[^.?!]{0,25}\b(?:press\w*|glass|push\w*)\b",
    r"\b(?:press\w*|glass|push\w*)\b[^.?!]{0,25}\b(?:doesn'?t|does\s+not|don'?t|dont|"
    r"won'?t|isn'?t|not)\s+(?:fade|blanch|turn\s+white)\b",
    r"\bunder\s+a\s+glass\b",
    r"\bsame\b[^.?!]{0,15}\bglass\b",
)

# The exercise that makes a blackout a heart question rather than a hot room. A match, a session, a
# run and a swim are all effort; a hot bath and a blood test are not, and they are fenced below.
BLACKOUT_EFFORT = (
    r"\b(?:gym|workout|work\s?out|exercis\w*|training|treadmill|weights|crossfit|hiit|"
    r"spin(?:ning)?|rowing|rowing\s+machine|cross\s+trainer|running|runs|jog\w*|sprint\w*|"
    r"football|rugby|soccer|netball|hockey|tennis|badminton|squash|basketball|swim\w*|"
    r"cycling|cycled|cycle|bike|triathlon|marathon|park\s?run|match|sports?\s+day|"
    r"pe\s+lesson|games\s+lesson|climbing|hillwalk\w*|hiking)\b",
)

# Coming round on the floor, or finding somebody there, is the blackout that was a collapse.
BLACKOUT_FLOOR = (
    r"\b(?:woke\s+up\s+on\s+the\s+(?:floor|ground|pavement|street)|"
    r"woke\s+on\s+the\s+(?:floor|ground)|came\s+round\s+on\s+the\s+(?:floor|ground)|"
    r"came\s+to\s+on\s+the\s+(?:floor|ground)|found\s+(?:him|her|them|my\s+\w+)\s+on\s+the\s+"
    r"(?:floor|ground)|on\s+the\s+floor\s+when\s+i\s+(?:woke|came\s+round|came\s+to))\b",
)

# A blackout that keeps happening is the same-day question however ordinary each one looked: two in a
# year is a GP's puzzle, and the arm below is written for it. And somebody else going down, whatever
# the cause, is a person on the floor to be checked now rather than a story to be told.
BLACKOUT_REPEAT = (
    r"\b(?:keep(?:s|ing)?\s+(?:on\s+)?(?:passing|blacking|faint\w*)|"
    r"(?:passed|blacked|faint\w*)\s+out\b[^.?!]{0,20}\bagain\b|"
    r"\b(?:twice|three\s+times|four\s+times|several\s+times|a\s+few\s+times|"
    r"\bover\s+and\s+over)\b[^.?!]{0,25}\b(?:passed\s+out|blacked\s+out|fainted)\b|"
    r"\b(?:passed\s+out|blacked\s+out|fainted)\b[^.?!]{0,25}\b(?:twice|again|"
    r"three\s+times|several\s+times|a\s+few\s+times)\b)",
)

# A breath held too long is the blackout that the effort arm misses: "i held my breath too long
# and blacked out" was the greeting module's "Good to hear. What was the best bit?", because
# nothing in the blackout case read the breath. A hypoxic blackout is the same-day-at-least
# question every other blackout is, and in water it is a 999.
BLACKOUT_BREATH = (
    r"\b(?:held|hold|holding)\b[^.?!]{0,20}\bbreath\b[^.?!]{0,40}"
    r"\b(?:too\s+long|until|till|and\s+(?:blacked|passed|fainted|went\s+under))\b",
)

BLACKOUT_SOMEONE_DOWN = (
    r"\bmy\s+(?:wife|husband|partner|mum|mom|mother|dad|father|son|daughter|child|kid|baby|"
    r"friend|mate|brother|sister|nan|gran|grandma|grandad|grandpa|neighbour|neighbor|flatmate|"
    r"colleague|boss|boyfriend|girlfriend)\b[^.?!]{0,30}\b(?:pass(?:ed)?\s+out|"
    r"black(?:ed)?\s+out|faint(?:ed)?|collapsed|went\s+limp|out\s+cold)\b",
)

# A screen, a phone, a set of lights and a set of curtains black out too, and none of them is a
# person on the floor: "my phone keeps blacking out" was the blackout card until this fence.
BLACKOUT_A_THING = (
    r"\b(?:screens?|phones?|telly|tv|television|monitor|display|laptop|computer|system|server|"
    r"lights?|streetlights?|power|electricity|wifi|wi-?fi|signal|cameras?|windows?|curtains?|"
    r"blinds?|bulbs?|fuses?|projector|kindle)\b[^.?!]{0,30}\b(?:black(?:ed|ing)?\s+out|"
    r"keep(?:s|ing)?\s+blacking\s+out)\b",
    r"\bblack(?:ed|ing)?\s+out\b[^.?!]{0,20}\b(?:screens?|phones?|telly|tv|lights?|windows?|"
    r"curtains?|power|signal|monitor|camera)\b",
    r"\bkeep(?:s|ing)?\s+blacking\s+out\b[^.?!]{0,20}\b(?:screen|phone|telly|tv|monitor|"
    r"lights?|signal)\b",
)

# The faint with a cause in the line is the composer's faint card and it is a good one: a hot room, a
# hot bath, a needle, giving blood, a skipped meal, standing up too fast, drink, and a faint that is
# over with nothing else wrong. A story about years ago is a GP line, not this one.
BLACKOUT_OFF = (
    r"\b(?:hot\s+(?:room|day|bath|shower|weather)|heat|heatwave|blood\s+test|bloods|"
    r"giving\s+blood|gave\s+blood|donated\s+blood|blood\s+donor|needle|injection|jab|"
    r"vaccine|hungry|not\s+eaten|skipped\s+(?:breakfast|lunch|dinner|a\s+meal)|standing\s+up|"
    r"stood\s+up|got\s+up\s+too\s+fast|period|drunk|drinking|alcohol|hungover|hangover|"
    r"laughing|laughed|laughs|joke|film|movie|programme|episode|book)\b",
    r"\b(?:years?|months?)\s+ago\b",
)

STIFF_NECK = (
    r"\bstiff\s+neck\b", r"\bneck\s+(?:is|feels|has\s+gone|went)\s+(?:very\s+|so\s+|really\s+)?stiff\b",
    r"\bneck\s+stiffness\b", r"\bcan'?t\s+bend\s+(?:my|his|her|their|the)\s+(?:neck|chin)\b",
    r"\bchin\s+(?:is\s+)?(?:stuck|touching|on|to)\s+(?:my|his|her|their)\s+chest\b",
)

MENINGITIS_OTHER = (
    r"\bheadache\w*", r"\bhead\s+(?:is\s+)?(?:killing|banging|thumping|pounding|hurting|sore)\b",
    r"\bhead\s+hurts\b", r"\bmy\s+head\b",
    r"\blight\b", r"\bsunlight\b", r"\bbright\b", r"\brash\w*", r"\bspots?\b",
    r"\bconfus\w*", r"\bdrows\w*", r"\bvomit\w*", r"\bbeing\s+sick\b", r"\bthrowing\s+up\b",
    r"\bseizure\b", r"\bfloppy\b", r"\bunrespons\w*",
)

STIFF_FINE = (
    r"\bfrom\s+(?:sleeping|sleep|the\s+gym|work|the\s+computer|lifting|stress|the\s+pillow|"
    r"the\s+cold|a\s+cold|driving|the\s+desk|studying|gardening)\b",
    r"\bslept\s+(?:funny|awkward|badly|on\s+it)\b", r"\b(?:crick|kink)\s+in\s+(?:it|my\s+neck)\b",
    r"\bneck\s+(?:ache|pain)\s+(?:from|after)\b",
)

# Sepsis is a fever that has gone wrong: the person is confused, drowsy, breathing fast or
# "not themselves", and that combination is the ambulance however well they look.
SEPSIS_SIGN = (
    r"\bconfus(?:ed|ion)\b", r"\bnot\s+making\s+sense\b", r"\bdrows\w*",
    r"\bvery\s+sleepy\b", r"\btoo\s+sleepy\b",
    r"\bhard\s+to\s+wake\b", r"\bwon'?t\s+wake\b", r"\bwont\s+wake\b", r"\bfloppy\b",
    r"\blimp\b", r"\bunrespons\w*", r"\bnot\s+themselves\b", r"\bnot\s+(?:him|her)self\b",
    r"\bbreathing\s+(?:fast|quickly|funny|strangely)\b", r"\bgrunting\b",
    r"\bblue\s+(?:lips?|round\s+the\s+lips?)\b", r"\bmottled\b", r"\blifeless\b",
    r"\bshivering\b", r"\bclammy\b", r"\bvery\s+cold\b",
)

# A temperature in a baby under three months is the hospital, whatever it says on the thermometer.
NEWBORN = (
    r"\bnewborn\b", r"\bnew\s?born\b", r"\b\d+\s*(?:days?|weeks?)\s+old\b",
    # Six months is not the hospital call: a baby under six months with a temperature is the
    # same-day child card, and only under three months is seen straight away whatever the reading.
    r"\b(?:under|less\s+than|not\s+yet)\s+(?:3|three)\s+months?\b",
    r"\b(?:under|less\s+than|not\s+yet)\s+(?:2|two)\s+months?\b",
    r"\b(?:3|6)\s+weeks?\s+old\b",
    # "he is 2 months", "a 10 week old", "six weeks": the age is said next to the temperature far
    # more often than the word newborn is.
    r"\b(?:is|only|just|nearly)\s+(?:1|2|one|two)\s+months?\b",
    # "my baby is 6 weeks and has a temperature" said the age a week at a time, where every
    # spelling with the number next to "old" ("my 6 week old", "my baby is six weeks old") was
    # read. A baby at six weeks got the small-child 111 card while the same baby at "6 week old"
    # got the newborn 999 card, which is the one thing this card exists to get right. A pregnancy
    # is a count of weeks about someone else, so it is left out here and stays with its own case.
    r"\b(?:baby|newborn|infant|son|daughter|boy|girl|little\s+one)\b[^.?!]{0,12}"
    r"(?:is|only|just|nearly)\s+(?:[1-9]|1[0-2]|one|two|three|four|five|six|seven|eight|nine|"
    r"ten|eleven|twelve)\s+weeks?\b(?![-\s]*(?:pregnan\w*|along|into|of))",
    r"\b(?:1|2|one|two)[-\s]*months?[-\s]*old\b",
    r"\b(?:4|5|6|7|8|nine|nine|eight|seven|six|five|four)\s+weeks?\s+old\b",
)

# A boiler is "six weeks old" as well, and "my boiler is 6 weeks old and has a temperature" was the
# newborn card: the age words are a newborn's anchor, and the appliance sits too far from the
# temperature for DEVICE_TEMP's window to see it. A thing is only ever weeks old in this shape -
# "<appliance> is 6 weeks old" - so the appliance has to be the subject of the age.
DEVICE_OLD = (
    r"\b(?:oven|boiler|room|water|thermostat|fridge|freezer|shower|bath|heating|radiator|"
    r"washing\s+machine|tumble\s+dryer|air|weather|engine|car|kettle|dishwasher|mattress|sofa|"
    r"roof|carpet|house|flat|washing\s+machine|dryer|heater|fan|pump|motor)\b"
    r"[^.?!]{0,10}\b(?:is|was|are|were|only|just|nearly|now)\b[^.?!]{0,10}"
    r"\b\d+\s*(?:days?|weeks?)\s+old\b",
)

CONFUSED_THING = (
    r"\bconfus(?:ed|ion)\s+(?:about|by|with|over|on)\s+(?:(?:my|the|his|her|their|a|this|that)\s+)?"
    r"(?:\w+\s+){0,3}(?:homework|question|instructions?|settings?|app|recipe|exam|form|bill|tickets?|map|"
    r"directions|order|complaint|book|film|movie|email|message|answer|word|plan|tablets?|pills?|"
    r"meds|medication|insulin|doses?|dose|reading|reading[s]?|numbers?|labels?|charges?|"
    r"where|which|who|when|how)s?\b",
)

# The age and the fever do not have to arrive in the same line. "my baby is 3 weeks old" and then
# "she has a temperature of 38" was read as an adult's fever and answered with paracetamol and
# ibuprofen, which is the one answer that must never reach a baby that small. The age is taken from
# what the person has just typed, so the arm below needs no age words of its own.
TINY_AGE = (
    r"\bnew\s?born\b", r"\bjust\s+born\b", r"\bonly\s+just\s+born\b",
    r"\b(?:1|2|3|4|5|6|7|8|9|10|11|12|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve)\s*(?:days?|weeks?)\s+old\b",
    # Six months is not the hospital call: a baby under six months with a temperature is the
    # same-day child card, and only under three months is seen straight away whatever the reading.
    r"\b(?:under|less\s+than|not\s+yet)\s+(?:3|three)\s+months?\b",
    r"\b(?:under|less\s+than|not\s+yet)\s+(?:2|two)\s+months?\b",
    # "my daughter is 4 weeks old", said without the "old" on the end.
    r"\b(?:baby|babies|newborn|infant|son|daughter|boy|girl|little\s+one)\s+(?:is|was|now|only)\s+"
    r"(?:1|2|3|4|5|6|7|8|9|10|11|12|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    r"\s*(?:days?|weeks?)\b",
)

# An age that is old enough settles it, and a later one wins over an earlier one: a baby who was
# three weeks old last month is four months old and this is not the hospital call any more.
# An older child named with his years in the same line settles it the other way: "my son is 5 and he
# has a temperature" is the five-year-old's card, not the three-week-old's. It sits next to
# TINY_AGE_FINE and not inside _tiny_baby, so "my son is 5" in the window cannot stand the baby's
# own next line down.
OLDER_CHILD_NAMED = (
    r"\b(?:my|our)\s+(?:son|daughter|boy|girl|child|toddler|kid)\b[^.!?]{0,12}"
    r"\b(?:is|was|aged)\s+(?:\d|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen)\b",
    r"\b(?:my|our)\s+(?:son|daughter|boy|girl|child|toddler|kid)\b[^.!?]{0,12}"
    r"\b(?:aged|age)\s+(?:\d|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b",
)

TINY_AGE_FINE = (
    r"\b(?:1[3-9]|[2-9]\d)\s*weeks?\s+old\b", r"\b\d+\s+months?\s+old\b",
    r"\b\d+\s+years?\s+old\b", r"\bover\s+(?:3|three|6|six)\s+months\b",
    # "shes 14 weeks now" leaves the "old" off, and it is the line that says this baby has
    # grown out of the hospital call.
    r"\b(?:1[3-9]|[2-9]\d|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)"
    r"\s*weeks?\b",
)

# The line that carries only the fever, about the baby and not about the speaker: "she has a
# temperature of 38", "he feels hot", "the baby is boiling". "i have a temperature" is an adult's
# line and stays where it was.
# Who has the temperature, not who is talking: a worried parent says "me" and "i" in the same
# line as the fever almost every time ("she has a temperature and it worries me"), and a guard on
# the bare "i" answered those as the adult's paracetamol. The speaker's own fever is the only
# thing that takes the line away from the baby.
ABOUT_THE_SPEAKER = (
    r"\bmy\s+(?:own\s+)?(?:temp|temps|temperature|fever)\b",
    r"\bi\s+(?:have|had|got|ve\s+got|am\s+running|feel|felt)\b.{0,24}"
    r"\b(?:temp|temps|temperature|fever|feverish|hot|boiling)\b",
    r"\bi\s*(?:'m|m)\s+(?:running\s+a\s+)?(?:a\s+)?(?:temp|temperature|fever|feverish|hot|boiling)\b",
    r"\bi\s+feel\s+(?:hot|feverish|boiling)\b",
    # "i have a temperature of 38 and the baby is fine" is still the speaker's own, and so is the
    # fever said with "mine".
    r"\bmine\s+(?:is|was)\b",
)

PALE_SECOND = (
    r"\bclammy\b", r"\bsweaty\b", r"\bshivery\b", r"\bshaking\b", r"\bsleepy\b",
    r"\bdrows\w*", r"\bfloppy\b", r"\blimp\b", r"\bconfus\w*", r"\bdizzy\b",
    r"\bvomit\w*", r"\bbeing\s+sick\b",
    # "not feeding" is not here: a baby who stops feeding has its own same-day answer in the
    # family knowledge base, and it names the age line and the A&E signs too. This card took the
    # turn from it (azure-trout's read).
    r"\bnot\s+(?:him|her|them)self\b",
    # "sweating" rather than only "sweaty": `my partner is white as a sheet and sweating` was the
    # night-sweats entry, and the tense of one word is not a different sign.
    r"\bsweat\w*\b",
    # Blue is a sign as well as a colour, so it can be the second thing: "my son is mottled and
    # blue" had two colours in it and neither of them was the sign the row wanted.
    r"\bblue\b",
    r"\bvery\s+cold\b", r"\bcold\s+and\b", r"\bcold\s+hands\b",
    r"\band\s+(?:very\s+)?cold\b",
)

# The heat is the same answer and the same cooling advice, and it is the one line that must never
# say "keep them warm": `my daughter is pale and sweaty from the heat` got exactly that on main
# (@steward-spare-finch). A long journey, a stuffy car or a hot room raises the same sweat.
PALE_HEAT = (
    r"\b(?:from|in|out\s+in)\s+the\s+(?:heat|sun|sunshine)\b",
    r"\b(?:hot\s+day|heat\s?wave|sunbathing|sunburn\w*|greenhouse|conservatory)\b",
    r"\b(?:after|during|from|in|on)\s+(?:the\s+|a\s+|his\s+|her\s+)?(?:journey|car|train|"
    r"bus|coach|flight|plane|tube|heating|radiator|stuffy\s+room|hot\s+room|sunbed)\b",
)

# Pale and sweaty straight after football is a child who has been running about - the colour is
# the effort, not the circulation. A hot day is deliberately not in this list: pale and clammy
# in the sun is heat exhaustion. "my daughter is pale and sweaty after football"
# was a child going downhill. The red signs below still win: a child who is floppy, wont wake,
# going blue or grey is the card whatever they were doing.
# Real exertion: a match, training, a run, the gym, swimming, a bike ride, PE. Sweaty and clammy
# straight after one of these is sweat, and the cooling answer is the right one. The shape is
# generic rather than a longer list of nouns, so "after cross country", "after a 3k race", "after
# the school run" and "after a swimming lesson" are all in it (@magenta-pine's read).
PALE_EXERTION = (
    r"\b(?:after|during|at|from|in)\s+(?:(?:a\s+|the\s+)?(?:\w+\s+){0,2}"
    r"(?:race|run|match|game|session|training|lesson|class|practice|workout|circuit|"
    r"walk|hike|ride)|"
    r"cross\s?country|school\s+run|football|rugby|netball|hockey|the\s+gym|sports?\s+day|"
    r"swimming|a\s+swim|cycling|a\s+bike\s+ride|pe)\b",
    # A named sport after the cue is the same thing - "after gymnastics", "after tennis" - and so
    # is "after his lesson".
    r"\b(?:after|during|at|from|in)\s+(?:his|her|my|their|our|the|a|an)?\s*"
    r"(?:tennis|badminton|squash|cricket|athletics|gymnastics|dance|dancing|ballet|judo|karate|"
    r"martial\s+arts|taekwondo|boxing|climbing|rowing|trampolining|skating|skateboarding|"
    r"snowboarding|skiing|riding|horse\s+riding|sports?|games?|practice|training|workout|walk|"
    r"walking|hike|hiking|ramble)\b",
)

PALE_EFFORT_RED = (
    r"\bfloppy\b", r"\blimp\b", r"\b(?:wont|won't|not|can't|cant|unable\s+to)\s+wake\b",
    r"\bunresponsive\b", r"\bunconscious\b", r"\bcollapsed\b", r"\bblue\b",
    r"\bgrey\b", r"\bgray\b", r"\bmottled\b", r"\bbreathing\s+(?:fast|quickly|hard)\b",
    r"\bgrunting\b", r"\bnot\s+breathing\b",
)

NAMED_SICK_FINE = (
    r"\bin\s+(?:hospital|icu|intensive\s+care|a\s+bed)\b", r"\bbeing\s+treated\b",
    r"\b(?:on|took|having)\s+antibiotics\b", r"\bantibiotics\b", r"\bhad\s+(?:it|this|"
    r"meningitis|sepsis|pneumonia)\b", r"\byears?\s+ago\b", r"\bwhen\s+(?:he|she|they)\s+"
    r"(?:was|were)\s+(?:little|a\s+baby|young|small|\d+)\b", r"\brecovered\b",
    r"\bgetting\s+better\b", r"\bnow\s+fine\b", r"\bback\s+in\s+\d{4}\b",
    r"\bis\s+(?:over|recovering)\b", r"\bcame\s+through\b", r"\bthankfully\b",
    # The illness can also be a line in the notes, a history, or a thing already fought off.
    r"\bin\s+(?:his|her|their|the)\s+(?:notes|file|records|chart|history)\b",
    r"\bhistory\s+of\b", r"\bwas\s+(?:treated|admitted|diagnosed)\b",
    r"\btreated\s+for\b", r"\bgot\s+over\b", r"\bfought\s+(?:it|that|this)\s+off\b",
    r"\bsurvived\b", r"\bdischarged\b", r"\bno\s+longer\b", r"\bused\s+to\b",
    r"\b(?:was|were|been)\s+ruled\s+out\b", r"\bruled\s+out\b", r"\bchecked\s+for\b",
)

# A question about a fever is not a child with one: "how do i bring a fever down in a toddler" and
# "what temperature should a baby's room be" are asking for the everyday advice the answers lane
# has, so the card only keeps the lines that say the fever is happening ("has a temperature of 38",
# "is running a temp", "feels hot").
FEVER_ASK = (r"^\s*(?:\w+\s+){0,2}(?:how|what|whats|what'?s|when|why|which|where|should|can|"
             r"could|do|does|will|would|shall)\b",
             # "is my son feverish" is a question and "my son is boiling hot" is not, so the
             # copula only counts as the first word of the line ("is", "are", "was") and never
             # three words in where a declarative puts it.
             r"^\s*(?:is|are|was|were|am|do|does)\s+(?:my|his|her|our|their|the|this|that|a|an)\b",)

FEVER_REPORT = (
    r"\b(?:has|have|had|got|is\s+running|is\s+reading|reading|reads|feels|felt|says|said|hit|"
    r"spiked|went\s+up\s+to|running)\b[^.?!]{0,16}\b(?:temperature|temps?|fever|feverish|hot)\b",
    r"\b(?:temperature|temp)\s+(?:is|was|reading|at|hit|spiked)\s*(?:\d|high|up|through\s+the\s+"
    r"roof)",
)

# The card is written for a small child, and a twelve-year-old with a temperature is not one.
# A five- to nine-year-old with a temperature and nothing else wrong is the everyday fever the
# answers lane already has ("light clothes and plenty to drink matter more than the number"). Only
# a small child's reading is the 111 card, so the school-age child stands the card down unless the
# line also names the thing that makes it urgent: floppy, drowsy, hard to wake, breathing hard, a
# rash, a fit, a stiff neck, blue lips, a very high number, or a baby too young to say.
CHILD_SCHOOL_AGE = (
    r"\b(?:5|6|7|8|9|five|six|seven|eight|nine)\s*(?:year|yr)s?[-\s]*old\b",
    # The "months" has to be read: "my son is 5 months old and has a temperature" matched the bare
    # "5" and lost the 111 card a baby that age must keep (steward-free-daisy, #7868).
    r"\b(?:my|his|her|their|our|the)\s+(?:son|daughter|boy|girl|child|kid|little\s+one)s?\s+"
    r"(?:is|was|aged|of)\s+(?:5|6|7|8|9|five|six|seven|eight|nine)\b"
    r"(?!\s*(?:month|week|day|yr\s*\d|mo\b))",
    r"\b(?:aged|age)\s+(?:5|6|7|8|9|five|six|seven|eight|nine)\b",
    # "in year 2" is not here on purpose: the answers lane reads a bare "year" as a school year and
    # answered "my son in year 2 has a fever" with "a relative going quiet is usually nothing more
    # than a busy year". A line this gate cannot read safely keeps the 111 card it had on main.
)

# "My child is drinking and playing" is the good sign, and the same words negated are the bad one:
# "my 6 year old has a fever and is not drinking" was read as a child who is drinking, stood the
# card down, and the alcohol-refusal row answered it ("have the line ready before the glass
# arrives"). A refusal of fluids is a red flag, so the good-sign gate has to see the "not".
CHILD_FEVER_NOT_EATING = (
    r"\b(?:not|isnt|isn'?t|wasnt|wasn'?t|wont|won'?t|hasnt|hasn'?t|havent|haven'?t|never)"
    r"\s+(?:been\s+)?(?:eating|drinking|taking\s+(?:fluids?|drinks?|bottles?)|"
    r"had\s+(?:a\s+)?(?:drink|anything|fluids?))\b",
    r"\b(?:refus\w*|off\s+(?:his|her|their)\s+(?:food|drink|bottle|feeds?))\b",
    r"\bno\s+(?:appetite|interest\s+in\s+(?:food|drink))\b",
    r"\b(?:dehydrated|dried\s+out)\b",
)

CHILD_FEVER_RED = (
    r"\b(?:floppy|floppy\s+as\s+a\s+rag|drowsy|drowsier|unresponsive|unconscious|"
    r"wont\s+wake|won'?t\s+wake|hard\s+to\s+wake|limp|listless|not\s+(?:himself|herself|"
    r"themselves)|breathing\s+(?:fast|hard|quickly|badly)|struggling\s+to\s+breathe|"
    r"grunting|groaning|blue\s+lips|blotchy|mottled|stiff\s+neck|screaming|"
    r"inconsolable|seizure|fit|convulsion|shaking|shivering\s+hard)\b",
    r"\b(?:3[9]|4[0-3])(?:\.\d)?\b", r"\b(?:forty|thirty-nine)\b",
    r"\b(?:rash|spots|non[\s-]?blanching)\b",
    r"\b(?:not\s+drinking|wont\s+drink|won'?t\s+drink|refusing\s+to\s+drink|"
    r"not\s+taking\s+(?:fluids?|drinks?)|refusing\s+(?:drinks?|fluids?|the\s+bottle)|"
    # A fever with repeated vomiting is the amber case, and "keeps being sick" is how a parent
    # says it: it was the everyday advice, which assumes the drinks stay down.
    r"keeps\s+(?:being\s+sick|throwing\s+up|vomiting)|being\s+sick|throwing\s+up|vomiting|"
    r"cant\s+keep\s+(?:fluids?|drinks?|water)\s+down|no\s+(?:wet\s+)?napp(?:y|ies)|"
    r"sunken\s+eyes)\b",
)

CHILD_GROWN = (
    r"\b(?:1[0-9]|[2-9]\d)\s*(?:year|yr)s?[-\s]*old\b",
    r"\b(?:my|his|her|their|our|the)\s+(?:son|daughter|boy|girl|child|kid|little\s+one)s?\s+"
    r"(?:is|was|aged|of)\s+(?:1[0-9]|[2-9]\d)\b",
    r"\b(?:aged|age)\s+(?:1[0-9]|[2-9]\d)\b",
    r"\b(?:teenager|teen|teens|adolescent)\b",
)

CHILD_YOUNG = (r"\b(?:toddler|baby|babies|infant|newborn|little\s+one|preschool|nursery|"
               r"\b\d+\s*(?:month|year)s?\s+old|\b(?:one|two|three|four|five|six|1|2|3|4|5|6)\s+"
               r"years?\s+old)\b",
               r"\b(?:my|his|her|their)\s+(?:son|daughter|boy|girl|kid|child|niece|nephew)\b"
               r"[^.?!]{0,12}\b(?:is|just|only|nearly|almost)\s+(?:one|two|three|four|1|2|3|4)\b")

RECENT_FIT_FINE = (
    # A seizure from laughing, or at a price, is the same joke as a heart attack at a bill.
    r"\b(?:laughing|at\s+that|at\s+the\s+price|when\s+i\s+saw|when\s+i\s+heard|nearly|almost|"
    r"felt\s+like|thought\s+i\s+would)\b",
    r"\bfit\s+of\b", r"\b(?:every|each|once|twice|three\s+times|a\s+month|a\s+year|"
    r"regularly|sometimes|usually|last\s+year|years\s+ago|used\s+to)\b",
    # A fit a week or a month ago is a question for the doctor today, not an ambulance now.
    r"\b(?:last\s+(?:week|month|summer|winter|spring|autumn)|weeks?\s+ago|months?\s+ago|"
    r"a\s+(?:few|couple)\s+(?:weeks|months)\s+ago|back\s+in\s+\d{4}|when\s+(?:he|she|they)\s+"
    r"(?:was|little)|as\s+a\s+(?:baby|kid|child))\b",
    r"\b(?:epilep\w+|condition|medication|meds|tablets?|keppra|epilim)\b",
)

# ...but a grunt in the cot is the noise a small baby makes in its sleep, not a struggling chest.
# The chest has to be the thing that is working, or something red has to be going on with it.
GRUNTING_FINE = (
    r"\b(?:in\s+(?:his|her|their|its|the)\s+(?:sleep|cot|crib)|while\s+(?:a)?sleep\w*|asleep|"
    r"sleeping|at\s+night|when\s+sleeping|grunting\s+baby\s+syndrome)\b",
    # Grumbling about something is a grunt with an object, not a chest working too hard.
    r"\bgrunt(?:s|ing|ed)?\s+(?:at|over|about|through|in\s+reply)\b",
)

FEVER_RASH_FINE = (
    r"\b(?:heat|nappy|diaper|teething|teething|prickly\s+heat|sweat)\s+rash\b",
    r"\bchicken\s?pox\b", r"\bhand[,\s]+foot\b", r"\beczema\b", r"\bnettle\s+rash\b",
    r"\broseola\b", r"\bhas\s+had\s+it\s+before\b", r"\bfifth\s+disease\b",
    r"\bsixth\s+disease\b", r"\bfungal\b", r"\bthrush\b",
)

HYPO_STRONG = (
    r"\bsweat\w*", r"\bclammy\b", r"\bshak\w*", r"\btrembl\w*", r"\bdrows\w*",
    r"\bslurr\w*", r"\bwon'?t\s+wake\b", r"\bcan'?t\s+stay\s+awake\b",
    r"\b(?:a|another)\s+fit\b", r"\bseizure\w*", r"\bcoma\b", r"\bunconscious\b",
    r"\bpassed\s+out\b", r"\bfaint\w*", r"\bacting\s+(?:drunk|odd|strange|weird)\b",
)

# A diabetic asking about food, or about the condition in general, is not a crisis: "what can i
# eat", "can diabetics drink beer", "is it normal to feel shaky when your sugar is high". The
# question is what makes it one, so a line with a sign in it and no question still rings.
HYPO_QUESTION = (
    r"\b(?:is|was)\s+(?:it|that)\s+(?:normal|ok|okay|safe|dangerous|common)\b",
    r"\bwhat\s+(?:can|could|should)\s+(?:i|he|she|they|we)\s+(?:eat|drink|have|snack)\b",
    r"\b(?:diet|recipes?|meal\s+(?:plan|ideas?)|what\s+to\s+cook)\b",
    r"\b(?:can|could|may|should)\s+(?:a\s+)?\bdiabetics?\b",
    r"\bdiabetics?\s+(?:eat|drink|have|take)\b",
    r"\b(?:symptoms?|signs?)\s+of\s+(?:a\s+)?(?:hypo\w*|low\s+blood\s+sugar)\b",
    r"\bhow\s+(?:common|likely|dangerous|many|often)\b",
    r"\bwhat\s+(?:does|do)\b[^.?!]{0,25}\b(?:feel|look|mean)\b",
)

# The signs that are not a wake-up: a lie-in stands down only when the time is all there is.
HYPO_STRONG_OTHER = (
    r"\bsweat\w*", r"\bclammy\b", r"\bshak\w*", r"\btrembl\w*", r"\bdrows\w*",
    r"\bconfus\w*", r"\bdisorient\w*", r"\bslurr\w*", r"\b(?:a|another)\s+fit\b",
    r"\bseizure\w*", r"\bcoma\b", r"\bunconscious\b", r"\bpassed\s+out\b",
    r"\bfaint\w*", r"\bacting\s+(?:drunk|odd|strange|weird)\b",
    r"\bcan'?t\s+stay\s+awake\b", r"\bnot\s+making\s+(?:any\s+)?sense\b",
)

# "How do i know im having a hypo" asks what a hypo feels like, so it is a question even though it
# says "having a hypo": the present low reading is what LOW_SUGAR_NOW is for, not a question.
HYPO_HOW_KNOW = (
    r"\bhow\s+(?:do|can|could|would|will|should)\s+(?:i|you|we|he|she|they)\s+(?:know|tell|spot|"
    r"avoid|prevent|stop|reduce)\b",
    r"\bhow\s+to\s+(?:avoid|prevent|stop|spot|recognise|recognize)\b",
    r"\bwhat\s+does\b[^.?!]{0,25}\b(?:feel|look)\s+like\b",
    # Worrying about one, or trying to keep one away, is the worry itself and not the hypo now.
    r"\b(?:avoid|avoiding|prevent|preventing|stop\s+myself|keep\s+(?:from|it\s+from)|"
    r"ward\s+off|less\s+likely)\b",
    r"\b(?:worried|worry|worrying|scared|afraid|frightened|anxious)\s+(?:about|of|that)\b",
    r"\b(?:risk\s+of|in\s+case\s+(?:i|he|she|they))\b",
)

# A bone in the throat is not a stock recipe and not a swallowed poison: it goes down or it is
# fished out, and only a bone that stops them swallowing their own spit is an ambulance. Without
# this, "i swallowed a chicken bone" was answered with how to make stock.
# A pea, a bead or a button battery goes up a small nose or into an ear, and nothing answered it:
# "my toddler has a button battery up his nose" was "Got it. Is there anything you'd like a hand
# with?", "my daughter has a bead up his nose" was "Noted:", and "my toddler put a raisin up his
# nose" was the choking advice about whole raisins. A button battery in either place burns the
# tissue within hours, so that one is A&E at once; an ordinary object wants one gentle blow and
# then urgent care today, and never a cotton bud or tweezers.
OBJECT_IN_HEAD_THING = (
    r"(?:beads?|batter(?:y|ies)|lego|bricks?|peas?|beans?|sweets?|corn(?:flake)?s?|cereal|"
    r"raisins?|sultanas?|nuts?|peanuts?|popcorn|marbles?|stones?|pebbles?|seeds?|pips?|crayons?|"
    r"pencils?|erasers?|rubbers?|toys?|playmobil|rice|pasta|papers?|tissues?|plastic|coins?|"
    r"magnets?|insects?|bugs?|flies|fly|spiders?|earwigs?|moths?|crumbs?|"
    r"something|a\s+thing|anything)"
)

BONE_THROAT = (
    r"\b(?:fish\s?bone|fishbone|chicken\s+bone|lamb\s+bone|pork\s+bone|beef\s+bone|turkey\s+bone|"
    r"rabbit\s+bone|duck\s+bone|bone|bones)\b[^.?!]{0,25}"
    r"\b(?:stuck|caught|lodged|wedged|scraping|scratching|gone\s+down\s+the\s+wrong\s+way)\b",
    r"\b(?:stuck|caught|lodged|wedged)\b[^.?!]{0,20}\b(?:in|down)\s+(?:my|his|her|their|the|your)\s+"
    r"(?:throat|gullet|neck|windpipe)\b",
    r"\b(?:swallowed|swallowing|ate|eaten|eating|got\s+down)\b[^.?!]{0,20}\b(?:fish\s?bone|bone|bones)\b",
    r"\b(?:bone|bones|fishbone|shell|husk|pip|kernel)\b[^.?!]{0,15}\b(?:in|down)\s+(?:my|his|her|their)\s+"
    r"throat\b",
)

# A bone in the stock pot, a bone in the leg, a bone to pick, and a dog with a bone are not throats.
BONE_ORDINARY = (
    r"\b(?:stock|broth|soup|carcass|recipe|roast|gravy|stew|casserole|curry|fry|bake|baking)\b",
    r"\b(?:dog|cat|puppy|kitten|pup|parrot|pet|bird|hamster)\b",
    r"\b(?:broken|breaks?|broke|fractur\w*|density|marrow|graft|spur|cancer|cyst|scan|x-?ray|"
    r"hip|leg|arm|wrist|ankle|shoulder|knee|spine|back|ribs?|skull|jaw|toe|foot)\b[^.?!]{0,15}\bbone\b",
    r"\bbone\b[^.?!]{0,15}\b(?:density|loss|pain|graft|marrow|spur|china|dry|tired|idle|lazy)\b",
    r"\b(?:wishbone|backbone|bare\s+bones|no\s+bones\s+about|bone\s+of\s+contention|"
    r"bone\s+to\s+pick|funny\s+bone|t-?bone|herringbone)\b",
    r"\b(?:chew|chewed|chewing|gnaw\w*)\b[^.?!]{0,15}\bbone\b",
)

# A bone that went down last year is a memory, not a throat that needs looking at now; it is only
# still live if the line says the thing never came out.
BONE_PAST = (
    r"\b(?:last|this)\s+(?:year|month|week|christmas|summer)\b",
    r"\b(?:years?|months?|weeks?)\s+(?:ago|back)\b", r"\bin\s+(?:19|20)\d\d\b",
    r"\b(?:as|when\s+i\s+was)\s+a\s+(?:kid|child|baby|teen|little\s+one)\b",
    r"\bused\s+to\b", r"\bwhen\s+i\s+was\s+(?:little|small|young)\b",
    r"\bages\s+ago\b",
)

# A fall in someone older is a check-today line even when they got up again: a hip and a head knock
# do not always show at the time, and being down once is what starts the long lie. The ambulance
# signs, the near miss and the fall that ended fine all keep their own readings above.
OLD_PERSON = (
    # "my dad is 85 and he fell", "she was 82", "hes 91 and had a fall".
    r"\b(?:is|was|'s|s|at|turned)\s+(?:6[5-9]|[7-9][0-9]|1[0-2][0-9])\b",
    r"\b(?:i'?m|im|i\s+am)\s+(?:6[5-9]|[7-9][0-9]|1[0-2][0-9])\b",
    # "my gran is 78 years old", "he is 85yo".
    r"\b(?:6[5-9]|[7-9][0-9]|1[0-2][0-9])\s*(?:years?[\s-]?old|yrs?\s+old|yr[\s-]?old|yo)\b",
    r"\baged\s+(?:6[5-9]|[7-9][0-9]|1[0-2][0-9])\b",
    r"\bover\s+(?:65|70|75|80|85|90|95)\b",
    # The decade is enough and needs no number: "my mum is in her 80s".
    r"\b(?:in|into|on)\s+(?:his|her|their)\s+(?:mid[\s-]?)?(?:60s|70s|80s|90s)\b",
    r"\b(?:elderly|pensioner|oap)\b",
    r"\bold\s+(?:man|woman|lady|gentleman|chap|boy|girl|dear|soul|mum|dad|mother|father|"
    r"mam|gran|grandad|neighbou?r)\b",
    # A grandparent is old enough for this to be worth saying, and that is how people write it.
    r"\b(?:gran|granny|nan|nana|grandma|grandmother|grandad|granddad|grandpa|grandfather)\b",
)

# A fall that ended fine is a story, and the person saying it says so: "he says hes fine", "the
# doctor has seen her", "nothing broken". "He got up" is deliberately not here - an older person
# who got up still wants a look today, which is the whole point of this arm.
OLD_FALL_FINE = (
    r"\b(?:but|and|though)\s+(?:he|she|they|it)\s*(?:'s|s|\s+is|\s+was)?\s*(?:ok|okay|fine|"
    r"alright|all\s+right)\b",
    r"[,;]\s*(?:but\s+)?(?:hes|shes|theyre|he\s+is|she\s+is|they\s+are|he'?s|she'?s|they'?re)\s+"
    r"(?:now\s+)?(?:ok|okay|fine|alright|all\s+right)\b",
    r"\b(?:says?|said|tells?|told)\s+(?:me\s+)?(?:he|she|they)\s*(?:'s|s|\s+was|\s+is)?\s*"
    r"(?:ok|okay|fine|alright)\b",
    r"\b(?:nothing\s+broken|no\s+harm|just\s+bruised|only\s+bruised|walked\s+it\s+off|"
    r"laughed\s+it\s+off|laughed\s+about\s+it)\b",
    r"\b(?:had|got)\s+(?:it|him|her|them)\s+(?:checked|looked\s+at)\b",
    r"\b(?:seen|checked)\s+by\s+(?:the\s+)?(?:doctor|gp|nurse|paramedics?)\b",
    r"\b(?:been\s+)?(?:x-?rayed|x-?rays?)\b", r"\bin\s+(?:the\s+)?hospital\b",
    r"\b(?:has|have|had)\s+been\s+(?:seen|checked)\b",
)

# A hip that hurts after a fall is an X-ray today whatever the person's age: the age is what makes a
# fall a fracture more likely, not what makes it worth looking at.
FALL_HIP = (
    r"\b(?:fell|fallen|fall|falls|slipped|tripped|went\s+over|had\s+a\s+fall|toppled)\b"
    r"[^.?!]{0,45}\b(?:hip|pelvis)\b[^.?!]{0,25}\b(?:hurt\w*|pain\w*|sore|ache\w*|aching|"
    r"broke\w*|click\w*|stiff|gave\s+way|is\s+bad)\b",
    r"\b(?:hurt\w*|pain\w*|sore|ache\w*|aching|broke\w*|click\w*)\b[^.?!]{0,25}"
    r"\b(?:hip|pelvis)\b[^.?!]{0,45}\b(?:fell|fallen|fall|slipped|tripped|went\s+over|"
    r"had\s+a\s+fall)\b",
    # "he fell and hurt his hip": the hip is what the fall did to him.
    r"\b(?:fell|fallen|fall|falls)\b[^.?!]{0,40}\b(?:hurt|broke\w*|injured|done|damaged)\b"
    r"\s+(?:his|her|their|my|the|a)\s+(?:hip|pelvis)\b",
)

# "He fell asleep at three", "she fell for it", "they fell out over the will": the verb, not a fall.
OLD_FALL_NOT = (
    r"\bfell\s+(?:asleep|for\s+(?:it|him|her|them|the)|in\s+love|out\s+(?:with|over)|apart|"
    r"through|short|behind|flat|ill|silent|prey)\b",
    r"\bfell\s+(?:over\s+|about\s+)?laughing\b", r"\bwent\s+down\s+(?:well|badly|a\s+treat|like)\b",
    # Going over on an ankle is a sprain, not a fall.
    r"\bwent\s+over\s+on\s+(?:my|his|her|their)\s+(?:ankle|foot)\b",
    r"\bthe\s+(?:price|prices|market|temperature|rain|snow|share|shares)\b",
    r"\bfall(?:ing)?\s+(?:asleep|for|in\s+love|out|apart|through|short|behind)\b",
)

SHOT = (
    r"\b(?:has|have|had|been|got|gets|was|were)\s+(?:been\s+)?shot\b",
    # The object of "shot" was somebody else - "shot him", "shot me" - and a reflexive is nobody's
    # object: "shot himself" matched no arm of this list and no other case in safety.py, so "my son
    # shot himself" was filed as a fact and answered "Noted: your son shot himself." A gunshot is a
    # gunshot whoever was holding the gun, so the reflexives are read the same way as the rest.
    r"\bshot\s+(?:him|her|them|me|my\s*self|himself|herself|themselves|in\s+the|through)\b",
    r"\bshot\s+(?:a\s+|the\s+)?(?:man|woman|person|boy|girl|kid|child|policeman|officer)\b",
    r"\b(?:gunshot|someone\s+shot|they\s+shot|he\s+shot|she\s+shot|shots\s+fired)\b",
)

SHOT_FINE = (
    r"\b(?:paintball\w*|bb\s+gun|airsoft|nerf|toy\s+gun|water\s+pistol|squirt\s+gun)\b",
    r"\b(?:flu|covid|tetanus|booster|vaccine|vaccination|immunisation|immunization|jab)s?\b",
    r"\b(?:photo|photograph|picture|film|movie|camera|scene|screenshot|screengrab|video)s?\b",
    r"\ba\s+shot\s+of\b", r"\bshot\s+glass(?:es)?\b", r"\bshot\s+put\b",
    r"\b(?:long|wide|close|medium)\s+shot\b", r"\bshot\s+(?:up|down)\b",
    # "it was a shot in the dark" is a guess, not a wound: "shot in the" alone fired the gunshot
    # card, so the figure of speech rang 999.
    r"\ba\s+shot\s+in\s+the\s+dark\b",
    # "shot himself in the foot with that email" is the figure of speech, and the something after
    # it is what says so: a real wound has no "with that" after it, and "i shot myself in the foot"
    # on its own keeps the card because a foot with a bullet in it is an ambulance either way.
    r"\bshot\s+(?:my\s*self|him|her|them)sel(?:f|ves)\s+in\s+the\s+foot\s+(?:with|over|on)\s+"
    r"(?:that|this|the)\b",
    r"\b(?:goal|baskets?|balls?|penalt(?:y|ies)|hoop|free\s+kick|target|round|bird|rabbit|"
    r"deer|fox|pheasant|clay\s+pigeon)s?\b",
)

# Acid, bleach or a drain cleaner in the eye: the rinsing is the treatment, and the clock is the
# sight. It has to say the chemical *and* that it went in the eye - fumes that make the eyes water
# are a different, smaller thing.
CHEM_WORD = (
    # A bottle that says "cleaner" and nothing else is the same burn as one that says bleach:
    # "i sprayed cleaner in my eye" was answered "Got it. Is there anything you'd like a hand
    # with?", which is the worst reply the bot can give to a chemical in the eye.
    r"\b(?:acid|bleach|cleaners?|detergent|powder|powders|drain\s+cleaner|caustic|chemical\w*|"
    r"lye|ammonia|white\s+spirit|"
    r"paint\s+thinner|thinners?|solvent|oven\s+cleaner|petrol|paraffin|chlorine|antifreeze|"
    r"disinfectant|diesel|turpentine|nail\s+varnish\s+remover)\b"
)

EYE_CHEM = (
    CHEM_WORD[:-2] + r"[^.?!]{0,25}\b(?:in|into|inside|over)\s+(?:my|his|her|their|your|both|one|"
    r"the)\s+eyes?\b",
    r"\beyes?\b[^.?!]{0,20}\b(?:full\s+of|covered\s+in|splashed\s+with|with)\b"
    r"[^.?!]{0,15}" + CHEM_WORD,
    r"\b(?:splashed|squirted|sprayed|poured)\b[^.?!]{0,20}" + CHEM_WORD
    + r"[^.?!]{0,20}\b(?:in|into)\s+(?:my|his|her|their|your)\s+eyes?\b",
    # A deodorant, a hairspray or a scoop of washing powder in the eye is the same burn as bleach, and
    # main answered it with a shrug: these are the chemicals people keep in a bathroom or a kitchen.
    r"\b(?:got|get|gets|getting|had|has|have|sprayed|spray|splashed|splash|poured|threw|squirted|"
    r"dabbed|rubbed|put|smeared|scooped)\b[^.?!]{0,30}"
    r"\b(?:washing\s+powder|washing\s+up\s+liquid|deodorant|hairspray|hair\s+spray|perfume|"
    r"aftershave|ac?etone|nail\s+varnish|superglue|glue|silicone|limescale|toilet\s+cleaner|"
    r"carpet\s+cleaner|screen\s+wash)\b[^.?!]{0,25}\b(?:eye|eyes)\b",
    # "how do i get powder out of my eye" names the getting-out, not the going-in, and it is the
    # same question: a laundry powder in the eye is a burn and the rinsing is the treatment.
    r"\b(?:powder|powders|detergent|cleaner|cleaners|bleach|spray)\b[^.?!]{0,20}"
    r"\b(?:out of|in|into|off)\s+(?:my|his|her|their|your)\s+eyes?\b",
    r"\b(?:washing\s+powder|deodorant|hairspray|perfume|aftershave|nail\s+varnish|superglue|"
    r"limescale|toilet\s+cleaner)\b[^.?!]{0,30}\b(?:in|into|went)\b[^.?!]{0,12}"
    r"\b(?:my|his|her|their|the)\s+(?:\w+\s+)?eyes?\b",
)

EYE_FINE = (
    r"\b(?:acid\s+reflux|heartburn|acid\s+stomach|stomach\s+acid|acid\s+rain|acid\s+jazz|"
    r"amino\s+acids?|folic\s+acid|acid\s+test|acid\s+house|acid\s+wash)\b",
    r"\b(?:clean|cleaning|cleaned)\s+(?:the\s+|my\s+)?(?:bathroom|kitchen|oven|drain|shower|"
    r"toilet|windows?)\b",
    r"\b(?:keep|keeps|kept|store|stored|out\s+of\s+reach)\b[^.?!]{0,30}\beyes?\b",
)

FOOD_CUT = (
    r"\b(?:avocado|avocados|bread|cake|loaf|cheese|tomato|tomatoes|onion|onions|lettuce|salad|"
    r"cabbage|apple|apples|banana|bananas|lemon|oranges?|melon|mango|pepper|peppers|cucumber|"
    r"carrot|carrots|potato|potatoes|celery|fruit|herbs?|chilli|chillies|garlic|ginger|lemon|"
    r"lime|bacon|ham|chicken|beef|pork|lamb|fish|sausage|sausages|steak|meat|pizza|lasagne|"
    r"quiche|pie|sandwich|wrap|roll|bagel|pastry|croissant|melon|watermelon|pineapple|veg|"
    r"vegetables?|courgette|aubergine|broccoli|cauliflower|squash|pumpkin)\b",
)

HEADACHE_BAD = (
    r"\b(?:worst|bad|terrible|awful|severe|unbearable|splitting|thumping|excruciating)\b"
    r"[^.?!]{0,15}\bhead(?:ache)?\b",
    r"\bhead(?:ache)?\b[^.?!]{0,30}\b(?:worst|unbearable|severe|excruciating|terrible|"
    r"awful|bad)\b",
    r"\bworst\s+head(?:ache)?\s+of\s+my\s+life\b",
)

HEADACHE_SUDDEN = (
    r"\bsudden\w*", r"\bout\s+of\s+(?:nowhere|the\s+blue)\b", r"\ball\s+of\s+a\s+sudden\b",
    r"\bthunderclap\b", r"\bwithin\s+(?:a\s+)?(?:minute|seconds?)\b",
    r"\blike\s+a\s+(?:bang|clap|thunder|blow)\b", r"\bexploded\b",
    r"\bcame\s+on\b[^.?!]{0,15}\b(?:suddenly|fast|quickly|in\s+seconds|like)\b",
)

# A headache that is over, or one with an ordinary cause named, is the ordinary module's answer.
HEADACHE_STORY = (
    r"\b(?:not|isnt|isn'?t)\s+(?:that|too|so|very)\s+bad\b", r"\ba\s+bit\b", r"\bslight\w*",
    r"\bmild\b", r"\bmanageable\b", r"\bnot\s+too\s+bad\b",
    r"\b(?:last\s+(?:year|month|week)|years?\s+ago|when\s+i\s+was\s+(?:a\s+)?(?:kid|child|"
    r"little)|used\s+to|went\s+away|gone\s+now|had\s+one\s+before|still\s+there)\b",
    r"\b(?:hangover|migraine|dehydrat\w*|sinus\w*|hay\s?fever|screen|computer|tension\s+headache|"
    r"stress\w*|period|flu|cold|cough|headache\s+tablets?|paracetamol|ibuprofen)\b",
)

# The everyday reasons for a rash and a headache together, which pass without a card: a heat rash,
# a shaving rash, chickenpox the family already knows about.
RASH_HEADACHE_FINE = (
    r"\b(?:heat|nappy|diaper|teething|prickly\s+heat|sweat|shav(?:e|ing)|razor|sunburn|"
    r"sun\s+burn|acne|hives|nettle|eczema|dermatitis|allerg\w*|hay\s?fever|thrush|fungal)\b"
    r"[^.?!]{0,15}\brash\b",
    r"\brash\b[^.?!]{0,15}\b(?:from|after|off)\s+(?:a\s+|the\s+|my\s+|her\s+|his\s+)?"
    r"(?:shav\w*|razor|wax\w*|sun|heat|perfume|new\s+cream|cream|washing\s+powder|plaster|"
    r"tape|nappy|diaper)\b",
    # A mark the line itself explains - a new shirt, a seat belt, a bump - is not a rash to ring
    # about, whichever of the rash words it used.
    r"\b(?:rash|rashes|spots|marks|dots|blotches)\b[^.?!]{0,20}\b(?:from|after|off|where)\b",
    r"\b(?:chicken\s?pox|hand[,\s]+foot|roseola|fifth\s+disease|sixth\s+disease|shingles)\b",
    r"\b(?:had\s+it\s+before|last\s+(?:week|month|year)|weeks?\s+ago|years?\s+ago)\b",
    # A teenager's spots are not a meningitis rash, and a face is where they are: "i have a
    # headache and spots on my face" was sent to ring 111 with the glass test, which is the one
    # thing that would make the card untrustworthy on the lines it is right for. The place has to
    # be beside the spot word, so "spots on my legs" and "a rash on her tummy" keep the card.
    r"\b(?:spots|pimples|blackheads|whiteheads|zits|acne|breakouts?)\b[^.?!]{0,25}"
    r"\b(?:on|around|across)\s+(?:my\s+|his\s+|her\s+|their\s+|the\s+)?"
    r"(?:face|forehead|chin|cheeks?|nose|jaw|back|shoulders?)\b",
)

# Blood in what you cough up is a today question, not a wait-and-see one.
COUGH_BLOOD = (
    r"\b(?:cough\w*|spit\w*|bringing|bring)\b[^.?!]{0,20}\b(?:up|out)\b"
    r"[^.?!]{0,20}\bblood\b",
    r"\bblood\b[^.?!]{0,20}\b(?:when\s+i\s+cough|coughing|in\s+my\s+(?:sputum|phlegm|spit|"
    r"mucus))\b",
    r"\b(?:coughing|spitting)\s+(?:up\s+)?blood\b",
    r"\bbloody\s+(?:sputum|phlegm)\b",
)

# Breathlessness out of the blue, or while sitting still, is a different animal from the stairs: a
# clot on the lung or a heart problem can start that way, so it is the ambulance.
BREATH_REST = (
    r"\b(?:suddenly|all\s+of\s+a\s+sudden|out\s+of\s+nowhere|out\s+of\s+the\s+blue|"
    r"just\s+now|came\s+on)\b.{0,30}"
    r"\b(?:short\s+of\s+breath|breathless|out\s+of\s+breath|can'?t\s+breath\w*|"
    r"struggling\s+to\s+breath\w*)\b",
    r"\b(?:short\s+of\s+breath|shortness\s+of\s+breath|breathless)\b.{0,30}"
    r"\b(?:sitting|sat\s+down|lying|in\s+bed|at\s+rest|resting|doing\s+nothing|"
    r"watching\s+tv|in\s+a\s+chair)\b",
)

# Swallow the tablets and keep the glass: a spiked drink is about the next few hours, not the drink.
SPIKED = (
    r"\b(?:drink|drinks|pint|glass|cocktail|bottle|water)\b[^.?!]{0,25}\b(?:was|got|is)\s+"
    r"(?:spiked|drugged|dosed)\b",
    r"\b(?:spiked|drugged|dosed)\s+(?:my|his|her|their|the|someone'?s)\s+(?:drink|drinks|pint|glass|"
    r"bottle|water)\b",
    r"\bi\s+(?:think\s+|reckon\s+|pretty\s+sure\s+)?(?:got|was|been)\s+(?:spiked|drugged|dosed)\b",
    r"\bsomeone\s+(?:put|slipped|dropped|spiked)\s+(?:something|a\s+pill|drugs?|roofies?)\s+"
    r"(?:in|into)\s+(?:my|his|her|their|the)\s+(?:drink|pint|glass|water|bottle)\b",
    r"\broofies?\b", r"\bdrink\s+was\s+spiked\b",
    # "my friend was spiked at the club" - the person is in the line, the drink is not.
    r"\b(?:i|he|she|they|my\s+" + PERSON + r"|a\s+" + PERSON + r")\b(?![^.?!]{0,20}\bdrink\b)"
    r"[^.?!]{0,20}\b(?:got|was|were|been)\s+(?:spiked|drugged|dosed)\b",
)

# Hearing someone hurt through a wall is a scene with no first person in it, so the abuse arm - which
# is written from the point of view of the person being hurt - never reached it.
HEARD_ASSAULT = (
    r"\b(?:screaming|screams|shouting|yelling|banging|smashing|glass\s+breaking|crashing)\b"
    r"[^.?!]{0,40}\b(?:hurting|hitting|beating|attacking|choking|dragging|kicking)\s+"
    r"(?:her|him|them|each\s+other|his\s+(?:wife|girlfriend|partner|kid|son|daughter)|"
    r"her\s+(?:husband|boyfriend|partner|kid|son|daughter))\b",
    r"\b(?:i\s+can\s+hear|i\s+heard|we\s+can\s+hear)\b[^.?!]{0,40}\b(?:screaming|shouting|"
    r"smashing|glass\s+breaking|banging|someone\s+crying)\b[^.?!]{0,40}\b(?:next\s+door|"
    r"upstairs|downstairs|neighbou?rs?|flat\s+above|flat\s+below|from\s+the\s+flat)\b",
    r"\b(?:my|our|the)\s+neighbou?rs?\b[^.?!]{0,40}\b(?:hurting|hitting|beating|attacking|"
    r"fighting|smashing\s+the\s+place)\b",
    # "theres a woman screaming in the flat next door": a person and a dwelling is the same call,
    # even without the words "i can hear".
    r"\b(?:a\s+|some\s+)?(?:woman|man|girl|boy|kid|child|lady|bloke|fella|someone|somebody|"
    r"neighbou?r)\b[^.?!]{0,30}\b(?:screaming|sobbing|shouting\s+for\s+help|"
    r"crying\s+for\s+help|begging)\b[^.?!]{0,40}\b(?:next\s+door|upstairs|downstairs|"
    r"the\s+flat|the\s+house|the\s+street|outside\s+(?:my|our|the))\b",
)

# "i ran for the bus and im gasping for air" is the effort, not a lung: an effort that has just
# happened takes the breathlessness back to ordinary, unless a body sign comes with it.
BREATH_EFFORT = (
    r"\b(?:ran|run|running|jogged|jogging|sprinted|hurried|rushed|chased|cycled|raced|legged\s+it)\b"
    r"[^.?!]{0,25}\b(?:for|to|after|up|down)\s+(?:the\s+|a\s+|my\s+)?(?:bus|train|tram|tube|"
    r"coach|plane|flight|stairs|steps|ladder|hill)\b",
    r"\b(?:ran|jogged|sprinted|walked)\s+(?:up|down)\s+the\s+(?:stairs|steps|hill|road)\b",
)

# A class or a sport named with a recovery phrase. BREATH_EFFORT above only knows running for a
# bus, so "i cant catch my breath after spin class" rang the ambulance for a person who had just
# done some exercise; a bare "i cant breathe after boxing" has no recovery phrase and keeps 999.
EXERTION_CLASS = (
    r"\b(?:spin(?:ning)?|zumba|pilates|cross-?fit|box(?:ing)?|kickbox\w*|skipping|badminton|rugby|"
    r"cricket|hike|hiking|treadmill|cross-?trainer|elliptical|aerobics|hiit|circuit|rowing|"
    r"boot\s?camp|exercise\s+class|fitness\s+class|spin\s+class|aqua\s?aerobics|squash|"
    r"body\s?pump|body\s?combat|pt\s+session|gym\s+class)\b",
    r"\b(?:class|classes|session|workout)\b",
)

EFFORT_RED_HEART = (
    r"\b(?:faint\w*|dizzy|light-?headed|numb|tingl\w*|passed\s+out|"
    r"collapsed|blacked\s+out|vomit\w*|nause\w*|queasy|palpitations?|fluttering)\b",
    r"\b(?:feel|feels|feeling|felt)\s+(?:sick|ill|queasy|faint)\b",
    # Pain that travels is how a heart reports itself: "i cant catch my breath after class and my
    # arm hurts" is the ambulance, and an arm, a jaw or a shoulder is as good as a chest.
    r"\b(?:arm|arms|jaw|shoulder|shoulders|neck)\b[^.?!]{0,20}"
    r"\b(?:hurt\w*|pain\w*|ache\w*|tight\w*|heavy|sore|numb)\b",
    r"\b(?:hurt\w*|pain\w*|ache\w*|tight\w*|heavy|sore)\b[^.?!]{0,15}"
    r"\b(?:arm|arms|jaw|shoulder|shoulders|neck)\b",
)

# Sweating, clamminess, a cold damp skin or feeling faint or sick is the cluster a heart reports
# itself with when it is short of blood, and it is what makes breathlessness on a small effort a
# call rather than a fitness question. Pain down an arm or into the jaw has its own reading above,
# so this is the rest of the cluster.
EFFORT_HEART_CLUSTER = (
    r"\b(?:clammy|light-?headed|dizzy|dizziness|faint\w*|woozy|queasy|nauseous|nausea)\b",
    r"\b(?:grey|gray|pale|ashy)\b[^.?!]{0,12}\b(?:face|skin|lips?)\b",
    # A sweat is the cluster only with a hand on either side of it: cold or drenching on its own, or
    # beside another of these words ("and i am sweating and dizzy"). Every hot stairwell in the
    # country produces a sweat, and the card is not for those.
    r"\b(?:cold|damp|drench(?:ed|ing)|soaked|wet)\s+(?:with\s+|in\s+|and\s+)?(?:sweat\w*|clammy)\b",
    r"\bsweat\w*\b[^.?!]{0,24}\b(?:dizzy|light-?headed|faint\w*|woozy|sick|queasy|nauseous|"
    r"clammy)\b",
)

# A pattern is not a call: months of the same breathlessness on the same stairs is a GP question
# about a body that has changed, not an ambulance tonight. It hands the line to the GP reading.
EFFORT_PATTERN = (
    r"\b(?:always|every\s+time|each\s+time|usually|normally|whenever)\b",
    r"\bfor\s+(?:months|years|weeks|ages|a\s+while)\b",
    r"\b(?:since|from)\s+(?:last\s+year|childhood|i\s+was\s+(?:a\s+)?(?:kid|child|younger|at\s+school))\b",
    r"\b(?:keeps?|kept)\s+(?:happening|coming\s+back|doing\s+it)\b",
    r"\bon\s+and\s+off\b",
)

# Something other than a heart explains the same words, and the everyday answers know more about
# those than this module does: a pregnant person feeling sick on the stairs, a stinking cold, hay
# fever, a hot day, being unfit, or the sweat of a class just finished. The cluster rule stands
# down for them so the rest of the bot can answer the line it was actually about.
EFFORT_BENIGN = (
    r"\b(?:pregnan\w*|expecting\s+a\s+baby|trimester)\b",
    r"\b(?:a|the|this|my)\s+(?:cold|flu|covid|coronavirus|chest\s+infection|virus)\b",
    r"\bhay\s?fever\b|\bpollen\b|\ballergie\w*\b|\bhistamine\b",
    r"\b(?:hot\s+day|heat\s?wave|in\s+this\s+heat|hot\s+weather|hot\s+building|boiling)\b",
    r"\b(?:unfit|out\s+of\s+shape|overweight|put\s+on\s+weight)\b",
)

# Ten minutes at rest is the line the settling answer itself draws: a line that says it has already
# been longer, or all afternoon, is not a person who has just come off a bike.
EFFORT_TOO_LONG = (
    r"\b(?:for|it'?s\s+been|its\s+been|been|about|over|more\s+than|nearly|almost)\s+"
    r"(?:an?\s+hour|half\s+an\s+hour|(?:eleven|twelve|fifteen|twenty|twenty-five|thirty|forty|"
    r"fifty|sixty|\d{2,})\s*(?:min|mins|minutes?)|ages)\b",
    r"\b(?:over|more\s+than)\s+ten\s+minutes\b",
    r"\ball\s+(?:day|morning|afternoon|evening)\b",
)

BREATH_EFFORT_RED = (
    r"\b(?:blue|grey|gray|collapsed|unconscious|passed\s+out|crushing|crushed|chest\s+pain|"
    r"pins\s+and\s+needles|numb)\b",
    r"\b(?:still|now|and)\b[^.?!]{0,20}\b(?:can'?t|cannot|cant)\s+breathe\b",
    r"\b(?:can'?t|cannot|cant|unable\s+to)\s+(?:catch|get)\s+(?:my|her|his|their)\s+breath\b",
    r"\b(?:hours?|days?)\s+(?:later|ago)\b",
)

# Swelling of the lips, tongue or throat can close the airway, and a sting or a food is the usual
# cause: the ambulance is the answer, not an antihistamine and a shrug. A cold sore, chapped lips
# and a new piercing are not this, so a cause or a throat/tongue/breathing word has to be there.
LIPS_SWELL = (
    r"\b(?:lips?|tongue|throat|face)\b[^.?!]{0,30}\b(?:swelling|swollen|swelled|puff\w*\s+up|"
    r"puffed\s+up|puffy|blowing\s+up)\b[^.?!]{0,40}"
    r"\b(?:sting\w*|bee|wasp|nut|nuts|peanut\w*|shellfish|food|medicine|antibiotic\w*|"
    r"prawn|egg|dairy|allerg\w*|throat|tongue|breath\w*|can'?t\s+swallow|epipen)\b",
    r"\b(?:sting\w*|bee|wasp|nut|peanut\w*|shellfish|food|antibiotic\w*|allerg\w*)\b"
    r"[^.?!]{0,40}\b(?:lips?|tongue|throat|face)\b[^.?!]{0,25}\b(?:swelling|swollen|swelled|"
    r"puff\w*|puffy)\b",
    r"\b(?:throat|tongue|uvula)\b[^.?!]{0,20}\b(?:swelling|swollen|closing|tight)\b",
    # "a tight throat" puts the word the other way round, and "i have a swollen lip and a tight
    # throat" is the anaphylaxis line with the tight throat after the comma.
    r"\b(?:tight|tightening)\s+throat\b",
)

LIPS_SWELL_BARE_OFF = (
    r"\b(?:cold\s+sore|chapped|chaps|dry\s+lips|chap\s?stick|lip\s+balm|piercing|"
    r"filler\w*|collagen|blister|ulcer|brace|braces|wisdom\s+tooth|gum|herpes|"
    r"bit\s+my\s+lip|bit\s+my\s+tongue|bite\s+my\s+lip|cut\s+my\s+lip|burnt\s+my\s+mouth|"
    r"hot\s+food|curry|chilli|hangover|dehydrated|kissed|kissing|numb)\b",
    r"\A(?![\s\S]*\b(?:faint\w*|dizz\w*|breath\w*|throat|tongue|wheez\w*|swallow\w*|"
    r"collaps\w*|vomit\w*|unconscious|itch\w*)\b)[\s\S]*"
    r"\b(?:yesterday|last\s+(?:night|week|month|year)|years?\s+ago|used\s+to|"
    r"always\s+(?:swells|does|goes)|as\s+a\s+(?:kid|child)|in\s+the\s+(?:cold|winter|sun)|"
    r"(?:from|because\s+of|after|with)\s+(?:the\s+)?(?:cold|wind|sun|weather|hayfever))\b",
    # The weather is said the other way round as well: "in the wind" is the same cold wind that
    # chaps a lip, and it was the ambulance because only "from ... wind" carried it. It is
    # scoped to the lips on purpose - a throat or a tongue swelling "in the wind" is still the
    # airway, and the weather should never excuse those.
    # ... and only when the weather is the whole of it: "my lips are swollen in the wind and i
    # feel faint" is an airway call with a weather word in it, so a line that names another
    # symptom anywhere never takes this reading.
    r"\A(?![\s\S]*\b(?:faint\w*|dizz\w*|breath\w*|throat|tongue|wheez\w*|swallow\w*|"
    r"collaps\w*|vomit\w*|unconscious|itch\w*|swollen\s+(?:shut|closed))\b)"
    r"[\s\S]*\blips?\b[^.?!]{0,25}\bin\s+(?:the\s+)?(?:cold|wind|sun|winter)\b",
    r"\A(?:if|when|what\s+if|should\s+i|would)\b",
    # A face swollen by crying is the most ordinary swelling there is, and main rang the ambulance
    # for it: "my face is swollen from crying", "my face is swollen from crying all night" and
    # "my lip is swollen after crying" all got "That is an ambulance". The crying has to be the
    # stated cause, so "my face is swelling and im crying" - a person frightened by the swelling
    # itself - keeps the card, and so does a throat, a tongue, a wheeze, a faint, a sting, an
    # itch or a swallow that is going. The guard is part of the same pattern as the crying it
    # stands beside: on its own it would match every line in the deck.
    r"\A(?![\s\S]*\b(?:throat|tongue|uvula|breath\w*|wheez\w*|swallow\w*|faint\w*|dizz\w*|collaps\w*|unconscious|sting\w*|stung|bee|wasp|hives|itch\w*|vomit\w*|reaction|allerg\w*|epipen|shut)\b)"
    r"[\s\S]*\b(?:face|eyes?|lips?)\b[^.?!]{0,30}\b(?:from|after|because\s+of|with)\s+(?:all\s+(?:the|that|my)\s+)?(?:crying|sobbing|a\s+good\s+cry)\b",
    # ...and the other way round, where the crying is the verb: "i cried so much my face is puffy".
    r"\A(?![\s\S]*\b(?:throat|tongue|uvula|breath\w*|wheez\w*|swallow\w*|faint\w*|dizz\w*|collaps\w*|unconscious|sting\w*|stung|bee|wasp|hives|itch\w*|vomit\w*|reaction|allerg\w*|epipen|shut)\b)"
    r"[\s\S]*\b(?:i\s+(?:have\s+|had\s+|was\s+|been\s+|just\s+)?(?:cried|crying|sobbed|sobbing)|(?:cried|crying|sobbing)\s+so\s+much)\b[^.?!]{0,30}\b(?:face|eyes?|lips?)\b[^.?!]{0,25}\b(?:puffy|puffed\s+up|swollen|swelling|swelled|blotchy|red)\b",
    r"\b(?:what|should)\s+(?:do\s+)?i\s+do\s+if\b",
)

# The first sign of the same reaction is usually said without "swelling" or "tight": a tingle, an
# itch or pins and needles in the lips, the mouth or the tongue, with the food, the sting or a
# reaction named. On its own the tingle is the cold, the curry, the kiss or the dentist.
LIPS_TINGLE = (
    r"\b(?:lips?|tongue|mouth|throat|face)\b[^.?!]{0,25}\b(?:tingl\w*|pins\s+and\s+needles|"
    r"itch\w*|prickl\w*|numb(?:ness|ed|ing|s)?)\b",
    r"\b(?:tingl\w*|pins\s+and\s+needles|itch\w*|prickl\w*|numb(?:ness|ed|ing|s)?)\b[^.?!]{0,25}"
    r"\b(?:lips?|tongue|mouth|throat|face)\b",
    # The throat's own way of saying the first sign, which is not "tight": "my throat feels funny"
    # after a sting is the same reaction, and it was getting the sting card ("scrape it out
    # sideways"). On its own, with no sting or food in the line, it stays the ordinary question.
    r"\bthroat\b[^.?!]{0,20}\b(?:feels?|is|going|getting)\s+(?:a\s+bit\s+|a\s+little\s+|"
    r"really\s+|very\s+|so\s+|properly\s+)?(?:funny|odd|weird|strange|thick|funny\s+feeling)\b",
)

# A sting that has already settled is not an airway closing: "a wasp stung me and i got dizzy and
# sat down, im fine now" is the person telling you it passed. The swelling and the breath still win
# over the settled words, because those are the danger whatever the person hopes.
STING_SETTLED = (
    r"\b(?:im|i'?m|i\s+am|its|it'?s|it\s+is|that'?s|thats)\s+(?:all\s+)?(?:fine|ok|okay|"
    r"better|gone|settled|passed|over|cleared\s+up)\s+now\b",
    r"\b(?:it|that)\s+(?:has\s+|'?s\s+|is\s+)?(?:passed|worn\s+off|gone\s+off|settled|"
    r"cleared\s+up)\b",
    r"\b(?:feel|feeling)\s+(?:fine|ok|okay|better)\s+now\b",
)

# What the person ate, which is the cause of a mouth tingle even when the tingle is the only symptom
# named: the list of foods cannot be complete, so the eating itself counts, and the dish after
# "after the" covers "my mouth is tingling after the sushi", which was "Thanks for telling me".
LIPS_TINGLE_FOOD = (
    r"\b(?:ate|eaten|eating|eats|swallowed)\b",
    r"\b(?:after|since)\s+(?:the\s+|my\s+|a\s+|that\s+)?(?:takeaway|take-?out|meal|dinner|"
    r"lunch|breakfast|snack|dessert|pudding|cake|sushi|curry|pizza|pasta|sandwich|salad|"
    r"noodles|rice|fish|chips|shellfish|prawns?|nuts?|peanut\w*|fruit|berries|strawberr\w*|"
    r"kiwi|mango|avocado|tomato|egg|eggs|milk|cheese|soy|bread|wheat|honey|wine|beer)\b",
)

# Swelling with it, a voice that changes, a faint or a wheeze is past the watch-and-wait.
LIPS_TINGLE_RED = (
    r"\b(?:swell\w*|swollen|puff(?:ed|y)?|bloat\w*)\b",
    r"\breaction\b", r"\bepipen\b", r"\banaphyla\w*\b",
    r"\b(?:faint\w*|dizzy|light\s?headed|giddy|collapse\w*|passing\s+out)\b",
    r"\b(?:breath\w*|wheez\w*|stridor|throat\s+(?:tight|closing))\b",
    r"\b(?:vomit\w*|throwing\s+up|sick)\b",
    # A tongue that has gone thick or heavy is the second sign, and it is said without the word
    # swelling: "my lips are tingling and my tongue feels thick" was "Thanks for telling me" on
    # main while the same line after a prawn had been was the ambulance.
    r"\b(?:thick|thickened|thickening|heavy|wooden|rubbery)\b[^.?!]{0,20}"
    r"\b(?:tongue|lips?)\b",
    r"\b(?:tongue|lips?)\b[^.?!]{0,20}\b(?:feels?|is|has\s+gone|has\s+got|going)\s+"
    r"(?:a\s+bit\s+|a\s+little\s+|really\s+|very\s+|so\s+|all\s+)?(?:thick|thickened|"
    r"thickening|heavy|wooden|rubbery)\b",
)

# The dentist, a panic attack and pins and needles in the hands as well as the mouth explain a
# tingle on their own, and they are the commonest tingles there are: a numb lip after a filling,
# and the mouth and fingers of someone over-breathing. A swelling, a throat that will not swallow
# or a breath that is wrong still keeps the card.
LIPS_TINGLE_OFF = (
    r"\b(?:dentist|dental|hygienist|filling|root\s+canal|tooth\s+out|wisdom\s+tooth|"
    r"injection|anaesthetic|anesthetic|numbing\s+gel|novocaine|lidocaine)\b",
    r"\b(?:panic|panicking|panic\s+attack|anxiety|anxious|hyperventilat\w*|over-?breath\w*|"
    r"breathing\s+too\s+fast|shaking|palpitations)\b",
    # A tingle in the hands and the feet is the over-breathing, but the same words reach across a
    # line with two places in it: "a bee stung my hand and my lips feel tingly" was stood down
    # because the hand was in the line, and the person got the sting card with nothing about the
    # airway. The limb only explains a tingle in the limb, so a mouth word between the two means it
    # does not.
    r"\b(?:hands?|fingers?|fingertips|feet|toes?|arms?|legs?)\b"
    r"(?:(?!\b(?:lips?|tongue|mouth|throat|face)\b)[^.?!]){0,30}"
    r"\b(?:tingl\w*|numb(?:ness|ed|ing|s)?|pins\s+and\s+needles|prickling)\b",
    r"\b(?:tingl\w*|numb(?:ness|ed|ing|s)?|pins\s+and\s+needles|prickling)\b"
    r"(?:(?!\b(?:lips?|tongue|mouth|throat|face)\b)[^.?!]){0,30}"
    r"\b(?:hands?|fingers?|fingertips|feet|toes?|arms?|legs?)\b",
    r"\b(?:cold\s+sore|cold\s+weather|in\s+the\s+cold|out\s+in\s+the\s+cold|wind|sunburn|"
    r"chapped|freezing|numb\s+with\s+the\s+cold)\b",
    r"\b(?:b12|vitamin\s+b12|deficien\w*|multiple\s+sclerosis|\bms\b|migraine|nerve\s+damage|"
    r"carpal|raynaud\w*)\b",
)

# The things that are not this arm at all: a tablet is the ordinary "i can't swallow pills", and a
# fish bone or a bit of food stuck in the throat is the bone card's line, which is the ambulance
# when the swallowing has gone (that arm sits later in the tuple, so this one has to stand aside).
SWALLOW_GONE_OFF = (
    r"\b(?:pills?|tablets?|capsules?|medicines?|medicine|supplements?|vitamins?)\b",
    # an idiom and an animal are the two ways this looks like the symptom without being it
    r"\b(?:pride|insult|my\s+words?|his\s+words?)\b",
    r"\b(?:dog|dogs|puppy|cat|cats|kitten|rabbit|hamster|guinea\s+pig|horse|pony|bird|parrot|"
    r"budgie|pet|pets)\b",
    r"\b(?:bone|fishbone|gristle|a\s+bit\s+of\s+(?:food|meat|steak|bread)|food)\b"
    r"[^.?!]{0,30}\b(?:stuck|sticking|caught|lodged|went\s+down\s+the\s+wrong)\b",
    r"\b(?:stuck|sticking|lodged|caught)\b[^.?!]{0,30}\b(?:throat|gullet|windpipe)\b",
    r"\b(?:fish\s*bone|bone)\b",
    r"\b(?:swallowed|gulped)\b",
)

SWALLOW_GONE_RED = (
    r"\b(?:drool\w*|dribbl\w*)\b",
    r"\b(?:lips?|tongue|throat|uvula|neck)\b[^.?!]{0,24}\b(?:swell\w*|swollen|closing|thick)\b",
    r"\b(?:swell\w*|swollen|puff\w*)\b[^.?!]{0,24}\b(?:lips?|tongue|throat|neck)\b",
    r"\b(?:muffled|no\s+voice|voice\s+(?:has\s+)?gone|lost\s+my\s+voice)\b",
    r"\b(?:my\s+(?:own\s+)?spit|saliva)\b",
)

# ...and the reasons it does that, which the GP question and the nerves answer already cover.
THROAT_TIGHT_CAUSE = (
    r"\b(?:nervous|anxious|anxiety|worried|interview|presentation|speech|exam|speaking\s+up)\b",
    # How people actually say a blocked nose: stuffy, bunged up, running, congestion, sinus. A
    # blocked nose makes the throat feel tight and it is not the airway (zippy-kangaroo).
    r"\b(?:blocked\s+nose|nose\s+is\s+blocked|stuffy|stuffed\s+up|bunged\s+up|bunged|"
    r"runny\s+nose|nose\s+(?:is\s+)?running|congest\w*|sinus\w*|hayfever|hay\s+fever|"
    r"allerg\w*)\b",
    # Reflux is worst lying down, so the time of day can be the only thing said.
    r"\b(?:in\s+the\s+morning|first\s+thing|when\s+i\s+wake\s+up|on\s+waking|at\s+night)\b",
    # Effort is the ordinary reason a throat feels tight: a run, a swim, a workout (zippy-kangaroo).
    r"\b(?:run|running|ran|jog\w*|exercise|workout|gym|swim\w*|cycl\w*|bike|cardio|"
    r"football|rugby|netball|hockey|squash|tennis|lifting|weights|sprinting|training)\b",
    r"\b(?:sore|croaky|hoarse|dry|scratchy)\s+throat\b",
    r"\b(?:singing|sang|shouted|shouting|talking\s+all\s+day|yesterday|last\s+night|"
    r"weeks?\s+ago|for\s+days|hayfever|hay\s+fever|allergies|post\s?nasal|reflux|"
    r"silent\s+reflux|tonsils?|tonsillitis|strep|cold|flu|covid)\b",
    r"\b(?:sometimes|occasionally|now\s+and\s+then)\b",
)

# Even a hedged throat is the airway when a part is swelling with it or the swallow or the breath
# has gone: "my lips are a bit swollen and my throat feels tight" stays the ambulance.
THROAT_TIGHT_EFFORT = (
    # Effort has to be said as effort: "my nose is running" is a cold, not a run.
    r"\b(?:when|while|after|during)\s+(?:i\s+|im\s+|i'?m\s+)?(?:run|running|jog\w*|exercis\w*|"
    r"workout|swim\w*|cycl\w*|train\w*|lift\w*|row\w*|climb\w*)\b",
    r"\b(?:after|during|in)\s+(?:a|the|my)\s+(?:run|jog|workout|swim|cycle|ride|game|match|class|"
    r"session|training|race)\b",
    r"\b(?:gym|swimming|cycling|cardio|football|rugby|netball|hockey|squash|tennis|aerobics|"
    r"spin\s+class|bike\s+ride|long\s+run|sprints?|weights|lifting|hiit)\b",
)

THROAT_TIGHT_RED = (
    r"\b(?:tongue|uvula)\b",
    r"\b(?:swell\w*|swollen|puff(?:ed|y)?|bloat\w*)\b[^.?!]{0,30}"
    r"\b(?:lips?|tongue|face|eyelids?|throat|uvula)\b",
    r"\b(?:lips?|face|eyelids?)\b[^.?!]{0,30}\b(?:swell\w*|swollen|puff(?:ed|y)?)\b",
    r"\b(?:can'?t|cannot|couldn'?t|hard\s+to|difficult\s+to|difficulty)\s+"
    r"(?:swallow|breathe|breath)\b",
    r"\b(?:breath\w*|wheez\w*|stridor|epipen|anaphyla\w*)\b",
    # A throat that is closing is the airway even when a blocked nose is offered as the reason.
    r"\bthroat\b[^.?!]{0,12}\b(?:is|feels?|'s|was)?\s*(?:closing|closed|shutting|clamped)\b",
    r"\b(?:closing|closed)\s+(?:up\s+)?my\s+throat\b",
    # A voice that has gone or changed, and lips or a tongue that tingle, are the airway too.
    r"\bvoic\w*\b[^.?!]{0,20}\b(?:gone|going|changed|changing|different|hoarse|raspy)\b",
    r"\b(?:lips?|tongue|mouth|face)\b[^.?!]{0,20}\b(?:tingl\w*|numb(?:ness|ed|ing|s)?|prickl\w*)\b",
    r"\b(?:peanuts?|nuts?|shellfish|prawns?|bee|wasp|sting\w*|stung|penicillin|antibiotic\w*)\b",
)

# Something that "bleeds" but is not a person: a pen, a steak, a radiator, a cherry.
NOT_A_WOUND_OFF = (
    # "hi, its still bleeding" is a follow-up: what "it" is lives in the conversation, so the
    # context-aware answer has it and this arm stands down (safety-402 and safety-784b in the deck).
    r"\bit\b",
    r"\b(?:pen|ink|printer|paint|brush|steak|meat|chicken|beef|lamb|sausage|burger|cake|"
    r"tomato|beetroot|cherry|berry|berries|fruit|juice|sauce|jam|dye|radiator|pipe|tap|boiler|"
    r"ceiling|mattress|wall|drain|nail\s+varnish)\b",
)

NOSE_RED = (
    r"\b(?:won'?t|wont|doesn'?t|doesnt|isn'?t|not)\s+stopp?(?:ed|ing)?\b",
    r"\bkeeps?\s+(?:on\s+)?bleeding\b", r"\bstill\s+bleeding\b",
    r"\b(?:half\s+an?\s+hour|an?\s+hour|hours|two\s+hours|twenty\s+minutes|20\s+minutes|"
    r"ten\s+minutes|10\s+minutes|fifteen\s+minutes|15\s+minutes)\b",
    r"\b(?:pale|grey|gray|dizzy|faint|fainted|fainting|clammy|sweaty|unconscious|shaking)\b",
    r"\b(?:blood\s+thinners?|warfarin|clopidogrel|apixaban|rivaroxaban|aspirin|heparin)\b",
    r"\b(?:after|from)\s+(?:a\s+|the\s+)?(?:bang|blow|knock|hit|bump|fall|punch|punching|"
    r"thump|smack)\b",
    r"\bhit\s+(?:my|his|her|their|the)\s+(?:head|face|nose)\b",
    r"\b(?:nose|nosebleed)\b.{0,25}\b(?:broken|fractured|crooked|out\s+of\s+place)\b",
)

MOUTH_BLEED_NOW = (
    r"\b(?:won'?t|wont|doesn'?t|doesnt)\s+stopp?(?:ed|ing)?\b",
    r"\bnot\s+stopp?ing\b", r"\bkeeps?\s+(?:on\s+)?bleeding\b",
    r"\bstill\s+bleeding\b", r"\bwon'?t\s+stop\s+bleeding\b",
    r"\bbleeding\s+(?:a\s+lot|badly|loads|everywhere)\b", r"\bbleeding\s+all\s+over\b",
    r"\bblood\s+in\s+(?:my|his|her|their)\s+mouth\b",
)

# The present-tense verbs a rewritten reply can hit: "if she also feel faint" needs the -s.
_THIRD = {"feel": "feels", "keep": "keeps", "seem": "seems", "get": "gets", "go": "goes",
          "need": "needs", "stop": "stops", "look": "looks", "come": "comes", "start": "starts",
          "do": "does", "have": "has", "are": "is", "were": "was", "aren't": "isn't",
          "weren't": "wasn't"}

# "im 34 weeks" is the way people actually write it; the prefix keeps "my baby is 6 weeks old"
# out, because that is a baby, not a pregnancy.
PREGNANCY_WORDS = (r"(?:pregnant|pregnancy|expecting\s+a\s+baby|weeks?\s+pregnant|baby\s+due|"
                   r"\d+\s+weeks?\s+(?:along|gone|in)|"
                   r"(?:^|\b)(?:i'?m|im|i\s+am|my\s+(?:wife|girlfriend|partner|fiancee|"
                   r"fianc\w+))(?:\s+is|\s+was)?\s+\d+\s+weeks?\b"
                   # "im 6 weeks into my new job" is a count of weeks, not a pregnancy.
                   r"(?!\s+(?:into|old|ago|in|since|on|of|back)\b))")

# What is not an appliance's own plug: a person's fingers, cutlery, a tool, or a small thing off the
# floor. The plug itself is not in this list, so "put the plug in the socket" stays ordinary.
SOCKET_OBJECT = (r"\b(?:fingers?|fingertips?|fork|forks|knife|knives|scissors|nails?|pins?|"
                 r"paper\s?clips?|screwdrivers?|hair\s?pins?|keys?|coins?|sticks?|pens?|"
                 r"pencils?|toys?|metal|wire|needles?|blades?|tools?|utensils?|spoons?|"
                 r"chopsticks?|tweezers|batter(?:y|ies)|earbuds?|bracelet|necklace)\b",)

# A shock that says what it came off, with the shock word people use: "i got a shock off the
# kettle" was covered, but "my son put a fork in the socket and got a shock" was not.
# What is not this: an adapter for a holiday, a socket that is loose or being replaced, and a story
# about a socket years ago. The tool in the socket is not in this list, because that is the fault.
SOCKET_THING_FINE = (
    r"\b(?:adapter|adaptors?|travel|holiday\s+home|abroad|in\s+(?:spain|france|greece|italy|"
    r"portugal|turkey|america|the\s+us)|type\s+[a-o]\b|voltage)",
    r"\b(?:loose|wobbly|cracked|broken|fallen\s+off|came\s+off|replac\w*|rewir\w*|"
    r"install\w*|fit\s+(?:a|the)\s+(?:new\s+)?socket|electrician|extends?\s+the\s+socket|"
    r"extension\s+lead|surge)",
    r"\b(?:years?\s+ago|last\s+(?:year|decade|century)|when\s+i\s+was\s+(?:a\s+)?(?:kid|"
    r"child|little|small|young)|as\s+a\s+(?:kid|child)|in\s+the\s+(?:19|20)\d\d)",
    r"\b(?:how\s+(?:does|do)\s+(?:a|the)\s+socket\s+work|wiring|wire|which\s+plug|"
    r"plug\s+on\s+a\s+(?:wire|cable|lead)|fuse\s+in\s+the\s+plug)\b",
)

# A person who is not breathing, is unconscious, has no pulse or has been pulled out cold beside a
# shock is a resuscitation, not a shock-and-check: the CPR and first-aid cards answer those, and the
# shock card's "111 the same day if it seems to have left nothing behind" must never reach them.
# The signs are spelled every way people type them, so this is a denylist of the signs rather than
# a list of the phrasings that were tested.
ELECTRIC_SHOCK_DOWN = (
    r"\b(?:not|isn'?t|isnt|is\s+not|wasn'?t|wasnt|was\s+not|stopped|stop|stops|won'?t|wont)"
    r"\s+(?:breathing|breath\w*)\b",
    r"\b(?:not|isn'?t|isnt|is\s+not)\s+(?:breathing|breath\w*)\b",
    r"\bno\s+(?:pulse|breath\w*|heartbeat)\b",
    r"\b(?:unconscious|unresponsive|knocked\s+out|passed\s+out|passing\s+out|out\s+cold|"
    r"collapsed|collaps\w*|in\s+a\s+heap|limp|floppy|blue\s+lips|going\s+blue)\b",
    r"\b(?:cpr|resuscitat\w*|revive\w*|recovery\s+position|defib\w*|heart\s+stopped)\b",
    r"\b(?:is|isnt|isn'?t)\s+not\s+responding\b|\bnot\s+responding\b",
)

# A shock of any kind said beside someone on the floor. "i got a shock and passed out" reached
# neither card: the shock case wants the word electric or "a shock from/off ...", so a bare "got a
# shock" is not it, and the collapse case wants "on the floor" or a named person, so a bare "i
# passed out" is not it either - the line got "How was it, overall?". The heart can go wrong hours
# after a shock, so losing consciousness beside one is an ambulance however well they feel now.
SHOCK_ANY = (
    r"\b(?:got|get|gets|getting|had|has|have|having|took|taken|suffered|given|gave|felt)\s+"
    r"(?:me\s+|him\s+|her\s+|them\s+)?(?:a\s+|an\s+|the\s+)?(?:\w+\s+){0,2}shock\b",
    r"\bshock(?:ed)?\b",
    r"\b(?:zapped|electrocut\w*)\b",
    # A live wire that put someone on the floor is the same call, and the line often says the wire
    # rather than the word shock.
    r"\blive\s+(?:wire|cable|rail|terminal)\b",
)

# A definition ask about the shock is the knowledge card, not the card: "what causes an electric
# shock" and "what is an electric shock" were answered with the holding line because the case above
# decided the next turn. Only the ask about the thing itself stands it down.
ELECTRIC_SHOCK_DEFINITION = (
    r"\b(?:what|why|how)\s+(?:is|are|causes?|caused|does|do|did)\b[^.?!]{0,30}\bshock\b",
    # "work" is the verb of the definition ("how does a shock work"), and "at work" is the place:
    # "i got a shock at work and passed out" is the accident, so the place spelling is kept out.
    r"\bshock\b[^.?!]{0,20}\b(?:(?<!at\s)(?<!from\s)(?<!of\s)work|works|happen|happens|"
    r"affect|affects|do\s+to|does\s+to|cause|causes)\b",
    r"\b(?:explain|definition\s+of|meaning\s+of)\b[^.?!]{0,25}\bshock\b",
)

# Blood in the poo and a poo that is black and tarry are a bleed nobody should sit on, and main
# answered both with "I'm listening". Black and tarry is the one that has been sitting in the gut
# bleeding, so it gets A&E today; a streak of red wants the same day too, but a word on the phone.
POO_BLOOD = (
    # A nappy is left out on purpose: a baby's nappy has its own answer, and a line about one
    # names the baby rather than the poo ("my baby is 6 weeks old and has blood in his nappy").
    r"\bblood\s+in\s+(?:my|his|her|their|the)\s+(?:poo|poo's|poop|stool|stools|shit|bowel\s+"
    r"movement|number\s+two|toilet|loo)\b",
    # The plainest way people type it: "i pooed blood".
    r"\b(?:pooed|pooped|crapped)\s+(?:out\s+)?(?:some\s+)?blood\b",
    r"\bblood\s+came\s+out\s+(?:when|after)\s+(?:i|he|she|they)\s+(?:pooed|pooped|went)\b",
    r"\b(?:poo|poop|stool|stools|shit|diarrhoea|diarrhea)\b[^.?!]{0,20}"
    r"\b(?:with|has|had|have|containing|covered\s+in)\b[^.?!]{0,10}\bblood\b",
    r"\bbloody\s+(?:poo|poop|stool|stools|shit|diarrhoea|diarrhea|bowel\s+movement)\b",
    r"\bred\s+blood\s+(?:in|on)\s+(?:the\s+)?(?:toilet|paper|loo|pan)\b",
    r"\b(?:when\s+i\s+wipe|when\s+he\s+wipes|when\s+she\s+wipes|after\s+i\s+wipe)\b"
    r"[^.?!]{0,25}\bblood\b",
)

POO_BLACK = (
    r"\b(?:poo|poop|stool|stools|shit|number\s+two)\b[^.?!]{0,20}\b(?:is|are|was|were|went|"
    r"has\s+gone|have\s+gone|looks?|looked|turned|come\s+out)\s+(?:all\s+)?(?:black|tarry|"
    r"tar-?like|like\s+tar|dark\s+(?:red|reddish))\b",
    r"\b(?:black|tarry)\s+(?:and\s+tarry\s+)?(?:poo|poop|stool|stools|shit|diarrhoea|"
    r"diarrhea)\b",
    r"\b(?:poo|poop|stool|stools|shit|bowel\s+movement)\b[^.?!]{0,30}\b(?:black|tarry|"
    r"tar-?like|like\s+tar)\b",
    r"\b(?:tarry|black)\s+(?:poo|poop|stool|stools|shit)\b",
    r"\b(?:melaena|melena)\b",
)

# Iron tablets, bismuth, black pudding and beetroot colour a poo without any bleeding, and a film
# or a story from years ago is not a body bleeding now.
POO_FINE = (
    r"\b(?:blood\s+sugar|blood\s+pressure|blood\s+test|blood\s+group|bloody\s+murder|"
    r"bloody\s+hell|blood\s+money)\b",
    r"\b(?:iron\s+(?:tablets?|pills?|supplements?|infusion)|ferrous|bismuth|pepto|charcoal\s+"
    r"tablets?|kaolin)\b",
    r"\b(?:black\s+pudding|black\s+beans?|black\s+currents?|blackberries|blueberries|"
    r"beetroot|beet\s+juice|licorice|liquorice|spinach|food\s+colouring)\b",
    r"\b(?:stool\s+test|test\s+kit|screening\s+kit|bowel\s+screening|fit\s+kit|"
    r"faecal\s+immunochemical|colonoscopy|endoscopy)\b",
    r"\b(?:years?\s+ago|decades?\s+ago|as\s+a\s+kid|when\s+i\s+was\s+(?:a\s+)?(?:kid|child|"
    r"little)|in\s+(?:a|the)\s+film|on\s+tv)\b",
    r"\b(?:my|the|our)\s+(?:dog|cat|puppy|kitten|rabbit|hamster|guinea\s+pig|horse|bird|"
    r"parrot|budgie|pet)s?\b",
)

# A bleed measured in weeks or months is the GP's appointment, not the same-day card: what to do
# about it depends on how long it has been going on.
STOOL_LONG = (
    r"\b(?:for\s+(?:a\s+|the\s+last\s+|about\s+a\s+|over\s+a\s+|nearly\s+a\s+)?(?:\d+\s+)?"
    r"(?:week|weeks|month|months|year|years))\b",
    r"\b(?:since\s+(?:i\s+was\s+\w+|christmas|last\s+year|the\s+summer)|years\s+now|"
    r"months\s+now|weeks\s+now|a\s+while\s+now|ages|all\s+my\s+life|on\s+and\s+off)\b",
)

# A twisted testicle has about six hours before it is lost, and the pain usually starts suddenly
# and wakes people, so the whole family of lines gets A&E today rather than a shrug.
TORSION = (
    r"\b(?:testicle|testicles|testis|ball|balls|ball\s+sack|ballsack|scrotum|scrotal|bollock|"
    r"bollocks|nad|nads|nuts)\b[^.?!]{0,30}\b(?:pain|painful|achy|ache|aching|sore|swollen|"
    r"swelling|tender|lump|twisted|hard|heavy|torsion|hurts?|hurting)\b",
    # It does not have to be named as a pain to be one: "my testicle woke me up in the night" is
    # the same sudden one, and the gate below only keeps it when the line says so.
    r"\b(?:testicle|testicles|testis|ball|balls|bollock|bollocks|scrotum|nad|nads)\b"
    r"[^.?!]{0,25}\b(?:woke|woken|wakes|waking)\b[^.?!]{0,15}\b(?:me|him|her|them)\b",
    r"\b(?:pain|ache|swelling|swollen|lump|tender|tenderness|hurt\w*)\b[^.?!]{0,20}\b(?:in|of|on|at)\s+"
    r"(?:my|his|her|their|one|the)\s+(?:testicle|testicles|ball|balls|ball\s+sack|scrotum|"
    r"bollock|side\s+of\s+the\s+scrotum)\b",
    r"\b(?:one|a)\s+(?:of\s+my\s+|of\s+his\s+|of\s+her\s+)?(?:ball|testicle|bollock)s?\b"
    r"[^.?!]{0,20}\b(?:bigger|swollen|sore|hurts?|aching|tender)\b",
    r"\b(?:testicle|testicles|testicular|testis|ball|balls|bollock)\b[^.?!]{0,25}"
    r"\b(?:torsion|twisted)\b",
    # And the twist named on its own, which main greeted with "Noted: you think you have testicular
    # torsion.": the shape has its own name and needs no other pain word to be the hospital.
    r"\btesticular\s+torsion\b",
    r"\btorsion\s+(?:in|of)\s+(?:the|my|his|her|their)\s+(?:testicle|ball)\b",
    # The same thing said adjective-first: "my husband has a sore swollen testicle".
    r"\b(?:sore|swollen|painful|tender|hard|twisted)\b[^.?!]{0,20}\b(?:testicle|testicles|"
    r"scrotum|bollock|ball|balls)\b",
)

# Itching, chafing, blue balls and the ache after a long ride are the ordinary ones, and a line
# about how to check them is a question rather than a scrotum in trouble.
TORSION_FINE = (
    r"\b(?:blue\s+balls|jock\s+itch|athletes?\s+foot|sweaty|itch\w*|chafe\w*|chafing|"
    r"shaving|shaved|wax\w*|trim\w*|razor|rash|dry\s+skin|fungal|thrush|spots?|pimples?)\b",
    r"\b(?:after|from)\s+(?:cycling|the\s+bike|a\s+bike\s+ride|a\s+long\s+ride|the\s+gym|"
    r"the\s+squat\s+rack|football|running|a\s+run|sex|the\s+marathon|riding)\b",
    r"\bwhen\s+(?:i|he|she|they)\s+(?:run|cycle|ride|train|lift|walk|swim)\b",
    r"\b(?:how\s+(?:do|should)\s+i\s+check|self\s+exam|check(?:ing)?\s+(?:them|it)\s+for|"
    r"testicular\s+cancer\s+(?:awareness|check|screening)|what\s+causes\s+testicular)\b",
)

# A lump, or one side bigger than the other, is the GP's fast-track referral rather than the
# few-hours A&E window: it is not a twist, and no pain word is needed to say so.
TESTIS_LUMP = (
    r"\b(?:lump|lumps|bump|bumps|hard\s+spot|pea-?sized)\b",
    r"\b(?:one|a)\s+(?:of\s+(?:my|his|her|their)\s+)?(?:ball|testicle|bollock)s?\b"
    r"[^.?!]{0,25}\b(?:bigger|larger|enlarged|different)\b",
    r"\b(?:bigger|larger|enlarged)\b[^.?!]{0,20}\b(?:than\s+the\s+other|ball|testicle)\b",
)

TORSION_ONSET = (
    r"\b(?:sudden\w*|all\s+of\s+a\s+sudden|out\s+of\s+nowhere|came\s+on|come\s+on|"
    r"started|start(?:s|ing)?|woke|woken|wakes|overnight|last\s+night|this\s+morning|"
    r"this\s+afternoon|an?\s+hour\s+ago|few\s+hours|just\s+now|right\s+now|now\s+(?:sore|swollen|"
    r"hurting|painful)|one\s+side|on\s+one\s+side|since\s+(?:this|"
    r"last)\s+(?:morning|night)|in\s+the\s+last\s+(?:hour|few\s+hours))\b",
)

# A nail or a piece of glass through a shoe is a puncture: it needs cleaning out and a tetanus
# check the same day even when the bleeding stops, because the hole closes over the dirt. A car
# tyre, a wall and a picture hook are the lookalikes, and a bite is the dog case's.
PUNCTURE = (
    r"\b(?:stepped|stood|trod|trodden)\b[^.?!]{0,20}\b(?:on|in)\b[^.?!]{0,20}"
    r"\b(?:a\s+|the\s+|some\s+)?\b(?:nail|screw|tack|needle|glass|barbed\s+wire|spike|thorn)\b",
    r"\b(?:nail|screw|tack|needle|spike|thorn|piece\s+of\s+glass)\b[^.?!]{0,25}"
    r"\b(?:through|into|in)\s+(?:my|his|her|their)\s+"
    r"(?:foot|shoe|boot|trainer|sock|hand|hand|palm|leg)\b",
    r"\b(?:nail|screw|needle)\s+(?:went|has\s+gone|gone)\s+(?:right\s+)?"
    r"(?:through|into)\s+(?:my|his|her|their)\b",
)

# The signs that turn "my baby fell off the bed" from a same-day check into an ambulance: they are
# the head-injury and sepsis red flags said about a baby, and the head answer owns them.
BABY_FELL_RED = (
    r"\b(?:sick|vomit\w*|threw\s+up|being\s+sick|sleepy|drowsy|floppy|limp|wont\s+wake|"
    r"won'?t\s+wake|unconscious|knocked\s+out|out\s+cold|blood|seizure|fitting|fit|"
    r"breathing\s+(?:funny|odd|strange)|not\s+breathing|gasping|turning\s+blue|"
    r"not\s+themselves|not\s+feeding|slept\s+(?:a\s+lot|for\s+ages|all\s+day|since)|"
    r"asleep|is\s+sleeping|fell\s+asleep|hard\s+to\s+wake|"
    r"sleeping\s+a\s+lot|off\s+their\s+food|not\s+waking\s+(?:up|properly))\b",
)

# A baby off a bed or a sofa is checked the same day however well they seem: a small head on a
# hard floor is the one knock that cannot be judged at home, and the next day is when the signs
# show. A grown adult off a sofa is ordinary, so the baby word has to be in the line.
BABY_FELL = (
    # The baby is the one who fell: the person word comes first, the surface last, and only a bed,
    # a sofa or something a baby is put on counts.
    r"\b(?:my|our|the)\s+(?:baby|infant|newborn|toddler|little\s+one|son|daughter|boy|girl|"
    r"child)\b[^.?!]{0,30}\b(?:fell|fallen|falling|rolled|dropped|tumbled|toppled)\b[^.?!]{0,15}"
    r"\b(?:off|from)\b[^.?!]{0,20}\b(?:bed|sofa|settee|couch|changing\s+table|table|chair|"
    r"highchair|pram|buggy|pushchair)\b",
    # The fall comes first and the baby is named after it.
    r"\b(?:fell|fallen|falling|rolled|dropped|tumbling|tumbled)\s+(?:off|from)\s+(?:the\s+|my\s+|a\s+)?"
    r"(?:bed|sofa|settee|couch|changing\s+table|highchair|pram|pushchair)\b"
    r"[^.?!]{0,30}\b(?:baby|infant|newborn|son|daughter|boy|girl|little\s+one)\b",
    # An age in weeks or months is a baby whatever name the family uses.
    r"\b(?:baby|infant|newborn|toddler|\d+\s*(?:months?|weeks?)\s+old)\b[^.?!]{0,40}"
    r"\b(?:fell|fallen|falling|rolled|dropped|tumbled|toppled)\b",
)

# A baby who has gone to sleep is not a baby who fell: "my baby fell asleep" and "the baby dropped
# off" matched the bare fall arm above, and "asleep" is one of the red flags, so the worst pair
# landed - a 999 card for bedtime. Going to sleep, in love, out for the count and off a dummy are
# all things a baby does on purpose.
BABY_FELL_OFF = (
    r"\bf(?:ell|alls?|alling)\s+(?:a\s+)?asleep\b",
    r"\b(?:dropp(?:ed|ing|s)|nod(?:ded|ding|s))\s+(?:off|to\s+sleep|asleep)\b",
    r"\b(?:went|gone|goes|going)\s+(?:off\s+)?to\s+sleep\b",
    r"\bfell\s+(?:in\s+love|out\s+(?:of|with)|over\s+(?:nothing|again|laughing))\b",
    r"\brolled\s+(?:over|onto\s+(?:his|her|their)\s+(?:front|tummy|back))\b",
    r"\bdropped\s+(?:his|her|their|the)\s+(?:dummy|comforter|toy|bottle|cup|spoon|muslin)\b",
)

# A sleep word on its own is bedtime, but the same sleep word after a fall from something is the
# head injury the red flags are looking for: "my baby fell off the bed and fell asleep" is 999.
BABY_FELL_SURFACE = (
    r"\b(?:fell|fallen|falling|rolled|dropped|tumbled|toppled)\s+(?:off|from)\s+"
    r"(?:the\s+|my\s+|a\s+|her\s+|his\s+)?(?:bed|sofa|settee|couch|changing\s+table|table|"
    r"chair|highchair|pram|buggy|pushchair|stairs|steps|ladder|wall|bike)\b",
    r"\b(?:bed|sofa|settee|couch|changing\s+table|highchair|pram|buggy|pushchair)\b[^.?!]{0,12}"
    r"\b(?:fell|fallen|falling|rolled|dropped|tumbled|toppled)\b",
)

# ...and the other way: the memory says when it happened. "my friend hung himself when we were
# kids" is a childhood, and it took the rescue script because a grandparent was the only old death
# the fence knew (purple-camel, #5545). A growing-up word and a year count the same way.
HANGED_LONG_AGO = (
    r"\bwhen\s+(?:i|we|he|she|they)\s+(?:were|was)\s+(?:kids?|children|child|teenagers?|"
    r"teen|teens|young|little|small|at\s+school)\b",
    r"\bwhen\s+(?:he|she|they|my\s+\w+)\s+was\s+(?:young|a\s+kid|a\s+child|little|small|"
    r"at\s+school)\b",
    r"\b(?:growing\s+up|as\s+a\s+(?:kid|child|teenager)|in\s+(?:my|his|her|their)\s+"
    r"(?:teens|twenties))\b",
    # "a long time ago" and "years back" are the same distance as "years ago", and where they
    # were at the time says it too: "she hung herself at university" is somebody's student years
    # (steward-spare-finch on #5545, who found six past lines still taking the rescue script).
    r"\b(?:years?|decades?)\s+(?:ago|back)\b",
    r"\b(?:a\s+)?(?:long|good\s+few|good)\s+(?:time|while|few\s+years?)\s+(?:ago|back)\b",
    r"\b(?:long|time)\s+ago\b",
    r"\bin\s+(?:19|20)\d\d\b",
    # "last term", "last spring", "last christmas": a school year and a season are dates too
    # (steward-spare-finch on #5545, who found `my daughter hanged herself at college last term`
    # and `my boy hung himself at school last spring` still taking the rescue script).
    r"\blast\s+(?:year|term|spring|summer|autumn|fall|winter|christmas|xmas|month|week|"
    r"night|new\s+year|easter)\b",
)

_STRUCK_RELATIVE = (r"(?:mum|mom|mother|dad|father|son|daughter|husband|wife|partner|boyfriend|"
                    r"girlfriend|brother|sister|friend|baby|child|kid|boy|girl|man|woman|lady|"
                    r"guy|bloke|neighbou?r|colleague|gran|granny|nan|grandad|grandma|grandpa|"
                    r"mate|passenger|cyclist|pedestrian|toddler|teenager|nephew|niece|cousin|"
                    r"aunt|uncle|fiance|fiancee|stepson|stepdaughter|stepdad|stepmum|person|"
                    r"people)")

# The person, not the vehicle, is holding somebody: "he trapped me in the car", "my partner pinned
# me in the car". The vehicle words are left out on purpose - "the car pinned me" is a crash.
TRAPPED_HELD_BY_A_PERSON = re.compile(
    r"\b(?:he|she|they|him|her|them|i|my\s+(?:husband|wife|partner|ex|boyfriend|girlfriend|dad|"
    r"mum|mom|father|mother|brother|sister|son|daughter|friend|mate|carer|uncle|aunt|cousin|nan|"
    r"gran|granny|grandad|grandma|grandpa|stepdad|stepmum|flatmate|housemate|neighbou?r)|"
    r"the\s+(?:man|woman|lady|guy|driver|bloke|father|mother))\b[^.?!]{0,20}\b(?:trapped|"
    r"pinned|locked|kept|keeps|holding|held|shut|stuck)\s+(?:me|us)\b")

# Not this call: a traffic jam is not a crash, a child seat is not a wreck, and being held in a car
# by a person is the abuse row's line rather than a collision.
TRAPPED_VEHICLE_NOT_NOW = (
    r"\bfor\s+(?:hours|ages|a\s+while|an\s+hour|\d+\s*(?:hours?|minutes?|mins?))\b",
    r"\btraffic\b", r"\bjam\b", r"\b(?:car|child|booster)\s+seat\b",
    r"\bbatter(?:y|ies)\b", r"\bflat\b", r"\bbreakdown\b", r"\bpetrol\b", r"\bdiesel\b",
    r"\bpuncture\b", r"\bcharged?\b", r"\bparking\b", r"\block(?:ed)?\s+out\b",
    # "i locked my keys in the car", "the phone is stuck in the car": a thing, not a person.
    r"\b(?:keys?|phone|mobile|wallet|purse|bag|handbag|teddy|dummy|toy|ball|money|cards?|"
    r"pram|buggy|medicines?|pills?)\b[^.?!]{0,25}\b(?:locked|trapped|stuck|shut|wedged)\b",
    r"\b(?:has|have|had|keeps?|kept|got)\s+(?:me|him|her|us|them)\s+"
    r"(?:trapped|stuck|pinned)\b",
    # A person who traps, pins or locks somebody into a car is the abuse row's line, and "keep
    # talking to them so they stay awake" cannot be said to the person describing it: see
    # TRAPPED_HELD_BY_A_PERSON below.
    r"\byesterday\b", r"\blast\s+night\b", r"\bago\b",
    r"\blast\s+(?:week|year|month|summer|winter)\b",
    r"\bwhen\s+i\s+was\s+(?:a\s+)?(?:kid|child|little|young|small)\b",
    r"\bwhat\s+if\b", r"\bif\s+(?:i|he|she|they|we|my\s+\w+)\b",
)

# What to say, one per case. Two sentences at most: the danger, then the real help.
# The two head-injury answers: one for the flags that mean now, one for a bang with none, each said
# to the user or about the person they named.
# The words people use for going down and coming back: a faint, a blackout, a collapse. The
# subject has to be a person, or "the shed collapsed last year" and "the bridge came down in 1999"
# get a medical answer instead of the ordinary one.
FAINT_STORY = (
    r"\b(?:i|he|she|they|we|my\s+" + PERSON + r"|the\s+" + PERSON + r"|" + PERSON + r")"
    r"\s+(?:\w+\s+){0,3}(?:fainted|fainting|faints|passed\s+out|passing\s+out|blacked\s+out|"
    r"blacking\s+out|collapsed|was\s+unconscious|were\s+unconscious|been\s+unconscious|"
    # "out cold" is the same faint said the way people say it. It is the one with two meanings -
    # a knock-out and a blackout - and OUT_COLD_KNOCKOUT is the knock-out half.
    r"(?:was|were|been|went)\s+out\s+cold|out\s+cold)\b",
    r"\b(?:had\s+)?(?:a\s+)?(?:funny\s+turn|blackout|fainting\s+fit)\b",
)

# A faint said as "out cold" is a faint, and it is the same advice every other faint gets: seen
# today rather than wait, because a first blackout is looked into whatever caused it. The child's
# version is the same call sooner, and the signs that mean an ambulance are the ones the other
# faint replies carry.
OUT_COLD_REPLY = (
    "Ring 111 today rather than waiting it out and say how long they were out and what they were "
    "doing - a first blackout is looked into every time, and a child is seen that day rather than "
    "this week. If they were out for more than a minute, went down during sport, hit their head, "
    "or have not come round, that is 999."
)

# The other "out cold", and the commoner one in a house with children: fast asleep. "i was out cold
# by nine", "the kids were out cold by eight", "my baby was out cold after her bottle" - a time, a
# bed, a feed or a journey after it is a person who has gone under for the night, not a blackout.
OUT_COLD_ASLEEP = (
    r"\bout\s+cold\b[^.?!]{0,20}\b(?:by|until|till|til|all\s+night|overnight|the\s+whole|"
    r"as\s+soon\s+as|bed|beds|bedtime|pillow|nap|naps|bottle|feed|sleep\w*)\b",
    r"\b(?:by|until|till|til|as\s+soon\s+as)\s+(?:\w+\s+){0,2}\bout\s+cold\b",
    r"\bout\s+cold\b[^.?!]{0,20}\b(?:after|before|from)\s+(?:the|a|his|her|my|their|our|that|"
    r"this)?\s*(?:run|walk|feed|bottle|shift|night\s+shift|work|meal|dinner|lunch|breakfast|"
    r"food|flight|drive|journey|day|game|match|film|movie|bath|swim|party|pub|wine|beer|drink\w*|"
    r"heat|exhaust\w*|jet\s?lag|gym|training|school|college|class|exercise|tiring\s+day|"
    r"long\s+day|night\s+out|night\s+in|table|sofa|exercise)\b",
)

WITHDRAWAL_STOP = (
    r"\b(?:stop(?:ped|ping)?|quit(?:ting)?|gave\s+up|giving\s+up|give\s+up|come\s+off|"
    r"coming\s+off|came\s+off|get\s+off|getting\s+off|got\s+off|off|detox\w*|withdraw\w*|"
    r"cut\s+down\s+on|cut\s+out|not\s+had\s+a\s+drink|havent\s+had\s+a\s+drink|"
    r"didn'?t\s+have\s+a\s+drink|without\s+a\s+drink|no\s+booze|no\s+alcohol|"
    r"dry\s+for|on\s+the\s+wagon)\b[^.?!]{0,30}"
    r"\b(?:drink\w*|alcohol|booze|beer|wine|vodka|whisky|whiskey|spirits?|pints?|lager|cider|"
    r"brandy|rum|gin|shots?)\b",
    # "i havent had a drink in 3 days" carries the drink inside the phrase, so it is its own arm.
    r"\b(?:havent|hasn'?t|hadn'?t|never)\s+had\s+(?:a\s+|any\s+)?(?:drink|alcohol|booze|"
    r"pint)\b",
    r"\b(?:no|zero)\s+(?:drinks?|alcohol|booze)\s+(?:for|in|since)\b",
    r"\b(?:drink\w*|alcohol|booze|beer|wine|vodka|whisky|whiskey)\b[^.?!]{0,30}"
    r"\b(?:withdraw\w*|detox\w*|dts?)\b",
)

# What a habit change is wrongly read as: the drink that was stopped is not alcohol, or the thing
# that was stopped is not a drink at all.
WITHDRAWAL_NOT_ALCOHOL = (
    r"\b(?:coffee|caffeine|tea|fizzy|juice|milk|water|squash|coke|cola|soda|lemonade|"
    r"energy\s+drinks?|sugar\w*|sweets|smok\w*|vap\w*|nicotine|fags?|cigs?|cigarettes?|"\
    r"rollies|weed|cannabis|drugs?|"
    r"painkillers?|screens?|tv|telly|gaming|gambl\w*|porn|shopping|meat|dairy|gluten|"
    r"phone|social\s+media|instagram|facebook|tiktok|doomscroll\w*)\b",
)

# A come-down done alone at home is the thing that kills people: there is nobody there when the fit
# or the confusion starts, so it gets the card before any sign is said.
WITHDRAWAL_ALONE_AT_HOME = (
    r"\b(?:detox\w*|coming\s+off|stopping|stopped|quitting|quit)\b[^.?!]{0,40}"
    r"\b(?:at\s+home|by\s+myself|on\s+my\s+own|alone|myself|on\s+his\s+own|on\s+her\s+own)\b"
    r"[^.?!]{0,40}\b(?:drink\w*|alcohol|booze|beer|wine|vodka|whisky|whiskey)\b",
    r"\b(?:detox\w*)\b[^.?!]{0,40}"
    r"\b(?:at\s+home|by\s+myself|on\s+my\s+own|alone|myself)\b",
)

# Dependence said as the day's routine rather than as a stop: the morning shake that a drink fixes,
# and the drink taken to stop the shaking. Both were the caffeine answer on main.
WITHDRAWAL_ROUTINE = (
    r"\bshak\w*\b[^.?!]{0,40}\b(?:until|when|if|before)\b[^.?!]{0,25}"
    r"\b(?:i|he|she)\s+(?:have|has|had|get|gets|got|need|needs)\s+(?:a|my|his|her)?\s*"
    r"(?:drink|beer|vodka|wine|gin|whisky|whiskey|pint)\b",
    r"\b(?:need|needs|have|has|had)\s+(?:a|my|his|her)\s+"
    r"(?:drink|beer|vodka|wine|gin|whisky|whiskey|pint)\b[^.?!]{0,30}"
    r"\b(?:to\s+)?(?:stop|stops|stopped|settle|ease)\s+(?:the\s+)?"
    r"(?:shak\w*|trembl\w*|shakes|nerves)\b",
    r"\bthe\s+shakes\s+(?:in\s+the\s+morning|every\s+morning|when\s+i\s+wake)\b",
    # the day's first drink as the thing that stops it: "i get the shakes if i dont drink by lunchtime"
    r"\bshak\w*\b[^.?!]{0,40}\b(?:if|when|unless)\b[^.?!]{0,25}"
    r"\b(?:i\s+)?(?:dont|don'?t|do\s+not|havent|haven'?t|miss|skip|go\s+without)\b"
    r"[^.?!]{0,20}\b(?:drink|drinks|beer|pint)\b",
)

# The body's side of it. Any one of these after a recent stop is the withdrawal, and the answer is
# the same for all of them.
WITHDRAWAL_SYMPTOM = (
    r"\bshak\w*", r"\bshaky\b", r"\btrembl\w*", r"\btremors?\b", r"\bsweat\w*",
    r"\bsweaty\b", r"\bclammy\b", r"\bnause\w*", r"\bvomit\w*", r"\bbeing\s+sick\b",
    r"\bthrowing\s+up\b", r"\bcan'?t\s+sleep\b", r"\bcant\s+sleep\b",
    r"\bnot\s+sleeping\b", r"\binsomnia\b", r"\bheart\s+(?:is\s+)?(?:racing|pounding)\b",
    r"\bpalpitations?\b", r"\banxious\b", r"\banxiety\b", r"\bjumpy\b", r"\bon\s+edge\b",
    r"\bnight\s+sweats?\b", r"\bfeel\w*\s+(?:awful|terrible|rough|dreadful|ill|horrible)\b",
    r"\bheadache\b", r"\bshiver\w*", r"\bcraving\w*",
    # The hallucination and the fit are severe signs, not ordinary ones: they live in
    # `WITHDRAWAL_HALLUCINATION` and `WITHDRAWAL_SEVERE`, where the innocent reading "i can taste
    # things again" can stand them down without also standing down the shakes.
)

# The symptoms that are the withdrawal itself rather than the things pregnancy, a missed meal and
# a bad week also do. A pregnant person who gave up the drink is told to give up the drink, so the
# sickness of early pregnancy must not be read as withdrawal: with a pregnancy in the line only
# these count.
WITHDRAWAL_STRONG = (
    r"\bshak\w*", r"\bshaky\b", r"\btrembl\w*", r"\btremors?\b", r"\bsweat\w*",
    r"\bsweaty\b", r"\bclammy\b", r"\bheart\s+(?:is\s+)?(?:racing|pounding)\b",
    r"\bpalpitations?\b", r"\bhallucinat\w*", r"\b(?:see|saw|seen|seeing)\s+things\b",
    r"\b(?:hear|heard|hearing)\s+(?:things|voices)\b", r"\bfits?\b", r"\bseizures?\b",
    r"\bdelirium\b", r"\bconfus\w*",
)

WITHDRAWAL_DANGER = (
    r"\bis\s+(?:that|it|this)\s+(?:dangerous|serious|bad|normal)\b",
    r"\bcan\s+(?:it|that|this)\s+(?:kill|be\s+dangerous|hurt\s+me)\b",
    r"\bwill\s+(?:i|he|she|they)\s+be\s+ok\b", r"\bshould\s+i\s+(?:worry|be\s+worried)\b",
    r"\bam\s*i\s+in\s+danger\b", r"\bwhy\s+(?:does|do)\b[^.?!]{0,20}\bshak\w*",
)

# "should i call 999 for alcohol withdrawal" asks the question the 111 in the card does not
# answer, so it gets the card that says what the ambulance is for.
WITHDRAWAL_ASK_DANGER = (
    r"\b(?:call|ring|phone|dial)\s+(?:an?\s+)?(?:999|911|112|ambulance|emergency)\b",
    r"\bshould\s+(?:i|we|he|she|they)\s+(?:call|ring|phone|worry|be\s+worried)\b",
    r"\bdo\s+(?:i|we)\s+need\s+(?:an?\s+)?ambulance\b",
    r"\b(?:can|could|will|would)\s+(?:i|you|he|she|they)\s+(?:die|be\s+in\s+danger)\b",
    r"\bis\s+(?:it|that|this)\s+(?:dangerous|serious|deadly|fatal)\b",
    r"\bis\b[^.?!]{0,30}\b(?:dangerous|deadly|fatal|life[-\s]?threatening)\b",
)

# Said a turn after the card, these are the step up rather than the same advice again.
# The drink offered as the medicine: "a beer to help me sleep", "a pint to stop the shakes",
# "hair of the dog". Only read after the card, where drinking again is the thing being asked about.
WITHDRAWAL_HAIR_OF_THE_DOG = (
    r"\b(?:a\s+)?(?:beer|pint|lager|glass\s+of\s+wine|wine|vodka|drink|drinks|stella|whisky)\b"
    r"[^.?!]{0,40}\b(?:help|helps|sleep|shake|shakes|shaking|stop|settle|ease|calm|take\s+the\s+edge)\b",
    r"\bhair\s+of\s+the\s+dog\b",
    r"\b(?:should|can|could|shall)\s+i\s+(?:have|drink|get)\s+(?:a|another|one)\b",
    r"\b(?:is\s+it\s+ok|is\s+it\s+alright|would\s+it\s+be\s+ok)\s+to\s+(?:have|drink)\b",
)

# The two words that say it with no symptom in the line at all.
WITHDRAWAL_NAMED = (
    r"\bwithdraw\w*", r"\bdetox\w*", r"\bdelirium\s+tremens\b", r"\bdts\b",
    # "im coming off alcohol" and "im off the booze three days now" name the state with no symptom
    # in the line, which is the point of saying it: the card is the caution for the stretch.
    r"\b(?:coming|come|came|getting|get|got|am|im|i'?m)\s+off\s+(?:the\s+|my\s+)?"
    r"(?:drink|booze|alcohol|wine|beer)\b",
)

# Seeing, hearing, tasting and smelling things are the same hallucination family and the same
# ambulance. They are their own tuple because the phrase has an innocent reading: "i can taste
# things again" is a sense coming back, not a hallucination.
WITHDRAWAL_HALLUCINATION = (
    r"\b(?:see|sees|saw|seen|seeing)\s+things\b",
    r"\b(?:hear|hears|heard|hearing)\s+(?:things|voices)\b", r"\bvoices\b",
    r"\b(?:taste|tastes|tasted|tasting)\s+things\b",
    r"\b(?:smell|smells|smelt|smelled|smelling)\s+things\b",
    # The sense named with the thing it reports, and the person saying it is not there: "i smell
    # burning that isnt there" is the olfactory hallucination and it was the units card.
    r"\b(?:see|sees|saw|seeing|hear|hears|heard|hearing|smell|smells|smelt|smelling|taste|"
    r"tastes|tasted|tasting)\b[^.?!]{0,25}\b(?:that|which)\s+"
    r"(?:isnt|isn'?t|is\s+not|wasnt|aren'?t|arent)\s+(?:really\s+)?there\b",
)

# The innocent readings: a sense that came back, and a way of looking at the day. Both were the
# delirium tremens card. The fence is narrow on purpose - "i can taste things and it is scaring
# me" is still severe, because only the phrase that says it is *fine* stands the card down.
WITHDRAWAL_SENSES_FINE = (
    r"\b(?:see|sees|seeing)\s+things\s+(?:differently|clearly|straight|in\s+a\s+different\s+way|"
    r"in\s+a\s+different\s+light|from\s+a\s+different\s+angle|more\s+clearly)\b",
    r"\b(?:taste|tastes|tasting|smell|smells|smelling)\s+things\s+(?:again|properly|at\s+last|now)\b",
    # "i can taste things" with nothing after it is food having a taste again, which is the first
    # good thing people notice. "and it is scaring me" is not that, so a follow-on clause keeps
    # the card.
    r"\bcan\s+(?:taste|smell)\s+things\b(?!\s*(?:and|but)\b)",
)

# A scorch mark is a mark to scrub off a worktop, and the same mark on a person is a burn:
# "i have a scorch mark on my arm" was the bicarbonate-of-soda answer for a pan.
# A singed fringe, eyebrow or eyelash is a haircut with a burn word in it: the burn row stands it
# down, and main answered `i singed my eyebrows` with "Noted: your eyebrows are singed" and a chat
# nod. Hair grows back, and the useful thing to say is which part is not hair - the skin under it.
# The word has to be hair and the verb has to be a scorch: `my hair caught fire` is a head on fire,
# which is the burn card and not a haircut.
HAIR_SCORCH = (
    r"\b(?:singe[ds]?|singeing|scorch(?:ed|es|ing)?|burnt|burned)\b[^.?!]{0,25}"
    r"\b(?:my|his|her|their|your)\s+(?:hair|fringe|bangs|eyebrows?|eyelashes|lashes|beard|"
    r"moustache|mustache)\b",
    r"\b(?:my|his|her|their|your)\s+(?:hair|fringe|bangs|eyebrows?|eyelashes|lashes|beard|"
    r"moustache|mustache)\b[^.?!]{0,20}"
    r"\b(?:is|are|got|was|were|looks?|keeps?)?\s*(?:singed|scorched|burnt|burned|crispy)\b",
)

HAIR_SCORCH_ANSWER = (
    "That is only hair, and hair grows back - trim the crunchy ends and it stops smelling. The part "
    "to check is the skin underneath: if the forehead, the eyelid or the scalp is red, blistered or "
    "sore, run it under cool water for twenty minutes and get it looked at today, because a burnt "
    "eyelid or brow can swell.",
    "Nothing to do about the hair itself except trim the crispy ends off - it grows back. Do look at "
    "the skin though: red, blistered or sore skin under a singed fringe or brow wants twenty minutes "
    "under cool water and a same-day check, since burnt skin near the eye swells.",
)

BURN_MARK_ON_A_BODY = (
    r"\b(?:burn|burns|burned|burnt|scorch|scorches|scorched|singe|singes|singed)\s+marks?\s+"
    r"(?:on|to)\s+(?:my|his|her|their|your)\s+(?:hand|hands|finger|fingers|thumb|arm|arms|"
    r"wrist|leg|legs|foot|feet|skin|face|chest|neck|shoulder|shoulders|back|thigh|tummy|belly)\b",
)

# A limp that is the *result* of a joint that gives way or rolls. The limp words match, but ice
# and rest are the wrong answer to an unstable knee or ankle: that line wants the ligament answer
# further down, so this row stands aside for it. simple-radio found it on `my knee gives way and i
# walk with a limp`, which was getting the knock-and-ice card. Only the words that have an owner
# are here: `locks` and `locks up` are a real mechanism, but no row answers a knee that locks, so
# standing aside for them trades a fair first-aid answer for nothing (modern-cap, on this PR).
LIMP_MECHANISM = (
    r"\bgiv(?:e|es|ing|en)\s+way\b",
    r"\bkeeps?\s+rolling\b",
    # "my ankle rolls and i walk with a limp" is the sprained-ankle answer's line, one word
    # away from the "keeps rolling" that is already here (alert-cat).
    r"\b(?:ankle|knee|foot|hip)s?\s+roll(?:s|ed)?\b",
    r"\broll(?:s|ed|ing)\s+(?:my|his|her|their|the)\s+(?:knee|ankle|shoulder|hip)\b",
    r"\bunstable\b",
    r"\b(?:knee|ankle|shoulder|hip|joint)s?\s+(?:is|feels?|has\s+been)\s+(?:giving\s+way|"
    r"giving\s+out|unstable|loose)\b",
)

# "my son has a limp wrist", "hes got a limp in his wrist": the word after "limp" says which limb
# it is, and it is not the leg. Leg first aid is the wrong card and skipping the row is worse (a
# bare "Got it"), so those lines get the limb-injury card the wrist already belongs to
# (polite-cord, steward-spare-finch and modern-cap, all on this PR).
LIMP_OTHER_LIMB = (
    r"\blimp\s+(?:wrist|wrists?|hands?|arms?|fingers?|thumbs?|elbows?|shoulders?)\b",
    r"\blimp\s+(?:in|on)\s+(?:his|her|my|their|the)\s+(?:wrist|wrists?|hands?|arms?|fingers?|"
    r"thumbs?|elbows?|shoulders?)\b",
    r"\b(?:wrist|wrists?|hands?|arms?|fingers?|thumbs?|elbows?|shoulders?)\s+(?:has\s+|have\s+)?"
    r"(?:gone\s+|all\s+)?limp\b",
)

# The same limp, but long-standing: a month of it is the GP's appointment rather than first aid.
LIMP_LONG = (
    # any span of weeks, typed as a digit or spelled out: "for 3 weeks" is the same long limp as
    # "for a month", and the digit was the one shape the first version of this row missed.
    r"\bfor\s+(?:the\s+(?:last|past)\s+)?(?:(?:[0-9]+|one|two|three|four|five|six|seven|eight|"
    r"nine|ten|eleven|twelve|a\s+couple(?:\s+of)?|a\s+few|few|several|many|over\s+a|"
    r"about\s+a|nearly\s+a|almost\s+a|half\s+a|a|an|the)\s+)?"
    r"(?:week|weeks|month|months|year|years|ages)\b",
    r"\bsince\s+(?:last|christmas|the\s+summer|a\s+\w+\s+ago|\d{4})\b",
    r"\b(?:weeks|months|years)\s+now\b",
)

# ..."somebody else has it", which is what the hip entry does not read. The first person stays
# out on purpose: it already has an answer above.
LIMP_SOMEBODY_ELSE = (
    r"\b(?:my|his|her|their|our)\s+(?:mum|mom|mother|dad|father|son|daughter|boy|girl|child|kid|"
    r"little\s+one|baby|nan|nana|gran|granny|grandma|grandad|grandpa|husband|wife|partner|"
    r"brother|sister|uncle|aunt|friend|neighbour|neighbor)\b",
    r"\b(?:he|she|they)\s+(?:has|have|had|got|is|was|were|walks|walk|limps|limp|hobbles|hobble)\b",
)

# The deadline is a finger swelling or tightening round the band, or already short of blood -
# blue, numb, cold, or the ring plainly cutting in. Whichever of those it is, the answer is the
# same in shape: get it off today, and A&E rather than a wait-and-see if it will not come off.
RING_DANGER = (r"\bswollen\b", r"\bswelling\b", r"\bswelled\b", r"\bswell\b",
               r"\btoo\s+tight\b", r"\bthrobbing\b", r"\bagony\b",
               r"\bcutting\s+(?:in|into)\b", r"\bcut\s+into\b",
               r"\b(?:gone|going|turned|turning)\s+blue\b", r"\bblue\b", r"\bpurple\b",
               r"\bnumb\b", r"\bblack\b")

# A ring nobody is wearing cannot be cutting anything off: "i dont wear a ring and my hand is
# swollen" is a swollen hand, and the answer it needs is the one for a swollen hand.
RING_NOT_WORN = (
    r"\b(?:don'?t|do\s+not|doesn'?t|didn'?t|never|not)\s+(?:wear|wearing|wore)\s+"
    r"(?:a\s+|any\s+|my\s+)?(?:ring|rings|jewellery|jewelry)\b",
    r"\bno\s+rings?\b", r"\bno\s+ring\s+on\b",
    r"\b(?:don'?t|do\s+not|doesn'?t)\s+(?:have|wear|got)\s+(?:a\s+|any\s+|my\s+)?rings?\s+on\b",
    r"\bwithout\s+(?:a\s+|my\s+|any\s+)?rings?\b",
    r"\b(?:took|take|taken|got|get|getting)\s+(?:my|the|her|his|their)\s+rings?\s+off\b",
    r"\b(?:my|the|her|his|their)\s+rings?\s+(?:is|was|are|were)?\s*(?:already\s+)?off\b",
    r"\b(?:ring|rings)\s+(?:is|are|was|were)\s+off\b",
    r"\bwhere\s+(?:my|the|her|his|their)\s+rings?\s+(?:normally|usually|used\s+to\s+be)\b",
)

HOW_TO_TREAT = (
    r"\b(?:how\s+(?:do|should|can)\s+(?:i|you|we)|what'?s\s+the\s+best\s+way\s+to)\b.{0,30}"
    r"\b(?:treat|care\s+for|clean|dress|look\s+after|soothe|deal\s+with)\b",
    r"\bwhat\s+(?:should|do|can)\s+(?:i|we)\s+do\s+(?:about|for|with)\b.{0,40}"
    r"\b(?:burn|scald|nosebleed|sprain\w*|splinter|bruise|graze|sunburn|twisted\s+ankle)\b",
    # "a cut" is a wound, but "a cut in the budget" or "a cut to my hours" is not
    r"\bwhat\s+(?:should|do|can)\s+(?:i|we)\s+do\s+(?:about|for|with)\s+(?:a|this|that|my|his|her)\s+"
    r"cut\b(?!\s+(?:in|to|from|of|price|budget|hours|pay|staff|spending)\b)",
    r"\b(?:treat|care\s+for|look\s+after)\b.{0,20}\b(?:a|an|my|the)\s+(?:burn|cut|scald|nosebleed|sprain|splinter|bruise|graze)\b",
)

# A question about your own hand is still the first aid: "what if i burn my hand on the oven" is
# how somebody asks before the chip pan goes on, and "what if i cut my foot on glass" is the
# question that stops the cut happening. The hypothetical only stands the minor reply down when
# the line is about somebody else or nobody in particular ("what if someone burns their hand"),
# and a story is a story whatever the words are.
OWN_INJURY_QUESTION = (
    # "what do you do if your child has a nosebleed" is the same question put to a friend, and it
    # was answered with "I can talk through everyday health - what's going on?".
    r"\bwhat\s+(?:if|do\s+(?:i|you)\s+do\s+(?:if|when)|should\s+i\s+do\s+(?:if|when)|happens\s+if)\b",
    r"\bhow\s+(?:do|should|can)\s+i\s+(?:treat|care\s+for|dress|clean|soothe)\b",
    r"\bwhat(?:'?s|\s+is)\s+the\s+(?:first\s+aid|best\s+way\s+to\s+treat)\b",
)

# A person the speaker looks after is not "somebody else": the speaker is the one who has to do
# the first aid, so the question is theirs. "what should i do if my child has a nosebleed" and
# "what if my child has a splinter" were shrugs, and "what should i do if my son burns his hand"
# was answered with a lump on the wrist, because a child on the line read as another person's
# accident. "what if someone" and a story still stand the card down.
OWN_INJURY_IN_MY_CARE = (
    r"\b(?:my|our|your)\s+(?:son|daughter|child|kid|kids|children|baby|babies|toddler|infant|"
    r"little\s+one|husband|wife|partner|boyfriend|girlfriend|mum|mom|mother|dad|father|"
    r"gran|granny|grandma|grandad|grandpa|nan|nana|niece|nephew|grandson|granddaughter)\b",
)

# A pan, a toast, a carpet or a shirt is what got burnt, not a person: "how do I clean a burnt pan"
# and "I burnt my toast" are kitchen questions, and the first-aid answer is the wrong one for them.
# The things that get burnt instead of people. Kept in one place so that the same word answers
# "I burnt my toast", "my toast got burnt" and "how do I stop burning my toast".
THING_BURNT_WORDS = (
    r"(?:onion|garlic|toast|bread|cake|biscuits?|"
    r"potatoes?|rice|pasta|sauce|soup|stew|curry|dinner|lunch|tea|food|meat|chicken|steak|fish|veg|"
    r"vegetables?|pizza|pan|pots?|saucepans?|wok|oven|grill|toaster|tray|tin|dish|baking|casserole|"
    r"bottom|base|crust|oil|butter|milk|sugar|carpet|shirt|iron|"
    r"cd|cds|dvd|dvds|disc|discs|disk|disks|candle|candles)"
)

THING_BURNT = (
    # "the burnt black bottom of my pan": a colour or a state between the burn and the thing
    r"\b(?:burnt|burned|scorched|charred|blackened|burning|burns?)\s+"
    r"(?:(?:my|the|our|a|an|his|her|their|your|some|black|brown|dark|sticky|thick|hard|"
    r"orange|crispy)\s+)*" + THING_BURNT_WORDS + r"\b",
    # "my toast got burnt": the thing first, then what happened to it. A word or two may sit
    # between them, because people write it that way: "my roasting tin has black burnt patches on
    # it" was a burn on a person to this pattern, and got twenty minutes under the cool tap.
    r"\b" + THING_BURNT_WORDS +
    r"\s+(?:(?:is|was|got|gets|looks|has|had|keeps\s+getting)\s+)?(?:\w+\s+){0,2}"
    r"(?:burnt|burned|scorched|charred)\b",
    r"\bburnt\s+(?:onto|on\s+to|to\s+the\s+bottom)\b",
    # "burnt on food off a pan": the burnt thing is stuck to a surface and the job is to get it
    # off. The "off" is what says so - "i got burnt on the oven door" has the same three words
    # and no "off", and keeps its first aid.
    r"\bburnt[\s-]*on\b[^.?!]{0,30}\boff\b",
    r"\b(?:stuck|stuck-on|stuck\s+on)\b[^.?!]{0,30}\bburn\w*\b",
    # "how do I get burnt off a baking tray", "how do I clean a burnt loaf tin", "burnt bits on
    # the tray": a tin, tray or shelf is what got burnt, with a word or two about it in between
    # (loaf, baking, bits, patches, food). _minor drops any line that names a body part, so "i
    # burnt my hand on the oven shelf" still gets the first aid.
    r"\b(?:burnt|burned|scorched|charred|blackened)\b(?:\s+\w+){0,3}\s+(?:tin|tins|trays?|pans?|"
    r"pots?|saucepans?|wok|dishes?|sheet|shelf|shelves|rack|mould|springform|traybake)\b",

    # "how do i burn my own cds": a disc is what gets burnt, so the burn is a job, not an injury.
    r"\bburn(?:ed|t|s|ing)?\s+(?:\w+\s+){0,2}"
    r"(?:cd|cds|dvd|dvds|disc|discs|disk|disks|candle|candles|incense)\b",
)

BURNT_SELF = (
    r"\b(?:burnt|burned|scalded)\s+(?:myself|me|himself|herself|themselves)\b",
    r"\b(?:i|he|she|they)\s+(?:was|were|got|am|is)\s+(?:burnt|burned|scalded)\b",
    # the noun, which the verb forms above miss: "i got a burn from the oven what should i do"
    # was answered as a burnt bake, because the oven is a thing this bot knows can burn
    r"\b(?:i|we|he|she|they)\s+(?:got|get|have|has|had)\s+(?:a|an|my|his|her|their|"
    r"me|some)?\s*(?:bad|nasty|little|nasty|small|sore|red)?\s*burn\b",
    r"\b(?:a|the)\s+(?:bad|nasty|little|small|sore|red)?\s*burn\s+(?:from|off)\b",
    r"\b(?:a|the)\s+(?:bad|nasty|little|small|sore|red)?\s*burn\s+"
    r"(?:on|to)\s+(?:my|his|her|their)\s+" + BURN_ON_BODY,
)

# A razor burn and a rope burn are friction and irritation, not heat, and "how do i stop razor burn
# on my neck" was getting the scalded-hand card: twenty minutes under cool running water and a loose
# cover, which is the first aid for a splash of boiling water. It is a false alarm in the other
# direction - an ordinary skin complaint answered as a burn - so the burn answers stand down and the
# shaving and rash answers get the line. The pattern puts the rubbing word next to the burn word, so
# "i burnt my neck on the curling tongs" and "i burnt myself shaving with hot wax" keep the burn.
RAZOR_BURN = (
    r"\b(?:razor\w*|sha(?:v|ve|ves|ved|ving)|shaving|shave|epilat\w+|wax(?:ed|ing)?|pluck\w*|"
    r"tweezers?)\b[^.?!]{0,25}\bburn\w*\b",
    r"\bburn\w*\b[^.?!]{0,25}\b(?:from|after|by|off)\s+(?:a\s+|the\s+|my\s+|her\s+|his\s+)?"
    r"(?:razor\w*|sha(?:v|ve|ves|ved|ving)|shaving|epilat\w+|wax(?:ed|ing)?)\b",
)

FRICTION_WORD = (
    r"\b(?:boots?|shoes?|trainers?|socks?|slippers?|sandals?|flip[\s-]?flops?|heels?|"
    r"rucksack|backpack|gloves?|rake|shovel|handle|rowing|oar|gym|running|runs|hiking|hike|"
    r"walking|walked|marathon|new\s+(?:boots?|shoes?|trainers?))\b",
    r"\b(?:from|by)\s+(?:the\s+)?(?:rubbing|friction)\b",
    r"\bblister\s+(?:plaster|pad|patch)\b",
    # A blister with no cause named is still a rubbing blister when the line asks what to do
    # with it or whether to pop it: "how do i treat a blister", "should i pop a blister", "can
    # i burst it". Those got twenty minutes under the cold tap, which is the advice for a burn
    # and the wrong thing for a rubbed heel. Heat still wins when the line names heat ("a
    # blister from the oven", "a burn blister"), because BURN_WORD is checked first.
    r"\b(?:pop|pops|popping|popped|burst|bursting|drain|draining)\b",
    r"\b(?:how\s+(?:do\s+i|to|should\s+i)|should\s+i|what\s+(?:should\s+i\s+do|do\s+i\s+do))"
    r"\s+(?:about|for|with)?\s*(?:treat|treating|deal\s+with|look\s+after|cover|dress|care)\b",
)

# A blister named on a body part, said as a state rather than a question: "my hand is blistered",
# "my arm is blistered", "i have a blister on my hand". With no heat in the line it is a rubbed
# blister, and it was reaching the scalded-hand card - twenty minutes under the cold tap is the
# wrong answer for it. Feet and heels are left out, because the shoe rows answer those already.
BLISTER_STATE = (
    r"\b(?:my|his|her|their)\s+(?:hand|hands|finger|fingers|thumb|thumbs|palm|palms|arm|arms|"
    r"wrist|wrists|leg|legs|thigh|thighs|shoulder|shoulders|back|neck|face|armpit)\b"
    r"[^.?!]{0,25}\bblister\w*\b",
    r"\b(?:i|he|she|they)\s+(?:have|has|got|ve\s+got)\s+(?:a|an|some|a\s+few)\s+"
    r"blister\w*\s+(?:on|across|under)\s+(?:my|his|her|their)\s+(?:hand|hands|finger|fingers|"
    r"thumb|palm|palms|arm|arms|wrist|writs|leg|legs|thigh|thighs|shoulder|shoulders|back|neck|"
    r"armpit)\b",
    r"\b(?:my|his|her|their)\s+(?:hand|hands|finger|fingers|thumb|palm|palms|arm|arms|wrist|"
    r"wrists|leg|legs|thigh|thighs|shoulder|shoulders|back|neck|armpit)\b[^.?!]{0,20}"
    r"\b(?:is|are|got|has|have|keeps?)\b[^.?!]{0,12}\bblister\w*\b",
)

# A blister with a cause that is not rubbing is a burn in the making: bleach, a chemical spray, a
# drain unblocker, the sun and nettles all want the same twenty minutes of cool water, and "cover
# it and stop whatever is rubbing it" is the opposite of the first aid for any of them. This is a
# stand-down from the plaster reply only; the burn row below answers those lines as it did before.
BLISTER_CAUSE_BURN = (
    r"\b(?:bleach\w*|chemical\w*|acid\w*|detergent\w*|clean(?:ing|ed|ers?)\b|"
    r"disinfectant\w*|degreaser\w*|drain\s+unblocker|caustic\w*|lye|ammonia|white\s+spirit|"
    r"paint\s+thinner|turpentine|paraffin|petrol|soda\s+crystals)\b",
    r"\b(?:sun\w*|uv\s+light|sunbed|sunlamp|nettles?|stinging\s+nettles?|hogweed)\b",
)

BLISTER_STATE_REPLIES = (
    "Leave it whole and cover it with a blister plaster or a clean non-fluffy dressing, and take "
    "the pressure off whatever rubbed it. Don't burst it: a blister that gets hot, spreading or "
    "weeping, or one you cannot keep off, should be seen.",
    "Leave it alone and cover it with a blister plaster, and stop whatever is rubbing it. Don't pop "
    "it; if it gets hot, red or weeping, or you are diabetic, get it looked at.",
)

# A how-long question is not a what-do-i-do question: "how long does a sprained ankle take to
# heal" was answered with the ice routine, which says nothing about the weeks, and
# "how long should i rest a sprained ankle" got sent to a pharmacist. Each entry in MINOR that
# has a healing clock gets one here, in the same (formal, plain) shape as the first aid.
HOW_LONG = (
    r"\bhow\s+long\b",
    r"\bhow\s+many\s+(?:days|weeks)\b",
    r"\bhow\s+long\s+(?:will|would|does|do|till|until|before|to)\b",
    r"\bwhen\s+(?:will|does|should)\s+it\s+(?:heal|be\s+(?:better|right|healed|back))\b",
    r"\btakes?\s+to\s+heal\b",
    r"\bhealing\s+time\b",
    r"\brecovery\s+time\b",
)

# The injury as it gets named in a how-long question, which is usually "a sprained ankle" or
# "a burn" rather than "my ankle": the first-aid patterns want a person in the line.
HEAL_WORDS = (
    # the injury has to be named as a sprain: "how long should i rest my knee" is a different
    # question with a different answer, and the bare joint word was taking it
    ("sprain", r"\bsprain\w*|\btwisted\s+(?:my|an?|the)\s+(?:ankle|knee|wrist)|"
               r"\b(?:rolled|went)\s+over\s+on\s+(?:my|an?|the)\s+ankle\b"),
    ("burn", r"\bburn(?:s|ed|t|ing)?\b|\bscald\w*"),
    ("cut", r"\bcuts?\b|\bgash\w*|\bgraz(?:e|ed|es)\b"),
    # a rubbed blister has a clock of its own, and without it "how long does a blister take to
    # heal" was answered with chickenpox, whose spots are also blisters
    ("blister", r"\bblisters?\b"),
)

INJURY_WORDS = (
    # The end of the word matters as much as the start. A bare "\bburn" is the start of "burner",
    # so "how do i clean the burner on my stove" was told to hold it under cool running water for
    # twenty minutes; a bare "\bcut" is the start of "cutlery", so "how do i clean rust off
    # cutlery" got the cut first aid. Each word now has to end where the word ends, with the
    # endings people actually type: burnt, burning, grazed, cuts, cutting.
    ("mouth_burn", (r"\btongue\b", r"\broof\s+of\s+(?:my|the)\s+mouth")),
    ("burn", (r"\bburn(?:s|t|ed|ing)?\b", r"\bscald(?:s|ed|ing)?\b",
              r"\bblister(?:s|ed|ing)?\b")),
    ("sunburn", (r"\bsun\s?burn(?:s|t|ed|ing)?\b",)),
    ("cut", (r"\bcut(?:s|ting)?\b", r"\bgraze(?:s|d|ing)?\b",
             r"\bscrape(?:s|d|ing)?\b", r"\bpaper\s+cuts?\b")),
    ("nosebleed", (r"\bnose\s*bleed",)),
    ("sprain", (r"\bsprain", r"\btwisted", r"\bankle\b", r"\bknee\b")),
    ("splinter", (r"\bsplinter",)),
)

# The injury words joined to the user's own body or self: "burn my hand", "cut my finger",
# "scalded myself", "my ankle is sprained". Only these make a conditioned question real.
OWN_INJURY = (
    r"\b(?:burn\w*|scald\w*|cut\w*|bled|bleeding|sprain\w*|fractur\w*|broke|broken|blister\w*|"
    r"spill\w*|spilt|pour\w*|tip\w*|knock\w*|dropped|splash\w*|threw)\b"
    r"[^.?!]{0,25}\b(?:my|me|myself|your|yourself)\b",
    r"\b(?:my|me|myself|your|yourself)\b[^.?!]{0,25}\b(?:burn\w*|scald\w*|cut\w*|bleed\w*|"
    r"sprain\w*|fractur\w*|broken|blister\w*)\b",
    # "what do i do if i get burnt": the person is the one who may be hurt, with no possessive.
    r"\b(?:i|we|you)\s+(?:get|got|gets|am|is|was)\s+(?:burnt|burned|scalded|blistered)\b",
    # "whats the first aid for a burn": the injury itself, asked about by name.
    r"\b(?:first\s+aid\s+for|treat|treating|soothe|do\s+for|good\s+for|best\s+(?:thing\s+)?for)"
    r"\b[^.?!]{0,15}\b(?:a|the|this)?\s*(?:bad\s+|red\s+|nasty\s+|serious\s+)?"
    r"(?:burn|scald)\b",
)

# The person being hurt is not the user: "what if my son burns his hand", "what if my husband
# scalds himself". Any of these words between the possessive and the injury makes the line about
# them, so a hypothetical stays hypothetical even though the words name a body part.
SOMEONE_ELSE_OWN = (
    r"\b(?:my|our|the|a)\s+(?:son|boys?|daughter|girl|child|kid|kids|baby|toddler|husband|wife|"
    r"partner|mum|mom|mother|dad|father|brother|sister|friend|mate|nana|nan|gran|grandma|"
    r"grandad|grandpa|neighbou?r|colleague|boss|flatmate|housemate|dog|cat|puppy|kitten)\b",
)

CLEANABLE_SURFACE = (r"\b(?:pans?|pots?|saucepans?|woks?|ovens?|grills?|hobs?|cookers?|rings?|"
                     r"trays?|tins?|dishes?|dish|baking|sheets?|plates?|bowls?|worktops?|"
                     r"sink|racks?|griddles?|barbecues?|bbqs?|burners?|casseroles?|toasters?|"
                     r"glasses?|glass|door)\b",)

PERSON_BURNT = (
    # "i got burnt on the oven door" is a person; "the oven door is burnt on" is grime. Only the
    # verbs a person does the burning with count, so a thing can be "burnt on" without being hurt.
    # "how do i get burnt grease off the oven" is the grime job, and "get" beside "burnt" read as a
    # person getting burnt, so the cleaning question kept the twenty minutes under the tap. A
    # person's "got burnt" is followed by where it happened or by nothing; a noun after it is the
    # stuff on the pan.
    r"\b(?:got|get|gets|getting)\s+(?:burnt|burned|scalded)\b"
    r"(?=\s*(?:$|[.,!?]|on\b|at\b|in\b|by\b|from\b|when\b|while\b|and\b|so\b|because\b))",
    r"\b(?:i|he|she|they|we)\s+(?:burnt|burned|scalded)\b",
)

# A minor injury is only minor while the person is otherwise well. "my son is limping and drowsy"
# is an unwell child who also limps, and the same hole was there for a burnt hand on a drowsy child,
# because a first-aid row matches its own word and never looks at the rest of the line. So a sign
# anywhere in the line outranks the injury word - but there are two kinds of sign, and they are
# answered differently.
#
# This first kind is the emergency on its own: the collapse, the fit, the breathing. Every minor
# row stands down and `urgent`'s ambulance script is the whole answer, because a person who cannot
# be woken needs the paramedics, not advice about their hand.
WHOLE_BODY_RED_FLAG = (
    r"\b(?:hard\s+to\s+wake|won'?t\s+wake|wont\s+wake|not\s+waking|floppy|"
    # A collapse is both ways round: "limp and floppy" and "limping and limp". The bare word
    # after "and" is the child going limp in the middle of a limp, and it was answered as the
    # gait alone - rest and ice - because only "limp and floppy" was read as the collapse. The
    # lookahead keeps "and limping": "limping and limping" is not a red flag, just a limp.
    r"and\s+limp\b(?!ing)|"
    r"limp\s+and\s+(?:floppy|blue))\b",
    r"\b(?:confused|confusion|disorientated|delirious|not\s+making\s+sense|unresponsive|"
    r"not\s+responding|vacant)\b",
    r"\b(?:seizure|seizures|convulsion|convulsions|fitting|having\s+a\s+fit|fitted)\b",
    r"\b(?:struggling\s+to\s+breathe|breathing\s+(?:fast|quickly|hard)|grunting|"
    r"blue\s+lips|grey\s+lips|gray\s+lips|lips\s+are\s+blue|clammy)\b",
    r"\b(?:stiff\s+neck|non[-\s]?blanching)\b",
)

# ...and this kind means "seen today, and 999 if it turns". The injury still needs its own answer:
# cooling a burn under running water is the thing that helps right now, and a reply that drops it
# for the escalation sends a person to hospital with the hand still hot. So the sign is said in the
# same breath as the first aid, and the words that send for the ambulance are in that sentence too.
MILD_BODY_SIGN = (
    r"\b(?:drowsy|drowsiness|sleepy|too\s+sleepy|listless)\b",
    r"\b(?:vomiting|vomited|throwing\s+up|thrown\s+up|projectile\s+vomit\w*)\b",
    r"\b(?:not\s+(?:himself|herself|themselves)|unlike\s+(?:him|her)self)\b",
    # ...and the other way a person says the same thing: a child who has stopped feeding, eating
    # or drinking, is off their food, or is "just not right". Main called the first two of these
    # 999, so the injury row has to keep an emergency in its answer rather than drop the line to
    # rest, ice and a day off it. The words are a person's, not a machine's: a boiler that is
    # "not right" and a foot that "doesn't feel right" are not this.
    r"\b(?:not\s+(?:feeding|feeding\s+well|eating|eating\s+much|drinking|drinking\s+much)|"
    r"off\s+(?:his|her|their)\s+(?:food|feeds|milk|bottles?)|"
    r"refusing\s+(?:feeds|food|bottles?|the\s+bottle))\b",
    r"\b(?:i|he|she|they|we|baby|child|son|daughter|kid|boy|girl|toddler|mum|mom|dad|mother|"
    r"father|nan|nana|grandad|grandma|husband|wife|partner|friend|sister|brother|niece|nephew)"
    r"\b[^.?!]{0,20}\b(?:not\s+right|not\s+(?:his|her|their)\s+usual\s+self)\b"
    r"(?!\s+(?:now|away|off|there|here|yet))",
)

# An ask about the injury itself, not a new line that happens to say "how long": the ask has to be
# about the healing or the care of the thing the last card answered.
ASKS_ABOUT_THE_INJURY = (
    r"\bhow\s+long\b", r"\bhow\s+many\s+(?:days|weeks)\b", r"\btakes?\s+to\s+heal\b",
    r"\bhealing\s+time\b", r"\brecovery\s+time\b", r"\bhow\s+(?:often|soon)\b",
    r"\bshould\s+i\s+(?:cover|bandage|dress|wrap|clean|wash|soak|pop|burst)\b",
    r"\b(?:do|should)\s+i\s+need\s+(?:a|to\s+see)\b",
    r"\bis\s+it\s+(?:meant|supposed)\s+to\b",
)

# The words a follow-up about the injury is made of, and nothing else: "how long will it take to
# heal", "should i cover it", "how many days till it is better". A line with any other word of its
# own ("how long does it take to fry chicken", "how long will the delivery take") names a subject
# of its own and is not asking about the injury, so it keeps the answer it had.
A_FOLLOW_UP_ABOUT_THE_INJURY = frozenset("""
how long will would does do did take takes taken heal heals healed healing time times day days week weeks
 till until til
many much soon often better right normal back recover recovered recovery
it that this these they them its theirs one
i my me should can could shall may might
a an the to be been being is are was were of about on in at for with and or then now not
cover covered covering bandage bandaged dressing dress wrapped wrap plaster plasters
clean cleaning wash washing soak soaking pop burst drain
need needs see seen looked look doctor nurse gp hospital a and e
sore red swollen painful blistering itchy scabby scab
properly fully completely still actually now then anyway please thanks
""".split())

# A question about how to do CPR is a question, not a scene: "how do i do cpr" with nobody on the
# floor wants 30 and 2, and it is the one answer nobody should have to search for. The line only
# counts as a question when it names the job or asks what to do with the push, so "how hard should
# i push at the gym" and "how fast should i run a 5k" stay ordinary.
CPR_HOWTO = (
    r"\bcpr\b", r"\bcompressions?\b", r"\brescue\s+breaths?\b", r"\bchest\s+compress\w*\b",
    r"\bhands[\s-]?only\b", r"\bhow\s+many\s+compressions\b", r"\bheart\s+massage\b",
    # "how fast should i push on the chest": the pushing and the chest together are the job, while
    # "chest pain" or "a chest infection" on its own is somebody's symptom and stays a scene.
    r"\bp(?:us|u)sh\w*\b[^.?!]{0,15}\bchest\b", r"\bchest\b[^.?!]{0,15}\bp(?:us|u)sh\w*\b",
    # "do i push hard", "how deep should i push", "am i pushing hard enough": the push and the
    # amount together, asked as a question. A flat "push hard" is not a question and is left to
    # whatever else follows it, so "my chest hurts when i push hard" keeps the chest answer.
    r"\b(?:how|do|does|should|shall|am|is|what)\b[^.?!]{0,20}\bp(?:us|u)sh\w*\b[^.?!]{0,12}"
    r"\b(?:hard|harder|fast|faster|deep|deeper|many|quickly|fast)\b",
    # "how deep should i push", "how hard should i push": the amount first, then the push.
    r"\bhow\s+(?:hard|harder|fast|deeper|deep|many|quickly|often)\b[^.?!]{0,20}"
    r"\bp(?:us|u)sh\w*\b",
    r"\bhow\s+(?:hard|fast|deep)\b[^.?!]{0,12}\bcompressions?\b",
)

# The room has to be empty for the how-to: the same words with somebody down are the scene below,
# and that answer starts with the call rather than with the numbers.
CPR_ROOM_EMPTY = (
    r"\bnot\s+breathing\b", r"\bstopped\s+breathing\b", r"\bisn'?t\s+breathing\b",
    r"\bunconscious\b", r"\bcollapsed\b", r"\bno\s+pulse\b", r"\bnot\s+waking\b",
    r"\b(?:gone|turning|going|is|are)\s+blue\b", r"\b(?:is|are)\s+(?:dead|dying)\b",
    r"\bchoking\b", r"\b(?:he|she|they|my\s+\w+)\s+(?:is|are|was)\s+(?:down|out)\b",
)

# Effort is not CPR: somebody asking how hard to push at the gym, on a run or at work is not in a
# room with a person who has stopped breathing.
CPR_NOT_EFFORT = (
    r"\b(?:gym|workout|rep|reps|sets?|weights?|lift\w*|sprint\w*|run|runs|running|jog\w*|"
    r"train\w*|cycl\w*|bike|swim\w*|row\w*|hike|walk\w*|stud\w*|revision|exam|business|"
    r"project|team|manager|career|pram|pushchair|wheelchair|trolley|barrow|mower|hoover|"
    r"vacuum|bike|car|van|drill|screw|nail|brush|paint\w*)\b",
    # An exercise named in the line is effort too, and it was the one shape missing: "how many
    # push ups should i do" and "how many push ups a day" were both read as "how many pushes"
    # and answered with 30 compressions and a 999 call. `p(?:us|u)sh` matches "push up" as
    # readily as "push hard", so a named rep - a press-up, a pull-up, a squat, a plank - has to
    # be said here rather than left to the gym words, which the line never says.
    r"\bp(?:us|u)sh[\s-]?ups?\b", r"\bpress[\s-]?ups?\b", r"\bpull[\s-]?ups?\b",
    r"\bchin[\s-]?ups?\b", r"\bsit[\s-]?ups?\b", r"\bsquats?\b", r"\blunges?\b",
    r"\bplanks?\b", r"\bcrunches?\b", r"\bburpees?\b", r"\bstar\s+jumps?\b",
)

CPR_WHEN_ALIVE = (
    "Not if they are breathing or have a pulse - compressions are for someone with neither. Put "
    "them in the recovery position, keep watching their breathing and ring 999 or 911 if you are "
    "worried; if they stop breathing normally, start CPR: 30 compressions, then 2 rescue breaths.",
    "Don't do compressions on someone who is breathing or has a pulse: roll them into the "
    "recovery position, stay with them and ring 999 or 911. If their breathing stops, it is 30 "
    "compressions and 2 rescue breaths, kept going until help arrives.",
)

CPR_NO_PULSE_NOW = (
    "Ring 999 or 911 now and start: no pulse and not breathing normally is CPR - 30 compressions "
    "in the centre of the chest, then 2 rescue breaths, kept going until the ambulance takes over.",
    "No pulse means CPR straight away, so ring 999 or 911 and start: 30 compressions, 2 rescue "
    "breaths, about 5-6 cm deep at 100-120 a minute, without stopping until help arrives.",
)

CPR_START = (
    "If they're not breathing normally, start now: 30 hard, fast compressions in the centre of "
    "the chest, then 2 rescue breaths, and keep going without stopping until the ambulance arrives.",
    "Yes - start now if they're not breathing normally, and stay on the line with the 999 or 911 "
    "call handler: 30 compressions in the centre of the chest, then 2 rescue breaths, without "
    "stopping until help takes over.",
)

CPR_HOW = (
    "Thirty compressions then two rescue breaths, about 5-6 cm deep in the centre of the chest at "
    "100-120 a minute, kept going until the ambulance arrives.",
    "Push hard and fast in the middle of the chest: 30 compressions, then 2 rescue breaths, about "
    "5-6 cm deep, letting the chest come all the way back up between pushes.",
)

# "should i stop when they arrive" is the last question people ask, and the answer is never "yes".
CPR_STOP = (
    r"\b(?:should|do|shall|can|when\s+(?:should|do|can))\s+(?:i|we)\s+stop\b",
    r"\bstop\s+(?:when|once|as\s+soon\s+as)\b.{0,30}\b(?:ambulance|paramedics?|crew|help|"
    r"arrive|arrives|come|comes)\b",
    r"\bhow\s+long\s+(?:do|should)\s+(?:i|we)\s+(?:keep|carry)\b", r"\buntil\s+when\b",
    r"\bwhen\s+(?:do|should)\s+(?:i|we)\s+(?:stop|give\s+up)\b",
)

CPR_STOP_REPLY = (
    "Keep going until the ambulance crew take over from you - they will tell you when to stop. If "
    "you are too exhausted to carry on, say so on the call and they will talk you through it.",
    "Don't stop until the crew take over, even if they seem to come round: keep the compressions "
    "going and let the paramedics decide.",
)

CPR_CHILD = (
    r"\b(?:child|children|kid|kids|toddler|toddlers|premature|school\s?age\w*)\b",
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|[1-9]|1[0-2])\s*"
    r"(?:year|yr)s?\s*old\b", r"\blittle\s+one\b",
    # "my son is 4 and isn't breathing" is a child and not a baby.
    r"\b(?:son|daughter|boy|girl|grandson|granddaughter|nephew|niece)\b[^.?!]{0,12}"
    r"\b(?:is|aged|of)\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"[1-9]|1[0-2])\b",
)

CPR_HOW_BABY = (
    "A baby gets five rescue breaths first - your mouth over their mouth and nose, small puffs - "
    "then 15 compressions with two fingers in the middle of the chest, about a third of the depth, "
    "and keep going 15 to 2. Ring 999 or 911 now and say it is a baby.",
    "For a baby: five small rescue breaths, then 15 compressions with two fingers in the centre of "
    "the chest, about a third of the depth, then two more breaths - and keep cycling. Ring 999 or "
    "911 now and tell them the baby's age.",
)

CPR_HOW_CHILD = (
    "A child gets five rescue breaths first, then 15 compressions with the heel of one hand (two "
    "for a bigger child) in the middle of the chest, about a third of the depth, and keep going 15 "
    "to 2. Ring 999 or 911 now.",
    "For a child: five rescue breaths, then 15 compressions with the heel of one hand in the "
    "centre of the chest, about a third of the depth, then two breaths, and keep cycling. Ring 999 "
    "or 911 now.",
)

CPR_BABY_SCENE = (
    "That's CPR now for a baby: ring 999 or 911 on speaker, give five small rescue breaths - your "
    "mouth over their mouth and nose - then 15 compressions with two fingers in the middle of the "
    "chest to about a third of the depth. Keep going 15 to 2 until help takes over.",
    "Ring 999 or 911 now and start for a baby: five rescue breaths, then 15 compressions with two "
    "fingers in the centre of the chest, and keep cycling 15 to 2 until the ambulance arrives.",
)

CPR_CHILD_SCENE = (
    "That's CPR now for a child: ring 999 or 911 on speaker, give five rescue breaths, then 15 "
    "compressions with the heel of one hand in the middle of the chest to about a third of the "
    "depth, and keep going 15 to 2 until help takes over.",
    "Ring 999 or 911 now and start: five rescue breaths, then 15 compressions with the heel of one "
    "hand, and keep cycling 15 to 2 until the ambulance arrives.",
)

CPR_ROUGH = (
    "Hard and fast is right: about 5-6 cm deep in the centre of the chest. If a rib gives, keep "
    "going - cracked ribs heal, and stopping is the bigger danger.",
    "Deep and fast is what's needed, so don't ease off. If ribs crack, carry on; only stop when "
    "help takes over or you are too exhausted to continue.",
)

CALL_HELP_REPLY = (
    "Yes - ring 999 or 911 now if you haven't already, say what you've seen and stay on the line "
    "until the call handler tells you what to do.",
    "If you haven't already, yes: ring 999 or 911 and describe exactly what's happening. Stay on "
    "the line - the call handler can talk you through the next step.",
)

ASPIRIN_REPLY = (
    "If they're not allergic to it, give one 300mg aspirin to chew while you wait, and tell the 999 "
    "call handler you have. If they're allergic, or the handler says no, don't.",
    "Chewed aspirin helps if it isn't going to be a problem for them: one 300mg tablet, then say on "
    "the call that you've given it. Skip it if they're allergic or the call handler says not to.",
)

WHEN_HELP_COMES = (
    r"\bhow\s+long\b.{0,40}\b(?:ambulance|paramedics?|fire|police|help)\b",
    r"\bwhen\s+(?:will|are|do)\b.{0,40}\b(?:ambulance|paramedics?|fire\s+(?:brigade|service)|"
    r"police|they)\b.{0,20}\b(?:coming|get|here|arrive)\b",
    r"\bare\s+they\s+(?:coming|on\s+their\s+way)\b",
)

WHEN_HELP_REPLY = (
    "They're usually with you within minutes for something like this: keep the door unlocked, the "
    "phone on speaker, and let the crew straight in when they knock.",
    "They are usually there quickly for something like this: leave the door unlocked and the phone "
    "on speaker, and the crew will knock and come in.",
)

# "fitting in with the new baby" and "a fitting for the shelf" are not fits: the word alone is
# never enough.
FITTING_IN = (
    r"\bfitting\s+(?:in|into|with|up|together)\b", r"\ba\s+fitting\b",
    # "fitting nicely" with no "in" is the same adjective: a child settling in at nursery or a
    # game coming together, and `my son is fitting nicely` rang the seizure line. It is read by
    # _a_settling_fit() rather than here, because the manner word has to be all there is.
    # "a fitting for the pipe" is a part; "fitting for the first time" is a first fit.
    r"\bfittings?\s+for\b(?!\s+(?:the\s+)?(?:first|last|second|third|final|an?\s+\w+\s+time|"
    r"hours?|days?|weeks?|months?|a\s+while|ages))",
)

FITTING_MANNER_TAIL = re.compile(
    r"\s*(?:(?:today|yesterday|lately|recently|nowadays)\b.*"
    r"|(?:at|in|into|with)\s+(?:the\s+|his\s+|her\s+|their\s+|our\s+|a\s+)?(?:new\s+)?"
    r"(?:nursery|preschool|playgroup|school|class|clubs?|teams?|groups?|other\s+kids|"
    r"the\s+others)\b.*)?$")

FRIGHTENED = (
    r"\b(?:can\s+you\s+hear\s+me|are\s+you\s+(?:still\s+)?there|you\s+still\s+there)\b",
    r"\bi'?m\s+(?:(?:really|so|very|that|proper|properly|absolutely|still|dead|scared\s+witless)\s+)*"
    r"(?:scared|frightened|terrified|panicking|shaking|bricking\s+it)\b",
    r"\bi\s+can'?t\s+stop\s+shaking\b",
    # "i'm scared i'm going to lose him" is the same fear in more words, and it is not a request
    # for the scene's next step, so it gets the steady answer rather than the waiting one.
    r"\b(?:going\s+to|gonna|might|may|could)\s+lose\s+(?:him|her|them)\b",
    r"\b(?:he|she|they)\s+(?:(?:might|may|could)\s+(?:not\s+)?(?:make\s+it|die|survive)|"
    r"(?:is|are)\s+going\s+to\s+die)\b",
    r"\b(?:will|is)\s+(?:he|she|they)\s+(?:going\s+to\s+)?be\s+(?:ok|okay|alright|fine)\b",
    r"\b(?:am|did)\s+i\s+do(?:ing)?\s+(?:it|this)?\s*right\b",
)

FRIGHTENED_REPLY = (
    "I'm here. You're doing the right thing by staying with them: keep the 999 or 911 call handler "
    "on speaker, say out loud what you can see, and keep talking to them until the ambulance comes.",
    "That's a frightening thing to be in the middle of. Keep the call handler on speaker, tell the "
    "handler everything you notice, and stay with the person until the ambulance arrives.",
)

# Fear is the one follow-up in an abuse thread that the scene replies fit worst: the person is not
# in the middle of an ambulance, they are frightened of somebody who has already hurt them. What
# helps is the next small step - a door that shuts, a phone charged, a neighbour's knock - and the
# number if the person comes back. Nothing here asks them to stay, leave or say anything to the
# person, because none of that is a decision for a frightened minute.
# The fear in an abuse thread is said in more words than the scene's fear is - "i am scared", "i
# keep shaking", "my hands keep shaking", "i am terrified" - and the scene's own pattern does not
# read them, so the composer answered them. This is the same list with the forms people type.
ABUSE_SCARED = FRIGHTENED + (
    r"\bi(?:'?m|\s+am)\s+(?:(?:really|so|very|that|proper|properly|absolutely|still|dead)\s+)*"
    r"(?:scared|frightened|terrified|panicking|shaking|shook|bricking\s+it)\b",
    r"\bi\s+keep\s+(?:shaking|trembling)\b",
    r"\bmy\s+hands?\s+(?:keep\s+|won'?t\s+stop\s+|cant\s+stop\s+)?shak(?:e|es|ing)\b",
    r"\bi\s+(?:feel|get)\s+(?:scared|frightened|terrified)\b",
    r"\b(?:i'?m|i\s+am)\s+(?:scared|frightened|terrified)\s+(?:of|about)\s+(?:him|her|them)\b",
)

ABUSE_SCARED_REPLY = (
    "That fear is worth trusting rather than pushing down: get somewhere you can shut a door, keep "
    "your phone charged and with you, and ring 999 or 911 if they come back.",
    "You don't have to sit with that on your own tonight - is there a neighbour or a friend whose "
    "door you could knock on? 999 or 911 if they come back, or if it gets worse before then.",
    "Being frightened is reason enough to get out of the room: phone and keys with you, go to "
    "someone you trust, and ring 999 or 911 if they try to stop you leaving.",
    "That is a frightening way to live, and you are not overreacting. Have a bag by the door, keep "
    "somewhere to go in mind tonight, and ring 999 or 911 the moment you feel he might start again.",
)

# Additions after an escalation, in the words people use: when it started, how long ago, who is
# with them. Not a question, so there is nothing to look up, and the person is still waiting.
DETAIL_AFTER_ESCALATION = (
    r"\b(?:it|this|he|she|they)\s+(?:started|began|happened|came\s+on|kicked\s+off)\b",
    r"\b(?:this\s+morning|this\s+afternoon|this\s+evening|earlier\s+today|yesterday|"
    r"last\s+night|an\s+hour\s+ago|\d+\s+(?:minutes?|hours?|days?)\s+ago)\b",
    r"\bsince\s+(?:this\s+morning|yesterday|last\s+night|about\s+\d)\b",
)

# A plan said on its own, after the crisis card: none of these carries a harm word, so the line is
# read as the crisis only because the thread is already one. "i have a plan" and "ive got a plan
# and the pills ready" are the same shape as the plan words the cut-off guard already knows, said
# without a cut, which is why they were left to the fallback.
HELD_CRISIS_DETAIL = CRISIS_PLAN_SAID + (
    r"\b(?:have|has|got|made|make|worked\s+out|thought\s+of|thought\s+about|picked|chosen)\s+"
    r"(?:a|the|my|one)\s+plan\b",
    r"\bthe\s+plan\s+is\s+(?:ready|set|made|done)\b",
    r"\b(?:wrote|written|writing)\s+(?:a|the|my)\s+(?:notes?|letters?)\b",
    r"\bi'?ve\s+(?:written\s+it|got\s+it)\s+down\b",
    # the means, named or ready
    r"\b(?:got|have|bought|saved|sorted)\s+(?:the|a|some)\s+(?:pills|tablets|meds|medicine|"
    r"painkillers|rope|noose|razor\w*|blades?|gun|knife|paracetamol)\b",
    r"\b(?:the\s+)?(?:pills|tablets|rope|noose|razors?|blades?)\s+(?:are|is)\s+"
    r"(?:ready|sorted|nearby|in\s+my\s+\w+)\b",
    # a date or a time
    r"\b(?:picked|chosen|set|know|got)\s+(?:a|the|my)\s+(?:date|day|time)\b",
    r"\bi\s+know\s+(?:when|where|how\s+much)\b",
    r"\bi\s+know\s+which\s+(?:place|spot|bridge|building|roof|window|tree|way\s+out|road)\b",
    r"\bhow\s+long\s+(?:till|until|before)\s+(?:that|then|it)\b",
    r"\bhow\s+long\s+(?:do|have|would)\s+i\s+(?:have|got)\b",
    r"\bwhen\s+(?:everyone'?s|everybody'?s|they'?re)\s+(?:asleep|gone|out|away)\b",
    r"\bi'?m\s+(?:going|gonna)\s+to\s+(?:do\s+it|go\s+through\s+with\s+it)\b",
    r"\bi'?ll\s+(?:do\s+it|go\s+through\s+with\s+it)\b",
    # Somebody coming to be with them is the answer to the card, not a change of subject: "my
    # sister says she can come over tonight" was the hospital-visit card ("Yes, go up. A short
    # visit tonight is worth more than a long one next week"). Nothing is wrong with the visit;
    # it is the wrong paragraph for the thread. This is the case the safety lane already had a
    # failing test for (tests.test_safety, test_a_crisis_thread_keeps_its_own_continuation).
    r"\b(?:my|a)\s+(?:sister|brother|friend|mum|mom|dad|mother|father|partner|wife|husband|"
    r"neighbour|neighbor|daughter|son|cousin|mate|flatmate|housemate|carer)\b[^.?!]{0,40}"
    r"\b(?:coming|comes|come|coming\s+over|on\s+(?:her|his|their)\s+way|is\s+with\s+me|"
    r"here\s+(?:tonight|now|with\s+me)|staying|made\s+it|got\s+here)\b",
    r"\b(?:im|i'?m)\s+not\s+on\s+my\s+own\b",
    r"\b(?:someone|somebody)\s+is\s+with\s+me\b",
    # The note or the means, said by where it is: "i put the note in my drawer", "ive hidden the
    # note", "ive filled the bottle". The thing is not being written any more, it is ready and
    # waiting, which is what makes it a plan. What is put away, though, can be an errand - "i put
    # the note about the rent on the table" - so CRISIS_PLAN_ORDINARY stands those down, and the
    # tablets in a cupboard are nobody's plan, but "the tablets are in my cupboard" says they are
    # ready and waiting, which is, so the shape above reads that and the errand words stand down
    # the rest: pills count in a pocket, a bag, a coat, and when the line says they are in place.
    r"\b(?:put|placed|hid|hidden|hide|kept|left|stashed)\b[^.?!]{0,24}"
    r"\b(?:notes?|letters?|razors?|blades?|rope|noose|gun)\b[^.?!]{0,20}"
    r"\b(?:in|on|under|behind|inside)\s+(?:my|the|a)\b",
    r"\b(?:pills|tablets|meds|bottle)\b[^.?!]{0,18}\b(?:in|on|under|behind|inside)\s+"
    r"(?:my|the)\s+(?:pocket|bag|handbag|rucksack|coat|jacket|sock|shoe|locker|desk|bedside|"
    r"drawer)\b",
    r"\b(?:hid|hidden|stashed)\b[^.?!]{0,20}\b(?:notes?|letters?|razors?|blades?|rope|noose)\b",
    # A move says where the thing now is: "i moved the tablets to the shed", "i moved the note".
    r"\b(?:moved|shifted|took|taken|carried|brought)\b[^.?!]{0,20}"
    r"\b(?:notes?|letters?|tablets?|pills?|razors?|blades?|rope|noose|gun)\b",
    r"\b(?:notes?|letters?|tablets|pills|razors?|blades?|rope|noose|gun)\b[^.?!]{0,14}"
    r"\b(?:is|are)\s+(?:already\s+)?(?:in|on|under|behind|inside)\s+(?:my|the|a)\b",
    r"\b(?:filled|packed|loaded|measured|counted|lined\s+up)\s+(?:the|a|my)\s+"
    r"(?:bottle|glass|syringe|needle|bag|box|tub|container)\b",
    # "i have the stuff", "i bought what i need": in a crisis thread the vague noun is the
    # means, and it is the vagueness that makes it worth reading - the person is not naming it
    # to anyone else. Outside a held crisis these keep their ordinary answer.
    r"\b(?:have|got|bought|sorted|saved)\s+(?:the|all\s+the)\s+stuff\b",
    r"\b(?:bought|got|have|sorted)\s+(?:everything|what)\s+i\s+need\b",
)

# The other half of that thread: the person turning towards help, or naming a plan that is not
# this one. Those lines have their own answers and must keep them.
HELD_CRISIS_OFF = (
    r"\bsafety\s+plan\b", r"\bplan\s+(?:with|from)\s+(?:my\s+)?(?:therapist|counsell?or|"
    r"doctor|gp|nurse|psychiatrist|social\s+worker|support\s+worker|cpn|key\s+worker)\b",
    r"\bplan\s+to\s+(?:ring|call|see|speak|talk|get\s+help|ask\s+for\s+help)\b",
    r"\bplan\s+for\s+(?:dinner|tea|lunch|breakfast|christmas|tonight'?s|the\s+weekend|"
    r"tomorrow'?s|the\s+party|the\s+trip|the\s+holiday|work)\b",
    r"\bcrisis\s+line\b", r"\bsamaritans\b", r"\b116\s*123\b", r"\b988\b",
    r"\b(?:im|i'?m|i\s+am)\s+(?:ok|okay|fine|safe|better|alright|calmer)\b",
    r"\b(?:feel|feeling)\s+(?:better|calmer|safer|a\s+bit\s+better)\b",
    r"\bnot\s+(?:going\s+to|gonna)\s+(?:do\s+it|do\s+anything)\b",
    r"\b(?:i\s+)?(?:will|'ll|ll)\s+(?:ring|call|see\s+someone|get\s+help)\b",
    r"\b(?:rang|called|texted)\s+(?:them|the\s+line|someone|my\s+\w+)\b",
    r"\bthank(?:s|\s*you)\b",
    # A note with somebody's name on it and a subject after it is a message, not the note:
    # "i wrote a note to my teacher about the trip". The suicide note is said as "the note" or
    # "my note", and the suicide word itself never reaches this rule.
    r"\b(?:note|letter)\s+(?:to|for)\s+(?:my|his|her|their|the|a|an)\b",
    # ...and a person who says they have no plan is not saying this one.
    r"\b(?:don'?t|do\s+not|havent|haven'?t|not|no\s+longer)\s+(?:have\s+)?(?:a|any|the)\s+plan\b",
    r"\bno\s+plan\b",
)

# A plan arrives a turn later. "i want to kill myself" gets the crisis card, and the next line -
# "i wrote a note", "ive picked a date", "i have the pills", "i bought a rope" - carries no wish
# word of its own, so no case read it and the greeting cheered. CRISIS_PLAN_SAID has the shapes
# that name a plan inside one line already; these are the same plan said on its own, and
# CRISIS_PLAN_ORDINARY is those words about an errand, which stay ordinary.
CRISIS_PLAN_CARRY = (
    r"\b(?:wrote|writing|written|left|leaving|leave)\s+(?:a|the|my)\s+(?:note|letter)\b",
    # The note said again as where it is, which is how people say it when they have already written
    # it: "the note is in my drawer", "the note is on the table". Main read only "the note is
    # written", so the turn got the floor placeholder - "Thanks for telling me - I'm here if you
    # want to dig into any of that" - after "i want to kill myself".
    r"\bthe\s+notes?\s+(?:is|are)\s+(?:in|on|under|by|at|next\s+to|inside)\b",
    r"\b(?:picked|pick|chosen|chose|set|setting|decided\s+on)\s+(?:a|the|my)?\s*"
    r"(?:date|day)\b",
    r"\b(?:got|get|bought|buy|have|having|stockpiled|stockpiling|saved\s+up|saving\s+up|"
    r"ordered|ordering|hid|hiding)\s+(?:the|a|some|enough|loads\s+of|up)?\s*"
    r"(?:pills|tablets|paracetamol|painkillers|rope|noose|razors?|blades?|knife|gun)\b",
    # "ive got a plan" is the same sentence as "i have a plan" with the apostrophe dropped, and
    # folding leaves it one word: the pattern wanted a space before "got", so the commonest way
    # people type it fell through to the placeholder.
    r"\bi(?:'ve|ve)?\s+(?:have|got)\s+a\s+plan\b",
    r"\bi\s+know\s+how\s+(?:i'?m|im|i\s+am|i'?d|id)\s+(?:going\s+to|gonna|to|would)\s+"
    r"(?:do\s+it|end\s+it|kill\s+myself|finish\s+it)\b",
    r"\b(?:said|saying|writing)\s+(?:my\s+)?goodbyes?\b",
    r"\b(?:picked|found|chosen)\s+(?:a|the)\s+(?:place|spot|bridge|roof|car\s+park)\b",
    r"\bnot\s+going\s+to\s+be\s+(?:here|around)\s+(?:much\s+)?(?:longer|after\s+this)\b",
    # The same goodbye with a date on it: "i wont be here next week", "i wont be around for
    # christmas". Read only in the crisis frame and only when it is the speaker's own future.
    r"\bi\s+won'?t\s+be\s+(?:here|around)\s+(?:for\s+)?(?:next\s+\w+|much\s+longer|"
    r"christmas|the\s+weekend|long)\b",
    # The plan said without the wish, a turn later: "im going to do it tonight", "ill do it", "i
    # just need the nerve", "i bought the stuff". Ordinary on their own, so only inside the frame.
    r"\b(?:i'?m|im|i\s+am|i\s+will|ill|i'?ll)\s+(?:going\s+to\s+|gonna\s+)?"
    r"(?:do\s+it|end\s+it|finish\s+it|go\s+through\s+with\s+it|kill\s+my\s*self)\b",
    # The nerve to ring somebody is the help, not the plan.
    r"\b(?:just\s+)?need\s+(?:the|some|a\s+bit\s+of|more)\s+nerve\b"
    r"(?![\s\S]*\b(?:ring|call|phone|contact|book|tell|text|see\s+(?:the|my|a)|"
    r"gp|doctor|nurse|samaritans|111|999|a\s?&\s?e|hospital|therapist|counsell?or)\b)",
    # "the stuff" is the means only when nothing after it says what it is for.
    r"\b(?:got|bought|have|have\s+got|found)\s+(?:the|all\s+the)\s*"
    r"(?:stuff|things|kit|equipment)\b(?=\s*(?:$|[.,!?]|ready\b|now\b|today\b|tonight\b))",

)

CRISIS_PLAN_ORDINARY = (
    # A note is an errand when the line says what it is about, and a note in an app is not a note
    # on the table: "i wrote a note about the rent" is the rent.
    r"\b(?:thank\s*you|thankyou|birthday|christmas|sick|absence|shopping|grocery|to[\s-]do|"
    r"sticky|reminder|credit|debit|bank)\b[^.?!]{0,14}\bnotes?\b",
    r"\bnotes?\b[^.?!]{0,24}\b(?:about\s+the|for\s+the|for\s+my\s+(?:work|boss|school|"
    r"doctor|landlord|mum|dad|teacher|team|rent|car|house|flat)|re:|saying\s+thank)\b",
    r"\bnotes?\s+(?:app|on\s+my\s+phone|in\s+my\s+phone)\b",
    # A letter to somebody official is that letter, not the one people leave behind.
    r"\bletters?\b[^.?!]{0,26}\b(?:to\s+the\s+(?:council|bank|landlord|school|doctor|"
    r"hospital|company|insurer|insurance|dvla|hmrc|mp|jobcentre|university|college)|"
    r"about\s+the\s+(?:rent|bill|debt|job|course|house|flat))\b",
    # The diary, not the plan: a date for the wedding, the exam, the scan.
    r"\b(?:date|day)\b[^.?!]{0,18}\b(?:for\s+(?:the\s+)?(?:wedding|holiday|exam|interview|"
    r"dentist|doctor|scan|move|party|trip|operation|op|viewing)|of\s+the\s+(?:wedding|exam))\b",
    # Tablets that are somebody's prescription, and the rope that is for the trailer.
    r"\b(?:my|the|his|her)\s+(?:prescription|antibiotics|contraceptive|blood\s+pressure|"
    r"diabetes|epilepsy|thyroid|thyroxine|metformin|statins?)\b",
    r"\b(?:pills|tablets|painkillers|paracetamol)\b[^.?!]{0,20}\b(?:from\s+the|under\s+"
    r"prescription|prescribed|for\s+my\s+(?:back|knee|period|headache|migraine|arthritis|pain|"
    r"hip|shoulder|neck|teeth|tooth))\b",
    # The vague noun has an ordinary referent too: "i have all the stuff for the cake", and a price
    # is a price - "i know how much it costs" - not a line about how much it would take.
    r"\bstuff\b[^.?!]{0,20}\bfor\s+the\s+(?:cake|party|trip|dinner|recipe|barbecue|bbq|"
    r"birthday|wedding|christmas|exam|interview|move|house|flat|garden|bathroom|kitchen|car)\b",
    r"\bi\s+know\s+how\s+much\b[^.?!]{0,24}\b(?:costs?|cost\s+me|pays?|weighs?|i\s+owe|"
    r"it\s+is|it's)\b",
    r"\bmeasured\b[^.?!]{0,24}\b(?:milk|water|flour|sugar|rice|ingredients?|grams|ml|ounces|"
    r"paint|timber|wood)\b",
    r"\b(?:rope|knife|blade|blades)\b[^.?!]{0,24}\b(?:for\s+the\s+(?:car|trailer|garden|"
    r"washing|bikes?|roof\s+rack|kitchen|cooking|dinner|bread|onions?|swings?|clothes\s+line|"
    r"washing\s+line|boat|trampoline|tree\s+house|shed|gate|fence)|"
    r"to\s+(?:tie|tow|cut|trim|slash|open|prune|chop|slice|fillet|carve|peel))\b",
)

# The card for a plan that has already been said: unlike the crisis card, it asks for a person in
# the room and for the means to go out of reach, because a plan is closer than a wish.
CRISIS_PLAN_REPLY = (
    "Thank you for telling me. That is a plan, and a plan needs help now rather than later: ring "
    "999 or 911, or get yourself to A&E and say what you have ready - and please do not stay on "
    "your own: put the tablets or the note out of reach and ask someone to come and sit with you.",
    "That is a plan, so please do not carry it on your own: ring 999 or 911, or go to A&E and say "
    "what you have got ready, and have someone come to you and take the means away. Samaritans are "
    "on 116 123 any hour if you need a voice before that.",
)

# "i can't wake my husband up", "i cant wake the baby". The pronoun object has its own pattern
# above ("i can't wake her"), and the noun was missing from every one of them: the same collapse
# said with a person's name in it was answered as a sleep question. A named reason to be up -
# school, work, an early shift - is still the grumble, so that is excluded here rather than in
# ROUTINE_WAKE, which only knows the shapes where no object comes between.
WAKE_UP_SOMEONE = (
    r"\b(?:can'?t|cant|cannot|can\s+not|unable\s+to|struggling\s+to|having\s+trouble)\b"
    r"[^.?!]{0,24}?\b(?:wake|waken|waking|rouse|wake\s+up)\s+"
    r"(?:my|the|our|his|her|their)\s+" + PERSON + r"\b"
    # a shift is the same reason as school or work, and it is the commonest way people say it:
    # "i cant wake my husband up for his shift" is the alarm clock, not a collapse.
    r"(?![^.?!]{0,12}\b(?:for|to|before|in\s+time\s+for)\s+(?:(?:his|her|their|the|a)\s+)?"
    r"(?:school|work|college|uni|university|nursery|childminder|shift|the\s+(?:bus|train))\b)",
    # "i can't get my husband to wake up": the person comes before the verb here, so the pattern
    # above cannot see it.
    r"\b(?:can'?t|cant|cannot|unable\s+to|struggling\s+to|having\s+trouble)\b[^.?!]{0,20}?"
    r"\b(?:get|keep)\s+(?:my|the|our|his|her|their)\s+" + PERSON + r"\b[^.?!]{0,15}?"
    r"\b(?:wake|waken|rouse|stir)\b",
)

# A reason to be up early is the whole story of a line like "i cant wake my mum up for work" or
# "i cant wake my son up for his paper round". The routine words are open-ended, so this is a list
# of reasons rather than another fence on each shape - and any red sign in the line beats it.
ROUTINE_REASON = (
    r"\b(?:school|work|college|uni|university|nursery|childminder|shifts?|alarms?|bus|train|"
    r"flight|exams?|test|interview|appointment|meeting|class|lecture|lesson|paper\s+round|"
    r"paper\s+deliveries|early\s+start|mornings?)\b",
)

SPELL_RED = (
    r"\b(?:temperatur\w+|fever\w*|breath\w*|blue|grey|gray|limp|floppy|floppiness|seizure|fit|"
    r"shaking|rash|stiff\s+neck|dribbling|drooling|unresponsive)\b",
)

MORNING_ROUTINE = (
    r"\b(?:in|of)\s+the\s+mornings?\b|\bmornings\b|\bbefore\s+(?:school|work|nursery|"
    r"breakfast)\b|\bon\s+school\s+days\b",
)

# "hard to wake", "difficult to rouse", "not rousable": the same collapse said as an adjective
# instead of an event. A teenager who is hard to wake in the mornings is not a collapse, so the
# morning words stand it down, and a bare "my son is hard to wake up" has no event in it at all -
# the sleepiness word is what turns it into one. A baby is the exception: rousing a newborn is how
# a parent checks it at all.
HARD_TO_WAKE = (
    r"\b(?:can'?t|cannot|can\s+not)\s+be\s+(?:woken|roused|wakened|stirred)\b",
    r"\b(?:very|so|really|extremely|quite)?\s*(?:sleepy|drowsy|lethargic|floppy|limp)\b[^.?!]{0,25}"
    r"\b(?:hard|difficult|impossible|not\s+easy)\s+to\s+(?:wake|rouse|waken|stir)\b",
    r"\b(?:hard|difficult|impossible|not\s+easy)\s+to\s+(?:wake|rouse|waken|stir)\b[^.?!]{0,25}"
    r"\b(?:very\s+|so\s+)?(?:sleepy|drowsy|floppy|limp|lethargic|not\s+(?:himself|herself|"
    r"themselves))\b",
    r"\b(?:baby|babies|newborn|infant)\b[^.?!]{0,25}\b(?:hard|difficult|impossible)\s+to\s+"
    r"(?:wake|rouse|waken|stir)\b",
    r"\b(?:hard|difficult|impossible)\s+to\s+(?:wake|rouse|waken|stir)\b[^.?!]{0,25}"
    r"\b(?:baby|newborn|infant)\b",
    # "rouse" is a clinical word, not a morning word: "my daughter is difficult to rouse" is
    # always a worry, while "hard to wake" on its own is usually the school run.
    r"\b(?:he|she|they|my\s+" + PERSON + r"|the\s+" + PERSON + r")\b[^.?!]{0,15}"
    r"\b(?:is|was|seems?|seemed|has\s+been|had\s+been)\b[^.?!]{0,8}"
    r"\b(?:hard|difficult|impossible)\s+to\s+(?:rouse|waken|stir)\b",
)

# A visit has a time on it and a collapse has a fall in it. When both readings are open - "my friend
# isnt coming round after all" - the visit wins unless something in the line says what happened.
VISIT_OR_TIME = (
    r"\b(?:tonight|later|tomorrow|this\s+(?:evening|afternoon|morning|weekend)|after\s+all|"
    r"next\s+(?:week|weekend)|until\s+\w+|for\s+(?:dinner|tea|coffee|lunch|supper|a\s+bit))\b",
)

COLLAPSE_HINT = (
    r"\b(?:fell|fallen|fall|bang|banged|hit|head|collapsed|floor|ground|pavement|breathing|"
    r"ambulance|pulse|overdose|swallowed|diabetic|seizure|the\s+water|pool)\b",
)

# "he wont come round", "she isnt coming round", "my dad isnt rousing": the same person who cannot
# be woken, in the other words people use for it. A visit has no "wont" in it either ("my mum is
# coming round later"), so the visit words are fenced - and the speaker is left out, because nobody
# who is unconscious is typing "i cant come round tonight".
WONT_COME_ROUND = (
    r"\b(?:he|she|they|my\s+" + PERSON + r"|the\s+" + PERSON + r")\b[^.?!]{0,12}"
    r"\b(?:won'?t|wont|isn'?t|isnt|is\s+not|not|hasn'?t|hasnt|didn'?t|didnt|can'?t|cant|cannot)\b"
    r"[^.?!]{0,10}\b(?:(?:com(?:e|ing))\s+round\b(?!\s*(?:for|to)\s+(?:dinner|tea|coffee|lunch|"
    r"supper|visit|see|pick|my|his|her|their|our|the\s+(?:idea|way|view|opinion|plan)))|"
    r"com(?:e|ing)\s+to\b(?!\s+(?:the|a|an|my|your|his|her|their|our|this|that|it|us|me|him|them)\b)|"
    r"rous(?:e|es|ing|ed|able)\b)",
    # "i cant bring him round", "i cant get her to come round"
    r"\b(?:can'?t|cant|cannot|unable\s+to|struggling\s+to|not\s+able\s+to)\b[^.?!]{0,15}"
    r"\b(?:bring|get|rouse|wake)\s+(?:him|her|them|my\s+" + PERSON + r"|the\s+" + PERSON + r")\b"
    r"(?:[^.?!]{0,15}\bround\b(?!\s+(?:for|to)\s+(?:dinner|tea|coffee|lunch|supper|see|my|his|her|"
    r"their|our|the\s+(?:idea|way|view|opinion)))|"
    r"[^.?!]{0,6}\bawake\b|"
    r"[^.?!]{0,8}\bto\s+(?:wake|waken|stir|rouse)\b|"
    r"[^.?!]{0,6}\bto\b(?=\s*[,.!?]|\s*$))",
)
# A wound whose redness is on the move, or that has a red line running from it, is lymphangitis:
# the infection has got into the channels that drain the wound, and that is the same-day call and
# the 999 call once a fever is with it. The shape was all over main and no case owned it - "my
# husband has a red streak up his arm" and "red line spreading up from my cut" got the wound
# watch-and-wait ("shows up two or three days after the injury"), "a red line is running up my leg
# from a cut" got a shrug, and "redness spreading up my arm from a cut" got the chest-pain card.
# The mark is the line, or the redness with a word of movement next to it, and it is never a thing:
# a red line on a train, in the hair, or in the sky is a different red.
_STREAK_MARK = (
    r"\bred\s+(?:line|streak|track)s?\b",
    r"\breddish\s+(?:line|streak)s?\b",
)
_STREAK_REDNESS = r"\b(?:redness|red\s+skin|red\s+area|red\s+patch|the\s+red\s+part|infection)\b"
_STREAK_MOVE = (
    r"\b(?:spreading|spread|creeping|crept|tracking|tracked|travell?ing|travell?ed|moving|moved|"
    r"running|ran|going|gone|goes|up|down)\b",
)
# The red has to be on a person: a wound word, or a part of the body. "The red line on the
# central line is shut" and "a red line on my favourite mug" are about the red, not about anybody.
_STREAK_ON_A_PERSON = (
    r"\b(?:cut|cuts|cuts?\s+myself|gash|graze[ds]?|scrape[ds]?|scratch(?:es|ed)?|wound|wounds|"
    r"sore|splinter|thorn|blister|bite|bites|bitten|burn(?:s|ed|t)?|sting(?:s|ed)?|puncture|"
    r"operation|opsite|stitches?|staple[ds]?|dressing|bandage[ds]?|plaster|tattoo)\b",
)
WOUND_STREAK = (
    r"\A(?=.*" + _STREAK_MARK[0] + r")(?=.*" + _STREAK_ON_A_PERSON[0] + r"|.*\b" + BODY + r")",
    r"\A(?=.*" + _STREAK_MARK[1] + r")(?=.*" + _STREAK_ON_A_PERSON[0] + r"|.*\b" + BODY + r")",
    r"\A(?=.*" + _STREAK_REDNESS + r"[^.?!]{0,30}" + _STREAK_MOVE[0] + r")"
    r"(?=.*" + _STREAK_ON_A_PERSON[0] + r"|.*\b" + BODY + r")",
    r"\A(?=.*" + _STREAK_MOVE[0] + r"[^.?!]{0,30}" + _STREAK_REDNESS + r")"
    r"(?=.*" + _STREAK_ON_A_PERSON[0] + r"|.*\b" + BODY + r")",
)
# The red is not a wound's: a dye, a print, a railway, the sky, a pen, a screen, a nappy crease.
WOUND_STREAK_OFF = (
    r"\bhair\b", r"\bdye\w*\b", r"\bhighlight\w*\b", r"\bnail\s+polish\b", r"\blipstick\b",
    r"\btrain\b", r"\btube\b", r"\bmetro\b", r"\bbus\b", r"\broad\b", r"\blane\b", r"\bmap\b",
    r"\bsky\b", r"\bsunset\b", r"\brainbow\b", r"\bpaint\w*\b", r"\bmarker\b", r"\bpen\b",
    r"\bscreen\b", r"\btv\b", r"\btele\b", r"\bfilm\b", r"\bbook\b", r"\bpaper\b", r"\bflag\b",
    r"\bteam\b", r"\bspider\s+vein\w*\b", r"\bstretch\s+mark\w*\b", r"\bnappy\b", r"\bnapkin\b",
    r"\bcrease\w*\b", r"\btyre\w*\b", r"\bcar\b", r"\bwall\b", r"\bfloor\b", r"\bkitchen\b",
)
# A fever, a shiver or a body going downhill is the sepsis card rather than the same-day one.
STREAK_FEVER = (
    r"\bfever\w*\b", r"\btemperatures?\b", r"\btemps?\b", r"\bshiver\w*\b", r"\brigors\b",
    r"\bclammy\b", r"\bvery\s+unwell\b", r"\bunwell\b", r"\bfluey\b", r"\bhot\b",
    r"\b\d{2}(?:\.\d)?\s*(?:c\b|degrees)\b",
)
# A red line running from a wound, or redness spreading from a wound, is lymphangitis: the
# infection is in the channels that drain the wound, so it is a same-day call, and the 999 call
# once a fever, a shiver or a body going downhill is with it. See WOUND_STREAK for why it needs an
# arm of its own: the wound watch-and-wait, a shrug and the chest-pain card all answered it.
def _with_streak_fever(pats):
    """The same streak shapes, read only when the line also has a fever in it."""
    extra = r"(?=[\s\S]*(?:" + "|".join(STREAK_FEVER) + r"))"
    return tuple(p + extra for p in pats)


WOUND_STREAK_FEVER = _with_streak_fever(WOUND_STREAK)


# --- the arms in safety.py that read a wish said as a body part, a means, another person, ------
# a mouthful in the perfect tense, or a plan with no wish word. `safety.py` must stay under the
# publisher's 1 MiB, so the patterns live here with the rest of the tables.
# A job after the place makes the leaving an errand: "walk off the roof to fix the gutter".
_A_PURPOSE_AFTER = (r"(?!\s*,?\s*(?:to|and|so|then)\s+"
                    r"(?:fix|get|catch|grab|fetch|collect|check|clean|clear|put|take|pick|mend|"
                    r"paint|water|feed|empty|see|look|have|find|hang|drop|pass|give|bring|do)\b)")

_OFF_A_HEIGHT = (
    r"off(?:\s+of)?\s+(?:a|an|the|my|our)?\s*"
    r"(?:bridge|roof|building|block|cliff|balcony|ledge|height|car\s*park)\b"
    + _A_PURPOSE_AFTER
)

# The edge of a platform, a pier or a wall is where people stand and where a train leaves from, so
# only the four verbs that are unmistakably a jump count on it: "jump off the platform" is a
# means, "stepping off the platform at euston" is how the day started.
_OFF_AN_EDGE = (
    r"off(?:\s+of)?\s+(?:a|an|the|my|our)?\s*"
    r"(?:platform|pier|wall|bank|edge)\b"
    + _A_PURPOSE_AFTER
)

_INTO_THE_WAY = (
    r"(?:in\s+front\s+of|under|onto)\s+(?:a|an|the|my|our)?\s*"
    r"(?:train|trains|bus|buses|lorry|truck|coach|traffic|tracks?|rails?|line)\b"
    + _A_PURPOSE_AFTER
)

SELF_HARM_WISHES_A_PART = (
    r"\b(?:want|wanna|wanted|wanting|need|needing|going|gonna|plan|planning|tempted|urge|"
    r"feel\s+like|feeling\s+like|think\s+about|thinking\s+about|thought\s+about)\s+(?:to\s+)?"
    r"(?:cut|cutting|burn|burning|hurt|hurting|harm|harming|scratch|scratching|scald|scalding|"
    r"starve|starving|bruise|bruising)\s+my\s+(?:own\s+)?"
    r"(?:skin|arms?|legs?|wrists?|thighs?|forearms?|belly|stomach|hips?|chest|hands?|feet|foot|"
    r"scalp|neck|shoulders?|back|face)\b"
    r"(?!\s+(?:hair|nails?|toenails?|fingernails?|fat|calories?|carbs?)\b)",
)

# The verbs a height takes. Walking or stepping off something is how a day starts or a job gets
# done ("stepping off the platform at euston", "walk off the roof to fix the gutter"), so those
# two only count with the way a vehicle comes (see `_INTO_THE_WAY`).
_HEIGHT_MEANS_VERB = (
    r"throw|throwing|threw|jump|jumping|jumped|leap|leaping|leapt|fall|falling|fell")
_ANY_MEANS_VERB = _HEIGHT_MEANS_VERB + r"|step|stepping|stepped|walk|walking|walked|lie|lying|lay"
_A_MEANS_PLACE = (r"(?:(?:" + _ANY_MEANS_VERB + r")\s+" + _INTO_THE_WAY
                  + r"|(?:" + _HEIGHT_MEANS_VERB + r")\s+(?:" + _OFF_A_HEIGHT
                  + r"|" + _OFF_AN_EDGE + r"))")

SELF_HARM_BY_A_MEANS = (
    r"\b(?:" + _ANY_MEANS_VERB + r")\s+(?:my\s*self|me)\s*" + _INTO_THE_WAY,
    r"\b(?:" + _HEIGHT_MEANS_VERB + r")\s+(?:my\s*self|me)\s*(?:" + _OFF_A_HEIGHT
    + r"|" + _OFF_AN_EDGE + r")",
    # The means as an instrument, which is the wish whatever it is held by.
    r"\b(?:hang|hanging|strangle|shoot|shooting|stab|poison|overdose|overdosing)\s+"
    r"(?:my\s*self|me)\b",
    r"\b(?:with|using|by)\s+(?:a\s+|the\s+)?(?:rope|knife|blade|razor|gun|pills|tablets|"
    r"paracetamol|belt)\b[^.?!]{0,24}\b(?:kill|hurt|harm|cut|hang|shoot)\s+my\s*self\b",
    # The same, said as a plan with no `myself` in it, or as the fragment somebody types in the
    # middle of it ("jump in front of a train"). A fragment has to open the line, so "the dog
    # jumped in front of the car" stays the dog.
    r"\b(?:i\s+want|i\s+wanna|im|i'?m|i\s+am|i\s+could|i\s+would|i\s+might|i\s+should|"
    r"im\s+going|i'?m\s+going|going|thinking\s+about|thought\s+about|tempted|planning)"
    r"\b[^.?!]{0,30}\b" + _A_MEANS_PLACE,
    r"^\s*(?:so\s+|and\s+|then\s+)?" + _A_MEANS_PLACE,
)

POISON_SAID = (
    r"\b(?:swallowed|drank|drunk|eaten|ate|took|downed|inhaled|gulped|licked)\s+"
    r"(?:some\s+|a\s+bit\s+of\s+|a\s+mouthful\s+of\s+|loads\s+of\s+|the\s+rest\s+of\s+|"
    r"half\s+a\s+bottle\s+of\s+|a\s+whole\s+bottle\s+of\s+)?"
    r"(?:bleach|detergent|disinfectant|antifreeze|weed\s?killer|hand\s+saniti[sz]er|"
    r"drain\s+cleaner|soap|shampoo|mouthwash|shower\s+gel|cleaning\s+products?|"
    r"paint\s?thinner|white\s+spirit)\b",
    # A doubled dose is the amount said as a mistake, which is the poisons line's question. The
    # present-tense prescription is not: "i take a double dose of my tablets" is the ordinary
    # line, so the doubling has to be something already done.
    r"\b(?:double|triple)\s+dos(?:ed|ing)\b",
    r"\b(?:doubl|tripl)(?:ed|ing)\s+(?:up\s+)?(?:on\s+)?(?:my|the)\s+"
    r"(?:dose|insulin|meds|medication|tablets|pills)\b",
)

A_HURT_OF_A_BODY_PART = (
    r"\b(?:hurt|hurting|harm|harming|work|working|push|pushing)\s+my\s+"
    r"(?:own\s+)?(?:arms?|legs?|shoulders?|muscles?|back|abs|core|chest|glutes?|calves)\b")

A_WORKOUT_CUE = (
    r"\b(?:gym|work\s?outs?|weights?|weight\s?lifting|lifting|dumbbells?|barbells?|kettlebells?|"
    r"treadmill|rowing|spin(?:ning)?\s+class|physio\w*|training\s+session|leg\s+day|"
    r"arm\s+day|pt\s+session)\b")

A_PLAN_SAID = (
    # "i know how i'd do it" - the shape CRISIS_PLAN_SAID spells, read cold. The "would" form and
    # the bare "id" are the two ways people type it.
    r"\bi\s+know\s+how\s+(?:i'?d|id|i\s+would)\s+(?:do\s+it|end\s+it|be\s+done|go\b)",
    r"\bi\s+know\s+how\s+(?:i'?m|im|i\s+am)\s+(?:going\s+to|gonna)\s+(?:do\s+it|end\s+it|be\s+done)\b",
    # "my plan is to jump", "the plan is to take all of them": the frame, a method, and nothing
    # that makes the method an errand. The line has to end at the method or at a crisis object.
    r"\b(?:my|the|our)\s+plan\s*(?:is|'s|was)\s+to\s+"
    r"(?:jump|cut|hang|overdose|swallow|take|use|go)\b"
    r"(?:\s+(?:it|them|all\s+of\s+them|them\s+all|the\s+lot|too\s+many|an?\s+overdose|"
    r"my\s+life|my\s*self|off\s+(?:a|the)\s+(?:bridge|roof|building|cliff|balcony)|"
    r"in\s+front\s+of\s+(?:a|the)\s+(?:train|bus)|my\s+(?:wrists?|throat|arms?|legs?|neck)))?"
    # "at once", "right now", "all at once" after the object is the same plan, not a diary.
    r"(?:\s+(?:all\s+at\s+once|at\s+once|right\s+now|tonight|today|now))?"
    r"\s*[.?!]*\s*$",
    # "i have a plan to end it", "ive got a plan for tonight" is not this: the method word is.
    r"\bi\s+(?:have|got|'ve\s+got|ve\s+got)\s+a\s+plan\s+to\s+(?:do\s+it|end\s+it|end\s+my\s+life|"
    r"kill\s+my\s*self|take\s+(?:all\s+of\s+them|them\s+all|the\s+lot)|jump|overdose)\b",
    # "im going to do it" with nothing after it. Only the bare line: "im going to do it after
    # work" is the decorating, and "i am going to do it three times a week" is the gym.
    r"\b(?:im|i'?m|i\s+am)\s+going\s+to\s+do\s+it\s*[.?!]*$",
    # "the plan is to take all of them" said with no frame noun at all.
    r"^\s*(?:so\s+)?(?:i'?m\s+)?going\s+to\s+(?:take|swallow)\s+(?:all\s+of\s+them|them\s+all|"
    r"the\s+(?:whole\s+)?packet|the\s+lot)\s*[.?!]*\s*$",
)

A_PLAN_ORDINARY = (
    r"\bplan\s+(?:is|'s|was)\s+to\s+(?:pay|save|book|call|ring|text|email|write|start|finish|"
    r"order|cancel|visit|see|meet|apply|clean|sort|tidy|walk|run|train|study|revise|move|"
    r"paint|cook|buy|sell|fly|drive|go\s+(?:to|back|home|out)|get\s+(?:the|a|my|some)|"
    r"have\s+(?:a|some|the|lunch|dinner|breakfast))\b",
    r"\bgoing\s+to\s+do\s+it\s+(?:after|before|on|at|in|next|this|tomorrow|tonight|later|when|"
    r"once|every|twice|again|three|two|with|for|if|and)\b",
    r"\bwe\s+(?:were|are)\s+going\s+to\s+do\s+it\b",
    r"\bjump\s*-?\s*start\b|\bjump\s+(?:the\s+queue|the\s+gun|start\s+the\s+car)\b",
    r"\bknow\s+how\s+(?:i'?d|id)\s+do\s+it\s+(?:now|too|myself|already)\b",
    # "i know how id do it" is the plan; the same words with a second person or a plain object
    # after them explain an ordinary job: "i know how i'd do it - you just click the button".
    r"\bknow\s+how\s+(?:i'?d|id|i\s+would)\s+(?:do\s+it|end\s+it)\b\s*(?:[-\u2013,:;]\s*)?"
    r"(?:you|u|it'?s|its|then|just|by|with|using|through|via)\b",
    # A condition or a tool after the doing is an errand: "if i had the money", "with a spanner".
    r"\b(?:do\s+it|end\s+it)\s+(?:if|when|once|with|by|using|through|via|for|on|at|in)\b",
)


SELF_HARM_OWN_PART = (*SELF_HARM_WISHES_A_PART, *SELF_HARM_BY_A_MEANS)
