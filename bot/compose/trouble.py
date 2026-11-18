"""Something has gone wrong and they are telling you about it.

A person who says "my washing machine is leaking" or "my knee has been aching for a week" is not
making conversation: they are handing you a problem, and the friendliest thing you can do is ask
the one question that gets it moving. On main every one of those lines got a line that fits
anything - "Noted! What would be most useful to talk about?", "Got it. Is there anything you'd
like a hand with?" - which reads as if nobody was listening.

So this answers the trouble itself, from a short pool: what is it doing, when did it start, what
have you tried. Two shapes, because a broken thing and an aching body want different questions:

* a thing that is not behaving - "my laptop wont turn on", "my boiler keeps cutting out"
* their own body - "my back pain keeps coming back", "I've had a cough for three weeks now"
* a setback they have not explained - "my cake was a disaster", "everything went wrong today"
  (the reading and the wording are bot/memory/setback.py: the question is what happened)

Every rule here is a guard against taking a turn that is not that:

* never a question (bot/understanding's kind is checked by the caller, and a question mark in the
  line is enough to stand aside): a line that asks something has its own reply;
* never a line asking for tips or advice - "my kid wont eet vegtables, any tips" is a plea, not
  a report, and "what's it doing exactly" would answer the wrong thing;
* **never a line about another person.** "my husband wont wake up", "my mum is having a sezure",
  "my baby has a temperature of 39 and is floppy" all name a body or a thing failing, and all of
  them are emergencies about someone else. Asking "when did it start?" there is far worse than a
  stock line, and the emergency read belongs to bot/modules/safety.py, not here. One word from
  OTHERS and this passes, whatever else the line says;
* a body reply needs the person themselves to be the one hurting ("i", "my <part>"), never a
  temperature or a symptom handed to a child;
* a thing reply needs something named to belong to them ("my", "our", "the", "it"), so "dead
  easy, mate" and "this heat is killing me" are small talk, not faults.
"""
import re
import string

from .badnews import reads_as_someones_death
from ..memory.setback import pool as _setback_pool, reading as _setback

# Another person in the line means it may be an emergency about them: safety's turn, not ours.
OTHERS = frozenset((
    "he", "she", "him", "her", "his", "hers", "they", "them", "their", "theirs",
    "mum", "mam", "mom", "mummy", "mummy", "dad", "daddy", "father", "mother", "parent",
    "son", "daughter", "child", "kid", "kids", "baby", "toddler", "teenager", "boy", "girl",
    "husband", "wife", "partner", "boyfriend", "girlfriend", "fiance", "fiancee",
    "nan", "nana", "gran", "granny", "grandma", "grandad", "grandpa", "grandparents",
    "brother", "sister", "sibling", "aunt", "uncle", "cousin", "nephew", "niece",
    "friend", "mate", "flatmate", "housemate", "neighbour", "neighbor", "colleague",
    "boss", "manager", "landlord", "landlady", "tenant", "carer", "nurse", "vet",
    "dog", "cat", "puppy", "kitten", "pet", "pup",
))

# The end of a thing, said the way people really say it: "our sofa has had it", "my old bike has
# had its day", "the kettle is done for". The thing is named in front of the words, and that is
# the whole of the reading: "ive had it" and "ive had it up to here" are the person's own limit
# rather than a machine's end (bot/compose/limit.py has that line), and "my mum has had it" is a
# person, which the someone-else fence in _shape takes away. The words are shared with A_DECLINE
# below, so the same shape is a fault here and nothing more than the decline there. "the mower
# died on me" is not one of them: "died" is already a fault word, and the wider pool's "tell me
# what it does" is the better question about a thing that stopped.
THE_END_OF_A_THING = r"""
      | (?:its|it's|mine|ours)\s+had\s+(?:it|its\s+day)
      | (?:mine|ours)\s+(?:has|have|had)\s+had\s+(?:it|its\s+day)
      | (?:my|our|the|this|that|these|those)\s+(?:[\w']+\s+){0,3}
          (?:has|have|had)\s+had\s+(?:it|its\s+day)
      | (?:my|our|the|this|that|these|those)\s+(?:[\w']+\s+){0,3}
          (?:is|are|was|were)\s+done\s+for
"""

# A thing that has stopped for good, said with the verb of putting a flat in boxes: "the oven has
# packed up", "the boiler packed in last week", "my tv gave up". The verb is the trouble only when
# the thing is the one doing it, so the thing is named in front of it: "i packed up my flat", "we
# packed up the tent", "i packed in my job" and "i gave up my seat" are the person doing something,
# and on main the bare word read them as a fault of a thing ("i packed in my job" was answered
# "Ugh, those are fiddly. How long has it been like that?").
A_THING_PACKED_UP = r"""
      | (?:mine|ours)\s+(?:has|have|had)?\s*(?:packed\s+(?:up|in)|(?:gave|given)\s+up)
      | (?:the|my|our|this|that|his|her|their|it|its)\s+(?:[\w']+\s+){0,3}
          (?:has|have|had)?\s*(?:packed\s+(?:up|in)|(?:gave|given)\s+up)
"""

# A thing of theirs that has gone into a bad state, said with the state rather than a fault verb.
# This is the commonest way people describe a thing that wants fixing and the vocabulary above had
# none of it, so the whole class fell past this module to the pool for an ordinary day:
# "my bike chain has seized up" was answered "Good to hear. What was the best bit?", "my oven door
# glass has gone all black and burnt on" with "Thanks for telling me - I'm here if you want to dig
# into any of that" and "the glass on my oven door is burnt on" with "Got it. Is there anything
# you'd like a hand with?". A cheer at a seized chain is the worst reply the bot can give, and it
# is not the fault of the day pool: no reader had called the line a fault at all.
#
# So the shape is the state, not the topic: what has happened to the thing. Only states that mean
# damage are here - black from burning, mould, rust, split, seized, hanging off - and not the
# states a thing goes into by itself (a hair going grey, the weather turning cold), which are news
# or a remark rather than a fault to talk through.
THING_STATE = r"""
    (?:has|have|had|is|are|was|were)\s+
      (?:(?:gone|got|become|turned)\s+)?
      (?:all\s+|a\s+bit\s+|a\s+lot\s+|really\s+|very\s+|quite\s+|so\s+|completely\s+
         |totally\s+|properly\s+|now\s+)?
      (?:a\s+|an\s+)?
      (?:
          black|brown|green|rusty|mouldy|moldy|mildewed|lumpy|soggy|slimy|sticky|greasy
        | furry|furred|scaled|pitted|warped|brittle|cracked|frayed|threadbare|bubbled
        | blistered|peeling|discoloured|discolored|crusty
        | burnt|burned|scorched|seized|rusted|corroded|perished|split|snapped|melted|bent
        | stuck|jammed|solid|knackered|kaput|buggered|stiff|dropped|flat
        | yellow|patchy|faded|bald|rip(?![\s-]+off\b)
        | crack|hole|tear|dent|patch
      )
      (?:\s+(?:on|up|through|off|shut|together|solid|apart|open|down|in|out))?
  | burnt\s+on
  | blown\s+(?:down|off|out|over|away)
  | (?:hanging|fell|fallen|come|coming|pulled)\s+(?:off|away|loose|apart|down|open)
  | conked\s+(?:out|off)
"""

# A plant going brown or green is the season and the weather, not a fault to talk through: "the
# leaves have gone brown" is an autumn remark. The colour words below are the mould and the rust
# on a made thing, so a growing thing named in the line is left to the garden reading.
GROWING = frozenset("""
    leaves leaf grass lawn lawns plants plant tree trees hedge hedges shrub shrubs bush bushes
    fruit veg vegetables tomatoes tomato potatoes crops flowers flower garden allotment ivy
    moss weeds weed field fields meadow hedgerow
""".split())

# The state block on its own, so a reading can tell a state of a thing from the fault verbs above:
# "my knee is stiff" is the body said in the same shape, and a knee wants the sore reading.
THING_STATE_ONLY = re.compile(r"\b(?:" + THING_STATE + r")\b", re.X)

