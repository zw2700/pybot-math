"""Someone they look after, in physical trouble, is never met with a stock line.

`bot/compose/trouble.py` answers the trouble the person is having themselves - their back, their
boiler - and stands aside for anything about another person, because an emergency about a
relative belongs to `bot/modules/safety.py`. That division is right, but the safety band's cue
list does not hold the state words yet: on main, of twelve plain reports about a relative's body,
four reach an emergency line and the other eight reach a pleasantry.

    my mum is unresponsive            -> Noted! What would be most useful to talk about?
    my son wont wake up               -> Noted! What would be most useful to talk about?
    my baby has a temperature of 40   -> Noted! What would be most useful to talk about?
    my wife is fitting                -> Got it. Is there anything you'd like a hand with?

The cue list is the safety lane's to own. What the composer owns is that a pleasantry of ours
is never the answer to one of these, so this module proposes the careful line instead, and only
when no module that can do better has anything to say.
"""
import random
import re
try:  # the reading of a dream, so a dream of the thing is not the thing
    from ..memory import dream as _dream
except Exception:  # noqa: BLE001 - a reading that cannot be imported just adds no rule
    _dream = None

WORD = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")

# Who is in trouble: the words people use for the person they are looking after.
FAMILY = frozenset({
    "mum", "mam", "mom", "mother", "mummy", "mommy", "dad", "father", "daddy", "son",
    "daughter", "baby", "toddler", "child", "kid", "boy", "girl", "nan", "nana", "granny",
    "gran", "grandma", "grandad", "grandpa", "grandmother", "grandfather", "husband", "wife",
    "partner", "boyfriend", "girlfriend", "brother", "sister", "friend", "neighbour",
    "neighbor", "uncle", "aunt", "auntie", "cousin", "stepson", "stepdaughter", "stepdad",
    "stepmum", "fiance", "fiancee", "flatmate", "housemate", "carer", "patient",
    "niece", "nephew", "grandson", "granddaughter", "stepson", "stepdaughter", "godson",
    "goddaughter", "toddler", "newborn", "childminder", "flatmate", "teenager", "teen",
    "adolescent",
})

# A professional who has not answered is a message, not a body: "my carer is not responding" is the
# carer who has not replied, and this module was the one that rang the ambulance for it. The safety
# module carries the same fence (PRO_NOT_ANSWERING / BODY_IN_THE_ROOM there); it has to be in both
# because this module answers even when the safety module stands down. Anything that puts the body
# in the room brings the call back: the floor, the bed, breathing, a colour, pain, a name.
PRO_ANSWERING = re.compile(
    r"\b(?:my|his|her|their|our|the)\s+(?:carers?|care\s+workers?|support\s+workers?|"
    r"social\s+workers?|personal\s+assistants?|nurses?|midwives?|midwife|doctors?|gps?|"
    r"physios?|therapists?)\b[^.?!]{0,30}\b(?:isn'?t|is\s+not|not|hasn'?t|has\s+not|never|"
    r"no)\s+respond(?:ing|ed|e)?\b"
    r"|\bno\s+response\s+from\s+(?:my|the|our)\s+(?:carer|care\s+worker|support\s+worker|"
    r"social\s+worker|personal\s+assistant|nurse|doctor|gp|physio|therapist)s?\b")
BODY_IN_THE_ROOM = re.compile(
    r"\b(?:floor|ground|bed|sofa|settee|couch|bath|pavement|street|doorstep)\b"
    r"|\b(?:collapsed|collapsing|fell|fallen|fainted|pass(?:ed)?\s+out|seizure|fitting)\b"
    r"|\b(?:breathing|breath|breathe|pulse|blue|lips|cold|clammy|sweating|eyes|pale|grey|gray)\b"
    r"|\b(?:unconscious|out\s+cold|unresponsive|in\s+front\s+of\s+me|with\s+me|next\s+to\s+me)\b"
    r"|\b(?:to\s+(?:pain|touch|voices?|noise|light|stimulus)|(?:his|her|their)\s+name)\b")

# Not awake, not breathing, fitting, choking, limp: an ambulance now.
NOW = (
    "unresponsive", "not responding", "no response", "wont wake", "won't wake", "cant wake",
    "can't wake", "not waking", "not breathing", "stopped breathing", "isnt breathing",
    "isn't breathing", "struggling to breathe", "cant breathe", "can't breathe", "gasping",
    # The other way people say the same thing, and it was a young couple's "trying for a baby"
    # card: the subject was left bare ("my baby is struggling") and the fertility row took it.
    "struggling for breath", "fighting for breath", "gasping for breath", "struggling for air",
    "unconscious", "unconcious", "collapsed", "limp", "floppy", "fitting", "seizure",
    "convulsing", "choking", "turning blue", "gone blue", "blue lips", "no pulse",
    "cardiac", "overdose", "took too many", "swallowed his tongue",
    # The commonest way people say a fit: "he had a fit this morning", "my son keeps having fits".
    "had a fit", "has a fit", "having a fit", "having fits", "keeps fitting", "kept fitting",
    "keeps having fits", "kept having fits",
    # "isnt responding" on its own is a body; the `to X` guard below keeps "isnt responding to
    # his name" and "isnt responding to treatment" out.
    "isnt responding", "isn't responding", "isnt responsive", "isn't responsive", "not responsive",
)

