"""The half of an answer a person can have: the thing, what is known about it, where the rest lives.

The composer's hedge is the same four words whatever was asked - "That's beyond what I know well,
sorry. Searching for it will turn up better sources than I can offer" - and it names nothing. A
person who has said what the thing is gets a line that would fit any message in the deck:

    how much exercise does it need        (after "i got a puppy last week")
                                    "I don't know enough to answer that honestly. A search should
                                     sort you out quickly - and I'm happy to help with the rest"
    how often do i clean it               (after "i got a humidifier") the same hedge
    how long till i get used to them      (after "i got new glasses") the same hedge

The rule is not "name the thing and send them to a website": a pointer on its own is not a reply,
because a person who is told "the maker's page has it" has learned nothing they did not already
know. STYLE.md's "Not knowing, honestly" gives the shape, and this file builds a reply of four
parts:

1. the part that cannot be checked, in a few words ("I can't check the schedule for that
   humidifier, sorry");
2. **what the bot does know about that kind of thing** - the shape of the job, the usual first
   step, what being behind looks like (`BY_KIND`, then `GENERAL_BY_PART`);
3. the one place that keeps the exact part, by kind (the maker's page, the label and the RHS, the
   optician, the paperwork, the venue's own page, the vet, the letter from the organisation);
4. one question, so the turn keeps going.

None of part 2 is a fact about one model: a habit of a whole kind of thing is not a made-up fact,
and a figure for a model nobody here has seen would be. The file knows where a kind of fact is
kept, and the shape of the job that produces it, so it can answer a kettle it has never heard of
without inventing anything.

The thing itself comes from the reading in `memory["understood"]`, then from the phrase after
`my/our/the/a`, then - for a follow-up that says only "it" - from the words of the turn before. It
stands down on every line where the missing part is somebody's own knowledge instead: a person the
bot has never met (`only_they_know.py`), a body or a live crisis (#answers, #safety), food, cooking,
a purchase, a judgement put to it, and a line that names nothing at all.

`bot/modules/greeting.py` asks this only where the composer's own reply is its hedge, so a line
with a card of its own never reaches it.
"""
import re

from . import fallback, pick

# The part of the answer the person is after. The first test that matches decides, so the method
# shapes are read before the figure ones: "how do i get the number" asks for the steps, not for a
# number the bot does not have either.
A_METHOD = re.compile(
    r"\bhow (?:do|can|could|should|would) i\b|\bhow to\b|\bwhats the best way\b|"
    r"\bwhat is the best way\b|\bhow do you\b")
A_TIME = re.compile(
    r"\bwhat time\b|\bwhat day\b|\bwhich day\b|\bhow soon\b|\bwhat date\b|\bwhen\b|"
    r"\bhow long (?:till|until|before|after|to)\b|\bopen (?:today|tomorrow|on)\b")
A_PLACE = re.compile(r"\bwhere\b")
A_FREQUENCY = re.compile(r"\bhow (?:often|frequently)\b|\bhow many times\b")
A_FIGURE = re.compile(
    r"\bhow (?:much|many|long|often|far|big|heavy|hot|old|deep|tall|wide)\b|"
    r"\bhow much\b|\bwhat (?:size|weight|percentage)\b|\bhow much does\b")
A_REASON = re.compile(r"\bwhy\b")

# The word the reply uses for the part it does not have.
PART_WORD = {
    "frequency": "the schedule",
    "figure": "the figure",
    "time": "the timing",
    "place": "the right place",
    "method": "the exact steps",
    "reason": "the reason",
}

