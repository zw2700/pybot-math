"""The answer the bot does not hold, and the one place that has it.

Nothing in the bot knew "whats the postcode for buckingham palace", "find me a plumber near me"
or "who plays in the beatles". The composer's honest pool answered all three with the same
sentence - "a quick search online will get you a solid answer" - which is true, and useless: it
names neither the thing that was asked about nor the place that holds it, so a person is told to
go and look without being told where. The decks are full of turns like these, and the bot has one
job in all of them: say in a few words what it cannot see (a branch's hours, who works near you,
a figure nobody has told it) and name the one thing that can, then stay for the part that is
still the bot's.

So this reads the shape of the ask and the thing named in it, and answers with the route a
friend would give:

* a place, an address, a postcode or a phone number -> a map app, which has all four at once;
* somebody to do a job -> a directory sorted by reviews, and two quotes before booking;
* something to do or stay in somewhere -> the reviews and the visitor site, in that order;
* a fact about a named thing, a band or a person -> the page that keeps it, with its sources;
* a figure about the world -> the same page, because a guessed number is the one thing worse
  than no number;
* a journey -> a map app or a journey planner, which knows the roads it has never seen;
* "how many do I need" for a material -> the two measurements, and the bot does the sum itself;
* where to buy a thing -> a map app search, and ring before setting off.

Every reader returns None for what it cannot route better than the hedge, and the hedge is what
a line with no shape here keeps. Nothing is ever filled in with an invented fact: the whole point
of the route is that the bot says what it does not know and hands over the one place that does.
"""

import re

# ---------------------------------------------------------------- shared words

def _has(line, phrases):
    """True when one of the phrases is in the line as a whole word or phrase.

    Whole words, because "stop" holds "top" and "goodbye" holds "good": a request for help with a
    cramp is not a request for the best of anything.
    """
    for phrase in phrases:
        if re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", line):
            return True
    return False


def _words(line):
    return set(re.findall(r"[a-z0-9']+", line))


def _names_one_of(line, phrases):
    """True when the line names one of the things, as a whole word or a whole phrase.

    Splitting every phrase into single words is how "things to do" matched the "thing" and the
    "to" of "how do i make a good impression", and it is why this takes each phrase as it stands.
    """
    words = _words(line)
    for phrase in phrases:
        parts = phrase.split()
        if len(parts) == 1:
            if parts[0] in words:
                return True
        elif re.search(r"(?<![a-z0-9])" + r"\s+".join(re.escape(part) for part in parts) +
                       r"(?![a-z0-9])", line):
            return True
    return False


# A thing in the person's own life, not a fact about the world: "how old is my mum" wants an
# answer only she has, and no page anywhere keeps it.
OWN_PERSON = frozenset("""
my our his her their i me we us myself himself herself yourself husband wife partner boyfriend
girlfriend fiance fiancee mum mom mother dad father son daughter kid kids child children baby
nan nana grandma grandad granny sister brother friend friends boss manager landlord landlady
neighbour neighbor colleague carer stepmum stepdad stepson stepdaughter nephew niece
""".split())
# "He", "she" and "they" with nobody named: the question is about whoever the last turn was
# about, and a page online does not know who that is.
NOBODY_NAMED = frozenset("""
it that this these those he she they him her them you your me us i we someone somebody anyone
anybody everyone everybody something anything nothing
""".split())
# Asking the bot about itself is not a fact to look up.
ABOUT_THE_BOT = ("made you", "created you", "built you", "who are you", "what are you",
                 "who made u", "who created u", "made u", "your name", "were you made",
                 "invented you", "designed you")

# ---------------------------------------------------------------- where it lives

# Where a thing is, and how to reach it: one map app holds the address, the postcode, the phone
# number and the hours at once, which is what a person would say without thinking about it.
CONTACT_ASKS = ("postcode", "postal code", "phone number", "telephone number", "telephone",
                "contact number", "contact details", "their number", "the number for",
                "number for the", "whats the number", "what's the number", "what is the number",
                "the address", "address of", "address for")
WHERE_ASKS = ("where is the", "where's the", "wheres the", "weres the", "where is a",
              "where is an", "where can i find", "where do i find", "nearest branch",
              "nearest one", "nearest shop", "nearest store", "nearest office",
              "closest branch", "nearest chemist", "nearest pharmacy")
# The kinds of place people ask the way to. A "where is the" question about a part of a machine,
# a point, or a feeling is not this: "where is the filter on a washing machine", "wheres the
# point of any of it" and "where's the best place to put it" name no place at all.
PLACE_NOUNS = ("station", "airport", "office", "shop", "store", "supermarket", "bank",
               "post office", "tip", "recycling centre", "dump", "library", "pool",
               "swimming pool", "leisure centre", "park", "car park", "car park", "surgery",
               "pharmacy", "chemist", "hospital", "museum", "hotel", "restaurant", "pub",
               "cafe", "church", "cathedral", "school", "college", "university", "market",
               "garage", "petrol station", "bus stop", "train station", "coach station",
               "toilets", "loo", "customer service", "reception", "depot", "showroom",
               "river", "lake", "mountain", "hill", "beach", "coast", "forest", "wood",
               "castle", "palace", "bridge", "square", "street", "road", "lane", "avenue",
               "village", "town", "city", "centre", "center")
# A question about the person's own parcle, order or appointment is a tracking question, and a
# map app answers none of it.
NOT_A_PLACE = re.compile(
    r"(?<![a-z])(?:parcel|order|delivery|refund|application|claim|appointment|interview|"
    r"flight|connection|luggage|suitcase|passport|keys|wallet|phone|remote|charger|filter|"
    r"point of|point in|sense of|point to|best place to put|best place for it)(?![a-z])")
# A "where is" inside a phrase being learned or translated is the words, not the place: "how
# do you say 'where is the train station' in french" wants the french for it, and the station
# never comes into it. A line that starts with "who" has a page of its own and no address.
NOT_A_LOOKUP = re.compile(
    r"^\s*who\b|(?<![a-z])(?:how do you say|how do i say|how would you say|how to say|"
    r"what does [a-z' ]{1,20} mean|translate|in french|in spanish|in german|in italian|"
    r"in welsh)(?![a-z])")
# A pointer on its own is not a reply: every line here leads with the thing that makes the answer
# move under the bot's feet (an address changes hands, a catalogue turns over, a tide turns) and
# only then says where the rest is. The rule comes from the lane: lead with what the bot knows -
# the usual options, what to look for, the first step - and point at the rest afterwards.
PLACE_POOL = (
    "A postcode, a phone number and opening hours all change hands, so I can't hold them: a "
    "map app turns the name into the address, the postcode and the number, and the place's "
    "own page has today's hours.",
    "The place's own page is the one with today's hours, and a map app has the address and "
    "the number, so tell me what they say and I'll help with the rest - I can't look either "
    "up from here.",
)
# How to get somewhere: a journey planner knows the roads, the changes and the times, and none of
# that is knowable from here. Only a line that names a way of travelling or two places? A "how do
# i get to sleep" is not a journey, and "how far in advance should i book" is not one either.
TRAVEL_WORDS = ("train", "trains", "station", "airport", "coach", "bus", "buses", "flight",
                "flights", "plane", "ferry", "tram", "tube", "underground", "motorway", "road",
                "drive", "driving", "journey", "commute", "cycle", "walk", "route", "miles",
                "distance", "terminals", "platform", "coast", "beach", "island", "seaside",
                "harbour", "harbor", "port", "stadium", "venue", "town centre", "city centre")