# A colour is not a body. "My daughter keeps asking why the sky is blue" and "my son is 4 and his
# favourite colour is blue" are not a child going blue in the face, and the 999 card on one of
# those is the worst reply the bot can give: the person asked about a sky, and the bot asked them
# to ring an ambulance. The loose ways of saying it - is/looks/went blue - count only when the line
# names the body that has gone that colour, or the person it is about ("he", "she", "the baby").
# The pinned ways ("turning blue", "gone blue", "blue lips") stay in the state list above, because
# no one says the sky is turning blue.
BLUE_LOOSE = re.compile(
    r"\b(?:is|are|was|were|looks?|looking|went|goes|getting|turned|turning|has gone|have gone)"
    r"\b[^.?!;]{0,14}\bblue\b")
# The words that can stand between the body and the colour without the colour belonging to
# something else: "his lips are pale and blue", "she went a bit blue", "my son has gone blue".
# Nothing else may stand there, which is what keeps "my son is 3 and everything he owns is blue"
# and "my mum says the sea is blue" out - the colour is two nouns away from the person.
BLUE_BETWEEN = (
    r"(?:\s+(?:a\s+bit|a\s+little|very|really|quite|all|pale|grey|gray|and|has\s+gone|"
    r"have\s+gone|had\s+gone|gone|getting|looking|turning|turned|is|are|was|were|looks?|"
    r"looked|went|goes))*")
BLUE_BODY = re.compile(
    r"\b(?:lips?|mouth|tongue|face|cheeks?|skin|fingers?|fingertips?|hands?|nails?|feet|foot|"
    r"toes?|arms?|legs?|body)\b" + BLUE_BETWEEN + r"\s+blue\b"
    r"|\b(?:he|she|they|baby|boy|girl|kid|child|son|daughter|mum|mam|mom|dad|father|mother|"
    r"wife|husband|partner|brother|sister|nan|granny|gran|grandad|grandma|grandpa|stepson|"
    r"stepdaughter|nephew|niece|friend|neighbour)\b" + BLUE_BETWEEN + r"\s+blue\b")

# Grey is the other colour of a body short of blood, and it is the colour of a great many things
# that are not a body: a tooth knocked out goes grey, hair goes grey, white washing goes grey, a
# mould goes grey. "my kid has a wobbly tooth thats gone grey" was asked for an ambulance because
# `gone grey` was in the state list with no body beside it. Grey therefore counts the way blue
# does - when the line names the part that changed or the person it is about, or says the whole of
# them changed.
GREY_LOOSE = re.compile(
    r"\b(?:is|are|was|were|looks?|looking|went|goes|getting|turned|turning|has gone|have gone|"
    r"had gone|going|gone)\b[^.?!;]{0,14}\b(?:grey|gray)\b")
# The words that may stand between the person and the colour. `BLUE_BETWEEN` is blue's list, and
# grey needed two more: "my daughter has turned grey" (has turned) and "his lips are going grey"
# (going). Both are the way people type it, and both left an emergency line with no card.
GREY_BETWEEN = (
    r"(?:\s+(?:a\s+bit|a\s+little|very|really|quite|all|pale|and|"
    r"has\s+gone|have\s+gone|had\s+gone|has\s+turned|have\s+turned|had\s+turned|"
    r"is\s+going|are\s+going|was\s+going|were\s+going|gone|going|goes|getting|looking|"
    r"turning|turned|is|are|was|were|looks?|looked|went))*")
# Who the colour can be about: the same words this module already keeps for the person they look
# after, plus the pronouns and the way `hes`/`shes` are typed. `\bhe\b` does not match "hes", so
# "hes gone grey" named nobody at all and lost the line main caught.
GREY_PEOPLE = "|".join(sorted(FAMILY | {"he", "she", "they", "hes", "shes", "everyone"},
                              key=len, reverse=True))
# A person going grey is nearly always their hair, and that is the one grey the card kept taking:
# "my husband is going grey" is a remark about age, not a body on the floor. A part of a person
# still counts with any verb ("his lips are going grey"), because lips do not go grey with age.
# Beside a person the colour has to be said as a state - "is grey", "has gone grey", "went grey",
# "has turned grey" - and not as the slow change "going/getting/turning grey".
GREY_PERSON_STATE = (
    r"(?:\s+(?:a\s+bit|a\s+little|very|really|quite|all|pale|and|"
    r"has\s+gone|have\s+gone|had\s+gone|has\s+turned|have\s+turned|had\s+turned|"
    r"gone|goes|went|is|are|was|were|looks?|looked|turned))*")
GREY_BODY = re.compile(
    r"\b(?:lips?|mouth|tongue|face|cheeks?|skin|fingers?|fingertips?|hands?|nails?|feet|foot|"
    r"toes?|arms?|legs?|body)\b" + GREY_BETWEEN + r"\s+(?:grey|gray)\b"
    r"|\b(?:" + GREY_PEOPLE + r")\b" + GREY_PERSON_STATE + r"\s+(?:grey|gray)\b")

# Not an ambulance this minute, but not a wait-and-see either.
TODAY = (
    "confused", "drowsy", "very sleepy", "sleepy and", "temperature of 40", "40 degrees",
    "39 degrees", "39.5 degrees", "temperature of 39", "temperature of 39.5",
    "very hot to touch", "burning up", "hit his head", "hit her head",
    "hit their head", "banged his head", "banged her head", "fell and hit",
    "fell down the stairs", "wont stop bleeding", "wont stop vomit", "dehydrated",
    # Dehydration shows in the nappy: a dry baby is the sign, not a child who skipped a meal.
    "not had a wee", "hasnt had a wee", "hasnt done a wee", "hasnt been for a wee",
    "no wet nappy", "dry nappy", "not passing urine",
)