# What kind of thing was named. One row per kind, and the row's words are the ones a person uses
# for it; anything that matches no row keeps the hedge, so a thing this file cannot place is never
# handed a keeper that does not fit it.
KINDS = (
    # Read first: a nebuliser ends in `-iser` and a CPAP is a machine in the house, but the plan
    # for either is written by a clinician, so the machine row's promise - "the maker's page has it
    # for the model on the rating plate" - is the wrong promise for them.
    ("clinical", re.compile(
        r"\b(?:tens|nebulisers?|nebulizers?|cpap|bipap|inhalers?|spacers?|crutches?|"
        r"walking (?:frame|stick|aid)|zimmer|catheters?|stoma|insulin|blood pressure monitor|"
        r"glucose meter|hearing aids?|compression (?:stocking|stockings|sleeve|sock|socks|tights)|"
        r"oxygen concentrator|feeding tube|peg tube)\b")),
    ("animal", re.compile(
        r"\b(?:dog|dogs|puppy|pup|cat|cats|kitten|rabbit|hamster|guinea pig|budgie|parrot|fish|"
        r"horse|pony|chickens?|hens?|ducks?|tortoise|snake|lizard|pet|pets|puppies|kittens)\b")),
    ("plant", re.compile(
        r"\b(?:plants?|trees?|shrubs?|roses?|tomato(?:es)?|potato(?:es)?|grass|lawn|hedge|"
        r"seedlings?|houseplants?|orchids?|cactus|fern|bulbs?|flowers?|vegetables?|herbs?|"
        r"garden|cuttings?|compost)\b")),
    # A machine in the house: it has a maker, a model number and a manual, and that is the whole
    # reason this kind can promise "the maker's page has it for the model on the rating plate".
    # The list is the kind's own vocabulary, so it is long on purpose - a thing left out of it is
    # read as `bought`, which may promise only the label and the shop.
    ("appliance", re.compile(
        r"\b(?:boiler|kettle|washer|washing machine|dishwasher|oven|cooker|hob|fridge|freezer|"
        r"fridge freezer|radiators?|heaters?|hoover|vacuum|dryer|tumble dryer|extractor|shower|"
        r"taps?|sink|mowers?|lawnmower|drill|microwave|toaster|iron|mattress|"
        r"humidifiers?|dehumidifiers?|air fryer|slow cooker|pressure cooker|bread maker|"
        r"breadmaker|coffee machine|blender|mixer|food processor|sewing machine|stitch|"
        r"strimmer|hedge trimmer|chainsaw|sander|pressure washer|jet wash|air conditioner|"
        r"air con|heat pump|fan|extractor fan|freezer|tumble|washer dryer|water softener|"
        r"\w+(?:ifier|ator|iser|izer))\b")),
    ("device", re.compile(
        r"\b(?:phone|laptop|tablet|computer|pc|router|wifi|broadband|console|smart watch|app|"
        r"account|email|password|website|browser|spreadsheet|software|printer|speaker|telly|tv|"
        r"television|privacy settings?)\b")),
    ("paper", re.compile(
        r"\b(?:bill|statement|letter|form|invoice|receipt|contract|ticket|warranty|guarantee|"
        r"passport|licence|license|payslip|tenancy|policy|quote|estimate|certificate|"
        r"application|booking|reservation|reference number)\b")),
    ("place", re.compile(
        r"\b(?:museum|castle|cathedral|minster|gallery|theatre|theater|zoo|park|beach|market|"
        r"library|station|airport|hotel|cafe|restaurant|pub|shop|store|supermarket|swimming pool|"
        r"leisure centre|farm|stadium|arena|church|abbey|palace|pier|harbour|harbor|city|town|"
        r"village|island|venue|exhibition)\b")),
    ("eyewear", re.compile(
        r"\b(?:glasses|specs|spectacles|contact lenses?|lenses|varifocals?|sunglasses)\b")),
    ("service", re.compile(
        r"\b(?:gp|doctor|dentist|vet|bank|council|school|nursery|surgery|hospital|insurance|"
        r"landlord|letting agent|solicitor|builder|plumber|electrician|garage|post office|"
        r"jobcentre|university|college)\b")),
)

# Where the part that cannot be seen is kept, by the kind of thing it is about. Each line is a
# place a person can open or ring in one step, and each one is true of every thing in its kind.
WHERE_IT_LIVES = {
    "animal": (
        "The vet or the practice's own page has it for the breed and the age, and the rehoming "
        "charity that matches the breed prints a figure too."),
    "plant": (
        "The label that came with that one has it, and the grower's or the RHS page keeps one by "
        "plant name and the time of year."),
    "appliance": (
        "The maker's own page has it for the model number on the rating plate, and the manual "
        "says it in the specification pages."),
    "device": (
        "The maker's support page has it for the model, and the settings screen on the thing "
        "itself shows what it is set to now."),
    "paper": (
        "The paperwork has it: the figure, the date and the reference are printed on the "
        "document itself, and the number to ring is on the back."),
    "place": (
        "The venue's own page or its map listing has it, and it changes with the day, so today's "
        "is the one that counts."),
    "eyewear": (
        "The optician who fitted them has it, and the practice's own page says what to expect and "
        "when to go back."),
    "service": (
        "The organisation's own page has it, and the number on your last letter from them reaches "
        "the desk that decides."),
    # A part is fitted rather than set: the manual for the whole machine is where the step is
    # written, and the old part is what the shop matches the new one against.
    "part": (
        "The manual or the fitting sheet for the thing it belongs to has the step for that part, "
        "and the maker's page has it for the model number, which is on the rating plate or the "
        "paperwork that came with it."),
    # The thing was bought or it arrived, so the shop and the maker are the two places that hold
    # whatever it is: a model number, a running cost, a way to reset it. This row is the one that
    # takes the things no list here has ever heard of - a humidifier, a bread maker, a punch bag -
    # and it is only used when the person's own line says they got it.
    "bought": (
        "The label or the paperwork that came with it is where its own numbers are, and the shop "
        "that sold it will tell you over the phone what it is and what it wants."),
    # Nothing was made here that keeps a calendar: the season sets it, and the people who keep
    # them know their own area's weather.
    "living": (
        "The people who keep them have it rather than a maker: the local association, the supplier "
        "you got them from, or a keeper a few years in will tell you the calendar for your area."),
    # Set by a person rather than a maker: the one who prescribed or fitted it wrote the plan
    # down, and the number to ring is on their letter.
    "clinical": (
        "Whoever prescribed or fitted it has it: the plan is written on the sheet they gave you, "
        "and the clinic or the pharmacist on that sheet answers a question about it."),
}