# A thing is not doing what it should. Only the words that mean a fault, so "i put her to sleep
# at 7" and "my sister is staying for a fortnight" stay out of it.
THING = re.compile(r"""
    \b(?:
        wont | won't | doesn'?t\s+work | isnt\s+working | isn'?t\s+working
      | not\s+(?:working|responding|turning\s+on|charging|draining|connecting|booting)
      | stopped\s+working | stopped\s+charging
      | broke | broken | broke\s+down | bust | faulty | on\s+the\s+blink | playing\s+up
      | leak(?:s|ing|ed)? | drain(?:s|ing)? | soaking | dripping | blocked | clogged | jammed | stuck
      | keeps?\s+(?:freezing|crashing|cutting|dropping|stopping|going\s+off|calling|
                    restarting|turning\s+off|coming\s+up|showing|flashing)
      | cutting\s+out | crashing | froze | frozen | freezes | collapses? | collapsed
      | makes?\s+a\s+noise | making\s+a\s+noise | noisy | rattl(?:es|ing|ed)
      | die(?:s|d)? | dead | flat\s+(?:tyre|battery) | slow | sluggish | overheats? | overheating
      | error | glitch(?:y|es)? | corrupt(?:ed)? | wont\s+connect | no\s+signal
      | needs?\s+(?:a\s+)?(?:fixing|servicing)
      | on\s+its\s+way\s+out
      | on\s+(?:its|his|her|their)\s+last\s+legs
      | clapped\s+out | seen\s+better\s+days | knackered
      | went\s+bang | blew\s+(?:a\s+)?fuse
""" + THE_END_OF_A_THING + A_THING_PACKED_UP + r"""
      | """ + THING_STATE + r"""
    )\b
""", re.X)

# A thing that will not do its job, said as the person's own inability: "i cant get my washing
# machine to spin", "cant get the app to open", "i cant get my printer working". The thing sits
# between the words, so the fault is named even when no fault word is: "spin" is not a fault on
# its own, but nothing else is meant by "i cant get my washing machine to spin". The verb at the
# end is what makes it a fault, so "i cant get out of bed", "i cant get to the shops" and
# "i cant get my head around it" stay out of it, and so does anything about another person.
CANT_GET = re.compile(r"""
    \b(?:can'?t|cannot|can\s+not|couldn'?t|could\s+not|unable\s+to|not\s+able\s+to)
      (?:\s+seem\s+to)?
      \s+(?:get|getting|make|making|keep|keeping|stop|stopping)\b
      (?:\s+[\w']+){1,4}?      # the thing: "my washing machine", "the app", "this printer"
      \s+(?:to\s+(?:work|job|run|go|start|stop|spin|turn|open|close|load|boot|charge
                      |connect|pair|sync|print|scan|save|drain|heat|light|fire|play|update
                      |install|download|upload|respond|unlock|switch|move|boil|cook|rise
                      |freeze|cool|record|log\s?in)
          |working|going|started|running|charged|connected|opening|booting)
""", re.X)

# Their own body, not doing what it should.
BODY = re.compile(r"""
    \b(?:
        hurt(?:s|ing)? | ach(?:e|es|ing|y) | sore(?:ness)? | pain(?:s|ful)? | stiff(?:ness)?
      | swell(?:s|ing|ings|en)? | tender(?:ness)? | numb | itch(?:y|es|ing)? | throbbing
      | migraines? | headaches? | toothaches? | cough(?:ing)? | rashes?
      | cramp(?:s|ing)? | bleeding | bled | sprain(?:s|ed)? | bruis(?:e|es|ed)
      | stubbed | burnt | burned | infection
    )\b
""", re.X)

# "pain", "sore" and "stiff" also mean a nuisance: "my job is a pain" is not a body. When one of
# those is the only ache word in the line, the line has to name a body part of theirs to be the
# body's trouble; "i am in pain" and "i have a pain in my side" still count, because the line is
# not about a thing of theirs.
FIGURATIVE = re.compile(r"\b(?:pain(?:s|ful)?|sore(?:ness)?|stiff(?:ness)?)\b")
# "my job is a pain", "my phone is painful to use", "my old essay was a real pain": the thing
# they own is said to be a nuisance, and there is no body in the line at all.
NUISANCE = re.compile(r"\b(?:my|our)\s+\w+(?:\s+\w+){0,2}\s+(?:is|are|was|were|'s)\s+"
                      r"(?:(?:a|real|right|such|quite|so|very|bit\s+of|proper|little)\s+){0,2}"
                      r"(?:pain|pains|painful|sore|stiff)\b")

# A body part that is theirs, which is what makes it their own trouble.
BODY_PART = frozenset((
    "back", "knee", "knees", "shoulder", "shoulders", "ankle", "ankles", "wrist", "wrists",
    "neck", "hip", "hips", "leg", "legs", "arm", "arms", "foot", "feet", "toe", "toes",
    "tooth", "teeth", "gum", "gums", "ear", "ears", "eye", "eyes", "chest", "stomach",
    "belly", "throat", "head", "skin", "hand", "hands", "finger", "fingers", "jaw",
    "sinus", "sinuses", "shoulder blade", "heart",
    # The parts a person names when it is their own ache, in the number they say it in: "my ribs
    # are killing me" and "my elbow is sore" were an echo of the line back, because the part was
    # not on this list. Nothing here is a word that is also something else the bot answers.
    "elbow", "elbows", "forearm", "forearms", "thigh", "thighs", "calf", "calves",
    "shin", "shins", "heel", "heels", "rib", "ribs", "collarbone", "collarbones",
    "hamstring", "hamstrings", "groin", "cheek", "cheeks", "chin", "eyebrow", "eyebrows",
    "knuckle", "knuckles", "tailbone", "spine", "tonsils",
))

# A fresh injury or an acute symptom is not a chore to work through: it may be an emergency, and
# "what have you tried for it" or "is it getting better or worse" is the wrong thing to say to
# someone whose lips are swelling or who has just come off a bike. Those turns belong to
# bot/modules/safety.py, so this stands aside for them.
ACUTE = re.compile(r"""
    \b(?:
        burn(?:s|ed|t)? | scald(?:s|ed)? | swell(?:s|ing|ed)? | swellings?
      | throat | lips? | tongue | breath(?:e|es|ing|less)? | choking | choked
      | bleed(?:s|ing)? | bled | numb | tingling | vision | sight | blurred
      | fell | fallen | fall(?:s|ing)? | collapsed | collapse | unconscious | dizzy | fainted
      | cut(?:s)? | gash | wound | crushed | twisted | sting(?:s|ing)?
      | rash(?:es|y)? | pois(?:on|oned|oning) | overdose | pill(?:s)? | seizure | sezure
      | can'?t\s+see | cant\s+see | can'?t\s+move | cant\s+move | can'?t\s+breathe
    )\b
""", re.X)

# A bone is not an appliance. "broken" is the word for a washing machine and for a wrist, so on
# its own it says nothing about which: every line here used to be read as an injury, and "my
# washing machine is broken" got the acknowledgement instead of "what's it doing exactly".
# A fracture word only stands this aside when there is a body for it to belong to, and the body
# words are a little wider than BODY_PART because ribs and a collarbone break and are not what
# BODY_PART is for.
FRACTURE = re.compile(r"\b(?:broken|fractures?|fractured)\b")

# The words a thing breaks with, and a part of someone's life breaks with the same words:
# "my marriage broke down" is not a machine to take apart, and "my laptop broke down" is.
BREAKS = re.compile(r"\b(?:broke|broken|broke\s+down|breaks|breaking|bust|busted)\b")
BONE = frozenset((
    "rib", "ribs", "collarbone", "collar", "pelvis", "spine", "shin", "thigh", "heel",
    "elbow", "elbows", "bone", "bones", "shoulder", "jaw", "skull", "tailbone", "wrist",
    "ankle", "hip", "kneecap", "knuckle", "knuckles",
    # The face breaks and none of these is in BODY_PART: "my nose is broken" was asked whether
    # it happens every time, or only now and then, which is the kettle's question.
    "nose", "cheekbone", "face", "cheek", "chin", "tooth", "teeth", "eyebrow", "brow",
    "temple", "mouth", "lip",
))

# A heart breaks and a marriage breaks and neither has a manual or an on-off switch. These are
# the words a person uses for a thing that is not a thing: "my marriage is broken" was asked
# what it is doing exactly, and a confident question about the wrong thing is worse than the
# shrug it replaced. Nothing here is an appliance, so nothing here is a fault to talk through.
NOT_A_THING = frozenset((
    "heart", "marriage", "relationship", "trust", "body", "voice", "sleep", "life",
    "family", "friendship", "confidence", "spirit", "faith", "childhood", "career",
    "mind", "soul", "home", "week", "year", "day",
    # Work is not a thing either: "my job is stuck" was asked what it is doing exactly, which is
    # the boiler's question about a career, and "my work is stuck" the same.
    "job", "work", "business", "mood",
))

# A thing of theirs doing the wrong thing over and over: "my razor keeps pulling", "the kettle
# keeps boiling over", "my mower kept stalling". The fault words above are a list, and a list is
# always short of the verb somebody's thing does, so this reads the shape of the sentence instead:
# "keeps" and a verb in -ing, said of something that is theirs. "my razor keeps pulling" is the
# same complaint as "my razor is broken" and wants the same question, and it was answered on main
# with "I'm listening - say more if it helps."
KEEPS_AT_IT = re.compile(r"\b(?:keeps?|kept)\s+([a-z]{3,}ing)\b")

