"""Where a person would find out what the bot cannot know.

The bot has no network and no files, so it cannot read the small print of an insurance policy or a
travel pass, and it cannot say what somebody else's rules allow. Those are ordinary questions that
people bring here often, and they used to end in the honest hedge ("a search should sort you out
quickly"), which is true and no help at all.

The live table in fallback.py already does the right thing for the weather, opening hours, live
prices and stock of a named thing, and `bot/compose/prices.py` reads a price asked as a shape.
This module is the same move for the two kinds those do not carry: **the terms a thing is sold
under** (what the policy, the pass or the warranty covers) and **whose rules allow something**
(is that legal, can I bring this in, what can my landlord ask for).

`options(clean)` returns a pool of replies, or None when the line is not one of those kinds. The
caller is `bot/modules/where_it_answers.py`, a module of its own at PRIORITY -999: it asks the
composer first and stands down unless that reply is a hedge, so this can only ever take the place
of a hedge, never a card's turn or a reply of the composer's own. It is a module rather than a hook
in `bot/compose/fallback.py` because that file is over the world's 1,048,576-byte cap on main.

Nothing here invents a fact. Each reply says, in a few words, what the bot cannot see and then
names the one place the answer actually lives: the terms page for what is included, the insurer
for a policy, the operator for what you can bring on, the council for its own rules, and Citizens
Advice or ACAS for a tenancy or a job. "Not knowing, honestly" in STYLE.md is the bar: a short
honest route beats a confident guess, and a confident guess here is somebody travelling on a
made-up rule or claiming on a policy that never covered them.
"""
import re

# What a thing is sold under. The thing has to be named, because "cover" on its own is the lid on
# a pan ("should i cover it") and a sheet over the plants on a frosty night, and neither of those
# is a question about terms.
INSURANCE_WORD = re.compile(
    r"\b(?:insurance|insurer|insured|insure|insures|policy|policies|excess|excesses|claim|"
    r"claims|cover note)\b")
TERMS_THING = re.compile(
    r"\b(?:insurance|policy|cover note|pass|railcard|ticket|tickets|warranty|guarantee|"
    r"membership|subscription|tariff|contract|lease|tenancy|terms|small print|conditions|"
    r"excess|excesses|deposit|exclusions|breakdown|breakdown cover|recovery|roadside|contents "
    r"cover|gadget cover|extended warranty)\b")
# What a holiday, a room or a job of work comes with is the same kind of question - "is breakfast
# included in the room rate" - but the thing named is the rate, not a policy, so the price words
# are read with it. "included" on its own catches "is my son included in the photo".
PRICE_THING = re.compile(
    r"\b(?:price|prices|rate|rates|cost|costs|booking|room|rooms|hotel|holiday|package|deal|"
    r"hire|fee|fees|quote|breakfast|meals?|parking|wifi|transfer|transfers|extras?|tax|taxes|"
    r"vat|service charge|delivery|postage and packing|p&p)\b")
INCLUDED_ASK = re.compile(
    r"\b(?:is|are|was|were|does|do)\b[^?]{0,35}\b(?:include|includes|included|extra|"
    r"free with|come with|comes with)\b")

# "covered" is not a thing, it is a state, and it belongs to a subject: "is my phone covered on
# holiday", "am i covered for a cancelled flight". Read as a bare word it catches "should i keep
# it covered" (a burn) and "keep the plants covered", where no terms page has anything to say.
COVERED_PHRASE = re.compile(
    r"\b(?:am i|are we|are they|is it|is that|is this|is my|is our|is the|is that phone|"
    r"are my)\b[^?]{0,30}\bcovered\b")
# The ask that reads those terms: "does my pass cover the sleeper", "will the insurance cover
# it", "is my phone covered on holiday", "is the excess included", "does the warranty count".
TERMS_ASK = re.compile(
    r"\b(?:cover|covers|covered|include|includes|included|excluded|excludes|apply|applies|"
    r"count|counts|valid|honour|honoured|pay out|payout|work|works|worked|accepted|accept|"
    r"any use|use it|use on)\b")

# "how do i work out whether a gym membership is worth it" is a sum to do, not a term to read,
# and "work" alone in TERMS_ASK was reading it as one.
WORKING_OUT = re.compile(r"\bwork(?:s|ed|ing)?\s+out\b")

# A rule somebody else sets, which is not a card and not something the bot can look up: "is that
# allowed", "are dogs allowed", "can i take my own wine on the ferry", "they want 30 days notice,
# is that allowed", "is she allowed at 13".
# "is it ok to put a plaster on it", "is that ok for the baby", "some days are ok" are advice or
# a mood, not a rule somebody else sets, so "ok" and "alright" are deliberately not in here: what
# makes a line this kind is the language of permission, and nothing else.
ALLOWED_ASK = re.compile(
    r"\b(?:is|are|was|were|am i|are we|can i|can we|could i|may i)\b[^?]{0,30}"
    r"\b(?:allowed|permitted|legal|against the rules)\b")