# The parts each kind of keeper can honestly hold. A mattress has a maker's page with a figure on
# it and a manual with steps in it, and neither of them knows where in the person's house the
# mattress goes, so "where do i put it" keeps the hedge instead of borrowing a page that does not
# answer it. A thing asked about a part its keeper does not hold keeps the hedge too.
HOLDS = {
    "animal": frozenset(("figure", "frequency", "method", "reason")),
    "part": frozenset(("method", "figure", "place")),
    "plant": frozenset(("figure", "frequency", "method", "reason", "time")),
    "appliance": frozenset(("figure", "frequency", "method", "reason")),
    "device": frozenset(("figure", "frequency", "method", "reason")),
    "paper": frozenset(("figure", "time")),
    "place": frozenset(("figure", "time", "place")),
    "eyewear": frozenset(("figure", "frequency", "method", "reason", "time")),
    "service": frozenset(("figure", "time", "place", "method")),
    "bought": frozenset(("figure", "frequency", "method", "reason")),
    "living": frozenset(("frequency", "method", "reason", "time")),
    "clinical": frozenset(("frequency", "method", "reason", "time")),
}

# A chicken in a roasting tin is dinner, and the vet has nothing to say about it: the cooking
# knowledge answers a cooking line, and a line this file cannot tell from one keeps the hedge.
COOKING = re.compile(
    r"\b(?:cook|cooks|cooked|cooking|roast|bake|boil|fry|grill|eat|eating|edible|recipe|oven|"
    r"marinade|defrost|reheat|serve|serving|portion|dinner|lunch|tea|pie|soup|stock|stuffing)\b")
# A purchase is a price, and a price is live: it is the composer's price note or the `worth`
# reader's turn, not a page that says where a figure is kept.
A_PURCHASE = re.compile(
    r"\b(?:new one|a new|to buy|buy|buys|buying|cheapest|price of|replace|replacement|"
    r"cost of a new|how much is|how much are)\b")

# The kinds that are a machine or part of one, and are the only kinds `GENERAL_BY_PART` may speak
# about. A plant does not work harder when it is busier, has no maker's page and no manual for its
# model, and the shop that sold it is a garden centre; a chandelier has no reset and a cast iron
# pan is not set by its rating plate. Sending these lines to every kind with no `BY_KIND` entry is
# how `i got a sarracenia / how often do i water it` came to be told about "the manual for the
# model" (@white-pot). Where a kind has no true general line it keeps the hedge, which is honest.
MADE = frozenset(("appliance", "device", "part"))

# What the bot does know about the kind of thing, before it says where the exact part lives.
#
# A pointer on its own is not an answer: "the maker's page has it" tells a person nothing they did
# not already know. Every line here is true of the whole kind rather than of one model - the shape
# of the job, the usual first step, what the sign of getting it wrong looks like - so the reply can
# lead with something the person can use and only then say where the exact figure or date is
# printed. Nothing is looked up and nothing is guessed: a fact about one model would be a made-up
# fact, and a habit of a whole kind of thing is not.
GENERAL_BY_PART = {
    "method": (
        "the first step is nearly always the same one - turn it off, wait, and start again from "
        "the beginning of the maker's own instructions",
        "the order matters more than the steps: the maker's list is written to be done from the "
        "top, and skipping ahead is what leaves a job half finished"),
    "frequency": (
        "how often it needs doing depends on how hard it works, so the busier it is the shorter "
        "the gap",
        "there is a usual interval and it moves with how much it is used, with the sign you are "
        "behind showing as a change you notice rather than a number"),
    "figure": (
        "the figure is set by the model and the size, so two of the same kind of thing can differ "
        "by a lot",
        "the number on the thing itself - the plate, the box, the letter - is the one that decides "
        "it, not the one in the advert"),
    "time": (
        "the timing is set by the calendar rather than by the person, so the season or the day is "
        "what to go by",
        "there is usually one date that matters and everything else is worked back from it"),
    "place": (
        "the usual place is the one that already does that job, rather than a special trip",
        "anywhere that sells or services the thing will know who locally does the rest"),
    "reason": (
        "there are usually two or three common causes, and which one it is shows in when it "
        "happens and what changes with it",
        "the way to tell the causes apart is to change one thing at a time and watch what "
        "changes"),
}

