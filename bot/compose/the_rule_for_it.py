"""What the bot knows about the kind of question, said before it says where the rest is.

STYLE.md's honest band has one rule this file exists for: a pointer on its own is not a reply.
"I can't look up live prices, sorry. The seller's site has today's figure" names no thing, says
nothing about the thing, and leaves the person exactly where they were - and the same shape was
in the plain shrug, the place pools and the live notes, so it was the commonest failing reply in
the band (843 shrugs on the deck at base `49408e53`, from three lines).

The general rule, not a list of wordings: **everyday asks come in kinds, and each kind has one
thing that always settles it.** A price turns on where you buy it and the size, never on the
first number you see. An amount turns on a portion per head and how many are eating, or on how
far one pack covers and how big the job is. Whether a thing is still good turns on how long it
has been and how it was kept. None of that is a fact about the world that could go out of date:
it is the shape of the answer, which is the part the bot can always give, and it is what makes
the pointer that follows worth reading.

So a reply here is three beats, in this order: what settles it (the rule, and their own subject
in it where the line has one), where the current figure or date is kept, and the part the bot can
still do - the sums, the weighing. It ends there, and it asks nothing back: the person has just
said what they want.

What it will not touch, because a rule of thumb about soup is wrong about a dose:

* a line naming a medicine, a dose or a body part - `safety.py` and the health cards own those;
* a line about a person rather than a thing: "how heavy should a 6 month old be" is a baby on a
  scale, not a joint on a plate, and a portion the count multiplies is the wrong arithmetic;
* a line about money on an account ("up front", a deposit, a bill) - the figure there is real and
  in one place, and the place pools say where;
* a keeping question with nothing in it that keeps: "where can i eat with my dog" and "my son has
  a nut allergy, what can i cook" both contain the words of a keeping ask and neither is one.

Every pool here is read last, after every reading that could answer the line, so it can only ever
stand in for a shrug.
"""
import re

# ---- a price ----------------------------------------------------------------------------------
#
# A figure nobody can see, of a thing being bought. The rule that settles it is the same whether
# the thing is a tattoo, a pint or a boiler: which one it is, where you buy it, and the day. A job
# is the exception and the line says so - a job is priced per quote, and two quotes on the same
# spec are worth more than any one figure. The hand-back is the sums, which is the thing a person
# ringing round three sellers actually wants.
PRICE_RULE = (
    "What a figure like that turns on is which one it is, where you buy it and the day, so two "
    "or three sellers compared all-in will beat any one number you see. The current figures are "
    "on their own pages, and bring them back and I will work out what they come to a month.",
    "A job is priced by the quote, not by a list: the same job gets two or three quotes on the "
    "same spec, in writing, and that is the number worth comparing. A thing on a shelf is the "
    "seller's own page, all in with delivery - tell me what you find and I will do the sums.",
    "Prices move by exactly what you are buying and by where, so one number from one seller is "
    "not an answer to it. Two sellers, what it comes to all in, and then the part I am good at: "
    "what it leaves you a month.",
)
# "how much is a X", "what does X cost", "how much should I be paying for X", "is that a fair
# price", "can I get it cheaper". A money word is required: "how much protein in chicken" is a
# quantity, and "how much is a portion" is not a price at all.
PRICE_ASK = re.compile(
    r"\bhow much (?:is|are|was|were|does|do|did|would|will|should|might)\b[^?.!,]{0,40}?"
    r"\b(?:cost|costs|charge|charge for|worth|set me back|come to|pay|paying|spend)\b"
    r"|\bhow much (?:should|shall|ought to|do|would)\b[^?.!,]{0,24}?\b(?:pay|spend|be paying)\b"
    r"|\bwhat (?:does|do|did|would|will|should)\b[^?.!,]{0,36}?\bcost\b"
    r"|\bwhat(?:'s|s)? the (?:cost|price|going rate|damage|ballpark)\b"
    r"|\bwhat about the cost\b|\bthe cost of\b|\bprice of (?:a|an|the)\b"
    r"|\bhow much (?:is|are) (?:a|an|the)\b"
    r"|\bis (?:that|it|this) (?:a )?(?:fair|good|normal|about right) (?:price|money)\b"
    r"|\bis (?:that|it|this) (?:too )?(?:expensive|dear|cheap)\b"
    r"|\bcan i get (?:it|that|one) (?:any )?cheaper\b"
    r"|\bwhat would that cost\b|\bhow much would that (?:be|cost)\b"
    r"|\bhow much (?:would|will|might|could) (?:a|an|the|one)\b[^?.!]{0,30}?\bbe\b"
    # The bare shape, with no verb in it at all: "how much are flights to rome", "how much is a
    # pint in dublin". A quantity word after it is the other kind of question, and "how much is
    # there" is not a figure anyone sells.
    r"|\bhow much (?:is|are|was|were)\b(?!\s*(?:enough|too\b|left|more|of\b|in\b|there\b|"
    r"it\b|that\b|this\b|going\b))",
    re.I)