GET_TO_ASKS = ("how do i get to", "how do you get to", "how do i get from", "how to get to",
               "how to get from", "directions to", "the way to", "get to", "get from",
               "way to get to", "way to get from", "way into town")
ROUTE_ASKS = re.compile(
    r"(?<![a-z])(?:how far (?:is|are) (?:it |that )?(?:from|away from)|"
    r"how many miles (?:is it |are there )?from|"
    r"how long does it take to (?:get|travel|drive|walk|cycle|go)\b|"
    r"how far is it\b|best route from|distance (?:from|between))(?![a-z])")
NOT_A_JOURNEY = ("in advance", "get over", "get fit", "get better", "get decent", "get going",
                 "get there with", "how do i get a", "how do i get my", "how do i get more",
                 "how do i get rid", "how do i get out of", "get toned", "get crispy",
                 "get to sleep", "get up", "get through", "get started", "get going",
         "get a passport", "get an appointment", "get a visa", "get my passport",
         "get a driving test", "get my licence", "get a refund", "get pregnant")
# The "how long does it take to" arm needs ground as well as a verb: with a place named, the
# journey is the planner's; with only a distance named, the pace is the bot's own sum.
TAKE_TO_ASKS = re.compile(r"(?<![a-z])how long does it take to(?![a-z])")
# Words that are somewhere to go, as opposed to a way of getting about. "Walk" and "cycle" on
# their own say nothing about where the journey ends.
GOES_TO = tuple(PLACE_NOUNS) + ("airport", "station", "town", "city", "coast", "beach",
                                "work", "school", "office", "home", "town centre",
                                "city centre", "train station", "bus stop")
PLACE_ROUTE_POOL = (
    "Miles and minutes depend on the roads on the day, which is why a journey planner is the "
    "one to ask - I can't measure one from here: put the two places in and it gives the "
    "distance and the time in one go.",
    "The roads decide it rather than the map, so I can't give you the miles and the time "
    "myself: put the two places into a map app and it'll have both; say what you're planning "
    "and I'll help with the rest of it.",
)

# Somebody to do a job: the trade is named and the line asks for one. "how do i complain about a
# plumber" and "my cat died, do i need a solicitor" name a trade and want something else, so the
# frame has to be a request and the line has to be clear of anything else that owns it.
TRADES = ("plumber", "electrician", "builder", "builders", "roofer", "painter", "decorator",
          "joiner", "carpenter", "plasterer", "tiler", "gardener", "cleaner", "locksmith",
          "boiler engineer", "gas engineer", "heating engineer", "accountant", "bookkeeper",
          "solicitor", "lawyer", "conveyancer", "dentist", "optician", "vet", "mechanic",
          "tutor", "physio", "physiotherapist", "chiropodist", "hairdresser", "barber",
          "mover", "movers", "removals", "surveyor", "architect", "tree surgeon",
          "pest controller", "chimney sweep", "appliance repair", "man with a van")
HIRING = ("find", "recommend", "any good", "know a", "know any", "know of", "looking for",
          "need a", "need an", "need someone", "someone who", "near me", "nearby", "local",
          "in my area", "can anyone", "suggest", "anybody", "anyone", "ne1", "some1", "any1")
# A trade word inside another thing is not a person to hire.
NOT_A_TRADE = ("vacuum cleaner", "steam cleaner", "carpet cleaner", "oven cleaner",
               "drain cleaner", "glass cleaner", "mascara", "lawyered")
# "Do I need a plumber or can I fix it myself" is a decision about the job, and "my cat died, do
# i need a solicitor" is a bereavement with a trade word in it. Both keep their own reply.
NOT_A_HIRE = ("do i need a", "do i need an", "will i need a", "will i need an",
              "should i get a", "should i get an", "myself", "died", "death", "bereave",
              "funeral", "complaint", "complain", "how do i", "how to", "why did",
              "my own", "sack", "dismiss", "tribunal", "quote from", "already got",
              "says i need", "told me i need", "said i need", "joining", "joined",
              "registered with", "agreeing a price with", "already have", "already seeing")
# The person's own dentist, vet or solicitor is not somebody to recommend: "my dentist says i
# need a crown" is a question about the crown.
OWN_PROFESSIONAL = re.compile(
    r"(?<![a-z])my\s+(?:[a-z]+\s+){0,2}(?:" + "|".join(TRADES) + r")(?![a-z])")
# Two kinds of ask, because they are found two ways. A trade quotes for a job, and two quotes and
# a registration check are how that goes; a professional is seen rather than hired, and the
# question there is whether they take new patients and how long the wait is. One pool for both
# said "get two written quotes" to a person looking for a dentist.
# A garage quotes for a job like a trade does - a written estimate, the price agreed before the
# work, the old parts back - and it is the one professional-looking trade that was in the list
# above but not here, so "can anyone recommend a mechanic" asked him whether he was taking new
# patients and how long the wait was. A wait and a fee is the dentist's question; a second quote
# is the garage's.
QUOTING_TRADES = ("plumber", "electrician", "builder", "builders", "roofer", "painter",
                  "decorator", "joiner", "carpenter", "plasterer", "tiler", "gardener",
                  "locksmith", "boiler engineer", "gas engineer", "heating engineer", "mover",
                  "movers", "removals", "tree surgeon", "pest controller", "chimney sweep",
                  "appliance repair", "man with a van", "cleaner", "mechanic")
TRADE_POOL = (
    "Who is any good and who is free changes month to month, so I can't vouch for one: a "
    "directory or map app search for {trade} near you sorted by the recent reviews, then two "
    "written quotes before you book anyone.",
    "The recent reviews are what tells you and I can't see them from here: a map app search "
    "for {trade} near you sorted by reviews is the quickest way in; ask for two quotes, and "
    "check they're registered before you pay a deposit.",
)
# A professional is rung rather than hired: whether they take new business, and how long the wait
# is, are the two things that decide it, and neither is here. The word for that cannot be
# "patients": this pool is drawn for every professional the trade list knows, so a lawyer, a
# hairdresser and an accountant were all told to ask whether they were taking new patients. "New
# people" is true of a dentist and of a solicitor, which is the test every line here has to pass.
PROFESSIONAL_POOL = (
    "Whether they're taking new people and how long the wait is are the two things that "
    "decide it, and neither is something I can see: a map app or the profession's own finder "
    "lists them by area - ring two and ask about the wait and the fee before you go.",
    "The wait and the fee are the parts that decide it and I can't see either from here: a "
    "map app or the official finder for {trade} near you shows who is taking on new people, so "
    "read the recent reviews and ring before you set off.",
)