# The kinds where the general line can be sharper, because the whole kind behaves the same way.
BY_KIND = {
    ("bought", "frequency"): (
        "there is no number that fits every one of them: what it is made of, how much it is used "
        "and where it is kept all move it",
        "the sign you are behind shows in the thing itself rather than on a date - how it sounds, "
        "smells or looks changes before anything else does"),
    ("clinical", "frequency"): (
        "how often it is used is set by whoever prescribed it and by how you are doing, not by a "
        "number that fits everyone: the plan on their sheet is the one that counts",
        "the dose of it is the part that changes, so the gap between uses comes from the review "
        "rather than from the instruction leaflet"),
    ("clinical", "method"): (
        "the way to use it is the way it was shown to you, and the sheet or the clinic will show "
        "you again rather than leave you guessing",
        "the settings are the part to get right, so it is worth a phone call to the clinic rather "
        "than a guess at the dial"),
    ("clinical", "time"): (
        "how long you keep using it is theirs to say, and it is looked at again at the review they "
        "booked",
        "the length of it is set by how the thing it is for is healing rather than by the calendar"),
    ("living", "frequency"): (
        "how often it needs doing is set by the season and by how the animals are doing rather "
        "than by a maker: a look most weeks in the busy months and less in the cold, with the "
        "sign you are behind showing in them rather than in a number",
        "the calendar follows the year - the swarming months, the cold, the hungry gap - so two "
        "keepers in two places will not do it on the same week"),
    ("plant", "time"): (
        "garden jobs go by the season more than the calendar: sow while the soil is warm, plant "
        "bare-root things while they are dormant, prune most shrubs after they flower",
        "the soil and the weather decide the week, and the packet holds the variety and the "
        "depth"),
    ("plant", "frequency"): (
        "watering goes by the compost rather than the day: dry an inch down means water, damp "
        "means wait",
        "a feed every couple of weeks in the growing season is the usual, and nothing in winter"),
    ("part", "method"): (
        "the order is what matters: isolate it first - water off at the valve, or unplugged - then "
        "take the old part out and match it, because it comes out one way and goes back the same "
        "way",
        "the old part is the pattern: take it to the shop and match it rather than trusting a "
        "model number alone, since the same model can be made with two different fittings"),
    ("animal", "frequency"): (
        "how much and how often is set by the age and the weight more than the breed, and the two "
        "things worth watching are the weight and what is left in the bowl",
        "the amount goes up with age and down with age again, and a vet weighs the animal rather "
        "than guessing"),
    ("animal", "figure"): (
        "the figure is set by the age and the size of the animal rather than by the breed name",
        "the two numbers that matter are the weight and the amount, and the bag or the tin prints "
        "both"),
    ("appliance", "method"): (
        "nearly every appliance has a reset that the maker built in: off at the wall for a "
        "minute, then back on and let it finish starting up",
        "the model number is the thing to have in front of you - it is on the rating plate or "
        "inside the door - because the maker's steps are written for that model and not the one "
        "beside it"),
    ("device", "method"): (
        "the first step on nearly all of them is the same: restart it, then look for the setting "
        "the message named rather than changing several at once",
        "the settings screen shows what it is set to now, which is usually the thing that is "
        "wrong"),
    ("eyewear", "time"): (
        "most people are told a week or two to settle into new glasses, and the first thing to "
        "check is that they sit straight and level",
        "the first days are the ones that feel wrong, and a headache that lasts past that is "
        "worth going back with"),
    ("paper", "figure"): (
        "the document carries the figure, the date and a reference, and that reference is what "
        "unlocks the answer on the phone",
        "the number to ring is printed on the letter rather than found on a website"),
    ("place", "time"): (
        "opening hours move with the season, the day and the odd refurbishment, so the day itself "
        "is the one to check",
        "the hours on a listing are a snapshot, and the venue's own page is the one that is kept "
        "current"),
    ("service", "method"): (
        "the first step with any of them is to ask in writing and quote the reference, because "
        "that is what makes a record",
        "the desk that decides is reached by the number on their own letter, not the switchboard"),
    ("bought", "method"): (
        "the sheet, label or card that came with it is the shortest route, and the shop that sold "
        "it will tell you the way it is normally done",
        "the first step is the one written on whatever came in the box or on the label, and it is "
        "written for that thing rather than for its kind"),
}

# One question to end on, so the turn keeps going with what the person can say from where they
# stand. Nothing here asks for a fact the bot could have looked up itself.
TAIL = {
    "frequency": (
        "Say how it has been going so far and I will tell you what the usual is.",
        "Tell me what you have been doing with it and I will say whether that is enough.",),
    "figure": (
        "Tell me the number you are working from and I will do the arithmetic with you.",
        "Say what you are comparing it with and I will help you weigh it."),
    "time": (
        "Tell me when you need it by and I will work the timing back from that.",
        "Say what you are working around and I will lay out the order to do things in."),
    "place": (
        "Tell me which one you have in mind and I will say what to ask them.",),
    "method": (
        "Tell me what you have already tried and I will go through the next step with you.",),
    "reason": (
        "Tell me what you have noticed and I will say what usually causes it.",),
}

# A person, not a thing: nothing about them is kept on any page, so those lines are the reading in
# `only_they_know.py` and `their_day.py` and not this one.
A_PERSON = re.compile(
    r"\b(?:mum|mom|mother|dad|father|son|daughter|kid|kids|child|children|baby|toddler|"
    r"boss|manager|partner|husband|wife|boyfriend|girlfriend|friend|neighbour|neighbor|sister|"
    r"brother|gran|granny|nan|aunt|uncle|cousin|teacher|carer)\b")