# A verdict asked of a thing, with no figure and no verb of costing in it: "is the train to
# cornwall expensive", "are taxis dear here", "are flights to spain pricey in august", "is it
# expensive to park in town". The figure is the same one nobody can see and the ask is the same
# ask - it turns on which one, where, and the day - but the grammar is only a thing and an
# adjective, so these reached the shrug while "how much is a train to york" got the fares answer.
#
# Only money adjectives count, and `dear` is read as a degree or a comparison, or after a thing
# ("are taxis dear here"), never as the word people put on the end of a greeting: "how are you
# dear" and "thanks dear" name no thing and are not this.
#
# The subject fence on the first arm keeps `you` out, the same way the last arm already did: "are
# you expensive to hire" is somebody joking about the bot, not a thing whose price is being asked,
# and it was given the two-sellers answer about buying something (gentle-wagon, trim-candle on
# #13445). A possessive is still a thing - "is your car insurance expensive" is the car's.
PRICE_VERDICT = re.compile(
    r"\b(?:is|are|was|were|will|would|does|do)\b(?!\s*(?:you|u)\b)[^?.!,]{0,40}?"
    r"\b(?:expensive|pricey|costly|spenny|overpriced)\b"
    r"|\b(?:is|are|was|were)\b[^?.!,]{0,40}?\b(?:too|so|very|quite|really|that|a bit|dead|"
    r"bloody)\s+dear\b"
    r"|\bdear(?:er)?\s+than\b"
    r"|\b(?:is|are)\s+(?!you\b|she\b|he\b|they\b|we\b|i\b)(?:[a-z']+\s+){1,3}(?:too\s+)?"
    r"dear\b", re.I)
# `dear` as a name, not a degree: "is my dear mum coming", "is the dear little thing coming",
# "is my dear friend around". The possessive or article directly before it makes it the word for
# somebody they love, and the price rule ("a job is priced by the quote") has nothing to do with
# it. `is that dear` and `are taxis dear here` name no person and keep the verdict.
A_DEAR_AS_A_NAME = re.compile(
    r"\b(?:my|your|our|his|her|their|the|a|an)\s+dear\b", re.I)
# A thing you buy to get somewhere, or to eat and sleep once you are there. Its price is set by
# the day rather than by the seller, which is what makes it worth its own pool: "are flights to
# spain pricey in august" and "are taxis dear here" are not answered by two sellers compared on
# the same spec, because the same seat on a Tuesday is not the same price as on a Monday.
#
# A room is not a fare, though it is bought the same way: "are hotels in york dear" and "is a
# hotel dear in august" have no seat and no off-peak Tuesday, and the fare pool told them about
# one. A room and a shelf both turn on which one and when, which is what `PRICE_RULE` says.
A_FARE_OR_A_TICKET = re.compile(
    r"\b(?:trains?|flights?|buses|coach|ferry|tubes?|parking|park|"
    r"tickets?|entry|admission|petrol|fuel|diesel|delivery|shipping|car hire|hire car)\b", re.I)
