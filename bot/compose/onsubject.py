"""A short follow-up with the subject left in the chat gets the subject named, not a search.

The decks are full of lines like "can he do that", "do i need an adapter there", "how long will
that take to clear", and every one of them reached the same honest hedge: "That's beyond what I
know well, sorry. Searching for it will turn up better sources than I can offer". The sentence is
true and it is the worst reply in the bot here, because the person has just told the bot what they
are talking about and the bot answers as if it had not been listening. A friend says the thing
back - "The rent, then" - and then says who does know: the tenancy team, the vet, the garage, the
operator's own site.

So this reads a follow-up that names nothing itself (short, no wh-word of its own subject, a
pronoun or a "that" for the thing), finds the word the chat is on from what the person said on the
earlier turns, and answers with that word and the one place that settles it. It is a hedge still -
the bot does not know the answer and says so - but it is a hedge that shows it followed the chat
and tells the person where to go, which is what STYLE.md asks for when the bot cannot know.

Nothing here is a fact about the world: the routes are places and people that exist for that kind
of question (a pharmacist, ACAS, the DVLA's own page), never a number, an hour or a rule.
"""
import re

# The line is a question about something already said: a short ask, no subject of its own.
A_ASK_OPENER = re.compile(
    r"^\s*(?:can|could|do|does|did|is|are|was|were|would|will|should|am|shall|have|has|had|"
    r"what|when|where|which|who|why|how|if)\b", re.I)
# "that", "it", "there", "him" - the thing is somewhere else, and somewhere else is the chat.
A_BACK_REFERENCE = re.compile(
    r"\b(?:it|that|this|there|he|she|they|him|her|them|one|those|these|hers|his|theirs)\b", re.I)
# A word of their own subject: "will that work on a wool one" asks about wool and is not this.
A_SUBJECT_WORD_LIMIT = 2
# A line with nothing of its own to be about: how many words of subject, and how long.
A_EMPTY_ASK_WORDS = 2
A_EMPTY_ASK_LENGTH = 7
A_EMPTY_ASK_OPENER = re.compile(r"^\s*(?:how|when)\b", re.I)
# A pointer ask - "which one", "who is it", "how come" - names the pointer and nothing else, and
# the pools for those already own the line (#9334). Naming a subject back to a line that says
# "which one" reads as an answer to a question nobody asked.
A_POINTER_ASK = re.compile(r"^\s*(?:which|who)\b|^\s*how\s+come\b", re.I)
# An ask for something to do about a person's distress - "what helps on a night like that" said of a
# 15-year-old crying over her gcses - is not a look-up about the thing named: the school office and
# the exam board have nothing for that night, and naming the gcse back reads cold. No place settles
# it, so this module stands down and the line goes wherever it went before.
A_HELP_ASK = re.compile(
    r"^\s*(?:what|anything)\s+(?:would\s+|will\s+|might\s+)?helps?\b|"
    r"^\s*what\s+(?:can|should|could)\s+(?:i|we)\s+do\b|"
    r"^\s*how\s+(?:do|can|should)\s+i\s+(?:help|calm|support|comfort|reassure)\b", re.I)
# A recall ask - "how many cats do i have", "when did we get him", "did you get that" - is a
# question about what the person said earlier, not about the world. The vet does not know how many
# cats somebody has and Shelter does not know when a tenancy started, so naming a place back is a
# wrong place, and the honest hedge the seed gives is the better answer.
A_RECALL_ASK = re.compile(
    r"^\s*(?:how many|how much)\b(?:(?!\bhow much (?:is|does|do|will|would)\b).)*?"
    r"\b(?:do i have|have i got|do we have|did i|did we|did he|did she)\b|"
    r"^\s*how many\b(?:\s+\w+){0,2}\s*$|^\s*how many\b.*\bagain\s*$|"
    r"^\s*what (?:day|date|time)\b|^\s*whats the (?:day|date|time)\b|"
    r"^\s*when (?:did|was that|were that|does my|is my|do i|are we)\b|"
    r"^\s*did you (?:get|catch|hear|note|remember|write)\b|"
    r"\b(?:what|how old|how long ago) (?:did|do|was) i (?:say|said|tell|told|mention|planning|"
    r"planning to do|doing)\b|\bdid i (?:say|tell|mention)\b", re.I)
# A comparison - "is that too far", "is that a lot", "is that worth it", "is that good for
# manchester" - asks what is normal, and nobody keeps that rule: a commute is too far for the
# person, not for ACAS. No place settles it, so this stands down and the hedge comes back.
A_COMPARISON_ASK = re.compile(
    r"\b(?:too (?:far|much|long|late|early|expensive|cheap|old|big|small)|worth it|a lot|"
    r"any good|good value|cheaper|expensive|good for|reasonable|enough)\b|"
    r"\b(?:is|was|would) (?:that|it|this) (?:good|bad|fair|ok|okay|decent)\b", re.I)
# A cooking cue in the ask means the chat is about food, whatever else was on the table: "sorry i
# meant a turkey" / "how long to rest it" is a bird in an oven, and the operator's own site is the
# wrong place for it. Cooking has its own answers; where it has none, the hedge is honest.
# A cooking time is a rule with one missing quantity in it, and the rule is the bot's: a chicken
# is 20 minutes per 500g plus 20 at 190C, beef 15 to 25 minutes per 500g once it has browned,
# eggs 6 to 10 minutes from boiling water. "how long to roast it" names no food at all and has no
# line above it, so there is no entry to reach and nothing to read a subject off - and the search
# hedge is the wrong answer twice over: the bot does know the rule, and what it is short of is the
# food and its weight, not the whole question. Two foods are named because naming one would decide
# what "it" is, and the shape follows the method that was asked about: a grilling or a resting time
# is not a roasting time, so those keep the hedge.
A_COOKING_TIME_ASK = re.compile(r"\bhow long\b", re.I)
A_FOOD_PRONOUN = re.compile(r"\b(?:it|them|those|that)\b", re.I)
A_ROASTING_WORD = re.compile(r"\b(?:roast|roasting|roasted|bake|baking|baked|oven)\b", re.I)
A_BOILING_WORD = re.compile(r"\b(?:boil|boiling|boiled|simmer|simmering)\b", re.I)
# The methods whose time the two rules above do not cover: a grilled or fried thing, or one
# resting, is not the oven rule and not the egg one, so those keep the hedge.
A_OTHER_METHOD = re.compile(
    r"\b(?:grill|grilling|grilled|fry|frying|fried|rest|resting|steam|steaming|poach|poaching|"
    r"barbecue|barbeque|bbq|microwave|air fryer|toast|toasting)\b", re.I)