# The subject has to be something, not a word doing another job in the sentence.
NOT_A_THING = frozenset("""
a an the it this that these those there here me you him her us them my your his its our their
something anything nothing everything one ones any some all more most less much many
thing things stuff
time times day days week weeks month months year years hour hours minute minutes
somebody anybody nobody everyone
new old secondhand second-hand little big small large same other good bad broken first next last
decent proper nice cheap expensive
got get gets got bought buy buying buyed ordered order arrived delivered picked treated
had have has want wants need needs keep keeps make makes made put puts use uses used
clean cleans cleaned fix fixes fixed change changes take takes took give gives gave
how what when where why which who whose often much many long soon till until
can could should would will shall may might must does did is are was were be been being am
about around anything something
at in on from with for to of by under over into near beside behind inside outside after before
during than like as per via onto upon within without across along towards toward through
""".split())
# The words that say the thing is in their hands: after one of these the person's own line has said
# they own it, and the shop that sold it is a place that holds what they are asking about.
# Coming by something, said in the past: "i got a humidifier", "we bought a bread maker", "it
# arrived on tuesday". A bare "get" is a job being asked about ("how do i get pet hair out of the
# drum") rather than a purchase, and it is not evidence that a shop holds anything at all.
GOT_IT = re.compile(
    r"\b(?:(?:i|we|he|she|they|mum|dad)\s+(?:have\s+|had\s+|just\s+|finally\s+)?"
    r"(?:got|bought|ordered|won|were given|was given|picked up|treated myself to)"
    r"|(?:it|they|this|that|the [a-z]+)\s+(?:has\s+|had\s+)?(?:arrived|come|turned up)"
    r"|\bdelivered\b)")


def _parts_of(said):
    """The part of the answer the line is after, by the first shape that matches."""
    for name, rule in (("method", A_METHOD), ("time", A_TIME), ("place", A_PLACE),
                       ("frequency", A_FREQUENCY), ("figure", A_FIGURE),
                       ("reason", A_REASON)):
        if rule.search(said):
            return name
    return ""


# An animal named as the source of a mess is not the thing being asked about. "how do i get pet
# hair out of the drum" says the pet is where the hair came from; the job is the drum and the hair,
# and the keeper for that is the maker's page, not the vet. The same holds for the animal's own
# bedding, bowl and lead, which are washed and cleaned rather than fed and walked.
ANIMAL_AS_A_SOURCE = re.compile(
    r"\b(?:pets?|dogs?|cats?|puppy|puppies|kitten|kittens|rabbit|hamster|horse|pony|tortoise|"
    r"parrot|budgie)\s+(?:'s\s+)?(?:hair|hairs|fur|fluff|moult|moulting|mess|poo|poop|poos|"
    r"wee|sick|vomit|smell|stink|stain|stains|mud|slobber|drool|spit|paw prints?|"
    r"footprints?|blanket|bed|basket|cage|hutch|litter|tray|toy|toys|lead|leash|collar|"
    r"bowl|bowls|food|biscuits|hairbrush|brush)\b")


def _kind_of(said):
    """The kind of thing the line names, or "" when it names none of them."""
    if ANIMAL_AS_A_SOURCE.search(said):
        return ""
    for kind, rule in KINDS:
        if rule.search(said):
            return kind
    return ""


SINGULAR_BUT_ENDS_IN_S = frozenset("""
mattress glass address gas bus dress class canvas tennis business harness lens iris
press stress boss mess
""".split())


# A line that points back at the thing instead of naming it: "how often do i clean it", "how long
# till they settle in". The thing is in the turn before, and a word the engine read out of this
# line ("seed" in "when should i seed it") is the act, not the thing.
REFERS_BACK = re.compile(
    r"\b(?:it|its|them|they|those|that one|this one|the one|that|this)\b")
A_DETERMINER = re.compile(r"\b(?:my|our|the|this|these|a|an)\s+[a-z]")


def _that(thing):
    """The word to put in front of the thing, singular or plural, from how people say it."""
    if thing.endswith("s") and thing not in SINGULAR_BUT_ENDS_IN_S:
        return "those"
    return "that"


# What is in food is a fact about the food, not about a thing's pages, and the answers side keeps
# it: a line asking about calories, protein or vitamins is not answered from here.
# A turn before that is still choosing what to buy: that choice is the answers lane's and the
# shop's, and a page of the maker's does not answer "which one".
A_BUYING_NOW = re.compile(
    r"\b(?:after an?|in the market|looking at an?|thinking (?:of|about) (?:buying|getting)|"
    r"should i (?:buy|get)|shall i (?:buy|get)|is it worth buying|which one (?:shall|should) i)\b")
NUTRITION = re.compile(
    r"\b(?:calorie|calories|kcal|protein|protien|carbs?|carbohydrate|vitamins?|fibre|fiber|"
    r"nutrients?|how many grams|grams? of)\b")


# Words that cannot be the last word of the thing: "how do i take the head off" names a head, and a
# thing called "head off" gets a reply about taking a head off something else entirely.
# The words people put between the determiner and the noun: "my new printer", "the little round
# filter", "our old bread maker". They say which one, never what it is, so the name starts after
# them and stops at the first word that is not one of them.
MODIFIERS = frozenset("""
new old older newer secondhand second-hand used brand little small big large long short tall wide
narrow round square tiny huge giant same other another good bad poor decent proper nice cheap
expensive pricey posh fancy rubbish rubbishy broken faulty dodgy spare extra main whole front back
top bottom side inner outer left right first second third last next previous electric electrical
manual digital smart wooden metal plastic glass stainless steel leather cotton woolen woollen
furry fluffy heavy light hard soft dark bright white black grey gray red blue green yellow pink
purple brown orange silver gold clear empty full wet dry hot cold warm cool clean dirty
""".split())


PARTICLES = frozenset("""
off on out up down back away apart over in into loose together around about through round
please again now then too also as well
""".split())