# "The best beach in cornwall", "a good pub in york": what is on the ground somewhere the bot has
# never been. The head is a thing a person picks between in a place - not every "good thing in a
# place" sentence, which would take "is oat milk good in tea" and "a good way to hide them in
# food" with it.
PICKED_IN_A_PLACE = (
    "place", "places", "area", "part", "parts", "bit", "side", "neighbourhood", "neighborhood",
    "quarter", "hotel", "hotels", "restaurant", "restaurants", "pub", "pubs", "bar", "bars",
    "cafe", "cafes", "café", "beach", "beaches", "town", "city", "village", "park", "museum",
    "museums", "gallery", "market", "markets", "spot", "spots", "stay", "campsite", "campsites",
    "site", "sites", "walk", "walks", "swim", "swimming", "view", "coffee", "breakfast",
    "brunch", "chippy", "takeaway", "shop", "shops", "things to do", "thing to do",
    "things to see", "day out", "day trip", "beer garden")
PICK_ASKS = ("best", "top", "good", "nice", "decent", "recommend", "worth", "which")
# "The best time to book", "a good time to go" and "is a diesel worth it in town": a time or a
# purchase in a place is a question about when or whether, not a pick between the places there.
NOT_A_PICK = ("best time", "good time", "right time", "busiest time", "cheapest time",
              "worth it if", "worth it when", "worth buying", "worth the money")
IN_A_PLACE = re.compile(
    r"\b(?:in|near|around|round|outside)\s+(?:the\s+|this\s+|that\s+)?"
    r"(?:here|there|[a-z][a-z'\-]*)")
# "Near me" is the whole sign that a line is about the person's own ground, and it needs no place
# name: "the best chippy near me" names nowhere and is still a local pick.
NEAR_ME = re.compile(r"(?<![a-z])(?:near|around|round|by) (?:me|us|here)(?![a-z])")
PICK_POOL = (
    "Reviews beat anything I could say about {thing}, which I have never been to: a map app or "
    "the town's visitor site will name the ones people rate - tell me what you want from it and "
    "I'll help you choose.",
    "Reviews beat a guess from me about {thing}, since I have never been to any of them: a map "
    "app or the local visitor site names the ones people rate - say what matters and I'll help "
    "you narrow it down.",
)
# The same ask where no thing was named: "is it worth visiting in skegness", "what is worth
# visiting near me". PICK_POOL names the thing back to the person, so it cannot answer these -
# "Reviews beat a guess about the it near you" is what the slot filler produced. This pool names
# no thing and still gives the route.
PICK_ANYWHERE_POOL = (
    "Reviews from people who have been beat any guess of mine about a place, and a map app or "
    "the town's visitor site names the ones people rate: tell me what you want from the trip "
    "and I'll help you choose.",
    "Other people's reviews beat anything I could say about a place, and I have never been to it: "
    "a map app or the local visitor site sorts it by what you want from the trip - say what "
    "matters and I'll help you narrow it down.",
)

WORTH_VISITING = re.compile(
    r"(?<![a-z])(?:is|are|will)\b[^.!?]{0,40}\bworth (?:visiting|going to|a visit|seeing)"
    r"(?![a-z])")

# "Who is the ceo of tesco", "who wrote the theme tune to eastenders", "who plays in the
# beatles": a named thing in the world with one page that keeps it. The bot answers a great many
# of these itself; what is left over has a single honest route.
WHO_FACT = re.compile(
    r"(?<![a-z])(?:who|whos|who's)\s+(?:is|are|was|were|owns|runs|makes|made|plays|played|"
    r"wrote|writes|invented|founded|created|discovered|sang|sings|composed|directed|built|"
    r"designed|painted|won)(?![a-z])")
WHO_POOL = (
    "The record is the only place it is written down, and a name I got half right would stick, "
    "so I can't check one: "
    "Wikipedia has it with its sources and the official site will confirm it - tell me what "
    "you find and I'll help you make sense of it.",
    "The Wikipedia page for it answers that in a line and cites where the line comes from, "
    "and I can't look it up from here: paste what it says and I'll help you weigh the rest.",
)

# A figure about the world: a population, a height, an age, an area. The bot does not guess a
# number it never held, so this says so and names the page that has it with its source.
FIGURE_ASKS = re.compile(
    r"(?<![a-z])(?:population|how many people (?:live|are there)|how tall|how deep|"
    r"how high|how old (?:is|are)|how heavy|how big (?:is|are|was)|how large|how long is the|"
    r"how wide|how many miles away|how far away|how far is|square miles|"
    r"square metres does)(?![a-z])")
# How to set a figure rather than know one: "how deep should i plant the bulbs" wants advice.
SETTING_ASKS = re.compile(
    r"(?<![a-z])(?:should|shall|do i|can i|need to|would i|is it best|is best|ought)(?![a-z])")
# A method rather than a number: "how do you tell how far away a storm is" asks for the trick
# with the seconds between the flash and the thunder, and a page of figures is no answer to it.
METHOD_ASKS = re.compile(r"^\W*(?:how (?:do|would|can|might) (?:you|i|we|one)|ways? to|"
                         r"any (?:way|tips))(?![a-z])")
# A rule a company keeps rather than a figure about the world: how long a return window is
# belongs to the shop's own policy page, and a page about the thing has no such number.
POLICY_WORDS = ("return window", "refund policy", "returns policy", "warranty", "guarantee",
                "terms and conditions", "the policy", "their policy", "rules")
FIGURE_POOL = (
    "The date on a figure matters as much as the figure, and I can't check one I wasn't told: "
    "Wikipedia has that number with its source - tell me what it says and I'll help you make "
    "sense of it.",
    "A number I invented would be worse than none, and the year is half of it, so I would not "
    "guess: the Wikipedia page or the official site will have it, with the source; paste what "
    "it says and I'll help you weigh it up.",
)

# "How many paving slabs do I need", "how many tins of paint for a bedroom": the bot cannot see
# the patio, but the sum itself is the bot's and the two numbers are the person's. This is the one
# shape here where the honest reply is more than a hand-off.
MATERIALS = ("slab", "slabs", "tile", "tiles", "brick", "bricks", "paint", "wallpaper", "turf",
             "gravel", "sand", "cement", "mortar", "decking", "boards", "panel", "panels",
             "pots", "seeds", "bulbs", "compost", "bark", "chippings", "insulation",
             "plasterboard", "skirting", "beading", "underlay", "carpet", "lino", "edging",
             "fence posts", "screws", "hooks", "plants", "shrubs", "trees")
MATERIAL_ASK = re.compile(
    r"(?<![a-z])(?:how many|how much)\b[^.!?]{0,40}?"
    r"(?<![a-z])(?:do i need|will i need|should i (?:get|buy)|would i need|do we need|"
    r"to cover|for a|for an|for my|needed)(?![a-z])")
HOW_MANY_POOL = (
    "I can do that sum if you give me the numbers: the length and width of what you're covering, "
    "and how much one slab, pot, roll or bag covers. Tell me those and I'll work out how many to "
    "buy, with a little extra for cuts.",
    "Give me the measurements - the area's length and width, and the size of one of them - and "
    "I'll do the arithmetic, waste and cuts included. That's the part I'm good for; the size of "
    "your patio is the part I can't see.",
)