# Something in the throat that stops the air or the voice: a nut, a sweet, a toy. "my son cant
# talk yet" and "my daughter has a sore throat" name no stuck object and are not this.
STUCK = re.compile(
    r"\bstuck\b[^.?!]{0,30}\bthroat\b|\bthroat\b[^.?!]{0,30}\bstuck\b"
    r"|\b(?:cant|can't|unable to|couldn't|couldnt) (?:talk|speak|breathe)\b[^.?!]{0,25}\bthroat\b"
    r"|\bthroat\b[^.?!]{0,25}\b(?:cant|can't|couldn't|couldnt) (?:talk|speak|breathe)\b"
    r"|\bcant get it out\b|\bcan't get it out\b"
    r"|\bturning purple\b|\bgoing purple\b|\bgone purple\b")

# Something swallowed: the verb is ordinary, the object decides. A chemical is an ambulance,
# a medicine or a small object is a call today, and lunch is neither.
INGEST = frozenset("""
    swallowed swallow swallowing ate eaten eating drank drunk drinking chewed chewing
    licked sucking sucked gulped gulping sipped downed
""".split())
CHEMICAL = ("washing tablet", "washing pod", "laundry tablet", "laundry pod", "dishwasher tablet",
            "detergent", "bleach", "antifreeze", "drain cleaner", "oven cleaner", "disinfectant",
            "weedkiller", "weed killer", "screenwash", "screen wash", "paint thinner", "methanol",
            "hand sanitiser", "hand sanitizer", "white spirit", "caustic",
            # The bottle under the sink or on the dressing table: all of them are a 999 call.
            "paint", "air freshener", "perfume", "aftershave", "mouthwash", "nail polish",
            "nail varnish", "polish remover", "vape", "e-liquid", "eliquid", "e-cigarette",
            "lighter fluid", "petrol", "paraffin", "turps", "turpentine", "caustic soda")
MEDICINE = frozenset("""
    tablet tablets pill pills capsule capsules paracetamol ibuprofen aspirin medicine medicines
    painkiller painkillers supplement supplements vitamins antidepressant antidepressants
    methadone insulin codeine morphine steroids
""".split())
SMALL_OBJECT = ("battery", "batteries", "magnet", "magnets", "coin", "marble", "bead", "button",
                "sim card", "screw", "drawing pin", "earring", "lego")

# The state words that are also ordinary English. "my wife is fitting the new door", "my sister is
# unresponsive to my texts", "my daughter is confused by her homework": the word is a verb or a
# figure of speech, and what follows it says so. A preposition straight after the state word means
# the state is not about a body, with one exception worth keeping: "unresponsive to pain".
AMBIGUOUS = ("unresponsive", "not responding", "no response", "limp", "floppy", "fitting",
             "confused", "drowsy", "burning up", "very hot to touch")
AMBIGUOUS_CUES = AMBIGUOUS + ("wont wake", "won't wake", "cant wake", "can't wake", "not waking",
                              "isnt responding", "isn't responding", "isnt responsive",
                              "isn't responsive", "not responsive")
# Which word after the state word says it is not about a body. `to`, `by`, `about`, `from`, `into`
# and `of` are never about a body once something follows them (`unresponsive to my texts`,
# `confused by her homework`). `in`, `with` and `for` are, depending on what comes next:
# `fitting in well at school` is a joiner, `fitting in the bath` is a body; `fitting for a minute`
# is a duration; `fitting with the curtains` is a fitter. `on` is a place — `unresponsive on the
# floor` is a body — so it never counts.
NOT_A_BODY = frozenset("to by about from into of".split())
MANNER = frozenset("well nicely easily fine ok okay perfectly together up out round around".split())
# The degree words that can settle a state word on their own: "fitting nicely", "fitting well",
# "fitting fine" and "fitting perfectly" are how a thing is going - a child settling in at nursery,
# a game coming together - not a body tonight. They are the words the safety module's own fit arm
# reads, so one list decides both layers.
SETTLING = frozenset("well nicely easily fine perfectly beautifully smoothly brilliantly".split())
# `ok` and `okay` are not here: they are what people say when they are asking ("fitting ok?"), so
# they fall through to MANNER below and the fit keeps its ambulance.
CALENDAR = frozenset("today yesterday lately recently nowadays".split())
# A second clause after the manner word is the red flag, not the manner: "fitting nicely but still
# having them", "fitting well and then sleeping for hours". Those go back to the safety module,
# whose card has the cushion and the timing in it, instead of stopping here at the generic 999.
SECOND_CLAUSE = re.compile(r"(?:but|and|then|so|because|yet|though|when)\b")
# ...and the place a child settles into leaves it a manner: "fitting in nicely at nursery".
SETTLING_PHRASES = re.compile(
    r"(?:at|in|into|with)\s+(?:the\s+|his\s+|her\s+|their\s+|our\s+|a\s+)?(?:new\s+)?"
    r"(?:nursery|preschool|playgroup|school|class|clubs?|teams?|groups?|other\s+kids|the\s+others)\b")