def _without_a_particle(phrase):
    words = phrase.split()
    while words and words[-1] in PARTICLES:
        words.pop()
    return " ".join(words)


def _a_thing_from(said, determiner_only=False):
    """The thing a person's own line names, by the words around it, or "".

    The understanding engine knows the words it has been taught, and the things people bring to a
    conversation are exactly the ones no list here has: a humidifier, a bread maker, a pair of
    glasses. So the words of the line are read here instead - the last run of ordinary words that
    is not a function word - and a run too short to be a thing is not one.
    """
    for match in re.finditer(
            r"\b(?:my|our|the|this|these|a|an)\s+([a-z][a-z'-]+(?:\s+[a-z][a-z'-]+){0,3})", said):
        # "the little round filter at the bottom" names a filter: the words people put in front of
        # the noun point at it and are not part of its name, and the noun phrase stops where the
        # person stops naming and starts saying something about it ("my lawn is patchy" is a lawn).
        words = match.group(1).split()
        while words and words[0] in MODIFIERS:
            words.pop(0)
        kept = []
        for word in words:
            if word in MODIFIERS or word in NOT_A_THING:
                break
            kept.append(word)
            if len(kept) == 2:
                break
        kept = _without_a_particle(" ".join(kept)).split()
        if kept:
            return " ".join(kept)
    if determiner_only:
        return ""
    words = re.findall(r"[a-z][a-z'-]+", said)
    run = []
    best = ""
    for word in words:
        if word in NOT_A_THING:
            if run:
                best = " ".join(run[-2:])
                run = []
            continue
        run.append(word)
    if run:
        best = " ".join(run[-2:])
    best = _without_a_particle(best.strip())
    if len(best) < 3 or not all(word.isalpha() for word in best.split()):
        return ""
    return best


# A person correcting themselves means the thing they said second. "the seal is fine, i mean the
# little round filter at the bottom" is a question about the filter, and the first phrase in the
# line is the one they have just ruled out.
CORRECTION = re.compile(
    r"\b(?:i mean|i meant|i mean't|sorry i mean|no i mean|rather than|not that,?|"
    r"i should have said|what i mean is)\b")


def _thing_named_in(text):
    """The thing a line names, read the way the line means it.

    A line that corrects itself means the second thing it says ("the seal is fine, i mean the
    little round filter at the bottom"): read straight through, the first phrase is the one the
    person has just ruled out, and a later question that only says "it" would keep pointing at a
    thing they have already taken back.
    """
    text = str(text or "")
    mark = CORRECTION.search(text)
    if mark:
        corrected = _a_thing_from(text[mark.end():], determiner_only=True)
        if corrected:
            return corrected
    return _a_thing_from(text)


def _the_thing(read, said, memory):
    """The thing the line is about, said the way the person said it, or "".

    The engine's own subject is used when it has one, because it has already weighed the whole
    line; then the last noun it recorded; then the words of the person's own line, which is where a
    thing no list here knows comes from. A follow-up that says only "it" takes the turn before,
    because the person has not changed what they are talking about - and that is exactly when the
    hedge names nothing.
    """
    before = _the_line_before(memory)
    before_text = str((before or {}).get("text") or "") if isinstance(before, dict) else ""
    named_before = _thing_named_in(before_text) if before_text else ""
    # A pronoun is the person telling you where to look, and a thing named later in the same line
    # is usually the object of the verb rather than the subject of the question: `i got a puppy /
    # how do i stop it chewing the furniture` is about the puppy, not the furniture (@white-pot).
    # The determiner only wins when it comes first - `the filter, how do i clean it` - which is the
    # line naming the thing outright.
    back = REFERS_BACK.search(said)
    points_back = bool(back) and not A_DETERMINER.search(said[:back.start()])
    if points_back and named_before:
        return named_before
    mark = CORRECTION.search(said)
    if mark:
        corrected = _a_thing_from(said[mark.end():], determiner_only=True)
        if corrected:
            return corrected
    named_now = _a_thing_from(said, determiner_only=True)
    if named_now:
        return named_now
    if isinstance(read, dict):
        subject = str(read.get("subject") or "").strip().lower()
        if subject and subject not in NOT_A_THING:
            return subject
        for ent in read.get("entities") or ():
            if not isinstance(ent, dict):
                continue
            text = str(ent.get("text") or "").strip().lower()
            if text and text not in NOT_A_THING:
                return text
    # The turn before, and only there, is read word by word: that is the line that named the
    # thing, and a question's own words ("how often do i clean it") are not a thing.
    before = _the_line_before(memory)
    if isinstance(before, dict):
        subject = str(before.get("subject") or "").strip().lower()
        if subject and subject not in NOT_A_THING:
            return subject
        for ent in before.get("entities") or ():
            if not isinstance(ent, dict):
                continue
            text = str(ent.get("text") or "").strip().lower()
            if text and text not in NOT_A_THING:
                return text
        named = _thing_named_in(str(before.get("text") or ""))
        if named:
            return named
    return ""


def before_text_from(memory):
    """The words of the person's previous line, or ""."""
    return str((_the_line_before(memory) or {}).get("text") or "")