# "Where can I buy a yoyo", "where can I get a bike tyre today": a stock question about a thing
# with no shop named. Nothing here knows what is in a shop near the person.
BUY_ASK = re.compile(
    r"(?<![a-z])(?:where can i|where do i|where could i|where should i|where to|who sells|"
    r"where sells)\s+(?:buy|get|find|pick up|order)(?![a-z])")
# The thing being bought, with its article: the reply says the words back into a sentence ("a
# search for a fridge", not "for fridge").
BUY_THING = re.compile(
    r"\b(?:buy|get|find|pick up|order|sells|selling)\s+(?:me\s+)?"
    r"((?:a|an|some|any|the|one|my|our)?\s*[a-z][a-z'\-]*(?:\s+[a-z][a-z'\-]*){0,3})")
# Where and when, said after the thing: "a bike tyre today", "a yoyo near me", "milk online".
BUY_TAIL = frozenset("""
    today tonight tomorrow now online cheap cheaply near nearby locally please then round
    second hand secondhand from at in on shop shops store stores
""".split())
BUY_TAIL_PHRASES = (" today", " tonight", " tomorrow", " now", " online", " cheap", " cheaply",
                    " near me", " near you", " nearby", " locally", " round here", " in town",
                    " second hand", " secondhand", " please", " asap", " this week")
# Who the thing is for, where, and why, are not part of its name: "a yoyo for my nephew" is a
# yoyo, and the pool that named the whole run-on said "a yoyo for my" back to the person. The
# cut is at the first joining word, because the name of a thing in a shop is the words before it.
BUY_THING_STOPS = re.compile(r"\s(?:for|to|as|with|in|on|at|from|near|under|around|that|which|"
                             r"because|so|and|or|but)\s")
# A thing that is not sold in a shop: "where do i get a tetanus jab" wants a surgery and "where
# do i find an apprenticeship near me" wants a jobs board, and a stock check is neither.
BUY_NOT = ("advice", "help", "support", "information", "info", "a loan", "a mortgage", "a job",
           "apprenticeship", "work", "jab", "jabs", "vaccine", "vaccination", "prescription",
           "treatment", "test", "checked", "tested", "treated", "seen", "blocked list",
           "settings", "setting", "menu", "my money back")
# A thing in a shop is something a shop stocks: a rate, a price, a time or a deal is looked up
# on a page, and "where do i find the rates" got a stock check for it.
BUY_NOT_THINGS = frozenset("""
rate rates price prices deal deals offer offers quote quotes times time hours opening
availability stock information info news number address date dates list lists
loan loans fixed repaired serviced mended certificate certificates replacement
payslip payslips document documents form forms passport licence license visa
""".split())
# A person, or "the new one": the thing is named by somebody else's mouth and no shop stocks it.
# The word can sit anywhere in the thing ("someone to do it"), so this reads every word of it.
BUY_NOT_PEOPLE = ("one", "ones", "someone", "somebody", "anyone", "anybody", "person", "people")
# A job done to a thing rather than a thing on a shelf: "where can i get colour matched" and
# "where do i get my bike fixed" want somebody who does the work, and no shop stocks it.
BUY_NOT_THE_THING = ("matched", "made", "done", "fixed", "printed", "framed", "engraved",
                     "repaired", "serviced", "mended", "altered", "adjusted", "measured",
                     "fitted", "installed", "drilled", "cleaned", "mounted", "trimmed",
                     "sharpened", "copied", "printed off")
# A job done to the thing rather than a thing on a shelf. "Where can i get my bike fixed" and
# "where can i get my hair cut" name a thing and a piece of work, and the composer answered both
# with the hedge - "a search should sort you out quickly" - because the stock-check reader below
# stands down for anything done to the thing and nothing else read the shape. The route is a
# person who does the work: a map app or a directory, recent reviews, two prices. The search words
# are the person's own ("bike repair", "hair cut"), so nothing is invented and nothing guessed.
SERVICE_WORK = {
    "fixed": "repair", "fix": "repair", "mended": "repair", "mend": "repair",
    "repaired": "repair", "repair": "repair", "serviced": "service", "service": "service",
    "cleaned": "cleaning", "clean": "cleaning", "cut": "cut", "trimmed": "trimming",
    "trim": "trimming", "altered": "alterations", "alter": "alterations",
    "adjusted": "adjustment", "adjust": "adjustment", "framed": "framing", "frame": "framing",
    "engraved": "engraving", "engrave": "engraving", "sharpened": "sharpening",
    "sharpen": "sharpening", "printed": "printing", "print": "printing",
    "fitted": "fitting", "fit": "fitting", "installed": "installation", "install": "installation",
    "drilled": "drilling", "drill": "drilling", "mounted": "mounting", "mount": "mounting",
    "copied": "copying", "copy": "copying", "restored": "restoration", "restore": "restoration",
    "valeted": "valet", "valet": "valet", "resoled": "resoling", "resole": "resoling",
    "replaced": "replacement", "replace": "replacement", "resprayed": "respray",
    "respray": "respray", "washed": "washing", "wash": "washing",
}
# The work named as a noun rather than a verb: "where can i get a haircut" is the same ask as
# "where can i get my hair cut", and the stock check read the first as a thing a shop has.
# The work said as two words: taking a garment in is an alteration, and "cut" alone would read a
# hem as a haircut.
SERVICE_PHRASES = (
    ("taken in", "alterations"), ("take in", "alterations"), ("taking in", "alterations"),
    ("let out", "alterations"), ("taken up", "alterations"), ("taken in a bit", "alterations"),
)
SERVICE_NOUNS = (
    ("haircut", ("hair cut", "")), ("hair cut", ("hair cut", "")),
    ("dry cleaning", ("dry cleaning", "")), ("mot", ("mot", "car")),
)
# The name of the work as a shop or a directory lists it. Most are the thing and the verb the
# person said ("bike repair", "jeans alterations"); a few are said the other way round, and
# "who does key cut near you" is not a thing anyone searches for.
SERVICE_JOB_NAMES = {
    ("hair", "cut"): "haircuts",
    ("", "hair cut"): "haircuts",
    ("key", "cut"): "key cutting",
    # "where can i get my car mot done" is an MOT, not "car mot"; a car wash is not "car washing".
    ("car", "mot"): "an MOT",
    ("car", "washing"): "a car wash",
    # a cobbler is searched for as shoe repairs, not as "shoes resoling".
    ("shoes", "resoling"): "shoe repairs",
    ("shoe", "resoling"): "shoe repairs",
}
SERVICE_POOL = (
    "The last few reviews and two prices are what decide a {job}, not a list I could keep: "
    "search a map app or a directory near you, read the recent ones, and ring two for a price "
    "before you book.",
    "Prices for the same {job} swing wide, so the reviews and two quotes decide it: a map app "
    "or a directory near you, sorted by the recent ones, then two prices before you book.",
)
# The ask that puts the thing in for work, as opposed to buying one: "where can i get my bike
# fixed", "who can fix my bike near me", "where do i get a suit altered".
SERVICE_ASK = re.compile(
    r"(?<![a-z])(?:where can i|where do i|where could i|where should i|where to|who can|"
    r"who could|who should i|who does|who would|anywhere i can)\s+"
    r"(?:get|have|take|find|send|put)\b|(?<![a-z])(?:who can|who could|who does|who would)\b"
    # the same ask with the where dropped: "can i get them taken in" after "the jeans dont fit"
    r"|(?<![a-z])(?:can|could|should|would|will)\s+i\s+(?:get|have)\b")