# Taking a thing onto somebody else's property, which is the same question in another shape:
# "can i take my own wine on the ferry", "can we bring the dog into the restaurant".
TAKE_ON = re.compile(
    r"\b(?:can|could|may|am i allowed to|are we allowed to)\s+(?:i\s+|we\s+)?(?:take|bring|carry|"
    r"pack|board with)\b[^?]{0,60}\b(?:on|onto|into|in|aboard)\b")

# The same question with the place given as a destination: "can i bring my own drinks to the
# arena". Only read when the line names a place of its own, or "can i take my son to school" would
# become a question about the school's rules.
TAKE_TO = re.compile(
    r"\b(?:can|could|may)\s+(?:i|we)\s+(?:bring|take|carry)\b[^?]{0,60}\bto\b")

# A permission somebody else grants - a licence, a permit, a visa, a certificate, a medical - is
# theirs to give and theirs to refuse, and the conditions are on the page that grants it. The
# permission has to be named, because "do i need to book" and "do i need an umbrella" are not this
# kind: what makes the line one is a thing another body issues.
NEEDED_THING = re.compile(
    r"\b(?:licen[cs]e|licen[cs]es|licen[cs]ing|licen[cs]ed|permit|permits|visa|visas|register|"
    r"registration|registered|certificate|certification|medical|inspection|qualification|"
    r"qualifications|background check|dbs check|crhb|health and safety|passport|passports)\b")
NEEDED_ASK = re.compile(
    r"\b(?:need|needs|needed|require|requires|required|have to|has to|must|renew|renewing|"
    r"speed up|speed it up|expedite|fast track|pay extra|pay more)\b")

# Getting out of an agreement before it runs out: the notice, the fee and whether they can charge
# at all are in the terms it was signed under, so this is the contract question in another shape.
# The agreement has to be named, or "can i cancel my meeting" and "should i cancel the card" would
# be sent to Citizens Advice.
AGREEMENT_WORD = re.compile(
    r"\b(?:tenancy|tenant|lease|landlord|letting agent|contract|membership|gym|subscription|"
    r"phone|mobile|broadband|internet|insurance|policy|booking|holiday|rental|hire|course)\b")
# Cancelling something that is not an agreement - a card, a meeting, a table - is not a question
# about terms, and "cancel early" on its own would reach it.
NOT_AN_AGREEMENT = re.compile(
    r"\b(?:card|meeting|dinner|lunch|reservation|restaurant|appointment|appointments|plans?|"
    r"party|birthday|barbecue|bbq)\b")
LEAVING_ASK = re.compile(
    r"\b(?:cancel(?:ling)?\s+early|leave\s+early|break the contract|end the contract|"
    r"charge\w*\s+me\s+to\s+(?:leave|cancel|go)|how much to cancel|notice period|"
    r"early termination)\b")
# "get out of" on its own catches "how do i get out of bed" and "i get out of breath", so it is
# only read with the thing being left named beside it.
GET_OUT_OF = re.compile(r"\bget(?:ting)?\s+out\s+of\b")
# "leave early" is a rota or a shift as often as it is an agreement: "my boss wont let me leave
# early" is a line about the person's day, and Citizens Advice is the wrong reply to it.
SHIFT_WORD = re.compile(r"\b(?:rota|shift|shifts|boss|manager|supervisor)\b")
LEAVE_EARLY = re.compile(r"\bleav(?:e|ing)\s+early\b")
# What it costs to call something off - a fee, a charge, a policy - is a term on the page that
# sold it, so it is read as the terms rather than as a contract to argue over.
CANCEL_TERMS = re.compile(
    r"\b(?:cancellation (?:fee|fees|charge|charges|policy)|how much to cancel|"
    r"fee to cancel|cost to cancel|charge to cancel|refund policy)\b")

# The same terms question with no ask verb in it. "How long is the warranty", "what's the
# cancellation policy", "is wind damage covered", "is my phone insured abroad": a term word is
# there, so the answer is written down somewhere, but a page that waits for "cover" or "include"
# never sees the line and the person gets a search hedge about a figure or a rule that is printed.
# The thing named can also be what happened to it - wind, water, a fall - because a policy names
# its perils rather than its objects.
HARM_NOUN = re.compile(
    r"\b(?:damage|damaged|flood|flooding|flooded|storm|storms|wind|water|fire|theft|thief|"
    r"thieves|stolen|stole|accidental|accident|liquid|injury|injuries|illness|subsidence|burst|"
    r"vermin)\b")
TERM_SHAPE = re.compile(
    r"\bhow long\b[^?]{0,30}\b(?:warranty|guarantee|guaranteed|cover|policy|contract|lease|"
    r"tenancy|membership|subscription|protection)\b"
    r"|\b(?:cancellation|refund|returns?|claims?|exchange) polic(?:y|ies)\b"
    r"|\binsur(?:e|ed|es|ing|ance)\b"
    r"|\b(?:what|which|whos|who) (?:is |are )?(?:not )?cover(?:ed|s)?\b")