# The fare, as against the thing on the shelf. The number is on the operator's page and it moves
# with the day, so the useful half is which day and how far ahead, and the sums afterwards.
FARE_PRICE_RULE = (
    "The day is what sets that one, not the seller: the same trip off-peak on a Tuesday can be a "
    "fraction of the peak on a Monday, and booking further ahead is nearly always cheaper than "
    "booking late. The operator's own page has today's figure - bring it back and I will work out "
    "what it comes to for you.",
    "Booked far enough ahead, a fare is a different number from the one a week before, so compare "
    "the same journey on the day you actually go rather than the first figure you see. Tell me "
    "the route and the dates and I will do the sums against the money you have.",
    "That price turns on the day, the time and how far ahead you book, and on a fare it is the "
    "time of day that moves it most. The figure is on the operator's own page; bring it back "
    "with what you can spend and I will tell you whether it stacks up.",
)
# A cab is a fare that is not a fare. The meter is the price, so it moves with the clock and the
# traffic rather than with how far ahead you booked, and a firm will usually fix a quote if you ask
# - which is the opposite advice to "book further ahead" and "the same trip off-peak on a Tuesday".
# The rail pool said that to `are taxis dear here`, a confident wrong answer about a thing the bot
# had just named, which is worse than the hedge it replaced (trim-candle on #13445).
A_CAB_OR_A_LIFT = re.compile(
    r"\b(?:taxis?|cabs?|minicabs?|private hire|black cab|ubers?|lyft|a cab|a taxi)\b", re.I)
CAB_FARE_RULE = (
    "A cab is metered, so it is the clock and the traffic that set the price, not the seller: the "
    "same trip at 8 in the morning and at 11 at night are different numbers. Ring the firm with "
    "the pickup, the drop-off and the time and ask for a fixed quote - most will give one, and "
    "that quote is the number worth comparing.",
    "A taxi fare is the meter, so the time of day and the traffic move it; there is nothing to "
    "book further ahead. Ask two firms for a fixed price for your trip and compare those, and ask "
    "whether the quote covers waiting and the return.",
)
# A verdict asked of a thing names no job and often nothing on a shelf: "are hotels in york dear",
# "is a tattoo expensive", "is a McDonald's expensive". `PRICE_RULE` carries the job line ("a job
# is priced by the quote ... a thing on a shelf is the seller's own page"), and the pool is picked
# by hash rather than by the line, so a verdict could be answered with the one frame that is false
# of it - a room is neither a job nor on a shelf (umber-desk and azure-cable on #13445). This pool
# holds only what is true of any priced thing, and the verdict arm uses it; the ask arm keeps
# `PRICE_RULE`, where the line usually does name a job.
PRICE_VERDICT_RULE = (
    "Whether that is dear depends on which one and where from: the same thing is a different "
    "number in two places and on two days. Two prices, all in, is the comparison - bring them "
    "back and I will tell you which one leaves you better off at the end of the month.",
    "There is no one price for it. What it comes to turns on the size, the seller and the day, so "
    "the useful thing is two quotes for the same thing with everything included. Tell me the two "
    "figures and I will work out what each leaves you.",
    "That is impossible to call from one number: what it costs moves with which one you pick, "
    "where you get it and when. Find two prices for the same thing, all in, and the difference "
    "between them is the part worth acting on.",
)
# An occasion is priced by the head and by the day, not by two sellers on the same spec and not by
# a quote for a job. "is a wedding expensive", "is a funeral expensive" and "is eating out
# expensive these days" all landed on `PRICE_RULE`'s job line - "a job is priced by the quote, not
# by a list ... a thing on a shelf is the seller's own page" - which is neither of the two things
# those asks are about (azure-cable on #13445). What is true of every one of them is the count, the
# date and what the price includes; the figures are on the venue's or the caterer's own page.
A_AN_OCCASION = re.compile(
    r"\b(?:weddings?|funerals?|christenings?|baptisms?|namings?|birthdays?|birthday party|"
    r"part(?:y|ies)|anniversar(?:y|ies)|honeymoons?|stag do|stag night|hen do|hen night|"
    r"graduations?|receptions?|eating out|eating away|meals out|meal out|dinner out|"
    r"restaurants?|takeaways?|catering|caterers?)\b", re.I)
OCCASION_PRICE_RULE = (
    "That one is priced by the head and by the day rather than by the seller: how many people, "
    "which day, and what is inside the price - the meal, the drinks, the extras. Two quotes on "
    "the same numbers is the only comparison worth making; tell me yours and I will do the sums.",
    "What it comes to turns on the count and the date, so fix the guest list and the day first, "
    "then ask two or three places for the same thing all in. Bring the figures back and I will "
    "work out what it leaves you a month.",
    "Every one of these is quoted per person and moves with the day of the week, so one figure "
    "from one place says little on its own. The same count and the same extras asked of two "
    "places is the comparison - and the venue's own page has today's numbers.",
)