# What is handed over is the thing, said without its possessive: nobody searches for "my bike".
SERVICE_THING = re.compile(
    r"\b(?:get|have|take|send|put|fix|repair|mend|service|clean|cut|alter|resole|reheel|"
    r"replace)\s+(?:me\s+)?((?:a|an|the|my|our|some)?\s*[a-z][a-z'\-]*"
    r"(?:\s+[a-z][a-z'\-]*){0,2})")
# A service done to "it" or "that" is a follow-up about the thread's own object, which the thread
# named; a body is not handed over at a counter, and a line about teeth or blood is a health ask
# another module answers ("where can i get my teeth cleaned" is a dentist, not a map app search).
SERVICE_NOT_A_THING = frozenset("""
it that this them one ones me him her us you yourself myself anything something nothing
""".split())
SERVICE_NOT_HEALTH = frozenset("""
teeth tooth dental blood bloods jab injection vaccine vaccination wound stitches cast mole skin
eye eyes ear ears smear scan xray procedure
""".split())
# Where the thing ends: at the work, at the hurry, or at the next clause. "My bike fixed cheaply"
# is a bike, and the work and the hurry are said after it.
SERVICE_STOPS = frozenset("""
cheap cheaply properly professionally done somewhere someone today tonight tomorrow please again
back off out about that which because so and or for taken take taking let
""".split())
BUY_POOL = (
    "Stock moves by the hour and a phone call is the only thing that checks it, so I can't "
    "see who has {thing} near you: a map app search shows what's nearest, and ring before you "
    "set off.",
    "Stock moves by the hour, so a list from me would be wrong by the time you got there: a "
    "map app or the chain's own site will say who has {thing} near you, and a ring first "
    "saves the trip.",
)


def _the_trade(line):
    """The trade named in the line, or "" when it names none."""
    for trade in TRADES:
        if re.search(r"(?<![a-z])" + re.escape(trade) + r"(?![a-z])", line):
            return trade
    return ""


def _the_thing(line):
    """The thing being bought, with its article, or "" when the line does not yield one."""
    found = BUY_THING.search(line)
    if not found:
        return ""
    text = " " + found.group(1).strip()
    for phrase in BUY_TAIL_PHRASES:
        if text.endswith(phrase):
            text = text[:-len(phrase)]
    cut = BUY_THING_STOPS.search(text)
    if cut:
        text = text[:cut.start()]
    words = [w for w in text.split() if w not in BUY_TAIL]
    while words and words[-1] in ("a", "an", "the", "some", "any", "my", "our", "of", "for"):
        words.pop()
    thing = " ".join(words[:4]).strip()
    if not thing or thing in ("a", "an", "the", "some", "any", "it", "one", "them", "me"):
        return ""
    return thing


def _trade_route(line, ctx):
    trade = _the_trade(line)
    if not trade or _has(line, NOT_A_TRADE) or _has(line, NOT_A_HIRE):
        return None
    if OWN_PROFESSIONAL.search(line):
        return None
    if not _has(line, HIRING):
        return None
    pool = TRADE_POOL if trade in QUOTING_TRADES else PROFESSIONAL_POOL
    return tuple(line.format(trade=trade) for line in pool)


def _buy_route(line, ctx):
    if not BUY_ASK.search(line) or _has(line, BUY_NOT):
        return None
    thing = _the_thing(line)
    if not thing or thing.split()[-1] in BUY_NOT_THINGS:
        return None
    # "where can i find my payslips": the person's own thing is on their own account, not in a
    # shop, and no map app shows it.
    if thing.split()[0].strip() in ("my", "our"):
        return None
    if _has(" " + thing + " ", BUY_NOT_THE_THING) or _has(" " + thing + " ", BUY_NOT_PEOPLE):
        return None
    return tuple(pool.format(thing=thing) for pool in BUY_POOL)


def _the_service(line, pointed=""):
    """(the work, the thing) for a line that puts a thing in for work, or None.

    `pointed` is what a pronoun in the line points at, which the understanding engine has already
    worked out: after "the jeans dont fit", "can i get them taken in" is the jeans, and a reader
    that only looked for a noun in the line itself would miss it.
    """
    if not SERVICE_ASK.search(line):
        return None
    work = ""
    for phrase, word in SERVICE_PHRASES:
        if re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", line):
            work = word
            break
    if not work:
        for verb, word in sorted(SERVICE_WORK.items(), key=lambda pair: -len(pair[0])):
            if re.search(r"(?<![a-z])" + re.escape(verb) + r"(?![a-z])", line):
                work = word
                break
    if not work:
        for noun, (word, thing) in SERVICE_NOUNS:
            if re.search(r"(?<![a-z])" + re.escape(noun) + r"(?![a-z])", line):
                return word, thing
        return None
    found = SERVICE_THING.search(line)
    if not found:
        return None
    words = []
    for word in found.group(1).split():
        if word in ("a", "an", "the", "my", "our", "some", "of", "for", "to", "in", "on"):
            continue
        if word in BUY_TAIL or word in SERVICE_WORK or word in SERVICE_STOPS:
            break
        words.append(word)
    if words and words[0] in SERVICE_NOT_A_THING:
        # "them", "it", "that": the thing is the one the thread named, if it named a thing at all.
        words = [word for word in str(pointed or "").lower().split() if re.search(r"[a-z]", word)]
        if not words or words[0] in SERVICE_NOT_A_THING:
            return None
    if not words:
        return None
    if any(word in SERVICE_NOT_HEALTH for word in words):
        return None
    return work, " ".join(words[:3])


def _service_route(line, ctx):
    found = _the_service(line, ctx.get("pointed") if isinstance(ctx, dict) else "")
    if not found:
        return None
    work, thing = found
    job = SERVICE_JOB_NAMES.get((thing, work)) or (thing + " " + work).strip()
    return tuple(pool.format(job=job) for pool in SERVICE_POOL)


def _about_a_place(line, ctx):
    """True when the line is about somewhere out in the world, not "in food" or "in a new job".

    A named place is the surest sign, and the understanding engine already says when a line
    carries one; a travel line without a name ("the best beach near me") is the other way in, and
    "near me" is the one phrase that makes a line local on its own.
    """
    if ctx.get("places"):
        return True
    if ctx.get("travel"):
        return True
    if WORTH_VISITING.search(line):
        return True
    return bool(NEAR_ME.search(line))


def _the_picked_thing(line):
    """The phrase the person picked out of the place: "beaches" from "the best beach in cornwall".

    PICK_POOL names it back to them ("Reviews beat anything I could say about beaches"), so the
    pool has a {thing} slot and every route that returns it has to fill that slot - a line said
    with "{thing}" still in it is worse than the shrug it replaced.
    """
    found = ""
    for phrase in PICKED_IN_A_PLACE:
        if len(phrase) <= len(found):
            continue
        if _names_one_of(line, (phrase,)):
            found = phrase
    if found == "thing to do" or found == "things to do":
        return "things to do"
    return found