# A price asked of a term - "what would the insurance be roughly", "how much is cover for a used
# car" - is somebody's number for this person, so it is a quote and not a rule. The bare
# "insur..." arm of TERM_SHAPE is what let a quote reach the subject-to-exclusions paragraph; a
# word that names the term itself keeps the line, and the price readers keep the rest.
PRICE_ASK = re.compile(
    r"\b(?:how much|how many|cheapest|cheaper|quote|quotes?|priced?|prices?|cost|costs|costly|"
    r"roughly|budget)\b")
TERM_WORD = re.compile(
    r"\b(?:policy|policies|excess|excesses|claim|claims|terms|small print|conditions|"
    r"exclusions|warranty|guarantee|deposit|premium|premiums)\b")

# What counts towards an allowance somebody else sets - the weight in a case, the bag in the hold,
# the pushchair on a fare - is decided on the operator's page, not by anything here.
COUNT_AS = re.compile(r"\bcount(?:s|ed|ing)?\s+(?:towards|toward|as)\b")
ALLOWANCE_WORD = re.compile(
    r"\b(?:luggage|baggage|allowance|limit|weight|fare|fares|ticket|tickets|quota|carry on|"
    r"cabin bag|hand luggage|bag|bags|pushchair|buggy|pram)\b")

# "could we take it to the pub" is a suggestion between two people, not a question about whose
# rules apply, and the thing taken on has no name to read. A named thing keeps the line - "can i
# bring my own drinks to the arena", "can we bring the dog into the restaurant".
NAMED_OBJECT = re.compile(r"\b(?:take|bring|carry|pack|board with)\s+(?:it|this|that|them|those|one)\b")

# Somebody else's rules where the thing being taken on is not the bot's business to guess at, and
# the person is asking about a place rather than a contract: a ferry, a restaurant, a campsite, a
# festival. The rules belong to whoever runs the place, so the reply names them.
VENUE_WORDS = re.compile(
    r"\b(?:ferry|plane|flight|train|bus|coach|tube|tram|boat|cruise|hotel|restaurant|cafe|pub|"
    r"camping|campsite|camp site|festival|stadium|ground|museum|gallery|cinema|pool|park|beach|"
    r"venue|abroad|airport|airline|airlines|on board|carry on|cabin bag|hand luggage|luggage|"
    r"baggage|suitcase|arena|theatre|gig|club|conference|showground|racecourse)\b")

# A contract, a tenancy or a job: the rules are written down somewhere, and there is a free,
# disinterested person whose whole job is reading them with you. That is a better answer than
# "the place's own page", which for a landlord or an employer does not exist.
CONTRACT_WORDS = re.compile(
    r"\b(?:landlord|letting agent|tenancy|tenant|deposit|notice|contract|employer|employee|boss|"
    r"redundancy|dismissed|sacked|refund|fined|fine|penalty|course of action|small claims|"
    r"rent|evict|evicted|eviction|housing|mortgage|arrears|work|working|job|jobs|shift|shifts|"
    r"annual leave|time off|day off|holiday ?pay|sick pay|maternity|paternity|overtime|rota)\b")

# A licence, a permit, a visa: the body that grants it is the only place the conditions are
# written, and it is also the only place that can say whether this person's own case needs one.
ISSUER = (
    "A licence, a permit or a visa is granted on conditions the issuing body writes, and most "
    "publish them as a short list: what you need, what it costs, how long it takes. The council "
    "grants licences and permits, and the government's site has passports, visas and driving "
    "licences. Their page first, their phone line if your own case is unusual.",
    "Conditions come from whoever grants the permission, and they are on its own site rather than "
    "in the form. The same body can tell you whether your own case needs one at all, and a phone "
    "call about that is usually quicker than filling anything in.",
)

LOCAL = (
    "Council rules are written for a street or a postcode, which is exactly why nobody else can "
    "answer them for you: a parking permit, the bin day, what the tip takes and planning are all on "
    "your own council's site. Their phone line gets you a straight answer about your address.",
    "Parking, bins, a permit, a hedge, planning: the council writes those rules and enforces them, "
    "and they are on its site under those headings. A ring with your address sorts out which one "
    "applies to you.",
)

# A line has to be asking. The understanding engine reads some questions as statements ("is my
# phone covered on holiday" arrived as one), and a route offered for "my insurance covers it,
# don't worry" is the wrong reply to somebody who was not asking anything.
QUESTION = re.compile(
    r"^\s*(?:is|are|was|were|does|do|did|will|would|can|could|should|shall|may|am|have|has|"
    r"what|whats|which)\b"
    r"|\b(?:is it|is that|is this|is she|is he|is my|is the|are they|are we|does it|does my|"
    r"does the|do they|do i|will it|will my|would it|can i|can we|should i)\b"
    r"|\bhow (?:much|long|do i|can i|does|would)\b")

# A child's permissions are a parenting question, not a rule about a place: "is she allowed at 13",
# "were the kids allowed out on their own". The bot has nothing to say about somebody's own child,
# and a route to the council's page is the wrong kind of answer.
# A hospital is the ward's rules, not a page anybody can read: "is he allowed visitors" is
# answered by the ward looking after him, and a reader in this lane (#9022) names it. The two
# words together are the guard, so "can i take my own drinks to the hospital" keeps its route.
WARD = re.compile(
    r"\b(?:hospital|ward|icu|hdu|itu|nicu|scbu|intensive care|high dependency|patient|patients|"
    r"ward sister|nurse in charge)\b")
