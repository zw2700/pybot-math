"""These are patterns from `bot/compose/fallback.py`, kept in their own file.

The world refuses a PR whose clone holds a file over 1 MB, and this file reached more than
that on main: from then on every change to it was refused before a reviewer saw it.
Every name here is a literal or a `re.compile` of literals, and none reads anything the
file defines, so each block moves as one piece with no change to a character of it. They
are imported back where they used to be defined, so every pattern built from them below
and every name a test reads off the module still resolves.
"""
import re

WHO_FOR_IT = re.compile(
    r"^(?:(?:so|and|ok|okay|right|but|then|now|hi|hey|hello|please)\s+)*"
    r"who\s+(?:do|should|can|could|would|must|will)\s+(?:i|we)\s+"
    # "who do i complain to" is not here: that one asks whether what was done is allowed, and the
    # reader for permission shapes answers it with the body that checks the paperwork. Two
    # readers on one line is one answer too many, so this one passes.
    r"(?:call|ring|phone|contact|tell|ask|chase|see|use|get|speak\s+to|talk\s+to|go\s+to"
    r"|report(?:\s+it)?\s+to)"
    r"(?:\s+(?:out|in|around|round))?"
    r"(?:\s+(?:to\s+)?(?:look\s+at|fix|check|sort|deal\s+with))?"
    r"(?:\s+(?:it|that|this|them))?"
    r"(?:\s+about\s+(?:it|that|this|them))?"
    r"(?:\s+(?:first|next|now|then|please|again))?"
    r"\s*[.?!]*$")
# "who can i talk to" with the crisis behind it: a person asking for a voice, a turn after the
# bot has answered something frightening. There is no search for this one and no route list.
CRISIS_ASK = re.compile(
    r"\b(?:who|someone|somebody|anyone|anybody)\b[^.!?]{0,30}?\b(?:talk|speak|chat|text|listen)\b"
    r"|\b(?:need|want|like)\b[^.!?]{0,12}?\b(?:someone|somebody|anyone|a\s+person)\b"
    r"[^.!?]{0,20}?\b(?:talk|speak|listen|there)\b")
A_PERSON_IN_A_CRISIS = (
    "Ring 116 123 - Samaritans, free, any hour, and they will stay on the line as long as you "
    "need. If you are in danger right now, 999. I am still here too, for as long as you want to "
    "type.",)
# The person the thread named a turn ago, said back: "my tooth hurts" / "who do i ring about it".
# The row it comes from is a spoken sentence already ("Your vet is the one to ask, and a call to
# the desk is usually free"), so the tail joins on rather than starting a second sentence about
# "the one" - two of those in a row read like a stutter.
# `who_settles` hands back a whole sentence for some of these ("Citizens Advice answers tenant
# questions free, and a call beats searching"), so each shape stands the who on its own and then
# says the one thing this turn adds. Tacked on with a dash the sentence ran into the tail and
# read like a stutter: "a call beats searching - that is who for what you were just saying".
WHO_FOR_IT_SAID = (
    "{who}. Ring them about what you were just saying, and give the one line: what it is, since "
    "when, and what you want done.",
    "{who}. Same call as a moment ago, so ring them with the details ready - what it is, when it "
    "started, any reference - and tell me what they say.",
)
# The same, for a person to talk to rather than a desk to ring. "who can i talk to" on a thread
# that already knows who settles it came back with "Ring them and give the one line", which
# answers a question the person did not ask: the voice lines are about being listened to, so the
# name joins them and the call stays a call only where it is one.
WHO_FOR_IT_SAID_VOICE = (
    "{who}. Talk to them about what you were just saying in your own words and ask what they "
    "would do - there is nothing to prepare.",
    "{who}. Same person as a moment ago, so talk to them about it: what it is, since when, and "
    "how much it is on your mind.",
)
# The actor the bot's own last answer named: "report it to the council" / "who do i ring about
# that" is the same call, and repeating it is better than a shrug at somebody who has just been
# told where to go.
WHO_NAMED_BEFORE = (
    "{who} - the one the last answer pointed at. Ring them, say the one line, and ask what "
    "happens next.",
    "{who}. You have the rest of it from a moment ago, so that is the call to make.",
)
# Nothing in the line and nothing in the thread: the honest reply is where each kind of trouble
# goes, and one question, because the next line of it decides the answer.
# Who to ring about a body the thread has already named: the GP, and 111 when it cannot wait.
# Not a diagnosis and not a guess at what it is - the thing a person can actually do tonight.
WHO_FOR_IT_BODY = (
    "A body is not something I can look at, so the person to ring is your GP - and 111 tonight if "
    "it is getting worse. Give them the one line: what it is, when it started, and what you are "
    "afraid it might be.",
    "Your GP is the one who can look at it, or 111 if it cannot wait until morning. Write down "
    "when it started first - that is the first thing they will ask.",
)
WHO_FOR_IT_ROUTES = (
    "It depends what it is, so give me the one line and I will point you at the right person: "
    "money, housing or a company that will not play ball is Citizens Advice; a job is a union rep "
    "or ACAS; a body or a medicine is a pharmacist or the GP; a leak, gas, the electrics or a "
    "broken appliance is a plumber, a gas engineer or an electrician.",
    "There is no one answer to that, so tell me what it is about - money, a repair, a body, a "
    "pet, a form - and I will name whose job it is.",
)
# "who can i talk to" outside a crisis: not a service to ring, a person to talk to, and the person
# is the part the bot has no record of. The line above it usually knows which kind of person, and
# then that is named; otherwise this says the honest thing about a stranger's address book and
# offers the next step the bot can actually take, which is help with the first message.
WHO_TO_TALK_ASK = re.compile(
    r"\b(?:who|anyone|anybody|someone|somebody)\b[^.!?]{0,40}?\b(?:talk|speak|chat)\b"
    r"|\b(?:need|want)\b[^.!?]{0,15}?\b(?:someone|somebody|anyone|a\s+person)\b"
    r"[^.!?]{0,20}?\b(?:talk|speak|listen)\b")