# The lines a price ask is really about something else: their own account, a payment, a rate.
NOT_ABOUT_A_PRICE = re.compile(
    r"\bmy (?:account|balance|bill|invoice|statement|payment|direct debit|order|parcel|quote|"
    r"refund|payslip|wage|salary|pension|mortgage|rent|card|loan|overdraft|credit)\b"
    r"|\b(?:up front|deposit|instal?ments?|per month|a month|a week|per hour|pay off|paid off|overdue)\b",
    re.I)

# ---- an amount --------------------------------------------------------------------------------
#
# How much of something to buy, cook or use - two shapes, because the two are settled by different
# halves and one pool cannot say both. Feeding people turns on a portion per head and how many are
# eating. A material turns on how far one pack or one scoop goes, and the size of the job. Saying
# which half is the useful part; the figure itself is on the pack, the label or the recipe they
# already have in their hand, which is also the only place that knows the size of their tin.
AMOUNT_FEEDING_RULE = (
    "That one is arithmetic rather than knowledge: a portion each, times how many you are "
    "feeding, and a little more if it is the only dish. The pack, the butcher or the recipe you "
    "are using carries the per-head figure - give me the count and I will turn it into a total.",
    "Work it from the number of people, not from the whole: what one person gets, multiplied, "
    "and a bit on top if it is the only thing being served. Tell me how many and I will do the "
    "sum with you.",
    "How much you need is per head, and whether it is the main thing or one of several decides "
    "which per-head figure: the pack or the recipe has that half. Bring me the numbers and I "
    "will work out what to buy.",
)
AMOUNT_COVER_RULE = (
    "That one is a coverage sum rather than a fact: how far one pack, tin or scoop goes, times "
    "the size of the job. How far it goes is on the label, and the size of the job is yours to "
    "measure - tell me it and I will work out how many you need.",
    "How much you need comes from how much one of them covers and how big the job is, so start "
    "with the coverage figure on the label and then it is arithmetic. Give me the measurements "
    "and I will do the working.",
    "The label says what one pack covers and the rest is a multiplication: that, times the area "
    "or the number of loads you are doing. Tell me the two numbers and I will turn them into how "
    "much to buy.",
)
# The whole of an amount ask. Which pool answers it is decided below, by whether people are being
# fed: "how much mince for a lasagne for four" is portions, "one wash" is coverage. "how long
# should the lamb go in" is a duration and is not here at all.
AMOUNT_ASK = re.compile(
    r"\bhow (?:much|many)\b[^?.!]{0,40}?\b(?:do|should|would|will|might|can|shall)\b[^?.!]{0,12}?"
    r"\b(?:i|we|you) (?:need|use|buy|get|make|cook|add|put|give|take|order|hire)\b"
    r"|\bhow (?:much|many) (?:do|does) (?:i|we|you) need\b"
    r"|\bhow (?:much|many)\b[^?.!]{0,30}?\bfor (?:two|three|four|five|six|seven|eight|nine|ten|"
    r"twelve|twenty|\d+)\b"
    r"|\bhow (?:heavy|big|large|thick) should\b"
    r"|\bhow many (?:portions|servings|heads)\b"
    r"|\bhow much per (?:person|head|portion)\b|\bper (?:head|person)\b"
    r"|\bhow much\b[^?.!]{0,28}?\b(?:goes|goes in|goes into)\b",
    re.I)
# The line is feeding somebody, or counting food: the pool that counts portions answers it.
FEEDING = re.compile(
    r"\b(?:people|person|persons|head|heads|portion|portions|serving|servings|guests?|kids?|"
    r"children|adults?|family|each|everyone|for (?:two|three|four|five|six|seven|eight|nine|ten|"
    r"twelve|twenty|\d+))\b"
    r"|\b(?:eat|eating|feed|feeding|dinner|lunch|supper|tea|buffet|barbecue|bbq)\b"
    r"|\b(?:meat|chicken|beef|pork|lamb|mince|rice|pasta|potato|potatoes|veg|vegetables?|"
    r"salad|soup|sauce|gravy|stuffing|bread|pastry|cheese|milk|cream|fruit|berries|cake|"
    r"biscuits?|pudding|dessert|starter|curry|stew|lasagne|lasagna|pie|quiche|sausages?|bacon|"
    r"eggs?|fish|salmon|prawns|prawn|prawns|cheese|butter|flour|sugar|oats|yoghurt|yogurt|"
    r"beans?|lentils?|chickpeas|nuts?|spuds|chips|roast|joint|turkey|duck|ham|tofu|hummus)\b",
    re.I)