VISITOR = re.compile(r"\b(?:visitors?|visiting|visit)\b")
# "is my mum allowed visitors": a person in a bed somewhere, so the ward or the care home says,
# and "a ring to them before you set off" is the wrong picture for it.
SOMEONES_PERSON = re.compile(
    r"\b(?:my|his|her|our|their)\s+(?:mum|mom|mam|dad|mother|father|nan|nana|gran|granny|"
    r"son|daughter|sister|brother|wife|husband|partner|friend|aunt|uncle|cousin|neighbour|"
    r"neighbor|grandad|grandpa|grandma)\b")

# "Is it legal to refuse cash", "is it legal to record a call": the law is the decider, not the
# person who runs the place, and the venue pool's own words say its rules are "set by whoever runs
# the thing rather than by the law". A line that names the law belongs to the reader that knows the
# law, so the venue branch stands down rather than claim the door has the last word on it.
LAW_NAMED = re.compile(
    r"\b(?:the law|in law|against the law|legal|illegal|legally|unlawful|statute|statutory|"
    r"consumer rights|gov\.?uk|offence|offense|criminal|solicitor|lawyers?)\b")

# ... except that a thing carried into a place is still that place's rule, whatever word the person
# uses for it. "Is it legal to take food into the cinema" is not statute: the cinema decides. So the
# law fence stands down only when what is asked is the law's, which is not the case when a person is
# carrying something in past the door.
CARRYING = re.compile(r"\b(?:take|taking|bring|bringing|carry|carrying|come in|walk in|get in)\b")
TO_INSIDE = re.compile(r"\b(?:into|inside|on board|aboard|through security|in the cabin)\b")

PERSON_ALLOWED = re.compile(
    r"\b(?:she|he|my son|my daughter|my kid|my kids|my child|my boy|my girl|the kids)\b"
    r"[^?]{0,20}\ballowed\b")

# A council's rules: parking, bins, a tip, noise, a hedge over the path. The county or district
# council is the one that writes them and the one that acts, so the reply can name it.
# The council's own rules are this module's; a court date, a summons or a notice through the door is
# a procedure with one right place to read it, and another reader owns that arm. This fence keeps the
# two of us from ever both speaking on the same line (agreed with that lane, #9034).
COURT_ARM = re.compile(
    r"\b(?:summons|summoned|magistrate|court date|court hearing|tribunal|prosecut\w*|"
    r"penalty charge notice|pcn|fixed penalty|fine notice|appeal the fine|contest the fine)\b")

LOCAL_WORDS = re.compile(
    r"\b(?:parking|parked|park on|permit|pavement|kerb|dropped kerb|bins?|bin day|fly tip|"
    r"fly tipping|recycling|planning permission|noise|neighbour's hedge|footpath|right of way|"
    r"council|tip|skip permit|dog fouling|street light)\b")

# The council's own services: the round, the size of the bin, the tip, a permit, a street light,
# a pothole, planning, a place at a school. `LOCAL_WORDS` knows those words too, but it was only
# ever read for the two permission shapes below ("can i take this to the tip"), so every other way
# of asking one of them fell through to the honest hedge - "what do i do about the bins", "how do i
# get a second bin" - or, worse, to an advice agency that cannot see a street either ("how do i
# apply for a parking permit" was answered "Citizens Advice covers this free, and a call beats
# searching"). A local authority service is decided for an address by the authority that runs it
# and published by it, so the honest reply says the two things that are true of every one of them -
# it is set per address, and the authority's own site or phone line is where the answer lives - and
# then names what it cannot do: it cannot see the person's street. Nothing in it can go stale.
#
# The words are read from a list of the services themselves rather than from `LOCAL_WORDS`,
# because that list is a wider net for a narrower question: "parking" and "noise" belong to a
# permission ask and to a noise somebody heard as well, and no page about a permit answers either.
SERVICE_WORDS = re.compile(
    r"\b(?:bins?|wheelie|recycling|bulky waste|household waste|garden waste|the tip(?! of)"
    r"|recycling cent(?:re|er)|street lights?|street lamps?|potholes?|kerbs?|gritting"
    r"|fly ?tipping|(?:parking|resident|visitor) permits?|planning permission"
    r"|planning application|allotments?|council tax)\b")

# A complaint about a neighbour's noise is the council's; a noise somebody heard is not, so one
# word is not enough and the second list is what makes it a complaint.
NOISE = re.compile(r"\bnoise\b|\bnoisy\b")
COMPLAINT = re.compile(
    r"\b(?:neighbours?|next door|loud music|nuisance|complain\w*|report\w*"
    r"|environmental health|council)\b")

