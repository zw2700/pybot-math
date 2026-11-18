"""A death or a loss is never answered as small talk.

"My dad died in march" answered with "Got it." is the kind of reply STYLE.md rules out: it is
careless, and it is also wrong — a death is not a thing to note and move on from. This reads a
death in the line and picks the reply the situation asks for:

* the user's own loss -> plain sympathy, and an offer of company or a practical hand;
* someone else's loss ("my friend's mum died") -> what to say to that person, because that is
  the question behind the line even when it is phrased as a statement;
* a condolence card or message -> words they can actually use;
* a question about grief itself ("is it normal to still cry", "i can't sleep") -> a short,
  normalising answer and the one useful pointer (their GP if it stays heavy).

Only a real death fires this: "my legs are dead", "dead against it", "my phone died", "nearly
died laughing", "a dead end" and "the deadline" are ordinary lines and must pass, so the dead
words need a person or a pet behind them, and never an object right before them.

The pools vary and never repeat, like the fallback's (`_choose` in bot/compose/fallback.py).
"""
import re
try:  # the reading of a dream, so a death in a dream is not a death
    from ..memory import dream as _dream
except Exception:  # noqa: BLE001 - a reading that cannot be imported just adds no rule
    _dream = None

from ..understanding import normalise
from ..understanding.topics import is_a_machine_word

# People and pets: a death word only counts when one of these is in the line (or is the thing
# that died). Relations are here so "my mum", "our nan", "her son" and "the dog" all count.
PEOPLE = frozenset((
    "mum", "mom", "mam", "mother", "dad", "father", "nan", "nana", "gran", "granny",
    "grandma", "grandmother", "grandad", "granddad", "grandpa", "grandfather", "grandparents",
    "parents", "son", "daughter", "child", "children", "kid", "kids", "baby", "boy", "girl",
    "brother", "sister", "wife", "husband", "partner", "friend", "friends", "mate", "mates",
    "neighbour", "neighbor", "neighbours", "neighbors", "colleague", "colleagues", "aunt",
    "auntie", "uncle", "cousin", "niece", "nephew", "family", "relative", "relatives",
    "stepdad", "stepmum", "godmother", "godfather", "in-laws", "mil", "fil",
    # The relations a person actually has, not just the closest family: the one who cares for
    # them, the partner they are not married to, the children of a second marriage, the
    # grandchildren, the step- and god-children, the twin, the flatmate. Each of these was a
    # real line that fell through - "my carer is dying" got the store's echo, "my stepson is
    # dying" the search shrug, "my fiance is dying" the shrug after it, "my other half is
    # dying" the money answer that reads "half" as a split. The list is relations, so a thing
    # with a possessive ("my phone is dying", "my garden is dying") still cannot get in.
    "parent", "sibling", "siblings", "spouse", "spouses", "boyfriend", "girlfriend",
    "boyfriends", "girlfriends", "fiance", "fiancee", "fianc\u00e9", "fianc\u00e9e", "fiances",
    "halfbrother", "halfsister", "ex",
    "stepson", "stepsons", "stepdaughter", "stepdaughters", "stepchild", "stepchildren",
    "stepbrother", "stepsister", "godson", "godsons", "goddaughter", "goddaughters",
    "godchild", "godchildren", "grandson", "grandsons", "granddaughter", "granddaughters",
    "grandchild", "grandchildren", "grandkids", "twin", "twins", "carer", "carers",
    "caregiver", "caregivers", "childminder", "guardian", "flatmate", "flatmates",
    "housemate", "housemates", "lodger",
    "dog", "dogs", "cat", "cats", "puppy", "kitten", "rabbit", "hamster", "budgie", "parrot",
    "horse", "pony", "pet", "pets", "tortoise", "ferret", "guinea",
    # a fish is a pet people mourn, and it was the one pet the condolence never saw: "my fish
    # died" and "my goldfish is dying" were both falling through to a shrug.
    "fish", "fishes", "goldfish", "snake", "lizard", "gerbil",
))

# The people who are not family and are still grieved like family: the carer who comes every
# morning, the nurse on the ward, the therapist they have seen for years, the person they share a
# flat with. A death said about one of them is the same bereavement, and without these words the
# line fell through to a shrug ("Got it. Is there anything you'd like a hand with?") or, worse,
# to the answer for a thing that has stopped working ("Tell me what it does and I'll work out the
# next step with you"). "worker" is here for the whole family of them - "my support worker died",
# "my care worker died", "my key worker died" - since the first word only says which kind.
CLOSE_PEOPLE = frozenset((
    "carer", "carers", "caregiver", "caregivers", "nurse", "nurses", "doctor", "doctors",
    "gp", "gps", "surgeon", "surgeons", "midwife", "midwives", "therapist", "therapists",
    "counsellor", "counsellors", "counselor", "counselors", "physio", "physiotherapist",
    "psychiatrist", "childminder", "childminders", "babysitter", "babysitters", "nanny",
    "nannies", "cleaner", "cleaners", "lodger", "lodgers", "housemate", "housemates",
    "flatmate", "flatmates", "classmate", "classmates", "schoolfriend", "tutor", "tutors",
    "teacher", "teachers", "manager", "managers", "priest", "vicar", "pastor", "rabbi",
    "imam", "barber", "hairdresser", "warden", "mentor", "worker", "workers",
))
# The same people said with two words, where the second is not a person on its own: "home help"
# is nobody if only "help" is read, and "my night carer" is nobody if only the time of day is.
ROLE_PHRASE = re.compile(
    r"\b(?:home\s+(?:help|carer)|care\s+assistant|foster\s+carer|support\s+staff|"
    r"(?:duty|night|live-in)\s+(?:nurse|carer))\b")
PEOPLE = PEOPLE | CLOSE_PEOPLE

# "my vacuum cleaner died" is an appliance and "my nanny goat died" is livestock: the second word
# is the one that can die, and the first says which kind of thing it is. "my window cleaner died"
# and "my oven cleaner says..." are people people do mourn, so only the machines are here, and a
# line that names another person as well keeps its person reading.
THING_ROLE = re.compile(
    r"\b(?:vacuum|oven|drain|steam|carpet|dishwasher|pipe|grill|barbecue|bbq|floor|gutter|jet|"
    r"pressure|upholstery|chimney)\s+cleaners?\b|\bnanny\s+goats?\b")
# The role words that are also a thing's name, so the phrase, not the word, has to decide.
TWO_WAY_ROLES = frozenset(("cleaner", "cleaners", "nanny", "nannies"))
# The paperwork that belongs to a person, which is what "i lost my carer badge" lost: the person's
# name is the qualifier and the thing after it is what went missing, so the line wants the search
# for it and not sympathy. "i lost my friends number" was the same fault before any role word was
# added, so this is read for family too.
THEIRS = frozenset((
    "badge", "badges", "card", "cards", "allowance", "funding", "letter", "letters", "note",
    "notes", "form", "forms", "paperwork", "payment", "payments", "appointment", "appointments",
    "referral", "referrals", "rota", "timesheet", "pass", "application", "number", "budget",
    "assessment", "plan", "diary", "file", "files", "folder", "prescription", "receipt",
    "invoice", "statement", "booking", "bookings", "certificate", "report", "results", "record",
    "records", "pin", "login", "password", "email", "address", "ticket", "tickets",
))

# The things people say when someone has died. Each of these is unambiguous on its own.
PLAIN = re.compile(
    r"\b(passed away|funeral|funerals|burial|cremation|cremated|cremate|"
    r"grief|grieving|grieve|bereaved|bereavement|widow|widowed|mourning|condolence|"
    r"condolences|eulogy|memorial service|post mortem|in memoriam)\b")

# A price question with no death in it is the knowledge base's: "funeral costs", "burial costs",
# "cheapest funeral" and "cremation costs" are somebody pricing the thing up, not somebody whose
# person has died, and "That's such sad news, I'm sorry" answered a question about money. A cost
# question that names the person ("my mums funeral costs") or that says a death has happened
# ("my mum died, the funeral costs are huge") stays here - that is a bereavement with a bill in it
# and the condolence is the right reply.
A_PRICE = re.compile(
    r"\b(?:cost|costs|costing|price|prices|pricing|cheap|cheapest|expensive|afford|affordable|"
    r"budget|pay|quote|quotes)\b|\bhow\s+much\b")
# The proceedings asked about as a thing rather than said of a funeral somebody is having: "how do
# i arrange a funeral", "can i have a funeral without a coffin". The wake card's "if you can make
# it, go" is an answer to neither.
PROCEEDINGS_ASK = re.compile(r"\b(?:how|what|which|can|could|should|do|does|any|tips?|ideas?)\b")
# A particular funeral, the one the chat is already about: "the funeral", "the burial", "my
# grandad's funeral". Every question about that one - what time it is, whether to go - is the
# grief band's, and a line that refers to it is not asking what a funeral is like in general.
THIS_ONE = re.compile(r"\b(?:the|this|that|our|their|his|her|its|today|tomorrow|yesterday)\s+"
                      r"(?:\w+\s+){0,2}(?:funeral|burial|cremation|wake|service|viewing)\b")
# Words that say a death has happened, is happening, or is being grieved, anywhere in the line.
A_DEATH_HAPPENED = re.compile(
    r"\b(?:died|dying|dies|dead|death|deaths|passed\s+away|passed\s+on|gone|killed|lost|"
    r"losing|buried|bury|burying|ashes|widow|widowed|bereaved|bereavement|grief|grieving|"
    r"mourning|condolence|condolences|eulogy|sympathy|miss|missing)\b")


# A line that takes back the subject of the earlier one instead of reporting one: "i meant a
# funeral" after "what should i wear to a wedding" is that question about the funeral. The death
# word in it is the new subject, not news of a death, and the plain sympathy pool sent a
# condolence card to somebody choosing an outfit. Only a line that says nothing else is this;
# "i meant to say my dad died" is still a death.
CORRECTS = re.compile(
    r"^\W*(?:(?:no|nope|sorry|apologies|actually|wait|hold on|oops)[\s,.!-]+)*"
    r"(?:i\s+(?:mean|meant|said)(?:\s+to\s+say)?|(?:you\s+)?mean|i\s+did\s+mean)[\s,.!-]+"
    r"(?P<rest>\S.*)$", re.I)


def _only_a_new_subject(line):
    """True when the line only puts a different thing in place of the earlier one."""
    found = CORRECTS.match((line or "").strip())
    if not found:
        return False
    rest = found.group("rest").strip(" .!?,")
    return bool(rest) and len(rest.split()) <= 3 and not DIED.search(rest)


def _only_the_proceedings(clean, words):
    """True when the line only asks about funerals as a thing, so the knowledge base answers it."""
    if A_DEATH_HAPPENED.search(clean) or _has_person(words):
        return False
    if _unnamed_person(words, clean) or THIS_ONE.search(clean):
        return False
    if ASK_WORDS.search(clean) or CARD_WORD.search(clean):
        # "what do i write in a condolence card" asks for words, and the card pool has them.
        return False
    return bool(A_PRICE.search(clean) or PROCEEDINGS_ASK.search(clean))


# An Irish wake is a funeral, but "wont wake up" is someone still alive who needs an ambulance,
# and "i wake up at 4 every morning" is the user's own sleep. So `wake` only counts as the noun,
# after whose wake it is, and it is never in the unambiguous list above.
WAKE = re.compile(
    r"\b(?:his|her|their|the|a|mum's|dad's|nan's|grandad's|gran's)\s+wake(?!\s*(?:up|me|him|"
    r"her|them|you|us|at|before|earlier|by|and|of)\b)\b")

# "buried" is a garden job and a dog with a bone as often as it is a funeral, so like "died" it
# needs a person or a pet behind it: "we buried my dad", "the dog is buried at the end".
BURIED = re.compile(r"\bburied\b")
# What can follow "buried" when it is a garden job rather than a funeral.
BURIED_OBJECT = ("a", "an", "the", "some", "old", "new", "these", "those", "his", "her", "my",
                 "our", "their", "your")
# "i buried my old dog", "i buried my poor old cat": an adjective between the owner and the pet is
# how people write it, and the person or pet is still the thing that was buried.
BURIED_ADJECTIVE = ("old", "poor", "little", "beloved", "dear", "sweet", "big", "lovely", "late",
                    "much", "loved", "own", "first", "precious", "wee", "new")

# "died" is a verb and not everyone uses it: people write the noun instead. "my mums death was
# sudden", "the first anniversary of his death", "dads death hit me hard" are all the same
# bereavement, and a bot that only looks for "died" reads them as small talk. The article or the
# owner is what makes it a particular death rather than the word on its own: "scared to death",
# "the death penalty", "death metal", "death in paradise" and "sudden death" keep their own
# meanings and must pass.
DEATH_NOUN = re.compile(
    r"\b(?:a|the|this|that|his|her|their|your|my|our)\s+deaths?\b|"
    r"\b[a-z]+(?:'s|s'|s)\s+deaths?\b|"
    r"\b(?:two|three|several)\s+deaths\b")
# Whose death it is, said with an owner: "his death", "my mums death", "the death of my wife".
OWN_DEATH = re.compile(
    r"\b(?:my|his|her|their|your|our)\s+(?:[a-z]+(?:'s|s'|s)\s+)?deaths?\b|"
    r"\b([a-z]+)(?:'s|s'|s)\s+deaths?\b")
# A bare "a death" / "the death" is a bereavement only with a cue in the line. Without one it is
# a word doing another job: "the death star lego set", "the death toll rose in the storm".
DEATH_CUE = re.compile(
    r"\b(?:guilty|cope|coping|cant stop|get over|getting over|anniversary|funeral|grief|"
    r"grieving|sudden|suddenly|wasnt there|wasn't there|angry|sad|numb|miss|misses|missed|"
    r"cry|crying|cried|wake|ashes|burial|memorial|condolence|mourning|hit me|hit him|hit her|"
    r"in the family|on the news|normal to feel|keep thinking|cant sleep|to terms|how do i|"
    r"what do i say|still)\b")
# A "death" doing the job of an adjective is a name, not a bereavement ("the death star", "death
# valley", "his death doula"). The noun has to do the work itself, so what follows it is a
# preposition, a verb of the death, or a word people write next to a real one.
DEATH_COMPOUND = re.compile(
    r"\bdeath\s+(?!(?:of|was|is|in|at|on|has|had|came|come|hit|hits|left|changed|anniversary|"
    r"day|days|month|months|year|years|certificate|notice|and|or|itself|row|toll|threat|"
    r"bed|i|we|he|she|they|you|my|our|his|her|their|me|us|them|really|just|still|so|but|if|"
    r"when|while|after|before|because|that|this|everything|nothing)\b)[a-z]+")
# A death on a screen or in a book is not someone's death, unless the line names a person too
# ("my nan died watching her favourite film" is caught by the verb, not here).
FICTION = re.compile(
    r"\b(?:film|films|movie|movies|book|books|novel|play|episode|series|documentary|"
    r"characters?|scene|plot|chapter|show|netflix|tv|actor|actress|game|anime|comic|season|"
    r"trailer|storyline)\b")
# The speaker's own death is a fear, not a bereavement: a condolence addressed to a living worrier
# is the wrong emotion. "i keep thinking about her death" is still someone else's.
OWN_WORRY = re.compile(
    r"\b(?:my|your|our)\s+(?:own\s+)?death\b|\bdeath anxiety\b|\bfear of death\b|"
    r"\b(?:scared|afraid) of death\b|\bdeath itself\b|\bthink(?:ing)? about death\b|"
    r"\b(?:what|when)\s+(?:is|comes after|happens after)\s+death\b|\bis death\b")
# A thing cannot die: "my laptops death" is the same line as "the death of my laptop", which the
# list above already refuses, and the owner form was slipping past it.
THINGS = frozenset((
    "laptop", "laptops", "phone", "phones", "car", "cars", "battery", "batteries", "boiler",
    "fridge", "freezer", "telly", "tv", "printer", "houseplant", "houseplants", "plant", "plants",
    "tree", "trees", "lawn", "garden", "business", "career", "job", "pub", "shop", "club",
    "brand", "game", "team", "band", "party", "project", "dream", "holiday", "marriage",
    "engine", "phone", "internet", "radio", "cinema", "print", "high",
))
# A pet is the one "thing" whose death is a bereavement, and the pet entries answer it better
# than a condolence (cremation, a home burial, a paw print), so the noun reading stays out of it.
PET_DEATH = re.compile(
    r"\b(?:cat|cats|dog|dogs|puppy|puppies|kitten|kittens|rabbit|rabbits|hamster|hamsters|"
    r"budgie|budgies|parrot|parrots|horse|horses|pony|ponies|guinea|goldfish|fish|pet|pets)"
    r"(?:'s|s'|s)?\s+deaths?\b")
THING_DEATH = re.compile(
    r"\b(?:" + "|".join(sorted(THINGS)) + r")(?:'s|s'|s)?\s+deaths?\b")
# The owner form said the other way round: "the death of my laptop" is the same line as "my
# laptops death", and the noun after "death of" is what died. Only that noun is tested, so
# "the death of my dad in his car" stays a bereavement.
DEATH_OF_OWNER = re.compile(
    r"\bdeaths?\s+of\s+(?:the|my|our|a|an|his|her|their|your)\s+((?:[a-z]+\s+){0,2}[a-z]+)\b")

# "died" and "dead" need a person or pet in the line, and no object right before them.
DIED = re.compile(r"\b(died|dying|dead|dies)\b")
DYING = re.compile(r"\b(died|dies)\b")
# "put down" is also "put the phone down", and "put her to sleep" is how a parent describes a
# baby's bedtime: it only counts with a pet as the object, or a vet/had-to/how-it-went beside it.
PUT_DOWN = re.compile(
    r"\bput\s+(?:her|him|it|(?:my|our|the)\s+\w+)\s+(?:down|to sleep)\b|"
    # "i regret putting my dog down": the same death said as a thing in progress. The pet word and
    # the bedtime/loss guard in `_put_down` still decide whether it is the death or the phone.
    r"\bputting\s+(?:her|him|it|(?:my|our|the)\s+\w+)\s+(?:down|to sleep)\b|"
    r"\bput\s+(?:down|to sleep)\b|"
    r"\bhad\s+(?:\w+\s+){0,3}?put\s+(?:down|to sleep)\b|"
    r"\b(?:was|were|been)\s+put\s+(?:down|to sleep)\b")
PET_WORDS = frozenset((
    "dog", "dogs", "cat", "cats", "puppy", "puppies", "kitten", "kittens", "rabbit", "hamster",
    "budgie", "parrot", "horse", "pony", "pet", "pets", "tortoise", "ferret", "guinea", "hen",
    "chicken", "rat", "mouse", "gerbil", "lurcher", "greyhound", "collie", "labrador",
    "fish", "fishes", "goldfish", "snake", "lizard",
))
# A relation said in two words: "my other half", "my support worker". The token list cannot
# hold these, and cutting them to one word would either lose the meaning ("half" is a split in
# the money answer) or name the wrong thing ("support" is not a person).
PEOPLE_PHRASES = (("other", "half"), ("other", "halves"), ("support", "worker"),
                  ("support", "workers"), ("care", "worker"), ("care", "workers"),
                  ("significant", "other"), ("home", "carer"), ("home", "carers"))


# The people in PEOPLE, without the pets: a conditional about a pet is a chore, and a conditional
# about a person ("he will die if nobody helps") is not something to wave away.
HUMAN_WORDS = PEOPLE - PET_WORDS
# What can die: a person or a pet, so "lost my dad" is a loss and "lost my job" is a job.
DEATHABLE = PEOPLE | PET_WORDS
# A word that names an animal and a machine, so the line, not the word, says which (see
# `_can_die` below and `is_a_machine_word` in the engine).
MACHINE_ANIMALS = frozenset(("mouse", "mice"))
# A death is often said without the word: "my cat was run over last night", "our dog got knocked
# down", "my rabbit drowned". The passive voice is what makes it this house's loss - "i ran over a
# cat" is the same accident read from the wheel - so the verb has to follow "was"/"got"/"been",
# and only verbs that are a death on their own are here. "was hit by a car" is left out on
# purpose: people write it about a broken leg as often as about a funeral.
MISADVENTURE = re.compile(
    r"\b(?:was|were|is|are|got|been|being|had been)\s+(?:run\s+over|knocked\s+(?:down|over)|"
    r"drowned)\b|"
    r"\b(?:run|knocked)\s+(?:over|down)\s+by\s+(?:a|the|an)?\s*\w+|"
    r"\bdrowned\b|"
    # A shock that killed: the person was electrocuted and the line says they died. On its own the
    # word is used for a shock survived - "i got electrocuted at work" and "my husband was
    # electrocuted" are the safety card's, which is why it was taken out of this house - so it is
    # here only when the death is said in the same line: "electrocuted and passed away",
    # "electrocuted and didnt make it".
    r"\b(?:was|were|got|been)\s+electrocuted\b(?=[^.?!]{0,45}\b(?:died|dead|killed|"
    r"didn'?t\s+make\s+it|did\s+not\s+make\s+it|passed\s+(?:away|on)|funeral|buried|"
    r"pronounced)\b)|"
    r"\bdied\s+(?:in|after)\s+(?:a\s+|the\s+)?(?:accident|crash|fire|fit|seizure)\b")
# The accident happened and the person or pet is still here: "my brother was run over but he's
# fine", "she's in hospital but recovering". A fright, not a bereavement, so the condolence stays
# out of it and the ordinary reply takes the line.
SURVIVED = re.compile(
    r"\bsurvived\b|\bstill alive\b|\b(?:is|was|seems|doing)\s+(?:ok|okay|alright|fine)\b|"
    r"\bbut\s+(?:he|she|they|it|we|i)(?:'s|s| is| was)?\s+(?:ok|okay|alright|fine|alive)\b|"
    r"\bin (?:the )?hospital\b|\brecovering\b|\bstable\b|\bjust bruises\b|"
    r"\bbroke (?:his|her|their|a|my)\b|\bstitches\b|"
    # "my mate was knocked down but he walked away": the accident happened and he got up.
    r"\bwalked\s+(?:away|off)\b|\bno\s+harm\b|\bunhurt\b|\bnot\s+(?:a\s+)?scratch\b|"
    r"\bnot\s+(?:hurt|injured|serious)\b|\bno\s+(?:injuries|injury|damage)\b")
LOSS_CONTEXT = ("had to", "have to", "put to sleep", "vet", "euthanis", "last week", "last night",
                "yesterday", "we had", "i had", "it was time")

# Whose accident it was: "my cat", "our old dog", "her nan". The words after the owner are
# kept, not just the first one, because "our old dog" and "my little brother" put an adjective
# in front of the one that can die.
OWNED = re.compile(r"\b(?:my|our|his|her|their)\s+((?:\w+\s+){0,2}\w+)")
# A verb carrying an object of its own is not a death of the owner: "my daughter drowned her phone
# in the sink" has the daughter as the one who did it, and "my uncle drowned his sorrows" is a
# drink. The person or pet has to be what the verb happened to.
VERB_OBJECT = re.compile(
    r"\b(?:drowned|run\s+over|knocked\s+(?:down|over))\s+(?:her|his|my|our|their|its?|the|a|an)\b")
# "my dad got knocked over by a bike" is a broken arm as often as a funeral, so a person knocked
# down by a named thing needs the death said in the line ("and killed", "didnt make it"). A pet
# knocked down needs nothing: a dog hit by a car usually did not get up.
KNOCKED_BY = re.compile(r"\b(?:run\s+over|knocked\s+(?:down|over))\s+by\s+(?:a|the|an)\b")
DEATH_SAID = re.compile(
    r"\b(?:died|dead|killed|didn'?t\s+make\s+it|did\s+not\s+make\s+it|lost|passing|passed|"
    r"gone|funeral|put\s+to\s+sleep|euthanis\w*)\b")

LOST = re.compile(r"\b(lost|we lost|i lost|he lost|she lost|they lost)\s+"
                  r"(?:my|our|his|her|their)\s+([a-z]+)")
# "we lost nan" names the person without a possessive: the subject of "lost" is the person.
LOST_BARE = re.compile(r"\b(?:i|we|he|she|they)\s+lost\s+"
                       r"(?!(?:my|our|his|her|their|the|it|a|an|that|this|him|them)\b)([a-z]+)\b")
# The verb was only read in the past tense and only with a possessive, so the same bereavement in
# the present or said of somebody else was read as an occasion: "what do i say when someone loses
# a baby" got the congratulations card ("Congratulations - she is beautiful"), "when a family
# loses a child" got the memory-loss card and "when my friend loses her husband" got a birthday
# card. The object decides, exactly as it does for "lost": a word that can die is a bereavement,
# and "lose weight", "lose my temper", "losing my keys" and "lose the plot" name things that
# cannot, so they are not one. The object may come with a determiner ("loses a baby", "lose the
# baby") or with none ("loses mum").
LOSE_A_PERSON = re.compile(
    r"\b(?:lose|loses)\s+(?:(?:my|our|his|her|their|the|a|an|this|that)\s+)?([a-z]+)")
# The three readings that ask "was that the person or a thing of theirs" read the verb in the
# same forms, so the tense cannot change the answer.
LOST_FORMS = ((LOST, 2), (LOST_BARE, 1), (LOSE_A_PERSON, 1))
# "the loss of my mum has hit me hard" and "losing my wife has hit me hard" say the bereavement
# that "i lost my mum" says, in the noun and in the -ing form, and neither was read as a loss at
# all: the sympathy never came and the follow-up got small talk. Both take an owner and a person
# or a pet, exactly like LOST, so "the loss of my job" and "losing my temper" stay out.
LOSS_OF = re.compile(r"\b(?:the\s+|a\s+|any\s+)?loss\s+of\s+(?:my|our|his|her|their)\s+([a-z]+)")
# The -ing form takes a determiner as well as a possessive: "someone is losing a baby" and
# "losing the baby" are the loss that "losing my baby" is. The relation still has to be a close
# one or the line still needs a grief cue, so "im losing a friend" stays a cooling friendship.
LOSING = re.compile(r"\blosing\s+(?:my|our|his|her|their|a|an|the)\s+([a-z]+)")
# A close relation is mourned the moment the -ing form names them: "losing my mum has been hard",
# "losing my wife hit me for months". The cue above is what a friend needs, because "im losing my
# friend" is as often a friendship cooling; a mum, a husband or a child is not. So the close
# relations skip the cue and everything else still asks for it.
CLOSE = frozenset((
    "mum", "mom", "mam", "mother", "dad", "father", "nan", "nana", "gran", "granny",
    "grandma", "grandmother", "grandad", "granddad", "grandpa", "grandfather",
    "son", "daughter", "child", "baby", "brother", "sister", "wife", "husband", "partner",
    "stepdad", "stepmum", "aunt", "uncle", "cousin", "niece", "nephew", "parents",
))
# "the news of my dad hit me hard": there is no death word at all, and the hit is what says the
# news was a death. A person or a pet still has to be there ("the news of the merger hit the
# shares" is a share price), and "the thought of my mum still breaks me" is the same story.
NEWS_OF = re.compile(
    r"\b(?:news|thought)\s+of\s+(?:my|our|his|her|their)\s+([a-z]+)[^.]{0,24}?"
    r"\b(?:hit|hits|hurt|hurts|broke|breaks|is\s+hard|was\s+hard)\b")
# "losing my friend" is as often a friendship cooling as a death, so the -ing form asks for a
# grief cue of its own: "since losing my dad", "losing my nan last year was hard". The cue is
# time or mourning, and not a feeling word: "im losing my friend and it hurts" is a cooling
# friendship, and the hurt is what every ending sounds like.
LOSS_GRIEF_CUE = re.compile(
    r"\b(?:since|after|still|every|cant|couldnt|miss|missed|cry|crying|cried|grief|grieving|"
    r"funeral|bereave\w*|yesterday|anniversary|"
    r"last\s+(?:year|month|week|night|christmas|summer|winter)|"
    r"(?:in|at|on)\s+(?:january|february|march|april|may|june|july|august|september|october|"
    r"november|december|christmas|christmas\s+eve|boxing\s+day|easter|new\s+year))\b")
# "i lost my son at the park" is ten bad minutes, not a bereavement: a person lost *in a place*
# was mislaid. Only an everyday place counts, so "i lost my dad in january" (a time) and "my mum
# died in hospital" stay a loss.
LOST_IN_A_PLACE = re.compile(
    r"\b(?:in|at|on|into|inside|outside|near|round|around)\s+(?:the\s+|a\s+|an\s+)?([a-z]+)")
PLACES = frozenset("""
supermarket shop shops store town city park parks playground beach seafront street streets
road motorway station airport bus train tube metro queue market mall museum gallery zoo fair
festival concert woods forest hill hills garden gardens pool lido crowd crowds field fields
arcade campsite caravan centre center precinct pier promenade high street roundabout bus stop
coach tram ferry harbour harbor dock docks
""".split())
# Someone with no name is still a person: "what do i say when someone dies" asks the same
# question as "what do i say to my friend". It is only a death when the ask is there, so
# "everyone dies eventually" and "everyone keeps dying in this show" stay remarks.
UNNAMED = frozenset(("someone", "somebody", "anyone", "everyone", "people", "person"))
MEDIA = frozenset(("show", "shows", "film", "films", "movie", "movies", "series", "episode",
                   "episodes", "game", "games", "book", "books", "soap", "documentary", "telly",
                   "tv"))

# "lost my keys", "lost the plot": a thing was lost, which is a bad afternoon, not a death. The
# words here are losses of the person's own state, the way grief is described, so they stay.
LOST_SELF = frozenset(("appetite", "sleep", "confidence", "interest", "motivation", "energy",
                       "joy", "focus", "weight", "voice", "self", "myself", "herself",
                       "himself", "themselves"))
# A cat or dog bringing something dead in is hunting, not a bereavement: "my cat keeps bringing
# dead birds in" is a question about the cat, and nobody has died. The pet has to be the one
# doing something with the carcass, so a pet that has died itself still counts below.
PREY = re.compile(r"\b(?:a\s+|the\s+|another\s+)?(?:dead|dying|half\s+dead)\s+"
                  r"(?:bird|birds|mouse|mice|rat|rats|vole|voles|rabbit|rabbits|squirrel|"
                  r"squirrels|pigeon|pigeons|frog|frogs|hedgehog|hedgehogs|sparrow|sparrows|"
                  r"blackbird|blackbirds|chick|chicks|goldfish|fish)\b")
HUNTING = re.compile(r"\b(bring|brings|bringing|brought|drag|drags|dragging|dragged|catch|"
                     r"catches|catching|caught|kill|kills|killed|killing|left|leaves|leaving|"
                     r"found|finds|dropping|dropped|deposit|deposits|present|presents)\b")
# "we lost the baby" is the same loss as "we lost our baby": people say it with "the". The words
# that follow it say whether the same person turned up again - "we lost the baby in the
# supermarket" is a minute of panic, not a bereavement.
LOST_THE = re.compile(r"\b(?:we|i|he|she|they)\s+lost\s+the\s+([a-z]+)\b")
LOST_THE_FOUND = re.compile(
    r"\b(?:found|got)\s+(?:him|her|them)\b|\b(?:in|at|near|outside|inside|by)\s+the\s+"
    r"(?:shop|shops|park|supermarket|street|station|queue|mall|woods|beach|playground|"
    r"car\s*park|bus|train|airport|market)\b")
# Grief named without a person: "still cry about my mum", "a death is never good news".
STILL_CRY = re.compile(r"\b(?:still|always|every|keep|keeps)\b[^.]{0,24}\b(?:cry|crying|cries|"
                       r"tears|gutted)\b")
# Someone else does the crying: "my son keeps crying", "the baby keeps crying at night", "my dog
# keeps crying". Their tears are not a death, and the condolence that answered them read as if a
# person had died. The speaker's own tears ("i still cry about my mum", "why do i still cry every
# morning") are not matched, so the grief reading above keeps its lines; a line that names an
# actual death still reads as one through the rules before it.
OTHER_WEEPS = re.compile(
    r"\b(?:my|our|his|her|their|the)\s+(?:[a-z']+\s+){0,2}"
    r"(?:keeps?|kept|is|are|was|were|has|have|had|still|always|constantly|every|starts?|started|"
    r"won'?t|wont)\b"
    # The window is a clause, not a word count: "my girls hair is always tangled and she cries"
    # puts the fault between the state and the tears, and a 16-character window missed it, so the
    # condolence answered a combing problem. A full stop ends the window, and a line that names a
    # death reads as one through the rules before this, so no grief line depends on the width.
    r"(?:(?!\b(?:i|we)\b)[^.]){0,40}\b(?:cry|crying|cries|tears|sob\w*)\b", re.I)
# Tears said in a clause of their own, after the trouble: "my girls hair is always tangled and she
# cries", "my sons teeth are always sore and he cries". The tears are somebody else's reaction to a
# thing that is wrong, not a bereavement, and the condolence that answered them read as if a person
# had died. The speaker's own tears ("i still cry about my mum", "i keep crying") are a different
# shape and keep the grief reading, and a line that names a death is read by the rules above this,
# so nothing that is a death depends on it.
THEIR_TEARS_IN_A_CLAUSE = re.compile(
    r"\b(?:and|so|but|then)\s+(?:he|she|they|it|the\s+[a-z]+)\b[^.]{0,24}"
    r"\b(?:cry|cries|cried|crying|sob\w*|weeps?|weeping|tears)\b", re.I)
# The noun with an article or an owner: "a death in the family", "his death hit me hard", "the death
# was sudden". A bare "death is nothing to be scared of" is a sentence about the idea of it, so the
# pattern needs the article or the owner, never the word on its own.
DEATH_AS_A_THING = re.compile(r"\b(?:a|any|the)\s+death\b|\b[a-z]+'?s\s+death\b|"
                              r"\b(?:his|her|their|your|my|our)\s+death\b")
# The same word doing another job. "a death penalty would be wrong" is an opinion, not a loss, and
# "scared to death" is an intensifier; the noun is about death without anyone having died.
NOT_A_DEATH = re.compile(
    r"\bdeath\s+(?:penalty|row|metal|stare|trap|wish|cab|valley|rate|rates|bed|note|star|toll|"
    r"scene|threat|match|laptop|phone|duty|tax|benefit|certificate|notice|inquest|camp)\b|"
    r"\bto\s+death\b|\bdeath of (?:me|him|her|us|them|a\s+salesman)\b|\bblack death\b|"
    r"\bsudden death\b|\bdeath in (?:paradise|venice)\b|"
    r"\b(?:death|deaths)\s+(?:per|rate|rates|toll|count|figures)\b|"
    r"\bdeath of (?:the|my|our|a)\s+(?:[a-z]+\s+){0,2}?(?:high street|cinema|print|telly|tv|"
    r"radio|music|pub|shop|business|club|scene|brand|houseplant|plant|tree|lawn|car)\b")
TOOK = re.compile(r"\b(took|taken|take)\s+(?:his|her|their)\s+own life\b")
# "killed" says a death only when the person named is the one who died: "my grandad was killed
# in a crash" is a bereavement, "my phone was killed by the update", "i got killed on the quiz"
# and "my brother killed it at the gig" are not. A passive or an incident phrase says whose
# death it was, so a pet with something in its mouth stays the pet's story. "killed himself" is
# left to the composer's own pool for a sudden death.
KILLED = re.compile(r"\b(?:was|were|got|been|being|is|are|had been)\s+killed\b"
                    r"|\bkilled\s+(?:in|by)\b")
# A death on a screen is not someone's death, and naming a person does not make it one: "my
# brother was killed in a film last night" is a story. The mistake is only in the incident
# phrase, so what "killed in" points at decides it - a film, a book, a game is a story, and a
# crash is not, which keeps "my nan was killed in a crash during the film" a bereavement.
KILLED_IN = re.compile(r"\bkilled\s+(?:in|on|during|at)\b")

STORY_MEDIUM = frozenset("""film films movie movies book books novel novels play episode
    episodes series documentary scene chapter show netflix tv game games anime comic comics
    season trailer storyline soap cartoon quiz""".split())
STORY_INCIDENT = frozenset("""crash accident road motorway car bike motorbike lorry truck bus
    train plane bomb blast explosion shooting shot stabbing stabbing attack fire house
    hospital childbirth home work""".split())
# The same mistake with the title instead of the medium: "my mate got killed on call of duty".
# Only titles people use as the place a thing happens, so a real line keeps its reading.
GAME_TITLES = re.compile(
    r"\b(?:call\s+of\s+duty|fortnite|minecraft|roblox|fifa|halo|overwatch|zelda|mario|"
    r"pokemon|among\s+us|gta|grand\s+theft\s+auto|world\s+of\s+warcraft|league\s+of\s+"
    r"legends|apex\s+legends|counter\s+strike|pubg|rocket\s+league|skyrim|tetris|"
    r"pac\s*man|street\s+fighter|mortal\s+kombat)\b")


def _killed_in_a_story(clean):
    """True when the thing "killed in/on" points at is a story, not an incident."""
    if GAME_TITLES.search(clean):
        return True
    found = KILLED_IN.search(clean)
    if not found:
        return False
    for word in clean[found.end():].split()[:4]:
        if word in STORY_INCIDENT:
            return False
        if word in STORY_MEDIUM:
            return True
    return False


# A birthday nobody reached: "my mum would have been 70 this week" counts the day that did not
# come, and it is the grief, not a fact about a living person. It needs "would have been" and a
# person in the line, so "the shop would have been open" and "my daughter would be 5 next week"
# (a birthday still coming) are left alone.
WOULD_HAVE_BEEN = re.compile(r"\bwould(?:'ve| have)\s+been\s+(?:\d{1,3}|(?:her|his|their)\s+"
                             r"\d{1,3})\b")

# "passed on" is also "i passed on the job offer", "we passed on the house" and "i passed on
# dessert", so it is not unambiguous the way "passed away" is: it needs a person or a pet as
# its subject, and no object straight after it, the way "died" does.
PASSED_ON = "passed on"
PASSED_ON_SUBJECT = frozenset(("he", "she", "they", "him", "her", "them"))
PASSED_ON_OBJECT = frozenset((
    "the", "a", "an", "my", "your", "his", "her", "their", "our", "this", "that",
    "these", "those", "it", "them", "some", "any", "all", "another", "one", "to",
))
# "my mum passed on the 3rd" is still a death: a date after "the" is not an object.
MONTHS = frozenset((
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
))