PLACE = frozenset("""
    floor ground bed bath sofa settee stairs street garden ward car cot pram pushchair chair
    table hospital home room arms lap arms shoulders knees chest hands
""".split())
OBJECT_WORD = frozenset("""
    it them the a an my our his her their its this that these those new some carpet door floor
    tiles kitchen bathroom wardrobe blind window shelves shelf units sink sofa curtains decor
""".split())
# What someone burning up or floppy can be with: a sign on the body, not a thing in the hand.
SYMPTOM = frozenset("""
    fever temperature temp cold flu cough rash pain headache seizure shivers sweat sweats
""".split())
# The ordinary reasons a child is not themselves for a minute, after `when`/`whenever`.
ORDINARY_STATE = frozenset("""
    tired sleepy asleep hungry teething crying cross grumpy upset angry excited playing bored
    told naughty tantrum tantrums whingey whinging
""".split())
DURATION = frozenset("minute minutes min hour hours day days week weeks month months year years".split())
# The channels a person is unresponsive *on*: "my mum is unresponsive on the group chat" is a reader
# saying nobody got a reply. A place is still a body - "unresponsive on the floor" rings - so `on`
# is read by what it introduces, like `in` and `with` above.
ONLINE = frozenset("""
    chat whatsapp messenger facebook instagram twitter tiktok app forum thread threads messages
    texts email emails phone phonecalls slack discord reddit linkedin zoom teams skype group
    groups feed forum list mailing
""".split())


def _not_a_body(rest, before=""):
    """True when what follows the state word says the state is not about a body."""
    words = rest.split()
    if not words:
        return False
    first = words[0]
    second = words[1] if len(words) > 1 else ""
    third = words[2] if len(words) > 2 else ""
    if first in NOT_A_BODY:
        if first == "to" and (second in TO_PAIN or (second in ("the", "any", "some", "his", "her")
                                                    and third in TO_PAIN)):
            return False
        if first == "to" and _fed_and_unresponsive(before, rest):
            return False
        return True
    if first.strip(".,!?;:") in SETTLING:
        # A degree word straight after the state word says how a thing is going, not a body
        # tonight: "my son is fitting nicely" at nursery rang the ambulance. A fit is bare - it is
        # followed by `now`, `again`, `since`, a time, a number, or nothing, and all of those still
        # ring. `up`, `out`, `round` and `around` name a place ("my son is fitting up in his room")
        # and `together` names an assembly, so none of them settle anything on their own.
        # A manner word is a manner on its own, with a calendar word after it, or with the place
        # being settled into. A second clause after it ("but still having them") is a fit that is
        # still going: that goes back to the safety module, whose card has the cushion and the
        # timing, and ringing the same line here with the generic 999 threw that away. A place of
        # its own after it ("in the car") is a fit in that place, and it rings here.
        tail = " ".join(words[1:]).strip(" .,!?;:")
        if not tail or tail in CALENDAR:
            return True
        if SECOND_CLAUSE.match(tail):
            return True
        return bool(SETTLING_PHRASES.match(tail))
    if first == "together" and second in ("a", "an", "the", "my", "our", "his", "her", "their",
                                          "some", "these", "those", "this"):
        # "my son is fitting together a lego set" is a child assembling; a bare `fitting together`
        # is a fit, and it rings.
        return True
    if first in ("when", "whenever"):
        # "my baby goes floppy when shes tired", "unresponsive when hes told off": an ordinary state
        # read by what follows, not a body tonight. `when i talk to her` names no such state.
        return bool(set(words[:6]) & ORDINARY_STATE)
    if first == "in":
        if second in ("with", "at"):
            # "fitting in with the new baby", "fitting in at his new school": settling in.
            return True
        if second in MANNER and second not in PLACE:
            return True
        if second in ("the", "a", "an", "his", "her", "their", "my", "our"):
            return third not in PLACE
        return False
    if first == "with":
        if second in ("a", "an", "the"):
            # "burning up with a fever" is a body; "burning up with the old letters" is not.
            return third not in SYMPTOM
        return second in OBJECT_WORD
    if first == "on":
        if second in ("the", "a", "an", "my", "his", "her", "their", "our", "this", "that"):
            return third in ONLINE
        return second in ONLINE
    if first == "for":
        return second in DURATION or (second in ("a", "an", "one", "two", "half") and third in DURATION)
    return False
# The same shape one level up: `cant wake` needs the person as its object. "i cant wake up in the
# mornings" is the speaker's own sleep, and `my wife died last week and i cant wake up` is grief.
WAKE_CUES = ("wont wake", "won't wake", "cant wake", "can't wake", "not waking")
WAKE_OBJECT = frozenset({
    "him", "her", "them", "it", "my", "your", "his", "our", "their", "the", "this", "that",
}) | {
    "mum", "mam", "mom", "mother", "dad", "father", "son", "daughter", "baby", "toddler",
    "child", "kid", "boy", "girl", "nan", "nana", "gran", "granny", "grandma", "grandad",
    "grandpa", "husband", "wife", "partner", "brother", "sister", "friend", "uncle", "aunt",
    "niece", "nephew", "newborn", "patient",
}
DEATH = ("died", "dies", "dying", "passed away", "passed on", "funeral", "buried", "cremation",
         "bereave", "widow", "death", "killed")