# What one pack covers is a coverage sum, and only a line about a material is one.
MATERIAL = re.compile(
    r"\b(?:paint|primer|undercoat|gloss|emulsion|wallpaper|paste|tiles?|grout|adhesive|"
    r"sealant|filler|plaster|cement|mortar|sand|gravel|bark|chippings|soil|compost|mulch|"
    r"feed|fertiliser|fertilizer|weedkiller|seeds?|grass seed|oil|varnish|stain|lacquer|"
    r"thinner|white spirit|bleach|detergent|washing powder|liquid|tablets|conditioner|"
    r"softener|disinfectant|cleaner|shampoo|foil|cling film|bin bags?|kitchen roll|cat litter|"
    r"litter|screws?|nails?|rawlplugs|dowels?|cable|wire|rope|string|tape)\b", re.I)
# Money on an account or up front is a figure that exists and is written down in one place: the
# coverage sum is the wrong arithmetic for it.
MONEY_ON_A_JOB = re.compile(
    r"\b(?:up front|deposit|pay|paid|paying|money|afford|budget|cost|costs|price|[£$€])\b", re.I)

# ---- whether a thing is still good ------------------------------------------------------------
#
# The keeping question, for food and for anything with a date on it. The rule that settles it is
# two things - how long, and how it was kept - and the line that draws it is the pack's own date.
# The advice past that line is the safe direction, because the safe direction is the only one the
# bot may give without seeing the thing.
STILL_GOOD_RULE = (
    "Whether it is still good turns on two things: how long it has been and how cold it stayed. "
    "The date on the pack is the line - past it, or warm for hours, it goes - and I will say what "
    "I would do with the details: which it is, and when it went in.",
    "Two things decide that, and neither is on my side of the screen: how long, and how it has "
    "been kept. The pack's own date is the limit; inside it and cold all along is fine, and past "
    "it or out for half a day is not worth the risk. The date on it is the one to read, and tell "
    "me that and when it went in and I will say what I would do.",
    "That is a keeping question rather than a recipe one: the date to go by is the one on the "
    "pack, and how it has been kept since decides the rest. Tell me when it went in and how it "
    "has been stored, and I will say what I would do.",
)
# The phrases that carry the question themselves, with no noun needing naming: something has
# gone off, or there is a date on it and it is the one that decides. "out of date" and "use by"
# are the same ruling whether it is a pot of cream or a passport - the thing's own date is the
# line, and how it has been kept since is the rest of it.
GONE_OFF_ASK = re.compile(
    r"\bgone off\b|\bout of date\b|\b(?:use by|best before|sell by)\b", re.I)
# The ask as it is actually put. "still" carries it on its own - "is it still ok to eat", "can i
# still have the pasta" - because the person is asking about time, which is the whole question.
STILL_ASK = re.compile(
    r"\bstill\b[^?.!]{0,40}?\b(?:ok|okay|fine|safe|alright|good|eat|eaten|use|using|keep|have|"
    r"drink|give|serve|cook|reheat|freeze|edible)\b"
    r"|\b(?:it|that|this|they|these)\b[^?.!]{0,30}?\bstill\b"
    r"|\bgone off\b|\bout of date\b|\bpast (?:its|the|their) (?:date|use by|best before)\b"
    r"|\buse by\b|\bbest before\b"
    r"|\bhow long (?:does|do|will|can|would)\b[^?.!]{0,30}?\b(?:keep|last|stay good|"
    r"stay fresh)\b",
    re.I)
# "how long does that keep" is the keeping question whatever it is about - the keeping is the
# verb, and the pack's date is the answer. "how long does it last" is not, because that is the
# same words about a washing machine.
KEEP_ASK = re.compile(
    r"\bhow long (?:does|do|will|can|would)\b[^?.!]{0,30}?\b(?:keep|stay fresh|stay good)\b",
    re.I)