# "passed" on its own is the same word as "passed away" and it is how a lot of people say a
# death: "my grandad passed in jan", "my dad passed last year", "she passed peacefully". It is
# also "i passed my test", "the deadline passed" and "he passed me the salt", so it takes the
# same subject rule as "passed on" - a person or a pet before it - and what comes after it has
# to be a date, a time, or nothing at all.
PASSED_ALONE = "passed"
PASSED_ALONE_TAIL = frozenset(("away", "on", "out", "by", "over", "up", "back"))
# "he passed me the salt" and "she passed him the ball": a pronoun straight after "passed" is the
# thing being handed over, not the next clause.
PASSED_ALONE_HANDED = frozenset(("me", "him", "her", "us", "them", "it", "you"))
# The bare noun objects: "my dad passed gas", "my mum passed comment on my cooking", "she passed
# water". A determiner covers most objects, but these idioms put the noun straight after the
# verb, and a condolence to a line about wind is the worst reply the bot can give.
PASSED_ALONE_NOUN = frozenset((
    "gas", "wind", "water", "blood", "comment", "comments", "remark", "remarks",
    "judgement", "judgment", "sentence", "motion", "muster", "note", "notes", "word",
    "words", "message", "messages", "memo", "review", "stone", "stones", "ball", "balloon",
    "duty", "laws", "law", "bill", "act", "exam", "exams", "test", "tests",
))
# The things a person passes that are good news. "my mum got her results and she passed" was met
# with "I'm so sorry to hear that" - the same word as "my dad passed in jan", and what tells them
# apart is earlier in the line: a test, an exam, a result is what was passed. Read before the
# end-of-line reading, because there nothing follows the word to go on.
PASSED_A_RESULT = frozenset((
    "results", "result", "exam", "exams", "test", "tests", "interview", "course", "grade",
    "grades", "marks", "finals", "mocks", "driving", "theory", "gcse", "gcses", "alevels",
    "a-levels", "degree", "dissertation", "viva", "audition", "assessment", "inspection",
    "mot", "physical", "boards", "revision", "resit",
))

# "my dad passed in jan" is a death; "she passed in maths" is a mark.
PASSED_DATE = frozenset((
    "jan", "january", "feb", "february", "mar", "march", "apr", "april", "may", "jun", "june",
    "jul", "july", "aug", "august", "sep", "sept", "september", "oct", "october", "nov",
    "november", "dec", "december", "christmas", "easter", "spring", "summer", "autumn",
    "winter", "the",
))
PASSED_TIME = frozenset((
    "morning", "afternoon", "evening", "night", "week", "weekend", "month", "year", "monday",
    "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
))

# An object right before the death word means the object died: "my phone died", "the battery
# died", "my car died on the motorway".
OBJECTS = frozenset((
    "phone", "phones", "battery", "car", "engine", "laptop", "computer", "pc", "tv", "telly",
    "boiler", "wifi", "router", "tablet", "console", "watch", "camera", "mower", "lawnmower",
    "plant", "plants", "tree", "tree", "hedge", "weed", "weeds", "flower", "flowers", "fire",
    "signal", "connection", "internet", "broadband", "radio", "speaker", "speakers", "bulb",
    "fuse", "printer", "headphones", "earphones", "remote", "kettle", "toaster", "washer",
    "dishwasher", "fridge", "freezer", "oven", "hoover", "vacuum", "scooter", "bike", "van",
))

# A bedtime routine, not a death: "put my cat to sleep at night", "sleep through the night".
BEDTIME = ("at night", "through the night", "all night", "every night", "bedtime", "bed time",
           "sleep through", "sleeps through", "sleeping through", "nap")

# "dead" is also an intensifier: "dead tired", "dead against it", "dead easy", "a dead end".
DEAD_IDIOM = frozenset((
    "against", "tired", "easy", "end", "ends", "battery", "silent", "pan", "weight", "set",
    "right", "on", "last", "by", "to", "heat", "centre", "center", "line", "bolt", "cert",
    "beat", "loss", "lift", "straight", "funny", "wrong", "certain", "serious", "stop",
    "cheap", "ahead", "slow", "cheerful", "glad", "lucky", "proud", "good", "bad", "keen",
    "jealous", "happy", "sure", "tricky", "hard", "quiet", "boring", "rude", "funny",
))
# "dead" before a word it describes is not a death: "dead birds", "dead leaves", "dead battery".
# The words that keep it a statement about a person are the ones that cannot be described by it.
DEAD_PREDICATE = frozenset("""
a an the this that these those my your his her its our their
and or but so if because when while after before since until till
in on at by for to from with without about of into onto over under
is was are were be been being am
now today already still yet again too also just only even ever never always here there
every any some no not nothing nobody none all both each other else
""".split())


def _dead_is_not_a_death(words, index):
    """True when the "dead" at `index` is not a death.

    Either it describes the word after it ("dead birds", "dead leaves on the lawn") or the two
    words are an idiom ("dead easy", "dead against it", "the battery is dead").
    """
    if index + 1 >= len(words):
        return False
    following = words[index + 1]
    return following in DEAD_IDIOM or following not in DEAD_PREDICATE


# The future tense of a death: a person or a pet "is going to die", "is dying soon", "will not
# make it". Only with a person or pet in the line, so "this plant is going to die" stays a plant.
GOING_TO_DIE = re.compile(
    r"\b(?:going\s+to|gonna|about\s+to|soon\s+to|will|won'?t|wont|isn'?t\s+going\s+to)\s+"
    r"(?:die\b(?!\s+(?:laughing|of\s+(?:laughter|boredom|embarrassment|shame|excitement)))|"
    r"pass\s+away|make\s+it\b(?!\s+(?:to\s+the|in\s+time|home))|be\s+put\s+(?:down|to\s+sleep))")
# A death still ahead of you, but said as a condition: "... will die if i go away", "... are going
# to die unless we clean the tank". Nothing has died and nothing is dying; the line is a job.
CONDITIONAL_TAIL = re.compile(
    r"\b(?:going\s+to|gonna|about\s+to|will|wont|won'?t|shall)\b[^.?!]{0,30}?"
    r"\b(?:die|dies|be\s+put\s+(?:down|to\s+sleep))\b[^.?!]{0,40}?"
    r"\b(?:if|unless|when|before|otherwise|or\s+else|without)\b")

LAUGHING = ("died laughing", "die laughing", "dying to", "died of embarrassment",
            "die of embarrassment", "nearly died", "almost died", "i could have died",
            "would die", "died down", "die down", "legs are dead", "arm is dead",
            "legs were dead", "arms are dead", "feet are dead", "hands are dead",
            "is dead to me", "drop dead gorgeous", "dead on my feet", "dead on time")

# The hard time belongs to somebody else: "my mum is lonely since dad died" is the mum's
# loneliness, and "take today slowly" is sympathy for the wrong person - the user has not said
# they are lonely, they have said their mum is. `whose` cannot read this shape: it looks for a
# possessive ("my mum's cat") or his/hers ("her dad"), and here the relation is the subject of
# the sentence and the state is theirs. The death is in the same breath as the reason, so only a
# lonely/low line that names a death is read this way: "my mum is lonely" with no death in it is
# an ordinary question about a lonely parent, and the family entries answer it.
A_RELATION_IN_A_HARD_TIME = re.compile(
    r"\bmy\s+(?:mum|mom|mam|mother|dad|father|nan|nana|gran|granny|grandma|grandad|"
    r"granddad|grandpa|sister|brother|son|daughter|wife|husband|partner|friend|mate|neighbour|"
    r"neighbor|aunt|auntie|uncle|cousin|niece|nephew|parents|family)\b"
    r"[^.?!]{0,40}?\b(?:is|are|seems?|has\s+been|have\s+been|keeps?\s+(?:being|getting)|"
    r"gets?|got)\b[^.?!]{0,25}?"
    r"\b(?:lonely|alone|on\s+(?:his|her|their)\s+own|by\s+(?:him|her|them)self|withdrawn|"
    r"not\s+(?:him|her|them)self|low|down|miserable|unhappy|quiet|stuck\s+at\s+home)\b",
    re.IGNORECASE)

# The reply for that line: meet the death, then the one practical thing that helps somebody
# living on their own after one - a standing invitation they can count on, offered as a time and
# a place rather than "let me know" - and hand the turn back with a question about them. What the
# person typing needs is not sympathy for a loss they have not claimed.
THEIR_HARD_TIME_REPLIES = (
    "That's a heavy thing for them to carry, and it lands on you too. What helps is a standing "
    "date they can count on - the same walk or the same coffee each week - rather than \"let me "
    "know if you need anything\". What do they like doing most?",
    "The quiet after a death is what does the damage, so keep the invitation concrete and keep "
    "making it: \"Tuesday, I'll pick you up at ten\" lands where \"I'm here if you need me\" "
    "does not. Are they eating and sleeping all right?",
    "Ring rather than text, at the same time each week, and keep asking after a no - that is "
    "what stops somebody going days without hearing a voice. Is there anyone else close by, or "
    "are you it?",
)

# "Whose loss it is: a friend's mum who died is not the user's own loss.
SOMEONE_ELSES = re.compile(
    r"\b(?:my|our|a|an|the|one of my)\s+(?:friend|friends|mate|mates|colleague|colleagues|"
    r"neighbour|neighbors|"
    r"neighbours|neighbor|boss|landlord|girlfriend|boyfriend|ex|coworker|workmate)"
    # "a friend whose dad died" and "a mate of mine whose mum has died" are the same question as
    # "my friend's dad died", and with a possessive in the pattern only the second one was read as
    # somebody else's loss: the first got a condolence for the person asking, which is sympathy
    # for a death that has not happened to them. "whose" and "of mine" say whose loss it is.
    r"(?:'s|s)?\s+(?:(?:of mine|of ours)\s+)?(?:whose\s+|with\s+|who\s+has\s+)?"
    r"(?:\w+\s+){0,2}?"
    r"(?:mum|mom|mother|dad|father|son|daughter|wife|husband|partner|nan|gran|grandma|"
    r"grandad|grandpa|brother|sister|aunt|uncle|cousin|child|baby|family)\b")
HIS_HERS = re.compile(
    r"\b(?:his|her|their)\s+(?:mum|mom|mother|dad|father|son|daughter|wife|husband|partner|"
    r"nan|gran|grandma|grandad|grandpa|brother|sister|aunt|uncle|cousin|child|baby|dog|cat|"
    r"funeral|wake|memorial|service|viewing|burial)\b")

# A loss that belongs to someone else even though the line names no friend: "my mum's cat died
# last week" is the mum's loss, "my dad's dog died" the dad's, "my mum's friend died" the mum's
# again. The possessive names who had it, so the sympathy is for them and what the user needs is
# what to say to them.
SOMEONE_ELSES_OWN = re.compile(
    r"\b(?:my|our)\s+[a-z]+(?:'s|s'|s)\s+(?:[a-z]+\s+){0,2}?(?P<who>"
    + "|".join(sorted(PEOPLE)) + r")\b")

# An animal nobody in the house keeps is not the user's to grieve: "the cat next door died last
# year", "a cat died in our street", "the dog over the road was put down". It is still a death,
# so it gets a warm line rather than the store's shrug, but not sympathy for a loss of theirs.
A_STRANGERS_ANIMAL = re.compile(
    r"\b(?:the|a|an|this|that)\s+(?:[a-z]+\s+){0,2}?(?:"
    + "|".join(sorted(PET_WORDS)) + r")s?\s+(?:[a-z]+\s+){0,4}?\b"
    r"(?:next door|over (?:the )?road|upstairs|downstairs|"
    r"in (?:our|the|my) (?:street|road|close|lane|block|crescent|estate))\b")

CARD = re.compile(r"\b(card|cards|condolence|sympathy|note|letter|message|text|msg)\b")
# "something to write in a bereavement card" and "bereavement card words" ask for the same
# words as "what do I write in a condolence card", but carry none of the asking shapes above.
# "write me a eulogy for my mum" is a page due, not a death to be comforted about: the person is
# at a desk, and "I'm sorry, be gentle with yourself" leaves them with nothing to read out. The
# writing is the ask, and bot/knowledge/wording.py::write-a-eulogy is the module that answers it.
# Only the word itself, and only next to a writing verb: "i have to give a reading at the funeral"
# is still a bereavement, and only the eulogy-to-write is a page due.
EULOGY_WORD = re.compile(r"\b(eulogy|eulogies)\b")
EULOGY_ASK = re.compile(
    r"\b(write|writing|wrote|help|helped|how|draft|start|starting|opening|open|begin|example|"
    r"examples|template|structure|length|long|short|words|word|minutes|include|say|saying|"
    r"nervous|stuck)\b")


# A card the person has to write or sign is the card pool; a letter, a text or a message on its
# own is not, so "his sister sent me a message" stays out of it.
CARD_TO_WRITE = re.compile(r"\b(card|cards|condolence|condolences|sympathy|note)\b")
WRITE_WORD = re.compile(
    r"\b(write|writing|wrote|put|say|saying|sign|signing|send|sending|word|words|something|"
    r"anything|line|lines)\b")
WEAR = re.compile(r"\b(?:what|which)\s+(?:do|should|can|could)\s+i\s+(?:wear|put on)\b|"
                  r"\bwhat\s+to\s+wear\b|\bdress\s+code\b")
ASK_WORDS = re.compile(
    r"\b(what do i (?:say|write|put|tell)|what to (?:say|write|put)|what should i (?:say|write|"
    r"put|tell)|what can i say|how do i (?:say|comfort|help|write|tell)|how to (?:comfort|"
    r"write|word)|any ideas for what to say|words for|what do you say)\b")
QUESTION = re.compile(
    r"\b(is it normal|is that normal|why do i|why am i|how long (?:does|will|do)|does it "
    r"(?:get|ever)|will it (?:get|ever)|cant sleep|can't sleep|keep (?:crying|waking)|"
    r"still (?:cry|crying|hurts|gutted|struggling)|when does it)\b")

# The grief question shapes come in two kinds. Some ask about the loss ("is it normal", "why do i",
# "how long does it", "does it get better"); the rest only report what it is doing to them ("cant
# sleep", "keep crying", "still crying"). A report that names a thing with an answer of its own -
# sleep, food, the mornings - is answered by the entry for that thing, and a turn after "i miss my
# mum" it was answered with "most people find the same" instead of the sleep routine.
GRIEF_ASK_FORM = re.compile(
    r"\b(is it normal|is that normal|why do i|why am i|how long (?:does|will|do)|does it "
    r"(?:get|ever)|will it (?:get|ever)|when does it)\b")
# After a death the practical questions are not grief: "how much does a funeral cost", "how long
# does probate take", "what should i cook for the wake", "how do i ask for bereavement leave".
# The answer modules have the facts, so the composer stands aside rather than offering comfort
# about the wrong thing - "if you can make it, go" is not an answer to what a funeral costs.
PRACTICAL = re.compile(
    r"\b(cost|costs|price|prices|pricing|cheap|cheapest|expensive|afford\w*|"
    r"pay|pays|paid|paying|payment|payments|cover|covers|covered|"
    r"how much (?:is|are|was|were|does|do|will|did)|"
    r"probate|paperwork|document\w*|register|registered|registering|certificate|death certificate|"
    r"wills|estate|insurance|solicitor|lawyer|undertaker|funeral director|coffin|crematorium|"
    r"cook|cooking|cooks|food|sandwiches|buffet|catering|caterer|drinks|flowers|order|book|booking|"
    r"berea\w+ leave|time off|back to work|allowance|benefit|benefits|grant|quotes?|forms?)\b")
# ...unless the line is asking about the grief itself, which stays here.
GRIEF_CUE = re.compile(
    r"\b(feel|feels|feeling|feelings|cope|coping|sleep|sleeping|crying|cry|normal|miss|missing|"
    r"heartbroken|numb|empty|guilt|guilty|angry|lonely)\b")

# A death still ahead of the person is not a condolence for a death that has happened. "My dog
# is being put down tomorrow" got "Some days will be heavier than others", which speaks as if the
# dog had gone and says nothing about the day that is coming; the days before are their own thing
# and they have things in them a person can do. The pool is read only for a death the line puts
# ahead of them (`NOT_YET`) that is a pet's: a person dying is answered by the loss pools, since
# what to say to a dying parent is not a paw print and a cremation.
# The same reading for a person: "my dad is dying of cancer" is a death that has not happened,
# and "I'm sorry, that's a real loss" answers it as if it had. What the days before a death ask
# for is being there, asking what will keep them comfortable, and saying the things now. Read
# only when the line names a person (`_a_person_dying`): a phone, a battery and a house plant all
# die, and none of them wants this.
SOMEONE_DYING = (
    "I'm sorry you are facing this. The waiting is the hardest part of it: ask the doctors what to "
    "expect and what will keep them comfortable, say what you would regret not saying, and let "
    "people help you - this is not a thing to carry on your own.",
    "I'm sorry. Being there is most of it: sit with them, keep the room calm, and let them talk "
    "about it or not. Ask about the pain relief and who you ring at night, so you know what to do "
    "when the time comes.",
    "I'm sorry. Spend the time on what they want rather than on what you think you should be "
    "doing. Tell the people around you what is happening - you will need them, and most of them "
    "will want to help.",
    "I'm sorry. Ask the doctor to explain what the next few weeks look like, in plain words, and "
    "write it down - it is hard to hold in your head. Then let the rest go and be with them.",
)


# The days before a death of an animal, and the wording is "them" rather than "him": this pool
# was written for a dog, and the vet's timeline now reaches a cat, a rabbit or a horse as well -
# a cat is as often "she", and the sex of the animal is not something the chat has to know.
THE_DAYS_BEFORE = (
    "I'm sorry the time is coming. Make the days they have left good ones: their favourite food "
    "and company, their usual routine as far as they can still enjoy it. Ask the vet what will "
    "keep them comfortable and what the last day will be like - knowing that is what makes it "
    "bearable.",
    "I'm sorry. The waiting is the hard part now: ask the vet to walk you through the day itself "
    "before it comes, so nothing about it is a surprise, and spend the time you have with them.",
    "I'm sorry you are facing this. Say the things you want to say while they can still hear them, "
    "spoil them a little, and be there at the end if you can bear it - most people are glad they "
    "were. Tell the vet now that you want to be there, so nobody has to ask you on the day.",
    "I'm sorry. You are doing the last kind thing for them, and a day too early is kinder than a "
    "day too late. Keep them comfortable and close, and tell the vet you want each step explained "
    "before it happens.",
)

# "What do i do now" once the death has happened. The first days are a short practical list, and
# saying it plainly is more use than a condolence: on the morning after, the person is being
# asked to organise things they have never organised before. The register office is one office
# and Tell Us Once is one code, so the paperwork is less than it looks.
FIRST_DAYS_PERSON = (
    "Nothing has to be sorted today. When you are ready it is the register office first - within "
    "five days in England and Wales - and then the funeral director, who takes it from there and "
    "tells you what to bring. Ask someone to sit with you for the forms.",
    "The practical list is shorter than it looks: the doctor or coroner gives you the medical "
    "certificate, you register the death at the local register office, and the funeral director "
    "handles what comes next. Tell Us Once covers the tax office, the council and benefits in one "
    "go. Everything else can wait.",
    "Take it in the order it comes. Register the death - five days, in England and Wales - and the "
    "register office gives you the certificates for the bank and the insurers and a Tell Us Once "
    "code. The rest of it, the house and the belongings and the letters, none of that is this "
    "week's job.",
)

# The same question about an animal: the vet does the practical part, and the only choice left
# is what happens to the body, so nothing here asks them to arrange anything today.
FIRST_DAYS_PET = (
    "Nothing has to be decided today. Ring the vet when you can face it and they will explain "
    "cremation or a home burial, and what you can keep - a paw print, a lock of fur. The rest of "
    "the day can just be quiet.",
    "The vet does the practical part, so the one thing to think about is what you would like done "
    "with their body, and whether you want them back home afterwards. Everything else can wait, "
    "and asking for a paw print or a clipping of fur is worth doing if you might want it.",
    "There is no rush to decide anything. The vet will talk you through the choices when you ring "
    "them, and they are used to being asked to wait while you think. Take the day slowly - people "
    "often find the first one is the hardest.",
)

# A life that is ending is often said without the word: "my dad is at the end", "my nan is on her
# last legs", "she is fading fast", "the doctors say there is nothing more they can do". Every one
# of those was read as something else - an ordinary chat, a breakup, a waiting-room question - so
# the reader only knew the plain words. The fence is the same rule as the pet one below: ask what
# follows the phrase, because "my dog is at the end of the garden" and "my cat is fading into the
# background" are the same words and not the same week. "at the end" has to stop the sentence or
# say whose life; "fading" has to be away, fast or now.
AT_THE_END = re.compile(
    r"\bat\s+the\s+end\b"
    r"(?=\s*(?:[,.!?;]|$)|\s+of\s+(?:his|her|its|their)\s+(?:life|days|time))"
    r"|\bon\s+(?:his|her|its|their)\s+last\s+legs\b"
    r"|\bfading\s+(?:away|fast|now)\b"
    r"|\b(?:is|are|seems?|looks?)\s+fading\b(?=\s*(?:[,.!?;]|$))"
    r"|\bnothing\s+more\s+(?:they|we|the\s+vet|the\s+doctors?|anyone)\s+can\s+do\s+"
    r"for\s+(?:me|us|him|her|them|my|our|his|their)\b"
    # "the vet says there is nothing more", "the doctors have said theres nothing more": the give-up
    # that stops the sentence, which is the shape a frightened owner types ("my dog keeps having
    # seizures and the vet says there is nothing more") and the one the give-up reader misses when
    # there is no "can do" after it. A care word is what says it is somebody's life and not a job.
    r"|\b(?:vets?|doctors?|consultants?|specialists?|oncologists?|surgeons?|hospital|hospice|"
    r"nurses?)\b[^.?!]{0,30}\bnothing\s+more\b(?=\s*(?:[,.!?;]|$))")

# A person who is dying is still here, and the line that says so is not asking for a condolence
# card: "that's a real loss" and "take today slowly" are answers about the week after the
# funeral, and they land on someone whose father is in the next room. The reader already counts
# the present tense as a loss (GOING_TO_DIE: the future tense is how people say it while it is
# happening), so this is the wording that goes with it, not a second reading. A line that also
# says a death has happened ("my dad died, my mum is dying too") keeps the death pools.
DYING_NOW = re.compile(
    # "she is dying her hair" and "he is dying to meet you" are not somebody dying: the word after
    # "dying" is what tells them apart, so a hair, an offering and an errand are left out.
    r"\b(?:is|are|am|was|were|isn'?t|aren'?t|isnt|arent)\s+(?:\w+\s+)?dying\b"
    r"(?!\s+(?:to|for|my|her|his|their|your|our|the|a|an)\b)"
    r"|\bdying\s+of\s+(?:cancer|the\s+cancer|dementia|alzheimers|alzheimer'?s|"
    r"motor\s+neurone|mnd|huntingtons?|parkinsons?|copd|heart\s+failure|kidney\s+failure|"
    r"liver\s+failure|aids|leukaemia|leukemia|a\s+brain\s+tumour|a\s+tumour|covid)\b"
    r"|\b(?:(?:is|are|was|were)\s+(?:now\s+)?terminal|terminally\s+ill|"
    r"end\s+of\s+life|palliative|"
    r"weeks\s+to\s+live|months\s+to\s+live|days\s+to\s+live|"
    r"(?:is|are|was|were)\s+(?:now\s+)?(?:in|at)\s+(?:a\s+)?hospice|"
    r"on\s+(?:her|his|their)\s+way\s+out)\b")
# The words that say a death is ahead without saying "dying": the grief starts here, and the
# composer answers with DYING_REPLIES because the person is still in the room. "my mum works in
# a hospice" is a job, so the hospice has to be where the person is.
ANTICIPATED = re.compile(
    r"\b(?:palliative|terminally\s+ill|(?:is|are|was|were)\s+terminal|end\s+of\s+life|"
    r"weeks\s+to\s+live|"
    r"months\s+to\s+live|days\s+to\s+live|"
    r"(?:is|are|was|were)\s+(?:now\s+)?(?:in|at)\s+(?:a\s+)?hospice)\b")
DYING_ALREADY = re.compile(
    r"\b(?:died|has\s+died|had\s+died|passed\s+away|was\s+buried|the\s+funeral|"
    r"the\s+death\b|my\s+late\b)\b")


def is_dying_now(text):
    """True when someone of ours is dying but not dead: "my dad is dying", "she's terminal".

    Kept apart from `reads_as_loss` on purpose - the reading is the reader's, and this only
    decides which wording fits. A pet dying counts: the dog in front of them has not gone yet.
    """
    said = text if isinstance(text, str) else " ".join(words_of(text))
    said = _spoken(said)
    clean = _tight(said)
    words = words_of(said)
    if not (DYING_NOW.search(clean) or _the_end_is_near(clean, words)
            or AT_THE_END.search(clean)):
        return False
    if DYING_ALREADY.search(clean):
        return False
    if _WORKING_WITH_THE_DYING.search(clean) and not _SAID_DYING.search(clean):
        return False  # "my mum is a palliative care nurse" is a job, not a father in the next room
    if _the_end_is_near(clean, words) and not DYING_NOW.search(clean):
        # The give-up names the doctor or the hospital rather than the person, and the person is
        # the one the chat is about: "the consultant said its a matter of time" is somebody dying.
        return True
    if _the_family_is_told(clean):
        # The strongest of those sentences carry no person at all: "theyve said its palliative
        # now", "the oncologist said the treatment isnt working anymore". Nothing else in the
        # line says who, and the words say it for them.
        return True
    return (bool(set(words) & (HUMAN_WORDS | PET_WORDS | _PEOPLE_PRONOUNS))
            or _a_role_phrase(clean))


# The words for the people who do this for a living: a line with one of them is about the job.
# The job reading needs the person to *be* the professional ("my mum is a palliative care nurse")
# or to do it for a living ("she works at the hospice"), never a mention of one: "my dad is dying
# and the nurses are amazing" is a father in the next room, and so is "my nan is in a hospice and
# the carers are lovely", which is the "Noted:" echo this whole piece exists to stop.
_WORKING_WITH_THE_DYING = re.compile(
    r"\b(?:works?|worked|working|volunteers?|volunteering)\s+(?:in|at|for|with)\b"
    r"|\b(?:is|are|was|were|am)\s+(?:a\s+|an\s+|the\s+|my\s+|our\s+)?"
    r"(?:\w+\s+){0,2}?(?:nurse|nurses|doctor|doctors|gp|carer|carers|consultant|registrar|"
    r"paramedic|paramedics)s?\b")
# Said plainly, "dying" beats the job reading: the people helping can be named beside it.
_SAID_DYING = re.compile(r"\bdying\b")


def dying_in_the_chat(memory, turns=6):
    """True when a line earlier in this chat said that someone of ours is dying.

    The question after it ("is it normal to cry all the time", "how do i cope") is about the
    person asking, and it says nothing about a death, so on its own it reads as a bereavement
    and gets the answer for after the funeral. The chat already knows which week this is.
    """
    history = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(history, list):
        return False
    for said in history[-turns:]:
        text = said.get("user") if isinstance(said, dict) else None
        if isinstance(text, str) and is_dying_now(text):
            return True
    return False


def _a_pet_of_ours(line, words=None):
    """True when the one dying is an animal, so the vet has the timeline and not a hospice."""
    if words is None:
        words = words_of(line)
    said = set(words)
    return bool(said & PET_WORDS) and not bool(said & HUMAN_WORDS)


def _the_end_is_near(tight, words=None):
    """True when the line says the treatment has run out or the days are counted.

    These are the sentences somebody's dying arrives in, and none of them has a death word in it:
    "the doctor said theres nothing more they can do", "the vet says theres not much more they can
    do", "theyve stopped mums chemo", "the hospital said theres nothing else they can try", "the
    consultant said its a matter of time", "my dad has weeks left". The reader above knew "dying",
    "terminal" and "hospice" and answered all of them as small talk.

    The who is what keeps the reading honest: a give-up is about somebody dying when a doctor, a
    vet or a hospital says it, while the council, the mechanic and the bank say the same sentence
    about a noise, a car and a loan and each has an entry that answers it.
    """
    if words is None:
        words = words_of(tight)
    who = bool(CARE_WHO.search(tight))
    if who and (NOTHING_MORE_TO_DO.search(tight) or TREATMENT_STOPPED.search(tight)
                or (NOT_WORKING.search(tight) and SERIOUS_CARE.search(tight))):
        # The treatment that stopped working is the treatment that ran out, but only when a
        # specialist said it: "my acne treatment isnt working anymore" is a chemist's line. And
        # the give-up that names something is only about somebody when what it names is one:
        # "nothing more they can do about my knee" is an orthopaedic appointment (see
        # `_the_give_up_is_about_somebody`).
        if not NOTHING_MORE_TO_DO.search(tight) or _the_give_up_is_about_somebody(tight, words):
            return True
    if _the_give_up_without_a_care_word(tight, who):
        # "they said there is nothing more they can do for her" - the shape and the person, said
        # by somebody, with no care word to carry it.
        return True
    if MEDICATION_STOPPED.search(tight) and SERIOUS_CARE.search(tight):
        # The pills only count next to the illness: "theyve stopped mums medication and started
        # her on morphine" is the last of the care, "stop the medication" is a chemist's note.
        return True
    if says_the_last_drug(tight):
        # The last drug needs no other word: "they put my dad on morphine" is the news on its
        # own, and it was answered with the pleasantry for a small account of a day.
        return True
    somebody = (_has_person(words) or _has_pet(words) or "she" in words or "he" in words
                or bool(HUMAN_WORDS & set(words)))
    if FINAL_DAYS.search(tight):
        # "shes in her final weeks" needs no other word to place it: the possessive already says
        # whose weeks they are, and "the final weeks of the season" has none.
        return True
    if not somebody and not who:
        # Nothing says whose days these are, and "its only a matter of time before they close the
        # shop" is the same words about a shop. The patterns below that name nobody need the
        # doctor's word to carry them; the ones below that need somebody are read as a death
        # only when it is there.
        return _the_family_is_told(tight)
    if DAYS_LEFT.search(tight) and not NOT_THE_END.search(tight):
        # Nobody named, so only a doctor or a hospital saying it makes the days somebody's; a
        # pronoun is not enough ("its only a matter of time before they close the shop"), but
        # "she has days left" is the person the chat has been about.
        return True
    if COULD_BE_DAYS.search(tight) and not NOT_THE_END.search(tight):
        # "shes in her final weeks", "weve been told it could be days": the same count in other
        # words, and this one is only read with somebody named, so "final weeks of the season" and
        # "it could be days before the parcel comes" are left alone. A pronoun is not that
        # somebody: "she said it could be days of rain" and "it might be days before he texts
        # back" borrow the speaker's, and the days are a wait for something (see DAYS_WAIT_FOR).
        return (not DAYS_WAIT_FOR.search(tight)
                and (who or _has_person(words) or _has_pet(words)))
    if LAST_STAGES.search(tight):
        return True
    if NOT_GETTING_BETTER.search(tight):
        # "my nan isnt going to get better" - said of a person it is the death, said of a back it
        # is the back, and `_has_person`/`HUMAN_WORDS` is what tells them apart.
        return True
    if GIVEN_UP_ON.search(tight) and who:
        return True
    if PREPARE.search(tight) and who and not PREPARE_OTHERWISE.search(tight):
        return True
    if OFF_LIFE_SUPPORT.search(tight) and not OFF_SUPPORT_WELL.search(tight):
        return True
    if HOSPICE_CARE.search(tight) and not HOSPICE_JOB.search(tight):
        return True
    if (PALLIATIVE_ITSELF.search(tight) and not asks_anything(tight)
            and not _WORKING_WITH_THE_DYING.search(tight)):
        # "my mum is a palliative care nurse" is a job with the same word in it.
        return True
    return False


def _the_family_is_told(tight):
    """True for the give-up that names nobody but carries the specialist's word.

    "theyve said its palliative now", "the consultant said the treatment isnt working anymore",
    "the doctor said to prepare ourselves": the person is in the chat, not in the line, and the
    other readings answered these as small talk. Only the words that are a death in every context
    are here - a specialist or an oncologist, palliative care, hospice - so "my acne treatment isnt
    working anymore" and "are you a consultant" stay where they were.
    """
    serious = bool(SERIOUS_CARE.search(tight))
    if serious and (NOT_WORKING.search(tight) or PREPARE.search(tight)):
        return not PREPARE_OTHERWISE.search(tight)
    if (PALLIATIVE_ITSELF.search(tight) and not asks_anything(tight)
            and not _WORKING_WITH_THE_DYING.search(tight)):
        # "theyve said its palliative now" is the sentence, "what is palliative care" is the
        # question about it, and the second one is somebody reading up, not somebody losing.
        return True
    if COULD_BE_DAYS.search(tight) and TOLD_US.search(tight):
        # "weve been told it could be days" is a family in a relatives' room, and "they said it
        # could be days for the results" is the same words about a wait.
        return not DAYS_WAIT_FOR.search(tight)
    if OFF_LIFE_SUPPORT.search(tight) and not OFF_SUPPORT_WELL.search(tight):
        return True
    if HOSPICE_CARE.search(tight) and not HOSPICE_JOB.search(tight):
        return True
    return False


def _the_vet_said_it(tight, words):
    """True when a vet is the one who said it, so the animal's own pool answers."""
    return ("vet" in tight.split() or "vets" in tight.split()) and not (
        set(words) & HUMAN_WORDS)


# What the doctor has given up on, when the line says it: "about my knee", "for my back". A
# give-up with nothing after it is the whole of somebody's care; one that names an object is only
# that news when the object is a person or the illness itself.
THE_GIVE_UP_NAMES = re.compile(
    r"\b(?:do|done|doing|try|trying|offer|suggest)\s+(?:about|for|with|on|to)\s+(.{0,40})")
# The people words a give-up can name after it, including the ones a body part hangs off: "about my
# mums knee" is still an appointment, but "about him" is not.
PEOPLE_AFTER_A_GIVE_UP = frozenset((
    "she", "he", "her", "him", "his", "hers", "them", "their", "us", "me", "mum", "mum's",
    "mums", "mom", "mom's", "moms", "dad", "dad's", "dads", "nan", "nan's", "nans", "gran",
    "gran's", "grans", "mother", "father", "parents", "son", "daughter", "husband", "wife",
    "sister", "brother", "child", "baby", "friend", "partner"))


def _the_give_up_is_about_somebody(tight, words, third_person_only=False):
    """True when the doctor's giving up is about somebody, else False.

    "The doctor said theres nothing more they can do" is the sentence this whole cluster is about.
    "The doctor said theres nothing more they can do about my knee" is an orthopaedic
    appointment, and the same words sit in front of a back, a hip, a shoulder and a pain. Nothing
    before the verb separates them, so what the giving up names decides it:

    - no object at all ("nothing more they can do") is the whole of somebody's care;
    - an object that is a person ("for my mum", "about him") or their illness ("about the
      cancer", "for the tumour") is the same news;
    - an object that is a body part or a thing ("about my knee", "about the pain") is not, and the
      line goes back to the ordinary answers, each of which has one.

    Only the text after the verb is read, so the specialist in front of it ("the doctor said",
    "the consultant said") cannot stand in for the person the giving up is about.

    `third_person_only` is for the reading that has no care word at all to carry it (see
    `_the_give_up_without_a_care_word`): there, "nothing more they can do for me" is the speaker
    talking about themselves, which the care words already cover, and only somebody else counts.
    """
    named = THE_GIVE_UP_NAMES.search(tight)
    if not named:
        return not third_person_only
    subject = named.group(1)
    if SERIOUS_CARE.search(subject):
        return True
    # The last word is the thing the giving up is really about: "my mums knee" hangs the body part
    # off a person, and the appointment is the knee's.
    named_words = words_of(subject)
    if not named_words:
        return not third_person_only
    last = named_words[-1]
    if third_person_only and last in ("me", "us", "i", "mine", "ours"):
        return False
    return last in PEOPLE_AFTER_A_GIVE_UP or _has_person([last])


# Who is left when a give-up has no care word in it: "they said there is nothing more they can do
# for her". The attribution plus a person is what makes it the news, and an institution saying the
# same about a pupil, a tenant or an account is not (each of those has its own answer).
SAID_IT = re.compile(r"\b(?:said|says|say|told|tells|telling)\b")
NOT_A_CARE_GIVER = re.compile(
    r"\b(?:schools?|council|boss|manager|bank|landlord|letting\s+agent|employer|work|hr|"
    r"university|college|nursery|garage|mechanic|dealer|insurers?|insurance|dwp|benefits|"
    r"union|lawyers?|solicitors?|social\s+services|court|police|jobcentre|agent|unions?|"
    r"customers?\s+service|the\s+office)\b")


def _the_give_up_without_a_care_word(tight, who):
    """True for the give-up that names a person but no doctor, else False.

    "they said there is nothing more they can do for her" has the shape and the person but none of
    the words `CARE_WHO` wants, so it stayed small talk while the same sentence with "the doctor"
    in front of it was read. Somebody said it, and it is about a third person: that is the news.
    "My boss said theres nothing more he can do for me" is the speaker's own job, which the care
    words cover when it is care at all, and an institution saying it about a pupil or a tenant is
    an institution's answer, so neither is here.
    """
    if who or not NOTHING_MORE_TO_DO.search(tight) or not SAID_IT.search(tight):
        return False
    if NOT_A_CARE_GIVER.search(tight):
        return False
    return _the_give_up_is_about_somebody(tight, None, third_person_only=True)


# Main already had a pool for the days before a death (`SOMEONE_DYING`, from the pet work).
# Its lines say what to do; these two ask the question back, because the person with a dying
# parent is usually alone in it and the question is what keeps them talking.
DYING_REPLIES = SOMEONE_DYING + (
    "I'm sorry. That's a hard thing to be living with - is there help coming in, or is most of it "
    "on you?",
    "I'm sorry. It is happening now rather than after, and that is the part nobody prepares you "
    "for. Who is looking after you while you look after them?",
)

# A put-down the person says they regret. The feeling first, and then the one next step, because
# after a pet is put down the cremation, the ashes and the paw print are still theirs to arrange
# and nobody tells you that. Not a card of options on its own: they did not ask about the body.
PUT_DOWN_REGRET_REPLIES = (
    "I'm so sorry. Wanting it back is not the same as having done it wrong, and it is the last "
    "call anyone wants to make. When you feel up to it the vet can arrange the cremation or a "
    "home burial, and you can ask them for a paw print.",
    "I'm sorry. That is the heaviest kind of decision to be carrying. You do not have to sort "
    "anything today; when you are ready the vet will handle the cremation, and they can take a "
    "paw print for you.",
    "I'm really sorry. Regret is what love looks like afterwards, and it does not mean you got "
    "it wrong. The practical bit can wait a day or two - the vet arranges the cremation, and ask "
    "them about a paw print if you would want one.",
)

# "my mum died in march" was answered "It's a hard thing to carry - I'm here if you want to talk
# about them". The pools are written with "them" because they are also the reply for a line that
# names nobody ("my best friend died"), and a condolence is the one place where the wrong word is
# heard: someone who has just said "my wife died" hears "them" as more than one person, and this
# is the first thing the bot says to them. The two lines that carried "them" talk about it
# instead, which is the death and never the wrong number of people. Putting "her" and "him" back
# from the relation in the line would be warmer still, and it cannot be done inside the pools: a
# pool is also how the thread is followed (`continues`, `_thread_pool`), so a reply that is not in
# its pool any more ends the bereavement it was answering.
LOSS_REPLIES = (
    "I'm so sorry to hear that. It's a hard thing to carry — I'm here if you want to talk "
    "about it, or if anything practical would help.",
    "I'm really sorry. Be gentle with yourself today, and tell me if there's anything you "
    "want to talk through.",
    "That's such sad news, I'm sorry. Some days will be heavier than others — I'm here if you "
    "want to talk about it, or about anything else.",
    "I'm sorry, that's a real loss. Take today slowly, and shout if there's anything I can "
    "help you sort out.",
)