# The state words that are verbs too, and take an object: `fitting the new door`, `fitting me in
# tomorrow`. A fit is a bare verb - it is followed by `now`, `again`, `since`, a time, or nothing.
# `burning up` is a fever and also a way of saying you are getting through the old letters, so it
# takes an object like `fitting` does. A fever takes `with a fever`, which is a body.
VERBY = ("fitting", "burning up")
OBJECTISH = re.compile(
    r"^\s+(the|a|an|my|your|his|her|their|our|its|it|me|him|them|us|you|new|some|these|those|"
    r"this|that|another|two|three|four|five|one|carpet|door|floor|tiles|kitchen|bathroom|"
    r"wardrobe|blind|window|shelves|shelf|units|sink|sofa)\b")

CONFUSED_SIGN = re.compile(r"\b(suddenly|very|extremely|really|getting more|more)\b")
CONFUSED_AFTER = re.compile(r"^\s*(?:and|,|or)\b")

TO_PAIN = ("pain", "the pain", "any pain", "stimulus", "stimuli", "voice", "voices", "sound",
           "noise", "loud", "touch", "light", "nothing", "anything")

# A small person who is unresponsive *to a feed* is still a body, and `to` must not take the call
# away: "my baby is unresponsive to her milk" is a parent saying the baby will not wake after a
# bottle, and the line is the same red flag as "my baby is unresponsive" and as "not responding to
# her feed". A message after `to` still reads as not-a-body ("unresponsive to my texts" is a phone),
# and so does an adult's email or request. The subject decides, not the preposition.
SMALL_PERSON = frozenset("""
    baby babies newborn infant toddler child kid son daughter boy girl little
""".split())
A_FEED = frozenset("""
    milk formula feed feeds feeding bottle breast solids weaning
""".split())


# A blocked nose is not an airway, in the first person or the third: "my baby cant breathe through
# her nose" is a stuffy nose and was answered with an ambulance. The phrase is taken out of the
# line before the state list reads it, so anything else in the line - turning blue, floppy, a
# seizure - still rings on its own words.
NOSE_BREATH = re.compile(
    r"\b(?:can'?t|cannot|couldn'?t|could\s+not|struggling|hard|unable|not|trouble)"
    r"\s+(?:to\s+)?breath\w*[^.?!]{0,18}?\bthrough\b[^.?!]{0,12}?\bnose\b")

# ...but only while there is nothing else in the line to ring for. These are the signs that a
# parent's line about a nose can carry and still be an ambulance: going blue, grey lips, grunting,
# ribs sucking in, limp, hard to wake. With one of them the phrase stays in and the rest of the
# line reads exactly as it did before the fence, because a baby who is going blue is not a baby
# with a stuffy nose. It lives here, once, because two places read it: this fence and
# `bot/modules/safety.py`, which decides whether the 999 stands.
NOSE_RED = (
    r"\b(?:going|turning|gone|looks?)\s+blue\b",
    r"\bblue\s+(?:lips|round\s+the\s+lips|in\s+the\s+face)\b",
    r"\bgrey\b", r"\bgray\b", r"\bgrunt\w*\b",
    # the ribs, and the chest that goes with them, in either order: "his ribs are sucking in",
    # "his chest is pulling in", "is pulling at her ribs"
    r"\bribs?\b[^.?!]{0,25}\b(?:suck\w*|pulling|pulling\s+in|drawing|recession)\b",
    r"\b(?:pulling|sucking|drawing)\s+(?:in|at)\b[^.?!]{0,25}\b(?:ribs?|chest)\b",
    r"\bchest\b[^.?!]{0,25}\b(?:pulling|sucking|drawing)\s+in\b",
    r"\blimp\b", r"\bfloppy\b", r"\bunresponsive\b", r"\bnot\s+responding\b",
    r"\bunconscious\b",
    r"\bhard\s+to\s+(?:wake|rouse|arouse|waken)\b",
    r"\bwont\s+wake\b", r"\bwon'?t\s+wake\b", r"\bnot\s+waking\b",
    # The same two facts in the words people type: "he collapsed laughing and wouldnt wake",
    # "she laughed so much she couldnt be woken", "my dad collapsed laughing and he is out cold".
    r"\b(?:wouldnt|wouldn'?t|didnt|didn'?t|never)\s+(?:wake|woke)\b",
    r"\b(?:couldnt|couldn'?t)\s+be\s+woken\b", r"\bisnt\s+waking\b", r"\bisn'?t\s+waking\b",
    r"\bout\s+cold\b",
    r"\bseizure\b", r"\bfitting\b", r"\bconvuls\w*\b",
    # "had a fit" is how a parent says a seizure, and "a fit of coughing" is not one: the noun
    # only counts with the verb in front, so the cough idiom keeps its own answer
    r"\b(?:had|has|having|with)\s+(?:a|another)\s+fit\b",
    r"\bsnoring\b", r"\bapnoea\b", r"\bapnea\b",
    r"\bnot\s+breathing\b", r"\bstops?\s+breathing\b",
    r"\bchoking\b", r"\bchokes?\b", r"\bcpr\b", r"\bambulance\b",
    # a fever is not an ambulance on its own, and it is not a stuffy nose either: it has its own
    # 111 answer, which only gets a look in while the line still reads as a breath line
    r"\bhigh\s+temperature\b", r"\btemperature\s+of\s+\d", r"\bburning\s+up\b",
)

# The same list as one expression, for the fence below.
NOSE_RED_BESIDE = re.compile("|".join("(?:%s)" % pattern for pattern in NOSE_RED))