def _pick_route(line, ctx):
    """Something to do, eat or stay in somewhere: the picks are the reviews' job, not the bot's."""
    if not _has(line, PICK_ASKS) and not WORTH_VISITING.search(line):
        return None
    if _has(line, NOT_A_PICK) or not _about_a_place(line, ctx):
        return None
    if WORTH_VISITING.search(line) and IN_A_PLACE.search(line):
        thing = _the_picked_thing(line)
        if not thing:
            # "Is it worth visiting in skegness" names no thing, so a line that says "about
            # {thing}" would have to say "about the it near you". Poetry is not the job.
            return PICK_ANYWHERE_POOL
        return tuple(pool.format(thing=thing) for pool in PICK_POOL)
    where = IN_A_PLACE.search(line)
    if not where:
        return None
    # The thing picked has to come before the place it is picked in: "the best beach in
    # cornwall" is a pick, and "losing my best friend to a new job in another city" only has the
    # place word "city" after the "in", which is the place itself and not a thing to pick.
    thing = _the_picked_thing(line[:where.start()])
    if not thing:
        return None
    return tuple(pool.format(thing=thing) for pool in PICK_POOL)


def _how_many_route(line, ctx):
    if not (MATERIAL_ASK.search(line) and _names_one_of(line, MATERIALS)):
        return None
    if not re.search(r"(?<![a-z])how (?:many|much)(?![a-z])", line):
        return None
    return HOW_MANY_POOL


def _place_route(line, ctx):
    if NOT_A_PLACE.search(line) or NOT_A_LOOKUP.search(line):
        return None
    if _has(line, CONTACT_ASKS):
        # A postcode or a phone number is a place lookup even when no place noun is named
        # ("whats the postcode for buckingham palace").
        return PLACE_POOL
    if not _has(line, WHERE_ASKS):
        return None
    if not _names_one_of(line, PLACE_NOUNS):
        return None
    return PLACE_POOL


def _route_route(line, ctx):
    """How to get somewhere, and how far it is: the journey is the map app's to measure."""
    if _has(line, NOT_A_JOURNEY):
        return None
    words = _words(line)
    travel = bool(words & set(TRAVEL_WORDS))
    if ROUTE_ASKS.search(line):
        if not (travel or ctx.get("places")):
            return None
        # "how long does it take to walk three miles" and "to cycle 10k" name a distance and
        # no ground: the pace is something the bot can say. A journey has somewhere to go.
        if TAKE_TO_ASKS.search(line) and not (ctx.get("places") or _names_one_of(line, GOES_TO)):
            return None
        return PLACE_ROUTE_POOL
    if _has(line, GET_TO_ASKS) and (travel or ctx.get("places")):
        # "The best way to get to manchester" names no road word; the place in it is the sign.
        return PLACE_ROUTE_POOL
    if re.search(r"(?<![a-z])from\b[^.!?]{1,40}\bto(?![a-z])", line) and travel \
            and re.search(r"how (?:do|can|should|would) (?:i|you|we)", line):
        return PLACE_ROUTE_POOL
    return None


# "Is there a pharmacy open near me on Sunday", "is the late chemist open tonight": a shop that is
# open now, near the person, on a day the usual one shuts. Nothing here knows the hours, and the
# hedge named no place at all. A chemist is the one kind of shop with a finder made for exactly
# this - the NHS one lists what is open nearby and until when - and 111 says the same on the
# phone, which is what STYLE.md means by naming the place a person can look.
# The hours, not just the whereabouts: "where is the nearest pharmacy" is a place ask and the
# place route answers it, while "which pharmacy is open late" is the one only the finder knows.
OPEN_CHEMIST_HOURS = re.compile(
    r"(?<![a-z])(?:open|opens|opening|closed|closing|closes|shut|shuts|late|late-night|latenight|"
    r"tonight|now|today|sunday|weekend|bank holiday|out of hours|24 ?hour|all night)(?![a-z])")
CHEMISTS = ("pharmacy", "pharmacies", "chemist", "chemists", "dispensary")
OPEN_CHEMIST_POOL = (
    "Most towns have one open late: a big chain chemist usually runs to 10 or 11, a supermarket "
    "one shuts by 8 and earlier on a Sunday, and a bank holiday moves it again. Which of the ones "
    "near you is open tonight I can't see - the NHS pharmacy finder lists them with the closing "
    "time and the distance, and 111 says the same on the phone.",
    "There is nearly always a late chemist somewhere in a town - the chains stay open to about 10, "
    "and the ones inside supermarkets shut by 8, earlier on a Sunday - but the hours near you are "
    "not something I can look up. The NHS pharmacy finder shows what is open now and until when; "
    "111 will find you one if the phone is easier, and an out-of-hours prescription can go there.",
)


def _open_chemist_route(line, ctx):
    """A chemist that has to be open now, or near, or on a day the usual one shuts."""
    if not _has(line, CHEMISTS) or not OPEN_CHEMIST_HOURS.search(line):
        return None
    # "what can i get from the chemist for a cough" is a counter question, and the counter answer
    # is the better one; only the hours and the whereabouts are this route's.
    if re.search(r"(?<![a-z])(?:what|anything|something|buy|get|recommend)(?![a-z])", line) \
            and not re.search(r"(?<![a-z])(?:open|closes|close|shut|late|tonight)(?![a-z])", line):
        return None
    return OPEN_CHEMIST_POOL


def _who_route(line, ctx):
    if not WHO_FACT.search(line) or _has(line, ABOUT_THE_BOT):
        return None
    words = _words(line)
    if words & OWN_PERSON:
        return None
    # "who is it", "who was that", "who is she": the subject is whoever was just named, and a
    # page online does not know who that was.
    if re.search(r"(?<![a-z])(?:who|whos|who's)\s+(?:is|was|were|are)\s+"
                 r"(?:it|that|this|he|she|they|them|you|thou)\b", line):
        return None
    return WHO_POOL


def _tide_route(line, ctx):
    """When the sea turns, which is a table for one beach and one day.

    High and low water move by up to an hour a day and by minutes between two beaches a few miles
    apart, so nothing here can hold the clock time, and a guess would send somebody onto a
    causeway or off a slipway at the wrong moment. The route names the table that has it.
    """
    if not TIDE_ASK.search(line):
        return None
    if TIDE_WHY.search(line):
        # How tides work is a fact the bot does hold, and the explanation is the better answer.
        return None
    return TIDE_POOL


def _figure_route(line, ctx):
    if not FIGURE_ASKS.search(line) or SETTING_ASKS.search(line):
        return None
    if METHOD_ASKS.search(line) or _has(" " + line + " ", POLICY_WORDS):
        return None
    if _words(line) & OWN_PERSON:
        return None
    if re.search(r"(?<![a-z])how (?:old|tall|big|heavy|deep|far) (?:is|are) "
                 r"(?:he|she|they|it|you|we)(?![a-z])", line):
        return None
    return FIGURE_POOL