# The words that say the thing is doing its job rather than misbehaving, and the gerunds that are
# only ever done by a person. "my pump keeps running" is a pump working, "my kid keeps fighting"
# is not a fault of a thing, and the real faults that use one of these words ("keeps going off",
# "keeps cutting out") are in THING above and are read there, before this.
KEEPS_FINE = frozenset((
    "working", "works", "going", "goes", "running", "runs", "coming", "comes", "growing",
    "improving", "doing", "does", "getting", "gets", "making", "makes", "trying", "tries",
    "taking", "takes", "giving", "gives", "helping", "happening", "arriving", "waiting",
    "sitting", "standing", "walking", "talking", "thinking", "looking", "feeling", "eating",
    "drinking", "sleeping", "learning", "playing", "wanting", "needing", "asking", "saying",
    "telling", "buying", "selling", "sending", "bringing", "paying", "saving", "spending",
    "cooking", "baking", "cleaning", "washing", "wearing", "reading", "writing", "watching",
    "listening", "smiling", "laughing", "crying", "shouting", "fighting", "arguing",
    "worrying", "wondering", "hoping", "practising", "practicing", "scrolling", "charging",
    "lasts", "lives", "matters", "counts", "means", "sounds", "seems", "moving", "noticing",
    "visiting", "changing",
))

# A person, or a pet, that keeps doing something is not a thing to repair: "my coworker keeps
# undermining me", "my ex keeps texting me", "my labrador keeps scratching". The pronouns and the
# family words are in OTHERS above; these are the rest of the words a line puts in that place.
KEEPS_NOT_A_THING = frozenset((
    "people", "person", "someone", "somebody", "anyone", "everyone", "nobody", "guy", "man",
    "woman", "bloke", "fella", "lad", "lass", "boy", "girl", "teen", "teenager", "kid", "ex",
    "exes", "coworker", "co-worker", "workmate", "colleague", "colleagues", "staff", "team",
    "crew", "teacher", "nurse", "doctor", "carer", "client", "customer", "supplier", "boss",
    "manager", "old", "year", "years", "puppy", "kitten", "rabbit", "hamster", "budgie",
    "parrot", "horse", "pony", "spaniel", "retriever", "poodle", "beagle", "collie",
    "labrador", "terrier", "chihuahua", "guinea", "ferret", "tortoise", "goldfish", "bird",
    "birds", "squirrel", "squirrels", "fox", "foxes", "mouse", "mice", "rat", "rats",
    # The trades and the people behind a counter: "my dentist keeps cancelling" and "my landlord
    # keeps coming round" are somebody letting the person down, and "tell me what it does" is the
    # boiler's question asked of a dentist.
    "dentist", "optician", "vet", "vet's", "landlord", "plumber", "mechanic", "electrician",
    "builder", "cleaner", "tutor", "hairdresser", "barber", "receptionist", "postie",
))

# A place or a service that keeps doing something is a timetable or a shop's hours, not a machine
# of theirs to talk through: "the shop keeps closing early", "the pool keeps closing for repairs",
# "the bank keeps closing my card". The next question for a machine ("what does it do?") is the
# wrong question for an opening time, and the pools that know about live hours are elsewhere, so
# this reading stands down and lets the line keep whatever answer it had.
KEEPS_NOT_THEIR_THING = frozenset((
    "shop", "shops", "store", "stores", "supermarket", "pub", "pubs", "bar", "cafe",
    "café", "restaurant", "takeaway", "chippy", "bank", "pool", "gym", "library", "hotel",
    "school", "nursery", "council", "hospital", "surgery", "clinic", "pharmacy", "chemist",
    "garage", "station", "bus", "buses", "train", "trains", "tram", "tube", "taxi",
    "delivery", "post", "airport", "airline", "office", "market", "mall", "centre",
))

# What has to be in front of "keeps" for the subject to be a thing of theirs: a determiner, in
# the three words before the verb ("my", "the", "our", "this"). Without one the subject is the
# person - "i keep putting it off", "do i keep offering", "should i keep this one" - and a
# habit of theirs is not a fault of a thing.
KEEPS_THEIRS = frozenset(("my", "our", "the", "this"))

# "My" and "our" say whose the thing is on their own. A plain "the" does not: "the road keeps
# flooding" and "the traffic keeps building up" are the world doing something, not a machine of
# theirs, and "tell me what it does" is the wrong question for either. So a subject said with
# "the" is read as theirs only when the line says somewhere that the thing is theirs, or when
# the noun is one of the things a household is made of - the machine, the appliance, the fitting.
# A list of the things a person has is the right shape here: it is what the reading is for, and
# a noun that is not on it keeps whatever answer it had, which is what the road and the traffic
# want. This way the exceptions do not have to grow one word at a time.
KEEPS_POSSESSIVE = frozenset(("my", "our"))

KEEPS_OF_A_HOUSE = frozenset((
    "fridge", "freezer", "fridge-freezer", "boiler", "kettle", "oven", "hob", "cooker", "microwave",
    "toaster", "dishwasher", "washer", "dryer", "tumble", "machine", "appliance", "fan", "pump",
    "radiator", "thermostat", "heater", "heating", "shower", "tap", "taps", "toilet", "sink",
    "drain", "drains", "pipe", "pipes", "plug", "socket", "switch", "fuse", "bulb", "light",
    "lights", "lamp", "alarm", "smoke", "detector", "door", "doors", "window", "windows", "lock",
    "locks", "handle", "hinge", "hinges", "flap", "damp", "roof", "gutter", "guttering", "fence",
    "gate", "shed", "decking", "drive", "garage", "hoover", "vacuum", "mower", "lawnmower",
    "strimmer", "wifi", "router", "broadband", "internet", "connection", "signal", "tv",
    "television", "remote", "phone", "mobile", "landline", "laptop", "computer", "pc", "tablet",
    "ipad", "printer", "keyboard", "mouse", "screen", "monitor", "charger", "battery", "car",
    "van", "bike", "bicycle", "scooter", "engine", "brakes", "brake", "clutch", "gears", "tyre",
    "tyres", "wheel", "wheels", "headlight", "indicator", "wiper", "wipers", "exhaust", "radiator",
    "mattress", "bed", "shower", "cooker", "hob", "freezer", "washer-dryer", "blind",
    "blinds", "curtain", "curtains", "shutter", "shutters", "clothes", "dryer",
    "doorbell", "bell", "buzzer", "intercom", "extractor", "immersion", "cistern", "valve",
    "tank", "timer", "thermostat", "sensor", "meter", "socket", "adaptor", "lead", "cable",
    "speaker", "radio", "console", "wifi", "hub", "box", "unit", "system", "board", "panel",
))

# The subject that can be left out of the whole-word traffic above: "my phone keeps freezing" has
# a thing in front of the fault, "i keep forgetting" has the person, and only the thing is this.
NOT_THE_THING = frozenset((
    "i", "we", "you", "he", "she", "they", "it", "there", "what", "which", "who",
    "and", "but", "so", "if", "when", "that", "this", "then", "also", "always",
    "do", "does", "did", "should", "would", "could", "can", "cant", "cannot", "will",
    "wont", "might", "may", "must", "to", "not", "never", "up", "one", "any", "much",
    "no", "how", "why", "still", "just", "only", "is", "are", "was", "were", "all",
))

# A line that asks the bot to choose - "my car is old and keeps breaking down, should i buy a new
# one", "my car keeps failing its mot, is it worth repairing" - is a decision, and the reply to a
# decision is the composer's own pool for it. The fault is why the question got asked, not the
# thing the person wants talked through, so "what have you tried so far" is the wrong question
# there. Our reading stands down and the decision keeps its turn.
ASKS_TO_CHOOSE = re.compile(r"""\b(?:should\s+i|shall\s+i|is\s+it\s+worth|is\s+it\s+better|
    would\s+it\s+be\s+better|which\s+(?:one\s+)?should\s+i|do\s+you\s+think\s+i\s+should|
    what\s+would\s+you\s+do|worth\s+(?:repairing|fixing|it)|new\s+one|replace\s+it|
    get\s+rid\s+of\s+it|throw\s+it\s+(?:out|away))\b""", re.X)

# A part of their life going flat - "my confidence has gone", "my patience is gone", "the spark
# has gone out of us" - is the same complaint as a career that is stuck, said with a different
# verb. "gone", "went" and "faded" are not fault words on their own: a machine that has gone is a
# machine that was taken away, and "my mum has gone" is not this at all. So the subject is what
# decides it, and the subject has to be one of these.
FLAT = re.compile(r"\b(?:is|are|was|were|has|have|had|went|goes|just|all|now|so|really|completely|"
                  r"totally|kind\s+of|sort\s+of)?\s*(?:gone|went|died|dead|faded|fading|vanished|"
                  r"disappeared|dried\s+up|evaporated|left\s+me)\b"
                  # "the interest has gone up" is a rise, not a flat part of a life.
                  r"(?!\s+(?:up|down)\b)")