A_NAMED_FOOD = re.compile(
    r"\b(?:chicken|turkey|beef|lamb|pork|ham|gammon|duck|goose|joint|steak|sausage|"
    r"sausages|fish|salmon|potato|potatoes|egg|eggs|rice|pasta|bread|cake|pastry|pie|"
    r"casserole|stew|chops|chop|brisket|shoulder|leg|breast|thigh|fillet|kettle)\b", re.I)
COOKING_TIME_SHAPES = {
    "oven": "Time depends on what it is and how heavy: a chicken is about 20 minutes per 500g plus "
            "20 minutes at 190C, and a joint of beef 15 to 25 minutes per 500g once it has browned. "
            "Tell me which it is and how much it weighs, and I'll do the sum.",
    "boil": "Boiling time depends on what they are: eggs are 6 minutes from boiling water for a "
            "runny yolk and 9 to 10 for a hard one. Tell me what it is and I'll narrow it down.",
    # "cook" says neither oven nor pan, so both rules are named rather than one being picked.
    "either": "Time depends on the food and how it is cooked: a chicken is about 20 minutes per "
              "500g plus 20 minutes at 190C in the oven, and eggs are 6 minutes from boiling "
              "water for a runny yolk. Tell me what it is and how you are cooking it.",
}
A_COOKING_ASK = re.compile(
    r"\b(?:cook|cooking|cooked|roast|roasting|bake|baking|boil|boiling|fry|frying|grill|oven|"
    r"freezer|fridge|thaw|defrost|stuffing|gravy|rice|pasta|potato|potatoes|recipe|rest it)\b",
    re.I)
# A word that is a computer before it is a car: "my laptop battery dies fast" / "is it safe" is not
# a garage question.
# Lost or left behind: the ask is where it is or what to do now, and no clause about a thing's
# age or its paperwork settles that.
A_LOST_THING = re.compile(
    r"\b(?:lost|mislaid|misplaced|can'?t find|cannot find)\b|"
    r"\bleft (?:it|them|my|the|his|her)\b[^.?!]*\b(?:in|on|at|by)\b", re.I)
A_MACHINE_CUE = re.compile(
    r"\b(?:laptop|computer|phone|tablet|charger|charging|screen|windows|macbook|pc)\b", re.I)
# A line that is itself a question is not a thing the chat is on.
A_A_QUESTION_ASK = re.compile(
    r"^\s*(?:what|whats|when|whens|where|wheres|which|who|whos|why|whys|how|hows|is|are|was|"
    r"were|do|does|did|can|could|should|would|will|shall|have|has|am|any|anything)\b", re.I)
# A judgement put to the bot - "is that a stupid idea", "would that be mad" - is about the person,
# not about a place that settles facts, and naming the bank back to "should i take money from work"
# answers a question nobody asked.
A_JUDGEMENT_ASK = re.compile(
    r"\b(?:stupid|silly|daft|mad|unreasonable|out of order|selfish|allowed)\b", re.I)
# A judgement about an amount - "my salary is 2400 a month" / "is that good for manchester" - is a
# comparison, not a rule nobody wrote down: no bank's rule says what is good, so naming the bank
# that keeps the rule sends the person to a desk that cannot answer. The plain hedge is the honest
# reply, so this stands down and lets it through.
A_JUDGEMENT_OF_AMOUNT = re.compile(
    r"\b(?:is|was|would) (?:that|it|this) (?:good|bad|ok|okay|enough|fair|normal|reasonable|"
    r"a lot|too much|too little|decent)\b", re.I)
# Where the reply's place is a keeper of rules rather than a judge of amounts.
AMOUNT_KINDS = ("money", "bills")
# Where the word in the kind is a machine of the person's before it is the thing the place
# repairs: "battery" is a laptop's here, not a car's.
MACHINE_BEFORE_MACHINE_KINDS = ("car",)
# An ask for the words: "how do i write to him about it", "what do i say to them". "I can\'t talk
# you through it without seeing it" is false about words, so these get their own shape. The words
# verb has to be what is being asked for: "can they do that without asking" has the word inside a
# clause about the doing, and answering it with "I can\'t put the words in your mouth" answers a
# question nobody asked.
A_WORDS_ASK = re.compile(
    r"^\s*(?:what|whats|how|hows|should|shall|can you|could you|would you|do i need to|give me|"
    r"help me)\b[^?]*\b(?:write|writing|word|words|say|saying|tell|telling|ask|asking|reply|"
    r"answer|email|letter|phone|ring|call|complain|phrase)\b", re.I)
# A naming ask - "what should i call it", "what shall we name him" - is a question about the
# person's taste, not about the world: no vet has an opinion on a cat's name, so naming a place
# would be a wrong place, and "call" is not an ask for the words to say to somebody either.
A_NAMING_ASK = re.compile(
    r"\b(?:should|shall|will|would|can|could|do|to) (?:i|we|you) (?:call|name)\b|"
    r"\b(?:call|name) (?:it|him|her|them)\b", re.I)
# A word that is only a place when a preposition puts it there: "at work", "to school" name where
# somebody was, not the subject of the chat ("my mum keeps ringing me at work" is the calls).
A_PLACE_WORD = frozenset(("work", "school", "college", "hospital", "bank", "town", "city",
                          "flat", "flats", "home", "house", "garage"))