WHO_TO_TALK_TO = (
    "Who you can talk to is the one thing I have no record of, so say what it is about - a class, "
    "a job, a repair, a body - and I will name the kind of person worth asking, then help you "
    "word the first message.",
    "I cannot pick the person for you, because I only have what you type. Tell me what it is "
    "about and I will say which kind of person knows, and what to say to them first.",
)
# The same ask, when the thread is a bad one. "i feel lonely at the weekends" and "i keep crying
# at work" then "who can i talk to" is somebody asking who could take some of it, and a route
# list or a question about what it is about is a cold answer to that. The GP line belongs here,
# and only here: it reads as "your doctor can get you to somebody trained", which is a claim about
# a body and a mood, and told to a person asking who runs a painting class it is an accusation.
WHO_TO_TALK_TO_A_BAD_STRETCH = (
    "Who you can talk to is the one thing I have no record of, so it has to be your people: "
    "whoever you would ring at eleven at night, and if that is nobody this week, the GP is not "
    "only for a body - say it is too much and they can get you talking to someone properly. I "
    "can help you word the first message if you tell me who it is.",
    "I cannot pick the person for you, because I only have what you type. The ordinary way in is "
    "one person who already knows you, and one sentence about how things actually are; if it is "
    "bigger than a bad week, your GP can put you in front of somebody trained for it. Say who "
    "you have in mind and I will help you work out what to say.",
)

# "is it worth fixing or shall i live with it", "should i bother fixing my old bike": a repair
# decision is one people ask constantly, and unlike most decisions it has a good general answer
# that needs nothing about the thing - so the honest "your call, not mine" pool is wrong here
# (careful-papaya, routing). It fires only when nothing else knows the thing, so a bike, a boiler
# or a laptop with an entry of its own keeps its answer.
REPAIR_DECISION = re.compile(
    r"\b(?:worth|bother)\s+(?:fixing|repairing|mending|replacing|getting\s+(?:it|that|this)"
    r"\s+(?:fixed|repaired|mended))\b"
    r"|\bfix(?:ing)?\s+(?:it\s+)?or\s+(?:replace|replacing|replacement|live|bin|chuck|"
    r"buy\s+(?:a\s+)?new|buying\s+(?:a\s+)?new)\b"
    r"|\brepair\s+or\s+replace\b"
    r"|\b(?:fix|repair|mend)\s+(?:it|that|this)\s+or\s+(?:live\s+with\s+it|"
    r"replace\s+it|leave\s+it|buy\s+(?:a\s+)?new)\b"
    r"|\bshall\s+i\s+(?:live\s+with\s+it|just\s+(?:fix|replace)\s+it)\b"
    r"|\b(?:is|would)\s+it\s+be\s+(?:better|cheaper)\s+to\s+(?:fix|repair|replace)\b"
    # The same decision in the words people use for the other half of it: paying someone to
    # look at the thing, keeping it against a new one, or writing it off. "is it worth getting
    # it serviced", "should i keep it or replace it" and "should i just write it off" are one
    # question - is the money better spent on this thing or on a new one - and the cost rule is
    # the answer to it, so they get the rule and not "that's your call, not mine", which is the
    # shrug the person came here to avoid. Nothing here names a thing or a trade: a service of
    # a boiler, a car or a bike is the same sum.
    r"|\b(?:worth|bother)\s+(?:servicing|getting\s+(?:it|that|this|them)\s+serviced"
    r"|a\s+service|paying\s+(?:for\s+)?(?:a\s+)?(?:service|repair|fix))\b"
    r"|\b(?:worth|bother)\s+getting\s+(?:a\s+)?new\s+one\b"
    r"|\b(?:get|getting)\s+(?:it|that|this)\s+serviced\s+or\s+(?:replace|replacing|bin|"
    r"leave|keep)\b"
    r"|\bservice\s+(?:it|that|this)\s+or\s+(?:replace|bin|scrap|chuck)\b"
    r"|\bkeep\s+(?:it|that|this|them)\s+or\s+(?:replace|replacing|bin|chuck|get\s+rid|"
    r"buy\s+(?:a\s+)?new|trade\s+(?:it\s+)?in)\b"
    r"|\b(?:write|writing)\s+(?:it|that|this)\s+off\s+or\s+(?:fix|repair|mend|keep)\b"
    r"|\bor\s+should\s+i\s+just\s+(?:replace|bin|chuck)\s+(?:it|that|this)\b"
    r"|\b(?:should|shall)\s+i\s+(?:just\s+)?(?:bin|chuck|scrap)\s+(?:it|that|this)\b"
    r"|\b(?:should|shall|do)\s+i\s+just\s+write\s+(?:it|that|this)\s+off\b")