FLAT_SUBJECT = frozenset((
    "spark", "hope", "hopes", "motivation", "patience", "appetite", "confidence", "humour",
    "humor", "laughter", "laugh", "libido", "mojo", "passion", "interest", "enthusiasm",
    "inspiration", "creativity", "energy", "buzz", "joy",
    # "interest" and "drive" are left out on purpose: an interest can go up and a hard drive can
    # go, and neither is a part of a life going flat.
    # A marriage, a friendship, a love life and a social life keep their STRAIN reading when they
    # go flat too: nothing here is a machine that stopped.
    "romance", "intimacy", "trust", "friendship", "marriage", "bubbliness", "zest",
))


# The words that only join a thing to its fault, so the noun behind one can be found: "my career
# is stuck" hangs on the career, "my washing machine has stopped working" on the machine.
JOINING = frozenset((
    "is", "are", "was", "were", "be", "been", "being", "has", "have", "had", "keeps",
    "keep", "kept", "just", "now", "still", "again", "always", "suddenly", "totally",
    "completely", "really", "all", "so", "very", "a", "an", "the", "and", "but", "then",
    "on", "off", "up", "it", "its", "it's", "there", "here", "one", "two", "twice",
    "kind", "sort", "bit", "little", "lot",
    # How the thing seemed to them is not a second noun: "my job feels stuck" and "my life seems
    # stuck" hang on the job and the life, not on "feels".
    "feel", "feels", "felt", "seem", "seems", "looks", "sounds", "gets", "got",
))
# The words that say a fault is somebody else's or a comparison's rather than theirs: "the",
# "this", "his", "in". A fault with one of these between it and their "my" is not about a part
# of their life at all.
NOT_OWNED = frozenset((
    "the", "a", "an", "this", "that", "these", "those", "his", "her", "its", "their",
    "your", "in", "on", "at", "for", "to", "with", "from", "of", "and", "but", "or",
    "then", "when", "if", "as", "than", "like",
))

# "i want to die my hair pink" is a hair appointment, and "i want to die" is the one line in the
# deck that must never be read as anything but what it is. Nothing here may touch a line like
# that, whatever else it says.
DEATHWISH = re.compile(r"\b(?:want|wanted|wanting|going|gonna|wish|wished|rather)\s+(?:to\s+)?"
                       r"(?:die|dead)\b|\b(?:die|dye)\s+my\s+hair\b")

# "the pub was dead quiet last night": the word before a describing word is how it felt, so
# neither the pub nor the night is a thing of theirs that stopped working, and "what's it doing
# exactly, and when did it start?" answers an evening. The reading is kept in step with the
# knowledge matcher (bot/knowledge/lookup.py, DEAD_AS_VERY_AFTER) and with the death reading
# (bot/compose/loss.py, DEAD_IDIOM), which has the same problem with the same word.
# The marks a word can carry and still be the word: "dead quiet," and "dead quiet!".
ODD_MARK = string.punctuation + "\u2019"
DEAD_AS_VERY_AFTER = frozenset((
    "quiet", "tired", "easy", "good", "bad", "cheap", "slow", "boring", "cheerful", "glad",
    "lucky", "proud", "keen", "jealous", "happy", "sure", "tricky", "hard", "funny", "rude",
    "straight", "wrong", "serious", "certain", "ahead", "silent", "knackered", "shattered",
    # the same idiom with the describing word after "and": "it was dead easy and dead quick" is
    # two ways of saying the same easy, so the second word has its own description in front
    # "dead" before a describing word says how much, and the composer's trouble panel was reading
    # it as a broken thing: "my trainers are dead comfy" -> "Annoying. Is it every time, or only
    # now and then?", "my new bed is dead comfortable" -> "Right. What have you tried so far?",
    # "the sofa is dead soft" -> the same panel. The adjectives people actually put it in front of:
    "comfy", "comfortable", "soft", "cosy", "cozy", "warm", "cold", "nice", "sweet", "pretty",
    "smooth", "strong", "fussy", "broke", "skint", "fun", "obvious", "scary", "gentle", "relaxed",
    "bright", "dark", "loud", "chuffed", "mint", "annoying", "embarrassing",
    "quick", "fast", "clean", "simple", "smart", "friendly", "heavy",
))
PLEA = re.compile(r"\b(?:tips?|advice|suggestions?|recommendations?|what\s+should\s+i|"
                  r"how\s+(?:do|can|should)\s+i|any\s+ideas?|help\s+me)\b")

# The person themselves, so a body part or a symptom belongs to them and not to someone named
# later in the line.
MINE = re.compile(r"^(?:i\b|i'm\b|im\b|i've\b|ive\b|my\b|our\b)")

# A body part with an owner on the front of it: "my mum's back hurts" and "my dog's leg hurts"
# are that person's or that animal's body, not the speaker's, and the panel for the speaker's own
# ache ("how long has it been like that?") is the wrong thing to say about either. The possessive
# is what hid them: OTHERS holds "mum" and "dog", and the line says "mum's" and "dog's".
OWNER_END = ("'s", "s'", "’s", "s")


def someone_elses(words):
    """True when the line names someone else's body as the thing that hurts.

    A word that is in OTHERS, or one of them with a possessive on the end ("mum's", "mums",
    "dogs"). Nothing else is stripped, so "ribs" is not "rib" and "legs" is not "leg"."""
    for word in words:
        word = str(word)
        if word in OTHERS:
            return True
        for ending in OWNER_END:
            if word.endswith(ending) and len(word) > len(ending) + 2:
                if word[:-len(ending)] in OTHERS:
                    return True
    return False

# Something of theirs, so the fault has an owner. "dead easy, mate" has none.
OWNS = re.compile(r"\b(?:my|our|mine|ours|the|this|that|it|its|it's)\b")

# The word a fault hangs on is the thing that is faulty, and which word that is decides whether
# the fault is a machine's: in "the cat flap is broken" the flap is what is broken, not the cat,
# and in "my marriage broke down" the marriage is what broke, not a thing of theirs. So the words
# between the subject and the fault ("is", "keeps", "still", "just") are skipped and the first
# real word in front of the fault is the one that answers the question.
FAULT_FILLERS = frozenset((
    "is", "are", "was", "were", "am", "be", "been", "being", "still", "just", "also", "again",
    "always", "never", "keeps", "keep", "kept", "now", "then", "so", "too", "very", "really",
    "totally", "completely", "half", "a", "an", "the", "of", "and", "but", "its", "it", "has",
    "have", "had", "hasnt", "hadnt", "isnt", "not", "no", "getting", "gone", "went", "bit",
    "little", "properly", "partly", "mostly", "sometimes", "today", "yesterday", "again",
))


def _the_fault_hangs_on(text):
    """The word each fault in the line hangs on: "flap" in "the cat flap is broken"."""
    heads = set()
    for match in (list(THING.finditer(text)) + list(CANT_GET.finditer(text))
                  + list(FLAT.finditer(text))):
        before = re.findall(r"[a-z']+", text[:match.start()])
        for word in reversed(before):
            if word in FAULT_FILLERS:
                continue
            heads.add(word)
            break
    return frozenset(heads)

# How long it has been going on. A person who says "for three weeks" has answered the question
# before it was asked: "how long has it been like that?" straight back at them is the reply of a
# bot that was not listening, so the pools come in two versions and the one without a duration
# is used when the line already gives one.
DURATION = re.compile(r"""
    \b(?:
        for\s+(?:about\s+|nearly\s+|over\s+|almost\s+)?(?:\w+\s+){0,2}
            (?:days?|nights?|weeks?|months?|years?)
      | since\s+(?:\w+\s+){0,3}(?:days?|weeks?|months?|years?|monday|tuesday|wednesday|
            thursday|friday|saturday|sunday|christmas|january|february|march|april|may|june|
            july|august|september|october|november|december)
      | going\s+on\s+(?:\w+\s+){0,2}(?:days?|weeks?|months?|years?)
      | (?:started|began)\s+(?:\w+\s+){0,2}(?:yesterday|today|last\s+week|last\s+night|
            this\s+morning|on\s+monday|a\s+(?:week|month|few\s+days)\s+ago|
            (?:\d+|two|three|four|five|six|seven|eight|nine|ten)\s+days\s+ago)
      | \b(?:two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|a\s+few|several|many)
            \s+(?:days?|weeks?|months?|years?)
      | \b\d+\s*(?:days?|weeks?|months?|years?)
    )\b
""", re.X)

BROKEN = (
    "That's a pain. What's it doing exactly, and when did it start?",
    "Annoying. Is it every time, or only now and then?",
    "Right. What have you tried so far?",
    "That would bother me too. Tell me what it does and I'll work out the next step with you.",
    "Ugh, those are fiddly. How long has it been like that?",
)

# The same pool for a line that already said how long.
BROKEN_TIME = tuple(line for line in BROKEN if "How long" not in line)