def _fed_and_unresponsive(before, rest):
    """Whether this is a small person who will not respond to a feed."""
    who = re.sub(r"[^a-z ]", " ", before.lower()).split()[-3:]
    what = re.sub(r"[^a-z ]", " ", rest.lower()).split()[:4]
    return bool(set(who) & SMALL_PERSON) and bool(set(what) & A_FEED)

# A fit of coughing, of sneezing or of the giggles is not a seizure, and a child who has a fit every
# few months has epilepsy a doctor already knows about: both are ordinary lines that the state list
# above reads as a body on the floor. They stay an ambulance when anything else in the line is a
# sign, so "he had a fit of coughing and now he cant breathe" is still a call.
FIT_OF = re.compile(
    r"\bfits?\s+of\s+(?:cough\w*|sneez\w*|giggl\w*|laughter|laughing|screaming|crying|"
    r"the\s+giggles|rage|temper|anger|pique|panic|inspiration)\b")
FIT_ROUTINE = re.compile(
    r"\b(?:every\s+(?:few|couple\s+of|so\s+many)\s+(?:months|weeks|years)|twice\s+a\s+year|"
    r"once\s+a\s+year|a\s+(?:few|couple)\s+of\s+times\s+a\s+year|now\s+and\s+(?:then|again)|"
    r"occasionally|from\s+time\s+to\s+time|keppra|epilep\w*)\b")
# The signs that keep a routine fit, or a fit of coughing, an ambulance.
FIT_STILL_RINGS = ("cant breathe", "can't breathe", "not breathing", "stopped breathing",
                   "turning blue", "blue lips", "unconscious", "collapsed", "wont stop",
                   "won't stop", "isnt stopping", "isn't stopping", "keeps going", "ambulance",
                   "999", "on the floor", "shaking all over", "convulsing", "stiff")

# Cues unambiguous enough to answer on a bare `he`/`she`.
PRONOUN_SAFE = (
    "had a fit", "has a fit", "having a fit", "having fits", "keeps fitting", "kept fitting",
    "keeps having fits", "kept having fits", "not breathing", "stopped breathing", "unconscious",
    "went limp", "gone limp", "limp in my arms", "limp in her arms", "limp in his arms",
    "no pulse", "seizure", "convulsing", "choking", "overdose", "took too many", "collapsed",
    "cardiac", "isnt breathing", "isn't breathing",
)

# A worried parent asking whether a soft state is normal gets told what it is, not an ambulance:
# "my baby is floppy when sleepy, is that normal". The hard states are not asked this way, and if
# they are, "my mum is unresponsive, what do i do" still rings.
SOFT_STATES = frozenset({"floppy", "limp", "confused", "drowsy", "burning up", "very hot to touch",
                         "very sleepy", "sleepy and"})
NORMAL_ASK = re.compile(
    r"\b(?:is that|is it|is this|should i|do i need to)\b[^.?!]{0,40}"
    r"\b(?:normal|ok|okay|fine|worry|worried|worrying|serious|dangerous)\b")

# A past marker means it is not happening now: "my son fell down the stairs 2 yrs ago" is not a
# call today, and "he banged his head last year" is not either. `last night`, `yesterday` and
# `this morning` are still recent enough to keep the today line.
PAST_MARK = re.compile(
    r"\b(?:ago|last (?:year|month|summer|winter|autumn|spring|week)|in (?:19|20)\d\d|"
    r"years back|months back|"
    # Their own childhood is the commonest one: "i had a fit when i was a kid" is a memory, not a
    # call today, so the first person is in here with the third, and the age is enough by itself.
    r"when (?:i|he|she|they|it|we) (?:was|were) (?:a |an )?"
    r"(?:baby|babies|toddler|tot|child|kid|teenager|born|little|small|young|tiny|"
    r"at school|\d+|one|two|three|four|five|six|seven|eight|nine|ten)|"
    r"as a (?:baby|child|kid|toddler|teenager)|used to)\b")

def reads_as_a_story(clean):
    """Whether the line puts the event firmly in the past, so no ambulance is needed now.

    `he had a fit last year`, `my mum collapsed last year`, `my dad was unconscious for a minute
    years ago` are stories. Something still going on ("... and he is still on the floor now"),
    happening now ("... and is unconscious now") or said to have passed ("... and now hes fine")
    is not a story, so the answer stays.
    """
    return bool(PAST_MARK.search(clean)) and (
        not NOW_WORDS.search(clean) or bool(ALL_BETTER.search(clean)))


# A near miss is worth a call today, not an ambulance: "my mum nearly had a seizure".
NEARLY = (" almost ", " nearly ", " like to have ")

# The state words above are about now, so a line that says outright it was years ago is a story:
# "he had a fit last year", "my mum collapsed last year", "my dad was unconscious for a minute
# years ago". `last night`, `yesterday` and `this morning` are recent enough to keep the answer.
# Something said to be continuing ("... and he still is", "... and he is on the floor now") or
# happening now ("... and is unconscious now") keeps it, and "and now hes fine" takes it back.
NOW_WORDS = re.compile(
    r"\b(?:now|right now|still|since|today|tonight|this (?:morning|evening|afternoon)|"
    r"at the moment|any ?more)\b")