# The same ask without "still" in it, which only counts when the line names something that can go
# off: "is it ok to eat chicken thats been in the fridge 4 days" is the keeping question, and
# "my son has a nut allergy, what can i cook for dinner" is not, though both have the words.
OFF_ASK = re.compile(
    r"\bis it (?:ok|okay|fine|safe|alright|good) (?:to|for)\b"
    r"|\bcan i (?:eat|use|keep|drink|have|give|serve|freeze|reheat|cook)\b"
    r"|\bis (?:it|that|this) (?:ok|okay|fine|safe|alright)\b"
    r"|\bwill (?:it|that|they|these) be (?:ok|okay|fine|alright|safe)\b", re.I)
# A dose is not a keeping question: the health cards and `safety.py` own every line with one.
NOT_A_KEEPING_QUESTION = re.compile(
    r"\b(?:medicine|medicines|tablets?|pills?|capsules?|dose|doses|dosage|paracetamol|ibuprofen|"
    r"calpol|antibiotics?|inhaler|insulin|syrup|prescription|allergy|allergic)\b", re.I)
# "Can I freeze this" is a question about what the thing will take, not about whether it is good
# today, and a dish somebody made has no pack to read a date off. The keeping rule points at the
# pack's own date, so where there is no pack - and where the ask is the freezer rather than the
# date - it has nothing to point at and stays out of the line.
KEEPING_HAS_NO_DATE = re.compile(
    r"\b(?:freeze|freezes|freezer|freezers|freezing|frozen|thaw|thaws|thawed|thawing|defrost|"
    r"defrosted|refreeze|re-freeze)\b"
    r"|\b(?:i|we) (?:made|make|baked|cooked|roasted|prepared|whipped up)\b", re.I)
# A body on a scale is not a joint on a plate: a weight asked about a person, a baby or a pet is
# not a portion to count, and it is the health lanes' question.
ABOUT_A_PERSON_OR_AN_ANIMAL = re.compile(
    r"\b(?:baby|babies|infant|newborn|toddler|child|children|boy|girl|son|daughter|kid|kids|"
    r"pup|puppy|kitten|dog|cat|months? old|years? old|weigh|weighs|weight|stone|kg|lbs|"
    r"pounds)\b", re.I)
# The food and pack nouns, on their own, without the verbs: "what can i eat" and "can i keep the
# handset" are not keeping questions, and a verb was all they had in common with one.
FOOD_OR_PACK = re.compile(
    r"\b(?:chicken|beef|pork|lamb|turkey|duck|ham|bacon|mince|sausage|sausages|fish|salmon|"
    r"prawns|shellfish|rice|pasta|noodles|potato|potatoes|veg|vegetables?|salad|soup|sauce|"
    r"gravy|bread|toast|pastry|cheese|milk|cream|yoghurt|yogurt|butter|eggs?|fruit|berries|"
    r"cake|quiche|pie|pudding|leftovers?|takeaway|curry|stew|lasagne|lasagna|sandwich|meat|"
    r"food|pack|packet|tin|jar|bottle|carton|use by|best before|date on it|label)\b", re.I)


# ---- how long it takes -----------------------------------------------------------------------
#
# A time asked for. The bot cannot know the number, and it does not have to: a time is a rate
# multiplied by a size - minutes per kilo, hours per coat, weeks per module - and the rate is
# published by whoever does the work (the recipe, the course, the trade). Saying that is worth
# more than "I don't know enough to answer that honestly", because it turns the shrug into a
# sum the person can finish, and the bot can do the sum.
TIME_RULE = (
    "A time is a rate times a size: minutes per kilo, hours per coat, days a chapter. Whoever "
    "sets the rate - the recipe, the course, the trade - says what it is, and give me your size "
    "and I will do the multiplication.",
    "How long it takes comes from how big the job is and how fast it goes, so the number to find "
    "is the rate rather than the total, and the rate is published - on the pack, in the recipe, "
    "or by whoever does the work. Tell me the two figures and I will work out the time.",
    "Time is the part I can work out but cannot know: the size of the job, times the rate it goes "
    "at. Bring me the rate from whoever does it and the size of yours, and I will turn it into a "
    "finish time you can plan round.",
)
TIME_ASK = re.compile(
    r"\bhow long (?:will|would|does|do|should|shall|can|could|might|must)\b[^?.!]{0,44}?"
    r"\b(?:take|takes|last|lasts|go in|sit|rest|stay in|be in|preheat|defrost|chill|set|rise|"
    r"prove|boil|simmer|roast|cook|bake|fry|grill|steam|soak|marinate|dry|run|walk|drive|train|"
    r"learn|build|fit|paint|decorate)\b"
    r"|\bhow long (?:is|would be) (?:it|that|this)\b[^?.!]{0,30}?\b(?:before|until|to)\b"
    r"|\bhow long (?:until|before)\b[^?.!]{0,40}?\b(?:done|ready|cooked|finished|it is|its)\b",
    re.I)