# "my car is on its last legs", "my phone is on its way out", "the oven has packed up": the
# thing is failing and the person has said nothing about what it does. Three of the questions
# above need a detail they have not given - there is no symptom, so there is nothing they have
# tried so far, nothing yet that happens every time, and no part on the table for "those are
# fiddly" to be about - so the decline gets its own pool, which asks what it is doing. On main
# every one of these lines got a line that fits any message: "my phone is on its way out" and
# "my washing machine is on its way out" were both answered "I'm listening - say more if it
# helps", and "my old van is on its last legs now" with "Thanks for telling me".
A_DECLINE = re.compile(r"""\b(?:
    on\s+its\s+way\s+out
  | on\s+(?:its|his|her|their)\s+last\s+legs
  | clapped\s+out | seen\s+better\s+days
""" + THE_END_OF_A_THING + A_THING_PACKED_UP + r"""
)\b""", re.X)

DECLINE = (
    "That's a pain. What's it doing exactly, and when did it start?",
    "Annoying. What's it doing when it goes wrong?",
    "That would bother me too. Tell me what it does and I'll work out the next step with you.",
    "Right. What is it doing that makes you think it is on the way out?",
)
# "on the way out", "on its last legs", "clapped out" and "seen better days" are a thing still
# going, so "what makes you think it is on the way out?" is the question that fits them. "the
# boiler has packed in", "the kettle is done for" and "my laptop has had it" have already
# stopped, and the same line asks them why they think what they have just said, so the pool
# without it answers a thing that has stopped.
STILL_FAILING = re.compile(r"\b(?:on\s+its\s+way\s+out"
                          r"|on\s+(?:its|his|her|their)\s+last\s+legs"
                          r"|clapped\s+out|seen\s+better\s+days)\b")
DECLINE_TIME = (
    "Annoying. What's it doing when it goes wrong?",
    "That would bother me too. Tell me what it does and I'll work out the next step with you.",
    "Right. What is it doing that makes you think it is on the way out?",
)


def _only_the_decline(text):
    """True when the line says a thing of theirs is failing and nothing more about it.

    "my phone is on its way out" is the whole of it, so the question is what it is doing.
    "my freezer has packed up and the food has thawed" names a second thing and its own
    consequence, and "the washing machine is old and on its way out" says why, so both keep the
    wider pool. The decline phrase is taken out of the line first, and any fault left in what
    remains - a symptom, an inability, a part of life gone flat - means the line is not only
    the decline.
    """
    match = A_DECLINE.search(text)
    if not match:
        return False
    rest = text[:match.start()] + " " + text[match.end():]
    return not (THING.search(rest) or CANT_GET.search(rest) or BODY.search(rest)
                or FLAT.search(rest))

SORE = (
    "That sounds wearing. Is it getting better, worse, or about the same?",
    "Does it come and go, or is it there all the time?",
    "Right. What have you tried for it so far?",
    "That's a nuisance to be carrying round. How long has it been like that?",
)

SORE_TIME = ("That's a nuisance to be carrying round. What's it like at its worst?",) \
    + tuple(line for line in SORE if "How long" not in line)

# A part of their life that has stopped going well - "my career is stuck", "my marriage is
# stuck" - is not a machine, so the questions above are the wrong ones: "what's it doing
# exactly, and when did it start?" is a repair question, and there is nothing here to repair.
# What a friend does is say the thing is worth being bothered by and ask what has gone wrong
# with it, without promising a fix that does not exist.
STRAIN = (
    # Not "what has gone wrong with it": a marriage is not a machine that broke, and for a mind
    # or a mood the "it" is the person. "What's gone wrong, do you think?" fits every one.
    "That sounds wearing. What's gone wrong, do you think?",
    "Right, that is a lot to carry. What is it like at the moment?",
    "That would weigh on me too. What has changed?",
    "Ugh, that is a hard one. How long has it been like that?",
    "Right. What would make the most difference, if it changed?",
)
STRAIN_TIME = tuple(line for line in STRAIN if "How long" not in line)


# The next questions once the first one has been answered. A person who adds a detail ("its sore
# when i sit down" after "how long has it been like that?") is carrying the same complaint on, so
# the reply is the next thing worth knowing about it, not the question they have just answered.
SORE_NEXT = (
    "And what makes it worse - moving about, sitting still, or nothing in particular?",
    "Is it the same all day, or worse at certain times?",
    "Has anything helped - a warm bath, a painkiller, or just resting it?",
)
BROKEN_NEXT = (
    "Does it do it every time, or only now and then?",
    "Has anything you tried made a difference?",
    "What's it doing when it goes wrong?",
)
# The same for a part of their life: there is nothing it does and nothing to try, so the next
# question is what it looks like to them and what would count as better.
STRAIN_NEXT = (
    "Is it one part of it, or the whole thing?",
    "Has anything helped, even a little?",
    "What would better look like, if it came?",
)

# A detail added to a complaint already on the table. The symptom or the trigger, not the owner:
# "its sore when i sit down" has no "my" in it because the part was named in the line before, and
# that is exactly why it is the same complaint and not a new subject.
DETAIL = re.compile(r"""\b(?:
    sore | sorer | hurting | hurts? | ache | aches | aching | achy | stiff | stiffness
  | swollen | swelling | tender | throb\w* | sharp | burning | numb | tight | bruised
  | worse | worst | better | eased? | eases | easier | helped | helps | relief
)\b""", re.X)
TRIGGER = re.compile(r"""\b(?:
    when\s+i | whenever\s+i | if\s+i | after\s+i | since\s+i
  | only\s+when | only\s+if | when\s+it | whenever\s+it | if\s+it
  | in\s+the\s+(?:morning|morning|evening|evenings|night)
  | first\s+thing | all\s+day | overnight
  | every\s+time | each\s+time | all\s+the\s+time | now\s+and\s+(?:then|again)
  | sometimes | most\s+(?:days|mornings|nights) | lately
  | sitting | standing | walking | running | lifting | bending | lying | sleeping | driving
)\b""", re.X)


# The words that make a short line a subject of its own rather than the answer to our question:
# a new ask ("how do i get a promotion"), a new trouble ("my car broke down"), or somebody else's
# news ("my sister is getting married"). The strain thread keeps the rest.
_NOT_A_STRAIN_DETAIL = re.compile(
    r"^(?:so |and |but |well |ok |okay )*(?:how|what|why|when|where|which|who|should|can|could|"
    r"would|will|is|are|do|does|did|shall)\b"
    r"|\b(?:broke|broken|died|dead|ill|hospital|accident|leaking|not working|stopped working)\b")


def answers_a_strain_question(clean, memory=None):
    """Whether this line is the answer to the strain question this module has just asked.

    The arbiter asks this before a card that matches a word in the line: "since the baby" after
    "what's it like at the moment?" is that thread's next turn, not the new-baby card, and "we
    have two kids and no time" is not an ack that asks how old the children are.
    """
    if _shape_on_the_table(memory) != "strain":
        return False
    return _answers_a_strain_question(_flat(clean), memory)


# A cause answers "what's it like at the moment?" as a fragment: "since the baby", "my boss",
# "no time with two kids". A line with a verb of its own is a sentence with something in it - an
# interview on Friday, a boss who keeps changing the plan, a week that has been mad - and the bot
# has a card for that, which is worth more than another question about the strain.
_A_SENTENCE = re.compile(
    r"\b(?:am|is|are|was|were|be|been|being|has|have|had|do|does|did|can|could|will|would|shall|"
    r"should|may|might|must|i'm|im|i've|ive|i'd|we're|we've|he's|she's|there's|get|gets|got|go|"
    # The contracted negatives people type: "i cant sleep", "i dont hear from him". Without them
    # "cant" is not "can" and the line reads as a fragment, and the sleep card loses its turn.
    r"cant|cannot|can't|dont|don't|didnt|didn't|wont|won't|isnt|isn't|wasnt|wasn't|havent|"
    r"haven't|hasnt|hasn't|couldnt|couldn't|wouldnt|wouldn't|doesnt|doesn't|arent|aren't|aint|"
    r"goes|going|went|keep|keeps|kept|want|wants|need|needs|feel|feels|felt|think|thinks|seem|"
    r"seems|seemed|know|knows|make|makes|made|work|works|worked|start|starts|started|stop|stops|"
    r"stopped|try|tries|tried|lost|lose|loses|die|died|broke|broken|hurt|hurts)\b")
# A line of nothing but a shrug is not a cause: "no idea", "i dont know". There is nothing in it
# for this module to carry on, and the ack that offers a hand is the better answer.
_A_HEDGE = frozenset(("no", "idea", "dont", "don't", "do", "not", "know", "sure", "dunno", "idk",
                      "nothing", "whatever", "meh", "maybe", "i", "nothing's", "nothings"))