ALL_BETTER = re.compile(
    r"\b(?:now|since|and)\b[^.?!]{0,16}\b(?:he|she|they|it|i|we)\s*(?:is|are|was|were|'s)?\s*"
    r"(?:fine|ok|okay|better|recovered|alright|back to normal|himself again|herself again)\b|"
    r"\b(?:now|since)\s*(?:hes|shes|theyre|its|im)\s*(?:fine|ok|okay|better|recovered|alright)\b")

# A question about a state is asked to be told what it is, not to be told to ring 999: "my nan is
# confused about her medication". The states in NOW are an ambulance however they are phrased.
ASKING = (" about ", " what ", " why ", " how ", " should i", " can i", " is that ", " do i")

NOW_REPLIES = (
    "Don't wait on that: ring 999 or 911 now and stay on the line with them. Put them on "
    "their side, tilt the head back so the airway stays open, and don't leave them alone.",
    "That needs an ambulance now. Ring 999 or 911, say exactly what you're seeing, and keep "
    "them on their side while you wait; if they stop breathing normally, start CPR and keep "
    "going until help comes.",
    "Ring 999 or 911 straight away and don't try to drive them in yourself. Stay with them, "
    "check they're breathing, and follow what the call handler tells you.",
)

POISON_NOW_REPLIES = (
    "Ring 999 or 911 now and say what they swallowed and how long ago; keep the packet or the "
    "bottle to read out. Don't make them sick and don't give them anything to drink.",
    "That's a 999 call now, and have the container ready to name to the handler. Keep them "
    "sitting up, wipe their mouth but don't rinse it, and don't try to make them vomit.",
)

POISON_TODAY_REPLIES = (
    "Ring 111 now rather than waiting, and have the packet in your hand: they will tell you "
    "whether they need to be seen. Don't make them sick. If they go sleepy, drool, cough or "
    "struggle to breathe, that's 999.",
    "Get advice on that today - 111 or the poisons line, with the packet to hand - and watch "
    "them closely for the next few hours. Anything drowsy, vomiting, drooling or breathing "
    "oddly means 999.",
)

TODAY_REPLIES = (
    "Get that looked at today rather than waiting: ring 111 or your GP now, and tell them "
    "just what you told me. If they get drowsy, hard to wake, or their breathing changes, "
    "that's 999.",
    "That's worth a call today - 111 or the doctor - and mention how it started. If they get "
    "harder to wake or go blue or floppy, ring 999 instead of waiting.",
)


# "she has a limp", "walks with a limp": the word is a gait, and the leg is not an emergency.
GAIT_BEFORE = frozenset("a an the this that his her my your their our".split())


def _named_a_gait(clean, start):
    """True when the word before the state word makes `limp` a leg rather than a body."""
    before = clean[:start].split()
    return bool(before) and before[-1] in GAIT_BEFORE


# A body that is limping is walking, and a body that went limp is not. The cue is looked up with
# find(), so `limp` is found inside `limping`, `limped` and `limps` as well: "my son is limping" had
# the word before the cue be "is" rather than "a", so _named_a_gait() said no and a sprained ankle
# got the ambulance. The walk is the stem of the word, not a word before it, so it is read here.
GAIT_STEM = re.compile(r"(?:ing|ed|s)\b")


def _walking(rest):
    """True when what follows the `limp` cue is the rest of a walk: limping, limped, limps."""
    return bool(GAIT_STEM.match(rest.lstrip()))


# "wont wake up for work", "for school", "at 7" is a lazy morning, not a coma. `up` on its own is
# a body: "my baby wont wake up" is the ambulance.
WAKE_OCCASION = frozenset("for to at on before until by".split())
FIGURE_OF_SPEECH = ("at the idea", "at the thought", "at the prospect", "at the mention")


def _signs_a_body(clean, phrase, rest, start=0):
    """Whether an ambiguous state word is about a body in this line."""
    if phrase == "limp":
        return not _named_a_gait(clean, start) and not _walking(rest)
    if phrase in WAKE_CUES:
        words = rest.split()
        if words and words[0] == "up":
            words = words[1:]
        if not words:
            return True
        if words[0] in WAKE_OCCASION:
            # "wont wake up for work" is a heavy sleeper; "wont wake up for his feed" a sleepy one.
            return False
        return bool(set(words[:5]) & WAKE_OBJECT)
    if phrase == "burning up":
        return not any(rest.lstrip().startswith(phrase_) for phrase_ in FIGURE_OF_SPEECH)
    if phrase == "confused":
        return bool(CONFUSED_SIGN.search(clean) or CONFUSED_AFTER.match(rest))
    return True


def _first(clean, phrases):
    """The first cue the line really carries.

    A cue from AMBIGUOUS_CUES is dropped when what follows it says it is not about a body:
    `unresponsive to my texts` is a phone, `unresponsive to pain` is a body.
    """
    for phrase in phrases:
        start = clean.find(phrase)
        while start >= 0:
            rest = clean[start + len(phrase):]
            if phrase not in AMBIGUOUS_CUES:
                return phrase
            if not _signs_a_body(clean, phrase, rest, start):
                start = clean.find(phrase, start + 1)
                continue
            if phrase in VERBY and OBJECTISH.match(rest):
                start = clean.find(phrase, start + 1)
                continue
            if not _not_a_body(rest, clean[:start]):
                return phrase
            start = clean.find(phrase, start + 1)
    return None


# A line about a pet is not about the family word further along it: the subject is the nearest
# noun, and a pet named before the first family word is the one the state word belongs to.
PETS = frozenset("""
    dog dogs puppy puppies cat cats kitten kittens rabbit rabbits bunny hamster gerbil guinea pig
    parrot budgie bird birds fish goldfish tortoise turtle snake lizard ferret pony horse horses
    chinchilla
""".split())