# The same decision asked the other way round: not whether it is worth mending, but whether it can
# be mended at all. The cost test is a good answer to "worth fixing" and a poor one here - nobody
# has said what has gone wrong yet, and the thing that decides it is the part, which a repair shop
# settles with the thing in front of them. "Worth", "bother" and the money words keep the cost
# test, because those lines do ask what it costs against new.
REPAIR_WHETHER = re.compile(
    r"\bcan\s+(?:it|they|this|that|these|those)\s+(?:be\s+)?(?:get\s+)?"
    r"(?:fixed|repaired|mended|restored|salvaged)\b"
    r"|\bcan\s+i\s+get\s+(?:it|them|this|that|these|those|mine)\s+"
    r"(?:fixed|repaired|mended|restored)\b"
    r"|\bis\s+(?:it|this|that|my|our|the)\s+(?:[a-z']+\s+){0,2}"
    r"(?:fixable|repairable|mendable|salvageable)\b")
# Only the words the cost rule actually answers stand this pool down. A plain money word does not:
# "can they be repaired or do i need new ones" is still the whether question, and the cost rule
# does not fire on it - it reads "worth fixing", "should i bother", not "fixable". So the guard is
# the worth shapes, and everything else gets the answer that says who can tell them.
REPAIR_WHAT_IT_IS_WORTH = re.compile(r"\b(?:worth|bother|cheaper)\b")
# Four of those name no thing to repair: "should i just bin it", "or should i just replace it",
# "should i just write it off" and "should i keep it or replace it" take the "it" from the thread.
# After "i hate this old painting" there is nothing with parts in it and no repair price to weigh,
# so the cost rule stands down unless the thread named a thing that gets serviced or replaced.
REPAIR_BARE_IT = re.compile(
    r"\b(?:bin|chuck|scrap|ditch|replace|write|throw)\s+(?:it|that|this|them)\b"
    r"|\bkeep\s+(?:it|that|this|them)\s+or\b"
    r"|\bor\s+should\s+i\s+just\s+(?:replace|bin|chuck|scrap)\b")
# "is it worth fixing the leak myself or should i call a plumber" is a different decision: who
# does the work, not whether the work is worth it, so the cost rule stands aside for it. It stands
# aside for the trade, not for the word "myself": "is it worth fixing myself" is the same sum as
# any other repair, and it was reaching "not mine to decide" because the first cut of this vetoed
# on the pronoun alone. A line that names another pair of hands still keeps its own answer.
REPAIR_TRADE = re.compile(r"\b(?:plumber|electrician|engineer|"
                          r"handyman|someone|somebody|tradesman|professional|garage)\b")
# A person is not a machine with a part in it: "is it worth fixing my marriage or shall i leave"
# and "is it worth fixing things with my ex" are not cost questions, so the rule stands aside
# wherever a person or a relationship is named.
REPAIR_PERSON = re.compile(
    r"\b(?:marriage|relationship|friendship|ex|husband|wife|partner|boyfriend|girlfriend|"
    r"son|daughter|kids?|children|mum|mom|mother|dad|father|brother|sister|nan|gran|grandma|"
    r"grandad|friend|friends|mate|mates|parents?|family|hair|skin|teeth|credit)\b"
    r"|\bthings?\s+(?:with|between)\s+(?:my|his|her|their|us)\b")
# The other half of the same decision: "my marriage is on the rocks" / "is it worth fixing or
# shall i leave" names the person in the thread and the leaving in the line, and the cost rule read
# the leaving as a thing to fix. Only the thread makes it about a person, though: the same words
# after "the garden gate is hanging off" are a decision about a gate, and after "my back keeps
# going" they are a body and belong to the health line, so the personal reading needs the thread.
LEAVING_IN_THE_LINE = re.compile(
    r"\bor\s+(?:shall|should)\s+i\s+(?:just\s+)?(?:leave|walk\s+away|split\s+up|end\s+it|"
    r"call\s+it\s+a\s+day|move\s+out|divorce)\b")