# What to say to someone who is dying is its own question, and the pool for someone who has lost
# them ("say you're sorry ... offer something practical") is an answer about the wrong person.
DYING_SAY_REPLIES = (
    "Say the plain things while they can hear them: that you love them, one memory you both "
    "laugh at, and that you will be all right. Nothing clever is needed.",
    "Skip the big speech and tell them one specific thing you are grateful for. It is easier to "
    "say than \"I love you\" out loud, and it is what people remember being told.",
    "Ask them what they want to talk about, and follow that. If they want the ordinary stuff - "
    "the garden, the football - that is not avoiding it, that is the visit.",
    "Bring them something to decide or to hear: how the family is, what the doctor said, the "
    "small gossip. Being useful is how most people say it.",
)

# Dying is grief that starts early, and it is a different grief from the one after: "is it normal
# to be like this already" needs the normalising answer, not a condolence.
DYING_GRIEF_REPLIES = (
    "Grieving someone who is still here is normal, and it is not a rehearsal for the real thing: "
    "it is the real thing, starting early. It comes in waves in the same way.",
    "That heaviness before the death is common - it is called anticipatory grief, and it does not "
    "make the later grief smaller or bigger, it is just its own thing. Talk to someone about it.",
    "It is normal to be tired, snappy and forgetful while someone is dying, and it is not a "
    "failing. If it is stopping you sleeping or eating for more than a fortnight, tell your GP.",
    "You can be grieving and relieved and guilty in the same hour, and none of that makes you "
    "bad. Most people who are where you are say the same.",
)

# How a person gets through the days is its own question, and it is the one that follows a
# death or a death coming. It names nothing of its own ("i dont know how to get through it"), so
# nothing read it: after a death the chat closed and the person got the search hedge, and when
# the one who had died was a pet the answer was the entry for a dog that is flat after a walk.
GETTING_THROUGH_REPLIES = (
    "One piece at a time is the only way anyone does it. Pick the next thing - a shower, a "
    "sandwich, one phone call - and let the rest wait until that is done.",
    "Keep the shape of the day: up at the usual time, food at the usual times, bed at night. "
    "The routine carries you on the days you cannot carry yourself.",
    "Tell one person how you are actually doing today and let them do one job for you. Most "
    "people want to help and do not know how to ask.",
    "The first days are the hardest and they are not a forecast of the rest. If you cannot eat "
    "or sleep, or you cannot see a way forward, tell your GP - they can help with that.",
)

# The same question while the death is still ahead: the days are the nursing as well as the
# grief, so the answer is about rationing what is asked of you.
GETTING_THROUGH_DYING_REPLIES = (
    "An hour at a time, and the ordinary things - food, a shower, going to work - are not a "
    "break from it, they are how you keep going.",
    "Take one day's jobs and no more, tell people what is happening so it is not all on you, "
    "and let the visits that do not matter drop.",
    "You do not have to be all right while this is going on. If you cannot sleep or eat, or you "
    "are carrying it with nobody to say it to, tell your GP.",
)

REMEMBER_REPLIES = (
    "Do it smaller rather than skip it: the same lunch or the same cake, with one or two people, "
    "and say out loud why you are having it. A day you have planned for is easier than one that "
    "just arrives.",
    "Keep the ritual and shrink it: the food they loved, their place at the table, and one story "
    "about them told to whoever is there. Doing something is what marks the day.",
    "Pick one thing to do at the time you would normally have spent together - the lunch, a walk, "
    "a visit - and tell someone you are doing it, so you are not carrying it on your own.",
    "Cook their dish or get their favourite in, and raise a glass to them: the point is to mark "
    "the day on purpose instead of letting it hit you sideways.",
    "Make the day about them: the meal they would have chosen, the people they liked, and the one "
    "thing you would have told them. If it all feels too heavy, do a small version and stop "
    "there.",
)

MISLAID_REPLIES = (
    "Tell a member of staff straight away — shops can call it out over the tannoy and watch the "
    "doors, which beats searching on your own.",
    "Go back to the last place you saw them and tell the nearest member of staff what they're "
    "wearing, so everyone is looking for the same person.",
    "Ask staff to put a call out and cover the exits. If it's a child, or someone vulnerable, "
    "ring 999 once it's more than a few minutes.",
)

SAY_REPLIES = (
    "Keep it plain and warm: \"I'm so sorry\". Use the person's name, don't rush to fill the "
    "silence, and offer one concrete thing — a lift, a meal, covering a shift.",
    "You don't need the perfect words. \"I'm so sorry\" and then listening is most of it; add "
    "one specific offer of help this week.",
    "Say you're sorry, name them if you can, and offer something practical. \"I'll bring "
    "dinner on Thursday\" helps far more than \"let me know if you need anything\".",
)

# The what-to-say pool for a loss the line names ("a friend whose mum died") - the two lines of
# SAY_REPLIES that name the person, without the one that does not.
NAMED_LOSS_SAY_REPLIES = (SAY_REPLIES[0], SAY_REPLIES[2])

CARD_REPLIES = (
    "Keep it short and warm: \"I'm so sorry for your loss. Thinking of you and your family.\" "
    "If you knew them, add one small memory — that is the part people keep.",
    "Two or three lines is plenty: name the person, say you are sorry, and add a practical "
    "offer — a meal, a lift, a hand with the children.",
)

GRIEF_REPLIES = (
    "That is normal after a loss, and it eases slowly for most people. If it is still this "
    "heavy, your GP is the right person to talk to.",
    "Most people find the same, and it does get easier. Be gentle with yourself — and see your "
    "GP if it has not lifted.",
    "That is part of grief for most people. If it stays like this, tell your GP; there is real "
    "help for it.",
)

# "does it get easier", "is this normal": a question about the grief itself. Answered in words
# that fit any death, it is a condolence card to nobody in particular, and the person who has just
# lost {animal} is asking about that animal. So a pet's death gets the same answer with the animal
# in it. The GP line stays: it is the person's own grief being asked about, and a vet cannot help
# with that.
PET_GRIEF_REPLIES = (
    "It does get easier, and slowly. Losing a {animal} takes something out of every day, so the "
    "quiet is loudest in the first weeks; if it is still this heavy after a month, your GP is the "
    "right person to talk to.",
    "It's real grief, and it eases the same way a person's does - slowly. Losing {article} "
    "{animal} leaves a gap in the day, so be gentle with yourself, and see your GP if it has not "
    "lifted in a few weeks.",
    "Most people find it eases, and no timetable is right. If it stays this heavy, tell your GP: "
    "grief for {article} {animal} counts, and there is real help for it.",
)

FUNERAL_REPLIES = (
    "Go if you can, even just for the service: turning up matters far more than anything you "
    "say. Take a card, say the plain thing, and leave when you need to.",
    "If you can make it, go — families remember who came. You don't have to speak; sitting "
    "with them is the thing.",
)

# What the arrangements cost, asked on its own, is a question for the knowledge base: it has the
# figures ("about GBP 4,000 to 5,000 all in"), and a line that names a price is answered there.
# This file does not keep a second copy of those numbers to drift from the entry's. What it does
# answer is the two shapes the entry does not: the two arrangements weighed against each other
# (below), and who helps pay the bill (further down) - both of which reached this file as a
# condolence or as "go if you can, turning up matters", which is advice for a guest given to
# somebody asking about a bill.

# The same question asked as a comparison - "is cremation cheaper than burial", "cremation or
# burial, which is cheaper" - which has an answer of its own: which of the two costs less, and
# what the difference is made of.
FUNERAL_COST_COMPARE_REPLIES = (
    "Cremation usually comes out cheaper than burial: the plot, the grave being dug and often a "
    "headstone are what the difference is made of. Ask two funeral directors for a written, "
    "itemised quote and compare the coffin, the cars and the cremation fee as separate lines.",
    "Cremation, yes - a burial adds the plot, the digging and usually a headstone, and that is "
    "where the difference is. The rest of the bill is much the same either way, so ask for the "
    "itemised quote and look at the coffin first.",
    "A cremation with no service is the cheapest of the lot, and a burial is the dearest: the "
    "plot and the headstone are the difference. Prices move a lot by area, so get two itemised "
    "quotes in writing before you decide.",
)

# The parts of the day other answers cover: what the flowers cost is a florist's question, and a
# card about the bill for a funeral is not the answer to it.
FUNERAL_COST_ELSE = re.compile(
    r"\b(?:flowers?|wreath|bouquet|music|songs?|hymns?|buffet|sandwiches|catering|drinks?|"
    r"order of service|programme|cards|outfit|clothes|suit|dress|shoes|tie|travel|fare|fares|"
    r"flights?|petrol|coach|taxi)\b"
    # "i cant afford to go to the funeral" is the journey, not the bill for the funeral, and the
    # funeral expenses payment is not the answer to it.
    r"|\b(?:go|get|going|getting) to (?:the|his|her|their) funeral\b")

# A part of the day, asked about: the music, the reading, the flowers, how long the service
# runs, and whether the children come. These have their own knowledge rows, and "If you can make
# it, go" answers none of them - it answers whether to be there at all, which is the one thing
# the person asking a part of the day has already decided. The part has to be *asked about*:
# "her favourite song was played" and "my kids were at the wake" only mention it.
_A_DAY_PART = (r"(?:music|songs?|hymns?|tunes?|readings?|reads?|recit(?:e|ed|ing)|poems?|"
               r"psalms?|flowers?|wreaths?|"
               r"bouquets?|order of service|kids?|children|child|baby|toddler|grandchildren|"
               r"grandkids)")
A_PART_OF_THE_DAY = re.compile(
    r"\b(?:what|which|any)\b(?:\W+\w+){0,5}\W+" + _A_DAY_PART + r"\b"
    r"|\b(?:should|shall|can|could|do)\s+(?:i|we|you)\b(?:\W+\w+){0,6}\W+" + _A_DAY_PART
    + r"\b"
    r"|\b(?:should|shall|can|could|do|does)\s+(?:(?:i|we|you|a|the|any|my|our)\s+)?"
    r"(?:kids?|children|child|baby|toddler|grandchildren|grandkids)\b"
    r"|\b(?:good|nice|right|best|suitable)\s+(?:songs?|hymns?|tunes?|music|readings?|poems?|"
    r"psalms?)\b"
    r"|\b(?:should|shall|can|could)\s+(?:my|our)\b(?:\W+\w+){0,4}\W+" + _A_DAY_PART + r"\b"
    r"|\bhow\s+long\s+(?:is|does|do|are|will|would)\b(?:\W+\w+){0,4}\W+(?:funeral|service|"
    r"cremation|burial|wake|memorial)\b"
    r"|\bhow\s+long\s+(?!until|till|to|before)\w*(?:\W+\w+){0,6}\W+\bfuneral\b"
    r"|\bhow\s+many\s+(?:days|weeks)\b(?:\W+\w+){0,6}\W+\bfuneral\b"
    r"|\bhow\s+soon\b(?:\W+\w+){0,4}\W+\bfuneral\b"
    r"|\bis\s+it\s+(?:ok|okay|fine|alright)\b(?:\W+\w+){0,6}\W+" + _A_DAY_PART + r"\b",
    re.I)
# A line asking what to say stays here whatever else it names: "what do i say at mums funeral"
# is the words, not the music or the flowers.
SAY_THE_WORDS = re.compile(
    r"\b(?:what to say|what do i say|what can i say|what should i say|what shall i say|"
    r"say at|say to|words for|eulogy|eulogies|speech)\b", re.I)

# A death in the line means the person is bereaved, and the sympathy - or the practical card an
# answer module has - is the reply. This reading is for the price on its own.
_DEATH_IN_LINE = re.compile(
    r"\b(?:died|dies|dying|dead|death|passed away|passed on|passed|killed|cremated|"
    r"buried|widow|widower)\b")

# The arrangements, and the words for money. "Service", "wake", "plot" and "grave" are left
# out on their own: they are ordinary words (a customer service, a plot of land, a grave mistake),
# and a price beside one of them is not a question about a funeral. A coffin or a headstone is a
# price of its own and keeps the honest "I can't look up live prices" it had.
_FUNERAL_NOUN = r"(?:funerals?|cremations?|cremation|crematoriums?|cremate|burials?|bury|buried|"
_FUNERAL_NOUN += r"undertakers?|funeral directors?)"
_COST_NOUN = r"(?:cost|costs|costing|price|prices|priced|expensive|cheaper|cheapest|cheap|"
_COST_NOUN += r"afford|affordable|pay|paid|paying|fee|fees|money|budget|quote|quotes|"
_COST_NOUN += r"how much)"
FUNERAL_COST = re.compile(
    r"\b" + _FUNERAL_NOUN + r"\b[^.?!]{0,30}?\b" + _COST_NOUN + r"\b"
    r"|\b" + _COST_NOUN + r"\b[^.?!]{0,30}?\b" + _FUNERAL_NOUN + r"\b")

# The other half of a funeral bill: not what it costs, but who helps pay it. The DWP payment is
# the one that exists, and the council has its own fund, so a line asking about help is answered
# with both rather than with where the money goes.
# The money the person left pays for their own funeral before anything is shared out, and that is
# a different answer from the benefits one: "does the estate pay for the funeral" got "apply for
# the funeral expenses payment from the DWP", which is help for somebody with no money, not where
# the bill goes when there is some. The estate rows answer it, so this pool stands aside.
_THE_ESTATE = re.compile(r"\b(?:estate|probate|inheritance|the will)\b")
FUNERAL_HELP = re.compile(
    r"\b" + _FUNERAL_NOUN + r"\b[^.?!]{0,30}?\b(?:help|afford|claim|payment|pay for|council|"
    r"benefits?|dwp|social fund|charity|charities)\b"
    r"|\b(?:help|afford|claim|payment|pay for|council|benefits?|dwp|social fund|charity|"
    r"charities)\b[^.?!]{0,30}?\b" + _FUNERAL_NOUN + r"\b")
# A question about help can come with no question shape at all ("i cant afford a funeral"), so
# the words for a bill they cannot meet are read as the ask on their own.
HELP_ASK = re.compile(r"\b(?:help|claim|claiming)\b|can'?t afford|cannot afford|cant pay|"
                      r"can'?t pay|no money|nothing to pay")
FUNERAL_HELP_REPLIES = (
    "There is help with it: the DWP funeral expenses payment covers part of the bill if you are "
    "on certain benefits, and you claim it after the funeral, within six months. Keep every "
    "receipt, and ring the council as well - they have a fund of their own for people who cannot "
    "pay.",
    "Claim the DWP funeral expenses payment within six months of the funeral: it covers the "
    "cremation or burial fees and some of the rest, and it goes to whoever arranged it. If you "
    "are on a low income, ask the council too - they pay for a funeral when there is no money at "
    "all.",
    "You can apply for the funeral expenses payment from the DWP after the funeral - within six "
    "months, and only on certain benefits - so tell the funeral director to invoice you and keep "
    "the receipts. The council's bereavement service has a separate fund, and Citizens Advice "
    "will help you fill the forms in.",
)
# A comparison is a question even when nothing at the front says so. A bare "cost" is not: "the
# funeral cost a fortune" is somebody telling you what they paid, and the sympathy is the reply.
QUIETER_ASK = re.compile(r"\b(?:which|cheaper|cheapest|how much|prices?)\b")
# The two arrangements weighed against each other, which is a question of its own.
FUNERAL_COST_COMPARE = re.compile(
    r"\b(?:cheaper|cheapest|more expensive|less expensive|costs? more|costs? less|vs|versus|"
    r"instead of|or a burial|or burial|or cremation|or a cremation|worth it)\b")
# A comparison names both of them: "is cremation cheaper than burial". A superlative about the
# funeral as a whole - "whats the cheapest funeral i can get" - is a price question, and the
# knowledge entry has the figure for it, so this reading stands aside and lets the entry answer.
_BURIAL_SIDE = re.compile(r"\b(?:burials?|bury|buried|burying|graves?|plots?|headstones?|coffins?)\b")
_CREMATION_SIDE = re.compile(r"\b(?:cremations?|cremate|cremated|crematoriums?|ashes|urns?)\b")


# The follow-up that names the arrangements only as "it": "and can i get help paying for it",
# "how do i pay for it". No word in the line says funeral, so no reading of a word can find it.
# What makes it the arrangements is the answer the bot gave last turn, which was about the bill.
_PRONOUN_MONEY_ASK = re.compile(
    r"\b(?:help|pay|paying|paid|afford|claim|claiming|cost|costs|costing|money|cheaper|"
    r"how much)\b[^.?!]{0,24}?\b(?:it|that|this|them)\b"
    r"|\b(?:it|that|this|them)\b[^.?!]{0,24}?\b(?:cost|costs|pay|paid|afford|expenses?|"
    r"expensive|cheap)\b")
# What the answer above has to be about: the arrangements, and the money for them.
_BILL_SUBJECT = re.compile(
    r"\b(?:funerals?|cremations?|cremation|crematoriums?|burials?|bury|buried|coffins?|"
    r"undertakers?|funeral directors?)\b")
_BILL_MONEY = re.compile(
    r"\b(?:cost|costs|price|prices|quote|quotes|pay|paid|paying|fee|fees|afford|bill|"
    r"dwp|benefit|benefits|cheapest|cheaper)\b|\u00a3|\bthousands?\b")

# A safety answer is never read back as the subject of a pronoun: "can i help with it" after a
# crisis line is the crisis, and it is not a bill.
_NOT_A_BILL_THREAD = frozenset(("safety", "urgent"))


