"""Pets: dogs, cats, fish and small animals, in everyday plain advice.

The answers lane owns this domain. One Entry per question people really ask, keyed by
the animal and the problem, and where something could be serious it says when to ring
a vet rather than guess.
"""
import re

from .lookup import PRESENT_ASK, about_them, a_weight, entry, not_keeping_an_eye_on_it

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
# "what can a hamster eat" and "can guinea pigs eat bananas" are read as food-and-drink, because the
# food in the line is the word doing the work, so this domain has to answer that topic too or the
# pet food row is unreachable and the line falls to the kitchen table or the search hedge.
ANSWERS = ("pets", "food-and-drink")

# The names people type without ever saying "dog" or "cat": "my labrador is overweight" is a
# question about a dog and was answered with an adult's BMI. The animal's own names are the
# vocabulary of two things at once - a row about an animal can key on them, and a row about a
# person can fence them off - so they live here, once, and family.py and health.py import them.
# Distinctive breed names only: "boxer", "pointer", "setter" and "chow" are all everyday words
# as well, and an avoid word that fires on "boxer shorts" is a fence that blocks a real question.
DOG_BREEDS = ("labrador", "retriever", "golden retriever", "terrier", "jack russell", "staffie",
              "staffordshire", "spaniel", "cocker spaniel", "springer", "collie",
              "border collie", "sheepdog", "pug", "pugs", "beagle", "bulldog", "poodle",
              "rottweiler", "german shepherd", "alsatian", "dachshund", "sausage dog",
              "greyhound", "whippet", "lurcher", "chihuahua", "shih tzu", "husky", "cavapoo",
              "cockapoo", "bichon", "doberman", "dalmatian", "great dane", "saint bernard",
              "st bernard", "yorkie", "yorkshire terrier", "corgi", "pomeranian", "maltese",
              "schnauzer", "bullmastiff", "mastiff", "crossbreed", "cross breed", "mongrel",
              "sprocker", "cavoodle", "labradoodle", "goldendoodle")
CAT_BREEDS = ("persian", "maine coon", "siamese", "bengal", "ragdoll", "burmese", "sphynx",
              "british shorthair", "russian blue", "tortoiseshell", "calico", "moggie")
ANIMAL_NOUNS = ("dog", "dogs", "puppy", "puppies", "pup", "bitch", "doggy", "cat", "cats",
                "kitten", "kittens", "rabbit", "rabbits", "hamster", "hamsters", "guinea pig",
                "guinea pigs", "gerbil", "gerbils", "ferret", "ferrets", "parrot", "parrots",
                "budgie", "budgies", "horse", "horses", "pony", "ponies", "pet", "pets",
                "vet") + DOG_BREEDS + CAT_BREEDS


# By the time people write in about a new pet, the meeting has usually already happened and gone
# badly: "we got a puppy and the older dog hates him", "we got a kitten and our old cat hates it".
# Both introduction rows gated on the words of a question being asked (how, should, introduce) plus
# the noises of a first meeting (hiss, growl, swipe), so the plainest way of saying it - the animal
# already there does not want the new one - had no word either row wanted. The first line got the
# chat's name question and the second got the older-cat check-up, which is the wrong question about
# the wrong cat. A reaction word is therefore a way of asking for both rows, and the key of each
# still has to name the two animals, so "my dog hates the car" and "my cat hates being picked up"
# are not introduction questions.
# An animal's claw in a person is what the cat-scratch card is written for, so the line has to
# name the animal. The row keys on the shape the wound comes in, and one of those shapes is
# "scratching my", which the loose forms also read as "scratched my" - so "i scratched my arm"
# carries two signals (that shape and "my arm") and gets "Wash a cat scratch under running water"
# with no animal in the line while the person has scratched themselves. The shapes that do name
# the animal ("cat scratch", "scratched by a cat") still carry it, so the card stands aside only
# when nothing in the line is an animal.
_THE_CLAW_ANIMALS = frozenset(word for word in ANIMAL_NOUNS if word not in ("vet", "vets"))


def _an_animal_did_it(understood):
    """True only when the line names the animal whose claw the wound came from."""
    words = " " + " ".join((understood or {}).get("words") or ()) + " "
    return any(f" {word} " in words for word in _THE_CLAW_ANIMALS)


_NEW_ANIMAL_REACTION = (
    "hates", "hate", "hated", "hates the", "hates him", "hates her", "hates it",
    "doesnt like", "doesn't like", "does not like", "not happy about", "not happy with",
    "unhappy about", "jealous", "jelous", "resentful", "terrified of", "scared of the",
    "afraid of the", "hiding from", "hides from", "hiding under", "snaps at", "snapped at",
    "snarling at", "snarls at", "wont leave", "won't leave", "wont accept", "won't accept",
    "wont go near", "won't go near", "rejecting", "not accepting", "bullied by",
    "picks on", "picking on", "keeps attacking", "keeps going for", "keeps swiping",
    "got a puppy", "got a kitten", "we got", "ive got a new", "got a second",
)


# A hiss, a growl or a swipe is a warning, and the answer has to lead with the warning rather than
# with the rod toy: a cat who has started hissing at her owner, or growling when she is picked up,
# is saying stop, and the first thing to say is give her the space. A cat who bites a hand while it
# plays is the other question, and the play answer is right for that one.
_CAT_WARNING = ("hiss", "hisses", "hissing", "growl", "growls", "growling", "lunge", "lunges",
                "lunging", "aggressive", "aggression", "went for", "goes for", "go for",
                "lashes out", "lashing out", "snarl", "snarls", "snarling")

# A dog's age is a number the line states, and it decides which of the age rows answers: a six
# month old dog is not an old dog, and a two year old is in its prime. The senior row's key holds
# the phrase "old dog", which is inside "month old dog", "week old dog" and "year old dog", so
# every young dog with an age in front of it was getting "For an older dog: a warm, soft bed...".
# The fix is a reading of the stated age, not a list of young phrases: a line that says how old
# the dog is can be answered by that number, and a line that only says "old" or "senior" has no
# number to disagree with.
_AGE_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
              "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
              "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
              "nineteen": 19, "twenty": 20, "a": 1, "half a": 0.5}
_AGE_PATTERN = re.compile(
    r"\b(\d{1,2}|half a|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen"
    r"|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\s*"
    r"(years?|yrs?|yo|months?|mths?|weeks?|wks?)\s*(?:old\b|of age\b)")
# A dog is senior from about seven: giant breeds a little earlier, small breeds later, so the
# number only has to settle the young end, which is where the phrase key was wrong.
_DOG_SENIOR_YEARS = 7


def _dog_age_years(understood):
    """The age a line states for an animal, in years, or None when it states none."""
    text = " " + str((understood or {}).get("clean")
                     or (understood or {}).get("text") or "").lower() + " "
    found = _AGE_PATTERN.search(text)
    if not found:
        return None
    raw, unit = found.group(1), found.group(2)
    number = _AGE_WORDS.get(raw)
    if number is None:
        try:
            number = float(raw)
        except ValueError:
            return None
    if unit.startswith(("month", "mth")):
        return number / 12.0
    if unit.startswith(("week", "wk")):
        return number / 52.0
    return float(number)


_DOG_STIFF = frozenset(("stiff", "stiffness", "stiffening", "limp", "limping", "limps", "lame",
                        "lameness", "arthritis", "arthritic", "hips", "hip", "dysplasia",
                        "slowing", "slow", "slower", "sore", "aching", "aches", "painful"))


# The sport and the pet are spelt with one word. "my dad is 62 and he loves fishing" is a
# present for a man with a rod; it was answered "A new fish needs the tank ready before it goes
# in: a filter running, water treated with a dechlorinator, and the tank cycled for four to six
# weeks", because "fishing" carries "fish" and "loves" carries nothing else the row needs.
# An `avoid` word cannot fence this off - a loose form of the row's own key word is skipped when
# the row scores itself - so the angling words are a guard on the reading instead.
_FISHING_SPORT = frozenset((
    "fishing", "fished", "fisherman", "fishermen", "angler", "anglers", "angling",
    "rod", "rods", "reel", "reels", "tackle", "bait", "maggots", "fly", "coarse",
    "spinner", "lure"))

# A fish that is ill, in water or newly bought is a pet whatever else the line says, so the
# guard asks first whether a fish being kept is named at all.
_FISH_CARE = frozenset(("tank", "tanks", "goldfish", "guppy", "guppies", "betta", "koi",
                        "bowl", "aquarium", "filter", "pond", "water", "ill", "sick",
                        "dying", "dead", "white", "spots", "fin", "gills", "swimming",
                        "bottom", "surface", "floating", "eating", "feed", "feeding"))


def _fish_not_the_sport(understood):
    """False when the line is the sport of fishing and not a fish being kept.

    "my dad loves fishing", "he is into fly fishing", "a fishing rod for his birthday" are all
    the hobby: no fish of the person's own is named, so the aquarium rows stand down and the
    present rows, or whatever else fits, answer instead. A line that does name a fish being kept
    - "my goldfish is lying on the bottom", "a new fish for the tank", "the fish in my pond" -
    keeps the row even when it also says "fishing".

    The angling words are a guard and not an `avoid` because a loose form of the row's own key
    word is skipped when the row scores its own avoid: "fishing" holds "fish", so an avoid of
    "fishing" fences nothing off.
    """
    clean = " " + str((understood or {}).get("clean")
                      or (understood or {}).get("text") or "").lower() + " "
    words = set(re.findall(r"[a-z']+", clean))
    if words & _FISH_CARE:
        return True
    return not (_FISHING_SPORT & words)


def _dog_not_young(understood):
    """True unless the line says the dog is under seven, which is not an older dog.

    A line with no age in it keeps the row: "my dog is old and stiff" and "my senior dog is
    slowing down" say it in words and there is no number to disagree with.
    """
    years = _dog_age_years(understood)
    if years is None or years >= _DOG_SENIOR_YEARS:
        return True
    clean = " " + str((understood or {}).get("clean")
                      or (understood or {}).get("text") or "").lower() + " "
    return bool(_DOG_STIFF & set(re.findall(r"[a-z']+", clean)))


# "Tablet" is a dog's medicine and a child's computer, and "bone" is something swallowed and
# something taken away. Score counts two of a key's three parts, so "can i give my dog a bone" was
# the tablet card (dog, give) and "my dog swallowed a chicken bone" the guarding one (dog, bone).
# The word that makes each line theirs is the one the row now requires: a medicine in the line for
# the tablet card, a warning in the line for the guarding card.
_A_MEDICINE_WORD = frozenset((
    "pill", "pills", "tablet", "tablets", "medicine", "medication", "medicines", "capsule",
    "capsules", "worming", "wormer", "drops", "antibiotic", "antibiotics", "inhaler",
))
_A_WARNING_WORD = frozenset((
    "growl", "growls", "growled", "growling", "snap", "snaps", "snapped", "snapping",
    "snarl", "snarls", "snarled", "snarling", "guard", "guards", "guarding", "guarded",
    "possessive", "protective", "bares", "baring", "lunge", "lunges", "lunged",
))


_A_HELD_WORD = frozenset((
    "his", "her", "their", "bone", "bones", "food", "bowl", "dinner", "toy", "toys", "chew",
    "treat", "treats", "bed", "rawhide", "kong", "slipper", "ball", "stick", "near", "take",
    "takes", "taking", "took", "touch", "touches", "grabs", "grab", "shares", "sharing",
))


def _a_medicine_line(understood):
    """True when the line itself names a medicine, which is what makes the pet's line the pet's."""
    clean = " " + str((understood or {}).get("clean")
                      or (understood or {}).get("text") or "").lower() + " "
    return bool(_A_MEDICINE_WORD & set(re.findall(r"[a-z']+", clean)))


_HANDLING_WARNING = frozenset((
    "growl", "growls", "growling", "growled", "snap", "snaps", "snapped", "snapping",
    "snarl", "snarls", "snarled", "snarls", "nips", "nipped", "nippy",
))


_HANDLING_WORD = frozenset((
    "brush", "brushing", "brushed", "groom", "grooming", "groomed", "groomer", "groomers",
    "nail", "nails", "claw", "claws", "clip", "clipping", "clippers", "paw", "paws", "feet",
    "harness", "collar", "lead", "bath", "bathe", "bathing", "wash", "washing", "towel",
    "wipe", "touch", "touched", "touching", "handling", "handled", "lift", "lifted",
    "pick", "picked", "hold", "holding", "held", "ears", "ear", "teeth",
))


def _a_handling_growl_line(understood):
    """True when the line says the warning and the handling, which is what this row answers.

    A dog that will not be brushed, or hates the brush, is a grooming question and has the
    grooming card. A growl or a snap while he is being handled is the warning that comes before
    a bite, and that is the only thing this row is about. The handling word has to be there too:
    "my dog growls at my husband" is a shy dog's question and has the shy dog's card, and the
    matching alone was loose enough to give it the brushing answer.
    """
    clean = " " + str((understood or {}).get("clean")
                      or (understood or {}).get("text") or "").lower() + " "
    words = set(re.findall(r"[a-z']+", clean))
    return bool(_HANDLING_WARNING & words) and bool(_HANDLING_WORD & words)


def _a_guarding_line(understood):
    """True when the line is about something held and a warning over it, not a growl on its own.

    A dog that growls at a husband, at other dogs or at the vet is shy or reactive and has its own
    cards: guarding needs the thing that is kept, or the hand going near it.
    """
    clean = " " + str((understood or {}).get("clean")
                      or (understood or {}).get("text") or "").lower() + " "
    words = set(re.findall(r"[a-z']+", clean))
    return bool(_A_WARNING_WORD & words) and bool(_A_HELD_WORD & words)


_A_TEETH_SHOW = frozenset((
    "bares", "bared", "baring", "shows", "showed", "showing", "showed",
))


# A puppy that snaps at a hand is mouthing, not warning, and the mouthing card is the one that
# answers it ("yelp or say ow and stop the game"). The same word from an adult dog is a warning,
# so only the puppy with hands or play in the line stands the warning row down.
_A_LITTLE_ONE = frozenset(("puppy", "puppy's", "puppies", "pup", "pups", "doggy"))


_HANDS_OR_PLAY = frozenset((
    "hand", "hands", "finger", "fingers", "thumb", "wrist", "play", "playing", "played", "game",
    "games", "mouth", "mouths", "mouthing", "mouthed", "nip", "nips", "nipping", "nipped", "toy",
    "toys", "trousers", "sleeve", "sleeves", "shoelaces", "ankles",
))


def _a_warning_sound_said(understood):
    """True when the line itself has a growl, a snarl, a snap or bared teeth in it.

    The `dog-warning` key's third part holds the places and the handling that set a warning off
    ("when i touch his back", "his collar"). Those words carry the row's score on their own, which
    put "my dog yelps when i touch his back" - a pain question with no warning in it at all - on
    the warning card, so the sound is asked for alongside the key.

    "my puppy snaps at my hands" is the mouthing card's line and not this one: a snap at a hand in
    play is a puppy with teeth, and the answer for it is to yelp and end the game, not to see a
    behaviourist. The puppy and the hand have to be on the line together for that.
    """
    clean = " " + str((understood or {}).get("clean")
                      or (understood or {}).get("text") or "").lower() + " "
    words = set(re.findall(r"[a-z']+", clean))
    if words & _A_LITTLE_ONE and words & _HANDS_OR_PLAY:
        return False
    if words & (_A_WARNING_WORD - {"guard", "guards", "guarding", "guarded",
                                   "possessive", "protective"}):
        return True
    return "teeth" in words and bool(words & _A_TEETH_SHOW)


def _cat_biting(memory, understood):
    clean = " " + ((understood or {}).get("clean") or "").lower() + " "
    warning = any(re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", clean)
                  for word in _CAT_WARNING)
    if not warning:
        return ("Hands are not the toy: play with a rod toy on a string and put it away after ten "
                "minutes, twice a day, because an under-exercised cat bites. Watch for the warning "
                "- tail flicking, ears back, skin twitching along the back - and stop stroking "
                "before it, since most bites are a cat asking for a break. A bite that comes out "
                "of nowhere in a calm cat is worth a vet visit, because pain or a bad tooth is "
                "often behind it.")
    return ("Take the warning as a no and give her the space: put her down or step back, stop what "
            "you were doing, and let her come to you rather than picking her up to show her it is "
            "fine. Never tell a cat off for hissing or growling - a cat punished for the warning "
            "skips it and goes straight to the bite - and give her somewhere high to get away to, "
            "because most of this is a cat with no escape route. Watch for the tail flick, the "
            "ears going back and the skin twitching along the back, and stop stroking before "
            "those. A cat who suddenly hisses or growls at someone she knows, or when she is "
            "picked up, needs a vet: pain, a bad tooth or arthritis is the usual reason, and this "
            "is often the first sign of it.")


# A cat and a baby in the same house is a different answer for a woman already expecting one:
# her question is the litter tray and toxoplasmosis, and it has to be the first sentence, not the
# last paragraph of the house rules. "is it safe to have a cat when pregnant" and "can i keep a
# cat when i am pregnant" were answered with "Yes - a cat and a baby are fine together", which
# tells her nothing she asked. (A cat's own pregnancy is in the entry's avoid list, so this is
# always the household's baby.)
_A_CREATURE = re.compile(
    r"\b(?:slugs?|snails?|bees?|wasps?|hornets?|bumblebees?|frogs?|toads?|beetles?|spiders?|"
    r"caterpillars?|woodlouse|woodlice|worms?|moths?|insects?|daddy long legs)\b")


def _an_eaten_creature(understood):
    """True only when the line names the creature, so "my dog ate a mushroom" is not this card.

    The scorer wants two signals, and an animal plus an eating verb is already two, so the third
    group has to be checked here: without it "my dog ate a mushroom in the garden" was told about
    lungworm.
    """
    reading = understood or {}
    line = str(reading.get("clean") or reading.get("text") or "").lower()
    return bool(line and _A_CREATURE.search(line))


# A mushroom is not a creature but it is the same kind of line - something has already gone down
# and the question is what to do now - and it needs the vet rather than a training tip. "my dog
# ate a mushroom in the garden" was answered with "teach 'leave it'" once the lungworm card was
# fenced off it, because the scatter for "dog" plus "ate" was all that was left.
_A_FUNGUS = re.compile(
    r"\b(?:mushrooms?|toadstools?|fungus|fungi|shrooms?|field mushrooms?|death ?caps?)\b")


# Something has already gone down, or is going down now: "ate", "has eaten", "is eating",
# "swallowed", "chewed", "licked", "nibbled", "got hold of", "keeps eating". The bare present is
# not on the list on purpose. "Can dogs eat mushrooms", "is it ok if my dog eats mushrooms" and
# "are mushrooms bad for dogs" ask whether a mushroom is safe, and nothing has happened yet:
# telling a person to ring the vet before any symptoms is the ordinary question treated as an
# emergency, which is the worst thing this card can do. The same verb, in the past, is the
# emergency and keeps it.
_A_FUNGUS_HAS_GONE_DOWN = re.compile(
    r"\b(?:ate|eaten|eating|swallowed|swallowing|licked|licking|chewed|chewing|nibbled|"
    r"nibbling|tasted|tasting|got hold of|got a|got one|got into|has had|had a|just had|"
    r"keeps? eating|kept eating|been eating)\b")


def _an_eaten_fungus(understood):
    """True only when the line names the fungus AND something has already gone down.

    The key can be earned with the present tense ("can dogs eat mushrooms" holds an animal, a
    fungus and "eat"), so the guard has to read the tense as well as the subject: a question
    about whether mushrooms are safe for a dog is not a dog that has eaten one, and it must not
    get "ring the vet now, before any symptoms".
    """
    reading = understood or {}
    line = str(reading.get("clean") or reading.get("text") or "").lower()
    return bool(line and _A_FUNGUS.search(line) and _A_FUNGUS_HAS_GONE_DOWN.search(line))


_PREGNANT_SELF = ("pregnant", "pregnancy", "expecting a baby", "expecting our", "due in",
                  "trimester", "weeks to go", "having a baby", "baby due")


def _cat_and_baby(memory, understood):
    said = " " + ((understood or {}).get("clean") or "").lower() + " "
    said += " ".join((turn.get("user") or "").lower()
                      for turn in (memory.get("turns") or [])[-2:]) + " "
    expecting = any(re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", said)
                    for word in _PREGNANT_SELF)
    if expecting:
        return ("Yes - keep the cat, and the one job to sort out before the baby comes is the "
                "litter tray: someone else should empty it every day while you are pregnant, or "
                "if you have to do it yourself, wear disposable gloves and wash your hands after, "
                "because toxoplasmosis - a parasite a cat picks up from raw meat and soil - can "
                "harm an unborn baby. A cat that stays indoors and eats tinned or cooked food "
                "carries almost no risk, and the other route is garden soil, so wear gloves for "
                "the weeding too. Wash fruit and veg and cook meat through, and that is the lot. "
                "When the baby arrives: the cot, the pram and the bouncy chair are out of bounds "
                "from day one, keep the door of the room the baby sleeps in shut, never hold the "
                "baby and the cat at once, give her somewhere high to get away to, keep her "
                "routine exactly as it is now, and have someone bring home a blanket the baby "
                "has slept on so the smell is familiar before they meet.")
    return ("Yes - a cat and a baby are fine together, and the house rules do the work: the cot, "
            "the pram and the bouncy chair are out of bounds from day one, so keep the cat out of "
            "the room the baby sleeps in and shut the door rather than shooing her away from the "
            "cot later. Never leave them alone in a room, and never hold the baby and the cat at "
            "the same time, because a startled cat scratches whatever is nearest. Cut the cat's "
            "claws out of the equation by giving her somewhere high to get away to, keep her "
            "routine the same as before the birth, and have someone bring home a blanket the baby "
            "has slept on so the smell is familiar before they meet. If you are pregnant, let "
            "someone else empty the litter tray and wear gloves for the garden, because of "
            "toxoplasmosis - a cat that stays indoors and is fed cooked or tinned food carries "
            "almost no risk.")


# Why to do it, by animal: the case is different enough that one paragraph answers it badly for
# the others - a cat is about litters and spraying, a dog about tumours and timing, a rabbit about
# uterine cancer.
NEUTER_WHY = (
    (("rabbit", "rabbits", "bunny", "bunnies"),
     "Yes, especially for a doe: by four or five an unneutered female rabbit has uterine cancer in "
     "the great majority of cases, and neutering takes that away. A buck is done for the spraying "
     "and the mounting, and two rabbits get on far better once both are done."),
    (("cat", "cats", "kitten", "kittens", "tom", "tomcat", "queen"),
     "Yes: a spayed cat is out of the annual litters (a cat can have three a year), stops the "
     "calling that keeps the house awake, and a queen spayed before her first season has a much "
     "lower risk of mammary tumours. A tom stops spraying and fighting once he is done. The age "
     "is the only real question, and for a cat it is young - about four months."),
    (("dog", "dogs", "puppy", "puppies", "bitch", "bitches"),
     "Usually yes. For a bitch, spaying before her first season cuts the risk of mammary tumours "
     "a long way and removes pyometra, which is an emergency operation; for a dog it stops the "
     "roaming, marking and fights and removes the risk of testicular cancer. The trade-off is "
     "timing: in a large or giant breed, neutering before the growth plates close is linked to "
     "joint trouble later, so many vets wait until 12 to 18 months. Ask your vet about the breed "
     "and size - the answer is usually yes, at the right age."),
)


# The other side of the question, for the lines that ask it: "why should i not neuter my dog",
# "reasons not to neuter my cat". Standing the case for down leaves those lines to the timing
# card, which answers a question nobody asked, so the row answers the one it was asked - honestly,
# because the case is not one-sided and the trade-offs are the same ones the case for is weighed
# against.
NEUTER_AGAINST = ("It is not one-sided. The operation is a general anaesthetic, which is very safe "
                  "in a healthy young animal but is the one real risk, and in a large or giant "
                  "breed neutering before the growth plates close is linked to joint trouble "
                  "later, which is why many people wait until a year or more. What waiting takes "
                  "on is everything the operation removes: pyometra, a womb infection that needs "
                  "an emergency operation, and mammary tumours in a female; and the roaming, "
                  "marking and fights in a male. Ask your vet about the timing for your animal - "
                  "most will talk the trade-off through rather than push a date.")
NEUTER_AGAINST_RABBIT = ("For a doe the other side is thin: by four or five an unneutered female "
                         "rabbit has uterine cancer in the great majority of cases, so the risk of "
                         "waiting is far larger than the risk of the anaesthetic. A buck is done "
                         "for the spraying and the mounting, and the operation is routine in a "
                         "rabbit that is healthy and eating.")


# The animals the three paragraphs above are not written for. A horse or a rat is done for other
# reasons, and handing it the dog's paragraph said things that are not true of it - a male rat has
# no seasons and no uterus, so "spaying before the first season cuts the risk of mammary tumours"
# is a confident answer about the wrong animal. A line that names one of these gets no answer from
# this row, which is what a person with a horse deserves rather than a dog's case.
NEUTER_NOT_WRITTEN_FOR = ("horse", "horses", "pony", "ponies", "donkey", "donkeys", "rat", "rats",
                          "mouse", "mice", "hamster", "hamsters", "gerbil", "gerbils",
                          "guinea pig", "guinea pigs", "ferret", "ferrets", "bird", "birds",
                          "parrot", "parrots", "parakeet", "parakeets", "budgie", "budgies",
                          "reptile", "reptiles", "snake", "snakes", "lizard", "lizards",
                          "tortoise", "tortoises", "chicken", "chickens", "goat", "goats",
                          "pig", "pigs", "sheep", "cow", "cows", "calf", "calves")

# "Why should i not neuter my dog" is the other side of the question, and answering it with the
# case for is answering the opposite of what was asked. Every other row in the store stands down
# on a negation rather than reading past it, so this one does too: the line goes to whatever else
# can take it ("what are the downsides" has its own answer) instead of an argument against itself.
# Only a real negation belongs here. "pros and cons of neutering a dog" and "what are the
# downsides" were this row's own lines before (answered with the case for, which a person asking
# for both sides can read as the pros half), and standing them down sent them to the timing card,
# a different question again.
NEUTER_SAYS_NOT = re.compile(r"\b(?:not|never|shouldnt|shouldn't|dont|don't|wouldnt|wouldn't|"
                             r"against|opposed)\b")


def _neuter_why(memory, understood):
    """The health case for neutering the animal named."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    against = bool(NEUTER_SAYS_NOT.search(said))
    for names, text in NEUTER_WHY:
        if any(re.search(r"\b%s\b" % re.escape(name), said) for name in names):
            if against:
                # the case against, for the animal named, in the animal's own terms
                if names[0] == "rabbit":
                    return NEUTER_AGAINST_RABBIT
                return NEUTER_AGAINST
            return text
    if any(re.search(r"\b%s\b" % re.escape(animal), said)
           for animal in NEUTER_NOT_WRITTEN_FOR):
        return None
    if against:
        return NEUTER_AGAINST
    return ("Usually yes. Spaying before the first season cuts the risk of mammary tumours and "
            "removes pyometra, an emergency operation; neutering a male stops the roaming, "
            "spraying and fights. The one trade-off is timing in a large dog, where vets often "
            "wait until it has stopped growing - so ask about the breed and the size you have.")


# The words that make a neutering line the why-question rather than the when-question. The timing
# row answers "when", "what age", "how old" and an age in the line; a person asking whether it is
# worth doing wants the case for it, and gets a date instead.
# "cons" is left out on purpose: the typo reader turns it into "comes", so it matches nothing
# and only makes the row look like it covers a phrase it does not. "pros" carries that line.
NEUTER_WHY_WORDS = ("why", "reason", "reasons", "point of", "point in", "benefit", "benefits",
                    "pros", "pros and cons", "cons and pros", "worth it", "worth doing",
                    "is it worth", "good idea",
                    "should i", "should we", "should you", "had it done", "get it done",
                    "do people", "positive", "advantage", "advantages")

# A person weighing up whether to have a cat at all is not asking what to buy for one.
# "should i get a cat", "im thinking of getting a cat" and "is it worth getting a cat" want the
# trade that settles it (opinions.py's `decide-a-choice`), and the shopping list answered them
# because "getting a cat" is one of this row's own phrases. The shapes are read with the animal
# as the object of the getting, and a line that also asks what to get *for* it - "what should i
# get for a new kitten", "im thinking of getting a cat what do i need", "should i get a cat
# flap" - keeps the list, which is the list's own question.
_WEIGHING_UP = re.compile(
    r"\b(?:should|shall)\s+(?:i|we)\s+(?:get|have|buy)\s+(?:a|an|another|one)\s+(?:cat|kitten)\b"
    r"|\b(?:thinking|thought|toying|tempted|torn|unsure|wondering)\b[\w\s,']{0,25}"
    r"\b(?:of|about|between|on)\b[\w\s,']{0,25}\b(?:getting|having|buying|cat|kitten)\b"
    r"|\b(?:is it |it )?worth\s+(?:getting|having|buying)\s+(?:a|an|another)?\s*(?:cat|kitten)\b"
    r"|\b(?:on the fence|two minds|not sure whether|deciding whether)\b[\w\s,']{0,30}"
    r"\b(?:cat|kitten)\b")
# What the line asks about the cat itself rather than whether to have one.
_FOR_THE_CAT = re.compile(
    r"\b(?:need|needs|buy|buying|shop|shopping|list|checklist|supplies|kit|need to get|have to get)"
    r"\b|\b(?:flap|litter|tray|trays|bed|beds|carrier|bowl|bowls|food|toys?|collar|microchip)"
    r"\b|\bwhat (?:should|do) i (?:get|need)\b|\bwhat to (?:get|buy)\b")
# "im thinking of getting two kittens" is still a line this list answers: what two of them need is
# a tray each plus one and two of everything, and the trade about having one at all is not it.
_TWO_OF_THEM = re.compile(r"\btwo (?:cats|kittens)\b|\bpair of (?:cats|kittens)\b",
                          re.IGNORECASE)


def _kitten_kit(memory, understood):
    """Supplies for a new cat or kitten; "food for its age" as most of these lines say "cat"."""
    said = " " + " ".join(str((understood or {}).get("clean")
                             or (understood or {}).get("text") or "").lower().split()) + " "
    if _WEIGHING_UP.search(said) and not _FOR_THE_CAT.search(said) \
            and not _TWO_OF_THEM.search(said):
        return None
    words = set((understood or {}).get("words") or ())
    food = "kitten food" if {"kitten", "kittens"} & words else "food for its age"
    return ("Litter tray and litter, two bowls, a scratching post, a carrier, a soft bed and "
            f"{food}, plus a vet visit booked for the first week. A second litter tray and a few "
            "toys save a lot of trouble, and nothing stringy or small enough to swallow.")


# A rabbit and a guinea pig are the same question in the same words - "what do i need for a
# rabbit", "how do i look after a guinea pig" - and the answer is not the same animal. The card
# named rabbits and answered for both, so "what do i need for a guinea pig" was told to buy a
# hutch for a rabbit, and "what do i need for a rabbit" reached the cooking row for rabbit meat,
# because "need" is an asking-frame word: it is read as the frame and the animal was left as the
# only word of the key. One handler, keyed on the animal the line names, and an `ask` so the
# buying shape counts for the row.
_SMALL_PET_KIT = {
    # main's own guinea-pig text, kept word for word: this table exists so the card can answer
    # the other half of its question (the cleaning), not to reword the set-up
    "guinea pig": (
        "A guinea pig needs a hutch with a big run attached, or a shed with floor space, hay "
        "all day and a handful of nuggets with vitamin C in them, since they cannot make "
        "their own. Keep two rather than one - a guinea pig on its own is a lonely animal - "
        "and skip the small cage."),
}
_SMALL_PET_KIT["rabbit"] = (
    "A rabbit needs a hutch with a run attached, or a big shed, plus hay all day, a water bottle, "
    "a litter tray, bedding, a carrier for the vet and a friend of its own kind. A small cage "
    "with an hour out is not enough for a rabbit, and hay is most of what it eats: it wears the "
    "teeth down and keeps the gut moving.")
# The buying shape: "what do i need for a rabbit", "what should i get before we get a guinea
# pig", "what do i need to buy for one". A line that asks what to get *for* the animal is the
# set-up question, and this is what says so once "need" has been read as the asking frame.
_BUYING_FOR = re.compile(r"\b(?:need|needs|needed|want|wants|get|gets|buy|buys|getting|buying)"
                         r"\b[\w\s,']{0,24}\b(?:for|before)\b")


def _the_buying_shape(text):
    return bool(_BUYING_FOR.search(str(text or "").lower()))


_GUINEA_PIG_RE = re.compile(r"\b(guinea ?pigs?|guineas?|cav(?:y|ies))\b")
_RABBIT_RE = re.compile(r"\b(rabbits?|bunn(?:y|ies))\b")
_HAMSTER_RE = re.compile(r"\b(hamsters?|syrian|dwarf hamster)\b")

# Every husbandry card has the same two faults: it answers for the animal it was written for
# whatever animal the line names, and it answers the half of the card the writer had in mind
# rather than the half that was asked. So the animal is read once, here, and each question
# (the set-up, the cleaning, the yearly visit, the litter tray) is one table keyed by animal.
# A card that has a table asks it instead of keeping its own copy of the answer.
_PET_NAMES = (
    ("guinea pig", _GUINEA_PIG_RE),
    ("rabbit", _RABBIT_RE),
    ("hamster", _HAMSTER_RE),
    ("tortoise", re.compile(r"\b(tortoises?|tort|terrapins?)\b")),
    ("bird", re.compile(r"\b(budgies?|parrots?|cockatiels?|canar(?:y|ies)|parakeets?)\b")),
    ("fish", re.compile(r"\b(goldfish|fish|koi|betta|gupp(?:y|ies))\b")),
    ("cat", re.compile(r"\b(cats?|kittens?)\b")),
    ("dog", re.compile(r"\b(dogs?|pupp(?:y|ies))\b")),
)


def _the_pet_named(memory, understood, default=None):
    """The animal the line names, else the one the chat was last about, else `default`.

    A new owner says "we are getting a guinea pig" and then "can i keep just one": the second
    line names no animal at all, and answering it with the rabbit card is how the set-up answer
    and the companion answer both went to the wrong animal. `default` is None at the call site
    that must not guess: a dog line is not a rabbit line because a rabbit came up earlier.
    """
    said = [_said(understood)]
    if isinstance(memory, dict):
        said += [str((turn or {}).get("user") or "").lower()
                 for turn in (memory.get("turns") or [])[-3:]][::-1]
    for line in said:
        for name, pattern in _PET_NAMES:
            if pattern.search(line):
                return name
    return default


def _the_small_pet(memory, understood):
    """The small animal this card is about: the one named, or the one the chat was about."""
    return _the_pet_named(memory, understood, default="rabbit")


# How often the hutch is cleaned is the same card's other question, and the set-up list answered
# it: "how often should i clean the rabbit hutch" came back as things to buy.
_CLEANING_ASK = re.compile(r"\b(?:clean|cleans|cleaning|clean out|clean it out|cleaned|scrub|"
                           r"disinfect|smell|smells|smelly|stinks|wash|washing)\b")
_PET_CLEANING = {
    "rabbit": (
        "Spot-clean the wet corner and the litter tray every day, change the bedding once a week "
        "and give the hutch a deep clean once a month: rabbit urine soaks into wood and the "
        "ammonia it gives off damages their lungs. Use a pet-safe disinfectant or a 1:10 white "
        "vinegar solution, rinse and dry it before the rabbit goes back in, and skip the phenolic "
        "ones like Jeyes fluid - they are toxic to small animals. Vinegar is also what takes the "
        "chalky white urine marks off the floor."),
    "guinea pig": (
        "Spot-clean the wet corner and the litter tray every day, change the bedding once a week "
        "and give the cage a deep clean once a month: guinea-pig urine soaks into wood and the "
        "ammonia it gives off damages their lungs. Use a pet-safe disinfectant or a 1:10 white "
        "vinegar solution, rinse and dry it before the guinea pigs go back in, and skip phenolic "
        "ones like Jeyes fluid. Keep a handful of the old bedding to put back, because a cage "
        "that smells completely new makes them nervous."),
    "hamster": (
        "Spot-clean the wet corner every day and change the bedding every few weeks, with a full "
        "scrub of the cage once a month: hamster urine is concentrated and the ammonia builds up "
        "fast in a small cage. Hot soapy water or a pet-safe cleaner, rinsed and dried right "
        "through before the bedding goes back, because a damp cage gives a hamster a chill and a "
        "chest infection. Put a handful of the old bedding back in the nest so the cage still "
        "smells of home."),
}


# The set-up of each small animal, so a caretaker card can answer the cleaning question without
# answering it with a shopping list.
_PET_SETUP = dict(_SMALL_PET_KIT)
_PET_SETUP["hamster"] = (
    "A hamster needs a deep bed of paper or wood-shaving bedding, a solid wheel and a sand bath, "
    "in a cage at least 80cm by 40cm on one level rather than tubes. Spot clean the wet corner "
    "daily, change the bedding every few weeks, and give a water bottle rather than a bowl. They "
    "are awake at night, so keep the cage out of the bedroom.")


def _small_pet_setup(memory, understood):
    """The set-up for the small animal the line actually names, not the one the card was written
    for: a guinea pig is not a rabbit and is not fed like one. Cleaning is this card's other
    question, and a list of things to buy is no answer to "how often should i clean the hutch".
    """
    animal = _the_small_pet(memory, understood)
    if _CLEANING_ASK.search(_said(understood)):
        return _PET_CLEANING[animal]
    return _PET_SETUP[animal]


def _the_hamster_basics(memory, understood):
    """The hamster card holds the same two questions, so it answers the one that was asked."""
    if _CLEANING_ASK.search(_said(understood)):
        return _PET_CLEANING["hamster"]
    return _PET_SETUP["hamster"]


# A rabbit's yearly jab is not a puppy's: myxomatosis and two strains of RHD are what kill
# rabbits, the jabs are yearly for life, and a rabbit that has never had one starts at any age.
# The check-up card answered every animal with the puppy and kitten course, so "do rabbits need
# vaccinations" came back as a puppy's first jabs.
_PET_CHECKUP = {
    "rabbit": (
        "Rabbits need a yearly jab and it is the one people forget: myxomatosis and rabbit "
        "haemorrhagic disease (RHD, both strains), usually as one combined injection, once a "
        "year for life, and a rabbit that has never had one can start at any age - including an "
        "older rescue. The same visit is the yearly check: teeth, weight and claws, because a "
        "rabbit's teeth grow all its life. Ask the practice to text the reminder."),
    "guinea pig": (
        "Guinea pigs need no routine jabs, but they do need the yearly check: teeth, weight and "
        "claws, and a look at the skin, because a guinea pig that stops eating goes downhill in "
        "a day. Ask the practice to text the reminder, and weigh at home once a week in between."),
    "hamster": (
        "Hamsters need no routine jabs, but they do need a vet who sees small animals: register "
        "with one that does exotics before anything goes wrong, because a hamster goes downhill "
        "in a day. The yearly visit is a weight, teeth and lump check - they get tumours "
        "easily and early ones are fixable. Weigh at home weekly, since a hamster losing weight "
        "is the first sign of most of it."),
    "other": (
        "Once a year for a health check, and the yearly booster goes in at the same visit. "
        "Puppies and kittens: a course of two or three jabs two to four weeks apart, then the "
        "yearly one. Past about eight years old, twice a year is worth it. A rabbit needs its "
        "teeth checked once a year. The practice usually texts the reminder, so ask them to set "
        "one."),
}


def _the_pet_checkup(memory, understood):
    """The yearly visit, in the animal the line names: a rabbit's jabs are not a puppy's."""
    animal = _the_pet_named(memory, understood, default="other")
    return _PET_CHECKUP.get(animal, _PET_CHECKUP["other"])


# The tray is the same question for every animal that uses one, and the cat's answer is the
# wrong one for a rabbit: clumping cat litter sets hard in a gut, and a rabbit will eat it.
_PET_LITTER = {
    "cat": (
        "Scoop the solids out twice a day and change the whole tray of clumping litter once a "
        "week - a tray that is cleaned that often does not need disinfecting every time, just hot "
        "water and a drop of unscented washing-up liquid. More trays than cats (three for two "
        "cats) is what stops accidents, and an unwashed tray is the commonest reason a cat starts "
        "going elsewhere. Never mix bleach with cat urine: it gives off a gas that hurts their "
        "lungs and yours."),
    "rabbit": (
        "A rabbit litter-trains easily: a tray in the corner it already uses, lined with paper or "
        "wood pellets - never clumping cat litter, which sets hard if a rabbit eats it. Lift the "
        "wet litter out every day, change the whole tray once or twice a week, and give a pair two "
        "trays, because a rabbit likes to eat hay and go in the same spot. Under a hay rack is "
        "where it will use it most."),
    "guinea pig": (
        "A guinea pig picks a corner of the cage to use, so a tray there lined with paper or wood "
        "pellets catches most of it - never clumping cat litter, which sets hard if it is eaten. "
        "Lift the wet litter out every day and change the tray twice a week, and put the hay rack "
        "over it, because a guinea pig toilets where it eats."),
    "hamster": (
        "A hamster picks one corner of the cage to pee in, so a small tray there with sand or "
        "paper pellets catches it: empty it every day or two and rinse it with hot water. Change "
        "the whole cage bedding every few weeks, not every week, because a hamster needs its nest "
        "to keep smelling of itself."),
}


def _the_litter_routine(memory, understood):
    """The tray question, in the animal the line names: a rabbit's tray is not a cat's."""
    animal = _the_pet_named(memory, understood, default="cat")
    return _PET_LITTER.get(animal, _PET_LITTER["cat"])


# A mouth that has gone pale, white, grey or blue is the fastest sign a pet is in trouble, and the
# brushing answer was taking those lines - "my dog has pale gums" sent a person to look for a
# toothbrush. Red or swollen gums are the gum-disease answer, so they keep the brushing text.
GUMS_COLOUR = ("pale", "white", "grey", "gray", "blue", "pink", "colour", "color", "normal",
               "healthy")
# A good colour word and no bad one is the "is this normal?" question, which wants a yes and the
# refill test, not the list of emergencies.
GUMS_FINE = ("pink", "healthy", "normal", "fine", "good")
# "what colour should my dogs gums be" names no colour at all: it asks what right looks like, and
# the emergency list is the wrong answer to it (@deft-squid on `40b1c3b7`). A bad colour word
# still wins, so "they should be pink but they are pale" keeps the vet-today text.
# "what colour are dogs gums" names no colour either, so the word "colour" itself is a question
# about what is right unless the line says the colour has changed.
GUMS_ASKING = ("should", "supposed", "ought", "colour", "color")
GUMS_CHANGED = ("changed", "change", "different", "darker", "lighter", "went", "turned")
GUMS_BAD = ("pale", "white", "grey", "gray", "blue", "bleached")
# Red is not the pale-mouth emergency: it is the gum-disease answer, which brushing alone will not
# clear. "my dog has red gums" was reaching the toothbrush text, which tells you nothing to do.
GUMS_RED = ("red", "reddish", "swollen", "swelling", "inflamed", "sore", "bleeding", "bleeds")


def _pet_mouth(memory, understood):
    """The colour of the gums first, the toothbrush second."""
    words = set((understood or {}).get("words") or ())
    said = (understood or {}).get("clean") or ""
    about_gums = "gums" in said or "gum colour" in said or "gum color" in said
    if about_gums and ("black" in words or "dark" in words or "patch" in words
                       or "patches" in words):
        return ("Black or dark patches are usually just pigment, and they are fine if they have "
                "always been there. A black or bruised patch that has just appeared, or gums that "
                "are dark and cold, is a vet call today.")
    if about_gums and any(word in words for word in GUMS_RED):
        return ("Red or swollen gums are gingivitis, and brushing will not shift it on its own: "
                "book a vet check for a scale and polish, then brush at the gum line every day, "
                "because that is what keeps it from coming back. Sore gums that bleed when touched "
                "are worth showing to the vet rather than watching for a week.")
    if about_gums and any(word in words for word in GUMS_COLOUR):
        if ((any(word in words for word in GUMS_FINE)
             or any(word in words for word in GUMS_ASKING))
                and not any(word in words for word in GUMS_BAD + GUMS_CHANGED)):
            return ("Pink and wet is right, and a pale pink is normal too. Press a fingertip on the "
                    "gum until it goes white: the colour should come back in under two seconds, and "
                    "pale, white, grey or blue gums mean the vet today, because they point to blood "
                    "loss, shock or too little oxygen.")
        return ("Pale, white, grey or blue gums mean the vet today, not a wait and see: they point "
                "to blood loss, shock or too little oxygen, and a pet that is also weak or breathing "
                "fast is an emergency. Press a fingertip on the gum until it goes white - the "
                "colour should come back in under two seconds, and pink and wet is what you want.")
    return ("Brush them, with a pet toothpaste and a finger brush, at the back first and only for "
            "a few seconds to start - human toothpaste is not for animals. Brown tartar and bad "
            "breath mean a vet check: a scale and polish is what stops gum disease, and chewing "
            "is not a substitute for it.")


# A dog that has been ill this conversation needs the vet's food advice, not a portion guide.
ILL = ("sick", "vomit", "vomited", "vomiting", "diarrhoea", "diarrhea", "not eating",
       "won't eat", "wont eat", "off his food", "off her food", "unwell")
# A pet that is hurt or ill is a body question, and the behaviour cards answer the body badly:
# "my cat is crying in pain" got the how-long-can-she-be-left card, "my cat vomits first thing" got
# the paw-pushes-things card because "thing" is in its key, and "my cat puked on the carpet" got the
# scratching post. Every one of those rows carries this fence, so a symptom stands the behaviour
# card down and the pain, sickness and vet rows answer instead.
SICK_OR_HURT = (
    "in pain", "pain", "pains", "hurt", "hurts", "hurting", "sore", "ache", "aching",
    "yelp", "yelps", "yelping", "flinch", "flinches", "flinching", "cries out", "cry out",
    "cried out", "screams", "screaming",
    "sick", "sickness", "sicked", "vomit", "vomits", "vomited", "vomiting", "being sick",
    "puke", "pukes", "puked", "puking", "throwing up", "threw up", "brings up", "brought up",
    "diarrhoea", "diarrhea", "the runs", "runny poo", "loose poo",
    "ill", "illness", "unwell", "poorly", "not well",
    "limp", "limping", "limped", "blood", "bleeding", "bled", "wound",
    "not eating", "stopped eating", "off her food", "off his food", "wont eat", "won't eat",
    "collapsed", "collapse", "fitting", "seizure", "seizures",
)

# A pet's tea or dinner is its food. The not-eating rows were written for the word "food" alone,
# so "the cat is a bit off her dinner today" reached nothing, "my dog is off his dinner" the
# dog-friendly pubs and "my dog has gone off his tea" the shelf life of tea. The phrases carry the
# meal, so the refusal is the same question whichever word the person uses for the bowl.
PET_OFF_MEAL = (
    "off his dinner", "off her dinner", "off their dinner",
    "off his tea", "off her tea", "off their tea",
    "gone off his dinner", "gone off her dinner", "gone off their dinner",
    "gone off his tea", "gone off her tea", "gone off their tea",
    "not eating his dinner", "not eating her dinner", "not eating his tea", "not eating her tea",
    "wont eat his dinner", "wont eat her dinner", "wont eat his tea", "wont eat her tea",
    "won't eat his dinner", "won't eat her dinner", "won't eat his tea", "won't eat her tea",
    # the same refusal without the word "eat" in it: a dog that will not touch his tea, leaves
    # his dinner, or has not eaten it all day was answered with the pub list, the walk clock or
    # a shrug, and "wont touch his food" alone was the only one written down.
    "wont touch his dinner", "wont touch her dinner", "wont touch their dinner",
    "wont touch his tea", "wont touch her tea", "wont touch their tea",
    "won't touch his dinner", "won't touch her dinner", "won't touch their dinner",
    "won't touch his tea", "won't touch her tea", "won't touch their tea",
    "leaves his dinner", "leaves her dinner", "leaves their dinner",
    "leaves his tea", "leaves her tea", "leaves their tea",
    "hasnt eaten his dinner", "hasnt eaten her dinner", "hasnt eaten his tea", "hasnt eaten her tea",
    "hasn't eaten his dinner", "hasn't eaten her dinner", "hasn't eaten his tea",
    "hasn't eaten her tea",
    "has not eaten his dinner", "has not eaten her dinner", "has not eaten his tea",
    "has not eaten her tea", "not eaten his dinner", "not eaten her dinner", "not eaten his tea",
    "not eaten her tea", "not eaten his food", "not eaten her food",
    # the same refusal said the other way round: "my dog turned his nose up at his dinner" was the
    # wound answer, because "nose" is a thing a vet looks at.
    "turned his nose up", "turned her nose up", "turns his nose up", "turns her nose up",
    "turning his nose up", "turning her nose up", "nose up at his", "nose up at her",
    "nose up at the", "turned its nose up", "turns its nose up",
)
# A dog word, or a pronoun that can only mean the dog once the line is about feeding him.
PET = {"dog", "dogs", "puppy", "pup", "him", "his", "her", "she", "he"}

# "When do i switch him to adult food" is the question after the portion guide, not another
# asking of it: it came back with the same guide three turns on, cut down to its first sentence,
# which reads as if the bot had not heard the new question. Only the line in front of the bot
# counts, because "adult food" from an earlier turn is exactly the history that made the guide
# look current.
SWITCH_WORDS = ("switch", "switches", "switching", "switched", "change over", "changeover",
                "change onto", "change to adult", "adult food", "grown up food", "grow out of",
                "off the puppy food", "off puppy food", "stop the puppy food",
                "keep him on puppy food", "keep her on puppy food", "keep them on puppy food",
                "on puppy food", "on kitten food", "puppy food for how long", "until what age")


def _a_switch_to_adult_food(understood):
    """The age a dog comes off puppy food, by size, and the week-long changeover."""
    here = (understood.get("clean") or "").lower()
    return any(word in here for word in SWITCH_WORDS)


# A feeding question asked with a pronoun is only the dog's when the dog is the animal the
# chat is on. The dog row does not key "him"/"her"/"his" itself: that took "what should i feed
# her" after a rabbit or a baby, and a reply function that returns nothing stops the lookup on
# its own row instead of letting the rabbit answer behind it. This reads the last few turns,
# where the animal is, and only the dog gets the dog's portion guide.
FEED_ASK = re.compile(r"\b(?:feed|feeds|feeding|food|portion|portions|grams|meals|amount)\b")
# The line is asking about an illness as well as the food: "hes got the runs and i dont no what
# to feed him" is the upset-stomach answer, not the everyday portion guide, and a question that
# says what is wrong with the animal is left to the entries that answer that.
SICK_NOW = re.compile(r"\b(?:runs?|loose|diarr\w*|vomit\w*|sick|ill|unwell|stomach|"
                      r"poorly|off (?:his|her|their) food|not eating|wont eat|won't eat)\b")
DOG_WORD = re.compile(r"\b(?:dog|dogs|puppy|puppies|pup|pups|bitch|doggy)\b")
NOT_DOG = re.compile(
    r"\b(?:cat|cats|kitten|kittens|rabbit|rabbits|bunny|bunnies|guinea|hamster|hamsters|"
    r"gerbil|gerbils|chinchilla|chinchillas|ferret|ferrets|parrot|parrots|budgie|budgies|"
    r"parakeet|cockatiel|tortoise|tortoises|lizard|lizards|snake|snakes|gecko|geckos|"
    r"goldfish|rat|rats|mouse|mice|degus|hedgehog|hedgehogs|"
    r"baby|babies|child|children|kid|kids|son|sons|daughter|daughters|toddler|toddlers|"
    r"husband|wife|partner|boyfriend|girlfriend|mum|mums|mom|moms|dad|dads|mother|father|"
    r"grandma|granddad|granny|grandpa)\b")


def the_dog_feed_follow_up(text, memory):
    """The dog's feeding answer for a line whose only subject is a pronoun, or "".

    "my dog has been sick twice today" / "he had his dinner fine" / "what should i feed him
    tomorrow": no line in that last turn names the dog, so the dog row's own words cannot reach
    it. The dog is still the animal the chat is on, and this puts the question back to the dog
    row. A rabbit or a baby more recent than the dog gets its own answer instead, so the line is
    not turned into a dog question.
    """
    said = str(text or "").lower()
    if not FEED_ASK.search(said) or SICK_NOW.search(said):
        return ""
    if DOG_WORD.search(said):
        return ""  # the dog row's own key reaches an explicit dog line
    if not re.search(r"\b(?:him|her|his|he|she|it)\b", said):
        return ""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    recent = [str((turn or {}).get("user") or "").lower()
              for turn in (turns or [])[-3:]]
    dog_at = -1
    other_at = -1
    for at, line in enumerate(recent):
        if DOG_WORD.search(line):
            dog_at = at
        if NOT_DOG.search(line):
            other_at = at
    if dog_at < 0 or other_at > dog_at:
        return ""
    return _dog_feed(memory, {"clean": said, "text": said})


def _dog_feed(memory, understood):
    """A portion guide, or bland food when the dog has been ill in the last few turns."""
    if _a_switch_to_adult_food(understood):
        return ("Most dogs move onto adult food at about a year. Small breeds can go at nine to "
                "twelve months; the big ones, a Labrador upwards, do better on puppy food until "
                "eighteen months to two years, because their joints are still growing. Change "
                "over a week or two rather than overnight: a quarter of the new food for two or "
                "three days, then half, then three quarters, and watch his poo - loose means slow "
                "down. Keep roughly the same amount and go by his ribs and waist rather than the "
                "packet.")
    said = [(understood.get("clean") or "")]
    said += [(turn.get("user") or "").lower() for turn in (memory.get("turns") or [])[-3:]]
    text = " ".join(said)
    # The illness has to be the dog's: a person who felt sick yesterday still wants
    # the portion guide, not a bland diet for the dog.
    if any(word in line and PET & set(re.findall(r"[a-z']+", line))
           for line in said for word in ILL):
        return ("Keep tomorrow bland and small: plain chicken and rice, or his normal food soaked "
                "soft, in four little meals rather than two big ones. Over a day or two mix his "
                "usual food back in. If the sickness comes back, or he stops drinking, ring the "
                "vet rather than waiting.")
    if "puppy" in text or "pup" in text:
        return ("Puppies need more than the adult 2% guide: feed a complete puppy food and follow "
                "the packet's weight and age chart. Four small meals a day up to about four "
                "months, then three, then two after six months. You should feel his ribs easily "
                "but not see them; ask the vet to weigh him at each vaccination visit and adjust "
                "from there.")
    return ("As a rough guide, an adult dog eats about 2% of his body weight a day: 400g of food "
            "for a 20kg dog, split into two meals. Use the bag or tin as a starting point, then go "
            "by condition: you should feel ribs easily but not see them, and see a waist from "
            "above. Puppies need more, and a vet can weigh him and give you an exact amount.")


# A lead that comes off is a fitting problem, not a training one, and a collar that pinches is a
# third thing: the same "lead" line has three answers, and the words for the trouble say which.
SLIP_WORDS = ("slip", "slips", "slipping", "slipped", "loose", "escape", "escapes", "escaping",
              "comes off", "came off", "gets out", "getting out")
TIGHT_WORDS = ("tight", "pinch", "pinches", "pinching", "rubs", "rubbing", "chafes", "chafing",
               "sore", "mark", "marks")
PULL_WORDS = ("pull", "pulls", "pulling", "drag", "drags", "dragging", "walk", "walks")


# "My dog is scared of my husband" is a question about that one person, and the answer reads
# better when it names him back; "my dog is scared of men" is the general case, and naming a
# husband there is what went wrong before. So the words in the line pick the wording.
WARY_ONE = (("husband", "your husband"), ("wife", "your wife"), ("partner", "your partner"),
            ("boyfriend", "your boyfriend"), ("girlfriend", "your girlfriend"),
            ("brother", "your brother"), ("sister", "your sister"), ("son", "your son"),
            ("daughter", "your daughter"), ("dad", "your dad"), ("father", "your dad"),
            ("mum", "your mum"), ("mother", "your mum"), ("grandad", "your grandad"),
            ("grandma", "your gran"), ("postman", "the postman"), ("neighbour", "your neighbour"),
            ("neighbor", "your neighbour"), ("friend", "your friend"), ("baby", "the baby"),
            ("toddler", "the toddler"), ("child", "the child"), ("man", "that man"),
            ("someone", "that person"))
WARY_MANY = (("men", "men"), ("strangers", "strangers"), ("people", "people"),
             ("visitors", "visitors"), ("visitor", "that visitor"), ("guests", "guests"),
             ("guest", "that guest"), ("children", "children"), ("kids", "children"),
             ("teenagers", "teenagers"), ("babies", "babies"), ("toddlers", "toddlers"),
             ("friends", "your friends"), ("new people", "new people"))


def _with_cause(memory, plan, cause):
    """A plan, with the cause in its opening sentence when the line asked why.

    "My dog barks at the door" wants what to do about it; "why does my dog bark at the door" wants
    the cause and gets a method with no reason. The reason is only added when the reading says a
    reason is what was asked for, and it opens the first sentence as a clause ("... is usually the
    alarm going off, so find ...") rather than a sentence of its own: the action is still there in
    the first sentence, and the sentence count a follow-up answer reads back does not change.
    """
    wants = ((memory or {}).get("understood") or {}).get("wants") or ()
    if isinstance(wants, str):
        wants = (wants,)
    if wants != "reason" and "reason" not in wants:
        return plan
    reason = cause.strip().rstrip(".")
    if not reason:
        return plan
    opening = plan[:1].lower() + plan[1:]
    return reason[0].upper() + reason[1:] + ", so " + opening


def _barking(memory, understood):
    """Barking: the plan, and the alarm in it when the line asked why."""
    return _with_cause(
        memory,
        "Find what starts it and block that first: a curtain over the window he watches, or the "
        "post put through a box away from the door. Then reward the quiet - a treat the moment he "
        "stops - and don't shout, because to a dog shouting sounds like you joining in. If he "
        "barks for hours when he is left, that is the being-left problem rather than the barking "
        "one.",
        "Barking is usually the alarm going off")


def _scared_of(memory, understood):
    """A dog wary of a person: the plan, and the fear in it when the line asked why."""
    return _with_cause(
        memory,
        _scared_of_plan(memory, understood),
        "Wary dogs are usually more frightened than bold")


def _scared_of_plan(memory, understood):
    words = set(re.findall(r"[a-z']+", ((understood or {}).get("clean") or "").lower()))
    for word, phrase in WARY_ONE:
        if word in words:
            return ("Let him come to %s on his own terms: no eye contact, no reaching over him, "
                    "and treats tossed on the floor while %s sits nearby and ignores the dog. "
                    "Being boring and calm is what builds trust, and it usually takes weeks "
                    "rather than days." % (phrase, phrase))
    for word, phrase in WARY_MANY:
        if word in words:
            return ("Let him come to %s on his own terms: no eye contact, no reaching over him, "
                    "and treats tossed on the floor while they sit nearby and ignore the dog. "
                    "Being boring and calm is what builds trust, and it usually takes weeks "
                    "rather than days." % phrase)
    return ("Let him come to the person he is wary of on his own terms: no eye contact, no "
            "reaching over him, and treats tossed on the floor while that person sits nearby "
            "and ignores the dog. Being boring and calm is what builds trust, and it usually "
            "takes weeks rather than days.")


def _dog_night(memory, understood):
    """A dog up at night, answered for the dog the line describes: a puppy, an old dog, or neither."""
    words = set((understood or {}).get("words") or ())
    clean = " " + ((understood or {}).get("clean") or "") + " "
    # "how long until he sleeps through the night" says nothing about age, and the answer to it
    # depends on the puppy named a turn earlier: the person's own recent words decide, never the
    # bot's last reply.
    earlier = " " + " ".join((turn.get("user") or "").lower()
                             for turn in (memory.get("turns") or [])[-2:]) + " "
    # An age in the line is the age: "my dog is 11" is an old dog, and it settles a line that
    # names no age at all in a conversation that started with a puppy.
    #
    # The number only counts next to the dog - "is 11", "aged 11", "an 11 year old dog" - because
    # a bare number is usually a clock: "my dog keeps waking at 9 every night" and "wakes at 11 at
    # night" are both read as a nine-year-old dog by a plain digit match, and get the arthritis
    # answer for a dog nobody said was old.
    older = bool({"elderly", "senior", "old", "older", "oldest", "aging", "ageing"} & words
                 or re.search(r"\b(?:(?:is|aged|about|nearly|almost|turned|turning|over|just "
                              r"over)\s+(\d{1,2})\b"
                              r"|(\d{1,2})\s*(?:years?\s+old|years?|yrs?|yo)\b)", clean))
    if not older and ("puppy" in earlier or " pup " in earlier):
        words.add("puppy")
    # A puppy is the age, not the word "old": "my 9 week old puppy cries at night" says both, so
    # the puppy test comes first and the number of weeks decides for it.
    if {"puppy", "puppies"} & words or "weeks old" in clean or "months old" in clean:
        return ("A puppy cannot hold it all night: at eight weeks expect to get up once, around 2 "
                "or 3am, and take him out just before you go to bed. Keep the last meal early and "
                "the bed beside yours so he can smell you, and answer the crying quietly and "
                "briefly with no lights and no play, so night stays boring. Most puppies sleep "
                "seven hours by about four months.")
    if older:
        return ("An older dog who starts waking at night is usually in discomfort rather than "
                "being naughty: arthritis makes lying still painful, and a dog who is stiff, "
                "pacing, panting or confused in the evening needs the vet rather than a training "
                "plan. Book a check, ask about pain relief, put a soft bed in a warm room with a "
                "night light, and take him out once last thing; sudden confusion in an old dog is "
                "worth a same-day call.")
    return ("Keep the night dull and the day busy: a last toilet trip on the lead, no lights, no "
            "chat and no play when he wakes, and a long walk plus some training in the afternoon "
            "so he is tired at bedtime. If he is sleeping a lot in the day, wake him gently for a "
            "short walk. A dog who starts waking at night after years of sleeping through is worth "
            "a vet check, especially if he is drinking more or seems stiff.")


# The pulling verb now sits in the key, so the row has to know it is a *dog* that pulls: "my razor
# keeps pulling", "i keep pulling out of it" and "the garden" in a conversation about leads all
# reached the lead-training card when the verb alone was enough. A dog word, or a word from the
# walk, is what makes the line this question.
_LEAD_SUBJECTS = frozenset((
    "dog", "dogs", "puppy", "pup", "pups", "puppies", "bitch", "doggy", "doggo", "collie",
    "collies", "spaniel", "terrier", "labrador", "lab", "retriever", "lurcher", "whippet",
    "poodle", "husky", "beagle", "dachshund", "corgi", "pug", "boxer", "vizsla", "shepherd",
    "lead", "leads", "leash", "leashes", "collar", "collars", "heel", "harness", "harnesses",
))
_LEAD_PHRASES = ("walk nicely", "walking nicely", "walk to heel", "on the lead", "lead walks")


def _on_a_lead(understood):
    """Whether the line is about a dog on a lead, rather than a razor or a fitness plan."""
    understood = understood or {}
    clean = " ".join((understood.get("clean") or "").split())
    if not (set(clean.split()) & _LEAD_SUBJECTS
            or any(phrase in clean for phrase in _LEAD_PHRASES)):
        return False
    # A follow-up is answered by swapping the new detail into the last ask, so "what about the
    # garden" after a lead question arrives here as "how do i stop my dog pulling on the garden"
    # - a sentence about a dog that is really about the garden. The subject the line was read
    # for says which: a garden is not a dog on a lead, and the row that knows the garden gets it.
    subject = " ".join(str(understood.get("subject") or "").lower().split())
    if not subject:
        return True
    return bool(set(re.findall(r"[a-z']+", subject)) & _LEAD_SUBJECTS)


def _dog_pulling(memory, understood):
    words = set(((understood or {}).get("clean") or "").split())
    clean = " ".join(words)
    if any(slip in clean for slip in SLIP_WORDS):
        return ("Check the fit before the training: a collar should take two fingers and no more, "
                "and a dog who backs out of a lead does it at the widest part of his head, so a "
                "sighthound or a narrow-headed dog needs a harness or a collar that tightens a "
                "little as he pulls. Practise putting it on and off with a treat so the lead is "
                "not the thing he braces against, and check the clip and stitching for wear.")
    if "collar" in clean and any(t in words for t in TIGHT_WORDS) and not any(
            p in words for p in PULL_WORDS):
        return ("Loosen it a notch: two fingers should slide under the collar and it should sit high "
                "on the neck, behind the ears, rather than low over the shoulders. Check for a "
                "mark or rubbed hair after a walk, and if he pulls into it, a harness takes the "
                "pressure off his throat instead.")
    return ("Train the lead as a stop-and-go game: the moment the lead goes tight, stand still "
            "until it slackens, then walk on, and reward him at your side with a treat. A "
            "front-clip harness or head halter helps while he learns, and a treat held at your "
            "knee keeps him where you want him.")


# The litter-tray answer, used by the "cat" entry and by the one that reads a line with no
# animal in it. When it still smells after a wash, the plastic has taken the smell up, which is
# the part a person who has already cleaned it is asking about.
# An accident in the house is not a tray question, and the litter answer was the tray: "my cat
# peed on the bed" was told how to scoop a tray when what the person asked is how to get the
# smell out of a duvet. The reply reads where it happened, so the spot comes first when the line
# says, and the tray and the vet follow it either way.
_WHERE_IT_LANDED = re.compile(
    r"\b(rug|rugs|carpet|carpets|bed|beds|duvet|duvets|mattress|sofa|sofas|settee|couch|"
    r"armchair|chair|floor|floorboards|lino|laminate|bath\s?mat|bathmat|bath|shower|sink|hall|"
    r"hallway|landing|house|home|indoors|inside|laundry|washing basket|curtains|blinds|"
    r"spare room|box room|corner|stairs|radiator|wardrobe|cupboard)\b")


def _litter_reply(memory, understood):
    """The tray answer, with the spot first when the person says where it happened."""
    text = ((understood or {}).get("norm_text") or (understood or {}).get("clean") or "").lower()
    if _WHERE_IT_LANDED.search(text):
        return ("Clean the spot properly first, because the smell is what takes her back to it: "
                "soak it with an enzyme cleaner, leave it to work and let it dry, and skip bleach "
                "and ammonia, because both smell like wee to a cat. Then the tray - one per cat "
                "plus one, scooped daily, unscented litter, in a quiet corner away from the food - "
                "and whatever changed in the house: a move, a new pet or a baby, building work, a "
                "door that now stays shut. A cat who was always clean and has suddenly started "
                "needs the vet first, because a urine infection or a bladder problem sits behind "
                "a lot of it.")
    return LITTER_REPLY


LITTER_REPLY = (
    "One tray per cat plus one, in quiet places, scooped daily and washed weekly with unscented "
    "soap. If it still smells after that, the plastic has picked it up: replace the tray and the "
    "litter, which is cheaper than fighting it. If a litter-trained cat suddenly goes outside the "
    "tray, a vet check comes first, because it is often a urine infection.")

# A cat in and out of the tray, or weeing somewhere new, is the commonest cat question after the
# fur, and it splits in two: a cat passing little or nothing is a blocked bladder and an
# emergency, which is the one thing here that cannot wait for a morning appointment.
_BLOCKED = re.compile(r"\b(cant|cannot|can not|unable to|blocked|no wee|nothing comes|"
                      r"nothing coming|not passing|passing nothing|passed nothing|struggling to)\b")
# "trying to wee" on its own is a cat going in and out of the tray, which is the cystitis answer:
# it is only the blocked-bladder emergency when the words for what came out are in the line too.
_TRYING = re.compile(r"\b(straining?|trying|keeps? trying|in and out|crying)\b")
_LITTLE = re.compile(r"\b(little|nothing|barely|drops?|only a drop|no urine|dry)\b")


_SPRAY = re.compile(r"\b(spray|sprays|sprayed|spraying|marking|marks)\b")
# Blood in the urine is the vet's line before it is a behaviour one, and "my cat keeps spraying
# and there is blood in his urine" was told how to stop the marking. A blood or straining word in
# the line stands the marking answer down, so the cystitis and blocked-bladder answers keep it.
_BLOOD = re.compile(r"\b(blood|bloody|bloodstained|straining|strains|dribbling|yelping|crying "
                    r"when|painful|in pain|sore)")


def _cat_urine(memory, understood):
    text = ((understood or {}).get("norm_text") or (understood or {}).get("clean") or "").lower()
    if _SPRAY.search(text) and not _BLOOD.search(text):
        # A cat spraying up a wall is marking, not cystitis: the answer was "blood or discomfort
        # when a cat wees is usually cystitis", which sends a person to the vet for a behaviour.
        if _the_neuter_is_done(understood):
            # the person has already said the tom is done, so "an unneutered tom does it most" is
            # the wrong half of the answer: in a cat that has been done, spraying is stress
            return ("A cat who is already done and still sprays is not doing it for the hormones: "
                    "in a neutered tom it is usually stress - a new animal in the house, a tray "
                    "moved, a cat outside the window - or a habit left from being done late. Put "
                    "a tray on each floor, plug in a pheromone diffuser, clean the spot with an "
                    "enzyme cleaner rather than bleach, and never shout at him for it. Spraying "
                    "with straining, blood or a tray he has stopped using is a vet check instead.")
        return ("Spraying up a wall or the back of the sofa is marking, and an unneutered tom does "
                "it most: neutering stops most of it, and the smell with it, though a tom done "
                "late may keep the habit. In a neutered cat new spraying is usually stress - a "
                "new animal, a moved tray, a cat outside the window - so put a tray on each "
                "floor, plug in a pheromone diffuser, and clean the spot with an enzyme cleaner "
                "rather than bleach. Never shout at him for it. Spraying with straining, blood "
                "or a litter tray he has stopped using is a vet check instead.")
    if _BLOCKED.search(text) or (_TRYING.search(text) and _LITTLE.search(text)):
        return ("A cat straining and passing little or nothing needs the vet now, tonight if you "
                "have to: a blocked bladder is an emergency, and it is most dangerous in male cats, "
                "who can go downhill in a day. Do not wait for the morning, do not press on his "
                "belly, and take him in a carrier with a towel over it. Keep a note of the last "
                "time you saw him pass a proper amount of urine.")
    return ("Blood or discomfort when a cat wees is usually cystitis, and it needs the vet in the "
            "next day or two rather than a wait-and-see, because the same signs cover crystals, a "
            "stone and the start of a blockage. Ring and ask them to test a urine sample if you can "
            "catch one in a clean tray with a little non-absorbent litter, keep the water bowl "
            "fresh and away from the food, and cut dry food back for a few weeks. If he ever "
            "strains and passes nothing at all, that is an emergency, not a next-day call.")


# A person saying the tray is fine is reassuring the bot in the middle of another worry ("my cat
# is 14 and yowling at night" -> "she's eating fine and uses the litter tray"), not asking how to
# clean it: the tray hygiene answer here would be a lecture about the wrong thing.
# Each phrase is the whole reassurance, not the plain act: `uses the litter tray` alone blocked
# A clear result from the vet is the answer a cat-urine chat is waiting on, and it changes the
# answer: with cystitis and stones ruled out, what is left is behaviour. The line that says it
# names no cat - "i did take her to the vet, they said no infection" - so this reads the chat for
# the animal, and stands down when the chat is about a person's own test.
NO_INFECTION_TEXT = (
    "That is the big one ruled out, then: a clear result means it is not illness, so it is "
    "behaviour - stress, a tray she has gone off, another cat in the garden she can smell through "
    "the window, or marking after a change in the house. Scoop twice a day, put a tray in every "
    "room she uses, and wash the places she has been with a biological detergent rather than "
    "bleach, which smells like urine to a cat and calls her back. A plug-in diffuser can settle "
    "things for a few weeks while she gets used to whatever changed.")
# "no infection", "came back clear", "said there was nothing there": the result, said plainly.
_A_CLEAR_RESULT = re.compile(
    r"\b(?:no|not an|isnt an|isn't an|wasnt an|wasn't an|without an?) infection\b|"
    r"\b(?:came|come|came back|comes back|got).{0,12}\bclear\b|"
    r"\b(?:nothing (?:wrong|there|found)|all clear|clear of)\b", re.I)
_A_CAT_NAMED = re.compile(r"\b(cat|cats|kitten|kittens|tom|tomcat|queen|litter)\b", re.I)


def _after_a_clear_urine_result(memory, understood):
    """The vet's clear result in a cat chat, which is the behaviour answer, not a shrug.

    The animal is named a turn or two back and not in the line that reports the result, so the
    chat decides. A person's own blood test is not this card: nothing here names a cat.
    """
    said = [str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()]
    said += [(turn.get("user") or "").lower() for turn in ((memory or {}).get("turns") or [])[-3:]]
    if not any(_A_CAT_NAMED.search(line) for line in said):
        return None
    if not _A_CLEAR_RESULT.search(said[0]):
        return None
    return NO_INFECTION_TEXT


# "my kitten wont use the litter tray", which is the question, not the reassurance.
LITTER_FINE = ("eating fine", "eating well", "eats fine", "still eating", "litter tray fine",
               "litter tray is fine", "no trouble with the tray", "uses it fine",
               "using it fine", "no problem with the tray")


# The milk line, unchanged: it was right, and the row keeps saying it. What the row did not do was
# answer the dairy that is neither milk nor cheese.
_PET_DAIRY_MILK = (
    "Cows' milk is the one to avoid: most cats and dogs stop making the enzyme for it, so it gives "
    "them wind and the runs, and water is all a cat needs to drink. A kitten wants its mother's "
    "milk or a proper kitten milk replacer rather than anything from the fridge. Small pieces of "
    "cheese are fine as a treat if they do not upset him.")


def _pet_dairy(memory, understood):
    """A spoon of plain yoghurt is the dairy this row never answered.

    Cheese and ice cream have their own answers and the row already stands down for them; milk,
    cream, dairy and lactose all get the one text. Yoghurt read as the milk question and the row
    only keys "milk", so "can i give my dog yoghurt" was the shrug.
    """
    text = ((understood or {}).get("norm_text") or (understood or {}).get("clean") or "").lower()
    if "yoghurt" in text or "yogurt" in text:
        return ("Plain yoghurt is fine: a spoonful or two of the natural sort with no sugar and "
                "no sweetener in it is a cool treat in summer, and it is gentle on a poorly "
                "stomach. Skip the fruit and vanilla ones, which are mostly sugar, and take it "
                "off the day's dinner rather than adding it on top.")
    return _PET_DAIRY_MILK


# "Can my dog eat this?" is asked about a short list of foods, and the list splits in two: a few
# are a vet visit (they belong to the poisons answer, not this one), the rest are fine in small
# amounts or fine with a word of caution. Keyed by the food, so one entry answers every way of
# asking, and the answer names the food the person asked about.
PLAIN_FISH = ("plain cooked fish is fine once every bone is out, and it is the battered, salted "
              "or smoked sort that is the problem")
SAFE_FOODS = {
    "banana": "a few slices of banana are fine",
    "apple": "apple is fine in slices, without the core and pips",
    "carrot": "carrots are good, raw or cooked",
    "rice": "plain cooked rice is fine, and it is what a poorly {kind} is fed on",
    "chicken": "plain cooked chicken is fine, with no bones and no skin",
    "peanut": "peanut butter is fine if the jar has no xylitol in it",
    "egg": "a cooked egg is fine",
    "tuna": "a little tinned tuna in spring water is fine, not the brine",
    "blueberr": "blueberries are fine",
    "bread": "a bit of plain bread is fine",
    "cucumber": "cucumber is fine",
    "pumpkin": "plain cooked pumpkin is fine",
    "watermelon": "watermelon is fine, without the rind and pips",
    "prawn": "a prawn or two is fine, cooked and plain",
    "turkey": "plain cooked turkey is fine, with no skin and no bones",
    "salmon": "cooked salmon is fine, with no bones; raw salmon is not",
    # "fish" is the word for the whole category, and without it "can i give my cat fish" and
    # "can my dog eat fish" were answered with a rod licence from the fishing row. The species
    # are here too, or "can my dog eat cod" falls past the table to the refuse list.
    "fish": PLAIN_FISH, "cod": PLAIN_FISH, "haddock": PLAIN_FISH, "hake": PLAIN_FISH,
    "pollock": PLAIN_FISH, "plaice": PLAIN_FISH, "tilapia": PLAIN_FISH, "whitebait": PLAIN_FISH,
    # The foods people actually ask about and the table did not hold: "is a burnt toast bad for
    # a dog" and "can dogs eat cheese" were the no-answer card and the milk card. Cheese keeps
    # its own sentence here rather than the kitten-milk one, and burnt toast is bread, not a
    # poison: it is the butter and the fruit loaf that matter.
    "cheese": "a small piece of hard cheese is fine, and it is the milk that upsets most of them",
    "toast": "plain toast is fine as a treat and not a meal, and burnt toast is the one to scrape",
    "yoghurt": "plain yoghurt is fine in a small amount, and the fruit or sugar sorts are not",
    "popcorn": "plain popcorn is fine in a few pieces, without butter or salt",
    "pasta": "plain cooked pasta is fine in a small amount",
    "porridge": "plain porridge oats, cooked in water, are fine",
}
CAUTION_FOODS = {
    "bone": "cooked bones splinter and a splinter is a vet job, so give a proper chew instead "
            "of anything off the plate. A small bit of gristle is not a problem.",
    "sausage": "sausages are salty and fatty: a piece is fine, a plateful is a bad habit.",
    "bacon": "bacon is salty and fatty: a piece is fine, a plateful is a bad habit.",
    "ham": "ham is salty and fatty: a piece is fine, a plateful is a bad habit.",
    "chips": "chips are fat and salt: one is a treat, a handful is a bad idea.",
    "salt": "salt is dangerous in quantity and {one}'s portion is tiny, so keep it out of reach. "
            "If a lot has gone down, ring the vet: too much salt is an emergency.",
    "sugar": "sugar is just empty calories, and it is the sugar-free sort with xylitol in it "
             "that is the dangerous one.",
    # Avocado, ice cream and pizza are the three that get asked about with a worried voice and are
    # not poison: each has one real hazard and the answer says which.
    "avocado": "the flesh is not a poison to a dog or a cat, but the stone is a blockage and the "
               "skin is hard to digest, so a bit of flesh is fine and the stone has to be out of "
               "reach. It is birds it kills.",
    "ice cream": "a lick of plain vanilla does no harm, and the dairy, the sugar and the chocolate "
                 "sort are the three reasons not to give a bowl of it.",
    "pizza": "salt, fat, and often onion or garlic, which damage a dog's red cells: a corner is "
             "not an emergency, and a slice is the vet if it is a small dog.",
    "raw egg": "a raw egg is not a poison, but the white is hard to digest and salmonella is the "
               "reason to cook it: a cooked or scrambled egg is the better treat.",
    "coffee": "caffeine is a poison to dogs and cats, and it is a vet call: keep cups and "
              "coffee grounds and caffeine tablets out of reach, and say how much went down.",
    "macadamia": "macadamia nuts are a poison to dogs even in small numbers: ring the vet and say "
                 "how many, and do not wait for the wobble to start.",
    # "is a burnt toast bad for a dog" is not the plain-toast answer: the charred part is the
    # bit to leave off, so it gets a caution rather than a yes.
    "burnt": "burnt toast or bread is not worth giving: scrape the black off, or use a fresh "
             "slice, because the charred part is not food. Plain toast is otherwise just bread.",
}
# The animal has to be in the line before an eaten-something answer fires. Without this,
# "i ate raw chicken is that bad" and "my kid ate a chicken bone" were answered about a dog:
# the verbs (ate, swallowed) are the same for a person, so the animal is the only thing that
# tells the two apart.
PET_ANIMAL_ASK = ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "kittens", "pet",
                  "pets", "rabbit", "rabbits", "bunny", "hamster", "guinea pig", "budgie",
                  "parrot", "tortoise",
                  # A horse is a pet the composer's ANIMALS list already knows, so once the
                  # dentist row stands aside for an animal these rows have to name it, or "my
                  # horse has a dental problem" falls to the "Noted:" receipt.
                  "horse", "horses", "pony", "ponies")

# A food that is chocolate or raisins without saying so. The poison is in the name a person
# writes, not in the word "chocolate": "my dog ate a whole easter egg" and "my dog ate a brownie"
# were answered "Noted: your dog ate a whole easter egg", and a dog that may be poisoned is the
# one line that must never be filed away. Every entry that uses these still needs a pet word and
# an eating verb in the line, so a person's own brownie is theirs.
CHOCOLATE_FOODS = ("chocolate", "easter egg", "easter eggs", "advent calendar",
                   "advent calendars", "nutella", "brownie", "brownies", "choc ice",
                   "chocolate spread", "pain au chocolat", "cocoa", "chocolate orange")
# Raisins are a kidney poison and they travel inside cakes: a mince pie, a hot cross bun and a
# slice of fruit cake are all the grape entry's business.
RAISIN_FOODS = ("mince pie", "mince pies", "fruit cake", "fruit cakes", "christmas cake",
                "hot cross bun", "hot cross buns", "eccles cake", "christmas pudding",
                "christmas puddings", "plum pudding", "plum puddings", "figgy pudding",
                "spotted dick", "spotted dick pudding", "fruit pudding", "fruit puddings")

CAN_EAT_ASK = tuple(SAFE_FOODS) + tuple(CAUTION_FOODS) + (
    "banana", "carrot", "apple", "rice", "chicken", "tuna", "peanut", "butter",
    "bones", "bone", "nuts", "sausage", "bacon", "ham", "chips", "bread", "food",
    "prawn", "prawns", "sugar", "salt", "ice cream", "turkey", "salmon", "pasta", "porridge",
    "fish", "white fish", "cod", "haddock", "hake", "plaice",
    "blueberries", "cucumber", "pumpkin", "watermelon", "egg", "eggs")


def _pet_tummy(memory, understood):
    """Loose stools in a cat or a rabbit, which are the two animals that must not skip a meal.

    A dog can miss a meal and come to no harm, so a dog's loose poo is the dog answer
    (`dog-vomiting`, which main has). A cat that goes a day or more without food can come down
    with hepatic lipidosis, and a rabbit that stops eating can go into gut stasis, which kills
    them, so both of these keep the food going instead. A reviewer of this PR caught the dog
    wording ("skip the next meal") being given to a cat.
    """
    text = (understood or {}).get("clean") or ""
    if re.search(r"\b(rabbit|rabbits|bunny|bunnies)\b", text):
        return ("A rabbit that is passing soft or watery droppings should not be starved: keep the "
                "hay and water going, take away the greens and pellets for a day, and ring a "
                "rabbit-savvy vet today. A rabbit that stops eating or passing droppings at all is "
                "an emergency, because the gut can stop moving within a day.")
    return ("Don't fast a cat: a cat that goes a day without food can run into liver trouble, so "
            "keep the food going as small bland meals - plain cooked chicken or white fish, a "
            "spoon at a time - with plenty of water, and leave her normal food out. Ring the vet "
            "the same day if there is blood, if she is flat or off her water, if it lasts more "
            "than a day, or if it is a kitten, because a small animal dehydrates fast.")


# A small pet or a bird is not fed like a dog, and the dog's list of dangerous foods is the wrong
# answer for one. Asked "can hamsters eat cheese", "can guinea pigs eat bananas" and "can budgies
# eat avocado" the bot said it did not know, and avocado can kill a bird: the food and the animal
# were both known, and neither table was. One row here answers every way of asking, keyed by the
# animal the person named, and it says the animal's own things rather than the dog's.
SMALL_PET_FOODS = {
    "hamster": {
        "cheese": "A scrap of hard cheese now and then does no harm, but it is a treat and not "
                  "food: the diet is its own nuggets, a little veg and a handful of seed, and too "
                  "much dairy at once gives it the runs.",
        "banana": "A small piece now and then is fine, but it is sugary, so it is a taste and not "
                  "a meal: nuggets, a little veg and a handful of scattered seed are the diet.",
        "carrot": "Carrot is good in a small piece, raw or cooked, and it is one of the few veg "
                  "nearly every hamster will take.",
        "chocolate": "No. Chocolate is poisonous to a hamster and even a small piece is a vet "
                     "call: ring one and say how much and how long ago.",
        # Grapes shut a dog's kidneys; for a hamster they are just sugar. The dog's warning was
        # answered to a hamster because the food and the animal were both known and only the dog's
        # table held the pair, which is the one mistake this table can make: the animal's rule, not
        # the nearest one.
        "grapes": "A small piece of grape now and then is fine, but it is sugary, so it is a treat "
                  "and not food: nuggets, veg and a handful of seed are the diet, and raisins are "
                  "worse than fresh because the sugar is concentrated.",
        "raisins": "A raisin or two is the same answer as a grape and no better: dried fruit is "
                   "sugar concentrated, so it is a treat and not food, and nuggets, veg and a "
                   "handful of seed are the diet.",
        "apple": "A small piece of apple is fine, without the pips, as an occasional treat.",
    },
    "guinea pig": {
        "banana": "A small slice of banana now and then is a treat, no more than that: the sugar "
                  "upsets the gut, and hay plus a vitamin C source every day is what a guinea pig "
                  "actually needs.",
        "lettuce": "Lettuce is fine as long as it is not iceberg: give romaine, a little "
                   "spinach, kale or parsley alongside unlimited hay, and go easy on anything "
                   "watery.",
        "carrot": "Carrot is fine in a small piece, and the green top is good too: it is sugary, "
                  "so it is a treat beside the hay.",
        "apple": "A small piece of apple is fine, without the pips, now and then.",
        "chocolate": "No, and it is a vet call: chocolate is poisonous to a guinea pig.",
        "grapes": "A small piece of grape is a treat and no more: fruit is sugary and the gut "
                  "does badly with much of it, so hay is the diet and grapes are a now-and-then "
                  "thing.",
    },
    "bird": {
        "avocado": "No, and never: avocado can kill a budgie or a parrot within hours. The flesh, "
                   "the skin and the stone are all off limits, and so is anything that has had "
                   "avocado in it. Ring an avian vet at once if a bird has pecked some.",
        "chocolate": "No: chocolate is poisonous to birds, and a small piece of milk chocolate is "
                     "enough to make one seriously ill. Ring an avian vet rather than waiting.",
        "apple": "Fine in a small piece, without the pips or the core, and it is a better treat "
                 "than anything from a packet.",
        "carrot": "Fine, grated or in thin strips, and a good source of the vitamin A a bird on a "
                  "seed-only diet is short of.",
        "banana": "Fine in a small piece now and then, and most birds like it: fruit is a treat "
                  "beside the pellets, veg and seed.",
        "bread": "A little dry bread is fine, but not the main food and never mouldy.",
        "cheese": "A tiny crumb now and then does no harm, but dairy is not a bird's food: pellets, "
                  "veg and a little fruit are.",
        "grapes": "Grapes are fine in a small piece or two, cut so it is not a whole one to choke "
                  "on, and they are a treat beside the pellets and veg rather than part of the "
                  "diet. Dried fruit is sweeter and sticks to the beak, so fresh is better.",
        "raisins": "A raisin is a grape with the water gone and the sugar left, so it is a treat "
                   "in one or two pieces at most, and never the whole handful: pellets and veg are "
                   "the food.",
    },
}
SMALL_PET_DIET = {
    "hamster": ("The diet is its own nuggets, a handful of seed scattered to dig for, and a little "
                "veg - broccoli, carrot, cucumber. Keep away chocolate, onion, garlic, citrus and "
                "anything salty or sugary, which is most of what a person snacks on; a piece of "
                "fruit is a now-and-then treat, not part of the diet."),
    "guinea pig": ("Hay all day, guinea-pig nuggets with vitamin C in them, and a handful of "
                   "greens - parsley, kale, broccoli, romaine - with a slice of orange now and "
                   "then. Keep away iceberg lettuce, potato, onion, garlic, rhubarb and anything "
                   "sugary in quantity."),
    "bird": ("Pellets for the species, fresh veg every day - carrot, broccoli, spinach, peas - "
             "and a little fruit as a treat, with seed as part of the mix rather than all of it. "
             "Avocado, chocolate, caffeine, alcohol and salty or sugary food can kill a bird, so "
             "nothing off a plate and nothing from a cup."),
    "gerbil": ("A gerbil lives on its own seed mix, a little hay and a small piece of veg, and it "
               "gets most of its water from that, so keep the bottle full anyway. Keep away "
               "chocolate, onion, garlic, citrus and anything sugary."),
    "chinchilla": ("Chinchillas are built for hay and dry pellets, with a raisin or a piece of "
                   "apple as an occasional treat. Nothing wet or fresh in quantity, and keep away "
                   "chocolate, onion, garlic and anything sugary: the gut does badly with a sudden "
                   "new food."),
    # "Can horses eat apples" reached the fruit-skin card ("apple and pear skin is the best part
    # of it"), which is a person's bowl of fruit and not a horse's bucket: an apple is a treat for
    # a horse, in pieces, and hay is the food. A horse is in this table because the row above it
    # stands down for one.
    "horse": ("Hay and grass are the diet - a horse at grass eats for most of the day - with a "
              "feed balancer or a ration of feed for the work it does, and water always. Apples "
              "and carrots are treats in pieces, one or two a day and not a bucket, and never lawn "
              "clippings or anything wilted: ragwort, sycamore seedlings and cut grass can all "
              "make a horse ill. Keep away chocolate, bread, and anything with sugar in it."),
    # A tortoise is not a small furry pet and the dog's list is wrong for it twice over: fruit is
    # a rare treat rather than food, and the protein and dairy in a plate's worth of anything does
    # the shell and the kidneys harm. "Can my tortoise eat apple" had no answer but the
    # whether-fruit-skin-is-edible card.
    "tortoise": ("Weeds and leaves are the diet - dandelion, clover, plantain, sow thistle and "
                 "the leaves of most garden weeds - with a proper tortoise pellet for the "
                 "vitamins. Apple, strawberry, tomato and grapes are a rare treat, once a week at most, "
                 "because the sugar upsets the gut; no dairy, no meat, no chocolate, no dog or cat "
                 "food and no bread. Wash anything picked near a road, and never feed anything "
                 "from a weedkilled lawn."),
}
# A named food for a tortoise is the same answer whichever food it is, because the reply already
# says which of them are a rare treat and which never. Only a named food comes here: the plain
# "what do tortoises eat" is a different row's question, and it already answers it well.
SMALL_PET_FOODS["tortoise"] = {
    food: SMALL_PET_DIET["tortoise"]
    for food in ("apple", "apples", "strawberry", "strawberries", "lettuce", "tomato",
                 "tomatoes", "banana", "bananas", "grape", "grapes", "raisin", "raisins",
                 "bread", "cheese", "carrot",
                 "carrots", "cucumber", "chocolate", "dandelion", "clover", "pellet", "pellets")
}
SMALL_PET_FOODS["horse"] = {
    "apple": "Apples are a treat for a horse, not food: one or two a day, cut into pieces so it "
             "does not choke, and never the core. Hay and grass are the diet, and a horse that has "
             "had a bucket of them will be loose behind before the day is out.",
    "apples": "Apples are a treat for a horse, not food: one or two a day, cut into pieces so it "
              "does not choke, and never the core. Hay and grass are the diet, and a horse that "
              "has had a bucket of them will be loose behind before the day is out.",
    "carrot": "Carrots are a treat, in pieces, alongside hay and grass - a couple a day is plenty, "
              "and a bucket of them is how a horse gets loose droppings.",
    "carrots": "Carrots are a treat, in pieces, alongside hay and grass - a couple a day is "
               "plenty, and a bucket of them is how a horse gets loose droppings.",
    "grass": "Grass is the diet for a horse at pasture, but not cut grass: lawn clippings ferment "
             "in the gut and can cause laminitis, so they go on the compost and not in the "
             "bucket. A pony on rich spring grass needs it restricted.",
    "hay": "Hay is the food: free access, a slice or two a day for a stabled horse, and it is what "
           "keeps the gut moving. Feed it off the ground or from a net, not on the bed.",
    "chocolate": "No, and it is a vet call: chocolate is poisonous to a horse as it is to a dog. "
                 "Ring the vet with the weight of the horse and how much it ate.",
    "grape": "Grapes are a treat, a small handful at most: they are mostly sugar, and a horse that "
             "gets sugar in a bucket gets loose droppings. Cut them in half so it does not bolt "
             "them, and keep them out of the feed if it has had laminitis.",
    "grapes": "Grapes are a treat, a small handful at most: they are mostly sugar, and a horse "
              "that gets sugar in a bucket gets loose droppings. Cut them in half so it does not "
              "bolt them, and keep them out of the feed if it has had laminitis.",
    "raisin": "A raisin is a grape with the sugar concentrated, so it is a treat and a small "
              "handful at most, and not something to put in a bucket of feed.",
    "raisins": "A raisin is a grape with the sugar concentrated, so it is a treat and a small "
               "handful at most, and not something to put in a bucket of feed.",
    "bread": "A handful of bread does no harm as a treat, but it is not food: hay and grass are, "
             "and too much starchy food is what brings laminitis on.",
}
SMALL_PET_ASK = ("cheese", "banana", "bananas", "lettuce", "apple", "apples", "carrot", "carrots",
                 "avocado", "chocolate", "grapes", "raisins", "onion", "onions", "garlic", "bread",
                 "rice", "pasta", "cucumber", "spinach", "kale", "tomato", "tomatoes", "nuts",
                 "seeds", "egg", "eggs", "broccoli", "potato", "potatoes", "orange", "strawberry",
                 "melon", "cabbage", "parsley", "hay", "grass", "weed", "weeds", "dandelion",
                 "fruit", "fruits", "veg", "vegetables", "salad", "peas", "berry", "berries",
                 # "what can i feed my guinea pig" names no food at all, and the diet is the
                 # answer to it: the ask words are the ask, and the row needs one of them.
                 "feed", "feeding", "food", "diet", "eat", "eats", "eating")


def _small_pet_kind(text):
    """The small animal the line names, as the name this table is keyed by."""
    # A gerbil before a hamster: main's SMALL_PET_HAMSTER holds "gerbil" too (the bedding answer is
    # the same), so reading it first gave a gerbil the hamster's diet and left the gerbil row of
    # this table with no way to be reached.
    if re.search(r"\b(?:gerbil|gerbils)\b", text):
        return "gerbil"
    if SMALL_PET_HAMSTER.search(text):
        return "hamster"
    if SMALL_PET_GUINEA.search(text):
        return "guinea pig"
    if re.search(r"\b(?:budgie|budgies|budgerigar|parakeet|cockatiel|canary|parrot|parrots|"
                 r"bird|birds)\b", text):
        return "bird"
    if re.search(r"\b(?:chinchilla|chinchillas)\b", text):
        return "chinchilla"
    if re.search(r"\b(?:tortoise|tortoises|turtle|turtles)\b", text):
        return "tortoise"
    if re.search(r"\b(?:horse|horses|pony|ponies|foal|foals|mare|mares|gelding|geldings)\b",
                 text):
        return "horse"
    return ""


def _small_pet_food(understood):
    """What the animal in the line may eat, in that animal's own terms.

    One food answers one way; any other food gets the animal's list of the ones to refuse, which
    is the answer a person asking about a hamster actually needs, and it is never the dog's list.
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    kind = _small_pet_kind(text)
    if not kind:
        return None
    words = set(re.findall(r"[a-z']+", text))
    for food, how in SMALL_PET_FOODS.get(kind, {}).items():
        if food in words or (len(food) > 3 and food + "s" in words):
            return how
    if kind in ("tortoise", "horse"):
        # "What do tortoises eat" and "what do horses eat" already have good answers in this file,
        # and this reply is for a named food, so one of them with no food named is that row's
        # question: the horse answer there has the 2% of body weight a day in it, which is what a
        # person asking the general question wants.
        return None
    return SMALL_PET_DIET[kind]


def _pet_words(understood):
    """The animal the line names, so a cat question is answered about a cat and not about a dog.

    "Can cats eat tuna" was answered "yes, and it is what a poorly dog is fed on": the food was
    keyed, the animal was not. One word, three forms, and every reply uses them.
    """
    text = (understood or {}).get("clean") or ""
    # A follow-up names no animal at all: after "my cat milly is 12", "she's been drinking a lot
    # more water" is about the cat, and the understanding engine says so. Without this the figure
    # for a dog was read out to a cat owner. See bot/understanding/references.py.
    pointed_at = (understood or {}).get("animal_in_hand") or ""
    if pointed_at:
        if pointed_at.startswith(("cat", "kitten")):
            return {"one": "a cat", "kind": "cat", "they": "cats"}
        if pointed_at.startswith(("rabbit", "bunny")):
            return {"one": "a rabbit", "kind": "rabbit", "they": "rabbits"}
        if pointed_at.startswith(("dog", "pupp")):
            return {"one": "a dog", "kind": "dog", "they": "dogs"}
        text = pointed_at
    if re.search(r"\b(cat|cats|kitten|kittens)\b", text):
        return {"one": "a cat", "kind": "cat", "they": "cats"}
    if re.search(r"\b(rabbit|rabbits|bunny|bunnies)\b", text):
        return {"one": "a rabbit", "kind": "rabbit", "they": "rabbits"}
    return {"one": "a dog", "kind": "dog", "they": "dogs"}


# A dog panting is how it cools down, so the word alone is not this card. The words that make
# panting worth a vet for a dog are the ones that mean the breathing itself is wrong.
_IS_PANTING = re.compile(r"\b(pant|pants|panted|panting)\b")
_BREATHING_ITSELF = re.compile(r"\b(breath\w*|breathe?\b|lips|gums|tongue|blue|collapse\w*|"
                               r"laboured|labored|open mouth|mouth open|struggl\w*)")


def _breathing_fast(memory, understood):
    """Fast or laboured breathing is an emergency, for whichever animal the line named.

    A panting dog is a dog cooling down - after a run, on a warm night, at a strange noise - so
    "my dog is panting", "my dog keeps panting" and "my old dog is panting" decline this entry
    and keep whatever answer main had. A cat that pants is a vet call, because a cat has no
    reason to pant, and so is either animal once the line says what the breathing is doing.
    """
    text = (understood or {}).get("clean") or ""
    pet = _pet_words(understood)
    if pet["kind"] == "dog" and _IS_PANTING.search(text) and not _BREATHING_ITSELF.search(text):
        return None
    return ("Ring the vet now: {one} breathing more than about 40 breaths a minute at rest, or "
            "breathing with the mouth open, is an emergency, and cats and dogs both hide chest and "
            "heart trouble until it is serious. Keep them cool and quiet, and carry them in rather "
            "than letting them walk.").format(**pet)


# A line about an animal none of these answers is written for: a guinea pig is not a small dog,
# and both new pet entries fall back to the dog text when the animal is not a cat, dog or rabbit.
# "Is my guinea pig bored" was answered "A dog is bored because the day is short on sniffing",
# so the animal the entry cannot speak for has to pass rather than be guessed at.
OTHER_PETS = ("guinea pig", "guinea pigs", "guinea", "hamster", "hamsters", "gerbil", "gerbils",
              "chinchilla", "chinchillas", "ferret", "ferrets", "parrot", "parrots", "budgie",
              "budgies", "parakeet", "cockatiel", "tortoise", "tortoises", "lizard", "lizards",
              "snake", "snakes", "gecko", "geckos", "fish", "goldfish", "rat", "rats",
              "mouse", "mice", "degus", "hedgehog", "hedgehogs", "chicken", "chickens", "duck")


# The animals an "is it ill" answer can speak for, which is every pet whose owner watches for the
# same handful of signs. A rabbit was not in it: "my rabbit is not well" was answered "A rabbit -
# how long has it been with you?", a question about a pet that had just been described as ill.
ANIMALS_ILL = ("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "pup", "pet", "pets",
               "rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs", "guinea",
               "hamster", "hamsters", "gerbil", "gerbils", "ferret", "ferrets", "chinchilla",
               "chinchillas", "rat", "rats", "mouse", "mice", "budgie", "budgies")


def _other_pet(understood):
    """True when the line names a pet these answers are not written for."""
    text = " " + str((understood or {}).get("clean") or "").lower() + " "
    return any(" " + word + " " in text for word in OTHER_PETS)


def _pet_wound(memory, understood):
    """A cut on a pet, about the animal the line named: a cat is not "him"."""
    return PET_WOUND_REPLY.format(**_pet_words(understood))


# "He's neutered" is a fact about the animal, not a question about when to have it done. The
# row's avoid list catches the written "is neutered", but people type "hes neutered" and
# "shes spayed", and in a chat about a cat weeing on the bed that line was answered with the age
# to neuter a kitten - the wrong half of the subject, and in the female for a male cat. The
# marker is read off the normalised line, which is where "hes" has become "he is".
_NEUTER_ALREADY_DONE = re.compile(
    r"\b(?:he|she|it|they|both|is|are|was|were|has|have|had|been|already|got|now)\b"
    r"[^.?!]{0,30}?\b(?:neutered|spayed|castrated|snipped|done)\b")
# The same shape with a "not" in it says the opposite: "my kitten isnt neutered yet" was read as a
# done animal and answered with the six weeks of hormones settling, which is the answer for the
# animal that has had it. The negation is read on the words just before the operation word, so a
# "not" about something else ("my cat is neutered, not eating") is not this.
_NEUTER_NOT_DONE = re.compile(
    r"\b(?:not|never|isnt|isn'?t|wasnt|wasn'?t|hasnt|hasn'?t|havent|haven'?t|wont|won'?t)\b"
    r"[^.?!]{0,25}?\b(?:neutered|spayed|castrated|snipped|done)\b")
# The same words are the question when a person asks whether or when, and those keep the age,
# the price and the days after the operation.
_NEUTER_STILL_ASKED = re.compile(
    r"\b(should|shall|when|what age|how old|how long|how much|cost|costs|price|worth|why|if|whether|"
    r"whether|know|check|confirm|tell|recover|recovery|heal|after the (?:op|operation))\b")
# The day of the operation is not the fact of it: a cat done yesterday, or one not eating after
# it, is the aftercare card's line and this one stands down with None.
_NEUTER_THE_DAY_OR_AFTER = re.compile(
    r"\b(yesterday|today|tonight|tomorrow|this morning|last night|just had|just been|stitches|"
    r"stitch|cones?|wound|licking|not eating|wont eat|won't eat|sleepy|lethargic|sick|vomiting|"
    r"recovering|recovery|dropping him off|dropping her off|picking him up|picking her up|"
    r"how long does it take to recover|the op|the operation)\b")
# "How do I know if he has been done" is a real question and had no card at all: the answer is
# what a vet looks at, and where the record is.
_NEUTER_HOW_TO_TELL = re.compile(
    r"\b(how (?:do|can|would) i (?:know|tell)|how to tell|whether (?:he|she|it|they|my \w+) "
    r"(?:has|have|had|is|are|was|were)|if (?:he|she|it|they|my \w+) (?:has|have|had) been|"
    # the question asked flat out: "is my cat neutered" was read as a statement of fact and told
    # the hormones had settled, which is the one thing the person is trying to find out
    r"^(?:is|are|was|were) (?:my|our|the|your|his|her|he|she|it|they) (?:\w+ )?"
    r"(?:already )?(?:neutered|spayed|castrated|snipped|done)\b)")
# What a person does with the fact once they have said it: a cat or dog that is already done and
# still wees, sprays, marks or mounts is the behaviour question, not the operation.
_NEUTER_BEHAVIOUR = re.compile(
    r"\b(wee|wees|weeing|weed|peed?|peeing|wee'd|spray|sprays|spraying|sprayed|mark|marks|"
    r"marking|marked|hump|humps|humping|humped|mount|mounts|mounting|mounted|litter|tray|"
    r"outside|bed|sofa|carpet|rug|furniture|scratching|running off|roaming|fighting|pregnant|"
    r"pregnancy|in season|on heat|season)\b")
# The operation still to come is not a fact about an animal that has had it: "my cat is booked in to
# be spayed next week" asks what to do before then, so the done reply stands down and the timing
# card answers, as it did before.
_NEUTER_NOT_YET = re.compile(
    r"\b(booked|booking|next week|next month|next year|next monday|next tuesday|next friday|"
    r"going to be|will be|is being|having him|having her|havent yet|haven't yet|not yet|"
    r"due to be|planned|planning|should i get)\b")
# A line that says the animal is done and then goes on about its weight, coat or teeth asks about
# that other thing: the row says nothing and the card for the other thing answers.
_NEUTER_ALSO_ABOUT = re.compile(
    r"\b(fat|fatter|overweight|underweight|weight|diet|food|feed|feeding|eating|eats|kilos?|kg|"
    r"coat|fur|skin|itch|itchy|scratchy|bald|hair|teeth|breath|ear|ears|eye|eyes|limp|vomit|"
    r"sick|diarrh|worm|worms|flea|fleas|tick|microchip|vaccin|jab|insurance|travel|pet passport|"
    r"holiday|landlord|meow|noise|crying|sleeps|sleeping|groom)\b")


def _the_neuter_is_done(understood):
    """True when the line states the animal has already been neutered, and asks nothing."""
    read = understood or {}
    said = " ".join(str(read.get(key) or "") for key in ("norm_text", "clean")).lower()
    if not _NEUTER_ALREADY_DONE.search(said) or _NEUTER_NOT_DONE.search(said):
        return False
    return not _NEUTER_STILL_ASKED.search(said)


def _the_sex_words(understood):
    """The line's own words, for reading the sex of the animal it is about."""
    read = understood or {}
    return " ".join(str(read.get(key) or "")
                    for key in ("clean", "text", "animal_in_hand")).lower()


def _the_neuter_sex(memory, understood):
    """Whether the animal the line is about is male, female, or not said.

    The operation word carries it as well as the pronouns: a person says a cat was spayed, not
    castrated, and the reply used to call a spayed queen "he" and her hormones "his".
    """
    said = _the_sex_words(understood)
    for turn in (memory.get("turns") or [])[-2:]:
        said += " " + (turn.get("user") or "").lower()
    if re.search(r"\b(spay|spays|spayed|spaying|queen|bitch|doe|she|shes|she's|her|hers|"
                 r"girl|female)\b", said):
        return "female"
    if re.search(r"\b(tom|castrat\w*|buck|he|hes|he's|him|his|boy|male|sire)\b", said):
        return "male"
    return ""


def _the_neuter_is_done_reply(memory, understood):
    """What being neutered does and does not change, for the animal and the behaviour in hand."""
    said = " " + ((understood or {}).get("clean") or "").lower() + " "
    for turn in (memory.get("turns") or [])[-3:]:
        said += (turn.get("user") or "").lower() + " "
    animal = _the_animal(understood)["kind"]
    if animal == "animal":
        # the animal named a turn ago is the one the person said it about
        for kind, words in _ANI_KIND:
            if any(re.search(r"\b%s\b" % re.escape(word), said) for word in words):
                animal = kind
                break
    sex = _the_neuter_sex(memory, understood)
    # a spayed queen is not "he": the pronouns come from the line, and a line that does not say
    # gets the neutral wording rather than the male one
    subj = {"female": "she", "male": "he"}.get(sex, "they")
    poss = {"female": "her", "male": "his"}.get(sex, "their")
    them = {"female": "her", "male": "him"}.get(sex, "them")
    # "they uses" is not English: where the line does not say, the noun keeps the verb right
    who = {"female": "she", "male": "he"}.get(sex, "the cat")
    behaviour = bool(_NEUTER_BEHAVIOUR.search(said))
    if animal == "cat" and behaviour:
        return ("Then it is not the hormones: a neutered cat that sprays or wees outside the tray "
                "is usually stressed or has a urine infection. Put a tray on every floor %s uses "
                "and scoop it daily, plug in a pheromone diffuser, clean the spot with an enzyme "
                "cleaner rather than bleach, and see the vet first if it started suddenly or %s "
                "strains and passes little. The other sprayers are new cats outside the window, "
                "a moved tray and building work." % (who, who))
    if animal == "cat":
        return ("Then the spraying, roaming and fighting that the operation stops are already "
                "handled: %s hormones settle about six weeks after it, so anything that starts "
                "after that is stress or habit rather than hormones. Neutering does not make a "
                "cat lazy or change its character, only the urge to roam, spray and fight."
                % poss)
    if animal == "dog" and behaviour:
        return ("A neutered dog can still mount, mark and pull towards a bitch, because the "
                "hormones take about six weeks to settle after the operation, and a dog done "
                "later can keep the habit for longer. Interrupt it and reward the alternative - "
                "send %s to the same spot outside and praise it - and wash an indoor mark with "
                "an enzyme cleaner so the smell does not call %s back." % (them, them))
    if animal == "dog":
        return ("Then the roaming, mounting and marking that the operation changes settle about "
                "six weeks after it as the hormones drop, and they are the main thing it changes. "
                "Anything left after that is training rather than hormones, and a neutered dog "
                "does not need to put on weight - feed the same portions unless the vet says "
                "otherwise.")
    if animal == "rabbit":
        # a spayed rabbit's reason is the womb cancer, not the spraying: the generic answer read
        # "spray and fight" to a person who had just said their rabbit was spayed
        return ("For a doe the operation is the protection that matters: unspayed does get cancer "
                "of the womb young, and most have it by four, so being done is the right state to "
                "be in. It does not change a rabbit's character or make it put on weight on its "
                "own, and a buck is done mostly for the spraying and the mounting - keep the hay "
                "and the portions as they were and watch the weight over the winter.")
    return ("The urge to roam, spray and fight fades over about six weeks after the operation as "
            "the hormones drop, so behaviour that starts later is habit or stress rather than "
            "hormones. Being neutered does not change an animal's character, and it does not make "
            "one put on weight on its own - keep the food and exercise as they were.")


def _pet_neuter(memory, understood):
    """When to have an animal neutered, about the animal the line named."""
    said = " ".join(str((understood or {}).get(key) or "")
                     for key in ("clean", "norm_text")).lower()
    if _NEUTER_THE_DAY_OR_AFTER.search(said) and not re.search(
            r"\b(should|when|what age|how old)\b", said):
        # the operation was yesterday, or the animal is not right after it: that is the aftercare
        # card's, and this row says nothing rather than the date
        return None
    if (_NEUTER_HOW_TO_TELL.search(said)
            and re.search(r"\b(neutered|spayed|castrated|the snip|done)\b", said)
            and not _NEUTER_BEHAVIOUR.search(said)):
        return ("Ask the vet to look, because most of it is a hands-on check: a male done a while "
                "ago has an empty scrotum, and a spayed female usually has no scar you can see. "
                "Rescue cats are often ear-tipped or tattooed, and the practice that did the "
                "operation has it on the record - so ring them, or the vet who has the animal's "
                "history, rather than guessing from behaviour alone.")
    if _the_neuter_is_done(understood) and not _NEUTER_NOT_YET.search(said):
        if _NEUTER_ALSO_ABOUT.search(said) and not _NEUTER_BEHAVIOUR.search(said):
            # it is done, and the line asks about something else: let that card answer
            return None
        # "hes neutered" in a chat about a cat weeing is a fact, not a question about the age
        return _the_neuter_is_done_reply(memory, understood)
    text = (understood or {}).get("clean") or ""
    # a price question wants the price, for whatever animal the line names, so this comes before
    # the age: "how much does it cost to spay a rabbit" was getting the rabbit's age (a reviewer
    # of this PR raised it)
    if re.search(r"\b(cost|costs|price|prices|much does it|how much (is|will|would)|cheapest|"
                 r"afford|pay for)\b", text):
        if re.search(r"\b(cat|cats|kitten|kittens|moggy|rabbit|rabbits|bunny|bunnies)\b", text):
            return ("Around £60 to £120 for a cat, more for a female than a male and more in a city "
                    "practice, and a rabbit is usually £80 to £150. Ask for a written quote, since "
                    "some practices add the pain relief or the cone on top, and Cats Protection or "
                    "the PDSA can help with a voucher if money is tight.")
        return ("Around £150 to £300 to castrate a dog and £200 to £400 to spay a bitch, depending "
                "on the size of the dog and the practice. Ask for a written quote that includes the "
                "pain relief and the follow-up check, and the Dogs Trust or the PDSA can help if "
                "money is tight.")
    if re.search(r"\b(rabbit|rabbits|bunny|bunnies)\b", text):
        return ("Rabbits are done from four months for a buck and five or six for a doe, and a doe "
                "that is never bred should be spayed: unspayed does get cancer of the womb young, "
                "and most have it by four. Ask a rabbit-savvy vet, since the anaesthetic is the "
                "risky part.")
    if re.search(r"\b(recover|recovery|recovering|after the (operation|op)|stitches|cones?|"
                 r"how long (does|till|until).*(take|recover)|come home)\b", text):
        # "how long does a cat take to recover from neutering" is about the days after, not the
        # age, and the age answer would be no answer at all
        pet = _pet_words(understood)
        return ("Most are home the same day and back to normal in two or three days: keep {one} "
                "quiet and indoors, no jumping or stairs, and let {one} sleep it off. A cone or a "
                "baby vest goes on if {one} licks at the wound, and the wound wants a look twice a "
                "day for redness, swelling or oozing. Ring the vet if {one} is not eating by the "
                "next morning, is sick, or the skin looks open. A male is usually himself again in "
                "a day or two; a female takes the longer end, about a week, with the stitches out "
                "at ten days.").format(**pet)
    if re.search(r"\b(cat|cats|kitten|kittens|moggy)\b", text):
        # the animal's own sex, because a male cat is not "she": "my tom is not done yet, when
        # should i have him neutered" was answered in the female every time
        if _the_neuter_sex(memory, understood) == "male":
            return ("Cats are usually done from four to six months, and a male is done at the the "
                    "same age as a female: the reason for a tom is the spraying, the roaming and "
                    "the fights, and those calm down about six weeks after the operation as his "
                    "hormones settle. Book it once he is his normal self after his vaccinations, "
                    "keep him in for a day or two after, and ring the vet if he is not eating by "
                    "the next morning.")
        if _the_neuter_sex(memory, understood) == "female":
            return ("Cats are usually done from four to six months, before the first season: a "
                    "queen can get pregnant at four months. Book it once she is her normal self "
                    "after her vaccinations, keep her in for a day or two after and give the vet "
                    "a call if she is not eating by the next morning. A male cat is done the same "
                    "age and calms down from the spraying once his hormones settle, about six "
                    "weeks later.")
        return ("Cats are usually done from four to six months, before the first season: a queen "
                "can get pregnant at four months, and a tom is done at the same age, which stops "
                "most of the spraying and roaming about six weeks later as the hormones settle. "
                "Book it once the cat is its normal self after the vaccinations, keep it in for "
                "a day or two after, and ring the vet if it is not eating by the next morning.")
    return ("Dogs are usually done from six months, and puppies of the big breeds wait until nine "
            "to twelve months so their joints finish growing - your vet will say which for your "
            "breed. Book it in once he is well and his vaccinations are done, and expect him to be "
            "quiet for a day or two with a cone on for a week. Neutering a bitch before her first "
            "season lowers her chance of mammary tumours.")


# A dog licking a paw and a cat licking a paw are the same question - a sore or an itch - but the
# causes are not the same, and a cat that stops grooming is the ill one. firm-sheep found the cat
# half: the licking words had been taken out of the wound entry, so "my cat wont stop licking her
# paw" fell to a cat-repellent garden answer.
DOG_PAW_LICK_REPLY = (
    # main's own dog answer, word for word, because it names the three causes the question is
    # asking about in its first sentence; the brown stain is the one sign it was missing
    "A dog who licks his paws is usually itchy: grass or pollen allergy, harvest mites "
    "between the toes, or a food allergy. Wash and dry the paws after walks, keep the hair "
    "between the pads short, and see the vet if the skin is red, smelly or the licking is "
    "constant, because an infection or a grass seed needs treating. A brown stain on the fur "
    "means weeks of it.")

CAT_PAW_LICK_REPLY = (
    "Cats wash constantly, so licking is only a problem when it is aimed at one spot: a cat "
    "working at a paw for minutes at a time is sore, itchy or stressed. Turn the paw over and "
    "look between the toes for a thorn or a grass seed, and part the fur for tiny black specks "
    "of flea dirt - a flea allergy is the commonest cause and one flea is enough. A bald or red "
    "patch, a swollen toe or a cat who has stopped grooming the rest of herself needs the vet "
    "within a day or two. Feliway or a quiet room helps the stress kind, and a cat collar has to "
    "be a snap-release one.")


def _paw_licking(memory, understood):
    """The same question for a dog and for a cat, in the words each owner needs."""
    if _pet_words(understood)["kind"] == "cat":
        return CAT_PAW_LICK_REPLY
    return DOG_PAW_LICK_REPLY


def _bone_hazard(memory, understood):
    """Cooked bone advice, about the animal the line named."""
    pet = _pet_words(understood)
    return ("Cooked bones are the worry, because they splinter: chicken, turkey and lamb chop "
            "bones in particular. Don't make {one} sick and don't pull anything out of the mouth "
            "with your fingers. Ring the vet today and say what kind of bone, roughly how big and "
            "how long ago, and watch for retching, drooling, a hard or swollen belly, or pain when "
            "you touch it - any of those means the vet now, not tomorrow. A raw bone is softer, "
            "but a piece that gets stuck is the same problem.").format(**pet)


def _raw_meat(memory, understood):
    """Raw meat is a bacteria question, and the answer has to be about the pet in the line."""
    pet = _pet_words(understood)
    return ("Raw chicken often carries campylobacter and salmonella, and a {kind} that has eaten "
            "some may bring it up or have a day or two of loose stools; most ride it out. Give "
            "{one} water, keep {one} off the beds and out of the kitchen while loose, wash your "
            "hands and the bowl, and ring the vet if the sickness lasts more than a day, if there "
            "is blood, or if {one} is flat and not drinking.").format(**pet)


def _grapes(memory, understood):
    pet = _pet_words(understood)
    return ("Ring your vet today and say how many and how long ago, even if {one} seems fine: "
            "grapes and raisins can shut down a {kind}'s kidneys, and there is no amount known to "
            "be safe, so a small one and a handful is enough to treat. Treatment works much better "
            "started early, and the vet may make {one} sick or give fluids.").format(**pet)


def _can_pet_eat(understood):
    """The answer for a named food: a word of caution, a yes, or a pointer to the bad list.

    Every reply is one template with {one}, {kind} and {they} in it, so the animal the line
    named is the animal the answer is about. Nothing else in the text is a brace.
    """
    text = " " + re.sub(r"[^a-z' ]+", " ", ((understood or {}).get("clean") or "").lower()) + " "
    words = set(re.findall(r"[a-z']+", text))
    pet = _pet_words(understood)

    def named(food):
        # "grapes" and "grape" are one food, and so are "onions" and "onion"
        if any(word == food or (len(food) > 3 and word.startswith(food)) for word in words):
            return True
        # A food whose name is two words never matched a word list split on spaces: "ice cream"
        # and "raw egg" were in the table and the row still answered with the list of everything
        # to refuse. The phrase is looked for in the line itself.
        return " " in food and food in text

    for food, how in CAUTION_FOODS.items():
        if named(food):
            return ("Careful: " + how).format(**pet)
    for food, how in SAFE_FOODS.items():
        if named(food):
            return ("Yes: " + how + ". Keep it to a small amount and off the dinner plate, "
                    "because a pet that begs gets fat and a fat {kind} gets joint trouble. "
                    "Anything new is worth a small piece of first, and a look an hour later."
                    ).format(**pet)
    return ("The ones to refuse are grapes and raisins, onions, garlic, leeks, chocolate, "
            "macadamia nuts, xylitol in sugar-free gum and raw dough. Plain cooked meat, rice, "
            "carrot and apple are fine in small amounts. If it was one of the bad list, ring the "
            "vet now rather than waiting for a symptom.")


# The bowl that belongs to the other animal in the house: "how do i stop my cat eating the
# dogs food" names two animals and one dinner, and it is a feeding question rather than a
# can-I-eat-this one. The words are matched as phrases with a space either side so "dog food"
# has to sit together, and the reading is the same `words` list every row reads.
_OTHER_PETS_DINNER = ("dog food", "dogs food", "dog s food", "dog dinner", "dogs dinner",
                      "dog s dinner", "dog bowl", "dogs bowl", "dog s bowl", "cat food",
                      "cats food", "cat s food", "cat dinner", "cats dinner",
                      "cat s dinner", "cat bowl", "cats bowl", "cat s bowl",
                      "each others food", "each others dinner", "the others food",
                      "the others dinner", "the others bowl", "rabbit food",
                      "rabbits food", "hamsters food", "guinea pigs food",
                      # "how do i feed two cats when one eats everything" names the two of them
                      # and no bowl at all
                      "two cats", "two dogs", "two kittens", "two puppies", "both cats",
                      "both dogs")
# What is happening to it: somebody is stopping it, keeping them off it, or already eating it.
# "can my dog eat cat food" has none of these, because it asks a different question.
_DINNER_TAKEN = ("stop", "stops", "stopped", "keep", "keeps", "keeping", "steal", "steals",
                 "stole", "stolen", "stealing", "eat", "eats", "eating", "ate", "eaten", "grabs",
                 "grabbing", "raids", "raiding", "snaffles", "snaffling",
                 # "my dog is always in the cats food" names no verb but says the habit
                 "always")


# Somebody is doing something about it: stopping it, keeping them apart, or having just watched
# it happen. These win over everything below, because "how do i stop my dog eating the cat food"
# is this question however it is phrased.
_DINNER_STOPPED = ("stop", "stops", "stopped", "keep", "keeps", "keeping", "steal", "steals",
                   "stole", "stolen", "stealing", "grabs", "grabbing", "raids", "raiding",
                   "snaffles", "snaffling")
# "can my dog eat cat food" is a permission question about the food itself, and the can-eat row
# answers it better; a pet that has gone off the other's dinner is a refusal question.
_DINNER_ASKED_OR_REFUSED = ("can", "could", "is it ok", "is it safe", "ok to", "safe to",
                            "allowed", "should i give", "should i feed", "wont eat",
                            "won't eat", "not eating", "stopped eating", "isnt eating",
                            "off his food", "off her food", "refusing")
# A person who ate the pet's dinner is a different worry, and the same words are in the line:
# "my toddler ate the dog food" is not a two-bowl problem and wants the poison-and-vet answer.
_A_PERSON_DID_IT = ("son", "sons", "daughter", "daughters", "child", "children", "kid", "kids",
                    "toddler", "toddlers", "baby", "babies", "boy", "girl", "grandson",
                    "granddaughter", "husband", "wife", "partner", "mum", "mom", "dad",
                    "i ate", "i ate some")
# One bowl raided and the animal is now ill is a sick-animal line, not a feeding routine: the
# vomiting, the diarrhoea and the bland-food rows answer those, so this one stands down for them.
# "my dog ate the cat food and was sick" wants the plain-chicken-and-rice answer, and the cat it
# names in passing must not take it to the cat-sick card.
_THE_ANIMAL_IS_ILL = ("sick", "sicker", "sickness", "poorly", "unwell", "ill", "vomiting",
                      "vomited", "vomits", "threw up", "throwing up", "been sick", "being sick",
                      "diarrhoea", "diarrhea", "the runs", "loose stools", "runny poo",
                      "bad tummy", "bad stomach", "upset stomach", "upset tummy", "the squits")


def _one_pets_dinner(memory_or_understood, understood=None):
    """True when the line is one animal getting at the other animal's dinner."""
    read = understood if understood is not None else memory_or_understood
    words = " " + " ".join((read or {}).get("words") or ()) + " "
    if not any(f" {phrase} " in words for phrase in _OTHER_PETS_DINNER):
        return False
    if any(f" {person} " in words for person in _A_PERSON_DID_IT):
        return False
    if any(f" {word} " in words for word in _THE_ANIMAL_IS_ILL):
        return False
    if any(f" {word} " in words for word in _DINNER_STOPPED):
        return True
    if any(f" {phrase} " in words for phrase in _DINNER_ASKED_OR_REFUSED):
        return False
    return any(f" {word} " in words for word in _DINNER_TAKEN)


# A line that says the animal has died is about the death, not about its hutch, its food or its
# training: the pet-loss entry and the composer answer those.
ABOUT_A_DEATH = ("died", "dying", "dead", "passed away", "passed on", "put down", "put to sleep",
                 "euthanised", "euthanized", "bury", "buried", "burying", "burial", "body",
                 "ashes", "cremated", "cremation", "cremate", "grieving")
def _rabbit_weather(memory, understood):
    """Hot or cold: a rabbit needs different things in each, and both are asked as "keep it ..."."""
    words = set((understood or {}).get("words") or ())
    if {"cold", "winter", "freezing", "frost", "warm", "warmth", "snow"} & words:
        return ("Keep the hutch out of the wind and rain, with a dry, deep bed of hay or straw to "
                "burrow into, and a cover or an old duvet over the mesh at night, leaving the "
                "front open for air. Two rabbits huddle and keep each other warm, so a single one "
                "needs the extra bedding. Give warm water rather than cold, and check the bottle "
                "has not frozen.")
    return ("Shade, a second bowl of water and a frozen bottle of water wrapped in a towel for her "
            "to lean against, with the hutch moved out of the sun for the day. Rabbits cannot "
            "sweat and over 25C is already risky, and you must never bath one to cool her down: a "
            "damp bottom in summer is how flystrike starts. A rabbit stretched out and drooling, or "
            "not eating in the heat, needs the vet that day.")


# The household things that frighten a pet, and the words that say the pet is frightened of one.
# The thing is what makes it that question: "my dog barks at the doorbell" is this, while "my dog
# is scared" on its own is someone's own worry and belongs to the shy-dog answer or to nobody.
_NOISY_THINGS = ("hoover", "vacuum", "vacuum cleaner", "blender", "hairdryer", "hair dryer",
                 "washing machine", "tumble dryer", "balloon", "balloons", "mixer",
                 "food processor", "lawnmower", "lawn mower", "dishwasher", "clippers",
                 "loud noise", "loud noises")
_FEAR_WORDS = ("scared", "afraid", "frightened", "frightens", "frighten", "terrified",
               "terrifies", "terrify", "terrifying", "scares", "scare", "hates", "hate",
               "panics", "panic", "shakes", "shaking", "trembles", "barks", "bark", "barking",
               "runs away", "runs off", "hides", "hiding", "cowers")


def _noise_fear(memory, understood):
    """The noise answer, with the animal the line named in it.

    A cat and a dog are frightened of a vacuum cleaner in much the same way, so this is one
    template with {one} and {they} in it rather than a dog answer read out to a cat owner.
    """
    pet = _pet_words(understood)
    return ("Let {one} leave the room and shut the door - walking away is what settles them - "
            "then switch it on for a few seconds at a time with the food bowl down, stopping "
            "before they bolt. Don't hold {one} still in front of it: a frightened animal that "
            "can't get away gets worse, not braver. If they shake for hours or won't eat "
            "afterwards, ask the vet.").format(one=pet["one"])


# The animal has to be in the line or the few turns before it: "should i drink more water" and
# "is it safe to drink the water in mexico" are keyed on the same two words as "how do i get my
# dog to drink more", and without this guard both got the dog's bowl-and-broth tips.
PET_NAMED = re.compile(
    r"\b(?:dog|dogs|puppy|pup|pups|puppies|cat|cats|kitten|kittens|kitty|rabbit|rabbits|bunny|"
    r"bunnies|hamster|hamsters|guinea pig|guinea pigs|parrot|budgie|tortoise|pet|pets|animal|"
    r"animals)\b")


PERSON_NAMED = re.compile(
    r"\b(?:i|me|my|myself|son|sons|daughter|daughters|husband|wife|partner|baby|child|children|"
    r"kid|kids|mother|mum|mom|father|dad|friend|friends|nan|granny|grandson|granddaughter)\b")


def _pet_in_the_talk(memory, understood):
    """True when the nearest turn that names anyone names a pet.

    "my dog is at the beach" then "he drank sea water" is the dog, so a pet from a turn or two
    back still counts. But "my son was at the beach" then "he drank sea water" is the son, and
    taking any pet from the last three turns sent a person to the vet. So the nearest line that
    names a pet or a person decides, and a pronoun decides nothing either way.
    """
    said = [(understood or {}).get("clean") or ""]
    said += [(turn.get("user") or "").lower() for turn in (memory.get("turns") or [])[-3:]]
    for line in reversed(said):
        if PET_NAMED.search(line):
            return True
        if PERSON_NAMED.search(line):
            return False
    return False


# The animal a follow-up line is about, when the line itself only says "he" or "she".
_ANIMAL_IN_A_TURN = re.compile(
    r"\b(dogs?|pups?|pupp(?:y|ies)|cats?|kittens?|rabbits?|bunn(?:y|ies))\b", re.I)
_ONE_ANIMAL = {"dogs": "dog", "pups": "pup", "puppies": "puppy", "cats": "cat",
               "kittens": "kitten", "rabbits": "rabbit", "bunnies": "bunny"}
_FOOD_OR_DRINK = re.compile(
    r"\b(?:eat|eats|eating|ate|have|has|having|give|giving|drink|drinks|drinking|drank|"
    r"water|thirsty|thirst|hydrat\w*)\b", re.I)
# Who a line is about, without the first person: "what should i feed her" is about the cat the
# chat is on, and its "i" must not turn the next pronoun into a person.
_PERSON_IN_A_TURN = re.compile(
    r"\b(?:son|sons|daughter|daughters|husband|wife|partner|baby|babies|child|children|kid|"
    r"kids|mother|mum|mom|father|dad|friend|friends|nan|granny|grandson|granddaughter)\b")


def the_animal_follow_up_line(text, memory):
    """The line with the chat's animal in place of a bare pronoun, or "".

    "my dog is 8 and a bit overweight" / "can he have cheese" is the dog's question, but the
    second line names no animal, so the pet rows cannot reach it and the cooking rows answer it
    as an omelette. The same goes for a rabbit and a carrot, and for a cat that will not drink.
    Only a line that asks about food or drink and whose nearest named person or animal is a pet
    is rewritten: a person's "can he have cheese" is left to the cooking rows.
    """
    said = str(text or "").lower()
    if not said or PET_NAMED.search(said) or not _FOOD_OR_DRINK.search(said):
        return ""
    pronoun = re.search(r"\b(?:he|she|him|her)\b", said)
    if pronoun is None:
        return ""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    recent = [str((turn or {}).get("user") or "").lower()
              for turn in reversed((turns or [])[-3:])]
    for line in [said] + recent:
        named = _ANIMAL_IN_A_TURN.search(line)
        if named is not None:
            word = named.group(1).lower()
            animal = _ONE_ANIMAL.get(word, word.rstrip("s"))
            return said[:pronoun.start()] + "my " + animal + " " + said[pronoun.end():]
        if _PERSON_IN_A_TURN.search(line):
            return ""
    return ""


def _pet_drink_more(memory, understood):
    """"How do I get my cat to drink more" - the encourage-it question, which the amount answer
    never met. Cats in particular take most of their water from food, so the tips differ.
    """
    if not _pet_in_the_talk(memory, understood):
        return None
    pet = _pet_words(understood)
    text = (understood or {}).get("clean") or ""
    if re.search(r"dehydrat|how do i know|drinking enough|signs?\b", text):
        if pet["kind"] == "cat":
            return ("Lift her scruff: on a hydrated cat it springs back at once, and on a dry one it "
                    "stays up in a tent. Check the gums too - wet and pink is right, tacky or pale "
                    "needs the vet - and the litter tray: a cat that stops weeing for a day is an "
                    "emergency. A cat that is also off her food or hiding is not a wait-and-see.")
        return ("Lift the skin on his back: it should drop straight back, and slow is a sign he is "
                "short of water. Look at the gums - wet and pink is right, tacky or pale is not - "
                "and count the wees: dark, strong-smelling or fewer than usual means water first "
                "and the vet today. A dog that is also sick or loose dehydrates fast.")
    if pet["kind"] == "cat":
        return ("Switch part of the dry food to wet, which is where most of a cat's water comes "
                "from, and add a spoon of warm water to the wet food. Then make water worth "
                "walking to: a wide bowl filled to the brim, several bowls out of the litter tray "
                "and away from the food, and a running tap or a pet fountain. Tuna water in oil "
                "drained off, or a splash of unsalted broth, gets a fussy one going.")
    return ("Add water to his food - a splash in the bowl, or soak the kibble 10 minutes - and put "
            "a second bowl down somewhere he passes, filled to the brim, washed daily. A splash "
            "of unsalted broth or the water from boiled chicken makes it worth drinking, and a "
            "dog that has been running or is on dry food in warm weather needs more than the "
            "same dog on wet food.")


def _pet_salt_water(memory, understood):
    """A pet that has drunk salt water needs the vet, and only a pet's line says so.

    The salt is the danger, not the amount, so this answer is "ring the vet now" rather than the
    thirst answer that tells the owner to measure the bowl. It was keyed on "sea water" and
    "drank" with no animal anywhere, so "i drank salt water at the beach", "my son swallowed sea
    water" and "is sea water safe to drink" were all told to ring the vet for a dog that was not
    there. The animal has to be in the line - or in the last few turns, because "he drank sea
    water" after "my dog is at the beach" is still the dog.
    """
    if not _pet_in_the_talk(memory, understood):
        return None
    pet = _pet_words(understood)
    return ("Ring the vet now and say how much salt water and when: salty water pulls water out of "
            "the body, and {one} that has had a lot will be sick, wobbly or drowsy within a few "
            "hours. Take the fresh water away so there is none to drink, offer small sips of plain "
            "water once the vet has said so, and do not wait for symptoms before you ring - this "
            "one is much easier treated early.").format(**pet)


# A rabbit and a small animal are not small dogs: the checks a dog owner is given - a bowl left in
# the sun, a splash of broth - are not their animal's, and a rabbit that stops drinking is the
# urgent one of the four, because the gut slows within hours. "my rabbit is not drinking" was
# answered with the dog text ("a dog off", "a dog that goes a full day") and "my guinea pig has
# stopped drinking" with the alcohol diary.
SMALL_PETS = re.compile(r"\b(guinea ?pigs?|hamsters?|gerbils?|rats?|mice|mouse|chinchillas?|"
                        r"ferrets?|degus?|hedgehogs?)\b")


def _pet_not_drinking(memory, understood):
    """A pet that will not drink, kept apart from one that drinks too much.

    The thirst answer measured how much a pet drinks; read out to "my dog won't drink water" it
    tells someone their worried dog is drinking too much. Not drinking is the opposite worry, and
    the useful answer is the check list and how long to wait before ringing the vet, in the terms
    of the animal the line names: a rabbit and a guinea pig are not small dogs, and a rabbit that
    stops drinking is the one that cannot wait.
    """
    text = (understood or {}).get("clean") or ""
    # A rabbit and a small animal are pets the talk has never had before, and PET_NAMED does not
    # carry the small ones, so "my gerbil has stopped drinking" was the only line here that fell
    # past this card to the thirst answer.
    if not (_pet_in_the_talk(memory, understood) or SMALL_PETS.search(text)
            or re.search(r"\b(rabbit|rabbits|bunny|bunnies)\b", text)):
        return None
    pet = _pet_words(understood)
    if re.search(r"\b(rabbit|rabbits|bunny|bunnies)\b", text):
        return ("Ring the vet today: a rabbit that stops drinking is urgent, because the gut slows "
                "within hours and a rabbit not eating or drinking is a same-day emergency rather "
                "than a wait-and-see. While you ring, check the bottle - a stuck ball or a bottle "
                "that has stopped flowing is the commonest reason of all - and put a heavy bowl "
                "down as well, since a rabbit drinking from a bowl takes more. Wet the greens, "
                "offer a little unsweetened apple juice in the water, and keep him warm and quiet "
                "with hay within reach. Hunched, grinding his teeth, or no droppings for a few "
                "hours means the vet now, not tomorrow.")
    if SMALL_PETS.search(text):
        return ("Ring the vet today: a guinea pig, hamster or rat that stops drinking goes "
                "downhill fast, and an animal that is also off its food, hunched or cold needs to "
                "be seen rather than watched. Check the bottle first - the ball stuck, the spout "
                "blocked, the water leaking away or warm - and put a shallow bowl down as well, "
                "because a guinea pig often drinks more from a bowl. Wash the veg and leave it wet "
                "for the water, keep fresh water in two places, and weigh the animal: a small "
                "animal that has lost weight is a vet call even if it is still nibbling.")
    if pet["kind"] == "cat":
        return ("Cats drink little anyway, so check the food first: a cat on wet food gets most "
                "of its water there, and a bowl next to the food or a running tap often starts one "
                "drinking. Offer tuna water or a splash of milk-free broth, keep the water away "
                "from the litter tray, and ring the vet the same day if she has not drunk for 24 "
                "hours, is straining in the tray, or is hiding and off her food.")
    return ("Check the boring things first: a dirty bowl, water left in the sun, or a bowl beside "
            "the food all put a dog off. Wash the bowl, put a second one down somewhere cool, and "
            "add a little water to his food or a splash of unsalted broth. A dog that goes a full "
            "day without drinking, or that is also sick, loose, or dribbling, needs the vet - "
            "especially in warm weather, when dehydration comes on quickly.")


def _pet_thirst(memory, understood):
    """How much a pet drinks, in the numbers for the animal the line named.

    A cat on wet food drinks very little and one on dry food drinks a lot, so the dog's 100ml a
    kilo read out to a cat owner is the wrong fact about the wrong animal.
    """
    pet = _pet_words(understood)
    if pet["kind"] == "cat":
        return ("Measure it for a few days: a cat takes roughly 40 to 60ml per kilo a day, more "
                "on dry food and very little on wet. A cat that suddenly drinks a lot, or sits at "
                "the tap, needs the vet - thirst is how kidney disease and diabetes show first.")
    return ("Measure it: a dog takes about 50 to 100ml per kilo a day, so a 10kg dog drinking "
            "more than a litre is drinking too much. Sudden thirst is a symptom - diabetes, a "
            "kidney problem, or an infection of the womb in a bitch - so ring the vet, and sooner "
            "if he is also off his food or weeing in the house.")


def _pet_limp(memory, understood):
    """A limp, for the animal that has it.

    "Lead walks" is the dog answer, and a cat owner read out of it cannot tell what to do with a
    cat, so the rest is the same and the keeping-still half follows the animal.
    """
    pet = _pet_words(understood)
    if _SMALL_PET_NAMED.search((understood or {}).get("clean") or ""):
        rest = ("Keep him in his own cage on soft, dry bedding with the food and water where he "
                "can reach them without climbing, and handle him as little as you can")
    elif pet["kind"] == "cat":
        rest = ("Keep him in for a couple of days with no jumping up or down - carry him up the "
                "stairs if he will let you, and put the food and litter on the floor")
    elif pet["kind"] == "rabbit":
        rest = ("Keep him in a small run on soft bedding, not the garden, and off anything he can "
                "jump on or off")
    else:
        rest = "Rest him - lead walks to the toilet and nothing more for two days"
    return ("{rest} - and look at the pad for a cut, a thorn or a torn nail. A leg he won't put "
            "weight on, a swelling, or a limp that is no better after two days needs the vet, and "
            "never give ibuprofen or paracetamol: both are poisonous to pets.").format(rest=rest)


_SMALL_PET_NAMED = re.compile(
    r"\b(guinea|guinea pigs?|cavy|hamster|hamsters|gerbil|gerbils|rat|rats|mouse|mice|"
    r"chinchilla|chinchillas|ferret|ferrets)\b")


# A small animal is picked up its own way, and the answer has to open with the animal in the
# line: "my hamster squeaks when i pick him up" read out the rabbit first, which is the one animal
# the person did not ask about.
_A_RABBIT_SAID = re.compile(r"\b(rabbit|rabbits|bunny|bunnies)\b")
_A_GUINEA_SAID = re.compile(r"\b(guinea|guinea pigs?|cavy|cavies)\b")
_A_RODENT_SAID = re.compile(
    r"\b(hamster|hamsters|gerbil|gerbils|rat|rats|mouse|mice|chinchilla|chinchillas)\b")
_A_FERRET_SAID = re.compile(r"\b(ferret|ferrets)\b")

# The animal that is not a rabbit, which is the one `small-pet-biting` writes its answer for.
_A_RODENT_OR_GUINEA = re.compile(
    r"\b(hamster|hamsters|gerbil|gerbils|guinea|guinea pigs?|cavy|cavies|rat|rats|mouse|mice|"
    r"chinchilla|chinchillas)\b")


def _small_pet_handling(memory, understood):
    """How this animal is picked up, said for the animal the line names."""
    text = (understood or {}).get("clean") or ""
    if _A_GUINEA_SAID.search(text):
        lead = ("A guinea pig is scooped up in both hands from underneath, one hand under the "
                "hindquarters and the other across the shoulders, and held low over your lap - "
                "never by the scruff, the ears or a leg, and never up at chest height, because a "
                "guinea pig that is dropped or that jumps from a height breaks its back")
        more = ""
    elif _A_RODENT_SAID.search(text):
        lead = ("A hamster, gerbil, rat or mouse is cupped in both hands, one under the chest and "
                "one over the back, and never picked up by the tail or the scruff")
        more = ""
    elif _A_FERRET_SAID.search(text):
        lead = ("A ferret is picked up round the shoulders with the hindquarters supported in your "
                "other hand, and never by the tail or the ears")
        more = ""
    else:
        lead = ("A rabbit is picked up with one hand under the chest and the other under the "
                "hindquarters, held against your body so the back legs cannot kick out - never by "
                "the ears, the scruff or the back of the neck, because a rabbit that kicks while "
                "nothing is holding its back end can break its own spine")
        more = " and a rabbit that stops eating after it is worth ringing the vet the same day"
    return (lead + ". Sit on the floor with him on your lap for a few minutes a day and a bit of "
            "food in your hand, and put him down before he starts to struggle, so being picked up "
            "stops being a surprise. A pet that squeals, flinches or struggles at being handled "
            "when he did not before needs a vet - a sore tooth, an injured back or mites is the "
            "usual reason" + more + ".")


# A plain "how do i hold a hamster" is the small-rodent card's question, and its answer already
# says the things this card cannot (the hand over the top, the week to settle, the hamster woken
# from a sleep). So this row stands down for a how-to-hold line about a small animal that is not
# a rabbit - and never for a rabbit, and never once the line says the animal flinches, squeals,
# kicks, struggles or is frightened, which is the shape this row was built for.
_A_HOW_TO_HOLD = re.compile(
    r"\b(?:how|what'?s? the best way|what is the best way|best way|properly|should i)\b"
    r"[^.!?]{0,40}?\b(?:hold|holding|pick (?:him|her|them|it)?\s?up|picking (?:him|her|them)?\s?up|"
    r"lift|lifting|handle|handling|carry)\b", re.IGNORECASE)
_A_WONT_BE_HELD = re.compile(
    r"\b(?:wont|won't|will not|refuses?|refusing|refused)\b[^.!?]{0,24}?"
    r"\b(?:hold|held|handle|handled|pick (?:him|her|them)?\s?up|picking|being (?:held|picked))\b",
    re.IGNORECASE)
_A_HURT_OR_FRIGHT = re.compile(
    r"\b(?:flinch\w*|squeal\w*|squeak\w*|scream\w*|screech\w*|cry|cries|crying|yelp\w*|"
    r"kick\w*|struggl\w*|squirm\w*|wriggl\w*|scared|frightened|afraid|nervous|hates?|"
    r"hate being|bit|bites|biting|nip\w*|snapp\w*|pain\w*|hurt\w*|sore|injur\w*)\b",
    re.IGNORECASE)


def _a_plain_hold_is_the_rodents_card(understood):
    """True unless this is a plain how-to-hold line about a small animal that is not a rabbit."""
    text = (understood or {}).get("clean") or ""
    if _A_RABBIT_SAID.search(text) or _A_FERRET_SAID.search(text):
        return True
    if not _A_RODENT_OR_GUINEA.search(text):
        return True
    if _A_HURT_OR_FRIGHT.search(text):
        return True
    return not (_A_HOW_TO_HOLD.search(text) or _A_WONT_BE_HELD.search(text))


# The person a dog is wary of. "My dog barks at my partner" is the shy-dog question, not the
# barking one, so the barking entry stands down on these words and this entry asks for them.
_PERSON_WORDS = ("men", "man", "husband", "partner", "strangers", "stranger", "people",
                 "visitors", "visitor", "guests", "guest", "children", "kids", "child", "someone",
                 "new people", "brother", "sister", "son", "daughter", "dad", "mum", "father",
                 "mother", "grandad", "grandma", "friend", "friends", "neighbour", "neighbor",
                 "postman", "boyfriend", "girlfriend", "baby", "babies", "toddler", "teenagers",
                 "teenager")


# A dog next door is a noise complaint, not the reader's dog to train or to take to the vet:
# every word of the two questions is shared except who the dog belongs to.
_NEIGHBOUR_DOG = ("neighbour", "neighbours", "neighbor", "neighbors", "next door", "upstairs",
                  "downstairs", "flat above", "their dog", "somebody's dog", "someones dog")


# A cat's sex is only in the line when the person says it: "tom", "boy" or the name they call him.
ANIMALS_MALE = ("tom", "tomcat", "male", "boy", "he", "him", "his", "lad", "stud")
ANIMALS_FEMALE = ("queen", "female", "girl", "she", "her", "hers", "mum", "mother")

# A cut on a pet is a vet question, not a human first-aid one: "my dog has a cut on his paw" was
# a shrug ("Sorry to hear that. What would help most right now?"). The pet word is what keeps
# "how do i cut glass" and "my son cut his hand" out of it, since the key wants a cut and an
# animal, and the paw, pad and nose words are there because that is where they get them.
# "scratch" is deliberately not here: a cat scratching the sofa and a dog scratching its ear are
# their own questions, and that word took four furniture lines to the vet.
PET_WOUND = ("cut", "cuts", "gash", "gashes", "wound", "wounded",
             "bleeding", "bleeds", "thorn", "thorns", "glass", "splinter", "slice", "sliced",
             "paw", "paws", "pad", "pads", "nose", "sore", "torn")
PET_WOUND_REPLY = (
    "Bathe it with cool water or salt water, dry it and keep the {kind} from licking it, and get "
    "the vet to look today if it is deep, gaping, bleeding steadily or it will not put weight on "
    "it. Check between the toes and across the pad for glass or a grass seed, since those keep a "
    "small cut open. A nick that has stopped bleeding: bathe it twice a day, keep it dry and "
    "covered on walks, and ring the vet if it goes red, swollen or smelly.")


# How long each animal lives. Small breeds outlive big ones by years, so the dog line gives
# the range and where a dog sits in it, rather than one number that is wrong for half the dogs.
_PET_LIFESPAN = (
    (("dog", "dogs", "puppy", "puppies", "pup"),
     "A dog lives around 10 to 13 years, and where it lands depends mostly on size: small breeds "
     "often reach 14 to 16, while the biggest breeds are usually 8 to 10. Kept lean, walked daily "
     "and seen by a vet once a year, a dog sits at the top of its range."),
    (("cat", "cats", "kitten", "kittens"),
     "An indoor cat lives about 12 to 15 years, and many reach 18 or more. A cat that goes "
     "outside averages a few years less, mostly because of roads, so a cat flap with a curfew or "
     "a secure garden is what buys the extra years."),
    (("rabbit", "rabbits", "bunny"),
     "A rabbit lives 8 to 12 years, which is longer than most people expect when they buy one for "
     "a child. A rabbit on its own in a small hutch usually dies years earlier than a pair with "
     "a run and hay all day, so company and space are the two things that matter."),
    (("hamster", "hamsters"),
     "A hamster lives 2 to 3 years, and a Syrian is at the top of that while a dwarf is usually "
     "closer to 2. That short life is normal rather than a sign you did something wrong."),
    (("guinea pig", "guinea pigs"),
     "A guinea pig lives 5 to 7 years, and they do better in pairs because they are herd animals. "
     "Hay all day and vitamin C in the food are what keep them going that long."),
    (("budgie", "budgies", "parrot", "cockatiel"),
     "A budgie lives 8 to 12 years, and a cockatiel or a small parrot 15 to 25. Company matters "
     "more than anything else: a bird alone in a cage for years usually has a shorter, sadder "
     "life than one with a friend and time out of the cage."),
    (("goldfish", "fish"),
     "A goldfish lives 10 to 20 years in a big enough tank or pond with a filter, which is why the "
     "fish bowl is the problem: a bowl with no filter is usually a couple of years at best. Two "
     "goldfish want a tank of 100 litres or more."),
    (("rat", "rats"),
     "A rat lives 2 to 3 years, and they are social, so a pair lives longer and better than one "
     "alone. That short life is the hard part of keeping them."),
    (("ferret", "ferrets"),
     "A ferret lives 6 to 10 years, with the males usually a little longer than the females."),
    (("horse", "pony", "horses", "ponies"),
     "A horse lives 25 to 30 years, and ponies often reach 35. Teeth and feet decide the last "
     "third of that, so a yearly check of both is worth more than anything else."),
    (("tortoise", "tortoises"),
     "A tortoise outlives most of us: a horsfield's or a Hermann's lives 40 to 70 years and some "
     "reach far beyond that, so it is a pet to leave in a will rather than a short commitment."),
    # The birds people keep for eggs are asked about as pets ("how long do chickens live"), and
    # the word for the bird is also the word for the meat, so this row is what keeps the roast
    # card away from a question about a hen in the garden.
    (("chicken", "chickens", "hen", "hens"),
     "A back-garden hen lives about 5 to 10 years, though the egg-laying years are nearer 3 to 5, "
     "and hybrids bred for laying burn out sooner than the old breeds."),
    (("duck", "ducks"),
     "A duck lives 8 to 12 years, and the big meat breeds sit at the bottom of that while a small "
     "call duck can reach the top."),
    (("goose", "geese"),
     "A goose lives 15 to 20 years, and they pair for life, so a lone one is a bad idea rather "
     "than a short commitment."),
    (("turkey", "turkeys"),
     "A turkey lives 5 to 10 years as a pet: the broad-breasted breeds are bred to grow so fast "
     "that few reach old age, while the heritage breeds are the ones that last."),
)

# The birds that are kept and eaten: for these the animal word is also the joint, so the word
# alone cannot say which question it is. "how long does a turkey need" is a cook asking about
# the oven and "how long do turkeys live" is a keeper asking about the bird, and both carry
# `how long` and `turkey`. The kitchen words in the avoid list catch every cooking line that
# says how it is cooked; these rows are what catches the ones that do not, by waiting for the
# life to be said out loud before they answer.
_BIRD_ALSO_MEAT = ("chicken", "duck", "goose", "turkey")
_LIFE_SAID = re.compile(
    r"\b(?:live|lives|lived|living|lifespan|life\s*span|life\s*expectancy|"
    r"as a pet|pets?|coop|hen\s*house|back\s*garden|in the garden|flock|free\s*range)\b")


def _bird_lifespan(reply):
    """A bird's life for a line that says life; None (pass) for the same bird on a plate."""
    def say(memory, understood):
        said = (understood or {}).get("clean") or ""
        return reply if _LIFE_SAID.search(said.lower()) else None
    return say


# The shape of the question: "how long do dogs live", "dog lifespan", "how many years does a
# cat live", "how long does a rabbit live for", "what is a ferret's life expectancy".
# The question arms only: a bare `live`/`lives`/`last` is not an ask, so a statement about where
# an animal lives - "my dog lives outside", "my cat lives indoors", "my goldfish lives in a bowl"
# - is not a question about how long it lives. "how long do dogs live" carries `how long` anyway.
_LIFESPAN_ASK = ("how long", "how many years", "lifespan", "life span", "life expectancy")

# Every other question with an animal and a length of time in it is a different question, and
# most of them are somebody else's answer already.
_LIFESPAN_AVOID = ("walk", "walks", "exercise", "leave him", "leave her", "leave alone",
                   # the kitchen words: "i dont like fish" then "how long do i roast a chicken"
                   # reached the goldfish answer, because the fish was still the topic and
                   # "how long" was the ask. A roast is not a lifespan.
                   "roast", "roasting", "roasted", "cook", "cooking", "oven", "bake",
                   "baked", "baking", "boil", "boiled", "fry", "fried", "grill", "grilled",
                   "barbecue", "bbq", "potato", "potatoes", "rice", "pasta", "minutes",
                   "gas mark", "degrees", "temperature", "celsius", "reheat", "leftovers",
                   # The meat words are not here on purpose: "chicken", "turkey" and "lamb" also
                   # name the animal, and "how long do chickens live as pets" is a lifespan
                   # question. Every cooking line about a joint carries a cooking word anyway
                   # ("roast", "oven", "cook", "how long in"), which is what holds it out.
                   # Keeping is the other question that reads like a lifespan: "how long does
                   # fish last in the fridge" is not a goldfish's life.
                   "fridge", "freezer", "use by", "best before", "once opened", "last in the",
                   "keeps for", "keeps in the", "keeps in a",
                   # "how long can you leave a cat alone" is the leaving question, and "how
                   # long" is what a lifespan is asked with: the bare "alone", "leave" and
                   # "weekend" hand it to the cat-alone and dog-alone answers below.
                   "left alone", "can i leave", "home alone", "without water", "without food",
                   "leave", "leaves", "leaving", "alone", "on its own", "on her own",
                   "on his own", "by itself", "weekend", "weekends", "while im out",
                   "while i'm out",
                   "go without", "hold it", "hold his", "hold her", "pregnant", "pregnancy",
                   "gestation", "in heat", "on heat", "season", "settle", "settles", "settling",
                   "sleep", "sleeps", "night", "bark", "barking", "howl", "grieve", "grieving",
                   "died", "dying", "dead", "put down", "put to sleep", "cancer", "disease",
                   "diagnosed", "ill", "sick", "medicine", "tablet", "worm", "worms", "flea",
                   "fleas", "food", "feed", "eat", "eats", "ate", "memory", "remember",
                   "training", "train", "recall", "grow", "growing", "weigh", "weight",
                   "coat", "groom", "nails", "claws", "bath", "hair", "shed", "moult",
                   "alone at home", "boarding", "kennel", "cattery", "moulting", "fly", "travel",
                   "heat", "chew", "chewing", "biting", "litter", "toilet", "vaccination",
                   # the days after an operation are their own question, and "how long does a
                   # cat take to recover from neutering" was getting the life expectancy
                   "neuter", "neutered", "neutering", "spay", "spayed", "spaying", "castrate",
                   "operation", "anaesthetic", "recover", "recovery", "recovering", "stitches",
                   "cone", "cones", "after the op",
                   # An animal that is also food: "how long does fish keep in the fridge" and
                   # "how long does rabbit last in the fridge" were the goldfish and rabbit
                   # lifespan answers, because the fish entry reads `fish` and `how long` and
                   # never asks what the line is about. The storage words are the question.
                   "fridge", "freezer", "frozen", "freeze", "defrost", "thaw", "thawed",
                   "cook", "cooks", "cooked", "cooking", "raw", "leftovers", "left over",
                   "storage", "store", "stored", "storing", "sell by", "use by", "best before",
                   "safe to eat", "eat it", "still good", "gone off", "keeps in the",
                   "keep in the", "last in the", "smell", "smells", "shelf life")

_LIFESPAN_UNKNOWN = (
    "Roughly: a dog 10 to 13 years, a cat 12 to 15, a rabbit 8 to 12, a guinea pig 5 to 7, "
    "a hamster 2 to 3, a budgie 8 to 12, and a goldfish 10 or more in a proper tank. "
    "Which animal is it?")


def _not_a_weight_of_food(understood):
    """False for a line that gives a weight: "how long does a 5kg chicken take".

    A chicken is a bird and a dinner, and the lifespan row read its weight as a life: the
    answer to a five kilo chicken was how long a hen lives. The storage words in
    _LIFESPAN_AVOID do not cover this, because the line says nothing about keeping it - the
    weight alone is what says the line is in the kitchen.
    """
    return not a_weight(understood)


def _lifespan_entries():
    """One entry per animal, so a second animal in the same conversation is a new subject.

    A single entry for the whole table was answered, but the composer reads a follow-up as a
    part of the last answer and narrows it: "how long do dogs live", then "how long does a cat
    live" came back as "10 to 13 years." - the dog's figure, about a cat. An entry of its own
    for each animal is what makes the line with a different animal in it answer itself.
    """
    out = [entry("pet-lifespan-" + names[0].replace(" ", "-"), (_LIFESPAN_ASK, names),
                 _bird_lifespan(reply) if names[0] in _BIRD_ALSO_MEAT else reply,
                 avoid=_LIFESPAN_AVOID, bias=1, guard=_not_a_weight_of_food)
           for names, reply in _PET_LIFESPAN]
    # A line that names no animal at all gets the list and the question back.
    out.append(entry("pet-lifespan", (_LIFESPAN_ASK, ("pet", "pets", "animal", "animals")),
                     _LIFESPAN_UNKNOWN, avoid=_LIFESPAN_AVOID, bias=1))
    return out
# "what's my dog called" asks for the name the store keeps, not for recall training. The key's
# "called" is there for "comes when called", which is the training question, so the ask for a
# name is what tells the two apart.
_NAME_ASK = re.compile(
    r"\b(?:what|whats|what's|which)\b.{0,30}\b(?:name|called|named)\b"
    # "what should i call my new puppy" is the naming question, not the recall one: the verb on
    # its own is in "what should i do when i call him", which is the training question.
    r"|\bwhat\s+(?:should|shall|do|would|will)\s+(?:i|we)\s+(?:call|name)\b"
    # "our dog is called Biscuit", "my dog called rex is 3" and "a dog called rex at the park"
    # are someone telling the bot a name, not asking for recall.
    r"|\b(?:is|are|was|were)\s+(?:called|named)\b")
# "called" followed by a name is the naming statement; followed by one of these it is the verb.
_CALLED_NAME = re.compile(r"\b(?:called|named)\s+([a-z]+)"
                            # "we call our cat tom" names the cat with the verb in front of
                            # the animal instead of behind it, and had no way into the naming
                            # test: it reached the bare "calling" key of the season row.
                            r"|\b(?:we|i|they|she|he)\s+call\s+(?:our|my|the|their|his|her)\s+[a-z]+\s+([a-z]+)")
# The words that say the cat is in season, which beat a name in the same line.
_A_SEASON_WORD = re.compile(
    r"\b(?:in\s+season|in\s+heat|on\s+heat|into\s+heat|into\s+season|yowling|caterwauling|"
    r"pregnant|pregnancy|gestation|calling|calls|call(?:ing)?\s+all\s+night)\b")
_CALLED_NOT_A_NAME = frozenset((
    "when", "by", "him", "her", "them", "me", "us", "it", "out", "for", "to", "at", "and",
    "but", "so", "if", "because", "yet", "he", "she", "they", "the", "a", "an", "in", "on",
    "up", "back", "over", "off", "again", "twice", "every", "each", "nothing", "something",
    "anything", "everything", "what", "which", "who", "how", "why"))
_DOG_RECALL_REPLY = ("Practise coming back somewhere boring, on a long line, saying his name once "
                     "and rewarding with something better than the treats he gets otherwise: "
                     "cheese or sausage. Never call him to something he dislikes, like a bath or "
                     "the end of a walk, or the word stops working.")


# "my cat is called Lily" is someone telling the bot a name, and "my cat keeps calling" is a cat
# in season asking for a mate. The two are the same word to the matcher - "called" is a form of
# "calling" - so the naming family reached the nine-weeks answer: "my cat is called Lily",
# "i have a cat called mia" and every other way of introducing a cat got the gestation of a
# pregnant queen. The name is what tells them apart, the same test the recall row already uses,
# with the words that follow "called" when it is not a name added to that set.
_CALLED_NOT_A_NAME_AT_HOME = _CALLED_NOT_A_NAME | frozenset((
    "about", "saying", "yesterday", "today", "this", "last", "just", "shortly", "earlier",
    "round", "in", "since", "later", "twice", "once"))


def _not_a_named_cat(understood):
    """False when the line is naming a cat, so the season-and-pregnancy row stands down."""
    text = str((understood or {}).get("clean") or "").lower()
    # A line can name the cat and still ask the season question: "my cat is called tom is he in
    # season" is a cat in season with a name in front of it, and standing the row down for the
    # name sent it to the naming answer ("A cat called Tom. What's it like to live with?").
    if _A_SEASON_WORD.search(text):
        return True
    for found in _CALLED_NAME.finditer(text):
        if found.group(1) not in _CALLED_NOT_A_NAME_AT_HOME:
            return False
    return True


# A litter has a cat in the line. The key holds "mum" and "mom" for "mum cat", and those are
# the ordinary words for a person: "how do i look after my mum who has dementia" was answered
# "Leave them with her and keep the room warm and quiet", because "look after" plus "mum" is
# the whole key and nothing in it named an animal. The cat, the kittens or the litter itself is
# what makes the line this row's.
_A_CAT_IN_THE_LINE = re.compile(
    r"\b(?:cat|cats|kitten|kittens|queen|litter|feline|puss|pusscat|tomcat|moggie)\b")


def _a_cat_in_the_line(understood):
    """Whether the line names a cat, kittens or a litter: what the newborn row is about."""
    text = str((understood or {}).get("clean") or "").lower()
    return _A_CAT_IN_THE_LINE.search(text) is not None


# "how do i look after a kitten" and "how do i care for a kitten" are the ordinary care question
# about one cat, and this row answered them with the first week in the nest, because "look after"
# and "care for" are two of its keys. Those two phrases are only this row's when there is a litter
# in the line - a newborn word, a birth, an orphan or a mother that will not feed them - so the
# reading decides, not the phrase: a general care question is the kitten-care row's, and a litter
# is still this one's.
_A_NEWBORN_WORD = re.compile(
    r"\b(?:newborns?|had kittens|had a litter|had her kittens|gave birth|giving birth|"
    r"just had|litter of|orphans?|orphaned|hand rear\w*|bottle feed\w*|rejected|wont feed\w*|"
    r"won't feed\w*|will not feed|eight weeks|leave their mother|abandoned)\b")
_A_CARE_PHRASE = re.compile(r"\b(?:look after|looking after|care for|caring for)\b")


def _a_litter_is_what_is_asked_about(understood):
    """False for a care question about one cat, which the kitten-care row answers."""
    text = str((understood or {}).get("clean") or "").lower().replace("\u2019", "'")
    if _A_NEWBORN_WORD.search(text):
        return True
    return not _A_CARE_PHRASE.search(text)


# The condolence says a pet has died, so the line in front of it has to be the one that says so.
# A follow-up borrows the earlier line's words, and "put" is a form of the key word "putting":
# after "put the kettle on", the harmless "she likes gin and cats" reached this entry on "cat"
# alone and was told the vet can arrange a cremation. The words below are the loss itself, in the
# shapes people type it, so the entry still answers every real one and stands down on the rest.
_LOSS_SAID = re.compile(
    r"\b(?:died|dies|dying|dead|death|deceased|passed away|passed on|euthani[sz]\w*|pts"
    r"|pts'd|put down|putting down|puts down|lost my|lost our|losing my|losing our"
    r"|gone now|no longer (?:with us|here)|buried|cremat\w*)\b")
# "put" and the goodbye can have the pet in between: "put our cat to sleep", "putting the dog
# down tomorrow". Four words between them covers a pet's name as well as the species.
_PUT_TO_SLEEP = re.compile(r"\bput(?:ting|s)?\b(?:\W+\w+){0,4}\W+(?:down|to sleep)\b")

LOSS_REPLY = ("I'm sorry, that's one of the hardest days. Nothing has to be decided today: the vet "
              "can arrange cremation or a home burial, and you can ask for a paw print or a lock "
              "of fur to keep. Be gentle with yourself for a while; it does get easier.")


# A dead *thing* is not a dead pet. "my dog ate a dead mouse" and "my dog ate something dead and
# is sick" were both told the vet could arrange a cremation: "dead" is the word the condolence is
# keyed on, and the animal that died is the mouse. Naming what was found, or saying the pet ate it
# or is ill, is a health question and keeps the answer about the pet.
_DEAD_NOT_THE_PET = re.compile(
    r"\bdead (?:mouse|mice|bird|birds|rat|rats|rabbit|rabbits|frog|frogs|fox|foxes|squirrel"
    r"|squirrels|pigeon|pigeons|fish|animal|animals|thing|things|hedgehog|vole|mole|insect"
    r"|insects|bug|bugs|sheep|lamb|chicken|chickens)\b"
    r"|\b(?:something|anything|stuff) dead\b")
_PET_ATE_OR_ILL = re.compile(
    r"\b(?:ate|eaten|eating|eats|swallowed|sick|vomit\w*|threw up|throwing up|diarrhoea"
    r"|diarrhea|poison\w*|unwell|ill|poorly)\b")
# ...unless the line says the pet itself is dying, which outranks both.
_THE_PET_IS_DYING = re.compile(
    r"\b(?:died|dies|dying|death|put down|putting down|euthani[sz]\w*|passed away|passed on)\b")


# The answer when the death said is the prey's, not the pet's: what to do about what has been
# brought in, which is the question behind "theyre dead though" after "how do i stop the cat
# bringing in mice". Silence is not an answer here - it left the line with "Ha! Glad you liked it."
PREY_DEATH_REPLY = (
    "That is the hunting instinct rather than anything wrong with the animal. Clear what it "
    "brings in away in gloves, bin or bury it where nothing else can get at it, and wash your "
    "hands after. Hunters pick up worms from what they catch, so keep the worming up to date, and "
    "a quick-release collar with a bell plus keeping it in from dusk until morning cuts how often "
    "it happens.")


def _pet_loss(memory, understood):
    """The condolence, or nothing when this line does not say a pet has died."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not said:
        return LOSS_REPLY
    if _DEAD_NOT_THE_PET.search(said):
        return ""
    if _PET_ATE_OR_ILL.search(said) and not _THE_PET_IS_DYING.search(said):
        return ""
    if _a_death_the_line_does_not_name(said, memory):
        return PREY_DEATH_REPLY
    if _LOSS_SAID.search(said) or _PUT_TO_SLEEP.search(said):
        return LOSS_REPLY
    return ""


# The rearing animal is not the one that died. "my cat keeps bringing in mice" / "theyre dead
# though" was told the vet could arrange a cremation: the line in front of it was about the cat,
# the death is said with a bare pronoun, and the thing that died is the mouse the cat brought in -
# which the bot had just named ("take the bird away in gloves"). A pronoun death is therefore
# read against the line above: when that line is about what the animal brings in or kills, the
# line that follows is about the prey, so the condolence stands down. A death the person's own
# animal is named in ("my cat", "our dog", a name given with "called") is never stood down.
_PREY_NAMED = re.compile(
    r"\b(?:mice|mouse|rats?|birds?|voles?|moles?|squirrels?|rabbits?|frogs?|foxes|fox|pigeons?"
    r"|hedgehogs?|insects?|bugs?|spiders?|worms?|chicks?|lambs?|fish)\b")
_BRINGING_IT_IN = re.compile(
    r"\bbring(?:s|ing)?\b(?:\W+\w+){0,3}\W+(?:in|home|back)\b"
    r"|\b(?:keeps? bringing|caught|catches|catch|killed|kills|killing|ate|eats|eating"
    r"|hunting|hunts?|prey|dragged in)\b")
_A_BARE_DEATH = re.compile(
    r"\b(?:theyre|they are|theyre all|its|it is|hes|shes|he is|she is|these are|those are)"
    r"(?:\s+(?:both|all|still|now|probably|definitely|always|usually|normally|mostly))?\s+"
    r"(?:dead|died|dying|gone|passed away|passed on)\b")
_THE_ANIMAL_IS_NAMED = re.compile(
    r"\b(?:my|our)\s+(?:\w+\s+){0,2}(?:cat|cats|dog|dogs|kitten|kittens|puppy|puppies|pet"
    r"|pets|rabbit|hamster|guinea|parrot|budgie|horse|pony|rat|ferret|tortoise|snake)\b")
# A death that happens over and over is not a pet's death: a pet dies once, and what comes in
# every morning is dead every morning. "its always dead" after "the cat brings a bird in most
# mornings" reaches this handler as "my cat is always dead" - the reader writes the thing in hand
# where the pronoun points, which is right for "its on 4%" and wrong for a death - so the animal
# being named in the line is not enough to keep the condolence: the word for how often it happens
# is what says the death is the prey's. "my cat died", "my cat is dead" and "he passed away" have
# no such word and keep it.
_A_REPEATED_DEATH = re.compile(
    r"\b(?:always|usually|normally|mostly|constantly|regularly|often|again|every time|each time"
    r"|all the time|by morning|every morning|each morning)\b")
# An animal of the person's own, by the word for it: "my cat", "our dog", "my old rabbit".
_AN_ANIMAL_OF_THEIRS = re.compile(
    r"\b(?:my|our)\s+(?:\w+\s+){0,2}(cat|cats|dog|dogs|kitten|kittens|puppy|puppies|pet"
    r"|pets|rabbit|rabbits|hamster|hamsters|guinea|parrot|budgie|horse|pony|rat|rats|ferret"
    r"|tortoise|snake)\b")


def _the_line_above(memory):
    """The person's own last line and the bot's answer to it, as one piece of text."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed(turns or []):
        if not isinstance(turn, dict):
            continue
        return "%s %s" % (turn.get("user") or "", turn.get("bot") or "")
    return ""


def _a_death_the_line_does_not_name(said, memory):
    """True when the death is the prey's: a bare pronoun, a named prey, or one said again."""
    above = _the_line_above(memory).lower()
    if not above:
        return False
    if not (_PREY_NAMED.search(above) and _BRINGING_IT_IN.search(above)):
        return False
    if _PREY_NAMED.search(said) and not _AN_ANIMAL_OF_THEIRS.search(said):
        # the line names what died and it is the prey: "the bird was dead", "the mice are dead"
        return True
    if _A_REPEATED_DEATH.search(said):
        # a death that keeps happening is the prey's, even when the reader has written the
        # animal in where the pronoun pointed ("its always dead" read as "my cat is always dead")
        return True
    if not _A_BARE_DEATH.search(said):
        return False
    if _THE_ANIMAL_IS_NAMED.search(said):
        return False
    return True


def _dog_recall(memory, understood):
    """The recall routine, or nothing when the line is asking what the dog is called."""
    said = str((understood or {}).get("clean") or "")
    if _NAME_ASK.search(said):
        return ""
    named = _CALLED_NAME.search(said)
    if named and named.group(1) not in _CALLED_NOT_A_NAME:
        return ""
    return _DOG_RECALL_REPLY


def _a_name_is_being_given(understood):
    """True when the line is telling the bot what the animal is called.

    "calling" is the word for a cat in season, and a key phrase is matched word by word through
    the loose forms, so "is called tom" reached "calling" on the stem "call": "i have a cat called
    tom", "my cat is called milly" and even "what should i call my cat" were answered with the
    nine weeks of pregnancy. A name after called or named is a naming statement and not a season,
    which is the same reading the dog-recall answer already uses.
    """
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    # The season question has the last word, because a line can carry a name and still ask it:
    # "my cat is called tom is he in season" is a cat in season with a name in front of it, and
    # standing the row down for the name sent it to the naming answer.
    if _A_SEASON_WORD.search(said):
        return False
    if _NAME_ASK.search(said):
        return True
    named = _CALLED_NAME.search(said)
    return bool(named and named.group(1) not in _CALLED_NOT_A_NAME)


# A cat in a house with children is a question, and the answer is the same for every way of
# asking it. The one exception is a person describing their own household - "i have 2 kids and a
# cat" - which is a note back and not a request for a safety talk unless it carries a worry.
CAT_AND_CHILDREN = (
    "A cat and a child get on fine with three rules: never leave a baby or a toddler alone in a "
    "room with the cat, give the cat somewhere up high and a room it can leave by, and show the "
    "child one finger down the back and to leave the cat alone while it is eating or in its "
    "basket. The old story that a cat smothers a baby is not true - a cat goes to warmth, so keep "
    "it out of the cot, and shut the bedroom and the pram against it while the baby sleeps. A swat "
    "is nearly always fear rather than nastiness: a cat that swats a child it used to accept should "
    "see the vet, because pain is often behind a change. Wash any scratch with soap and water, and "
    "a deep bite on a hand wants looking at.")

_CHILD_WORRY = ("ok", "okay", "safe", "worry", "worried", "risk", "smother", "having a baby",
                "new baby", "expecting", "newborn", "what do i need")


def _cat_and_children(memory, understood):
    """The safety answer - but a plain description of a household gets a note back instead."""
    said = " ".join(str((understood or {}).get(key) or "") for key in ("clean", "text"))
    said = " " + re.sub(r"[^a-z0-9' ]+", " ", said.lower()) + " "
    if (understood or {}).get("kind") == "statement" and not any(
            " %s " % word in said for word in _CHILD_WORRY):
        return None
    return CAT_AND_CHILDREN


# What a pet costs is the first year as much as the animal, and the animal's price depends on
# where it comes from: a rescue is the cheap route and the pedigree the dear one. "how much does a
# puppy cost" was answered with the five-minutes-a-month walking rule ("how much" is the exercise
# entry's own key), and "how much does a kitten cost" with the kitten-feeding guide.
PET_COST_RESCUE = re.compile(
    r"\b(?:rescue|rescued|rehome|rehomed|rehoming|adopt|adopted|adopting|adoption|shelter|"
    r"rspca|battersea|dogs trust|blue cross)\b")
PET_COST_BREEDER = re.compile(
    r"\b(?:breeder|breeders|pedigree|kennel club|registered|from a breeder|with papers)\b")
PET_COST_KITTEN = re.compile(r"\b(?:kitten|kittens|cat|cats)\b")

PET_COST_RESCUE_LINE = (
    "From a rescue it is about 150 to 350 pounds for a puppy or a dog, which usually covers the "
    "neutering, the microchip and the first jabs. The first year still costs more than that: "
    "insurance 20 to 40 a month, food, worming, a crate and a bed. Budget around 1,000 in the "
    "first year and keep a vet fund separately.")
PET_COST_BREEDER_LINE = (
    "A pedigree puppy is about 800 to 3,000 pounds depending on the breed, and the first year "
    "costs more than the puppy does: jabs and a microchip 60 to 100, neutering 150 to 300, "
    "insurance 20 to 40 a month, plus food, worming, a crate and a bed. Budget around 1,500 in "
    "the first year and keep a vet fund separately. Walk away from anyone who will not show you "
    "the mother.")
PET_COST_KITTEN_LINE = (
    "A kitten is about 50 to 150 pounds from a rescue or a friend's litter, and 300 to 800 for a "
    "pedigree; the first year costs more than the kitten does: jabs and a microchip 60 to 100, "
    "neutering 60 to 120 for a male and more for a female, insurance 8 to 20 a month, plus "
    "litter, food and a carrier. Budget around 800 in the first year and keep a vet fund "
    "separately.")
PET_COST_PUPPY_LINE = (
    "A puppy is about 800 to 3,000 pounds from a breeder depending on the breed, and 150 to 350 "
    "from a rescue, and the first year costs more than the puppy does: jabs and a microchip 60 to "
    "100, neutering 150 to 300, insurance 20 to 40 a month, plus food, worming, a crate and a "
    "bed. Budget around 1,500 in the first year and keep a vet fund separately. Walk away from "
    "anyone who will not show you the mother.")


PET_COST_DOG = re.compile(r"\b(?:dog|dogs|puppy|puppies|pup)\b")
PET_COST_ONE_OR_OTHER = re.compile(
    r"\b(?:cheaper|cheapest|dearer|more expensive|less expensive|cost more|costs more|"
    r"compare|compared|versus|vs)\b")
PET_COST_COMPARE_LINE = (
    "A cat is the cheaper of the two to keep: about 800 to 1,200 pounds a year against 1,000 to "
    "1,700 for a dog, because insurance is 8 to 20 a month instead of 20 to 40 and a cat eats "
    "far less than a medium dog. The buying price is the other way round - a pedigree puppy is "
    "usually dearer than a pedigree kitten - but over ten years the dog costs the most.")

# The first year with a small pet is the set-up, not the animal: a rabbit needs a hutch and a
# run, a hamster a tank big enough to dig in, and a horse is livery every month for ever. These
# are the prices people cannot find, and "how much does a hamster cost" was a shrug on main.
SMALL_PET_RABBIT = re.compile(r"\b(?:rabbit|rabbits|bunny|bunnies)\b")
SMALL_PET_HAMSTER = re.compile(r"\b(?:hamster|hamsters|gerbil|gerbils)\b")
SMALL_PET_GUINEA = re.compile(r"\b(?:guinea pig|guinea pigs|guineapig|guineapigs)\b")
SMALL_PET_BUDGIE = re.compile(r"\b(?:budgie|budgies|budgerigar|parakeet|cockatiel|canary)\b")
SMALL_PET_HORSE = re.compile(r"\b(?:horse|horses|pony|ponies)\b")
SMALL_PET_FISH = re.compile(r"\b(?:fish tank|fish tanks|aquarium|aquariums|tropical fish)\b")

SMALL_PET_RABBIT_LINE = (
    "A rabbit is 150 to 300 pounds a year to keep, and the set-up is the real money: a hutch with "
    "a run attached, or a shed, is 200 to 400, then hay all day at 20 to 40 a month, pellets, a "
    "few greens, neutering 60 to 120 and the annual jabs. Keep two, because a rabbit alone is a "
    "stressed rabbit, and they live eight to ten years.")
SMALL_PET_HAMSTER_LINE = (
    "A hamster is 10 to 20 pounds to buy and 5 to 10 a month to keep: bedding, food and a little "
    "veg. The cage is the cost - 60 to 120 pounds for a tank at least 100 by 50cm with a deep "
    "base to dig in, not the small barred cage in the shop. Save for the vet too: not every "
    "practice treats small furries, and a consultation is 30 to 60 pounds.")
SMALL_PET_GUINEA_LINE = (
    "A guinea pig is 10 to 25 pounds each and 200 to 400 a year to keep: a cage at least 120 by "
    "60cm, hay all day, pellets with added vitamin C, and greens every day. They need a friend of "
    "their own kind, so two is the real minimum, and they live five to seven years.")
SMALL_PET_BUDGIE_LINE = (
    "A budgie is 15 to 40 pounds and about 150 to 250 a year: a wide cage rather than a tall one, "
    "at least 60cm across so it can fly between perches, a friend, and pellets with daily veg. "
    "The catch is the vet - an avian vet charges more than a small-animal practice, and a budgie "
    "should see one at the first sign of fluffing up.")
SMALL_PET_HORSE_LINE = (
    "A horse costs 4,000 to 8,000 pounds a year all in: livery at 150 to 400 a month, hay and "
    "feed, shoes every six weeks at 80 to 120, insurance, worming, teeth and the vet. The horse "
    "itself is the cheap part. Never buy one without a vetting and a trial, and budget the first "
    "year higher still for tack and rugs.")
SMALL_PET_FISH_LINE = (
    "Setting up a tank is 150 to 300 pounds - tank, filter, heater, gravel, a test kit and water "
    "treatment - and then 10 to 20 a month for food and electricity. Cycle the tank for four to "
    "six weeks before any fish go in, and start with a few hardy ones: most first tanks fail "
    "because the fish go in on day one.")


def _small_pet_cost(memory, understood):
    """The price of the small animal the line named, since each one costs a different amount."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    for pattern, line in ((SMALL_PET_RABBIT, SMALL_PET_RABBIT_LINE),
                          (SMALL_PET_HAMSTER, SMALL_PET_HAMSTER_LINE),
                          (SMALL_PET_GUINEA, SMALL_PET_GUINEA_LINE),
                          (SMALL_PET_BUDGIE, SMALL_PET_BUDGIE_LINE),
                          (SMALL_PET_HORSE, SMALL_PET_HORSE_LINE),
                          (SMALL_PET_FISH, SMALL_PET_FISH_LINE)):
        if pattern.search(said):
            return line
    return None


def _pet_cost(memory, understood):
    """What a dog or a cat costs, priced for the route the person named."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not PET_COST_KITTEN.search(said) and not PET_COST_DOG.search(said):
        # The line points back and names no animal: "how much do they cost a month" after two
        # cats was answered with the price of a puppy. What the chat is on is the animal.
        from ..memory import named  # lazy: the facts do not import the store
        said = said + " " + str(named.subject_word(memory) or "").lower()
    # "is a cat cheaper than a dog" asks for both, and a number for one is no answer to it
    if PET_COST_ONE_OR_OTHER.search(said) and PET_COST_KITTEN.search(said) \
            and PET_COST_DOG.search(said):
        return PET_COST_COMPARE_LINE
    if PET_COST_KITTEN.search(said):
        return PET_COST_KITTEN_LINE
    if PET_COST_RESCUE.search(said):
        return PET_COST_RESCUE_LINE
    if PET_COST_BREEDER.search(said):
        return PET_COST_BREEDER_LINE
    return PET_COST_PUPPY_LINE


# "how do i brush my cat" is a routine question and "my cat has matted fur" is a rescue, and the
# two share the words brush, coat and fur: one entry reads the line so each gets its own answer.
_COAT_MAT = re.compile(r"\b(matt?s?|matted|matting|knotted|knots?|tangled?|dreadlocks?|clumps?)\b")


_COAT_GREASY = re.compile(r"\b(greasy|grease|oily|oily coat|stud tail)\b")


def _cat_coat(memory, understood):
    text = ((understood or {}).get("norm_text") or (understood or {}).get("clean") or "").lower()
    if _COAT_GREASY.search(text) and not _COAT_MAT.search(text):
        return ("A greasy or scurfy coat is rarely a brushing problem: a cat who has stopped washing "
                "herself, or an unneutered tom with a greasy patch at the base of the tail, means "
                "have her seen. Otherwise it is diet or over-grooming - a cheaper food, or fleas "
                "making her lick - so check for flea dirt with a damp tissue and move her onto a "
                "food with meat as the first ingredient.")
    if _COAT_MAT.search(text):
        return ("Work a mat out from the tip inwards with a metal comb or a slicker brush, a "
                "little at a time with your fingers holding the skin so you are not pulling it. "
                "Never cut one with scissors: cat skin tents up into them. A big or sore mat, or "
                "a cat that will not be handled, comes off in minutes with a groomer's clippers, "
                "and an old cat that stops grooming needs a vet look too.")
    return ("About 5 minutes: once a day for a long-haired cat, twice a week for a short-haired "
            "one. The two brushes worth having are a metal-toothed comb for long coats and a "
            "rubber curry brush for short ones. Brush along the way the fur lies, in sections on "
            "the back legs and under the belly where the tangles start, and keep it short and calm. "
            "A cat that hates it does better with a few minutes after a meal than one long "
            "session.")


# A pet losing weight is the opposite question from a pet that is too heavy, and the two share
# every word, so each weight entry reads the line: a pet whose weight is going the wrong way gets
# the vet answer, a pet that is too heavy gets the food answer. "how do i help my cat lose weight"
# is the second, not the first.
_GOING_THIN = ("losing weight", "lost weight", "gone thin", "getting thin", "too thin",
               "very thin", "underweight", "skinny", "bony", "bones", "ribs", "ribs showing",
               "gone off her food", "gone off his food", "not eating", "stopped eating",
               "off her food", "off his food", "wont eat", "won't eat")
_THIN_WORDS = ("thin", "skinny", "bony", "underweight", "ribs")
_WEIGHT_UP = ("overweight", "over weight", "fat", "obese", "heavy", "too heavy",
              "putting on weight", "put on weight", "gained", "putting weight on",
              "lose weight", "slim", "slimming", "diet", "dieting")
# asking for help to make it happen, rather than reporting it: "how do i help her lose weight" is
# the food question, and "she is losing weight" is the vet one
_ASKING = ("help", "make", "get", "start", "should", "how do i", "how can i", "want to")


def _going_thin(text):
    said = [one for one in _GOING_THIN if re.search(r"\b" + re.escape(one), text)]
    bare = [one for one in _THIN_WORDS
            if re.search(r"\b" + re.escape(one) + r"\b", text)
            and not re.search(r"\b" + re.escape(one) + r" (coat|fur|hair|skin)", text)]
    if not said and not bare:
        return False
    up = [one for one in _WEIGHT_UP if re.search(r"\b" + re.escape(one), text)]
    asking = [one for one in _ASKING if one in text]
    return not (up and asking)


def _said(understood):
    return ((understood or {}).get("norm_text") or (understood or {}).get("clean") or "").lower()

# A dog and a cat have a weight card each; a fat rabbit, guinea pig or pony was answered with an
# echo ("A rabbit - is it good company?"). The animal in the line decides which answer it is,
# because the amounts and the danger are not the same: a fat pony is laminitis, a fat rabbit is
# pellets, and neither may be dieted the way a dog is.
_PONY_FAT = (
    "A fat pony is a laminitis risk, so treat it now rather than in spring: use a weigh tape once a "
    "week, strip-graze or use a grazing muzzle, soak hay for twelve hours and drop any hard feed. "
    "Ask your vet or farrier for a target weight, and have an older pony that gains on almost "
    "nothing tested for Cushing's.")
_RABBIT_FAT = (
    "A fat rabbit is nearly always too many pellets: about an eggcup a day, hay always in the rack, "
    "vegetables instead of treats, and a run it can move about in. Weigh weekly and cut back slowly, "
    "because starving a rabbit can bring on gut stasis. If it gained on the same food, ask a "
    "rabbit-savvy vet about its teeth.")
_RODENT_FAT = (
    "Take the pellets down rather than the hay: about an eighth of a cup a day for a guinea pig and "
    "an eggcup for a hamster, with unlimited hay, which is what wears their teeth, and vegetables "
    "for vitamin C. Give it more space to run in, weigh it weekly, and see the vet if the weight "
    "changed with no change in food.")


def _small_pet_fat(memory, understood):
    """The same question about an animal whose weight card is not the dog's."""
    text = _said(understood)
    if re.search(r"\b(horse|horses|pony|ponies|donkey|donkeys|shettie|shetties|equine)\b", text):
        return _PONY_FAT
    if re.search(r"\b(rabbit|rabbits|bunny|bunnies)\b", text):
        return _RABBIT_FAT
    return _RODENT_FAT


_CAT_THIN_REPLY = (
    "A cat that loses weight without being put on a diet needs the vet, not a food change: weigh "
    "her weekly on kitchen scales and note the figures to take with you. The usual causes are "
    "treatable - bad teeth first, then an overactive thyroid, kidney disease and worms - so a "
    "check with a blood test settles it. Do not wait to see if she picks up: a cat off her food "
    "for more than a day should be seen the same week.")


# "How much should a labrador weigh" asks for a number, and the file only had the diet side of
# weight: the line reached `pet-cost`, which answered with what a puppy costs, and "how heavy
# should a labrador be" got the shrug. Two things were missing, the words ("weigh", "how heavy",
# "kilos" are not "weight") and a reply with a figure in it. The breed the person named decides
# the range; a line that names no breed gets the bands and the way a vet judges it by hand.
# Adult ranges, in kilos, rounded to the figures the breed clubs publish. Kept short on purpose:
# these are the names people type, and anything not here falls through to the bands below.
DOG_KG = {
    "chihuahua": (1.5, 3), "yorkshire terrier": (2, 3.2), "pomeranian": (1.8, 3),
    "maltese": (2, 4), "shih tzu": (4.5, 8), "westie": (6, 10),
    "west highland terrier": (6, 10), "border terrier": (5, 7), "cavalier": (5.5, 8),
    "jack russell": (5, 8),
    "pug": (6, 8), "bichon": (5, 8), "dachshund": (7, 14), "cockapoo": (6, 12),
    "cavapoo": (6, 10), "french bulldog": (9, 13), "beagle": (9, 16),
    "staffie": (11, 17), "staffordshire bull terrier": (11, 17), "whippet": (8, 14),
    "cocker spaniel": (12, 15), "border collie": (14, 20), "husky": (16, 27),
    "springer spaniel": (16, 25), "bulldog": (18, 25), "poodle": (20, 32),
    "labradoodle": (20, 30), "lurcher": (20, 30), "terrier": (5, 10),
    "german shepherd": (22, 40), "alsatian": (22, 40), "boxer dog": (25, 32),
    "golden retriever": (25, 34), "labrador": (25, 36), "retriever": (25, 36),
    "greyhound": (26, 40), "rottweiler": (35, 50), "mastiff": (50, 80),
}
CAT_KG = {
    "maine coon": (5, 9), "ragdoll": (5, 8), "british shorthair": (4, 7),
    "siamese": (3.5, 5.5), "tabby": (3.5, 6), "moggy": (3.5, 5.5),
}
# The words that make a line a "what should it weigh" question rather than a diet one. "kg" and
# "kilos" are here because "how many kg should a border collie be" names no weight word at all.
_WEIGH_WORDS = ("weigh", "weighs", "weighing", "how heavy", "kg", "kilo", "kilos",
                "kilogram", "kilograms", "healthy weight", "ideal weight", "target weight",
                "body condition", "lbs")
# The direction words mean the person is asking what to do about it, which is the diet card.
_WEIGH_DIRECTION = ("overweight", "over weight", "too fat", "fat", "obese", "diet", "slim",
                    # "my dog weighs too much" is the diet question, not a request for the
                    # breed's range: the direction words send it to the slimming card
                    "weighs too much", "weigh too much", "too heavy", "too much",
                    "lose", "losing", "lost", "gained", "gaining", "putting on", "put on",
                    "too thin", "getting thin", "gone thin", "skinny", "bony", "ribs")


def _a_weigh_question(text):
    """What should it weigh, rather than what to do about its weight."""
    if not any(re.search(r"\b" + re.escape(one), text) for one in _WEIGH_WORDS):
        return False
    return not any(re.search(r"\b" + re.escape(one), text) for one in _WEIGH_DIRECTION)


def _the_range(text, table):
    """The longest breed name the line says a word for, so "jack russell" beats "terrier"."""
    for name in sorted(table, key=len, reverse=True):
        if re.search(r"\b" + re.escape(name) + r"\b", text):
            return name, table[name][0], table[name][1]
    return None


def _weigh_reply(text, table, bands, adult):
    if re.search(r"\b(kitten|kittens|puppy|pup|puppies)\b", text):
        return ("Weigh it weekly on the kitchen scales and write the figures down, because the "
                "number that matters for a young animal is that it is going up, not where it is "
                "on a chart: a puppy roughly doubles its birth weight in the first ten days and "
                "gains most before it is six months old, and a kitten gains about 100g a week. "
                "A grown one is %s. A vet can say whether yours is on its own curve at the next "
                "jab, and the line going flat or down is worth a call before then." % bands)
    named = _the_range(text, table)
    if named:
        name, low, high = named
        return ("An adult %s is usually %g to %gkg, males at the top of that range and females at "
                "the bottom, and a line bred for work or for show can sit outside it. Go by hand "
                "as well as by figure: you should feel the ribs easily under a thin cover and see "
                "a waist from above, which is what the vet scores. A young one is not that weight "
                "until it is full grown, at %s, so weigh it monthly and hold the food steady "
                "while it is still filling out." % (name, low, high, adult))
    return ("It depends on the breed and the bands are wide: %s. What you can check at home is the "
            "shape - ribs felt easily under a thin cover, a waist seen from above - and the vet "
            "scores the same thing by hand. Weigh it monthly on the same scales, so a slow change "
            "shows up before it is a problem." % bands)


def _cat_weight(memory, understood):
    text = _said(understood)
    if _a_weigh_question(text):
        return _weigh_reply(text, CAT_KG,
                            "3.5 to 5.5kg for most cats, and 5 to 9kg for a big breed like a "
                            "Maine Coon", "about a year")
    if _going_thin(text):
        return _CAT_THIN_REPLY
    return ("Cats get overweight on very little food, so weigh the dry food instead of filling "
            "the bowl and cut it by a tenth: a 4kg cat needs about 3 or 4 pouches of 85g, or 40 "
            "to 50g of dry, a day, and should lose about 1 per cent of body weight a week, never "
            "fast. Split the day into small meals, use a puzzle feeder and a wand toy for five "
            "minutes twice a day, and ask the vet for a target weight - a cat gaining on the same "
            "food needs a thyroid check.")


_DOG_THIN_REPLY = (
    "A dog that loses weight while eating normally needs the vet: worms are the commonest cause "
    "and the easiest to rule out, then bad teeth, diabetes and a gut that cannot absorb food "
    "properly. Weigh him every two weeks on the same scales and take the figures with you. Rapid "
    "loss, or loss with vomiting, a big thirst or a swollen belly, is the same week, not the "
    "same month.")


def _dog_weight(memory, understood):
    text = _said(understood)
    if _a_weigh_question(text):
        return _weigh_reply(text, DOG_KG,
                            "2 to 10kg for a small dog, 10 to 25kg for a medium one, 25 to 40kg "
                            "for a large one and 40kg and up for a giant",
                            "a year for a small dog and eighteen months for a large one")
    if _going_thin(text):
        return _DOG_THIN_REPLY
    return ("You should be able to feel the ribs without pressing and see a waist from above; if "
            "you can't, cut treats first, weigh the food instead of scooping it, and swap some of "
            "the kibble for green beans or carrot. Ask the vet for a target weight, since a dog "
            "that loses 10% of its body weight is often livelier and longer-lived for it.")


# "i want to lose weight but my cat keeps waking me up" is a question about the cat, and "how do
# i lose weight when my cat keeps waking me up" is the person's own goal with the cat as the
# reason it is hard: every weight row stands down for the waking words, or the weight words in
# the line take it.
_WAKING_AVOID = ("waking me", "wakes me", "woke me", "keeps waking", "waking up",
                 "i want to lose", "i want to get fit", "im trying to lose",
                 "my own weight")



# A puppy that mouths hands is teething; an adult dog that bites its owner is a behaviour
# problem; a dog attacking someone now is an ambulance. All three arrive as "my dog is biting
# me", and the safety module won on every one of them, so an owner asking how to stop it got
# "Call 999 or 911 now, and don't put yourself in the way".
BITE_NOW = ("attack", "attacks", "attacking", "attacked", "maul", "mauls", "mauling", "mauled",
            "going for", "went for", "turned on", "turning on", "right now", "at this moment",
            "as we speak", "dragging", "has hold of", "wont let go", "won't let go")
# Mouthing, play biting and a nip are the teething answer, unless the teeth are landing on a
# child: "my dog keeps nipping the baby" is not a puppy to be yelped at.
BITE_TEETH = ("puppy", "pup", "puppies", "teething", "teeth", "mouthing", "mouths",
              "play biting", "playbiting", "landshark", "nips", "nipping", "nippy")
BITE_SKIN = ("broke the skin", "broken the skin", "broke skin", "bleeding", "blood", "puncture",
             "stitches", "a&e", "hospital")
# Somebody other than the owner: a bite on a visitor is a report, and the owner wants to know that.
BITE_SOMEONE_ELSE = ("postman", "postwoman", "postie", "delivery", "courier", "neighbour",
                     "neighbors", "neighbour's", "visitor", "visitors", "guest", "guests",
                     "stranger", "strangers", "child", "children", "kid", "kids", "boy", "girl",
                     "baby", "toddler", "someone", "somebody", "passer", "vet", "groomer",
                     "customer", "window cleaner", "paperboy", "friend", "family", "husband",
                     "wife", "partner", "son", "daughter", "grandchild", "grandson",
                     "granddaughter")


# A bite that has already landed reads as a done deed, and a child is no different then: "my dog
# just bit a child" is the child seen today and the 101 call, while "my dog keeps biting the kids"
# is the habit the child-gate answer is for. The bare "bit a child" is left alone - it is the
# safety module's card on main, and this change does not move it.
BITE_DONE_DEED = ("just bit", "just bitten", "has bitten", "had bitten")
# The report after a bite, in the words the safety card and the old pets row both used.
BITE_REPORT = ("Get the person seen today and keep the dog away from people until you have a "
               "plan: ring 101 to report a bite that broke the skin, because in the UK a dog that "
               "injures someone is a criminal matter and the owner can be liable. A vet visit is "
               "worth it too - pain, a bad ear or failing eyesight is often behind a first bite.")
BITE_REPORT_CHILD = ("Get the child seen today, and keep the dog away from children until you "
                     "have a plan: ring 101 to report it, because in the UK a dog that injures "
                     "someone is a criminal matter and the owner can be liable. After that it is a "
                     "vet visit and a qualified behaviourist, because a first bite on a child is "
                     "never nothing.")

# Who a habit-bite lands on changes what to do today: a child in the house is the one case where
# the management has to be said out loud.
BITE_CHILD_WORDS = ("baby", "babies", "child", "children", "kid", "kids", "toddler", "son",
                    "daughter", "grandchild", "grandchildren", "grandson", "granddaughter",
                    "school run")
BITE_DOOR_WORDS = ("postman", "postwoman", "postie", "delivery", "courier", "paperboy",
                   "window cleaner", "doorbell", "door")
BITE_OTHERS_HABIT = BITE_SOMEONE_ELSE + BITE_CHILD_WORDS + BITE_DOOR_WORDS + ("people", "folk")


def _dog_chewing(memory, understood):
    """Why a dog chews, which is a puppy question only while the dog is a puppy."""
    words = [str(word).lower() for word in (understood.get("words") or ())]
    said = " " + " ".join(words) + " "

    def has(*wanted):
        return any(" %s " % want in said for want in wanted)

    # Nothing in "my dog chewed the arm of the sofa" says how old the dog is, and the teething
    # answer was going to every one of them: a six-year-old collie that strips a sofa was told
    # about a frozen carrot and that puppies grow out of it. Teeth only explain a puppy, so the
    # line has to say so - a puppy, a pup, teething, or a few months old - and every other dog
    # gets the adult causes, which start with the day it is having.
    # A stated age is a number, and it decides on its own: "20 month old" is in the phrase list
    # above as "month old", but twenty months is nearly two and the dog is not teething, so the
    # number is read first and the phrases only answer a line that states no number at all.
    years = _dog_age_years(understood)
    if years is not None:
        if years < 1.0:
            return ("Chewing is normal while teeth change, so redirect it: plenty of chew toys, "
                    "a frozen carrot or stuffed Kong, and pick everything else up out of reach. "
                    "Puppies usually grow out of it by seven or eight months.")
        return ("An adult dog chews for a reason and teeth are not it: boredom, a walk that is "
                "too short, or being left alone longer than it can take. Give it a proper sniffy "
                "walk before you go out, leave a stuffed Kong or a long-lasting chew, and block "
                "off the sofa for a fortnight while the habit breaks. If it has just started in a "
                "dog that never did it, get its teeth and gums checked, because a sore mouth "
                "makes a dog chew to soothe it.")
    if has("puppy", "puppies", "pup", "pups", "teething", "teeth", "months old", "month old",
           "weeks old", "week old", "just got him", "just got her", "just got it",
           "new puppy", "young dog"):
        return ("Chewing is normal while teeth change, so redirect it: plenty of chew toys, a "
                "frozen carrot or stuffed Kong, and pick everything else up out of reach. Puppies "
                "usually grow out of it by seven or eight months.")
    return ("An adult dog chews for a reason and teeth are not it: boredom, a walk that is too "
            "short, or being left alone longer than it can take. Give it a proper sniffy walk "
            "before you go out, leave a stuffed Kong or a long-lasting chew, and block off the "
            "sofa for a fortnight while the habit breaks. If it has just started in a dog that "
            "never did it, get its teeth and gums checked, because a sore mouth makes a dog chew "
            "to soothe it.")


def _dog_bite_person(memory, understood):
    """How to stop a dog biting people, at the weight the line carries."""
    words = [str(word).lower() for word in (understood.get("words") or ())]
    said = " " + " ".join(words) + " "

    def has(*wanted):
        return any(" %s " % want in said for want in wanted)

    # The dog's own body is not a person: "my dog is biting his paw" is an itch or a sore, and the
    # licking and skin entries answer it, so this row stands down instead of training it out.
    if has("his", "her", "its", "their") and has(
            *("paw", "paws", "tail", "leg", "legs", "foot", "feet", "ear", "ears", "fur", "skin")):
        return None
    # Nor is the dog itself: "my dog is scratching and biting himself" is a skin question, so the
    # itch entry takes it rather than a training plan for a dog that has not bitten anyone.
    if has("himself", "herself", "itself") and has(
            *("scratching", "scratches", "scratch", "itching", "itches", "itchy")):
        return None
    # Nor is a fence or a lead a person: "my dog is biting the fence" is the chewing answer.
    # "the door" and "his bone" are left out on purpose: a dog that bites a person at the door, and
    # one that guards a bone, are both about a person and belong here.
    if has("fence", "fences", "lead", "leads", "sofa", "toy", "toys", "bed", "cushion", "blanket",
           "cage", "nappy", "slipper", "slippers", "shoe", "furniture", "wall", "stick", "sticks",
           "skirting"):
        return None
    # A dog at someone now is the ambulance, and the barrier advice is the safety module's own.
    if has(*BITE_NOW):
        return ("Call 999 or 911 now, and don't put yourself in the way: shout and use a barrier "
                "- a door, a chair, a bin - not your arms, and get children and the dog into "
                "separate rooms. A dog that has hold of someone and will not let go is a police "
                "job too, and 101 takes the report once everyone is safe.")
    # A puppy mouthing hands is teething, and the answer is a redirect rather than a report.
    if has(*BITE_TEETH) and not has(*BITE_SKIN) and not has(*BITE_CHILD_WORDS):
        # Main's puppy answer, kept word for word: it is already the right one.
        return ("Yelp or say \"ow\" and stop the game the moment teeth touch skin, then turn away "
                "for ten seconds before playing again; the puppy learns that teeth end the fun. "
                "Give a chew toy instead every time he goes for hands, and if he is over-tired, a "
                "nap settles more of it than any training.")
    # A bite that has already landed on a child is not a training question: the child is seen
    # today and the bite is reported, whatever else the line says.
    if has(*BITE_CHILD_WORDS) and has(*BITE_DONE_DEED):
        return BITE_REPORT_CHILD
    # A bite that drew blood, or one that landed on somebody else, is a report and not a habit.
    if has(*BITE_SKIN) or (has(*BITE_SOMEONE_ELSE) and not has(*BITE_CHILD_WORDS)
                           and has("bit", "bitten", "nipped")):
        return BITE_REPORT
    advice = ("Stop the biting by changing what happens before it: keep him away from the "
              "situations that set it off - a baby gate or a lead indoors is not a failure - "
              "muzzle-train him for the vet and the walk, and book the vet to rule out pain, a bad "
              "ear or bad eyesight. Punishing him after the event teaches nothing, and a "
              "qualified behaviourist is worth the money for a dog that has bitten once.")
    if has(*BITE_OTHERS_HABIT):
        # A dog that nips the baby or the visitors is the one that needs a door between them and
        # the person today, so the management half comes with the training half.
        if has(*BITE_CHILD_WORDS):
            who, alone = "the children", ", and never leave them alone together"
        elif has(*BITE_DOOR_WORDS):
            who, alone = "anyone coming to the door", ""
        else:
            who, alone = "visitors", ""
        advice += (" Until someone has seen him, keep a shut door or a gate between him and %s%s."
                   % (who, alone))
    return advice


# "is it ok to give my dog the leftovers" asks what may go on the plate, and "my dog ate the
# leftovers" asks what to do now - the same words, one event later. Both reach the leftovers
# entry, so it carries two cards and picks between them on the tense of the line rather than
# telling somebody whose dog has already eaten to "keep it to a tablespoon or two".
PLATE_LEFTOVERS_TEXT = (
    "Plain cooked meat and cooked veg in small amounts are fine, cut small and cooled, with no "
    "gravy, salt or seasoning. What must never be on the plate is onion, garlic, leek and chives, "
    "grapes and raisins, chocolate, and any cooked bone, because all of them are the ones that "
    "end in a vet visit. Rich or salty takeaway is the fourth: it is the fat and the salt that "
    "cause the trouble rather than the meat. Keep it to a tablespoon or two, count it as part of "
    "the day's food, and give anything new as a small piece first.")
ATE_LEFTOVERS_TEXT = (
    "Then what matters is what was in it: onion, garlic, leek or chives, grapes and raisins, "
    "chocolate or a cooked bone mean a call to the vet today, even if the {kind} seems fine, and "
    "say how much and when. If it was plain meat, veg or a bit of bread, most {they} are fine: "
    "watch for vomiting, diarrhoea or a sore belly over the next day, keep water down, and ring "
    "the vet if it starts being sick more than once or goes off its food.")
# The past-tense words, and the phrases a word set cannot see. "can my dog have the leftovers" is
# the plate question and "my dog got into the leftovers" is what to do now, so the tense decides -
# and the present tense is the habit, not the event: "my dog eats leftovers" is asking the plate
# question, so "eats" and a bare "eating" are not here.
LEFT_OVERS_EATEN = ("ate", "eaten", "swallowed", "stole", "stolen")
LEFT_OVERS_EATEN_PHRASES = ("got into", "has had", "just had", "already had", "already eaten",
                            "helped himself", "helped herself", "is eating", "was eating",
                            "kept eating")


# A plate of leftovers is not a named food, so the small-animal table cannot answer it: it is keyed
# by one food at a time. "My rabbit ate the leftovers" was answered "Nice one. How did the rest of
# it go?", and the rabbit is the pet where a mixed plate is riskiest - its gut has to keep moving
# and a rabbit that stops passing droppings goes downhill within a day. One card per kind of small
# pet, because the danger is a different organ: the gut for a rabbit or a guinea pig, the pouches
# and the runs for a hamster, the whole bird for a budgie.
_SMALL_PET_ATE_LEFTOVERS = {
    "rabbit": ("Hay and water are the whole job now: leave both within reach and watch the "
               "droppings. A bit of bread, fruit or something off a plate is usually fine, but a "
               "rabbit's gut has to keep moving - soft or no droppings within twelve hours, or a "
               "rabbit that sits hunched and will not eat, is the vet today. Do not starve it and "
               "do not wait for it to pick up, because a rabbit that stops eating goes downhill "
               "inside a day."),
    "guinea pig": ("Hay, water and the nuggets are the whole job now, and watch the droppings. A "
                   "bit of something off a plate is usually fine, but a guinea pig's gut has to "
                   "keep moving - soft or no droppings within twelve hours, or one that sits "
                   "hunched and will not eat, is the vet today. It cannot make its own vitamin C, "
                   "so do not let a plate of scraps replace the nuggets."),
    "hamster": ("Clear out what is left and keep its own food and water going, and watch it: a "
                "hamster that is still busy, eating and hoarding is fine, because a scrap of most "
                "human food is a treat rather than a poison. The trouble is what a mixed plate "
                "carries - salt, sugar, cheese and fried food - so expect a loose back end, and "
                "ring the vet if it is hunched, cold, not eating or has diarrhoea for more than a "
                "day."),
    "gerbil": ("Clear out what is left and keep its own food and water going, and watch it: a "
               "gerbil that is still busy, eating and digging is fine, because a scrap of most "
               "human food is a treat rather than a poison. Salt, sugar and fried food are what a "
               "mixed plate carries, so expect a loose back end, and ring the vet if it is "
               "hunched, cold, not eating or loose for more than a day."),
    "chinchilla": ("Clear out what is left and keep the hay, pellets and water going: a chinchilla "
                   "is the least able of the small pets to cope with sugar and fat, so a plate of "
                   "scraps is the one to avoid rather than a treat. Watch the droppings and ring "
                   "the vet if it is hunched, not eating, or loose for more than a day."),
    "bird": ("Clear the plate away and give it its own food and water, then watch it: a budgie or "
             "a parrot that has had plain bread or veg is usually fine, but anything salty, "
             "sugary, fatty or fried, and anything with avocado, chocolate, onion or caffeine in "
             "it, is a vet call today. A bird that sits fluffed up, stops eating or has loose "
             "droppings needs the vet rather than a wait-and-see, because a bird hides illness "
             "until it is very ill."),
}


# The rabbit has no row in SMALL_PET_DIET - its diet is the `rabbit-food` entry - so the plate
# answer for a rabbit is the same facts kept in one line, and the rest come from the table.
_SMALL_PET_DIET_OR_PLATE = dict(SMALL_PET_DIET)
_SMALL_PET_DIET_OR_PLATE["rabbit"] = (
    "Leftovers are not a rabbit's food: hay is the diet, a pile the size of the rabbit every day, "
    "with a handful of greens and a measured scoop of nuggets, and a rabbit that fills up on bread "
    "or scraps stops eating the hay it needs. Nothing off a plate at all is the simple rule, "
    "because sugar and starchy food upset the gut that keeps a rabbit alive.")


# A dog or a cat that got into the bin already has a card of its own, and it is the better one: it
# asks what was in there and names the poisons, which a plate-of-leftovers answer cannot, because
# the bin is not a known plate. So this row stands down for that pair and only that pair - a rabbit
# or a guinea pig in the bin has no card of its own, and the gut risk is the same either way.
_A_BIN = re.compile(r"\b(?:bin|bins|rubbish|trash|landfill|compost)\b")
_A_DOG_OR_CAT = re.compile(r"\b(?:dog|dogs|puppy|pup|pups|cat|cats|kitten|kittens)\b")


def _the_bin_is_the_dogs_question(understood):
    text = ((understood or {}).get("clean") or "").lower()
    return bool(_A_BIN.search(text) and _A_DOG_OR_CAT.search(text))


def _leftovers_answer(memory, understood):
    """The plate answer, or the what-to-do-now answer when the animal has already eaten."""
    pet = _pet_words(understood)
    text = ((understood or {}).get("clean") or "").lower()
    words = set(re.findall(r"[a-z']+", text))
    eaten = bool(words & set(LEFT_OVERS_EATEN)) or any(
        phrase in text for phrase in LEFT_OVERS_EATEN_PHRASES)
    # `_small_pet_kind` has no rabbit branch (the rabbit's food answers live in their own entry),
    # so the rabbit is read here rather than drawn into every table that function feeds.
    kind = ("rabbit" if re.search(r"\b(?:rabbit|rabbits|bunny|bunnies)\b", text)
            else _small_pet_kind(text))
    if kind in _SMALL_PET_ATE_LEFTOVERS:
        if not eaten:
            return _SMALL_PET_DIET_OR_PLATE[kind]
        return _SMALL_PET_ATE_LEFTOVERS[kind]
    if not eaten:
        return PLATE_LEFTOVERS_TEXT
    return ATE_LEFTOVERS_TEXT.format(kind=pet["kind"], they=pet["they"])


# A card about an animal answers a line about the animal. When the line reports the person's
# own routine with it - "i walk the dog every day", "i feed the cats at six", "i take him out
# twice a day" - the animal is what they do it to, and the routine is the news. The habit tail
# says that back ("You walk the dog every day. That's a habit now."), while a card here answers
# a different line: "how much exercise should my dog get", which nobody asked.
#
# Declared for the whole domain so every card in this file stands aside together, rather than
# a guard copied into each of them. Read by bot/knowledge/__init__.py::entries.
def STANDS_ASIDE(understood):
    return not bool((understood or {}).get("routine"))


# A line that asks how to say something to the animal's *owner* is a conversation about people,
# not a question about the behaviour - and so is the follow-up that has moved on to whether to
# raise it at all. Both shapes reach these rows with the animal and the behaviour carried from
# the turn before: after "how do i tell my friend her cat scratched my child" and "she got
# defensive", the next turn "should i drop it" was answered with the post-and-throw card, which
# is advice about a sofa the person had stopped asking about. One list, so all four rows stand
# down together and the next wording only has to be added here.
_CAT_SICK_REPLY = ("A cat that keeps being sick needs the vet rather than a wait-and-see: repeated "
                   "vomiting in a cat is often a swallowed blockage (string, a hairband, a toy) or "
                   "a poison, and cats go downhill fast. Offer small amounts of water, no food for "
                   "a few hours, and ring the vet; go straight away if there is blood, if she is "
                   "retching with nothing coming up, or if she is flat and hiding.")
_DOG_SICK_REPLY = ("One vomit or one loose poo in a dog that is otherwise bright is usually "
                   "nothing: withhold food for a few hours, then offer small amounts of plain "
                   "chicken and rice, and keep the water down. Ring the vet if it repeats, if "
                   "there's blood, if he is flat and not drinking, or if it is a puppy, an old dog "
                   "or going on for more than a day.")

_RABBIT_SICK_REPLY = ("A rabbit that is being sick needs a vet today, not a wait-and-see: a "
                      "rabbit cannot vomit, so what looks like sickness is usually a blockage or "
                      "something it should not have eaten, and a rabbit that stops eating goes "
                      "downhill within a day. Keep him warm and calm, leave water and hay within "
                      "reach, do not syringe anything down him, and ring the vet now.")

def _chocolate_for(animal):
    """The poison card for the animal that ate it.

    "My cat ate chocolate" was answered "chocolate is poisonous to dogs ... ring your vet with the
    dog's weight": true, and about the wrong animal. The advice is the same and the animal is not.
    """
    if animal == "cat":
        return ("Yes, chocolate is poisonous to cats as well as dogs: the darker the chocolate, "
                "the worse it is, and a cat is small enough that a couple of squares matters. Ring "
                "your vet with the cat's weight and roughly how much and what kind of chocolate it "
                "ate, and don't wait for symptoms - the first signs are being sick, a racing heart "
                "and restlessness.")
    if animal and animal != "dog":
        return ("Yes, chocolate is poisonous to " + animal + "s: the darker the chocolate, the "
                "worse it is. Ring your vet with its weight and roughly how much and what kind of "
                "chocolate it ate, and don't wait for symptoms.")
    return ("Yes, chocolate is poisonous to dogs: the darker the chocolate, the worse it is. Ring "
            "your vet with the dog's weight and roughly how much and what kind of chocolate it "
            "ate; don't wait for symptoms.")


def _the_animal_that_ate(understood):
    """The animal named in the line, as "cat", "dog", "rabbit" and so on, or None."""
    words = [str(word).lower() for word in ((understood or {}).get("words") or ())]
    text = " ".join(words) or str((understood or {}).get("clean") or "").lower()
    for word, animal in (("kitten", "cat"), ("kittens", "cat"), ("cat", "cat"), ("cats", "cat"),
                         ("puppy", "dog"), ("pup", "dog"), ("dog", "dog"), ("dogs", "dog"),
                         ("rabbit", "rabbit"), ("bunny", "rabbit"), ("hamster", "hamster"),
                         ("guinea pig", "guinea pig"), ("parrot", "parrot"), ("budgie", "budgie")):
        if word in text.split() or (" " + word + " ") in (" " + text + " "):
            return animal
    return None


def _the_small_animal(text):
    """The small animal named in `text`, as the person would say it, or None."""
    said = " " + str(text or "").lower() + " "
    best, best_at = None, None
    for word, noun in _A_SMALL_ANIMAL:
        at = said.find(" " + word + " ")
        if at < 0:
            continue
        if best_at is None or at < best_at:
            best, best_at = noun, at
    return best


def _small_animal_sick(animal):
    """The card for a small animal that keeps being sick.

    Something that small is flat and dehydrated within a day, and the cause is nearly always one
    of four things, so the answer says what to do while the phone is ringing rather than "see a
    vet". A rat in a house is a pest; a rat in a cage is a pet, and this is the pet's card.
    """
    return ("A " + animal + " that keeps being sick needs the vet today rather than a "
            "wait-and-see: something that small can be flat and dehydrated within a day, and the "
            "sickness is usually the teeth, an ulcer or something it should not have eaten. Put "
            "water in a shallow bowl as well as the bottle, keep it warm and quiet, offer its usual "
            "food or wet food, and weigh it - a small animal that has lost weight is a vet call even "
            "if it is still nibbling.")


# An animal that keeps being sick is the animal's card, not the person's. "my cat keeps being
# sick after eating" reached the human what-to-eat-while-ill answer ("toast, crackers, rice, a
# banana"), and so did the plain follow-up "she keeps being sick after eating" after "my cat is
# sick" - the animal had been named in the turn before, and no key word of the cat row was in the
# line at all (patient-olive, #conversation 76637).
# Two parts, because a key needs a word in each of two positions to count at all: the sickness,
# and the word that says it keeps happening.
_A_RABBIT = ("rabbit", "rabbits", "bunny", "bunnies")
# The animals small enough that the same words are the same urgency, and the name to say back to
# the person ("a guinea pig that keeps being sick"), because "a small animal" reads as a leaflet.
_A_SMALL_ANIMAL = (("guinea pigs", "guinea pig"), ("guinea pig", "guinea pig"),
                   ("hamsters", "hamster"), ("hamster", "hamster"), ("gerbils", "gerbil"),
                   ("gerbil", "gerbil"), ("rats", "rat"), ("rat", "rat"),
                   ("mice", "mouse"), ("mouse", "mouse"), ("ferrets", "ferret"),
                   ("ferret", "ferret"), ("chinchillas", "chinchilla"),
                   ("chinchilla", "chinchilla"), ("degus", "degu"), ("degu", "degu"),
                   ("hedgehogs", "hedgehog"), ("hedgehog", "hedgehog"))
_PET_SICK_AGAIN = (("sick", "sickness", "vomiting", "vomit", "vomited", "throwing up",
                    "threw up", "poorly", "off his food", "off her food"),
                   ("keeps being sick", "keep being sick", "kept being sick", "keeps vomiting",
                    "keep vomiting", "keeps throwing up", "keeps being poorly", "after eating",
                    "after every meal", "after meals", "after food", "after his food",
                    "after her food", "after his dinner", "after her dinner",
                    "cant keep food down", "can't keep food down", "cant keep anything down",
                    "can't keep anything down", "again and again"))

# The animals this row speaks for, and the people it must not speak for: a child who keeps being
# sick is the person's question, however recently a cat was mentioned.
_PET_SUBJECT = ("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies", "pup",
                "pups", "rabbit", "rabbits", "bunny", "bunnies", "hamster", "hamsters",
                "guinea pig", "guinea pigs", "ferret", "ferrets", "parrot", "parrots", "budgie",
                "budgies", "tortoise", "tortoises", "pet", "pets",
                # the small ones: "my rat keeps being sick" is read as the health talk, and a rat
                # in a cage is not the pest in the loft
                "rat", "rats", "mouse", "mice", "gerbil", "gerbils", "degu", "degus",
                "hedgehog", "hedgehogs", "chinchilla", "chinchillas")
_A_PERSON = ("son", "sons", "daughter", "daughters", "child", "children", "kid", "kids",
             "baby", "babies", "toddler", "toddlers", "mum", "mums", "mummy", "mom", "dad",
             "dads", "daddy", "mother", "father", "wife", "husband", "partner", "boyfriend",
             "girlfriend", "brother", "sister", "grandson", "granddaughter", "grandchild",
             "aunt", "uncle", "nephew", "niece", "friend", "friends", "neighbour", "neighbor",
             "patient",
             # the speaker. "i keep being sick after eating" is a person's line even straight
             # after "my cat is sick", and this row must not touch it at all.
             "i", "im", "i'm", "me", "myself", "we", "us", "our", "ours")
# The same list without the speaker: "do i need the vet" names no patient at all, and the speaker
# is the one asking rather than the one who is ill.
_NOT_A_SPEAKER = ("i", "im", "i'm", "me", "myself", "we", "us", "our", "ours")
# "i need a vet for my family" names no animal and no single person, and a family is a group of
# people too.
_A_PERSON_NAMED = tuple(word for word in _A_PERSON
                        if word not in _NOT_A_SPEAKER) + ("family", "household")
# The pronouns are left out on purpose: "he keeps being sick after his dinner" and "she keeps
# being sick" are exactly how a dog and a cat are talked about.
# The animals whose sickness is a card of its own: a rabbit or a hamster that keeps being sick
# is not a cat and not a dog, so this row stays out of the way and leaves the line to the rows
# that answer for them.
_NOT_A_CAT_OR_DOG = (
                     "parrot", "parrots", "budgie", "budgies", "bird", "birds", "tortoise",
                     "tortoises", "snake", "snakes", "lizard", "lizards", "horse", "horses",
                     "pony", "ponies", "chicken", "chickens", "fish", "fishes")


def _this_is_the_pets_talk(understood):
    """Whether the line is being read as the pets talk, or names an animal itself.

    The row can read the line alone or the turns before it, so the person's follow-up is the
    danger: "my mum is ill" then "she keeps being sick after eating" is the same words as the
    cat's follow-up and the sick person's question, and a reply that only says "not mine" at
    the last moment hands the turn to the chat module and loses the answer that was coming
    ("How long has that been going on with your mum?"). The reading of the line says which talk
    this is - the cat's follow-up is read as pets and the person's as health - so the row is
    only offered for the pets one, and for a line that names the animal in its own words.
    """
    reading = understood or {}
    topics = reading.get("topics") or ()
    if isinstance(topics, str):
        topics = (topics,)
    if "pets" in topics or reading.get("topic") == "pets":
        return True
    said = set(re.findall(r"[a-z']+", " " + str(reading.get("clean") or "").lower() + " "))
    return bool(said & set(_PET_SUBJECT))


def _a_word_in(text, words):
    """Whether one of `words` is in `text` as a whole word."""
    found = set(re.findall(r"[a-z']+", " " + text + " "))
    return bool(found & set(words))

def _a_person_who_is_not_the_patient(understood):
    """Whether the line names a person and no animal, so the vet is not who is being asked.

    "my mum is ill do i need the vet" and "should i take my friend to the vets" are a person who
    needs a doctor, and the vet-decision card answered both with what to do about an animal. The
    animal words are read too: "should i take my son's dog to the vet" names a person and the
    patient is the dog, so that line keeps the vet answer.
    """
    said = " ".join(str((understood or {}).get("clean")
                        or (understood or {}).get("text") or "").lower().split())
    if _a_word_in(said, _PET_SUBJECT) or _the_small_animal(said):
        return False
    if _a_word_in(said, _A_PERSON_NAMED):
        return True
    return any(phrase in said for phrase in _A_SPEAKER_IS_ILL)


# The speaker is the patient when they say so: "i am ill do i need the vet" is not a line about an
# animal, and the animal words have already been ruled out before these are read.
_A_SPEAKER_IS_ILL = (
    "i am ill", "im ill", "i'm ill", "i feel ill", "i am sick", "im sick", "i'm sick",
    "i feel sick", "i am unwell", "im unwell", "i'm unwell", "i feel unwell",
    "i have a temperature", "ive got a temperature", "i've got a temperature",
    "ive been sick", "i've been sick", "i have been sick", "i am in pain", "im in pain")

_WHEN_A_VET_IS_NEEDED = (
    "Ring today rather than wait if the animal is struggling to breathe, straining to pee and "
    "passing nothing (a blocked cat can die in a day), has a hard swollen belly, is fitting, has "
    "eaten something poisonous, or cannot stand - say exactly what you see when you ring. For "
    "anything else the call is free: most practices triage on the phone and will tell you whether "
    "to come in, and a nurse appointment costs less than a consultation.")

_A_VET_IS_FOR_ANIMALS = (
    "A vet treats animals, not people: for a person, ring 111 or the GP surgery today - and 999 "
    "if they are struggling to breathe, confused, blue at the lips or have chest pain. Say how "
    "long it has been going on and what you have noticed, and the call costs nothing. If it is a "
    "child, a baby or someone frail or elderly, ring rather than wait to see how the day goes.")


def _the_vet_question(memory, understood):
    """The vet decision for an animal, and the doctor for a person with no animal in the line."""
    if _a_person_who_is_not_the_patient(understood):
        return _A_VET_IS_FOR_ANIMALS
    return _WHEN_A_VET_IS_NEEDED


def _pet_sick_again(memory, understood):
    """The cat or dog card for an animal that keeps being sick, or None for anybody else.

    The line alone can say whose it is - "my cat keeps being sick after eating" - and then the
    animal is in it. More often it cannot: "she keeps being sick after eating" is asked straight
    after "my cat is sick", so the animal is read from the turns just before. Only a cat or a dog
    is spoken for: a rabbit that keeps being sick needs a rabbit's answer and a person needs the
    person's, and both are left to the rows that have one.
    """
    clean = " ".join(str((understood or {}).get("clean")
                         or (understood or {}).get("text") or "").lower().split())
    here = set(re.findall(r"[a-z']+", " " + clean + " "))
    cat_here = bool(here & {"cat", "cats", "kitten", "kittens"})
    dog_here = bool(here & {"dog", "dogs", "puppy", "puppies", "pup", "pups"})
    rabbit_here = bool(here & set(_A_RABBIT))
    small_here = _the_small_animal(clean)
    if small_here and not (cat_here or dog_here or rabbit_here):
        return _small_animal_sick(small_here)
    if rabbit_here and not (cat_here or dog_here):
        return _RABBIT_SICK_REPLY
    if cat_here or dog_here:
        return _CAT_SICK_REPLY if cat_here and not dog_here else _DOG_SICK_REPLY
    if not isinstance(memory, dict):
        return None
    earlier = ""
    for turn in (memory.get("turns") or [])[-4:]:
        if not isinstance(turn, dict):
            continue
        said = " ".join(str(turn.get("user") or "").lower().split())
        if said and said != clean:
            earlier += " " + said
    if not earlier.strip():
        return None
    if _a_word_in(earlier, _A_PERSON) and not _a_word_in(earlier, _PET_SUBJECT):
        return None
    # `_a_word_in` looks at single words, and "guinea pig" is two, so the small animals are read
    # by the same helper that reads the line itself.
    if not (_a_word_in(earlier, _PET_SUBJECT) or _the_small_animal(earlier)):
        return None
    # A rabbit, a hamster or a bird in the turn before is not a cat and not a dog: this row has
    # no card for them, and saying "the same goes for a dog" over one is worse than leaving the
    # line to its own rows.
    if _a_word_in(earlier, _NOT_A_CAT_OR_DOG) and not _a_word_in(
            earlier, ("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies")):
        return None
    cat_named = _a_word_in(earlier, ("cat", "cats", "kitten", "kittens"))
    dog_named = _a_word_in(earlier, ("dog", "dogs", "puppy", "puppies", "pup", "pups"))
    # A rabbit is not a small dog here either: a rabbit cannot vomit at all, so the same words
    # are an urgent different question, and it gets the rabbit's card.
    if _a_word_in(earlier, _A_RABBIT) and not (cat_named or dog_named):
        return _RABBIT_SICK_REPLY
    # The same for a hamster, a guinea pig or a rat: the words are theirs too, and a name in the
    # turn before is how the follow-up arrives ("my guinea pig is unwell" then "he keeps being sick").
    if not (cat_named or dog_named):
        small_earlier = _the_small_animal(earlier)
        if small_earlier:
            return _small_animal_sick(small_earlier)
    if cat_named and not dog_named:
        return _CAT_SICK_REPLY
    if dog_named and not cat_named:
        return _DOG_SICK_REPLY
    return _CAT_SICK_REPLY + " The same goes for a dog that keeps being sick."

_SAYING_FRAME = ("how do i tell", "how do i say", "how do i ask", "what do i say", "how to tell",
                 "tell my friend", "tell her", "tell them", "tell him", "bring it up",
                 "say to her", "say to him", "say to them",
                 "should i drop", "drop it", "let it go", "letting it go", "leave it alone",
                 "is it worth", "worth saying", "worth bringing", "say anything", "should i say",
                 "should i bring", "say something")
# Words that stand a *biting* row down belong to that row's own `avoid`, never here. When the
# training words were added to this shared frame they also stood the cat-biting row down, and
# every one of its key words with them: "he keeps biting my hands", "my cat keeps biting the
# children", "how do i stop my cat biting my hand" and "how do i stop my kitten biting my hands"
# all lost the play answer - to the human wrist-tendon card, the vet's desk, a shrug or a search
# hedge. A body part ("hands", "fingers") and a person ("kids", "children") are what a cat
# bites; they are not a how-to-say-it frame.

# The news and the shopping question are two different turns, and the same paragraph for both
# reads as one answer given twice: "we are getting a puppy" then "what do i need to buy first" came
# back as "Nothing separate for buy - it is the same advice: For a puppy: a bed, two bowls...". The
# shopping turn keeps the list exactly as it was; the news gets its own opening and the same things
# named, so the second turn is a fresh answer rather than the first one handed back.
_SHOPPING_WORDS = ("buy", "buying", "bought", "need", "needs", "supplies", "supply", "shopping",
                   "shop", "kit", "get", "order", "pick")
_DOG_KIT_LIST = ("A bed it can stretch out flat in, two bowls, a collar and a lead, a harness for "
                 "walks where it pulls, poo bags and food of the brand it is already on, plus a "
                 "coat if it has a thin coat like a greyhound. A rescue usually comes with its own "
                 "lead and a bag of food, so ask the centre what it has been eating and keep to "
                 "that for the first fortnight, and budget about £1,500 to £2,000 a year for a dog "
                 "before any vet bill.")
_DOG_KIT_NEWS = ("Lucky you. The first things to have in are a bed it can stretch out flat in "
                 "and two bowls, a collar and a lead with a tag on it, poo bags, a harness for "
                 "walks where it pulls, and the food it is already on so its stomach stays "
                 "settled. Register with a vet in the first week, and if it is a rescue ask the "
                 "centre what it has been eating and how much it has been walked.")
_PUPPY_KIT_LIST = ("For a puppy: a bed, two bowls, a crate or pen, a collar and lead, an "
                   "adjustable harness, safe chew toys, poo bags and puppy food of the brand it's "
                   "already on. Book the first vet check for the first week and ask about "
                   "vaccinations and worming then.")
_PUPPY_KIT_NEWS = ("Lucky you. Before a puppy comes home: a bed, two bowls, a crate or pen, a "
                   "collar and lead, an adjustable harness, safe chew toys, poo bags and puppy "
                   "food of the brand it is already on. Book the first vet check for its first "
                   "week and ask about vaccinations and worming then.")


def _shopping_or_news(understood):
    """True when the line is the question to buy, False when it is the news that one is coming."""
    words = set((understood or {}).get("words") or ())
    return any(word in words for word in _SHOPPING_WORDS)


def _dog_kit(memory, understood):
    return _DOG_KIT_LIST if _shopping_or_news(understood) else _DOG_KIT_NEWS


def _puppy_kit(memory, understood):
    return _PUPPY_KIT_LIST if _shopping_or_news(understood) else _PUPPY_KIT_NEWS


def _fish_tank(memory, understood):
    """The weekly water change, or the impeller when the filter is the thing making the noise."""
    line = " " + str((understood or {}).get("clean") or "").lower() + " "
    if any(word in line for word in (" noisy", " noise", " rattl", " humming", " buzzing",
                                     " loud")):
        return ("A filter that rattles or hums is usually air in the housing or grit in the "
                "impeller: unplug it, lift the impeller out and rinse it, and top the tank up so "
                "the water is above the intake. If it still grinds the impeller is worn, and that "
                "is a cheap part rather than a new filter.")
    return ("Change about a quarter of the water once a week, and rinse the filter sponge in the "
            "water you take out, never under the tap. A full clean strips the good bacteria and "
            "does far more harm than the dirt.")


def _rescue_or_baby(memory, understood):
    """The rescue-versus-baby pick, in the animal the line names.

    A cat question and a dog question get the same advice in different words, so the animal is
    read off the line rather than being fixed in the reply: "should i get a rescue cat or a
    kitten" was answered with the scent-before-sight paragraph for a second cat.
    """
    words = set(re.findall(r"[a-z']+", ((understood or {}).get("clean") or "").lower()))
    if words & {"cat", "cats", "kitten", "kittens", "kitty"}:
        return ("A rescue cat comes with a known character, is past the kitten climbing and "
                "biting, and settles in a week or two; a kitten is months of work but you shape "
                "it from the start. Out at work all day, or a first cat: the adult rescue is the "
                "kinder start.")
    return ("A rescue adult usually comes with a known character, is past the chewing, and settles "
            "in a week or two; a puppy is a year of work but you shape everything from the start. "
            "First dog, or a busy household: the rescue is the kinder start.")



# The pets that are not a dog or a cat, which the human-painkiller answer had no word for: "can i
# give my rabbit ibuprofen" was answered with the rabbit's diet, and "can i give my rabbit calpol"
# with it too. It is the same question as a dog's - a person reaching for their own tablets - and
# the small animals are the ones a human dose poisons fastest.
HUMAN_TABLET_PETS = ("rabbit", "rabbits", "bunny", "guinea", "guineas", "hamster", "hamsters",
                     "rat", "rats", "mouse", "mice", "gerbil", "gerbils", "ferret", "ferrets",
                     "bird", "birds", "budgie", "budgies", "parrot", "parrots", "tortoise",
                     "tortoises")
# A bald patch on a rabbit, a guinea pig or a hamster came back as the person's own hair loss:
# "Hair that comes out in handfuls for a few months is usually telogen effluvium", which is a
# different animal's problem entirely. The state words are the same for both, so the animal in the
# line decides: this row takes the small ones, and the human card stands down on them.
SMALL_FUR = re.compile(r"\b(?:rabbit|rabbits|bunny|bunnies|guinea ?pigs?|hamsters?|gerbils?|"
                       r"budgies?|budgerigars?|cockatiels?|canar(?:y|ies)|chinchillas?|ferrets?|"
                       r"degus?|rats?|mice|mouse|tortoises?|horses?|pony|ponies)\b")
# "losing" and "loss" are the only state words with no fur in them, and they carry a weight
# question too: "my rabbit is losing weight" was this card, and a bald patch is no answer to it.
SMALL_FUR_STATE = re.compile(
    r"\b(?:bald|bald patch|bald patches|bare patch|fur|hair|coat|mites?|mange|ringworm|scabby|"
    r"scabs?|flaky|dandruff|itching|itchy|scratching|shedding|moulting|molting|"
    r"plucking|plucked|thin|thinning|patchy|patches?|bare|feathers?|feather)\b")


# A bird that plucks itself is not a moult, and the plucking card says what to do about it while
# this one opens on a moult: "my budgie is plucking its feathers" stands this row down.
BIRD_FUR = re.compile(r"\b(?:budgies?|budgerigars?|cockatiels?|canar(?:y|ies)|parrots?|"
                      r"parakeets?|lovebirds?|birds?)\b")
BIRD_PLUCKING = re.compile(r"\b(?:plucking|plucked|plucks|pulling|pulls|picked|picking|"
                           r"picking at|self[- ]plucking|barbering)\b")


def _small_fur_loss(memory, understood):
    """A bald or itchy patch on a small animal, answered for the animal the line names."""
    clean = str((understood or {}).get("clean") or "").lower()
    if not SMALL_FUR.search(clean):
        return None
    if BIRD_FUR.search(clean) and BIRD_PLUCKING.search(clean):
        return None
    if re.search(r"\b(?:rabbit|rabbits|bunny|bunnies)\b", clean):
        return ("Bald patches on a rabbit are usually fur mites - the flaky white dandruff that "
                "crawls is the giveaway - ringworm, which is round and scaly, or a normal moult, "
                "which comes out in tufts and leaves patchy fur for a week or two. A vet treats "
                "mites with a spot-on made for rabbits, and every rabbit in contact needs it, "
                "since dog and cat flea products can kill a rabbit. A doe pulling fur from her "
                "dewlap is building a nest.")
    if re.search(r"\b(?:guinea ?pigs?)\b", clean):
        return ("Hair loss in a guinea pig is usually mites, which they carry and then suffer from "
                "under stress, or ringworm: both need a vet, and every pig in the hutch treated. "
                "In an older sow, bald flanks point at ovarian cysts. Guinea pigs cannot make "
                "their own vitamin C, so a diet without it shows in a poor coat too.")
    if re.search(r"\b(?:hamsters?)\b", clean):
        return ("A bald patch on a hamster is often normal - the scent gland on the belly wears "
                "bare - but a patch that spreads, itches or has flakes on the skin is mites, "
                "ringworm or an over-grooming cagemate, and it needs a vet who treats small "
                "furries. Check the bedding and the wheel for rubbing, and never use a dog or "
                "cat mite product on it.")
    if re.search(r"\b(?:gerbils?|chinchillas?|degus?|rats?|mice|mouse)\b", clean):
        return ("Mites, ringworm and a cagemate over-grooming it are the usual causes of a bald "
                "patch, scabs or flaky skin on a rat, gerbil, chinchilla or mouse: hair thin "
                "along the back and shoulders point at mites or ringworm, and bald patches on "
                "the head and shoulders of the others in the cage point at barbering. Both need "
                "a vet who treats small furries, and never use a dog or cat mite product on it.")
    if re.search(r"\b(?:budgies?|budgerigars?|cockatiels?|canar(?:y|ies))\b", clean):
        return ("Feather loss in a bird is usually a moult, a companion pulling the feathers out, or "
                "mites, and a moult leaves the wing and tail feathers even. A bare patch with "
                "sore or flaky skin, or a bird plucking itself, needs an avian vet - the "
                "condition is often boredom, a bad diet or a liver problem rather than mites.")
    if re.search(r"\b(?:horses?|pony|ponies)\b", clean):
        return ("A bald patch on a horse is usually a rub: the saddle, a rug or a tight browband "
                "wearing the hair off where the edges sit, and it grows back once the tack fits. "
                "The other causes are ringworm, which is round and scaly with hair standing up "
                "around the edge, rain scald and lice along the back, and sweet itch where the "
                "mane and tail meet the skin at the tail base. Ringworm and lice need the vet or "
                "an SQP at the feed merchant, and ringworm spreads to people, so wash your hands.")
    return ("A bald or itchy patch on a small animal is usually mites, ringworm or over-grooming, "
            "and all three need a vet who treats that species. Check the skin for white flakes or "
            "ringworm's round scaly edge, and never use a dog or cat flea or mite product on a "
            "rabbit, guinea pig, hamster or bird.")


# A dog that is in a hot car now needs the first aid first, and a person asking whether to
# leave him there needs the number and the rule. Both live in one card, so the lead sentence
# is chosen from the line: "my dog was left in a hot car" was answered with the two-hour food
# rule on main, and "can i leave the dog in the car" with four hours at home.
_DOG_COOL = ("was left", "is left", "left him", "left her", "left the dog", "left in the car",
             "is in the car", "is in there", "already in the car", "stuck in the car",
             "shut in", "locked in", "trapped", "cant get out", "can t get out",
             "right now", "at the moment", "panting", "drooling", "wobbly", "limp",
             "collapsed", "in distress", "help")
_DOG_CAR_FIRST_AID = ("Get him out of the car and into the shade now: a car in the sun passes "
                      "40C inside within ten minutes, even with a window down, and a dog can "
                      "only cool himself by panting, so he goes downhill fast. Wet his coat, "
                      "belly and paws with cool - not iced - water, put him in front of a fan "
                      "or the car air conditioning, and offer small sips of water. Ring the "
                      "vet on the way: if he is panting hard, drooling, wobbly, vomiting or "
                      "limp he needs to be seen, and if he is shut in and in distress ring 999, "
                      "because the police can break the window. Never leave a dog in a parked "
                      "car for any length of time on a warm day, and not at all from late "
                      "spring to early autumn.")
_DOG_CAR_RULE = ("Not on a warm day, and not for more than a few minutes at any time of year: "
                 "a car in the sun passes 40C inside within ten minutes even with a window "
                 "down. On a cool morning park in the shade with the windows down a couple of "
                 "inches and water for him, and be back in ten minutes - from late spring to "
                 "early autumn, leave him at home and tie him up outside the shop instead. If "
                 "he is already in a hot car, get him into the shade and wet his coat, belly "
                 "and paws with cool water, and ring the vet if he is panting hard, drooling, "
                 "wobbly or limp; if he is shut in and in distress, ring 999, because the "
                 "police can break the window.")

def _dog_in_a_car(memory, reading):
    """First aid for a dog already in a hot car, the rule for one that might be left there."""
    said = " " + str((reading or {}).get("clean") or (reading or {}).get("text") or "").lower() + " "
    if any(" " + phrase + " " in said for phrase in _DOG_COOL):
        return _DOG_CAR_FIRST_AID
    return _DOG_CAR_RULE


_A_LOST_ANIMAL = ("dog", "doggy", "puppy", "pup", "cat", "kitten", "rabbit", "hamster",
                  "guinea pig", "ferret", "parrot", "budgie", "tortoise")

# "how do i stop my dog escaping the garden" is the boundary question, and the boundary row is a
# better answer than a search routine: a search is for an animal that is already out. The verb
# "escaping" sits on both keys, so the frame decides which question was asked.
_STOPPING_A_PET_GETTING_OUT = re.compile(
    r"\b(how do i stop|how to stop|how can i stop|stop (?:my|him|her|the|it)|prevent|"
    r"keep (?:him|her|it|them) in|secure|escape proof|escaping the garden)\b")


def _a_lost_pet(memory, understood):
    """The lost-pet routine, said about the animal the line named.

    "my cat is missing" answered about a dog is the kind of thing that makes a bot useless, and
    the same advice holds for a cat, so only the noun changes.
    """
    noun = "pet"
    if _STOPPING_A_PET_GETTING_OUT.search(str((understood or {}).get("clean") or "").lower()):
        return ""
    words = " " + " ".join(str(w) for w in ((understood or {}).get("words") or ())).lower() + " "
    for word in _A_LOST_ANIMAL:
        if " " + word + " " in words:
            noun = "cat" if word in ("kitten",) else word
            break
    else:
        text = " " + str((understood or {}).get("clean") or "").lower() + " "
        for word in _A_LOST_ANIMAL:
            if " " + word + " " in text:
                noun = "cat" if word in ("kitten",) else word
                break
    return ("Ring the microchip register and the council's animal warden to report the " + noun +
            " missing, then a photo with the last place seen on the local Facebook and Nextdoor "
            "pages and a call to the vets within five miles. Walk the streets calling calmly, "
            "since a frightened " + noun + " hides close by, and leave something that smells of "
            "home and water at the door. Never chase it: kneel down and let it come to you.")


    # A dog that is out *now* got a lecture about hunting instinct: "my dog got out and i cant find
    # him", "my dog escaped and i cant find him" and "i cant find my dog anywhere" were all the
    # scent card, "my dog has gone missing what do i do" was a search hedge, "my dog is missing" was
    # "sorry to hear that", and "i lost my dog" was the bereavement card - the one reply a person
    # whose dog is alive and loose must never get. The boundary row answers a dog that keeps
    # getting out; this one answers a dog that is not back.
    entry("pet-lost-now", (("dog", "dogs", "doggy", "puppy", "pup", "cat", "cats", "kitten",
                            "kittens", "pet", "rabbit", "hamster", "guinea pig", "ferret",
                            "parrot", "budgie", "tortoise"),
                           ("missing", "gone missing", "went missing", "lost", "cant find",
                            "can't find", "cannot find", "nowhere", "disappeared",
                            "ran off", "ran away", "run off", "bolted", "escaped",
                            "got loose", "got away", "slipped his collar", "slipped her collar",
                            "took off", "not come back", "hasnt come back", "hasn't come back",
                            "didnt come home", "didn't come home", "hasnt come home",
                            "hasn't come home", "not come home", "no sign of")),
          _a_lost_pet,
          # A dog that keeps getting out is the boundary row's question, and a dog that is hurt,
          # dead or being put down is not a search: those cards keep their lines.
          avoid=("keeps", "kept", "always", "every time", "again", "lets himself out",
                 "hit by a car", "run over", "bleeding", "injured", "dead", "died", "dying",
                 "put to sleep", "put down", "passed away", "euthanised", "cremation",
                 "buried", "ashes", "lost my dog", "lost our dog", "lost her today",
                 "how long do", "how do i know",
                 # "my dog is missing his collar" is the harness card, not a search: the thing
                 # missing is a piece of kit, not the animal.
                 "missing his", "missing her", "missing its", "missing a tooth",
                 "missing teeth", "missing a leg", "missing an eye", "missing hair",
                 "is missing out", "missing out", "all the time", "every day", "every week"),
          bias=3),
# Where a pet sleeps depends on the animal, and one paragraph for both animals gave a dog the
# cat's answer: "where should the dog sleep" and "where should my puppy sleep" were told about the
# top of a wardrobe and a windowsill, which is where a cat goes and not where a dog does. The row
# keys on either animal because the question is the same shape, so the reply reads the animal off
# the line and gives its own places; a line that names neither, or names both, keeps the paragraph
# that answers both.
_DOG_SLEEP_WORDS = frozenset(("dog", "dogs", "puppy", "puppies", "pup", "pups", "doggy")
                             + DOG_BREEDS)
_CAT_SLEEP_WORDS = frozenset(("cat", "cats", "kitten", "kittens") + CAT_BREEDS)

_WHERE_THE_CAT_SLEEPS = (
    "Put it where she already sleeps - the top of a wardrobe, a windowsill, the end of the sofa "
    "- and away from the draught between the door and the radiator: a cat picks height and a view "
    "over a soft bed on the floor, so a bed in the middle of a busy room stays empty. Warm it with "
    "a worn jumper of yours for the first week, and if she ignores it, move it rather than buy "
    "another one.")
_WHERE_THE_DOG_SLEEPS = (
    "Put it in the quiet corner of the room he already settles in, out of the walkway and away "
    "from the radiator he will overheat beside: a dog rests best where he can see the door without "
    "lying across the path everyone takes, so the middle of a busy room stays empty. Warm it with "
    "a worn jumper of yours for the first week, and if he will not use it, move it to where he "
    "already lies down rather than buy another one.")
_WHERE_EITHER_SLEEPS = _WHERE_THE_CAT_SLEEPS + " " + _WHERE_THE_DOG_SLEEPS


def _the_animal_in_the_chat(memory, understood):
    """"dog", "cat" or None for the animal the line - or the chat it carries on - is about."""
    said = {str(word).lower() for word in ((understood or {}).get("words") or ())}
    dogs, cats = bool(said & _DOG_SLEEP_WORDS), bool(said & _CAT_SLEEP_WORDS)
    if dogs != cats:
        return "dog" if dogs else "cat"
    if dogs and cats:
        return None
    try:
        from ..memory import topics as _topics
        earlier = " ".join(str(text).lower() for text in _topics.context(memory, 2))
    except Exception:
        return None
    heard = set(re.findall(r"[a-z']+", earlier))
    dogs, cats = bool(heard & _DOG_SLEEP_WORDS), bool(heard & _CAT_SLEEP_WORDS)
    if dogs != cats:
        return "dog" if dogs else "cat"
    return None


def _where_the_pet_sleeps(memory, understood):
    """The sleeping place of the animal the person has."""
    animal = _the_animal_in_the_chat(memory, understood)
    if animal == "dog":
        return _WHERE_THE_DOG_SLEEPS
    if animal == "cat":
        return _WHERE_THE_CAT_SLEEPS
    return _WHERE_EITHER_SLEEPS

# A small pet that has eaten the wrong thing is a diet question, not a dose one: "my rabbit ate
# some carrot tops" is answered by the rabbit's own food, and it was the poisoning card once the
# small animals joined the ask on `pet-ate-some`. A rabbit, a hamster or a bird only reaches that
# card when the line names something that is not food at all - a spray, a bait, a cleaner, a
# medicine - and then the vet call in it is the right answer, whatever the animal.
_SMALL_ANIMAL = re.compile(r"\b(rabbit|rabbits|bunny|bunnies|hamster|hamsters|guinea|gerbil|"
                           r"gerbils|ferret|ferrets|tortoise|bird|birds|parrot|parrots|budgie|"
                           r"budgies|cockatiel|canary)\b")
_NOT_FOOD = re.compile(r"\b(spray|sprays|sprayed|weedkiller|weed killer|bait|baits|pellet|"
                       r"pellets|powder|powders|poison|poisoned|bleach|antifreeze|cleaner|cleaners|chemical|"
                       r"chemicals|disinfectant|medicine|medicines|tablet|tablets|pill|pills|"
                       r"paracetamol|ibuprofen|medicine cabinet|paint|glue|oil)\b")


def _eaten_thing_is_not_food(understood):
    """False only for a small animal whose mouthful was something other than food."""
    text = (understood or {}).get("clean") or (understood or {}).get("text") or ""
    if not _SMALL_ANIMAL.search(text):
        return True
    return bool(_NOT_FOOD.search(text))


# "we got a kitten" is news, and the bot's answer to news is to ask for the name or how old it
# is - the memory store's turn, which is what the deck's kitten chats open with. A care list in
# its place talks over the person and loses the thread: the chat that says "we got a kitten" and
# then "how old is he" was left with a shrug. So the care card only answers a line that asks
# something, a question or a want ("any advice" is read as `recommend`).
_CARE_OF_A_NEW_PET = re.compile(
    r"\b(?:look after|looking after|care for|caring for|care of|bring home|bringing home|"
    r"brought home|just got|we got|we've got|ive got|i've got|settle|settling|get used to|"
    r"advice|tips|what do i need to know|first few days|first week|what do i do)\b")


# "i just got a kitten what do i need" is the shopping list, and the first-days card answered
# it with the feeding-and-vet paragraph: the list is what a person wants on the day they bring
# the kitten home, and it is a card of its own (`kitten-kit`). The words cannot go in `avoid=`
# - an avoid word is read loosely, and "what do i need" would put "need" in a list that stands
# the row down for "what do i need to know about a kitten", which is this card's own question -
# so the reading is here.
_A_SHOPPING_ASK = re.compile(
    r"\b(?:what|which)\b[^?]{0,24}\b(?:do|should|shall|would)\s+i\s+(?:need|buy|get)\b"
    r"|\bneed(?:s|ed)?\s+to\s+(?:buy|get|pick up)\b|\bshopping list\b|\bstarter kit\b",
    re.I)


def _it_asks_what_to_do(understood):
    """False for a line that only says what happened, or that leans on the turn before.

    The question has to be in this line: "how old is he" after "we got a kitten" is a follow-up
    about the age, and reading the kitten off the turn before made the care card answer it.
    """
    if (understood or {}).get("leans_on"):
        # "how old is he" after "we got a kitten" is a question about the age, and the card is
        # read with the turn before it in its words; the memory store owns that line.
        return False
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    said = said.replace("\u2019", "'")
    if not _CARE_OF_A_NEW_PET.search(said):
        return False
    if _A_SHOPPING_ASK.search(said):
        # the supplies list is `kitten-kit`, and it is the better answer on the first day
        return False
    return bool((understood or {}).get("asks"))


ENTRIES = [
    entry("small-pet-fur-loss",
          (("rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs", "guineapig",
            "guineapigs", "hamster", "hamsters", "gerbil", "gerbils", "budgie", "budgies",
            "budgerigar", "cockatiel", "canary", "chinchilla", "ferret", "degu", "rat", "rats",
            "mouse", "mice", "tortoise", "horse", "pony"),
           ("bald", "bald patch", "bald patches", "bare patch", "fur", "hair", "coat", "mites",
            "mite", "mange", "ringworm", "scabby", "scabs", "flaky", "dandruff", "itching",
            "itchy", "scratching", "shedding", "moulting", "molting",
            "thinning", "patchy", "patch", "patches", "feathers", "feather",
            # a bird that pulls its own feathers is the same question and said none of these
            "plucking", "plucked", "bare", "bald spots", "hair loss", "fur loss")),
          _small_fur_loss,
          # a dog and a cat have a card of their own for this, and the diet, the cost and the
          # hutch questions are different questions about the same animal
          avoid=("dog", "dogs", "puppy", "cat", "cats", "kitten", "feed", "food", "diet",
                 "cost", "price", "how much", "hutch", "cage", "buy", "adopt", "rescue",
                 "litter", "bedding", "neutering", "spay", "vaccinations", "jabs"),
          # "my guinea pig has a bald patch" is answered by the new-pet hello - "A guinea pig, is
          # it good company?" - which reads any "my <animal>" line as an introduction. A symptom
          # in the line outranks the hello.
          bias=2),
    # --- losing a pet ---
    entry("pet-loss", (("cat", "dog", "puppy", "kitten", "rabbit", "hamster", "horse",
                       "budgie", "pet"),
                      ("put down", "put him down", "put her down", "put our", "put my",
                       "had to put", "have to put", "putting", "put to sleep", "put him to sleep",
                       "put her to sleep", "to sleep", "euthanised", "euthanized",
                       "euthanise", "euthanize", "died", "dying", "dead", "passed away",
                       "death", "lost my")),
          _pet_loss, bias=2,
          # The bare word "down" used to be in the key above, for "put down"; it also means low, so
          # "my dog seems a bit down" and "the dog seems down in himself" got this bereavement
          # reply. The phrase forms carry the putting-to-sleep sense now, and pet-low takes the
          # rest. "down" is also how people say "put down" with a word in between ("we had to put
          # our cat down this morning"), which is what "put our" and "had to put" are for.
          # A cat can also fall down the stairs, and "dead" is how people say very tired. A pet
          # that has brought something dead in is hunting ("cat-brings-prey"), not dying.
          avoid=("fell", "fall", "falls", "falling", "stairs", "steps", "slipped", "jumped",
                 "knocked", "knock", "sat", "sit", "lies", "lying", "roll", "rolled",
                 "bring", "brings", "bringing", "brought", "drag", "drags", "dragged",
                 "caught", "catches", "prey", "bird", "birds", "pigeon", "pigeons",
                 # "rabbit" is not in this list on its own: a rabbit is a pet someone keeps,
                 # and "my rabbits death" is that pet's death. The hunting verbs above
                 # ("bring", "brought", "drag", "caught") are what keep "the cat brought a
                 # rabbit in" out of here, and they do that on their own. A killed animal is
                 # hunting too, and that is a verb, not a species.
                 "killed a", "kills a", "kill a", "killed my", "kills my", "mauled a", "mauled my",
                 "left", "leaves", "leaving", "found", "finds", "finding", "dropped",
                 "dropping", "deposited", "presented", "presents", "gift", "gifts",
                 "half dead",
                 # things that run down or die that are not pets: a phone battery "dying" in the
                 # line before is the context this entry used to read as a pet death ("will it
                 # hurt my cat" got the grief answer after a battery question)
                 "phone", "phones", "iphone", "android", "battery", "batteries", "charger",
                 "charging", "charge", "laptop", "computer", "car", "engine", "plant",
                 "plants", "grass", "lawn", "weeds", "bulb", "light", "router", "wifi",
                 "internet", "printer", "remote", "torch", "hoover", "vacuum",
                 "washing machine", "boiler", "phone battery", "battery life",
                 "tired", "exhausted", "knackered", "nap", "crate", "for a nap", "asleep",
                 "easy", "against", "weight", "to me", "serious", "funny", "lucky", "quiet",
                 "beat", "right",
                 # "put my cat to sleep at night" is the bedtime routine, not a goodbye
                 "to sleep at", "sleep at night", "sleeping at night", "bedtime", "at bedtime",
                 # "i'm putting the cat in the carrier" is the vet trip, not the goodbye
                 "carrier", "carriers", "basket", "in the box", "into the box", "muzzle", "leash",
                 # "thanks, that helps" in the middle of a loss is an acknowledgement, not a
                 # second death: the loss module has the thread and this entry would say the
                 # condolence again, word for word
                 "thanks", "thank you", "thankyou", "cheers", "that helps", "that helped",
                 "helped", "appreciate"),
          # "put my cat to sleep" is also a bedtime routine, so the line has to say when or how
          # it happened: "how do i put my cat to sleep at night" is a sleep question.
          ask=("died", "dies", "dead", "dying", "passed away", "death", "put down", "was put",
               "were put", "putting", "had to", "vet", "yesterday", "last week", "last night",
               "last month", "this morning", "today", "euthanised", "euthanized")),
    entry("pet-low", (("cat", "dog", "puppy", "kitten", "rabbit", "hamster", "budgie", "pet"),
                      ("down", "a bit down", "seems down", "seems a bit down", "low", "quiet",
                       "not himself", "not herself", "off colour", "moping", "mopey",
                       "withdrawn", "not right")),
          ("A quiet day is usually nothing: watch for the next twenty-four hours, and check the "
           "basics - is he eating, drinking, weeing and pooing as usual, and any limping, "
           "sickness or yelping when you touch him? A pet who is off his food for a whole day, "
           "or low and also sick, lame or drinking a lot, should see a vet rather than wait."),
          # "put down", "put to sleep" and "died" are the loss entry's lines, and a line that says
          # one of them is not asking about a quiet day. "put" alone is here because the loss key
          # cannot see "we had to put our cat down this morning" as one phrase.
          avoid=("put down", "put him down", "put her down", "put to sleep", "put him to sleep",
                 "put her to sleep", "put", "euthanised", "euthanized", "died", "dead", "dying",
                 "passed away", "death", "cremat",
                 # a pet that has stopped eating is dog-not-eating's and cat-not-eating's line
                 "stopped eating", "not eating", "wont eat", "won't eat", "isnt eating",
                 "isn't eating", "appetite", "off his food", "off her food",
                 # a pet low after losing its companion is grieving, and "a quiet day is usually
                 # nothing" is the wrong thing to say to that: the loss is the subject
                 "lost our", "we lost", "since we lost", "grieving", "grief", "passed away",
                 "missing her", "missing him", "misses her", "misses him")),

    # --- dogs ---
    # "Should I get a cat or a dog" names a cat and "get", two key words of this entry, but the
    # line is a choice between pets and a shopping list is not an answer to it.
    # A bare "cat" is not enough: "how do i get my cat to use a scratch post" names a cat and
    # "get", two key words of this entry, but it is a behaviour question and a shopping list is
    # not an answer to it. Getting or having a cat, or a new one, does ask for the list.
    # People say the animal and not the word "new": "what do i need for a cat" and "what should i
    # get for my cat" were shrugs while "what do i need for a new cat" got the list, which is the
    # same question asked more plainly. The phrases are "for a/my/the cat" rather than a bare
    # "cat", so the row is not opened to every line about one; what a cat eats, costs or needs a
    # vet for keeps its own row.
    entry("kitten-kit", (("kitten", "kittens", "new cat", "new kitten", "getting a cat",
                          "getting a kitten", "for a cat", "for cats", "for my cat",
                          "for my cats", "for the cat", "for the cats"),
                         ("need", "buy", "getting", "new", "kit", "supplies", "get",
                          "equipment", "prepare")),
          _kitten_kit, bias=1,
          # "cat or dog", "cat vs dog": a line weighing two pets is a choice, not a shopping
          # list, so the comparison is kept out as a phrase ("cat or dog", not a bare "or", which
          # is in "a bed or a blanket"); so is a problem with the cat.
          avoid=("cat or dog", "dog or cat", "cat or a dog", "dog or a cat",
                 "cat vs dog", "dog vs cat", "cat versus dog", "dog versus cat",
                 "which is better", "what is better", "either a cat", "either a dog",
                 # a name for it is the naming question, not a list of things to buy
                 "name", "named", "naming", "call it", "call him", "call her", "call them",
                 "left alone", "long hours", "work all day", "who looks after",
                 "sick", "biting", "allergic", "lost",
                 # "how do i get a cat to use a litter tray" is the training question, and
                 # "getting" made it a shopping list
                 "use the litter", "use a litter", "use its litter", "use her litter",
                 "litter train", "train the cat", "train my cat",
                 "to use the tray", "to use a tray", "wont use the litter",
                 # getting a second cat is the introduction question, not a shopping list:
                 # "how do i introduce a new kitten to my cat", "can i get a kitten with my
                 # older cat"
                 "introduce", "introducing", "second cat", "older cat", "existing cat",
                 "with my cat", "another cat", "with my older",
                 "scratching the", "scratches the", "keeps scratching",
                 # the past tense too: "my kitten scratched my new sofa" was read as a kitten
                 # shopping list because "new" matched, once the refund row stood down.
                 "scratch the", "scratched the", "scratched my", "scratched a", "scratching my",
                 # "how do i get my cat to sleep through the night" is a sleep question, not a
                 # shopping list: "getting" matched, so the night words pass here.
                 "night", "nights", "sleep", "sleeping", "wake", "wakes", "waking",
                 "meowing", "early", "settle", "cries", "crying",
                 # a cat that cannot get up the stairs, or is stiff and struggling, is a vet
                 # line: "my cat is struggling to get up the stairs" was a shopping list.
                 "struggling", "struggle", "stairs", "steps", "cant get up", "wont move",
                 "weak", "limp", "arthritis", "stiff", "incontinent", "years old", "old and",
                 # A new cat that hides is settling in, which is cat-hiding's answer: "new cat"
                 # was in this key, so the shopping list answered "my new cat hides under the bed".
                 "hides", "hiding", "hiding under", "under the bed", "under the sofa",
                 "wont come out", "won't come out", "scared", "frightened", "afraid",
                 "timid", "shy", "nervous", "settling", "settling in", "settle in",
                 # an old cat that hisses at the newcomer is the introduction question, and this
                 # shopping list answered it: "my cat is hissing at the new kitten"
                 "hiss", "hisses", "hissing", "growl", "growls", "growling", "spit", "spits",
                 "spitting", "swipe", "swipes", "swiping", "battling", "fighting", "attacking",
                 "chasing", "wont get on", "won't get on", "hates the", "bullies", "bullied",
                 # Where it will live is the cat-in-a-flat question, not a list to buy: "get a
                 # cat" and "getting a cat" already reach this key, so the flat sits on top of it.
                 "flat", "flats", "apartment", "maisonette", "indoor", "block of flats",
                 # a present for the cat is shopping.gift-for-a-pet, not a kit list
                 # "for a cat" is a phrase now, so the asks that are about something else than
                 # the kit come through it: what a cat eats, what it costs to insure, whether it
                 # needs a licence, and the trip to the vet are each their own question
                 "food", "foods", "feed", "feeding", "fed", "diet", "ate", "eat", "eating",
                 "treat", "treats", "insurance", "insure", "licence", "license", "vet",
                 "vaccination", "vaccinations", "worming", "flea",
                 # "what do i need for my cat with a cold" is the vet's question, and the cold
                 # got the kit list once "for my cat" was a key phrase
                 "cold", "flu", "sneezing", "coughing", "temperature", "not eating",
                 ) + PRESENT_ASK),

    # The one dog question where the wrong answer hurts him: people reach for their own tablets
    # without thinking. Keyed on the medicine and the animal, so "can i give my dog a bath" is out.
    entry("pet-painkillers",
          (("paracetamol", "ibuprofen", "aspirin", "painkiller", "painkillers", "calpol",
            "nurofen", "human medicine", "human medicines", "my medicine", "my tablets"),
           ("dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "give", "given", "dose",
            "safe", "ok", "hurt", "pain", "leg", "limp")
           + HUMAN_TABLET_PETS),
          ("Never give a pet human painkillers. Paracetamol and ibuprofen are both dangerous to a "
           "dog or a cat, and a single paracetamol can kill a cat; rabbits, guinea pigs, hamsters "
           "and birds are poisoned by even less, and aspirin and ibuprofen give a dog stomach "
           "ulcers and kidney damage. Pain relief comes from a vet, dosed by weight: ring them "
           "today, and say what was given, the pet's weight and how much."), bias=1,
          # The animal has to be named: "can i give my little girl paracetamol" is a parent's
          # question, and this reply would terrify them for no reason.
          # `him` and `her` were in this guard, and a pronoun is not an animal: "give him
          # calpol" in a conversation about a child with a fever was answered as a dog's dose,
          # and told a parent that their child could die from the tablet they were asking about.
          # A child is a `him` too, so the pet has to be named - by the pet word here, or by the
          # "dog"/"cat" in the key above, which every real pet line has.
          ask=("dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets",
               "pup", "my dog", "my cat") + HUMAN_TABLET_PETS),
    # --- things that poison a pet: the vet now, not a training tip -----------------
    # Each one needs a pet word in the line (ask=), so "can i eat grapes on a diet" never
    # reaches the vet answer, and "grapes" alone is not enough to open it. Grapes keep main's
    # `_grapes` entry further down (it asks how many and how long ago); this table only adds the
    # poisons main had no answer for.
    entry("dog-onion", (("onion", "onions", "garlic", "leek", "leeks", "chives", "shallot",
                         "shallots"),
                        ("dog", "dogs", "puppy", "cat", "cats", "ate", "eat", "eaten",
                         "poisonous", "toxic")),
          ("Onions, garlic, leeks and chives damage a dog's red blood cells, and cats are affected "
           "too. A small taste is usually harmless, but a whole onion or a pile of garlic needs a "
           "call to the vet today with the pet's weight."), bias=1,
          ask=("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "vet")),
    entry("dog-xylitol", (("xylitol", "sweetener", "chewing gum", "gum", "mints"),
                          ("dog", "dogs", "puppy", "ate", "eat", "eaten", "chewed")),
          ("Xylitol, the sweetener in sugar-free gum, mints and some peanut butters, makes a dog's "
           "blood sugar crash and can damage the liver. Even one piece of gum means ringing the "
           "vet now, before any symptoms."), bias=1,
          # `gum` is the word that carries "my dog ate chewing gum", and it also sits inside `gums`,
          # so a symptom line - "my dog has pale gums" - was answered with xylitol. The symptom
          # words name the other question: `gums` itself cannot go here, because the matcher reads
          # it as a form of `gum` and the real gum lines would lose the answer too.
          # `gum` is the word that carries "my dog ate chewing gum", and the matcher reads `gums`
          # as one of its forms, so a line about the mouth - "my dog has pale gums", "my dogs gums
          # are white", "should my dogs gums be pink" - was answered with xylitol. The symptom
          # words stand this answer down; `gums` itself cannot go in the list, because a form
          # match would take "my dog ate chewing gum" away with it.
          avoid=("pale", "swollen", "receding", "tartar", "bad breath", "gums look", "gums are",
                 "bleeding gums", "white", "went white", "grey gums", "gray gums", "blue gums",
                 "gums white", "red gums", "gums are red", "black gums", "gums are black",
                 "gum colour", "gum color", "colour", "color",
                 # a patch on the gum is the mouth's question too: "my dog has a black patch on
                 # his gums" was reaching this answer, so the black-patch branch never ran
                 "black", "dark", "patch", "patches", "spot on his gum", "spot on her gum",
                 # the "what should they look like" shapes, which named no colour at all
                 "gums be", "gums should", "should my dogs gums", "should my cats gums",
                 "are my dogs gums", "are my cats gums", "gums healthy", "gums normal",
                 "gums pink", "gums are pink", "look pink", "healthy gums", "normal gums"),
          ask=("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "vet")),
    entry("dog-alcohol", (("alcohol", "beer", "wine", "vodka", "whisky", "whiskey", "prosecco",
                           "liqueur", "cider"),
                          ("dog", "dogs", "puppy", "cat", "cats", "drank", "drink", "ate",
                           "eaten")),
          ("Alcohol is poisonous to dogs and cats: even a small amount of beer or wine can make a "
           "small dog very ill. Keep glasses out of reach, and ring the vet with the pet's weight "
           "and how much it drank."),
          # A person's own drink is not this question: "i drank too much wine last night" is a
          # hangover, and only a pet word in the line opens the vet answer. Naming an animal is
          # not a poison line either - "my cat is called Whisky" is a name, not a drink.
          avoid=("called", "named", "is my cat", "is my dog", "his name", "her name"),
          ask=("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "vet")),
    entry("dog-peanut-butter", (("peanut butter", "peanuts"),
                                ("treat", "safe", "give", "gave", "have", "ok", "eat", "ate")),
          ("Plain peanut butter is fine for most dogs in small amounts, but check the label for "
           "xylitol, which is poisonous to them. Keep it to a teaspoon as a treat, and skip it if "
           "the dog is overweight."),
          ask=("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "vet")),
    entry("dog-macadamia", (("macadamia", "macadamias", "macadamia nuts"),
                            ("dog", "dogs", "puppy", "pup", "ate", "eat", "eaten", "poisonous",
                             "toxic", "safe")),
          ("Macadamia nuts are poisonous to dogs: within 12 hours they can bring on weakness, "
           "wobbling, tremors and a fever. Ring your vet now, keep the packet and tell them how "
           "many he ate; most dogs recover in a day or two with support, but tremors need seeing "
           "to."), bias=1,
          ask=("dog", "dogs", "puppy", "pup", "cat", "cats", "pet", "vet")),
    entry("dog-antidepressants", (("antidepressant", "antidepressants", "ssri", "sertraline",
                                   "fluoxetine", "citalopram", "prescription"),
                                  ("dog", "dogs", "puppy", "pup", "cat", "cats", "ate", "eat",
                                   "eaten", "chewed", "tablets", "pills")),
          ("A dropped prescription is an emergency: human antidepressants are dangerous to pets "
           "even in small amounts. Ring your vet or the animal poison line now with the packet and "
           "the strength, and do not wait for symptoms - serotonin poisoning shows up as "
           "restlessness, a racing heart and tremors."), bias=1,
          ask=("dog", "dogs", "puppy", "pup", "cat", "cats", "pet", "vet")),
    # The animal words are in `ask=`, not in the key: with `cat` in the key, "our cat Lily is
    # old" and "my cat is called Lily" matched on the cat's name and got a poisoning answer.
    entry("cat-lily", (("lily", "lilies", "lily pollen", "bouquet", "flowers"),
                       ("ate", "eat", "eaten", "chewed", "poisonous", "toxic", "safe",
                        "nibbled", "pollen", "petals", "licked", "sniffed", "rubbed",
                        "touched", "vase", "water", "brought", "sent", "dangerous")),
          ("Lilies are the worst plant for cats: even the pollen on their fur can cause kidney "
           "failure, and there is no safe part of the flower. Ring the vet now, and if a cat has "
           "any on their coat, wash it off with them held away from the sink. Do not wait to see "
           "if they are sick."), bias=1,
          ask=("cat", "cats", "kitten", "pet", "vet")),
    entry("poinsettia", (("poinsettia", "poinsettias", "christmas plant", "holly", "mistletoe"),
                        ("cat", "cats", "dog", "dogs", "kitten", "puppy", "ate", "eat", "eaten",
                         "chewed", "poisonous", "toxic", "safe")),
          ("A poinsettia is only a mild irritant: the sap makes a cat or dog dribble and feel sick, "
           "and it usually settles without treatment. Rinse the mouth with water and keep the plant "
           "out of reach. Mistletoe and holly berries are the ones to ring the vet about."),
          ask=("cat", "cats", "dog", "dogs", "kitten", "puppy", "pet", "vet")),
    # A dog that will not wake up is the one line on this shelf where the answer cannot wait, and
    # it was answered with the night routine. Kept narrow: only a dog that will not rouse is this
    # entry, because "my dog is sleepy" and "my dog will not sleep" are ordinary days and nights.
    entry("pet-unresponsive", (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten",
                                "pet", "pets", "rabbit", "hamster"),
                               ("will not wake up", "wont wake up", "won't wake up",
                                "cannot wake him", "cant wake him", "can't wake him",
                                "cannot wake her", "cant wake her", "can't wake her",
                                "not waking up", "wont wake", "unresponsive", "unconscious",
                                "collapsed", "not moving", "will not move", "wont move",
                                "stopped breathing", "not breathing", "lifeless")),
          ("That is an emergency, so ring your vet now and say the animal will not wake up: most "
           "practices have an out-of-hours number for exactly this. Keep him warm and still, do "
           "not try to give him anything by mouth, and check he is breathing while you wait. If he "
           "has stopped breathing, start chest compressions and keep going until you reach the "
           "vet."),
          # a dog that is asleep, or that the person cannot wake for a walk, is not this line
          avoid=("in the night", "at night", "sleep", "sleeps", "sleeping", "settle",
                 "routine", "early", "morning", "bedtime", "tired", "meowing", "food",
                 "barking", "walk"),
          bias=1),
    # The chocolate card names the animal that ate it: see _chocolate_for above, because a cat
    # owner was told "chocolate is poisonous to dogs" and then asked for "the dog's weight" in
    # the same breath.
    # "My dog ate chocolate" is the line people write when they know the word. The same accident
    # in the words a person actually uses - "my dog ate a whole easter egg", "my dog ate a
    # brownie", "my dog ate nutella" - names no chocolate at all, so each one was answered with
    # "Noted: your dog ate a whole easter egg", which is the coldest reply there is to a dog that
    # may be poisoned. The names of the chocolate are in the key beside the word itself.
    entry("dog-chocolate", (CHOCOLATE_FOODS, ("dog", "dogs", "puppy", "pup", "cat", "cats",
                                              "ate", "eaten", "eating", "licked", "stole")),
          lambda memory, understood: _chocolate_for(_the_animal_that_ate(understood)),
          # The foods are in the key now, so the animal has to be in the line as well: "i ate a
          # whole easter egg" is somebody's Easter, not a dog that may be poisoned.
          ask=PET_ANIMAL_ASK, bias=1),
    # A dog that has taken a bone off the table is the other half of the food question: the kitchen
    # table answers what to do with the carcass, and this says what to do about the dog.
    # Only a bone that has already gone down is this question. "Can I give my dog a bone" is the
    # calm giving-a-chew answer in pet-can-eat, and a dog burying one in the garden is not eating it.
    entry("dog-ate-bone", (("bone", "bones", "carcass", "carcasses"),
                           ("swallowed", "swallow", "ate", "eaten", "chewed", "chewing",
                            "choking", "choke", "got hold of", "stole", "took", "got",
                            "grabbed", "gobbled")),
          _bone_hazard,
          # "got" is in the verb group, and it is a common enough word that the entry has to say
          # what it is not: a bone from the butcher, or a bone taken out of a joint, is shopping
          # and butchery, not a swallowed bone. The animal has to be in the line as well, or
          # "my kid ate a chicken bone" is a dog answer.
          avoid=("stock", "broth", "gravy", "recipe", "buried", "bury", "burying", "digging",
                 "dug", "garden", "butcher", "bought", "buy", "shop", "supermarket", "bones out",
                 "from the bone"), ask=PET_ANIMAL_ASK, bias=1),
    # "Is it ok to give my dog the leftovers" is a question a friend answers in a sentence, and on
    # main `e43fd80` both phrasings were the no-answer card. It is not the named-food answer either:
    # the leftovers are a mixed plate, so the reply is the yes and the four things that are never
    # in it, rather than a caution about one food.
    entry("dog-leftovers",
          # the animal is the first group on purpose: "is leftover pizza still ok to eat" has
          # the word leftovers in it too, and a person's own lunch is the keeping answer
          # a small pet is in the first group for the same reason a dog is: the plate is what the
          # line is about, and "my rabbit ate the leftovers" has no food word in it for the table.
          (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets",
            "rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs", "guineapig",
            "hamster", "hamsters", "gerbil", "gerbils", "chinchilla", "chinchillas",
            "budgie", "budgies", "parrot", "parrots", "bird", "birds"),
           ("leftover", "leftovers", "left over", "left overs", "scraps", "table scraps",
            "the remains", "off the plate", "from my plate", "the plate", "dinner scraps",
            "food scraps", "my dinner", "my lunch", "my tea", "my breakfast", "my food",
            # the bare meal words beside the phrases: a key word matches a line word, and "ate
            # some of my dinner" carries "dinner" and nothing else this row can hold on to
            "dinner", "lunch", "breakfast", "supper", "takeaway", "take-away",
            "our dinner", "our tea", "the bin", "the rubbish", "the trash", "dog food",
            "cat food", "human food", "people food")),
          _leftovers_answer,
          # a person's own leftovers, the fridge rule and the dog-bone entry are three other
          # answers: the animal and the giving have to be in the line for this one
          # the ask words include the plate by name, because "my hamster ate my dinner" carries no
          # "leftovers" at all and the meal is the mixed plate in that line
          ask=("leftover", "leftovers", "left over", "left overs", "scraps", "table scraps",
               "from my plate", "off the plate", "dinner scraps", "food scraps",
               "my dinner", "my lunch", "my tea", "my breakfast", "my food", "our dinner",
               "the bin", "the rubbish", "the trash", "dog food", "cat food", "human food",
               "people food", "dinner", "lunch", "breakfast", "supper", "takeaway", "take-away"),
          avoid=("how long", "fridge", "freezer", "reheat", "reheating", "microwave",
                 "poisoning", "my own", "human", "i eat", "is it safe to eat",
                 # a named food is the named-food answer, which knows the amount and the risk:
                 # "is it safe to give my cat tuna leftovers" is tuna, not a mixed plate
                 ) + tuple(SAFE_FOODS) + tuple(CAUTION_FOODS),
          guard=lambda understood: not _the_bin_is_the_dogs_question(understood),
          bias=2),
    # Grapes and raisins shut down a dog's kidneys, and the amount is not something to guess at, so
    # this one is a vet call even when the dog seems fine.
    entry("dog-grapes", ((("grape", "grapes", "raisin", "raisins", "sultana", "sultanas",
                           "currants") + RAISIN_FOODS),
                         ("dog", "dogs", "puppy", "pup", "cat", "cats", "pet", "pets",
                          "ate", "eaten", "eating", "swallowed", "stole", "got")),
          _grapes,
          avoid=("wine", "vine", "growing", "grow", "vineyard", "plant", "seedless",
                 # a follow-up about the dog turns "can i eat grapes on a diet" into a dog
                 # question, and a person's own diet is the answer this must not be given to
                 "diet", "calories", "calorie",
                 # A grape is not a dog's poison for the small animals: for a hamster, a rabbit,
                 # a bird or a tortoise it is sugar at worst. "Can a hamster eat grapes" told the
                 # owner to ring the vet today about a raisin that never happened, which is a
                 # shrug traded for an alarm - worse than the fruit-skin card this branch took
                 # away. The small-animal table answers each of them, so this card keeps to the
                 # two animals it is true for.
                 "rabbit", "rabbits", "bunny", "bunnies", "hamster", "hamsters", "gerbil",
                 "gerbils", "guinea pig", "guinea pigs", "guineapig", "guineapigs", "chinchilla",
                 "chinchillas", "ferret", "ferrets", "budgie", "budgies", "budgerigar",
                 "parakeet", "cockatiel", "canary", "parrot", "parrots", "bird", "birds",
                 "tortoise", "tortoises", "turtle", "turtles", "horse", "horses", "pony",
                 "ponies", "rat", "rats", "mouse", "mice"),
          ask=PET_ANIMAL_ASK, bias=1),
    # "What about the dog eating pudding" was answered with a dessert recipe, and "my dog ate the
    # christmas pudding" with "Noted". The pudding that matters is the one full of raisins, so the
    # named ones go in RAISIN_FOODS above; this entry catches the bare word and says which pudding
    # is the worry, because a rice pudding or a Yorkshire pudding is not a poison.
    entry("dog-pudding", (("pudding", "puddings"),
                          ("dog eating", "dog ate", "dog eat", "dogs eat", "dog has eaten",
                           "dog got", "dog licked", "ate the pudding", "eating pudding",
                           "eaten the pudding", "cat ate", "cat eating", "cats eat",
                           "kitten ate", "pet ate", "pet eating")),
          ("If it had raisins, currants or sultanas in it, ring your vet today and say how much "
           "went down: a Christmas pudding or a spotted dick can shut down a dog's kidneys, and "
           "no amount is known to be safe. A plain rice, Yorkshire or black pudding has none of "
           "those, so it is not poison, but it is rich - a taste only, and ring the vet if the "
           "dog is sick or dribbling."),
          avoid=("christmas", "plum", "figgy", "spotted dick", "fruit pudding", "recipe",
                 "make", "cook", "bake"),
          # The cooking pudding-ideas entry keys "what about" as well, so "what about the dog
          # eating pudding" tied with the dessert recipe and lost on registry order.
          ask=PET_ANIMAL_ASK, bias=2),
    # Raw chicken and raw meat are a bacteria question rather than a bone or a poison one.
    entry("dog-raw-meat", (("raw chicken", "raw meat", "raw fish", "raw egg", "raw eggs"),
                           ("dog", "dogs", "puppy", "pup", "cat", "cats", "pet", "pets",
                            "ate", "eaten", "eating", "swallowed", "stole", "licked")),
          _raw_meat,
          # the pet words are in the key, but "i ate raw chicken is that bad" has the same verb:
          # the animal has to be there before this is a pet question
          avoid=("cook", "cooking", "bake", "roast", "defrost", "thaw",
                 # An egg is not a joint of meat: the food table answers it with the salmonella
                 # and the cooked-is-the-treat version, and this row's campylobacter paragraph
                 # about raw chicken is the wrong answer to "can dogs eat a raw egg". Only the
                 # eating phrasings, not "egg" itself, so a raw diet question ("raw egg in dog
                 # food", "is raw egg good for dogs") keeps this row's answer.
                 "eat raw egg", "eat a raw egg", "eat raw eggs", "eats raw egg",
                 "ate raw egg", "ate a raw egg", "ate raw eggs", "having raw egg",
                 "raw egg be bad", "raw egg bad", "raw egg safe", "raw eggs bad",
                 "raw eggs safe", "raw egg ok", "raw eggs ok"),
          ask=PET_ANIMAL_ASK, bias=1),
    # "how do i teach my dog to walk nicely" names the lead without saying lead, and it was the
    # exercise table's answer ("30 minutes to an hour a day") - the ask is training, and the
    # training a dog does on a lead is this answer. The teaching words are only in the second
    # half, so a line with no lead or walking word in it is still not this entry.
    entry("dog-pulling", (("lead", "leash", "collar", "walk nicely", "walks nicely",
                           "walking nicely", "walk to heel", "to heel",
                           "walk on the lead", "walking on the lead",
                           # The pulling itself is the question, and three common ways of
                           # asking it named no lead: "how do i teach my dog to stop pulling",
                           # "why does my dog pull on walks" (the exercise table) and "my dog
                           # drags me down the street" (the sit-and-stay card, on the word
                           # "down"). The verb belongs in this half as well.
                           "pull", "pulls", "pulling", "pulled", "drag", "drags", "dragging",
                           "drags me", "pulls me", "pulls ahead", "pulling ahead"),
                          ("pull", "pulls", "pulling", "walks", "tight", "slip", "slips",
                           # "me", "ahead" and "street" are what is left once the pulling verb
                           # has moved to the other half: "drags me down the street" is one
                           # word of trouble and one word of where
                           "me", "us", "ahead", "along", "street", "stop", "stops", "stopping",
                           "keeps", "keep", "always", "why",
                           "teach", "teaches", "teaching", "train", "trains", "training",
                           "learn", "nicely",
                           "slipping", "slipped", "loose", "escape", "escapes", "escaping",
                           "comes off", "came off", "gets out", "getting out",
                           "pinch", "pinches", "pinching", "rub", "rubs", "rubbing", "chafes",
                           "chafing", "sore", "mark", "marks")),
          _dog_pulling, bias=1, guard=_on_a_lead,
          # a dog that pulls the cushions off the sofa is the chewing-and-furniture question,
          # and "keeps" would otherwise make it this one
          avoid=("sofa", "cushions", "cushion", "blanket", "bed", "furniture", "washing",
                 "table", "worktop", "bin", "rubbish", "clothes", "socks", "shoes")),
    # "dog" plus "lead" alone is not a pulling dog: it is usually someone buying a lead, or one
    # that has broken, and the training reply answered a question nobody asked. Both halves of
    # the pulling question are in dog-pulling; this entry answers the shopping one.
    entry("dog-lead-buy", (("lead", "leash"),
                           ("broken", "buy", "chewed", "chews", "best", "replace", "which")),
          ("Buy a flat webbing lead about 2m long, in one piece rather than an extending one: a "
           "metal clip, a padded handle and a width of 20 to 25mm for a medium dog. Check the "
           "stitching at both ends and the clip before you use it, and replace a chewed lead "
           "rather than tying a knot in it."), bias=1),
    # "scared" alone is not a question about people: "my dog is getting old and i'm scared" is
    # someone's own worry, and it was getting advice about a husband the dog fears. The person
    # the dog is wary of is what makes this the shy-dog question, so those words are the ask.
    # A limp, a lump, fleas and a pet drinking more than usual are the everyday health questions
    # people type as a statement, and every one of them was answered "Noted: your dog has a
    # limp." - the line echoed back with no advice in it.
    entry("pet-limp", (("limp", "limping", "limps", "lame", "lamed", "hobbling", "hobbles",
                        "won't put weight", "wont put weight", "hurting his leg", "hurting her leg"),
                       ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "rabbit",
                        "rabbits", "bunny", "guinea pig", "guinea pigs", "guinea", "hamster",
                        "hamsters", "gerbil", "gerbils", "rat", "rats", "mouse", "mice")),
          _pet_limp, bias=1),
    # A lump is something you can put a finger on, so the key word is "lump" and the answer is
    # the needle test. A bare "bump" was doing the work of a lump too, so "my dog is going blind
    # and keeps bumping into things" was told to get a needle test: a blind animal walks into
    # the furniture, it does not have a lump on it. The words that say an animal is losing its
    # sight are kept out of this row and answered by "pet-going-blind" below.
    entry("pet-lump", (("lump", "lumps", "growth", "bump", "bumps", "mass", "swelling",
                         "swollen"),
                       ("dog", "dogs", "puppy", "cat", "cats", "kitten", "rabbit", "rabbits",
                        "bunny", "pet")),
          ("Get a vet to look at it: most lumps are harmless fatty ones, but one that is firm, "
           "growing fast, or bigger than a pea is worth a needle test, and small is the cheapest "
           "time to find out. Note the date and the size - a lump on a ruler tells a vet more "
           "than a memory does."), bias=1,
          avoid=("bumping into", "bumps into", "bumped into", "bumping in to",
                 "into things", "into the furniture", "into the wall", "into the door",
                 "going blind", "gone blind", "is blind", "blind in one eye",
                 "losing his sight", "losing her sight", "losing their sight",
                 "losing its sight", "loss of sight", "cant see", "can't see",
                 "cannot see", "cloudy eyes", "eyes are cloudy", "cataracts")),
    entry("pet-fleas", (("flea", "fleas", "flea bitten", "flea dirt", "flea treatment",
                         "flea collar", "itchy", "itching"),
                        ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "house",
                         "home", "bedding", "carpet", "carpets", "sofa", "rabbit", "rid",
                         "treat", "treating", "scratch", "bites")),
          # A second entry of this name arrived in #1870 with a fuller answer in it, which meant
          # this one never ran and its own test went red on main ("the carpets vacuumed daily").
          # There is one flea answer, and it keeps the sentence that says what to do to the house
          # and the ones that say where the fleas come from and what is deadly to a cat.
          ("Fleas are not a sign of a dirty house: they come in on the animal and the eggs drop "
           "into the carpet, so the house is the part that keeps them coming back. Treat the "
           "animal and the house on the same day: a spot-on or tablet from the vet for every pet, "
           "bedding washed at 60C, and the carpets vacuumed daily for a fortnight, emptying the "
           "vacuum outside, because most of a flea infestation is eggs and pupae in the floor, "
           "not fleas on the pet. Only about one flea in twenty is on the animal at any time, "
           "which is why one treatment rarely clears it and it takes a few weeks; a pet that is "
           "still itchy a week later is a reinfestation, not a failed treatment. Never put a dog "
           "flea product on a cat - permethrin, in most dog spot-ons, is deadly to cats."),
          # a flea market and a flea circus are not fleas on a pet
          avoid=("market", "markets", "circus", "flea pit", "flea in my ear"), bias=-1),
    entry("pet-thirst", (("thirsty", "thirst", "drinking a lot", "drinks a lot", "drinking more",
                          "drinks more", "drinking loads", "always drinking", "water",
                          "drinking too much", "drinks too much", "too much water",
                          # "how much should a dog drink" names no water at all, and the amount
                          # the animal needs is the question it is asking: the animal is in the
                          # second key part, so "should i drink more water" stays out
                          "drink", "drinks", "drinking",
                          "drank too much", "drunk too much", "drank a lot",
                          "drank the whole bowl", "drank all the water", "empties the bowl",
                          # a pet that is weeing more is the same question as one that is drinking
                          # more, and it was landing on the litter-tray answer
                          "weeing more", "peeing more", "weeing a lot", "peeing a lot",
                          "wees a lot", "pees a lot", "weeing loads", "peeing loads",
                          "urinating more", "urinating a lot", "urinates", "urinating"),
                         ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten")),
          _pet_thirst, bias=1,
          # a pet that will not drink is the opposite question, with its own answer: read out of
          # this one, "my dog won't drink water" was told about sudden excessive thirst
          avoid=("wont drink", "won't drink", "not drinking", "isnt drinking", "isn't drinking",
                 "stopped drinking", "refuses to drink", "refusing to drink",
                 "hasnt drunk", "hasn't drunk", "not drunk",
                 "no water", "off his water", "off her water",
                 "touch his water", "touch her water", "touch the water",
                 "refuses water", "refused water", "refusing water", "refuses any water",
                 "will not drink", "wont drink water", "won't drink water",
                 # salt water is a poisoning question, not a thirst one
                 "sea water", "salt water", "saltwater", "seawater",
                 # "how do i get my cat to drink more" is the encourage-it question, and the
                 # measurement of how much a pet drinks is the wrong answer to it
                 "to drink", "encourage", "drink enough",
                 # where a pet drinks from is that same encouragement question, and keying the
                 # bare verb "drink" took those lines: "my cat drinks from the tap" and "my dog
                 # drinks from the toilet" are about the source, not about the amount
                 "from the tap", "the tap", "running tap", "from the sink", "the sink",
                 "from the toilet", "the toilet", "toilet", "out of the bath", "the bath",
                 "from my glass", "out of my glass", "puddle", "puddles", "water fountain",
                 "drinking fountain", "only drinks", "refill", "water bowl is empty")),
    # "how do i get my cat to drink more" got the measurement of how much a cat drinks, which is
    # the answer to the opposite question; the encouragement tips are the useful reply.
    entry("pet-drink-more",
          # Not a bare "to drink": "is it safe to drink tap water in mexico" has those words
          # and got the dog-hydration tips. The encouragement question names the pet and the
          # drinking ("get my dog to drink"), so the keys name the pair, and the "drink more" /
          # "drink enough" keys carry the rest. No key uses the bare word "get": it is also in
          # "will my dog get on with my new kitten", and a word two entries share stops counting
          # as rare, which cost the cat-and-dog introduction its answer.
          (("dog to drink", "dogs to drink", "puppy to drink", "pup to drink",
            "cat to drink", "cats to drink", "kitten to drink",
            "to drink more", "to drink enough",
            "drink more", "drinking more water", "encourage", "drink enough",
            "wont drink enough", "won't drink enough", "drinks enough",
            "hydrated", "dehydrated", "dehydration", "drinking enough"),
           # the animal has to be named: "i keep forgetting to drink water" is a person, and
           # the bare "water" in this group used to hand them the dog's bowl advice.
           ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets",
            "rabbit", "hamster")),
          _pet_drink_more, bias=1,
          # An animal has to be in the line: with the bare word "water" in the key, "am i
          # drinking enough water", "i forget to drink water" and "how do i drink more water"
          # were all read as pet questions and got "lift the skin on his back".
          ask=PET_ANIMAL_ASK,
          # a refusal, salt water and too much thirst all have their own answers
          avoid=("refuses water", "refused water", "not drinking", "isnt drinking", "hasnt drunk",
                 "stopped drinking", "sea water", "salt water", "too much", "a lot",
                 "loads", "more than usual",
                 # "is the tap water in mexico safe to drink" is a trip question: the table that
                 # says which countries' tap water is drinkable answers it, not a dog's bowl.
                 "tap water", "safe to drink", "the local water", "abroad")),
    # A dog that has drunk sea water needs the vet, and it was getting the thirst answer telling
    # its owner to measure the bowl - the salt is the danger, not the amount.
    entry("pet-salt-water",
          (("sea water", "salt water", "saltwater", "seawater", "the sea",
            "salt water from", "brine"),
           ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "drank", "drink",
            "licked", "swallowed")),
          _pet_salt_water,
          bias=4),
    # The refusal itself is a key: "my cat won't drink water" and "my dog has stopped drinking"
    # are the same worried line, and neither is a thirst question.
    entry("pet-not-drinking",
          (("wont drink", "won't drink", "not drinking", "isnt drinking", "isn't drinking",
            "stopped drinking", "refuses to drink", "refusing to drink", "wont touch water",
            "won't touch water", "not touching water", "hasnt drunk", "hasn't drunk", "not drunk",
            "off his water", "off her water", "touch his water", "touch her water", "touch the water",
            "refuses water", "refused water", "refusing water", "refuses any water",
            "will not drink"),
           # As pet-drink-more above: the pet word is the key's other half, and the bare "water"
           # is the word a person uses about their own drinking. With it here, "im not drinking
           # enough water" was told to check the dog's bowl and move it out of the sun.
           ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets",
            "rabbit", "rabbits", "bunny", "bunnies", "hamster", "hamsters", "guinea pig",
            "guinea pigs", "guinea", "gerbil", "gerbils", "rat", "rats", "mouse", "mice",
            "chinchilla", "chinchillas", "ferret", "ferrets", "degus", "hedgehog")),
          _pet_not_drinking, bias=1,
          # a cat that turns her nose up at food is the not-eating question, not this one
          avoid=("food", "foods", "eat", "eats", "eating", "ate", "meal", "meals", "kibble",
                 "biscuits", "treats", "appetite", "breakfast", "dinner", "supper", "litter")),
    # Barking at the postman is the most common complaint a dog owner has, and it was answered
    # "Noted: your dog barks at everything." - the line echoed back. The dog and the bark are
    # both keys, so a cat that meows is not this one.
    entry("dog-bark", (("dog", "dogs", "puppy", "pup"),
                       ("bark", "barks", "barking", "barker", "yaps", "howls", "howling",
                        # "my dog wont shut up" is the same question and the line says it
                        # that way far more often than it says "barks"
                        "wont shut up", "won't shut up", "shut up", "never shuts up")),
          _barking,
          # barking because nobody is there is the being-left question, not the barking one,
          # and barking at a person is the shy-dog question
          avoid=("when i leave", "when i go out", "when im out", "when i'm out", "left alone",
                 "home alone", "when we go out",
                 # the doorbell has its own answer, which is the training plan for the bell
                 "doorbell", "door bell", "knock", "knocks", "knocking", "callers", "visitors",
                 "someone at the door", "people at the door",
                 # a neighbour's dog is not the reader's dog to train: that is the noise
                 # complaint, and the two questions share every word but this one. A place
                 # ("next door", "upstairs") is not in this list: the reader's own dog can be
                 # the one barking at the dog next door, and those lines are this answer.
                 "neighbour's dog", "neighbours dog", "neighbors dog", "neighbor's dog",
                 "their dog", "somebody's dog", "someones dog",
                 # a dog barking at other dogs on a walk is a distance-and-lead question, which
                 # dog-scared-dogs answers; this row now carries the higher bias, so the lines it
                 # should not have are named here
                 "other dogs", "other dog", "strange dogs", "passing dogs", "on a walk",
                 "on walks", "on the walk", "dog on dog")
          # a person at the door is the shy-dog answer, the postman included: taking it slowly
          # and letting the dog come to them is more use than a curtain over the window
          # a barking line also reaches the door-scratching card and the wall-mark card, on
          # "the door" and on ("door", "get"); the bark is the answer they want, so this row
          # carries three
          + _PERSON_WORDS, bias=3),
    # "can i leave my cat alone all day" was answered with the hunting-collar answer, which is a
    # different question. A dog left alone has its own answer; a cat left alone is this one.
    entry("cat-alone", (("cat", "cats", "kitten", "kittens"),
                       ("alone", "leave", "leaves", "left", "weekend", "weekends",
                        "on their own", "on his own", "on her own", "on its own",
                        "by itself",
                        "empty house", "cry", "cries", "crying", "when im out", "while im out",
                        "lonely", "left all day", "left in the house", "in all day",
                        "left alone", "home alone", "overnight", "a night",
                        "two nights", "holiday", "holidays")),
          ("An adult cat is fine on her own for a working day - food, water, a clean tray and "
           "somewhere warm to sleep - and most cope with a night too. Past 24 hours she needs "
           "someone to look in daily: cats get shut in cupboards and run out of water, and a "
           "weekend away is a visitor, not a big bowl. Crying at the door is usually boredom or "
           "a change in the house, so leave a window perch, somewhere to hide and a few minutes "
           "of play when you get in."), bias=1,
          # "my cat keeps leaving mice in the hall" is what she brings home, not how long she is
          # left; the same guard the dog-alone entry has, for the same reason.
          avoid=("bird", "birds", "mouse", "mice", "rat", "rats", "rabbit", "rabbits", "squirrel",
                 "squirrels", "vole", "voles", "prey", "carcass", "bringing", "brings", "brought",
                 "caught", "catches", "catching", "killed", "dead", "presents", "by the door",
                 "on the mat", "on the step", "on the doorstep", "in the hall", "in the house"
                 # A cat that cries in pain, yelps when touched or is being sick is a cat with a
                 # body problem, and "how long can she be left" is the wrong answer to it. The
                 # crying words are in this key on purpose ("crying at the door" is boredom), so
                 # the symptom words are what stand this entry down.
                 ) + SICK_OR_HURT
                 # and a cat crying when it is stroked is the over-stimulation answer, not the
                 # leaving-alone one: "she cries when i stroke her back" was this card
                 + ("stroke", "strokes", "stroked", "stroking", "patted", "patting")
                 # a cat that cries when it is picked up is in pain, not carrying anything:
                 # "my cat carries her toy around and cries" is the other question, so only the
                 # handled-and-crying half is fenced here
                 + ("cries when i pick", "cries when i lift", "cries when i touch",
                    "cries when i stroke", "cries when i hold", "yelps when i",
                    "in pain", "in agony")),
    # "should i get a dog if i work all day" was "That's your call, not mine" and "is it fair to
    # get a dog if i work full time" a shrug. It is the first thing a would-be owner asks.
    entry("dog-work-all-day",
          (("work all day", "works all day", "working all day", "work full time",
            "working full time", "out all day", "out at work", "9 to 5", "nine to five",
            "long hours", "away all day", "work away"),
           ("dog", "dogs", "puppy", "puppies", "pup", "get a dog", "have a dog", "adopt",
            "rescue", "fit")),
          ("A normal working day is fine for an adult dog if it gets a proper walk before you go "
           "and another when you are back, and someone lets it out at lunchtime on the long days "
           "- a dog walker, a neighbour or daycare. What is not fair is a puppy, or ten hours with "
           "no break at all. Build the time alone up slowly, and an older rescue that is used to a "
           "quiet house often suits a working day better than a puppy does."), bias=1,
          # the dog you already have is the alone entry's, and a dog that barks, chews or wees
          # while you are out is a problem with an answer, not a decision about getting one
          avoid=("my dog", "my puppy", "my pup", "already", "bark", "barks", "barking", "howl",
                 "howling", "cry", "cries", "chew", "chews", "chewing", "toilet", "wee", "poo",
                 "sick", "vomit", "vet", "walk", "walks", "walking")),
    # The same ask for a cat, which main answered with a decision. Two cats are the answer more
    # often than a cat and a kitten, and the kitten is the part that does not work.
    entry("cat-work-long-hours",
          (("work all day", "works all day", "working all day", "work full time",
            "working full time", "out all day", "long hours", "9 to 5", "nine to five",
            "away all day"),
           ("cat", "cats", "kitten", "kittens", "get a cat", "have a cat")),
          ("An adult cat is fine with a working day, and two cats are often happier than one "
           "because they keep each other company while you are out. A kitten is not: it wants "
           "feeding little and often and gets into trouble on its own. Leave a clean tray, water "
           "away from the food, a window to watch and something to climb, and ask a neighbour to "
           "look in on the longest days."), bias=1,
          avoid=("my cat", "already", "wee", "wees", "poo", "litter", "sick", "vomit", "scratch",
                 "meow", "meowing", "night", "sleep", "bird", "birds", "mouse", "mice",
                 "outside", "garden", "flap"),
          # "should i get a cat when i work long hours" is that question; "my cat is out all
          # day" is the garden door
          ask=("get a cat", "have a cat", "should i", "is it fair", "can i", "should we",
               "is it ok", "kitten", "kittens")),
    # A rabbit or a hamster in a heatwave was answered with "Noted": small furries are the pets
    # that die in the heat, and the owner is asking what to do about it now.
    entry("pet-small-heat",
          (("too hot", "hot", "heat", "heatwave", "heat wave", "boiling", "scorching",
            "cool down", "keep cool", "cool", "cooler", "warm weather"),
           ("rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs", "hamster",
            "hamsters", "gerbil", "gerbils", "ferret", "ferrets", "chinchilla", "chinchillas")),
          ("Shade first: move the hutch or cage out of the sun, and give her a frozen water bottle "
           "wrapped in a towel to lie against, a cool ceramic floor tile and a heavy bowl of water "
           "as well as the bottle. Rabbits and guinea pigs cannot sweat or pant, so much over 25C "
           "is dangerous - brush out the loose fur, wet her ears with cool water, never bath her, "
           "and bring her indoors on the hottest days."), bias=1,
          avoid=("dog", "dogs", "cat", "cats", "kitten", "puppy", "oven", "cook", "cooking",
                 "food", "radiator", "house", "room", "bedroom", "baby", "child", "i am",
                 "i'm", "my room", "bath")),
    # Why to do it is a different question from when: on the deck, "why should i neuter my cat"
    # came back as the age, "whats the point of neutering" was a search hedge and "is it worth
    # neutering my dog" was the price. The case differs by animal, so the species named picks the
    # paragraph, and the timing row stands down for these words.
    entry("neuter-why", (("neuter", "neutered", "neutering", "spay", "spayed", "spaying",
                          "castrate", "castrated", "castrating", "the snip", "get done",
                          "getting done", "desexed", "sterilised", "sterilized"),
                         NEUTER_WHY_WORDS),
          _neuter_why, bias=2,
          # the price, a symptom and the recovery are other rows' questions
          avoid=("cost", "costs", "price", "prices", "how much", "cheap", "cheaper", "insurance",
                 "voucher", "recovery", "recovering", "after", "sick", "vomiting", "limp",
                 # "cone" is out: the typo reader turns "cons" into "cone", so the word vetoed
                 # every "pros and cons" line. The word is covered by "stitches" and "wound".
                 "wound", "stitches", "bleeding", "swelling", "infection",
                 # a sterilised bottle is a baby's, not a bitch's: "when should i stop sterilising
                 # bottles" was answered with the case for spaying
                 "bottle", "bottles", "teat", "teats", "dummy", "dummies", "formula",
                 "sterilising bottles", "sterilise bottles", "sterilizing bottles"),
          ask=NEUTER_WHY_WORDS + ("worth", "think", "advice", "recommend", "or not")),
    entry("pet-teeth", (("dog", "dogs", "puppy", "cat", "cats", "kitten", "pet", "pets"),
                        # The key is exactly what it was: the colour lives in the reader, and
                        # adding a dozen gum phrases here moved every other entry's rarity, so
                        # "my dog has a bad tooth" stopped reaching the toothache answer.
                        ("teeth", "tooth", "toothbrush", "breath", "tartar", "gums")),
          _pet_mouth, bias=1,
          # a tooth that hurts, wobbles or is broken is not a brushing question
          avoid=("bad tooth", "bad teeth", "broken tooth", "broke a tooth", "chipped tooth",
                 "chipped a tooth", "chip a tooth", "cracked a tooth", "cracked tooth",
                 "broke his tooth", "broke her tooth", "broke the tooth",
                 "knocked out a tooth", "tooth came out", "lost a tooth", "dental",
                 "dental problems", "dental work", "teeth problems", "tooth problems",
                 "sore mouth", "mouth problems", "gum disease", "swollen gums", "sore gums",
                 "bleeding gums", "bad gums",
                 "rotten", "abscess", "tooth is loose", "loose tooth", "wobbly tooth",
                 "tooth is broken", "toothache", "tooth hurts", "hurts to eat",
                 # breathing is not brushing: "my cat is breathing strangely" and "my dog is
                 # breathing fast after a walk" were both answered with the toothbrush. Phrases,
                 # not the bare verbs: "breathe" shares a root with the key's "breath" and would
                 # take the bad-breath answer down with it.
                 "breathing strangely", "breathing fast", "breathing heavily",
                 "breathing noisily", "breathing problems", "breathing funny", "out of breath",
                 # "loudly" was the phrasal shape missing, and it is how people say it: a
                 # bulldog that breathes loudly was told to brush his teeth. "bad breath" and
                 # "breath smells" keep the answer, since those are the mouth.
                 "breathing loudly", "breathing loud", "loud breathing", "noisy breathing",
                 "breathing loudly at night", "breathing loud at night",
                 "short of breath", "panting", "pants", "panted")),
    entry("pet-toothache", (PET_ANIMAL_ASK,
                            ("bad tooth", "bad teeth", "broken tooth", "broke a tooth",
                             "chipped tooth", "rotten tooth", "abscess", "loose tooth",
                             "wobbly tooth", "tooth is loose", "tooth is broken", "toothache",
                             "tooth hurts", "hurts to eat", "swollen face", "swollen jaw",
                             # A verb then the tooth is the same damage as the compound above:
                             # "my dog chipped a tooth" was the toothbrush answer while "broke a
                             # tooth" reached the vet, so the verb form of each is named here.
                             "chipped a tooth", "chips a tooth", "chip a tooth",
                             "cracked a tooth", "cracked tooth", "cracks a tooth",
                             "broke his tooth", "broke her tooth", "broke the tooth",
                             "knocked out a tooth", "tooth came out", "lost a tooth", "dental",
                 "dental problems", "dental work", "teeth problems", "tooth problems",
                 "sore mouth", "mouth problems", "gum disease", "swollen gums", "sore gums",
                 "bleeding gums", "bad gums",
                             # A dental word is the same question: "my rabbit has dental
                             # problems" was a human dentist, then a "Noted:" receipt, and the
                             # animal with a mouth problem is the vet's every time.
                             "dental", "dental problems", "dental problem", "dental work",
                             "teeth problems", "tooth problems", "sore mouth", "mouth problems",
                             # The gum words are named as diseases and not as "gum", which is
                             # chewing gum, and "my dog ate chewing gum" is a poison question.
                             "gum disease", "swollen gums", "sore gums", "bleeding gums",
                             "gums are bad", "bad gums")),
          ("That is a vet visit rather than a brushing one: a broken or rotten tooth hurts, and an "
           "animal with a sore mouth often just eats less and drops food. Ring the vet for an "
           "exam, soften his food or offer it soaked until he is seen, and do not pull it "
           "yourself. A swelling under "
           "the eye or a jaw that looks lopsided wants to be seen the same day, because an "
           "abscess there can spread."), bias=3),
    # "my dog has a runny eye" was the cold answer and "my dog has a sore eye" was the 20-20-20
    # screen rule, because no row named the eye at all. An eye is its own question.
    entry("pet-eye", (PET_ANIMAL_ASK, ("eye", "eyes", "runny eye", "weeping", "weepy", "discharge",
                                       "gunky", "crusty", "squinting", "squints", "red eye",
                                       "cloudy eye", "shut eye")),
          ("Bathe it with cooled boiled water on cotton wool, one wipe per eye, working from the "
           "inside corner out, and use a fresh piece each time. A clear watery eye in an otherwise "
           "happy animal often settles in a day or two; yellow or green discharge, a squint, "
           "pawing at it or a cloudy eye needs the vet today - an ulcer gets worse fast and "
           "drops made for a human eye can make it worse still."),
          ask=("eye", "eyes", "runny", "weeping", "weepy", "discharge", "gunky", "crusty",
               "squinting", "squints", "red", "cloudy", "shut"),
          # "keep an eye on the dog" is watching him, not a sore eye
          guard=not_keeping_an_eye_on_it, bias=1),
    # An animal losing its sight is mostly a house question, and it is asked as a statement
    # ("my dog is going blind") as often as a question. Every one of these lines was either the
    # search hedge or, worse, the lump answer above, because a blind animal bumps into things.
    # Sudden blindness is the one to have seen quickly: a detached retina and high blood
    # pressure in a cat are both treatable, and a cataract operation gives sight back.
    entry("pet-going-blind", (PET_ANIMAL_ASK,
                              ("going blind", "gone blind", "went blind", "has gone blind",
                               "became blind", "blind overnight", "gone blind in one",
                               "is blind", "blind in one", "losing his sight",
                               "losing her sight", "losing its sight", "losing their sight",
                               "lost his sight", "lost her sight", "lost its sight",
                               "loss of sight", "sight is going", "sight is failing",
                               "bumping into things", "bumps into things",
                               "bumping into the furniture", "bumping into walls",
                               "bumping into the wall", "bumps into the wall",
                               "walks into things", "walking into things",
                               "walks into the wall", "cant see", "can't see", "cannot see",
                               "cataracts", "cataract")),
          ("Keep the house the way they know it: the furniture where it is, the food, water, bed "
           "and litter tray in the same spot, and the same routine for walks and meals. Say their "
           "name before you touch them so they are not startled, leave a light on in the room "
           "they sleep in, and a radio on low gives them something to steer by. Sudden loss of "
           "sight needs the vet today - a detached retina, high blood pressure in a cat and "
           "glaucoma all need treating fast - while a cataract can be operated on and gives the "
           "sight back."),
          bias=2),
    # "my cats gums are pale" was the tooth-brushing answer and "my cat has white gums and wont
    # eat" was the xylitol-poisoning answer, because the bad-breath row keys a bare "gums". Pale
    # gums are the one sign that wants a vet today, so they get a row of their own, gated on the
    # gums word so an ordinary tooth line keeps its answer.
    entry("pet-gums", (PET_ANIMAL_ASK, ("pale gums", "white gums", "blue gums", "grey gums",
                                        "gray gums", "gums are pale", "gums look pale",
                                        "gums pale", "gums white", "gums are white",
                                        "gums look white", "gums turning pale",
                                        "gums turning white", "gum colour", "gum color",
                                        "gums blue", "gums are blue")),
          ("Pale, white or blue gums are an emergency, not a teeth problem: lift the lip and press "
           "the gum with a finger - the colour should come back within two seconds, and slower "
           "than that means the circulation is struggling. Pale gums go with bleeding inside, "
           "shock, a badly upset stomach or, in a cat, anaemia from fleas. Ring the vet now and go "
           "in today; keep the animal warm and quiet on the way and do not wait to see if it "
           "passes."),
          ask=("gums", "gum", "pale", "white", "blue", "grey", "gray"), bias=3),
    entry("cat-dog-intro", (("dog", "dogs", "puppy", "puppies"),
                            ("introduce", "introduction", "get on", "gets on", "meet", "met",
                             "growl", "growls", "chase", "chases", "hates", "hate", "together",
                             # "my cat and dog fight" was answered by the greeting with "A cat
                             # and a dog. Who's in charge?" - a question where the person had
                             # asked for help. The words for not getting on are the row's own,
                             # and the row still needs the cat, so two fighting dogs are not it.
                             "fight", "fights", "fighting", "fought", "scrap", "scraps",
                             "scrapping", "hiss", "hisses", "hissing", "swipe", "swipes",
                             "swiping", "dont get on", "don't get on", "not getting on")),
          ("Keep them apart behind a baby gate at first, feed each one on their own side of it so "
           "the other means food, and swap their bedding for a day so the smell is familiar "
           "before they meet. Give the cat high places to get away to and never hold them nose "
           "to nose; the cat sets the pace, and a week of slow is faster than a day of forcing "
           "it."), ask=("cat", "cats", "kitten", "kittens"), bias=2),
    # "my dog is scared of the hoover" is keyed on the thing feared, not on the fear: storms and
    # fireworks have their own answer in nature, and this is the everyday household noise a pet
    # meets indoors. Without it the line fell through to "Sorry to hear that. What would help
    # most right now?" - an offer of comfort for a question about a vacuum cleaner.
    entry("pet-noises", (_NOISY_THINGS, _FEAR_WORDS), _noise_fear, bias=1,
          # a storm is its own answer, and it is the better one for the noise: thunder and
          # fireworks are loud in a way a vacuum cleaner is not
          avoid=("thunder", "storm", "storms", "lightning", "firework", "fireworks", "bonfire",
                 "new year", "diwali", "guy fawkes",
                 # "why does my washing machine shake when it spins" is the machine's question,
                 # and "shakes when" is the very phrase that let it in: a line about the spin of
                 # an appliance is not a line about an animal, so the phrases go in rather than
                 # the words (a dog really can be frightened of the hoover going round).
                 "when it spins", "on spin", "on the spin", "spin cycle", "when it spins dry",
                 "washing machine shake", "washing machine shakes", "washer shakes",
                 "tumble dryer shake", "dishwasher shake"),
          # A key that shakes is usually the machine's own fault. Without this gate
          # "why does my washing machine shake" came out as a frightened dog, and so
          # did the tumble dryer and the dishwasher. An animal, or a phrase only a pet
          # line uses, is what makes a line this answer.
          ask=("dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens",
               "pet", "pets", "rabbit", "hamster", "guinea", "parrot", "bird", "birds",
               "horse", "pony", "pup", "kitty", "scared of", "afraid of",
               "frightened of", "terrified of", "panics at", "panics when", "hates the",
               "shakes when", "shaking when", "trembles when", "runs away from",
               "runs off when", "hides from", "hides when", "cowers")),
    # "puppy" as well as "dog": the shy dog and the barking dog entries both answer a puppy, and
    # "my puppy barks at the neighbours" was the one line of the three that fell between them.
    entry("dog-scared-men", (("dog", "puppy", "pup"), ("scared", "afraid", "frightened", "hides", "trust",
                                        "growls", "growl", "growling", "barks", "barks at",
                                        "wary", "nervous", "anxious")),
          _scared_of,
          ask=("men", "man", "husband", "partner", "strangers", "stranger", "people", "visitors",
               "visitor", "guests", "guest", "children", "kids", "child", "someone", "new people",
               "brother", "sister", "son", "daughter", "dad", "mum", "father", "mother", "grandad",
               "grandma", "friend", "friends", "neighbour", "neighbor", "postman", "boyfriend",
               "girlfriend", "baby", "babies", "toddler", "teenagers", "teenager"),
          # A neighbour's dog that barks all night is a noise complaint, not a shy dog: the
          # same two words ("dog", "neighbour") are in both questions, and the complaint shape
          # is what tells them apart. The phrase guard keeps a personal fear line.
          avoid=("stop a neighbour", "stop the neighbour", "stop my neighbour",
                 "stop a neighbor", "stop the neighbor", "stop my neighbor",
                 "all night", "every night", "keeps me awake", "cant sleep", "can't sleep",
                 "noise", "noisy", "party")),
    # "puppy" as well as "dog": the line people send is "my puppy cries when i leave him", and a
    # puppy left alone is the same question as a dog left alone
    entry("dog-alone", (("dog", "puppy", "pup"),
                        ("alone", "left alone", "home alone", "leave", "leaves",
                         # "my dog whines at night when im not there" is being left as well
                         "not there", "without me", "when im out", "when i'm out",
                         "when i am out",
                         # "my dog howls when we go out" is the leaving question, not the noise
                         "go out", "goes out", "going out", "when we go out", "went out",
                         "at work", "go to work", "goes to work", "gone to work",
                         # a long day out is being left too, and main keeps the bare "work" out
                         # of the key because a career line would match it. Bare "hours" and
                         # "all day" are long-time phrases about anything ("my dog sleeps all
                         # day", "my dog barks all day"), so the leaving idea has to be in them.
                         "while im out", "while i'm out",
                         # "all day" alone is a length of time about anything, and an earlier
                         # "all day while" arm took "my dog sleeps all day while i work" and
                         # "my dog barks all day while i work" away from the sleep and barking
                         # answers. Every arm here has to carry the leaving idea in it.
                         "all day alone", "alone all day", "home alone all day",
                         "all day on his own", "all day on her own", "all day on their own",
                         "on his own all day", "on her own all day", "on their own all day",
                         "by himself all day", "by herself all day",
                         "left all day", "left home all day",
                         "hours alone", "hours on his own", "hours on her own",
                         "hours on their own")),
          ("Four hours at a time is the usual comfortable limit for an adult dog, and puppies much "
           "less. Build it up in short chunks, leave something to chew and a radio on, and a "
           "dog-walker or a neighbour for longer days."), bias=1,
          # "leaving them by the door" is what a dog does with its catch, not how long it is left
          avoid=("bird", "birds", "mouse", "mice", "rat", "rats", "rabbit", "rabbits", "squirrel",
                 "squirrels", "pheasant", "vole", "voles", "prey", "carcass", "bringing",
                 "brings", "brought", "caught", "catches", "catching", "killed", "dead",
                 "presents", "by the door", "on the mat",
                 # a dog that went missing is not a dog left at home: "we lost the dog at the park
                 # for an hour" was getting the four-hour answer
                 "lost", "lose", "missing", "ran off", "escaped", "got out", "found", "park",
                 "stolen", "ran away",
                 # "my mate says rescue dogs are hard work" is a remark about someone else's
                 # opinion, not a question about leaving the dog
                 "says", "said", "thinks", "reckon", "apparently",
                 # four hours at home is this card; four hours in a car is a different and
                 # dangerous answer, so every car word stands this one down
                 "car", "cars", "van", "boot", "parked", "car park", "in the car",
                 "in a car", "windows down",
                 # a dog in pain or being sick is the same body problem as the cat's, and the
                 # four-hour answer is not the answer to it
                 ) + SICK_OR_HURT),
    # A dog left in a car is the commonest hot-weather question there is, and main answered it
    # "Four hours at a time is the usual comfortable limit" - the leaving-him-at-home card, which
    # is a dangerous thing to say about a car. The heat card has the right sentence but only
    # answers when a heat word is in the line, and "can i leave the dog in the car" has none.
    entry("dog-in-the-car", (("dog", "dogs", "puppy", "pup", "puppies", "pet", "pets",
                              "cat", "cats", "kitten", "kittens"),
                             ("in the car", "in a car", "parked car", "car", "cars", "van",
                              "boot", "car park", "outside the shop", "while i shop",
                              "while we shop", "windows down", "window down")),
          _dog_in_a_car,
          bias=1,
          # a car journey, a car-sick dog and a dog that barks at cars are other cards, and the
          # line has to be about the dog being left rather than a car that needs fixing
          avoid=("journey", "journeys", "travel", "travelling", "traveling", "drive", "driving",
                 "ride", "rides", "car sick", "carsick", "sick", "sickness", "vomit", "vomits",
                 "scared", "scary", "afraid", "frightened", "terrified", "nervous", "anxious",
                 "bark", "barks", "barking", "chase", "chases", "chasing",
                 "windscreen", "windshield", "demist", "demisted", "misted", "condensation",
                 "engine", "coolant", "radiator", "mot", "tyre",
                 "tyres", "brake", "brakes", "gearbox", "clutch", "battery", "insurance",
                 "parking ticket", "parking permit", "clean the car", "wash the car")),
    entry("dog-chewing", (("puppy", "dog"), ("chew", "chewing", "biting", "destroys", "bites",
                                             "bit")),
          _dog_chewing,
          # "a bit down" is the same letters as "bit down": a low dog was getting chewing advice.
          # "bit me" is a bite on a person, which the bite-wound entries answer, so the word "bit"
          # in this key must not take it: the object after the verb tells the two apart.
          # A dog biting at his own paws is an itch, not puppy teeth, so the paws are another
          # answer: #2288 asked for that, and the bite-on-a-person words above stay.
          avoid=("a bit", "bit down", "a little down", "seems down", "feeling down", "fed up",
                 "bit me", "bit my", "bit him", "bit her", "bit them", "bit a person",
                 "bit someone", "bit the child", "bit the kids",
                 "licking", "lick", "himself", "herself", "itchy", "itching", "fleas", "raw",
                 # what to do about a bite that has landed is the wound's question, and this row
                 # carries "biting" and "bite", so "dog bite first aid" was asked for the first
                 # aid and told why a dog chews
                 "first aid", "washed", "washing", "bleeding", "bled", "infected", "infection",
                 "tetanus", "plaster", "puncture",
                 # "a dog bite" with an article in front of it is the wound as a noun, not this
                 # dog biting: "what should i do for a dog bite" and "is there anything i should
                 # put on a dog bite" were answered with the training plan.
                 "a dog bite", "a cat bite", "a puppy bite", "the dog bite")),
    # A dog that has bitten a person is not a teething question. The chewing row above carries
    # "bites" and "biting", so every line about a bite on a person landed on it; the wound itself
    # is the safety module's (it wants a body part or a child, and "bit the postman" never
    # reached it). This row is the other half: what the owner does about the dog.
    entry("dog-bite-person", (("dog", "puppy", "pup", "staffie", "terrier", "alsatian",
                               "labrador", "collie", "spaniel"),
                              # "snapped at" is not a bite: a dog that snaps at a visitor is the
                              # reactivity answer, and telling them to ring 101 would be wrong.
                              ("bit", "bite", "bites", "bitten", "biting", "mauled", "nipped")),
          _dog_bite_person,
          bias=2,
          # A person, or the act of stopping it, is what makes this the owner's question: "my dog
          # keeps biting me" and "how do i stop my dog biting" both used to go to the safety
          # module's 999 card, which is right for a dog at someone now and wrong for a habit.
          ask=("someone", "somebody", "person", "postman", "postwoman", "post", "delivery",
               "courier", "neighbour", "neighbors", "neighbour's", "visitor", "stranger", "man",
               "woman", "child", "kid", "boy", "girl", "people", "passer", "paperboy",
               "window cleaner", "vet", "groomer", "customer",
               "me", "us", "our", "my hand", "my arm", "my leg", "my face", "my fingers",
               "my ankle", "my ankles", "my feet", "my foot", "my trousers", "my sleeve",
               "baby", "toddler", "husband", "wife", "partner", "son", "daughter", "family",
               "everyone", "anyone", "guests", "guest", "stop", "stopping", "biting", "bites"),
          avoid=("chew", "chews", "chewing", "chew toy", "teeth", "teething", "mouthing",
                 # "bit" is also the noun of an amount: "my dog seems a bit down since we lost
                 # our other dog" was answered with the training plan for a biter, and "a bit of
                 # chicken is fine for the dog" with it too. The phrases are what carry the
                 # noun, so a line with one of them and no other bite word is not this row;
                 # a real bite is left alone - "my dog bit my hand a bit" still says "bit my".
                 "a bit", "quite a bit", "a little bit", "bit of", "bits of", "bit more",
                 "bit less", "bit longer",
                 "stay", "lead", "recall", "furniture", "sofa", "shoe", "shoes", "slipper",
                 # a dog the person does not own is the dangerous-neighbour-dog letter, and the
                 # advice here is written for the owner
                 "my neighbour", "my neighbors dog", "my neighbours dog", "the neighbours dog",
                 "next door", "their dog", "someone elses dog", "someone else's dog",
                 "somebody elses dog", "a dog on the field", "dog on the street",
                 "slippers", "cushion", "toy", "toys", "blanket", "garden hose",
                 # how to train a dog out of it is the training row's answer: it has the lure and
                 # the clicker, which is better than telling them to book a behaviourist.
                 "train", "training", "trained", "teach", "lure", "clicker", "trick",
                 "puppy class", "puppy classes", "obedience",
                 # a puppy that mouths is teething, and dog-chewing is the row for that: it
                 # already says yelp, turn away and swap in a chew toy.
                 "puppy", "pup", "puppies", "pups", "kitten",
                 # A question about what to do with the bite is the wound's: "dog bite first aid"
                 # reached this row on "dog" and "bite" once the habit words were in place, and
                 # was answered with the training plan ("stop the biting by changing what happens
                 # before it") for a bite that has already landed. The after-the-bite words stand
                 # the habit row down, and "how do i stop my dog biting" still keeps it.
                 "first aid", "wash", "washed", "washing", "clean", "cleaned", "clean it",
                 "bleeding", "bled", "infected", "infection", "tetanus", "plaster",
                 "puncture", "broken the skin", "broke the skin", "swollen", "stitches",
                 # the wound said as a noun stands the owner's row down as well
                 "a dog bite", "a cat bite", "a puppy bite", "the dog bite")),
    entry("pet-wound", (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "rabbit",
                         "guinea", "hamster", "pet"),
                        PET_WOUND),
          _pet_wound, bias=2,
          # a dog that is lame already has its own answer, and a limp is not a wound. The
          # furniture words are the cat-scratching row's: a scratched sofa is not a scratch.
          avoid=("limping", "limp", "lame", "lameness", "stiff", "arthritis", "hip",
                 # a dog that keeps licking at a paw is a habit question, not a cut to bathe
                 "keeps licking", "licking his", "licking her", "licking its", "licking the",
                 "licking at", "licking paws", "licking paw", "always licking",
                 "won't stop licking", "wont stop licking",
                 "won't walk", "wont walk", "dragging",
                 "sofa", "couch", "settee", "furniture", "chair", "curtains", "carpet",
                 "door", "walls", "wall", "scratching post", "scratch post", "post",
                 "nails", "nail", "claws", "claw", "clip", "clipping", "trim", "trimming",
                 "groomer", "grooming", "clippers",
                 # "glass" is in the ask because a cut from broken glass is a wound, and it is
                 # what took "my cat keeps knocking glasses off the table": the reader's cat is
                 # not cut, it is being a cat. The knocking shapes are the behaviour row's.
                 "knock", "knocks", "knocking", "knocked", "pushes", "pushing", "swipes",
                 "swiping", "off the table", "off the shelf", "off the worktop",
                 "off the counter", "off the side", "off my desk",
                 # a dog that only licks or chews at his paw has no wound to bathe, and the
                 # paw-licking answer is the one that says what it usually is
                 "lick", "licks", "licking", "licked", "chew", "chews", "chewing",
                 "gnaw", "gnawing", "nibble", "nibbling", "paws a lot",
                 # teeth on his own paws is the itchy-paw answer, and a wound phrase such as
                 # "a bite wound" keeps this entry: only the teeth-on-paws shapes step aside
                 "biting his paws", "biting her paws", "biting at his paws", "biting at her paws",
                 "bites his paws", "bites her paws", "chewing his paws", "chewing her paws",
                 # "how do i clean my dogs paws" is the washing answer: a paw named in the line
                 # is not a wound, and this entry holds "paws" in its key, so it says so
                 "clean", "cleaning", "wash", "washing", "wipe", "wiping", "muddy", "dirty",
                 # a nose turned up at a bowl is a refusal to eat, not a cut: "my dog turned his
                 # nose up at his dinner" was bathed by this row. The not-eating rows read these
                 # phrases, so the wound stands down and leaves them the line.
                 "nose up", "turned his nose", "turned her nose", "turned its nose",
                 "turns his nose", "turns her nose", "turning his nose", "turning her nose",
                 "off his food", "off her food", "off his dinner", "off her dinner",
                 "off his tea", "off her tea", "gone off his food", "gone off her food",
                 "appetite", "not eating", "wont eat", "won't eat", "stopped eating"),
          ask=("paw", "paws", "pad", "pads", "nose", "leg", "foot", "tail", "skin",
               "belly", "cut", "gash", "wound", "bleeding", "bleeds", "thorn",
               "glass", "splinter")),
    # A bottom dragged along the carpet was the toilet-training basics, which is advice for a
    # different problem: a dog that scoots is usually full of anal glands, and the answer says so
    # and says when it is a vet visit rather than a wait.
    entry("dog-scooting",
          (("dog", "dogs", "puppy", "pup", "puppies", "bitch", "doggy"),
           ("scoot", "scoots", "scooting", "scooted",
            "drag his bum", "drags his bum", "dragging his bum", "drag her bum",
            "drags her bum", "dragging her bum", "drag its bum", "bum on the carpet",
            "bottom on the carpet", "bum along the floor", "bottom along the floor",
            "rubs his bum", "rubbing his bum", "rubs her bum", "rubbing her bum",
            "itchy bum", "sore bum", "bum on the floor", "bottom on the floor",
            "wipes his bum", "wiping his bum", "drag his bottom", "drags his bottom")),
          ("A dog scooting along the floor is usually the anal glands: a vet or a groomer empties "
           "them in a minute, so book it this week. Go sooner if he is licking or biting at the "
           "area, if there is a swelling beside the anus or blood on the carpet, because an "
           "infected gland needs treating rather than emptying. Worms and a mucky back end do it "
           "too, so worm him if that is overdue, and if it keeps coming back ask the vet about "
           "adding a little fibre - a spoon of bran or tinned pumpkin - to firm the stool up."),
          bias=1),

    # A dog whose back end has gone is the one thing here that cannot wait for an appointment.
    # Main answered "my dog is dragging his back legs" with a hem-stitching card and "my dog cant
    # use his back legs" with "Got it. Is there anything you'd like a hand with?".
    entry("dog-back-legs",
          (("dog", "dogs", "puppy", "pup", "puppies", "bitch", "doggy", "dachshund"),
           ("dragging his back legs", "dragging her back legs", "dragging its back legs",
            "drag his back legs", "drags his back legs", "drag her back legs",
            "dragging a back leg", "dragging one back leg", "dragging his legs",
            "dragging her legs", "dragging his hind legs", "dragging her hind legs",
            "knuckling", "knuckling over", "knuckles over", "knuckling his paw",
            "cant use his back legs", "can't use his back legs", "cannot use his back legs",
            "cant use her back legs", "can't use her back legs", "wont use his back legs",
            "wont use her back legs", "back legs have gone", "back legs gone", "legs have gone",
            "wobbly back end", "back end has gone", "back end gone", "weak in the back end",
            "back end is wobbly", "back end wobbly", "back end is weak", "weak back end",
            "wobbly on his back legs", "wobbly on her back legs", "wobbly in the back",
            "cant stand up", "cannot stand up", "cant get up", "slipped disc", "ivdd",
            "paralysed", "paralyzed", "paralysis")),
          ("That needs a vet today, not an appointment next week: a dog who drags a back leg, "
           "knuckles over on a paw or suddenly cannot use his back end usually has a slipped "
           "disc, and the sooner it is seen the better the chance he walks again. Carry him - a "
           "towel under the belly if he is heavy - keep him still and warm, and ring the vet on "
           "the way rather than waiting at home to see if it improves. Do not give him anything "
           "from the medicine cupboard: ibuprofen and paracetamol are both poisonous to dogs. If "
           "it came on after a jump, a fall or a long walk, say so when you ring."),
          bias=2),

    # The first things anyone teaches a dog, and main answered none of them. Kept apart from the
    # problem entries above (pulling, chewing, toilet) because "how do i teach him to sit" is a
    # request for the method, not a complaint.
    entry("dog-sit", (("dog", "puppy", "pup"),
                      ("sit", "sits", "stay", "down", "lie down", "training", "train",
                       "obedience", "puppy class")),
          ("Lure him into it and name it once: a treat just above his nose moved back over his "
           "head drops his bottom into a sit, so say 'sit' the moment it lands and give the treat. "
           "The same hand carries on down to the floor for 'down', and a flat palm held up for "
           "'stay', one step at a time. Three or four goes, several times a day, and stop while he "
           "is still enjoying it; never push his bottom down, let him work it out."), bias=1,
          # "down" is what a sit order is called, and also how a low dog is described: "my dog
          # seems a bit down" is not a training question.
          avoid=("a bit down", "a little down", "bit down", "seems down", "feeling down",
                 "fed up", "is down", "been down", "low",
                 # "where can the dog stay while we are on holiday" is where the dog boards, and
                 # "stay" in the key above is the command: once the trip abroad row stopped
                 # answering the word "holiday" (#7798), the standing question about a holiday
                 # landed here and was answered with a treat over the nose. Every going-away
                 # shape is the `pet-holiday` row's, and "how do i teach my dog to stay" has
                 # none of them, so the command keeps this answer.
                 "holiday", "holidays", "on holiday", "holiday let", "going away", "go away",
                 "while we are away", "while we're away", "while im away", "while i'm away",
                 "while i am away", "when we go away", "when im away", "when i'm away",
                 "kennel", "kennels", "cattery", "boarding", "dog sitter", "cat sitter",
                 "pet sitter", "abroad", "away for a week",
                 # "how do i train a puppy not to bite" is the biting question, and the word
                 # "train" was enough to send it to the sit-and-stay answer. Each of these has
                 # its own row: mouthing, chewing, jumping up, pulling, recall, toilet.
                 "bite", "bites", "biting", "bit", "chew", "chews", "chewing", "nip", "nips",
                 "nipping", "mouthing", "jump", "jumps", "jumping", "jumped", "pull", "pulls",
                 "pulling", "lead", "leash", "bark", "barks", "barking", "toilet", "wee",
                 "wees", "poo", "poos", "house training", "house-trained", "come when called",
                 "recall", "go to the toilet", "go to the loo", "toilet training",
                 "go outside", "go out", "goes outside")),
    entry("dog-recall", (("dog", "puppy", "pup"),
                         ("recall", "come back", "comes back", "coming back", "wont come",
                          "wont return", "runs off", "chase",
                          # "teach my dog to come when called" and "how do i get him to come to
                          # me" are the same question, and neither said "come back"
                          "come when called", "come when i call", "come to me", "come here",
                          "call him", "call her", "comes to me", "coming to me", "when called",
                          # not bare "called": "i have 2 kids n a dog called rex" is not a
                          # recall question, and neither is "whats my dog called"
                          "call him back", "call her back", "called back")),
          _dog_recall, bias=1),
    entry("dog-jumping", (("dog", "puppy", "pup"),
                          ("jump", "jumps", "jumping", "jumped", "on people", "at people",
                           "greets", "greeting")),
          ("Turn away and fold your arms the moment he jumps, then greet him calmly when all four "
           "paws are down: jumping up is how a dog says hello, so attention is the reward that "
           "keeps it going. Ask visitors to do the same, and reward sitting instead."), bias=1),
    # A dog that gets out is the boundary first and the training second: recall does not stop a
    # dog leaving, and the sweeps had this family of lines spread over four cards that were all
    # about something else - "how do i stop my dog escaping the garden" got which breed suits a
    # flat, "my dog keeps getting out the front door" got a scuff off a painted wall, "my dog bolts
    # when the door opens" got the slow-feeder bowl (through "bolts"), "my dog jumps the fence" got
    # jumping up at visitors and "my dog digs under the fence" got how to set a fence post.
    # Keyed on the animal plus the way out, so every phrasing of it lands here.
    entry("dog-gets-out", (("dog", "dogs", "puppy", "pup", "labrador", "terrier", "collie",
                            "spaniel", "retriever", "greyhound", "whippet", "beagle", "staffie",
                            "poodle", "jack russell"),
                           ("escaping", "escape", "escapes", "escaped", "got out", "gets out",
                            "getting out", "keeps getting out", "gets loose",
                            "got loose", "gets away", "got away",
                            # not bare "runs off": a dog that runs off in the park is the recall
                            # card, and that one is about practice rather than a boundary
                            "bolts when", "bolts out", "bolts through",
                            "bolts past", "jumps the fence", "jumping the fence",
                            "over the fence", "under the fence", "climbs", "climbing",
                            "digs under", "digging under",
                            # not bare "slips out": "my dog can slip out of his collar" is the
                            # collar-fit card, and that one is the answer to a dog on a lead
                            "slips out the door", "slips out the gate", "slips out when",
                            "slips past", "the gate", "the front door",
                            "out the door", "out of the door", "out of the garden",
                            "out of the gate", "squeezes through", "wriggles through",
                            # how high the fence has to be, and the gate a dog can work out
                            # for itself, are the same boundary question
                            "fence", "fences", "gate", "gates", "fence height", "how high",
                            "what height", "garden wall", "over the wall", "opens the gate",
                            "opens the garden gate", "can open", "latch",
                            "keep my dog in", "keep him in", "keep her in")),
          ("Fix the boundary before the training, because recall never stops a dog getting out. "
           "Walk the fence line: 1.2m holds most dogs and 1.8m a jumper, nothing against it to "
           "climb, and a gap under a gate is wide enough if his head goes through. Set the mesh "
           "30cm into the ground or run a line of slabs along the base so he cannot dig out. Keep "
           "him out of the hall while the front door is open, or put a stair gate across it. Then "
           "microchip and a tag with your number, and a long line for recall practice."),
          # a dog that bolts its food, jumps at people, digs a bed or is bought for a flat is a
          # different question, and the animal's health is the vet's
          avoid=("eat", "eats", "eating", "ate", "food", "bowl", "gulp", "gulps", "gulping",
                 "chew", "chews", "chewing", "jump up", "jumps up", "jumping up", "on people",
                 "at people", "greets", "greeting", "digs the bed", "digging the bed",
                 "digs a hole", "digging a hole", "dig the bed",
                 "flat", "flats", "apartment", "breed", "breeds", "which dog", "what breed",
                 # a dog that backs out of its collar or harness is the fit card, on the lead
                 "collar", "collars", "harness", "lead", "leash", "walks", "on the sofa",
                 "on the bed", "on the couch",
                 # mud on the floor is a cleaning question, and "muddy paws" says so
                 "muddy", "mud", "paws", "paw", "floor", "carpet", "marks", "scuffs",
                 "cat", "cats", "kitten", "rabbit", "horse", "vet", "sick", "vomit", "limp",
                 "bark", "barks", "barking", "toilet", "wee", "poo", "housetrain",
                 "come when called", "recall"),
          bias=1),
    # The table is where begging is taught, so the answer is about the table and not the food:
    # "how do i stop my dog begging" was a shrug ("that's beyond what I know well, sorry").
    # A frightened pet whose fear has no name in the line yet: "my dog is scared and hides under
    # the table" stood down from the begging row and landed on the readers for a person's own
    # feelings, so the reply was about the owner's day. The named fears - a noise, one person,
    # another animal, the vet, the car - keep their own answers below.
    entry("pet-fear-unnamed", (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten",
                                 "kittens"),
                                ("scared", "frightened", "afraid", "nervous", "anxious",
                                 "terrified", "spooked", "shaking", "trembling", "cowering",
                                 "hides", "hiding", "hidden")),
          ("Give him somewhere he can get to that nobody reaches into - a covered crate, or the "
           "gap behind the sofa - and do not pull him out of it: a pet allowed to hide comes out "
           "sooner. Crouch down and turn side-on rather than leaning over him, talk quietly, and "
           "let him come to you; that is weeks of small steps rather than one good day. If it "
           "came on suddenly in an older animal, or he growls when he is cornered, have the vet "
           "look at him - pain and failing eyesight turn calm pets fearful."),
          # a fear of one noise, of one person, of another animal, and of the car each have a
          # better answer of their own, so this one keeps to the fears with nothing named
          avoid=_NOISY_THINGS + ("thunder", "storm", "storms", "lightning", "firework",
                                "fireworks", "bonfire", "men", "man", "husband", "wife",
                                "partner", "stranger", "strangers", "people", "visitors",
                                "visitor", "guests", "guest", "children", "kids", "child",
                                "neighbour", "neighbor", "postman", "baby", "toddler",
                                "vet", "car", "walk", "walks",
                                # hiding a toy is play, and a cat that hides all day has its own
                                # settling-in answer (the quiet room, the litter tray, no pulling
                                # her out): this one is for a fear nobody has named
                                "toy", "toys", "ball", "bone", "bones", "treats", "plays",
                                "playing", "all day", "first few days", "new home",
                                "settling in", "just got him", "just got her")),
    entry("dog-begging", (("dog", "dogs", "puppy", "pup"),
                          ("beg", "begs", "begging", "at the table", "from the table",
                           "under the table", "while we eat", "while i eat", "when we eat",
                           "when i eat")),
          ("Feed him before you sit down and give him something to do - a chew on his bed in "
           "another room, or a stuffed toy - so your meal is not the interesting part of his "
           "evening. Never hand food over from the table, and get everyone in the house to hold "
           "the same line: a dog given a scrap once will try every single meal."), bias=1,
          # what he eats, how much, and what is poisonous are their own questions: this one is
          # only the begging itself
          avoid=("how much", "what should i feed", "weight", "fat", "chocolate", "grapes",
                 "poison", "onion", "raw", "kibble", "cat", "cat food", "bin",
                 # the counter is where he helps himself, not where he begs
                 "counter", "worktop", "steals", "steal", "helping himself",
                 # under the table is where a frightened or a sleeping dog goes too, and that is
                 # a fear question ("he's scared of men and hides under the table") or a rest
                 # one, not begging: the food sense needs one of the begging words above.
                 "hide", "hides", "hiding", "hidden", "scared", "scary", "afraid", "fear",
                 "frightened", "nervous", "anxious", "shaking", "trembling", "cowering",
                 "growl", "snap", "sleeps", "sleeping", "asleep", "sleep", "resting",
                 "raining", "thunder", "fireworks", "storms", "noise",
                 # the fear itself, in the words people use for it, and never the occasion:
                 # "when visitors" and "when people come" were in this list for one round and
                 # they cost the begging lines themselves ("my dog begs when visitors come" fell
                 # to the doorbell answer)
                 "terrified", "shy", "cowers")),
    # Cheese and milk are the second half of "can he eat this", and they are not poison, so they
    # keep their own answer: a kitten asked about milk should not get the grapes warning. The
    # dairy do not all answer the same way - cheese is fine in small pieces and milk is not - and
    # one text for the family opened with the milk, so "can i give my dog cheese" was answered
    # with a paragraph about cows' milk before it said the one thing that was asked.
    entry("pet-dairy", (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "kittens"),
                        ("milk", "cream", "dairy", "lactose", "yoghurt", "yogurt")),
          _pet_dairy,
          # "can dogs eat cheese" and "can dogs eat ice cream" named a dairy word and got the
          # kitten-milk card, which is about milk: cheese has its own sentence in the named-food
          # table, and ice cream's hazards are the dairy and the sugar, not the lactose alone
          avoid=("cheese", "ice cream"),
          bias=1),
    # A puppy is asked about with the same words as a dog - "how long should i walk my puppy" is
    # the commonest way people put it - and the rule for a puppy is a different one, so it is in
    # the keys and in the answer rather than left to "your vet is the one to ask".
    entry("dog-walks", (("dog", "dogs", "puppy", "pup"),
                        ("how much exercise", "how long walk", "how long should i walk",
                         # "how far should i walk my puppy" tied at four with the travel and
                         # expenses entries until the distance question was a phrase of its own
                         "how far", "how far should i walk", "how far can i walk",
                         "walks", "walk", "walking", "exercise",
                         # "is it ok to run with my dog" asked nothing on main but the exercise
                         # word, and the key held the walking words only: the running words are
                         # the same question, so they belong in the same place
                         "run", "runs", "running", "jog", "jogging", "can i run", "run with",
                         "running with", "canicross", "cycle", "cycling", "bike", "biking")),
          ("Most adult dogs need 30 minutes to an hour a day, and a working breed rather more. A "
           "puppy is the other way round: about five minutes of walking for every month of age, "
           "twice a day, so a four-month-old gets two twenty-minute walks and no long hikes or "
           "stair runs until the growth plates close at a year. Flat-faced breeds and older dogs "
           "need less and overheat easily, so go by the dog rather than the breed chart. Running "
           "or cycling with a dog is the same rule at speed: wait until he is a year old, start "
           "with a mile and add a little each week, keep it on soft ground, and skip it on warm "
           "days, because a dog on hot tarmac is burnt pads and heat stroke."),
          # a dog that eats everything on a walk is not a how-far question: that is dog-scavenge
          avoid=("eat", "eats", "eating", "eats everything", "eats things", "eat things",
                 "eat everything", "scavenge", "scavenging", "picks up", "picking up",
                 "picks things", "rubbish", "pavement", "garbage", "bin", "fast", "gulps",
                 # walking in the heat is its own question, and the generic rule is wrong advice
                 # for it: "how long do i walk my dog in the heat" takes dog-walks on main
                 "in the heat", "when its hot", "hot", "heatwave",
                 # the same question in the words people actually type: "should i run with my dog
                 # in this heat" is a heat question, and the distance answer even says so
                 "in this heat", "this heat", "in the sun", "hot weather", "hot day", "hot days",
                 "when it is hot", "when it's hot", "boiling", "scorching", "heat",
                 # a dog that runs off, runs at another dog or runs to the door is a recall or a
                 # behaviour question, and the running words above would take those lines
                 "runs off", "running off", "runs away", "running away", "runs at",
                 "escapes", "escaped", "bolts", "bolted", "chases", "chasing", "recall",
                 "runs to the door", "runs out", "runs in the road", "in the road")),
    # A cat that bites or nips a hand is a play and over-handling question, and the garden row
    # --- a cat and the children in the house -------------------------------------
    # "is my cat safe with the kids" was a shrug and "is a cat ok with a 2 year old" was the
    # vaccination answer, while "how do i stop my cat biting the kids" is the biting row's (its
    # ask keeps it). A household with a child in it is a question with its own answer: the baby
    # myth, the rule that matters, and the cat's own need for a way out.
    entry("cat-and-children", (("cat", "cats", "kitten", "kittens"),
                               ("kids", "kid", "child", "children", "toddler", "baby",
                                "newborn", "my son", "my daughter", "grandchild",
                                "grandchildren", "grandson", "granddaughter", "a 2 year old",
                                "a 3 year old", "a 4 year old", "two year old",
                                "three year old", "family")),
          _cat_and_children,
          # the behaviour rows own a cat that will not stop, and an introduction is its own answer
          avoid=("bite", "bites", "biting", "bit", "bitten", "nip", "nips", "nipping",
                 "attack", "attacks", "attacking", "stop", "stops", "keeps", "keep",
                 "introduce", "introduction", "litter", "tray", "claws", "fleas", "worming",
                 # a woman expecting a baby is asking about the litter tray and toxoplasmosis,
                 # and cat-and-baby answers that; the house rules are for the child already here
                 "pregnant", "pregnancy", "expecting", "due in",
                 "vaccination", "vaccinations", "neutered", "scratching post"),
          # A question or a concern is the gate, not the bare household: "i have 2 kids and a
          # cat" is a person describing their home, and it stays a note back.
          ask=("safe", "ok", "okay", "good", "fine", "will", "would", "smother", "leave",
               "alone", "worry", "worried", "risk", "having a baby", "new baby", "expecting",
               "newborn", "toddler", "and a cat", "with a cat", "have a cat"),
          bias=2),
    # used to take it: "how do i stop my cat biting" keyed on cat + stop and got the flowerbed
    # answer. The garden row now lists bite/biting in its avoid, and this is the cat's own.
    entry("cat-biting", (("cat", "cats", "kitten", "kittens"),
                         ("bite", "bites", "biting", "bit", "bit me", "bitten", "nip",
                            "nips", "nipping", "nips me", "scratch me", "attacks my hand",
                            "attacks my feet", "play biting",
                            # Phrases, because the rarity rule reads a bare "bite" family word
                            # as an ordinary word once four keys hold one - and a kitten that
                            # "keeps biting my hands" is then only a carried word from the line
                            # before, so the follow-up stopped reaching this answer.
                            "bites my hand", "bites my hands", "biting my hands", "bit my hand",
                            "bit my hands", "bites my fingers", "chews my hands",
                            # a cat that hisses, growls, swipes or lunges has not bitten yet,
                            # and it is the same warning the answer is about: "my cat hisses at
                            # me" was only noted back to the person and "my cat growls when i
                            # pick her up" was a shrug.
                            "hiss", "hisses", "hissing", "growl", "growls", "growling",
                            "aggressive", "aggression", "went for", "goes for", "go for",
                            "bites and scratches",
                            # "how do i get my cat to stop biting the kids" was reaching the
                            # child-hitting row: a person the cat bites names the person
                            "kids", "kid", "child", "children", "toddler", "baby", "grandson",
                            "granddaughter", "my son", "my daughter")),
          _cat_biting,
          # the sofa, the flowerbed and the litter tray have their own answers, and so is a line
          # about stroking: "my cat hisses at me" then "she only does it when i stroke her" was
          # through this row and got the play answer, when the stroking answer belongs to
          # cat-overstimulated
          avoid=("sofa", "couch", "furniture", "garden", "flowerbed", "lawn", "scratching post",
                 "litter", "tray", "spray", "hiss at the vet", "carrier",
                 "stroke", "strokes", "stroking", "stroked", "patted", "patting", "fusses", "fussing",
                 # A cat that hisses at the other cat, or goes for the dog, is not a person being
                 # warned off: "put her down or step back" is advice for somebody handling her,
                 # and nobody is. Those lines belong to the two-cats answer (or to a neutral
                 # note), so an animal named in the line stands this one down.
                 "other cat", "other cats", "another cat", "each other", "the other one",
                 "two cats", "second cat", "new cat", "other animals", "the dog", "my dog",
                 "the dogs", "the kitten", "another kitten", "the rabbit", "the puppy",
                 # a cable in the line is the cable card's question, and `cat-biting` carries the
                 # same score for it: "my cat bit through a plugged in cable and is drooling" got
                 # "Hands are not the toy" - the play answer - for a cat that may be burnt.
                 "cable", "cables", "wire", "wires", "charger", "chargers", "flex", "lead",
                 "extension lead",
                 # and a how-to-say-it line is a conversation about the owner, not a bite:
                 # "how do i tell my friend her cat scratched my child" got the play answer
                 ) + _SAYING_FRAME,
          # The people a cat bites are in the key so "how do i stop my cat biting the kids" is
          # this answer, and that also made it the answer to "i have 2 kids and a cat": a
          # household being described is not a bite. One word of the biting itself, or of asking
          # it to stop, has to be in the line.
          ask=("bite", "bites", "biting", "bit", "bitten", "nip", "nips", "nipping", "nip me",
               "scratch", "scratches", "scratched", "scratching", "attack", "attacks",
               "attacking", "attacked", "stop", "stops", "stopped", "stopping", "wont leave",
               "keeps going for", "goes for my", "goes for", "went for", "hiss", "hisses",
               "hissing", "growl", "growls", "growling", "aggression", "aggressive"),
          bias=1),
    # A cat and a baby in the same house is the question people ask before they get the cat, or
    # when they are expecting: "is a cat ok with a baby" was answered by the health visitor card
    # and "can i have a cat with a baby" by the same one, because a baby plus an animal reads as
    # a risk line. It is an ordinary household question with an ordinary answer.
    entry("cat-and-baby",
          (("cat", "cats", "kitten", "kittens"),
           ("baby", "babies", "newborn", "infant", "pregnant", "pregnancy", "expecting",
            "new arrival", "due in")),
          _cat_and_baby,
          # "my cat is pregnant", a cat giving birth and a cat's own labour are other rows: the
          # baby is the household's here, not the cat's litter
          avoid=("pregnant cat", "cat pregnancy", "in labour", "giving birth", "queening",
                 "litter of", "hisses at the baby", "bites the baby", "scratched the baby",
                 # the litter tray is its own hygiene question, and "is it safe to change cat
                 # litter when pregnant" wants the gloves answer, not the house rules
                 "litter", "litter tray", "tray", "toxoplasmosis", "scoop", "scooping",
                 "cat flap", "allergic", "allergy", "asthma", "miscarriage", "sids", "cot death",
                 # a child already in the house is the children row's (cat-and-children), which
                 # answers the smothering story and the first aid: this row is about a new baby
                 # arriving and about a pregnancy, so it hands the older child on
                 "kids", "kid", "child", "children", "toddler", "year old", "grandchild",
                 "grandchildren", "grandson", "granddaughter", "my son", "my daughter"),
          ask=("ok", "okay", "safe", "fine", "can i", "can we", "should i", "should we",
               "is it", "is a", "good idea", "risk", "dangerous", "worry", "worried", "advice",
               "have a cat", "get a cat", "getting a cat", "keep my cat", "with a baby",
               "with the baby", "around a baby", "introduce"),
          bias=1),
    # A dog that hoovers the pavement is a scavenging question: "how do i stop my dog eating
    # everything on walks" reached the how-far row, which said 30 minutes to an hour a day.
    entry("dog-scavenge", (("dog", "puppy", "pup"),
                           ("eat everything", "eats everything", "eating everything",
                            "eats things", "eat things", "eating things", "eats rubbish",
                            "eating rubbish", "picks things up", "picking things up",
                            "picks up", "picking up", "scavenge", "scavenging", "hoovers",
                            # a place is not a fault: "my dog runs off in the park" is recall
                            "eats on walks", "eating on walks", "picks up on walks",
                            "eats in the park", "scavenges in the park")),
          ("Teach a 'leave it' with a treat in your closed hand, then on the floor, then on a "
           "walk, and reward every time he looks at you instead of the ground: a dog that eats "
           "first and is told off after does not learn. Walk him on a head collar or a short "
           "lead past the bins, take high-value treats on the route, and feed a bit less at home "
           "so the search for food is less urgent. Ring the vet straight away if he swallows "
           "something that could block him - a bone, a corn cob, a sock - or if he is retching."),
          # eating fast at the bowl, chewing the furniture and what he can eat are other rows
          avoid=("bowl", "too fast", "fast", "gulp", "gulps", "chew", "chews", "chewing",
                 "furniture", "safe", "poison", "toxic", "chocolate", "grape", "onion"),
          # The behaviour phrase itself is the question: "how do i stop my dog eating
          # everything" has no walk or park in it, so the ask list has to name the shapes that
          # carry the behaviour, or the line falls through to the pub listings on the bare
          # word "eat". "in sight", "off the floor" and "in the garden" are the same fault.
          ask=("walk", "walks", "walking", "park", "pavement", "outside", "ground", "bin",
               "rubbish", "things", "everything", "anything", "finds", "sight", "floor",
               "garden", "pavements", "street"),
          bias=1),
    # "how do i tell my dog off" was a search hedge: the dog rows cover what to do about chewing
    # or jumping, none of them said how to say no, and the answer is that the telling off is not
    # the tool - the interruption and the thing you show him instead are.
    entry("telling-a-dog-off",
          (("dog", "dogs", "puppy", "pup", "puppies", "doggy"),
           ("tell off", "tell him off", "tell her off", "told off", "telling off", "tell it off",
            "scold", "scolding", "shout at", "shouting at", "punish", "punishment", "discipline",
            "telling my dog", "how do i tell my", "how do you tell", "how do i tell", "how to tell",
            "tell a dog off", "tell a puppy off", "tell my puppy off", "tell the dog off")),
          "Catch it in the act, interrupt with one short low word - 'ah-ah' or 'no' - and then "
          "show him what you do want: the sit instead of the jump, a chew toy instead of the "
          "shoe, and praise that. A telling off even a minute later means nothing to a dog, and "
          "shouting or a smack teaches him to hide it from you rather than stop. Use the same "
          "word every time, keep your voice flat rather than loud, and be quicker to reward the "
          "right version than to mark the wrong one.",
          # what to do about the behaviour itself, and a dog that is scared of people, are other
          # rows
          avoid=("bark", "barks", "barking", "scared", "afraid", "growl", "growls", "bite me",
                 "bit me", "snap", "snapped", "recall", "come back", "chew", "chews",
                 "chewing", "jump up", "jumping up", "vet", "vets"),
          bias=2),
    # Which dog suits a flat is the question people actually ask before they buy one, and the
    # answer is energy and noise, not size: a greyhound sleeps most of the day and a terrier does
    # not. Keyed on the home rather than the breed, so "what breed for a flat" and "is a labrador
    # ok in a flat" both land here.
    entry("dog-for-a-flat", (("dog", "dogs", "puppy", "pup", "breed", "breeds", "labrador",
                              "terrier", "greyhound", "whippet", "spaniel", "retriever",
                              "staffie", "collie", "pug", "cavapoo", "cockapoo"),
                             ("flat", "flats", "apartment", "maisonette", "small", "tiny",
                              "garden", "upstairs", "city", "suit", "best", "good", "which",
                              "what breed", "ok in", "indoor")),
          "Go by energy and noise, not size: a whippet or greyhound sleeps most of the day and "
          "suits a flat, while a collie or terrier needs a job and will bark at every noise in the "
          "stairwell. A fostered rescue can tell you what the dog is like indoors, and a breeder "
          "cannot. Check your lease allows dogs in writing, and think about the stairs before you "
          "say yes to a big old dog you will end up carrying.",
          # a cat, a rented flat's deposit and "how many walks" are all other answers, and so is
          # anything a dog has eaten or is doing ("can dogs eat grapes" is the vet's line)
          avoid=("cat", "cats", "kitten", "rabbit", "hamster", "deposit", "landlord", "rent",
                 "how much exercise", "how long walk", "eat", "eats", "eating", "ate", "grapes",
                 "chocolate", "onion", "raisins", "xylitol", "toxic", "poison", "poisoned",
                 "sick", "vomit", "vomiting", "vet", "barking", "barks", "bark", "growling",
                 "called",
                 # "keeps" alone stood the row down for "can i keep a dog in a flat", which is the
                 # same question asked with the other verb. What is not this row is a dog that
                 # keeps doing something, and those say what it keeps doing.
                 "keeps barking", "keeps chewing", "keeps scratching", "keeps weeing",
                 "keeps licking", "keeps escaping", "keeps jumping"),
          # it is the "which dog" question, not "my dog is doing something"
          # "can i have a dog in a flat" is the plainest way the question is put and every one of
          # its words missed this list, so the row that owns the question never answered it. The
          # key is a dog and a home, so the ask only has to be a way of asking - it is not doing
          # the work of saying what the row is about.
          ask=("what", "which", "how", "is it", "is a", "is an", "should", "any", "tips",
               "tip", "advice", "best", "good", "worth", "suit", "suitable", "ok in",
               "recommend", "recommendation", "can i", "can we", "can you", "could i", "may i",
               "allowed", "allow", "permitted", "have a", "keep a")),
    # The mirror of dog-for-a-flat: the question people ask before they get a cat. Two rooms and
    # a window are enough for a cat, and what it needs is something to climb and something to
    # hunt - so "can i keep a cat in a small flat", "will a cat be happy in a flat" and "are
    # indoor cats ok" all land here, and only the home words are in the key so a cat with a
    # sore paw in a flat is still the vet's line.
    entry("cat-for-a-flat", (("cat", "cats", "kitten", "kittens", "kitty", "moggy", "mog"),
                             ("flat", "flats", "apartment", "maisonette", "indoor", "inside",
                              "upstairs", "no garden", "one bedroom", "small flat",
                              "tiny flat", "rented", "block of flats", "high rise")),
          "A flat suits a cat well: two rooms and a window are enough as long as there is "
          "something to climb and something to hunt. A tall post by the window, a shelf at head "
          "height and a windowsill give it the height a garden would, and ten minutes with a toy "
          "on a string twice a day tires it out before bed. A bored indoor cat is the one that "
          "yowls at night. Keep the windows on catches, the blind cords short and the cables "
          "tucked away, check the lease allows pets in writing, and a rescue that has already "
          "lived indoors is an easier first cat than a kitten.",
          # a dog's flat, a cat left alone, a sick cat and a cat's scratching are all other rows
          avoid=("dog", "dogs", "puppy", "pup", "puppies", "hamster", "rabbit", "guinea",
                 "budgie", "parrot", "fish", "alone", "leaves", "leave", "long hours",
                 "weekend", "holiday", "litter tray", "litter box", "scratch", "scratching",
                 "sofa", "claws", "claw", "sick", "vomit", "vet", "eat", "eats", "eating",
                 "deposit", "insurance", "landlord")),
    entry("dog-toilet-training", (("dog", "puppy", "pup"),
                                   # "toilet train" and "potty train" are the ask as people write it,
                                   # and as phrases they out-weigh the bathroom-cleaning entry that
                                   # also keys on the bare word "toilet"
                                   ("toilet train", "toilet training", "potty train",
                                    "potty training", "house train", "housetrain",
                                    "wee", "wees", "weeing", "wee'd", "weed", "pee", "peeing",
                                    "peed", "piddle", "piddled",
                                    "toilet", "house training", "house trained", "potty",
                                    # the phrase, not bare "train": "how do i train my dog to
                                    # sit" is the obedience entry, and it must stay that way
                                    "toilet train", "toilet training", "potty train",
                                    "potty training",
                                    "inside", "in the house", "on the floor", "on the carpet",
                                    # "on the sofa" alone is not a toilet question - "the dog keeps
                                    # getting on the sofa" was answered with toilet training. The
                                    # accident on the sofa still matches on "wee"/"pee"/"marking".
                                    "marking",
                                    # "how long until it can hold its bladder" is the timing side
                                    # of the same training, so it is answered here rather than
                                    # left to the fallback
                                    "bladder", "hold it", "hold its wee", "hold his wee",
                                    # "how do i train my puppy to go outside" is this training:
                                    # "go outside" is how people say it, and the obedience entry
                                    # took it on the word "train"
                                    "go outside", "go out", "goes outside", "outside to wee",
                                    "outside to the toilet")),
          ("Go back to the basics of toilet training: take him out every hour and after every "
           "meal, nap and play, wait five minutes and praise and treat him the moment he goes "
           "outside. Clean indoor spots with an enzyme cleaner so no smell is left to return to, "
           "and don't scold him after the event, because he can't connect it. A puppy can hold "
           "about an hour for every month of age - two hours at two months, four at four - and less "
           "when he is excited or has just drunk, so expect a night trip until he is four or five "
           "months old. If a house-trained dog suddenly starts, have the vet check for a urine "
           "infection first."), bias=1,
          # a smell in the house is a cleaning job, not house training: "how do i get rid of a
          # dog smell in the house" was answered "take him out every hour and after every meal",
          # which is advice for a dog still learning. The words that name a smell stand this row
          # down so the pet-smell answer can take it.
          avoid=("smell", "smells", "smelling", "smelly", "smelt", "smelled", "odour", "odor",
                 "stink", "stinks", "stinking", "reek", "reeks", "reeking", "pong", "pongs",
                 "stench", "dog smell", "dog odour", "pet smell", "pet odour", "cat smell",
                 "wee smell", "urine smell", "musty", "damp")),
    # The timing is asked on its own: "how long until a puppy is house trained", "how long does
    # it take to house train a puppy" and "how often should i take a puppy out" were answered
    # with how much exercise to give him, because the walk row keys on "how long" and "how often"
    # beside "puppy"; "how long does house training take" named no dog at all and a Lifetime ISA
    # answered. The training itself is the subject here, so the walk, sleep, food and money rows
    # cannot be reached from a question about it.
    entry("dog-house-training-timeline",
          (("house train", "house trained", "house training", "housetrain", "housetrained",
            "housetraining", "toilet train", "toilet trained", "toilet training",
            "potty train", "potty training", "house training", "take a puppy out",
            "take the puppy out", "take a dog out", "take the dog out"),
           ("how long", "how often", "how many months", "until", "when will", "when can",
            "when", "long", "often", "long does", "long until", "time")),
          "Most puppies are clean in the house by four to six months, and a determined few take "
          "until nine or ten. The way there is frequency rather than a clock: out every hour at "
          "eight weeks and every two hours by twelve, and always after waking, eating and playing, "
          "plus once last thing at night. Catch the accidents you can - watch for sniffing and "
          "circling, take him straight out, praise the moment he goes, and clean any spot with an "
          "enzyme cleaner so no smell invites him back. A house-trained dog that suddenly starts "
          "needs the vet to rule out a urine infection.",
          bias=1,
          # the same words ask about sleep, walks and money, and those are other rows' lines.
          # "potty" is the child's word and "house" is the puppy's, but both are in this key,
          # because people do say "how do i potty train a puppy": a child named in the line
          # stands this row down, and a line naming no animal at all ("when do i start potty
          # training") goes to `potty-training`, which is biased above this row.
          avoid=("my son", "my daughter", "my child", "my toddler", "toddler", "toddlers",
                 "preschooler", "nursery", "playgroup", "my kid", "my boy", "my girl",
                 "two year old", "2 year old", "three year old", "3 year old",
                 "four year old", "4 year old",
                 "walk", "walks", "walking", "exercise", "sleep", "sleeps", "sleeping",
                 "through the night", "nap", "naps", "alone", "leave", "left", "hours",
                 "feed", "food", "cost", "price", "afford", "years", "live", "lifespan",
                 "bark", "biting", "chew", "crate", "car", "lead", "harness", "vet")),
    entry("puppy-excitement-wee", (("puppy", "pup", "dog"),
                                   ("excited", "excitement", "exciteable", "excitable",
                                    "greeting", "greets", "greeted")),
          ("That's excitement weeing, and it's not disobedience: keep greetings low key, say hello "
           "outside or on a hard floor, and don't lean over or stare at him. Take him out to "
           "wee the moment a visitor arrives, and it usually fades by a year old as his bladder "
           "and his self-control grow."), bias=2,
          # A dog that coughs, barks or is sick when excited was getting the toilet-training
          # answer, because "excited" was the only thing the line had to match.
          avoid=("cough", "coughs", "coughing", "sneeze", "sneezes", "bark", "barks",
                 "barking", "vomit", "vomiting", "sick", "chew", "chewing", "bite", "biting")),
    entry("dog-feed-amount", (("dog", "dogs", "puppy", "pup"),
                              ("feed", "feeding", "food", "portion", "portions",
                               "grams", "meals", "amount")),
          _dog_feed, avoid=("chocolate", "toxic", "poison", "poisonous", "raw", "human food",
                            # a dog that is too fat or too thin is a weight question, and "what
                            # should i feed him" inside it is the diet, not a portion guide
                            "fat", "too fat", "overweight", "obese", "diet", "slim", "slimming",
                            "losing weight", "lost weight", "put on weight", "putting on weight",
                            "gaining weight", "underweight", "too thin", "skinny",
                            "ate too much", "eaten too much", "stole", "greedy", "swallowed",
                            "exercise", "walk", "walking", "training", "play"),
          # a dog getting at the cat's dinner is a two-bowl problem, not a portion guide
          guard=lambda understood: not _one_pets_dinner(understood)),
    # "raw" alone is a food word ("my dog ate raw chicken"), so only the skin sense is keyed here.
    entry("dog-itch", ("dog", ("scratch", "scratching", "itchy", "itches", "itching",
                               "raw patch", "raw skin", "raw patches", "skin",
                               # a dog that chews one spot raw has an itch, not puppy teeth, and
                               # with "raw" off the chewing row those lines had no entry at all
                               "chewing his back", "chewing her back", "chewed his back",
                               "chewed her back", "chewing his skin", "chewing her skin",
                               "chewed his skin", "chewing himself", "chewed himself",
                               "chewing herself", "chewed herself", "licking himself raw",
                               "licking herself raw")),
          ("Itching that goes on for days is usually fleas, a food or pollen allergy, or a skin "
           "infection. Check the coat for fleas and flea dirt, treat all the pets in the house, "
           "and wash bedding hot. If the skin is red, broken or he is licking raw patches, see the "
           "vet: a short course of treatment settles it far faster than home remedies."),
          # An eaten meal is not a skin question: "my dog ate raw chicken" is about the food.
          avoid=("sofa", "furniture", "carpet", "door", "doors", "floor", "bed", "bedding",
                 "rug", "couch", "at the door", "to go out",
                 "ate", "eat", "eaten", "eating", "chicken", "bone", "bones", "swallowed")),
    # Fleas, worms and ticks are the three everyday pet-health questions people bring, and on
    entry("pet-worms", (PET_ANIMAL_ASK, ("worm", "worms", "worming", "wormed", "tapeworm",
                                         "roundworm", "threadworm")),
          ("Worms are treated rather than cured: most dogs are wormed every three months and "
           "cats on the vet's schedule, with a product from the vet, because shop ones do not "
           "always cover tapeworm. Roundworm eggs in dog and cat muck can infect people, so "
           "clear the garden and the litter tray daily, wash your hands, and keep children away "
           "from the tray. If the animal is also being sick, has a pot belly or a dull coat, or "
           "if someone in the house has threadworms, say so when you ring - and worm everyone "
           "in the house at the same time, because threadworms pass back and forth."),
          avoid=("compost", "garden worm", "wormery", "worm farm", "casting", "castings",
                 "bookworm", "worm cast"), bias=1),
    entry("pet-ticks", (PET_ANIMAL_ASK, ("tick", "ticks", "tick bite", "tick bites")),
          ("A tick has to come out properly: fine-tipped tweezers as close to the skin as you "
           "can get, pull steadily straight out without twisting, then clean the spot. Do not "
           "burn it, smother it in oil or pull it with your fingers - that makes it more likely "
           "to leave mouth parts behind or pass infection on. Keep it in a sealed pot in case "
           "the vet asks, and check the animal over daily after walks in long grass. Ring the "
           "vet if the bite goes red or a rash spreads from it, if the animal goes off its "
           "food, or if there is a limp or a fever in the weeks after."),
          # a tick is also a box to put a mark in, and a clock ticks
          # an avoid word that is an inflection of the key word cannot work: "ticked" and
          # "ticking" carry "tick" as a loose form, so they would turn the entry off for every
          # line it is for. The animal in the key is what keeps a clock out.
          avoid=("tick box", "tick list", "checklist", "tick tock", "tick the box",
                 "tick a box", "ticking clock", "clock"), bias=1),
    # Rabbit and guinea-pig claws are the same job as a cat's with two differences: they need it
    # even when they live outside, and a rabbit will not sit still for it. "how do i clip my
    # rabbits nails" was the search hedge, because `cat-claws` names a cat and nothing else.
    entry("rabbit-claws",
          (("rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs", "guinea",
            "hamster", "hamsters", "gerbil", "gerbils"),
           # Only the words a rabbit's claws are asked with, and no bare "nails": every common
           # word in a key makes that word less rare for every other row, and "nails" here was
           # enough to take "how often should i trim my dogs nails" off the dog's own card and
           # give it to grooming.
           ("claws", "claw", "clip", "clipping", "trim", "trimming", "cutting",
            "nails are", "nails too", "nails need", "overgrown")),
          "Use small animal or cat claw clippers and take only the clear hook off the end, well "
          "before the pink quick inside the claw - on a dark claw, shine a torch through it or "
          "take a sliver at a time. Wrap the animal in a towel with just one paw out, do a couple "
          "of claws a day and give a treat after each; a towel and two people make it much "
          "easier, and a hamster or a gerbil is worth a vet nurse's hand the first time instead "
          "of your own. Rabbits and guinea pigs on soft bedding need their claws doing every six "
          "to eight weeks, and a vet nurse will show you once for free.",
          # a rabbit's teeth and its hutch are other rows, and a rabbit that cannot use a leg is
          # the vet's
          avoid=("teeth", "tooth", "gnaw", "overgrown teeth", "hutch", "cage", "litter",
                 "limping", "limp", "not eating", "stopped eating", "sick", "ill", "vet",
                 "eats", "eating", "food", "diet", "hay"),
          # Above `pet-scratching`, which is a tie on "rabbits" and "claws" and normally wins
          # that tie on its own bias: a claw that wants cutting is not a pet scratching at
          # something, and the clippers are the answer.
          bias=4),

    entry("cat-claws", (("cat", "cats", "kitty", "claw", "claws",
                         # the apostrophe is its own word: "how do i clip my cat's claws" reached
                         # the furniture card because "cat's" is neither "cat" nor "cats", and
                         # the claws row needs two of its own words to be in the line
                         "cat's"),
                        ("clip", "cut", "trim", "clipping", "trimming", "cutting", "too long",
                         "sharp")),
          ("Take just the clear hook off the end and stop well before the pink quick: hold the paw, "
           "press the pad so the claw comes out, and cut straight across the tip. Do one or two "
           "claws a day with a treat if she hates it, and keep a scratching post so she wears them "
           "down herself."),
          # A scratched sofa is a furniture question, not a job for the clippers.
          avoid=("furniture", "sofa", "settee", "couch", "chair", "curtains", "carpet",
                 "door", "walls", "wall", "scratching post", "post", "groomer", "grooming"),
          # a clipped claw is this row and nothing else: "how do i clip my cat's claws" is two
          # ordinary words and a tie, which the scratching-card row was winning on entry order
          bias=1),
    entry("pet-breathing-fast", (("cat", "cats", "kitty", "dog", "dogs", "puppy", "pup", "pet"),
                                 ("breathing fast", "breathing quickly", "breathless", "panting",
                                  "open mouth breathing", "mouth open", "laboured breathing",
                                  "struggling to breathe", "breathing hard", "can't breathe",
                                  "cant breathe")),
          _breathing_fast, bias=1,
          # A normal breath, a smelly breath or a chesty cough is another entry. Panting is how
          # a dog cools down, so heat, a walk and a warm room take the line away from this card:
          # "my dog is panting a lot in this heat" wants shade and water, not the vet now.
          avoid=("smell", "smells", "kitten", "kittens", "cough", "coughing",
                 "sneeze", "sneezing", "hiccup", "heat", "hot", "walk", "walks",
                 "walked", "weather", "after", "car", "play", "playing", "excited",
                 "summer", "sun", "humid")),
    # "my dog has the runs" was answered with "Noted: your dog has the runs", and the sick row
    # below said "A single vomit" to a dog with diarrhoea, which is the words that were wrong
    # rather than the advice. The phrases are whole ones ("the runs", "runny poo") because bare
    # "runs" is a dog running off in the park, which is the recall question.
    entry("dog-vomiting", (("dog", "puppy", "puppies", "pup"),
                           ("vomit", "vomits", "vomiting", "vomited", "puke", "pukes",
                            "puked", "puking", "brings up", "brought up",
                            "sick", "diarrhoea", "diarrhea",
                            "the runs", "has the runs", "got the runs", "runny poo",
                            "runny tummy", "loose poo", "loose stools", "squits",
                            "bad belly", "bad tummy", "upset tummy", "upset stomach",
                            "dodgy belly", "poorly tummy")),
          _DOG_SICK_REPLY,
          # the car answer comes first for a puppy that is sick on a journey, and this row must
          # not take it back
          avoid=("car", "cars", "travel", "journey", "journeys", "drive", "driving",
                 "back seat", "backseat", "motion", "cat", "cats", "kitten", "kittens")),
    # "My cat is sick in the car" was the passenger's answer - "sit in the front seat, look at
    # the horizon rather than a screen" - because the human motion-sickness row is the only one
    # that keys a car and sickness for an animal that is not a dog. A cat in a car is in a
    # carrier, not a front seat, and the two causes (travel sickness and fear) are handled
    # together.
    entry("cat-car-sick", (("cat", "cats", "kitten", "kittens"),
                           # an actual car word: the sickness is required by ask below
                           ("car", "cars", "travel", "journey", "journeys", "drive", "driving",
                            "motion", "back seat", "backseat", "on the way")),
          ("A cat that is sick in the car is usually travel sick or frightened, and the two are "
           "managed the same way: nothing to eat for three or four hours before you set off, the "
           "carrier on the back seat with a familiar blanket over it and facing forward, the car "
           "cool, and a break halfway on a long drive. Two or three short trips to somewhere "
           "pleasant and back build her up, and ask the vet about a travel-sickness tablet for a "
           "house move. Never let her out of the carrier in a moving car."),
          # the human motion-sickness card is written for the passenger in the front seat, so a
          # line that names a cat has to beat it
          bias=3,
          ask=("sick", "sickness", "sick in the car", "car sick", "carsick", "vomit", "vomits",
               "vomited", "vomiting", "throw up", "threw up", "throwing up", "puke", "drool",
               "drools", "drooling", "travel sickness", "motion sickness", "queasy",
               "scared", "scary", "afraid", "frightened", "terrified", "hates", "hate",
               "nervous", "anxious", "panics", "shakes", "shaking", "cries", "crying",
               "mews", "miaows", "howls", "yelps", "wees", "poos", "toilet",
               # "how do i get my cat used to the car" is the same question as the sickness and
               # the fear: the reply is the two short trips and the blanket over the carrier
               "used to", "get used", "used to the car", "first journey", "first trip",
               "settle", "calm", "calm down"),
          # heat and a cat left in a car are the heat answer; the trip to the vet is its own card
          avoid=("panting", "pants", "hot", "heat", "cool down", "window open",
                 "left in the car", "leaving her in the car", "in the car park",
                 "to the vet", "vet visit", "cattery", "litter tray")),
    entry("dog-car-sick", (("dog", "dogs", "puppy", "pup"),
                        # only an actual car word: the sickness is required by ask below
                        ("car", "cars", "travel", "journey", "journeys", "drive", "driving",
                         "motion", "back seat", "backseat", "on the way")),
          ("Don't feed him for a few hours before a journey, keep the car cool and well ventilated, "
           "and cover the seat with a familiar blanket. Short trips to somewhere good, built up "
           "over weeks, settle most dogs; ask the vet about travel sickness tablets for long "
           "journeys."),
          # the human motion-sickness answer is written for the passenger in the front seat, so a
          # line that names a puppy or a dog has to beat it
          bias=3,
          # "my dog is being sick" is the vomiting answer: only a car word makes it travel sickness
          # a car word alone is not enough: "can i leave my dog in the car" is the heat-and-car
          # answer, so the line has to be about being sick as well
          # A dog that is frightened of the car is the same journey question: the answer's second
          # half is the desensitising plan, and without the feeling words in this gate
          # "my dog is scared of the car" was a shrug.
          ask=("sick", "sickness", "sick in the car", "car sick", "carsick", "vomit", "vomits",
               "vomited", "vomiting", "throw up", "threw up", "throwing up", "puke", "drool",
               "drools", "drooling", "travel sickness", "motion sickness", "queasy",
               "scared", "scary", "afraid", "frightened", "terrified", "hates", "hate",
               "nervous", "anxious", "panics", "shakes", "shaking", "whines", "whining",
               "cries", "crying"),
          # a dog panting in the car is the heat answer, and the car word alone is not sickness
          avoid=("panting", "pants", "hot", "heat", "pant", "cool down", "window open",
                 "leaving him in the car", "left in the car", "in the car park")),
    entry("dog-night-cough", (("dog", "dogs", "puppy"),
                              ("cough", "coughs", "coughing", "hacking", "night", "nights",
                               "at night", "in the night", "evening", "nighttime")),
          ("A cough that only comes at night is worth a vet visit rather than a wait. In an older "
           "dog it can be a heart problem or a collapsing windpipe, in any dog kennel cough or a "
           "soft-palate problem, and in a puppy it is urgent. Ring today, and go straight in "
           "tonight if he is also panting at rest, breathing fast, off his food or pale or blue "
           "at the gums."),
          # "my dog has a cough" is a plain symptom line, and the night answer would read as a
          # guess about the time of day, so a night word has to be there. A cough is also
          # required: with the dog named a turn earlier, "we got a puppy last week" then "and
          # at night" put the puppy back on a line that says nothing about coughing, and the
          # vet card was the answer to a bedtime question. A line that names a cough and a night
          # is a cough, whatever else it says.
          ask=("cough", "coughs", "coughing", "coughed", "hacking", "hacks", "hack",
               "wheeze", "wheezes", "wheezing", "kennel cough", "honking"),
          # "how long until he sleeps through the night" is a puppy-sleep question, and with the
          # puppy named in the last turn it landed here: a cough is a cough, not a bedtime.
          # And a dog barking next door at night is nobody's cough: "dog" and "night" alone were
          # enough to send a noise complaint to the vet, so the noise words stand this one down.
          # Pacing, panting, tiredness and crying at night have their own answers, and the cough
          # reply would read as a guess about the time of day: the night word alone must not win.
          avoid=("cat", "cats", "kitten", "kittens", "paracetamol", "ibuprofen", "sleep",
                 "sleeps", "sleeping", "slept", "through the night", "crate", "crying",
                 "cries", "cried", "whining", "whines", "settle", "settles", "bedtime",
                 # "my dog is 11 and keeps waking at night" is the night question, not a cough
                 "wake", "wakes", "waking", "woke", "asleep", "to sleep", "settling",
                 "paces", "pacing", "paced", "wanders", "wandering", "restless",
                 "pants", "panting", "panted", "pant", "out of breath", "breathing",
                 "tired", "sleepy", "yawn", "yawns", "hot", "overheated",
                 "drinking", "drinks", "drink", "thirsty", "thirst", "water",
                 "weeing", "urinating", "peeing",
                 "bark", "barks", "barking", "noise", "noisy", "howl", "howls", "howling",
                 ) + _NEIGHBOUR_DOG),
    entry("dog-doorbell", (("dog", "dogs", "puppy"),
                           ("doorbell", "door bell", "knock", "knocks", "knocking", "visitors",
                            "callers", "someone at the door", "people at the door")),
          ("Practise the whole thing rather than the bark: put him on a lead, have someone ring "
           "the bell or knock, and ask for a sit a few steps back from the door before it opens. "
           "Reward the sit, not the silence. Five times a day for a week with a friend and it "
           "starts to stick, and give him a mat or a spot to go to when the bell goes. Shouting "
           "at the barking, or at the door, makes it worse."),
          avoid=("go out", "to go out", "let him out", "let her out", "let out", "outside",
                 "toilet", "wee", "poo", "scratches", "scratching")),
    entry("dog-eating-grass", (("dog", "dogs", "puppy", "pup"), ("grass", "eat grass",
                                   "eating grass", "eats grass", "chew grass", "chewing grass")),
          ("Most dogs eat grass now and then and it is usually harmless, but it often means an "
           "upset stomach, boredom or too little fibre. Make sure the grass has not been treated "
           "with weedkiller, give a little more fibre and something to chew, and see the vet if "
           "it is repeated with vomiting, tiredness or weight loss."), bias=1),
    entry("dog-friendly-places", (("dog",),
                                  # a place to eat, never the bare verb: "how do i stop my dog
                                  # eating everything" is a behaviour question, and it was
                                  # answered with the pub listings because "eat" was enough.
                                  ("pub", "pubs", "restaurant", "restaurants", "cafe", "cafes",
                                   "coffee shop", "places", "to eat", "eat out", "eat with",
                                   "out to eat", "somewhere to eat", "place to eat", "meal",
                                   "lunch", "dinner", "drink", "stay", "stay over",
                                   # "is there anywhere i can eat and bring my dog" rests on the
                                   # verb alone once the bare "eat" is gone, and the behaviour
                                   # answer took it: the eating-out shapes are spelled out here.
                                   # Each one keeps the word "eat" next to a place or a joining
                                   # word, so "eats everything in the garden" still is not this.
                                   "anywhere to eat", "anywhere i can eat", "anywhere we can eat",
                                   "anywhere i can take", "anywhere we can take",
                                   "eat and", "eat there", "eat in", "eat at", "go for a meal",
                                   "eat something with", "somewhere with the dog")),
          # "why do dogs eat grass" is not a question about where to take the dog for dinner.
          ("Search \"dog friendly pubs\" and the town name: the listings on DogFriendly and "
           "PubsGalore are usually accurate and current. In most British towns the old pubs with "
           "wooden floors are the safest bet, and a quick phone call settles it."),
          # a dog that will not eat is a worry, not a question about pubs. Name the not-eating
          # shapes, never the bare word "eat": "where can i eat something with my dog" is a pub
          # question, and so is "my dog is ill, can i still take him to the pub".
          avoid=("not eating", "wont eat", "won't eat", "stopped eating", "off his food",
                 "off her food", "off their food", "isnt eating", "isn't eating", "doesnt eat",
                 "doesn't eat", "appetite", "ate something", "eaten something", "swallowed",
                 # a refusal is a refusal of food, not a booking: "our spaniel refused his
                 # dinner" got the pub listings because "dinner" was the only word the row
                 # needed, and a dog that will not eat is the vet question instead.
                 "refused", "refuses", "refusing", "refuse", "wont touch", "won't touch",
                 "not touched", "turned his nose up", "turns his nose up", "turned her nose up",
                 "vomit", "vomiting", "miserable", "sick", "vet",
                 # and neither is what he is allowed to eat: "can dogs eat grapes" was getting
                 # the pub listings. The poisons table itself is #126's, not a second entry here.
                 "cheese", "milk", "grapes", "grape", "raisins", "raisin", "onion", "onions",
                 "garlic", "poison", "poisonous", "toxic", "feed", "foods", "diet", "xylitol",
                 "sugar free", "sugar-free", "macadamia", "avocado", "lilies", "alcohol",
                 # and a dog that gulps his dinner wants the slow feeder, not the pub listings
                 "too fast", "eats fast", "eating fast", "eats too quick", "gulps", "gulping",
                 "gobbles", "bolts", "bolting", "wolfing", "scarfing", "inhales", "vacuums",
                 "banana", "apple", "carrot", "peanut butter", "nuts",
                 # and a dog eating grass is not a dog to take out for dinner
                 "grass", "lawn", "poo")),
    # The beach is the one day out a dog comes to, so it is the dog's question and not the
    # picnic's: "can i take my dog to the beach" was answered with a frittata cut in wedges, and
    # "are dogs allowed on the beach" with the leaving-him-alone card, because no row claimed the
    # beach for a dog. What settles it is the council's seasonal ban, and that is on the sign.
    entry("dog-beach", (("dog", "dogs", "puppy", "pup", "puppies"),
                        ("beach", "beaches", "seaside", "the coast", "sand", "sands", "shore",
                         "seafront", "sea front", "promenade", "dunes", "sand dunes",
                         "on the sand", "dog friendly beach", "dog friendly beaches")),
          ("Most beaches allow dogs, but plenty of councils ban them on the main stretch from "
           "about May to September, so read the sign where you walk on: it names the beach and "
           "the months, and the council's own page lists the rest. Take fresh water, because sea "
           "water gives a dog the runs, and go early or late on a hot day as sand and pebbles "
           "burn pads. Keep the lead on where birds nest or lifeguards are working, check the "
           "tide before he swims, and bag it and bin it."), bias=1,
          # "my dog is at the beach" is news, and it was told the council's rules: the line has
          # to ask whether the dog may be there, or how to take him.
          ask=("allowed", "can i", "can we", "could i", "should i", "is it", "is the", "are the",
               "are they", "is there", "ok", "okay", "fine", "friendly", "take", "taking",
               "bring", "bringing", "let", "off the lead", "off lead", "lead", "safe",
               "which", "where", "near me", "nearby"),
          # A dog that has drunk the sea, or eaten something on the sand, is the vet question and
          # those rows carry their own bias; a dog that ran off is the search; and the place to
          # eat afterwards is the pub row's.
          avoid=("sea water", "salt water", "saltwater", "seawater", "drank", "drink", "drinking",
                 "swallowed", "ate", "eaten", "eating", "poison", "poisonous", "toxic",
                 "lost", "missing", "gone missing", "ran off", "run off", "escaped", "bolted",
                 "pub", "pubs", "restaurant", "cafe", "somewhere to eat", "place to eat",
                 "ferry", "plane", "flight", "train", "abroad", "pet passport", "travel",
                 "food", "picnic", "lunch", "sandwich", "sandwiches", "cool box")),
    # A pet's dinner or tea is its food, and only "food" was written down: "the cat is a bit off
    # her dinner today" reached no answer at all, "my dog is off his dinner" the dog-friendly pubs
    # and "my dog has gone off his tea" the shelf life of tea. The meal words are the same refusal
    # in the words people use for the bowl, so both not-eating rows read them.
    entry("dog-not-eating", (("dog", "puppy", "pup"),
                             ("not eating", "wont eat", "won't eat", "isnt eating", "isn't eating",
                              "doesnt eat", "doesn't eat", "will not eat", "stopped eating",
                              "off his food", "off her food", "off their food", "refusing food",
                              "no appetite", "refuses food", "refuses his food",
                              "refuses her food", "refuses to eat", "wont touch his food",
                              "wont touch her food", "not touching his food",
                              "not touching her food", "leaves his food", "leaves her food",
                              # the refusal said in the past tense, and said about the meal
                              # rather than the appetite: "our spaniel refused his dinner" named
                              # no food shape at all, so with the pub listings stood down the
                              # line fell through to a dud instead of the vet question.
                              "refused his food", "refused her food", "refused food",
                              "refused his dinner", "refused her dinner", "refused the food",
                              "refused his meal", "refused her meal", "refused to eat",
                              "refuses his dinner", "refuses her dinner", "refusing food",
                              "hasnt eaten", "hasn't eaten", "not eaten")
                             + PET_OFF_MEAL),
          ("Ring the vet today if it has been more than 24 hours, and straight away for a puppy "
           "under six months, or if there is vomiting, diarrhoea or he seems dull. A dog that "
           "refuses food is usually feeling sick or in pain rather than being fussy; if he is "
           "bright and drinking, take the bowl away after 20 minutes and offer it again next "
           "meal. Meanwhile try warm chicken and rice by hand, and check his mouth and teeth for "
           "something stuck."), bias=1,
          # a dog that will not stop eating the cat's dinner is greedy, not off his food
          guard=lambda understood: not _one_pets_dinner(understood)),

    # --- cats --------------------------------------------------------------------
    entry("cat-not-eating", ("cat", ("not eating", "stopped eating", "not eaten", "wont eat",
                                     "won't eat", "off her food", "off his food", "appetite",
                                     "not hungry", "no interest in food", "eating less",
                                     "eats less", "barely eating",
                                     # the same refusal without the phrase "not eating": a cat
                                     # that turns her nose up is a cat that is not eating. The
                                     # bare word `food` is still out, because "what should i feed
                                     # my cat" is a different question.
                                     "wont touch her food", "wont touch his food",
                                     "won't touch her food", "won't touch his food",
                                     "wont touch food", "turning her nose up",
                                     "turning his nose up", "nose up at her food",
                                     "refused his food", "refused her food", "refused food",
                                     "refused his dinner", "refused her dinner",
                                     "refused to eat", "turned her nose up",
                                     "turned his nose up", "hasnt eaten", "hasn't eaten",
                                     "nose up at his food", "no interest in her food",
                                     "no interest in his food", "interested in her food",
                                     "interested in his food", "fussy with her food",
                                     "fussy with his food", "fussy eater", "fussy about food")
                                    + PET_OFF_MEAL),
          ("A cat that stops eating for more than 24 hours needs a vet, especially an older one: "
           "cats can get dangerously ill quickly from not eating. Offer warm strong-smelling food "
           "and a quiet place, and ring the vet today if she is 12 and off her food."),
          # A nose turned up at food is the line this row is for, and a wound row must not rank
          # above it: the key word "turning" in the pale-gums row below changed the rarity
          # arithmetic and put a bite or a scratch answer on a cat that simply will not eat.
          bias=3,
          # "eating" alone answers the opposite line: "she's 12 and still eating fine" is a
          # reassuring turn in a chat about a cough, and it was getting the not-eating answer.
          # A cat eating grass or a houseplant is not a cat off its food either.
          avoid=("eating fine", "eating well", "eating ok", "eating okay", "eating normally",
                 "eating again", "eating as normal", "eating plenty", "eating everything",
                 "appetite is fine", "appetite is good", "appetite back", "grass", "grazing",
                 "chew", "chewing", "licking", "plant", "plants", "houseplant", "houseplants",
                 "flowers"),
          # "my dog wont stop eating the cats food" is the opposite of a cat off her food, and
          # the other pet's dinner is the row below's question.
          guard=lambda understood: not _one_pets_dinner(understood)),
    entry("cat-eating-grass", (("cat", "cats", "kitten"),
                               ("grass", "eat grass", "eating grass", "eats grass", "chew grass",
                                "chewing grass")),
          ("Cats eat grass now and then and it is mostly harmless: the blades tickle the stomach "
           "so she brings up a hairball or settles an upset tummy. Check the grass has not been "
           "treated with weedkiller, and see the vet if she is sick every time or off her food."),
          bias=1,
          # A cat that is already being sick, or off its food, wants the vet answer this entry's
          # own reply ends on - not the reassurance that grass is usually harmless.
          avoid=("sick after", "sick since", "sick twice", "sick a lot", "sick again",
                 "being sick", "been sick", "threw up", "throwing up", "vomit", "vomiting",
                 "vomited", "off her food", "off his food", "not eating", "stopped eating",
                 "poisoned", "wobbly", "drooling", "too much")),
    entry("cat-eating-plants", (("cat", "cats", "kitten"),
                                ("plant", "plants", "houseplant", "houseplants", "flowers")),
          ("A cat chews houseplants for the crunch and the water in the leaves, but some are "
           "dangerous: true lilies are deadly to cats, even a sniff of the pollen, and ivy, "
           "poinsettia and peace lily burn the mouth. Move those out of reach, put a tray of cat "
           "grass down instead, and ring the vet if she drools, vomits or looks wobbly."),
          bias=1,
          # A cat called Flower, Daisy or Lily is a cat, not a plant. The plant words are loose
          # forms, so the line has to be about eating or about harm before this entry answers.
          ask=("eat", "eats", "eating", "ate", "chew", "chews", "chewing", "nibble", "nibbling",
               "bite", "bites", "biting", "munch", "munches", "safe", "toxic", "poison",
               "poisonous", "harm", "harmful", "dangerous", "sick", "vomit", "drool"),
          # a cat that has stopped eating is a vet question, not a plant question
          avoid=("not eating", "stopped eating", "wont eat", "won't eat", "off her food",
                 "off his food", "appetite")),
    # A cat that chews plastic, string or cables is not eating a plant, and it is not a habit
    # tip either: the soft thing she tears up is a boredom answer with a real hazard behind it,
    # because a cat that swallows string or a hair tie gets a linear blockage that needs surgery.
    entry("cat-chews-things", (("cat", "cats", "kitten", "kittens"),
                               # never "bites" or "biting": those are `cat-biting`'s own words,
                               # and a key word is only *specific* to a follow-up while few keys
                               # hold it - adding them here pushed "biting" over the rarity line
                               # and "he keeps biting my hands" after a kitten stopped reaching
                               # the play answer at all.
                               ("chews", "chewing", "chew", "chewed",
                                "nibbles", "nibbling", "sucks", "sucking",
                                "plastic", "plastics", "plastic bags", "bag", "bags",
                                "carrier bag", "string", "wool", "tinsel", "hair ties",
                                "hairband", "hair bands", "rubber bands", "elastic",
                                # the cable words live in `pet-chews-cables`, which is the
                                # electrical question: while they were here, "my cat bit through a
                                # plugged in cable and is drooling" got the plastic-and-string
                                # card, and a card that names a burnt mouth cannot be the second
                                # answer to the same word.
                                "cords", "bubble wrap", "foil")),
          ("Cats chew plastic and string for the crinkle and the texture, and it is usually "
           "boredom or hunting that has nowhere to go: a wand-toy game before meals, a cardboard "
           "box to shred and a chew-safe toy give her something better to do. Keep bags, rubber "
           "bands, hair ties, tinsel and string out of reach, because a cat that swallows them can "
           "get a linear blockage that needs surgery. If she has swallowed string or tinsel, or is "
           "being sick or off her food, ring the vet today rather than watching it."),
          # the plant question has its own row (some houseplants are deadly), and a cat that has
          # stopped eating is a vet question rather than a chewing one
          avoid=("plant", "plants", "houseplant", "houseplants", "flowers", "toxic", "poison",
                 "poisonous", "lily", "lilies", "not eating", "stopped eating", "wont eat",
                 "won't eat", "off her food", "off his food", "appetite",
                 # A cat that has already swallowed the thing is not asking about the habit:
                 # "my cat swallowed a rubber band" is a foreign body and a vet call tonight,
                 # and safety.py only catches the word "string" here. The habit lines say
                 # "chews" or "keeps eating", which are left to the row.
                 "swallow", "swallowed", "swallowing", "choked", "choking",
                 "ate a", "ate the", "has eaten", "has swallowed")),
    # a new cat under the bed is not a shopping list and not a medical worry: it is the first
    # few days, and the answer is to give it room. The words are the cat's own behaviour, so a
    # dog line never reaches it.
    entry("cat-hiding", (("cat", "cats", "kitten", "kittens"),
                         ("hides", "hiding", "hides under", "hiding under", "under the bed",
                          "under the sofa", "under the settee", "behind the sofa", "wont come out",
                          "won't come out", "wont come out from", "stays under", "staying under",
                          "goes under", "went under", "keeps hiding", "hiding away",
                          "new home", "first night", "first day", "new house", "just brought her home",
                          "just got her home")),
          ("That is normal, especially in the first few days or when something new has arrived: "
           "let her hide and do not pull her out. Keep her in one quiet room with food, water and "
           "the litter tray close by, sit on the floor and talk or read aloud for ten minutes at a "
           "time so she gets used to you, then let her come to you. She should be eating, drinking "
           "and using the tray within 24 hours; after three or four days of hiding, or if she stops "
           "eating, ring the vet."),
          # A fear word on its own is not this answer: "my cat is scared of the new puppy" and
          # "my cat is afraid of fireworks" are fear-of-something questions, and telling that
          # owner to shut her in a quiet room answers the wrong thing (#misroutes, airy-deer).
          avoid=("scared", "frightened", "afraid", "terrified", "timid", "shy", "nervous",
                 "used to", "getting used to")),
    entry("cat-overstimulated",
          (("cat", "cats", "kitten", "kittens"),
           # the stroking, not the scratching: a cat that shreds the sofa is cat-scratching's.
           # Phrases, not bare "bite"/"bites": "a bit overweight" reads as "bite", and a fat cat
           # was getting the stroking answer.
           ("bites me", "bites my", "bites when", "biting me", "biting my", "nips me",
            "nipping me", "stroke", "strokes", "stroking", "patted", "pats", "turns on me",
            "swipes",
            # "swipes" was the only one here, so "my cat swipes at me" is this answer rather than
            # the general biting row: the same handful of words, said as a warning first
            "swipe", "swiping", "lashes out", "lashing out")),
          ("That is usually over-stimulation: stroking gets too much for her and the bite is how "
           "she says stop. Keep it to the head and cheeks rather than the back and tail, watch for "
           "the tail flick and the skin twitch and stop before that, and let her come to you. A "
           "sudden change in a cat who used to enjoy it is worth a vet check for pain."), bias=1,
          # a puppy or a dog is the mouthing answer's, and a person biting their nails is nobody's
          # A kitten biting during play is the play answer's ("hands are not the toy", above):
          # "my new kitten is biting me" was getting the stroking answer instead, which tells the
          # owner to stop stroking a cat that was never being stroked.
          avoid=("puppy", "pup", "dog", "dogs", "children", "child", "toddler", "baby", "my son",
                 "my daughter", "nails", "hand", "hands", "kitten", "kittens", "new kitten",
                 "play", "playing", "toy", "toys")),
    # Being picked up is the one thing most cats will not put up with, and it had no answer:
    # "my cat wont let me pick her up" was a shrug, "how do i hold a cat" and "can i pick my cat
    # up by the scruff" were two more, "my kitten wont let me hold her" was sent to the vet's
    # desk, and "my cat hates being picked up" and "my cat bites me when i pick her up" were
    # answered about stroking, which the cat was not being. The stroking row keeps the stroke
    # words now, and the lift, the hold and the scruff are this row's.
    entry("cat-handling",
          (("cat", "cats", "kitten", "kittens"),
           ("pick her up", "pick him up", "pick them up", "pick up", "picked up", "picking up",
            "lift her", "lift him", "lifting", "hold her", "hold him", "holding her",
            "holding him", "be held", "being held", "cuddle", "cuddles", "cuddling",
            "carry her", "carry him", "carrying", "hold a", "holding a", "hold your", "hold my", "holding my",
            "carry a cat", "let me pick", "lets me pick",
            "wont let me pick", "won't let me pick", "wont let me hold", "won't let me hold",
            "hates being picked", "hates being held", "scruff", "squirms", "squirm",
            "wriggles", "wriggle",
            # the bite or the scratch is what says the cat does not want to be lifted, and the
            # stroking row keys the same "bites me": the lift has to be named in the key, not
            # left to the bite
            "bites me when i pick", "bites when i pick", "bites me when i lift",
            "scratches me when i pick", "scratches when i pick", "bites when picked",
            "hates being picked up", "hates being held")),
          ("Most cats hate being lifted off the ground, so pick her up rarely and briefly: one "
           "hand under the chest behind the front legs, one under the back legs, and hold her "
           "against you so all four feet are supported. Never lift an adult cat by the scruff - "
           "that is for a vet holding a kitten. Put her down the moment she starts to wriggle, and "
           "let her come to you on the sofa instead: a cat that is picked up only when she asks "
           "starts to allow it. If she used to be fine and now struggles, that is often pain - a "
           "bad tooth, a sore back, arthritis - so a change like that is worth a vet visit."),
          bias=2,
          # stroking a cat that then bites is the over-stimulation answer, and a carrier, a car
          # journey and a lead are their own questions: this row is only about the lift.
          avoid=("stroke", "strokes", "stroking", "patted", "patting", "tummy", "belly",
                 "carrier", "carriers", "car journey", "in the car", "travelling", "travel",
                 "vet", "vaccination", "harness", "lead", "scratching", "scratch",
                 # a cat that cries or yelps when it is handled is the pain row's, not this
                 # one's: the lift is how a sore cat says where it hurts, and this answer is for
                 # the cat that only dislikes being picked up
                 "cries when i pick", "crying when i pick", "cries when i lift",
                 "cries when i touch", "cries when i stroke", "yelps", "yowls when i",
                 "hisses when i", "in pain", "in agony", "sore", "hurts when", "aches when")),
    # Getting a cat into its carrier is the other half of handling one, and it was nothing at
    # all: "my cat hates the carrier" was a plain ack and "how do i get my cat in a carrier" was
    # a shrug. The answer is the carrier as furniture, not a fight in the hall.
    entry("cat-carrier",
          (("cat", "cats", "kitten", "kittens"),
           ("carrier", "carriers", "crate", "basket", "cat box", "pet carrier", "travel box",
            "in the carrier", "into the carrier", "get her in", "get him in", "put her in",
            "put him in", "car journey", "in the car", "vet visit", "travel to the vet")),
          ("Leave the carrier out all the time with a blanket and a familiar smelling toy in it, "
           "feed her next to it and then inside it, and never tip her in: pick the carrier up "
           "with her already in it, or lower her in back feet first. On the day, a towel over the "
           "carrier keeps her calmer, and the seatbelt goes through the handle rather than the "
           "cat loose in the car. If she panics every time, ask the vet for a plug-in or a "
           "short course of a calming supplement before the next appointment."),
          bias=1,
          # being picked up is the lift answer, and a cat that is sick on the journey is the
          # car-sickness row: this one is only about the box.
          avoid=("sick", "vomit", "vomited", "travel sick", "car sick", "drool", "drools",
                 "how do i hold a cat", "pick her up", "pick him up", "scruff")),
    # And a cat that will not be brushed is the fourth: "my cat hates being brushed" and "how do
    # i brush my cat" both got the frequency answer, and "my cat attacks the brush" got it too,
    # which is no help to somebody holding a brush and a cat with its ears back.
    entry("cat-brushing-hate",
          (("cat", "cats", "kitten", "kittens"),
           ("hates being brushed", "hates the brush", "hates brushing", "hates being groomed",
            "wont let me brush", "won't let me brush", "wont let me groom", "wont be brushed",
            "attacks the brush", "bites the brush", "bites me when i brush",
            "scratches me when i brush", "struggles when i brush", "hates the comb",
            "wont let me comb", "fights the brush",
            # the coat row keys "brush" twice over and wins the score on it, so the dislike has
            # to be named in its own words and carry the higher bias
            "brush", "brushes", "brushing", "brushed", "comb", "combing")),
          ("Keep it to one minute and start when she is already sleepy, after a meal: let her "
           "sniff the brush and put it down beside her first, then do one stroke along her back, "
           "a treat, and stop while she is still happy. A soft rubber glove or a short-bristled "
           "brush hurts less than a metal comb on a short coat, and the belly, tail and legs are "
           "for the vet or the groomer, not for a cat who already hates it. Two or three of those "
           "minutes a week is plenty for most cats. If she used to be fine and has started to "
           "hate being touched, that is often pain - teeth, back, an over-sensitive patch - so "
           "have her looked at."),
          # a frequency question is the brushing row's, and a mat is the mat answer's: this is
          # only the cat that will not have it
          avoid=("how often", "how many times", "times a week", "once a day", "twice a week",
                 "every day", "daily", "mat", "mats", "matted", "matting", "knots", "tangled",
                 # and a plain how-to-brush is the coat row's routine, which is a good answer:
                 # this row is only for the cat that will not have it
                 "how do i brush", "how should i brush", "how do i comb", "which brush",
                 "best brush", "what brush", "how to brush"),
          bias=3),
    # A cat that will not sit on you is the third side of the same question as the lift and the
    # carrier, and it was nobody's: "my cat wont sit on my lap" and "my cat doesnt like being
    # touched" and "my cat ignores me" were plain acks, "how do i get my cat to like me" was a
    # shrug, "my cat is not affectionate" was "I'm listening", and "how do i bond with my cat" was
    # the answer about introducing a second cat.
    entry("cat-affection",
          (("cat", "cats", "kitten", "kittens"),
           ("sit on my lap", "sit on me", "sits on my lap", "lap", "cuddle", "cuddles",
            "affection", "affectionate", "bond", "bonding", "like me", "likes me", "love me",
            "loves me", "ignores me", "ignoring me", "wont come near me", "wont come to me",
            "doesnt like being touched", "doesn't like being touched", "not a lap cat",
            "follows me", "comes to me", "purrs", "not friendly", "friendly", "shy with me",
            "scared of me", "hates me", "only likes my partner", "likes my partner more",
            "likes my husband more", "likes my wife more", "closer to my")),
          ("Cats show affection on their own terms, and the way to be chosen is to stop reaching: "
           "sit on the floor, play with a wand toy for five minutes twice a day, and let her come "
           "to you and walk away again without being picked up. Offer a finger to sniff, blink "
           "slowly at her and look away, and put a treat down rather than holding it out. She may "
           "never be a lap cat and that is normal; the cats who do sit on laps are the ones nobody "
           "lifted. It can take weeks or months with a shy cat, and a cat who used to be "
           "affectionate and now hides from you is a vet question, because pain and thyroid "
           "trouble both change a cat's temper."),
          bias=2,
          # the carrier, the lift, a new cat meeting the old one and a cat that has stopped eating
          # are their own answers, and a person describing their cat is not asking for advice
          avoid=("carrier", "pick her up", "pick him up", "scruff", "introduce", "introduction",
                 "new kitten", "another cat", "second cat", "other cat", "not eating", "litter",
                 "tray", "weeing", "spraying", "scratching", "scratch", "hissing", "fighting",
                 "growling", "meowing at night", "yowling", "sick", "vet",
                 # purring is its own answer and it is a good one ("purring is not only
                 # happiness"), so a question about purring keeps it
                 "purr", "purrs", "purring", "knead", "kneading", "headbutt", "head bump",
                 # a cat that is scared or hiding wants somewhere to get to, which is the
                 # hiding row's answer, and "my cat is friendly" is a person describing a cat
                 "scared of me", "afraid of me", "frightened of me", "is friendly", "so friendly")),
    # "kitten" is not "cat" to a word list, and a kitten that shreds the sofa is the same
    # question: "my kitten keeps scratching the furniture" was a plain ack once the wood-repair
    # row stood down for cat words.
    entry("cat-scratching", (("cat", "cats", "kitten", "kittens"),
                             ("scratch", "scratches", "scratching", "scratched", "claw", "claws",
                              "clawing", "sofa", "furniture", "carpet",
                              # A bare "how do i stop her doing it" after a scratching turn is
                              # the same question, and the words are the ones a person repeats,
                              # not a new subject: with these the follow-up reaches this answer
                              # rather than nothing.
                              "stop her doing", "stop him doing", "stop it doing",
                              "stop doing it",
                              # the rest of the furniture a cat is told off for, and the two
                              # phrases it comes in: "my cat scratches the table" was answered by
                              # the ants, which key the worktop, and a phrase is worth more
                              "curtain", "curtains", "wallpaper", "banister", "bannister",
                              # not the stairs: "my cat struggles with the stairs" and "my cat
                              # struggles with the stairs" are the arthritis question, and a
                              # bare stair noun here stole them ("my cat struggles with the
                              # stairs" got the scratching post, and the repo's own
                              # test_a_stiff_cat_is_still_arthritis failed). A claw line on the
                              # stairs still reaches this row on "cat" and "scratching".
                              "rug", "settee", "couch",
                              # "worktop" on its own is the cat that pushes things off it, and
                              # that is the cat-pushes-things row: "my cat swipes things off the
                              # worktop" and "my female cat knocks things off the worktop" were
                              # both told to buy a scratching post. The surface belongs to this
                              # row only when the verb is the claw.
                              "scratches the table", "scratching the table",
                              "scratch the table", "scratches the worktop",
                              "scratching the worktop", "scratch the worktop")),
          ("Cats scratch to mark territory, so put a tall scratching post right next to the "
           "corner she uses, and make the sofa less appealing with a throw or double-sided tape "
           "for a few weeks. A post with height lets her do it properly."),
          # a cat being sick on the carpet is a sick cat, not a scratching-post question
          avoid=("sick", "vomit", "vomiting", "vomited", "sicked", "throwing up", "threw up",
                 "puke", "pukes", "puked", "puking", "brings up", "brought up",
                 # hair on the furniture is shed, not scratched: "how do i get rid of cat hair
                 # on the sofa" named a sofa and a claw-shaped subject and got a scratching post
                 "hair", "hairs", "fur", "fluff", "shed", "sheds", "shedding", "hoover",
                 "vacuum", "vacuuming", "lint", "lint roller",
                 "poo", "pooed", "poops", "pooped", "pooping", "pooing", "messed", "messes",
                 "messing", "soiled", "wee", "peed", "diarrhoea", "blood",
                 # a cat that weeds on the sofa is a toilet and tray question, and "sofa" in this
                 # key gave it a scratching post: the accident words are the whole of that ask
                 "weed", "wees", "weeing", "pee", "pees", "peeing", "urine", "urinating",
                 "spray", "sprays", "spraying", "sprayed", "marking", "litter tray",
                 "accident", "accidents",
                 # a scratch on a person is a wound, and it was being answered with a post and
                 # a throw: washing it under the tap is the answer
                 "treat", "treating", "wash", "washed", "clean it", "infected", "infection",
                 "tetanus", "plaster", "bandage", "swollen", "red line", "me", "my hand",
                 "my arm", "my face", "my leg", "my finger", "bleeding", "bled",
                 # and a cat scratching itself sore is a skin question, not a post
                 "himself", "herself", "raw", "sore", "itchy", "itching", "so much",
                 "all the time", "bald patch", "fleas",
                 # the sofa lines are this row's own answer, and a cat that cannot jump on the
                 # sofa is the arthritis question, not a scratching one
                 "jump", "jumping", "cant jump", "stiff", "stiffness", "stiff legs",
                 "arthritis", "limping", "limp", "slow to eat", "slow eater", "reluctant to eat",
                 "not eating", "drinking",
                 # scraping the floor or the bedding before lying down is the general row's
                 # answer, and it says why dogs and cats do it; this row has only the post
                 "floor", "floors", "rug", "rugs", "bedding", "lying down", "before lying",
                 "mattress", "mat",
                 # hair on the sofa is a cleaning job: "how do i get cat hair off a sofa" was
                 # this row's post and throw, because the cat and the sofa are both in it
                 "hair", "hairs", "fur", "pet hair", "cat hair", "dog hair", "lint",
                 "hoover", "vacuum", "brush off",
                 # choosing kit for a new kitten is the supplies question: "do i need a
                 # scratching post or will cardboard do for a new kitten" is a buy decision,
                 # not a why-does-she-scratch one, and the kit row answered it before this
                 # row's word "scratching" got heavier than it
                 "scratching post or", "or will cardboard", "cardboard",
                 # a claw that wants cutting is the grooming question, not the furniture, and
                 # "how do i clip my cat's claws" keys this row on "claw": the clipping words
                 # are the whole of that ask, and an ear or a bald patch is the skin question
                 "ears", "ear", "bald", "clip", "clipping", "clipped", "clippers",
                 "trim", "trimming", "trimmed", "nails", "nail", "quick", "cut the claws",
                 "cutting", "scratched me", "scratches me", "scratching me",
                 "scratched my hand", "on my hand",
                 # a line asking how to say something to the owner is a conversation, not a
                 # post: "how do i tell my friend her cat scratched my child" got a post
                 ) + _SAYING_FRAME,
          # the post-and-throw answer is written for this exact question, so it wins the tie
          # against the general pet-scratching row
          bias=4),
    # A cat's claw in a person is the one cat-scratching question that is not about the cat: "how
    # do i treat a cat scratch" and "cat scratch on my hand" were told to buy a scratching post and
    # then, once that row stood down, shrugged at the vet's desk. The two shapes are the phrase the
    # wound comes in, so they never meet the furniture words.
    entry("cat-scratch-wound", (("cat scratch", "cat scratches", "cat scratched",
                                 "kitten scratch", "kitten scratched", "scratched by a cat",
                                 "scratched by the cat", "cat bite", "cat bites", "cat bit me",
                                 # the person is the thing being scratched, and the line says so
                                 # without ever saying "cat scratch": "my cat is scratching my
                                 # hand" went to the ack that asks how long she has been with you
                                 "scratching my", "scratching me", "scratched me",
                                 "scratching your", "scratches me"),
                                ("treat", "clean", "wash", "washed", "infected", "infection",
                                 "swollen", "sore", "bleeding", "plaster", "dressing",
                                 "on my hand", "on my arm", "on my finger", "my hand", "my arm",
                                 "finger", "went red", "hot",
                                 # is it serious, and who looks at it: "is a cat scratch
                                 # dangerous" and "should i see a doctor for a cat bite" both had
                                 # another row's answer on them
                                 "dangerous", "serious", "doctor", "gp", "a&e", "hospital",
                                 "look at it", "get it checked", "checked out",
                                 "by a cat", "by the cat",
                                 # "my cat scratches me" names no body and no wound word, and
                                 # with the clippers no longer claiming it the play answer had
                                 # it; a cat's claw in a person is the wound, and the stroking
                                 # line is held out above so it keeps the over-stimulation answer
                                 "scratches me", "scratching me", "scratched me")),
          # The words a cat scratch most needs are main's own and they stay: five minutes under
          # the tap, the two-week window, the glands and the GP. Cat scratch disease is the whole
          # reason this row exists, so a shorter wash and a shorter watch are the wrong answer
          # however well the row routes.
          ("Wash a cat scratch under running water for five minutes with soap, pat it dry and "
           "cover it with a plaster, and do not use antiseptic or alcohol on it. Cat scratches "
           "are the ones that matter: watch for swelling, a red line spreading up the arm, "
           "swollen glands or a fever over the next two weeks, and see a GP if any of those "
           "appear. Get a bite, a deep puncture or a scratch near the eye looked at the same "
           "day, and check your tetanus is up to date."),
          avoid=("sofa", "furniture", "carpet", "post", "wallpaper", "curtain", "curtains",
                 "table", "chair", "door", "doors", "scratching post",
                 # A cat that bites hands is playing or is over-stimulated, and the advice is
                 # about the play, not about washing: "my cat bites my hands" was reaching this
                 # row. The present tense is what is held out, so a bite that has landed ("my cat
                 # bit my hand") keeps the wound answer.
                 "bites my hands", "biting my hands", "bites hands", "bites my fingers",
                 "biting my fingers", "bites my ankles", "bites my feet", "play biting",
                 "play bites", "when i stroke", "when i pet", "when i pick him up",
                 "when i pick her up"),
          # The person's own scratching is not a claw: see _an_animal_did_it above.
          guard=_an_animal_did_it,
          # "i got scratched by a cat" is two ordinary words and tied with the furniture row,
          # which reads the same cat and the same verb: a wound is the one with a person in it.
          # The tie is real on main, which raised the furniture row to 4 for its own reasons, so
          # this row has to sit above it to answer the lines it exists for.
          bias=5),
    # "kitten" is not "cat" to a word list, and "my kitten wont use the litter tray" was a plain
    # ack: the one line a new owner most needs answered is the one that never reached this entry.
    entry("cat-litter", (("cat", "cats", "kitten", "kittens"),
                         # "house train" and "toilet train" are how a person who has had a puppy
                         # says it, and a kitten is trained the same way, on a tray: the line was
                         # "Your vet is the one to ask" while the tray answer sat right here.
                         ("litter", "tray", "toilet", "weeing", "peeing", "pee", "pees",
                          "outside the tray",
                          "smells", "smelly", "stinks", "stink", "odor", "odour", "pooed",
                          "pooing", "pooped", "poop", "messing",
                          # the same accident in the words people actually use, because the
                          # bed rows stand down on them and there was nothing else to catch
                          # the line: "my cat peed on my bed" was a reflection echo, and
                          # "my cat keeps spraying in my bedroom" a nod.
                          "pee", "peed", "peeing", "piddle", "piddled", "urine", "urinating",
                          # "weed" is how people type it - "my cat weed on the rug" was a
                          # greeting, and "my cat weed on the bed" reached the garden card,
                          # because "weed" is a plant and "bed" a flower bed
                          "weed", "wees", "wee'd", "went for a wee", "did a wee",
                          "wet", "wets", "wetting", "wet the bed",
                          "spray", "sprays", "spraying", "sprayed",
                          "house train", "house training", "house trained",
                          "toilet train", "toilet training", "toilet trained")),
          _litter_reply,
          # a cat that is weeing more often, or in the wrong place, is a vet question about
          # cystitis, diabetes or kidneys, not about the tray: the thirst entry answers it
          avoid=("put down", "to sleep", "euthanised", "euthanized", "died", "dying", "dead",
                 "passed away", "death",
                 "weeing more", "peeing more", "weeing a lot", "peeing a lot", "wees a lot",
                 "pees a lot", "urinating", "drinking more", "drinking a lot", "drinks a lot",
                 "thirsty", "spraying", "straining",
                 # a cat trying and getting nothing out is a blocked bladder, not a tray question
                 "trying to wee", "trying to pee", "nothing comes", "nothing coming",
                 "no wee coming", "keeps trying", "weeing blood", "cystitis",
                 "passing nothing", "nothing out") + LITTER_FINE),
    entry("cat-urine",
          (("cat", "cats", "kitten", "kittens", "tom", "tomcat"),
           ("straining", "straining to wee", "straining to pee", "cant wee", "cannot wee",
            "cant pee", "cannot pee", "cant urinate", "cant pass urine", "blocked",
            # where it landed is not what is wrong: "my cat is peeing on the bed" is a tray and
            # behaviour question, and the cystitis answer is confidently about something else
            "weeing blood", "blood in his wee", "blood in her wee",
            "blood in the urine", "cystitis", "urine infection", "crying when he wees",
            "crying when she wees", "spraying",
            "trying to wee", "trying to pee", "nothing comes", "nothing coming",
            "no wee coming", "keeps trying", "passing nothing", "nothing out")),
          _cat_urine, bias=2,
          # how to clean a smelly tray, a cat drinking or weeing "a lot" (the thirst entry) and a
          # cat that will not use the tray at all are three other answers
          # "spraying" is the marking sense, and its forms reach a can of fly spray: "is the spray
          # safe with a cat" was answered with cystitis, because spray reads as spraying. The
          # product is the household-chemical answer's line, so the shapes that mean a spray can
          # are stood down here and the marking ones are not.
          avoid=("smell", "smelly", "stinks", "stink", "odor", "odour", "clean", "wash",
                 "weeing more", "peeing more", "weeing a lot", "peeing a lot", "urinating a lot",
                 "drinking more", "drinking a lot", "drinks a lot", "thirsty",
                 "wont use", "won't use", "not using the litter", "litter tray",
                 "the spray", "a spray", "fly spray", "insect spray", "ant spray", "wasp spray",
                 "flea spray", "bug spray", "mosquito spray", "air freshener", "aerosol",
                 "spray safe", "safe with", "safe around", "i sprayed", "after spraying")),

    # The turn after the vet's clear result. "i did take her to the vet, they said no infection"
    # was answered by the litter card's own last sentence - "a vet check comes first, because it
    # is often a urine infection" - which tells a person who has just had the check done to go
    # and have it done. The result is the question, and it moves the answer to behaviour.
    entry("after-a-clear-urine-result",
          (("vet", "vets", "vet's", "the vets", "test", "tests", "results", "sample", "checkup",
            "check up", "check-up"),
           ("no infection", "not an infection", "isnt an infection", "isn't an infection",
            "wasnt an infection", "wasn't an infection", "quiet on infection",
            "came back clear", "come back clear", "comes back clear", "got the all clear",
            "all clear", "nothing wrong", "nothing there", "nothing found",
            "clear of infection", "no crystals", "no stones")),
          _after_a_clear_urine_result, bias=2,
          # a person's own result is the health card's, and a question about what a result means
          # is not a result that came back
          avoid=("my own", "my blood", "my results", "my test", "my urine", "my sample",
                 "myself", "my son", "my daughter", "my mum", "my dad", "my wife", "my husband",
                 "my partner", "my baby", "my child", "will it be", "would it be", "could it be",
                 "might it be", "should i", "do i need", "when will")),

    # Where the tray goes is not how the tray is cleaned, and it had no row of its own: "where
    # should i put the litter tray" was a shrug, with the placement answer nowhere in the file.
    entry("litter-tray-place",
          ("litter tray", ("where", "put", "place", "position", "corner", "room", "go",
                           "best place", "should it go", "siting")),
          ("A quiet corner away from the food and water, and not next to the washing machine or "
           "a door that bangs, because a cat will not use a tray where she cannot hear trouble "
           "coming. One tray for each floor, somewhere she can leave in two directions rather "
           "than a dead end, and never inside a closed cupboard or under a lid: a tray in the "
           "dark is where the mess starts."),
          # buying one, or how big it is, is a shopping question and not this one
          avoid=("buy", "buying", "cheap", "cheapest", "price", "cost", "online", "order",
                 "how big", "what size", "best litter", "which litter", "wood pellet",
                 "clumping")),
    # --- a cat expecting kittens, and a cat with them --------------------------------------
    # "how long are cats pregnant" was answered with the human fertility card ("trying for a
    # baby is a wait of up to a year at under 35"), "my cat is pregnant" with "Lovely to hear.
    # Enjoy it!", "my cat is in season" and "my cat had kittens" with a plain ack, and "how do i
    # look after newborn kittens" with the cat-and-child card about a toddler. A pregnancy is
    # nine weeks and the litter needs three answers, so there are three rows here.
    entry("cat-pregnant",
          (("cat", "cats", "kitten", "kittens", "queen", "mother cat", "mum cat", "mom cat"),
           ("pregnant", "pregnancy", "how long are cats pregnant", "how long is a cat pregnant",
            "how long do cats stay pregnant", "gestation", "expecting kittens",
            "weeks pregnant", "how many weeks", "due date", "when is she due", "due in",
            "due next week", "due soon", "due any day",
            "in season", "in heat", "came into season", "keeps calling",
            # A cat on heat "is calling", and the bare word had no way in: the key phrases here
            # all carry a second word, so "my cat is calling" was a shrug. The word alone also
            # reaches "called" through the loose matcher, which is what the naming guard above
            # is for.
            "calling",
            "calling for a mate", "calling at night", "calling all night",
            "calling and rolling", "yowling at night",
            "on heat")),
          ("Cats are pregnant for about nine weeks, 63 to 65 days, and the vet usually wants to "
           "see her about three weeks in to confirm it. Feed her kitten food from around four "
           "weeks in because she needs the extra, and put a box somewhere quiet and warm with "
           "towels in it so she has a den to choose; she will pick her own spot if you do not. A "
           "cat in season is not ill and not in pain - the calling and rolling is hormones - but "
           "she will get out of the door given the chance, and the litter arrives nine weeks "
           "later, so book the spay and keep her in until it is done."),
          # the human fertility row keys "how long" and "are cats pregnant" too and won the tie
          # on its own bias, so the nine weeks has to be said with the louder voice
          bias=3,
          # a pregnant person is not a pregnant cat, and a cat that is being sick, not eating or
          # losing weight is the vet question, not a due date
          avoid=("i am", "im pregnant", "i'm pregnant", "my wife", "my girlfriend", "my partner",
                 # a person's period is named by the phrases below; the bare word stood this row
                 # down for a cat's own "gestation period", which is the ordinary way of asking,
                 # and the human cycle card answered a question about a cat with 21 to 35 days
                 "my daughter", "my son", "human", "trying for a baby", "ivf",
                 "my period", "period pain", "period cramps", "late period",
                 "my rabbits", "rabbit", "guinea pig", "dog", "bitch", "sick", "vomiting",
                 "not eating", "losing weight", "bleeding", "litter tray", "weeing",
                 # "my cat is 14 and has started yowling at night" is an old cat, and the answer
                 # is not a due date: the age stands the pregnancy card down however the chat
                 # carries the yowling forward
                 "years old", "year old", "is 12", "is 13", "is 14", "is 15", "is 16", "is 17",
                 "12 years", "13 years", "14 years", "15 years", "16 years", "17 years",
                 "old cat", "older cat", "elderly", "senior", "geriatric", "spayed",
                 "neutered", "already spayed"),
          # the key's "calling" is a cat on heat, and "called" is the same word to the matcher,
          # so a named cat is not an expecting one. A line can carry both ("my cat is called tom
          # is he in season"), and then the season words win. A row carries one guard, so the
          # two readings are made here: see _not_a_named_cat and _a_name_is_being_given.
          guard=lambda understood: (_not_a_named_cat(understood)
                                    and not _a_name_is_being_given(understood))),
    entry("cat-kittens-new",
          (("cat", "cats", "kitten", "kittens", "queen", "mother cat", "mum", "mom"),
           ("had kittens", "had a litter", "had her kittens", "newborn", "newborns",
            "gave birth", "giving birth", "just had kittens", "a litter of",
            "how do i look after", "how do i care for", "keeping them warm",
            "rejected", "wont feed them", "wont feed her kittens", "abandoned",
            "when can they leave", "leave their mother", "when can kittens leave",
            "eight weeks", "hand rearing", "hand rear", "bottle feed kittens",
            "orphan kittens", "orphaned")),
          ("Leave them with her and keep the room warm and quiet: for the first week she does "
           "everything, and handling is mostly weighing - a kitchen scale in a box, once a day, "
           "written down, because a kitten that is not gaining is the one that needs help. She "
           "wants kitten food and water within reach of the nest, and a litter tray she can get "
           "to in two steps. Kittens should stay with her until eight weeks, and never leave "
           "before then. If she leaves one out, will not settle on it or it feels cold, ring the "
           "vet that day; a mother cat that stops feeding them needs the vet too, not a bottle "
           "from the kitchen."),
          # "how do i look after newborn kittens" was the cat-and-child row: that row keys a baby
          # in the house, and this one is a litter on the floor
          bias=2,
          # "mum" and "mom" are in the key for one phrase, "mum cat", and on their own they are
          # every person asking about their mother: "how do i look after my mum who has dementia"
          # was told to leave the kittens with her and weigh them on a kitchen scale. The line has
          # to name a cat or a litter for this row to answer it, and then the family rows have
          # their line back.
          guard=lambda understood: (_a_cat_in_the_line(understood)
                                    and _a_litter_is_what_is_asked_about(understood)),
          # a cat and a new baby is a different answer, and so is a cat left alone all day. A
          # kitten that bites hands is the play answer, and a kitten-kit shopping line is the
          # list of things to buy: "my new kitten is biting me" was "leave them with her" here
          # until the biting and the shopping words were held out.
          avoid=("baby", "toddler", "child", "children", "grandchild", "toddler's", "human",
                 "pregnant", "alone all day", "out all day",
                 "biting", "bites", "bite", "nip", "nips", "nipping", "chewing", "hands",
                 "scratching post", "cardboard", "buy", "buying", "do i need", "will i need",
                 "what do i need", "kit", "starter", "toys", "toy", "litter tray", "bowls",
                 "play")),
    # A constipated cat was "Thanks for telling me", which is the coldest answer to somebody
    # with a cat straining in a tray. Water, wet food and a two-day limit is the whole answer.
    entry("cat-constipated",
          (("cat", "cats", "kitten", "kittens"),
           ("constipated", "constipation", "hasnt pooed", "hasn't pooed", "not pooing",
            "wont poo", "won't poo", "cant poo", "can't poo", "straining", "straining in the tray",
            # the tray on its own is the litter-tray question, and it took "my cat wont use the
            # litter tray" to the water-and-pumpkin answer; only a tray with nothing in it is
            # constipation. "litter tray" as a key word also told a tray that smells and a cat
            # that will not use one about constipation, so the tray is only named with what is
            # not in it, and "going in the tray" is the two tray questions' own word.
            "hard poo", "hard stools", "dry poo", "no poo", "blocked up",
            "nothing in the litter tray", "nothing in the tray", "not pooing in the tray",
            "no poo in the tray", "going in the tray")),
          ("A constipated cat needs water rather than a remedy: wet food twice a day, a bowl of "
           "water away from the food and a fountain if she likes running water, and a few "
           "teaspoons of plain cooked pumpkin in her food. A cat that has passed nothing for two "
           "days, or is straining in the tray and producing nothing, or is being sick with it, is "
           "a vet visit today: a blocked cat is an emergency, and long-standing constipation needs "
           "a vet's laxative rather than a human one."),
          bias=1,
          # a cat weeing outside the tray, or straining to wee and passing nothing, is the
          # cystitis answer and it is the more urgent one
          avoid=("wee", "wees", "weeing", "pee", "pees", "peeing", "urine", "urinating",
                 "spray", "spraying", "blood", "cystitis", "outside the tray", "newborn",
                 "kittens are", "litter training",
                 "smell", "smells", "smelling", "smelly", "stinks", "stink", "odor", "odour",
                 "wont use", "won't use", "not using", "wont go", "won't go")),
    entry("cat-hairball",
          (("cat", "cats", "kitten", "kittens"),
           ("hairball", "hairballs", "hair ball", "hair balls", "furball", "furballs",
            "brings up hairballs", "bring up hairballs", "brought up a hairball",
            "coughing up", "retching", "hacking", "sick after grooming", "tube of hair")),
          ("Hairballs are normal a few times a year in a cat that grooms a lot, and the fix is "
           "brushing rather than a paste: comb her daily through the moult with a metal comb so "
           "the loose hair goes in the bin instead of down her throat, and keep her water and wet "
           "food up because a dry diet alone makes them likelier. Retching that brings nothing up, "
           "or hairballs more than about once a month, is the vet rather than a remedy: it can be "
           "over-grooming from fleas or stress, or something blocking the gut."),
          bias=1,
          # prey brought in is not a hairball, and a cat being sick with anything else is the vet
          avoid=("bird", "birds", "mouse", "mice", "rat", "rats", "prey", "brought in",
                 "on the step", "doorstep", "diarrhoea", "blood", "poison", "lily", "bitten")),
    entry("cat-brings-prey",
          (("cat", "cats", "kitten", "kittens"),
           # the prey names do the work; "left" and "found" alone are how people talk about a
           # cat that is left alone or a cat that was found, which is not this answer
           ("bird", "birds", "mouse", "mice", "rat", "rats", "vole", "voles", "prey",
            "bring", "brings", "bringing", "brought", "caught", "catches",
            "on the step", "on the doorstep")),
          # "in the house" keyed this entry, so "my cat is weeing in the house" was read as a cat
          # bringing prey in: the prey word has to be there now, and a toilet line stands down
          ("A quick-release collar with a bell cuts the hunting down, and keeping her in from "
           "dusk until morning misses the hours most of it happens; a garden bird feeder on a "
           "pole away from cover helps too. She is bringing food to the household rather than "
           "being naughty, so take the bird away in gloves and don't scold her for it."),
          # a cat that has died is pet-loss, and a bird that died in the garden is not this.
          # "is a cat alright if i'm out all day and it's left alone" is a should-i-get-one
          # question: "left" is how the prey gets on the step, and how a cat gets left alone too.
          avoid=("died", "dying", "passed away", "funeral", "put down", "to sleep",
                 "euthanised", "euthanized",
                 "wee", "wees", "weeing", "pee", "pees", "peeing", "spray", "spraying",
                 "litter", "tray", "toilet", "poo", "pooing", "sick", "vomit",
                 # "when im out all day" is how a hunting line is worded, so the leaving
                 # phrases have to be the ones only a should-I-get-one question uses.
                 "alone all day", "left alone all day", "out all day and", "on its own all day",
                 "get a cat", "should i get", "alright if i", "ok to leave", "worth getting")),
    entry("dog-brings-prey",
          (("dog", "dogs", "puppy", "puppies", "terrier", "spaniel", "labrador"),
           ("bird", "birds", "mouse", "mice", "rat", "rats", "rabbit", "rabbits", "squirrel",
            "squirrels", "pheasant", "prey", "bring", "brings", "bringing", "brought",
            "caught", "catches", "killed", "kills", "killing", "left", "leaves", "leaving",
            "found", "finds", "dropped", "deposits", "presents")),
          ("That is hunting instinct, not a health problem, and it is worst at dusk and dawn, so "
           "keep him in then and put a bell on his collar. Teach a rock-solid \"leave it\" with "
           "treats and swap every carcass for something better: scolding him for bringing it to "
           "you only teaches him to eat it out of sight. Clear it up in gloves."),
          # a dog that has died is pet-loss; a dog tired after a walk is not this
          avoid=("died", "dying", "passed away", "put down", "to sleep", "euthanised",
                 "euthanized", "tired", "exhausted", "knackered",
                 # "i found fleas on my dog" is a health question, not a hunting one
                 "flea", "fleas", "tick", "ticks", "worm", "worms")),
    # "my cat is dead tired" is about the cat, not about the person: 'dead' is how people say
    # 'very'. A sleepy cat is normal, so the answer says what is not.
    entry("cat-tired", ("cat", ("tired", "sleepy", "lethargic", "lazy", "no energy",
                                "sleeps all day", "sleeping all day", "sleeps a lot",
                                "always sleeping", "seems flat", "gone flat", "flat out")),
          ("Cats sleep 12 to 16 hours a day, so a sleepy cat is normal, especially after a big "
           "meal or a warm afternoon. What is not normal: a cat that stops eating, hides away, "
           "or is floppy when you pick her up, which needs a vet the same day."),
          # "Cat or dog for a flat with no garden?" says "flat" about a home, not a feeling: the
          # should-I-get-one line is the choice entry's question.
          avoid=("garden", "flat with", "apartment", "cat or dog", "or a dog", "or dog",
                 "which pet", "which one", "should i get", "better pet", "no garden",
                 # how much a cat sleeps is this row; where she should sleep is the bed's place
                 "where should", "where to", "where do i", "where can", "where does",
                 "which room", "what room")),
    entry("dog-tired", (("dog", "dogs", "puppy", "puppies"),
                        ("tired", "exhausted", "knackered", "shattered", "worn out",
                         "sleeping", "sleeps", "sleepy", "lethargic", "lazy", "no energy",
                         "sleeps all day", "sleeping all day", "sleeps a lot",
                         "always sleeping", "seems flat", "gone flat", "flat out")),
          ("After a long walk or a big day that is normal, so let him sleep it off with water "
           "down and feed him later than usual. If he is still flat tomorrow, or will not eat or "
           "drink, that is a vet visit."),
          # a sleepy dog is this row; where the dog should sleep is the bed's place
          avoid=("where should", "where to", "where do i", "where can", "where does",
                 "which room", "what room")),

    # The puppy's dates had no row at all: "when do puppies get their injections" and "when can
    # my puppy go out" were a search hedge, the toilet-training steps and the kit list, while the
    # kitten's equivalent had its own answer. The dates are two and they decide when the door
    # opens, which is the whole of what people ask.
    entry("puppy-vaccinations",
          # "puppy" and "puppies" only: a grown dog's booster is the annual-check row's, and a
          # cat's or a kitten's dates are `kitten-outside`'s
          # the thing asked about, not the shape of the asking: a jab word, or the walk the
          # jabs unlock. "puppy" plus "when" was enough before, and it took twelve typed
          # "when ... puppy" lines to the two dates - when do puppies stop biting, stop chewing,
          # lose their baby teeth, calm down, start on solid food, have a bath, go to the
          # groomer, get their first walk (firm-sheep, #7631).
          (("puppy", "puppies"),
           ("jab", "jabs", "injection", "injections", "vaccination", "vaccinations", "vaccine",
            "vaccines", "vaccinated", "go out", "go outside", "outside", "out and about",
            "take him out", "take her out", "take my puppy out", "take the puppy out",
            "due", "jab due", "jabs due")),
          "A puppy has two injections: the first at six to eight weeks, usually done by the "
          "breeder, and the second at ten to twelve weeks, and he can go out for walks a week "
          "after the second one - around twelve to thirteen weeks. Until then he can be carried "
          "outside, meet people and play on clean floors indoors, because the socialising window "
          "shuts around sixteen weeks and waiting for the last jab to start it is a mistake. "
          "Book the second one as soon as you get him home.",
          # a kitten's dates, a grown dog's booster, the price and the worming are other answers
          # it beats the general check-up card: a line that says when the puppy's jabs are due
          # wants the two dates, not "once a year"
          bias=4,
          avoid=("kitten", "kittens", "cat", "cats", "rabbit", "hamster", "guinea pig", "ferret",
                 "booster", "boosters", "annual", "yearly", "every year", "how much", "cost",
                 "costs", "price", "microchip", "worming", "worm", "fleas", "flea", "neutering",
                 "neutered", "spay", "spayed",
                 # the care questions that a bare "when" used to pull in here, so the shape can
                 # come back without taking them again
                 "biting", "bites", "bite", "chewing", "chew", "teeth", "baby teeth", "calm",
                 "training", "train", "groomer", "grooming", "bath", "solid food", "weaning",
                 "sleep", "sleeping", "crying", "cries", "first walk", "meet other dogs",
                 "mix with", "socialis", "litter", "toilet")),

    # A grown dog's booster was the child-seat law and then the shopping list, and it is one of
    # the two vet dates people actually ask about.
    entry("dog-booster",
          (("dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens"),
           # no bare "when": "when can a kitten go outside" is the kitten's date, and with
           # "kitten" and "cat" in the key it was read as a booster question. No bare "how
           # often" either: that word is how every care question is asked, and it took "how
           # often should i walk my dog", "how often should i feed my dog", "how often should i
           # trim my dogs nails", "how often should i groom my dog" and "how often should i wash
           # my dog" off their own answers. A booster line says the booster.
           ("booster", "boosters", "annual", "yearly", "every year", "each year", "jab",
            "jabs", "top up", "due")),
          "Once a year for a dog, and a cat the same: the leptospirosis part of a dog's booster "
          "has to be every year, while the distemper, hepatitis and parvovirus parts are often "
          "given every three years, so ask the vet which you are due. Kennel cough is the extra "
          "one worth having if he goes to a groomer, day care or a boarding kennel.",
          # the child's booster seat, the jabs a puppy has in its first weeks, and the price are
          # other answers
          avoid=("child", "children", "baby", "toddler", "seat", "car seat", "isofix", "car",
                 "trolley", "first", "six to eight weeks", "second", "outside", "outdoors",
                 "out", "garden", "litter", "travel", "pet passport",
                 "how much", "cost", "costs", "price",
                 # the everyday care questions are asked "how often" and each has its own row
                 "walk", "walks", "walking", "feed", "feeds", "feeding", "fed", "wash", "washing",
                 "bath", "bathe", "groom", "grooming", "brush", "brushing", "nails", "claws",
                 "trim", "trimming", "clip", "clipping", "flea", "fleas", "worm", "worming",
                 "microchip", "chipped",
                 # a puppy's own two dates are `puppy-vaccinations`' question: this row is the
                 # annual booster of a grown animal
                 "puppy", "puppies", "kitten", "kittens"),
          # a booster line wants this row's detail - which part of the booster is yearly and
          # which is every three years - over the general check-up card that main added later
          bias=5),

    # The first time a kitten goes out is a date, not a shrug, and three ways of asking it -
    # "when can a kitten go outside", "can i let my cat outside", "should i let my kitten out" -
    # were a vet punt and two hedges. The vaccinations are the answer, so they lead.
    entry("kitten-outside",
          (("kitten", "kittens", "cat", "cats"),
           ("outside", "outdoors", "out", "garden", "outdoor")),
          ("A kitten goes out a week after her second vaccination, which is usually around four "
           "months, and not before, because she has no immunity to anything until then; a grown "
           "cat that is vaccinated and chipped can go out now. Microchip first either way (it is "
           "the law from 20 weeks in the UK), then let her out hungry, an hour before a meal, so "
           "the rattle of the biscuits brings her back. Go with her for the first few trips, keep "
           "them short, and keep her in at night: most cats are lost in their first month out, "
           "in the dark."),
          ask=("outside", "outdoors", "out", "garden"),
          # a cat that has escaped, or is going outside the tray, is a different worry
          avoid=("litter", "tray", "got out", "escaped", "ran out", "ran away", "gone missing",
                 "missing", "lost", "wont come back", "hit by", "road", "dead", "died",
                 "put down", "euthanised", "euthanized", "wee", "poo", "sick", "vomit")),

    # "Where should i put the cat bed" is the same shape of question as the tray, and it reached
    # the garden's mulch answer because "beds" is a form of "bed". A cat chooses height and a
    # view, so the answer is where she already sleeps, not the middle of the floor.
    entry("cat-bed-place",
          (("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies"),
           ("bed", "beds", "basket", "blanket"),
           ("where", "put", "place", "best", "should it go", "right place", "wont use",
            "wont go in", "wont sleep", "wont settle", "ignores", "new bed", "sleep in",
            # Where a pet sleeps is the bed's place, and it is the way people ask it: "where
            # should my dog sleep", "where should my puppy sleep" and "where should my cat
            # sleep at night" were a dog-tired paragraph, a vet punt and the cat's sleep hours.
            # The where-words are what carry the question, and the two sleepy-pet rows below
            # stand down for them, so "my dog sleeps all day" keeps the tiredness answer.
            "where should", "where do i", "where does he", "where does she", "where can",
            "where would", "which room", "what room")),
          _where_the_pet_sleeps,
          # the bed word has to be there. Without the gate the rowed read "what litter is best for
          # cats" (cat + best) and "my kitten wont use the litter tray" (kitten + wont use), and
          # took two tray questions away from the tray answer.
          # and the where-words are the gate for a sleeping place, because the line that asks
          # where a dog should sleep never says the word bed
          ask=("bed", "beds", "basket", "blanket", "where should", "where do i", "where can",
               "where does", "which room", "what room"),
          # the garden's mulch answer is the one this line reached before, so the garden words
          # are fenced here rather than in the garden row
          # a bed that is the wrong place to sleep is not a bed somebody weed on: where the
          # tray goes is the litter row's answer, and "my cat is peeing on the bed" was being
          # told to move the bed to a wardrobe
          avoid=("garden", "flower", "border", "mulch", "soil", "poo", "pooing", "digging",
                 "dig", "flowerbed", "lawn", "weed", "weeds", "hutch", "cage", "shed",
                 # what a cat carried onto the bed is the hunting answer's question:
                 # "my cat leaves dead mice on the bed" was being told where to put a cat bed.
                 "mouse", "mice", "rat", "rats", "vole", "voles", "bird", "birds", "prey",
                 "brings", "bringing", "brought", "caught", "catches", "killed", "kills",
                 "dead", "carcass", "hunting", "hunts",
                 # a bed is not for the car, and where a dog eats is the bowl's place:
                 # "where should my dog sleep in the car" and "where should my dog eat" were
                 # being handed the bed's answer on the where-words alone.
                 "in the car", "the car", "car boot", "eat", "eats", "eating", "food",
                 "feed", "feeding", "bowl", "bowls", "dinner", "kennel", "at work",
                 "while at work", "holiday",
                 "wee", "wees", "weeing", "peed", "pee", "pees", "peeing", "poos", "pooped",
                 "poop", "urine", "spraying", "sprayed", "puddle", "puddles", "litter", "tray",
                 # This row places the bed a pet is bought. The bed you sleep in, and the sofa,
                 # are where the pet is not wanted, and that is the furniture row's question.
                 "in my bed", "on my bed", "in our bed", "on our bed", "my sofa", "my couch",
                 "my settee", "off the sofa", "off the couch", "off the bed",
                 "sleeps in my", "sleeps on my", "sleeping in my", "sleeping on my")),
    # The human bed and the sofa are not the dog's own bed. "my dog sleeps on my bed" was given
    # the cat tower's height and a view, and "my dog wont get off the sofa" the upholstery stain
    # card, because the row that holds the one-rule routine is fenced against "sleep" and "slept"
    # (a dog that will not sleep is the night-toilet row's line). The furniture keeps its own row.
    entry("dog-on-the-furniture",
          # "my dog" is a phrase and so weighs more than the bare word: the sofa's stain card says
          # "get off" too, sits in an earlier module and took "my dog wont get off the sofa" on a tie
          (("dog", "dogs", "puppy", "pup", "puppies", "my dog", "our dog"),
           ("on my bed", "in my bed", "on the bed", "in the bed", "on our bed", "up on the bed",
            "on my sofa", "on the sofa", "on my couch", "on the couch", "on the settee",
            "off the sofa", "off the couch", "off the settee", "off my bed", "off the bed",
            "on the furniture", "on the pillows", "on my pillow", "sleeps on my bed",
            "sleeps in my bed", "sleeping on my bed", "sleeping in my bed", "sleeps on the bed",
            "sleeping on the bed", "sleeps on the sofa", "sleeps on the couch",
            "getting on the bed", "gets on the bed", "getting on the sofa", "gets on the sofa",
            "getting up on the", "gets up on the", "wont get off", "won't get off",
            "wont get down", "won't get down", "wont stay off", "won't stay off",
            "taken over my bed", "taken over the bed", "took over my bed", "taken over the sofa",
            "jumps on the bed", "jumping on the bed",
            "jumps on the sofa", "jumping on the sofa")),
          "Pick the one rule and keep it the same every day: the bed or the sofa is off limits, and "
          "he has a better place of his own - a bed in the same room, a chew in it, a treat every "
          "time he settles there. Say nothing and walk him off by the collar when he tries it, then "
          "praise him on his own bed straight away; a telling-off is still attention, and that is "
          "half of why he keeps getting up. Nobody in the house should let him up \"just this "
          "once\", because that is the lesson he remembers. If you would rather he shared the bed, "
          "put an old blanket where he likes to lie instead, so the fur and the mud land on that.",
          # his own bed bought, cleaned or slept in at night is another answer, and so is anything
          # that happened to him on the furniture: a fall or a limp is a health question
          avoid=("buy", "buying", "bought", "best", "which bed", "what bed", "bed for",
                 "clean", "cleaning", "wash", "washing", "stain", "smell", "smells",
                 "garden", "hutch", "crate", "puppy pad", "toilet", "wee", "wees", "weeing",
                 "weed", "poo", "poos", "pooed", "pooped", "pooing", "peed", "peed on", "mess",
                 "sick", "sicked", "vomit", "vomited", "mess", "mud", "muddy", "paw", "paws",
                 "fell", "fall", "fallen", "jumped off the", "hurt", "limp",
                 "wont sleep", "won't sleep", "wont settle", "won't settle", "cries", "crying",
                 "bark", "barks", "barking", "how often", "chew", "chewed", "scratch",
                 "scratched"),
          bias=1),
    # A rabbit, a guinea pig or a hamster that will not be picked up, flinches, squeals or kicks
    # when it is handled had no answer at all: "how do i pick up a rabbit" and "my guinea pig
    # squeals when i pick him up" were both the search hedge, and "my rabbit is scared of me" was
    # "Ugh, that's a lot to carry". The small pets are picked up differently from a cat or a dog,
    # and a flinch that is new is a sore place rather than a training problem.
    entry("small-pet-handling",
          (("rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs",
            "cavy", "hamster", "hamsters", "gerbil", "gerbils", "rat", "rats",
            "chinchilla", "chinchillas", "ferret", "ferrets"),
           # the phrase with the article in it, because the cooking rows take any "how do i" line
           # with an animal in it: "how do i hold a rabbit" was the braise-or-roast card
           ("pick up", "picks up", "picking up", "pick up a", "pick up my", "pick up the",
            "picking up a", "picking up my", "pick him", "pick her", "pick them",
            "picked up", "lift", "lifting", "lifts him",
            "hold", "holds", "holding", "hold a", "hold my", "hold the", "holding a",
            "holding my", "holding the", "held",
            "held", "handle", "handled", "handling", "cuddle", "cuddling",
            "flinches", "flinching", "flinched", "squeals", "squealing", "squealed",
            "squeaks when", "squeaking when", "kicks", "kicking", "kicked when",
            "struggles", "struggling", "squirms", "squirming", "wriggles", "wriggling",
            "scared of me", "scared of us", "afraid of me", "runs away from me",
            "runs off when i", "wont let me pick", "won't let me pick", "wont let me hold",
            "won't let me hold", "hates being picked", "hates being held",
            "being picked up", "being held", "get him out", "get her out")),
          _small_pet_handling,
          # the bite, the cage, the hutch, the hay, the claws and the heat are each their own
          # question, and a pet that is already ill or not eating is the vet's
          avoid=("bite", "bites", "biting", "bit", "bitten", "nip", "nips", "nipping",
                 "cage", "cages", "hutch", "run", "bedding", "clean out", "cleaning out",
                 "litter", "food", "feeding", "feed", "hay", "diet", "water bottle",
                 "claws", "claw", "nails", "teeth", "gnawing", "chewing", "chew",
                 "vet", "ill", "sick", "poorly", "not eating", "stopped eating", "eating",
                 "diarrhoea", "limp", "limping", "lump", "eye", "eyes", "fur", "brush",
                 "bath", "bathing", "heat", "hot", "cold", "weather", "pregnant", "babies",
                 "two", "pair", "another", "company", "alone", "cost", "price", "lifespan",
                 "how long do", "die", "dead"),
          # a plain how-to-hold line about the small rodents is `small-pet-biting`'s, whose
          # answer is written for them; every rabbit, and anything that flinches or squeals, is
          # this card
          guard=_a_plain_hold_is_the_rodents_card,
          # above `small-pet-biting`, which is a tie on the animals and on "pick him up": a pet
          # that will not be handled is this card, and a bite still keeps its own.
          bias=3),
    # A bite from a hamster or a gerbil is fright, not temperament, and "my hamster is biting me"
    # was answered "Noted: your hamster is biting you" - the animal heard, the question dropped.
    entry("small-pet-biting",
          (("hamster", "hamsters", "gerbil", "gerbils", "guinea pig", "guinea pigs",
            "rat", "rats", "mouse", "mice", "chinchilla", "chinchillas"),
           ("bite", "bites", "biting", "bit", "bitten", "nip", "nips", "nipping", "nibble",
            "nibbling", "hold", "holding", "handle", "handling", "pick up", "picking up",
            "tame", "taming", "friendly")),
          ("Wash your hands first so he does not smell of food, and scoop him up in both hands "
           "from underneath: a hand coming over the top is a hawk, and that is what a bite is "
           "usually about. Let him wake up properly before you touch him - a hamster woken from "
           "a deep sleep bites - keep your fingers out of the bars, and give a new one a week to "
           "settle before handling at all. Two or three short goes a day with a treat on the "
           "palm, and put him down the moment he nips, teaches him faster than one long hold."),
          # the lifespan and cost rows and the heatwave row are not this answer
          avoid=("how long", "lifespan", "live", "cost", "price", "cheap", "heatwave", "too hot",
                 "hot", "cold", "die", "died", "dead", "dying", "sick", "ill", "vet",
                 "bedding", "cage", "food", "eat", "eating")),
    # The same question without the animal in it. People leave it out - the tray is obviously
    # theirs - and then the words "litter" and "tray" had nothing to reach: "my litter tray
    # smells" was a shrug and "how do i stop my litter tray smelling" was a search hedge.
    entry("litter-smell", ("litter", ("smell", "smells", "smelly", "stinks", "stink", "odor",
                                      "odour")),
          LITTER_REPLY, avoid=LITTER_FINE),
    entry("cat-sick", ("cat", ("sick", "vomit", "vomiting", "vomited", "threw up", "throwing up",
                               "retching", "sick all night", "keeps being sick",
                               # "my cat puked on the carpet" is the same question, and the
                               # scratching row answered it because the carpet is in its key
                               "puke", "pukes", "puked", "puking", "brings up", "brought up",
                               "sick in the morning", "vomits in the morning")),
          _CAT_SICK_REPLY,
          avoid=("car", "cars", "travel", "journey", "ferry", "boat", "plane", "died", "dying",
                 "dead", "passed away", "put down", "euthanised", "euthanized", "death")),
    # A cat that falls ill is the same question as a dog that falls ill, and it had no row at
    # all: "how do i know if my cat is ill", "my cat seems poorly" and "my cat is unwell" were a
    # shrug, while "is my cat sick" reached the vomiting row. The signs a cat hides are what this
    # answers, and the vomiting, off-food, thirst and limp rows keep their own lines.
    entry("pet-ill", (ANIMALS_ILL, ("ill", "illness", "poorly", "unwell", "not well",
                                    "not himself", "not herself", "not itself", "warning signs",
                                    "poorly cat", "is my cat ok", "is my dog ok", "seems off",
                                    "not right", "off colour", "off color", "not looking right")),
          ("The signs to act on are: not eating for a day, hiding away, breathing fast or with "
           "the mouth open, drinking or weeing far more than usual, a sudden weight loss, a coat "
           "that stops being groomed, or a pet that stops wanting its usual walks or its run "
           "about. Animals hide illness until it is advanced, so any of those in a pet that is "
           "normally lively is a vet call rather than a wait: ring the practice and say what has "
           "changed and when. A rabbit or a guinea pig that stops eating at all is a same-day "
           "call: neither can vomit, and a gut that stops moving is an emergency in hours."),
          # the specific fault rows answer their own line: being sick, going off food, drinking
          # more, a limp, arthritis, a wound
          avoid=("vomit", "vomiting", "vomited", "sick", "threw up", "throwing up", "retching",
                 "off her food", "off his food", "not eating", "stopped eating", "wont eat",
                 "won't eat", "drinking more", "drinking a lot", "thirsty", "limp", "limping",
                 "cut", "wound", "stairs", "stiff", "scratching", "sneeze", "sneezing",
                 "coughing", "poo", "diarrhoea", "diarrhea",
                 # "how do i know if my cat is dehydrated" is the dehydration signs row's, and
                 # the thirst row answers how much a pet drinks
                 "dehydrated", "dehydration", "drink", "drinking", "drinks", "water",
                 "thirsty", "wee", "weeing"),
          bias=1),
    # Introducing a second cat is asked far more often than it is decided: the answer is scent
    # before sight, and weeks rather than days. Nothing in the tables had it.
    # Every phrase here names a cat that is not the first one, because that is what the answer is
    # about: the cat in the next room, the swap of bedding and the door. A bare "kitten" or a bare
    # "should i get" was in this list, and it took every line about a first cat: "should i get a
    # kitten", "should i get a cat flap" and "should i get a cat or a dog" were all told how to
    # introduce a second cat. A line weighing up a cat for the first time is the trade in
    # opinions.py, and the shopping list is the kitten-kit row's.
    entry("cat-second-cat", ("cat", ("second cat", "another cat", "new cat",
                                     "two cats", "introduce", "introducing", "introduction",
                                     "get a friend for", "companion", "get another",
                                     # "can i get a kitten with my older cat" is this question,
                                     # not the shopping list for a first kitten
                                     "older cat", "existing cat", "other cat", "with my cat",
                                     "with my older", "another kitten", "get a kitten with",
                                     # people say "the new kitten" more often than "a kitten":
                                     # "my cat is hissing at the new kitten" found nothing
                                     "new kitten", "the new kitten", "kitten wont",
                                     "kitten keeps", "kittens wont", "kittens keep",
                                     # the two-cat situation said as a feeling: "my cat is jealous
                                     # of the kitten", "we got a kitten and our old cat hates it"
                                     "jealous", "hates the kitten", "old cat hates",
                                     "and our old cat", "kitten and our",
                                     # a hiss or a growl is only this question when the other
                                     # animal is the new one: "my cat hisses at me" is the cat
                                     # saying no to a person, which has its own answer
                                     "at the kitten", "at the new kitten", "at another cat")),
          ("Keep the new cat in one room with a litter tray and water and let the two of them "
           "smell each other through the door for the first few days, swapping bedding and "
           "feeding them on either side of it. Then short, supervised visits and a baby gate, and "
           "back out again before any hissing starts; expect that to take a week or two, and go "
           "at the cats' pace, not yours. Two trays in separate rooms and one high place only the "
           "old cat can reach stop the resource fights."),
          avoid=("ill", "poorly", "lost", "died", "dead", "passed away", "put down", "allergic",
                 # the older-cat check-up row owns "how often should i take an older cat to the
                 # vet", which names an older cat too
                 "vet", "check up", "checkup", "vaccination", "jabs", "vaccines", "how often",
                 "twice a year", "once a year",
                 # a count ask is not the introduction question: "how many cats do i have"
                 # carries "how" and "cats", and would otherwise get the scent-before-sight
                 # paragraph instead of the number the chat was told.
                 "many", "how many",
                 # Choosing whether to take on a rescue or a kitten is not introducing one to
                 # the cat you already have: "should i get a rescue cat or a kitten" was told to
                 # let the two of them smell each other through the door. The words that make
                 # the line a choice hand it to rescue-or-baby.
                 "or a kitten", "or a cat", "or a rescue", "or an older", "kitten or", "cat or",
                 "rescue cat", "rescue kitten", "first cat", "first kitten", "good idea",
                 "worth getting",
                 # "when should i get my cat spayed" is the neutering row, not a second cat
                 "spay", "spayed", "spaying", "neuter", "neutered", "neutering", "castrate",
                 "the snip",
                 # cats that already live together and have fallen out are the cat-fighting row's
                 # question: "my cat attacked my other cat" holds "other cat" and would otherwise
                 # be told how to introduce a second cat, which is not what happened.
                 # The arms are narrow on purpose: "my kitten wont stop attacking my older cat"
                 # is still the introduction's question, so a bare attack verb is not enough to
                 # hand it over, and a hiss is never enough - "my cat is hissing at the new
                 # kitten" is why "kitten" is in the key above.
                 "keeps fighting", "keep fighting", "are fighting", "was fighting",
                 "fight over", "fighting over", "fought", "aggressive towards",
                 "aggressive toward", "bullies", "bullying", "picked on",
                 "attacks my other", "attacked my other", "attack my other",
                 "attacking my other",
                 # A cat who does not like other cats in general has not been given a new one, and
                 # "my cat hates other cats" was answered with the scent-before-sight paragraph
                 # for a second cat that does not exist. The words for a cat outside the house go
                 # with it, and "my cat hates the other cat" stays the fighting row's line.
                 "other cats", "other cat", "neighbours cat", "neighbours cats",
                 "neighbour's cat", "next doors cat", "next door's cat", "cats outside",
                 "cat outside", "the stray", "strays",
                 # "should i get two cats" and "is it better to have two cats" name two cats but
                 # there is no first cat yet: the question is whether one cat wants company, and
                 # the introduction paragraph answers a cat the person already has.
                 "get two", "get 2", "have two", "having two", "two cats to", "two cats or",
                 "two cats instead", "two cats better", "one or two cats", "enough company",
                 "need company", "needs company", "lonely", "bored"),
          # "I've got two cats, Milo and Otis" names two cats and is not a question: without
          # this the introduction answer took the opener of a chat and then stuck to the next
          # turn as well. The line has to be asking, deciding or planning.
          # "how many cats do i have" is a count of the cats the chat was told about, not the
          # introduction question: a bare "how" in the gate took every count ask, because the
          # store's "You've got two cats." loses the turn to an entry whatever its priority.
          ask=("how", "should", "can", "could", "shall", "will they", "would", "introduce",
               "introducing", "introduction", "want", "wanting", "thinking", "advice",
               "best", "worth", "good idea", "getting", "get a", "planning", "settle",
               "ok to", "alright",
               # the fight has usually already started by the time people ask, so a report of
               # hissing, growling or swiping counts as the question: "my cat is hissing at the
               # new kitten" was the shopping list for a first kitten
               "hiss", "hisses", "hissing", "growl", "growls", "growling", "spit", "spits",
               "spitting", "swipe", "swipes", "swiping", "fighting", "battling", "attacking",
               "chasing", "new kitten", "the new kitten", "newcomer", "scared of the", "afraid of")
               + _NEW_ANIMAL_REACTION,
          bias=1),
    # "do cats need company" and "are cats lonely on their own" were both a shrug, and "should
    # i get two cats" was the introducing-two-cats paragraph read out to someone with no cat
    # yet. The answer is that a cat's sociability is real but optional, and that a kitten is the
    # one that cannot be left.
    entry("cat-company",
          (("cat", "cats", "kitten", "kittens", "kitty", "moggy"),
           ("company", "need company", "needs company", "lonely", "loneliness", "bored",
            "boredom", "one cat", "single cat", "two cats", "get two cats", "getting two cats",
            "another cat",
            "second cat", "a friend for", "need a friend", "needs a friend",
            "want a friend", "wants a friend", "a companion", "on its own", "on their own",
            "by itself",
            "left on their own", "alone in the house", "does it need")),
          ("Cats are sociable, but they hunt alone and sleep sixteen hours a day, so an adult "
           "cat does not need company the way a dog does: a clean tray, water, food and something "
           "to climb are enough for the hours you are out. Two cats that get on will often "
           "choose to be in the same room, so two is kinder than one if you are out long days - "
           "but get them together as kittens, or introduce an adult pair slowly. What does need a "
           "person about is a kitten: it wants feeding little and often for months."), bias=1,
          # a cat already hissing at a newcomer, a cat left for a weekend and a sick cat are
          # other rows, and the count of cats a chat was told about is the store's
          avoid=("hiss", "hisses", "hissing", "growl", "growling", "swipe", "fighting",
                 "attacking", "introduce", "introducing", "introduction", "new kitten",
                 "the new kitten", "weekend", "holiday", "while im away", "while i'm away",
                 "how many", "many cats", "sick", "ill", "vet", "died", "dead", "passed away",
                 "put down", "move house", "moving", "cattery",
                 # a duration ask is the leaving question, not whether a cat wants company
                 "how long", "how many hours", "be left", "left on", "left for",
                 # "we have two cats" is a chat telling the bot its own household, and the store
                 # notes it: the count is the evidence for the advice, not a question about it
                 "we have two", "weve got two", "we've got two", "i have two", "ive got two",
                 "i've got two", "we have a cat", "weve got a cat", "we've got a cat",
                 # and a line that is correcting the count already told is the chat's business:
                 # "sorry, 1 cat" must not be answered with a lecture on two cats
                 "sorry", "i mean", "i meant", "make that", "correction", "no wait",
                 "not two", "only one", "just one")),

    # "what about a cat instead" is the swap inside a pet conversation, and it went unanswered
    # because the pick between the two animals needs both named on the same line. Only the
    # phrases that say "instead" are in the key, so a cat that wees instead of using the tray
    # is still the litter question.
    entry("cat-instead",
          # "than a dog" and "rather than a dog" are deliberately not here: those are a
          # comparison, and the pick between the two animals answers them.
          (("cat", "cats"), ("cat instead", "a cat instead", "instead of a dog", "cat rather",
                             "instead of dogs", "what about a cat", "rather have a cat",
                             "rather get a cat", "cat rather than")),
          ("A cat suits a working day better than a dog: it sleeps through your shift, needs no "
           "walk at seven in the morning and is happy with two rooms and a window. Get an adult "
           "cat rather than a kitten if you are out all day, or two cats so they have company, "
           "and leave something tall to climb and a windowsill to watch. A dog is the better "
           "choice if you want the walk and the welcome home more than the quiet."), bias=1,
          avoid=("wee", "wees", "weeing", "poo", "litter", "tray", "scratch", "vomit", "sick",
                 "vet", "eat", "eats", "ate", "food", "hiss", "growl", "died", "dead")),

    # An older cat that stops jumping or starts taking the stairs slowly is the same arthritis
    # question a dog gets, and it has its own answer rather than a shrug.
    # Two cats in one house that have stopped getting on is what people write in about far
    # more often than the introduction: "my cat is aggressive towards the other cat" and "my
    # cats keep fighting" were both read back to the person ("Noted: ...") and "how do i stop my
    # cats fighting" reached the digging row, because "stop" and "cats" are in it.
    entry("cat-fighting", (("cat", "cats", "kitten", "kittens"),
                           ("aggressive", "aggression", "fighting", "fight", "fights",
                            "fought", "attack", "attacked", "scrapping",
                            "hissing", "hiss", "bully", "bullies", "bullied", "picked on",
                            "spat", "spats", "growling", "growls", "swiping", "attacking",
                            "attacks", "hate each other", "hates the other", "hates each other",
                            # one cat and the idea of other cats, which is the same tension said
                            # without a second cat named in the house: "my cat hates other cats"
                            # reached no row at all and was answered "Anything you'd like a hand
                            # with?", though the separate-bowls-and-trays answer is what it is.
                            "hates other cats", "hate other cats", "hates other", "hate other",
                            "hates other animals", "dislikes other cats", "doesnt like other cats",
                            "does not like other cats", "cant stand other cats",
                            "hisses at other cats", "swears at other cats",
                            "get my cat to like other cats", "cat to like other cats",
                            "get on with other cats", "get along with other cats")),
          ("Separate the things they share before anything else: two bowls in different rooms, "
           "two litter trays and a high place each, so neither cat can be cornered, and a "
           "Feliway plug-in in the room they use most. Then feed them on either side of a "
           "closed door and swap their bedding, and only put them together when the hissing at "
           "the door has stopped - never face to face to sort it out. If a cat that was calm "
           "has turned on the other one, take her to the vet first: pain and a bad tooth are "
           "what turn a settled cat grumpy."),
          # the digging row is a garden question, and being bitten or scratched is its own
          # answer; a person picking the cat up is asking about the cat's mood, not this
          avoid=("dig", "digs", "digging", "dug", "flowerbed", "border", "soil", "mulch",
                 "bite", "bites", "biting", "bit", "bitten", "scratch", "scratched", "scratching",
                 "pick", "picked", "picking", "stroke", "stroked", "stroking", "cuddle", "lap",
                 "baby", "child", "toddler", "newborn", "grandchild",
                 # two cats that scrap at night are the crepuscular-hours row's question, and a
                 # cat that fights the dog needs the dog half of it
                 "night", "nights", "nighttime", "bed", "sleep", "sleeping", "asleep", "awake",
                 "waking", "wake", "dawn", "early", "4am", "5am", "morning",
                 "dog", "dogs", "puppy", "puppies",
                 # a kitten and an older cat, or a cat and a new one, is the introduction's
                 # question even when the line says "attacking": the separate room and the door
                 # are what fixes it, and that row already answers it.
                 "older cat", "older cats", "new kitten", "new cat", "second cat", "introduce",
                 "introducing", "introduction", "another cat",
                 # a cat that goes for a person is not a cat that fights the other cat: the
                 # answer below is two bowls and two trays, which says nothing to someone who
                 # has been scratched, and the bite and scratch rows are the ones that do.
                 "towards me", "toward me", "at me", "to me", "towards us", "toward us",
                 "at us", "the kids", "my kids", "my children", "my partner",
                 "attacks me", "attack me", "attacking me", "attacked me",
                 "attacks my partner", "attacks my wife", "attacks my husband",
                 "attacks my son", "attacks my daughter", "attacks my baby",
                 "went for me", "goes for me", "bit me", "bites me", "scratched me",
                 # the same thing said the other way round: "my cat keeps fighting me" is a
                 # person being gone for, and it is the scratch and bite rows' question
                 "fighting me", "fights me", "fought me", "fighting us", "fights us",
                 "brush", "brushing", "brushed", "groom", "grooming", "groomed",
                 # a cat fighting an illness is not fighting another cat, and the cold card is
                 # the one that answers it
                 "cold", "colds", "flu", "ill", "illness", "sick", "sickness", "unwell",
                 "sneezing", "sneezes", "sneeze", "cough", "coughing", "virus", "fever",
                 # a cat from another house is not one of the two that share this one: the
                 # answer above is two bowls and two trays, and there are no bowls to separate
                 # when the other cat lives up the road. "my cat keeps fighting with next doors
                 # cat" is the cat-other-house row's question.
                 "next door", "nextdoor", "nextdoors", "neighbour", "neighbour's", "neighbours",
                 "neighbors", "neighbor", "across the road", "up the road", "stray", "strays",
                 "feral", "roaming", "visiting cat", "other house"),
          # "my cat is aggressive" with nothing else in the line does not say who at, and "my two
          # cats dont get on" is the introduction row's: this answer needs a word that names the
          # other cat or the fight itself.
          # "my cats dont get on" is the same question as "they fight", and the group above
          # holds the word "cat", so a "get on" arm here cannot reach a person.
          # a hiss on its own does not say there is a second cat in the house ("my cat spat at
          # the vet" was reaching this answer), so the hiss words are not an ask: a line that
          # names the other cat still arrives through "other", "each other" or "together".
          ask=("other", "each other", "one of my cats", "two cats", "both", "together",
               "fighting", "fight", "fights", "bully", "bullies", "bullied", "picked on",
               "attacking", "aggressive towards", "hate each other",
               "get on", "get along", "getting on", "getting along"),
          bias=1),
    # The other animal in a cat fight is often not in the house: "my cat fights with the cat
    # across the road" and "the cat from next door keeps attacking mine" were read back to the
    # person, because no row says what to do about a visitor you do not own. What works there is
    # different - you cannot put the other cat's dinner in another room or carry it to the vet.
    entry("cat-other-house", (("cat", "cats", "kitten", "kittens"),
                              ("neighbour", "neighbour's", "neighbours", "neighbor", "neighbors",
                               "next door", "nextdoor", "nextdoors", "across the road",
                               "up the road", "stray", "strays", "feral", "roaming",
                               # not "other cat": one edit away from "other cats", which is how
                               # "my cat attacked my other cat" is worded, and that is one house
                               "other house", "someone else's cat")),
          ("Keep your cat in from dusk to dawn and lock the cat flap at night, because that is "
           "when the fights happen: a cat is most likely to be on the boundary at dawn and "
           "dusk. Then break the sightline - a sheet of card or frosted film on the low window "
           "and nothing to sit on beside it - and put a motion water spray or a sonic unit on "
           "the fence where the visiting cat comes in. Chasing it off by hand only works while "
           "you are there. If your cat comes home with a bite or a limp, have the vet look at "
           "it, because a cat bite abscesses."),
          # the digging and pooing rows are the garden's question and they answer it better;
          # a cat that hisses at its own housemate never gets here (cat-fighting takes it).
          avoid=("dig", "digs", "digging", "dug", "poo", "poos", "pooing", "pooed", "poop",
                 "soil", "mulch", "flowerbed", "border", "lawn", "garden", "gardens", "weed",
                 "weeds",
                 "older cat", "new kitten", "new cat", "second cat", "introduce", "introducing"),
          ask=("fighting", "fight", "fights", "fought", "attacking", "attacks", "attacked",
               "aggressive", "keeps coming", "coming in", "come in", "keeps getting in",
               "spraying", "scrapping", "hissing", "bullying", "picked on", "what can i do",
               "how do i stop"),
          bias=2),
    entry("cat-arthritis", ("cat", ("stairs", "struggling", "stiff", "stiffness", "jumping",
                                    "jump", "arthritis", "slow", "slower", "reluctant",
                                    "cant jump", "can't jump", "limping", "limp")),
          ("A cat that stops jumping up or takes the stairs one step at a time is usually in pain "
           "from arthritis, which most cats over ten have somewhere. Take her to the vet: there are "
           "painkillers made for cats, and a monthly injection does well for many. Put a step or a "
           "box beside the sofa and the bed, keep her food and litter on one floor, and a warm bed "
           "away from draughts helps the stiffness more than people expect."),
          avoid=("died", "dying", "dead", "passed away", "put down", "euthanised", "euthanized",
                 # a cat up on the worktop is the counters question, not stiffness
                 "worktop", "worktops", "counter", "counters", "countertop", "hob", "cooker",
                 "stove", "kitchen", "surface", "surfaces",
                 "death", "vomit", "vomiting", "sick", "cough", "coughing", "wheez", "sneez",
                 # breathing trouble is the cough entry's line, and it is urgent
                 "breathe", "breathing", "breath", "breathless", "panting",
                 # a cat that eats or drinks differently is the food or the water question, not
                 # a stiff one: "my cat is a slow eater" is not arthritis. Phrased, so that
                 # "my cat is hungry at night" stays the night question.
                 "drink", "drinks", "drinking", "water", "thirsty",
                 "not eating", "eating less", "eats less", "off her food", "off his food",
                 "off their food", "slow eater", "slow to eat", "wont eat", "won't eat",
                 "reluctant to eat", "refusing food", "refuses food"),
          bias=1),
    entry("cat-cough", ("cat", ("cough", "coughing", "sneezing", "wheezing", "breathing")),
          ("A cat coughing or wheezing is a vet visit, not a wait-and-see: cats hide chest trouble "
           "well and a night cough can be asthma, a hairball problem or heart disease. Note how "
           "often it happens and whether she is eating, then book her in; take her straight away "
           "if she is open-mouth breathing or her gums look pale or blue.")),
    entry("cat-night", (("cat", "cats", "kitten", "kittens"),
                        ("night", "nights", "wake", "wakes", "waking", "meowing", "early",
                         "to sleep")),
          ("Cats are crepuscular, which is why they will happily get you up at 5am: feed the last meal late, "
           "play hard for ten minutes before bed, and never get up to feed or play at night, or "
           "the routine sticks. An automatic feeder helps more than anything else."), bias=1,
          # The topic of an earlier turn can carry into this one, so a cat answer must refuse a
          # line that names another animal: "my dog has a cough at night" is not about a cat.
          # A cat that is sick or coughing at night is the vet's line.
          avoid=("died", "dying", "dead", "passed away", "death", "put down",
                 "dog", "dogs", "puppy", "puppies", "rabbit", "hamster", "horse",
                 "cough", "coughing", "wheez", "sneez", "breathing", "limp", "vomit", "sick",
                 # a cat that drinks a lot is the water question. The food guard is phrased:
                 # getting you up at 5am for food is the crepuscular complaint itself, so
                 # "food", "eat" and "hungry" cannot guard this entry.
                 "drink", "drinks", "drinking", "water", "thirsty",
                 "not eating", "eating less", "eats less", "off her food", "off his food",
                 "off their food", "slow eater", "slow to eat", "wont eat", "won't eat",
                 "reluctant to eat", "refusing food", "refuses food")),
    # Meowing at a closed door is not the 5am waking question: the cat is asking to be let
    # through, and "Cats are crepuscular ..." tells the person to feed later and play before
    # bed, which does nothing for a door. The door is the subject, so it is in the key and the
    # night row keeps the doorless waking lines.
    entry("cat-door", (("cat", "cats", "kitten", "kittens"),
                       ("door", "doors", "back door", "front door", "bedroom door")),
          ("A cat meows at a closed door because she wants through, and the door she can see but "
           "not cross is what the noise is about: open it once while she is crying and the "
           "crying is what she learns works. Decide when she is allowed through and be "
           "consistent - let her through before she starts if you are going that way, and "
           "otherwise ignore the meowing and scratching completely. A cat flap or a bell on the "
           "door gives her a quieter way to ask."), bias=3,
          ask=("meow", "meows", "meowing", "miaow", "miaows", "miaowing", "mew",
               "mews", "mewing", "crying", "cries", "cry"),
          avoid=("dog", "dogs", "puppy", "puppies", "rabbit", "hamster", "horse",
                 "died", "dying", "dead", "put down", "sick", "ill", "hurt", "pain",
                 "cough", "coughing", "sneeze", "sneezing", "breathing", "vomit", "limp",
                 "not eating", "wont eat", "won't eat", "refusing food")),
    # A dog pacing at night is a pain or a dementia question, not a puppy that cannot hold it,
    # and it had no answer at all: the night entry refuses the word "pacing" on purpose.
    entry("dog-pacing", (("dog", "dogs"), ("paces", "pacing", "wanders", "wandering",
                                           "restless", "confused", "disorientated",
                                           "disoriented")),
          ("A dog who paces or seems confused at night is usually in pain or getting muddled, "
           "not being naughty: arthritis makes lying still hurt, and an older dog can lose track "
           "of where he is in the dark. Book a vet visit and mention the nights, leave a small "
           "light on the landing and let him out calmly when he asks. Do not scold him for it, "
           "and note how much he drinks, because that points the vet one way or the other."),
          avoid=("died", "dying", "dead", "passed away", "put down", "euthanised", "euthanized",
                 # a cat is not a dog question, and a neighbour's dog is not this dog
                 "cat", "cats", "kitten", "kittens", "barks", "barking", "neighbour",
                 "neighbours", "neighbor", "neighbors", "next door")),
    # A puppy that will not settle and a puppy that was put to sleep share "to sleep at night":
    # pet-loss and the loss composer have to leave that line alone, and this entry answers it.
    # The reply says what a puppy needs, so it asks for one before it talks about bladders.
    entry("dog-night", (("puppy", "puppies", "dog", "dogs"),
                        ("night", "nights", "settle at night", "settles at night",
                         "cant settle at night", "wont settle at night",
                         "settle down at night", "paces at night", "pacing at night",
                         "wake", "wakes", "waking",
                         "crying", "cries", "whines", "whining", "to sleep", "asleep",
                         # "my dog is up at 5am every morning" names no night word at all.
                         # Bare "sleep" and "morning" are out on their own: "my dog sleeps all
                         # day" is not a night question, and typing "in the morning" is not either.
                         "morning", "mornings", "up at", "early",
                         # The person's own lost sleep, said as a phrase: "i cant sleep since we
                         # got the puppy", "my puppy keeps me awake", "i havent slept since we got
                         # the dog" were the vet shrug and "A dog - how long has it been with
                         # you?" - the card that answers them existed and wanted the night named.
                         # A phrase, never the bare word, for the same reason as above.
                         "cant sleep", "can not sleep", "cannot sleep", "couldnt sleep",
                         "not sleeping", "havent slept", "have not slept", "not slept",
                         "keeps me awake", "kept me awake", "keeping me awake",
                         "keeps me up", "kept me up", "wakes me up", "waking me up",
                         "woke me up")),
          _dog_night, bias=1,
          avoid=("died", "dying", "dead", "passed away", "death", "euthanised", "euthanized",
                 "put down",
                 # a puppy crying when it is left is a daytime question, not a night one
                 "leave", "leaves", "leaving", "left", "alone", "work", "daytime",
                 # a neighbour's dog barking at night is their problem, not puppy advice
                 "barks", "barking", "neighbour", "neighbours", "neighbor", "neighbors",
                 "next door",
                 # a walk is the person's day, not the dog's night, in the words people use for
                 # it: "i walk the dog every morning", "i take the dog out every morning"
                 "walk", "walks", "walking", "walkies", "take the dog", "take him out",
                 "take her out", "let the dog", "let him out", "let her out", "the dog out",
                 # "my dog will not wake up" is an emergency, not a bedtime: a routine would be
                 # the worst possible answer to it, so an unresponsive dog is never this entry
                 "will not wake up", "wont wake up", "won't wake up", "not waking up",
                 "wont wake", "not moving", "unresponsive", "unconscious", "collapsed",
                 "not breathing", "stopped breathing", "fits", "seizure", "blue gums",
                 # a dog coughing or sick at night is a health question, not a settling one
                 "cough", "coughing", "sneeze", "sneezing", "sick", "vomit", "vomits",
                 "vomiting", "diarrhoea", "ill", "unwell", "pain", "limp", "limping",
                 "blood", "scratching", "itch", "itchy", "temperature", "breathing",
                 # a dog that is asleep at night is fine, and a stiff slow one is a vet line
                 "asleep", "stiff", "slow", "slower", "lame",
                 # "up at" is the clock in "my dog is up at 5am", but it is also the jump in
                 # "the dog jumps up at visitors" - that one is the jumping-up answer
                 "jumps up", "jumping up", "jump up", "jumped up", "jumping on", "jumps on",
                 "up at people", "up at visitors", "up at guests", "up at strangers",
                 "up at everyone", "up at the door", "up at the postman", "up at me",
                 "up at my", "greeting visitors", "meets people", "meeting people",
                 # and a line that names a cat is not a dog question, even if a dog is on topic
                 "cat", "cats", "kitten", "kittens",
                 # an old dog up at night is a vet question, not a puppy that cannot hold it:
                 # "my old dog wanders at night and seems confused" must not get puppy advice.
                 # "old" on its own stays out: "my 9 week old puppy cries at night" says it too,
                 # and the reply itself says a dog that starts waking after years is a vet check.
                 "elderly", "senior", "aging", "ageing", "wanders",
                 "wandering", "pacing", "confused", "disorientated", "disoriented", "stairs",
                 "stiff", "struggling", "arthritis", "incontinent", "toilet",
                 # a tired dog in the evening is a tiredness question, and a dog left on its own
                 # at night is the separation question: both have their own answers
                 "tired", "exhausted", "lethargic", "sleepy", "no energy", "shattered",
                 "knackered", "not there", "without me", "when im out", "when i'm out",
                 "when i am out", "when im away", "when i'm away",
                 # panting, heat and drinking more are the vet signs this reply names, so a line
                 # about one of them is not a settling question
                 "pant", "pants", "panting", "hot", "heat", "overheated", "sweating",
                 "sweaty", "drink", "drinks", "drinking", "water", "thirsty", "eat",
                 "eats", "eating", "food", "appetite", "hungry")),
    # A dog that starts panting at night, or drinks the bowl dry, is a vet question rather than
    # a settling one, and it had no answer of its own.
    # The first question after a rescue or a rehome is how long the settling takes, and there was
    # no answer to it at all: "how long until he settles" got nail clipping, because the only
    # entry that matched was one keyed on "long".
    entry("dog-rescue-settle",
          (("rescue", "rescued", "rehomed", "adopted", "we adopted", "shelter", "kennels",
            "rescue dog"),
           ("settle", "settles", "settling", "settled", "how long", "take", "calm", "relax",
            "at home", "himself", "herself",
            # the first thing people ask once the dog is home is not how long it takes but what
            # to do: "how do i look after a rescue dog" and "we got a rescue greyhound last
            # month" both reached nothing at all.
            "look after", "looking after", "care for", "caring for", "care", "advice", "tips",
            "first", "first month", "first week", "new dog", "just got", "got a", "we got",
            "brought him home", "brought her home", "settle in", "settling in")),
          ("Three days, then three weeks, then three months: three days where he mostly rests and "
           "you leave him be, three weeks to learn the routine and start trusting the house, and "
           "about three months before he is properly himself. Keep the first week boring, with "
           "the same food, short walks and no visitors, let him come to you rather than reaching "
           "over him, and give him a corner he can retreat to that nobody follows him into."),
          bias=2,
          avoid=("sleep", "sleeps", "sleeping", "night", "nights", "bedtime", "wake", "wakes",
                 "waking", "cries", "crying", "whines", "whining", "barks", "barking",
                 "feed", "feeding", "food", "eat", "eats", "toilet", "training", "vet",
                 "puppy", "puppies", "kitten")),
    # A cat is not a dog about heat: a dog pants to cool down, a cat almost never does, so an
    # open mouth in a cat is a warning rather than the normal way it sheds heat. "my cat is
    # panting in this heat" reached nothing at all (the dog cards hold "in this heat" out, and
    # pet-hot's reply talks about walking him), and the chat module asked whether a cat was good
    # company instead.
    entry("cat-panting", (("cat", "cats", "kitten", "kittens"),
                          ("panting", "pants", "panted", "pant", "mouth open", "open mouth",
                           "breathing fast", "breathing quickly", "hot", "too hot",
                           "overheated", "overheating", "heat")),
          ("A cat with its mouth open is not cooling down the way a dog does, so treat it as a "
           "warning: move her to the coolest room, water in a wide bowl, a damp towel on the "
           "belly and a fan on the floor rather than on her face, and let her lie stretched out "
           "on tiles. If the panting carries on after ten minutes in the cool, or comes with "
           "drooling, wobbling, gums that look pale or brick red, or a cat that will not stand, "
           "ring the vet now - that is heat stroke, not a warm day. A few seconds of panting "
           "after hard play is normal and should stop as soon as she rests."),
          bias=2,
          # the weather is what makes this row right: a cat panting with no heat in the line is a
          # breathing emergency and has a better card of its own ("Ring the vet now: a cat
          # breathing more than about 40 breaths a minute at rest ..."), so the heat word gates it
          ask=("hot", "heat", "heatwave", "heat wave", "warm", "summer", "sun", "sunny",
               "too warm"),
          avoid=("died", "dying", "dead", "passed away", "put down", "euthanised", "euthanized",
                 "dog", "dogs", "puppy", "puppies",
                 # a cat that is off its food, sick or drinking a lot is those rows' question
                 "not eating", "wont eat", "sick", "vomit", "vomiting", "diarrhoea",
                 "drinking", "litter", "limping", "swollen", "wound")),
    entry("pet-hot", (("dog", "dogs", "puppy", "puppies", "cat", "cats"),
                      ("panting", "pants", "pant", "hot", "too hot", "overheated",
                       "sweating")),
          ("Panting is how a dog cools down, so on a warm night give him a cooler spot than the "
           "bedding he has, water within reach and a bowl in the shade; walk him early and late "
           "rather than in the heat of the day. A dog that pants hard while it is not hot, or has "
           "bright red gums, is a vet call rather than a cool room."),
          avoid=("died", "dying", "dead", "passed away", "put down", "euthanised",
                 "euthanized", "breathing", "breathe", "cough",
                 # a hot spot is a skin infection and a season is a different question
                 "hot spot", "hot spots", "in heat", "on heat",
                 # a line that already names the weather is dog-heat's: it has the pavement and
                 # the parked car in it, and this entry answered "my dog is panting a lot in this
                 # heat" instead of it
                 "in this heat", "this heat", "hot weather", "hot day", "heatwave",
                 "heat wave",
                 # "is it too hot to walk my dog" asks whether to go out, and dog-heat has the
                 # pavement test and the parked car in it
                 "too hot to walk", "too hot to go", "walk my dog", "walk the dog",
                 "should i walk", "go for a walk", "walking my dog", "in summer", "the summer", "sunny", "in the sun",
                 "keep him cool", "keep her cool", "keep my dog cool", "cool down")),
    entry("dog-thirsty", (("dog", "dogs", "puppy", "puppies"),
                          ("drinking a lot", "drinks a lot", "drinking more", "drinks more",
                           "thirsty", "always drinking", "weeing more", "peeing more")),
          ("A dog that suddenly drinks much more, and wees more with it, needs the vet: diabetes "
           "and kidney trouble both start that way, and so does a bladder infection. Note how "
           "much he drinks in a day and take a urine sample if you can, keep the water bowl full "
           "in the meantime, and do not restrict it."),
          avoid=("died", "dying", "dead", "passed away", "put down", "euthanised",
                 "euthanized", "heat", "hot", "panting", "vomit", "sick")),
    entry("cat-water", (("cat",), ("water", "drink", "drinking", "not drinking")),
          ("Cats are bad at drinking, so encourage it: a wide bowl filled to the brim, a second "
           "bowl away from the food, and a running tap or pet fountain. Wet food adds water too, "
           "and it matters most for their kidneys.")),
    # A water bowl is changed, not measured. "how often should i change the dog's water" and "how
    # often should i wash the water bowl" reached `pet-thirst` on the word water, so a person asking
    # how often to change it was told how much a dog drinks in a day. The interval is the ask here
    # and the thirst row keeps the amount.
    entry("pet-water-fresh",
          (("water", "bowl", "water bowl", "water bowls", "water bottle", "water bottles"),
           PET_ANIMAL_ASK),
          "Fresh water every day, and properly wash the bowl every day or two rather than just "
          "topping it up: a bowl that is only rinsed grows the slimy film that puts a cat off "
          "drinking, and a dog will drink from it anyway and then be off his food. Hot water and "
          "washing-up liquid, then a rinse, is enough - a dishwasher cycle once a week is easier "
          "still. Water bottles for rabbits, guinea pigs and hamsters get fresh water daily too, and "
          "twice a day in hot weather.",
          # it is the interval that is wanted: the amount a pet drinks, a pet that will not drink
          # and where it drinks from are the thirst row's questions
          ask=("how often", "how many times", "times a day", "daily", "every day", "how regularly",
               "how frequent"),
          avoid=("thirsty", "thirst", "drinking a lot", "drinks a lot", "drinking more",
                 "drinks more", "drinking loads", "always drinking", "drinking too much",
                 "drinks too much", "too much water", "not drinking", "wont drink", "won't drink",
                 "from the tap", "the tap", "from the toilet", "the toilet", "fountain",
                 "fish tank", "fish water", "aquarium", "pond", "water the plants",
                 "water my plants",
                 # cut flowers have their own answer, which is the vase
                 "vase", "vases", "flowers", "flower", "stems", "bouquet", "bunch"),
          bias=2),
    # The same question with no animal named: after "i got a puppy" the follow-up is a bare "how
    # often should i change the water", and "how often should i wash the water bowl".
    entry("pet-water-bowl",
          (("water bowl", "water bowls", "water bottle", "water bottles", "drinking water",
            "water dish", "his water", "her water", "their water", "change the water",
            "fresh water"),
           ("how often", "how many times", "times a day", "daily", "every day", "wash", "clean",
            "change", "refill", "emptying", "slimy")),
          "Fresh water every day, and wash the bowl properly every day or two: hot water and "
          "washing-up liquid, then a rinse, because a bowl that is only topped up grows a slimy "
          "film on the side and a cat will stop drinking from it. A dishwasher cycle once a week is "
          "easier still, and a water bottle wants fresh water daily and a scrub with a bottle brush.",
          avoid=("fish tank", "fish water", "aquarium", "pond", "toilet",
                 "vase", "vases", "flowers", "flower", "stems", "bouquet", "bunch")),
    entry("cat-pushes-things", (("cat", "cats", "kitten", "kittens"),
                                ("knock", "knocks", "knocking", "push", "pushes", "pushing",
                                 "off the", "off my", "table", "desk", "worktop", "shelf",
                                 "shelves", "swipes", "swiping", "things", "stuff",
                                 "mug", "cups", "vase", "ornaments")),
          # A cat entry is chosen by the behaviour, not by the cat, so "my tom cat keeps knocking
          # things off the table" was answered "She is not being naughty". The reply reads the
          # animal off the line.
          about_them("{they} {is} not being naughty: paws are how a cat tests the world, and the "
                     "crash gets a reaction every time. Take the reaction away and the game stops "
                     "being fun — no shout, no grab, just put the mug down and walk off. Give "
                     "{them} a shelf or a windowsill of {their} own, and a few minutes with a "
                     "wand toy before you sit down to work; a bored cat knocks more.",
                     male=ANIMALS_MALE, female=ANIMALS_FEMALE),
          # a cat that knocks things off a table is not digging in a flowerbed, and a swipe at a
          # mug is not over-stimulation from stroking: both reach the same couple of words, and
          # this is the entry that answers the line. One step only: a phone a cat knocked into
          # the bath is still the phone's question, and that card sits one step above this.
          #
          # up on the worktop, and getting the cat to stay off it, is the counters entry: this
          # one is the paw that pushes things onto the floor.
          avoid=("on the worktop", "on the counter", "on the counters", "on the kitchen",
                 "jumps on", "jumping on", "jumps up", "jumping up", "jump up", "gets on",
                 "getting on", "keep her off", "keep him off", "keep them off", "keep the cat off",
                 "keep a cat off", "keep cats off", "stay off", "staying off", "not allowed",
                 # and a garden is not a worktop: "how do i keep cats off my garden" keys the
                 # same two parts as this one ("cat" and "off my") and won the tie on registry
                 # order, so a cat in the flowerbed was told why paws push mugs off a table.
                 "garden", "gardens", "flowerbed", "flower bed", "flowerbeds", "lawn", "soil",
                 "borders", "digging", "pooing", "poo", "poos", "messing", "fence"
                 # "my cat vomits first thing" reached this entry on the word "thing", and a cat
                 # being sick in the morning is a body problem, not a paw on a worktop
                 ) + SICK_OR_HURT
                 # and the retching and the blood are the sickness rows' words too
                 + ("sick", "vomit", "vomits", "vomited", "vomiting", "threw up", "throwing up",
                    "retching", "blood", "diarrhoea", "diarrhea"),
          bias=1),
    entry("cat-purring", (("purr", "purrs", "purring", "purred"),
                          ("cat", "cats", "kitten", "mean", "means", "why", "happy", "content",
                           "loud", "always", "healing", "sick")),
          ("Purring is not only happiness. Cats purr when they are content, but also when they "
           "are nervous, in pain or healing — the vibration seems to settle them. So read the "
           "rest of the cat: a loose body and slow blinks mean content, crouched and tight means "
           "worried. A cat that purrs but has stopped eating still needs the vet."),
          # "he purred for the first time" is a moment someone is telling you about, not a
          # question, so the entry wants a question word before it takes the turn.
          ask=("why", "what", "mean", "means", "does", "do", "always", "loud", "happy",
               "content", "sick", "healing", "normal")),
    # An old cat hides illness, so the visit is the answer and the signs come second.
    entry("older-cat-checks", (("cat", "cats"),
                               ("old", "older", "elderly", "senior", "ageing", "9", "10", "11",
                                "12", "13", "14", "15", "check up", "check-up", "checkups",
                                "how often", "twice a year", "once a year", "still")),
          ("From about eight, twice a year is worth it: the vet can find the things old cats hide "
           "— kidney trouble, thyroid, arthritis, high blood pressure — before you see them. "
           "Weigh her monthly at home and ask for a blood and urine test at the annual visit. "
           "Don't wait for the check-up, though, if she loses weight, drinks more, hides away, "
           "stops grooming or goes off her food; those need the vet this week."), bias=1,
          # An old cat yowling at night is a night question (and sometimes a thyroid or blood
          # pressure one), not a "when is the next check-up" question.
          avoid=("night", "nights", "at night", "yowl", "yowling", "yowls", "howling",
                 "sleep", "sleeping", "wake", "wakes", "waking", "meowing", "meows", "early",
                 # "how often should i feed a cat" is the portion answer, not the check-up: the
                 # "how often" in both keys was enough to take it
                 "feed", "feeds", "feeding", "fed", "food", "meals", "meal", "how much",
                 "portion", "portions", "wet", "dry", "kibble", "treats", "treat", "water",
                 "litter", "grain", "raw",
                 # "how often should i play with my cat" takes "how often" and is a play question
                 "play", "playing", "playtime", "exercise", "bored", "boredom", "toys")),

    # --- fish and small animals --------------------------------------------------
    # "the tank is murky" names the tank and not the fish, and the tank is the whole of the
    # question: the state word in the second part says it is a tank somebody is looking after,
    # and the avoid list below is every other tank in the house.
    entry("fish-tank", (("fish tank", "fish water", "the fish water", "goldfish", "aquarium",
                         "tank", "tanks"), ("clean", "water", "often",
                                                               "how often", "change",
                                                               # "my fish tank smells" is the
                                                               # same tank question: the water is
                                                               # the answer, and the words for a
                                                               # sour tank have to be in the key
                                                               "smell", "smells", "smelly", "stink",
                                                               "stinks", "cloudy", "murky", "green",
                                                               "dirty", "foul",
                                                               # the green that grows in a tank is
                                                               # the same tank question: "my fish tank
                                                               # has algae" fell through to a recipe
                                                               # once the new-fish row stood down on it
                                                               "algae", "alga", "green water", "slime",
                                                               "slimy", "hair algae",
                                                               # changing the water is the same
                                                               # question said the other way round:
                                                               # "how often should i change the fish
                                                               # water" was the baked-fish method
                                                               "water change", "change the water",
                                                               "change the fish water",
                                                               "changing the water",
                                                               # a filter that rattles or hums is
                                                               # the same tank, and the kitchen
                                                               # fan answered it instead
                                                               "noisy", "noise", "noises",
                                                               "rattling", "rattles", "rattle",
                                                               "humming", "buzzing", "loud",
                                                               "grinding")),
          _fish_tank, bias=3,
          # "fishing" as a bare word is a trap: the loose forms of an avoid word are handed out
          # like the key's own, so it matched "fish" and stood this row down on "clean fish tank".
          avoid=("pond", "ponds", "cook", "cooking", "eat", "eating", "recipe",
                 "fish and chips", "go fishing", "gone fishing", "fishing rod", "fishing trip",
                 "fishing licence", "septic", "cesspit", "petrol", "diesel", "fuel", "gas",
                 "oil tank", "water tank", "hot water", "toilet", "boiler",
                 # The key carries "smell" for the tank that has gone sour, and a kitchen that
                 # smells of fish is the same two words: "how do i get rid of the smell of fish in
                 # the kitchen", "the kitchen smells of fish" and "the house smells of fish" were
                 # all told to change a quarter of the water. The phrases below are a room that
                 # smells and not a tank that does, so "my fish tank smells" stays here.
                 "smell of fish", "fish smell", "smells of fish", "smells like fish",
                 # "fishy" is the loose form of "fish", which is this row's own key word, so a
                 # bare "fishy" here stood the whole row down on "how do i clean a fish tank" and
                 # "my fish tank smells" (the trap `fish-new` records). The kitchen that smells
                 # of fish is caught by the phrases instead, which keep both their words.
                 "fishy smell", "fishy smells", "smells fishy", "smell fishy", "tastes fishy",
                 "fishy taste", "fishy smell in",
                 "smells like fish", "cooking smell", "kitchen smells", "house smells",
                 "fishy smell", "fishy smells", "fishy smell in", "smell fishy",
                 "the house smells", "after cooking", "from cooking", "frying", "fried fish",
                 # "tank" on its own is the word this row now takes, so the tanks that are not
                 # fish are stood down by name: the one in the loft, the one on the car, the
                 # army's, and the vest.
                 "tank top", "tank tops", "think tank", "tank up", "tanked up", "tankless",
                 "septic tank", "oil tank", "petrol tank", "diesel tank", "fuel tank",
                 "expansion tank", "header tank", "cistern", "tanker", "tanks for",
                 # "the tank in the loft is murky" is a cold-water storage tank, and the loft
                 # is how people name it: the card below told them to change a quarter of the
                 # water and rinse the filter sponge, in a tank feeding the hot taps.
                 "loft", "in the loft", "loft tank", "cold water tank", "cold water",
                 "central heating", "radiator", "radiators", "immersion", "hot water cylinder",
                 # a tank on a car is the car wash's job: "how do i clean my car tank" was told
                 # to change a quarter of the water and rinse the filter sponge
                 "car", "cars", "van", "vans", "motorbike", "motorcycle", "lorry",
                 # a feeding question is not a water change, and this row carries "how often"
                 # for "how often should i change the water": "how often should i feed my
                 # goldfish" was answered with the quarter water change, and the tank row has
                 # the higher bias so the feeding row below could not take it back
                 "feed", "feeds", "feeding", "fed", "food", "flake", "flakes", "pellet",
                 "pellets", "overfeed", "overfeeding", "how much")),
    # A fish that is already in the water and wants feeding is neither a new tank nor a water
    # change: "how often should i feed my fish", "how much should i feed my goldfish" and "what
    # should i feed my goldfish" were all told how to cycle a new tank, which is no use to
    # somebody holding a pot of flakes. The feed words are the question and the fish is the
    # subject; cooking a fish is the kitchen's.
    entry("fish-feed",
          # "fish tank" and "aquarium" are deliberately not in this key: both are the tank row's
          # own words, and a shared word moves the rarity the whole table scores on, which took
          # "clean my fish tank" away from the tank row and left it with no answer at all
          (("fish", "fishes", "goldfish", "tropical fish", "koi", "betta", "guppy", "guppies"),
           ("feed", "feeds", "feeding", "fed", "food", "foods", "overfeed", "overfeeding",
            "how much", "flakes", "flake", "pellets", "pellet", "what should i feed",
            "how often should i feed", "how many times a day should i feed", "starving",
            "hungry", "sinking", "floating food")),
          ("A pinch of food once or twice a day, and only what they clear in two minutes: a fish's "
           "stomach is about the size of its eye, and uneaten food fouls the water faster than "
           "anything else. Skip one day a week, use flakes or pellets made for the species rather "
           "than bread or scraps, and if the water clouds up after a feed, you are feeding too much."),
          # a fish that is in its tank and wants feeding is this row, not the new-tank row: both
          # reach "how often should i feed my fish" (this row on feed + fish, that one on "my" +
          # "fish"), so the bias, not an avoid word, is what puts a pot of flakes above a cycled
          # tank. The tank row keeps out the feeding words so it cannot win the same line.
          bias=5,
          # cooking a fish, buying one and a sick one are all other answers
          avoid=("cook", "cooking", "cooked", "eat", "eating", "ate", "recipe", "dinner", "tea",
                 "supper", "lunch", "meal", "pie", "cake", "cakes", "chips", "batter", "baked",
                 "bake", "fry", "fried", "grill", "roast", "steam", "poach", "raw", "sushi",
                 "sashimi", "smoked", "kipper", "fillet", "fillets", "market", "monger", "shop",
                 "buy", "price", "cheap", "fresh", "frozen", "freezer", "thaw", "defrost",
                 "leftover", "leftovers", "allergy", "allergic", "shellfish",
                 "white spots", "whitespot", "ich", "speck", "specks", "sick", "ill", "poorly",
                 "dying", "dead", "died", "floating upside", "on its side", "fin rot", "dropsy",
                 "swollen", "gasping", "new tank", "set up", "cycled", "cycling",
                 "dechlorinator", "gravel", "litres", "bowl"),
          # an angling line is the rod licence and not a pot of flakes: "how much is a fishing
          # licence" scored this row on `fish` + `how much`, and the day-ticket prices are the
          # answer. The angling words are the shared guard rather than an avoid word here, since
          # a bare "fishing" holds "fish" and would stand the row down on its own key word.
          guard=_fish_not_the_sport),

    # Cycling a tank is the one fish question with a clock on it, and "cycle" is a word with a
    # second life in the body: "my new tank is cycling how long" was answered with "the usual
    # cycle is 21 to 35 days from the first day of one period". The tank words are the whole
    # subject here, so the row names them with the words for the bacteria it is waiting on.
    entry("fish-tank-cycle",
          (("tank", "tanks", "aquarium", "fish tank", "filter", "nitrite", "nitrate", "ammonia"),
           ("cycle", "cycles", "cycling", "cycled", "fishless cycle", "nitrogen cycle",
            "how long", "how many weeks", "ready for fish", "add fish", "first fish",
            "new tank", "new aquarium", "set up", "setting up", "started", "start",
            "bacteria", "mature", "seasoned")),
          ("Four to six weeks, with a test kit telling you when it is done. Ammonia from fish "
           "waste and food has to be eaten by bacteria that take weeks to grow, and the tank is "
           "ready when ammonia and nitrite both read zero a day after you add a little food: "
           "ammonia peaks in the first week or two, nitrite in the third or fourth, and nitrate "
           "climbing at the end is the sign it has finished. A bottle of starter bacteria can "
           "cut a week or so off. Don't add more than a few small fish at first, and don't "
           "change the filter media in that time."), bias=1,
          # a tank of petrol, a hot-water tank and a fish that is ill are other answers
          avoid=("petrol", "diesel", "fuel", "septic", "cesspit", "loft", "cold water tank",
                 "central heating", "radiator", "car", "van", "lorry", "tank top",
                 "white spots", "white spot", "lying on the bottom", "gasping", "dying")),

    # "my goldfish has been lying on the bottom all day" had no answer at all: the tank answer
    # is about the weekly water change and the small-tank answer is about litres, and neither is
    # what a person with a sick fish is asking. The behaviour is the whole of the ask here - the
    # fish is on the bottom, at the top, on its side, or not eating - so the fish word carries
    # the subject and the behaviour carries the question.
    entry("fish-sick",
          (("goldfish", "fish", "fishes", "tropical fish", "koi", "betta", "guppy", "guppies"),
           ("lying on the bottom", "on the bottom", "at the bottom", "bottom of the tank",
            "sitting on the bottom", "at the top", "at the surface", "gasping", "gulping",
            "on its side", "upside down", "floating", "not moving", "not eating", "wont eat",
            "wont move", "sick", "ill", "dying", "dead", "red gills", "fungus", "dropsy")),
          ("A fish sitting on the bottom, or hanging at the surface gulping, is reacting to the "
           "water rather than to you, and ammonia is the usual cause: change a quarter of the "
           "water now with water of the same temperature that has been dechlorinated, stop "
           "feeding for two or three days, and check the filter is running and not clogged. "
           "Then test the water - a kit for ammonia and nitrite costs less than the fish does - "
           "before you buy any medicine, because a medicine in a tank with ammonia in it kills "
           "faster than the disease. On its side, gasping at the top, or with red gills is an "
           "emergency: water change now, lights off, no food."),
          # the weekly water change, the litres a goldfish needs and a pond are other questions
          avoid=("how often", "how much", "litre", "litres", "gallon", "gallons", "tank size",
                 "how big", "bowl", "pond", "clean", "cleaning", "water change", "feed them",
                 "how many fish"),
          guard=_fish_not_the_sport),

    # White spots are their own illness with their own cure, and the water answer is not it: a
    # fish with grains of salt on it wants the temperature up and a treatment, and the spots only
    # die off the fish in the stage when they have dropped into the water.
    entry("fish-whitespot",
          (("goldfish", "fish", "fishes", "tropical fish", "koi", "betta", "guppy", "guppies"),
           ("white spots", "white spot", "whitespot", "whitespots", "white spots disease",
            "white specks", "white dots", "ich", "ick", "grains of salt", "salt grains",
            "little white")),
          ("White spots the size of grains of salt are whitespot (ich), and it is curable: raise "
           "the temperature a degree or two a day to about 26C, add a whitespot treatment from the "
           "aquarium shop or aquarium salt at the dose on the bottle, and keep treating for a few "
           "days after the last spot goes - the parasite is only killable when it drops off the "
           "fish into the water. Test for ammonia first, because a fish in poor water catches it, "
           "and don't add new fish until the tank has been clear for a fortnight."),
          # a spot of food, a spot of colour and a new tank are other questions
          avoid=("spot of", "feed", "feeding", "eat", "food", "buy", "shop for", "choose",
                 "how many", "litres", "gallon", "pond", "water change", "clean", "cleaning"),
          guard=_fish_not_the_sport),


    # "i have a fish" is one animal, and the kitchen answered it with a cod traybake: "fish" is a
    # food word and a pet, and only the article tells them apart. "i have some fish" is dinner and
    # stays with the kitchen; a counted fish - a, one, two, this, my, "just got" - is a pet.
    entry("fish-new",
          (("fish", "fishes", "goldfish", "betta", "guppy", "guppies", "tropical fish", "koi"),
           ("have", "has", "got", "get", "new", "just", "bought", "my", "our", "look after", "care",
            "take care", "what do i feed", "how do i feed", "feeding", "feed it", "starter",
            "first fish", "set up", "keeping")),
          ("A new fish needs the tank ready before it goes in: a filter running, water treated "
           "with a dechlorinator, and the tank cycled for four to six weeks so the bacteria that "
           "eat the fish's waste can grow. Feed only what it clears in two minutes, once or twice "
           "a day, and change about a quarter of the water every week. A goldfish needs 100 litres "
           "and a filter - a bowl is not a home for it."), bias=4,
          # "some fish" is the fishmonger, and a pie or a finger is dinner: those stay with the
          # kitchen, which is where the recipe and the cooking times live
          # a fish that is ill is the water question, and it is asked with "has" as well as
          # "is" ("my goldfish has white spots"), so the illness words stand this row down
          # "my dishwasher smells of fish" was this card's ("fish" + "my"), and the person
          # wanted the kitchen appliance. The things a fish is cooked or served in - and the
          # words for an appliance that smells - stand the pet row down.
          # Looking after the tank is the tank row's question, and this row's bias (4) let it take
          # every one of them: "how do i clean my fish tank" and "how often should i clean the
          # filter" were told how to cycle a new tank. A new fish is the only thing this row knows.
          # a fish being eaten is the kitchen's question: "my fish tastes too fishy" was told how
          # to cycle a tank, because "fish" and "my" is most of this key. The taste words are
          # phrases, never the bare "fishy": the ending table hands a typed "fish" the avoid
          # word's own forms, so "fishy" alone stood this row down on every line with a fish in it.
          avoid=("taste", "tastes", "tasting", "tasted", "too fishy", "tastes fishy",
                 "smells fishy", "on the plate", "cooked it", "edible",
                 "clean", "cleaning", "cleaned", "how often", "water change", "change the water",
                 "change the filter", "filter", "filters", "cloudy", "murky", "algae", "green",
                 "dirty", "gravel", "vacuum", "siphon", "test the water", "water test",
                 "dishwasher", "washing machine", "fridge", "freezer", "oven", "microwave",
                 "sink", "bin", "kitchen", "smell", "smells", "smelling", "smelly", "stink",
                 "stinks", "stinking", "plate", "plates", "dish", "dishes", "dinner", "lunch",
                 "recipe", "cook", "cooking", "fried", "battered", "fish and chips", "fishcake",
                 "fishcakes", "fish finger", "fish fingers", "supper", "meal",
                 # a live fish does not fall apart: "my fish is falling apart", "my fish breaks up
                 # in the pan" and "my fish is falling to bits" are the flesh of a cooked one, and
                 # the kitchen row for it is `fish-falls-apart`.
                 "falls apart", "falling apart", "fell apart", "fallen apart", "fall apart",
                 "breaks up", "breaking up", "breaks apart", "breaking apart", "to bits",
                 "crumbles", "crumbling", "splits", "splitting", "mushy",
                 "white spots", "white spot", "whitespot", "specks", "ich", "ick", "grains",
                 "grains of salt", "sick", "ill", "poorly", "dying", "dying", "dead", "died",
                 "not eating", "wont eat", "won't eat", "not moving", "on its side",
                 # a fish already in a bowl is the room question, and that row says more
                 "bowl", "bowls", "in a bowl",
                 "upside down", "on the bottom", "at the bottom", "at the top", "gasping",
                 "gulping", "fungus", "fin rot", "dropsy", "swollen", "floating",
                 # a person who will not eat fish is a dinner question, not a tank one: "my mum
                 # doesnt like fish" was told a new fish needs the tank ready before it goes in,
                 # because "fish" and "my" is most of this key and nothing in it says who the
                 # eater is. The phrase is what says the eater - the bare "like" would stand the
                 # row down on "my fish doesnt like the flakes", which is still a fish.
                 "like fish", "likes fish", "doesnt like fish", "doesn't like fish", "hate fish",
                 "hates fish", "off fish", "cant eat fish", "can't eat fish", "wont eat fish",
                 "won't eat fish", "will not eat fish", "allergic to fish", "allergy to fish",
                 "instead of fish", "some", "some fish", "i have fish", "i got fish",
                 "we have fish", "we got fish",
                 "have fish", "got fish", "cook", "cooking", "cooked", "eat", "eating", "recipe",
                 "dinner", "tea", "supper", "lunch", "meal", "pie", "fingers", "cake", "cakes",
                 "chips", "bake", "baked", "fry", "fried", "grill", "roast", "steam", "poach",
                 "raw", "sushi", "sashimi", "market", "monger", "shop for", "price", "cheap",
                 "frozen", "freezer", "thaw", "defrost", "leftover", "leftovers",
                 # a fish that went wrong is a dish, and this row took it: "my fish went wrong"
                 # was read "A new fish needs the tank ready before it goes in". The fault is
                 # the cooking one, so the words for a dish that came out badly stand this row
                 # down. "went wrong" and not a bare "wrong", because "what's wrong with my
                 # goldfish" is the illness question and belongs to the fish.
                 "went wrong", "goes wrong", "gone wrong", "undercooked", "undercook",
                 "overcooked", "overcook", "rubbery", "soggy", "bland", "tastes", "tasted",
                 "sauce split", "split sauce", "raw in the middle", "not cooked", "didnt cook",
                 "did not cook", "came out", "stuck to the pan", "burnt", "burned",
                 # not "fishing": its loose form is "fish", which would stand this row down on
                 # its own key word (the same trap `fish-tank` records)
                 "go fishing", "gone fishing", "pond", "batter", "sauce", "smoked", "kipper", "allergy",
                 "allergic", "shellfish",
                 # a fish being served is a dinner, and this row's "have" took the pairing ask:
                 # "what can i have with fish" was told how to cycle a new tank. The serving
                 # frames carry no "fish" of their own, so they cannot fold onto this key.
                 "have with", "have it with", "eat with", "goes with", "go with", "serve with",
                 "serving with", "pairs with", "alongside", "on the side", "as a side",
                 "side dish", "sides",
                 # a tank being cleaned is the tank row's question, not the new-fish one: this
                 # key carries "my"/"our", so "how do i clean my fish tank", "my fish tank needs
                 # cleaning" and "how often should i clean my fish tank" were the new-fish card.
                 "clean", "cleans", "cleaning", "cleaned", "water change", "gravel", "filter",
                 "rinse", "algae", "scrub", "vacuum", "dechlorinator",
                 # a tank that has gone cloudy or green is the same tank question: "my fish tank
                 # is cloudy" was the new-fish card, which is about the tank before the fish.
                 "cloudy", "cloudier", "murky", "dirty", "foul", "milky", "hazy", "slime",
                 # a pet given a fish, or taken fishing, is the pet-food or the angling answer:
                 # "can i give my cat fresh fish" was told how to set up a new tank, and so was
                 # "can i take my dog fishing"
                 "give my cat", "give my dog", "feed my cat", "feed my dog", "can my cat",
                 "can my dog", "can cats", "can dogs", "dog", "dogs", "cat", "cats", "kitten",
                 "kittens", "fishing rod", "fishing licence", "day ticket", "rod licence",
                 "licence", "license", "permit",
                 # cleaning the tank is the water change, not how to start one: this row has
                 # the higher bias, so "how do i clean my fish tank" and "how often should i
                 # clean a fish tank" were both told how to cycle a new tank, and a person with
                 # a tank already full of water wanted the quarter change. The cleaning words
                 # stand this row down and the tank row below answers.
                 "clean", "cleans", "cleaning", "cleaned", "clean out", "cleaning out",
                 "water change", "change the water", "change the fish water",
                 # and the cleaning that main already names above is kept: this row's own
                 # cleaning words are the ones below
                 "clean out", "cleaning out",
                 # a line about the smell of fish is the kitchen smell answer: "my kitchen smells
                 # of fish" and "how do i get the smell of fish out of the house" were both
                 # answered with how to set up a tank
                 "smell", "smells", "smelled", "smelling", "smelly", "stink", "stinks", "stinking",
                 "odour", "odor", "kitchen", "house", "home", "room"
                 # and a present for somebody who likes fishing is the shopping question:
                 # "what can i buy my dad who likes fishing" wanted a tackle box, not a tank
                 ) + PRESENT_ASK,
          guard=_fish_not_the_sport),
    entry("fish-tank-small", ("goldfish", ("tank", "bowl", "size", "need")),
          ("Goldfish need far more room than pet shops suggest: 100 litres plus for one, and a "
           "filter and a spare tank for cleaning. A bowl isn't a home for a fish that grows to "
           "20cm.")),
    # A cat is not a small dog: an adult cat wants about 4-5% of her weight a day wet, and the
    # packet guide overfeeds most indoor cats, so the portion is the question people actually ask
    # ("what should i feed my cat", "how much should i feed my cat") and it had no answer at all.
    entry("cat-feed-amount",
          (("cat", "cats", "moggy", "mog"),
           # "what should i" is not in this key on purpose: it is the frame of every
           # "what should i do if my cat ..." line, and with it here the portion answer took the
           # flea, the limp and the bird on the doormat. The feed words are what the question is.
           ("feed", "feeding", "food", "diet", "portion", "portions", "much", "grams",
            "meals", "wet", "dry", "kibble", "give"),
           # how often is the same question as how much, and the count is in the answer. This is
           # a part of its own so the frequency words add a signal rather than riding on the feed
           # ones: "how often should i feed my cat" then carries cat + feed + how often, which is
           # more than the brush row and the old-cat check-up row can show.
           ("how often", "how many times", "how frequently", "times a day", "times per day",
            "meals a day", "per day", "once a day", "twice a day", "a day")),
          "Two measured meals a day for an adult cat, adding up to about 3 or 4 pouches of 85g for "
          "a 4kg cat, or 40-50g of dry, and less for a cat that sleeps all day: a complete cat "
          "food, wet or wet with a little dry. Cats are obligate carnivores, so no "
          "dog food and no vegetarian diet, and a cat should never go more than a day without "
          "eating. Free-fed dry food is what makes most indoor cats fat: check by feeling the "
          "ribs without pressing.",
          # what a cat must not eat, a sick cat, and a cat that has stopped eating are each their
          # own answer, and a food allergy or a diet for a condition is a vet question
          avoid=("chocolate", "grape", "raisin", "onion", "garlic", "lily", "antifreeze",
                 # "how much exercise does a cat need" is not a feeding question, though "much"
                 # in the key used to win it; "how much is it to spay a cat" carries it too
                 "exercise", "play", "playing", "playtime", "bored", "boredom", "enrichment",
                 "spay", "spayed", "spaying", "neuter", "neutered", "neutering",
                 "castrate", "operation", "anaesthetic", "jab", "jabs",
                 "toxic", "poison", "poisoned", "not eating", "wont eat", "won't eat",
                 # "what can i give my cat for pain" is the painkiller answer, not the portion
                 # one; "give" is in this key for "what should i give my cat to eat"
                 "pain", "painkiller", "painkillers", "paracetamol", "ibuprofen", "aspirin",
                 "medicine", "medication", "tablet", "tablets", "pill", "pills",
                 # and a symptom is its own answer too: with "give" in the key, "what can i give
                 # my cat for a cough" and "for hairballs" reached the portion card.
                 # the frequency part made this row the answer to every "how often should i ... a
                 # cat" line, so the care questions stand it down: teeth, ears and claws have
                 # their own answers and none of them is dinner
                 # ...and the check-up is not dinner either: "how often should i take an older
                 # cat to the vet" carries cat + how often and was answered with the portions
                 # ...and drinking is a bowl of water, not a portion: "how much water should my
                 # cat drink" and "my cat is not drinking" were both answered with the pouches
                 "drink", "drinks", "drinking", "drank", "water", "bowl", "bowls", "thirsty",
                 "thirst", "hydrated", "dehydrated",
                 "vet", "vets", "check up", "check-up", "checkup", "checkups", "older", "old",
                 "elderly", "senior", "ageing", "aging", "annual", "vaccine", "vaccination",
                 "vaccinations", "booster", "boosters", "jab", "jabs", "dentist",
                 "teeth", "tooth", "toothbrush", "gum", "gums", "breath", "ears", "ear",
                 "claws", "claw", "nails", "nail", "brush", "brushing", "brushed", "groom",
                 "grooms", "grooming", "comb", "combs", "combing", "matted", "knots",
                 "temperature", "fever", "cough", "coughing", "hairball", "hairballs",
                 "fleas", "flea", "tick", "ticks", "worms", "worming", "limp", "limping",
                 "scratching", "itchy", "cut", "wound", "bleeding", "cold", "sneezing",
                 "stopped eating", "sick", "vomit", "diarrhoea", "allergy", "allergic",
                 "kidney", "diabetes", "diet food", "prescription", "raw", "human food",
                 "ate my", "stole", "stolen", "tuna", "milk", "kitten",
                 # "what should i name my cat" is the naming rule: this entry keys the phrase
                 # "what should i" for the portion question, so the naming words have to keep it
                 # out rather than the phrase coming out of its key
                 "name", "named", "naming", "call it", "call him", "call her", "call my",
                 "call the", "call them",
                 # "how much should my cat weigh" is the body-weight question, and the word
                 # "much" in this key took it: the cat-weight card has the figure
                 "weigh", "weighs", "weighing", "weight", "how heavy", "kg",
                 "kilos", "kilogram", "kilograms", "lbs", "healthy weight", "ideal weight",
                 "target weight", "body condition"),
          bias=1),
    # The first days with a kitten are the most asked line in this domain and the least
    # answered: "how do i look after a kitten" was a shrug, and "how do i care for a kitten" was
    # the houseplant watering card, because "care for" is the plant owner's word too. The four
    # things a new kitten needs are the answer, and they lead in the order people need them. A
    # kitten that is already ill, or not eating, has a card of its own above, so those words keep
    # this one out; so does everything else this domain already answers - the supplies list, the
    # feeding amounts, the introduction to another cat, and the opening to the outside.
    entry("new-kitten",
          (("kitten", "kittens", "new kitten", "new cat", "kitty"),
           ("look after", "care for", "care of", "caring for", "keep", "looking after",
            "bring home", "brought home", "bringing home", "just got", "we got", "ive got",
            "getting a", "first", "new", "advice", "what do i need to know", "what do i do",
            "how do i start", "settle in", "settling in", "settle", "settling",
            "get used to", "used to us", "used to me", "first few days", "first week")),
          ("Food first: kitten food, not cat food, four small meals a day until about six months, "
           "and water in a wide bowl. Keep her in one warm room to start with a litter tray, a bed "
           "and something to hide under, and let her come to you rather than picking her up all "
           "the time. Book the vet in the first week: the first jab is due at eight to nine weeks "
           "and the second three to four weeks later, worming runs every two weeks until twelve "
           "weeks, and a microchip and neutering at about four months. Play with a wand toy "
           "rather than your hands, so hands stay boring, and no cow's milk - it gives kittens "
           "the runs."),
          bias=1,
          # A kitten that is ill, hurt, off its food or in trouble is the cards above, and this
          # one only knows the happy first days.
          avoid=("sick", "ill", "poorly", "unwell", "dying", "died", "wont eat", "won't eat",
                 "not eating", "stopped eating", "hiding", "limp", "cut", "wound", "vomiting",
                 "vomit", "sick on", "diarrhoea", "worms", "worming", "fleas", "jabs",
                 "vaccination", "vaccinations", "vaccinate", "microchip", "neuter", "neutered",
                 "spay", "spayed", "cost", "how much is", "price", "cheap", "name", "named",
                 "naming", "call it", "call him", "call her", "call my", "buy", "supplies",
                 "kit", "what do i need for", "introduce", "introducing", "second cat",
                 "another cat", "our old cat", "older cat", "existing cat", "litter tray",
                 "wont use the tray", "outside", "outdoors", "scratch", "scratches", "biting",
                 "bites", "night", "sleep", "crying", "cries", "meowing", "left alone",
                 "allergic", "lost", "missing", "how much food", "how often feed", "how much to feed",
                 "what should i feed", "what do kittens eat", "what can kittens eat"),
          ask=("look after", "care for", "care of", "caring for", "looking after", "keep",
               "bring home", "brought home", "just got", "we got", "ive got", "advice",
               "what do i need to know", "what do i do", "settle in", "settling in", "settle",
               "settling", "first few days", "first week", "how do i start"),
          guard=_it_asks_what_to_do),
    entry("kitten-feeding", (("kitten", "kittens"),
                             ("feed", "food", "how much", "diet", "give", "eat"),
                             # "how often should i feed a kitten" was the brush routine too, for
                             # the same reason as the adult cat: the frequency is the question
                             ("how often", "how many times", "how frequently", "times a day",
                              "meals a day", "per day", "once a day", "twice a day", "a day")),
          ("Feed a kitten kitten food, not cat food, four small meals a day until about six months "
           "and then two: wet food plus a little dry suits most, and leave water out in a wide "
           "bowl. A kitten should gain weight steadily, so weigh her weekly and ask the vet if she "
           "does not."),
          # "what should i name my kitten" is the naming rule. This entry keys "what should i",
          # and both new pet entries key "kitten", so kitten is no longer a word one entry owns
          # and the naming row loses the point it was winning by. The cat row above keeps out
          # the naming words for the same reason.
          avoid=("name", "named", "naming", "call it", "call him", "call her", "call my",
                 "call the", "call them",
                 # "how much should a kitten weigh" is the body-weight question, and "how much"
                 # is in this key
                 "weigh", "weighs", "weighing", "weight", "how heavy", "kg", "kilos",
                 "kilogram", "kilograms", "lbs", "healthy weight", "ideal weight",
                 "target weight", "body condition")),
    # Hay is most of what a rabbit or a guinea pig eats, and neither "how do i get my rabbit to
    # eat hay" nor "how much hay should a rabbit have" had an answer. The animal and the word
    # "hay" are both needed: hay for a horse or a hay-fever line is another question.
    entry("pet-hay", (("hay", "haylage"),
                      ("rabbit", "rabbits", "bunny", "bunnies", "guinea", "guinea pig",
                       "guinea pigs", "piggies", "piggie")),
          ("Hay is the diet, not a topping: give a pile the size of the animal's own body every "
           "day, and it should be eaten. Meadow or timothy hay for adults, alfalfa only for "
           "growing youngsters and nursing mothers. If yours will not touch it, buy a fresher, "
           "greener bag, put it in a rack and a cardboard tube as well as on the floor, and cut "
           "the pellets and treats right back, because a pet full of nuggets has no room for hay. "
           "Drooling, or no droppings for a day, means the vet today."),
          ask=("rabbit", "rabbits", "bunny", "guinea", "hay", "eat", "eating", "feed", "diet",
               "much", "how much", "wont eat", "not eating", "all day")),
    # "what can i feed a dog with a poorly stomach" was answered with the person's own sick-day
    # card (toast, crackers, a banana, plain yoghurt): that card is a whole diet guide and the
    # dog's vomiting row never mentions feeding, so nothing said "a dog" and the plain food won.
    # This row keeps the animal, the stomach and the feeding word together. The animal is what
    # the ask holds, so a person who is ill, a child, or a person who happens to own a dog still
    # gets their own answer: without it "what can i eat with a poorly stomach" would reach here
    # on the two words in the middle.
    entry("dog-sick-food", (("poorly", "upset", "bad", "funny", "queasy", "bug", "buggy"),
                            ("stomach", "tummy", "belly", "gut")),
          ("Keep it plain and small: plain chicken with boiled rice, or his own food, in four or "
           "five small meals a day rather than one big one. Withhold food for a few "
           "hours first if he has been sick, keep the water down, and skip anything fatty or "
           "milky. Ring the vet if he will not drink, if it lasts more than a day, or if there is "
           "blood, and straight away for a puppy or an old dog."),
          # A rank above the plain-food card, which is a whole diet guide and outranked this row on
          # the rarity of its own key words ("toast", "crackers", "yoghurt") even with a lower
          # score, and above the dog's vomiting card for a line that only names the stomach. Safe
          # because the ask below needs the animal before this row scores at all.
          bias=5,
          # "sore" and "dodgy" are not in the key on purpose. A sore tummy is the dog's pain card
          # ("a dog shows pain by changing how he moves"), and "dodgy" is the word the triage card
          # owns ("one vomit or one loose poo in a dog that is otherwise bright is usually
          # nothing"). Either is a better first sentence than a bowl of rice, so both are left to
          # the rows that have them; "poorly", "upset", "bad", "funny" and "queasy" carry every
          # line this card is for.
          # the animal is what the ask holds: the two key parts are the stomach and the feeding,
          # and a person's own poorly stomach has the same two, so without this "what can i eat
          # with a poorly stomach" would land here. A plain feeding question has only the feeding
          # half of the key, which is one word, and one word is not enough to answer a line.
          ask=("dog", "dogs", "puppy", "puppies", "pup", "pups", "doggy"),
          # A dog that eats grass and is sick afterwards is the grass answer, and a dog that will
          # not eat is the stopped-eating answer, which is the vet-today one. Neither is a question
          # about what to put in the bowl.
          avoid=("grass", "lawn", "eating grass", "eats grass",
                 "wont eat", "won't eat", "not eating", "not eaten", "stopped eating",
                 "hasnt eaten", "hasn't eaten", "refusing food", "off his food", "off her food")),
    # "chewing" alone never matched "chews": the forms of the -ing word come out as "chewe", so
    # "my rabbit chews the skirting boards" reached nothing and the turn ended on a shrug
    entry("rabbit-teeth", (("rabbit", "rabbits", "guinea pig", "guinea pigs", "bunny", "bunnies",
                            "hamster", "hamsters", "gerbil", "gerbils"),
                           ("teeth", "tooth", "gnaw", "gnaws", "chew", "chews", "chewed",
                            "chewing", "nibble", "nibbles", "overgrown", "too long", "long teeth",
                            "trim", "trimming")),
          ("Rabbit and rodent teeth grow all their lives and hay is what wears them down: unlimited hay, some "
           "leafy greens and a wooden block to gnaw, and skip the muesli mix. Drooling, wet chin "
           "or refusing food means the teeth need the vet before they stop eating altogether.")),
    # "how do i stop my rabbit chewing the wires" was the technology row that winds a cable
    # tidily, because "chewing" folds to "chewe" and the teeth row's key never saw it. A rabbit
    # that chews the skirting, the sofa or a cable is a housing-and-enrichment question.
    entry("rabbit-chews-things",
          (("rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs", "hamster",
            "hamsters", "gerbil", "gerbils"),
           ("chew", "chews", "chewed", "chewing", "chewe", "gnaw", "gnaws", "gnawing",
            "nibble", "nibbles", "nibbling",
            "wire", "wires", "cable", "cables", "lead", "leads", "skirting", "skirting board",
            "furniture", "sofa", "carpet", "bars", "hutch bars")),
          ("A rabbit chews because its teeth grow all its life, so hay all day plus apple or "
           "willow sticks and a cardboard box give it something better to chew. Then make the "
           "wires boring: plastic trunking or a length of hose split down one side over them, "
           "tucked behind the furniture, and a pen that keeps the back of the telly out of "
           "reach. Chewing the bars means more space and more to do, not less."),
          # "bite" is out: a hamster that bites the hand holding it is the taming answer, and
          # nothing about a wire or a skirting board is said with it.
          ask=("chew", "chews", "chewed", "chewing", "chewe", "gnaw", "gnaws", "gnawing",
               "nibble", "nibbles", "nibbling"),
          avoid=("teeth", "tooth", "overgrown", "too long", "long teeth", "drool", "drooling",
                 "wet chin", "trim", "trimming", "not eating", "stopped eating", "wont eat",
                 "won't eat", "off his food", "off her food", "vet", "lump", "abscess",
                 "died", "dead", "bury", "burying", "cremat", "dig", "digging"),
          bias=2),
    # A guinea pig has its own card (main's `guinea-pig-basics`), so the rabbit key names the
    # rabbit alone: the animal the line names is read by the card's own table, not by widening
    # one animal's key to hold another.
    entry("rabbit-hutch", (("rabbit", "rabbits", "bunny", "bunnies"),
                           ("hutch", "bedding", "care", "need", "look after", "looking after",
                            "keep", "keeping", "own", "new", "starter", "setup", "set up",
                            # "how do i clean out the guinea pig cage" named the animal and the
                            # cage and reached nothing: the cleaning question is this card's.
                            "cage", "cages", "clean", "cleaning", "clean out", "hutches")),
          _small_pet_setup,
          # "what do i need for a rabbit" is the shape a new owner writes and "need" is read as
          # the asking frame, so the animal was left alone in the key and the row scored nothing;
          # the cooking row for rabbit meat took the line. The buying shape is a signal here.
          # The buying shape is a signal of its own: "what do i need for a rabbit" reads "need"
          # as the asking frame, so it is blanked before the key is scored and the animal was left
          # as the only word of the line, which is not enough to answer. The shape puts the second
          # signal back without weakening the frame rule for every other row.
          shape=(_the_buying_shape,),
          # "need" is the trigger, so "my rabbit died, do we need to bury it deep" used to be
          # answered with housing advice. The composer now stands aside for a pet's burial or
          # cremation (it has no card of its own for that), so a care entry has to stay out of a
          # line that says the animal has died. Heat and cold are their own answer, not the setup
          # question, so those words keep "how do i keep a rabbit cool" for `rabbit-weather`.
          # "keeps" is the second key word as well, so "my guinea pig keeps being sick" and "my
          # rabbit keeps being sick" were answered with housing: a question about a sick animal is
          # not a question about a hutch.
          avoid=ABOUT_A_DEATH + ("hot", "heat", "cool", "warm", "summer", "winter", "sun",
                                 "sunny", "freezing", "frost", "snow", "sick", "sickness",
                                 "vomiting", "vomit", "throwing up", "being sick", "unwell",
                                 "ill", "illness", "diarrhoea", "diarrhea", "not eating")),
        # "how do i look after a hamster" names the animal and nothing else, so the ask is the
    # phrase a new owner writes: look after, keep, own, get one.
    entry("hamster-basics", (("hamster", "hamsters", "syrian", "dwarf hamster"),
                             ("cage", "care", "bedding", "need", "look after", "looking after",
                              "keep", "keeping", "own", "having", "get", "new", "starter",
                              "basic", "basics", "setup", "set up")),
          # the hamster card holds the set-up and the cleaning, and it answers the half asked
          _the_hamster_basics),
    # A guinea pig is not a small rabbit: it has its own card on main, and this change keeps
    # that card's text word for word while letting it answer the half that was asked (the
    # cleaning of the cage is not a list of things to buy).
    entry("guinea-pig-basics", (("guinea pig", "guinea pigs", "cavy", "cavies"),
                                ("cage", "hutch", "run", "care", "bedding", "need", "needs",
                                 "look after", "looking after", "keep", "keeping", "own",
                                 "having", "get", "getting", "new", "starter", "basic",
                                 "basics", "setup", "set up", "want", "wants", "wanted",
                                 "ask", "asks", "asking", "buy", "buying", "thinking")),
          _small_pet_setup),

    # --- the everyday care of the animal itself --------------------------------
    # Heat, nails, a bath and the brush are the four things a new owner asks in the first week,
    # and each one is about the animal, not a problem with it, so they key on the care word.
    # "how do i rehome my dog" reached the search hedge. The past-tense story ("we had to rehome
    # our dog") is the chat lane's to answer, so this entry needs an asking shape, which is what
    # `ask` is for; the words alone would take the story too.
    entry("pet-rehome", (("rehome", "rehoming", "rehomed", "give up", "gave up", "surrender",
                          "find a new home", "find him a new home", "find her a new home",
                          "new home for", "cant keep", "can't keep", "cannot keep",
                          "get rid of"),
                         ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets",
                          "rabbit", "hamster")),
          ("Start where the animal came from: the breeder usually takes them back, and every "
           "breed has a rescue that will. A good rescue home-checks and asks for the vet records, "
           "and that is far kinder than advertising online, where the wrong people look. Be honest "
           "about the animal's quirks, expect a waiting list because most rescues are full, and "
           "say if money or housing is the reason - there is more help than people expect, from "
           "pet food banks to a landlord letter."),
          ask=("how do i", "how can i", "how would i", "where do i", "where can i", "cant keep",
               "can't keep", "cannot keep", "need to", "have to", "help me", "looking for",
               "find a", "get rid of", "is it ok to", "should i", "what do i do"),
          # "a new home" is also the settling-in story ("my cat is hiding in her new home"), which
          # is the more common line, so this entry asks and then nudges above it.
          bias=2,
          # giving a pet up is not a heat question and not a nail question
          avoid=("died", "passed away", "put down", "euthanise", "euthanize", "hiding",
                 "settling", "settle in", "first few days", "scratching the furniture",
                 # "get rid of" is the phrase people use for an infestation too, and it was
                 # rehoming the animal: "how do i get rid of fleas on my cat" was answered
                 # "the breeder usually takes them back, and every breed has a rescue".
                 "flea", "fleas", "tick", "ticks", "mite", "mites", "worms", "lice",
                 "the smell", "the stains", "the mess",
                 # a smell the animal has left behind is the cleaning question:
                 # "how do i get rid of a pet smell in the carpet" was answered with the breeder
                 "smell", "smells", "smelling", "smelly", "whiff", "reek", "stinks", "odour",
                 "stain", "stains", "stained", "pee", "urine", "hair", "fur",
                 # the other infestation: a cat using the garden as a toilet is the soil
                 # question, not a cat looking for a new home.
                 "garden", "gardens", "lawn", "flowerbed", "flower beds", "borders",
                 "pooing", "poo", "poos", "digging", "digging up", "messing", "seedlings")),
    entry("dog-heat", (("dog", "dogs", "puppy", "pup", "puppies"),
                       ("cool", "keep cool", "heat", "hot", "summer", "heatwave", "heat wave",
                        "panting", "overheating", "sun", "sunny")),
          ("Shade and water out all day, walk before ten and after five so the pavement is not "
           "burning his pads - if it is too hot for your hand for five seconds, it is too hot for "
           "his feet. Never leave him in a parked car, even with the windows down: it reaches 40C "
           "inside in ten minutes. A wet towel to lie on helps, and flat-faced, old and thick-"
           "coated dogs struggle most. Heavy panting with wobbling or collapsing is heatstroke, so "
           "cool him with wet towels and ring the vet on the way."),
          # a bitch in season is "in heat", and a hot spot is a skin problem. A dog given up in a
          # summer is a loss, not a hot dog: "summer" is in this key, so "we had to rehome the dog
          # in the summer" was being told to keep him out of a parked car.
          avoid=("in heat", "on heat", "season", "hot spot", "hotspot", "hot spots", "sore",
                 "itch", "itching", "scratching", "lump", "limp", "limping",
                 "rehome", "rehomed", "rehoming", "gave him away", "gave her away",
                 "gave the dog away", "gave our dog away", "gave away", "give away",
                 "given away", "new home", "couldnt keep him", "couldn't keep him",
                 "couldnt keep her", "couldn't keep her", "couldn't keep", "couldnt keep",
                 "give him up", "give her up", "gave him up", "gave her up", "surrendered",
                 "adopted", "rescue", "put down", "passed away")),
    # A dog that growls while it is being brushed, lifted or clipped is not asking how to be
    # brushed: the grooming card, the nail card, the bath card and the guarding card were all
    # answering it, and every one of them started on the job. A growl is the warning before a
    # snap, so the answer has to be about the warning and what causes it - pain, mats, a fright -
    # and about stopping rather than finishing the job. The animal, the warning noise and the
    # handling word are what make the question; a growl at another dog or over a bone is the
    # guarding or the lead row's question and stays there.
    entry("dog-handling-growl",
          (("dog", "dogs", "puppy", "puppies", "pup", "doggy"),
           ("growl", "growls", "growling", "growled", "snap", "snaps", "snapped", "snapping",
            "snarl", "snarls", "snarled", "nips", "nips at", "bares his teeth", "baring his teeth"),
           ("brush", "brushing", "brushed", "groom", "grooming", "groomed", "groomer",
            "nail", "nails", "claw", "claws", "clip", "clipping", "clippers",
            "paw", "paws", "feet", "harness", "collar", "lead", "bath", "bathe", "bathing",
            "wash", "towel", "wipe", "touch", "touched", "touching", "handling", "handled",
            "lift", "pick him up", "pick her up", "pick up", "hold him", "hold her",
            "ears", "ear", "teeth", "groomers")),
          "A growl while he is being brushed or handled is him saying it hurts or frightens him, "
          "so stop as soon as he does it and never tell him off for it - a dog punished for the "
          "warning goes straight to the snap. Run your hands over him first, because mats behind "
          "the ears, a tight collar and a sore ear or hip are the usual causes, and a dog who has "
          "always been fine and has just started wants a vet check. If there is nothing sore, go "
          "in two-second bursts with a second person feeding him chicken, and for nails do one a "
          "day and let a groomer or a vet nurse do the rest.",
          avoid=("food", "bone", "bones", "bowl", "bowls", "dinner", "toy", "toys", "chew",
                 "chews", "treat", "treats", "rawhide", "kong", "guards", "guarding", "guard",
                 "possessive", "protective", "other dogs", "another dog", "at other dogs",
                 "strangers", "stranger", "visitors", "postman", "doorbell", "garden", "gate",
                 "vet", "vets", "vet visit", "bit me", "bites me", "bitten", "bit my",
                 "bleeding", "blood", "broke the skin", "punctured"),
          guard=_a_handling_growl_line,
          bias=3),
    entry("dog-grooming", (("dog", "dogs", "puppy", "pup"),
                           ("groom", "grooming", "groomer", "brush", "brushing", "matted",
                            "matts", "mats", "knots", "tangled", "shedding", "sheds",
                            "shed", "fur", "hair", "trim", "clippers")),
          ("Brush for a few minutes a day, working the small knots out with your fingers before "
           "the brush touches them so it never pulls: a slicker brush for a short coat, an "
           "undercoat rake for a double coat. Do not shave a double coat, because it is his "
           "insulation in hot weather as well as cold. Ears and paws are the parts people forget, "
           "and anything that needs clippers is worth watching a groomer do once."),
          # a dog that chews the brush is a chewing question, and bald patches are the vet
          avoid=("chew", "chews", "chewing", "ate", "eating", "swallowed", "bald", "patch",
                 # "he keeps leaving birds on the mat" is a gift, not a coat question: "mat" is
                 # a loose form of "matted", so the coat answer needs a coat word in the line
                 "bird", "birds", "mouse", "mice", "rat", "rats", "dead", "leaving", "brought",
                 "dragged", "on the mat", "in the hall",
                 "patches", "rash", "itch", "itching", "scratching", "skin")),
    entry("dog-nails", (("dog", "dogs", "puppy", "paws", "paw"),
                        ("nail", "nails", "claw", "claws", "clip", "clipping", "clippers",
                         "trim", "cut",
                         # "long" alone is an adjective in everybody's sentence: it made the
                         # next turn of any conversation about a dog - "but i work long hours" -
                         # and "how long until he sleeps through the night" nail-clipping
                         # questions. The length is only this entry's when a nail word is
                         # beside it, and "nails" is already a key.
                         "long nails", "nails are long", "nails getting long",
                         "nails too long", "long claws", "claws are long")),
          ("Take a sliver off at a time and stop at the pink centre, the quick: hold a torch "
           "under the nail and it shows as a darker oval to aim short of. Cut straight across "
           "rather than at an angle, keep the treats coming, and if he hates it do one nail a day. "
           "If you do cut too far, press kitchen roll or a pinch of flour on it for a couple of "
           "minutes and it stops; walks on pavement wear them down in between."),
          # a cut pad or a broken nail is a vet question, not a how-to
          avoid=("pad", "pads", "glass", "cut his paw", "cut her paw", "cut paw", "bleeding",
                  "bleeds", "blood", "broken", "torn", "limp", "limping", "swollen")),
    entry("dog-bathing", (("dog", "dogs", "puppy", "pup"),
                          ("bath", "bathe", "bathing", "wash", "washing", "shampoo", "shower",
                           "stinks", "smelly")),
          ("Every six to eight weeks is plenty for most dogs, and less for a short coat: use a "
           "dog shampoo rather than yours, because a dog's skin sits at a different pH. Wet him "
           "right down to the skin, lather, then rinse for twice as long as feels necessary - "
           "leftover shampoo is what causes the scratching afterwards. Brush the knots out before "
           "he gets wet, since water tightens a tangle into felt, and dry him properly and keep "
           "him warm after."),
          # a paw wash after a walk is not a bath
          avoid=("paws", "paw", "feet", "foot", "toes", "pads")),
    # "my dog has a cold" was read as "out in the cold" and answered with a coat, and "my cat has
    # a cold" was only noted back. A pet with a cold is an illness question, not a weather one.
    entry("pet-cold", (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets",
                        "rabbit", "hamster"),
                       ("has a cold", "has got a cold", "caught a cold", "cold", "sneezing",
                        "sneezes", "sneeze", "runny nose", "sniffles", "chesty",
                        # a "runny eye" was this row's line and it is not a cold: the eye row
                        # answers it with cotton wool and the vet rule. Out of the key and out
                        # of the ask, so "my dog has a runny eye" has nowhere else to go.
                        "blocked nose", "cough and a cold")),
          ("Dogs and cats don't catch our colds: a pet that is sneezing, has a runny nose or "
           "runny eyes usually has an infection of its own, an allergy or a bit of grit, and a "
           "cat with cat flu is the one that needs a vet quickly. Keep the water topped up, wipe "
           "the eyes with damp cotton wool, and ring the vet if it lasts more than a few days, "
           "or straight away if there is a green discharge, a fever, no appetite or noisy "
           "breathing."),
          ask=("cold", "sneezing", "sneezes", "sneeze", "runny nose", "sniffles",
               "chesty", "blocked nose", "cat flu"),
          bias=2,
          # the weather answer is what "too cold for a walk", "out in the cold" and "keep him
          # warm" are asking, and "cold" on its own is a word dogs and walks share
          avoid=("outside", "out in", "walk", "walks", "walking", "weather", "winter", "snow",
                 "frost", "icy", "warm", "coat", "car", "garden", "night", "bed",
                 # a sneeze the day after the room was sprayed is the spray, not a cold
                 "spray", "sprays", "sprayed", "spraying", "aerosol", "air freshener",
                 "plug in", "diffuser")),
    entry("pet-ear", (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets"),
                      ("ear", "ears", "ear infection", "ear infections", "smelly ear",
                       "smelly ears", "shaking his head", "shaking her head", "shakes his head",
                       "shakes her head", "head shaking", "shaking head", "ear mites", "waxy",
                       "scratching his ears", "scratching her ears", "ear drops", "sore ear")),
          ("An ear that smells, hurts or makes him shake his head is usually an infection or "
           "ear mites, and a vet needs to look down it with an otoscope and give drops that match "
           "the cause - the wrong drops can burst an eardrum. Don't push cotton buds down it or "
           "use old drops from last time, and hold off the bath until it is clear. A head tilt, a "
           "swollen ear flap or an ear that is painful to touch wants to be seen the same day."),
          ask=("ear", "ears", "head", "ear mites", "ear drops"),
          bias=1,
          # a rabbit's ears or a dog shaking after a bath is not this, and "listen" is a person's
          # ear: the vet answer belongs to a real ear symptom
          avoid=("rabbit", "rabbits", "hear", "hearing", "listen", "loud", "noise", "music",
                 "head collar", "shampoo", "bath",
                 # "how do i clean my dogs ears" has its own answer: leave the wax alone
                 "clean", "cleaning", "cleaner", "wax", "cotton bud", "cotton buds", "cotton wool")),
    entry("dog-winter", (("dog", "dogs", "puppy", "pup"),
                         ("winter", "cold", "freezing", "snow", "frost", "icy", "freeze",
                          "warm", "keep warm", "freezing outside")),
          ("A healthy dog with a thick coat is fine out in the cold, but thin-coated, short-"
           "legged, old and small dogs feel it: a coat that covers the belly and a shorter walk "
           "are enough. Towel him dry when you get in, paws and between the toes included, and "
           "rinse off grit and salt. Never leave him in a cold car, and keep antifreeze out of "
           "reach, because a few licks of it are fatal."),
          # a dog that is cold and shaking indoors is a vet question if it keeps happening
          avoid=("shivering", "shivers", "shaking", "temperature", "fever")),
    entry("litter-tray-routine", (("litter", "litter tray", "litter box", "cat litter",
                                   "toilet corner", "pee corner", "toilet area"),
                                  ("how often", "often", "clean", "cleaning", "change",
                                   "changing", "scoop", "scooping", "empty", "emptying",
                                   "replace", "replacing", "wash", "washing", "daily", "weekly")),
          _the_litter_routine,
          # a cat that has stopped using the tray is a problem, not a cleaning schedule
          # bias=1: main's `older-cat-checks` also keys cat + "how often", and on
          # "how often should i change the cat litter" the two tie, so the schedule has to be
          # the one that wins - the senior-cat answer is for the vet and the yowling lines.
          bias=1,
          avoid=("stopped using", "wont use", "won't use", "outside the", "on the carpet",
                  "on the floor", "on the bed", "weeing", "peeing", "blood")),
    entry("rabbit-weather", (("rabbit", "rabbits", "guinea pig", "guinea pigs", "bunny"),
                             ("hot", "heat", "summer", "cool", "warm", "cold", "winter",
                              "freezing", "frost", "snow", "heatwave", "heat wave",
                              "sun", "sunny")),
          _rabbit_weather,
          # a guinea pig is "in season" as a sow, and a hot spot is a skin thing
          avoid=("hot spot", "in heat", "season")),
    entry("cat-pain", (("cat", "cats", "kitten", "kittens"),
                       ("pain", "pains", "hurts", "hurting", "sore", "ache", "aching", "in pain",
                        "suffering", "uncomfortable",
                        # "my cat yelps when i touch her tummy" is the same question asked by
                        # what happens under a hand, and no word here reached it
                        "yelp", "yelps", "yelping", "flinch", "flinches", "flinching",
                        "cries out", "cry out", "cried out", "screams", "screaming",
                        # a cat that yowls is the cat in pain or in season; "my cat yowls when i
                        # lift her" was a shrug, and the card itself already names the yowl
                        "yowl", "yowls", "yowling", "yowled",
                        # the cry has to be tied to the hand, or "cries when im out" is lost to
                        # this row: a cry at being lifted is a sore cat, not a lonely one. A bare
                        # "when i pick her up" is not enough: it also took "my cat growls when i
                        # pick her up", and the growl card's take-the-warning-as-a-no is better
                        # there, since it ends by naming pain as the reason to see a vet.
                        "cries when picked up", "cries when i pick", "cry when i pick",
                        "cries when lifted", "cry when lifted", "cries when touched",
                        "cries when i touch", "cries if i touch", "screams when",
                        "cries out when",
                        "cries when i hold", "cries when i lift", "cries when carried",
                        # a sore cat shows it as a shape before it says it, and plain people
                        # describe the shape: "my cat is hunched up" was a greeting
                        "hunched", "hunched up", "hunched over", "sitting hunched",
                        "walking hunched", "hunched in a corner", "curled up and hunched",
                        # not "head low" or "head down": both read as frames to this matcher and
                        # took "my cat yelps when i touch her tummy" with them, which was in
                        # this row before the change
                        "not putting weight",
                        "not weight bearing", "reluctant to move")),
          ("Look for what has changed rather than for crying: hiding, sitting hunched with her "
           "head low, no longer jumping up where she used to, over-grooming one spot, eating less, "
           "or going outside the tray. Cats purr when they are in pain as well as when they are "
           "content, so a purring cat is not a comfortable one. Any of that for more than a day is "
           "a vet visit, and a cat that yowls, cries out or flinches when you touch one spot, or "
           "stops eating, is urgent: ring the vet today."),
          # a cat that cries when it is touched is this row's, and the crying words sit in the
          # leaving-alone key as well ("crying at the door" is boredom): the nudge settles it
          bias=2,
          avoid=("put down", "to sleep", "died", "dying", "dead", "passed away", "euthanised",
                 "euthanized", "euthanasia")),
    entry("cat-bathing", (("cat", "cats", "kitten", "kittens"),
                          ("bath", "bathe", "bathing", "wash", "washing", "shampoo")),
          ("Most cats never need a bath, because they keep themselves clean, so do it only for "
           "something they got into. Use a cat shampoo, lukewarm water an inch deep in the sink, "
           "one hand on the scruff or a towel wrap to keep her calm, and rinse very well; then "
           "towel her dry somewhere warm. Two people make it far easier than one, and a smear of "
           "butter or a lick treat on the side of the sink buys the ten minutes you need."),
          avoid=("put down", "to sleep", "died", "dying", "dead", "passed away", "euthanised",
                  "euthanized")),
    entry("dog-pain", (("dog", "dogs", "puppy", "pup"),
                       ("pain", "pains", "hurts", "hurting", "sore", "ache", "aching", "in pain",
                        "suffering",
                        # the same under-a-hand words as the cat's: "my dog yelps when i touch
                        # his back" was a shrug
                        "yelp", "yelps", "yelping", "flinch", "flinches", "flinching",
                        "cries out", "cry out", "cried out", "screams", "screaming",
                        # tied to the hand for the same reason as the cat's: "my dog growls when
                        # i pick him up" is the warning card, not this one
                        "cries when picked up", "cries when i pick", "cry when i pick",
                        "cries when lifted", "cry when lifted", "cries when touched",
                        "cries when i touch", "cries when stroked", "cries when i stroke",
                        "cries when i hold", "cries when i lift", "screams when", "cries out when")),
          ("A dog shows pain by changing how he moves rather than by crying: stiff getting up, "
           "refusing the stairs or the sofa, lagging on walks, licking one spot, panting at rest "
           "or snapping when touched. Look at him from behind while he stands - a hunched back and "
           "a tucked belly is a sore middle. Anything that lasts more than a day is a vet visit, "
           "and a dog who cannot settle or is breathing fast needs one today."),
          bias=1,
          avoid=("put down", "to sleep", "died", "dying", "dead", "passed away", "euthanised",
                  "euthanized")),
    # --- general ----------------------------------------------------------------
    entry("pet-insurance", (("pet insurance", "insurance for the dog", "insurance for the cat",
                             "insurance for a puppy", "insurance for a dog", "insurance for a cat",
                             "puppy insurance", "dog insurance", "cat insurance",
                             "kitten insurance", "insure my dog", "insure my cat",
                             "insure the dog", "insure the cat", "insure my puppy", "insure a puppy",
                             # "how much does a dog cost to insure" is the cover's price, not the
                             # puppy's: the verb alone is the insurance and never the animal, so
                             # it opens this row and closes the buying-price row
                             "insure", "insured", "insuring", "insures"),
                            # "how much does puppy insurance cost" was answered with the walking
                            # rule and then with buildings insurance: the cost of the cover is
                            # this row's question, and £20 to £40 a month is in the reply.
                            ("worth", "worth it", "should i", "need", "need it", "get", "buy",
                             "any good", "how much", "cost", "costs", "price", "per month",
                             "a month", "monthly")),
          ("Pet insurance is worth it for a dog or a cat if you could not find \u00a32,000 in a "
           "hurry: a broken leg or a blocked bladder runs to \u00a31,500 and up. Take lifetime "
           "cover rather than the cheapest accident-only policy, because anything the vet has "
           "already treated is excluded for good, and a dog costs about \u00a320 to \u00a340 a "
           "month. If you would rather not pay monthly, keep \u00a31,000 in a separate pot "
           "instead.")),
    # "should i take him to the vet" is the commonest shape of a pet worry, and it had no row of
    # its own: on main it fell to whatever held the pronoun, and the care-home gift card answered
    # it with "bring the things that make the room theirs". The decision is what is being asked,
    # so the decision is in the key and the animal is not needed - "him" is a dog in this chat and
    # a grandfather in another, and the vet word settles which.
    entry("pet-when-to-see-a-vet",
          (("vet", "vets", "the vet", "out of hours vet", "emergency vet"),
           # the shapes people use to ask whether it can wait; "is it worth" is not here, because
           # that line is asking what a consultation costs, which pet-vet answers
           ("should i take", "should i bring", "should we take", "should we bring",
            "do i need to take", "do i have to take", "do i need a vet", "does he need the vet",
            "does she need the vet", "do we need the vet", "need the vet", "need a vet",
            "should i get him seen", "should i get her seen", "is it an emergency",
            "is this an emergency", "is that an emergency", "how do i know if",
            "should i call the vet", "should i ring the vet")),
          _the_vet_question,
          # what a vet costs is pet-vet's line, and a line about the bill names no decision
          avoid=("how much", "cost", "costs", "cheap", "cheapest", "afford", "price", "prices",
                 "insurance", "insured", "quote", "fee", "fees", "payment plan",
                 "euthanise", "put to sleep", "put down", "putting to sleep",
                 # "should i take my 12 year old cat to the vet" and "how often should i take an
                 # older cat to the vet" are the check-up cadence, and the twice-a-year card
                 # answered both before this row existed
                 "how often", "how frequently", "check up", "checkup", "check-up", "check ups",
                 "year old", "years old", "older", "old cat", "old dog", "annual", "yearly",
                 "once a year", "twice a year", "vaccination", "vaccinations", "jab", "jabs",
                 "booster", "boosters"),
          bias=1),
    entry("pet-vet", (("vet", "vets"), ("how much", "cost", "cheap", "bill", "insurance")),
          ("Pet insurance is worth it for dogs and cats in most cases: a broken leg can run to "
           "£1,500 or more. If you'd rather self-insure, keep a dedicated savings pot of about £1,000 "
           "and check whether your vet does a payment plan.")),
    # "away" on its own is not a holiday: "we had to give the dog away" and "we rehomed the cat"
    # are a pet leaving the house for good, and boarding advice answers nothing. Only the phrases
    # that say the person is the one going away count.
    # "where can the dog stay" is this row's question and `stay` is the dog command's word, so
    # the shapes that mean boarding are named as phrases: the command line ("teach my dog to
    # stay") has none of them. Without the phrases the standing question went to a dog friendly
    # pubs row once the trip-abroad entry stopped answering the bare word "holiday" (#7798).
    entry("pet-holiday", (("dog", "cat", "pet"), ("holiday", "kennel", "cattery", "boarding",
                                                  "going away", "go away", "away for", "away next",
                                                  "who looks after", "dog sitter", "cat sitter",
                                                  "pet sitter", "when im away", "when i'm away",
                                                  "when i am away", "while im away",
                                                  "while i'm away",
                                                  "while we are away", "while we're away",
                                                  "while im away", "while i am away",
                                                  "when we go away",
                                                  "where can the dog stay", "where can my dog stay",
                                                  "where can the cat stay", "where can my cat stay",
                                                  "where can i leave the dog", "where can we leave the dog",
                                                  "where can i leave the cat", "can the dog stay",
                                                  "can my dog stay", "can the cat stay",
                                                  "someone to look after the dog",
                                                  "someone to look after the cat")),
          ("Book boarding early, ask your vet for a recommendation, and visit before you book: "
           "clean, calm and willing to show you the runs tells you more than any website. A pet "
           "sitter at home suits cats far better than a cattery."),
          # the where-to-sleep row keys "where ... dog" too, and "where can the dog stay when we
          # go away" tied with it and lost to its bias: a bed in the quiet corner of the room is
          # not an answer about a holiday. One point settles the tie in the holiday's favour, and
          # a bed question that never says holiday, away or kennel still has its own answer.
          bias=1),
    # --- what a pet may eat ------------------------------------------------------
    # "He ate a handful off the table" is the follow-up to a food question, with no food named:
    # the useful answer asks which, and says which ones cannot wait.
    entry("pet-ate-some", (("ate", "eaten", "swallowed", "licked", "stole", "got into"),
                           ("handful", "some", "piece", "bit", "few", "slice", "table",
                            "counter", "floor", "bin", "bins", "wrapper", "packet", "tub",
                            # a household poison is eaten in the same way as a joint of meat,
                            # and the answer is the same three questions: what, how much, how
                            # long ago. "my rabbit ate some fly spray" was a chat nod, and
                            # "my cat licked weedkiller" was the fumes card.
                            "spray", "fly spray", "insect spray", "weedkiller", "weed killer",
                            "ant powder", "slug pellets", "bait", "bleach", "antifreeze",
                            "cleaner", "chemicals")),
          ("What was it, and roughly how much, and how long ago? If it was grapes, raisins, "
           "onion, garlic, chocolate, anything with xylitol in it or any of your medicine, ring "
           "the vet now rather than watching him - most of those are treatable and much easier "
           "early. If it was a bit of plain meat or bread off the table, no harm done."),
          avoid=("grass", "dinner", "breakfast", "lunch", "kibble", "meal", "biscuit", "treat"),
          # small pets eat the wrong thing too, and the vet call is the same: a rabbit or a bird
          # that has had a mouthful of spray is not a dog question with a different animal in it
          ask=("him", "her", "he", "she", "dog", "dogs", "puppy", "pup", "cat", "cats",
               "kitten", "pet", "pets", "rabbit", "rabbits", "bunny", "bunnies", "hamster",
               "hamsters", "gerbil", "gerbils", "guinea", "bird", "birds", "parrot", "budgie",
               "ferret", "tortoise"), bias=1,
          guard=_eaten_thing_is_not_food),
    # The follow-up to "can he eat this" is "he ate some", and then "should I make him sick".
    # Making a pet sick at home is the one thing not to do, so that line has its own answer.
    entry("pet-dont-induce", (("make him sick", "make her sick", "make him vomit",
                               "make her vomit", "make the dog sick", "make my dog sick",
                               "make my dog vomit", "make my cat sick", "make my cat vomit",
                               "induce vomiting", "pump his stomach", "pump her stomach"),
                              ("should", "can i", "is it safe", "shall i", "do i", "safe")),
          ("Don't: never make a pet sick at home. Salt water, peroxide and fingers down the "
           "throat do real damage, and for some poisons being sick makes it worse. Ring the vet "
           "or the animal poisons line, say what was eaten and how much and how long ago, and "
           "they will tell you whether it needs to come up and how."),
          avoid=("child", "son", "daughter", "toddler", "baby", "kid", "kids", "myself", "me"),
          ask=("him", "her", "dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet",
               "pets"), bias=1),
    entry("pet-can-eat", (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets"),
                          # single words, not "can eat": the phrase has to be adjacent, and
                          # nobody writes "can eat" without something in between
                          ("can", "eat", "eats", "have", "give", "feed", "safe", "ok", "bad",
                           "toxic", "poisonous", "allowed", "should",
                           # "my dog drank my coffee" is the same question as "can he eat it",
                           # and the eating verbs are how it is asked when the thing is a drink
                           "drink", "drank", "drunk", "licked", "lick", "swallowed", "chewed",
                           # "my dog ate a raw egg" is the same question as "can dogs eat raw
                           # egg", and without the past tense it was the teach-"leave it" answer
                           "ate", "eaten", "eating", "stole")),
          lambda memory, understood: _can_pet_eat(understood), ask=CAN_EAT_ASK, bias=2,
          # chocolate already has its own answer, and it is the better one for the question.
          # "is dry food ok for my cat" is not a can-I-eat-this question either: it is the
          # feeding one, and the foods-to-refuse answer is the wrong reply to it.
          avoid=("chocolate", "dry food", "wet food", "kibble", "biscuits", "diet",
                 # "when can my puppy go onto adult food" is the age to change the food, not a
                 # question about whether adult food is safe to eat: the refuse-these list is
                 # a wrong answer to it, and the feeding entry knows the age.
                 "adult food", "puppy food", "kitten food", "grown up food",
                 "portion", "portions", "how much should i feed", "what should i feed",
                 "how much to feed", "should i feed",
                 # holding fish out of the angling row put the activity inside this one:
                 # "can i take my dog fishing" was the rod licence and became the dinner card.
                 # A dog on a riverbank is a licence question. The phrases, not the bare word:
                 # an avoid word is read in its loose forms, so "fishing" would also swallow
                 # "can my dog eat fish", which is a real dinner question.
                 "go fishing", "come fishing", "fishing trip", "fishing rod", "angling",
                 "rod licence", "rod license", "fishing with my dog", "fishing with my cat",
                 "take my dog fishing"),
          guard=lambda understood: not _one_pets_dinner(understood)),
    # Two pets and two bowls is its own question, and the can-I-eat row above answered it with
    # the foods-to-refuse list: "how do i stop my cat eating the dogs food" read as a poison
    # question, and "the dog eats the cats dinner" reached the dog-friendly-pubs card. What a
    # stolen dinner means is not a vet visit but a change to how the house feeds them.
    entry("one-pets-dinner", (("dog", "dogs", "dog's", "puppy", "cat", "cats", "cat's",
                               "kitten", "pet", "pets", "rabbit", "hamster",
                               # "they eat each others food" names no animal, and the guard
                               # below already insists on the other pet's dinner
                               "they", "them", "both"),
                              ("food", "dinner", "tea", "bowl", "bowls", "meal", "meals",
                               "kibble", "biscuits", "dish", "plate",
                               "everything") + _DINNER_TAKEN),
          ("Not a poison, so no vet for a stolen dinner: a dog living on cat food gets fat and "
           "its gut complains, and a cat living on dog food goes short of taurine, which it "
           "cannot make itself. Feed them at set times in separate rooms and lift both bowls "
           "after ten minutes, and put the cat's bowl up on a worktop or a shelf the dog cannot "
           "reach, or behind a microchip cat flap. Feed the cat first, because a cat chased off "
           "its food twice stops eating. And if either is on a prescription diet, the other must "
           "never share it."),
          guard=_one_pets_dinner, bias=3,
          # a food named in the line is the can-I-eat question, and a dog that will not eat is
          # ill rather than greedy
          avoid=("chocolate", "grapes", "raisins", "onion", "garlic", "xylitol",
                 "wont eat", "won't eat", "not eating", "off his food",
                 "off her food", "sick", "vomiting", "loose stools", "allergic",
                 "diarrhoea", "diarrhea", "the runs", "threw up", "poorly", "unwell",
                 "bad tummy", "upset stomach")),
    # "Can hamsters eat cheese", "can guinea pigs eat bananas" and "can budgies eat avocado" were
    # all "I'm not sure about that one", and the dog's refuse list is the wrong reply to any of
    # them: a bird's dangerous foods are not a hamster's, and avocado kills a bird. Keyed by the
    # animal, so the answer is about the animal the person named.
    entry("small-pet-food", (("hamster", "hamsters", "guinea pig", "guinea pigs", "guineapig",
                              "guineapigs", "budgie", "budgies", "budgerigar", "parakeet",
                              "cockatiel", "canary", "parrot", "parrots", "bird", "birds",
                              "gerbil", "gerbils", "chinchilla", "chinchillas",
                              "tortoise", "tortoises", "turtle", "turtles",
                              "horse", "horses", "pony", "ponies", "foal", "foals"),
                             ("can", "eat", "eats", "eating", "have", "give", "feed", "feeding",
                              "fed", "safe", "ok", "allowed", "poisonous", "toxic", "food",
                              "diet", "treat", "treats", "bad", "good", "drink")),
          lambda memory, understood: _small_pet_food(understood),
          ask=SMALL_PET_ASK, bias=2,
          # what it costs, how long it lives, why it is ill and what to call it are other rows
          # and other answers: this one is only about what goes in the bowl.
          avoid=("cost", "price", "how much is", "how much are", "how much does", "how much do",
                 "lifespan", "live for", "lives for", "how long do", "how long does", "hutch",
                 # A wild bird on a feeder is the garden's question, and "how do i stop
                 # squirrels eating the bird food" was answered with parrot pellets here.
                 "squirrel", "squirrels", "bird food", "bird feeder", "bird table", "feeder",
                 "fat balls", "fatballs", "peanuts for the birds", "wild bird", "wild birds",
                 "seed feeder", "niger seed", "sunflower hearts", "hedgehog", "fox", "foxes",
                 "badger", "badgers", "mouse", "mice", "rats", "rat",
                 "cage", "tank", "ill", "sick", "vet", "not eating", "stopped eating", "wont eat",
                 "won't eat", "off his food", "off her food", "name", "called", "bite", "biting",
                 "noise", "noisy", "shouting", "screaming", "escape", "escaped", "tame")),
    # A dog that eats in thirty seconds brings it back up again, and the fix is the bowl.
    # What a rabbit eats is asked in a hundred shapes and every one of them is a diet question:
    # hay is the answer, and the greens, the nuggets and the treats come after it.
    entry("rabbit-food", (("rabbit", "rabbits", "bunny", "bunnies"),
                          ("eat", "eats", "eating", "feed", "feeding", "food", "give", "diet",
                           "lettuce", "carrot", "carrots", "cabbage", "broccoli", "kale", "spinach",
                           "herbs", "apple", "fruit", "veg", "vegetables", "greens", "grass", "hay",
                           "grape", "grapes", "raisins",
                           "treat", "treats", "fresh", "safe", "ok", "allowed", "dandelion",
                           # a rabbit that is always hungry is a hay question and the hay card is
                           # this one, so the words people use for it reach the diet, not a punt
                           "hungry", "starving", "never full", "never seems full", "always eating",
                           "wants more")),
          "Hay is the diet: a pile the size of the rabbit every day, since it wears the teeth "
          "down and keeps the gut moving. Add a handful of leafy greens - lettuce, kale, spinach, "
          "herbs - and an eggcup of nuggets. Carrot, apple and grapes are treats, because the sugar "
          "loosens the droppings, so go easy on cabbage and iceberg lettuce too. Grass is fine "
          "unless it has been weedkilled. Change a food over a week, not in a day.",
          # a rabbit that has stopped eating is the vet's, and how long one lives or what it
          # costs are other rows
          ask=("rabbit", "rabbits", "bunny", "bunnies"),
          avoid=("not eating", "stopped eating", "wont eat", "won't eat", "refusing food",
                 "is off his food", "is off her food", "not pooing", "diarrhoea", "sick", "ill",
                 "vet", "dying", "died", "how long do", "lifespan", "live for", "cost", "price",
                 "how much is", "hutch", "cage", "recipe", "cook", "litter", "best rabbit")),
    entry("dog-eats-fast", (("dog", "dogs", "puppy", "pup"),
                            ("too fast", "eats fast", "eating fast", "eats too quick", "gulps",
                             "too quickly", "eats quickly", "eating quickly", "so quickly",
                             "in seconds", "in ten seconds", "in about ten seconds", "ten seconds flat",
                             "gulping", "gobbles", "bolts", "bolting", "wolfing", "scarfing",
                             "inhales", "vacuums", "in one go", "slow down")),
          ("Put the food in a slow feeder bowl or scatter it across a towel so he has to work for "
           "it, split the day's food into three or four small meals, and use bigger kibble if he "
           "is on dry food. A dog that gulps also swallows air: with a deep-chested breed, take "
           "him to the vet straight away if his belly is swollen and he is retching and can't "
           "settle, because that is bloat."), bias=1),

    # A dog that is always hungry is the commonest worry there is about a dog that is otherwise
    # well, and it had no answer of its own: "my dog is always hungry" was a punt and "my
    # labrador is always hungry" was the human hunger card with its stomach hormone, because
    # both rows key the word "hungry" and nothing stood the human one down for an animal.
    entry("dog-always-hungry",
          (("dog", "dogs", "puppy", "pup", "pups", "doggy", "labrador", "retriever",
            "terrier", "spaniel", "collie", "beagle", "poodle", "bulldog", "greyhound",
            "whippet", "pug", "boxer", "husky", "shepherd", "schnauzer", "cocker", "dachshund",
            "cavapoo", "cockapoo", "labradoodle", "goldendoodle", "jack russell", "staffie",
            "springer", "pointer", "setter", "chihuahua", "pomeranian", "shih tzu"),
           ("always hungry", "hungry all the time", "always starving", "starving",
            "never full", "never seems full", "always wants food", "always looking for food",
            "always after food", "constantly hungry", "greedy", "always eating",
            "wants more food", "hungry")),
          "Most dogs that seem permanently hungry are simply greedy, and it is no sign that "
          "anything is wrong: weigh the day's food on the kitchen scale against the amount on "
          "the bag for his weight, split it into two meals, and slow him down with a puzzle bowl "
          "or a scatter feed. Go to the vet if the weight is dropping, if he has started "
          "drinking a lot, or if the hunger came on with a change of food - worms, a gut problem "
          "and diabetes all look like this. Treats come out of the day's food rather than on top "
          "of it, which is the usual reason a dog on the right amount keeps gaining.",
          # a cat is a different animal with a different answer, and the dog rows that already
          # exist own their own lines: eating too fast, weight, and what to feed him
          ask=("dog", "dogs", "puppy", "pup", "pups", "doggy", "labrador"),
          avoid=("cat", "cats", "kitten", "kittens", "rabbit", "hamster", "guinea pig", "horse",
                 "eats fast", "eats too fast", "eating fast", "too fast", "gulps", "gobbles",
                 "bolts", "begging at the table", "steals food", "overweight", "too fat",
                 "losing weight", "lost weight", "put on weight", "how much should i feed",
                 "what should i feed", "dog food", "raw food", "vomiting", "sick", "diarrhoea",
                 "not eating", "stopped eating", "wont eat", "won't eat", "off his food",
                 # a dog that begs at the table has its own answer, and it was this row's line
                 # before the fence: "my dog begs for food all the time" is a training question
                 "beg", "begs", "begging", "scrounge", "scrounges", "scrounging", "at the table",
                 "from the table", "under the table"),
          bias=4),

    # The same worry about a cat, and a different answer: a cat fed little and often never looks
    # full, and a new appetite in an older cat is the one that needs the vet.
    entry("cat-always-hungry",
          (("cat", "cats", "kitten", "kittens", "moggy", "moggie", "persian", "maine coon",
            "siamese", "bengal", "ragdoll", "burmese", "sphynx", "tabby", "tomcat"),
           ("always hungry", "hungry all the time", "always starving", "starving",
            "never full", "never seems full", "always wants food", "always looking for food",
            "constantly hungry", "greedy", "wants more food", "hungry", "always crying for food",
            "always meowing")),
          "Most cats that nag for food are bored or used to being fed little and often, and it is "
          "fine to hold the line: weigh the day's food against the amount on the packet for her "
          "weight and give it in several small meals or a puzzle feeder rather than leaving a "
          "bowl down, because a cat that grazes all day never looks full. A cat that is hungry "
          "and losing weight needs the vet, since an overactive thyroid and diabetes both start "
          "exactly like that and both are treatable. A sudden new appetite in an older cat is "
          "worth a check before you feed more.",
          ask=("cat", "cats", "kitten", "kittens", "moggy", "moggie"),
          avoid=("dog", "dogs", "puppy", "rabbit", "hamster", "guinea pig", "horse",
                 "overweight", "too fat", "losing weight", "put on weight", "not eating",
                 "stopped eating", "wont eat", "won't eat", "off her food", "vomiting", "sick",
                 "diarrhoea", "how much should i feed", "what should i feed", "cat food",
                 "raw food", "steals food"),
          bias=4),

    # A horse is meant to be eating most of the day, so the honest answer is about hay and the
    # belly rather than about appetite: the danger is the sudden one, and the laminitis that
    # follows a rich field.
    entry("horse-always-hungry",
          (("horse", "horses", "pony", "ponies", "cob", "gelding", "mare", "foal", "shettie",
            "connemara", "thoroughbred", "warmblood", "arab"),
           ("always hungry", "hungry all the time", "always starving", "starving", "never full",
            "always wants food", "constantly hungry", "always eating", "greedy", "hungry",
            "never seems full")),
          "A horse is built to eat for sixteen hours a day, so a greedy one is usually normal: "
          "keep forage in front of him - hay in a small-holed net or a trickle feeder - and split "
          "the hard feed so the stomach is never empty. The appetite to worry about is the sudden "
          "one: ravenous with weight dropping is worms, ulcers or a tapeworm burden, and a horse "
          "that is hungry and off his hay needs the vet. Keep a fat pony off rich spring grass, "
          "because laminitis is what the greedy ones get.",
          ask=("horse", "horses", "pony", "ponies", "cob", "gelding", "mare", "foal"),
          # a horse that is merely fat, off its hay or colicking is another row; the weight
          # coming off with the appetite is this one, and it says so
          avoid=("dog", "cat", "rabbit", "hamster", "guinea pig", "laminitis", "too fat",
                 "overweight", "not eating", "stopped eating", "wont eat", "won't eat",
                 "colic", "sick", "hay", "feed", "rug"),
          bias=4),

    # A guinea pig is a hay animal too, and "my guinea pig is always hungry" had no answer at
    # all: the small-pet food row answers "can my guinea pig eat X" and this is the other half.
    entry("guinea-pig-always-hungry",
          (("guinea pig", "guinea pigs", "guineapig", "guineapigs", "cavy", "cavies"),
           ("always hungry", "hungry all the time", "always starving", "starving", "never full",
            "never seems full", "always wants food", "constantly hungry", "greedy", "hungry",
            "always eating", "squeaking for food")),
          "Guinea pigs graze all day, so a hungry one is doing what it is built for: keep hay in "
          "the rack so there is always some, and add a mug of leafy greens and a quarter of a "
          "pepper a day for the vitamin C they cannot make themselves. Nuggets are a small "
          "measured handful, not a bowl to top up. If the appetite is new and the weight is "
          "going down, or the teeth look long, that is the vet, because guinea pigs hide illness "
          "until they are quite unwell.",
          avoid=("can", "eat", "poisonous", "toxic", "safe", "cost", "price", "lifespan",
                 "not eating", "stopped eating", "wont eat", "won't eat", "ill", "sick", "vet",
                 "died", "dying", "hutch", "cage"),
          bias=4),

    # "what should i name my cat" shrugged and "suggest a name for my new kitten" got the kitten
    # kit: a naming question wants a rule for choosing, not a shopping list. The animal is in the
    # key, and an animal that already has a name of its own ("does my cat know his name") is a
    # different question, so those shapes are kept out.
    entry("pet-name", (("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "pup", "pups",
                        "hamster", "rabbit", "bunny", "guinea pig", "parrot", "budgie", "fish",
                        "horse", "pony", "tortoise", "pet", "pets"),
                       ("name", "named", "naming", "call it", "call him", "call her", "call them",
                        "call")),
          ("Two syllables with a hard sound in it is the rule - Biscuit, Otis, Poppy, Rufus - "
           "because a name you can shout across a park has to carry, and a long soft one gets "
           "shortened whether you like it or not. Say it out loud with 'come' and with 'no' "
           "before you commit: nothing that sounds like either, and nothing that a person or "
           "another animal in the house already answers to. A cat can be sillier - they learn "
           "the tone rather than the word, so a daft name does no harm - but a dog will hear it "
           "a few thousand times."),
          # the question has to be asking for a suggestion: "what is my dog called" and
          # "whats my cats name" are the memory store's, and it answers them right
          ask=("should i name", "should we name", "should i call", "should we call",
               "what should i name", "what should i call", "what to name", "what could i name",
               "suggest", "ideas", "idea", "any name", "good name", "nice name", "name for my",
               "name my", "help me name", "help me pick", "recommend", "come up with",
               "think of a name", "how do i name", "rename", "what would you call",
               # "any good cat names" and "name ideas for a cat" ask the same thing without a
               # question word; the pet word in the key keeps them off anything else
               "any good", "names", "name ideas"),
          # a pet that already has a name, a name that is a fact about the pet, and the other
          # things in the house that get named are all somebody else's question
          avoid=("know", "knows", "recognise", "recognize", "respond", "responds", "come when",
                 # "whats my dogs name" is the memory store's: it answers "you haven't told me
                 # about a pet yet", which is the truth, and a naming lecture is not
                 "whats my", "what is my", "what are my", "do i call my", "did i name",
                 "when i call", "i named", "we named", "named her", "named him",
                 "named it", "named after", "change", "changed", "rename", "recall", "come back", "come here",
                 # teaching a pet the name it already has is training, not a suggestion:
                 # "can i teach my dog his name" is about recall
                 "teach", "teaches", "teaching", "taught", "learn", "learns", "learning",
                 "train", "trains", "training", "trained", "his name", "her name", "their name",
                 # a group of animals has a collective noun, which is a different question
                 "group of", "called?", "collective", "term for", "word for",
                 "wifi", "network",
                 "band", "boat", "starter", "sourdough", "podcast", "business", "company",
                 "baby", "child", "children", "son", "daughter", "plant"), bias=1),
    # Nothing in the knowledge base said how long an animal lives, so the first thing anyone
    # asks about a pet - "how long do dogs live" - got a shrug from every domain. One table,
    # keyed by the animal and the live-for shape, so the same fact answers "dog lifespan",
    # "how many years does a cat live" and "how long does a rabbit live for".
    *_lifespan_entries(),
    entry("dog-ageing-worry", ("dog", ("getting old", "growing old", "old age", "ageing",
                                      "aging", "dementia", "quality of life", "end of life",
                                      "euthanasia", "not himself",
                                      "slowing down", "nearing the end")),
          "It's a hard thing to watch, and being scared for him is part of loving an old dog. What "
          "helps most is a vet check now and every six months: pain relief for stiff joints, a "
          "senior food, and a plan for the bad days. A dog still eating, asking for you and "
          "getting up for a sniff is usually doing all right; write down the good days and the bad "
          "ones, because that list is the honest answer.", bias=2),
    entry("dog-crate", (("dog", "puppy", "pup"),
                        ("crate", "crating", "cage", "den", "crate train", "crate training")),
          "A crate is a good den if it's introduced slowly: leave the door open, feed meals inside, "
          "and shut it for seconds at a time while you're in the room. Get one big enough to stand "
          "up and turn round in, never use it for long stretches, and never as a punishment."),
    entry("dog-dig", ("dog", ("dig", "digs", "digging", "dug", "holes", "garden", "lawn")),
          "Dogs dig out of boredom, heat or the smell of something buried, so give it a spot of its "
          "own — a sandpit with toys buried in it — and reward digging there. Cover the rest with "
          "stones or a mesh, keep it exercised and never shout when it's already dug.",
          # "cat or dog for a flat with no garden" names the garden, but it is a choice between
          # pets: the dog has to be digging for this to be the answer
          ask=("dig", "digs", "digging", "dug", "holes", "lawn", "flowerbed", "border")),
    entry("dog-early-waking", (("dog", "dogs", "bitch", "lab", "terrier", "collie", "spaniel",
                                "retriever", "shepherd", "husky", "poodle", "beagle", "boxer"),
                               ("wakes me", "wake me", "waking me", "wakes up early", "too early",
                                "5am", "5 am", "4am", "4 am", "6am", "6 am", "early morning",
                                "first light", "before dawn", "crack of dawn")),
          ("An early-rising adult dog is usually on a habit, not a need: push his last walk and "
           "last meal an hour later, then leave him and keep the greeting flat until the alarm "
           "goes, because getting up to let him out teaches him that 5am works. Blackout curtains "
           "help in summer, and if the waking is new, a dog that suddenly cannot last the night "
           "should see the vet."),
          # an adult dog line matches puppy-night too (both key on "wakes me up"), and the habit
          # answer is the right one, so this wins the tie
          bias=3,
          ask=("wake", "wakes", "waking", "early", "5am", "5 am", "4am", "4 am", "6am", "6 am",
               "dawn"),
          # a puppy that cannot last the night needs the puppy answer
          avoid=("puppy", "puppies", "pup", "weeks old", "months old", "crate", "new puppy")),
    entry("dog-ears", ("dog", ("ear", "ears", "head shaking", "shakes his head",
                               "shaking his head", "scratching his ear", "smelly ears")),
          "Head shaking, scratching at an ear or a smell usually means an ear infection, which "
          "needs the vet rather than cotton buds, because the treatment differs for yeast, bacteria "
          "and ear mites. Keep ears dry after walks and swimming, and only use an ear cleaner the "
          "vet has approved."),
    entry("dog-eats-poo", (("poo", "poop", "poos", "faeces", "feces"), ("eat", "eats", "eating")),
          "It's grim but very common and usually harmless: pick up straight away, keep the garden "
          "clear, and teach \"leave it\" with a treat that beats the prize. Ask the vet if it "
          "started suddenly, because sometimes it follows a diet that isn't satisfying him.",
          # the generic picking-things-up entry names "dog" and "eating" too, so eating poo ties
          # with it and the rarity of the words decides; naming poo is the more specific answer
          bias=1),
    entry("dog-hair-loss", ("dog", ("bald", "bald patch", "hair loss", "losing hair", "patchy",
                                     "patches", "thin coat")),
          ("A bald patch is usually fleas, a skin infection or an allergy, and sometimes a spot "
           "rubbed raw by licking or a harness. Have the vet look if it is spreading, scabby, "
           "itchy or the dog is unwell; flea treatment for every pet in the house and a hot wash "
           "of the bedding sorts the commonest cause."),
          ask=("bald", "patch", "patches", "hair", "coat", "skin", "scabby", "itchy")),
    entry("dog-harness", ("dog", ("harness", "harnesses", "collar", "collars")),
          "A harness is kinder for a dog that pulls, because it takes the strain off the throat, and "
          "it's the safer choice for flat-faced breeds. Use a Y-shaped one that doesn't cross the "
          "shoulders, keep a collar on for the tag, and get the fit checked — two fingers should "
          "slip under the straps."),
    entry("dog-mouthing", (("puppy", "dog"), ("biting", "bites", "mouthing", "nipping", "nips",
                                              "hands", "fingers")),
          ("Yelp or say \"ow\" and stop the game the moment teeth touch skin, then turn away for "
           "ten seconds before playing again; the puppy learns that teeth end the fun. Give a chew "
           "toy instead every time he goes for hands, and if he is over-tired, a nap settles more "
           "of it than any training."),
          # "a bit" lemmatises to "bit", which is also how the matcher reads "biting", so a dog
          # described as "a bit overweight" landed here instead of on the weight entry.
          avoid=("overweight", "fat", "weight", "diet", "slim", "obese", "thin",
                 # furniture is the chewing entry's line, even when the verb is "bites"
                 "furniture", "sofa", "chair", "chairs", "table", "table leg", "leg of",
                 "shoes", "slippers", "socks", "carpet", "curtains", "everything",
                 # a dog the person does not own is not theirs to train, and "my neighbours dog
                 # bites people" was getting the puppy-mouthing answer: yelp and turn away is
                 # useless advice for someone else's dog
                 "my neighbour", "my neighbors dog", "my neighbours dog", "the neighbours dog",
                 "next door", "their dog", "someone elses dog", "someone else's dog",
                 "somebody elses dog",
                 # a tongue is not teeth: "why does my dog lick my hands" was this answer,
                 # which is about a puppy learning that teeth end the game
                 "lick", "licks", "licking", "licked",
                 # a bite that has already happened is a wound question - wash it, watch it,
                 # get a hand bite seen - and the mouthing answer is advice for a habit. The
                 # wound rows (animal-scratch, dog-bite-person) have this line and used to lose
                 # it to nothing; they must not lose it to this one.
                 "bled", "bleeding", "blood", "broke the skin", "broken the skin", "puncture",
                 "plaster", "tetanus", "infected", "infection", "swollen", "went red",
                 "bit my", "bit me", "bit the", "bitten", "yesterday"),
          # the teeth have to be on a person: "my puppy bites a lot" is chewing, so the line has
          # to name hands, fingers or an arm for this answer to be the right one
          ask=("hands", "hand", "fingers", "finger", "arms", "arm", "mouths", "mouthing",
               "nips", "nipping", "me", "us", "the kids", "kids", "kid", "child", "children",
               "toddler",
               # "how do i stop my puppy biting" and "train a puppy not to bite" name nobody,
               # but the ask is the same: the teeth on skin are the problem, not the furniture.
               "not to bite", "stop biting", "stop the biting", "stop him biting",
               "biting people", "bite people", "biting us", "biting me", "biting hands",
               # "how do i stop my puppy biting" names no hands and no me, so the words people
               # say it with are here as phrases. "my puppy bites a lot" is deliberately not one
               # of them: that line is the chewing row's (test_pets_common asserts it), and a
               # phrase of "puppy" + "biting" would take it, because the stems meet.
               "stop my puppy biting", "stop puppy biting",
               # and the article people write: "how do i stop a puppy biting" named no hand and
               # no "me", so the wound row answered it with wash it under the tap. A phrase with
               # the animal in it, so "my puppy bites a lot" stays the chewing row's.
               "stop a puppy biting", "stop a dog biting", "stop the puppy biting",
               "stop the dog biting", "stop a puppy from biting", "stop a dog from biting",
               "puppy biting me"),
          # A habit row has to beat the wound row when the line describes the habit and names a
          # hand, and the wound row is bias 4: "my puppy keeps biting me" and "my puppy bites my
          # hands" were both told to wash it under running water and check their tetanus. The
          # avoid list above hands the real bites back, so the bias only settles the habit.
          # teeth on a hand is mouthing even though "bites" is in the chewing key too
          bias=2),
    # The same pick asked about a cat, and asked as "is a rescue cat a good idea": both were
    # reaching the introducing-a-second-cat paragraph, which tells you to let the two of them
    # smell each other through a door that does not exist yet, or nothing at all.
    entry("rescue-or-baby", (("rescue dog", "rescue cat", "rescue kitten", "rescue puppy",
                              "rescue", "older dog", "older cat", "older pet", "shelter dog",
                              "shelter cat", "a rescue"),
                             ("first dog", "first cat", "first kitten", "first pet", "which",
                              "better", "should i get", "should we get", "should i adopt",
                              "choose", "or a puppy", "or a kitten", "or a cat", "or a dog",
                              "or a rescue", "or an older", "or adult",
                              # "is a rescue dog a good idea" is the adoption card's line - the
                              # three questions, the £1,500 and the landlord - so "good idea" is
                              # not a choosing word here. The cat side of it has no other answer,
                              # and keeps one in the row below.
                              # "rescue dog or puppy" on its own is the one-line pick that
                              # already answers it ("Rescue dog. I'd take that and not think
                              # about it again."); this card is for the line that asks a
                              # question, so bare "or puppy" and its kind are not here.
                              )),
          _rescue_or_baby,
          # "rescue" is a word other things use about themselves: a rescue inhaler, a rescue
          # remedy, a mountain rescue. None of them is a choice between two animals.
          avoid=("inhaler", "inhalers", "remedy", "drops", "mountain", "mountain rescue",
                 "drama", "mission", "at sea", "operation", "pet food", "insurance")),
    # The other side of the same coin: "is a rescue cat a good idea" asks for a verdict and names
    # no second animal, which is not a pick between two and not a dog question either. Its words
    # are the cat phrased with "rescue", so the dog's idea question keeps the adoption card.
    entry("rescue-cat-good-idea", (("rescue cat", "rescue kitten", "shelter cat", "older cat",
                                    "adult cat", "a rescue cat", "rescue cats"),
                                   ("good idea", "worth getting", "worth it", "wise", "sensible",
                                    "good choice", "should i", "would you")),
          "Usually yes, and more so as a first cat. An adult rescue comes with a known character, "
          "is past the kitten climbing and biting, and settles in a week or two; a kitten is "
          "months of work but you shape it from the start. Ask the rescue what it is like with "
          "other cats, children and the litter tray, and take the one that comes to you.",
          # a treatment, a remedy and a mountain are the other rescuers in this file
          avoid=("inhaler", "inhalers", "remedy", "drops", "mountain", "mission", "at sea",
                 "operation", "pet food", "insurance")),
    entry("dog-paw-licking", (("dog", "dogs", "puppy", "puppies", "pup",
                               # a cat licking at one paw is the same question asked about a cat:
                               # the causes differ, so the reply reads the animal off the line
                               "cat", "cats", "kitten", "kittens"),
                              # "chewing" and "biting at" were in this list and are not the same
                              # question: "my dog keeps chewing the door" is the chewing answer's
                              ("licking", "lick", "licks", "licked", "paws", "paw", "feet",
                               # the animal's own paws said as teeth on them: the chewing and
                               # teething rows carry the same bare words, and a longer phrase
                               # settles it here - "my dog is chewing his paws" is the itch
                               "chewing his paws", "chewing her paws", "chewing its paws",
                               "chewing his paw", "chewing her paw", "chews his paws",
                               "chews her paws", "chews his feet", "chews her feet",
                               "chewing his feet", "chewing her feet", "chewing his pads",
                               "chewing her pads", "biting his paws", "biting her paws",
                               "biting at his paws", "biting at her paws", "bites his paws",
                               "bites her paws", "nibbling his paws", "nibbling her paws",
                               # the whole dog rather than one paw: "my dog is scratching and
                               # biting himself" is the same itchy-skin question, and the habit row
                               # would otherwise answer it with a training plan
                               "scratching and biting", "biting and scratching",
                               "scratching himself", "scratching herself",
                               "scratches himself", "scratches herself",
                               "itching himself", "itching herself")),
          _paw_licking,
          # an injured paw is the lameness answer: a cut, a thorn or a broken claw is not itchy skin
          avoid=("hurt", "hurts", "hurting", "cut", "cuts", "sore", "swollen", "swelling",
                 "bleeding", "bled", "limp", "limping", "limps", "lame", "thorn", "grass seed",
                 "won't put weight", "wont put weight", "not putting weight", "broken claw",
                 "yesterday", "suddenly",
                 # teeth on the person's own feet or hands is mouthing, and teeth on the furniture
                 # or a lead is chewing: only the animal's own paws are the itch answer
                 "my feet", "my foot", "my toes", "my ankles", "my hands", "my fingers",
                 "my arms", "my legs", "my hand", "the furniture", "the table leg", "shoes",
                 "slippers", "the lead", "the leash", "the blanket", "the cushion",
                 # a paw that is muddy or dirty and being washed is the cleaning question, and
                 # "clean my dogs paws" reached this row after the paw words came in above
                 "clean his paws", "clean her paws", "clean my dogs paws", "clean my dog's paws",
                 "clean the paws", "clean paws", "cleaning paws", "wash his paws",
                 "wash her paws", "wash my dogs paws", "wash my dog's paws", "wipe his paws",
                 "wipe her paws", "wipe the paws", "muddy paws", "muddy feet", "dirty paws",
                 "paws after a walk", "washing paws",
                 # the garden and the furniture: a cat that licks the carpet or works at the
                 # sofa is not a paw question, and licking a cable or wool is pica's own line
                 "garden", "repellent", "keep them off the", "plastic", "bag", "bags", "wool",
                 "string", "cable", "cables", "wire", "wires", "fabric", "curtain", "curtains",
                 "nappy", "nappies",
                 # a cat that licked a plant may have been poisoned, and the plant rows are the
                 # ones that save it: the verb "licked" was reading as grooming (pink-nail)
                 "toxic", "poison", "poisoned", "poisonous", "plant", "plants", "houseplant",
                 "houseplants", "lily", "lilies", "ivy", "poinsettia", "daffodil", "flower"),
          # "how do i stop my cat licking her paw" is level with the cat-repellent garden answer
          # on the two key parts both of them reach and lost the tie on registry order
          bias=1),
    entry("dog-pulling-dog", (("dog", "puppy"),
                              ("pull", "pulls", "pulling", "lead", "leash", "collar", "slips",
                               "slipping", "escapes", "tight", "pinches", "rubbing", "chafes")),
          _dog_pulling),
    entry("dog-scared-dogs", (("dog", "puppy"),
                              ("other dogs", "other dog", "other animals", "strange dogs",
                               "barking at dogs", "scared of dogs", "afraid of dogs")),
          ("Start further away than you think you need to: a distance where he can see a dog and "
           "still take a treat, then let the other dog pass and walk on. Repeat that a few times a "
           "week, never let dogs rush up nose to nose on the lead, and stay calm yourself because "
           "the lead tightens when you brace and that tells him there is something to fear."),
          # "my dog seems a bit down since we lost our other dog" is grief, not a dog in the park
          avoid=("lost our other", "our other dog", "since we lost", "died", "death", "passed away",
                 "put down", "put to sleep", "grieving", "grief", "bereave", "seems down",
                 "a bit down", "not himself", "off his food", "stopped eating"),
          bias=1),
    # "my dog ate a slug" is not a scavenging question: the answer is lungworm, a sting or a
    # toad's skin, and "teach leave it" teaches nothing about what has already gone down. The
    # creature has to be named as well as the animal and the eating, so "my dog eats rubbish"
    # and "my dog has worms" keep their own answers.
    entry("dog-ate-a-creature",
          (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets"),
           ("ate", "eaten", "eat", "eats", "eating", "swallowed", "swallow", "licked",
            "licking", "chewed", "chewing", "got"),
           ("slug", "slugs", "snail", "snails", "bee", "bees", "wasp", "wasps", "hornet",
            "hornets", "frog", "frogs", "toad", "toads", "beetle", "beetles", "spider",
            "spiders", "caterpillar", "caterpillars", "woodlouse", "woodlice", "worm", "worms",
            "moth", "moths", "insect", "insects", "bumblebee", "daddy long legs")),
          ("Slugs and snails are the ones that matter: they carry lungworm, so tell your vet he "
           "has eaten one and get him a lungworm worming - a monthly spot-on is what vets use "
           "for a dog that keeps picking them up. If there are slug pellets in the garden, ring "
           "the vet now and say how many, because those poison him. A bee or wasp sting in the "
           "mouth is sore for a day: ring the vet if his face swells, he drools or his "
           "breathing gets noisy. A toad leaves an irritant on the skin, so rinse his mouth out "
           "with water, let him have a drink of clean water after and expect drooling for an "
           "hour. A beetle, a spider or a woodlouse is usually nothing at all."),
          guard=_an_eaten_creature),
    # The other half of that card, and the one that needs the vet rather than the garden: some
    # garden mushrooms are poisonous to a dog and a few kill, they come up in the same lawn the
    # dog is walked on, and waiting to see how he goes is the mistake the advice is against. The
    # sample is what lets the vet identify it, so that comes with the phone call.
    entry("dog-ate-a-mushroom",
          (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets"),
           ("ate", "eaten", "eat", "eats", "eating", "swallowed", "swallow", "licked",
            "licking", "chewed", "chewing", "nibbled", "nibbling", "got"),
           ("mushroom", "mushrooms", "toadstool", "toadstools", "fungus", "fungi",
            "shroom", "shrooms")),
          ("Ring the vet now, before any symptoms: some garden mushrooms are poisonous to dogs "
           "and cats, a few of them deadly, and the dangerous ones look much like the harmless "
           "ones. Take a photo of where it was growing and whatever is left of it in a paper bag "
           "or a bit of damp kitchen roll, so the vet can identify it, and do not make him sick "
           "yourself. If he is already drooling, being sick, shaky or wobbly, say that on the "
           "phone, because it makes it urgent."),
          # the cat and the dog both eat what they find, so both are in the key; a person's own
          # mushroom is a cooking question and has no animal in it
          avoid=("recipe", "cook", "cooking", "fry", "fried", "risotto", "soup", "pasta",
                 "picking mushrooms", "pick mushrooms", "forage", "foraging", "baby",
                 "toddler", "my son", "my daughter"),
          guard=_an_eaten_fungus),
    entry("dog-scavenging", (("dog", "puppy"),
                             ("eat", "eating", "eats", "ate", "picks up", "picking up", "street",
                              "pavement", "rubbish", "junk", "litter", "scavenge",
                              "scavenges", "scavenging", "bins")),
          ("Teach \"leave it\" with a treat in each hand: say it, show the treat, and reward him the "
           "second he looks away, then practise on walks with a boring bit of food before you try it "
           "on a chip. Keep him on a short lead past takeaways and bins and feed him before walks so "
           "he isn't hungry; if he swallows things that could block him, muzzle training is worth the "
           "time, because a sock or a kebab stick means surgery."),
          # eating poo is dog-eats-poo, so "poo" is deliberately not here. "Can dogs eat cheese"
          # names "eat" and "dog" but it is a food-safety question, and "leave it" training is
          # not the answer: those go to dog-human-food.
          ask=("eat", "eating", "eats", "ate", "picks up", "picking up", "street", "pavement",
               "rubbish", "junk", "litter", "scavenge", "scavenging", "bins", "garbage"),
          # a dog that turns his dinner down is not a dog that picks things up: the refusal words
          # belong to dog-not-eating, even though "eat" is in both keys
          avoid=("not eating", "not eaten", "off his food", "off her food", "refusing food",
                 "stopped eating", "leaves his food", "leaves her food", "skips a meal",
                 "eats much", "eating much", "not hungry",
                 # bolting his dinner at the bowl is the slow-feeder answer, not the pavement
                 "bowl", "dinner", "in seconds", "ten seconds", "too fast", "eats fast",
                 "too quickly", "so quickly", "really quickly", "gulps", "gulp", "slow feeder",
                 "slowly",
                 "can dogs eat", "can my dog eat", "can a dog eat", "can i give", "is it safe",
                 # what has already gone down is the vet's, not a training tip: a mushroom off
                 # the lawn is `dog-ate-a-mushroom`, which is a phone call rather than a lead
                 "mushroom", "mushrooms", "toadstool", "toadstools", "fungus", "fungi",
                 "safe for dogs", "safe to give", "cheese", "milk", "dairy", "grapes", "grape",
                 "raisins", "raisin", "onion", "onions", "garlic", "chocolate", "xylitol",
                 "sugar free", "sugar-free", "macadamia", "avocado", "lilies", "alcohol",
                 "poison", "poisonous", "toxic", "feed", "foods", "diet",
                 # things that can block or poison: these are the swallowed entry, not training
                 "medication", "medicine", "medicines", "tablets", "tablet", "pills", "pill",
                 "drugs", "drug", "battery", "batteries", "coin", "coins", "plastic", "wrapper",
                 "string", "tights", "corn cob", "corncob", "needle", "nappy", "nappy sack"),
          ),
    entry("dog-senior", ("dog", ("old dog", "older dog", "senior", "aging", "ageing", "arthritic",
                                 "arthritis", "stiff")),
          "For an older dog: a warm, soft bed away from draughts, a ramp or a low step for the "
          "sofa, shorter and more frequent walks, and a vet check twice a year. Keep its claws "
          "short, which is easy to forget when it walks less, and ask the vet about pain relief if "
          "it's slow to get up.",
          avoid=("eat", "eating", "food", "places", "pub", "restaurant", "town",
                 # An age written in weeks or months is a young dog, and `dog-senior` keys the
                 # phrase "old dog": "my 6 month old dog chews everything" carries it whole
                 # ("month |old dog| chews") and was told to put a ramp by the sofa. A dog is not
                 # senior at 6 months, so the age markers stand this row down and the puppy and
                 # chewing rows below take the line.
                 "week old", "weeks old", "month old", "months old",
                 # "how do i introduce a new puppy to my older dog" is an introduction, and a
                 # grumpy pair is the same question asked as a complaint
                 "introduce", "introducing", "introduction", "new puppy", "new dog", "another dog",
                 "second dog", "meet", "meeting", "puppy", "pup", "grumpy", "snappy",
                 "growls at", "growling", "snaps at", "hates the puppy"),
          # the phrase "old dog" sits inside "month old dog" and "year old dog", so the stated age
          # decides: a six month old dog that chews everything is the chewing row's, not this one
          guard=_dog_not_young),
    entry("dog-should-we",
          (("should we get a", "should i get a", "should we have a", "thinking about getting a",
            "thinking of getting a", "is it fair to", "can we get a", "can i get a", "good idea",
            "right time", "good time", "ready for a",
            # "can we still get a dog" is the same question with the store's own "still" in it,
            # and it was the one shape of it that reached nothing at all
            "can we still get a", "can we still have a", "can i still get a",
            "can i still have a"),
           ("dog", "dogs", "puppy", "puppies", "pup")),
          "Ask three questions and answer them honestly: who walks it twice a day in the rain, who "
          "pays, and where it goes when you are away. A puppy is about \u00a31,500 to \u00a32,000 in the first "
          "year and around \u00a31,000 a year after that, with 30 to 60 minutes of walking a day, "
          "training classes, insurance and a vet, and it cannot be left more than a few hours for "
          "the first months. If you rent, get the landlord's yes in writing first. If all three "
          "answers are real, it is a good idea; if one of them is a hope, wait.",
          # a second dog, and a pup that is already home, are other questions
          # the getting has to be in the line: "is it fair to leave a dog alone for eight hours" is
          # the dog-alone answer, however much it reads like deciding
          ask=("get a", "getting a", "getting", "should we", "should i", "thinking about",
               "thinking of", "ready for", "go for a", "good idea", "right time", "worth it",
               "worth getting"),
          avoid=("second", "another dog", "another puppy", "already got", "we have",
                 "i have a", "had a dog", "puppy comes home",
                 # a cat or a dog is a choice between two, not this; and a walk, a heatwave and a
                 # baby are their own questions however good an idea they are
                 "cat", "cats", "walk", "walking", "heat", "hot", "cold", "park", "baby")),
    entry("dog-swallowed", ("dog", ("swallowed", "sock", "toy", "bone", "stick", "object",
                                    "foreign", "medication", "medicine", "medicines", "tablets",
                                    "tablet", "pills", "pill", "drugs", "drug", "battery",
                                    "batteries", "coin", "coins", "corn cob", "corncob", "needle",
                                    "nappy")),
          "Ring the vet now for pills, medicine, a battery or a coin, and for anything sharp, a "
          "sock or a toy: batteries burn through in hours and some pills are dangerous in one "
          "tablet. Don't pull a stick or bone out yourself and don't make him sick unless the vet "
          "says so. Signs that it's stuck are retching, drooling, a hard swollen belly, or trying "
          "to be sick with nothing coming up — that last one is an emergency."),
    # Getting a tablet into a dog or a cat was answered by three cards about people: "how do i
    # give my cat a pill" and "how do i get my dog to take his medicine" got the GP repeat
    # prescription, "my dog wont take his tablets" the child's screen-time rule ("tablet" read as
    # the device), and "my cat is hard to pill" the instructions for a person to swallow one. The
    # animal, the medicine and the act of getting it in are all named, so the row keys on the
    # three: a pet that has *eaten* the packet is a poisoning and stays with the poisoning card.
    entry("pet-medicine",
          (("dog", "dogs", "puppy", "puppies", "pup", "doggy", "cat", "cats", "kitten",
            "kittens", "puss", "rabbit", "rabbits", "bunny", "hamster", "guinea pig",
            "terrier", "spaniel", "collie", "labrador", "retriever", "whippet", "beagle"),
           ("pill", "pills", "tablet", "tablets", "medicine", "medication", "capsule",
            "capsules", "worming tablet", "worming", "wormer", "drops", "eye drops",
            "ear drops", "antibiotics"),
           ("give", "giving", "get him", "get her", "get my", "get it down", "take his",
            "take her", "takes his", "takes her", "wont take", "won't take", "will not take",
            "refuses", "spits", "spat", "hard to pill", "pill him", "pill her", "hide",
            "hiding", "sneak", "mixed in", "in his food", "in her food")),
          "Into the back of the mouth rather than the food if he spits it out: hold the head gently "
          "up, drop the tablet past the hump of the tongue, close the mouth and rub the throat or "
          "blow on his nose until he swallows, then give water or a treat so it doesn't stick. Pate, "
          "cheese or a pill pocket hides most of them, and ask the vet for a liquid or a spot-on if "
          "a cat fights the tablets. Squirt a liquid into the cheek pouch a little at a time, never "
          "straight down the throat, and never crush or open a capsule unless the vet says so.",
          # a pet that has eaten the pills, or eaten its own medicine, is a poisoning, not a how-to
          # "It will not take it" and "it has already swallowed it" are opposite questions, and the
          # second one is the urgent half: "my dog ate some of my tablets" was told how to get a
          # tablet in, so every way of saying the packet has gone down stands this row down.
          avoid=("swallowed", "swallow it", "ate", "eaten", "eats", "got hold of", "got into",
                 "chewed", "already had", "already taken", "overdose", "how many", "dose",
                 "dosage", "side effect", "reaction", "poison", "is it safe", "was sick", "vomited"),
          guard=_a_medicine_line,
          bias=3),
    # Taking a bone or a bowl away and getting a growl was "Ring the vet now for pills, medicine, a
    # battery or a coin", the daily food amount, and the puppy-teething card: the object noun and
    # the animal were the whole key. Guarding is a behaviour question with its own answer, so it
    # keys on the animal, the warning noise and the thing guarded. A bite that broke the skin keeps
    # the bite-wound card, which is where the person's own hand belongs.
    entry("dog-guarding",
          (("dog", "dogs", "puppy", "puppies", "pup", "doggy"),
           ("growl", "growls", "growling", "growled", "snap", "snaps", "snapped", "snapping",
            "snarl", "snarls", "snarled", "bares his teeth", "baring his teeth",
            "guards", "guarding", "guard", "possessive", "protective of"),
           ("his", "her", "their", "bone", "food", "bowl", "dinner", "toy", "chew", "treat",
            "bed", "rawhide", "kong", "pig ear", "slipper", "ball", "stick", "chew toy")),
          "Guarding food or a bone is ordinary dog behaviour that gets worse when it is punished, so "
          "stop taking things off him and teach a trade instead: hold a better treat out to one "
          "side, say \"drop\" as he leaves it, give the bone back, and hands coming near start to "
          "mean something good. Feed him where nobody walks past and leave him alone with a bone. If "
          "he has actually snapped at a child, ask the vet for a referral to a behaviourist rather "
          "than a trainer's quick fix.",
          avoid=("other dogs", "another dog", "at other dogs", "on the lead", "stranger",
                 "strangers", "visitors", "the postman", "barks at", "play biting", "playful",
                 "teething", "puppy teeth", "my hands", "my fingers", "garden", "doorbell",
                 # a dog growling while it is brushed, clipped or harnessed is being handled,
                 # not guarding: that question has its own card, and this one answered it with
                 # "stop taking things off him and teach a trade", which is about a bone.
                 "brush", "brushing", "brushed", "groom", "grooming", "groomed", "groomer",
                 "nail", "nails", "claw", "claws", "clip", "clipping", "clippers",
                 "paw", "paws", "harness", "collar", "bath", "bathe", "bathing", "towel",
                 "lift", "pick him up", "pick her up", "lead on"),
          guard=_a_guarding_line,
          bias=3),
    # A dog that growls, snarls or shows his teeth at a person is giving a warning, and main had no
    # answer for the plainest shape of it: "my dog growls at me" was only noted back, "my dog
    # growls when i pick him up" was a shrug, "my dog snarled at my son" was "Noted:" and "my dog
    # bared his teeth at me" was the tooth-brushing card, because "teeth" was the only word in the
    # line the knowledge base knew. The guarding row is the other question and needs the thing that
    # is kept, so the warning on its own belongs here.
    entry("dog-warning", (("dog", "dogs", "puppy", "puppies", "pup", "doggy"),
                          ("growl", "growls", "growling", "growled",
                           "snarl", "snarls", "snarling", "snarled",
                           "bares his teeth", "bared his teeth", "bares her teeth",
                           "bared her teeth", "baring his teeth", "baring her teeth",
                           "shows his teeth", "showed his teeth", "shows her teeth",
                           "showed her teeth", "lunge at me", "lunges at me", "lunged at me"),
                          # the person it is aimed at, or the handling that set it off: this is
                          # what tells the warning apart from the guarding row, which counts the
                          # same words plus the thing that is kept
                          ("at me", "at us", "at him", "at her", "at my", "when i",
                           "stroke", "strokes", "stroking", "touch", "touches", "touching",
                           "pick", "picks", "picked", "lift", "lifts", "lifted", "lifting",
                           "handle", "handled", "handling", "near",
                           # the place he was touched: "growls when i touch his back" reached
                           # nothing, because "back" is a body word and the row named no part,
                           # and "his ear" and "his leg" fell to the guarding row
                           "back", "leg", "legs", "ear", "ears", "paw", "paws", "head", "tail",
                           "neck", "shoulder", "shoulders", "belly", "tummy", "foot", "feet",
                           "hand", "hands", "arm", "collar", "harness",
                           "husband", "wife", "partner", "son", "daughter", "child", "kids",
                           "toddler", "baby", "warning")),
          ("A growl is a warning rather than a fault, so the first thing is to stop what you were "
           "doing, step back and let him come to you - and never tell a dog off for growling, "
           "because a dog punished for the warning learns to skip it and go straight to the snap. "
           "Then find out what it is about: being picked up or handled, a hand near his food, bed "
           "or a stolen sock, or pain. A dog who growls when he is lifted or touched in one place "
           "needs a vet first, since a bad tooth, an ear, a sore back or an arthritic hip is the "
           "usual reason. If nothing hurts, keep children out of his space, give him a bed he can "
           "walk away to, and ask the vet for a referral to a behaviourist rather than a trainer's "
           "quick fix."),
          # the thing that is held is the guarding row's question, the lead and other dogs are
          # theirs, the vet visit is its own answer, and a bite is the safety lane's
          avoid=("food", "bone", "bones", "bowl", "dinner", "toy", "toys", "chew", "treat",
                 "treats", "bed", "rawhide", "kong", "slipper", "ball", "stick", "tea",
                 "other dog", "other dogs", "another dog", "the dog next door", "on the lead",
                 "lead", "walk", "walking", "door", "doorbell", "postman", "barks", "barking",
                 "bark", "vet", "vets", "the vets", "groomer", "brush", "brushing",
                 "toothbrush", "teeth brushing", "bite", "bites", "bit", "bitten", "bit me",
                 # a dog that is scared of somebody is the shy-dog question, and it is answered
                 # by letting him come to that person on his own terms
                 "scared", "afraid", "frightened", "terrified", "nervous", "wary", "shy"),
          guard=_a_warning_sound_said, bias=4),
    entry("dog-vet-visit", (("dog", "puppy"),
                            ("vet", "vets", "the vets", "vet visit", "groomer")),
          ("Ask the vet for a nurse appointment and wait in the car until it's your turn, then feed "
           "him treats in the waiting room without letting other dogs crowd him. Ask them to crouch "
           "down and examine him on the floor, and go in for a free weigh-in every few weeks so most "
           "visits are boring: a dog who has been in four times for nothing is a much easier patient."),
          ask=("vet", "vets", "the vets", "vet visit", "groomer", "scared", "afraid",
               "terrified", "hates", "nervous", "shaking"),
          # the vet is in the conversation window after any answer that mentions it, so this row
          # woke up for the line after one too: "and can i report the dog to anyone", following a
          # question about a bite, was told how to make the next vet visit easier. Reporting a dog
          # is not a visit.
          avoid=("report", "reported", "reporting", "police", "officer", "dog warden",
                 "the council", "council", "dangerous dog", "sue", "compensation", "claim",
                 "who do i tell", "anyone i can tell")),
    # A dog that is out *now* got a lecture about hunting instinct: "my dog got out and i cant find
    # him", "my dog escaped and i cant find him" and "i cant find my dog anywhere" were all the
    # scent card, "my dog has gone missing what do i do" was a search hedge, "my dog is missing" was
    # "sorry to hear that", and "i lost my dog" was the bereavement card - the one reply a person
    # whose dog is alive and loose must never get. The boundary row answers a dog that keeps
    # getting out; this one answers a dog that is not back.
    entry("pet-lost-now", (("dog", "dogs", "doggy", "puppy", "pup", "cat", "cats", "kitten",
                            "kittens", "pet", "rabbit", "hamster", "guinea pig", "ferret",
                            "parrot", "budgie", "tortoise"),
                           ("missing", "gone missing", "went missing", "lost", "cant find",
                            "can't find", "cannot find", "nowhere", "disappeared",
                            "ran off", "ran away", "run off", "bolted", "escaped",
                            "got loose", "got away", "slipped his collar", "slipped her collar",
                            "took off", "not come back", "hasnt come back", "hasn't come back",
                            "didnt come home", "didn't come home", "hasnt come home",
                            "hasn't come home", "not come home", "no sign of")),
          _a_lost_pet,
          # A dog that keeps getting out is the boundary row's question, and a dog that is hurt,
          # dead or being put down is not a search: those cards keep their lines.
          avoid=("keeps", "kept", "always", "every time", "again", "lets himself out",
                 "hit by a car", "run over", "bleeding", "injured", "dead", "died", "dying",
                 "put to sleep", "put down", "passed away", "euthanised", "cremation",
                 "buried", "ashes", "lost my dog", "lost our dog", "lost her today",
                 "how long do", "how do i know",
                 # "my dog is missing his collar" is the harness card, not a search: the thing
                 # missing is a piece of kit, not the animal.
                 "missing his", "missing her", "missing its", "missing a tooth",
                 "missing teeth", "missing a leg", "missing an eye", "missing hair",
                 "is missing out", "missing out", "all the time", "every day", "every week"),
          bias=3),
    # A cat at the vet had no row of its own: "my cat spat at the vet" and "my cat hates the vet"
    # were a mirror back at the person, "my cat is scared of the vet" was the vet's desk, "my cat
    # bit the vet" was the play-biting card, and "how do i calm my cat before the vet" was the
    # yearly check-up schedule. The dog has had its own visit card all along; a cat is a different
    # patient, and the thing that settles a cat is a carrier nobody chases it into.
    entry("cat-vet-visit", (("cat", "cats", "kitten", "kittens"),
                            ("vet", "vets", "the vets", "vet visit", "vet trip",
                             "vet appointment")),
          "Ask for the first appointment of the day and wait in the car until it is your turn, with "
          "a towel over the carrier. Leave the carrier out all week with a worn T-shirt in it and "
          "feed her beside it, so it is not the thing that only means the vet. Ring the desk before "
          "you go: a calming spray or a sedative is kinder than being held down for a jab.",
          ask=("vet", "vets", "the vets", "spat", "scared", "afraid", "terrified", "hates",
               "hate", "nervous", "shaking", "shakes", "screams", "screaming", "cries", "crying",
               "bit", "bites", "hissed", "growled", "calm", "calming", "car", "carrier"),
          # How often it is seen, and what goes in it, is the check-up row's question: "how often
          # should my cat see the vet" and "when are my cats boosters" are not nerves.
          avoid=("how often", "how many times", "how regularly", "once a year", "every year",
                 "yearly", "annual", "annually", "boosters", "booster", "vaccination",
                 "vaccinations", "vaccine", "vaccines", "jab", "jabs", "worming", "microchip",
                 "how much", "cost", "price", "insurance", "afford", "sick", "ill", "vomiting",
                 "limp", "blood", "dying", "put to sleep"),
          bias=2),
    # How often the vet is seen is not the nerves of the visit. "how often should i take my dog to
    # the vet" reached `dog-vet-visit` and was told how to make the waiting room easier, which is
    # the answer to "my dog hates the vet". A booster is not a child's car seat either: "how often
    # does my dog need his boosters" was answered with the car-seat law.
    entry("pet-checkup",
          (PET_ANIMAL_ASK,
           ("check up", "checkup", "check-up", "health check", "boosters", "booster",
            "booster jab", "vaccinations", "vaccination", "vaccine", "vaccines", "jabs", "jab",
            "vaccinate", "vaccinated", "vaccinating", "jabbed", "inoculation",
            "vet", "vets", "see the vet", "go to the vet", "visit the vet", "yearly check")),
          _the_pet_checkup,
          ask=("how often", "how many times", "how regularly", "when", "yearly", "annual",
               "annually", "once a year", "every year", "should", "need", "does", "do i"),
          # a frightened animal at the vet, a price, an insurance bill and a sick pet are other
          # questions, and so is the date of a puppy's first jab
          avoid=("scared", "afraid", "terrified", "hates the vet", "hates going", "nervous",
                 "shaking", "cost", "price", "cheap", "expensive", "insurance", "bill",
                 "limp", "limping", "vomiting", "sick", "ill", "dying", "put down", "euthanise",
                 "euthanize", "chewing", "groomer", "grooming", "first jab", "first vaccination",
                 # an older cat or dog has a senior check card of its own, with what the extra
                 # visit looks for, so it keeps that line
                 "older", "old age", "elderly", "senior", "aging", "ageing",
                 "how old", "when can"),
          bias=3),
    entry("dog-walk-cold", (("dog", "dogs", "puppy", "pup"),
                            ("too cold", "cold outside", "cold weather", "cold today", "freezing",
                             "frost", "snow", "snowing", "ice", "icy", "minus", "need a coat")),
          ("Most dogs are fine down to about -5C as long as they are moving, so walk a shorter "
           "round, keep him on the lead in snow, and skip it in freezing rain. Thin, small, "
           "short-haired, old and very young dogs feel it sooner and want a coat below about 5C. "
           "Turn back if he shivers, lifts a paw or refuses to walk, and wash the salt off his "
           "paws when you are home."), bias=1),
    entry("dog-weight", (("dog", "dogs", "puppy", "pup"),
                         # "how do i help my dog lose weight" is the food answer and "my dog is
                         # losing weight" is the vet one: the callable reads which it is, so both
                         # shapes belong in the key
                         ("fat", "overweight", "weight", "diet", "slim", "obese", "thin",
                          "lose weight", "losing weight", "lost weight", "slim down",
                          "too heavy", "needs to lose", "need to lose", "cut down his food",
                          "cut down her food", "getting thin", "too thin", "ribs", "bony",
                          "skinny",
                          # "how much should a labrador weigh" asks for a figure, and "weigh"
                          # is not "weight": that line reached `pet-cost` and was told what a
                          # puppy costs, and "how heavy should a labrador be" got a shrug.
                          # "how many kg should a border collie be" names no weight word at all.
                          "weigh", "weighs", "weighing", "how heavy", "heavier", "kg",
                          "kilos", "kilo", "kilogram", "kilograms", "lbs",
                          "healthy weight", "ideal weight", "target weight",
                          "body condition", "what weight")),
          _dog_weight),
    # "cutting" is not a key word: "my dog has a cut on his paw" was read as a nail trim, because
    # the line's "cut" is a form of "cutting". "cut his nails" is a phrase, so the trim lines keep
    # their answer without handing them the wounded paw.
    entry("pet-cough", (("dog", "dogs", "puppy", "pup"),
                        ("cough", "coughing", "kennel cough", "wheezing", "hacking")),
          ("A cough that lasts more than a day or two needs a vet, and quickly if the animal is "
           "flat, off its food or breathing fast; kennel cough is common in dogs and spreads where "
           "dogs meet. Don't give human cough medicine, and keep a coughing dog away from others "
           "until the vet has seen it."), bias=1),
    # An adult dog is not a puppy, and its kit list is not the puppy's: no puppy food, no pen
    # for the daytime, and a greyhound or a rescue needs a coat and a bed it can stretch out in.
    # "im thinking of getting a rescue greyhound" then "what do i need to buy" reached nothing,
    # and the bot said "that is all of what I know on it" over an answer that never mentioned a
    # single thing to buy.
    entry("dog-kit", (("dog", "dogs", "greyhound", "lurcher", "rescue dog", "rescued dog",
                       "rescue greyhound", "rescue lurcher", "puppy", "puppies"),
                      ("need to buy", "what do i need", "need for", "need", "buy", "buying",
                       "supplies", "shopping", "kit", "what do i get", "pick up", "get in",
                       # The line that shares the news never names a thing to buy: "we are
                       # getting a dog next week" was "Get stuck in. What's the first bit?" and
                       # "we are adopting a dog" was "A dog - how long has it been with you?",
                       # which is nonsense for a dog that has not arrived. A cat gets its list on
                       # the same line, so a dog does too.
                       "new dog", "new puppy", "getting a dog", "getting a puppy",
                       "getting a pup", "getting one", "getting a rescue", "adopting",
                       "adopted", "adoption",
                       "arriving", "arrives", "coming home", "prepare", "preparing",
                       "before we", "before my")),
          _dog_kit,
          # The gate holds the phrase, not the verb: "getting" is the same word to the matcher as
          # "get", so a bare "getting" let "how do i get him out of it" - a puppy that nips -
          # reach a shopping list, and a behaviour question was answered with a bed and two bowls.
          ask=("need to buy", "what do i need", "need for", "need", "buy", "buying", "supplies",
               "shopping", "kit", "what do i get", "pick up", "get in",
               "getting a dog", "getting a puppy", "getting a pup", "getting my dog",
               "getting my puppy", "getting one", "getting another", "getting a rescue",
               "adopting", "adopted", "adoption", "arriving", "arrives",
               "coming home", "prepare", "preparing", "before we", "before my"),
          # "rescue" alone is a word about a cat, a rabbit or a donkey as easily as a dog, so the
          # species words are kept out: "what do i need for a rescue cat" is the cat's question.
          avoid=("cat", "cats", "kitten", "kittens", "rabbit", "rabbits", "bunny", "hamster",
                 "guinea", "bird", "birds", "parrot", "fish", "horse", "pony", "ferret",
                 "puppy", "puppies", "weeks old", "months old", "crate", "crate train", "train",
                 "training", "vet", "sick", "ill", "vomit", "limp", "cost", "how much", "afford",
                 "walk", "walking", "exercise", "feed", "feeding", "food", "sleep", "bark",
                 "settle", "name", "eat", "eating", "neut",
                 # "how do i get my dog to stop jumping" has the word "getting" in its stem and
                 # is a behaviour question, so the problems hold the list off
                 "jump", "jumps", "jumping", "bite", "bites", "biting", "pull", "pulls",
                 "pulling", "recall", "chew", "chews", "chewing", "scratch", "scratches",
                 "scratching", "barking", "how do i get", "stop",
                 # "need" is in this key, so a health question about a dog already in the house
                 # was the shopping list: "does my dog need a booster jab" was a bed, two bowls
                 # and a lead. The vet words belong to the rows that answer them.
                 "booster", "boosters", "jab", "jabs", "vaccination", "vaccinations", "vaccine",
                 "vaccines", "worming", "wormer", "wormed", "flea", "fleas", "tick", "ticks",
                 "diarrhoea", "microchip", "chipped", "insurance", "neutering", "spay",
                 "spayed")),
    # "how do i look after a new puppy" was reaching the two-dogs row, which told the person to
    # meet on neutral ground with one walker each: the only cards about a puppy were the kit list,
    # the walk, the feeding and how to introduce it to another dog, and none of them is the first
    # fortnight. "how do i care for a new puppy" was reaching houseplants-watering.
    entry("new-puppy",
          (("new puppy", "new pup", "puppy", "puppies", "pup", "got a puppy", "getting a puppy"),
           ("look after", "care for", "take care of", "care", "first week", "first night",
            "first day", "what do i do", "what now", "bring home", "brought home",
            "brought it home", "just got", "just brought", "routine", "settle in", "start")),
          "Three things on repeat: out into the garden every hour and after every meal, nap and "
          "play, because that is the whole of toilet training; food three or four times a day at "
          "set times; and a crate or pen it can sleep in with the door shut and something safe to "
          "chew. Book the first vet visit for the first week - a check, worming and the "
          "vaccination plan - and until the second jab is done walk it only where no other dogs "
          "go, carrying it out to meet people so it still meets the world. Keep the house small "
          "for a fortnight: one room, one bed, one routine, and short mad half-hours are normal.",
          ask=("how do i", "what do i", "what now", "look after", "care", "start", "need",
               "should i"),
          # two dogs meeting, the kit list, how much to feed, how far to walk, the vet and the
          # training are each their own card
          avoid=("introduce", "introducing", "meet", "meeting", "another dog", "second dog",
                 "existing dog", "older dog", "get on", "bond", "cost", "costs", "how much",
                 "price", "insurance", "afford", "need", "need to buy", "buy", "buying",
                 "supplies", "shopping", "kit", "feed", "feeding", "portion", "exercise",
                 "walk", "walks", "walking", "how long", "how often", "train", "training",
                 "crate size", "crate for", "which crate", "sick", "ill", "vomiting",
                 "diarrhoea", "limp", "bark", "barking", "bite", "biting", "chew", "chewing",
                 "sleep through", "crying at night")),
    entry("puppy-kit", ("puppy", ("need", "buy", "supplies",
                                  "shopping", "new puppy", "getting a puppy", "getting a pup",
                                  "getting one", 
                                  "adopting", "adopted", "arriving",
                                  "arrives", "coming home", "prepare", "preparing")),
          _puppy_kit,
          # the kit list only answers a shopping question: "i work full time, is that fair on it"
          # comes after "we're thinking about getting a puppy" and is not one
          # the phrase, not the verb: see the dog's gate above
          ask=("need", "buy", "buying", "supplies", "shopping", "get in", "getting in", "pick up",
               "kit", "what do i get", "getting a puppy", "getting a pup", "getting my puppy",
               "getting one", "getting another", "adopting", "adopted",
               "arriving", "arrives", "coming home", "prepare", "preparing"),
          avoid=("neuter", "neutered", "neutering", "spay", "spayed", "spaying", "castrate",
                 "castrated", "fair", "work", "working", "alone", "hours", "afford", "cost",
                 # "how much exercise does a puppy need" is not a shopping question
                 "exercise", "walk", "walks", "walking", "how much", "how often", "how long",
                 "feed", "feeding", "food", "training", "train", "sleep", "sleeping",
                 # "what do i buy my puppy for his first christmas" is a present, not the kit
                 ) + PRESENT_ASK),
    entry("dog-settling", (("dog", "dogs", "puppy", "pup", "rescue", "rescued",
                            "how long until he settles", "how long until she settles",
                            "how long until it settles", "how long before he settles",
                            "how long before she settles"),
                        ("settle", "settles", "settling", "settled", "settling in",
                         "first week", "first few days", "how long until he settles")),
          ("Give a rescue dog three days to feel safe, three weeks to unwind and three months to "
           "trust the routine: keep the first week quiet, no visitors and no long trips, and let "
           "him come to you. Feed and walk at the same times, give him a bed he can retreat to, "
           "and build up time alone from ten minutes. A confident dog settles in a fortnight, a "
           "nervous one takes a couple of months; if he is still hiding or off his food after a "
           "week, ring the rescue for help."),
          bias=2),
    # --- losing a pet ---
    entry("puppy-exercise", (("puppy", "puppies", "pup", "pups"),
                              ("exercise", "walk", "walks", "walking", "run", "running", "play",
                               "how much", "how often", "how long")),
          "Five minutes of walking for each month of age, twice a day, so three months is about "
          "fifteen minutes a time and six months about half an hour. Until the vaccinations are "
          "done, keep him off the ground where other dogs go and let him play in the garden "
          "instead; free running and stairs are the things to hold back on while his joints form.",
          # "how long does a puppy sleep" and "how long until he sleeps through" are sleep lines
          avoid=("sleep", "sleeps", "sleeping", "night", "nights", "nap", "naps", "bed",
                 "bedtime", "through the night", "settle", "settles", "settling",
                 # "how long can i leave my puppy alone" is the leaving answer, not exercise
                 "alone", "leave", "leaves", "left", "home alone", "on his own", "on her own",
                 # "how much is a puppy" was answered with the walking rule: "how much" is in
                 # this row's key as an ask, so every price question about a puppy landed here.
                 # What one costs to buy is `pet-cost`, and these words send the line there.
                 "how much is", "how much are", "how much does", "how much do", "what does",
                 "price", "prices", "cost", "costs", "expensive", "cheap", "cheaper",
                 "cheapest", "afford", "buy", "buying", "worth", "kennel club breeder",
                 "while i go", "while im out", "at work", "hours", "holiday",
                 # "how much should i feed my puppy" is the feeding answer: "how much" is in the
                 # key, and food is the one thing it means besides exercise
                 "feed", "feeds", "feeding", "food", "eat", "eats", "eating", "meals", "meal",
                 "portion", "portions", "grams", "treats", "diet",
                 # "my puppy has the runs" is loose stools, not a run around the park: the verb
                 # after "has the" is not the exercise in the key
                 "the runs", "has the runs", "got the runs", "runny", "runny poo", "loose poo",
                 "diarrhoea", "diarrhea", "squits", "tummy", "vomit", "vomiting", "sick",
                 # "how much does a puppy cost" is the money question: "how much" is in the
                 # key, and money is the other thing it means besides exercise
                 # "how much should a puppy weigh" is the body-weight question, and "how much"
                 # is in this key: the dog-weight card has the figure people want
                 "weigh", "weighs", "weighing", "weight", "how heavy", "kg", "kilos",
                 "kilogram", "kilograms", "lbs", "healthy weight", "ideal weight",
                 "target weight", "body condition",
                 "cost", "costs", "price", "prices", "expensive", "cheap", "afford", "budget",
                 "money", "spend", "insurance", "vet fees",
                 # "how much is a labrador puppy" asks what it costs, and the word "how much"
                 # in this key answered it with the walking rule
                 "how much is", "how much are", "how much for", "how much would",
                 "how much do puppies", "how much does a", "how much do dogs",
                 # house training has its own answer, and "how long" here was taking it: "how long
                 # until a puppy is house trained" and "how often should i take a puppy out" are
                 # the timing of toilet training, not of walks
                 "house train", "house trained", "house training", "toilet train",
                 "toilet training", "potty train", "potty training", "wee", "wees", "weeing",
                 "weed", "pee", "peeing", "peed", "piddle", "bladder", "accident", "accidents",
                 "toilet",
                 # "how often should i take a puppy out" is the toilet timing: taking him out is
                 # what toilet training is made of, and the walk answer took it on "how often"
                 "take a puppy out", "take the puppy out", "out to wee",
                 "out to the toilet"),
          bias=2),
    entry("pet-cost", (("puppy", "puppies", "pup", "dog", "dogs", "kitten", "kittens",
                         "cat", "cats"),
                          ("cost", "costs", "how much", "price", "prices", "expensive", "cheap",
                           "cheaper", "cheapest", "dearer", "afford", "affordable", "worth",
                           "budget", "money", "spend", "compare", "versus", "vs")),
          _pet_cost,
          # feeding, walking and sleeping are their own answers, and so is a rescue settling in;
          # insurance and a vet bill are quoted by their own lines rather than the buying price
          avoid=("feed", "feeds", "feeding", "food", "eat", "eats", "eating", "exercise", "walk",
                 "walks", "walking", "run", "sleep", "sleeps", "settle", "settling", "alone",
                 "leave", "hours", "toilet", "train", "training", "bite", "biting", "bark",
                 "insurance", "insure", "insured", "insures", "insuring", "insurance quote",
                 "vacccin", "vaccine", "vaccination", "jabs cost", "vet bill",
                 "vet fees", "consultation", "put to sleep",
                 # "how much to groom a dog" is the groomer's price and "how much water should a
                 # dog drink" is the water rule: neither is what the animal costs to buy, and
                 # "how much" is in this entry's key, so the words have to send them away
                 "groom", "grooms", "grooming", "groomer", "brush", "brushing", "trim", "clip",
                 "bath", "water", "drink", "drinks", "drinking", "thirsty", "walker", "walkers",
                 # a procedure with its own price is not the price of the animal
                 "neuter", "neutering", "neutered", "spay", "spaying", "spayed",
                 "castrate", "castrated", "castration", "microchip",
                 # "how much should a labrador weigh" and "how many kg should a border collie
                 # be" carry "how much" like a price question does, and the answer people want
                 # is a figure for the animal, not what it costs to buy
                 "weigh", "weighs", "weighing", "weight", "how heavy", "heavier", "kg",
                 "kilos", "kilo", "kilogram", "kilograms", "lbs", "stone",
                 "healthy weight", "ideal weight", "target weight", "body condition",
                 "jabs", "vaccinations", "worming", "flea", "kennel", "kennels", "boarding"),
          ask=("cost", "costs", "how much", "price", "prices", "expensive", "cheap", "cheaper",
               "cheapest", "afford", "budget", "money", "spend"),
          bias=2),
    # The small pets are priced one at a time: a hamster is 10 pounds and a horse is thousands a
    # year, so a single "a pet costs this much" line would be wrong for both of them.
    entry("small-pet-cost", (("rabbit", "rabbits", "bunny", "bunnies", "hamster", "hamsters",
                              "gerbil", "gerbils", "guinea pig", "guinea pigs", "budgie",
                              "budgies", "budgerigar", "parakeet", "cockatiel", "canary",
                              "horse", "horses", "pony", "ponies", "fish tank", "aquarium",
                              "tropical fish"),
                             ("cost", "costs", "how much", "price", "prices", "expensive",
                              "cheap", "cheaper", "afford", "budget", "money", "spend", "keep",
                              "keeping", "look after", "run")),
          _small_pet_cost,
          avoid=("how long", "lifespan", "live for", "how old", "cage size", "what do i feed",
                 "what to feed", "feed a", "food for", "hutch size", "how big", "sick", "ill",
                 "vet", "vets", "dying", "died", "pregnant", "litter", "train", "training",
                 "bite", "biting", "handle", "holding", "exercise", "wheel", "hay", "bedding",
                 "groom", "grooming", "brush", "nails", "teeth", "insurance", "name", "name it"),
          ask=("cost", "costs", "how much", "price", "prices", "expensive", "afford", "budget",
               "money", "spend"),
          bias=1),
    entry("dog-introduce", (("dog", "dogs", "puppy", "puppies", "pup"),
                             ("introduce", "introducing", "introduction", "meet", "meeting",
                              "get on", "bond", "another dog", "second dog", "new dog",
                              "older dog", "new puppy", "existing dog",
                              # "my two dogs fight" is the same question as "my dogs dont get on",
                              # and it was answered "Two dogs - do they get on?", which asks the
                              # person what they had just told the bot.
                              "fight", "fights", "fighting", "fought", "scrap", "scraps",
                              "scrapping", "squabble", "squabbles")),
          "Meet on neutral ground, one walker each, and walk them side by side rather than face to "
          "face, then let them off lead only in a fenced space where the older dog can walk away. "
          "At home give the older dog his own bed, bowl and corner that the puppy cannot reach, "
          "feed them apart, and step in before the puppy hangs off his ears. Two weeks of short, "
          "supervised time together settles most pairs; guarding food or a hard stare needs a "
          "behaviourist.",
          # "should i get a second dog" is whether, not how: that one keeps its own answer, and
          # "what do i need for a new puppy" is the kit list. The line has to ask how they meet.
          ask=("introduce", "introducing", "introduction", "meet", "meeting", "get on",
               "get along", "get used to each other", "bond", "bonding", "settle in together",
               "grumpy", "growl", "growls", "growling", "snaps at", "snappy", "hates the puppy",
               "doesn't like the puppy", "does not like the puppy", "being off with the puppy",
               # "getting a puppy with an older dog" and "new puppy and existing dog" name the two
               # animals and ask nothing else: they were read back as "A puppy and a dog. Who's in
               # charge?" - the opener of a chat, when the introduction is the question.
               "getting", "new puppy", "existing dog", "older dog", "second dog",
               "another dog", "fight", "fights", "fighting", "fought", "scrap", "scraps",
               "scrapping", "squabble", "squabbles") + _NEW_ANIMAL_REACTION,
          avoid=("should i get", "should we get", "should i", "should we", "thinking about",
                 "thinking of", "is it fair", "good idea", "ready for", "right time",
                 "what do i need", "need for a", "buy",
                 # the first fortnight with one puppy is its own card, and it was this row that
                 # answered "how do i look after a new puppy" with the two-dogs introduction
                 "look after", "care for", "take care of", "first week", "first night",
                 "bring home", "brought home", "just got", "got a new puppy", "got a puppy",
                 "i got a puppy", "what do i do", "what now", "what should i do",
                 # a puppy biting the furniture is a chewing question, not two dogs meeting
                 "biting", "bites", "chewing", "chews", "chewed", "nips", "nipping",
                 # A bird is not a second dog: "will a dog get on with my parrot" was answered
                 # "one walker each, walk them side by side ... let them off lead", which is
                 # advice for two dogs and nobody else.
                 "parrot", "parrots", "budgie", "budgies", "budgerigar", "cockatiel",
                 "parakeet", "canary", "canaries", "bird", "birds",
                 # "suggest a name for my new puppy" met "new puppy" and was told how two dogs
                 # should meet: a naming question is pet-name's, and so is a name already given
                 "name", "names", "named", "naming", "name for", "call him", "call her",
                 "call it", "call them", "rename", "suggest a name",
                 # "my dog keeps getting on the sofa" is the keeping-off row, not two dogs
                 # meeting: the bare "get on" in the key reaches it as a form of "getting on"
                 "sofa", "settee", "couch", "getting on the", "gets on the", "allowed on",
                 "keep him off", "keep her off", "keep the dog off", "keeps jumping up",
                 # A puppy crying at night is not two dogs meeting. "our new puppy cries all
                 # night" reached this row off "new puppy" in the key and got the neutral-ground
                 # introduction, and the night card that answers it was passed over.
                 "cries", "crying", "cried", "whines", "whining", "all night", "at night",
                 "every night", "wont sleep", "will not sleep", "cant sleep", "cannot sleep",
                 "keeps me awake", "wakes me", "waking me", "woke me"),
          bias=2),
    entry("puppy-night-when", (("sleep through the night", "sleeps through the night",
                                 "sleep through", "sleeps through", "through the night",
                                 "sleep all night", "sleeps all night",
                                 # the animal is named too, because the follow-up that asks when
                                 # leans on the puppy named a turn earlier and an entry about no
                                 # animal at all is passed over for the neighbour that names one
                                 "puppy", "puppies", "pup", "dog", "dogs"),
                                ("how long", "when", "how many weeks", "how old", "until",
                                 "what age")),
          "Most puppies manage a whole night at around four months, and none of them at eight "
          "weeks: their bladder is small and they need to go out in the night. Take him out last "
          "thing and once in the night without playing or talking, keep the room dark, and wake "
          "him for that trip rather than waiting for the whine, so he learns the night is for "
          "sleeping.",
          # "how long can a dog hold its bladder" and "how long should a dog sleep" are other
          # questions: this entry is the night-settling one, so it needs the phrase that asks it
          ask=("sleep through", "sleeps through", "through the night", "all night"),
          # the same words are a parent's question: "when do babies sleep through the night"
          # came back with four months and a puppy's bladder
          avoid=("baby", "babies", "newborn", "infant", "toddler", "child", "children", "kid",
                 "kids", "my son", "my daughter", "cot", "crib", "breastfeed", "breastfeeding",
                 "formula", "night feed", "night feeds", "teething", "months old", "month old"),
          bias=2),
    # The age a pet is neutered is asked far more often than it is decided, and nothing in the
    # tables had it: "when do you spay a female dog" and "what age do you neuter a rabbit" were
    # search hedges, "when should i get my dog neutered" was the getting-a-puppy answer and
    # "what age do you neuter a cat" was the older-cat check-up. The price is the cost row's,
    # and the age the jabs are due is not this row: that line is taken by the store's own age
    # ask before any knowledge row sees it, which is a fault of its own and not of this table.
    entry("pet-neuter-when",
          # The operation's word is the subject, not the animal: with the animal in this arm the
          # line "should i get a dog" answered what age a dog is neutered, because "should" is
          # one of the asks below.
          (("neuter", "neutered", "neutering", "neuters", "spay", "spayed", "spaying",
            "spays", "castrate", "castrated", "castrating", "castration", "the snip",
            "snipped", "desexed", "sterilised", "sterilized"),
           ("when", "how old", "what age", "at what age", "how many months", "months old",
            "before", "too young", "too old", "too late", "best age", "right age",
            "old enough",
            # "should i get my dog neutered" was read as "should I get a dog" and answered the
            # walking-it-at-seven card, and "do i have to neuter my dog" was a hedge: the choice
            # is the same question as the timing, and a neuter word is needed either way
            "should", "should i", "should we", "have to", "need to", "got to", "must",
            "necessary", "required", "recommended", "worth it", "optional", "a choice")),
          # Said with the animal first in the line or not at all, so the opening is the same for
          # a cat, a rabbit and a dog rather than a dog's answer that happens to mention cats.
          ("It depends on the animal. A dog is usually done at about six months, and the bigger "
           "the breed the later: a large or giant dog is often left to nine or twelve months, a "
           "small one at five or six, and a bitch before her first season or three months after "
           "one ends rather than in the middle of it. A cat at four to six months, a female from "
           "about four, before her first litter. A rabbit at about four months for a buck and "
           "five or six for a doe, and both before they are bonded rather than after. There is "
           "no upper limit either, so an older animal can still be done and the vet will weigh "
           "the anaesthetic against the reason. Nothing says you must, so it is a choice as well "
           "as a date: ask your own vet what they would do for your animal, because the timing "
           "is a conversation, not a rule."),
          ask=("when", "age", "how old", "months", "weeks", "time", "best", "right",
               "old enough", "too young", "too old", "too late", "should", "have to",
               "need to", "must", "worth it", "choice"),
          avoid=("cost", "costs", "price", "prices", "how much", "expensive", "cheap",
                 "afford", "money", "quote", "insurance", "jab", "jabs", "vaccination",
                 # a baby's bottle is sterilised too, and "when should i stop sterilising
                 # bottles" was answered with what age a dog is neutered
                 "bottle", "bottles", "teat", "teats", "dummy", "dummies", "breast pump",
                 "sterilising bottles", "sterilising a bottle", "jam", "jars",
                 "vaccinations", "vaccine", "microchip", "chipped", "worming", "flea",
                 # not the surgery: a pet that has just been done, or is unwell after it, is the
                 # vet's question and not the timing of it
                 # the day of the operation is also not the date of it: a person asking what to
                 # do tomorrow has the date and needs the bowl and the blanket
                 "tomorrow", "tonight", "last night", "this morning", "what do i do",
                 "what should i do", "before the op", "before his op", "before her op",
                 "the night before", "dropping him off", "dropping her off", "prepare",
                 "after the op", "after his op", "after her op", "recovery", "recovering",
                 "swelling", "bleeding", "stitches", "cone", "not eating", "sleepy",
                 "lethargic", "vomiting", "sick", "wound", "infection",
                 # behaviour a person hopes the operation will cure is its own question
                 "calm", "calmer", "calming", "humping", "aggressive", "aggression",
                 "marking", "spraying", "roaming", "wander", "wandering", "behaviour",
                 "will it stop", "stop him", "stop her", "hormonal", "moody", "season",
                 "in season", "heat", "pregnant", "pregnancy",
                 # a person is not a pet
                 "hysterectomy", "vasectomy", "my husband", "my wife", "myself", "human",
                 "baby", "babies", "child", "children", "kid", "kids"),
          bias=2),
    entry("cat-matted-fur",
          (("cat", "cats", "kitten", "kitty"),
           ("mat", "mats", "matted", "knot", "knots", "knotty", "knotted", "tangled",
            "tangles", "tangle", "clumps", "clump", "fur", "coat", "brush", "brushing",
            "groom", "grooms", "grooming", "groomed",
            # "how often should i brush my cat" was the older-cat check-up answer, because the
            # how-often words are what that row keys on: the count is the question here too.
            "how often", "how many times", "every day", "daily", "once a week", "twice a week",
            "weekly", "greasy", "grease", "oily",
            # main's `older-cat-checks` keys cat + "how often" too and wins the tie on its bias,
            # and a part credits only its best alternative, so the brushing has to be a part of
            # its own for "how often should i brush my cat" to count three signals.
            ),
           # brushing only: "grooming" is in the part above and the hair-loss row keys it too,
           # and a part of its own for it took "my cat has stopped grooming" away from the vet
           ("brush", "brushes", "brushing", "brushed", "comb", "combs", "combing")),
          _cat_coat,
          # a bath mat is a place a cat wees, and "mat"/"mats" alone was taking those lines
          avoid=("dog", "dogs", "rabbit", "human", "my hair", "haircut", "shedding vacuum",
                 "vacuum", "hoover", "brush for the sofa", "wee", "wees", "weeing", "peed",
                 "pee", "poo", "poos", "pooing", "litter", "tray", "toilet", "bath mat",
                 "bathroom mat", "scratching", "scratches", "mouse", "mice", "rat", "rats",
                 "bird", "birds", "caught", "dropped", "deposited", "prey", "dead",
                 # a coat coming out is the hair-loss row, not a mat to be worked loose: this
                 # row keys on "coat" and "fur", so a shedding line would otherwise get the
                 # brush routine
                 "shed", "sheds", "shedding", "moult", "moulting", "molting", "hair loss",
                 "losing fur", "losing hair", "bald", "patchy", "patches", "thin coat",
                 # teeth, claws and ears are brushed too, and none of them is the coat
                 "teeth", "tooth", "toothbrush", "breath", "claws", "claw", "nails", "ears",
                 "ear",
                 # the row carries "how often" for "how often should i brush my cat", and so
                 # does the feeding question: "how often should i feed my cat" and "how often
                 # should i feed a kitten" were both answered with the five-minute brush
                 # routine. The feeding words stand the brush down, whatever the frequency.
                 "feed", "feeds", "feeding", "fed", "food", "foods", "meal", "meals",
                 "how much", "portion", "portions", "kibble", "wet food", "dry food",
                 "treats", "treat", "hungry", "eats", "eating", "ate",
                 # a cat that is sick is not a cat to be brushed, and this row's frequency words
                 # ("every day", "daily", "how often", "twice a week") are exactly how people
                 # say how often it happens: "my cat is sick every day", "my cat has been sick
                 # every day this week", "my cat is being sick daily", "my cat vomits every
                 # day", "my cat is ill every day" and "my cat has been sick once a week" were
                 # all answered with the five-minute brush routine. A schedule is the question in
                 # those lines too, and the answer is the vet's. "hairball" stays out on purpose:
                 # brushing is half the answer to a cat that keeps bringing them up.
                 # The bare adjectives stay out: "ill" is in "ill tempered" and "not well" in
                 # "not well behaved", so a bare one stood the brush routine down for a cat with
                 # nothing wrong with it and some other cat row took the line (an old-cat
                 # check-up for "my cat is ill tempered, how often should i brush her"). A word
                 # here carries either the symptom itself ("being sick", "throwing up") or the
                 # repetition that is what the brush row keys on ("ill every", "diarrhoea for"),
                 # so a person asking how often to brush a cat with a grumble keeps the brush
                 # routine and a cat that is ill every day gets the vet.
                 "sick", "sickness", "vomit", "vomits", "vomiting", "vomited",
                 "throwing up", "threw up", "throws up",
                 "being sick", "keeps being sick",
                 "ill every", "ill since", "ill most days", "ill for",
                 "unwell every", "unwell since", "unwell for",
                 "poorly every", "poorly since", "poorly for",
                 "diarrhoea every", "diarrhoea since", "diarrhoea for", "diarrhoea twice",
                 "diarrhoea once a week", "diarrhea every", "diarrhea since", "diarrhea for",
                 "diarrhea twice", "diarrhea once a week",
                 "off her food", "off his food", "off their food", "not eating",
                 "stopped eating")),

    entry("cat-off-counters", (("cat", "cats", "kitten", "kittens"),
                               ("counter", "counters", "countertop", "kitchen", "worktop",
                                "worktops", "hob", "cooker", "stove", "surface", "surfaces",
                                "work surfaces", "table", "tables", "up on the", "jump up",
                                "jumps up", "jumping up",
                                "jump", "jumps", "jumping",
                                # the phrase, not the verb: "how do i keep my cat off the
                                # counters" scores a phrase point for "off the" and so outranks
                                # the pushing-things answer, which is where it went before.
                                "off the", "off my", "off our", "stay off", "kept off")),
          ("Make the worktop boring and the floor worth being on. Clear the counters of food and "
           "anything breakable, put double-sided tape or a strip of foil along the edge for a "
           "fortnight - cats hate the feel and the noise - and give her a stool or a chair by the "
           "window instead. Feed her before you cook rather than while you eat, and never leave a "
           "chair pulled up against the counter. Shouting or squirting water teaches her to jump "
           "up when you are not there, so the quiet, boring counter is what works."),
          # a garden is not a worktop, and neither is a table: the garden answer owns the
          # flowerbed, and the pushing-things answer owns the mug on the table.
          avoid=("garden", "gardens", "lawn", "flowerbed", "flower beds", "borders", "sandpit",
                 "pooing", "poo", "poos", "digging", "messing", "seedlings",
                 # a table is a surface to keep a cat off too, and it is in the key now:
                 # "my cat keeps jumping on the kitchen table" was a bare "Got it" (pink-nail)
                 "shelf", "shelves", "desk", "mug", "cups", "vase",
                 # a sofa and a plate are not the worktop either, and "off the" now reaches
                 # this entry from all three: "how do i keep my cat off the sofa" wants the
                 # furniture answer, and food off a plate is the begging question.
                 "sofa", "sofas", "couch", "settee", "armchair", "bed", "beds", "christmas tree",
                 "plate", "plates", "food", "eating", "eats", "eat my", "scraps",
                 # knocking the mug off is the paws answer, even when the surface is the
                 # counter: this entry is about staying up there, not about the crash.
                 "knock", "knocks", "knocking", "push", "pushes", "pushing", "swipes", "swiping",
                 # a cat being sick on the table is not a cat who lives on it
                 "sick", "vomit", "vomited", "vomiting", "threw up", "throwing up", "hairball",
                 # a cat that has stopped jumping, or cannot, is stiff and wants the vet, not a
                 # strip of foil on the worktop: "my cat wont jump up any more" and "my cat
                 # struggles with the stairs and wont jump up" were both this answer.
                 "wont jump", "won't jump", "stopped jumping", "cant jump up", "can't jump up",
                 "no longer jumps", "not jumping any more", "struggles with the stairs",
                 "stiff", "arthritis", "in pain"),
          # "my cat jumps on the worktop" is this question, and main answered it with the
          # arthritis one: the counters answer wins the tie with the knocking-things one.
          # "how do i keep my cat off the counters" is the same tie against the pushing-things
          # answer, and two is what makes the counters answer win it.
          bias=2),

    entry("dog-kept-out-of-a-room",
          (("dog", "dogs", "puppy", "pup", "puppies"),
           # The rooms are not in the key on their own. "bed", "kitchen" and "room" are nouns
           # that every dog-bed line and every dog-in-the-kitchen line carries, so a bare
           # "bed" took "which dog bed is best" and "my dog sleeps in my bed" and gave them a
           # door routine. The keeping-out phrase is the question, and the room rides along.
           ("off the", "out of the", "keep him out", "keep her out", "keep them out",
            "keep the dog out", "keep a dog out", "keep dogs out", "kept out", "not allowed",
            "baby gate", "stairgate", "stay out", "stay off", "staying out", "staying off",
            "getting in the", "getting into the", "getting on the", "gets in the",
            "gets on the", "got in the", "got on the", "going upstairs", "goes upstairs",
            "allowed on the", "allowed in the", "allowed upstairs", "allowed up the",
            "not allowed on", "banned from the", "barred from the",
            "going up the stairs", "up the stairs", "on the sofa", "on the couch",
            "on the settee", "in the kitchen", "in the bedroom", "in the front room")),
          "One rule, always the same, and a place that is better than the one you are banning: a "
          "bed in the corner of the same room, a chew there, and a treat every time he settles on "
          "it. A baby gate or stairgate does the kitchen and the stairs without a fight, and "
          "closing the door beats saying no twenty times. Nobody in the house should let him up "
          "\"just this once\" - that is what teaches him to keep trying. If he is already in the "
          "room, walk him out by the collar without a word and reward him for the bed.",
          # The doorbell, the chew and the chewing are other entries' lines, and so is anything
          # that happened to the dog on the furniture: a fall or a limp is a health question.
          avoid=("doorbell", "door bell", "bark", "barks", "barking", "chew", "chewing",
                 "chewed", "toilet", "wee", "poo", "separation", "alone", "car", "vet",
                 "clean", "cleaning", "stain", "smell", "fell", "fall", "falls", "fallen",
                 # "out of the" and "getting into the" are in the key because that is how a
                 # room is named, and beside a dog they also carry the mess he left: "how do i
                 # get dog sick out of the carpet" scored key words "dog" and "out of the" and
                 # was told how to keep him out of the front room. Anything that came out of the
                 # dog and landed somewhere is the cleaning rows' question, not the door's.
                 "sick", "vomit", "vomited", "vomiting", "spit up", "threw up",
                 "spill", "spills", "spilled", "spilt", "spillage",
                 "jumped off", "jumps off", "slipped", "hurt", "hurts", "limp", "limping",
                 "seems fine", "shaking", "crying", "in pain",
                 # licking the furniture is a habit question, not a door one
                 "lick", "licks", "licking", "chewing the", "scratching the",
                 # what he picks up and eats out on a walk is the scavenging entry's line
                 "street", "pavement", "walk", "walks", "eating things", "eats things",
                 "picks up", "rubbish", "litter", "bins", "off the ground",
                 "grow out of", "grows out of", "grow out", "will he", "will she",
                 # a bed is bought, slept in, washed and moved: none of those is the door
                 "sleep", "sleeps", "slept", "sleeping", "wont sleep", "won't sleep",
                 "buy", "buying", "bought", "best", "which bed", "what bed", "bed for",
                 "how often", "follows me", "follows him", "follows her",
                 # "how do i stop the dog getting in the kitchen" is this question
                 ),
          bias=1),

    entry("pet-bed-clean",
          (("dog bed", "dog beds", "cat bed", "cat beds", "pet bed", "pet beds", "puppy bed",
            "kitten bed", "dog basket", "cat basket", "pet basket", "dog blanket", "cat blanket",
            "dog bedding", "pet bedding", "dog mattress", "cat igloo"),
           ("clean", "cleaning", "cleaned", "wash", "washing", "washed", "smell", "smells",
            "smelly", "stink", "stinks", "how", "how often", "often", "stain", "stains",
            "hair", "should i")),
          "Take the cover off and wash it at 60C with a normal detergent and no fabric softener, "
          "which coats the fibres and holds the smell in. The foam or filling inside usually cannot "
          "go in a machine: hoover it, sponge any stain with warm water and a little washing-up "
          "liquid, and let it dry flat in the sun or by a radiator, turned once, until it is dry "
          "right through - a bed that is still damp inside smells again within a week. If there "
          "have been fleas, wash everything at 60C and vacuum the cracks round the bed as well, "
          "because the eggs are not in the bed. Two covers so one is on while the other washes.",
          avoid=("where should", "which bed to buy", "what bed", "size", "buy", "buying",
                 "crate", "training", "out of the", "keep him out", "keep her out", "sleep",
                 "sleeps in my", "in my bed", "on my bed"),
          # "beds" in a garden entry is a flower bed, so a cat's own bed needs the nudge
          bias=1),
]

from .costs import time_entries
# A consultation at the vet is asked how long it takes, and the duration is what is missing.
ENTRIES += time_entries("vet")


# --- a bored pet, and whether a pet knows its name -------------------------------------------
# Neither had an answer: "i think my cat is bored, what can i do" and "my dog is bored, what can
# i do" both shrugged, "my cat seems bored what should i do" got the feeding amounts, "how do i
# play with my cat" got the new-cat-and-dog introduction, and "does my cat know his name" got the
# feeding amounts while "does my cat understand me" reached the interview answer. The name entry
# had been kept off "know his name" on purpose, because that is a different question from naming
# one - it just had nowhere to go.
ANIMAL = r"\b(cat|cats|kitten|kittens|dog|dogs|puppy|pup|puppies|rabbit|rabbits|bunny|bunnies)\b"


def _pet_kind(memory, understood):
    """Which animal this line is about: the one it names, otherwise the one the chat is on.

    "my cat is bored" then "what toys should i get" is a question about that cat, and the follow-up
    names no animal of its own, so the animal is read off the chat: `_pet_words` falls back to a dog
    when the line names none, and the person got "A dog is bored because the day is short on
    sniffing" about a cat. Nothing in memory to go on leaves the old reading alone.
    """
    text = (understood or {}).get("clean") or ""
    if re.search(ANIMAL, text):
        return _pet_words(understood)["kind"]
    pets = (memory.get("user") or {}).get("pets") if isinstance(memory, dict) else None
    for one in pets or []:
        animal = str((one or {}).get("animal") or "").strip().lower()
        if animal in ("cat", "dog", "rabbit"):
            return animal
    return _pet_words(understood)["kind"]


BORED_ASK = ("bored", "boredom", "entertain", "entertained", "entertainment", "stimulation",
             "enrichment", "nothing to do", "play", "playing", "playtime", "play with", "toy",
             "toys", "occupied", "keep busy")


def _bored_pet(memory, understood):
    """What to do about a bored pet, in the animal's own terms."""
    if _other_pet(understood):
        return None
    kind = _pet_kind(memory, understood)
    if kind == "cat":
        return ("Play with a wand toy for five or ten minutes, two or three times a day, and let "
                "her stalk and pounce before you let her catch it, then give her a meal so the "
                "hunt has an end. The rest of the day wants things rather than toys: a food "
                "puzzle, a cardboard box, a paper bag, somewhere high to sit and a window to "
                "watch. Rotate the toys and put half of them away, because a basket she has seen "
                "for months is furniture.")
    if kind == "rabbit":
        return ("A rabbit is bored when it has nothing to chew and nowhere to dig: give it a run "
                "of a few hours a day outside a hutch, a box of hay to root through, willow or "
                "apple sticks to chew and something to hide under. A lone rabbit wants a rabbit "
                "friend more than it wants toys, and the two are happiest neutered and introduced "
                "slowly.")
    if re.search(r"\b(work|working|left|alone|out)\b", (understood or {}).get("clean") or ""):
        return ("Four hours at a time is about the usual comfortable limit for an adult dog, so "
                "build the time up in short chunks and have someone look in at lunchtime for a "
                "puppy. Then fill the day: half his dinner scattered on the "
                "lawn or in a snuffle mat, something legal to chew, the radio on, and a walk where "
                "he is allowed to sniff when you get back. A dog left with nothing to do chews "
                "the furniture and paces, and that is boredom rather than badness.")
    return ("A dog is bored because the day is short on sniffing and chewing, not because he "
            "needs more toys. One walk where he is allowed to stop and sniff does more than a "
            "long march, and a scatter of his dinner on the lawn or in a snuffle mat takes ten "
            "minutes off the clock. Add five minutes of training a day, something legal to chew "
            "and a game of tug, and break the day up rather than saving it all for the evening.")


NAME_ASK = ("know his name", "knows his name", "know her name", "know its name",
            "know their name", "know the name", "recognise his name", "recognize his name",
            "recognise her name", "respond to his name", "respond to her name",
            "learn his name", "learn her name", "teach his name", "teach her name",
            "understand his name", "understand me", "understand you", "know your voice",
            "know what i say", "learn words", "know words", "know the word",
            # the phrase has to sit side by side in the line to match, and "can i teach my cat
            # his name" puts the animal in the middle of it: the bare verbs keep that shape
            "teach", "teaches", "learn", "learns", "learned", "learnt", "recognise", "recognize",
            "respond", "responds")


def _knows_name(memory, understood):
    """Whether a pet knows its name: a dog learns the word, and a cat does too, but answers less."""
    if _other_pet(understood):
        return None
    kind = _pet_kind(memory, understood)
    if kind == "cat":
        return ("Yes - a cat can pick her own name out of a list of similar words, so she knows it "
                "about as well as a dog does; what she does not do is come running when she hears "
                "it. Say it before the food or the wand toy rather than after, and she will start "
                "looking up when you use it. A cat that stops answering her name may have gone "
                "deaf, which a vet can check, or may just have decided the sofa is better.")
    if kind == "rabbit":
        return ("A rabbit learns its name as a sound that means food, not the way a dog does: say "
                "it just before you put the bowl down or open the run, and it will start turning "
                "towards you. They are prey animals and will not usually come when called, and a "
                "rabbit that ignores its name has not forgotten it.")
    return ("Yes - most family dogs understand a few dozen words, and the best of them well over a "
            "hundred, and their own name is the first. Say the name once and then the cue - "
            "'Biscuit, sit' - and reward, so the name becomes the thing to look at before "
            "something good happens. Never use it to tell him off: a name that means trouble is a "
            "name he learns to ignore.")


ENTRIES.append(entry(
    "pet-bored",
    (("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "pup", "puppies", "rabbit",
      "rabbits", "bunny", "bunnies", "pet", "pets"),
     BORED_ASK),
    _bored_pet, bias=2,
    # A new cat meeting a dog is the introduction answer, another cat is the second-cat one, and
    # a name is the naming question: all three get asked with "play" or "bored" in the line.
    avoid=("introduce", "introduction", "get on", "gets on", "new cat", "new kitten",
           "second cat", "another cat", "hates the dog", "growl", "growls", "chase", "chases",
           "name", "names", "named", "naming", "on walks", "lead", "recall", "come when"),
    ask=BORED_ASK))

ENTRIES.append(entry(
    "pet-knows-name",
    (("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "pup", "puppies", "rabbit",
      "rabbits", "bunny", "pet", "pets"),
     NAME_ASK),
    _knows_name, bias=2,
    # Naming a pet is the other question, a name that is a fact about the house is memory's, and
    # a cue the animal is taught to obey is training ("how do i teach my dog to sit").
    avoid=("what should i name", "what shall i name", "should i name", "should we name",
           "what to name", "name ideas", "name for my", "whats my", "what is my", "i named",
           "we named", "rename", "called",
           # a fact about the pet is the memory store's to acknowledge: "my dog knows his name
           # already" was "Noted: your dog knows his name already", which is the better reply
           "already",
           # "teach my dog to come to me" is the recall lesson, and the bare "teach" in NAME_ASK
           # was letting it through: a name question never says "come to".
           "come to", "come to me", "come to us", "come here",
           "sit", "stay", "down", "off", "heel", "recall", "come back", "come when", "fetch",
           # "my dog drags me down the street" is the lead question, and "down" was the only
           # word the sit card needed for it
           "drag", "drags", "dragging", "pulls me", "down the street", "down the road",
           "paw", "trick", "tricks", "toilet", "lead", "walk", "walks", "bark", "barking",
           # the pulling question is asked with the bare verb and no lead: "how do i teach my
           # dog to stop pulling" was answered with how many words a dog understands
           "pull", "pulls", "pulling", "pulled", "drag", "drags", "dragging"),
    ask=NAME_ASK))

# --- the animal that has stopped eating, and the two lines about it --------------
# `dog-not-eating` and `cat-not-eating` cover the two commonest pets, and every other animal had
# nothing: "my rabbit is off her food" came back as "Noted: your rabbit is off her food" and "my
# tortoise wont eat" as the advice for a child who will not eat vegetables. How long it can wait
# matters more than the species, so one row says the number for each kind of animal.
_OFF_FOOD = ("rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs", "guineapig",
             "hamster", "hamsters", "gerbil", "gerbils", "chinchilla", "chinchillas", "ferret",
             "ferrets", "rat", "rats", "mouse", "mice", "degu", "degus", "hedgehog", "hedgehogs",
             "tortoise", "tortoises", "turtle", "turtles", "lizard", "lizards", "bearded dragon",
             "gecko", "geckos", "snake", "snakes", "python", "corn snake", "budgie", "budgies",
             "parrot", "parrots", "cockatiel", "cockatiels", "bird", "birds", "fish", "goldfish")

_OFF_FOOD_ASK = ("not eating", "isnt eating", "isn't eating", "wont eat", "won't eat",
                 "doesnt eat", "doesn't eat", "stopped eating", "off her food", "off his food",
                 "off their food", "off its food", "refusing food", "refusing to eat",
                 "no appetite", "not hungry", "hasnt eaten", "hasn't eaten", "not eaten",
                 "eating nothing", "wont touch her food", "wont touch his food",
                 "wont touch its food", "wont feed", "will not eat", "not feeding")

# How long it can wait is the thing a person needs, and it is not the same animal twice: a rabbit
# is in trouble at twelve hours, a snake that skips a fortnight is normal, and a budgie hides it
# until it is very thin. The species in the line picks the reply, so one row can hold them all.
_OFF_FOOD_RABBIT = ("rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs",
                    "guineapig", "cavy")
_OFF_FOOD_RODENT = ("hamster", "hamsters", "gerbil", "gerbils", "rat", "rats", "mouse", "mice",
                    "chinchilla", "chinchillas", "ferret", "ferrets", "degu", "degus", "hedgehog",
                    "hedgehogs")
_OFF_FOOD_BIRD = ("budgie", "budgies", "parrot", "parrots", "cockatiel", "cockatiels", "bird",
                  "birds", "canary", "lovebird", "cockatoo", "finch")
_OFF_FOOD_REPTILE = ("tortoise", "tortoises", "turtle", "turtles", "lizard", "lizards",
                     "bearded dragon", "gecko", "geckos", "snake", "snakes", "python",
                     "corn snake", "chameleon", "skink", "terrapin")
_OFF_FOOD_FISH = ("fish", "goldfish", "koi", "betta", "guppy", "tetra", "cichlid", "molly")


def _off_food_said(line, words):
    return any(word in line for word in words)


# The eating verb, so the line can tell the animal that has stopped eating from the animal that is
# being eaten: "my goldfish wont eat" has the animal before the verb, "my son doesnt eat fish" has
# it after. Only the first two kinds are pets that stop feeding; the third is a person's diet.
_EAT_VERB = re.compile(r"\b(?:eat|eats|eating|ate|eaten|fed|feeding|feed)\b")


def _the_animal_is_eaten(line):
    """Whether the animal in the line is what someone eats, rather than the one off its food.

    "my son doesnt eat fish" is a fact about the son's diet, and the fish answer - test the water,
    it is nearly always ammonia - is about a different line altogether. "my fish isnt eating" and
    "the fish in my tank wont eat" keep it, because there the animal is in front of the verb.
    """
    verb = _EAT_VERB.search(line)
    if not verb:
        return False
    first = min((line.find(word) for word in _OFF_FOOD if word in line), default=-1)
    return first > verb.start()


def _off_food_reply(memory, understood):
    line = str(understood.get("clean") or understood.get("text") or "").lower()
    if _the_animal_is_eaten(line):
        return None
    if _off_food_said(line, _OFF_FOOD_FISH):
        return ("Don't feed it and test the water: a fish that stops feeding is nearly always "
                "ammonia, nitrite or a tank that has gone cold, so use a liquid test kit, change a "
                "quarter of the water with dechlorinated water at the same temperature and leave "
                "the feeding for a day or two. A fish that is also gulping at the top or swimming "
                "on its side is the urgent one.")
    if _off_food_said(line, _OFF_FOOD_REPTILE):
        return ("A reptile that skips a feed is usually nothing: a snake can go weeks, and a "
                "tortoise off its food in winter or before shedding is normal. What makes it a vet "
                "visit is weight loss, a soft shell, a runny nose, sunken eyes, or no food for more "
                "than a week - and check the basking temperature and the UVB bulb first, because a "
                "cold reptile cannot digest.")
    if _off_food_said(line, _OFF_FOOD_BIRD):
        return ("Ring an avian vet today: a budgie or parrot hides illness until it is very thin, "
                "so a bird that has taken nothing for 24 hours is an emergency. Keep the cage warm "
                "and covered, put food and water where the bird is sitting rather than on the "
                "floor, and offer its usual food warm - not a new one it has never seen.")
    if _off_food_said(line, _OFF_FOOD_RODENT):
        return ("Ring the vet today: a hamster, rat or ferret that stops eating usually has a bad "
                "front tooth or an illness it has hidden, and 12 hours is already long for "
                "something that small. Look at the teeth, offer the food it likes best, warm, and "
                "keep it quiet and warm while you ring rather than waiting to see if it picks up.")
    if _off_food_said(line, _OFF_FOOD_RABBIT):
        return ("Ring the vet today, not tomorrow: 12 hours without food is an emergency for a "
                "rabbit or guinea pig, because the gut stops moving and will not restart on its "
                "own. Keep hay and water in front of it, offer warm strong-smelling food and gentle "
                "exercise, and do not wait to see if it picks up.")
    return ("Ring the vet today rather than waiting: anything small that has taken nothing for 24 "
            "hours is a vet visit, and a rabbit or guinea pig is an emergency at 12. Offer the food "
            "it likes best, warm and strong-smelling, somewhere quiet, and look for a cause you can "
            "see - a blocked nose, an overgrown tooth, a new food, a move, a new pet.")


# A cat losing fur is three questions in one family, and the whole family got "Noted: your cat is
# over grooming" or a shrug before this row: "my cat is shedding a lot" is the moult, "my cat has a
# bald patch" is the vet, and "my cat has stopped grooming" is a cat in pain rather than a brushing
# problem. One row reads the line so the first sentence is about what the person actually said.
_CAT_SHED = re.compile(r"\b(shed|sheds|shedding|moult|moulting|molting|blowing her coat|"
                       r"blowing his coat|fur everywhere|hair everywhere)\b")
_CAT_NOTWASH = re.compile(r"\b(not grooming|no longer grooming|stopped grooming|isnt grooming|"
                          r"isn't grooming|wont groom|won't groom|wont wash|won't wash|"
                          r"stopped washing|not cleaning herself|not cleaning himself)\b")
_CAT_SHED_REPLY = (
    "Shedding a lot with no bare skin showing is the moult, and it comes twice a year: brush her "
    "daily, more if her coat is long, and a rubber glove or a damp hand takes the loose hair off "
    "the furniture. If you can see skin, or she is licking a patch bald, that is a vet question.")
_CAT_NOTWASH_REPLY = (
    "A cat who stops washing herself is not a grooming problem but usually a painful one: bad "
    "teeth, arthritis, or weight that stops her reaching round, so have her seen rather than "
    "bathed. Cats keep themselves clean, so a greasy or scruffy coat is an early sign worth acting "
    "on. If she is over-grooming to bald skin instead, think fleas first.")
_CAT_BALD_REPLY = (
    "Bare or patchy skin is a vet question, not a brushing one: over-grooming is usually fleas or "
    "a flea allergy, then ringworm (a round scaly patch), stress, and an overactive thyroid in an "
    "older cat. Treat every pet in the house for fleas and hot-wash the bedding, and have a cat "
    "licking herself bald seen.")


def _cat_hair(memory, understood):
    text = ((understood or {}).get("clean") or "").lower()
    if _CAT_NOTWASH.search(text):
        return _CAT_NOTWASH_REPLY
    if _CAT_SHED.search(text):
        return _CAT_SHED_REPLY
    return _CAT_BALD_REPLY




ENTRIES.append(entry(
    "pet-off-food", (_OFF_FOOD, _OFF_FOOD_ASK),
    _off_food_reply,
    bias=3,
    # A pet that is eating fine, or eating the wrong thing, is the opposite line.
    avoid=("eating fine", "eating well", "eating ok", "eating again", "eating normally",
           "eating plenty", "still eating", "eating everything", "ate a", "ate my", "ate his",
           "ate her", "swallowed", "poison", "chocolate")))

# A cat that shrinks while eating is the vet's line, not a diet: thyroid, diabetes and teeth.
ENTRIES.append(entry(
    "cat-weight-loss",
    (("cat", "cats", "kitten", "kittens", "moggy"),
     ("losing weight", "lost weight", "weight loss", "getting thin", "grown thin", "gone thin",
      "too thin", "ribs", "bony", "skinny", "wasting away", "keeps shrinking")),
    # the same words as the diet question, so this row reads the direction as well: it is
    # _cat_weight, not the thin answer, or "how do i help my cat lose weight" gets the vet line
    _cat_weight,
    bias=2,
    # The direction of the question decides the row: a cat the person is trying to slim is
    # cat-weight, and this vet answer is for a cat that shrank on its own.
    # "i want to lose weight but my cat keeps waking me up" is the person's line
    avoid=_WAKING_AVOID + ("help my cat lose", "help him lose", "help her lose", "help me",
                           "how do i help", "how can i help", "make him lose", "make her lose",
                           "make my cat lose", "to lose weight", "needs to lose", "should lose",
                           "want to lose", "slim", "overweight", "too fat", "is fat",
                           "getting fat", "obese", "diet")))


# A fish at the surface is a water problem first, and a shopping list second.
ENTRIES.append(entry(
    "fish-at-top",
    (("fish", "goldfish", "aquarium", "tank"),
     ("floating", "floats", "at the top", "top of the tank", "surface", "gasping", "gulping",
      "upside down", "on its side")),
    ("A fish hanging at the top and gulping is short of oxygen, which is nearly always the water: "
     "test ammonia and nitrite with a liquid kit, change a quarter of the water with dechlorinated "
     "water at the same temperature, and add an air stone or point the filter outlet at the "
     "surface. Do not feed it for a day, and do not do a full clean - the bacteria in the filter "
     "are what is keeping it alive. A fish floating on its side or upside down is swim-bladder "
     "trouble or already dead, and either way it comes out of the tank."),
    bias=1,
    # Cleaning the tank or choosing one is another line.
    avoid=("clean", "cleaning", "how often", "how big", "size", "litres", "liters", "bowl")))


# A cat's weight and a matted coat are two of the most common cat questions and neither had an
# answer: the weight answer went to the human one ("fill half the plate with vegetables") and the
# coat got "Noted: your cat has matted fur".
ENTRIES.append(entry(
    "cat-weight",
    (("cat", "cats", "kitten", "kittens", "kitty"),
     ("overweight", "fat", "obese", "heavy", "too heavy", "putting on weight", "put on weight",
      "gained weight", "gaining weight", "lose weight", "losing weight", "weight", "diet",
      "dieting", "slim", "slimming", "kilos", "kg", "weigh", "weighing",
      # the going-thin words have to be in the key too, or the callable never reads the line
      "thin", "too thin", "getting thin", "gone thin", "skinny", "bony", "ribs",
      # and the ways people say a cat is too heavy without using the word
      "chubby", "slim down", "slimming down", "weighs too much", "too much weight",
      "cut down her food", "cut down his food")),
    _cat_weight,
    # a person's weight is the human answer, and a dog's or a rabbit's is their own food
    # question: this entry is the cat
    avoid=("i am", "im ", "my weight", "myself", "me to lose", "dog", "dogs", "puppy", "pup",
           "puppies", "rabbit", "rabbits", "hamster", "guinea pig", "horse", "baby", "kid",
           "child", "hedgehog") + _WAKING_AVOID))


ENTRIES.append(entry(
    "cat-hair-loss",
    (("cat", "cats", "kitten", "kittens", "kitty"),
     ("bald", "bald patch", "bald patches", "bald spots", "hair loss", "losing hair",
      "losing fur", "fur falling out", "coat falling out", "patchy", "patches", "thin coat",
      "over grooming", "overgrooming", "grooming herself bald", "grooming himself bald",
      "licking herself bald", "licking himself bald", "biting her fur", "biting his fur",
      "chewing her fur", "chewing his fur", "chewing at her fur", "chewing at his fur",
      "pulling her fur out", "pulling his fur out", "shedding", "sheds", "shed", "moulting",
      "molting", "moult", "falling out", "fur coming out", "hair coming out",
      "coat coming out", "cat is patchy", "fur is patchy", "hair is coming out",
      "fur is coming out", "coat is patchy", "going bald", "gone bald",
      "not grooming", "no longer grooming", "stopped grooming", "isnt grooming",
      "isn't grooming", "wont groom", "wont wash", "stopped washing", "not cleaning herself")),
    _cat_hair,
    # the coat, the carpet and the person's own hair are other rows
    avoid=("dog", "dogs", "puppy", "pup", "puppies", "rabbit", "rabbits", "hamster",
           "guinea pig", "horse", "carpet", "rug", "floor", "mat", "mats", "curtain",
           "sofa", "bed", "clothes", "cook", "cooking", "my hair", "the rug"),
    # every shape of the key that is not in the ask would score nothing, so the ask repeats it
    ask=("bald", "patch", "patchy", "patches", "spot", "spots", "hair", "fur", "coat",
         "skin", "shed", "sheds", "shedding", "grooming", "moult", "moulting", "losing",
         "falling", "coming", "going", "gone", "thin", "chewing", "pulling", "groom",
         "washed", "cleaning", "groomed"))),


# The person's dandruff answer is a medicated scalp shampoo, and it was answering "my cat has
# dandruff" and "my dog has dandruff" with it. A pet's flaky coat is food, fleas and over-bathing,
# and the word alone cannot tell the two apart, so the pet has to be named.
ENTRIES.append(entry("pet-dandruff",
          (("cat", "cats", "kitten", "kittens", "kitty", "dog", "dogs", "puppy", "puppies",
            "pup", "pet", "pets", "rabbit", "rabbits", "hamster", "guinea pig"),
           # "dry skin" stays with the itchy-dog row: dry skin alone is not flakes, and that
           # answer already covers fleas, mites and food
           ("dandruff", "flaky", "flakes", "flake", "scaly", "scurf", "scurfy", "white bits",
            "white flakes")),
          ("For a cat or a dog with dandruff, look at food, fleas and baths before a shampoo: a dry flaky coat is usually a cheap diet or winter air, and flea dirt looks like it until a damp tissue turns it red-brown. Brush weekly to lift the flakes, add an omega-3 or fish-oil supplement, and bathe no more than monthly with a pet shampoo. Thick greasy flakes, red or itchy skin, or flakes with hair loss is the vet's call - that is often a mite or a yeast."),
          # the person's own scalp is the shampoo card, and a pastry is not a pet
          avoid=("my hair", "my scalp", "my head", "my own", "i have", "i get", "human",
                 "baby", "cradle cap", "child", "children", "pastry", "pie", "fish", "chocolate",
                 "bread", "onion", "garlic", "grapes", "raisins", "xylitol"),
          # the feeding row keys cat + "flaky skin" loosely enough to tie, and a flaky coat is
          # not a portion question
          bias=2))

# --- the small habits people ask "why does she do that" about -----------------
# A cat's own questions read as curiosity rather than a problem, so they got the search hedge:
# "why does my cat knead me", "why does my cat headbutt me" and "why does my cat sit on my
# laptop" had no answer anywhere in the domain. The three readings are different behaviours, so
# the reply is a callable that opens with the one the line names.
_KNEAD_ASK = ("knead", "kneads", "kneading", "kneaded", "making biscuits", "make biscuits",
              "biscuits on me", "pummelling", "pummeling", "pummels", "padding my chest",
              "padding my lap", "patting my")
_HEADBUTT_ASK = ("headbutt", "headbutts", "headbutting", "head butt", "head butts",
                 "head butting", "bunting", "bunts", "butts his head", "butts her head",
                 "pushes his head", "pushes her head", "pushes its head", "nudges his head",
                 "nudges her head", "rubs his head", "rubs her head",
                 # the same bump said from the cat's side: "why does my cat rub its head on me"
                 # was a search hedge while the row read only "his" and "her"
                 "rubs its head", "rubbing its head", "rubs its face", "rubbing its face",
                 "head against my", "head on my", "head into my", "nudges me", "nudging me")
_ON_YOU_ASK = ("sit on my laptop", "sits on my laptop", "on my laptop", "sit on my chest",
               "sits on my chest", "on my keyboard", "on my book", "on my pillow",
               "follows me everywhere", "follows me around", "follows me to the",
               "wont leave me alone", "won t leave me alone", "wont leave me", "slow blink",
               "slow blinks", "blinks slowly")

_KNEAD_REPLY = (
    "Kneading is the one thing she never grew out of: a kitten pushes its paws on the mother to "
    "get the milk down, and an adult cat keeps the movement because it feels good. The paws have "
    "scent glands, so she is also putting her smell on you, and a cat only does it on something "
    "she is settled on. Trim her claws or slide a folded blanket under her - pushing her off "
    "teaches her nothing, and a little drooling or purring with it is normal.")
_HEADBUTT_REPLY = (
    "That is a compliment: the scent glands are on the head and cheeks, so a head bump is her "
    "putting her smell on you and marking you as safe and hers. Cats do it to the people they "
    "trust, and usually as a greeting or an ask, so offer a hand at nose height or bump her back "
    "gently and most cats take it as an answer.")
_ON_YOU_REPLY = (
    "She is after the warmth and the company, and a cat that wants to be where you are is a "
    "settled cat rather than a needy one; the laptop is warm and it is where your hands are. "
    "Put a blanket or a box on the desk beside you and reward her when she takes it, and she will "
    "usually choose that over the keyboard.")


# The key reads the phrasing, but the reply is chosen by the meaning, so the arms are patterns:
# "rub his head" and "rubs her head" are one behaviour, and "pushes her head into my hand" is a
# bump even though "push" belongs to the knock-things-off row in the key.
_KNEAD_SAID = re.compile(r"\bknead\w*|\bbiscuits\b|\bpummel\w*|\bpatting my\b")
_HEAD_SAID = re.compile(r"\bhead\s?butt\w*|\bbunt\w*|"
                        r"\b(?:butt|bump|nudg|rub|push|press)\w*\b[^.]{0,20}\bhead\b")


def _cat_habit(memory, understood):
    clean = " " + ((understood or {}).get("clean") or "").lower() + " "
    if _KNEAD_SAID.search(clean):
        return _KNEAD_REPLY
    if _HEAD_SAID.search(clean):
        return _HEADBUTT_REPLY
    return _ON_YOU_REPLY


ENTRIES.append(entry(
    "cat-habit",
    (("cat", "cats", "kitten", "kittens", "kitty", "moggy", "mog"),
     _KNEAD_ASK + _HEADBUTT_ASK + _ON_YOU_ASK),
    _cat_habit, bias=1,
    # A recipe kneads and bakes biscuits, a dog leans rather than kneads, and a person's own
    # habit is not the cat's question.
    avoid=("dough", "bread", "pastry", "recipe", "recipes", "bake", "baking", "baked", "oven",
           "flour", "yeast", "dog", "dogs", "puppy", "puppies", "rabbit", "hamster", "i knead",
           "i keep", "my back", "my neck", "shoulder", "massage", "muscle")))

# A rabbit on its own is the commonest mistake with them, and the person usually asks it as
# "is my rabbit lonely" rather than "how many rabbits": the hay answer carried the word "friend"
# but said nothing about the bonding, the neutering or how long it takes.
_RABBIT_ALONE_ASK = ("lonely", "alone", "on its own", "on her own", "on his own", "company",
                     "companion", "a friend", "friend for", "needs a friend", "need a friend",
                     "another rabbit", "second rabbit", "two rabbits", "bond", "bonding",
                     "bonded", "pair", "pairing", "single rabbit", "keep it with",
                     # "can i keep one guinea pig" is the same question as "is it lonely", and
                     # the housing answer it used to get says nothing about the second animal.
                     "keep one", "keep a single", "just one", "only one", "one on its own",
                     "single guinea pig", "alone all day", "left on its own")

# A rabbit and a guinea pig are the same question in the same words - "is my rabbit lonely",
# "do guinea pigs need a friend", "can i keep one" - and the answer is the same rule with a
# different animal in it. The row named rabbits only, so a guinea pig on its own was answered
# with the rabbit card or with nothing at all, and the guinea pig is the pet most often kept
# alone by mistake.
_SMALL_PET_ALONE = {
    "rabbit": (
        "Rabbits are herd animals, so one on its own is the exception: the best setup is a "
        "neutered pair in a hutch with a run attached, and a lone rabbit gets withdrawn, "
        "over-grooms and chews the bars. A few hours alone in the day is fine, a whole day and "
        "night with nobody in is not. Bonding needs neutral ground, two of everything - bowls, "
        "trays, hidey holes - and short meetings that build over a week or two, never one rabbit "
        "dropped into the other's hutch. Neuter both first, or they will fight and then breed."),
    "guinea pig": (
        "Guinea pigs are herd animals, so a single one is the exception: two sows, or a neutered "
        "boar with a sow, in a big cage or a hutch with a run, is the normal setup, and a guinea "
        "pig kept alone gets withdrawn and can stop eating. A few hours alone in the day is fine, "
        "a whole day and night with nobody in is not. Bond on neutral ground with two of "
        "everything and short meetings, and never drop a new one into the other's cage. A rabbit "
        "is not a substitute: they eat different food and a rabbit can injure a guinea pig."),
}


def _small_pet_alone(memory, understood):
    """The companion answer, in the animal the line names or the chat was last about."""
    return _SMALL_PET_ALONE[_the_small_pet(memory, understood)]


ENTRIES.append(entry(
    "small-pet-alone",
    (("rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs"), _RABBIT_ALONE_ASK),
    _small_pet_alone,
    # A pet that has died is pet-loss, and food, hay and housing are their own answers.
    avoid=("died", "dead", "dying", "passed away", "put down", "euthanised", "euthanized",
           "eat", "eats", "ate", "eating", "food", "hay", "hutch size", "how big", "run size",
           "hamster", "hamsters", "cat", "dog")))

# Hamsters chew bars in almost every cage people buy, so the question is the commonest thing
# said about them and it had nothing behind it: "my hamster is biting the bars" was read back as
# "Noted: your hamster is biting the bars."
_HAMSTER_BARS_ASK = ("bars", "bar", "chewing the bars", "chewing bars", "chews the bars",
                     "chew the bars", "bites the bars", "biting the bars", "cage bars",
                     "the cage", "cage", "wants out",
                     "wants to come out", "come out", "escaping", "escape", "escapes",
                     "climbing", "monkey barring", "chewing everything", "chews everything")

ENTRIES.append(entry(
    "hamster-bars",
    (("hamster", "hamsters"), _HAMSTER_BARS_ASK),
    ("Bar-chewing is usually a cage too small or bedding too shallow to dig in: a Syrian wants "
     "about 100 by 50 cm of floor, a 28 cm wheel it can run in with a straight back, and 15 cm of "
     "bedding, and a dwarf a little less. If the cage is big enough it is boredom, so add a sand "
     "bath, tubes and paper to shred, and swap the chews weekly. A bare patch on the nose, or "
     "chewing that runs for hours, is worth a vet check."),
    # A hamster that has died is pet-loss, its food and its cage's cleaning are other answers,
    # and a hamster that is out of its cage is the escape question, not the bar-chewing one.
    avoid=("died", "dead", "dying", "passed away", "put down", "euthanised", "euthanized",
           "eat", "eats", "ate", "eating", "food", "bedding change", "clean", "cleaning",
           "how often", "rabbit", "guinea pig", "cat", "dog",
           "got out", "get out", "getting out", "out of the cage", "out of its cage",
           "out of his cage", "out of her cage", "escaped", "escape", "escapes", "loose",
           "missing", "cant find", "can't find", "gone from")))
ENTRIES.append(entry(
    "cat-on-my-bed",
    # "my bed" is a phrase and so weighs a little more than the bare word: it is the difference
    # between "my cat wont get off my bed" reaching this row and the push-things row, which says
    # "off the" and comes first in the file. The cat itself is not a phrase here - "my cat keeps
    # fighting me" named no bed and was answered about one.
    (("bed", "beds", "pillow", "duvet", "bedroom", "my bed", "our bed"),
     ("cat", "cats", "kitten", "kitty", "moggy", "mog", "sleep", "sleeps", "sleeping", "slept",
      "on my bed", "in my bed", "keeps getting on", "wont get off", "won't get off")),
    ("Your bed is warm, soft and smells of you, which makes it the best place in the house as far "
     "as a cat is concerned. To move him, offer something warmer and closer than the floor - a "
     "heat pad or a folded blanket on a chair beside the bed - and shut the bedroom door for a few "
     "nights so the new spot is the only good one.",
     ),
    bias=1,
    # The animal has to be in the line, not in what the chat was about. "i keep reading it in
    # bed" after a sleepless night reached this row on the stored topic "sleep" plus the word
    # "bed", and a person with no cat was told to offer it a heat pad. Only the answer can name
    # a cat, so only a line that says cat can have it.
    ask=("cat", "cats", "kitten", "kittens", "kitty", "moggy", "mog", "tom cat", "tomcat",
         "tom", "tomcats"),
    # A bed that has broken is the bed's repair, not the cat's habit. The row's second group
    # used to hold a bare "my bed" beside the location phrases, so "my bed leg is broken" and
    # "my bed frame broke" were the cat card; the bare phrase is gone and a bed fault stands
    # the row down. "on my bed" and "in my bed" stay: "my cat sleeps in my bed at night" needs
    # them to beat the garden beds.
    # Washing the bed, and keeping a pet off a sofa or out of a room, are other lines.
    # "bedding" and "beds" carry the forms of "bed", so the phrase "on my bed" in the second group
    # matched "my bedding" and "my beds": a laundry line ("how often should i clean my bedding")
    # and a garden one ("how often should i water my beds") were each given the cat answer. The
    # fence is the sense, not the word - "bedding" itself cannot go in this list, because its
    # forms hold "bed" and it would stand this row down on every cat line.
    avoid=("how often", "how many times", "how frequently", "water", "watering", "watered",
           "clean", "cleaning", "wash", "washing", "stain", "smell", "flea", "fleas", "sofa",
           "settee", "couch", "crate", "buy", "buying", "which bed", "what bed", "size",
           # a cat weeing or pooing on the bed is asking about the toilet, not about warmth:
           # "my cat is peeing on the bed" was told to put a heat pad on a chair
           "wee", "wees", "weeing", "weed", "pee", "pees", "peeing", "peed", "poo", "poos",
           "pooing", "pooed", "poop", "urine", "spraying", "sprayed", "puddle", "puddles",
           "litter", "tray", "toilet",
           # the same behaviour asked about a dog is a dog question, and this reply says "cat"
           "dog", "dogs", "puppy", "pup", "puppies", "doggy", "labrador", "terrier", "spaniel",
           # a bed that has broken or hurts is the bed's repair, not the cat's habit
           "broken", "broke", "snapped", "snap", "cracked", "crack", "wobbly", "wobbles",
           "collapsed", "bed leg", "legs of the bed", "bed frame", "bed slat", "bed slats",
           "foot of the bed", "hurts", "aching", "sore",
           # what the cat carried onto the bed is the hunting answer's question, not warmth:
           # "my cat leaves dead mice on the bed" was told to offer a heat pad on a chair.
           # The prey names have to stand this row down; "on my bed" in the key cannot.
           "mouse", "mice", "rat", "rats", "vole", "voles", "bird", "birds", "prey",
           "bring", "brings", "bringing", "brought", "caught", "catches", "killed", "kills",
           "dead", "carcass", "hunting", "hunts")))

ENTRIES.append(entry(
    "dog-follows-me",
    (("follows me", "follow me", "following me", "follows him", "follows her", "following him",
      "following her", "wont leave me", "won't leave me", "never leaves me",
      "velcro dog", "always with me", "follows me everywhere", "everywhere i go"),
     ("dog", "dogs", "puppy", "pup", "puppies", "doggy", "labrador", "terrier", "spaniel")),
    ("Following you is company and routine: you are the whole of his social world, and he has "
     "learned the shape of your day, so he goes where the next thing happens. Give the habit "
     "somewhere to go - send him to his bed with something to chew while you move about. It is "
     "worth a vet visit only if it started suddenly or comes with panting, pacing and chewing, "
     "which is anxiety rather than affection.",
     ),
    bias=1,
    # Barking at the door, being left alone, pulling on the lead and chewing are other entries.
    avoid=("bark", "barks", "barking", "doorbell", "alone", "separation", "lead", "leash", "walk",
           "walks", "chew", "chewing", "pulling", "recall", "come back", "jumping", "begging",
           "stares", "staring", "stare")))

ENTRIES.append(entry(
    "dog-stares-at-me",
    (("stares at me", "staring at me", "stares at him", "stares at her", "staring at him",
      "staring at her", "stares at the wall", "staring at the wall", "watches me"),
     ("dog", "dogs", "puppy", "pup", "puppies", "doggy", "labrador", "terrier", "spaniel")),
    ("Staring is usually waiting on a cue, because you are the hand that opens the door and fills "
     "the bowl, so he watches it. Give the watching a job: send him to his bed and reward him for "
     "staying there. A hard stare with a stiff body, growling or the whites of the eyes showing is "
     "different - give him space and do not stare back.",
     ),
    bias=1,
    # Following, barking and growling at a stranger are other lines.
    avoid=("follows", "follow", "following", "bark", "barks", "barking", "growl", "growling",
           "snarl", "bite", "bites", "growls", "lead", "walk", "chew", "alone")))

ENTRIES.append(entry(
    "dog-rolls-in-poo",
    (("rolls in", "roll in", "rolling in", "rolled in", "rolls on", "rolls over it",
      "rubbing himself in", "rubbing herself in", "rubs himself in", "rubs herself in",
      # "dead bird" and "dead thing" are not this row: a dog that rolls in something dead is not
      # the dog that carries one in and leaves it on the mat - that card owns those words, and
      # this one was taking them off the word "dead" alone.
      "fox poo", "poo", "fox mess", "something smelly", "something dead", "dead fox"),
     ("dog", "dogs", "puppy", "pup", "puppies", "doggy", "terrier", "spaniel", "labrador")),
    ("Rolling in something dead or foul comes from the wolf side of the family: a strong smell "
     "masks your own scent and hides the hunter, and the habit stuck. There is nothing to "
     "discipline - he is not being defiant - so keep the lead short past fox runs, and wash him "
     "with dog shampoo and warm water rather than tomato juice, which only stains a pale coat.",
     ),
    bias=1,
    # Foxes in the garden, general dog poo in the house, and eating poo are other lines.
    avoid=("garden", "lawn", "bins", "bin", "rubbish", "litter", "eats poo", "eat poo",
           "eating poo", "his own poo", "cat poo", "in the house", "on the carpet", "stain",
           # NOT "foxes": the word folds onto "fox" and would stand this row down for its own
           # question. The garden's fox card is fenced from its own side instead.
           "clean", "cleaning", "why does he eat", "digging", "dug up")))

ENTRIES.append(entry(
    "dog-licks-me",
    (("licks me", "lick me", "licking me", "licks my feet", "licks my hands", "licks my face",
      "licks my toes", "licking my feet", "licks the air", "licking the air", "licks my legs"),
     ("dog", "dogs", "puppy", "pup", "puppies", "doggy", "terrier", "spaniel", "labrador")),
    ("Licking you is affection and taste: skin is salty, and licking hands and feet brings the "
     "salt with the closeness. Some dogs do it more when they are bored or asking for something, "
     "and most do it while settling down. It is harmless unless it is constant and new, which can "
     "mean an itchy skin or an upset stomach - look for scratching, paw-chewing or loose poo.",
     ),
    bias=1,
    # A dog licking his own paws is the itchy-paws line; licking the floor or furniture is not this.
    avoid=("paws", "paw", "scratching", "scratch", "itches", "itchy", "floor", "sofa", "carpet",
           "furniture", "cut", "wound", "sore", "lip", "nose", "ears", "gums", "after surgery")))

# The everyday things a pet owner asks that nothing above answered, kept in one block so the
# rows are easy to find and to extend.
ENTRIES.extend([

    # ---- the everyday things a pet owner asks that nothing above answered ----------------
    # "my dog has a runny tummy" was echoed back. diarrhoea sat in dog-vomiting, whose answer is
    # about a dog being sick; a loose tummy is a different run of advice, so it gets its own.
    # A cat and a rabbit are the two that must not skip a meal, so this row is theirs; a dog's
    # loose poo is `dog-vomiting`, which main already answers well.
    entry("pet-tummy", (("cat", "cats", "kitten", "kittens", "moggy", "rabbit", "rabbits",
                         "bunny", "bunnies", "guinea pig", "guinea pigs"),
                        ("runny tummy", "tummy upset", "upset tummy", "tummy trouble",
                         "bad tummy", "runny poo", "runny poop", "loose poo", "loose stools",
                         "watery poo", "soft poo", "the runs", "diarrhoea", "diarrhea",
                         "squits", "dodgy tummy")),
          _pet_tummy,
          # being sick on its own is dog-vomiting, and a worm or a poison is another answer
          avoid=("vomit", "vomiting", "sick", "throwing up", "threw up", "worm", "worms",
                 "poison", "chocolate", "grape", "raisin", "onion", "lily")),
    # A cat getting thin is the opposite question to a fat cat, and the honest answer is a vet
    # visit: the common causes are all treatable and all need a blood test.
    # A dog that slims down on the same food is a vet question, and the answer is not "feed him
    # more": a reviewer of this PR pointed out the gap (a cat had this answer, a dog only got a nod)
    entry("dog-weight-loss", (("dog", "dogs", "puppy", "pup", "bitch", "doggy") + DOG_BREEDS,
                              ("losing weight", "lost weight", "weight loss", "getting thin",
                               "getting skinny", "too thin", "skinny", "underweight", "bony",
                               "ribs showing", "ribs", "wasting away", "thin")),
          "A dog that loses weight on the same food needs the vet: worms, bad teeth, kidney or "
          "liver trouble, diabetes and an overactive thyroid are the usual causes, and some "
          "cancers start that way. Weigh him now, take the number with you, and go this week - a "
          "dog should not get thin on a full bowl.",
          # the fat dog, the cat, the food question and the person's own weight are other answers
          avoid=("overweight", "too fat", "is fat", "getting fat", "obese", "put on weight",
                 "putting on weight", "gaining", "gained", "diet", "slim", "slimming",
                 "how much should i feed", "what should i feed", "food", "feed", "feeding",
                 "help my dog lose", "help him lose", "help her lose", "make him lose",
                 "make her lose", "needs to lose", "need to lose", "to lose weight",
                 "lose a few", "slim him", "slim her", "my own", "myself",
                 "cat", "cats", "kitten", "rabbit", "hamster", "guinea pig")),
    # The other direction, for the same reason the cat has one: a dog whose ribs show is thin and
    # a dog with no waist is fat, and "how much should i feed him" is a third answer.
    entry("small-pet-overweight",
          (("rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs", "piggy",
            "piggies", "hamster", "hamsters", "gerbil", "gerbils", "chinchilla", "chinchillas",
            "horse", "horses", "pony", "ponies", "donkey", "donkeys", "shettie", "shetties"),
           ("overweight", "too fat", "is fat", "getting fat", "getting chubby", "obese",
            "put on weight", "putting on weight", "gaining weight", "gained weight",
            "needs to lose", "need to lose", "should lose", "slim", "slimming", "on a diet",
            "diet", "lose a bit", "laminitis", "weigh tape",
            # "how do i help my rabbit lose weight" was answered with the human diet card
            "lose weight", "losing weight", "lose some weight", "help it lose", "help him lose",
            "help her lose", "lose the weight", "slim down", "cut down", "cut back",
            "slimming down")),
          _small_pet_fat,
          # a dog and a cat have their own cards with their own numbers
          avoid=("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "kittens"),
          bias=1),
    entry("dog-overweight", (("dog", "dogs", "puppy", "pup", "bitch", "doggy") + DOG_BREEDS,
                             ("overweight", "too fat", "is fat", "getting fat", "obese",
                              "put on weight", "putting on weight", "gaining weight",
                              "gained weight", "needs to lose", "need to lose", "should lose",
                              "slim", "slimming", "on a diet",
                              # "how do i slim him down" and "how do i slim my dog down" are this
                              # question asked as a how-to, and the treat-lure card won them both
                              "slim him down", "slim her down", "slim my dog", "slim the dog",
                              "slim down", "lose a bit")),
          "Cut the treats first and weigh the day's food on a kitchen scale instead of guessing: a "
          "dog should lose about one to two per cent of its body weight a week, so a 20kg dog is "
          "about 200 to 400g. Fill part of the bowl with green beans or carrot, and add a walk "
          "rather than taking food away. Have the vet weigh him first, because an underactive "
          "thyroid and bad joints both look like greed and both need a different plan.",
          # the key says nothing about "weight" on its own, so a thin dog stays a thin dog:
          # "losing weight" and "lose weight" are one word to the reader, and the word alone
          # cannot tell the two directions apart
          avoid=("getting thin", "too thin", "skinny", "underweight", "bony", "ribs showing",
                 "wasting away", "how much should i feed", "what should i feed", "feed him",
                 "food for", "what can dogs eat", "can my dog eat", "dog food", "dog treats",
                 "cat", "cats", "kitten", "rabbit", "hamster", "guinea pig"),
          # "how do i slim my dog down" lost to the treat-lure card, which is keyed on "how do i"
          # as well: a dog with no waist is this row's question whatever the how-to sounds like
          bias=1),
    # Washing a dog's paws after a walk, which main shrugged at.
    entry("dog-paws-clean", (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet"),
                             ("clean his paws", "clean her paws", "clean my dogs paws",
                              "clean my dog's paws", "clean the paws", "clean paws",
                              "wash my dogs paws", "wash my dog's paws", "my dogs paws",
                              "my dog's paws",
                              "clean his feet", "clean her feet", "wash his paws",
                              "wash her paws", "wipe his paws", "wipe her paws",
                              "wipe the paws", "muddy paws", "muddy dog", "dirty paws",
                              "paws after a walk", "muddy feet",
                              "cleaning paws", "washing paws")),
          "A damp cloth and warm water is enough after a walk: wipe the pads and between the toes, "
          "then dry them properly, especially between the toes. Skip human shampoo, check for grit "
          "and grass seeds while you are there, and wash the towel rather than the dog if it is "
          "only mud.",
          avoid=("ear", "ears", "shower", "bath", "bathroom", "sink", "worktop", "oven", "floor",
                 "carpet", "tiles")),
    # "how much exercise does a cat need" was answered with the feeding line.
    # main grew a `pet-bored` row while this sat, which answers the play lines too; this one has
    # the exercise wording ("how much exercise does a cat need"), which was reaching the feeding
    # answer, so it keeps its place with the bias that wins the tie.
    entry("cat-exercise", (("cat", "cats", "kitten", "kittens", "moggy"),
                           ("exercise", "exercising", "play", "playing", "playtime", "play time",
                            "entertain", "entertainment", "enrichment", "bored", "boredom",
                            "how much exercise", "how often should i play")),
          "Two or three play sessions a day of ten to fifteen minutes each, with a wand toy that "
          "moves like a bird or a mouse, and finish each one with a small meal so the hunt ends in "
          "a catch. That is plenty for an indoor cat; a laser pointer should always end on "
          "something she can actually pounce on, or it leaves her wound up.",
          avoid=("feed", "feeding", "food", "diet", "portion", "much should i feed",
                 "litter", "scratch", "scratching", "dog", "puppy"), bias=1),
    # A hamster out of its cage was answered "Noted: your hamster escaped."
    entry("hamster-escaped", (("hamster", "hamsters", "gerbil", "gerbils", "guinea pig",
                               "guinea pigs", "mouse", "rat"),
                              ("escaped", "escape", "got out", "get out", "loose", "missing",
                               "ran away", "run away", "out of the cage", "out the cage",
                               "cant find", "can't find")),
          "Shut the door of the room, put the other pets out, and leave his food and water low "
          "down along the skirting, because they follow walls and come out at night. A bucket with "
          "a towel in the bottom and a little food in it catches most of them, and a torch along "
          "the edges of the fridge and under the sofa finds the rest; no poison and no traps. One "
          "out in daylight is usually thirsty, so offer water first.",
          avoid=("dog", "cat", "rabbit", "bird", "outside", "garden")),
    entry("pet-neuter", (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "kittens",
                          "rabbit", "rabbits", "bunny"),
                         ("neuter", "neutered", "neutering", "spay", "spayed", "spaying",
                          "castrate", "castrated", "castration", "the snip",
                          "get him done", "get her done")),
          # the operation itself has to be named: "how much should i feed my puppy" also has a
          # "should i" in it, and bare "should i" made this the answer to half the pet lines
          _pet_neuter, ask=("neuter", "neutering", "spay", "spaying", "castrate",
                            "castration", "the snip", "get him done", "get her done"),
          # "when should i get my dog done" is the neutering line; "when should i walk my dog" is
          # not, so the operation words in ask= do that work. A person's own operation is not this.
          # The statement forms - "my cat is spayed", "hes neutered" - used to be avoided here,
          # because the card answers the date of the operation. They are answered by the card's
          # own "already done" reply now, which reads the normalised line, so a typo'd "hes
          # neutered" and a written "he is neutered" reach the same answer.
          avoid=("myself", "me", "i am having", "i'm having", "hysterectomy", "vasectomy",
                 "my son", "my daughter", "my husband", "my wife", "my partner"),
          # a small pet's neutering price is asked with the same words as its buying price, and
          # the buying-price row has a bias, so this row has to win the tie: "how much does it
          # cost to spay a rabbit" was getting a dog and cat price with no rabbit in it
          bias=2),
    # A cat's eye runs for the same two reasons a person's does, and the wait-and-see is the
    # wrong advice: a squinting cat is in pain and an ulcer gets worse in a day.
    # A hard swollen belly in a dog is bloat until a vet says otherwise, and the answer people
    # get today is an echo. Say the thing that kills: go now.
    entry("dog-bloat", (("dog", "dogs", "puppy", "pup", "labrador", "retriever", "setter",
                         "shepherd", "boxer", "great dane", "greyhound", "pointer", "weimaraner"),
                        ("swollen belly", "hard belly", "swollen stomach", "hard stomach",
                         # a line that splits the phrase ("belly is swollen and hard") has to
                         # score something, so the bare words are here too; ask= keeps it to
                         # belly/stomach/tummy and avoid= keeps paws, legs and faces out
                         "swollen", "hard",
                         "bloated", "bloat", "bloating", "distended", "tummy looks big",
                         "belly is big", "belly looks big", "tight belly", "retching",
                         "trying to be sick", "unproductive", "heaving", "dry heaving")),
          ("Treat a hard, swollen belly in a dog as an emergency: ring the vet and go now, tonight "
           "if that is when it starts. If he is also retching or trying to be sick and nothing "
           "comes up, restless, drooling or his gums look pale, that is bloat (GDV), and the "
           "stomach can twist - it kills within hours and waiting to see if he settles is what "
           "people regret. Do not feed him, do not wait for morning, and phone ahead so the "
           "practice is ready."), bias=2,
          # a swollen paw, a fat dog and a wormy kitten are their own questions
          avoid=("paw", "paws", "leg", "joint", "face", "eye", "ear", "weight", "fat",
                 "overweight", "worm", "worms", "pregnant", "pregnancy", "ate", "eaten",
                 "chocolate", "grapes", "raisins", "onion"),
          ask=("belly", "stomach", "tummy", "bloat", "bloated", "distended", "retching",
               "heaving")),
    # "how do i look after a puppy", "puppy advice" and "how do i look after a dog" had no
    # answer at all: the puppy went to the vet greeting and the dog to a shrug, while the kit
    # list and the night crying had rows of their own. The care question is the routine, so the
    # reply is the day, the jabs and the legal bits, in that order.
    entry("looking-after-a-dog",
          (("dog", "dogs", "puppy", "puppies", "pup", "pups", "puppy dog"),
           ("look after", "looking after", "care for", "caring for", "care of", "advice",
            "routine", "day to day", "daily", "what do i need to know", "how do i start",
            "first dog", "first puppy", "new to dogs", "responsible", "keep it healthy",
            "keep him healthy", "keep her healthy")),
          ("The day is the whole job: a short walk first thing, a proper one later, a last five "
           "minutes before bed, a garden break after every meal, and food twice a day for an adult "
           "or three or four small meals for a puppy. Then the boring parts that keep him well - "
           "a microchip (law in the UK), a yearly check and booster at the vet, worming every three "
           "months and flea treatment monthly, and insurance taken out before anything is wrong "
           "with him. A dog should not be left more than about four hours a day, and the chewing "
           "and barking that people call naughty is usually a dog with nothing to do."),
           bias=1,
           # the kit list, the price, the night crying, the walks, the jabs and every behaviour
           # question have their own rows, and each of them is the better answer
           avoid=("what do i need", "buy", "kit", "checklist", "cost", "price", "much does",
                  # a dog left behind while the person goes away is the boarding question:
                  # "who looks after my dog when i go away" lost its boarding card to this row.
                  "go away", "goes away", "going away", "while im away", "while i'm away",
                  "while i am away", "when im away", "when i'm away", "when we go away",
                  "boarding", "kennel", "kennels", "away",
                  "insurance cost", "rescue", "rehome", "adopt", "breeder", "pedigree",
                  "name", "call him", "call her", "breed", "which breed", "best breed",
                  "bark", "barks", "barking", "howl", "chew", "chews", "chewing", "bite",
                  "bites", "biting", "nip", "nipping", "mouthing", "jump", "jumping",
                  "pull", "pulling", "recall", "come back", "walk", "walks", "how long",
                  "how far", "how much exercise", "minutes", "miles", "toilet", "house train",
                  "house training", "crate", "sleep", "night", "cries", "crying", "whine",
                  "whining", "sick", "ill", "vomit", "diarrhoea", "limp", "scratch",
                  "fleas", "worms", "worming", "jab", "jabs", "vaccination", "vaccinations",
                  "neutering", "neuter", "spay", "season", "heat", "pregnant", "food",
                  "feed", "feeding", "diet", "treats", "puppy pads", "lead", "collar",
                  "harness", "muzzle", "alone", "separation", "car", "travel", "holiday",
                  "kennel", "grooming", "bath", "nail", "teeth", "breath", "hot", "heatwave",
                  "weather", "cold", "paddling", "swim", "park", "other dogs", "aggressive",
                  "growl", "resource", "guard", "cat", "cats", "kitten", "rabbit", "hamster",
                  "puppy farm", "age", "old dog", "senior")),
    # The same question about a cat or a kitten: "how do i look after a kitten" was going to the
    # vet greeting, and the kit list and the litter tray had rows of their own.
    entry("looking-after-a-cat",
          (("cat", "cats", "kitten", "kittens", "kitty", "moggy", "mog"),
           ("look after", "looking after", "care for", "caring for", "care of", "advice",
            "routine", "day to day", "daily", "what do i need to know", "how do i start",
            "first cat", "first kitten", "new to cats", "keep it healthy", "keep him healthy",
            "keep her healthy")),
          ("A cat is mostly a routine it can rely on: two meals at the same times, water in a bowl "
           "away from the food, a litter tray scooped every day and washed out with plain hot water "
           "once a week, and somewhere high to sit. Play with a wand toy for ten minutes twice a "
           "day, because a cat that hunts indoors does not hunt the sofa. Then the vet side: a "
           "microchip (law in the UK), a yearly check and booster, worming and flea treatment "
           "monthly, and neutering at about four to six months. Indoors-only is fine if there is "
           "space to climb, and a kitten should stay in until the vaccinations are finished."),
           bias=1,
           # the kit list, the litter tray trouble, the night crying, the scratching, the food
           # and every behaviour question have their own rows
           avoid=("what do i need", "buy", "kit", "checklist", "cost", "price", "much does",
                  "go away", "goes away", "going away", "while im away", "while i'm away",
                  "while i am away", "when im away", "when i'm away", "when we go away", "away",
                  "rescue", "rehome", "adopt", "breeder", "pedigree", "name", "call him",
                  "call her", "breed", "which breed", "scratch", "scratching", "sofa",
                  "litter tray smell", "smelly litter", "wee", "peeing", "spraying", "spray",
                  "bite", "bites", "biting", "hiss", "growl", "night", "cries", "crying",
                  "meowing", "meowing at night", "wont use", "not using", "outside", "outdoor",
                  "indoor", "garden", "hunting", "birds", "sick", "ill", "vomit", "hairball",
                  "hairballs", "worms", "fleas", "jab", "jabs", "vaccination", "vaccinations",
                  "neutering", "neuter", "spay", "pregnant", "kittens due", "food", "feed",
                  "feeding", "diet", "treats", "alone", "separation", "car", "travel",
                  "holiday", "cattery", "grooming", "brush", "fur", "teeth", "breath",
                  "hot", "heatwave", "weather", "cold", "other cats", "aggressive", "fight",
                  "fighting", "new baby", "dog", "dogs", "puppy", "puppies", "rabbit",
                  "hamster", "senior", "old cat", "age")),
])

# =====================================================================================
# A pet that scratches. The word "scratch" belonged to two rows that do not answer a
# pet: the cut-sting fact ("why does my dog scratch the floor" was told that a cut
# stings because nerve endings are exposed) and the furniture repair ("how do i stop my
# cat scratching the furniture" was told to rub a walnut along the grain). An animal
# scratching something is a behaviour question, and what it means depends on what is
# being scratched: a door, the floor, the furniture, or the animal's own skin.
# =====================================================================================
_PET_SCRATCH_ASK = ("scratch", "scratches", "scratching", "scratched", "scratcher",
                    "claw", "claws", "clawing", "clawed")


def _scratching_what(understood):
    """The thing being scratched: "door", "floor", "furniture" or "skin", else ""."""
    words = [str(word).lower() for word in (understood.get("words") or ())]
    text = " ".join(words)
    for keys, what in (
            (("door", "doors", "back door", "front door", "bedroom door", "gate"), "door"),
            (("floor", "floors", "carpet", "carpets", "rug", "rugs", "bedding", "bed",
              "blanket", "cushion", "cushions", "mat", "mattress"), "floor"),
            (("sofa", "sofas", "settee", "couch", "armchair", "chair", "chairs", "curtain",
              "curtains", "furniture", "table", "tables", "woodwork", "wallpaper", "wall"),
             "furniture"),
            (("himself", "herself", "themselves", "skin", "raw", "sore", "itchy", "itching",
              "scratching", "so much", "all the time", "constantly", "bleeding", "bald",
              "patch", "patches"), "skin")):
        for key in keys:
            if key in words or key in text:
                return what
    return ""


_PET_SCRATCHING = {
    "door": (
        "A pet that scratches the door wants through, so the scratching is the way it has "
        "learned to ask. Do not open it while the paw is on the door: wait for a pause of a "
        "few seconds, then open it, and it learns the pause is what works. Hanging a bell on "
        "the door and teaching a touch of the nose to it gives a cat a quieter way to ask, and "
        "a dog with a shut door between him and you usually wants company more than the room: "
        "put his bed on the side of the door you are on, and leave the door open once he is "
        "settled."),
    "floor": (
        "Scratching the floor or the bedding before lying down is normal: dogs and cats turn and "
        "scrape to flatten a spot and leave their scent, and it is not a fault. It is worth "
        "answering if it is new or constant: give him a soft bed of his own so he has something "
        "to turn round in, check the room is not too warm, and if a dog is scraping hard at hard "
        "flooring his claws may be catching, so have them clipped. A cat that scrapes at the "
        "carpet by the door is marking, and a mat or a vertical post in that spot takes the "
        "behaviour."),
    "furniture": (
        "Put a tall scratching post right beside the corner she uses and make the sofa less "
        "appealing with a throw or double-sided tape for a few weeks: cats scratch to mark "
        "territory and to shed the outer claw, so the post has to be tall enough to stretch up "
        "and steady enough not to wobble. A dog scratching at the sofa or the cushions is usually "
        "digging up a nest, so give him a blanket to scrabble at and a walk before the evening, "
        "and if it is one spot in particular put something solid in front of it."),
    "furniture-dog": (
        "A dog scrabbling at the sofa or the cushions is usually digging itself a nest, so give "
        "him a blanket or an old duvet of his own to scrabble at and a walk before the evening. "
        "If it is one spot he keeps going at, put something solid in front of it for a fortnight "
        "and praise him when he uses his own bed instead. Chewing the furniture is a different "
        "problem with a different answer, so say if that is what is happening."),
    "skin": (
        "A pet scratching itself sore is a skin question, not a behaviour one: fleas are the "
        "first thing to rule out, then a food or pollen allergy, and a cat over-grooming a bald "
        "patch can be mites or stress. Have the vet look before the skin is broken, because an "
        "open scratch gets infected. In the meantime a flea treatment from the vet rather than "
        "the supermarket, no shampoo unless the vet names one, and a cone if he will not leave a "
        "wound alone."),
    "": (
        "Give them something that is theirs to scratch and put it where they already do it: a "
        "tall, steady post for a cat, and a blanket or a bit of matting for a dog. Cats scratch "
        "to mark and to shed claw, so a post beside the sofa stops the sofa being the spot, and "
        "a dog scraping at the floor or the bedding before lying down is just making a nest. "
        "Clipped claws and a walk before the evening take the rest of it, and scratching that "
        "has suddenly become constant, or is leaving the skin raw, is the vet's."),
}


_DOG_WORDS = ("dog", "dogs", "puppy", "pup", "bitch", "lab", "labrador", "terrier", "collie",
              "spaniel", "retriever", "poodle", "beagle", "boxer", "husky", "shepherd")


def _pet_scratching(understood):
    what = _scratching_what(understood)
    words = [str(word).lower() for word in (understood.get("words") or ())]
    if what == "furniture" and any(word in _DOG_WORDS for word in words):
        return _PET_SCRATCHING["furniture-dog"]
    return _PET_SCRATCHING[what]


ENTRIES.append(entry(
    "pet-scratching",
    (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "kittens", "pet", "pets",
      "rabbit", "hamster", "guinea pig"),
     _PET_SCRATCH_ASK + ("the floor", "the carpet", "the door", "the sofa", "the furniture",
                         "himself", "herself", "so much")),
    lambda memory, understood: _pet_scratching(understood),
    # a bark is not a scratch: "how do i stop my dog barking at the door" named a dog and a
    # door, and this row (bias 3) beat the barking answer
    bias=3,
    # a person's own cut or a scratch from a pet is a wound question, not a behaviour one;
    # and a scratch on the table is a repair, which home.py answers; a claw that wants cutting
    # is the claws row, which this row was beating on entry order ("how do i clip my cat's
    # claws" is two ordinary words each and a tie, and this row carries the higher bias)
    avoid=("clip", "clipping", "clipped", "clippers", "trim", "trimming", "trimmed",
           # a bark is not a scratch: "how do i stop my dog barking at the door" named a dog and
           # a door, and this row's bias beat the barking answer
           "bark", "barks", "barking", "barked", "yap", "yaps", "yapping", "howl", "howls",
           "howling", "meow", "meows", "meowing", "miaow", "noise", "noisy",
           # "how do i cut my cats claws" was the empty fallback below ("give them something
           # that is theirs to scratch"), because only the clip and trim words were held out
           "cut", "cutting", "to cut",
           "treat", "treating", "clean it", "wash it", "washed it", "infected", "infection",
           "tetanus", "antiseptic", "plaster", "bandage", "swollen", "red", "weeping",
           "scratched me", "scratch me", "scratches me", "scratched my hand", "scratched my arm",
           "scratched my face", "scratched my leg", "clawed me", "bit me", "bitten",
           # digging is its own answer (dog-dig): a dog digging at the floor is not a dog
           # scratching at it, and the reason is different
           "dig", "digs", "digging", "dug", "hole", "holes", "lawn",
           # and a noise at the door is not a paw on it: "how do i get my dog to stop barking at
           # the door" was given the door-scratching card, because "the door" is a key here.
           # Dog-bark owns every one of these lines.
           "bark", "barks", "barking", "howl", "howls", "howling", "yap", "yaps",
           "yapping", "whine", "whines", "whining", "growl", "growls", "growling",
           "meow", "meows", "meowing", "miaow", "miaows",
           # a cat being sick or a puppy weeing on the carpet is not a scratching question,
           # though the line says "carpet": those rows answer it
           "sick", "sicked", "vomit", "vomiting", "vomited", "throwing up", "threw up",
           "poo", "pooed", "pooing", "pee", "peed", "peeing", "wee", "weeing", "toilet",
           "litter", "diarrhoea",
           # and a shopping line that names a scratching post is asking what to buy
           "scratching post", "cardboard", "buy", "buying", "need", "should i get",
           "which one", "kit",
           # a nail trim is the grooming row's answer
           "nail", "nails", "trim", "trimming", "clippers", "clip his", "clip her",
           # getting the hair off the sofa is housework, not behaviour: the line names a
           # surface and "off", and the pet-hair row answers it. Without this the sofa word
           # carried "how do i get cat hair off a sofa" to the scratching post
           "hair", "hairs", "fur", "pet hair", "dog hair", "cat hair", "furball", "furballs",
           "lint", "hoover", "vacuum", "vacuuming", "brush off", "sticky roller",
           # chewing is its own answer, and an ear that smells or shakes is the vet's
           "chew", "chews", "chewing", "chewed", "gnaw", "gnawing", "biting the furniture",
           "ear", "ears", "head shaking", "shakes his head", "shaking her head",
           # a mark that is already there is the repair question, not the habit question. The
           # tense cannot say which: an avoid phrase is read with loose forms, so "scratched the
           # table" also holds out "scratching the table". The repair rows win that tie on their
           # own bias, and only the phrase "scratch marks" is held out here.
           "scratch marks", "scratch in the finish", "get scratches out",
           # a how-to-say-it line is a conversation: "how do i tell my friend her cat scratched
           # my child" is about the friendship, not about the cat's furniture habit
           ) + _SAYING_FRAME,
    # The ask is the scratch words alone. "stop", "keeps" and "why" are in every behaviour
    # question, so with them here a dog barking at the door met "dog" and "the door" and was
    # answered with the scratching-the-door advice.
    ask=_PET_SCRATCH_ASK))

# A door is the way out, not the furniture. The cat row keys the cat and the verb and carries the
# higher bias, so "my cat scratches the door at night" was told to buy a tall scratching post
# beside the corner she uses. The door words are added here rather than in that row's own `avoid`
# list: the list is under constant edit and this is one shape, said once.
for _item in ENTRIES:
    if _item.id == "cat-scratching":
        _item.avoid = _item.avoid + (
            "door", "doors", "back door", "front door", "bedroom door", "door frame")

# A scratch from an animal is a small wound with one specific worry, cat scratch disease, and
# the first thing to do is wash it under running water rather than hunt for a post.
ENTRIES.append(entry(
    "animal-scratch",
    (("cat", "cats", "kitten", "dog", "dogs", "puppy", "pet", "rabbit", "hamster", "horse"),
     ("scratch", "scratched", "scratches", "scratching", "claw", "clawed", "claws", "bite",
      "bitten", "bit")),
    ("Wash it under running water for five minutes with soap, pat it dry and cover it with a "
     "plaster, and do not use antiseptic or alcohol on it. Cat scratches are the ones that "
     "matter: watch for swelling, a red line spreading up the arm, swollen glands or a fever "
     "over the next two weeks, and see a GP if any of those appear. Get a tetanus booster if "
     "yours is out of date, and see a doctor the same day for a bite that has broken the skin on "
     "the hand, a deep puncture, or a scratch near the eye."),
    bias=4,
    avoid=("sofa", "sofa bed", "table", "tables", "door", "floor", "carpet", "furniture",
           "wallpaper", "scratching post", "scratching the", "scratches the", "he scratches",
           "she scratches", "himself", "herself",
           # a kitten that keeps biting a hand is a habit question, not a wound: a present-tense
           # bite with "keeps" or "play" in the line is the behaviour row's, and this one was
           # answering "my new kitten is biting me" with wash it under the tap.
           "keeps biting", "keeps biting me", "keeps biting my", "keeps scratching me",
           "keeps scratching my", "biting my hand", "biting my hands", "biting my fingers",
           "bites my hand", "bites my hands", "bites my fingers", "play biting", "play bites",
           "playful biting", "nip", "nips", "nipping", "teething",
           # the present tense is the habit too: "my new kitten is biting me" is what a new owner
           # writes, and a past bite ("my cat bit me") stays the wound question.
           "biting me", "bites me", "is biting", "biting my", "bites my", "is scratching",
           # a nail trim is the grooming row's answer, not a wound: "how do i trim my dogs
           # claws" was being told to wash it under the tap
           "nail", "nails", "trim", "trimming", "clip", "clipping", "clipped", "groom",
           "grooming",
           # and the same conversation frame: "how do i tell my friend her dog bit my son" is
           # how to say it, not what to do about the bite
           # teeth that keep landing on a hand are a habit to train out, not a wound: "my puppy
           # keeps biting my hands" was told to wash it under the tap and watch for a red line.
           # Only the shapes that say it happens again and again step aside - "my cat scratched
           # me" and "my dog bit my hand and it is bleeding" are wounds, and keep this card.
           # Main grew its own list of the same shapes; both are kept, because a phrase only one
           # of them names would otherwise fall back to the wash-it answer.
           # a line that asks how to stop it is the training question, whatever the tense:
           # "how do i stop a puppy biting" was told to wash it under the tap and watch for a red
           # line, while "the same line with my in it was the behaviour row's. The phrases name
           # the animal, so "how do i stop the bleeding from a dog bite" keeps this card.
           "how do i stop a puppy", "how do i stop the puppy", "how do i stop my puppy",
           "how do i stop a dog", "how do i stop the dog", "how do i stop my dog",
           "how do i stop a kitten", "how do i stop the kitten", "how do i stop my kitten",
           "how do i stop a cat", "how do i stop the cat", "how do i stop my cat",
           "stop it biting", "stop the biting", "stop a puppy biting", "stop puppy biting",
           "stop the puppy biting", "biting habit", "biting problem", "biting stage",
           "keep biting", "kept biting", "keeps mouthing", "keeps chewing", "keeps nipping",
           "always biting", "always nipping", "always mouthing", "constantly biting",
           "constantly nipping", "wont stop biting", "won't stop biting", "wont stop nipping",
           "won't stop nipping", "mouthing", "playbiting", "biting at my",
           # a puppy being taught manners is training, not a scratch to dress: this row was
           # answering "how do i train a puppy not to bite" with the wash-it advice for a bite
           # that has broken the skin. `dog-mouthing` owns the training line. These belong to
           # this row only - in the shared frame they also stood down the cat-biting row, whose
           # own key is the bite it was being told to stand aside for.
           "train", "training", "teach", "teaching", "not to bite", "stop biting",
           "stop the biting") + _SAYING_FRAME,
    ask=("treat", "clean", "wash", "washed", "infected", "infection", "tetanus", "plaster",
         "bleeding", "swollen",
         # A body part on its own is not a wound: "my puppy bites my hands" and "my puppy keeps
         # biting me" are the mouthing row's, and both were told to wash it under running water
         # and check their tetanus. A body part *and* a wound word still comes here, and so does
         # a bite that has already happened.
         "bit me", "bitten", "broke the skin", "broken the skin",
         "puncture", "look at it", "checked", "get it checked",
         # "should i see a doctor for a dog bite" is a wound question with a doctor in it, and
         # with the question frames gone from this list it fell to the training row's answer
         "doctor", "gp", "a and e", "a&e", "hospital", "antibiotics", "stitches",
         # "dog bite first aid" names the thing to do rather than the wound, and with the habit
         # rows standing down it was left with no ask word at all and got "A dog. What's it like
         # to live with?" - the first aid is what the card is.
         "first aid",
         # The bite said as a noun is the wound: "a dog bite", where "my dog bites" is the
         # habit. Only the article makes the difference, so only the article is here.
         "a dog bite", "a cat bite", "a puppy bite")))


# --- the animal hurt a person who is not the one typing ----------------------
# "the cat scratched the baby" was answered with the scratching post by the sofa, "the cat bit the
# baby" with the rod toy, "my dog bit the baby" with the training plan, and "the fox bit the baby"
# with the baby-food card: every row that reads a bite keys on the animal and the verb, and none of
# them reads the person in the object slot. The person who was hurt is what this row is for, so the
# object is the whole reading - and a line where the animal is the object ("the baby scratched the
# cat") is not this row's.
_HURT_PERSON = frozenset((
    "baby", "babies", "toddler", "child", "children", "kid", "kids", "son", "daughter", "boy",
    "girl", "mum", "mom", "mother", "dad", "father", "wife", "husband", "partner", "sister",
    "brother", "grandad", "grandma", "grandparent", "granny", "nan", "niece", "nephew", "cousin",
    "flatmate", "housemate", "postman", "postwoman", "postie", "delivery", "courier", "neighbour",
    "neighbor", "visitor", "visitors", "guest", "guests", "stranger", "strangers", "passer",
    "customer", "paperboy", "cleaner", "carer", "colleague", "friend", "someone", "somebody",
    "anyone"))
_HURT_VERBS = frozenset(("bit", "bite", "bites", "bitten", "scratched", "scratches", "scratching",
                         "clawed", "stung", "stings", "nipped", "attacked", "went"))
_HURT_PASSIVE = re.compile(r"\b(?:was|were|got|gets|has|had|been)\s+"
                           r"(?:bit|bitten|scratched|clawed|stung|nipped|attacked)\b")


def _a_person_was_hurt(understood):
    """True when a person other than the speaker is the one bitten, scratched or stung."""
    words = [str(word).lower() for word in (understood.get("words") or ())]
    for at, word in enumerate(words):
        if word in _HURT_VERBS:
            # the object comes after the verb, with only articles and names in between
            if any(near in _HURT_PERSON for near in words[at + 1:at + 5]):
                return True
    # the same thing said the other way round: "my son was bitten by our dog"
    if _HURT_PASSIVE.search(" " + " ".join(words) + " "):
        return any(word in _HURT_PERSON for word in words)
    return False


# Whoever was hurt, the wound comes first. The reporting half is not the same person: a bite on a
# stranger is a report to the police and a dog kept away from people until there is a plan, and a
# bite on a child of the house is the same report with the behaviourist after it.
_HURT_WOUND = ("Wash it under running water for five minutes with soap, pat it dry and cover it "
               "with a plaster, and skip the antiseptic on it. Get it seen the same day if the "
               "skin is broken - dog and cat bites on a hand, a foot or a face are the ones that "
               "get infected, and a child's face is where a dog bite most often lands. ")
_HURT_OWN_HOME = ("If the animal is yours, have the vet look it over even once - pain, a bad ear "
                  "or failing eyesight is often behind a first bite - and keep it out of the room "
                  "while the wound is being cleaned up. Check your tetanus is up to date, and "
                  "watch a cat scratch for a red line up the arm, swollen glands or a fever over "
                  "the next two weeks.")
_HURT_STRANGER = frozenset(("postman", "postwoman", "postie", "delivery", "courier", "neighbour",
                            "neighbor", "visitor", "visitors", "guest", "guests", "stranger",
                            "strangers", "passer", "customer", "paperboy", "cleaner", "carer",
                            "colleague", "friend", "someone", "somebody", "anyone"))


# The report is a dog's: in the UK a dog that injures someone is a criminal matter and the owner
# can be liable, and the same sentence for a cat scratch would be wrong twice over. A cat, a fox or
# a rabbit that breaks the skin wants the same-day look and the tetanus, not the police.
_HURT_ANOTHER_ANIMAL = ("A bite or a scratch from any animal that has broken the skin wants a "
                        "doctor's look the same day, and check the tetanus is up to date. Keep the "
                        "animal out of the room while the wound is being cleaned up, and watch a "
                        "cat scratch for a red line up the arm, swollen glands or a fever over the "
                        "next two weeks.")
_DOG_WORDS = frozenset(("dog", "dogs", "puppy", "puppies", "pup", "pups"))


def _the_person_hurt(memory, understood):
    """The wound care, and then the half that belongs to the person who was hurt."""
    words = {str(word).lower() for word in (understood.get("words") or ())}
    if words & set(BITE_CHILD_WORDS):
        if words & _DOG_WORDS:
            return _HURT_WOUND + BITE_REPORT_CHILD
        return _HURT_WOUND + _HURT_ANOTHER_ANIMAL
    if words & _DOG_WORDS:
        if words & _HURT_STRANGER:
            return _HURT_WOUND + BITE_REPORT
        return _HURT_WOUND + _HURT_OWN_HOME
    return _HURT_WOUND + _HURT_ANOTHER_ANIMAL


ENTRIES.append(entry(
    "animal-hurt-a-person",
    (("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies", "pup", "rabbit",
      "hamster", "horse", "pony", "parrot", "budgie", "gerbil", "ferret", "rat", "fox", "goat",
      "sheep", "snake", "lizard", "tortoise", "pet", "pets", "animal", "animals"),
     ("bit", "bite", "bites", "bitten", "scratched", "scratches", "scratching", "clawed",
      "stung", "stings", "attacked", "nipped", "went for")),
    _the_person_hurt,
    guard=_a_person_was_hurt,
    # the person typing is another row's question, and so is the animal doing it again and again:
    # this row exists for the third person in the sentence
    avoid=("sofa", "furniture", "carpet", "scratching post", "my hand", "my arm", "my leg",
           "my foot", "my finger", "my ankle", "my face", "bites me", "bit me", "scratched me",
           "keeps biting", "keeps scratching", "teething", "play biting",
           # what to say to the other parent is a conversation, not a wound
           "how do i tell", "how do i say", "should i tell", "say to", "tell her", "tell him"),
    bias=6))


# --- the small pet doing an odd thing ----------------------------------------
# "my hamster chews the bars", "my rabbit thumps at night", "my cat kneads me" and "my parrot
# plucks its feathers" were all answered with the echo - "Noted: your hamster chews the bars" -
# which is what the bot says when it has heard a fact rather than a question. Each one is an
# everyday thing a pet does, and the person is asking whether it is normal and what to do, so
# each gets the animal's own answer. The animal names the row: a thump is a rabbit's, and a
# budgie that screams is not a parrot that plucks.

ENTRIES.append(entry(
    "rabbit-thump",
    (("rabbit", "rabbits", "bunny", "bunnies"),
     ("thumps", "thumping", "thump", "stamps", "stamping", "stomps", "stomping",
      "bangs its feet", "banging its feet", "feet")),
    ("A rabbit thumping a hind foot is a warning, not a problem: it has heard something new, and "
     "it does it most at dawn and dusk when a rabbit would be out feeding. Look for a fox or a cat "
     "outside the hutch and give it a covered box to bolt into; a rabbit that also stops eating or "
     "sits hunched up needs the vet."),
    avoid=("teeth", "chew", "chewing", "fur", "hair", "litter", "poop", "droppings")))

ENTRIES.append(entry(
    "bird-noise",
    (("budgie", "budgies", "parrot", "parrots", "cockatiel", "cockatiels", "parakeet",
      "parakeets", "bird", "birds"),
     ("screeches", "screeching", "screams", "screaming", "squawks", "squawking", "noisy",
      "noise", "loud", "shouting", "shouts")),
    ("A budgie or parrot screeches for company, so answer it, let it out for an hour or two a day, "
     "and put the cage where the family is rather than in a quiet room. Cover the cage at dusk and "
     "keep to the same time each night, because a bird that screams at the same hour every evening "
     "is usually asking for the cover. Screaming with ruffled feathers or changed droppings is a "
     "vet question."),
    avoid=("pluck", "plucking", "feathers", "clip", "clipping", "wings", "wing")))

ENTRIES.append(entry(
    "parrot-plucks",
    (("parrot", "parrots", "budgie", "budgies", "cockatiel", "cockatiels", "parakeet",
      "parakeets", "bird", "birds"),
     ("plucks", "plucking", "plucked", "pulls its feathers", "pulling its feathers",
      "feathers", "bald", "bald patch", "bare patch", "over-grooms", "overgrooms")),
    ("Plucking is usually health or boredom, so have a bird vet see it first: mites, a diet of "
     "seed alone and a liver problem all cause it. If it is well, the fix is out-of-cage time, "
     "company, things to shred, a bath, and ten to twelve hours of sleep in a covered cage."),
    # clipping a bird's wings is a different question, and so is the moult
    avoid=("clip", "clipping", "wings", "wing trim", "moult", "molting", "moulting")))

# A dog that has been in a pond is two questions at once - is he all right now, and is the water
# he just drank going to make him ill - and on main the line reached three cards that fit neither:
# "my dog fell in the pond" answered "A dog - is it good company?", "my dog fell in the pond what
# do i do" reached the drowning card meant for a person ("start CPR"), and "my puppy fell in the
# water" got the how-much-should-a-dog-drink figures. Water is the key, and the animal has to be
# named, because a child who has fallen in a pond is the safety card's line and not this one.
ENTRIES.append(entry(
    "pet-fell-in-water",
    (("dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens", "rabbit",
      "rabbits", "hamster", "guinea pig", "horse", "pony", "puppy dog"),
     # "water" on its own is not the key: a dog's bowl is topped up, cleaned and emptied with
     # that word, and "how often should i change my dogs water" and "my dog wont go near the
     # water" both came to this card asking nothing about a dog that had been in it. The water
     # has to be somewhere (a pond, a river, a lake) or the animal has to have gone in it.
     ("pond", "ponds", "canal", "canals", "river", "rivers", "lake", "lakes",
      "stream", "streams", "sea", "reservoir", "dyke", "ditch", "swam", "swum", "swimming",
      "in the water", "in water", "water he drank", "drank the water", "drinking the water",
      "fell in", "fallen in", "jumped in", "jumps in", "went in the", "in the pond",
      "in the water", "in the canal", "in the river", "in the lake", "in the sea")),
    ("Rinse the pond water off with a hose and dry him, especially between the toes, then keep him "
     "warm and quiet for the rest of the day. Either way keep him out of the water and do not let "
     "him drink from it: ponds and slow rivers "
     "carry leptospirosis from rats' urine, which is why the annual jab matters, and a pond with a "
     "green scum on it in summer is blue-green algae, which is an emergency - ring the vet at once "
     "and do not wait for a sign. Watch for coughing, fast or noisy breathing or a wobble over the "
     "next few hours, because that is water in the lungs and needs the vet that day."),
    # the dog's drinking figures, the hot-weather card and the pond in the garden are other rows,
    # and a person in the water is the safety lane's line, not this one
    avoid=("how much water", "how much should he drink", "drink enough", "water intake",
           "how often", "change the water", "change his water", "change her water",
           "change my dogs water", "clean the water", "clean his water", "clean her water",
           "empty the water", "top up", "top up the water", "go near", "wont go near",
           "won't go near", "water bowl", "fresh water", "water fountain", "hot weather",
           "heat", "hot day",
           "garden pond", "build a pond", "built a pond", "build the pond", "dug a pond",
           "dig a pond", "digging a pond", "wants a pond", "want a pond", "made a pond",
           "new pond", "wildlife pond", "pond liner", "pond in the garden", "ponds in the garden",
           "has a pond", "have a pond", "got a pond", "the pond is", "pond is green",
           "clean the pond", "clean out the pond", "empty the pond", "fill the pond",
           "cover the pond", "net the pond", "pond pump", "pond filter", "fish", "goldfish",
           "bath", "in the bath", "bath water", "shower", "paddling pool", "splash pool",
           # a sink, a bin, a bucket and a washing machine hold no pond water, and the
           # leptospirosis and algae warnings are for water the animal swam in: "my guinea pig fell
           # in the sink", "my hamster fell in the toilet", "my cat fell in the washing machine"
           # and "my dog fell in the bin" all reached this card off the bare "fell in"
           "sink", "basin", "bin", "bins", "bucket", "box", "toilet", "loo", "washing machine",
           "tumble dryer", "dishwasher", "sink full",
           # "my dog is scared of water" is the confidence card, not a dog that has been in it
           "scared", "scared of water", "afraid", "terrified", "frightened", "nervous",
           "hates water", "hates the water", "wont go in", "won't go in", "doesnt like water",
           "doesn't like water", "refuses to go in", "wont get in",
           "kayak", "boat", "swim", "swims", "swim in", "holiday", "beach"),
    ask=("pond", "water", "canal", "river", "lake", "stream", "sea", "reservoir", "dyke",
         "ditch", "fell", "fallen", "jumped", "jumps", "went in", "swam", "swum"),
    bias=2))

# An animal named inside a smell has not been in the water. "my washing machine smells like a wet
# dog" and "the machine smells of wet dog" both carry a dog and the word wet, so the soak card
# below answered them - "towel him dry right through ... a rabbit, guinea pig or hamster loses
# heat fast" - when the machine was the thing that needed the answer, and it was on `0f78b40`
# getting the service-wash card. A comparison is what makes the difference: the animal after
# "like" or "of" is what something smells of, not the animal that is soaked. Only a smell, a
# comparison and an animal after it together stand the row down, so "my cat fell in the sink and
# smells of soap" keeps the drying, and a line that says the animal is wet keeps it too.
_SMELL_WORDS = ("smell", "stinks", "stank", "reeks", "pong")
_SMELL_OF_AN_ANIMAL = re.compile(
    r"\b(?:" + "|".join(_SMELL_WORDS) + r")\w*\b[^.?!]{0,30}?\b(?:like|of)\b"
    r"[^.?!]{0,20}?\b(?:dog|dogs|puppy|pup|cat|cats|kitten|rabbit|hamster|guinea pig|budgie"
    r"|parrot|ferret|animal|pet)\b")


def _a_smell_is_not_a_soaking(understood):
    """"it smells like a wet dog" describes a smell, so no animal has been in the water."""
    return not _SMELL_OF_AN_ANIMAL.search(_said(understood))


# A machine, sink or bin is where an animal gets soaked, and it is also where its hair collects,
# so the place alone does not say which question it is. "my washing machine is full of dog hair"
# matched on the dog and the machine and was told to towel a soaked guinea pig dry. The hair,
# fur and lint words name the cleaning question, and a soaking has a wet or a fall in it.
_THE_COAT_THE_MACHINE_IS_FULL_OF = re.compile(
    r"\b(?:hair|hairs|fur|furball|furballs|lint|fluff|moult\w*|molting|shedding|sheds)\b")
_A_SOAKING = re.compile(
    r"\b(?:soak\w*|sopping|saturated|drenched|wet|wetter|fell|fallen|falling|jumped|jumps|"
    r"jumping|went in|goes in|swam|swum|swimming|splashed|shiver\w*|towel\w*|"
    r"dry (?:him|her|it|them)|drying (?:him|her|it|them))\b")


# A machine, a sink or a bin is also just *where* a pet is, and a dog that shakes when the washing
# machine goes on has not been in it. The card is about drying a soaked animal, so the line has to
# say the animal got wet or went in.
_AN_ANIMAL_IN_THE_WATER = re.compile(
    r"\b(?:fell|fallen|jumped|jumps|dropped|went through|gone through|in the|inside the"
    r"|soaked|soaking|sopping|drenched|wet through|got wet|swam|swim)\b")


def _the_animal_got_wet(understood):
    said = _said(understood)
    return bool(_AN_ANIMAL_IN_THE_WATER.search(said) or _A_SOAKING.search(said))


def _a_soaking_is_not_a_smell_or_a_hair(understood):
    """True unless the line is a smell of an animal, or a coat the machine is full of.

    The two faults share a shape: an animal and a place with water in it, and the card about
    drying a soaked pet. The smell is about what something smells of (`_a_smell_is_not_a_soaking`).
    The hair is about the cleaning: a machine, a drum or a filter full of dog hair has not had a
    dog in it, and the answer is the hair card, not the drying one. A line with a wet or a fall
    in it keeps the row, so "my cat fell in the sink and smells of soap" still gets the drying.
    """
    said = _said(understood)
    if _SMELL_OF_AN_ANIMAL.search(said):
        return False
    return not (_THE_COAT_THE_MACHINE_IS_FULL_OF.search(said) and not _A_SOAKING.search(said))


# A soaking is not a pond. Once the water-borne disease text stands down for a sink, a bin or a
# washing machine, the line was left with an echo: "my guinea pig fell in the sink" answered
# "Thanks for telling me - I'm here if you want to dig into any of that." What a soaked animal
# needs is the drying, and a small pet is the one that suffers, so that is this card. The wash
# cycle is the other half: a cat that went through one can look untouched and still be injured.
ENTRIES.append(entry(
    "pet-soaked",
    (("dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens", "rabbit",
      "rabbits", "hamster", "guinea pig", "guinea pigs", "budgie", "parrot", "ferret"),
     ("sink", "sink full", "basin", "toilet", "loo", "bin", "bins", "wheelie bin", "bucket",
      "washing machine", "tumble dryer", "dishwasher",
      "soaked", "soaking", "sopping", "drenched", "wet through", "got wet", "fell in the",
      "in the washing machine", "in the sink", "in the toilet", "in the bin")),
    ("Towel him dry right through, not just the top, then keep him somewhere warm for an hour: a "
     "soaked coat loses heat fast, and a small pet suffers most of all - a rabbit, guinea pig or "
     "hamster chills quickly, and a hutch or cage that got wet needs the bedding changed too. If "
     "the water had soap, detergent or bleach in it, rinse "
     "it off with clean water before you dry him, because a cat or a small pet that licks its "
     "coat clean will swallow it. A pet that went through a wash or a dry cycle needs the vet "
     "even if it looks fine, and so does one that keeps shivering, goes quiet and floppy, or is "
     "breathing fast - those are the signs the wet has got inside him."),
    # the pond, river and sea lines are the card above, and a bath, a shower and a puddle are
    # their own answers; mud is the paws card, and a weather question is the cold card
    avoid=("pond", "canal", "river", "lake", "stream", "sea", "reservoir", "dyke", "ditch",
           "bath", "in the bath", "bath water", "shower", "paddling pool", "puddle", "puddles",
           "rain", "walk", "walks", "walking", "paws", "muddy", "mud", "garden", "outside",
           "swim", "swims", "swimming", "beach", "hot tub", "water bowl", "drinking water",
           "how much water", "snow", "frosty", "wind"),
    ask=("sink", "toilet", "bin", "bucket", "washing machine", "dishwasher", "tumble dryer",
         "soaked", "soaking", "wet", "fell", "drenched"),
    # the machine that smells of wet dog is the laundry card's question, not this one
    # a machine, a sink or a bin is where an animal can be and get soaked: the drying card needs
    # the line to say the animal got wet, or "the dog shakes when the washing machine goes on"
    # is told to towel a pet that is dry
    guard=_a_soaking_is_not_a_smell_or_a_hair and _the_animal_got_wet,
    bias=2))

ENTRIES.append(entry("pet-sick-again", _PET_SICK_AGAIN, _pet_sick_again, bias=6,
                          # only for the pets talk, never for the same words about a person
                          guard=_this_is_the_pets_talk,
                          # a journey is the travel-sickness card, and a pet that is being sick
                          # in the car keeps it
                          avoid=("car", "cars", "travel", "journey", "journeys", "drive",
                                 "driving", "motion", "ferry", "boat")
                          # who it is about. A person's line is never this row's, and the row
                          # must not even be reached for one: standing down at the last moment
                          # (a reply that returns None) hands the turn to the chat module and
                          # loses the answer the person would otherwise have had.
                          + _A_PERSON + _NOT_A_CAT_OR_DOG))


# --- a pet in a rented home ------------------------------------------------
# "my landlord said pets are fine as long as no damage" was answered with the deposit-deduction
# letter and "my tenancy says no pets" with "Got it. Is there anything you'd like a hand with?".
# Nothing in the knowledge base owned the permission question: the pet rows are care rows and the
# money rows are about getting a deposit back, so both halves of the line were read and neither
# answered it.
_PET_RENT = ("tenancy", "tenancy agreement", "tenancy says", "my lease", "the lease",
             "landlord", "landlady", "letting agent", "rented flat", "rented house", "renting",
             "housing association", "council flat", "no pets", "pet clause", "pet deposit",
             "pet rent")

_PET_ALLOWED = ("pets", "pet", "a cat", "a kitten", "a dog", "a puppy", "a rabbit",
                "keep a cat", "keep a dog", "keep pets", "get a cat", "get a dog",
                "have a cat", "have a dog", "have a pet", "pets are fine", "pets are allowed",
                "pets are ok", "allowed", "am i allowed",
                "can i keep", "can we keep", "can i get", "permission", "consent")

ENTRIES.append(entry(
    "pets-in-a-rented-home", (_PET_RENT, _PET_ALLOWED),
    "Ask in writing before you get the animal, because a tenancy that says no pets is a term you "
    "can ask to have changed but not one you can ignore: put the animal in the letter - the kind, "
    "its age, that it is house-trained and insured - offer to have the carpets cleaned when you "
    "leave and to put right anything it damages, and ask for a written answer. A landlord can say "
    "no, but in England a blanket ban with no way to ask is the kind of term consumer law lets "
    "you challenge, so a reasoned refusal in writing is worth having before you take it further. "
    "A separate pet deposit or pet rent on top of the normal five weeks is not something they can "
    "charge you. If they refuse for no reason, the council's tenancy relations officer or Shelter "
    "will tell you where you stand, and getting the animal anyway is a breach that can start an "
    "eviction.",
    # a poorly pet, a puppy's food and a cat that will not use the tray are the care rows, and the
    # deposit coming back is the money row
    avoid=("barking", "barks", "litter", "litter tray", "food", "feed", "feeding", "vet",
           "insurance quote", "neutered", "neutering", "worming", "flea", "fleas", "vaccine",
           "vaccinations", "training", "walk", "walks", "cat flap", "scratching", "sick",
           "vomiting", "diarrhoea", "limping", "breed", "breeder", "how much does")))
# The small pets are strict herbivores with a gut that has to keep moving: bread, toast and
# pastry are the everyday "he ate mine" question for a guinea pig or a rabbit, and the loaf's own
# mould card was answering it, so "my guinea pig has eaten the bread" was told to bin the loaf.
ENTRIES.append(entry(
    "guinea-pig-ate-bread",
    (("guinea pig", "guinea pigs", "guineapig", "guinea", "rabbit", "rabbits", "bunny",
      "hamster", "hamsters", "degus", "chinchilla"),
     # Only the food itself: the verbs ("ate", "chewed", "nibbled") are a form of each other
     # and reached "how do i get my rabbit to eat hay" and "my hamster chews the bars", which
     # are their own answers. A line about bread says bread.
     ("bread", "toast", "crust", "pastry", "cake", "biscuit", "cracker", "crumpet",
      "scone", "cookie", "bun", "muffin", "pizza", "chips", "cereal")),
    ("A nibble of plain bread will not poison a rabbit or a guinea pig, but bread is not food "
     "for one: it swells in a gut that cannot cope with it and can start the bloat and the "
     "not-eating that kill small pets quickly. Take the rest away, make sure hay and water are "
     "there, and watch for six hours for a tight belly, no droppings or sitting hunched, which is "
     "the vet today. Never give mouldy bread, and dough is an emergency."),
    # pet-ate-some is written for a dog's stomach and scores the same 4 on a rabbit that has
    # eaten toast: the small-pet gut answer goes first
    bias=3,
    # an animal that has escaped is a different card, even though it "got" something
    ask=("bread", "toast", "crust", "pastry", "cake", "biscuit", "cracker", "crumpet",
         "scone", "cookie", "bun", "muffin", "pizza", "chips", "cereal"),
    avoid=("got out", "escaped", "escape", "loose", "missing", "lost", "gone", "cage",
           "hutch", "run away", "ran away")))


# A pet that chews the cables is a question about the house, not about the animal's teeth: the
# rabbit row answered "how do i stop my house rabbit chewing wires" with hay and a wooden block,
# and before that the winding-instructions row for headphones had it, because "wires" and "stop"
# are its own words. The cable is the part a person can move.
# A pet that has already bitten through a live cable may be in trouble now, and prevention is the
# wrong reply for that line: "my rabbit chewed the wire and is shaking" needs the power off and the
# vet, not trunking. The state words and a bite on a live cable lead; everything else gets the
# prevention card.
_PET_SHOCKED = re.compile(
    r"\b(shaking|trembling|fitting|seizure|seizures|twitching|limp|limping|collapsed|collapse"
    r"|burnt|burn|burns|blistered|unconscious|passed out|not moving|dead|died|drooling|wobbly"
    r"|weak|breathing fast|smell of burning)\b")
_PET_CHEWED = re.compile(r"\b(chewed|bitten|bit|ate|eaten|gnawed|nibbled|through)\b")
_PET_LIVE = re.compile(r"\b(live|plugged in|plugged|switched on|mains|socket)\b")


def _pet_cable(memory, understood):
    """The cable card, with the after-a-bite half in front when the bite has already happened."""
    text = " " + re.sub(r"[^a-z0-9' ]+", " ", str((understood or {}).get("clean") or "").lower()) + " "
    shocked = bool(_PET_SHOCKED.search(text))
    bitten_live = bool(_PET_CHEWED.search(text)) and bool(_PET_LIVE.search(text))
    if shocked or bitten_live:
        return ("Switch the power off at the wall before you touch it, then ring the vet now: a bite "
                "through a live cable can stop the heart, and a burnt mouth swells over the next "
                "hour. Do not pull the cable out of its mouth and do not give it food or water. "
                "Afterwards, put the cable out of reach - plastic trunking along the skirting, a "
                "socket cover on the plug, cables behind furniture - and give it a chew toy where "
                "the chewing happened.")
    return ("Put the cable out of reach instead of trusting training: plastic trunking or a cable "
            "cover along the skirting, clipped to the wall, a socket cover on the plug, and cables "
            "behind furniture rather than across the floor. Then give the chewing somewhere to go "
            "- a chew toy or a stuffed Kong for a dog, a catnip toy for a cat, hay and a wooden "
            "block for a rabbit - and dab a bitter pet spray on the cable for a week. A pet that "
            "has bitten through a live cable needs the vet, and a chewed plug needs replacing, "
            "not taping up.")


ENTRIES.append(entry("pet-chews-cables",
          (("cable", "cables", "wire", "wires", "charger", "chargers", "flex",
            "extension lead", "extension leads", "phone charger", "laptop charger"),
           # "bit" and "bitten" are the past tense everybody uses with a pet ("my puppy bit the
           # charger", "my rabbit bit the cable and is shaking"), and the key had only the present
           # forms while the vet half's own regex has all three: the most natural line for the
           # worst case scored nothing and fell to the cat-biting or the chewing habit row.
           ("chew", "chews", "chewed", "chewing", "bite", "bites", "biting", "bit", "bitten",
            "gnaw", "gnawing",
            "nibble", "nibbles", "nibbling", "ate", "eaten", "protect", "hide", "cover",
            "safe", "dangerous", "hazard",
            # "how do i keep my puppy away from cables" asks the same thing and had no key word
            # at all, so it reached the vet line
            "keep", "keep away", "away from", "stop")),
          _pet_cable,
          # a tie with `cat-chews-things` is the plastic card, and the cable card is the one that
          # names the electrical danger, so this row wins the tie.
          bias=2,
          # the winding, the tidy desk, a broken charger and the animal's own chewing habit are
          # four other answers, and the dog's chewing row already knows the puppy half. A wire coat
          # hanger is something swallowed, and barbed wire is the field's problem, not a cable.
          avoid=("headphones", "earphones", "earbuds", "airpods", "tangle", "tangles", "tangled",
                 "knot", "knots", "coil", "coils", "wind", "wrap", "desk", "tidy", "clutter",
                 "organise", "organize", "not working", "stopped working", "broken",
                 "furniture", "sofa", "skirting board", "shoes", "slippers", "hands",
                 "coat hanger", "hangers", "barbed wire", "wire wool", "chicken wire",
                 "wire brush", "guitar"),
          # and the animal has to be in the line: this is pet-proofing advice, and a cable
          # question with no pet in it ("my cable is frayed is it safe", "how do i hide cables on
          # a wall") was being told to put the cable out of reach of an animal it does not have
          ask=("dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens", "rabbit",
               "rabbits", "bunny", "bunnies", "hamster", "hamsters", "gerbil", "gerbils",
               "guinea pig", "guinea pigs", "pet", "pets", "parrot", "parrots", "bird", "birds",
               "tortoise", "ferret", "ferrets", "chinchilla")))

# "is a raw food diet ok for dogs" and "should i feed my dog raw food" reached the cold-takeaway
# complaint card, which keys `raw` and `food`. Raw feeding is a common question and the honest
# answer is a set of trade-offs, not a verdict.
ENTRIES.append(entry("dog-raw-diet",
                     (("raw food", "raw diet", "raw feeding", "raw meat", "barf diet",
                       "raw food diet", "feed raw", "feeding raw", "fed raw"),
                      ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets",
                       "ok", "okay", "safe", "better", "good", "should i", "can i", "is it",
                       "worth it", "healthy", "right", "how")),
                     # Two sentences, not a comma-run with an "or" in it: the composer reads a
                     # comma-run as a menu of options, and "you pick" after this reply offered
                     # "it carries more bacteria than cooked food" as a choice.
                     "It can be done well and it is not automatically better. A raw diet has to be "
                     "properly balanced; minced meat on its own is short of calcium, it carries "
                     "more bacteria than cooked food, and a puppy needs the right ratio of calcium "
                     "to phosphorus for its bones to grow right. If you want to try it, use a "
                     "complete raw brand rather than supermarket mince, keep it frozen until the "
                     "day, wash hands, bowls and the worktop afterwards, and don't feed raw bones "
                     "to a gulper. Vets disagree about it, so ask yours about your own dog.",
                     bias=3,
                     # a fussy dog and a dog that is off its food are different rows
                     avoid=("dog food", "brand", "which food", "fussy", "not eating", "wont eat",
                            "won't eat", "stopped eating", "sick", "vomit", "diarrhoea",
                            "is it safe to eat", "restaurant", "takeaway", "chicken", "rice")))
# A pet that shivers, a horse that goes lame, a horse that stops eating or drinking, and a dog or
# rabbit in moult: four everyday lines that had no answer on main at all. "my dog is shivering",
# "my whippet is shivering", "my greyhound is shivering", "my horse is shivering", "my horse is
# lame", "my horse is not eating", "my horse is not drinking", "my dog is moulting" and "my rabbit
# is moulting" were the listening line or a shrug. The fear rows keep "shaking" and "trembling" - a
# frightened pet has its own card - so these read the shiver itself, and the horse and the coat
# each get the question they actually are.
_SHIVER = ("shivering", "shivers", "shiver", "shivering all over", "shivering and shaking",
           "trembling all over", "shaking all over", "quivering")
_THIN_COAT = ("whippet", "whippets", "greyhound", "greyhounds", "lurcher", "lurchers",
              "saluki", "salukis", "italian greyhound", "italian greyhounds", "deerhound",
              "borzoi", "dachshund", "dachshunds", "chihuahua", "chihuahuas")
_HORSE = ("horse", "horses", "pony", "ponies", "foal", "foals", "cob", "cobs", "mare", "mares",
          "stallion", "stallions", "gelding", "geldings", "yearling", "yearlings", "shettie",
          "shetties")
_PET_FOR_SHIVER = ("dog", "dogs", "puppy", "pup", "puppies", "cat", "cats", "kitten",
                   "kittens", "pet", "pets", "rabbit", "rabbits", "hamster", "hamsters",
                   "guinea pig", "guinea pigs")


def _pet_shivers(understood):
    text = ((understood or {}).get("clean") or "").lower()
    if _a_word_in(text, _HORSE):
        return ("A horse that shivers is cold, in pain or tying up, so rug it, give it hay and "
                "water and take its temperature: ring the vet today if it is sweating, stiff behind "
                "or unwilling to move, because tying-up needs a vet and a blood test rather than a "
                "walk round the field to loosen it off.")
    if _a_word_in(text, _THIN_COAT):
        return ("A thin-coated dog like a whippet or a greyhound shivers from cold before anything "
                "else, so a coat indoors, a bed off the floor and a coat for winter walks are what "
                "settle it. If it is shivering in a warm room, tucked up and off its food, that is "
                "pain or a fever and it wants the vet today.")
    return ("Shivering in a warm room is pain or a fever rather than cold: feel the ears and the "
            "belly, and a pet that is tucked up, hot or off its food wants the vet today. A small "
            "or thin-coated one can simply be cold, which a coat and a bed off the floor fix, and a "
            "pet shivering after a fright settles once it has somewhere to hide.")


def _horse_lame(understood):
    text = ((understood or {}).get("clean") or "").lower()
    foot = _a_word_in(text, ("hoof", "hooves", "foot", "feet", "foot sole", "sole"))
    if foot:
        return ("A lame horse is a vet out today: keep it in on a deep clean bed with hay and "
                "water, and do not ride it or trot it up for anyone, because an abscess in the hoof "
                "and laminitis both get worse with movement. Tell the vet which foot it is, whether "
                "the hoof feels hot and whether it will put weight on it at all.")
    return ("A horse that goes lame wants the vet today rather than a wait and see: an abscess in "
            "the hoof or laminitis is what it usually is, and both get worse if it is walked on. "
            "Keep it in on a deep bed with hay and water, don't ride it, and tell the vet which leg "
            "it is and whether it will put weight on it.")


def _horse_off_food(understood):
    text = ((understood or {}).get("clean") or "").lower()
    eating = _a_word_in(text, ("eating", "eat", "eats", "eaten", "food", "feed", "hay", "feed")
                        )
    if eating:
        return ("A horse that stops eating is a colic until the vet says otherwise, so ring them now "
                "rather than waiting for the morning. Keep it walking gently if it wants to roll, "
                "take the hard feed away, leave water and hay in reach, and tell the vet how long it "
                "has been, whether there are droppings and whether it has a temperature.")
    return ("Check the water first, because a frozen, dirty or new trough is the commonest reason a "
            "horse stops drinking: fresh warm water in a clean bucket, and a pinch of salt in the "
            "feed, often settles it. A horse that still will not drink by the next morning, or that "
            "is off its hay as well, is a vet call - colic starts that way.")


def _pet_moult(understood):
    text = ((understood or {}).get("clean") or "").lower()
    if _a_word_in(text, ("rabbit", "rabbits", "bunny", "bunnies")):
        return ("A rabbit in moult needs brushing every day, and twice a day at the peak, because "
                "the fur it swallows is what can block the gut: keep the hay coming and watch the "
                "droppings. Bare patches, or skin that is sore or scurfy, are the vet rather than "
                "the moult.")
    return ("A dog blowing its coat twice a year is normal: brush it daily while it lasts, more if "
            "the coat is long, and a rubber glove or a damp hand takes the loose hair off the "
            "furniture. Bare skin, bald patches or constant scratching is a skin question for the "
            "vet rather than the moult.")


# A pet that shivers: the fear rows own "shaking" and "trembling", so this reads the shiver.
ENTRIES.append(entry("pet-shivering", (_PET_FOR_SHIVER + _HORSE + _THIN_COAT, _SHIVER),
                     lambda memory, understood: _pet_shivers(understood), bias=1,
                     # a person who is shivering, and a shiver that names a fear, are other answers
                     avoid=("i am shivering", "im shivering", "i'm shivering",
                            "shivering with cold", "shivering with fear", "fireworks", "thunder",
                            "scared", "frightened", "afraid", "my hands", "my legs")))

ENTRIES.append(entry("horse-lame", (_HORSE,
                                    ("lame", "lameness", "limping", "limps", "limp",
                                     "wont walk", "won't walk", "not walking", "foot sore",
                                     "footsore", "hoof", "hooves", "hobbling", "going lame",
                                     "gone lame", "lame on", "stiff on")),
                     lambda memory, understood: _horse_lame(understood), bias=1))

ENTRIES.append(entry("horse-off-food", (_HORSE,
                                        ("not eating", "isnt eating", "isn't eating", "wont eat",
                                         "won't eat", "stopped eating", "off his food",
                                         "off her food", "not drinking", "isnt drinking",
                                         "isn't drinking", "wont drink", "won't drink",
                                         "stopped drinking", "no droppings", "not pooing",
                                         "colic", "rolling")),
                     lambda memory, understood: _horse_off_food(understood), bias=1))

# Snoring: "my dog is snoring" and "my pug is snoring a lot" were the listening line, and the shape
# of the face is what the answer hangs on. A gasping line is the vet tonight and stays with the
# breathing card in crisis_replies, so the words here are the snore itself.
_FLAT_FACE = ("pug", "pugs", "bulldog", "bulldogs", "french bulldog", "english bulldog",
              "boston terrier", "shih tzu", "shih-tzu", "boxer", "boxers", "pekingese", "pekinese",
              "persian", "persians", "cavalier", "cavaliers", "staffordshire", "mastiff")


def _pet_snoring(understood):
    text = ((understood or {}).get("clean") or "").lower()
    if _a_word_in(text, _FLAT_FACE):
        return ("Snoring in a flat-faced dog or cat is the shape of the face: the soft palate and the "
                "narrowed nostrils vibrate, and every extra kilo makes it worse, so keep the weight "
                "down and ask the vet about the airway at the next check. Ring them sooner if it "
                "stops breathing for a few seconds and wakes with a snort, if the gums look blue, or "
                "if it cannot settle at all at night - that is when an operation is talked about.")
    return ("Snoring in a dog or cat is usually weight and position: keep the weight down and let it "
            "sleep with the head a little raised, and a squashed-up sleeper often snores less on a "
            "flat bed than on a piled one. It is worth the vet if it has started suddenly, if it "
            "stops breathing for a few seconds and wakes with a snort, or if the animal is sleepy "
            "all day.")


ENTRIES.append(entry("pet-snoring", (("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten",
                                      "pet", "pets") + _FLAT_FACE,
                                     ("snoring", "snores", "snore", "snored", "snorting",
                                      "snorts", "snort", "loud snoring", "snoring loudly",
                                      "snores loudly", "wakes himself up", "wakes herself up",
                                      # a flat-faced animal that breathes loudly is the same airway
                                      # question, and the breathing card in crisis_replies keeps the
                                      # gasping lines; this is checked below, not assumed
                                      "breathing loudly", "breathing loud", "noisy breathing",
                                      "loud breathing", "breathing noisily")),
                     lambda memory, understood: _pet_snoring(understood), bias=1,
                     # a person who snores is the sleep question, not the pet's
                     avoid=("my husband", "my wife", "my partner", "my boyfriend",
                            "my girlfriend", "my mum", "my dad", "i snore", "i am snoring",
                            "im snoring", "i'm snoring", "he snores", "she snores",
                            "husband snores", "wife snores", "partner snores", "my son",
                            "my daughter", "my brother", "my sister", "my friend", "my baby")))

# A dog or a rabbit in moult: the cat's own coat row stands down for both, so this is the question
# they were left with nothing for.
ENTRIES.append(entry("pet-moult", (("dog", "dogs", "puppy", "pup", "puppies", "rabbit", "rabbits",
                                    "bunny", "bunnies"),
                                   # the moult itself, and not the coat falling out: "my dog is
                                   # losing hair" is the skin row, "my dog is shedding everywhere"
                                   # is the grooming row, and a dog that sheds is already told to
                                   # brush it, so this row keys on the season and the new coat
                                   ("moulting", "molting", "moult", "molt", "blowing his coat",
                                    "blowing her coat", "coat coming out", "coat coming in",
                                    "new coat coming in", "coat is coming out")),
                     lambda memory, understood: _pet_moult(understood), bias=1,
                     avoid=("cat", "cats", "kitten", "kittens", "carpet", "rug", "floor", "sofa",
                            "curtain", "cushion", "my hair", "my head", "ate the")))
# A dog that is breathing heavily at rest, and a horse sweating at rest: the two lines left over
# from the same afternoon's chat as the shiver and the moult. "my dog is breathing heavily" was
# "Thanks for telling me - I'm here if you want to dig into any of that", because pet-hot holds
# out the word breathing (panting in the heat is its line, not this one) and nothing else wanted
# it. "my horse is sweating" was the same nothing.
# Only the words pet-breathing-fast does not carry: that card already has "breathing fast",
# "breathing hard", "laboured breathing" and "struggling to breathe", and it is the stronger
# answer for them.
# "breathing loudly" and "breathing noisily" are left out on purpose: the tooth row's fence sends
# them to the airway card, which is the right answer for a flat-faced dog.
_PET_BREATHING = ("breathing heavily", "breathing heavy", "breathing like that",
                  "panting at rest", "belly heaving", "sides heaving", "breathing all the time",
                  "working to breathe")
_PET_ANIMAL = ("dog", "dogs", "puppy", "puppies", "pup", "cat", "cats", "kitten", "kittens",
               "horse", "horses", "pony", "ponies", "rabbit", "rabbits", "bunny", "pet", "pets",
               "guinea pig", "hamster", "ferret", "bird", "birds", "parrot", "budgie",
               # a line that names the breed instead of the animal is the same question
               "greyhound", "whippet", "lurcher", "labrador", "lab", "terrier", "collie",
               "spaniel", "retriever", "poodle", "beagle", "boxer", "husky", "shepherd",
               "staffie", "jack russell", "cocker", "dachshund", "pug", "bulldog", "ragdoll",
               "siamese", "tabby", "moggy", "moggie")
_NOT_A_PERSON_BREATHING = ("asthma", "copd", "inhaler", "wheez", "my chest", "i cant breathe",
                           "i can't breathe", "i am breathless", "i feel breathless", "panic",
                           "anxiety", "when i walk", "stairs")
_PET_BREATHING_REPLY = (
    "Breathing like that at rest is the vet today rather than a wait: an animal working to "
    "breathe, with the belly or the sides heaving, gums pale or blue, or that cannot settle, is "
    "fluid on the lungs, heat or pain, and it gets worse rather than better. Keep it cool and "
    "quiet with water in reach and let the vet see it - do not wait for the morning if the "
    "breathing is getting harder.",
    "Panting hard straight after a run or in the heat is normal and settles in about ten minutes "
    "in a cool room with water; breathing hard while it is resting is not, and that is a vet "
    "call. Flat-faced dogs are noisy breathers anyway, so what matters is whether this is new, "
    "and whether it is worse than usual.")
_WHAT_IS_THE_BREATHING = ("breathing", "breathe", "breath", "panting", "pant", "asthma", "cough")


_BEEN_ACTIVE = ("after a walk", "after the walk", "after a run", "after playing", "after the park",
                "in this heat", "hot day", "on a walk", "just got back", "after fetch",
                "after agility", "at the park", "been running")


def _pet_breathing(understood):
    """The breathing row, or None for a person's own breath."""
    text = (understood.get("clean") or "").lower()
    if any(w in text for w in _NOT_A_PERSON_BREATHING):
        return None
    if not _a_word_in(text, _PET_ANIMAL):
        return None
    if "asthma" in text or "inhaler" in text:
        return None
    if any(w in text for w in _BEEN_ACTIVE):
        return _PET_BREATHING_REPLY[1]
    return _PET_BREATHING_REPLY[0]


ENTRIES.append(entry("pet-breathing",
                     (_PET_BREATHING, _PET_ANIMAL),
                     lambda memory, understood: _pet_breathing(understood), bias=3,
                     avoid=_NOT_A_PERSON_BREATHING + (
                         # a cough, a sneeze or a heart question has its own card, and the
                         # heat rows own a panting animal in warm weather
                         "cough", "coughing", "sneez", "in this heat", "this heat",
                         "hot weather", "heatwave", "hot day", "hot spot",
                         "gave birth", "whelping", "kittening", "collapsed", "collapse")))

# A horse sweats to cool itself when it works, and a horse standing sweating in its box is in
# pain: colic, tying-up or a fever. The two are told apart by what the horse has been doing.
_HORSE = ("horse", "horses", "pony", "ponies", "mare", "gelding", "foal", "cob", "colt")
_SWEATING = ("sweating", "sweaty", "sweats", "sweating up", "sweating badly", "in a lather",
             "lathered up", "drenched in sweat", "sweat", "hot and sweating")
_HORSE_BEEN_WORKING = ("after riding", "after a ride", "after work", "after exercise",
                       "after a hack", "after schooling", "after the field", "just ridden",
                       "just worked", "been ridden", "coming back from", "after a show",
                       "in the field", "after hunting")
_SWEATING_REPLY = (
    # at rest
    "A horse standing sweating when it has not been worked is pain until the vet says otherwise - "
    "colic, tying-up or a fever - so ring them now and keep it walking gently if it will. A horse "
    "that is sweating, tucked up and off its feed is the same call.",
    # after work
    "That is normal cooling after work: walk it off, sponge the big muscles and the neck with cool "
    "water, scrape the water off and let it drink. A horse still sweating and blowing half an hour "
    "later, or stiff behind, wants the vet.")


def _horse_sweating(understood):
    text = (understood.get("clean") or "").lower()
    if not any(w in text for w in _HORSE):
        return None
    if any(p in text for p in _HORSE_BEEN_WORKING):
        return _SWEATING_REPLY[1]
    return _SWEATING_REPLY[0]


ENTRIES.append(entry("horse-sweating",
                     (_SWEATING, _HORSE),
                     lambda memory, understood: _horse_sweating(understood), bias=3,
                     avoid=("i sweat", "i am sweating", "im sweating", "night sweats",
                            "i keep sweating", "sweating at night", "menopause",
                            "hot flush", "hot flushes", "heat rash", "sweat rash",
                            "under my arms", "underarms")))


# An animal's symptom is the animal's, not a person's. From the deck census in #answers thread
# 111660: "my cat is dragging her back legs" was the hem of a skirt, "my horse is wobbly on his
# feet" was falls in older people, "my dog cant walk properly" was the daily dog walk and "my
# guinea pig is not moving much" was the stroke card. The animal is the subject of the sentence,
# so the animal's symptom is the question, and the rows below answer it for every animal the
# line can name rather than for a dog read out to a rabbit's owner.
_ANI = ("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "pup", "rabbit", "rabbits",
        "bunny", "bunnies", "guinea pig", "guinea pigs", "guinea", "hamster", "hamsters",
        "gerbil", "gerbils", "ferret", "ferrets", "rat", "rats", "horse", "horses", "pony",
        "ponies", "pet", "pets")

# The animal named, as words a reply can use. A horse and a guinea pig are not "a dog", which is
# what _pet_words falls back to, so they are read first and named properly.
_ANI_KIND = (("guinea pig", ("guinea pig", "guinea pigs", "guinea")),
             ("horse", ("horse", "horses", "pony", "ponies")),
             ("hamster", ("hamster", "hamsters")),
             ("rabbit", ("rabbit", "rabbits", "bunny", "bunnies")),
             ("cat", ("cat", "cats", "kitten", "kittens")),
             ("dog", ("dog", "dogs", "puppy", "puppies", "pup")))


def _the_animal(understood):
    """The animal the line names, as {one, they, kind}, or the dog these answers default to."""
    text = " " + str((understood or {}).get("clean") or "").lower() + " "
    pointed_at = str((understood or {}).get("animal_in_hand") or "").lower()
    for kind, words in _ANI_KIND:
        for word in words:
            if " " + word + " " in text or (pointed_at and pointed_at.startswith(word)):
                if kind == "guinea pig":
                    return {"one": "a guinea pig", "One": "A guinea pig",
                            "they": "guinea pigs", "them": "it", "kind": kind}
                if kind == "horse":
                    return {"one": "a horse", "One": "A horse", "they": "horses",
                            "them": "it", "kind": kind}
                return {"one": "a " + kind, "One": "A " + kind, "they": kind + "s",
                        "them": "it", "kind": kind}
    return {"one": "an animal", "One": "An animal", "they": "animals", "them": "it",
            "kind": "animal"}


_BACK_LEGS = ("dragging his back legs", "dragging her back legs", "dragging its back legs",
              "dragging his back leg", "dragging her back leg", "dragging back legs",
              "dragging his back end", "dragging her back end", "dragging its back end",
              "dragged his back legs", "dragged her back legs",
              "cant use his back legs", "cant use her back legs", "cant use its back legs",
              "can't use his back legs", "can't use her back legs", "can't use its back legs",
              "back legs are paralysed", "back legs are paralyzed", "back legs have gone",
              "back legs gave way", "back end is paralysed", "back end is paralyzed",
              "cant move his back legs", "cant move her back legs",
              "cant move its back legs", "sudden paralysis", "suddenly paralysed",
              "suddenly paralyzed", "dragging his hind legs", "dragging her hind legs",
              "gone off his back legs", "gone off her back legs", "gone off its back legs",
              "off his back legs", "off her back legs", "off its back legs",
              "back legs are gone", "back legs have gone", "cant feel his back legs",
              "cant feel her back legs", "back legs wont work", "back legs dont work",
              "hind legs are paralysed", "hind legs are paralyzed", "cant stand up")


def _pet_back_legs(memory, understood):
    pet = _the_animal(understood)
    if pet["kind"] == "horse":
        return ("That is an emergency - ring the vet now. A horse that cannot use its back legs "
                "may have a fracture, a spinal injury or a poisoning, and it must not be walked "
                "or moved far: keep it still on level ground, do not try to get it up by pulling "
                "the head or the tail, and keep other horses away while you wait for the vet.")
    return ("Ring the vet now if this came on today: {one} that suddenly cannot use its back legs "
            "usually has a blood clot at the back of the aorta or a spinal injury, and the first "
            "hours decide how much comes back. Keep {them} warm and quiet on a towel, carry "
            "{them} to the car rather than letting {them} walk, and note the time it started. A "
            "slow drag that has built up over months is a different, less urgent question - but "
            "a change today is not one to watch.").format(**pet)


_WOBBLY = ("wobbly on his feet", "wobbly on her feet", "wobbly on its feet", "wobbly",
           "swaying", "sways", "swaying about", "swaying side to side",
           "unsteady on his feet", "unsteady on her feet", "unsteady",
           "cant walk properly", "can't walk properly", "cant walk straight",
           "cant walk in a straight line", "staggering", "staggers", "staggered",
           "keeps falling over", "falling over", "keeps falling down", "off his legs",
           "off her legs", "off its legs", "weak in the back legs", "wobbling")


def _pet_wobbly(memory, understood):
    pet = _the_animal(understood)
    if pet["kind"] == "horse":
        return ("A horse that is wobbly or unsteady wants the vet out today, not a day's rest: "
                "it can be the neck or spine, a poisoning, or the balance centre, and a horse "
                "that goes down is hard to get up again. Keep {them} on level ground with food "
                "and water within reach, do not ride or lunge {them}, and note when it started "
                "and whether it is worse on one side.").format(**pet)
    return ("A wobbly animal is a vet visit today, not a wait and see: in a dog or cat it is often "
            "the inner ear, a poisoning or something pressing on the spine. Keep {them} off "
            "stairs and off the furniture, with food and water within reach, and note whether "
            "{they} is falling to one side, tilting its head or crossing its legs - a vet reads "
            "that off the note better than off a memory.").format(**pet)


_NOT_MOVING = ("not moving much", "not moving", "isnt moving", "isn't moving", "wont move",
               "will not move", "not moving about", "not moving around", "lying flat",
               "lying still", "just lying there", "flopped out", "not himself at all",
               "not herself at all", "very quiet and not moving")


def _pet_not_moving(memory, understood):
    pet = _the_animal(understood)
    return ("{One} that has stopped moving about is ill, and small animals hide it until they are "
            "very sick - a rabbit, guinea pig or hamster sitting still and fluffed up is a vet "
            "call today, tonight if it is also off its food. Keep {them} warm and quiet, put "
            "water and hay or its usual food within reach so it need not move for them, and do "
            "not bath or handle it more than you have to.").format(**pet)


_DIRTY_BOTTOM = ("dirty bottom", "mucky bottom", "dirty bum", "mucky bum", "soiled bottom",
                 "matted bottom", "dirty back end", "messy bottom", "smelly bottom",
                 "cant clean himself", "cant clean herself", "not cleaning himself",
                 "not cleaning herself", "flies around", "fly strike", "flystrike")


def _pet_dirty_bottom(memory, understood):
    return ("Wash and dry it today and ring the vet: a rabbit or guinea pig with a dirty bottom is "
            "at risk of flystrike, where flies lay eggs in the soiled fur and maggots hatch within "
            "hours in warm weather. Check the bottom twice a day in summer and keep the hutch "
            "clean; an animal that cannot keep itself clean needs a vet for the cause, which is "
            "usually teeth or a sore back.")

ENTRIES.append(entry("pet-back-legs", (_BACK_LEGS, _ANI), _pet_back_legs, bias=3))
ENTRIES.append(entry("pet-wobbly", (_WOBBLY, _ANI), _pet_wobbly, bias=3,
                     # a wobbly table and a wobbly tooth are not animals: this row needs the
                     # animal, and these say the line is about something else
                     avoid=("my tooth", "a tooth", "tooth is", "teeth", "table", "chair",
                            "shelf", "i feel", "i am", "im ", "my legs", "i keep",
                            "my knee", "my ankle", "my hand")))
ENTRIES.append(entry("pet-not-moving", (_NOT_MOVING, _ANI), _pet_not_moving, bias=2))
ENTRIES.append(entry("pet-dirty-bottom",
                     (_DIRTY_BOTTOM, ("rabbit", "rabbits", "bunny", "bunnies", "guinea pig",
                                      "guinea pigs", "guinea", "hamster", "hamsters")),
                     _pet_dirty_bottom, bias=3))


# The row, by name, for a follow-up answered from the same words. It is looked up after the list
# is built so the row keeps its place in the order the entries were written in.
DOG_FEED_AMOUNT_ENTRY = next(_entry for _entry in ENTRIES if _entry.id == "dog-feed-amount")