def _answers_a_strain_question(text, memory=None):
    """Whether a short line is the answer to "what's gone wrong, do you think?".

    A cause is what a friend asked for, and a cause has no vocabulary of its own: "since the baby",
    "money", "work has been mad", "we never see each other". So the line is judged by what it is
    not - a question, a fault to repair, somebody else's news, or long enough to be a new subject -
    rather than by words it must have.
    """
    words = text.split()
    if len(words) < 2 or len(words) > 9 or "?" in text:
        return False
    if _NOT_A_STRAIN_DETAIL.search(text) or _A_SENTENCE.search(text):
        return False
    if all(word.strip(",.") in _A_HEDGE for word in words):
        return False
    # A card that answers the line itself is worth more than another question about the strain:
    # "i cant sleep" and "headaches every day" are causes *and* named complaints, and the sleep
    # entry and the GP pointer are the answers to those. This asks the knowledge base rather than
    # carrying a list of symptoms, so every card the answers lane adds stands this down for free.
    if _a_card_answers(text) or _a_length_of_time(text, memory):
        return False
    return not reads_as_trouble(text)


# How long it has been going on is a detail with an answer of its own, and it is not in the
# knowledge base: the standing replies in bot/modules/chat.py say "months is long enough that it
# deserves a proper look - ask for a longer appointment and say how long it's been", which is
# worth more than another question about the strain. So a line that names a length of time stands
# this down, the same way a line the knowledge base answers does.
_A_LENGTH_OF_TIME = re.compile(
    r"\b(?:\d+|a|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a couple of|"
    r"a few|several)\s+(?:days?|weeks?|months?|years?)\b"
    r"|\b(?:days|weeks|months|years|ages)\b(?:\s+(?:now|too|already))*\W*$"
    r"|\bsince\s+(?:yesterday|this morning|last night|the weekend|christmas|the summer|"
    r"last \w+|monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|"
    r"march|april|may|june|july|august|september|october|november|december)\b"
    r"|\bfor\s+(?:years|months|weeks|ages|a long time)\b"
    r"|\b(?:ages|a long time|all (?:week|month|year))\b")


def _a_length_of_time(text, memory=None):
    """Whether the line says how long it has been going on, and chat answers it as a length.

    The length reply is chat's (`STANDING_REPLIES` / `STANDING_FEELING_REPLIES`), reached through
    `_standing`, but `_standing` is not the first thing chat tries: a follow-up or a row can answer
    the same line with an echo ("Got it. Is there anything you'd like a hand with?"), and standing
    down for that would be worse than the thread's next question. So the module is asked for its
    reply on a copy of the memory - it writes notes while it reads, and a copy keeps those notes
    out of the real turn - and this stands aside only when the reply it would give is one of the
    length pools.
    """
    if not _A_LENGTH_OF_TIME.search(text):
        return False
    try:
        import copy as _copy
        from ..modules import chat
        said = chat.respond(text, _copy.deepcopy(memory) if isinstance(memory, dict) else {})
    except Exception:  # a chat module that cannot answer is simply no length reply
        return False
    if not said:
        return False
    said = str(said).lower()
    pools = []
    for name in ("STANDING_REPLIES", "STANDING_FEELING_REPLIES"):
        buckets = getattr(chat, name, None)
        if isinstance(buckets, dict):
            for lines in buckets.values():
                pools.extend(str(line) for line in lines)
    return any(line.lower()[:60] in said for line in pools if line)


def _a_card_answers(text):
    """Whether the knowledge base has an answer for this line on its own words."""
    try:
        from ..knowledge import lookup
    except Exception:
        return False
    try:
        found = lookup.find({"clean": text, "words": text.split()})
    except Exception:
        return False
    return found is not None


def _flat(line):
    return " ".join(str(line or "").lower().split())


def _said_already(lines, memory):
    """The lines the bot has not said yet in this conversation.

    A pool the conversation has used up is still never empty: the last line of a shape is worth
    saying again before the bot says nothing, because a shape with no reply left is not an
    answer and the turn falls through to whatever else the composer has - and on a long chat
    that is the neutral nod, or with nothing at all, "Hello!". So the whole pool is said once,
    and after that the rule is the one the pools already keep: everything but the reply just
    given ("a bot that says the same sentence twice in a row reads as if it stopped listening").
    """
    said = []
    for turn in (memory.get("turns") if isinstance(memory, dict) else None) or ():
        if isinstance(turn, dict):
            said.append(_flat(turn.get("bot")))
    said = [line for line in said if line]
    if not said:
        return tuple(lines)
    fresh = tuple(line for line in lines if _flat(line) not in said)
    if fresh:
        return fresh
    last = said[-1]
    return tuple(line for line in lines if _flat(line) != last) or tuple(lines)


# A line that says what the person has already done about it: "i tried turning it really hard",
# "i bled the radiators", "we poured drain cleaner down". Asking them "what have you tried so far"
# after that is the bot not listening to the line it just read, so the pool drops the question.
# The shape is the person and a verb in the past tense, not a list of jobs: any attempt is said
# that way, and a list would only cover the ones someone thought of.
ALREADY_TRIED = re.compile(
    r"\b(?:i|we|ive|i've|weve|we've|hes|he's|shes|she's|they|they've)\s+"
    r"(?:already\s+|just\s+|even\s+|also\s+)?(?:\w+ly\s+)?(?:tried|did|had a go|gave it a go|"
    r"used|\w+ed)\b")


def pool(shape, clean, memory=None):
    """The replies for a shape, without the ones that would ask what the line just told us.

    With `memory`, the questions this conversation has already asked are dropped too: a person
    who answers "how long has it been like that?" and then says more must not be asked it again.
    """
    text = " " + str(clean or "").lower() + " "
    if shape == "vague":
        # A setback with nothing behind it yet: what happened is the only question, and the
        # wording carries the person's own thing (bot/memory/setback.py).
        return _said_already(_setback_pool(clean), memory)
    stated = bool(DURATION.search(text))
    if shape == "sore":
        lines = SORE_TIME if stated else SORE
    elif shape == "strain":
        lines = STRAIN_TIME if stated else STRAIN
    elif _only_the_decline(text):
        lines = DECLINE_TIME if stated else DECLINE
        if not STILL_FAILING.search(text):
            # The line says the thing has stopped, not that it is failing: "what makes you think
            # it is on the way out?" asks about a doubt the person has already settled.
            lines = tuple(line for line in lines if "on the way out" not in line)
    else:
        lines = BROKEN_TIME if stated else BROKEN
    if ALREADY_TRIED.search(text):
        # "i tried turning it really hard and now its worse" says what they tried, so the one
        # question the pool cannot ask is "what have you tried so far".
        lines = tuple(line for line in lines if "tried so far" not in line)
    return _said_already(lines, memory)


def _shape_on_the_table(memory):
    """'sore' or 'thing' when our last reply was one of this module's questions, else None."""
    turns = (memory.get("turns") if isinstance(memory, dict) else None) or ()
    if not turns or not isinstance(turns[-1], dict):
        return None
    last = _flat(turns[-1].get("bot"))
    if not last:
        return None
    for shape, lines in (("sore", SORE + SORE_TIME), ("thing", BROKEN + BROKEN_TIME),
                         ("strain", STRAIN + STRAIN_TIME),
                         ("sore", SORE_NEXT), ("thing", BROKEN_NEXT),
                         ("strain", STRAIN_NEXT)):
        for line in lines:
            if _flat(line) in last:
                return shape
    return None


IT = re.compile(r"\b(?:it|its|it's|this|that|these|those)\b")
MINE_AGAIN = re.compile(r"\bmy\s+([a-z']+)")


def _points_at_it(text, memory):
    """Whether a detail is about what we were already talking about.

    A detail carries on a thread by pointing back at it: "its worse in the morning", "only when
    it spins", "my back is worse". A line that names a new thing of its own ("the weather is
    better today", "my laptop is better now") only shares a word with the detail vocabulary, so
    it is left to the rest of the composer.
    """
    if IT.search(text):
        return True
    turns = (memory.get("turns") if isinstance(memory, dict) else None) or ()
    said = _flat(turns[-1].get("user")) if turns and isinstance(turns[-1], dict) else ""
    if not said:
        return True
    for noun in MINE_AGAIN.findall(text):
        if re.search(rf"\b{re.escape(noun)}\b", said):
            return True
    return False


def _shape_answered(memory):
    """The shape of a fault we have just given a whole answer to, or None.

    Most faults are answered by the knowledge base rather than by this module ("my washing
    machine is leaking" gets the valve, "my back aches" gets the two-weeks talk), so the thread
    is on the table without this module having said anything. The detail that follows - "only
    when it spins", "it started yesterday", "its worse in the morning" - is still the next line
    of the same fault, and it was being said back as a fact about nothing.

    Only the previous turn counts, and only when our answer did not ask anything: if the reply
    ended in a question, the detail is the answer to that question and the ack already has it.
    """
    turns = (memory.get("turns") if isinstance(memory, dict) else None) or ()
    if len(turns) < 1 or not isinstance(turns[-1], dict):
        return None
    last = _flat(turns[-1].get("bot"))
    if not last or last.rstrip().endswith("?"):
        return None
    said = _flat(turns[-1].get("user"))
    if not said:
        return None
    return _shape(said)