# A body word can be the frame of a joke: "he collapsed laughing" is a good night out, and it was
# reaching the emergency line because "collapsed" is on the state list. The laugh has to be
# attached to the word, so "he collapsed at work" and "she went down in the street" keep the
# ambulance.
LAUGH_IDIOM = re.compile(
    r"\b(?:collaps\w*|went down|doubled over|fell about|fell over)\s+"
    r"(?:laughing|giggling|in (?:a )?(?:fit|stitches|hysterics)|with laugh\w*|helpless)\b")


def _pet_is_the_subject(clean):
    words = WORD.findall(clean)
    for i, word in enumerate(words):
        if word in FAMILY:
            return False
        if word in PETS:
            return True
    return False


def reply_for(text, memory=None):
    """A careful line when someone they look after is in trouble, else None."""
    clean = " ".join(str(text or "").lower().split())
    # A dream of the thing is not the thing, and this module answers before safety is asked:
    # "i dreamt my baby stopped breathing" was the ambulance line for a baby who was asleep
    # beside the person who dreamed it. The dream has its own module; anything that says it is
    # happening now ("still", "right now", "woke up") is in the waking world and keeps the line.
    if _dream is not None and _dream.a_dream_is_not_happening(clean):
        return None
    if NOSE_BREATH.search(clean) and not NOSE_RED_BESIDE.search(clean):
        # A blocked nose is not an airway. The phrase is *not* taken out of the line and left for
        # whatever answers the remainder: "my baby is struggling to breathe through his nose" was
        # read as "my baby is struggling" and answered with the fertility card, which is worse
        # than the ambulance it replaced. The whole line belongs to the knowledge rows - the
        # blocked-nose row and the baby's own - so this module stands down and they answer it.
        return None
    words = set(WORD.findall(clean))
    # A grey body written with only a pronoun is the one colour line with no noun of its own:
    # "hes gone grey" names nobody and no part, so the family words above cannot see it and the
    # cue list does not hold a colour. The body test is the same one the card uses, and a pet is
    # still set aside below ("my old dog is 12 and hes gone grey").
    pronoun_grey = bool(words & {"he", "she", "hes", "shes"}) and bool(GREY_BODY.search(clean))
    if (not words & FAMILY and not pronoun_grey
            and not (words & {"he", "she"} and _first(clean, PRONOUN_SAFE))):
        # A relative, or `he`/`she` with a cue that cannot be anything but a body: "he had a fit
        # this morning". `they` is left out — "they are fitting new windows" is a builder.
        return None
    if PRO_ANSWERING.search(clean) and not BODY_IN_THE_ROOM.search(clean):
        return None
    if _pet_is_the_subject(clean):
        # "my cat is fitting in with the new baby": `baby` is a family word but not the subject.
        return None
    if (FIT_OF.search(clean) or FIT_ROUTINE.search(clean)) and not any(
            mark in clean for mark in FIT_STILL_RINGS):
        # A fit of coughing or the giggles, or the fits a child has every few months, are not the
        # state list's body on the floor.
        return None
    if LAUGH_IDIOM.search(clean):
        # The laugh is the cause and the collapse is the effect: a joke, not a body on the floor.
        return None
    if any(mark in clean for mark in DEATH):
        # A death in the line is the loss module's, however the rest of it reads: "my wife died
        # last week and i cant wake up in the morning" is grief, not an ambulance.
        return None
    nearly = any(hedge in " " + clean + " " for hedge in NEARLY)
    swallowed = bool(words & INGEST)
    # A paintball is a soft pellet, not a bottle of paint.
    chem_text = clean.replace("paint ball", " ").replace("paintball", " ")
    chemical = swallowed and any(phrase in chem_text for phrase in CHEMICAL)
    poisoned = swallowed and not chemical and (
        bool(words & MEDICINE) or any(phrase in clean for phrase in SMALL_OBJECT))
    blue = BLUE_LOOSE.search(clean) and BLUE_BODY.search(clean)
    grey = GREY_LOOSE.search(clean) and GREY_BODY.search(clean)
    now = None if nearly else (_first(clean, NOW) or ("is blue" if blue else None)
                              or ("is grey" if grey else None)
                              or ("airway" if STUCK.search(clean) else None)
                              or ("chemical" if chemical else None))
    if now and reads_as_a_story(clean):
        now = None
    if now in SOFT_STATES and NORMAL_ASK.search(clean):
        now = None
    today = None
    if "?" not in clean and not any(ask in " " + clean + " " for ask in ASKING):
        today = _first(clean, TODAY) or ("swallowed" if poisoned else None)
        if today and PAST_MARK.search(clean):
            today = None
    pools = {"chemical": POISON_NOW_REPLIES, "swallowed": POISON_TODAY_REPLIES}
    for state, options in ((now, NOW_REPLIES), (today, TODAY_REPLIES)):
        options = pools.get(state, options)
        if state:
            turns = (memory or {}).get("turns") or []
            recent = {t.get("bot") for t in turns[-5:] if isinstance(t, dict)}
            fresh = [o for o in options if o not in recent] or list(options)
            seed = len(turns) * 7919 + sum(ord(c) for c in clean)
            return random.Random(seed).choice(fresh)
    return None