# A tariff is fixed, not repaired: "is it worth fixing for two years" is an energy deal and "is it
# worth fixing my mortgage for five years" is a rate, and nothing about a part and a quote settles
# either. Both lines had an answer before this rule (the supplier card, the money advice), so the
# cost rule stands aside wherever the thing fixed is a rate, a supplier or a contract.
REPAIR_TARIFF = re.compile(
    r"\b(?:supplier|tariffs?|energy|electricity|gas and electric|price cap|standing charge|"
    r"mortgage|remortgag\w*|contract|deal|policy|premium|insurance|price|prices|rate|rates|"
    r"fix(?:ed|ing)?\s+(?:it\s+)?for\s+(?:one|two|three|four|five|six|a|an|\d+)\s*"
    r"(?:year|years|month|months))\b", re.I)

# The bot is what is trusted, not the world: "can i trust wikipedia" and "can i trust the
# reviews" are questions about those sources and keep the answer they had.
TRUST_ASK = re.compile(
    r"\b(?:can|could|should|would)\s+i\s+trust\s+(?:you|what\s+you|your\s+\w+|"
    r"the\s+(?:answers?|advice|things?)\s+you)\b"
    r"|\btrust\s+(?:what\s+you\s+(?:say|tell)|your\s+answers?|you\s+with)\b"
    r"|\bare\s+you\s+(?:safe|reliable|trustworthy|honest)\b"
    r"|\bis\s+(?:it|this)\s+safe\s+to\s+(?:talk|chat|speak)\s+(?:to\s+)?you\b"
    r"|\bhow\s+do\s+i\s+know\s+(?:you|that\s+you|what\s+you\s+(?:say|tell))\b"
    r"[^?!.]{0,30}?\b(?:right|true|correct|honest|telling|lying|making)\b"
    r"|\bcan\s+you\s+be\s+(?:wrong|trusted)\b|\bare\s+you\s+making\s+(?:this|that|it)\s+up\b",
    re.I)
# The food a person is holding is a different "is it safe", and it has an answer of its own.
PRIVACY_NOT_THIS = re.compile(
    r"\b(?:eat|eaten|eating|cook|cooked|cooking|freezer|fridge|left\s+out|defrost|reheat|"
    r"mouldy|moldy|smell|shelf|use\s+by|best\s+before|baby|child|kid|toddler|pregnan\w*|"
    r"drink|water|ibuprofen|paracetamol|medicine|dose|tablet|drive|driving|swim)\b", re.I)


# A question about the bot itself rather than about something it could do for the person. The
# subject has to be the bot ("can you learn", "do you have opinions"), as a question about it,
# and everything after it has to be one of the words people use for a mind or a machine: "can
# you think of a name for my cat" is about the cat, and "can you learn this song for me" is
# about the song, so both keep the answer they had.
# A line that points back at something the bot said is a follow-up, not a question about the
# bot's nature. "how long did you say" and "when did you say it was" were answered with "No home
# and no history of my own", because every word of them but the bot is filler and "how long" is
# the opener for "where are you". The person is asking again what they already heard, and the
# memory store answers it from what was said a turn or two back.
REFERS_BACK = re.compile(
    r"\b(?:did|do|does|were|was|had|have)\s+(?:you|u)\s+(?:say|said|tell|told|mention|mean)\b|"
    r"\byou\s+(?:said|says|told|mentioned)\b")
# The words that make a line a question about what the bot is, even behind "did you say": the
# self reading is the only one that can answer them.
NAMES_THE_BOT = re.compile(
    r"\b(?:ai|a\.i\.|bot|robot|chatbot|machine|computer|program|programme|algorithm|model|"
    r"human|person|people|alive|sentient|conscious|real)\b")
# "do you think <clause>" hands the bot a proposition to weigh, which is not a question about the
# bot's own nature whatever the clause is made of. Only the clause is read here, so "what do you
# think" on its own stays with the self reading, and "can" is left out on purpose: "can you think
# for yourself" is the ability being asked about, not a view.
A_VIEW_ASKED_FOR = re.compile(
    r"^\s*(?:(?:and|so|but|ok|okay|well|honestly|then|right|also)\s+)*"
    r"(?:do|does|did|would|will)\s+(?:you|u)\s+(?:think|reckon|believe|say)\b(.*)$")
SELF_ASK = re.compile(r"\b(?:can|could|do|does|did|are|is|was|were|will|would|have|has|why|"
                      r"where|when|how\s+long)\s+(?:you|u)\b")
HUMAN_ASK = re.compile(
    r"\b(?:am i|are we|is anyone|is somebody) (?:talking|speaking|chatting|typing) (?:to|with) "
    r"(?:a |an |a real |some )*(?:human|person|real person|bot|robot|machine|computer|ai|"
    r"program)\b|"
    r"\bis (?:this|it) (?:a |an |really )*(?:real )?(?:human|person|bot|robot|machine|ai|"
    r"program|computer)\b|"
    r"\b(?:real person|actual person|human being) (?:on|at) the (?:other|end)\b")