# The word "bin" is a verb as often as it is a service: "should i just bin it", "does that mean i
# should bin it" are a person deciding to throw something away, and the council has no page for
# that. A kitchen bin, a bread bin and the recycle bin on a desktop share the word too.
NOT_A_SERVICE = re.compile(
    r"\bbin(?:ned|ning)?\s+(?:it|that|this|them|those|these)\b"
    r"|\b(?:should|shall|do|can)\s+(?:i|we)\s+bin\b"
    r"|\b(?:bread|kitchen|pedal|nappy|compost|diaper|sensor|swing) bins?\b|\brecycle bin\b"
    r"|\brecycling bin\b|\bwindows?\b|\blaptop\b|\bdesktop\b")

# A line is asking about its own street when it puts a question, by word or by mark. A report
# ("the bin men came at six again") is conversation, not a request for a page, so it stands down.
ASKING_SHAPE = re.compile(
    r"\b(?:what|how|where|who|when|why|which|can|could|should|do|does|did|is|are|will|would)\b"
    r"|\?")

# Taking something with food or on an empty stomach is a question about a body, not about whose
# rules apply: "can i take paracetamol on an empty stomach" was reaching the permission pool. The
# reading is the health shape, not the drug's name, so an unseen medicine lands.
BODY_STATE = re.compile(
    r"\b(?:on an empty stomach|empty stomach|with food|with water|before food|after food|"
    r"before eating|after eating|on antibiotics|with alcohol|on a full stomach)\b")

# "should i cover it", "shall i cover the pan": the lid, not the policy. A line that is deciding
# whether to put something over something else is a cooking or garden decision, and no terms page
# has anything to say about it.
COVER_IT = re.compile(r"\b(?:should|shall|do|can)\s+(?:i|we)\s+(?:cover|covering)\b")

# "is my phone covered in suncream", "is the path covered in ice": covered in something is a
# physical covering, and telling that person to look for the letter about their terms is worse
# than saying nothing. Only "in" and "with" are stood down, because "is my shed covered by my
# home insurance" is a policy question and keeps its route.
COVERED_IN = re.compile(r"\bcovered\s+(?:in|with)\b")

# The pools. Three lines each, in the voice of the rest of the bot, and each one in the same
# order: what is known about the kind of question (where such an answer is written, how it is
# decided), then the one place the answer actually is, then the move that makes it stick - a
# written answer, or the free adviser who reads it beside you. A pointer on its own is not an
# answer, so no line opens with what the bot cannot do.
TERMS = (
    "Cover sits in a section headed what is included and what is excluded, and the exclusions "
    "are often the longer list. That section is the one that counts; if the page is vague, the "
    "letter or email they sent you repeats the same words, and asking them in writing leaves you "
    "with an answer you can point to.",
    "This turns on one clause: what the policy calls the thing, and whether your loss is on its "
    "list of exclusions. Find that section before you rely on it, and ask them to confirm it in "
    "writing, because a written answer is the one you can hold them to.",
    "What applies is what the wording says, and it is written in the same three places: the "
    "section on what is included, the exclusions, and the letter they sent when you took it out. "
    "A call to whoever sold it you settles the last doubt, and their answer in writing settles it "
    "for good.",
)

# What a price covers is a different page from what a policy covers. "Is wifi included", "is
# parking included in the price", "is breakfast included in the room rate": the person is holding
# a bill, not a policy, and sending them to look for a list of exclusions is the wrong desk. The
# list of what is included is written where the thing is sold, and the extras are charged on the
# day - so the reply names the booking page, the desk, and the total in writing.
INCLUDED = (
    "What a price covers is written where it is sold: the booking page lists what comes with it, "
    "and anything it does not list is charged on top, often at the desk rather than before. Ask "
    "for the total in writing before you pay, and keep that email for the day itself.",
    "Included and not included are two lists, and the second is the one that costs you: it is on "
    "the page you book on, then at the desk, where the extras get added. Read the first list "
    "before you book and ask for the total by email, because that is the version they have to "
    "honour.",
    "A room, a package or a rate names what comes with it in its own terms, and whatever it does "
    "not name is charged separately - parking, breakfast and the wifi are the usual three. Check "
    "that list before you book, and ring to confirm what applies to your own booking.",
)

# The local authority's own services, in the voice of the pools above: what is true of all of them
# first (each one is settled for a whole street, by the authority that runs it, and published by
# that authority), then the one place the answer is, then the move that makes it stick - the
# postcode on their site, or their phone line with the address. The last line names what the bot
# cannot do in a few words, because "I cannot see your street" is the part a person needs to hear.
LOCAL_SERVICE = (
    "Bins, the tip, permits, a street light, a complaint about noise: each one is your local "
    "authority's own service, decided for a whole street at a time and published by the council or "
    "town hall that runs it. Their site takes your postcode and gives the page for your address, "
    "and their phone line with the address answers faster than a search will. Tell me what they "
    "say and I'll help with the next step.",
    "That one is settled per address rather than in general, so I can't see your street from here: "
    "the council or town hall for your address decides it for its own postcodes, and publishes "
    "what it wants from you - the address, the date, and usually one photo. Their page first, then "
    "their phone line if your case does not fit it. What is it you are trying to get done?",
    "Your council or town hall runs that service and writes the rule for it street by street, so "
    "its site with your postcode in it is the only place that is right for your address. Ring them "
    "if the page does not cover your case - they answer for one address faster than a search will. "
    "What have you got so far?",
)