def _the_bill_was_the_last_turn(memory):
    """True when the last answer was about the arrangements and what they cost."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    last = turns[-1]
    if last.get("module") in _NOT_A_BILL_THREAD:
        return False
    said = str(last.get("bot") or "").lower()
    return bool(_BILL_SUBJECT.search(said) and _BILL_MONEY.search(said))

# How many turns a death stays the thread, which is the same window the grief module keeps it
# for. The two numbers are read separately so that this file's reading of a price never has to
# import a module that imports it; if they drift, the line falls back to this file's ordinary
# pools, which is what it had before this reading existed.
LOSS_STILL_THE_THREAD = 3


def _loss_is_the_thread(memory):
    """True when a death has been talked about in the last few turns of this conversation."""
    record = (memory or {}).get("loss")
    if not isinstance(record, dict):
        return False
    turns = (memory or {}).get("turns") or ()
    return len(turns) - int(record.get("turn") or 0) <= LOSS_STILL_THE_THREAD


def arrangement_cost_pool(line, tight=None, memory=None):
    """The cost of the arrangements, asked on its own: the pool to answer with, or None.

    Read before `is_practical_ask`, which stands the composer aside for every other practical
    question inside a bereavement: a price question with no death in it is not one of those, and
    the modules it was standing aside for had nothing about a funeral to say. A comparison of the
    two ("is cremation cheaper than burial") has its own pool, because the answer is which of them
    costs less rather than where the money goes.
    """
    tight = _tight(line) if tight is None else tight
    if FUNERAL_COST_ELSE.search(tight) or _DEATH_IN_LINE.search(tight):
        return None
    if _PRONOUN_MONEY_ASK.search(tight) and _the_bill_was_the_last_turn(memory):
        # "and can i get help paying for it" after an answer about the bill: the "it" is the
        # arrangements, and the help with them is what is being asked for. This is read before
        # the death-thread stand-aside below, because the grief module leaves the practical
        # follow-up to the composer and the search shrug is what answered it.
        if FUNERAL_COST_COMPARE.search(tight) and not HELP_ASK.search(tight):
            return FUNERAL_COST_COMPARE_REPLIES
        return FUNERAL_HELP_REPLIES
    if _loss_is_the_thread(memory):
        # A death is already in this conversation and the grief module is still on it, so the
        # price question is answered there, in a reply written for someone who has just been
        # bereaved. This reading is for the price asked cold, by somebody who has said nothing
        # about a death at all.
        return None
    if not (FUNERAL_COST.search(tight) or FUNERAL_HELP.search(tight)):
        return None
    # "cremation or burial, which is cheaper" is a question without a question mark or a question
    # word at the front, so the comparison itself is read as the ask. A remark about what was
    # already paid - "the funeral cost a fortune", "the council paid for it" - is not a question
    # and gets whatever the pools above have.
    if not (asks_anything(line, tight) or QUIETER_ASK.search(tight)
            or FUNERAL_COST_COMPARE.search(tight) or HELP_ASK.search(tight)):
        return None
    if FUNERAL_HELP.search(tight) and not _THE_ESTATE.search(tight):
        # "does the council pay for funerals", "how do i claim the funeral expenses payment",
        # "i cant afford a funeral": the money is the question, and where it goes is not the
        # answer to it.
        return FUNERAL_HELP_REPLIES
    if (FUNERAL_COST_COMPARE.search(tight) and _BURIAL_SIDE.search(tight)
            and _CREMATION_SIDE.search(tight)):
        return FUNERAL_COST_COMPARE_REPLIES
    # A plain "how much does a funeral cost" is left to the knowledge entry that carries the
    # figures; nothing here answers it, so the line falls through to whatever it had.
    return None

# A reply that already says the sad thing itself: the pets entry ("I'm sorry, that's one of the
# hardest days") answers a pet's death with more than sympathy, so a module that only comforts
# lets it keep the turn.
# The sorry has to be about a death: "I'm sorry — that's frustrating" is an apology for a
# broken laptop, and a fallback line is never the answer to a bereavement.
ACKNOWLEDGE = re.compile(
    r"\b(?:sorry (?:to hear|for your loss)|such sad news|condolences|my sympathy|sympathies|"
    r"real loss|hard(?:est)? days?|nothing prepares you)\b")


# The words people use about their own state in the first weeks: "i keep crying", "i feel guilty",
# "i miss him", "i cant stop thinking about it". A line like that is about the person's feelings,
# so it asks for company, not for the practical card a topic entry would give them.
OWN_STATE = re.compile(
    r"\b(?:i|i'm|im|i've|ive|me|my|we|we're|were|us)\b[^.]*\b(?:cry|crying|cried|tears|"
    r"guilty|guilt|miss|missing|struggling|broken|heartbroken|devastated|numb|angry|lonely|"
    r"sad|empty|numb|cant stop|can't stop|cannot stop|keep thinking|nightmares?|feel awful|"
    r"feel terrible|feel lost|feel sick)\b")


# The pet has to be the person's own: "my dog", "our old cat", but not "my mates dog" (their
# friend's loss, which asks for what to say to them) and not "her cat".
OWN_PET = re.compile(r"\b(?:my|our)\s+(?:(?:old|poor|little|beloved|lovely|sweet|baby|family|"
                     r"best)\s+)?(?:" + "|".join(sorted(PET_WORDS)) + r")\b")

# Where one clause stops and the next starts: the death has to be the pet's, and a pet named in
# the next clause ("her dog needs a home") is not the one that died.
CLAUSE = re.compile(r"[;,]|\b(?:and|but|then|so|because|although|though|while|after|before|"
                    r"which|who)\b")


# ... except when the person says they regret it: "i regret putting my dog down" is the same
# death as "i had to put my dog down", said in a frame that can only be about the past. The plan
# reading in `NOT_YET` takes any "putting X down", and a regret is never about a day still ahead.
PUTTING_REGRETTED = re.compile(
    r"\b(?:regrets?|regretted|regretting|wish)\b[^.?!]{0,24}?"
    r"\bputting\s+(?:\w+\s+){0,3}?(?:to sleep|down)\b")

# A pet still to be put down has not died: "my dog is being put to sleep tomorrow" is a hard
# appointment, and the cremation card answers a death that has not happened. The plan is read
# from the verb shape and never from a time word, because people say the day too: "our cat was
# put to sleep on friday" is a death, and the past forms ("we had to put our cat down yesterday",
# "was put down last tuesday") have to keep counting.
NOT_YET = re.compile(
    # "was being put to sleep yesterday" is a death that has already happened, so it is the
    # pets entry's line; only the present "is being put" is a plan (fancy-penguin, #1712).
    r"\b(?:is|are|am)\s+being\s+(?:put|euthanis\w*)"
    r"|\b(?:will|would|going to|about to|has to|have to|needs? to|got to|due to)\s+"
    r"(?:be\s+)?(?:put|euthanis\w*)"
    r"|\b(?:have|has|need|needs|got)\s+to\s+(?:put|be put)\b"
    # "i have to have my dog put to sleep next week": the plan is in the outer "have to", and the
    # putting is the vet's, so the pet is named between them.
    r"|\b(?:have|has|need|needs|got)\s+to\s+have\s+(?:\w+\s+){0,3}?(?:put|euthanis\w*)"
    r"|\bputting\s+(?:\w+\s+){0,3}?(?:to sleep|down)\b"
    # a pet that is dying, or that the vet says will not last, is not dead yet either
    r"|\b(?:is|are|am|was|were)\s+dying\b"
    # "my mums dying", "my dads dying": the possessive swallows the "is", and people type it that
    # way more often than not.
    r"|\b(?:mum|mom|mam|dad|father|mother|nan|nana|gran|granny|grandad|grandma|brother|sister|"
    r"wife|husband|partner|friend|son|daughter)s\s+dying\b"
    r"|\b(?:isn'?t|isnt|not|never|won'?t|wont|is not)\s+going\s+to\s+(?:make\s+it|last)\b"
    # The vet's estimate is a death still ahead: "the vet says my cat has a few weeks left", "they
    # gave him two months". Said about the end of a job or a term it is not, so the line has to
    # name the animal or the person for this to be read, and that is the caller's check.
    r"|\b(?:has|had|have|say|says|said|told)\s+(?:\w+\s+){0,4}?"
    r"(?:a\s+few|a\s+couple\s+of|another|one|two|three|four|five|six|a\s+matter\s+of)\s+"
    r"(?:days?|weeks?|months?)\s+(?:left|to\s+go|or\s+so)\b"
    # "they gave my dad two months" needs no "left" after it: the giving is the estimate, and
    # "i have two weeks holiday" is not, so only the giving verbs carry the short form.
    r"|\b(?:gave|given|gives)\s+(?:\w+\s+){0,4}?"
    r"(?:a\s+few|a\s+couple\s+of|another|one|two|three|four|five|six|a\s+matter\s+of)\s+"
    r"(?:days?|weeks?|months?)\b"
    r"|\b(?:days?|weeks?|months?)\s+(?:left|to\s+go)\b"
    r"(?!\s+(?:of|in|on|until|till|before|for))")
# The vet's or the doctor's estimate alone: "the vet says my cat has a few weeks left", "they
# gave my dad two months". `NOT_YET` also holds the plain present "is dying", and a line that
# says that is answered by DYING_REPLIES - the wording for someone still in the room - so the
# estimate needs its own pattern and must not stand in front of that branch (fast-shelf, #3379).
ESTIMATE = re.compile(
    r"\b(?:has|had|have|say|says|said|told)\s+(?:\w+\s+){0,4}?"
    r"(?:a\s+few|a\s+couple\s+of|another|one|two|three|four|five|six|a\s+matter\s+of)\s+"
    r"(?:days?|weeks?|months?)\s+(?:left|to\s+go|or\s+so)\b"
    r"|\b(?:gave|given|gives)\s+(?:\w+\s+){0,4}?"
    r"(?:a\s+few|a\s+couple\s+of|another|one|two|three|four|five|six|a\s+matter\s+of)\s+"
    r"(?:days?|weeks?|months?)\b")
# The treatment has run out, which is how most people say somebody is dying now: "the doctor said
# theres nothing more they can do", "theyve stopped mums chemo", "the consultant said its a matter
# of time". Not one of those lines has "dying", "terminal" or "hospice" in it, so the reader below
# answered all of them as small talk - the shrug ("I'm listening - say more if it helps"), "Noted:
# your dad has weeks left", and a GP appointment for a mother the hospital had already given up on.
NOTHING_MORE_TO_DO = re.compile(
    r"\b(?:nothing|not\s+much|not\s+anything)\s+(?:more|else|further|left)\b"
    r"[^.!?]{0,40}?\b(?:do|done|try|trying|offer|suggest)\b")
TREATMENT_STOPPED = re.compile(
    r"\b(?:stopped|stopping|stop|cease[ds]?|halted|withdrawn\s+from|taken\s+off|came\s+off|"
    r"no\s+longer\s+(?:having|on))\s+(?:\w+\s+){0,3}?"
    r"(?:treatment|chemo|chemotherapy|radiotherapy|dialysis)\b"
    r"|\bno\s+(?:more|further)\s+(?:treatment|chemo|chemotherapy|radiotherapy|options)\b"
    # The same thing said the other way round: "mums chemo has been stopped". Only a doctors'
    # word makes the stopped thing a treatment worth reading - "my medication has been stopped"
    # is a chemist's line and stays out, because nothing in it is on the CARE_WHO list below.
    r"|\b(?:treatment|chemo|chemotherapy|radiotherapy|dialysis)\s+"
    r"(?:has|have|had|is|are|was|were)\s+(?:been\s+)?(?:stopped|halted|withdrawn)\b")
# The pills are only the same news next to the illness: "the doctor said to stop my medication" is
# as often a statin stopped as it is the last of the care, so this one waits for a specialist or a
# condition, and "stop the medication" on its own waits for the chat to already be a loss.
MEDICATION_STOPPED = re.compile(
    r"\b(?:stopped|stopping|stop|cease[ds]?|halted|no\s+longer\s+(?:having|on)|taken\s+off)\s+"
    r"(?:\w+\s+){0,3}?(?:medication|meds|drugs|tablets|pills|painkillers)\b"
    r"|\b(?:medication|meds|drugs|tablets|pills|painkillers)\s+"
    r"(?:has|have|had|is|are|was|were)\s+(?:been\s+)?(?:stopped|halted|withdrawn)\b")
# The drug that is only given when the treatment has stopped being a cure: "they put my dad on
# morphine", "they started my mum on morphine", "hes on a syringe driver now". These are the
# words a family hears on the day the doctors stop trying, and none of them is a death word, so
# the reader answered "they put my dad on morphine" with the pleasantry for a small account of a
# day - "Nice one. How did the rest of it go?" - and "they started my mum on morphine" with
# "How was it, overall?". The drug list is the last-of-life ones only: a painkiller, a statin or
# an antibiotic is an ordinary prescription and stays out.
LAST_DRUG = (r"morphine|diamorphine|midazolam|fentanyl|oxycodone|alfentanil|levomepromazine|"
             r"syringe\s+driver|palliative\s+sedation|end\s+of\s+life\s+(?:meds|medication|drugs)")
ON_THE_LAST_DRUG = re.compile(
    # Somebody was put on it: "they put my dad on morphine", "started her on a syringe driver".
    r"\b(?:put|puts|putting|started|starting|starts?|switched|moved)\s+(?:\w+\s+){0,3}?"
    r"(?:on|onto)\s+(?:a\s+|the\s+|her\s+|his\s+|their\s+)?(?:" + LAST_DRUG + r")\b"
    # ...or they are on it now: "hes on morphine now", "my mum is on a syringe driver".
    r"|\b(?:he|she|they|mum|dad|nan|gran|grandad|grandma|grandpa|husband|wife|son|daughter|"
    r"mother|father|brother|sister|friend|mate)\b[^.!?,]{0,12}?\b(?:is|are|was|were)\s+"
    r"(?:now\s+)?(?:on|getting)\s+(?:a\s+|the\s+)?(?:" + LAST_DRUG + r")\b")
# The same drug for a pain of the person's own: "im on morphine for my back", "i was put on
# morphine after my op" is an operation, not a death, and it is the person speaking about
# themselves that says so.
SELF_ON_THE_DRUG = re.compile(
    r"\b(?:i|i'?m|im|i'?ve|i\s+have|i\s+was|i\s+got|i'?d|me|my\s+(?:back|knee|hip|leg|arm|"
    r"shoulder|teeth|tooth|wrist|ankle))\b[^.!?]{0,20}?\b(?:" + LAST_DRUG + r")\b")


def says_the_last_drug(tight):
    """True when the line says somebody has been started on the drug that ends the treatment.

    "they put my dad on morphine", "they started my mum on morphine", "she is on a syringe
    driver now": the cure has stopped, the comfort has started, and it is the sentence a family
    hears in the room. The person's own painkiller is not that news ("im on morphine for my
    back", "i was put on morphine after my op"), so the first person switches it off.
    """
    if not ON_THE_LAST_DRUG.search(tight):
        return False
    return not SELF_ON_THE_DRUG.search(tight)


# A give-up is somebody dying when a doctor, a vet or a hospital says it, and only then: "the
# council said theres nothing more they can do about the noise" is a housing answer, "the mechanic
# said theres nothing more he can do" is the car's, and the condolence for either is the wrong
# answer to a real ask. The condition and the treatment are what make the give-up a medical one.
CARE_WHO = re.compile(
    r"\b(?:doctors?|doctor'?s|gps?|consultants?|surgeons?|specialists?|oncologists?|oncology|"
    r"hospitals?|hospice|ward|icu|intensive\s+care|nurses?|palliative|vets?|clinic|"
    r"treatment|chemo|chemotherapy|radiotherapy|dialysis|cancer|tumours?|tumors?|leukaemia|"
    r"leukemia|dementia|motor\s+neurone|parkinsons?)\b")
# The days that are left: "my dad has weeks left", "she has days left", "my nan hasnt got long
# left", "a matter of time". Only the whole of what is left counts - "my son has two weeks left of
# school" and "i have two weeks left to finish my essay" are a term and a deadline, and both were
# read as a death on main.
DAYS_LEFT = re.compile(
    r"\b(?:days?|weeks?|months?)\s+left\b"
    r"(?!\s+(?:of|in|on|at|with|before|until|for)\b)(?!\s+to\b(?!\s+live\b))"
    r"|\b(?:days?|weeks?|months?)\s+to\s+live\b"
    r"|\b(?:not\s+)?long\s+(?:left|to\s+go)\b"
    r"|\b(?:a|only\s+a)\s+matter\s+of\s+(?:time|days|weeks|hours)\b")
NOT_THE_END = re.compile(
    r"\b(?:left|to\s+go)\s+(?:of|in|on|at|with|before|until|for)\b"
    r"|\b(?:left|to\s+go)\s+to\s+(?!live\b|be\b)")
# The same week said the other ways round: "shes in her final weeks", "weve been told it could be
# days", "my nan isnt going to get better". Each needs somebody for the days to belong to (see
# `_the_end_is_near`), because "a few days" and "final weeks" are a delivery and a season too.
FINAL_DAYS = re.compile(
    r"\b(?:her|his|their|my|our)\s+final\s+(?:days|weeks|months)\b"
    r"|\bfinal\s+(?:days|weeks|months)\s+of\s+(?:her|his|their|my|our)\s+life\b")
COULD_BE_DAYS = re.compile(
    r"\b(?:could|might|may|probably)\s+be\s+(?:a\s+)?(?:few\s+|couple\s+of\s+)?"
    r"(?:days|weeks|hours)\b")
# The same count of days spent waiting for something that is not a death: "it could be days
# before the parcel comes", "she said it could be days of rain", "they said it could be days for
# the results". "could be days" names nobody - the `it` is impersonal and the `she` or `he` beside
# it is the one who spoke - so what follows the count is what says whose days they are. The end
# itself is still a death: "it could be days before the end" keeps its answer.
DAYS_WAIT_FOR = re.compile(
    r"\b(?:days?|weeks?|hours?)\s+(?:for|until|till|til|before|by|of)\s+"
    r"(?!the\s+(?:end|worst)\b|his\s+end\b|her\s+end\b|she\s+goes\b|he\s+goes\b|"
    r"it\s+happens\b)")
# "my mum is in the last stages now": the same count with the stages named. Read only with
# somebody in the line (see `_the_end_is_near`), so "the last stages of the project" stays a plan.
LAST_STAGES = re.compile(
    r"\b(?:the\s+)?(?:last|final|end)\s+(?:days|weeks|stages?)\b"
    r"|\bin\s+(?:the\s+)?(?:final|end)\s+stages?\b"
    r"|\b(?:final\s+)?stages?\s+of\s+(?:her|his|their|my|our)\s+(?:cancer|illness|disease|life)\b")
NOT_GETTING_BETTER = re.compile(
    r"\b(?:isnt|isn'?t|wont|won'?t|never\s+going\s+to|not\s+going\s+to|will\s+not)\s+"
    r"(?:will\s+)?(?:going\s+to\s+)?get\s+(?:any\s+)?better\b"
    r"|\bno\s+longer\s+going\s+to\s+get\s+better\b")
# The specialists' version of the give-up, and the sentence a family hears from the doctor: "the
# specialists have given up on my son", "the doctor said to prepare ourselves", "theyve taken him
# off the ventilator". These carry a care word strong enough on its own only with somebody named,
# so a car and a leaking roof keep their own answers.
GIVEN_UP_ON = re.compile(r"\bgiven\s+up\s+on\b|\bhave\s+given\s+up\b|\bgive\s+up\s+on\b")
PREPARE = re.compile(
    r"\bprepare\s+(?:ourselves|yourself|yourselves|the\s+family|them)\b")
# What a family is preparing for that is not a death: a result, an exam, a scan, a move.
PREPARE_OTHERWISE = re.compile(
    r"\b(?:results?|exams?|tests?|interviews?|inspections?|audit|inspection|wedding|move|visit|"
    r"appointment|flight|holiday|winter|storm|review|scans?|x-?rays?)\b")
OFF_LIFE_SUPPORT = re.compile(
    r"\b(?:taken|taking|took|take|came|come|coming|coming\s+off)\s+(?:\w+\s+){0,2}?"
    r"off\s+(?:the\s+)?(?:ventilator|ventilation|life\s+support|breathing\s+machine)\b")
# ...and the same words on a good day: taken off the machine and breathing alone.
OFF_SUPPORT_WELL = re.compile(
    r"\b(?:on\s+(?:his|her|their)\s+own|breathing\s+(?:on|by)|himself|herself|awake|talking)\b")
# "weve been told it could be days": a family being told, which is the figure said out loud in a
# relatives' room. The plural is what makes it that - "i was told it could be days before the
# parcel comes" stays a delivery.
TOLD_US = re.compile(
    r"\b(?:we'?ve\s+been\s+told|we\s+were\s+told|they'?ve\s+told\s+us|they\s+told\s+us|"
    r"they\s+(?:have\s+)?said|doctors?\s+(?:have\s+)?said|consultants?\s+(?:have\s+)?said)"
    r"\b")
# The treatment that has stopped working is the treatment that has run out (the oncologist says
# it in the same breath). A cream or a diet that stops working is not, so this one needs a
# serious condition or a specialist who handles dying, never a plain GP or the word treatment on
# its own: "my acne treatment isnt working anymore" is a chemist's line.
NOT_WORKING = re.compile(
    r"\b(?:isnt|isn'?t|not|stopped|no\s+longer)\s+working\b"
    r"|\b(?:has|have|had)\s+stopped\s+working\b")
SERIOUS_CARE = re.compile(
    r"\b(?:oncologists?|oncology|consultants?|specialists?|palliative|hospices?|"
    r"cancer|tumours?|tumors?|leukaemia|leukemia|dementia|motor\s+neurone|parkinsons?|mnd|"
    r"end\s+of\s+life|morphine|syringe\s+driver|last\s+stages)\b")
# Hospice is the word for the last stop, but only when somebody is in its care: "my mum is in a
# hospice", "she was moved to the hospice", "hospice is being arranged for my wife", "hospice
# care". Naming one is not the same news - a sponsored walk, a cake sale, a bring-and-buy, a job
# and a volunteer shift all say the word too, and each has its own answer.
HOSPICE_CARE = re.compile(
    r"\bhospice\s+care\b"
    r"|\b(?:in|at)\s+(?:a\s+|the\s+|her\s+|his\s+|their\s+)?hospice\b"
    # Going there is a move, not a referral: "how do i get a referral to a hospice" is a question
    # about the letter, and it has its own answer.
    r"|\b(?:moved|moving|transferred|gone|went|going|admitted|taken|took)\b"
    r"(?:\s+\w+){0,3}?\s+(?:in)?to\s+(?:a\s+|the\s+|her\s+|his\s+|their\s+)?hospice\b"
    r"|\b(?:into|onto)\s+(?:a\s+|the\s+|her\s+|his\s+|their\s+)?hospice\b"
    r"|\bhospice\s+(?:is\s+being\s+arranged|has\s+been\s+arranged|at\s+home)\b")
# The words that make a hospice somewhere a person goes, works or raises money rather than the
# place somebody is dying in. "my mum volunteers at the hospice" and "the hospice is looking for
# volunteers" are about the building, not about her.
HOSPICE_JOB = re.compile(
    r"\b(?:jobs?|works?|worked|working|volunteers?|volunteering|nurse\s+there|manager|staff|"
    r"shifts?|sponsors?|sponsored|sponsoring|fundrais\w*|raise\s+(?:money|funds)|raising\s+money|"
    r"collecting|collection|donate|donating|donations?|cake\s+sale|charity|justgiving|marathon|"
    r"walk|run|cycle|ride|quiz|raffle|tombola|bring\s+and\s+buy|open\s+day)\b")
# "its palliative now" - the adjective on its own, which is the last-of-care sentence. A question
# about what palliative means is a knowledge ask and stays out.
PALLIATIVE_ITSELF = re.compile(r"\bpalliative\b")

# "dying" is the word of a death, and also the word of wanting something badly and of dyeing
# your hair: "my mum is dying for a coffee" and "my mums dying her hair" are not a death, and
# they must not be told what to say at a deathbed or sent a condolence.
DYING_OTHER = re.compile(
    r"\bdying\s+(?:for|to)\b"
    r"|\bdying\s+(?:my|her|his|their|our|your|the)\s+"
    r"(?:hair|beard|roots|eyebrows|eyebrow|nails|lashes)\b"
    r"|\bdying\s+it\b")

# "is it my fault", "was that the right thing to do": a question with no wh-word and no modal,
# so `asks_anything` misses it. Only the pets entry's reading wants this one: broadening the
# shared reading made "my mum died, the cost of it all" a practical ask, which stood the
# condolences down and left the composer hedging.
ASK_BARE = re.compile(r"\b(?:is|was|isn'?t|wasn'?t)\s+(?:it|that|this)\b")


def asks_about_the_remains(line, tight=None):
    """True when the pets entry is the answer to what the line asks.

    The entry knows one thing: what happens to the body, and that the vet can arrange it, so it
    keeps the turn only for a line that asks about the body - "can we bury him at home", "what do
    i do with his bed". A line that asks something else is a person the card has no answer for:
    "my dog died, when should i get another one" got the cremation paragraph, and "our hamster
    died, is it my fault" got a paw print. The condolence answers those.

    A line that asks nothing at all is not this reading's business either: `bot/modules/loss.py`
    asks `asks_for_a_decision` first, so a bare "my dog died" is met rather than carded, and this
    only decides which asks the card answers. It reads the ask itself (`ASK_BARE` is the shape
    with no wh-word and no modal, "is it my fault"), so it is not standing on that call.
    """
    line = str(line or "")
    tight = _tight(line) if tight is None else tight
    if not PET_ARRANGEMENT.search(tight):
        return False
    # The question can be in the second half of the line, so the household shapes and the
    # comma-then-question shape count beside the composer's own ask reading: "my dog died, can we
    # bury him at home" asks about the body, "my dog died last night" asks nothing.
    # `ASK_TAIL` reads the line as typed: `_tight` is for the word lists, and it drops the comma
    # that makes "my cat died, is cremation expensive" a question at all.
    return bool(asks_anything(line, tight) or ASK_WE.search(tight) or ASK_TAIL.search(line)
                or ASK_BARE.search(tight))


def a_pet_died(line):
    """True when the death in the line is a pet's, so the pets entry is the answer to it.

    "we had to put our cat down yesterday" and "my dog died last night" are that entry's lines.
    "my aunt died and her dog needs a home" is a person's death with a live dog in the next
    clause, and the cremation card is not the answer to that. Read clause by clause, and reuse
    this file's reading of a death so "dead birds" and "put my cat to sleep at night" stay out.

    A death still to come is not a death (`NOT_YET`): the dog is alive on the day before.
    """
    text = str(line or "").lower().replace("\u2019", "'")
    if NOT_YET.search(text) and not PUTTING_REGRETTED.search(text):
        return False
    for clause in CLAUSE.split(text):
        if not OWN_PET.search(clause):
            continue  # "my mates dog", "her cat": someone else's pet, so it is not their loss
        words = _plain(clause)
        if words and reads_as_loss(clause, words):
            return True
    return False


# A question about what to do now the pet has gone: "do we need to bury it deep", "what do i do
# with her bed", "how do i cancel her insurance", "should we get another". The act is in the
# line, so the entry that knows how it is done answers it better than a sympathy does. A bare
# question mark is not an act: "my dog died?" and "will it stop hurting?" ask about the loss, and
# a sympathy is the right answer to both, so the ask word has to be doing work (`what do`, `how
# do i`, `should we`) rather than just ending the line.
PRACTICAL_ASK = re.compile(
    r"\b(?:what|who|where|when|how)\s+(?:do|does|should|shall|can|could|now|next)\b"
    r"|\b(?:do|should|shall|can|could|need)\s+(?:we|i)\s+\w+"
    # a price is a decision about the body, and it is asked without an act word: "my cat died,
    # is cremation expensive" wants the entry that knows what happens to a pet's body, not the
    # funeral answer for a person ("say what you actually want before they price it").
    r"|\b(?:is|was|isn'?t|wasn'?t)\s+(?:\w+\s+){0,3}(?:expensive|costly|cheap)\b"
    r"|\bhow\s+(?:much|expensive)\b")


# A death leaves paperwork and money behind, and a line about a death often asks about them in the
# same breath: "my mum died, is the cremation expensive", "my dad died last week how long does
# probate take", "my husband passed away last month and i dont know where to start with probate".
# Those words are the administration, not a feeling, so the entry that knows what to do about them
# answers the line better than a condolence does, and the person is left holding the question.
ADMINISTRATION = re.compile(
    r"\b(?:funerals?|cremation|crematorium|burial|coffin|headstone|probate|wills?|estate|"
    r"solicitors?|coroner|register(?:ing)? the death|death certificate|medical certificate|"
    r"bank accounts?|insurance|pension|bereavement|inheritance|funeral directors?|grave|"
    r"chapel of rest|quotes?|cheapest)\b", re.I)


def asks_the_administration(line):
    """True when the line asks about the paperwork or the money a death leaves behind.

    Read on the words of the administration themselves, not on the shape of the ask: "is the
    cremation expensive" and "my dad died last week how long does probate take" are the funeral
    and the probate entries' lines, while "is it normal to still cry" is about the person and
    belongs to the condolence.
    """
    text = " ".join(str(line or "").lower().replace("\u2019", "'").split())
    return bool(ADMINISTRATION.search(text))


# The same words as one key each, so a line and a reply can be asked whether they are about the
# same piece of paperwork: "his bank accounts" and "the account holder has died" are both the
# accounts, and "probate" is probate whatever else the sentence says. A bare word is not enough
# on its own - "pension" belongs to the card about paying into one, and "will" to the card that
# defines one - so the key only decides the topic; the two questions below decide the rest.
ADMINISTRATION_KEYS = (
    ("accounts", r"\b(?:bank\s+)?accounts?\b|\bbereavement team\b"),
    ("registration", r"\bregist(?:er|ering|ration)(?:\s+(?:the|a|his|her|their))?\s+death\b"
                     r"|\bregister office\b"),
    ("death certificate", r"\bdeath certificate\b|\bmedical certificate\b"),
    ("probate", r"\bprobate\b|\bletters of administration\b"),
    ("inheritance", r"\binheritance(?: tax)?\b|\biht\d*\b"),
    ("estate", r"\bestate\b|\bexecutor\b"),
    ("will", r"\bwills?\b"),
    ("funeral", r"\bfunerals?\b|\bfuneral directors?\b|\bchapel of rest\b"),
    ("cremation", r"\bcremat(?:ion|orium|e|ed)\b"),
    ("burial", r"\bburials?\b|\bbury\b|\bburied\b|\bgrave(?:side)?\b"),
    ("coffin", r"\bcoffins?\b|\bheadstones?\b"),
    ("solicitor", r"\bsolicitors?\b"),
    ("coroner", r"\bcoroners?\b"),
    ("insurance", r"\binsurance\b|\blife cover\b"),
    ("pension", r"\bpensions?\b"),
)


def administration_keys(text):
    """The pieces of paperwork a line or a reply names, as plain keys."""
    lowered = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    return frozenset(key for key, pattern in ADMINISTRATION_KEYS
                     if re.search(pattern, lowered))


# A reply that only defines the word the person asked about answers a different question: "what
# do i do about her will" was answered with "A will says who gets what when you die", which gives
# the kind of answer the line asked for (it reads as instructions) and none of what to do.
DEFINES = re.compile(r"^\s*(?:a|an|the)\s+[\w'-]+\s+(?:says|means|is)\b", re.I)

# A death leaves paperwork behind, and a reply about it says whose it is: a card about paying
# into a pension is about a living person, however well its instructions fit the ask.
THE_DEATH = re.compile(
    r"\b(?:died|dies|dying|death|dead|deceased|passed away|bereave\w*|widow\w*|widower\w*|"
    r"estate|executor|next of kin|funeral|cremation|burial)\b", re.I)


def is_about_the_paperwork(reply, line):
    """Whether the reply answers the paperwork the line named, not merely the right shape.

    Three things have to hold, and each of them was a real turn: the reply has to name the same
    piece of paperwork the line named ("what do i bring to the funeral" was answered with the
    wake food list, which names none), it has to say whose paperwork it is ("i have to sort out
    her pension" was answered with a card about paying into your own), and it must not be a
    definition of the word ("what do i do about her will" got what a will is).
    """
    if not (administration_keys(line) & administration_keys(reply)):
        return False
    text = str(reply or "")
    if DEFINES.match(text) or not THE_DEATH.search(text):
        return False
    return True


# The open ask, with no thing of its own: "what do i do now", "what next", "where do i start",
# "so what do i do". Inside a loss it is not a shrug - it is the same question the loss asks,
# and the answer is the stage the chat is at. A line with a thing in it ("what do i do with her
# bed") is a practical question and the entries' line, so this shape has to be the whole line.
OPEN_ASK = re.compile(
    r"^\s*(?:(?:and|so|ok|okay|but|well|right)\s*,?\s*)*"
    r"(?:what\s+(?:do|should|shall|can|could)\s+(?:i|we)\s+(?:do|now|next)(?:\s+(?:now|next|today))?"
    r"|what\s+(?:now|next|happens\s+now|do\s+i\s+do\s+now)"
    r"|now\s+what|where\s+do\s+(?:i|we)\s+(?:start|begin)(?:\s+now)?"
    r"|what\s+am\s+i\s+supposed\s+to\s+do(?:\s+now)?)"
    # The same ask pointed at the death already on the table: "what should i do about it" is the
    # open ask with the loss as its object, and without this tail it was not an open ask at all.
    # A named object keeps its own line - "what do i do about the funeral", "what do i do with
    # her bed" - so only a pronoun comes in, and the ask with nothing in it still has to be the
    # whole line.
    r"(?:\s+about\s+(?:it|that|this|him|her|them|all this|all of it))?"
    r"\s*[.?!]*$")

# The coping ask: "i dont know how to get through it", "how do i get through the day", "how am i
# supposed to get through this". It carries no death and no subject, which is why nothing read
# it. "Get through to him" is reaching somebody, not surviving the week, so it is not this.
GET_THROUGH = re.compile(
    r"\bget(?:ting)?\s+through\s+(?:it|this|that|today|tonight|the\s+"
    r"(?:day|days|night|nights|week|weeks|weekend|first\s+few\s+days|first\s+week))\b"
    # "how do i get through it" and "how do i carry on" ask the same nameless thing. The object
    # has to be one of those words or missing: "how do i get through the funeral" names a thing
    # the knowledge base has an answer for, and that answer is the one to keep.
    r"|\bhow\s+(?:am|do|will|can)\s+i\s+(?:supposed\s+to\s+)?"
    r"(?:get\s+through|carry\s+on)"
    r"(?:\s+(?:it|this|that|today|tonight|the\s+"
    r"(?:day|days|night|nights|week|weeks|weekend|first\s+few\s+days|first\s+week)))?"
    r"\s*[.?!]*$")
GET_THROUGH_TO = re.compile(r"\bget(?:s|ting)?\s+through\s+to\b")
# The day that has to be got through can also be named: getting through christmas without
# somebody is the question the ritual pool answers, and the entries gave it a line about holiday
# entitlement ("bank holidays sit inside your 5.6 weeks of paid holiday").
GET_THROUGH_DAY = re.compile(
    r"\bget(?:ting)?\s+through\s+(?:christmas|the\s+holidays?|new\s+year|easter|"
    r"(?:his|her|their|my\s+(?:mums?|dads?|nans?|grans?|sons?|daughters?))\s+birthday|"
    r"birthdays?|the\s+anniversary|our\s+anniversary|mothers?\s+day|fathers?\s+day)\b")

# What is being got through decides whether the ask is about the loss at all. A pronoun, a bare
# stretch of time, a date or a ceremony is the loss itself, and the pool is the answer. A named
# practical thing has a subject of its own and an answer somewhere else, and a grief line for it
# answers the wrong question: inside a loss conversation "how do i get through this week of night
# shifts" was given "The first days are the hardest..." where the entry has the night-shift rota.
# Read on the words after "through" only, so a whole loss line keeps its pool: "get through the
# first christmas without her" is untouched.
GET_THROUGH_OBJECT = re.compile(r"\bget(?:ting)?\s+through\s+([a-z' ]{1,60})")
# The words that carry no subject of their own: articles, possessives, prepositions, and the
# adverbs that hang off an ask. A word here says nothing about what the thing is.
GET_THROUGH_FILLER = frozenset((
    "the", "a", "an", "this", "that", "these", "those", "my", "his", "her", "their", "our",
    "your", "of", "at", "in", "on", "to", "with", "without", "and", "for", "by", "from", "s",
    "too", "as", "well", "again", "now", "still", "just", "all", "every", "first", "next",
    "last", "few", "couple", "up", "through", "it", "him", "them", "us", "me", "i", "if", "when",
    "while", "til", "until", "alone", "so", "very", "much", "more", "each", "any", "some",
))
# And the words that are the loss: a stretch of time with nothing else in it, a date or a
# ceremony, and the vocabulary of a death. A named thing outside this list is a subject, and the
# entry that knows it answers better than sympathy can.
GET_THROUGH_THE_LOSS = frozenset((
    "day", "days", "night", "nights", "week", "weeks", "weekend", "weekends", "month",
    "months", "year", "years", "hour", "hours", "evening", "evenings", "morning", "mornings",
    "afternoon", "afternoons", "today", "tonight", "tomorrow", "time", "times",
    "christmas", "xmas", "easter", "new", "birthday", "birthdays", "anniversary", "wedding",
    "funeral", "wake", "holiday", "holidays", "mothers", "fathers", "mother", "father", "mum",
    "mums", "dad", "dads", "nan", "nans", "gran", "grans", "son", "sons", "daughter",
    "daughters", "valentines", "death", "dying", "loss", "grief", "sorrow", "mourning",
    "missing", "absence", "empty", "quiet", "silence", "sad", "hard", "hardest", "worst", "bad",
    "dark", "lonely", "pain", "ache", "rest", "everything", "bit", "part", "piece", "pieces",
    "one", "two", "three", "it", "them", "him", "her",
    # going back among people is the loss's question too: "get through this week at work" in a
    # bereavement chat is the first week back, not a question about shifts
    "work", "office", "colleagues", "people",
))


def _a_thing_of_its_own_to_get_through(line):
    """True when the "get through" ask is about something that has an answer of its own.

    The pool belongs to the loss: a pronoun, a bare day or week, a date, a ceremony. Anything
    else in the object names a thing with its own subject - night shifts, the rota, a driving
    test, the exam period, the paperwork - and the entry that knows that thing is the answer.
    """
    found = GET_THROUGH_OBJECT.search(line)
    if not found:
        return False
    for word in words_of(found.group(1)):
        if word in GET_THROUGH_FILLER or word in GET_THROUGH_THE_LOSS:
            continue
        return True
    return False


def asks_for_a_decision(line):
    """True when the line asks what to do now, not how the person feels.

    "my dog died" and "we had to put our cat down yesterday" say the thing and ask for nothing:
    the card's "nothing has to be decided today, the vet can arrange cremation" is colder than
    a sympathy on that day. "my rabbit died, do we need to bury it deep" and "what do i do with
    her bed" do ask, and the pets entry is the only thing that knows.
    """
    text = " ".join(str(line or "").lower().replace("\u2019", "'").split())
    return bool(PRACTICAL_ASK.search(text))


# "my dog died, is cremation sad": the feeling word is the predicate of the body question, not a
# statement about the person, so it is still a question about the body. "my dog died, i feel
# guilty about the cremation" is the person's own feeling and stays a condolence.
BODY_FEELING = re.compile(
    # "is cremation sad" puts the copula first, "the cremation was sad" puts the body word first,
    # and both have the feeling word as the predicate of the body, not of the person.
    r"\b(?:is|was|feels|seems|sounds)\s+(?:\w+\s+){0,3}"
    r"(?:cremat\w*|burial|burying|ashes|coffin|casket|urn|grave|euthanasi\w*)\s+"
    r"(?:\w+\s+){0,3}"
    r"(?:sad|hard|difficult|awful|grim|brutal|expensive|cheap|costly|right|wrong|ok|okay|"
    r"easy|quick|painful|kind|better)\b"
    r"|\b(?:cremat\w*|burial|burying|ashes|coffin|casket|urn|grave|euthanasi\w*)\s+"
    r"(?:is|was|feels|seems|sounds)\s+(?:\w+\s+){0,2}"
    r"(?:sad|hard|difficult|awful|grim|brutal|expensive|cheap|costly|right|wrong|ok|okay|"
    r"easy|quick|painful|kind|better)\b")

def feeling_about_the_body(line):
    """True when a feeling word in the line is about the body, not about the person."""
    return bool(BODY_FEELING.search(" ".join(str(line or "").lower().split())))


def names_a_feeling(line):
    """True when the line talks about the person's own feelings, so sympathy beats the card.

    "my cat died and i keep crying" is not a question about cremation; "we had to put our cat
    down yesterday" is, and the pets entry earns that turn. The loss module reads this before it
    lets another candidate keep the turn (`DEFERS_TO`).
    """
    text = " ".join(str(line or "").lower().split())
    # The absence shape is how people say it in the days after: "i keep expecting him at the
    # door", "the house feels so quiet". ABSENCE already reads those for the composer, so this
    # guard is no wider than the rest of the file and the two cannot disagree.
    return bool(OWN_STATE.search(text) or ABSENCE.search(text))


def acknowledges(reply):
    """True when a reply says the sad thing in its own words, so an entry that does can speak.

    Public because the loss module hands it to the arbiter as `DEFERS_TO`: a topic entry that
    already acknowledges the death (the pets entry, with cremation and a paw print) is a better
    answer than a generic sympathy, so the arbiter lets it keep the turn.
    """
    return bool(ACKNOWLEDGE.search(" ".join(str(reply or "").lower().split())))


# "What time is the funeral?" is a different question from "should I go?": it wants when and
# where, which only the family or the funeral director can say.
WHEN_ASK = re.compile(r"\b(what time|what day|what date|which day|when is|when's|whens|"
                      r"how long until|how long till|what time does)\b")
FUNERAL_WHEN_REPLIES = (
    "The time and place are on the family's notice or the funeral director's page — ask a family "
    "member or the funeral director if you can't find it, nobody minds being asked.",
    "Check the notice the family put out, or ring the funeral director: they will tell you the "
    "time and where to meet. Ask whether to go straight to the crematorium or meet at the house.",
    "Ask a relative or the funeral director for the time and the meeting place — most services "
    "are at the church or chapel first, then the crematorium — and get there a little early.",
)


def _when_asked(tight):
    """True for a line asking when the funeral is, rather than whether to go."""
    return bool(WHEN_ASK.search(tight))


def a_part_of_the_day_asked(tight):
    """True when the line asks about a part of the service, not whether to be at it.

    "what song should i play at my dads funeral", "what reading should i do at mums funeral",
    "should we have flowers at the funeral" and "should i take my kids to my mums funeral" all
    reached the funeral card ("If you can make it, go"), which is about turning up. The music,
    the readings, the flowers, the length and whether the children come are each a knowledge
    row, and the person asking is often the one arranging the day. A line asking what to *say*
    stays here: the words for a funeral are this file's.
    """
    if not A_PART_OF_THE_DAY.search(tight):
        return False
    return not SAY_THE_WORDS.search(tight)


# A question whose subject is the feeling rather than the death: "is it normal to feel
# relieved", "is it weird that i feel relieved about it", "why do i still feel guilty". The same
# feeling word in "what do i say at the funeral" is a question about the day, and the pools that
# answer it are untouched.
ASKS_ABOUT_THE_FEELING = re.compile(
    r"\bis\s+(?:it|that|this)\s+(?:normal|weird|wrong|bad|ok|okay|common|selfish|strange|odd|"
    r"awful)\s+(?:to\s+)?(?:feel|be)\b"
    r"|\bis\s+(?:it|that)\s+(?:normal|weird|wrong|bad|ok|okay|common|selfish|strange|odd)\s+"
    r"(?:that|if)\s+i\s+(?:feel|felt|am)\b"
    r"|\bis\s+that\s+a\s+(?:normal|bad|selfish|strange)\s+thing\b"
    r"|\bwhy\s+do\s+i\s+(?:still\s+)?(?:feel|keep\s+feeling)\b"
    r"|\bdoes\s+(?:it|that)\s+(?:make\s+me|mean\s+i'?m)\b", re.I)


def _asks_about_the_feeling(tight):
    """Whether the question is about the feeling rather than about the death or the day."""
    return bool(ASKS_ABOUT_THE_FEELING.search(tight))

SYMPATHY = re.compile(r"\b(sympathy|condolence|condolences|bereavement)\b")
CARD_WORD = re.compile(r"\b(card|cards|message|note|letter|text)\b")
ASK_FORM = re.compile(r"\b(should i|do i|can i|how do i|shall i|would you)\b")
# The same questions said by a household rather than by one person: "should we bury him at home",
# "can we get her cremated", "do we need to register it". Missing these made a family's question
# read as a statement, so the pet card and the practical cards never saw it.
ASK_WE = re.compile(r"\b(should we|can we|do we|how do we|shall we|where do we|what do we|"
                    r"when do we|who do we)\b")
# The second half of a line: "my cat died, is cremation expensive" is a question even though it
# does not open with one.
ASK_TAIL = re.compile(r",\s*(?:is|are|was|were|do|does|did|should|can|how|what|where|when|who|"
                      r"will|would|shall)\b")
# What happens to the body, in the words people use the day after.
PET_ARRANGEMENT = re.compile(
    r"\b(bury|buried|burying|burial|body|bodies|dead|ashes|cremat\w*|cremate|urn|plot|grave|graveside|"
    r"headstone|memorial|paw\s?print|lock\s+of\s+(?:fur|hair)|coffin|casket|collect\w*|"
    r"pick\w*\s+(?:\w+\s+){0,2}up|collect\s+\w+\s+from\s+the\s+vet)\b")
PET = re.compile(r"\b(cat|dog|puppy|kitten|rabbit|hamster|guinea\s?pig|horse|pony|budgie|parrot|"
                 r"pet|pets|ferret|gerbil|rat|mouse|tortoise|snake|lizard|fish|goldfish)\b")
# The animal is the one who has had enough: "my dog wants to die", "my cat has no quality of life",
# "he doesnt want to live anymore". Nothing has died and no vet has given a timeline, so every pool
# below reads the line as somebody else's death sentence or as nothing at all - the answer is the
# days before it, and this is the wish that says so. A person getting these words is left alone
# (`_a_pet_of_ours`), and so is a speaker who says the same of themselves in the same line: that
# line is a crisis, and bot/modules/safety.py keeps the card for it.
# "my dog has had enough" is a goodbye; "my dog has had enough of the rain", "... of the car",
# "... of the vet", "... of the food" is an ordinary annoyance. The two shared one pattern to
# begin with, so a fence listing the harmless nouns would always be one noun short (reviewers
# measured rain, the car, the vet, the hoover, the food and his dinner within an hour). Ask what
# the line does after "had enough" instead: it has to stop there, or name the animal's state.
PET_HAS_HAD_ENOUGH_AFTER = (
    r"has\s+had\s+enough"
    r"(?=\s*(?:[,.!?;]|$)"
    r"|\s*,?\s*(?:of\s+)?(?:it|this|life|everything|it\s+all|all\s+of\s+it)\b"
    r"|\s*,?\s*(?:of\s+)?(?:the|his|her|their)\s+"
    r"(?:pain|suffering|treatment|chemo|medication|operations|surgery|seizures|incontinence)\b"
    r"|\s*,?\s+(?:he|she|it|they)?\s*(?:is|are|s)?\s*(?:not\s+eating|stopped\s+eating|"
    r"cant\s+eat|cant\s+get\s+up|cant\s+walk|cant\s+stand|in\s+pain|suffering|giving\s+up)\b"
    r"|\s+(?:now|today|already)\b)")
PET_HAS_HAD_ENOUGH = re.compile(
    r"\b(?:wants?\s+to\s+die|wants?\s+to\s+be\s+put\s+to\s+sleep|no\s+will\s+to\s+live|"
    r"doesn'?t\s+want\s+to\s+live|does\s+not\s+want\s+to\s+live|no\s+quality\s+of\s+life|"
    + PET_HAS_HAD_ENOUGH_AFTER + r")\b")
SPEAKER_HAS_HAD_ENOUGH = re.compile(
    r"\b(?:i|me|myself)\b[^.?!]{0,24}\b(?:die|dying|kill\s+myself|end\s+it|go\s+on)\b|"
    r"\b(?:so\s+(?:do|will|would|can|am|are|have|has)\s+i|me\s+too)\b")
# The ending said twice in one line: "my dog is at the end and so am i", "my nan is fading fast and
# so am i", "my dad is at the end and i am too". The first half is somebody else's week, so the arms
# above answer for them - the animal's days before, or a carer's pool - and `SPEAKER_HAS_HAD_ENOUGH`
# stands the pet arm down and then nothing answered at all: the line came back as "Thanks for
# telling me", as a punt, or as the echo "Noted: your nan is fading fast and so am you." The
# speaker has put themselves in the same place as the one they are losing, so the answer is for
# both of them, and it offers a person to talk to instead of arranging the vet.
SPEAKER_TOO = re.compile(
    r"\b(?:and\s+)?so\s+(?:am|do|have|has|will|would|can|are|is)\s+i\b"
    r"|\b(?:and\s+)?i(?:'m|\s+am|\s+do|\s+have|\s+will|\s+would|\s+can)\s+(?:too|as\s+well)\b"
    r"|\b(?:me\s+too|same\s+here|i\s+feel\s+the\s+same|i\s+feel\s+it\s+too|"
    r"neither\s+(?:do|am|have)\s+i)\b")
# A wish in the line is the safety lane's card and its card is the right one: "my dog wants to die
# and so do i", "my cat is at the end and i want to die" keep the suicide card, not this pool.
WISH_FRAME = re.compile(
    r"\b(?:want|wants|wanted|wanna|wish|wishes|wished|plan|plans|planning|tempted|urge|"
    r"thinking\s+(?:of|about)|thought\s+about)\b|\b(?:going|gonna)\s+to\b")
# Two people at the end at once is too much for one of them to hold quietly, so the reply names
# both, offers a person, and gives the crisis line without assuming the speaker means suicide.
SPEAKER_TOO_REPLIES = (
    "You are carrying their ending and your own in the same breath, and that is more than one "
    "person should hold. Tell someone today - a GP, a friend, or a crisis line on 116 123 in the "
    "UK or 988 in the US - and let them take a share of it.",
    "That is two of you at the end at once, and you should not be managing it on your own. Ring a "
    "crisis line today (116 123 in the UK, 988 in the US), or tell someone close so they can be "
    "with you while you say the rest.",
    "I'm sorry. Both at once is more than one person can carry quietly: say it out loud to someone "
    "today - a friend, your GP, or a crisis line on 116 123 in the UK or 988 in the US - and let "
    "them help with the next bit.",
    "You matter in this too, not only the one you are losing. Please tell someone today - a crisis "
    "line is 116 123 in the UK and 988 in the US - and let them sit with you while you say it.",
)
# The owner's own words for the coming goodbye, which are not words for a death anywhere else:
# "my dog is done", "my cat is ready to go", "i think my dog is telling me its time", "he is 15 and
# i think its time". Each is only these words about an animal - "my dad is done" is a hard week and
# "my nan is ready to go home" is a discharge - so this fence is read only when the animal is ours
# and the speaker's own wish is not in the line. "is done" and "ready to go" stop the sentence, so
# "my dog is done with his dinner" and "ready to go for a walk" stay ordinary.
PET_AT_THE_END = re.compile(
    r"\b(?:is|are|seems?|looks?)\s+done\b(?=\s*(?:[,.!?;]|$))"
    r"|\bready\s+to\s+go\b(?=\s*(?:[,.!?;]|$))"
    r"|\btelling\s+me\s+(?:its|it'?s|his|her)\s+time\b"
    r"|\bi\s+think\s+(?:its|it'?s)\s+time\b")

FILLERS = frozenset(("actually", "really", "even", "just", "exactly", "honestly",
                     "literally", "basically", "anyway", "still", "perhaps", "maybe"))
# A death arrives with a feeling, and a condolence answers none of it. Guilt and anger are the
# two that turn up most ("i feel guilty about my mums death", "i feel angry about her death"),
# and naming the feeling back beats a generic "I'm so sorry" (STYLE.md: answer what they said).
FEELING_WORDS = {
    "guilty": "guilt", "guilt": "guilt", "ashamed": "guilt", "shame": "guilt",
    "angry": "anger", "anger": "anger", "furious": "anger", "rage": "anger",
    "numb": "numb", "relieved": "relief", "relief": "relief",
}
FEELING_REPLIES = {
    "guilt": (
        "Guilt turns up with grief for most people, whether or not there is anything to be "
        "guilty about. Say the thing you keep going over out loud to someone who knew them; "
        "it weighs less that way.",
        "That guilt is a common part of it, and it is rarely fair. Tell one person who knew "
        "them what you keep turning over — you do not have to carry it on your own.",
    ),
    "anger": (
        "Anger is part of grief for most people, and it does not have to make sense. Let it "
        "out somewhere safe, then tell someone who knew them what you are angry about.",
        "Being angry at them, or at the world, or at whoever was there is common after a "
        "death. Say it out loud to one person you trust rather than keeping it in.",
    ),
    "numb": (
        "That numb feeling is common early on; it is not coldness. Be gentle with yourself "
        "today, and tell me or one person close to you if it stays like this.",
        "Numb is one of the ways grief shows up first. Nothing has to be decided today — "
        "just keep eating and sleeping, and let someone know how you are.",
    ),
    "relief": (
        "Relief after a death is more common than people admit, and it does not cancel the "
        "grief. Say it to someone who will not judge it — that is usually enough to make it "
        "sit easier.",
        "Feeling relief does not make you cold. If they were ill for a long time it is a "
        "normal thing to feel, and it can sit alongside missing them.",
    ),
}


def _feeling(tight):
    """The feeling the line names, if it names one of ours, else ""."""
    for word in tight.split():
        if word in FEELING_WORDS:
            return FEELING_WORDS[word]
    return ""


# A line that is nothing but a greeting: the word, then an optional "again/there/all", then
# nothing, or the polite "how are you" that is part of the greeting rather than a question about
# the bot. Anchored at both ends because any content after the hello is news ("hi, its still
# bleeding", "hiya my dad died") and belongs to the pools.
HELLO_ON_ITS_OWN = re.compile(
    r"^(?:hi+|hey+|hello+|hiya+|yo|howdy|morning|good morning|afternoon|good afternoon|evening|"
    r"good evening|greetings)\b[\s,!.]*"
    r"(?:(?:again|there|all|everyone|everybody|folks|you|mate|love|both)\b[\s,!.]*)*"
    r"(?:(?:how are (?:you|things|you doing|you keeping)|how'?s it going|hows it going|"
    r"how are we|you ok|you alright|hope you'?re well|its me)\b[\s,.!?]*)*$")

# A hello inside a bereavement chat, with no news in it at all ("hiya", "hello again",
# "morning"). The cheerful pool that starts a new day - "Morning! How's your day going?" - reads
# as if the bot had forgotten the death two lines up, and the condolence again reads as if the
# person had said nothing. So the hello is answered as a hello that remembers, and the door back
# to the loss is left open. Only a line that is nothing but a greeting gets here: "hi, its still
# bleeding" and "hiya, my dad died" carry news and go to the pools below.
HELLO_AFTER = (
    "Hello again. I'm still here - how are you doing today?",
    "Hi. No need to say anything in particular - how are you holding up?",
    "Hello. I'm here whenever you want to talk about it, or about anything else.",
    "Hi again. How has the day been?",
)
# How long it has been is the whole of what some lines say. "its been a year", "six months now",
# "nearly two years": inside a bereavement chat that is not small talk, it is the person saying the
# date out loud, and both main's pools answered it as if they had said nothing ("I'm listening - say
# more if it helps", "Thanks for telling me - I'm here if you want to dig into any of that"). None
# of these names a duration, so one pool answers all of them: the line is about the size of the
# gap, not about the number in it.
TIME_SINCE_REPLIES = (
    "The calendar is a poor measure of it. However long the gap is, it takes the time it takes.",
    "Dates like that come round whether you are ready or not. Whatever it is like on the day, it "
    "is allowed to be like that.",
    "Most people around you will have stopped counting long before you did. That is not you doing "
    "it wrong.",
    "However long it has been, this is not something you are meant to be over by now. Be as "
    "gentle with yourself about it as you would with anybody else.",
    "It tends to come back in waves rather than fade in a straight line. What has it been like "
    "for you lately?",
)
# The gap said out loud after an ending rather than a death: "my girlfriend broke up with me" then
# "its been 3 weeks". Nothing has died, so `reads_as_loss` is right to leave the line alone, and
# the line named no entry of its own, so the widen in bot/modules/chat.py read it with the topic
# in front of it and the nearest entry answered it - "Faulty goods are the retailer's problem, not
# the maker's" for two people who split up. The chat is a loss in everything but the word, so the
# gap is answered as the gap. A pool of its own rather than `TIME_SINCE_REPLIES`, because two of
# those lines are about a date coming back round the year, which is the wrong day for an ending.
ENDING_SINCE_REPLIES = (
    "The calendar is not the measure of this. However long it has been, it is not a deadline you "
    "are behind on.",
    "Most people are still in pieces at this point and telling nobody. You are not late.",
    "It does not fade in a straight line, so a bad morning now does not mean you went backwards.",
    "Being able to say how long it has been is its own kind of progress, even on a day that hurts.",
    "However long it has been, you are allowed to still mind. That is not you doing it wrong.",
)
# The endings that are two people's, with a person in front of them or the leaving said plainly.
# A news line ("we split the bill") is not this, so the split is only read with "up", and
# "separated" has to be about people rather than eggs.
_THE_ONE_WHO_LEFT = (
    r"(?:he|she|they|my\s+(?:wife|husband|partner|girlfriend|boyfriend|fiance|fiancee|ex|"
    r"other\s+half|missus|man|woman))")
AN_ENDING = re.compile(
    # "broke up" on its own is the bridge that broke up the traffic as often as it is two people,
    # so it is read with a person at one end: "broke up with", "we broke up", "i just broke up".
    r"\b(?:broke\s+up\s+with|(?:i|we|they|he|she)\s+(?:just\s+|finally\s+|recently\s+)?broke\s+up|"
    r"break\s+up|breaking\s+up|split\s+up|splitting\s+up|dumped\s+me|"
    r"got\s+dumped|divorced\s+(?:me|him|her)|got\s+divorced|getting\s+divorced|"
    r"walked\s+out\s+on\s+me|" + _THE_ONE_WHO_LEFT + r"\s+left\s+me|"
    r"ended\s+it\s+with\s+me|we\s+are\s+through|we\s+are\s+over)\b", re.I)
# "how long will it take to feel better", "will it ever stop hurting", said in the chat about an
# ending rather than a death. The two shapes a person asks in the first month, and neither names
# the ending, so both are read off the chat. Only the ask, not a line that names its own subject
# ("how long will my cold take to clear up" after a break-up is still a cold).
A_FEELING_BETTER_ASK = re.compile(
    r"\b(?:how\s+long|when\s+will|(?:will|does|is|can)\s+it(?:\s+ever)?)\b"
    r".{0,45}?\b(?:feel|get|be|stop)\s+(?:better|over\s+it|myself\s+again|back\s+to\s+normal|"
    r"hurting|easier|normal|right|ok|okay)\b", re.I)
# The gap named on its own is the shape people use in the second month ("three weeks today"), and
# the honest answer is that the calendar is not the measure of it.
ENDING_FEELINGS_REPLIES = (
    "The worst of it usually eases over a few weeks and then comes back in shorter waves. A bad "
    "day a month from now is part of it, not a step back.",
    "There is no set time, and anybody who gives you one is guessing. The mornings usually lift "
    "before the evenings do, and the odd day still catches you.",
    "Most people find the sharp edge goes within a few weeks and the flat days last longer than "
    "the crying ones. If months go by with no good day in them, that is worth talking to someone "
    "about.",
)

# The span itself: "its been a year", "six months now", "nearly two years", "a year this week",
# "two years on". Read only inside a chat that is already about a death, and only on a line that
# says nothing else, so "ive been off work for a year" and "its been a year since i started the
# job" keep their own answers.
_SPAN_COUNT = (
    r"a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2}|few|couple"
    r"|several")
A_SPAN = re.compile(
    # "a year and a half", "two and a half years" and "half a year" are one gap however they are
    # written, and "and a half" is how most people say a year and a bit.
    r"\b(?:(?:%s)(?:\s+and\s+a\s+half)?\s+(?:day|week|month|year)s?"
    r"(?:\s+and\s+a\s+half)?|half\s+an?\s+(?:day|week|month|year)s?)\b"
    % _SPAN_COUNT, re.I)
# The gap said without a number in it: "its been a long time", "its been quite a while".
A_SPAN_NO_NUMBER = re.compile(
    r"\b(?:a (?:long|good|fair) (?:time|while)|(?:quite )?a while)\b", re.I)
A_SPAN_LEAD = re.compile(
    r"\b(?:been|nearly|almost|just over|over|about|only|coming up|nearly a|a year this week)\b", re.I)
A_SPAN_TAIL = re.compile(
    r"\b(?:now|this week|today|on|ago|already|next week|coming up|marks?\b|marking)\b", re.I)
# The line has to be about the gap and nothing else: a job, a habit or a plan that also has a
# length in it is that thing, not the loss.
A_SPAN_ELSEWHERE = re.compile(
    r"\b(?:since|started|stopped|quit|gave up|off work|signed off|been doing|been on|sober|"
    r"smoking|drinking|diet|gym|job|course|school|married|together|moved|live|living|"
    r"rent|paying|treatment|therapy|sober)\b", re.I)


def _how_long_since(tight, words):
    """True when the line says only how long it has been, inside a bereavement chat.

    "its been a year", "six months now", "nearly two years". The span has to be there, the line
    has to be short, and it must not name anything else with a length in it - a job, a course, a
    habit - because those are their own subjects even three lines after a death.
    """
    if not tight or len(tight.split()) > 9:
        return False
    if ASK_FORM.search(tight) or "?" in tight:
        return False
    if A_SPAN_ELSEWHERE.search(tight):
        return False
    span = A_SPAN.search(tight)
    if not span:
        # "its been a long time" is the gap said without a number in it. It is the same shape and
        # the same pool, and no other reader knows what to do with it either.
        span = A_SPAN_NO_NUMBER.search(tight)
    if not span:
        return False
    rest = (tight[:span.start()] + " " + tight[span.end():]).strip()
    # The span is the gap however many words it takes to write, so it is counted as one: what is
    # left has to be short, or the line is about something longer than the gap.
    if len(rest.split()) + 2 > 6:
        return False
    if not (A_SPAN_LEAD.search(rest) or A_SPAN_TAIL.search(rest) or len(rest.split()) <= 2):
        return False
    return True

# "i miss my mum", "missing my dog today": no death is said, and there is nothing to solve. The
# fallback answered it as a problem ("That sounds rough. If you want, I can help you think through
# what to do next."), which is the wrong thing to offer someone who is only saying they are sad,
# and calling it news ("I'm so sorry to hear that") invents a death they did not mention.
MISS_REPLIES = (
    # Main's own line for a miss, kept as it is: it is the one concrete thing said about grief
    # here, and a reader that answers the line should not be a step down from it. The other four
    # are the variety a pool is for - no offer of a task, and no line that explains the feeling
    # back to the person who is having it.
    "Of course you do. It goes in waves, and the waves get further apart.",
    "The ones we miss are the ones who mattered. Say as much or as little as you like.",
    "That ache is real, and it doesn't keep office hours. Say more whenever you want to.",
    "Missing like that makes sense. Those days can be long ones — I'm around if talking would "
    "help.",
    "Some days the missing is louder than others. No need to do anything with it here; I'm just "
    "listening.",
)
# The verb is present tense only ("i miss / i'm missing"), because "i missed my mum" is as often
# a missed train as a bereavement. What is missed has to be a person or a pet, said with an owner
# ("my mum", "our old dog") or as a pronoun, and it has to be the end of what they said about it,
# so "i miss my mum's cooking" and "i miss my old flat" keep their own meanings.
# "ive been missing him" and "im missing my mum" are the same line as "i have been missing him",
# and they are how most people type it: with the bare `i` alone, the apostrophe-less form never
# matched and the line fell through to the greeting ("Sorry to hear that. What would help right
# now?"), which is a reaction to news rather than to the missing.
MISS_SUBJECT = (r"(?:i|we|i'm|im|i've|ive|we're|were|we've|weve)")
MISS_VERB = re.compile(r"\b" + MISS_SUBJECT +
                       r"\s+(?:really\s+|so\s+much\s+|just\s+|properly\s+)?"
                       r"(?:have\s+|been\s+|am\s+|are\s+)?(?:miss|missing)\b"
                       r"|\bmissing\s+(?:my|our)\b", re.I)
# Who people say they miss, which is not quite who a death is read for: "i miss my boyfriend"
# and "i miss my twin" are the missing, and neither word is a bereavement noun. The set is local
# to this reading so the death reader still sees only the relations a death is written with.
MISS_PEOPLE = PEOPLE | frozenset((
    "boyfriend", "girlfriend", "fiance", "fiancee", "twin", "twins", "stepdad", "stepmum",
    "ex", "husband", "wife", "partner", "mates", "flatmate", "roommate", "bestie",
))
# A partner is not in `PEOPLE` because a death is never read from "my boyfriend died" alone -
# the death reader wants a relation it knows - so "i miss my boyfriend" and "i miss my girlfriend"
# were answered "Of course you do. It goes in waves", the stock chat line the whole change is
# about. "i miss my twin" missed for the same reason. Adding them here and not to `PEOPLE` keeps
# the death reader reading exactly what it read before.
MISS_NOUN = re.compile(r"\b(?:my|our|his|her|their)\s+(?:[a-z]+\s+){0,2}(?:" +
                       "|".join(sorted(MISS_PEOPLE, key=len, reverse=True)) + r")\b", re.I)
# The words between "my" and the person can only be words about the person themselves. "my life
# before kids" is the life they had, not the children: a word that moves the missing to another
# time or place means the noun after it is not what is missed.
MISS_NOT_BETWEEN = re.compile(r"\b(?:before|after|without|since|from|during|when|until|like|"
                              r"around|away)\b", re.I)
MISS_TAIL = re.compile(r"^\s*(?:$|[.,;:!?]|\b(?:today|tonight|so much|a lot|loads|terribly|"
                       r"badly|every day|still|again|now|already|lots|heaps|more than ever|"
                       r"like mad|to bits|awfully)\b|\band\b|\bbut\b|\bso\b)", re.I)
# The animals, so a name after the animal ("i miss my old dog rex") is still the animal missed.
MISS_ANIMALS = frozenset("""dog dogs cat cats puppy kitten rabbit hamster budgie parrot horse pony
pet pets tortoise ferret guinea""".split())
# The word after the animal is its name ("i miss my dog rex") unless it is one of the things that
# live beside an animal: "i miss my dog walker" is a person, and a dog food bowl is not a dog.
MISS_ANIMAL_NOUNS = frozenset("""walker walkers sitter sitters food bed beds bowl bowls lead leads
collar collars toy toys treat treats vet vets breeder breeders groomer groomers blanket blankets
basket baskets door doors lead name""".split())
MISS_PRONOUN = re.compile(r"\b" + MISS_SUBJECT +
                          r"\s+(?:really\s+|so\s+much\s+|just\s+)?"
                          r"(?:have\s+|been\s+|am\s+|are\s+)?(?:miss|missing)\s+"
                          r"(?:him|her|them|mum|dad|nan|gran)\b", re.I)
# "i miss having a dog" is a wish, not a bereavement, and "do you miss me" is a question about the
# bot's own feelings, not something to be comforted about.
MISS_NOT = re.compile(r"\b(?:miss|missing)\s+(?:having|being|doing|going|work|working|school|"
                      r"home|the|a|an|me|you)\b", re.I)
ASK_AT_START = re.compile(r"^\s*(?:do|does|will|would|did|are|is|have|has|can|could|should)\b", re.I)


def _missing_someone(text):
    """True when the line says they miss a person or a pet, without saying that anyone died."""
    if not MISS_VERB.search(text):
        return False
    if ASK_AT_START.match(text) or "?" in text:
        return False
    noun = MISS_NOUN.search(text)
    if noun and MISS_NOT_BETWEEN.search(noun.group(0)):
        noun = None
    if not (noun or MISS_PRONOUN.search(text)):
        return False
    if MISS_NOT.search(text):
        return False
    found = noun or MISS_PRONOUN.search(text)
    if noun and not MISS_TAIL.match(text[found.end():]):
        # "i miss my mum's cooking", "i miss my dog walker": what is missed is the thing after.
        rest = text[found.end():].strip()
        animal = found.group(0).split()[-1].lower() in MISS_ANIMALS
        named = re.match(r"([A-Za-z]+)([.!?]?)(.*)$", rest)
        if not (animal and named and named.group(1).lower() not in MISS_ANIMAL_NOUNS
                and MISS_TAIL.match(named.group(3))):
            # "i miss my old dog rex", "i miss my cat milly so much": the name after the animal is
            # still the animal that is missed.
            return False
    return True


# A line that asks about a feeling itself - "how do i stop feeling guilty", "i feel so sad" - has an
# answer of its own in the chat band's pools, and the condolence pool says nothing about what was
# asked. The composer stands aside for those. Only a feeling state counts, not something a person
# does: "how do i stop crying" has no answer of its own, and the warmth here beats a shrug.
FEELING_STATES = frozenset((
    "guilt", "guilty", "ashamed", "shame", "sad", "sadness", "angry", "anger", "furious", "rage",
    "numb", "relief", "relieved", "lonely", "empty", "hopeless", "anxious", "anxiety", "worried",
))
FEELING_ASK = re.compile(r"\bhow (?:do|can|could|should) i (?:stop|deal with|cope with|get rid of|"
                         r"handle|manage)\b|\bi (?:just |really |still |keep )?feel(?:ing)?\b", re.I)
# The words a question about a feeling is made of: nothing in it names anything else, so the feeling
# is the whole subject. A person in the line ends that ("i feel guilty about shouting at her").
FEELING_ONLY_WORDS = frozenset("""how do does can could should would i me my im am is are was
what when it this that the a an so really still just very much anymore again now bad worse better
feel feels feeling stop deal with cope get rid of handle manage about over like why""".split())


# The words in a feeling ask that only say who it is about: "i feel guilty about her", "i feel sad
# about my mum". They are not a second subject, so they do not keep the turn for the loss.
FEELING_PERSON_WORDS = frozenset((
    "he", "she", "him", "her", "hers", "they", "them", "their", "theirs", "his", "who",
)) | MISS_PEOPLE


def _a_question_about_the_feeling(line, words):
    """True when the line asks about a feeling itself and names nothing else to be about.

    Main has a reader of its own called `_asks_about_the_feeling(tight)` a few hundred lines up,
    and its call site passes one argument: a second function of the same name here does not
    replace that call, it breaks it - the later definition wins and the call raises a TypeError
    that the module's own `except` swallows, so the loss stands down for every line that reaches
    it. Hence the different name.

    The person can be named and it is still the feeling: "i feel guilty about her" asks about the
    guilt, and the answer to it is the same one the line gets standing alone. What ends it is a
    deed or a thing in the line - "i feel guilty about shouting at her" is about the shouting.
    """
    if not FEELING_ASK.search(line):
        return False
    if not (words & FEELING_STATES):
        return False
    return not (words - FEELING_STATES - FEELING_ONLY_WORDS - FEELING_PERSON_WORDS)


# And the words that are about grief only when the line is about the person themselves:
# "i still can't sleep", "some days i can't get out of bed", "it was really hard". A line that
# names its own subject keeps its own answer, so "the pub was dead quiet last night" and
# "my boss is hard work at the moment" are not bereavement.
GRIEF_SELF = frozenset((
    "hard", "hardest", "tough", "rough", "bad", "awful", "horrible", "heavy", "hurts", "hurt",
    "sleep", "sleeping", "sleepless", "slept", "bed", "nights", "night", "wake", "wakes",
    "woke", "tired", "exhausted", "weird", "strange", "stuck", "empty", "quiet", "silent",
    "silence", "coping", "cope", "eating", "appetite", "mornings", "morning",
    # How a family member not managing is described ("my mum isnt coping") - see FAMILY below,
    # these only count when the line names one.
    "struggling", "struggle", "breaking", "broken", "withdrawn", "shut", "drinking",
    "unbearable",
))
# A family member who is not coping is the same story from one step out: after "my dad died",
# "my mum isnt coping" is not a new subject. The words above decide the second half; this is
# the first - a named family member, never "my boss" or "my friend".
FAMILY = frozenset(("mum", "mom", "mam", "dad", "mother", "father", "brother", "sister",
                    "son", "daughter", "wife", "husband", "partner", "nan", "nana", "grandad",
                    "grandma", "grandpa", "granny", "gran", "uncle", "aunt", "auntie", "cousin",
                    "family", "parents", "kids", "children", "baby"))
# The openers that make a line about the person talking, rather than about the pub or the boss.
SELF_OPENERS = (
    "i ", "i'", "im ", "ime ", "ive ", "id ", "some days", "some nights", "most days",
    "most nights", "every night", "at night", "lately", "these days", "it ", "it's ", "its ",
    "that ", "that's ", "this ", "they ", "we ", "we're ",
)
# "my" says something about the person only when it is a part of their own life.
SELF_NOUNS = frozenset(("sleep", "night", "nights", "mornings", "mood", "head", "appetite",
                        "grief", "sadness", "coping"))
# "this morning", "last night" say when, not how they are: they are not a grief cue.
WHEN_WORDS = frozenset(("this", "last", "next", "tomorrow", "yesterday", "every", "one", "that"))
# A question that points back at what was just said, without naming anything.
GRIEF_REFERRING = ("is that normal", "is it normal", "is this normal", "does it get better",
                   "will it get better", "does it ever stop", "when does it stop",
                   "how long does it last", "does it get easier", "will it always",
                   "feel lost", "so lost", "feel empty", "feel numb")
# The same question with any of the words people point back with. "does it ever stop" was in the
# list above and "does that stop" was not, so the second half of the same thought fell out of the
# chat into a search hedge; "that" and "this" point at the grief exactly as "it" does. Anchored to
# the end of the line, because "does that stop the leak" names a thing of its own and keeps its
# own answer.
GRIEF_POINTS_BACK = re.compile(
    r"^(?:so\s+|and\s+|but\s+)?"
    r"(?:does|did|will|would|is|was|am"
    r"|when\s+(?:does|did|will|would|is|am)"
    r"|how\s+long\s+(?:does|did|will|would|is|am))"
    # "will i ever stop hurting" is the same question as "will it ever stop": after a death the
    # person talking about their own pain is asking about the grief, and "the pain" is the same.
    r"\s+(?:it|that|this|i|things|the\s+pain|the\s+ache|this\s+pain)\b"
    r"(?:\s+(?:ever|always|still|really|actually|never|not))?\s*"
    r"(?:stop|end|ease|pass|fade|last|go\s+away|let\s+up|get\s+easier|get\s+better|"
    r"feel\s+better|feel\s+normal|feel\s+like\s+myself|"
    r"hurt|hurts|hurting|normal|better|easier|forever)"
    # "when will it stop hurting" left "hurting" on the end and fell out of the chat into a
    # search hedge; the word after the verb is the same question, not a different one.
    r"(?:\s+(?:hurting|aching))?\b"
    r"(?:\s+(?:so|then|eventually|now|at\s+some\s+point|after\s+a\s+while|for\s+ever"
    r"|some\s*day))?\s*[.?!]*$",
    re.I)
# The house and the person's things: the other way people talk about a loss.
GRIEF_OBJECTS = ("without her", "without him", "without them", "her things", "his things",
                 "the house", "the flat", "her room", "his room", "empty house", "quiet house")
# The other way people keep talking about the same person: a pronoun back to them. "i cant stop
# thinking about him", "i have to sort out her house and i cant face it". A line that asks for a
# plan about them or their things ("how do i cancel her phone contract") is a question with its
# own answer, and a happy line naming someone else ("my daughter loves her new bike") is not
# about the person who died, so the mood has to be other than positive.
REFERS_TO_THEM = re.compile(r"\b(?:him|her|them|his|hers|their)\b")
# A question that asks what to do: a plan about them is not a condolence.
IDEA_ASK = re.compile(r"^(?:what|how|where|which)\b.*\b(?:do|does|could|should|can|would|shall)\b")
# The topics under which a line is still the bereavement rather than a subject of its own. A
# cough, a bad back, a boiler or a job brings its own answer; a pet is the one subject that can
# itself be the loss ("we lost my nan in the summer" and then "we had to put the dog down").
THREAD_TOPICS = frozenset(("feelings", "grief", "loss", "small-talk", "sleep", "pets"))

# The second week of a bereavement is mostly this: the person is still expected. "i keep
# expecting to see her", "i still look for him at the bus stop", "the house feels empty". None
# of these says "grief", and they are the lines that fell out of the thread into a stock note.
# Absence is about a person, so the verb has to point at one: "i keep looking for my keys",
# "i still wait for the bus" and "i keep expecting the council to reply" are an ordinary
# bereavement thread carrying on with an ordinary line, and they keep their own answer.
# Only read inside a thread (it sits after `continues`), so the same words outside one are
# untouched anyway.
THEM = (r"(?:him|her|them|he|she|they|hes|shes|theyre|his|hers|their|mum|mom|mam|dad|father|"
        r"mother|nan|gran|granny|nana|grandad|granddad|grandma|grandpa|son|daughter|brother|"
        r"sister|wife|husband|partner|baby|friend|uncle|aunt|cousin|dog|cat|puppy|kitten)")
ABSENCE = re.compile(
    r"\b(?:keep|keeps|kept|still)\s+(?:expecting|expect|looking|look|waiting|wait|listening|"
    r"listen|hearing|hear|seeing|see|reaching|reach|thinking|think|setting|set|saving|saved)\b"
    r"[^.]{0,30}\b" + THEM + r"\b|"
    r"\b(?:habit|instinct|reflex|second nature)\b|"
    r"\b(?:house|home|flat|kitchen|bed|place|room)\s+(?:feels|felt|is|was)\s+"
    r"(?:so\s+|too\s+|very\s+)?(?:empty|quiet|silent|big|strange|wrong)\b|"
    r"\b(?:set|laid|lay|set out|lay out)\s+(?:the\s+|a\s+)?table for (?:two|three|four)\b|"
    r"\bfor(?:got|get|gets|getting)\b[^.]{0,30}\b(?:gone|dead|not here|isnt here|wouldnt be"
    r" here)\b|"
    r"\b(?:hear|hearing|smell|smelling)\s+(?:his|her|their)\b")
# What the reading counts, why each shape is only ever a loss, and the pool for each one. Every
# pattern names somebody (`THEM` carries the person or the animal) and the "without" shape needs
# the owner in it: "the house is so quiet without the kids" is an empty nest, and the routine and
# the place at the table are a strange thing to say to that. Bare "i keep thinking about my mum"
# is left out on purpose - the mum may be alive and simply far away.
STILL_LAYING = re.compile(
    r"\b(?:set|setting|lay|laying|laid)\s+(?:out\s+)?(?:the\s+|a\s+)?table\s+for\s+"
    r"(?:two|three|four)\b|"
    r"\b(?:lay|laying|laid|set|setting|put|putting)\s+(?:out\s+)?(?:\w+\s+){0,3}"
    r"(?:place|places|bowl|bowls|plate|plates|cup|cups)\b(?:\s+\w+){0,4}\s+for\s+(?:two|three)\b|"
    r"\b(?:keep|keeps|still)\s+(?:\w+\s+){0,2}(?:set|setting|put|putting|lay|laying|buy|buying)\b"
    r"[^.]{0,24}\b(?:bowls?|places?|plates?|cups?|mugs?|glasses|food|biscuits?|treats?)\b|"
    # The second one still gets made, poured, cooked: "i still make two cups of tea", "i still
    # buy two of everything", "i still dish up two plates". The verb is what makes it a routine
    # and the count is what makes it theirs, so both are in the shape, and the count has to come
    # within a few words of the verb rather than anywhere in the line.
    r"\b(?:keep|keeps|kept|still)\s+(?:\w+\s+){0,3}"
    r"(?:make|making|made|pour|pouring|poured|buy|buying|bought|cook|cooking|cooked|dish|"
    r"dishing|fill|filling|cut|cutting|butter|buttering|boil|boiling)\b"
    r"[^.]{0,24}\b(?:two|three|both)\b|"
    r"\b(?:two|three|both)\s+(?:cups?|mugs?|teas?|coffees?|plates?|bowls?|portions?|"
    r"helpings?|sandwiches?|glasses)\b[^.]{0,24}\b(?:for (?:us|two|both of us)|still)\b", re.I)
STILL_WITHOUT = re.compile(
    r"\b(?:empty|quiet|silent)\s+without\s+(?:my|our|him|her|them)\b", re.I)
STILL_CRYING = re.compile(
    r"\b(?:cry|cries|cried|crying)\s+(?:over|about|for)\s+(?:my|our|him|her|them)\b|"
    r"\b(?:cant|cannot|can'?t)\s+stop\s+(?:cry\w*|think\w*)\s+(?:about|over|for)\s+"
    r"(?:my|our|him|her|them)\b", re.I)
# The habit where the person is not named, because the thing that carried them is: "i keep looking
# up when the door goes", "i still reach for the phone", "i keep setting two places". Only ever
# asked inside a thread or a line that already has the death, since the door and the phone are in
# everybody's day.
STILL_AT_THE_DOOR = re.compile(
    r"\b(?:keep|keeps|kept|still)\s+(?:\w+\s+){0,2}"
    r"(?:looking|look|listening|listen|waiting|wait|reaching|reach|expecting|expect|setting|set)\b"
    r"[^.]{0,30}\b(?:door|doorbell|phone|key|keys|ring(?:ing)?|places?|table|seat)\b", re.I)
STILL_SEEING = re.compile(
    r"\b(?:keep|keeps|kept|still)\s+(?:\w+\s+){0,3}"
    r"(?:expect\w*|looking|look|waiting|wait|listening|listen|hearing|hear|seeing|see|"
    r"reaching|reach|saving|saved)\b[^.]{0,30}\b" + THEM + r"\b", re.I)
THE_ROUTINE_REPLIES = (
    "The hands keep the routine for a while - the second bowl, the place at the table. That is "
    "muscle memory, not madness, and you can let it go when it stops being a comfort.",
    "Laying it out for them is the routine still running. Put it away when you want to, not "
    "because anyone says it is time.",
    "Half of it is the small jobs your hands still do. There is nothing wrong with any of them.",
)
# The jobs that were theirs, still being done. The routine pool names the table, so it is wrong for
# a phone or a coffee, and these are the three that hold whichever job the line names.
THE_JOBS_FOR_THEM_REPLIES = (
    "The jobs you did for them do not stop on the day. The hands keep going for a while, and that "
    "is not a sign you are stuck.",
    "Some part of the day is still theirs. Doing the job anyway is how a lot of people get "
    "through the first year, and there is nothing wrong with it.",
    "A habit that was for them takes a while to notice as a habit. Do it, or stop, whichever "
    "comes first - neither is a betrayal of them.",
)
THE_HOUSE_REPLIES = (
    "An empty house is the hardest part of the day to fill. It does get less loud, and the quiet "
    "is not a measure of anything.",
    "The quiet is the whole of it, and it is worst in the evenings. Nobody gets to tell you there "
    "is a timetable for that.",
    "A house with one fewer person in it feels wrong before it feels like anything else. Be slow "
    "with it.",
)
THE_CANNOT_STOP_REPLIES = (
    "Crying over them, or thinking of nothing else, is the plainest way of saying they mattered. "
    "It comes in waves - let it, and be kind to yourself after.",
    "If that is all you can do today, it is enough for today. It eases, and it keeps its own "
    "timetable.",
    "That is grief doing its work, and it is not something to get on top of. I am here for as "
    "much of it as you want to say.",
)
# The reflex that named them: the eye, the ear, the reaching for the phone.
THE_HABIT_REPLIES = (
    "Seeing them out of the corner of your eye is the habit outliving them. Most people who have "
    "lost someone do it for months, and it says nothing about how you are.",
    "Seeing them, hearing them, waiting for them - it is a habit that had years to set. It fades "
    "slowly, and it is not a sign you are losing them.",
    "That reflex is the shape of them still in your day. There is nothing to do about it, and it "
    "goes with how much of the day they were in.",
)


def _an_ask_in_the_line(line):
    """True when the line puts a question, whatever its punctuation.

    `QUESTION` is the grief shapes ("is it normal", "why do i"); this is the ordinary ask that no
    pool here answers: "should i still set a place for him", "do i keep the bowls out".
    """
    if ASK_AT_START.match(line):
        return True
    return bool(re.search(r"\b(?:should|shall|do|does|did|can|could|would|will|is|are|was|were|"
                          r"why|how|what|when|where|who)\s+(?:i|we|you|he|she|they|it)\b", line))


# The routine done for them and for nobody else: "i still make his coffee", "i still call her
# phone", "i still put his bowl down", "i still say goodnight to him", "i still buy his beer".
# The verb is what makes it a job the hands still do and the person named after it is who it is
# still done for, so both are in the shape and the person has to come within a few words of the
# verb. The feeling verbs stay out on purpose - "i still love her" and "i still miss him" are the
# loss itself, and "i still owe him 200" is a debt, not a habit - and so does a bare "he"/"she",
# because "i still say he was a good man" is a verdict, not a routine.
STILL_DOING_FOR_THEM = re.compile(
    r"\b(?:keep|keeps|kept|still)\s+(?:\w+\s+){0,3}"
    r"(?:make|making|pour|pouring|buy|buying|cook|cooking|dish|dishing|lay|laying|set|setting|"
    r"put|putting|save|saving|leave|leaving|wash|washing|iron|ironing|fold|folding|"
    r"call|calling|text|texting|ring|ringing|phone|phoning|greet|greeting|kiss|kissing|"
    r"say|saying|check|checking|fill|filling|clean|cleaning|top|topping|pay|paying|paid|"
    r"do|doing)\b"
    r"[^.]{0,30}\b(?:his|her|their|him|them|hers|theirs)\b", re.I)


HABIT_PATTERNS = ((STILL_LAYING, THE_ROUTINE_REPLIES),
                  (STILL_DOING_FOR_THEM, THE_JOBS_FOR_THEM_REPLIES),
                  (STILL_WITHOUT, THE_HOUSE_REPLIES),
                  (STILL_CRYING, THE_CANNOT_STOP_REPLIES),
                  (STILL_SEEING, THE_HABIT_REPLIES),
                  (STILL_AT_THE_DOOR, THE_HABIT_REPLIES))
def _still_here(line, words):
    """The pool for the habit a line reports, or None.

    It is asked only once a death is read in the line, because the habit alone is not a death:
    "i still see my dad every sunday" and "the office feels so empty without my team" are
    somebody alive and away, and the loss pool says the person is gone. `ABSENCE` stays where it
    is for the same reason - inside a thread that already has the death. What this adds is the
    line that carries both: "my dad died in march and i keep reaching for the phone to ring
    him" is a death said again with the part they actually want to talk about, and the condolence
    is the stock answer STYLE.md rules out.
    """
    if "?" in line or QUESTION.search(line):
        return None
    # A question with a "?" is gone before this reading sees the line (the caller hands it the
    # words), so "should i still set a place for him" has to be caught by its shape.
    if _an_ask_in_the_line(line):
        return None
    if MISS_NOT.search(line) or _a_thing_of_theirs(words):
        return None
    if _only_the_proceedings(" ".join(words), words):
        return None
    for pattern, pool in HABIT_PATTERNS:
        if pattern.search(line):
            return pool
    return None


def _a_habit_in(line):
    """True when the line reports one of the habits the pools above answer, whatever the pool."""
    return any(pattern.search(line) for pattern, _pool in HABIT_PATTERNS)


AFTER_REPLIES = (
    "I'm here. Take your time with it — tell me what it has been like, if you want to.",
    "There's no rush to talk about it. I'm here when you want to say more.",
    "That sounds heavy to be carrying. I'm listening, however much or little you want to say.",
    "I'm glad you said that out loud. Say as much or as little as you like — I'm here.",
)
# How people describe it after the first line, when they are still on the same subject. Kept to
# the words that can only be about a loss: they count wherever they are in the line.
GRIEF_FEELINGS = frozenset((
    "miss", "missing", "cry", "crying", "cried", "tears", "numb", "sad", "lonely", "angry",
    "guilty", "guilt", "grief", "grieving", "mourning", "funeral", "ashes", "grave",
    "anniversary", "reminded", "memories", "remember", "shock", "shocked", "unreal",
    "bereaved", "gutted",
    # "it comes in waves" is how people say the grief keeps coming back, so the word holds the
    # thread on its own; it is only ever read inside a chat that already has a death.
    "waves",
    # The shape grief takes in the months after: a dream about them, their voice on the phone,
    # their smell in a coat, a photo. These words only turn up in this chat on a line that is
    # still about the person, so they count wherever they are in the line. A bare "see", "hear"
    # or "expect" does not: "i expect the death certificate in the post" is admin, not grief.
    "dream", "dreams", "dreamt", "dreamed", "dreaming", "voice", "smell", "doorbell",
    "photo", "photos",
))
# And the words that are about grief only when the line is about the person themselves:
# "i still can't sleep", "some days i can't get out of bed", "it was really hard". A line that
# names its own subject keeps its own answer, so "the pub was dead quiet last night" and
# "my boss is hard work at the moment" are not bereavement.
GRIEF_SELF = frozenset((
    "hard", "hardest", "tough", "rough", "bad", "awful", "horrible", "heavy", "hurts", "hurt",
    "sleep", "sleeping", "sleepless", "slept", "bed", "nights", "night", "wake", "wakes",
    "woke", "tired", "exhausted", "weird", "strange", "stuck", "empty", "quiet", "silent",
    "silence", "coping", "cope", "eating", "appetite", "mornings", "morning",
    # How a family member not managing is described ("my mum isnt coping") - see FAMILY below,
    # these only count when the line names one.
    "struggling", "struggle", "breaking", "broken", "withdrawn", "shut", "drinking",
    "unbearable",
))
# A family member who is not coping is the same story from one step out: after "my dad died",
# "my mum isnt coping" is not a new subject. The words above decide the second half; this is
# the first - a named family member, never "my boss" or "my friend".
FAMILY = frozenset(("mum", "mom", "mam", "dad", "mother", "father", "brother", "sister",
                    "son", "daughter", "wife", "husband", "partner", "nan", "nana", "grandad",
                    "grandma", "grandpa", "granny", "gran", "uncle", "aunt", "auntie", "cousin",
                    "family", "parents", "kids", "children", "baby"))
# The openers that make a line about the person talking, rather than about the pub or the boss.
SELF_OPENERS = (
    "i ", "i'", "im ", "ime ", "ive ", "id ", "some days", "some nights", "most days",
    "most nights", "every night", "at night", "lately", "these days", "it ", "it's ", "its ",
    "that ", "that's ", "this ", "they ", "we ", "we're ",
)
# "my" says something about the person only when it is a part of their own life.
SELF_NOUNS = frozenset(("sleep", "night", "nights", "mornings", "mood", "head", "appetite",
                        "grief", "sadness", "coping"))
# "this morning", "last night" say when, not how they are: they are not a grief cue.
WHEN_WORDS = frozenset(("this", "last", "next", "tomorrow", "yesterday", "every", "one", "that"))
# A question that points back at what was just said, without naming anything.
GRIEF_REFERRING = ("is that normal", "is it normal", "is this normal", "does it get better",
                   "will it get better", "does it ever stop", "when does it stop",
                   "how long does it last", "does it get easier", "will it always",
                   "feel lost", "so lost", "feel empty", "feel numb")
# The same question with any of the words people point back with. "does it ever stop" was in the
# list above and "does that stop" was not, so the second half of the same thought fell out of the
# chat into a search hedge; "that" and "this" point at the grief exactly as "it" does. Anchored to
# the end of the line, because "does that stop the leak" names a thing of its own and keeps its
# own answer.
GRIEF_POINTS_BACK = re.compile(
    r"^(?:so\s+|and\s+|but\s+)?"
    r"(?:does|did|will|would|is|was|am"
    r"|when\s+(?:does|did|will|would|is|am)"
    r"|how\s+long\s+(?:does|did|will|would|is|am))"
    # "will i ever stop hurting" is the same question as "will it ever stop": after a death the
    # person talking about their own pain is asking about the grief, and "the pain" is the same.
    r"\s+(?:it|that|this|i|things|the\s+pain|the\s+ache|this\s+pain)\b"
    r"(?:\s+(?:ever|always|still|really|actually|never|not))?\s*"
    r"(?:stop|end|ease|pass|fade|last|go\s+away|let\s+up|get\s+easier|get\s+better|"
    r"feel\s+better|feel\s+normal|feel\s+like\s+myself|"
    r"hurt|hurts|hurting|normal|better|easier|forever)"
    # "when will it stop hurting" left "hurting" on the end and fell out of the chat into a
    # search hedge; the word after the verb is the same question, not a different one.
    r"(?:\s+(?:hurting|aching))?\b"
    r"(?:\s+(?:so|then|eventually|now|at\s+some\s+point|after\s+a\s+while|for\s+ever"
    r"|some\s*day))?\s*[.?!]*$",
    re.I)
# The house and the person's things: the other way people talk about a loss.
GRIEF_OBJECTS = ("without her", "without him", "without them", "her things", "his things",
                 "the house", "the flat", "her room", "his room", "empty house", "quiet house")
# The other way people keep talking about the same person: a pronoun back to them. "i cant stop
# thinking about him", "i have to sort out her house and i cant face it". A line that asks for a
# plan about them or their things ("how do i cancel her phone contract") is a question with its
# own answer, and a happy line naming someone else ("my daughter loves her new bike") is not
# about the person who died, so the mood has to be other than positive.
REFERS_TO_THEM = re.compile(r"\b(?:him|her|them|his|hers|their)\b")
# A question that asks what to do: a plan about them is not a condolence.
IDEA_ASK = re.compile(r"^(?:what|how|where|which)\b.*\b(?:do|does|could|should|can|would|shall)\b")
# The topics under which a line is still the bereavement rather than a subject of its own. A
# cough, a bad back, a boiler or a job brings its own answer; a pet is the one subject that can
# itself be the loss ("we lost my nan in the summer" and then "we had to put the dog down").
THREAD_TOPICS = frozenset(("feelings", "grief", "loss", "small-talk", "sleep", "pets"))

# The second week of a bereavement is mostly this: the person is still expected. "i keep
# expecting to see her", "i still look for him at the bus stop", "the house feels empty". None
# of these says "grief", and they are the lines that fell out of the thread into a stock note.
# Absence is about a person, so the verb has to point at one: "i keep looking for my keys",
# "i still wait for the bus" and "i keep expecting the council to reply" are an ordinary
# bereavement thread carrying on with an ordinary line, and they keep their own answer.
# Only read inside a thread (it sits after `continues`), so the same words outside one are
# untouched anyway.
THEM = (r"(?:him|her|them|he|she|they|hes|shes|theyre|his|hers|their|mum|mom|mam|dad|father|"
        r"mother|nan|gran|granny|nana|grandad|granddad|grandma|grandpa|son|daughter|brother|"
        r"sister|wife|husband|partner|baby|friend|uncle|aunt|cousin|dog|cat|puppy|kitten)")
ABSENCE = re.compile(
    r"\b(?:keep|keeps|kept|still)\s+(?:expecting|expect|looking|look|waiting|wait|listening|"
    r"listen|hearing|hear|seeing|see|reaching|reach|thinking|think|setting|set|saving|saved)\b"
    r"[^.]{0,30}\b" + THEM + r"\b|"
    r"\b(?:habit|instinct|reflex|second nature)\b|"
    r"\b(?:house|home|flat|kitchen|bed|place|room)\s+(?:feels|felt|is|was)\s+"
    r"(?:so\s+|too\s+|very\s+)?(?:empty|quiet|silent|big|strange|wrong)\b|"
    r"\b(?:set|laid|lay|set out|lay out)\s+(?:the\s+|a\s+)?table for (?:two|three|four)\b|"
    r"\bfor(?:got|get|gets|getting)\b[^.]{0,30}\b(?:gone|dead|not here|isnt here|wouldnt be"
    r" here)\b|"
    r"\b(?:hear|hearing|smell|smelling)\s+(?:his|her|their)\b")
# What the reading counts, and why each shape is only ever a loss. Every alternative names
# somebody (`THEM` carries the person or the animal). The "without" shape needs the owner in it:
# "the house is so quiet without the kids" is an empty nest, and the routine, the muscle memory
# and the place at the table are a strange thing to say to that. Bare "i keep thinking about my
# mum" is left out on purpose - the mum may be alive and simply far away, and this pool says the
# person is gone.
# The line that argues it was handled right: "it was the right thing to do", "we did the kindest
# thing", "he had a good life", "at least she is not in pain now". Nothing in it is sad, and the
# echo says it back - "It was the right thing to do - noted." is the coldest line the store has.
# Only read inside a bereavement thread: the composer asks `continues` before it comes here, and a
# question ("was it the right thing to do") keeps its own answer.
REASSURING = re.compile(
    r"\b(?:the right (?:thing|call|decision)|did the (?:right|kindest|best) thing|for the best|"
    r"the kindest thing|no other choice|"
    r"(?:he|she|they) had a good (?:life|innings)|would(?:'ve| have) wanted|at peace|"
    r"no more pain|not in pain|out of (?:his|her|their) pain|no longer suffering)\b")

# "i feel at peace now" is the person saying where they have got to, not arguing that the death was
# handled right. It is a line about their own state, and the store already answers it well ("Most
# people find the same, and it does get easier. Be gentle with yourself"), so a listening line in
# its place assumes they want to talk when they have just said something good. The same words about
# the person who died - "he's at peace now", "mum is at peace" - are the claim, and stay.
PEACE_IS_MINE = re.compile(
    r"\b(?:i|we)(?:'?m|'?ve|\s+am|\s+are|\s+have|\s+feel|\s+feeling|\s+felt)?\s+"
    r"(?:now\s+|so\s+|really\s+|quite\s+|a bit\s+|more\s+)*at (?:peace|rest)\b")
# A person who has died is often spoken of by the day and by the absence, not by a death word:
# "my mum would have been 70 this week", "the first christmas without her". Nothing else in those
# lines says anyone died, so the reading has to take the tense and the missing person instead.
# "would have been 70" only makes sense of someone who is not going to be 70, and the age is
# wanted, so "it would have been nice" is left alone.
WOULD_HAVE = re.compile(
    r"\bwould\s+(?:have|ve)\s+(?:been|turned)\s+(?:\d{1,3}\b|twenty|thirty|forty|fifty|"
    r"sixty|seventy|eighty|ninety)")
# The occasions people mark when someone is missing from them.
OCCASION = re.compile(
    r"\b(birthday|birthdays|xmas|christmas|anniversary|anniversaries|mothers day|mothering "
    r"sunday|fathers day|new year|new years|easter|the day itself|her day|his day|their day)\b")
WITHOUT = re.compile(r"\bwithout\s+(?:my|our|his|her|them|him|mum|dad)\b")
# A tradition the day used to have. It is what makes "her birthday" a question rather than a
# mention: "we always did a lunch for her birthday, i don't know what to do instead".
TRADITION = re.compile(
    r"\b(we always|always did|always had|every year|used to|tradition|same as always|instead|"
    r"what do i do|dont know what to do|don t know what to do|nothing feels right)\b")
# Asking permission to keep the thing going, once the chat is about a loss: "should i still do a
# cake". It is the same question as the tradition, asked from the other side, and it takes both
# halves: the word "still" (which is a filler word for phrase matching, so it is read off the line
# as typed) and the thing the day is made of. "what should i cook for dinner" is a cooking question
# even in a bereavement chat, and so is "should i still go to work tomorrow" a work one.
STILL_KEEP = re.compile(
    r"\b(?:should i|shall i|do you think i should|am i supposed to|is it (?:ok|okay|alright|"
    r"wrong) (?:to|if i))\s+still\s+"
    r"(?:do|have|bake|cook|make|put|keep|send|host|hang|light|set out|visit)\b"
    # the same question without the word "still": "is it ok to put the tree up this year".
    r"|\bis it (?:ok|okay|alright|wrong) to (?:put up|put|do|keep|hang) (?:the|a|our) "
    r"(?:tree|decorations|lights|wreath|cake|cards?)\b")
# What the day is made of: food, the tree, the cards, the grave. One of these has to be in the line
# for the question about keeping it going to be about the day.
DAY_THING = re.compile(
    r"\b(cakes?|tree|dinner|lunch|meal|roast|turkey|cards?|presents?|gifts?|decorations|wreath|"
    r"flowers|party|tradition|toast|grave|christmas|xmas|birthday|anniversary)\b")
# The day named straight after the question: "what should i do for our anniversary now". It is
# the tradition question without the tradition, so it needs the day word as well.
DAY_QUESTION = re.compile(r"\b(?:what|how)\s+(?:should|do|can|could)\s+(?:i|we)\s+"
                          r"(?:do|mark|handle|spend|keep)\b")
KEEPS = (TRADITION, STILL_KEEP)

FUNERAL = re.compile(r"\b(funeral|memorial|service|viewing|burial|cremation)\b")

# `FUNERAL` stops at the singular, and the parts of the day are asked about in the plural as often:
# "do kids go to funerals", "what hymns at funerals". Read only where a part of the day is named
# too, so it never decides on its own that a line is about a death.
FUNERALS = re.compile(r"\b(?:funerals|memorials|burials|cremations|crematoria|crematorium|"
                      r"graveside|gravesides)\b")

# How to tell a child, not what to say to a grieving adult. "how do i tell my 5 year old that
# grandma died" got "Keep it plain and warm: I'm so sorry", which is the line for the person who
# had the loss, and the same happened to "my dog died how do i tell my child". The words for a
# child are a different answer (the plain words a small child can hold, and who stays the same),
# and it belongs to the family entries, so this composer stands aside.
TELL_CHILD = re.compile(
    r"\b(?:tell|telling|explain|explaining|talk to|talking to)\b([\w\s]{0,24}?)"
    r"\b(?:child|children|kid|kids|son|daughter|toddler|boy|girl|baby|teenager)\b")
YEAR_OLD = re.compile(r"\d+\s*(?:year|yr)s?[\s-]*old")


def _telling_a_child(tight):
    """True when the line asks how to explain a death to a child of the user's.

    "i have to tell my boss my dad died" is not this: the person being told is not a child.
    Neither is "how do i tell people about my son", where the child is who died rather than who
    has to be told.
    """
    found = TELL_CHILD.search(tight)
    if not found:
        # "how do i tell my 5 year old" carries no child word from the list at all
        return bool(YEAR_OLD.search(tight) and re.search(r"\b(?:tell|explain)\w*\b", tight))
    between = found.group(1) or ""
    if re.search(r"\b(?:about|of|people|everyone|office|work|boss)\b", between):
        return False
    return True


PRONOUN = frozenset(("he", "she", "they", "him", "her", "them"))


def marks_a_day(text, known=False):
    """True when the line is about a day that matters and someone who is not there for it.

    Strong evidence, enough on its own: the age someone would have been ("my mum would have been
    70 this week", "he would have been 60 next month"), and an occasion with the missing person
    in it ("the first christmas without my dad"). An age in the conditional is only a person if
    the line names one, so "the cake would have been 20 minutes" is left alone.
    Weak evidence, only enough once the chat is already about a loss (`known`): the tradition
    ("we always did a lunch for her birthday, what do i do instead") and the question about
    keeping it going ("should i still do a cake"). A line on its own that says only "my sisters
    birthday is coming up and i dont know what to do" is a question about a present, and must not
    be read as a bereavement.
    """
    if isinstance(text, str):
        raw = " ".join(_plain(text))
        words = raw.split()
    else:
        words = list(text or ())
        raw = " ".join(words)
    tight = " ".join(word for word in words if word not in FILLERS)
    subject = _has_person(words) or bool(set(words) & PRONOUN)
    if WOULD_HAVE.search(tight):
        return subject
    # The tradition needs the day in it too, or "we always have pasta on fridays, what should i
    # cook tonight" inside a bereavement chat becomes a plan for the anniversary.
    # A named day or a named person, not the bare pronoun: "what could i do with her on a
    # sunday", asked about a lonely nan, is company for the nan and not the anniversary.
    day_named = bool(DAY_THING.search(raw) or OCCASION.search(tight) or _has_person(words))
    if known and ((TRADITION.search(tight) and day_named)
                  or (STILL_KEEP.search(raw) and DAY_THING.search(raw))
                  or (DAY_QUESTION.search(tight) and day_named)):
        # the day is already the subject of the chat, so a question about keeping it going is
        # the same question: "should i still do a cake" after "mum would have turned 80".
        return True
    if not OCCASION.search(tight):
        return False
    if WITHOUT.search(tight):
        return True
    return False


# A day that matters is not always a question. "my mum would have been 70 this week" and "it's my
# first christmas without her" are said to the bot, not asked at it, and the answer to a line like
# that is company, not a plan; main's own tests say so. Advice is for the line that asks.
ASKS_ABOUT_THE_DAY = re.compile(
    r"\b(what (?:do|should|can|could) i|what (?:do|would) we|should i|shall i|how do i|how can i|"
    # "we" as well as "i": a day belongs to the family, and the commonest shape is the question
    # asked for two people - "we always did a lunch for her birthday, should we still do it".
    r"should we|shall we|do we|would we|can we|could we|how do we|"
    r"any ideas?|what to do|instead|nothing feels right|dont know|don t know|do you think|"
    r"is it (?:ok|okay|alright|wrong)|am i supposed to)\b")


def asks_what_to_do(text):
    """True when the line about the day also asks what to do about it.

    "we always did a lunch for her birthday, i don't know what to do instead" asks; "my mum would
    have been 70 this week" does not, however much the day is on their mind.
    """
    if isinstance(text, str):
        raw = " ".join(_plain(text))
        words = raw.split()
    else:
        words = list(text or ())
        raw = " ".join(words)
    if "?" in str(text or ""):
        return True
    return bool(ASKS_ABOUT_THE_DAY.search(raw))


def _plain(text):
    """The line as words: lower case, apostrophes and punctuation flattened."""
    text = str(text or "").lower().replace("\u2019", "'")
    return [word.strip(".,!?;:\"'()") for word in text.split()]


def _about_them(line):
    """True when the line is about the person talking, not about the pub or the boss."""
    text = (line or "").strip()
    if text.startswith(SELF_OPENERS):
        return True
    words = text.split()
    return len(words) > 1 and words[0] == "my" and words[1].strip(",.!?") in SELF_NOUNS


def _about_family(words):
    """True when the line names a family member as its subject: "my mum isnt coping"."""
    return len(words) > 1 and words[0] in ("my", "his", "her", "their", "our") and any(
        word.strip(",.!?") in FAMILY for word in words[1:3])


def _own_state(words):
    """The person's own state: "can't sleep", "so tired", "the mornings are hard" - but not
    "i lost my keys this morning"."""
    for index, word in enumerate(words):
        if word in GRIEF_SELF and not (index and words[index - 1] in WHEN_WORDS):
            return True
    return False


# The time of day as the subject of the line, rather than the "this morning" that only says
# when: "the mornings are hard", "the nights are worst", "the weekends are tough". `_about_them`
# needs an "i" or a "my" to read a line as the person's own, and these have neither, so the
# second week of a bereavement fell through to the stock note. The noun has to open the line and
# the state word has to follow, so "the pub was dead quiet last night" keeps its own answer.
TIME_OF_DAY = re.compile(r"^\s*the\s+(?:mornings?|nights?|evenings?|weekends?|days?)\b")
# The words that can follow a state word and still leave it describing the person: "i feel bad
# still", "it was really hard today". Any other word after it ("bad cough", "hard work", "a heavy
# cold") makes the state word describe that thing, which means the line brought a subject.
STATE_TAIL = frozenset((
    "and", "but", "or", "so", "too", "all", "at", "in", "on", "to", "with", "when", "since",
    "because", "today", "tonight", "now", "still", "lately", "already", "again", "yet", "just",
    "quite", "very", "really", "bit", "as", "like", "about", "for", "of", "that", "it", "i",
    "im", "i'm", "this", "these", "some", "most", "every", "days", "day", "weeks", "week",
    "months", "time", "times", "though", "honestly", "actually", "sometimes", "if", "than",
    "without", "after", "before", "anymore", "any", "more", "less", "enough",
))


def _state_describes_them(words):
    """True when a state word in the line describes the person, not a thing they named.

    "i feel so bad", "it was really hard", "the mornings are hard" are the person's own state.
    "i have a bad cough", "my boss is hard work" are a subject with an answer of its own: the
    state word there only describes that thing, so the line is not the bereavement.
    """
    for index, word in enumerate(words):
        if word in GRIEF_SELF and (index + 1 >= len(words) or words[index + 1] in STATE_TAIL):
            return True
    return False


# Topics that say nothing about what a line is about. A question about a length or a quantity
# is read as "maths and numbers" whatever it asks ("how long does this go on for", "how long
# does probate take"), so the topic cannot be what tells a subject question from a grief one.
# What a bereavement does to the person's own body: "is it normal to not eat", "why do i keep
# forgetting to eat", "is it normal to drink more", "is it normal to lose weight". The reader
# gives these a health subject, so `_names_a_subject` stands the pool down and the line falls to
# a recipe entry, an entry about forgetting, or the honest hedge - and "You haven't told me what
# your dad eats" is nobody's answer. The word alone is not enough: "how much water should i
# drink" is about water, so the shape has to be the person.
BODY_STATE = frozenset((
    "eat", "eats", "ate", "eating", "appetite", "hungry", "food", "meal", "meals",
    "drink", "drinks", "drank", "drinking", "alcohol", "wine",
    "sleep", "sleeps", "sleeping", "slept", "weight", "cry", "crying",
))
THEMSELVES = re.compile(r"\b(?:i|im|i'm|me|my|myself)\b")
# "is it normal to ..." has no "i" in it and is still the speaker's own body being asked about.
ASK_NORMAL = re.compile(r"^is (?:it|that) normal\b")
# "is it normal to feel sick all the time" two turns after a death: whatever topic the reader
# gives it (a body word reads as health), the thing being asked about is how the loss is
# treating them. The adjective is not the point, so this shape does not look for one.
NORMAL_TO_FEEL = re.compile(r"^is (?:it|that|this) (?:normal|ok|okay|common|usual) to feel\b")
QUANTITY = re.compile(r"\bhow (?:much|many)\b")


def _the_body_is_theirs(tight, words):
    """True when the line asks what the loss is doing to the person's own body or appetite."""
    if QUANTITY.search(tight):
        return False
    if NORMAL_TO_FEEL.match(tight):
        return True
    if not (THEMSELVES.search(tight) or ASK_NORMAL.match(tight)):
        return False
    words = tuple(words)
    for index, word in enumerate(words):
        if word in BODY_STATE and (index + 1 >= len(words) or words[index + 1] in STATE_TAIL):
            return True
    return False


MEASURE_TOPICS = frozenset(("maths-and-numbers",))


# The body words with a practical answer of their own. Crying is left out on purpose: there is no
# entry for it, and the company here beats a shrug at "i keep crying".
BODY_ANSWER = frozenset((
    "eat", "eats", "ate", "eating", "appetite", "hungry", "food", "meal", "meals",
    "drink", "drinks", "drank", "drinking", "thirsty",
    "sleep", "sleeps", "sleeping", "slept", "wake", "wakes", "waking", "woke", "awake",
    "insomnia", "tired", "weight",
))


def _a_body_with_its_own_answer(tight, words):
    """True when the line reports the person's own body in a way that has a practical answer.

    "i cant sleep", "i keep waking at 3", "i have no appetite", "i cant face food": sleep and
    food have entries, and a turn into a bereavement they are the better answer. "how much water
    should i drink" is a quantity asked about water, so it does not count.
    """
    if QUANTITY.search(tight):
        return False
    if not THEMSELVES.search(tight):
        return False
    return any(word in BODY_ANSWER for word in words)


def _names_a_subject(topics):
    """True when the reader gave the line a subject of its own to be answered.

    `_own_subject` with the measure topics taken out: "how long does this go on for" is read as
    maths and numbers, and a length asked about the loss is still the loss.
    """
    if not isinstance(topics, (list, tuple)) or not topics:
        return False
    return bool(set(topics) - THREAD_TOPICS - MEASURE_TOPICS)


def _own_subject(topics):
    """True when the reader gave the line a subject that has an answer of its own.

    A cough, a bad back, a broken boiler, a lost job: the line names something the bot knows
    about, and a bereavement chat does not stop it being that. Only the topics that are the
    bereavement itself, or fillers, leave the thread where it is.
    """
    if not isinstance(topics, (list, tuple)) or not topics:
        return False
    return bool(set(topics) - THREAD_TOPICS)


# What keeps the next line about the person they miss: a word for them, or the words a person
# uses about someone gone ("i keep expecting her to call", "every year", "that song"). Any other
# question is a question, and the pools below answer it.
STILL_ABOUT_THEM = re.compile(
    r"\b(?:he|she|him|her|they|them|his|hers|their|theirs)\b"
    r"|\b(?:keep|keeps|kept|still|always|expect|expecting|used to|every (?:day|night|year)|"
    r"last (?:week|month|year)|anniversary|birthday|that (?:day|night|song|photo|place))\b", re.I)


# The two halves of "a detail about them, not the missing said again": a line that opens on the
# person, and one that carries none of the words for the missing itself.
ABOUT_THEM_OPENS = re.compile(
    r"^\s*(?:(?:and|but|so|yeah|yes|oh|well|then|also|plus|too|god|honestly)\b[\s,]*)*"
    r"(?:he|she|they|him|her|his|their|them|theyre|he's|she's|he'd|she'd|they'd|hes|shes)\b",
    re.I)
MISSING_SAID_AGAIN = re.compile(
    r"\b(?:miss|missed|misses|missing|cry|cried|crying|tears|sad|sadness|ache|aches|aching|"
    r"keep|keeps|kept|still|always|expect|expecting|hard|hardest|heavy|hurts?)\b", re.I)


def _hands_over_a_detail(tight):
    """Whether the line adds something new about the person rather than the missing said again.

    "i miss my nan" then "she taught me to bake" is a friend's cue: the detail is the thing to
    answer, and the store's own line - "She taught you to bake. That is a lot to carry on top of
    how you feel" - beats the company pool, which would say the same warm thing to any line at
    all. "i miss my mum" then "i keep expecting her to call" is the missing again with nothing
    new in it, and that one is the pool's. "she died two years ago" opens on her as well, and the
    death modules have their own answer for it, so the thread stands aside for that too.
    """
    return bool(ABOUT_THEM_OPENS.match(tight) and not MISSING_SAID_AGAIN.search(tight))


def _thread_pool(memory):
    """The pool behind the bot's last line, when that line was the what-to-say advice.

    "what do i say to my friend" then "its a workmate, i barely know him" is the same question
    about what to say, not the person's own bereavement, so the advice continues.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return None
    last = str(turns[-1].get("bot") or "")
    if not last:
        return None
    if last in SAY_REPLIES:
        return SAY_REPLIES
    if last in MISS_REPLIES:
        # "i miss my mum" was met with company, so the next line ("she died two years ago",
        # "she taught me to bake") is the same person, not a fresh chat.
        return MISS_REPLIES
    return None


# People type the contraction and often drop the apostrophe, so the copula is spelled out before
# any phrase touches the line: "my mum's dying", "my dads dying" and "she's palliative" are all
# "my mum is dying". The possessive looks the same ("the plants dying"), and that is fine: a
# plant is not a person, so the reader turns it down a line later anyway.
_CONTRACTED = re.compile(
    r"\b(\w+)['\u2019]?s\s+(?=(?:dying|terminal|terminally|palliative|"
    r"in\s+(?:a\s+)?hospice)\b)")
# Only the words that can be dying are respelled: "works in a hospice" and "his dying wish" are
# not contractions, and a list of what can die is short.
# The stand-ins for a person count as naming one: "she's dying" is somebody's nan, and the line
# usually follows a turn that said who. "it" is left out - "it's dying" is a phone or a plant.
_PEOPLE_PRONOUNS = frozenset(("she", "he", "they", "someone", "anyone", "everyone", "nobody",
                              "who"))
# "dying to see it" is wanting, not dying: a pronoun line that would otherwise be a death.
DYING_TO = re.compile(r"\bdying\s+to\b|\bdying\s+for\b|\bdying\s+of\s+(?:boredom|"
                      r"embarrassment|laughter|curiosity|shame|excitement|a\s+cold)\b")
# A word ending in "s" is a contraction unless it is the copula itself: "is dying" is not "i is
# dying", and the "s" of "his" and "this" belongs to nothing.
_NOT_A_CONTRACTION = frozenset(("is", "was", "has", "does", "this", "its", "his", "hers", "ours",
                                "theirs"))
_CAN_BE_DYING = frozenset(PEOPLE) | _PEOPLE_PRONOUNS


def _spoken(text):
    """The line with the contractions spelled out, so "my mum's dying" matches "my mum is dying".

    People write the contraction and often drop the apostrophe - "my mum's dying", "my dads
    dying", "my nan's in a hospice" - and both readers wanted the copula spelled out, so those
    lines were answered as if nobody were dying.
    """
    def spell(match):
        base = match.group(1).lower()
        if base in _CAN_BE_DYING and base + "s" not in _NOT_A_CONTRACTION:
            return match.group(1) + " is "
        return match.group(0)

    return _CONTRACTED.sub(spell, text)


def _tight(text):
    """The line without filler words, for phrase matching: "what do I even say" is "what do
    I say"."""
    return " ".join(word for word in _plain(text) if word not in FILLERS)


def _their_thing_after(clean, start):
    """True when the word after the person is one of their things rather than a place or a time.

    "i lost my carer badge", "i lost my nurse notes", "i lost my mums keys": the person is the
    qualifier and the thing after them is what went missing.
    """
    rest = clean[start:].split()
    return bool(rest) and rest[0] in (OBJECTS | THEIRS)


def _another_person(words, clean):
    """True when the line names a person who is not the role word a thing has borrowed.

    "the drain cleaner died" is a blocked pipe; "my mum thinks the drain cleaner died" is still
    about the pipe, but "my mum died and the drain cleaner is in the cupboard" has a person in it
    and keeps the death reading.
    """
    if set(words) & (HUMAN_WORDS - TWO_WAY_ROLES):
        return True
    return bool(ROLE_PHRASE.search(clean))


def _a_thing_of_theirs(words):
    """True when a person word is only the qualifier of one of their things.

    "my carer badge", "my nurse notes", "my carer allowance letter": the thing after the person
    is what the line is about, and the person is whose it is. Read as a person, a badge that has
    stopped got a condolence.
    """
    for index, word in enumerate(words):
        if index + 1 >= len(words) or words[index + 1] not in (OBJECTS | THEIRS):
            continue
        stem = word[:-2] if word.endswith("'s") else (word[:-1] if word.endswith("s") else word)
        if word not in PEOPLE and stem not in PEOPLE:
            continue
        others = [other for place, other in enumerate(words)
                  if place != index
                  and (other in PEOPLE
                       or (len(other) > 2 and other.endswith("s") and other[:-1] in PEOPLE))]
        if not others:
            return True
    return False


def _a_role_phrase(clean):
    """True when the line names a person a death can be said about with two words.

    "my home help died" and "my night carer died" name nobody word by word: "help" is the commonest
    verb in the language and "night" is a time of day. The whole phrase is the person, so it is read
    as one.
    """
    return bool(ROLE_PHRASE.search(clean))


def _has_person(words):
    """True when a person or a pet is named, in any form people type it.

    "my mum's birthday", "my mums anniversary" and "my sisters wedding" are the same person as
    "my mum", "my sister": a possessive and a plural are how the line says whose day it is, and
    without them the day went unread.
    """
    for word in words:
        if word in PEOPLE:
            return True
        if word.endswith("'s") and word[:-2] in PEOPLE:
            return True
        if word.endswith("s") and word[:-1] in PEOPLE:
            return True
    for first, second in PEOPLE_PHRASES:
        for index, word in enumerate(words[:-1]):
            if word == first and words[index + 1] == second:
                return True
    # A role said in two ordinary words ("my home help", "my night carer") names a person the
    # token list cannot hold, because each word on its own is something else.
    return _a_role_phrase(" ".join(words))


def _object_died(words):
    """True when the thing before "died"/"dead" is an object, not a person."""
    for index, word in enumerate(words):
        if word in ("died", "dies", "dead", "dying") and index:
            if words[index - 1] in OBJECTS:
                return True
            if index > 1 and words[index - 2] in OBJECTS and words[index - 1] in ("is", "was",
                                                                                "has", "had"):
                return True
    return False


# A thing put down and not found is not a knock-back: the line wants help finding it, not
# sympathy. `lost_a_thing` below already tells a lost thing from a death, but it counts a job
# and a match as things lost too, and those are disappointments. This reads only what can be
# picked up and put down, so the answer is where to look.
FINDABLE = (r"keys?|key ?ring|phone|mobile|wallet|purse|handbag|backpack|rucksack|bag|passport|"
            r"tickets?|(?:(?:bank|debit|credit|travel|id|library) )?cards?|glasses|specs|"
            r"headphones|earphones|earbuds|airpods|charger|laptop|tablet|mouse|umbrella|"
            r"coat|jacket|scarf|glove|hat|shoes|trainers|book|file|documents?|parcel|package|"
            r"remote|toy|teddy")
LOST_THING_TO_FIND = re.compile(
    r"\b(?:i|we|ive|i've|he|she|they|you|my [a-z]+|our [a-z]+)\s+"
    r"(?:have\s+|had\s+)?(?:lost|losing)\s+"
    r"(?:my|our|his|her|their|your|the|a|an)\s+(?:" + FINDABLE + r")\b")
# The same thing said the other way round: "i cant find my keys", "where are my keys",
# "have you seen my passport". A thing that is being looked for is a thing to help find.
CANT_FIND_THING = re.compile(
    r"\b(?:(?:i|we|he|she|they)\s+)?(?:can ?not|can't|cant|couldn't|could not)\s+"
    r"(?:find|see)\s+"
    r"(?:my|our|his|her|their|the|a|an)\s+(?:" + FINDABLE + r")\b")
LEFT_THING = re.compile(
    r"\b(?:i|we|he|she|they)(?:\s+think i)?\s+(?:left|forgot|lost track of)\s+"
    r"(?:my|our|his|her|their|the|a|an)\s+(?:" + FINDABLE + r")\b")
# The place forgotten rather than the thing: "i forgot where i put my phone", "i cant remember
# where i left my keys", "no idea where i put my wallet". LEFT_THING reads "forgot my phone" and
# nothing here read "forgot where", so the commonest way of saying it got the nod. The thing still
# has to be named with its own or the definite article, so "why do i keep forgetting where i put
# things" stays the memory-science question it was.
REMEMBER_NOT_WHERE = re.compile(
    r"\b(?:forgot|forget|can ?not remember|can't remember|cant remember|do not remember|"
    r"don't remember|dont remember|no idea|not sure|no clue)\s+where\s+(?:i|we|he|she|they)\s+"
    r"(?:have\s+|had\s+)?(?:put|left|laid|placed)\s+"
    r"(?:my|our|his|her|their|the|a|an)\s+(?:" + FINDABLE + r")\b")
# "forgot where i parked" is deliberately not this shape: a car park needs a level and a row of
# bays, and the retrace pool talks about a coat pocket, which is the wrong place to send somebody
# looking. That line answers as well as it did before, which is not at all - a gap of its own.
KEEP_LOSING_THING = re.compile(
    r"\b(?:i|we)\s+keep\s+(?:losing|misplacing)\s+(?:my|our|the)\s+(?:" + FINDABLE + r")\b")
# The same habit with the thing in front: "my glasses keep going missing", "my phone keeps
# disappearing", "the remote keeps vanishing". The thing that keeps going missing is the subject
# of the sentence, so every pattern above missed it: "i keep losing my keys" gets the one-home
# answer, while "my glasses keep going missing" was answered by the empathy pool ("That sounds
# rough. If you want, I can help you think through what to do next.") and "my phone keeps going
# missing" with "What would make today a bit easier?". A thing that comes back lost again and
# again is the same habit, whichever way round it is said.
KEPT_GOING_MISSING = re.compile(
    r"\b(?:my|our|his|her|their|the)\s+(?:" + FINDABLE + r")\s+"
    r"(?:keeps?|kept)\s+(?:going\s+missing|disappearing|vanishing|getting\s+lost|walking)\b")
GONE_THING = re.compile(
    r"\b(?:my|our|his|her|their)\s+(?:" + FINDABLE + r")\s+(?:is|are|has gone|have gone)\s+"
    r"(?:gone|missing|nowhere)\b")
WHERE_IS_THING = re.compile(
    r"\b(?:where(?:'s| is| are)|where has|where have|where did i (?:put|leave)|"
    r"where have i put|have you seen|has anyone seen|"
    r"did you see|any sign of)\s+(?:my|our|his|her|their|the|a|an)\s+(?:" + FINDABLE + r")\b")
# "Where did I put it" is the frame that says a thing is mislaid, and it says it whatever the
# thing is. The list above can only hold the things people lose most, and the ones it could not
# guess were answered with the honest hedge: "where did i put the sudocrem", "where did i put my
# driving licence", "where did i put the calpol", "where did i put the baby wipes" all got "I'm
# not sure about that one, sorry - I'd rather not guess. A quick search online will get you a
# solid answer", which is a shrug at somebody who has lost something in their own house. A line
# that asks where they put a thing wants somewhere to look, and the answer to that does not
# depend on what the thing is. Only the putting and the leaving, which nothing else is asked
# with: "where is my X" and "where are my X" keep to the list, because a refund, an order and a
# train are all asked that way and each has its own answer.
WHERE_I_PUT_IT = re.compile(
    r"\bwhere\s+(?:did|have|has|had)\s+i\s+(?:put|leave)\b"
    r"(?:\s+(?:my|our|his|her|their|the|a|an))?")
# The frame is the asking, but not everything the asking can be about is a thing that was put
# down. A person is not - "where did i put my son" - and neither is an errand or an abstraction -
# "where did i put the bins out", "where did i leave my job". The people words are the ones the
# condolence already reads, so a thing named the way a person is ("the baby wipes", "my son's
# coat") is saved by the word after it: only a person standing alone is a person.
NOT_MISLAID = PEOPLE | frozenset((
    "job", "jobs", "shift", "shifts", "foot", "feet", "finger", "fingers", "hand", "hands",
    "mind", "way", "place", "bins", "bin", "rubbish", "washing", "recycling", "ironing",
    "football", "weight", "effort", "record", "case"))
NOT_A_THING_NEXT = frozenset((
    "out", "away", "back", "down", "off", "and", "but", "or", "so", "then", "i", "it", "was",
    "were", "is", "are", "that", "this", "for", "to", "in", "on", "at", "with", "from", "again",
    "somewhere", "before", "after", "today", "yesterday", "last", "now", "though", "honestly",
    "probably", "right", "anyway"))


def _where_i_put_it(said):
    """True when the line asks where a thing was put, people and errands aside."""
    for match in WHERE_I_PUT_IT.finditer(said):
        rest = said[match.end():].split()
        if rest and rest[0] in NOT_MISLAID:
            if len(rest) == 1 or rest[1] in NOT_A_THING_NEXT:
                continue
        return True
    return False
# The same ask with the verb left out, which is how people type when they are in a hurry:
# "where my keys", "so where my wallet". The whole line has to be the ask and it has to end at
# the thing, so a statement that carries on keeps its own reading: "the place where my phone
# charger goes", "where my keys go" and "this is where my wallet lives" are not this.
WHERE_IS_THING_BARE = re.compile(
    r"^\s*(?:so |ok |okay |and |but )?where\s+(?:my|our|his|her|their|the|a|an)\s+(?:"
    + FINDABLE + r")\s*$")


# Shut out of the place they live or the car: "i lost my keys and im locked out". The search
# can wait; the way back in is what the first line has to be about. Digital accounts are not
# this reading — "locked out of my email" wants a password reset, not a locksmith.
LOCKED_OUT = re.compile(
    r"\b(?:locked out|lock(?:ed)? (?:me|myself|us) out|shut out of (?:the|my|our) "
    r"(?:flat|house|home|car|van)|keys? (?:are |is )?(?:still )?(?:in|inside) (?:the|my) "
    r"(?:door|lock|ignition)|lock(?:ed)? (?:my|the) keys? (?:in|inside) (?:the|my) "
    r"(?:car|van|house|flat|boot|door)|no spare key)\b")
NOT_A_DOOR = re.compile(
    r"\b(?:account|email|e-mail|bank|banking|online|app|website|site|password|login|log in|"
    r"profile|facebook|instagram|twitter|whatsapp|icloud|google|netflix|laptop|computer|"
    r"phone|tablet|xbox|playstation|steam|psn|system|server|admin|router|wifi|"
    r"cat|dog|puppy|kitten|pet|bird|hen|chicken|rabbit|hamster)\b")
CAR_LOCK_OUT = re.compile(r"\b(?:car|van|boot|ignition|keys? (?:are |is )?in the (?:car|van))\b")


def locked_out(text):
    """True when they are shut out of their home or car: "im locked out, i lost my keys".

    Kept apart from `lost_thing_to_find` because the answer is different in kind: a search is
    no use to someone standing in the street, and the way back in is the urgent half. A digital
    account ("locked out of my email") and the cat being shut out are not this.
    """
    said = " ".join(words_of(text))
    if not LOCKED_OUT.search(said):
        return False
    return not NOT_A_DOOR.search(said)


def locked_out_of_the_car(text):
    """True when the thing they are shut out of is the car, which has its own way in."""
    return bool(CAR_LOCK_OUT.search(" ".join(words_of(text))))


def _readable(text):
    """The line with the engine's repairs in it: "wheres my keys" reads as "where is my keys".

    The patterns below match a line as it was typed, and people type "wheres", "weres",
    "whers" and "where r" far more often than "where's". The understanding engine already knows
    every one of those spellings, so the repairs are taken from it rather than listed again here:
    a table of misspellings in a composer is a second copy of the engine's, and it lags it.
    """
    try:
        read = normalise(str(text or ""))
    except Exception:
        return str(text or "")
    return " ".join(read.get("norm") or []) or str(text or "")


def lost_thing_to_find(text):
    """True when the line is something mislaid and findable: "i lost my keys", "ive lost my bag".

    Kept separate from `lost_a_thing`, which also reads a job, a match and a train of thought:
    those are disappointments and idioms, and the answer to them is not "retrace your steps".
    """
    said = " ".join(words_of(_readable(text)))
    return bool(LOST_THING_TO_FIND.search(said) or CANT_FIND_THING.search(said)
                or WHERE_IS_THING.search(said) or _where_i_put_it(said)
                or WHERE_IS_THING_BARE.search(said)
                or LEFT_THING.search(said)
                or GONE_THING.search(said) or KEEP_LOSING_THING.search(said)
                or REMEMBER_NOT_WHERE.search(said))


FOUND_WHAT_WAS_LOST = re.compile(
    r"\b(?:found (?:them|it|ours|his|hers|mine|my [a-z]+)|(?:it|they|he|she|my [a-z]+) "
    r"(?:has |have )?(?:turned up|was in|were in|was under|were under|was behind|were behind|"
    r"was on|were on|was at|were at|showed up))\b")


def keeps_losing_thing(text):
    """True when the same thing goes missing again and again: "i keep losing my keys".

    The answer to that is a habit rather than a search, so it gets its own pool.
    """
    said = " ".join(words_of(text))
    return bool(KEEP_LOSING_THING.search(said) or KEPT_GOING_MISSING.search(said))


def found_what_was_lost(text):
    """True when the line says a thing that was being looked for has turned up.

    Only worth a reply of its own when the last line was that search, so the caller checks
    `lost_thing_to_find(`the previous line`)` as well.
    """
    return bool(FOUND_WHAT_WAS_LOST.search(" ".join(words_of(text))))


def lost_in_a_place(text):
    """True when a person was lost in an everyday place: "i lost my son at the park".

    It reads the person the line lost, then looks for a place after it. Kept public because the
    modules that answer a lost child or a lost parent need the same reading, and because it is
    the guard that keeps the sympathy away from a panic.
    """
    clean = " ".join(words_of(text))
    for pattern, group in LOST_FORMS:
        found = pattern.search(clean)
        if not found or found.group(group) not in DEATHABLE:
            continue
        place = LOST_IN_A_PLACE.search(clean, found.end())
        return bool(place) and place.group(1) in PLACES
    return False


# "losing my baby weight" is not a baby being mourned: the relation word is a description of the
# pounds, not a person. Only the things people shed after a birth are here.
SHED = re.compile(r"\s+(?:weight|fat|pounds|stone|belly|blubber|tummy|tummies|inches|waist|"
                       r"middle|kilos?|kilograms?)\b")


def _shed_after(clean, start):
    """True when what follows the relation is the weight rather than the person."""
    return bool(SHED.match(clean, start))


# A loss that is feared, hoped against or only imagined is not one that has happened. "i hope i
# never lose my dad" and "if i lose my mum i dont know what ill do" are the fear, and the
# bereavement pool answered them "i'm sorry, that's a real loss" - a claim about the world that
# was never made. The frame is in front of the verb, so it is read there, before the verb is.
# Only the forms that look forward take it: "i never got to say goodbye, i lost my dad" keeps its
# loss, because "lost" is not a form the frame can precede.
FEARED_NOT_YET = re.compile(
    r"\b(?:dont|don't|do not|doesnt|doesn't|never|hope|hoping|hoped|scared|afraid|worried|"
    r"worry|worrying|dread|dreading|if|unless|before|hate|bear)\b"
    r"[^.!?]{0,24}?\b(?:lose|loses|losing)\b", re.I)


def _feared_not_done(clean, start):
    """True when the verb a match begins at sits behind a frame that keeps it in the future.

    The frame ends on the verb itself, so a match that starts before the frame's end is the verb
    the frame is about: "i dont want to lose my mum" matches at "lose", four letters before the
    frame ends.
    """
    for frame in FEARED_NOT_YET.finditer(clean):
        if frame.start() <= start and 4 <= frame.end() - start <= 6:
            return True
    return False


def _lost_in_a_place_after(clean, start):
    """True when an everyday place follows the person at *start*.

    "losing my son at the park" is a mislaid child, not a bereavement, and the -ing form and the
    noun form have to use the same list of places as "i lost my son at the park".
    """
    place = LOST_IN_A_PLACE.search(clean, start)
    return bool(place) and place.group(1) in PLACES


def _can_die(clean):
    """What can die in this line. A mouse in a line about a computer cannot: "i lost my mouse"
    is a bad afternoon with a mouse mat, not a bereavement, and it wants the search for a lost
    thing rather than sympathy. "my pet mouse died" keeps the animal reading.
    """
    if is_a_machine_word(clean):
        return DEATHABLE - MACHINE_ANIMALS
    return DEATHABLE


def lost_a_thing(text):
    """True when the line says something was lost and it is not a person or a pet.

    A follow-up to sympathy is read as still part of the loss, and a negative word is often all
    that is in the line ("it was really hard"). "i lost my keys", "i lost my phone" and "i lost
    the plot a bit today" are also negative and are not the loss: they belong to the modules
    that know about keys and phones, or to no module at all.
    """
    words = words_of(text)
    clean = " ".join(words)
    deathable = _can_die(clean)
    if re.search(r"\blost\s+it\b", clean):
        return True  # "i lost it with the kids": a bad moment, not a death
    for pattern, group in LOST_FORMS:
        found = pattern.search(clean)
        if not found:
            continue
        thing = found.group(group)
        if thing in deathable or thing in LOST_SELF:
            return False
        return True
    if re.search(r"\b(?:lost|losing|lose)\s+the\s+([a-z]+)", clean):
        return True
    return False


def words_of(text):
    """The line's words, lower case and without punctuation: the reading both functions use."""
    return _plain(text)


# A pet that brought prey in and has since died is still a loss: "my cat died yesterday and he
# used to bring dead birds in" is the condolence, not a collar. The death is read on the line with
# the prey phrase taken out, so "dead birds" cannot be the death being counted.
PET_DIED = re.compile(r"\b(?:died|dying|dead|dies|passed away|passed on|put down|"
                      r"put to sleep|euthanised|euthanized|pts)\b")


def _brought_in_prey(clean, words):
    """True when a living pet has brought something dead in, which is not a loss."""
    if not (_has_pet(words) and PREY.search(clean) and HUNTING.search(clean)):
        return False
    return not PET_DIED.search(PREY.sub(" ", clean))


# "and it died", "it just died", "it died last night": the death word with a pronoun for its
# subject. On its own that is not enough - "it died" after "my nan" could be anything - so the
# line also has to name one of the things that stop working, and then the question is about the
# thing.
IT_DIED = re.compile(r"\bit\s+(?:just\s+|has\s+|had\s+|finally\s+)?(?:died|dies)\b")


def _a_pronoun_is_what_died(words, clean):
    """True when "it" is what died and the line names a thing that could be the "it".

    "i bought a phone for my daughter and it died" is a fault; "my dad died last week" is not,
    and neither is a family noun with a pronoun that names no thing ("my nan ... then it died"
    about a car still names the car, so the thing decides, not the pronoun).
    """
    if not IT_DIED.search(clean):
        return False
    return any(word in THINGS for word in words)


def a_thing_stopped(text, words=None):
    """True when the death word in the line is about a thing, not a person or a pet.

    A phone, a laptop, a boiler and a car all "die", and "dead" is also an intensifier: "my
    trainers are dead comfy", "the pub was dead quiet", "im dead tired". Read on its own the
    word says a bereavement, which is why the composer's doubt floor ("is that normal" after "my
    laptop battery dies fast") has to be able to ask this before it reaches for the condolence.
    Only the death words are read here, so a line that says a person died stays a death however
    much of the rest of it is about a thing: "my nan died and the boiler went the same week" is
    still their nan.
    """
    if words is None:
        words = words_of(text)
    if not words:
        return False
    if _object_died(words):
        # "my laptop is dead", "the battery dies by lunchtime": the word before the death word
        # is the thing that stopped.
        return True
    return any(word == "dead" and _dead_is_not_a_death(words, place)
               for place, word in enumerate(words))


def reads_as_loss(text, words=None, a_pet=False):
    """True when the line is about a death or a loss of a person or a pet.

    `a_pet` says the line names an animal the store already holds ("rex died"): a name is not in
    any of the word lists, so without it a death said by name alone is read as small talk.
    """
    if words is None:
        words = words_of(text)
    if not words:
        return False
    deathable = _can_die(" ".join(words))
    clean = " ".join(words)
    if any(phrase in clean for phrase in LAUGHING):
        return False
    if lost_in_a_place(clean):
        return False
    if WOULD_HAVE_BEEN.search(clean) and (_has_person(words) or _unnamed_person(words, clean)):
        # "my mum would have been 70 this week": the day is the loss.
        return True
    if _brought_in_prey(clean, words):
        # "my cat keeps bringing dead birds in": the cat is fine and the bird is its dinner.
        return False
    if _a_thing_of_theirs(words):
        # "my carer badge died", "my nurse notes went missing": the badge and the notes are the
        # subject and the person is whose they are, so the line is about the thing. Read before
        # the death words, because a thing of theirs said with "died" is a thing that has
        # stopped.
        return False
    if _a_pronoun_is_what_died(words, clean):
        # "i bought a phone for my daughter and it died": a person is in the line, but the subject
        # of "died" is "it", and the thing a phone is beats the person whose phone it is. Read
        # before the person test, because a parent in the sentence is what made this a condolence.
        return False
    person = _has_person(words) or _unnamed_person(words, clean)
    if _the_end_is_near(clean, words):
        # "the doctor said theres nothing more they can do", "theyve stopped mums chemo", "my dad
        # has weeks left": the treatment has run out, which is how most people say somebody is
        # dying now, and the grief starts here rather than at the funeral. Asked before the
        # proceedings, because those lines say "can" and have no person in them, which is the
        # shape of "how do i arrange a funeral" - and the proceedings reading sent the give-up to
        # the shrug ("I'm listening - say more if it helps").
        return True
    if _only_the_proceedings(clean, words):
        # "funeral costs": a question about the proceedings is the knowledge base's, not a
        # condolence.
        return False
    if person and THING_ROLE.search(clean) and not _another_person(words, clean):
        # "my vacuum cleaner died": the appliance has stopped, and sympathy is the wrong answer.
        person = False
    if PLAIN.search(clean):
        return True
    if _passed_alone(clean, person) or _passed_on(clean, person) or _death_noun(clean, words, person):
        return True
    if WAKE.search(clean):
        return True
    if _buried_person(clean, words, person):
        return True
    if SYMPATHY.search(clean) and CARD_WORD.search(clean):
        return True
    if TOOK.search(clean):
        return True
    # A killing is a death when a person is in the line, and only then.
    if (KILLED.search(clean) and not _killed_in_a_story(clean)
            and (person or set(words) & set(PASSED_ON_SUBJECT))):
        return True
    if _put_down(clean, words):
        return True
    if (person and STILL_CRY.search(clean) and not OTHER_WEEPS.search(clean)
            and not THEIR_TEARS_IN_A_CLAUSE.search(clean)):
        # "is it normal to still cry about my mum three years later" names no death but is grief.
        # A line where it is someone else crying ("my son keeps crying", "the baby keeps crying
        # at night") is about them, not a bereavement, and passed here before this guard.
        return True
    if DEATH_AS_A_THING.search(clean) and not NOT_A_DEATH.search(clean):
        # "a death is never good news, is it" is about death itself, not about the rate of it.
        # The same three readings that keep a false death out of the noun form keep it out here:
        # the speaker's own death ("my death anxiety is bad"), a thing that died ("the death of
        # my laptop", "my houseplants death") and a death on a screen ("his death in the film").
        if OWN_WORRY.search(clean) or THING_DEATH.search(clean) or PET_DEATH.search(clean):
            return False
        if FICTION.search(clean) and not person:
            return False
        if DEATH_COMPOUND.search(clean):
            # "his death doula was lovely": the word after "death" is the thing being named.
            return False
        owner = DEATH_OF_OWNER.search(clean)
        if owner and owner.group(1).split()[-1] in THINGS and not person:
            # "the death of our old boiler": the last word of the owner phrase is the thing.
            return False
        return True
    lost_the = LOST_THE.search(clean)
    if (lost_the and lost_the.group(1) in deathable and lost_the.group(1) not in PET_WORDS
            and not LOST_THE_FOUND.search(clean)):
        # "we lost the baby at twelve weeks" is a bereavement; "we lost the baby in the
        # supermarket" is a minute of panic, and "we lost the dog" could be either.
        return True
    for pattern, group in LOST_FORMS:
        found = pattern.search(clean)
        if found and found.group(group) in deathable:
            # "lost her job" is a job; "lost my dad" is a dad; "we lost nan" is nan.
            if _their_thing_after(clean, found.end()):
                continue  # "i lost my carer badge": the badge went missing, not the carer
            # "losing my son at the park" is ten bad minutes and "how do i lose the baby
            # weight" is the pounds, in the present tense as well as the past.
            if (_lost_in_a_place_after(clean, found.end())
                    or _shed_after(clean, found.end())
                    or _feared_not_done(clean, found.start())):
                continue
            return True
    for pattern in (LOSS_OF, NEWS_OF):
        found = pattern.search(clean)
        if found and found.group(1) in deathable:
            # "the loss of my mum" is the loss; "the loss of my appetite" names nothing that can
            # die, and "the news of my dad hit me hard" is the death in the hit, not in the noun.
            if pattern is LOSS_OF and _lost_in_a_place_after(clean, found.end()):
                continue
            return True
    losing = LOSING.search(clean)
    if (losing and losing.group(1) in deathable
            and (losing.group(1) in CLOSE or LOSS_GRIEF_CUE.search(clean))
            and not _shed_after(clean, losing.end())
            and not _feared_not_done(clean, losing.start())
            and not _lost_in_a_place_after(clean, losing.end())):
        # "losing my wife has hit me hard" is a bereavement; "losing my son at the park" is ten
        # bad minutes and "im losing my friend" has no grief cue at all.
        return True
    if marks_a_day(clean):
        # "my mum would have been 70 this week", "the first christmas without my dad": the death
        # is in the tense and in the missing person, not in a death word.
        return True
    if CONDITIONAL_TAIL.search(clean) and not (set(words) & HUMAN_WORDS):
        # A conditional is a chore, not a death: "our fish are going to die if we dont clean the
        # tank" is about the tank, and "the plants will die unless i water them" is about water.
        return False
    # "she's dying" names no noun: the person was named a turn earlier, and the pronoun stands
    # for them. Only she and he and they: "it is dying" is a plant.
    a_pronoun = bool(set(words_of(_spoken(clean))) & _PEOPLE_PRONOUNS)
    if (ANTICIPATED.search(_spoken(clean)) and (person or a_pronoun) and not _object_died(words)
            and not (_WORKING_WITH_THE_DYING.search(clean)
                     and not _SAID_DYING.search(clean))):
        # "my wife is on palliative care", "my nan is in a hospice", "she has weeks to live":
        # the death is ahead and the grief is already here. Read as a loss so the composer
        # answers it, and answered by the DYING_REPLIES pool because nobody has died yet.
        return True
    if (not person and a_pronoun and DYING_NOW.search(_spoken(clean))
            and not _object_died(words) and not DYING_TO.search(clean)):
        # "she's dying", "he is terminal": the line names nobody, and the turn before named who.
        # Only where no noun carries the person, so a line that says who is read as it was.
        return True
    if GOING_TO_DIE.search(clean) and (person or a_pronoun) and not _object_died(words):
        # "my nan is going to die" and "my mum is going to die soon" are the loss now, not later:
        # the future tense is how people say it while it is happening. A feeling that follows
        # ("going to die of embarrassment") is the idiom, and LAUGHING has already returned.
        return True
    if (a_pet and (DYING.search(clean) or DIED.search(clean))
            and not _object_died(words) and not NOT_A_DEATH.search(clean)):
        return True
    if _accident_death(clean):
        # "my cat was run over last night": no death word in the line, and the cat card that
        # knows about cats answers a cat that is still in the room.
        return True
    if (DYING.search(clean) or DIED.search(clean)) and person and not _object_died(words):
        for index, word in enumerate(words):
            if word == "dead" and _dead_is_not_a_death(words, index):
                # "dead birds": this "dead" describes the word after it, so it is not a death.
                # "my cat died yesterday and he used to bring dead birds in" still is one.
                continue
            if word in ("died", "dies", "dead", "dying"):
                return True
    return False


def _accident_death(clean):
    """True when the line says someone of ours died in an accident, without the word "died".

    The passive is what makes it a death rather than a mishap of the speaker's doing: "my cat was
    run over last night" is a loss, "i ran over a cat" is not the same line from the wheel. The
    loss also has to be of ours - an owner and a person or a pet - so "the shed was knocked down"
    and "we were run over by the rush" stay ordinary lines, and a line that says the person is
    fine ("was run over but hes ok", "she's in hospital") is a fright, not a bereavement.
    """
    if not MISADVENTURE.search(clean) or SURVIVED.search(clean):
        return False
    if NOT_A_DEATH.search(clean):
        return False  # "death row", "the death of the high street": the word is not a loss
    if VERB_OBJECT.search(clean):
        return False  # "my daughter drowned her phone", not the daughter
    victim = _owned_deathable(clean)
    if not victim:
        return False
    if victim not in PET_WORDS and KNOCKED_BY.search(clean) and not DEATH_SAID.search(clean):
        return False  # "my dad got knocked over by a bike" is a broken arm until it says otherwise
    return True


def _owned_deathable(clean):
    """The person or pet an accident happened to, or None.

    Every word after the owner is tried, so the adjective in "our old dog" and "my little
    brother" does not stand in for the one that can die.
    """
    for owner in OWNED.finditer(clean):
        for word in owner.group(1).split():
            if word in DEATHABLE:
                return word
    return None


def _passed_on(clean, person):
    """True when "passed on" is a death, not a declined offer.

    "my nan passed on in march" and "she passed on last year" are bereavements; "i passed on the
    message to my boss", "we passed on the house" and "i passed on dessert" are not. A person or
    pet has to be the subject, and the word after "on" must not be an object.
    """
    if PASSED_ON not in clean:
        return False
    before, _, after = clean.partition(PASSED_ON)
    if not person and not set(before.split()[-3:]) & PASSED_ON_SUBJECT:
        return False
    rest = after.split()
    if not rest:
        return True
    if rest[0] not in PASSED_ON_OBJECT:
        return True
    if rest[0] == "the" and len(rest) > 1 and (rest[1] in MONTHS or rest[1][:1].isdigit()
                                               or rest[1] in ("1st", "2nd", "3rd")):
        return True
    return False


def _passed_alone(clean, person):
    """True when "passed" on its own is a death, not a test, a deadline or a plate.

    "my grandad passed in jan", "my dad passed last year" and "she passed suddenly" are
    bereavements; "i passed my test", "the deadline passed" and "he passed me the salt" are not.
    A person or pet has to be the subject, and what follows has to be a date, a time or nothing.
    """
    words = clean.split()
    if PASSED_ALONE not in words:
        return False
    for i, word in enumerate(words):
        if word != PASSED_ALONE:
            continue
        if not person and not set(words[max(0, i - 4):i]) & PASSED_ON_SUBJECT:
            continue
        if set(words[:i]) & PASSED_A_RESULT:
            # "my mum got her results and she passed": something to pass was named, so the word
            # is the achievement and not the death.
            continue
        rest = words[i + 1:]
        if not rest:
            return True
        head = rest[0]
        nxt = rest[1] if len(rest) > 1 else ""
        if head in PASSED_ALONE_TAIL:
            continue
        if head in ("in", "on", "at", "last", "this", "that", "back"):
            if head == "at":
                if nxt in PASSED_TIME:
                    return True
                continue
            if nxt in PASSED_DATE or nxt in PASSED_TIME or nxt[:1].isdigit():
                return True
            continue
        if head == "it" and nxt in ("was", "is", "has", "had"):
            # "my nan passed, it was expected" - the next clause, not an object.
            return True
        if head in PASSED_ON_OBJECT or head in PASSED_ALONE_HANDED or head in PASSED_ALONE_NOUN:
            continue
        return True
    return False


def _death_noun(clean, words, person):
    """True when the word "death" in this line is someone's death, not a word doing another job.

    An owner makes it a particular death ("his death", "my mums death"), so it counts on its own.
    A bare article needs a bereavement cue as well, which is the general rule that also protects
    the proper nouns nobody listed ("the death star lego set", "death valley", "the death
    toll"). Fiction, the speaker's own death and object deaths are all read out.
    """
    if not DEATH_NOUN.search(clean) or NOT_A_DEATH.search(clean):
        return False
    if THING_DEATH.search(clean) or PET_DEATH.search(clean):
        return False
    if DEATH_COMPOUND.search(clean):
        return False
    if FICTION.search(clean) and not person:
        return False
    if OWN_WORRY.search(clean):
        return False
    if person:
        return True
    owned = OWN_DEATH.search(clean)
    if owned:
        owner = clean[owned.start():owned.end()].split()[0]
        if owner in ("my", "his", "her", "their", "your", "our"):
            return True
        # "dads death" is a death; "hamlets death" is a play, so the owner has to be a person.
        stem = owner.rstrip("s").rstrip("'")
        if stem in PEOPLE or owner in PEOPLE:
            return True
    return bool(DEATH_CUE.search(clean))



def _unnamed_person(words, clean):
    """True only when "someone"/"people" is a real death: the line asks what to say about it.

    "what do i say when someone dies" is the same question as "what do i say to my friend", so
    the ask has to be there. A show or a film dying is never anyone's loss.
    """
    if not any(word in UNNAMED for word in words):
        return False
    if any(word in MEDIA for word in words):
        return False
    return bool(ASK_WORDS.search(clean))


# The passive voice puts the thing that is buried in front of the verb, so "how deep should a
# fence post be buried" and "when should the ashes be buried" look the same to the verb alone.
# With one of these in front, only a person or a pet in the line makes it a funeral.
PASSIVE_AUX = ("be", "being", "been", "get", "gets", "getting", "got", "is", "was", "are",
               "were", "will", "to")
# What can be the subject of a passive burial and still mean a funeral: the person is in the line
# or the thing being buried is what is left of them.
REMAINS = ("ashes", "body", "bodies", "coffin", "coffins", "casket", "caskets", "urn", "urns",
           "remains", "grave", "graves", "plot", "plots")

# What a line buries when nobody has died: a fence post, a cable, a bag of rubbish. The passive
# "be buried" needs this list because the verb is the same either way - "he was buried in France"
# and "the post was buried two foot down" differ only in their subject.
BURIABLE = ("post", "posts", "fence", "fences", "fencing", "panel", "panels", "gate", "gates",
            "cable", "cables", "wire", "wires", "pipe", "pipes", "hose", "hosepipe", "drain",
            "drains", "treasure", "bulb", "bulbs", "seed", "seeds", "tank", "tub", "rubbish",
            "waste", "compost", "manure", "sand", "gravel", "rubble", "shed", "trampoline")


def _buried_person(clean, words, person=False):
    """True for "we buried my dad", false for "i buried the fence posts" and "the dog buried a
    bone": after the verb, the thing being buried has to be a person or a pet. A passive
    "be buried" is read from the subject in front of it, which the line names as a person or
    not at all."""
    if not BURIED.search(clean):
        return False
    for index, word in enumerate(words):
        if word not in ("buried", "bury"):
            continue
        if index and words[index - 1] in PASSIVE_AUX:
            # "my dad was buried last year" and "she was buried with her wedding ring" are
            # funerals; "the fence post should be buried two foot deep" and "the cable is
            # buried in the garden" are not. A person, a pet or a grave object settles it one
            # way, a thing that gets buried the other, and anything else keeps the reading the
            # verb had before, so a condolence is not lost to a subject nobody listed.
            if person or _has_pet(words) or set(words) & set(REMAINS):
                return True
            return not (set(words) & set(BURIABLE))
        rest = words[index + 1:index + 5]
        while rest and rest[0] in BURIED_ADJECTIVE:
            rest = rest[1:]
        if rest and rest[0] in ("him", "her", "them"):
            return True
        if rest and rest[0] in BURIED_OBJECT:
            rest = rest[1:]
            while rest and rest[0] in BURIED_ADJECTIVE:
                rest = rest[1:]
            if not rest:
                return False
            return rest[0] in PEOPLE
        return True
    return False


def _put_down(clean, words):
    """True when "put down" / "put to sleep" is about a pet that died, not a nap or a phone."""
    if not PUT_DOWN.search(clean):
        return False
    if any(phrase in clean for phrase in BEDTIME) and not any(
            phrase in clean for phrase in LOSS_CONTEXT):
        # "how do i put my cat to sleep at night" is about a bedtime routine, not a death;
        # a loss still counts when it says when ("last night", "yesterday") or how ("vet").
        return False
    if _has_pet(words):
        return True
    return any(phrase in clean for phrase in LOSS_CONTEXT)


def _names_a_stored_pet(text, memory):
    """Whether the line names a pet the store holds: "rex died" is about a pet the bot knows."""
    known = (memory or {}).get("user") or {}
    # A pet the observer has just taken off the store is still the animal the line is about.
    pets = list(known.get("pets") or []) + list(known.get("pets_gone") or [])
    said = set(words_of(text))
    for pet in pets:
        if not isinstance(pet, dict):
            continue
        name = str(pet.get("name") or "").strip().lower()
        if name and len(name) > 2 and name in said:
            return True
    return False


def _has_pet(words):
    return any(word in PET_WORDS for word in words)


def _a_person_dying(tight):
    """True when a death that is still ahead is somebody's: "my dad is dying", "shes dying".

    A phone dies, a battery dies, the house plants die. The person is read from the same words
    the rest of the loss code uses (`_has_person`), so a relation that is not the closest family
    counts too: "my carer is dying" and "my other half is dying" were both the person in front
    of them, and both fell through to an echo or to the money answer that reads "half" as a
    split.
    """
    words = [word.strip(",.?!") for word in tight.split()]
    if any(word in ("he", "she", "they", "him", "her", "them") for word in words):
        return True
    return _has_person(words)


def _a_hard_time_that_is_theirs(line):
    """True when the line says a person close to the user is having the hard time.

    "my mum is lonely since dad died" is about the mum, and "i'm lonely since dad died" is about
    the person typing - so the relation has to be the subject, the state has to be theirs, and a
    death has to be in the line. A pet in the line is somebody else's answer (`a_relative_pet`),
    and so is a line about what to say to them.
    """
    text = str(line or "").lower().replace("\u2019", "'")
    if not A_RELATION_IN_A_HARD_TIME.search(text):
        return False
    if not DEATH_WORD.search(text):
        return False
    return not the_animal(text)


# A child of the house whose other parent, brother or grandparent has died: "my son cried when
# his dad died" is the user's own household in a hard time, and the pool for a loss that belongs
# to somebody else told them how to write a sympathy message about their own son's father
# ("Say you're sorry, name them if you can"). The child lives with the user, so the loss is
# theirs too. A line about somebody else's relative ("my mum cried when her dad died") keeps its
# reading, because the person named first is not a child of the house.
CHILDS_OWN_LOSS = re.compile(
    r"\b(?:my|our)\s+(?:son|sons|daughter|daughters|child|children|kid|kids|boy|girl|lad|lass|"
    r"teenager|baby|toddler|stepsons?|stepdaughters?|stepchildren)\b[^.]{0,40}"
    r"\b(?:his|her|their)\s+(?:dad|daddy|mum|mummy|father|mother|parent|parents|brother|"
    r"sister|grandad|grandads|granddad|grandma|grandmas|gran|grans|nan|nans|grandpa|grandparents)\b",
    re.I)


def whose(clean):
    """'someone' when the loss belongs to someone else, else 'own'.

    Three shapes: a friend named with their relation ("my friend's mum"), a relation or an
    animal named as his or hers ("her dad", "their dog"), and a household named with a
    possessive or a neighbour's animal said as the street's ("my mum's cat", "the cat next
    door"). All of them mean the same thing: the person in front of us is not the bereaved one,
    so the reply is what to say rather than sympathy for them.
    """
    if CHILDS_OWN_LOSS.search(clean) and not A_STRANGERS_ANIMAL.search(clean):
        return "own"
    if (SOMEONE_ELSES.search(clean) or HIS_HERS.search(clean)
            or SOMEONE_ELSES_OWN.search(clean) or A_STRANGERS_ANIMAL.search(clean)):
        return "someone"
    return "own"


# A pet that belonged to someone else in the family is that person's loss: "my mum's cat died"
# wants what to say to her, not sympathy for the user and not the cremation card, which is advice
# for the person who has to decide about the body.
# "the {animal}" is filled from the line: "my mum's dog died" was handed the one line of this pool
# with an animal in it, and that animal was the cat. Being told to say "sorry about the cat" about
# a dog reads as a machine, and the animal the line gave is the only one that can be right.
RELATIVE_PET_REPLIES = (
    "Oh, that's hard on them. A {one} is family to the person who had it — say straight out "
    "that you're sorry, and ask how they're doing.",
    "That's a real loss for them, not a small one. Say it plainly (\"I'm so sorry about the "
    "{animal}\"), then check in again in a week or so.",
    "Pets are family, so treat it the way you would a family death for them: say you're sorry "
    "about the {animal}, and offer one concrete thing if you're close enough.",
)

# An animal nobody in the house keeps is not the user's to grieve, but it is still a death in
# their week: "the cat next door died last year" is the street's loss, so it gets a warm line
# rather than sympathy for the person in front of us.
STRANGER_ANIMAL_REPLIES = (
    "That's sad. A {one} you only see over the fence is still part of the day, and the street "
    "is quieter without it.",
    "Sorry to hear that. You don't have to own a {one} to miss one — it's a real gap when one "
    "that was always about goes.",
    "Oh no. Even a neighbour's {animal} leaves a quiet patch behind it, and noticing that isn't "
    "silly.",
)

# The animal as the line names it. Two words when it takes two: "my mates guinea pig died" is not
# "sorry about the guinea". The last animal word in the line is the one the death is about.
TWO_WORD_PETS = (("guinea", "pig"), ("guinea", "pigs"))
# The same animal in the singular, for the lines that start "A ..." or "a ...": "our neighbour's
# cats died" was "A cats is family", which is not a sentence. Only these few words pluralise.
PLURAL_PAIRS = {"cats": "cat", "dogs": "dog", "rabbits": "rabbit", "bunnies": "bunny",
                "hamsters": "hamster", "budgies": "budgie", "parrots": "parrot", "horses": "horse",
                "ponies": "pony", "ferrets": "ferret", "rats": "rat", "tortoises": "tortoise",
                "snakes": "snake", "lizards": "lizard", "gerbils": "gerbil",
                "chinchillas": "chinchilla", "cockatiels": "cockatiel", "guinea pigs": "guinea pig",
                "puppies": "puppy", "kittens": "kitten", "fish": "fish", "mice": "mouse"}


def one_of(animal):
    """The animal in the singular, because "A cats is family" is not a sentence."""
    return PLURAL_PAIRS.get(animal, animal)


# The animal that died is named before the death word, never after it: "my dad's dog died, he still
# has a cat" names a live cat, and a condolence about the cat would be about the wrong animal. A
# second animal after the death is a thing people do say, so the words are split at the death.
DEATH_WORD = re.compile(
    r"\b(?:died|dies|dying|dead|death|passed|put\s+down|put\s+to\s+sleep|euthanised|"
    r"euthanized|killed|pts|gone|loss|lost)\b")


def the_animal(line):
    """The animal the line names ("dog", "guinea pig"), or "" when it names none."""
    text = str(line or "").lower().replace("\u2019", "'")
    words = words_of(text)
    named = [word for word in words if word in PET_WORDS]
    if not named:
        return ""
    death = DEATH_WORD.search(text)
    if death:
        before = [word for word in words_of(text[:death.start()]) if word in PET_WORDS]
        named = before or named
    for first, second in TWO_WORD_PETS:
        if first in words and second in words:
            return f"{first} {second}"
    return named[-1]


def named_animal(replies, line):
    """The pool with the animal the line named in it: "my mum's dog died" hears about the dog.

    "pet" is the word when the line names no animal at all, which reads in every one of these
    sentences and cannot be wrong the way a guessed animal can.
    """
    animal = the_animal(line) or "pet"
    return tuple(reply.format(animal=animal, one=one_of(animal)) for reply in replies)


def a_relative_pet(line):
    """True when the animal that died was someone else's in the family: "my mum's cat died"."""
    match = SOMEONE_ELSES_OWN.search(str(line or "").lower().replace("\u2019", "'"))
    return bool(match and match.group("who") in PET_WORDS)


def a_strangers_animal(line):
    """True when the animal that died belongs to nobody in the house: "the cat next door"."""
    return bool(A_STRANGERS_ANIMAL.search(str(line or "").lower().replace("\u2019", "'")))


# Whose loss it is and what stage it is at, read off the thread rather than off this line.
# "what about the wake", "and the flowers": a line that swaps the thing in the question before
# it keeps that question's ask. It is how a conversation narrows ("what should i wear to a
# funeral" / "what about the wake"), so the answer to it is about the thing swapped in and not
# about the day. Only a swap that follows a question about going inherits an ask this file's
# attendance card answers, which is why "should i go to the funeral" / "what about the wake"
# still gets the card and the deck's "what should i wear to a wedding" / "i meant a funeral" /
# "what about the wake" gets the clothes answer instead of "Go if you can".
SWAP_ASK = re.compile(r"^(?:and|but|also|what\s+about|how\s+about|what\s+(?:of|say)|and\s+what\s+about)\b")
SWAP_MOST_WORDS = 8
# A line that asks something: a question word at the front, or a question mark anywhere. Used to
# find the question a swap inherits, so a correction between the two ("i meant a funeral") is
# stepped over rather than read as the question.
ASKS = re.compile(
    r"\?|\b(?:what|which|how|when|where|who|why|should|shall|can|could|do|does|did|is|are|"
    r"was|were|will|would|must|have|has)\b", re.I)
# A swap's own ask words: what the person wants about the thing they swapped in. When the
# question before asked one of these, the swap asks it again about the new thing.
A_SWAP_INHERITS = re.compile(
    r"\b(?:wear|wearing|put\s+on|bring|brings|take|give|send|order|buy|cook|make|pack|"
    r"choose|pick|pay|cost|costs)\b")


def _a_swap_of_the_question_before(text, memory):
    """True when the line only swaps the thing in the question before it, and that question asked
    something this file's funeral card does not answer.

    "what about the wake" a turn after "what should i wear to a funeral" is the wear question
    with the wake in it, so the clothes answer fits and "Go if you can, even just for the
    service" is advice for a different question. The card keeps the line when the question
    before was about going, about what to say, or when nothing was asked before at all.
    """
    tight_line = _tight(text)
    if not SWAP_ASK.match(tight_line):
        return False
    if len(_plain(text)) > SWAP_MOST_WORDS:
        return False
    previous = ""
    for turn in reversed([t for t in (memory.get("turns") or []) if isinstance(t, dict)][:8]):
        line = str(turn.get("user") or "")
        if not line.strip() or _plain(line) == _plain(text):
            continue
        # A correction ("i meant a funeral") is not the question the swap inherits: the question
        # is the one before it, which the correction was rewriting.
        if ASKS.search(" ".join(_plain(line))):
            previous = line
            break
    if not previous or not _plain(previous):
        return False
    return bool(A_SWAP_INHERITS.search(_tight(previous)))


def _still_ahead(memory):
    """The pool for a death that has not come yet, or None when it has.

    A chat about a pet the vet has given weeks to, or a parent in the last stages, is at the
    days before - and the answer to "what do i do now" there is about those days, never the card
    for what happens to a body.
    """
    record = memory.get("loss")
    if isinstance(record, dict) and record.get("ahead"):
        # The store was told which week this is: "the doctor said theres nothing more they can do"
        # is the days before the death, so the turn after it is not the register office.
        pool = THE_DAYS_BEFORE if record.get("pet") else SOMEONE_DYING
        return _less_what_was_said(pool, [t for t in (memory.get("turns") or [])
                                          if isinstance(t, dict)])
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-4:]):
        line = str(turn.get("user") or "")
        tight_line = _tight(line)
        if not line or QUESTION.search(line) or not NOT_YET.search(tight_line):
            continue
        # The estimate has to be about somebody: "i have three weeks left until my holiday" is a
        # countdown to a holiday, not a death.
        if _has_pet(_plain(line)):
            return _less_what_was_said(THE_DAYS_BEFORE, turns)
        if _a_person_dying(tight_line):
            return _less_what_was_said(SOMEONE_DYING, turns)
    last = str(turns[-1].get("bot") or "") if turns else ""
    if last and last in THE_DAYS_BEFORE:
        return _less_what_was_said(THE_DAYS_BEFORE, turns)
    if last and last in SOMEONE_DYING:
        return _less_what_was_said(SOMEONE_DYING, turns)
    return None


