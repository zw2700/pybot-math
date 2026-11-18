"""Home and DIY: the jobs around a flat or house people ask about most.

The answers lane owns this domain. Entries are keyed by the thing and the problem (the
radiator, the blocked sink, the mould) rather than by wording, so the same advice
answers "how do I..." and "my X is doing Y". Everything here is the ordinary version
of the job: the steps a careful neighbour would give, plus when to stop and call
someone qualified (gas, mains electrics, anything you can't isolate).
"""
import re

from ..compose import pick
from .lookup import JOB_GUARD, entry, the_fault, the_thing_has_gone
from .wording import A_JOB_LEFT_UNDONE, MACHINE_SOUNDS, NOISE_WORDS
from .body import THING_PARTS, _a_thing_owns_the_part, the_stomach_is_what_it_is_about
from .dishes import cook_ask

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("home-and-diy", "garden-and-plants")

# The paragraph both arrival keys answer with: one text, so a change to one is a change to
# both, and a person who has just walked in does not get a different set of first-night jobs
# from one who is asking about it before the move.
FIRST_NIGHT_BOX = (
    "On the first night you need the bed made, toilet roll, a kettle, mugs, a torch and "
    "chargers in one labelled box. Photograph the gas and electricity meters when you arrive, "
    "and find the stopcock and fuse box before you need them.")

# A small appliance is the one place where new beats repair: the call-out costs more than the
# thing. Naming it matters, because "repair the washing machine" about a toaster is worse than a
# shrug, so the machine the line names is read from one table and the rule is worded for it.
SMALL_APPLIANCES = (("sandwich maker", "sandwich maker"), ("hair dryer", "hair dryer"),
                    ("hairdryer", "hair dryer"), ("toaster", "toaster"), ("kettle", "kettle"),
                    ("blender", "blender"))

GARDEN_MACHINES = (("hedge trimmer", "hedge trimmer"), ("leaf blower", "leaf blower"),
                   ("lawnmower", "mower"), ("mower", "mower"), ("strimmer", "strimmer"),
                   ("chainsaw", "chainsaw"))

WHITE_GOODS = (("washing machine", "washing machine"), ("washer", "washing machine"),
               ("tumble dryer", "tumble dryer"), ("dishwasher", "dishwasher"),
               ("fridge", "fridge"), ("freezer", "freezer"),
               ("oven", "oven"), ("cooker", "cooker"), ("hob", "hob"),
               ("microwave", "microwave"), ("boiler", "boiler"), ("dryer", "tumble dryer"),
               ("vacuum", "vacuum cleaner"), ("hoover", "vacuum cleaner"))

# An appliance door is not a room door. A fridge door that will not shut is the seal, an oven door
# is the hinge, and the strike plate and the wind have nothing to do with either - but a room-door
# entry keyed on "door" and "shutting" read every one of them as a door in a draught ("the freezer
# door wont stay shut" was told to fit a hook and eye). The words are built from the white goods, so
# an appliance added to that table is covered here the same day.
APPLIANCE_DOOR_WORDS = tuple(name + " door" for name, _ in WHITE_GOODS) + (
    "machine door", "appliance door", "microwave door")

# The decision has to be asked for in this line, because a follow-up is read with the last turns
# put back in and "the machine has a delay start on it" otherwise inherits "is it worth ...".
DECIDING_NOW = re.compile(r"\b(worth|repair|repairing|repairs|replace|replacing|mend|mending|fix|"
                          r"fixing|scrap|scrapping|buy new|buying new|new one|or new|engineer|"
                          r"engineers)\b")
# Shopping is the other question: "is it worth buying a new washing machine" wants the drum sizes,
# not a rule about repairing the old one, so the buying shapes stand the rule down.
# "worth getting" alone is not a shopping shape: "is it worth getting someone in" is a repair
# question about the machine the last line named, so the words after it have to name a thing.
SHOPPING_NOW = re.compile(r"\b(worth (?:buying|getting) (?:a|an|the|one|another|new)|"
                          r"should i (?:buy|get) (?:a|an|the|one|another|new)|"
                          r"which \w+ (?:should i|to) buy|what \w+ should i buy|is it worth a new)\b")
# The decision is asked both ways round: "should i repair it or buy a new one" and "is it worth
# fixing or should i get a new one". In the second the buying comes after the "or", so the
# shopping pattern on its own would stand the rule down on a plain repair question. Any repair
# word followed by an "or" in the same clause is somebody weighing it up, not choosing a model.
# The money rule is about the machine you already own, so the line has to say something is wrong
# with it, or name the repair. "Is a tumble dryer worth it" names a machine and asks whether to buy
# one; "my oven is broken, is it worth it" asks the decision without ever saying repair. A fault
# word (or keeping-versus-replacing) is what separates the two, which a list of phrases cannot do,
# because "worth it" is in both questions.
KEEPING_NOW = re.compile(r"\b(keep|keeps|keeping|kept)\b")


# "Do I need a new washer" is the decision said the plainest way there is: nobody asks it about
# a machine they do not already own, and the answer is the quote rule rather than a drum size.
# The buying question ("what washing machine should i buy") names what to buy; this one weighs up
# the one in the house, so `need a new` counts as both the ask and the owning.
NEED_A_NEW = re.compile(r"\b(?:do|will|would|should|could|might)\s+i\s+need\s+"
                        r"(?:a|an|another)\s+new\b")
CHOOSING = re.compile(r"\bor\s+(?:repair|repair|fix|fixed|mend|keep)\b"
                      r"|\b(?:repair|repairing|fix|fixed|fixing|mend|mending|keep|keeping)\b[^.]{0,40}?\bor\b")

# The rule is about a machine that is already in the house. "is a tumble dryer worth it" and
# "are air fryers worth it" ask whether to buy one at all, and answering those with a quote on a
# machine nobody said they own is nonsense (alert-cat filed it on `19c7d63`). A possessive or a
# fault in the line is what makes the machine theirs, and a repair word makes it theirs too.
OWNED_NOW = re.compile(r"\b(?:my|our|me and|we've got|we have|weve got|i have|i've got|ive got)\b")
# A fault is said in a lot of ways and one of them is a whole phrase: "the oven has packed in,
# should i get it fixed or buy a new one" is the decision, and "packed in" was the only thing
# saying anything had gone wrong. This constant was defined twice in this module by two merges,
# so only the second set was ever live and the phrases above it never matched.
FAULT_NOW = re.compile(r"\b(?:broken|broke|bust|faulty|fault|repair|repairing|fix|fixing|mend|"
                       r"mending|fixes|fixed|replace|replacing|replacement|scrap|scrapping|leak|leaks|leaking|"
                       r"noisy|noise|banging|stopped|stopping|stopped working|not working|"
                       r"gone wrong|on the blink|playing up|packed in|packed up|conked out|"
                       r"given up the ghost|had it|dead|wont|won't|isnt|isn't|error|smell|smells|"
                       r"engineer|part|parts|motor|drum|pump|element|seal|not heating)\b")

# The age the line gives is half of the decision on its own: a machine past eight years is at the
# end of its life, so a quote is money towards a new one, whatever the repair is.
YEARS_OLD = re.compile(r"\b(\d{1,2})\s*(?:year|yr)s?[ -]?old\b")


# The things whose own smoke is a fault, not a house fire. Kept beside the appliance entries so
# the answer for one smoking thing names the same objects the safety stand-down does.
_SMOKING_THING = ("oven", "cooker", "hob", "grill", "toaster", "kettle", "microwave",
                  "air fryer", "washing machine", "washer", "tumble dryer", "dryer",
                  "dishwasher", "fridge", "freezer", "hoover", "vacuum", "laptop",
                  "computer", "phone", "mobile", "charger", "plug", "socket", "tv",
                  "telly", "television", "iron", "hair dryer", "printer", "boiler",
                  "radiator", "heater", "extractor fan", "fuse box", "appliance")


# Who can reach the bottle decides the answer, and what is in it decides the sentence before. The
# classes are the ones a household actually holds: a poison placed on purpose, pellets a child can
# pick up, a dusting, a spray, a trap, a bottle of cleaner, and the two that smell of nothing.
_CHEMICAL_CHILD = ("toddler", "toddlers", "baby", "babies", "newborn", "child", "children",
                   "kid", "kids", "grandchild", "grandchildren")
_CHEMICAL_EXPECTING = ("pregnant", "pregnancy", "expecting")
_CHEMICAL_PET = ("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies", "pet",
                 "pets", "hamster", "rabbit", "bird", "birds", "parrot", "fish")

_CHEMICAL_BAIT = (
    "Rat and mouse bait is a poison by design, so the box is the answer: a lockable bait station "
    "fixed down or pushed tight against a wall, with the block inside it and nothing loose under a "
    "cupboard. A toddler can open a screw-top tub, and a dog can chew a station pushed behind a "
    "bin, so put them where an adult can reach and a child cannot see. The poison thins the blood, "
    "so the hospital gives the antidote rather than waiting for symptoms - say what it was and when.")
_CHEMICAL_PELLETS = (
    "Slug pellets are the garden poison a child picks up, because they are small, blue and the size "
    "of a sweet: a handful is an A&E trip, and a dog that eats them starts shaking within hours. "
    "Use them inside a closed trap or under a slate rather than scattered on a bed, or skip the "
    "poison altogether - a beer trap sunk to the rim, copper tape round a pot and nematodes watered "
    "on in spring all work.")
_CHEMICAL_POWDER = (
    "Ant powder is an insecticide for cracks, not for floors: puff it along the skirting, under the "
    "worktop edge and into the gap by the pipe, leave it a week, then hoover it up. A crawling baby "
    "and a cat that licks its fur are both in the way of a dusting across a doorway, so keep the "
    "room empty until it has settled and wipe anything that was out on the side.")
_CHEMICAL_SPRAY = (
    "Weedkiller is safe to the household when it is dry and not before: an hour on a warm day, and "
    "the lawn is a no-go for a toddler and a cat until then. Mix it outside, keep it in its own "
    "labelled bottle - never a drinks bottle, which is how most of these cases start - and let "
    "somebody else spray it if you are pregnant.")
_CHEMICAL_TRAP = (
    "A trap belongs in a box or behind a unit, not on a floor a child crawls on: a snap trap at the "
    "back of a cupboard behind the kickboard, or a tunnel trap whose openings are too small for "
    "fingers. Put it where you can see it and a toddler cannot reach, check it daily, and use a "
    "live trap if there is a cat about.")
_CHEMICAL_CLEANER = (
    "Bleach, oven cleaner and white spirit are safe in the house as long as nobody small can get "
    "at them, so the catch on the cupboard is the whole answer: the bottle they came in, the lid "
    "on tight, and never decanted into a drinks bottle or a jam jar. Gloves and an open window for the "
    "fumes, and wash the skin with plenty of water if it splashes.")
_CHEMICAL_AIR = (
    "An oil diffuser is the one to think about, because the oil is concentrated, smells of sweets "
    "and a toddler can drink a whole bottle of it. Keep reed diffusers, plug-ins and the refill "
    "bottles above arm's reach or in a locked cupboard, and use a wall plug-in rather than a bowl "
    "of oil on a side table.")
# A spray is the one hazard where the air is the danger rather than the bottle: the person is
# usually in the room while it settles, and for a cat there is a specific poison to know about.
# Permethrin and the other pyrethroids are in almost every fly spray and in every dog flea
# treatment, and a cat's liver cannot clear them, which is why a dog product on or near a cat is
# the classic cat poisoning.
_CHEMICAL_AEROSOL = (
    "Fumes are the thing with a spray, so open a window and keep the cat, the dog and the baby out "
    "of the room until it has settled, and take a fish tank or a bird out of the house altogether. "
    "Cats are the ones to be strict about: permethrin and the other pyrethroids in fly sprays and "
    "in every dog flea spray are deadly to them, so never use a dog product near a cat and keep "
    "them apart for a couple of days. A puppy and a crawling baby come next, because both lick "
    "surfaces - wipe the sides down and put the food bowls away first. A cat that starts drooling, "
    "twitching or walking wobbly after a spray needs the vet now, not tomorrow.")

_CHEMICAL_FOGGER = (
    "A fogger leaves insecticide on every surface a baby touches, so the room has to be empty for "
    "the hours on the tin, with the fish tank covered, and everything washed down afterwards. With "
    "a crawling baby or a cat in the house, a spot-on treatment and a hot wash of the bedding does "
    "the same job with the poison kept on the animal.")
_CHEMICAL_ANTIFREEZE = (
    "Antifreeze is the sweet one and a spoonful is enough to kill a cat: it lives in a sealed "
    "container, spills are soaked up with cat litter and swept, and the bottle never sits open in "
    "the garage. A pet that has licked a spill needs the vet the same day, because the treatment "
    "works best in the first hours.")

_CHEMICAL_CLASSES = (
    (("bait", "rat bait", "mouse bait", "bait box", "bait station",
      "rat poison", "mouse poison", "rodenticide"), _CHEMICAL_BAIT),
    (("slug pellet", "slug pellets", "slug bait"), _CHEMICAL_PELLETS),
    (("ant powder", "ant killer", "ant bait", "insect powder", "pesticide"), _CHEMICAL_POWDER),
    (("weedkiller", "weed killer"), _CHEMICAL_SPRAY),
    (("trap", "traps", "mouse trap", "mouse traps", "rat trap", "rat traps"), _CHEMICAL_TRAP),
    (("flea bomb", "flea bombs", "fogger", "bug bomb"), _CHEMICAL_FOGGER),
    # Before the air freshener, because a line that says "insect spray" is the air question and one
    # that says "air freshener" is the bottle question; the longest name on the line decides.
    (("insect spray", "fly spray", "ant spray", "wasp spray", "flea spray", "bug spray",
      "mosquito spray", "room spray", "fly killer", "insect killer", "aerosol", "sprayed",
      "spraying", "spray", "sprays"), _CHEMICAL_AEROSOL),
    (("air freshener", "air fresheners", "diffuser", "reed diffuser", "plug in air freshener",
      "chemical", "chemicals"), _CHEMICAL_AIR),
    (("antifreeze",), _CHEMICAL_ANTIFREEZE),
    (("bleach", "oven cleaner", "drain cleaner", "white spirit", "paint thinner"), _CHEMICAL_CLEANER),
)

_CHEMICAL_CHILD_RING = ("If a child has eaten or drunk any, ring 111 now and take the box or the "
                        "bottle with you - don't wait for them to look ill.")
_CHEMICAL_PET_RING = ("If a pet has got at it, ring the vet and take the packet: the weight of the "
                      "animal decides the dose.")
_CHEMICAL_EXPECTING_RING = ("If you are pregnant, get somebody else to put it down and stay out of "
                            "the room while it settles.")


def _the_space_in_the_house(understood):
    """False when the "room" in the line is a bed for the night rather than space at home.

    The row below answers where the things go, and "the hotel has no room for us" is a booking
    problem. Which one the line means is not in the word: it is the rest of the sentence
    ("kitchen", "cupboard", "put" against "hotel", "booking", "two nights"), so the reading says
    it once for every row that needs it (bot/understanding/senses.py) and this row reads it here.
    A line that says neither keeps its storage answer, which is what it had before.
    """
    sense = (understood or {}).get("sense") or {}
    return sense.get("room") != "booking"


def _chemical_safety(memory, understood):
    """A poison, a powder or a cleaner, answered by who is in the house."""
    words = [str(word).lower() for word in ((understood or {}).get("words") or [])]
    if not words:
        return None
    said = " ".join(words)

    def named(names):
        return any(re.search(r"\b" + re.escape(name) + r"\b", said) for name in names)

    # The longest name on the line decides the class, so "is antifreeze poisonous to dogs" is
    # antifreeze rather than the bare word "poison" that the bait class also holds.
    hazard = None
    best = 0
    for names, answer in _CHEMICAL_CLASSES:
        for name in names:
            if len(name) > best and named((name,)):
                best = len(name)
                hazard = answer
    if hazard is None:
        hazard = _CHEMICAL_CLEANER

    parts = [hazard]
    child = named(_CHEMICAL_CHILD)
    pet = named(_CHEMICAL_PET)
    expecting = named(_CHEMICAL_EXPECTING)
    if child:
        parts.append(_CHEMICAL_CHILD_RING)
    if pet:
        parts.append(_CHEMICAL_PET_RING)
    if expecting:
        parts.append(_CHEMICAL_EXPECTING_RING)
    if not (child or pet or expecting):
        return None
    return " ".join(parts)


def _place_smell(memory, understood):
    """A smell in a place: the source first, then the cleaner that works on that source."""
    line = " ".join(str((understood or {}).get("clean")
                        or (understood or {}).get("text") or "").lower().split())
    if re.search(r"\b(mice|mouse|rodent|rodents|rats|rat)\b", line):
        return ("Look for droppings first, along the joists and behind anything stored, because in "
                "a loft, a shed or an empty room that is usually mice: clear them up in gloves and "
                "a mask, wet the area before sweeping so the dust does not rise, then wash it with "
                "a disinfectant. Block the gaps round pipes and cables and set traps along the "
                "wall.")
    if re.search(r"\b(wee|urine|peed|peeing|pee|piss)\b", line):
        return ("Something has soaked it up, so find that first: a hard floor or the skirting comes "
                "clean with a biological (enzyme) cleaner, and bleach only hides it for a day. "
                "Sniff low down and in the corners to find the patch, soak the cleaner in, press a "
                "towel hard onto it, then air the room while it dries.")
    if re.search(r"\b(chips|chip pan|fried|frying|fish|bacon|curry|onions?|garlic)\b", line):
        return ("Open a window, then simmer a pan of water with a sliced lemon or a splash of "
                "vinegar for 10 minutes: that clears cooking smells better than any spray. Check "
                "the bin, the drain and the fridge as well, because fat that has gone down them "
                "keeps giving the smell back.")
    return ("Find the source before you treat the air: a damp patch, a dead mouse, a spilt bottle or "
            "a blocked drain keeps giving off until it is dealt with, and a smell that comes and goes "
            "after rain usually means water is getting in somewhere. Then air it hard - the door and "
            "a window open with a fan pushing air through for an hour or two - and wash the hard "
            "surfaces with hot soapy water. A bowl of bicarbonate of soda or vinegar left in the "
            "corner takes out what is left; masking it with air freshener only works for an hour.")


def _soft_smell(memory, understood):
    """A soft thing or a car seat that has taken a smell up: the cleaner, then how to dry it."""
    return ("Soak a biological (enzyme) cleaner into it rather than scrubbing the surface: that is "
            "what breaks down what has soaked in, and bleach or a normal carpet shampoo only "
            "freshens the top. Press a towel hard onto the patch to pull the moisture out, leave "
            "bicarbonate of soda on it overnight, then vacuum it and air the thing with a window "
            "open until it is properly dry. A car seat wants the same job with the doors open, and "
            "if the smell comes back the leak is under it, so check the floor or the foam.")


def _age_in(line):
    """The age the line gives, or None: "my 15 year old washing machine", "it is 12 years old"."""
    match = YEARS_OLD.search(line) or re.search(r"\b(\d{1,2})\s*(?:year|yr)s?\b", line)
    return int(match.group(1)) if match else None


def _words_of_age(age):
    return {1: "a year", 2: "two years", 3: "three years", 4: "four years", 5: "five years",
            6: "six years", 7: "seven years", 8: "eight years", 9: "nine years",
            10: "ten years", 11: "eleven years", 12: "twelve years", 13: "thirteen years",
            14: "fourteen years", 15: "fifteen years", 16: "sixteen years",
            17: "seventeen years", 18: "eighteen years", 19: "nineteen years",
            20: "twenty years"}.get(age, "%d years" % age)


def _named(said, table, default="washing machine"):
    """The machine the line names, read as whole words so "iron" is not "ironing"."""
    for word, name in table:
        if re.search(r"\b" + re.escape(word) + r"s?\b", said):
            return name
    return default


def _small_appliance(thing, memory):
    article = "an" if thing[0] in "aeiou" else "a"
    return pick([
        article.capitalize() + " " + thing + " is not worth repairing: a new one costs less than "
        "the call-out, so replace it. Buy the next one from a shop with a two-year guarantee and "
        "keep the receipt, because that is the only cover a cheap appliance is worth having.",
        "Replace the " + thing + " rather than repair it: the call-out alone usually costs more "
        "than a new one, and the parts are not made to be swapped. A two-year guarantee from the "
        "shop is worth more than any repair here.",
    ], memory)


def _garden_machine(thing, memory):
    article = "an" if thing[0] in "aeiou" else "a"
    return pick([
        article.capitalize() + " " + thing + " is worth a service if the engine is sound: a blade, "
        "oil and a spark plug cost a fraction of a new one, and a service is the whole of the "
        "repair most of them ever need. If the engine is seized or the body has rusted through, "
        "replace it instead.",
        "Service the " + thing + " if it starts and runs: a new blade, oil and a plug is a small "
        "fraction of the price of a new one. If it will not start at all, or the body has rusted "
        "through, put the money towards a new one.",
    ], memory)


# Something wrong with a machine, for the turn that says it ("the washing machine smells of
# damp"). Kept here beside CALLING_SOMEONE because the follow-up below is what needs it: the
# ownership gate the repair rule uses for its own line may grow separately.
TROUBLE_NOW = re.compile(
    r"\b(?:broken|broke|bust|faulty|fault|leak|leaking|smell|smells|smelly|noisy|noise|banging|"
    r"rattling|grinding|squealing|stopped working|stopped|wont start|won't start|isnt|isn't|error|"
    r"tripping|blocked|clogged|stuck|rusty|not heating|not spinning|not draining|drum|element|"
    r"pump|motor|seal|worn)\b")

# "is it worth getting someone in" is a question about the machine the last line named, and it
# names neither the machine nor the fault itself (sky-tuna, #answers 14156). The two facts were
# said one line earlier, so they are read from there -- see machine_before().
CALLING_SOMEONE = re.compile(
    r"\b(?:someone in|somebody in|a man in|someone out|engineer|plumber|repair ?man|call ?out|"
    r"call someone|who (?:do|should) i (?:call|ring)|get it looked at|looked at|"
    r"worth getting someone|second opinion|quote)\b")


# "who do i call about it" asks for the trade, not for the decision: the person has already
# accepted that someone comes out and wants to know who. It is answered with who to ring and
# what to ask them, before the money rule, which answers "is it worth it" instead.
WHO_TO_CALL = re.compile(
    r"\b(?:who (?:do|should) i (?:call|ring|get|use)|who to call|which engineer|"
    r"what kind of engineer)\b")

# The machine rule fires on a line that points back at what was just said ("is it worth fixing",
# "shall i just replace it") as well as on one that asks who to call. A line naming a machine of
# its own is that machine's own question, and a line naming something else ("should i replace my
# sofa") has no back-pointer, so neither is read as being about the machine.
FOLLOWING_IT = re.compile(r"\b(?:it|its|that|this|them|they|one)\b")

# "Can I do it myself" is the skill question, not the money one. The person asking whether the
# job is in their hands wants the same decision worded as which parts are a swap, and a money
# word in the same line ("is it worth fixing it myself or shall i replace it") keeps the quote
# rule. "replace" is deliberately not a money word on its own: "can i replace a door seal
# myself" is the skill question about a part.
SELF_JOB_NOW = re.compile(r"\b(?:myself|my self|diy|diy job|on my own|my own|can i fix|"
                          r"could i fix|can i repair|could i repair|can i replace|"
                          r"can i change|could i change|do it myself|have a go|give it a go|"
                          r"give it a try)\b")
WORTH_NOW = re.compile(r"\b(?:worth|scrap|scrapping|new one|buy a new|buying new|or new|"
                       r"money)\b")

# What a person can do themselves on each machine, and what is not theirs to touch. The quote
# rule already says whether the machine is worth repairing; this is the same decision said as
# which parts are a swap, which is what "can i fix it myself" asks. One line per machine,
# because the answer really is different: a washing machine's pump is a trade and its filter
# cap is not, and a microwave keeps a lethal charge after it is unplugged.
DIY_PARTS = {
    "washing machine": "the door seal, the filter cap, the inlet hose and the belt are swaps with "
                       "the water off and the plug out, and the pump inside, the drum and the "
                       "wiring need an engineer",
    "dishwasher": "the filter, the spray arms, the door seal and the inlet hose are swaps with the "
                  "water off and the plug out, and the pump and the control board need an engineer",
    "tumble dryer": "the filter, the door seal and the belt are yours with the plug out, and the "
                    "heating element and the thermal fuse behind the back are an engineer's job",
    "fridge": "the door seals, the drainage hole at the back and the thermostat are yours, and the "
              "sealed gas and the compressor are an engineer's job",
    "freezer": "the door seals and the thermostat are yours, and the sealed gas and the compressor "
               "are an engineer's job",
    "oven": "a failed element, the fan motor, the door seal and the shelf runners are swaps with "
            "the power off at the wall, and the wiring and the control board are an engineer's",
    "cooker": "an element, the door seal and the shelf runners are swaps with the power off at the "
              "wall, and the wiring and the control board are an engineer's",
    "hob": "the knobs, the pan supports and a ceramic ring are swaps with the power off, and the "
           "wiring behind the wall plate is an electrician's job",
    "microwave": "nothing inside a microwave is a DIY job, because the capacitor holds a lethal "
                 "charge long after it is unplugged, so a faulty one is replaced rather than "
                 "repaired",
    "vacuum cleaner": "the belt, the filters and a blocked hose are yours, and the motor and the "
                      "wiring are not worth touching at the price of a new one",
}


# A machine the tables do not know is still a machine: "my coffee machine is leaking" then "is it
# worth getting someone in" gets the same rule, worded about "a machine".
MACHINE_WORD = re.compile(r"\b(?:machine|appliance|unit|device|white goods)\b")


def machine_named(said):
    """The machine a line names, or "" -- "washing machine", "coffee machine", "lawnmower"."""
    said = str(said or "").lower()
    return (_named(said, SMALL_APPLIANCES, default=None)
            or _named(said, GARDEN_MACHINES, default=None)
            or _named(said, WHITE_GOODS, default=None) or "")


def machine_before(memory):
    """The line before, when it named a machine and said something was wrong with it.

    Only the turn immediately before, and only with a machine and a fault in it together: a
    machine that dropped out of the conversation three turns ago is not what "is it worth getting
    someone in" is about, and "i'm exhausted" is not a fault. answers.py asks for this before it
    answers a line that names no machine of its own.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return ""
    earlier = str((turns[-1] or {}).get("user") or "").strip().lower()
    if not _machine_turn(earlier):
        return ""
    return earlier


def _machine_turn(line):
    """True when the line says something is wrong with a machine ("the kettle is leaking")."""
    line = str(line or "").lower()
    if not TROUBLE_NOW.search(line):
        return False
    return bool(machine_named(line) or MACHINE_WORD.search(line))


def the_machine_decision(memory, earlier, line):
    """The repair rule for the machine the line before named, when this line asks about it.

    "the washing machine smells of damp" then "is it worth getting someone in": the machine and
    the fault are in the first line, the decision in the second, so the rule is asked about both.
    Empty when the rule does not apply, so the caller can answer the line another way.
    """
    if not _machine_turn(earlier):
        return ""
    if WHO_TO_CALL.search(str(line or "").lower()):
        # A line that names a trade of its own is that trade's question, not the machine's:
        # "my boiler is making a banging noise" then "who do i call about a wasp nest?" was
        # answered with a Gas Safe engineer. The who-to-call row reads the line's own trade
        # first, so the machine path stands aside for it.
        if _trade_for(str(line or "").lower()):
            return ""
        heard = str(earlier or "").lower()
        if _named(heard, WHITE_GOODS, default=None) in ("boiler", "gas boiler"):
            return ("A Gas Safe engineer, not a general plumber: gas work is theirs by law. Ask "
                    "for a fixed call-out price and say what the boiler is doing, and check the "
                    "quote against half the price of a new one before you agree to a repair.")
        named = machine_named(heard)
        maker = "the " + named if named else "the machine"
        return ("Look for a repair engineer who covers " + maker + " - the maker's own service "
                "while it is under warranty, otherwise a local white-goods engineer with good "
                "reviews. Ask for a fixed call-out price before they come, and weigh the quote "
                "against half the price of a new one: past that, replace it.")
    reading = {"text": str(line or "").lower(),
               "clean": (str(earlier or "") + " " + str(line or "")).strip().lower(),
               "earlier": str(earlier or "").strip().lower(),
               # The earlier line was read and it did say something was wrong (TROUBLE_NOW), so
               # the fault rule has its fault even when the word for it is not one FAULT_NOW
               # knows ("smells of damp", "banging", "stopped").
               "fault": True,
               "calling": bool(CALLING_SOMEONE.search(str(line or "").lower()))}
    return _repair_judgement(memory, reading)


def _diy_decision(said, memory=None):
    """The skill question answered for the machine the conversation is about.

    "can i fix it myself" after a fault is a question about the person's own hands, so the answer
    is the list of parts a swap each way round: the maker's manual gives the part number, and the
    rest is an engineer's. A machine with no parts worth swapping says so instead - a cheap one is
    replaced, and a microwave is never opened.
    """
    said = str(said or "").lower()
    thing = (machine_named(said) or _named(said, SMALL_APPLIANCES, default=None)
             or _named(said, GARDEN_MACHINES, default=None) or "")
    if not thing:
        # The machine is often a line back: "my boiler keeps locking out" then "can i fix it
        # myself". Reading only for a fault would miss "keeps locking out" - a fault the parser
        # does not know - so the last line's machine counts here on its own.
        turns = memory.get("turns") if isinstance(memory, dict) else None
        last = str(((turns or [{}])[-1] or {}).get("user") or "") if turns else ""
        thing = machine_named(machine_before(memory)) or machine_named(last)
    if thing in ("boiler",):
        # A boiler is the one machine where the answer is mostly "no": the pressure and the
        # reset are the whole of what a person may touch, and the rest is Gas Safe work by law.
        return ("Partly: the pressure gauge (1 to 1.5 bar), the thermostat and the reset button "
                "are yours, and anything inside the case is the engineer's, because a gas boiler "
                "is Gas Safe work by law. If it locks out twice, or you smell gas, stop and call a "
                "Gas Safe engineer.")
    parts = DIY_PARTS.get(thing)
    if parts:
        article = "an " if thing[0] in "aeiou" else "a "
        return ("For " + article + thing + ", " + parts + ". Take the model number and the part "
                "number off the manual before you order anything, and photograph how it came "
                "apart.")
    if thing:
        article = "an " if thing[0] in "aeiou" else "a "
        return ("On " + article + thing + ", the parts you can see - a filter, a seal, a hose, a "
                "belt, a plug fuse - are swaps with the water off and the plug out, and the "
                "motor, the drum and the wiring are an engineer's job.")
    return ("Do the parts you can see: a filter, a door seal, an inlet hose, a belt or a plug fuse "
            "is a swap with the water off and the plug out, and the manual gives the part number. "
            "Leave the motor, the drum, the wiring and anything with gas in it to an engineer.")


def _repair_judgement(memory, understood):
    """The money rule for a broken appliance, worded for the machine the line names."""
    reading = understood if isinstance(understood, dict) else {}
    # `clean` carries the last turns put back in for a follow-up, so "the machine has a delay start
    # on it" after "is it worth doing the washing at night" reads as worth + machine. The decision
    # has to be in this line, so the guard reads `text`, which is the line as it was sent.
    line = str(reading.get("text") or reading.get("clean") or "").lower()
    choosing = CHOOSING.search(line)
    # Asking who to call is asking whether to spend: "should i get an engineer out" after a fault
    # is the same question as "is it worth repairing it", so the follow-up hands that in as
    # `calling`. A line on its own still has to say worth, repair, replace or fix.
    need_new = bool(NEED_A_NEW.search(line))
    asking = (bool(DECIDING_NOW.search(line)) or bool(SELF_JOB_NOW.search(line)) or need_new
              or bool(reading.get("calling") and CALLING_SOMEONE.search(line)))
    # "should i get an engineer out" trips the "should i get" buying shape while naming no thing
    # to buy, and a line about calling someone in is never a model choice.
    shopping = SHOPPING_NOW.search(line) and not CALLING_SOMEONE.search(line)
    if not asking or (shopping and not choosing and not FAULT_NOW.search(line)):
        # "my dryer is not heating up, should i buy a new one" ticks a shopping shape while asking
        # about the machine that has gone wrong, and the answer it wants is the replace rule, not
        # a model. Only a fault in this line counts: "is it worth buying a new tumble dryer" is
        # still a model choice.
        return ""
    # "the washing machine smells of damp" then "is it worth getting someone in": the later line
    # says nothing is wrong and nothing about owning one, because both are in the line before, so
    # the fault is looked for in the earlier line too. `clean` is not used here - it also carries
    # older turns, and a fault three turns back is not this question.
    earlier = str(reading.get("earlier") or "").strip().lower()
    if not (OWNED_NOW.search(line) or need_new) and not (FAULT_NOW.search(line)
                                                         or (earlier and FAULT_NOW.search(earlier))):
        # Nothing in the line says they have one, so this is a question about buying one:
        # the shopping table answers what the machine is good for.
        return ""
    said = str(reading.get("clean") or "").lower()
    # The skill question is the same decision said another way, and it is asked in the line the
    # fault was in or in this one: "can i fix it myself" after "my washing machine is leaking"
    # was answered with the quote rule, which is about money and not about whose hands the job is
    # in (agile-poppy, #quality 7387).
    skill = SELF_JOB_NOW.search(line) and not WORTH_NOW.search(line)
    # The machine and the fault can be in the line before ("the washing machine smells of damp"
    # then "is it worth getting someone in"), which answers.py hands over as `earlier`. Those
    # words join the reading before the fault is looked for, so a fault said one line ago counts,
    # and nothing is carried over that the earlier line did not say.
    if earlier:
        said = earlier + " " + said
    if not (FAULT_NOW.search(line) or FAULT_NOW.search(said) or KEEPING_NOW.search(line)
            or reading.get("fault") or skill or need_new):
        # Nothing has gone wrong and nothing is being asked about repairing it, so "is it worth it"
        # is the buying question ("is a tumble dryer worth it"). The rule is about the one you own.
        return ""
    small = _named(line, SMALL_APPLIANCES, default=None) or _named(said, SMALL_APPLIANCES, default=None)
    if small:
        return _small_appliance(small, memory)
    garden = (_named(line, GARDEN_MACHINES, default=None)
              or _named(said, GARDEN_MACHINES, default=None))
    if garden:
        return _garden_machine(garden, memory)
    if skill:
        return _diy_decision(said, memory)
    # A machine the table does not know ("is it worth repairing my coffee machine") must not be
    # renamed a washing machine: the rule still holds, so it is worded about "it".
    thing = _named(said, WHITE_GOODS, default=None)
    name = thing or "machine"
    article = "an" if name[0] in "aeiou" else "a"
    if thing == "boiler":
        return ("A gas boiler is Gas Safe work by law: the repair itself is an engineer's job, not "
                "a DIY one, so the question is what to spend on it. Repair it while it is under "
                "about eight years old and the quote is less than half a new one; past that, or "
                "with a failed heat exchanger, put the money towards a new boiler, which will also "
                "be cheaper to run.")
    age = _age_in(line) or _age_in(said)
    if age and age >= 8:
        return pick([
            "At " + _words_of_age(age) + " the " + name + " is at the end of its life, so replace "
            "it rather than repair it: a quote for a seal or a pump on a machine that age is money "
            "towards a new one, and the next fault is already on its way.",
            "Replace the " + name + ": at " + _words_of_age(age) + " old the repair is throwing "
            "money after the next breakdown. A new one comes with a guarantee, and the running "
            "costs of a modern " + name + " are lower too.",
        ], memory)
    return pick([
        article.capitalize() + " " + name + " is worth repairing while the quote is under about "
        "half the price of a new one and it is under six or seven years old: a seal, a pump, a "
        "belt or a heating element is usually money well spent, while a failed drum bearing or "
        "control board on an old one is not. Ask how long the parts are guaranteed before you "
        "agree, and take a quote near half the price of new as the signal to replace it: an "
        "engineer who wants £80 before touching it is already half a new machine.",
        "Repair the " + name + " if it is under about six years old and the quote is less than "
        "half a new one; replace it if the repair costs more than that or it is past eight years. "
        "The wear and tear repairs (seals, belts, pumps, elements) are worth doing on a good "
        "machine, and a control board or a drum on an old one is not. Get the quote in writing "
        "with a guarantee on the parts, because that is what separates a repair from throwing "
        "money at it.",
        "The rule of thumb is half and six: repair the " + name + " while the quote is under "
        "half the price of a new one and it is under six years old, and replace it after eight "
        "years or when the repair passes that half. A seal, a pump or a heating element on a good "
        "machine is money well spent; a control board or a drum bearing on an old one is not. "
        "Ask how long the parts are guaranteed before you say yes.",
    ], memory)


# "I tweaked my back lifting boxes. Rest it or keep moving?" is a body question, and "boxes" plus
# "moving" is exactly what the two packing entries key on, so both of them name the body words.
BODY_WORDS = ("back", "backs", "lifting", "lift", "lifted", "hurt", "hurts", "hurting",
              "tweaked", "ache", "aches", "aching", "pain", "painful", "sciatica",
              "shoulder", "shoulders", "knees", "knee", "neck", "injury", "injured", "strain")

# How long the things around the house usually last, asked as "how long do washing machines
# last", "how long should a boiler last", "when should i replace my fridge". One table, so the
# lifespan is written once and every appliance is answered the same way: (names, how it is
# called in a sentence, the span). "Last" is the word that carries the question, and the food
# that keeps in the fridge has its own answer, so the fridge row is held off "how long does milk
# last in the fridge" by the guard below.
LIFESPAN = (
    (("washing machine", "washer"), "a washing machine", "eight to ten years",
     "a 60C service wash once a month, a clean filter and a drum that is never overloaded are "
     "what keep it at the top of that"),
    (("dishwasher",), "a dishwasher", "eight to ten years",
     "rinsing the filter monthly and using salt if your water is hard keeps it at the top of "
     "that"),
    (("tumble dryer", "tumbler", "dryer"), "a tumble dryer", "ten to thirteen years",
     "emptying the lint filter after every load is the whole of it, because a blocked filter is "
     "what kills dryers"),
    # a fridge, a freezer and a fridge freezer are three things in a kitchen, and the line says
    # which one: the longest name wins, so "fridge freezer" is answered as itself
    (("fridge freezer",), "a fridge freezer", "ten to fifteen years",
     "dusting the coils at the back once a year and keeping it out of a hot corner is most of it"),
    (("fridge",), "a fridge", "ten to fifteen years",
     "dusting the coils at the back once a year and keeping it out of a hot corner is most of it, "
     "and a door seal that grips a sheet of paper is what keeps the cold in"),
    (("freezer",), "a freezer", "ten to fifteen years",
     "a freezer kept full and defrosted when the ice thickens lasts longest"),
    # the same machine under three names, and the answer says the one the line used: a cooker is
    # the whole thing stood on the floor, an oven is the box, and a range cooker is the big one
    (("range cooker",), "a range cooker", "fifteen to twenty years",
     "the element and the thermostat are the parts that go and both are cheap to swap, so one "
     "fault is almost never a reason to replace it"),
    (("cooker", "stove"), "a cooker", "ten to fifteen years",
     "the element and the thermostat are the parts that go and both are cheap to swap, so one "
     "fault is almost never a reason to replace it"),
    (("oven",), "an oven", "ten to fifteen years",
     "the element and the thermostat are the parts that go and both are cheap to swap, so one "
     "fault is almost never a reason to replace it"),
    (("slow cooker",), "a slow cooker", "five to ten years",
     "the stoneware and the seal are what go first, so wash it by hand rather than in the "
     "dishwasher and do not plunge it hot into cold water"),
    # a heat pump is the one heating machine that outlasts a boiler, and "how long does a heat
    # pump last" was answered with how one works, because no row here had a heat pump to age.
    (("heat pump", "heat pumps", "air source heat pump", "ground source heat pump"),
     "a heat pump", "fifteen to twenty years",
     "an annual service and a clean filter are most of it, and the compressor and the outdoor "
     "unit are what go first"),
    (("boiler",), "a boiler", "ten to fifteen years",
     "an annual service is the whole of it, and the last third of that range is where repair "
     "bills start to beat a new one"),
    (("microwave",), "a microwave", "seven to ten years",
     "never running it empty and keeping the door seal clean is most of it"),
    (("vacuum cleaner", "hoover", "vacuum"), "a vacuum cleaner", "six to eight years",
     "emptying the bin and washing the filters is most of it; the motor is what fails in the end"),
    (("kettle",), "a kettle", "three to five years",
     "descaling it now and then is most of it, because the element is what scales up and dies"),
    (("toaster",), "a toaster", "three to five years",
     "emptying the crumb tray and never poking a knife in it is most of it"),
    (("air fryer", "airfryer"), "an air fryer", "five to eight years",
     "washing the basket by hand rather than in the dishwasher and not overfilling it are most "
     "of it, and the non-stick goes before the element does"),
    (("hob",), "a hob", "ten to fifteen years",
     "a ceramic or induction hob usually dies at the touch controls, so keep spills off them"),
    (("hair dryer", "hairdryer"), "a hair dryer", "four to six years",
     "cleaning the filter at the back is what stops it overheating"),
    (("blender",), "a blender", "three to five years",
     "not running it past a minute at a time is most of it; the motor is what goes"),
    (("sandwich maker", "toastie maker"), "a sandwich maker", "five to eight years",
     "wiping the plates and brushing the crumbs out after each use is most of it, and the hinge "
     "and the non-stick coating are what go first"),
    (("mattress",), "a mattress", "eight to ten years",
     "airing it and turning or rotating it every few months is what keeps it there"),
    # Not everything in a house that lasts for years is plugged in. "how long does a carpet last",
    # "how long does a sofa last", "how long do pans last" and "how long does a hot water bottle
    # last" were all a punt, and each of them wants the same table: one row, one span, one habit.
    (("carpet", "carpets"), "a carpet", "ten years in a room people walk through every day",
     "the underlay matters as much as the carpet, and a cheap carpet on a good underlay outlasts "
     "a good one laid straight onto the floor"),
    (("sofa", "sofas", "couch", "settee", "armchair", "suite"), "a sofa", "seven to fifteen years",
     "the frame decides it - a hardwood frame outlasts chipboard - and the cushions and covers "
     "can be replaced long before the frame goes"),
    (("frying pan", "saucepan", "pans", "wok", "cookware"), "a pan",
     "five to ten years if it is non-stick, and a lifetime if it is stainless steel or cast iron",
     "the coating is what goes first, and metal utensils and the dishwasher hurry it along"),
    (("hot water bottle", "hot water bottles"), "a hot water bottle", "two to three years",
     "the rubber perishes from the inside whether or not it is used, so go by the date on the "
     "neck rather than by how it looks"),
    (("bed frame", "bedframe", "bedstead"), "a bed frame", "ten to fifteen years",
     "a wooden frame that is glued as well as screwed, and joints tightened once a year, is what "
     "stops it creaking and wobbling before then"),
)
# What decides the end of a thing that is not a machine. The appliances share the repair-or-
# replace rule; a mattress, a carpet, a sofa and a pan have no service and no repair bill, so each
# of them says the one sign that means it is finished.
LIFE_RULE = {
    "a mattress": "Replace it once it sags or the springs go, or you wake up stiff.",
    "a carpet": "Replace it when the pile is worn through on the walkways - a professional clean "
                "brings a dirty carpet back once, not a worn one.",
    "a sofa": "Re-cover it or have the cushions refilled before you replace it: that is a "
              "fraction of the price of a new one.",
    "a pan": "Replace a non-stick one once the coating is scratched or flaking, and keep a "
             "stainless or cast iron one for good - it cleans back to itself.",
    "a hot water bottle": "Replace it at the first crack, bulge or stiff patch, and never fill one "
                          "that has sat in a cupboard for years.",
    "a bed frame": "Tighten the joints once a year and put a felt pad under a leg that wobbles "
                   "rather than waiting for the frame to work itself loose.",
}
LIFE_NAMES = tuple(name for row in LIFESPAN for name in row[0]) + ("white goods", "appliances",
                                                                  "appliance", "kitchen gadgets")
# "how long", "last" and "years" are the question; "replace" alone is the repair decision's word,
# so it only counts here with a lifespan word beside it.
LIFE_ASK = ("how long", "how many years", "last", "lasts", "lasting", "lifespan", "life span",
            "life expectancy", "expectancy", "how long will", "how old",
            # The decision to replace or repair is the same question the years table answers, and
            # it is how most people ask it: "my fridge is ten years old, is it worth replacing"
            # was answered with how to keep food cold in a power cut, and "my oven is twelve years
            # old, should i get a new one" with the composer's shrug, because neither phrasing was
            # in this key. The words are the whole ask, so a shop question still goes to shopping.
            "worth replacing", "worth repairing", "worth fixing", "worth mending",
            "worth a new one", "worth a new", "should i replace", "should we replace",
            "should i get a new", "should we get a new", "should i buy a new",
            "time for a new", "time to get a new", "need a new one", "needs a new one",
            "replace it or repair", "repair or replace", "new one or repair", "fix it or replace",
            "replace or fix", "replace or repair")
# Food keeping in the fridge is the food-safety answer: "how long does milk last in the fridge"
# names an appliance and asks about the clock, and the lifespan of the fridge is not its question.
LIFE_GUARD = ("fitting", "fitting it", "install", "installation", "deliver", "to arrive",
              "does it take", "will it take", "does fitting",
              # "how long does X take" is a duration, not a life: the appliance sits between the
              # two words, so the exact phrase above never fired and a kettle's three to five
              # years answered "how long does a kettle take to boil" (broad-berry, mint-wolf).
              "take", "takes", "taking", "boil", "heat up", "cool down", "cycle",
              "preheat", "pre-heat", "spin",
              # a service and how often it is done is its own answer
              "service", "servicing", "serviced",
              # "how long in the oven" is the cake, not the oven: an oven named for what is
              # done in it is a place, and the answer is the one for what is being cooked.
              "in the oven", "in a fan oven", "fan oven", "oven temperature", "oven heat",
              "hot oven", "bake", "baking", "roast", "roasting", "cook", "cooking", "grill",
              # Food keeping is the food answer, and it says where the food is: an appliance's
              # lifespan is never asked as "in the fridge" or "can i keep". "how long can mince
              # stay in the freezer" was getting the fridge freezer's ten to fifteen years.
              "in the fridge", "in the freezer", "in the cupboard", "in a cupboard",
              "can i keep", "can you keep", "can i store", "can it stay", "food stay",
              "stay fresh", "stays fresh", "keep for", "keeps for", "mince", "sausage",
              "bacon", "chop", "potato", "food", "leftover",
              # A consumable is not the machine: "how long does a dishwasher tablet last" is a
              # box of tablets, not ten to fifteen years of appliance.
              "tablet", "pod", "capsule", "rinse aid", "detergent", "powder", "salt", "filter",
              "bag", "bags", "sponge", "cloth", "bottle of", "cartridge",
              # "how do i make my sofa last longer" and "how long does a sofa last before it
              # sags" are care and wear questions, not the span: one wants the habit and the
              # other wants the sign it is going.
              "last longer", "last as long", "make it last", "make them last", "care for",
              "look after", "before it", "before they", "sag", "sags", "sagging", "worn",
              # and neither is a power cut: "how long does a freezer stay cold without power".
              "without power", "power cut", "stay cold", "stays cold", "keep food",
              "stay frozen", "keep it frozen",
              # "how long do you microwave porridge for" asked the bowl's minutes and got the
              # machine's seven to ten years. The food words below are the same guard as the list
              # above, and a bowl of oats is on it.
              "porridge", "oats", "oatmeal",
              "milk", "cooked", "rice", "pasta", "chicken", "meat", "beef", "pork", "fish",
              "cheese", "butter", "eggs", "egg", "yogurt", "yoghurt", "leftovers", "leftover",
              "soup", "bread", "cake", "beans", "fruit", "veg", "vegetables", "salad", "ham",
              "opened", "opening", "tin", "tinned", "shelf life", "use by", "defrosted", "thawed",
              "cooked rice", "stock")


def _spans_plural(text, names):
    """_spans, but "washing machines" names a washing machine."""
    return _spans(text, tuple(name for base in names
                              for name in (base, base + "s", base + "es")))


def _longest_row(text, table):
    """The row whose name covers the most of the line, so an alias cannot stand in front.

    The table keeps short aliases beside the full names - "dryer" for a tumble dryer, "washer"
    for a washing machine - and the first match in table order reads the alias inside a longer
    name: "how long does a hair dryer last" was answered about a tumble dryer, because bare
    "dryer" comes first and matches inside "hair dryer". Longest wins, and a tie keeps table
    order, which is how "fridge freezer" beats the bare "fridge" in the same row.
    """
    best, found = "", None
    for row in table:
        for name in row[0]:
            if len(name) > len(best) and _spans_plural(text, (name,)):
                best, found = name, row
    return found


# "how long do i ...", "how long should i ...": the person asks what they do, not how long the
# machine lasts. Only a word about years makes it a question about the machine's life.
_FIRST_PERSON = re.compile(r"\b(?:i|im|i'm|my|me|we|us|our)\b|\bhow\s+long\s+to\b", re.I)
# "how long does a freezer stay cold without power" holds what is in it, which the keeping and
# power-cut tables answer; "how long does a mattress stay good for" and "how long will a mattress
# stay comfortable" are the same life question in other words, and "hold water" is a fault. So
# the verb only stands the years row down when the line also names what is being held.
_HOLDS = re.compile(r"\b(?:stay|stays|staying|hold|holds|holding)\b", re.I)
_HOLDS_A_THING = re.compile(r"\b(?:cold|hot|warm|frozen|chilled|cool|ice|heat|power|off|outage|without|temperature)\b", re.I)
_A_LIFE = re.compile(r"\b(?:last|lasts|lasting|lasted|life|lifespan|life\s*span|expectancy|"
                     r"expect|years?|old)\b", re.I)
# The same question in the language people use for it: "when should i replace my mattress" asks
# how long it is good for and what says it is finished, not which one to buy next. The words are
# the whole ask ("when to replace", "should i replace"), never "replace" alone, which is the
# repair-or-replace sum's word - "when should i replace my washing machine" is that card's line
# and must keep it.
_WHEN_TO_REPLACE = re.compile(
    r"\bwhen\s+to\s+replac|\bwhen\s+(?:should|shall|do|does|would)\s+(?:i\s+|we\s+|you\s+)?replac"
    r"|\bshould\s+(?:i|we|you)\s+replac|\btime\s+to\s+replac|\btime\s+(?:for|i)\s+"
    r"(?:a\s+)?(?:new|replac)|\bneed\s+a\s+new\b", re.I)


def _lifespan(memory, understood):
    """How long the appliance lasts, from the one table.

    The machine has to be named in this line. A follow-up is read with the turns before it put
    back in, so "and how long does fitting take" after a boiler question was answered with the
    washing machine's lifespan: the boiler was in the memory, not in the question.
    """
    line = str(understood.get("text") or understood.get("clean") or "")
    earlier = str(understood.get("earlier") or "")
    # A machine named in a line about what the person does with it ("how long should i microwave
    # porridge", "how long to microwave oats") is the machine being used, not a machine being
    # aged: the microwave is the verb there. "how long" plus a first person is how the language
    # asks for a duration, so without a word about years there is no life being asked about.
    if (_FIRST_PERSON.search(line) and not _A_LIFE.search(line)
            and not _WHEN_TO_REPLACE.search(line)
            and not _spans_plural(line, ("white goods", "appliances", "appliance"))):
        return ""
    # The machine named as a place is the cupboard, not the thing being aged: "how long do apples
    # last in the fridge" was reaching the fridge's ten to fifteen years here, because the other
    # appliance-life row was fenced off and this one was not. The shape is the same fence.
    if _named_as_a_place(line.lower(),
                         tuple(word for word, _called in WHITE_GOODS + SMALL_APPLIANCES)):
        return ""
    if re.search(r"\bbe\b\s*\??\s*$", line.lower()) and not _A_LIFE.search(line):
        # "how long should a sofa be", "how long should curtains be": a measurement, and nothing
        # that lasts is asked in that shape. The years row finally had a sofa to offer and took
        # the length question with it.
        return ""
    if _HOLDS.search(line) and _HOLDS_A_THING.search(line) and not _A_LIFE.search(line):
        # "how long does a hot water bottle stay warm" holds its heat, and the thing that lasts
        # two or three years is the rubber, not the warmth. Same fence as the row below, because
        # both tables answer "how long does a X last" and either of them can take the line.
        return ""
    row = _longest_row(line, LIFESPAN)
    if row is None and earlier:
        # "how long do they usually last" after "my washing machine is nine years old": the
        # machine is the one in the line before, and only that one, not the whole memory.
        row = _longest_row(earlier, LIFESPAN)
    if row is None and not _spans_plural(line, ("white goods", "appliances", "appliance",
                                                "kitchen gadgets")):
        return ""
    rule = ("Repair it while a fix is well under half the price of a new one, and replace it once "
            "it needs two repairs in a year.")
    if row and row[1] in LIFE_RULE:
        # a mattress, a carpet, a sofa and a pan are not machines: there is nothing to service and
        # no repair bill to weigh, so the sentence about replacing it says the one thing that
        # decides it instead of the appliance rule.
        rule = LIFE_RULE[row[1]]
    if row:
        return pick([
            f"{row[1].capitalize()} lasts about {row[2]} if it is looked after: {row[3]}. " + rule,
            # "Expect a fridge to last about ten to fifteen years": the word "last" in both
            # wordings is what makes the answer say how long the thing lasts, and the keeping
            # reader in front of the lookup keeps only a reply that does. Without it the answer
            # was accepted or dropped at random, and when it was dropped the question about the
            # machine was answered by whatever keeps in a fridge.
            f"Expect {row[1]} to last about {row[2]} - {row[3]}. " + rule,
        ], memory)
    return ("Washing machines and dishwashers last about eight to ten years, a fridge freezer, "
            "oven or tumble dryer ten to fifteen, and a kettle or a toaster three to five. "
            + rule)


# What the things around the house cost to run, in pence, at about 24p a unit (Britain, 2024).
# One table, so "is it cheaper to run the dishwasher or wash by hand" is answered however the
# two are named, and a figure only has to be right once. Each row is (names, pence, label,
# detail): the label is how the thing is called in a sentence, the detail is the cost itself,
# so one row reads as a whole answer and two rows read as a comparison.
RUNNING = (
    (("fan", "desk fan", "tower fan", "standing fan"),
     2, "a fan", "a penny or two an hour, and it cools you rather than the room"),
    (("air fryer", "airfryer"),
     18, "an air fryer", "about 15 to 20p an hour, and it is hot in three minutes"),
    (("oven", "fan oven", "electric oven", "double oven"),
     50, "an electric oven", "about 50p an hour at 180C, and much of that is the warm-up"),
    # Gas is about a quarter of the price of electricity for the same heat, and people ask the
    # pair question ("is it cheaper to run a gas oven or electric") as often as the single one.
    # The figure carries the comparison with it, because a line that says "or electric" names
    # only one of the two rows and still wants the verdict.
    (("gas oven", "gas cooker"),
     22, "a gas oven", "about 20 to 25p an hour at 180C, roughly half what an electric oven "
                        "of the same size costs"),
    (("gas hob", "gas ring", "gas burner"),
     12, "a gas hob", "roughly 10 to 15p an hour of use, the cheapest of the hobs"),
    (("electric hob", "electric ring", "ceramic hob", "halogen hob"),
     30, "an electric hob", "about 25 to 35p an hour, and more if the pan is smaller than the "
                             "ring"),
    (("induction hob", "induction cooker"),
     16, "an induction hob", "about 15 to 20p an hour, close to gas and about twice as quick to "
                              "boil"),
    (("microwave", "microwave oven"),
     5, "a microwave", "pennies for a reheated plate, because it runs for minutes not hours"),
    (("slow cooker", "crockpot"),
     2, "a slow cooker", "a couple of pence an hour, so around 15p for a whole afternoon"),
    (("dishwasher",),
     22, "a dishwasher", "about 20 to 25p a cycle on eco, water and all"),
    (("washing up by hand", "wash by hand", "washing by hand", "washing up", "by hand"),
     8, "washing up by hand", "roughly 5 to 10p of gas to heat a bowl, and 20p or more if the "
                              "hot water is electric"),
    (("tumble dryer", "tumbler", "heat pump dryer", "heat pump drier",
      "heat pump tumble dryer", "vented dryer", "condenser dryer"),
     30, "a tumble dryer", "about 25p a cycle with a heat pump and more like 60p with a vented one"),
    (("dehumidifier",),
     7, "a dehumidifier", "about 7p an hour, and it dries a room by running longer rather than hotter"),
    (("electric heater", "fan heater", "convector heater", "oil heater", "oil filled radiator",
      "space heater"),
     48, "an electric heater", "about 45 to 50p an hour whatever the type, because they all turn "
                               "electricity into heat the same way"),
    (("kettle",),
     3, "a kettle", "about 2 to 3p a boil, so boil only what you are going to drink"),
    (("washing machine",),
     25, "a washing machine", "about 25p a cycle at 40C and nearer 15p at 30C"),
    # A bath and a shower are not appliances, but they are the same question, and they had no
    # row: "how much does a bath cost to run" and "how much does it cost to run a shower" were
    # both answered by the used-car running-cost row in money.py. Heating the water is nearly
    # all of the bill, so each figure is one use of it: 80 litres raised about 35C is 3.3 kWh
    # of heat, and five minutes at 40 litres is 1.6 kWh.
    (("bath", "baths", "bathtub", "hot bath"),
     30, "a hot bath", "about 25 to 30p of gas for 80 litres, and nearer 60 to 80p if the water "
                       "comes from an electric immersion"),
    (("shower", "showers", "showering"),
     15, "a shower", "roughly 10 to 15p for five minutes on a gas boiler, and 15 to 20p on an "
                     "electric shower, which heats its own water as it goes"),
    (("central heating", "the heating", "heating on", "gas heating", "radiator", "radiators",
      "boiler", "combi"),
     60, "gas central heating", "about 60p an hour while the boiler is actually firing, so five "
                                 "hours a day is £2 to £3, and a heat pump or electric heating is "
                                 "cheaper per unit of heat only if it is a real heat pump"),
    (("electric blanket", "heated blanket"),
     2, "an electric blanket", "a penny or two for an evening, and far cheaper than heating the room"),
    (("vacuum cleaner", "hoover", "vacuum"),
     30, "a vacuum cleaner", "about 25 to 50p an hour, though you rarely run one for an hour"),
    (("air conditioning", "air con", "aircon", "air conditioner"),
     40, "a portable air conditioner", "30 to 50p an hour, and a fitted one more than that"),
    (("fridge freezer", "fridge", "freezer"),
     1, "a fridge freezer", "about 25p a day, which works out near a penny an hour because it "
                             "only ticks over"),
)

# What the thing in the row costs to BUY, which is the other half of "how much does a washing
# machine cost". Every one of these lines was answered with the running figure: "how much does an
# air fryer cost" was "about 15 to 20p an hour", and a person pricing a purchase was told what it
# would add to the bill instead of what it costs in the shop. The figure is a band, because a
# price is a band and not one number, and the label is the same label the running row uses.
# A row with no entry here is a thing nobody buys by the unit - a bath, a shower, a boiler firing -
# so those keep the running figure alone.
PRICE_OF = {
    "an air fryer": "An air fryer is £40 to £120: a 4 to 5 litre one is £70 to £90 and is the size "
                    "most people use, and a two-drawer one is £120 to £200.",
    "a microwave": "A freestanding microwave is £60 to £150, and £150 to £250 buys a combi or a "
                   "flatbed one; a built-in model is £250 upwards plus fitting.",
    "a fan": "A pedestal or tower fan is £25 to £80, and a good one moves the same air as a cheap "
             "one for half the noise. A portable air conditioner, which actually cools, is "
             "£250 to £500.",
    "a tumble dryer": "A vented tumble dryer is £250 to £400, a condenser £300 to £500, and a heat "
                      "pump £350 to £600 - the dearer one pays the difference back in about two "
                      "years of running costs.",
    "a dehumidifier": "A 12 to 20 litre dehumidifier is £150 to £250, and a desiccant one for a "
                      "cold garage or a flat that never warms up is £200 to £300.",
    "a vacuum cleaner": "A corded vacuum is £100 to £250, and a cordless one £150 to £400 with the "
                        "battery being most of the price - check what a replacement battery costs "
                        "before you buy.",
    "a fridge freezer": "A fridge freezer is £400 to £700 for a frost-free 50/50 model, and "
                        "£700 to £1,200 for an American-style one; measure the gap and the door "
                        "swing first.",
    "an electric oven": "A built-in electric oven is £300 to £600, and a range cooker £700 to "
                        "£2,000; fitting is usually £60 to £120 on top.",
    "a dishwasher": "A freestanding dishwasher is £300 to £500, and £450 to £700 for a quieter one "
                    "with a cutlery tray; integrated models cost about the same plus a door panel.",
    "an electric blanket": "An electric blanket is £40 to £80 for a single and £60 to £120 for a "
                           "double, and one with separate controls and a timer is worth the extra.",
    "a kettle": "A kettle is £25 to £60; a 3kW one boils about twice as fast as a 1.7kW one, which "
                "matters more than the shape of the spout.",
    "a slow cooker": "A slow cooker is £30 to £70, and a 3.5 to 6 litre one with a sear setting "
                     "covers most households.",
    "a washing machine": "A new basic washing machine is about £300 to £400, and £450 to £600 buys "
                         "a quieter one with a bigger drum and a longer guarantee. Refurbished from "
                         "a dealer is £180 to £250, and a private sale £80 to £150 with no "
                         "guarantee.",
}

# The names the table knows and the words that make a line a question about cost, so the
# entry is one key and this table is the only place either list lives.
RUNNING_WORDS = tuple(name for row in RUNNING for name in row[0])
# "much", "more" and "worth" are deliberately absent: "how much water for two cups of tea" and
# "is it worth getting an air fryer" are a quantity and a buying question, not a running cost.
# "run" and "running" are deliberately absent too: they are what a machine does, so a state line
# ("the washing machine is running") would claim them, and every cost question that matters says
# "cost" or "cheaper" anyway.
COST_WORDS = ("cheaper", "cheap", "cheapest", "cost", "costs", "electricity", "expensive",
              "save", "saving")

# How a pair is summed up once both costs are known: the heat is the bill, so whatever is
# smaller and quicker is the cheaper way to do the same job.
RUNNING_TAIL = "The heat is nearly all of the cost, so fill whatever you use and skip the preheat."
# Only a pair of things you cook in ends with that: a dryer and a dehumidifier share no preheat.
COOKING = ("an electric oven", "an air fryer", "a microwave", "a slow cooker")


def _spans(text, names):
    """(start, end) of the longest name in the line, or None."""
    best = None
    for name in names:
        match = re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", text)
        if match and (best is None or match.end() - match.start() > best[1] - best[0]):
            best = (match.start(), match.end())
    return best


def running_costs(text):
    """The RUNNING rows the line names, in the order it names them."""
    found = []
    for row in RUNNING:
        span = _spans(text, row[0])
        if span:
            found.append((span, row))
    # "fan oven" names the oven, not a fan, and "fan heater" is not a fan: drop any name that
    # sits inside a longer one.
    kept = [item for item in found
            if not any(other[0][0] <= item[0][0] and item[0][1] <= other[0][1]
                       and other[0] != item[0] for other in found)]
    kept.sort(key=lambda item: item[0][0])
    return [row for _span, row in kept]


# "i keep running to the loo" is a symptom, not a cistern. The toilet row's key holds "running"
# because a cistern runs, and "keeps" too, so a line about a person going reached the plumbing
# answer with both halves of its key although nothing in it is about water. The row already holds
# avoid phrases for the "i need the loo" half of the same collision; this is the going half, and it
# is a reading of the whole line rather than a word list, because "the toilet keeps running" and
# "i keep running to the toilet" differ only in which of them is the subject.
_GOING_TO_THE_LOO = re.compile(
    r"\b(?:i|im|i'm|ive|i've|we|were|we're)\b[^.?!]{0,28}?"
    r"\b(?:run|runs|running|ran|rush|rushes|rushing|dash|dashing|nip|nipping|pop|popping|"
    r"go|goes|going|went|walk|walking|need|needs|needing|needed|up and down)\b[^.?!]{0,20}?"
    r"\b(?:to|into|for|out of)\s+(?:the\s+|my\s+)?"
    r"(?:loo|toilet|toilets|bathroom|bog|john|restroom|washroom|lavatory)\b", re.I)
# "i was in and out of the loo all night" has no verb of going in it at all: the pair of
# prepositions is the going.
_IN_AND_OUT_OF_THE_LOO = re.compile(
    r"\b(?:in and out of|up and down to|back and forth to)\s+(?:the\s+|my\s+)?"
    r"(?:loo|toilet|toilets|bathroom|bog|john|restroom|washroom|lavatory)\b", re.I)
# "i was up all night with it" and "every twenty minutes" name the going without a verb that
# reaches the loo: the count is what makes it a symptom rather than a plumbing fault.
_EVERY_FEW_MINUTES = re.compile(
    r"\b(?:every|each)\s+(?:\d+|five|ten|fifteen|twenty|thirty|few|fewer|half an hour|hour)\b"
    r"[^.?!]{0,30}?\b(?:loo|toilet|toilets|bathroom|bog|john|restroom|washroom)\b", re.I)


def _going_to_the_loo(understood):
    """False when the line is about the person going to the loo, not about the cistern."""
    clean = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    return not (_GOING_TO_THE_LOO.search(clean) or _IN_AND_OUT_OF_THE_LOO.search(clean)
                or _EVERY_FEW_MINUTES.search(clean))


# "cost" is also what a thing costs to buy, and the running rows claimed every one of those
# lines: "how much does a washing machine cost" and "how much does an air fryer cost" were told
# the pence per cycle or per hour, which is the answer to a different question. A price ask says
# "how much" and names the thing; a bill ask says what the cost is FOR - to run it, a cycle, an
# hour, a month - or compares two of them. So the line's own words decide which half of the row
# answers, and the purchase band comes first when the price is the question.
_WHAT_IT_IS_FOR = (
    "run", "runs", "running", "ran", "to use", "using", "use it", "cycle", "cycles", "wash",
    "load", "loads", "boil", "boils", "boiling", "hour", "hours", "minute", "minutes", "day",
    "days", "week", "weeks", "month", "months", "night", "overnight", "per", "a go", "each go",
    "electricity", "energy", "kwh", "unit", "units", "standby", "left on", "leave it on",
    "keep it on", "on all day", "all day", "bill", "bills", "quarter", "year",
)
_A_COMPARISON = ("cheaper", "cheap", "cheapest", "expensive", "more than", "less than", "save",
                 "saving", "savings", "compare", "comparison", "rather", "worth running",
                 "worth leaving", "better than", "worse than")
# Whole words only: "wash" sits inside "washing machine" and "dishwasher", so a substring test
# read every one of those price questions as a question about using it.
_A_COMPARISON_SAID = re.compile(r"(?<![a-z])(?:" + "|".join(
    re.escape(word) for word in _A_COMPARISON) + r")(?![a-z])")
_WHAT_IT_IS_FOR_SAID = re.compile(r"(?<![a-z])(?:" + "|".join(
    re.escape(word) for word in _WHAT_IT_IS_FOR) + r")(?![a-z])")
# The words that ask the price of the thing rather than the price of using it.
_THE_PRICE_OF = re.compile(
    r"\b(?:how much (?:does|do|is|are|would|will)|what (?:does|do|is|are) (?:a|an|the|one)|"
    r"price of|prices of|cost of (?:a|an|the)\b|cost to buy|how much for|what do (?:a|an|the)\b)",
    re.I)


def _names_the_thing(clean, label):
    """True when the line says the thing the band is for, not a word that merely resembles it.

    The chat writes its subject back into a follow-up ("how much do they cost" after a washing
    machine has gone arrives as "how much do my washing cost"), so a row that matched on one loose
    word was enough to answer a question about a launderette with the price of a machine. Every
    word of the band's own name has to be said: "washing" alone is not "a washing machine".
    """
    words = [word for word in str(label or "").lower().split() if word not in ("a", "an", "the")]
    if not words:
        return False
    text = " " + str(clean or "").lower() + " "
    return all(re.search(r"(?<![a-z])" + re.escape(word), text) for word in words)


def _asks_the_price(text):
    """True when the line is the price of the thing, not the price of running it."""
    clean = " " + (text or "").lower() + " "
    if not _THE_PRICE_OF.search(clean):
        return False
    if _A_COMPARISON_SAID.search(clean):
        return False
    return not _WHAT_IT_IS_FOR_SAID.search(clean)


def _running(memory, understood):
    """Compare the running costs of the things the line names, or give one thing its figure."""
    clean = understood.get("clean") or ""
    rows = running_costs(clean)
    if not rows:
        return None
    first = rows[0]
    if len(rows) == 1:
        # A price ask gets the band it costs in the shop, and then the figure for using it,
        # because a person who asks what a tumble dryer costs is usually weighing both.
        band = PRICE_OF.get(first[2])
        if band and _asks_the_price(clean) and _names_the_thing(clean, first[2]):
            return f"{band} To run it, it is {first[3]}."
        return f"{first[2].capitalize()} is {first[3]}."
    second = rows[1]
    cheaper, dearer = (first, second) if first[1] <= second[1] else (second, first)
    # The verdict first, then both figures, then the one rule that follows from them, when the
    # two things share a job and a warm-up.
    tail = f" {RUNNING_TAIL}" if cheaper[2] in COOKING and dearer[2] in COOKING else ""
    return (f"{cheaper[2].capitalize()} is the cheaper one, {cheaper[3]}; "
            f"{dearer[2]} is {dearer[3]}.{tail}")


# A stain in a rented home is a deposit question more often than a cleaning one: "deduction for a
# stain on the sofa, is that fair" wants to know who pays, and answering it with blotting
# instructions is worse than useless. `boiler-broken` already stands aside for the same words; the
# furnishing entries need it too.
#
# Only the money words are here. "landlord", "tenancy" and "moving out" are words a *cleaning*
# question uses as well - "my landlord says the carpet needs cleaning", "how do i get a stain out
# of a carpet before i move out" - and standing the cleaning answer aside for them takes the answer
# away from a person who still has to clean it. The pairing is done by `damage-deduction` below,
# which needs a stain and a money word in the same line.
LETTING = ("letting agent", "deposit", "deduct", "deducted", "deducting", "deduction",
           "deductions", "withheld", "withhold", "withholding", "wear and tear", "end of tenancy")
# What a machine's noise means, one record per appliance: the ordinary sounds and why they
# happen, the one or two sounds that point at a known fault, and the line where it stops
# being ordinary. A record without a sentence for a sound just gets the ordinary part, so a
# new appliance is a few lines of data and no new matching.
# NOISE_WORDS, the plain words for "it is making a noise", lives in wording.py because the
# neighbour-noise row reads it too: one list for every row that answers a noise.

# The sounds are the same sounds on every machine, and the washer's own table below used to know
# more of them than this one did: "my washing machine is screeching" was answered and "my tumble
# dryer is screeching" was met with a nod, because `screech` and `shriek` were in the washer's
# list only. A screech and a shriek are the same belt as a squeal, and a clunk or a clank is the
# same loose thing as a rattle, so the two families are here now.
NOISE_KINDS = (
    ("grind", ("grind", "scrap", "roar", "rumbl")),
    ("squeak", ("squeak", "squeal", "screech", "shriek", "scream", "whine", "whistl")),
    ("knock", ("knock", "bang", "thump", "hammer")),
    ("rattle", ("rattl", "vibrat", "shak", "clunk", "clank")),
    ("click", ("click", "tick")),
    ("gurgle", ("gurgl", "glug")),
    # last, so any named sound above wins: a bare "noisy" only gets a sentence where the
    # general answer really is the fault most of the time (a scaled kettle, a greasy oven fan)
    ("loud", NOISE_WORDS),
)

NOISE_TABLE = (
    {"words": ("dishwasher", "dish washer"),
     "normal": ("A hum from the dishwasher is the wash pump and the whoosh at the start is it "
                "draining, both ordinary."),
     "kinds": {"grind": ("Grinding is usually the filter or a bit of glass in the sump: take out "
                         "the bottom basket, unscrew the filter and rinse it, and check the spray "
                         "arms turn freely."),
               "rattle": ("A rattle is normally cutlery in the basket or a spray arm fouling the "
                          "rack."),
               # a bang is not ordinary noise, so it is not answered with the hum and the whoosh:
               # something is moving that should not. "the dishwasher bangs when it drains" was
               # told its sounds were ordinary, which is a shrug at the fault it named.
               "knock": ("A bang is something moving that should not: stack pans so nothing can "
                         "touch a spray arm, check both arms spin freely and are not split, and "
                         "reseat the filter and the sump cover, because a gap there lets things "
                         "jump under the water. A bang only when it drains, or a thud as the pump "
                         "starts, is usually something in the drain pump: take out the bottom "
                         "basket, unscrew the filter and feel inside the sump for glass or a "
                         "stone.")},
     "urgent": "Water on the floor means pull the plug and stop using it."},
    {"words": ("tumble dryer", "dryer"),
     "normal": "A steady rumble from the tumble dryer is the drum turning, which is ordinary.",
     "first": (("shake", ("shak", "vibrat")),),
     "kinds": {"squeak": ("A squeak is the belt or a drum roller, so clean the filter and feel "
                          "round the drum."),
               "rattle": ("A rattle is usually coins or a bra wire in the drum: empty the "
                          "pockets and feel round the inside of it."),
               # A dryer is the one machine here whose shake is not something loose inside it:
               # it is the load and the feet. This record names "shake" before the shared
               # table, so "my tumble dryer is shaking" leads with the load, while "my dryer is
               # making a rattle noise" still gets the drum. A dryer has no transport bolts, so
               # the levelling steps written for a washer are not the answer either.
               "shake": ("A dryer that shakes is nearly always the load or the feet: undo the "
                         "tangle, put a couple of towels in with a heavy item, and turn the "
                         "front feet out until it sits flat and cannot rock. If it still walks, "
                         "an overloaded drum or the machine touching a cupboard is the next "
                         "thing to check - and a dryer has no transport bolts to undo."),
               "grind": "Grinding means stop using it: something metal has got past the filter."},
     "urgent": ("Lint round the heater is a fire risk, so clear the filter after every load.")},
    {"words": ("oven fan", "oven"),
     "normal": ("The fan running on after the oven is switched off is it cooling itself, which is "
                "ordinary."),
     "kinds": {"rattle": "A rattle is usually a bent blade or baked-on grease on the fan.",
               "squeak": "A squeal is the fan motor, which is an engineer's job.",
               "loud": "A noisy fan is usually baked-on grease throwing it off balance, which a "
                       "good clean fixes."},
     "urgent": "If the oven also heats unevenly, the fan is the thing to have looked at."},
    {"words": ("kettle",),
     "normal": "A rumble as it comes to the boil is ordinary.",
     "kinds": {"rattle": ("A loud crackle or a furred element is scale: descale with vinegar or "
                          "citric acid and it quietens down."),
               "loud": ("A noisy kettle is nearly always scale on the element: descale with vinegar "
                        "or citric acid and it quietens down."),
               "click": ("Clicking off before it boils is a scaled or worn switch, which is not "
                         "worth repairing.")},
     "urgent": "Unplug it before you descale, and never fill above the max line."},
    {"words": ("microwave",),
     "normal": ("A hum is the microwave's transformer and fan, and a clunk is the turntable, all "
                "ordinary."),
     "kinds": {"rattle": "A rattle is usually the turntable roller or the plate not seated.",
               "squeak": "A squeak from the turntable motor is harmless until the plate stops "
                         "turning."},
     "urgent": ("A loud buzz with no heat, a burning smell, or sparking at the door mesh means "
                "stop using it.")},
    {"words": ("vacuum", "hoover"),
     "normal": "A high whine from a vacuum is a blocked hose or a full bag.",
     "kinds": {"rattle": "A rattle is something caught in the brush bar: cut the hair off it.",
               "squeak": ("A squeal from the brush bar is hair wound round the roller: cut it off "
                          "with scissors and the noise goes.")},
     "urgent": "A burning smell means switch off: the motor is overheating."},
    # A fan hums because that is what it does, so the answer is "normal, unless". Last in the table:
    # "oven fan" and "extractor fan" name their own machine and must not be read as a plain fan.
    {"words": ("fan", "fans", "ceiling fan", "desk fan", "pedestal fan", "floor fan"),
     "normal": ("A fan hums because that is the motor and the moving air, so a steady low hum is "
                "the fan working: on a hot night it is louder than you expect because the room is "
                "silent and it is running all night."),
     "kinds": {"rattle": ("A rattle is usually the guard or a dusty blade: unplug it, wipe the "
                          "blades and the grille, and check the nut on the blade is tight."),
               "squeak": ("A squeal or a screech is the bearing drying out, which a drop of "
                          "machine oil on the motor spindle often fixes, and a fan that still "
                          "squeals wants replacing."),
               "grind": "Grinding means stop using it: the bearing has gone.",
               # a click is the guard or a blade working loose, the same fix as the rattle, and
               # the hum paragraph is no answer to it
               "click": ("A click is usually the guard vibrating against the housing or a blade "
                         "nut working loose: unplug it and tighten both.")},
     # Two sentences, not one: the follow-up path narrows a repeated answer to the clause that
     # shares a word with the new line, so a single sentence joined by ", and" came back as
     # "And stop using a fan whose plug or cable gets hot" with no subject in front of it.
     "urgent": ("Unplug it before you touch the blades. Stop using a fan whose plug or cable gets "
                "hot.")},
)


def _says(said, word):
    return re.search(r"\b" + re.escape(word) + r"\b", said) is not None


def _noise_kind(said, record=None):
    # A record can name a sound of its own before the shared table: on every machine here a
    # shake is something loose inside it, but on a dryer it is the load and the feet.
    for kind, stems in (record or {}).get("first", ()):
        for stem in stems:
            if re.search(r"\b" + stem, said):
                return kind
    for kind, stems in NOISE_KINDS:
        for stem in stems:
            if re.search(r"\b" + stem, said):
                return kind
    return ""


# One answer per sound a washing machine makes when the fault is not the load. Each is its own
# paragraph on purpose: a machine that grinds, squeals or rattles needs a different next step,
# and the row above for the load would have bolted the levelling onto all three.
_WASHER_SOUND_ANSWERS = {
    "grind": ("Grinding or scraping means stop using it and find the metal: a bra wire, a coin or "
              "a key gets past the drum and grinds against the outer tub. Pull the plug out, turn the drum by hand and listen, feel round the inside "
              "through the door, and empty the filter and the coin trap behind the kick plate. If "
              "it grinds only on the spin, with the drum turning freely by hand, that is the drum "
              "bearing rather than something loose, and on a machine past six or seven years it "
              "is usually the end of the machine rather than a repair."),
    "squeak": ("A squeal or a screech is nearly always the drive belt, which is a cheap part and "
               "the usual cause: it slips on the spin, loudest with a heavy load. Stop using it if "
               "there is a burning smell with the noise, because that is the belt rubbing rather "
               "than slipping."),
    "rattle": ("A rattle is something loose in the drum rather than a fault in the motor: empty out "
               "the pockets that went through the wash, feel round the inside of the drum for a bra "
               "wire or a coin, and check the filter and the coin trap behind the kick plate."),
}

# The stems are checked in this order, and the machine's own words are not in them: the row's key
# has already said which machine and which sound, so this only decides which of the three.
_WASHER_SOUND_STEMS = (
    ("grind", ("grind", "scrap", "roar", "rumbl")),
    ("squeak", ("squeak", "squeal", "screech", "shriek", "whine", "whistl")),
    ("rattle", ("rattl", "clunk")),
)


def _washer_sound_fault(memory, understood):
    """Which fault a washing machine's sound names, or the grind when it names none of them."""
    said = str((understood or {}).get("clean") or "").lower()
    for kind, stems in _WASHER_SOUND_STEMS:
        if any(re.search(r"\b" + stem, said) for stem in stems):
            return _WASHER_SOUND_ANSWERS[kind]
    return _WASHER_SOUND_ANSWERS["grind"]


def _a_dryer_is_not_a_washer(understood):
    """True when the machine whose drum is making the sound is a washing machine.

    "drum" is one of the row's key words, and a tumble dryer and a dishwasher have a drum too, so
    `the drum in my tumble dryer is grinding` was given the washer's answer: it says to empty the
    coin trap behind the kick plate, and a dryer has no kick plate. A line that names a washer
    dryer keeps the row, because the washing half of it is the same machine.
    """
    said = " " + str((understood or {}).get("clean") or "").lower() + " "
    if re.search(r"\b(washer|washing)\b", said):
        return True
    return not any(word in said for word in ("dryer", "tumble", "dishwasher"))


# A bang is the one sound no machine makes when it is well, so a record that has no sentence for
# a knock does not fall through to the ordinary paragraph: `my tumble dryer thumps` and `the dryer
# is banging` were told "A steady rumble from the tumble dryer is the drum turning, which is
# ordinary", which is a shrug at the fault the person named. The dishwasher's own knock sentence
# above is better where it applies, so this is only the fallback.
_A_BANG_IS_A_FAULT = (
    "A bang is not a sound a machine makes when it is well: something is loose inside it or is "
    "being hit, so empty it and find that before you run it again. Turn the part that moves by "
    "hand and listen for where the noise is, and check the machine stands level and is not "
    "touching the cupboard or the wall beside it. A machine that still bangs empty and standing "
    "flat wants an engineer rather than another load.")


def _appliance_noise(memory, understood):
    """What the noise means for the appliance the line names.

    A line that names the sound gets the sentence for that sound first - it is the question -
    and the ordinary sounds after it, so the fault is not buried under what is normal. A line
    that only says "noisy" or "loud" has named nothing, so the ordinary sounds come first.
    """
    said = str((understood or {}).get("clean") or "").lower()
    for record in NOISE_TABLE:
        if any(_says(said, word) for word in record["words"]):
            break
    else:
        return None
    kind = _noise_kind(said, record)
    advice = record["kinds"].get(kind) if kind else None
    if not advice and kind == "knock":
        advice = _A_BANG_IS_A_FAULT
    if advice and kind != "loud":
        parts = [advice, record["normal"]]
    else:
        # a bare "noisy" is the ordinary sounds first, then the one thing that usually is
        # wrong (a scaled kettle, a greasy oven fan)
        parts = [record["normal"]] + ([advice] if advice else [])
    parts.append(record["urgent"])
    return " ".join(parts)

# A key that is stiff belongs to whatever it is the key for, and the conversation is what says
# which: "it clicks when i turn the key" after a line about a car is the car, and the door
# table has nothing for it. A line that names the door or the lock is always this answer.
_ELSEWHERE_KEY = ("car", "cars", "van", "bike", "bicycle", "motorbike", "scooter", "laptop",
                  "computer", "suitcase", "padlock", "garage", "safe", "keyboard")
_NAMES_A_LOCK = ("door", "doors", "lock", "locks", "barrel", "deadlock", "yale", "latch",
                 "keyhole", "front", "back")


def _recent_said(memory):
    """Everything the last few turns and the running topic said, lower case, as one string."""
    parts = []
    topic = memory.get("topic")
    if isinstance(topic, dict):
        parts.append(str(topic.get("text") or ""))
        parts.extend(str(word) for word in topic.get("words") or ())
    history = memory.get("turns") or []
    for one in history[-4:]:
        if isinstance(one, dict):
            parts.append(str(one.get("user") or ""))
    return " ".join(parts).lower()


LOCK_STIFF_REPLY = (
    "Puff graphite powder, or a PTFE dry lubricant, into the keyhole and work the key in and out "
    "a dozen times: that is the fix for a stiff barrel, and unlike oil or grease it does not "
    "collect grit. If it went hard to turn all at once, try the spare key first, because a worn "
    "or slightly bent key is the usual cause and a copy cut from the spare solves it. WD-40 frees "
    "a seized lock, but finish with graphite. If the key snaps off inside, or the barrel spins, "
    "that is a locksmith, and keep the door on the latch until they come.")


# Keys that are gone are not a lock that is stiff: `door-lock-stiff` passes on "lost", so this
# entry owns the line. The two useful answers are different, so one reply reads the line for a
# vehicle, the way the washer and the vacuum split on the appliance named.
CAR_KEY_LOST_RE = re.compile(
    r"\b(?:car|van|motorbike|motorcycle|vehicle|keyless|fob|fobs)\b", re.I)

# "i cant find my keys" is the commonest way people say it, and the keys are usually in the house:
# the search comes first and the spare and the barrel are what to do once it has failed. The order
# matters - opening on the barrel tells someone who has simply mislaid them to spend £60 to £120.
LOST_HOUSE_KEYS_REPLY = (
    "Retrace the last hour in order and check the boring places again - coat pocket, under the car "
    "seat, the last counter you were at. If they are really gone: the spare first, then whoever "
    "else has a set, and with no spare change the barrel rather than hope, which a locksmith does "
    "for about \u00a360 to \u00a3120. If the ring had your address on it, do that today.")

LOST_CAR_KEYS_REPLY = (
    "Search the car properly before anything else - between the seats, the door pocket, the boot, "
    "and the pockets of the coat you wore. If it is gone, a car key is a dealer or an auto "
    "locksmith job: about \u00a3150 to \u00a3250 to cut and code a new one, and you need the V5 and "
    "photo ID. If it was stolen rather than mislaid, ring your insurer before you replace it, "
    "because theft cover often pays.")


# "i keep losing my keys" is not one loss, it is the same loss again, and the fix for that is
# the place they live, not another search: told to retrace the last hour, a person who has done
# this five times hears the answer they already know. "keep" and "always" say it is a habit;
# "again" says it has happened before. One loss is still the search first.
# The recurrence is said two ways: a habit word ("keep", "always", "over and over") and a
# frequency ("every single day", "all the time", "most days"). The frequency words were missing,
# so "i lose my keys every single day" and "my keys go missing all the time" were read as one
# loss and got the search, which is the answer a person who has done this five times already
# knows by heart.
KEYS_AGAIN_RE = re.compile(
    r"\b(?:keep|keeps|always|constantly|forever|again|over and over|every time|twice|"
    r"second time|third time|lost them before|"
    r"every (?:single |other |blooming )?(?:day|week|month)|every day|all the time|"
    r"most days|a lot of the time|regularly|on a regular basis)\b", re.I)

KEYS_AGAIN_REPLY = (
    "Give them a place of their own and nothing else: a bowl or a hook by the front door, emptied "
    "the moment you come in, so the same spot takes them every time. That is the part that stops "
    "it happening - a key hook by the door costs a few pounds and works better than remembering. "
    "For today: retrace the last hour again - coat pocket, under the car seat, the last counter "
    "you were at.")

CAR_KEYS_AGAIN_REPLY = (
    "A key bowl by the door is the fix for a fob that keeps vanishing, because it is the only place "
    "it ever gets put down. For today: search the car properly - between the seats, the door "
    "pocket, the boot, the pockets of the coat you wore.")


# They already have a place and the keys are still gone ("i keep my keys in the bowl but now i
# cant find them"): the lecture about a bowl by the door is advice they have taken, so the search
# is the answer and the habit reading stands aside.
KEYS_KEPT_SOMEWHERE_RE = re.compile(
    r"\bkeep(?:s|ing)?\s+(?:my\s+|the\s+|our\s+)?(?:keys|key|fob)?\s*(?:in|on|by|under|next to)\b",
    re.I)


def _lost_keys(memory, understood):
    """The keys answer for the thing they open: a house barrel or a car's coding."""
    text = str(understood.get("clean") or understood.get("text") or "")
    car = bool(CAR_KEY_LOST_RE.search(text))
    if KEYS_AGAIN_RE.search(text) and not KEYS_KEPT_SOMEWHERE_RE.search(text):
        return CAR_KEYS_AGAIN_REPLY if car else KEYS_AGAIN_REPLY
    if car:
        return LOST_CAR_KEYS_REPLY
    return LOST_HOUSE_KEYS_REPLY


def _door_lock_stiff(memory, understood):
    """The graphite answer, unless the key being talked about belongs to something else."""
    words = " ".join(str(word) for word in (understood.get("words") or ())).lower().split()
    if not any(word in words for word in _NAMES_A_LOCK):
        recent = _recent_said(memory).split()
        if any(word in recent for word in _ELSEWHERE_KEY):
            return ""
    return LOCK_STIFF_REPLY




# The same black mould needs two different last sentences. In a bathroom the cure is the
# extractor fan, because the steam is made there; on a bedroom window frame or a chimney breast
# the steam is not the cause, and telling someone to run the fan after a shower is a bathroom
# answer to a room that has no shower in it. "there is black mould round my window frame" read
# as bathroom mould because "black" was one of this entry's surfaces.
MOULD_IN_THE_BATHROOM = ("bathroom", "en suite", "ensuite", "shower", "showers", "shower cubicle",
                         "bath", "tiles", "tiling", "grouting", "grout", "sealant", "silicone",
                         "extractor")
_MOULD_ROOM = ("Wipe it off with a mould spray, or a dilute bleach solution wearing gloves, and "
               "then find the water it is living on, because mould on a dry wall does not come "
               "back: a window frame wants the gap round it checked and the trickle vent opened, "
               "a cold outside wall wants air moving past it, and a corner behind furniture wants "
               "the furniture pulled out. Keeping the room warm and ventilated for a few weeks "
               "does more than any spray. If it keeps returning in the same place, that patch is "
               "a damp problem, not dirt.")


CUTTING_OUT = (
    (("kettle", "boils", "boil"),
     "A kettle that switches off before it boils is scaled, and the scale is what the cut-out "
     "reads: fill it to the line with half water and half white vinegar, boil, leave it an hour "
     "and rinse. Do that once a month in a hard water area."),
    (("microwave",),
     "A microwave that quits part way is protecting itself from heat: clear the vents, give it "
     "5cm of space on every side, don't run it empty, and stop using it if the turntable is not "
     "turning. One that stops after a minute on full power wants replacing, not repairing."),
    (("dishwasher",),
     "A dishwasher that stops part way is nearly always the drain or the door: clean the filter "
     "in the base, check the hose is not kinked, and make sure the door latch clicks. A flashing "
     "tap symbol means it is not filling, so check the water is on at the valve under the sink."),
    (("washing machine", "washer", "spin", "drum"),
     "A washer that stops mid-cycle is usually the door not quite latched or a drain that cannot "
     "empty: check the door clicks shut, clean the filter behind the kick plate, look for a kinked "
     "hose. The error code names it - E20 or F21 is a draining fault on most machines."),
    (("toaster", "toast", "pops", "popping", "pop up"),
     "A toaster that pops early usually has a full crumb tray or a weak timer: unplug it, empty "
     "the tray, turn the dial up one notch (most count darker to the right). If it pops after a "
     "couple of seconds on every setting the latch is worn, and a new one is cheaper."),
    (("dryer", "tumble dryer", "tumble"),
     "A dryer that cuts out is overheating: empty the lint filter after every load, clear the "
     "condenser and check the vent is not crushed, because a blocked vent is also a fire risk. "
     "If it stops with the clothes still wet on a low setting, the thermostat is the likely part."),
    (("oven",),
     "An oven that cuts out is usually the thermostat or the cooling fan: if it cooks unevenly or "
     "the fan is noisy before it stops, that is the fan; if it just goes cold and comes back, it "
     "is the thermostat. Both are repair jobs rather than a new oven."),
)
# Some of these lines are the machine doing its job: a kettle cuts out when the water boils, an
# oven when its timer ends, a microwave when the door opens. Held as phrases, because the fault
# lines are built from the same words - "switches off when it boils" is normal, "switches off
# *before* it boils" is scale - and a bare "boils" would take both.
NORMAL_CUTOUT = (
    "when it boils", "as it boils", "once it boils", "as soon as it boils",
    "when the timer ends", "when the timer runs out", "when the timer goes off",
    "when it reaches temperature", "when i open the door", "when you open the door",
    "when the door opens", "at the end of the cycle", "when the cycle ends",
    "when the programme ends", "when it finishes", "when it has finished",
)

# A kitchen machine that smokes, sparks or will not heat is not a recipe question, and the recipe
# tables were answering it: "my air fryer is smoking" got "chicken thighs 25 minutes at 190C". The
# fault is held as two kinds - it is burning, or it is dead - and the machine is read off the line,
# so each machine gets its own first check rather than a generic one.
MACHINE_BURNING = (
    "smoking", "smokes", "smoke", "sparking", "sparks", "sparked", "spark",
    "smells of burning", "smells like burning", "smells like its burning", "smell of burning",
    "burning smell", "burnt plastic", "smells hot", "getting very hot", "overheating",
    "caught fire", "smouldering", "smoldering",
)
MACHINE_DEAD = (
    "wont heat", "wont heat up", "won't heat", "won't heat up", "not heating", "not heating up",
    "isnt heating", "isn't heating", "isnt heating up", "stopped heating", "doesnt heat",
    "doesn't heat", "no heat", "stopped working", "has stopped working", "stopped",
    "wont turn on", "won't turn on", "wont switch on", "wont come on", "wont start",
    "dead", "no power", "has no power", "not getting power", "rattling",
    "making a grinding noise", "wont drain",
)
# A leak is a different cure from a dead machine - a seal or a split tank, not the electrics - so it
# is its own kind, and the machine named decides which seal the person is looking for.
MACHINE_LEAKING = (
    "leaking", "leaks", "leaked", "dripping", "drips", "water everywhere", "puddle",
    "puddles", "water coming out",
)
LEAK_CHECKS = (
    (("kettle",),
     "A leaking kettle is a perished seal or a split in the body, and neither is worth repairing: "
     "replace the kettle rather than keep a wet electrical appliance on the worktop."),
    (("coffee machine", "espresso", "bean to cup"),
     "Unplug it and take the tank and the group head off: a coffee machine that leaks is usually a "
     "perished group seal, a blocked spout or a tank seal that needs washing and reseating, and "
     "all three are cheap parts rather than a new machine."),
    (("blender", "food processor", "juicer", "soup maker"),
     "A jug or a bowl that leaks is the rubber seal under the blade assembly: take it out, wash it "
     "and put it back the right way up. A split jug or bowl is a replacement part, not a new "
     "machine."),
    (("slow cooker", "pressure cooker", "instant pot", "multi cooker"),
     "A slow cooker that leaks is overfilled, or the seal on the lid or the pot has gone: keep it "
     "under the fill line, and unplug it before you touch anything on the base."),
)
FALLBACK_LEAK = (
    "A leak is a seal, a gasket or a split tank rather than the electrics, so unplug it, dry it and "
    "look for the joint it comes from - and do not leave a wet machine plugged in while you look."
)
# the machine named in the line, then its burning answer and its dead answer. A person reading a
# kettle method for their slow cooker has to go and ask again, so the machine leads.
MACHINE_CHECKS = (
    (("air fryer", "airfryer", "air-fryer"),
     "Unplug it and let it cool: smoke from an air fryer is nearly always fat or a bit of food on "
     "the element or in the base of the drawer, so wash the basket and the inside of the drawer "
     "properly and check the element has no crust burnt onto it. If it sparked, or the coating on "
     "the element is flaking, stop using it - a new drawer or a new machine is cheaper than a "
     "kitchen fire.",
     "Unplug it, check the fuse in the plug and try another socket; if the display stays dark the "
     "element or the thermal cut-out has gone and it is not a repair worth doing. If it lights up "
     "but never gets hot, the element itself has failed."),
    (("slow cooker", "pressure cooker", "instant pot", "multi cooker"),
     "Unplug it and stop using it: a slow cooker that smokes or smells hot has usually had its "
     "element seal go, and the outside being discoloured says the same thing. It is not a repair "
     "worth doing on a machine that costs what they cost.",
     "Check the socket and the fuse first, then that the pot or the inner bowl is sitting right "
     "down on the base - a slow cooker that will not heat is usually one of those three and not "
     "the machine."),
    (("microwave",),
     "Stop it and unplug it. Sparks in a microwave are metal - foil, a gold rim, a twist of cling "
     "film with wire in it - or a burnt waveguide cover, or charred food on the inside wall. Take "
     "the plate out, clean the walls and try a mug of water: if it still sparks with nothing metal "
     "inside, the cover or the magnetron has gone and it needs an engineer or replacing.",
     "If the light and the clock work but nothing heats, the magnetron or its fuse has gone and it "
     "is an engineer's job. If it is completely dead, check the fuse in the plug first - a "
     "microwave on the same ring as a kettle blows it more often than you would think."),
    (("kettle",),
     "Unplug it and stop using it: a kettle that sparks or smells of burning at the base has a "
     "fault in the element or the connector, and a kettle is cheaper than the risk.",
     "If it will not switch on at all, check the fuse in the plug and try another socket first, "
     "because the contacts in the base are a common fault. If it stays dead it is a new kettle "
     "rather than a repair."),
    (("toaster", "sandwich toaster", "grill", "griddle", "waffle maker", "panini"),
     "Unplug it and tip the crumbs out: a toaster that sparks or smells of burning usually has "
     "crumbs or a damaged element catching. If the element glows unevenly or a bit of it is "
     "missing, it is a new toaster rather than a repair.",
     "If it will not pop up, the spring or the timer has gone and it is a new toaster. If it will "
     "not heat at all, check the fuse in the plug first, then the timer dial."),
    (("bread maker", "bread machine", "stand mixer", "blender", "food processor", "soup maker",
      "yogurt maker", "coffee machine", "rice cooker", "deep fat fryer", "fryer", "juicer"),
     "Unplug it and stop: a machine that smells of burning has cooked its motor, and the thermal "
     "cut-out that should have saved it has already done what it can. Motors and seals are the "
     "parts that fail and neither is worth paying someone to fit on a kitchen machine.",
     "Check the fuse in the plug, then the switch, then the lid or the bowl interlock - a machine "
     "that will not start very often thinks the lid is open. If it hums and does not turn, the "
     "motor or the belt has gone."),
)
FALLBACK_BURNING = (
    "Unplug it and stop using it. A machine that smokes or sparks is usually finished rather than "
    "repairable, and the smoke is often worse than the fault: check the fuse and the socket once, "
    "and if it does it again, replace it."
)
FALLBACK_DEAD = (
    "Unplug it, check the fuse in the plug and try another socket before you write it off, because "
    "the plug is the cheapest thing to rule out. If it is still dead on another socket, the "
    "machine is the fault and it is usually a replacement rather than a repair."
)


# A kettle, a toaster or a coffee machine that has stopped is already answered, and the answer that
# holds it carries the price of a new one, the guarantee and the retailer's six-year duty with it. A
# short "check the fuse" would be a loss on those three, so this entry stands aside for them and
# keeps the dead lines of the machines nothing else answers - the slow cooker, the bread maker, the
# air fryer. A leak or a burn on any of them is still this entry's, because nothing else has it.
DEAD_ALREADY_ANSWERED = (
    "kettle", "toaster", "sandwich toaster", "coffee machine", "espresso", "bean to cup",
    "air fryer", "airfryer", "air-fryer", "microwave",
)
# The same holds for a machine that is smoking: the fire card - unplug it, keep the door shut, get it
# outside - is the right first move, and it already has those machines. Splitting them, so that
# "my toaster is smoking" gets the fire card and "my sandwich toaster is smoking" gets the crumbs,
# would be one fault with two answers depending on the wording.
BURNING_ALREADY_ANSWERED = (
    "air fryer", "airfryer", "air-fryer", "toaster", "sandwich toaster", "kettle", "microwave",
)


def _machine_fault(memory, understood):
    """The named machine's own answer for the kind of fault the line describes."""
    said = str((understood or {}).get("clean") or (understood or {}).get("norm_text") or "").lower()
    burning = any(_says(said, word) for word in MACHINE_BURNING)
    if any(_says(said, word) for word in MACHINE_LEAKING) and not burning:
        return next((text for words, text in LEAK_CHECKS
                     if any(_says(said, word) for word in words)), FALLBACK_LEAK)
    if burning and any(_says(said, word) for word in BURNING_ALREADY_ANSWERED):
        return ""
    if not burning and any(_says(said, word) for word in DEAD_ALREADY_ANSWERED):
        return ""
    for words, hot, dead in MACHINE_CHECKS:
        if any(_says(said, word) for word in words):
            return hot if burning else dead
    return FALLBACK_BURNING if burning else FALLBACK_DEAD


FALLBACK_CUT_OUT = (
    "An appliance that stops part way is usually protecting itself: give it room to breathe, "
    "clear the filter or vents and see whether it does it again on a lighter load."
)


def _appliance_cutting_out(memory, understood):
    """The sentence for the appliance the line names, then the two checks that fit most of them.

    "My kettle keeps switching off before it boils" and "my washer stops mid-cycle" are the
    same shape and different faults, so the answer for the appliance named comes first: a
    person reading a descaling method for their washing machine has to go and ask again.
    """
    said = str((understood or {}).get("clean") or "").lower()
    lead = next((text for words, text in CUTTING_OUT if any(_says(said, word) for word in words)),
                FALLBACK_CUT_OUT)
    close = ("If it only ever happens on one socket, feel the plug: a warm plug is a loose "
             "connection, so stop using that socket and get an electrician in.")
    return lead + " " + close


# The other way a kettle fails: it does not stop. Scale makes a kettle switch off too early, and
# that answer says "the scale is what the cut-out reads", so "my kettle never switches off" and
# "my kettle boils dry" were being told the wrong fault - a person reading it goes looking for
# scale while the kettle in front of them is trying to boil itself dry. The steam switch (or the
# bimetal strip under the base) is the part that has failed, and a kettle that keeps going is a
# scorched base, melted plastic and, on a plastic one, a fire. One reply covers the whole family
# of lines, because they are one fault: wont switch off, never switches off, wont turn off, wont
# shut off, keeps boiling, wont stop boiling, boils dry.
_KETTLE_WILL_NOT_STOP = (
    "Stop using it: a kettle that boils dry is not cutting out, and the steam switch in the lid "
    "or the strip in the base that should cut it is the part that has failed. Scale can hold that "
    "switch shut, so descale it once - half water, half white vinegar, boil, leave it an hour, "
    "rinse - and try it again with the lid on and shut, because the steam has to reach the switch "
    "for it to work. Watch that next boil, and if it still refuses to click off, bin it: a kettle "
    "costs less than the repair, and one that has already boiled dry can scorch its element, melt "
    "the plastic round it or trip the house electrics.")


def _kettle_will_not_stop(memory, understood):
    return _KETTLE_WILL_NOT_STOP


# A screen that has gone black is technology's question: the key's "gone black" and "going
# black" are how people describe mould, and they are how people describe a dead display too.
# The surface is what tells them apart, so a device word with no wall, window or room named is
# handed back. Keeping this in the reply rather than in the entry's avoid list is what lets
# "the wall behind my monitor has gone black" stay a mould answer.
MOULD_DEVICE = ("screen", "screens", "monitor", "monitors", "display", "laptop", "laptops",
                "phone", "phones", "iphone", "ipad", "tablet", "computer", "pc", "telly", "tv",
                "television", "screenshot", "kindle", "console", "playstation", "xbox",
                "keyboard", "keyboards", "headset", "headsets", "headphones", "earbuds",
                "earphones", "airpods",
                "speaker", "speakers", "remote", "mouse", "watch", "smartwatch")
# The mould key carries the plainest way people name it - "gone black", "turned black", "black
# on the" - because "my wall has gone black" names no mould at all. Those same shapes read a body
# that has changed colour: `my ankle is sprained` then `its turned black`, and `the bruise has gone
# black and blue`, were both told to wipe it with a mould spray and find the water it is living on.
# A line that names a body part or a bruise stands the mould row down unless it also names mould or
# one of the surfaces of a house; the colour of a body is the body's question.
MOULD_BODY = ("ankle", "ankles", "knee", "knees", "shin", "shins", "calf", "calves", "heel",
              "heels", "foot", "feet", "toe", "toes", "nail", "nails", "finger", "fingers",
              "thumb", "thumbs", "hand", "hands", "wrist", "wrists", "arm", "arms", "elbow",
              "elbows", "shoulder", "shoulders", "leg", "legs", "thigh", "thighs", "hip", "hips",
              "skin", "bruise", "bruises", "bruised", "swelling", "swollen", "sprain", "sprained",
              # the mouth is not a wall either, and a gum or a tongue that has gone black wants
              # its own row: leaving it out here keeps the answer it had rather than a shrug.
              "wound", "cut", "cuts", "eyelid",
              "eye", "eyes", "ear", "ears", "face", "forehead", "neck", "chest", "rib", "ribs",
              "fingertip", "knuckle", "knuckles", "cuticle", "toenail", "fingernail", "vein",
              "veins", "scalp", "jaw", "chin", "temple", "sock", "socks")


MOULD_SURFACE = ("wall", "walls", "ceiling", "ceilings", "window", "windows", "frame", "sill",
                 # `my chest of drawers has gone black` is a piece of furniture: chest is a
                 # body part and had the mould row standing down, so the line got no answer.
                 "drawer", "drawers", "furniture", "door", "doors", "floor", "floors",
                 "floorboard", "floorboards", "wood",
                 "windowsill", "corner", "corners", "sealant", "silicone", "tile", "tiles",
                 "grout", "grouting", "skirting", "wallpaper", "paint", "bathroom", "bedroom",
                 "kitchen", "hall", "hallway", "cupboard", "wardrobe", "flat", "house", "room",
                 "rooms", "loft", "attic", "shower", "bath", "behind the", "grout", "woodwork",
                 "paving", "path", "decking", "fence", "garage", "shed", "mattress", "curtains",
                 # a case, a cover and a strap are surfaces a device is inside rather than the
                 # device: "my phone case has gone black" was a mould spray, and a stand-down that
                 # read "phone" alone turned it into a punt. The surface word is what tells them
                 # apart, so it goes here beside the wall and the ceiling.
                 "case", "cover", "strap", "band", "backsplash", "back splash")


def _the_black_is_not_a_body(understood):
    """A colour a body has changed to is the body's question, not a wall's.

    The mould row is the one place the shape "gone black" is a key word rather than a mould word,
    because people say "the wall has gone black" and never the word mould. A bruise says the same
    thing, so a line that names a body part or a bruise hands the line back unless it also says
    mould or names something in the house (a wall, a window, a shower, a case).
    """
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or
               (understood or {}).get("norm_text") or "").lower()
    if not any(_says(said, word) for word in MOULD_BODY):
        return True
    if any(_says(said, word) for word in MOULD_SAID):
        return True
    return any(_says(said, word) for word in MOULD_SURFACE)


# A device word only separates a dead display from a mouldy one while the line never says mould.
# "My laptop screen has black mould" and "my screen has black mould on it" are mould questions
# about a thing in the room, and handing them back told a person with a mouldy screen to press a
# key, which is the one answer that cannot help them. The line that needs the display row - "my
# screen keeps going black" - does not say mould, so this loses nothing it was built for.
MOULD_SAID = ("mould", "moulds", "mouldy", "moulded", "mold", "molds", "moldy", "molded",
              "mildew", "mildews", "mildewy", "mildewed", "fungus", "fungal")
_MOULD_DEVICE_REPLY = (
    "Wipe it off with a cloth just damp with isopropyl alcohol, or with a little white vinegar on a "
    "cotton bud for the joins, then dry it and let it air - not the bathroom mould spray or neat "
    "bleach, which mark a screen and eat the plastic. Mould needs damp, so the fix is the room: keep "
    "the device out of a cold outside wall or a steamy bathroom, and if it comes back in the same "
    "corner the damp is coming through there and wants finding before the next wipe.")


def _mould(memory, understood):
    """The bathroom cure where the steam is made, the room cure everywhere else."""
    said = (understood.get("norm_text") or understood.get("text") or "")
    # The subject overrules the device word. "my screen has black mould on it" names a screen and
    # a mould, and the mould is what the person is asking about: the stand-down read the screen
    # alone and left the line with nothing. A surface word or a guard word (the growth itself)
    # means the device is what the mould is on, so it is the mould answer.
    if any(_says(said, word) for word in MOULD_DEVICE) and not any(
            _says(said, word) for word in MOULD_SURFACE) and not any(
            _says(said, word) for word in MOULD_SAID):
        return ""
    if any(_says(said, word) for word in MOULD_DEVICE) and not any(
            _says(said, word) for word in MOULD_SURFACE):
        return _MOULD_DEVICE_REPLY
    # A body that has changed colour says the same shape as a wall, and the follow-up names no
    # body at all: `my ankle is sprained` then `its turned black` reached the mould spray because
    # the key matched "turned black" and the ankle was in the turn before. The line has to say
    # something about the house, or say mould, for the colour to be mould.
    if not any(_says(said, word) for word in MOULD_SAID) and not any(
            _says(said, word) for word in MOULD_SURFACE) and any(
            _says(_recent_said(memory), word) for word in MOULD_BODY):
        return ""
    if any(_says(said, word) for word in MOULD_IN_THE_BATHROOM):
        return ("Wipe the mould off with a mould spray, or a dilute bleach solution wearing gloves, "
                "then stop it coming back: run the extractor fan during and for 20 minutes after a "
                "shower, and wipe the condensation off the walls. If it returns, the cause is damp, "
                "not the paint.")
    return _MOULD_ROOM

def _pipes(memory, understood):
    """A pipe that has already frozen needs the thaw first; a cold snap needs the prevention."""
    text = str(understood.get("clean") or " ".join(understood.get("words") or [])).lower()
    thaw = ("Turn the water off at the stopcock first, then thaw the pipe gently from the tap end "
            "with a hot water bottle, warm towels or a hairdryer on low: a frozen pipe is not a "
            "burst one yet, and being gentle is what keeps it that way. Never use a blowtorch. If "
            "the pipe has already split, keep the water off and call a plumber.")
    prevent = ("Lag the pipes in the loft and under the floor, and in cold snaps leave the heating "
               "on a low setting, 12 to 15C, rather than off: that costs far less than a burst "
               "pipe.")
    if any(word in text for word in ("frozen", "froze", "thaw", "burst", "split", "no water",
                                     "already", "freeze up", "froze up", "solid")):
        # the thaw already names the stopcock and the blowtorch, so the prevention half drops the
        # sentence it would otherwise repeat
        return thaw + " " + prevent
    return prevent + " " + thaw


# --- turning things off ---------------------------------------------------------
# Finding the stopcock and the fuse box, switching the water off and resetting a trip are four jobs
# with a known answer that the bot met with "A plumber or electrician will spot it in minutes".
# The water ones were worse than a shrug: travel's tap-water entry reads "water" and "mains" as a
# question about drinking it, so "how do i turn the water off at the mains" was answered with
# advice about bottled water abroad. The question shape decides the paragraph, so the one entry
# below reads the line instead of the topic.
# The fuse box is the other switch-off question, and it was the plumber shrug too: "where is my
# fuse box", "how do i reset a trip switch" and "how do i turn off the electricity" (which got a
# paragraph on electrons). Where it is, how to reset it and how to kill the power are three
# answers to one subject, so the question shape decides again.
UNIT_WHERE = re.compile(r"\b(where|find|locate)\b", re.I)
UNIT_RESET = re.compile(r"\b(reset|resetting|tripped|trips|keeps|kept|blown|won't stay|wont stay|"
                        r"down)\b", re.I)
# A power cut and a house with no power at all are the same opening move (look at the consumer
# unit) and a different second one: "why has the power gone off" was being told how to turn it
# off, which is the one thing the person cannot do anything useful with.
# The power is already off, so being told how to switch it off is the one answer that cannot
# help. "Is off", "is out", "upstairs" and "half the house" say that as plainly as "gone off".
UNIT_GONE = re.compile(r"\b(gone off|went off|has gone|have gone|why|no power|no electricity|"
                       r"is off|are off|is out|are out|in one room|upstairs|downstairs|"
                       r"half the house|half the flat|not coming back|"
                       r"wont come back|won't come back|back on|everywhere|street)\b", re.I)
# A trip switch that only goes in wet weather is water in an outside fitting, not a power cut.
UNIT_WET = re.compile(r"\b(rain|rains|raining|wet|damp|weather|storm|storms|stormy|snow|thaw)\b",
                      re.I)


def _consumer_unit(memory, understood):
    """Where the consumer unit is, how to reset it, and how to turn the power off at it."""
    said = str((understood or {}).get("clean") or " ".join((understood or {}).get("words") or []))
    said = said.lower()
    where = ("The consumer unit is a white or grey plastic box with a row of switches and a test "
             "button, usually in the hall near the front door, under the stairs, in the garage or "
             "next to the electricity meter; an older house may still have a wooden board with "
             "fuses instead. Look for the box with the switches on the inside of the front wall, "
             "and take a photo of it so you can see which switch was up.")
    reset = ("Push the switch that is down, or the button that has popped out, firmly to off and "
             "then back on - a tripped switch only half moves, so it has to go fully off first. If "
             "it trips again straight away, unplug everything on that circuit, reset it, then plug "
             "things back one at a time to find the culprit; if it trips with nothing plugged in, "
             "the wiring is at fault and that needs an electrician.")
    gone = ("Look at the consumer unit first: if every switch is up, the fault is outside the "
            "house - check whether a neighbour has power too, then ring 105 (free, 24 hours) or "
            "your supplier, and leave a light switch on so you know when it is back. If one switch "
            "is down, only that circuit went off, so unplug what is on it before you reset it.")
    off = ("The big switch at one end of the consumer unit turns off everything in the house, and "
           "it is the right thing to do before you work on a socket or a light. Don't pull the "
           "fuse out of the meter or cut the seal on it - that is the supplier's, and it is live.")
    wet = ("A switch that trips only when it rains is water getting into an outside socket, a light "
           "or a cable: leave that circuit off, dry out and reseal the outside fitting, and get an "
           "electrician to look at it, because it will keep tripping until that water is kept out. "
           "Don't keep resetting it into a fault.")
    if UNIT_WHERE.search(said):
        return where
    if UNIT_WET.search(said):
        return wet
    if UNIT_RESET.search(said):
        return reset
    if UNIT_GONE.search(said):
        return gone
    return off


SHUTOFF_WHERE = re.compile(r"\b(where|find|locate)\b", re.I)
# The same step in the other direction: a valve closes clockwise and opens anticlockwise, and
# "how do i turn the water back on" was getting the closing instruction.
SHUTOFF_ON = re.compile(r"\b(back on|turn(ed|ing)? (it |the water )?on|switch(ed|ing)? (it |the water )?"
                        r"on|open(ing)? (it|the valve) up|restore)\b", re.I)
SHUTOFF_FAULT = re.compile(r"\b(wont|won't|will not|keeps?|kept|still|not)\s+(stop|stops|stopping|"
                           r"shut|turning|turn off|going|come out)\b|\brunning\b|\bleaking\b|"
                           r"\bflood(ed|ing|s)?\b", re.I)


def _water_off(memory, understood):
    """Where the stopcock is, how to shut the water off, and what to do when it will not stop."""
    said = str((understood or {}).get("clean") or " ".join((understood or {}).get("words") or []))
    said = said.lower()
    where = ("The inside stopcock is usually under the kitchen sink, and sometimes under the stairs, "
             "in a downstairs loo or in the airing cupboard: it is a brass tap on the pipe where the "
             "mains comes in, and it closes with a quarter turn clockwise. If there is not one "
             "indoors, look for a small metal cover just outside the front wall or at the boundary "
             "of the property, which needs a stopcock key or a spanner.")
    how = ("Turn it clockwise until it stops - a quarter turn is usually enough - then open the cold "
           "taps downstairs to run the water out of the pipes before you start work, and open the "
           "lowest tap if you are draining the system properly. Combi boilers lose their pressure "
           "this way, so note the gauge and top it back up afterwards.")
    on = ("Open it anticlockwise, a quarter turn at a time, and listen for the water coming back "
          "through the pipes. Close the taps you left open first, or the water will run straight "
          "out of them, then run the cold tap at the kitchen sink for a minute to clear the air "
          "before you use the boiler or the washing machine again.")
    fault = ("Shut it off at the stopcock first and open the cold taps to take the pressure off; if "
             "the water keeps coming, the inside valve has failed, so use the outside one at the "
             "boundary, or ring the water company and they can shut it in the road. Water near a "
             "socket or a light fitting means don't touch the switches - turn the power off at the "
             "consumer unit first.")
    if SHUTOFF_ON.search(said) and not SHUTOFF_WHERE.search(said):
        return on
    if SHUTOFF_FAULT.search(said):
        return fault
    if SHUTOFF_WHERE.search(said):
        return where
    return how


# --- colour, as a table ------------------------------------------------------------
# "what goes with a blue sofa", "what colour curtains go with grey walls" and "is grey and beige ok
# together" all reached the search hedge. A colour question is one question with one answer shape -
# what suits it, what to keep neutral, what to put it with - and the colour is data, so a new colour
# is one row. The words here are the ones people say, not the paint chart's names.
COLOUR_PARTNERS = {
    "blue": "Warm company stops blue going cold: mustard, tan leather, brass, a warm white on the "
            "walls, and one wooden thing.",
    "navy": "Cream, camel and brass suit navy, or a pale grey with a shot of green; keep the metals "
            "warm so it does not read as a uniform.",
    "grey": "Warm grey up with wood, brass and one soft colour - blush, mustard or sage - because "
            "grey with grey goes flat and grey with black goes cold.",
    "green": "White or cream lets green breathe, then pink, mustard or brown leather; a dark green "
             "wants brass and a pale wall behind it.",
    "sage": "Off-white, pale wood and terracotta suit sage, with a darker green somewhere to give "
            "it depth.",
    "teal": "Mustard, coral, brass and a warm white suit teal, and most of the room should stay "
            "pale.",
    "black": "Warm neutrals stop black reading as an empty room: cream, camel, walnut and brass, "
             "with one bright colour in a cushion or a plant pot.",
    "brown": "Light walls and a strong third colour: cream, olive, rust or a deep blue. Brown on "
             "brown in a small room needs a pale floor.",
    "beige": "Texture, one darker tone from the same family and a green plant: flat beige is what "
             "makes a room look unfinished.",
    "cream": "Nearly everything suits cream, which is the risk - anchor it with wood, black or a "
             "deep colour so it does not look like undercoat.",
    "white": "Wood, black, brass and any one colour you like; the trick with white is texture, not "
             "shade.",
    "yellow": "Grey or white calms yellow, black or navy sharpens it, and orange is the one colour "
              "not to put in the same room.",
    "mustard": "Navy, charcoal or olive on a cream wall; mustard is strong enough to be the only "
               "colour in the room.",
    "pink": "Grey, olive or brass suit pink; a grown-up pink is dusty rather than bright, and it "
            "sits well with a brown wood floor.",
    "red": "Small amounts, with a lot of white or black: a red sofa wants pale walls and no second "
           "colour.",
    "terracotta": "Cream, olive and pale wood suit terracotta, with a little black to stop it going "
                  "sweet.",
    "purple": "Grey or cream walls, a little gold and a white floor: a whole purple room goes dark "
              "in the evening.",
    "orange": "Grey or white walls with a cool blue somewhere, because orange dates fast in large "
              "amounts.",
    "silver": "Warm wood and cream, or one deep colour: cold metal against cold walls feels "
              "clinical.",
}
# Two colours in the line is its own question - "will grey and beige go together" - and the answer
# is about the pair, not one of them.
COLOUR_NEUTRAL = frozenset(("grey", "gray", "beige", "cream", "white", "black", "brown",
                            "charcoal", "navy", "taupe"))
COLOUR_WARM = frozenset(("mustard", "orange", "red", "terracotta", "yellow", "brown", "pink"))
COLOUR_COOL = frozenset(("blue", "navy", "teal", "green", "sage", "grey", "gray", "purple",
                         "silver"))

def _colours_in(line):
    """Every colour the line names, in the order it names them, without repeats."""
    found = []
    for word in re.findall(r"[a-z']+", line.lower()):
        if word in COLOUR_PARTNERS and word not in found:
            found.append(word)
    return found


def _colour_advice(memory, understood):
    """What to put a named colour with, or the rule when the line names none."""
    line = understood.get("text") or understood.get("clean") or ""
    colours = _colours_in(line)
    if len(colours) >= 2:
        first, second = colours[0], colours[1]
        both_neutral = first in COLOUR_NEUTRAL and second in COLOUR_NEUTRAL
        mixed = (first in COLOUR_WARM) != (second in COLOUR_WARM)
        if both_neutral and mixed:
            return (f"{first.title()} and {second} work together, and that is the point: one is "
                    f"warm and one is cool, so the room has depth. Anchor them with a wood, a "
                    f"metal and texture - a rug, a throw - because two neutrals alone look "
                    f"unfinished, and put one deeper tone in the cushions.")
        if both_neutral:
            return (f"{first.title()} and {second} are both quiet, so nothing in the room is doing "
                    f"the work: add a third colour you actually like - green, mustard or rust - "
                    f"plus a wood and a texture, or it will look like a show home.")
        return (f"They go together if one stays big and the other stays small: let {first} be the "
                f"walls or the sofa, and keep {second} to cushions, a rug or a picture. Two strong "
                f"colours at the same size fight, and a cream or white between them settles it.")
    if colours:
        name = colours[0]
        return (f"{COLOUR_PARTNERS[name]} Sample it before you buy with a patch on the wall or a "
                f"cushion taken home, because {name} changes with the light, and keep the rest of "
                f"the room quiet so the one colour has somewhere to sit.")
    return ("Pick the thing you cannot change - the sofa, the floor, the tiles - and pull one colour "
            "out of it for the walls in a paler version of itself, then one deeper tone for a rug or "
            "cushions and a wood or metal to warm it. Three colours, one of them a neutral, and a "
            "sample pot painted on a patch of wall you can see in the morning and at night: that is "
            "the whole trick.")

_OUTBUILDING = ("shed", "sheds", "garage", "garages", "greenhouse", "greenhouses",
                "outbuilding", "outbuildings", "carport", "kennel", "coop", "porch",
                "conservatory", "summerhouse")


def _roof_leak(memory, understood):
    """The steps for a live leak, shorter when the roof is not over anybody's head."""
    line = (understood.get("clean") or understood.get("text") or "").lower()
    if any(re.search(r"\b" + word + r"\b", line) for word in _OUTBUILDING):
        return ("Get a tarpaulin over it and weigh it down rather than standing underneath to sort "
                "it: a shed, a garage or a greenhouse roof is not worth a fall. Move anything "
                "electric or valuable out of it, photograph the damage for insurance, then get a "
                "roofer - a felt or corrugated roof is a same-day patch for one. If the water is "
                "running near the house or the consumer unit, treat it as the house's leak and "
                "call an electrician before anything else.")
    return ("Catch it and cut the power before anything else: a bucket under the drip, and turn off "
          "the light circuit for that room at the fuse board if water is near a fitting, because "
          "water and ceiling lights are the dangerous pair. Do not go up on a wet roof or into a "
          "loft with wet boards - a fall from a roof kills more people than a leak ever does. "
          "Absorb what you can, move furniture and photos, and photograph it all with the date: "
          "the ceiling may sag, so stay out of the room if the plaster bulges. If "
          "you rent, tell the landlord in writing now and keep the message, because a leak they "
          "were told about is theirs to fix. Then get a roofer out - most will tarp a live leak "
          "the same day - and check your insurance covers the escape of water.")



# A patch or a stain on a ceiling is usually the mark a leak left, and that answer is the one to
# find where it comes in. A patch that is *wet* is the leak itself, and it wants the steps that
# start with cutting the power: "there is a wet patch on my ceiling" is a live leak near a light
# fitting, not history. The words for the mark and the words for the water are read apart here so
# the row stands down for the one and keeps the other.
A_MARK_WORD = r"\b(?:patches?|stains?|stained|marks?|water mark|water marks)\b"
THE_WATER_IS_MOVING = (
    r"\b(?:wet|wetter|soaked|soaking|soggy|dripping|dripped|drips?|weeping|seeping|"
    r"spreading|growing|live|coming through|coming in|pouring|just happened|today|"
    r"this morning|tonight|last night)\b")

def _a_mark_that_is_live(understood):
    """The live-leak row keeps a mark that is wet, and leaves a dried one to the ceiling patch."""
    line = (understood.get("clean") or understood.get("text") or "").lower()
    if not re.search(A_MARK_WORD, line):
        return True
    return bool(re.search(THE_WATER_IS_MOVING, line))


def _pressure_weak(memory, reading):
    """Weak water at a shower and weak water at a tap.

    One entry answers both, because the cause is usually the same - scale at the outlet, then the
    supply - but the outlet is not the same thing in the two lines. STYLE asks for the answer in
    the first sentence, and a person whose shower has lost its force does not want a paragraph
    about aerators: their head is the part that unscrews. A line naming a shower gets the head
    first; everything else keeps the tap answer unchanged.
    """
    words = set(reading.get("words") or ())
    if words & {"shower", "showers", "showerhead", "showering"}:
        return ("Scale in the shower head is the first thing to check: unscrew it, pick the grit "
                "out of the holes and soak it in vinegar or citric acid overnight, and clean the "
                "small filter where the hose joins the outlet. Check the head is not clicked onto "
                "an economy or pause stop too. If the other taps are weak as well it is the "
                "supply instead: on a combi it is whatever the mains gives, and on a tank it is "
                "the pump or the head of water, so look at the boiler gauge (1 to 1.5 bar cold) "
                "and the stopcock before you buy a new head.")
    return ("If it is one tap, it is nearly always scale in the spout: the mesh aerator unscrews by "
            "hand, so soak it in vinegar and the flow usually comes back. If it is every tap, "
            "check the stopcock under the kitchen sink is fully open, then ask a neighbour - if "
            "theirs is weak too it is the mains and you ring the water company. A combi boiler "
            "reads its pressure on the gauge under the front panel, 1 to 1.5 bar when cold, and "
            "low pressure there means weak hot water everywhere, which you top up with the filling "
            "loop. A shower that is only weak when hot has a scaled head or a tired hose.")

_SMOKE_COMPUTER = re.compile(r"\b(?:laptop|computer|pc|phone|mobile|charger|tablet|tv|telly|"
                             r"television|printer|socket|plug|extension lead|monitor|console|"
                             r"xbox|playstation)\b", re.I)
_SMOKE_MACHINE = re.compile(r"\b(?:washing machine|washer|tumble dryer|dryer|dishwasher|"
                            r"hoover|vacuum)\b", re.I)
_SMOKE_CRUMBS = re.compile(r"\b(?:toaster|microwave|air fryer|fryer|sandwich maker|"
                             r"grill|toasted sandwich)\b", re.I)
_SMOKE_HEATER = re.compile(r"\b(?:kettle|boiler|iron|hair dryer|hairdryer|heater|radiator|"
                           r"fuse box|immersion|shower)\b", re.I)


def _smoking_appliance(memory, reading):
    """Smoke out of one thing, with the cause that thing actually gives.

    The opening and the close are the same for every appliance, because the danger is: a
    smouldering element or a trapped wire is a fire waiting to happen. What sits between them
    cannot be, because an oven smokes for a different reason than a laptop, and the reply used to
    name the oven to people whose toaster, or whose phone, was the thing smoking. A cause sentence
    about the wrong appliance is worse than none: it hides the thing to check.
    """
    clean = reading.get("clean") or ""
    lead = ("Switch it off at the wall and unplug it, and keep the door shut - opening it feeds "
            "the smoke and can flare a fire up. Let it cool, open the windows, and take it outside "
            "if it is small enough to lift safely. ")
    end = (" Don't use it again until it has been checked, because a smouldering element or a "
           "trapped wire is a fire waiting to happen - and if you see flames or the smoke spreads "
           "past the appliance, get out and ring 999 or 911.")
    if _SMOKE_COMPUTER.search(clean):
        return (lead + "Smoke from a laptop, a phone or a plug is usually a failing battery or a "
                "hot joint rather than anything burning inside the case: pull the charger out "
                "too, and do not shut it in a cupboard or a bag while it cools." + end)
    if _SMOKE_MACHINE.search(clean):
        return (lead + "On a washer or a dryer it is usually the motor, a belt, or fluff against "
                "the heater, and a dryer full of fluff can go up on its own: take the washing out "
                "before you look, and clear the filter once it is cold." + end)
    if _SMOKE_HEATER.search(clean):
        return (lead + "On something that heats, a burning smell is often dust or scale on the "
                "element after a spell unused, but check the plug and the cable for a hot or "
                "blackened end, because that is the part that catches." + end)
    if _SMOKE_CRUMBS.search(clean):
        return (lead + "On a toaster or a microwave it is nearly always crumbs or a burnt lining: "
                "once it is cold, tip the crumbs out over the bin, wipe the inside with a damp "
                "cloth and leave it open to dry before you use it again." + end)
    return (lead + "On an oven or a grill it is nearly always old grease or a spill burning off: "
            "once it is cold, a paste of bicarbonate of soda and water on the inside (not the "
            "elements) gets rid of that." + end)


_ALARM_STEAM = re.compile(r"\b(?:shower|showering|bath|bathroom|steam|steamy|kettle|"
                           r"boiling|washing)\b", re.I)
# An alarm that went off with nothing to smell is the third kind of nuisance alarm: the causes are
# in the unit and the room rather than on the hob. Dust and insects in the chamber, a damp day, and
# a sensor past its tenth year are what sets one off when nothing is cooking, so the answer that
# opens by blaming toast is the wrong answer to it.
_ALARM_NO_CAUSE = re.compile(
    r"\b(?:for no (?:apparent |obvious )?reason|no reason at all|nothing (?:was |is )?burning"
    r"|nothing on fire|no smoke|no fire|was no fire|nothing caught fire"
    r"|nothing (?:was |is )?cooking|nothings cooking|wasn'?t cooking"
    r"|not cooking|randomly|out of nowhere|middle of the night|at [123] ?am)\b", re.I)


def _alarm_nuisance(memory, reading):
    """An alarm that goes off for something that is not a fire, blamed on the right cause.

    Which way to move it depends on what sets it off: an alarm above the hob wants to go a couple
    of metres along the ceiling, one outside a bathroom wants to go past the door, since steam
    off a shower is what a smoke sensor cannot tell from smoke. One sentence naming both was
    advice for a kitchen given to people standing in a bathroom.
    """
    clean = reading.get("clean") or ""
    if _ALARM_NO_CAUSE.search(clean) and not _ALARM_STEAM.search(clean):
        return ("If nothing was cooking and there was no smoke, the usual causes are in the unit "
                "and the room: dust or a spider in the sensing chamber, steam from a bathroom or a "
                "damp day, and a sensor that is past its tenth year. Vacuum the vents, press the "
                "test button, and replace the whole unit if it is old or if it keeps doing it - the "
                "sensor wears out before the battery does. Never take the battery out to silence it, "
                "because that is how a real fire goes unnoticed.")
    if _ALARM_STEAM.search(clean):
        cause = ("It cannot tell steam from smoke, so a hot shower with the door open will set it "
                 "off. Keep the door shut with the window open while you shower, or use the fan, "
                 "and if that is not enough, move the alarm a couple of metres further from the "
                 "bathroom door - not out of the landing, because that is where a real fire has "
                 "to wake you.")
    else:
        cause = ("It cannot tell toast or frying from a fire. Open a window and put the extractor "
                 "on before the pan gets hot, and if it still goes off, move the alarm a couple of "
                 "metres further from the hob - not out of the room, because that is where a real "
                 "fire has to wake you.")
    quiet = "nothing is running at all" if _ALARM_STEAM.search(clean) else "nothing is cooking"
    return (cause + " Never take the battery out to silence it, because that is how a real fire "
            "goes unnoticed. If it goes off when "
            + quiet + ", vacuum the vents, press the test button, and replace the whole unit once "
            "it is ten years old: the sensor wears out before the battery does.")


_HOB_INDUCTION = re.compile(r"\b(?:induction)\b", re.I)
# A ring that will not light, spark or stay lit is a gas ring whatever else the line says: an
# electric ring has nothing to light. The word is the only clue, so it decides the branch on its own.
_HOB_GAS = re.compile(r"\b(?:gas|flame|flames|burner|burners|jet|jets|igniter|ignition|"
                      r"cap|spark|sparks|sparking|light|lights|lit|lighting|ignite|ignites|"
                      r"relight|out)\b", re.I)
_IRON_COLD = re.compile(r"\b(?:heat|heats|heating|hot|cold|dead|working|power|turns? on|"
                        r"turned on|switch(?:es|ed)? on)\b", re.I)
_IRON_SCALE = re.compile(r"\b(?:brown|white|chalky|rusty|rust|grit|bits|flakes|dirty|"
                         r"mark|marks|stain|stains|scorch)\b", re.I)


# A phone rings and a hob has rings, and "ringing" folds onto "ring", which is in the hob's key
# and cannot leave it: "my mum wont stop ringing me" and "my mum has stopped ringing me" were both
# answered with a ceramic element on its way out. A phone word in the avoid list cannot help,
# because the word in the line is "ringing". So the ring is read by whose it is: a relation plus a
# phone verb aimed at the speaker is a person's line, and the hob stands down.
_HOB_PERSON = re.compile(r"\b(?:mum|mam|mom|mother|mummy|dad|daddy|father|parent|parents|sister"
                         r"|brother|son|daughter|husband|wife|partner|boyfriend|girlfriend"
                         r"|friend|friends|nan|gran|granny|grandma|grandad|aunt|uncle|relative"
                         r"|neighbour|neighbours|boss|colleague|carer)s?\b", re.I)
_HOB_THE_PHONE = re.compile(r"\b(?:rings? me|ringing me|rang me|calls? me|calling me|called me"
                            r"|texts? me|texting me|texted me|phones? me|phoning me|phoned me"
                            r"|keeps ringing|kept ringing|wont stop ringing|never stops ringing"
                            r"|doesnt stop ringing|does not stop ringing|non stop ringing"
                            r"|constantly ringing|always ringing)\b", re.I)


def _a_person_not_a_hob(understood):
    """False for "my mum wont stop ringing me", true for "the ring takes ages to heat"."""
    clean = " ".join(str((understood or {}).get("clean") or "").lower().split())
    return not (_HOB_PERSON.search(clean) and _HOB_THE_PHONE.search(clean))


def _hob_heat(memory, reading):
    """A hob that is slow, or a ring that has stopped, answered for the hob the person has.

    Which check comes first is not the same on gas, induction and a ceramic top: a gas ring that
    will not light is a wet cap or a blocked jet, an induction ring that will not heat is usually
    the pan rather than the hob, and a ceramic ring that heats slowly is the element on its way
    out. One answer naming all three hides the one thing to check, so the sentence that opens
    says the thing to do first for the hob that was actually mentioned.
    """
    clean = reading.get("clean") or ""
    if _HOB_INDUCTION.search(clean):
        return ("Check the pan before the hob: an induction ring only heats a magnetic base, so a "
                "fridge magnet should stick to the bottom of the pan. If it does not, the pan is "
                "the problem, not the ring - and a pan narrower than the ring, or one lifted a "
                "centimetre off it, will not heat either. If the magnet sticks and the ring stays "
                "cold, switch it off at the wall for a minute and back on, and if that does not "
                "bring it back, the ring or its board has gone and it is a repair.")
    if _HOB_GAS.search(clean):
        return ("Take the cap and the burner head off and check the holes first: they block with "
                "spill and grease, and a damp cap after cleaning will not light until it dries. "
                "Scrub the holes with a pin or a brush, dry the parts properly and put them back "
                "flat. If the igniter clicks but nothing lights, it is the spark jumping to the "
                "wrong place or a blocked jet, and a jet is an engineer's job because it has to "
                "be the right size for the gas.")
    return ("On a ceramic or solid-plate hob a ring that takes ten minutes to glow is the element "
            "on its way out, and one ring that never heats at all is either that element or the "
            "switch behind the knob: turn the knob and listen for the click, because a switch that "
            "clicks but heats nothing points at the element. Both parts are cheap, and neither is "
            "a job for anyone who is not happy turning the power off at the fuse box first.")


def _iron_fault(memory, reading):
    """An iron that spits, drips, leaves marks or will not heat, told apart by what it does.

    Water coming out is the iron too cool for steam, or filled past the line: below the steam
    setting the water is pumped at a soleplate that cannot turn it to steam and it comes out as
    droplets. Brown or white marks are scale, which is a cleaning job on the same appliance. A
    soleplate that never gets hot is a different fault with a different first check, so the
    opening sentence says which one the line is about.
    """
    clean = reading.get("clean") or ""
    if _IRON_SCALE.search(clean):
        return ("That is scale, not a fault: fill the tank with a mix of half water and half white "
                "vinegar, stand the iron upright and let it steam itself empty over an old towel, "
                "then fill with clean water and press the steam burst a few times to rinse it out. "
                "Use the self-clean button if it has one. Once it runs clear it will stop marking, "
                "and if it keeps marking after that, the soleplate wants a wipe with a cloth and "
                "bicarbonate of soda while it is warm but unplugged.")
    if _IRON_COLD.search(clean):
        return ("Check the fuse in the plug first, then the flex where it goes into the iron at "
                "the heel: a wire broken there is the commonest reason an iron goes dead, because "
                "that is the part that bends every time you use it. Wiggle the flex with it "
                "plugged in and see if the light flickers. If the light comes on and the soleplate "
                "still stays cold, it is the thermostat or the thermal fuse, and on a cheap iron "
                "the part costs more to fit than a new one.")
    return ("The iron is not hot enough for the steam setting: water only turns to steam at the "
            "top of the range, so below it the pump pushes water at a soleplate that just spits it "
            "out. Turn the dial to the steam or max setting, wait for the light to go out, and only "
            "then press the steam button. Also check the tank is not over the max line, and empty "
            "it after each use, because water left standing in it is what turns to scale.")


_HEAT_CHEM = re.compile(r"\b(?:magnetron|thermostat|element|heating element|thermal fuse)\b")


def _small_appliance_not_heating(memory, reading):
    """A microwave, a kettle or a toaster that will not heat, each with its own first check.

    They fail the same way and have different cheap fixes, so the appliance the line names
    picks the sentence. A microwave that lights up and runs but leaves the food cold is the
    magnetron or its high-voltage fuse, which is not a job for anyone without the meter and the
    knowledge, because the capacitor holds a charge after it is unplugged. A kettle that will
    not heat is usually the base contacts or the plug fuse, and a new kettle is cheaper than a
    repair. A toaster that will not heat is a broken element or a timer.
    """
    said = str((reading or {}).get("clean") or "").lower()
    if any(_says(said, word) for word in ("microwave", "microwaves", "microwave oven")):
        return ("Check the plug fuse and the door first: a microwave that thinks the door is "
                "open runs the fan and the light and no microwaves. If it lights up and turns "
                "but the food stays cold, the magnetron or its high-voltage fuse has gone, and "
                "that is an engineer's job, not a DIY one - the capacitor holds a lethal charge "
                "after the plug is out. Most repairs cost more than a new microwave.")
    if any(_says(said, word) for word in ("kettle", "kettles")):
        return ("Check the fuse in the plug and try another socket first, then look at the "
                "contacts in the base: the ring of metal there corrodes and scales and stops "
                "passing current, which is the usual reason a kettle stops heating rather than "
                "dying. If the switch clicks and nothing happens on another socket, the element "
                "has gone, and a kettle is cheaper to replace than to repair.")
    return ("Check the fuse in the plug and try another socket first, then the timer or the "
            "switch: on a toaster the element and the timer are what fail, and neither is worth "
            "replacing on a machine that costs what they cost. Look along the element in the "
            "dark with it switched on for a gap or a section that never glows.")


def _dryer_heat(memory, reading):
    """A dryer that will not heat, said as cold air or as clothes that take three goes.

    Both are one fault (the air cannot get through, or the heat is not being asked for), but the
    first thing to check is not the same for both: a slow dryer is nearly always the airflow, and
    a cold one is often the dial on a cool-down phase before it is any part at all. STYLE asks for
    the answer in the first sentence, so the sentence that opens says the thing to do first for
    the line that was actually sent.
    """
    words = set(reading.get("words") or ())
    slow = {"ages", "forever", "slow", "slower", "slowly", "long", "longer", "hours", "again",
            "twice", "ages.", "slowly.", "goes", "go", "cycles", "cycle", "damp", "damp.",
            "wet", "wet."}
    if words & slow:
        return ("Slow drying is nearly always the air: empty the fluff filter, rinse the condenser "
                "if it has one, and check the vent hose is not kinked. A drum stuffed full will not "
                "dry either, so try half a load. If the air still comes out cold, it is the fuse on "
                "the element - an engineer's job, cheap part.")
    return ("Nearly always the air or the setting, not a part: check the dial first, since most "
            "machines finish on a cool-down phase that heats nothing, then empty the fluff filter "
            "and check the vent hose is not kinked. If the drum turns and the air still comes out "
            "cold, it is the thermal fuse on the element - an engineer's job, cheap part.")


# "can i fix it myself" is asked after a fault far more often than it is typed as a whole
# question. Alone it is this entry's. In a thread the job is named in the turn before - "my
# radiator is cold at the top" then "can i bleed it myself", "my bike chain keeps slipping" then
# "can i fix it myself" - and the avoid list only sees the line it is answering, so the entry
# took turns whose own answer is the better one. So the reply looks back: when an earlier turn
# in the thread had an answer of its own, this one stands down and lets it hold the follow-up.
_DIY_ANSWER = (
    "More of it than people think: a tap washer, a door seal, a blocked filter, a belt or a "
    "trapped drain is a few pounds in parts and an hour's work, and there is a video for "
    "almost every make. Not the gas, a sealed boiler, or wiring, and nothing in a bathroom "
    "or kitchen that needs a certificate - those need a Gas Safe or registered engineer. "
    "Check the warranty before you open anything, and if the part costs less than the "
    "call-out (usually £50 to £100) it is worth a go.")


_DIY_AVOID = (
    # Everything that uses "myself", "my own" or "on my own" for something that is not a broken
    # thing in the house: the body, a haircut, money paperwork, a website, and the things whose
    # repair has its own answer (a car, a phone, a laptop, a bike, a watch).
    "hair", "haircut", "hair cut", "nails", "eyebrows", "beard", "dye",
    "teeth", "dental", "tattoo", "makeup", "make up",
    "hurt", "hurting", "harmed", "harm myself", "injur", "cut myself",
    "tax return", "tax", "self assessment", "accounts", "pension", "nis",
    "website", "server", "blog", "app", "cv", "c.v",
    # "will" on its own is not the future tense of a report: "can i fix it myself, will it void
    # the warranty" is one question in two clauses, and the wide word punted it. The report it
    # was guarding ("i will do it myself") is held by the ask gate now.
    "i will", "ill do", "i'll do",
    "lonely", "loneliness", "alone", "lives on my own", "live on my own",
    "car", "van", "motorbike", "motorcycle", "bike", "bicycle", "tyre", "tyres",
    "phone", "iphone", "laptop", "computer", "tablet", "ipad", "console",
    "watch", "tv", "television", "fridge seals", "oven clean", "battery",
    # A pair of glasses has its own answer and it is the better one: an optician does a frame
    # repair or fits the old lenses into a new frame for a few pounds, while the do-it-yourself
    # reply is a survey of washers and belts. "can i fix my glasses myself" read as a house job
    # and was answered with a tap washer.
    "glasses", "specs", "spectacles", "sunglasses", "optician", "my frames", "eyeglasses",
    # A car and the mains are two repairs where "worth a go" is the wrong advice, not a weak
    # one: the reply ends "if the part costs less than the call-out it is worth a go", and said
    # about brakes that is dangerous. The list cannot tell what is being fixed, so the words
    # that name these two jobs keep them out, and their own answers take the line.
    "brake", "brakes", "clutch", "exhaust", "engine", "gearbox", "mot", "oil change",
    "windscreen", "headlight", "suspension", "socket", "sockets", "wiring", "rewire",
    "rewiring", "fuse", "consumer unit", "light fitting", "electrics", "electrician",
    "circuit", "ring main", "earth wire", "shower", "immersion",
    # A broken thing that already has a how-to of its own is not a "should I have a go" question:
    # a dripping tap, a leaking pipe and a blocked drain all get the fix itself, which is the
    # better answer than a survey of what is worth doing yourself. "tap washer" is deliberately
    # not here - that one is the job this entry exists for.
    "dripping tap", "dripping taps", "tap dripping", "leaking tap", "tap leak", "taps drip",
    "pipe", "pipes", "leak", "leaking", "burst", "blocked drain", "drain is blocked",
    # The job named in the line has its own answer, and it is the better one: a radiator that
    # needs bleeding and a boiler that needs servicing are jobs, not do-it-yourself questions,
    # and the line says which. The "it" rows are what this entry is for, and they name no job.
    "radiator", "radiators", "boiler", "boilers", "thermostat",
    "cook", "cooking", "bake", "baking", "bread", "yoghurt", "yogurt", "make my own")


# The word that names the job is often in the turn before this one: "my radiator is cold at the
# top" then "can i bleed it myself", "my bike chain keeps slipping" then "can i fix it myself",
# "i want to lose a few kilos" then "can i do it myself". The avoid list only sees the line it is
# answering, so on the follow-up this entry took a turn whose own answer is the better one. The
# reply reads the turns before it for these words and stands down, which leaves the thread to the
# answer it is following on from.
_DIY_EARLIER = ("radiator", "radiators", "boiler", "boilers", "thermostat", "bike", "bicycle",
                "chain", "car", "van", "motorbike", "phone", "laptop", "watch", "tv",
                "glasses", "specs", "spectacles", "sunglasses", "optician", "frames",
                "lose weight", "losing weight", "kilo", "kilos", "diet", "stones", "pounds",
                # the body, which the avoid list refuses on the line itself: "my back hurts"
                # then "can i fix it myself" is not a question about a tap.
                "hurt", "hurts", "hurting", "injur", "pain", "sore", "ache", "aches",
                "sprain", "my back", "my knee", "my shoulder", "my ankle", "my wrist",
                # a pair of glasses is repaired by an optician and its second half ("can i fix
                # them myself", "can i glue it back on") belongs to the pair, not to a tap washer
                "glasses", "spectacles", "specs", "sunglasses", "lenses", "frame")


def _diy(memory, reading):
    """The do-it-yourself answer, unless the turn before named a job with an answer of its own.

    The line being answered is the question ("can i fix it myself", "can i replace a tap washer
    myself"), so the job it names is this entry's business - otherwise the entry would answer
    every "myself" in the language, which the avoid list stops on the line itself. What it must
    not do is take a turn that is following on from one of those: "can i bleed it myself" after a
    cold radiator, "can i do it myself" after a diet. The words are looked for in the earlier
    turns only, so a line that names its own job is still answered here.
    """
    turns = (memory or {}).get("turns")
    if isinstance(turns, list):
        for turn in turns[-2:]:
            said = str((turn or {}).get("user") if isinstance(turn, dict) else "").lower()
            line = " " + " ".join(said.split()) + " "
            if any(word in line for word in _DIY_EARLIER):
                return None
    return _DIY_ANSWER
# How long the machine in the corner is meant to last, per the name WHITE_GOODS gives it. The
# years are the ordinary range for a machine that is looked after, not the guarantee, and the
# second half is the habit that decides which end of it you get: a person asking "how long does a
# washing machine last" is usually deciding whether the repair in front of them is worth paying,
# so the answer says both the number and what moves it.
APPLIANCE_LIFE = {
    "washing machine": ("eight to ten years",
                        "a hot 60C service wash once a month, a clean filter and a drum that is "
                        "never overloaded are what keep it at the top of that"),
    "tumble dryer": ("ten to thirteen years",
                     "emptying the lint filter after every load is the whole of it - a blocked "
                     "filter is what kills dryers"),
    "dishwasher": ("eight to ten years",
                   "rinsing the filter monthly and using salt if your water is hard keeps it at "
                   "the top of that"),
    "fridge": ("ten to fifteen years",
               "dusting the coils at the back once a year and keeping it out of a hot corner is "
               "most of it"),
    "freezer": ("ten to fifteen years",
                "a freezer kept full and defrosted when the ice thickens lasts longest"),
    "oven": ("ten to fifteen years",
             "the element and the thermostat are the parts that go and both are cheap to swap, so "
             "one fault is almost never a reason to replace it"),
    "cooker": ("ten to fifteen years",
               "the element and the thermostat are the parts that go and both are cheap to swap"),
    "hob": ("ten to fifteen years",
            "a ceramic or induction hob usually dies at the touch controls, so keep spills off them"),
    "microwave": ("seven to ten years",
                  "never run it empty and keep the door seal clean"),
    "boiler": ("ten to fifteen years",
               "an annual service is the whole of it; the last third of that range is where the "
               "repair bills start to beat a new one"),
    "vacuum cleaner": ("six to eight years",
                       "emptying the bin and washing the filters is most of it; the motor is what "
                       "fails in the end"),
    "kettle": ("three to five years",
               "descaling it now and then is most of it - the element is what scales up and dies"),
    "toaster": ("three to five years",
                "emptying the crumb tray and never poking a knife in it is most of it"),
    "hair dryer": ("four to six years",
                   "cleaning the filter at the back is what stops it overheating"),
    "blender": ("three to five years",
                "don't run it past a minute at a time; the motor is what goes"),
    "sandwich maker": ("five to eight years",
                       "wiping the plates and brushing the crumbs out after each use is most of it; "
                       "the hinge and the non-stick coating are what go first"),
    "mattress": ("eight to ten years",
                 "airing it and turning or rotating it every few months is what keeps it there"),
}
# A lifespan question names the machine and asks how long it goes on for. The verb is what says so:
# "how long does milk last in the fridge" names a machine and asks about the milk, so the food
# words in the entry's avoid stand it down and the fridge-life rows answer that line instead.
LIFE_WORDS = ("how long does", "how long do", "how long should", "how long will", "how long can",
              "how many years does", "how many years do", "how many years should",
              "how many years will", "life expectancy", "life span", "lifespan", "life of",
              "expected to last", "should last", "does last", "do last", "years of life",
              "how long is a", "how long is the life")
LIFE_THINGS = (tuple(name for pair in WHITE_GOODS for name in pair)
               + tuple(name for pair in SMALL_APPLIANCES for name in pair)
               + ("mattress", "mattresses"))


def _longest_named(said, table):
    """The longest name the line holds, so a short alias cannot stand in front of the thing.

    The tables keep short aliases beside the full names - "dryer" for a tumble dryer, "washer"
    for a washing machine - and the first match in table order reads the alias inside a longer
    name: "how long does a hair dryer last" answered about a tumble dryer, because bare "dryer"
    comes first and matches inside "hair dryer". Longest wins, and a tie keeps table order.
    """
    best = ""
    name = None
    for word, called in table:
        if len(word) > len(best) and re.search(r"\b" + re.escape(word) + r"s?\b", said):
            best, name = word, called
    return name


# An appliance named as the place a thing is kept or done in is not the appliance being aged:
# "how long does spinach last in the fridge" is the spinach, and the fridge sits there as a
# cupboard. The word in front is what says so, so the test is that shape and not a list of the
# foods, which can never be finished - spinach, lettuce, mushrooms, ham and soup all reached the
# fridge's ten to fifteen years while milk and chicken were safe only because somebody had
# written them down (urban-orange measured it, #3722).
def _named_as_a_place(said, names):
    """True when one of `names` follows "in the"/"out of the"/"from the": the fridge as a place.

    "how long does spinach last in the fridge" asks about spinach that is in the fridge, not
    about the fridge lasting, and the same shape covers every food nobody listed: "in the oven",
    "in the freezer", "in the cupboard". A line that asks how long the machine lasts ("how long
    does the fridge last") has no such phrase in it and is answered as before.
    """
    for match in re.finditer(r"\b(?:in|into|inside|out of|from|kept in|stored in|keep in|"
                             r"store in)\s+(?:the|a|an|my|our|your|his|her|their|this|that)\s+"
                             r"([a-z]+(?: [a-z]+)?)\b", said):
        after = match.group(1)
        for name in names:
            if after == name or after.startswith(name + " ") or name.startswith(after + " "):
                return True
    return False


# How long a machine takes to do the thing is the other question the lifespan table stands down
# on, and nothing answered it: "how long does a fridge take to get cold" was getting the
# cooked-food keeping card, and "how long does a dishwasher take to run" the exercise one. One row
# per machine, and the machine has to be the whole of the question after its name - a chicken or a
# joint of meat in the oven is a cooking time, not the oven's warm-up.
MACHINE_TAKES = {
    "fridge": ("about 4 hours to get cold, and up to 24 hours for a fridge-freezer's freezer side",
               "put the food in once it is down to temperature, and put a few bottles of water in "
               "the gaps - a full fridge holds its temperature far better than an empty one"),
    "freezer": ("up to 24 hours to reach -18C from new",
                "leave it empty and shut until then, and when you move house keep it packed and "
                "shut - a full freezer stays frozen for a day"),
    "oven": ("10 to 15 minutes to reach 180C (160C fan)",
             "the light going out is the thermostat cutting in, not the shelves; a fan oven "
             "reaches temperature in about 5 minutes"),
    "washing machine": ("about 2 hours for a normal cotton wash at 40C, and 3 hours or more on "
                        "an eco cycle",
                        "the quick programme is 15 to 30 minutes for a lightly worn load, and a cold "
                        "wash takes the same time as a hot one"),
    "dishwasher": ("about 2 hours on a normal cycle",
                   "an eco cycle runs longer, 3 hours or more, because it heats the water slowly "
                   "and uses less of it"),
    "tumble dryer": ("1 to 2 hours for a full load",
                     "a spin at the end of the wash cuts it, and so does clearing the lint filter"),
    # A boiler has a turn-round time too, and "how long does a boiler take to heat water" was
    # answered with the machine's ten to fifteen years, because this table had no row for it and
    # the lifespan row took the line back. The two answers are not the same question.
    "boiler": ("a few seconds for hot water at the tap and about 20 to 30 minutes to warm the "
               "radiators from cold",
               "a combi boiler is the fast one because it heats water as you use it, a hot water "
               "tank takes its own half hour to refill and reheat, and radiators that stay cold at "
               "the top want bleeding"),
}
# The words that may follow the machine's name and still leave it the subject of the question.
_TAKE_WORDS = frozenset((
    "take", "takes", "taking", "to", "get", "gets", "cold", "chilled", "cool", "cooled", "down",
    "up", "heat", "heated", "warm", "preheat", "boil", "run", "running", "a", "load", "wash",
    "dry", "cycle", "finish", "reach", "temperature", "its", "for", "and", "the", "my", "an",
    # "how long does a boiler take to heat water" is the same question as the radiators
    "water", "hot", "radiator", "radiators",
    "of", "time", "how", "long", "does", "do", "is", "it", "on", "in", "come", "comeup", "warmup",
    # the words people put round the question without changing it: "how long does a new fridge
    # take to cool down", "roughly how long does an oven take to heat up"
    "new", "brand", "roughly", "about", "usually", "normally", "typically"))


TAKES_THINGS = tuple(name for pair in WHITE_GOODS + SMALL_APPLIANCES for name in pair)


def _how_long_a_machine_takes(said):
    """The machine whose turn-round time this line asks for, or "" - the food in it is not it.

    The longest name wins, so "how long does a hair dryer take" is not read as the alias "dryer"
    inside it and given the tumble dryer's hour or two.
    """
    best, found = "", ""
    for word, called in WHITE_GOODS + SMALL_APPLIANCES:
        # every name is read, not just the ones with a row: a machine this table has no time for
        # must stand the row down rather than let a shorter alias inside its name answer
        if len(word) <= len(best):
            continue
        for match in re.finditer(r"\b" + re.escape(word) + r"\b", said):
            words = re.findall(r"[a-z]+", said[match.end():])
            # The words in front of the name are read too: "how long does it take for a fridge to
            # get cold" puts the take before the machine, and reading only what follows it left
            # that line on the cooked-food keeping card. Both sides have to be the question, so a
            # chicken or a joint of meat in the oven still stands the row down.
            ahead = re.findall(r"[a-z]+", said[:match.start()])
            # "take"/"takes" has to be there, or "how long does a fridge take to get cold" and a
            # line that only names the machine would be the same question
            if (words or ahead) and ("take" in words + ahead or "takes" in words + ahead) \
                    and all(w in _TAKE_WORDS for w in words + ahead):
                best, found = word, called
                break
    return found if found in MACHINE_TAKES else ""


# "Takes" is two questions, and this row was answering only the first: how long a machine needs is
# the turn-round time, and a machine that needed *two goes* at the job is a fault. "the tumble dryer
# takes two goes to dry a load" reached this row on "takes" and was handed a blank - there is no time
# to give a line that is not asking how long - while the drying row answered it with a clothes rack.
# The shape is A_JOB_LEFT_UNDONE in wording.py, read here, in clothing.py and by the fault rows, and
# the answer for the machine is the one already written for its fault.
def _the_job_needed_twice(memory, reading, said):
    """The fault answer for a machine that had to do the job twice, or left it undone."""
    if not any(phrase in said for phrase in A_JOB_LEFT_UNDONE):
        return ""
    machine = _longest_named(said, WHITE_GOODS + SMALL_APPLIANCES)
    if machine == "tumble dryer":
        return _dryer_heat(memory, reading)
    return ""


def _machine_takes(memory, understood):
    reading = understood if isinstance(understood, dict) else {}
    said = str(reading.get("clean") or reading.get("plain") or "").lower()
    thing = _how_long_a_machine_takes(said)
    if not thing:
        return _the_job_needed_twice(memory, reading, said)
    takes, tip = MACHINE_TAKES[thing]
    article = "An" if thing[0] in "aeiou" else "A"
    return "%s %s takes %s. %s." % (article, thing, takes, tip[0].upper() + tip[1:])


def _appliance_life(memory, understood):
    """The years the named machine is good for, and the habit that decides which end of them."""
    reading = understood if isinstance(understood, dict) else {}
    said = str(reading.get("clean") or reading.get("plain") or "").lower()
    names = tuple(word for word, _called in WHITE_GOODS + SMALL_APPLIANCES)
    if _named_as_a_place(said, names + ("mattress",)):
        return ""
    if (_FIRST_PERSON.search(said) and not _A_LIFE.search(said)
            and not _spans_plural(said, ("white goods", "appliances", "appliance"))):
        # "how long should i microwave porridge" is the machine being used, not aged: the same
        # fence the years row in the other table reads, because this row now wins such lines
        return ""
    if _HOLDS.search(said) and _HOLDS_A_THING.search(said) and not _A_LIFE.search(said):
        # "how long does a freezer stay cold without power" asks how long it holds what is in it,
        # which the keeping and power cut tables answer, not how many years it lasts. The held
        # thing has to be named: "stay good", "stay firm" and "stay comfortable" are the life
        # question, and "hold water" is a fault, so the verb alone is not enough.
        return ""
    if _longest_row(said, LIFESPAN):
        # the other table has a row written for this machine, so its sentence answers this life
        # question - returning nothing here would let whatever keeps in an oven answer it instead.
        # A line that asks how long a machine runs or stays cold is left to the row for that.
        return _lifespan(memory, understood)
    thing = _longest_named(said, WHITE_GOODS + SMALL_APPLIANCES + (("mattress", "mattress"),))
    if not thing or thing not in APPLIANCE_LIFE:
        # a name in the reading tables with no row here is a gap in this table, not a reason to
        # fall over: the line goes to whatever else can answer it
        return ""
    years, habit = APPLIANCE_LIFE[thing]
    article = "An" if thing[0] in "aeiou" else "A"
    return ("%s %s usually lasts about %s if it is looked after, and %s. Repair it while a fix is "
            "well under half the price of a new one; replace it once it needs two repairs in a "
            "year, or the parts are no longer made." % (article, thing, years, habit))


# --- a fitting that has come loose, come off or stopped shutting -------------------
# "the cupboard door is hanging off" and "the kitchen tap is loose" were "Got it - is there
# anything you'd like a hand with?", "the cupboard shelf has snapped" was a frittata ("Quick: tuna
# pasta in 15"), "a kitchen cupboard door that hangs crooked" was how to clean a cupboard, and
# "the cupboard door wont stay shut" and "the window wont shut" got hinge oil, which is the wrong
# part on all three. One table of fittings: the fitting says which part it is, and the shared move
# for a screw that has pulled out of chipboard is said once.
SCREW_HOLE = ("If the screw spins, the hole has stripped the board: push matchsticks or a dowel "
              "dipped in wood glue into it, leave an hour, then screw back in.")
FITTING_TEXT = {
    "oven": ("An oven door that will not shut is almost always the hinge, not the door: open it "
             "wide and look for a bent or snapped hinge arm, and check nothing is jamming the seal "
             "or the shelf lip. A hinge arm is a cheap part - quote the oven's model number, and it "
             "is usually two screws to change."),
    "cupboard": ("A cupboard door hanging off has pulled its hinge screws out of the board: take "
                 "the door off, fill the holes and screw the hinge back where it was. If the hinge "
                 "plate is bent, a new pair is a few pounds."),
    "catch": ("A cupboard door that will not stay shut is the catch, not the hinges: a magnetic or "
              "roller catch lives on the inside edge, one half on the door and one on the carcass. "
              "Shut it and see whether the two halves touch - if they miss, slacken the screws and "
              "move the plate a millimetre, or fit a new catch for a couple of pounds."),
    "crooked": ("A door that hangs crooked is set on the hinge, not by eye: the two screws on the "
                "cabinet side of each hinge plate move the door up and down and in and out. "
                "Slacken them a quarter turn, nudge the door, tighten, and try it closed; the screw "
                "nearest the door edge sets the gap."),
    "tap": ("A tap that rocks is loose on the sink, not broken: go underneath and tighten the back "
            "nut or the clamp that holds the body to the worktop, and if the whole tap turns look "
            "for the small grub screw behind the base that locks it. A tap that drips is a washer "
            "or cartridge, which is a different job."),
    "shelf": ("A snapped shelf is a new board, not a repair: measure the width, the depth and the "
              "thickness (15 or 18 mm is usual) and ask a timber yard or DIY shop to cut one to "
              "size - a few pounds, or ask for a white melamine shelf the same depth. If the pin "
              "holes have crumbled, fit a shelf support bracket instead of trusting the pins."),
    "drawer": ("Drawer runners are a part you replace, not mend: pull the drawer right out and "
               "measure the length of the runner, and whether it fits on the side or underneath. "
               "Buy the pair, sold by length and by side or under, and swap them - two screws at "
               "the back and two at the front of each side."),
    "window": ("A window that will not shut is usually out of line, not broken: check nothing is "
               "jamming the frame - a blind, a latch, a stone chip - then turn the handle and see "
               "whether the bar in the sash edge lines up with the keep on the frame. Lift or push "
               "the sash across to meet it. A handle that spins means a broken spindle, and that is "
               "a window fitter."),
}
# "my oven is broken" and "my cooker is broken" are a whole machine that has stopped, and they
# were given a hinge arm to change: the fitting card is for a part, so it stands down unless the
# line names one. A line that does name a part keeps whichever answer it had.
_OVEN_PART = ("door", "doors", "hinge", "hinges", "seal", "seals", "shelf", "shelves", "shelf lip",
              "runner", "runners", "handle", "handles", "knob", "knobs", "glass", "light", "timer",
              "fan", "element", "shut", "shuts", "shutting", "close", "closes", "closing",
              "closed", "stay shut", "stay closed", "drops", "dropped", "drooping", "sagged",
              "sagging", "swings open")

# A "not this fitting" word keeps the answer with whichever entry already had it: a dripping tap,
# a window stuck open with paint, an oven that will not heat and the mould inside a wardrobe are
# all different jobs.
FITTING_STANDDOWN = {
    "oven": ("clean", "cleaning", "burnt", "bake", "baking", "roast", "temperature", "heat",
             "heats", "gas", "glass", "ceramic", "hob", "fan", "element", "smell", "smoke",
             "self clean", "chips", "preservative", "replacement", "timer", "thermostat"),
    "tap": ("drip", "drips", "dripping", "dripped", "leak", "leaks", "leaking", "running",
            "cartridge", "washer", "garden tap", "beer tap", "outside tap", "hot water",
            "cold water", "water pressure", "tap water", "limescale", "scale", "boiling",
            "drinking"),
    "window": ("stuck", "paint", "painted", "opening", "wont open", "won't open", "draft",
               "draught", "condensation", "clean", "cleaning", "blind", "curtain", "curtains",
               "quote", "replace", "broken glass", "cracked", "double glazing",
               # A smashed window is not a window that will not shut, and this card opened by
               # saying so: "how do i fix a broken window" and "someone broke my window" were
               # told to check the handle and the keep (early-badge, #4083). The break words
               # hand the line to the broken-window card, which is where the price is too.
               "broken window", "window is broken", "window was broken", "broke my window",
               "broke the window", "someone broke", "somebody broke", "smashed", "shattered",
               "put through", "pane", "panes", "glass broke", "board up", "boarded up"),
    "shelf": ("book", "books", "oven shelf", "fridge shelf", "shelf life", "freezer",
              "supermarket", "shopping", "shelving unit", "tv"),
    "drawer": ("bedside", "cutlery", "junk", "sock", "socks", "bank", "underwear", "under bed"),
    "catch": ("smell", "smells", "mould", "mold", "damp", "clean", "cleaning", "organise",
              "organize", "tidy", "clothes", "hoover", "vacuum"),
}

# "my oven is broken, is it worth it" is the repair-or-replace decision, not the part: those
# words stand every fitting down, because the answer is a judgement on the machine. They are in
# the entry's `avoid` rather than the callable, because the entry has to lose the *score* for the
# line - a callable that returns None still wins the entry the line was measured against.
# A tenant asking about a landlord is not asking how to do the job: "the oven is broken and the
# landlord wont fix it" got a hinge tutorial, and the person needed the letter that makes the
# landlord act (mint-wolf, #40500, reproduced by sure-wombat and early-badge). The tenancy
# phrasings stand the DIY answers down; the bare word `landlord` would also stand down lines
# that name the fault as well, so both are here and the landlord entry takes them instead.
FITTING_SHARED_STANDDOWN = ("landlord", "landlords", "letting agent", "letting agency",
                            "landlady", "my tenancy", "won't fix it", "wont fix it",
                            "wont fix", "won't fix", "refuses to fix", "refusing to fix",
                            "worth it", "worth fixing", "worth repairing", "is it worth",
                            "worth a repair", "repair or replace", "replace or repair",
                            "replace it", "buy a new one", "new one", "cheaper to replace",
                            "drip", "drips", "dripping", "dripped", "leak", "leaks", "leaking",
                            "washer", "cartridge", "stuck", "paint", "painted", "shelf life")

# The words a line can use to be about a cupboard. A cupboard has no fitting word of its own, so
# these are what the table's last resort is for: "the cupboard door is hanging off", "how do i
# clear out my pantry", "the wardrobe door has dropped". A follow-up that names no thing ("i fixed
# the tap" / "it worked") is not one of them, and the table passes on it rather than changing the
# subject - that line was told to take a cupboard door off and fill its hinge holes.
_CUPBOARD_WORDS = ("cupboard", "cupboards", "cupboard door", "cupboards doors", "door", "doors",
                   "hinge", "hinges", "hinge plate", "catch", "catches", "latch", "latches",
                   "cabinet", "cabinets", "kitchen unit", "kitchen units", "unit", "units",
                   "wardrobe", "wardrobes", "pantry", "pantries", "cupboard door", "drawer front",
                   "shelf pin", "shelf pins", "larder")


def _names_a_cupboard(said):
    """Whether the line has a word in it that a cupboard can be the answer to."""
    said = str(said or "").lower()
    return any(re.search(r"\b" + re.escape(word) + r"\b", said) for word in _CUPBOARD_WORDS)


# The order the fitting is looked for: the thing named first wins, so "the cupboard door that
# hangs over the tap" is the cupboard. `catch` and `crooked` are the two cupboard faults with a
# different part behind them, so they come last and only after no fitting has been named.
_FITTING_ORDER = ("oven", "shelf", "drawer", "window", "tap")
_FITTING_WORDS = {
    "oven": ("oven", "cooker", "range cooker", "grill"),
    "shelf": ("shelf", "shelves", "shelving"),
    "drawer": ("drawer", "drawers"),
    "window": ("window", "windows", "sash", "casement"),
    "tap": ("tap", "taps", "faucet", "mixer"),
}
_STAY_SHUT = ("wont stay shut", "won't stay shut", "will not stay shut", "wont stay closed",
              "won't stay closed", "swings open", "swing open", "pops open", "keeps opening",
              "wont close", "won't close", "wont shut", "won't shut")
_CROOKED = ("crooked", "hangs low", "hanging low", "dropped", "out of line", "doesnt line up",
            "doesn't line up", "adjust", "misaligned", "gap at the top")


def _fitting_repair(memory, understood):
    """The part behind the fitting the line names, or None when that job is another entry's."""
    said = " ".join(str(part) for part in (
        (understood or {}).get("clean"), (understood or {}).get("text"),
        " ".join((understood or {}).get("words") or ()))).lower()
    kind = None
    for name in _FITTING_ORDER:
        if any(re.search(r"\b" + re.escape(word) + r"\b", said) for word in _FITTING_WORDS[name]):
            kind = name
            break
    if kind is None:
        # The thing the line is about can be named in a spelling the fitting table cannot
        # find: "my winda wont shut" is a window, and with no fitting to name, the shut
        # phrases below read it as a cupboard. The reading already knows what the line is
        # about, so the subject it worked out names the fitting when the words do not.
        named = set(re.findall(r"[a-z]+", str((understood or {}).get("subject") or "").lower()))
        for name in _FITTING_ORDER:
            if named & set(_FITTING_WORDS[name]):
                kind = name
                break
    if kind is None:
        if any(phrase in said for phrase in _STAY_SHUT):
            kind = "catch"
        elif any(phrase in said for phrase in _CROOKED):
            kind = "crooked"
        elif _names_a_cupboard(said):
            kind = "cupboard"
        else:
            return None
    # A line that asks who to call has already decided that somebody comes out, and the trade
    # table further down this file answers it: "who do i call about a broken window" is a glazier,
    # not a hinge to adjust by hand.
    if TRADE_ASKS.search(said):
        return None
    if kind == "oven" and not any(word in said for word in _OVEN_PART):
        # a machine that has stopped is the appliance card's line, not a hinge to change
        return None
    if any(word in said for word in FITTING_STANDDOWN.get(kind, ())):
        return None
    if any(phrase in said for phrase in FITTING_SHARED_STANDDOWN):
        return None
    text = FITTING_TEXT[kind]
    if kind == "cupboard":
        text = text + " " + SCREW_HOLE
    return text
# Bath and "bath" are two different things in English, and a card keyed on the word alone will
# answer "best hotel in bath" with a shower. The travel answers live in travel.py, so the shower
# cards stand down whenever the line is about the city.
_BATH_CITY = ("to bath", "in bath", "from bath", "at bath", "visit bath", "visiting bath",
              "bath spa", "roman baths", "the roman baths", "hotel", "hotels", "weekend",
              "day trip", "day out", "weekend break", "stay in", "staying in", "bristol",
              "journey", "trip to bath", "train to bath", "things to do", "sights",
              "best time to visit", "see bath", "in a day")

# "do i need to shower every day" and "shower every day yes or no" were getting the bath-length
# paragraph, which opens on how long a bath lasts and then guesses at the question in its second
# sentence. The two asks in the entry - how long, and how often - want different openings.
_BATH_EVERYDAY = ("every day", "daily", "every morning", "every night", "twice a day",
                  "how often", "how many times", "need to shower", "need to bathe",
                  "need a shower", "yes or no")


def _bath_length(memory, understood):
    text = str((understood or {}).get("norm_text") or (understood or {}).get("text") or "")
    if any(word in text for word in _BATH_EVERYDAY):
        return ("Every day is fine for most people: it is long hot showers and harsh soap that "
                "leave skin tight and itchy, not the water itself. A five-minute warm shower "
                "daily is plenty, and every other day is enough if you wash the face, armpits "
                "and groin in between, unless you have been sweating or it is hot. If your skin "
                "still feels dry, shorten the shower and turn the heat down before you cut one "
                "out.")
    # A shower question wants the shower number first: "how long should my shower be" was still
    # opening "A bath is at its best around 15 to 20 minutes", which is the confident answer to a
    # different question.
    if "shower" in text and "bath" not in text:
        return ("Five to ten minutes is long enough for a shower, and heat matters more than "
                "length: keep it warm rather than hot and pat dry instead of rubbing, because "
                "long hot water is what leaves skin tight and itchy. A bath wants 15 to 20 "
                "minutes; past that the water is cooling and you can come out light-headed.")
    return ("A bath is at its best around 15 to 20 minutes: past that the water is cooling, your "
            "skin dries out and you can come out light-headed, and a shower is long enough at "
            "five to ten minutes. Heat matters more than length, so keep it warm rather than hot "
            "and get out slowly if you feel the room spin.")


# "how much does it cost to replace a window" was answered with the make-safe card, which has a
# price in its third sentence and opens with a bin bag. A price question gets the price first
# (ample-ox and soft-bag, #3207), and the same card reads the same way for a break.
_WINDOW_COST = (
    "Budget 80 to 150 pounds for a single pane fitted, 150 to 300 for a sealed double-glazed "
    "unit, and often nothing for an emergency board-up if it goes through your insurer or the "
    "landlord; cutting and puttying a single pane in a wooden frame yourself is about 15 to 30 "
    "pounds of glass and an afternoon. ")
_WINDOW_SAFE = (
    "Make it safe tonight: sweep the glass up in a box, tape a bin bag or a sheet of card over "
    "the hole from the inside and shut the room off, and if it is a ground-floor window a sheet "
    "of hardboard screwed over the frame is worth the ten minutes. Then it is two different "
    "jobs: a single pane in a wooden frame you can do yourself with cut glass, putty and a "
    "couple of hours, where a glazier coming out is usually 60 to 150; a double-glazed sealed "
    "unit cannot be paned at home, the whole unit is replaced, so get two quotes. If you rent, "
    "the landlord pays unless you broke it; if it was a break-in or the wind, tell your insurer "
    "before you throw the glass away and photograph the frame.")
_WINDOW_COST_RE = re.compile(
    r"\b(?:cost|costs|costing|price|prices|priced|pricing|expensive|cheaper|cheapest|cheap|"
    r"quote|quotes|pay|pays|paid|budget|charge|charges|worth)\b|\bhow much\b")
_WINDOW_ASKS = ("how much", "how expensive", "what does it cost", "what would it cost")


def _broken_window(memory, understood):
    """The same answer, with the price first when the line is asking what it costs."""
    clean = " ".join((understood.get("clean") or "").lower().split())
    # "who fixes a broken window" asks which trade, not what to do tonight, and the trade table
    # answers it: the make-safe card stands down for the same shape `_fitting_repair` does.
    if TRADE_ASKS.search(clean):
        return None
    asked_price = bool(_WINDOW_COST_RE.search(clean)) or any(
        phrase in clean for phrase in _WINDOW_ASKS)
    return (_WINDOW_COST + _WINDOW_SAFE) if asked_price else _WINDOW_SAFE


# --- who to call about a job ---------------------------------------------------------------
# "who do i call about a blocked drain" was the Telephone Preference Service, because "blocked"
# and "call" are both key words of the nuisance-calls row; "who do i call about a smelly drain"
# was a search hedge, and "who do i call about my damp wall" got the damp answer, which says
# where the water comes from instead of who comes to look at it. A person who asks who to call
# has already decided that somebody comes out, so the trade is the first word of the answer.
TRADE_ASKS = re.compile(
    r"\b(?:who (?:can|do|should|could|would|will|shall) i (?:call|ring|get|use|find|hire)|"
    r"who to (?:call|ring)|"
    # "who can fix a leaking tap", "who fixes a broken window", "who can service my boiler": the
    # same question said with the job for a verb. It was the search hedge and the make-it-safe
    # card for the window, because only "call" and "ring" asked for a trade.
    r"who (?:can|could|should|would|will) (?:i )?"
    r"(?:fix|mend|repair|service|fit|install|replace|look at)\b|"
    r"who (?:fixes|mends|repairs|services|fits|installs)\b|"
    r"which (?:engineer|tradesman|trade|firm)|what kind of (?:engineer|tradesman)|"
    r"is there someone i can (?:call|ring)|someone to (?:call|ring))\b", re.I)

# The thing said and the trade that owns it. The order is the answer, and it is not alphabetical:
# a leaking roof is a roofer before it is a plumber, a gas boiler is Gas Safe before anything,
# and a machine of your own is a white-goods engineer before it is any trade at all.
TRADES = (
    (("boiler", "gas boiler", "gas fire", "gas hob", "gas cooker", "gas work", "gas engineer"),
     "A Gas Safe engineer, not a general plumber: gas work is theirs by law and a plumber without "
     "the ticket cannot touch it. Ask for a fixed call-out price, say what the boiler is doing, "
     "and check their number on the Gas Safe Register before you book."),
    (("electrics", "electrical", "electrician", "wiring", "socket", "sockets", "fuse box",
      "consumer unit", "lighting", "tripping", "trips", "short circuit", "rcd"),
     "A registered electrician, not a handyman: the wiring, the sockets, the fuse box and lights "
     "that keep tripping are theirs, and in the UK the work has to be certified. Say whether the "
     "whole house is off or only one circuit."),
    (("roof", "roofs", "roofing", "roofer", "gutter", "gutters", "chimney", "flashing",
      "slate", "slates", "tile", "tiles"),
     "A roofer, and ask them to find the leak rather than quote for a new roof: say where the "
     "stain is inside, and get a written quote with the scaffolding in it, because the "
     "scaffolding is often half the bill."),
    (("drain", "drains", "drainage", "sewer", "sewers", "manhole", "soakaway", "septic tank",
      "outside pipe", "outside pipes"),
     "A drain company, or a plumber if the slow one is a sink, a bath or a toilet: the drain firm "
     "has the rods and the camera. Ask the price to clear it and the price to camera it, because "
     "only the camera finds a collapsed pipe."),
    (("window", "windows", "glass", "glazier", "patio door", "double glazing", "window pane"),
     "A glazier for broken glass, and a window fitter or a carpenter for a frame that has dropped "
     "or will not shut. Say which one it is on the phone, and ask for the call-out price before "
     "they come."),
    (("lock", "locks", "locksmith", "locked out", "broken key", "key snapped", "snapped in"),
     "A locksmith, and ask what it costs to open the door before they set off: one who will not "
     "give a price on the phone charges by the hour at your door. Check they are local, and ask "
     "whether the price includes a new lock."),
    (("door", "doors", "front door", "back door", "door frame", "sagging door", "garden gate",
      "gate", "gates", "fence", "fences", "fencing", "decking", "shed", "sheds", "joiner",
      "carpenter"),
     "A joiner or carpenter for a door, a gate or a fence panel, and a locksmith instead if the "
     "lock is the part that has gone. Send a photo of the job first: a door that will not shut is "
     "often a hinge to adjust, and a fence panel is a panel rather than a visit."),
    (("wasp", "wasps", "wasp nest", "nest", "mice", "mouse", "rat", "rats", "pest", "pests",
      "bedbugs", "bed bugs", "cockroach", "cockroaches", "squirrel", "squirrels", "pigeon",
      "pigeons"),
     "A pest controller, and most give a price over the phone: say what you have seen and whether "
     "it is inside, because wasps in a loft and mice in a kitchen are different jobs. The council "
     "still does rats and mice in some areas, usually cheaper than a firm."),
    (("damp", "damp patch", "wet patch", "mould", "mold", "condensation", "rising damp"),
     "A damp surveyor, not a builder who sells the treatment: a wet patch is usually a leak, a "
     "gutter or water coming up, and a survey should name the water before anything is injected. "
     "Ask whether the survey is free and whether the firm sells the work as well."),
    (("washing machine", "dishwasher", "tumble dryer", "tumble drier", "fridge", "freezer",
      "oven", "cooker", "appliance", "white goods"),
     "A white-goods engineer who covers your make: the maker's own service while it is under "
     "warranty, otherwise a local one with reviews. Ask for a fixed call-out price, and weigh the "
     "quote against half the price of a new one."),
    (("tree", "trees", "tree surgeon", "branch", "branches", "hedge", "hedges", "stump", "ivy"),
     "A tree surgeon with insurance, and ask to see the certificate before anyone climbs: say how "
     "close the tree is to the house or the wires, and get the price for taking the waste away, "
     "because that is often half the cost."),
    (("leak", "leaks", "leaking", "drip", "dripping", "pipe", "pipes", "tap", "taps",
      "radiator", "radiators", "toilet", "shower", "sink", "bath", "stopcock", "water"),
     "A plumber: a dripping pipe, a leak under a sink, a tap or a radiator is theirs. Turn the "
     "water off at the stopcock first, and ask for a fixed call-out price before they come."),
)
# A line that names a person or an organisation already has an answer of its own, and the trade
# table must keep out of it: the landlord, the council, the insurer, the vet.
NOT_A_TRADE_WORDS = ("landlord", "landlady", "letting agent", "council", "housing association",
                    "insurer", "insurance", "solicitor", "police", "doctor", "gp", "vet",
                    "boss", "employer", "school", "neighbour", "neighbor", "friend",
                    "family", "mum", "dad",
                    # drains in the street are the council's (see drain branch)
                    "in the street", "in the road", "on the street", "on the road",
                    "street drain", "road drain", "gully", "gulleys", "gullies",
                    "pavement", "kerb", "curb", "highway", "highways")
NOT_A_TRADE = re.compile(r"\b(?:" + "|".join(NOT_A_TRADE_WORDS) + r")\b")


def the_trade_to_call(memory, understanding):
    """The trade for a "who do i call about X" line, or "" when the line does not ask that."""
    line = " ".join(str((understanding or {}).get("clean")
                        or (understanding or {}).get("text") or "").lower().split())
    if not TRADE_ASKS.search(line):
        return ""
    if NOT_A_TRADE.search(line):
        return ""
    reply = _trade_for(line)
    if reply:
        return reply
    # "who do i call" is the whole question after "my roof is leaking", and the thing to call
    # about is the line before: the trade is read off that turn, the same way the machine rule
    # reads its machine.
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return ""
    earlier = " ".join(str((turns[-1] or {}).get("user") or "").lower().split())
    if earlier and not NOT_A_TRADE.search(earlier):
        reply = _trade_for(earlier)
        if reply:
            return reply
    # "my boiler is making a banging noise" / "is it dangerous?" / "who do i call?" was the
    # search hedge: the middle turn is about the boiler but names no trade, so reading only the
    # last line lost it. A follow-up carries the thing it is about in `leans_on`, which is the
    # earlier line the reading says this one leans on, so the trade is read off that too - but
    # only when the line before was such a follow-up. A line that brings its own thing ("my cat
    # is sick", "the tap is dripping") is what the question is about, and the boiler before it
    # is not: `topics` records the subject lines, so its last turn says which this is.
    topics = (memory or {}).get("topics") if isinstance(memory, dict) else None
    last_turn = len(turns) - 1
    if isinstance(topics, list) and any(
            isinstance(one, dict) and one.get("turn") == last_turn for one in topics):
        return ""
    leans_on = (understanding or {}).get("leans_on") if isinstance(understanding, dict) else None
    if isinstance(leans_on, dict) and leans_on.get("text"):
        leans_on_line = " ".join(str(leans_on["text"]).lower().split())
        if leans_on_line and not NOT_A_TRADE.search(leans_on_line):
            reply = _trade_for(leans_on_line)
            if reply:
                return reply
    # "is that dangerous" can be the whole of the follow-up, with no `leans_on` subject to
    # carry the thing forward ("my electrics keep tripping" does not). The line before that
    # follow-up is then the thing asked about, and it is one line back, not a subject of its
    # own the guard above would have stopped at.
    if len(turns) >= 2:
        prior = " ".join(str((turns[-2] or {}).get("user") or "").lower().split())
        if prior and not NOT_A_TRADE.search(prior):
            return _trade_for(prior)
    return ""


def _trade_for(line):
    """The reply of the first trade row whose words are in the line, or ""."""
    for names, reply in TRADES:
        if re.search(r"\b(?:" + "|".join(re.escape(name) for name in names) + r")\b", line):
            return reply
    return ""


# A tenant is not the person who may fix or pay for the fence or the hedge, so a line that names a
# landlord, a letting agent or a housing association is the tenancy question, not the DIY one:
# "my landlord wont fix the fence" was the panel method on this branch, and main's letter
# ("Put it in writing ... keep a copy") is the answer it wants.
NOT_A_FENCE_JOB = ("landlord", "landlords", "letting agent", "lettings agent", "letting agents",
                   "housing association", "housing trust", "council house", "estate agent",
                   "my tenant", "tenants")


_A_FENCE_WORD = re.compile(
    r"\b(fence|fences|fencing|closeboard|boundary|post|posts)\b", re.I)


# The things a person says when the boiler itself is the fault: "my boiler is banging", "keeps
# losing pressure", "is locking out". A boiler named without one of these is the thing they have
# already ruled out, and the radiator's own answer stands.
BOILER_IS_WRONG = re.compile(
    r"\b(?:banging|bangs|noisy|noise|loud|rumbling|rumbles|kettling|whistling|gurgling|broken|"
    r"dead|failed|faulty|fault|leaking|dripping|losing pressure|loses pressure|pressure (?:is )?"
    r"(?:low|dropping|dropped|down|below)|low pressure|dropping pressure|keeps? dropping|"
    r"locked out|locking out|lockout|cutting out|cuts out|not firing|wont fire|wont light|"
    r"not working|stopped working|error|e1|f1|f22|f28)\b")


# "Is it worth getting X" is two questions in one wording: X is a thing you buy, or X is somebody
# who comes out. A callout row keyed on the bare phrase answers a visit, so the words that say the
# buying have to stand it down. The difference is the shape and not a list of appliances: a thing
# named as the thing to buy is a purchase, and a visitor or a fault beside the phrase makes it a
# callout. "a new one" is not a purchase of something else - it points at the thing already in the
# chat, which is this row's subject - so a placeholder keeps the row.
A_THING_TO_BUY = re.compile(
    r"\bworth\s+(?:getting|buying|having|installing|fitting)\s+"
    r"(?:a|an|the|some|these|those|another)\s+(?!(?:new\s+)?(?:one|ones|it|them)\b)[a-z]", re.I)
# The same purchase said the other way round: "a heat pump worth getting".
A_THING_TO_BUY_NAMED_FIRST = re.compile(
    r"\b(?:a|an|the|my|our|your|their|his|her)\s+(?:[a-z-]+\s+){0,4}worth\s+(?:getting|buying)\b",
    re.I)
# "a new one", "another one", "one of those": the thing in hand, so the row keeps the line.
THE_THING_IN_HAND = re.compile(
    r"\b(?:a|an|the|another)\s+(?:new|second|bigger|smaller|different|better)\s+(?:one|ones)\b"
    r"|\b(?:a|an|the|another)\s+(?:one|ones)\b|\bone\s+of\s+those\b", re.I)
# Somebody who comes out, or the visit itself.
A_VISITOR = re.compile(
    r"\b(?:someone|somebody|anyone|engineer|plumber|tradesman|gas\s+safe|electrician|"
    r"callout|call\s+out|out\s+to|looked\s+at|looked\s+over|look\s+at\s+it|seen\s+to|"
    r"come\s+out|a\s+call)\b", re.I)
# What is wrong, which is what a visit is for.
A_FAULT_TO_CALL_SOMEONE_ABOUT = re.compile(
    r"\b(?:broken|broke|not\s+working|wont\s+work|won't\s+work|wont\s+fire|won't\s+fire|"
    r"fault\w*|error\s+code|leak\w*|noise|noisy|rattl\w*|pressure|reset\w*|cutt?ing\s+out|"
    r"keeps?\s+going\s+off|locks?\s+out|lockout|dead|stuck|dripping)\b", re.I)


# Work done to the thing they already own is what a callout is for: "boiler checked", "the heating
# serviced", "the radiators bled". A thing named on its own is a purchase only when nothing says
# something is being done to it.
A_WORK_DONE_TO_THE_THING = re.compile(
    r"\b(?:check\w*|test\w*|servic\w*|inspect\w*|flush\w*|maintain\w*|"
    r"cleaned|cleaning|swept|sweep|safety\s+check)\b", re.I)


def _a_visit_not_a_purchase(understood):
    """The callout row answers a visit: "is it worth getting a heat pump" is a purchase.

    `boiler-callout` keys "worth getting" because "is it worth getting someone out" is its
    question, and the bare phrase also matched "is it worth getting a heat pump" and "is a heat
    pump worth getting". Both were told to check the pressure gauge and ring a Gas Safe engineer,
    over the card that says whether a heat pump is worth it at all. A heat pump is electric and a
    heat pump drier is a drier, so there is no list of appliances that would fix this: the buying
    is the shape, and the line answers the callout row only when it names a visitor or a fault.
    """
    bits = [str((understood or {}).get(key) or "")
            for key in ("clean", "text", "raw", "rewritten", "plain")]
    text = " ".join(bits).lower()
    if not re.search(r"\bworth\b", text):
        return True
    if THE_THING_IN_HAND.search(text):
        return True
    if A_VISITOR.search(text) or A_FAULT_TO_CALL_SOMEONE_ABOUT.search(text):
        return True
    if A_WORK_DONE_TO_THE_THING.search(text):
        return True
    return not (A_THING_TO_BUY.search(text) or A_THING_TO_BUY_NAMED_FIRST.search(text))


def _the_boiler_is_not_the_fault(understood):
    """A boiler named as the thing that is fine is not a reason to drop the radiator's answer.

    #6487 put the bare word "boiler" in this row's `avoid`, which held the bleed card out of every
    line that mentioned the boiler at all. People mention it to rule it out - "my radiator is cold
    at the top, the boiler pressure is fine" - and those lines lost the answer they need and were
    told to top the pressure up through the filling loop, or got the cold-and-flu card. A boiler
    named with something wrong with it is still the boiler's answer, so the row stands down only
    then.
    """
    bits = [str((understood or {}).get(key) or "")
            for key in ("clean", "text", "raw", "rewritten", "plain")]
    words = (understood or {}).get("words") or ()
    text = " ".join(bits + [str(word) for word in words]).lower()
    if not re.search(r"\b(?:boiler|boilers|combi)\b", text):
        return True
    return not BOILER_IS_WRONG.search(text)


# "its a 3 bed with a garden" is a description of the new home, not a bed to carry up the stairs.
# The count has to be a home's size - a number and the word together, never a bare number or a
# bare "bedroom" - and the line has to be telling the bot about the place rather than asking how
# to move something into it.
HOME_SIZE = re.compile(r"\b(?:one|two|three|four|five|six|[1-6])[\s-]?(?:bed|bedroom)s?\b")
# The words people open a description of their new place with: "its a 3 bed", "we've got a two
# bed flat", "we're moving to a 3 bed house". Ordinary asks - "how do i move a 5 bed house on my
# own", "how do i get a 3 bed base upstairs" - do not open that way, so they keep the card.
HOME_SIZE_OPENER = re.compile(
    r"\b(?:its|it's|it is|thats|that's|we're|we are|were|i've|i have|we've|we have|"
    r"bought|rented|moving|moved)[^.?]{0,22}$")
# Anything being carried is this row's own question, whatever size the home is.
HOME_SIZE_CARRIED = re.compile(
    r"\b(?:bed|beds|mattress|settee|sofa|couch|wardrobe|sideboard|bookcase|bookshelf|dresser|"
    r"table|divan|frame|headboard|base|furniture|boxes)\b|"
    r"upstairs|downstairs|through the door|doorway")


# "heat my back", "warm the knee": the thing being warmed is what the line is about, and a body
# part is not a room. `heat-a-room` keeps "heat my"/"warm my" in its key because "how do i heat my
# flat" is the plainest way to ask it, so the phrase alone reached "heat my back or ice it" and
# answered it with a 1kW electric radiator for the room the person was sitting in.
_HEAT_OR_WARM_A_THING = re.compile(
    r"\b(?:heat|heating|warm|warming|warm\s+up)\s+(?:the|my|our|that|this|a|an)\s+([a-z']+)")
_A_BODY_PART_BEING_WARMED = frozenset((
    "back", "neck", "shoulder", "shoulders", "knee", "knees", "ankle", "ankles", "foot", "feet",
    "hand", "hands", "toe", "toes", "leg", "legs", "arm", "arms", "muscle", "muscles", "joint",
    "joints", "hip", "hips", "wrist", "elbow", "head", "chest", "stomach", "belly", "tummy",
    "ear", "ears", "face", "throat", "body", "skin", "sore", "bump", "bruise"))


def _a_room_being_heated(understood):
    """True unless the line heats a body part, which is the compress card's question."""
    reading = understood if isinstance(understood, dict) else {}
    line = str(reading.get("clean") or reading.get("text") or "").lower()
    return not any(thing in _A_BODY_PART_BEING_WARMED
                   for thing in _HEAT_OR_WARM_A_THING.findall(line))


def _not_a_size_of_a_home(understood):
    """A line that tells the bot the home's size is not a line about carrying a bed upstairs.

    `furniture-upstairs` keys the word "bed", and the second part of its key is the whole move -
    "we're moving house in 6 weeks" met it, so the next line, "its a 3 bed with a garden", was
    answered "Measure first: the stairwell's width ... the narrowest side of the bed" (#mtl-14).
    Standing down on the size alone is too wide, though: "a 4 bed mattress", "a 2 bed settee" and
    "how do i move a 5 bed house on my own" all want the measuring card, so the row stands down
    only when the line describes the place - an opener, then the count, and nothing being carried.
    """
    text = " " + ((understood or {}).get("clean") or "").lower() + " "
    size = HOME_SIZE.search(text)
    if size is None:
        return True
    if HOME_SIZE_CARRIED.search(text[:size.start()] + " " + text[size.end():]):
        return True
    return not HOME_SIZE_OPENER.search(text[:size.start()])


def _a_fence_is_named(understood):
    """"where do i start" is a way of asking, not a thing, so the fence row wants a fence word.

    "where do i start" and "where do i begin" sit in the build row's first key group, and a
    phrasing in the first group counts as the subject of the line. So every line that says "where
    do i start" - "my laptop has got really slow, where do i start", "i want to learn to code,
    where do i start", "the house is a mess and my in laws come tomorrow, where do i start" - was
    answered with how to set fence posts. The row now also needs a fence or garden word said
    somewhere in the line, which every real fence ask has and none of those lines do.
    """
    # "plain" is the line as the reading repaired it, so a slip stays a fence: "how do i put up a
    # fense" is not in the text or the words, but it is what `plain` carries
    bits = [str((understood or {}).get(key) or "")
            for key in ("clean", "text", "raw", "rewritten", "plain")]
    words = (understood or {}).get("words") or ()
    text = " ".join(bits + [str(word) for word in words])
    return bool(_A_FENCE_WORD.search(text))


# Taking paint OFF a thing is not painting it, and the rows below are keyed by the thing painted,
# so every one of them carries these words: "how do i remove paint from a door" was answered with
# "take the door off and paint the top and bottom edges first", and a person with old paint to get
# rid of was told how to add another coat. `paint-strip` is the row that owns these lines.
_TAKING_PAINT_OFF = ("remove", "removing", "strip", "stripping", "get off", "gets off",
                     "take off", "taking off", "sand off", "sanding off", "peel", "peeling",
                     "flaking", "flaky")


_WASHER_NEW = ("new", "brand new", "worth buying new", "buy new", "budget", "how much is a new")


def _washer_price(memory, reading):
    """What a washer costs, led by the kind the line asks about.

    The answer opened on private-sale prices, so "how much is a new washing machine" was told that
    one costs 80 to 150 pounds, which is the second-hand price. The facts are the same three
    tiers; which one is said first is the whole of the fix.
    """
    clean = (reading or {}).get("clean") or ""
    if any(word in clean for word in _WASHER_NEW) and not any(
            word in clean for word in ("second hand", "second-hand", "used", "refurbished",
                                       "reconditioned", "nearly new", "cheapest way")):
        return ("A new basic washing machine is about 300 to 400 pounds, and 450 to 600 buys a "
                "quieter one with a bigger drum and a longer guarantee. Refurbished from a dealer "
                "with a six-month guarantee is 180 to 250, and a private sale is 80 to 150 with no "
                "guarantee at all. Measure the gap and the door before you order, and check the "
                "warranty length: two years is worth having on a machine that will last eight.")
    return ("Private sale, 80 to 150 pounds; refurbished from a dealer with a six-month guarantee, "
            "180 to 250; a new basic one about 300 to 400. See it run a spin before you pay, "
            "listen for a rumble from the bearings, check the door seal for black mould and the "
            "drum for rust, and ask why it is going. Add 20 to 40 pounds for delivery and "
            "plumbing, and run a hot wash with soda crystals before your first load.")

# --- a radiator that will not heat -----------------------------------------------------
# Two faults look like one from the line and want different first moves: a single radiator that
# stays cold while the rest are hot is its own valve or its balancing, and a house where every
# radiator is cold is the boiler or the pump. Main answered the first with "Thanks for telling me -
# I'm here if you want to dig into any of that" and the second with the energy-saving card, because
# the only radiator rows are keyed on the cold radiator naming itself ("my radiator is cold") and
# the denial reader throws away a key built on the state word ("is not getting hot" rules out hot).
# So the key is the fault phrase, which carries its own "not" and is passed by the denial check.
RADIATOR_WHOLE_HOUSE = ("all the radiators", "all radiators", "every radiator", "every rad",
                        "whole house", "whole flat", "nowhere", "no radiator", "none of the",
                        "central heating", "the heating", "my heating", "our heating",
                        "heating is on", "heating on but")
# The words that make it one radiator rather than the house: they are checked first, because a
# line can name both ("my heating is on but one radiator is cold") and it is the one that is cold.
RADIATOR_ONE = ("one radiator", "one rad", "a single radiator", "single radiator",
                "one of the radiators", "one of the rads", "the radiator in", "radiator in the",
                "just one", "only one")
RADIATOR_ALREADY_BLED = ("bled", "bleed", "bleeding", "radiator key", "i have bled")
# A floor of the house rather than the whole of it: cold upstairs is balance, air or a zone valve,
# and the boiler pressure answer is wrong for it, since the boiler is plainly working downstairs.
RADIATOR_UP = ("upstairs", "landing", "first", "second", "top")
RADIATOR_DOWN = ("downstairs", "ground")
# What a floor is said to be: "cold upstairs" and "warm downstairs" say the same thing about the
# same floor, and the answer is the same one, so both readings are counted.
RADIATOR_COLD = ("cold", "coldest", "cool", "cooler", "lukewarm", "freezing", "stone")
RADIATOR_WARM = ("warm", "warmest", "hot", "hotter", "fine", "working", "ok", "roasting")
# A radiator that is too hot is the other fault. The row below keys on *where* the radiator is
# ("radiator in my", "radiator in the"), because "the radiator in my bedroom is cold" puts the
# cold somewhere other than next to the word radiator, and that key says nothing about what is
# wrong: a bedroom radiator left on full reached the card for a radiator that never heats, and the
# person was told their valve was stuck when all they wanted was the room cooler.
RADIATOR_TOO_HOT = ("too hot", "very hot", "roasting", "scorching", "overheating",
                    "overheated", "boiling", "piping hot", "red hot", "blasting",
                    "on full", "full blast", "full on", "max", "maximum", "on high",
                    "as high as", "cant sleep", "cannot sleep", "too warm", "too much heat",
                    "blistering", "burning up")
# The words that make the line the cold radiator's after all: the head is stuck shut *and* the
# radiator is stone cold, which is this row's question however hot the person wishes it were.
RADIATOR_SAYS_COLD = RADIATOR_COLD + ("not hot", "not warming", "not warm", "never heats",
                                      "never heated", "wont heat", "wont warm", "no heat")


def _radiator_floor(said):
    """Which floor is the cold one: "up", "down", "both" or None.

    "my radiators are cold upstairs" and "my radiators are cold but downstairs is warm" are the
    same fault, and a plain keyword check reads the second one backwards, since "downstairs" is
    the word it finds first. So each floor is read by the state word nearest to it.
    """
    words = said.replace(",", " ").replace(".", " ").split()
    if not words:
        return None

    def nearest(index, marks):
        """The distance to the nearest state word, counting only the words after the floor when
        there are any: "downstairs is warm" is about the floor before it, and a tie on distance
        ("cold but downstairs is warm") has to go the same way."""
        after = [(i - index, 0) for i, word in enumerate(words) if word in marks and i > index]
        if after:
            return min(after)
        before = [(index - i, 1) for i, word in enumerate(words) if word in marks and i < index]
        return min(before) if before else None

    cold_up = cold_down = 0
    for i, word in enumerate(words):
        if word not in RADIATOR_UP and word not in RADIATOR_DOWN:
            continue
        cold, warm = nearest(i, RADIATOR_COLD), nearest(i, RADIATOR_WARM)
        if cold is None and warm is None:
            continue
        is_cold = cold is not None and (warm is None or cold < warm)
        is_warm = warm is not None and (cold is None or warm < cold)
        if word in RADIATOR_UP:
            cold_up += 1 if is_cold else 0
            cold_down += 1 if is_warm else 0
        else:
            cold_down += 1 if is_cold else 0
            cold_up += 1 if is_warm else 0
    if cold_up and cold_down:
        return "both"
    if cold_up:
        return "up"
    if cold_down:
        return "down"
    return None


def _radiator_not_hot(memory, understood):
    """The one cold radiator, the radiator already bled, or the whole house.

    The plural is the tell for the house: "my radiators wont heat up" is not one radiator with a
    stuck valve, it is the boiler or the pump, and that is the card `no-heating` already gives.
    A line can name both ("my heating is on but one radiator is cold"), so the one radiator wins.

    The row keys on where the radiator is rather than on what is wrong with it, so a radiator that
    is stuck open, or turned up too far, reads as this row's line. A line that says the radiator is
    too hot and never says it is cold is the valve's own question, and the row below answers it.
    "cannot sleep" counts as too hot here because that is the line people bring, and a cold
    radiator is already covered by RADIATOR_SAYS_COLD.
    """
    said = str(understood.get("clean") or " ".join(understood.get("words") or [])).lower()
    too_hot = any(_says(said, phrase) or phrase in said for phrase in RADIATOR_TOO_HOT)
    if too_hot and not any(word in said for word in RADIATOR_SAYS_COLD):
        return None
    one = any(_says(said, phrase) or phrase in said for phrase in RADIATOR_ONE)
    bled = any(_says(said, word) or word in said for word in RADIATOR_ALREADY_BLED)
    floor = _radiator_floor(said)
    if floor and one is False and bled is False:
        # a line that says both floors are cold is the whole house, and the boiler is the answer
        if floor != "both":
            if floor == "down":
                return ("Warm upstairs and cold downstairs is the bottom of the system not getting "
                        "its water: the pump speed, a zone valve stuck shut or a downstairs circuit "
                        "that was never balanced, and the first two are an engineer's job. Check the "
                        "room thermostat downstairs is calling for heat and that the downstairs "
                        "radiators have their valves open before you ring anyone.")
            return ("Cold upstairs and warm downstairs is the top of the system not getting its "
                    "share: bleed the upstairs radiators first, because air rises and collects at "
                    "the highest point, then balance them - open the lockshield at the far end of "
                    "the coldest one a quarter turn and turn the downstairs ones down a little, "
                    "since water takes the easiest path. A stuck thermostatic valve on one of them "
                    "is the other common cause, so check the pins too.")
    house = one is False and (bled is False and (
        any(_says(said, phrase) or phrase in said for phrase in RADIATOR_WHOLE_HOUSE)
        or any(_says(said, word) for word in ("radiators", "rads"))))
    if house:
        return ("If every radiator is cold it is the boiler or the pump, not a radiator: check the "
                "pressure gauge reads 1 to 1.5 bar cold and top it up at the filling loop, make sure "
                "the room thermostat and the programmer are calling for heat, and press reset once. "
                "A pump that runs but moves no heat is an engineer's job.")
    if bled:
        return ("If it stays cold after bleeding, air was not the problem: the thermostatic valve is "
                "stuck shut, the bottom of the radiator is sludged up, or the system needs balancing. "
                "Take the valve head off and press the pin under it - a pin that will not spring back "
                "is stuck - then open both valves and turn the other radiators down so the water is "
                "pushed its way.")
    return ("One radiator cold while the others are hot is usually its own valve, not the boiler: "
            "take the thermostatic head off and press the little pin underneath - a pin that does not "
            "spring back is stuck, and a few taps with a screwdriver handle usually free it. If the pin "
            "moves, the valve at the other end is closed or the system needs balancing.")

# Furniture up a stairwell is a measuring and lifting question, and the answer that saves the
# wall (and a back) is the tape measure, not muscle. The reply was written around a wardrobe, so
# "how do i get a sofa up the stairs" was told to take the wardrobe's doors and drawers off. Each
# of these comes apart differently, and naming the thing is the useful half of the answer.
UPSTAIRS_ITEMS = (
    # (words people write, what to call it, what comes off first)
    (("mattress",), "mattress",
     "A mattress never folds down the middle, so it goes on its edge: bend it more than about "
     "thirty degrees and the springs and the foam take a set and it never lies flat again"),
    (("sofa", "couch", "settee", "armchair", "suite"), "sofa",
     "The legs come off, the cushions come off, and a two-piece sofa splits at the back, which is "
     "usually enough on its own"),
    (("table", "desk"), "table",
     "The legs come off and the top goes up on its edge, which turns a wide thing into a tall one"),
    (("bed frame", "bedframe", "divan", "bed"), "bed",
     "A bed frame comes apart into sides and ends, and a divan splits into two halves"),
    (("wardrobe", "chest of drawers", "sideboard", "bookcase", "bookshelf", "shelving", "dresser",
      "cabinet", "furniture"), "furniture",
     "Doors and drawers come out and the back panel comes off, because the carcass is a good deal "
     "narrower than anything with the doors on"),
)


def _furniture_upstairs(memory, understood):
    """Name the thing being moved and its own first move, then the measuring advice."""
    text = " " + ((understood or {}).get("clean") or "").lower() + " "
    kind = "furniture"
    first = UPSTAIRS_ITEMS[-1][2]
    for words, name, move in UPSTAIRS_ITEMS:
        said = [word for word in words if " " + word in text]
        if said:
            # the person's own word for it reads better than a category: "the narrowest side of
            # the bookcase" rather than "of the furniture"
            kind, first = max(said, key=len), move
            break
    return ("Measure first: the stairwell's width and the tightest height under the turn, then "
            "the narrowest side of the " + kind + ". " + first + ". Two people and a strap, not "
            "one: a man with a van is 40 to 80 pounds and cheaper than a surgeon. If the numbers "
            "say no, a two-piece or flat-pack version that comes up in boxes is the honest "
            "answer.")


def _not_a_cook_ask(understood):
    """False when the line asks what to cook with a food it names, so this row stands down."""
    return not cook_ask(understood)

# The repair letter, worded once: every tenancy row that answers "the landlord will not deal
# with this" gives the same letter, so a change to it happens in one place.
LANDLORD_REPAIR_LETTER = the_fault(
    "Put it in writing, a text or email is fine, and keep a copy: \"Hi - I reported the "
    "{fault} on [date] and nothing has been done. Please arrange a repair within 14 "
    "days. Thanks, [name].\" Landlords have to do most repairs in a reasonable time, "
    "and anything that came with the flat counts, appliances included, while something "
    "you brought with you is yours to fix. If they "
    "ignore you, your council's environmental health team or Shelter can push it along.",
    "Put it in writing, a text or email is fine, and keep a copy. Name what is wrong "
    "and when it started, say what you want done and ask for a date, then keep the "
    "messages: landlords have to do most repairs in a reasonable time, and anything that "
    "came with the flat, appliances included, counts, while something you brought with "
    "you is yours to fix. If they ignore you, your council's "
    "environmental health team or Shelter can push it along.")

# The fittings the DIY rows and the body claim are the landlord's to deal with, so a line that
# names a tenant and one of these is the repair question, not the hardware shop. Measured on
# main: "my landlord wont fix the shower" got the shower tray, "... the tap" the washer, "... the
# window" the window frame, "landlord wont fix the front door lock" the lock barrel, "... the
# cupboard" a hinge, and "my landlord wont fix the toilet" the constipation answer.
LANDLORD_JOB_FITTINGS = (
    "shower", "showers", "tap", "taps", "faucet", "mixer", "bath", "baths", "sink", "sinks",
    "basin", "loo", "toilet", "toilets", "cistern", "bog", "window", "windows", "sash",
    "casement", "door", "doors", "door lock", "lock", "locks", "cupboard", "cupboards",
    "cabinet", "cabinets", "wardrobe", "drain", "drains", "gutter", "gutters", "guttering",
    "extractor", "extractor fan", "tiles", "floorboards", "skirting", "fireplace")

def _paint_brush_care(memory, understood):
    """Keeping a brush usable: between coats, overnight, or after it has gone hard.

    One card, because it is one tool and one rule - the paint must not dry in the bristles - and
    the line picks which sentence leads. A brush that has already gone hard is the only case that
    wants the rescue first.
    """
    read = understood if isinstance(understood, dict) else {}
    line = " " + str(read.get("clean") or read.get("text") or "").lower() + " "
    oil = any(word in line for word in (" gloss", " oil based", " oil-based", " white spirit",
                                       " varnish", " oil paint", " turps"))
    if any(word in line for word in (" gone hard", " went hard", " hard", " stiff", " dried out",
                                     " dry out", " save", " saved", " rescue")):
        if any(word in line for word in (" roller", " sleeve", " sleeves")):
            return ("A sleeve that has gone hard is not worth rescuing: the paint has set through "
                    "the pile and no amount of white spirit brings the nap back, so bin it and buy "
                    "another - they are two or three pounds. What saves you the next one is not "
                    "leaving it to dry: wrap it in cling film between coats, and wash it out the "
                    "moment you finish.")
        return ("Soak it before you bin it: water-based paint softens in an hour or two in hot "
                "water with a good squeeze of washing-up liquid, worked through the bristles with "
                "your fingers and a comb, and gloss wants white spirit or a brush restorer first "
                "and the soapy wash after. Once it is soft, comb it straight and dry it bristles "
                "down - and if the bristles have set bent, it will paint bent, so keep it for "
                "priming and undercoat.")
    if any(word in line for word in (" losing bristles", " lose bristles", " loses bristles",
                                     " lost bristles", " sheds", " shedding",
                                     " bristles are falling", " bristles falling",
                                     " bristles falling out", " bristles coming out",
                                     " loose bristles", " moulting",
                                     # "my brush keeps falling apart" is the same fault: the
                                     # head is not held any more, so the bristles come away.
                                     " falling apart", " falls apart", " come apart",
                                     " comes apart", " coming apart")):
        return ("Bristles that come out in the paint are usually a cheap brush rather than a "
                "fault you can fix: the ferrule is crimped onto a bundle that was never glued "
                "properly, and no amount of washing holds it. Comb it out dry before you start, "
                "keep that brush for undercoat and primer where a stray bristle does not show, "
                "and buy a decent one for the topcoat - a bristle left in gloss shows for years.")
    # a roller sleeve has no ferrule and no bristles, and "how do i clean a paint roller" was
    # answered with the brush sentence word for word. The sleeve is the key, so the sentence is
    # about a sleeve: wash or spin it out, stand it on end, and do not leave it in the tray.
    roller = any(word in line for word in (" roller", " sleeve", " sleeves"))
    brush = "brush" in line or "bristle" in line
    if roller and not brush:
        if any(word in line for word in (" between coats", " overnight", " over night",
                                        " store", " storing", " keep", " keeping", " tonight",
                                        " tomorrow", " next day", " wrap", " wrapped",
                                        " cling film", " clingfilm", " carrier bag",
                                        " plastic bag", " lunchtime", " short break")) \
                and not any(word in line for word in (" clean", " wash", " rinse")):
            return ("Wrap the sleeve, do not wash it: cling film or a carrier bag pressed round "
                    "the pile with the air out keeps it soft between coats, and the same goes "
                    "overnight with the roller in the fridge rather than the freezer. Standing "
                    "it in the tray with a little paint on it works for an hour or so. A "
                    "sleeve that is left to dry out is a sleeve you throw away.")
        if oil:
            return ("A sleeve that has had gloss on it wants white spirit worked through it, then "
                    "a wash in warm soapy water: oil paint skins over in a sleeve the same way it "
                    "does in a brush, and a skinned sleeve sheds fibres on the next wall. Spin it "
                    "out, stand it on end to drain, and let it dry standing up so the pile does "
                    "not flatten. A sleeve that has gone hard is not worth saving - they are two "
                    "or three pounds.")
        return ("Wash a roller sleeve under warm water with a little washing-up liquid, working it "
                "with your fingers until the water runs clear, then spin it out - a roller on its "
                "frame spun in a bucket or against the side of the sink - and stand it on end to "
                "drain so the pile does not flatten. For a short stop, wrap the sleeve in cling "
                "film or stand it in the tray with a little paint on it, and never leave it "
                "soaking in water: the glue that holds the pile lets go.")
    # "how do i get oil paint off a brush" is the wash question with none of those words in it,
    # and it was answered with the cling-film trick for keeping a brush soft between coats - an
    # answer to a different question.
    if any(word in line for word in (" clean", " wash", " rinse", " after ", " finished",
                                     " done with", " out of", " get out", " got out",
                                     " remove", " removing",
                                     " off a brush", " off my brush", " off the brush",
                                     " off a paintbrush", " off my paintbrush",
                                     " out of a brush", " out of my brush",
                                     " out of a paintbrush", " out of my paintbrush",
                                     " out of the bristles",
                                     " off a roller", " out of a roller", " out of the sleeve",
                                     " get it off", " get the paint off")):
        if oil:
            return ("Gloss and oil-based paint come out with white spirit, not water: work it "
                    "through the bristles, wipe them on a rag, then wash the brush in warm soapy "
                    "water and comb it straight. Dry it bristles down so water does not sit in "
                    "the ferrule, and never leave it standing on its bristles in a jar.")
        return ("Warm water and washing-up liquid, worked right down to the ferrule until the "
                "water runs clear, then comb the bristles straight and dry the brush bristles "
                "down - never standing on them in a jar, which sets them splayed. Emulsion comes "
                "out easily while it is wet and hardly at all once it has dried.")
    if any(word in line for word in (" overnight", " over night", " tomorrow", " next day",
                                     " fridge", " until the morning")):
        return ("Wrap it and put it in the fridge: cling film or a carrier bag pressed round the "
                "bristles with the air out keeps a brush soft overnight, and a day or two at a "
                "push, as long as the bag is sealed so the solvent cannot dry out. Take it out an "
                "hour before you paint again, and never put a brush in the freezer - the cold "
                "cracks the paint in the bristles.")
    return ("Wrap it in cling film or a carrier bag with the air squeezed out, or in a damp cloth, "
            "and it will still be soft at the end of the day: that is the whole trick between "
            "coats, and a brush left out on the tin dries in about an hour. For an overnight stop, "
            "wrap it and put it in the fridge rather than the freezer, and for a roller, wrap the "
            "sleeve the same way or stand it in the tray with a little paint on it.")


WASHING_MACHINE_FILTER = (
    "It is behind the little hatch or kick plate at the bottom front: towel, shallow bowl, "
    "then unscrew the cap slowly and pull out the coins, hair and the odd sock. Do it every "
    "two or three months, and check the drain hose behind the machine is not kinked while "
    "you are down there. If the machine has stopped emptying, that same cap is the drain "
    "pump: the impeller behind it is what a coin or a hair grip jams, so clear it before you "
    "call anyone.")

# A machine's filter is asked about twice: named in the line ("how do i clean the washing
# machine filter"), and then again with only the part named ("i cleaned the filter"). The second
# line has no machine in it, so no machine's filter row could reach it and `vacuum-filter` answered
# in their place. The three rows below gain "filter" as a word so they are in play on the
# follow-up, and `the_filter_of` says which machine the filter belongs to: the one in the line, or
# the one the last turns are about. Anything else stands down, so "my hoover filter is blocked" and
# a bare "how often should i clean the filter" still reach the vacuum's card.
TUMBLE_DRYER_FILTER = (
    "Pull the fluff off the lint filter after every load, and wash the filter under the tap "
    "once a month with a little washing-up liquid, drying it fully before it goes back in. "
    "A clogged filter is why a load takes two goes, and it is a fire risk, so never run a "
    "dryer with it out of place.")

EXTRACTOR_GREASE_FILTER = (
    "Clean the grease filters first: the metal ones go in the dishwasher, or in a hot soapy "
    "sink once a month, and a clogged filter is what makes a hood both noisy and weak. A "
    "rattle is usually a filter that is not seated or the flap on the outside wall vent "
    "banging; noise on the boost setting is normal, and a grind means the motor is on its way "
    "out.")

FILTER_TURNS = 3


def the_filter_of(words, text):
    """An Entry reply for a machine's filter row that also answers a bare "filter"."""
    patterns = [re.compile(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])")
                for word in words]

    def reply(memory, reading):
        line = str((reading or {}).get("text") or (reading or {}).get("clean") or "").lower()
        if any(pattern.search(line) for pattern in patterns):
            return text
        try:
            from ..memory import topics as _topics
            heard = " ".join(_topics.context(memory, FILTER_TURNS)).lower()
        except Exception:
            heard = ""
        if any(pattern.search(heard) for pattern in patterns):
            return text
        return ""

    return reply


# A ceiling question is two questions. "what colour should i paint the ceiling" is a colour, and
# "how do i paint a ceiling" is the painting method, which this file already answers for every
# surface. Only a line that names a colour - or asks "which" - is the colour row's.
_CEILING_COLOUR_WORDS = ("colour", "color", "colours", "colors", "white", "which", "shade",
                         "tint", "paint it", "paint the ceiling white", "paint my ceiling white")
_CEILING_HOW_TO = ("how do i paint", "how to paint", "how do you paint", "what order",
                   "which first", "do i paint the ceiling first", "roller", "brush", "coats",
                   "undercoat", "primer", "prepare", "prep")


def _asks_the_ceiling_colour(understood):
    """True for a ceiling question that is about the colour, not about how to paint it."""
    line = " " + str((understood or {}).get("clean") or "").lower() + " "
    if any(how in line for how in _CEILING_HOW_TO):
        return False
    return any(" %s " % word in line or (" %s" % word) in line
               for word in _CEILING_COLOUR_WORDS)



def _the_paper_is_in_the_line(understood):
    """True when the line names the paper this job hangs, and not just the hanging.

    "hang" and "put up" are the verbs of half the wall jobs there are - a picture, a mirror, a
    shelf, a telly, a curtain rail - so those are held off by the list below. Laundry was the
    one this row had no answer for: after a washing question, "i hang it in the spare room" read
    "hang" and "room" as two parts of this job and was told how to size a wall and paste a drop.
    The paper is what makes the verb this row's, so the paper is what has to be said.
    """
    line = str(understood.get("text") or understood.get("clean") or "").lower()
    return any(word in line for word in ("wallpaper", "wall paper", "lining paper", "paper",
                                         "paste"))
# The sounds a machine makes, kept beside the rows that answer them.
#
# A sound named in the line is a fault's question, whatever else the line says: "my boiler
# whistles when the hot water runs" holds "boiler", "hot water" and "runs", which are the words
# the fuel comparison keys, so it was answered with the price of gas. The rows that answer a
# cost, a setting or a temperature are right about the appliance and wrong about the ask, and
# this list is how they tell the difference - a named sound stands them down.
#
# The whole word, never a stem: "hum" is inside "thumps" and inside "humidity", and a bang and a
# damp patch were both answered with the vibration card for it.
A_SOUND_NAMED = (
    "hum", "hums", "humming", "hummed", "buzz", "buzzes", "buzzing", "buzzed",
    "drone", "drones", "droning", "vibrate", "vibrates", "vibrating", "vibrated",
    "whistle", "whistles", "whistling", "whistled", "whine", "whines", "whining", "whined",
    "squeal", "squeals", "squealing", "squealed", "squeak", "squeaks", "squeaking", "squeaked",
    "screech", "screeches", "screeching", "screeched", "shriek", "shrieks", "shrieking",
    "hiss", "hisses", "hissing", "gurgle", "gurgles", "gurgling", "glug", "glugs", "glugging",
    "bang", "bangs", "banging", "banged", "knock", "knocks", "knocking", "knocked",
    "rumble", "rumbles", "rumbling", "rumbled", "clunk", "clunks", "clunking", "clanked",
    "clank", "clanks", "clanking", "rattle", "rattles", "rattling", "rattled",
    "tick", "ticks", "ticking", "ticked", "tap", "taps", "tapping", "tapped",
    "click", "clicks", "clicking", "clicked", "thump", "thumps", "thumping", "thumped",
    "roar", "roars", "roaring", "grind", "grinds", "grinding", "ground",
    "scrape", "scrapes", "scraping", "scraped")

# The forms a whole-word match on `understood["words"]` can miss: a typo, or a sound said with an
# ending the reader dropped. Long enough not to sit inside another word.
_A_SOUND_STEM = ("humming", "hummed", "buzzing", "buzzed", "vibrating", "droning", "hissing",
                 "rattling", "knocking", "banging", "grinding", "ticking", "clicking",
                 "whistling", "whistled", "squeaking", "squealed", "squealing", "screeching",
                 "thumping", "clanking", "clunking", "rumbling")


def a_sound_is_named(understood):
    """True when the line names the sound a thing is making, not what it costs or how it is set."""
    read = understood if isinstance(understood, dict) else {}
    words = set(str(word).lower() for word in (read.get("words") or []))
    if words & set(A_SOUND_NAMED):
        return True
    said = " ".join(str(read.get("clean") or read.get("text") or "").lower().split())
    return any(stem in said for stem in _A_SOUND_STEM)


def not_a_sound(understood):
    """The guard for a row about a cost, a setting or a temperature: a named sound stands it down."""
    return not a_sound_is_named(understood)


def _boiler_noise(memory, understood):
    """A noise in a boiler, with the cause that noise actually has.

    One card answered a whine, a hum, a whistle and a bang with the banging answer, and each of
    the four has its own first move: air, vibration, a restriction, expansion.
    """
    line = " ".join(str((understood or {}).get("plain")
                        or (understood or {}).get("text")
                        or (understood or {}).get("clean") or "").lower().split())
    words = set(str(word).lower() for word in ((understood or {}).get("words") or []))
    said = lambda *names: any(name in line for name in names)  # noqa: E731
    # A hum is the word, not the letters: "thumps" and "humidity" both hold "hum", and a bang
    # and a damp patch were both answered with the vibration card.
    if said("humming", "hummed", "buzzing", "buzzed", "vibrating", "droning") \
            or words & {"hum", "hums", "humming", "hummed", "buzz", "buzzes", "buzzing",
                        "buzzed", "vibrate", "vibrates", "vibrating", "vibrated", "drone",
                        "drones", "droning"}:
        return ("A steady hum is vibration rather than anything burning: the casing or a pipe "
                "touching a wall or a floorboard, the pump left on its highest speed, or a fan "
                "bearing on the way out. Press a hand on the pipes and the casing while it runs to "
                "feel which one is ringing, put a cloth or a bit of foam where metal touches "
                "plaster, and turn the pump down a speed if it has a dial. A hum that changes pitch "
                "with the firing, or comes with a hot smell or a fault code, is the fan or the "
                "pump itself and wants an engineer.")
    if said("whistl", "whine", "whining", "squeal", "squeak", "screech", "hiss", "shriek") \
            or words & {"squeak", "squeaks", "squeaking", "squeaked", "screech", "screeches",
                        "screeching", "screeched", "squeal", "squeals", "squealing",
                        "squealed"}:
        return ("A whistle, a whine or a hiss is a restriction or air rather than the flame: a "
                "radiator valve left nearly shut, the boiler's own isolation valve not fully open, "
                "low pressure, or scale on the heat exchanger. Check the gauge is between 1 and 1.5 "
                "bar cold, open every radiator valve fully, and if the noise only comes with hot "
                "water it is usually the diverter valve, which is an engineer's job. Do not run it "
                "with the pressure below 1 bar.")
    if said("gurgl", "gurgling", "glug"):
        return ("Gurgling is air: bleed every radiator from the top, with the heating off until the "
                "water runs steady, then check the pressure is 1 to 1.5 bar and top it up if it has "
                "dropped. If it gurgles again within a week, air is getting in somewhere and that "
                "is an engineer's visit rather than a bleeding.")
    if said("tap", "tapping", "tick", "ticking", "click"):
        return ("A tick or a tap is usually pipes expanding as they heat, and it is harmless: slide "
                "a bit of felt or plastic where the pipe passes through a joist or a wall, and "
                "leave the heating on a steady setting rather than switching it on and off. A "
                "ticking that turns into a knock when the pump starts is air, so bleed the "
                "radiators as well.")
    # A grind is not a bang, and it is not a shrug: metal on metal is stop and get an engineer.
    if said("grind", "grinding", "scraping") \
            or words & {"grind", "grinds", "grinding", "ground", "scrape", "scrapes",
                        "scraping", "scraped"}:
        return ("Grinding means stop running it and get an engineer: on a boiler it is the pump or a "
                "seized fan rather than air, and a pump that has gone on grinding has often taken "
                "the shaft with it. Turn it off at the programmer, leave the heating off, and say "
                "what it sounds like and how long ago it started - a grind that stops when the "
                "boiler does is the pump, and one that carries on is the fan.")
    return ("Banging or rumbling when the heating starts is usually air or a pump set too fast: bleed "
            "the radiators, check the pressure is 1 to 1.5 bar, and if it carries on get a heating "
            "engineer to look at the pump. A knocking that comes at the end of a burn is limescale "
            "on the heat exchanger, and a knock with a hot smell or a fault code is one to switch "
            "off and report.")


def _heating_goes_cold(memory, understood):
    """The answer to a heating or a hot water that keeps going cold, by which one was named."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(word in said for word in ("hot water", "hot tap", "tap", "bath", "shower",
                                     "cylinder", "immersion", "boiler")):
        return ("Hot water that runs cold after a few minutes is nearly always the flow rate: a "
                "combi heats only the water you draw, so a hot tap opened full, or two taps at "
                "once, outruns it - run it slower and see whether it holds. A tank with an "
                "immersion is the other case: the hot runs out when the cylinder empties, so a "
                "longer draw needs the immersion on for longer or the cylinder thermostat turned "
                "up. If it goes cold at random, check the boiler pressure is between 1 and 1.5 "
                "bar.")
    return ("A heating that comes on and then goes cold is usually the room thermostat reaching "
            "its set temperature and shutting the boiler off, which is it working, not a fault - "
            "turn the thermostat up a degree and see whether the radiators stay hot. If it goes "
            "off long before the room is warm, check the boiler pressure is between 1 and 1.5 bar, "
            "that the programmer or timer is not cutting out early, and whether the thermostat "
            "sits somewhere warm like a hallway by a radiator, which makes it read the wrong room.")


def _a_safety_ask(understood):
    """A boiler, or a line that asks whether something is safe.

    "can i leave the heating on all night" is the cost question and stays with the heating row;
    "is it safe to leave the heating on all night" is about the flame, and comes here.
    """
    text = " " + str(understood.get("clean") or understood.get("norm_text") or "").lower() + " "
    if re.search(r"\b(boiler|combi|back boiler|gas fire|gas boiler|flue)\b", text):
        return True
    return bool(re.search(r"\b(safe|safely|unsafe|dangerous|danger|risk|alright to leave"
                          r"|ok to leave|okay to leave)\b", text))


# The rows of this list live in home_craft.py: this file went over the publisher's 1 MiB file
# limit, and the list of data is the cheapest thing to move. Nothing else changed - the rows are
# put back in front of the ones appended below, at the end of this file, so ENTRIES is the same
# rows in the same order.
# "which is better a heat pump or a new boiler" names both sides, and the boiler's own rows have
# nothing to compare: the boiler-lifespan card was the answer, which tells you when a boiler wears
# out and never mentions the heat pump. A line that names both is the choice between them, and it
# gets a pick with the two prices in it; the mechanics answer stays for every line that names the
# heat pump alone.
_A_BOILER_TOO = re.compile(
    r"\b(?:boiler|boilers|combi|gas boiler|back boiler|central heating system)\b", re.I)
# The choice between them is said with a comparison: "or a new boiler", "heat pump vs boiler",
# "instead of a boiler". A line that only mentions the heating ("my central heating pump is
# noisy") is a fault question, and the pick would be an answer to something nobody asked, so
# "central heating" and the radiator are not a side of the choice on their own.
_WEIGHING_THE_TWO = re.compile(
    r"\b(?:or|vs|versus|compared|compare|instead of|rather than|better than|which is better|"
    r"worth swapping|swap|replace(?:ing)? (?:it|my \w+) with|which one(?: should i| would you| do i)?)"
    r"\b", re.I)
_HEAT_PUMP_OR_BOILER = (
    "A heat pump, if the house is insulated and the radiators can be upsized: it is roughly "
    "\u00a310,000 to \u00a314,000 fitted before any grant, and one unit of electricity gives about "
    "three of heat, so it is the cheaper way to heat a well-insulated home. A new combi boiler is "
    "\u00a32,000 to \u00a33,000 fitted and the simpler answer for a draughty house with small "
    "radiators, where a heat pump would need every one of them replaced.")
_HEAT_PUMP_MECHANICS = (
    "A heat pump moves heat rather than making it, like a fridge in reverse: a refrigerant "
    "picks up warmth from outside air even on a cold day, a compressor squeezes it to a "
    "higher temperature, and that heat goes into your radiators or underfloor. One unit of "
    "electricity gives you roughly three of heat, so it is cheapest to run with big "
    "radiators, underfloor heating and good insulation, and dearer in a draughty house with "
    "small radiators. Worth it if your radiators can be upsized and your home is insulated; "
    "ask for a heat loss survey and a quote before deciding.")


def _heat_pump_answer(memory, reading):
    """The heat pump's own answer, or the pick when the line weighs it against a boiler."""
    reading = reading if isinstance(reading, dict) else {}
    said = " ".join(str(one) for one in (reading.get("words") or ()))
    if not said:
        said = str(reading.get("clean") or reading.get("text") or "")
    if _A_BOILER_TOO.search(said) and _WEIGHING_THE_TWO.search(said):
        return _HEAT_PUMP_OR_BOILER
    return _HEAT_PUMP_MECHANICS



# "the sewer in my garden is blocked" is a drain inside your own boundary, and it is yours: the
# row below keys "sewer" plus "garden", so it sent that line to the water company's sewer line,
# where the cover-and-gully answer under `outside-drain` was right. A line that says blocked and
# names nothing public - no street, road, pavement, manhole or drain cover - keeps the covers.
_OWN_BOUNDARY = re.compile(r"\b(?:garden|yard|driveway|patio|allotment|boundary)\b")
_PUBLIC_WAY = re.compile(r"\b(?:street|roads?|roadside|pavement|kerb|manhole|man hole|"
                         r"drain cover|gully|public|highway|verge|alley|back lane)\b")
_BLOCKED_DRAIN = re.compile(r"\b(?:blocked|blockage|blocking|unblock|unblocking|"
                            r"draining away|backs? up|backed up)\b")


def _a_blocked_drain_of_your_own(understood):
    """True when the line is a blocked drain on the person's own side of the boundary."""
    said = " ".join(str((understood or {}).get("clean") or "").lower().split())
    return bool(_BLOCKED_DRAIN.search(said) and _OWN_BOUNDARY.search(said)
                and not _PUBLIC_WAY.search(said))


# A tree, a fence or a roof that came down is storm damage, and the question behind it is who pays
# before it is how to mend it: "a tree fell on my car", "the fence blew down in the storm" and "the
# storm took half the roof off" all want the insurer's phone call first. Two different words are
# needed, one for something coming down and one for the thing it happened to, because "how do i
# protect my shed from storms" names the shed and nothing came down. The person under it is the
# safety card's line, not this one, and a leak is the leak rows', so nothing here reads a bare
# "leaking" or "broken".
_CAME_DOWN = re.compile(
    r"\b(?:fell\s+in|fallen\s+in|falling\s+in|fell|fallen|falling|blew|blown|blew\s+over|"
    r"came\s+down|come\s+down|collapsed|"
    r"caved\s+in|knocked\s+down|knocked\s+over|uprooted|up\s?rooted|brought\s+down|"
    r"ripped\s+off|took\s+off|torn\s+off|snapped|damaged|damage|took\s+half|"
    r"struck\s+by\s+lightning|hit\s+by\s+lightning)\b", re.I)
_CAME_DOWN_ON = re.compile(
    r"\b(?:roofs?|tiles?|slates?|chimney|ceilings?|guttering|gutters?|fences?|fencing|sheds?|garages?|"
    r"carport|conservatory|greenhouse|windows?|cars?|van|drive|driveway|garden|house|"
    r"property|outbuilding|outbuildings|wall|walls|storm|storms|gale|gales|wind|lightning|"
    r"insurance|insurer|claim|claims|policy)\b", re.I)


# A thing that came down *onto* something is a claim, and one that came *off* is a fixing: "the
# mirror in the bathroom fell off the wall" is a screw and a hook, not a storm, and the wall is
# the word that would otherwise take it. So the line needs either weather in it or a preposition
# that says where the thing landed.
_STORM_LANDED = re.compile(r"\b(?:on|onto|over|down|into)\b", re.I)
# ...and a thing *taken* off is still storm damage: "the storm blew my shed roof off", "a gale
# ripped the tiles off". The verb is what separates those from a mirror that fell off its hook.
_STORM_TAKEN_OFF = re.compile(r"\b(?:blew|blown|ripped|tore|torn|took|snapped|knocked|came)\s+"
                              r"(?:\w+\s+){0,2}off\b", re.I)
# "the garage roof fell in" is the same claim with no preposition of its own.
_STORM_FELL_IN = re.compile(r"\bf(?:ell|allen|alling)\s+in\b", re.I)
_STORM_WEATHER = re.compile(r"\b(?:storm|storms|stormy|gale|gales|wind|winds|windy|lightning|"
                            r"hail|snow|flood|floods|flooded)\b", re.I)


def _storm_damage(understood):
    """True when the line says something came down on the person's roof, fence, shed or car."""
    line = str((understood or {}).get("clean") or (understood or {}).get("plain") or "")
    if not (_CAME_DOWN.search(line) and _CAME_DOWN_ON.search(line)):
        return False
    return bool(_STORM_WEATHER.search(line) or _STORM_LANDED.search(line)
                or _STORM_TAKEN_OFF.search(line) or _STORM_FELL_IN.search(line))


ENTRIES = [
    entry("sewage-coming-up",
          (("sewage", "sewer", "sewers", "raw sewage", "effluent", "foul water", "foul drain",
            "smelly water", "dirty water", "brown water", "waste water", "manhole", "man hole",
            "drain cover", "gully", "street", "road", "roadside", "pavement"),
           ("coming up", "coming out", "comes up", "backing up", "backed up", "bubbling up",
            "bubbles up", "overflowing", "overflowed", "surcharging", "rising", "seeping",
            "spilling out", "spilling over", "leaking out", "oozing", "smell", "smells",
            "smelly", "stink", "stinks", "collapsed", "caved in", "garden", "yard",
            "driveway")),
          ("Ring your water company's sewer line: the public sewer, the manhole and the drains "
           "under the road are theirs, and they clear them free. Keep children and pets away, "
           "don't lift a manhole cover yourself, wash your hands after touching anything it "
           "reached, and photograph the mess before you clear up for an insurance claim. If it is "
           "only ever inside your own boundary it is your drain, and that is a drain company."),
          avoid=("flood", "floods", "flooded", "flooding", "rain", "rainwater", "river",
                 "burst", "leak under", "boiler", "radiator", "gutter", "gutters", "roof",
                 "washing machine", "dishwasher", "toilet", "bath", "shower", "sink",
                 "compost", "water butt", "irrigation", "lawn", "plant", "plants", "hosepipe",
                 "water the garden", "how do i water",
                 # @airy-hippo: a cover that is gone is the council's job and there is nothing
                 # to lift, and a line that asks where to send a report wants the department,
                 # not a phone number for the water company. Neither shape is keyed, so the
                 # cards that answer them keep them.
                 "missing", "stolen", "no cover", "open manhole", "report", "reports",
                 "reported", "complaint", "complain"),
          guard=lambda understood: not _a_blocked_drain_of_your_own(understood),
          bias=1),]

_A_DISHWASHER = re.compile(r"\b(?:dishwasher|dish washer|dishdrawer|dish drawer)"
                           r"|\bdishwasher (?:salt|tablet|tablets|powder|detergent)"
                           r"|\bdish washer (?:salt|tablet|tablets|powder|detergent)", re.I)
_A_WASHER = re.compile(r"\b(?:washing machine|washer|washer dryer|washer-dryer)\b", re.I)
# The words that only ever name a machine's consumable: a dishwasher's rinse aid, and the
# washing machine's detergent, powder and softener.
_ONLY_A_MACHINE = ("rinse aid", "rinse-aid", "fabric softener", "detergent", "washing powder")

# A line with nothing left in the box is a different question from where the new box goes in:
# "i have run out of washing powder" wants what to do without it and "which detergent should i
# buy" wants a pick, and both were answered with the drawer's three compartments when the powder
# row started taking the bare name. The line is a restock only when it does not also ask where
# the stuff goes, so "i've run out of salt, where does the new bag go" keeps its answer.
_A_RESTOCK = re.compile(r"\b(?:run|runs|ran|running)\s+out\b|\bout\s+of\b|\bbuy|buys|"
                        r"buying|bought|replace|replacing|instead\s+of"
                        r"|which\s+(?:one|brand|type)\b", re.I)
_A_WHERE_IT_GOES = re.compile(r"\bwhere\b|\bcompartment|\bput|\bfill|\bgo(?:es|ing)?\b"
                              r"|\btop\s+up\b|\badd|\bload|\bpour|\bdrawer", re.I)


def _a_machine_consumable(understood):
    """True when the line asks where the salt, powder, tablet or rinse aid of a machine goes.

    The consumables are the words a person uses for a machine's own compartments - "where do i put
    the salt in the dishwasher" - and on their own they are cooking and shopping words, so the
    machine has to be named in the line as well: "where do i put the salt" is the kitchen's
    question, and "where do i put the salt in the dishwasher" is not.
    """
    said = str((understood or {}).get("plain") or (understood or {}).get("clean") or "")
    if _A_RESTOCK.search(said) and not _A_WHERE_IT_GOES.search(said):
        return False
    if _A_DISHWASHER.search(said) or _A_WASHER.search(said):
        return True
    # a word that is only ever a machine's needs no machine named beside it
    return any(word in said for word in _ONLY_A_MACHINE)


# The two machines' compartments, as the person holding the box needs them in one go.
# One sentence per compartment, so a line that names one of them can be answered with it
# (`_leading_sentence`): "where does fabric softener go" owes the flower compartment first, not
# the main wash.
_WASHER_DRAWER = (
    "The drawer is the front-left panel: pull it out and you have three compartments. "
    "The main wash (usually marked II) takes the powder, the liquid or the detergent. "
    "The small one marked I is the pre-wash and only matters if you choose that programme. "
    "The one with the flower symbol is the softener, filled to the MAX line and never over it. "
    "A tablet or a pod goes straight into the empty drum instead, before the washing, never in "
    "the drawer. If the machine has no drawer, the detergent goes in the little box inside the "
    "door.")
_DISHWASHER_COMPARTMENTS = (
    "Dishwasher salt goes in the screw-cap well in the floor of the drum, under the bottom "
    "basket: fill it to the top using a funnel, because the water softener uses it up over a few "
    "weeks and the light comes on when it is low. Rinse aid goes in the smaller compartment in "
    "the door, the one with the dial - set that to 4 or 5. The tablet or powder goes in the "
    "dispenser behind the door flap, never in the cutlery basket.")


# The consumable the line asked about leads the reply (STYLE.md: the answer in the first
# sentence). Both cards name three or four things, and read from the top they answered "how much
# rinse aid should i use" with the salt well, "where does fabric softener go" with the main wash
# compartment. The sentence that names their own word is the one they asked for, and the rest of
# the card follows it as the other compartments.
_CONSUMABLE_WORDS = (("salt",), ("rinse aid", "rinse-aid", "drying"),
                     ("tablet", "tablets", "powder", "pod", "pods", "capsule", "capsules",
                      "detergent", "liquid"),
                     ("softener", "conditioner"))


def _leading_sentence(text, said):
    """The card's sentence that names the consumable asked about, then the rest of the card."""
    asked = said.lower()
    sentences = [part.strip() for part in re.split(r"(?<=\.)\s+", text) if part.strip()]
    if len(sentences) < 2:
        return text
    best, score = 0, 0
    for index, sentence in enumerate(sentences):
        here = sentence.lower()
        hits = sum(1 for words in _CONSUMABLE_WORDS for word in words
                   if word in asked and word in here)
        if hits > score:
            best, score = index, hits
    if not score:
        return text
    return " ".join([sentences[best]] + [one for index, one in enumerate(sentences)
                                         if index != best])


def _where_the_consumable_goes(memory, understood):
    """The compartment each consumable belongs in, for the machine the line named."""
    said = str((understood or {}).get("plain") or (understood or {}).get("clean") or "")
    if _A_WASHER.search(said) and not _A_DISHWASHER.search(said):
        return _leading_sentence(_WASHER_DRAWER, said)
    if _A_DISHWASHER.search(said) or "rinse aid" in said or "rinse-aid" in said:
        return _leading_sentence(_DISHWASHER_COMPARTMENTS, said)
    # nothing but a consumable was named, and detergent and washing powder are the washing
    # machine's: the drawer answer is the one that names both of them
    return _leading_sentence(_WASHER_DRAWER, said)


# How much water a job around the house takes. It is a question about litres, and the daily
# drinking figure is the wrong answer to it: "how much water does a bath hold" and "how much
# water does a washing machine use" came back with six to eight glasses a day, and the appliance
# ones with the second-hand price of a washing machine. The number is the answer, so the thing
# that holds or uses the water is read from one table and the reply is worded for it.
WATER_USE = (
    (("bath", "bathtub", "bath tub"),
     "A full bath is about 80 litres, and a deep one nearer 100, so a short shower is the cheaper "
     "wash: five minutes under a normal shower is around 50 litres."),
    (("shower",),
     "A shower runs at about 10 litres a minute, so five minutes is 50 litres and ten is 100; a "
     "power shower can be twice that, and turning the tap off while you soap up is the free half "
     "of the saving."),
    (("toilet", "flush", "cistern"),
     "A modern toilet uses about 6 litres a flush and an older one 9 to 13, so a family of four "
     "flushing ten times a day is 240 to 500 litres a week. Put a few drops of food colouring in "
     "the cistern: if it reaches the pan without a flush, the valve is leaking and that is a "
     "cheap repair that pays for itself."),
    (("washing machine", "washer dryer", "wash cycle"),
     "A washing machine cycle uses about 45 to 50 litres, and a half load uses nearly the same as "
     "a full one, so wait for a full drum; a 30 degree cycle saves the electricity rather than "
     "the water."),
    (("dishwasher",),
     "A dishwasher uses about 10 to 15 litres a wash, which is less than washing up by hand under "
     "a running tap, so run it full and on the eco setting rather than rinsing the plates first."),
    (("bucket", "mop bucket"),
     "A bucket is about 10 litres, a mop bucket 5 to 15 depending on the size, which is the "
     "measure to count in when you are sizing a water butt: a 100 litre butt is ten buckets."),
    (("hose", "sprinkler", "hosepipe"),
     "A garden hose runs at 10 to 15 litres a minute, so twenty minutes with a sprinkler is 200 to "
     "300 litres, more than a family uses indoors in a day: a watering can at the roots is the "
     "same water where the plant can reach it."),
    (("hot tub",),
     "A hot tub holds 1,000 to 1,500 litres, and that water is changed every few weeks rather than "
     "every day, so a cover on it is the difference between a cheap one and a frightening bill."),
    (("water butt", "butt"),
     "A water butt is sold by size: 100 to 250 litres is the usual garden one, and a roof gives "
     "about 1 litre for every millimetre of rain on every square metre of it, so 1,000 litres a "
     "year per square metre in most of the UK."),
    (("paddling pool", "paddling pools", "swimming pool"),
     "Measure it and multiply: length times width times depth in metres, times 1,000, gives "
     "litres. A 2m by 1m paddling pool 30cm deep holds 600 litres, and a cubic metre is 1,000."),
)


def _water_use(memory, understood):
    """Litres for the thing that holds or uses the water, read from one table."""
    line = str(understood.get("text") or understood.get("clean") or "")
    row = _longest_row(line, WATER_USE)
    if row is not None:
        return row[1]
    return ("Measure it and multiply: length times width times depth in metres, times 1,000, "
            "gives litres, and a cubic metre is 1,000 litres. A full bath is about 80 litres and "
            "five minutes in the shower about 50.")


# A length of stay is a travel question wherever it is asked: "how many days in bath" is the city
# of Bath, not the tub, and this row's ask holds "many" and "how much", so the litres card answered
# it and "how many days do i need in bath" as well. It is a guard and not a phrase in the avoid
# list for two reasons. The asking words sit far from the place ("do i need in bath", "should i
# spend in bath" are more than two words from "bath"), and an avoid phrase only reads across two
# words that do not count. And the place is asked of the travel table rather than named here, so
# any city added to it is covered - Bath is only the one that is also a common word today.
_A_LENGTH_OF_STAY_ASK = re.compile(
    r"\b(?:how long|how many days|how many nights|how much time|how many hours|how many weeks)\b",
    re.I)


def _not_a_length_of_stay(understood):
    """False when the line is a length of stay in a city the travel table knows."""
    from .lookup import the_line
    from .travel import CITY_DAYS, _find_in

    line = the_line(understood)
    if not _A_LENGTH_OF_STAY_ASK.search(line):
        return True
    return not _find_in(line, CITY_DAYS)


ENTRIES = ENTRIES + [
    # "do i need to rinse plates before the dishwasher" was answered with "a dishwasher is worth
    # it for three or more people", which is the buying question and no use to someone standing at
    # the sink. Pre-rinsing is its own question with its own answer.
    entry("dishwasher-rinse-before",
          (("dishwasher", "dish washer", "plates", "dishes", "pans", "cutlery"),
           # A bare "before" is not an ask: with "dishes"/"pans" as names it took
           # "should i preheat the pan before adding oil" and "should i wash the dishes before my
           # mum arrives". The machine, or the rinse itself, is what the line has to carry.
           ("rinse", "rinsing", "pre rinse", "pre-rinse", "prerinse", "scrape", "scraping",
            "load it", "loading", "put them in", "put it in",
            # NOT "do i need to", "should i wash" or a bare "before": those are the asks of a
            # sink full of dishes and of a pan waiting for oil, and both were answered here
            "before loading", "before i load", "before it goes in", "before they go in",
            "before putting them", "rinse first", "rinse them", "rinse the dishes",
            "have to rinse", "need to rinse",
            # the same question said as its cost: "is rinsing plates a waste of water"
            "waste", "wasting", "waste of water", "uses less water", "use less water",
            "use much water", "worth rinsing",
            # the machine named beside the wash is the same question: "do i have to wash plates
            # before the dishwasher". The phrase, not the machine word, is what carries it.
            "before the dishwasher", "before it goes in the dishwasher",
            "wash plates before", "wash the plates before", "have to wash plates",
            "have to wash the plates", "wash them before",
            # NOT the machine's name on its own, and not "in the dishwasher": the machine is in
            # the first group already, and a second path through it alone answered "can i put my
            # pan in the dishwasher", "the dishwasher wont drain" and "can i put my glasses in the
            # dishwasher" with the rinse card. The rinse or the scrape is what this row is for.
            )),
          "No - scrape the food into the bin and load them. Modern tablets and a 55C or hotter "
          "cycle cope with grease and smears, and rinsing first wastes the water and time the "
          "machine was bought to save. Soak burnt-on pans and give the filter a rinse weekly; "
          "that is the washing up worth doing.",
          # the machine's own cleaning, a salty or cloudy load, and the buying question are all
          # other rows: salt, rinse aid, smell, price and which one to buy stand this one down
          avoid=("salt", "rinse aid", "cloudy", "streaks", "smell", "smells", "squeaky",
                 "filter", "clean it", "cleaning", "clean the", "worth it", "should i buy",
                 "which one", "best", "price", "cost", "smeg", "bosch", "shark", "miele"),
          # a pre-rinse line and the "is a dishwasher worth it" rows score the same on the
          # machine's name, and the buying question was answering the sink
          bias=2),

    # "How much water does a bath hold" is a litres question about a thing in the house, so the
    # thing has to be named and the ask has to be about water or an amount. "My toilet is
    # blocked" and "the shower is weak" name a fixture with no water in the line at all, and
    # those belong to the repair entries.
    entry("water-use",
          (("bath", "baths", "bathtub", "shower", "showers", "toilet", "toilets", "flush",
            "cistern", "washing machine", "washing machines", "dishwasher", "dishwashers",
            "bucket", "buckets", "mop bucket", "hose", "hosepipe", "sprinkler",
            "paddling pool", "swimming pool", "hot tub", "water butt", "rainwater"),
           ("water", "litre", "litres", "liter", "liters", "much", "many", "use", "uses",
            "used", "hold", "holds", "per", "how much", "how many")),
          _water_use,
          # A tie with the second-hand price row for the same machine, and a line that asks how
          # much water a washer uses is the litre answer: the price row is about buying one.
          bias=1,
          # ...and a length of stay in a city is the travel card's question
          guard=_not_a_length_of_stay,
          avoid=("should i drink", "drink", "drinking", "glasses", "a day", "enough",
                 "hydrat", "urine", "dehydrated", "drink more",
                 # The table answers litres for the things that hold water, and an eye is not
                 # one of them: "i keep getting water in my eye in the shower" was answered with
                 # the ten-litres-a-minute figure because "shower" and "water" are both here.
                 # The eye is the subject of that line, so the row stands down for it.
                 "in my eye", "in my eyes", "in the eye", "in the eyes", "my eye", "my eyes",
                 "eyeball", "eyelid", "my eyes are", "water in my eye",
                 # How much water goes in a child's bath is a question about depth and
                 # temperature, and this row answered it with "a full bath is about 80 litres, and
                 # a deep one nearer 100": the numbers were right and the advice was backwards.
                 # The bath-depth card in this file (baby-bath) and the one in family.py hold it.
                 "bath for a toddler", "bath for a baby", "bath for a child", "bath for kids",
                 "bath for my toddler", "bath for my baby", "bath for my child", "bath for the kids",
                 "deep should the bath", "deep the bath", "how deep should the water",
                 "water be for a toddler", "water be for a baby", "water be for a child",
                 # a ban is about what is allowed, not about litres: "can i use a hosepipe in a
                 # drought" was told the hose runs at 10 to 15 litres a minute
                 "drought", "hosepipe ban", "hose ban", "banned", "ban on", "restriction",
                 "restrictions", "shortage", "not allowed",
                 # a fixture that is broken, blocked or weak is a repair, not a volume
                 "blocked", "broke", "broken", "not flushing", "wont flush", "won't flush",
                 "weak", "leaking", "leak", "dripping", "drips", "no water", "wont drain",
                 "won't drain", "not draining", "smells", "smelly", "install", "installing",
                 # Water in the wrong place is a fault, whatever fixture it is coming out of:
                 # "water is pouring out of my washing machine" and "the machine is full of
                 # water" are the leak and the drain answers, not the litres one.
                 "coming out", "coming out of", "coming from", "pouring", "poured", "leaks out",
                 # how the water moves, not just what it is doing: "water is running into my
                 # toilet pan" and "water is pooling by my toilet" were both given the litres
                 # card, and a person watching water arrive wants the valve, not the usage.
                 # not the bare "pooling": it stems to "pool" and took "how much water in a
                 # paddling pool" with it
                 "running into", "running down", "running out", "water is pooling",
                 "is pooling", "pooling around", "pooling under", "pool of water",
                 "seeping", "trickling",
                 # ...and water that has changed colour or gone cloudy is a fault too
                 "went blue", "turned blue", "water is blue", "water went", "water turned",
                 "discoloured", "cloudy", "bits in", "gritty",
                 "full of water", "full of it", "sitting in", "in the drum", "in the bottom",
                 "overflow", "overflowing", "flooded", "flooding", "puddle", "puddles",
                 "not spinning", "isnt spinning", "stopped mid", "stops halfway",
                 "wet", "soaked", "damp", "smell", "stink", "stinks",
                 "fit a", "fitting", "replace", "replacing", "cost", "costs", "quote",
                 "price", "cheap", "cheapest", "buy", "hard water", "soft water", "limescale",
                 # "how much is a shower" is the price of the fitting, not the litres it runs
                 # at: the price entries own every "how much is" shape on a thing you buy.
                 "how much is", "how much are", "how much for", "on finance", "in the sales",
                 "kettle", "boiler", "heating", "pressure", "bills", "bill", "meter")),
    entry("storm-damage",
          (("fell", "fallen", "blew", "blown", "down", "collapsed", "storm", "damaged", "damage",
            "gale", "gales", "lightning", "uprooted"),
           ("roof", "roofs", "tiles", "slates", "chimney", "ceiling", "ceilings",
            "guttering", "gutter",
            "shed", "sheds", "garage", "carport", "conservatory", "greenhouse",
            "window", "windows", "car", "cars", "van", "vans", "drive", "driveway", "garden",
            "house", "outbuilding", "wall", "walls", "tree", "trees", "branch", "branches",
            "insurance", "insurer", "claim", "policy")),
          "Make it safe, photograph it before you clear anything, and ring your insurer's claim "
          "line: a roof, a shed or a fence is usually on the buildings cover, a car on its own "
          "comprehensive policy. Tarpaulin over the hole, weighed down - not under it. Keep the "
          "debris and the receipts, and report it within a few days: the deadline is short. A "
          "neighbour's tree is an insurance claim too unless they were negligent, so tell them "
          "and keep the photos.",
          avoid=("leak", "leaking", "leaks", "dripping", "wet patch", "damp", "mould", "quote",
                 "quotes", "how much", "cost", "price", "cheapest", "buy", "cost to replace",
                 # a fence panel, a post or a dent is the repair card's line, and a line that asks
                 # whether the policy covers something wants the policy's answer, not the steps
                 "garden fence", "fence panel", "panel", "panels", "posts", "dent", "dented",
                 "dents", "scratch", "scratched", "covered", "cover", "does insurance",
                 # the person under it is the safety card's line, so a line that says it came
                 # down on the person themselves stands this one down rather than talking about
                 # insurance to somebody who may be hurt
                 "on top of me", "on me", "on us", "fell on me", "fell on us", "came down on me",
                 "collapsed on me", "hit me", "hit my back", "on my back",
                 "my son", "my daughter", "my dad", "my mum", "my wife", "my husband", "my leg",
                 "my foot", "my head", "my arm"),
          guard=_storm_damage,
          bias=3),
]

# A hosepipe in a drought is a question about what is allowed, and the litres row answered it
# with the flow rate of a hose. The ban is the answer: what it covers, what still works, and who
# to ask whether one is on.
ENTRIES.append(entry(
    "hose-ban",
    (("hosepipe", "hose", "sprinkler", "pressure washer"),
     ("drought", "ban", "banned", "restriction", "restrictions", "shortage", "not allowed",
      "allowed", "illegal", "fine", "rules")),
    "Water with a can or a bucket - that is allowed under a ban - and leave the hose, the "
    "sprinkler, the pressure washer and filling a pool, which are the things a ban usually "
    "covers. Your water company says on its site whether one is on in your area and exactly what "
    "it covers, and in England and Wales breaking one can mean a fine of up to \u00a31,000.",
    # how often to water a plant in a dry spell is the garden's question, and it says "drought"
    # too; the ban is only about the hose
    avoid=("how often", "watering can", "tomato", "tomatoes", "plants", "plant", "lawn",
           "flowers", "veg", "beds", "seedlings", "hanging basket")))

# "how do i make a bed" and "how do i stop a mattress sliding" were both hedges on main; the
# items people actually want are the order of the layers and the thing that stops the sheet
# creeping. `bedsheets-often` owns washing them and `mattress-clean` owns cleaning them, so both
# of these ask for their own words first.
ENTRIES.append(entry(
    "make-a-bed",
    (("bed", "beds", "duvet", "sheet", "sheets", "pillow", "pillows", "pillowcase", "bedding"),
     ("make", "making", "made", "tidy", "tidy up", "neat", "hospital corners", "properly",
      "quickly", "nicely", "layer", "layers", "order")),
    "Fitted sheet first, corners over the corners of the mattress and the elastic under it, then "
    "the flat sheet if you use one, then the duvet shaken out so it hangs evenly on both sides. "
    "Pillows last, plumped and stood up against the headboard, or laid flat if the bed is only "
    "going to be slept in. Pull the duvet back a hand's width at the top so the sheet shows, and "
    "the bed looks made with the top edge straight.",
    # "hospital" is not here: "hospital corners" is one of the shapes this answers, and the
    # avoid word would match its own key.
    avoid=("wash", "washing", "often", "change", "stain", "stains", "clean", "cleaning", "mattress",
           "size", "buy", "buying", "wet", "sweat", "bed bug", "bed bugs", "care home",
           "nursery", "cot", "toddler", "how long",
           # a raised bed is a garden box: "how do i make a raised bed" was told how to put a
           # fitted sheet on a mattress, because "bed" and "make" are all it took
           "raised bed", "raised beds", "garden", "allotment", "compost", "soil", "veg",
           "vegetables", "plant", "plants", "planting", "grow", "growing", "flower bed",
           "flower beds", "flowerbed", "flowerbeds", "border", "borders", "turf", "lawn",
           # A body that lurches when the person gets up is not a bed to be made: "i go woozy
           # if i get out of bed quickly" was told where the fitted sheet goes, because "bed"
           # and "quickly" are all this row needs. A symptom in the line stands it down, and the
           # dizzy answer (`dizzy-standing`) has the row for that moment.
           "woozy", "dizzy", "dizziness", "light headed", "lightheaded", "faint", "fainting",
           "giddy", "swimmy", "vertigo", "unsteady", "nausea", "nauseous", "spins", "spin",
           "swims", "hurts", "ache", "aching", "sore", "weak", "shaky", "breathless",
           "getting up", "get up too", "out of bed"),
    ask=("make", "making", "made", "tidy", "neat", "hospital corners", "properly", "quickly",
         "nicely", "layer", "layers", "order")))

ENTRIES.append(entry(
    "mattress-slide",
    (("mattress", "mattresses"),
     ("slide", "slides", "sliding", "slip", "slips", "slipping", "shift", "shifts", "shifting",
      "moves", "moving", "creep", "creeps", "creeping", "wont stay", "doesnt stay", "stay put",
      "keeps moving", "keeps sliding",
      # a sheet that comes off a mattress is the same question as a mattress that slides
      "keeps coming off", "coming off", "comes off", "keeps falling off", "falls off")),
    "Put a non-slip mattress pad or a piece of rubbery shelf liner under it, cut to the frame, and "
    "push the mattress back hard against the headboard before you put the sheets on. A bed frame "
    "with a lip or a box base holds it better than slats, and if there is a gap at the foot, a "
    "rolled towel between mattress and frame stops the creep. Smooth bedding slides more than "
    "cotton or linen, so a fitted sheet tucked right under the corners helps too.",
    avoid=("clean", "cleaning", "stain", "stains", "smell", "size", "buy", "buying", "price",
           "cost", "best", "which", "how long", "replace", "lumpy", "sagging", "back pain"),
    ask=("slide", "slides", "sliding", "slip", "slips", "slipping", "shift", "shifts", "shifting",
         "creep", "creeps", "creeping", "stay put", "keeps moving", "keeps sliding", "wont stay",
         "doesnt stay", "keeps coming off", "coming off", "comes off", "keeps falling off",
         "falls off")))
# The same question about everything else that will not stay where it is put. A mattress has its
# own card because a bed frame is the thing that holds it; a fitted sheet, a cushion, a throw and
# a sofa cover are held by the fabric and the fit, and all four were reaching the stain row
# ("blot, do not rub") because " off" is how both a mark and a cushion come off something.
ENTRIES.append(entry(
    "cushion-wont-stay",
    (("cushion", "cushions", "fitted sheet", "fitted sheets", "sheet", "sheets", "throw", "throws",
      "sofa cover", "sofa covers", "seat pad", "seat pads", "blanket", "blankets",
      "duvet", "duvets"),
     ("slide", "slides", "sliding", "slip", "slips", "slipping", "keeps coming off", "coming off",
      "comes off", "keeps falling off", "falls off", "wont stay", "won't stay", "doesnt stay",
      "doesn't stay", "not staying", "keeps moving", "shift", "shifts", "shifting", "creep",
      "creeps", "stay put")),
    "A grip pad under it, not a tighter fit: cut a square of that rubbery open-weave shelf liner to "
    "sit inside the cushion's seam or under the throw, and it stops dead. A fitted sheet that will "
    "not stay is the elastic gone slack, a sheet a size too small, or a deep mattress on a shallow "
    "sheet - sheet clips or a strap across the corners will hold it until you replace it. Cotton "
    "and linen grip each other better than a smooth polyester, so a rougher cover is the cheap fix.",
    # a stain on a cushion and a cushion that slides are the same words in a different order
    avoid=("stain", "stains", "stained", "mark", "marks", "spill", "spilled", "spilt", "smell",
           "smells", "clean", "cleaning", "wash", "washing", "buy", "buying", "size", "price",
           "how long", "replace it", "mattress")))

# "how do i complain about a builder" reached the shop-complaint answer - "complain to the shop
# first, say what you bought" - and "how do i complain about a painter" reached nothing at all,
# because the composer's trader list has no painter in it. Work done on your own house is its
# own complaint: an agreed job, a deposit, and a person who has to be asked back.
ENTRIES.append(entry(
    "tradesman-bad-job",
    (("builder", "builders", "tradesman", "tradesmen", "plumber", "plumbers", "electrician",
      "electricians", "decorator", "decorators", "painter", "painters", "roofer", "roofers",
      "contractor", "contractors", "plasterer", "plasterers", "tiler", "tilers", "joiner",
      "joiner", "workman", "workmen", "fitter", "fitters", "landscaper", "installer",
      "rogue trader", "cowboy", "cowboys", "cowboy builder", "trade"),
     ("complain", "complains", "complained", "complaint", "bad job", "shoddy", "botched",
      "unfinished", "not finished", "half finished", "snag", "snags", "snagging", "did a bad",
      "done wrong", "took my money", "took the money", "ran off", "disappeared", "vanished",
      "wont come back", "won't come back", "not coming back", "refuses", "refusing", "guarantee",
      "warranty", "what can i do", "what are my rights", "owe", "withhold", "unhappy",
      "not happy", "poor job", "mess", "leak", "damp", "crack", "cracks", "wrong")),
    "Put it in writing the same day and take dated photos of the work: what you agreed, what is "
    "wrong, what you want put right and by when, and say you are holding the balance until it is "
    "done. Give them 14 days to come back and fix it. Then use the levers you already have: a "
    "trade body scheme (FMB, TrustMark, Which? Trusted Traders) has a dispute service, a card "
    "payment over 100 pounds is a section 75 claim with your bank, and money owed up to 10,000 "
    "pounds goes through the small claims track online without a solicitor. A tradesman who took "
    "a deposit and vanished is a police matter, so report it and keep every message.",
    # The letters are the other questions this domain already answers, and a quote, a
    # recommendation or a legal claim of negligence is not "he did a bad job".
    avoid=("landlord", "neighbour", "neighbor", "council", "insurance", "insurer", "claim on",
           "how do i find", "find a good", "recommend", "recommendation", "how much should",
           "quote", "quotes", "cost", "price", "cheapest", "check", "vet a", "deposit protection",
           "sue", "solicitor", "negligence", "court claim", "planning permission",
           "building regulations", "extension cost", "diy", "myself", "yourself"),
    ask=("complain", "complains", "complained", "complaint", "bad job", "shoddy", "botched",
         "unfinished", "not finished", "snag", "snags", "took my money", "wont come back",
         "won't come back", "not coming back", "refuses", "refusing", "what can i do",
         "what are my rights", "guarantee", "poor job", "not happy", "unhappy")))

# Where to put things when there is nowhere to put them. "how do i make room in a small kitchen"
# was answered by the cleaning entry (it shares "kitchen" and "room"), "small kitchen storage
# ideas" and "how do i store things in a small flat" were shrugs, and "how can i make my flat
# feel bigger" reached the seasoning answer. Two questions, because the answer differs: one is
# where the things go, the other is why the room looks small.
HOME_ROOM_WORDS = ("room", "space", "storage", "store", "storing", "stuff", "clutter",
                   "cupboard", "cupboards", "wardrobe", "wardrobes", "shelf", "shelves",
                   "tidy", "bedroom", "kitchen", "clothes",
                   # "there is nowhere to put anything in my flat" named no key word at all
                   # once "nowhere" had covered its one word: the home itself is the other half
                   # of a line about where the things go.
                   "flat", "flats", "house", "home", "place", "bedsit")
NO_ROOM_WORDS = ("no room", "no space", "nowhere", "not enough", "too much stuff",
                 "no storage", "make room", "make space", "more space", "more room", "fit it",
                 "small", "tiny", "little", "tidy", "clutter",
                 "nowhere to put", "nowhere to keep", "nowhere to store", "anywhere",
                 "cramped", "poky", "pokey", "squashed", "too many",
                 # "im trying to get my flat sorted before winter" and "i want to clear out the
                 # bedroom": the job is the same as "no room", and without these the line had a
                 # room word and no second half, so it got a shrug.
                 "sorted", "sort out", "sort it out", "declutter", "clear out", "clear it out",
                 "tidy up", "tidy it up", "have a clearout")

# --- the kit that wears out --------------------------------------------------------------
#
# "when should i replace my running shoes", "how long do running shoes last", "how do i know
# when my shoes are done", "when do i need a new bike helmet", "how long does a smoke alarm
# last" and "how often should i get new contact lenses" are one shape, not six questions: a
# thing is used up, and the person wants the interval and the sign that it is finished. Each of
# them fell to whatever owned the noun - the running-shoe card that says what to pay for a
# fitting ("For running, yes: a proper pair ... £90 to £130"), the smoke alarm's low-battery
# chirp, a shop's contact-lens fitting fee - because a buying row owns the name of the thing and
# the question is about the end of it.
#
# One table, keyed by the name of the thing, in the same shape as LIFESPAN above: the span, and
# the one sign that decides it. A row that buys or fixes the same thing keeps its own line by
# answering a buying or a fault word, and stands down for the life words below.
WEARS_OUT = (
    {"names": ("running shoes", "running trainers", "running shoe", "runners", "trainers"),
     "called": "running shoes",
     "span": "every 500 to 800km, which is six to twelve months for most people",
     "sign": ("the midsole foam goes before the tread looks worn, so the sign is a shoe that "
              "feels flat or leaves you stiff the morning after a run. Keep the old pair for the "
              "garden")},
    {"names": ("bike helmet", "cycling helmet", "cycle helmet", "helmet", "helmets"),
     "called": "a bike helmet",
     "span": "every three to five years, and at once after any knock",
     "sign": ("the foam is what absorbs a hit and it does not spring back, so a helmet that has "
              "been crashed or dropped hard is finished even when the shell looks perfect, and a "
              "chalky or cracked shell is the other sign")},
    {"names": ("smoke alarm", "smoke alarms", "smoke detector", "smoke detectors"),
     "called": "a smoke alarm",
     "span": "every ten years, with a new battery every year",
     "sign": ("the sensor drifts with age and most modern ones are sealed, so the replace-by "
              "date stamped on the back is the one to go by, and it should be tested monthly"),
     # a chirp, a battery swap and an alarm that goes off at the toaster are the fault rows'
     "avoid": ("beep", "beeps", "beeping", "chirp", "chirping", "goes off", "going off",
               "the battery is flat", "replace the battery", "change the battery", "low battery",
               "test it",
               "toast", "burnt", "burning", "cooking", "steam", "fire")},
    {"names": ("contact lenses", "contact lens", "monthly lenses", "daily lenses", "contacts"),
     "called": "contact lenses",
     "span": "as often as the pack says: daily ones every day, monthlies every month, and never "
             "past the date on the blister",
     "sign": ("the material collects protein and deposits as it is worn and the case is where the "
              "biofilm grows, so change the case every three months too"),
     "avoid": ("solution", "sore", "red", "infection", "infected", "itch", "itchy", "dry eye",
               "put them in", "put it in", "take them out", "stuck", "lost", "torn", "cost",
               "costs", "price", "month", "a month")},
    {"names": ("cycling shoes", "cycle shoes", "clipless", "cleats", "cleat"),
     "called": "cycling shoes and cleats",
     "span": "every 1,000 to 2,000km for the cleats, and a new pair of shoes when the sole or "
             "the ratchet has gone",
     "sign": ("the cleat wears on the side you put your foot down first, so it starts clipping in "
              "loose or rocking side to side, and a shoe whose sole flexes over the pedal is "
              "spreading the load onto your foot instead")},
    {"names": ("walking boots", "walking boot", "hiking boots", "hiking boot", "boots"),
     "called": "walking boots",
     "span": "every 800 to 1,000 miles, or sooner if the sole has gone thin under the ball of "
             "the foot",
     "sign": ("a boot is finished when the midsole has compressed and it no longer holds your "
              "foot over rough ground, which is why a leather upper in fine condition can still "
              "be a boot to throw away; a resole buys another few hundred miles"),
     "avoid": ("wax", "dubbin", "waterproof", "waterproofing", "laces", "laces came", "smell",
               "wet", "leak", "leaking", "squeak", "rub", "blister", "blisters", "buy",
               "which", "womens", "mens", "size", "fit")},
    {"names": ("climbing harness", "harness", "harnesses"),
     "called": "a climbing harness",
     "span": "every five years of regular use, and ten years from new even if it has hardly been used",
     "sign": ("the webbing and the stitching age from sweat, sun and abrasion rather than from "
              "wear you can see, so the date on the label is the rule; retire it at once after "
              "any load that was not a normal fall, and after a big fall"),
     "avoid": ("baby", "toddler", "car seat", "child", "dog", "seat belt", "seatbelt",
               "cable", "wiring", "loft", "climbing wall prices", "hire")},
    {"names": ("phone battery", "battery", "batteries"),
     "called": "a phone battery",
     "span": "every two to three years, or about 500 full charges",
     "sign": ("the settings show the health: on an iPhone it is Settings, Battery, Battery "
              "Health, and anything under 80% is worn out. A phone that dies at 20%, shuts down "
              "in the cold or gets hot on charge is the same verdict, and a new battery is "
              "£30 to £70 fitted rather than a new handset"),
     "avoid": ("drain", "drains", "draining", "dies", "dying", "dies fast", "hot", "swollen",
               "swelling", "charge", "charging", "charger", "won't charge", "wont charge",
               "not charging", "percentage", "screen", "screenshot", "laptop", "car battery",
               "car", "smoke alarm", "aa", "aaa", "remote", "watch", "replace it myself",
               "how do i replace")},
)
# The life words: how long it lasts, when to replace it, and how worn it is. "Last" and "replace"
# are read as whole words, because "last" sits inside "lasts" and "lasting" by design (lookup's
# avoid is a loose match) and inside nothing else that matters here.
_WEAR_ASK = ("how long", "how many miles", "how many km", "how many charges", "last", "lasts",
             "lasting", "life of", "lifespan", "replace", "replacing", "replacement",
             "need a new", "needs replacing", "time for a new", "time to change", "worn out",
             "wearing out", "worn down", "how often", "when should i", "when do i", "when to",
             "change my", "get a new")
# A buying word, a fault, or something done to the thing is not the end of its life: the shop
# card, the repair rows and the how-to rows keep those lines. The per-thing words a row needs
# are in its own "avoid".
_NOT_A_WEAR = ("buy", "buying", "bought", "cheap", "cheapest", "price", "prices", "cost",
               "costs", "worth", "shop", "shops", "which", "best", "fit", "fitted", "fitting",
               "size", "gait", "sale", "deal", "money", "afford",
               "broken", "cracked", "split", "smell", "clean", "cleaning", "wash", "washing",
               "how do i replace it myself", "myself",
               # a battery made to last longer is the looking-after answer, not the interval that
               # says when it is finished: "how do i make my phone battery last longer" was told
               # to buy a new battery every two to three years, when the person wants the day to
               # run to bedtime. The words name the battery, because the same phrasing about a
               # pair of shoes asks when they are done, and the interval is the right answer
               # there.
               "battery last longer", "battery lasts longer", "make the battery last",
               "battery to last", "battery for longer", "phone last all day",
               "make it last all day", "get through the day")


def _a_wear(memory, understood):
    """The interval and the sign, for the thing the line names."""
    reading = understood if isinstance(understood, dict) else {}
    said = str(reading.get("clean") or reading.get("plain") or "").lower()
    best, row = "", None
    for candidate in WEARS_OUT:
        for name in candidate["names"]:
            if len(name) > len(best) and re.search(r"\b" + re.escape(name) + r"\b", said):
                best, row = name, candidate
    if row is None:
        return ""
    return "Replace %s %s: %s." % (row["called"], row["span"], row["sign"])


def _worn_out_avoid():
    """The words that stand the whole table down, from the shared list and each row's own.

    A word that is the name of some thing in the table is not one of them: the smoke alarm's
    "battery" and the phone battery's "battery" are the same word, and standing the table down on
    it would leave both questions to the chirp card and the drain tips.
    """
    names = set(name for row in WEARS_OUT for name in row["names"])
    words = list(_NOT_A_WEAR)
    for row in WEARS_OUT:
        for word in row.get("avoid", ()):
            if word not in names and word not in words:
                words.append(word)
    return tuple(words)


ENTRIES.append(entry(
    "worn-out-kit",
    (tuple(name for row in WEARS_OUT for name in row["names"]), _WEAR_ASK),
    _a_wear,
    avoid=_worn_out_avoid(),
    ask=_WEAR_ASK,
    bias=3,
))

ENTRIES += [
    entry("no-room-at-home",
          (HOME_ROOM_WORDS, NO_ROOM_WORDS),
          "Go up before you go out: a shelf over the door, hooks on the back of a cupboard door "
          "and boxes stacked to the ceiling use space you already have. Take the doors off one "
          "base cupboard and put a bin or open shelves in it, keep the worktop clear, and send "
          "anything you use less than monthly to the top of a wardrobe or under the bed.",
          # A bigger room is a different answer, and a full disk is a computer's: the storage
          # rows in devices.py are keyed on the same two words.
          avoid=("feel bigger", "look bigger", "feels small", "looks small", "more spacious",
                 "mac", "macbook", "disk", "laptop", "computer", "phone", "iphone", "pc",
                 "windows", "ssd", "hard drive", "gb",
                 # an inbox with no room in it is the mailbox answer's, not a shelf over a door
                 "inbox", "email", "emails", "mailbox", "mail box", "gmail", "outlook",
                 # painting a small room is the painting answer's, not a storage one.
                 "paint", "painting", "decorate", "decorating", "wallpaper", "tip", "tips",
                 # "what dog would suit a small flat" is the dog answer, and "flat" was enough
                 # to make it a storage one
                 "dog", "dogs", "puppy", "breed", "cat", "cats", "kitten", "pet", "pets",
                 # "i'm moving flat next month and i've got too much stuff" carries this entry's
                 # own phrase, "too much stuff", but the question is the move: packing and
                 # thinning out is the moving answer's, and a shelf over the door is a place for
                 # things in a flat that is staying put. A move is said with a few words, and
                 # they are all here, so a storage line with none of them is untouched.
                 "moving", "move", "moved", "removal", "removals", "movers", "pack",
                 "packing", "packed", "unpack", "unpacking", "van",
                 # A hotel with no room is the travel answer's: "the hotel has no room for us"
                 # was told where to put a shelf over the door. Only the booking problem stands
                 # this row down, though - a room being small is still a storage question, and
                 # "my hotel room is too small" was losing the shelf tip to a bare "hotel".
                 "booking", "booked", "rebooking", "reservation", "reception", "check in",
                 "check-in", "overbooked", "over booked", "double booked", "double-booked",
                 "walked to", "turned away", "gave our room away", "gave my room away",
                 "gave away our room", "gave away my room", "no room for us", "no room for me",
                 # "have no room"/"has no room" were here for "the hotel has no room for us",
                 # and they also fenced off "i have no room in my kitchen" and "my kitchen has
                 # no room", which are this row's own question. The sense reading above tells the
                 # two apart from the whole sentence, so the phrases are gone.
                 # A room that is *in a state* is a job to start, not a question about where the
                 # things go: "the kitchen is a mess" and "the house is a mess and i cant cope"
                 # were told to put a shelf over the door. The state rows answer those.
                 # "messy" is a loose form of "mess", so the mess has to be said in the shapes
                 # people actually use: the bare "a mess" is not enough for "what a mess my
                 # kitchen is", so the whole family of ways of saying it is here.
                 "a mess", "in a mess", "what a mess", "such a mess", "a right mess", "right mess",
                 "complete mess", "absolute mess", "total mess",
                 "a tip", "a shambles", "in a state", "a state",
                 "cant cope", "can't cope", "cannot cope", "coping", "no energy", "too tired",
                 "overwhelmed", "guests", "visitors", "coming over", "coming round",
                 # Getting rid of things is the clear-out's question and a shelf is the answer to
                 # a different one: "how do i declutter my house" was told where to put a box,
                 # which is what you do after the clear-out, not instead of it. A storage line
                 # never says give away, sell or throw out.
                 "declutter", "decluttering", "clear out", "clearout", "clear it out",
                 "clearing out", "clear the clutter", "get rid of", "throw out", "throwing out",
                 "throw away", "throwing away", "bin it", "donate", "donating", "charity shop",
                 "car boot", "freecycle", "free ad"),
          ask=("kitchen", "flat", "house", "home", "bedroom", "room", "cupboard", "wardrobe",
               "hall", "bathroom", "lounge", "living room", "utility", "shed", "loft"),
          guard=_the_space_in_the_house,
          # "my bedroom is too small for my clothes" also ticks the shrunk-jumper answer on
          # "clothes" and "small", and where the clothes go is this question. Two, not one: the
          # jumper row is in a domain of its own and its rarity bonus tied with this one.
          bias=2),
    entry("room-feels-bigger",
          (("flat", "room", "bedroom", "lounge", "living room", "kitchen", "house", "box room"),
           ("feel bigger", "look bigger", "feels small", "feels tiny", "looks small",
            "feel small", "more spacious", "bigger", "size of")),
          "Paint it all one pale colour, ceiling included, and put a mirror where it catches a "
          "window: the eye reads the reflection as another room. Hang the curtains at ceiling "
          "height rather than at the window, keep the floor visible, and use one rug that stops "
          "short of the walls rather than carpet that runs wall to wall.",
          # Where the things go is the entry above, and a line about the size of a dish or a
          # portion is neither. A line that says paint is a painting question even when the room
          # in it is small: "how do i paint a small room to make it look bigger" is the paint
          # answer's, which says the colour, the filler and the coats, and this answer cannot
          # tell anyone how to hold a brush.
          avoid=("storage", "store", "cupboard", "wardrobe", "stuff", "clutter", "no room",
                 "no space", "portion", "serving", "recipe", "cake", "tin", "oven", "dish",
                 "paint", "paints", "painting", "painted", "roller", "undercoat", "primer",
                 "gloss", "emulsion", "filler", "sandpaper", "masking")),

    # Leaving the house empty. Every word of "how do i keep my house safe while im away" was
    # already known and none of it answered: the burglar alarm rows are about fitting one and
    # the holiday rows are about the trip, so the question fell through to "I don't know enough".
    # "place" on its own was the one key word that is not a house: "best places to visit in
    # spain for a week" is a trip question and it was read as a house left empty, because
    # "places" holds "place" and "for a week" is the trip. "my place" and "the place" keep the
    # household lines ("how do i keep the place safe while we are away").
    entry("house-safe-away",
          (("house", "home", "flat", "apartment", "bungalow", "my place", "the place"),
           ("away", "holiday", "holidays", "vacation", "going away", "left empty", "empty",
            "unoccupied", "while we're gone", "while im away", "while i'm away",
            "while we are away", "for two weeks", "for a week", "for a month", "burglar",
            "burglars", "break in", "break-in", "broken into", "secure", "security")),
          "Make it look lived in and keep the signs of absence out of sight: a couple of plug-in "
          "lamp timers, a radio on a timer, post held at the sorting office and a bin put out by "
          "a neighbour, because piled post and a full bin are what tell a burglar the house is "
          "empty. Ask a neighbour to park on the drive, don't post the trip until you are home, "
          "and tell your insurer if it will be empty for more than 30 days.",
          # a pet, a plant, a boiler or a freezer is looked after differently while the house is
          # empty, and each has its own answer
          # "away" is the trip and also half of "throw away": "our house is full of stuff and i
          # cant throw anything away" was told how to make the house look lived in.
          avoid=("throw away", "throw out", "throw things", "throw stuff", "cant throw",
                 "can't throw", "cannot throw", "wont throw", "won't throw", "get rid of",
                 "declutter", "junk", "clear out", "hoard", "hoarding",
                 "cat", "dog", "pet", "pets", "fish", "hamster", "rabbit", "plants", "plant",
                 "water", "watering", "garden", "lawn", "heating", "boiler", "frost",
                 "freezing", "pipes", "fridge", "freezer", "food", "washing", "laundry",
                 "insect", "mould", "damp")),

    # The waking-up row in sleep.py keys on the bare word "alarm", so every other alarm reached
    # its snooze tip: "my burglar alarm keeps going off" was told to put the alarm across the
    # room. A house alarm that fires for no reason has its own causes and its own next step.
    entry("burglar-alarm-going-off",
          (("burglar alarm", "intruder alarm", "security alarm", "alarm system", "house alarm",
            "home alarm", "alarm panel", "alarm keeps going off", "alarm went off",
            "our alarm", "the alarm"),
           ("going off", "goes off", "went off", "keeps going", "keeps beeping", "beeping",
            "beeps", "chirping", "randomly", "for no reason", "in the night", "at night",
            "all the time", "again", "resetting", "reset it", "how do i reset", "turn it off",
            "silence it", "stop it", "flashing", "fault", "triggered")),
          ("Most false alarms are small and physical: a spider or a moth crawling across a sensor, "
           "a contact on a door or window that has worked loose, or a dying battery in one sensor "
           "chirping for attention. Read the event log on the panel first, because it names the "
           "zone that tripped, and check that sensor and its battery before you change anything "
           "else. The backup battery in the panel sets a fault of its own once it is years old: "
           "replace it, then reset with the code you were given. If it still fires at nothing, ring "
           "the alarm company rather than the police. If it goes off while you are in the house and "
           "someone could be inside, get out and ring 999."),
          bias=1,
          # an alarm in a car, a smoke alarm and a fire alarm all say "going off" too, and each
          # has its own answer; a cooking alarm is the smoke alarm's line, not the panel's
          avoid=("car", "cars", "van", "vans", "motorbike", "motorcycle", "scooter", "bike",
                 "bicycle", "lorry", "truck", "smoke", "smoke alarm", "carbon monoxide",
                 "fire", "fire alarm", "cook", "cooking", "cooked", "toast", "frying", "fry",
                 "hob", "oven", "grill", "burnt", "steam", "shower", "bathroom", "kettle")),
]

# --- when the household basics run out ------------------------------------
# "i have run out of washing powder" was answered with the laundry-sorting rule, "i have run out
# of toilet cleaner" with how to diagnose a loo that will not flush, and half a dozen more with
# "I'm listening". They are one question - what do I do until I shop - with a row per item,
# because the stand-in is what changes and the shape of the answer does not. The same table
# answers "we are out of X" and "i need more X", which are the same question said earlier.
RUN_OUT_WORDS = ("run out", "runs out", "ran out", "running out", "run out of", "ran out of",
                 "out of", "none left", "nothing left", "no more", "need more", "need some more",
                 "buy more", "get more", "run low", "running low", "down to my last",
                 "last one", "nearly empty")

RUN_OUT_ROWS = (
    (("washing powder", "soap powder", "laundry powder", "laundry detergent", "laundry liquid",
      "washing liquid", "washing capsules", "laundry capsules", "washing detergent"),
     "A teaspoon of washing-up liquid or shampoo gets one load through: it will not foam the same "
     "and it is not for every week, but a wash now beats a sour load. A 30-wash box lasts about a "
     "month for two people, so keep a spare under the sink, and a tablespoon of powder is enough "
     "for a normal load."),
    (("kitchen roll", "kitchen towel", "kitchen towels", "paper towel", "paper towels",
      "kitchen paper"),
     "A tea towel and a pile of old cloths do the same job, and newspaper is better than either "
     "for glass and windows. Buy a four-pack and keep one roll back; a roll lasts about a week in "
     "a busy kitchen, and the blue shop towels are the ones worth the extra for grease."),
    (("tin foil", "foil", "aluminium foil", "silver foil"),
     "Baking paper on a tray, and a lid or an upturned plate over a dish, cover most of what foil "
     "does; for the grill, oil the rack and slide a tray underneath. A 30cm roll lasts a couple of "
     "months, and a wide catering roll is cheaper by the metre if you use it for roasting."),
    (("cling film", "clingfilm", "plastic wrap", "saran wrap", "shrink wrap"),
     "A plate on top of a bowl, foil, or a saucepan lid covers most things, a freezer bag does "
     "instead in the freezer, and a shower cap over a bowl is the trick that works in the fridge. "
     "Beeswax wraps are the reusable version and last about a year, so they pay for themselves."),
    (("dishwasher tablets", "dishwasher tablet", "dishwasher powder", "dishwasher salt",
      "rinse aid"),
     "Two tablespoons of soda crystals on a hot empty cycle cleans the machine, and most of the UK "
     "has water soft enough to skip the salt for a week. A splash of white vinegar stands in for "
     "rinse aid, and half a tablet does a normal wash in a soft-water area."),
    (("toilet roll", "toilet rolls", "loo roll", "toilet paper", "bog roll"),
     "Kitchen roll or tissues will get you through a day, and neither belongs down the loo in a "
     "handful - paper and water are the only things that should go in. Two people use three or "
     "four rolls a week, so buy the big pack and keep one under the stairs."),
    (("bin bags", "bin bag", "bin liners", "bin liner", "rubbish bags", "black bags"),
     "A carrier bag, or the bag out of a cereal box, lines a kitchen bin for a day: double it if "
     "the rubbish is heavy and keep food waste in its own bag so it cannot split. A roll of 20 "
     "lasts about two months, and the next size up holds a week of kitchen rubbish."),
    (("washing up liquid", "washing-up liquid", "dish soap", "dishwashing liquid", "fairy liquid"),
     "A squirt of hand soap or shampoo in hot water will do a sink of dishes, and a spoon of soda "
     "crystals cuts grease better than either; never put dishwasher tablets in a bowl of washing "
     "up. A 500ml bottle lasts about two months of daily washing up."),
    (("bleach", "toilet cleaner", "loo cleaner", "disinfectant", "harpic", "domestos"),
     "A tablespoon of soda crystals left in the loo overnight and a scrub with the brush does the "
     "same job, and washing-up liquid with hot water does a basin or a floor. Never mix bleach "
     "with vinegar or with a limescale remover: the gas that comes off is what hurts people. Thin "
     "bleach is the cheap one - buy two litres at a time."),
    (("shampoo", "shampoos", "conditioner"),
     "A bar of soap washes hair for a few days, and a spoon of bicarbonate of soda stirred into a "
     "mug of warm water is the old stand-in; expect it to feel rough without conditioner. A 400ml "
     "bottle lasts about two months at three washes a week, so a spare is worth keeping."),
    (("toothpaste", "tooth paste"),
     "Brush with water alone for a day or two: it still lifts the film off the teeth and washes "
     "the sugar away, and keep flossing until you shop. A pea-sized amount means a 100ml tube "
     "lasts about two months at twice a day."),
    (("soap", "hand soap", "bar soap", "handwash", "hand wash"),
     "Washing-up liquid or shower gel does the job at a sink for a few days, and a spoon of soda "
     "crystals in warm water is the cheap hand wash. A bar lasts about a month in a busy bathroom, "
     "and bars work out cheaper than pumps per wash."),
)


def _run_out_basics(memory, understood):
    """The row for the household thing the line has run out of, or None when it names none."""
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join(str(part) for part in (
        reading.get("clean"), reading.get("text"), " ".join(reading.get("words") or ()))).lower()
    best, longest = None, -1
    for names, reply in RUN_OUT_ROWS:
        for name in names:
            if len(name) > longest and re.search(r"\b" + re.escape(name) + r"\b", said):
                best, longest = reply, len(name)
    return best


ENTRIES.append(entry(
    "run-out-basics",
    (("washing powder", "soap powder", "laundry powder", "laundry detergent", "laundry liquid",
      "washing liquid", "washing capsules", "laundry capsules", "washing detergent", "kitchen roll",
      "kitchen towel", "kitchen towels", "paper towel", "paper towels", "kitchen paper", "tin foil",
      "foil", "aluminium foil", "silver foil", "cling film", "clingfilm", "plastic wrap",
      "saran wrap", "shrink wrap", "dishwasher tablets", "dishwasher tablet", "dishwasher powder",
      "dishwasher salt", "rinse aid", "toilet roll", "toilet rolls", "loo roll", "toilet paper",
      "bog roll", "bin bags", "bin bag", "bin liners", "bin liner", "rubbish bags", "black bags",
      "washing up liquid", "washing-up liquid", "dish soap", "dishwashing liquid", "fairy liquid",
      "bleach", "toilet cleaner", "loo cleaner", "disinfectant", "harpic", "domestos", "shampoo",
      "shampoos", "conditioner", "toothpaste", "tooth paste", "soap", "hand soap", "bar soap",
      "handwash", "hand wash"),
     RUN_OUT_WORDS),
    _run_out_basics,
    # getting the stuff *off* something is a cleaning question with its own method, and the same
    # nouns sit in both: "how do i get soap out of my eye" is not a shopping line.
    # Every word here is one of the things you get the stuff *off*, and none of them can be part
    # of the line this entry does answer: "toilet", "dishwasher" and "sink" are in the key's own
    # items, so they cannot stand in an avoid list without cancelling it.
    avoid=("eye", "eyes", "hair", "mouth", "swallowed", "swallow", "skin", "face", "hands",
           "stain", "stains", "carpet", "sofa", "shirt", "shirts", "duvet", "mattress",
           "recipe", "cake", "bake", "baking", "burnt", "grease"),
    # the running-out words have to be there: "how do i use washing powder in the dishwasher" and
    # "which bleach is best" are different questions.
    ask=RUN_OUT_WORDS))


ENTRIES.append(entry(
    "air-fryer-fault",
    (("air fryer", "airfryer", "air-fryer", "actifry", "ninja foodi"),
     # a fault report, not "how long do chips take": the cooking-times question names a food and
     # a number of minutes, and this entry answers the machine that will not do its job
     ("not heating", "isnt heating", "isn't heating", "not heating up", "heating up", "no heat",
      "wont heat", "won't heat", "wont turn on", "won't turn on", "not turning on",
      "wont switch on", "won't switch on", "stopped working", "not working", "broken",
      "fuse", "fuses", "trips", "tripping", "smoking", "smoke", "sparking", "sparks",
      "error", "fault", "reset", "dead", "drawer wont", "drawer won't", "basket wont",
      "basket won't", "wont close", "won't close",
      "smell", "smells", "smelling", "stink", "stinks", "plastic", "chemical")),
    "Unplug it and take the basket out first: most air fryers will not heat with the basket or "
    "drawer not clicked fully home, and a few reset when you open and shut the drawer. If the "
    "whole thing is dead, try another socket and check the plug's fuse. One that trips the "
    "fuse, smokes or sparks is a return, not a repair, so stop using it and ring the shop or "
    "the maker while it is still in warranty. Smoke from one that is working is usually oil or "
    "crumbs on the element - let it cool and wipe the element and the tray. A new one that "
    "smells of hot plastic settles after two or three uses: run it empty at its top temperature "
    "for ten minutes with the window open.",
    # "how long do sausages take in the air fryer" and "is an air fryer worth it" both name the
    # machine and ask something else: the cooking times and the buying advice own those lines.
    # What may be put in the basket is not a fault either: "can i put plastic in an air fryer"
    # is a question about the plastic, and the "plastic" in the key below is there for the smell
    # of it burning. The shapes that ask what may go in stand this one down.
    avoid=("how long", "minutes", "temperature", "degrees", "recipe", "recipes", "chips",
           "chicken", "wedges", "roast", "cook", "cooking", "worth", "buy", "buying", "oven",
           "can i put", "can you put", "could i put", "can i use", "is it safe", "safe to put",
           "ok to put", "okay to put", "fine to put", "go in", "goes in", "put it in",
           "put in an air fryer", "put in the air fryer", "put in my air fryer",
           "put in a air fryer"),
    # the dinner-ideas table scores the same on "my air fryer is smoking"; a machine that is
    # broken is the question that needs answering, so this one goes first, well clear of the
    # meal-ideas table that also keys the words "air fryer"
    bias=4))
# --- the thing on the worktop has stopped working -----------------------
# "my kettle broke" got the energy-tariff answer, because the money state was keyed on the bare
# verb "broke" and "my" turned it into a possession (fixed in money.py). Once that was right,
# nothing owned the line at all and it fell to a listening turn: a kettle that will not boil is
# an everyday line, and the answer is what to check first and who owes you the repair.
#
# Two words have to be in the line for this one: the fault and the machine. The deciding
# question ("is it worth repairing my washing machine") stays with the machine rule above, so
# every repair word is held out here, and so is every other fault that has an entry of its own
# (a leak, a smell, a fridge that is not cold) - those are the machine's own answers.
_MACHINE_FAULT = ("broke", "broken", "break", "breaks", "breaking", "breaks down",
                  "broke down", "stopped working", "packed up", "packed in", "conked out",
                  # a machine that keeps going wrong is said in the present tense: "my washing
                  # machine breaks down every month" was answered with "that's a habit now",
                  # and "my washing machine keeps breaking down" got the listening turn.
                  "breaking down", "keep breaking", "keeps breaking",
                  "keeps going wrong", "goes wrong", "going wrong",
                  "died", "dead", "given up",
                  # The everyday ways of saying a machine is on its way out. `_machine_broke` asks
                  # for a fault word in the line before "gone" can be read as one, so a phrasing
                  # that says the fault in its own words has to be here or the row stands down:
                  # "my washing machine is on the blink" lost its card to the generic one.
                  "on the blink", "blinking", "knackered", "acting up", "playing up",
                  "on its way out", "gone wrong",
                  # "my kettle has gone", "my washing machine has gone and its not a year old",
                  # "the seal on my fridge door has gone": the everyday way of saying a thing has
                  # stopped, and it was the colour-run row ("rewash the ruined whites") or a
                  # shrug. The two words are looked at again in `_machine_broke` below, because
                  # "gone black" and "gone off" are a picture and a smell, not a fault.
                  "gone", "went",
                  "wont turn on", "won t turn on", "wont switch on",
                  "won t switch on", "wont start", "won t start", "wont come on", "won t come on",
                  "isnt working", "isn t working", "not working", "faulty", "kaput", "stopped",
                  "no power", "just stopped",
                  # "how do i fix my fridge" asks for the same first checks as "my fridge is
                  # broken": the fault is not named, so the answer is what to check before you
                  # pay anyone, and it was the search hedge on every one of the machines here.
                  # Only the help shapes are keyed, because the deciding shapes ("worth fixing",
                  # "fix or replace", "how much to fix") are held out below.
                  "fix", "fixing", "fixed", "how do i fix", "how to fix", "can i fix",
                  "how do i mend", "mend",
                  # a machine a person has given up on is said as a verdict on it, not as a
                  # fault: "my toaster is rubbish" and "my kettle is useless" got a sympathetic
                  # noise and no help. The phrases carry the verb, so "the rubbish bin is full"
                  # and "a useless present" are not this row.
                  "is rubbish", "are rubbish", "is useless", "are useless", "is crap",
                  "is a dud", "is junk", "is a piece of junk", "piece of junk",
                  "is had it", "is on its way out", "on its way out",
                  # "how do i repair my washing machine" is the same question as "how do i fix
                  # it", and it was the hedge too: the word "repair" was held out below for the
                  # deciding question, and the deciding question is a shape ("is it worth
                  # repairing"), not the word.
                  "repair", "repairs", "repairing")

_MACHINE_WORDS = ("kettle", "kettles", "toaster", "toasters", "blender", "blenders",
                  "washing machine", "washing machines", "washer", "tumble dryer",
                  "tumble dryers", "dryer", "dryers", "dishwasher", "dishwashers", "fridge",
                  "fridges", "freezer", "freezers", "oven", "ovens", "cooker", "cookers",
                  "hob", "hobs", "microwave", "microwaves", "hoover", "hoovers", "vacuum",
                  "vacuum cleaner", "iron", "irons", "coffee machine", "coffee machines",
                  "appliance", "appliances", "white goods", "extractor fan", "fridge freezer")

# The decision, and the shopping around it, belongs to the machine rule, not here.
_MACHINE_DECISION = ("worth", "replacing", "replace",
                     # "fix" and "mend" are the help words now, so only the deciding shapes are
                     # held out: "is it worth fixing my washing machine" is the money rule, and
                     # "how do i fix my washing machine" is the first checks.
                     "worth fixing", "worth a fix", "worth mending", "worth a mend",
                     "fix or", "fixing or", "or fix", "or fixing", "mend or", "or mend",
                     "should i fix", "should i get it fixed", "get it fixed", "cost to fix",
                     "much to fix", "pay someone to fix", "call someone to fix",
                     "worth repairing", "worth a repair", "repair or", "repairing or",
                     "or repair", "or repairing", "should i repair", "cost to repair",
                     "much to repair", "pay to repair", "pay someone to repair",
                     # "my washing machine breaks down every month" is a habit, not a machine
                     # that is stopped now, and the card's first checks answer nothing. The
                     # phrases are spelled out rather than left as the bare words "again",
                     # "keeps" and "always": a bare avoid word stands the whole row down, and
                     # "my fridge broke again" is the commonest line of the lot.
                     "every month", "every few", "every week", "every year",
                     "keeps stopping", "keeps breaking", "keeps cutting out",
                     "keeps switching off", "always breaking", "always stops",
                     # the same habit the other way round: a machine that keeps going wrong is
                     # the machine-keeps-failing row below, not the first checks for one that
                     # has stopped dead
                     "keeps going wrong", "always goes wrong", "breaks down every",
                     "broken down every", "breaking down every", "goes wrong every",
                     "gone wrong every",
                     # who pays for it is the landlord entry's question, and the checks above
                     # are advice for the person doing it themselves
                     "landlord", "landlords", "landlady", "letting agent", "tenant", "tenants",
                     "council", "housing association",
                     "or a new one", "engineer", "engineers", "quote",
                     "quotes", "call out", "callout", "scrap", "new one", "buy a new",
                     "buying a new", "guarantee", "warranty", "receipt", "consumer rights",
                     # the machine's own fault entries
                     "leak", "leaks", "leaking", "smell", "smells", "smelly", "noisy", "noise",
                     "rattling", "banging", "grinding", "sparking", "not cold", "not freezing",
                     "icing", "iced up", "not draining", "not spinning", "wont spin", "wont drain",
                     "not heating", "not drying", "takes ages", "error", "blocked", "clogged",
                     "scale", "scaled", "limescale", "descaling", "descale", "flu",
                     # a machine that trips the electric is the tripping entry's question, and
                     # the fix there is the socket rather than the fuse in the plug, which is the
                     # opposite advice: that entry keeps the line.
                     "trips", "tripping", "tripped", "electric", "electrics", "electricity",
                     "rcd", "breaker", "fuse box", "power",
                     # static and cling are not a machine that has stopped: "how do i stop static
                     # in the tumble dryer" is the dryer-sheet answer, and this row answered it
                     # with the plug fuse and the door switch
                     "static", "crackle", "crackles", "crackling", "cling", "clings", "clinging",
                     "shock", "shocks", "zap", "zaps",
                     # not a machine on a worktop
                     "car", "van", "mot", "phone", "laptop", "computer", "glasses", "tv",
                     "television", "boiler", "radiator", "heating", "light", "lights", "plug",
                     "socket", "fuse", "washing line", "drum",
                     # "how do i iron a shirt" and "ironing board" are not a broken appliance;
                     # the loose forms of "ironing" reach "iron", so the word is left out here
                     "ironing board", "ironing a", "crease", "creases",
                     # A line that names the part is the part's own entry, not the first checks:
                     # "how do i fix the door on my washing machine" is the door lock and "how do
                     # i fix the drain on my washing machine" is the filter behind the kick plate,
                     # and the generic answer took both of them. The part words stand the generic
                     # down, the same way the deciding shapes above do. Filter and seal already
                     # reach their own cards; they are here so the next part word cannot break in
                     # the same way.
                     "door", "doors", "drain", "drains", "pump", "pumps", "belt", "belts",
                     "ice maker", "ice-maker", "icemaker", "element", "element failed",
                     "thermostat", "hinge", "hinges", "seal", "seals", "filter", "filters")


# The words that make a stopped fridge a food question rather than a repair question. Every one
# of them has an answer of its own in health.py or home.py already.
_COLD_STOP = re.compile(
    r"\b(food|foods|still safe|safe to eat|safe to keep|thawed|thawing|went off|gone off|"
    r"keep|keeping|throw out|threw out|temperature|stopped working|has stopped|not working|"
    r"not cold|cold enough|seal|smell|door left open|off overnight)\b")


# A fridge is where a dough or a starter lives, not the thing that has gone wrong: "my starter
# stopped bubbling after i moved it to the fridge" is a loaf question, and it was answered with
# the plug fuse, the wall switch and the door seal because "fridge" is an appliance and "stopped"
# is a fault. The kitchen has its own answer for each of these, so a bread or a ferment in the
# line takes it away from the white goods.
_NOT_A_MACHINE = (
    "starter", "starters", "sourdough", "levain", "dough", "doughs", "batter", "sponge",
    "yeast", "bread", "breads", "loaf", "loaves", "roll", "rolls", "boule", "batard",
    "focaccia", "brioche", "croissant", "pastry", "cake", "cakes", "bun", "buns",
    "proving", "proofing", "proved", "rise", "risen", "rising", "knead", "kneaded",
    "ferment", "fermented", "fermenting", "bubbling", "bubbles",
)


# The fault words that are not "gone"/"went", as one pattern: a line with one of these says
# what is wrong with the machine in its own words, so "gone" does not have to carry it.
_GONE_WORDS = ("gone", "went")
_OTHER_FAULT = re.compile("|".join(
    r"\b" + re.escape(word) + r"\b" for word in _MACHINE_FAULT
    if word not in _GONE_WORDS))


# A pet that got into the machine is not a load of washing. "my cat fell in the washing machine"
# was answered "Sort lights from darks, empty the pockets and close the zips" - good advice for a
# laundry question, and useless to a person whose cat is inside the drum. The animal and the
# place together make it pets.py's soak card, so the how-to-run-a-wash row stands down.
_AN_ANIMAL_IN_THE_MACHINE = re.compile(
    r"\b(?:dog|dogs|puppy|puppies|cat|cats|kitten|kittens|rabbit|rabbits|hamster|hamsters|"
    r"guinea pig|guinea pigs|ferret|ferrets|budgie|budgies|parrot|parrots|pet|pets|animal|"
    r"animals)\b[^.?!]{0,25}\b(?:in|into|inside|through|after|out of|in the|in my)\b[^.?!]{0,20}"
    r"\b(?:washing machine|washer|tumble dryer|tumbler|dryer|drum|machine)\b"
    r"|\b(?:washing machine|washer|tumble dryer|tumbler|dryer)\b[^.?!]{0,25}"
    r"\b(?:has|with|holding|holds)\b[^.?!]{0,12}\b(?:dog|dogs|cat|cats|pet|pets|animal|"
    r"animals)\b")


# A machine fault said as a symptom rather than as "broken". A washer that will not spin, that
# bangs, or that stops part way through is the same fault as one that has stopped, but these are
# not `_MACHINE_FAULT` words: that table decides which fault row answers ("my dishwasher isnt
# draining" is the dishwasher's filter, not the generic first checks), and it is read here only
# to take the line away from the rows that explain how a machine is used.
_A_SYMPTOM = re.compile("|".join(r"\b" + re.escape(word) + r"\b" for word in (
    "isnt spinning", "isn t spinning", "not spinning", "no spin", "wont spin", "won t spin",
    "wont turn", "won t turn", "banging", "bangs", "rattling", "stopped", "stops",
    "stopped mid", "stops mid", "stopped halfway", "keeps stopping", "not draining",
    "isnt draining", "isn t draining", "not heating", "isnt heating", "full of water",
    "no heat", "not filling", "isnt emptying", "not emptying", "leaking", "keeps tripping",
)))


# The ask that keeps a how-to row in play when the line also names a symptom.
_ASKS_HOW = re.compile(
    r"\bhow (?:do|can|should|would|might) (?:i|we|you)\b|\bhow to\b|\bwhat should i\b"
    r"|\bis it worth\b|\bwhere do i\b")


# A part of a person's body is washed by a person, not by a drum: "how do i wash my back" is the
# same fault as "how do i wash my hair", and the first wording that reached the laundry card was
# only one of the ways it is said. The parts are read rather than listed in the avoid tuple so
# that a part nobody has written a card for still stands the laundry row down.
_A_PART_OF_A_PERSON = re.compile(
    r"\bmy (?:own )?(?:back|legs?|feet|foot|arms?|hands?|face|hair|head|neck|chest|belly|tummy|"
    r"skin|scalp|ears?|armpits?|underarms?|bottom|bum|toes?|knees?|thighs?|shoulders?|body|"
    r"beard|teeth|mouth|eyebrows?|fingernails?|toenails?)\b")


def _not_a_machine_that_has_gone(understood):
    """Whether this is any line but "the machine has gone", which is a repair and not a how-to.

    "The washing machine has gone and its not a year old" was answered with the cycle and the
    detergent dose, because "the washing" is in the how-to-run-a-wash row's key. A thing that has
    gone is `machine-stopped`'s question, and the rows that describe how to use it stand down.
    A pet in the drum is not a load of washing either, and that card stands down for it too.
    """
    reading = understood if isinstance(understood, dict) else {}
    line = (str(reading.get("text") or "") + " " + str(reading.get("clean") or "")).lower()
    if _AN_ANIMAL_IN_THE_MACHINE.search(line):
        return False
    if _A_PART_OF_A_PERSON.search(line):
        return False
    # A fault said in its own words is a fault, not a lesson in using the machine. This guard is
    # on every row that explains how a machine is used or how long its cycle takes, and those
    # rows key and ask on the same vocabulary ("washing machine" carries "washing"), so a line
    # that only names the machine and what is wrong with it matched them and got the how-to-run-a
    # -load card. The fault words are `_MACHINE_FAULT`'s, so a new symptom added there reaches
    # every row guarded here.
    # ...and only when the line is telling you what is wrong rather than asking how to do
    # something about it: "how do i stop the washing machine banging" is a how-to question, and
    # standing this row down for it left the line to a haircut card that keys "how do i stop".
    if (_OTHER_FAULT.search(line) or _A_SYMPTOM.search(line)) and not _ASKS_HOW.search(line):
        return False
    return not the_thing_has_gone(reading)


def _machine_broke(memory, understood):
    """The machine named in the line, if this is a fault statement rather than a decision."""
    reading = understood if isinstance(understood, dict) else {}
    line = (str(reading.get("text") or "") + " " +
            str(reading.get("clean") or "")).lower()
    if any(re.search(r"\b" + word + r"\b", line) for word in _NOT_A_MACHINE):
        return ""
    # "My kettle has gone" is the same fault as "my kettle is broken", and it was a shrug.
    # "Gone" is also what a colour, a picture or the food does ("the washing machine has gone
    # quiet", "the milk has gone off"), so where the line says nothing else about the fault, the
    # word has to be the whole of what the thing did - see lookup.the_thing_has_gone.
    if not _OTHER_FAULT.search(line) and not the_thing_has_gone(reading):
        return ""
    small = _named(line, SMALL_APPLIANCES, default=None)
    # A fridge or a freezer that has stopped is a food and temperature question first: "is my
    # food still safe after the fridge broke" is what to keep and what to throw out, and "my
    # fridge stopped working" is the thermometer and the door seal. Those are their own entries,
    # so the cold appliance stands this one down whenever the line is about the food or the cold
    # rather than the fact that it will not start.
    cold = small or _named(line, WHITE_GOODS, default=None) or ""
    if ("fridge" in cold or "freezer" in cold) and _COLD_STOP.search(line):
        return ""
    # "what should i do when the internet breaks" names no appliance, and the card below can
    # only say "most machines that stop dead": it is a machine line only when the person said
    # machine or appliance themselves ("the machine that breaks every month").
    if not cold and not re.search(r"\b(machine|machines|appliance|appliances)\b", line):
        return ""
    if small:
        article = "an" if small[0] in "aeiou" else "a"
        return pick([
            "Check the fuse in the plug and the socket before anything else, because on " + article +
            " " + small + " that is what has failed nine times out of ten, then move the plug to "
            "another socket to be sure. If it is still dead, replace it: a " + small + " is not "
            "worth repairing, since the call-out costs more than a new one and the parts are not "
            "made to be swapped. Buy the next from a shop with a two-year guarantee and keep the "
            "receipt.",
            "On " + article + " " + small + " the fault is usually the fuse or the socket, so try "
            "both of those first. Past that it is not worth mending: a new " + small + " costs less "
            "than the call-out, so replace it, buy it from a shop with a two-year guarantee and "
            "keep the receipt - that guarantee is the only cover worth having on a cheap appliance.",
        ], memory)
    thing = _named(line, WHITE_GOODS, default=None)
    # A machine the tables do not know ("my coffee machine is dead") still gets the same
    # first checks, worded about "it" rather than renamed - naming it a washing machine is
    # the fault this domain keeps away from.
    label = (thing + "s") if thing else "machines"
    return pick([
        "Check the cheap things before you pay anyone: the fuse in the plug and the socket, the "
        "switch on the wall, the door shut properly, and any filter or drain it has - most " + label +
        " that will not start are one of those. If it has really "
        "failed, go to the shop you bought it from, not the maker: they owe you a repair, "
        "replacement or refund for up to six years in England and Wales (five in Scotland), and a "
        "manufacturer's guarantee is in addition to that. Get a written quote with a guarantee on "
        "the parts, and treat a repair costing more than half a new one as the signal to replace.",
        "Start with the plug fuse, the wall switch and the door or any filter: those account for "
        "most " + label + " that stop dead, and they cost nothing to check. Then ring the retailer "
        "with your receipt, because your claim is against the shop rather than the maker - up to "
        "six years in England and Wales, five in Scotland, for a repair, a replacement or a "
        "refund - and any guarantee you were given sits on top of that right. Before agreeing to "
        "work, ask for the quote in writing and for how long the parts are guaranteed.",
    ], memory)


# --- the part of the machine that failed ----------------------------------------------------
# "the belt on my washing machine snapped" was "Got it. Is there anything you'd like a hand with?"
# and "my vacuum belt keeps slipping" was "Thanks for telling me": `machine-stopped` holds its
# generic first checks out of every line that names a part, because each part was supposed to have
# its own answer, and the belt, the pump and the vacuum's brush bar did not have one. The drum that
# hums without turning and the brush bar that has stopped are the same fault in different machines,
# so one row answers them all and says which part of the answer is the machine's.
# A machine that will not drain has named the pump without saying the word: the water sitting in
# it is the pump's job. "my tumble dryer is not draining" and "the heat pump dryer is not emptying"
# were a chat nod and a radiator-valve card, and the part they are about is the same little motor
# behind the kick plate that the word "pump" reaches.
# Only the draining itself. "not emptying" was tried too and it is a different fault on a dryer:
# the water tank or the hose, which has its own answer, so it stays out of this list.
_A_DRAIN_FAULT = ("not draining", "wont drain", "won't drain", "will not drain",
                  "not draining out", "wont drain out", "won't drain out",
                  "not pumping out", "wont pump out", "won't pump out",
                  "water left in", "water sitting in", "standing water in",
                  "full of water", "water in the drum")
_MACHINE_PARTS = (("bearing", "bearings", "drum bearing", "drum bearings"),
                  ("belt", "belts", "drive belt", "drive belts", "fan belt"),
                  ("pump", "pumps", "drain pump", "waste pump") + _A_DRAIN_FAULT,
                  ("brush bar", "brushbar", "brush roll", "brushroll", "beater bar",
                   "beater bars", "roller", "rollers"))

# The kinds of dryer people name when they are choosing one, and the words that make the line a
# choice. A fault in a machine that is already there is still the part row's question.
_DRYER_KINDS = ("heat pump", "condenser", "vented")
_CHOOSING_WORDS = ("better", "best", "which", "worth", " or ", "rather", "worse", "vs",
                   "cheaper", "cheap", "expensive", "run", "running", "cost", "energy",
                   "kwh", "efficient", "efficiency")
_PUMP_FAULT = ("not drain", "won't drain", "wont drain", "will not drain", "not draining",
               "no drain", "leak", "leaking", "broken", "faulty", "stopped", "blocked",
               "clogged", "noisy", "humming", "not spinning", "error",
               # "run" and "start" are choosing words, so a machine that will not run stood this
               # row down as if the line were a comparison: "my heat pump dryer will not run" and
               # "... won't start" were told about the kinds instead of the pump (@sleek-shark,
               # #10269). A negation in front of them is a fault, not an ask about running costs.
               "not run", "won't run", "wont run", "will not run", "not running", "not start",
               "won't start", "wont start", "will not start", "not starting", "not heating",
               "not turning", "won't turn", "wont turn", "not coming on", "won't come on",
               "not drying", "won't heat", "wont heat", "not heat")

_MACHINE_PART_TEXT = {
    "bearing": (
        "A rumble or a grinding that gets louder through the spin, with black streaks round the "
        "door glass, is the drum bearing rather than the belt. Unplug it and turn the drum by "
        "hand: a gritty scrape, or a drum you can lift at the front edge, is the bearing. The part "
        "is only 10 to 20 pounds, but the drum comes out to fit it and on most machines the outer "
        "tub is sealed, so it is a two to four hour job for someone who has done one and a "
        "repairer will usually quote 100 to 200 pounds. On a machine more than six or seven years "
        "old that is more than the machine is worth, so replace it, and buy the next one with a "
        "five-year guarantee."),
    "belt": (
        "A drive belt is a rubber loop round the motor and the drum, or round the motor and the "
        "brush bar. Unplug it and take the back panel off - on most machines that is a handful of "
        "screws - and look at the belt before buying anything: a snapped one is obvious, and one "
        "that has slipped off usually looks fine and is sitting loose at the bottom. Photograph the "
        "route it takes round the pulleys, because the path is the part people get wrong. Buy the "
        "belt for your model: the rating plate is inside the door or on the back, and a parts shop "
        "matches the code for about 5 to 10 pounds. Ten minutes with a screwdriver, half an hour on "
        "a machine where the back is tight. If it is under guarantee, ring the retailer instead, "
        "because opening it yourself can void it."),
    "pump": (
        "The pump is the small motor at the bottom behind the kick plate, and it is the part that "
        "sends the water out. If the machine will not drain, empty it first through the little "
        "filter hose or the drain filter, then check the pump for hair, coins and bra wires before "
        "you buy a new one - a blocked impeller feels exactly like a dead pump. A pump for most "
        "washing machines and dishwashers is 15 to 30 pounds and comes out with two or three "
        "screws and a clip on the hoses; put a towel down, there is always water left in it."),
    "brush bar": (
        "The brush bar is turned by a small belt from the motor, so the order is: unplug it, turn "
        "the machine over and cut the hair off the bar with scissors, check the belt has not "
        "slipped or snapped, then press the reset button on the top if it has one. If the bar "
        "turns freely by hand but not when it is switched on, the belt is the usual answer; if it "
        "will not turn by hand at all, a thread or a sock is jammed round the end of it. The belt "
        "is a few pounds for your model."),
}


def _machine_part(memory, understood):
    """Which part of which machine failed, and what to do about the part."""
    reading = understood if isinstance(understood, dict) else {}
    line = " " + " ".join(str(word).lower() for word in (reading.get("words") or [])) + " "
    part = ""
    for names in _MACHINE_PARTS:
        if any(" " + name + " " in line or " " + name + "s " in line for name in names):
            part = names[0]
            break
    if not part:
        return None
    # A part on its own belongs to nothing: "my belt is broken" is a belt, "my seat belt is
    # broken" is a car, and "my water pump is broken" is a pump. The part row only answers when
    # the line says which machine the part is in, because that is the case its text is written
    # for - the model plate, the back panel, the kick plate.
    machine = (_named(line, WHITE_GOODS, default="") or
               _named(line, (("hoover", "vacuum cleaner"), ("vacuum", "vacuum cleaner"),
                             ("dyson", "vacuum cleaner"), ("henry", "vacuum cleaner"),
                             ("machine", "machine"), ("machines", "machine"),
                             ("appliance", "machine"), ("appliances", "machine")),
                      default=""))
    if not machine:
        return ""
    # A "heat pump" is a kind of dryer and it holds the word "pump", so a line that names a kind
    # of dryer is not naming a part: "is a heat pump dryer any good", "is a heat pump dryer
    # cheaper to run" and "heat pump or condenser tumble dryer" were all told about the little
    # motor behind the kick plate. The kind of machine decides nothing here - the fault does. A
    # dryer that will not drain is the drain pump's question, and so is one whose water is
    # sitting in the drum; a dryer that will not heat, or that is simply broken, is not.
    if part == "pump" and any(kind in line for kind in _DRYER_KINDS):
        rest = line
        for kind in _DRYER_KINDS:
            rest = rest.replace(kind, " ")
        said_the_pump = bool(re.search(r"\bpumps?\b", rest))
        if not said_the_pump and not any(word in line for word in _A_DRAIN_FAULT):
            return ""
    text = _MACHINE_PART_TEXT[part]
    if machine == "machine":
        text += (" The model number on the rating plate is what the parts shop needs.")
    else:
        text += (" Yours is a " + machine + ", so the model number on the rating plate is what "
                 "the parts shop needs.")
    return text


# A heat pump is not a pump, and the fence for it is in `_machine_part` where the part is read.
# It used to be a guard here, standing the row down for every line with "heat pump" in it, which
# took the fault with it: "my heat pump dryer is not draining" and "my heat pump dryer wont drain"
# became a chat nod. A heat pump dryer does have a drain pump, so the kind of machine cannot be
# the test - whether the line is choosing or faulting can, and that is what the function does.


# The washing machine already has the right answer to this: the filter behind the kick plate is
# the commonest cause and the first thing to check, and `washer-wont-drain` says so. A dryer has
# no such row, so the drain fault reaches the pump here - but a line that names a washer keeps the
# filter, which is the card a person should read first.
def _the_washers_drain_has_its_own_answer(understood):
    line = " ".join(str((understood or {}).get("clean")
                        or (understood or {}).get("text") or "").lower().split())
    if not any(word in line for word in _A_DRAIN_FAULT):
        return True
    return not ("washing machine" in line or "washer" in line)


ENTRIES.append(entry(
    "machine-part",
    (("bearing", "bearings", "drum bearing", "belt", "belts", "drive belt", "pump", "pumps",
      "drain pump", "waste pump", "brush bar",
      "brushbar", "brush roll", "brushroll", "beater bar", "beater bars", "impeller")
     + _A_DRAIN_FAULT,
     ("washing machine", "washer", "tumble dryer", "dryer", "dishwasher", "vacuum", "hoover",
      "dyson", "henry", "vacuum cleaner", "machine", "appliance", "snapped", "snaps", "slipping",
      "slipped", "slipping off", "broken", "broke", "gone", "worn", "wont turn", "won t turn",
      "stopped spinning", "stopped turning", "not spinning", "keeps slipping", "replace",
      "replacing", "change", "changing", "fit", "fitting", "drum", "spin", "spinning")),
    _machine_part,
    # A car has its own belts and the boiler and the bike are their own machines, and the part
    # that already has an answer (the filter behind the kick plate, the door lock, the element,
    # the seal) keeps it.
    avoid=("car", "cars", "van", "engine", "cam belt", "timing belt", "fan belt", "alternator",
           "motorbike", "bike", "bicycle", "boiler", "central heating", "radiator",
           "filter", "filters", "door", "doors", "seal", "seals", "element", "thermostat",
           "hose", "hoses", "leak", "leaking", "noise", "noisy", "banging", "grinding",
           "sparking", "error", "code", "worth", "replace the machine", "new machine",
           "landlord", "warranty", "guarantee", "rower", "rowers", "fan belt"),
    guard=_the_washers_drain_has_its_own_answer,
    bias=2))


# A garment that came out of a machine wrong is a question about the garment, not about the
# machine: "my wool jumper shrank in the dryer, can i fix it" was answered with the tumble
# dryer's first checks - the plug, the filter - because the line names the dryer and asks how to
# fix it. The row that knows what heat does to wool is the one that should answer.
_GARMENT_IN_THE_LINE = ("jumper", "jumpers", "sweater", "sweaters", "cardigan", "cardigans",
                        "knitwear", "wool", "woollen", "woolen", "hoodie", "hoodies", "shirt",
                        "shirts", "t-shirt", "trousers", "jeans", "dress", "dresses", "skirt", "socks", "sock", "coat", "jacket", "joggers", "leggings")

ENTRIES.append(entry(
    "machine-stopped",
    (_MACHINE_FAULT, _MACHINE_WORDS),
    _machine_broke,
    # ... and it stands down for the air path: a vacuum that runs but picks nothing up is the
    # hose, the bag or the filter, which is `vacuum-suction`'s answer, not the first checks.
    avoid=_MACHINE_DECISION + ("suction", "no suction", "lost suction", "picking up", "pick up",
                               "picks up", "not picking", "weak", "unclog", "unclogging",
                               "unblock", "unblocking", "clogged", "blocked", "brush bar",
                               "hose", "clogging",
                               # A machine that runs but ruins what is in it has not stopped:
                               # "how do i stop clothes shrinking in the dryer" matched "dryer"
                               # and "stopped" and got the plug and the fuse, while the shrinking
                               # answer sat one row away.
                               "shrink", "shrinks", "shrinking", "shrank", "shrunk",
                               "too small", "came out small", "comes out small", "gone small",
                               "went small", "stretched", "faded", "fading", "ruined",
                               "ruining", "ruins", "bobbled", "bobbling",
                               # Scale is not a fault either: "how do i stop my kettle furring
                               # up" matched "stop" and "kettle" and got the plug and the fuse,
                               # while `descale-kettle` sat one row away. The words are the
                               # scale ones and not the bare "scale", because a set of kitchen
                               # scales is a machine that can stop working.
                               "furred", "furring", "fur", "limescale", "descale", "descaling",
                               "descaled", "chalky", "white bits", "white flakes", "white stuff",
                               "scale in the", "scale in my", "scaling up", "scaled up",
                               ) + _GARMENT_IN_THE_LINE,
    # "what do you do when your fridge breaks" is the same fault as "my fridge has stopped":
    # "your" is how a person asks about the thing they own when they are not claiming it yet
    ask=("my", "the", "our", "your", "has", "stopped", "broke", "broken", "break", "breaks",
         "gone", "dead"),
    bias=1,
    # The answer is about the appliance, not about a dish: a line that says what it cannot
    # cook with is answered by the kitchen plan, and the check card is for the machine.
    fault=True))


# --- the machine in the shed ----------------------------------------------------------------
# "how do i clean the filter on my lawnmower" was answered with the vacuum cleaner's filter, and
# "how do i sharpen the blade on my lawnmower" with a kitchen knife on a steel. A mower is a
# machine with four parts that go wrong in a fixed order, and the order is what the answer is.
_MOWER_PETROL = ("wont start", "won t start", "not starting", "not start", "stalls", "stalling",
                 "cutting out", "smoking", "smoke", "coughing", "spluttering", "firing")
_MOWER_BLADE = ("blade", "blades", "blunt", "sharpen", "sharpening", "sharp", "cutting",
                "leaves grass", "leaves the grass", "torn grass", "uneven", "scruffy")
_MOWER_SERVICE = ("filter", "filters", "air filter", "oil", "spark plug", "sparkplug",
                  "service", "servicing", "maintenance", "winter", "wintering", "store",
                  "storing", "put away", "clean", "cleaning")
# The starter battery was the one part of a mower with no words in the row: "my ride-on mower
# battery is flat" was "I'm listening - say more if it helps", "lawnmower battery keeps going
# flat" was the phone's battery-hog card, and the row's keys only knew "wont start". A ride-on,
# a cordless mower and the question of which battery to buy are three different answers, so the
# row names the battery and the reply splits on the line.
_MOWER_CORDLESS = ("cordless", "battery mower", "battery lawnmower", "battery powered",
                   "battery-powered", "no cable", "electric mower", "robot mower",
                   "robot lawnmower", "charging")
_MOWER_BATTERY_BUY = ("which battery", "what battery", "what sort of battery",
                      "what size battery", "which mower battery", "best battery",
                      "battery do i need", "battery should i buy", "replace the battery",
                      "new battery")
_MOWER_BATTERY = ("battery", "batteries", "battery is flat", "battery flat", "battery dead",
                  "dead battery", "flat battery", "jump start", "jumping it", "charger",
                  "starter", "starter motor", "turn over", "turns over", "turning over",
                  "wont turn over", "won t turn over")


def _mower(memory, understood):
    """A mower that will not start, a blunt blade, a filter or an oil change."""
    reading = understood if isinstance(understood, dict) else {}
    said = [str(word).lower() for word in (reading.get("words") or [])]
    words = set(said)
    # in the order the line says them: the phrases below ("wont start", "cutting out") are two
    # words and sorting the list would pull them apart
    line = " " + " ".join(said) + " "
    if any(" " + phrase + " " in line for phrase in _MOWER_CORDLESS):
        return ("Let the battery come to room temperature first: a mower battery left in a cold "
                "shed or a hot car will not start charging, and most chargers flash a fault light "
                "instead. Then seat it fully in the charger and look for the charge light - if "
                "there is nothing, try the charger on another tool of the same make, which tells "
                "you whether it is the battery or the charger. One stored flat over the winter "
                "often needs two or three charge-and-run cycles before it holds again, and check "
                "the mower's safety key or handle switch is seated, because the mower will not run "
                "and often will not charge with it out.")
    if any(" " + phrase + " " in line for phrase in _MOWER_BATTERY_BUY):
        return ("Take the old battery out and match the label: 12V and the amp-hour figure (12Ah, "
                "18Ah and so on) for a ride-on, and the same shape and terminal layout, because a "
                "different case size will not fit the tray or reach the leads. About 40 to 60 "
                "pounds for a ride-on, more for one with a higher amp-hour rating, and a mower "
                "shop or a battery place will match it from the old one.")
    if words & set(_MOWER_BATTERY) or any(" " + phrase + " " in line
                                          for phrase in _MOWER_BATTERY):
        return ("Charge it first, properly: a 12V charger on a ride-on's battery for four to six "
                "hours, or overnight on a trickle setting, and clean the terminals with a wire "
                "brush and tighten them while it is off - a loose or furred terminal behaves "
                "exactly like a flat battery. If it spins over slowly and will not catch, the "
                "battery is doing its job and the fuel or the spark plug is the fault. A jump "
                "start from a car works, with the car's engine off and positive to positive, "
                "negative to negative, but a battery over three or four years old that goes flat "
                "twice is finished: a new one is about 40 to 60 pounds and it is a five-minute "
                "swap.")
    if any(" " + phrase + " " in line for phrase in _MOWER_PETROL):
        return ("Nine times in ten a petrol mower that will not start is the fuel: petrol goes off "
                "in about a month, so last autumn's half tank is the first thing to drain and "
                "replace. Then work through it in this order - the spark plug out and checked "
                "(clean it, set the gap, or fit a new one for a fiver), the air filter shaken out "
                "or washed and dried, the oil level, and the blade for a jammed stick or a build-up "
                "of wet grass under the deck, which drags the engine down and makes it stall. An "
                "electric mower that will not start is the cable, the plug fuse and the cut-out "
                "switch in the handle, in that order.")
    if any(" " + phrase + " " in line for phrase in _MOWER_BLADE):
        return ("Take the blade off - disconnect the spark plug lead first, or pull the electric "
                "one out - and file the cutting edge back to the angle it already has, about 30 to "
                "45 degrees, keeping the file flat against the bevel and taking a dozen strokes a "
                "side. A blunt blade tears grass rather than cutting it, which is what leaves white "
                "shredded tips and a lawn that yellows. Any deep nick or a bent blade means a new "
                "one, about 15 to 25 pounds, and a bent blade is also a vibration you can feel. "
                "Balance it on a nail afterwards and take a little more off the heavy side.")
    if words & {"oil", "oili"} or "change the oil" in line:
        return ("Warm the engine for five minutes so the dirt comes out with the oil, put a tray "
                "under the drain plug, tip the mower to drain it and refill with about half a litre "
                "of SAE 30 four-stroke oil to the mark on the dipstick. Once a season, or every "
                "25 hours of cutting. Four-stroke mowers take straight oil in a separate sump; a "
                "two-stroke takes a petrol-and-oil mix and has no oil to change, so check which "
                "yours is before you buy anything.")
    return ("The air filter is the part that gets missed: a foam one comes out, washes in warm "
            "soapy water, dries completely and goes back with a few drops of oil worked through "
            "it, and a paper one is tapped clean or replaced. Do it every 25 hours or whenever "
            "the grass is dusty, and change the oil once a season too - a mower that runs badly "
            "or smokes is usually a choked filter and old fuel rather than anything broken.")


ENTRIES.append(entry(
    "mower-service",
    (("lawnmower", "lawn mower", "lawnmowers", "mower", "mowers", "petrol mower",
      "hover mower", "ride on mower", "strimmer", "grass trimmer"),
     ("wont start", "won t start", "not starting", "not start", "stalls", "smoking", "blade",
      "blades", "blunt", "sharpen", "sharpening", "sharp", "cutting", "filter", "filters",
      "air filter", "oil", "spark plug", "service", "servicing", "maintenance", "clean",
      "cleaning", "leaves grass", "uneven", "store", "storing", "winter",
      # the flat battery that will not turn the engine over
      "battery", "batteries", "battery is flat", "battery flat", "flat battery", "battery dead",
      "dead battery", "jump start", "starter", "starter motor", "turn over", "turns over",
      "turning over", "charger", "charging")),
    _mower,
    # A mower's blade is not a knife, a blender's or a plane's, and the lawn itself has its own
    # rows: mowing, moss, weeds and the new lawn are all garden.py's.
    avoid=("kitchen", "knife", "knives", "chef", "chisel", "plane", "blender", "scissors",
           "shears", "hedge", "mowing", "mow the", "how often", "how short", "height",
           "moss", "weed", "weeds", "new lawn", "seed", "turf", "scalp", "lawn care",
           "car", "cars", "van", "engine oil", "chainsaw",
           # how long it lasts and whether it is worth buying are the lifespan and buying rows
           "how long", "how many years", "lifespan", "life expectancy", "worth", "buy",
           "buying", "which one", "recommend"),
    bias=3))


# --- jobs that had no row at all -----------------------------------------------------------
# "how do i paint a ceiling", "how do i tile a wall", "how do i plaster a wall", "how do i fit a
# door handle", "how do i fit a toilet seat" and "how do i wire a plug" were all the search hedge
# on main, and "how do i change a light fitting" was answered with a car headlamp. Each row below
# is one job with the order to do it in and the thing that goes wrong.


ENTRIES.append(entry(
    "tile-wall",
    (("tile", "tiles", "tiling", "tiled", "splashback", "splash back", "backsplash"),
     # the ask words are out of this group on purpose: with "how" in it, every how-to that named
     # a tile was a tiling job, so "how do i screw into a tile" was given the adhesive method and
     # "how do i drill a tile" had no card of its own to reach. A tiling line says where the tiles
     # go or that it is a laying job, and that is what this group asks for.
     ("wall", "walls", "bathroom", "kitchen", "shower", "splashback", "splash back",
      "start", "starting", "first", "lay", "lay it")),
    "Mark a level line one tile up from the lowest point of the wall and work up from a batten "
    "screwed along it, because a floor is never level: the cut row goes in at the bottom last. "
    "Spread adhesive with a notched trowel over about a square metre at a time, press each tile on "
    "with a slight twist, and keep 2mm spacers between them. In a shower or round a bath use "
    "waterproof adhesive and grout, leave the grout 24 hours, then wipe the haze off with a damp "
    "sponge and seal the corners with silicone rather than grout.",
    # whitening a tile that is already on the wall is a cleaning job, not a laying one, so these
    # words keep the tiling method off a line about the tiles looking dingy
    avoid=("floor", "floors", "flooring", "grout", "grouting", "clean", "cleaning", "black",
           "mould", "lino", "laminate", "roof", "roofs", "slate", "paving", "patio", "garden",
           "remove", "removing", "drill", "hole", "loose", "cracked", "paint", "paint it",
           "whiten", "whitening", "whiter", "white again", "brighten", "brightening")))

ENTRIES.append(entry(
    "grout-tiles",
    (("grout", "grouting", "re grout", "re-grout", "regrout", "joints", "joint", "grout lines"),
     ("tile", "tiles", "tiling", "tiled", "wall", "walls", "floor", "floors", "bathroom",
      "shower", "kitchen", "splashback", "how", "do i", "apply", "put", "fill", "finish",
      "after tiling", "start", "first", "seal")),
    "Push the grout into the joints diagonally with a rubber float, a square metre at a time, "
    "pressing hard enough that the joint is full and flush - a grout bag or a gun is slower and "
    "messier on a wall. When it has firmed up, about 15 to 20 minutes, wipe the haze off with a "
    "damp sponge wrung out in clean water and change the water often, rather than wiping while it "
    "is still wet and pulling the joints open. Leave it 24 hours, buff the film off with a dry "
    "cloth, and run silicone down the corners and round the bath instead of grout, because grout "
    "cracks where two surfaces move at different rates.",
    # a joint that is already grouted and looking dingy is the cleaning row's question, and the
    # tiles coming off, the gap to leave and what it costs are three more answers of their own
    avoid=("clean", "cleaning", "cleaned", "scrub", "scrubbing", "black", "mould", "mold",
           "mouldy", "moldy", "dingy", "dirty", "stain", "stains", "stained", "whiten",
           "whitening", "white again", "brighten", "brightening", "bring back", "remove",
           "removing", "take out", "taking out", "rake out", "raking out", "loose", "cracked",
           "crumbly", "how much", "how many", "cost", "costs", "price", "bag", "bags",
           "gap", "gaps", "spacing", "how wide", "paint", "painting", "seal the", "waterproof")))

ENTRIES.append(entry(
    "sand-a-wood-floor",
    (("sand", "sanding", "sanded", "sander", "drum sander", "floor sander", "belt sander"),
     # the floor has to be named: "do i sand first or fill first" is an ordering question
     # about decorating, not a floor being taken back to bare
     ("floor", "floors", "floorboard", "floorboards", "boards", "board", "wooden floor",
      "wood floor", "wooden floors", "pine", "parquet", "back to bare", "bare wood")),
    "Punch every nail head below the surface first, because a proud nail rips the paper and one "
    "rip ruins the drum. Then hire a drum sander and an edge sander, and take the whole room in "
    "one pass per grit - 40, then 80, then 120 - moving steadily and overlapping each run by half "
    "its width, never stopping in one place, because a sander left standing burns a dip into the "
    "board. Vacuum between grits and do not skip the 120, which is the grit that takes the "
    "scratch marks out; finish with three coats of floor varnish or two of hard wax oil, "
    "de-nibbing lightly between coats.",
    # sand is a beach and a sandwich before it is a sander, and a floor that is dirty, sticky or
    # already varnished is three other rows
    avoid=("beach", "beaches", "sandpit", "sand pit", "castle", "castles", "sandwich",
           "sandwiches", "desert", "sea", "seaside", "kids", "child", "children", "toddler",
           "clean", "cleaning", "polish", "polishing", "varnish", "varnishing", "oiling",
           "sticky", "squeak", "squeaking", "creaks", "creaking", "gap", "gaps", "draught",
           "how much", "cost", "price", "hire cost",
           # and the paper is a different question from the machine
           "sandpaper", "grit", "grade",
           # a door, a table or a worktop is not a floor, and the nails-and-boards method here
           # is no use on it
           "door", "doors", "table", "tables", "chair", "chairs", "furniture", "worktop",
           "worktops", "decking", "deck", "gate", "gates", "window", "windows", "stairs",
           "stair", "cabinet", "cabinets", "wardrobe", "skirting", "shelf", "shelves")))

ENTRIES.append(entry(
    "shed-base",
    (("shed", "sheds", "garden shed", "workshop shed", "summerhouse", "summer house"),
     # the base itself has to be in the line: "how do i build a shed" is standing one up, and
     # that is a different job from the ground under it
     ("base", "bases", "footing", "footings", "foundation", "foundations", "level",
      "levelling", "leveling", "sit", "ground", "concrete", "slabs", "slab", "bearers",
      "paving")),
    "Peg out the footprint with a line and dig off about 10cm, then lay 5cm of compacted "
    "hardcore under 5cm of sharp sand and stand the shed on bearers or a grid of concrete blocks "
    "at 60cm centres, rather than on slabs in the corners where it will sag - or cast a level "
    "concrete pad if the ground is soft. Check the level across both diagonals before the shed "
    "goes on, because a base that rocks twists the frame and the doors stop closing within a "
    "season. Make the base 5cm bigger than the shed each way and a little proud of the grass, so "
    "water runs away from the floor rather than into it.",
    # the shed already standing is a repair, a leak, a door that will not shut or a coat of paint
    avoid=("leak", "leaks", "leaking", "leaked", "roof", "felt", "damp", "mould", "rot", "rotten",
           "door", "doors", "window", "windows", "paint", "painting", "treat", "treatment",
           "preserver", "shelves", "shelf", "insulate", "insulation", "electric", "electricity",
           "how much", "cost", "price", "size", "big", "small", "move", "moving", "demolish",
           "take down", "remove", "buy", "planning permission", "permission",
           # standing a shed up or putting one together is not the base under it
           "put up", "putting up", "erect", "erecting", "assemble", "assembling",
           "instructions", "flat pack", "flatpack")))

ENTRIES.append(entry(
    "fit-a-cat-flap",
    (("cat flap", "cat flaps", "cat door", "pet flap", "pet door", "flap"),
     ("fit", "fitting", "install", "installing", "installed", "put", "cut", "how", "do i",
      "door", "doors", "wall", "back door", "glass", "pane", "panes", "panel")),
    "Fit it in a door rather than a wall, and take the door off its hinges first: a door that "
    "lies flat is ten minutes with a jigsaw. Mark the template at the height of the cat's belly, "
    "drill the four corners, cut between them, and screw the two halves together through the "
    "door with the tunnel trimmed to the door's thickness. Watch where the cat already pushes "
    "before you cut, keep the flap clear of any panel doing structural work, and in a double "
    "glazed door use a glazier - a cut pane has to be replaced, not drilled.",
    # the cat's behaviour, its litter and its food are other rows, and a flap that already leaks
    # or lets a neighbour's cat in is a fix rather than a fitting
    avoid=("litter", "litter tray", "toilet", "wet", "spray", "spraying", "scratching",
           "keeps", "keeps coming", "coming in", "neighbours cat", "neighbour's cat", "other cat",
           "keep out", "draught", "draft", "drafts", "wind", "noisy", "rattle", "rattles",
           "broken", "stuck", "jammed", "magnet", "microchip", "how much", "cost", "price",
           "best", "which", "buy", "recommend")))

ENTRIES.append(entry(
    "fit-a-washing-machine",
    (("washing machine", "washing machines", "washer", "washers", "tumble washer"),
     ("fit", "fitting", "fitted", "install", "installing", "installation", "plumb in",
      "plumbing in", "plumbed in", "connect", "connecting", "hook up", "hooking up",
      "set up", "setting up", "put in", "putting in", "new machine", "how")),
    "Take the transport bolts out of the back before the first wash: three or four long bolts hold "
    "the drum still for the lorry, and leaving them in wrecks the bearings and the drum in one "
    "spin. Water off at the valve first, then the blue fill hose onto the cold inlet with its "
    "rubber washer, hand tight plus a quarter turn, and the drain hose hooked up at 60 to 90 cm - "
    "a grey hose lying in a bowl on the floor will siphon your wash water away or flood the "
    "kitchen. Level the feet so it rocks on nothing, then run it empty on a hot wash before the "
    "first load, because new machines carry oil and dust in the drum.",
    # a machine that will not spin, leaks, smells or shows a code is a fault card, not this job
    avoid=("not spinning", "wont spin", "won't spin", "leak", "leaks", "leaking", "smell",
           "clean", "cleaning", "cleaned", "dust", "wipe", "marks", "mark", "scuff",
           "descale", "drain", "drainage",
           "smells", "smelly", "drum", "noise", "noisy", "banging", "error", "error code",
           "fault", "broken", "repair", "repairing", "fix", "fixing", "not draining",
           "draining", "blocked", "filter", "how much", "cost", "price", "buy", "buying",
           "which", "best", "review", "reviews", "should i", "shall i", "is it worth",
           "worth fixing", "or repair", "extended warranty", "insurance", "clean", "cleaning",
           "descale", "dishwasher", "washer dryer", "dryer")))

ENTRIES.append(entry(
    "fit-skirting-boards",
    (("skirting", "skirtings", "skirting board", "skirting boards", "skirting board up"),
     # no "how" in here: an ask word in a key is what put this row over "how do i make skirting
     # boards look new", and "new" is the board itself, not the job, so it is keyed with the
     # board ("new skirting") and not on its own ("look new" is a clean). "fix" was only ever
     # reaching this row through the "how" beside it, so it is here in its own right.
     ("fit", "fitting", "fitted", "fix", "fixing", "fixed", "put up", "putting up",
      "install", "installing",
      "new skirting", "new skirting board", "new skirting boards", "new board",
      "replace", "replacing", "cut", "cutting", "mitre", "joint")),
    "Fix it to the wall and never through into the floor, because the floor moves and the board "
    "will crack or come loose: plugs and screws at 600 mm centres, or grab adhesive with a screw "
    "at each end, and keep the screws 10 mm down from the top edge. The two cuts that matter are "
    "the corners, so mitre an offcut first and check it against the actual corner - internal "
    "corners can be coped instead, which is the back of the profile cut away with a coping saw so "
    "it sits over the board it meets and the joint cannot open. Mark the board in place and scribe "
    "the bottom to the floor rather than trusting the gap, prime the bare ends and the back before "
    "it goes on, then caulk the top edge and fill the screw holes.",
    # a board that is coming off, or being painted, or a height question, is another answer
    avoid=("come off", "came off", "coming off", "loose", "loose board", "falling off", "paint",
           "dust", "dusting", "wipe", "scrub", "marks", "mark", "scuff", "scuffs", "dirty",
           "painting", "painted", "white", "clean", "cleaning", "height", "how high",
           "how tall", "thickness", "how much", "cost", "price", "buy", "which", "best",
           "should i", "is it worth", "remove", "removing", "take off", "taking off",
           "floor", "flooring", "laminate", "remove", "gap under", "cover a gap")))

ENTRIES.append(entry(
    "fit-coving",
    (("coving", "cornice", "cornices", "ceiling coving", "ceiling cornice"),
     ("fit", "fitting", "fitted", "put up", "putting up", "install", "installing", "new",
      "hang", "hanging", "how", "cut", "cutting", "mitre", "fix", "fixing")),
    "Cut the mitres first, on the ceiling line and not the face, with the piece upside down and "
    "back to front in the mitre box as though it were already on the ceiling, and try every cut on "
    "an offcut before it goes near the wall. Then adhesive along both the top and the bottom edge "
    "in a zigzag, press it up onto a pencil line drawn at the coving's drop, and put a screw into "
    "the wall just under the bottom edge for the first metre until the adhesive grabs - the screw "
    "head gets filled afterwards. Long walls want a joint cut on a scarf rather than butted, and "
    "any gap at the ceiling line is caulk and paint, not more adhesive.",
    # painting, removing, or which size to buy, is not this job
    avoid=("paint", "painting", "painted", "clean", "cleaning", "dust", "wipe", "marks",
           "cracks", "cracking", "crumbly", "remove", "removing",
           "take down", "taking down", "how high", "how much", "how wide", "size", "width",
           "depth", "which", "best", "cost", "price", "buy", "buying", "should i",
           "is it worth", "ceiling rose", "picture rail", "plaster", "crack", "cracked",
           "falling off", "came off", "coming off", "loose")))

# Drilling a tile is the step that ruins the job if it goes wrong, and it had no row: "how do i
# drill into a tile" was a search hedge while "how do i drill into tiles without cracking them" was
# the no-tool table (the word "without" reads as a shortage) and "how do i drill a hole in a
# bathroom tile" was the whole-bathroom cleaning card.
ENTRIES.append(entry(
    "drill-into-a-tile",
    (("drill", "drilling", "drilled", "hole", "holes", "screw", "screws", "fix", "fixing",
      "hang", "hanging", "mount", "put up", "putting up"),
     ("tile", "tiles", "tiled", "ceramic", "porcelain", "metro tile", "wall tile", "bathroom tile",
      "kitchen tile", "splashback")),
    "Turn the hammer off and use a tile bit, or an ordinary masonry bit with the drill on rotary "
    "only: the hammer is what cracks the glaze, and porcelain wants a proper spear-point bit. Put "
    "a square of masking tape over the spot so the bit cannot skate, mark the hole through it, and "
    "start at a low speed and a shallow angle with almost no pressure until the glaze is through, "
    "then straighten up and keep a wet sponge or a squirt of water on the bit because the heat is "
    "the other thing that splits a tile. Stay at least 2 to 3 cm in from an edge or a corner, and "
    "once you are through the tile put the hammer back on for the wall behind it.",
    # a broken tile, a grubby one, the tiling itself and what a tiler costs are other answers
    avoid=("clean", "cleaning", "grout", "grouting", "mould", "mold", "limescale", "stain",
           "stains", "cracked tile", "cracked tiles", "crack", "cracks", "chipped", "chips",
           "replace", "replacing", "remove a tile", "removing a tile", "how many", "how much", "cost", "price", "buy", "buying",
           "which", "best", "should i", "is it worth", "tiler", "how long", "how thick",
           # a drill that is broken, missing or being bought is not this job either
           "broken", "not working", "wont", "won't", "stopped working", "battery", "charger",
           "which drill", "what drill should i buy")))

ENTRIES.append(entry(
    "fit-door-handle",
    (("door handle", "door handles", "handle", "handles", "door knob", "knob", "lever",
      "lever handle", "latch"),
     ("fit", "fitting", "replace", "replacing", "change", "changing", "new", "swap", "put on",
      "install", "how")),
    "Nearly every door handle is two of them on one spindle, so buy a pair and keep the spindle: "
    "unscrew the handle on each side, pull them off and the spindle comes with one of them. Measure "
    "the backset - the distance from the edge of the door to the middle of the hole - and buy a "
    "handle with the same, or the new one will not line up with the latch. Screw the new pair on "
    "with the spindle through the middle and the grub screws tightened onto it, and check the latch "
    "still clicks before you shut the door.",
    # a loose handle is a two-minute tighten, and `door-handle-loose` above has it
    avoid=("loose", "wobbly", "wobbles", "wobble", "rattles", "rattle", "spins", "spinning",
           # "handle" is also the verb for putting up with someone, so a person in the line is
           # never this entry: "how do i handle a friend who drains me" was the door-handle card
           "friend", "friends", "mate", "mates", "people", "someone", "somebody",
           "draining", "drains", "drained", "exhausting", "exhausted", "relationship",
           "fallen off", "fell off", "came off", "come off", "dropped", "stiff", "sticking",
           "squeak", "squeaking", "car", "cupboard", "drawer", "window", "oven", "fridge",
           "suitcase", "pan", "knife",
           # and when "handle" is the verb, a door word has to be said as well, or any job the
           # person is trying to handle ("how do i handle stress at work") buys a pair of them.
           # "stress" and the rest below are only examples of that, and the list was always one
           # topic short: "how do i handle a breakup" bought the handles too. So the door word is
           # asked for as well, and no list of topics has to be kept up to date.
           "stress", "anxious", "anxiety", "worried", "nerves", "nervous",
           "interview", "money", "kids", "children", "teenager", "toddler",
           # "handle" is a verb as often as a noun: "how do i handle a cheeky email from a
           # colleague" and "how do i handle a rude text from my boss" were buying a pair of
           # door handles. Nothing a door handle has is written, spoken or sent.
           "email", "emails", "message", "messages", "text", "texts", "whatsapp", "reply",
           "letter", "comment", "colleague", "colleagues", "boss", "manager", "customer",
           "rude", "cheeky", "complaint", "call", "calls",
           # and the people a job is about: "how do i handle a micromanager" was buying a pair
           # of them on one spindle, because "handle" is the verb in the line, not the noun
           "micromanager", "micromanagers", "micromanage", "micromanages", "micromanaging",
           "micromanaged", "toxic", "team lead", "team leader", "line manager", "employees",
           "staff", "staff member", "intern", "apprentice", "difficult person"),
    # The list above is the other half of the same problem: every person somebody can "handle"
    # had to be written down one at a time. The door itself, or the part of it, is what makes
    # this a job rather than a thing to handle, so that is what is asked for - "how do i handle
    # a breakup" and "how do i handle stress at work" are not door questions however they are
    # phrased.
    ask=("door", "doors", "back door", "front door", "knob", "knobs", "latch", "lever",
         "spindle")))

ENTRIES.append(entry(
    "plaster-wall",
    (("plaster", "plastering", "skim", "skimming", "render", "rendering"),
     ("wall", "walls", "ceiling", "room", "how", "patch", "hole", "do i", "learn", "myself")),
    "A patch is a DIY job and a whole wall is not: for anything over a square metre get a "
    "plasterer, because the finish is all in the timing. For a patch, scrape it back to sound "
    "plaster, wet the edges, press filler in with a wide filling knife and scrape it flat while it "
    "is still soft, then sand it once dry. A skim is two coats of multi-finish about an hour "
    "apart, each 2 to 3mm, laid on with a trowel and flattened with a wider one, then polished "
    "with a wet trowel when it starts to set - and the whole wall wants PVA or a bonding agent "
    "first, or the new plaster dries too fast and crazes.",
    # "how do i hang a picture on a plaster wall" was the plasterer's answer, because "plaster"
    # and "wall" are two key parts and the thing being hung was nobody's word. Wallpapering a
    # plaster wall is the same misread from the other side, so that is fenced too.
    avoid=("crack", "cracks", "cracked", "hole", "holes", "damp", "water", "render", "pebble",
           "dash", "outside", "external", "brick", "breeze", "block", "board", "drywall",
           "plasterboard", "fill", "filler", "screw", "fixing", "rawplug", "rawl",
           "picture", "pictures", "mirror", "mirrors", "shelf", "shelves", "bracket",
           "tv", "television", "telly", "hook", "hooks", "hang", "hanging", "hung",
           "put up", "wallpaper", "wallpapering", "papering", "lining paper",
           # "skim" is what you do to a stock as well as to a wall, and "do i need to skim
           # the scum off stock" bought a bag of multi-finish. The pot's words stand this
           # row down.
           "stock", "stocks", "broth", "carcass", "bones", "scum", "foam", "soup", "gravy")))

ENTRIES.append(entry(
    "fit-toilet-seat",
    (("toilet seat", "toilet seats", "seat", "lid", "toilet lid"),
     ("fit", "fitting", "replace", "replacing", "change", "changing", "new", "swap", "put on",
      "install", "broken", "how", "which")),
    "Measure the distance between the two hinge holes and the shape of the pan before buying, "
    "because seats come in round and oval and the holes are not all the same spacing. Most hinges "
    "are top-fixing now - a screw you turn from above with an Allen key that pulls a rubber bung "
    "tight under the rim - which is a ten-minute job. If the old one is bottom-fixing, the nuts "
    "are underneath and behind the pan, so a small spanner and a torch help; put the new seat on "
    "with the hinges level and tighten until it stops wobbling, not until it stops moving.",
    avoid=("wobble", "wobbly", "loose", "tighten", "stuck", "blocked", "running", "leak",
           "leaking", "flush", "flush not", "cistern", "seat belt", "car seat", "bike seat",
           "chair", "garden", "bench")))

# A toilet being swapped for a new one is a plumbing job with an order to it, and it had no row:
# "how do i replace a toilet" was answered with the constipation card and "i need to replace my
# toilet pan" with the going-often one, because both health rows key on the word "toilet" and
# neither had a word for the job. The china, the wax seal and the two connectors are this row's;
# a loo that leaks, runs or will not flush is the fault rows above, and a seat is its own row.
ENTRIES.append(entry(
    "fit-a-toilet",
    (("toilet", "toilets", "loo", "loos", "bog", "wc", "pan", "cistern", "toilet pan",
      "toilet suite", "close coupled"),
     ("replace", "replacing", "replacement", "fit", "fitting", "install", "installing",
      "swap", "swapping", "change", "changing", "new", "remove", "removing", "take out",
      "taking out", "put in", "putting in", "how", "myself")),
    "Turn the water off at the isolation valve, flush to empty the cistern and sponge out what is "
    "left, then undo the nuts on the water connector and the two screws holding the pan to the "
    "floor. Lift the pan out with a bag over the outlet, because there is always water in the "
    "trap, and scrape the old seal off the waste pipe. The pan connector and the flexible water "
    "connector both get replaced with the toilet, never reused: they seal by being crushed once. "
    "Sit the cistern on the new pan before you lift it in, push the pan onto a new connector lined "
    "up square, screw it down on its own holes and tighten the water nut by hand plus a quarter "
    "turn, because a spanner on a plastic nut cracks the china.",
    # a loo that leaks, runs, will not flush or keeps blocking is the fault rows, and a seat, a
    # roll or a brush is not the pan. Everything to do with the body stays with health.py.
    avoid=("leak", "leaks", "leaking", "leaky", "drip", "drips", "dripping", "flush",
           "flushes", "flushing", "wont flush", "won't flush", "not flushing", "running", "runs",
           "keeps running", "blocked", "blockage", "blocking", "unblock", "plunger",
           "overflow", "overflowing", "hissing", "banging", "filling", "refilling",
           "topping up", "ballcock", "ball valve", "valve", "smell", "smells", "smelly",
           "seat", "seats", "lid", "roll", "rolls", "paper", "brush", "clean", "cleaning",
           "cleaner", "bleach", "limescale", "stain", "stains", "training", "trained",
           "toddler", "child", "baby", "nappy", "constipated", "constipation", "bowel", "poo",
           "wee", "peeing", "pee", "urine", "going often", "cystitis", "blood", "doctor", "gp",
           "how much", "how many", "cost", "costs", "price", "prices", "pay", "charge",
           "which one", "best", "review", "reviews", "buy", "worth it",
           # "should i replace my old toilet" is a decision, and the decision rows answer that
           # better than the method does: this row is the job once the decision is made.
           "should i", "should we", "is it worth", "worth replacing", "worth it",
           "or repair", "repair it instead")))

ENTRIES.append(entry(
    "wire-plug",
    # "how do i change a plug" is this job, and it was tying at four with the plug-fuse card
    # above and losing on the order: the phrase is the whole of the ask, and it says which job it
    # is, so it is its own key part rather than a bare "plug" that the fuse answer also covers.
    (("wire a plug", "wire the plug", "rewire a plug", "plug", "plug top", "13 amp plug",
      "change a plug", "change the plug", "changing a plug", "fit a plug", "fit a new plug",
      "fitting a plug", "put a new plug", "new plug on", "replace a plug", "replace the plug",
      "replace the plug on", "replacing a plug"),
     ("wire", "wiring", "rewire", "fit", "fitting", "change", "changing", "new", "fuse",
      "which way", "how", "replace", "replacing")),
    "Brown to the live pin marked L, blue to neutral N, green and yellow to earth E, and the cable "
    "grip clamped over the outer white sheath, not the inner cores - that clamp is what stops the "
    "wires pulling out. Strip about a centimetre, twist each core so no strand strays, and shorten "
    "the live and neutral so the earth is the last to pull tight if the cable is tugged. The fuse "
    "has to match the appliance: 3A for a lamp or a radio, 13A for a kettle or a heater. Never "
    "open a moulded plug - if it fails, cut it off and fit a new one.",
    avoid=("socket", "sockets", "extension", "adapter", "usb", "charger", "phone", "laptop",
           "tv", "printer", "car", "tow bar", "ear", "earphone", "headphone",
           # a projector is cabled to a laptop, in `projector-connect`
           "projector", "projectors", "hdmi")))

# Which fuse an appliance takes is the one part of a plug question that is not the wiring, and it
# had nothing: "which fuse for a lamp" reached a "a plumber or electrician will spot it in minutes"
# card and "what size fuse for a microwave" the same. The rating follows the appliance, so it is
# keyed on the appliance's own current rather than on the wiring words.
ENTRIES.append(entry(
    "fuse-rating",
    (("fuse", "fuses", "amp", "amps", "amperage"),
     ("which", "what size", "what amp", "what rating", "rating", "how many amp", "for a lamp",
      "for a kettle", "for a heater", "for a microwave", "for an iron", "for a tv", "for a radio",
      "should i use", "do i need", "fit", "use")),
    "The fuse is chosen for the appliance, not the plug: 3A for a lamp, a radio or anything on a "
    "thin flex, 5A for a small appliance like a TV or a music system, and 13A for a kettle, heater, "
    "iron, toaster or anything that makes heat. If the right fuse blows again straight away, the "
    "appliance itself is faulty - stop changing fuses and have it looked at.",
    # a fuse that has already blown is the plug answer, and a switch that keeps tripping is the
    # consumer unit: this row is only the rating
    bias=2,
    # Two tables key "size" and one of them is a clothes chart, so "what size fuse for a
    # microwave" reached the UK-to-EU-to-US list on the merge that added it while every other way
    # of asking ("which fuse for a kettle", "what amp fuse for a microwave") got this row. The
    # appliance named beside the word fuse is what decides it, and the chart's own lines name no
    # fuse or amp at all, so the tie goes to the rating.
    avoid=("blown", "blew", "keeps tripping", "keeps blowing", "tripped", "rcd", "breaker",
           "consumer unit", "reset", "car", "caravan", "motorhome", "wiring a plug", "wire a plug",
           "brown", "blue", "earth wire", "socket", "sockets", "extension")))

ENTRIES.append(entry(
    "ceiling-light",
    (("light fitting", "light fittings", "ceiling light", "ceiling lights", "light", "lights",
      "lampshade", "pendant", "pendant light", "chandelier", "downlight", "downlights",
      "spotlight", "spotlights", "dimmer", "light switch", "bulb", "bulbs", "light bulb",
      "lightbulb", "bayonet", "screw fitting", "edison screw", "gu10", "led"),
     ("change", "changing", "replace", "replacing", "fit", "fitting", "new", "swap", "install",
      "move", "add", "how", "wire", "wiring", "gone", "blown", "out", "not working",
      "flickering", "flicker", "keeps going", "stopped working", "dimmer switch")),
    "Turn the lighting circuit off at the consumer unit first and check the light is dead - a "
    "wall switch leaves the loop wires live. Photograph the wires at the rose: the browns "
    "that are not the switch live go in their own loop terminal, not with the others. A metal "
    "fitting must be earthed; with no earth in the ceiling, buy a double-insulated plastic one. "
    "A new fitting in a bathroom or kitchen is notifiable, so use an electrician.",
    # a car bulb is not a ceiling one: the headlight row used to answer every "change a light",
    # and it is a short, cheap answer so it also wins a tie - hence the bias as well as the avoid
    bias=2,
    # flashes in the eye are a detached retina, not a fitting: "i see flashing lights and new
    # floaters" went to this row through `lights` and `new`, and it is the floaters answer that
    # carries the same-day warning
    avoid=("car", "headlight", "headlights", "headlamp", "tail light", "brake light", "indicator",
           "number plate", "trailer", "van", "caravan",
           # "light" is in the key and "how" closes the score, so a suitcase was being wired in:
           # "how do i pack light for a week" got the consumer unit and the loop wires. Travel's
           # packing-light row has the answer, and the luggage words send the line there.
           "pack", "packing", "packed", "suitcase", "suitcases", "hand luggage", "carry on",
           "carry-on", "abroad", "holiday", "holidays", "flight", "flights", "travelling",
           "traveling", "travel", "trip", "weekend away", "for a week", "for two weeks",
           "eye", "eyes", "vision", "sight", "floater", "floaters", "in my vision", "aura",
           # "light headed" is a person's head and never a fitting, and the word "light" in it
           # was the whole of this row's score on "how do i stop feeling light headed when i
           # stand up", so that faint was answered with the consumer unit and the loop wires.
           # What a faint is belongs to the health rows; this row keeps lamps and room lights.
           "light headed", "light-headed", "lightheaded", "light headedness",
           "head rush", "head spins",
           "bulb has gone", "boiler", "pilot", "cooker", "oven", "hob", "fridge", "freezer",
           "washing machine", "tumble", "fairy", "christmas", "street", "traffic",
           # a tree, a hedge and a neighbour are not a fitting, and the neighbour-hedge-light row
           # keys the same words: "how do i stop my neighbour's tree blocking my light" and
           # "how do i stop a tree blocking my light" were answered with the consumer unit.
           # Not a bare "garden": "how do i fix a light in my garden" and "my garden light is not
           # working" are fittings, and that one word threw them to a hedge.
           "tree", "trees", "tree's", "hedge", "hedges",
           "neighbour", "neighbours", "neighbor", "neighbors", "neighbour's", "next door",
           "blocking my light", "blocks my light", "blocking the light", "daylight", "sunlight",
           "shade", "shady", "overhanging", "overhangs", "branches",
           # the physics question: "how fast does light travel" was answered with the wiring
           # card because `light` and `how` are both in this row's key and its bias is 2. A
           # speed, a year or a photon is not a fitting; the jobs this row owns are untouched.
           # "how fast" and not the bare "fast": the speed question is put that way, and a bare
           # "fast" would stand this row down for a fitting question asked in a hurry.
           "speed of light", "speed of sound", "light year", "light years", "how fast",
           "fast does light",
           # and a bag packed light is not a fitting either: "how do i pack light for a week"
           # was answered "turn the lighting circuit off at the consumer unit", which is the
           # worst kind of wrong - confident, and about a different job in the same house.
           "pack light", "packing light", "packed light", "travel light", "travelling light",
           "traveling light", "suitcase", "cabin bag", "hand luggage", "carry on", "carry-on",
           "backpack", "backpacking", "wash bag",
           # A fire is not a fitting. "how do i light the bbq", "how do i light a bonfire" and
           # "how do i light a candle safely" all read `light` and `how`, and this row's bias of
           # 2 takes them ahead of the shrug: the answer then turned the lighting circuit off at
           # the consumer unit to light a barbecue. Nothing here is a fitting, so the row stands
           # down and those lines go back to being unclaimed rather than wrong.
           "bbq", "barbecue", "bonfire", "campfire", "fire pit", "candle", "candles",
           "fireplace", "wood burner", "log burner", "stove", "fire",
           # a match is not a fitting either, and it is the same fault as the barbecue: "how do
           # i light a match" and "how do i light a match safely" read `light` and `how`, and
           # the answer turned the lighting circuit off at the consumer unit. Which matches to
           # buy and how to strike one is not this row's job, so it stands down.
           "match", "matches", "matchstick", "matchsticks", "light a match",
           "lighting a match", "light a fag", "light my cigarette", "light a cigarette",
           # and a photograph is not a fitting: "how do i get better photos in low light on my
           # phone" read `light` and `how` and was told to turn off the lighting circuit at the
           # consumer unit. Taking the picture is not the row's job, so the row stands down.
           "photo", "photos", "photograph", "photographs", "photography", "camera", "cameras",
           "picture", "pictures", "selfie", "selfies", "portrait", "low light", "dim light",
           "night shot", "in the dark",
           # a smart bulb that will not join the wifi is `smart-bulb-wont-connect`, not a fitting
           "hue", "philips hue", "smart bulb", "smart bulbs", "smart light", "smart lights",
           "smart plug", "led strip", "alexa", "google home")))


# "how do i find a good removals firm" and "what should i ask a removal firm" were both search
# hedges, while the cost of one and how to pack were already answered: what was missing is how
# to pick one, which is the question people ask before they book.
ENTRIES.append(entry(
    "choosing-a-mover",
    (("removal firm", "removal firms", "removals firm", "removals firms", "removal company",
      "removals company", "removals", "movers", "mover", "man with a van", "moving company",
      "house movers", "removals men"),
     ("choose", "choosing", "pick", "picking", "find a good", "find a", "good", "reliable",
      "reputable", "trust", "trustworthy", "cowboy", "scam", "avoid", "check", "vet",
      "recommend", "what should i ask", "what to ask", "questions", "insurance",
      "survey", "quote", "before i book", "book")),
    ("Get three firms to look round the place before they quote: an over-the-phone figure is the "
     "one that grows on the day. Check they are a British Association of Removers member and ask "
     "for goods-in-transit cover in writing, which is what pays if your sofa goes through a "
     "window; agree a fixed price rather than an hourly rate, and pay no more than a small deposit "
     "up front, never cash."),
    # how much it costs, packing for the move and the move itself are answered elsewhere, and a
    # survey of the house is not a survey of the firm
    avoid=("how much", "cost", "price", "cheap", "cheapest", "budget", "hire", "van",
           "pack", "packing", "packed", "boxes", "unpack", "first night", "what do i do first",
           "moving house", "moving in", "move out", "moving out", "do i need to tell",
           "council", "school", "doctor", "piano", "stressed", "stress", "worried")))

# --- reading a thing that is not a book ----------------------------------------------
# A craft pattern, a tape measure and a spirit level are all "how do I read a ..." lines, and
# "read" is the verb of the reading-list answers: "how do i read a knitting pattern" was a
# shrug while "how do i read a bus timetable" was a holiday read. Each row here is keyed on the
# thing that is read, so one answer covers every way of asking about it, and the reply reads the
# craft off the line rather than answering knitters with crochet.

CRAFT_KINDS = (("knit", "knitting"), ("knitting", "knitting"), ("knitted", "knitting"),
               ("purl", "knitting"), ("wool", "knitting"), ("knitting needles", "knitting"),
               ("k2tog", "knitting"), ("kfb", "knitting"), ("crochet", "crochet"),
               ("crocheting", "crochet"), ("crochet hook", "crochet"), ("sewing", "sewing"),
               ("sew", "sewing"), ("dressmaking", "sewing"), ("fabric", "sewing"),
               ("paper pattern", "sewing"), ("seam allowance", "sewing"), ("tote bag", "sewing"))


# The abbreviations people look up by name rather than by reading the key at the top of the
# pattern: a definition in the first sentence, then what it is for, because the reason a stitch
# leans or loses is what tells a beginner whether they have done it right.
KNITTING_MEANINGS = (
    ("k2tog", "k2tog means knit two stitches together as one. That loses a stitch and leans the "
              "work to the right, and it is how a jumper narrows at an armhole or a sleeve."),
    ("p2tog", "p2tog means purl two stitches together as one. It loses a stitch and, because it "
              "is purled, the lean goes the other way from k2tog."),
    ("ssk", "ssk means slip one stitch knitwise, slip the next the same way, then knit both "
            "through the back loops. It is a decrease that leans left, the mirror of k2tog."),
    ("kfb", "kfb means knit into the front of the stitch and then into the back of the same one "
            "before slipping it off. It makes two stitches out of one with no hole, which is "
            "what a thumb gusset or a raglan uses."),
    ("yarn over", "A yarn over (yo) is the yarn taken round the needle without working a stitch. "
                  "It adds a stitch and leaves the hole the pattern wants - an eyelet, a "
                  "buttonhole or a lacy edge."),
    ("psso", "psso means pass the slipped stitch over: slip one, work the next, then lift the "
             "slipped one over the stitch you just made. It loses a stitch."),
)


def _read_pattern(memory, understood):
    """The craft named in the line, so a knitter is not read the sewing answer."""
    reading = understood if isinstance(understood, dict) else {}
    line = (str(reading.get("text") or "") + " " +
            str(reading.get("clean") or "")).lower()
    kind = _named(line, CRAFT_KINDS, default="knitting")
    # An abbreviation asked about by name is a definition question, not a how-to-read question:
    # "what does k2tog mean" answered with "start with the abbreviations key" is no answer.
    meaning = _named(line, KNITTING_MEANINGS, default="")
    if meaning:
        return meaning
    if kind == "knitting" and re.search(r"\bcast(?:ing)?\s+on\b", line):
        return pick([
            "Cast on with the long tail, which is the one most patterns assume: pull out a tail "
            "about three times the width of the knitting, make a slip knot on the needle, then "
            "scoop the thumb strand through the finger strand and put that loop on the needle, "
            "over and over until you have the number the pattern asks for. Count them once at "
            "the end and, if you are one out, it matters - a stitch lost here shows up as a "
            "lop-sided edge fifty rows later.",
            "The long-tail cast on does nearly every job and gives a neat, stretchy edge: leave a "
            "tail three times the width of what you are making, knot it on, and use your thumb "
            "and finger to lift each new loop over the needle. The number you cast on is the "
            "pattern's first number, so if it lists sizes take the one you circled.",
        ], memory)
    if kind == "crochet":
        return pick([
            "Crochet reads a row at a time, but check whose stitch names the pattern uses before "
            "you start: a US single crochet is a UK double crochet and a US double is a UK "
            "treble, and most patterns online are American. Then 'ch 3, turn' starts the next "
            "row, brackets and asterisks are a repeat worked as many times as the number after "
            "them says, and the number in brackets at the end of a row is how many stitches you "
            "should have - count it, because that is what tells you a stitch went missing ten "
            "rows earlier.",
            "Work down the page one row at a time and keep the count at the end of each row: the "
            "pattern tells you how many stitches you should have, and that number is the only "
            "thing that catches a mistake before it becomes a shape. Brackets and asterisks mean "
            "repeat, a turning chain is the 'ch 1' or 'ch 3' at the start of a row, and if the "
            "stitch names look wrong for the stitch you know, it is the country: US single "
            "crochet is UK double, US double is UK treble.",
        ], memory)
    if kind == "sewing":
        return pick([
            "Circle your size on every piece before you cut anything: the pattern holds several "
            "sizes on the same lines, and the seam allowance is usually not included (1.5 cm, or "
            "5/8 inch, is printed on the envelope). Lay the pieces out with the arrow on the "
            "straight grain, match the notches, and fold the fabric wherever a piece says 'cut on "
            "the fold'. Read the instructions end to end once first - the order matters more than "
            "the sewing does.",
            "Read a paper pattern as a list of pieces and a list of steps, not as a diagram: the "
            "notches and the grain arrow line the fabric up, the same line carries every size so "
            "you trace yours with a pencil, and anything marked 'cut on the fold' is laid on a "
            "folded edge. Check the envelope for whether the seam allowance is included - it "
            "usually is not - and press each seam as you sew it, which is most of what makes the "
            "finished thing look right.",
        ], memory)
    return pick([
        "Read a knitting pattern a line at a time: the number at the start is the row. k is knit, "
        "p is purl, k2tog knits two stitches together (a decrease), kfb knits into the front and "
        "back of one (an increase) and yo is a yarn over (a hole and an increase). Brackets or "
        "asterisks are a repeat, worked as many times as the number after them says, and when a "
        "line lists sizes the first number is the smallest - circle your own before you cast on. "
        "Knit a 10 cm square in the pattern stitch first: if it comes out narrow, go up a needle "
        "size.",
        "Start with the abbreviations key, then work a row at a time from the row number. Three "
        "things trip people up: brackets with a number after them are a repeat, not a note; the "
        "sizes are stacked in the same line with the smallest first, so ring yours in pencil; and "
        "the tension at the top of the pattern is the size check, so knit a 10 cm square and "
        "change the needle rather than the pattern if it is out. k2tog loses a stitch, kfb and yo "
        "add one, and the stitch count at the end of a row should still match the pattern.",
    ], memory)


ENTRIES.append(entry(
    "read-a-craft-pattern",
    (("knitting pattern", "knitting patterns", "knitting chart", "crochet pattern",
      "crochet patterns", "sewing pattern", "sewing patterns", "dressmaking pattern",
      "paper pattern", "pattern instructions", "pattern instruction", "knitting instructions",
      "crochet instructions", "knitting abbreviations", "abbreviations in knitting",
      "k2tog", "kfb", "ssk", "psso", "p2tog", "yarn over", "stocking stitch", "garter stitch", "cast on",
      "casting on"),
     ("read", "reading", "how", "what", "mean", "means", "understand", "follow", "says",
      "start", "starting", "beginner", "size", "sizes", "needles", "needle", "hook", "yarn",
      "wool", "first", "do i")),
    _read_pattern,
    ask=("read", "reading", "how", "what", "mean", "means", "understand", "follow", "says",
         "start", "beginner", "size", "sizes", "needles", "needle", "hook", "yarn", "wool",
         "do i", "is it"),
    # a recipe is read a different way and has its own answer, and "read" is in a hundred lines
    avoid=("recipe", "recipes", "food label", "nutrition", "book", "books", "novel",
           "reading list", "holiday read", "timetable", "schedule", "map", "meter", "bank",
           "statement", "contract", "email", "letter", "report", "music", "chord", "score"),
    bias=1))

# --- the first hour of a craft -------------------------------------------------------
# Reading a pattern is covered above, and it assumes a person who has started. "how do i knit a
# scarf", "how do i knit", "how do i purl", "what size needles for a scarf" and "how do i use a
# sewing machine" had no answer at all on main `9fe4a4cc`, and "how do i knit a hat" was answered
# with advice about a strict teacher, because "hat" reaches the teacher row's "hates" by prefix.
# The start of a craft is one small thing you can finish today, so each answer gives the size, the
# stitch and the first hour rather than a course.

_A_PURL = re.compile(r"\bpurl(?:s|wise|ed|ing)?\b", re.I)
_A_SEWING_MACHINE = re.compile(r"\bsewing\s+machine\b|\bmachine\s+sewing\b", re.I)
_A_PATCH = re.compile(r"\bpatch(?:es|ing|ed)?\b", re.I)
_A_THREAD_NEEDLE = re.compile(r"\bthread(?:ing)?\s+(?:a|the)\s+needle\b|\bneedle\s+threader\b",
                              re.I)
_A_POM_POM = re.compile(r"\bpom\s?-?\s?poms?\b", re.I)
# The three jobs the first hour does not cover, and the words that name them. "how do i knit in
# the round" was answered with "Look at the digit just after the place you are keeping" (the
# arithmetic row, on the word "round"), and "how do i knit socks", "how do i join wool" and "how
# do i use circular needles" reached nothing but a search hedge.
_A_IN_THE_ROUND = re.compile(
    r"\bin\s+the\s+round\b|\bcircular\s+(?:needles?|knitting)\b|\bround\s+needles?\b|"
    r"\bmagic\s+loop\b|\bdouble[- ]pointed\b|\bdpn\b|\bknit\s+(?:a\s+)?(?:hat|jumper|"
    r"sweater|blanket|sleeve|mittens?|gloves?|cushion|cardigan)\s+in\s+the\s+round\b", re.I)
_A_A_SOCK = re.compile(r"\bsocks?\b|\btwo\s+at\s+a\s+time\b", re.I)
_A_JOIN_WOOL = re.compile(
    r"\bjoin(?:ing)?\s+(?:in\s+)?(?:a\s+)?(?:new\s+)?(?:ball|wool|yarn|skein)\b|"
    r"\bnew\s+ball\s+of\s+(?:wool|yarn)\b|\brun\s+out\s+of\s+(?:wool|yarn)\b|"
    r"\bchange\s+(?:the\s+)?colou?r\b", re.I)


_A_NEEDLE_SIZE = re.compile(
    r"\bwhat\s+(?:size|thickness|kind of|sort of)\s+(?:needles?|yarn|wool|hook)\b|"
    r"\b(?:needle|hook)\s+size\b|\bsize\s+(?:needles?|hook)\b|"
    r"\bwhich\s+(?:needles?|yarn|wool|hook)\b|\bwhat\s+(?:needles?|yarn|wool)\b|"
    r"\bhow\s+(?:thick|chunky|much)\s+(?:yarn|wool)\b", re.I)


# "what is double knit wool" and "what does aran mean" ask what a word means, and the answer to
# that is a definition, not the first hour of a scarf. The avoid list cannot carry this: an avoid
# word is matched loosely, so "whats" stood the row down for "what needles for a baby blanket".
_A_DEFINITION_ASK = re.compile(
    r"^\s*(?:what|whats|what's)\s+(?:is|are|does|do)\b|^\s*(?:what|whats)\s+does\b|"
    r"\b(?:tell me about|explain|meaning of|difference between|definition of)\b", re.I)


# "i want to start knitting" already has a good answer on main - the kit, the plain square, the
# video and the sit-and-knit group - so the row that teaches the first stitches stands down when
# the line is a wish to get into an activity rather than a question about the craft.
_A_GETTING_INTO = re.compile(
    r"\b(?:want|wanted|would like|thinking of|thinking about|keen|hoping)\s+to\s+"
    r"(?:start|begin|take\s+up|try|get\s+into|learn)\b|"
    r"\b(?:get|getting)\s+into\b|\b(?:take|taking)\s+up\b|\bbeen\s+meaning\s+to\b", re.I)


def _start_craft_applies(reading):
    """Not for a definition ("what is double knit wool") or a wish to take a craft up."""
    line = str((reading or {}).get("text") or (reading or {}).get("clean") or "")
    if _A_DEFINITION_ASK.search(line):
        return False
    return not _A_GETTING_INTO.search(line)


def _start_craft(memory, understood):
    """The first small thing that finishes today, in the craft the line names."""
    reading = understood if isinstance(understood, dict) else {}
    line = (str(reading.get("text") or "") + " " +
            str(reading.get("clean") or "")).lower()
    kind = _named(line, CRAFT_KINDS, default="knitting")
    if _A_A_SOCK.search(line):
        return pick([
            "A sock is the second project, not the first, and the reason is the heel: it is a "
            "turning point you knit back and forth on half the stitches, and nothing before it "
            "prepares you for it - but it is four small steps in order, not one hard one. For an "
            "adult sock in 4-ply, cast on 60 stitches on 2.5 mm needles, join in the round "
            "without a twist, and work 2x2 rib for 5 cm, then knit every round for 15 cm. Then "
            "the heel flap over 30 stitches for about 30 rows, turn the heel, pick up the "
            "gusset, and decrease back to 60 before the foot.",
            "Sock yarn wants nylon in it - about 75 per cent wool and 25 per cent nylon, sold as "
            "4-ply or sock yarn - because pure wool wears through at the heel inside a season, "
            "and 60 stitches on 2.5 mm needles is the usual adult size. Knit the leg in the "
            "round until it is 15 cm, then the heel: half the stitches back and forth for 30 "
            "rows, turn the heel, pick up the gusset, and decrease back to 60. Write the count "
            "down as you go, because a sock is the one thing where losing count shows.",
        ], memory)
    if _A_JOIN_WOOL.search(line):
        return pick([
            "Join a new ball at the end of a row and leave 15 cm tails: knit three or four "
            "stitches holding the old and new strands together, drop the old, and carry on. "
            "Then darn the two tails into the back of the work at the end rather than knotting "
            "them - a knot works loose in the wash and leaves a hard lump in the fabric. Same "
            "for a colour change: swap the yarn at the start of a row, and the jog where the "
            "colours meet sits at the side seam if you plan it there.",
            "The join that does not show is a spit splice on pure wool: fray the two ends, "
            "overlap them 5 cm, wet them and rub them between your palms until the fibres felt "
            "together. On anything else, leave 15 cm tails, knit a few stitches with both "
            "strands, and weave the tails in afterwards with a blunt needle. Never knot them - "
            "the knot is what comes undone and what you feel through the sole of a sock.",
        ], memory)
    if _A_IN_THE_ROUND.search(line):
        return pick([
            "Circular needles, one length that fits the job: 40 cm for a hat, 60 cm for a "
            "child's jumper, 80 cm for an adult's. Cast on the whole round at once, check the "
            "cast-on edge is not twisted before you join, put a marker at the join and knit "
            "every stitch - no turning - and you get stocking stitch without ever purling. A "
            "hat is 90 stitches on a 4 mm needle, knit for 20 cm, then decrease 10 stitches "
            "every other round until 10 are left and pull the yarn through them.",
            "The join is the only tricky moment: the cast-on edge has to run straight round "
            "without a twist in it, or the whole piece is a Mobius and you find out 10 cm in. "
            "Lay it flat on the table, line the bumps up along the inside, then knit the first "
            "stitch and put a marker there. On a 40 cm needle a hat works in one piece; for a "
            "sleeve or a jumper neck that is too small for the needle, pull a loop of cable out "
            "at the side - the magic loop - rather than buying double-pointed needles.",
        ], memory)
    if _A_SEWING_MACHINE.search(line):
        return pick([
            "Thread it in this order and it will sew: spool, the arm guide, the tension dial, "
            "the take-up lever, then the needle from front to back. Wind a bobbin, drop it in "
            "with the thread trailing to the left, and turn the handwheel towards you with the "
            "needle down to bring the bobbin thread up. Then sew on a scrap before the real "
            "thing: stitch length about 2.5 mm, the presser foot down before the pedal, and let "
            "the machine pull the fabric - pulling it bends the needle and skips stitches.",
            "The order is what matters: the spool, round the arm guide, through the tension "
            "dial, up and through the take-up lever, down to the needle, threaded front to back. "
            "Then the bobbin, wound and dropped in with its thread to the left, and one turn of "
            "the handwheel brings the bobbin thread up through the plate. Set the stitch length "
            "to 2.5 mm, put the foot down, and sew a line on scrap: if the stitches loop on the "
            "underside it is the top tension, and if it puckers the stitch is too long.",
        ], memory)
    if _A_THREAD_NEEDLE.search(line):
        return pick([
            "Cut the thread at a slant rather than straight across, wet it and pinch it flat, "
            "then push it through the eye against something white so you can see the hole. A "
            "needle threader costs pennies and does it in a second. Knot the two ends together "
            "so you are working with a double thread, and cut it to about a forearm's length - "
            "longer than that tangles and snarls with every stitch.",
            "The thread goes through the eye far more easily if it is cut at an angle and "
            "pressed flat between wet fingers, and a needle threader turns the whole thing into "
            "a two-second job. Use a length about as long as your forearm, doubled and knotted "
            "at the end, because a long thread twists, knots and wears thin before it runs out.",
        ], memory)
    if _A_POM_POM.search(line):
        return pick([
            "Cut two circles of card the size you want, each with a hole in the middle the size "
            "of a 10p piece, and wind yarn round both together until the hole is filled. Cut "
            "the yarn round the outside between the two circles, tie a long thread tight round "
            "the middle and knot it twice, then take the card away and trim it round. Tie it "
            "hard - a loose tie is the one thing that makes a pom pom fall apart.",
            "Two cardboard rings, a hole in the middle, yarn wound through the hole until it "
            "is full and the middle is closed: then cut between the rings all the way round, "
            "slip a doubled thread round the waist of the bundle, and pull it as tight as you "
            "can before you knot it. Trim it while it is still on the card if you want a tidy "
            "ball, and use a plate or a coin as the template so both rings match.",
        ], memory)
    if _A_PATCH.search(line):
        return pick([
            "Patch it from both sides: put a piece of similar-weight fabric or iron-on denim "
            "over the hole, press it with a hot iron through a damp cloth, then sew round the "
            "edge with a straight or zigzag stitch so it cannot lift. On a knee, put the patch "
            "inside and stitch the shape of the hole closed first - a patch on the outside of a "
            "knee rubs through in weeks, and on the seat it looks like a repair from the bus.",
            "The fix is a patch as close to the weight of the denim as you can find, ironed on "
            "with a hot iron through a cloth and then stitched round the edge; the stitching is "
            "what survives the washing. Put it inside the leg for a knee or a seat and outside "
            "for a rip at the hem, and stitch the frayed edges flat first so the patch has "
            "something to hold.",
        ], memory)
    if kind == "sewing":
        return pick([
            "Hand-sewing is three stitches: running stitch, in and out in an even line; back "
            "stitch, one back for every two forward, which is the one that holds a seam that "
            "takes a pull; and slip stitch, worked inside a fold so it barely shows, which is "
            "what a hem wants. Start and finish with two tiny back stitches on the spot instead "
            "of a knot, and keep the thread to a forearm's length.",
            "Learn running stitch first - in and out in an even line, which is gathering, "
            "basting and half the repairs you will ever do - then back stitch, which is the "
            "strong one and goes one stitch back for every two forward. A hem is slip stitch, "
            "worked along the inside of the fold. An iron between steps does more for how the "
            "finished thing looks than neat stitches do.",
        ], memory)
    if _A_NEEDLE_SIZE.search(line):
        return pick([
            "Match the needle to the yarn and the pattern does the rest: 4 mm for double knit, "
            "5 mm for aran, 6 mm for chunky, and the ball band prints the size that suits it. "
            "For a scarf, 5 mm with aran and 30 stitches gives about 20 cm wide, and two 100 g "
            "balls make one about 1.5 m long; a hat is 5 mm and about 80 stitches worked in the "
            "round.",
            "The ball band is the answer - it prints the needle size the yarn was made for, "
            "and 4 mm for double knit, 5 mm for aran and 6 mm for chunky are the usual. Then "
            "the pattern's tension square is the check: knit 10 cm, and change the needle rather "
            "than the pattern if the square comes out the wrong size. Thirty stitches on 5 mm is "
            "a scarf about 20 cm wide.",
        ], memory)
    if kind == "crochet":
        return pick([
            "Start with a 4 mm hook and a smooth double knit: a slip knot, then chain 12, then "
            "one double crochet into the second chain from the hook and into each chain after "
            "it, turning at the end of every row. That is a square, and the same stitch in rows "
            "is a blanket. Check which country the pattern is from before you learn its names: "
            "a US double crochet is a UK treble.",
            "A 4 mm hook, a smooth double knit and one stitch gets you going: chain 12, then "
            "double crochet into the second chain and every one after it, turn, chain one, and "
            "work back along the row. Count at the end of each row - the count is the only thing "
            "that catches a dropped stitch before it becomes a sloping edge.",
        ], memory)
    if _A_PURL.search(line):
        return pick([
            "A purl is a knit made with the yarn in front: keep the yarn towards you, put the "
            "right needle into the front of the stitch from right to left, wrap the yarn over "
            "the needle and pull the loop through to the back. Knit one and purl one and you "
            "have ribbing, which is what makes a cuff or a hat brim pull in and stay up.",
            "For a purl the yarn goes in front of the work, the needle goes into the front of "
            "the stitch from right to left, and the new loop is brought through to the back. "
            "Ribbing - knit one, purl one - is the reason to learn it: it stretches and pulls "
            "back, so it is the cuff, the neckband and the bottom of a hat.",
        ], memory)
    return pick([
        "Start with one square you can finish today: 5 mm needles and a smooth aran yarn, cast "
        "on about 30 stitches and knit every stitch of every row. That is garter stitch, it is "
        "flat and it does not curl, and 30 stitches is a scarf about 20 cm wide - two 100 g "
        "balls make one about 1.5 m long. Your tension evens out after ten rows, so the first "
        "rows looking uneven is not a mistake.",
        "The way in is the smallest finished thing: cast on 30 stitches on 5 mm needles, knit "
        "every row until it looks like a scarf, and cast off. Knit every row is garter stitch "
        "and needs no pattern at all. When a row goes wrong, undo it stitch by stitch rather "
        "than pulling it all out - a dropped stitch is easy to pick back up with a crochet hook.",
    ], memory)


ENTRIES.append(entry(
    "start-a-craft",
    (("knit", "knits", "knitting", "knitted", "purl", "purls", "purl stitch", "stockinette",
      "yarn", "wool", "crochet", "crocheting", "crochet hook", "sewing", "sew", "sewing machine",
      "patch jeans", "patch trousers", "patch denim", "thread a needle", "needle and thread",
      "pom pom", "pom pom maker", "double knit", "aran", "chunky yarn", "needles", "knitting needles"),
     ("how", "learn", "learning", "start", "starting", "first", "beginner", "teach", "show me",
      "use", "using", "do i", "can i", "should i", "tip", "tips", "easiest", "best", "simple",
      "want to", "size", "thickness", "which", "what", "way")),
    _start_craft,
    guard=_start_craft_applies,
    ask=("how", "learn", "start", "first", "beginner", "teach", "use", "using", "do i", "can i",
         "should i", "tips", "easiest", "best", "simple", "which", "what"),
    # a pattern, an abbreviation, a hole to darn, a hem and a button are each their own answer;
    # a bone knits together and a brow can be knitted, and a tight-knit family is neither
    avoid=("pattern", "patterns", "chart", "abbreviation", "abbreviations", "k2tog", "kfb",
           "ssk", "psso", "p2tog", "yarn over", "stocking stitch", "garter stitch", "cast on",
           "casting on", "darn", "darning", "hole", "holes", "ladder", "hem", "hems", "hemming",
           "button", "buttons", "zip", "bone", "bones", "fracture", "brow", "brows", "eyebrow",
           "eyebrows", "family", "community", "team", "school", "teacher", "teachers", "lesson",
           "class", "exam", "machine knitting", "knitting machine", "knitwear", "shop", "buy",
           "price", "cost", "itchy", "wool coat", "sheep", "recipe", "book", "novel",
           # a fault in the finished thing is a repair or a care question, not the start of a
           # craft: "how do i stop my knitted jumper bobbling" and "how do i stop my sewing
           # machine skipping stitches" were both taken by this row until these went in
           "bobble", "bobbles", "bobbling", "pill", "pills", "pilling", "pilled", "shrink",
           "shrunk", "shrinking", "stretch", "stretched", "stretching", "felt", "felting",
           "felted", "skip", "skips", "skipping", "skipped", "jam", "jammed", "stuck",
           "broken", "smell", "smells", "smelling", "snag", "snagged", "laddered",
           # how much of it, and where to keep it, are quantities and storage, not a first hour
           "how much", "how many", "balls", "skein", "store", "stores", "stored", "storage",
           # dyed or handspun wool, a quilted jacket, a knitting group and a pair of socks on
           # the needles are not the first hour (a sock, a circle and a join are, and they answer
           # above): a pattern's shaping, a heel turn and a dye pot are each their own job.
           "dye", "dyeing",
           "dyed", "spin", "spinning", "handspun", "leather", "quilt", "quilting",
           "keep", "keeps", "block", "blocking", "blocked",
           # a definition is the pattern row's meaning, not a lesson in starting
           "mean", "means", "meaning", "definition",
           "wash", "washing", "clean", "cleaning",
           "iron", "ironing",
           # a present for someone who knits is the gift question, not the first hour of
           # learning: "what present for a mum who loves knitting" was the cast-on lesson
           "present", "presents", "gift", "gifts"),
    bias=1))


def _read_tape(memory, understood):
    """What the marks on a tape mean, and the one thing that makes the number wrong."""
    return pick([
        "On a metric tape the big numbers are centimetres and the small marks between them are "
        "millimetres, ten to the centimetre, so three marks past the 7 is 73 mm. The imperial "
        "side runs the other way up: between two inches the longest small mark is the half, the "
        "next longest the quarter, then eighths, then sixteenths. Lay the tape flat and read it "
        "with your eye straight above the mark, and add the width of the hook if you are "
        "measuring to an outside edge.",
        "The numbers on a tape are centimetres with millimetres marked between them, and the "
        "hook at the end is loose on purpose - about a millimetre of play, so it works hooked "
        "over an edge and butted against one. For anything inside a frame or a recess, measure "
        "from the 100 mm mark instead and take 100 mm off the reading, and the hook never "
        "matters. On a ruler the zero is at the very end, so check a new ruler against a tape "
        "once: some are trimmed a millimetre short.",
    ], memory)


def _read_level(memory, understood):
    """The bubble, the check in both directions, and the check on the tool itself."""
    reading = understood if isinstance(understood, dict) else {}
    line = (str(reading.get("text") or "") + " " +
            str(reading.get("clean") or "")).lower()
    # A laser level has no bubble, so the answer that opens on the bubble is no answer to it.
    if re.search(r"\blaser\b", line):
        return pick([
            "A laser level throws a line or a dot along the wall instead of a bubble: stand it on "
            "something solid, switch it on, and wait for the line to stop blinking before you "
            "trust it - that blink is it levelling itself. Once it is steady, work to the line, "
            "and check it by turning the unit round and seeing whether the line lands in the same "
            "place; a laser that has been dropped can be a few millimetres out over a room.",
            "Set the laser on a tripod or a firm surface and give it a moment to settle - most "
            "self-level within a few degrees, and the light flashes until they have. The line is "
            "your reference at whatever height you set it, so mark both ends of a shelf from the "
            "line rather than measuring from one end, and if the room is bright, or the run is "
            "longer than about five metres, use the detector rather than your eye.",
        ], memory)
    return pick([
        "The bubble sits between the two lines when the surface is level, and if it is touching a "
        "line the surface is off by about 2 mm over a metre. Check along the shelf and then "
        "across its depth - a shelf can be level one way and tilted the other - and turn the level "
        "end for end over the same spot: if the bubble moves, the level is out, not the shelf. Use "
        "the longest one that fits, because a 600 mm level shows four times the gap a 150 mm one "
        "does on the same slope.",
        "Put the level on the surface and read the bubble: in the middle, between the two lines, "
        "is level, and the further it drifts towards a line the steeper the surface. Then test "
        "the other way across the same spot, and swap the level's ends to check the tool itself - "
        "a dropped level is out by more than the shelf is. A shelf wants to be within a couple of "
        "millimetres over its length, so mark the fixings from the level rather than trusting the "
        "wall.",
    ], memory)


# The tape and the level. Both are "how do I read a ..." lines that had no answer, and both
# answers are the same shape: what the marks mean, and the one mistake that makes the number
# wrong.
ENTRIES.append(entry(
    "read-a-tape-measure",
    # "metre rule" and "yardstick" are not here: a line naming a meter belongs to read-a-meter,
    # and a third key on "meter" in this domain takes its rarity point away from that row.
    (("tape measure", "measuring tape", "tape measurer", "ruler", "half inch",
      "measuring stick"),
     ("read", "reading", "how", "use", "what", "mean", "means", "cm", "centimetre",
      "centimetres", "centimeter", "centimeters", "mm", "inch", "inches", "measure",
      "measuring", "mark", "marks", "accurate")),
    _read_tape,
    # "measure" and "measuring" are key words here, not ask words: with them in the ask, a
    # tape that has lost its spring ("my tape measure has retracted") was answered with how to
    # read one.
    ask=("read", "reading", "how", "use", "what", "mean", "means", "do i", "is it"),
    avoid=("recipe", "book", "timetable", "label", "waist", "weight", "diet", "curtain",
           "wallpaper", "carpet", "room", "house", "floor", "shelf"),
    bias=1))

ENTRIES.append(entry(
    "use-a-spirit-level",
    (("spirit level", "spirit levels", "bubble level", "laser level", "level a shelf",
      "level the shelf", "level my shelf", "level a floor", "get it level", "make it level",
      "level it", "is it level", "the bubble", "bubble is", "bubble sits", "bubble in the"),
     ("how", "use", "read", "check", "straight", "middle", "lines", "mean", "what", "way",
      "right", "floor", "wall", "shelf", "shelves", "fence", "decking", "worktop", "picture",
      "tiles", "shed", "hang", "fit")),
    _read_level,
    ask=("how", "use", "read", "check", "what", "which", "should", "does", "do i", "is it",
         "mean", "way", "middle"),
    avoid=("a level", "a-level", "as level", "maths", "math", "game", "gaming", "level up",
           "next level", "difficulty", "sea level", "water level", "noise", "stress", "energy",
           "mood", "blood", "sugar", "health", "fitness", "skill", "grade", "exam", "course"),
    bias=1))
# A shower that leaks had no answer: shower-cold stands itself down for "leak", drain-blocked is
# about water that will not go away, and the leak rows were the tap, the toilet, the machine and
# the roof. Where the water shows is what names the part, so the reply is one question at a time.
ENTRIES.append(entry(
    "shower-leak",
    (("shower", "showers", "power shower", "electric shower", "mixer shower", "shower tray",
      "shower cubicle", "shower enclosure", "shower door", "shower screen", "shower waste",
      "shower valve", "shower unit", "shower hose"),
     ("leak", "leaks", "leaking", "leaked", "dripping", "drips", "drip", "water coming out",
      "water coming from", "coming through", "puddle", "puddles", "soaked", "wet patch",
      "damp patch", "water on the floor", "water on the ceiling", "downstairs ceiling",
      "coming out", "coming from", "coming through the", "getting wet", "went through",
      "fix", "fixing", "repair", "stop it", "seal", "reseal", "silicone", "how do i")),
    ("The place the water appears tells you the part, so find it before you buy anything. Water "
     "from under the tray, or a damp patch on the ceiling below, is the waste or the seal where "
     "the tray meets the wall: dry it, cut the old silicone out properly, redo it with a "
     "bathroom silicone and leave it 24 hours before anyone showers. Water round the door is the "
     "bottom seal strip and the vertical magnetic strip, which are cheap to replace. Water at the "
     "taps or the mixer is a worn cartridge or O-ring, or the joint behind it. A tray that is "
     "loose on its feet cracks the seal, so check it does not rock. Stop using the shower until "
     "the seal has cured, and if the ceiling below is wet, turn the water off at the stopcock and "
     "let it dry before you patch it."),
    bias=1,
    # a slow drain is not a leak, a cold shower is not a leak, and the rest are other leaks with
    # their own answers
    avoid=("blocked", "blockage", "slow to drain", "not draining", "wont drain", "doesn't drain",
           # "how do i unblock a shower drain" was told where the water comes from: the leak row
           # held the generic "how do i" and the drain row holds "unblock", so this stands down
           "unblock", "unblocking", "plunger", "drain snake", "bent wire", "clear the drain",
           "hair", "smell", "smells", "mould", "mold",
           # "unblock" and "drain" were not here, so "how do i unblock a shower drain" got the
           # leak answer: the second group holds the bare ask "how do i", and a shower plus an
           # ask was enough. A drain that will not clear is the blockage row's question.
           "unblock", "unblocking", "unclog", "unclogging", "clogged", "drain", "drains",
           "plughole", "plug hole", "drainage", "clear the drain", "hair trap",
           # a mark on the glass or the tiles is a cleaning question, not water going where it
           # should not: "how do i stop white marks on the shower glass" was told where to look
           # for a leak, because "how do i" is in this key.
           "mark", "marks", "white marks", "limescale", "scale", "cloudy", "scum", "clean",
           "cleaning", "cleaner", "grout", "tile", "tiles",
           # the adjective is the common shape of the mould question, and "mould" did not
           # catch "mouldy": "how do i stop my shower going mouldy" was told where the water
           # comes from, which is a leak, and the black sealant line the same
           "mouldy", "moldy", "mildew", "black spot", "black spots", "black mould",
           "black mold", "going black", "gone black", "turned black",
           "limescale", "descale", "clean",
           "cleaning", "cold", "not hot", "no hot water", "boiler", "radiator", "heating",
           "buy", "best", "which", "cheapest", "install", "replace a shower head",
           "shower head", "curtain", "tile a", "retile", "grout the whole",
           # chalk, not water out of place: "how do i get rid of hard water stains on the
           # shower" and the rust version were the leak diagnosis, and a hard water row owns them.
           # It is the words for the mark that fence this row, not the words for the surface:
           # "grout", "tiles" and "tiled" stood down "water coming through the tiles in my
           # shower", which is this row's own question (a reviewer's catch).
           "hard water", "scale", "scaled", "scaling", "rust", "rusty", "rust stain",
           "soap scum", "scum", "whiten the grout",
           "roof", "gutter", "toilet", "cistern", "washing machine", "dishwasher", "tap",
           "taps", "kitchen tap", "kitchen sink", "kitchen ceiling", "sink", "bath",
           "bathroom floor", "underfloor",
           # a shower running to waste is a saving question, not a leak: "how do i use less water
           # in the shower" has "shower" and "water" in it, which is this row's shape, and it was
           # told where the water from under the tray tells you the part. The household card
           # (`water-less`) answers the saving, so the words for the saving stand this row down.
           "less water", "save water", "saving water", "wasting water", "waste water",
           "water use", "water usage", "water bill", "use so much water", "shorter shower",
           "cheaper shower", "eco")))


# --- the bed, the sofa and the small wear nobody had a card for -------------
# "how do i stop my mattress sagging", "my pillows are flat", "my bed squeaks", "how do i stop my
# sofa sagging", "my curtains dont block the light" and "how do i fix a scratch on a wooden table"
# each got a greeting or a search hedge: the thing was named and the fault was named, but no row
# owned the pair. Each entry below is keyed on the thing and the fault, and stands down on the
# rows that own the stain, the cleaning and the buying decision of the same thing.

ENTRIES.append(entry(
    "mattress-sag",
    (("mattress", "mattresses"),
     ("sag", "sags", "sagging", "sagged", "dip", "dips", "dipped", "dipping", "hollow",
      "sunk", "sinking", "dented", "dent", "lumpy", "collapsed", "soft spot", "worn",
      "worn out", "body shape", "middle")),
    "Rotate it head to foot every three months, and put a 6mm plywood board over the slats if "
    "they bow: a dip is nearly always the base or the foam settling, not the springs going. Lay "
    "a broom handle across the width - a gap of more than about 2cm under your hip is a real dip, "
    "and past seven or eight years a new mattress is the cheaper answer. A topper hides a dip for "
    "a year, it does not fix it.",
    # a stain, a wash and a price are the other rows' lines, and the bed-wetting question names
    # a child rather than a worn mattress
    avoid=("stain", "stains", "stained", "spill", "spilled", "wash", "washing", "clean",
           "cleaning", "smell", "smells", "buy", "buying", "best", "which", "how much", "cost",
           "price", "cheap", "firm", "memory foam", "pocket spring", "cot", "cotbed", "crib",
           "moses", "baby", "child", "bed wetting", "wets the bed", "wee"),
    bias=1))

ENTRIES.append(entry(
    "mattress-flip",
    (("mattress", "mattresses"),
     ("flip", "flips", "flipping", "flipped", "rotate", "rotated", "rotating", "rotation",
      "turn over", "turn it over", "turning over", "two sided", "one sided", "head to foot",
      "ends to middle", "turn the mattress", "turn", "turning", "turned", "over",
      "which way up")),
    "Rotate it head to foot every three months, and only flip it if the label or the shop says it "
    "is two-sided: most modern mattresses have their comfort layer on top and are made never to be "
    "turned over. A two-sided one gets flipped and rotated on the same schedule; a pillow-top or "
    "memory-foam one is only rotated, because flipping puts the soft layer underneath.",
    avoid=("stain", "stains", "clean", "cleaning", "wash", "smell", "spill", "buy", "buying",
           "best", "price", "cost", "how much", "cheap", "cot", "cotbed", "crib", "baby",
           "child"),
    bias=1))

ENTRIES.append(entry(
    "pillow-flat",
    (("pillow", "pillows"),
     ("flat", "lumpy", "sagging", "sag", "squashed", "old", "worn", "replace", "replacement",
      "when", "new", "done", "gone", "neck", "support", "uncomfortable",
      "how long", "last", "lasts", "need replacing", "needs replacing")),
    "Fold the pillow in half and let go: one that stays folded has gone flat, which for most is "
    "after one to two years, hollowfibre sooner than foam. Buy the same loft and firmness again "
    "rather than a fancier one, and until it arrives a rolled towel under the neck end fills the "
    "gap a flat pillow leaves - two flat pillows stacked do not, they just make the head higher.",
    ask=("flat", "lumpy", "sagging", "sag", "squashed", "old", "worn", "replace", "replacement",
         "when", "done", "neck", "support", "uncomfortable", "new", "how long", "last", "lasts"),
    avoid=("best", "which", "how much", "price", "cost", "cheap", "memory foam",
           "case", "cover", "wash", "washing", "clean", "stain", "silk", "travel", "baby",
           "child", "toddler", "pregnancy", "breastfeeding"),
    bias=3))

ENTRIES.append(entry(
    "bed-squeak",
    (("bed", "beds", "bedframe", "bed frame", "headboard", "bedstead", "slat", "slats",
      "footboard"),
     ("squeak", "squeaks", "squeaking", "squeaky", "creak", "creaks", "creaking", "creaky",
      "rattle", "rattles", "wobble", "wobbles", "wobbly", "loose", "noisy", "moves")),
    "Tighten every bolt and screw on the frame and the headboard, and add a spring washer where "
    "one keeps working loose: a squeak is two surfaces rubbing, not a joint that is about to "
    "give. Where wood still rubs, work candle wax or talcum powder into the joint, and on a "
    "slatted base put a strip of felt or tape between the slats and the rail, which is where most "
    "noise comes from.",
    # a cot, a bunk and a hospital bed are other answers, a mattress fault belongs to the
    # mattress rows, and a back or a hip that hurts is a body question
    avoid=("cot", "cotbed", "crib", "moses", "bunk", "hospital", "care home", "mattress",
           "pillow", "sheet", "back", "hip", "neck", "shoulder", "when i lie", "buy", "new bed",
           "replacement", "price", "cost",
           # "should i hire a van to move my bed" is a moving line, and "moves" here means the
           # frame shifting, not a bed going to another house
           "van", "hire", "moving", "move house", "moved house", "removals", "removal firm",
           "moving out", "moving in", "pack", "boxes"),
    bias=1))

ENTRIES.append(entry(
    "sofa-sag",
    (("sofa", "sofas", "couch", "couches", "settee", "settees", "armchair", "armchairs",
      "suite", "seats", "cushion", "cushions"),
     ("sag", "sags", "sagging", "sagged", "dip", "dips", "dipped", "sunk", "sinking",
      "squashed", "flat", "collapsed", "lumpy", "worn", "gone soft", "bottoming out")),
    "Turn the seat cushions over and swap them round, then look under them: a sofa sags because "
    "the foam in the seat cushions has flattened or the webbing across the base has stretched, "
    "rarely because the frame has gone. A new seat cushion in 35kg/m3 foam costs about GBP 30 to "
    "60 and does more than anything else; stretched webbing re-tensions with a staple gun, and a "
    "10mm board under the cushion is the five-minute fix.",
    avoid=("stain", "stains", "stained", "spill", "clean", "cleaning", "wash", "smell", "smells",
           "buy", "buying", "best", "which", "how much", "price", "cost", "cheap", "leather",
           "suede", "cover", "covers", "throw"),
    bias=1))

# --- a thing that has faded, or is fading, in the sun --------------------------------
# "how do i stop my curtains fading", "how do i stop my sofa fading" and "how do i protect furniture
# from sunlight" all went to the search hedge, while "my curtains have faded in the sun" already had
# the blackout-lining answer. The ask and the thing are there in every one of them; what was missing
# was a row that reads the sun as the cause and says what to do about it.
ENTRIES.append(entry(
    "stop-fading",
    (("fading", "faded", "fade", "fades", "sun fading", "sun bleached", "sun-bleached",
      "bleached", "discoloured", "discolored", "gone pale", "lost its colour", "lost its color",
      "colour has gone", "color has gone"),
     ("curtain", "curtains", "sofa", "sofas", "couch", "settee", "rug", "rugs", "carpet",
      "carpets", "furniture", "upholstery", "cushion", "cushions", "armchair", "armchairs",
      "chairs", "floor", "flooring", "wood floor", "paintwork", "picture", "pictures",
      "blinds", "sunlight", "sun", "sunny", "window", "windows", "conservatory", "orangerie",
      "table", "shelf", "shelves"),
     ("stop", "stops", "prevent", "protect", "keep", "save", "how", "patch", "match",
      "stop it", "keep it from")),
    "The sun does the fading, so block the light rather than treat the fabric: a UV film on the "
    "glass takes out most of it for a few pounds, and a blackout or thermal lining behind the "
    "curtain does the same job - pull them across the sunny hours in summer, and the room stays "
    "cooler too. Turn sofa and chair cushions every few weeks so the fade lands evenly, move "
    "anything that sits in one spot, and keep the sun off a wooden floor with a rug in the bright "
    "patch. Once a colour has gone you cannot bring it back, so a fabric dye or a throw over the "
    "worn arm is the repair, and everything else is prevention.",
    # the wash is where clothes fade, and that row is `faded-black`'s: "how do i stop colours
    # fading in the wash" is about the machine, not the window
    avoid=("wash", "washing", "laundry", "detergent", "machine", "cycle", "spin", "dryer",
           "tumble", "clothes", "shirt", "shirts", "jeans", "tshirt", "t-shirt", "black",
           "colour-safe", "color-safe", "fabric softener", "spin cycle",
           # a lining to fit or a curtain to hang is the fitting row's question, and a blackout
           # blind that will not stay put is its own
           "lining", "blackout lining", "measure", "measuring", "how wide", "how long", "size",
           "hang", "hanging", "pole", "track", "sew", "hem", "buy", "buying", "price", "cost",
           "cheap", "which curtains", "how much"),
    # the row answers the ask to stop it happening, not the report that it already has: "my curtains
    # have faded in the sun" is the blackout-lining answer, and it is a better one than this
    ask=(("stop", "stops", "prevent", "protect", "how do i keep", "keep it from", "save",
          "how do i stop", "how to stop", "can i stop", "what stops", "anything i can do"),),
    bias=1))

ENTRIES.append(entry(
    "curtain-blocks-light",
    (("curtain", "curtains", "drapes", "blind", "blinds"),
     ("light", "light through", "block", "blocks", "blackout", "dark", "darken", "darkening",
      "daylight", "morning", "bright", "glow", "wake me", "wakes me", "sun")),
    "A blackout lining is the fix, and the fitting matters as much as the fabric: hang the track "
    "or pole 10 to 15cm above the window and run the curtains 10 to 15cm past each side, so light "
    "cannot come round the edges. The light that wakes people is usually the strip along the top, "
    "so a pelmet or a blackout blind inside the recess behind the curtains closes it for a few "
    "pounds. The same lining is what slows a bright room fading the fabric, so it earns its keep "
    "twice.",
    avoid=("measure", "measuring", "how wide", "how long", "size", "fit", "hang", "hanging",
           "buy", "buying", "best", "which", "how much", "price", "cost", "cheap", "iron",
           "wash", "cleaning", "sew", "hem", "pole", "track"),
    bias=1))

# `wood-stain` already answers a white ring, a water mark and a bloom, and it answers them with the
# mayonnaise, the hairdryer and the iron in one reply. The finish row above reaches those lines on
# the same words, and with the wood in its key it outscored the stain card for "white mark off my
# oak table": the person got three sentences about scratches first. So this row stands down when
# the line names a white or water mark and no scratch.
WHITE_ONLY = ("white mark", "white marks", "white ring", "white rings", "water mark",
              "water marks", "watermark", "watermarks", "milky", "bloom", "white stain",
              "white patch", "white patches")
SCRATCH_WORDS = ("scratch", "scratches", "scratched", "scuff", "scuffs", "scuffed", "gouge",
                 "gouges", "nick", "nicks")


def _not_only_a_white_mark(reading):
    """A white ring or a water mark on its own is the stain card's question, not the scratch."""
    reading = reading if isinstance(reading, dict) else {}
    line = str(reading.get("text") or reading.get("clean") or reading.get("plain") or "").lower()
    if any(word in line for word in SCRATCH_WORDS):
        return True
    return not any(word in line for word in WHITE_ONLY)


ENTRIES.append(entry(
    "table-scratch",
    (("table", "tables", "tabletop", "table top", "desk", "desks", "sideboard", "sideboards",
      "cabinet", "cabinets", "wardrobe", "furniture", "dresser", "bookcase",
      # the wood and not only the piece of furniture: "how do i fix a scratch in oak" and
      # "scratched veneer" named no table and reached nothing
      "wood", "wooden", "woodwork", "oak", "pine", "walnut", "mahogany", "teak", "veneer"),
     # a dent is raised with an iron (wood-dent) and a chip is a fill, so this row keeps the
     # marks that sit in the finish
     ("scratch", "scratches", "scratched", "scuff", "scuffs", "scuffed")),
    "A light scratch in the finish lifts with a walnut rubbed along the grain, or a dab of wax "
    "polish in the same shade. If a fingernail does not catch on it, the scratch is only in the "
    "finish. A white ring from a wet glass is moisture trapped in the lacquer rather than a mark "
    "in the wood: a warm iron over a cloth for a few seconds lifts it, and a deep gouge wants a "
    "wax filler stick of the right colour, not sandpaper, which takes the finish off round it.",
    # A cat that scratches the furniture is a behaviour question, not a mark in the finish:
    # "my cat scratches the furniture" and "how do i stop my cat scratching the furniture" were
    # telling the person to rub a walnut along the grain. Cat words stand this row down and
    # `pets.cat-scratching` answers it.
    avoid=("floor", "floors", "floorboard", "floorboards", "laminate", "vinyl", "worktop",
           "chopping", "cutting board", "kitchen cupboard", "buy", "buying", "best", "which",
           "price", "cost", "how much", "paint", "varnish", "car", "phone", "screen", "glasses",
           # an animal scratches what it sits on, and a walnut does not stop it: "why does my cat
           # scratch the furniture" is the scratching-post row's question (pets.py cat-scratching)
           "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies", "claw", "claws",
           "clawing", "pet", "pets", "rabbit", "hooves"),
    guard=_not_only_a_white_mark,
    bias=1))


# A chip in a mug or a plate is not a wood chip, a potato chip or a claim about a new purchase, and
# on main "how do i fix a chipped plate" was the cut-potato recipe. Nothing glues china back
# safely, so the answer is what to do with it instead.
ENTRIES.append(entry(
    "chipped-china",
    (("mug", "mugs", "cup", "cups", "plate", "plates", "bowl", "bowls", "crockery", "china",
      "teapot", "jug", "jug", "saucer", "saucers", "dish", "dishes", "tumbler", "glass",
      "glasses", "porcelain", "stoneware"),
     ("chipped", "chip", "cracked", "crack", "cracks", "crazed", "crazing")),
    "A chip in china or glass cannot be glued back safely: the glaze is gone at the chip, that "
    "spot holds bacteria and it will crack through in a dishwasher. Retire a chipped mug to a pen "
    "pot or a plant saucer, and if it was new take it back, because a chip at the rim is a fault "
    "the shop has to put right. Never use a cracked one for hot drinks.",
    # "chips" is not in here on purpose: a typed word one slip from an avoid word stands the row
    # down, and "chipped" is one slip from "chips", so the fence would take the chip in the china
    # with it. The cut-potato row fences itself off the mug words instead.
    avoid=("fries", "oven", "tooth", "teeth", "nail", "nails", "polish", "windscreen",
           "windshield", "screen", "phone", "paint", "varnish", "wood", "wooden", "floor",
           "wall", "walls", "tile", "tiles", "tiling", "toilet", "sink", "bath", "shower",
           "car", "window", "windscreen chip", "tooth is", "filling", "dentures", "brace"),
    bias=1))

# Moving a fridge and moving a washer were shrugs on main, and the two answers are not
# interchangeable: a fridge has a compressor and oil that has to settle, a washer has a drum to
# lock with its transit bolts.
ENTRIES.extend([
    # A washer is not a fridge: it has a drum to lock and hoses to empty, not a compressor to
    # settle. Two entries, so a line about one never opens with the advice for the other.
    entry("move-appliance", (("fridge", "freezer", "fridge freezer"),
                             # "lift" and "carry" are here for the journey questions ("how do
                             # i lift a washing machine into a van"), and a line that has already
                             # lifted the thing is the back card's, which carries bias=1 to win
                             # the tie: "i lifted a washing machine" is not a travel question.
                             ("move", "moving", "moved", "carry", "carrying", "lift", "lifting",
                              "upstairs", "downstairs", "shift", "van", "hire", "transport",
                              "new house", "new flat", "stairs", "up the stairs",
                              "down the stairs", "flights")),
          ("Move the fridge and freezer upright in a van or on a sack truck, never on their side "
           "for more than a few minutes, and let a fridge stand upright for 24 hours before "
           "plugging it in, or the compressor oil will not have settled back. Empty and defrost it "
           "the day before, tape the doors shut and take the shelves out. Two people and a strap "
           "beat one person and a bad back."),
          avoid=("repair", "repairs", "broken", "not working", "noisy", "smell", "leak", "leaking",
                 "frost", "pressure", "cold", "not cooling", "noise", "fix", "washing machine",
                 "washer", "tumble dryer", "dryer")),
    entry("move-washer", (("washing machine", "washer", "tumble dryer", "dryer", "washer dryer"),
                          ("move", "moving", "moved", "carry", "carrying", "lift", "lifting",
                           "upstairs", "downstairs", "shift", "van", "hire", "transport",
                           "new flat", "new house", "stairs", "up the stairs")),
          ("Put the transit bolts back in before it travels: they lock the drum, and without them "
           "the drum wrecks its own bearings on the drive. The set came with the machine and is "
           "usually still taped inside the door or under the lid; a removal firm can supply one. "
           "Turn the water off, unscrew the hoses, drain the filter behind the front flap and the "
           "water in the pump, and tape the door shut. Once it is bolted it is fine on its side for "
           "a short trip, and a tumble dryer travels upright."),
          avoid=("repair", "repairs", "broken", "not working", "noisy", "smell", "leaking",
                 "not draining", "wont drain", "error", "plumb", "plumbing", "install", "fitting",
                 "fridge", "freezer", "frost",
                 # "the washing machine moves when it spins" is the levelling row: a machine
                 # that shakes is not being taken anywhere, so the shake words stand this one
                 # down and its own "move" never reads as a removal
                 "wobble", "wobbles", "wobbly", "shaking", "shakes", "vibrating", "vibration",
                 "walking", "banging", "noisy", "noise", "spinning", "spins", "loud"),
          # "how do i move a washing machine" scores the same as the levelling row, which comes
          # first, so the bare move words reached the wobble answer. A move is the question
          # here, so this row wins the tie now that the shake words are fenced off.
          bias=2),
])


# --- the clock on the oven, and the shower head that needs replacing ------------------------
# Both are ordinary jobs a household does once and then has to look up, and both hedged:
# "how do i set the clock on my oven" and "how do i replace a shower head" were search hedges,
# while "my oven clock is wrong" was answered with how to drop the temperature for a fan oven.
ENTRIES.append(entry(
    "set-an-oven-clock",
    (("oven clock", "clock on the oven", "clock on my oven", "clock on the cooker",
      "the clock on my oven", "oven display", "oven timer", "time on the oven", "oven flashing",
      "clock keeps flashing", "clock flashing", "clock is wrong", "clock is flashing",
      "set the time on the oven", "change the time on the oven", "time on my oven",
      "time on the oven", "the time on my oven", "oven now says", "oven clock is out",
      "oven clock is wrong"),
     ("set", "setting", "change", "changing", "fix", "wrong", "reset", "resetting", "flashing",
      "puts", "put", "how", "adjust", "correct", "back", "shows", "blank")),
    ("The clock is set with the two small buttons under the display, not with the dials: hold the "
     "one with the clock symbol until the hour flashes, tap the other to move it on, press the "
     "clock button for the minutes and then leave it alone for a few seconds to lock the time in. "
     "If it is flashing '0:00' after a power cut, the oven will not heat until it knows the time, "
     "which is why setting the clock is what puts the oven back on."),
    # the temperature, the timer's own beep and a clock that is not an oven's are other answers
    avoid=("fan oven", "fan oven temperature", "temperature", "bake", "baking", "roast", "grill",
           "cook", "cooking", "how long", "heating", "element", "not heating", "fan runs",
           "microwave", "alarm clock", "clock radio", "wall clock", "watch",
           # the key holds the bare phrase "clock is wrong", so every clock in the house
           # reached the oven's: "my thermostat clock is wrong" was given the oven buttons.
           # The house's heating has its own clock, on the programmer, and these words stand
           # this row down for it.
           "thermostat", "thermostats", "boiler", "combi", "programmer", "heating programmer",
           "central heating", "the heating", "my heating", "radiator", "radiators",
           "hot water", "heating timer", "heating times"),
    ask=("set", "setting", "change", "fix", "wrong", "reset", "resetting", "flashing", "how",
         "adjust", "correct", "shows"),
    bias=2))

ENTRIES.append(entry(
    "replace-a-shower-head",
    (("shower head", "shower heads", "showerhead", "shower rose", "head on the shower",
      "new shower head", "head of the shower", "shower attachment"),
     ("replace", "replacing", "change", "changing", "fit", "fitting", "new", "swap", "remove",
      "removing", "broken", "cracked", "split", "worn", "come off", "came off", "screw off",
      "how", "which")),
    ("Unscrew the old head anticlockwise by hand - a cloth round it if it is stiff - and expect a "
     "cupful of water out of the hose. Keep the rubber washer that comes out, wrap the thread two "
     "or three turns of PTFE tape clockwise as you look at the end, and screw the new head on by "
     "hand until it is snug plus a quarter turn with a cloth; no wrench, because a plastic thread "
     "cross-threads and splits. The thread on nearly every UK shower is 1/2 inch BSP, so any head "
     "in the shop fits - but pick a low-pressure one if the shower runs off a tank in the loft "
     "rather than a combi, or the spray will collapse to a trickle."),
    # descaling, a blocked spray and a shower that loses pressure are the cleaning and fault
    # answers, and a shower curtain or a tray is not the head
    avoid=("descale", "descaled", "descaler", "limescale", "scale", "clean", "cleaning",
           "blocked", "blocking", "vinegar", "soak", "mould", "mold", "pressure", "low pressure",
           "flow", "cold", "hot water", "boiler", "pump", "leak from the pipe", "grout", "tray",
           "curtain", "screen", "door", "mixer", "valve", "tap", "shower gel", "bath",
           "shower pump", "electric shower"),
    ask=("replace", "replacing", "change", "fit", "fitting", "new", "swap", "remove", "broken",
         "cracked", "split", "worn", "come off", "how", "which"),
    bias=1))

# --- the shower curtain that clings to you --------------------------------------------------
# "how do i stop my shower curtain sticking to me" was answered with how to read a textbook,
# "the shower curtain keeps blowing in" with "Got it." and "how do i stop the shower curtain
# clinging" with a hedge: the words are all ordinary and no row owned them.
ENTRIES.append(entry(
    "shower-curtain-clinging",
    (("shower curtain", "shower curtains", "curtain in the shower", "bathroom curtain",
      "shower liner", "shower curtin", "curtain clinging", "curtain sticks", "curtain blows",
      "curtain blowing", "curtain sucks"),
     ("cling", "clinging", "clings", "stick", "sticks", "sticking", "stuck", "blow", "blows",
      "blowing", "flap", "flaps", "suck", "sucks", "billow", "keeps", "in on me", "against me",
      "stop", "how", "fix")),
    ("A shower curtain clings because the hot water makes the air rise, and the rising air drags "
     "the curtain in behind it - so the fixes are weight and air. A hem with weights in it, or a "
     "magnet at the bottom corners if the tray or bath is steel, holds it down; a curtain that "
     "hangs to just below the rim of the tray clings less than a long one that pools; and a "
     "curved rail holds the curtain away from you while it hangs. If it still flaps, leave the "
     "bathroom door ajar so the room is not sealed, which is often the whole cause in a small "
     "bathroom with the window shut."),
    # the rail, the curtain as a thing to buy or fit, and the mould along the bottom are other jobs
    avoid=("rail", "rod", "pole", "fit a rail", "fit the rail", "install", "replace", "buy",
           "size", "length", "width", "colour", "color", "blackout", "mould", "mold",
           "mouldy", "moldy", "mildew", "smelly", "stain", "stains",
           "clean", "cleaning", "washing machine", "bleach", "vinegar", "smell", "smells",
           "window", "lined", "thermal", "tie back", "tieback", "sew", "hem a",
           # "curtains" is not here: the avoid words are matched as word forms, so a plural
           # "curtains" stood the whole row down for every line that said "shower curtain"
           "window curtain", "net curtains", "blackout curtains"),
    ask=("cling", "clinging", "clings", "stick", "sticks", "sticking", "blow", "blows", "blowing",
         "flap", "flaps", "suck", "sucks", "billow", "keeps", "stop", "how", "fix"),
    bias=1))

# Which fuel is cheaper to cook on is a question people ask when they are choosing a hob or
# deciding whether to run the oven, and on main it had two wrong answers: "is it cheaper to cook
# with gas or electric" got the night-tariff card, and "is an induction hob cheaper to run than
# gas" got the boiler advice. Both are about heating the house on a cheap hour; this is about the
# pan in front of you.
_FUEL_HOB = "gas hob"
ENTRIES.append(entry(
    "cooking-fuel",
    (("gas", "electric", "electrical", "electricity", "induction", "ceramic", "halogen"),
     ("hob", "hobs", "oven", "ovens", "cooker", "cook", "cooks", "cooking", "cooked",
      "ring", "rings", "pan", "pans", "cheaper", "cheapest", "run", "running", "cost",
      "costs", "better", "which", "boil", "boils", "boiling")),
    "Gas is the cheapest to run: a gas ring is roughly 10 to 15p an hour against 25 to 35p for a "
    "standard electric ring, and a gas oven is about half the cost of an electric one at the same "
    "heat. Induction is the one most people prefer in use - about 15 to 20p an hour, because it "
    "puts almost all the heat into the pan and boils a pan of water in around half the time, so "
    "the shorter cooking usually makes up the difference. The pan matters as much as the fuel: a "
    "flat base that covers the ring, and a lid on, save more than changing fuel does.",
    ask=("hob", "hobs", "oven", "ovens", "cooker", "cook", "cooking", "ring", "rings",
         "boil", "boils", "boiling", "induction", "gas", "electric", "cheaper", "cheapest",
         "cost", "costs", "run", "running", "better"),
    avoid=(
        # the kettle is its own answer (2 to 3p a boil), and it is cheaper than any hob
        "kettle", "kettles", "boil water in a kettle",
        # a bill, a boiler, a heater or a car is a different ledger
        "bill", "bills", "tariff", "standing charge", "direct debit", "pay", "paying",
        "supplier", "price cap", "boiler", "radiator", "heating", "hot water", "immersion",
        "heater", "log burner", "wood burner", "fire", "car", "vehicle", "charge the car",
        "fireplace",
        # the fuel comparison with no hob in it is the heating-fuel row's, and "is gas cheaper
        # than electricity" was still read as a hob because gas and cheaper are both key words
        "electric heating", "gas heating", "gas cheaper", "cheaper than electricity",
        "cheaper than gas", "gas or electricity", "electricity or gas",
        "heat the house", "heat my house", "heat a house", "heat with",
        # a fault is a repair, a hob to buy is a buying question, and cleaning one is a cleaning one
        "not working", "wont heat", "won't heat", "wont light", "won't light", "broken",
        "faulty", "repair", "replace", "buy", "buying", "shop", "review", "reviews",
        "clean", "cleaning", "scrub", "stain", "stains", "mould", "mold"),
    bias=1))

# Which fuel is cheaper to HEAT with is the bigger version of the hob question, and on main it had
# two wrong answers: "is gas cheaper than electricity" got the night-tariff card, and "is it
# cheaper to heat with gas or electricity" got the way-to-pay card. The cooking-fuel row above
# names the hob, the oven and the ring in avoid precisely because this is the other question, so
# this row keys the things that heat a house instead: the boiler, the radiators, the heat pump,
# the immersion, a storage heater, or the bare word gas with a cost word beside it.
ENTRIES.append(entry(
    "heating-fuel",
    (("gas", "gas boiler", "gas heating", "electric", "electrical", "electricity",
      "electric heating", "heat pump", "boiler", "radiator", "radiators", "immersion",
      "storage heater", "night storage", "hot water", "central heating", "heating"),
     ("cheaper", "cheapest", "cheap", "cost", "costs", "costing", "run", "runs", "running",
      "to run", "compare", "comparison", "which is", "which one is", "better", "worse",
      "vs", "versus", "more expensive", "less expensive", "dearer")),
    "Gas is much the cheapest for heat: about 6 to 7p a unit (kWh) against about 24 to 25p for "
    "electricity, so the same heat costs roughly a quarter as much, and that is why a gas boiler "
    "is the cheap way to warm a house. The one electric thing that competes is a heat pump, "
    "because it moves heat instead of making it - three units of heat for one of electricity "
    "puts it near or below gas - while panel heaters, fan heaters and an immersion are the "
    "dearest, at about four times the gas price for the same warmth. Whatever the fuel, the "
    "cheapest heat is the heat you do not lose: loft and cavity insulation, and a boiler flow "
    "temperature of 55 to 60C, cut the bill more than switching fuel does.",
    ask=("cheaper", "cheapest", "cost", "costs", "run", "running", "compare", "which is",
         "better", "worth", "gas", "electric", "electricity", "heat pump", "boiler",
         "radiators", "immersion", "heating"),
    avoid=(
        # whether to leave the heating running all day is not which fuel is cheaper: "is it
        # cheaper to leave the heating on all day" asks about the habit, and home_craft's
        # heating-all-day row answers it with a yes or no where this row compares gas and
        # electricity. The habit phrases stand this row down.
        "leave the heating on", "leaving the heating on", "left the heating on",
        "leave my heating on", "leaving my heating on", "leave our heating on",
        "leave the heating running", "leave it on", "leaving it on", "left it on",
        "leave the boiler on", "leaving the boiler on", "keep the heating on",
        "keeping the heating on", "on all day", "on all night", "all the time",
        "all day and night", "day and night",
        # the hob, the oven and the kettle are the cooking-fuel row's, and a pan is not a house
        "hob", "hobs", "oven", "ovens", "cooker", "cook", "cooks", "cooking", "cooked",
        "induction", "ring", "rings", "kettle", "kettles", "air fryer", "microwave",
        "slow cooker", "toaster",
        # one appliance's cycle is its own answer, not the fuel ledger
        "shower", "showers", "bath", "baths", "washing machine", "dishwasher", "tumble dryer",
        "dryer", "car", "vehicle", "charge the car", "ev", "electric car", "boiler on finance",
        # what a unit is and what one costs is money's unit-rate row ("a unit is a kilowatt
        # hour"): "how much is a kwh of electricity" was answered with this comparison.
        "kwh", "kw h", "kilowatt", "kilowatts", "what is a unit", "what does a unit mean",
        # the running cost of one thing is the running-costs table's: "how much does it cost to
        # run a radiator" wants its 60p an hour, not a comparison of the two fuels.
        "cost to run", "to run a", "costs to run", "an hour", "per hour", "a day", "per day",
        "a month", "per month", "how much does it cost",
        # a bill, a tariff, a supplier and a payment are money's rows, not this one
        "bill", "bills", "tariff", "tariffs", "supplier", "suppliers", "price cap", "standing charge",
        "direct debit", "pay", "pays", "paying", "paid", "payment", "switch", "switching",
        "deal", "deals", "fixed rate", "quote", "quotes", "afford", "debt", "arrears",
        "gone up", "went up", "too high", "too much", "so much", "why is", "why does", "why has",
        # a fault is the boiler's repair row, and a grant or a buying decision is its own
        "broken", "not working", "wont heat", "won't heat", "no hot water", "leak", "leaking",
        "noise", "noisy", "banging", "knocking", "kettling", "pressure", "fault", "faulty",
        "repair", "grant", "grants", "install", "installation", "buy", "buying", "replace",
        "new boiler", "which boiler", "best boiler", "log burner", "wood burner", "fireplace",
        "one room", "room", "rooms", "bedroom", "tonight", "cold", "freezing",
        # the hour of the day is the cheapest-hours row's, and "what time is electricity
        # cheapest" is exactly that question with a fuel word in it.
        "what time", "best time", "when is", "night", "nights", "overnight", "at night",
        # "what is the cheapest time to use electricity" is the hour question with a fuel word
        # in it, and "what time" alone missed it because the line says "what is the cheapest
        # time". A line that names the time of day rather than the fuel is the tariff row's.
        "cheapest time", "time of day", "time to use", "time to run", "time to put",
        "off peak", "off-peak", "economy 7", "economy7", "delay", "timer", "timed",
        "cheap window", "morning", "evening", "afternoon",
        # "heat" and "better" are an ache's words as much as a boiler's, and the stove doesn't
        # heat a house with it: "is heat or ice better for a sore back" was answered with the
        # price of gas, because the burning word in this row and the burning word in the
        # compress question are the same word. A line that names a body or an ache, or a pack
        # you put on one, is the body rows' question.
        "ice", "ice pack", "ice packs", "cold pack", "hot pack", "heat pack", "heat packs",
        "compress", "wheat bag", "frozen peas", "ice bath", "sore", "soreness", "ache",
        "aches", "aching", "achy", "sprain", "sprained", "strain", "strained", "pulled",
        "muscle", "muscles", "stiff", "stiffness", "swollen", "swelling", "tender", "throbbing",
        "back pain", "neck", "shoulder", "shoulders", "knee", "knees", "ankle", "ankles",
        "hip", "hips", "elbow", "wrist", "thigh", "calf", "shin", "joint", "joints",
        "tendon", "ligament", "hurts", "hurting", "pinched nerve", "sciatica",
        # an animal in the heat is its own card, and "run" is in this row's second group, so
        # "should i run with my dog in this heat" was answered with the price of gas. Any line
        # that names an animal is not a comparison of two fuels.
        "dog", "dogs", "puppy", "puppies", "pup", "cat", "cats", "kitten", "kittens",
        "pet", "pets", "hamster", "rabbit", "guinea pig", "horse", "pony", "chicken",
        "chickens", "the dog", "my dog", "the cat", "my cat"),
    # a shade above the hour row so the tie between "gas", "electric" and "cheaper" goes to the
    # fuel comparison, which is what the line is asking.
    bias=2, guard=not_a_sound))


# Using the machine for the first time is its own question: "how do i use a washing machine" and
# "how do i wash clothes" reached nothing at all, while the temperature, the smell and the broken
# drum each had a row. It is the ordinary load, not a fault.
ENTRIES.append(entry(
    "use-the-washer",
    (("washing machine", "washer", "washing", "laundry", "clothes", "wash"),
     ("how do i use", "how to use", "how do you use", "use the", "use a", "use my", "first time",
      "put a wash on", "put on a wash", "wash clothes", "wash my clothes", "do the washing",
      "the washing", "how do i wash", "how to wash", "start it", "start a wash", "load it",
      "how does it work", "which cycle", "which programme", "what cycle")),
    "Sort lights from darks, empty the pockets and close the zips, then load it so a hand fits "
    "flat on top of the pile - a packed drum does not rinse. Everyday clothes: a 30 or 40 degree "
    "cotton wash, normal spin, and the detergent dose on the bottle in the drawer. A pod goes in "
    "the drum, not the drawer. A wool or silk label gets its own cycle. Run an empty hot wash "
    "once a month.",
    # a machine that is broken, smelly or full of water is a fault with its own row, and the
    # temperature of a wash, a stain and drying are each their own question
    # "how do i clean behind the washing machine" is the gap, not the load: the place stands
    # this row down.
    avoid=("broken", "not working", "wont", "won't", "error", "flashing", "leaking", "drain",
           "draining", "smells", "smelly", "mould", "mold", "repair", "replace", "buy",
           # a machine that bangs, rattles or walks is a fault the noise row knows, and "the
           # washing machine bangs when it spins" was sorted into the ordinary-load answer
           "bang", "bangs", "banging", "rattle", "rattles", "rattling", "shake", "shakes",
           "shaking", "vibrate", "vibrates", "noise", "noisy", "loud", "walk", "walks",
           "behind", "underneath", "at the back of",
           # water on the floor is a fault, and it is said as "water is coming out of the bottom
           # of the machine" more often than as "leaking": that line was told to sort lights from
           # darks. The words for water escaping stand this row down.
           "coming out", "coming from", "puddle", "puddles", "water everywhere", "flooded",
           "flooding", "water on the floor",
           "temperature", "degrees", "what temperature", "wool only", "shrink", "shrunk",
           "stain", "stains", "dryer", "tumble", "drying", "iron", "hand wash only",
           # a duvet, a pillow and a sleeping bag do not go in the drum with the shirts: each has
           # a size, a drying problem and usually a launderette, and cleaning.py answers them
           # a machine that wobbles, walks or jumps is not the load lesson: it wants levelling
           # or a load spread round the drum, and "the washing machine wobbles when it spins" was
           # answered with how to sort lights from darks because "the washing" is in this key.
           "wobble", "wobbles", "wobbling", "wobbly", "shakes", "shaking", "rocks", "rocking",
           "walks across", "walking", "jumps", "vibrates", "vibrating", "not level",
           "off balance",
           "duvet", "duvets", "quilt", "quilts", "pillow", "pillows", "sleeping bag",
           "blanket", "blankets", "bedding", "mattress", "feather", "feathers", "down",
           # "washing up" is the dishes, not the machine: "my flatmate never does the washing up"
           # was answered "Sort lights from darks, empty the pockets and close the zips" because
           # "the washing" carries the dish word in it.
           "washing up", "wash up", "washing-up", "dishes", "dish", "dirty dishes", "plates",
           "pots and pans", "dishwasher", "sink", "cutlery", "mugs",
           # "put the washing machine on at night" is not how to use it: the hour and the tariff
           # are the cheapest-hours row's question, and "the washing" in this key caught the
           # phrase "put the washing machine on" every time.
           "at night", "overnight", "late at night", "economy 7", "economy7", "off peak",
           "off-peak", "tariff", "tariffs", "what time", "best time", "cheapest", "cheaper",
           "cheap time", "time of day", "during the day", "in the morning", "in the evening",
           "delay", "delayed", "timer", "timed",
           # a place to do the washing is a place question, not a lesson in the cycle: "is there
           # a launderette near me" was answered with the load-it-properly card once the washer
           # was already in the conversation.
           "launderette", "laundrette", "laundromat", "near me", "nearest", "nearest one",
           "how much do they cost",
           # where the powder, the softener or a pod goes is the drawer's question, and this
           # row answers the load rather than the compartment
           "where do i put", "where does", "where do the", "where should i put",
           "which compartment", "what compartment",
           # a device that went through the wash is the device's question, not how to run a
           # load: "my earbuds went in the washing machine" and "i left my phone in my jeans and
           # washed them" were both told to sort lights from darks (@ivory-magnet, #9232 family)
           "earbuds", "airpods", "headphones", "phone", "iphone", "mobile", "laptop", "tablet",
           "ipad", "kindle", "watch", "device", "hearing aid", "remote", "keys",
           # a food being washed or rinsed is a kitchen instruction, and "how do i wash rice"
           # was the lesson in loading a drum: "how do i wash" is in the key and "wash" in
           # both groups, so nothing else was needed to take it.
           "rice", "pasta", "spaghetti", "noodles", "lentils", "quinoa", "chickpeas",
           "beans", "greens", "spinach", "lettuce", "mushrooms", "vegetables", "veg",
           "fruit", "salad", "water runs clear", "runs clear",
           # "how do i wash" is in the key for a load, and it also opens a wash of a body:
           # "how do i wash a newborn baby", "how do i wash a toddler's hair", "how do i wash
           # my hair" and "how do i wash myself" were all answered with the drum, the 30 degree
           # cotton wash and the pod. A person is not a load, and the baby-bath row and the
           # hair rows answer those lines.
           "baby", "babies", "newborn", "infant", "toddler", "child", "children", "kid", "kids",
           "my hair", "hair", "my face", "face", "myself", "my body", "my hands", "body",
           "bath", "bathe", "shower", "bathroom", "dog", "puppy", "cat", "kitten", "car"),
    bias=1, guard=_not_a_machine_that_has_gone))

ENTRIES.append(entry(
    "hang-door",
    (("door", "doors", "internal door", "internal doors", "panel door", "replacement door"),
     # the bare ask is not a key word here: with "how do i" in this group, "how do i strip old
     # gloss off a door" was a door question and this row took it from the paint row on nothing
     # but "door" and the ask. The fitting words carry the ask on their own.
     ("hang", "hanging", "rehang", "re-hang", "fit", "fitting", "replace", "replacing", "new",
      "put on", "putting on", "swing", "sagging", "dropped", "plane", "planed")),
    "Take the old door off its hinges and measure it, because a new one is trimmed to that, not the "
    "other way round: width, height, and the distance from the top edge to the hinge centres. Cut "
    "2-3mm off the closing edge and 3mm off the bottom, plane a whisker of a chamfer on the "
    "closing side so it does not rub, and keep the hinge positions from the old door - about "
    "125mm up from the top and 250mm from the bottom, so the door weight is carried at the top. "
    "Chisel the recesses no deeper than the hinge leaf, screw the hinge to the door first, hang it "
    "on the frame with one screw in each and check it swings before the rest go in. A door wants "
    "2-3mm all round at the closing edge and 5mm or so off the floor over a carpet; if it swings "
    "itself open or shut, the frame is out of plumb, not the door.",
    # the door that will not close, will not stay shut and is being painted each have their own
    # row, and a hinge is what the fitter already knows about.
    avoid=("creak", "creaks", "creaking", "squeak", "squeaks", "squeaking", "rubbing", "rubs",
           "scrape", "scraping", "sticking", "stuck", "wont shut", "won't shut", "wont close",
           "lock", "locks", "handle", "handles", "knob", "key", "keys", "paint", "painting",
           "painted", "draught", "draft", "cupboard", "wardrobe", "cabinet", "garage", "car",
           "oven", "washing machine", "shower", "sliding", "bifold", "patio", "front door",
           "back door", "doorbell", "camera", "frozen", "slam", "slams", "banging", "toy",
           "safety", "bathroom door lock",
           # a pet barking, scratching or sleeping at a door is a behaviour question, and the
           # generic "how do i" in this row's key caught "how do i stop my dog barking at the
           # door" once the pet row stood down on the bark
           "bark", "barks", "barking", "barked", "yap", "howl", "howling", "meow", "meowing",
           "scratch", "scratches", "scratching", "scratching at the door", "dog", "dogs",
           "puppy", "cat", "cats", "kitten", "pet", "pets", "wee", "weeing", "poo", "pooing")))

# ---- what temperature an appliance runs at ------------------------------------------------
#
# The same question asked of a different machine: "what temperature should the freezer be",
# "how hot should a dishwasher be", "how hot should the grill be", "how hot does a kettle get".
# None of them had an answer - the freezer lines fell to a shrug, to the fridge card, or to the
# weather, the grill ones to a shrug, and the kettle to "I'm not sure" - because each appliance
# was only ever written about through its fault or its cost.
#
# The subject is the appliance and the ask is the heat of it, so the guards can be few: a fault,
# a smell or a price carries no heat word and never reaches these rows. No word another row keys
# is named in avoid, because that would take the only-entry-uses-it point off the row that keys
# it - "my tumble dryer is not heating up" lost its own card that way. The food a person cooks is
# the one exception: "what temperature should i grill chicken at" and "how hot should the grill
# be for sausages" ask the heat of the food, not of the appliance, so those lines keep the
# cooking answers they had.
APPLIANCE_HEAT = (
    (("freezer", "freezers", "chest freezer", "freezer compartment", "freezer drawer",
      "ice box"),
     "freezer",
     "A freezer should sit at -18C or colder (0F on an American dial). Most freezers have a dial "
     "marked 1 to 5 rather than degrees, so stand a thermometer between two frozen packs "
     "overnight: warmer than -18C and you are keeping food for weeks rather than months, and "
     "colder is fine, just dearer to run."),
    (("dishwasher", "dishwashers"),
     "dishwasher",
     "Most dishwashers wash at about 50C on eco, 60 to 65C on the normal programme and 70C on "
     "intensive, and the final rinse is hotter than any of them. For greasy pans, plastic and "
     "anything that was hand-washed badly, use the 60C programme or above: that, with the hot "
     "rinse, is what does the cleaning."),
    (("grill", "grills", "oven grill", "top grill", "grill pan", "broiler", "overhead grill"),
     "grill",
     "An oven grill wants about five minutes preheating with the door shut, with the shelf 10cm "
     "or so below the element: the element should be glowing red across its whole length, and a "
     "drop of water flicked at the pan should sizzle. Food that browns in a minute and stays raw "
     "inside means the shelf is too high, not that the grill is too hot."),
    (("kettle", "kettles", "electric kettle"),
     "kettle",
     "A kettle takes water to 100C and switches itself off there, and that switch is the same "
     "thermal cut-out on every electric kettle, so there is no hotter setting to find. The "
     "outside of a plastic kettle stays much cooler than the water; a steel one gets hot enough "
     "to sting, so lift it by the handle."),
)

# The ask is what keeps these rows honest: a temperature, a heat, a dial setting - and nothing
# else. "my freezer smells", "the grill is broken", "is a dishwasher worth it" and "how do i
# descale the kettle" carry no heat word, so they never arrive here.
_HEAT_ASK = ("how hot", "how cold", "how warm", "warmest", "coldest", "what temperature",
             "what temp", "which temperature", "temperature", "temp", "setting",
             "settings", "run at", "runs at", "goes up to")


_HEAT_NOT_FOOD = ("chicken", "meat", "beef", "pork", "lamb", "steak", "sausage", "sausages",
                  "bacon", "fish", "salmon", "turkey", "ham", "mince", "burger", "toast",
                  "bread", "cake", "pizza", "chips", "rice", "pasta", "potato", "vegetables")


def _heat_row(names, slug, said):
    """One appliance temperature, keyed by the appliance and asked about the heat of it."""
    return entry("appliance-heat-" + slug, (names, _HEAT_ASK), said, avoid=_HEAT_NOT_FOOD,
                 bias=2)


for _names, _slug, _said in APPLIANCE_HEAT:
    ENTRIES.append(_heat_row(_names, _slug, _said))
# --- a water softener ----------------------------------------------------------------
# "how do i top up the salt" with nothing else in the line is the softener: the salt is what
# the thing runs on and the two sentences are in every manual. The bare lines are spelled out
# as whole subjects of their own, because "salt" alone is the cooking word and the dishwasher
# word and both have answers; the rows that name the machine are keyed on the machine.
ENTRIES.append(entry(
    "water-softener-salt",
    ("how do i top up the salt", "top up the salt", "topping up the salt",
     "how do i top up salt", "the salt has run out", "the salt ran out", "salt has run out",
     "the salt is low", "salt level", "salt needs topping up", "do i need to top up the salt",
     "how much salt does a softener use", "what salt do i need for the softener"),
    "Block or tablet salt, dropped into the brine tank and kept above the water line - check it "
    "monthly and top it up then, because a family of four gets through roughly one 25kg bag a "
    "month. Fill no higher than the top of the brine well, and never use table, cooking or "
    "dishwasher salt: the anti-caking agents turn to sludge in the tank.",
    # the dishwasher takes its own salt, cooking has salt in it, and a fabric softener is a
    # different machine in a different room.
    avoid=("dishwasher", "pasta", "cooking", "chips", "popcorn", "bath", "blood pressure",
           "grit", "gritting", "road", "drive", "path", "stock", "fabric", "laundry",
           "washing machine", "clothes", "tumble dryer", "salt water", "sea water")))

# "how do i soften water" is the question the machine exists to answer, and it is asked before
# there is a machine: nothing you add to a glass takes hardness out, and the answer is what a
# softener is and what it does not do. "water" alone is the dry-eye entry's word, so each subject
# below carries the hardness with it and the scale-in-the-kettle lines stay out.
ENTRIES.append(entry(
    "soften-hard-water",
    (("soften", "softening", "soft water", "hard water", "hardness"),
     ("water", "my water", "the water", "tap water", "mains water")),
    "Hardness is calcium and magnesium dissolved in the water, and the only thing that takes it "
    "out is an ion-exchange softener plumbed in where the mains comes into the house: it swaps "
    "the calcium for sodium, and the salt you put in it is what does the swapping. A jug filter "
    "changes the taste and nothing else, and boiling leaves the calcium behind as the scale you "
    "find in the kettle. It needs a plumbed feed and a drain, so in a rented flat ask the "
    "landlord first.",
    # said as a how-to, not as a what-is: "is hard water bad" and "what is hard water" already
    # have their own rows, and this one is the instruction the person is asking for. It is an
    # ask and not a third key group, because a group only says one of its words is somewhere in
    # the line, and "we have soft water" is a fact about their house: the explainer told somebody
    # what hardness is when they had just said they had none of it, where the chat's own
    # "Noted: you have soft water" is right.
    ask=("how", "how do i", "how to", "how can i", "what can i do", "best way", "fix",
         "deal with", "get rid", "solve", "help", "stop"),
    # the machine bought or broken is the rows below, the kettle's scale is the kettle's, and a
    # body (hair, skin, drinking, a baby's bottle) asks about hardness a different way.
    avoid=("kettle", "descale", "descaler", "limescale", "dishwasher", "washing machine",
           "hair", "skin", "baby", "formula", "plants", "fish", "boiler", "buy", "buying",
           "cost", "price", "install", "plumber", "rent", "salt", "salt level",
           # whether it is bad for you, and what the reading is in your area, are questions about
           # the water itself and they already have an answer: this row is only the how-to.
           "bad", "bad for", "harmful", "safe", "healthy", "drink", "drinking",
           "in my area", "my area", "supplier", "reading", "test")))

# Whether to have a softener at all is a different question from filling one, and this row's
# key carries "need" and "what" so the buying question scored on the same two words. A guard,
# not an avoid: an avoid phrase matches loosely, and "do i need" in the avoid list stood the
# row down for "what salt do i need for the water softener" as well.
A_SOFTENER_SALT_WORD = ("salt", "brine", "tablet", "block", "granule")

def _not_the_buying_question(understood):
    """True unless the line asks whether to have a softener rather than how to fill one."""
    said = str((understood or {}).get("text") or "").lower()
    if any(word in said for word in A_SOFTENER_SALT_WORD):
        return True
    return not re.search(r"\bworth\b|\bshould (?:i|we) (?:get|buy|have|install|bother|invest)\b|"
                         r"\bdo (?:i|we) (?:want|need)\b|\bis it necessary\b|\bgood idea\b|"
                         r"\bworth the money\b", said)

# The same salt question with the machine in the line: "how often do i put salt in the
# softener", "how much salt does the water softener take".
ENTRIES.append(entry(
    "water-softener-salt-named",
    (("water softener", "water softeners", "salt softener", "brine tank", "salt tank",
      "softener salt", "block salt", "tablet salt", "salt blocks", "salt tablets", "softener"),
     ("salt", "top up", "topup", "refill", "fill", "add", "put", "how often", "monthly",
      "how much", "much", "level", "run out", "ran out", "runs out", "low", "empty", "need",
      "needs", "which", "what", "kind", "type", "buy")),
    "Block or tablet salt, dropped into the brine tank and kept above the water line - check it "
    "monthly and top it up then, because a family of four gets through roughly one 25kg bag a "
    "month. Fill no higher than the top of the brine well, and never use table, cooking or "
    "dishwasher salt: the anti-caking agents turn to sludge in the tank.",
    avoid=("fabric", "laundry", "washing machine", "clothes", "tumble dryer", "conditioner",
           "dishwasher", "pasta", "cooking", "grit", "gritting", "road"),
    # "do i need a water softener" is the buying question and this row is the salt how-to, but
    # a `do i need` in the avoid list stood this row down for "what salt do i NEED for the water
    # softener" too, because an avoid phrase matches loosely. A guard reads the line instead.
    guard=_not_the_buying_question,
    bias=2))

# Whether to have a softener at all is the one water question nothing answered: the rows above
# are how to fill it, what it is and what to do when it stops working, so "is a water softener
# worth it" went to the fabric conditioner card (the bare word "softener") and "do i need a
# water softener" to the salt how-to. The honest answer depends on the hardness of the supply
# and on what the marks are actually costing, so this row names both and the cheaper options.
ENTRIES.append(entry(
    "water-softener-worth-it",
    (("water softener", "water softeners", "softener", "softened water", "hard water",
      "water is hard", "water hard"),
     ("worth", "worth it", "worth the money", "should i get", "should i buy", "should we get",
      "do i need", "do we need", "do i want", "is it necessary", "necessary", "good idea",
      "buy", "cost", "price", "expensive", "how much", "money", "saving", "savings",
      "install", "installed", "installation", "rent", "rented", "alternative", "instead")),
    "It is worth it only if your supply is properly hard - over about 250mg of calcium "
    "carbonate per litre, which your water supplier publishes for your postcode - and if the "
    "scale is costing you money: a kettle that furs up and a shower head that clogs. Expect a "
    "few hundred to well over a thousand pounds fitted, plus a bag of salt a month, and a "
    "bypass tap for drinking water because it adds sodium. For a kettle and a shower head "
    "alone, a filter jug and a bottle of descaler cost far less and do most of the work.",
    bias=4,
    # the machine's own how-tos and faults own their words: salt, brine tank, not working
    avoid=("salt", "brine", "tablet", "block salt", "not working", "stopped working", "fault",
           "top up", "refill",
           # "do i need fabric softener" is the drawer, not the plumbing: the bare word
           # "softener" is in both, and "fabric" is what tells them apart.
           "fabric", "conditioner", "laundry", "clothes", "drawer"),
))

# A softener that has stopped softening is a fault, not a how-to: the salt is there and the
# water is still hard, which is bridging or a bypass valve, and both are checked before any
# call-out.
ENTRIES.append(entry(
    "water-softener-fault",
    (("water softener", "softener", "brine tank", "salt tank"),
     ("not working", "isnt working", "doesnt work", "not using salt", "isnt using salt",
      # "my softener has stopped using salt" is the same fault said as a change of state, and
      # without it the fill card answered a softener that is not working
      "not using the salt", "stopped using salt", "stopped using the salt", "stopped taking salt",
      "using no salt", "has used no salt", "uses no salt",
      "not softening", "isnt softening", "doesnt soften",
      # the two words "still limescale" stood here, and the word alone cost the `limescale`
      # card its reading: "what can i do about limescale" reached nothing at all and got a
      # shrug, because a word another row's key holds stops answering a third reading of it.
      # The change of state is "still hard" and the machine's own words, which are above.
      "still hard", "not soft", "stopped working", "fault", "problem",
      "scum", "no salt", "hard water", "not drawing", "isnt drawing")),
    "A softener that has stopped using salt has usually bridged: the salt has crusted into a "
    "solid shelf over the water, so push a broom handle down into the tank - if it will not "
    "sink, break the crust up and let it re-dissolve. If the salt is loose, check the bypass "
    "valve is shut, set the hardness to your supplier's figure for your area, and clean the "
    "brine injector; still hard after that and it needs a service.",
    avoid=("fabric", "laundry", "washing machine", "clothes", "tumble dryer", "conditioner",
           "shower head", "kettle", "tap", "showerhead"),
    bias=2))

# A chip in a worktop, a sink, a bath or a plate is a repair question, and nothing owned it: the
# chips recipe took "how do i get a chip out of a worktop" (it saw the food), a chipped sink got
# the "rinse the sink after every wash-up" line, "how do i fill a chip in a laminate worktop" got
# the dentist, and a chipped tile got "mark a level line one tile up". The repair is different for
# laminate, stone, enamel and crockery, so one reply names each and the composer shows the one the
# line asked about.
def _chip_says(said, words):
    """True when one of the words is said as a word, or the phrase as a phrase.

    A plain `word in said` reads "bath" out of "bathroom" and "hob" out of "hobby", so a
    chipped tile in the bathroom was getting the enamel-bath repair. The words are matched
    whole, and a phrase is matched as it is written.
    """
    for word in words:
        if " " in word:
            if word in said:
                return True
        elif re.search(r"\b%s\b" % re.escape(word), said):
            return True
    return False


def _a_chip_in_it(memory, understood):
    """The repair for a chip, by what has been chipped."""
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    # laminate and veneer: the chip is a hole in the picture, and the core is what swells
    if _chip_says(said, ("laminate", "veneer", "formica", "melamine", "chipboard", "ikea")):
        return ("Seal a laminate chip rather than fill it: a repair wax or a touch-up kit in the "
                "same colour goes in with a fingertip and a clear top coat stops water reaching "
                "the chipboard core, which is the part that swells and lifts the surface. If the "
                "edge of the chip has lifted, press it down with a warm iron through a cloth "
                "first. A chip along a front edge that keeps catching wants a new worktop strip or "
                "a whole top, because a filler there takes the knocks for a few months only.")
    # stone, granite, quartz, composite: a pro job, and a dyed epoxy at home
    if _chip_says(said, ("stone", "granite", "quartz", "marble", "composite", "corian",
                         "silestone", "solid surface")):
        return ("A stone worktop chip is a two-part epoxy job, tinted to the stone: clean the "
                "chip out, build the epoxy slightly proud, let it cure hard and then flat it back "
                "with a fine diamond pad and polish. Granite and quartz are a fitter's call if the "
                "chip is bigger than a fingertip or on a joint, and most fitters will do a small "
                "one for a call-out fee. Never use a filler that shrinks or a heat gun near the "
                "stone, because a thermal shock cracks it.")
    # the commonest of all: a worktop, and the repair follows the material it is made of
    if _chip_says(said, ("worktop", "worktops", "counter", "countertop", "counter top",
                         "breakfast bar")):
        return ("Find out what the top is made of before you buy anything, because the three "
                "repairs do not swap. A laminate or veneered top takes a repair wax in the "
                "matching colour and a clear seal over it, so water cannot reach the chipboard "
                "core and swell it; solid wood is sanded back and filled with a wax or wood filler "
                "and then re-oiled; stone or quartz takes a tinted two-part epoxy, built proud, "
                "flattened and polished. A chip on a front edge that keeps catching a sleeve is "
                "the one worth a new edge strip instead of a filler.")
    # an acrylic or glazed sink, which is neither enamel nor stone
    if _chip_says(said, ("sink", "sinks", "basin", "ceramic", "porcelain", "glazed", "glaze")):
        return ("Match the kit to the sink: a glazed ceramic one takes an enamel repair kit, and "
                "an acrylic or composite one takes an acrylic filler matched to the colour, "
                "because the enamel kit will not bond to plastic. Clean the chip right out, let "
                "it dry, and build two or three thin coats rather than one thick one. A chip "
                "through the glaze on a ceramic sink keeps dirt in the crater, so it is worth "
                "doing even though it will still show.")
    # enamel: a bath, a basin or a cooker top, and the repair is an enamel kit, not a filler
    if _chip_says(said, ("enamel", "bath", "cast iron", "steel bath", "shower tray", "cooker",
                         "hob")):
        return ("An enamel chip wants an enamel repair kit: clean it, de-grease it, then build two "
                "or three thin coats of the enamel touch-up rather than one thick one, letting "
                "each go off. It is a cosmetic repair that stops the chip rusting and picking up "
                "dirt, and it will show a little; a bath chip through to the cast iron has to be "
                "done or the enamel round it starts to flake. A chip on a hob ring or a shower "
                "tray is the same kit, and a crack rather than a chip is a replacement.")
    # crockery and glassware: sharp, porous, and the honest answer is often to stop using it
    if _chip_says(said, ("plate", "plates", "mug", "mugs", "bowl", "bowls", "cup", "cups",
                         "teapot", "jug", "dish", "dishes", "glass", "glasses", "tumbler",
                         "wine glass", "pint glass")):
        return ("Retire a chipped plate, mug or glass: the chip is a sharp edge that will cut a "
                "lip, the glaze round it is no longer sealed, and there is no repair worth making. "
                "A chip on the foot or the underside is the one that is safe to keep for a plant "
                "pot or a pet bowl, and if it is glass, a chip anywhere near the rim is a break "
                "waiting to happen with hot water in it.")
    # a tile: filler hides it, but a chipped tile on a corner usually wants replacing
    if _chip_says(said, ("tile", "tiles", "grout", "splashback")):
        return ("A small chip in a tile hides with a dab of the same-colour grout, a touch-up "
                "pen or a drop of enamel, worked into the chip with a fingertip and wiped off the "
                "face at once. A chip out of a corner or an edge is the tile coming away from the "
                "wall, so press it back and check for a hollow sound; if it is hollow, the tile "
                "wants replacing rather than filling, and buy a spare now because the shade will "
                "not match later.")
    # a gap is not a chip, and it wants a flexible filler rather than a hard one
    if _chip_says(said, ("gap", "gaps", "crack between", "cracks between", "opening up",
                         "draught", "draft")):
        return ("A gap in a floor or under a skirting wants a flexible filler, not a hard one: rake "
                "the dust out, push in a foam backer rod if it is deep, then run a paintable "
                "acrylic sealant or a sliver of matching wood glued in and planed flat, because a "
                "hard filler in a floor cracks out with the first bit of movement. Between "
                "floorboards on a suspended floor, fill from above with a sliver of pine and glue "
                "rather than sealing it, so the boards can still move.")
    # bare wood: sand and fill, because the chip has taken the finish with it
    if _chip_says(said, ("wood", "wooden", "oak", "pine", "beech", "walnut", "table",
                         "tabletop", "floorboard", "floor", "door", "skirting", "furniture")):
        return ("Sand the chip back to sound wood, then fill it with a wood filler or a wax stick "
                "in the right colour, building it a little proud and paring it flat once it has "
                "gone off. Wipe a drop of oil or the same finish over it afterwards, or the bare "
                "patch shows as a light mark and dries out again. A chip on a corner that keeps "
                "being knocked wants a rounded edge or a corner trim rather than another fill.")
    # the worktop or sink that is glazed ceramic or acrylic, and the plain default
    return ("Match the repair to the surface, because a filler that is right for one is wrong for "
            "the next. A laminate chip takes a repair wax and a clear seal so water cannot reach "
            "the core; a stone top takes tinted two-part epoxy, flattened and polished; an enamel "
            "bath or basin takes an enamel touch-up kit in thin coats; a chipped plate or glass is "
            "one to retire, and a chipped tile takes colour-matched grout or enamel, or a "
            "replacement if the corner has lifted. Photograph it and take the chip's colour to a "
            "hardware shop rather than trusting the name on the tin.")

ENTRIES.append(entry(
    "chip-in-a-surface",
    (("chip", "chips", "chipped", "chip out of", "chip in", "broken edge", "snapped edge",
      "gap", "gaps",
      # "how do i fill a chip in a laminate worktop": the matcher masks the verb and what it
      # takes, so the surface word is all that is left and the chip word needs saying again
      "fill", "fills", "filling", "filled", "fill in", "fill the chip"),
     ("worktop", "worktops", "counter", "countertop", "counter top", "sink", "sinks", "bath",
      "basin", "enamel", "tile", "tiles", "grout", "splashback", "table", "tabletop", "plate",
      "plates", "mug", "mugs", "bowl", "bowls", "cup", "cups", "glass", "glasses", "tumbler",
      "wood", "wooden", "oak", "pine", "stone", "granite", "quartz", "marble", "laminate",
      "veneer", "floor", "floorboard", "door", "skirting", "furniture", "hob", "cooker",
      "shower tray", "pond",
      # "how do i fix a chip in the bathroom" names no surface, and the cleaning row was
      # answering it: with a chip word in the key these three reach the repair that asks which
      # surface it is
      "bathroom", "kitchen", "shower")),
    _a_chip_in_it,
    # the food is not a chip in a surface, and a chip in a windscreen, a tooth, a phone, a
    # spectacle lens or a car's paintwork has an answer of its own already
    avoid=("cook", "cooking", "oven", "fry", "fried", "frying", "bake", "baked", "roast",
           "potato", "potatoes", "maris", "air fryer", "deep fry", "chip shop", "chips and",
           "serving", "recipe", "sauce", "mayo", "salt and vinegar", "takeaway",
           "windscreen", "windshield", "car", "cars", "van", "bonnet", "bodywork", "paint",
           "dent", "scratch", "scratches", "tooth", "teeth", "dental", "dentist",
           "toenail", "nail", "nails", "phone", "screen", "laptop", "watch", "spectacles",
           "spectacle", "glasses frame", "lens", "lenses", "drill bit", "chisel", "blade",
           "knife", "lawnmower", "mower", "hedge trimmer", "buy", "best", "which", "cheapest",
           "how many", "calories", "freeze", "frozen",
           # a smell of chips is the kitchen's air, not a chip in the surface: the second half of
           # the key takes a room word, so "the kitchen smells of chips" and "how do i stop the
           # kitchen smelling of chips" were both answered with a laminate repair wax. The smell
           # rows in this file and in bot/knowledge/cooking_entries.py keep their own lines.
           "smell", "smells", "smelling", "smelly", "stink", "stinks", "stinking", "reek",
           "reeks", "reeking", "odour", "odor",
           # How much water a bath holds is a water-use question, not a chip. "how much water does
           # it take to fill a bath" matched "fill" in the first arm and "bath" in the second and
           # was answered "An enamel chip wants an enamel repair kit": a quantity of WATER is
           # never a repair. The bare "how much" is deliberately not here - "how much enamel do i
           # need to fix a chip in the bath" is still a chip repair, and so is "is it cheaper to
           # repair a chip or replace it" - only the water words, and the cost of running a bath.
           "how many litres", "how many litres of water", "how much water", "water use",
           "litres of water", "gallons of water", "cost to run a bath", "run a bath",
           "running cost of a bath"),
    bias=4))

# A hot water tank is not the stopcock under the kitchen sink and not a radiator: it is fed by
# the cold main through a valve of its own, and the immersion has a switch of its own on the
# wall. "how do i turn off the water heater" was answered with where the kitchen stopcock is,
# and "where is the valve on the hot water tank" with a radiator leak, so both questions about
# the tank got a valve that empties something else.
ENTRIES.append(entry(
    "water-heater-valve",
    (("water heater", "immersion", "immersion heater", "immersion switch", "hot water tank",
      "hot water cylinder", "hot water tank", "hot cylinder", "hot water cistern",
      "boiler cupboard", "airing cupboard"),
     ("turn off", "turning off", "switch off", "switching off", "shut off", "valve",
      "isolate", "isolation", "drain", "draining", "empty", "where is", "wheres", "where's",
      "how do i", "how to", "stop", "cold feed", "back on", "turn back on", "refill",
      "fill back up", "no hot water")),
    "Two things feed a hot water tank. The immersion heater has its own switch on the wall, a "
    "fused spur usually marked immersion - that is the one to turn off for the electric side. "
    "The tank itself is fed from the cold main through a valve on the pipe running into the "
    "side or bottom of it, often red or brass, or a lever valve: a lever across the pipe is "
    "shut, along it is open. Close that, then open the hot taps to drain it. Let it cool "
    "first - a tank full of water is scalding - and leave the wiring alone beyond the switch.",
    avoid=("radiator", "radiators", "gas", "fuse box", "consumer unit", "trip", "boiler pressure",
           "central heating", "thermostat setting", "shower", "washing machine", "dishwasher",
           # a tank that has gone wrong is the fault card below: "how do i test an immersion
           # heater" is not how to drain it, and this row's "how do i" key took it
           "test", "testing", "check", "checking", "not working", "isnt working", "isn't working",
           # the asking forms that name no fault word at all: "how do i know if my immersion is
           # broken" and "how can i tell the element has gone" reached the turn-off row
           "how do i know", "how can i tell", "how do i tell", "broken", "gone", "gone wrong",
           "blown", "faulty",
           "not heating", "no heat", "leak", "leaks", "leaking", "dripping", "tripping",
           "fault", "faulty", "lukewarm", "tepid", "stopped working"),
    # A running-hydration card keys "water" and "on", and it answered "where is the valve on the
    # hot water tank" and "how do i drain the hot water tank" with what to carry on a long run.
    # The tank's own words are specific enough to outweigh it.
    bias=2))

# A hot water tank goes wrong in two ways, and neither had an answer: "my immersion heater isnt
# working" was "That's a pain. What's it doing exactly", "the immersion heater is not heating the
# water" was "Thanks for telling me", "my hot water tank is leaking" was a nod and "water is
# coming out of the lagging" was the water cycle. The turn-off row above keys "no hot water" as an
# ask, so a fault question reached it and got the valve; a fault is its own card, and the two
# faults - no heat, and a leak - are told apart by the line.
_HOT_FAULT_LEAK = ("leak", "leaks", "leaking", "leaked", "drip", "drips", "dripping", "dripped",
                   "weeping", "weeps", "puddle", "water coming out", "coming out",
                   "coming through", "soaked", "wet", "burst", "split", "cracked", "rusty",
                   "rust", "running water", "losing water", "losing pressure")
_HOT_FAULT_COLD = ("not working", "isnt working", "isn't working", "not heating", "not heating up",
                   "wont heat", "won't heat", "wont heat up", "won't heat up", "not getting hot",
                   "not hot", "cold", "cold water", "only cold", "lukewarm", "tepid", "stopped",
                   "stopped working", "packed up", "broken", "fault", "faulty", "tripping",
                   "trips", "trip", "fuse", "fuse box", "cut out", "cutting out", "reset",
                   "test", "check", "fix", "mend", "repair", "replace", "element", "thermostat")
_HOT_FAULT_LEAK_ANSWER = (
    "Turn the cold feed off at the valve on the pipe into the tank and switch the immersion off "
    "at its wall spur, then open the hot taps to take the water level down; the tank holds "
    "scalding water, so let it cool before you touch it. A drip at a nut or a fitting is often a "
    "case of nipping the compression nut up a quarter turn, but if the body of the cylinder is "
    "wet, or the foam lagging is soaked through, the tank has gone and a plumber swaps it - that "
    "is a day's work, and it is not a job to leave running. Catch the water in a bucket or a "
    "towel, and if it is coming through a ceiling, turn the water off at the stopcock as well.")
_HOT_FAULT_COLD_ANSWER = (
    "Check the immersion heater's own fused spur switch on the wall first - the little switch "
    "beside the tank with a fuse in it - and then the timer or programmer, because a tank on a "
    "timer that has been knocked is the commonest reason for cold water. If the spur is on, take "
    "the cap off the immersion and press the red cut-out button on top of it, which trips when "
    "the element overheats. Still cold, or the fuse blows again, means the element has gone: an "
    "electrician or plumber drains the tank and swaps it in about an hour, and it is usually "
    "pounds rather than hundreds.")
# "how do i test an immersion heater" is asking for the test, not for a verdict, and the three
# fault answers below give a verdict. The test is a short list that can be done with a screwdriver
# and a cheap multimeter, so it gets its own arm.
_HOT_FAULT_TEST = ("test", "tests", "testing", "how do i know", "how can i tell", "check",
                   "checking", "multimeter", "continuity", "resistance", "prove", "proving")
_HOT_FAULT_TEST_ANSWER = (
    "Test the immersion in three steps, with the power off at the spur each time you touch the cap. "
    "First the "
    "supply: is the fused spur switched on and is its fuse sound, or does the breaker stay up when "
    "you reset it. Then the thermostat: take the round cap off the top of the cylinder, turn the "
    "dial right up and listen - a click means the thermostat works, and a cut-out button that has "
    "popped out means it tripped on overheat and needs pressing back in. Then the element itself: "
    "with the spur off and the two element wires off, a multimeter across the terminals should read "
    "somewhere between about 15 and 30 ohms; no reading at all means the element has gone.")
_HOT_FAULT_TRIP_ANSWER = (
    "Stop resetting it - an immersion element that trips the breaker has gone electrically, and "
    "resetting it each time is how a fuse board gets hot. Leave the circuit off at the spur, and "
    "get it swapped: the tank is drained, the old element unscrewed and a new one fitted, an "
    "hour's work for a plumber or electrician. Until then the boiler or the back-up heating is "
    "what you have for hot water.")

def _hot_water_fault(memory, reading):
    """A leak, no heat, or an element that trips the fuse: three faults with three answers."""
    said = " " + str((reading or {}).get("clean") or (reading or {}).get("text") or "").lower() + " "
    if any(" " + w + " " in said for w in _HOT_FAULT_LEAK):
        return _HOT_FAULT_LEAK_ANSWER
    if any(" " + w + " " in said for w in _HOT_FAULT_TEST):
        return _HOT_FAULT_TEST_ANSWER
    if any(" " + w + " " in said for w in ("tripping", "trips", "trip", "fuse", "fuse box",
                                           "breaker", "rcd", "mcb", "cut out", "cutting out")):
        return _HOT_FAULT_TRIP_ANSWER
    return _HOT_FAULT_COLD_ANSWER

ENTRIES.append(entry(
    "hot-water-faults",
    (("immersion", "immersion heater", "immersion switch", "immersion element", "immersion cap",
      "hot water cylinder", "hot water tank", "hot cylinder", "hot water cistern", "cylinder",
      "lagging", "airing cupboard"),
     ("not working", "isnt working", "isn't working", "not heating", "not heating up", "wont heat",
      "won't heat", "wont heat up", "won't heat up", "not getting hot", "not hot", "cold",
      "cold water", "only cold", "lukewarm", "tepid", "stopped working", "packed up", "broken",
      "fault", "faulty", "leak", "leaks", "leaking", "drip", "drips", "dripping", "puddle",
      "water coming out", "coming out", "soaked", "rusty", "tripping", "trips", "fuse",
      "cut out", "reset", "test", "fix", "mend", "repair", "replace", "element", "thermostat",
      "no hot water", "why")),
    _hot_water_fault,
    # the same tank words in the turn-off row, the boiler rows and the cheap-electrics rows: those
    # are different questions, and a gas cylinder or a fish tank is not this tank
    avoid=("turn off", "turning off", "switch off", "switching off", "shut off", "isolate",
           "isolation", "drain", "draining", "empty", "where is", "wheres", "where's", "valve",
           "back on", "refill", "fill back up", "cost", "much", "cheaper", "worth", "price",
           "boiler", "boilers", "radiator", "radiators", "central heating", "gas", "lpg",
           "calor", "bottle", "bottles", "camping", "caravan", "fish", "fish tank", "aquarium",
           "petrol", "diesel", "scuba", "oxygen", "diving", "shower", "washing machine",
           "dishwasher", "kettle", "insurance", "renting", "landlord"),
    bias=2))

# "how do i get power of attorney" is the life-admin row's question, and the test that said no
# entry should answer it was written before that row existed.
# "Is it worth servicing the washing machine" was answered with the cost of heating a wash, and
# "how often should i service my washing machine" with a shrug. A service is the job the line
# names, so one row owns the verdict and the interval for every machine in the house, and the
# boiler is the one machine where the answer is a yearly yes.
_SERVICE_WORDS = ("service", "services", "servicing", "serviced")


def _service_machine(reading):
    """The machine a service question is about, or "" when it names none of ours."""
    said = " " + " ".join(str(reading.get("clean") or "").split()) + " "
    for name in ("washing machine", "washer", "dishwasher", "tumble dryer", "dryer",
                 "oven", "fridge freezer", "fridge", "freezer"):
        # the plural ("boilers", "ovens") names the same machine, and the phrase names stay
        # whole inside a longer line ("get the tumble dryer serviced")
        if not re.search(r"\b" + re.escape(name) + r"s?\b", said):
            continue
        if name == "washer":
            return "washing machine"
        if name == "dryer":
            return "tumble dryer"
        return name
    return ""


def _a_service_worth(memory, reading):
    """The verdict, or the interval, for servicing the machine the line names."""
    asks = set(reading.get("asks") or ())
    words = set(reading.get("words") or ())
    said = str(reading.get("clean") or "")
    # a price is the cost row's question, and a how-to is the DIY row's
    if "how_much" in asks or "how do i" in said or "how can i" in said:
        return None
    if not (asks & {"yesno", "how_often", "recommend"} or "worth" in words
            or "worthwhile" in words or "point" in words):
        return None
    machine = _service_machine(reading)
    often = "how_often" in asks or "how often" in said
    if machine == "washing machine":
        if often:
            return ("There is no yearly service to book: a washing machine has no service "
                    "interval like a boiler's. What keeps it going is cleaning the filter, "
                    "leaving the door open to dry, and a hot 60C maintenance wash once a month, "
                    "with a descaler if your water is hard. Pay someone only when it is noisy, "
                    "leaking or not draining, and that is a repair rather than a service.")
        return ("No, a washing machine has no yearly service like a boiler's. What keeps it going "
                "is cleaning the filter, leaving the door open to dry, and a hot 60C maintenance "
                "wash once a month, with a descaler if your water is hard. Pay someone only when "
                "it is noisy, leaking or not draining, and that is a repair rather than a service.")
    if machine == "dishwasher":
        if often:
            return ("There is no yearly service to book: a dishwasher looks after itself if you "
                    "clean the filter once a month, keep the salt topped up in hard water and run "
                    "the hottest cycle now and then. A paid visit is only worth it if it smells "
                    "or will not drain, and then it is a repair.")
        return ("No, a dishwasher does not need a yearly service. Clean the filter once a month, "
                "keep the salt topped up if your water is hard, and run the hottest cycle now and "
                "then; a paid visit is only worth it if it smells or will not drain, and then it is "
                "a repair.")
    if machine == "tumble dryer":
        if often:
            return ("There is no yearly service to book: a dryer needs its lint filter emptied "
                    "after every load, its vent pipe cleared, and the condenser filter rinsed "
                    "once a month on a heat-pump model. Pay someone only if it takes two cycles "
                    "to dry, which is usually a blocked vent or a worn belt.")
        return ("No, a dryer does not need a yearly service. Empty the lint filter after every "
                "load, clear the vent pipe, and rinse the condenser filter on a heat-pump dryer "
                "once a month. Pay someone only if it takes two cycles to dry, which is usually a "
                "blocked vent or a worn belt.")
    if machine in {"oven", "fridge freezer", "fridge", "freezer"}:
        if machine == "oven":
            if often:
                return ("There is no yearly service to book: clean the shelves and the door glass, "
                        "run the pyrolytic setting if it has one, and leave the rest alone unless "
                        "it stops heating evenly. A paid oven clean is cleaning, not servicing.")
            return ("No, an oven does not need a yearly service. Clean the shelves and the door "
                    "glass, run the pyrolytic setting if it has one, and leave the rest alone "
                    "unless it stops heating evenly; a paid oven clean is cleaning, not servicing.")
        if often:
            return ("There is no yearly service to book: dust the coils at the back once a year, "
                    "keep the door seal clean, and leave a gap round it for the heat to escape. "
                    "Pay someone only when it stops holding temperature.")
        return ("No, a fridge or freezer does not need a yearly service. Dust the coils at the "
                "back once a year, keep the door seal clean, and leave a gap round it for the heat "
                "to escape; pay someone only when it stops holding temperature.")

# ---- the words on a lease, a service charge and a new build's snagging list ------------------
#
# People meet these words when they buy or rent a flat and ask what they mean: on main "what is a
# ground rent", "what is a lease", "how long is a lease", "what is a managing agent", "what is a
# service charge on a flat", "what is a freeholder", "what is an EPC", "what is gazumping" and
# "what is a snagging list" were all search hedges, while a bare "what is a service charge" is the
# restaurant's question and belongs to the tipping card. One table, one way in: the word is the key
# and the answer says what the thing is and the one number or trap that matters.
_PROPERTY_WORDS = (
    (("ground rent", "ground rents"),
     "Ground rent is the yearly charge a leaseholder pays to the freeholder for the land the flat "
     "stands on - often £50 to £250, though some newer leases set it much higher. Read the lease "
     "for how it reviews: one that doubles every ten years, or rises with the retail prices index, "
     "is a real problem, because a mortgage lender will refuse it and a buyer will too. Ask the "
     "seller for the last three years of demands."),
    (("service charge", "service charges", "maintenance charge", "maintenance charges",
      "management fee", "management fees", "estate charge", "estate charges"),
     "A service charge is your share of what the block costs to run: buildings insurance, the "
     "cleaner, the lift, the lights, the roof, and the managing agent's fee. It is not profit for "
     "the landlord - you are entitled to the yearly accounts and to challenge anything "
     "unreasonable at a tribunal - so ask for the last three years of it and what the reserve fund "
     "holds for big jobs. A charge that jumps in one year is usually a repair or an insurance "
     "renewal, and the accounts will say which."),
    (("managing agent", "managing agents", "management company", "managing company"),
     "The managing agent is the company the freeholder pays to run the block day to day: repairs, "
     "insurance, the service charge accounts and the cleaning. It is not the freeholder and it "
     "cannot sell you the freehold, but it is who you ring about the broken door. Ask for the "
     "agent's name and the last set of accounts before you buy, and put a complaint about the "
     "block in writing to the agent first, because the freeholder is only reachable through it."),
    (("freeholder", "freeholders"),
     "The freeholder owns the building and the land; a leaseholder owns the right to live in one "
     "flat for a set number of years. The freeholder's jobs are the structure and the outside, "
     "paid for by the service charge, and the leaseholders have the right to buy that freehold "
     "between them if enough of them want to."),
    # The words a first-time buyer meets in the paperwork, all of which were the honest pass on
    # main: "what is freehold" and "what is a title deed" among them. Each is a definition and
    # nothing else, so one line answers it and the property row's own fence keeps car leases and
    # restaurant service charges out.
    (("freehold",),
     "Freehold means you own the building and the land it stands on outright, with no end date and "
     "no ground rent or service charge to anyone. A house is usually freehold; a flat is usually "
     "leasehold, or the flat is leasehold and the freehold is owned by a company the flat owners "
     "share."),
    (("leasehold",),
     "Leasehold means you own the right to live in the property for the number of years left on the "
     "lease, not the land under it. You pay ground rent and a service charge to the freeholder, and "
     "the lease is the contract that says what you may and may not do - which is why the years left "
     "matter so much when you sell."),
    (("covenant", "covenants", "deed of covenant", "deeds of covenant", "restrictive covenant",
      "restrictive covenants"),
     "A covenant is a promise written into a deed. In a lease it is what you must and must not do "
     "(no subletting, keep the hallway clear); on a freehold it is usually a restriction on the "
     "land, such as not running a business from the house, and it can still be enforced fifty years "
     "on. A deed of covenant on its own is also the name for a signed promise to pay a fixed sum - "
     "often to a charity, so it can claim the tax back."),
    (("easement", "easements"),
     "An easement is a right to use someone else's land for one purpose: a right of way across a "
     "drive, drains running under a neighbour's garden, or access to lay pipes. It stays with the "
     "property rather than the person, so it is on the title and a buyer's solicitor will find it. "
     "You cannot build over one, and it needs registering to be safe."),
    (("title deed", "title deeds", "title register", "land registry"),
     "The title deeds are the documents that prove who owns a property. In England and Wales they "
     "are now held electronically by HM Land Registry, so there is nothing for you to keep in a "
     "safe - a copy of the title register can be downloaded for a few pounds. It lists the owner, "
     "the price last paid, the boundaries on a map and anything registered against the property, "
     "such as a mortgage or a covenant."),
    (("conveyancer", "conveyancers", "conveyancing"),
     "A conveyancer is the solicitor or licensed conveyancer who does the legal work of buying or "
     "selling a home: searches, the contract, the lease or title, the mortgage conditions and the "
     "money on completion. Fees are usually £800 to £2,000 plus searches and VAT; ask for the total "
     "quoted for your property, and use one who is on your lender's panel if you have a mortgage."),
    # "what is a lease extension" was reaching the row below and getting the answer about how
    # long a lease is, which is the neighbour's question: what the thing is comes first, and the
    # length is what makes it worth doing.
    (("what is a lease extension", "whats a lease extension", "lease extension mean",
     "lease extension meaning", "what does lease extension mean", "define lease extension"),
     "A lease extension is a new, longer lease on the same flat: you pay the freeholder a premium "
     "and the years are added, 90 on top of what is left if you use the legal right, which you "
     "have once you have owned the flat for two years. Your solicitor serves the notice and the "
     "new lease is registered at the Land Registry; the premium is the negotiation. Do it before "
     "the lease drops under about 80 years, because the price climbs sharply after that."),
    (("lease extension", "extend my lease", "extend the lease", "extending my lease",
      "short lease", "lease length", "how long is the lease", "how long is my lease",
      "how long is a lease", "how long a lease", "how many years left on the lease",
      "how many years left on my lease", "years left on the lease",
      "years are left on the lease", "years are left on my lease"),
     "A lease is your right to live there for a fixed number of years, and the length is what "
     "matters at the end: below about 80 years it gets expensive to extend and some lenders will "
     "not touch it. After two years of owning it you have the right to add 90 years at a "
     "peppercorn rent, which is a legal route rather than a favour, so a short lease is a "
     "negotiating point on the price and not a reason to walk away. Get the premium quoted by a "
     "surveyor who does lease extensions before you agree anything."),
    (("what is a lease", "whats a lease", "what is a leasehold", "leasehold mean",
      "leasehold meaning"),
     "A lease is the document that gives you the right to live in a flat for a set number of "
     "years - 99, 125 and 999 are the usual lengths - and it comes with ground rent, a service "
     "charge and rules about the building. You own the inside of the flat and the right to live "
     "there; the freeholder owns the structure and the land. The two numbers to check are how many "
     "years are left and what the ground rent does."),
    (("epc", "energy performance certificate", "energy performance"),
     "An EPC is the energy rating for the property, A to G, and it has to be done before a home is "
     "sold or rented, and it lasts ten years. E is the lowest rating a landlord may let a home on "
     "in England and Wales, so a flat rated F or G is either a bargaining point or a bill for "
     "insulation and a new boiler. Read the recommendation list on page three, because that is "
     "where the cheap wins are."),
    (("gazumping", "gazumped", "gazumping mean"),
     "Gazumping is a seller accepting a higher offer after they had already accepted yours, which "
     "in England and Wales is legal until contracts are exchanged - nothing is binding before "
     "that, and you can lose the survey and legal fees you have paid. The defences are to ask for "
     "the property to be taken off the market in writing and to move fast towards exchange; in "
     "Scotland the offer is binding much earlier, so the risk is different there."),
    (("snagging list", "snagging", "snags list"),
     "A snagging list is the list of small faults in a new build - a door that rubs, a crooked "
     "tile, a scratch on the worktop - which you hand to the developer to put right. Do it in the "
     "first days after you get the keys rather than at the end of the year, with a photo of each "
     "snag and where it is, and keep the emailed copy: the warranty usually gives you two years "
     "for this kind of thing, and the list is what starts the clock."),
    (("peppercorn", "peppercorn rent"),
     "A peppercorn rent is a ground rent of nothing at all - the name is the old token payment, "
     "and it means the lease has no ground rent to pay. A lease extended the statutory way ends up "
     "on one, so a peppercorn ground rent in a lease is a good sign rather than a puzzle."),
)

# A definition ask, in the shapes people use for one. A job ("how do i extend my lease"), a
# decision ("should i buy the freehold") and a price question about a bill all belong to other
# cards, so this row only answers the word.
PROPERTY_DEFINITION_ASKS = ("what", "whats", "what is", "what are", "mean", "means", "meaning",
                            "define", "explain", "how long", "how many", "how much is",
                            "how much are",
                            "how does", "why", "worth", "difference", "bad", "good", "do i need")


# "Service charge" is the one word here that is also ordinary at a restaurant till, where it is a
# tip already added to the bill and the tipping card defines it. So the bare word only counts when
# the line says which one it is: a flat, a block, a lease, a landlord or the maintenance of a
# building. "what is a service charge on a flat" and "how much is the service charge on a flat"
# are this card's; a bare "what is a service charge" stays with the restaurant.
PROPERTY_SERVICE_WORDS = ("service charge", "service charges", "maintenance charge",
                          "maintenance charges", "management fee", "management fees",
                          "estate charge", "estate charges")
PROPERTY_SERVICE_CONTEXT = ("flat", "flats", "block", "blocks", "lease", "leasehold",
                            "freeholder", "freehold", "building", "landlord", "agent",
                            "estate", "residents", "maintenance", "ground rent", "property",
                            "buying", "bought", "mortgage", "conveyancer", "solicitor")


def _property_word(understood):
    """The word the line asks about, answered in the first sentence."""
    words = [str(word).lower() for word in ((understood or {}).get("words") or ())]
    text = " ".join(words)
    for keys, reply in _PROPERTY_WORDS:
        for key in keys:
            if not (" " in key and key in text) and key not in words:
                continue
            if key in PROPERTY_SERVICE_WORDS and not any(
                    word in words or (" " in word and word in text)
                    for word in PROPERTY_SERVICE_CONTEXT):
                continue
            return reply
    return None


ENTRIES.append(entry(
    "machine-service-worth",
    (("washing machine", "washer", "dishwasher", "dishwashers",
      "tumble dryer", "dryer", "dryers", "oven", "ovens", "fridge", "fridge freezer", "freezer"),
     _SERVICE_WORDS),
    _a_service_worth,
    # a price is the cost row's, and a fault is the repair row's
    avoid=("cost", "much", "price", "quote", "broken", "not heating", "not draining", "leaking",
           "noisy", "error", "repair"),
    bias=3))

# A machine that keeps going wrong, or that has broken and been mended more than once, is a
# different question from one that has stopped dead, and it had no answer at all: the
# machine-stopped row stands these lines down on purpose ("my washing machine breaks down every
# month" is a habit, not a fault, and the plug fuse answers nothing) and the repeat-fault entry in
# consumer.py keeps "washing machine" and "boiler" out, because the trades there are the machine's.
# Both halves of the line were read and nobody owned it, so "my washing machine keeps breaking
# down" got "Thanks for telling me" and "breaks down every month" got "That's a habit now".
_MACHINE_KEEPS = ("keeps breaking", "keeps breaking down", "keep breaking",
                  "keeps going wrong", "keeps cutting out", "keeps switching off",
                  "keeps stopping", "always breaking", "always goes wrong",
                  "breaks down every", "broken down every", "breaking down every",
                  "goes wrong every", "gone wrong every",
                  # a repair named as a repeat, not a machine that has simply broken again:
                  # "my fridge broke again" is the first-checks answer above, and the shop's
                  # attempts are the question once the person says there have been some
                  "repaired twice", "repaired again", "been repaired", "had it repaired",
                  "repaired it twice", "same fault", "same thing keeps", "went again")

ENTRIES.append(entry(
    "machine-keeps-failing",
    (_MACHINE_WORDS, _MACHINE_KEEPS),
    "A machine that keeps going wrong is not bad luck, and it is not your job to keep paying for "
    "repairs: a repair has to be done properly and within a reasonable time, so when the same "
    "fault comes back you can refuse another repair and ask for a refund or a price reduction "
    "instead. Put it in writing, list each date and what went wrong, and keep the receipts - "
    "within six months of buying, the shop has to prove the fault was not there when they sold "
    "it. Past six months, an independent report saying the fault was built in is what wins it.",
    # the fix-it-yourself lines are the machine row's, and a machine that is simply stopped is the
    # first-checks answer, not the shop's
    ask=("keeps", "keep", "always", "every", "repaired", "same fault", "broken down",
         "breaks down", "breaking down", "went again"),
    # A part that keeps failing is that part's own answer: "my washing machine belt keeps
    # slipping" is the belt, and "refuse another repair" is no advice about a belt. The trades, an
    # upgrade, a leak, a smell and the landlord are the entries next door's.
    avoid=("belt", "belts", "pump", "pumps", "brush bar", "filter", "filters", "door", "hose",
           "seal", "seals", "element", "thermostat", "hinge", "hinges",
           "leak", "leaks", "leaking", "smell", "smells", "noisy", "noise", "rattling",
           "grinding", "sparking", "trips", "tripping", "not draining", "not spinning",
           "not heating", "not drying", "error", "blocked", "clogged", "scale",
           "landlord", "landlords", "landlady", "letting agent", "tenant", "council",
           "engineer", "quote", "quotes", "call out", "callout", "scrap", "new one", "buy a new",
           "guarantee", "warranty", "shirt", "shirts", "ironing")))

# The pair on the face and the glass in the hand are one word to the matcher ("glasses" is a
# loose form of "glass"), so the row that clears up broken glass has to stand down when the
# plural, or the name of the pair, is what the line says. clothing.py's two spectacles rows carry
# the other half of the same guard: they stand down for "my glass broke" and answer "my glasses
# broke", which is where a pair that will not go on the face belongs.
_A_PAIR_OF_GLASSES = re.compile(r"\bglasses\b|\bspectacles\b|\bspecs\b|\beyeglasses\b",
                                re.I)


def _not_a_pair_of_glasses(understood):
    """False when the line is about spectacles rather than the glass somebody was drinking from."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text")).lower()
    return not _A_PAIR_OF_GLASSES.search(said)


# A glass that has broken on the floor is not a window and not a pair of spectacles: "i broke my
# glass at home" and "how do i get broken glass off the floor" were both told to take it to an
# optician. Clearing it up is what is asked, and it is a safety job before it is a disposal one.
ENTRIES.append(entry(
    "broken-glass-on-the-floor",
    (("broken glass", "smashed glass", "glass on the floor", "glass in the sink",
      "shard", "shards", "splinter of glass", "splinters of glass",
      "glass", "glasses", "tumbler", "wine glass", "pint glass", "drinking glass"),
     ("broke", "broken", "smashed", "shattered", "dropped", "dropped it", "knocked over",
      "floor", "sweep", "swept", "clear up", "clearing up", "clean up", "pick up",
      "pick it up", "off the floor", "in the kitchen", "at home", "cut myself",
      "keep cutting myself")),
    "Sweep it rather than wipe it: a brush and dustpan, then a torch held flat on the floor shows "
    "the bits the brush missed and a damp piece of kitchen paper picks up the dust. Wrap the glass "
    "in newspaper or an old tea towel and put it straight in the outside bin, not the kitchen one "
    "and not the recycling, and keep shoes on in there until the floor has had the torch over it. "
    "A cut from glass that will not stop bleeding after ten minutes of pressing needs looking at.",
    # a window or a pane is the glazier's row, a windscreen is the car's, a pair of spectacles is
    # the optician's, and where a glass goes after it is cleared up is the recycling row's.
    # "my glasses", "pair of glasses" cannot be avoided here: "glass" and "glasses" are loose
    # forms of one word, so the phrase would stand this row down on its own line.
    avoid=("optician", "spectacles", "specs", "lens", "lenses", "windscreen", "windshield",
           "pane", "panes", "window", "windows", "double glazing", "bottle bank",
           "recycle", "recycling", "recycled", "bottle"),
    guard=_not_a_pair_of_glasses))


# "do i need a plumber" comes after the steps, or on its own from somebody weighing up a job: the
# question is whether the work is theirs to finish, so the card is where the job stops being DIY
# and what to ask before agreeing a price. Kept out of the cost rows by the avoid list, and out of
# the gas and electrics rows because those name the trade they want, not this decision.
# The ask is the question shape, not the noun: "i need a plumber" is somebody telling you their
# day, and the chat module's "worth doing, what first?" is the right answer to it.
_NEED_A_TRADE_ASK = (
    "do i need", "do we need", "do you need", "should i get", "should i call", "worth getting",
    "is it worth getting", "get someone in", "get a man in", "call one", "call someone",
    "notifiable", "sign off", "certificate", "or a professional", "or a pro", "or a proper",
    "or a trade", "or a plumber", "or an electrician")

ENTRIES.append(entry(
    "need-a-plumber",
    (("plumber", "plumbers", "plumbing", "pipe work", "pipework", "central heating engineer"),
     _NEED_A_TRADE_ASK),
    "Not for the small jobs: a dripping tap, a loo that keeps running, a blocked trap, a ball "
    "valve or a washing-machine hose is an hour with a spanner and a few pounds in parts. Call "
    "one when the water will not stop at the stopcock, the leak is under a floor or inside a "
    "wall, a joint still weeps after two goes, or the job is a new bathroom or a boiler swap. "
    "Fitting an appliance is usually cheaper from the shop that sells it, so ask them first. "
    "Then get a fixed call-out price before they come, and say what the fault is doing so the "
    "price is for this job and not for a look.",
    # "how much does a plumber charge" is the cost question, a burst is an emergency, and a line
    # that names the job has a card of its own that starts with the fix: the decision card is for
    # the ask with no job in it, or for the job whose card is about something else (a new bath).
    avoid=("cost", "much", "price", "quote", "charge", "charges", "rates", "hourly", "day rate",
           "emergency", "burst", "flooding", "banging", "no hot water", "no heating",
           "tap", "taps", "dripping", "drip", "leak", "leaks", "leaking", "loo", "toilet",
           "cistern", "trap", "blocked", "drain", "drains", "radiator", "sink",
           # a gas appliance is the Gas Safe row's, and every one of these had a good card of its
           # own on main ("can i fix that myself or do i need a plumber" after a boiler at
           # pressure: the case is the engineer's, and that row says so)
           "boiler", "boilers", "gas", "hob", "cooker", "gas fire", "gas safe",
           # the DIY half of the question is the "can i fix it myself" row's, and that row is the
           # better answer when the line asks both
           "myself", "can i fix", "fix it", "do it", "top it up"),
    bias=2))

ENTRIES.append(entry(
    "need-an-electrician",
    (("electrician", "electricians", "sparky", "sparkies", "electrical work", "rewire",
      "socket", "sockets", "socket face", "light fitting", "light fittings", "fused spur",
      "new circuit"),
     _NEED_A_TRADE_ASK + ("how do i", "how can i", "can i", "is it safe", "safe to")),
    "No for a switch, a socket face, a light fitting or a fused spur, so long as the circuit is "
    "off at the consumer unit and the wires go back as they came out. You need one for anything "
    "inside the consumer unit, a new circuit, a shower or garden supply, or anything that smells "
    "of burning or has scorched a plug. A new circuit or work in a bathroom or kitchen also "
    "needs a certificate, so use a registered electrician, get the certificate price with the "
    "job price, and agree the whole figure before they come.",
    # the lines that name the fault have their own cards (a tripping circuit, a burning smell)
    avoid=("cost", "much", "price", "quote", "charge", "rates", "hourly", "day rate",
           "keeps tripping", "tripping", "trips", "fuse box", "smell", "smells", "buzzing",
           "flickering", "flicker", "cracked", "crack", "broken", "loose", "sparking",
           "sparks", "burnt", "burn", "burning", "melted", "scorched", "hot",
           # a fault already named, and the follow-up that asks whether it is still safe to use,
           # are the safety card's: "the plug socket is cracked" then "can i still use it" was
           # answered from memory until the word socket reached this row
           "still use", "use it", "safe", "dangerous", "unsafe"),
    bias=2))


# Paper is the one thing in a house that ages in plain sight: the books go brown, the letters go
# yellow, the photos fade and the musty smell arrives before the colour does. None of it had an
# answer. "how do i stop my book pages going yellow" got the read-more habit card ("Keep the book
# where you idle - beside the kettle"), "how do i keep old letters from going yellow" got the
# four-paragraph complaint letter, "how do i store old books" was a punt, and "my old books smell
# musty" got the hotel card, because the word "booking" and the word "books" are the same word to
# a stemmer.
_PAPER_THINGS = ("book", "books", "page", "pages", "paper", "papers", "letter", "letters",
                 "photo", "photos", "photograph", "photographs", "print", "prints", "album",
                 "albums", "postcard", "postcards", "newspaper", "newspapers", "comic", "comics",
                 "diary", "diaries", "certificate", "certificates", "magazine", "magazines",
                 "keepsake", "keepsakes", "memorabilia", "scrapbook", "scrapbooks")
_PAPER_AGEING = ("yellow", "yellowing", "yellowed", "gone brown", "going brown", "browned",
                 "browning", "fading", "faded", "fade", "foxing", "discoloured", "discolored",
                 "ageing", "aging", "old", "older", "oldest", "musty", "fusty", "smell",
                 "smells", "smelly", "storage", "store", "storing", "stored", "keep",
                 "keeping", "preserve", "preserving", "protect", "conserving", "last longer")
_PAPER_PHOTOS = ("photo", "photos", "photograph", "photographs", "print", "prints", "album",
                 "albums", "negatives", "slides")
_PAPER_SMELL = ("musty", "fusty", "smell", "smells", "smelly", "damp", "mildew", "mouldy",
                "moldy", "mould", "mold", "foxing")


def _keeping_paper(memory, understood):
    line = " " + str((understood or {}).get("clean") or (understood or {}).get("text")
                     or "").lower() + " "
    if any((" " + word + " ") in line or line.rstrip().endswith(" " + word)
           for word in _PAPER_SMELL):
        return ("Musty paper is damp paper, and the smell is mould growing in it: stand the books "
                "or letters up with the pages fanned in a dry room for a day or two - not in "
                "sunlight, which yellows them faster - then keep them somewhere dry and steady. A "
                "sachet of silica gel in the box, a cupboard inside the house rather than the "
                "loft, garage or cellar, and a dehumidifier in a room that has had a leak will "
                "stop it coming back. Don't wipe them with bleach or a wet cloth: it takes the "
                "print with it.")
    if any((" " + word + " ") in line or line.rstrip().endswith(" " + word)
           for word in _PAPER_PHOTOS):
        return ("Prints fade from light and from the plastic in old albums, so keep them out of "
                "sunlight, in acid-free sleeves or a proper album rather than a PVC one, and scan "
                "the ones that matter - a digital copy is the only version that cannot fade. A "
                "framed photo wants UV-filtering glass and a wall that never gets direct sun.")
    return ("Cheap paper is made from wood pulp, and the lignin in it turns acidic and brown as it "
            "sits - light, heat and damp speed it up, which is why the box in the loft goes first. "
            "So keep paper cool, dry, dark and steady: a cupboard inside the house, not the loft, "
            "shed or cellar; acid-free folders and boxes rather than polythene bags, which trap "
            "damp; no sellotape and no lamination, both of which stain and cannot be undone. "
            "Yellowing that has already started can be slowed, not reversed.")


ENTRIES.append(entry(
    "paper-going-yellow",
    (_PAPER_THINGS,
     _PAPER_AGEING),
    _keeping_paper,
    # a stain on a page is the cleaning row's question, and a book to read, a book club and a
    # present are the reading rows'
    avoid=("clean", "cleaning", "stain", "stains", "spill", "spilt", "spilled", "coffee",
           "wet", "water damage", "ink", "mould stain", "sticky", "dust", "dusting",
           "recommend", "recommendation", "suggest", "what should i read", "good book",
           "book club", "book clubs", "reading group", "reading club",
           "for my mum", "for my dad", "for her", "for him", "present", "gift",
           "read to", "reading to", "bedtime story", "learn to read", "struggling", "dyslexia",
           "how do i read", "more books", "start reading", "get back into reading",
           # not "booking"/"booked": an avoid word is stemmed, so "booking" is the word "book" and
           # it fenced every line about books - which is the whole row
           "flight", "hotel", "table", "restaurant", "ticket",
           "tickets", "appointment", "doctor", "dentist",
           # a certificate you need a copy of, a passport and a will are the admin rows'
           "passport", "birth certificate", "marriage certificate", "will", "probate",
           "how much is", "worth", "sell", "selling", "value",
           # a screen is not paper. The row keys "photos", "print" and "old", so without these
           # "how do i get my photos off my old phone", "how do i scan old photos" and "how do i
           # delete old photos from google photos" all got the fading-prints card - and the last
           # one was a punt on main turned into a confident wrong answer
           "phone", "iphone", "android", "mobile", "laptop", "computer", "cloud", "icloud",
           "google photos", "whatsapp", "storage", "delete", "deleting", "deleted", "scan",
           "scanning", "scanner", "backup", "back up", "download", "upload", "screenshot",
           "camera roll", "gallery", "app", "apps", "sim", "sd card", "usb", "album on"),
    bias=2))


# `home_craft.entries()` is called here, at the end, because the rows it returns are built with
# the helpers and tables above: they hold references to them, and the import cannot be at the top
# of the file without a circle. Putting the rows in front of the ones appended above keeps
# ENTRIES in exactly the order it had when the whole list was written in this file.
from .home_craft import entries as _craft_entries

ENTRIES.append(entry(
    "property-word",
    (tuple(key for keys, _ in _PROPERTY_WORDS for key in keys), PROPERTY_DEFINITION_ASKS),
    lambda memory, understood: _property_word(understood),
    bias=1,
    # a lease on a car or a van is hire purchase, a service charge on a restaurant bill is a tip,
    # and a freeholder in a line about a tenancy deposit is not the word being asked about
    avoid=("car", "cars", "van", "vans", "vehicle", "hire purchase", "contract hire",
           "leased car", "lease car", "car lease", "rental", "phone", "laptop", "equipment",
           "restaurant", "restaurants", "bill", "tip", "tipping", "hotel", "cafe",
           "how do i", "how can i", "should i", "help me", "what can i do",
           "my landlord", "landlord", "tenant", "tenants"),
))
# A machine that feels hot is its own question, and it had none: "my washing machine gets hot on
# the outside" and "the drum of my washer is hot" were a listening reply and the unbalanced load
# answer. Warmth is normal; a hot plug or a burning smell is not. It is appended here, after the
# rows of home_craft, because those rows were written in this file first and keeping ENTRIES in
# that order is what the move promised.
ENTRIES.append(entry(
    "machine-hot",
    # no bare "machine" or "appliance": a sewing machine, a coffee machine and a dishwasher are
    # not washers, and "my sewing machine gets hot" was answered as one
    (("washing machine", "washer", "washer dryer", "tumble dryer", "dryer",
      "washing machine door", "the washer", "my washer"),
     ("hot", "warm", "warm to the touch", "hot to the touch", "too hot", "gets hot",
      "getting hot", "is hot", "overheating", "overheated", "burning", "burning smell",
      "smell of burning", "smells of burning", "smells hot", "very warm")),
    ("Warm on the outside after a hot wash is normal, so a washer or dryer that is only a little "
     "warm and works fine needs nothing. What is not normal is a plug, socket or cable that is "
     "hot, a burning smell, a door glass too hot to touch, or the machine tripping the fuse: "
     "switch it off at the wall, unplug it and get it looked at rather than using it again. "
     "Otherwise give it air - a hand's gap behind and above, the fluff filter clear, and no "
     "cupboard door shut on a dryer while it runs."),
    # a wash temperature, a spin fault, a smell inside the drum and a dryer that will not heat are
    # all other rows; "hot" is the whole point of this one
    avoid=("what temperature", "which temperature", "what temp", "how hot", "degrees",
           "30c", "40c", "60c", "90c", "wash temperature", "wont spin", "won't spin",
           "not spinning", "soaking", "smells", "smelly", "musty", "inside the drum",
           "wont heat", "won't heat", "not heating", "no heat", "takes ages", "not drying",
           "leak", "leaking",
           # a plug, socket or lead that is hot is the hot-plug answer's line, and it says more
           # about the plug than this row's one clause does
           "plug", "plugs", "socket", "sockets", "cable", "cables", "lead", "wire",
           "wiring", "charger", "extension lead",
           # and a machine of another kind is another answer entirely
           "sewing", "coffee", "drilling", "milling", "sewing machine", "coffee machine",
           "treadmill", "dishwasher", "vacuum", "hoover", "mower", "car")))

# --- keeping the place tidy is a routine, not a clean --------------------------------------
# "how do i keep my house tidy", "how do i tidy up quickly", "how do i stop my house getting messy"
# and "how do i keep on top of tidying" were three different punts and a plan about tomorrow's three
# tasks: none of them is a cleaning question, so no cleaning row could answer them. The row is the
# habit, and the rooms with their own cards keep them.
ENTRIES.append(entry("keeping-on-top-of-the-house",
      (("tidy", "tidying", "tidy up", "mess", "messy", "clutter", "housework", "cluttered"),
       ("keep", "keeping", "stays", "stay", "on top of", "every day", "daily", "routine",
        "always", "never", "quickly", "habit", "stop")),
      "Ten minutes a day beats one big clean: pick a fixed time - before bed is the easy one - and "
      "do the surfaces in one room and the washing-up, so nothing piles up. Give everything a home, "
      "a box, a hook or a shelf, and anything without one goes out. One load of washing a day beats "
      "a mountain at the weekend, and a basket at the bottom of the stairs takes the things that "
      "belong in another room.",
      avoid=("clean", "cleaning", "cleaner", "scrub", "bleach", "disinfect", "hoover", "vacuum",
             "mop", "spring clean", "deep clean", "oven", "fridge", "bath", "toilet", "sink",
             "kitchen", "bathroom", "garage", "shelf", "shelves", "storage", "where do i put",
             "who should", "fair", "does nothing", "chores fairly", "split the jobs", "job list",
             "office", "desk at work", "car", "garden", "shed", "wardrobe", "declutter",
             "clear out", "skip", "junk", "moving", "move house", "packing")))

# A fence, a hedge or a garden wall on a boundary is the deeds' question ("who owns it"), not the
# Party Wall Act's, and the party-wall row shares the word "boundary" with it.
_A_BOUNDARY_THING = re.compile(
    r"\b(?:fence|fences|hedge|hedges|garden wall|boundary wall|retaining wall|wallpaper)\b", re.I)


def _not_a_boundary(understood):
    """False when the line is about a fence, a hedge or a garden wall rather than a party wall."""
    if not isinstance(understood, dict):
        return True
    clean = str(understood.get("clean") or understood.get("text") or "")
    return not _A_BOUNDARY_THING.search(clean)


# --- the words in a house purchase ---------------------------------------------------------
# Two words in the paperwork of buying a house that people sign past. "what is a party wall" was
# answered with a dress code and "what is a survey" with a search hedge, and both are definitions
# with a step attached, so each answer says what the thing is and then what to do about it.
ENTRIES.append(entry(
    "party-wall",
    (("party wall", "party walls", "party wall agreement", "party wall award",
      "shared wall", "shared walls", "party wall notice"),
     ("what is", "whats", "what does", "mean", "means", "do i need", "notice", "agreement",
      "award", "neighbour", "neighbours", "neighbor", "extend", "extension", "loft",
      "works", "builder", "dispute", "cost", "surveyor", "act")),
    "A party wall is a wall, floor or ceiling that two properties share, or a wall that stands "
    "on the boundary between two gardens, and it comes with its own law: the Party Wall etc. Act "
    "1996. If you are doing work on one - a loft, an extension, a new chimney breast, digging "
    "foundations within three metres of next door - you serve a notice on the neighbour two "
    "months before, and a week before for a simple party wall job. If they agree in writing the "
    "two of you can go ahead; if they object, each side appoints a surveyor who sets a party wall "
    "award saying how the work is done and who pays. Doing it without the notice is the mistake: "
    "the neighbour can go to court and stop the job.",
    # a boundary fence, a dividing hedge and a garden wall that is not shared are other questions
    avoid=("fence", "fences", "hedge", "hedges", "boundary", "garden wall", "retaining wall",
           "wallpaper", "party decorations", "birthday"),
    # The avoid list alone was not enough: the row won "what is a boundary fence" on the shared
    # word "boundary" and then stood down, and a row that stands down leaves nothing behind -
    # the deeds answer that had it on main was never asked. A guard is read before the ranking,
    # so the row never enters it and the deeds row answers as it did.
    guard=_not_a_boundary,
    bias=1))

# The rows of home_craft.py go in front of the ones appended below, which is the order the whole
# list had when it was still written in this file. The call sits here, after the rows the guards
# and helper tables above are built from, because the import cannot be at the top without a circle.
ENTRIES[:] = _craft_entries() + ENTRIES


# --- the words on a tenancy and on the money round a flat ------------------------------
# Seven more that main missed, and two it answered with the card next door: a tenancy deposit
# got the card-payment £100 rule, contents insurance got the buildings card, and a break
# clause got the grammar answer about clauses.
_HOME_WORDS_2 = (
    (("ground rent",),
     "Ground rent is the yearly charge a leaseholder pays the freeholder for the land the flat "
     "stands on, on top of the service charge: often £100 to £300, and now usually a fixed sum "
     "written into the lease. It is not the same as the service charge, which pays for the "
     "building, and a lease with ground rent that doubles every ten years is the one to argue "
     "about before you buy.",
     ("my", "how do i", "should i", "increase", "doubled", "doubling", "demand", "arrears",
      "paying", "pay it", "not paying")),
    (("tenancy deposit", "deposit scheme", "deposit protection"),
     "A tenancy deposit is the money you pay a landlord at the start to cover damage or unpaid "
     "rent, usually five weeks' rent, and it is not the landlord's to keep: in England and Wales "
     "it must be put in a government-backed protection scheme within 30 days and you get a "
     "certificate saying where. If it was not protected, or your landlord keeps it for wear and "
     "tear, you can claim up to three times the deposit.",
     ("not paid back", "not returned", "withheld", "kept my", "claim", "how do i", "should i",
      "my landlord", "how much", "returned")),
    # "sinking fund" itself is money_words.py's, and the leasehold sense of it is the same
    # money: two cards for one fact is what the deck's duplicate check is for. The two names a
    # leaseholder is likelier to meet in their own paperwork are here, because the savings card
    # does not know them.
    (("reserve fund", "major works fund", "reserve funds"),
     "A reserve fund - a sinking fund, in a block of flats - is money the leaseholders pay into "
     "each month so the big jobs of the next twenty years, a new roof or lifts or external paint, "
     "are already paid for when they come. It is separate from the service charge for this year's "
     "running costs, and the balance shows in the annual accounts, so check it before you buy a "
     "leasehold flat.",
     ("my", "how do i", "should i", "start one", "set one up", "for a car", "house deposit",
      "savings")),
    (("break clause", "breakclause"),
     "A break clause is a term in a tenancy or a commercial lease that lets either side end it "
     "early, on a date and with notice written into the contract: you still pay the rent until "
     "that date, and the notice is often two months. Ask exactly how the notice has to be given, "
     "in writing, and diary the day two months before the break date.",
     ("grammar", "sentence", "verb", "clause in", "relative clause", "subordinate", "my", "how do i",
      "should i", "can i leave", "exercise it")),
    (("inventory", "check in report", "check-in report"),
     "An inventory is the list of what was in the flat and what condition it was in when you "
     "moved in, with photos, and it is the document the deposit is judged against at the end. "
     "Check it against the flat on the day, write down anything missing or already damaged, date "
     "and sign it, and photograph any marks before you send it back.",
     ("stock", "shop", "business", "warehouse", "my", "how do i", "should i", "do one")),
    (("contents insurance", "contents cover"),
     "Contents insurance covers the things in the home: furniture, clothes, a laptop, a bike if "
     "it is listed, the damage a leak or a fire does to them - where buildings insurance covers "
     "the structure itself, which is the landlord's job in a rented flat. Add up what it would "
     "cost to replace everything new, keep receipts for anything over a few hundred pounds, and "
     "check the single-item limit before you assume the bike is covered.",
     ("my", "how do i", "should i", "claim", "not paying", "renew", "cancel", "cheapest",
      "compare", "do i need")),
)

HOME_DEFINITION_ASKS_2 = ("what", "whats", "what is", "what's", "what are", "mean", "means",
                          "meaning", "define", "definition", "explain", "stand for", "stands for")


def _home_word_2(memory, understood):
    text = understood.get("clean") or ""
    words = understood.get("words") or []
    for keys, reply, avoid in _HOME_WORDS_2:
        if not any(key in text or key in words for key in keys):
            continue
        if any(word in text or word in words for word in avoid):
            continue
        return reply
    return None


ENTRIES.append(entry(
    "home-word-2",
    (tuple(key for keys, _, _ in _HOME_WORDS_2 for key in keys), HOME_DEFINITION_ASKS_2),
    _home_word_2,
    bias=2,
    avoid=("how do i", "should i", "help me", "what can i do"),
))

# "what do i do with old carpet" was a punt, and it has three real answers: the council's bulky
# collection, the household waste site, and the piece that is still good going down under gravel
# as a weed membrane. Fitters and charity shops take clean offcuts.
ENTRIES.append(entry(
    "old-carpet",
    (("old carpet", "old carpets", "a carpet", "the carpet", "carpets", "carpet",
      "underlay", "rug", "rugs", "offcuts", "offcut"),
     ("get rid of", "throw away", "throwing away", "throw out", "thrown out", "dispose",
      "disposal", "dump", "tip", "waste", "recycle", "recycling", "bin", "rubbish",
      "what do i do with", "how do i get rid", "where can i take", "skip", "council",
      "old", "replace", "replacing", "ripping up", "taken up")),
    ("Book a bulky waste collection with your council, usually £15-£40 for a roll, or take it to "
     "the household waste site yourself - it will not go in the wheelie bin. A fitter who is "
     "laying the new one will often take the old one away for a small charge, and a charity shop "
     "takes a clean rug. A sound piece is worth keeping: laid upside down under gravel or bark it "
     "stops weeds for years."),
    bias=2,
    # cleaning a carpet, a stain, a carpet that smells and buying one are other questions
    avoid=("clean", "cleaning", "cleaned", "shampoo", "stain", "stains", "smell", "smells",
           "smelly", "steam", "vacuum", "hoover", "buy", "buying", "cheap", "price",
           "which carpet", "best carpet", "fitted", "measure")))


# Soaked trainers and boots had no row at all: "how do i dry wet shoes overnight" and "how do i
# dry my trainers" were both the "I'd rather not guess" hedge, on a question with five real steps.
# The smell of a shoe and the repair of one are other cards, so they are fenced out.
ENTRIES.append(entry(
    "dry-wet-shoes",
    (("shoe", "shoes", "trainers", "boots", "sneakers", "runners", "football boots", "wellies",
      "wellingtons", "plimsolls", "slippers", "walking boots", "hiking boots", "school shoes"),
     ("wet", "wet through", "soaked", "soaking", "soggy", "drying", "dry", "dried", "overnight",
      "rained", "rain", "puddle", "puddles", "snow", "washed", "washing machine", "damp",
      "in the rain", "damp out")),
    ("Take the insoles and laces out, stuff the shoe with newspaper or kitchen roll, and change "
     "the paper after an hour; that pulls the water out far faster than air alone. Then leave them "
     "in a warm room with a bit of air moving, and most trainers are dry overnight. Keep leather "
     "and glued soles off a radiator and out of a tumble dryer, which cracks the leather and "
     "softens the glue; a hair dryer on the cool setting is fine for the last damp patch. If they "
     "still smell of damp afterwards, sit a sock of bicarbonate of soda in each shoe overnight."),
    # the smell, the fit and the repair of a shoe are other questions with other answers
    avoid=("smell", "smells", "smelly", "stink", "stinks", "odour", "odor", "size", "fit",
           "too small", "too big", "blister", "blisters", "verruca", "soles", "heels",
           "resole", "repair", "polish", "white trainers", "clean my trainers",
           "clean my shoes", "laces come undone", "shoe rack", "shoe shop", "buy",
           # choosing a pair is the buying question, and it says so with "get" rather than
           # "buy": "what boots should i get for playing in the rain" was the newspaper-and-
           # radiator answer, because "boots" and "rain" are both in this row's key
           "should i get", "what boots", "which boots", "best boots", "good boots",
           "what trainers", "which trainers", "best trainers", "what shoes", "which shoes",
           "best shoes", "recommend", "worth it"),
    bias=1))



# --- a count of what the job needs ---------------------------------------------------------
# A person with a tape measure asks for a count, not an area: "how many tiles for a 3 by 2 metre
# floor" wants the tiles, not the six square metres. Paint, wallpaper and the bulk materials
# already answer their own quantities; a tile, a slab, a board, a brick and a run of skirting had
# no row, so the word fell to whichever card held its other sense - "how many tiles in a box" was
# twelve rounds of boxing, "how many floorboards for a room" was mopping, "how many paving slabs
# for a patio" was a search hedge, and the skirting answer stopped at the perimeter.
#
# One table of what a unit covers answers the family, and one reading of the line feeds it, so a
# new material is a reply and a row rather than a new parser. Where the line gives no measurement
# the reply asks for the one it needs; where it gives two, the arithmetic is done in the answer,
# because that is the part people get wrong.
_METRE = {"mm": 0.001, "cm": 0.01, "m": 1.0, "metre": 1.0, "metres": 1.0, "meter": 1.0,
          "meters": 1.0, "ft": 0.3048, "foot": 0.3048, "feet": 0.3048, "in": 0.0254,
          "inch": 0.0254, "inches": 0.0254, "yd": 0.9144, "yard": 0.9144, "yards": 0.9144}
# Number words, because a tape measure is written down as much as it is typed: "three metres".
_SAID_NUMBER = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "twenty": 20,
                "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60}
_A_NUMBER = (r"(\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
             r"twenty|thirty|forty|fifty|sixty)")
_A_UNIT = r"(mm|cm|metres?|meters?|m|ft|feet|foot|in|inch|inches|yd|yards?)?"
# "3 by 2", "4m x 3m", "600mm x 600mm": the two sides of a surface, written either way round.
_SIDE_BY_SIDE = re.compile(_A_NUMBER + r"\s*" + _A_UNIT + r"\s*(?:by|x|×|\*)\s*" + _A_NUMBER
                           + r"\s*" + _A_UNIT)
# "12 square metres", "12 sq m", "12m2": an area already worked out.
_A_SQUARE = re.compile(_A_NUMBER + r"\s*(?:square\s*(metres?|meters?|feet|foot|ft|yards?|yd|m)|"
                       r"sq\.?\s*(?:m|metres?|meters?|ft|feet)|(m2|m²))")
# One side on its own: "20 metres of fence", "14m of skirting".
_A_LENGTH = re.compile(_A_NUMBER + r"\s*(mm|cm|metres?|meters?|m|ft|feet|foot|yards?|yd)\b")

# A length with a height or depth said as words: "6 metres long and 1 metre high", "4m wide
# by 3m deep", "8 foot long and 2 foot high". The sides are the same two numbers as "6m x 1m",
# only the words in between are different, and a wall or a fence run is often said this way.
_A_LONG_AND_HIGH = re.compile(_A_NUMBER + r"\s*" + _A_UNIT
                              + r"\s*(?:long|wide|deep|tall)\s*(?:and|by|x|×|\*|,)\s*"
                              + _A_NUMBER + r"\s*" + _A_UNIT + r"\s*(?:high|tall|deep)\b")
# and the same the other way round: "1 metre high and 6 metres long"
_A_HIGH_AND_LONG = re.compile(_A_NUMBER + r"\s*" + _A_UNIT
                              + r"\s*(?:high|tall|deep)\s*(?:and|by|x|×|\*|,)\s*"
                              + _A_NUMBER + r"\s*" + _A_UNIT
                              + r"\s*(?:long|wide|deep|tall)\b")

# The ceiling of a room, said either side of the word: "2.4m ceilings", "with ceilings of 2.7m".
# A room's paint is its perimeter times this, and the line often names it because 2.4m is only the
# usual height: "how much paint do i need for a room 4m by 3m with 2.7m ceilings" was answered with
# a worked example of a different room, ceiling height and all.
_A_CEILING_BEFORE = re.compile(_A_NUMBER + r"\s*" + _A_UNIT + r"\s*(?:high\s+)?ceilings\b")
_A_CEILING_AFTER = re.compile(r"\bceiling\s+height\s*(?:of\s+)?" + _A_NUMBER + r"\s*" + _A_UNIT
                              + r"|\bceilings?\s+of\s+" + _A_NUMBER + r"\s*" + _A_UNIT)
# The thing being painted, when it is the ceiling: a ceiling is one flat surface.
_A_CEILING_THING = re.compile(r"\bceilings?\b")
# The height a room is assumed to be when the line does not say, and the one the paint card's own
# worked example uses: "a 4m by 4m room with 2.4m ceilings is about 38 square metres".
_DEFAULT_CEILING = 2.4


def _said_number(raw):
    """The value of a number as typed or as said ("3", "three"), or None."""
    raw = str(raw or "").strip().lower()
    if raw in _SAID_NUMBER:
        return float(_SAID_NUMBER[raw])
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _in_metres(raw, unit):
    """A value in metres: the unit as a person writes it ("metres", "m", "ft"), default metres."""
    value = _said_number(raw)
    if value is None:
        return None
    unit = str(unit or "m").strip().lower()
    return value * _METRE.get(unit, _METRE.get(unit.rstrip("s"), 1.0))


def _measurements(clean):
    """(area in square metres or None, one length or perimeter in metres or None) from the line.

    A pair of sides is a room when both are a size a room is; "600 by 600" beside "300mm tiles"
    is a tile, so it is read as the size of the thing being laid rather than of the floor, and a
    line with only a tile size in it is left with no measurement to work from.
    """
    for found in _SIDE_BY_SIDE.finditer(clean):
        first = _in_metres(found.group(1), found.group(2))
        second = _in_metres(found.group(3), found.group(4) or found.group(2))
        if not first or not second:
            continue
        if 0.3 <= first <= 40 and 0.3 <= second <= 40:
            return round(first * second, 2), round(2 * (first + second), 2)
    for pattern, height_first in ((_A_LONG_AND_HIGH, False), (_A_HIGH_AND_LONG, True)):
        found = pattern.search(clean)
        if not found:
            continue
        first = _in_metres(found.group(1), found.group(2))
        second = _in_metres(found.group(3), found.group(4))
        if not first or not second:
            continue
        run, height = (second, first) if height_first else (first, second)
        if 0.3 <= run <= 40 and 0.3 <= height <= 40:
            # The run is the first number said, so a fence or a skirting question still gets a
            # length rather than a perimeter it never asked for.
            return round(run * height, 2), round(run, 2)
    found = _A_SQUARE.search(clean)
    if found:
        value = _said_number(found.group(1))
        unit = found.group(2) or found.group(3) or "m"
        if value:
            return round(value * _in_metres(1, unit) ** 2, 2), None
    found = _A_LENGTH.search(clean)
    if found:
        value = _in_metres(found.group(1), found.group(2))
        if value:
            return None, round(value, 2)
    return None, None


def _the_ceiling(clean):
    """The ceiling height the line names in metres, or None."""
    for pattern in (_A_CEILING_BEFORE, _A_CEILING_AFTER):
        found = pattern.search(clean)
        if not found:
            continue
        value = _in_metres(found.group(1), found.group(2))
        if value and 1.8 <= value <= 5:
            return round(value, 2)
    return None


# A single surface is one flat thing whatever its two numbers are, and a room is four walls.
# "how much paint for a 4m by 3m wall" is 12 square metres, not 14 metres round times a ceiling
# height nobody said; the noun in the line is what tells the two apart, so it does not become a
# rule about which numbers came first.
_ONE_SURFACE = re.compile(
    r"\b(?:walls?|panel|panels|doors?|gates?|boards?|windows?|sills?|wardrobes?|cupboards?|"
    r"cabinets?|worktop|worktops|shelves|shelf|radiator|radiators)\b", re.I)
_A_ROOM = re.compile(
    r"\b(?:rooms?|bedrooms?|kitchens?|lounges?|living rooms?|dining rooms?|halls?|hallways?|"
    r"landings?|bathrooms?|lofts?|studies|study|nurser(?:y|ies)|offices?|garages?|"
    r"conservator(?:y|ies)|cellars?|attics?|utility|sheds?)\b", re.I)


def _wall_area(understood, memory=None):
    """(square metres to paint, the ceiling height used or None, what is painted) from the line.

    A wall said with two dimensions gives its own area: "a wall 6 metres long and 2.5 high" is
    15 square metres. A room said as two sides gives the floor area and the perimeter, and what
    is painted is the perimeter times the ceiling height - the height the line names, or 2.4m
    when it names none, which is what the paint card's own worked example assumes. An area
    already worked out ("a 15 square metre wall") or a ceiling said as two sides is one flat
    surface, so its own area is what wants the paint. A follow-up that leaves the size out ("and
    how much paint for that") is sized by the turn that gave it, the way the tile and slab rows
    already are. A line with no size anywhere gets nothing, and the paint row answers that one
    with the method.

    The third thing is what the figure is about, because a ceiling is not a room's walls: "how
    much paint for a ceiling 4m by 3m" is 12 square metres over the head, not 14 metres round
    times a ceiling height read off the ceiling's own width.
    """
    clean = _the_line(understood)
    earlier = None
    if not any(_measurements(clean)):
        remembered = _the_size_said_before(memory, clean) if memory else None
        earlier = str(remembered[2]).lower() if remembered else None
    for text in (clean, earlier):
        if not text:
            continue
        area, run = _measurements(text)
        if not area and not run:
            continue
        if _A_LONG_AND_HIGH.search(text) or _A_HIGH_AND_LONG.search(text):
            return (area, None, "wall") if area else (None, None, None)
        if area and run is None:
            # an area already worked out: one surface, its own figure
            return area, None, "wall"
        if not area or not run:
            return None, None, None
        if (_A_CEILING_THING.search(text) and _the_ceiling(text) is None
                and not re.search(r"\brooms?\b|\bwalls?\b", text)):
            # the ceiling is the thing to paint, not a height said about a room
            return area, None, "ceiling"
        if _ONE_SURFACE.search(text) and not _A_ROOM.search(text):
            # a wall, a panel, a door: the two numbers are its own width and height
            return area, None, "wall"
        ceiling = _the_ceiling(text) or _DEFAULT_CEILING
        return round(run * ceiling, 2), ceiling, "room"
    return None, None, None


def _the_line(understood):
    """The line as typed, or as tidied when there is nothing typed.

    The typed line comes first: the tidied one repairs a wrong word, but it also writes a
    number it reads as a homophone the other way round ("a 5 by 4 lawn" came back as "a 5 by
    for lawn"), and a measurement is the one thing this row cannot do without.
    """
    reading = understood or {}
    return str(reading.get("clean") or reading.get("plain") or reading.get("text") or "").lower()


def _wall_width_and_height(understood, memory=None):
    """(width, height) of the one wall the line gives, or (None, None).

    Wallpaper is counted in drops along the wall, so the paper row needs the width rather than the
    area the paint row works with: "a wall 1m by 1m" is two drops of a 52cm roll, and a wall 6
    metres long and 2.5 high is twelve. The pair is read here the way `_measurements` reads it,
    but kept as the two sides rather than turned into an area and a perimeter, which is what a
    room needs. A room is not a wall, and a wall said only as an area has no width to count along,
    so both of those keep the method the card teaches.
    """
    clean = _the_line(understood)
    text, carried = clean, False
    if not any(_measurements(clean)):
        remembered = _the_size_said_before(memory, clean) if memory else None
        text, carried = (str(remembered[2]).lower() if remembered else ""), True
    if not text:
        return None, None
    # The thing being papered is named in the line that gave the size, and a bare "how much
    # wallpaper for that" carries the wall without the word: `_wall_area` has already said this is
    # one surface, so the noun is only read while the line speaks for itself.
    if not carried:
        if _A_CEILING_THING.search(text) and _the_ceiling(text) is None:
            return None, None
        if not _ONE_SURFACE.search(text) or _A_ROOM.search(text):
            return None, None
    for found in _SIDE_BY_SIDE.finditer(text):
        first = _in_metres(found.group(1), found.group(2))
        second = _in_metres(found.group(3), found.group(4) or found.group(2))
        if first and second and 0.3 <= first <= 40 and 0.3 <= second <= 40:
            return round(first, 2), round(second, 2)
    for pattern, height_first in ((_A_LONG_AND_HIGH, False), (_A_HIGH_AND_LONG, True)):
        found = pattern.search(text)
        if not found:
            continue
        first = _in_metres(found.group(1), found.group(2))
        second = _in_metres(found.group(3), found.group(4))
        if not first or not second:
            continue
        width, height = (second, first) if height_first else (first, second)
        if 0.3 <= width <= 40 and 0.3 <= height <= 40:
            return round(width, 2), round(height, 2)
    return None, None


def _the_size_said_before(memory, clean):
    """(area, run, the earlier line) when this line leaves the size out and the chat gave it.

    "and how much grout for that" is the same floor as the turn before, and asking for its
    length and width again reads as if the bot had not listened. Only a line that names no size
    of its own is filled in, and only from the last few turns.
    """
    area, run = _measurements(clean)
    if area or run:
        return None
    for turn in reversed(((memory or {}).get("turns") or [])[-4:]):
        said = str(turn.get("user") or "")
        if not said:
            continue
        before, before_run = _measurements(said.lower())
        if before or before_run:
            return before, before_run, said.strip()
    return None


# What the person is paving or boarding, so the ask for a size names their own job back:
# "how many paving slabs do i need for a driveway" must not ask how big the patio is.
_SURFACE_WORD = (("driveway", "driveway"), ("drive", "driveway"), ("path", "path"),
                 ("patio", "patio"), ("terrace", "terrace"), ("shed base", "shed base"),
                 ("yard", "yard"), ("garden", "garden"), ("lawn", "lawn"), ("deck", "deck"))


def _sized_by_the_chat_before(reply):
    """A follow-up that leaves the size out is sized by the line before it.

    "and how much grout for that" is the same floor as the turn before; asking for its length
    and width again reads as if the bot had not listened. A line that names its own size is
    left alone, and the size is only read from the four turns before this one.
    """
    def answered(memory, understood):
        earlier = _the_size_said_before(memory, _the_line(understood))
        if earlier:
            under = dict(understood or {})
            under["clean"] = f"{_the_line(understood)} {earlier[2]}".strip()
            return reply(memory, under)
        return reply(memory, understood)
    answered.__name__ = getattr(reply, "__name__", "answered")
    answered.__doc__ = getattr(reply, "__doc__", None)
    return answered


def _the_surface(clean, default):
    """The word for the thing being measured, as the line named it, or the row's own default."""
    for word, said in _SURFACE_WORD:
        if re.search(rf"\b{word}\b", clean):
            return said
    return default


def _a_lay_size(clean):
    """The size of the tile or slab being laid, when the line names one: "600 by 600 tiles".

    A pair too small to be a room is the piece being laid, not the surface it goes on, which is
    how "how many 600 by 600 tiles for a 3 by 2 metre floor" asks two things at once.
    """
    for found in _SIDE_BY_SIDE.finditer(clean):
        first = _in_metres(found.group(1), found.group(2))
        second = _in_metres(found.group(3), found.group(4) or found.group(2))
        if not first or not second:
            continue
        if not (found.group(2) or found.group(4)) and 1.5 < first <= 3000:
            # "600 by 600 tiles" and "450 by 450 slabs" are millimetres: nobody lays a
            # piece of any other size on a floor, and a bare number that big is the small side.
            first, second = first / 1000, second / 1000
        if 0.05 <= first <= 1.5 and 0.05 <= second <= 1.5:
            return first, second
    return None


def _a_piece(size):
    """A tile or slab size said the way it is sold: 300mm by 300mm, 4.8m by 145mm."""
    said = []
    for value in size:
        if value < 1:
            said.append(f"{_said(round(value * 1000))}mm")
        else:
            said.append(f"{value:g}m")
    return " by ".join(said)


def _up(value):
    """A whole number of things to buy: you cannot buy part of a tile."""
    return int(-(-value // 1))


def _said(value):
    """A whole count the way a person says it, without a needless ".0"."""
    return f"{int(round(value)):,}"


def _boxes(tiles):
    """The boxes of a dozen the tiles come to, said the way it is said: "around 7 boxes"."""
    boxes = _up(tiles / 12)
    return f"{'around' if boxes > 1 else ''} {_counted(boxes, 'box', 'boxes')} of a dozen".strip()


def _counted(count, thing, many=None):
    """A count with its thing, in the number the sentence needs: "1 tile", "74 tiles"."""
    if round(count) == 1:
        return f"1 {thing}"
    return f"{_said(count)} {many or thing + 's'}"


def _about_the_area(area):
    """Six square metres" - the area said back, so the arithmetic is the person's own."""
    if round(area, 1) == 1:
        return "One square metre"
    # A bit under a square metre is not "1 square metres": the figure the person's own numbers
    # gave is kept to one decimal, because rounding it to a whole square metre changes the sum.
    if area != int(area):
        return f"{area:g} square metres"
    return f"{_said(area)} square metres"


@_sized_by_the_chat_before
def _how_many_tiles(memory, understood):
    clean = _the_line(understood)
    area, _ = _measurements(clean)
    size = _a_lay_size(clean)
    # "how many boxes of tiles" is a count of boxes, so the area and the label on the box are what
    # it turns on - not a rule about tiles to the square metre with no count in it.
    in_boxes = bool(re.search(r"\b(?:in|per|a|one) box\b|\bboxes\b", clean))
    if area and size:
        count = area / (size[0] * size[1])
        buy = _up(count * 1.1)
        return (f"{_about_the_area(area).capitalize()} of {_a_piece(size)} tiles is "
                f"{_counted(round(count), 'tile')}, so buy {_counted(buy, 'tile')} for the cuts - "
                f"{_boxes(buy)}. Line the cuts up in the corner nobody looks at and check a spare "
                f"tile is left over for a repair.")
    if area and in_boxes:
        return (f"A box says the square metres it covers on the label, and most cover about one, "
                f"so {_about_the_area(area)} is about {_said(_up(area))} boxes, or "
                f"{_said(_up(area * 1.1))} with the cuts. A 600mm tile comes three to the square "
                f"metre, so a box of those covers more and the count drops: read the m2 on the "
                f"box rather than the number of tiles in it.")
    if not area:
        if size:
            # The person named the tile they are buying: say the count that size gives, so the
            # question back is only about the surface and not about the tile as well.
            per = _up(1 / (size[0] * size[1]))
            return (f"A {_a_piece(size)} tile is about {_said(per)} to the square metre, so add "
                    f"10% to the area for the cuts. How big is the wall or floor - length and "
                    f"width in metres?")
        if in_boxes:
            return ("A box of tiles covers about a square metre - it says the m2 on the box - so "
                    "the count follows from the tile size: a 300mm tile is about 11 to the square "
                    "metre, and a 600mm one just under three. Buy 10% more than the area needs "
                    "for the cuts at the edges. How big is the wall or floor?")
        return ("A 300mm tile covers about a tenth of a square metre, so count about 11 to the "
                "square metre and add 10% for cuts. How big is the wall or floor - length and "
                "width in metres?")
    count = area * 11.1
    buy = _up(count * 1.1)
    return (f"{_about_the_area(area).capitalize()} at about 11 tiles to the square metre is "
            f"{_counted(round(count), 'tile')}, so buy {_counted(buy, 'tile')} to allow for cuts "
            f"- {_boxes(buy)}. A 600mm tile is just under three to the square metre, so that size "
            f"needs about a quarter of the count.")



@_sized_by_the_chat_before
def _how_many_decking(memory, understood):
    clean = _the_line(understood)
    area, _ = _measurements(clean)
    if not area:
        return (f"A 4.8m board of 145mm decking covers about 0.7 of a square metre, so a square "
                f"metre is about a board and a half. How big is the "
                f"{_the_surface(clean, 'deck')} - length and width in metres?")
    count = area / 0.696
    buy = _up(count * 1.1)
    return (f"{_about_the_area(area).capitalize()} at about 0.7 of a square metre a board is "
            f"{_said(round(count))} boards of 4.8m, so buy {_said(buy)} with the cuts. The joists "
            f"are the other count: at 400mm centres a 4m by 3m deck needs about 9 runs, and the "
            f"boards run across them with a 5mm gap.")


@_sized_by_the_chat_before
def _how_many_fence(memory, understood):
    clean = _the_line(understood)
    _, length = _measurements(clean)
    # "how many fence posts for 6 panels" already carries the count: six panels is 11 metres of
    # run and seven posts, and asking how long the run is reads as if the six had not been said.
    said_panels = re.search(r"\b(\d+)\s+(?:fence\s+|6ft\s+)?panels?\b", clean)
    if said_panels and not length:
        panels = int(said_panels.group(1))
        if not panels:
            panels = 1
        run = panels * 1.83
        return (f"{_said(panels)} panels at 1.83m is {_said(round(run, 1))} metres of run, so you "
                f"want {_said(panels + 1)} posts if it starts and ends on one. Set each post "
                f"600mm into the ground in concrete and put a gravel board under every panel so "
                f"the wood does not sit in the wet.")
    if not length:
        return ("A standard 6ft fence panel is 1.83m wide, so 20 metres needs 11 panels and 12 "
                "posts. How long is the run in metres?")
    panels = _up(length / 1.83)
    return (f"{_said(length)} metres at 1.83m for a standard 6ft panel is {_said(round(panels))} "
            f"panels, and {_said(panels + 1)} posts if the run starts and ends on one. Put a "
            f"gravel board under each panel so the wood does not sit in the wet, and set the "
            f"posts 600mm into the ground in concrete.")


@_sized_by_the_chat_before
def _how_many_bricks(memory, understood):
    clean = _the_line(understood)
    area, _ = _measurements(clean)
    blocks = bool(re.search(r"\bblocks?\b", clean))
    if not area:
        if blocks:
            return ("A concrete block is 440 by 215mm, so a square metre of single-skin wall is "
                    "about 10 blocks. How big is the wall - length and height in metres?")
        return ("A standard brick with its mortar joint covers about 60 to the square metre of "
                "single-skin wall. How big is the wall - length and height in metres?")
    if blocks:
        count = area * 10
        return (f"{_about_the_area(area).capitalize()} of single-skin wall at about 10 blocks to "
                f"the square metre is {_said(round(count))} blocks, so order "
                f"{_said(_up(count * 1.05))} with the waste. A cavity wall takes two skins, so "
                f"double it and add wall ties.")
    count = area * 60
    return (f"{_about_the_area(area).capitalize()} of single-skin wall at about 60 bricks to the "
            f"square metre is {_said(round(count))} bricks, so order {_said(_up(count * 1.05))} "
            f"with the waste - and double it for a cavity wall. A 25kg bag of mortar mix lays "
            f"about 25 bricks.")


@_sized_by_the_chat_before
def _how_many_floorboards(memory, understood):
    clean = _the_line(understood)
    area, _ = _measurements(clean)
    if not area:
        return ("A 2.4m floorboard 120mm wide covers about 0.29 of a square metre, so a square "
                "metre is about three and a half boards. How big is the room - length and width "
                "in metres?")
    count = area / 0.288
    return (f"{_about_the_area(area).capitalize()} at about 0.29 of a square metre a board is "
            f"{_said(round(count))} boards of 2.4m by 120mm, so buy {_said(_up(count * 1.1))} for "
            f"cuts. Run them across the joists and leave an 8 to 10mm gap at each wall for "
            f"movement.")


@_sized_by_the_chat_before
def _how_many_skirting(memory, understood):
    clean = _the_line(understood)
    _, length = _measurements(clean)
    if not length:
        return ("Skirting comes in 2.4m lengths, so add up the room's perimeter and divide: a 4m "
                "by 3m room is 14m round, which is six lengths. How big is the room - length and "
                "width in metres?")
    lengths = _up(length / 2.4)
    return (f"{_said(length)} metres round at 2.4m a length is {_said(round(lengths))} lengths, "
            f"so buy {_said(lengths + 1)} to allow for the mitres and a mistake. Work the "
            f"perimeter out as twice (length + width), and add a length for each doorway you have "
            f"to cut round.")



@_sized_by_the_chat_before
def _how_many_plasterboard(memory, understood):
    clean = _the_line(understood)
    area, _ = _measurements(clean)
    # a sheet is 2.4m by 1.2m, which is what everyone sells; a ceiling takes 12.5mm, a wall 9.5mm
    if not area:
        return ("A plasterboard sheet is 2.4m by 1.2m, so just under three square metres, and "
                "you want about 10% more than the wall for the cuts and the joints. How big is "
                "the wall or ceiling - length and width in metres?")
    count = area / 2.88
    thick = "12.5mm" if re.search(r"\bceilings?\b|\broof\b", clean) else "9.5mm"
    return (f"{_about_the_area(area).capitalize()} is {_said(count)} sheets of 2.4m by 1.2m "
            f"{thick} plasterboard once it is covered, so buy {_said(_up(area * 1.1 / 2.88))} "
            f"with the cuts at the edges and keep the offcut for a patch. Stagger the joints, "
            f"leave a 3mm gap between the sheets, and screwing it into the joists or studs holds "
            f"better than gluing it on its own.")




# A count row never answers an explaining ask: "how do i work out square metres" is the sum
# itself, and after a turn about tiles it was taken as a follow-up about the tiles and then
# dropped, so the person got a shrug.
_NOT_A_TASK = ("work out", "workout", "calculate", "formula", "explain", "explaining",
               # a frequency or a duration is not a count: "how often do i need to change my bed
               # sheets" was answered with the plasterboard sheet
               "how often", "how many times", "how long", "when should i", "when do i",
               "how frequently", "every week", "every month")


# Every word a count row keys on does other work in English, and the row was answering the other
# work with the price of a wall: "how many rooms should we block" is a venue, "how many blocks of
# butter" is a shop, "how many sheets of paper in a ream" is stationery, "how many bricks in a
# lego set" is a toy, "how many tiles fell off my roof" is a repair. Four readings of the whole
# line, so a row keeps its turn wherever the material really is the subject of the question.
_DOUBLE_DUTY = ("block", "post", "panel", "sheet", "board", "roll", "coat", "tile", "slab",
                "brick", "deck", "fence", "plank", "bag", "pack", "tin", "can", "turf")
# The word in front of a verb: "we block", "should i post", "lets tile". A material word after
# one of these is a doing, not a thing.
_A_SUBJECT_OR_MODAL = ("i", "we", "you", "they", "he", "she", "it", "to", "should",
                       "could", "would", "can", "will", "may", "might", "must", "shall",
                       "lets", "let's", "do", "does", "did", "dont", "didnt", "cant",
                       "wont", "not")
# What can follow "of" and still be the material itself: "bags of tile adhesive" is adhesive in
# bags. "Blocks of butter" and "sheets of paper" are not a wall or a wall lining.
_OURS = ("adhesive", "grout", "cement", "mortar", "sand", "ballast", "hardcore", "plaster",
         "plasterboard", "paint", "tile", "brick", "block", "slab", "board", "plank",
         "panel", "post", "decking", "deck", "fencing", "fence", "skirting", "turf",
         "floorboard", "paving", "compound", "insulation")
# A thing a count is asked about in a yard, a shop or a toy box rather than on a job: "in a box"
# and "in a pack" are the material on sale, "in a lego set" is not.
_A_JOB_WORD = ("wall", "walls", "floor", "floors", "flooring", "bathroom", "kitchen",
               "shower", "room", "rooms", "patio", "path", "drive", "driveway", "garden",
               "lawn", "shed", "fence", "fencing", "deck", "decking", "ceiling", "loft",
               "attic", "hall", "hallway", "landing", "conservatory", "garage", "extension",
               "fireplace", "splashback", "table", "tabletop", "stairs", "cladding", "border",
               "flowerbed", "bed", "allotment", "greenhouse", "workshop", "utility", "cabin",
               "basement", "cellar", "porch", "outbuilding", "roof", "gutter", "window",
               "windowsill", "doorway", "door", "frame", "arch", "pillar", "column")
_A_UNIT_WORD = ("box", "boxes", "pack", "packs", "packet", "packets", "bag", "bags", "tin",
                "tins", "roll", "rolls", "pallet", "pallets", "crate", "crates", "bundle",
                "bundles", "bale", "bales", "sleeve", "sleeves", "tub", "tubs", "tube",
                "tubes", "sheet", "sheets", "metre", "metres", "m2", "square")
# A thing that has already come away is not a thing to buy: the count of what fell is a repair.
_A_CAME_AWAY = ("fell off", "fallen off", "falling off", "came off", "come off", "coming off",
                "blew off", "blown off", "blowing off", "peeled off", "popped off",
                "dropped off", "worked loose", "cracked off")
# Nor is a count of what is already there, or already gone. "how many paving slabs were lifted",
# "how many boards are on the floor", "how many bags of cement do i own" and "how many bricks have
# i got" all ask about stock or history, and a row that answers with the price to buy is answering
# a question nobody asked. The buying shapes - need, buy, will i need, come on a pallet - are what
# these rows are for, so the past and the possessive stand them down.
_A_LOOKING_BACK = ("were ", "was ", "did ", "do i own", "do we own", "have i got", "have we got",
                   "has he got", "has she got", "have they got", "are left", "is left", "left in",
                   "left over", "are on the", "were there", "does it hold", "how many are",
                   "how many do they", "how many did", "got left")


def _the_material_is_the_subject(understood):
    """False when the material word in the line is doing another word's job.

    The guard is the four readings above, in one place: a material word used as a verb, a
    partitive that is not the material ("blocks of butter"), something that came away rather than
    something to buy, and a container that is not a shop's ("in a lego set"). It reads the whole
    line, so it holds for every count row and needs no list of the ways people phrase a job.
    """
    reading = understood or {}
    line = str(reading.get("clean") or reading.get("text") or "").lower()
    if not line:
        return True
    if any(phrase in line for phrase in _A_CAME_AWAY):
        return False
    if any(phrase in line for phrase in _A_LOOKING_BACK):
        return False
    for word in _DOUBLE_DUTY:
        family = re.compile(r"\b" + word + r"(?:s|es|ed|ing)?\b")
        for found in family.finditer(line):
            before = line[:found.start()].split()
            if not before or before[-1] not in _A_SUBJECT_OR_MODAL:
                continue
            rest = line[:found.start()] + " " + line[found.end():]
            if not family.search(rest):
                return False        # the only mention is the doing, not the thing
    def ours(word):
        """Whether the word is the material, allowing for a plural: "blocks" counts, "til" does not."""
        stems = {word}
        if word.endswith("s") and len(word) > 3:
            stems.add(word[:-1])
        if word.endswith("es") and len(word) > 4:
            stems.add(word[:-2])
        return bool(stems & set(_OURS))

    for found in re.finditer(r"\b([a-z]+)\s+of\s+([a-z]+)", line):
        holder, held = found.group(1), found.group(2)
        if (holder in _A_UNIT_WORD or ours(holder)) and not ours(held):
            return False
    for found in re.finditer(r"\bin\s+(?:a|an|the|one)\s+([a-z]+)", line):
        holder = found.group(1)
        if holder in _A_UNIT_WORD or holder in _A_JOB_WORD or holder in _OURS:
            continue
        return False
    return True


ENTRIES += [
    # The quantity ask, and only that: the laying, the cleaning and the price of each material
    # are their own answers, and a how-to line that mentions tiles must keep them.
    entry("tile-quantity",
          (("tile", "tiles", "tiling", "wall tile", "wall tiles", "floor tile", "floor tiles",
            "tile box", "box of tiles", "boxes of tiles"),
           ("how many", "much", "need", "needs", "buy", "cover", "covers", "enough", "quantity",
            "do i need", "will i need", "many tiles", "per square metre", "per box", "in a box")),
          _how_many_tiles,
          ask=("many", "much", "need", "buy", "cover", "quantity"),
          guard=_the_material_is_the_subject,
          bias=1,
          avoid=_NOT_A_TASK + ("how do i tile", "how to tile", "laying", "lay a", "lay the", "lay them",
                 "fit", "fitting", "fix", "fixing", "remove", "removing", "clean", "cleaning",
                 "grout", "grouting", "seal", "sealing", "cut", "cutting", "drill", "drilling",
                 "cracked", "crack", "loose", "lifting", "cost", "costs", "price", "prices",
                 "cheap", "cheapest", "expensive", "which", "what colour", "what color",
                 "pattern", "splashback style", "bathroom wall", "wallpaper", "adhesive",
                 "additive", "glue", "grout bag", "bags of")),
    entry("decking-quantity",
          (("decking", "deck", "deck boards", "decking boards", "decking board", "planks",
            "decking planks"),
           ("how many", "much", "need", "needs", "buy", "cover", "covers", "enough", "quantity",
            "do i need", "will i need", "many boards", "per square metre", "for a deck",
            "for the deck")),
          _how_many_decking,
          ask=("many", "much", "need", "buy", "cover", "quantity"),
          guard=_the_material_is_the_subject,
          bias=1,
          avoid=_NOT_A_TASK + ("how do i build", "how to build", "how do i lay", "how to lay", "laying",
                 "build", "building", "install", "installing", "fitting", "fix", "fixing",
                 "clean", "cleaning", "oil", "oiling", "treat", "treating", "stain", "staining",
                 "paint", "painting", "slippery", "rotten", "rot", "wobbly", "loose", "replace",
                 "repair", "cost", "costs", "price", "prices", "cheap", "cheapest", "expensive",
                 "which", "what type", "best type", "composite or")),
    entry("fence-quantity",
          (("fence", "fences", "fence panel", "fence panels", "fence post", "fence posts",
            "panels", "posts", "panel"),
           ("how many", "much", "need", "needs", "buy", "cover", "covers", "enough", "quantity",
            "do i need", "will i need", "many panels", "many posts", "for a fence",
            "for the fence", "for 20", "metres of")),
          _how_many_fence,
          ask=("many", "much", "need", "buy", "cover", "quantity"),
          guard=_the_material_is_the_subject,
          bias=1,
          avoid=_NOT_A_TASK + ("how do i fix", "how to fix", "how do i repair", "how to repair", "fix",
                 "fixing", "repair", "repairs", "blew down", "blown down", "fell", "fallen",
                 "rotten", "rot", "leaning", "loose", "wobbly", "replace", "replacing", "paint",
                 "painting", "treat", "treating", "stain", "staining", "clean", "cleaning",
                 "neighbour", "neighbor", "boundary", "who owns", "pay half", "who pays",
                 "cost", "costs", "price", "prices", "cheap", "expensive", "which", "what type",
                 "height", "how high", "how tall", "planning permission",
                 # The post the letter goes in is not a fence post: `posts` is one of the key's
                 # own words, so "how much is second class post" was answered with 11 panels and
                 # 12 posts. Everything that makes it the post office's stands the count down.
                 "post office", "postage", "first class", "second class", "stamp", "stamps",
                 "royal mail", "postbox", "post box", "letter", "letters", "parcel", "parcels",
                 "delivery", "postcode")),
    entry("brick-quantity",
          (("brick", "bricks", "brickwork", "blocks", "concrete blocks", "blockwork",
            "breeze block", "breeze blocks", "cinder block", "cinder blocks"),
           ("how many", "much", "need", "needs", "buy", "cover", "covers", "enough", "quantity",
            "do i need", "will i need", "many bricks", "many blocks", "per square metre",
            "for a wall", "for the wall", "for a garden wall")),
          _how_many_bricks,
          ask=("many", "much", "need", "buy", "cover", "quantity"),
          guard=_the_material_is_the_subject,
          bias=1,
          avoid=_NOT_A_TASK + ("how do i build", "how to build", "how do i lay", "how to lay", "laying",
                 "build", "building", "point", "pointing", "repoint", "repointing", "mortar mix",
                 "mix", "render", "rendering", "plaster", "plastering", "clean", "cleaning",
                 "efflorescence", "paint", "painting", "seal", "sealing", "match", "matching",
                 "cracked", "crack", "damaged", "replace", "replacing", "repair", "repairs",
                 "cost", "costs", "price", "prices", "cheap", "expensive", "which", "what type",
                 "best type", "facing", "engineering", "london stock")),
    entry("floorboard-quantity",
          (("floorboard", "floorboards", "floor board", "floor boards", "flooring boards",
            "timber boards", "planks"),
           ("how many", "much", "need", "needs", "buy", "cover", "covers", "enough", "quantity",
            "do i need", "will i need", "many boards", "per square metre", "for a room",
            "for the room", "for a floor", "for the floor")),
          _how_many_floorboards,
          ask=("many", "much", "need", "buy", "cover", "quantity"),
          guard=_the_material_is_the_subject,
          bias=1,
          avoid=_NOT_A_TASK + ("how do i fit", "how to fit", "how do i lay", "how to lay", "laying", "fit",
                 "fitting", "replace", "replacing", "repair", "repairs", "squeak", "squeaks",
                 "squeaking", "creak", "creaks", "creaking", "gap", "gaps", "fill", "filling",
                 "sand", "sanding", "varnish", "varnishing", "oil", "oiling", "stain", "staining",
                 "clean", "cleaning", "mop", "mopping", "cost", "costs", "price", "prices",
                 "cheap", "expensive", "which", "what type", "best type")),
    entry("skirting-quantity",
          (("skirting", "skirting board", "skirting boards", "skirting lengths", "skirtings",
            "architrave", "skirting plank", "skirting planks"),
           ("how many", "much", "need", "needs", "buy", "cover", "covers", "enough", "quantity",
            "do i need", "will i need", "many lengths", "many boards", "metres of", "for a room",
            "for the room", "how much skirting")),
          _how_many_skirting,
          ask=("many", "much", "need", "buy", "cover", "quantity"),
          guard=_the_material_is_the_subject,
          bias=2,
          avoid=_NOT_A_TASK + ("how do i fit", "how to fit", "how do i fix", "how to fix", "fitting", "fit",
                 "fix", "fixing", "remove", "removing", "replace", "replacing", "repair",
                 "paint", "painting", "clean", "cleaning", "dust", "dusting", "caulk",
                 "caulking", "fill", "filling", "gap", "gaps", "nail", "nailing", "glue",
                 "cost", "costs", "price", "prices", "cheap", "expensive", "which", "what type",
                 "height", "how high", "mdf or", "pine or")),
    entry("plasterboard-quantity",
          (("plasterboard", "plaster board", "plasterboards", "plaster boards", "sheet",
            "sheets", "gypsum board", "drywall"),
           ("how many", "much", "need", "needs", "buy", "cover", "covers", "quantity",
            "do i need", "will i need", "many sheets", "for a wall", "for the wall",
            "for a ceiling", "for the ceiling")),
          _how_many_plasterboard,
          ask=("many", "much", "need", "buy", "cover", "quantity"),
          guard=_the_material_is_the_subject,
          bias=1,
          avoid=_NOT_A_TASK + ("how do i", "how to", "hang", "hanging", "fix", "fixing", "screw", "screwing",
                 "tape", "joint", "skim", "skimming", "sanding", "patch", "patching", "crack",
                 "cracks", "cost", "costs", "price", "prices", "cheap", "expensive", "which",
                 "thickness", "9.5", "12.5", "mdf", "soundproof", "insulate", "insulation")),
]
# ---- a fixing, and the bit that goes with it ------------------------------------------------
#
# "what size drill bit for a wall plug", "what size screws for a shelf" and "what size rawl plug
# for a wall" were each answered with the women's clothes size conversion, because "what size" was
# the only part of the line the bot acted on. The clothes row now stands down for every tool and
# fixing, and this row is what they asked: the bit is the plug's own diameter, and a shelf into
# plasterboard alone is a bracket problem rather than a screw size.
PLUG_ANSWER = (
    "A drill bit the same diameter as the plug: 5mm for a yellow plug, 6mm for a red one, 7mm for "
    "a brown and 10mm for a blue. Drill a few millimetres deeper than the plug is long, push it in "
    "flush with the wall - a tap with the screwdriver handle finishes it - and take the screw size "
    "from the packet, which is the one number it always prints. In plasterboard with nothing "
    "behind it no plug holds: find a stud, or use a plasterboard fixing rated well above what you "
    "are hanging.")
SHELF_ANSWER = (
    "For a shelf into studs or masonry, 4 x 40mm or 5 x 50mm screws are plenty, and the brackets "
    "matter more than the screws do: fix each bracket to a stud where you can, keep the shelf "
    "within the brackets' span, and put the heavy things over the brackets rather than at the ends. "
    "Into plasterboard with nothing behind it, no screw holds a loaded shelf - use plasterboard "
    "fixings rated well above the weight, or a batten screwed into the studs.")
# A screw asked about by length, gauge or head is a different question, and so is a wall whose
# drill bit is being asked about for a hole in a tile or a hole in metal.
_FIXING_WORDS = ("drill bit", "drill bits", "wall plug", "wall plugs", "rawl plug", "rawl plugs",
                 "rawlplug", "rawlplugs", "raw plug", "raw plugs", "rawplug", "plasterboard "
                 "fixing", "plasterboard fixings", "masonry bit", "masonry drill", "screw",
                 "screws", "fixing", "fixings", "anchor", "anchors", "nut", "nuts", "bolt",
                 "bolts", "washer", "washers", "rivet", "rivets", "dowel", "dowels", "thread",
                 "threads", "spanner", "spanners")
_FIXING_ASK = ("what size", "which size", "what drill", "what bit", "what length", "how long",
               "size", "right size", "need", "use", "for a wall", "for plasterboard",
               "for a shelf", "for shelves", "into plasterboard", "into brick", "into masonry")


NUT_ANSWER = (
    "A nut and a bolt match on the thread, and the number in the name is the thread's diameter "
    "in millimetres: an M8 nut goes on an M8 bolt, which takes a 13mm spanner, and M6 takes 10mm, "
    "M10 takes 17mm and M12 takes 19mm. Take the bolt with you if you only need the nut, and a "
    "washer or a nyloc nut is what stops the joint shaking loose.")


# "Fixing" is the noun a wall plug is, and it is also the verb in "i need to fix my bike":
# words match loosely, so the row keyed on the noun took every line about mending something and
# answered it with a drill bit. A line that says what it is mending is a repair job, and the row
# for the fixing is not its answer. Only the verb shapes are here, because "a fixing for a shelf"
# is the row's own question.
_A_REPAIR_VERB = re.compile(
    r"\b(?:fix|fixes|fixed|fixing|repair|repairs|repaired|repairing|mend|mends|mended|mending|"
    r"service|servicing)\s+(?:my|your|his|her|their|our|the|a|an|this|that|it|some)\b")
_A_NEEDS_MENDING = re.compile(
    r"\b(?:needs?|needed|worth|wants?)\s+(?:fixing|fix|repairing|repair|mending|mend)\b")


# `washer` is the everyday word for the machine, and it is also the word for the little rubber
# thing in a tap and for the ring that goes under a nut. This row owned the bare word and
# answered "do i need a new washer" and "do i need a washer for the tap" with a drill-bit chart,
# because its second list has "need" and "size" and those are the words people ask with. A washer
# is this row's only when the line also names the fixing it goes on: a bolt, a nut, a screw, a
# plug, a drill. Anything else is the machine or the tap, and those rows can have it.
_WASHER_WORDS = frozenset(("washer", "washers"))
_A_FIXING_TO_PUT_IT_ON = frozenset((
    "bolt", "bolts", "nut", "nuts", "screw", "screws", "plug", "plugs", "rawl", "rawlplug",
    "rawlplugs", "rawlplugs", "anchor", "anchors", "rivet", "rivets", "dowel", "dowels",
    "thread", "threads", "spanner", "spanners", "drill", "drilled", "drilling", "drill bit",
    "masonry", "plasterboard", "fixing", "fixings", "wall"))


def _a_washer_is_the_fixing(understood):
    """False for a washer that is a machine or a tap, which this row cannot answer."""
    words = set((understood or {}).get("words") or ())
    if not (_WASHER_WORDS & words):
        return True
    return bool(_A_FIXING_TO_PUT_IT_ON & words)


def _a_repair_job_is_not_a_fixing(understood):
    """False for a line about mending a thing, which is a job rather than a wall plug."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _A_REPAIR_VERB.search(said) or _A_NEEDS_MENDING.search(said):
        return False
    return _a_washer_is_the_fixing(understood)


# "A washer" is the machine that does the washing, the disc in a tap, and the ring that goes under
# a bolt head. The fixing row took every one of them, so "do i need a new washer" was answered
# with a drill bit. A washer is the row's own question only when the line names the joint it goes
# in, and then the joint decides which answer it gets.
_A_WASHER_AT_A_JOINT = re.compile(
    r"\b(?:bolt|bolts|nut|nuts|screw|screws|thread|threads|plug|plugs|drill|drill bit|"
    r"drill bits|masonry|rawl|raw|spanner|anchor|anchors|dowel|dowels)\b")


def _a_washer_names_its_joint(understood):
    """True unless the line says "washer" and never says what the washer goes into."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    words = set((understood or {}).get("words") or ())
    if not ({"washer", "washers"} & words or "washer" in said):
        return True
    return bool(_A_WASHER_AT_A_JOINT.search(said))


def _a_fixing_is_the_question(understood):
    return _a_repair_job_is_not_a_fixing(understood) and _a_washer_names_its_joint(understood)


def _a_fixing(memory, understood):
    """A plug and a drill bit first; a screw asked about for a shelf gets the shelf's answer."""
    said = str((understood or {}).get("clean") or "").lower()
    words = set((understood or {}).get("words") or ())
    shelf = bool({"shelf", "shelves", "bookcase", "bookcase shelf"} & words) or "a shelf" in said
    plug = any(phrase in said for phrase in ("plug", "drill bit", "masonry bit", "drill"))
    if shelf and not plug:
        return SHELF_ANSWER
    # a nut, a bolt and a thread are asked about by name, and the plug's colours say nothing
    # about them
    if {"nut", "nuts", "bolt", "bolts", "thread", "threads", "spanner", "spanners"} & words \
            and not plug:
        return NUT_ANSWER
    return PLUG_ANSWER


# A bed is sold by a name and a size, and "what size sheet for a double bed" had no answer at all
# on main. The four names carry the numbers, which is the whole question.
_BED_SIZES = ("Single is 90 x 190cm, double is 135 x 190, king is 150 x 200 and super king is "
              "180 x 200. Buy the size the frame is sold as rather than measuring the old sheet, "
              "and check the pocket depth for a deep mattress - 30cm or more covers most of "
              "them, and a fitted sheet that is too shallow pings off the corners.")


def _a_bed_size(memory, understood):
    return _BED_SIZES


ENTRIES.append(entry(
    "a-bed-is-a-size",
    (("bed", "beds", "bedding", "sheet", "sheets", "fitted sheet", "duvet", "duvet cover",
      "pillowcase", "pillowcases", "mattress", "mattress topper", "valance"),
     ("what size", "which size", "size", "sizes", "double", "king", "single", "super king",
      "fit", "fits", "measurements", "how wide", "how big")),
    _a_bed_size,
    # a bed that creaks, sags or smells is a fault, and a washing question is the laundry's
    avoid=("creak", "creaks", "creaky", "squeak", "squeaks", "squeaky", "sag", "sags",
           "sagging", "lumpy", "stain", "stains", "smell", "smells", "smelly", "damp",
           "mould", "mold", "bed bugs", "bedbugs", "wash", "washing", "clean", "cleaning",
           "dust mite", "dust mites", "allergy", "allergies", "back", "backache", "sore",
           "too soft", "too hard", "too firm", "firm", "replace", "broken", "slats"),
    bias=1,
))

ENTRIES.append(entry(
    "a-fixing-and-its-drill-bit",
    (_FIXING_WORDS, _FIXING_ASK),
    _a_fixing,
    guard=_a_fixing_is_the_question,
    # a screw head, a screwdriver and a stripped screw are repairs, a wall that is damp or cracked
    # is a fault, and a self-tapping screw is a different question again
    avoid=("stripped", "stuck", "wont come out", "won't come out", "rounded", "head", "heads",
           "screwdriver", "screwdrivers", "self tapping", "self-tapping", "damp", "crack",
           "cracked", "cracks", "mould", "mold", "wet", "leak", "leaking", "wallpaper",
           "paint", "painting", "drill a hole in a tile", "tile", "tiles", "metal", "steel",
           # a decking screw is a screw asked about by board, not by plug
           "deck", "decks", "decking", "floorboard", "floorboards", "fence", "fencing",
           "gazebo", "shed", "sheds",
           "concrete lintel", "lender", "mortgage", "curtain", "curtains", "tv", "television",
           "mirror", "picture", "pictures", "cupboard", "wardrobe", "kitchen unit",
           "kitchen units",
           # a rate that is fixed is not a thing being fixed: "do I need a fixed tariff" reached
           # this row through the word "need" and was told what drill bit a wall plug takes.
           "tariff", "tariffs", "price cap", "energy", "energy bill", "energy bills",
           "variable rate", "fixed rate", "electricity", "gas bill", "gas bills"),
    bias=1,
))


# The tank's own two faults, which were chat echoes: the immersion that is not heating, and hot
# water that runs hot and then cold. `no-hot-water` stands down for both on purpose (it avoids
# "immersion", and the halfway-through shapes belong to the shower), so nothing answered them.
ENTRIES.append(entry(
    "immersion-not-heating",
    (("immersion", "immersion heater", "immersion switch", "immersion element", "immersion stat",
      "immersion thermostat", "cylinder thermostat", "hot water tank", "hot water cylinder"),
     ("not heating", "isnt heating", "not heating up", "stopped heating", "not working",
      "isnt working", "stopped working", "only warm", "lukewarm", "tepid", "cold",
      "keeps tripping", "trips", "reset", "how much", "cost to replace", "replace", "fault",
      "problem", "broken", "gone")),
    "Start with the switch on the wall: an immersion heater has its own fused spur, usually in "
    "the airing cupboard, and it trips like any other. If the spur is on, the thermostat is "
    "under the round cap on the top of the element - turn it up a little and listen for a click; "
    "no click and a tank that stays cold means the element or the stat has gone. That is a "
    "drain-the-tank job: the part is about 40-60 pounds and an hour or two of a plumber's time. "
    "Where a tank has two elements, the bottom one does the heavy lifting.",
    avoid=("boiler", "gas", "hot water bottle", "kettle", "shower head", "radiator",
           "washing machine", "dishwasher", "tumble dryer")))

ENTRIES.append(entry(
    "hot-water-runs-out",
    (("hot water", "hot water tank", "hot water cylinder", "the water", "the hot water"),
     ("hot then cold", "hot then goes cold", "hot and then cold", "goes hot then cold",
      "runs hot then cold", "hot for a minute", "only hot for a minute", "only hot for a few",
      "runs out", "runs out fast", "runs out quickly", "running out", "warm then cold",
      "hot then warm",
      # "my hot water runs cold after a few minutes" is the same fault said the other way round,
      # and without these shapes it went to a running card about cold air.
      "runs cold", "goes cold", "turns cold", "cold after a", "hot for a bit",
      "hot for a minute")),
    "Hot water that runs hot and then cold is the tank running out, not overheating: cold water "
    "comes in at the bottom and pushes the hot out of the top, so the last of it comes through "
    "cool. Set the cylinder thermostat to 60-65 degrees, which is also the temperature that "
    "keeps bacteria down, and see whether a second long shower is what empties it. With two "
    "elements, the bottom one having gone is why a tank heats for a minute and then gives up. A "
    "combi has no tank, so hot-then-cold there is the diverter valve or somebody else's tap.",
    # A line that names the shower keeps the shower answer: "the hot water runs out after one
    # shower" is the combi-or-valve question and this row answered it about a cylinder.
    avoid=("bottle", "flask", "hose", "tap water", "bath water", "drinking", "kettle",
           "shower", "showers")))

# A line with no hot water at all is `no-hot-water`'s, and it names the fault it is not: keeping
# "hot water" out of this row's key would have lost the halfway-through shapes it is for.

# How long the tank takes is not the same question as why it is not heating, and the fault row
# answered it with the switch on the wall.
ENTRIES.append(entry(
    "immersion-heating-time",
    (("immersion", "immersion heater", "immersion switch", "hot water tank", "hot water cylinder"),
     ("how long", "how long does it take", "how long to heat", "how long will it take",
      "takes to heat", "take to heat", "how long for", "time to heat", "hour to heat",
      "can i leave it on", "leave it on overnight", "leave it on all day")),
    "An immersion is nearly always 3kW, and a full 120-litre tank takes about an hour and a half "
    "to two hours from cold; 30 to 40 minutes is enough for a couple of showers. Colder water in "
    "winter and a scaled element both make it slower, and turning the thermostat higher does not "
    "make it heat any faster - it only makes the water hotter. Leaving it on all night is what "
    "the timer is for.",
    avoid=("boiler", "gas", "how much", "cost", "price", "running cost", "kettle", "bottle"),
    # a fish tank's cycling row keys the bare word "tank" and "how long", so "how long will the
    # immersion take to heat the tank" tied with it and lost on registry order. The line names an
    # immersion, so this row is the one that should answer it.
    bias=2))

# A bathroom swapped over: a bath out, a shower in. Three cards answered it and none was the
# question. "is it worth replacing a bath with a shower" reached the repair-or-bin rule ("Fix it
# if it is a part and a few pounds"), "is replacing a bath with a shower expensive" reached the
# running cost of a hot bath, and the same job told as news - "we are replacing our bath with a
# walk in shower" - reached the weather, because `shower` is one. The ask is the same in all
# three shapes: is it worth it, what it costs, and what it involves. So the row carries the
# verdict and the fitted figure, and it is keyed by the swap rather than by the ask's wording.
ENTRIES.append(entry(
    "bath-swapped-for-a-shower",
    (("bath", "baths", "bathtub", "bath tub", "shower", "showers", "walk in shower",
      "walk-in shower", "wet room", "bathroom", "suite", "tub"),
     ("replace", "replaces", "replacing", "replaced", "swap", "swaps", "swapping", "swapped",
      "rip out", "ripping out", "take out", "taking out", "taken out", "remove", "removing",
      "fit a", "fitting a", "fitted a", "install", "installs", "installing", "installation",
      "convert", "converting", "conversion", "walk in shower", "walk-in shower")),
    "Usually yes, and it is the swap most people are glad of: a walk-in shower is easier for "
    "anyone with bad knees or hips, safer than stepping over a bath side, and it makes a small "
    "bathroom feel bigger. Budget about £1,500 to £3,500 fitted for a straight swap in the same "
    "spot, and £3,000 to £6,000+ for a walk-in with a low tray, a wet-room floor and new "
    "tiling - the waterproofing and moving the waste are what the money mostly goes on. Ask for "
    "the tiling and the waste in the quote, and check the floor will take a level-access tray "
    "before you buy one.",
    avoid=("visiting", "visit", "trip", "city", "roman", "roman baths", "hot springs",
           "christmas market", "weekend in bath", "day out",
           "tap", "taps", "mixer", "shower head", "head", "screen", "screens", "sealant",
           "silicone", "leak", "leaks", "leaking", "leaked", "drip", "drips", "dripping",
           "blocked", "drain", "drains", "plug", "panel", "panels", "rust", "mould", "mold",
           "mildew", "clean", "cleaning", "cleaner", "grout", "grouting", "run", "runs",
           "running", "cost to run", "hot water", "boiler", "curtain", "curtains", "rail",
           "mat", "grab rail", "hoist", "tile", "tiles", "tiling", "paint", "painting",
           "bath bomb", "bath salts", "bath oil", "how often", "baby", "toddler", "dog",
           "bath mat", "sponge", "flannel"),
    bias=2,
))

# Where a thing goes is not a how-to about the thing. "where should i put my dehumidifier" and
# "where should i put my nest thermostat" both fell to other rows - a boiler-cost card and a pest
# controller - because no row owns the siting question, and the appliance rows are keyed on the
# fault and the running cost.
ENTRIES.append(entry(
    "where-to-site-a-dehumidifier",
    (("dehumidifier", "dehumidifiers", "dehumidify", "condensation", "damp room",
      "damp bedroom", "drying a room"),
     ("where", "put", "place", "site", "siting", "position", "best place", "which room",
      "keep it", "leave it")),
    "Put it in the dampest room with the door and windows shut, on a flat surface and a hand's "
    "width from the wall so air can get at it - a landing or a hallway rarely is the dampest "
    "room, and a dehumidifier there just dries the air that leaks out of everywhere else. Keep "
    "it off a cold loft or garage floor in winter, where the coil ices up and it spends its time "
    "defrosting instead of drying. Empty the tank before it stops itself, or fit the hose and let "
    "it drain into a sink or a bucket.",
    avoid=("how much", "cost", "price", "running cost", "electricity", "watt", "energy",
           "broken", "not working", "repair", "leak"),
    bias=2))

ENTRIES.append(entry(
    "where-to-site-a-thermostat",
    (("thermostat", "nest thermostat", "hive thermostat", "smart thermostat",
      "room thermostat", "wall thermostat"),
     ("where", "put", "place", "site", "mount", "fit", "position", "height", "how high",
      "which wall", "hallway", "hall")),
    "On an inside wall of the room you heat most, about 1.4 metres off the floor - roughly "
    "eye level - where it feels the same temperature as the middle of the room. Keep it away "
    "from radiators, direct sun, a draught from a door or window, and the kitchen's cooking "
    "heat, or it reads a temperature nobody is standing in and the boiler works to the wrong "
    "number. A hallway is the usual compromise: fine if the hall is a room you actually heat, "
    "wrong if it is the coldest place in the house, because then every other room runs hot.",
    avoid=("not working", "no heat", "cold", "broken", "fault", "error", "setting the",
           "how do i set", "temperature setting", "boiler pressure", "radiator"),
    bias=2))