# ... and the same word after a place preposition and one determiner is still the place: "in a
# flat" is where the puppy would live, not the tenancy.
A_DETERMINER = frozenset(("a", "an", "the", "my", "our", "your", "his", "her", "their", "this"))
A_PLACE_PREP = frozenset(("at", "to", "from", "in", "into", "near", "off", "for", "of", "on"))
# Keys that are the small verb of a follow-up rather than the thing it is about: "how long can he
# leave it like that" is about the landlord, and "leave" is a key in the work kind. These never
# decide what the chat is on and never stand the reading down.
# A line that explains the one before it does not set the subject: "hes said the boiler needs
# replacing too so thats why" comes after a landlord putting the rent up, and "is that even
# allowed" is about the rent rise, not about the boiler.
A_EXPLANATION = re.compile(r"\b(?:thats why|that is why|because|so that|the reason)\b", re.I)
# A key whose word means the thing only when its neighbour says so. "washing" is a machine in a
# kitchen and a wash in a drum: "my jeans came up tight after a wash" / "will they give a bit"
# answered "The washing, then ... a plumber will confirm it on the phone", which offers a plumber
# for a pair of jeans. The word on its own is too light to be the thing the chat is on.
A_NEEDS_A_NEIGHBOUR = {
    "washing": frozenset(("machine", "machines", "powder", "liquid", "detergent", "basket",
                          "line", "drum", "load", "cycle")),
}
# What the reply calls a key when the key is only half the name, or is not a noun at all: "the
# washing machine", not "the washing"; and "i was sacked last week" / "can they do that" is the
# job, never "The sacked, then".
A_SHOWN_AS = {"washing": "washing machine", "sacked": "job"}
# A line with a subject of its own is not a bare follow-up: "the dial doesnt work" / "what about
# the little one shes 3" is a child with an age, not the oven three turns back.
A_ITS_OWN_SUBJECT = re.compile(
    r"\b(?:little one|little man|youngest|eldest|oldest|the baby)\b"
    r"|\b(?:he|she|they|him|her|them|son|daughter|child|kid|boy|girl)\b[^?]{0,12}\b\d+\b",
    re.I)
# A car line whose ask is not the paperwork: a garage answers a repair, the DVLA never does.
A_DVLA_WORD = re.compile(r"\b(?:mot|dvla|tax|sorn|licence|license|log ?book|v5|clamped)\b", re.I)
WHO_CAR_GARAGE = "a garage will tell you over the phone"

A_LIGHT_KEY = frozenset(("leave", "pay", "order", "booking", "paint", "drill", "work", "delivery",
                         "bid", "invoice", "credit", "deal", "cover", "fill", "charge", "term"))

STOP = frozenset("""
a an the and or but if so then than that this those these i me my mine you your yours we us our he
she it they them him her his hers their there here what which who whom whose when where why how do
does did done doing is are was were be been being am have has had having will would can could
should shall may might must not no nor yes ok okay just also too very really quite about for with
without on in into at by from to of as up down out off over under again more most much many any
some all both each either neither other another same such own only ever never always still yet
already even though although because while since until before after during against between among
right well thing things stuff get got give take make made say said tell told want wanted need
needed like liked know knew think thought feel felt go going went come came back put let try tried
use used find found work works working day days time times week weeks month months year years one
two three four five six seven eight nine ten bit lot lots sort kind way ways now today tomorrow
yesterday please thanks thank hi hello hey yeah yep nope um uh oh ah eh due anyway gonna wanna dont
doesnt didnt isnt wasnt cant couldnt wouldnt shouldnt havent hasnt im ive id ill youre youve theyre
thats whats heres theres whose wont
""".split())

# The kind of thing the chat is on, most specific first, and inside each kind the word a person
# would recognise. The first word of the chat that matches is the one the reply names, so "rent"
# comes out as the rent rather than as money, and "boiler" as the boiler rather than the heating.
KINDS = (
    ("tenancy", ("landlord", "tenancy", "tenant", "tenants", "deposit", "eviction", "lease",
                 "letting", "lettings", "rent", "flat", "flats")),
    ("pet", ("vet", "puppy", "puppies", "kitten", "kittens", "dog", "dogs", "cat", "cats",
             "rabbit", "rabbits", "hamster", "guinea", "parrot", "fleas", "flea", "litter")),
    ("car", ("mot", "tyre", "tyres", "brake", "brakes", "clutch", "gearbox", "engine", "battery",
             "batteries", "hybrid", "mileage", "garage", "mechanic", "dvla", "car", "cars")),
    ("bills", ("bill", "bills", "electric", "electricity", "energy", "supplier", "meter",
               "standing", "tariff", "direct", "debit", "arrears")),
    ("health", ("prescription", "pharmacist", "pharmacy", "symptom", "symptoms", "migraine",
                "infection", "swelling", "swollen", "rash", "piles", "pain", "dose", "tablets",
                "tablet", "medicine", "doctor", "hospital", "nurse", "clinic", "surgery")),
    ("work", ("sacked", "redundancy", "disciplinary", "warning", "rota", "shift", "shifts",
              "overtime", "payslip", "employer", "manager", "boss", "hr", "union", "interview",
              "contract", "job", "workplace", "work", "leave")),
    ("school", ("gcse", "gcses", "a-level", "a-levels", "exam", "exams", "revision", "homework",
                "teacher", "lesson", "lessons", "school", "college", "university", "ucas",
                "course", "term", "paper", "papers")),
    ("home", ("boiler", "radiator", "radiators", "thermostat", "dishwasher", "washer", "washing",
              "fridge", "freezer", "oven", "hob", "toilet", "shower", "leak", "leaking", "damp",
              "mould", "ceiling", "roof", "gutter", "gutters", "socket", "wiring", "plumber",
              "electrician", "limescale", "drain", "drains", "filter", "pump", "tap", "taps")),
    ("diy", ("curtain", "curtains", "rail", "drill", "shelf", "shelves", "paint", "wall", "walls",
             "screw", "screws", "rawplug", "rawplugs", "tile", "tiles", "tiling", "grout",
             "sanding", "filler", "sealant", "flatpack")),
    ("travel", ("passport", "visa", "boarding", "luggage", "suitcase", "adapter", "plug",
                "flight", "flights", "airport", "hotel", "train", "booking", "holiday",
                "abroad", "japan", "spain", "france", "italy", "greece", "portugal", "germany",
                "holland", "turkey", "egypt", "mexico", "canada", "america", "australia",
                "ireland", "scotland", "wales", "england", "london", "paris", "rome", "madrid",
                "lisbon")),
    ("shopping", ("receipt", "refund", "returns", "warranty", "guarantee", "seller", "order",
                  "delivery", "shop", "store")),
    ("money", ("overdraft", "mortgage", "loan", "loan", "benefits", "universal", "pension",
               "savings", "debt", "invoice", "bill", "bills", "tax", "salary", "wages", "wage",
               "pay", "bank", "credit", "budget", "money")),
)