# The people the advice sends you to. Two pool lines about the doctor are the same move said
# again, however the sentence is built.
_HELPERS = re.compile(r"\b(?:doctor|doctors|gp|gps|consultant|nurse|nurses|vet|vets|"
                      r"hospice|hospital|carers?)\b", re.I)


def _less_what_was_said(pool, turns):
    """The pool with the advice this chat has already been given taken out.

    "my dad is dying" then "what do i do now": the answer to the second is about the days before
    it, and the bot had already said to ask the doctor what to expect. Handing that back with the
    words rearranged reads as a bot that is not listening, so a line the chat has already had -
    and a line that sends them to the same people - is not offered again (fast-shelf, #3379).
    """
    said = [str(t.get("bot") or "").strip() for t in turns or [] if str(t.get("bot") or "").strip()]
    if not said:
        return pool
    kept = [line for line in pool
            if line.strip() not in said
            and not (_HELPERS.search(line) and any(_HELPERS.search(one) for one in said))]
    return tuple(kept) or pool


# Whether to end an animal's life is not a bereavement: nothing has died, and the person is
# carrying a decision rather than a funeral. The question comes in one shape - a judgement word
# (cruel, selfish, wrong, unfair) about keeping the animal going - and the animal it is about is
# either named in the line or is the one this chat has been about, never guessed from nothing.
KEEPING_JUDGED = re.compile(
    r"\b(?:cruel|cruelty|unkind|wrong|selfish|unfair|mean|nasty)\b[^.?!]{0,60}?"
    r"\b(?:keep|keeping|kept)\b(?=[^.?!]{0,50}\b(?:going|alive)\b)"
    r"|\b(?:keep|keeping|kept)\b(?:\s+\w+){0,4}\s+(?:going|alive)\b[^.?!]{0,50}?"
    r"\b(?:cruel|cruelty|unkind|wrong|selfish|unfair)\b"
    # the same question with the putting said instead of the keeping: "is it selfish to put him
    # down", "am i being cruel having her put to sleep"
    r"|\b(?:cruel|cruelty|unkind|wrong|selfish|unfair)\b[^.?!]{0,60}?"
    r"\b(?:put|putting|having\s+(?:\w+\s+){0,3}put)\b(?:\s+\w+){0,4}\s+(?:down|to\s+sleep)\b"
    r"|\b(?:cruel|cruelty|unkind|wrong|selfish|unfair)\b[^.?!]{0,60}?\blet\s+(?:\w+\s+)?go\b")