# The words above are also how a person names somebody *else* in a line about them, and then the
# clause after them says what that person is doing: "is this a real person selling the tickets",
# "is anyone talking to a real person about this", "is this person a doctor". Those are questions
# about the world, so the identity reading only claims the line when what follows is nothing, a
# few words of the same question ("or a machine", "or just a bot", "please"), or a note about
# the chat itself ("on here", "in this chat").
HUMAN_TAIL = re.compile(
    r"^(?:\s*(?:or|and|not|just|really|actually|so|then|please|pls|though|right|then)\b)*"
    r"\s*(?:a |an |the )?(?:human|person|bot|robot|machine|computer|ai|program|real person|"
    r"program|chatbot|chat bot|thing|it)?\s*(?:or (?:a |an )?(?:human|person|bot|robot|"
    r"machine|computer|ai|program|chatbot|chat bot|thing))?\s*"
    r"(?:on here|in here|in this chat|on this|here|end|line|side|thanks|thank you|cheers|ok|"
    r"okay)?\s*[.!?]*\s*$")

# The same words with the tail asking us for something are still the bot: "is this a real person
# who can help with my ticket", "is there a human i can ask about my refund". What follows names
# what they want done, not another person doing it.
HUMAN_HELPS = re.compile(
    r"^\s*(?:who|that|which)?\s*(?:can|could|will|would|is able to|to)\s+"
    r"(?:help|answer|sort|deal with|look at|explain|tell me|check)\b|"
    r"^\s*(?:i can (?:talk|speak|ask) to|to (?:talk|speak) (?:to|with))\b")
# The ask has to be the line, not a clause on the end of something else: "someone messaged me
# about it, is this a real person" is about the person who messaged, and only a greeting or a
# "so"/"sorry" in front of the question is still the whole line being asked.
HUMAN_LEAD = re.compile(
    r"^\s*(?:(?:hi|hiya|hey|hello|ok|okay|so|but|and|also|sorry|wait|right|just|quick|"
    r"question|one|more|thing|to|check|first|then|is|are|am|was|were|do|does|did|there|"
    r"any|anyone|anybody|somebody|this|that|a|an|the|real|actually|really)\b[ ,]*)*$")


# A question quoted as somebody else's is still that question: "my mate says am i talking to a
# human", "he asked is this a real person".
HUMAN_QUOTED = re.compile(r"\b(?:says|said|asks|asked|wants to know|is asking|was asking|"
                          r"keeps asking|texted)\s*$")
TRIED_THE_LOT = re.compile(
    r"^(?:(?:ok|okay|alright|right|so|well|yeah|yep|yes|cool|fine|and|but|then|i|we|ive|i've|"
    r"weve|we've)\s+)*"
    r"(?:(?:have|had|did)\s+)?(?:tried|been trying|done|did)\s+"
    r"(?:them all|it all|everything|the lot|all of (?:it|them|those|these)|both)\b")
# The same report in the perfect tense and with the pronoun dropped: "ok ive done that", "done it",
# "did that this morning". People say what they have finished, not "i tried that", and those lines
# were reaching the neutral nod a turn after the answer told them to do it: "my back hurts" /
# "ok ive done that" got "Got it. Is there anything you'd like a hand with?". Anchored, because
# "what did that" in the middle of a line is a question about somebody else's doing.
DONE_IT = re.compile(
    r"^(?:(?:ok|okay|alright|right|so|well|yeah|yep|yes|cool|fine|and|but|then|"
    r"i|we|ive|i've|weve|we've)\s+)*"
    r"(?:(?:have|had)\s+)?(?:done|did)\s+(?:it|that|this|them)\b")


# The fifth outcome, and the only one that is not about the person's own try: they did what the
# answer said and somebody else said no. It was filed back as the person's own words - "my boss
# said no" was answered "Got it - your boss said no" - which hands them their sentence back and
# takes the thread nowhere. The action the person needs is the same whatever the ask was: one more
# go, and find out what would change it. The wording varies; the action does not.
REFUSED = re.compile(
    r"\b(?:said|says|saying|told\s+me)\s+no\b"
    r"|\b(?:turned|turns)\s+(?:me|it|us|him|her|them)\s+down\b"
    r"|\b(?:knocked|knocks)\s+(?:me|it|us|them)\s+back\b"
    r"|\bno\s+(?:for\s+an\s+answer|was\s+the\s+answer)\b"
    # "he refused" is a no to the ask; "my card was refused" and "my application was refused" are
    # a payment and a decision letter, so the verb only counts with somebody in front of it.
    r"|\b(?:he|she|they|we|the\s+\w+|my\s+\w+)\s+refused\b"
    r"|\b(?:wouldnt|wouldn't|wont|won't)\s+(?:budge|bend|agree|have\s+it|do\s+it|come\s+round)\b",
    re.I)
# A no from somebody treating them is not a no to ask again about: "the doctor said no" is a
# clinical decision, and "ask what would make it a yes" is the wrong thing to say to a person
# about their own care. Those lines keep whatever the health cards and the care pools have.
REFUSED_NOT = re.compile(
    r"\b(?:doctor|gp|nurse|consultant|midwife|surgeon|physio\w*|pharmacist|chemist|dentist|"
    r"hospital|surgery|clinic|111|a&e|ae|paramedic\w*)\b", re.I)