# A record: the biggest, the oldest, the longest. It is a settled fact and it is one the bot does
# not hold, so the honest reply is a hand-off to the page that keeps the list - not the news note,
# which is what "in the world" earned it ("I can't see the news from here, sorry"), and not the
# plain hedge, which names nothing to look at. The understanding engine says which of the two
# kinds a question is (`over_time`), so this reader fires only on the settled one, and a live
# question that happens to use a superlative ("the cheapest price today") keeps its own reader.
RECORD_ASKS = re.compile(
    r"(?<![a-z])(?:biggest|largest|tallest|longest|oldest|youngest|smallest|deepest|shallowest|"
    r"highest|lowest|heaviest|lightest|fastest|slowest|widest|narrowest|thinnest|strongest|"
    r"richest|poorest|wealthiest|busiest|coldest|hottest|wettest|driest|sunniest)(?![a-z])|"
    r"\bmost\s+(?:populous|expensive|common|popular|visited|deadly|abundant|spoken)(?![a-z])")
# The record has to be asked for, not used as a figure of speech: "the biggest mistake i made at
# work" is a line about them, and "the best way to clean a grill" is advice with no record in it.
RECORD_ASKED = re.compile(
    r"(?<![a-z])(?:what|whats|what's|which|whichs|which's|who|whos|who's|where|wheres|where's|"
    r"name|tell me)(?![a-z])")
RECORD_POOL = (
    "I can't check a record from here, sorry - the list moves when somebody breaks it. Wikipedia "
    "keeps it with the date each one was set; paste what it says and I'll help you weigh it up.",
    "No record book here, sorry, and a half-remembered number would be wrong without saying so. "
    "The Wikipedia page for it keeps the list and dates it - tell me what it says and we can go "
    "from there.",
)


def _record_route(line, ctx):
    """A record the bot does not hold: the page that keeps the list, not today's news."""
    if not ctx.get("settled"):
        return None
    if not RECORD_ASKS.search(line) or not RECORD_ASKED.search(line):
        return None
    if _words(line) & OWN_PERSON or SETTING_ASKS.search(line) or METHOD_ASKS.search(line):
        return None
    if re.search(r"(?<![a-z])(?:the best|my best|your best|best way|worst way|best time)(?![a-z])",
                 line):
        return None
    # "whats the biggest size nappy" and "the biggest pack of loo roll" ask what a shop stocks,
    # not who holds a record: a superlative in front of a thing being bought is the shelf.
    if _has(" " + line + " ", ("size", "sizes", "pack", "packs", "box", "boxes", "bottle",
                              "bottles", "tin", "tins", "bag", "bags")):
        return None
    # A number is not a record that is measured: there is no page holding the biggest one, and no
    # list that moves - the biggest number is arithmetic and the longest word is a dictionary.
    # "what is the biggest number" and "the longest word in english" were sent to the record book
    # and told that somebody breaks the record, which is worse than the plain hedge they had.
    if _has(" " + line + " ", ("number", "numbers", "word", "words", "letter", "letters",
                              "digit", "digits", "prime", "sum", "total")):
        return None
    return RECORD_POOL


# What the understanding engine makes of a line that the readers use: the places it names, and
# whether it is a travel line at all. Read once per ask, because every reader may want it.
TRAVEL_TOPICS = ("geography-and-travel", "travel", "holidays", "days-out", "outdoors")


def _the_reading(understood):
    """The parts of the reading the readers use, from what the understanding engine says."""
    if not understood:
        return {"places": set(), "travel": False, "pointed": "", "settled": False}
    places = set()
    for entity in understood.get("entities") or ():
        if isinstance(entity, dict) and entity.get("type") == "place" and entity.get("text"):
            places.add(entity["text"])
    # What a pronoun in the line points at: "can i get them taken in" after "the jeans dont fit".
    pointed = ""
    ref = understood.get("ref")
    if isinstance(ref, dict):
        for key in ("it", "that", "they", "them"):
            value = ref.get(key)
            if isinstance(value, str) and value.strip():
                pointed = value.strip()
                break
    topics = set(understood.get("topics") or ())
    if understood.get("topic"):
        topics.add(understood["topic"])
    travel = bool(topics & set(TRAVEL_TOPICS))
    # Whether what the line asks about is a settled fact rather than live data: a record, a count,
    # a date in the past. Read from the understanding engine, which owns the reading of the two
    # kinds, so this file does not keep a second list of the words.
    settled = understood.get("over_time") is False
    return {"places": places, "travel": travel, "pointed": pointed, "settled": settled}


# When the sea comes in and goes out: a live number for one beach and one day, which is the kind
# of thing nothing here holds. It is also the shape that got the wrong subject - "is the tide in
# or out" was read as a pick between two people - so the reader only fires on a line that asks for
# the time, the height or the state, never on one that asks how tides work.
TIDE_ASK = re.compile(
    r"(?<![a-z])(?:what|which|whats|what's)\s+time\s+(?:is|are|does|do|will|would)"
    r"[^.!?]{0,24}?(?<![a-z])(?:high|low|the)\s*tides?(?![a-z])"
    r"|(?<![a-z])when(?:'s|s|'re|re| is| are| does| do| will| can| should)?\s+(?:the\s+)?"
    r"(?:high|low)\s+tide(?![a-z])"
    r"|(?<![a-z])when\s+(?:is|does|will)\s+the\s+tide(?![a-z])"
    r"|(?<![a-z])is\s+the\s+tide\s+(?:in|out|coming|going|high|low|up|down)(?![a-z])"
    r"|(?<![a-z])tide\s+(?:is\s+)?(?:in|out)\s+or\s+(?:in|out)(?![a-z])"
    r"|(?<![a-z])tide\s+(?:times|table|timetable)(?![a-z])"
    r"|(?<![a-z])what(?:'s|s|\s+is)\s+the\s+tide\s+(?:doing|like)(?![a-z])"
    r"|(?<![a-z])how\s+(?:high|low|far\s+out)\s+(?:is|will|does)\s+the\s+tide(?![a-z])"
    r"|(?<![a-z])when\s+(?:can|should)\s+(?:i|we)\s+(?:swim|walk|launch|get)\s+(?:out|across|on\s+the\s+"
    r"water|to\s+the\s+boat)(?![a-z])")
# How tides work: the explanation is the answer, and it is one the bot holds.
TIDE_WHY = re.compile(
    r"(?<![a-z])(?:why|how\s+(?:do|does|come)|what\s+causes?|explain|explained|what\s+are)\b"
    r"[^.!?]{0,20}(?<![a-z])tides?(?![a-z])"
    r"|(?<![a-z])tides?\b[^.!?]{0,24}(?:work|works|happen|caused|spring|neap|moon)(?![a-z])")
TIDE_POOL = (
    "High and low water move by up to an hour a day, and by minutes between two beaches a few "
    "miles apart, so a tide time is the one thing I would not guess: a tide-table site for "
    "that beach, or the harbour or pier's own page, has today and tomorrow, and the local "
    "paper prints them too.",
    "Two beaches a few miles apart turn minutes apart and the same one is an hour later "
    "tomorrow, so I can't hold today's times: the harbour's page or a tide table for that "
    "beach has them, with the height as well as the clock time - the height is the bit that "
    "matters if you are walking a causeway or launching a boat.",
)


# ---------------------------------------------------------------- a form that ate the work