# The same decision asked as a time rather than a judgement: "should i put her to sleep", "when
# do you know its time". There is no judgement word in it, so it needs its own shape, and it is
# only read when the animal is named in the line or this chat has been about one.
ENDING_ASKED = re.compile(
    # Anchored at the start of the line, because a line that *states* the appointment ("my dog is
    # being put to sleep tomorrow") has an "is" and a "put to sleep" in it too, and that one is
    # the days before it, not this question.
    r"^(?:(?:and|so|but|oh|god|honestly|now|then|ok|okay)\s+)*"
    r"(?:should|shall|ought|when|how|do|does|is|will)\b(?![^.?!]{0,40}\b(?:bed|bedtime|"
    r"crate|kennel|lead|garden|room|downstairs|upstairs|outside|night|nights|nap|naps)\b)"
    r"[^.?!]{0,40}?\b(?:put|putting|have\s+(?:\w+\s+){0,3}put|let\s+(?:\w+\s+)?go)\b"
    r"(?:\s+\w+){0,4}\s+(?:down|to\s+sleep)\b"
    r"|^(?:(?:and|so|but|oh|honestly|now|then)\s+)*(?:when|how)\b[^.?!]{0,30}?"
    r"\b(?:know|tell|decide|sure)\b[^.?!]{0,30}?\b(?:its|it's|the)\s+(?:time|right\s+time|end)\b"
    r"|^(?:(?:and|so|but|oh|honestly|now|then)\s+)*is\s+it\s+(?:the\s+|the\s+right\s+)?time\b"
    r"[^.?!]{0,20}\b(?:to\s+)?(?:let|put|say\s+goodbye|stop|end)\b")