# The same question about a ticket, a pass or a fare: what it is good on is written by the
# operator, so "the letter they sent you" is the wrong address for a railcard and their own page
# on what the fare covers is the right one.
TICKET_WORD = re.compile(
    r"\b(?:railcard|rail pass|ticket|tickets|season ticket|oyster|travelcard|travel card|"
    r"boarding pass|day pass|bus pass|fare|fares|rover|interrail)\b")

OPERATOR = (
    "A ticket usually names on its face the route, the operator and the times it is good for, and "
    "the full conditions live on the operator's page rather than at the station. Check the ticket, "
    "then their page on what the fare covers; the guard on board checks the one you have.",
    "What a pass is good on is set by the operator whose buses or trains it is for, and their page "
    "on what is included lists it by name: the routes, the times and the extras. A call to them "
    "settles your own ticket in a few minutes.",
    "Fares and passes come with conditions written by the company that runs the service, and they "
    "are published with the timetable rather than with the ticket. Their page on what the fare "
    "covers is the one that counts, and the guard on the day has the last word.",
)

# The same question, where the thing is an insurer's: the reply can name the insurer, which is a
# better address than "they" for somebody holding a policy.
INSURER = (
    "A policy is decided by its own wording and its list of exclusions, not by the kind of claim "
    "it sounds like. Read the exclusions first, then ring the insurer to confirm your own case "
    "before you claim or pay for anything: they have to tell you, and that answer is the one that "
    "counts.",
    "Insurers decide this from the wording in your schedule, which is written when the policy is "
    "taken out and does not change with the claim. Their claims line will tell you straight away, "
    "and it is worth asking for it by email so you have it in writing.",
    "Whether a claim is met is the policy's own test: what is included, then what is excluded, "
    "then the excess. The insurer is the only one who can apply that to your case, and asking "
    "before you spend anything is the cheap way round.",
)

ALLOWED = (
    "Places and companies write these rules down, usually under a heading like what you can bring "
    "or what is not allowed, and the person on the door has the last word on the day. Find that "
    "page, then ask them by email so you have the answer to show.",
    "This is somebody else's rule to make, and they are the only ones who can apply it to your "
    "case. An email asking whether it is allowed is worth more than a phone call, because you can "
    "point to it later.",
    "Rules like this are set by whoever runs the thing rather than by the law or by me, and they "
    "are written where you book. If the page is vague, ring before you set off: being turned away "
    "at the door is the expensive way to find out.",
)

# The same question about a place you would be taking something into: the rules are the
# operator's, and they are written for travellers rather than for lawyers.
VENUE = (
    "A ferry, an arena, a campsite: whoever runs the place writes what you can bring on, and it is "
    "on their own page about what is allowed in, not in the booking email. Worth a call before you "
    "travel if the page is vague.",
    "What you can bring on with you is decided by whoever runs the place, and it is written for "
    "travellers rather than for lawyers - on their page about what is allowed in. A quick call "
    "settles it before you pack.",
    "Their rule, written where you book: most places publish what is allowed in and what has to go "
    "in the hold or be left at the door. The page first, then a ring to confirm your own case.",
)

# A landlord, an employer, a shop that will not refund: the terms are in writing, and there is a
# free service whose whole job is reading them beside you. That is a better answer than a page
# the person may not be able to find.
CONTRACT = (
    "That is set by what you agreed to: the section on notice and fees says what it costs to end "
    "it early, and it is usually a fixed sum or the rest of the term. If it is a tenancy or a job, "
    "Citizens Advice, or ACAS for work, will read it beside you for free.",
    "The notice and the fee are on the paper you signed, or in the account page if you joined "
    "online, and it is usually one short section headed ending the agreement. Ask them for the "
    "figure in writing, because that is the one you can hold them to.",
    "Leaving early usually costs a fixed sum or the rest of the term, and the section that says "
    "which is in the terms you agreed. If the wording is not clear, Citizens Advice will go "
    "through a tenancy or an employment contract with you for free.",
)

# ---- what a place has, and what happens to the old one ---------------------------------------
#
# Two everyday asks with no answer written anywhere general, and both are the same fault as the
# rest of this file: a card about something else took them, or the honest hedge did.
#
# "Is there a hairdryer in the room", "is there parking at the hotel": what is in a room is
# decided per building, listed on the page you book on and settled by a call to reception. The
# line to avoid is the price card - "is there parking at the hotel" is not "how much is parking",
# and the charge is a separate line from whether the thing exists at all.
A_PLACE = re.compile(
    r"\b(?:hotel|guest ?house|b\s?and\s?b|hostel|campsite|caravan park|holiday park|cottage|"
    r"villa|apartment|airport|station|venue|concert hall|leisure cent(?:re|er)|swimming pool|"
    r"gym|restaurant|pub|club|theatre|cinema|hospital|surgery|office|rooms?|bedrooms?|the flat|"
    r"the house|the cottage|the caravan|flat we(?:ve| have) booked|the building|building|"
    r"the premises|the shop|the salon|the clinic|the garage)\b")