# The one route where what the bot knows is not a place that holds the answer but the order to do
# things in. Nobody's system is visible from here, and "I'm listening" is no help to somebody
# staring at an empty application they spent twenty minutes on.
FILLING_IT_IN = re.compile(
    r"(?<![a-z])(?:form|forms|application|answers|questionnaire|survey|booking|checkout|basket|"
    r"page|webpage|website|site|screen|portal|online|typed|filled\s+it\s+in|"
    r"filled\s+the\s+form\s+in)(?![a-z])")
# A save button is only on a screen, so this arm of the loss cue puts the form on one by itself.
SAVING_FAILED = re.compile(
    r"(?<![a-z])(?:didnt|didn't|did\s+not|doesnt|doesn't|does\s+not|wouldnt|wouldn't|would\s+not|"
    r"wont|won't|will\s+not|refused\s+to)\s+(?:save|keep|remember)(?![a-z])")
LOST_THE_WORK = re.compile(
    r"(?<![a-z])(?:didnt|didn't|did\s+not|doesnt|doesn't|does\s+not|wouldnt|wouldn't|would\s+not|"
    r"wont|won't|will\s+not|refused\s+to)\s+(?:save|keep|remember)(?![a-z])"
    r"|(?<![a-z])(?:went|took\s+me|jumped)\s+back\s+to\s+the\s+start(?![a-z])"
    r"|(?<![a-z])(?:start|do)\b[^.!?]{0,22}?(?<![a-z])(?:again|from\s+scratch)(?![a-z])"
    r"|(?<![a-z])(?:all\s+over\s+again)(?![a-z])"
    r"|(?<![a-z])(?:lost|wiped|cleared|erased|emptied)\s+(?:my\s+|the\s+|all\s+|the\s+whole\s+)?"
    r"(?:answers|work|everything|it\s+all|the\s+lot|basket|cart|form|application)(?![a-z])"
    r"|(?<![a-z])(?:disappeared|vanished|never\s+went\s+through)(?![a-z])"
    r"|(?<![a-z])(?:timed\s+out|crashed)(?![a-z])"
    r"|(?<![a-z])(?:signed\s+me\s+out|logged\s+me\s+out|kicked\s+me\s+out|threw\s+me\s+out)(?![a-z])"
    r"|(?<![a-z])(?:cant|can't|couldnt|couldn't|wont|won't)\s+(?:let\s+me\s+|allow\s+me\s+)?"
    r"(?:submit|send\s+it)(?![a-z])")
# A form on paper is a different problem, and a lost parcel with a claim is not this one at all.
# "form" and "application" are also a thing on paper: "i lost the application form" is a sheet
# off a desk, and the order below (a back button, a saved draft) is advice about a screen. So the
# bare filling-in words need a word that puts the form on a screen with them. "booking" is the same
# shape and is the booking reader's (a lost paper form is nobody's here).
ON_A_SCREEN = re.compile(
    r"(?<![a-z])(?:online|website|web\s?site|site|webpage|web\s?page|page|screen|portal|checkout|"
    r"basket|cart|typed|typing|type|submitted|submit|link|app|browser|internet|form\s+online|"
    r"filling\s+in|click\w*|tap\w*|refresh\w*|reload\w*|scroll\w*|timed\s+out|session|"
    r"the\s+back\s+button|save\s+button)(?![a-z])")
# The work itself named as a quantity - "the whole application", "every answer" - is not a sheet
# of paper, whatever the noun is.
THE_WORK_ITSELF = re.compile(
    r"(?<![a-z])(?:whole|entire|all\s+of\s+(?:it|my|the)|every\s+(?:answer|page|line|word)|"
    r"all\s+(?:of\s+)?(?:my|the)\s+(?:answers|work))(?![a-z])")
# The loss is described as the form going back or starting over, which is a screen and nothing else.
BACK_TO_START = re.compile(
    r"(?<![a-z])(?:went|took\s+me|jumped|sent\s+me)\s+back\s+to\s+the\s+start(?![a-z])"
    r"|(?<![a-z])(?:start|do)\b[^.!?]{0,22}?(?<![a-z])(?:again|from\s+scratch)(?![a-z])"
    r"|(?<![a-z])(?:all\s+over\s+again)(?![a-z])")
THE_BARE_FORMS = re.compile(
    r"(?<![a-z])(?:form|forms|application|applications|answers|questionnaire|survey)(?![a-z])")
NOT_A_WRECKED_FORM = ("in the post", "by post", "posted", "paper", "printed", "print it",
                      "in the letter", "through the door", "on paper", "claim", "compensation",
                      "lost my bag", "lost bag")
WRECKED_POOL = (
    "I can't see their system, but this order gets a lost form back more often than not: the back "
    "button before a reload, then a saved draft or a 'continue where you left off' link, then the "
    "service itself - ask them to check the half-finished application before you type it all "
    "again, because a duplicate is harder to undo than a gap.",
    "Their system isn't visible from here, so the order is what matters: back one page rather than "
    "reloading, then the drafts or 'continue your application' link, then the service itself, "
    "quoting any reference you were given. When you do type it again, keep the long answers in a "
    "document and paste them in, so a second timeout costs you nothing.",
)


def the_wrecked_form_reply(line):
    """The pool for a form or a page that threw the person's work away, or None.

    Public because a line like this is a *statement* - "my online application didnt save" has no
    question in it - so it never reaches `for_the_ask`: the chain has already offered the lost-ask
    and sympathy pools by then. The composer asks this one question first, and it answers for
    every wording of a form that ate the work, not just this one.
    """
    if not line or _has(line, NOT_A_WRECKED_FORM):
        return None
    if not FILLING_IT_IN.search(line) or not LOST_THE_WORK.search(line):
        return None
    # A paper form that went missing keeps the reply it had: when the only word about filling
    # something in is a form or an application, and nothing in the line puts it on a screen, the
    # order below (a back button, a saved draft) is about a screen the person is not looking at.
    if THE_BARE_FORMS.search(line) and not (ON_A_SCREEN.search(line)
                                           or SAVING_FAILED.search(line)
                                           or BACK_TO_START.search(line)
                                           or THE_WORK_ITSELF.search(line)):
        return None
    return WRECKED_POOL


# No entry in `READERS`: a line that asks about a form ("will it keep my answers?") is a question
# and the pools above read it, while a line that *reports* a form eating the work is a statement
# and never reaches `for_the_ask` at all. The statement is answered from `fallback_chain.py`, and
# the question shape reaches this pool through `HEDGE_POOL`, which is where a question with no
# reader of its own ends up.
READERS = (_trade_route, _service_route, _buy_route, _pick_route, _how_many_route, _place_route,
           _route_route, _who_route, _tide_route, _figure_route, _record_route,
           _open_chemist_route)


def for_the_ask(clean, repaired="", understood=None):
    """The pool of honest routes for this ask, or None when none of them beats the hedge.

    `clean` is the line as typed and `repaired` the same line with its chat-speak put right, the
    convention every reader in the composer follows: the typed line is read first, and the
    repaired one only catches what a slip hid.
    """
    if not clean:
        return None
    ctx = _the_reading(understood)
    for line in (clean, repaired or ""):
        if not line or not line.strip():
            continue
        for reader in READERS:
            found = reader(line, ctx)
            if found:
                return found
    return None