# What the decision gets: the judgement answered plainly first, then the one test that turns a
# guess into a reading - a normal week, written down - and the vet told to be blunt. No question
# back, because the person is already in the worst part of it.
KEEPING_GOING_REPLIES = (
    "Not cruel, no. Wanting to keep a pet with you is the ordinary way love behaves, and asking "
    "the question is what someone who is still looking after them does. What helps is a written "
    "week - did they eat, settle, sleep, enjoy one thing - because a change is easier to see over "
    "a fortnight than in one bad night.",
    "That is not selfish, and it is not a vote. Ask the vet what they would do with their own "
    "animal and ask them to be blunt about pain and appetite, then keep a note of the good days "
    "against the bad ones - most people find the answer is in that note rather than in the guilt.",
    "Asking it says most of what needs saying: you have not stopped looking after them. Whether "
    "keeping on is fair depends on the animal, not on you - eating, drinking, pain, one thing "
    "still enjoyed. Take that list to the vet and let them tell you what the next weeks look "
    "like, rather than working it out alone.",
    "No, not cruel. There is no scoreboard for this, and the person who is doing it for the "
    "animal's sake is usually the one who feels worst about it. The useful thing is the vet's "
    "honest view plus a normal week written down: food, drink, sleep, pain, one good thing a day.",
)
# The same decision asked as a time: "should i put her to sleep", "when do you know its time".
# Same subject, so the same first move - the vet's honest view and a written week - but "cruel"
# is not what was asked, so these never open by answering it.
IS_IT_TIME_REPLIES = (
    "There is no single day, and waiting for a sign that everyone agrees on is what makes this "
    "the hardest part. What people use: more bad days than good, no interest in food or in the "
    "things they loved, pain the vet cannot get on top of. Ask the vet to go through a "
    "quality-of-life list with you - it turns a guess into something you can look at.",
    "Only you and the vet can say, and the vet has done this far more often than you have. Write "
    "down a normal day for the next week - eating, drinking, moving, sleeping, one thing they "
    "still enjoy - and take that to the appointment; a fortnight of it usually makes the call "
    "clearer than any single bad night.",
    "It is a judgement rather than a date, and the ones that go wrong are the ones made in a "
    "panic at 2am. Book a talk with the vet about quality of life and ask them plainly: would "
    "they wait, and what would make them stop waiting?",
)


def _an_animal_in_the_chat(memory, turns=6):
    """True when a line earlier in this chat named an animal of ours.

    "is it cruel to keep him going" carries no animal in it, and the only way to know it is a dog
    "or a cat is the line before it: "my dog is 12 and going blind" then "he keeps bumping into
    "things". Read off the turns, never assumed.
    """
    history = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(history, list):
        return False
    for turn in history[-turns:]:
        said = turn.get("user") if isinstance(turn, dict) else None
        if isinstance(said, str) and PET.search(_tight(said)):
            return True
    return False


def _keeping_going(tight, words, memory):
    """The pool for whether to keep an animal going, or None when the line is not that question.

    Kept to animals: the end of a person's life is a different question with a different answer,
    and the lines that ask it are handled by the dying pools above. When the line names no animal,
    the chat has to have one, so "is it cruel to keep him going" after "my dog is 12" reads and
    "is it cruel to keep him going" on its own does not.
    """
    judged = bool(KEEPING_JUDGED.search(tight))
    if not judged and not ENDING_ASKED.search(tight):
        return None
    where = KEEPING_GOING_REPLIES if judged else IS_IT_TIME_REPLIES
    if _has_pet(words):
        return where
    if _has_person(words):
        return None  # "is it cruel to keep my mum going" is a different question, with its own pools
    if _an_animal_in_the_chat(memory):
        return where
    return None


def _first_days(memory):
    """The pool for the days just after a death: the animal's, or a person's."""
    record = memory.get("loss")
    pet = isinstance(record, dict) and record.get("pet")
    return FIRST_DAYS_PET if pet else FIRST_DAYS_PERSON
# The ask that belongs to a person who is still here and not to a death: "how do i say goodbye to
# him", "what do i say to her while she can still hear me". Once the chat is about a dying person
# the same words are the wrong pool - SAY_REPLIES is how you tell somebody that someone died ("say
# the name: your dad died on Tuesday"), which is a different week and a different job.
SAY_GOODBYE = re.compile(
    r"\b(?:say\s+good\s?bye|good\s?bye\s+to\s+(?:him|her|them)|last\s+words|"
    r"what\s+(?:do|should|can)\s+i\s+say\b|what\s+to\s+say\b|"
    r"how\s+(?:do|can)\s+i\s+say\b)")