def _the_line_before(memory):
    """The person's previous line, word for word, for a follow-up that names "it".

    The store keeps the words of every turn (`turns`, with `user` and `bot`), and the reading of
    the current line is on `understood`; the reading of an older line is not kept, so the words
    themselves are what this file reads. That is enough: the thing is named in the line, and this
    file only needs the name.
    """
    now = str((memory.get("understood") or {}).get("text") or "").strip().lower()
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns):
        said = str(turn.get("user") or "").strip()
        if said and said.lower() != now:
            return {"text": said}
    return None


# A kind is a property of the thing, and "bought" is not one: it says how the thing arrived, not
# what it is. A hive, a pond, a wormery and a colony are all things a person came by, and none of
# them has a maker who sets the calendar - the season and the animals themselves do, and the people
# who keep them are where the rest lives. Reading this after `bought` is what let `i got a beehive /
# how often does it need doing` be told about a model number.
LIVING = re.compile(
    r"\b(?:beehive|bee hive|hive|colony|nuc|bees|wormery|worms|compost|pond|aquarium|"
    r"fish tank|hens|chickens|quail|mushroom kit|starter|terrarium)\b")


# A possessive is not a purchase. "my knee is sore", "my hair is a mess", "my week is packed" say
# whose it is, not that it came in a box, and the maker's page and the shop hold nothing about any
# of them. The bought row is for things a person came by.
NOT_AN_OBJECT = frozenset("""
hair hairs head face back neck shoulder shoulders knee knees leg legs foot feet arm arms hand hands
finger fingers thumb skin eye eyes ear ears tooth teeth mouth tongue jaw stomach tummy belly gut
chest cough breath voice sleep mood temper day days week weeks weekend month months year years
time life job work shift shifts money rent bill bills debt weight appetite headache head cold
toenail nails toothache backache stress anxiety energy patience brain memory
""".split())


# The thing is already in the person's hands and is playing up: "the bread makers gone wrong",
# "my drill keeps stopping". A definite article and a fault is as good as "i got it" for knowing
# that the maker's page and the shop are the two places that hold the rest.
OWNED_ANYWAY = re.compile(
    r"\b(?:the|my|our)\s+[a-z][a-z' -]{0,26}?\b(?:is|are|was|were|has|have|had|keeps|kept|"
    r"went|gone|goes|stopped|stops|broke|broken|won't|wont|doesn't|doesnt|isn't|isnt|smells?|"
    r"makes?|making|sounds?|leaks?|leaking|arrived|turned up)\b")


# A part of something bigger: the head of a tap, the seal on a machine, the filter in the bottom of
# it. No maker has a reset for a seal and no rating plate on a tap head, and the honest knowledge is
# the order of a fitting job: isolate it, take the old one out, match it, put it back the way it
# came. These words are the parts people ask about on their own, and the thing they belong to is
# whatever the chat has been about.
# A thing on the body, or a thing fitted to it, is not a thing that came in a box. A wound has no
# label and no shop, a denture has no manual for its model, and a tattoo is not maintained from a
# maker's page: what keeps them right is a person - a nurse, a dentist, the artist who did it, a
# pharmacist - and `how often should i clean my wound` was told "what it is made of, how much it is
# used ... the label or the paperwork that came with it is where its own numbers are" (@white-pigeon).
# Read before `bought`, and the hedge stands rather than a page that does not exist.
ON_THE_BODY = re.compile(
    r"\b(?:wounds?|cuts?|grazes?|grazed|burns?|scalds?|blisters?|bruises?|rashes?|sores?|spots?|"
    r"ulcers?|abscess|scar|scars|stitches|staples|sutures|tattoos?|piercings?|fillings?|"
    r"crowns?|dentures?|denture|retainers?|aligners?|implants?|bridges?|veneer|veneers|"
    r"dentist|gums?|tooth|teeth|stump|amputation|prosthes[ie]s|prosthetic|stoma|colostomy|"
    r"dressings?|bandages?|plasters?|splints?|casts?|wig|wigs|toupee|hairpiece|"
    r"injection|injections|insulin pen|catheter|drip|line|port|pacemaker|coil|implant)\b")


# A device a clinician sets the plan for is not a machine with a maker's schedule and not a thing
# that came in a box either. A TENS machine, a nebuliser and a CPAP are used on the body and the
# dose of them - how often, how long, how strong - comes from whoever prescribed it and from how
# the person is doing, never from a label. `i got a tens machine / how often should i use it` was
# told "there is no number that fits every one of them: what it is made of, how hard it is used",
# which is maintenance language for something that is not maintenance (@white-pigeon).
CLINICAL = re.compile(
    r"\b(?:tens|tens machine|tens unit|nebuliser|nebulizer|cpap|bipap|inhaler|spacer|"
    r"crutch|crutches|walking (?:frame|stick|aid)|zimmer|catheter|stoma|insulin|"
    r"blood pressure monitor|blood sugar|glucose meter|hearing aid|hearing aids|"
    r"compression (?:stocking|stockings|sleeve|sock|socks|tights)|"
    r"oxygen|oxygen concentrator|feeding tube|peg tube|syringe driver)\b")