# A facility or a thing a room may or may not have. "parking" is here rather than in a price list:
# whether there is any at all is the first question, and the charge is the second.
A_FACILITY = re.compile(
    r"\b(?:parking|car park|wifi|wi-?fi|internet|pool|gym|spa|sauna|breakfast|air ?con(?:ditioning)?|"
    r"kitchen(?:ette)?|lift|elevator|shower|bath|towels?|hairdryer|hair dryer|kettle|microwave|"
    r"fridge|freezer|washing machine|iron|tv|television|safe|balcony|room service|charger|"
    r"plug sockets?|"
    r"toaster|crockery|cutlery|pans|a cot|cot bed|high ?chair|towels|bedding|linen|"
    r"accessible|wheelchair|dog friendly|disabled access)\b")
# The things a building has rather than a day out has: named alone they still belong to some place,
# and the pool's own line asks which one. "is there a lift" is not a question about nothing.
A_ROOM_FACILITY = re.compile(
    r"\b(?:parking|car park|wifi|wi-?fi|internet|air ?con(?:ditioning)?|kitchen(?:ette)?|lift|"
    r"elevator|shower|bath|towels?|hairdryer|hair dryer|kettle|microwave|fridge|washing machine|"
    r"iron|tv|television|a safe|the safe|balcony|toaster|a cot|cot bed|high ?chair|"
    r"plug sockets?|room service)\b")
# ... and the ask that the answer to it is yes or no.
A_HAS_ASK = re.compile(
    r"\b(?:is there|are there|is there any|do they have|does (?:it|this|that|the [a-z]+) have|"
    r"have (?:they|you) got|does it come with|will there be|is it got|got a|"
    r"do (?:the|these|those|your) [a-z]+ have)\b")
# A time or an opening is the venue's hours, which the place pools read, and a price is a price.
NOT_A_HAS = re.compile(
    r"\b(?:open|opens|opening|closed?|closing|hours|what time|how much|price|cost|charge|fee|"
    r"parking permit|bus|train|tube|tram|roadworks|traffic)\b")

# "Will they take the old fridge away", "can i keep the old boiler": what happens to the thing
# being replaced is decided by who owns it and by whoever installs the new one, and neither is
# written on a page about boilers. The two answers that are true of every swap: the installer
# takes it if it is asked for at the quote, and a council collection is the free way to lose what
# nobody wants.
THE_OLD_ONE = re.compile(
    r"\b(?:the|my|our|that|this|these|those) old (?:one|ones|unit|units|boiler|fridge|freezer|"
    r"fridge ?freezer|washing machine|dishwasher|tumble dryer|cooker|oven|hob|bath|shower|toilet|"
    r"radiators?|windows?|doors?|carpets?|sofa|settee|bed|mattress|tyres?|batteries|cupboard|"
    r"wardrobe|kitchen|bathroom|fire|fireplace|water tank|tank)\b")
MOVING_THE_OLD = re.compile(
    r"\b(?:keep|keeping|take\b[^,.;]{0,30}\baway|getting? rid|get rid|dispose|"
    r"disposal|recycl\w*|scrap\w*|trade ?in|remove|removed|removal|throw (?:it|them) out|"
    r"skip|tip|leave (?:it|them)|what happens to)\b")
# A food or a pet is not a fitted thing, whatever the sentence says about the old one.
NOT_THE_OLD_ONE = re.compile(
    r"\b(?:rice|potatoes?|bread|milk|chicken|meat|curry|soup|leftovers?|stock|pasta|veg|"
    r"cat|dog|horse|rabbit|hamster|fish)\b")

A_PLACE_HAS = (
    "Whether a place has a thing is decided by that place and not by its name: the same chain "
    "differs from one branch to the next, and a station, an office and a hotel each answer for "
    "themselves. Its own site or the page you book on lists what comes as standard and what costs "
    "extra, and one call to the place confirms what the page leaves out - ask for it in writing if "
    "it matters on the day.",
    "Facilities belong to whoever runs the place, so the current list is on their own page rather "
    "than anywhere general, and anything charged for usually sits on a line of its own, so look for "
    "both before you decide. If the page is silent, the place itself is the one that knows.",
    "That turns on the building rather than the name above the door, and the people there know it "
    "exactly. Ring or email the place itself and ask them to confirm it for the day you are going, "
    "so you have it in writing if it turns out not to be there.",
)

THE_OLD_ONE_POOL = (
    "The old one is usually the fitter's to take: whoever installs the new one carries the old "
    "away for a small fee if you ask when the job is quoted, and a shop that only delivers will "
    "not touch it. Ask about it with the quote and it is one less thing on the day.",
    "Whether you can keep it turns on who owns it now: bought outright it is yours, and rented or "
    "on finance it is not - that is in the agreement, not on any page. If it is yours and nobody "
    "wants it, the council's own site lists the bulky collection, what they take and what it "
    "costs.",
    "Two things settle it: who owns it after the swap, and who will move it. The installer "
    "answers the first when they quote, and a scrap merchant or the council's bulky waste service "
    "answers the second - both are worth asking before the day rather than on it.",
)