# Who the say ask is aimed at. "what do i say to the kids" and "what do i say to the school" are
# what to tell other people, and the visit pool is the wrong answer to them, so the target has to
# be the dying person (or nothing at all). A list of the ones that mean them is safer than a
# catch-all on "to the ...": the wrong way round gives the telling-others advice to a person who
# is about to sit with someone dying.
SAY_TO_WHO = re.compile(r"\b(?:say|talk)\s+to\s+"
                        r"(?:(?:the|my|our|his|her|their|your)\s+)?(\w+)")
VISIT_TARGETS = frozenset(("him", "her", "them", "himself", "herself", "themselves"))


def _the_visit_ask(clean):
    """True when the line asks what to say to the person who is dying, not what to tell others."""
    if not SAY_GOODBYE.search(clean):
        return False
    for found in SAY_TO_WHO.finditer(clean):
        if found.group(1) not in VISIT_TARGETS:
            return False
    return True


def _the_animal_of(text, memory):
    """The animal this turn is about: the one the line names, else the one the loss was about."""
    animal = the_animal(text)
    if animal:
        return animal
    record = (memory or {}).get("loss") if isinstance(memory, dict) else None
    if isinstance(record, dict):
        return the_animal(str(record.get("who") or ""))
    return ""


def _grief_replies(line, memory):
    """The pool for "does it get easier": a pet's death is answered with the animal in it.

    Only the person's own animal counts: "my friend's dog died" is a line about what to say to
    your friend, and a line about the gap in *your* day would be somebody else's grief.
    """
    if whose(line) == "someone":
        return GRIEF_REPLIES
    animal = _the_animal_of(line, memory)
    if not animal:
        return GRIEF_REPLIES
    if animal.endswith("s"):
        # "my dogs died": the pool says "losing a dog", not "losing a dogs".
        singular = animal[:-1]
        if singular in PET_WORDS or singular.endswith(" pig"):
            animal = singular
    article = "an" if animal[:1] in "aeiou" else "a"
    return tuple(reply.format(animal=animal, article=article) for reply in PET_GRIEF_REPLIES)


def _a_colour_is_worn(line):
    """True when the line asks about a colour of clothes (the knowledge base's own reading)."""
    try:
        from ..knowledge import lookup
        return lookup.a_colour_is_worn(line)
    except Exception:  # noqa: BLE001 - a reading that fails leaves the loss where it was
        return False


def reply_for(text, memory, clean=None, topics=None, mood=None):
    """The pool the line asks for, or None when it is not about a death.

    The caller picks from the pool, so the wording still varies and never repeats. A follow-up
    to the bot's own sympathy ("what do I even say to him", "i still can't sleep") is read the
    same way, because the family of a death keeps asking the same few things.
    """
    words = words_of(text)
    line = clean if isinstance(clean, str) and clean else " ".join(words)
    tight = _tight(line)
    if _a_colour_is_worn(line) and not A_DEATH_HAPPENED.search(tight):
        # Clothes are not the loss. "is white ok at a funeral" is the question "what do I wear to
        # the funeral" with the colour where the verb would go, and the condolence that follows is
        # "Go if you can, even just for the service" - advice for somebody who has not decided to
        # go at all. The reading is the knowledge base's own (`lookup.a_colour_is_worn`), so this
        # file keeps no second list of colours, and a colour a person only reports ("i bought a
        # black dress for my mums funeral") is still the loss it was. A line that says a death
        # happened keeps the loss even with a colour in it: "my mum died last week, is black ok at
        # the funeral" is somebody's week first, and the clothes answer to it was a shrug.
        return None
    if _dream is not None and _dream.SETTLED_IT.search(line) \
            and _dream.told_in_the_turn_before(memory):
        # The line that settles a dream the bot was just told ("hes fine its just a dream") names
        # no frame of its own, and it was read as a bereavement: the condolence answered a death
        # the same person had just said did not happen. The dream thread keeps it.
        return None
    if _dream is not None and _dream.a_dream_is_not_happening(line) \
            and not _dream.a_death_came_first(line):
        # A death in a dream is not a death: "i dreamt my dad died", "i had a dream my mother
        # died" and "i dreamt my cat died" were each answered with the condolence for a death
        # that had not happened. The dream module has the whole line. A death in the waking life
        # with a dream beside it ("my dad died and i dreamt about him") is still this module's.
        return None
    if _only_a_new_subject(line):
        return None  # the thing the line corrects, not a loss it reports
    if DYING_OTHER.search(tight):
        return None  # "my mum is dying for a coffee", "my mums dying her hair"
    if SPEAKER_TOO.search(tight) and not WISH_FRAME.search(tight):
        # Read the other half as it would be read alone: the same clause said of the speaker is
        # taken off first, so "my dog is at the end and so am i" is read as "my dog is at the end"
        # and "the paint is fading and so am i" is read as "the paint is fading" - which is not
        # somebody's week, and stays ordinary.
        rest = SPEAKER_TOO.sub(" ", tight).strip()
        animal = bool(PET.search(rest)) and _a_pet_of_ours(rest, words)
        if (is_dying_now(rest) or _the_end_is_near(rest, words)
                or (animal and (AT_THE_END.search(rest) or PET_AT_THE_END.search(rest)
                                or PET_HAS_HAD_ENOUGH.search(rest)))):
            # "my dog is at the end and so am i", "my nan is fading fast and so am i": the ending
            # is said of the other one and then of the speaker, and the speaker is the one nobody
            # was answering - the pet pool would be about the animal, and the echo is no answer.
            return SPEAKER_TOO_REPLIES
    if (PET_HAS_HAD_ENOUGH.search(tight) and PET.search(tight)
            and _a_pet_of_ours(line, words) and not SPEAKER_HAS_HAD_ENOUGH.search(tight)):
        # "my dog wants to die", "my cat has no quality of life": the animal has had enough and
        # the person is facing the days before it, which is the one pool written for that day.
        return THE_DAYS_BEFORE
    if (PET_AT_THE_END.search(tight) and PET.search(tight)
            and _a_pet_of_ours(line, words) and not SPEAKER_HAS_HAD_ENOUGH.search(tight)):
        # "my dog is at the end", "my cat is ready to go", "i think my dog is telling me its time":
        # the same week as "my dog is dying", said the way people say it. Nothing here has died, so
        # every condolence pool is about the wrong day.
        return THE_DAYS_BEFORE
    if AT_THE_END.search(tight) and not SPEAKER_HAS_HAD_ENOUGH.search(tight):
        # The ending said another way, for whichever of ours it is: "my dad is at the end", "my nan
        # is on her last legs", "the doctors say there is nothing more they can do". Before this
        # they came back as a memory echo ("Noted: your nan is on her last legs"), a punt, or - for
        # "my friend is at the end" - the card for a breakup. `is_dying_now` carries the reading, so
        # the follow-up after one of these lines ("what do i say to him") knows the week too.
        if is_dying_now(tight):
            if PET.search(tight) and _a_pet_of_ours(line, words):
                return THE_DAYS_BEFORE
            if "?" in line or ASK_WORDS.search(tight) or line.startswith(
                    ("what", "how", "should", "can", "do", "does", "is", "why", "when")):
                return DYING_SAY_REPLIES
            return DYING_REPLIES
    if _the_visit_ask(tight) and dying_in_the_chat(memory):
        # "how do i say goodbye to her" two turns after "my carer is dying" is about the visit,
        # not the announcement: the person is still here, and the other pool tells somebody the
        # news. Read before the follow-up guard below, which wants a pronoun the line may not
        # have ("how do i say goodbye").
        return DYING_SAY_REPLIES
    asking = "?" in line or bool(ASK_FORM.search(tight)) or bool(ASK_WORDS.search(tight)) or line.startswith(
        ("what", "how", "should", "can", "do", "does", "is", "why", "when"))
    if EULOGY_WORD.search(tight) and EULOGY_ASK.search(tight):
        # a eulogy to write is a writing job: the wording entry has the structure and the length
        return None
    if WEAR.search(tight):
        # "what do i wear to the funeral" is a question about clothes, and the clothing entry
        # answers it better than the funeral pool can.
        return None
    if _a_swap_of_the_question_before(text, memory):
        # "what about the wake" a turn after "what do i wear to the funeral" is the wear question
        # with a new thing in it, so the entry for that thing answers it ("The same goes for the
        # wake: Familiar, subdued clothes are the thing"). This file's funeral card answers
        # whether to turn up, which is a different question - the one the deck's
        # "what should i wear to a wedding" / "i meant a funeral" / "what about the wake" chat was
        # answered with before this line existed.
        return None
    if _a_gift_for_someone_in_care(tight):
        # "my mum is in a hospice, what do i buy her" is a present question asked by somebody whose
        # mother is dying, and the sympathy pool has no present in it: it answered "sit with them,
        # keep the room calm", which is not a reply about a gift at all. The gift entry knows what
        # to take to a bedside, so the composer stands aside for it. Only the ask, never the
        # statement: "my nan is in a hospice" is the condolence and nothing else.
        return None
    if _telling_a_child(tight):
        # how to explain a death to a child is the family entries' question, not sympathy for
        # the adult the line is written by (see TELL_CHILD)
        return None
    cost_pool = (arrangement_cost_pool(line, tight, memory)
                 or arrangement_cost_pool(text, tight, memory))
    if cost_pool:
        # "is cremation cheaper than burial": a price question about the arrangements with no
        # death in the line. Nothing that reads words had anything about a funeral to say to it,
        # and the funeral pool gave a guest's advice to somebody weighing up a bill.
        return cost_pool
    if is_practical_ask(line, tight) or is_practical_ask(text, tight):
        # A practical question in the middle of a bereavement is not a request for comfort:
        # what a funeral costs, how long probate takes, what to cook for the wake, how to ask
        # for bereavement leave. Read only as a loss, each of them got the wrong pool; the
        # answer modules and the honest hedges do better, so the composer stands aside.
        return None
    if (not QUESTION.search(line) and not ASK_WORDS.search(tight)
            and not NOT_THE_END.search(tight) and (
                ESTIMATE.search(tight) or _the_end_is_near(tight, words))) and (
            _has_pet(words) or _a_person_dying(tight) or CARE_WHO.search(tight)):
        # The vet's estimate instead of the word itself: "the vet says my cat has a few weeks
        # left", "they gave my dad two months". Nothing has died yet, so the day it is at is the
        # days before it, and this is the answer the entries below would never reach. Only the
        # estimate, never the plain "is dying": that one is `DYING_REPLIES`, below.
        pet = _has_pet(words) or _the_vet_said_it(tight, words)
        return THE_DAYS_BEFORE if pet else SOMEONE_DYING
    if OPEN_ASK.match(tight):
        # "what do i do now" while a death is still ahead is that question, whether or not the
        # store has a record of the loss yet: "the vet says my cat has a few weeks left" is
        # answered here without one, so the thread has to be read off the turns.
        ahead = _still_ahead(memory)
        if ahead is not None:
            return ahead
    if lost_in_a_place(text):
        # A person lost in a shop or a park is a panic, not a bereavement, and the answer is
        # what to do in the next five minutes.
        return MISLAID_REPLIES
    if (GET_THROUGH.search(tight) or GET_THROUGH_DAY.search(tight)) \
            and not GET_THROUGH_TO.search(tight):
        # It is a loss line only when the chat already is one, because the line names no death:
        # nothing else in this file can say so. "how do i get through the week" on its own is
        # somebody with too much on and is left to the entries.
        ahead = bool(is_dying_now(tight) or dying_in_the_chat(memory) or _still_ahead(memory))
        if _a_thing_of_its_own_to_get_through(tight):
            # A practical thing got through is that thing's question, and it stays one inside a
            # loss conversation: the rota, the exam, the paperwork all have an entry, and none of
            # them is answered by "pick the next thing - a shower, a sandwich, one phone call".
            return None
        if ahead or continues(memory) or reads_as_loss(
                text, words, _names_a_stored_pet(text, memory)):
            if GET_THROUGH_DAY.search(tight):
                # A day with a shape to it is got through by marking it: the ritual pool.
                return REMEMBER_REPLIES
            if ahead:
                # The days before: the nursing and the grief are the same days.
                return GETTING_THROUGH_DYING_REPLIES
            return GETTING_THROUGH_REPLIES
    if not continues(memory) and _an_ending_in_the_chat(memory):
        # "my girlfriend broke up with me" then "its been 3 weeks" or "will it ever get better":
        # a follow-up in a chat that is a loss without a death in it. Left alone, neither line
        # named an entry of its own, so bot/modules/chat.py read it with the topic in front of it
        # and the nearest entry answered - the refund ladder for the gap ("Faulty goods are the
        # retailer's problem, not the maker's") and a fitness card for the feeling ("two to three
        # weeks of regular sessions and the stairs and your sleep are easier"). `continues` is
        # False because an ending's own answer is an entry's card, not a pool line, and a
        # bereavement chat keeps `TIME_SINCE_REPLIES` below for itself.
        if _how_long_since(tight, tight.split()) and not _names_a_subject(topics):
            return ENDING_SINCE_REPLIES
        if (A_FEELING_BETTER_ASK.search(tight)
                and not (set(topics or ()) - THREAD_TOPICS - MEASURE_TOPICS - {"health"})):
            # "how long will it take to feel better" is read as a health line by the reader, and
            # the health topics are this file's own ("what should i do", "will it ever stop"), so
            # health is allowed here where the span above does not need it.
            return ENDING_FEELINGS_REPLIES
    keeping = _keeping_going(tight, words, memory)
    if keeping:
        # "is it cruel to keep him going" after "my dog is 12 and going blind": nothing has died,
        # so the condolence pools are about the wrong day, and the pets entry's careful-routine
        # answer reads "keep" as the furniture. The decision itself is what was asked.
        return keeping
    if reads_as_loss(text, words, _names_a_stored_pet(text, memory)):
        if CARD.search(tight) and (ASK_WORDS.search(tight) or asking
                                   or (CARD_TO_WRITE.search(tight) and WRITE_WORD.search(tight))):
            return CARD_REPLIES
        ahead_now = (is_dying_now(line) or _the_end_is_near(tight, words)
                     or (dying_in_the_chat(memory)
                         and (TREATMENT_STOPPED.search(tight)
                              or NOTHING_MORE_TO_DO.search(tight))))
        if ahead_now and not (FUNERAL.search(tight) or WAKE.search(tight)):
            # Still here, so the plain sympathy is about the wrong day (see DYING_NOW). It comes
            # before the "what do i say to them" pool because what to say to someone who is
            # dying is not what to say to someone who has lost them.
            if _a_pet_of_ours(line, words) or _the_vet_said_it(tight, words):
                # The vet's timeline is main's `THE_DAYS_BEFORE` (the pet work landed it first);
                # this reading only makes it reachable from the contraction and the job guard.
                return THE_DAYS_BEFORE
            if ASK_WORDS.search(tight):
                return DYING_SAY_REPLIES
            if QUESTION.search(line):
                return DYING_GRIEF_REPLIES
            return DYING_REPLIES
        if ASK_WORDS.search(tight):
            return SAY_REPLIES
        if (NOT_YET.search(tight) and not PUTTING_REGRETTED.search(tight)
                and not QUESTION.search(line)):
            # A death that is still ahead is not a condolence for a death that has happened: what
            # helps is the days before it, whether it is a pet or a person. A putting the person
            # says they regret is not still ahead (`PUTTING_REGRETTED`).
            if PET.search(tight):
                return THE_DAYS_BEFORE
            if _a_person_dying(tight):
                return SOMEONE_DYING
        if (FUNERAL.search(tight) or WAKE.search(tight)) and (
                asking or whose(line) == "someone") and not _feeling(tight):
            # "i'm going to his wake tomorrow" wants the same answer as "should i go to the
            # funeral": the user is not the bereaved one, they are the one turning up. A line
            # that names a feeling of theirs is asking about the feeling, not about the
            # attendance: "is it normal to feel relieved after a funeral" was sent to the
            # funeral card ("If you can make it, go") when it is the one line this file already
            # has an answer for - that relief after a death is common and does not cancel grief.
            if _when_asked(tight):
                return FUNERAL_WHEN_REPLIES
            return FUNERAL_REPLIES
        if marks_a_day(tight) and asks_what_to_do(tight):
            return REMEMBER_REPLIES
        feeling = _feeling(tight)
        if feeling and _asks_about_the_feeling(tight):
            # A question about the feeling itself - "is it normal to feel relieved after a
            # funeral", "is it weird that i feel relieved about it" - is answered by what the
            # feeling is, and the line for that is here. The question guard below answers a
            # question about the loss in general ("how long does this take"), and the funeral
            # card answers one about turning up, which is neither of these.
            return FEELING_REPLIES[feeling]
        if QUESTION.search(line):
            return _grief_replies(line, memory)
        if feeling:
            return FEELING_REPLIES[feeling]
        if whose(line) == "someone":
            # Not the user's loss, so the answer is what to say to whoever had it — or, for an
            # animal that is nobody's in the house, a warm line about the animal itself.
            if a_relative_pet(line):
                return named_animal(RELATIVE_PET_REPLIES, line)
            if a_strangers_animal(line):
                return named_animal(STRANGER_ANIMAL_REPLIES, line)
            if set(words_of(line)) & CLOSE:
                # The line names whose relation died ("a friend whose mum died", "my friend's dad
                # died"), so the answer names them too. One line of the pool is for a loss the
                # line never names - "you don't need the perfect words" - which is the weaker
                # answer once the person is in the line; the other two carry the sentence to say.
                return NAMED_LOSS_SAY_REPLIES
            return SAY_REPLIES
        if PUTTING_REGRETTED.search(tight):
            # "i regret putting my dog down" is grief and a decision in one line. The sympathy
            # alone is the stock line STYLE.md rules out, and the cremation card alone is a cold
            # thing to hand a person who has just said they are sorry. Meet it, then offer the
            # one practical thing that is still theirs to sort out.
            return PUT_DOWN_REGRET_REPLIES
        habit = _still_here(line, words or tight.split())
        if habit:
            # "my dog died yesterday and i keep expecting to see him by the door": the death is in
            # the line and so is the habit, and the habit is the half they are telling us about.
            return habit
        if _a_hard_time_that_is_theirs(tight) and whose(line) == "own":
            # The last place the line can land is the plain sympathy pool, and that is the pool
            # meant for the person typing. "my mum is lonely since dad died" is not their
            # bereavement: the death is the reason for her loneliness, which is what they are
            # telling us about. Reached only when nothing more specific has taken the turn - a
            # "what do i say to them" line is already `whose` == "someone" and keeps its own
            # answer above.
            return THEIR_HARD_TIME_REPLIES
        return LOSS_REPLIES
    if not continues(memory):
        if _missing_someone(tight):
            # "i miss my mum" with no death mentioned and nothing to continue: the feeling is
            # there to be met, not a problem to be worked out, and not news to be sorry about.
            return MISS_REPLIES
        return None
    if dying_in_the_chat(memory) and (QUESTION.search(line) or _feeling(tight)):
        # Somebody at home is dying and the question is now about the person asking: "is it
        # normal to cry all the time" is not answered by the pool for after a death.
        return DYING_GRIEF_REPLIES
    if dying_in_the_chat(memory) and _the_visit_ask(tight):
        # "how do i say goodbye to her" two turns after "my carer is dying" is about the visit,
        # not about telling anyone the news.
        return DYING_SAY_REPLIES
    if (_thread_pool(memory) is MISS_REPLIES
            and not GRIEF_ASK_FORM.search(line) and not REFERS_TO_THEM.search(tight)
            and not _DEATH_IN_LINE.search(tight)
            and _a_body_with_its_own_answer(tight, tight.split())):
        # The thread was opened by "i miss my mum", so the missing is already said: what the body
        # is doing ("i cant sleep", "i keep waking at 3", "i have no appetite") is a practical
        # ask, and the answer modules have the answer for it. The company branch below reads
        # "keep" and "still" as still about them, which is why it has to be checked before it.
        # Asked as a grief question, or after a death said outright, the same words stay here:
        # "is it normal that i cant sleep" is the loss, and "my dad died last month" then "i cant
        # sleep" is a grief symptom, which the main thread tests pin down.
        return None
    if HELLO_ON_ITS_OWN.match(tight):
        # A hello two lines after the sympathy is a hello, not a new subject. Left to the
        # cheerful greeting the person gets "Morning! How's your day going?" right after a death
        # (chat, on main), and a second condolence would read as if they had said nothing.
        return HELLO_AFTER
    if OPEN_ASK.match(tight):
        # "what do i do now" is the question the whole chat is about, and the loss has the answer
        # for the stage it is at. Left to the entries it was a search hedge on every shape, and
        # after a dying animal it was the card for what to do with a body that is not gone yet.
        return _still_ahead(memory) or _first_days(memory)
    if marks_a_day(line, known=True) and asks_what_to_do(line):
        # "we always did a lunch for her birthday, i don't know what to do instead", a turn after
        # the sympathy: the day is the question, and the tradition is enough here because the
        # chat is already about the loss. It comes before the plain ritual answer, because a
        # question about the day is more than company.
        return REMEMBER_REPLIES
    if (not asking and _a_habit_in(tight + " " + line)
            and (continues(memory)
                 or _thread_pool(memory) in (MISS_REPLIES, AFTER_REPLIES, THE_HABIT_REPLIES))):
        habit = _still_here(line, tight.split())
        if habit:
            # "i keep expecting him to ring", "i still expect her at the door", a turn after "i
            # missed my dad": the habit is the one specific thing in the line, and the general
            # condolence said back to it ("I'm glad you said that out loud") tells a person their
            # line was not heard. `_still_here` already answers a habit said beside a death in
            # the same line; this asks it the same question one turn later, where the death is in
            # the thread and the habit is all the line has.
            return habit
    if (_thread_pool(memory) is MISS_REPLIES and not asking
            and STILL_ABOUT_THEM.search(tight)
            and not _a_question_about_the_feeling(line, set(tight.split()))
            and not _hands_over_a_detail(tight)):
        # "i miss my mum" then "she died two years ago" or "she taught me to bake": the person is
        # still the subject, so the company pool rather than "Noted!". The guard used to be
        # ASK_WORDS alone, which is only "what do i say to him", so every other question was
        # answered with company instead of its answer: "i miss my dog" then "what can i feed my
        # new puppy" lost the puppy food, and "i miss my mum" then "im fine actually" (the person
        # closing, not opening) got "I'm glad you said that out loud." A line that keeps the
        # person in it is the same thread; a question about anything else is that question.
        return AFTER_REPLIES
    if RITUAL.search(tight) and RITUAL_PERSON.search(tight):
        return AFTER_REPLIES
    if lost_a_thing(line):
        # "i lost my keys" a turn after sympathy is still a lost bunch of keys.
        return None
    if CARD.search(tight) and (ASK_WORDS.search(tight)
                               or (CARD_TO_WRITE.search(tight) and WRITE_WORD.search(tight))):
        return CARD_REPLIES
    if ASK_WORDS.search(tight):
        return SAY_REPLIES
    if (FUNERAL.search(tight) or WAKE.search(tight)) and asking and not _feeling(tight):
        if _when_asked(tight):
            return FUNERAL_WHEN_REPLIES  # when and where, whether it is the service or the wake
        return FUNERAL_REPLIES
    if GRIEF_POINTS_BACK.match(tight):
        # "does that stop", "will this always hurt": a question that points back at the feeling
        # and names nothing else is about the loss, whatever topic word the reader thought it
        # heard in it. It comes before the question guard below, which is there for a real
        # question with a subject of its own. "does it get easier" is the same question as
        # "is this normal", so a pet's death gets the animal in the answer here too.
        return _grief_replies(line, memory)
    words_now = tight.split()
    if QUESTION.search(line) and not (_names_a_subject(topics)
                                      and not _state_describes_them(words_now)
                                      and not _the_body_is_theirs(tight, words_now)):
        # The grief question shapes ("how long does it take", "why do i", "is it normal") are
        # about the loss only when nothing else in the line is being asked about. "how long do
        # i roast a chicken for" a turn after a death is a cooking question that happens to
        # start like a grief one, and the reader has already given it a subject of its own. The
        # state word still wins when it describes the person ("why do i still cry at the
        # mornings") - that is `_state_describes_them`, the same test the branch below uses.
        return _grief_replies(line, memory)
    said = set(words_now)
    if said & GRIEF_FEELINGS:
        # "i miss her", "the funeral is on friday": about the loss wherever they sit in the line.
        if _a_question_about_the_feeling(line, said):
            # "how do i stop feeling guilty", "i feel sad": the feeling is the whole subject and
            # the chat band answers it, so the condolence stands aside rather than saying
            # "that sounds heavy to be carrying" to a question.
            return None
        return AFTER_REPLIES
    if _about_family(words_now) and said & GRIEF_SELF:
        # "my mum isnt coping", "my grandad is struggling": the death is still the subject.
        return AFTER_REPLIES
    if REFERS_TO_THEM.search(tight) and _about_them(tight) and mood != "positive":
        # "i cant stop thinking about him", "i have to sort out her house and i cant face it":
        # still the person who died, still the grief.
        if IDEA_ASK.search(tight) or (asking and _own_subject(topics)):
            return None
        if _thread_pool(memory) is SAY_REPLIES:
            # "what do i say to him" then "its a workmate, i barely know him" is still the same
            # question about what to say, not the person's own bereavement.
            return SAY_REPLIES
        return AFTER_REPLIES
    if ABSENCE.search(line) and not asking:
        # "i still set the table for two", "the house feels empty", "i keep looking for him at the
        # door": the line says the absence, so a topic word in it ("table" -> food, "phone" ->
        # shopping) does not turn it into a question about that. A real question that happens to
        # carry the words ("how do i set a table for two") is still a question.
        return AFTER_REPLIES
    if (REASSURING.search(tight) and not asking and not _own_subject(topics)
            and not PEACE_IS_MINE.search(tight)):
        # "it was the right thing to do", "she had a good innings": the death was handled right
        # and the line is still about it. Said back as a fact it is a clerk's stamp; a question
        # that carries the same words keeps its own answer.
        return AFTER_REPLIES
    if _how_long_since(tight, words_now) and not _names_a_subject(topics):
        # "its been a year", "six months now": the gap is the whole of the line, and it is about
        # the person who died. Said back as a stock ack it told them they had said nothing.
        # `_names_a_subject` rather than `_own_subject` because "a year and a half" is read as
        # maths and numbers, and half a year said about the gap is still only the gap.
        return TIME_SINCE_REPLIES
    if _own_subject(topics) and not _state_describes_them(words_now):
        return None
    if (_about_them(tight) or TIME_OF_DAY.search(tight)) and _own_state(words_now):
        # "i still can't sleep", "some days i can't get out of bed", "the mornings are hard".
        return AFTER_REPLIES
    if any(phrase in tight for phrase in GRIEF_REFERRING + GRIEF_OBJECTS):
        # "does it get better", "the house feels so quiet without her".
        return AFTER_REPLIES
    if mood == "negative":
        return AFTER_REPLIES
    if ABSENCE.search(line):
        # "i keep expecting to see her" is the same death, said in the way people actually say
        # it in the second week: no grief word in the line at all.
        return AFTER_REPLIES
    if isinstance(topics, (list, tuple)) and topics:
        if not set(topics) - {"feelings", "health", "sleep"}:
            return _grief_replies(line, memory)
    if _missing_someone(tight):
        return MISS_REPLIES
    return None


# A tradition that now happens without the person: "we always did a lunch for her birthday, i
# don't know what to do instead". The words name a ritual, not a food, so this is company and
# not a recipe — the lunch entry used to answer it with a packed lunch in five minutes.
RITUAL = re.compile(r"\b(?:we (?:always|used to)|every year|her birthday|his birthday|"
                    r"their birthday|anniversary|(?:first )?(?:christmas|birthday|mothers day|"
                    r"fathers day) without)\b")
# A ritual is about the person who is missing, so the line has to name them or the day as well:
# "we always have pasta on fridays, what should i cook tonight" is a cooking question even inside
# a grief thread, and a camping trip "every year" is a travel question.
RITUAL_PERSON = re.compile(r"\b(?:her|his|their|mum|mom|mam|dad|mother|father|nan|nana|gran|"
                           r"granny|grandad|grandma|grandpa|husband|wife|partner|son|daughter|"
                           r"brother|sister|birthday|anniversary|christmas)\b")

# How far back a practical question can sit and still leave the death thread open.
THREAD_TURNS = 6


def asks_anything(line, tight=None):
    """True when the line puts a question, however it is written.

    One reading for the whole composer: "can we bury him at home" asks, "my dog died yesterday"
    does not, and "my cat died, should we bury her" asks in its second half. A bare "?" counts,
    and so does a wh-word or a modal at the front without one.
    """
    line = str(line or "")
    tight = _tight(line) if tight is None else tight
    return ("?" in line or bool(ASK_FORM.search(tight))
            or line.startswith(("what", "how", "should", "can", "do", "does", "is", "why",
                                "when", "where")))


# The papers, said in the second half of a line about a death ("my dad died, how long does
# probate take"): the estate admin has a factual answer and a grief pool has nothing to say
# about it, so this is the half of a practical ask that stands the condolences down.
# Only the paper words the grief band answers itself: probate, the estate, the will, the death
# certificate, the register office. "my dad died, is there a form to fill in" is not one of them -
# grief has no card for a bare "form", so standing the condolence down for it left the person with
# the composer's search shrug, which is colder still than the condolence it replaced.
PAPER_ASK = re.compile(
    r"\b(probate|grant of probate|letters of administration|estate|paperwork|solicitor|"
    r"wills|(?:the|his|her|their|my|our|a) will|inheritance tax|death certificate|"
    r"register (?:the |his |her |their )?death)\b")



# A thing asked for at a bedside. The halved shapes are how people say it - "i dont know what to
# bring him", "what should i take her" - and the nouns are the ones a gift entry keys on, so this
# only has to recognise the ask, not the present.
GIFT_THING_ASK = re.compile(
    r"\bwhat (?:to|should i|shall i|can i|could i|do i|would you|should we|can we|do we)\s+"
    r"(?:buy|bring|get|take|give|make)\b"
    r"|\bwhat (?:do|would|could|should) you\s+(?:buy|bring|get|take|give)\b"
    r"|\b(?:dont|don't|do not|not)\s+know what to\s+(?:buy|bring|get|take|give)\b"
    r"|\b(?:gift|present)\s+(?:idea|ideas)\b"
    r"|\b(?:a|any) gift\b")
# Somewhere a person is being cared for. A gift for someone in hospital is already the entry's
# line; hospice is the same place in the same words the person uses, and it was the one the entry
# did not know.
IN_CARE = re.compile(r"\b(?:hospice|hospital|ward|icu|hdu|hospice bed)\b")


# A thing taken to a funeral is not a thing taken to a bedside, and the line about the funeral is
# the funeral answer's ("my dad died in hospital, what do i bring to the funeral" belongs with the
# day itself, not with the phone cable). The ask is the same shape, so the reading has to look at
# what the thing is for.
NOT_A_BEDSIDE = re.compile(r"\b(funeral|funerals|wake|burial|cremation|memorial|service|"
                           r"church|grave|graveside|scattering)\b")


def _a_gift_for_someone_in_care(tight):
    """True for a gift asked for a person in care: the present entry answers it, not sympathy."""
    return bool(GIFT_THING_ASK.search(tight) and IN_CARE.search(tight)
                and not NOT_A_BEDSIDE.search(tight))


def is_practical_ask(line, tight=None):
    """True for a practical question inside a bereavement: what a funeral costs, probate.

    The composer does not answer these, and the person is still bereaved: "how long does probate
    take" followed by "i cant sleep" is one conversation, so this is also what `continues` reads
    to keep the thread open past the answer modules' reply.
    """
    line = str(line or "")
    tight = _tight(line) if tight is None else tight
    # A line opening with an interrogative word is a question even when it carries no question
    # mark and no ASK_FORM: "who pays for a funeral", "where is the funeral", "which funeral
    # director". The tuple of openers this reads elsewhere in the file has what, how, should,
    # can, do, does, is, why, when - but not who, where or which, so "who pays for a funeral"
    # read as a statement and got the condolence for somebody else's loss instead of the money
    # answer. Read here, where a practical question after a death is what stands the composer
    # down, rather than across the whole file.
    asking = (asks_anything(line, tight)
              or bool(re.match(r"\s*(?:who|who's|whos|whose|where|which)\b", tight)))
    # A question that arrives as the second half of a line - "my cat died, should we bury her",
    # "the cremation, is it expensive" - is only read as an ask by the pet card, which is what
    # the shape was added for. For everything else it made a person's death read as a practical
    # ask: "my mum died, is the cremation expensive" stood the condolences down and the composer
    # hedged, which is worse than the sympathy it replaced.
    opened_late = bool(ASK_WE.search(tight)) or bool(ASK_TAIL.search(line))
    if (FUNERAL.search(tight) or FUNERALS.search(tight)
            or WAKE.search(tight)) and a_part_of_the_day_asked(tight):
        # A part of the day - the music, the readings, the flowers, how long the service runs,
        # when the day is, whether the children come - is a practical question about the
        # arrangements, and each has a knowledge row. This is read here, with the price and the
        # probate, so it stands down before the line is read as a loss: "do kids go to funerals"
        # and "how long between death and funeral" name no death of their own and were answered
        # with a condolence for somebody the person had not mentioned.
        return True
    if (asking or opened_late) and PET_ARRANGEMENT.search(tight) and PET.search(tight):
        # "my cat died, should we bury her in the garden": the pets entry already answers what
        # to do with the body and that the vet can arrange a cremation or a home burial, so it
        # is the card that answers this, not a condolence. The line still leaves the thread open
        # (`continues` reads this function) and a person's body is not read here: there is no
        # card for that yet, and the honest condolence beats the honest shrug.
        return True
    if opened_late and PAPER_ASK.search(tight) and not GRIEF_CUE.search(tight):
        # The paperwork asked after the death in the same line is still the paperwork: "my dad
        # died, how long does probate take" was answered with the grief pool's "that is part of
        # grief for most people... tell your GP", which is an answer about the person's feelings
        # to a question about the estate, and the phone number for a doctor's appointment. The
        # grief band knows the probate answer itself, so the composer stands aside for it.
        # Only the papers, and not every practical word: reading a cost question the same way
        # ("my mum died, is the cremation expensive") stood the condolences down for a funeral
        # price, which is the colder reply on the day, and that is what this guarded before.
        return True
    return bool(asking and PRACTICAL.search(tight) and not GRIEF_CUE.search(tight)
                and not ASK_WORDS.search(tight))

# MISS_REPLIES is in the list so a line said after it ("she died two years ago", "i keep expecting
# him at the door") is still the same conversation rather than a fresh chat.
# GETTING_THROUGH_REPLIES is here for the same reason, and it was the one pool missing: it is the
# answer to the plea ("any thoughts"), so it is said *inside* the bereavement and the line after it
# is still that bereavement. Without it the module's own answer closed the thread it had just
# opened - "my dad died last week", "any thoughts" got the keeping-going line and then "any ideas"
# and "any tips" went back to the search hedge and the tips pool, which are the two lines the plea
# reading exists to delete. Every pool this file *says* is a pool the thread reads past.
POOLS = (LOSS_REPLIES, SAY_REPLIES, CARD_REPLIES, GRIEF_REPLIES, FUNERAL_REPLIES,
         FUNERAL_COST_COMPARE_REPLIES, FUNERAL_HELP_REPLIES,
         REMEMBER_REPLIES, FUNERAL_WHEN_REPLIES, AFTER_REPLIES, HELLO_AFTER,
         MISS_REPLIES, THE_ROUTINE_REPLIES, THE_HOUSE_REPLIES, THE_CANNOT_STOP_REPLIES,
         THE_HABIT_REPLIES, THE_JOBS_FOR_THEM_REPLIES,
         GETTING_THROUGH_REPLIES) + tuple(FEELING_REPLIES.values())


# An emergency inside a bereavement is answered by the safety band ("my mum died and i cant
# breathe" -> 999) and the chat is still that bereavement on the next turn. A chest pain does not
# un-bereave anyone, and going cold straight after an ambulance line is the coldest thing the bot
# could do, so the thread looks past an emergency rather than ending on it. The band's module is
# named here; a rename only stops the rule, it cannot misread a line.
SAFETY_MODULES = ("safety",)
# The fallback answers shrugs and stock notes, so a turn it answered does not open a thread. Any
# other module that answered a line about a death did so as a bereavement turn: the pet entry
# answers "my cat was put down last week", and the thread has to survive that just as it
# survives this file's own sympathy.
FALLBACK_MODULES = ("greeting",)


# How far back the ending can sit and still be the subject: the announcement, then a line or two
# of this file's own answers to it ("its been 3 weeks", "will it ever get better").
ENDING_TURNS = 3


def _an_ending_in_the_chat(memory):
    """True when the chat holds a break-up, so the gap and the how-long ask are about that.

    An ending is nobody's death, so `reads_as_loss` leaves those lines alone and the pools above
    never see them; the chat still holds an ending, and "its been 3 weeks" said after it is about
    that. It reads back past this file's own answers - the second and third follow-up in the same
    chat are still the same chat - and stops at the first turn that is something else, so an
    ending with a sleepless night or a job after it is history and those answers stand.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    stepped = 0
    while turns and stepped < ENDING_TURNS:
        said = str(turns[-1].get("user") or "")
        if AN_ENDING.search(said):
            return True
        if str(turns[-1].get("module") or "") not in ("loss", "grief"):
            return False
        turns, stepped = turns[:-1], stepped + 1
    return False


def continues(memory):
    """True when the bot's last line was sympathy or what to say, so this is still that chat.

    A safety answer does not end the thread: whatever was last said about the death still stands.
    When the death itself arrived inside the emergency ("my mum died and i cant breathe"), the
    sympathy was never said, so the line that was answered as an emergency is read instead.

    A practical question inside a bereavement is the same shape for a different reason: "how long
    does probate take" is answered by the answer modules, not by a pool, and the answer must not
    close the thread - the next line ("i cant sleep") is still about the person who died. So the
    thread reads past up to THREAD_TURNS of those turns, and it closes on any other kind of line.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    looked_past = False
    stepped = 0
    while turns and stepped < THREAD_TURNS:
        if str(turns[-1].get("module") or "") in SAFETY_MODULES:
            turns, looked_past = turns[:-1], True
            continue
        if is_practical_ask(turns[-1].get("user")):
            turns, looked_past, stepped = turns[:-1], True, stepped + 1
            continue
        break
    if not turns:
        if not looked_past:
            return False
        return any(reads_as_loss(str(turn.get("user") or ""))
                   for turn in (memory.get("turns") or []) if isinstance(turn, dict))
    last = str(turns[-1].get("bot") or "")
    if last and any(last in pool for pool in POOLS):
        return True
    # A death answered by another module ("my cat was put down last week" -> the pet entry) is a
    # bereavement turn too, as long as it was not the fallback that answered.
    module = str(turns[-1].get("module") or "")
    return bool(module) and module not in FALLBACK_MODULES + SAFETY_MODULES and reads_as_loss(
        str(turns[-1].get("user") or ""))