# The no that belongs to the speaker: "i said no", "we told him no". They are the one who refused,
# so there is nobody for them to ask again.
OWN_NO = re.compile(
    r"\b(?:i|we|ive|i've|weve|we've)\b[^.!?]{0,12}?\b(?:said|says|told|tells?|turned|refused|"
    r"knocked)\b[^.!?]{0,12}?\bno\b"
    r"|\b(?:i|we)\b[^.!?]{0,12}?\b(?:refused|turned\s+\w+\s+down)\b", re.I)
# The no that comes from the speaker's own household is not an application: "my husband said no"
# is a disagreement, and "ask once more what would make it a yes" is advice for a panel, not for
# the person they live with. Those lines keep whatever the relationship cards have.
REFUSED_FAMILY = re.compile(
    r"\b(?:husband|wife|partner|boyfriend|girlfriend|fiance|fiancee|ex|exes|mum|mom|mother|dad|"
    r"father|son|daughter|sister|brother|mate|friend|flatmate|housemate|roommate|stepdad|"
    r"stepmum|stepmother|stepfather|gran|granny|nan|nana|grandad|grandpa|grandma|"
    r"uncle|aunt|auntie|cousin|in-law|in\s+laws)\b", re.I)
# The party who said no has to be one that answers an ask: a boss, a bank, a council, a landlord, a
# panel. Those said no to an application, and a second ask with one change in it is the next move.
# A no with no party named - "she said no", "they wouldnt budge" - has nothing in it that says who
# answered, and on its own it is somebody turned down in their own life, which the relationship
# cards answer with care. That line only counts as this outcome where the bot gave an answer above
# and the person came back with how it went (see `_an_answer_above`).
REFUSED_PARTY = re.compile(
    r"\b(?:boss|manager|managers|employer|employers|hr|personnel|bank|banks|building\s+society|"
    r"council|councils|landlord|landlady|letting\s+agent|jobcentre|job\s+centre|dwp|"
    r"panel|committee|board|union|university|uni|college|school|nursery|shop|store|retailer|"
    r"seller|supplier|insurer|insurance|agent|agency|recruiter|firm|company|office|"
    r"department|court|tribunal|ombudsman|clinic|hospital|charity|club|gym|council\s+tax|"
    r"mortgage\s+company|housing\s+association|benefits\s+office)\b", re.I)
# A written thing "says no" what is in it: "the invite says no dress code", "the sign says no
# parking outside", "the label says no added sugar", "the menu says no substitutions". Nobody
# refused anybody there. The no in a refusal is the whole answer ("my boss said no", "the
# landlord said no to the dog"), and when a word of the thing being ruled out follows it, the no is
# a rule written down instead. So the verb stands down on a no that a word of its own follows -
# except the set phrases that are a refusal ("said no way", "said no thanks").
REFUSED_NO_OBJECT = re.compile(
    r"\b(?:said|says|saying|told\s+me)\s+no\s+(?!(?:way|chance|deal|thanks|thank|worries|"
    r"problem|dice|objection|to|about|on|again|twice|either|yet|at|for\s+now|so|and|but|then|"
    r"though|after|before|last|this|it|because|when|until|unless)\b)[a-z]", re.I)
# An answer that already says what to do when somebody says no: the card told them to dispute the
# deductions, to use the scheme or the ombudsman, to appeal. "Ask once more with one change in it"
# is weaker than the step they were already given, so the card keeps the turn - the store hands that
# answer back ("Same answer, and it covers this: ...") and the person hears their own step. It has
# to be a formal next step, not any mention of writing: the pay-rise card ends "follow up in
# writing", and the pool is the gain there.
AN_ANSWER_ABOUT_A_NO = re.compile(
    r"\b(?:dispute[ds]?|disputing|appeal|complain\w*|complaint\w*|ombudsman|tribunal|"
    r"small\s+claims|letter\s+before\s+action|trading\s+standards|protection\s+scheme|"
    r"escalate|raise\s+it\s+with\s+the\s+council)\b", re.I)
# The same words as a question, which is a question and not a report: "why did my boss say no".
ASKS_WHY = re.compile(r"^(?:why|how|what|when|where|who|did|does|do|is|are|was|were|can|could|"
                      r"should|would|will|any\s+idea)\b", re.I)
# A no that has not happened yet is a case the person is planning for, not one they were given:
# "i want to ask about going part time" / "and what if he says no" was answered "put it to them
# once more", to somebody who had not put it to anybody. It is a foresight, so the ask is still
# ahead of them and the wording for that case is what they want.
HYPOTHETICAL = re.compile(
    r"\b(?:what\s+if|if|suppose|supposing|supposed|in\s+case|unless|should|were\s+to|may|might|"
    r"would|what\s+happens\s+(?:if|when)|when)\b(?:\s+\w+){0,5}\s*$", re.I)