WHAT_IT_DOES = re.compile(r"what\s+it\s+does|what's\s+it\s+doing|what\s+is\s+it\s+doing",
                            re.I)


def carried_on(clean, words=None, memory=None):
    """The replies for a detail added to the complaint we are already on, or None.

    The first line of a complaint names what hurts ("my tailbone hurts") and the next line is
    usually the detail kind of answer - when it is worse, what brings it on. With nothing to
    carry it on, the composer answers that detail with a stock line that could have come before
    any message at all ("Thanks for telling me"), which throws away the thread the pool had just
    started. So this needs both halves: one of our own questions as the last reply, and a line
    that is a detail about it rather than a new subject.
    """
    shape = _shape_on_the_table(memory)
    fuzzy = False
    if not shape:
        # A whole answer to a fault is a looser thread than one of this module's questions, so
        # the line has to say it is about that same thing, not just share a word with it.
        shape = _shape_answered(memory)
        fuzzy = bool(shape)
    if not shape:
        return None
    text = _flat(clean)
    if not text or "?" in text:
        return None
    if words is None:
        words = set(re.findall(r"[a-z']+", text))
    words = set(words)
    # The strain question is "what's gone wrong, do you think?", and the answer to it is a cause
    # rather than a symptom: "since the baby", "we have two kids and no time", "money". None of
    # those words is in DETAIL or TRIGGER, so the thread was dropped and "since the baby" was
    # answered with the new-baby card. Once this module has asked the strain question, a short
    # line that is not a question, a fault to repair or one of their people's news is that answer.
    answers_the_strain = shape == "strain" and not fuzzy and _answers_a_strain_question(text,
                                                                                        memory)
    if someone_elses(words) and not _a_fault_of_a_thing(text) and not answers_the_strain:
        return None
    padded = " " + text + " "
    says_what = answers_the_strain or bool(DETAIL.search(padded) or TRIGGER.search(padded))
    if not (says_what or DURATION.search(padded)):
        return None
    if fuzzy and not _points_at_it(padded, memory):
        return None  # "the weather is better today" after a bad back is not that back
    nexts = {"sore": SORE_NEXT, "strain": STRAIN_NEXT}.get(shape, BROKEN_NEXT)
    lines = list(_said_already(nexts, memory))
    for line in pool(shape, clean, memory):
        # The first question of the thread is not a second question: once the person has said
        # what went wrong, "what's gone wrong, do you think?" in another wording is the same ask.
        if line in STRAIN or line in lines:
            continue
        lines.append(line)
    # "What's it doing when it goes wrong?" is the first question of a complaint, not the second:
    # the detail they just typed already said what or when, or the answer they just got did.
    lines = [line for line in lines if not WHAT_IT_DOES.search(line)]
    return tuple(lines) or None


def reads_as_trouble(clean, words=None, repaired=""):
    """'thing' for a broken thing, 'sore' for their own body, None for anything else.

    `repaired` is the same line with its wrong words put right (the reading's `plain`), and it
    is only consulted when the line as typed is not trouble: the owner is the opening word, so
    "me knee is killing me" is the same complaint as "my knee is killing me" and only the
    repair knows it."""
    text = _without_a_dead_that_only_means_very(_without_wanting_or_praise(
        " ".join(str(clean or "").lower().split())))
    if not text or "?" in text:
        return None  # a question is not a fault to talk them through, whatever it says next
    if reads_as_someones_death(text):
        # "someone in my class died" is not a thing that is broken: "what is it doing exactly"
        # is the wrong question about a death, and the pool has no way to tell. A phone that
        # died stays here, because the subject of that death is not a person.
        return None
    shape = _shape(text, words)
    if shape is None and repaired and repaired != text:
        shape = _shape(_without_a_dead_that_only_means_very(
            _without_wanting_or_praise(repaired)))
    return shape


# Praise and wanting are said with the word for dying, and the thing in front of it is what the
# praise is about. "this soup is to die for" was read as a fault of the soup and answered "Ugh,
# those are fiddly. How long has it been like that?" - a repair question about a bowl of soup -
# and "the cake was to die for" got "Annoying. Is it every time, or only now and then?". The word
# is the whole of the reading, so the phrase goes before anything reads the word, exactly as the
# "dead" that means very does. Only the praise and the wanting: "my phone died" and "the boiler
# is dead" are still faults, and "to die for" is never said about a thing that has stopped.
WANTING_OR_PRAISE = re.compile(r"""
    \b(?:
        to\s+die\s+for
      | worth\s+dying\s+for
      | (?:would|could|might|will)\s+(?:die|kill)\s+for
      | (?:i|you|we|they|he|she)'?d\s+(?:die|kill)\s+for
      | (?:would|could|will)?\s*die[sd]?\s+on\s+(?:that|this|a|the)\s+hill
      | dy(?:ing|in)\s+(?:for|to)\b
    )
""", re.X)


def _without_wanting_or_praise(text):
    """The line with a "to die for" / "I'd die for" taken out of it.

    Nothing else goes, and the words around it stay where they were, so a line that carries both
    the praise and a fault is still read for the fault: "this soup is to die for but the oven is
    broken" is the oven.
    """
    return WANTING_OR_PRAISE.sub(" ", str(text or ""))


def _without_a_dead_that_only_means_very(text):
    """The line with a "dead" that describes the next word taken out (see DEAD_AS_VERY_AFTER).

    Only that word goes, so the rest of the line is read as it was: "the boiler is dead and it
    keeps cutting out" is still the boiler.
    """
    words = str(text or "").split()
    if "dead" not in words:
        return text
    kept = []
    for index, word in enumerate(words):
        following = words[index + 1] if index + 1 < len(words) else ""
        if word == "dead" and following.strip(ODD_MARK) in DEAD_AS_VERY_AFTER:
            continue
        kept.append(word)
    return " ".join(kept)


# The animals whose names are also the front half of a thing's name: a cat flap, a dog flap, a
# fish tank, a rabbit hutch, a bird feeder. The animal word there is a modifier, not the subject.
ANIMAL_MODIFIERS = frozenset((
    "cat", "cats", "dog", "dogs", "puppy", "puppies", "kitten", "kittens", "pup", "pups",
    "pet", "pets", "bird", "birds", "fish", "rabbit", "rabbits", "hamster", "hamsters",
    "chicken", "chickens", "horse", "horses", "tortoise", "parrot", "budgie", "ferret",
    "snake", "lizard", "mouse", "rat", "rats", "guinea", "pig", "pigs",
))

# What can follow a name without making it half of another thing's name. "the cat flap" is a
# flap; "my cat has", "my cat wont", "my cat got out" are the cat.
NOT_A_MODIFIER = frozenset((
    "is", "are", "was", "were", "am", "be", "been", "being", "has", "have", "had", "will",
    "wont", "cant", "cannot", "could", "would", "should", "might", "may", "must", "needs",
    "need", "got", "get", "gets", "getting", "went", "goes", "going", "keeps", "keep", "kept",
    "died", "dies", "die", "dead", "ill", "sick", "old", "young", "small", "big", "little",
    "and", "but", "so", "that", "who", "which", "doesnt", "didnt", "isnt", "wasnt", "to",
))


def _someone_is_the_subject(text):
    """True when a person or an animal in the line is what it is about.

    A name is the subject unless it is the front half of a thing's name: "the cat flap is
    broken" is a flap, while "my cat is ill" and "my son took all my pills" are theirs, and an
    emergency about somebody else is not a fault to talk through.
    """
    words = re.findall(r"[a-z']+", text)
    for index, word in enumerate(words):
        if not someone_elses((word,)):
            continue
        following = words[index + 1] if index + 1 < len(words) else ""
        if word in ANIMAL_MODIFIERS and following and following not in NOT_A_MODIFIER:
            continue  # "cat flap", "fish tank": the animal is part of the thing's name
        return True
    return False


def _the_noun_before(text, at):
    """The noun just before a match, whoever owns it: "the leaves" is leaves, "my slabs" is slabs.

    _the_thing_it_hangs_on answers a different question - whether the fault is a thing of theirs
    rather than the world's, so it says nothing when the owner is "the". This one only wants the
    word, for readings about what kind of thing it is.
    """
    words = re.findall(r"[a-z']+", " " + str(text or "")[:at])
    while words and words[-1] in JOINING:
        words.pop()
    return words[-1] if words else ""


def _a_fault_of_a_thing(text):
    """True when the fault in the line hangs on a thing, not on a person or an animal."""
    padded = " " + text + " "
    return bool(THING.search(padded) and OWNS.search(padded)
                and not _someone_is_the_subject(text))