PART_OF_SOMETHING = frozenset("""
head seal seals filter filters drawer lid cap hose belt blade blades tray element washer valve
aerator spout handle handles sole soles heel heels zip zipper button buttons strap buckle wick
filament plug plugs gasket bearing impeller pump thermostat cartridge cartridges hinge catch latch
knob dial flange nut bolt screw screws
""".split())


def _kind_from_the_owning_line(memory, thing, said=""):
    """The kind of thing, when the person's own line says they got it, or "".

    A thing no list here knows still has a kind when the line that named it says it was bought or
    arrived: whatever it is, the shop that sold it and the maker's page hold its model number, its
    running cost and how to reset it.
    """
    if not thing:
        return ""
    sources = [(memory or {}).get("understood") or {}, _the_line_before(memory) or {},
               {"text": said}]
    for source in sources:
        text = str(source.get("text") or "").lower() if isinstance(source, dict) else ""
        if thing not in text:
            continue
        if all(word in NOT_AN_OBJECT for word in thing.split()):
            continue
        # "my humidifier", "our bread maker": the person has said it is theirs, so the maker's page
        # and the manual are the pages that hold it, whatever the thing turns out to be.
        if ("my " + thing in text or "our " + thing in text or GOT_IT.search(text)
                or OWNED_ANYWAY.search(text)):
            # A thing that is alive, or is a home for something alive, keeps its own calendar:
            # nothing about it is set by a maker or printed on a model plate.
            if LIVING.search(thing):
                return "living"
            if CLINICAL.search(thing):
                return "clinical"
            # Nothing on the body came in a box, whatever the line says about having it.
            if ON_THE_BODY.search(thing):
                return ""
            return "bought"
    return ""


# The parts `bought` can honestly hold, and what it says about them. A thing whose kind nothing
# here knows is often not a machine at all - a plant, a hive, a bag of compost - so the only lines
# that may be said about it are the ones that are true of anything a person came by.
BOUGHT_GENERAL = {
    "figure": (
        "the number on the thing itself, or on the label or paperwork that came with it, is the "
        "one that decides it rather than the one in the advert",
        "the size and the make are what the figure follows from, so two of the same kind of thing "
        "can differ by a lot"),
    "reason": (
        "there are usually two or three common causes, and which one it is shows in when it "
        "happens and what changes with it",
        "the way to tell the causes apart is to change one thing at a time and watch what "
        "changes"),
}


def _known(kind, part):
    """What this file can say about the kind of thing, before it says where the rest is.

    A kind only speaks about itself. `BY_KIND` is the sharpest and always wins; then the machine
    kinds, whose habits `GENERAL_BY_PART` describes; then `bought`, which may say only what is
    true of anything a person came by. Everything else returns nothing, and the hedge stands.
    """
    if (kind, part) in BY_KIND:
        return BY_KIND[(kind, part)]
    if kind in MADE:
        return GENERAL_BY_PART.get(part) or ()
    if kind == "bought":
        return BOUGHT_GENERAL.get(part) or ()
    return ()


def reply_for(text, memory=None, reply=""):
    """What is known about the thing, where the rest of it lives, and one question - or None."""
    if not fallback.is_a_hedge(reply):
        return None
    if fallback.in_a_safety_thread(memory or {}):
        return None
    said = str(text or "").lower()
    if not said.strip():
        return None
    if A_PERSON.search(said):
        return None
    if fallback._thread_is_about_the_body(memory or {}):
        return None
    read = (memory or {}).get("understood") if isinstance(memory, dict) else None
    read = read if isinstance(read, dict) else {}
    if (COOKING.search(said) or A_PURCHASE.search(said) or NUTRITION.search(said)
            or A_BUYING_NOW.search(before_text_from(memory or {}))):
        return None
    if ANIMAL_AS_A_SOURCE.search(said):
        return None
    thing = _the_thing(read, said, memory or {})
    if not thing:
        return None
    if ANIMAL_AS_A_SOURCE.search(thing):
        return None
    if A_PERSON.search(thing):
        return None
    kind = "part" if all(word in PART_OF_SOMETHING for word in thing.split()) else ""
    kind = kind or _kind_of(said) or _kind_of(thing)
    if not kind:
        before = _the_line_before(memory or {}) or {}
        kind = _kind_of(str((memory or {}).get("understood", {}).get("text") or ""))
        if not kind:
            kind = _kind_of(str(before.get("text") or ""))
    if not kind:
        kind = _kind_from_the_owning_line(memory or {}, thing, said)
    if not kind:
        return None
    part = _parts_of(said)
    if not part:
        return None
    if part not in HOLDS.get(kind, frozenset()):
        return None
    where = WHERE_IT_LIVES.get(kind)
    knowns = _known(kind, part)
    word = PART_WORD.get(part)
    tails = TAIL.get(part)
    if not where or not knowns or not word or not tails:
        return None
    # The shape of the reply is the one STYLE.md asks for where the bot does not know: the part it
    # cannot check said in a few words, then what it does know about the kind of thing, then the
    # one place that keeps the rest, then a question that keeps the turn going.
    options = tuple(
        "I can't check {word} for {dem} {thing}, sorry. What I can say is that {known}. "
        "{where} {tail}".format(
            word=word, dem=_that(thing), thing=thing, known=known, where=where, tail=tail)
        for known in knowns for tail in tails)
    return pick(options, read, said)