def options(clean):
    """A pool of "here is where to find out" replies for this line, or None.

    `clean` is the matchable line the rest of the composer reads: lower case, no apostrophes,
    single spaces. Terms are read first, because "is my phone covered if it gets stolen at the
    festival" is a question about a policy, not about the festival's rules.
    """
    if not isinstance(clean, str) or not clean:
        return None
    if COVER_IT.search(clean):
        return None  # the lid on a pan, or a sheet over the plants
    if COVERED_IN.search(clean):
        return None  # a thing covered in something, not a thing a policy covers
    if PERSON_ALLOWED.search(clean) or WORKING_OUT.search(clean) or BODY_STATE.search(clean):
        return None
    if VISITOR.search(clean) and (WARD.search(clean) or SOMEONES_PERSON.search(clean)):
        return None  # the ward answers this one, not a page
    asking = bool(QUESTION.search(clean))
    if re.match(r"\s*(?:was|were)\b", clean):
        return None  # what was allowed at something that has already happened
    if asking and THE_OLD_ONE.search(clean) and MOVING_THE_OLD.search(clean) \
            and not NOT_THE_OLD_ONE.search(clean):
        return THE_OLD_ONE_POOL  # who owns it and who carries it: the fitter and the council
    if asking and (A_PLACE.search(clean) or A_ROOM_FACILITY.search(clean)) \
            and A_FACILITY.search(clean) and A_HAS_ASK.search(clean) \
            and not NOT_A_HAS.search(clean):
        return A_PLACE_HAS  # what the building has is on the page you book on
    if asking and CANCEL_TERMS.search(clean):
        return TERMS  # the fee for calling it off is on the page it was sold on
    if asking and HARM_NOUN.search(clean) and re.search(r"\bcover(?:ed|s)?\b", clean):
        return INSURER  # "is wind damage covered": the perils are named, so a policy owns the answer
    if asking and TERM_SHAPE.search(clean):
        if PRICE_ASK.search(clean) and not TERM_WORD.search(clean):
            return None  # a quote for this person, not a rule printed on a page
        if INSURANCE_WORD.search(clean) or HARM_NOUN.search(clean):
            return INSURER  # what a policy covers for wind, water or a theft is in its exclusions
        if TICKET_WORD.search(clean):
            return OPERATOR
        if CONTRACT_WORDS.search(clean):
            return CONTRACT
        return TERMS
    terms = TERMS_THING.search(clean) or COVERED_PHRASE.search(clean)
    if asking and not terms and INCLUDED_ASK.search(clean) and PRICE_THING.search(clean):
        return INCLUDED  # a bill, not a policy: what the price covers is on the page it was sold on
    if COURT_ARM.search(clean):
        return None  # a court or a notice is another reader's arm, not a council's discretion
    if asking and terms and TERMS_ASK.search(clean):
        if INSURANCE_WORD.search(clean):
            return INSURER
        if TICKET_WORD.search(clean):
            return OPERATOR
        return TERMS
    # "can i leave my gym early", "how do i end the lease early": the thing being left is named,
    # so "early" on its own is a question about the terms it was signed under.
    early_exit = re.search(r"\bearly\b", clean) and AGREEMENT_WORD.search(clean)
    leaving = (LEAVING_ASK.search(clean) or early_exit
               or (GET_OUT_OF.search(clean) and AGREEMENT_WORD.search(clean)))
    if leaving and LEAVE_EARLY.search(clean) and SHIFT_WORD.search(clean):
        leaving = False  # the rota, not the agreement
    if leaving and not NOT_AN_AGREEMENT.search(clean):
        return CONTRACT  # the notice and the fee are in the terms it was signed under
    if COUNT_AS.search(clean) and ALLOWANCE_WORD.search(clean):
        return VENUE  # what counts towards an allowance is on the operator's page
    if asking and NEEDED_THING.search(clean) and NEEDED_ASK.search(clean):
        return ISSUER
    taking = (not NAMED_OBJECT.search(clean)
              and (TAKE_ON.search(clean)
                   or (TAKE_TO.search(clean) and VENUE_WORDS.search(clean))))
    if ALLOWED_ASK.search(clean) or taking:
        if LOCAL_WORDS.search(clean):
            return LOCAL  # the council writes this one and it is the council that acts on it
        if LAW_NAMED.search(clean) and not (CARRYING.search(clean) and TO_INSIDE.search(clean)):
            return None  # the law decides this, not whoever runs the place
        if VENUE_WORDS.search(clean):
            return VENUE
        if CONTRACT_WORDS.search(clean):
            return CONTRACT
        return ALLOWED
    # Every way of asking about a local service, not only the permission shapes above. A card that
    # knows the service (the bin day, a missed bin, the tip's charges, a council tax band) keeps the
    # turn, because the caller only replaces a hedge; this is the door for the ones nobody wrote.
    if (ASKING_SHAPE.search(clean) and not NOT_A_SERVICE.search(clean)
            and (SERVICE_WORDS.search(clean)
                 or (NOISE.search(clean) and COMPLAINT.search(clean)))):
        return LOCAL_SERVICE
    return None