def _names_a_body_part(text):
    """True when the line names a part of a body, which is what a bodily pain needs."""
    return bool(set(re.findall(r"[a-z']+", text)) & BODY_PART)


def _figurative_passes(text):
    """True when a line whose only ache word can also mean "a nuisance" is about the body.

    A named body part settles it. Without one, "my job is a pain" and "my phone is painful to
    use" stand aside, while "i am in pain" and "i have a pain in my side" stay: the nuisance
    reading needs a thing of theirs to be the nuisance."""
    if _names_a_body_part(text):
        return True
    return not NUISANCE.search(text)


def _shape(clean, words=None):
    """The shape of the trouble in this one text, or None."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return None
    words = set(words) if words else set(re.findall(r"[a-z']+", text))
    mine = " " + text + " "
    # A state of a thing - "has gone all black", "is burnt on", "has seized up" - read before the
    # body and the acute fence, because the burn and the seizure are words those two also own.
    a_state = THING_STATE_ONLY.search(mine)
    growing_state = bool(a_state and _the_noun_before(mine, a_state.start()) in GROWING)
    if someone_elses(words) and not _a_fault_of_a_thing(text):
        # Someone else in the line stands this reading down when they are what the fault hangs
        # on ("my mum is ill", "the cat is stuck up the tree"). A thing of theirs is not that:
        # "the cat flap is broken" is a flap, and the cat is only part of its name.
        return None
    if PLEA.search(text) or DEATHWISH.search(text):
        return None
    # The one acute word this reading shares with the safety reader is the burn: "the pan is
    # burnt" and "my oven door glass has gone all black and burnt on" are a thing's damage, and
    # the burn the safety reader owns is on a body. So the acute stand-down holds everywhere but
    # a state of a thing with no body part in the line.
    if ACUTE.search(text) and not (a_state and not growing_state
                                   and not words & BODY_PART):
        return None
    # A fracture word is an injury only when a body is there for it to belong to: "my wrist is
    # broken" keeps safety's turn, "my washing machine is broken" is a fault to talk through.
    if FRACTURE.search(text) and (words & (BODY_PART | BONE)):
        return None
    # And a broken heart, a broken marriage, a marriage that broke down and a broken trust are
    # not things that are doing something: those are for the loss and the feelings readers, not
    # for a repair question. The word a break hangs on decides it, so "my career broke down" is
    # the career's and "my laptop broke down" is the laptop's.
    hung_on = _the_fault_hangs_on(text)
    if BREAKS.search(text) and ((words & NOT_A_THING) or (hung_on & NOT_A_THING)):
        return None
    own = bool(MINE.match(text))
    # "my legs are dead after that run" is the same complaint as "my knee is aching" said with a
    # body part and no pain word, so a body part plus dead/killing/hurting counts as one.
    # "my knee has had it" and "my knees are done for after that run" are the same complaint as
    # "my knee is killing me", said in the words a person uses for a machine, so a body part with
    # the end-of-a-thing words counts as the body's trouble too.
    body_word = BODY.search(mine)
    if a_state and not growing_state and not words & BODY_PART:
        # "the pan is burnt" and "my oven door glass has gone all black and burnt on" are a thing's
        # damage; the burn the body reader owns is the one on a body, so only a body part in the
        # line keeps the word for the body ("my lips are burnt") .
        body_word = None
    ache = body_word or (words & BODY_PART
                                 and re.search(r"\b(?:dead|killing|kills|hurts?|banging|"
                                               r"thumping|pounding|splitting|had\s+it|"
                                               r"done\s+for)\b", mine))
    if own and ache:
        if FIGURATIVE.search(mine) and not _figurative_passes(text):
            return None
        return "sore"
    # A part of their life going flat is not a fault to repair and not a shrug: "my confidence
    # has gone" was answered "Got it. Is there anything you'd like a hand with?", a line that
    # fits any message at all, and "my laughter died" was asked what it does and when it started.
    flat = FLAT.search(mine)
    if flat and (_the_fault_hangs_on(mine) & FLAT_SUBJECT):
        return "strain"
    # A setback said vaguely ("my cake was a disaster", "the party went badly") is a thing of
    # theirs too, and the question is what happened rather than what it is doing. Read before
    # THING, which wants a fault word the line does not have, and after the body, which is never
    # a setback: "me knee is killing me" is the same line as "my knee is killing me" once
    # the owner is put right, and only the repair reads it as theirs. The reading refuses a
    # question, a line about somebody else and a line that goes on to say what happened.
    if _setback(text) and not words & BODY_PART:
        return "vague"
    thing = THING.search(mine)
    if thing and OWNS.search(mine):
        # A fault said of a part of their life rather than of a thing they own is not a repair
        # question: "my career is stuck" was asked whether it does it every time, or only now
        # and then. It is the "strain" shape, which asks what has gone wrong with it instead.
        hangs_on = _the_thing_it_hangs_on(mine, thing.start())
        if hangs_on in NOT_A_THING:
            return "strain"
        # A body part said in the shape of a state - "my knee is stiff", "my back has gone" - is
        # the body's complaint, and the sore reading is the one that talks about it rather than
        # asking what the knee is doing while it does it.
        if hangs_on in BODY_PART and a_state and a_state.start() == thing.start():
            return "sore"
        # The state branch is what matched, and the thing that went into the state is growing:
        # its colour is the season. Read after the body so "my lips are burnt" keeps its answer.
        if growing_state and a_state.start() == thing.start():
            return None
        # "my knee is on its last legs" is a body said with the words for a washing machine:
        # "what's it doing exactly" is the wrong question for a knee, and the next thing a
        # person needs is what a doctor or a pharmacist would ask. A body part stands this
        # reading down only for the decline idioms, so every fault that was already read here
        # ("my knee is stuck") keeps its answer.
        if hangs_on in BODY_PART and A_DECLINE.search(mine[thing.start():]):
            return None
        return "thing"
    if CANT_GET.search(mine) and OWNS.search(mine) and not words & BODY_PART:
        return "thing"
    if _keeps_doing_it(mine) and not words & BODY_PART:
        return "thing"
    return None


def _keeps_doing_it(text):
    """True when something of theirs keeps doing the wrong thing: "my razor keeps pulling".

    The thing the fault hangs on has to be a thing. In "i keep waking up at four" the subject is
    the person, in "my knee keeps clicking" it is their body, and in "my confidence keeps going"
    it is a part of their life; those are not a machine to talk through. A word that names a way
    the thing is supposed to work (KEEPS_FINE) is not a fault either - "the fridge keeps running"
    is a fridge, not a problem - so only a verb outside that set makes the line this one.
    """
    if ASKS_TO_CHOOSE.search(text):
        return False
    for match in KEEPS_AT_IT.finditer(text):
        doing = match.group(1)
        if doing in KEEPS_FINE:
            continue
        before = re.findall(r"[a-z']+", text[:match.start()])
        if not KEEPS_THEIRS & set(before[-3:]):
            continue
        head = ""
        for word in reversed(before):
            if word in FAULT_FILLERS or word in NOT_THE_THING:
                continue
            head = word
            break
        if not head or head in OTHERS or head in NOT_A_THING or head in BODY_PART:
            continue
        if head in NOT_THE_THING or head in KEEPS_NOT_A_THING:
            continue
        if head in KEEPS_NOT_THEIR_THING:
            continue
        if not OWNS.search(text):
            continue
        # "my razor keeps pulling" says whose the razor is; "the road keeps flooding" does not
        # say whose the road is, and it is not theirs to repair. So the words in front of the
        # verb have to carry a possessive, or name something a household is made of, or the
        # line keeps the answer it had.
        phrase = set(word for word in before
                     if word not in FAULT_FILLERS and word not in NOT_THE_THING)
        if not phrase & KEEPS_POSSESSIVE and not phrase & KEEPS_OF_A_HOUSE:
            continue
        return True
    return False


def _the_thing_it_hangs_on(text, at):
    """The word a fault hangs on: the noun just before it, past the words that only join them.

    "my career is stuck" is a career, "my washing machine has stopped working" is the machine,
    and "my home wifi keeps dropping" is the wifi - which is what keeps a line about a part of
    their life apart from a line about a machine that is in it.
    """
    words = re.findall(r"[a-z']+", text[:at])
    while words and words[-1] in JOINING:
        words.pop()
    if not words:
        return ""
    noun = words[-1]
    # The fault belongs to the thing they named, so a "my" or an "our" has to be in front of it,
    # with nothing but the thing's own words in between ("my home wifi"): a line that hangs on a
    # day or a comparison - "hes fine in the day just wont settle at night" - hangs on nothing of
    # theirs, and is left to the reading that already has it.
    back = words[:-1]
    for _ in range(3):
        if not back:
            break
        if back[-1] in ("my", "our"):
            return noun
        if back[-1] in NOT_OWNED:
            return ""
        back.pop()
    return ""