# The words that make a line a report on how they are, not a new subject. It needs a first
# person and a feeling ("i feel better", "im doing ok now"), and a negator or "still"/"not"
# keeps it the emergency ("i dont feel better", "still feel awful").
# The easing comes in two shapes. One names the speaker ("i feel a bit better now", "we're doing
# ok"); the other is the bare report people actually type straight after a first-aid answer - "a
# bit better", "much better", "a lot better" - which has no subject for the first pattern to hold
# on and was read as no easing at all, so the care pool said "still going on" to a person who had
# just said it was easing. The second shape needs its quantifier: a bare "better" is a word in
# "you better go" and "better to wait", and neither of those is an easing.
FEELS_BETTER = re.compile(
    r"\b(?:i|im|i'?m|we|we'?re|feeling|feel|doing|getting|its|it'?s)\b[^.?!]{0,24}"
    r"\b(?:better|calmer|calm|alright|okay|ok|fine|easier|lighter|less\s+(?:awful|bad))\b"
    r"|\b(?:better|calmer)\s+(?:now|today|tonight|thanks)\b"
    r"|\b(?:(?:just\s+)?a\s+(?:bit|little|touch|lot)|lots|much|slightly|way|far)\s+"
    r"(?:better|calmer|easier|lighter)\b"
    r"|\b(?:its|it'?s|it is)\s+easing\b")
FEELS_NOT_BETTER = re.compile(
    r"\b(?:don'?t|doesn'?t|not|never|still|worse|no better|not any)\b")
# A line that asks to leave the subject is the end of the thread, not an easing inside it.
MOVE_ON = re.compile(r"\b(?:something else|something different|change the subject|move on|"
                     r"different topic|another topic|talk about anything|talk about something|"
                     r"nothing else)\b")

# "Still going on" is the person's own report, so it is only said to a line that makes it: "thanks,
# still bleeding", "it keeps catching", "worse today". A follow-up about the injury that reports
# nothing - "can i go up the stairs" after a twisted knee - is not a report, and telling that
# person it is still going on invents a symptom they never described (reported against #5882).
# It is kept as its own line because the line that reaches this pool is inside the emergency and
# cannot be told it has handled things well.
STILL_GOING = re.compile(r"\b(?:still|keeps?|kept|stopped|stops|worse|worsening|again|"
                         r"hasn't|has not|haven't|have not|won't)\b")

CARE_SEEN_ASKS = re.compile(
    r"\b(?:should|shall|do|does|need|needs|have to|got to) (?:i|we|it|this)\b[^.?!]*"
    r"\b(?:go|a&e|stitches|checked|seen|hospital|doctor|walk-in|later|tonight)\b"
    r"|\bdo (?:i|we) need\b|\bam i being (?:silly|daft)\b")
IN_HOSPITAL = re.compile(
    r"\b(?:hospital|ward|casualty|admitted|admission|intensive care|icu|hdu|hospice|"
    r"a\s*&\s*e|a and e|aande|ambulance|in for tests|in for an operation|"
    r"having an operation|on a drip|taken in)\b")
VISIT_ASK = re.compile(
    r"\b(?:go|come|get) (?:up|over|round|across|down)\b"
    r"|\bgo (?:and )?see\b|\bvisit(?:ing)?\b")
# "Go up" is also how people ask about their own body on a staircase: "i twisted my knee" then
# "can i go up the stairs" is a question about weight-bearing, and the visit pool answered it
# "ask whoever is on the ward" - which reported it. So a phrase that runs on to a way up, a bed
# or their own room is somebody measuring what they can do, not going to sit with anyone.
NOT_A_VISIT = re.compile(
    r"\b(?:go|come|get|walk|climb|run)\s+(?:up|down)\s+(?:and\s+(?:down|up)\s+)?"
    r"(?:the\s+|a\s+|my\s+|these\s+|those\s+)?"
    r"(?:stairs?|staircase|steps?|ladder|hill|slope|ramp|stile|loft|scaffold)\b"
    r"|\b(?:go|get|come)\s+up\s+(?:to\s+)?(?:bed|my room|the bedroom)\b")
MEDICAL_PLACE = re.compile(
    r"\b(?:hospital|casualty|ward|clinic|surgery|doctor|doctors|gp|walk[\s-]?in|out of "
    r"hours|a\s*&\s*e|a and e|aande|ae|999|111)\b")
# The shape of the question, not the subject: "should i put butter on it", "can i cover it",
# "do i need a plaster on it". Read only inside a care thread, so a household line cannot use it.
BURN_ON_IT = re.compile(
    r"\b(?:put|rub|smear|spread|dab)\b[^.?!]{0,30}\b(?:on|over) (?:it|them|that|there)\b"
    r"|\b(?:cover|wrap|dress|bandage)\b[^.?!]{0,20}\b(?:it|them|that|the burn)\b")
# The bare noun on its own is only about the burn where the line is asking. "i need to go to the
# shop for some cream" and "i like ice cream" are not questions about the burn, and answering
# them "cool water only, I'm afraid" was two real bugs (hardy-pen, #784).
BURN_THING = re.compile(r"\b(?:cream|ointment|antiseptic|butter|toothpaste|ice|ice ?pack|"
                        r"plaster|dressing)\b")