# A how-long question that is about a person, a wait out in the world, or the past is not this one.
TIME_NOT_THIS = re.compile(
    r"\b(?:ago|been|queue|waiting list|on hold|does it keep|how long have)\b", re.I)
# A cooking time is asked of a joint, a bird, a cake - "how long should the lamb go in" - and the
# answer is a weight times a heat, which is a card ("a leg of lamb is 25 minutes per 500g at
# 200C"). The rule read the same words and answered with the arithmetic in the abstract: "Time is
# the part I can work out but cannot know: the size of the job, times the rate it goes at", which
# is a lecture about a roast rather than the time it goes in. Where a food is named with an oven
# word or a cooking verb, this stands down: the cooking cards keep the turn when they can take it,
# and the fallback says the one thing that decides it - the weight and the heat - when they cannot.
A_COOKING_TIME = re.compile(
    r"\b(?:roast|roasting|cook|cooking|bake|baking|boil|boiling|simmer|fry|frying|grill|grilling|"
    r"steam|steaming|poach|oven|go in|goes in|be in|sit in|stay in|rest|barbecue|bbq|"
    r"air fryer|slow cooker|pressure cooker|pan)\b", re.I)
A_FOOD = re.compile(
    r"\b(?:lamb|beef|chicken|turkey|duck|goose|pork|ham|gammon|bacon|sausages?|mince|steak|"
    r"joint|bird|casserole|stew|pie|tart|cake|sponge|bread|loaf|scones?|biscuits?|pudding|"
    r"potatoes?|chips?|veg|vegetables?|carrots?|parsnips?|onions?|rice|pasta|lasagne|lasagna|"
    r"eggs?|fish|salmon|trout|cod|prawns?|tofu|halloumi|mushrooms?|tomatoes?|peppers?"
    r"|dough|batter|pastry)\b", re.I)


def the_rule_for_it(clean, repaired=None):
    """The pool for the kind of ask this line is, or None when it is not one of the kinds.

    Read only for a line that is about to be shrugged at, and read on the repaired line as well
    as the typed one, the way every other pool here is: "how mutch does a tattoo cost" is the
    same ask.
    """
    for line in (clean, repaired):
        said = " ".join(str(line or "").lower().split())
        if not said:
            continue
        if NOT_A_KEEPING_QUESTION.search(said):
            return None
        if ABOUT_A_PERSON_OR_AN_ANIMAL.search(said):
            return None
        if not KEEPING_HAS_NO_DATE.search(said):
            if KEEP_ASK.search(said) or GONE_OFF_ASK.search(said):
                return STILL_GOOD_RULE
            if STILL_ASK.search(said) and FOOD_OR_PACK.search(said):
                return STILL_GOOD_RULE
            if OFF_ASK.search(said) and FOOD_OR_PACK.search(said):
                return STILL_GOOD_RULE
        if AMOUNT_ASK.search(said) and not MONEY_ON_A_JOB.search(said):
            if MATERIAL.search(said) and not FEEDING.search(said):
                return AMOUNT_COVER_RULE
            if FEEDING.search(said):
                return AMOUNT_FEEDING_RULE
        if (PRICE_VERDICT.search(said) and not NOT_ABOUT_A_PRICE.search(said)
                and not A_DEAR_AS_A_NAME.search(said)):
            if A_CAB_OR_A_LIFT.search(said):
                return CAB_FARE_RULE  # the meter, not the day: no seat and nothing to book ahead
            if A_AN_OCCASION.search(said):
                return OCCASION_PRICE_RULE  # per head, by the day: not a job and not a fare
            if A_FARE_OR_A_TICKET.search(said):
                return FARE_PRICE_RULE
            return PRICE_VERDICT_RULE  # a verdict names no job: only what is true of any price
        if PRICE_ASK.search(said) and not NOT_ABOUT_A_PRICE.search(said):
            if A_CAB_OR_A_LIFT.search(said):
                return CAB_FARE_RULE
            if A_AN_OCCASION.search(said):
                return OCCASION_PRICE_RULE
            return PRICE_RULE
        if TIME_ASK.search(said) and not TIME_NOT_THIS.search(said):
            if A_COOKING_TIME.search(said) and A_FOOD.search(said):
                return COOKING_TIME_RULE  # a joint and an oven: the weight and the heat
            return TIME_RULE
    return None