# Places that are said without "the": "Japan, then", not "The japan, then".
PLACES = frozenset((
    "japan", "spain", "france", "italy", "greece", "portugal", "germany", "holland", "turkey",
    "egypt", "mexico", "canada", "america", "australia", "ireland", "scotland", "wales",
    "england", "london", "manchester", "birmingham", "edinburgh", "cardiff", "belfast",
    "dublin", "paris", "rome", "madrid", "lisbon", "new", "york", "florida", "california",
))

# A passport is a document, not a trip: the operator's own site and the airline have nothing to
# say about renewing one, and gov.uk says all of it.
A_PASSPORT_WORD = frozenset(("passport", "passports", "visa", "visas"))
WHO_PASSPORT = "gov.uk's own page states it, and the passport office will confirm it on the phone"
# A verb that acts on a thing the person owns. Said straight after a country named in passing, the
# thing acted on is not the country: "we are in spain for a week in june" / "do i need to renew it"
# is a passport, so this stands down rather than point at the airline.
A_THING_VERB_ASK = re.compile(
    r"\b(?:renew|renewing|cancel|cancelling|canceled|refund|rebook|upgrade|print|return)\b",
    re.I)

# Who settles it, for that kind of thing. A place that exists, never a rule or a number.
WHO = {
    "tenancy": "Shelter's advice line or your council's tenancy team will tell you what the rule "
               "is",
    "pet": "your vet's reception will answer that in one call, and the breeder or rescue you got "
           "them from knows the rest",
    "car": "a garage will tell you over the phone, and the DVLA's own page has the rule",
    "bills": "your supplier will say what their own rules are, and Citizens Advice has the free "
             "script for asking them",
    "health": "a pharmacist will settle it across the counter, and 111 if it cannot wait",
    "work": "ACAS will tell you where you stand in one free call, and your contract says what "
            "was agreed",
    "school": "the school office will tell you, and the exam board's specification says it in "
              "writing",
    "home": "the manual for that model says what it does, and a plumber will confirm it on the "
            "phone",
    "diy": "the instructions that came with it say, and anyone behind the counter at a builders' "
           "merchant will tell you",
    "travel": "the operator's own site states it, and the airline or the hotel will confirm it "
              "in a message",
    "shopping": "the shop's own page states it, and their chat will confirm it in writing",
    "money": "your bank or the office that runs it has the exact rule in writing",
}

# The shape of the ask, so the hedge says the right thing it cannot do.
# What the reply knows comes first and what it cannot do comes after it, because the substance is
# the answer and the apology is not: "The warning, then. What settles it is the dates and what was
# put in writing. I can't say yes or no from here; ACAS will tell you where you stand." Reading
# "I can't say yes or no to that from here, sorry" first told the person nothing for a whole
# sentence, and the review said so.
SHAPES = {
    "howlong": "{subject}, then. {on} I can't put a time on that from here; {who}.",
    "yesno": "{subject}, then. {on} I can't say yes or no from here; {who}.",
    "how": "{subject}, then. {on} I can't talk you through it without seeing it; {who}.",
    "what": "{subject}, then. {on} That one is past what I know well; {who}.",
    "words": "{subject}, then. Keep it to three lines, say what you want and by when; {who}.",
    "howmuch": "I haven't got a figure for {subject}, and a guessed one is worse than none. "
               "{on} {who}.",
}


# A pointer on its own is not a reply (STYLE.md, "Not knowing, honestly"): before the answer is
# given up on, the knowledge base is asked about the thing the chat is on, and what it knows is
# said first. It is the line the person said themselves that is asked about - "my rent is going up
# 50 pounds" reaches the rent-rise entry, "i cant afford the electric bill" reaches the payment
# plan - because that line is the matter in hand and the follow-up is the same matter asked about.
# Only where the follow-up names no kind of its own: an ask about the adapter for a trip to Spain
# would otherwise be answered with what to see in Barcelona, which is what the travel entry for
# Spain says.
# An open ask about the thing itself is the one the entry for the line before answers: "what do i
# do now", "what would you do about it", "what does that mean". An ask about one part of it -
# "what shall we name him", "how much work a week" - is not answered by that entry, and what the
# entry says would answer a question nobody asked (a naming question is not a settling-in
# checklist), so those keep the first step and the place instead.
A_OPEN_ASK = re.compile(
    r"\bwhat (?:do|should|shall|can|could|would) (?:i|we|you|they) do\b|"
    r"\bwhat (?:happens|now|next)\b|\bwhat does (?:that|it|this) mean\b", re.I)
A_KNOWS_IT = 0.6
A_WORD = re.compile(r"[a-z0-9']+")
# When the knowledge base has nothing on the subject, the reply still says what the answer turns
# on, which is true of every question of that kind and is what a friend says before naming who
# knows. A pointer on its own is not a reply. The clause is about the matter, never a rule or a
# figure: "what settles it is the agreement and what is in writing" cannot be wrong.
A_TURNS_ON = {
    "tenancy": "what settles it is the agreement and what is in writing",
    "pet": "what settles it is the age and the breed",
    "car": "what settles it is the age, the mileage and the last MOT",
    "bills": "what settles it is the account and what the supplier has already been told",
    "health": "what settles it is how long it has gone on and what has already been tried",
    "work": "what settles it is the dates and what was put in writing",
    "school": "what settles it is the subject, the board and the dates",
    "home": "what settles it is the model and when it started",
    "diy": "what settles it is the size and what it is fixed to",
    "travel": "what settles it is the booking reference and the dates",
    "shopping": "what settles it is the receipt and the date you bought it",
    "money": "what settles it is the account and the figures",
}