BURN_ASK = re.compile(r"\b(?:should|can|could|do|would|will|is|are)\s+(?:i|we|it|they)\b"
                      r"|\?")
BURN_BLISTER_LINE = re.compile(
    r"\b(?:pop|piercing|pierce|burst|drain|squeeze|lance)\b[^.?!]{0,20}\b(?:blister|bubble)\b"
    r"|\bblister\b[^.?!]{0,20}\b(?:pop|burst|drain|squeeze)\b")
# Which injury the thread is: read from the bot's answer and from the line that started it. The
# sunburn answer ("cool showers, plenty of water and a loose cotton shirt... leave blisters
# alone") never says "burn", so reading only the answer sent "can i pop the blister" three lines
# after "i got sunburnt" to the generic care line instead of the blister answer.
BURN_WORD = re.compile(r"\b(?:burns?|burnt|burned|burning|scald(?:s|ed|ing)?|"
                       r"sunburn(?:s|ed|t)?|sunburnt)\b")
# "can i pop it" two lines after "i burnt my hand": the object is the blister the bot has just
# described, so the line is about the burn though it names nothing. Read only inside a burn
# thread, where there is nothing else a person could be popping.
POP_A_BARE_IT = re.compile(r"\b(?:pop|pierce|burst|drain|lance|squeeze)\b[^.?!]{0,12}"
                           r"\b(?:it|that|them|this)\b")
# Asking about the time: "is ten minutes enough", "how long should i hold it", "is twenty
# minutes too long", "does it have to be that long". A number with "enough"/"too long" is the
# commonest spelling, so both halves of a time ask are here.
ADVICE_TIME_ASK = re.compile(
    r"\b(?:is|are|was)\s+(?:\d+|one|two|three|four|five|ten|fifteen|twenty|thirty|forty)\s*"
    r"(?:min|mins|minutes?|secs?|seconds?)\s+(?:enough|too\s+(?:long|short|much|little)|"
    r"ok|okay|fine)\b"
    r"|\bis\s+(?:that|this|it)\s+long\s+enough\b"
    r"|\bhow\s+long\s+(?:should|shall|do|can|must|need)\s+(?:i|we)\s+"
    r"(?:hold|keep|leave|stay|run|do|press|put)\b"
    r"|\bhow\s+long\s+does\s+it\s+(?:need|take|have\s+to\s+be)\b"
    r"|\bdoes\s+it\s+have\s+to\s+be\s+that\s+long\b"
    r"|\b(?:can|could|should)\s+i\s+stop\s+(?:early|now|sooner)\b")
# Whether the water has to be cold: only asked about something that was cooled, so the branch
# checks the last answer before using it.
ADVICE_COOL_ASK = re.compile(
    r"\b(?:lukewarm|tepid)\b"
    r"|\b(?:cold|cool|warm|hot)\s+water\b"
    r"|\bdoes\s+it\s+have\s+to\s+be\s+(?:cold|cool|warm)\b"
    r"|\bis\s+(?:cold|cool|warm)\s+(?:ok|okay|fine|enough)\b")
# The three pools below say "the time in the answer", so they are only used when the answer gave
# one. A poisoning, an overdose or an asthma attack is answered with 999 and a container to keep,
# not with a timed step, and "give it the full time" is nonsense in those threads.
ADVICE_TIME_WORDS = re.compile(
    r"\b(?:\d+|one|two|three|five|ten|fifteen|twenty|thirty)\s*"
    r"(?:minutes?|mins?|seconds?|secs?)\b")
# Whether the same thing is done again: "can i do it again", "do i need to start again".
ADVICE_AGAIN_ASK = re.compile(
    r"\b(?:can|could|should|shall|do)\s+i\s+(?:do|have|start|try|run|hold|press)\s+"
    r"(?:it|that|this)\s+(?:again|twice)\b"
    r"|\bdo\s+i\s+need\s+to\s+(?:do|start|repeat)\s+(?:it|that)\s+again\b"
    r"|\b(?:can|could|should)\s+i\s+(?:do|have|run)\s+(?:another|a\s+second)\b")
# What to do when the advice has not worked. Not "what if it hurts" - that is the injury still
# going, and the pools below answer it. "How do I know when it's done" is deliberately not here:
# it asks for the sign to watch for, and the pool below answers "stop waiting and have it seen",
# which is the opposite answer to the question asked.
ADVICE_WORSE_ASK = re.compile(
    r"\bwhat\s+if\s+(?:it|that|this|the\s+bleeding|the\s+pain)\s+"
    r"(?:doesnt|does\s+not|didnt|wont|won't|still\s+doesnt)\s+"
    r"(?:stop|work|settle|ease|help|go\s+away|slow)\b"
    r"|\bwhat\s+if\s+(?:it|that)\s+keeps?\s+(?:going|bleeding|hurting|burning)\b")