# A care thread is never answered by a rule of thumb. "My dog is having an operation tomorrow" /
# "im worried" / "how long will it take" was given "a time is a rate times the size of the job" -
# the arithmetic for a roast, said to somebody waiting on a vet. The words are few and none of
# them is a coincidence: an operation, a ward, a course of treatment, an animal at the vets.
A_CARE_WORD = re.compile(
    r"\b(?:operation|surgery|theatre|hospital|hospitalised|ward|vets?|vet's|recovery|recovering"
    r"|rehab|treatment|chemo|chemotherapy|dialysis|scans?|consultant|nurse|nurses"
    r"|doctor|doctors|gp|111|a&e|icu|hospice|palliative|dementia|carer|carers"
    r"|in labour|due date|pregnant|pregnancy)\b")


# A debt being paid down is a rate and a size too, and the sums in `TIME_RULE` are still the wrong
# thing to say to "ive got 2000 on a credit card" / "how long will that take to clear": the rate is
# the APR and the size is theirs, and a rule about coats and kilos reads as not listening. The
# words are money words in the thread, not in the line, because the line is usually the bare ask.
A_MONEY_WORD = re.compile(
    r"\b(?:credit card|credit cards|card|cards|apr|loan|loans|mortgage|mortgages|overdraft"
    r"|debt|debts|interest|repayments?|overpay|overpaying|arrears|rent arrears|invoice"
    r"|bailiffs?|iva|ccj|payday|minimum payment|balance)\b")


# The five pools, for the one reader that has to know this band is the last resort and not an
# answer: `fallback.is_a_hedge`, which the arbiter uses to pass a shrug over for anything that
# knows the line. Without this a rule would outrank the answer the bot had just read out - "how
# long do i cook them", a turn after "200g of plain flour for four people", was given the time
# rule instead of "they take a minute a side in a hot pan". A rule is what is said when nothing
# else can be, so it is classed with the hedges it stands in for, and every real answer beats it.
# A cooking time is one number and one question: minutes per 500g at a heat. Everybody publishes
# it - on the pack, in the recipe, in a book on the shelf - so the useful thing to say is where it
# is and what to bring, not the formula about jobs and rates, and not a shrug either. The cards
# take this line whenever they know the cut; this pool is what is left when they do not.
COOKING_TIME_RULE = (
    "Oven times go by weight and heat: minutes per 500g at a set temperature, and both are on the "
    "pack or in the recipe. Tell me the weight and the heat and I will work out the clock time for "
    "you.",
    "That one is a minutes-per-500g job at a set heat, and the figure for the thing you are "
    "cooking is on the pack, the recipe or the book. How heavy is it, and what heat are you "
    "using?",
    "The weight and the oven heat decide it, and the rate for that joint or bird is written down "
    "somewhere you already have - the pack, the recipe, or the shop's own guide. Bring me the "
    "weight and I will do the arithmetic.",
)
RULE_POOLS = (PRICE_RULE, PRICE_VERDICT_RULE, FARE_PRICE_RULE, CAB_FARE_RULE,
              OCCASION_PRICE_RULE,
              AMOUNT_FEEDING_RULE,
              AMOUNT_COVER_RULE, STILL_GOOD_RULE, COOKING_TIME_RULE, TIME_RULE)
RULE_HEADS = tuple(line[:40] for pool in RULE_POOLS for line in pool)