def _words(line):
    return re.findall(r"[a-z']+", str(line or "").lower())


def _bare_follow_up(clean):
    """The line when it is a short ask about something said earlier, else None."""
    text = " ".join(str(clean or "").lower().split())
    if not text or len(_words(text)) > 8:
        return None
    if not (A_ASK_OPENER.match(text) or text.rstrip().endswith("?")):
        return None
    subject = [w for w in _words(text) if w not in STOP and len(w) > 2]
    if len(subject) > A_SUBJECT_WORD_LIMIT:
        return None
    if not A_BACK_REFERENCE.search(text):
        # "how long do i have to wait" carries no pronoun and is still about the boiler said a
        # turn ago: a line this short with nothing in it to be about has nothing else to be
        # about. Anything longer without a back reference ("do i need an appointment") waits for
        # the same words plus the thing.
        if (len(subject) > A_EMPTY_ASK_WORDS or len(_words(text)) > A_EMPTY_ASK_LENGTH
                or not A_EMPTY_ASK_OPENER.match(text)):
            return None
    return text


def _stem(word):
    """The part of a word that stays the same when it is inflected.

    A KINDS key and a word in the line have to meet by stem or "sack" misses "sacked", which is
    the shape that sent a person to a garage: "the car passed its mot" / "can they sack me now"
    answered "The mot, then ... the DVLA's own page has the rule". So the key "sacked" and the
    word "sack" are the same word here, and so are "tyre"/"tyres", "bug"/"bugs".
    """
    word = str(word or "").lower().strip("'")
    for suffix in ("ing", "ies", "ied", "es", "ed", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            word = word[:-len(suffix)]
            break
    if len(word) > 3 and word.endswith("e"):
        word = word[:-1]
    return word


def _only_a_place(words, index):
    """True when the word at index only ever appears as the place: "at work", "in a flat"."""
    before = words[index - 1] if index > 0 else ""
    if before in A_PLACE_PREP:
        return True
    if before in A_DETERMINER and index > 1 and words[index - 2] in A_PLACE_PREP:
        return True
    return False


def _beside(words, index, allowed):
    """True when the word either side of this one is in allowed: "washing machine", "a drum wash"."""
    if index > 0 and words[index - 1] in allowed:
        return True
    return index + 1 < len(words) and words[index + 1] in allowed


def _named(line, skip_place_words=False, light=True):
    """[(the word from KINDS that the line says, the kind)] for one line, in KINDS order."""
    words = _words(line)
    said = {}
    for index, word in enumerate(words):
        said.setdefault(_stem(word), []).append(index)
    found = []
    for kind, keys in KINDS:
        for key in keys:
            places = said.get(_stem(key))
            if not places:
                continue
            if light and key in A_LIGHT_KEY:
                continue
            neighbour = A_NEEDS_A_NEIGHBOUR.get(key)
            if neighbour and not any(_beside(words, index, neighbour) for index in places):
                continue
            if skip_place_words and key in A_PLACE_WORD and all(
                    _only_a_place(words, index) for index in places):
                # "at work", "in a flat": where somebody or something was, not the chat's subject.
                continue
            found.append((key, kind))
            break
    return found


def _the_subject(memory, clean=""):
    """(the word the chat is on, the kind of thing it is, the line it came from) or blanks."""
    now = " ".join(str(clean or "").lower().split())
    lines = []
    topic = memory.get("topic") if isinstance(memory, dict) else None
    # The store moves the topic onto the line it is answering even when that line names nothing,
    # and the turn being answered is already in the turns: either one read back here would say
    # "the adapter" for "do i need an adapter there" and miss Japan, which is the whole subject.
    if isinstance(topic, dict) and topic.get("text"):
        said = " ".join(str(topic["text"]).lower().split())
        if said and said != now:
            lines.append(str(topic["text"]))
    turns = list(memory.get("turns") or []) if isinstance(memory, dict) else []
    for turn in reversed(turns[-5:]):
        if not isinstance(turn, dict) or not turn.get("user"):
            continue
        said = " ".join(str(turn["user"]).lower().split())
        if said and said != now:
            lines.append(str(turn["user"]))
    # What the chat is on is a thing said earlier: a word in the ask itself picks the subject only
    # when the newest line could be about either of two things, and the ask says which. "i have an
    # interview on friday and they asked about money" / "how do i ask about the money" names the
    # money, not the interview; "im off to japan in april" / "do i need an adapter there" names
    # Japan, not the adapter, because that line is about one thing already.
    # The subject is a thing the person said, so a line that only explains the one before it is
    # read only when there is nothing else.
    # The subject is a thing the person said a line or two ago, and it is a statement, not a
    # question they asked earlier: "we have a dog, a spaniel" / "whats my job" / "does she need a
    # walk every day" is the dog, and "how do i get rid of them" in the middle of a chat is not a
    # subject at all. Reaching further back is how "how do i save faster" after "it takes forever"
    # became the housing and "do they need a gift list thing" after "what would you get" the
    # budget: the ask then names one thing and points at the place for another.
    said_things = []
    for turn in reversed(turns):
        if not isinstance(turn, dict) or not turn.get("user"):
            continue
        said = " ".join(str(turn["user"]).lower().split())
        if not said or said == now or A_A_QUESTION_ASK.match(said):
            continue
        if A_EXPLANATION.search(said):
            continue
        said_things.append(str(turn["user"]))
        if len(said_things) == 2:
            break
    if not said_things:
        return "", "", ""
    newest = _named(said_things[0], skip_place_words=True)
    if len({kind for _word, kind in newest}) > 1:
        for word, kind in _named(now, skip_place_words=True):
            if kind in {named_kind for _word, named_kind in newest}:
                return word, kind, now
    for line in said_things:
        named = _named(line, skip_place_words=True)
        if named:
            word, kind = named[0]
            return word, kind, line
    return "", "", ""


def _already_the_who(word, kind):
    """True when the reply's own place is this word, so saying it back would repeat it.

    "the pharmacist gave me tablets for the rash" / "how often do i take them" said back as "The
    pharmacist, then ... a pharmacist will settle it across the counter" repeats the place inside
    one breath. The thing beside it in the same line is the better subject.
    """
    stem = _stem(word)
    return any(_stem(each) == stem for each in _words(WHO.get(kind) or ""))


def _beside_the_who(line, kind, subject):
    """Another word of the same kind in the line, when the subject is already the reply's place.

    Only a thing will do: a place name is the other half of the sentence ("we booked a hotel in
    rome" is not a figure for Rome), and a light key is a word the line says in passing.
    """
    keys = dict(KINDS).get(kind) or ()
    by_stem = {}
    for key in keys:
        by_stem.setdefault(_stem(key), key)
    for word in _words(line):
        key = by_stem.get(_stem(word))
        if not key or key == subject or key in A_LIGHT_KEY or key in PLACES:
            continue
        if _already_the_who(key, kind):
            continue
        return key
    return ""


def _shape(text):
    if A_WORDS_ASK.match(text):
        # "how do i write to him about it": the thing the bot cannot do is write it, not see it.
        return "words"
    if re.search(r"\bhow long\b", text) or re.search(r"\bhow soon\b", text):
        return "howlong"
    if re.search(r"\bhow much\b", text) or re.search(r"\bhow many\b", text):
        return "howmuch"
    if re.match(r"^\s*how\b", text):
        return "how"
    if re.match(r"^\s*(?:what|which|who|when|where)\b", text):
        return "what"
    return "yesno"


def _content(text):
    """The words of a sentence that carry its meaning, for telling it from one already said."""
    return [word for word in A_WORD.findall(str(text or "").lower()) if len(word) > 3]


def _already_said(sentence, memory):
    """True when the bot has said most of this sentence already, in its last few replies."""
    mine = _content(sentence)
    if not mine:
        return True
    seen = set()
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in list(turns or [])[-3:]:
        if isinstance(turn, dict):
            seen.update(_content(turn.get("bot")))
    if not seen:
        return False
    return sum(1 for word in mine if word in seen) >= A_KNOWS_IT * len(mine)


def _one_sentence(text, limit=250):
    """The first sentence of an answer, cut at a clause if it runs long, for a short reply."""
    said = " ".join(str(text or "").split())
    stop = said.find(". ")
    if 40 < stop < limit:
        said = said[:stop + 1]
    if len(said) > limit:
        cut = said.rfind(", ", 0, limit - 3)
        if cut < 100:
            cut = said.rfind(" ", 0, limit - 3)
        said = said[:max(cut, 100)].rstrip(" ,;:-") + ", and"
    # A whole sentence of a quoted letter is not a whole quote: "ask for a date: "Hi - I reported
    # the boiler on [date]" left the mark open once the sentence was cut. The part before the
    # quote still says what to do, so the quote goes rather than being closed by guesswork.
    for opener in ('"', "(", "["):
        if said.count(opener) % 2:
            at = said.rfind(opener)
            if at > 40:
                said = said[:at].rstrip(" ,;:-")
    return said


def _cap(clause):
    """A clause that starts a sentence gets a capital; one used mid-sentence does not."""
    clause = str(clause or "")
    return clause[0].upper() + clause[1:] if clause else clause


# A question with "there" in it is a question about the place the chat named, and the one thing a
# pointer cannot do that an answer can is put the place back into the line and answer it: "do i
# need an adapter there" after a week in Spain is "do i need an adapter in spain", which the
# knowledge base answers with the sockets and the voltage. So the place is taken out of the line
# the person said, spliced into the ask, and the answers lane is asked once more; a hedge back
# means nothing of its own claimed the result and the generic reply is used as before. This is
# what turns the whole class - adapters, plugs, driving, tipping, water, currency, visas - from a
# pointer into an answer, for every place rather than the one in the deck.
A_THERE = re.compile(r"\bthere\b", re.I)
# Not a place, though it comes after "in": a month, a week, a part of the day, or the small words
# of a phrase. "we are in spain for a week in june" names two of them before it names Spain.
A_NOT_A_PLACE = frozenset((
    "january", "february", "march", "april", "may", "june", "july", "august", "september",
    "october", "november", "december", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep",
    "sept", "oct", "nov", "dec", "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "week", "weeks", "weekend", "month", "months", "year", "years", "day",
    "days", "morning", "afternoon", "evening", "night", "spring", "summer", "autumn", "winter",
    "a", "an", "the", "my", "our", "your", "his", "her", "their", "this", "that", "these",
    "those", "it", "them", "all", "some", "any", "no", "one", "two", "three", "ten", "twenty",
    "future", "past", "total", "general", "fact", "particular", "touch", "writing", "person",
    "which", "what", "order", "case", "time", "front", "bed", "hospital", "work", "school",
))
A_NAMED_PLACE = re.compile(r"\b(?:in|to|at|from|visiting|visit)\s+([a-z][\w'-]*)", re.I)
# "is there", "are there", "there is": the subject of that clause is the thing asked about, not a
# place the chat named.
A_REPEAT_LEAD = re.compile(r"^same (?:as before|answer)\b[^:]{0,40}:", re.I)
A_EXISTENTIAL_THERE = re.compile(
    r"\b(?:is|are|was|were|isn't|aren't|wasn't|weren't)\s+there\b|\bthere(?:'s| is| are| was| were)\b",
    re.I)


def _the_place(line):
    """The place the subject's line names, when it names one: "we are in spain" -> "spain"."""
    for match in A_NAMED_PLACE.finditer(str(line or "").lower()):
        word = match.group(1)
        if word not in A_NOT_A_PLACE and word not in STOP and len(word) > 2:
            return word
    return None


def _the_answer_about_the_place(text, line, memory):
    """What the bot knows about the ask with the place put back into it, or "".

    "do i need an adapter there" is asked of the answers lane as "do i need an adapter in spain".
    Only a real answer is taken: the search hedge back means no entry claims that question, and
    the reply below is the better one after all.
    """
    if not A_THERE.search(text):
        return ""
    # Two "there"s are not the place. "is there anything i can do" and "was there a queue" are the
    # existential one, and nothing follows from a country for them. And a how-long ask is about
    # somebody's stay rather than about what to see: "my husband is working in germany" / "how
    # long is he there for" was answered with a five-day itinerary of Berlin and Munich.
    if A_EXISTENTIAL_THERE.search(text) or _shape(text) == "howlong":
        return ""
    place = _the_place(line)
    if not place:
        return ""
    spliced = A_THERE.sub("in " + place, text, count=1)
    # The memory the lane is asked with is the lines of the chat and nothing else. Its own record
    # of what it said last turn is left behind on purpose: asked with that, it answers "Same
    # answer, and it covers this" about the country entry - the one the subject's line already
    # got - instead of the question with the place in it. The new line is a new question, and a
    # question with the place said out loud is one it has not been asked yet.
    chat = memory if isinstance(memory, dict) else {}
    clean = {"turns": [turn for turn in (chat.get("turns") or []) if isinstance(turn, dict)]}
    try:
        # Imported here: the answers lane is the biggest module in the bot, and this path runs on
        # the few lines that ask about a place.
        from . import fallback
        from ..modules import answers
        answer = answers.respond(spliced, clean)
    except Exception:
        return ""
    if not answer or not str(answer).strip():
        return ""
    from . import fallback
    if fallback._in_a_pool(str(answer), (fallback.UNKNOWN,)):
        return ""
    # Two sentences is the room a reply has; the rest of the entry is a page, not a message.
    first = _one_sentence(str(answer))
    rest = str(answer)[len(first):].strip()
    second = _one_sentence(rest)
    said = (first + (" " + second if second else "")).strip()
    # A head that points back at the last answer - "Same as before: Spain: Barcelona for a city
    # and a beach" - is the answers lane saying it has nothing new, so it is not taken: the reply
    # below says what it can and who settles the rest instead of repeating a card.
    if A_REPEAT_LEAD.match(said):
        return ""
    # The answer has to be about the place for this to be an answer about the place. "we are going
    # to book" gives the place "book", and the answer that comes back is a novel; "how to lose" is
    # "lose". An entry that answers about the place names it, so a reply that never says it is not
    # this question's answer.
    if place.lower() not in said.lower():
        return ""
    return said


def _what_it_knows(line, memory):
    """One sentence the knowledge base has about the thing the chat is on, or "".

    `line` is the line the subject came from, as the person said it. The entry is looked up by
    that line's own reading, so the words stay in the knowledge base and nothing about the world
    is written here. A sentence the bot has already said is no good to the person twice, so the
    second one is used when the first is on their screen, and "" when the whole answer is.
    """
    line = " ".join(str(line or "").split())
    if not line:
        return ""
    try:
        # Imported here: this reading fires on one line in forty, and the knowledge base is the
        # heaviest thing in the bot to load.
        from ..knowledge import lookup
        from ..understanding import understand
        from . import fallback
        reading = understand(line)
        entry = lookup.find(reading)
        if entry is None:
            return ""
        answer = entry.reply
        if callable(answer):
            answer = answer({}, reading)
        if not isinstance(answer, str) or not answer.strip():
            return ""
        if fallback._in_a_pool(answer, (fallback.UNKNOWN,)):
            return ""
    except Exception:  # noqa: BLE001 - a lookup that fails knows nothing, and says so
        return ""
    for sentence in re.split(r"(?<=[.!?])\s+", " ".join(answer.split())):
        if len(sentence) < 40 or _already_said(sentence, memory):
            continue
        return _one_sentence(sentence)
    return ""


def _the_line_before(chat, now):
    """The newest line the person said that names a place, and is not the ask itself."""
    for turn in reversed(list(chat.get("turns") or [])[-3:]):
        if not isinstance(turn, dict) or not turn.get("user"):
            continue
        said = str(turn["user"])
        if " ".join(said.lower().split()) == now:
            continue
        if _the_place(said):
            return said
    return ""


def place_pool(clean, understood=None, memory=None):
    """A there-ask about the place the chat named, where the line names no subject at all.

    "were off to orlando in october" / "do i need an adapter there" reaches no key: the reading
    knows no subject word in Orlando, so `pool` passes and the seed fallback gives the search
    hedge. The place is the whole of what that question needs, so the place goes back into the
    ask and the answers lane answers it. It answers only where the seed would have hedged, so
    this is still a last resort, and nothing is said that the knowledge base does not say.
    """
    text = _bare_follow_up(clean)
    if text is None or not A_THERE.search(text) or A_EXISTENTIAL_THERE.search(text):
        return None
    if _shape(text) == "howlong":
        return None
    # The same lines the follow-up reading turns away from, for the same reasons: a recall is the
    # bot's own memory, a naming is the person's taste, and an ask about a part of something is
    # not a question the place answers.
    if A_POINTER_ASK.match(text) or A_HELP_ASK.match(text) or A_JUDGEMENT_ASK.search(text):
        return None
    if A_RECALL_ASK.search(text) or A_COMPARISON_ASK.search(text) or A_COOKING_ASK.search(text):
        return None
    if A_NAMING_ASK.search(text) or A_ITS_OWN_SUBJECT.search(text):
        return None
    chat = memory if isinstance(memory, dict) else {}
    try:
        from . import fallback
        if not fallback._in_a_pool(fallback.reply_for(clean, chat), (fallback.UNKNOWN,)):
            return None
    except Exception:  # noqa: BLE001 - a broken composer keeps its own turn
        return None
    line = _the_line_before(chat, text)
    if not line:
        return None
    answer = _the_answer_about_the_place(text, line, chat)
    place = _the_place(line)
    if not answer or not place:
        return None
    return "%s, then. %s" % (_cap(place), answer)


def _food_above(memory):
    """True when a recent line is already about food, so the chat can answer this one."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in (turns or [])[-6:]:
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if A_COOKING_ASK.search(said) or A_NAMED_FOOD.search(said) or A_ROASTING_WORD.search(said):
            return True
    return False


def pool(clean, understood=None, memory=None):
    """The honest line for a follow-up whose subject is only in the chat, or None."""
    text = _bare_follow_up(clean)
    if text is None:
        return None
    if A_POINTER_ASK.match(text) or A_HELP_ASK.match(text) or A_JUDGEMENT_ASK.search(text):
        return None
    if A_NAMING_ASK.search(text):
        return None
    if A_ITS_OWN_SUBJECT.search(text):
        return None
    subject = _the_subject(memory or {}, text)[0]
    if not subject and A_COOKING_TIME_ASK.search(text) and A_FOOD_PRONOUN.search(text) \
            and not A_NAMED_FOOD.search(text) and not _food_above(memory or {}):
        # "how long to roast it" with nothing above it: no food named and no line to read a
        # subject off, and the rule is the bot's own - so the rule and the one missing quantity,
        # not a search hedge. Only where the chat names no subject and no line above is about
        # food: "how do i make pancakes" / "how long do i cook them" is a food chat, and what the
        # chat already said answers it better than a rule of thumb.
        if A_ROASTING_WORD.search(text):
            return COOKING_TIME_SHAPES["oven"]
        if A_BOILING_WORD.search(text):
            return COOKING_TIME_SHAPES["boil"]
        if A_COOKING_ASK.search(text) and not A_OTHER_METHOD.search(text):
            return COOKING_TIME_SHAPES["either"]
    if A_RECALL_ASK.search(text) or A_COMPARISON_ASK.search(text) or A_COOKING_ASK.search(text):
        return None
    subject, kind, line = _the_subject(memory or {}, text)
    if not subject:
        return None
    # The ask names a kind of its own that the chat is not on: "the car passed its mot" / "can
    # they sack me now" is about the sack, and standing down is right when this cannot tell which
    # thing the person means. A wrong place is worse than the hedge it replaces.
    if line != text:
        mine = [named_kind for _word, named_kind in _named(text, skip_place_words=True)]
        if mine and kind not in mine:
            return None
    who = WHO.get(kind)
    if not who:
        return None
    if kind in AMOUNT_KINDS and A_JUDGEMENT_OF_AMOUNT.search(text):
        return None
    if kind in MACHINE_BEFORE_MACHINE_KINDS and A_MACHINE_CUE.search(line):
        return None
    if A_LOST_THING.search(str(line or "")):
        # A thing that is lost or left somewhere is not a thing with a history: "i left my coat in
        # the car" / "is there anything i can do" was answered with the age, the mileage and the
        # last MOT, and a garage will not find a coat.
        return None
    if _already_the_who(subject, kind):
        subject = _beside_the_who(line, kind, subject) or subject
    if subject in PLACES and A_THING_VERB_ASK.search(text):
        return None
    if subject in A_PASSPORT_WORD:
        who = WHO_PASSPORT
    if kind == "car" and not (A_DVLA_WORD.search(text) or A_DVLA_WORD.search(str(line or ""))):
        # "the car is in the garage" / "how long will that take": a garage answers that, and the
        # DVLA has nothing to say about a repair.
        who = WHO_CAR_GARAGE
    said = subject if subject in PLACES else "the " + A_SHOWN_AS.get(subject, subject)
    shape_kind = _shape(text)
    shape = SHAPES[shape_kind]
    # A subject that opens the line is a name and gets a capital; one used inside the sentence
    # ("I haven't got a figure for the mot") does not.
    if shape.startswith("{subject}"):
        said = said[0].upper() + said[1:]
    # What the bot does know about the thing, before where the rest is. Two things have to be
    # true for that to be an answer to this line rather than to the line before it. The ask must
    # name nothing of its own - "do i need an adapter there" after a holiday asks about the
    # adapter, and the travel entry for the country would answer a different question - and it
    # must be an open one ("what do i do now", "what happens next"), because the entry answers
    # the thing itself. An ask with a verb of its own asks something the entry was not written
    # for: "can he just ignore it" and "is that dangerous" would both be handed a letter
    # template, which is how a reply stops being an answer and becomes noise.
    known = ""
    if A_OPEN_ASK.search(text) and not _named(text, skip_place_words=True):
        known = _what_it_knows(line, memory or {})
    whole = ""
    if not known:
        # "do i need an adapter there": the place goes back into the line and the answers lane is
        # asked the question with the place in it, which is one the knowledge base answers.
        whole = _the_answer_about_the_place(text, line, memory or {})
    if whole:
        # The entry answered the question that was asked, so there is nothing left to point at:
        # "In Spain the sockets are type C and E" needs no airline to confirm it.
        return f"{said}, then. {whole}"
    if known:
        # A sentence of what the bot knows ends with its mark, and the place is a new sentence;
        # a clause of it is joined with a semicolon. Either way the reply says the thing first.
        ends = known[-1:] in ".!?"
        join = " " if ends else "; "
        place = _cap(who) if ends else who
        if shape_kind == "howmuch":
            return (f"I haven't got a figure for {said}, and a guessed one is worse than none - "
                    f"{known}{join}{place}.")
        return f"{said}, then. {known}{join}{place}."
    # When there is nothing on the subject in the knowledge base, the reply still says what the
    # answer turns on before it names who knows. The shape keeps its own honesty, because that is
    # what this one cannot do ("I haven't got a figure", "I can't put a time on that").
    turns_on = A_TURNS_ON.get(kind)
    # The words shape already says what to put in it ("keep it to three lines, say what you want
    # and by when"), so the first step is not said twice.
    on = ""
    if turns_on and shape_kind != "words":
        on = turns_on[0].upper() + turns_on[1:] + "."
    reply = shape.format(subject=said, on=on, who=who)
    return re.sub(r"\s+", " ", reply).replace(" .", ".").strip()
